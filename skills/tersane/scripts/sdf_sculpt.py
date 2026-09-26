"""Tersane — SDF (işaretli mesafe alanı) ile yontu: figür, arma, oyma süsleme.

Neden: metaball "damlası" oyuncak gibi yumuşak kalır; SDF'de biçimler yumuşak birleşir (smooth union), keskin oyulur
(smooth subtraction), ince tutamlar (fur lock) arasında oyma vadileri kalır. Tüm parçalar tek alanda olduğu için sonuç
**tek parça, kapalı** mesh'tir (oyunda figür tek parça). Bölge başına malzeme kimliği (göz, diş, dil…) alanla birlikte
taşınır ve yüzeye aktarılır.

    import sdf_sculpt as S
    g = S.Grid((-1, -1, -1), (1, 1, 1), voxel=0.006)
    g.union(S.Ellipsoid((0, 0, 0), (0.3, 0.2, 0.2)), k=0.05, mat=0)
    g.union(S.RoundCone((0.2, 0, 0), (0.6, 0, -0.05), 0.12, 0.07), k=0.06)
    g.union(S.Chain(S.bezier([(…), (…), (…), (…)], 8), [0.05, 0.01], flat=((0, 1, 0), 0.5)), k=0.012)   # tutam
    g.subtract(S.Ellipsoid(...), k=0.01)                                                              # oyma
    verts, faces, face_mat = g.mesh()
    me = S.to_blender("MOD_X", verts, faces, face_mat, [mat0, mat1])

Gereken: numpy < 2, scikit-image (marching cubes) — `pip install "numpy==1.26.4" "scikit-image==0.22.0" "scipy<1.15"`.
Voksel 5–6 mm: 2,4 m figürde ~40 M voksel (~200 MB), yüzey ~0,5 M üçgen → Blender'da azalt (Decimate).
"""

import math

import numpy as np


# ------------------------------------------------------------------ yardımcılar
def _v(p):
    return np.asarray(p, dtype=np.float64)


def rot_to(x_axis, z_hint=(0, 0, 1)):
    """Yerel X'i x_axis'e çeviren 3×3 dönüş (sütunlar yerel eksenler, dünya koordinatında)."""
    x = _v(x_axis)
    x = x / np.linalg.norm(x)
    z = _v(z_hint)
    z = z - x * np.dot(z, x)
    if np.linalg.norm(z) < 1e-6:
        z = np.array([0.0, 1.0, 0.0]) - x * x[1]
    z = z / np.linalg.norm(z)
    y = np.cross(z, x)
    return np.stack([x, y, z], axis=1)


def bezier(ctrl, n):
    """Kübik Bezier (4 nokta) ya da Catmull-Rom (≥ 5 nokta) örnekleri."""
    c = [_v(p) for p in ctrl]
    if len(c) == 4:
        out = []
        for i in range(n + 1):
            t = i / n
            out.append((1 - t) ** 3 * c[0] + 3 * (1 - t) ** 2 * t * c[1] + 3 * (1 - t) * t ** 2 * c[2] + t ** 3 * c[3])
        return out
    out = []
    pts = [c[0]] + c + [c[-1]]
    seg = len(c) - 1
    per = max(1, n // seg)
    for s in range(seg):
        p0, p1, p2, p3 = pts[s], pts[s + 1], pts[s + 2], pts[s + 3]
        for j in range(per):
            t = j / per
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(c[-1])
    return out


# ------------------------------------------------------------------ ilkel biçimler
class Prim:
    def bbox(self):
        raise NotImplementedError

    def dist(self, X, Y, Z):
        raise NotImplementedError


class Ellipsoid(Prim):
    def __init__(self, c, r, x_axis=(1, 0, 0), z_hint=(0, 0, 1)):
        self.c, self.r = _v(c), _v(r)
        self.R = rot_to(x_axis, z_hint)

    def bbox(self):
        e = np.abs(self.R) @ self.r
        return self.c - e, self.c + e

    def dist(self, X, Y, Z):
        dx, dy, dz = X - self.c[0], Y - self.c[1], Z - self.c[2]
        R = self.R
        lx = dx * R[0, 0] + dy * R[1, 0] + dz * R[2, 0]
        ly = dx * R[0, 1] + dy * R[1, 1] + dz * R[2, 1]
        lz = dx * R[0, 2] + dy * R[1, 2] + dz * R[2, 2]
        k0 = np.sqrt((lx / self.r[0]) ** 2 + (ly / self.r[1]) ** 2 + (lz / self.r[2]) ** 2)
        k1 = np.sqrt((lx / self.r[0] ** 2) ** 2 + (ly / self.r[1] ** 2) ** 2 + (lz / self.r[2] ** 2) ** 2)
        return k0 * (k0 - 1.0) / np.maximum(k1, 1e-9)            # iq yaklaşık elipsoit SDF


class RoundCone(Prim):
    """a→b doğru parçası, yarıçap ra→rb. flat=(eksen, oran): o eksen boyunca kesit basıklaşır (şerit/tüy tutamı)."""

    def __init__(self, a, b, ra, rb, flat=None):
        self.a, self.b, self.ra, self.rb = _v(a), _v(b), float(ra), float(rb)
        self.flat = None if flat is None else (_v(flat[0]) / np.linalg.norm(flat[0]), float(flat[1]))

    def bbox(self):
        r = max(self.ra, self.rb)
        return np.minimum(self.a, self.b) - r, np.maximum(self.a, self.b) + r

    def dist(self, X, Y, Z):
        ba = self.b - self.a
        L2 = max(float(np.dot(ba, ba)), 1e-12)
        px, py, pz = X - self.a[0], Y - self.a[1], Z - self.a[2]
        t = np.clip((px * ba[0] + py * ba[1] + pz * ba[2]) / L2, 0.0, 1.0)
        qx, qy, qz = px - t * ba[0], py - t * ba[1], pz - t * ba[2]
        if self.flat is not None:
            f, s = self.flat
            qf = qx * f[0] + qy * f[1] + qz * f[2]
            m = (1.0 / s - 1.0) * qf
            qx, qy, qz = qx + m * f[0], qy + m * f[1], qz + m * f[2]
        return np.sqrt(qx * qx + qy * qy + qz * qz) - (self.ra + (self.rb - self.ra) * t)


class Chain(Prim):
    """Nokta dizisi boyunca konik kapsüller (tutam, kaş, dudak çizgisi). radii: [başlangıç, bitiş] ya da nokta başına."""

    def __init__(self, pts, radii, flat=None):
        self.pts = [_v(p) for p in pts]
        n = len(self.pts)
        if len(radii) == 2 and n != 2:
            radii = [radii[0] + (radii[1] - radii[0]) * i / (n - 1) for i in range(n)]
        self.segs = [RoundCone(self.pts[i], self.pts[i + 1], radii[i], radii[i + 1], flat) for i in range(n - 1)]

    def bbox(self):
        bs = [s.bbox() for s in self.segs]
        return np.min([b[0] for b in bs], axis=0), np.max([b[1] for b in bs], axis=0)

    def dist(self, X, Y, Z):
        d = None
        for s in self.segs:
            e = s.dist(X, Y, Z)
            d = e if d is None else np.minimum(d, e)
        return d


# ------------------------------------------------------------------ ızgara
class Grid:
    def __init__(self, lo, hi, voxel=0.006):
        self.lo, self.hi, self.h = _v(lo), _v(hi), float(voxel)
        self.n = np.ceil((self.hi - self.lo) / self.h).astype(int) + 1
        self.d = np.full(tuple(self.n), 10.0, dtype=np.float32)
        self.m = np.zeros(tuple(self.n), dtype=np.int8)

    def _region(self, prim, pad):
        b0, b1 = prim.bbox()
        i0 = np.maximum(np.floor((b0 - pad - self.lo) / self.h).astype(int), 0)
        i1 = np.minimum(np.ceil((b1 + pad - self.lo) / self.h).astype(int) + 1, self.n)
        if np.any(i1 <= i0):
            return None
        xs = self.lo[0] + self.h * np.arange(i0[0], i1[0])
        ys = self.lo[1] + self.h * np.arange(i0[1], i1[1])
        zs = self.lo[2] + self.h * np.arange(i0[2], i1[2])
        X, Y, Z = np.meshgrid(xs, ys, zs, indexing="ij")
        sl = tuple(slice(a, b) for a, b in zip(i0, i1))
        return sl, X, Y, Z

    def _chain_dist(self, prim, sl, pad):
        """Zincir: her parça yalnız kendi küçük kutusunda hesaplanır, zincir içi sert min (eklemde şişme olmaz)."""
        shape = tuple(x.stop - x.start for x in sl)
        out = np.full(shape, 10.0)
        base = np.array([x.start for x in sl])
        for seg in prim.segs:
            reg = self._region(seg, pad)
            if reg is None:
                continue
            ssl, X, Y, Z = reg
            lo = np.array([x.start for x in ssl]) - base
            hi = np.array([x.stop for x in ssl]) - base
            lo2, hi2 = np.maximum(lo, 0), np.minimum(hi, shape)
            if np.any(hi2 <= lo2):
                continue
            cut = tuple(slice(a - l, b - l) for a, b, l in zip(lo2, hi2, lo))
            dst = tuple(slice(a, b) for a, b in zip(lo2, hi2))
            out[dst] = np.minimum(out[dst], seg.dist(X[cut], Y[cut], Z[cut]))
        return out

    def union(self, prim, k=0.02, mat=0, field_pad=0.10):
        # field_pad: yüzey çevresinde gerçek mesafe alanı (yansıtma/gradyan için); uzak alan sabit kalır
        pad = max(k + 2 * self.h, field_pad)
        reg = self._region(prim, pad)
        if reg is None:
            return
        sl, X, Y, Z = reg
        a = self.d[sl].astype(np.float64)
        b = self._chain_dist(prim, sl, pad) if isinstance(prim, Chain) else prim.dist(X, Y, Z)
        if k > 0:
            h = np.clip(0.5 + 0.5 * (a - b) / k, 0.0, 1.0)
            r = a * (1 - h) + b * h - k * h * (1 - h)
        else:
            r = np.minimum(a, b)
        mm = self.m[sl]
        mm[b < a] = mat
        self.m[sl] = mm
        self.d[sl] = r.astype(np.float32)

    def subtract(self, prim, k=0.01):
        reg = self._region(prim, k + 2 * self.h)
        if reg is None:
            return
        sl, X, Y, Z = reg
        a = self.d[sl].astype(np.float64)
        b = self._chain_dist(prim, sl, k + 2 * self.h) if isinstance(prim, Chain) else prim.dist(X, Y, Z)
        if k > 0:
            h = np.clip(0.5 - 0.5 * (a + b) / k, 0.0, 1.0)
            r = a * (1 - h) + (-b) * h + k * h * (1 - h)
        else:
            r = np.maximum(a, -b)
        self.d[sl] = r.astype(np.float32)

    # --- örnekleme ve yüzeye yansıtma (tüy tutamlarını mevcut yüzeye yatırmak için)
    def sample(self, P):
        """Üç doğrusal enterpolasyonla mesafe (P: (N,3))."""
        P = np.atleast_2d(np.asarray(P, dtype=np.float64))
        q = (P - self.lo) / self.h
        q = np.clip(q, 0, self.n - 1.001)
        i0 = np.floor(q).astype(int)
        f = q - i0
        i1 = np.minimum(i0 + 1, self.n - 1)
        d = self.d
        out = np.zeros(len(P))
        for dx in (0, 1):
            ix = i1[:, 0] if dx else i0[:, 0]
            wx = f[:, 0] if dx else 1 - f[:, 0]
            for dy in (0, 1):
                iy = i1[:, 1] if dy else i0[:, 1]
                wy = f[:, 1] if dy else 1 - f[:, 1]
                for dz in (0, 1):
                    iz = i1[:, 2] if dz else i0[:, 2]
                    wz = f[:, 2] if dz else 1 - f[:, 2]
                    out += wx * wy * wz * d[ix, iy, iz]
        return out

    def normal(self, P):
        P = np.atleast_2d(np.asarray(P, dtype=np.float64))
        e = self.h
        g = np.stack([self.sample(P + np.array([e, 0, 0])) - self.sample(P - np.array([e, 0, 0])),
                      self.sample(P + np.array([0, e, 0])) - self.sample(P - np.array([0, e, 0])),
                      self.sample(P + np.array([0, 0, e])) - self.sample(P - np.array([0, 0, e]))], axis=1)
        return g / np.maximum(np.linalg.norm(g, axis=1, keepdims=True), 1e-9)

    def project(self, P, iters=8):
        """Noktaları sıfır yüzeyine taşır; (noktalar, normaller, geçerli) döner. Uzak alanda (gradyan yok) geçersiz."""
        P = np.atleast_2d(np.asarray(P, dtype=np.float64)).copy()
        for _ in range(iters):
            d = np.nan_to_num(self.sample(P), nan=0.0)
            n = np.nan_to_num(self.normal(P))
            step = np.clip(d, -0.08, 0.08)                   # büyük sıçramaları kes
            P = P - step[:, None] * n
        ok = np.abs(np.nan_to_num(self.sample(P), nan=9.0)) < 2.5 * self.h
        return P, self.normal(P), ok

    def mesh(self, step=1):
        from skimage.measure import marching_cubes
        v, f, _, _ = marching_cubes(self.d, level=0.0, spacing=(self.h,) * 3, step_size=step, allow_degenerate=False)
        v = v + self.lo
        c = v[f].mean(axis=1)                                   # yüz merkezi → en yakın voksel → malzeme
        idx = np.clip(np.rint((c - self.lo) / self.h).astype(int), 0, self.n - 1)
        # yüzeyin hemen içindeki vokseli seç (merkez yüzeyde; içeri bakan komşunun kimliği daha güvenilir)
        fm = self.m[idx[:, 0], idx[:, 1], idx[:, 2]].astype(np.int32)
        return v, f, fm


def to_blender(name, verts, faces, face_mat, mats, flip=False):
    import bpy
    me = bpy.data.meshes.new(name)
    f = faces[:, ::-1] if flip else faces
    me.from_pydata(verts.tolist(), [], f.tolist())
    me.update()
    for m in mats:
        me.materials.append(m)
    me.polygons.foreach_set("material_index", face_mat.tolist())
    me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
    me.update()
    return me


def poisson_seeds(P, spacing, rng=None):
    """Nokta kümesini en az `spacing` aralıkla seyreltir (basit ızgara karması)."""
    P = np.asarray(P)
    order = np.arange(len(P)) if rng is None else rng.permutation(len(P))
    cell = {}
    keep = []
    for i in order:
        p = P[i]
        key = tuple((p // spacing).astype(int))
        ok = True
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    for j in cell.get((key[0] + dx, key[1] + dy, key[2] + dz), ()):
                        if np.linalg.norm(P[j] - p) < spacing:
                            ok = False
                            break
                    if not ok:
                        break
                if not ok:
                    break
            if not ok:
                break
        if ok:
            keep.append(i)
            cell.setdefault(key, []).append(i)
    return P[keep]


def components(verts, faces):
    """Bileşen etiketleri (yüz başına) ve bileşen yüz sayıları."""
    parent = np.arange(len(verts))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for a, b, c in faces:
        ra, rb, rc = find(a), find(b), find(c)
        parent[rb] = ra
        parent[find(rc)] = ra
    lab = np.array([find(a) for a in faces[:, 0]])
    uniq, inv, cnt = np.unique(lab, return_inverse=True, return_counts=True)
    return inv, cnt


def islands_count(verts, faces):
    """Bağlı bileşen sayısı (tek parça doğrulaması) — birleşim-bul."""
    parent = np.arange(len(verts))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for a, b, c in faces:
        ra, rb, rc = find(a), find(b), find(c)
        parent[rb] = ra
        parent[find(rc)] = ra
    return len({find(i) for i in np.unique(faces)})
