"""Pass v023 — Hareketli arma ve makaralar (RigSet parçası), v022 üzerine.

Çalıştırma (depo kökünden):
    python3 OTTOMAN_FRIGATE_1780_ISTANBUL/scripts/pass_v023_running_rigging.py [--no-render | --render-only]

Kullanıcı sırası (2026-09-26): yelkenler → "halat ve makaralar" → bayrak → ambar içi → LOD/bake.
Kapsam (sarılı yelken durumuna göre):
  - Her serende iki kaldırıcı (lift): seren ucundan direk başındaki makaraya, oradan direk boyunca güverteye.
  - Gabya ve babafingo mandarları (halyard): seren ortasından çanaklık/kıstak makarasına, oradan güverteye.
  - Brasyalar (braces): seren uçlarından öndeki/arkadaki direğe ya da kıç omuzluğa makarayla, oradan güverteye.
  - Randa: pik ve boğaz mandarı, bumba iskotası (kıç küpeşteye). Flok mandarı.
  - Güverte: pruva, ana ve mizana direklerinin önünde palanga parmaklıkları (fife rail, armadora pinleriyle);
    brasyalar için küpeşte üstü koçboynuzları (kevel/cleat).
Güverte ucu noktaları mürettebat, tulumba ve ambar ağızlarından uzak seçildi; denetim raporda.
Halatlar ince boru mesh (UE'de kablo/spline ile değiştirilebilir). Ölçüler TAHMİN.
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
P13, P5, H, C3 = P15.P13, P15.P5, P15.H, P15.C3
SRC_VER, VER = "v022", "v023"
ROOT, SHIP = H.ROOT, H.SHIP_ID
MANIFEST_VERSION = 20
P5.MANIFEST_VERSION = MANIFEST_VERSION
V = Vector
W = P15.W
KEYS = ("COURSE", "TOPSAIL", "TOPGALLANT")
R_RUN = 0.016                     # hareketli halat yarıçapı (dünya) — TAHMİN
RAIL_X = {"FORE": 0.70, "MAIN": 0.65, "MIZZEN": 0.62}     # fife rail, direğin önünde (dünya, +x)


def deck_z(sc, dg, x, y):
    for z0 in (9.0, 7.0, 5.5):
        ok, loc, nrm, idx, ob, _ = sc.ray_cast(dg, V((x, y, z0)), V((0, 0, -1)), distance=8.0)
        if ok and ob.name.startswith("CORE_DECK_"):
            return loc.z
        if ok:
            o = loc - V((0, 0, 0.01))
            ok2, loc2, _, _, ob2, _ = sc.ray_cast(dg, o, V((0, 0, -1)), distance=6.0)
            if ok2 and ob2.name.startswith("CORE_DECK_"):
                return loc2.z
    return None


def block(bm_w, bm_i, c, axis, size=0.22):
    """Makara: elipsoit gövde + iki yanda yiv, demir kanca halkası (rope yönü `axis`)."""
    axis = axis.normalized()
    q = V((0, 0, 1)).rotation_difference(axis).to_matrix().to_4x4()
    T = Matrix.Translation(c) @ q
    r = bmesh.ops.create_uvsphere(bm_w, u_segments=12, v_segments=8, radius=1.0)
    bmesh.ops.scale(bm_w, vec=(size * 0.36, size * 0.26, size * 0.5), verts=r["verts"])
    bmesh.ops.transform(bm_w, matrix=T, verts=r["verts"])
    ring = [T @ V((0.035 * math.cos(2 * math.pi * k / 10), 0.0, size * 0.5 + 0.045 + 0.035 * math.sin(2 * math.pi * k / 10)))
            for k in range(10)]
    P15.tube(bm_i, ring + [ring[0]], 0.009, seg=4)


def rope(bm, pts, sag=0.0, r=R_RUN):
    out = []
    for a, b in zip(pts[:-1], pts[1:]):
        n = max(int((b - a).length / 1.5), 1)
        for k in range(n):
            t = k / n
            out.append(a.lerp(b, t) - V((0, 0, sag * math.sin(math.pi * t) * (b - a).length / 10)))
    out.append(pts[-1])
    P15.tube(bm, out, r, seg=5)


def build_fife_rails(sc, dg, core, M, masts):
    bw, bi = bmesh.new(), bmesh.new()
    pins = {}
    for name, m in masts.items():
        base = W(m.P(0.0))
        x = base.x + RAIL_X[name] + m.D * 1.1 / 2
        z = deck_z(sc, dg, x, 0.0)
        half = 1.0
        for y in (-half, half):                                  # dikmeler
            P5.lathe(bw, [(0.0, 0.0), (0.085, 0.0), (0.075, 0.1), (0.07, 0.95), (0.085, 1.0), (0.0, 1.02)], 12,
                     Matrix.Translation((x, y, z)))
        P5.aabox(bw, x - 0.08, x + 0.08, -half - 0.1, half + 0.1, z + 0.80, z + 0.90)          # parmaklık
        pl = []
        for k in range(9):                                       # armadora pinleri (koyun)
            y = -0.8 + 1.6 * k / 8
            P5.lathe(bw, [(0.0, -0.20), (0.016, -0.20), (0.018, 0.0), (0.028, 0.02), (0.022, 0.10), (0.0, 0.12)], 8,
                     Matrix.Translation((x, y, z + 0.90)))
            pl.append(V((x, y, z + 0.87)))
        pins[name] = pl
    ob = P5.finish("CORE_FIFE_RAILS", bw, core, [M["timber"]], bevel=0.008)
    return ob, pins


def kevels(sc, dg, core, M, points):
    """Küpeşte üstü koçboynuzları (brasya bağları)."""
    bw = bmesh.new()
    for p in points:
        P5.aabox(bw, p.x - 0.22, p.x + 0.22, p.y - 0.05, p.y + 0.05, p.z, p.z + 0.06)
        for dx in (-0.16, 0.16):
            P5.aabox(bw, p.x + dx - 0.03, p.x + dx + 0.03, p.y - 0.05, p.y + 0.05, p.z - 0.10, p.z)
    return P5.finish("CORE_KEVELS", bw, core, [M["timber"]], bevel=0.006)


def bulwark_point(x, sgn, dz=0.0):
    """Bel küpeştesinin iç kenarında bir nokta (dünya)."""
    zd = None
    s = P13.s_of_x(x / 1.1, P13.zu)
    zt = H.top_z(s)
    y = (H.hull_point(s, zt - 0.05)[1] - 0.20) * 1.1
    return V((x, sgn * y, zt * 1.1 + P13.DWL + dz))


def main_build(sc):
    M = P15.materials()
    C = {c.name: c for c in bpy.data.collections}
    rig, core = C["20_MODULES_RIG"], C["10_HULL_CORE"]
    dg = bpy.context.evaluated_depsgraph_get()
    masts = {n: P15.Mast(n) for n in ("FORE", "MAIN", "MIZZEN")}
    rail_ob, pins = build_fife_rails(sc, dg, core, M, masts)
    pin_i = {n: 0 for n in pins}

    def pin(name):
        p = pins[name][pin_i[name] % len(pins[name])]
        pin_i[name] += 1
        return p

    br, bw, bi = {n: bmesh.new() for n in masts}, {n: bmesh.new() for n in masts}, {n: bmesh.new() for n in masts}
    n_blocks, n_lines = 0, 0
    kevel_pts = []
    heads = {"COURSE": lambda m, s: m.P(m.t_cap - 0.25, 0.10, s * 0.38),
             "TOPSAIL": lambda m, s: m.P(m.t_th + 0.12, m.ft + 0.05, s * 0.30),
             "TOPGALLANT": lambda m, s: m.P(m.t_g1 - 0.30, m.fg, s * 0.12)}
    down = lambda m, s: m.P(1.6, m.D / 2 + 0.1, s * (m.D / 2 + 0.06))   # noqa: E731  direk boyunca iniş noktası
    brace_to = {  # (direk, anahtar) → işaret: yönlendirme makarasının konumu (tasarım uzayı fonksiyonu)
        "FORE": lambda k, s: masts["MAIN"].P({"COURSE": 4.0, "TOPSAIL": masts["MAIN"].t_h - 0.8,
                                              "TOPGALLANT": masts["MAIN"].t_th - 0.6}[k], 0.3, s * 0.6),
        "MAIN": lambda k, s: (None if k == "COURSE" else masts["MIZZEN"].P({"TOPSAIL": masts["MIZZEN"].t_h - 0.8,
                                                                            "TOPGALLANT": masts["MIZZEN"].t_th - 0.6}[k], 0.3, s * 0.5)),
        "MIZZEN": lambda k, s: masts["MAIN"].P({"COURSE": 3.2, "TOPSAIL": 5.0, "TOPGALLANT": masts["MAIN"].t_h - 2.5}[k],
                                               -m_rad("MAIN") - 0.1, s * 0.6),
    }

    for name, m in masts.items():
        for key in KEYS:
            yob = bpy.data.objects[f"MOD_RIG_YARD_{name}_{key}_A"]
            half = max(abs(v.co.y) for v in yob.data.vertices)
            mw = yob.matrix_world
            for s in (1, -1):
                arm = mw @ V((0.0, s * half * 0.93, 0.05))
                # kaldırıcı
                hb = W(heads[key](m, s))
                block(bw[name], bi[name], hb, arm - hb, 0.20)
                rope(br[name], [arm, hb])
                rope(br[name], [hb, W(down(m, s)), pin(name)])
                n_blocks += 1
                n_lines += 1
                # brasya
                lead = brace_to[name](key, s)
                if lead is not None:
                    lw = W(lead)
                    block(bw[name], bi[name], lw, arm - lw, 0.18)
                    other = "MAIN" if name in ("FORE", "MIZZEN") else "MIZZEN"
                    rope(br[name], [arm, lw], sag=0.15)
                    rope(br[name], [lw, W(masts[other].P(1.6, 0.3, s * 0.5)), pin(other)])
                    n_blocks += 1
                else:                                        # ana alt seren brasyası: kıç omuzluğa, küpeşte koçboynuzuna
                    kx = W(masts["MIZZEN"].P(0.0)).x - 3.2
                    kp = bulwark_point(kx, s, 0.06)
                    lw = kp + V((0.0, 0.0, 1.2))
                    block(bw[name], bi[name], lw, arm - lw, 0.18)
                    rope(br[name], [arm, lw], sag=0.15)
                    rope(br[name], [lw, kp + V((0, 0, 0.1))])
                    kevel_pts.append(kp)
                    n_blocks += 1
                n_lines += 1
            if key != "COURSE":                               # mandar
                c = mw @ V((0.0, 0.0, 0.12))
                top = W(m.P(m.t_th + 0.30, m.ft, 0.0) if key == "TOPSAIL" else m.P(m.t_g1 - 0.15, m.fg, 0.0))
                block(bw[name], bi[name], top, c - top, 0.24)
                rope(br[name], [c, top])
                rope(br[name], [top, W(m.P(2.0, -m.D / 2 - 0.1, 0.0)), pin(name)])
                n_blocks += 1
                n_lines += 1
    # randa ve flok
    mz = masts["MIZZEN"]
    gaff, boom = bpy.data.objects["MOD_RIG_GAFF_MIZZEN_A"], bpy.data.objects["MOD_RIG_BOOM_MIZZEN_A"]

    def ends(o):
        pts = [o.matrix_world @ v.co for v in o.data.vertices]
        p0 = o.matrix_world.translation
        return p0, max(pts, key=lambda p: (p - p0).length)
    g0, g1 = ends(gaff)
    b0, b1 = ends(boom)
    hb = W(mz.P(mz.t_h - 0.35, -mz.D / 2 - 0.1, 0.0))
    block(bw["MIZZEN"], bi["MIZZEN"], hb, g1 - hb, 0.22)
    rope(br["MIZZEN"], [g1, hb], sag=0.3)
    rope(br["MIZZEN"], [g0 + V((0, 0, 0.15)), hb])
    rope(br["MIZZEN"], [hb, W(mz.P(1.6, -mz.D / 2 - 0.1, 0.2)), pin("MIZZEN")])
    tr = bulwark_point(b1.x + 0.8, 1, 0.1)
    taff = V((b1.x + 0.6, 0.0, max(tr.z, b1.z - 1.3)))
    block(bw["MIZZEN"], bi["MIZZEN"], b1 + V((0, 0, -0.25)), taff - b1, 0.2)
    rope(br["MIZZEN"], [b1 + V((0, 0, -0.35)), taff])
    fr = masts["FORE"]
    jh = W(fr.P(fr.t_th - 0.2, fr.ft + fr.Dt / 2 + 0.1, 0.0))
    block(bw["FORE"], bi["FORE"], jh, V((1, 0, -1)), 0.22)
    rope(br["FORE"], [jh, W(fr.P(2.2, fr.D / 2 + 0.1, 0.25)), pin("FORE")])
    n_blocks += 3
    n_lines += 5
    kev = kevels(sc, dg, core, M, kevel_pts)
    obs = []
    for name in masts:
        merged = bmesh.new()
        for idx, b in enumerate((br[name], bw[name], bi[name])):
            me = bpy.data.meshes.new("_tmp")
            bmesh.ops.recalc_face_normals(b, faces=b.faces)
            b.to_mesh(me)
            b.free()
            me.polygons.foreach_set("material_index", [idx] * len(me.polygons))
            merged.from_mesh(me)
            bpy.data.meshes.remove(me)
        ob = P5.finish(f"MOD_RIG_RUNNING_{name}_A", merged, rig, [M["rope"], M["timber"], M["iron"]])
        ob["module_family"] = "RigSet"
        ob["note"] = "hareketli arma (sarılı yelken durumu); UE'de kablo/spline ile değiştirilebilir"
        obs.append(ob)
    # denetim: fife rail ve koçboynuzu çevresinde mürettebat/tulumba/merdiven
    conflicts = []
    rails = [V((p[0].x, 0.0)) for p in pins.values()]
    for o in bpy.data.objects:
        if o.type == "EMPTY" and o.name.startswith(("SOCK_CREW_", "SOCK_NAVLINK_", "SOCK_STATION_", "SOCKET_PUMP")):
            for r in rails:
                if abs(o.location.x - r.x) < 0.35 and abs(o.location.y) < 1.2 and o.location.z > 2.5:
                    conflicts.append({"socket": o.name, "rail_x": round(r.x, 2)})
    return obs + [rail_ob, kev], n_blocks, n_lines, conflicts, {k: round(v[0].x, 2) for k, v in pins.items()}


def m_rad(name):
    return P15.Mast(name).D / 2


def render(sc):
    H.setup_render(sc, fast=True)
    out = ROOT / "renders" / VER
    out.mkdir(parents=True, exist_ok=True)
    views = [
        ("bas_omzu", V((53, 42, 25)), V((0, 0, 14.2)), 32),
        ("ana_direk_dibi", V((6.5, 4.2, 5.4)), V((2.2, 0.0, 4.0)), 28),
        ("gabya_makaralar", V((9.0, 8.0, 27.0)), V((2.4, 0.0, 26.0)), 30),
        ("kic_omzu", V((-50, -37, 21)), V((0, 0, 14.2)), 32),
    ]
    for name, loc, tgt, lens in views:
        sc.camera = H.camera(sc, f"CAM23_{name}", loc, tgt, lens=lens)
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
    obs, nb, nl, conflicts, rails = main_build(sc)
    bpy.context.view_layer.update()
    col = bpy.data.collections["40_COLLISION"]
    fr = bpy.data.objects["CORE_FIFE_RAILS"]
    pts = [fr.matrix_world @ v.co for v in fr.data.vertices]
    for name, x in rails.items():
        sel = [p for p in pts if abs(p.x - x) < 0.3]
        u = C3.convex(f"UCX_CORE_FIFE_RAILS_{len([o for o in col.objects if o.name.startswith('UCX_CORE_FIFE_RAILS_')]):02d}",
                      [V((a, b, c)) for a in (min(p.x for p in sel), max(p.x for p in sel)) for b in (min(p.y for p in sel), max(p.y for p in sel))
                       for c in (min(p.z for p in sel), max(p.z for p in sel))], col, "fife_rail")
        u["owner_mesh"] = "CORE_FIFE_RAILS"
    bpy.ops.wm.save_as_mainfile(filepath=str(out), compress=True)
    H.VERSION = VER
    ap = ROOT / "reports" / f"scene_audit_{VER}.json"
    rep = H.audit(sc, ap)

    def tri(o):
        o.data.calc_loop_triangles()
        return len(o.data.loop_triangles)

    rep["running_v023"] = {"objects": [o.name for o in obs], "blocks": nb, "lines": nl, "fife_rail_x_world": rails,
                           "rail_conflicts": conflicts, "tris": {o.name: tri(o) for o in obs}, "sources": "düzen TAHMİN"}
    rep["pass"] = {"name": "pass_v023_running_rigging", "source": f"Blender/versions/{SHIP}_{SRC_VER}.blend",
                   "manifest_version": MANIFEST_VERSION, "geometry_changed": "hareketli arma, makaralar, palanga parmaklıkları"}
    ap.write_text(json.dumps(rep, indent=2, ensure_ascii=False), encoding="utf-8")
    print("V023", json.dumps({k: rep["running_v023"][k] for k in ("blocks", "lines", "fife_rail_x_world", "rail_conflicts", "tris")}, ensure_ascii=False))
    if "--no-render" not in sys.argv:
        render(sc)


if __name__ == "__main__":
    main()
