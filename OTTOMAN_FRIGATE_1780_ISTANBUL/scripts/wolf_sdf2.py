"""Bozkurt pruva figürü — SDF yontusu v036 (wolf_sdf.py v035'in sürümü; v035 kaynağı değişmeden kalır).

v036 farkı: tüy tutamları birbirine yumuşak kaynar (CLUMP_K 0,012; kabarma ×0,85) → tek tek "solucan" tüpler yerine
oyma/döküm bir yele kütlesi; clean_mats() ile diş/dil/göz sınırındaki tek-yüz malzeme tırtıkları temizlenir.
Önceki denemeler (basık oluklu "kiremit" tutamlar) çukur/delik bıraktığı için bırakıldı.

Koordinat: figür-yerel (orijin = SOCKET_FIGUREHEAD, baş kıvrımının üst ucu; +X ileri, +Z yukarı; metre).
Kafa ayrı bir yerel çerçevede tanımlanır (orijin = art kafa/occiput, +X burna doğru) ve H() ile figüre yerleşir.
Oranlar gerçek kurt kafasına göre ölçeklenmiş (kafa boyu L = 1,10 m; kafatası %55, burun %45) [TAHMİN, üslup: oyma figür].
Malzeme kimlikleri: 0 tunç gövde, 1 göz (kehribar), 2 diş (fildişi), 3 dil/diş eti, 4 burun (siyah), 5 altın (kaide sarmalı).
"""

import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "skills" / "tersane" / "scripts"))
import sdf_sculpt as S  # noqa: E402

V = np.array

PITCH = math.radians(6.0)                 # burun hafif aşağı
F = V([0.30, 0.0, 0.92])                  # art kafanın figürdeki yeri
JAW = math.radians(30.0)                  # çene açıklığı
PIVOT = V([0.46, 0.0, -0.13])             # çene menteşesi (kafa-yerel)


def H(p):
    """kafa-yerel → figür-yerel."""
    x, y, z = p
    c, s = math.cos(PITCH), math.sin(PITCH)
    return F + V([x * c + z * s, y, -x * s + z * c])


def Hinv(P):
    """figür-yerel (N,3) → kafa-yerel."""
    c, s_ = math.cos(PITCH), math.sin(PITCH)
    Q = np.asarray(P) - F
    return np.stack([Q[:, 0] * c - Q[:, 2] * s_, Q[:, 1], Q[:, 0] * s_ + Q[:, 2] * c], axis=1)


def Hd(d):
    x, y, z = d
    c, s = math.cos(PITCH), math.sin(PITCH)
    return V([x * c + z * s, y, -x * s + z * c])


def J(xr, y, zr):
    """çene-yerel (menteşeden, çene ekseni boyunca) → kafa-yerel."""
    c, s = math.cos(JAW), math.sin(JAW)
    return PIVOT + V([xr * c + zr * s, y, -xr * s + zr * c])


def HJ(xr, y, zr):
    return H(J(xr, y, zr))


def E(c, r, ax=(1, 0, 0), z=(0, 0, 1)):
    return S.Ellipsoid(H(c), r, Hd(ax), Hd(z))


def RC(a, b, ra, rb, flat=None):
    f = None if flat is None else (Hd(flat[0]), flat[1])
    return S.RoundCone(H(a), H(b), ra, rb, f)


def CH(pts, radii, flat=None, n=10):
    f = None if flat is None else (Hd(flat[0]), flat[1])
    ps = S.bezier([H(p) for p in pts], n) if len(pts) >= 4 else [H(p) for p in pts]
    return S.Chain(ps, radii, f)


CLUMP_K, LIFT_S = 0.012, 0.85     # v036: tutamlar birbirine yumuşak kaynar (tek oyma kütle), daha alçak kabarma


def clump(g, p0, p1, width, lift=0.024, flat=0.34, sway=0.0, mat=0, k=None, n=7):
    """Yüzeye yatan tüy tutamı: p0→p1 arası noktalar mevcut yüzeye yansıtılır, normal boyunca kabartılır;
    kalın dip, sivri uç, normal doğrultusunda basık (oyma tüy görünümü). sway: yana S kıvrımı (m)."""
    k = CLUMP_K if k is None else k
    lift = lift * LIFT_S
    p0, p1 = V(p0, dtype=float), V(p1, dtype=float)
    ts = np.linspace(0, 1, n)
    side = np.cross(p1 - p0, V([0.0, 0.0, 1.0]))
    side = side / max(np.linalg.norm(side), 1e-9)
    raw = np.array([p0 + (p1 - p0) * t + side * sway * math.sin(math.pi * t) for t in ts])
    q, nr, ok = g.project(raw)
    if not ok.all():
        return False
    prof = np.clip(0.35 + 0.65 * np.sin(np.pi * np.clip(ts * 0.8 + 0.1, 0, 1)), 0, 1) * np.clip(ts * 4, 0, 1)
    pts = q + nr * (lift * prof - 0.008)[:, None]                  # dip gömük, gövde kabarık, uç hafif kalkık
    radii = width * np.maximum((1.0 - ts) ** 0.85, 0.10)           # hızla sivrilen oyma tüy şeridi
    nm = nr.mean(axis=0)
    nm = nm / max(np.linalg.norm(nm), 1e-9)
    ch = S.Chain(S.bezier(list(pts), 32), list(np.interp(np.linspace(0, 1, 33), ts, radii)), (nm, flat))
    g.union(ch, k=k, mat=mat)
    return True


def fur_field(g, lo, hi, keep, flow, spacing, length, width, lift, rng, n_cand=9000, flat=0.38):
    """Bölgeye tohum dağıt → yüzeye yansıt → eşit aralıkla seyrelt → akış yönünde tutam."""
    cand = lo + (hi - lo) * rng.random((n_cand, 3))
    d = g.sample(cand)
    cand = cand[np.abs(d) < 0.09]
    if not len(cand):
        return 0
    q, nr, ok = g.project(cand)
    q, nr = q[ok], nr[ok]
    m = keep(q)
    q, nr = q[m], nr[m]
    seeds = S.poisson_seeds(q, spacing, rng)
    n_ok = 0
    for p in seeds:
        nrm = g.normal(p[None])[0]
        f = flow(p)
        f = f - nrm * np.dot(f, nrm)
        if np.linalg.norm(f) < 1e-6:
            continue
        f = f / np.linalg.norm(f)
        L, w, lf = length(p), width(p), lift(p)
        sw = 0.035 * math.sin(7.0 * p[1] + 4.0 * p[2] + 3.0 * p[0])     # tutarlı dalga (akış kıvrımı)
        if clump(g, p, p + f * L, w, lift=lf, sway=sw, flat=flat):
            n_ok += 1
    return n_ok


def build(voxel=0.006):
    g = S.Grid((-1.20, -0.80, -0.35), (1.62, 0.80, 1.62), voxel)
    U, SUB = g.union, g.subtract
    rng = np.random.default_rng(7)
    # ---------------- kaide + göğüs + boyun (figür-yerel)
    U(S.Ellipsoid((-0.15, 0, 0.02), (0.58, 0.46, 0.22)), k=0.06, mat=0)
    U(S.Ellipsoid((-0.08, 0, 0.34), (0.46, 0.40, 0.40)), k=0.12, mat=0)
    U(S.RoundCone((-0.05, 0, 0.45), H((0.14, 0, -0.06)), 0.34, 0.25), k=0.12, mat=0)
    for i in range(40):                                # kaide kuşağı: altın gadroon (dikey kabarık oluklar)
        a = 2 * math.pi * i / 40
        c, s_ = math.cos(a), math.sin(a)
        p_top = V([-0.15 + 0.60 * c, 0.48 * s_, 0.10])
        p_bot = V([-0.15 + 0.60 * c, 0.48 * s_, -0.07])
        q, _, ok = g.project(np.array([p_top, (p_top + p_bot) / 2, p_bot]))
        if ok.all():
            U(S.Chain(list(q), [0.028, 0.030, 0.022]), k=0.010, mat=5)
    for s in (1, -1):                                  # kaide yanlarında altın rumi sarmalları
        pts = []
        for k in range(70):
            t = k / 69
            a = 0.2 + t * 3.1 * math.pi
            r = 0.17 * (1 - 0.82 * t)
            pts.append((-0.25 + r * math.cos(a), s * 0.40, 0.04 + r * math.sin(a) * 0.9))
        q, _, _ = g.project(np.array(pts))
        U(S.Chain(list(q + np.array([0, s * 0.012, 0])), [0.030, 0.012]), k=0.012, mat=5)
    # ---------------- kafatası
    U(E((0.30, 0, 0.02), (0.31, 0.24, 0.22)), k=0.10)
    U(RC((0.05, 0, 0.15), (0.40, 0, 0.21), 0.05, 0.04), k=0.06)
    for s in (1, -1):
        U(E((0.25, 0.16 * s, 0.08), (0.20, 0.09, 0.13)), k=0.07)
        U(E((0.47, 0.19 * s, -0.07), (0.17, 0.08, 0.09), (1, 0.25 * s, 0)), k=0.09)
    U(E((0.55, 0, 0.09), (0.14, 0.15, 0.10)), k=0.08)
    # ---------------- burun (namlu)
    U(RC((0.55, 0, -0.01), (1.02, 0, -0.035), 0.145, 0.085), k=0.07)
    U(RC((0.58, 0, 0.08), (1.02, 0, 0.02), 0.075, 0.048), k=0.05)
    for s in (1, -1):
        U(RC((0.62, 0.08 * s, -0.08), (1.00, 0.05 * s, -0.095), 0.075, 0.048), k=0.05)
        U(RC((0.64, 0.085 * s, -0.125), (1.00, 0.05 * s, -0.115), 0.028, 0.022), k=0.012, mat=3)
    # ---------------- alt çene (açık) + dil
    for s in (1, -1):
        U(S.RoundCone(HJ(0.0, 0.12 * s, -0.02), HJ(0.50, 0.045 * s, -0.03), 0.080, 0.050), k=0.06)
        U(S.RoundCone(HJ(0.10, 0.085 * s, 0.03), HJ(0.48, 0.045 * s, 0.02), 0.025, 0.02), k=0.012, mat=3)
        U(E((0.40, 0.14 * s, -0.19), (0.12, 0.06, 0.09)), k=0.10)                         # yanak–çene köşesi (yumuşak)
    U(S.RoundCone(HJ(0.05, 0, -0.04), HJ(0.48, 0, -0.05), 0.095, 0.055), k=0.06)
    U(S.Ellipsoid(HJ(0.50, 0, -0.06), (0.065, 0.065, 0.055)), k=0.04)
    tj = Hd(np.array([math.sin(JAW), 0, math.cos(JAW)]))
    U(S.Chain([HJ(0.06, 0, 0.00), HJ(0.26, 0, 0.025), HJ(0.42, 0, 0.035)], [0.062, 0.045], (tj, 0.35)), k=0.012, mat=3)
    # ---------------- kulaklar (büyük, geriye yatık) — tüyden önce, kulak kökü tüylerle örtülsün
    for s in (1, -1):
        base, tip = V([0.22, 0.17 * s, 0.17]), V([-0.16, 0.30 * s, 0.46])
        n = V([0.30, 0.94 * s, 0.10])
        axis = (tip - base) / np.linalg.norm(tip - base)
        U(RC(base, tip, 0.135, 0.016, (n, 0.40)), k=0.05)
        SUB(RC(base + n * 0.040 + axis * 0.05, tip - axis * 0.07 + n * 0.024, 0.085, 0.010, (n, 0.34)), k=0.010)
    # ---------------- tüyler: tüy alanı üreteci (yüzeye yatan, üst üste binen tutamlar)
    headx = lambda P: Hinv(P)[:, 0]                                              # noqa: E731
    ear_axes = [(V([0.22, 0.17 * s_, 0.17]), V([-0.16, 0.30 * s_, 0.46])) for s_ in (1, -1)]

    def off_ears(P, clear=0.075):
        Q = Hinv(P)
        ok = np.ones(len(Q), bool)
        for a, b in ear_axes:
            ab = b - a
            t = np.clip(((Q - a) @ ab) / (ab @ ab), 0, 1)
            dist = np.linalg.norm(Q - (a + t[:, None] * ab), axis=1)
            ok &= dist > (0.135 * (1 - t) + 0.016 * t) + clear
        return ok
    fig = lambda lo_, hi_: (V(lo_, dtype=float), V(hi_, dtype=float))            # noqa: E731
    stats = {}
    # boyun/göğüs postu + sırtta yele (kafanın arkası ve altı; kaide çıplak)
    lo_, hi_ = fig((-0.95, -0.62, 0.22), (0.95, 0.62, 1.45))

    def keep_neck(P):
        hx = headx(P)
        return (P[:, 2] > 0.26) & ((hx < 0.30) | (Hinv(P)[:, 2] < -0.28)) & off_ears(P)

    def flow_neck(p):
        s_ = 1.0 if p[1] >= 0 else -1.0
        return V([-0.78, 0.28 * s_ * min(1.0, abs(p[1]) / 0.25), -0.60])

    crest = lambda p: abs(p[1]) < 0.14 and p[2] > 0.70                           # noqa: E731
    stats["boyun"] = fur_field(g, lo_, hi_, keep_neck, flow_neck, 0.075,
                               lambda p: 0.46 if crest(p) else 0.38, lambda p: 0.080 if crest(p) else 0.070,
                               lambda p: 0.046 if crest(p) else 0.030, rng)
    # yanak yelesi (elmacık arkası, çene köşesi) — geriye
    lo_, hi_ = fig((0.20, -0.45, 0.45), (1.05, 0.45, 1.20))

    def keep_cheek(P):
        Q = Hinv(P)
        return (Q[:, 0] > 0.26) & (Q[:, 0] < 0.56) & (np.abs(Q[:, 1]) > 0.13) & (Q[:, 2] < 0.06) & (Q[:, 2] > -0.32)

    def flow_cheek(p):
        s_ = 1.0 if p[1] >= 0 else -1.0
        return Hd(V([-1.0, 0.22 * s_, -0.30]))
    stats["yanak"] = fur_field(g, lo_, hi_, keep_cheek, flow_cheek, 0.052, lambda p: 0.26, lambda p: 0.052, lambda p: 0.026, rng)
    # alın / tepe — kısa, alçak
    lo_, hi_ = fig((0.25, -0.30, 0.95), (1.05, 0.30, 1.30))

    def keep_crown(P):
        Q = Hinv(P)
        return (Q[:, 0] > 0.06) & (Q[:, 0] < 0.57) & (Q[:, 2] > 0.07) & (np.abs(Q[:, 1]) < 0.22) & off_ears(P)
    stats["tepe"] = fur_field(g, lo_, hi_, keep_crown, lambda p: Hd(V([-1.0, 0.0, 0.05])), 0.040,
                              lambda p: 0.17, lambda p: 0.030, lambda p: 0.010, rng)
    # boğaz — aşağı
    lo_, hi_ = fig((0.20, -0.30, 0.45), (0.95, 0.30, 0.95))

    def keep_throat(P):
        Q = Hinv(P)
        return (Q[:, 0] > 0.12) & (Q[:, 0] < 0.46) & (Q[:, 2] < -0.20)
    stats["bogaz"] = fur_field(g, lo_, hi_, keep_throat, lambda p: V([-0.25, 0.0, -1.0]), 0.060,
                               lambda p: 0.30, lambda p: 0.058, lambda p: 0.024, rng)
    g.fur_stats = stats
    # ---------------- oymalar (tüyden sonra): kırışık, dudak, burun, göz, kaş
    for i, x in enumerate((0.72, 0.79, 0.86, 0.925)):                  # hırlama kıvrımları (kabarık) + aralarında sığ oluk
        r = 0.016 - 0.0015 * i
        for s in (1, -1):
            U(CH([(x + 0.012, 0.105 * s, -0.02), (x + 0.004, 0.075 * s, 0.05), (x - 0.006, 0.035 * s, 0.087), (x - 0.008, 0.0, 0.093)],
                 [r, r * 0.8], n=24), k=0.020)
            SUB(CH([(x + 0.047, 0.10 * s, -0.02), (x + 0.039, 0.07 * s, 0.05), (x + 0.029, 0.03 * s, 0.084), (x + 0.027, 0.0, 0.088)],
                   [0.007, 0.006], n=24), k=0.010)
    for s in (1, -1):
        SUB(CH([(0.55, 0.13 * s, -0.12), (0.75, 0.12 * s, -0.10), (1.0, 0.075 * s, -0.08)], [0.011, 0.008], n=12), k=0.008)
    U(E((1.075, 0, -0.005), (0.055, 0.07, 0.05)), k=0.015, mat=4)
    for s in (1, -1):
        SUB(E((1.115, 0.03 * s, -0.018), (0.020, 0.014, 0.013), (1, 0.5 * s, -0.3)), k=0.006)
    SUB(RC((1.118, 0, -0.03), (1.10, 0, -0.075), 0.007, 0.005), k=0.004)
    for s in (1, -1):
        ax = (1, 0.55 * s, 0.25)
        SUB(E((0.66, 0.158 * s, 0.075), (0.052, 0.034, 0.032), ax), k=0.014)
        U(E((0.652, 0.150 * s, 0.072), (0.040, 0.026, 0.026), ax), k=0.004, mat=1)
        U(CH([(0.60, 0.172 * s, 0.10), (0.66, 0.154 * s, 0.114), (0.715, 0.12 * s, 0.097)], [0.014, 0.010], n=24), k=0.030)
        U(CH([(0.55, 0.19 * s, 0.14), (0.63, 0.13 * s, 0.165), (0.69, 0.06 * s, 0.135)], [0.036, 0.024], n=24), k=0.075)
        SUB(RC((0.62, 0.026 * s, 0.17), (0.69, 0.020 * s, 0.12), 0.009, 0.007), k=0.008)
    # ---------------- dişler (en son; kökleri diş etine gömülü)
    for s in (1, -1):
        U(S.Chain([H((0.945, 0.066 * s, -0.09)), H((0.968, 0.071 * s, -0.19)), H((0.955, 0.068 * s, -0.255))], [0.025, 0.004]), k=0.003, mat=2)
        U(S.Chain([HJ(0.44, 0.056 * s, 0.00), HJ(0.455, 0.060 * s, 0.09), HJ(0.445, 0.058 * s, 0.14)], [0.023, 0.004]), k=0.003, mat=2)
        for i, y in enumerate((0.013, 0.030, 0.047)):
            x = 1.005 - 0.012 * i
            U(S.RoundCone(H((x, y * s, -0.09)), H((x + 0.004, y * s, -0.16)), 0.011, 0.006), k=0.003, mat=2)
            U(S.RoundCone(HJ(0.485 - 0.01 * i, y * s, 0.005), HJ(0.49 - 0.01 * i, y * s, 0.075), 0.010, 0.005), k=0.003, mat=2)
        for x, rr, ln in ((0.64, 0.022, 0.07), (0.72, 0.016, 0.05), (0.80, 0.015, 0.045), (0.88, 0.014, 0.04)):
            y = (0.088 - 0.03 * (x - 0.64)) * s
            U(S.RoundCone(H((x, y, -0.11)), H((x + 0.01, y, -0.125 - ln)), rr, 0.004), k=0.003, mat=2)
        for xr in (0.20, 0.28, 0.36):
            U(S.RoundCone(HJ(xr, 0.078 * s, 0.015), HJ(xr + 0.01, 0.078 * s, 0.075), 0.014, 0.004), k=0.003, mat=2)
    return g


def clean_mats(f, fm, iters=4):
    """Kenar komşuluğunda çoğunluk süzgeci: iki komşusu aynı ve kendisinden farklı malzemedeyse yüz o malzemeye geçer
    (voksel sınırında oluşan tek-yüz tırtıkları giderir)."""
    f = np.asarray(f)
    e = np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]])
    fid = np.tile(np.arange(len(f)), 3)
    e.sort(axis=1)
    key = e[:, 0].astype(np.int64) * (int(f.max()) + 1) + e[:, 1]
    o = np.argsort(key, kind="stable")
    k2, f2 = key[o], fid[o]
    same = k2[1:] == k2[:-1]
    a, b = f2[:-1][same], f2[1:][same]
    nb = -np.ones((len(f), 3), dtype=np.int64)
    cnt = np.zeros(len(f), dtype=np.int64)
    for x, y in ((a, b), (b, a)):
        for i, j in zip(x, y):
            if cnt[i] < 3:
                nb[i, cnt[i]] = j
                cnt[i] += 1
    fm = np.asarray(fm).copy()
    ok = (nb >= 0).all(axis=1)
    for _ in range(iters):
        m = fm[np.where(nb >= 0, nb, 0)]
        n0, n1, n2 = m[:, 0], m[:, 1], m[:, 2]
        maj = np.where(n0 == n1, n0, np.where(n1 == n2, n1, np.where(n0 == n2, n0, fm)))
        chg = ok & (maj != fm) & ((n0 == maj).astype(int) + (n1 == maj) + (n2 == maj) >= 2)
        if not chg.any():
            break
        fm[chg] = maj[chg]
    return fm


if __name__ == "__main__":
    import time
    t = time.time()
    g = build()
    v, f, fm = g.mesh()
    print("voxels", g.n, "tris", len(f), "islands", S.islands_count(v, f), "mats", np.bincount(fm), round(time.time() - t, 1), "s",
          getattr(g, "fur_stats", {}))
