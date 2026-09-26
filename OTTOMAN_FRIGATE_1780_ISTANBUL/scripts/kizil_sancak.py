"""Kızıl Sancak İmparatorluğu görsel kimliği — ortak şekiller ve dokular.

Kaynak: kullanıcının tasarım paketi, Bütün Ciltler s. 17 (sancak dili: kızıl zemin, hilal benzeri ÖZGÜN gök sembolü,
altın işlemeler, sancak kıvrımları) ve s. 44 (kuruluş efsanesi: Alkan Beyran'ın parçalanmış kırmızı yelkeni).
"Yüzde Yetmiş Özgünlük Kuralı": gerçek Osmanlı ay-yıldızı, tuğra vb. birebir kullanılmaz.

YELKEN HİLALİ (özgün gök sembolü): dış kenarı hilal yayı; iç kenarı rüzgârla dolmuş, uçları yırtık bir yelkenin
üç kıvrımı (kuruluş efsanesi); üst boynuzdan yükselen alev/sancak kıvrımı. Yıldız YOK.
Birim: sembolün dış yarıçapı = 1. Hilal sağa açıktır; "yukarı" +y.
"""

import math

import numpy as np

OUTER_END_DEG = 64.0          # dış yay üst ucu (alev tabanı dış köşesi)
LOWER_HORN_DEG = 308.0        # alt boynuz ucu
IC, IR = 0.40, 0.80           # iç yay merkezi (x) ve yarıçapı


def _bez(p0, p1, p2, p3, t):
    u = 1 - t
    return u ** 3 * p0 + 3 * u * u * t * p1 + 3 * u * t * t * p2 + t ** 3 * p3


def _ccw(poly):
    poly = [tuple(map(float, p)) for p in poly]
    a = sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(poly, poly[1:] + poly[:1]))
    return poly if a > 0 else poly[::-1]


def yelken_hilali(n=200):
    """İki kapalı çokgen (CCW), birim yarıçaplı: [hilal, sancak kıvrımı]. Alevin tabanı hilal ucunun içinden başlar
    (birleşim: iki şeklin bileşimi — doku için üst üste çizim, kabartma için üst üste katı)."""
    horn = 50.0
    lo_deg, hi_deg = 360.0 - horn, horn
    lo = np.array([math.cos(math.radians(lo_deg)), math.sin(math.radians(lo_deg))])
    hi = np.array([math.cos(math.radians(hi_deg)), math.sin(math.radians(hi_deg))])
    outer = [np.array([math.cos(math.radians(a)), math.sin(math.radians(a))]) for a in np.linspace(lo_deg, hi_deg, n)]
    b_hi = math.atan2(hi[1], hi[0] - IC)
    b_lo = math.atan2(lo[1], lo[0] - IC) % (2 * math.pi)
    inner = []
    for k, b in enumerate(np.linspace(b_hi, b_lo, n)):
        t = k / (n - 1)
        r_edge = np.hypot(math.cos(b) * IR + IC, math.sin(b) * IR)          # boynuza yakın yumuşak geçiş için
        bil = 0.12 * abs(math.sin(3 * math.pi * t)) * math.sin(math.pi * t) ** 0.3
        notch = 0.0
        for tc, dep in ((0.34, 0.055), (0.69, 0.045)):
            d = abs(t - tc) / 0.026
            if d < 1:
                notch += dep * (1 - d)
        rr = IR - bil + notch
        inner.append(np.array([IC + rr * math.cos(b), rr * math.sin(b)]))
    crescent = _ccw(outer + inner[1:-1])
    # sancak kıvrımı: hilal ucunun içinden (boynuzdan 0,18 geride) başlayan S alev
    tip_in = np.array([math.cos(math.radians(hi_deg + 14)), math.sin(math.radians(hi_deg + 14))]) * 0.92
    s0 = tip_in
    P0, P1, P2, P3 = s0, s0 + np.array([0.02, 0.34]), s0 + np.array([0.42, 0.44]), s0 + np.array([0.26, 0.92])
    ts = np.linspace(0, 1, max(24, n // 3))
    sp = np.array([_bez(P0, P1, P2, P3, t) for t in ts])
    tg = np.gradient(sp, axis=0)
    tg /= np.linalg.norm(tg, axis=1, keepdims=True)
    nr = np.stack([-tg[:, 1], tg[:, 0]], axis=1)
    w = 0.10 * (1 - ts) ** 0.7 * (1 + 0.35 * np.sin(np.pi * ts))
    flame = _ccw(list(sp + nr * w[:, None]) + list((sp - nr * w[:, None])[::-1]))
    return [crescent, flame]


def raster(polys, size, scale, center, rot_deg=0.0, supersample=4):
    """Çokgen(ler)i (birim) size×size maskeye çizer (PIL, bileşim); scale: birim → piksel, center: piksel."""
    from PIL import Image, ImageDraw
    S = size * supersample
    im = Image.new("L", (S, S), 0)
    c, s = math.cos(math.radians(rot_deg)), math.sin(math.radians(rot_deg))
    if polys and isinstance(polys[0][0], (int, float)):
        polys = [polys]
    for poly in polys:
        pts = [((center[0] + (x * c - y * s) * scale) * supersample, (center[1] - (x * s + y * c) * scale) * supersample) for x, y in poly]
        ImageDraw.Draw(im).polygon(pts, fill=255)
    return np.asarray(im.resize((size, size), Image.LANCZOS)).astype(np.float32) / 255.0


# ------------------------------------------------------------------ KIZIL SANCAK ARMASI (kullanıcı konsepti, 2026-09-26)
# Kullanıcının tasarım paketinden ürettiği konsept görsel: yukarı açık hilal + içinden geçen dikey mızrak + üstte
# gök yıldızı (pusula biçimli, uzun dikey ışınlı — birebir Osmanlı 8 köşeli yıldızı DEĞİL) + altta üç dalga
# ("Dalgalarda Daima"). Birim: hilal dış yarıçapı = 1; "yukarı" +y.

def _circle_arc(cx, cy, r, a0, a1, n):
    return [(cx + r * math.cos(a), cy + r * math.sin(a)) for a in np.linspace(a0, a1, n)]


def _hilal_up(n):
    """Yukarı açık hilal: dış çember (0,0) R=1, iç çember (0, 0.34) r=0.80; boynuzlar yukarıda."""
    R, cy, r = 1.0, 0.34, 0.80
    y = (R * R - r * r + cy * cy) / (2 * cy)
    x = math.sqrt(max(R * R - y * y, 1e-9))
    th_r = math.atan2(y, x)
    outer = _circle_arc(0, 0, R, th_r, (math.pi - th_r) - 2 * math.pi, n)        # sağ boynuz → alt → sol boynuz
    ph_l, ph_r = math.atan2(y - cy, -x), math.atan2(y - cy, x)
    inner = _circle_arc(0, cy, r, ph_l, ph_r + 2 * math.pi, n)                    # sol boynuz → alt → sağ boynuz
    return _ccw(outer + inner[1:-1])


def _mizrak(n):
    """Dikey mızrak: lale biçimli uç, sap, kısa balçak, alt topuz."""
    pts = []
    tip_y, blade0, shaft_w = 1.28, 0.62, 0.055
    # sağ kenar alttan üste
    pts += [(0.10, -1.30), (0.12, -1.22), (shaft_w, -1.14)]                 # topuz
    pts += [(shaft_w, 0.30), (0.22, 0.34), (0.26, 0.42), (0.20, 0.44), (shaft_w, 0.42)]   # balçak (kıvrık uçlu)
    for t in np.linspace(0, 1, n):                                          # lale uç (sağ)
        y = blade0 + (tip_y - blade0) * t
        w = 0.16 * math.sin(math.pi * min(t / 0.62, 1.0) * 0.5 + (0 if t < 0.62 else 0)) if t < 0.62 else 0.16 * (1 - (t - 0.62) / 0.38) ** 1.3
        pts.append((max(w, shaft_w * (1 - t)), y))
    left = [(-x, y) for x, y in reversed(pts)]
    return _ccw(pts + left[1:-1])


def _gok_yildizi(cx, cy, r_long, r_short, r_in):
    """Pusula biçimli gök yıldızı: 4 uzun (dikey uzun) + 4 kısa ışın."""
    out = []
    for k in range(16):
        a = math.pi / 2 + k * math.pi / 8
        if k % 2:
            rr = r_in
        elif k % 4 == 0:
            rr = r_long * (1.45 if k in (0, 8) else 1.0)
        else:
            rr = r_short
        out.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    return _ccw(out)


def _dalga(y0, amp, width, length, n):
    top = [(x, y0 + amp * math.sin(2 * math.pi * (x / length) * 2.0) + width / 2) for x in np.linspace(-length / 2, length / 2, n)]
    bot = [(x, y0 + amp * math.sin(2 * math.pi * (x / length) * 2.0) - width / 2) for x in np.linspace(length / 2, -length / 2, n)]
    # uçları sivrilt
    top[0] = (top[0][0], (top[0][1] + bot[-1][1]) / 2)
    top[-1] = (top[-1][0], (top[-1][1] + bot[0][1]) / 2)
    return _ccw(top + bot[1:-1])


def sancak_armasi(n=160, waves=True):
    """Kızıl Sancak arması: [hilal, mızrak, gök yıldızı, dalga×3]."""
    polys = [_hilal_up(n), _mizrak(max(12, n // 8)), _gok_yildizi(0.0, 1.62, 0.34, 0.20, 0.07)]
    if waves:
        for k, y0 in enumerate((-1.48, -1.78, -2.08)):
            polys.append(_dalga(y0, 0.07, 0.11, 2.3 - 0.35 * k, max(40, n // 3)))
    return polys
