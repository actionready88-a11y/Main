"""Kızıl Sancak dokuları (v040): sancak, flandra, yelken amblemi — Kızıl Sancak arması (kullanıcı konsepti;
scripts/kizil_sancak.py: hilal + mızrak + gök yıldızı + dalgalar).

    python3.11 OTTOMAN_FRIGATE_1780_ISTANBUL/scripts/make_kizil_sancak_textures.py

Kaynak: kullanıcı tasarım paketi, Bütün Ciltler s. 17 — "kızıl zemin, hilal benzeri özgün gök sembolü, altın
işlemeler, sancak kıvrımları". Gerçek Osmanlı ay-yıldızı KULLANILMAZ (Yüzde Yetmiş Özgünlük Kuralı).
Renkler ve oranlar TAHMİN (görsel karar). Eski T_Flag_OttomanNavy1793_A / T_Pennant_OttomanNavy_A dosyaları
geçmiş sürümler (v039 ve önce) için yerinde bırakılır.
"""

import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kizil_sancak as K  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
CRIMSON = np.array([0.55, 0.045, 0.055])
GOLD = np.array([0.86, 0.66, 0.26])
GOLD_DK = np.array([0.52, 0.34, 0.10])
rng = np.random.default_rng(40)


def noise(h, w, cell, seed):
    r = np.random.default_rng(seed)
    g = r.standard_normal((h // cell + 2, w // cell + 2))
    im = Image.fromarray(((g - g.min()) / (np.ptp(g) + 1e-9) * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
    return np.asarray(im).astype(np.float32) / 255.0 - 0.5


def fabric(h, w, base, seed):
    weave = 0.5 * np.sin(np.arange(w)[None, :] * 2.1) * np.sin(np.arange(h)[:, None] * 2.1)
    tone = 1 + 0.06 * noise(h, w, 96, seed) + 0.02 * noise(h, w, 8, seed + 1) + 0.015 * weave
    return base[None, None] * tone[..., None]


def embroider(img, mask, hatch_px, seed, outline_px=6):
    """Altın işleme: satin dikiş (çapraz tarama) + koyu altın kontur."""
    h, w = mask.shape
    y, x = np.mgrid[0:h, 0:w]
    sat = 0.82 + 0.18 * (0.5 + 0.5 * np.sin((x + y) * 2 * math.pi / hatch_px))
    gold = GOLD[None, None] * (sat[..., None] + 0.05 * noise(h, w, 32, seed)[..., None])
    m = Image.fromarray((mask * 255).astype(np.uint8))
    grown = np.asarray(m.filter(ImageFilter.MaxFilter(2 * outline_px + 1))).astype(np.float32) / 255.0
    ring = np.clip(grown - mask, 0, 1)
    img = img * (1 - ring[..., None]) + GOLD_DK[None, None] * ring[..., None]
    img = img * (1 - mask[..., None]) + gold * mask[..., None]
    return img


def border_band(h, w, band, hoist=True):
    m = np.zeros((h, w), np.float32)
    m[:band, :] = 1
    m[-band:, :] = 1
    if hoist:
        m[:, :band] = 1
    # bant içi motif: sık aralıklı küçük baklava (kırmızı) — işleme görünümü
    y, x = np.mgrid[0:h, 0:w]
    period = band * 1.6
    lz = (np.abs(((x + period / 2) % period) - period / 2) + np.abs(((y % band) - band / 2))) < band * 0.28
    return m, lz


def ensign(W=3072, H=2048):
    img = fabric(H, W, CRIMSON, 1)
    band = int(H * 0.055)
    bm, lz = border_band(H, W, band)
    img = embroider(img, bm, 9, 2, outline_px=3)
    inner = (bm > 0) & lz
    img[inner] = CRIMSON * 0.9
    sym = K.raster(K.sancak_armasi(), max(W, H), H * 0.155, (W * 0.36, H * 0.50))[:H, :W]
    img = embroider(img, sym, 11, 3, outline_px=7)
    # sancak kıvrımı: çatal uç (kırlangıç kuyruğu), kenarları hafif kavisli
    alpha = Image.new("L", (W, H), 255)
    d = ImageDraw.Draw(alpha)
    notch = [(W * 0.80, H * 0.5)]
    for t in np.linspace(0, 1, 40):
        notch.append((W * (0.80 + 0.20 * t), H * (0.5 - 0.30 * t - 0.03 * math.sin(math.pi * t))))
    for t in np.linspace(1, 0, 40):
        notch.append((W * (0.80 + 0.20 * t), H * (0.5 + 0.30 * t + 0.03 * math.sin(math.pi * t))))
    d.polygon(notch, fill=0)
    a = np.asarray(alpha).astype(np.float32) / 255.0
    rgba = np.dstack([np.clip(img, 0, 1), a])
    return Image.fromarray((rgba * 255).astype(np.uint8)).resize((W // 2, H // 2), Image.LANCZOS)


def pennant(W=4096, H=512):
    img = fabric(H, W, CRIMSON, 5)
    alpha = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(alpha)
    d.polygon([(0, 0), (W, H * 0.40), (W * 0.90, H * 0.5), (W, H * 0.60), (0, H)], fill=255)
    a = np.asarray(alpha).astype(np.float32) / 255.0
    # altın kenar çizgileri (üst ve alt kenara paralel)
    y, x = np.mgrid[0:H, 0:W]
    top = H * 0.40 * x / W
    bot = H - H * 0.40 * x / W
    edge = ((np.abs(y - (top + H * 0.06 * (1 - x / W))) < H * 0.018) | (np.abs(y - (bot - H * 0.06 * (1 - x / W))) < H * 0.018)) & (x < W * 0.9)
    img[edge] = GOLD
    sym = K.raster(K.sancak_armasi(waves=False), H, H * 0.20, (H * 0.60, H * 0.56))
    full = np.zeros((H, W), np.float32)
    full[:, :H] = sym
    img = embroider(img, full, 7, 6, outline_px=3)
    rgba = np.dstack([np.clip(img, 0, 1), a])
    return Image.fromarray((rgba * 255).astype(np.uint8)).resize((W // 2, H // 2), Image.LANCZOS)


def sail_emblem(S=2048):
    """Yelken amblemi: boyalı altın Yelken Hilali, koyu kızıl kontur; saydam zemin."""
    sym = K.raster(K.sancak_armasi(), S, S * 0.21, (S * 0.50, S * 0.48))
    m = Image.fromarray((sym * 255).astype(np.uint8))
    out = np.asarray(m.filter(ImageFilter.MaxFilter(25))).astype(np.float32) / 255.0
    img = np.zeros((S, S, 3), np.float32)
    ring = np.clip(out - sym, 0, 1)
    paint = GOLD[None, None] * (1 + 0.06 * noise(S, S, 64, 9)[..., None])
    img = img + CRIMSON[None, None] * 0.55 * ring[..., None] + paint * sym[..., None]
    a = np.clip(out, 0, 1) * (0.93 + 0.07 * noise(S, S, 16, 10))           # boya aşınması
    rgba = np.dstack([np.clip(img, 0, 1), np.clip(a, 0, 1)])
    return Image.fromarray((rgba * 255).astype(np.uint8))


def main():
    fl = ROOT / "Textures" / "flags"
    em = ROOT / "Textures" / "emblems"
    fl.mkdir(parents=True, exist_ok=True)
    em.mkdir(parents=True, exist_ok=True)
    ensign().save(fl / "T_Flag_KizilSancak_A.png")
    pennant().save(fl / "T_Pennant_KizilSancak_A.png")
    sail_emblem().save(em / "T_SailEmblem_KizilSancak_A.png")
    print("yazıldı: T_Flag_KizilSancak_A, T_Pennant_KizilSancak_A, T_SailEmblem_KizilSancak_A")


if __name__ == "__main__":
    main()
