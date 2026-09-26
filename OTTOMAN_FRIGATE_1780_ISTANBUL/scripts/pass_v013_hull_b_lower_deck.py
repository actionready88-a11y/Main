"""Pass v013 — Hull_B: alt top güverteli gövde sınıfı (v012 üzerine; gemi suda ~1 m yükselir).

Çalıştırma (depo kökünden):
    python3 OTTOMAN_FRIGATE_1780_ISTANBUL/scripts/pass_v013_hull_b_lower_deck.py [--no-render | --render-only]

Kullanıcı kararları (2026-09-26):
  - "1": gemi baştan Hull_B olarak kurulur; alt lumbarlar kapalı gelir, yükseltme kapakları açıp topları takar.
  - "Gemi aynı yükseklikte": güverteler ve siluet değişmez; alt güverte mevcut güvertenin altına girer.
  - Ara yükseklik 2,2 m (dünya) = 2,0 m tasarım.
  - Alt güverte su hattının altına düştüğü için "Gemi suda yükselsin": gövde geometrisi aynı, tüm gemi
    DWL = +1,00 m (dünya) yukarı taşınır → su çekimi 4,95 → ~3,95 m. Su hattı Z=0 standardı korunur.
  - Alt güverte: temel set (güverte, 10+10 lumbar + çerçeve + kapalı kapak modülü, 20 top soketi +
    80 mürettebat soketi, ambar ağızları, iniş merdivenleri, çarpışma) + kıçta subay bölmesi (gunroom) +
    duvar fenerleri.
Kaynaksız sayı yok: ölçüler tasarım tahminidir ve rapora "tahmin/oyun kararı" olarak yazılır.
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


P12 = _load("pass_v012", "pass_v012_guns20.py")
P11, P5, P4, H, K, SK = P12.P11, P12.P5, P12.P4, P12.H, P12.K, P12.SK
C3 = P5.C3
P8 = _load("pass_v008", "pass_v008_access_stairs.py")   # yalnız genel merdiven üreticisi (stair)

SRC_VER, VER = "v012", "v013"
ROOT, SHIP = H.ROOT, H.SHIP_ID
MANIFEST_VERSION = 11
P5.MANIFEST_VERSION = MANIFEST_VERSION
P11.MANIFEST_VERSION = MANIFEST_VERSION
NS_UUID = P4.NS_UUID

HULL_CLASS = "HULL_B_TWO_DECK"
DWL = 1.00                 # dünya; gemi suda bu kadar yükselir (su çekimi azalır)
DL = 2.20 / K              # tasarım; üst güverte → alt güverte
LOWER_X = tuple(x + 1.09 for x in P12.WAIST)   # alt lumbarlar üsttekilerin arasına (şaşırtmalı) — tasarım
GUNS_LOWER = 10
LID_T = 0.07               # kapak kalınlığı (tasarım)
FRAME_T = 0.07             # lumbar çerçeve genişliği (build_port_frames ile aynı)
XG = -10.50                # subay bölmesi (gunroom) ön yüzü, tasarım
DOOR_W, DOOR_H = 0.85, 1.65
BEAM_W, BEAM_D, BEAM_STEP = 0.20, 0.18, 1.20
DECK_T = 0.10              # deck_surface solidify kalınlığı
# ambar ağızları (tasarım): ad, x0, x1, |y|, tür
HATCHES = [("AFT", -6.95, -5.05, 0.55, "ladder"), ("MAIN", -2.30, -0.70, 0.70, "grating"), ("FORE", 5.55, 7.45, 0.55, "ladder")]
COAM_W, COAM_H = 0.10, 0.25
LADDER_W, LADDER_RUN, LADDER_STEPS = 0.80, 1.45, 9
LANTERN_X_SIDE = (-5.69, 0.85, 7.39)
LANTERN_Z = 1.45           # alt güverte üstü (tasarım)
SHIFT = Matrix.Translation((0.0, 0.0, DWL))


# --- Tasarım fonksiyonları -------------------------------------------------------
def zu(s):
    return H.deck_z(s)


def zl(s):
    return H.deck_z(s) - DL


def x_at(s, z):
    return H.stern_x(z) + s * (H.bow_x(z) - H.stern_x(z))


def s_of_x(x, zfn):
    lo, hi = 0.0, 1.0
    for _ in range(60):
        mid = (lo + hi) / 2
        if x_at(mid, zfn(mid)) < x:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def inner_half(s, z):
    return H.hull_point(s, z)[1] - 0.24


def deck_top(x, y, zfn):
    s = s_of_x(x, zfn)
    z = zfn(s)
    half = inner_half(s, z)
    v = min(abs(y) / half, 1.0)
    return z + 0.12 * (1 - v * v)


def W(p):
    """Tasarım noktası → dünya (×K, +DWL)."""
    return Vector(p) * K + Vector((0.0, 0.0, DWL))


def lower_ports():
    ports = []
    for k, x in enumerate(np.linspace(LOWER_X[0], LOWER_X[1], GUNS_LOWER)):
        s = s_of_x(x, zl)
        ports.append(("LOWER", k + 1, float(x), s, zl(s) + H.PORT_SILL + H.PORT_H / 2))
    return ports


# --- Nesne yardımcıları ------------------------------------------------------------
def shift_existing():
    """Mevcut tüm nesneleri +DWL taşı. Orijini sıfırdaki mesh'ler veride taşınır (pivot su hattında kalır)."""
    done_meshes, n = set(), 0
    for o in list(bpy.data.objects):
        if o.parent is not None:
            continue
        if o.type == "MESH" and o.location.length < 1e-6:
            if o.data.name not in done_meshes:
                o.data.transform(SHIFT)
                done_meshes.add(o.data.name)
        else:
            o.location.z += DWL
        n += 1
    return n


def place(ob):
    """Tasarım uzayında kurulmuş nesne → dünya (×K, UV ×K) ve +DWL."""
    P11.to_world(ob)
    if ob.type == "MESH" and ob.location.length < 1e-6:
        ob.data.transform(SHIFT)
    else:
        ob.location.z += DWL
    return ob


def move_to(ob, col):
    for c in list(ob.users_collection):
        c.objects.unlink(ob)
    col.objects.link(ob)


def set_socket(name, loc_world, col, shape="SINGLE_ARROW", size=0.3, rot=(0, 0, 0), **props):
    e, _ = P5.set_socket(name, loc_world, col, shape=shape, size=size, rot=rot, **props)
    e.rotation_euler = rot
    return e


# --- Gövde (Hull_B) parçaları --------------------------------------------------------
def build_lower_ports(core, M, hull):
    bm = bmesh.new()
    for kind, idx, x, s, z in lower_ports():
        _, y = H.hull_point(s, z)
        for side in (1, -1):
            r = bmesh.ops.create_cube(bm, size=1.0)
            bmesh.ops.scale(bm, vec=(H.PORT_W, 1.2, H.PORT_H), verts=r["verts"])
            bmesh.ops.translate(bm, vec=(x, side * y, z), verts=r["verts"])
    cut = H.obj_from_bmesh("CUT_GUNPORTS_LOWER", bm, core)
    cut.display_type = "WIRE"
    cut.hide_render = True
    place(cut)
    cut.hide_set(True)
    cut.hide_viewport = True
    mod = hull.modifiers.new("GunPortsLower", "BOOLEAN")
    mod.operation = "DIFFERENCE"
    mod.object = cut
    mod.solver = "EXACT"
    orig = H.port_positions
    H.port_positions = lower_ports
    try:
        fr = H.build_port_frames(core, M)
    finally:
        H.port_positions = orig
    fr.name = fr.data.name = "CORE_GUNPORT_FRAMES_LOWER"
    place(fr)
    H.build_uv_fallback(fr)
    wale = H.band_strip("CORE_WALE_LOWER_TIER", lambda s: zl(s) - 0.15, 0.34, 0.12, core, M["hull"], 0.012, 0.975)
    place(wale)
    return [cut, fr, wale]


# --- Güverte (Hull_B) parçaları --------------------------------------------------------
def hatch_cutter(core, deck):
    bm = bmesh.new()
    for name, x0, x1, hy, kind in HATCHES:
        s = s_of_x((x0 + x1) / 2, zu)
        z = zu(s)
        P5.aabox(bm, x0, x1, -hy, hy, z - 0.5, z + 0.5)
    cut = H.obj_from_bmesh("CUT_HATCHES", bm, core)
    cut.display_type = "WIRE"
    cut.hide_render = True
    place(cut)
    cut.hide_set(True)
    cut.hide_viewport = True
    mod = deck.modifiers.new("Hatches", "BOOLEAN")
    mod.operation = "DIFFERENCE"
    mod.object = cut
    mod.solver = "EXACT"
    return cut


def build_hatches(core, M):
    bm_c, bm_g = bmesh.new(), bmesh.new()
    info = {}
    for name, x0, x1, hy, kind in HATCHES:
        zb = deck_top((x0 + x1) / 2, hy, zu) - 0.04
        zt = deck_top((x0 + x1) / 2, 0.0, zu) + COAM_H
        c = COAM_W
        P5.aabox(bm_c, x0 - c, x1 + c, hy, hy + c, zb, zt)
        P5.aabox(bm_c, x0 - c, x1 + c, -hy - c, -hy, zb, zt)
        P5.aabox(bm_c, x0 - c, x0, -hy, hy, zb, zt)
        P5.aabox(bm_c, x1, x1 + c, -hy, hy, zb, zt)
        if kind == "grating":
            # ızgara: iki yönde çıta, üst yüzü koaming üstünde (yürünebilir)
            n_x = int((x1 - x0) / 0.12)
            n_y = int(2 * hy / 0.12)
            for k in range(1, n_x):
                xx = x0 + (x1 - x0) * k / n_x
                P5.aabox(bm_g, xx - 0.025, xx + 0.025, -hy, hy, zt - 0.06, zt)
            for k in range(1, n_y):
                yy = -hy + 2 * hy * k / n_y
                P5.aabox(bm_g, x0, x1, yy - 0.025, yy + 0.025, zt - 0.10, zt - 0.05)
        info[name] = dict(x0=x0, x1=x1, hy=hy, kind=kind, z_coaming_top=zt, z_deck=zb + 0.04)
    coam = P5.finish("CORE_HATCH_COAMINGS", bm_c, core, [M["timber"]], bevel=0.01)
    grat = P5.finish("CORE_HATCH_GRATING_MAIN", bm_g, core, [M["timber"]])
    return [place(coam), place(grat)], info


def build_ladders(core, M):
    obs, info = [], {}
    for name, x0, x1, hy, kind in HATCHES:
        if kind != "ladder":
            continue
        xt = x0 + 0.05
        xb = xt + LADDER_RUN
        p1 = Vector((xt, 0.0, deck_top(xt, 0.0, zu)))
        p0 = Vector((xb, 0.0, deck_top(xb, 0.0, zl)))
        bms = (bmesh.new(), bmesh.new(), bmesh.new())
        st = P8.stair(bms, p0, p1, width=LADDER_W, n=LADDER_STEPS)
        ob = P8.merge_finish(f"CORE_LADDER_LOWER_{name}", list(zip(bms, (M["deck"], M["timber"], M["yellow"]))), core)
        ob.data.transform(SHIFT)
        obs.append(ob)
        st.update(dict(x_top=xt, x_bottom=xb, z_top=p1.z, z_bottom=p0.z))
        info[name] = st
    return obs, info


def build_beams(core, M):
    """Üst güverte kirişleri (alt güverte tavanı). Ambar ağızlarını kesen kirişler atlanır."""
    bm = bmesh.new()
    xs = list(np.arange(x_at(0.03, zu(0.03)) + 0.6, x_at(0.965, zu(0.965)) - 0.3, BEAM_STEP)) + [XG - BEAM_W / 2]
    used = []
    for x in sorted(xs):
        if any(x0 - 0.2 < x < x1 + 0.2 for _, x0, x1, _, _ in HATCHES):
            continue
        if any(abs(x - u) < BEAM_W * 1.5 for u in used):
            continue
        used.append(x)
        s = s_of_x(x, zu)
        z = zu(s)
        half = inner_half(s, z - 0.2) + 0.05
        ys = np.linspace(-half, half, 13)
        for a, b in zip(ys[:-1], ys[1:]):
            ta = deck_top(x, a, zu) - DECK_T
            tb = deck_top(x, b, zu) - DECK_T
            x0, x1 = x - BEAM_W / 2, x + BEAM_W / 2
            P5.box8(bm, [Vector((x0, a, ta - BEAM_D)), Vector((x1, a, ta - BEAM_D)), Vector((x1, b, tb - BEAM_D)), Vector((x0, b, tb - BEAM_D)),
                         Vector((x0, a, ta)), Vector((x1, a, ta)), Vector((x1, b, tb)), Vector((x0, b, tb))])
    ob = P5.finish("CORE_DECK_BEAMS_UPPER", bm, core, [M["timber"]], bevel=0.01)
    return place(ob), used


def build_gunroom_bulkhead(core, M):
    s = s_of_x(XG, zl)
    zq = zl(s)
    su = s_of_x(XG, zu)
    zp = zu(su)
    half_l = inner_half(s, zq)
    half_u = inner_half(su, zp)
    yq = min(half_l, H.hull_point(s, zq + 1.0)[1] - 0.24, inner_half(su, zp - 0.3)) + 0.05

    def camb(y, half):
        v = min(abs(y) / half, 1.0)
        return 0.12 * (1 - v * v)

    bot = lambda y: zq + camb(y, half_l) - 0.05  # noqa: E731
    top = lambda y: zp + camb(y, half_u) - DECK_T - 0.01  # noqa: E731
    bm = bmesh.new()
    x0, x1 = XG - 0.08, XG

    def strip(ya, yb, zb, zt):
        P5.box8(bm, [Vector((x0, ya, zb(ya))), Vector((x1, ya, zb(ya))), Vector((x1, yb, zb(yb))), Vector((x0, yb, zb(yb))),
                     Vector((x0, ya, zt(ya))), Vector((x1, ya, zt(ya))), Vector((x1, yb, zt(yb))), Vector((x0, yb, zt(yb)))])

    for arr in (np.linspace(-yq, -DOOR_W / 2, 9), np.linspace(DOOR_W / 2, yq, 9)):
        for a, b in zip(arr[:-1], arr[1:]):
            strip(a, b, bot, top)
    door_top = bot(0.0) + DOOR_H
    strip(-DOOR_W / 2, DOOR_W / 2, lambda y: door_top, top)
    n_wall = len(bm.faces)
    for sgn in (-1, 1):   # pervaz: her iki yüzde dikmeler + başlık
        y0, y1 = sorted((sgn * DOOR_W / 2, sgn * (DOOR_W / 2 + 0.10)))
        P5.aabox(bm, XG - 0.12, XG + 0.04, y0, y1, zq + 0.07, door_top + 0.10)
    P5.aabox(bm, XG - 0.12, XG + 0.05, -DOOR_W / 2 - 0.14, DOOR_W / 2 + 0.14, door_top, door_top + 0.12)
    ob = P5.finish("CORE_GUNROOM_BULKHEAD", bm, core, [M["inner"], M["yellow"]], sharp=30, bevel=0.008)
    P5.assign_by(ob, lambda p: 0 if p.index < n_wall else 1)
    return place(ob), dict(zq=zq, zp=zp, yq=yq, door_top=door_top)


# --- Modüller: lumbar kapakları, duvar fenerleri --------------------------------------
def lid_mesh(M):
    """Yerel: menteşe ekseni X (orijin), kapak -Z yönünde sarkar, +Y dışa. Dünya metre."""
    w = (H.PORT_W + 2 * FRAME_T) * K
    h = (H.PORT_H + 2 * FRAME_T) * K
    t = LID_T * K
    bm = bmesh.new()
    P5.aabox(bm, -w / 2, w / 2, 0.0, t, -h, 0.0)
    n_board = len(bm.faces)
    for sx in (-0.22 * w, 0.22 * w):   # iki demir menteşe lamı
        P5.aabox(bm, sx - 0.03, sx + 0.03, t, t + 0.012, -0.80 * h, 0.01)
        P5.aabox(bm, sx - 0.045, sx + 0.045, t - 0.01, t + 0.035, -0.02, 0.035)
    P5.aabox(bm, -0.03, 0.03, t, t + 0.03, -0.92 * h, -0.86 * h)   # halka yuvası (açma halatı)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new("MOD_PORT_LID_A")
    bm.to_mesh(me)
    bm.free()
    for m in (M["hull"], M["inner"], M["iron"]):
        me.materials.append(m)
    for p in me.polygons:
        if p.index >= n_board:
            p.material_index = 2
        elif p.normal.y < -0.5:
            p.material_index = 1
        else:
            p.material_index = 0
    tmp = bpy.data.objects.new("_tmp_lid", me)
    H.build_uv_fallback(tmp)
    bpy.data.objects.remove(tmp)
    me.set_sharp_from_angle(angle=math.radians(30))
    return me


def lid_frame(side, s, z):
    """Kapak menteşe noktası ve eksenleri (tasarım), gövdenin eğimine göre."""
    y0 = H.hull_point(s, z - 0.2)[1]
    y1 = H.hull_point(s, z + 0.2)[1]
    a, b = (y1 - y0), 0.4
    n = math.hypot(a, b)
    a, b = a / n, b / n
    if side > 0:
        X, Z = Vector((1, 0, 0)), Vector((0, a, b))
    else:
        X, Z = Vector((-1, 0, 0)), Vector((0, -a, b))
    Y = Z.cross(X)
    return Matrix((X, Y, Z)).transposed()


def build_lids(mods, col_s, M):
    me = lid_mesh(M)
    obs, socks = [], []
    for kind, idx, x, s, z in lower_ports():
        zh = z + H.PORT_H / 2 + FRAME_T
        _, yh = H.hull_point(s, zh)
        for side, tag in ((1, "S"), (-1, "P")):
            R = lid_frame(side, s, zh)
            pos_d = Vector((x, side * yh, zh)) + R @ Vector((0, 0.05, 0))
            loc = W(pos_d)
            rot = R.to_euler()
            name = f"LOWER_{tag}_{idx:02d}"
            ob = bpy.data.objects.new(f"MOD_PORT_LID_{name}", me)
            mods.objects.link(ob)
            ob.location = loc
            ob.rotation_euler = rot
            ob["module_family"] = "PortLidSet"
            ob["hinge_axis"] = "local_X"
            ob["open_rotation_local_x_deg"] = 80.0
            ob["state_default"] = "closed"
            ob["socket"] = f"SOCKET_PORT_LID_{name}"
            obs.append(ob)
            e = set_socket(f"SOCKET_PORT_LID_{name}", loc, col_s, shape="ARROWS", size=0.25, rot=rot,
                           module_family="PortLidSet", gun_socket=f"SOCKET_CANNON_{name}", hull_class=HULL_CLASS)
            socks.append(e.name)
    return obs, socks


def lantern_mesh(M):
    """Yerel: orijin duvarda, +Y odaya doğru, Z yukarı. Dünya metre."""
    bm_i, bm_g = bmesh.new(), bmesh.new()
    P5.aabox(bm_i, -0.06, 0.06, 0.0, 0.025, -0.10, 0.14)                 # duvar levhası
    P5.aabox(bm_i, -0.015, 0.015, 0.02, 0.30, 0.09, 0.12)                 # kol
    P5.aabox(bm_i, -0.015, 0.015, 0.27, 0.30, 0.02, 0.12)                 # askı
    cx, cy = 0.0, 0.285
    for dx in (-0.075, 0.075):                                            # kafes dikmeleri
        for dy in (-0.075, 0.075):
            P5.aabox(bm_i, cx + dx - 0.01, cx + dx + 0.01, cy + dy - 0.01, cy + dy + 0.01, -0.26, 0.0)
    P5.aabox(bm_i, cx - 0.09, cx + 0.09, cy - 0.09, cy + 0.09, -0.29, -0.26)   # taban
    P5.aabox(bm_i, cx - 0.09, cx + 0.09, cy - 0.09, cy + 0.09, 0.0, 0.03)      # kapak
    r = bmesh.ops.create_cone(bm_i, cap_ends=True, segments=8, radius1=0.08, radius2=0.015, depth=0.07)
    bmesh.ops.translate(bm_i, vec=(cx, cy, 0.065), verts=r["verts"])
    P5.aabox(bm_g, cx - 0.066, cx + 0.066, cy - 0.066, cy + 0.066, -0.255, -0.005)
    me = bpy.data.meshes.new("MOD_LANTERN_WALL_A")
    merged = bmesh.new()
    for idx, b in enumerate((bm_i, bm_g)):
        tmp = bpy.data.meshes.new("_tmp")
        b.to_mesh(tmp)
        b.free()
        tmp.polygons.foreach_set("material_index", [idx] * len(tmp.polygons))
        merged.from_mesh(tmp)
        bpy.data.meshes.remove(tmp)
    bmesh.ops.recalc_face_normals(merged, faces=merged.faces)
    merged.to_mesh(me)
    merged.free()
    me.materials.append(M["iron"])
    me.materials.append(M["lamp"])
    tmp = bpy.data.objects.new("_tmp_lan", me)
    H.build_uv_fallback(tmp)
    bpy.data.objects.remove(tmp)
    me.set_sharp_from_angle(angle=math.radians(30))
    return me


def build_lanterns(mods, col_s, M, bk):
    me = lantern_mesh(M)
    spots = []
    for x in LANTERN_X_SIDE:
        s = s_of_x(x, zl)
        z = zl(s) + LANTERN_Z
        y = H.hull_point(s, z)[1] - 0.24
        spots.append(((x, y - 0.01, z), math.pi))      # sancak duvarı, oda -Y yönünde
        spots.append(((x, -(y - 0.01), z), 0.0))       # iskele duvarı
    for yy in (1.6, -1.6):                              # subay bölmesi (bölmenin kıç yüzü)
        spots.append(((XG - 0.09, yy, bk["zq"] + LANTERN_Z), math.pi / 2))
    obs, socks = [], []
    for k, (p, rz) in enumerate(spots, 1):
        loc = W(p)
        ob = bpy.data.objects.new(f"MOD_LANTERN_WALL_A_{k:02d}", me)
        mods.objects.link(ob)
        ob.location = loc
        ob.rotation_euler = (0, 0, rz)
        ob["module_family"] = "LanternFlagSet"
        ob["socket"] = f"SOCK_LANTERN_LOWER_{k:02d}"
        obs.append(ob)
        e = set_socket(f"SOCK_LANTERN_LOWER_{k:02d}", loc, col_s, shape="SPHERE", size=0.12, rot=(0, 0, rz),
                       module_family="LanternFlagSet", light="point (UE), değer oyun ayarı",
                       light_offset_local=[0.0, 0.285, -0.13], room="gunroom" if k > 6 else "lower_gun_deck")
        socks.append(e.name)
    return obs, socks


# --- Soketler ------------------------------------------------------------------------
def build_lower_sockets(col):
    names = []
    for kind, idx, x, s, z in lower_ports():
        _, y = H.hull_point(s, z)
        for side, tag in ((1, "S"), (-1, "P")):
            rz = math.radians(90) if side > 0 else math.radians(-90)
            loc = W((x, side * (y - 1.2), zl(s)))
            gname = f"SOCKET_CANNON_LOWER_{tag}_{idx:02d}"
            grp = f"{'STARBOARD' if side > 0 else 'PORT'}_LOWER"
            g = set_socket(gname, loc, col, shape="ARROWS", size=0.25, rot=(0, 0, rz), battery_group=grp,
                           slot="SLOT_" + gname[len("SOCKET_"):], upgrade="lower_deck_battery", default_enabled=False,
                           port_lid=f"MOD_PORT_LID_LOWER_{tag}_{idx:02d}", hull_class=HULL_CLASS)
            names.append(gname)
            bpy.context.view_layer.update()
            for key, (role, (lx, ly)) in P4.CREW.items():
                p = g.matrix_world @ (Vector((lx, ly, 0.0)) * K)
                cname = f"SOCK_CREW_LOWER_{tag}_{idx:02d}_{key}"
                set_socket(cname, p, col, shape="SINGLE_ARROW", size=0.35, rot=(0, 0, rz), crew_role=role, gun_socket=gname,
                           battery_group=grp, upgrade="lower_deck_battery")
                names.append(cname)
    return names


def build_nav_sockets(col, ladders, bk):
    names = []
    for key, st in ladders.items():
        ym = 0.0
        pair = f"SOCK_NAVLINK_LADDER_{key}"
        for end, p in (("TOP", (st["x_top"] - 0.45, ym, st["z_top"])), ("BOTTOM", (st["x_bottom"] + 0.40, ym, st["z_bottom"]))):
            set_socket(f"{pair}_{end}", W(p), col, shape="SPHERE", size=0.2 * K, link="stairs", pair=pair,
                       decks=["gun_deck_upper", "gun_deck_lower"])
            names.append(f"{pair}_{end}")
    for end, dx in (("OUT", 0.6), ("IN", -0.6)):
        set_socket(f"SOCK_NAVLINK_GUNROOM_DOOR_{end}", W((XG + dx, 0.0, bk["zq"] + 0.12)), col, shape="SPHERE", size=0.2 * K,
                   link="door", pair="SOCK_NAVLINK_GUNROOM_DOOR", room="gunroom (subay bölmesi, alt güverte kıçı)")
        names.append(f"SOCK_NAVLINK_GUNROOM_DOOR_{end}")
    x = 3.20
    set_socket("SOCK_STATION_LOWER_BATTERY_OFFICER", W((x, 0.0, deck_top(x, 0.0, zl))), col, shape="SINGLE_ARROW", size=0.6,
               station_role="lower_battery_officer", command_chain=["player", "second_captain", "gunnery_officer", "lower_battery_officer"],
               upgrade="lower_deck_battery")
    names.append("SOCK_STATION_LOWER_BATTERY_OFFICER")
    return names


def update_existing_sockets(col):
    """Kaldırma ile anlamı değişen soketler: yüzdürme (su hattı altı), mahmuz (su hattında), direkler."""
    moved = []
    k = 0
    for s in np.linspace(0.12, 0.9, 8):
        zd = (-1.32 - DWL) / K
        x, y = H.hull_point(s, zd)
        for side in (1, -1):
            k += 1
            e = bpy.data.objects[f"SOCK_BUOY_{k:02d}"]
            old = [round(v, 3) for v in e.location]
            e.location = Vector((x * K, side * y * 0.6 * K, -1.32))
            moved.append({"socket": e.name, "from": old, "to": [round(v, 3) for v in e.location]})
    e = bpy.data.objects["SOCKET_RAM"]
    zd = (-0.38 - DWL) / K
    old = [round(v, 3) for v in e.location]
    e.location = Vector((H.bow_x(zd) * K + 0.05, 0.0, -0.38))
    moved.append({"socket": "SOCKET_RAM", "from": old, "to": [round(v, 3) for v in e.location]})
    for m in ("FORE", "MAIN", "MIZZEN"):
        o = bpy.data.objects[f"SOCKET_MAST_{m}"]
        s = H.MAST_S[m]
        o["passes_lower_deck"] = True
        o["lower_deck_z_world"] = round(zl(s) * K + DWL, 3)
    for o in bpy.data.objects:
        if o.type == "EMPTY":
            o["manifest_version"] = MANIFEST_VERSION
            o["hull_class"] = HULL_CLASS
    return moved


# --- Çarpışma -------------------------------------------------------------------------
def deck_pieces(zfn, s0, s1, n, purpose, holes=()):
    xa, xb = x_at(s0, zfn(s0)), x_at(s1, zfn(s1))
    xs = sorted(set([float(v) for v in np.linspace(xa, xb, n + 1)] + [v for h in holes for v in (h[0], h[1])]))
    xs = [v for v in xs if xa <= v <= xb]
    out = []
    for a, b in zip(xs[:-1], xs[1:]):
        if b - a < 0.05:
            continue
        mid = (a + b) / 2
        hole = next((h for h in holes if h[0] <= mid <= h[1]), None)
        rows = []
        for x in (a, b):
            s = s_of_x(x, zfn)
            z = zfn(s)
            w = max(inner_half(s, z), 0.3)
            rows.append((x, z, w))
        if hole is None:
            pts = []
            for x, z, w in rows:
                pts += [Vector((x, yy, z + 0.12 * (1 - (yy / w) ** 2))) for yy in (-w, -w / 2, 0.0, w / 2, w)]
                pts += [Vector((x, w, z - 0.25)), Vector((x, -w, z - 0.25))]
            out.append((pts, purpose))
        else:
            hy = hole[2]
            for sgn in (1, -1):
                pts = []
                for x, z, w in rows:
                    for yy in (hy, (hy + w) / 2, w):
                        pts.append(Vector((x, sgn * yy, z + 0.12 * (1 - (yy / w) ** 2))))
                    pts += [Vector((x, sgn * hy, z - 0.25)), Vector((x, sgn * w, z - 0.25))]
                out.append((pts, purpose))
    return out


def rebuild_collision(col, hatch_info, ladders, bk):
    removed = []
    for o in list(col.objects):
        if o.name.startswith("UCX_") and o.get("ucx_purpose") in ("hull", "deck_gun"):
            removed.append(o.get("ucx_purpose"))
            me = o.data
            bpy.data.objects.remove(o, do_unlink=True)
            bpy.data.meshes.remove(me)
    parts = []
    # ambar altı (alt güvertenin altı dolu; ambar şimdilik oynanabilir değil)
    edges = np.linspace(0.0, 1.0, 7)
    for a, b in zip(edges[:-1], edges[1:]):
        pts = []
        for s in (a, b):
            top = zl(s) - 0.25
            for z in np.linspace(H.ZK, top, 9):
                x, y = H.hull_point(s, z)
                y = max(y, 0.15)
                pts += [Vector((x, y, z)), Vector((x, -y, z))]
            pts.append(Vector((H.hull_point(s, H.ZK)[0], 0.0, -H.T)))
        parts.append((pts, "hull"))
    # alt güverte ile üst güverte arası borda duvarları
    edges = np.linspace(0.012, 0.985, 15)
    for side in (1, -1):
        for a, b in zip(edges[:-1], edges[1:]):
            pts = []
            for s in (a, b):
                for z in np.linspace(zl(s) - 0.3, zu(s), 4):
                    x, y = H.hull_point(s, z)
                    pts += [Vector((x, side * y, z)), Vector((x, side * max(y - 0.26, 0.0), z))]
            parts.append((pts, "hull_side_starboard" if side > 0 else "hull_side_port"))
    pts = []
    for z in np.linspace(zl(0.0) - 0.3, zu(0.0), 5):
        y = H.half_breadth(0.0, z)
        for dx in (0.0, 0.30):
            pts += [Vector((H.stern_x(z) + dx, y, z)), Vector((H.stern_x(z) + dx, -y, z))]
    parts.append((pts, "transom_lower"))
    holes = [(h["x0"], h["x1"], h["hy"]) for h in hatch_info.values() if h["kind"] == "ladder"]
    parts += deck_pieces(zu, 0.02, 0.975, 10, "deck_gun", holes)
    parts += deck_pieces(zl, 0.012, 0.972, 12, "deck_lower")
    for name, h in hatch_info.items():
        x0, x1, hy, zt, zd = h["x0"], h["x1"], h["hy"], h["z_coaming_top"], h["z_deck"]
        c = COAM_W
        if h["kind"] == "grating":
            parts.append(([Vector((x, y, z)) for x in (x0 - c, x1 + c) for y in (-hy - c, hy + c) for z in (zd - 0.05, zt)], "hatch_grating"))
        else:
            for bx in ((x0 - c, x1 + c, hy, hy + c), (x0 - c, x1 + c, -hy - c, -hy), (x0 - c, x0, -hy, hy), (x1, x1 + c, -hy, hy)):
                parts.append(([Vector((x, y, z)) for x in bx[:2] for y in bx[2:] for z in (zd - 0.05, zt)], "hatch_coaming"))
    for key, st in ladders.items():
        ya, yb = -LADDER_W / 2, LADDER_W / 2
        parts.append(([Vector((x, y, z)) for y in (ya, yb) for (x, z) in ((st["x_bottom"], st["z_bottom"]), (st["x_top"], st["z_top"]),
                                                                           (st["x_top"], st["z_bottom"]))], "stairs"))
    zq, zp, yq, dt = bk["zq"], bk["zp"], bk["yq"], bk["door_top"]
    for y0, y1, z0, z1 in ((-yq, -DOOR_W / 2, zq, zp), (DOOR_W / 2, yq, zq, zp), (-DOOR_W / 2, DOOR_W / 2, dt, zp)):
        parts.append(([Vector((x, y, z)) for x in (XG - 0.10, XG) for y in (y0, y1) for z in (z0, z1)], "bulkhead_gunroom"))
    made = [C3.convex(f"UCX_TMP_{k}", [W(p) for p in pts], col, purpose) for k, (pts, purpose) in enumerate(parts)]
    allu = sorted([o for o in col.objects if o.name.startswith("UCX_") and o not in made], key=lambda o: o.name) + made
    for i, o in enumerate(allu):
        o.name = f"_tmp_ucx_{i}"
    for i, o in enumerate(allu):
        o.name = f"UCX_CORE_HULL_SHELL_{i:02d}"
        o.data.name = o.name
    return allu, removed, len(made)


# --- Denetimler -------------------------------------------------------------------------
def checks(ladders, bk):
    out = {}
    ports = lower_ports()
    out["lower_port_sill_above_wl_world_m"] = {
        "min": round(min((zl(s) + H.PORT_SILL) * K + DWL for _, _, _, s, _ in ports), 3),
        "max": round(max((zl(s) + H.PORT_SILL) * K + DWL for _, _, _, s, _ in ports), 3)}
    out["lower_deck_above_wl_world_m"] = {"midship": round(zl(0.45) * K + DWL, 3),
                                          "min": round(min(zl(s) for s in np.linspace(0.012, 0.972, 50)) * K + DWL, 3)}
    out["between_decks_world_m"] = round(DL * K, 3)
    out["clear_under_beams_world_m"] = round((DL - DECK_T - BEAM_D) * K, 3)
    out["upper_deck_above_wl_world_m"] = round(zu(0.45) * K + DWL, 3)
    # lumbar ile kuşak arası boşluk (tasarım, göreli)
    top_lower_frame = -DL + H.PORT_SILL + H.PORT_H + FRAME_T
    out["gap_lower_port_frame_to_wale_lower_world_m"] = round(((-0.55 - 0.13) - top_lower_frame) * K, 3)
    out["gap_wale_lower_tier_to_port_frame_world_m"] = round(((-DL + H.PORT_SILL - FRAME_T) - (-DL - 0.15 + 0.17)) * K, 3)
    # mürettebat: güverte içinde mi; merdiven/bölme ile çakışma
    inside, conflicts = [], []
    for o in bpy.data.objects:
        if o.type != "EMPTY" or not o.name.startswith("SOCK_CREW_LOWER_"):
            continue
        p = (o.location - Vector((0, 0, DWL))) / K
        s = s_of_x(p.x, zl)
        if abs(p.y) > inner_half(s, zl(s)) - 0.30:
            inside.append(o.name)
        if p.x < XG + 0.25:
            conflicts.append({"crew": o.name, "with": "gunroom_bulkhead", "x_world": round(o.location.x, 2)})
        for key, st in ladders.items():
            if st["x_top"] - 0.2 <= p.x <= st["x_bottom"] + 0.6 and abs(p.y) < LADDER_W / 2 + 0.3:
                conflicts.append({"crew": o.name, "with": f"ladder_{key}"})
    out["crew_outside_deck"] = inside
    out["crew_conflicts"] = conflicts
    # ambar ağzı / direk mesafesi
    mast = {m: x_at(s, zu(s)) for m, s in H.MAST_S.items()}
    out["hatch_mast_clearance_world_m"] = {
        name: round(min(min(abs(mx - x0), abs(mx - x1)) if not (x0 <= mx <= x1) else 0.0 for mx in mast.values()) * K, 3)
        for name, x0, x1, _, _ in HATCHES}
    return out


# --- Render ------------------------------------------------------------------------------
def render(sc):
    H.setup_render(sc, fast=True)
    out = ROOT / "renders" / VER
    out.mkdir(parents=True, exist_ok=True)
    for o in bpy.data.objects:
        if o.name.startswith("SOCK_LANTERN_LOWER_"):
            lamp = bpy.data.lights.new(o.name + "_L", "POINT")
            lamp.energy = 700      # yalnız önizleme ışığı; oyunda UE PointLight ayarlanır
            lamp.color = (1.0, 0.72, 0.45)
            lamp.shadow_soft_size = 0.08
            lo = bpy.data.objects.new("LGT_" + o.name, lamp)
            lo.location = o.matrix_world @ Vector((0.0, 0.285, -0.13))
            sc.collection.objects.link(lo)
    V = Vector
    views = [
        ("iskele_profil", (1.5, -80, 2.9), (1.5, 0, 2.9), None, 48),
        ("sancak_profil", (1.5, 80, 2.9), (1.5, 0, 2.9), None, 48),
        ("bas_omzu", (34, 26, 12), (1, 0, 1.2), 35, None),
        ("kic_omzu", (-34, -24, 11), (-4, 0, 1.6), 35, None),
        ("guverte", (18, 12, 28), (-4, 0, 3.0), 30, None),
        ("ambar_agzi", (-2.5, 2.2, 5.2), (-6.2, 0, 0.5), 30, None),
        ("alt_guverte_ic", (-9.2, 0.6, 1.53), (8.0, -0.4, 1.1), 16, None),
        ("subay_bolmesi", (-14.8, 1.3, 1.95), (-10.5, -0.3, 1.4), 16, None),
        ("kapak_yakin", (-1.0, 12.0, 1.2), (-1.0, 4.8, 0.7), 35, None),
    ]
    for name, loc, tgt, lens, osc in views:
        if osc:
            cam = H.camera(sc, f"CAM13_{name}", V(loc) * K, V(tgt) * K, ortho=osc * K)
        else:
            cam = H.camera(sc, f"CAM13_{name}", V(loc) * K + V((0, 0, DWL)), V(tgt) * K + V((0, 0, DWL)), lens=lens)
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
    assert abs(float(sc.get("ship_scale", 1.0)) - K) < 1e-6
    M = P5.ensure_materials()
    C = {c.name: c for c in bpy.data.collections}
    core, socks, ucx_col = C["10_HULL_CORE"], C["30_SOCKETS"], C["40_COLLISION"]
    n_shift = shift_existing()

    hull = bpy.data.objects["CORE_HULL_SHELL"]
    new = build_lower_ports(core, M, hull)
    lower = H.deck_surface("CORE_DECK_LOWER", 0.012, 0.972, zl, core, M["deck"])
    new.append(place(lower))
    new.append(hatch_cutter(core, bpy.data.objects["CORE_DECK_GUN"]))
    hob, hatch_info = build_hatches(core, M)
    new += hob
    lob, ladders = build_ladders(core, M)
    new += lob
    beams, beam_x = build_beams(core, M)
    new.append(beams)
    gb, bk = build_gunroom_bulkhead(core, M)
    new.append(gb)
    lids, lid_socks = build_lids(C["22_MODULES_CANNONS"], socks, M)
    lans, lan_socks = build_lanterns(C["24_MODULES_DECOR"], socks, M, bk)

    gun_socks = build_lower_sockets(socks)
    nav_socks = build_nav_sockets(socks, ladders, bk)
    moved = update_existing_sockets(socks)
    ucx, ucx_removed, ucx_added = rebuild_collision(ucx_col, hatch_info, ladders, bk)
    sc["hull_class"] = HULL_CLASS
    sc["waterline_lift_world_m"] = DWL
    chk = checks(ladders, bk)

    bpy.ops.wm.save_as_mainfile(filepath=str(out), compress=True)
    H.VERSION = VER
    ap = ROOT / "reports" / f"scene_audit_{VER}.json"
    rep = H.audit(sc, ap)
    core_parts = sorted(o.name for o in core.objects if not o.name.startswith("CUT_"))
    rep["hull_b_v013"] = {
        "hull_class": HULL_CLASS, "waterline_lift_world_m": DWL,
        "draft_world_m": rep["checks"]["draft_from_bounds_m"],
        "checks": chk,
        "lower_gun_x_world": [round(p[2] * K, 2) for p in lower_ports()],
        "hatches_world": {k: {"x": [round(v["x0"] * K, 2), round(v["x1"] * K, 2)], "half_width": round(v["hy"] * K, 2), "kind": v["kind"]}
                          for k, v in hatch_info.items()},
        "ladders": {k: {"angle_deg": v["angle_deg"], "riser_m": round(v["riser_m"] * K, 3), "tread_m": round(v["tread_m"] * K, 3)}
                    for k, v in ladders.items()},
        "gunroom": {"x_front_world": round(XG * K, 2), "door_world_m": [round(DOOR_W * K, 2), round(DOOR_H * K, 2)]},
        "beams_x_world": [round(x * K, 2) for x in beam_x],
        "core_parts": core_parts, "core_count": len(core_parts),
        "modules_added": {"port_lids": len(lids), "wall_lanterns": len(lans)},
        "sockets_added": {"cannon_lower": sum(1 for n in gun_socks if n.startswith("SOCKET_CANNON")),
                          "crew_lower": sum(1 for n in gun_socks if n.startswith("SOCK_CREW")),
                          "port_lid": len(lid_socks), "lantern": len(lan_socks), "nav_station": len(nav_socks)},
        "sockets_total": sum(1 for o in sc.objects if o.type == "EMPTY"),
        "ucx": {"total": len(ucx), "added": ucx_added, "removed_purposes": sorted(set(ucx_removed)), "removed": len(ucx_removed)},
    }
    rep["pass"] = {"name": "pass_v013_hull_b_lower_deck", "source": f"Blender/versions/{SHIP}_{SRC_VER}.blend",
                   "pass_changes": {"shifted_objects_dwl": n_shift, "added": [o.name for o in new],
                                    "modules": [o.name for o in lids + lans], "sockets_moved": moved},
                   "manifest_version": MANIFEST_VERSION,
                   "geometry_changed": "gövde şekli aynı; tüm gemi +DWL; alt güverte, lumbarlar, ambar ağızları, kirişler eklendi"}
    ap.write_text(json.dumps(rep, indent=2, ensure_ascii=False), encoding="utf-8")
    hb = rep["hull_b_v013"]
    print("CHECKS", json.dumps(chk, ensure_ascii=False))
    print("LADDERS", hb["ladders"])
    print("CORE", hb["core_count"], "SOCKETS", hb["sockets_total"], "UCX", hb["ucx"], "BOUNDS", rep["checks"]["bounds_m"],
          "TRIS", rep["checks"]["render_tris_total"])
    if "--no-render" not in sys.argv:
        render(sc)


if __name__ == "__main__":
    main()
