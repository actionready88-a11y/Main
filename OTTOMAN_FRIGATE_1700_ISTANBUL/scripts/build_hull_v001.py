"""OTTOMAN_FRIGATE_1700_ISTANBUL — Hull Core v001 üretici.

Çalıştırma (depo kökünden):
    python3 OTTOMAN_FRIGATE_1700_ISTANBUL/scripts/build_hull_v001.py [--no-render]

Blender 5.x `bpy` modülüyle headless çalışır. Ölçüler ve kaynakları:
reports/MODELLEME_PLANI.md §2. Eksen: X ileri (baş), Z yukarı, su hattı Z=0.
Proje standardına göre +Y = sancak, -Y = iskele (FBX smoke-test'te doğrulanacak).
"""

import json
import math
import os
import sys
from pathlib import Path

import bpy  # noqa: I001 — bmesh, bpy'den sonra yüklenmeli
import bmesh
import numpy as np
from mathutils import Matrix, Vector

SHIP_ID = "OTTOMAN_FRIGATE_1700_ISTANBUL"
VERSION = "v001"
ROOT = Path(__file__).resolve().parents[1]

# --- Ana ölçüler (m) -------------------------------------------------------
L = 35.92        # gundeck boyu — HMS Lyme 1748 (kaynak: plan §2)
B = 10.31        # en — HMS Lyme 1748
T = 4.50         # su çekimi, TAHMİN: B x 0.41-0.48 aralığının ortası
KEEL_D = 0.40    # omurga derinliği (tahmin)
ZK = -T + KEEL_D # kabuğun alt çizgisi (omurga üstü)
ZM = 0.55        # en geniş kesit yüksekliği (tahmin)
TUMBLE = 0.13    # küpeşteye doğru içe çekilme oranı (tahmin)

DECK_MID = 1.90  # batarya güvertesi su hattından yükseklik, orta kesit (tahmin)
QD_H = 2.00      # kıç kasarası / baş kasarası güverte yüksekliği (tahmin)
S_QD = 0.34      # kıç kasarası s<0.34 (s: 0 kıç, 1 baş)
S_FC = 0.83      # baş kasarası s>0.83

NS, NZ = 140, 30  # istasyon ve kesit çözünürlüğü (yarım gövde)

GUNS_PER_SIDE = 12   # HMS Lyme: 24 x 9-pdr batarya güvertesi
QD_GUNS_PER_SIDE = 2 # HMS Lyme: 4 x 3-pdr kıç kasarası
PORT_W, PORT_H, PORT_SILL = 0.62, 0.56, 0.55

# Direk yerleri: HIBRIT_CHATGPT_03 profilinden ölçülen oranlar (s: kıçtan)
MAST_S = {"FORE": 0.815, "MAIN": 0.54, "MIZZEN": 0.245}


# --- Gövde fonksiyonları ---------------------------------------------------
def smooth(a, b, x):
    t = min(max((x - a) / (b - a), 0.0), 1.0)
    return t * t * (3 - 2 * t)


def deck_z(s):
    """Batarya güvertesi sheer eğrisi."""
    if s >= 0.45:
        return DECK_MID + 1.15 * ((s - 0.45) / 0.55) ** 2.2
    return DECK_MID + 1.05 * ((0.45 - s) / 0.45) ** 2.0


def top_z(s):
    """Borda üst kenarı: bel 1.7 m, kasaralarda güverte + QD_H + 1.1 m."""
    waist = deck_z(s) + 1.70
    castle = deck_z(s) + QD_H + 1.10
    w_qd = 1.0 - smooth(S_QD - 0.02, S_QD + 0.03, s)
    w_fc = smooth(S_FC - 0.03, S_FC + 0.02, s)
    return waist + (castle - waist) * max(w_qd, w_fc)


def plan(s):
    """En geniş kesitteki yarı en oranı."""
    if s < 0.36:
        return 0.66 + 0.34 * smooth(0.0, 0.36, s)
    if s <= 0.56:
        return 1.0
    return max(0.0, 1.0 - ((s - 0.56) / 0.44) ** 2.1) ** 0.55


def fullness(s):
    """Süper elips üssü: orta kesit dolgun, uçlar V."""
    if s < 0.40:
        return 1.35 + 0.95 * smooth(0.0, 0.40, s)
    if s <= 0.58:
        return 2.3
    return 2.3 - 0.8 * smooth(0.58, 1.0, s)


def bow_x(z):
    below = min(max(-z / T, 0.0), 1.0)
    return L / 2 - 4.2 * below ** 1.9 + 0.38 * max(z, 0.0)


Z_TR = 1.05  # kıç aynası (wing transom) alt kenarı, su hattından (tahmin)


def stern_x(z):
    """Kıç bodoslaması hattı: omurgadan aynaya ileri eğik, aynadan yukarı kıça yatık."""
    if z <= Z_TR:
        t = min(max((Z_TR - z) / (Z_TR - ZK), 0.0), 1.0)
        return -L / 2 + 1.3 * t ** 1.3
    return -L / 2 - 0.22 * (z - Z_TR)


def stern_close(s, z):
    """Ayna altında gövdeyi kıç bodoslamasına kapatan çarpan (s=0'da 0)."""
    low = 1.0 - smooth(Z_TR - 2.2, Z_TR, z)
    run = smooth(0.0, 0.16, s) ** 0.8
    return 1.0 - low * (1.0 - run)


def half_breadth(s, z):
    bmax = B / 2 * plan(s)
    if z <= ZM:
        t = min((ZM - z) / (ZM - ZK), 1.0)
        n = fullness(s)
        y = bmax * max(1.0 - t ** n, 0.0) ** (1.0 / n)
    else:
        top = top_z(s)
        t = min((z - ZM) / (top - ZM), 1.0)
        y = bmax * (1.0 - TUMBLE * t ** 1.6)
    return max(y * stern_close(s, z), 0.0)


def hull_point(s, z):
    x = stern_x(z) + s * (bow_x(z) - stern_x(z))
    return x, half_breadth(s, z)


# --- Sahne yardımcıları ----------------------------------------------------
def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.unit_settings.system = "METRIC"
    sc.unit_settings.scale_length = 1.0
    return sc


def collection(name, parent=None):
    col = bpy.data.collections.new(name)
    (parent or bpy.context.scene.collection).children.link(col)
    return col


def obj_from_bmesh(name, bm, col, mats=()):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for m in mats:
        me.materials.append(m)
    ob = bpy.data.objects.new(name, me)
    col.objects.link(ob)
    for p in me.polygons:
        p.use_smooth = True
    return ob


def empty(name, loc, col, size=0.4, shape="ARROWS", rot=(0, 0, 0)):
    e = bpy.data.objects.new(name, None)
    e.empty_display_type = shape
    e.empty_display_size = size
    e.location = loc
    e.rotation_euler = rot
    col.objects.link(e)
    return e


# --- Materyaller (prosedürel PBR, önizleme) ---------------------------------
def principled(name, base, rough=0.7, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*base, 1)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    return m, nt, bsdf


def plank_material(name, base, dark, plank_w=0.26, rough=0.72, seam=0.012, bump=0.25, below_wl=None):
    """UV (metre) üzerinde kaplama tahtası: v yönünde bantlar, u yönünde ek yerleri."""
    m, nt, bsdf = principled(name, base, rough)
    N, Lk = nt.nodes, nt.links
    uv = N.new("ShaderNodeTexCoord")
    sep = N.new("ShaderNodeSeparateXYZ")
    Lk.new(uv.outputs["UV"], sep.inputs[0])
    # tahta indeksi
    div = N.new("ShaderNodeMath"); div.operation = "DIVIDE"
    div.inputs[1].default_value = plank_w
    Lk.new(sep.outputs["Y"], div.inputs[0])
    fl = N.new("ShaderNodeMath"); fl.operation = "FLOOR"
    Lk.new(div.outputs[0], fl.inputs[0])
    frac = N.new("ShaderNodeMath"); frac.operation = "FRACT"
    Lk.new(div.outputs[0], frac.inputs[0])
    # ek yeri çizgisi (tahta kenarı)
    edge = N.new("ShaderNodeMapRange")
    Lk.new(frac.outputs[0], edge.inputs["Value"])
    edge.inputs["From Min"].default_value = 0.0
    edge.inputs["From Max"].default_value = seam / plank_w
    edge.clamp = True
    # tahta başına renk sapması + uç ekleri (u yönünde 6 m, kaydırmalı)
    rnd = N.new("ShaderNodeTexWhiteNoise"); rnd.noise_dimensions = "1D"
    Lk.new(fl.outputs[0], rnd.inputs["W"])
    butt_add = N.new("ShaderNodeMath"); butt_add.operation = "MULTIPLY_ADD"
    Lk.new(fl.outputs[0], butt_add.inputs[0])
    butt_add.inputs[1].default_value = 1.7
    Lk.new(sep.outputs["X"], butt_add.inputs[2])
    bdiv = N.new("ShaderNodeMath"); bdiv.operation = "DIVIDE"
    bdiv.inputs[1].default_value = 6.0
    Lk.new(butt_add.outputs[0], bdiv.inputs[0])
    bfr = N.new("ShaderNodeMath"); bfr.operation = "FRACT"
    Lk.new(bdiv.outputs[0], bfr.inputs[0])
    bedge = N.new("ShaderNodeMapRange"); bedge.clamp = True
    Lk.new(bfr.outputs[0], bedge.inputs["Value"])
    bedge.inputs["From Max"].default_value = 0.004
    seams = N.new("ShaderNodeMath"); seams.operation = "MINIMUM"
    Lk.new(edge.outputs[0], seams.inputs[0]); Lk.new(bedge.outputs[0], seams.inputs[1])
    # damar
    noise = N.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 3.0
    noise.inputs["Detail"].default_value = 8.0
    noise.inputs["Roughness"].default_value = 0.62
    mapn = N.new("ShaderNodeMapping")
    mapn.inputs["Scale"].default_value = (0.25, 4.0, 1.0)
    Lk.new(uv.outputs["UV"], mapn.inputs[0])
    Lk.new(mapn.outputs[0], noise.inputs["Vector"])
    grime = N.new("ShaderNodeTexNoise")
    grime.inputs["Scale"].default_value = 0.6
    grime.inputs["Detail"].default_value = 6.0
    Lk.new(uv.outputs["UV"], grime.inputs["Vector"])
    mix1 = N.new("ShaderNodeMix"); mix1.data_type = "RGBA"
    mix1.inputs["A"].default_value = (*dark, 1)
    mix1.inputs["B"].default_value = (*base, 1)
    fac = N.new("ShaderNodeMath"); fac.operation = "MULTIPLY_ADD"
    Lk.new(noise.outputs["Fac"], fac.inputs[0])
    fac.inputs[1].default_value = 0.7
    Lk.new(rnd.outputs["Value"], fac.inputs[2])
    Lk.new(fac.outputs[0], mix1.inputs["Factor"])
    mix2 = N.new("ShaderNodeMix"); mix2.data_type = "RGBA"
    Lk.new(grime.outputs["Fac"], mix2.inputs["Factor"])
    Lk.new(mix1.outputs["Result"], mix2.inputs["A"])
    mix2.inputs["B"].default_value = (*[c * 0.55 for c in dark], 1)
    mix2.blend_type = "MULTIPLY"
    mix3 = N.new("ShaderNodeMix"); mix3.data_type = "RGBA"
    Lk.new(seams.outputs[0], mix3.inputs["Factor"])
    mix3.inputs["A"].default_value = (0.012, 0.009, 0.007, 1)
    Lk.new(mix2.outputs["Result"], mix3.inputs["B"])
    color_out = mix3.outputs["Result"]
    if below_wl is not None:
        # su hattı (Z=0) üstünde 0,12 m'lik düz boya sınırı; altında daha açık ton
        geo = N.new("ShaderNodeNewGeometry")
        gz = N.new("ShaderNodeSeparateXYZ")
        Lk.new(geo.outputs["Position"], gz.inputs[0])
        wl = N.new("ShaderNodeMapRange"); wl.clamp = True
        Lk.new(gz.outputs["Z"], wl.inputs["Value"])
        wl.inputs["From Min"].default_value = 0.11
        wl.inputs["From Max"].default_value = 0.13
        wl.inputs["To Min"].default_value = 1.0
        wl.inputs["To Max"].default_value = 0.0
        tint = N.new("ShaderNodeMix"); tint.data_type = "RGBA"
        tint.inputs["Factor"].default_value = 0.7
        Lk.new(mix3.outputs["Result"], tint.inputs["A"])
        tint.inputs["B"].default_value = (*below_wl, 1)
        wmix = N.new("ShaderNodeMix"); wmix.data_type = "RGBA"
        Lk.new(wl.outputs["Result"], wmix.inputs["Factor"])
        Lk.new(mix3.outputs["Result"], wmix.inputs["A"])
        Lk.new(tint.outputs["Result"], wmix.inputs["B"])
        color_out = wmix.outputs["Result"]
    Lk.new(color_out, bsdf.inputs["Base Color"])
    bmp = N.new("ShaderNodeBump")
    bmp.inputs["Strength"].default_value = bump
    bmp.inputs["Distance"].default_value = 0.01
    hmix = N.new("ShaderNodeMath"); hmix.operation = "MULTIPLY_ADD"
    Lk.new(noise.outputs["Fac"], hmix.inputs[0])
    hmix.inputs[1].default_value = 0.15
    Lk.new(seams.outputs[0], hmix.inputs[2])
    Lk.new(hmix.outputs[0], bmp.inputs["Height"])
    Lk.new(bmp.outputs["Normal"], bsdf.inputs["Normal"])
    return m


def build_materials():
    M = {}
    M["hull"] = plank_material("MAT_Hull_TarredOak", (0.055, 0.040, 0.032), (0.020, 0.016, 0.014), rough=0.62,
                               below_wl=(0.15, 0.13, 0.10))
    M["band"] = plank_material("MAT_Hull_RedBand", (0.30, 0.035, 0.025), (0.14, 0.018, 0.014), rough=0.55, bump=0.15)
    M["inner"] = plank_material("MAT_Bulwark_InnerRed", (0.26, 0.05, 0.03), (0.12, 0.03, 0.02), rough=0.6, bump=0.1)
    M["deck"] = plank_material("MAT_Deck_Pine", (0.36, 0.27, 0.18), (0.17, 0.12, 0.08), plank_w=0.22, rough=0.78, seam=0.008)
    M["gold"], _, b = principled("MAT_Trim_Gilt", (0.62, 0.43, 0.14), rough=0.35, metal=0.85)
    M["yellow"], _, _ = principled("MAT_Trim_YellowOchre", (0.52, 0.34, 0.08), rough=0.55)
    M["timber"] = plank_material("MAT_Timber_Oak", (0.12, 0.08, 0.05), (0.05, 0.035, 0.025), plank_w=0.4, rough=0.7)
    M["iron"], _, _ = principled("MAT_Iron_Black", (0.03, 0.03, 0.03), rough=0.5, metal=0.9)
    M["dark"], _, _ = principled("MAT_PortInterior", (0.01, 0.008, 0.006), rough=0.9)
    return M


# --- Gövde kabuğu ----------------------------------------------------------
def build_hull_shell(col, M):
    """Yarım gövde ızgarası, simetrik ayna. Malzeme indeksi yüksekliğe göre."""
    bm = bmesh.new()
    uv_layer = bm.loops.layers.uv.new("UVMap")
    grid = {}
    girth = np.zeros((NS + 1, NZ + 1))
    for side in (1, -1):
        for i in range(NS + 1):
            s = i / NS
            top = top_z(s)
            prev = None
            for j in range(NZ + 1):
                # alt tarafta daha sık örnekleme
                t = j / NZ
                z = ZK + (top - ZK) * (0.5 - 0.5 * math.cos(math.pi * t)) ** 0.9
                x, y = hull_point(s, z)
                y = max(y, 0.15)  # omurga yarı genişliği (0.12 iç yüzlerin çakışmasına yol açıyordu)
                co = Vector((x, side * y, z))
                if side == 1:
                    if prev is not None:
                        girth[i, j] = girth[i, j - 1] + (co - prev).length
                    prev = co
                grid[(side, i, j)] = bm.verts.new(co)
    for side in (1, -1):
        for i in range(NS):
            for j in range(NZ):
                vs = [grid[(side, i, j)], grid[(side, i + 1, j)],
                      grid[(side, i + 1, j + 1)], grid[(side, i, j + 1)]]
                if side == -1:
                    vs.reverse()
                f = bm.faces.new(vs)
                zc = sum(v.co.z for v in vs) / 4
                s = (i + 0.5) / NS
                dz = deck_z(s)
                if zc > dz + 1.28:
                    f.material_index = 2
                else:
                    f.material_index = 0
                ij = [(i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)]
                if side == -1:
                    ij.reverse()
                for loop, (a, b) in zip(f.loops, ij):
                    loop[uv_layer].uv = (loop.vert.co.x, girth[a, b] * side)
    # kıç aynası: yalnız ayna bölgesi (y > 0.15), ızgara halinde (n-gon yok)
    NC = 10
    rows = [j for j in range(NZ + 1) if grid[(1, 0, j)].co.y > 0.18]
    tgrid = {}
    for j in rows:
        a, b = grid[(1, 0, j)], grid[(-1, 0, j)]
        for c in range(NC + 1):
            if c == 0:
                tgrid[(j, c)] = a
            elif c == NC:
                tgrid[(j, c)] = b
            else:
                tgrid[(j, c)] = bm.verts.new(a.co.lerp(b.co, c / NC))
    for j0, j1 in zip(rows[:-1], rows[1:]):
        for c in range(NC):
            f = bm.faces.new([tgrid[(j0, c)], tgrid[(j0, c + 1)], tgrid[(j1, c + 1)], tgrid[(j1, c)]])
            zc = sum(v.co.z for v in f.verts) / 4
            f.material_index = 2 if zc > Z_TR - 0.05 else 0
            for loop in f.loops:
                loop[uv_layer].uv = (loop.vert.co.y, loop.vert.co.z)
    # ayna alt kenarı: iki yarıyı bağlayan tek şerit
    j0 = rows[0]
    if j0 > 0:
        for j in range(j0):
            f = bm.faces.new([grid[(1, 0, j)], grid[(1, 0, j + 1)], grid[(-1, 0, j + 1)], grid[(-1, 0, j)]])
            f.material_index = 0
    # alt dikiş: iki yarının alt kenarı arasındaki şerit
    for i in range(NS):
        f = bm.faces.new([grid[(1, i, 0)], grid[(-1, i, 0)], grid[(-1, i + 1, 0)], grid[(1, i + 1, 0)]])
        f.material_index = 0
    crease = bm.edges.layers.float.new("crease_edge")
    for side in (1, -1):
        for j in range(NZ):
            for i in (0, NS):
                e = bm.edges.get([grid[(side, i, j)], grid[(side, i, j + 1)]])
                if e:
                    e[crease] = 1.0
        for i in range(NS):
            e = bm.edges.get([grid[(side, i, 0)], grid[(side, i + 1, 0)]])
            if e:
                e[crease] = 1.0
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
    bm.normal_update()
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = obj_from_bmesh("CORE_HULL_SHELL", bm, col, [M["hull"], M["inner"], M["band"], M["inner"]])
    sub = ob.modifiers.new("Subdivision", "SUBSURF")
    sub.levels = 1
    sub.render_levels = 2
    sol = ob.modifiers.new("Solidify", "SOLIDIFY")
    sol.thickness = 0.24
    sol.offset = -1.0
    sol.use_even_offset = True
    sol.material_offset = 3  # iç yüz -> iskele/iç kırmızı (index 3)
    sol.material_offset_rim = 2
    return ob


def build_uv_fallback(ob):
    """Izgara dışı yüzlerde UV'yi metre ölçekli kutu projeksiyonuyla tamamla."""
    me = ob.data
    if not me.uv_layers:
        me.uv_layers.new(name="UVMap")
    uv = me.uv_layers.active.data
    for p in me.polygons:
        n = p.normal
        for li in p.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            if abs(n.z) > max(abs(n.x), abs(n.y)):
                uv[li].uv = (co.x, co.y)
            elif abs(n.y) > abs(n.x):
                uv[li].uv = (co.x, co.z)
            else:
                uv[li].uv = (co.y, co.z)


# --- Kuşak/wale şeritleri --------------------------------------------------
def band_strip(name, z_of_s, height, depth, col, mat, s0=0.0, s1=1.0, n=120):
    """Gövde yüzeyi boyunca uzanan dikdörtgen kesitli şerit (wale, silme)."""
    bm = bmesh.new()
    rows = []
    for side in (1, -1):
        rows = []
        for i in range(n + 1):
            s = s0 + (s1 - s0) * i / n
            zc = z_of_s(s)
            ring = []
            for dz, dd in ((-height / 2, 0.0), (-height / 2, depth), (height / 2, depth), (height / 2, 0.0)):
                x, y = hull_point(s, zc + dz)
                if y < 0.2:
                    y = 0.2
                ring.append(bm.verts.new((x, side * (y + dd - 0.01), zc + dz)))
            rows.append(ring)
        for i in range(n):
            for k in range(3):
                vs = [rows[i][k], rows[i + 1][k], rows[i + 1][k + 1], rows[i][k + 1]]
                if side == 1:
                    vs.reverse()
                bm.faces.new(vs)
        for ring in (rows[0], rows[-1]):
            bm.faces.new(ring if side == -1 else list(reversed(ring)))
    bm.normal_update()
    ob = obj_from_bmesh(name, bm, col, [mat])
    bmesh_fix_normals(ob)
    bev = ob.modifiers.new("Bevel", "BEVEL")
    bev.width = min(height, depth) * 0.2
    bev.segments = 2
    build_uv_fallback(ob)
    return ob


def bmesh_fix_normals(ob):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(ob.data)
    bm.free()


# --- Güverteler ------------------------------------------------------------
def deck_surface(name, s0, s1, z_fn, col, mat, inset=0.24, n=90, m=16):
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    rows = []
    for i in range(n + 1):
        s = s0 + (s1 - s0) * i / n
        z = z_fn(s)
        x, y = hull_point(s, z)
        y = max(y - inset, 0.05)
        camber = 0.12
        row = []
        for k in range(m + 1):
            v = -1 + 2 * k / m
            row.append(bm.verts.new((x, v * y, z + camber * (1 - v * v))))
        rows.append(row)
    for i in range(n):
        for k in range(m):
            f = bm.faces.new([rows[i][k], rows[i + 1][k], rows[i + 1][k + 1], rows[i][k + 1]])
            for loop in f.loops:
                # tahtalar boyuna (X) uzanır: v = y
                loop[uvl].uv = (loop.vert.co.x, loop.vert.co.y)
    ob = obj_from_bmesh(name, bm, col, [mat])
    sol = ob.modifiers.new("Solidify", "SOLIDIFY")
    sol.thickness = 0.10
    sol.offset = -1
    return ob


# --- Omurga, bodoslama, kıç bodoslaması -------------------------------------
def sweep_profile(name, pts, width, col, mat, depth_out=0.0):
    """Orta hatta (Y=0) nokta dizisi boyunca dikdörtgen kesitli ağaç."""
    bm = bmesh.new()
    rings = []
    for i, p in enumerate(pts):
        p = Vector(p)
        a = Vector(pts[max(i - 1, 0)]); b = Vector(pts[min(i + 1, len(pts) - 1)])
        tan = (b - a).normalized()
        nrm = Vector((tan.z, 0, -tan.x))  # XZ düzleminde dik
        w = width / 2
        d = depth_out
        ring = [bm.verts.new(p + nrm * d + Vector((0, -w, 0))),
                bm.verts.new(p + nrm * d + Vector((0, w, 0))),
                bm.verts.new(p - nrm * 0.25 + Vector((0, w, 0))),
                bm.verts.new(p - nrm * 0.25 + Vector((0, -w, 0)))]
        rings.append(ring)
    for i in range(len(rings) - 1):
        for k in range(4):
            bm.faces.new([rings[i][k], rings[i + 1][k], rings[i + 1][(k + 1) % 4], rings[i][(k + 1) % 4]])
    bm.faces.new(rings[0]); bm.faces.new(list(reversed(rings[-1])))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = obj_from_bmesh(name, bm, col, [mat])
    bev = ob.modifiers.new("Bevel", "BEVEL"); bev.width = 0.03; bev.segments = 2
    build_uv_fallback(ob)
    return ob


def build_backbone(col, M):
    x0 = stern_x(-T) - 0.25            # kıç bodoslamasının arka yüzü (topuk)
    x1 = bow_x(-T + 0.25) + 0.15       # bodoslamanın alt ucuyla bindirme
    keel_pts = [(x, 0, -T + 0.25) for x in np.linspace(x0, x1, 26)]
    keel = sweep_profile("CORE_KEEL", keel_pts, 0.42, col, M["hull"], depth_out=0.25)
    # bodoslama: baş eğrisi boyunca, omurgadan küpeşteye
    stem_pts = []
    for z in np.linspace(-T + 0.25, top_z(1.0) - 0.1, 36):
        stem_pts.append((bow_x(z) + 0.02, 0, z))
    stem = sweep_profile("CORE_STEM", stem_pts, 0.40, col, M["hull"], depth_out=0.18)
    post_pts = [(stern_x(z) + 0.02, 0, z) for z in np.linspace(-T + 0.25, Z_TR + 0.7, 20)]
    post = sweep_profile("CORE_STERNPOST", post_pts, 0.40, col, M["hull"], depth_out=0.25)  # gövde çizgisinin 0,25 m iç ve 0,25 m dışı
    return [keel, stem, post]


# --- Baş (head) yapısı -----------------------------------------------------
def build_head(col, M):
    """Baş bodoslaması önünde kıvrık 'knee of the head' ve yan kıvrım rayları."""
    pts = []
    z0 = 0.3
    for t in np.linspace(0, 1, 30):
        z = z0 + t * (deck_z(1.0) + 1.2 - z0)
        x = bow_x(z) + 0.3 + 2.6 * math.sin(t * math.pi * 0.55) ** 1.4
        pts.append((x, 0, z))
    knee = sweep_profile("CORE_HEAD_KNEE", pts, 0.34, col, M["timber"], depth_out=0.15)
    rails = []
    for side in (1, -1):
        bm = bmesh.new()
        crv = []
        for t in np.linspace(0, 1, 24):
            s = 0.97 + 0.03 * t
            z = deck_z(1.0) + 0.2 + 0.9 * t ** 1.5
            x = bow_x(z) + 2.3 * t
            y = side * (1.2 * (1 - t) + 0.25)
            crv.append(Vector((x, y, z)))
        rings = []
        for c in crv:
            r = [bm.verts.new(c + Vector(o)) for o in ((0, 0.06, 0.08), (0, -0.06, 0.08), (0, -0.06, -0.08), (0, 0.06, -0.08))]
            rings.append(r)
        for i in range(len(rings) - 1):
            for k in range(4):
                bm.faces.new([rings[i][k], rings[i + 1][k], rings[i + 1][(k + 1) % 4], rings[i][(k + 1) % 4]])
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        ob = obj_from_bmesh(f"CORE_HEAD_RAIL_{'S' if side > 0 else 'P'}", bm, col, [M["gold"]])
        build_uv_fallback(ob)
        rails.append(ob)
    return [knee] + rails


# --- Top lumbarları --------------------------------------------------------
def port_positions():
    """Batarya güvertesi (12/borda) ve kıç kasarası (2/borda) lumbar merkezleri."""
    ports = []
    xs = np.linspace(-13.4, 12.6, GUNS_PER_SIDE)
    for k, x in enumerate(xs):
        s = (x - stern_x(2)) / (bow_x(2) - stern_x(2))
        z = deck_z(s) + PORT_SILL + PORT_H / 2
        ports.append(("MAIN", k + 1, x, s, z))
    for k, x in enumerate((-12.6, -10.2)):
        s = (x - stern_x(4)) / (bow_x(4) - stern_x(4))
        z = deck_z(s) + QD_H + 0.40 + 0.22
        ports.append(("QD", k + 1, x, s, z))
    return ports


def build_port_cutters(col, hull):
    cutters = []
    bm = bmesh.new()
    for kind, idx, x, s, z in port_positions():
        w = PORT_W if kind == "MAIN" else 0.44
        h = PORT_H if kind == "MAIN" else 0.40
        _, y = hull_point(s, z)
        for side in (1, -1):
            ret = bmesh.ops.create_cube(bm, size=1.0)
            vs = ret["verts"]
            bmesh.ops.scale(bm, vec=(w, 1.2, h), verts=vs)
            bmesh.ops.translate(bm, vec=(x, side * y, z), verts=vs)
    # kovalama lumbarları: baş (2) ve kıç aynası (2)
    for side in (1, -1):
        z = deck_z(0.96) + PORT_SILL + 0.28
        s = 0.955
        x, y = hull_point(s, z)
        ret = bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=(1.4, 0.55, 0.5), verts=ret["verts"])
        bmesh.ops.rotate(bm, cent=Vector((0, 0, 0)), matrix=Matrix.Rotation(math.radians(side * 38), 3, "Z"), verts=ret["verts"])
        bmesh.ops.translate(bm, vec=(x, side * (y - 0.1), z), verts=ret["verts"])
        z = deck_z(0.0) + PORT_SILL + 0.28
        ret = bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=(1.6, 0.55, 0.5), verts=ret["verts"])
        bmesh.ops.translate(bm, vec=(stern_x(z), side * 1.6, z), verts=ret["verts"])
    ob = obj_from_bmesh("CUT_GUNPORTS", bm, col)
    ob.display_type = "WIRE"
    ob.hide_render = True
    mod = hull.modifiers.new("GunPorts", "BOOLEAN")
    mod.operation = "DIFFERENCE"
    mod.object = ob
    mod.solver = "EXACT"
    return ob


def build_port_frames(col, M):
    """Lumbar çerçeveleri (sarı-altın silme) ve iç karanlık yüz."""
    bm = bmesh.new()
    for kind, idx, x, s, z in port_positions():
        w = PORT_W if kind == "MAIN" else 0.44
        h = PORT_H if kind == "MAIN" else 0.40
        _, y = hull_point(s, z)
        for side in (1, -1):
            yy = side * (y + 0.02)
            t = 0.07
            for (cx, cz, sx, sz) in ((x, z + h / 2 + t / 2, w + 2 * t, t), (x, z - h / 2 - t / 2, w + 2 * t, t),
                                      (x - w / 2 - t / 2, z, t, h), (x + w / 2 + t / 2, z, t, h)):
                ret = bmesh.ops.create_cube(bm, size=1.0)
                bmesh.ops.scale(bm, vec=(sx, 0.06, sz), verts=ret["verts"])
                bmesh.ops.translate(bm, vec=(cx, yy, cz), verts=ret["verts"])
    ob = obj_from_bmesh("CORE_GUNPORT_FRAMES", bm, col, [M["yellow"]])
    for p in ob.data.polygons:
        p.use_smooth = False
    build_uv_fallback(ob)
    return ob


def build_breast_rails(col, M):
    """Kıç kasarası ön kenarı ve baş kasarası arka kenarında korkuluk + torna balüsterler."""
    obs = []
    for name, s in (("QD", S_QD), ("FC", S_FC)):
        z0 = deck_z(s) + QD_H + 0.10
        x, y = hull_point(s, z0)
        y -= 0.30
        bm = bmesh.new()
        for zc, h in ((z0 + 0.95, 0.12), (z0 + 0.06, 0.10)):
            r = bmesh.ops.create_cube(bm, size=1.0)
            bmesh.ops.scale(bm, vec=(0.16, 2 * y, h), verts=r["verts"])
            bmesh.ops.translate(bm, vec=(x, 0, zc), verts=r["verts"])
        n = max(int(2 * y / 0.32), 4)
        for k in range(n + 1):
            yy = -y + 2 * y * k / n
            r = bmesh.ops.create_cone(bm, cap_ends=True, segments=12, radius1=0.055, radius2=0.035, depth=0.8)
            bmesh.ops.translate(bm, vec=(x, yy, z0 + 0.5), verts=r["verts"])
        ob = obj_from_bmesh(f"CORE_BREAST_RAIL_{name}", bm, col, [M["yellow"]])
        bev = ob.modifiers.new("Bevel", "BEVEL"); bev.width = 0.015; bev.segments = 2
        build_uv_fallback(ob)
        obs.append(ob)
    return obs


# --- Modüller (yer tutucu olmayan, basit ilk sürüm) --------------------------
def build_rudder(col, M):
    pts = [(stern_x(z) - 0.30, 0, z) for z in np.linspace(-T + 0.3, Z_TR + 0.5, 22)]
    bm = bmesh.new()
    rings = []
    for i, p in enumerate(pts):
        z = p[2]
        chord = 1.15 if z < -0.8 else 1.15 - 0.75 * smooth(-0.8, Z_TR + 0.5, z)
        c = Vector(p)
        r = [bm.verts.new(c + Vector(o)) for o in ((0.12, -0.17, 0), (0.12, 0.17, 0), (-chord, 0.07, 0), (-chord, -0.07, 0))]
        rings.append(r)
    for i in range(len(rings) - 1):
        for k in range(4):
            bm.faces.new([rings[i][k], rings[i + 1][k], rings[i + 1][(k + 1) % 4], rings[i][(k + 1) % 4]])
    bm.faces.new(rings[0]); bm.faces.new(list(reversed(rings[-1])))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = obj_from_bmesh("MOD_RUDDER_STERNPOST_A", bm, col, [M["hull"]])
    bev = ob.modifiers.new("Bevel", "BEVEL"); bev.width = 0.04; bev.segments = 2
    build_uv_fallback(ob)
    return ob


# --- Soketler, çarpışma ----------------------------------------------------
def build_sockets(col, rudder):
    socks = {}

    def add(name, loc, rot=(0, 0, 0), shape="ARROWS"):
        socks[name] = empty(name, loc, col, rot=rot, shape=shape)

    for mast, s in MAST_S.items():
        dz = deck_z(s)
        x, _ = hull_point(s, dz)
        add(f"SOCKET_MAST_{mast}", (x, 0, dz), shape="SINGLE_ARROW")
    add("SOCKET_RIG_PRIMARY", (hull_point(MAST_S["MAIN"], 0)[0], 0, deck_z(MAST_S["MAIN"])))
    add("SOCKET_RUDDER", (stern_x(0) - 0.30, 0, 0.0))
    rudder.parent = None
    rudder.location = (0, 0, 0)
    add("SOCKET_FIGUREHEAD", (bow_x(deck_z(1.0)) + 2.7, 0, deck_z(1.0) + 1.05))
    add("SOCKET_STERN_MODULE", (stern_x(deck_z(0.0) + 2.0), 0, deck_z(0.0) + 2.0))
    for kind, idx, x, s, z in port_positions():
        _, y = hull_point(s, z)
        tag = "" if kind == "MAIN" else "QD_"
        dz = deck_z(s) + (0 if kind == "MAIN" else QD_H)
        add(f"SOCKET_CANNON_S_{tag}{idx:02d}", (x, y - 1.2, dz), rot=(0, 0, math.radians(-90)))
        add(f"SOCKET_CANNON_P_{tag}{idx:02d}", (x, -(y - 1.2), dz), rot=(0, 0, math.radians(90)))
    add("SOCKET_CANNON_CHASE_BOW_S", (hull_point(0.95, 2.5)[0] - 1.0, 1.0, deck_z(0.95)))
    add("SOCKET_CANNON_CHASE_BOW_P", (hull_point(0.95, 2.5)[0] - 1.0, -1.0, deck_z(0.95)))
    add("SOCKET_CANNON_CHASE_STERN_S", (stern_x(2.5) + 1.2, 1.6, deck_z(0.0)), rot=(0, 0, math.pi))
    add("SOCKET_CANNON_CHASE_STERN_P", (stern_x(2.5) + 1.2, -1.6, deck_z(0.0)), rot=(0, 0, math.pi))
    for side, tag in ((1, "STARBOARD"), (-1, "PORT")):
        x, y = hull_point(0.9, deck_z(0.9))
        add(f"SOCKET_ANCHOR_{tag}", (x, side * (y + 0.2), deck_z(0.9) + 0.6))
    add("SOCKET_BOAT_PRIMARY", (0.5, 0, deck_z(0.5) + 0.3))
    add("SOCKET_FLAG_STERN", (stern_x(top_z(0)) - 0.4, 0, top_z(0.0)))
    add("SOCK_COM", (-0.6, 0, -1.0), shape="SPHERE")
    k = 0
    for s in np.linspace(0.12, 0.9, 8):
        for side in (1, -1):
            k += 1
            x, y = hull_point(s, -1.2)
            add(f"SOCK_BUOY_{k:02d}", (x, side * y * 0.6, -1.2), shape="SPHERE")
    return socks


def build_collision(col, hull_shell):
    """Gövde kabuğundan 4 dilimli dışbükey UCX parçaları."""
    dg = bpy.context.evaluated_depsgraph_get()
    ev = hull_shell.evaluated_get(dg)
    me = ev.to_mesh()
    pts = [v.co.copy() for v in me.vertices]
    ev.to_mesh_clear()
    edges = np.linspace(-L / 2 - 1.5, L / 2 + 1.5, 5)
    obs = []
    for k in range(4):
        sel = [p for p in pts if edges[k] - 0.3 <= p.x <= edges[k + 1] + 0.3]
        bm = bmesh.new()
        for p in sel:
            bm.verts.new(p)
        bmesh.ops.convex_hull(bm, input=bm.verts)
        loose = [v for v in bm.verts if not v.link_faces]
        bmesh.ops.delete(bm, geom=loose, context="VERTS")
        ob = obj_from_bmesh(f"UCX_CORE_HULL_SHELL_{k:02d}", bm, col)
        ob.display_type = "WIRE"
        ob.hide_render = True
        obs.append(ob)
    return obs


# --- Render ----------------------------------------------------------------
def setup_render(sc, fast=False):
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = 48 if fast else 96
    sc.cycles.use_denoising = True
    sc.render.resolution_x = 1600
    sc.render.resolution_y = 900
    sc.render.film_transparent = False
    sc.view_settings.view_transform = "AgX"
    world = bpy.data.worlds.new("World")
    sc.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.20, 0.205, 0.21, 1)
    bg.inputs["Strength"].default_value = 0.9
    sun = bpy.data.lights.new("Sun", "SUN")
    sun.energy = 3.2
    sun.angle = math.radians(8)
    so = bpy.data.objects.new("LGT_Sun", sun)
    so.rotation_euler = (math.radians(50), math.radians(12), math.radians(-35))
    sc.collection.objects.link(so)
    fill = bpy.data.lights.new("Fill", "AREA")
    fill.energy = 2500
    fill.size = 20
    fo = bpy.data.objects.new("LGT_Fill", fill)
    fo.location = (-25, -30, 12)
    fo.rotation_euler = (math.radians(70), 0, math.radians(-40))
    sc.collection.objects.link(fo)


def camera(sc, name, loc, target, ortho=None, lens=50):
    cam = bpy.data.cameras.new(name)
    if ortho:
        cam.type = "ORTHO"
        cam.ortho_scale = ortho
    else:
        cam.lens = lens
    cam.clip_end = 500
    ob = bpy.data.objects.new(name, cam)
    ob.location = loc
    d = Vector(target) - Vector(loc)
    ob.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    sc.collection.objects.link(ob)
    return ob


def render_views(sc, out_dir):
    out_dir.mkdir(parents=True, exist_ok=True)
    zc = 1.0
    views = {
        "bas": ((60, 0, zc), (0, 0, zc), 22),
        "kic": ((-60, 0, zc), (0, 0, zc), 22),
        "iskele_profil": ((0, -80, zc), (0, 0, zc), 44),
        "sancak_profil": ((0, 80, zc), (0, 0, zc), 44),
    }
    paths = []
    for name, (loc, tgt, osc) in views.items():
        sc.camera = camera(sc, f"CAM_{name}", loc, tgt, ortho=osc)
        p = out_dir / f"{SHIP_ID}_{VERSION}_{name}.png"
        sc.render.filepath = str(p)
        bpy.ops.render.render(write_still=True)
        paths.append(p)
    persp = {
        "bas_omzu": ((34, 26, 12), (2, 0, 0.5), 35),
        "kic_omzu": ((-32, -25, 11), (-2, 0, 0.5), 35),
        "guverte": ((22, 14, 26), (-1, 0, 1.5), 32),
    }
    for name, (loc, tgt, lens) in persp.items():
        sc.camera = camera(sc, f"CAM_{name}", loc, tgt, lens=lens)
        p = out_dir / f"{SHIP_ID}_{VERSION}_{name}.png"
        sc.render.filepath = str(p)
        bpy.ops.render.render(write_still=True)
        paths.append(p)
    return paths


# --- Denetim (audit) -------------------------------------------------------
def audit(sc, path):
    dg = bpy.context.evaluated_depsgraph_get()
    rep = {"ship_id": SHIP_ID, "version": VERSION, "blender": bpy.app.version_string,
           "unit_scale": sc.unit_settings.scale_length, "objects": [], "checks": {}}
    tri_total = 0
    zmin, zmax = 1e9, -1e9
    xmin, xmax, ymax = 1e9, -1e9, 0
    missing_uv, no_mat = [], []
    for ob in sc.objects:
        entry = {"name": ob.name, "type": ob.type,
                 "collection": ob.users_collection[0].name if ob.users_collection else None,
                 "location": [round(c, 4) for c in ob.location],
                 "scale": [round(c, 4) for c in ob.scale]}
        if ob.type == "MESH":
            ev = ob.evaluated_get(dg)
            me = ev.to_mesh()
            me.calc_loop_triangles()
            tris = len(me.loop_triangles)
            entry.update({"verts": len(me.vertices), "tris": tris,
                          "materials": [m.name for m in ob.data.materials if m],
                          "uv_layers": [u.name for u in ob.data.uv_layers],
                          "modifiers": [m.type for m in ob.modifiers]})
            if not ob.name.startswith(("UCX_", "CUT_")):
                tri_total += tris
                if not ob.data.uv_layers:
                    missing_uv.append(ob.name)
                if not ob.data.materials:
                    no_mat.append(ob.name)
                for v in me.vertices:
                    w = ob.matrix_world @ v.co
                    zmin = min(zmin, w.z); zmax = max(zmax, w.z)
                    xmin = min(xmin, w.x); xmax = max(xmax, w.x); ymax = max(ymax, abs(w.y))
            ev.to_mesh_clear()
        rep["objects"].append(entry)
    rep["checks"] = {
        "render_tris_total": tri_total,
        "bounds_m": {"x": [round(xmin, 3), round(xmax, 3)], "half_beam_max": round(ymax, 3),
                     "z": [round(zmin, 3), round(zmax, 3)]},
        "waterline_z": 0.0,
        "draft_from_bounds_m": round(-zmin, 3),
        "missing_uv": missing_uv,
        "missing_material": no_mat,
        "images_missing": [i.name for i in bpy.data.images if i.source == "FILE" and not os.path.exists(bpy.path.abspath(i.filepath))],
        "non_unit_scale": [o.name for o in sc.objects if tuple(round(c, 4) for c in o.scale) != (1.0, 1.0, 1.0)],
        "sockets": sorted(o.name for o in sc.objects if o.type == "EMPTY"),
        "collections": [c.name for c in sc.collection.children],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rep, indent=2, ensure_ascii=False), encoding="utf-8")
    return rep


def main():
    no_render = "--no-render" in sys.argv
    sc = reset_scene()
    names = ["00_REFERENCE", "10_HULL_CORE", "20_MODULES_RIG", "21_MODULES_SAILS", "22_MODULES_CANNONS",
             "23_MODULES_DECK", "24_MODULES_DECOR", "30_SOCKETS", "40_COLLISION", "50_LODS", "90_EXPORT"]
    C = {n: collection(n) for n in names}
    M = build_materials()

    hull = build_hull_shell(C["10_HULL_CORE"], M)
    build_port_cutters(C["10_HULL_CORE"], hull)
    build_port_frames(C["10_HULL_CORE"], M)
    build_backbone(C["10_HULL_CORE"], M)
    build_head(C["10_HULL_CORE"], M)

    # wale'ler ve silmeler
    band_strip("CORE_WALE_MAIN", lambda s: deck_z(s) + 0.15, 0.34, 0.12, C["10_HULL_CORE"], M["hull"], 0.01, 0.985)
    band_strip("CORE_WALE_LOWER", lambda s: deck_z(s) - 0.55, 0.26, 0.10, C["10_HULL_CORE"], M["hull"], 0.01, 0.975)
    band_strip("CORE_MOULDING_BAND_LOW", lambda s: deck_z(s) + 1.30, 0.07, 0.06, C["10_HULL_CORE"], M["gold"], 0.005, 0.99)
    band_strip("CORE_MOULDING_RAIL", lambda s: top_z(s) - 0.06, 0.12, 0.10, C["10_HULL_CORE"], M["yellow"], 0.003, 0.995)

    deck_surface("CORE_DECK_GUN", 0.02, 0.975, deck_z, C["10_HULL_CORE"], M["deck"])
    deck_surface("CORE_DECK_QUARTER", 0.004, S_QD, lambda s: deck_z(s) + QD_H, C["10_HULL_CORE"], M["deck"])
    deck_surface("CORE_DECK_FORECASTLE", S_FC, 0.985, lambda s: deck_z(s) + QD_H, C["10_HULL_CORE"], M["deck"])

    build_breast_rails(C["10_HULL_CORE"], M)
    rudder = build_rudder(C["24_MODULES_DECOR"], M)
    build_sockets(C["30_SOCKETS"], rudder)
    build_uv_fallback(hull) if not hull.data.uv_layers else None
    build_collision(C["40_COLLISION"], hull)

    blend_dir = ROOT / "Blender" / "versions"
    blend_dir.mkdir(parents=True, exist_ok=True)
    blend = blend_dir / f"{SHIP_ID}_{VERSION}.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend), compress=True)
    rep = audit(sc, ROOT / "reports" / f"scene_audit_{VERSION}.json")
    print(json.dumps(rep["checks"], indent=1, ensure_ascii=False)[:2000])
    if not no_render:
        setup_render(sc, fast="--fast" in sys.argv)
        paths = render_views(sc, ROOT / "renders" / VERSION)
        print("RENDERS", *paths, sep="\n")


if __name__ == "__main__":
    main()
