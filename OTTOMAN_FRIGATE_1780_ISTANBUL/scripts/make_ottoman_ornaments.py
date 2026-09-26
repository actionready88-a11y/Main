"""Osmanlı süsleme dokuları (prosedürel çizim; tarihsel desen kopyası değildir, üslup esinlidir).

Çalıştırma: python3.11 OTTOMAN_FRIGATE_1780_ISTANBUL/scripts/make_ottoman_ornaments.py
Çıktı: OTTOMAN_FRIGATE_1780_ISTANBUL/Textures/ornaments/
    T_Orn_Frieze_Rumi_A_{BC,H}.png     2048×256, X'te döşenir — dış friz (altın rumi sarmaşık, kırmızı zemin)
    T_Orn_Frieze_Lale_A_{BC,H}.png     2048×256, X'te döşenir — iç/kasara frizi (lale + karanfil, yeşil zemin)
    T_Orn_Panel_Rumi_A_{BC,H}.png      1024×1024 — kıç aynası / baş tahtası paneli (şemse + köşebent)
    T_Orn_Kalemisi_A_{BC,H}.png        1024², döşenir — kamara duvar/tavan kalemişi (ogee kafes, lale)
    T_Orn_Iznik_Tile_A_{BC,H}.png      1024², döşenir (2×2 çini) — kamara duvar kuşağı
    T_Orn_Carpet_Usak_A_BC.png         2048×1024 — kamara halısı (Uşak madalyonlu üslup)
_H: yükseklik (beyaz = kabartma) → Blender'da Bump, UE için normal'e bake edilir.
"""

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "Textures" / "ornaments"

GOLD = (201, 156, 68)
GOLD_D = (150, 108, 40)
CRIMSON = (122, 20, 30)
CRIMSON_D = (84, 12, 20)
GREEN = (22, 70, 52)
GREEN_D = (14, 46, 34)
NAVY = (24, 36, 78)
CREAM = (236, 222, 190)
COBALT = (28, 58, 150)
TURQ = (38, 150, 150)
CORAL = (190, 46, 40)
WHITE = (244, 242, 234)


def bez(p0, p1, p2, p3, n=40):
    out = []
    for k in range(n + 1):
        t = k / n
        a, b, c, d = (1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t ** 2, t ** 3
        out.append((a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0], a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1]))
    return out


def petal(cx, base_y, top_y, half_w, lean=0.0):
    h = base_y - top_y
    r = bez((cx, base_y), (cx + half_w * 1.1, base_y - h * 0.25), (cx + half_w * 0.9 + lean, top_y + h * 0.35), (cx + lean, top_y))
    l = bez((cx + lean, top_y), (cx - half_w * 0.9 + lean, top_y + h * 0.35), (cx - half_w * 1.1, base_y - h * 0.25), (cx, base_y))
    return r + l[1:]


def rot(pts, c, a):
    ca, sa = math.cos(a), math.sin(a)
    return [(c[0] + (x - c[0]) * ca - (y - c[1]) * sa, c[1] + (x - c[0]) * sa + (y - c[1]) * ca) for x, y in pts]


class Canvas:
    """Renk (RGB) + yükseklik (L) birlikte çizilir. wrap_x/wrap_y: döşenebilir kenar için ±boyut kopyası."""

    def __init__(self, w, h, bg, wrap_x=False, wrap_y=False, ss=2):
        self.ss, self.w, self.h = ss, w * ss, h * ss
        self.im = Image.new("RGB", (self.w, self.h), bg)
        self.hm = Image.new("L", (self.w, self.h), 40)
        self.d, self.dh = ImageDraw.Draw(self.im), ImageDraw.Draw(self.hm)
        self.offs = [(dx, dy) for dx in ((-self.w, 0, self.w) if wrap_x else (0,)) for dy in ((-self.h, 0, self.h) if wrap_y else (0,))]

    def _sh(self, pts, dx, dy):
        return [(x * self.ss + dx, y * self.ss + dy) for x, y in pts]

    def poly(self, pts, fill, height=200, outline=None, ow=0, oh=None):
        for dx, dy in self.offs:
            p = self._sh(pts, dx, dy)
            self.d.polygon(p, fill=fill)
            self.dh.polygon(p, fill=height)
            if outline:
                self.d.line(p + [p[0]], fill=outline, width=int(ow * self.ss), joint="curve")
                self.dh.line(p + [p[0]], fill=oh if oh is not None else min(255, height + 30), width=int(ow * self.ss), joint="curve")

    def line(self, pts, fill, w, height=220):
        for dx, dy in self.offs:
            p = self._sh(pts, dx, dy)
            self.d.line(p, fill=fill, width=max(1, int(w * self.ss)), joint="curve")
            self.dh.line(p, fill=height, width=max(1, int(w * self.ss)), joint="curve")

    def ellipse(self, c, r, fill, height=220, outline=None, ow=0):
        for dx, dy in self.offs:
            x, y = c[0] * self.ss + dx, c[1] * self.ss + dy
            rr = r * self.ss
            self.d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=fill, outline=outline, width=int(ow * self.ss))
            self.dh.ellipse([x - rr, y - rr, x + rr, y + rr], fill=height)

    def rect(self, x0, y0, x1, y1, fill, height=200):
        for dx, dy in self.offs:
            b = [x0 * self.ss + dx, y0 * self.ss + dy, x1 * self.ss + dx, y1 * self.ss + dy]
            self.d.rectangle(b, fill=fill)
            self.dh.rectangle(b, fill=height)

    def save(self, name, height=True):
        OUT.mkdir(parents=True, exist_ok=True)
        size = (self.w // self.ss, self.h // self.ss)
        self.im.filter(ImageFilter.GaussianBlur(0.8)).resize(size, Image.LANCZOS).save(OUT / f"{name}_BC.png")
        if height:
            self.hm.filter(ImageFilter.GaussianBlur(2.2 * self.ss)).resize(size, Image.LANCZOS).save(OUT / f"{name}_H.png")
        return name


# ---------------------------------------------------------------- motif parçaları
def rumi_leaf(c, cx, cy, s, ang, fill, edge):
    """Rumi (çatal uçlu, kıvrık) yaprak: iki sivri lob + iç damar."""
    lob1 = bez((0, 0), (0.35 * s, -0.30 * s), (0.85 * s, -0.25 * s), (1.0 * s, -0.02 * s))
    lob1 += bez((1.0 * s, -0.02 * s), (0.70 * s, -0.08 * s), (0.55 * s, 0.02 * s), (0.62 * s, 0.10 * s))[1:]
    lob1 += bez((0.62 * s, 0.10 * s), (0.80 * s, 0.14 * s), (0.95 * s, 0.26 * s), (0.98 * s, 0.34 * s))[1:]
    lob1 += bez((0.98 * s, 0.34 * s), (0.60 * s, 0.34 * s), (0.25 * s, 0.22 * s), (0, 0))[1:]
    pts = rot([(cx + x, cy + y) for x, y in lob1], (cx, cy), ang)
    c.poly(pts, fill, 210, edge, 0.018 * s + 1, 235)
    vein = rot([(cx + x, cy + y) for x, y in bez((0.05 * s, 0.02 * s), (0.35 * s, -0.06 * s), (0.55 * s, 0.0), (0.70 * s, 0.08 * s), 12)],
               (cx, cy), ang)
    c.line(vein, edge, 0.02 * s + 1, 240)


def tulip(c, cx, cy, s, body, edge, stem=True):
    if stem:
        c.line(bez((cx, cy + 0.30 * s), (cx + 0.04 * s, cy + 0.5 * s), (cx - 0.04 * s, cy + 0.7 * s), (cx, cy + 0.9 * s)), edge, 0.04 * s, 215)
    for sg in (1, -1):
        p = bez((cx, cy + 0.34 * s), (cx + sg * 0.30 * s, cy + 0.28 * s), (cx + sg * 0.34 * s, cy - 0.05 * s), (cx + sg * 0.40 * s, cy - 0.30 * s))
        q = bez((cx + sg * 0.40 * s, cy - 0.30 * s), (cx + sg * 0.22 * s, cy - 0.12 * s), (cx + sg * 0.12 * s, cy + 0.05 * s), (cx, cy + 0.10 * s))
        c.poly(p + q[1:], body, 215, edge, 0.03 * s, 240)
    c.poly(petal(cx, cy + 0.30 * s, cy - 0.46 * s, 0.17 * s), body, 225, edge, 0.03 * s, 245)
    c.line([(cx, cy + 0.26 * s), (cx, cy - 0.30 * s)], edge, 0.018 * s, 245)


def carnation(c, cx, cy, s, body, edge):
    """Karanfil: yelpaze taç (5 dişli), çanak."""
    for k in range(5):
        a = math.radians(-150 + k * 30)
        tip = (cx + math.cos(a) * 0.45 * s, cy + math.sin(a) * 0.45 * s)
        c.poly(petal(cx, cy, cy - 0.45 * s, 0.10 * s), body, 215, edge, 0.025 * s, 240) if k == 2 else \
            c.poly(rot(petal(cx, cy, cy - 0.42 * s, 0.09 * s), (cx, cy), a + math.pi / 2), body, 210, edge, 0.025 * s, 238)
        c.ellipse(tip, 0.035 * s, edge, 245)
    c.poly([(cx - 0.12 * s, cy), (cx + 0.12 * s, cy), (cx + 0.06 * s, cy + 0.28 * s), (cx - 0.06 * s, cy + 0.28 * s)], GREEN, 210, edge, 0.02 * s)


def rosette(c, cx, cy, r, body, edge, n=8):
    for k in range(n):
        a = 2 * math.pi * k / n
        c.poly(rot(petal(cx, cy, cy - r, r * 0.28), (cx, cy), a), body, 215, edge, r * 0.06, 240)
    c.ellipse((cx, cy), r * 0.26, edge, 250)
    c.ellipse((cx, cy), r * 0.14, body, 235)


def bead_border(c, y, w, r, fill, step):
    x = step / 2
    while x < w + step:
        c.ellipse((x, y), r, fill, 235)
        x += step


# ---------------------------------------------------------------- dokular
def frieze(name, ground, ground_d, body, flower):
    W, H = 2048, 256
    c = Canvas(W, H, ground, wrap_x=True)
    c.rect(0, 0, W, 22, GOLD, 200)                      # üst/alt altın silme + inci dizisi
    c.rect(0, H - 22, W, H, GOLD, 200)
    c.rect(0, 22, W, 30, ground_d, 60)
    c.rect(0, H - 30, W, H - 22, ground_d, 60)
    bead_border(c, 11, W, 6, GOLD_D, 32)
    bead_border(c, H - 11, W, 6, GOLD_D, 32)
    n = 4                                              # 4 dalga / doku → her 512 px bir motif çifti
    mid = H / 2
    vine = [(x, mid + 52 * math.sin(2 * math.pi * n * x / W)) for x in range(-8, W + 9, 4)]
    c.line(vine, GOLD_D, 16, 225)
    c.line(vine, GOLD, 10, 235)
    A = 52
    for k in range(2 * n):                             # dalga kemerlerinin içine çiçek, kollara rumi yaprak + filiz
        xp = (k + 0.5) * W / (2 * n)                    # k çift: dalga altta (görüntü y aşağı) → çiçek kemerin içinde, üstte
        up = k % 2 == 0
        if up:
            tulip(c, xp, mid - 30, 100, flower, GOLD, stem=False) if k % 4 == 0 else carnation(c, xp, mid - 20, 90, flower, GOLD)
        else:
            tulip(c, xp, mid + 20, 100, flower, GOLD, stem=False) if k % 4 == 1 else carnation(c, xp, mid + 28, 90, flower, GOLD)
        for sg in (1, -1):
            for f, sz in ((0.5, 66), (0.78, 46)):
                xl = xp + sg * f * W / (4 * n)
                yl = mid + A * math.sin(2 * math.pi * n * xl / W)
                ang = math.atan(A * 2 * math.pi * n / W * math.cos(2 * math.pi * n * xl / W))
                side = 1 if up else -1
                rumi_leaf(c, xl, yl, sz, ang + (math.pi if sg < 0 else 0) + side * 0.75 * (1 if sg > 0 else -1), body, GOLD)
    return c.save(name)


def panel_rumi(name):
    W = 1024
    c = Canvas(W, W, CRIMSON)
    m = 26
    c.rect(0, 0, W, W, GOLD, 200)
    c.rect(m, m, W - m, W - m, CRIMSON_D, 60)
    c.rect(m + 14, m + 14, W - m - 14, W - m - 14, CRIMSON, 90)
    bead_border(c, m / 2, W, 7, GOLD_D, 34)
    bead_border(c, W - m / 2, W, 7, GOLD_D, 34)
    cx = cy = W / 2
    # şemse (sivri madalyon)
    r = bez((cx, cy - 330), (cx + 150, cy - 250), (cx + 250, cy - 60), (cx + 250, cy))
    r += bez((cx + 250, cy), (cx + 250, cy + 60), (cx + 150, cy + 250), (cx, cy + 330))[1:]
    out = r + [(2 * cx - x, y) for x, y in reversed(r)][1:]
    c.poly(out, GREEN, 150, GOLD, 16, 240)
    inner = [(cx + (x - cx) * 0.88, cy + (y - cy) * 0.88) for x, y in out]
    c.line(inner + [inner[0]], GOLD_D, 6, 200)
    for fy in (1, -1):
        for sg in (1, -1):
            rumi_leaf(c, cx + sg * 20, cy + fy * 40, 170, (0 if sg > 0 else math.pi) + fy * (-0.9 if sg > 0 else 0.9), GOLD, GOLD_D)
    tulip(c, cx, cy - 20, 170, CRIMSON, GOLD)
    for sg in (1, -1):                                  # alemler
        c.poly(petal(cx, cy + sg * 330, cy + sg * 420, 26), GOLD, 240, GOLD_D, 4)
    for qx in (m + 14, W - m - 14):                     # köşebentler (çeyrek şemse)
        for qy in (m + 14, W - m - 14):
            sx, sy = (1 if qx < cx else -1), (1 if qy < cy else -1)
            q = [(qx, qy)] + [(qx + sx * 190 * math.cos(t * math.pi / 2 / 20), qy + sy * 190 * math.sin(t * math.pi / 2 / 20)) for t in range(21)]
            c.poly(q, GREEN, 150, GOLD, 10, 235)
            rumi_leaf(c, qx + sx * 30, qy + sy * 30, 110, math.atan2(sy, sx), GOLD, GOLD_D)
    return c.save(name)


def kalemisi(name):
    W = 1024
    c = Canvas(W, W, CREAM, wrap_x=True, wrap_y=True)
    s = W / 2                                           # 2×2 ogee hücre
    for i in range(3):
        for j in range(3):
            cx, cy = i * s, j * s
            for ox, oy in ((0, 0), (s / 2, s / 2)):
                x, y = cx + ox, cy + oy
                # ogee (soğan kemer) hücre konturu
                r = bez((x, y - s / 2), (x + s * 0.10, y - s * 0.30), (x + s * 0.42, y - s * 0.18), (x + s / 2, y))
                r += bez((x + s / 2, y), (x + s * 0.42, y + s * 0.18), (x + s * 0.10, y + s * 0.30), (x, y + s / 2))[1:]
                ogee = r + [(2 * x - px, py) for px, py in reversed(r)][1:]
                c.line(ogee + [ogee[0]], CRIMSON, 12, 150)
                c.line(ogee + [ogee[0]], GOLD, 4, 170)
                if (ox, oy) == (0, 0):
                    tulip(c, x, y - 24, 190, CRIMSON, NAVY)
                else:
                    carnation(c, x, y + 14, 150, NAVY, CRIMSON)
            rosette(c, cx + s / 2, cy, 34, GOLD, CRIMSON, 8)
    return c.save(name)


def iznik(name):
    W = 1024
    c = Canvas(W, W, WHITE, wrap_x=True, wrap_y=True)
    t = W / 2
    for i in range(2):
        for j in range(2):
            x0, y0 = i * t, j * t
            cx, cy = x0 + t / 2, y0 + t / 2
            for k in range(4):                          # saz yaprakları çarkı
                a = k * math.pi / 2 + math.pi / 4
                leaf = rot(petal(cx, cy - 40, cy - 230, 46, lean=30), (cx, cy), a)
                c.poly(leaf, COBALT, 150, NAVY, 5)
                c.line(rot([(cx, cy - 50), (cx + 12, cy - 210)], (cx, cy), a), TURQ, 5, 150)
            for k in range(4):
                a = k * math.pi / 2
                px, py = cx + math.cos(a) * 170, cy + math.sin(a) * 170
                carnation(c, px, py, 70, CORAL, NAVY)
            rosette(c, cx, cy, 60, TURQ, COBALT, 8)
            for qx in (x0, x0 + t):                    # köşe çeyrek lale (komşu çiniyle birleşir)
                for qy in (y0, y0 + t):
                    rosette(c, qx, qy, 44, CORAL, COBALT, 6)
            c.rect(x0, y0, x0 + t, y0 + 3, (188, 182, 170), 10)      # derz
            c.rect(x0, y0, x0 + 3, y0 + t, (188, 182, 170), 10)
    return c.save(name)


def carpet(name):
    W, H = 2048, 1024
    c = Canvas(W, H, (132, 26, 30), ss=1)
    RED, NV, IV, YE = (132, 26, 30), (26, 34, 70), (226, 212, 176), (198, 150, 62)
    c.rect(0, 0, W, H, NV, 0)
    c.rect(40, 40, W - 40, H - 40, IV, 0)
    c.rect(56, 56, W - 56, H - 56, NV, 0)
    for x in range(80, W - 80, 64):                     # bordür motifleri
        for y in (78, H - 78):
            rosette(c, x + 32, y, 18, YE, RED, 6)
    for y in range(140, H - 140, 64):
        for x in (78, W - 78):
            rosette(c, x, y + 32, 18, YE, RED, 6)
    c.rect(110, 110, W - 110, H - 110, RED, 0)
    for x in range(180, W - 150, 110):                  # zemin serpme çiçekleri
        for y in range(170, H - 150, 110):
            c.ellipse((x, y), 7, YE, 0)
    cx, cy = W / 2, H / 2                               # merkez yıldız madalyon
    pts = []
    for k in range(32):
        a = 2 * math.pi * k / 32
        rr = 330 if k % 2 == 0 else 250
        pts.append((cx + math.cos(a) * rr * 1.25, cy + math.sin(a) * rr * 0.95))
    c.poly(pts, NV, 0, YE, 8)
    c.poly([(cx + (x - cx) * 0.7, cy + (y - cy) * 0.7) for x, y in pts], RED, 0, YE, 5)
    rosette(c, cx, cy, 90, YE, NV, 8)
    for sx in (-1, 1):                                  # köşe çeyrek madalyonlar
        for sy in (-1, 1):
            qx, qy = cx + sx * (W / 2 - 110), cy + sy * (H / 2 - 110)
            q = [(qx, qy)] + [(qx - sx * 260 * math.cos(t * math.pi / 40), qy - sy * 200 * math.sin(t * math.pi / 40)) for t in range(21)]
            c.poly(q, NV, 0, YE, 6)
    return c.save(name, height=False)


def main():
    out = [frieze("T_Orn_Frieze_Rumi_A", CRIMSON, CRIMSON_D, GOLD, GREEN),
           frieze("T_Orn_Frieze_Lale_A", GREEN, GREEN_D, GOLD, CRIMSON),
           panel_rumi("T_Orn_Panel_Rumi_A"), kalemisi("T_Orn_Kalemisi_A"), iznik("T_Orn_Iznik_Tile_A"),
           carpet("T_Orn_Carpet_Usak_A")]
    print("ORN", out)


if __name__ == "__main__":
    main()
