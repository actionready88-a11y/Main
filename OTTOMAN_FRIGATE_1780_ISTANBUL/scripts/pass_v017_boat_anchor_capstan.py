"""Pass v017 — BoatSet (filika + kızaklar), AnchorSet (2 ana çapa + kedi başları), DeckUtility (ırgat), v016 üzerine.

Çalıştırma (depo kökünden):
    python3 OTTOMAN_FRIGATE_1780_ISTANBUL/scripts/pass_v017_boat_anchor_capstan.py [--no-render | --render-only]

Plan: MODELLEME_PLANI §6 madde 5 (BoatSet, AnchorSet) ve v002 listesi (ırgat). Soketler v001'den beri hazırdı
(SOCKET_BOAT_PRIMARY, SOCKET_ANCHOR_{PORT,STARBOARD}); ırgat için SOCKET_CAPSTAN eklenir.
Ölçüler TAHMİN (kaynak kullanılmadı): filika 7,0 m × 2,0 m; çapa gövdesi 3,6 m; ırgat başı çapı 1,3 m.
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


P16 = _load("pass_v016", "pass_v016_cabin_interior.py")
P15, P14, P13 = P16.P15, P16.P14, P16.P13
P5, H, K, C3 = P13.P5, P13.H, P13.K, P15.C3
SRC_VER, VER = "v016", "v017"
ROOT, SHIP = H.ROOT, H.SHIP_ID
MANIFEST_VERSION = 15
P5.MANIFEST_VERSION = MANIFEST_VERSION
DWL = P13.DWL
V = Vector

BOAT_L, BOAT_B, BOAT_D = 7.0, 2.0, 0.78
CAPSTAN_X = -4.10                 # dünya; ana ambar ızgarası ile kıç ambar ağzı arası
SHANK, ARM_SPAN, STOCK = 3.6, 2.3, 3.4


def mats():
    M = P16.mats()
    if "MAT_Boat_PaintWhite" not in bpy.data.materials:
        H.plank_material("MAT_Boat_PaintWhite", (0.62, 0.60, 0.55), (0.40, 0.38, 0.34), plank_w=0.12, rough=0.55, seam=0.003, bump=0.1)
    M["boat"] = bpy.data.materials["MAT_Boat_PaintWhite"]
    return M


# --- Filika ------------------------------------------------------------------------------
def boat_half(u):
    """u: -1 kıç (ayna), +1 baş. Yarı en oranı."""
    if u <= 0:
        return 0.55 + 0.45 * (1 - (-u) ** 2.2) ** 0.5
    return max(1 - u ** 1.9, 0.0) ** 0.62


def boat_sheer(u):
    return BOAT_D + 0.12 * u ** 2 + (0.06 * u if u > 0 else 0.0)


def boat_mesh(M):
    bs, bw, bo = bmesh.new(), bmesh.new(), bmesh.new()
    NU, NT = 28, 10
    grid = {}
    for i in range(NU + 1):
        u = -1 + 2 * i / NU
        x = u * BOAT_L / 2
        hb = BOAT_B / 2 * boat_half(u)
        top = boat_sheer(u)
        keel_rise = 0.10 * max(u, 0) ** 2 * 3
        for side in (1, -1):
            for j in range(NT + 1):
                t = j / NT                                 # 0 omurga, 1 küpeşte
                z = keel_rise + (top - keel_rise) * (1 - (1 - t) ** 1.6)
                y = side * max(hb * (1 - (1 - t) ** 2.4) ** 0.55, 0.02 if j else 0.0)
                grid[(i, side, j)] = bs.verts.new((x, y, z))
    for i in range(NU):
        for side in (1, -1):
            for j in range(NT):
                vs = [grid[(i, side, j)], grid[(i + 1, side, j)], grid[(i + 1, side, j + 1)], grid[(i, side, j + 1)]]
                if side < 0:
                    vs.reverse()
                bs.faces.new(vs)
    bmesh.ops.remove_doubles(bs, verts=bs.verts, dist=1e-4)
    # kıç aynası
    bs.verts.ensure_lookup_table()
    tr = [grid[(0, 1, j)] for j in range(NT + 1)] + [grid[(0, -1, j)] for j in reversed(range(NT + 1))]
    tr = [v for v in tr if v.is_valid]
    try:
        bs.faces.new(list(dict.fromkeys(tr)))
    except ValueError:
        pass
    ext = bmesh.ops.solidify(bs, geom=list(bs.faces), thickness=0.03) if hasattr(bmesh.ops, "solidify") else None
    # küpeşte (gunwale), omurga, bodoslama, oturaklar, kürekler
    for side in (1, -1):
        pts = []
        for i in range(NU + 1):
            u = -1 + 2 * i / NU
            pts.append(V((u * BOAT_L / 2, side * (BOAT_B / 2 * boat_half(u) + 0.01), boat_sheer(u) + 0.02)))
        P5.sweep_rect(bw, pts, 0.07, 0.06)
    P5.aabox(bw, -BOAT_L / 2, BOAT_L / 2 - 0.2, -0.05, 0.05, -0.10, 0.02)
    for k, u in enumerate((-0.55, -0.2, 0.15, 0.45)):
        hb = BOAT_B / 2 * boat_half(u) - 0.05
        z = boat_sheer(u) - 0.28
        P5.aabox(bw, u * BOAT_L / 2 - 0.12, u * BOAT_L / 2 + 0.12, -hb, hb, z, z + 0.05)
    P5.aabox(bw, -BOAT_L / 2 + 0.15, -BOAT_L / 2 + 1.1, -0.45, 0.45, 0.22, 0.26)      # kıç oturağı (stern sheets)
    for k in range(4):                                                                  # kürekler (oturaklar üstünde)
        y = -0.45 + k * 0.3
        P5.lathe(bo, [(0.0, 0.0), (0.025, 0.05), (0.025, 3.2), (0.06, 3.3), (0.06, 3.9), (0.0, 4.0)], 8,
                 Matrix.Translation((-1.9, y, boat_sheer(0.0) - 0.20)) @ Matrix.Rotation(math.radians(90), 4, "Y"))
    me = P16.make_mesh("MOD_BOAT_CUTTER_A", [(bs, M["boat"]), (bw, M["timber"]), (bo, M["spar"])])
    return me


def build_boat(C, M):
    sock = bpy.data.objects["SOCKET_BOAT_PRIMARY"]
    loc = sock.location.copy()
    ob = bpy.data.objects.new("MOD_BOAT_CUTTER_A", boat_mesh(M))
    C["23_MODULES_DECK"].objects.link(ob)
    ob.location = loc
    ob["module_family"] = "BoatSet"
    ob["socket"] = sock.name
    ob["dims_m"] = [BOAT_L, BOAT_B, BOAT_D]
    sock["installed_module"] = ob.name
    sock["manifest_version"] = MANIFEST_VERSION
    # kızaklar (skid beams) + dikmeler — Hull Core'a bağlı DeckUtility
    bw = bmesh.new()
    deck = lambda x: P14.deck_hit(bpy.context.scene, bpy.context.evaluated_depsgraph_get(), V((x, 0.0, loc.z - 0.6)))  # noqa: E731
    for dx in (-2.2, 2.2):
        x = loc.x + dx
        zd = deck(x) or (loc.z - 2.2)
        s = P13.s_of_x(x / K, P13.zu)
        half = (H.hull_point(s, P13.zu(s) + 1.5)[1] - 0.20) * K
        P5.aabox(bw, x - 0.12, x + 0.12, -half, half, loc.z - 0.22, loc.z)
        for yy in (-1.2, 1.2):
            P5.aabox(bw, x - 0.08, x + 0.08, yy - 0.08, yy + 0.08, zd, loc.z - 0.22)
        for yy in (-0.75, 0.75):                                                      # beşik takozları
            P5.aabox(bw, x - 0.10, x + 0.10, yy - 0.12, yy + 0.12, loc.z, loc.z + 0.18)
    sk = P5.finish("CORE_BOAT_SKIDS", bw, C["10_HULL_CORE"], [M["timber"]], bevel=0.01)
    ob.location.z += 0.10
    return ob, sk


# --- Çapa ----------------------------------------------------------------------------------
def anchor_mesh(M):
    """Yerel: orijin halka (ring) üstte; gövde -Z yönünde; kollar XZ düzleminde; çipo (stock) Y boyunca."""
    bi, bw = bmesh.new(), bmesh.new()
    P5.lathe(bi, [(0.0, -SHANK), (0.12, -SHANK), (0.115, -SHANK * 0.5), (0.085, -0.25), (0.07, -0.20), (0.0, -0.20)], 10, Matrix())
    ring_r, ring_t = 0.24, 0.045
    rings = []
    for k in range(16):                                       # halka (XZ düzleminde)
        a = 2 * math.pi * k / 16
        c = V((ring_r * math.cos(a), 0.0, -0.20 + ring_r + ring_r * math.sin(a) - 0.02))
        rings.append(c)
    P15.tube(bi, rings + [rings[0]], ring_t, seg=6)
    crown = V((0.0, 0.0, -SHANK))
    for sgn in (1, -1):                                       # kollar + tırnaklar (palms)
        pts = []
        for k in range(9):
            a = math.radians(sgn * (0 + 55 * k / 8))
            r = ARM_SPAN / 2 / math.sin(math.radians(55))
            pts.append(crown + V((r * math.sin(a) * 0.95, 0.0, r * (1 - math.cos(a)) * 0.9)))
        P15.tube(bi, pts, 0.105, seg=8)
        tip = pts[-1]
        d = (pts[-1] - pts[-3]).normalized()
        n = V((0, 1, 0))
        P15.obox(bi, tip - d * 0.30, d, n, d.cross(n), 0.32, 0.24, 0.035)
    for sgn in (1, -1):                                       # ahşap çipo, iki yarım, demir çemberli
        y0, y1 = sorted((sgn * 0.08, sgn * STOCK / 2))
        P5.box8(bw, [V((-0.14, y0, -0.44)), V((0.14, y0, -0.44)), V((0.09, y1, -0.40)), V((-0.09, y1, -0.40)),
                     V((-0.14, y0, -0.16)), V((0.14, y0, -0.16)), V((0.09, y1, -0.20)), V((-0.09, y1, -0.20))])
        for t in (0.25, 0.6, 0.92):
            y = sgn * (0.08 + t * (STOCK / 2 - 0.08))
            P5.aabox(bi, -0.15 + 0.05 * t, 0.15 - 0.05 * t, y - 0.03, y + 0.03, -0.45 + 0.04 * t, -0.15 - 0.04 * t)
    return P16.make_mesh("MOD_ANCHOR_BOWER_A", [(bi, M["iron"]), (bw, M["timber"])])


def hull_y_world(x, z):
    zd = (z - DWL) / K
    s = P13.s_of_x(x / K, lambda s_: zd)
    return H.hull_point(s, zd)[1] * K


def build_anchors(C, M):
    me = anchor_mesh(M)
    obs, cat_parts, info = [], bmesh.new(), {}
    for tag, sgn in (("STARBOARD", 1), ("PORT", -1)):
        sock = bpy.data.objects[f"SOCKET_ANCHOR_{tag}"]
        x = sock.location.x
        s_fc = P13.s_of_x(x / K, P13.zu)
        z_fc = (P13.zu(s_fc) + H.QD_H) * K + DWL
        z_cat = z_fc + 0.95
        y_hull = hull_y_world(x, z_cat)
        # dışa açıklık: çapanın tüm noktaları gövdeden ≥ 0,15 m dışarıda kalana dek artır
        out = 0.6
        R = Matrix.Rotation(math.radians(90.0), 3, "Z")        # çipo baş-kıç doğrultusunda, kollar bordaya dik
        for _ in range(40):
            ring = V((x + 0.5, sgn * (y_hull + out), z_cat - 0.05))
            ok = True
            for v in me.vertices:
                p = ring + R @ v.co
                if p.z < 0.2:
                    continue
                if abs(p.y) < hull_y_world(p.x, p.z) + 0.15:
                    ok = False
                    break
            if ok:
                break
            out += 0.1
        ob = bpy.data.objects.new(f"MOD_ANCHOR_BOWER_{tag}", me)
        C["24_MODULES_DECOR"].objects.link(ob)
        ob.location = ring
        ob.rotation_euler = (0.0, 0.0, math.radians(90.0))
        ob["module_family"] = "AnchorSet"
        ob["socket"] = sock.name
        ob["state_default"] = "catted"
        sock.location = ring
        sock["installed_module"] = ob.name
        sock["manifest_version"] = MANIFEST_VERSION
        obs.append(ob)
        # kedi başı (cathead): borda üstünden dışa ve hafif başa uzanan kalas
        y_in = sgn * (hull_y_world(x + 0.5, z_cat) - 0.6)
        a = V((x + 0.2, y_in, z_cat))
        b = V((x + 0.5, sgn * (y_hull + out + 0.10), z_cat + 0.10))
        d = (b - a)
        L = d.length
        d.normalize()
        up = V((0, 0, 1))
        side = up.cross(d).normalized()
        P15.obox(cat_parts, (a + b) / 2, d, side, side.cross(d).normalized() * -1, L / 2, 0.16, 0.16)
        P15.obox(cat_parts, b + d * 0.02, d, side, up, 0.04, 0.2, 0.2)
        info[tag] = {"outboard_m": round(out, 2), "ring_world": [round(v, 2) for v in ring]}
    cat = P5.finish("CORE_CATHEADS", cat_parts, C["10_HULL_CORE"], [M["timber"]], bevel=0.01)
    return obs, cat, info


# --- Irgat -----------------------------------------------------------------------------------
def capstan_mesh(M):
    bw, bi = bmesh.new(), bmesh.new()
    P5.lathe(bw, [(0.0, 0.0), (0.75, 0.0), (0.75, 0.08), (0.62, 0.10), (0.62, 0.16), (0.0, 0.16)], 24, Matrix())   # taban/pawl ring
    P5.lathe(bw, [(0.0, 0.16), (0.40, 0.16), (0.34, 0.55), (0.36, 0.72), (0.0, 0.72)], 24, Matrix())             # gövde (barrel)
    for k in range(8):                                                                                           # kamlar (whelps)
        a = 2 * math.pi * k / 8
        c = V((0.39 * math.cos(a), 0.39 * math.sin(a), 0.44))
        r = V((math.cos(a), math.sin(a), 0))
        P15.obox(bw, c, r, V((-math.sin(a), math.cos(a), 0)), V((0, 0, 1)), 0.06, 0.05, 0.27)
    P5.lathe(bw, [(0.0, 0.72), (0.65, 0.72), (0.66, 0.78), (0.65, 0.98), (0.55, 1.02), (0.0, 1.04)], 24, Matrix())  # başlık (drumhead)
    for k in range(10):                                                                                          # manivela yuvaları
        a = 2 * math.pi * k / 10
        c = V((0.62 * math.cos(a), 0.62 * math.sin(a), 0.88))
        r = V((math.cos(a), math.sin(a), 0))
        P15.obox(bi, c, r, V((-math.sin(a), math.cos(a), 0)), V((0, 0, 1)), 0.05, 0.07, 0.07)
    for k in range(4):                                                                                           # kastanyola (pawls)
        a = 2 * math.pi * k / 4 + 0.3
        c = V((0.66 * math.cos(a), 0.66 * math.sin(a), 0.06))
        P15.obox(bi, c, V((math.cos(a), math.sin(a), 0)), V((-math.sin(a), math.cos(a), 0)), V((0, 0, 1)), 0.10, 0.03, 0.03)
    return P16.make_mesh("MOD_CAPSTAN_A", [(bw, M["timber"]), (bi, M["iron"])])


def build_capstan(C, M):
    sc = bpy.context.scene
    dg = bpy.context.evaluated_depsgraph_get()
    z = P14.deck_hit(sc, dg, V((CAPSTAN_X, 0.0, 3.6)))
    ob = bpy.data.objects.new("MOD_CAPSTAN_A", capstan_mesh(M))
    C["23_MODULES_DECK"].objects.link(ob)
    ob.location = V((CAPSTAN_X, 0.0, z))
    ob["module_family"] = "DeckUtility"
    ob["socket"] = "SOCKET_CAPSTAN"
    col = C["30_SOCKETS"]
    P13.set_socket("SOCKET_CAPSTAN", ob.location, col, shape="ARROWS", size=0.5, module_family="DeckUtility")
    crew = []
    for k in range(10):                                                                            # manivela iticileri
        a = 2 * math.pi * k / 10 + math.pi / 10
        p = ob.location + V((2.1 * math.cos(a), 2.1 * math.sin(a), 0.0))
        n = f"SOCK_CREW_CAPSTAN_{k + 1:02d}"
        P13.set_socket(n, p, col, shape="SINGLE_ARROW", size=0.35, rot=(0, 0, a + math.pi / 2), crew_role="capstan_bar",
                       station="SOCKET_CAPSTAN", exclusive_with="battery_manned", note="manivelalar takılıyken (demir alma)")
        crew.append(n)
    return ob, crew


def collision(C, boat, skids, anchors, cat, capstan):
    col = C["40_COLLISION"]
    out = []

    def bbox_pts(o):
        return [o.matrix_world @ V(c) for c in o.bound_box]

    for o, purpose in ((boat, "boat"), (capstan, "capstan"), (cat, "cathead")):
        u = C3.convex(f"UCX_{o.name}_00", bbox_pts(o) if o is not boat else [o.matrix_world @ v.co for v in o.data.vertices],
                      col, purpose)
        u.name = u.data.name = f"UCX_{o.name}_00"
        u["owner_mesh"] = o.name
        out.append(u.name)
    for i, a in enumerate(anchors):
        u = C3.convex(f"UCX_{a.name}_00", [a.matrix_world @ v.co for v in a.data.vertices], col, "anchor")
        u.name = u.data.name = f"UCX_{a.name}_00"
        u["owner_mesh"] = a.name
        out.append(u.name)
    x0, x1, y0, y1, z0, z1 = P16.world_bbox(skids)
    for k, xc in enumerate((boat.location.x - 2.2, boat.location.x + 2.2)):
        u = C3.convex(f"UCX_CORE_BOAT_SKIDS_{k:02d}", [V((x, y, z)) for x in (xc - 0.12, xc + 0.12) for y in (y0, y1)
                                                          for z in (z1 - 0.32, z1)], col, "boat_skid")
        u["owner_mesh"] = "CORE_BOAT_SKIDS"
        out.append(u.name)
    return out


def checks(boat, capstan, crew_cap):
    res = {}
    dg = bpy.context.evaluated_depsgraph_get()
    x0, x1, y0, y1, z0, z1 = P16.world_bbox(boat)
    zdeck = P14.deck_hit(bpy.context.scene, dg, V(((x0 + x1) / 2, 0.0, z0 - 1.8)))
    res["boat_clearance_above_deck_m"] = round(z0 - zdeck, 3) if zdeck else None
    hatch = [o for o in bpy.data.objects if o.name == "SOCK_NAVLINK_LADDER_FORE_TOP"]
    res["fore_ladder_top_under_boat"] = bool(hatch and x0 < hatch[0].location.x < x1)
    near = []
    for o in bpy.data.objects:
        if o.type == "EMPTY" and o.name.startswith("SOCK_CREW_") and not o.name.startswith(("SOCK_CREW_CAPSTAN", "SOCK_CREW_LOWER")):
            if (o.location - capstan.location).length < 0.9:
                near.append(o.name)
    res["battery_crew_within_0p9m_of_capstan"] = near
    return res


def render(sc):
    H.setup_render(sc, fast=True)
    out = ROOT / "renders" / VER
    out.mkdir(parents=True, exist_ok=True)
    b = bpy.data.objects["MOD_BOAT_CUTTER_A"].location
    a = bpy.data.objects["MOD_ANCHOR_BOWER_STARBOARD"].location
    c = bpy.data.objects["MOD_CAPSTAN_A"].location
    views = [
        ("filika", b + V((-6.5, 6.5, 3.0)), b + V((0, 0, 0.3)), 28),
        ("capa_sancak", a + V((5.5, 7.5, -0.5)), a + V((0, 0, -1.8)), 30),
        ("irgat", c + V((3.2, 2.6, 2.2)), c + V((0, 0, 0.5)), 30),
        ("bas_omzu", V((48, 38, 22)) * K + V((0, 0, DWL)), V((0, 0, 12)) * K + V((0, 0, DWL)), 32),
    ]
    for name, loc, tgt, lens in views:
        sc.camera = H.camera(sc, f"CAM17_{name}", loc, tgt, lens=lens)
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
    M = mats()
    C = {c.name: c for c in bpy.data.collections}
    boat, skids = build_boat(C, M)
    anchors, cat, ainfo = build_anchors(C, M)
    capstan, crew_cap = build_capstan(C, M)
    bpy.context.view_layer.update()
    ucx = collision(C, boat, skids, anchors, cat, capstan)
    chk = checks(boat, capstan, crew_cap)
    bpy.ops.wm.save_as_mainfile(filepath=str(out), compress=True)
    H.VERSION = VER
    ap = ROOT / "reports" / f"scene_audit_{VER}.json"
    rep = H.audit(sc, ap)
    rep["v017"] = {"boat": {"module": boat.name, "dims_m": [BOAT_L, BOAT_B, BOAT_D]}, "anchors": ainfo,
                   "capstan": {"x_world": CAPSTAN_X, "crew": len(crew_cap)}, "ucx": ucx, "checks": chk,
                   "sources": "ölçüler TAHMİN"}
    rep["pass"] = {"name": "pass_v017_boat_anchor_capstan", "source": f"Blender/versions/{SHIP}_{SRC_VER}.blend",
                   "pass_changes": {"modules_added": [boat.name, capstan.name] + [a.name for a in anchors],
                                    "core_added": [skids.name, cat.name], "ucx_added": len(ucx)},
                   "manifest_version": MANIFEST_VERSION, "geometry_changed": "modüller + kızaklar + kedi başları"}
    ap.write_text(json.dumps(rep, indent=2, ensure_ascii=False), encoding="utf-8")
    print("V017", json.dumps(rep["v017"], ensure_ascii=False))
    if "--no-render" not in sys.argv:
        render(sc)


if __name__ == "__main__":
    main()
