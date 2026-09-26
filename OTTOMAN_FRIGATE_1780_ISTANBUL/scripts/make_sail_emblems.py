"""Yelken motifleri (PNG, saydam): lale ve rumi şemse. Kullanıcının verdiği referans görseldeki desen tarzı
(kırmızı dolgu + altın kontur, krem yelken üstünde). Prosedürel çizim; tarihsel desen kopyası değildir.

Çalıştırma: python3 OTTOMAN_FRIGATE_1780_ISTANBUL/scripts/make_sail_emblems.py
Çıktı: OTTOMAN_FRIGATE_1780_ISTANBUL/Textures/emblems/T_SailEmblem_{Lale,Rumi}_A.png (2048², RGBA)
"""

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "Textures" / "emblems"
S = 4096                    # çizim çözünürlüğü (2048'e küçültülür)
CRIMSON = (128, 22, 34, 255)
CRIMSON_D = (92, 14, 24, 255)
GOLD = (196, 150, 64, 255)


def bez(p0, p1, p2, p3, n=40):
    out = []
    for k in range(n + 1):
        t = k / n
        a = (1 - t) ** 3
        b = 3 * (1 - t) ** 2 * t
        c = 3 * (1 - t) * t ** 2
        d = t ** 3
        out.append((a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0], a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1]))
    return out


def mirror(pts, cx):
    return [(2 * cx - x, y) for x, y in pts]


def shape(d, pts, fill, outline=GOLD, w=26):
    d.polygon(pts, fill=fill)
    d.line(pts + [pts[0]], fill=outline, width=w, joint="curve")


def petal(cx, base_y, top_y, half_w, lean=0.0, tip_curl=0.0):
    """Sivri uçlu badem yaprak (sağ yarı bezier, sol yarı ayna)."""
    right = bez((cx, base_y), (cx + half_w * 1.1, base_y - (base_y - top_y) * 0.25),
                (cx + half_w * 0.9 + lean, top_y + (base_y - top_y) * 0.35), (cx + lean + tip_curl, top_y))
    left = bez((cx + lean + tip_curl, top_y), (cx - half_w * 0.9 + lean, top_y + (base_y - top_y) * 0.35),
               (cx - half_w * 1.1, base_y - (base_y - top_y) * 0.25), (cx, base_y))
    return right + left[1:]


def tulip(d, cx, cy, sc):
    """Osmanlı lalesi: orta sivri yaprak, iki yana kıvrılan yan yapraklar, sap ve iki yaprak."""
    s = sc
    # sap
    stem = bez((cx, cy + 0.34 * s), (cx + 0.03 * s, cy + 0.55 * s), (cx - 0.03 * s, cy + 0.75 * s), (cx, cy + 0.95 * s))
    d.line(stem, fill=GOLD, width=int(0.035 * s), joint="curve")
    d.line(stem, fill=CRIMSON_D, width=int(0.018 * s), joint="curve")
    for sg in (1, -1):                                      # sap yaprakları (uzun, kıvrık)
        leaf = bez((cx, cy + 0.80 * s), (cx + sg * 0.20 * s, cy + 0.70 * s), (cx + sg * 0.34 * s, cy + 0.52 * s),
                   (cx + sg * 0.30 * s, cy + 0.36 * s))
        leaf2 = bez((cx + sg * 0.30 * s, cy + 0.36 * s), (cx + sg * 0.26 * s, cy + 0.55 * s), (cx + sg * 0.12 * s, cy + 0.72 * s),
                    (cx, cy + 0.86 * s))
        shape(d, leaf + leaf2[1:], CRIMSON_D, w=int(0.014 * s))
    # yan yapraklar (dışa kıvrılan uçlar)
    for sg in (1, -1):
        p = bez((cx, cy + 0.36 * s), (cx + sg * 0.30 * s, cy + 0.30 * s), (cx + sg * 0.34 * s, cy - 0.05 * s),
                (cx + sg * 0.40 * s, cy - 0.30 * s))
        q = bez((cx + sg * 0.40 * s, cy - 0.30 * s), (cx + sg * 0.22 * s, cy - 0.12 * s), (cx + sg * 0.12 * s, cy + 0.05 * s),
                (cx, cy + 0.10 * s))
        shape(d, p + q[1:], CRIMSON, w=int(0.016 * s))
    # orta yaprak
    shape(d, petal(cx, cy + 0.32 * s, cy - 0.46 * s, 0.17 * s), CRIMSON, w=int(0.018 * s))
    # iç çizgiler (altın)
    for sg in (1, -1):
        d.line(bez((cx, cy + 0.26 * s), (cx + sg * 0.06 * s, cy + 0.05 * s), (cx + sg * 0.05 * s, cy - 0.18 * s),
                   (cx + sg * 0.01 * s, cy - 0.34 * s)), fill=GOLD, width=int(0.010 * s), joint="curve")
    d.line([(cx, cy + 0.28 * s), (cx, cy - 0.30 * s)], fill=GOLD, width=int(0.008 * s))


def rumi_scroll(d, cx, cy, sc, sg, flip=1):
    """Rumi kıvrımı: dışa kıvrılan, ucu çatallı spiral kol."""
    s = sc
    arm = bez((cx, cy), (cx + sg * 0.25 * s, cy - flip * 0.30 * s), (cx + sg * 0.55 * s, cy - flip * 0.10 * s),
              (cx + sg * 0.48 * s, cy + flip * 0.12 * s))
    spiral = []
    c = (cx + sg * 0.40 * s, cy + flip * 0.06 * s)
    for k in range(40):
        a = math.pi * 0.2 + k / 39 * math.pi * 1.6
        r = 0.09 * s * (1 - k / 55)
        spiral.append((c[0] + sg * r * math.cos(a), c[1] + flip * r * math.sin(a)))
    d.line(arm + spiral, fill=GOLD, width=int(0.040 * s), joint="curve")
    d.line(arm + spiral, fill=CRIMSON, width=int(0.020 * s), joint="curve")
    tip = arm[len(arm) // 2]                                  # yan filiz (çatal yaprak)
    leaf = petal(tip[0], tip[1], tip[1] - flip * 0.16 * s, 0.05 * s, lean=sg * 0.06 * s)
    shape(d, leaf, CRIMSON, w=int(0.010 * s))


def medallion(d, cx, cy, sc):
    """Rumi şemse: sivri kemerli madalyon, içinde lale ve simetrik rumi kolları, dışında alem uçları."""
    s = sc
    right = bez((cx, cy - 0.62 * s), (cx + 0.28 * s, cy - 0.46 * s), (cx + 0.46 * s, cy - 0.10 * s), (cx + 0.46 * s, cy + 0.04 * s))
    right += bez((cx + 0.46 * s, cy + 0.04 * s), (cx + 0.46 * s, cy + 0.26 * s), (cx + 0.26 * s, cy + 0.48 * s), (cx, cy + 0.60 * s))[1:]
    outline = right + mirror(list(reversed(right)), cx)[1:]
    shape(d, outline, (240, 226, 196, 0), w=int(0.030 * s))    # yalnız kontur (yelken bezi görünür)
    inner = [(cx + (x - cx) * 0.86, cy + (y - cy) * 0.86) for x, y in outline]
    d.line(inner + [inner[0]], fill=CRIMSON, width=int(0.012 * s), joint="curve")
    for flip in (1, -1):                                       # dört rumi kolu
        for sg in (1, -1):
            rumi_scroll(d, cx, cy + flip * 0.05 * s, 0.62 * s, sg, flip)
    tulip(d, cx, cy - 0.04 * s, 0.42 * s)
    for sg in (1, -1):                                         # üst ve alt alem uçları (şemse sivri uçları)
        tipc = (cx, cy + sg * 0.62 * s)
        shape(d, petal(tipc[0], tipc[1], tipc[1] + sg * 0.20 * s, 0.07 * s), CRIMSON, w=int(0.012 * s))


def render(fn, name):
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    fn(d)
    im = im.filter(ImageFilter.GaussianBlur(1.2)).resize((S // 2, S // 2), Image.LANCZOS)
    OUT.mkdir(parents=True, exist_ok=True)
    p = OUT / f"T_SailEmblem_{name}_A.png"
    im.save(p)
    return p


def main():
    a = render(lambda d: tulip(d, S / 2, S * 0.40, S * 0.62), "Lale")
    b = render(lambda d: medallion(d, S / 2, S / 2, S * 0.62), "Rumi")
    print(a, b)


if __name__ == "__main__":
    main()
