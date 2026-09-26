"""Pass v022 — SailSet: sarılı yelkenler (varsayılan) + açık yelken varyantı + motif modülleri, v021 üzerine.

Çalıştırma (depo kökünden):
    python3 OTTOMAN_FRIGATE_1780_ISTANBUL/scripts/make_sail_emblems.py        # motif dokuları (bir kez)
    python3 OTTOMAN_FRIGATE_1780_ISTANBUL/scripts/pass_v022_sailset.py [--no-render | --render-only]

Kullanıcı (2026-09-26): "yelkenler sarılı olacak"; "yelkenlerin üstüne buradaki Osmanlı motiflerini ekle,
modüler parça olsun" (referans görsel: krem yelkenlerde kırmızı/altın lale ve rumi desenleri).
- Sarılı (FURLED, görünür): her serenin üstünde gasketlerle bağlanmış yelken rulosu (9 seren), randa gafa
  toplanmış, flok ve velena cıvadıra/flok bumbası üstünde.
- Açık (SET, gizli varyant): 8 kare yelken (mizana alt sereni boş — dönem düzeni), randa, flok, velena;
  bezin boyuna dikiş çizgileri, rüzgârla karnı öne. UE'de kumaş/cloth ya da iskeletli mesh'e dönüştürülebilir.
- Motifler (gizli, SET ile birlikte): MOD_SAIL_EMBLEM_{RUMI,LALE}_A_* — yelken yüzeyini izleyen ayrı decal
  mesh'ler (iki yüz), soket SOCKET_SAIL_EMBLEM_*. Doku: Textures/emblems/*.png.
Durumlar nesne özelliği `sail_state` (furled/set) ile işaretlidir. Ölçüler seren ve direklerden türetilir.
"""

import importlib.util
import json
import math
import sys
from pathlib import Path

import bpy  # noqa: I001
import bmesh
from mathutils import Matrix, Vector

HERE = Path(__file__).resolve().parent


def _load(name, fname):
    sp = importlib.util.spec_from_file_location(name, HERE / fname)
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


P15 = _load("pass_v015", "pass_v015_rigset.py")
P13, P5, H = P15.P13, P15.P5, P15.H
SRC_VER, VER = "v021", "v022"
ROOT, SHIP = H.ROOT, H.SHIP_ID
MANIFEST_VERSION = 19
P5.MANIFEST_VERSION = MANIFEST_VERSION
V = Vector
MASTS = ("FORE", "MAIN", "MIZZEN")
KEYS = ("COURSE", "TOPSAIL", "TOPGALLANT")
FURL_R = {"COURSE": 0.27, "TOPSAIL": 0.23, "TOPGALLANT": 0.15}
EMBLEMS = {"FORE_COURSE": "RUMI", "MAIN_COURSE": "RUMI", "FORE_TOPSAIL": "LALE", "MAIN_TOPSAIL": "LALE",
           "MIZZEN_TOPSAIL": "LALE", "SPANKER": "LALE"}


# --- Malzemeler -------------------------------------------------------------------------
def canvas_material():
    name = "MAT_Sail_Canvas"
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    N, Lk = m.node_tree.nodes, m.node_tree.links
    b = N["Principled BSDF"]
    uv = N.new("ShaderNodeTexCoord")
    sep = N.new("ShaderNodeSeparateXYZ")
    Lk.new(uv.outputs["UV"], sep.inputs[0])
    wave = N.new("ShaderNodeTexWave")                 # bez dikişleri (UV u yönünde, ~0,6 m)
    wave.wave_type = "BANDS"
    wave.bands_direction = "X"
    wave.inputs["Scale"].default_value = 1.0
    mul = N.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    mul.inputs[1].default_value = 1.0 / 0.6
    Lk.new(sep.outputs["X"], mul.inputs[0])
    comb = N.new("ShaderNodeCombineXYZ")
    Lk.new(mul.outputs[0], comb.inputs["X"])
    Lk.new(comb.outputs[0], wave.inputs["Vector"])
    ramp = N.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = (0.50, 0.46, 0.38, 1)
    ramp.color_ramp.elements[1].position = 0.08
    ramp.color_ramp.elements[1].color = (0.80, 0.76, 0.66, 1)
    Lk.new(wave.outputs["Fac"], ramp.inputs["Fac"])
    noise = N.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 3.0
    Lk.new(uv.outputs["UV"], noise.inputs["Vector"])
    mix = N.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.blend_type = "MULTIPLY"
    mix.inputs["Factor"].default_value = 0.18
    Lk.new(ramp.outputs["Color"], mix.inputs["A"])
    Lk.new(noise.outputs["Color"], mix.inputs["B"])
    Lk.new(mix.outputs["Result"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.9
    b.inputs["Transmission Weight"].default_value = 0.0
    b.inputs["Subsurface Weight"].default_value = 0.05
    return m


def emblem_material(key):
    name = f"MAT_SailEmblem_{key.title()}_A"
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    path = ROOT / "Textures" / "emblems" / f"T_SailEmblem_{key.title()}_A.png"
    img = bpy.data.images.load(str(path), check_existing=True)
    img.filepath = bpy.path.relpath(str(path), start=str(ROOT / "Blender" / "versions"))
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    N, Lk = m.node_tree.nodes, m.node_tree.links
    b = N["Principled BSDF"]
    tex = N.new("ShaderNodeTexImage")
    tex.image = img
    Lk.new(tex.outputs["Color"], b.inputs["Base Color"])
    Lk.new(tex.outputs["Alpha"], b.inputs["Alpha"])
    b.inputs["Roughness"].default_value = 0.85
    m.blend_method = "HASHED" if hasattr(m, "blend_method") else None
    return m


# --- Yardımcılar ------------------------------------------------------------------------
def yard_info(mast, key):
    ob = bpy.data.objects[f"MOD_RIG_YARD_{mast}_{key}_A"]
    half = max(abs(v.co.y) for v in ob.data.vertices)
    dia = 2 * max(abs(v.co.x) for v in ob.data.vertices if abs(v.co.y) < half * 0.3 and abs(v.co.z) < 0.35)
    return ob, half, dia


def mk_object(name, bm, mats, col, origin_mw=None, state="furled", visible=True):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for m in mats:
        me.materials.append(m)
    for p in me.polygons:
        p.use_smooth = True
    ob = bpy.data.objects.new(name, me)
    col.objects.link(ob)
    if origin_mw is not None:                       # mesh dünya koordinatında kuruldu → orijini sokete taşı
        me.transform(origin_mw.inverted())
        ob.matrix_world = origin_mw
    tmp = bpy.data.objects.new("_tmp_uv", me)
    if not me.uv_layers:
        H.build_uv_fallback(tmp)
    bpy.data.objects.remove(tmp)
    ob["module_family"] = "SailSet"
    ob["sail_state"] = state
    ob.hide_render = not visible
    ob.hide_viewport = not visible
    return ob


# --- Sarılı yelkenler --------------------------------------------------------------------
def furled_bundle(bm, L2W, half, r0, dia, n_gask=None):
    """Yerel (seren) çerçevesinde: Y boyunca rulo, serenin üstünde ve hafif kıçında."""
    NY, NR = 40, 14
    rings = []
    span = half * 0.86
    for i in range(NY + 1):
        y = -span + 2 * span * i / NY
        t = abs(y) / span
        r = r0 * (1.0 - 0.72 * t ** 2.2) * (1.0 + 0.10 * math.sin(i * 1.7) * (1 - t))
        cx, cz = -0.06, dia / 2 + r * 0.75
        ring = []
        for k in range(NR):
            a = 2 * math.pi * k / NR
            wob = 1.0 + 0.07 * math.sin(3 * a + i * 0.9)
            ring.append(bm.verts.new(L2W @ V((cx + r * 1.05 * math.cos(a) * wob, y, cz + r * 0.82 * math.sin(a) * wob))))
        rings.append(ring)
    for r0_, r1_ in zip(rings[:-1], rings[1:]):
        for k in range(NR):
            bm.faces.new([r0_[k], r0_[(k + 1) % NR], r1_[(k + 1) % NR], r1_[k]])
    for rr in (rings[0], rings[-1]):
        c = sum((v.co for v in rr), V()) / len(rr)
        cv = bm.verts.new(c)
        for k in range(NR):
            bm.faces.new([rr[k], rr[(k + 1) % NR], cv])
    return span


def gaskets(bm, L2W, span, r0, dia):
    n = max(int(2 * span / 0.95), 2)
    for g in range(n + 1):
        y = -span + 2 * span * g / n
        t = abs(y) / span
        r = r0 * (1.0 - 0.72 * t ** 2.2) + 0.02
        cx, cz = -0.06, dia / 2 + (r - 0.02) * 0.75
        pts = [L2W @ V((cx + r * 1.08 * math.cos(2 * math.pi * k / 12), y, cz + r * 0.86 * math.sin(2 * math.pi * k / 12)))
               for k in range(13)]
        P15.tube(bm, pts, 0.012, seg=4)


def build_furled(col, M):
    obs = []
    for mast in MASTS:
        for key in KEYS:
            yob, half, dia = yard_info(mast, key)
            mw = yob.matrix_world.copy()
            bs, br = bmesh.new(), bmesh.new()
            span = furled_bundle(bs, mw, half, FURL_R[key], dia)
            gaskets(br, mw, span, FURL_R[key], dia)
            merged = merge([(bs, 0), (br, 1)])
            ob = mk_object(f"MOD_SAIL_FURLED_{mast}_{key}_A", merged, [M["canvas"], M["rope"]], col, origin_mw=mw)
            ob["socket"] = f"SOCKET_YARD_{mast}_{key}"
            obs.append(ob)
    # randa: gafa toplanmış
    gaff = bpy.data.objects["MOD_RIG_GAFF_MIZZEN_A"]
    gl = max(v.co.length for v in gaff.data.vertices)
    gmw = gaff.matrix_world.copy()
    d = (gmw.to_3x3() @ V((0, 0, 1)))                # spar() yerel Z = gaf yönü değil; dünya uçlarından yön al
    pts = [gmw @ v.co for v in gaff.data.vertices]
    p0 = gmw.translation
    p1 = max(pts, key=lambda p: (p - p0).length)
    d = (p1 - p0).normalized()
    side = d.cross(V((0, 1, 0))).normalized()
    if side.z > 0:
        side = -side
    L2W = Matrix((d.cross(side).normalized() * -1, d, -side)).transposed().to_4x4()
    L2W.translation = p0 + d * ((p1 - p0).length / 2)
    bs, br = bmesh.new(), bmesh.new()
    span = furled_bundle(bs, L2W, (p1 - p0).length / 2, 0.20, 0.18)
    gaskets(br, L2W, span, 0.20, 0.18)
    ob = mk_object("MOD_SAIL_FURLED_SPANKER_A", merge([(bs, 0), (br, 1)]), [M["canvas"], M["rope"]], col, origin_mw=gmw)
    ob["socket"] = "SOCKET_GAFF_MIZZEN"
    obs.append(ob)
    # flok ve velena: cıvadıra ve flok bumbası üstünde
    bsp = bpy.data.objects["MOD_RIG_BOWSPRIT_A"]
    bmw = bsp.matrix_world.copy()
    bpts = [bmw @ v.co for v in bsp.data.vertices]
    h0 = bmw.translation
    tip = max(bpts, key=lambda p: p.x)
    d = (tip - h0).normalized()
    up = V((-d.z, 0.0, d.x))
    for name, a, b, r in (("JIB", 0.62, 0.97, 0.14), ("FORE_STAYSAIL", 0.34, 0.60, 0.16)):
        c = h0 + (tip - h0) * ((a + b) / 2) + up * 0.42
        L2W = Matrix((-up.cross(d).normalized(), d, up)).transposed().to_4x4()
        L2W = Matrix((up.cross(d).normalized(), d, up)).transposed().to_4x4()
        L2W.translation = c
        bs, br = bmesh.new(), bmesh.new()
        span = furled_bundle(bs, L2W, (tip - h0).length * (b - a) / 2, r, 0.0)
        gaskets(br, L2W, span, r, 0.0)
        ob = mk_object(f"MOD_SAIL_FURLED_{name}_A", merge([(bs, 0), (br, 1)]), [M["canvas"], M["rope"]], col, origin_mw=bmw)
        ob["socket"] = "SOCKET_BOWSPRIT"
        obs.append(ob)
    return obs


def merge(parts):
    out = bmesh.new()
    for b, idx in parts:
        me = bpy.data.meshes.new("_tmp")
        b.to_mesh(me)
        b.free()
        me.polygons.foreach_set("material_index", [idx] * len(me.polygons))
        out.from_mesh(me)
        bpy.data.meshes.remove(me)
    return out


# --- Açık yelkenler (varyant) ---------------------------------------------------------------
def sail_surface(c00, c10, c01, c11, belly, NU=16, NV=12, fwd=V((1, 0, 0))):
    """c00 üst-iskele, c10 üst-sancak, c01 alt-iskele, c11 alt-sancak. Karın `fwd` yönünde."""
    grid = []
    for j in range(NV + 1):
        v = j / NV
        row = []
        for i in range(NU + 1):
            u = i / NU
            p = (c00 * (1 - u) + c10 * u) * (1 - v) + (c01 * (1 - u) + c11 * u) * v
            b = belly * math.sin(math.pi * u) * math.sin(math.pi * min(v * 0.9 + 0.1, 1.0)) * (0.35 + 0.65 * v)
            row.append(p + fwd * b)
        grid.append(row)
    return grid


def grid_mesh(bm, grid, uvscale):
    uvl = bm.loops.layers.uv.verify()
    vs = [[bm.verts.new(p) for p in row] for row in grid]
    NV, NU = len(grid) - 1, len(grid[0]) - 1
    for j in range(NV):
        for i in range(NU):
            f = bm.faces.new([vs[j][i], vs[j][i + 1], vs[j + 1][i + 1], vs[j + 1][i]])
            for loop, (ii, jj) in zip(f.loops, ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))):
                loop[uvl].uv = (ii / NU * uvscale[0], 1 - jj / NV * uvscale[1])


def build_set(col, M, deck_z):
    sails = {}
    for mast in MASTS:
        infos = {k: yard_info(mast, k) for k in KEYS}
        for key in KEYS:
            if mast == "MIZZEN" and key == "COURSE":
                continue                                  # crossjack: dönemde yelkensiz
            yob, half, dia = infos[key]
            mw = yob.matrix_world
            hh = half * 0.88
            top_l, top_r = mw @ V((0.12, -hh, 0.0)), mw @ V((0.12, hh, 0.0))
            if key == "COURSE":
                fz = deck_z(mw.translation.x) + 3.0
                bl = V((top_l.x + 0.4, top_l.y * 1.04, fz))
                br = V((top_r.x + 0.4, top_r.y * 1.04, fz))
            else:
                lo = {"TOPSAIL": "COURSE", "TOPGALLANT": "TOPSAIL"}[key]
                lob, lhalf, _ = infos[lo]
                lh = lhalf * 0.88
                bl, br = lob.matrix_world @ V((0.25, -lh, 0.2)), lob.matrix_world @ V((0.25, lh, 0.2))
            width = (top_r - top_l).length
            grid = sail_surface(top_l, top_r, bl, br, belly=0.11 * width)
            sails[f"{mast}_{key}"] = (grid, mw.copy(), f"SOCKET_YARD_{mast}_{key}")
    # randa (gaf – bumba)
    gaff, boom = bpy.data.objects["MOD_RIG_GAFF_MIZZEN_A"], bpy.data.objects["MOD_RIG_BOOM_MIZZEN_A"]

    def ends(o):
        pts = [o.matrix_world @ v.co for v in o.data.vertices]
        p0 = o.matrix_world.translation
        return p0, max(pts, key=lambda p: (p - p0).length)
    g0, g1 = ends(gaff)
    b0, b1 = ends(boom)
    grid = sail_surface(g0 + V((-0.05, 0, -0.1)), g1 + V((0.1, 0, -0.1)), b0 + V((-0.05, 0, 0.12)), b1 + V((0.3, 0, 0.12)),
                        belly=0.6, fwd=V((0, 1, 0)))
    sails["SPANKER"] = (grid, gaff.matrix_world.copy(), "SOCKET_GAFF_MIZZEN")
    # flok ve velena (üçgen: üst uç tekrar)
    bsp = bpy.data.objects["MOD_RIG_BOWSPRIT_A"]
    pts = [bsp.matrix_world @ v.co for v in bsp.data.vertices]
    tip = max(pts, key=lambda p: p.x)
    heel = bsp.matrix_world.translation
    fore = bpy.data.objects["MOD_RIG_MAST_FORE_A"]
    fpts = [fore.matrix_world @ v.co for v in fore.data.vertices]
    ftop = max(fpts, key=lambda p: p.z)
    head_jib = fore.matrix_world.translation.lerp(ftop, 0.78)
    head_st = fore.matrix_world.translation.lerp(ftop, 0.52)
    for name, head, tack, clew in (
        ("JIB", head_jib, tip + V((-0.4, 0, 0.1)), heel.lerp(tip, 0.48) + V((-1.5, 0.0, 1.8))),
        ("FORE_STAYSAIL", head_st, heel.lerp(tip, 0.55), heel.lerp(tip, 0.15) + V((-1.2, 0.0, 1.4))),
    ):
        grid = sail_surface(head, head + (head - tack) * 0.0001, tack, clew, belly=0.5, NU=10, NV=12, fwd=V((0, 1, 0)))
        sails[name] = (grid, bsp.matrix_world.copy(), "SOCKET_BOWSPRIT")
    obs = {}
    for name, (grid, mw, sock) in sails.items():
        bm = bmesh.new()
        w = (grid[0][-1] - grid[0][0]).length or (grid[-1][-1] - grid[-1][0]).length
        hgt = (grid[-1][len(grid[0]) // 2] - grid[0][len(grid[0]) // 2]).length
        grid_mesh(bm, grid, (w, hgt))
        ob = mk_object(f"MOD_SAIL_SET_{name}_A", bm, [M["canvas"]], col, origin_mw=mw, state="set", visible=False)
        ob["socket"] = sock
        obs[name] = (ob, grid)
    return obs


def build_emblems(col, col_s, set_sails):
    out, socks = [], []
    for sail, kind in EMBLEMS.items():
        if sail not in set_sails:
            continue
        ob, grid = set_sails[sail]
        NV, NU = len(grid) - 1, len(grid[0]) - 1
        # desen alanı: yelkenin orta bölgesi (u 0,28–0,72; v 0,18–0,78), karenin en/boy oranı korunur
        uc, vc = 0.5, 0.47
        w = (grid[NV // 2][-1] - grid[NV // 2][0]).length
        hgt = (grid[-1][NU // 2] - grid[0][NU // 2]).length
        size = min(w * 0.46, hgt * 0.62)
        du, dv = size / w / 2, size / hgt / 2

        def at(u, v):
            j = min(max(v, 0), 1) * NV
            i = min(max(u, 0), 1) * NU
            j0, i0 = min(int(j), NV - 1), min(int(i), NU - 1)
            fj, fi = j - j0, i - i0
            a = grid[j0][i0].lerp(grid[j0][i0 + 1], fi)
            b = grid[j0 + 1][i0].lerp(grid[j0 + 1][i0 + 1], fi)
            return a.lerp(b, fj)

        N = 10
        pts = [[at(uc - du + 2 * du * i / N, vc - dv + 2 * dv * j / N) for i in range(N + 1)] for j in range(N + 1)]
        bm = bmesh.new()
        uvl = bm.loops.layers.uv.verify()
        for side in (1, -1):                                   # iki yüz (baştan ve kıçtan görünür)
            vs = []
            for j in range(N + 1):
                row = []
                for i in range(N + 1):
                    p = pts[j][i]
                    a = pts[j][min(i + 1, N)] - pts[j][max(i - 1, 0)]
                    b = pts[min(j + 1, N)][i] - pts[max(j - 1, 0)][i]
                    n = a.cross(b).normalized()
                    row.append(bm.verts.new(p + n * 0.012 * side))
                vs.append(row)
            for j in range(N):
                for i in range(N):
                    q = [vs[j][i], vs[j][i + 1], vs[j + 1][i + 1], vs[j + 1][i]]
                    uvs = [(i / N, 1 - j / N), ((i + 1) / N, 1 - j / N), ((i + 1) / N, 1 - (j + 1) / N), (i / N, 1 - (j + 1) / N)]
                    if side < 0:
                        q.reverse()
                        uvs.reverse()
                        uvs = [(1 - u, v) for u, v in uvs]
                    f = bm.faces.new(q)
                    for loop, uv in zip(f.loops, uvs):
                        loop[uvl].uv = uv
        center = at(uc, vc)
        mw = Matrix.Translation(center) @ ob.matrix_world.to_3x3().to_4x4()
        eo = mk_object(f"MOD_SAIL_EMBLEM_{kind}_A_{sail}", bm, [emblem_material(kind)], col, origin_mw=mw, state="set", visible=False)
        eo["socket"] = f"SOCKET_SAIL_EMBLEM_{sail}"
        eo["emblem"] = kind.lower()
        P13.set_socket(f"SOCKET_SAIL_EMBLEM_{sail}", center, col_s, shape="PLAIN_AXES", size=0.3,
                       rot=ob.matrix_world.to_euler(), module_family="SailSet", accepts=["MOD_SAIL_EMBLEM_*"], sail=ob.name)
        out.append(eo)
        socks.append(f"SOCKET_SAIL_EMBLEM_{sail}")
    return out, socks


def set_state(state):
    for o in bpy.data.objects:
        st = o.get("sail_state")
        if st:
            vis = st == state
            o.hide_render = not vis
            o.hide_viewport = not vis


def render(sc):
    H.setup_render(sc, fast=True)
    out = ROOT / "renders" / VER
    out.mkdir(parents=True, exist_ok=True)
    D = V((0, 0, 1.0))
    K = 1.1
    shots = [
        ("furled", "sarili_bas_omzu", V((48, 38, 22)) * K + D, V((0, 0, 12)) * K + D, 32),
        ("furled", "sarili_seren_yakin", V((6.5, 9.0, 23.0)), V((1.8, 2.0, 20.4)), 30),
        ("set", "acik_bas_omzu", V((48, 38, 22)) * K + D, V((0, 0, 12)) * K + D, 32),
        ("set", "acik_kic_omzu", V((-46, -34, 18)) * K + D, V((0, 0, 12)) * K + D, 32),
        ("set", "acik_motif_yakin", V((-14, 16, 14)), V((3, 0, 16)), 30),
    ]
    for state, name, loc, tgt, lens in shots:
        set_state(state)
        sc.camera = H.camera(sc, f"CAM22_{name}", loc, tgt, lens=lens)
        sc.render.filepath = str(out / f"{SHIP}_{VER}_{name}.png")
        bpy.ops.render.render(write_still=True)
    set_state("furled")


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
    M["canvas"] = canvas_material()
    C = {c.name: c for c in bpy.data.collections}
    col, col_s = C["21_MODULES_SAILS"], C["30_SOCKETS"]
    dg = bpy.context.evaluated_depsgraph_get()

    def deck_z(x):
        return _deck_hit(sc, dg, x)

    furled = build_furled(col, M)
    set_sails = build_set(col, M, deck_z)
    emblems, esocks = build_emblems(col, col_s, set_sails)
    rp = bpy.data.objects["SOCKET_RIG_PRIMARY"]
    rp["sail_family"] = "OF1780_FULLSHIP_A"
    rp["sail_states"] = ["furled", "set"]
    rp["sail_state_default"] = "furled"
    bpy.ops.wm.save_as_mainfile(filepath=str(out), compress=True)
    H.VERSION = VER
    ap = ROOT / "reports" / f"scene_audit_{VER}.json"
    rep = H.audit(sc, ap)

    def tri(o):
        o.data.calc_loop_triangles()
        return len(o.data.loop_triangles)

    rep["sailset_v022"] = {"furled": [o.name for o in furled], "set": [o.name for o, _ in set_sails.values()],
                           "emblems": [o.name for o in emblems], "emblem_sockets": esocks,
                           "tris_furled": sum(tri(o) for o in furled), "tris_set": sum(tri(o) for o, _ in set_sails.values()),
                           "default_state": "furled", "textures": ["Textures/emblems/T_SailEmblem_Lale_A.png",
                                                                   "Textures/emblems/T_SailEmblem_Rumi_A.png"]}
    rep["pass"] = {"name": "pass_v022_sailset", "source": f"Blender/versions/{SHIP}_{SRC_VER}.blend",
                   "manifest_version": MANIFEST_VERSION, "geometry_changed": "SailSet modülleri eklendi"}
    ap.write_text(json.dumps(rep, indent=2, ensure_ascii=False), encoding="utf-8")
    print("V022", json.dumps({k: v for k, v in rep["sailset_v022"].items() if k.startswith("tris") or k == "emblems"}, ensure_ascii=False))
    if "--no-render" not in sys.argv:
        render(sc)


def _deck_hit(sc, dg, x):
    for z0 in (9.0, 7.0, 5.0):
        ok, loc, *_ = sc.ray_cast(dg, V((x, 0.3, z0)), V((0, 0, -1)), distance=8.0)
        if ok:
            return loc.z
    return 3.1


if __name__ == "__main__":
    main()
