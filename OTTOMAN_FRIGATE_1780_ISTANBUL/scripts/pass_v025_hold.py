"""Pass v025 — Ambar (hold) iç mekânı, v024 üzerine.

Çalıştırma (depo kökünden):
    python3 OTTOMAN_FRIGATE_1780_ISTANBUL/scripts/pass_v025_hold.py [--no-render | --render-only]

Kullanıcı sırası (2026-09-26): bayrak → "ambar içi" → LOD/bake. "Her yer gezilebilir" kararı gereği ambar oynanabilir olur.
- Ambar tabanı (ceiling/platform) alt güvertenin 2,53 m (dünya) altında; alt güverte kirişleri (CORE_DECK_BEAMS_LOWER)
  ambar tavanında. Taban ambarın orta bölümünde (s 0,12–0,88): uçlarda gövde daralır.
- Erişim: alt güvertede ana ambar ağzı (üst güvertedeki ızgaralı ambar ağzının tam altı), koaming + iniş merdiveni.
- Direk topukları: üç direk ambarda omurgaya kadar görünür (MOD_RIG_MAST_*_HEEL_A) + ıskaça (mast step) takozları.
- Yük: iki yanda iki sıra fıçı istifi (orta yol boş), halat (demir zinciri yerine palamar) roda kangalları pruvada,
  ana direk dibinde gülle dolabı, kıçta sandık istifi. 4 asma fener soketi.
- Çarpışma: ambar altı dolu dilimler tabana kadar, ambar borda duvarları, taban, yük blokları; alt güverte UCX'i
  ambar ağzı delikli olarak yeniden kuruldu.
Ölçüler TAHMİN.
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


P15 = _load("pass_v015", "pass_v015_rigset.py")
P13, P5, H, C3 = P15.P13, P15.P5, P15.H, P15.C3
P16 = _load("pass_v016", "pass_v016_cabin_interior.py")
SRC_VER, VER = "v024", "v025"
ROOT, SHIP = H.ROOT, H.SHIP_ID
MANIFEST_VERSION = 22
P5.MANIFEST_VERSION = MANIFEST_VERSION
V = Vector
K, DWL = P13.K, P13.DWL
DH = 2.30                          # alt güverte → ambar tabanı (tasarım) = 2,53 m dünya
S_HOLD = (0.12, 0.88)
HATCH = (-2.30, -0.70, 0.70)       # tasarım: x0, x1, |y| (üst güvertedeki ana ambar ağzının altı)
LADDER_RUN, LADDER_STEPS = 1.45, 10


def zh(s):
    return P13.zl(s) - DH


def build_floor_and_beams(core, M):
    obs = []
    fl = H.deck_surface("CORE_HOLD_FLOOR", S_HOLD[0], S_HOLD[1], zh, core, M["deck"])
    obs.append(P13.place(fl))
    # alt güverte kirişleri (ambar tavanı)
    bm = bmesh.new()
    xs = np.arange(P13.x_at(S_HOLD[0], zh(S_HOLD[0])) + 0.4, P13.x_at(S_HOLD[1], zh(S_HOLD[1])) - 0.2, P13.BEAM_STEP)
    used = []
    for x in xs:
        if HATCH[0] - 0.2 < x < HATCH[1] + 0.2:
            continue
        used.append(float(x))
        s = P13.s_of_x(x, P13.zl)
        half = P13.inner_half(s, P13.zl(s) - 0.2) + 0.05
        ys = np.linspace(-half, half, 13)
        for a, b in zip(ys[:-1], ys[1:]):
            ta = P13.deck_top(x, a, P13.zl) - P13.DECK_T
            tb = P13.deck_top(x, b, P13.zl) - P13.DECK_T
            x0, x1 = x - P13.BEAM_W / 2, x + P13.BEAM_W / 2
            P5.box8(bm, [V((x0, a, ta - P13.BEAM_D)), V((x1, a, ta - P13.BEAM_D)), V((x1, b, tb - P13.BEAM_D)), V((x0, b, tb - P13.BEAM_D)),
                         V((x0, a, ta)), V((x1, a, ta)), V((x1, b, tb)), V((x0, b, tb))])
    ob = P5.finish("CORE_DECK_BEAMS_LOWER", bm, core, [M["timber"]], bevel=0.01)
    obs.append(P13.place(ob))
    return obs, used


def build_hatch_and_ladder(core, M):
    x0, x1, hy = HATCH
    deck = bpy.data.objects["CORE_DECK_LOWER"]
    bm = bmesh.new()
    s = P13.s_of_x((x0 + x1) / 2, P13.zl)
    z = P13.zl(s)
    P5.aabox(bm, x0, x1, -hy, hy, z - 0.5, z + 0.5)
    cut = H.obj_from_bmesh("CUT_HATCH_HOLD", bm, core)
    cut.display_type = "WIRE"
    cut.hide_render = True
    P13.place(cut)
    cut.hide_set(True)
    cut.hide_viewport = True
    mod = deck.modifiers.new("HatchHold", "BOOLEAN")
    mod.operation = "DIFFERENCE"
    mod.object = cut
    mod.solver = "EXACT"
    bc = bmesh.new()
    zb = P13.deck_top((x0 + x1) / 2, hy, P13.zl) - 0.04
    zt = P13.deck_top((x0 + x1) / 2, 0.0, P13.zl) + P13.COAM_H
    c = P13.COAM_W
    for bx in ((x0 - c, x1 + c, hy, hy + c), (x0 - c, x1 + c, -hy - c, -hy), (x0 - c, x0, -hy, hy), (x1, x1 + c, -hy, hy)):
        P5.aabox(bc, bx[0], bx[1], bx[2], bx[3], zb, zt)
    co = P5.finish("CORE_HATCH_COAMING_HOLD", bc, core, [M["timber"]], bevel=0.01)
    P13.place(co)
    xt = x0 + 0.05
    xb = xt + LADDER_RUN
    p1 = V((xt, 0.0, P13.deck_top(xt, 0.0, P13.zl)))
    p0 = V((xb, 0.0, P13.deck_top(xb, 0.0, zh)))
    bms = (bmesh.new(), bmesh.new(), bmesh.new())
    st = P13.P8.stair(bms, p0, p1, width=P13.LADDER_W, n=LADDER_STEPS)
    lad = P13.P8.merge_finish("CORE_LADDER_HOLD", list(zip(bms, (M["deck"], M["timber"], M["yellow"]))), core)
    lad.data.transform(P13.SHIFT)
    return [cut, co, lad], dict(x_top=xt, x_bottom=xb, z_top=p1.z, z_bottom=p0.z, zt=zt, zd=zb + 0.04, **st)


def build_mast_heels(rig, M):
    obs = []
    for name in ("FORE", "MAIN", "MIZZEN"):
        m = P15.Mast(name)
        bw, bb = bmesh.new(), bmesh.new()
        t0 = (P15.HEEL_Z - m.base.z) / math.cos(m.rake)
        P15.spar(bw, m.P(t0), m.P(m.t_low + 0.02), m.D * 0.48, m.D / 2, seg=20)
        c = m.P(t0)
        P5.aabox(bb, c.x - 0.6, c.x + 0.6, -0.45, 0.45, c.z - 0.35, c.z + 0.05)                  # ıskaça
        ob = P15.finish(f"MOD_RIG_MAST_{name}_HEEL_A", [(bw, M["spar"]), (bb, M["timber"])], rig, origin=P15.W(m.base))
        ob["module_family"] = "RigSet"
        ob["note"] = "direğin ambardaki topuk kısmı (alt güverteden omurgaya)"
        obs.append(ob)
    return obs


def cask(bm_w, bm_i, c, axis_y, r=0.30, L=0.80):
    """Yatık fıçı (ekseni Y): göbekli profil + 2 demir çember (oyun bütçesi: ~130 üçgen)."""
    prof = [(0.0, -L / 2), (r * 0.82, -L / 2)]
    for k in range(5):
        t = k / 4
        prof.append((r * (0.84 + 0.16 * math.sin(math.pi * t)), -L / 2 + 0.02 + (L - 0.04) * t))
    prof += [(r * 0.82, L / 2), (0.0, L / 2)]
    T = Matrix.Translation(c) @ Matrix.Rotation(math.radians(-90), 4, "X")
    P5.lathe(bm_w, prof, 10, T)
    for t in (0.18, 0.82):
        y = -L / 2 + L * t
        rr = r * (0.84 + 0.16 * math.sin(math.pi * t)) + 0.006
        P5.lathe(bm_i, [(rr, y), (rr, y + 0.035)], 10, T)


def build_cargo(dec, M, sc, dg):
    bw, bi, bc = bmesh.new(), bmesh.new(), bmesh.new()
    blocks = []
    zfloor = lambda x, y: P14_floor(sc, dg, x, y)  # noqa: E731
    for xa, xb in ((-8.6, -4.0), (0.6, 7.6)):                       # fıçı istifleri (dünya)
        for sgn in (1, -1):
            xs = np.arange(xa, xb, 0.66)
            for x in xs:
                z0 = zfloor(x, sgn * 1.6)
                if z0 is None:
                    continue
                half = hold_half(x, z0 + 0.4)
                ys = [y for y in np.arange(1.15, half - 0.35, 0.86)]
                for y in ys:
                    cask(bw, bi, V((x, sgn * y, z0 + 0.30)), True)
                    if y < half - 0.9:
                        cask(bw, bi, V((x + 0.33, sgn * (y + 0.43), z0 + 0.82)), True)
                if ys:
                    blocks.append(((x - 0.33, x + 0.33), sorted((sgn * 1.0, sgn * (ys[-1] + 0.35))), (z0, z0 + 1.15)))
    # roda (palamar) kangalları — pruva
    for sgn in (1, -1):
        x = 9.4
        z0 = zfloor(x, sgn * 1.5)
        if z0 is not None:
            for k in range(7):
                rr = 0.95 - k * 0.09
                ring = [V((x + rr * math.cos(2 * math.pi * j / 24), sgn * 1.5 + rr * math.sin(2 * math.pi * j / 24), z0 + 0.09 + (k % 3) * 0.17))
                        for j in range(25)]
                P15.tube(bc, ring, 0.085, seg=6)
            blocks.append(((x - 1.0, x + 1.0), sorted((sgn * 0.5, sgn * 2.5)), (z0, z0 + 0.55)))
    # gülle dolabı — ana direk topuğunun kıçında
    xm = bpy.data.objects["SOCKET_MAST_MAIN"].location.x - 1.1
    z0 = zfloor(xm, 0.0)
    if z0 is not None:
        P5.aabox(bw, xm - 0.45, xm + 0.45, -0.7, 0.7, z0, z0 + 0.9)
        for i in range(6):
            for j in range(9):
                r = bmesh.ops.create_uvsphere(bi, u_segments=8, v_segments=6, radius=0.05)
                bmesh.ops.translate(bi, vec=(xm - 0.35 + i * 0.14, -0.6 + j * 0.15, z0 + 0.95), verts=r["verts"])
        blocks.append(((xm - 0.45, xm + 0.45), (-0.7, 0.7), (z0, z0 + 1.0)))
    # sandık istifi — kıç
    for k, (x, y) in enumerate(((-10.9, 1.6), (-10.9, -1.6), (-11.8, 1.3), (-11.8, -1.3))):
        z0 = zfloor(x, y)
        if z0 is None:
            continue
        P5.aabox(bw, x - 0.4, x + 0.4, y - 0.35, y + 0.35, z0, z0 + 0.6)
        if k < 2:
            P5.aabox(bw, x - 0.35, x + 0.35, y - 0.3, y + 0.3, z0 + 0.6, z0 + 1.1)
        blocks.append(((x - 0.4, x + 0.4), (y - 0.35, y + 0.35), (z0, z0 + 1.1)))
    merged = bmesh.new()
    for idx, b in enumerate((bw, bi, bc)):
        me = bpy.data.meshes.new("_tmp")
        bmesh.ops.recalc_face_normals(b, faces=b.faces)
        b.to_mesh(me)
        b.free()
        me.polygons.foreach_set("material_index", [idx] * len(me.polygons))
        merged.from_mesh(me)
        bpy.data.meshes.remove(me)
    ob = P5.finish("MOD_HOLD_CARGO_A", merged, dec, [M["timber"], M["iron"], M["rope"]])
    ob["module_family"] = "InteriorSet"
    ob["room"] = "hold"
    return ob, blocks


def hold_half(x, z):
    zd = (z - DWL) / K
    s = P13.s_of_x(x / K, lambda s_: zd)
    return (H.hull_point(s, zd)[1] - 0.24) * K


def P14_floor(sc, dg, x, y):
    s = P13.s_of_x(x / K, zh)
    zt = zh(s) * K + DWL + 0.6
    ok, loc, _, _, ob, _ = sc.ray_cast(dg, V((x, y, zt)), V((0, 0, -1)), distance=1.5)
    if ok and ob.name == "CORE_HOLD_FLOOR":
        return loc.z
    return None


def rebuild_collision(col, ladder):
    removed = []
    for o in list(col.objects):
        if o.get("ucx_purpose") in ("hull", "deck_lower"):
            removed.append(o.get("ucx_purpose"))
            me = o.data
            bpy.data.objects.remove(o, do_unlink=True)
            bpy.data.meshes.remove(me)
    parts = []
    # ambar tabanı altı dolu (uçlarda alt güverteye kadar)
    for a, b in zip(np.linspace(0.0, 1.0, 9)[:-1], np.linspace(0.0, 1.0, 9)[1:]):
        pts = []
        for s in (a, b):
            inside = S_HOLD[0] <= s <= S_HOLD[1]
            top = (zh(s) if inside else P13.zl(s)) - 0.25
            for z in np.linspace(H.ZK, top, 9):
                x, y = H.hull_point(s, z)
                pts += [V((x, max(y, 0.15), z)), V((x, -max(y, 0.15), z))]
            pts.append(V((H.hull_point(s, H.ZK)[0], 0.0, -H.T)))
        parts.append((pts, "hull"))
    # ambar borda duvarları
    edges = np.linspace(S_HOLD[0], S_HOLD[1], 11)
    for side in (1, -1):
        for a, b in zip(edges[:-1], edges[1:]):
            pts = []
            for s in (a, b):
                for z in np.linspace(zh(s) - 0.3, P13.zl(s) - 0.2, 4):
                    x, y = H.hull_point(s, z)
                    pts += [V((x, side * y, z)), V((x, side * max(y - 0.26, 0.0), z))]
            parts.append((pts, "hull_side_starboard" if side > 0 else "hull_side_port"))
    parts += P13.deck_pieces(zh, S_HOLD[0], S_HOLD[1], 10, "hold_floor")
    parts += P13.deck_pieces(P13.zl, 0.006, 0.972, 12, "deck_lower", holes=[HATCH])
    x0, x1, hy = HATCH
    c = P13.COAM_W
    for bx in ((x0 - c, x1 + c, hy, hy + c), (x0 - c, x1 + c, -hy - c, -hy), (x0 - c, x0, -hy, hy), (x1, x1 + c, -hy, hy)):
        parts.append(([V((x, y, z)) for x in bx[:2] for y in bx[2:] for z in (ladder["zd"] - 0.05, ladder["zt"])], "hatch_coaming"))
    ya, yb = -P13.LADDER_W / 2, P13.LADDER_W / 2
    parts.append(([V((x, y, z)) for y in (ya, yb) for (x, z) in ((ladder["x_bottom"], ladder["z_bottom"]), (ladder["x_top"], ladder["z_top"]),
                                                                 (ladder["x_top"], ladder["z_bottom"]))], "stairs"))
    made = [C3.convex(f"_tmp_h_{k}", [P13.W(p) for p in pts], col, purpose) for k, (pts, purpose) in enumerate(parts)]
    for o in made:
        o["owner_mesh"] = "CORE_HULL_SHELL"
    core_ucx = sorted([o for o in col.objects if o.name.startswith("UCX_CORE_HULL_SHELL_")], key=lambda o: o.name) + made
    for i, o in enumerate(core_ucx):
        o.name = f"_tmp_ucx_{i}"
    for i, o in enumerate(core_ucx):
        o.name = o.data.name = f"UCX_CORE_HULL_SHELL_{i:02d}"
    return len(made), removed


def render(sc):
    H.setup_render(sc, fast=True)
    out = ROOT / "renders" / VER
    out.mkdir(parents=True, exist_ok=True)
    for o in bpy.data.objects:
        if o.name.startswith(("SOCK_LANTERN_HOLD_", "SOCK_LANTERN_LOWER_")):
            lamp = bpy.data.lights.new(o.name + "_L", "POINT")
            lamp.energy = 700
            lamp.color = (1.0, 0.72, 0.45)
            lo = bpy.data.objects.new("LGT_" + o.name, lamp)
            lo.location = o.location + V((0, 0, -0.3))
            sc.collection.objects.link(lo)
    fill = bpy.data.lights.new("HoldFill", "AREA")
    fill.energy = 700
    fill.size = 12.0
    fo = bpy.data.objects.new("LGT_HoldFill", fill)
    fo.location = V((0.0, 0.0, P13.zl(0.45) * K + DWL - 0.5))
    sc.collection.objects.link(fo)
    zf = zh(0.45) * K + DWL
    views = [
        ("ambar_ileri", V((-7.5, 0.3, zf + 1.6)), V((8.0, -0.3, zf + 0.8)), 18),
        ("ambar_kica", V((6.0, -0.3, zf + 1.6)), V((-10.0, 0.4, zf + 0.7)), 18),
        ("ambar_merdiven", V((1.5, 1.6, zf + 2.0)), V((-1.8, 0.0, zf + 1.2)), 24),
    ]
    for name, loc, tgt, lens in views:
        sc.camera = H.camera(sc, f"CAM25_{name}", loc, tgt, lens=lens)
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
    C = {c.name: c for c in bpy.data.collections}
    core, col_s = C["10_HULL_CORE"], C["30_SOCKETS"]
    floor_obs, beams_x = build_floor_and_beams(core, M)
    hatch_obs, ladder = build_hatch_and_ladder(core, M)
    heels = build_mast_heels(C["20_MODULES_RIG"], M)
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    cargo, blocks = build_cargo(C["24_MODULES_DECOR"], M, sc, dg)
    n_ucx, removed = rebuild_collision(C["40_COLLISION"], ladder)
    col = C["40_COLLISION"]
    for k, ((x0, x1), (y0, y1), (z0, z1)) in enumerate(blocks):
        u = C3.convex(f"UCX_MOD_HOLD_CARGO_A_{k:02d}", [V((x, y, z)) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)], col, "cargo")
        u.name = u.data.name = f"UCX_MOD_HOLD_CARGO_A_{k:02d}"
        u["owner_mesh"] = "MOD_HOLD_CARGO_A"
    # soketler: ambar merdiveni navlink, 4 fener
    pair = "SOCK_NAVLINK_LADDER_HOLD"
    for end, p in (("TOP", (ladder["x_top"] - 0.45, 0.0, ladder["z_top"])), ("BOTTOM", (ladder["x_bottom"] + 0.40, 0.0, ladder["z_bottom"]))):
        P13.set_socket(f"{pair}_{end}", P13.W(p), col_s, shape="SPHERE", size=0.22, link="stairs", pair=pair,
                       decks=["gun_deck_lower", "hold"])
    for k, x in enumerate((-9.5, -5.2, 3.8, 8.2), 1):
        s = P13.s_of_x(x / K, P13.zl)
        z = (P13.zl(s) - P13.DECK_T - P13.BEAM_D) * K + DWL - 0.05
        P13.set_socket(f"SOCK_LANTERN_HOLD_{k:02d}", V((x, 0.0, z)), col_s, shape="SPHERE", size=0.12, module_family="LanternFlagSet",
                       room="hold", light="point (UE), değer oyun ayarı", mount="kirişe asma")
    # denetim
    zf = zh(0.45) * K + DWL
    zc = (P13.zl(0.45) - P13.DECK_T - P13.BEAM_D) * K + DWL
    bpy.ops.wm.save_as_mainfile(filepath=str(out), compress=True)
    H.VERSION = VER
    ap = ROOT / "reports" / f"scene_audit_{VER}.json"
    rep = H.audit(sc, ap)
    rep["hold_v025"] = {"floor_above_wl_mid_m": round(zf, 3), "clear_under_lower_beams_m": round(zc - zf, 3),
                        "hold_span_s": S_HOLD, "hatch_world": [round(v * K, 2) for v in HATCH],
                        "ladder": {"angle_deg": ladder["angle_deg"], "riser_m": round(ladder["riser_m"] * K, 3)},
                        "beams": len(beams_x), "cargo_blocks": len(blocks), "ucx_added": n_ucx + len(blocks),
                        "ucx_removed_purposes": sorted(set(removed)), "sources": "ölçüler TAHMİN"}
    rep["pass"] = {"name": "pass_v025_hold", "source": f"Blender/versions/{SHIP}_{SRC_VER}.blend",
                   "manifest_version": MANIFEST_VERSION, "geometry_changed": "ambar tabanı, kirişler, ambar ağzı, merdiven, yük, direk topukları"}
    ap.write_text(json.dumps(rep, indent=2, ensure_ascii=False), encoding="utf-8")
    print("V025", json.dumps(rep["hold_v025"], ensure_ascii=False))
    if "--no-render" not in sys.argv:
        render(sc)


if __name__ == "__main__":
    main()
