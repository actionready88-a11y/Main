"""Pass v028 — Osmanlı tunç topu MOD_CANNON_OTTOMAN_C (B'nin yerine) + palangalar + top takımı, v027 üzerine.

Çalıştırma (depo kökünden):
    python3 OTTOMAN_FRIGATE_1780_ISTANBUL/scripts/pass_v028_cannon_ottoman_bronze.py [--no-render | --render-only]

Kullanıcı (2026-09-26): "toplar kalitesiz duruyor; kalitesini artır; oyunlarda ve tarihte Osmanlı gemilerinde
kullanılan toplar neler, araştır".
Araştırma (arama özetleri; kaynak sayfaların çoğu bu ortamda açılamadı):
  - Osmanlı gemi topları: ağır — şayka, balyemez, bacaluşka, kanon, şahî, kolomborna; hafif — darbzen, prangı,
    sakaloz, havan, misket [İKİNCİL: dergipark "Osmanlı devleti'nde gemi tipleri…"; Sütçüoğlu, Türk Topçuluğunun ABC'si].
  - Toplar Tophâne-i Âmire'de dökülür/yenilenir; 1682 sonrası kalyonlarda "80 bronze guns" [İKİNCİL: weaponsandwarfare /
    warhistory "Ottoman Naval Gunnery in the Eighteenth Century", arama özeti]. Fırkateyn 30–40 top [İKİNCİL].
  - Tunç toplarda kaldırma kulpları "yunus" biçiminde süslenir; kaskabel ve süsler ayrı kalıpla eklenir [İKİNCİL:
    Fort Ticonderoga "Cannon"; arama özeti].
  - Oyun kalitesi: namlu, kızak, tekerler ayrı; parça başına UV + PBR seti; kızakta 6 palanga halkası, 2 brok halkası,
    palanga halkası, taban, takoz, muylu kapakları [İKİNCİL: CGTrader/RenderHub model açıklamaları; QAR projesi].
Uygulama:
  - Namlu (tunç, 64 dilim): kaskabel topuzu ve halkaları, taban halkası, falya yastığı + deliği, **tuğra madalyonu**
    (stilize; belirli bir padişahın tuğrası DEĞİL), **kitabe kartuşu** (stilize yazı çizgileri), **yunus kulplar**,
    kabartma sarmaşık kuşakları, lale ağız. Ölçüler B ile aynı (çap 0,107 m [İKİNCİL], diğerleri TAHMİN) → pivot,
    mürettebat ve brok halatları değişmez.
  - Kızak: B geometrisi + pah (bevel) + demir levhalar/cıvatalar; malzeme: aşınmış kırmızı aşı boyası (kenarlarda
    ahşap, girintilerde kir), ahşap damarı; demir aksam pas; tunç patina (girintilerde yeşil).
  - Gemi: her borda topuna iki yan palanga (makara çifti + halat, kızak halkasından borda halkasına).
    Toplar arasına top takımı rafı: tokmak, sünger, harbi, fitil sopası (MOD_GUN_TOOLS_RACK_A).
  - UE için modüle özel UV + bake (BaseColor/Normal/ORM, AO dahil): Textures/Modules/Cannon_C/.
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


P20 = _load("pass_v020", "pass_v020_cannon_realistic.py")
P18 = _load("pass_v018", "pass_v018_battery_dressing.py")
P5, H, P15, P14 = P20.P5, P20.H, P20.P15, P20.P14
SRC_VER, VER = "v027", "v028"
ROOT, SHIP = H.ROOT, H.SHIP_ID
MANIFEST_VERSION = 24
V = Vector
L, XB, XM, BORE = P20.L, P20.XB, P20.XM, P20.BORE
TRUN_X, TRUN_Z = P20.TRUN_X, P20.TRUN_Z
SEG = 64


# --- Malzemeler ---------------------------------------------------------------------------------
def _nodes(m):
    m.use_nodes = True
    return m.node_tree.nodes, m.node_tree.links, m.node_tree.nodes["Principled BSDF"]


def mat_bronze():
    n = "MAT_Bronze_Ottoman"
    if n in bpy.data.materials:
        return bpy.data.materials[n]
    m = bpy.data.materials.new(n)
    N, Lk, b = _nodes(m)
    tc = N.new("ShaderNodeTexCoord")
    ao = N.new("ShaderNodeAmbientOcclusion")
    ao.inputs["Distance"].default_value = 0.05
    noise = N.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 9.0
    noise.inputs["Detail"].default_value = 12.0
    Lk.new(tc.outputs["Object"], noise.inputs["Vector"])
    inv = N.new("ShaderNodeMath")
    inv.operation = "SUBTRACT"
    inv.inputs[0].default_value = 1.0
    Lk.new(ao.outputs["AO"], inv.inputs[1])
    pat = N.new("ShaderNodeMath")
    pat.operation = "MULTIPLY_ADD"
    Lk.new(inv.outputs[0], pat.inputs[0])
    pat.inputs[1].default_value = 1.6
    nm = N.new("ShaderNodeMath")
    nm.operation = "MULTIPLY"
    nm.inputs[1].default_value = 0.45
    Lk.new(noise.outputs["Fac"], nm.inputs[0])
    Lk.new(nm.outputs[0], pat.inputs[2])
    ramp = N.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.30
    ramp.color_ramp.elements[0].color = (0.50, 0.33, 0.13, 1)     # tunç
    ramp.color_ramp.elements[1].position = 0.62
    ramp.color_ramp.elements[1].color = (0.13, 0.24, 0.18, 1)     # patina
    Lk.new(pat.outputs[0], ramp.inputs["Fac"])
    Lk.new(ramp.outputs["Color"], b.inputs["Base Color"])
    rr = N.new("ShaderNodeMapRange")
    rr.inputs["To Min"].default_value = 0.28
    rr.inputs["To Max"].default_value = 0.72
    Lk.new(pat.outputs[0], rr.inputs["Value"])
    Lk.new(rr.outputs["Result"], b.inputs["Roughness"])
    mt = N.new("ShaderNodeMapRange")
    mt.inputs["To Min"].default_value = 1.0
    mt.inputs["To Max"].default_value = 0.35
    Lk.new(pat.outputs[0], mt.inputs["Value"])
    Lk.new(mt.outputs["Result"], b.inputs["Metallic"])
    fine = N.new("ShaderNodeTexNoise")
    fine.inputs["Scale"].default_value = 180.0
    Lk.new(tc.outputs["Object"], fine.inputs["Vector"])
    bump = N.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.12
    Lk.new(fine.outputs["Fac"], bump.inputs["Height"])
    Lk.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m


def mat_painted_wood():
    n = "MAT_Carriage_PaintedWorn"
    if n in bpy.data.materials:
        return bpy.data.materials[n]
    m = bpy.data.materials.new(n)
    N, Lk, b = _nodes(m)
    tc = N.new("ShaderNodeTexCoord")
    mp = N.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1.0, 14.0, 14.0)            # damar yerel X boyunca
    Lk.new(tc.outputs["Object"], mp.inputs["Vector"])
    dist = N.new("ShaderNodeTexNoise")
    dist.inputs["Scale"].default_value = 3.0
    Lk.new(mp.outputs["Vector"], dist.inputs["Vector"])
    wave = N.new("ShaderNodeTexWave")
    wave.inputs["Scale"].default_value = 3.0
    wave.inputs["Distortion"].default_value = 6.0
    wave.inputs["Detail"].default_value = 4.0
    Lk.new(mp.outputs["Vector"], wave.inputs["Vector"])
    wood = N.new("ShaderNodeValToRGB")
    wood.color_ramp.elements[0].color = (0.10, 0.055, 0.03, 1)
    wood.color_ramp.elements[1].color = (0.28, 0.17, 0.09, 1)
    Lk.new(wave.outputs["Fac"], wood.inputs["Fac"])
    geo = N.new("ShaderNodeNewGeometry")
    edge = N.new("ShaderNodeMapRange")
    edge.inputs["From Min"].default_value = 0.52
    edge.inputs["From Max"].default_value = 0.60
    Lk.new(geo.outputs["Pointiness"], edge.inputs["Value"])
    wn = N.new("ShaderNodeTexNoise")
    wn.inputs["Scale"].default_value = 14.0
    wn.inputs["Detail"].default_value = 8.0
    Lk.new(tc.outputs["Object"], wn.inputs["Vector"])
    wear = N.new("ShaderNodeMath")
    wear.operation = "MULTIPLY"
    Lk.new(edge.outputs["Result"], wear.inputs[0])
    wm = N.new("ShaderNodeMapRange")
    wm.inputs["From Min"].default_value = 0.45
    wm.inputs["From Max"].default_value = 0.62
    Lk.new(wn.outputs["Fac"], wm.inputs["Value"])
    Lk.new(wm.outputs["Result"], wear.inputs[1])
    paint = N.new("ShaderNodeMix")
    paint.data_type = "RGBA"
    paint.inputs["A"].default_value = (0.26, 0.05, 0.03, 1)
    Lk.new(wood.outputs["Color"], paint.inputs["B"])
    Lk.new(wear.outputs[0], paint.inputs["Factor"])
    ao = N.new("ShaderNodeAmbientOcclusion")
    ao.inputs["Distance"].default_value = 0.12
    dirt = N.new("ShaderNodeMix")
    dirt.data_type = "RGBA"
    dirt.blend_type = "MULTIPLY"
    dirt.inputs["Factor"].default_value = 1.0
    Lk.new(paint.outputs["Result"], dirt.inputs["A"])
    dr = N.new("ShaderNodeMapRange")
    dr.inputs["To Min"].default_value = 0.45
    Lk.new(ao.outputs["AO"], dr.inputs["Value"])
    comb = N.new("ShaderNodeCombineColor")
    for s in ("Red", "Green", "Blue"):
        Lk.new(dr.outputs["Result"], comb.inputs[s])
    Lk.new(comb.outputs["Color"], dirt.inputs["B"])
    Lk.new(dirt.outputs["Result"], b.inputs["Base Color"])
    ro = N.new("ShaderNodeMapRange")
    ro.inputs["To Min"].default_value = 0.62
    ro.inputs["To Max"].default_value = 0.85
    Lk.new(wear.outputs[0], ro.inputs["Value"])
    Lk.new(ro.outputs["Result"], b.inputs["Roughness"])
    bump = N.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.25
    Lk.new(wave.outputs["Fac"], bump.inputs["Height"])
    Lk.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m


def mat_iron_rusty():
    n = "MAT_Iron_Fittings"
    if n in bpy.data.materials:
        return bpy.data.materials[n]
    m = bpy.data.materials.new(n)
    N, Lk, b = _nodes(m)
    tc = N.new("ShaderNodeTexCoord")
    ao = N.new("ShaderNodeAmbientOcclusion")
    ao.inputs["Distance"].default_value = 0.04
    noise = N.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 30.0
    noise.inputs["Detail"].default_value = 10.0
    Lk.new(tc.outputs["Object"], noise.inputs["Vector"])
    f = N.new("ShaderNodeMath")
    f.operation = "SUBTRACT"
    Lk.new(noise.outputs["Fac"], f.inputs[0])
    Lk.new(ao.outputs["AO"], f.inputs[1])
    ramp = N.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = -0.25 + 0.5
    ramp.color_ramp.elements[0].color = (0.025, 0.024, 0.023, 1)
    ramp.color_ramp.elements[1].position = 0.62
    ramp.color_ramp.elements[1].color = (0.16, 0.07, 0.03, 1)
    add = N.new("ShaderNodeMath")
    add.inputs[1].default_value = 0.5
    Lk.new(f.outputs[0], add.inputs[0])
    Lk.new(add.outputs[0], ramp.inputs["Fac"])
    Lk.new(ramp.outputs["Color"], b.inputs["Base Color"])
    rr = N.new("ShaderNodeMapRange")
    rr.inputs["To Min"].default_value = 0.4
    rr.inputs["To Max"].default_value = 0.9
    Lk.new(add.outputs[0], rr.inputs["Value"])
    Lk.new(rr.outputs["Result"], b.inputs["Roughness"])
    b.inputs["Metallic"].default_value = 0.8
    return m


# --- Namlu ---------------------------------------------------------------------------------------------
def outer_profile():
    p = P20.barrel_profile()
    cut = next(i for i, (r, x) in enumerate(p) if abs(r - (BORE / 2 + 0.010)) < 1e-6)
    return p[:cut]


def radius_at(x, prof):
    pts = sorted([(xx, r) for r, xx in prof if r > 0.02], key=lambda t: t[0])
    for (x0, r0), (x1, r1) in zip(pts[:-1], pts[1:]):
        if x0 <= x <= x1:
            return r0 + (r1 - r0) * (x - x0) / max(x1 - x0, 1e-6)
    return pts[-1][1]


def surf(x, phi, prof, h=0.0):
    """Namlu yüzeyinde nokta: x boyuna, phi üstten açı (rad), h yüzeyden yükseklik."""
    r = radius_at(x, prof) + h
    return V((x, r * math.sin(phi), r * math.cos(phi)))


def tube_var(bm, pts, radii, seg=8):
    rings = []
    for i, p in enumerate(pts):
        a, b = pts[max(i - 1, 0)], pts[min(i + 1, len(pts) - 1)]
        t = (b - a).normalized()
        u = t.cross(V((0, 0, 1)))
        if u.length < 1e-3:
            u = t.cross(V((0, 1, 0)))
        u.normalize()
        w = t.cross(u)
        rings.append([bm.verts.new(p + (u * math.cos(2 * math.pi * k / seg) + w * math.sin(2 * math.pi * k / seg)) * radii[i])
                      for k in range(seg)])
    for r0, r1 in zip(rings[:-1], rings[1:]):
        for k in range(seg):
            bm.faces.new([r0[k], r0[(k + 1) % seg], r1[(k + 1) % seg], r1[k]])
    bm.faces.new(list(reversed(rings[0])))
    bm.faces.new(rings[-1])


def raised_panel(bm, prof, x0, x1, phi_w, h, rim=0.012, nu=16, nv=8, round_ends=True):
    """Namlu yüzeyine oturan kabartma levha (kartuş/madalyon tabanı) + kenar çıtası."""
    grid = []
    for i in range(nu + 1):
        x = x0 + (x1 - x0) * i / nu
        t = (i / nu) * 2 - 1
        wf = math.sqrt(max(1 - t * t, 0.0)) if round_ends else 1.0
        row = []
        for j in range(nv + 1):
            phi = (-1 + 2 * j / nv) * phi_w * max(wf, 0.25 if round_ends else 1.0)
            row.append(bm.verts.new(surf(x, phi, prof, h)))
        grid.append(row)
    for i in range(nu):
        for j in range(nv):
            bm.faces.new([grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1]])
    edge = [grid[i][0].co.copy() for i in range(nu + 1)] + [grid[nu][j].co.copy() for j in range(nv + 1)] + \
           [grid[i][nv].co.copy() for i in range(nu, -1, -1)] + [grid[0][j].co.copy() for j in range(nv, -1, -1)]
    P15.tube(bm, edge, rim, seg=6)
    base = [surf(x0 + (x1 - x0) * i / nu, 0, prof, 0) for i in range(nu + 1)]
    return base


def build_barrel(M):
    prof = outer_profile()
    bm = bmesh.new()
    P5.lathe(bm, P20.barrel_profile(), SEG, Matrix.Rotation(math.radians(90), 4, "Y"))
    for sgn in (1, -1):                                           # muylular
        m = Matrix.Translation((0, sgn * 0.150, -0.012)) @ Matrix.Rotation(math.radians(-90 * sgn), 4, "X")
        P5.lathe(bm, [(0.0, 0.0), (0.090, 0.0), (0.090, 0.018), (0.082, 0.028), (0.062, 0.034), (0.055, 0.040),
                      (0.055, 0.150), (0.052, 0.156), (0.030, 0.160), (0.0, 0.161)], 32, m)
    # falya yastığı + delik
    xv = XB + 0.16
    c = surf(xv, 0, prof, -0.004)
    P5.lathe(bm, [(0.0, 0.0), (0.040, 0.0), (0.040, 0.010), (0.034, 0.016), (0.010, 0.018), (0.007, 0.010), (0.0, 0.010)], 24,
             P5.axis_matrix(c, V((0, 0, 1))))
    # yunus kulplar (muylunun biraz önünde, iki yanda 35°)
    for sgn in (1, -1):
        phi = sgn * math.radians(34)
        pts, rad = [], []
        for k in range(22):
            t = k / 21
            x = 0.03 + 0.30 * t
            hgt = 0.015 + 0.12 * math.sin(math.pi * min(t * 1.12, 1.0))
            p = surf(x, phi, prof, hgt)
            pts.append(p)
            rad.append(0.030 * (1.0 - 0.55 * t) + 0.006 * math.sin(math.pi * t * 3))
        tube_var(bm, pts, rad, seg=10)
        head = surf(0.03, phi, prof, 0.018)
        r = bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=0.034)
        bmesh.ops.translate(bm, vec=head, verts=r["verts"])
        tail = pts[-1]
        for s2 in (1, -1):                                        # kuyruk yüzgeci
            P15.tube(bm, [tail, tail + V((0.045, s2 * 0.025, 0.035))], 0.010, seg=6)
    # tuğra madalyonu (1. takviye üstü) — stilize çizgiler
    xt = XB + 0.42
    raised_panel(bm, prof, xt - 0.09, xt + 0.09, math.radians(26), 0.006, rim=0.010, nu=14, nv=8)
    for k, dx in enumerate((-0.035, -0.012, 0.012)):              # üç dikey kol (tuğ)
        pts = [surf(xt + dx + 0.004 * j, math.radians(-8 + 2.5 * j * 0), prof, 0.012) for j in range(1)]
        pts = [surf(xt + dx, math.radians(ph), prof, 0.012) for ph in (-12, -4, 4, 13 + 3 * k)]
        P15.tube(bm, pts, 0.0045, seg=5)
    loop = [surf(xt + 0.035 + 0.030 * math.cos(a), math.radians(10 * math.sin(a) - 4), prof, 0.012)
            for a in np.linspace(0, 2 * math.pi, 18)]                # beyze (oval kavis)
    P15.tube(bm, loop, 0.0045, seg=5)
    base = [surf(xt - 0.06 + 0.12 * t, math.radians(-15 + 4 * math.sin(t * math.pi * 2)), prof, 0.012) for t in np.linspace(0, 1, 12)]
    P15.tube(bm, base, 0.004, seg=5)
    # kitabe kartuşu (kovanda) — stilize yazı satırları
    xk0, xk1 = XB + L * 0.60, XB + L * 0.60 + 0.34
    raised_panel(bm, prof, xk0, xk1, math.radians(22), 0.005, rim=0.009, nu=18, nv=6)
    for row, ph in enumerate((-9, 0, 9)):
        pts = [surf(xk0 + 0.04 + 0.26 * t, math.radians(ph + 2.2 * math.sin(t * 17 + row)), prof, 0.010) for t in np.linspace(0, 1, 16)]
        P15.tube(bm, pts, 0.0035, seg=4)
    # sarmaşık kuşakları (2) + yaprak kabartmaları
    for xc in (XB + L * 0.33, XB + L * 0.78):
        ring = [surf(xc + 0.018 * math.sin(6 * a), a, prof, 0.004) for a in np.linspace(0, 2 * math.pi, 73)]
        P15.tube(bm, ring, 0.006, seg=5)
        for k in range(12):
            a = 2 * math.pi * (k + 0.5) / 12
            r = bmesh.ops.create_uvsphere(bm, u_segments=8, v_segments=6, radius=1.0)
            bmesh.ops.scale(bm, vec=(0.022, 0.010, 0.006), verts=r["verts"])
            q = V((0, 0, 1)).rotation_difference(V((0, math.sin(a), math.cos(a)))).to_matrix().to_4x4()
            bmesh.ops.transform(bm, matrix=Matrix.Translation(surf(xc + 0.03 * math.sin(6 * a + 1.5), a, prof, 0.004)) @ q,
                                verts=r["verts"])
    me = P20.finalize("MOD_CANNON_OTTOMAN_C_BARREL", [(bm, M["bronze"])], sharp=30)
    return me


def build_carriage(M):
    me = P20.build_carriage(M["iron"], M["wood"])
    me.name = "MOD_CANNON_OTTOMAN_C_CARRIAGE"
    return me


# --- Gemi: palangalar ve takım rafları -----------------------------------------------------------------
def build_tackles_and_racks(M):
    col = bpy.data.collections["22_MODULES_CANNONS"]
    core = bpy.data.collections["10_HULL_CORE"]
    brope, bw, bi = bmesh.new(), bmesh.new(), bmesh.new()
    n = 0
    guns = [o for o in bpy.data.objects if o.type == "EMPTY" and o.name.startswith("SOCKET_CANNON_") and "LOWER" not in o.name
            and "CHASE" not in o.name]
    for g in guns:
        mw = g.matrix_world
        sgn = 1 if g.location.y > 0 else -1
        for side in (1, -1):                                        # yan palanga: kızak halkası → borda halkası
            a = mw @ V((0.22, side * 0.37, 0.46))
            hx = g.location.x + side * (-sgn) * 0.62               # v018 halka cıvatası (x ± 0,62)
            zb = g.location.z + 0.52
            yi = P18.inner_y_world(hx, zb)
            b = V((hx, sgn * (yi - 0.14), zb))
            d = (b - a).normalized()
            for blk in (a + d * 0.18, b - d * 0.18):
                P15.obox(bw, blk, d, d.cross(V((0, 0, 1))).normalized(), d.cross(d.cross(V((0, 0, 1)))).normalized(), 0.07, 0.045, 0.035)
            for off in (-0.02, 0.02):                               # iki kol (palanga)
                o = V((0, 0, off))
                P15.tube(brope, [a + d * 0.24 + o, b - d * 0.24 + o], 0.011, seg=5)
            P15.tube(brope, [a, a + d * 0.12], 0.012, seg=5)
            P15.tube(brope, [b, b - d * 0.12], 0.012, seg=5)
            n += 1
    # top takımı rafı: bel küpeştesinde toplar arasında (tokmak/sünger/harbi/fitil)
    racks = 0
    for sgn in (1, -1):
        gs = sorted([g for g in guns if (g.location.y > 0) == (sgn > 0)], key=lambda g: g.location.x)
        for a, b in zip(gs[:-1:2], gs[1::2]):
            x = (a.location.x + b.location.x) / 2
            z = (a.location.z + b.location.z) / 2 + 1.25
            yi = P18.inner_y_world(x, z) - 0.03
            for dx in (-0.55, 0.55):                                # iki kanca
                P5.aabox(bi, x + dx - 0.02, x + dx + 0.02, *sorted((sgn * (yi - 0.14), sgn * yi)), z - 0.02, z + 0.02)
            for k, (L_t, head) in enumerate(((3.0, "sponge"), (3.0, "rammer"), (2.6, "worm"), (1.4, "linstock"))):
                zz = z + 0.05 + 0.055 * k
                yy = sgn * (yi - 0.08)
                x0, x1 = x - L_t / 2, x + L_t / 2
                P5.lathe(bw, [(0.0, 0.0), (0.018, 0.0), (0.018, L_t), (0.0, L_t)], 8,
                         Matrix.Translation((x0, yy, zz)) @ Matrix.Rotation(math.radians(90), 4, "Y"))
                if head == "sponge":
                    P5.lathe(bw, [(0.0, 0.0), (0.05, 0.0), (0.052, 0.20), (0.0, 0.22)], 12,
                             Matrix.Translation((x1, yy, zz)) @ Matrix.Rotation(math.radians(90), 4, "Y"))
                elif head == "rammer":
                    P5.lathe(bw, [(0.0, 0.0), (0.05, 0.0), (0.05, 0.12), (0.0, 0.12)], 12,
                             Matrix.Translation((x1, yy, zz)) @ Matrix.Rotation(math.radians(90), 4, "Y"))
                elif head == "worm":
                    helix = [V((x1 + 0.012 * t, yy + 0.03 * math.cos(t), zz + 0.03 * math.sin(t))) for t in np.linspace(0, 12, 30)]
                    P15.tube(bi, helix, 0.005, seg=4)
            racks += 1
    merged = bmesh.new()
    for idx, b in enumerate((brope, bw, bi)):
        tmp = bpy.data.meshes.new("_tmp")
        bmesh.ops.recalc_face_normals(b, faces=b.faces)
        b.to_mesh(tmp)
        b.free()
        tmp.polygons.foreach_set("material_index", [idx] * len(tmp.polygons))
        merged.from_mesh(tmp)
        bpy.data.meshes.remove(tmp)
    ob = P5.finish("MOD_CANNON_TACKLES_TOOLS_A", merged, col, [M["rope"], M["timber"], M["iron"]])
    ob["module_family"] = "CannonBattery"
    ob["note"] = "yan palangalar (her topa 2) + top takımı rafları; UE'de palangalar kablo/spline ile değiştirilebilir"
    return ob, n, racks


# --- Değiştirme ---------------------------------------------------------------------------------------------
def swap(bar_me, car_me):
    swapped = []
    old = set()
    for o in list(bpy.data.objects):
        if o.type != "MESH" or not o.name.startswith("MOD_CANNON_9PDR_B_") or o.name.endswith("_BARREL"):
            continue
        tag = o.name[len("MOD_CANNON_9PDR_B_"):]
        old.add(o.data)
        o.data = car_me
        o.name = f"MOD_CANNON_OTTOMAN_C_{tag}"
        o["gun_type"] = "ottoman_bronze_long_C"
        if not any(m.type == "BEVEL" for m in o.modifiers):
            bv = o.modifiers.new("Bevel", "BEVEL")
            bv.width = 0.012
            bv.segments = 2
            bv.limit_method = "ANGLE"
        for ch in o.children:
            if ch.type == "MESH":
                old.add(ch.data)
                ch.data = bar_me
                ch.name = f"MOD_CANNON_OTTOMAN_C_{tag}_BARREL"
        s = bpy.data.objects.get(o.get("socket", ""))
        if s:
            s["installed_module"] = o.name
            s["manifest_version"] = MANIFEST_VERSION
        swapped.append(o.name)
    for me in old:
        if me.users == 0:
            bpy.data.meshes.remove(me)
    for o in bpy.data.objects:
        if o.type == "EMPTY" and o.name.startswith("SOCKET_CANNON_LOWER_"):
            o["module_family_accepts"] = "MOD_CANNON_OTTOMAN_C"
        if o.name in ("SOCKET_GUN_MUZZLE", "SOCKET_GUN_TOUCHHOLE"):
            o["mesh_socket_of"] = "MOD_CANNON_OTTOMAN_C_BARREL"
            o["manifest_version"] = MANIFEST_VERSION
    return swapped


def render(sc):
    H.setup_render(sc, fast=True)
    sc.cycles.samples = 64
    out = ROOT / "renders" / VER
    out.mkdir(parents=True, exist_ok=True)
    g = bpy.data.objects["SOCKET_CANNON_S_05"].matrix_world
    views = [
        ("top_arka_ust", g @ V((-2.4, 1.3, 1.6)), g @ V((0.2, 0.0, 0.62)), 32),
        ("top_yakin_tugra", g @ V((-1.2, 0.55, 1.45)), g @ V((-0.35, 0.0, 0.95)), 45),
        ("top_yan", g @ V((-0.9, -1.9, 1.1)), g @ V((-0.2, 0.1, 0.6)), 30),
        ("bel_batarya", V((-12.0, 0.2, 5.4)), V((6.0, 3.0, 3.4)), 24),
    ]
    for name, loc, tgt, lens in views:
        sc.camera = H.camera(sc, f"CAM28_{name}", loc, tgt, lens=lens)
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
    M = P15.materials()
    M.update({"bronze": mat_bronze(), "wood": mat_painted_wood(), "iron": mat_iron_rusty()})
    bar_me = build_barrel(M)
    car_me = build_carriage(M)
    swapped = swap(bar_me, car_me)
    bpy.context.view_layer.update()
    # brok halatlarını yeni modele göre yenile
    for nme in ("CORE_RING_BOLTS", "MOD_CANNON_BREECHING_S_A", "MOD_CANNON_BREECHING_P_A"):
        o = bpy.data.objects.get(nme)
        if o:
            me = o.data
            bpy.data.objects.remove(o, do_unlink=True)
            if me.users == 0:
                bpy.data.meshes.remove(me)
    _, n_b, n_r = P18.build_bolts_and_breeching(bpy.data.collections["10_HULL_CORE"], None, P18.P17.mats())
    tk, n_t, n_racks = build_tackles_and_racks(M)
    bpy.ops.wm.save_as_mainfile(filepath=str(out), compress=True)
    H.VERSION = VER
    ap = ROOT / "reports" / f"scene_audit_{VER}.json"
    rep = H.audit(sc, ap)

    def tris(me):
        me.calc_loop_triangles()
        return len(me.loop_triangles)

    rep["cannon_v028"] = {"module": "MOD_CANNON_OTTOMAN_C", "replaced": len(swapped), "tris": {"barrel": tris(bar_me), "carriage": tris(car_me)},
                          "breeching": n_r, "ring_bolts": n_b, "side_tackles": n_t, "tool_racks": n_racks,
                          "ornament_note": "tuğra ve kitabe stilizedir; belirli bir padişahın tuğrası/yazısı değildir"}
    rep["pass"] = {"name": "pass_v028_cannon_ottoman_bronze", "source": f"Blender/versions/{SHIP}_{SRC_VER}.blend",
                   "manifest_version": MANIFEST_VERSION, "geometry_changed": "top modülü B → C; palangalar, takım rafları"}
    ap.write_text(json.dumps(rep, indent=2, ensure_ascii=False), encoding="utf-8")
    print("V028", json.dumps(rep["cannon_v028"], ensure_ascii=False))
    if "--no-render" not in sys.argv:
        render(sc)


if __name__ == "__main__":
    main()
