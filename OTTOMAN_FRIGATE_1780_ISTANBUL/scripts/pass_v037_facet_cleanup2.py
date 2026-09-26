"""v037 — kalan fasetler, ikinci tur (kullanıcı: "diğerlerini halledelim").

    python3.11 OTTOMAN_FRIGATE_1780_ISTANBUL/scripts/pass_v037_facet_cleanup2.py [--no-render]

v036 kalite testi: 23 nesne eşik üstü. Bu pass:
 1. Ana/mizana çanaklığı (16 mm): v033 seçimi levhayı eksene dik sanıyordu; bu direklerde çanaklık yatıklık kadar
    eğik (kalınlık yönü 0,21–0,27 m) → bulunamadı. Yeni: topolojiyle (üst/alt yüz halkası, basamak/kenar ayrımı)
    4 halka çıkarılır, sapmaya göre UYARLAMALI Catmull-Rom sıklaştırma (köşelerde daha sık). Üç direğe de uygulanır.
 2. Hareketli arma (halat makara/armadorda keskin döner, 30°, 1,7 m'lik yüzde 116 mm sapma): dönüş yuvarlatma
    (resegment.fillet_kinks: ±d halkası + Catmull-Rom; d = max(3r, 4 cm), makara dili sarımı gibi); babalardaki kısa
    ardışık dönüşler için 0,6 mm toleransla ikinci sıklaştırma turu.
 3. Seyrek eğri yüzeyli küçük modüller (filika, ırgat, kıç panoları, fener, dümen dolabı, kıç galerisi, tulumba,
    ambar yükü, bordada alt kuşak, bodoslama, seren, sarılı yelken): yalnız faset içeren adalar ayrılır, sert kenarlara
    kıvrım (crease 1) verilir, 1 düzey Catmull-Clark uygulanır. Her nesnede ölçülür: en kötü sapma azalmadıysa ya da
    yüzey özgün yüzeyden > 12 mm ayrıldıysa geri alınır (v033'teki filika şişmesi dersi).
 4. Gövde kabuğu: faset kıç altındaki "tuck" bölgesinde (x < −17 m, su altı; çoğu ≈ 2 mm) → bu pass'te dokunulmaz,
    raporlanır (subsurf 3 gövdeyi 2,2 M üçgene çıkarır).
v031–v036 betikleri değiştirilmez.
"""

import importlib.util
import json
import math
import sys
from pathlib import Path

import bpy  # noqa: I001
import bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree

HERE = Path(__file__).resolve().parent
sp = importlib.util.spec_from_file_location("pass_v033", HERE / "pass_v033_facet_cleanup.py")
P33 = importlib.util.module_from_spec(sp)
sp.loader.exec_module(P33)
P31 = P33.P31
RS, QA, LODS, H = P31.RS, P31.QA, P31.LODS, P31.H
ROOT, SHIP = P31.ROOT, P31.SHIP
SRC_VER, VER = "v036", "v037"
V = Vector
TOL = 0.0015


# ------------------------------------------------------------------ 1. çanaklık
def _pca_normal(pts):
    import numpy as np
    A = np.array([tuple(p) for p in pts])
    c = A.mean(axis=0)
    w, vec = np.linalg.eigh(np.cov((A - c).T))
    return V(c), V(vec[:, 0]).normalized()


def _cycle(edges):
    """Derecesi 2 olan kenar kümesinden kapalı döngüler (köşe indis listeleri)."""
    adj = {}
    for a, b in edges:
        adj.setdefault(a, []).append(b)
        adj.setdefault(b, []).append(a)
    if any(len(x) != 2 for x in adj.values()):
        return []
    seen, out = set(), []
    for s in adj:
        if s in seen:
            continue
        loop, prev, cur = [s], None, s
        seen.add(s)
        while True:
            n = adj[cur][0] if adj[cur][0] != prev else adj[cur][1]
            if n == s:
                break
            loop.append(n)
            seen.add(n)
            prev, cur = cur, n
        out.append(loop)
    return out


def _adaptive_counts(pts, tol=0.0010, kmax=12):
    """Kapalı Catmull-Rom halkasında her parça için alt bölme sayısı: sapma ≈ L·θ/8 → k = ⌈√(sapma/tol)⌉."""
    n = len(pts)
    ks = []
    for i in range(n):
        a, b, c, d = pts[i - 1], pts[i], pts[(i + 1) % n], pts[(i + 2) % n]
        L = (c - b).length
        t0 = (b - a).angle(c - b, 0.0) if (b - a).length > 1e-9 and (c - b).length > 1e-9 else 0.0
        t1 = (c - b).angle(d - c, 0.0) if (d - c).length > 1e-9 and (c - b).length > 1e-9 else 0.0
        sag = L * max(t0, t1) / 8.0
        ks.append(max(1, min(kmax, int(math.ceil(math.sqrt(sag / tol))))))
    return ks


def _cr_loop(pts, ks):
    n = len(pts)
    out = []
    for i in range(n):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[(i + 1) % n], pts[(i + 2) % n]
        for j in range(ks[i]):
            out.append(RS._cr(p0, p1, p2, p3, j / ks[i]))
    return out


def mast_tops_v2():
    rep = {}
    for mast in ("FORE", "MAIN", "MIZZEN"):
        ob = bpy.data.objects[f"MOD_RIG_MAST_{mast}_A"]
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        bm.faces.index_update()
        bm.verts.index_update()
        best = None
        for fs in RS.islands(bm):
            vs = list({v for f in fs for v in f.verts})
            if len(vs) < 128 or len(vs) % 4:
                continue
            c, n = _pca_normal([v.co for v in vs])
            h = [(v.co - c).dot(n) for v in vs]
            thick = max(h) - min(h)
            span = max((v.co - c).length for v in vs)
            if thick < 0.35 and span > 1.0 and all(len(f.verts) == 4 for f in fs) and (best is None or len(vs) > len(best[1])):
                best = (fs, vs, c, n)
        if best is None:
            rep[mast] = "bulunamadı"
            bm.free()
            continue
        fs, vs, c, n = best
        mat = fs[0].material_index
        top = [f for f in fs if f.normal.dot(n) > 0.85]
        bot = [f for f in fs if f.normal.dot(n) < -0.85]
        if len(top) * 4 != len(fs) or len(bot) != len(top):
            rep[mast] = f"yüz sınıfı uymadı ({len(top)}/{len(bot)}/{len(fs)})"
            bm.free()
            continue

        def loops_of(face_set):
            fset = set(face_set)
            rung, rim = [], []
            for f in face_set:
                for e in f.edges:
                    other = [g for g in e.link_faces if g is not f]
                    (rung if other and other[0] in fset else rim).append((e.verts[0].index, e.verts[1].index))
            cyc = _cycle(set(tuple(sorted(x)) for x in rim))
            rungs = {}
            for a, b in set(tuple(sorted(x)) for x in rung):
                rungs[a], rungs[b] = b, a
            return cyc, rungs
        vi = {v.index: v for v in vs}
        (ct, rt), (cb, rb) = loops_of(top), loops_of(bot)
        if len(ct) != 2 or len(cb) != 2:
            rep[mast] = "halka yapısı uymadı"
            bm.free()
            continue
        per = lambda lp: sum((vi[lp[i]].co - vi[lp[i - 1]].co).length for i in range(len(lp)))   # noqa: E731
        ti, to = sorted(ct, key=per)
        # dış-üst halkaya hizalı sıra: iç = basamakla eşi; alt = dikey kenarla eşi
        vert_pair = {}
        for e in bm.edges:
            a, b = e.verts
            if a.index in vi and b.index in vi and abs((b.co - a.co).normalized().dot(n)) > 0.9:
                vert_pair[a.index], vert_pair[b.index] = b.index, a.index
        try:
            L_to = to
            L_ti = [rt[i] for i in L_to]
            L_bo = [vert_pair[i] for i in L_to]
            L_bi = [vert_pair[i] for i in L_ti]
        except KeyError:
            rep[mast] = "eşleşme bulunamadı"
            bm.free()
            continue
        P = {k: [vi[i].co.copy() for i in L] for k, L in (("to", L_to), ("ti", L_ti), ("bo", L_bo), ("bi", L_bi))}
        ks = [max(a, b) for a, b in zip(_adaptive_counts(P["to"]), _adaptive_counts(P["ti"]))]
        old_n = len(L_to)
        bmesh.ops.delete(bm, geom=vs, context="VERTS")
        L = {k: [bm.verts.new(p) for p in _cr_loop(pts, ks)] for k, pts in P.items()}
        m = len(L["to"])
        newf = []
        for a, b in (("ti", "to"), ("bo", "bi"), ("to", "bo"), ("bi", "ti")):
            A, B = L[a], L[b]
            for k in range(m):
                newf.append(bm.faces.new([A[k], B[k], B[(k + 1) % m], A[(k + 1) % m]]))
        for f in newf:
            f.material_index = mat
            f.smooth = True
        bmesh.ops.recalc_face_normals(bm, faces=newf)
        uv = bm.loops.layers.uv.active
        if uv is not None:
            for f in newf:
                for lp in f.loops:
                    q = lp.vert.co - c
                    lp[uv].uv = (q.x, q.y)
        bm.to_mesh(ob.data)
        bm.free()
        RS.sharp_from_angle_keep(ob.data, 35)
        rep[mast] = {"ring_pts_before": old_n, "ring_pts": m, "thickness_axis_tilt_deg": round(math.degrees(n.angle(V((0, 0, 1)))), 1)}
    return rep


# ------------------------------------------------------------------ 3. seçici Catmull-Clark
def _world_bm(ob, evaluated=False):
    bm = bmesh.new()
    if evaluated:
        dg = bpy.context.evaluated_depsgraph_get()
        ev = ob.evaluated_get(dg)
        me = ev.to_mesh()
        bm.from_mesh(me)
        ev.to_mesh_clear()
    else:
        bm.from_mesh(ob.data)
    bm.transform(ob.matrix_world)
    return bm


def _facet_face_islands(ob):
    """Faset kenarı içeren adaların yüz indisleri (taban mesh, dünya ölçüsünde ölçülür)."""
    bm = _world_bm(ob)
    bm.faces.index_update()
    isl_of = {}
    for k, fs in enumerate(RS.islands(bm)):
        for f in fs:
            isl_of[f.index] = k
    hit = set()
    for e in bm.edges:
        if len(e.link_faces) != 2 or not e.smooth:
            continue
        f0, f1 = e.link_faces
        if not (f0.smooth and f1.smooth):
            continue
        th = e.calc_face_angle(0.0)
        if math.degrees(th) < 4 or math.degrees(th) >= 60 or e.calc_length() < 1e-4:
            continue
        w = min(QA._perp_width(f0, e), QA._perp_width(f1, e))
        if 0.5 * w * math.tan(th / 4) <= TOL:
            continue
        o0, o1 = QA._opposite_turn(f0, e), QA._opposite_turn(f1, e)
        if (o0 is not None or o1 is not None) and max(o0 or 0.0, o1 or 0.0) < 0.4 * th:
            continue
        hit.add(isl_of[f0.index])
    faces = {i for i, k in isl_of.items() if k in hit}
    bm.free()
    return faces


def cc_subdivide(ob, max_dev=0.012):
    me0 = ob.data
    dg = bpy.context.evaluated_depsgraph_get()
    before = QA.facet_metrics(ob, dg)
    sel = _facet_face_islands(ob)
    if not sel:
        return {"skip": "faset adası yok"}
    # hedef adaları ayrı mesh'e al
    bm = bmesh.new()
    bm.from_mesh(me0)
    bm.faces.ensure_lookup_table()
    other = [f for f in bm.faces if f.index not in sel]
    bmA = bm.copy()
    bmesh.ops.delete(bmA, geom=[f for f in bmA.faces if f.index not in sel], context="FACES")
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.index in sel], context="FACES")
    del other
    cr = bmA.edges.layers.float.get("crease_edge") or bmA.edges.layers.float.new("crease_edge")
    n_cr = 0
    for e in bmA.edges:
        hard = (not e.smooth) or e.is_boundary or len(e.link_faces) != 2 or any(not f.smooth for f in e.link_faces) \
            or e.calc_face_angle(0.0) >= math.radians(35)
        e[cr] = 1.0 if hard else 0.0
        n_cr += hard
    meA = bpy.data.meshes.new("_ccA")
    bmA.to_mesh(meA)
    bmA.free()
    for m in me0.materials:
        meA.materials.append(m)
    tmp = bpy.data.objects.new("_ccA", meA)
    bpy.context.scene.collection.objects.link(tmp)
    sub = tmp.modifiers.new("cc", "SUBSURF")
    sub.levels = sub.render_levels = 1
    sub.use_creases = True
    sub.boundary_smooth = "PRESERVE_CORNERS"
    dg = bpy.context.evaluated_depsgraph_get()
    dg.update()
    meB = bpy.data.meshes.new_from_object(tmp.evaluated_get(dg))
    bpy.data.objects.remove(tmp, do_unlink=True)
    bpy.data.meshes.remove(meA)
    n_keep, meB_faces = len(bm.faces), range(len(meB.polygons))
    bm.from_mesh(meB)                                    # özgün kalan + alt bölünmüş adalar
    bpy.data.meshes.remove(meB)
    me1 = bpy.data.meshes.new(me0.name + "_cc")
    bm.to_mesh(me1)
    bm.free()
    for m in me0.materials:
        me1.materials.append(m)
    n_expect = n_keep + len(meB_faces)
    if len(me1.polygons) != n_expect:
        bpy.data.meshes.remove(me1)
        return {"skip": f"birleştirme yüz sayısı uymadı ({len(me1.polygons)} ≠ {n_expect})"}
    # ölç: özgün yüzeyden sapma
    b0 = _world_bm(ob)
    tree = BVHTree.FromBMesh(b0)
    users = [o for o in bpy.data.objects if o.data == me0]
    for o in users:
        o.data = me1
    RS.sharp_from_angle_keep(me1, 35)
    dev = 0.0
    for v in me1.vertices:
        hit = tree.find_nearest(ob.matrix_world @ v.co, 1.0)
        if hit[0] is not None:
            dev = max(dev, hit[3])
    b0.free()
    dg = bpy.context.evaluated_depsgraph_get()
    dg.update()
    after = QA.facet_metrics(ob, dg)
    ok = after[5] < before[5] and after[1] < before[1] and dev <= max_dev
    if not ok:
        for o in users:
            o.data = me0
        bpy.data.meshes.remove(me1)
    else:
        name = me0.name
        bpy.data.meshes.remove(me0)
        me1.name = name
    return {"kept": ok, "islands_faces": len(sel), "creased_edges": n_cr, "max_dev_mm": round(dev * 1000, 1),
            "sag_mm": [round(before[5] * 1000, 1), round(after[5] * 1000, 1)],
            "facet_m": [round(before[1], 2), round(after[1], 2)], "tris": [before[0], after[0]]}


CC_TARGETS = ["MOD_BOAT_CUTTER_A", "MOD_CAPSTAN_A", "MOD_ORN_STERN_PANELS", "MOD_LANTERN_STERN_A", "MOD_HELM_WHEEL_A",
              "MOD_STERN_GALLERY_A", "MOD_PUMP_ELM_A_S", "MOD_HOLD_CARGO_A", "CORE_WALE_LOWER_TIER", "CORE_STEM",
              "MOD_RIG_YARD_FORE_COURSE_A", "MOD_RIG_YARD_MAIN_COURSE_A", "MOD_RIG_YARD_MAIN_TOPSAIL_A",
              "MOD_RIG_YARD_MIZZEN_COURSE_A", "MOD_SAIL_FURLED_JIB_A", "MOD_SAIL_FURLED_SPANKER_A"]
ROPES = ["MOD_RIG_RUNNING_FORE_A", "MOD_RIG_RUNNING_MAIN_A", "MOD_RIG_RUNNING_MIZZEN_A"]


def render(sc):
    H.setup_render(sc, fast=True)
    sc.cycles.samples = 32
    out = ROOT / "renders" / VER
    out.mkdir(parents=True, exist_ok=True)
    for name, loc, tgt, lens in (("canaklik_ana", V((7.5, 6.5, 22.5)), V((1.3, 0.0, 19.8)), 40),
                                 ("filika", V((12.5, 5.5, 9.0)), V((6.5, 0.0, 6.3)), 40),
                                 ("halat_armador", V((-6.0, 5.0, 8.5)), V((-9.9, 0.5, 6.8)), 40),
                                 ("irgat", V((-2.0, 2.5, 6.0)), V((-4.4, 0.0, 4.2)), 40)):
        sc.camera = H.camera(sc, f"CAM37_{name}", loc, tgt, lens=lens)
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
    rep = {"mast_tops": mast_tops_v2()}
    # halat: dönüş yuvarlatma + sıkı tolerans (babalardaki kısa ardışık dönüşler tek turda yetmiyor) + ikinci sıklaştırma
    rep["ropes"] = {n: [RS.resegment_object(bpy.data.objects[n], fillet_path_deg=8.0, tol=0.0006),
                        RS.resegment_object(bpy.data.objects[n], tol=0.0006)] for n in ROPES}
    rep["cc"] = {n: cc_subdivide(bpy.data.objects[n]) for n in CC_TARGETS if n in bpy.data.objects}
    changed = ["MOD_RIG_MAST_FORE_A", "MOD_RIG_MAST_MAIN_A", "MOD_RIG_MAST_MIZZEN_A"] + ROPES + \
        [n for n, r in rep["cc"].items() if r.get("kept")]
    for n in changed:
        for o in [o for o in bpy.data.objects if o.name.startswith(n + "_LOD")]:
            bpy.data.objects.remove(o, do_unlink=True)
    LODS.build_lods(sc, only=set(changed))
    bpy.ops.wm.save_as_mainfile(filepath=str(out), compress=True)
    H.VERSION = VER
    ap = ROOT / "reports" / f"scene_audit_{VER}.json"
    arep = H.audit(sc, ap)
    arep["facets_v037"] = rep
    arep["pass"] = {"name": "pass_v037_facet_cleanup2", "source": f"Blender/versions/{SHIP}_{SRC_VER}.blend"}
    ap.write_text(json.dumps(arep, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    qa = QA.audit(sc, top=60)
    (ROOT / "reports" / f"kalite_testi_{VER}.json").write_text(json.dumps(qa, indent=1, ensure_ascii=False), encoding="utf-8")
    print("V037", json.dumps(rep, ensure_ascii=False, default=str))
    print("V037 QA", json.dumps(qa["summary"], ensure_ascii=False))
    for r in sorted([r for r in qa["objects"] if r["fail"]], key=lambda r: -r["facet_m"]):
        print(f"  HATA {r['name']} facet={r['facet_m']}m sag={r['worst_sag_mm']}mm flat={r['flat_ratio']} havada={r['floating_islands'][:2]}")
    if "--no-render" not in sys.argv:
        render(sc)


if __name__ == "__main__":
    main()
