"""Pass v005 — yüksek kıç (kıç üstü güverte), merdivenler, dümen, kıç galerisi ve fener (v004 üzerine).

Çalıştırma (depo kökünden):
    python3 OTTOMAN_FRIGATE_1780_ISTANBUL/scripts/pass_v005_stern.py [--no-render]

Kullanıcı isteği (2026-09-25, görsel referansla):
  "Kıç kısmını bu görseldeki tarzda yap: normalden yüksek ve merdivenle çıkılabilir bir alan;
   orada şimdilik dümen olsun."
Yorum ve kararlar (oynanış/stil; 18. yy frigate'inde kıç üstü güverte tipik değil — hibrit):
  - Kıç üstü güverte (poop): kıç kasarası güvertesinin POOP_H = 2,0 m üstünde (kasara kararıyla aynı).
    Altında gezilebilir kaptan kamarası; ön bölmede kapı.
  - İki merdiven (iskele/sancak), kapının iki yanında, kıça doğru yükselir; eğim ≤ 40° (UE yürünebilir).
  - Kenarlarda torna balüsterli korkuluk; kıç aynası üstünde güneş motifli oyma tepelik ve kıç feneri.
  - Kıç aynasında 5 kafesli pencere (gerçek açıklık), iki yanda kafesli yan galeriler.
  - Dümen dolabı (MOD_HELM_WHEEL_A) kıç üstü güvertede; kaptan istasyonu dümenin arkasında.
  - Merdivenlere yer açmak için kıç kasarası topları ileri alındı: x = -12,6/-10,2 → -10,3/-7,9.
Gövde kabuğu yeniden üretilir (üst kenar kıçta 1,2 m yükselir). Mevcut yükseklikler altında
kesit formülü birebir aynıdır; yalnız yukarı uzatma eklenir.
"""

import importlib.util
import json
import math
import sys
import uuid
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


H = _load("hull_v001", "build_hull_v001.py")
C3 = _load("pass_v003", "pass_v003_collision.py")
C3.H = H  # çarpışma üreticileri yamalı gövde fonksiyonlarını kullansın
P4 = _load("pass_v004", "pass_v004_gameplay_sockets.py")

SRC_VER, VER = "v004", "v005"
ROOT, SHIP = H.ROOT, H.SHIP_ID
NS_UUID = P4.NS_UUID
MANIFEST_VERSION = 3  # v004 = 2; QD top soketleri ve istasyonlar taşındı

POOP_H = 2.00         # kıç üstü güverte, kıç kasarası güvertesinin üstünde (kullanıcı: 2 m yeterli)
RIM_H = 0.30          # güverte üstünde dolu küpeşte; üzerinde balüster korkuluk
RAIL_H = 0.70         # balüster boyu
X_FRONT = -13.90      # kıç üstü güverte ön bölmesinin ön yüzü
DOOR_W, DOOR_H = 0.90, 1.85
STAIR_Y = (0.85, 1.75)  # merdiven iç/dış kenarı (|y|)
STAIR_RUN = 2.40
STAIR_STEPS = 10
QD_PORT_X = (-10.30, -7.90)
TH = math.atan(0.22)  # kıç aynası eğimi (stern_x: -0,22 m/m)

ORIG_TOP = H.top_z


# --- Yamalı gövde fonksiyonları ------------------------------------------------
def x_at(s, z):
    return H.stern_x(z) + s * (H.bow_x(z) - H.stern_x(z))


def s_of_x(x, zfn):
    lo, hi = 0.0, 0.7
    for _ in range(60):
        mid = (lo + hi) / 2
        if x_at(mid, zfn(mid)) < x:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def zqd(s):
    return H.deck_z(s) + H.QD_H


def zpd(s):
    return H.deck_z(s) + H.QD_H + POOP_H


S_POOP = s_of_x(X_FRONT, lambda s: zqd(s) + 1.0)
RISE = (H.QD_H + POOP_H + RIM_H) - (H.QD_H + 1.10)


def poop_w(s):
    return 1.0 - H.smooth(S_POOP + 0.01, S_POOP + 0.05, s)


def top_v005(s):
    return ORIG_TOP(s) + RISE * poop_w(s)


def half_breadth_v005(s, z):
    """v001 kesit formülü, eski üst kenara göre; onun üstünde hafif içe çekilen uzatma."""
    bmax = H.B / 2 * H.plan(s)
    if z <= H.ZM:
        t = min((H.ZM - z) / (H.ZM - H.ZK), 1.0)
        n = H.fullness(s)
        y = bmax * max(1.0 - t ** n, 0.0) ** (1.0 / n)
    else:
        top_o = ORIG_TOP(s)
        t = min((z - H.ZM) / (top_o - H.ZM), 1.0)
        y = bmax * (1.0 - H.TUMBLE * t ** 1.6)
        if z > top_o:
            y -= 0.04 * (z - top_o)
    return max(y * H.stern_close(s, z), 0.0)


def port_positions_v005():
    ports = []
    for k, x in enumerate(np.linspace(-13.4, 12.6, H.GUNS_PER_SIDE)):
        s = (x - H.stern_x(2)) / (H.bow_x(2) - H.stern_x(2))
        ports.append(("MAIN", k + 1, x, s, H.deck_z(s) + H.PORT_SILL + H.PORT_H / 2))
    for k, x in enumerate(QD_PORT_X):
        s = (x - H.stern_x(4)) / (H.bow_x(4) - H.stern_x(4))
        ports.append(("QD", k + 1, x, s, H.deck_z(s) + H.QD_H + 0.40 + 0.22))
    return ports


J_B = 25  # kırmızı kuşak sınırına (batarya güvertesi + 1,30 m) denk gelen gövde satırı


def row_z_v005(s, t, top):
    """Satır J_B tam kuşak sınırında: malzeme sınırı testere dişi yerine düz çizgi olur."""
    zb = H.deck_z(s) + 1.30
    tb = J_B / H.NZ
    if t <= tb:
        f = (0.5 - 0.5 * math.cos(math.pi * t)) ** 0.9 / (0.5 - 0.5 * math.cos(math.pi * tb)) ** 0.9
        return H.ZK + (zb - H.ZK) * f
    return zb + (top - zb) * (t - tb) / (1 - tb)


H.top_z = top_v005
H.half_breadth = half_breadth_v005
H.port_positions = port_positions_v005
H.row_z = row_z_v005


def deck_top(x, y, level):
    """Güverte üst yüzeyi (kamburluk dahil) — level: 'qd' ya da 'poop'."""
    zf = zqd if level == "qd" else zpd
    s = s_of_x(x, zf)
    z = zf(s)
    half = H.hull_point(s, z)[1] - 0.24
    v = min(abs(y) / half, 1.0)
    return z + 0.12 * (1 - v * v)


# --- Geometri yardımcıları ------------------------------------------------------
def box8(bm, c):
    v = [bm.verts.new(p) for p in c]
    for f in ((0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)):
        bm.faces.new([v[i] for i in f])


def box_f(bm, F, u0, u1, v0, v1, w0, w1):
    box8(bm, [F(u0, v0, w0), F(u1, v0, w0), F(u1, v1, w0), F(u0, v1, w0),
              F(u0, v0, w1), F(u1, v0, w1), F(u1, v1, w1), F(u0, v1, w1)])


def aabox(bm, x0, x1, y0, y1, z0, z1):
    box_f(bm, lambda u, v, w: Vector((u, v, w)), x0, x1, y0, y1, z0, z1)


def bar2d(bm, F, p, q, bw, w0, w1):
    d = (q - p)
    if d.length < 1e-4:
        return
    d.normalize()
    e = Vector((-d.y, d.x)) * (bw / 2)
    pts2 = [p - e, q - e, q + e, p + e]
    box8(bm, [F(a.x, a.y, w0) for a in pts2] + [F(a.x, a.y, w1) for a in pts2])


def lathe(bm, profile, seg, mat):
    rings = []
    for r, z in profile:
        if r < 1e-5:
            rings.append([bm.verts.new(mat @ Vector((0.0, 0.0, z)))])
        else:
            rings.append([bm.verts.new(mat @ Vector((r * math.cos(2 * math.pi * k / seg),
                                                     r * math.sin(2 * math.pi * k / seg), z)))
                          for k in range(seg)])
    for a, b in zip(rings[:-1], rings[1:]):
        if len(a) == 1 and len(b) == 1:
            continue
        if len(a) == 1:
            for k in range(seg):
                bm.faces.new([a[0], b[(k + 1) % seg], b[k]])
        elif len(b) == 1:
            for k in range(seg):
                bm.faces.new([a[k], a[(k + 1) % seg], b[0]])
        else:
            for k in range(seg):
                bm.faces.new([a[k], a[(k + 1) % seg], b[(k + 1) % seg], b[k]])


def axis_matrix(origin, axis):
    """Yerel Z'yi `axis` yönüne çeviren dönüşüm."""
    q = Vector((0, 0, 1)).rotation_difference(Vector(axis).normalized())
    return Matrix.Translation(Vector(origin)) @ q.to_matrix().to_4x4()


def sweep_rect(bm, pts, wy, hz):
    """Nokta dizisi boyunca yatay dikdörtgen kesitli ray (korkuluk küpeştesi)."""
    rings = []
    for i, p in enumerate(pts):
        a = pts[max(i - 1, 0)]
        b = pts[min(i + 1, len(pts) - 1)]
        t = (b - a)
        t.z = 0
        t.normalize()
        side = Vector((-t.y, t.x, 0)) * (wy / 2)
        up = Vector((0, 0, hz / 2))
        rings.append([bm.verts.new(p - side - up), bm.verts.new(p + side - up),
                      bm.verts.new(p + side + up), bm.verts.new(p - side + up)])
    for r0, r1 in zip(rings[:-1], rings[1:]):
        for k in range(4):
            bm.faces.new([r0[k], r0[(k + 1) % 4], r1[(k + 1) % 4], r1[k]])
    bm.faces.new(rings[0])
    bm.faces.new(list(reversed(rings[-1])))


def finish(name, bm, col, mats, sharp=40, bevel=None, origin=None):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = H.obj_from_bmesh(name, bm, col, mats)
    ob.data.set_sharp_from_angle(angle=math.radians(sharp))
    if bevel:
        m = ob.modifiers.new("Bevel", "BEVEL")
        m.width = bevel
        m.segments = 2
        m.limit_method = "ANGLE"
    H.build_uv_fallback(ob)
    if origin is not None:
        ob.data.transform(Matrix.Translation(-Vector(origin)))
        ob.location = Vector(origin)
    return ob


def assign_by(ob, fn):
    """Yüz merkezine göre malzeme indeksi ata."""
    for p in ob.data.polygons:
        p.material_index = fn(p)


def ensure_materials():
    M = {k: bpy.data.materials[v] for k, v in {
        "hull": "MAT_Hull_TarredOak", "band": "MAT_Hull_RedBand", "inner": "MAT_Bulwark_InnerRed",
        "deck": "MAT_Deck_Pine", "gold": "MAT_Trim_Gilt", "yellow": "MAT_Trim_YellowOchre",
        "timber": "MAT_Timber_Oak"}.items()}
    if "MAT_Iron_Black" not in bpy.data.materials:
        H.principled("MAT_Iron_Black", (0.03, 0.03, 0.03), rough=0.5, metal=0.9)
    M["iron"] = bpy.data.materials["MAT_Iron_Black"]
    if "MAT_Glass_Window" not in bpy.data.materials:
        m, _, b = H.principled("MAT_Glass_Window", (0.020, 0.024, 0.028), rough=0.06)
        b.inputs["Specular IOR Level"].default_value = 0.8
    M["glass"] = bpy.data.materials["MAT_Glass_Window"]
    if "MAT_Glass_Lantern" not in bpy.data.materials:
        m, _, b = H.principled("MAT_Glass_Lantern", (0.9, 0.7, 0.4), rough=0.2)
        b.inputs["Emission Color"].default_value = (1.0, 0.62, 0.28, 1)
        b.inputs["Emission Strength"].default_value = 6.0
    M["lamp"] = bpy.data.materials["MAT_Glass_Lantern"]
    return M


# --- Kıç aynası çerçevesi --------------------------------------------------------
Z0 = zqd(0.0)                   # kıç kasarası güvertesinin aynadaki yüksekliği
O_T = Vector((H.stern_x(Z0), 0.0, Z0))
U_T = Vector((0.0, 1.0, 0.0))
V_T = Vector((-math.sin(TH), 0.0, math.cos(TH)))
N_T = Vector((-math.cos(TH), 0.0, -math.sin(TH)))  # dışa (kıça) normal


def FT(u, v, w):
    return O_T + U_T * u + V_T * v + N_T * w


def v_of_z(z):
    return (z - Z0) / math.cos(TH)


WIN_V = (v_of_z(Z0 + 0.75), v_of_z(Z0 + 1.75))
WIN_U = [-1.90, -0.95, 0.0, 0.95, 1.90]
WIN_W = 0.62
CREST_W, CREST_SPR = 1.20, None


def lattice(bm, F, u0, u1, v0, v1, spacing=0.10, bw=0.022, w0=0.01, w1=0.04):
    dc = spacing * math.sqrt(2)
    for sign in (1, -1):
        cs = np.arange((v0 - sign * u1 if sign > 0 else v0 + u0) - dc, (v1 - sign * u0 if sign > 0 else v1 + u1) + dc, dc)
        for c in cs:
            pts = []
            for u in (u0, u1):
                v = sign * u + c
                if v0 - 1e-6 <= v <= v1 + 1e-6:
                    pts.append(Vector((u, v)))
            for v in (v0, v1):
                u = (v - c) / sign
                if u0 - 1e-6 <= u <= u1 + 1e-6:
                    pts.append(Vector((u, v)))
            uniq = []
            for p in pts:
                if all((p - q).length > 1e-4 for q in uniq):
                    uniq.append(p)
            if len(uniq) >= 2:
                bar2d(bm, F, uniq[0], uniq[1], bw, w0, w1)


def window_unit(bm_frame, bm_lat, bm_glass, F, uc, vc, w, h, glass_w=-0.12):
    u0, u1, v0, v1 = uc - w / 2, uc + w / 2, vc - h / 2, vc + h / 2
    fw = 0.07
    box_f(bm_frame, F, u0 - fw, u1 + fw, v1, v1 + fw, 0.0, 0.08)          # üst
    box_f(bm_frame, F, u0 - fw - 0.03, u1 + fw + 0.03, v0 - fw - 0.02, v0, 0.0, 0.10)  # eşik
    box_f(bm_frame, F, u0 - fw, u0, v0, v1, 0.0, 0.08)                     # sol
    box_f(bm_frame, F, u1, u1 + fw, v0, v1, 0.0, 0.08)                     # sağ
    box_f(bm_frame, F, u0 - fw - 0.04, u1 + fw + 0.04, v1 + fw, v1 + fw + 0.06, 0.0, 0.12)  # alın
    lattice(bm_lat, F, u0, u1, v0, v1)
    g = [bm_glass.verts.new(F(a, b, glass_w)) for a, b in ((u0, v0), (u1, v0), (u1, v1), (u0, v1))]
    bm_glass.faces.new(g)


# --- Yapı parçaları ----------------------------------------------------------------
def build_poop_deck(col, M):
    s1 = s_of_x(X_FRONT, zpd)
    return H.deck_surface("CORE_DECK_POOP", 0.004, s1, zpd, col, M["deck"])


def build_bulkhead(col, M):
    s_q = s_of_x(X_FRONT, zqd)
    zq = zqd(s_q)
    s_p = s_of_x(X_FRONT, zpd)
    zp = zpd(s_p)
    half_q = H.hull_point(s_q, zq)[1] - 0.24
    half_p = H.hull_point(s_p, zp)[1] - 0.24
    yq = H.hull_point(s_q, zq + 1.0)[1] - 0.10

    def camb(y, half):
        v = min(abs(y) / half, 1.0)
        return 0.12 * (1 - v * v)

    bot = lambda y: zq + camb(y, half_q) - 0.05  # noqa: E731
    top = lambda y: zp + camb(y, half_p) - 0.09  # noqa: E731
    bm = bmesh.new()
    x0, x1 = X_FRONT - 0.10, X_FRONT

    def strip(ya, yb, zb, zt):
        box8(bm, [Vector((x0, ya, zb(ya))), Vector((x1, ya, zb(ya))), Vector((x1, yb, zb(yb))), Vector((x0, yb, zb(yb))),
                  Vector((x0, ya, zt(ya))), Vector((x1, ya, zt(ya))), Vector((x1, yb, zt(yb))), Vector((x0, yb, zt(yb)))])

    for arr in (np.linspace(-yq, -DOOR_W / 2, 7), np.linspace(DOOR_W / 2, yq, 7)):
        for a, b in zip(arr[:-1], arr[1:]):
            strip(a, b, bot, top)
    door_top = bot(0.0) + DOOR_H
    strip(-DOOR_W / 2, DOOR_W / 2, lambda y: door_top, top)
    wall = finish("CORE_POOP_BULKHEAD", bm, col, [M["inner"]], sharp=30)

    bm = bmesh.new()
    for sgn in (-1, 1):  # kapı pervazı (dikmeler)
        y0, y1 = sorted((sgn * DOOR_W / 2, sgn * (DOOR_W / 2 + 0.12)))
        aabox(bm, X_FRONT - 0.02, X_FRONT + 0.06, y0, y1, zq + 0.10, door_top + 0.10)
    aabox(bm, X_FRONT - 0.02, X_FRONT + 0.07, -DOOR_W / 2 - 0.16, DOOR_W / 2 + 0.16, door_top, door_top + 0.14)
    aabox(bm, X_FRONT - 0.02, X_FRONT + 0.08, -yq, yq, zp - 0.30, zp - 0.10)   # ön kiriş
    trim = finish("CORE_POOP_BULKHEAD_TRIM", bm, col, [M["yellow"]], bevel=0.012)
    return [wall, trim], dict(zq=zq, zp=zp, yq=yq, door_top=door_top, half_p=half_p)


def build_stairs(col, M):
    obs = []
    info = []
    for sgn, tag in ((1, "S"), (-1, "P")):
        yi, yo = STAIR_Y
        ymid = sgn * (yi + yo) / 2
        xb = X_FRONT + STAIR_RUN
        z_bot = deck_top(xb, ymid, "qd")
        z_top = deck_top(X_FRONT - 0.05, ymid, "poop")
        rise = (z_top - z_bot) / STAIR_STEPS
        run = STAIR_RUN / STAIR_STEPS
        ya, yb = sorted((sgn * yi, sgn * yo))
        bm = bmesh.new()
        n_tread = []
        for k in range(1, STAIR_STEPS + 1):
            xf = xb - (k - 1) * run + 0.03
            xr = xb - k * run
            zt = z_bot + k * rise
            aabox(bm, xr, xf, ya + 0.02, yb - 0.02, zt - 0.05, zt)
            n_tread.append(len(bm.faces))
        # iki yan kiriş (stringer)
        p0 = Vector((xb + 0.12, 0, z_bot - 0.02))
        p1 = Vector((X_FRONT, 0, z_top - 0.02))
        d = (p1 - p0).normalized()
        perp = Vector((d.z, 0, -d.x))  # aşağı-ileri
        for yy in (ya, yb - 0.06):
            c = []
            for pz in (p0, p1, p1 + perp * 0.30, p0 + perp * 0.30):
                c.append(Vector((pz.x, yy, pz.z)))
            c += [Vector((q.x, q.y + 0.06, q.z)) for q in c]
            box8(bm, c)
        treads_end = len(bm.faces)
        # tırabzanlar (iki kenar): iki dikme + eğik küpeşte + ara dikmeler
        hr = 0.95
        posts = [(xb - 0.05, z_bot + rise), (X_FRONT + 0.10, z_top)]
        for yr in (yb - 0.03, ya + 0.03):
            for px, pz in posts:
                aabox(bm, px - 0.05, px + 0.05, yr - 0.05, yr + 0.05, pz, pz + hr + 0.08)
            for k in range(1, 5):
                t = k / 5
                px = posts[0][0] + t * (posts[1][0] - posts[0][0])
                pz = posts[0][1] + t * (posts[1][1] - posts[0][1])
                aabox(bm, px - 0.02, px + 0.02, yr - 0.02, yr + 0.02, pz, pz + hr)
            a = Vector((posts[0][0], yr, posts[0][1] + hr))
            b = Vector((posts[1][0], yr, posts[1][1] + hr))
            dd = (b - a).normalized()
            pp = Vector((dd.z, 0, -dd.x)) * 0.04
            c = [a - Vector((0, 0.04, 0)) - pp, b - Vector((0, 0.04, 0)) - pp, b + Vector((0, 0.04, 0)) - pp, a + Vector((0, 0.04, 0)) - pp]
            c += [q + pp * 2 for q in c]
            box8(bm, c)
        ob = finish(f"CORE_STAIRS_POOP_{tag}", bm, col, [M["deck"], M["timber"], M["yellow"]], bevel=0.008)
        nt = n_tread[-1]
        assign_by(ob, lambda p, nt=nt, te=treads_end: 0 if p.index < nt else (1 if p.index < te else 2))
        obs.append(ob)
        ang = math.degrees(math.atan2(z_top - z_bot, STAIR_RUN))
        info.append(dict(side=tag, x_bottom=round(xb, 3), x_top=X_FRONT, z_bottom=round(z_bot, 3), z_top=round(z_top, 3),
                         riser_m=round(rise, 3), tread_m=round(run, 3), angle_deg=round(ang, 1), y=[round(ya, 2), round(yb, 2)]))
    return obs, info


BALUSTER = [(0.0, 0.0), (0.050, 0.0), (0.050, 0.06), (0.036, 0.08), (0.030, 0.16), (0.052, 0.28), (0.056, 0.34),
            (0.040, 0.44), (0.026, 0.52), (0.026, 0.58), (0.040, 0.62), (0.046, 0.66), (0.046, 0.70), (0.0, 0.70)]


def rail_run(bm, pts, base_z_fn=None, spacing=0.28):
    """pts: korkuluğun oturduğu çizgi (taban). Balüster + alt/üst küpeşte."""
    pts = [Vector(p) for p in pts]
    lengths = [0.0]
    for a, b in zip(pts[:-1], pts[1:]):
        lengths.append(lengths[-1] + (b - a).length)
    total = lengths[-1]
    n = max(int(total / spacing), 1)
    for k in range(n + 1):
        d = total * k / n
        i = max(j for j in range(len(lengths)) if lengths[j] <= d + 1e-9)
        i = min(i, len(pts) - 2)
        t = (d - lengths[i]) / max(lengths[i + 1] - lengths[i], 1e-9)
        p = pts[i].lerp(pts[i + 1], t)
        lathe(bm, BALUSTER, 10, Matrix.Translation(p))
    sweep_rect(bm, [p + Vector((0, 0, 0.03)) for p in pts], 0.11, 0.06)
    sweep_rect(bm, [p + Vector((0, 0, RAIL_H + 0.045)) for p in pts], 0.13, 0.09)


def build_balustrade(col, M, bk):
    bm = bmesh.new()
    # yanlar: gövde üst kenarı boyunca (kıç üstü güverte önünden aynaya)
    s_front_top = s_of_x(X_FRONT - 0.05, lambda s: H.top_z(s))
    for sgn in (1, -1):
        pts = []
        for s in np.linspace(s_front_top, 0.004, 26):
            z = H.top_z(s)
            x = x_at(s, z)
            y = H.half_breadth(s, z) - 0.12
            pts.append((x, sgn * y, z))
        rail_run(bm, pts)
    # kıç: ayna üst kenarı boyunca, tepelik (|y| < CREST_W + 0.05) hariç
    zt = H.top_z(0.0)
    xt = H.stern_x(zt) + 0.12 * math.cos(TH)
    yt = H.half_breadth(0.004, zt) - 0.12
    for sgn in (1, -1):
        pts = [(xt, sgn * y, zt) for y in np.linspace(CREST_W + 0.08, yt, 6)]
        rail_run(bm, pts)
    # ön kenar: merdiven boşlukları hariç, 0,30 m kaide üstünde
    xf = X_FRONT - 0.06
    zp_edge = bk["zp"]
    wf = bk["half_p"] - 0.02
    segs = [(-wf + 0.22, -STAIR_Y[1]), (-STAIR_Y[0], STAIR_Y[0]), (STAIR_Y[1], wf - 0.22)]  # köşede yan korkulukla çakışmasın
    plinth = bmesh.new()
    for y0, y1 in segs:
        za, zb_ = deck_top(xf, y0, "poop") - 0.03, deck_top(xf, y1, "poop") - 0.03
        box8(plinth, [Vector((xf - 0.07, y0, za)), Vector((xf + 0.07, y0, za)), Vector((xf + 0.07, y1, zb_)), Vector((xf - 0.07, y1, zb_)),
                      Vector((xf - 0.07, y0, za + RIM_H)), Vector((xf + 0.07, y0, za + RIM_H)),
                      Vector((xf + 0.07, y1, zb_ + RIM_H)), Vector((xf - 0.07, y1, zb_ + RIM_H))])
        ys_ = np.linspace(y0 + 0.08, y1 - 0.08, 4)
        rail_run(bm, [(xf, y, za + (zb_ - za) * (y - y0) / (y1 - y0) + RIM_H) for y in ys_])
    rails = finish("CORE_POOP_BALUSTRADE", bm, col, [M["yellow"]], sharp=50)
    pl = finish("CORE_POOP_BREAST_PLINTH", plinth, col, [M["inner"]], bevel=0.01)
    return [rails, pl]


def build_stern_gallery(col, M, sock):
    bm_body, bm_frame, bm_lat, bm_glass, bm_gold = (bmesh.new() for _ in range(5))
    # 1) kıç aynası pencereleri
    vc = (WIN_V[0] + WIN_V[1]) / 2
    h = WIN_V[1] - WIN_V[0]
    for uc in WIN_U:
        window_unit(bm_frame, bm_lat, bm_glass, FT, uc, vc, WIN_W, h)
    # pilastrlar, eşik ve korniş silmesi
    pil_u = [(WIN_U[i] + WIN_U[i + 1]) / 2 for i in range(len(WIN_U) - 1)] + [WIN_U[0] - 0.55, WIN_U[-1] + 0.55]
    for pu in pil_u:
        box_f(bm_frame, FT, pu - 0.07, pu + 0.07, WIN_V[0] - 0.15, WIN_V[1] + 0.20, 0.0, 0.07)
        box_f(bm_gold, FT, pu - 0.10, pu + 0.10, WIN_V[1] + 0.12, WIN_V[1] + 0.22, 0.0, 0.10)  # başlık
    wu = max(abs(u) for u in pil_u) + 0.25
    box_f(bm_frame, FT, -wu, wu, WIN_V[0] - 0.24, WIN_V[0] - 0.14, 0.0, 0.12)
    box_f(bm_gold, FT, -wu - 0.05, wu + 0.05, WIN_V[1] + 0.22, WIN_V[1] + 0.32, 0.0, 0.14)
    # 2) oyma tepelik (kemerli pano) + güneş motifi
    v_rim = v_of_z(H.top_z(0.0))
    vb, vs, vt = v_rim - 0.28, v_rim + 0.35, v_rim + 0.85
    outline = [Vector((-CREST_W, vb)), Vector((CREST_W, vb)), Vector((CREST_W, vs))]
    for k in range(1, 24):
        a = math.pi * k / 24
        outline.append(Vector((CREST_W * math.cos(a), vs + (vt - vs) * math.sin(a))))
    outline.append(Vector((-CREST_W, vs)))
    front = [bm_body.verts.new(FT(p.x, p.y, 0.02)) for p in outline]
    back = [bm_body.verts.new(FT(p.x, p.y, -0.10)) for p in outline]
    bm_body.faces.new(front)
    bm_body.faces.new(list(reversed(back)))
    for i in range(len(outline)):
        j = (i + 1) % len(outline)
        bm_body.faces.new([front[i], back[i], back[j], front[j]])
    for i in range(len(outline)):  # altın bordür
        j = (i + 1) % len(outline)
        a, b = outline[i], outline[j]
        mid = (a + b) / 2
        inward = (Vector((0, (vb + vt) / 2)) - mid).normalized() * 0.04
        bar2d(bm_gold, FT, a + inward, b + inward, 0.08, 0.02, 0.08)
    sc_ = Vector((0.0, (vs + vt) / 2 - 0.05))
    ring = [bm_gold.verts.new(FT(sc_.x + 0.24 * math.cos(2 * math.pi * k / 24), sc_.y + 0.24 * math.sin(2 * math.pi * k / 24), 0.10))
            for k in range(24)]
    ring_b = [bm_gold.verts.new(FT(sc_.x + 0.24 * math.cos(2 * math.pi * k / 24), sc_.y + 0.24 * math.sin(2 * math.pi * k / 24), 0.02))
              for k in range(24)]
    bm_gold.faces.new(ring)
    bm_gold.faces.new(list(reversed(ring_b)))
    for k in range(24):
        bm_gold.faces.new([ring[k], ring_b[k], ring_b[(k + 1) % 24], ring[(k + 1) % 24]])
    for k in range(16):
        a = 2 * math.pi * k / 16
        r1 = 0.30
        r2 = 0.52 if k % 2 == 0 else 0.42
        half = 0.06
        p_l = sc_ + Vector((r1 * math.cos(a - half), r1 * math.sin(a - half)))
        p_r = sc_ + Vector((r1 * math.cos(a + half), r1 * math.sin(a + half)))
        p_t = sc_ + Vector((r2 * math.cos(a), r2 * math.sin(a)))
        tri_f = [bm_gold.verts.new(FT(p.x, p.y, 0.08)) for p in (p_l, p_r, p_t)]
        tri_b = [bm_gold.verts.new(FT(p.x, p.y, 0.02)) for p in (p_l, p_r, p_t)]
        bm_gold.faces.new(tri_f)
        bm_gold.faces.new(list(reversed(tri_b)))
        for i in range(3):
            j = (i + 1) % 3
            bm_gold.faces.new([tri_f[i], tri_b[i], tri_b[j], tri_f[j]])
    lantern_socket = FT(0.0, vt, -0.04)
    # 3) yan galeriler (iskele/sancak)
    zb, zt_ = Z0 - 0.35, zpd(0.0) - 0.12  # çatı sırtı kıç üstü küpeştesinin altında kalsın
    zc = Z0 + 1.25
    for sgn in (1, -1):
        x_fwd = H.stern_x(zc) + 2.10
        s_f = s_of_x(x_fwd, lambda s: zc)
        ys = [H.half_breadth(s, z) for s in np.linspace(0.0, s_f, 8) for z in np.linspace(zb, zt_, 6)]
        y_in, y_out = min(ys) - 0.10, max(ys) + 0.55
        xa = lambda z: H.stern_x(z) + 0.03  # noqa: E731
        c = [Vector((xa(zb), sgn * y_in, zb)), Vector((x_fwd, sgn * y_in, zb)), Vector((x_fwd, sgn * y_out, zb)), Vector((xa(zb), sgn * y_out, zb)),
             Vector((xa(zt_), sgn * y_in, zt_)), Vector((x_fwd, sgn * y_in, zt_)), Vector((x_fwd, sgn * y_out, zt_)), Vector((xa(zt_), sgn * y_out, zt_))]
        box8(bm_body, c)
        x_mid = (xa(zc) + x_fwd) / 2

        def FS(u, v, w, x_mid=x_mid, y_out=y_out, sgn=sgn):
            return Vector((x_mid + u, sgn * (y_out + w), zc + v))

        for uc in (-0.62, 0.0, 0.62):
            window_unit(bm_frame, bm_lat, bm_glass, FS, uc, 0.0, 0.42, 0.80, glass_w=0.004)
        for pu in (-0.93, -0.31, 0.31, 0.93):
            box_f(bm_frame, FS, pu - 0.05, pu + 0.05, -0.52, 0.55, 0.0, 0.06)
        box_f(bm_gold, FS, -1.02, 1.02, 0.55, 0.64, 0.0, 0.10)
        box_f(bm_frame, FS, -1.02, 1.02, -0.62, -0.52, 0.0, 0.10)
        # çatı: çıkıntılı saçak + dışa eğimli çatı
        ov = 0.08
        y_roof = min(ys) - 0.02  # çatı iç kenarı gövde duvarının içinde; güverteye taşmaz
        box8(bm_body, [Vector((xa(zt_) - ov, sgn * y_roof, zt_)), Vector((x_fwd + ov, sgn * y_roof, zt_)),
                       Vector((x_fwd + ov, sgn * (y_out + ov), zt_)), Vector((xa(zt_) - ov, sgn * (y_out + ov), zt_)),
                       Vector((xa(zt_ + 0.34) - ov, sgn * y_roof, zt_ + 0.34)), Vector((x_fwd + ov, sgn * y_roof, zt_ + 0.34)),
                       Vector((x_fwd + ov, sgn * (y_out + ov), zt_ + 0.08)), Vector((xa(zt_ + 0.08) - ov, sgn * (y_out + ov), zt_ + 0.08))])
        # alt sarkıt (drop) + topuz
        bx = [Vector((xa(zb), sgn * y_in, zb)), Vector((x_fwd, sgn * y_in, zb)), Vector((x_fwd, sgn * y_out, zb)), Vector((xa(zb), sgn * y_out, zb))]
        cx = (xa(zb) + x_fwd) / 2
        cy = sgn * (y_in + y_out) / 2 + sgn * 0.1
        tip = [Vector((cx - 0.14, cy - 0.10, zb - 0.95)), Vector((cx + 0.14, cy - 0.10, zb - 0.95)),
               Vector((cx + 0.14, cy + 0.10, zb - 0.95)), Vector((cx - 0.14, cy + 0.10, zb - 0.95))]
        box8(bm_body, bx + tip)
        lathe(bm_gold, [(0.0, 0.0), (0.12, -0.02), (0.14, -0.10), (0.06, -0.20), (0.09, -0.28), (0.0, -0.40)], 12,
              Matrix.Translation((cx, cy, zb - 0.95)))
    # nesneleri birleştir: gövde (kırmızı), çerçeve (sarı), kafes (meşe), cam, altın
    bms = [(bm_body, "band"), (bm_frame, "yellow"), (bm_lat, "timber"), (bm_glass, "glass"), (bm_gold, "gold")]
    mats = [M[k] for _, k in bms]
    merged = bmesh.new()
    offsets = []
    for idx, (b, _) in enumerate(bms):
        me = bpy.data.meshes.new("_tmp")
        b.to_mesh(me)
        b.free()
        me.polygons.foreach_set("material_index", [idx] * len(me.polygons))
        merged.from_mesh(me)
        bpy.data.meshes.remove(me)
        offsets.append(idx)
    ob = finish("MOD_STERN_GALLERY_A", merged, col, mats, sharp=35, origin=sock)
    ob["module_family"] = "SternModule"
    ob["socket"] = "SOCKET_STERN_MODULE"
    ob["manifest_version"] = MANIFEST_VERSION
    ob["note"] = "Kıç aynası pencere açıklıkları Hull Core'da (CUT_STERN_WINDOWS); varyantlar aynı düzeni kullanmalı"
    return ob, lantern_socket


def build_stern_window_cutter(col, hull):
    bm = bmesh.new()
    vc = (WIN_V[0] + WIN_V[1]) / 2
    h = WIN_V[1] - WIN_V[0]
    for uc in WIN_U:
        box_f(bm, FT, uc - WIN_W / 2, uc + WIN_W / 2, vc - h / 2, vc + h / 2, -0.9, 0.3)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = H.obj_from_bmesh("CUT_STERN_WINDOWS", bm, col)
    ob.display_type = "WIRE"
    ob.hide_render = True
    ob.hide_set(True)
    ob.hide_viewport = True
    m = hull.modifiers.new("SternWindows", "BOOLEAN")
    m.operation = "DIFFERENCE"
    m.object = ob
    m.solver = "EXACT"
    return ob


def build_helm(col, M, sock_loc):
    """Dümen dolabı: dümen tamburun kıç ucunda; oyuncu dümenin arkasında durup başa bakar."""
    bm_w, bm_g, bm_i = bmesh.new(), bmesh.new(), bmesh.new()
    ox, oy, oz = sock_loc
    hz = 1.05
    wx = ox - 0.35  # dümen düzlemi
    # jant (dış ve iç halka) — y-z düzleminde
    for rad, sw, sd, segs in ((0.62, 0.07, 0.065, 48), (0.36, 0.05, 0.04, 36)):
        rings = []
        for k in range(segs):
            a = 2 * math.pi * k / segs
            dirv = Vector((0, math.cos(a), math.sin(a)))
            c = Vector((wx, oy, oz + hz)) + dirv * rad
            rings.append([bm_w.verts.new(c + Vector((-sw / 2, 0, 0)) - dirv * sd / 2),
                          bm_w.verts.new(c + Vector((sw / 2, 0, 0)) - dirv * sd / 2),
                          bm_w.verts.new(c + Vector((sw / 2, 0, 0)) + dirv * sd / 2),
                          bm_w.verts.new(c + Vector((-sw / 2, 0, 0)) + dirv * sd / 2)])
        for k in range(segs):
            r0, r1 = rings[k], rings[(k + 1) % segs]
            for j in range(4):
                bm_w.faces.new([r0[j], r0[(j + 1) % 4], r1[(j + 1) % 4], r1[j]])
    # parmaklar (10) — torna profil, uçta tutamak
    spoke = [(0.0, 0.07), (0.024, 0.08), (0.030, 0.20), (0.022, 0.34), (0.026, 0.50), (0.024, 0.62), (0.020, 0.66),
             (0.030, 0.72), (0.022, 0.77), (0.028, 0.81), (0.0, 0.84)]
    for k in range(10):
        a = 2 * math.pi * k / 10 + math.pi / 20
        axis = Vector((0, math.cos(a), math.sin(a)))
        lathe(bm_w, spoke, 8, axis_matrix((wx, oy, oz + hz), axis))
    # göbek + pirinç kapak
    lathe(bm_w, [(0.0, -0.10), (0.11, -0.10), (0.12, -0.06), (0.12, 0.06), (0.11, 0.10), (0.0, 0.10)], 16,
          axis_matrix((wx, oy, oz + hz), (1, 0, 0)))
    lathe(bm_g, [(0.0, -0.13), (0.07, -0.13), (0.06, -0.10), (0.0, -0.10)], 16, axis_matrix((wx, oy, oz + hz), (1, 0, 0)))
    # tambur (varil) ve demir bilezikler
    lathe(bm_w, [(0.0, 0.0), (0.17, 0.0), (0.18, 0.05), (0.18, 0.55), (0.17, 0.60), (0.0, 0.60)], 20,
          axis_matrix((wx + 0.10, oy, oz + hz), (1, 0, 0)))
    for t in (0.08, 0.52):
        lathe(bm_i, [(0.0, t), (0.186, t), (0.186, t + 0.035), (0.0, t + 0.035)], 20, axis_matrix((wx + 0.10, oy, oz + hz), (1, 0, 0)))
    # iki A-ayak
    for sx in (wx + 0.13, wx + 0.78):
        for sy in (-1, 1):
            c0 = Vector((sx, oy + sy * 0.42, oz))
            c1 = Vector((sx, oy + sy * 0.10, oz + hz + 0.08))
            d = (c1 - c0).normalized()
            e = Vector((0, d.z, -d.y)) * 0.045
            q = [c0 - e + Vector((-0.045, 0, 0)), c0 - e + Vector((0.045, 0, 0)), c0 + e + Vector((0.045, 0, 0)), c0 + e + Vector((-0.045, 0, 0))]
            q += [p + (c1 - c0) for p in q]
            box8(bm_w, q)
        aabox(bm_w, sx - 0.05, sx + 0.05, oy - 0.30, oy + 0.30, oz + 0.30, oz + 0.38)
        aabox(bm_w, sx - 0.06, sx + 0.06, oy - 0.16, oy + 0.16, oz + hz + 0.05, oz + hz + 0.15)
    # dümenci ızgarası (platform)
    aabox(bm_w, wx - 0.95, wx - 0.15, oy - 0.55, oy + 0.55, oz, oz + 0.07)
    mats = [M["timber"], M["gold"], M["iron"]]
    merged = bmesh.new()
    for idx, b in enumerate((bm_w, bm_g, bm_i)):
        me = bpy.data.meshes.new("_tmp")
        b.to_mesh(me)
        b.free()
        me.polygons.foreach_set("material_index", [idx] * len(me.polygons))
        merged.from_mesh(me)
        bpy.data.meshes.remove(me)
    ob = finish("MOD_HELM_WHEEL_A", merged, bpy.data.collections["23_MODULES_DECK"], mats, sharp=40, origin=sock_loc)
    ob["module_family"] = "DeckUtility/Helm"
    ob["socket"] = "SOCKET_HELM"
    ob["manifest_version"] = MANIFEST_VERSION
    return ob, Vector((wx - 0.55, oy, oz))


def build_lantern(M, loc):
    bm_g, bm_l = bmesh.new(), bmesh.new()
    T = Matrix.Translation(loc)
    lathe(bm_g, [(0.0, 0.0), (0.06, 0.0), (0.05, 0.08), (0.05, 0.15), (0.0, 0.15)], 12, T)
    lathe(bm_g, [(0.0, 0.15), (0.12, 0.15), (0.22, 0.22), (0.30, 0.30), (0.32, 0.34), (0.30, 0.37), (0.0, 0.37)], 6, T)
    lathe(bm_l, [(0.27, 0.37), (0.27, 0.82)], 6, T)  # 6 cam
    for k in range(6):
        a = 2 * math.pi * k / 6
        p = Vector((0.285 * math.cos(a), 0.285 * math.sin(a), 0.0)) + loc
        aabox(bm_g, p.x - 0.022, p.x + 0.022, p.y - 0.022, p.y + 0.022, p.z + 0.35, p.z + 0.84)
    lathe(bm_g, [(0.0, 0.82), (0.31, 0.82), (0.33, 0.86), (0.26, 0.92), (0.18, 1.02), (0.10, 1.10), (0.05, 1.16),
                 (0.06, 1.20), (0.0, 1.24)], 6, T)
    lathe(bm_g, [(0.0, 1.24), (0.04, 1.26), (0.02, 1.30), (0.05, 1.36), (0.0, 1.42)], 12, T)
    merged = bmesh.new()
    for idx, b in enumerate((bm_g, bm_l)):
        me = bpy.data.meshes.new("_tmp")
        b.to_mesh(me)
        b.free()
        me.polygons.foreach_set("material_index", [idx] * len(me.polygons))
        merged.from_mesh(me)
        bpy.data.meshes.remove(me)
    ob = finish("MOD_LANTERN_STERN_A", merged, bpy.data.collections["24_MODULES_DECOR"], [M["gold"], M["lamp"]],
                sharp=50, origin=loc)
    ob["module_family"] = "LanternFlagSet"
    ob["socket"] = "SOCKET_LANTERN_STERN"
    ob["manifest_version"] = MANIFEST_VERSION
    return ob


# --- Soketler ----------------------------------------------------------------------
def set_socket(name, loc, col, shape="SINGLE_ARROW", size=0.6, rot=(0, 0, 0), **props):
    e = bpy.data.objects.get(name)
    moved = None
    if e is None:
        e = P4.empty(name, Vector(loc), col, rot=rot, shape=shape, size=size)
        e["mount_id"] = str(uuid.uuid5(NS_UUID, name))
    else:
        old = [round(v, 4) for v in e.location]
        e.location = Vector(loc)
        moved = {"socket": name, "from": old, "to": [round(v, 4) for v in e.location]}
    for k, v in props.items():
        e[k] = v
    e["manifest_version"] = MANIFEST_VERSION
    return e, moved


def update_sockets(col, helm_station, lantern_loc, stairs_info, bk):
    moved, added = [], []
    # kıç kasarası topları ileri + mürettebat yeniden
    for kind, idx, x, s, z in H.port_positions():
        if kind != "QD":
            continue
        _, y = H.hull_point(s, z)
        dz = H.deck_z(s) + H.QD_H
        for side, tag in ((1, "S"), (-1, "P")):
            name = f"SOCKET_CANNON_{tag}_QD_{idx:02d}"
            g = bpy.data.objects[name]
            old = [round(v, 4) for v in g.location]
            g.location = Vector((x, side * (y - 1.2), dz))
            g["manifest_version"] = MANIFEST_VERSION
            moved.append({"socket": name, "from": old, "to": [round(v, 4) for v in g.location]})
            bpy.context.view_layer.update()
            for key, (role, (lx, ly)) in P4.CREW.items():
                cn = f"SOCK_CREW_{tag}_QD_{idx:02d}_{key}"
                c = bpy.data.objects[cn]
                c.location = g.matrix_world @ Vector((lx, ly, 0.0))
                c["manifest_version"] = MANIFEST_VERSION
    # kaptan kıç üstü güverteye (SOCKET_HELM main() içinde taşındı)
    e, m = set_socket("SOCK_STATION_CAPTAIN", helm_station, col, station_role="captain",
                      command_chain=["player", "second_captain", "gunnery_officer"])
    moved.append(m)
    s2 = 0.325
    e, m = set_socket("SOCK_STATION_SECOND_CAPTAIN", (x_at(s2, zqd(s2)), 0.0, zqd(s2) + 0.12), col)
    moved.append(m)
    # kıç bayrağı: kıç üstü güverte kıç ucunda direk yeri
    zfl = deck_top(H.stern_x(zpd(0.0)) + 0.75, 0.0, "poop")
    e, m = set_socket("SOCKET_FLAG_STERN", (H.stern_x(zpd(0.0)) + 0.75, 0.0, zfl), col, shape="ARROWS")
    moved.append(m)
    e, _ = set_socket("SOCKET_LANTERN_STERN", lantern_loc, col, shape="ARROWS", size=0.4, module_family="LanternFlagSet")
    added.append(e.name)
    # navlink çiftleri
    for st in stairs_info:
        sgn = 1 if st["side"] == "S" else -1
        ym = sgn * (STAIR_Y[0] + STAIR_Y[1]) / 2
        for end, loc in (("BOTTOM", (st["x_bottom"] + 0.35, ym, st["z_bottom"])), ("TOP", (X_FRONT - 0.35, ym, st["z_top"]))):
            e, _ = set_socket(f"SOCK_NAVLINK_POOP_STAIR_{st['side']}_{end}", loc, col, shape="SPHERE", size=0.2,
                              link="stairs", pair=f"SOCK_NAVLINK_POOP_STAIR_{st['side']}")
            added.append(e.name)
    for end, dx in (("OUT", 0.6), ("IN", -0.6)):
        e, _ = set_socket(f"SOCK_NAVLINK_CABIN_DOOR_{end}", (X_FRONT + dx, 0.0, bk["zq"] + 0.12), col, shape="SPHERE",
                          size=0.2, link="door", pair="SOCK_NAVLINK_CABIN_DOOR")
        added.append(e.name)
    return [m for m in moved if m], added


# --- Çarpışma ----------------------------------------------------------------------
def rebuild_collision(col, bk, stairs_info):
    for o in [o for o in col.objects if o.name.startswith("UCX_")]:
        me = o.data
        bpy.data.objects.remove(o, do_unlink=True)
        if me.users == 0:
            bpy.data.meshes.remove(me)
    parts = C3.hull_slices(6)
    parts += C3.deck_slices(0.02, 0.975, H.deck_z, 10, "deck_gun")
    parts += C3.deck_slices(0.004, H.S_QD, zqd, 4, "deck_quarter")
    parts += C3.deck_slices(H.S_FC, 0.985, zqd, 2, "deck_forecastle")
    parts += C3.deck_slices(0.004, s_of_x(X_FRONT, zpd), zpd, 2, "deck_poop")
    parts += C3.bulwark_slices(14)
    # kıç aynası duvarı (bataryadan kıç üstü küpeşteye)
    pts = []
    for z in np.linspace(H.deck_z(0.0), H.top_z(0.0), 6):
        y = H.half_breadth(0.0, z)
        for dx in (0.0, 0.30):
            pts += [Vector((H.stern_x(z) + dx, y, z)), Vector((H.stern_x(z) + dx, -y, z))]
    parts.append((pts, "transom"))
    # ön bölme (kapının iki yanı + üstü)
    zq, zp, yq, dt = bk["zq"], bk["zp"], bk["yq"], bk["door_top"]
    for y0, y1, z0, z1 in ((-yq, -DOOR_W / 2, zq, zp), (DOOR_W / 2, yq, zq, zp), (-DOOR_W / 2, DOOR_W / 2, dt, zp)):
        pts = [Vector((x, y, z)) for x in (X_FRONT - 0.12, X_FRONT) for y in (y0, y1) for z in (z0, z1)]
        parts.append((pts, "bulkhead"))
    # merdiven rampaları (üçgen prizma)
    for st in stairs_info:
        ya, yb = st["y"]
        xb, xt, zb, zt = st["x_bottom"], st["x_top"], st["z_bottom"], st["z_top"]
        pts = [Vector((x, y, z)) for y in (ya, yb) for (x, z) in ((xb, zb), (xt, zt), (xt, zb))]
        parts.append((pts, "stairs"))
    # kıç üstü korkuluklar (düşme engeli)
    s_front_top = s_of_x(X_FRONT - 0.05, lambda s: H.top_z(s))
    edges = np.linspace(s_front_top, 0.004, 4)
    for sgn in (1, -1):
        for a, b in zip(edges[:-1], edges[1:]):
            pts = []
            for s in (a, b):
                z = H.top_z(s)
                x = x_at(s, z)
                y = H.half_breadth(s, z) - 0.12
                for dy in (-0.08, 0.08):
                    for dz in (0.0, RAIL_H + 0.09):
                        pts.append(Vector((x, sgn * (y + dy), z + dz)))
            parts.append((pts, "rail_poop"))
    zt = H.top_z(0.0)
    xt = H.stern_x(zt) + 0.12
    yt = H.half_breadth(0.004, zt)
    pts = [Vector((xt + dx, y, zt + dz)) for dx in (-0.08, 0.08) for y in (-yt, yt) for dz in (0.0, RAIL_H + 0.9)]
    parts.append((pts, "rail_poop"))
    for y0, y1 in ((-bk["half_p"], -STAIR_Y[1]), (-STAIR_Y[0], STAIR_Y[0]), (STAIR_Y[1], bk["half_p"])):
        pts = [Vector((x, y, z)) for x in (X_FRONT - 0.14, X_FRONT) for y in (y0, y1) for z in (zp, zp + RIM_H + RAIL_H + 0.1)]
        parts.append((pts, "rail_poop"))
    made = [C3.convex(f"UCX_CORE_HULL_SHELL_{k:02d}", p, col, purpose) for k, (p, purpose) in enumerate(parts)]
    return made


# --- Ana akış -------------------------------------------------------------------------
def main():
    if "--render-only" in sys.argv:
        bpy.ops.wm.open_mainfile(filepath=str(ROOT / "Blender" / "versions" / f"{SHIP}_{VER}.blend"))
        return render_v005(bpy.context.scene)
    bpy.ops.wm.open_mainfile(filepath=str(ROOT / "Blender" / "versions" / f"{SHIP}_{SRC_VER}.blend"))
    sc = bpy.context.scene
    M = ensure_materials()
    Cc = {c.name: c for c in bpy.data.collections}
    core = Cc["10_HULL_CORE"]
    socks = Cc["30_SOCKETS"]

    replaced = ["CORE_HULL_SHELL", "CUT_GUNPORTS", "CORE_GUNPORT_FRAMES", "CORE_MOULDING_RAIL"]
    for n in replaced:
        ob = bpy.data.objects.get(n)
        if ob:
            me = ob.data
            bpy.data.objects.remove(ob, do_unlink=True)
            if me is not None and me.users == 0:
                bpy.data.meshes.remove(me)

    hull = H.build_hull_shell(core, M)
    cut = H.build_port_cutters(core, hull)
    cut.hide_set(True)
    cut.hide_viewport = True
    build_stern_window_cutter(core, hull)
    H.build_port_frames(core, M)
    H.band_strip("CORE_MOULDING_RAIL", lambda s: H.top_z(s) - 0.06, 0.12, 0.10, core, M["yellow"], 0.003, 0.995)

    new = []
    new.append(build_poop_deck(core, M))
    bk_obs, bk = build_bulkhead(core, M)
    new += bk_obs
    stairs, stairs_info = build_stairs(core, M)
    new += stairs
    new += build_balustrade(core, M, bk)
    gallery, lantern_loc = build_stern_gallery(Cc["24_MODULES_DECOR"], M, bpy.data.objects["SOCKET_STERN_MODULE"].location.copy())
    new.append(gallery)
    # dümen soketi: ön bölmenin 1,9 m kıçı, orta hat, güverte yüzeyi
    hx = X_FRONT - 1.9
    helm_loc = Vector((hx, 0.0, deck_top(hx, 0.0, "poop")))
    hs = bpy.data.objects["SOCKET_HELM"]
    helm_move = {"socket": "SOCKET_HELM", "from": [round(v, 4) for v in hs.location], "to": [round(v, 4) for v in helm_loc]}
    hs.location = helm_loc
    helm, helm_station = build_helm(Cc["23_MODULES_DECK"], M, helm_loc)
    new.append(helm)
    new.append(build_lantern(M, lantern_loc))
    moved, added = update_sockets(socks, helm_station, lantern_loc, stairs_info, bk)
    moved.insert(0, helm_move)
    ucx = rebuild_collision(Cc["40_COLLISION"], bk, stairs_info)

    out = ROOT / "Blender" / "versions" / f"{SHIP}_{VER}.blend"
    if out.exists():
        raise SystemExit(f"{out} zaten var; versiyonlu kayıt üzerine yazılmaz.")
    bpy.ops.wm.save_as_mainfile(filepath=str(out), compress=True)

    H.VERSION = VER
    ap = ROOT / "reports" / f"scene_audit_{VER}.json"
    rep = H.audit(sc, ap)
    zp_front = bk["zp"]
    zq_front = bk["zq"]
    lant = bpy.data.objects["MOD_LANTERN_STERN_A"]
    rep["stern"] = {
        "poop_deck_above_quarterdeck_m": POOP_H,
        "poop_front_x": X_FRONT,
        "poop_length_at_deck_m": round(X_FRONT - H.stern_x(zp_front), 2),
        "poop_deck_z_front": round(zp_front, 3), "quarterdeck_z_front": round(zq_front, 3),
        "cabin_clear_height_center_m": round((zp_front + 0.12 - 0.10) - (zq_front + 0.12), 3),
        "door_m": [DOOR_W, DOOR_H],
        "stairs": stairs_info,
        "hull_top_at_stern_z": round(H.top_z(0.0), 3),
        "lantern_top_z": round(lant.location.z + 1.42, 3),
        "qd_gun_x": list(QD_PORT_X),
        "s_poop": round(S_POOP, 4),
    }
    rep["collision"] = {"count": len(ucx), "max_verts": max(len(o.data.vertices) for o in ucx),
                        "by_purpose": {p: sum(1 for o in ucx if o["ucx_purpose"] == p) for p in sorted({o["ucx_purpose"] for o in ucx})}}
    rep["pass"] = {"name": "pass_v005_stern", "source": f"Blender/versions/{SHIP}_{SRC_VER}.blend",
                   "pass_changes": {"rebuilt": replaced + ["UCX_*"],
                                    "added": [o.name for o in new] + ["CUT_STERN_WINDOWS"],
                                    "sockets_moved": moved, "sockets_added": added},
                   "manifest_version": MANIFEST_VERSION,
                   "geometry_changed": "hull top raised in stern (s<~0.17); hull section below old top unchanged"}
    ap.write_text(json.dumps(rep, indent=2, ensure_ascii=False), encoding="utf-8")
    st = rep["stern"]
    print("STERN", json.dumps({k: st[k] for k in ("poop_length_at_deck_m", "cabin_clear_height_center_m", "hull_top_at_stern_z",
                                                   "lantern_top_z")}, ensure_ascii=False))
    print("STAIRS", [(s["side"], s["angle_deg"], s["riser_m"]) for s in stairs_info])
    print("UCX", rep["collision"], "tris", rep["checks"]["render_tris_total"])
    print("MOVED", len(moved), "ADDED", len(added))

    if "--no-render" not in sys.argv:
        render_v005(sc)


def render_v005(sc):
    H.setup_render(sc, fast=True)
    out = ROOT / "renders" / VER
    out.mkdir(parents=True, exist_ok=True)
    zc = 2.3
    views = [
        ("bas", (60, 0, zc), (0, 0, zc), 27, None),
        ("kic", (-60, 0, zc), (0, 0, zc), 27, None),
        ("iskele_profil", (1.5, -80, zc), (1.5, 0, zc), 48, None),
        ("sancak_profil", (1.5, 80, zc), (1.5, 0, zc), 48, None),
        ("bas_omzu", (34, 26, 13), (1, 0, 1.5), None, 35),
        ("kic_omzu", (-34, -24, 12), (-4, 0, 2.5), None, 35),
        ("guverte", (18, 12, 28), (-4, 0, 3.0), None, 30),
        ("kic_yakin", (-27, 11, 8.5), (-17.5, 0, 5.2), None, 40),
        ("kic_ust_guverte", (-7.5, 7.5, 12.5), (-15.5, 0, 6.5), None, 28),
        ("merdivenler", (-6.0, -2.5, 6.6), (-13.8, 0.0, 5.2), None, 26),
    ]
    for name, loc, tgt, osc, lens in views:
        sc.camera = H.camera(sc, f"CAM5_{name}", loc, tgt, ortho=osc) if osc else H.camera(sc, f"CAM5_{name}", loc, tgt, lens=lens)
        sc.render.filepath = str(out / f"{SHIP}_{VER}_{name}.png")
        bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    main()
