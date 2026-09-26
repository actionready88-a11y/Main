"""v045 — Pruva figürü D: kullanıcının yeni "Kurt Gemi Figürü" (Meshy AI), yıldızlar silindi, bordaya gömülü ve büyük.

    python3.11 OTTOMAN_FRIGATE_1780_ISTANBUL/scripts/pass_v045_figurehead_kurt.py [--no-render | --render-only]

Kullanıcı kararları:
- "Figür bu gemideki gibi tam oturması lazım, emanet gibi durmayacak" (referans gemi görseli); seçenek "Bordaya
  dayalı, büyük": baş kıvrımı (CORE_HEAD_KNEE) kaldırılır, figür büyütülür, montaj bloğu bodoslamaya gömülür.
- "Yıldızı sil, hilal kalsın" (KIZIL_SANCAK_UYARLAMA_PLANI §0): alın + iki omuz ay-yıldızı → yalnız hilal
  (`figure_kurt_prep.py`: geometri kabartması düzlenir, BC/N/ORM dokuları zemine çekilir).
Kaynak: Imports/Meshy/Kurt Gemi Figürü.glb (kullanıcı üretimi; 3,0 M yüz, 4K BC + 4K N + 2K ORM). Lisans: Meshy
koşulları — ücretsiz plan CC BY 4.0 (atıf), ücretli plan kullanıcıya ait; plan kullanıcı tarafından doğrulanacak.
Yerleşim [TAHMİN, render ile ayarlandı]: yükseklik 3,0 m; bodoslama tırmığına uyum için 15° öne eğim; blok arka yüzü
bodoslamaya 10 cm gömülü; parmaklık kolları yeleye 6 cm girip biter.
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


def _load(name, file):
    sp = importlib.util.spec_from_file_location(name, HERE / file)
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


PT = _load("figmount_taslak", "pass_v04X_figurehead_mount_TASLAK.py")
P31 = PT.P31
RS, QA, LODS, H = P31.RS, P31.QA, P31.LODS, P31.H
ROOT, SHIP = P31.ROOT, P31.SHIP
SRC_VER, VER = "v044", "v045"
V = Vector
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT.parent / "skills" / "tersane" / "scripts"))
import figure_kurt_prep as FK  # noqa: E402
import lod_store  # noqa: E402

GLB = ROOT / "Imports" / "Meshy" / "Kurt Gemi Figürü.glb"
NAME = "MOD_FIGUREHEAD_KURT_D"
OLD = "MOD_FIGUREHEAD_BOZKURT_C"
HEIGHT = 3.0
PITCH_DEG = 15.0
BOTTOM_Z = 3.85
TARGET_TRIS = 450000
PT.EMBED = 0.10


def import_glb():
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(GLB))
    new = [o for o in bpy.data.objects if o not in before]
    ob = [o for o in new if o.type == "MESH"][0]
    for o in new:
        if o is not ob:
            bpy.data.objects.remove(o, do_unlink=True)
    ob.parent = None
    me = ob.data
    me.transform(ob.matrix_world)
    ob.matrix_world = Matrix.Identity(4)
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-5)
    bm.to_mesh(me)
    bm.free()
    return ob


def decimate(ob):
    me = ob.data
    me.calc_loop_triangles()
    t0 = len(me.loop_triangles)
    dc = ob.modifiers.new("Decimate", "DECIMATE")
    dc.decimate_type, dc.ratio = "COLLAPSE", min(1.0, TARGET_TRIS / max(t0, 1))
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
    return t0


def export_textures(ob, imgs):
    out = ROOT / "Textures" / "Figurehead"
    out.mkdir(parents=True, exist_ok=True)
    m = ob.data.materials[0]
    m.name = "MAT_Figure_KurtD"
    roles = {}
    for role, im in imgs.items():
        if im is None:
            continue
        path = out / f"T_Figure_KurtD_{role}.png"
        im.filepath_raw = str(path)
        im.file_format = "PNG"
        im.save()
        if im.packed_file:
            im.unpack(method="REMOVE")
        im.filepath = str(path)
        im.name = path.stem
        roles[role] = {"size": list(im.size), "file": str(path.relative_to(ROOT))}
    m["ue_note"] = "UE: BC (sRGB), N (OpenGL → UE'de yeşil kanal ters), ORM glTF düzeni: G pürüzlülük, B metal"
    return roles


def place(ob):
    """Ham: yüz −Y, blok +Y. Z +90° → yüz +X; ölçek; Y ekseninde öne eğim; blok bodoslamaya."""
    me = ob.data
    me.transform(Matrix.Rotation(math.radians(90), 4, "Z"))
    zs = [v.co.z for v in me.vertices]
    f = HEIGHT / (max(zs) - min(zs))
    me.transform(Matrix.Rotation(math.radians(PITCH_DEG), 4, "Y") @ Matrix.Scale(f, 4))
    xs = [v.co.x for v in me.vertices]
    ys = [v.co.y for v in me.vertices]
    zs = [v.co.z for v in me.vertices]
    back_x = PT.stem_front(BOTTOM_Z, BOTTOM_Z + HEIGHT * 0.5) - PT.EMBED
    me.transform(Matrix.Translation(V((back_x - min(xs), -(min(ys) + max(ys)) / 2, BOTTOM_Z - min(zs)))))
    me.update()
    ob.name = me.name = NAME
    return f


def block_contact(ob):
    """Blok arka yüzü ile bodoslama arası: arka 0,5 m içindeki köşelerden −X ışını; gömülü (içeride) / boşluk ölçümü."""
    o = bpy.data.objects["CORE_STEM"]
    dg = bpy.context.evaluated_depsgraph_get()
    ev = o.evaluated_get(dg).to_mesh()
    ts = BVHTree.FromPolygons([o.matrix_world @ v.co for v in ev.vertices], [tuple(p.vertices) for p in ev.polygons])
    o.evaluated_get(dg).to_mesh_clear()
    xmin = min(v.co.x for v in ob.data.vertices)
    gaps, inside = [], 0
    for v in ob.data.vertices:
        if v.co.x < xmin + 0.5 and abs(v.co.y) < 0.2:
            hit = ts.ray_cast(v.co + V((0.001, 0, 0)), V((-1, 0, 0)), 2.0)
            back = ts.ray_cast(v.co, V((1, 0, 0)), 2.0)
            if back[0] is not None and back[3] < 0.5 and hit[0] is not None and hit[3] > back[3]:
                inside += 1
            elif hit[0] is not None:
                gaps.append(hit[3])
    gaps.sort()
    return {"embedded_verts": inside, "gap_min_m": round(gaps[0], 3) if gaps else None,
            "gap_p90_m": round(gaps[int(len(gaps) * 0.9)], 3) if gaps else None}


def render(sc):
    H.setup_render(sc, fast=True)
    sc.cycles.samples = 48
    out = ROOT / "renders" / VER
    out.mkdir(parents=True, exist_ok=True)
    ob = bpy.data.objects[NAME]
    ws = [v.co for v in ob.data.vertices]
    c = V((sum(w.x for w in ws[::50]), sum(w.y for w in ws[::50]), sum(w.z for w in ws[::50]))) / len(ws[::50])
    for name, loc, tgt, lens in (("figur_yan", c + V((0.6, 8.0, 0.6)), c, 40),
                                 ("figur_on", c + V((6.5, 3.2, 1.2)), c, 40),
                                 ("figur_yakin", c + V((3.2, -2.2, 1.4)), c + V((0.4, 0, 0.6)), 35),
                                 ("figur_ust", c + V((-2.8, 1.6, 4.0)), c, 32),
                                 ("bas_omzu", V((34.0, 14.0, 9.0)), V((21.0, 0.0, 6.0)), 35)):
        sc.camera = H.camera(sc, f"CAM45_{name}", loc, tgt, lens=lens)
        sc.render.filepath = str(out / f"{SHIP}_{VER}_{name}.png")
        bpy.ops.render.render(write_still=True)


def main():
    main_out = ROOT / "Blender" / "versions" / f"{SHIP}_{VER}.blend"
    if "--render-only" in sys.argv:
        bpy.ops.wm.open_mainfile(filepath=str(main_out))
        return render(bpy.context.scene)
    if main_out.exists() or lod_store.lod_path(main_out).exists():
        raise SystemExit(f"{main_out} zaten var; versiyonlu kayıt üzerine yazılmaz.")
    src = ROOT / "Blender" / "versions" / f"{SHIP}_{SRC_VER}.blend"
    bpy.ops.wm.open_mainfile(filepath=str(src))
    sc = bpy.context.scene
    rep = {"lod_load": lod_store.load(src)}
    old = bpy.data.objects[OLD]
    col = old.users_collection[0]
    props = {k: old[k] for k in old.keys() if k in ("module_family", "socket")}
    rep["removed"] = PT.drop((OLD, "UCX_" + OLD, "CORE_HEAD_KNEE", "UCX_CORE_HEAD_KNEE"))
    for m in [m for m in bpy.data.materials if m.name.startswith("MAT_Figure_BozkurtC") and m.users == 0]:
        bpy.data.materials.remove(m)
    rep["rail_supports"] = PT.strip_rail_supports()
    ob = import_glb()
    for c in list(ob.users_collection):
        c.objects.unlink(ob)
    col.objects.link(ob)
    imgs = FK.material_images(ob)
    rep["stars"] = FK.remove_stars(ob, imgs)
    rep["textures"] = export_textures(ob, imgs)
    rep["tris_raw"] = decimate(ob)
    rep["scale"] = round(place(ob), 3)
    rep["stem_gap_closed_m"] = PT.seat_on_stem(ob)
    rep["block_contact"] = block_contact(ob)
    for k, v in props.items():
        ob[k] = v
    ob["motif"] = "zırhlı bozkurt — kükreyen baş, yele, oymalı zırh, uzanan pençeler; alın ve omuzlarda yalnız hilal"
    ob["source"] = "Meshy AI (kullanıcı üretimi, image-to-3D) — Imports/Meshy/" + GLB.name
    ob["license"] = "Meshy koşulları: ücretsiz plan → CC BY 4.0 (atıf 'Meshy AI'); ücretli plan → kullanıcıya ait. Kullanıcı doğrulayacak."
    ob["symbol_edit"] = "ay-yıldızdaki yıldızlar silindi (alın, iki omuz); hilal kaldı — Yüzde Yetmiş Özgünlük Kuralı"
    ob["quality"] = f"hero; ham {rep['tris_raw'] // 1000}k → {TARGET_TRIS // 1000}k üçgen (COLLAPSE), Meshy normal haritası detay taşır"
    me = ob.data
    pts = [v.co.copy() for v in me.vertices]
    xs, ys, zs = [p.x for p in pts], [p.y for p in pts], [p.z for p in pts]
    rep["bbox"] = [[round(min(xs), 2), round(min(ys), 2), round(min(zs), 2)], [round(max(xs), 2), round(max(ys), 2), round(max(zs), 2)]]
    rep["size_m"] = [round(max(xs) - min(xs), 2), round(max(ys) - min(ys), 2), round(max(zs) - min(zs), 2)]
    s = bpy.data.objects.get("SOCKET_FIGUREHEAD")
    if s:
        s.location = V((min(xs) + PT.EMBED, 0.0, BOTTOM_Z + HEIGHT * 0.3))
        s["installed_module"] = NAME
        s["mount"] = "bodoslama ön kenarı (v045; baş kıvrımı kaldırıldı)"
        rep["socket"] = [round(c, 2) for c in s.location]
    geom = __import__("geom")
    step = max(1, len(pts) // 3000)
    u = geom.convex_ucx(f"UCX_{NAME}_00", pts[::step], bpy.data.collections["40_COLLISION"], "figurehead", owner=NAME)
    rep["ucx_verts"] = len(u.data.vertices)
    dg = bpy.context.evaluated_depsgraph_get()
    dg.update()

    def tree(n):
        o = bpy.data.objects[n]
        ev = o.evaluated_get(dg).to_mesh()
        t = BVHTree.FromPolygons([o.matrix_world @ v.co for v in ev.vertices], [tuple(p.vertices) for p in ev.polygons])
        o.evaluated_get(dg).to_mesh_clear()
        return t
    tb = tree("MOD_RIG_BOWSPRIT_A")
    rep["min_gap_to_bowsprit_m"] = round(min(tb.find_nearest(p, 9.0)[3] for p in pts[::40]), 3)
    tf = BVHTree.FromPolygons(pts, [tuple(p.vertices) for p in me.polygons])
    rep["rail_trim"] = PT.trim_rails(tf)
    rails = {}
    for sd in ("S", "P"):
        r = bpy.data.objects[f"CORE_HEAD_RAIL_{sd}"]
        vs = [r.matrix_world @ v.co for v in r.data.vertices]
        fwd = max(vs, key=lambda p: p.x)
        rt = BVHTree.FromPolygons(vs, [tuple(p.vertices) for p in r.data.polygons])
        rails[sd] = {"front_x": round(fwd.x, 2), "front_to_figure_m": round(tf.find_nearest(fwd, 9.0)[3], 3),
                     "touches_figure": bool(rt.overlap(tf))}
    rep["head_rails"] = rails
    for n in (NAME, OLD, "CORE_HEAD_RAIL_S", "CORE_HEAD_RAIL_P", "CORE_HEAD_KNEE"):
        PT.drop((n + "_LOD",))
    LODS.build_lods(sc, only={NAME, "CORE_HEAD_RAIL_S", "CORE_HEAD_RAIL_P"})
    me.calc_loop_triangles()
    rep["tris"] = len(me.loop_triangles)
    H.VERSION = VER
    ap = ROOT / "reports" / f"scene_audit_{VER}.json"
    arep = H.audit(sc, ap)
    arep["figurehead_v045"] = rep
    arep["pass"] = {"name": "pass_v045_figurehead_kurt", "source": f"Blender/versions/{SHIP}_{SRC_VER}.blend"}
    qa = QA.audit(sc, top=60)
    (ROOT / "reports" / f"kalite_testi_{VER}.json").write_text(json.dumps(qa, indent=1, ensure_ascii=False), encoding="utf-8")
    rep["save"] = lod_store.save_split(main_out)
    ap.write_text(json.dumps(arep, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    r = next(x for x in qa["objects"] if x["name"] == NAME)
    print("V045", json.dumps(rep, ensure_ascii=False, default=str))
    print("V045 QA", json.dumps(qa["summary"], ensure_ascii=False), "figür:", r["fail"], r["facet_m"], r["worst_sag_mm"], r["floating_islands"][:3])
    for x in [x for x in qa["objects"] if x["fail"] or x["floating_islands"]]:
        print(f"  HATA {x['name']} facet={x['facet_m']}m sag={x['worst_sag_mm']}mm havada={x['floating_islands'][:3]}")
    if "--no-render" not in sys.argv:
        render(sc)


if __name__ == "__main__":
    main()
