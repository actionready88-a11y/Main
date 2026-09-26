"""Tersane — çakışmasız gemi merdiveni (basamak + kırpılmış yan kiriş + tırabzan).

Ders (OTTOMAN_FRIGATE_1780 v027): eğimli yan kirişler üst uçta güverte kalınlığına/koaminge/kasara alın kirişine,
altta güverteye giriyordu. Kirişler ayakta p0.z + 0,06 m'de, üstte run − 0,14 m'de kırpılır.

    import stairs, geom
    bms = (bmesh.new(), bmesh.new(), bmesh.new())      # basamak, kiriş, tırabzan
    info = stairs.stair_clipped(bms, p0, p1, width=0.9, n=10, k=1.0)
    ob = geom.finish("CORE_STAIRS_X", list(zip(bms, (M_deck, M_timber, M_trim))), col, bevel=0.008)

p0: alt uç (alt güverte üstü, merdiven ekseni), p1: üst uç (üst güverte kenarı). k: ölçek (tasarım→dünya).
"""

import math

from mathutils import Vector

import geom

V = Vector


def stair_clipped(bms, p0, p1, width, n, k=1.0, handrail_h=0.95):
    bt, bs, bh = bms
    p0, p1 = V(p0), V(p1)
    d = p1 - p0
    u = V((d.x, d.y, 0.0))
    run = u.length
    u.normalize()
    w = V((-u.y, u.x, 0.0))
    rise, tread = d.z / n, run / n
    hw = width / 2 - 0.02 * k
    for i in range(1, n + 1):                               # basamaklar
        a = p0 + u * (tread * (i - 1) - 0.03 * k)
        b = p0 + u * (tread * i)
        z = p0.z + rise * i
        c = [V((q.x, q.y, z - 0.05 * k)) for q in (a - w * hw, b - w * hw, b + w * hw, a + w * hw)]
        c += [V((q.x, q.y, z)) for q in (a - w * hw, b - w * hw, b + w * hw, a + w * hw)]
        geom.box8(bt, c)
    tan = d.z / run
    h = 0.30 * k / math.cos(math.atan(tan))
    for side in (-1, 1):                                    # yan kirişler (kırpılmış çokgen)
        o = w * side * (width / 2 - 0.03 * k)

        def top(s):
            return p0.z + s * tan + 0.02 * k
        zf = p0.z + 0.06 * k
        s_a = (zf - p0.z + h - 0.02 * k) / tan
        s_e = run - 0.14 * k
        poly = [(0.0, zf), (s_a, zf), (s_e, top(s_e) - h), (s_e, top(s_e)), (0.0, max(top(0.0), zf + 0.02 * k))]
        pts = [p0 + u * s + o for s, _ in poly]
        r0 = [bs.verts.new(V((p.x, p.y, z))) for p, (_, z) in zip(pts, poly)]
        r1 = [bs.verts.new(v.co + w * 0.06 * k * side) for v in r0]
        bs.faces.new(r0)
        bs.faces.new(list(reversed(r1)))
        for j in range(len(r0)):
            bs.faces.new([r0[j], r0[(j + 1) % len(r0)], r1[(j + 1) % len(r0)], r1[j]])
    hr = handrail_h * k                                     # tırabzanlar
    posts = [p0 + u * (0.05 * k) + V((0, 0, rise)), p1 - u * (0.10 * k)]
    for side in (-1, 1):
        o = w * side * (width / 2 - 0.03 * k)
        for p in posts:
            q = p + o
            geom.aabox(bh, q.x - 0.05 * k, q.x + 0.05 * k, q.y - 0.05 * k, q.y + 0.05 * k, q.z, q.z + hr + 0.08 * k)
        for j in range(1, 5):
            q = posts[0].lerp(posts[1], j / 5) + o
            geom.aabox(bh, q.x - 0.02 * k, q.x + 0.02 * k, q.y - 0.02 * k, q.y + 0.02 * k, q.z, q.z + hr)
        a = posts[0] + o + V((0, 0, hr))
        b = posts[1] + o + V((0, 0, hr))
        dd = (b - a).normalized()
        pp = dd.cross(w).normalized() * 0.04 * k
        c = [a - w * 0.04 * k - pp, b - w * 0.04 * k - pp, b + w * 0.04 * k - pp, a + w * 0.04 * k - pp]
        geom.box8(bh, c + [q + pp * 2 for q in c])
    return {"angle_deg": round(math.degrees(math.atan2(d.z, run)), 1), "riser_m": round(rise, 3), "tread_m": round(tread, 3)}


def stair_params_from_mesh(ob):
    """Mevcut bir merdiven mesh'inden (basamaklar malzeme 0) p0, p1, genişlik, basamak sayısı çıkarır (yeniden kurmak için)."""
    me, mw = ob.data, ob.matrix_world
    tops = []
    for p in me.polygons:
        if p.material_index == 0 and (mw.to_3x3() @ p.normal).normalized().z > 0.9:
            tops.append((mw @ p.center, p))
    tops.sort(key=lambda t: t[0].z)
    groups = []
    for c, p in tops:
        if groups and abs(groups[-1][0][0].z - c.z) < 0.03:
            groups[-1].append((c, p))
        else:
            groups.append([(c, p)])
    centers, widths = [], []
    for g in groups:
        centers.append(sum((x[0] for x in g), V()) / len(g))
        vs = [mw @ me.vertices[i].co for x in g for i in x[1].vertices]
        widths.append(max(v.y for v in vs) - min(v.y for v in vs))
    n = len(centers)
    c1, cn = centers[0], centers[-1]
    rise = (cn.z - c1.z) / (n - 1)
    u = V((cn.x - c1.x, cn.y - c1.y, 0.0))
    tread = u.length / (n - 1)
    u.normalize()
    return V((c1.x, c1.y, c1.z - rise)) - u * (tread / 2), V((cn.x, cn.y, cn.z)) + u * (tread / 2), max(widths) + 0.04, n
