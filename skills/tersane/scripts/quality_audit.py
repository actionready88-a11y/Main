"""Tersane — genel kalite testi (low-poly yasağı denetimi + artık/havada parça).

    python3.11 quality_audit.py <gemi.blend> [--out rapor.json] [--top 40]

Ölçütler (her render mesh'i, UCX/CUT/LOD hariç, paylaşılan mesh bir kez):
1. FASET: yumuşak gölgeli kenarda yerel yay sapması (w/2)·tan(θ/4) > 1,5 mm ve eğrilik sürekli ise kenar "faset"tir
   (w: bitişik yüzün kenara dik genişliği, θ: kırılma açısı; θ ≥ 60° ve komşusu kırılmayan tekil kenar gerçek köşedir).
   Kiriş sapması kuralının kenar karşılığıdır: ince halatta 12 dilim geçer, kalın serende 10 dilim kalır. Ölçü: faset kenar uzunluğu toplamı (m) ve yoğunluğu
   (m / m² yüzey). Keskin işaretli ve ≥ 60° gerçek köşeler sayılmaz.
2. DÜZ GÖLGE: `use_smooth = False` yüz oranı (eğri parçada kabul edilmez).
3. KİRİŞ SAPMASI (sagitta): lathe/tube dilim sayısı için kural  seg ≥ π / acos(1 − tol/r),
   tol = 1,5 mm (güverte/iç mekân, yakın bakış) — 3 mm (arma yukarısı). `required_segments(r)` ile hesapla.
4. HAVADA ADA: nesnenin bağımsız parçalarından (loose island) hiçbir köşesi başka bir nesneye / kendi diğer
   adalarına 3 cm'den yakın değilse "havada" sayılır (artık parça, yanlış konum).
Sonuç JSON: objects[{name, tris, facet_m, facet_density, flat_ratio, floating_islands}], worst listesi, özet.
Eşikler: facet_m > 0,5 m ya da flat_ratio > 0.2 ya da havada ada → KALİTE_HATASI.
İstisna: nesnede `quality_exempt` özelliği (ör. "BLOCKOUT: nihai model bekliyor") → hata sayılmaz, özette ayrıca listelenir.
"""

import json
import math
import sys

import bpy  # noqa: I001  (bpy, bmesh'ten önce yüklenmeli)
import bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree


def required_segments(r, tol=0.0015, minimum=6):
    """Kiriş sapması ≤ tol için yuvarlak kesit dilim sayısı (4'ün katına yuvarlanır)."""
    if r <= tol:
        return minimum
    n = math.pi / math.acos(1 - tol / r)
    return max(minimum, int(math.ceil(n / 4.0)) * 4)


def _render_meshes(sc):
    seen = set()
    for o in sc.objects:
        if o.type != "MESH" or o.name.startswith(("UCX_", "CUT_")) or "_LOD" in o.name or o.hide_render:
            continue
        key = o.data.name
        if key in seen:
            continue
        seen.add(key)
        yield o


def _perp_width(f, e):
    a, b = e.verts[0].co, e.verts[1].co
    d = b - a
    L2 = d.length_squared
    if L2 < 1e-12:
        return 0.0
    best = 0.0
    for v in f.verts:
        p = v.co - a
        best = max(best, (p - d * (p.dot(d) / L2)).length)
    return best


def _opposite_turn(f, e):
    """Yüzün e'ye karşı (paralel) kenarındaki kırılma açısı; faset tekrarlar, gerçek köşe tek başınadır."""
    if len(f.verts) != 4:
        return None
    ev = set(e.verts)
    for o in f.edges:
        if not (set(o.verts) & ev) and len(o.link_faces) == 2:
            return o.calc_face_angle(0.0)
    return None


def facet_metrics(o, dg, tol=0.0015, hard=60.0, min_deg=4.0):
    """Faset = yumuşak gölgeli kenarda gerçek görsel sapma > tol ve eğrilik sürekliliği.
    Sapma: (w/2)·tan(θ/4); w = bitişik yüzün kenara dik genişliği (dejenere kenar atlanır), θ = kırılma açısı.
    Süreklilik: iki yandaki yüzlerden birinin karşı kenarı da ≥ 0,4·θ kırılıyorsa kenar eğri bir yüzeyin
    parçasıdır (faset); yalnız başına kırılan kenar (güverte–gövde birleşimi, kıç aynası köşesi) gerçek köşedir."""
    ev = o.evaluated_get(dg)
    me = ev.to_mesh()
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.transform(o.matrix_world)
    facet = 0.0
    worst = 0.0
    area = sum(f.calc_area() for f in bm.faces) or 1e-9
    for e in bm.edges:
        if len(e.link_faces) != 2 or not e.smooth:
            continue
        f0, f1 = e.link_faces
        if not (f0.smooth and f1.smooth):
            continue
        th = e.calc_face_angle(0.0)
        if math.degrees(th) < min_deg or math.degrees(th) >= hard:
            continue                                   # < 4°: gölgede ve siluette görünmez (uzun konik direk vb.)
        L = e.calc_length()
        if L < 1e-4:
            continue
        w = min(_perp_width(f0, e), _perp_width(f1, e))
        sag = 0.5 * w * math.tan(th / 4.0)
        if sag <= tol:
            continue
        o0, o1 = _opposite_turn(f0, e), _opposite_turn(f1, e)
        if (o0 is not None or o1 is not None) and max(o0 or 0.0, o1 or 0.0) < 0.4 * th:
            continue                                   # tekil köşe
        facet += L
        worst = max(worst, sag)
    flat = sum(1 for f in bm.faces if not f.smooth) / max(len(bm.faces), 1)
    me.calc_loop_triangles()
    tris = len(me.loop_triangles)
    bm.free()
    ev.to_mesh_clear()
    return tris, facet, facet / area, flat, area, worst


def _islands(bm):
    """Bağlı yüz grupları → [(köşe listesi, üçgen listesi)] (dünya koordinatı)."""
    seen, out = set(), []
    for f in bm.faces:
        if f.index in seen:
            continue
        stack, faces = [f], []
        seen.add(f.index)
        while stack:
            a = stack.pop()
            faces.append(a)
            for e in a.edges:
                for g in e.link_faces:
                    if g.index not in seen:
                        seen.add(g.index)
                        stack.append(g)
        vids = {}
        polys = []
        for fc in faces:
            polys.append(tuple(vids.setdefault(v.index, len(vids)) for v in fc.verts))
        verts = [None] * len(vids)
        for v in {v for fc in faces for v in fc.verts}:
            verts[vids[v.index]] = v.co.copy()
        out.append((verts, polys))
    return out


def _bbox(pts, pad):
    xs, ys, zs = zip(*pts)
    return (min(xs) - pad, min(ys) - pad, min(zs) - pad, max(xs) + pad, max(ys) + pad, max(zs) + pad)


def _bb_hit(a, b):
    return all(a[i] <= b[i + 3] and b[i] <= a[i + 3] for i in range(3))


def floating_islands(objs, dg, gap=0.03, max_islands=600):
    """Her ada (bağlı yüz grubu) için: başka bir nesneye ya da aynı nesnenin başka adasına gap'ten yakın mı?
    Yakınlık: BVH kesişmesi (overlap) ya da adanın örnek köşelerinden hedef BVH'a en yakın nokta (yüzeye değme)."""
    data = {}
    for o in objs:
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        bm = bmesh.new()
        bm.from_mesh(me)
        bm.transform(o.matrix_world)
        bm.faces.index_update()
        isl = _islands(bm)
        bm.free()
        ev.to_mesh_clear()
        items = [(BVHTree.FromPolygons(v, p), _bbox(v, gap), v) for v, p in isl if v]
        data[o.name] = items
    res = {}
    for o in objs:
        items = data[o.name]
        if len(items) > max_islands:
            continue
        bad = []
        for k, (tk, bk, vk) in enumerate(items):
            samp = vk[:: max(1, len(vk) // 48)]
            near = False
            for n, its in data.items():
                for j, (tj, bj, _) in enumerate(its):
                    if (n == o.name and j == k) or not _bb_hit(bk, bj):
                        continue
                    if tj.overlap(tk) or any(tj.find_nearest(p, gap)[0] is not None for p in samp):
                        near = True                  # kesişme (ray dikmenin içinden geçer) ya da yakınlık
                        break
                if near:
                    break
            if not near:
                c = sum(vk, Vector()) / len(vk)
                bad.append([round(c.x, 2), round(c.y, 2), round(c.z, 2)])
        if bad:
            res[o.name] = bad
    return res


def audit(sc, top=40, check_floating=True, float_prefixes=("CORE_", "MOD_")):
    dg = bpy.context.evaluated_depsgraph_get()
    rows = []
    objs = list(_render_meshes(sc))
    for o in objs:
        tris, facet, dens, flat, area, worst = facet_metrics(o, dg)
        rows.append({"name": o.name, "users": o.data.users, "tris": tris, "facet_m": round(facet, 2), "worst_sag_mm": round(worst * 1000, 1),
                     "facet_density": round(dens, 3), "flat_ratio": round(flat, 3), "area_m2": round(area, 2)})
    fl = {}
    if check_floating:
        cand = [o for o in objs if o.name.startswith(float_prefixes)]
        fl = floating_islands(cand, dg)
    for r in rows:
        r["floating_islands"] = fl.get(r["name"], [])
        ex = bpy.data.objects[r["name"]].get("quality_exempt")
        r["exempt"] = ex or ""
        r["fail"] = (r["facet_m"] > 0.5 or r["flat_ratio"] > 0.2 or bool(r["floating_islands"])) and not ex
    worst = sorted(rows, key=lambda r: (-r["facet_density"]))[:top]
    return {"summary": {"objects": len(rows), "fail": sum(r["fail"] for r in rows),
                        "exempt": [r["name"] + ": " + r["exempt"] for r in rows if r["exempt"]],
                        "facet_m_total": round(sum(r["facet_m"] * r["users"] for r in rows), 1),
                        "floating_objects": len(fl)},
            "worst_by_facet_density": [r["name"] for r in worst], "objects": rows}


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    bpy.ops.wm.open_mainfile(filepath=argv[0])
    out = argv[argv.index("--out") + 1] if "--out" in argv else None
    top = int(argv[argv.index("--top") + 1]) if "--top" in argv else 40
    rep = audit(bpy.context.scene, top)
    txt = json.dumps(rep, indent=1, ensure_ascii=False)
    if out:
        open(out, "w", encoding="utf-8").write(txt)
    print(json.dumps(rep["summary"], ensure_ascii=False))
    for r in sorted(rep["objects"], key=lambda r: -r["facet_density"])[:top]:
        print(f"{'HATA' if r['fail'] else 'ok  '} dens={r['facet_density']:.2f} facet={r['facet_m']:8.1f}m sag={r['worst_sag_mm']:5.1f}mm flat={r['flat_ratio']:.2f} "
              f"tris={r['tris']:7d} x{r['users']} {r['name']} {'HAVADA:' + str(r['floating_islands'][:3]) if r['floating_islands'] else ''}")


if __name__ == "__main__":
    main()
