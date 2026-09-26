"""Bayrak dokuları: Osmanlı donanma sancağı (kırmızı zemin, beyaz hilal ve sekiz köşeli yıldız) ve flama.

Kaynak: 1793'te donanma gemilerine çekilecek sancakların kırmızı zeminli, beyaz ay-yıldızlı olması emredildi;
1793–1826 arasında yıldız sekiz köşeli; ay-yıldızın devlet simgesi olarak kullanımı III. Mustafa (1757–1774)
döneminde başlar [İKİNCİL: tr.wikipedia "Osmanlı bayrakları", dergipark "Tarihsel süreçte bayrak ve sancaklarımız";
arama özeti]. Gemi 1780 tarihli: resmî biçim 1793 — oyun için kabul edilen küçük tarih farkı raporda not edildi.
Oranlar (hilal/yıldız konumu) TAHMİN.

Çalıştırma: python3 OTTOMAN_FRIGATE_1780_ISTANBUL/scripts/make_flags.py
"""

import math
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "Textures" / "flags"
RED = (170, 18, 32, 255)
WHITE = (242, 238, 228, 255)


def crescent(d, cx, cy, r, off, r2):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=WHITE)
    d.ellipse([cx - r2 + off, cy - r2, cx + r2 + off, cy + r2], fill=RED)


def star8(d, cx, cy, ro, ri):
    pts = []
    for k in range(16):
        a = -math.pi / 2 + k * math.pi / 8
        r = ro if k % 2 == 0 else ri
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    d.polygon(pts, fill=WHITE)


def ensign(w=3072, h=2048):
    im = Image.new("RGBA", (w, h), RED)
    d = ImageDraw.Draw(im)
    cx, cy = w * 0.42, h * 0.5
    r = h * 0.25
    crescent(d, cx, cy, r, r * 0.33, r * 0.80)
    star8(d, cx + r * 0.88, cy, h * 0.10, h * 0.045)
    return im.resize((w // 2, h // 2), Image.LANCZOS)


def pennant(w=4096, h=512):
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.polygon([(0, 0), (w, h * 0.42), (w * 0.93, h * 0.5), (w, h * 0.58), (0, h)], fill=RED)   # kırlangıç kuyruklu
    r = h * 0.30
    crescent(d, h * 0.62, h * 0.5, r, r * 0.33, r * 0.80)
    star8(d, h * 0.62 + r * 0.88, h * 0.5, h * 0.12, h * 0.055)
    return im.resize((w // 2, h // 2), Image.LANCZOS)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    a = OUT / "T_Flag_OttomanNavy1793_A.png"
    b = OUT / "T_Pennant_OttomanNavy_A.png"
    ensign().save(a)
    pennant().save(b)
    print(a, b)


if __name__ == "__main__":
    main()
