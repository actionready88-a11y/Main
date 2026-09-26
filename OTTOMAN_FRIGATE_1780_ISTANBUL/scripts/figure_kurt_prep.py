"""Kurt Gemi Figürü (Meshy, kullanıcı üretimi) — ay-yıldızdaki yıldızları silme (hilal kalır).

Kullanıcı kararı (KIZIL_SANCAK_UYARLAMA_PLANI §0): "Yıldızı sil, hilal kalsın" — Yüzde Yetmiş Özgünlük Kuralı.
Modelde 3 ay-yıldız var: alın (miğfer) ve iki omuz zırhı. Her biri hem geometride kabartma hem renk dokusunda yaldız.

Yöntem (ham GLB uzayında; yüz −Y, montaj bloğu +Y):
1. Yıldız merkezi: bilinen kameradan piksel ışını → yüzey noktası + normal (`STARS`).
2. Geometri: merkez çevresindeki halkadan (1,25r–1,7r) alt zarf düzlemi (zemin) oturtulur; r içindeki ve düzlemin
   üstündeki köşeler düzleme indirilir (kenarda yumuşak geçiş). Hilal halkanın dışında kalır.
3. Doku: r içindeki yüzlerin UV üçgenleri maskelenir; BC → halkanın koyu zemin pikselleri (rastgele örnek + bulanık),
   N → halkanın normal pikselleri (grenli zemin), ORM → halka medyanı.
"""

import math
import random

import bmesh
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from PIL import Image, ImageDraw, ImageFilter

V = Vector
RES = 700
LENS = 50.0
# (ad, kamera konumu, hedef, yıldız merkez pikseli, yıldız yarıçapı px) — ham GLB uzayı, 700×700 render
STARS = (
    ("alin", (0, -1.3, 0.95), (0, -0.5, 0.55), (412, 504), 36),
    ("omuz_sol", (1.2, -0.9, 0.35), (0.3, -0.25, 0.1), (410, 422), 21),
    ("omuz_sag", (-1.2, -0.9, 0.35), (-0.3, -0.25, 0.1), (309, 415), 23),
)


def pixel_ray(loc, tgt, px):
    loc, tgt = V(loc), V(tgt)
    fwd = (tgt - loc).normalized()
    q = fwd.to_track_quat("-Z", "Y")
    right = q @ V((1, 0, 0))
    up = q @ V((0, 1, 0))
    half = math.tan(math.atan(36.0 / (2 * LENS)))          # sensör 36 mm, kare çıktı
    u = (px[0] + 0.5) / RES * 2 - 1
    v = 1 - (px[1] + 0.5) / RES * 2
    d = (fwd + right * u * half + up * v * half).normalized()
    return loc, d, 2 * half / RES


def locate(tree, entry):
    name, loc, tgt, px, rpx = entry
    o, d, pxsz = pixel_ray(loc, tgt, px)
    hit = tree.ray_cast(o, d, 10.0)
    if hit[0] is None:
        return None
    r = rpx * pxsz * hit[3]
    n = hit[1] if hit[1].dot(d) < 0 else -hit[1]
    return {"name": name, "c": hit[0], "n": n.normalized(), "r": r}


def _fit_floor(pts, n0):
    """Alt zarf düzlemi: en küçük kareler, tepede kalanları (hilal, süs) atarak 4 tur."""
    P = np.array([tuple(p) for p in pts])
    n = np.array(tuple(n0))
    for _ in range(4):
        c = P.mean(axis=0)
        _, _, vt = np.linalg.svd(P - c)
        n = vt[2] if vt[2].dot(np.array(tuple(n0))) > 0 else -vt[2]
        h = (P - c) @ n
        keep = h <= np.percentile(h, 60)
        if keep.sum() < 12:
            break
        P = P[keep]
    return V(tuple(P.mean(axis=0))), V(tuple(n)).normalized()


def flatten(bm, s):
    c, n, r = s["c"], s["n"], s["r"]
    R0, R1 = 1.25 * r, 1.7 * r
    near, ring = [], []
    for v in bm.verts:
        d = v.co - c
        h = d.dot(n)
        lat = (d - n * h).length
        if abs(h) > 0.6 * r or v.normal.dot(n) < -0.2:
            continue
        if lat < 1.08 * r:
            near.append((v, lat))
        elif R0 < lat < R1:
            ring.append(v.co.copy())
    if len(ring) < 12:
        return {"moved": 0, "ring": len(ring)}
    p0, pn = _fit_floor(ring, n)
    moved, hmax = 0, 0.0
    for v, lat in near:
        h = (v.co - p0).dot(pn)
        if h <= 0.0:
            continue
        w = 1.0 if lat < 0.9 * r else max(0.0, (1.08 * r - lat) / (0.18 * r))
        v.co -= pn * h * w
        hmax = max(hmax, h)
        moved += 1
    s["floor"] = (p0, pn)
    return {"moved": moved, "ring": len(ring), "relief_mm_raw": round(hmax * 1000, 2)}


def _uv_polys(bm, uv, faces, W, Hh):
    out = []
    for f in faces:
        out.append([(l[uv].uv.x * W, (1 - l[uv].uv.y) * Hh) for l in f.loops])
    return out


def face_sets(bm, s):
    c, n, r = s["c"], s["n"], s["r"]
    inner, ring = [], []
    for f in bm.faces:
        d = f.calc_center_median() - c
        h = d.dot(n)
        if abs(h) > 0.6 * r or f.normal.dot(n) < 0.2:
            continue
        lat = (d - n * h).length
        if lat < 1.12 * r:
            inner.append(f)
        elif 1.3 * r < lat < 1.9 * r:
            ring.append(f)
    return inner, ring


def _load(im):
    w, h = im.size
    a = np.empty(w * h * 4, dtype=np.float32)
    im.pixels.foreach_get(a)
    return a.reshape(h, w, 4)[::-1].copy()        # üst satır 0


def _store(im, arr):
    im.pixels.foreach_set(arr[::-1].astype(np.float32).ravel())
    im.update()


def fix_textures(bm, stars, imgs):
    """imgs: {'BC': image, 'N': image, 'ORM': image}. Diziler yerinde değişir."""
    uv = bm.loops.layers.uv.active
    rng = random.Random(7)
    arrs = {k: _load(im) for k, im in imgs.items() if im is not None}
    rep = {}
    for s in stars:
        inner, ring = face_sets(bm, s)
        rp = {"faces": len(inner), "ring_faces": len(ring)}
        for k, A in arrs.items():
            Hh, W = A.shape[:2]
            m = Image.new("L", (W, Hh), 0)
            dr = ImageDraw.Draw(m)
            for p in _uv_polys(bm, uv, inner, W, Hh):
                dr.polygon(p, fill=255)
            m = m.filter(ImageFilter.MaxFilter(5))        # UV dikiş sızıntısı için 2 px genişlet
            rm = Image.new("L", (W, Hh), 0)
            dr = ImageDraw.Draw(rm)
            for p in _uv_polys(bm, uv, ring, W, Hh):
                dr.polygon(p, fill=255)
            M = np.array(m) > 127
            RM = (np.array(rm) > 127) & ~M
            if not M.any() or not RM.any():
                continue
            ringpx = A[RM]
            if k in ("BC", "N"):
                if k == "BC":
                    lum = ringpx[:, :3] @ np.array([0.3, 0.59, 0.11])
                    dark = ringpx[lum <= np.percentile(lum, 35)]     # yaldız değil, koyu zemin
                else:
                    dark = ringpx                                     # zeminin ince doku kabartısı korunur
                idx = np.array([rng.randrange(len(dark)) for _ in range(int(M.sum()))])
                fill = dark[idx]
                B = A.copy()
                B[M] = fill
                # rastgele örnek → hafif bulanık (grenli zemin gibi)
                img = Image.fromarray((np.clip(B[:, :, :3], 0, 1) * 255).astype(np.uint8))
                bl = np.asarray(img.filter(ImageFilter.GaussianBlur(1.2))).astype(np.float32) / 255.0
                A[M, 0:3] = bl[M]
                rp[f"{k.lower()}_fill_rgb"] = [round(float(x), 3) for x in dark[:, :3].mean(axis=0)]
            else:
                A[M, 0:3] = np.median(ringpx[:, :3], axis=0)
            rp[f"{k}_px"] = int(M.sum())
        rep[s["name"]] = rp
    for k, A in arrs.items():
        _store(imgs[k], A)
    return rep


def remove_stars(ob, imgs):
    """ob: ham GLB uzayında (dönüşüm uygulanmamış) Kurt figürü. Geometri + doku düzeltmesi."""
    me = ob.data
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.transform(ob.matrix_world)
    bm.normal_update()
    tree = BVHTree.FromBMesh(bm)
    stars = [s for s in (locate(tree, e) for e in STARS) if s]
    rep = {"found": [s["name"] for s in stars]}
    rep["textures"] = fix_textures(bm, stars, imgs)          # önce doku (yüz seçimi kabartma üstünde)
    for s in stars:
        rep[s["name"]] = dict(flatten(bm, s), center=[round(x, 3) for x in s["c"]], r_m=round(s["r"], 3))
    bm.transform(ob.matrix_world.inverted())
    bm.to_mesh(me)
    bm.free()
    me.update()
    return rep


def material_images(ob):
    m = ob.data.materials[0]
    nt = m.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    out = {"BC": None, "N": None, "ORM": None}
    for n in nt.nodes:
        if n.type != "TEX_IMAGE" or not n.image:
            continue
        to = [lk.to_node for lk in nt.links if lk.from_node == n]
        if any(t.type == "NORMAL_MAP" for t in to):
            out["N"] = n.image
        elif any(t.type == "SEPARATE_COLOR" for t in to):
            out["ORM"] = n.image
        elif bsdf in to:
            out["BC"] = n.image
    return out
