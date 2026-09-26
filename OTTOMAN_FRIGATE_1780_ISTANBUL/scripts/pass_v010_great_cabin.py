"""Pass v010 — kıç kasarası altında büyük kaptan kamarası (v009 üzerine; gövde kabuğu değişmez).

Çalıştırma (depo kökünden):
    python3 OTTOMAN_FRIGATE_1780_ISTANBUL/scripts/pass_v010_great_cabin.py [--no-render | --render-only]

Kullanıcı kararı (2026-09-26): "Kıç kasarası altını kapat" — ortadaki iki merdiven kalkar, kıç kasarasının
altındaki açık alan (ana güverte seviyesi) ön duvarla kapatılıp kaptan kamarası olur; giriş, kıç üstü
bölmesindeki kapı tarzında, belden girilen ön duvardaki kapı. Kıç kasarasına çıkış köşelere taşınır.
Kısıt: ön duvarın önünde 5. top çiftinin mürettebatı var → merdivenler duvar boyunca enlemesine
(kapının yanından köşeye doğru yükselir), koşu 2,1 m (tasarım), eğim ≈ 43,6° (UE sınırı 44,76°).
Kamarada 1-4. top çiftleri kalır (dönemin frigate'lerinde kaptan kamarasında top bulunurdu).
Ana batarya yeniden dizildi: 1-4 → x = -13,4 … -6,9; 5-11 → -3,55 … 9,55 (tasarım); 12 baş kasarası altında.
"""

import importlib.util
import json
import sys
from pathlib import Path

import bpy  # noqa: I001
import bmesh
import numpy as np
from mathutils import Vector

HERE = Path(__file__).resolve().parent
_sp = importlib.util.spec_from_file_location("pass_v009", HERE / "pass_v009_fc_stairs_corners.py")
P9 = importlib.util.module_from_spec(_sp)
_sp.loader.exec_module(P9)
P8, P5, H, C3, K = P9.P8, P9.P5, P9.H, P9.C3, P9.K

SRC_VER, VER = "v009", "v010"
ROOT, SHIP = H.ROOT, H.SHIP_ID
P8.VER = VER
MANIFEST_VERSION = 8
P8.MANIFEST_VERSION = MANIFEST_VERSION
DOOR_W, DOOR_H = 0.90, 1.85   # tasarım (dünyada 0,99 × 2,04)
STAIR_Y0, QD_RUN = 0.62, 2.10  # merdiven alt ucu |y| ve koşu (tasarım)
P9.MANIFEST_VERSION = MANIFEST_VERSION
CABIN_GUNS_X = (-13.40, -6.90)   # 1-4. toplar (kamara içi); 4. topun ön mürettebatı duvarın arkasında kalsın
WAIST_GUNS_X = (-3.55, 9.55)     # 5-11. toplar; 5. topun arka mürettebatı merdiven ayak izinin önünde


def port_positions_v010():
    ports = []
    xs = list(np.linspace(*CABIN_GUNS_X, 4)) + list(np.linspace(*WAIST_GUNS_X, 7)) + [P8.GUN12_X]
    for k, x in enumerate(xs):
        s = (x - H.stern_x(2)) / (H.bow_x(2) - H.stern_x(2))
        ports.append(("MAIN", k + 1, x, s, H.deck_z(s) + H.PORT_SILL + H.PORT_H / 2))
    for kind, idx, x, s, z in P5.port_positions_v005():
        if kind == "QD":
            ports.append((kind, idx, x, s, z))
    return ports


H.port_positions = port_positions_v010


def remove(name):
    ob = bpy.data.objects.get(name)
    if ob is None:
        return False
    me = ob.data
    bpy.data.objects.remove(ob, do_unlink=True)
    if me is not None and me.users == 0:
        bpy.data.meshes.remove(me)
    return True


def build_front_wall(core, M):
    x_e, _ = P8.edges()
    s_g = P8.s_of_x(x_e, lambda s: P8.zlev(s, "gun"))
    zg = P8.zlev(s_g, "gun")
    s_q = P8.s_of_x(x_e, lambda s: P8.zlev(s, "qd"))
    zq = P8.zlev(s_q, "qd")
    half_g = H.hull_point(s_g, zg)[1] - 0.24
    half_q = H.hull_point(s_q, zq)[1] - 0.24
    yw = H.hull_point(s_g, zg + 1.0)[1] - 0.10

    def camb(y, half):
        v = min(abs(y) / half, 1.0)
        return 0.12 * (1 - v * v)

    bot = lambda y: zg + camb(y, half_g) - 0.05  # noqa: E731
    top = lambda y: zq + camb(y, half_q) - 0.09  # noqa: E731
    x0, x1 = x_e - 0.10, x_e
    bm = bmesh.new()

    def strip(ya, yb, zb, zt):
        P5.box8(bm, [Vector((x0, ya, zb(ya))), Vector((x1, ya, zb(ya))), Vector((x1, yb, zb(yb))), Vector((x0, yb, zb(yb))),
                     Vector((x0, ya, zt(ya))), Vector((x1, ya, zt(ya))), Vector((x1, yb, zt(yb))), Vector((x0, yb, zt(yb)))])

    for arr in (np.linspace(-yw, -DOOR_W / 2, 9), np.linspace(DOOR_W / 2, yw, 9)):
        for a, b in zip(arr[:-1], arr[1:]):
            strip(a, b, bot, top)
    door_top = bot(0.0) + DOOR_H
    strip(-DOOR_W / 2, DOOR_W / 2, lambda y: door_top, top)
    bm_t = bmesh.new()
    for sgn in (-1, 1):
        y0, y1 = sorted((sgn * DOOR_W / 2, sgn * (DOOR_W / 2 + 0.12)))
        P5.aabox(bm_t, x_e - 0.02, x_e + 0.06, y0, y1, zg + 0.10, door_top + 0.10)
    P5.aabox(bm_t, x_e - 0.02, x_e + 0.07, -DOOR_W / 2 - 0.16, DOOR_W / 2 + 0.16, door_top, door_top + 0.14)
    ob = P8.merge_finish("CORE_GREAT_CABIN_BULKHEAD", [(bm, M["inner"]), (bm_t, M["yellow"])], core, sharp=30, bevel=None)
    return ob, dict(x_e=x_e, zg=zg, zq=zq, yw=yw, door_top=door_top)


def build_stairs_and_rail(core, M, wall):
    x_e = wall["x_e"]
    xc = x_e + P8.STAIR_W / 2 + 0.02
    infos, objs = {}, []
    for sgn, tag in ((1, "S"), (-1, "P")):
        p0 = Vector((xc, sgn * STAIR_Y0, P8.deck_top(xc, sgn * STAIR_Y0, "gun")))
        y1 = STAIR_Y0 + QD_RUN
        p1 = Vector((xc, sgn * y1, P8.deck_top(x_e - 0.05, sgn * y1, "qd")))
        bms = (bmesh.new(), bmesh.new(), bmesh.new())
        infos[f"QD_{tag}"] = P8.stair(bms, p0, p1)
        infos[f"QD_{tag}"]["y"] = sorted((sgn * STAIR_Y0, sgn * y1))
        objs.append(P8.merge_finish(f"CORE_STAIRS_QD_{tag}", list(zip(bms, (M["deck"], M["timber"], M["yellow"]))), core))
    # kıç kasarası ön korkuluğu: orta parça + köşelerde merdiven başı boşluğu
    xr = x_e - 0.08
    wf = P8.inner_half(xr, "qd") - 0.02
    top_y = STAIR_Y0 + QD_RUN
    segs = [(-(top_y - 0.30), top_y - 0.30), (top_y + 0.12, wf), (-wf, -(top_y + 0.12))]
    segs = [(a, b) for a, b in segs if b - a > 0.30]
    bm_r, bm_p, bm_f = bmesh.new(), bmesh.new(), bmesh.new()
    for y0, y1 in segs:
        za, zb = P8.deck_top(xr, y0, "qd") - 0.03, P8.deck_top(xr, y1, "qd") - 0.03
        P5.box8(bm_p, [Vector((xr - 0.07, y0, za)), Vector((xr + 0.07, y0, za)), Vector((xr + 0.07, y1, zb)), Vector((xr - 0.07, y1, zb)),
                       Vector((xr - 0.07, y0, za + P5.RIM_H)), Vector((xr + 0.07, y0, za + P5.RIM_H)),
                       Vector((xr + 0.07, y1, zb + P5.RIM_H)), Vector((xr - 0.07, y1, zb + P5.RIM_H))])
        n = max(int((y1 - y0) / 0.28), 2)
        ys = [y0 + 0.08 + (y1 - y0 - 0.16) * t / n for t in range(n + 1)]
        P5.rail_run(bm_r, [(xr, yy, za + (zb - za) * (yy - y0) / (y1 - y0) + P5.RIM_H) for yy in ys])
    zb_edge = P8.zlev(H.S_QD, "qd")
    P5.aabox(bm_f, x_e - 0.02, x_e + 0.08, -wf, wf, zb_edge - 0.30, zb_edge - 0.10)
    objs.append(P8.merge_finish("CORE_BREAST_RAIL_QD", [(bm_r, M["yellow"]), (bm_p, M["inner"]), (bm_f, M["yellow"])],
                                core, sharp=50, bevel=None))
    return objs, infos, [dict(key="QD", x=xr, segs=segs, level="qd")]


def update_collision(col, infos, rails, wall):
    removed = []
    for o in list(col.objects):
        if not o.name.startswith("UCX_"):
            continue
        p = o.get("ucx_purpose")
        cx = sum((o.matrix_world @ v.co).x for v in o.data.vertices) / max(len(o.data.vertices), 1)
        if p == "rail_qd" or (p == "stairs" and -10.0 < cx < 0.0):
            removed.append(o.name)
            me = o.data
            bpy.data.objects.remove(o, do_unlink=True)
            bpy.data.meshes.remove(me)
    made = P8.add_collision(col, infos, rails)
    x_e, zg, zq, yw, dt = wall["x_e"], wall["zg"], wall["zq"], wall["yw"], wall["door_top"]
    for y0, y1, z0, z1 in ((-yw, -DOOR_W / 2, zg, zq), (DOOR_W / 2, yw, zg, zq), (-DOOR_W / 2, DOOR_W / 2, dt, zq)):
        pts = [Vector((x, y, z)) * K for x in (x_e - 0.12, x_e) for y in (y0, y1) for z in (z0, z1)]
        made.append(C3.convex(f"UCX_TMP_{len(made)}", pts, col, "bulkhead_great_cabin"))
    ucx = [o for o in col.objects if o.name.startswith(("UCX_",))]
    order = sorted([o for o in ucx if o not in made], key=lambda o: o.name) + made
    for i, o in enumerate(order):
        o.name = f"_tmp_ucx_{i}"
    for i, o in enumerate(order):
        o.name = f"UCX_CORE_HULL_SHELL_{i:02d}"
        o.data.name = o.name
    return removed, made


def add_door_links(col, wall):
    added = []
    for end, dx in (("OUT", 0.6), ("IN", -0.6)):
        name = f"SOCK_NAVLINK_GREAT_CABIN_DOOR_{end}"
        loc = Vector((wall["x_e"] + dx, 0.0, P8.deck_top(wall["x_e"] + dx, 0.0, "gun"))) * K
        e, _ = P5.set_socket(name, loc, col, shape="SPHERE", size=0.2 * K, link="door", pair="SOCK_NAVLINK_GREAT_CABIN_DOOR")
        e["manifest_version"] = MANIFEST_VERSION
        added.append(name)
    return added


def render(sc):
    from mathutils import Vector as V
    H.setup_render(sc, fast=True)
    out = ROOT / "renders" / VER
    out.mkdir(parents=True, exist_ok=True)
    x_q, x_f = P8.edges()
    lamp = bpy.data.lights.new("CabinLamp", "POINT")
    lamp.energy = 900
    lamp.shadow_soft_size = 0.6
    lo = bpy.data.objects.new("LGT_CabinLamp", lamp)
    lo.location = V((-10.0, 0.0, 3.6)) * K
    sc.collection.objects.link(lo)
    views = [
        ("bel_kica", (4.0, -3.2, 5.8), (x_q - 1.0, 0.0, 3.6), 30),
        ("kamara_kapisi", (0.5, 0.8, 3.4), (x_q, 0.0, 3.2), 30),
        ("kamara_ici", (x_q - 0.6, 1.2, 3.5), (-16.0, -0.5, 3.0), 18),
        ("guverte", (18, 12, 28), (-4, 0, 3.0), 30),
        ("kic_omzu", (-34, -24, 12), (-4, 0, 2.5), 35),
    ]
    for name, loc, tgt, lens in views:
        sc.camera = H.camera(sc, f"CAM10_{name}", V(loc) * K, V(tgt) * K, lens=lens)
        sc.render.filepath = str(out / f"{SHIP}_{VER}_{name}.png")
        bpy.ops.render.render(write_still=True)


def main():
    if "--render-only" in sys.argv:
        bpy.ops.wm.open_mainfile(filepath=str(ROOT / "Blender" / "versions" / f"{SHIP}_{VER}.blend"))
        return render(bpy.context.scene)
    bpy.ops.wm.open_mainfile(filepath=str(ROOT / "Blender" / "versions" / f"{SHIP}_{SRC_VER}.blend"))
    sc = bpy.context.scene
    M = P5.ensure_materials()
    C = {c.name: c for c in bpy.data.collections}
    core = C["10_HULL_CORE"]
    replaced = [n for n in ("CORE_STAIRS_QD_S", "CORE_STAIRS_QD_P", "CORE_BREAST_RAIL_QD") if remove(n)]
    guns_moved = P9.relocate_main_guns(core, M)
    wall_ob, wall = build_front_wall(core, M)
    objs, infos, rails = build_stairs_and_rail(core, M, wall)
    P8.add_sockets(C["30_SOCKETS"], infos)
    added = add_door_links(C["30_SOCKETS"], wall)
    removed, made = update_collision(C["40_COLLISION"], infos, rails, wall)
    fc = json.loads((ROOT / "reports" / "scene_audit_v009.json").read_text(encoding="utf-8"))["fc_stairs"]["stairs_world"]
    all_infos = dict(infos)
    for k in ("FC_S", "FC_P"):
        all_infos[k] = {"bottom": [c / K for c in fc[k]["bottom"]], "top": [c / K for c in fc[k]["top"]]}
    conflicts = P8.crew_conflicts(all_infos)

    out = ROOT / "Blender" / "versions" / f"{SHIP}_{VER}.blend"
    if out.exists():
        raise SystemExit(f"{out} zaten var; versiyonlu kayıt üzerine yazılmaz.")
    bpy.ops.wm.save_as_mainfile(filepath=str(out), compress=True)

    H.VERSION = VER
    ap = ROOT / "reports" / f"scene_audit_{VER}.json"
    rep = H.audit(sc, ap)
    cabin_guns = [p[1] for p in H.port_positions() if p[0] == "MAIN" and p[2] < wall["x_e"]]
    rep["great_cabin"] = {
        "front_wall_x_world": round(wall["x_e"] * K, 3),
        "length_to_transom_world_m": round((wall["x_e"] - H.stern_x(wall["zg"] + 1.0)) * K, 2),
        "door_world_m": [round(DOOR_W * K, 2), round(DOOR_H * K, 2)],
        "guns_inside": cabin_guns,
        "qd_stairs_world": {k: {**v, "bottom": [round(c * K, 3) for c in v["bottom"]], "top": [round(c * K, 3) for c in v["top"]],
                                "y": [round(c * K, 3) for c in v["y"]]} for k, v in infos.items()},
        "crew_conflicts_all_access_stairs": conflicts,
        "rail_segments_design": [[round(a, 2), round(b, 2)] for a, b in rails[0]["segs"]],
    }
    rep["pass"] = {"name": "pass_v010_great_cabin", "source": f"Blender/versions/{SHIP}_{SRC_VER}.blend",
                   "pass_changes": {"removed": replaced, "added": [wall_ob.name] + [o.name for o in objs],
                                    "sockets_added": added, "ucx_removed": removed, "ucx_added": len(made),
                                    "guns_moved": guns_moved},
                   "manifest_version": MANIFEST_VERSION, "geometry_changed": "QD front wall/door, QD stairs, QD rail, gun ports 1-11; hull shell unchanged"}
    ap.write_text(json.dumps(rep, indent=2, ensure_ascii=False), encoding="utf-8")
    gc = rep["great_cabin"]
    print("CABIN", gc["front_wall_x_world"], gc["length_to_transom_world_m"], gc["door_world_m"], "guns", gc["guns_inside"])
    print("STAIRS", [(k, v["angle_deg"], v["y"]) for k, v in gc["qd_stairs_world"].items()])
    print("CONFLICTS", conflicts)
    print("RAIL", gc["rail_segments_design"], "UCX -", len(removed), "+", len(made))
    if "--no-render" not in sys.argv:
        render(sc)


if __name__ == "__main__":
    main()
