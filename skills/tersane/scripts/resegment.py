"""Tersane — mesh düzeyinde yeniden dilimleme (low-poly yasağı için kiriş sapması kuralı).

Neden: yuvarlak parçalar (halat, seren, direk, bigot, fıçı, balüster, makara, gülle) onlarca farklı üreticiden
(lathe/tube/uvsphere) çıkar; üreticileri tek tek yeniden çağırmak kırılgandır. Bu araç birleşik mesh'in içindeki
her adayı (bağlı yüz grubu) çözümler:
  • HALKA DİZİSİ (lathe/tube çıktısı): köşeler üretim sırasıyla `seg`'lik eş-yarıçaplı düzlemsel halkalar ve tek
    köşeli kutuplar (pole) halinde dizilidir → her halkanın merkezi/yarıçapı/fazı korunarak `required_segments(r)`
    dilimle yeniden kurulur; uç kapakları (n-gon) korunur. Silindirik UV (U = çevre, V = boy, metre) yazılır.
  • SÜPÜRME (dairesel olmayan kesit, ör. dikdörtgen bodoslama/dümen): köşe çizgileri 1°–45° kırılıyorsa ara kesitler.
  • SIKLAŞTIRMA: halka dizisinin yüzey çizgileri 8°–60° kırılıyorsa (seyrek profil ya da eğri yol: halka cıvatası,
    brok halatı, kangal, ırgat başı) araya Catmull-Rom halkalar eklenir; ≥ 60° kasıtlı köşeler korunur.
  • ELİPSOİT (uvsphere/ölçekli küre): PCA eksenlerine oturtulmuş yeni uvsphere.
Kutu/serbest biçimli adalara dokunulmaz (onlar için bevel segment ≥ 3 + harden normals).

    import resegment as rs
    rep = rs.resegment_object(ob, tol=0.0015, max_seg=64, keep=lambda info: False)

Kural: seg ≥ π / acos(1 − tol / r), çift sayıya yuvarlanır; tol 1,5 mm (yakın bakış), arma yukarısı için 3 mm verilebilir.
Sınır: halka köşeleri eşit açılı ve eş yarıçaplı olmalı (sapma < %3); elips kesitli ölçekli lathe'ler atlanır.
"""

import math

import bpy  # noqa: I001  (bpy, bmesh'ten önce yüklenmeli)
import bmesh
from mathutils import Matrix, Vector

V = Vector


def required_segments(r, tol=0.0015, minimum=6, maximum=64):
    if r <= tol * 1.01:
        return minimum
    n = math.pi / math.acos(1.0 - tol / r)
    n = int(math.ceil(n))
    n += n % 2
    return max(minimum, min(maximum, n))


# ------------------------------------------------------------------ çözümleme
def _ring_info(pts):
    """Eş aralıklı çember mi? → (merkez, yarıçap, normal, u0) ya da None."""
    n = len(pts)
    if n < 3:
        return None
    c = sum(pts, V()) / n
    d = [(p - c).length for p in pts]
    r = sum(d) / n
    if r < 1e-5 or max(abs(x - r) for x in d) > 0.03 * r + 1e-5:
        return None
    nrm = V()
    for i in range(n):
        nrm += (pts[i] - c).cross(pts[(i + 1) % n] - c)
    if nrm.length < 1e-12:
        return None
    nrm.normalize()
    if max(abs((p - c).dot(nrm)) for p in pts) > 0.02 * r + 1e-5:
        return None
    step = 2 * math.pi / n
    for i in range(n):
        a = (pts[i] - c).angle(pts[(i + 1) % n] - c, 0.0)
        if abs(a - step) > 0.08 * step:
            return None
    return c, r, nrm, (pts[0] - c).normalized()


def _parse_rings(verts, seg):
    groups, i, n = [], 0, len(verts)
    while i < n:
        if i + seg <= n:
            ri = _ring_info(verts[i:i + seg])
            if ri:
                groups.append(("R", ri))
                i += seg
                continue
        groups.append(("P", verts[i]))
        i += 1
    rings = [g for g in groups if g[0] == "R"]
    if not rings:
        return None
    # kutuplar yalnız başta/sonda olabilir
    kinds = "".join(g[0] for g in groups)
    core = kinds.strip("P")
    if "P" in core or len(kinds) - len(kinds.lstrip("P")) > 1 or len(kinds) - len(kinds.rstrip("P")) > 1:
        return None
    return groups


def _is_thin_rope(groups, r_max=0.02, slender=15.0):
    rings = [g[1] for g in groups if g[0] == "R"]
    r = max(ri[1] for ri in rings)
    length = sum((b[0] - a[0]).length for a, b in zip(rings[:-1], rings[1:]))
    return r <= r_max and length / r >= slender


def _expected_faces(groups, seg, caps):
    f = 0
    for a, b in zip(groups[:-1], groups[1:]):
        if a[0] == "R" or b[0] == "R":
            f += seg
    return f + caps


def analyse_island(faces):
    """faces: bmesh yüzleri (tek ada). Dönüş: ('ring', seg, groups, caps, mat, smooth) | ('ellipsoid', ...) | None"""
    verts = sorted({v for f in faces for v in f.verts}, key=lambda v: v.index)
    pts = [v.co.copy() for v in verts]
    mat = max(set(f.material_index for f in faces), key=lambda m: sum(1 for f in faces if f.material_index == m))
    smooth = sum(f.smooth for f in faces) * 2 >= len(faces)
    ngons = [len(f.verts) for f in faces if len(f.verts) > 4]
    cands = set(ngons)
    for v in verts:
        k = len(v.link_faces)
        if k > 4 and all(len(f.verts) == 3 for f in v.link_faces):
            cands.add(k)
    if not cands:
        cands = set(range(3, 25))
    for seg in sorted(cands):
        if seg < 3:
            continue
        groups = _parse_rings(pts, seg)
        if not groups:
            continue
        caps = len(faces) - _expected_faces(groups, seg, 0)
        if caps in (0, 1, 2) and (caps == 0 or sum(1 for f in faces if len(f.verts) == seg) >= caps):
            if seg <= 4 and not _is_thin_rope(groups):
                return None                      # kare kesitli kutu (kuşak demiri, takoz) — silindir yapılmaz
            return ("ring", seg, groups, caps, mat, smooth)
    ell = _ellipsoid(pts, len(faces))
    if ell:
        return ("ellipsoid",) + ell + (mat, smooth)
    return None


def _ellipsoid(pts, nf):
    if len(pts) < 20:
        return None
    c = sum(pts, V()) / len(pts)
    cov = Matrix(((0, 0, 0), (0, 0, 0), (0, 0, 0)))
    for p in pts:
        d = p - c
        for i in range(3):
            for j in range(3):
                cov[i][j] += d[i] * d[j]
    # güç yinelemesiyle eksenler (3×3 simetrik)
    axes = []
    A = cov.copy()
    for _ in range(3):
        v = V((0.577, 0.577, 0.577))
        for a in axes:
            v -= a * v.dot(a)
        for _ in range(60):
            w = A @ v
            for a in axes:
                w -= a * w.dot(a)
            if w.length < 1e-12:
                break
            v = w.normalized()
        axes.append(v.normalized())
    ext = [max(abs((p - c).dot(a)) for p in pts) for a in axes]
    if min(ext) < 1e-4:
        return None
    for p in pts:
        d = p - c
        q = sum(((d.dot(a)) / e) ** 2 for a, e in zip(axes, ext))
        if abs(q - 1.0) > 0.08:
            return None
    u_seg = sum(1 for p in pts if abs((p - c).dot(axes[2])) < 1e-3 * ext[2] + 1e-6)
    return (c, axes, ext, max(u_seg, 1))


# ------------------------------------------------------------------ profil / yol sıklaştırma
def _rim_turns(rings):
    """Her halkada yüzey çizgilerinin (0°, 90°, 180°, 270° fazı) kırılma açısı (derece, en büyüğü)."""
    n = len(rings)
    out = [0.0] * n
    for i in range(1, n - 1):
        best = 0.0
        for ph in range(4):
            def rim(k):
                c, r, nn, u0 = rings[k]
                w = nn.cross(u0)
                a = ph * math.pi / 2
                return c + (u0 * math.cos(a) + w * math.sin(a)) * r
            d0, d1 = rim(i) - rim(i - 1), rim(i + 1) - rim(i)
            if d0.length > 1e-6 and d1.length > 1e-6:
                best = max(best, math.degrees(d0.angle(d1, 0.0)))
        out[i] = best
    return out


def _cr(p0, p1, p2, p3, t):
    t2, t3 = t * t, t * t * t
    return 0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3)


def _path_turns(rings):
    n = len(rings)
    out = [0.0] * n
    for i in range(1, n - 1):
        d0, d1 = rings[i][0] - rings[i - 1][0], rings[i + 1][0] - rings[i][0]
        if d0.length > 1e-6 and d1.length > 1e-6:
            out[i] = math.degrees(d0.angle(d1, 0.0))
    return out


def densify(groups, tol=0.0015, hard_deg=60.0, max_insert=8, max_insert_path=24, hard_path_deg=None):
    """R-R aralıklarında yüzey çizgisi kırılıyorsa ara halkalar ekler (Catmull-Rom merkez + yarıçap, normal slerp).
    Ek halka sayısı kiriş sapmasından: sapma ≈ L·θ/8 → k = ⌈√(sapma/tol)⌉. Lathe profilinde ≥ hard_deg kırılma
    kasıtlı köşedir (dokunulmaz); yol bükülen süpürmede (halat) köşe sayılmaz."""
    idx = [i for i, g in enumerate(groups) if g[0] == "R"]
    if len(idx) < 3:
        return groups, 0
    rings = [groups[i][1] for i in idx]
    rim, path = _rim_turns(rings), _path_turns(rings)
    hard = [(rim[i] >= hard_deg and path[i] < 5.0) or (hard_path_deg is not None and path[i] >= hard_path_deg)
            for i in range(len(rings))]                      # hard_path_deg: makaradan dönen halat — kırılma korunur
    out = [groups[i] for i in range(idx[0])]
    added = 0
    for j in range(len(rings)):
        out.append(("R", rings[j]))
        if j == len(rings) - 1:
            break
        c1, r1, n1, u1 = rings[j]
        c2, r2, n2, u2 = rings[j + 1]
        th = max(0.0 if hard[j] else rim[j], 0.0 if hard[j + 1] else rim[j + 1])
        if th < 1.0:
            continue
        L = max((c2 - c1).length, abs(r2 - r1))
        sag = L * math.radians(th) / 8.0
        cap = max_insert_path if max(path[j], path[j + 1]) >= 5.0 else max_insert
        k = min(cap, int(math.ceil(math.sqrt(sag / tol))))
        if k < 2:
            continue
        c0, r0 = (rings[j - 1][0], rings[j - 1][1]) if j > 0 and not hard[j] else (c1 - (c2 - c1), r1 - (r2 - r1))
        c3, r3 = (rings[j + 2][0], rings[j + 2][1]) if j + 2 < len(rings) and not hard[j + 1] else (c2 + (c2 - c1), r2 + (r2 - r1))
        for m in range(1, k):
            t = m / k
            c = _cr(c0, c1, c2, c3, t)
            r = max(_cr(V((r0, 0, 0)), V((r1, 0, 0)), V((r2, 0, 0)), V((r3, 0, 0)), t).x, 1e-5)
            n = n1.slerp(n2, t) if n1.dot(n2) > -0.99 else n1
            u = n1.rotation_difference(n) @ u1
            u = (u - n * u.dot(n)).normalized()
            out.append(("R", (c, r, n.normalized(), u)))
            added += 1
    out += [groups[i] for i in range(idx[-1] + 1, len(groups))]
    return out, added


# ------------------------------------------------------------------ yeniden kurma
def _build_rings(bm, groups, seg0, caps, seg, mat, smooth, uv):
    new_groups = []
    for kind, info in groups:
        if kind == "P":
            new_groups.append(("P", [bm.verts.new(info)]))
            continue
        c, r, n, u0 = info
        w = n.cross(u0)
        ring = [bm.verts.new(c + (u0 * math.cos(2 * math.pi * k / seg) + w * math.sin(2 * math.pi * k / seg)) * r)
                for k in range(seg)]
        new_groups.append(("R", ring, c))
    faces = []
    # boy koordinatı (V) — halka merkezleri boyunca biriken uzunluk
    vpos, acc, prev = [], 0.0, None
    for g in new_groups:
        p = g[1][0].co if g[0] == "P" else g[2]
        if prev is not None:
            acc += (p - prev).length
        vpos.append(acc)
        prev = p
    for gi, (a, b) in enumerate(zip(new_groups[:-1], new_groups[1:])):
        va, vb = vpos[gi], vpos[gi + 1]
        if a[0] == "R" and b[0] == "R":
            for k in range(seg):
                f = bm.faces.new([a[1][k], a[1][(k + 1) % seg], b[1][(k + 1) % seg], b[1][k]])
                faces.append((f, [(k / seg, va), ((k + 1) / seg, va), ((k + 1) / seg, vb), (k / seg, vb)]))
        elif a[0] == "P" and b[0] == "R":
            for k in range(seg):
                f = bm.faces.new([a[1][0], b[1][(k + 1) % seg], b[1][k]])
                faces.append((f, [((k + 0.5) / seg, va), ((k + 1) / seg, vb), (k / seg, vb)]))
        elif a[0] == "R" and b[0] == "P":
            for k in range(seg):
                f = bm.faces.new([a[1][k], a[1][(k + 1) % seg], b[1][0]])
                faces.append((f, [(k / seg, va), ((k + 1) / seg, va), ((k + 0.5) / seg, vb)]))
    rings = [g for g in new_groups if g[0] == "R"]
    if caps >= 1:
        f = bm.faces.new(list(reversed(rings[0][1])))
        faces.append((f, None))
    if caps >= 2:
        f = bm.faces.new(rings[-1][1])
        faces.append((f, None))
    for f, uvs in faces:
        f.material_index = mat
        f.smooth = smooth
        if uv is not None:
            if uvs is None:
                c = rings[0][2]
                uvs = [((l.vert.co - c).x, (l.vert.co - c).y) for l in f.loops]
            for l, t in zip(f.loops, uvs):
                l[uv].uv = t
    return [f for f, _ in faces]


def _build_ellipsoid(bm, c, axes, ext, seg, mat, smooth, uv):
    r = bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=max(seg // 2, 6), radius=1.0)
    M = Matrix.Translation(c) @ Matrix((
        (axes[0].x * ext[0], axes[1].x * ext[1], axes[2].x * ext[2], 0),
        (axes[0].y * ext[0], axes[1].y * ext[1], axes[2].y * ext[2], 0),
        (axes[0].z * ext[0], axes[1].z * ext[1], axes[2].z * ext[2], 0),
        (0, 0, 0, 1)))
    bmesh.ops.transform(bm, matrix=M, verts=r["verts"])
    fs = list({f for v in r["verts"] for f in v.link_faces})
    for f in fs:
        f.material_index = mat
        f.smooth = smooth
    return fs


def _parse_sweep(faces):
    """Dairesel olmayan kesitli süpürme (dikdörtgen/profil): köşeler m'lik halkalar halinde sıralı, dörtgenler i→i+1."""
    verts = sorted({v for f in faces for v in f.verts}, key=lambda v: v.index)
    n = len(verts)
    pos = {v: i for i, v in enumerate(verts)}
    quads = [f for f in faces if len(f.verts) == 4]
    for m in (4, 5, 6, 8, 10, 12, 16):
        if n % m or n // m < 3:
            continue
        nr = n // m
        ok, band = True, 0
        for f in faces:
            rs = {pos[v] // m for v in f.verts}
            if len(rs) == 1:
                if len(f.verts) != m:
                    ok = False
                    break
            elif len(rs) == 2 and len(f.verts) == 4 and max(rs) - min(rs) == 1:
                band += 1
            else:
                ok = False
                break
        if ok and band == m * (nr - 1):
            return m, [verts[i * m:(i + 1) * m] for i in range(nr)]
    return None


def densify_sweep(rings, tol=0.0015, hard_deg=45.0, max_insert=12):
    """Kesit köşe çizgilerinin (her köşe için bir çizgi) kırılmasına göre ara kesitler (Catmull-Rom) üretir."""
    pts = [[v.co.copy() for v in r] for r in rings]
    nr, m = len(pts), len(pts[0])

    def turn(i, c):
        if i <= 0 or i >= nr - 1:
            return 0.0
        a, b = pts[i][c] - pts[i - 1][c], pts[i + 1][c] - pts[i][c]
        return math.degrees(a.angle(b, 0.0)) if a.length > 1e-6 and b.length > 1e-6 else 0.0
    out, added = [pts[0]], 0
    for i in range(nr - 1):
        th = max(max(turn(i, c) for c in range(m)), max(turn(i + 1, c) for c in range(m)))
        if th >= hard_deg or th < 1.0:
            out.append(pts[i + 1])
            continue
        L = max((pts[i + 1][c] - pts[i][c]).length for c in range(m))
        k = min(max_insert, int(math.ceil(math.sqrt(L * math.radians(th) / 8.0 / tol))))
        for t in range(1, k):
            q = []
            for c in range(m):
                p0 = pts[max(i - 1, 0)][c]
                p3 = pts[min(i + 2, nr - 1)][c]
                q.append(_cr(p0, pts[i][c], pts[i + 1][c], p3, t / k))
            out.append(q)
            added += 1
        out.append(pts[i + 1])
    return out, added


def sharp_from_angle_keep(me, deg):
    """set_sharp_from_angle, ama elle işaretlenmiş keskin kenarları korur (Blender 5.0'da keep parametresi yok)."""
    att = me.attributes.get("sharp_edge")
    keep = [False] * len(me.edges)
    if att is not None and att.domain == "EDGE":
        att.data.foreach_get("value", keep)
    me.set_sharp_from_angle(angle=math.radians(deg))
    att = me.attributes.get("sharp_edge")
    if att is not None and any(keep):
        cur = [False] * len(me.edges)
        att.data.foreach_get("value", cur)
        att.data.foreach_set("value", [a or b for a, b in zip(cur, keep)])


def islands(bm):
    seen, out = set(), []
    for f in bm.faces:
        if f.index in seen:
            continue
        stack, isl = [f], []
        seen.add(f.index)
        while stack:
            a = stack.pop()
            isl.append(a)
            for e in a.edges:
                for g in e.link_faces:
                    if g.index not in seen:
                        seen.add(g.index)
                        stack.append(g)
        out.append(isl)
    return out


def resegment_mesh(me, scale=1.0, tol=0.0015, max_seg=64, min_seg=6, keep=None, sharp_deg=35, densify_paths=True,
                   hard_path_deg=None):
    """Mesh'i yerinde yeniden dilimler. scale: nesne → dünya ölçeği (yarıçap kuralı dünya metresinde).
    keep(info) True dönerse ada olduğu gibi kalır (ör. kasıtlı altıgen fener)."""
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.verts.index_update()
    bm.faces.index_update()
    uv = bm.loops.layers.uv.active
    rep = {"rings": 0, "ellipsoids": 0, "kept": 0, "skipped": 0}
    kill_verts, new_faces = [], []
    todo = []
    for isl in islands(bm):
        info = analyse_island(isl)
        if info is None:
            sw = _parse_sweep(isl) if densify_paths else None
            if sw:
                m, rings = sw
                new_rings, added = densify_sweep(rings, tol / max(scale, 1e-6))
                if added:
                    mat = isl[0].material_index
                    smooth = sum(f.smooth for f in isl) * 2 >= len(isl)
                    todo.append(("sweep", isl, new_rings, m, mat, smooth,
                                 [len(f.verts) == m and len({v.index for v in f.verts} & {v.index for v in rings[0]}) == m for f in isl],
                                 any(len(f.verts) == m and set(f.verts) == set(rings[-1]) for f in isl)))
                    rep["sweeps"] = rep.get("sweeps", 0) + 1
                    rep["rings_added"] = rep.get("rings_added", 0) + added
                    continue
            rep["skipped"] += 1
            continue
        if info[0] == "ring":
            _, seg0, groups, caps, mat, smooth = info
            rmax = max(g[1][1] for g in groups if g[0] == "R") * scale
            seg = max(seg0, required_segments(rmax, tol, min_seg, max_seg))
            if keep and keep({"kind": "ring", "seg": seg0, "r": rmax}):
                rep["kept"] += 1
                continue
            dgroups, added = densify(groups, tol / max(scale, 1e-6), hard_path_deg=hard_path_deg) if densify_paths else (groups, 0)
            if seg <= seg0 and not added:
                rep["kept"] += 1
                continue
            rep["rings_added"] = rep.get("rings_added", 0) + added
            todo.append(("ring", isl, dgroups, seg0, caps, seg, mat, smooth))
        else:
            _, c, axes, ext, useg0, mat, smooth = info
            rmax = max(ext) * scale
            seg = required_segments(rmax, tol, max(min_seg, 12), max_seg)
            if seg <= useg0 or (keep and keep({"kind": "ellipsoid", "seg": useg0, "r": rmax})):
                rep["kept"] += 1
                continue
            todo.append(("ell", isl, c, axes, ext, seg, mat, smooth))
    for t in todo:
        isl = t[1]
        kill_verts += list({v for f in isl for v in f.verts})
        if t[0] == "sweep":
            _, _, rings, m, mat, smooth, cap_flags, cap_end = t
            vr = [[bm.verts.new(p) for p in r] for r in rings]
            acc = [0.0]
            for a_, b_ in zip(rings[:-1], rings[1:]):
                acc.append(acc[-1] + (sum(b_, V()) / m - sum(a_, V()) / m).length)
            fs = []
            for i, (a_, b_) in enumerate(zip(vr[:-1], vr[1:])):
                for k in range(m):
                    f = bm.faces.new([a_[k], a_[(k + 1) % m], b_[(k + 1) % m], b_[k]])
                    if uv is not None:
                        for lp, t in zip(f.loops, [(acc[i], k / m), (acc[i], (k + 1) / m), (acc[i + 1], (k + 1) / m), (acc[i + 1], k / m)]):
                            lp[uv].uv = t
                    fs.append(f)
            if any(cap_flags):
                fs.append(bm.faces.new(list(reversed(vr[0]))))
            if cap_end:
                fs.append(bm.faces.new(vr[-1]))
            for f in fs:
                f.material_index = mat
                f.smooth = smooth
            new_faces += fs
            continue
        if t[0] == "ring":
            _, _, groups, seg0, caps, seg, mat, smooth = t
            new_faces += _build_rings(bm, groups, seg0, caps, seg, mat, smooth, uv)
            rep["rings"] += 1
        else:
            _, _, c, axes, ext, seg, mat, smooth = t
            new_faces += _build_ellipsoid(bm, c, axes, ext, seg, mat, smooth, uv)
            rep["ellipsoids"] += 1
    if kill_verts:
        bmesh.ops.delete(bm, geom=list(set(kill_verts)), context="VERTS")
    if new_faces:
        bmesh.ops.recalc_face_normals(bm, faces=[f for f in new_faces if f.is_valid])
    bm.to_mesh(me)
    bm.free()
    if todo:
        sharp_from_angle_keep(me, sharp_deg)
    me.update()
    return rep


def resegment_object(ob, **kw):
    s = sum(ob.matrix_world.to_scale()) / 3.0
    return resegment_mesh(ob.data, scale=s, **kw)
