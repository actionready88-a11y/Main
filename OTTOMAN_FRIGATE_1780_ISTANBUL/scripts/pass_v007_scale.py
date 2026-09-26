"""Pass v007 — gemiyi eşit oranda %10 büyüt (v006 üzerine).

Çalıştırma (depo kökünden):
    python3 OTTOMAN_FRIGATE_1780_ISTANBUL/scripts/pass_v007_scale.py [--no-render | --render-only]

Gerekçe: kıç kasarası altı, baş kasarası altı ve kaptan kamarası net tavanları 1,88-1,90 m idi
(UE varsayılan karakter kapsülü 1,76 m). Kullanıcı izni (2026-09-26): "bunlar sıkıntılı oluyorsa
hafiften gemiyi büyütebilirsin."
Yöntem: tüm nesneler orijine göre ölçeklenir (su hattı Z=0 korunur); ölçek mesh verisine uygulanır,
nesne ölçeği 1 kalır. UV'ler de aynı oranla çarpılır (UV metre cinsinden; tahta genişliği korunur).
Modifier kalınlıkları (kaplama 0,24 m, güverte 0,10 m) gerçek malzeme kalınlığı olarak korunur.
Soket ve modül dönüşleri değişmez; konumlar ölçeklenir (manifest 5).
"""

import importlib.util
import json
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

HERE = Path(__file__).resolve().parent


def _load(name, fname):
    sp = importlib.util.spec_from_file_location(name, HERE / fname)
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


P5 = _load("pass_v005", "pass_v005_stern.py")
SS = _load("ship_scale", "ship_scale.py")
H = P5.H
K = SS.SHIP_SCALE
SRC_VER, VER = "v006", "v007"
ROOT, SHIP = H.ROOT, H.SHIP_ID
MANIFEST_VERSION = 5


def scale_scene():
    S = Matrix.Scale(K, 4)
    done_meshes = set()
    for ob in bpy.data.objects:
        if ob.parent is not None:
            raise SystemExit(f"Beklenmeyen ebeveyn: {ob.name}")
        ob.location = ob.location * K
        if ob.type == "MESH":
            me = ob.data
            if me.name not in done_meshes:
                me.transform(S)
                for uvl in me.uv_layers:
                    for d in uvl.data:
                        d.uv = d.uv * K
                done_meshes.add(me.name)
        elif ob.type == "EMPTY":
            ob.empty_display_size *= K
            if "manifest_version" in ob.keys():
                ob["manifest_version"] = MANIFEST_VERSION
    for ob in bpy.data.objects:
        if ob.type == "MESH" and ob.name.startswith("MOD_") and "manifest_version" in ob.keys():
            ob["manifest_version"] = MANIFEST_VERSION
    sc = bpy.context.scene
    sc["ship_scale"] = K
    sc["design_space_note"] = "dünya = ship_scale × tasarım uzayı (scripts/ship_scale.py)"
    return len(done_meshes)


def deck_level_at(name, x, y=0.0, tol=0.35):
    """Değerlendirilmiş güverte mesh'inde (x, y) yakınındaki üst ve alt yüzey z değerleri."""
    dg = bpy.context.evaluated_depsgraph_get()
    ob = bpy.data.objects[name]
    me = ob.evaluated_get(dg).to_mesh()
    zs = [(ob.matrix_world @ v.co).z for v in me.vertices
          if abs((ob.matrix_world @ v.co).x - x) < tol and abs((ob.matrix_world @ v.co).y - y) < tol]
    ob.evaluated_get(dg).to_mesh_clear()
    return (min(zs), max(zs)) if zs else (None, None)


def headrooms():
    W = SS.wrap(H)
    out = {}
    xq = W.hull_point(0.25, W.deck_z(0.25))[0]
    xf = W.hull_point(0.90, W.deck_z(0.90))[0]
    xc = (P5.X_FRONT - 1.0) * K
    for key, x, upper, lower in (("kic_kasarasi_alti", xq, "CORE_DECK_QUARTER", "CORE_DECK_GUN"),
                                 ("bas_kasarasi_alti", xf, "CORE_DECK_FORECASTLE", "CORE_DECK_GUN"),
                                 ("kaptan_kamarasi", xc, "CORE_DECK_POOP", "CORE_DECK_QUARTER")):
        u_bot, _ = deck_level_at(upper, x)
        _, l_top = deck_level_at(lower, x)
        out[key] = {"x": round(x, 2), "net_m": round(u_bot - l_top, 3) if u_bot and l_top else None}
    return out


def render_scaled(sc):
    P5.H.setup_render(sc, fast=True)
    out = ROOT / "renders" / VER
    out.mkdir(parents=True, exist_ok=True)
    zc = 2.3 * K
    views = [
        ("bas", (60, 0, zc), (0, 0, zc), 27, None),
        ("kic", (-60, 0, zc), (0, 0, zc), 27, None),
        ("iskele_profil", (1.5, -80, zc), (1.5, 0, zc), 48, None),
        ("sancak_profil", (1.5, 80, zc), (1.5, 0, zc), 48, None),
        ("bas_omzu", (34, 26, 13), (1, 0, 1.5), None, 35),
        ("kic_omzu", (-34, -24, 12), (-4, 0, 2.5), None, 35),
        ("guverte", (18, 12, 28), (-4, 0, 3.0), None, 30),
        ("kic_yakin", (-27, 11, 8.5), (-17.5, 0, 5.2), None, 40),
        ("kic_ust_guverte", (-7.5, 7.5, 12.5), (-15.5, 0, 6.5), None, 28),
        ("merdivenler", (-6.0, -2.5, 6.6), (-13.8, 0.0, 5.2), None, 26),
    ]
    for name, loc, tgt, osc, lens in views:
        loc = Vector(loc) * K
        tgt = Vector(tgt) * K
        cam = (P5.H.camera(sc, f"CAM7_{name}", loc, tgt, ortho=osc * K) if osc
               else P5.H.camera(sc, f"CAM7_{name}", loc, tgt, lens=lens))
        sc.camera = cam
        sc.render.filepath = str(out / f"{SHIP}_{VER}_{name}.png")
        bpy.ops.render.render(write_still=True)


def main():
    if "--render-only" in sys.argv:
        bpy.ops.wm.open_mainfile(filepath=str(ROOT / "Blender" / "versions" / f"{SHIP}_{VER}.blend"))
        return render_scaled(bpy.context.scene)
    bpy.ops.wm.open_mainfile(filepath=str(ROOT / "Blender" / "versions" / f"{SHIP}_{SRC_VER}.blend"))
    sc = bpy.context.scene
    n_mesh = scale_scene()
    bpy.context.view_layer.update()
    hr = headrooms()

    out = ROOT / "Blender" / "versions" / f"{SHIP}_{VER}.blend"
    if out.exists():
        raise SystemExit(f"{out} zaten var; versiyonlu kayıt üzerine yazılmaz.")
    bpy.ops.wm.save_as_mainfile(filepath=str(out), compress=True)

    H.VERSION = VER
    ap = ROOT / "reports" / f"scene_audit_{VER}.json"
    rep = H.audit(sc, ap)
    rep["scale"] = {
        "ship_scale": K, "meshes_scaled": n_mesh, "headroom_net_m": hr,
        "dimensions_design_to_world_m": {
            "length_gundeck": [H.L, round(H.L * K, 2)], "beam": [H.B, round(H.B * K, 2)],
            "draft": [H.T, round(H.T * K, 2)], "gun_deck_above_wl_mid": [H.DECK_MID, round(H.DECK_MID * K, 2)],
            "castle_above_gun_deck": [H.QD_H, round(H.QD_H * K, 2)], "poop_above_quarterdeck": [P5.POOP_H, round(P5.POOP_H * K, 2)],
        },
        "kept_absolute": ["hull plank thickness 0.24 (Solidify)", "deck thickness 0.10 (Solidify)", "bevel widths"],
    }
    rep["pass"] = {"name": "pass_v007_scale", "source": f"Blender/versions/{SHIP}_{SRC_VER}.blend",
                   "pass_changes": {"all_objects_scaled_about_origin": K, "uv_scaled": K},
                   "manifest_version": MANIFEST_VERSION}
    ap.write_text(json.dumps(rep, indent=2, ensure_ascii=False), encoding="utf-8")
    c = rep["checks"]
    print("BOUNDS", c["bounds_m"], "draft", c["draft_from_bounds_m"], "non_unit_scale", c["non_unit_scale"])
    print("HEADROOM", json.dumps(hr, ensure_ascii=False))

    if "--no-render" not in sys.argv:
        render_scaled(sc)


if __name__ == "__main__":
    main()
