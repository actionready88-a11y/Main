"""v039 — Bozkurt pruva figürü C: kullanıcının Meshy AI modeli (Imports/Meshy/*.glb).

    python3.11 OTTOMAN_FRIGATE_1780_ISTANBUL/scripts/pass_v039_figurehead_meshy.py [--no-render | --render-only]

Kaynak: kullanıcı Meshy AI "image-to-3D" ile üretti ve depoya yükledi (2026-09-26). Lisans: Meshy kullanım koşullarına
bağlı — ücretsiz planla üretilen varlık CC BY 4.0 (atıf: "Meshy AI"), ücretli planla üretilen kullanıcıya ait
[İKİNCİL: Meshy kullanım koşulları; plan kullanıcı tarafından doğrulanacak]. Lisanslı Fab varlığı değildir.
Ham GLB: 2,40 M üçgen, 930 ada (glTF UV dikişlerinde köşe ayrımı; 1e-5 m birleştirmeyle tek ada), 4K BC + 4K normal
+ 2K ORM (metal/pürüzlülük). Yön: yüz −Y, montaj plakası +Y; boyut 1,90 × 0,72 × 1,50 m.
İşlem: köşe birleştirme → COLLAPSE azaltma (hero bütçe 250k üçgen; UV/doku korunur) → Z +90° (yüz +X, pruva) →
×1,25 (≈ 2,38 × 0,90 × 1,88 m; v036 figürü 2,18 × 1,0 × 1,6 m) → plaka baş kıvrımına oturtulur. Dokular
Textures/Figurehead/T_Figure_BozkurtC_{BC,N,ORM}.png olarak dışarı yazılır (blend'e gömülmez).
"""

import importlib.util
import json
import math
import sys
from pathlib import Path

import bpy  # noqa: I001
import bmesh
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

HERE = Path(__file__).resolve().parent
sp = importlib.util.spec_from_file_location("pass_v035", HERE / "pass_v035_figurehead_bozkurt_b2.py")
P35 = importlib.util.module_from_spec(sp)
sp.loader.exec_module(P35)
P31 = P35.P31
RS, QA, LODS, H = P31.RS, P31.QA, P31.LODS, P31.H
ROOT, SHIP = P31.ROOT, P31.SHIP
SRC_VER, VER = "v038", "v039"
V = Vector
GLB = ROOT / "Imports" / "Meshy" / "Meshy_AI_ottoman_wolf_prow_fig_0926123443_image-to-3d-texture.glb"
NAME = "MOD_FIGUREHEAD_BOZKURT_C"
O = P35.O                                   # SOCKET_FIGUREHEAD (24,25; 0; 5,55)
TARGET_TRIS = 250000
SCALE = 1.25
BACK_X = O.x - 0.95                          # plakanın arka ucu (baş kıvrımına gömülü) [TAHMİN, render ile ayarlandı]
BOTTOM_Z = O.z - 0.55                        # plaka alt ucu


def import_glb():
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(GLB))
    new = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in new if o.type == "MESH"]
    ob = meshes[0]
    for o in new:
        if o is not ob:
            bpy.data.objects.remove(o, do_unlink=True)
    ob.parent = None
    return ob


def clean_and_decimate(ob):
    me = ob.data
    raw = len(me.polygons)
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-5)
    bm.to_mesh(me)
    bm.free()
    me.calc_loop_triangles()
    tris0 = len(me.loop_triangles)
    dc = ob.modifiers.new("Decimate", "DECIMATE")
    dc.decimate_type, dc.ratio = "COLLAPSE", min(1.0, TARGET_TRIS / max(tris0, 1))
    dc.use_collapse_triangulate = True
    dg = bpy.context.evaluated_depsgraph_get()
    dg.update()
    out = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    ob.modifiers.clear()
    old = ob.data
    ob.data = out
    bpy.data.meshes.remove(old)
    for p in out.polygons:
        p.use_smooth = True
    return {"raw_faces": raw, "tris_after_merge": tris0}


def place(ob):
    # yüz −Y → +X : Z ekseni etrafında +90°; ölçek; dönüşümü mesh'e uygula
    ob.data.transform(Matrix.Rotation(math.radians(90), 4, "Z") @ Matrix.Scale(SCALE, 4))
    xs = [v.co.x for v in ob.data.vertices]
    zs = [v.co.z for v in ob.data.vertices]
    ys = [v.co.y for v in ob.data.vertices]
    off = V((BACK_X - min(xs), -(min(ys) + max(ys)) / 2, BOTTOM_Z - min(zs)))
    ob.data.transform(Matrix.Translation(off))
    ob.matrix_world = Matrix.Identity(4)
    ob.name = ob.data.name = NAME


def export_textures(ob):
    out = ROOT / "Textures" / "Figurehead"
    out.mkdir(parents=True, exist_ok=True)
    m = ob.data.materials[0]
    m.name = "MAT_Figure_BozkurtC"
    roles = {}
    nt = m.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    for n in nt.nodes:
        if n.type != "TEX_IMAGE" or not n.image:
            continue
        link_to = [lk.to_node for lk in nt.links if lk.from_node == n]
        if any(t.type == "NORMAL_MAP" for t in link_to):
            role = "N"
        elif any(t.type == "SEPARATE_COLOR" for t in link_to):
            role = "ORM"
        elif bsdf in link_to:
            role = "BC"
        else:
            role = n.image.name
        path = out / f"T_Figure_BozkurtC_{role}.png"
        im = n.image
        im.filepath_raw = str(path)
        im.file_format = "PNG"
        im.save()
        if im.packed_file:
            im.unpack(method="REMOVE")
        im.filepath = str(path)
        im.name = path.stem
        roles[role] = {"size": list(im.size), "file": str(path.relative_to(ROOT))}
    m["ue_note"] = "UE: BC (sRGB), N (OpenGL → UE'de yeşil kanal ters), ORM kanalları glTF düzeni: G pürüzlülük, B metal"
    return roles


def render(sc):
    P35.VER = VER
    return P35.render(sc)


def main():
    if "--render-only" in sys.argv:
        bpy.ops.wm.open_mainfile(filepath=str(ROOT / "Blender" / "versions" / f"{SHIP}_{VER}.blend"))
        return render(bpy.context.scene)
    out = ROOT / "Blender" / "versions" / f"{SHIP}_{VER}.blend"
    if out.exists():
        raise SystemExit(f"{out} zaten var; versiyonlu kayıt üzerine yazılmaz.")
    bpy.ops.wm.open_mainfile(filepath=str(ROOT / "Blender" / "versions" / f"{SHIP}_{SRC_VER}.blend"))
    sc = bpy.context.scene
    old = bpy.data.objects["MOD_FIGUREHEAD_BOZKURT_B"]
    col = old.users_collection[0]
    props = {k: v for k, v in old.items() if k in ("module_family", "socket")}
    for o in [o for o in bpy.data.objects if o.name.startswith(("MOD_FIGUREHEAD_BOZKURT_", "UCX_MOD_FIGUREHEAD_BOZKURT_"))]:
        me = o.data
        bpy.data.objects.remove(o, do_unlink=True)
        if me is not None and me.users == 0:
            bpy.data.meshes.remove(me)
    ob = import_glb()
    for c in list(ob.users_collection):
        c.objects.unlink(ob)
    col.objects.link(ob)
    rep = clean_and_decimate(ob)
    place(ob)
    rep["textures"] = export_textures(ob)
    for k, v in props.items():
        ob[k] = v
    ob["motif"] = "bozkurt — hırlayan baş, yele, oymalı zırh, pençeler, hilal motifli montaj plakası"
    ob["source"] = "Meshy AI (kullanıcı üretimi, image-to-3D) — Imports/Meshy/" + GLB.name
    ob["license"] = "Meshy koşulları: ücretsiz plan → CC BY 4.0 (atıf 'Meshy AI'); ücretli plan → kullanıcıya ait. Kullanıcı doğrulayacak."
    ob["quality"] = f"hero; ham 2,40 M → {TARGET_TRIS // 1000}k üçgen (COLLAPSE), Meshy normal haritası detay taşır"
    s = bpy.data.objects.get("SOCKET_FIGUREHEAD")
    if s:
        s["installed_module"] = NAME
    me = ob.data
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.faces.index_update()
    rep["islands"] = len(RS.islands(bm))
    rep["boundary_edges"] = sum(1 for e in bm.edges if e.is_boundary)
    bm.free()
    geom = __import__("geom")
    pts = [v.co.copy() for v in me.vertices]
    step = max(1, len(pts) // 3000)
    u = geom.convex_ucx(f"UCX_{NAME}_00", pts[::step], bpy.data.collections["40_COLLISION"], "figurehead", owner=NAME)
    rep["ucx_verts"] = len(u.data.vertices)
    # cıvadıra ve baş kıvrımı ile ilişki
    dg = bpy.context.evaluated_depsgraph_get()

    def tree(n):
        o = bpy.data.objects[n]
        ev = o.evaluated_get(dg).to_mesh()
        t = BVHTree.FromPolygons([o.matrix_world @ v.co for v in ev.vertices], [tuple(p.vertices) for p in ev.polygons])
        o.evaluated_get(dg).to_mesh_clear()
        return t
    tb, ts = tree("MOD_RIG_BOWSPRIT_A"), tree("CORE_STEM")
    rep["min_gap_to_bowsprit_m"] = round(min(tb.find_nearest(p, 5.0)[3] for p in pts[::50]), 3)
    rep["min_gap_to_stem_m"] = round(min(ts.find_nearest(p, 5.0)[3] for p in pts[::50]), 3)
    tf = BVHTree.FromPolygons(pts, [tuple(p.vertices) for p in me.polygons])
    rails = {}
    for sd in ("S", "P"):
        r = bpy.data.objects[f"CORE_HEAD_RAIL_{sd}"]
        vs = [r.matrix_world @ v.co for v in r.data.vertices]
        fwd = max(vs, key=lambda p: p.x)
        rails[sd] = round(tf.find_nearest(fwd, 5.0)[3], 3)
    rep["head_rail_front_to_figure_m"] = rails
    xs, ys, zs = [p.x for p in pts], [p.y for p in pts], [p.z for p in pts]
    rep["bbox"] = [[round(min(xs), 2), round(min(ys), 2), round(min(zs), 2)], [round(max(xs), 2), round(max(ys), 2), round(max(zs), 2)]]
    for o in [o for o in bpy.data.objects if o.name.startswith(NAME + "_LOD")]:
        bpy.data.objects.remove(o, do_unlink=True)
    LODS.build_lods(sc, only={NAME})
    me.calc_loop_triangles()
    rep["tris"] = len(me.loop_triangles)
    bpy.ops.wm.save_as_mainfile(filepath=str(out), compress=True)
    H.VERSION = VER
    ap = ROOT / "reports" / f"scene_audit_{VER}.json"
    arep = H.audit(sc, ap)
    arep["figurehead_v039"] = rep
    arep["pass"] = {"name": "pass_v039_figurehead_meshy", "source": f"Blender/versions/{SHIP}_{SRC_VER}.blend"}
    ap.write_text(json.dumps(arep, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    qa = QA.audit(sc, top=60)
    (ROOT / "reports" / f"kalite_testi_{VER}.json").write_text(json.dumps(qa, indent=1, ensure_ascii=False), encoding="utf-8")
    r = next(x for x in qa["objects"] if x["name"] == NAME)
    print("V039", json.dumps(rep, ensure_ascii=False, default=str))
    print("V039 QA", json.dumps(qa["summary"], ensure_ascii=False), "figür:", r["fail"], r["facet_m"], r["worst_sag_mm"], r["floating_islands"][:3])
    if "--no-render" not in sys.argv:
        render(sc)


if __name__ == "__main__":
    main()
