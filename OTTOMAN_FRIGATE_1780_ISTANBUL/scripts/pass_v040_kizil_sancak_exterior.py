"""v040 — Kızıl Sancak dış kimliği (onaylı plan: reports/KIZIL_SANCAK_UYARLAMA_PLANI.md, Gate A: kullanıcı onayı).

    python3.11 OTTOMAN_FRIGATE_1780_ISTANBUL/scripts/pass_v040_kizil_sancak_exterior.py [--no-render | --render-only]

Gemi: Kızıl Sancak İmparatorluğu donanması (Kızıl Deniz Meclisi), ana üs Sancakkale, oyun içi adı "Kızıl Pençe"
(kullanıcı: "şimdilik"). Birebir Osmanlı sembolleri (ay-yıldız sancak, tuğra) özgün "Yelken Hilali"ne çevrilir.
 1. Sancak ve flandra: T_Flag_KizilSancak_A / T_Pennant_KizilSancak_A (kızıl zemin, altın işleme, Yelken Hilali,
    çatal uç — scripts/make_kizil_sancak_textures.py). Nesne adları KIZILSANCAK.
 2. Kurucu kırmızı yelken simgesi (kullanıcı seçimi: "ana yelkende kızıl bant"): ana mayistra ve ana gabyada orta
    dört bez eni (2,44 m) kızıl boyalı kanvas; bu iki yelkenin amblemi Yelken Hilali (2,2 m, iki yüz).
 3. Kıç arması: hilal-yıldız → Yelken Hilali kabartması; madalyon yeşil mine → kızıl mine.
 4. Top C namlusu: stilize tuğra (üç tuğ, beyze, taban) sökülür; aynı panelde Yelken Hilali kabartması
    (Alkan mührü). Kitabe kartuşu (stilize satırlar) kalır.
 5. Kıç ad levhası: pencere sırası altındaki bantta altın kabartma "KIZIL PENÇE".
 6. Kimlik: 00_CONTROLS/SHIP_IDENTITY boşu (faction, home_port, navy, ship_name, uyarlama planı).
Figür (ay-yıldız kabartması) en son uyarlanacak (kullanıcı kararı) — bu pass'te dokunulmaz.
"""

import importlib.util
import json
import math
import sys
from pathlib import Path

import bpy  # noqa: I001
import bmesh
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

HERE = Path(__file__).resolve().parent
sp = importlib.util.spec_from_file_location("pass_v033", HERE / "pass_v033_facet_cleanup.py")
P33 = importlib.util.module_from_spec(sp)
sp.loader.exec_module(P33)
P31 = P33.P31
RS, QA, LODS, H = P31.RS, P31.QA, P31.LODS, P31.H
ROOT, SHIP = P31.ROOT, P31.SHIP
SRC_VER, VER = "v039", "v040"
V = Vector
sys.path.insert(0, str(HERE))
import kizil_sancak as K  # noqa: E402

SHIP_NAME = "Kızıl Pençe"
TILE = 2.44
CLOTH = 0.61


def mw(o):
    return o.matrix_basis.copy() if o.parent is None else o.matrix_world.copy()


def sym_polys(R, cx=0.0, cy=0.0, n=360, waves=True):
    """Kızıl Sancak arması çokgenleri (kullanıcı konsepti), ölçek R; (cx, cy) armanın görsel ortası."""
    polys = K.sancak_armasi(n, waves=waves)
    ys = [y for p in polys for _, y in p]
    xs = [x for p in polys for x, _ in p]
    mx, my = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    return [[(cx + (x - mx) * R, cy + (y - my) * R) for x, y in p] for p in polys]


def copy_mat(src, name, image=None):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = src.copy()
    m.name = name
    if image:
        for n in m.node_tree.nodes:
            if n.type == "TEX_IMAGE":
                n.image = bpy.data.images.load(str(image), check_existing=True)
    return m


def rename_with_lods(old, new):
    out = []
    for o in [o for o in bpy.data.objects if o.name == old or o.name.startswith(old + "_LOD")]:
        o.name = o.name.replace(old, new, 1)
        if o.type == "MESH" and o.data.users == 1:
            o.data.name = o.name
        out.append(o.name)
    return out


def drop_lods(name):
    for o in [o for o in bpy.data.objects if o.name.startswith(name + "_LOD")]:
        me = o.data
        bpy.data.objects.remove(o, do_unlink=True)
        if me is not None and me.users == 0:
            bpy.data.meshes.remove(me)


# ------------------------------------------------------------------ 1. sancak / flandra
def flags():
    rep = {}
    tex = ROOT / "Textures" / "flags"
    for old, new, oldmat, newmat, img, design in (
            ("MOD_FLAG_ENSIGN_OTTOMAN_A", "MOD_FLAG_ENSIGN_KIZILSANCAK_A", "MAT_Flag_OttomanNavy1793_A", "MAT_Flag_KizilSancak_A",
             tex / "T_Flag_KizilSancak_A.png", "Kızıl Sancak: kızıl zemin, altın işleme kenar, Yelken Hilali, çatal uç"),
            ("MOD_FLAG_PENNANT_OTTOMAN_A", "MOD_FLAG_PENNANT_KIZILSANCAK_A", "MAT_Pennant_OttomanNavy_A", "MAT_Pennant_KizilSancak_A",
             tex / "T_Pennant_KizilSancak_A.png", "Kızıl Sancak flandrası: kızıl, altın kenar çizgisi, Yelken Hilali, çatal uç")):
        m = copy_mat(bpy.data.materials[oldmat], newmat, img)
        nt = m.node_tree                                   # çatal uç: doku alfası → BSDF alfa (kesik)
        ti = next(n for n in nt.nodes if n.type == "TEX_IMAGE")
        bs = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
        if not bs.inputs["Alpha"].is_linked:
            nt.links.new(ti.outputs["Alpha"], bs.inputs["Alpha"])
        m.surface_render_method = "DITHERED"
        names = rename_with_lods(old, new)
        for n in names:
            me = bpy.data.objects[n].data
            for i, s in enumerate(me.materials):
                if s and s.name == oldmat:
                    me.materials[i] = m
        bpy.data.objects[new]["design"] = design
        bpy.data.objects[new]["faction"] = "KIZIL_SANCAK"
        rep[new] = names
    return rep


# ------------------------------------------------------------------ 2. kızıl bant + amblem
def mat_canvas_kizil():
    m = bpy.data.materials.get("MAT_Sail_Canvas_B_Kizil")
    if m:
        return m
    m = bpy.data.materials["MAT_Sail_Canvas_B"].copy()
    m.name = "MAT_Sail_Canvas_B_Kizil"
    nt = m.node_tree
    mul = next(n for n in nt.nodes if n.type == "MIX" and n.blend_type == "MULTIPLY")
    tint = nt.nodes.new("ShaderNodeMix")
    tint.data_type, tint.blend_type = "RGBA", "MULTIPLY"
    tint.inputs["Factor"].default_value = 1.0
    tint.inputs["B"].default_value = (0.36, 0.020, 0.018, 1.0)          # kök boyalı kızıl kanvas [TAHMİN]
    nt.links.new(mul.outputs["Result"], tint.inputs["A"])
    for lk in list(nt.links):
        if lk.from_node == mul and lk.to_node != tint:
            to = lk.to_socket
            nt.links.remove(lk)
            nt.links.new(tint.outputs["Result"], to)
    m["kizil_sancak"] = "kurucu kırmızı yelken simgesi (Alkan Beyran efsanesi) — orta dört bez eni"
    return m


def sail_band(name, kizil):
    ob = bpy.data.objects[name]
    me = ob.data
    if kizil.name not in [m.name for m in me.materials if m]:
        me.materials.append(kizil)
    ki = [i for i, m in enumerate(me.materials) if m and m.name == kizil.name][0]
    # yelken yerel çerçevesi: yaka ve alt kenar Y = 0'a göre simetrik → bant, simetri ekseni etrafında ±2 bez eni
    cloth_faces = [p for p in me.polygons if p.material_index == 0]
    ys = [me.vertices[i].co.y for p in cloth_faces for i in p.vertices]
    W = max(ys) - min(ys)
    c = (max(ys) + min(ys)) / 2
    n = 0
    for p in cloth_faces:
        if abs(p.center.y - c) < 2 * CLOTH:
            p.material_index = ki
            n += 1
    return {"width_m": round(W, 2), "band_center_m": round(c, 2), "band_m": 4 * CLOTH, "faces": n}, c


def sail_decal(sail, emb_old, band_c, emat, size=2.2, grid=28):
    """Yelken Hilali amblemi: yelken yüzeyine iki yüzlü çıkartma (yelken yerel çerçevesinde, ışın izleme)."""
    me = sail.data
    tree = BVHTree.FromPolygons([v.co for v in me.vertices], [tuple(p.vertices) for p in me.polygons if p.material_index != 1])
    yc = band_c
    Me = mw(emb_old)
    Ms_inv = mw(sail).inverted()
    ec = [Ms_inv @ (Me @ v.co) for v in emb_old.data.vertices]
    zc = (min(p.z for p in ec) + max(p.z for p in ec)) / 2
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    for side in (1, -1):
        rows = []
        for i in range(grid + 1):
            row = []
            for j in range(grid + 1):
                u, v = j / grid, i / grid
                y = yc + (0.5 - u) * size          # önden bakınca soldan sağa (yerel -Y sağ)
                z = zc + (v - 0.5) * size
                hit = tree.ray_cast(V((side * 6.0, y, z)), V((-side, 0, 0)), 20.0)
                if hit[0] is None:
                    row.append(None)
                    continue
                nrm = hit[1] if hit[1].x * side > 0 else -hit[1]
                row.append((bm.verts.new(hit[0] + nrm * 0.012), (u, v)))
            rows.append(row)
        for i in range(grid):
            for j in range(grid):
                q = [rows[i][j], rows[i][j + 1], rows[i + 1][j + 1], rows[i + 1][j]]
                if any(x is None for x in q):
                    continue
                if side < 0:
                    q = q[::-1]
                f = bm.faces.new([x[0] for x in q])
                f.smooth = True
                for lp, x in zip(f.loops, q):
                    lp[uvl].uv = x[1]
    nme = bpy.data.meshes.new("_decal")
    bm.to_mesh(nme)
    bm.free()
    nme.materials.append(emat)
    old = emb_old.data
    emb_old.data = nme
    emb_old.parent = None
    emb_old.matrix_basis = mw(sail)
    if old.users == 0:
        bpy.data.meshes.remove(old)
    return {"size_m": size, "faces": len(nme.polygons), "center_local": [round(yc, 2), round(zc, 2)]}


def sails():
    kizil = mat_canvas_kizil()
    emat = copy_mat(bpy.data.materials["MAT_SailEmblem_Lale_A"], "MAT_SailEmblem_KizilSancak_A",
                    ROOT / "Textures" / "emblems" / "T_SailEmblem_KizilSancak_A.png")
    rep = {}
    for sail_name, emb_name, new_emb in (("MOD_SAIL_SET_MAIN_COURSE_A", "MOD_SAIL_EMBLEM_RUMI_A_MAIN_COURSE", "MOD_SAIL_EMBLEM_HILAL_A_MAIN_COURSE"),
                                         ("MOD_SAIL_SET_MAIN_TOPSAIL_A", "MOD_SAIL_EMBLEM_LALE_A_MAIN_TOPSAIL", "MOD_SAIL_EMBLEM_HILAL_A_MAIN_TOPSAIL")):
        info, c = sail_band(sail_name, kizil)
        drop_lods(emb_name)
        emb = bpy.data.objects[emb_name]
        info["emblem"] = sail_decal(bpy.data.objects[sail_name], emb, c, emat)
        emb.name = new_emb
        emb.data.name = new_emb
        emb["design"] = "Kızıl Sancak arması (hilal, mızrak, gök yıldızı, dalgalar), iki yüzlü boya"
        rep[sail_name] = info
    return rep


# ------------------------------------------------------------------ 3. kıç arması
def stern_crest():
    P31.__dict__["K_SYMS"] = sym_polys(0.19, 0.0, -0.01)
    P33.patch_default("stern_crest", """    extrude_shape(bm, crescent2d(0.24, 0.20, 0.07, 96), (o + U * -0.02, U, Vv, N), 0.035, 0.05, mat=0)
    extrude_shape(bm, star2d(0.20, 0.0, 0.085, 0.036, 8), (o, U, Vv, N), 0.035, 0.05, mat=0)""",
                      """    for _p in K_SYMS:                                    # v040: Kızıl Sancak arması (kullanıcı konsepti)
        extrude_shape(bm, _p, (o, U, Vv, N), 0.035, 0.05, mat=0)""")
    P33.patch_default("stern_crest", "ogee2d(0.78, 0.92, 160)", "ogee2d(0.78, 0.92, 320)")
    P33.patch_default("stern_crest", "ring_o = ogee2d(0.86, 1.00, 160)", "ring_o = ogee2d(0.86, 1.00, 320)")
    P33.patch_default("rumi_wing2d", "def rumi_wing2d(s, n=96):", "def rumi_wing2d(s, n=200):")
    col = bpy.data.objects["MOD_ORN_STERN_CREST"].users_collection[0]
    drop_lods("MOD_ORN_STERN_CREST")
    M = P31.mats()
    red = bpy.data.materials.get("MAT_Orn_Enamel_Crimson")
    if red is None:
        red = M["green"].copy()
        red.name = "MAT_Orn_Enamel_Crimson"
        b = next(n for n in red.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        b.inputs["Base Color"].default_value = (0.30, 0.012, 0.016, 1)
    M = dict(M)
    M["green"] = red
    ob = P31.stern_crest(M, col)
    ob["note"] = "Kızıl Sancak arması (hilal, mızrak, gök yıldızı, dalgalar — kullanıcı konsepti) kızıl mine madalyon üzerinde; rumi kanatlar üslup esinli [TAHMİN]"
    return {"faces": len(ob.data.polygons)}


# ------------------------------------------------------------------ 4. top mührü
def _inside(poly, pts):
    """Çift-tek ışın testi (numpy): pts (N,2) çokgen içinde mi."""
    import numpy as np
    P = np.asarray(poly)
    x, y = pts[:, 0], pts[:, 1]
    ins = np.zeros(len(pts), bool)
    j = len(P) - 1
    for i in range(len(P)):
        xi, yi, xj, yj = P[i, 0], P[i, 1], P[j, 0], P[j, 1]
        c = ((yi > y) != (yj > y)) & (x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi)
        ins ^= c
        j = i
    return ins


def relief(bm_dst, tree, polys, O, U, Vv, N, depth, mat=0, step=0.004):
    """2B çokgenleri yüzeye oturtup depth kabartır. Kapak: sınır + iç ızgara noktaları üzerinde Delaunay
    (ince uzun üçgen yok; eğri yüzeyi izler), yan duvar sınırdan yüzeyin 1,5 mm altına."""
    import numpy as np
    from scipy.spatial import Delaunay
    made = 0
    for poly in polys:
        B = np.asarray(poly, float)
        lo, hi = B.min(axis=0), B.max(axis=0)
        gx, gy = np.meshgrid(np.arange(lo[0], hi[0], step), np.arange(lo[1], hi[1], step))
        G = np.stack([gx.ravel(), gy.ravel()], axis=1)
        G = G[_inside(B, G)]
        # sınıra çok yakın iç noktaları at (ince üçgen önlemi)
        if len(G):
            d = np.min(np.linalg.norm(G[:, None, :] - B[None, ::2, :], axis=2), axis=1)
            G = G[d > step * 0.6]
        Pts = np.vstack([B, G])
        tri = Delaunay(Pts).simplices
        cen = Pts[tri].mean(axis=1)
        tri = tri[_inside(B, cen)]
        proj = []
        for u, v in Pts:
            p = O + U * u + Vv * v
            hit = tree.ray_cast(p + N * 0.3, -N, 1.0)
            proj.append(hit if hit[0] is not None else None)
        if any(h is None for h in proj):
            continue
        top = [bm_dst.verts.new(h[0] + h[1] * depth) for h in proj]
        nb = len(B)
        base = [bm_dst.verts.new(proj[i][0] - proj[i][1] * 0.0015) for i in range(nb)]
        for a, b, c in tri:
            pa, pb, pc = Pts[a], Pts[b], Pts[c]
            if (pb[0] - pa[0]) * (pc[1] - pa[1]) - (pb[1] - pa[1]) * (pc[0] - pa[0]) < 0:
                b, c = c, b
            try:
                f = bm_dst.faces.new([top[a], top[b], top[c]])
                f.material_index, f.smooth = mat, True
            except ValueError:
                pass
        for i in range(nb):                      # CCW sınır: dış normal yönünde duvar
            a, b = i, (i + 1) % nb
            f = bm_dst.faces.new([top[b], top[a], base[a], base[b]])
            f.material_index, f.smooth = mat, True
        made += 1
    return made


def cannon_seal():
    me = bpy.data.meshes["MOD_CANNON_OTTOMAN_C_BARREL"]
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.faces.index_update()
    kill = []
    removed = 0
    for isl in RS.islands(bm):
        vs = {v for f in isl for v in f.verts}
        lo = [min(v.co[i] for v in vs) for i in range(3)]
        hi = [max(v.co[i] for v in vs) for i in range(3)]
        # tuğra: panel (x −0,726…−0,526) üzerindeki küçük tüp adaları; panelin kendisi (284) ve kenarı (112) kalır
        if lo[0] > -0.70 and hi[0] < -0.55 and lo[2] > 0.175 and len(isl) <= 104:
            kill += list(vs)
            removed += 1
    bmesh.ops.delete(bm, geom=list(set(kill)), context="VERTS")
    tree = BVHTree.FromBMesh(bm)
    polys = sym_polys(0.046, 0.0, 0.0, waves=False)
    O, U, Vv, N = V((-0.626, 0.0, 0.0)), V((0, -1, 0)), V((1, 0, 0)), V((0, 0, 1))
    made = relief(bm, tree, polys, O, U, Vv, N, 0.0045, mat=0, step=0.004)
    bm.to_mesh(me)
    bm.free()
    RS.sharp_from_angle_keep(me, 30)
    users = [o.name for o in bpy.data.objects if o.type == "MESH" and o.data == me]
    return {"tugra_islands_removed": removed, "seal_shapes": made, "barrel_users": len(users)}, users


# ------------------------------------------------------------------ 5. ad levhası
def name_board(col):
    sc = bpy.context.scene
    dg = bpy.context.evaluated_depsgraph_get()
    z = 4.75
    xs = []
    for y in (-1.2, -0.6, 0.0, 0.6, 1.2):
        ok, loc, n, *_ = sc.ray_cast(dg, V((-30.0, y, z)), V((1, 0, 0)), distance=15.0)
        if ok:
            xs.append(loc.x)
    x_face = (min(xs) if xs else -21.0) - 0.004
    cu = bpy.data.curves.new("_name", "FONT")
    cu.body = "KIZIL PENÇE" if SHIP_NAME == "Kızıl Pençe" else SHIP_NAME.upper()
    font = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
    try:
        cu.font = bpy.data.fonts.load(font, check_existing=True)
    except RuntimeError:
        pass
    cu.size = 0.21
    cu.align_x, cu.align_y = "CENTER", "CENTER"
    cu.extrude = 0.008
    cu.bevel_depth = 0.0025
    cu.bevel_resolution = 3
    cu.resolution_u = 24
    cu.space_character = 1.12
    tmp = bpy.data.objects.new("_name", cu)
    sc.collection.objects.link(tmp)
    dg.update()
    me = bpy.data.meshes.new_from_object(tmp.evaluated_get(dg))
    bpy.data.objects.remove(tmp, do_unlink=True)
    bpy.data.curves.remove(cu)
    # yazı düzlemi (XY) → kıç yüzü: yazı sağa (−Y, arkadan bakınca), yukarı Z, dışa −X
    R = Matrix(((0, 0, -1, 0), (-1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 0, 1)))
    me.transform(Matrix.Translation(V((x_face - 0.008, 0.0, z))) @ R)
    for p in me.polygons:
        p.use_smooth = True
    me.materials.clear()
    me.materials.append(bpy.data.materials["MAT_Trim_Gilt"])     # kızıl kaplama üstünde altın kabartma harf (konsept)
    P31.geo_uv(me)
    RS.sharp_from_angle_keep(me, 30)
    ob = P31.new_object("MOD_ORN_STERN_NAMEBOARD", me, col, socket="SOCKET_ORN_STERN_NAME")
    ob["ship_name"] = SHIP_NAME
    ob["variant"] = "KIZIL_SANCAK_A"
    ob["note"] = "kıç pencere sırasının altında kızıl kaplama üstünde altın kabartma harfler (DejaVu Serif Bold); ad kullanıcı tarafından 'şimdilik' seçildi"
    xs2 = [v.co.x for v in me.vertices]
    ys2 = [v.co.y for v in me.vertices]
    return {"text": "KIZIL PENÇE", "width_m": round(max(ys2) - min(ys2), 2), "x_face": round(x_face, 3), "z": z,
            "faces": len(me.polygons), "depth_m": round(max(xs2) - min(xs2), 3)}


# ------------------------------------------------------------------ 6. kimlik
def identity():
    ctrl_col = bpy.data.collections.get("00_CONTROLS")
    e = bpy.data.objects.get("SHIP_IDENTITY") or bpy.data.objects.new("SHIP_IDENTITY", None)
    if ctrl_col and e.name not in ctrl_col.objects:
        ctrl_col.objects.link(e)
    for k, v in ({"faction": "KIZIL_SANCAK", "faction_display": "Kızıl Sancak İmparatorluğu", "home_port": "Sancakkale",
              "navy": "Kızıl Deniz Meclisi", "ship_name": SHIP_NAME, "ship_name_status": "geçici (kullanıcı: şimdilik)",
              "ship_class": "frigate", "symbol": "Kızıl Sancak arması: yukarı açık hilal, lale uçlu mızrak, pusula biçimli gök yıldızı, üç dalga (kullanıcı konsepti)", "motto": "Dalgalarda Daima",
              "design_plan": "reports/KIZIL_SANCAK_UYARLAMA_PLANI.md", "lore_source": "Project Pirate tasarım paketi (depoda değil)"}).items():
        e[k] = v
    bpy.context.scene["faction"] = "KIZIL_SANCAK"
    bpy.context.scene["ship_name"] = SHIP_NAME
    return dict(e.items())


# ------------------------------------------------------------------ render
def render(sc):
    for o in bpy.data.objects:
        st = o.get("sail_state")
        if st and o.animation_data:
            for fc in list(o.animation_data.drivers):
                if fc.data_path in ("hide_render", "hide_viewport"):
                    o.animation_data.drivers.remove(fc)
        if st:
            o.hide_render = o.hide_viewport = (st == "furled")
    H.setup_render(sc, fast=True)
    sc.cycles.samples = 32
    out = ROOT / "renders" / VER
    out.mkdir(parents=True, exist_ok=True)
    gun = max((o for o in bpy.data.objects if o.type == "MESH" and o.data.name == "MOD_CANNON_OTTOMAN_C_BARREL"),
              key=lambda o: (o.matrix_world.translation.y, -abs(o.matrix_world.translation.x)))
    g = gun.matrix_world
    fo = bpy.data.objects["MOD_FLAG_ENSIGN_KIZILSANCAK_A"]
    fws = [fo.matrix_world @ v.co for v in fo.data.vertices]
    fc = sum(fws, V()) / len(fws)
    shots = (("kic", V((-34, 0, 7.5)), V((-21, 0, 6.0)), 50),
             ("sancak", fc + V((4.5, 7.5, 0.8)), fc, 40),
             ("yelken_bant", V((-24, 22, 16)), V((3, 0, 18)), 32),
             ("top_muhru", g @ V((-1.3, 0.35, 0.9)), g @ V((-0.62, 0.0, 0.18)), 55),
             ("ad_levhasi", V((-24.5, 0.0, 4.9)), V((-20.5, 0.0, 4.75)), 50))
    for name, loc, tgt, lens in shots:
        sc.camera = H.camera(sc, f"CAM40_{name}", loc, tgt, lens=lens)
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
    bpy.context.view_layer.update()
    rep = {"flags": flags(), "sails": sails(), "stern_crest": stern_crest()}
    rep["cannon_seal"], gun_users = cannon_seal()
    rep["name_board"] = name_board(bpy.data.collections[P31.COL])
    rep["identity"] = identity()
    P31.switch([bpy.data.objects["MOD_ORN_STERN_CREST"], bpy.data.objects["MOD_ORN_STERN_NAMEBOARD"]])
    changed = {"MOD_FLAG_ENSIGN_KIZILSANCAK_A", "MOD_FLAG_PENNANT_KIZILSANCAK_A", "MOD_SAIL_SET_MAIN_COURSE_A",
               "MOD_SAIL_SET_MAIN_TOPSAIL_A", "MOD_SAIL_EMBLEM_HILAL_A_MAIN_COURSE", "MOD_SAIL_EMBLEM_HILAL_A_MAIN_TOPSAIL",
               "MOD_ORN_STERN_CREST", "MOD_ORN_STERN_NAMEBOARD"} | set(gun_users)
    for n in list(changed) + ["MOD_CANNON_OTTOMAN_C_BARREL"]:
        drop_lods(n)
    LODS.build_lods(sc, only=changed)
    bpy.ops.wm.save_as_mainfile(filepath=str(out), compress=True)
    H.VERSION = VER
    ap = ROOT / "reports" / f"scene_audit_{VER}.json"
    arep = H.audit(sc, ap)
    arep["kizil_sancak_v040"] = rep
    arep["pass"] = {"name": "pass_v040_kizil_sancak_exterior", "source": f"Blender/versions/{SHIP}_{SRC_VER}.blend"}
    ap.write_text(json.dumps(arep, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    qa = QA.audit(sc, top=60)
    dg = bpy.context.evaluated_depsgraph_get()
    extra = {}
    for n in ("MOD_SAIL_SET_MAIN_COURSE_A", "MOD_SAIL_SET_MAIN_TOPSAIL_A", "MOD_SAIL_EMBLEM_HILAL_A_MAIN_COURSE",
              "MOD_SAIL_EMBLEM_HILAL_A_MAIN_TOPSAIL"):
        m = QA.facet_metrics(bpy.data.objects[n], dg)
        extra[n] = {"tris": m[0], "facet_m": round(m[1], 2), "worst_sag_mm": round(m[5] * 1000, 1)}
    qa["open_sails"] = extra
    (ROOT / "reports" / f"kalite_testi_{VER}.json").write_text(json.dumps(qa, indent=1, ensure_ascii=False), encoding="utf-8")
    print("V040", json.dumps({k: v for k, v in rep.items() if k != "identity"}, ensure_ascii=False, default=str))
    print("V040 QA", json.dumps(qa["summary"], ensure_ascii=False), json.dumps(extra, ensure_ascii=False))
    for r in [r for r in qa["objects"] if r["fail"]]:
        print(f"  HATA {r['name']} facet={r['facet_m']}m sag={r['worst_sag_mm']}mm havada={r['floating_islands'][:2]}")
    if "--no-render" not in sys.argv:
        render(sc)


if __name__ == "__main__":
    main()
