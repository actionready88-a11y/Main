"""Pass v024 — LanternFlagSet: donanma sancağı (gaf ucunda) + flama (ana direk topuzunda), v023 üzerine.

Çalıştırma (depo kökünden):
    python3 OTTOMAN_FRIGATE_1780_ISTANBUL/scripts/make_flags.py      # dokular (bir kez)
    python3 OTTOMAN_FRIGATE_1780_ISTANBUL/scripts/pass_v024_flags.py [--no-render | --render-only]

Kullanıcı sırası (2026-09-26): halat/makara → "bayrak" → ambar içi → LOD/bake.
- Sancak: kırmızı zemin, beyaz hilal ve sekiz köşeli yıldız (1793 donanma sancağı biçimi; ay-yıldız III. Mustafa
  döneminden beri) [İKİNCİL — make_flags.py]. Boyut 3,6 × 2,4 m (TAHMİN).
- Konum: kıçtaki SOCKET_FLAG_STERN üstünden randa bumbası geçtiği için bayrak direği bumbaya çarpar; sancak
  denizde olduğu gibi gaf ucundan çekilir (SOCKET_FLAG_GAFF_PEAK). SOCKET_FLAG_STERN limanda bayrak direği
  seçeneği olarak kalır.
- Flama: kırlangıç kuyruklu, 8,0 × 0,5 m (TAHMİN), ana direk babafingo topuzunda (SOCKET_FLAG_MAIN_TRUCK).
Bayraklar dalgalı statik mesh (UE'de kumaş simülasyonuna uygun ızgara, orijin gönderde).
"""

import importlib.util
import json
import math
import sys
from pathlib import Path

import bpy  # noqa: I001
import bmesh
from mathutils import Matrix, Vector

HERE = Path(__file__).resolve().parent


def _load(name, fname):
    sp = importlib.util.spec_from_file_location(name, HERE / fname)
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


P15 = _load("pass_v015", "pass_v015_rigset.py")
P13, P5, H = P15.P13, P15.P5, P15.H
SRC_VER, VER = "v023", "v024"
ROOT, SHIP = H.ROOT, H.SHIP_ID
MANIFEST_VERSION = 21
P5.MANIFEST_VERSION = MANIFEST_VERSION
V = Vector


def image_material(name, rel, alpha=False):
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    path = ROOT / rel
    img = bpy.data.images.load(str(path), check_existing=True)
    img.filepath = bpy.path.relpath(str(path), start=str(ROOT / "Blender" / "versions"))
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    N, Lk = m.node_tree.nodes, m.node_tree.links
    b = N["Principled BSDF"]
    t = N.new("ShaderNodeTexImage")
    t.image = img
    Lk.new(t.outputs["Color"], b.inputs["Base Color"])
    if alpha:
        Lk.new(t.outputs["Alpha"], b.inputs["Alpha"])
    b.inputs["Roughness"].default_value = 0.85
    b.inputs["Subsurface Weight"].default_value = 0.05
    return m


def flag_mesh(name, w, h, mat, nu=24, nv=12, amp=0.18, waves=1.6, droop=0.0):
    """Yerel: gönder kenarı Z ekseninde (0..-h), bez -X yönünde uçar (kıça), dalga Y'de."""
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.verify()
    vs = []
    for j in range(nv + 1):
        v = j / nv
        row = []
        for i in range(nu + 1):
            u = i / nu
            x = -w * u
            y = amp * u * math.sin(2 * math.pi * (waves * u + 0.15 * v))
            z = -h * v - droop * u ** 2
            row.append(bm.verts.new((x, y, z)))
        vs.append(row)
    for j in range(nv):
        for i in range(nu):
            f = bm.faces.new([vs[j][i], vs[j + 1][i], vs[j + 1][i + 1], vs[j][i + 1]])
            for loop, (ii, jj) in zip(f.loops, ((i, j), (i, j + 1), (i + 1, j + 1), (i + 1, j))):
                loop[uvl].uv = (ii / nu, 1 - jj / nv)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mat)
    for p in me.polygons:
        p.use_smooth = True
    return me


def build(C, M):
    col, col_s = C["24_MODULES_DECOR"], C["30_SOCKETS"]
    ens_mat = image_material("MAT_Flag_OttomanNavy1793_A", "Textures/flags/T_Flag_OttomanNavy1793_A.png")
    pen_mat = image_material("MAT_Pennant_OttomanNavy_A", "Textures/flags/T_Pennant_OttomanNavy_A.png", alpha=True)
    # gaf ucu
    gaff = bpy.data.objects["MOD_RIG_GAFF_MIZZEN_A"]
    pts = [gaff.matrix_world @ v.co for v in gaff.data.vertices]
    p0 = gaff.matrix_world.translation
    peak = max(pts, key=lambda p: (p - p0).length)
    hoist = peak + V((0.0, 0.0, -0.35))
    ens = bpy.data.objects.new("MOD_FLAG_ENSIGN_OTTOMAN_A", flag_mesh("MOD_FLAG_ENSIGN_OTTOMAN_A", 3.6, 2.4, ens_mat))
    col.objects.link(ens)
    ens.location = hoist
    ens.rotation_euler = (0.0, 0.0, math.radians(-8.0))
    ens["module_family"] = "LanternFlagSet"
    ens["socket"] = "SOCKET_FLAG_GAFF_PEAK"
    ens["design"] = "kırmızı zemin, beyaz hilal + 8 köşeli yıldız (1793 biçimi) [İKİNCİL]"
    P13.set_socket("SOCKET_FLAG_GAFF_PEAK", hoist, col_s, shape="SINGLE_ARROW", size=0.4, module_family="LanternFlagSet",
                   accepts=["MOD_FLAG_*"])
    fs = bpy.data.objects["SOCKET_FLAG_STERN"]
    fs["note"] = "limanda bayrak direği seçeneği; denizde sancak gaf ucunda (bumba bu soketin üstünden geçer)"
    fs["manifest_version"] = MANIFEST_VERSION
    # halat: gaf ucu makarasından sancağın gönder kenarına
    br = bmesh.new()
    P15.tube(br, [peak, hoist + V((0.0, 0.0, 0.0)), hoist + V((0.0, 0.0, -2.4))], 0.010, seg=4)
    me = bpy.data.meshes.new("MOD_FLAG_ENSIGN_HALYARD")
    br.to_mesh(me)
    br.free()
    me.materials.append(M["rope"])
    hl = bpy.data.objects.new("MOD_FLAG_ENSIGN_HALYARD", me)
    col.objects.link(hl)
    hl["module_family"] = "LanternFlagSet"
    # flama: ana direk topuzu
    main = P15.Mast("MAIN")
    truck = P15.W(main.P(main.t_g1 - 0.05, main.fg))
    pen = bpy.data.objects.new("MOD_FLAG_PENNANT_OTTOMAN_A", flag_mesh("MOD_FLAG_PENNANT_OTTOMAN_A", 8.0, 0.5, pen_mat,
                                                                         nu=40, nv=3, amp=0.35, waves=2.4, droop=1.2))
    col.objects.link(pen)
    pen.location = truck
    pen.rotation_euler = (0.0, 0.0, math.radians(-10.0))
    pen["module_family"] = "LanternFlagSet"
    pen["socket"] = "SOCKET_FLAG_MAIN_TRUCK"
    P13.set_socket("SOCKET_FLAG_MAIN_TRUCK", truck, col_s, shape="SINGLE_ARROW", size=0.4, module_family="LanternFlagSet",
                   accepts=["MOD_FLAG_*"])
    return [ens, hl, pen], peak, truck


def render(sc):
    H.setup_render(sc, fast=True)
    out = ROOT / "renders" / VER
    out.mkdir(parents=True, exist_ok=True)
    e = bpy.data.objects["MOD_FLAG_ENSIGN_OTTOMAN_A"].location
    views = [
        ("sancak_yakin", e + V((-2.0, -9.0, -1.0)), e + V((-1.8, 0, -1.2)), 35),
        ("kic_omzu", V((-50, -37, 21)), V((0, 0, 14.2)), 32),
        ("bas_omzu", V((53, 42, 25)), V((0, 0, 14.2)), 32),
    ]
    for name, loc, tgt, lens in views:
        sc.camera = H.camera(sc, f"CAM24_{name}", loc, tgt, lens=lens)
        sc.render.filepath = str(out / f"{SHIP}_{VER}_{name}.png")
        bpy.ops.render.render(write_still=True)


def main():
    if "--render-only" in sys.argv:
        bpy.ops.wm.open_mainfile(filepath=str(ROOT / "Blender" / "versions" / f"{SHIP}_{VER}.blend"))
        return render(bpy.context.scene)
    out = ROOT / "Blender" / "versions" / f"{SHIP}_{VER}.blend"
    if out.exists():
        raise SystemExit(f"{out} zaten var; versiyonlu kayıt üzerine yazılmaz.")
    bpy.ops.wm.open_mainfile(filepath=str(ROOT / "Blender" / "versions" / f"{SHIP}_{SRC_VER}.blend"))
    sc = bpy.context.scene
    M = P15.materials()
    C = {c.name: c for c in bpy.data.collections}
    obs, peak, truck = build(C, M)
    bpy.ops.wm.save_as_mainfile(filepath=str(out), compress=True)
    H.VERSION = VER
    ap = ROOT / "reports" / f"scene_audit_{VER}.json"
    rep = H.audit(sc, ap)
    rep["flags_v024"] = {"objects": [o.name for o in obs], "gaff_peak_world": [round(v, 2) for v in peak],
                         "main_truck_world": [round(v, 2) for v in truck], "ensign_m": [3.6, 2.4], "pennant_m": [8.0, 0.5],
                         "textures": ["Textures/flags/T_Flag_OttomanNavy1793_A.png", "Textures/flags/T_Pennant_OttomanNavy_A.png"],
                         "note": "1793 donanma sancağı biçimi; gemi 1780 — küçük tarih farkı (oyun kararı)"}
    rep["pass"] = {"name": "pass_v024_flags", "source": f"Blender/versions/{SHIP}_{SRC_VER}.blend",
                   "manifest_version": MANIFEST_VERSION, "geometry_changed": "bayrak modülleri"}
    ap.write_text(json.dumps(rep, indent=2, ensure_ascii=False), encoding="utf-8")
    print("V024", json.dumps(rep["flags_v024"], ensure_ascii=False))
    if "--no-render" not in sys.argv:
        render(sc)


if __name__ == "__main__":
    main()
