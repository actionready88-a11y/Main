"""v040 — bozkurt figürü C bordaya dayalı, büyük; baş kıvrımı kaldırıldı.

    python3.11 OTTOMAN_FRIGATE_1780_ISTANBUL/scripts/pass_v040_figurehead_mount.py [--no-render | --render-only]

Kullanıcı (v039 ekran görüntüsü): "çok küçük duruyor, alt tarafındaki parçayı kaldırıp tam o iç kısma sığdıracak
şekilde büyüt" → seçenek: "Bordaya dayalı, büyük".
 1. CORE_HEAD_KNEE (baş kıvrımı, x 20,4–24,8 m) ve LOD/UCX'leri kaldırılır.
 2. Baş parmaklıklarının kıvrıma inen destekleri (her yanda 2 dikme adası) kaldırılır; parmaklık kolu kalır.
 3. Figür: montaj plakasının arka yüzü bodoslama (CORE_STEM) ön kenarına 10 cm gömülür; ölçek, parmaklık üst
    kotu ile destek alt kotu arasındaki boşluğu dolduracak biçimde (≈ 3,0 m yükseklik) seçilir [TAHMİN, görsel].
 4. SOCKET_FIGUREHEAD figürün montaj noktasına taşınır; UCX, LOD'lar yenilenir; cıvadıra/parmaklık mesafeleri raporlanır.
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
SRC_VER, VER = "v039", "v040"
V = Vector
NAME = "MOD_FIGUREHEAD_BOZKURT_C"
HEIGHT = 3.0          # figür yüksekliği (m)
TARGET_TRIS = 450000  # 3,8 m'lik hero figür; 250k'da 1,6× büyütmede 4,5 mm faset kaldı
BOTTOM_Z = 2.75       # plaka alt ucu ≈ eski destek alt kotu (2,77 m)
EMBED = 0.10


def drop(prefixes):
    gone = []
    for o in [o for o in bpy.data.objects if o.name.startswith(prefixes)]:
        me = o.data
        gone.append(o.name)
        bpy.data.objects.remove(o, do_unlink=True)
        if me is not None and getattr(me, "users", 1) == 0:
            bpy.data.meshes.remove(me)
    return gone


def strip_rail_supports():
    rep = {}
    for sd in ("S", "P"):
        o = bpy.data.objects[f"CORE_HEAD_RAIL_{sd}"]
        bm = bmesh.new()
        bm.from_mesh(o.data)
        bm.transform(o.matrix_world)
        kill = []
        for isl in RS.islands(bm):
            vs = {v for f in isl for v in f.verts}
            if min(v.co.z for v in vs) < 5.0:          # parmaklık kolu 5,09–5,64 m; destekler 2,77 m'ye iner
                kill += list(vs)
        bmesh.ops.delete(bm, geom=list(set(kill)), context="VERTS")
        bm.transform(o.matrix_world.inverted())
        bm.to_mesh(o.data)
        bm.free()
        rep[sd] = {"removed_verts": len(set(kill))}
    return rep


def stem_front(z0, z1):
    o = bpy.data.objects["CORE_STEM"]
    ws = [o.matrix_world @ v.co for v in o.data.vertices]
    return max(w.x for w in ws if z0 <= w.z <= z1)


def reimport(old):
    """Ham GLB'den yüksek bütçeyle yeniden al; v039 malzemesi (dışa yazılmış dokular) korunur."""
    sp39 = importlib.util.spec_from_file_location("pass_v039", HERE / "pass_v039_figurehead_meshy.py")
    P39 = importlib.util.module_from_spec(sp39)
    sp39.loader.exec_module(P39)
    P39.TARGET_TRIS = TARGET_TRIS
    mat = old.data.materials[0]
    col = old.users_collection[0]
    props = {k: old[k] for k in old.keys()}
    mats_before = set(bpy.data.materials)
    imgs_before = set(bpy.data.images)
    old_me = old.data
    bpy.data.objects.remove(old, do_unlink=True)
    bpy.data.meshes.remove(old_me)
    ob = P39.import_glb()
    for c in list(ob.users_collection):
        c.objects.unlink(ob)
    col.objects.link(ob)
    info = P39.clean_and_decimate(ob)
    P39.place(ob)
    ob.data.materials.clear()
    ob.data.materials.append(mat)
    for m in set(bpy.data.materials) - mats_before:
        bpy.data.materials.remove(m)
    for im in set(bpy.data.images) - imgs_before:
        bpy.data.images.remove(im)
    for k, v in props.items():
        ob[k] = v
    ob["quality"] = f"hero; ham 2,40 M → {TARGET_TRIS // 1000}k üçgen (COLLAPSE), Meshy normal haritası detay taşır"
    return ob, info


def seat_on_stem(ob):
    """Plakanın arka yüzünden −X yönünde ışın → bodoslama; en küçük boşluk kadar geri + EMBED gömme."""
    o = bpy.data.objects["CORE_STEM"]
    dg = bpy.context.evaluated_depsgraph_get()
    ev = o.evaluated_get(dg).to_mesh()
    ts = BVHTree.FromPolygons([o.matrix_world @ v.co for v in ev.vertices], [tuple(p.vertices) for p in ev.polygons])
    o.evaluated_get(dg).to_mesh_clear()
    me = ob.data
    xmin = min(v.co.x for v in me.vertices)
    gaps = []
    for v in me.vertices:
        if v.co.x < xmin + 0.6:
            hit = ts.ray_cast(v.co, V((-1, 0, 0)), 3.0)
            if hit[0] is not None:
                gaps.append(hit[3])
    if not gaps:
        return None
    g = min(gaps)
    me.transform(Matrix.Translation(V((-(g + EMBED), 0, 0))))
    me.update()
    return round(g, 3)


def extend_rails(tf):
    rep = {}
    for sd in ("S", "P"):
        r = bpy.data.objects[f"CORE_HEAD_RAIL_{sd}"]
        M, Mi = r.matrix_world, r.matrix_world.inverted()
        ws = [M @ v.co for v in r.data.vertices]
        xmax = max(w.x for w in ws)
        front = [i for i, w in enumerate(ws) if w.x > xmax - 0.06]
        back = [i for i, w in enumerate(ws) if xmax - 0.40 < w.x < xmax - 0.30]
        cf = sum((ws[i] for i in front), V()) / len(front)
        cb = sum((ws[i] for i in back), V()) / len(back)
        t = (cf - cb).normalized()
        hit = tf.ray_cast(cf, t, 2.0)
        d = (hit[3] + 0.04) if hit[0] is not None else 0.0
        for i in range(len(ws)):
            w = ws[i]
            k = max(0.0, min(1.0, (w.x - (xmax - 0.30)) / 0.30))     # uç 0,30 m içinde yumuşak uzatma
            if k > 0:
                r.data.vertices[i].co = Mi @ (w + t * d * k)
        r.data.update()
        rep[sd] = round(d, 3)
    return rep


def trim_rails(tf):
    """Parmaklık kolu yeleden geçip başa saplanıyordu → kol, figüre ilk girdiği yerden 5 cm içeride biter
    (içeride kalan kısım silinir; açık uç yelenin içinde görünmez)."""
    rep = {}
    for sd in ("S", "P"):
        r = bpy.data.objects[f"CORE_HEAD_RAIL_{sd}"]
        M = r.matrix_world
        bm = bmesh.new()
        bm.from_mesh(r.data)
        # kol boyunca (x artan) figür yüzeyine ilk değme noktası (≤ 1,5 cm); kol oradan 6 cm ileride biter
        touch_x = []
        for v in bm.verts:
            w = M @ v.co
            loc, nrm, _, d = tf.find_nearest(w, 1.0)
            if loc is not None and d < 0.015:
                touch_x.append(w.x)
        inside_x = [min(touch_x) + 0.06] if touch_x else []
        cut = min(inside_x)
        kill = [v for v in bm.verts if (M @ v.co).x > cut]
        bmesh.ops.delete(bm, geom=kill, context="VERTS")
        bm.to_mesh(r.data)
        bm.free()
        rep[sd] = {"cut_x": round(cut, 2), "removed_verts": len(kill)}
    return rep


def refit(ob):
    me = ob.data
    zs = [v.co.z for v in me.vertices]
    f = HEIGHT / (max(zs) - min(zs))
    me.transform(Matrix.Scale(f, 4))
    xs = [v.co.x for v in me.vertices]
    ys = [v.co.y for v in me.vertices]
    zs = [v.co.z for v in me.vertices]
    # plakanın arka ucu: alt yarıdaki en geri noktalar (plaka) → bodoslama ön kenarına gömülür
    zmin = min(zs)
    band = (BOTTOM_Z, BOTTOM_Z + HEIGHT * 0.9)
    back_x = stem_front(*band) - EMBED
    me.transform(Matrix.Translation(V((back_x - min(xs), -(min(ys) + max(ys)) / 2, BOTTOM_Z - zmin))))
    me.update()
    return f, back_x


def render(sc):
    H.setup_render(sc, fast=True)
    sc.cycles.samples = 32
    out = ROOT / "renders" / VER
    out.mkdir(parents=True, exist_ok=True)
    c = V((23.6, 0.0, 4.3))
    for name, loc, tgt, lens in (("figur_yan", c + V((0.8, 7.5, 0.8)), c, 40),
                                 ("figur_on", c + V((6.0, 3.0, 1.5)), c, 40),
                                 ("figur_parmaklik", V((26.5, 6.5, 7.5)), V((22.5, 0.4, 4.3)), 32),
                                 ("bas_omzu", V((34.0, 14.0, 9.0)), V((21.0, 0.0, 6.0)), 35)):
        sc.camera = H.camera(sc, f"CAM40_{name}", loc, tgt, lens=lens)
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
    bpy.context.view_layer.update()
    rep = {"removed": drop(("CORE_HEAD_KNEE", "UCX_CORE_HEAD_KNEE"))}
    rep["rail_supports"] = strip_rail_supports()
    ob, rep["reimport"] = reimport(bpy.data.objects[NAME])
    f, back_x = refit(ob)
    rep["stem_gap_closed_m"] = seat_on_stem(ob)
    back_x = min(v.co.x for v in ob.data.vertices)
    rep["scale_factor_vs_v039"] = round(f, 3)
    rep["plate_back_x"] = round(back_x, 3)
    me = ob.data
    pts = [v.co.copy() for v in me.vertices]
    xs, ys, zs = [p.x for p in pts], [p.y for p in pts], [p.z for p in pts]
    rep["bbox"] = [[round(min(xs), 2), round(min(ys), 2), round(min(zs), 2)], [round(max(xs), 2), round(max(ys), 2), round(max(zs), 2)]]
    rep["size_m"] = [round(max(xs) - min(xs), 2), round(max(ys) - min(ys), 2), round(max(zs) - min(zs), 2)]
    s = bpy.data.objects.get("SOCKET_FIGUREHEAD")
    if s:
        s.location = V((back_x + EMBED, 0.0, BOTTOM_Z + HEIGHT * 0.45))   # yaklaşık montaj noktası
        s["mount"] = "bodoslama ön kenarı (v040; baş kıvrımı kaldırıldı)"
        rep["socket"] = [round(c, 2) for c in s.location]
    drop(("UCX_" + NAME,))
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
    ts = tree("CORE_STEM")
    rep["stem_overlap"] = bool(ts.overlap(tf))
    rep["rail_extension_m"] = extend_rails(tf)
    rep["rail_trim"] = trim_rails(tf)
    rails = {}
    for sd in ("S", "P"):
        r = bpy.data.objects[f"CORE_HEAD_RAIL_{sd}"]
        vs = [r.matrix_world @ v.co for v in r.data.vertices]
        fwd = max(vs, key=lambda p: p.x)
        rt = BVHTree.FromPolygons(vs, [tuple(p.vertices) for p in r.data.polygons])
        rails[sd] = {"front_to_figure_m": round(tf.find_nearest(fwd, 9.0)[3], 3), "touches_figure": bool(rt.overlap(tf))}
    rep["head_rails"] = rails
    for n in (NAME, "CORE_HEAD_RAIL_S", "CORE_HEAD_RAIL_P"):
        drop((n + "_LOD",))
    LODS.build_lods(sc, only={NAME, "CORE_HEAD_RAIL_S", "CORE_HEAD_RAIL_P"})
    me.calc_loop_triangles()
    rep["tris"] = len(me.loop_triangles)
    bpy.ops.wm.save_as_mainfile(filepath=str(out), compress=True)
    H.VERSION = VER
    ap = ROOT / "reports" / f"scene_audit_{VER}.json"
    arep = H.audit(sc, ap)
    arep["figurehead_v040"] = rep
    arep["pass"] = {"name": "pass_v040_figurehead_mount", "source": f"Blender/versions/{SHIP}_{SRC_VER}.blend"}
    ap.write_text(json.dumps(arep, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    qa = QA.audit(sc, top=60)
    (ROOT / "reports" / f"kalite_testi_{VER}.json").write_text(json.dumps(qa, indent=1, ensure_ascii=False), encoding="utf-8")
    r = next(x for x in qa["objects"] if x["name"] == NAME)
    print("V040", json.dumps(rep, ensure_ascii=False, default=str))
    print("V040 QA", json.dumps(qa["summary"], ensure_ascii=False), "figür:", r["fail"], r["facet_m"], r["worst_sag_mm"], r["floating_islands"][:3])
    if "--no-render" not in sys.argv:
        render(sc)


if __name__ == "__main__":
    main()
