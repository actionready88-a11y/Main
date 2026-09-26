"""Pass v015 — RigSet: üç direk (alt direk + çanaklık + gabya + babafingo), serenler, cıvadıra, sabit arma
(çarmıhlar + iskalarya, istralyalar, patrisalar), kuşak tahtaları (channels); tırmanma soketleri ve UCX. v014 üzerine.

Çalıştırma (depo kökünden):
    python3 OTTOMAN_FRIGATE_1780_ISTANBUL/scripts/pass_v015_rigset.py [--no-render | --render-only]

Kullanıcı kararı (2026-09-26): top modülünden sonra "direkler ve arma"; "her yer AC tarzı tırmanılabilir".
Yelken yok (SailSet ayrı). Hareketli arma (halat/makara) yok; sonraki RigSet pass'i.

Kaynak / tahmin (web kaynaklarının çoğu bu ortamda açılamadı → oranlar TAHMİN, Lees tablosuyla doğrulanmalı):
  - Direk yerleri: v001 MAST_S (HIBRIT_CHATGPT_03 profilinden ölçüldü).
  - Ana direk boyu (topuktan başlığa) = (güverte boyu + en) / 2 — dönem kuralı olarak yaygın; TAHMİN.
  - Direk çapı: "her yarda için bir inç" — TAHMİN (dönem kuralı).
  - Pruva direği = 8/9 ana; mizana = 0,86 ana; gabya = 0,6 alt direk (mizana 0,55); babafingo = 0,5 gabya — TAHMİN.
  - Ana seren = 0,56 × güverte boyu; pruva 0,875 ana; mizana (crossjack) 0,7 ana; gabya sereni 0,72 alt
    sereni; babafingo 0,66 gabya — TAHMİN.
  - Cıvadıra = 0,6 ana direk, eğim 25° — TAHMİN. Çarmıh sayısı ana/pruva 9, mizana 5 (bordada) — TAHMİN.
Tüm ölçüler tasarım uzayında kurulur (HMS Lyme), dünyaya ×1,10 ve +DWL ile geçer.
"""

import importlib.util
import json
import math
import sys
from pathlib import Path

import bpy  # noqa: I001
import bmesh
import numpy as np
from mathutils import Matrix, Vector

HERE = Path(__file__).resolve().parent


def _load(name, fname):
    sp = importlib.util.spec_from_file_location(name, HERE / fname)
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


P14 = _load("pass_v014", "pass_v014_cannon_9pdr.py")
P13 = P14.P13
P5, H, K = P13.P5, P13.H, P13.K
C3 = P5.C3
SRC_VER, VER = "v014", "v015"
ROOT, SHIP = H.ROOT, H.SHIP_ID
MANIFEST_VERSION = 13
P5.MANIFEST_VERSION = MANIFEST_VERSION
DWL = P13.DWL
TW = Matrix.Translation((0.0, 0.0, DWL)) @ Matrix.Scale(K, 4)
Y = Vector((0, 1, 0))

HEEL_Z = -H.T + 0.70                       # iç omurga üstü (tasarım)
L_MAIN = 0.5 * (H.L + H.B)                 # TAHMİN
MASTS = {  # ad: (alt direk boyu, gabya oranı, yatıklık derece, çarmıh/borda, patrisa/borda)
    "FORE": (L_MAIN * 8 / 9, 0.60, 0.0, 9, 2),
    "MAIN": (L_MAIN, 0.60, 1.5, 9, 2),
    "MIZZEN": (L_MAIN * 0.86, 0.55, 3.0, 5, 1),
}
YARD_MAIN = 0.56 * H.L
YARD_K = {"FORE": 0.875, "MAIN": 1.0, "MIZZEN": 0.70}
BS_STEEVE = math.radians(25.0)
SHROUD_STEP = 0.75
RAT_STEP = 0.36                            # iskalarya aralığı (tasarım) → 0,40 m dünya
R_SHROUD, R_STAY, R_RAT, R_FOOT = 0.028, 0.045, 0.011, 0.014


# --- Temel geometri ---------------------------------------------------------------
def tube(bm, pts, r, seg=6):
    """Nokta dizisi boyunca yuvarlak kesitli halat (uçları kapalı)."""
    pts = [Vector(p) for p in pts]
    rings = []
    for i, p in enumerate(pts):
        a = pts[max(i - 1, 0)]
        b = pts[min(i + 1, len(pts) - 1)]
        t = (b - a).normalized()
        u = t.cross(Vector((0, 0, 1)))
        if u.length < 1e-3:
            u = t.cross(Vector((1, 0, 0)))
        u.normalize()
        v = t.cross(u)
        rings.append([bm.verts.new(p + (u * math.cos(2 * math.pi * k / seg) + v * math.sin(2 * math.pi * k / seg)) * r)
                      for k in range(seg)])
    for r0, r1 in zip(rings[:-1], rings[1:]):
        for k in range(seg):
            bm.faces.new([r0[k], r0[(k + 1) % seg], r1[(k + 1) % seg], r1[k]])
    bm.faces.new(list(reversed(rings[0])))
    bm.faces.new(rings[-1])


def spar(bm, p0, p1, r0, r1, seg=16, rmid=None):
    """p0→p1 arasında konik yuvarlak ağaç (rmid: ortada şişkinlik)."""
    d = (p1 - p0)
    L = d.length
    prof = [(0.0, 0.0), (r0, 0.0)]
    if rmid:
        prof += [(rmid, L * 0.5)]
    prof += [(r1, L), (0.0, L)]
    P5.lathe(bm, prof, seg, P5.axis_matrix(p0, d))


def disc(bm, c, n, r, h, seg=12):
    """c merkezli, n eksenli kısa silindir (bigota/deadeye)."""
    P5.lathe(bm, [(0.0, -h / 2), (r * 0.8, -h / 2), (r, -h / 4), (r, h / 4), (r * 0.8, h / 2), (0.0, h / 2)], seg, P5.axis_matrix(c, n))


def obox(bm, c, X, Yv, Z, sx, sy, sz):
    """Yönlü kutu: merkez c, eksenler X/Yv/Z, yarı boyutlar."""
    pts = []
    for dz in (-sz, sz):
        for dx, dy in ((-sx, -sy), (sx, -sy), (sx, sy), (-sx, sy)):
            pts.append(c + X * dx + Yv * dy + Z * dz)
    P5.box8(bm, [pts[0], pts[1], pts[2], pts[3], pts[4], pts[5], pts[6], pts[7]])


def finish(name, parts, col, sharp=35, bevel=None, world=True, origin=None):
    """parts: [(bmesh, malzeme)] → tek nesne (tasarım → dünya)."""
    merged = bmesh.new()
    mats = []
    for idx, (b, mat) in enumerate(parts):
        if world:
            b.transform(TW)
        me = bpy.data.meshes.new("_tmp")
        bmesh.ops.recalc_face_normals(b, faces=b.faces)
        b.to_mesh(me)
        b.free()
        me.polygons.foreach_set("material_index", [idx] * len(me.polygons))
        merged.from_mesh(me)
        bpy.data.meshes.remove(me)
        mats.append(mat)
    ob = P5.finish(name, merged, col, mats, sharp=sharp, bevel=bevel)
    if origin is not None:
        ob.data.transform(Matrix.Translation(-Vector(origin)))
        ob.location = Vector(origin)
    return ob


def W(p):
    return TW @ Vector(p)


# --- Direk çerçevesi -----------------------------------------------------------------
class Mast:
    def __init__(self, name):
        self.name = name
        Lm, kt, rake, n_sh, n_bs = MASTS[name]
        sock = bpy.data.objects[f"SOCKET_MAST_{name}"]
        base_w = sock.location
        self.base = Vector((base_w.x / K, 0.0, (base_w.z - DWL) / K))   # üst güvertede (tasarım)
        r = math.radians(rake)
        self.A = Vector((-math.sin(r), 0.0, math.cos(r)))             # direk ekseni (kıça yatık)
        self.F = Vector((math.cos(r), 0.0, math.sin(r)))              # ileri
        self.rake = r
        self.Lm = Lm
        self.D = 0.0278 * Lm                                          # 1 inç / yarda
        zc = HEEL_Z + Lm
        self.t_cap = (zc - self.base.z) / math.cos(r)
        self.hd = 0.111 * Lm
        self.t_h = self.t_cap - self.hd                               # çanaklık (hounds)
        self.t_low = (P13.zl(self.s()) - self.base.z) - 0.12           # görünür alt uç: alt güverte
        self.Lt = kt * Lm
        self.Dt = 0.025 * self.Lt
        self.ft = self.D / 2 + self.Dt / 2 + 0.06                      # gabya ileri kaçıklığı
        self.t_t0 = self.t_h - 0.35
        self.t_t1 = self.t_t0 + self.Lt
        self.hd_t = 0.12 * self.Lt
        self.t_th = self.t_t1 - self.hd_t                             # gabya çanaklığı
        self.Lg = 0.5 * self.Lt
        self.Dg = 0.022 * self.Lg
        self.fg = self.ft + self.Dt / 2 + self.Dg / 2 + 0.04
        self.t_g0 = self.t_th - 0.25
        self.t_g1 = self.t_g0 + self.Lg
        self.top_w = self.Lt / 3.0
        self.top_l = 0.75 * self.top_w
        self.n_sh, self.n_bs = n_sh, n_bs

    def s(self):
        return P13.s_of_x(self.base.x, P13.zu)

    def P(self, t, f=0.0, v=0.0):
        return self.base + self.A * t + self.F * f + Y * v


# --- Direkler ---------------------------------------------------------------------
def build_mast(m, col, M):
    bw, bi, bk = bmesh.new(), bmesh.new(), bmesh.new()    # ağaç, demir, siyah (çanaklık)
    # alt direk: alt güverteden başlığa (konik); başlık dört köşe
    spar(bw, m.P(m.t_low), m.P(m.t_h), m.D / 2, m.D * 0.40, seg=20, rmid=m.D * 0.5)
    hd = m.D * 0.40
    obox(bw, m.P((m.t_h + m.t_cap) / 2), m.F, Y, m.A, hd, hd, (m.t_cap - m.t_h) / 2)
    for t in np.arange(0.4, m.t_h - 1.5, 1.25):          # demir çemberler (güverte üstü)
        r = (m.D / 2) * (1 - 0.2 * t / m.t_h) + 0.012
        P5.lathe(bi, [(r - 0.02, 0.0), (r, 0.0), (r, 0.06), (r - 0.02, 0.06)], 20, P5.axis_matrix(m.P(t), m.A))
    # yanaklar (cheeks) ve kıstaklar (trestletrees / crosstrees) — çanaklık altı
    for sgn in (1, -1):
        obox(bw, m.P(m.t_h - 1.1, 0.0, sgn * (m.D * 0.45 + 0.06)), m.F, Y, m.A, m.D * 0.5, 0.06, 1.1)
        obox(bk, m.P(m.t_h + 0.09, m.top_l * 0.05, sgn * (m.D * 0.40 + 0.09)), m.F, Y, m.A, m.top_l * 0.5, 0.08, 0.09)
    for u in (-0.30, 0.05, 0.40):
        obox(bk, m.P(m.t_h + 0.24, u * m.top_l, 0.0), m.F, Y, m.A, 0.07, m.top_w * 0.46, 0.06)
    # çanaklık platformu: D biçimi, iskele-sancak ortada lubber deliği
    # D biçimi: kıç kenarı düz, baş tarafı yarım elips; ortada lubber deliği. Merkezden ışınlarla halka ızgara.
    hole_u, hole_v = (-0.55, 0.75), 0.80
    uc0 = (hole_u[0] + hole_u[1]) / 2
    ua, ub, hw = -0.45 * m.top_l, 0.55 * m.top_l, m.top_w / 2

    def outer(th):
        du, dv = math.cos(th), math.sin(th)
        best = 1e9
        if du < -1e-6:                                   # kıç kenarı (düz)
            best = min(best, (ua - uc0) / du)
        if abs(dv) > 1e-6:                               # yan kenarlar (kıç yarısında düz)
            r = (math.copysign(hw, dv)) / dv
            if uc0 + r * du <= 0.0:
                best = min(best, r)
        lo, hi = 0.0, 20.0                               # baş yarısı: elips (ikiye bölme)
        for _ in range(50):
            mid = (lo + hi) / 2
            u, v = uc0 + mid * du, mid * dv
            inside = (u <= 0 and abs(v) <= hw and u >= ua) or (u > 0 and (u / ub) ** 2 + (v / hw) ** 2 <= 1.0)
            lo, hi = (mid, hi) if inside else (lo, mid)
        return min(best, lo)

    def inner(th):
        du, dv = math.cos(th), math.sin(th)
        rs = []
        if abs(du) > 1e-6:
            rs.append(((hole_u[1] if du > 0 else hole_u[0]) - uc0) / du)
        if abs(dv) > 1e-6:
            rs.append(hole_v / abs(dv))
        return min(r for r in rs if r > 0)

    N = 64
    bp = bmesh.new()
    zt = m.t_h + 0.41
    ring_o, ring_i = [], []
    for k in range(N):
        th = 2 * math.pi * k / N
        du, dv = math.cos(th), math.sin(th)
        ro, ri = outer(th), inner(th)
        ring_o.append(bp.verts.new(m.P(zt, uc0 + ro * du, ro * dv)))
        ring_i.append(bp.verts.new(m.P(zt, uc0 + ri * du, ri * dv)))
    for k in range(N):
        bp.faces.new([ring_i[k], ring_o[k], ring_o[(k + 1) % N], ring_i[(k + 1) % N]])
    ext = bmesh.ops.extrude_face_region(bp, geom=list(bp.faces))
    bmesh.ops.translate(bp, verts=[e for e in ext["geom"] if isinstance(e, bmesh.types.BMVert)], vec=-m.A * 0.10)
    bmesh.ops.recalc_face_normals(bp, faces=bp.faces)
    me_tmp = bpy.data.meshes.new("_tmp_top")
    bp.to_mesh(me_tmp)
    bp.free()
    bk.from_mesh(me_tmp)
    bpy.data.meshes.remove(me_tmp)
    # kıç kenar korkuluğu (top rail)
    ua = -0.45 * m.top_l + 0.06
    for v in np.linspace(-m.top_w / 2 + 0.1, m.top_w / 2 - 0.1, 7):
        obox(bk, m.P(m.t_h + 0.85, ua, v), m.F, Y, m.A, 0.03, 0.03, 0.45)
    obox(bk, m.P(m.t_h + 1.32, ua, 0.0), m.F, Y, m.A, 0.05, m.top_w / 2 - 0.05, 0.04)
    # başlık kepi (cap)
    obox(bk, m.P(m.t_cap + 0.14, m.ft / 2, 0.0), m.F, Y, m.A, m.ft / 2 + m.Dt * 0.8, m.D * 0.55, 0.14)
    # gabya ve babafingo
    spar(bw, m.P(m.t_t0, m.ft), m.P(m.t_th, m.ft), m.Dt / 2, m.Dt * 0.38, seg=16)
    obox(bw, m.P((m.t_th + m.t_t1) / 2, m.ft), m.F, Y, m.A, m.Dt * 0.38, m.Dt * 0.38, m.hd_t / 2)
    obox(bk, m.P(m.t_t1 + 0.08, (m.ft + m.fg) / 2), m.F, Y, m.A, (m.fg - m.ft) / 2 + m.Dg, m.Dt * 0.5, 0.08)
    cw = m.top_w * 0.55
    for sgn in (1, -1):
        obox(bk, m.P(m.t_th + 0.06, m.ft, sgn * (m.Dt * 0.4 + 0.06)), m.F, Y, m.A, 0.5, 0.05, 0.06)
    for u in (-0.25, 0.25):
        obox(bk, m.P(m.t_th + 0.16, m.ft + u, 0.0), m.F, Y, m.A, 0.05, cw / 2, 0.04)
    spar(bw, m.P(m.t_g0, m.fg), m.P(m.t_g1, m.fg), m.Dg / 2, m.Dg * 0.25, seg=12)
    P5.lathe(bw, [(0.0, 0.0), (m.Dg * 0.6, 0.0), (m.Dg * 0.6, 0.08), (0.0, 0.14)], 12,
             P5.axis_matrix(m.P(m.t_g1, m.fg), m.A))                     # topuz (truck)
    # direk yakası (mast coat) üst güvertede
    P5.lathe(bw, [(m.D / 2 + 0.18, 0.02), (m.D / 2 + 0.02, 0.20), (m.D / 2, 0.20), (m.D / 2, 0.0)], 20,
             P5.axis_matrix(m.P(0.08), m.A))
    origin = W(m.base)
    ob = finish(f"MOD_RIG_MAST_{m.name}_A", [(bw, M["spar"]), (bi, M["iron"]), (bk, M["black"])], col, bevel=0.01, origin=origin)
    ob["module_family"] = "RigSet"
    ob["socket"] = f"SOCKET_MAST_{m.name}"
    ob["rake_deg"] = round(math.degrees(m.rake), 2)
    return ob


# --- Serenler ------------------------------------------------------------------------
def yard_mesh(name, length, dia, M, footrope=True):
    """Yerel: Y boyunca seren, X ileri, Z direk ekseni; orijin askı (slings). Tasarım → dünya ölçeği."""
    bw, bi, bt = bmesh.new(), bmesh.new(), bmesh.new()
    half = length / 2
    arm = 0.12 * half
    prof = [(0.0, -half), (dia * 0.22, -half), (dia * 0.22, -half + arm), (dia * 0.30, -half + arm + 0.02),
            (dia * 0.42, -half * 0.6), (dia * 0.5, -half * 0.12), (dia * 0.5, half * 0.12), (dia * 0.42, half * 0.6),
            (dia * 0.30, half - arm - 0.02), (dia * 0.22, half - arm), (dia * 0.22, half), (0.0, half)]
    P5.lathe(bw, prof, 14, Matrix.Rotation(math.radians(-90), 4, "X"))
    for sgn in (1, -1):                                    # askı kuşakları ve yard-arm çemberleri
        for yy in (sgn * half * 0.1, sgn * (half - arm)):
            r = dia * 0.5 + 0.012 if abs(yy) < half * 0.2 else dia * 0.24
            P5.lathe(bi, [(r - 0.015, 0.0), (r, 0.0), (r, 0.05), (r - 0.015, 0.05)], 12,
                     P5.axis_matrix(Vector((0, yy, 0)), Vector((0, 1, 0))))
        if footrope:                                       # basamak halatı: askıdan yard-arm'a, 0,9 m aşağıda sarkık
            pts = []
            for k in range(9):
                t = k / 8
                yy = sgn * (0.35 + t * (half - arm - 0.35))
                pts.append(Vector((0.18, yy, -0.80 - 0.10 * math.sin(math.pi * t))))
            tube(bt, pts, R_FOOT, seg=5)
            for t in (0.3, 0.65):                          # üzengiler (stirrups)
                yy = sgn * (0.35 + t * (half - arm - 0.35))
                tube(bt, [Vector((0.0, yy, 0.0)), Vector((0.18, yy, -0.80 - 0.10 * math.sin(math.pi * t)))], R_FOOT * 0.8, seg=4)
    parts = [(bw, M["spar"]), (bi, M["iron"]), (bt, M["rope"])]
    merged = bmesh.new()
    mats = []
    for idx, (b, mat) in enumerate(parts):
        b.transform(Matrix.Scale(K, 4))
        me = bpy.data.meshes.new("_tmp")
        bmesh.ops.recalc_face_normals(b, faces=b.faces)
        b.to_mesh(me)
        b.free()
        me.polygons.foreach_set("material_index", [idx] * len(me.polygons))
        merged.from_mesh(me)
        bpy.data.meshes.remove(me)
        mats.append(mat)
    me = bpy.data.meshes.new(name)
    merged.to_mesh(me)
    merged.free()
    for mt in mats:
        me.materials.append(mt)
    me.set_sharp_from_angle(angle=math.radians(35))
    tmp = bpy.data.objects.new("_tmp_uv", me)
    H.build_uv_fallback(tmp)
    bpy.data.objects.remove(tmp)
    return me


def build_yards(m, col, col_s, M):
    Lc = YARD_MAIN * YARD_K[m.name]
    Lts = 0.72 * Lc
    Ltg = 0.66 * Lts
    specs = [("COURSE", Lc, m.t_h - 1.3, m.D / 2), ("TOPSAIL", Lts, m.t_th - 0.9, m.ft + m.Dt / 2),
             ("TOPGALLANT", Ltg, m.t_g1 - 0.9, m.fg + m.Dg / 2)]
    obs, socks, info = [], [], []
    for key, length, t, f0 in specs:
        dia = 0.0208 * length                          # 3/4 inç / yarda (TAHMİN)
        pivot = m.P(t, f0 + dia / 2 + 0.05)
        name = f"MOD_RIG_YARD_{m.name}_{key}_A"
        me = yard_mesh(name, length, dia, M, footrope=True)
        ob = bpy.data.objects.new(name, me)
        col.objects.link(ob)
        ob.location = W(pivot)
        ob.rotation_euler = (0.0, -m.rake, 0.0)
        ob["module_family"] = "RigSet"
        ob["pivot"] = "askı; yerel Z (direk ekseni) etrafında brasya dönüşü"
        ob["brace_limit_deg"] = 35.0                       # TAHMİN
        ob["walkable"] = "footrope"
        obs.append(ob)
        sname = f"SOCKET_YARD_{m.name}_{key}"
        e = P13.set_socket(sname, W(pivot), col_s, shape="ARROWS", size=0.4, rot=(0.0, -m.rake, 0.0),
                           module_family="RigSet", yard=name, sail_slot=f"SLOT_SAIL_{m.name}_{key}")
        socks.append(e.name)
        for sgn, tag in ((1, "S"), (-1, "P")):
            p = pivot + Y * sgn * (length / 2 - 0.12 * length / 2)
            e = P13.set_socket(f"SOCK_YARDARM_{m.name}_{key}_{tag}", W(p), col_s, shape="SPHERE", size=0.15,
                               link="yard_walk", pair=f"SOCK_YARDARM_{m.name}_{key}", yard=name)
            socks.append(e.name)
        info.append(dict(name=name, length=length, dia=dia, pivot=pivot, key=key))
    if m.name == "MIZZEN":                                   # randa yelkeni: gaf ve bumba
        t_gaff = m.t_h - 0.7
        gl, bl = 0.55 * Lc, 0.90 * Lc
        zb = P5.zpd(0.02) + 2.35
        t_boom = (zb - m.base.z) / math.cos(m.rake)
        for key, t, length, ang in (("GAFF", t_gaff, gl, math.radians(40)), ("BOOM", t_boom, bl, math.radians(3))):
            dia = 0.0208 * length
            d = Vector((-math.cos(ang), 0.0, math.sin(ang)))
            p0 = m.P(t, -m.D / 2 - 0.05)
            bw, bj = bmesh.new(), bmesh.new()
            spar(bw, p0, p0 + d * length, dia / 2, dia * 0.3, seg=12)
            for sgn in (1, -1):                              # çatal (jaws)
                obox(bj, m.P(t, -m.D / 2 + 0.05, sgn * (m.D / 2 + 0.05)), m.F, Y, m.A, m.D * 0.6, 0.04, 0.10)
            ob = finish(f"MOD_RIG_{key}_MIZZEN_A", [(bw, M["spar"]), (bj, M["black"])], col, origin=W(p0))
            ob["module_family"] = "RigSet"
            ob["pivot"] = "çatal; direk ekseni etrafında dönüş"
            obs.append(ob)
            e = P13.set_socket(f"SOCKET_{key}_MIZZEN", W(p0), col_s, shape="ARROWS", size=0.4, module_family="RigSet",
                               sail_slot="SLOT_SAIL_MIZZEN_SPANKER")
            socks.append(e.name)
            info.append(dict(name=ob.name, length=length, dia=dia, pivot=p0, key=key, dir=d))
    return obs, socks, info


# --- Cıvadıra ------------------------------------------------------------------------
def build_bowsprit(col, col_s, M, fore):
    s_b = 0.992
    zt = H.top_z(s_b)
    xs = P13.x_at(s_b, zt)
    L_bs = 0.6 * L_MAIN
    D_bs = fore.D * 0.95
    d = Vector((math.cos(BS_STEEVE), 0.0, math.sin(BS_STEEVE)))
    over = Vector((xs, 0.0, zt + D_bs / 2 + 0.05))            # pruva başı üstünden geçer
    heel = over - d * (0.36 * L_BS_frac() * L_bs)
    end = heel + d * L_bs
    bw, bk = bmesh.new(), bmesh.new()
    spar(bw, heel, end, D_bs / 2, D_bs * 0.32, seg=18, rmid=D_bs * 0.5)
    L_jb = 0.5 * L_bs
    Dj = 0.022 * L_jb
    up = Vector((-math.sin(BS_STEEVE), 0.0, math.cos(BS_STEEVE)))
    j0 = end - d * (0.35 * L_jb) + up * (D_bs * 0.32 + Dj / 2 + 0.02)
    spar(bw, j0, j0 + d * L_jb, Dj / 2, Dj * 0.3, seg=12)
    obox(bk, end + up * (Dj / 2), d, Y, up, 0.12, D_bs * 0.45, D_bs * 0.6)     # cıvadıra kepi
    for k in range(5):                                          # demir çemberler
        c = heel + d * (L_bs * (0.45 + 0.1 * k))
        P5.lathe(bk, [(D_bs * 0.47, 0.0), (D_bs * 0.5, 0.0), (D_bs * 0.5, 0.05), (D_bs * 0.47, 0.05)], 16, P5.axis_matrix(c, d))
    ob = finish("MOD_RIG_BOWSPRIT_A", [(bw, M["spar"]), (bk, M["black"])], col, bevel=0.01, origin=W(heel))
    ob["module_family"] = "RigSet"
    ob["steeve_deg"] = round(math.degrees(BS_STEEVE), 1)
    ob["walkable"] = "balance"
    e = P13.set_socket("SOCKET_BOWSPRIT", W(heel), col_s, shape="ARROWS", size=0.5, module_family="RigSet")
    return ob, dict(heel=heel, end=end, d=d, D=D_bs, jb_end=j0 + d * L_jb, over=over, L=L_bs), e.name


def L_BS_frac():
    return 1.0


# --- Kuşak tahtaları (channels), bigotalar, çarmıhlar, iskalarya -----------------------
def channel_points(m):
    """Bordadaki alt bigota noktaları (tasarım): çarmıhlar + patrisalar."""
    s = m.s()
    z_ch = min(H.top_z(P13.s_of_x(m.base.x + 0.3 - k * SHROUD_STEP, P13.zu)) for k in range(m.n_sh + m.n_bs)) - 0.35
    xs = [m.base.x + 0.3 - k * SHROUD_STEP for k in range(m.n_sh + m.n_bs)]
    out = []
    for x in xs:
        ss = P13.s_of_x(x, lambda s_: z_ch)
        y = H.hull_point(ss, z_ch)[1]
        out.append((x, y, z_ch))
    return out, z_ch


def ratlines(bm, lines, z0, z1):
    """lines: [(alt, üst)] aynı borda çarmıhları (kıçtan başa). z0..z1 arasında her RAT_STEP'te bir sıra."""
    n = 0
    for z in np.arange(z0, z1, RAT_STEP):
        pts = []
        for a, b in lines:
            t = (z - a.z) / (b.z - a.z)
            if not 0.0 <= t <= 1.0:
                pts = []
                break
            pts.append(a.lerp(b, t))
        if len(pts) >= 2:
            tube(bm, pts, R_RAT, seg=4)
            n += 1
    return n


def build_standing(m, col, M, col_s, climb):
    br, bd, bi, bc = bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new()   # halat, bigota, demir, kuşak tahtası
    pts, z_ch = channel_points(m)
    W_ch = 0.45
    n_rat = 0
    for sgn, tag in ((1, "S"), (-1, "P")):
        # kuşak tahtası
        x0, x1 = pts[-1][0] - 0.35, pts[0][0] + 0.35
        ys = [p[1] for p in pts]
        ymin = min(ys) - 0.02
        P5.aabox(bc, x0, x1, *sorted((sgn * ymin, sgn * (max(ys) + W_ch))), z_ch - 0.10, z_ch)
        lower = []
        for k, (x, y, z) in enumerate(pts):
            yo = sgn * (y + W_ch - 0.06)
            lo = Vector((x, yo, z + 0.16))
            hi = lo + Vector((0, 0, 0.75))
            n_dir = Vector((0, 0, 1))
            disc(bd, lo, Vector((0, sgn, 0)), 0.13, 0.08)
            disc(bd, hi, Vector((0, sgn, 0)), 0.12, 0.08)
            for dx in (-0.06, 0.0, 0.06):                     # savlo (lanyard)
                tube(br, [lo + Vector((dx, 0, 0.1)), hi + Vector((dx, 0, -0.1))], 0.008, seg=4)
            P5.aabox(bi, x - 0.03, x + 0.03, *sorted((sgn * (yo - 0.03), sgn * (yo + 0.03))), z - 0.40, z + 0.10)   # zincir levhası
            lower.append((k, hi))
        # alt çarmıhlar → direk başı (çanaklık altı)
        lines = []
        for k, hi in lower[:m.n_sh]:
            top = m.P(m.t_h - 0.25, -0.05 * k, sgn * (m.D / 2 + 0.05))
            tube(br, [hi + Vector((0, 0, 0.08)), top], R_SHROUD, seg=6)
            lines.append((hi + Vector((0, 0, 0.08)), top))
        z0 = lines[0][0].z + 0.45
        z1 = min(l[1].z for l in lines) - 1.6
        n_rat += ratlines(br, lines, z0, z1)
        climb.append((f"{m.name}_{tag}_LOWER", [lines[0][0], lines[-1][0], lines[0][1], lines[-1][1]],
                      Vector(((lines[0][0].x + lines[-1][0].x) / 2, lines[0][0].y, lines[0][0].z)),
                      m.P(m.t_h + 0.45, 0.0, sgn * (m.top_w / 2 - 0.3))))
        # patrisalar (gabya backstay) → gabya çanaklığı
        for k, hi in lower[m.n_sh:]:
            tube(br, [hi + Vector((0, 0, 0.08)), m.P(m.t_th - 0.15, m.ft, sgn * (m.Dt / 2 + 0.04))], R_SHROUD * 0.9, seg=6)
        # futtock çarmıhları (çanaklık kenarı → alt direk) ve gabya çarmıhları (çanaklık → gabya çanaklığı)
        n_top = 4 if m.name != "MIZZEN" else 3
        tl = []
        for k in range(n_top):
            u = -0.25 * m.top_l + k * (0.5 * m.top_l / max(n_top - 1, 1))
            rim = m.P(m.t_h + 0.40, u, sgn * (m.top_w / 2 - 0.08))
            disc(bd, rim + m.A * 0.18, Y * sgn, 0.08, 0.06)
            tube(br, [rim, m.P(m.t_h - 1.4, u * 0.3, sgn * (m.D / 2 + 0.03))], R_SHROUD * 0.8, seg=5)   # futtock
            hi = rim + m.A * 0.30
            top = m.P(m.t_th - 0.15, m.ft, sgn * (m.Dt / 2 + 0.04))
            tube(br, [hi, top], R_SHROUD * 0.75, seg=5)
            tl.append((hi, top))
        tl.sort(key=lambda l: l[0].x)
        n_rat += ratlines(br, tl, tl[0][0].z + 0.35, min(l[1].z for l in tl) - 1.0)
        climb.append((f"{m.name}_{tag}_TOPMAST", [tl[0][0], tl[-1][0], tl[0][1], tl[-1][1]],
                      m.P(m.t_h + 0.45, 0.0, sgn * (m.top_w / 2 - 0.3)), m.P(m.t_th + 0.25, m.ft, sgn * 0.4)))
        # babafingo çarmıhları (gabya kıstağı → babafingo başı)
        cw = m.top_w * 0.55
        for u in (-0.25, 0.25):
            tube(br, [m.P(m.t_th + 0.2, m.ft + u, sgn * cw / 2), m.P(m.t_g1 - 0.6, m.fg, sgn * (m.Dg / 2 + 0.02))], R_SHROUD * 0.6, seg=5)
    ob = finish(f"MOD_RIG_STANDING_{m.name}_A", [(br, M["rope"]), (bd, M["timber"]), (bi, M["iron"]), (bc, M["hull"])], col,
                origin=W(m.base))
    ob["module_family"] = "RigSet"
    ob["climbable"] = "iskalarya (ratlines)"
    return ob, dict(z_ch=z_ch, channel_x=(pts[-1][0], pts[0][0]), ratline_rows=n_rat)


def build_stays(masts, bs, col, M):
    br = bmesh.new()
    f, mn, mz = masts["FORE"], masts["MAIN"], masts["MIZZEN"]
    stays = [
        ("fore_stay", f.P(f.t_h - 0.1, f.D / 2), bs["heel"] + bs["d"] * (0.55 * bs["L"]), R_STAY),
        ("fore_topmast_stay", f.P(f.t_th - 0.1, f.ft + f.Dt / 2), bs["end"], R_STAY * 0.7),
        ("fore_tg_stay", f.P(f.t_g1 - 0.6, f.fg + f.Dg / 2), bs["jb_end"], R_STAY * 0.5),
        ("main_stay", mn.P(mn.t_h - 0.1, mn.D / 2), f.P(0.6, f.D / 2 + 0.1), R_STAY * 1.1),
        ("main_topmast_stay", mn.P(mn.t_th - 0.1, mn.ft + mn.Dt / 2), f.P(f.t_h + 0.3, 0.2), R_STAY * 0.7),
        ("main_tg_stay", mn.P(mn.t_g1 - 0.6, mn.fg + mn.Dg / 2), f.P(f.t_th + 0.1, f.ft), R_STAY * 0.5),
        ("mizzen_stay", mz.P(mz.t_h - 0.1, mz.D / 2), mn.P(2.2, -mn.D / 2 - 0.05), R_STAY * 0.8),
        ("mizzen_topmast_stay", mz.P(mz.t_th - 0.1, mz.ft + mz.Dt / 2), mn.P(mn.t_h + 0.3, -0.3), R_STAY * 0.6),
    ]
    for _, a, b, r in stays:
        mid = a.lerp(b, 0.5) - Vector((0, 0, 0.012 * (a - b).length))   # hafif sehim
        tube(br, [a, a.lerp(mid, 0.5), mid, mid.lerp(b, 0.5), b], r, seg=8)
    ob = finish("MOD_RIG_STAYS_A", [(br, M["rope"])], col)
    ob["module_family"] = "RigSet"
    return ob, [s[0] for s in stays]


# --- Çarpışma, tırmanma soketleri --------------------------------------------------------
def build_collision(col, masts, yards, bs, climb, chans):
    parts = []

    def prism(p0, p1, r, n=8):
        d = (p1 - p0).normalized()
        u = d.cross(Vector((0, 1, 0))).normalized() if abs(d.y) < 0.9 else d.cross(Vector((1, 0, 0))).normalized()
        v = d.cross(u)
        pts = []
        for p in (p0, p1):
            for k in range(n):
                a = 2 * math.pi * k / n
                pts.append(p + (u * math.cos(a) + v * math.sin(a)) * r)
        return pts

    for m in masts.values():
        parts.append((prism(m.P(0.0), m.P(m.t_cap), m.D / 2), "mast", f"MOD_RIG_MAST_{m.name}_A"))
        parts.append((prism(m.P(m.t_t0, m.ft), m.P(m.t_t1, m.ft), m.Dt / 2, 6), "mast", f"MOD_RIG_MAST_{m.name}_A"))
        parts.append((prism(m.P(m.t_g0, m.fg), m.P(m.t_g1, m.fg), m.Dg / 2 + 0.02, 6), "mast", f"MOD_RIG_MAST_{m.name}_A"))
        pts = []
        for u in (-0.45 * m.top_l, 0.0, 0.3 * m.top_l, 0.55 * m.top_l):
            half = m.top_w / 2 if u <= 0 else m.top_w / 2 * math.sqrt(max(1 - (u / (0.55 * m.top_l)) ** 2, 0.05))
            for v in (-half, half):
                for dz in (0.28, 0.42):
                    pts.append(m.P(m.t_h + dz, u, v))
        parts.append((pts, "top_platform", f"MOD_RIG_MAST_{m.name}_A"))
        cw = m.top_w * 0.55
        parts.append(([m.P(m.t_th + dz, m.ft + du, dv) for dz in (0.1, 0.22) for du in (-0.3, 0.3) for dv in (-cw / 2, cw / 2)],
                      "crosstree", f"MOD_RIG_MAST_{m.name}_A"))
    for y in yards:
        if y["key"] in ("GAFF", "BOOM"):
            p0 = y["pivot"]
            parts.append((prism(p0, p0 + y["dir"] * y["length"], y["dia"] / 2 + 0.03, 6), "yard", y["name"]))
            continue
        c, half = y["pivot"], y["length"] / 2
        parts.append(([c + Vector((dx, dy, dz)) for dx in (-y["dia"] / 2, y["dia"] / 2) for dy in (-half, half)
                       for dz in (-y["dia"] / 2, y["dia"] / 2)], "yard", y["name"]))
    parts.append((prism(bs["heel"], bs["end"], bs["D"] / 2 + 0.02), "bowsprit", "MOD_RIG_BOWSPRIT_A"))
    for name, quad, _, _ in climb:
        a, b, c, d = quad
        n = (b - a).cross(c - a).normalized()
        parts.append(([p + n * s for p in quad for s in (-0.06, 0.06)], "climb_shrouds", name))
    for mname, (x0, x1, z, ylist) in chans.items():
        for sgn in (1, -1):
            parts.append(([Vector((x, sgn * y, zz)) for x in (x0, x1) for y in ylist for zz in (z - 0.1, z)], "channel",
                          f"MOD_RIG_STANDING_{mname}_A"))
    made = []
    for k, (pts, purpose, owner) in enumerate(parts):
        o = C3.convex(f"_tmp_rig_{k}", [W(p) for p in pts], col, purpose)
        o["owner_mesh"] = owner
        made.append((o, owner))
    counts = {}
    for o, owner in made:
        i = counts.get(owner, 0)
        counts[owner] = i + 1
        o.name = f"UCX_{owner}_{i:02d}"
        o.data.name = o.name
    return [o for o, _ in made]


def climb_sockets(col_s, climb):
    names = []
    for name, _, bot, top in climb:
        for end, p in (("BOTTOM", bot), ("TOP", top)):
            n = f"SOCK_CLIMB_{name}_{end}"
            P13.set_socket(n, W(p), col_s, shape="SPHERE", size=0.2, link="climb", pair=f"SOCK_CLIMB_{name}")
            names.append(n)
    return names


# --- Malzemeler --------------------------------------------------------------------------
def materials():
    M = P5.ensure_materials()
    if "MAT_Spar_Pine" not in bpy.data.materials:
        H.plank_material("MAT_Spar_Pine", (0.42, 0.30, 0.17), (0.22, 0.15, 0.08), plank_w=0.9, rough=0.55, seam=0.001, bump=0.08)
    if "MAT_Rope_Tarred" not in bpy.data.materials:
        H.principled("MAT_Rope_Tarred", (0.035, 0.028, 0.02), rough=0.85)
    if "MAT_Paint_Black" not in bpy.data.materials:
        H.principled("MAT_Paint_Black", (0.018, 0.017, 0.016), rough=0.6)
    M["spar"] = bpy.data.materials["MAT_Spar_Pine"]
    M["rope"] = bpy.data.materials["MAT_Rope_Tarred"]
    M["black"] = bpy.data.materials["MAT_Paint_Black"]
    return M


def render(sc):
    H.setup_render(sc, fast=True)
    out = ROOT / "renders" / VER
    out.mkdir(parents=True, exist_ok=True)
    V = Vector
    D = V((0, 0, DWL))
    views = [
        ("iskele_profil", V((1.5, -110, 14)) * K + D, V((1.5, 0, 14)) * K + D, None, 62),
        ("bas", V((95, 0, 14)) * K + D, V((0, 0, 14)) * K + D, None, 40),
        ("bas_omzu", V((48, 38, 22)) * K + D, V((0, 0, 12)) * K + D, 32, None),
        ("kic_omzu", V((-46, -34, 20)) * K + D, V((0, 0, 11)) * K + D, 32, None),
        ("ana_canaklik", V((4.5, 6.5, 22.5)) * K + D, V((1.0, 0, 17.5)) * K + D, 28, None),
        ("carmih_yakin", V((-2.0, 9.0, 5.5)) * K + D, V((0.0, 4.5, 6.5)) * K + D, 32, None),
        ("guverte_yukari", V((-14.0, 2.5, 7.5)) * K + D, V((5.0, 0, 16.0)) * K + D, 20, None),
    ]
    for name, loc, tgt, lens, osc in views:
        cam = H.camera(sc, f"CAM15_{name}", loc, tgt, ortho=osc * K if osc else None, lens=lens or 50)
        sc.camera = cam
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
    M = materials()
    C = {c.name: c for c in bpy.data.collections}
    rig, socks, ucx_col = C["20_MODULES_RIG"], C["30_SOCKETS"], C["40_COLLISION"]
    masts = {n: Mast(n) for n in ("FORE", "MAIN", "MIZZEN")}
    obs, yards, climb, info, sock_names = [], [], [], {}, []
    chans = {}
    for m in masts.values():
        obs.append(build_mast(m, rig, M))
        yo, ys, yi = build_yards(m, rig, socks, M)
        obs += yo
        yards += yi
        sock_names += ys
        so, si = build_standing(m, rig, M, socks, climb)
        obs.append(so)
        pts, z_ch = channel_points(m)
        chans[m.name] = (pts[-1][0] - 0.35, pts[0][0] + 0.35, z_ch, (min(p[1] for p in pts) - 0.02, max(p[1] for p in pts) + 0.45))
        info[m.name] = dict(lower_mast_design=round(m.Lm, 2), lower_mast_world=round(m.Lm * K, 2), dia_world=round(m.D * K, 3),
                            topmast_world=round(m.Lt * K, 2), topgallant_world=round(m.Lg * K, 2),
                            truck_z_world=round(W(m.P(m.t_g1, m.fg)).z, 2), top_z_world=round(W(m.P(m.t_h + 0.4)).z, 2),
                            top_w_world=round(m.top_w * K, 2), rake_deg=MASTS[m.name][2], **si)
    bso, bs, bsock = build_bowsprit(rig, socks, M, masts["FORE"])
    obs.append(bso)
    sock_names.append(bsock)
    st, stays = build_stays(masts, bs, rig, M)
    obs.append(st)
    sock_names += climb_sockets(socks, climb)
    ucx = build_collision(ucx_col, masts, yards, bs, climb, chans)
    # filika soketi ana direkle çakışıyordu (v001'den beri): ana ve pruva direkleri arasına, ızgara üstü kızaklara
    boat = bpy.data.objects["SOCKET_BOAT_PRIMARY"]
    old_boat = [round(v, 3) for v in boat.location]
    xb = (masts["MAIN"].base.x + masts["FORE"].base.x) / 2
    boat.location = W((xb, 0.0, P13.zu(P13.s_of_x(xb, P13.zu)) + 2.00))
    boat["note"] = ("v015: ana direkle çakışma giderildi; kızaklar (skids) güverteden 2,2 m (dünya) yüksekte — "
                    "altından yürünür, baş ambar merdiveni çıkışı açık kalır (TAHMİN)")
    for o in bpy.data.objects:
        if o.type == "EMPTY" and o.name.startswith(("SOCKET_MAST_", "SOCKET_RIG_PRIMARY", "SOCKET_BOAT")):
            o["manifest_version"] = MANIFEST_VERSION
    bpy.data.objects["SOCKET_RIG_PRIMARY"]["rig_profile"] = "Rig.FullShip"
    bpy.data.objects["SOCKET_RIG_PRIMARY"]["mast_rig_family"] = "OF1780_FULLSHIP_A"

    bpy.ops.wm.save_as_mainfile(filepath=str(out), compress=True)
    H.VERSION = VER
    ap = ROOT / "reports" / f"scene_audit_{VER}.json"
    rep = H.audit(sc, ap)
    dg = bpy.context.evaluated_depsgraph_get()
    tri = {}
    for o in obs:
        me = o.evaluated_get(dg).to_mesh()
        me.calc_loop_triangles()
        tri[o.name] = len(me.loop_triangles)
        o.evaluated_get(dg).to_mesh_clear()
    rep["rigset_v015"] = {
        "masts": info,
        "yards": {y["name"]: {"length_world": round(y["length"] * K, 2), "dia_world": round(y["dia"] * K, 3)} for y in yards},
        "bowsprit": {"length_world": round(bs["L"] * K, 2), "steeve_deg": round(math.degrees(BS_STEEVE), 1),
                     "end_world": [round(v, 2) for v in W(bs["jb_end"])]},
        "stays": stays, "climb_routes": [c[0] for c in climb], "ucx_added": len(ucx),
        "tris": tri, "tris_total": sum(tri.values()),
        "boat_socket": {"from": old_boat, "to": [round(v, 3) for v in boat.location]},
        "sources": "oranlar TAHMİN (dönem kuralları; Lees 'Masting and Rigging of English Ships of War' ile doğrulanmalı)",
    }
    rep["pass"] = {"name": "pass_v015_rigset", "source": f"Blender/versions/{SHIP}_{SRC_VER}.blend",
                   "pass_changes": {"modules_added": [o.name for o in obs], "sockets_added": len(sock_names), "ucx_added": len(ucx)},
                   "manifest_version": MANIFEST_VERSION, "geometry_changed": "yalnız RigSet modülleri; gövde değişmedi"}
    ap.write_text(json.dumps(rep, indent=2, ensure_ascii=False), encoding="utf-8")
    r = rep["rigset_v015"]
    print("MASTS", json.dumps(r["masts"], ensure_ascii=False))
    print("TRIS", r["tris_total"], "UCX", len(ucx), "SOCKS", len(sock_names), "BOUNDS", rep["checks"]["bounds_m"])
    if "--no-render" not in sys.argv:
        render(sc)


if __name__ == "__main__":
    main()
