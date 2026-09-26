"""Yelken kanvası dokusu (döşenebilir): T_Sail_Canvas_B_{BC,N,ORM}.png → Textures/Sails/.

    python3.11 OTTOMAN_FRIGATE_1780_ISTANBUL/scripts/make_sail_canvas.py

Karo 2,44 m × 2,44 m = 4 bez eni. Bez eni 24 inç ≈ 0,61 m [İKİNCİL: 18. yy yelken bezi topları için yaygın
ölçü; Steel, "Elements and Practice of Rigging and Seamanship" (1794) yelken bezini 24 inç verir]. Dikiş bindirmesi
≈ 1,5 inç (3,8 cm) [TAHMİN, aynı kaynaktaki dikiş payı aralığı]; her bindirmenin iki kenarında sık dikiş sırası.
Doku prosedürel (numpy); fotoğraf/lisanslı kaynak kullanılmaz.
"""

from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "Textures" / "Sails"
N = 2048
TILE_M = 2.44
PX_M = N / TILE_M
rng = np.random.default_rng(1780)


def fbm(n, octaves, base, seed):
    r = np.random.default_rng(seed)
    out = np.zeros((n, n))
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        k = base * 2 ** o
        g = r.standard_normal((k, k))
        # döşenebilir: periyodik yukarı örnekleme (FFT)
        F = np.fft.fft2(g)
        big = np.zeros((n, n), complex)
        h = k // 2
        big[:h, :h], big[:h, -h:], big[-h:, :h], big[-h:, -h:] = F[:h, :h], F[:h, -h:], F[-h:, :h], F[-h:, -h:]
        layer = np.real(np.fft.ifft2(big))
        layer /= np.abs(layer).max() + 1e-9
        out += amp * layer
        tot += amp
        amp *= 0.5
    return out / tot


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    y, x = np.mgrid[0:N, 0:N].astype(float)
    # dokuma: atkı/çözgü (≈ 2,4 px periyot), iplik kalınlık düzensizliği
    weave = 0.5 * np.sin(2 * np.pi * x / 2.4) * np.sin(2 * np.pi * y / 2.4)
    slub_x = fbm(N, 3, 64, 1)[:, :1] * np.ones((1, N))
    slub_y = fbm(N, 3, 64, 2)[:1, :] * np.ones((N, 1))
    fibre = fbm(N, 4, 128, 3)
    mott = fbm(N, 4, 4, 4)
    # dikiş bindirmeleri: her 0,61 m'de (512 px) 3,8 cm şerit, kenarlarında dikiş sırası
    cloth_px = N / 4
    seam_w = 0.038 * PX_M
    xm = np.mod(x, cloth_px)
    dist = np.minimum(xm, cloth_px - xm)
    band = np.clip(1.0 - dist / (seam_w / 2), 0, 1)
    band = (band > 0).astype(float) * (0.6 + 0.4 * np.cos(np.clip(dist / (seam_w / 2), 0, 1) * np.pi / 2))
    stitch_line = np.exp(-((dist - seam_w / 2 + 3) ** 2) / 2.0)
    stitch = stitch_line * (np.mod(y, 9) < 5)                        # ≈ 1 cm'de 1 dikiş
    # yükseklik
    hgt = 0.35 * weave + 0.25 * slub_x + 0.2 * slub_y + 0.15 * fibre + 1.2 * band - 0.6 * stitch
    # renk (sRGB): ağartılmamış keten/kenevir kanvas
    base = np.array([0.80, 0.77, 0.70])
    tone = 1.0 + 0.045 * mott + 0.02 * fibre + 0.015 * weave - 0.05 * band - 0.18 * stitch
    warm = 0.012 * fbm(N, 3, 8, 5)
    bc = np.stack([base[0] * tone + warm, base[1] * tone, base[2] * tone - warm], axis=-1)
    Image.fromarray((np.clip(bc, 0, 1) * 255).astype(np.uint8)).save(OUT / "T_Sail_Canvas_B_BC.png")
    # normal (OpenGL, +Y yukarı), döşenebilir türev
    s = 2.2
    dx = (np.roll(hgt, -1, 1) - np.roll(hgt, 1, 1)) * s
    dy = (np.roll(hgt, -1, 0) - np.roll(hgt, 1, 0)) * s
    nrm = np.stack([-dx, dy, np.ones_like(hgt)], axis=-1)
    nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True)
    Image.fromarray(((nrm * 0.5 + 0.5) * 255).astype(np.uint8)).save(OUT / "T_Sail_Canvas_B_N.png")
    # ORM: AO (dikiş dibi), pürüzlülük, metal 0
    ao = np.clip(1.0 - 0.25 * stitch - 0.08 * np.clip(-weave, 0, 1), 0, 1)
    rough = np.clip(0.86 + 0.05 * fibre - 0.04 * band, 0, 1)
    orm = np.stack([ao, rough, np.zeros_like(ao)], axis=-1)
    Image.fromarray((orm * 255).astype(np.uint8)).save(OUT / "T_Sail_Canvas_B_ORM.png")
    print("yazıldı:", [p.name for p in sorted(OUT.glob("T_Sail_Canvas_B_*"))], "karo", TILE_M, "m")


if __name__ == "__main__":
    main()
