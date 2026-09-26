"""Pass v021 — Pruva figürü: Bozkurt (MOD_FIGUREHEAD_BOZKURT_A), v020 üzerine.

Çalıştırma (depo kökünden):
    python3 OTTOMAN_FRIGATE_1780_ISTANBUL/scripts/pass_v021_figurehead_bozkurt.py [--no-render | --render-only]

Kullanıcı (2026-09-26): "figürü bozkurt ile değiştirebiliriz, Türklerin simgesi".
Not: v020'ye kadar gemide figür yoktu; yalnız baş kıvrımı (CORE_HEAD_KNEE) ve boş SOCKET_FIGUREHEAD vardı.
Yapım: iskelet (skin modifier) → alt bölümleme → oyma dokusu (displace) → tek mesh. Ağızı açık, kulakları dik,
ön ayakları baş kıvrımının üstündeki yaldızlı kaideye basan gri kurt büstü; gözler, dişler, dil ayrı malzeme.
Kaide yaldızlı (gemideki süslemelerle aynı malzeme). Boy yaklaşık 2,1 m (TAHMİN; cıvadıranın altında kalır).
DURUM: blockout (yer tutucu). Skin-modifier yöntemi heykel kalitesine ulaşmadı; soket, ölçü ve malzeme
yuvaları nihai model için hazır.
Tarihsel not: bozkurt figürü bu gemi için oyun/tasarım kararıdır, dönem kaynağı yok.
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


P13 = _load("pass_v013", "pass_v013_hull_b_lower_deck.py")
P5, H, C3 = P13.P5, P13.H, P13.C3
SRC_VER, VER = "v020", "v021"
ROOT, SHIP = H.ROOT, H.SHIP_ID
MANIFEST_VERSION = 18
P5.MANIFEST_VERSION = MANIFEST_VERSION
V = Vector
ORIGIN = V((24.25, 0.0, 5.55))    # baş kıvrımının üst ucu (dünya; v020 ölçümü)
SC = 1.15

# iskelet: (ad, konum (yerel, ölçeksiz), yarıçap x, yarıçap y)
NODES = {
    "base": ((0.00, 0.00, 0.00), 0.36, 0.33),
    "chest": ((0.24, 0.00, 0.30), 0.40, 0.36),
    "neck0": ((0.46, 0.00, 0.62), 0.36, 0.33),
    "neck1": ((0.66, 0.00, 0.86), 0.32, 0.30),
    "mane": ((0.52, 0.00, 0.90), 0.30, 0.34),
    "skull": ((0.88, 0.00, 1.02), 0.30, 0.27),
    "brow": ((1.07, 0.00, 1.07), 0.20, 0.19),
    "muzzle": ((1.24, 0.00, 1.01), 0.14, 0.13),
    "nose": ((1.40, 0.00, 0.98), 0.095, 0.09),
    "jaw0": ((0.96, 0.00, 0.90), 0.16, 0.14),
    "jaw1": ((1.16, 0.00, 0.84), 0.10, 0.09),
    "jaw2": ((1.32, 0.00, 0.80), 0.07, 0.065),
    "ruffS": ((0.66, 0.20, 0.82), 0.22, 0.16),
    "ruffP": ((0.66, -0.20, 0.82), 0.22, 0.16),
    "cheekS": ((0.94, 0.17, 0.97), 0.13, 0.11),
    "cheekP": ((0.94, -0.17, 0.97), 0.13, 0.11),
    "earS0": ((0.80, 0.15, 1.24), 0.10, 0.06),
    "earS1": ((0.74, 0.19, 1.50), 0.035, 0.025),
    "earP0": ((0.80, -0.15, 1.24), 0.10, 0.06),
    "earP1": ((0.74, -0.19, 1.50), 0.035, 0.025),
    "shS": ((0.34, 0.22, 0.16), 0.17, 0.14),
    "elS": ((0.46, 0.25, -0.02), 0.12, 0.11),
    "pawS": ((0.58, 0.24, -0.08), 0.11, 0.10),
    "shP": ((0.34, -0.22, 0.16), 0.17, 0.14),
    "elP": ((0.46, -0.25, -0.02), 0.12, 0.11),
    "pawP": ((0.58, -0.24, -0.08), 0.11, 0.10),
}
EDGES = [("base", "chest"), ("chest", "neck0"), ("neck0", "neck1"), ("neck1", "skull"), ("neck0", "mane"), ("skull", "brow"), ("brow", "muzzle"),
         ("muzzle", "nose"), ("skull", "jaw0"), ("jaw0", "jaw1"), ("jaw1", "jaw2"), ("neck0", "ruffS"), ("neck0", "ruffP"),
         ("skull", "cheekS"), ("skull", "cheekP"), ("skull", "earS0"), ("earS0", "earS1"), ("skull", "earP0"), ("earP0", "earP1"),
         ("chest", "shS"), ("shS", "elS"), ("elS", "pawS"), ("chest", "shP"), ("shP", "elP"), ("elP", "pawP")]


def wolf_material():
    name = "MAT_Figure_WolfGrey"
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    N, Lk = m.node_tree.nodes, m.node_tree.links
    b = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord")
    geo = N.new("ShaderNodeNewGeometry")
    sep = N.new("ShaderNodeSeparateXYZ")
    Lk.new(geo.outputs["Normal"], sep.inputs[0])
    ramp = N.new("ShaderNodeValToRGB")                 # sırt koyu, göğüs/alt açık gri
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = (0.30, 0.30, 0.31, 1)
    ramp.color_ramp.elements[1].position = 1.0
    ramp.color_ramp.elements[1].color = (0.11, 0.105, 0.10, 1)
    mr = N.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = -1.0
    Lk.new(sep.outputs["Z"], mr.inputs["Value"])
    Lk.new(mr.outputs["Result"], ramp.inputs["Fac"])
    noise = N.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 40.0
    noise.inputs["Detail"].default_value = 6.0
    Lk.new(tc.outputs["Object"], noise.inputs["Vector"])
    mix = N.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.blend_type = "MULTIPLY"
    mix.inputs["Factor"].default_value = 0.35
    Lk.new(ramp.outputs["Color"], mix.inputs["A"])
    Lk.new(noise.outputs["Color"], mix.inputs["B"])
    Lk.new(mix.outputs["Result"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.55
    return m


def simple(name, color, rough=0.4, metal=0.0):
    if name not in bpy.data.materials:
        H.principled(name, color, rough=rough, metal=metal)
    return bpy.data.materials[name]


def build_body(col):
    me = bpy.data.meshes.new("_wolf_skel")
    names = list(NODES)
    me.from_pydata([NODES[n][0] for n in names], [(names.index(a), names.index(b)) for a, b in EDGES], [])
    ob = bpy.data.objects.new("_wolf_skel", me)
    col.objects.link(ob)
    sk = ob.modifiers.new("Skin", "SKIN")
    sk.use_smooth_shade = True
    sk.branch_smoothing = 0.6
    sv = me.skin_vertices[0].data
    for i, n in enumerate(names):
        sv[i].radius = (NODES[n][1], NODES[n][2])
        sv[i].use_root = (n == "base")
    sub = ob.modifiers.new("Sub", "SUBSURF")
    sub.levels = 3
    sub.render_levels = 3
    sm = ob.modifiers.new("Smooth", "SMOOTH")
    sm.factor = 0.8
    sm.iterations = 6
    tex = bpy.data.textures.new("TEX_WolfFur", "WOOD")
    tex.wood_type = "BANDNOISE"
    tex.noise_basis_2 = "SIN"
    tex.turbulence = 18.0
    tex.noise_scale = 0.03
    disp = ob.modifiers.new("Fur", "DISPLACE")
    disp.texture = tex
    disp.texture_coords = "LOCAL"
    disp.strength = 0.007
    disp.mid_level = 0.5
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    body = bpy.data.meshes.new_from_object(ev)
    bpy.data.objects.remove(ob, do_unlink=True)
    bpy.data.meshes.remove(me)
    bpy.data.textures.remove(tex)
    return body


def build_details():
    b_eye, b_teeth, b_tongue, b_nose = bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new()
    for s in (1, -1):
        r = bmesh.ops.create_uvsphere(b_eye, u_segments=16, v_segments=10, radius=0.04)
        bmesh.ops.translate(b_eye, vec=(1.07, s * 0.140, 1.115), verts=r["verts"])
        for k in range(5):                                           # üst dişler (kesici + köpek)
            t = k / 4
            p = V((1.40 - 0.28 * t, s * (0.035 + 0.075 * t), 0.935 - 0.01 * t))
            ln = 0.09 if k == 1 else 0.04
            r = bmesh.ops.create_cone(b_teeth, cap_ends=True, segments=6, radius1=0.014 if k == 1 else 0.010, radius2=0.001, depth=ln)
            bmesh.ops.translate(b_teeth, vec=(0, 0, -ln / 2), verts=r["verts"])
            bmesh.ops.translate(b_teeth, vec=p, verts=r["verts"])
        for k in range(4):                                           # alt dişler
            t = k / 3
            p = V((1.34 - 0.26 * t, s * (0.03 + 0.05 * t), 0.835 + 0.03 * t))
            ln = 0.07 if k == 1 else 0.035
            r = bmesh.ops.create_cone(b_teeth, cap_ends=True, segments=6, radius1=0.012 if k == 1 else 0.009, radius2=0.001, depth=ln)
            bmesh.ops.translate(b_teeth, vec=(0, 0, ln / 2), verts=r["verts"])
            bmesh.ops.translate(b_teeth, vec=p, verts=r["verts"])
    r = bmesh.ops.create_uvsphere(b_tongue, u_segments=12, v_segments=8, radius=1.0)
    bmesh.ops.scale(b_tongue, vec=(0.16, 0.055, 0.025), verts=r["verts"])
    bmesh.ops.translate(b_tongue, vec=(1.16, 0.0, 0.88), verts=r["verts"])
    r = bmesh.ops.create_uvsphere(b_nose, u_segments=14, v_segments=8, radius=1.0)
    bmesh.ops.scale(b_nose, vec=(0.05, 0.065, 0.045), verts=r["verts"])
    bmesh.ops.translate(b_nose, vec=(1.395, 0.0, 1.0), verts=r["verts"])
    return b_eye, b_teeth, b_tongue, b_nose


def build_plinth():
    """Yaldızlı kaide: baş kıvrımının ucunu saran kıvrık konsol + akantus şeritleri."""
    bm = bmesh.new()
    P5.lathe(bm, [(0.0, -0.45), (0.30, -0.45), (0.36, -0.40), (0.33, -0.34), (0.40, -0.30), (0.42, -0.24), (0.36, -0.20),
                  (0.30, -0.12), (0.0, -0.10)], 24, Matrix.Scale(1.0, 4) @ Matrix.Diagonal((1.45, 1.0, 1.0, 1.0)))
    for s in (1, -1):                                               # iki yanda volüt (kıvrım)
        pts = []
        for k in range(30):
            a = 2.6 * math.pi * k / 29
            r = 0.16 * (1 - k / 40)
            pts.append(V((0.05 + r * math.cos(a), s * 0.36, -0.28 + r * math.sin(a))))
        tube_rect(bm, pts, 0.05)
    return bm


def tube_rect(bm, pts, r):
    rings = []
    for i, p in enumerate(pts):
        a = pts[max(i - 1, 0)]
        b = pts[min(i + 1, len(pts) - 1)]
        t = (b - a).normalized()
        u = V((0, 1, 0))
        w = t.cross(u).normalized()
        rings.append([bm.verts.new(p + (u * math.cos(2 * math.pi * k / 8) + w * math.sin(2 * math.pi * k / 8)) * r) for k in range(8)])
    for r0, r1 in zip(rings[:-1], rings[1:]):
        for k in range(8):
            bm.faces.new([r0[k], r0[(k + 1) % 8], r1[(k + 1) % 8], r1[k]])


def build_figure(C, M):
    body = build_body(C["24_MODULES_DECOR"])
    parts = []
    bb = bmesh.new()
    bb.from_mesh(body)
    bpy.data.meshes.remove(body)
    eye, teeth, tongue, nose = build_details()
    plinth = build_plinth()
    mats = [M["wolf"], M["eye"], M["tooth"], M["tongue"], M["noseblack"], M["gold"]]
    merged = bmesh.new()
    for idx, b in enumerate((bb, eye, teeth, tongue, nose, plinth)):
        b.transform(Matrix.Scale(SC, 4))
        bmesh.ops.recalc_face_normals(b, faces=b.faces)
        tmp = bpy.data.meshes.new("_tmp")
        b.to_mesh(tmp)
        b.free()
        tmp.polygons.foreach_set("material_index", [idx] * len(tmp.polygons))
        merged.from_mesh(tmp)
        bpy.data.meshes.remove(tmp)
    me = bpy.data.meshes.new("MOD_FIGUREHEAD_BOZKURT_A")
    merged.to_mesh(me)
    merged.free()
    for m in mats:
        me.materials.append(m)
    for p in me.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new("MOD_FIGUREHEAD_BOZKURT_A", me)
    C["24_MODULES_DECOR"].objects.link(ob)
    tmp = bpy.data.objects.new("_tmp_uv", me)
    H.build_uv_fallback(tmp)
    bpy.data.objects.remove(tmp)
    ob.location = ORIGIN
    ob["module_family"] = "Figurehead"
    ob["socket"] = "SOCKET_FIGUREHEAD"
    ob["motif"] = "bozkurt (kullanıcı kararı; tasarım, dönem kaynağı yok)"
    ob["quality"] = "blockout — prosedürel yer tutucu; nihai heykel (sculpt/AI 3D/hazır varlık) ile değiştirilecek"
    s = bpy.data.objects["SOCKET_FIGUREHEAD"]
    old = [round(v, 3) for v in s.location]
    s.location = ORIGIN
    s["installed_module"] = ob.name
    s["manifest_version"] = MANIFEST_VERSION
    return ob, old


def clearance(ob):
    bs = bpy.data.objects["MOD_RIG_BOWSPRIT_A"]
    bp = [bs.matrix_world @ v.co for v in bs.data.vertices]
    fp = [ob.matrix_world @ v.co for v in ob.data.vertices]
    worst = 1e9
    for p in fp[::7]:
        near = [q for q in bp if abs(q.x - p.x) < 0.15]
        if near:
            worst = min(worst, min(q.z for q in near) - p.z)
    return round(worst, 3), [round(v, 2) for v in (max(p.x for p in fp), max(p.z for p in fp))]


def render(sc):
    H.setup_render(sc, fast=True)
    out = ROOT / "renders" / VER
    out.mkdir(parents=True, exist_ok=True)
    o = ORIGIN
    views = [
        ("bozkurt_yan", o + V((1.0, 6.5, 1.2)), o + V((1.0, 0, 0.9)), 45),
        ("bozkurt_on", o + V((6.0, 3.0, 1.8)), o + V((1.2, 0, 1.0)), 40),
        ("bozkurt_yakin", o + V((3.6, 1.6, 2.2)), o + V((1.8, 0, 1.3)), 35),
        ("bas_omzu", V((48, 38, 22)) * 1.1 + V((0, 0, 1.0)), V((0, 0, 12)) * 1.1 + V((0, 0, 1.0)), 32),
    ]
    for name, loc, tgt, lens in views:
        sc.camera = H.camera(sc, f"CAM21_{name}", loc, tgt, lens=lens)
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
    M = P5.ensure_materials()
    M["wolf"] = wolf_material()
    M["eye"] = simple("MAT_Figure_EyeAmber", (0.55, 0.30, 0.04), rough=0.15)
    M["tooth"] = simple("MAT_Figure_Ivory", (0.75, 0.70, 0.58), rough=0.35)
    M["tongue"] = simple("MAT_Figure_Tongue", (0.40, 0.06, 0.06), rough=0.45)
    M["noseblack"] = simple("MAT_Figure_NoseBlack", (0.015, 0.014, 0.014), rough=0.3)
    C = {c.name: c for c in bpy.data.collections}
    ob, old = build_figure(C, M)
    bpy.context.view_layer.update()
    u = C3.convex("UCX_MOD_FIGUREHEAD_BOZKURT_A_00", [ob.matrix_world @ v.co for v in ob.data.vertices][::25], C["40_COLLISION"], "figurehead")
    u.name = u.data.name = "UCX_MOD_FIGUREHEAD_BOZKURT_A_00"
    u["owner_mesh"] = ob.name
    if len(u.data.vertices) > 64:                                  # köşe sınırı: seyrelt
        pts = [u.matrix_world @ v.co for v in u.data.vertices][::max(len(u.data.vertices) // 48, 2)]
        me = u.data
        bpy.data.objects.remove(u, do_unlink=True)
        bpy.data.meshes.remove(me)
        u = C3.convex("UCX_MOD_FIGUREHEAD_BOZKURT_A_00", pts, C["40_COLLISION"], "figurehead")
        u.name = u.data.name = "UCX_MOD_FIGUREHEAD_BOZKURT_A_00"
        u["owner_mesh"] = ob.name
    gap, ext = clearance(ob)
    bpy.ops.wm.save_as_mainfile(filepath=str(out), compress=True)
    H.VERSION = VER
    ap = ROOT / "reports" / f"scene_audit_{VER}.json"
    rep = H.audit(sc, ap)
    ob.data.calc_loop_triangles()
    rep["figurehead_v021"] = {"module": ob.name, "tris": len(ob.data.loop_triangles), "socket_from": old,
                              "socket_to": [round(v, 3) for v in ORIGIN], "min_gap_to_bowsprit_m": gap,
                              "front_top_world": ext, "ucx_verts": len(u.data.vertices)}
    rep["pass"] = {"name": "pass_v021_figurehead_bozkurt", "source": f"Blender/versions/{SHIP}_{SRC_VER}.blend",
                   "manifest_version": MANIFEST_VERSION, "geometry_changed": "figür modülü eklendi"}
    ap.write_text(json.dumps(rep, indent=2, ensure_ascii=False), encoding="utf-8")
    print("V021", json.dumps(rep["figurehead_v021"], ensure_ascii=False))
    if "--no-render" not in sys.argv:
        render(sc)


if __name__ == "__main__":
    main()
