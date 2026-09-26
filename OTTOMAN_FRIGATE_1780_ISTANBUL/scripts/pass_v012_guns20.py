"""Pass v012 — 20 borda topu (bordada 10) + 4 kovalama, v011 üzerine; gövde değişmez.

Çalıştırma (depo kökünden):
    python3 OTTOMAN_FRIGATE_1780_ISTANBUL/scripts/pass_v012_guns20.py [--no-render | --render-only]

Kullanıcı kararı (2026-09-26): "Toplam top sayısını 20'ye indir; oyunda yükseltme ile alt güverteye ekstra
toplar eklenebilir." Kullanıcı netleştirmesi: "20+4" → 20 borda (10/borda, üst güverte, bel) + 2 baş + 2 kıç kovalama.
Bel topları x = -10,05 … 9,55 (tasarım; v011 ile aynı yerler, aralık 2,18). Baş kasarası altındaki top kaldırıldı.
Alt güverte yükseltmesi: mevcut gövdede alt güverte lumbarları su hattının altında kalır → yükseltme,
bordası yüksek ayrı bir Hull sınıfı/varyantı olarak planlanır (MODULAR_SHIP_STANDARD: yapısal gövde
değişimi yeni hull sınıfıdır).
"""

import importlib.util
import json
import sys
from pathlib import Path

import bpy  # noqa: I001
import bmesh
import numpy as np
from mathutils import Vector

HERE = Path(__file__).resolve().parent
_sp = importlib.util.spec_from_file_location("pass_v011", HERE / "pass_v011_lower_stern.py")
P11 = importlib.util.module_from_spec(_sp)
_sp.loader.exec_module(P11)
P5, P4, H, K, SK = P11.P5, P11.P4, P11.H, P11.K, P11.SK

SRC_VER, VER = "v011", "v012"
ROOT, SHIP = H.ROOT, H.SHIP_ID
MANIFEST_VERSION = 10
P11.MANIFEST_VERSION = MANIFEST_VERSION
GUNS_PER_SIDE = 10
WAIST = (-10.05, 9.55)


def port_positions_v012():
    ports = []
    for k, x in enumerate(np.linspace(WAIST[0], WAIST[1], GUNS_PER_SIDE)):
        s = (x - H.stern_x(2)) / (H.bow_x(2) - H.stern_x(2))
        ports.append(("MAIN", k + 1, x, s, H.deck_z(s) + H.PORT_SILL + H.PORT_H / 2))
    return ports


H.port_positions = port_positions_v012


def rebuild_cutter(core):
    old = bpy.data.objects["CUT_GUNPORTS"]
    dummy = bpy.data.objects.new("_dummy_hull", bpy.data.meshes.new("_dummy_hull"))
    core.objects.link(dummy)
    new = H.build_port_cutters(core, dummy)
    bm = bmesh.new()
    bm.from_mesh(new.data)
    seen, kill = set(), []
    for v in bm.verts:
        if v.index in seen:
            continue
        stack, isl = [v], []
        while stack:
            a = stack.pop()
            if a.index in seen:
                continue
            seen.add(a.index)
            isl.append(a)
            stack += [e.other_vert(a) for e in a.link_edges]
        if sum(p.co.x for p in isl) / len(isl) < -17.0:  # kıç aynası kovalama lumbarları (kapalı kalır)
            kill += isl
    bmesh.ops.delete(bm, geom=kill, context="VERTS")
    bm.to_mesh(new.data)
    bm.free()
    new.data.transform(SK)
    old_me = old.data
    old.data = new.data
    bpy.data.objects.remove(new, do_unlink=True)
    dm = dummy.data
    bpy.data.objects.remove(dummy, do_unlink=True)
    bpy.data.meshes.remove(dm)
    if old_me.users == 0:
        bpy.data.meshes.remove(old_me)


def main():
    if "--render-only" in sys.argv:
        bpy.ops.wm.open_mainfile(filepath=str(ROOT / "Blender" / "versions" / f"{SHIP}_{VER}.blend"))
        return render(bpy.context.scene)
    bpy.ops.wm.open_mainfile(filepath=str(ROOT / "Blender" / "versions" / f"{SHIP}_{SRC_VER}.blend"))
    sc = bpy.context.scene
    M = P5.ensure_materials()
    C = {c.name: c for c in bpy.data.collections}
    core, col = C["10_HULL_CORE"], C["30_SOCKETS"]
    rebuild_cutter(core)
    P11.remove("CORE_GUNPORT_FRAMES")
    fr = H.build_port_frames(core, M)
    P11.to_world(fr)
    H.build_uv_fallback(fr)
    deleted = []
    for o in list(bpy.data.objects):
        if o.type != "EMPTY":
            continue
        for tag in ("S", "P"):
            for idx in range(GUNS_PER_SIDE + 1, 13):
                if o.name == f"SOCKET_CANNON_{tag}_{idx:02d}" or o.name.startswith(f"SOCK_CREW_{tag}_{idx:02d}_"):
                    deleted.append(o.name)
                    bpy.data.objects.remove(o, do_unlink=True)
                    break
            else:
                continue
            break
    moved = []
    for kind, idx, x, s, z in H.port_positions():
        _, y = H.hull_point(s, z)
        for side, tag in ((1, "S"), (-1, "P")):
            moved.append(P11.set_world(f"SOCKET_CANNON_{tag}_{idx:02d}", (x, side * (y - 1.2), H.deck_z(s)), col))
    bpy.context.view_layer.update()
    for tag in ("S", "P"):
        for idx in range(1, GUNS_PER_SIDE + 1):
            g = bpy.data.objects[f"SOCKET_CANNON_{tag}_{idx:02d}"]
            for key, (role, (lx, ly)) in P4.CREW.items():
                c = bpy.data.objects[f"SOCK_CREW_{tag}_{idx:02d}_{key}"]
                c.location = g.matrix_world @ (Vector((lx, ly, 0.0)) * K)
                c["manifest_version"] = MANIFEST_VERSION
    guns = sorted(o.name for o in bpy.data.objects if o.type == "EMPTY" and o.name.startswith("SOCKET_CANNON_"))

    out = ROOT / "Blender" / "versions" / f"{SHIP}_{VER}.blend"
    if out.exists():
        raise SystemExit(f"{out} zaten var; versiyonlu kayıt üzerine yazılmaz.")
    bpy.ops.wm.save_as_mainfile(filepath=str(out), compress=True)
    H.VERSION = VER
    ap = ROOT / "reports" / f"scene_audit_{VER}.json"
    rep = H.audit(sc, ap)
    rep["armament_v012"] = {
        "total": len(guns), "broadside_per_side": GUNS_PER_SIDE, "chase": {"bow": 2, "stern": 2},
        "main_gun_x_world": [round(p[2] * K, 2) for p in H.port_positions()], "sockets": guns,
        "upgrade_note": "alt güverte topları: ayrı, bordası yüksek Hull varyantı gerektirir (mevcut gövdede lumbar su hattı altında)",
    }
    rep["pass"] = {"name": "pass_v012_guns20", "source": f"Blender/versions/{SHIP}_{SRC_VER}.blend",
                   "pass_changes": {"sockets_deleted": deleted, "rebuilt": ["CUT_GUNPORTS (mesh, yerinde)", "CORE_GUNPORT_FRAMES"]},
                   "manifest_version": MANIFEST_VERSION, "geometry_changed": "yalnız lumbar açıklıkları ve çerçeveleri"}
    ap.write_text(json.dumps(rep, indent=2, ensure_ascii=False), encoding="utf-8")
    print("GUNS", len(guns), rep["armament_v012"]["main_gun_x_world"], "DELETED", len(deleted))
    if "--no-render" not in sys.argv:
        render(sc)


def render(sc):
    H.setup_render(sc, fast=True)
    out = ROOT / "renders" / VER
    out.mkdir(parents=True, exist_ok=True)
    for name, loc, tgt, lens, osc in (("iskele_profil", (1.5, -80, 2.3), (1.5, 0, 2.3), None, 48),
                                      ("guverte", (18, 12, 28), (-4, 0, 3.0), 30, None),
                                      ("bas_omzu", (34, 26, 13), (1, 0, 1.5), 35, None)):
        cam = (H.camera(sc, f"CAM12_{name}", Vector(loc) * K, Vector(tgt) * K, ortho=osc * K) if osc
               else H.camera(sc, f"CAM12_{name}", Vector(loc) * K, Vector(tgt) * K, lens=lens))
        sc.camera = cam
        sc.render.filepath = str(out / f"{SHIP}_{VER}_{name}.png")
        bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    main()
