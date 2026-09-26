"""v038 — açık yelkenler B: rüzgârla dolgun biçim, kumaş kıvrımları, kenar halatı, camadan, kanvas dokusu, yıpranma.

    python3.11 OTTOMAN_FRIGATE_1780_ISTANBUL/scripts/pass_v038_sails_b.py [--no-render | --render-only]

Kullanıcı: "bizim yelkenler biraz basit duruyor" (Fab gemisi referans ekran görüntüsü). Tespit (v037):
 - Açık yelkenler 120–192 yüzlük kaba ızgara (≈ 1,1 m hücre), karın zayıf, alt kenar düz, yaka yardın önünde şişkin.
 - Malzeme tek ton beyaz + gölgelendiricide çizgi; dikiş kabartısı, kenar halatı, camadan, kir/yıpranma yok.
 - Kalite testi açık yelkenleri görmedi (varsayılan durum "sarılı" → açık yelkenler render'da gizli, test atlıyor).
Yeni kurulum (yelken nesneleri, sürücüleri ve soketleri korunur; yalnız mesh ve malzeme değişir):
 1. Biçim: eski ızgaranın dört kenarından Coons yaması; yaka yarda boyunca düz (eski yakadaki 17 cm şişkinlik
    kaldırıldı), köşeler (iskota/karula bağlantıları) yerinde. Karın: derinlik = oran × en; kare yelken 0,10,
    flok/velena 0,08, randa 0,07 [TAHMİN, rüzgârla dolmuş yelken görünümü; resim ve modellerle karşılaştırmalı].
    Kare yelkende alt kenar kavisi (roach) yüksekliğin %3,5'i (≤ 45 cm) [TAHMİN].
 2. Ayrıntı (geometri, ≈ 15 cm ağ): yakada yarda bağlarının topladığı düşey kıvrımlar, iskota köşelerinden merkeze
    çapraz gerilme kırışıkları, flok/velenada gurcatalar boyunca kıvrım; gabya yelkenlerinde 3 camadan bandı
    (yakadan 1,4 / 2,8 / 4,2 m [TAHMİN]) hafif kabartı + iki yüzde sarkan camadan bağları (0,6 m arayla).
 3. Kenar halatı (r 2 cm, katranlı halat malzemesi) dört kenarda (üçgende üç).
 4. Malzeme MAT_Sail_Canvas_B: Textures/Sails/T_Sail_Canvas_B_{BC,N,ORM} (0,61 m bez eni, dikiş bindirmesi) ×
    "Weathering" renk özniteliği (alt kenar kiri, kenar isi, düşey yağmur izleri, camadan bandı kiri, onarım
    yamaları); arkadan ışıkta %22 geçirgenlik. Randa/flok/velena bezi biraz daha eski ton.
 5. Lale/rumi amblemleri eski yüzeydeki (u, v) konumlarından yeni yüzeye taşınır (1,2 cm önde).
 6. Donanım çakışması: yeni yelken, eski yelkenin kesişmediği bir halat/seren nesnesiyle kesişirse karın %15
    adımlarla küçültülür (raporlanır).
"""

import importlib.util
import json
import math
import sys
import zlib
from pathlib import Path

import bpy  # noqa: I001
import bmesh
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

HERE = Path(__file__).resolve().parent
sp = importlib.util.spec_from_file_location("pass_v033", HERE / "pass_v033_facet_cleanup.py")
P33 = importlib.util.module_from_spec(sp)
sp.loader.exec_module(P33)
P31 = P33.P31
RS, QA, LODS, H = P31.RS, P31.QA, P31.LODS, P31.H
ROOT, SHIP = P31.ROOT, P31.SHIP
SRC_VER, VER = "v037", "v038"
V = Vector
SPACING = 0.12
TILE = 2.44
ROPE_R = 0.020
REEF_M = (1.4, 2.8, 4.2)


# ------------------------------------------------------------------ yardımcılar
def mw(o):
    """Gizli nesnenin (açık yelken varsayılan gizli) matrix_world'ü hesaplanmaz → ebeveynsizde matrix_basis."""
    return o.matrix_basis.copy() if o.parent is None else o.matrix_world.copy()


def grid_of(me, nu):
    co = np.array([v.co[:] for v in me.vertices])
    return co.reshape(-1, nu, 3)


def _cr_curve(P, n):
    """Açık Catmull-Rom eğrisini n noktaya yeniden örnekler (uç uzatmalı, yay uzunluğuna göre)."""
    P = np.asarray(P, float)
    ext = np.vstack([2 * P[0] - P[1], P, 2 * P[-1] - P[-2]])
    seg = np.linalg.norm(np.diff(P, axis=0), axis=1)
    if seg.sum() < 1e-9:
        return np.repeat(P[:1], n, axis=0)
    s = np.concatenate([[0], np.cumsum(seg)]) / seg.sum()
    out = []
    for t in np.linspace(0, 1, n):
        i = min(np.searchsorted(s, t, side="right") - 1, len(P) - 2)
        L = s[i + 1] - s[i]
        tt = 0.0 if L < 1e-12 else (t - s[i]) / L
        p0, p1, p2, p3 = ext[i], ext[i + 1], ext[i + 2], ext[i + 3]
        t2, t3 = tt * tt, tt * tt * tt
        out.append(0.5 * (2 * p1 + (-p0 + p2) * tt + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    return np.array(out)


def _length(P):
    return float(np.linalg.norm(np.diff(np.asarray(P), axis=0), axis=1).sum())


def smooth_noise(n, scale, rng):
    """1B düzgün gürültü (n örnek, ~scale örnekte bir tepe)."""
    k = max(2, int(n / max(scale, 1)) + 3)
    g = rng.standard_normal(k)
    return np.interp(np.linspace(0, k - 3, n), np.arange(k), g)


def kind_of(name):
    if "JIB" in name or "STAYSAIL" in name:
        return "stay"
    if "SPANKER" in name:
        return "spanker"
    return "square"


# ------------------------------------------------------------------ biçim
def design(ob, rng, depth_scale=1.0):
    """Yeni yelken yüzeyi (yerel): dönüş (P[Nv,Nu,3], normal yönü b, param, bilgi)."""
    me = ob.data
    nu = 17 if len(me.vertices) == 221 else 11
    G = grid_of(me, nu)
    kind = kind_of(ob.name)
    head, foot, lu, ru = G[0], G[-1], G[:, 0], G[:, -1]
    collapsed = _length(head) < 0.30
    b_ax = np.array([1.0, 0, 0]) if kind == "square" else np.array([0, 1.0, 0])
    bell = G[1:-1, 1:-1] @ b_ax - ((G[1:-1, :1] @ b_ax + G[1:-1, -1:] @ b_ax) / 2)
    sgn = 1.0 if kind == "square" else (1.0 if bell.mean() >= 0 else -1.0)
    W = max(_length(G[len(G) // 2]), 1e-3)
    Hh = max(_length(G[:, nu // 2]), 1e-3)
    Nu = max(24, int(math.ceil(max(_length(r) for r in G) / SPACING)) + 1)
    Nv = max(24, int(math.ceil(max(_length(G[:, j]) for j in range(nu)) / SPACING)) + 1)
    if kind == "square":                              # yaka yarda boyunca düz
        head = np.array([head[0] + (head[-1] - head[0]) * t for t in np.linspace(0, 1, nu)])
    Hc = _cr_curve(head, Nu)
    Fc = _cr_curve(foot, Nu)
    Lc = _cr_curve(lu, Nv)
    Rc = _cr_curve(ru, Nv)
    # kenarlardaki eski karın bileşenini kaldır (düz kenar), yeni karın ekle
    for C in (Lc, Rc, Fc):
        C -= np.outer(C @ b_ax - np.linspace(C[0] @ b_ax, C[-1] @ b_ax, len(C)), b_ax)
    u = np.linspace(0, 1, Nu)[None, :, None]
    v = np.linspace(0, 1, Nv)[:, None, None]
    P = (1 - v) * Hc[None] + v * Fc[None] + (1 - u) * Lc[:, None] + u * Rc[:, None] \
        - ((1 - u) * (1 - v) * Hc[0] + u * (1 - v) * Hc[-1] + (1 - u) * v * Fc[0] + u * v * Fc[-1])
    uu = np.broadcast_to(u[..., 0], (Nv, Nu)).copy()
    vv = np.broadcast_to(v[..., 0], (Nv, Nu)).copy()
    ratio = {"square": 0.10, "stay": 0.08, "spanker": 0.07}[kind] * depth_scale
    D = ratio * W
    g = np.sin(np.pi * uu) ** 0.85
    f = np.sin(0.75 * np.pi * vv ** 0.8)
    disp = sgn * D * g * f
    # alt kenar kavisi (yalnız kare yelken; yelken düzleminde yukarı)
    if kind == "square":
        roach = min(0.035 * Hh, 0.45)
        up = np.array([0, 0, 1.0])
        P += (roach * np.sin(np.pi * uu) * np.clip((vv - 0.55) / 0.45, 0, 1) ** 2)[..., None] * up
    # ölçü koordinatları (m)
    Um = np.cumsum(np.concatenate([np.zeros((Nv, 1)), np.linalg.norm(np.diff(P, axis=1), axis=2)], axis=1), axis=1)
    Vm = np.cumsum(np.concatenate([np.zeros((1, Nu)), np.linalg.norm(np.diff(P, axis=0), axis=2)], axis=0), axis=0)
    det = np.zeros_like(uu)
    # yaka toplama kıvrımları
    ph = smooth_noise(Nu, Nu / 6, rng) * 1.2
    lam = 1.35
    zone = np.clip(1 - Vm / (0.20 * Hh), 0, 1) ** 2
    det += 0.045 * zone * np.sin(2 * np.pi * Um / lam + ph[None, :]) * (0.6 + 0.4 * np.sin(np.pi * uu))
    # iskota/karula köşesi gerilme kırışıkları (merkeze doğru çapraz sırtlar)
    cU, cV = Um[Nv // 2, Nu // 2], Vm[Nv // 2, Nu // 2]
    for ci, cj in ((Nv - 1, 0), (Nv - 1, Nu - 1)) + (((0, Nu - 1),) if kind == "spanker" else ()):
        x0, y0 = Um[ci, cj], Vm[ci, cj]
        d = np.array([cU - x0, cV - y0])
        d /= max(np.linalg.norm(d), 1e-9)
        t_perp = (Um - x0) * -d[1] + (Vm - y0) * d[0]
        r = np.hypot(Um - x0, Vm - y0)
        R = min(3.5, 0.35 * min(W, Hh))
        det += 0.026 * np.clip(1 - r / R, 0, 1) ** 2 * np.sin(2 * np.pi * t_perp / 1.05)
    # flok/velena: gurcata (stay) boyunca kıvrım
    if kind == "stay":
        zl = np.clip(1 - Um / (0.12 * W), 0, 1) ** 2
        det += 0.028 * zl * np.sin(2 * np.pi * Vm / 1.1)
    reef_rows = []
    if "TOPSAIL" in ob.name:
        for m in REEF_M:
            if m < 0.6 * Hh:
                det += 0.016 * np.exp(-((Vm - m) / 0.18) ** 2)
                reef_rows.append(m)
    # ayrıntı kenarda sıfırdan başlar (kenar halatı düzgün kalır; tek yönlü normal hatası taşınmaz);
    # çökmüş yaka (üçgen yelken tepesi) çevresinde ayrıca sönümlenir
    edge = np.minimum.reduce([Um, Um[:, -1:] - Um, Vm, Vm[-1:] - Vm])
    t = np.clip(edge / 0.35, 0, 1)
    det *= t * t * (3 - 2 * t)
    if collapsed:
        det *= np.clip(Vm / 1.5, 0, 1) ** 2
    # yüzey normali (yerel) ve yer değiştirme
    P = P + disp[..., None] * b_ax
    N = _normals(P)
    N *= np.sign((N @ b_ax).mean() or 1.0) * sgn
    P = P + det[..., None] * N
    N = _normals(P)
    N *= np.sign((N @ b_ax).mean() or 1.0) * sgn
    info = {"kind": kind, "grid": [int(Nv), int(Nu)], "width_m": round(W, 2), "height_m": round(Hh, 2),
            "belly_m": round(D, 2), "collapsed_head": bool(collapsed), "reef_bands_m": reef_rows}
    return P, N, (uu, vv, Um, Vm), info, (G, nu)


def _normals(P):
    du = np.gradient(P, axis=1)
    dv = np.gradient(P, axis=0)
    n = np.cross(du, dv)
    ln = np.linalg.norm(n, axis=2, keepdims=True)
    return n / np.maximum(ln, 1e-12)


# ------------------------------------------------------------------ yıpranma
def weathering(prm, info, rng, kind):
    uu, vv, Um, Vm = prm
    Nv, Nu = uu.shape
    W, Hh = Um[:, -1].max(), Vm[-1].max()
    dirt = 0.30 * vv ** 2.5
    edge = np.minimum.reduce([Um, Um[:, -1:] - Um, Vm, Vm[-1:] - Vm])
    dirt += 0.22 * np.exp(-edge / 0.30)
    streak = np.clip(smooth_noise(Nu, max(3, Nu / 40), rng), 0, None)[None, :] * np.clip(vv, 0.1, 1) ** 0.7
    dirt += 0.10 * streak + 0.05 * np.clip(smooth_noise(Nv, Nv / 5, rng), -1, 1)[:, None]
    for m in info["reef_bands_m"]:
        dirt += 0.16 * np.exp(-((Vm - m) / 0.10) ** 2)
    tint = np.ones_like(uu)
    for _ in range(int(2 + W * Hh / 60)):                   # onarım yamaları: bez enine hizalı
        c0 = math.floor(rng.uniform(0.1, 0.85) * W / 0.61) * 0.61
        w = 0.61 * rng.integers(1, 3)
        v0 = rng.uniform(0.15, 0.8) * Hh
        h = rng.uniform(0.7, 1.6)
        m = (Um >= c0) & (Um <= c0 + w) & (Vm >= v0) & (Vm <= v0 + h)
        tint[m] *= rng.choice([1.06, 0.93, 0.90])
    base = np.array([1.0, 1.0, 1.0]) if kind == "square" else np.array([0.93, 0.89, 0.82])
    grime = np.array([0.52, 0.47, 0.40])
    dirt = np.clip(dirt, 0, 0.75)
    col = (base[None, None] * (1 - dirt[..., None]) + grime[None, None] * dirt[..., None]) * tint[..., None]
    return np.clip(col, 0, 1)


# ------------------------------------------------------------------ mesh kurulumu
def _tube(bm, pts, r, mat, uvl, seg=None, caps=True):
    pts = [V(p) for p in pts]
    clean = [pts[0]]
    for p in pts[1:]:
        if (p - clean[-1]).length > 1e-4:
            clean.append(p)
    if len(clean) < 2:
        return []
    seg = seg or RS.required_segments(r)
    t0 = (clean[1] - clean[0]).normalized()
    n0 = t0.orthogonal().normalized()
    rings, faces = [], []
    prev_t = t0
    for i, p in enumerate(clean):
        t = ((clean[min(i + 1, len(clean) - 1)] - clean[max(i - 1, 0)])).normalized()
        n0 = (prev_t.rotation_difference(t) @ n0)
        n0 = (n0 - t * n0.dot(t)).normalized()
        b0 = t.cross(n0)
        prev_t = t
        rings.append([bm.verts.new(p + (n0 * math.cos(2 * math.pi * k / seg) + b0 * math.sin(2 * math.pi * k / seg)) * r)
                      for k in range(seg)])
    acc = [0.0]
    for a, b in zip(clean[:-1], clean[1:]):
        acc.append(acc[-1] + (b - a).length)
    for i in range(len(rings) - 1):
        A, B = rings[i], rings[i + 1]
        for k in range(seg):
            f = bm.faces.new([A[k], A[(k + 1) % seg], B[(k + 1) % seg], B[k]])
            f.material_index, f.smooth = mat, True
            if uvl is not None:
                for lp, t in zip(f.loops, [(k / seg, acc[i]), ((k + 1) / seg, acc[i]), ((k + 1) / seg, acc[i + 1]), (k / seg, acc[i + 1])]):
                    lp[uvl].uv = t
            faces.append(f)
    if caps:
        for R_, rev in ((rings[0], True), (rings[-1], False)):
            f = bm.faces.new(list(reversed(R_)) if rev else R_)
            f.material_index, f.smooth = mat, True
            faces.append(f)
    return faces


def build_mesh(ob, P, N, prm, info, col, rng, mats):
    Nv, Nu = P.shape[:2]
    uu, vv, Um, Vm = prm
    me = bpy.data.meshes.new(ob.data.name + "_B")
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    ccl = bm.loops.layers.float_color.new("Weathering")
    vs = [[bm.verts.new(V(P[i, j])) for j in range(Nu)] for i in range(Nv)]
    for i in range(Nv - 1):
        for j in range(Nu - 1):
            q = [vs[i][j], vs[i + 1][j], vs[i + 1][j + 1], vs[i][j + 1]]
            if info["kind"] != "square":
                q = [vs[i][j], vs[i][j + 1], vs[i + 1][j + 1], vs[i + 1][j]]
            f = bm.faces.new(q)
            f.material_index, f.smooth = 0, True
            for lp in f.loops:
                ii, jj = _ij(vs, lp.vert, i, j)
                lp[uvl].uv = (Um[ii, jj] / TILE, Vm[ii, jj] / TILE)
                c = col[ii, jj]
                lp[ccl] = (c[0], c[1], c[2], 1.0)
    # yaka noktası çökmüş üçgen yelken: çakışan köşeleri birleştir
    if info["collapsed_head"]:
        bmesh.ops.pointmerge(bm, verts=vs[0], merge_co=vs[0][0].co.copy())
    # yüz yönü: normal b yönünde (rüzgâr altı)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    # kenar halatı (üçgende çökmüş yaka atlanır)
    edges = [P[0, :], P[:, -1], P[-1, ::-1], P[::-1, 0]]
    n_rope = 0
    for E in edges:
        if _length(E) > 0.2:
            _tube(bm, list(E), ROPE_R, 1, uvl)
            n_rope += 1
    # camadan bağları: iki yüzde sarkan kısa bağlar
    n_reef = 0
    down = np.array([0, 0, -1.0])
    for m in info["reef_bands_m"]:
        i = int(np.argmin(np.abs(Vm[:, Nu // 2] - m)))
        W = Um[i, -1]
        for x in np.arange(0.5, W - 0.4, 0.6):
            j = int(np.argmin(np.abs(Um[i] - x)))
            p0, n0 = P[i, j], N[i, j]
            for side in (1, -1):
                a = p0 + n0 * side * 0.006
                pts = [a + n0 * side * (0.05 * math.sin(t * math.pi / 2)) + down * (0.24 * t) for t in np.linspace(0, 1, 8)]
                _tube(bm, pts, 0.005, 1, uvl, seg=6)
                n_reef += 1
    bm.to_mesh(me)
    bm.free()
    for m in mats:
        me.materials.append(m)
    RS.sharp_from_angle_keep(me, 35)
    info["bolt_rope_edges"] = n_rope
    info["reef_points"] = n_reef
    return me


def _ij(vs, vert, i, j):
    for di in (0, 1):
        for dj in (0, 1):
            if vs[i + di][j + dj] is vert:
                return i + di, j + dj
    return i, j


# ------------------------------------------------------------------ malzeme
def mat_canvas():
    m = bpy.data.materials.get("MAT_Sail_Canvas_B") or bpy.data.materials.new("MAT_Sail_Canvas_B")
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    tr = nt.nodes.new("ShaderNodeBsdfTranslucent")
    mix = nt.nodes.new("ShaderNodeMixShader")
    mix.inputs["Fac"].default_value = 0.22
    tex_dir = ROOT / "Textures" / "Sails"

    def img(name, non_color):
        t = nt.nodes.new("ShaderNodeTexImage")
        im = bpy.data.images.load(str(tex_dir / name), check_existing=True)
        if non_color:
            im.colorspace_settings.name = "Non-Color"
        t.image = im
        return t
    bc, nm, orm = img("T_Sail_Canvas_B_BC.png", False), img("T_Sail_Canvas_B_N.png", True), img("T_Sail_Canvas_B_ORM.png", True)
    attr = nt.nodes.new("ShaderNodeAttribute")
    attr.attribute_name = "Weathering"
    mul = nt.nodes.new("ShaderNodeMix")
    mul.data_type, mul.blend_type = "RGBA", "MULTIPLY"
    mul.inputs["Factor"].default_value = 1.0
    nt.links.new(bc.outputs["Color"], mul.inputs["A"])
    nt.links.new(attr.outputs["Color"], mul.inputs["B"])
    nt.links.new(mul.outputs["Result"], bsdf.inputs["Base Color"])
    nt.links.new(mul.outputs["Result"], tr.inputs["Color"])
    sep = nt.nodes.new("ShaderNodeSeparateColor")
    nt.links.new(orm.outputs["Color"], sep.inputs["Color"])
    nt.links.new(sep.outputs["Green"], bsdf.inputs["Roughness"])
    nmap = nt.nodes.new("ShaderNodeNormalMap")
    nmap.inputs["Strength"].default_value = 0.8
    nt.links.new(nm.outputs["Color"], nmap.inputs["Color"])
    nt.links.new(nmap.outputs["Normal"], bsdf.inputs["Normal"])
    bsdf.inputs["Sheen Weight"].default_value = 0.25
    nt.links.new(bsdf.outputs["BSDF"], mix.inputs[1])
    nt.links.new(tr.outputs["BSDF"], mix.inputs[2])
    nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])
    m["ue_note"] = "UE: BC × vertex color (Weathering), N, ORM; iki yüzlü, Two Sided Foliage/Subsurface ≈ %22 geçirgenlik"
    return m


# ------------------------------------------------------------------ amblem taşıma
def remap_emblem(emb, sail, G_old, nu_old, P, N):
    Mi = mw(sail).inverted()
    verts_old = [V(p) for p in G_old.reshape(-1, 3)]
    nv_old = len(G_old)
    faces = [(i * nu_old + j, (i + 1) * nu_old + j, (i + 1) * nu_old + j + 1, i * nu_old + j + 1)
             for i in range(nv_old - 1) for j in range(nu_old - 1)]
    tree = BVHTree.FromPolygons(verts_old, faces)
    Nv, Nu = P.shape[:2]
    me = emb.data
    Me = mw(emb)
    Mei = Me.inverted()
    moved = 0
    for vtx in me.vertices:
        p = Mi @ (Me @ vtx.co)
        loc, nrm, fi, d = tree.find_nearest(p, 5.0)
        if fi is None:
            continue
        i, j = divmod(fi, nu_old - 1)
        a = G_old[i, j]
        e1, e2 = G_old[i, j + 1] - a, G_old[i + 1, j] - a
        q = np.array(loc) - a
        s = np.clip(q @ e1 / max(e1 @ e1, 1e-12), 0, 1)
        t = np.clip(q @ e2 / max(e2 @ e2, 1e-12), 0, 1)
        u, v = (j + s) / (nu_old - 1), (i + t) / (nv_old - 1)
        side = 1.0 if (p - loc).dot(nrm) >= 0 else -1.0
        x, y = u * (Nu - 1), v * (Nv - 1)
        j0, i0 = min(int(x), Nu - 2), min(int(y), Nv - 2)
        fx, fy = x - j0, y - i0
        pt = (P[i0, j0] * (1 - fx) * (1 - fy) + P[i0, j0 + 1] * fx * (1 - fy) + P[i0 + 1, j0] * (1 - fx) * fy + P[i0 + 1, j0 + 1] * fx * fy)
        nn = (N[i0, j0] * (1 - fx) * (1 - fy) + N[i0, j0 + 1] * fx * (1 - fy) + N[i0 + 1, j0] * (1 - fx) * fy + N[i0 + 1, j0 + 1] * fx * fy)
        nn /= max(np.linalg.norm(nn), 1e-9)
        # eski yüzeyde hangi yüzdeydi: eski normale göre; yeni normal aynı yöne bakıyorsa aynı işaret
        sgn = side * (1.0 if np.dot(nn, np.array(nrm)) >= 0 else -1.0)
        vtx.co = Mei @ (mw(sail) @ V(pt + nn * sgn * 0.012))
        moved += 1
    me.update()
    return moved


# ------------------------------------------------------------------ çakışma
def _bvh(o):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = o.evaluated_get(dg)
    me = ev.to_mesh()
    M = mw(o)
    vs = [M @ v.co for v in me.vertices]
    fs = [tuple(p.vertices) for p in me.polygons]
    ev.to_mesh_clear()
    if not fs:
        return None, None
    lo = V((min(v.x for v in vs), min(v.y for v in vs), min(v.z for v in vs)))
    hi = V((max(v.x for v in vs), max(v.y for v in vs), max(v.z for v in vs)))
    return BVHTree.FromPolygons(vs, fs), (lo, hi)


def clashes(sail, others):
    t, bb = _bvh(sail)
    out = set()
    if t is None:
        return out
    for o, (to, bbo) in others.items():
        if to is None or any(bb[1][k] < bbo[0][k] or bbo[1][k] < bb[0][k] for k in range(3)):
            continue
        if to.overlap(t):
            out.add(o)
    return out


# ------------------------------------------------------------------ ana akış
def render(sc):
    H.setup_render(sc, fast=True)
    sc.cycles.samples = 32
    out = ROOT / "renders" / VER
    out.mkdir(parents=True, exist_ok=True)
    ctrl = bpy.data.objects.get("CTRL_YELKEN")
    # başsız modda sürücü sonucu yazılmaz → görünürlüğü doğrudan ayarla (dosyaya kaydedilmez)
    for o in bpy.data.objects:
        st = o.get("sail_state")
        if st and o.animation_data:
            for fc in list(o.animation_data.drivers):
                if fc.data_path in ("hide_render", "hide_viewport"):
                    o.animation_data.drivers.remove(fc)
        if st:
            o.hide_render = o.hide_viewport = (st == "furled")
    if ctrl:
        ctrl["yelken_acik"] = 1
    for name, loc, tgt, lens in (("yelken_genel", V((-38, 30, 22)), V((0, 0, 16)), 32),
                                 ("yelken_yakin", V((-8, 14, 20)), V((2, 0, 19)), 35),
                                 ("yelken_bas", V((34, 22, 14)), V((8, 0, 16)), 35),
                                 ("yelken_ters_isik", V((30, -26, 12)), V((0, 0, 17)), 30)):
        sc.camera = H.camera(sc, f"CAM38_{name}", loc, tgt, lens=lens)
        sc.render.filepath = str(out / f"{SHIP}_{VER}_{name}.png")
        bpy.ops.render.render(write_still=True)


def main():
    if "--render-only" in sys.argv:
        bpy.ops.wm.open_mainfile(filepath=str(ROOT / "Blender" / "versions" / f"{SHIP}_{VER}.blend"))
        return render(bpy.context.scene)
    out = ROOT / "Blender" / "versions" / f"{SHIP}_{VER}.blend"
    if out.exists():
        raise SystemExit(f"{out} zaten var; versiyonlu kayıt üzerine yazılmaz.")
    bpy.ops.wm.open_mainfile(filepath=str(ROOT / "Blender" / "versions" / f"{SHIP}_{SRC_VER}.blend"))
    sc = bpy.context.scene
    bpy.context.view_layer.update()          # yüklemeden sonra matrix_world güncel değil (sürücülü nesneler)
    rng = np.random.default_rng(38)
    canvas = mat_canvas()
    rope = bpy.data.materials["MAT_Rope_Tarred"]
    sails = sorted((o for o in bpy.data.objects if o.name.startswith("MOD_SAIL_SET_") and "_LOD" not in o.name and o.type == "MESH"), key=lambda o: o.name)
    emblems = {o.name: o for o in bpy.data.objects if o.name.startswith("MOD_SAIL_EMBLEM_") and "_LOD" not in o.name}
    rig = [o for o in bpy.data.objects if o.type == "MESH" and o.name.startswith(("MOD_RIG_", "MOD_SAIL_SET_"))
           and "_LOD" not in o.name and not o.name.startswith("UCX_")]
    others = {o.name: _bvh(o) for o in rig}
    rep = {}
    only = [x for x in sys.argv if x.startswith("--only=")]
    if only:
        sails = [o for o in sails if o.name in only[0][7:].split(",")]
    for ob in sails:
        base = clashes(ob, {k: v for k, v in others.items() if k != ob.name})
        old_me = ob.data
        G_old = None
        # karın ölçeği: çakışma karından kaynaklanıyorsa küçült; en küçük ölçekte de süren çakışma karından değildir
        # (mevcut donanım yakınlığı) → o durumda tam karın korunur ve raporlanır
        trials = {}
        for scale in (1.0, 0.85, 0.7, 0.55, 0.4):
            P, N, prm, info, (G_old, nu_old) = design(ob, np.random.default_rng(zlib.crc32(ob.name.encode())), scale)
            col = weathering(prm, info, np.random.default_rng(zlib.crc32(ob.name.encode()) + 7), info["kind"])
            me = build_mesh(ob, P, N, prm, info, col, rng, [canvas, rope])
            ob.data = me
            new = clashes(ob, {k: v for k, v in others.items() if k != ob.name}) - base
            ob.data = old_me
            trials[scale] = (P, N, prm, info, me, new)
            if not new:
                break
        floor = trials[min(trials)][5]
        scale = max(sc_ for sc_, t in trials.items() if t[5] <= floor)
        P, N, prm, info, me, res = trials[scale]
        for sc_, t in trials.items():
            if sc_ != scale:
                bpy.data.meshes.remove(t[4])
        ob.data = me
        # amblemler
        key = ob.name.replace("MOD_SAIL_SET_", "").replace("_A", "")
        em = [e for n, e in emblems.items() if n.endswith("_" + key)]
        for e in em:
            info.setdefault("emblems", {})[e.name] = remap_emblem(e, ob, G_old, nu_old, P, N)
        name = old_me.name
        if old_me.users == 0:
            bpy.data.meshes.remove(old_me)
        me.name = name
        me.calc_loop_triangles()
        info.update({"belly_scale": round(scale, 2), "new_clashes": sorted(res), "tris": len(me.loop_triangles)})
        others[ob.name] = _bvh(ob)
        rep[ob.name] = info
    changed = [o.name for o in sails] + list(emblems)
    for n in changed:
        for o in [o for o in bpy.data.objects if o.name.startswith(n + "_LOD")]:
            bpy.data.objects.remove(o, do_unlink=True)
    LODS.build_lods(sc, only=set(changed))
    bpy.ops.wm.save_as_mainfile(filepath=str(out), compress=True)
    H.VERSION = VER
    ap = ROOT / "reports" / f"scene_audit_{VER}.json"
    arep = H.audit(sc, ap)
    arep["sails_v038"] = rep
    arep["pass"] = {"name": "pass_v038_sails_b", "source": f"Blender/versions/{SHIP}_{SRC_VER}.blend"}
    # kalite testi: açık yelkenler görünür durumda da ölçülür (varsayılan durum sarılı → test onları atlıyordu)
    dg = bpy.context.evaluated_depsgraph_get()
    sail_q = {}
    for ob in sails + [emblems[n] for n in emblems]:
        m = QA.facet_metrics(ob, dg)
        sail_q[ob.name] = {"tris": m[0], "facet_m": round(m[1], 2), "worst_sag_mm": round(m[5] * 1000, 1)}
    arep["sails_v038_quality"] = sail_q
    ap.write_text(json.dumps(arep, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    qa = QA.audit(sc, top=60)
    qa["open_sails"] = sail_q
    (ROOT / "reports" / f"kalite_testi_{VER}.json").write_text(json.dumps(qa, indent=1, ensure_ascii=False), encoding="utf-8")
    print("V038", json.dumps(rep, ensure_ascii=False, default=str))
    print("V038 SAIL QA", json.dumps(sail_q, ensure_ascii=False))
    print("V038 QA", json.dumps(qa["summary"], ensure_ascii=False))
    if "--no-render" not in sys.argv:
        render(sc)


if __name__ == "__main__":
    main()
