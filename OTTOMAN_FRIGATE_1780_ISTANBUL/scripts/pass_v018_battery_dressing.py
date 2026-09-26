"""Pass v018 — Batarya ve güverte ayrıntıları, v017 üzerine.

Çalıştırma (depo kökünden):
    python3 OTTOMAN_FRIGATE_1780_ISTANBUL/scripts/pass_v018_battery_dressing.py [--no-render | --render-only]

Plan: MODELLEME_PLANI §6 madde 2 (iç postalar/dirsekler, güverte donanımı). Eklenenler:
  - Alt güverte: kiriş uçlarında asma dirsekler (hanging knees), lumbar ve fenerlerle çakışanlar atlanır.
  - Top başına iki halka cıvatası (iç borda, lumbarın iki yanı) — üst ve alt güverte.
  - Üst güvertedeki 20 borda topuna brok halatı (breeching) — kaskabelden iki halka cıvatasına.
  - Üst güvertede toplar arasında gülle rafları (her rafta 10 gülle, çap 0,10 m ≈ namlu çapı).
  - Ana direğin kıçında iki sintine tulumbası (DeckUtility) + kullanıcı soketleri.
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


P17 = _load("pass_v017", "pass_v017_boat_anchor_capstan.py")
P16, P15, P14, P13 = P17.P16, P17.P15, P17.P14, P17.P13
P5, H, K, C3 = P13.P5, P13.H, P13.K, P15.C3
SRC_VER, VER = "v017", "v018"
ROOT, SHIP = H.ROOT, H.SHIP_ID
MANIFEST_VERSION = 16
P5.MANIFEST_VERSION = MANIFEST_VERSION
DWL = P13.DWL
V = Vector
SHOT_R = 0.05
PUMP_X, PUMP_Y = 0.55, 0.85       # dünya; ana direk (x = 1,92) kıçında


def inner_y_world(x, z):
    zd = (z - DWL) / K
    s = P13.s_of_x(x / K, lambda s_: zd)
    return (H.hull_point(s, zd)[1] - 0.24) * K


def gun_sockets(lower):
    out = []
    for o in bpy.data.objects:
        if o.type != "EMPTY" or not o.name.startswith("SOCKET_CANNON_") or "CHASE" in o.name:
            continue
        if ("LOWER" in o.name) == lower:
            out.append(o)
    return sorted(out, key=lambda o: o.name)


# --- Asma dirsekler ------------------------------------------------------------------------
def build_knees(core, M):
    beams = bpy.data.objects["CORE_DECK_BEAMS_UPPER"]
    xs = sorted({round((beams.matrix_world @ v.co).x, 2) for v in beams.data.vertices})
    centers = []
    for a in xs:
        if not centers or a - centers[-1][-1] > 0.3:
            centers.append([a])
        else:
            centers[-1].append(a)
    cx = [sum(c) / len(c) for c in centers]
    ports = [o.location.x for o in gun_sockets(True) if o.location.y > 0]
    lanterns = [o.location.x for o in bpy.data.objects if o.name.startswith("SOCK_LANTERN_LOWER_")]
    xg = P13.XG * K
    bm = bmesh.new()
    placed, skipped = [], []
    sc, dg = bpy.context.scene, bpy.context.evaluated_depsgraph_get()
    for x in cx:
        if abs(x - xg) < 0.3 or any(abs(x - p) < 0.52 for p in ports) or any(abs(x - l) < 0.4 for l in lanterns):
            skipped.append(round(x, 2))
            continue
        zl = P14.deck_hit(sc, dg, V((x, 0.0, P13.zl(P13.s_of_x(x / K, P13.zl)) * K + DWL - 0.3)))
        if zl is None:
            skipped.append(round(x, 2))
            continue
        zb = zl + P13.DL * K - (P13.DECK_T + P13.BEAM_D) * K       # kiriş altı (orta hat yaklaşık)
        if inner_y_world(x, zb - 0.45) < 1.4:                      # pruva/kıç darlığı: iki dirsek üst üste biner
            skipped.append(round(x, 2))
            continue
        for sgn in (1, -1):
            yi = inner_y_world(x, zb - 0.45)
            zb_side = zb - 0.12                                   # kamburluk: kenarda kiriş altı daha alçak
            prof = [(0.0, 0.0), (-0.85, 0.0), (-0.85, -0.12), (-0.35, -0.20), (-0.16, -0.40), (-0.12, -0.85), (0.0, -0.85)]
            ring0 = [bm.verts.new((x - 0.08, sgn * (yi + dy), zb_side + dz)) for dy, dz in prof]
            ring1 = [bm.verts.new((x + 0.08, sgn * (yi + dy), zb_side + dz)) for dy, dz in prof]
            n = len(prof)
            f0 = bm.faces.new(ring0)
            f1 = bm.faces.new(list(reversed(ring1)))
            for k in range(n):
                bm.faces.new([ring0[k], ring1[k], ring1[(k + 1) % n], ring0[(k + 1) % n]])
            placed.append(round(x, 2))
    ob = P5.finish("CORE_KNEES_LOWER_DECK", bm, core, [M["timber"]], bevel=0.01)
    return ob, sorted(set(placed)), skipped


# --- Halka cıvataları, brok halatları ----------------------------------------------------------
def ring_bolt(bm, c, n):
    """c: gövde iç yüzeyinde; n: içeri normal. Küçük halka + taban pulu."""
    ring = []
    r = 0.07
    u = V((1, 0, 0))
    for k in range(10):
        a = 2 * math.pi * k / 10
        ring.append(c + n * (0.05 + r + r * math.cos(a)) + V((0, 0, -r * 0.2)) + u * (r * math.sin(a)))
    P15.tube(bm, ring + [ring[0]], 0.014, seg=5)
    P5.lathe(bm, [(0.0, 0.0), (0.05, 0.0), (0.05, 0.02), (0.0, 0.03)], 8, P5.axis_matrix(c, n))


def build_bolts_and_breeching(core, cannons, M):
    bi, br = {"S": bmesh.new(), "P": bmesh.new()}, {"S": bmesh.new(), "P": bmesh.new()}
    bolts = bmesh.new()
    n_b, n_r = 0, 0
    tr_x = P14.TRUN_X
    casc = -P14.TRUN_FROM_BREECH - 0.21
    for lower in (False, True):
        for g in gun_sockets(lower):
            side = "S" if g.location.y > 0 else "P"
            sgn = 1 if side == "S" else -1
            mw = g.matrix_world
            zb = g.location.z + 0.52
            pts = []
            for dx in (-0.62, 0.62):
                x = g.location.x + dx
                yi = inner_y_world(x, zb)
                c = V((x, sgn * (yi - 0.01), zb))
                ring_bolt(bolts, c, V((0, -sgn, 0)))
                pts.append(c + V((0, -sgn * 0.12, 0)))
                n_b += 1
            if lower:
                continue
            tag = g.name[len('SOCKET_CANNON_'):]
            car = bpy.data.objects.get(f"MOD_CANNON_9PDR_A_{tag}") or bpy.data.objects.get(f"MOD_CANNON_9PDR_B_{tag}")
            if car is None:
                continue
            cp = mw @ V((tr_x + casc, 0.0, P14.TRUN_Z - 0.02))
            a, b = pts
            seq = []
            for t in np.linspace(0, 1, 7):                      # halka → kaskabel (sarkık)
                p = a.lerp(cp, t) + V((0, 0, -0.18 * math.sin(math.pi * t)))
                seq.append(p)
            for t in np.linspace(0, 1, 7)[1:]:
                p = cp.lerp(b, t) + V((0, 0, -0.18 * math.sin(math.pi * t)))
                seq.append(p)
            P15.tube(br[side], seq, 0.028, seg=6)
            n_r += 1
    obs = [P5.finish("CORE_RING_BOLTS", bolts, core, [M["iron"]])]
    mods = bpy.data.collections["22_MODULES_CANNONS"]
    for side in ("S", "P"):
        ob = P5.finish(f"MOD_CANNON_BREECHING_{side}_A", br[side], mods, [M["rope"]])
        ob["module_family"] = "CannonBattery"
        ob["note"] = "brok halatları (toplar içerideyken); UE'de kablo/spline ile değiştirilebilir"
        obs.append(ob)
    for b in bi.values():
        b.free()
    return obs, n_b, n_r


# --- Gülle rafları --------------------------------------------------------------------------
def build_shot_racks(core, M):
    bw, bs = bmesh.new(), bmesh.new()
    n = 0
    for side, sgn in (("S", 1), ("P", -1)):
        guns = sorted([g for g in gun_sockets(False) if (g.location.y > 0) == (sgn > 0)], key=lambda g: g.location.x)
        for a, b in zip(guns[:-1], guns[1:]):
            x = (a.location.x + b.location.x) / 2
            z = (a.location.z + b.location.z) / 2
            yi = inner_y_world(x, z + 0.3) - 0.02
            y0, y1 = sorted((sgn * (yi - 0.20), sgn * yi))
            L = 1.15
            P5.aabox(bw, x - L / 2, x + L / 2, y0, y1, z + 0.02, z + 0.10)
            for k in range(2):
                P5.aabox(bw, x - L / 2 + 0.02 + k * (L - 0.08), x - L / 2 + 0.06 + k * (L - 0.08), y0, y1, z, z + 0.14)
            for k in range(10):
                xx = x - L / 2 + 0.08 + k * (L - 0.16) / 9
                yy = sgn * (yi - 0.10)
                r = bmesh.ops.create_uvsphere(bs, u_segments=10, v_segments=6, radius=SHOT_R)
                bmesh.ops.translate(bs, vec=(xx, yy, z + 0.10 + SHOT_R * 0.55), verts=r["verts"])
            n += 1
    ob = P16.make_mesh("CORE_SHOT_RACKS", [(bw, M["timber"]), (bs, M["iron"])])
    o = bpy.data.objects.new("CORE_SHOT_RACKS", ob)
    core.objects.link(o)
    return o, n


# --- Tulumbalar ---------------------------------------------------------------------------------
def pump_mesh(M):
    bw, bi = bmesh.new(), bmesh.new()
    P5.lathe(bw, [(0.0, 0.0), (0.20, 0.0), (0.20, 0.06), (0.16, 0.08), (0.16, 0.95), (0.19, 0.98), (0.19, 1.05), (0.0, 1.05)], 16, Matrix())
    for z in (0.25, 0.60, 0.90):
        P5.lathe(bi, [(0.165, z), (0.175, z), (0.175, z + 0.04), (0.165, z + 0.04)], 16, Matrix())
    P5.aabox(bw, 0.14, 0.42, -0.05, 0.05, 0.78, 0.86)                              # oluk (spout)
    P5.aabox(bw, -0.30, -0.22, -0.05, 0.05, 1.05, 1.45)                            # çatal dikme
    P15.obox(bw, V((0.10, 0.0, 1.38)), V((0.97, 0.0, -0.24)).normalized(), V((0, 1, 0)),
             V((0.24, 0.0, 0.97)).normalized(), 0.95, 0.03, 0.03)                  # kol (brake)
    P15.tube(bi, [V((0.0, 0.0, 1.30)), V((0.0, 0.0, 1.05))], 0.018, seg=6)         # piston kolu
    return P16.make_mesh("MOD_PUMP_ELM_A", [(bw, M["timber"]), (bi, M["iron"])])


def build_pumps(C, M):
    me = pump_mesh(M)
    sc, dg = bpy.context.scene, bpy.context.evaluated_depsgraph_get()
    obs, socks = [], []
    for tag, sgn in (("S", 1), ("P", -1)):
        x, y = PUMP_X, sgn * PUMP_Y
        z = P14.deck_hit(sc, dg, V((x, y, 3.4)))
        ob = bpy.data.objects.new(f"MOD_PUMP_ELM_A_{tag}", me)
        C["23_MODULES_DECK"].objects.link(ob)
        ob.location = V((x, y, z))
        ob.rotation_euler = (0, 0, math.pi if sgn < 0 else 0.0)
        ob["module_family"] = "DeckUtility"
        ob["socket"] = f"SOCKET_PUMP_{tag}"
        obs.append(ob)
        P13.set_socket(f"SOCKET_PUMP_{tag}", ob.location, C["30_SOCKETS"], shape="ARROWS", size=0.3, module_family="DeckUtility")
        p = ob.location + V((1.05 if sgn > 0 else -1.05, 0.0, 0.0))
        P13.set_socket(f"SOCK_CREW_PUMP_{tag}", p, C["30_SOCKETS"], shape="SINGLE_ARROW", size=0.35,
                       rot=(0, 0, math.pi if sgn > 0 else 0.0), crew_role="pump", station=f"SOCKET_PUMP_{tag}")
        socks += [f"SOCKET_PUMP_{tag}", f"SOCK_CREW_PUMP_{tag}"]
    return obs, socks


def checks(pumps):
    res = {"pump_to_battery_crew_min_m": None}
    d = 1e9
    for o in bpy.data.objects:
        if o.type == "EMPTY" and o.name.startswith("SOCK_CREW_") and not o.name.startswith(("SOCK_CREW_PUMP", "SOCK_CREW_LOWER", "SOCK_CREW_CAPSTAN")):
            for p in pumps:
                d = min(d, (V((o.location.x, o.location.y)) - V((p.location.x, p.location.y))).length)
    res["pump_to_battery_crew_min_m"] = round(d, 3)
    main = bpy.data.objects["SOCKET_MAST_MAIN"].location
    res["pump_to_mainmast_m"] = round(min((V((p.location.x, p.location.y)) - V((main.x, main.y))).length for p in pumps), 3)
    return res


def render(sc):
    H.setup_render(sc, fast=True)
    out = ROOT / "renders" / VER
    out.mkdir(parents=True, exist_ok=True)
    for o in bpy.data.objects:
        if o.name.startswith("SOCK_LANTERN_LOWER_"):
            lamp = bpy.data.lights.new(o.name + "_L", "POINT")
            lamp.energy = 700
            lamp.color = (1.0, 0.72, 0.45)
            lo = bpy.data.objects.new("LGT_" + o.name, lamp)
            lo.location = o.matrix_world @ V((0.0, 0.285, -0.13))
            sc.collection.objects.link(lo)
    fill = bpy.data.lights.new("LowerDeckFill", "AREA")
    fill.energy = 900
    fill.size = 14.0
    fo = bpy.data.objects.new("LGT_LowerDeckFill", fill)
    fo.location = V((0.0, 0.0, 2.6))
    sc.collection.objects.link(fo)
    g = bpy.data.objects["SOCKET_CANNON_S_06"].matrix_world
    views = [
        ("brok_halati", g @ V((-2.6, 1.8, 1.7)), g @ V((0.4, -0.2, 0.5)), 28),
        ("gulle_rafi", g @ V((-1.6, -1.9, 1.3)), g @ V((0.9, -1.2, 0.2)), 28),
        ("tulumba", V((-1.6, 2.6, 5.0)), V((0.6, 0.0, 3.7)), 30),
        ("alt_guverte_dirsek", V((-6.0, -1.5, 2.3)), V((1.0, 3.4, 2.2)), 20),
    ]
    for name, loc, tgt, lens in views:
        sc.camera = H.camera(sc, f"CAM18_{name}", loc, tgt, lens=lens)
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
    M = P17.mats()
    C = {c.name: c for c in bpy.data.collections}
    core = C["10_HULL_CORE"]
    knees, placed, skipped = build_knees(core, M)
    bolt_obs, n_b, n_r = build_bolts_and_breeching(core, None, M)
    racks, n_racks = build_shot_racks(core, M)
    pumps, psocks = build_pumps(C, M)
    bpy.context.view_layer.update()
    for p in pumps:
        u = C3.convex(f"UCX_{p.name}_00", [p.matrix_world @ V(c) for c in p.bound_box], C["40_COLLISION"], "pump")
        u.name = u.data.name = f"UCX_{p.name}_00"
        u["owner_mesh"] = p.name
    chk = checks(pumps)
    bpy.ops.wm.save_as_mainfile(filepath=str(out), compress=True)
    H.VERSION = VER
    ap = ROOT / "reports" / f"scene_audit_{VER}.json"
    rep = H.audit(sc, ap)
    rep["v018"] = {"knees": {"beams_with_knees_x": placed, "skipped_x": skipped, "count": 2 * len(placed)},
                   "ring_bolts": n_b, "breeching_ropes": n_r, "shot_racks": n_racks, "shot_per_rack": 10,
                   "pumps": [p.name for p in pumps], "sockets_added": psocks, "checks": chk, "sources": "ölçüler TAHMİN"}
    rep["pass"] = {"name": "pass_v018_battery_dressing", "source": f"Blender/versions/{SHIP}_{SRC_VER}.blend",
                   "pass_changes": {"added": [knees.name, racks.name] + [o.name for o in bolt_obs + pumps]},
                   "manifest_version": MANIFEST_VERSION, "geometry_changed": "ayrıntı parçaları eklendi"}
    ap.write_text(json.dumps(rep, indent=2, ensure_ascii=False), encoding="utf-8")
    print("V018", json.dumps(rep["v018"], ensure_ascii=False))
    if "--no-render" not in sys.argv:
        render(sc)


if __name__ == "__main__":
    main()
