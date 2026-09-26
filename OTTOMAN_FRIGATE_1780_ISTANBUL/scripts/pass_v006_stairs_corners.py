"""Pass v006 — kıç üstü güverte merdivenleri köşelere (v005 üzerine; gövde kabuğu değişmez).

Çalıştırma (depo kökünden):
    python3 OTTOMAN_FRIGATE_1780_ISTANBUL/scripts/pass_v006_stairs_corners.py [--no-render | --render-only]

Kullanıcı geri bildirimi (2026-09-26): "Şu an ikisi de ortada gibi duruyor; biri sağ, biri sol köşede duracak."
Değişenler:
  - İki merdiven kapının yanından borda duvarına yaslanan köşelere taşındı (sancak ve iskele).
    Dış kenar, iç duvar yüzünden 5 cm içeride; genişlik 0,90 m.
  - Ön korkuluk: orta parça kapının üstünde tek parça; köşeler merdiven boşluğu.
  - Kıç kasarası topları merdiven ayağından uzaklaşsın diye 30/20 cm ileri: x = -10,3/-7,9 → -10,0/-7,7
    (lumbar kesicisi yerinde güncellenir; gövde kabuğu yeniden üretilmez).
  - Navlink'ler, top/mürettebat soketleri ve UCX güncellenir (manifest 4).
"""

import importlib.util
import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
_sp = importlib.util.spec_from_file_location("pass_v005", HERE / "pass_v005_stern.py")
P5 = importlib.util.module_from_spec(_sp)
_sp.loader.exec_module(P5)
H, C3 = P5.H, P5.C3

SRC_VER, VER = "v005", "v006"
ROOT, SHIP = H.ROOT, H.SHIP_ID
P5.VER = VER
P5.MANIFEST_VERSION = 4
P5.QD_PORT_X = (-10.00, -7.70)
STAIR_W = 0.90


def corner_stair_y():
    """Merdivenin dış kenarı: koşu boyunca iç borda yüzünün en dar yerinden 5 cm içeride."""
    ys = []
    for i in range(13):
        x = P5.X_FRONT + P5.STAIR_RUN * i / 12
        z_lo = P5.zqd(P5.s_of_x(x, P5.zqd))
        z_hi = P5.zpd(P5.s_of_x(x, P5.zpd)) + P5.RIM_H
        for k in range(9):
            z = z_lo + (z_hi - z_lo) * k / 8
            s = P5.s_of_x(x, lambda s, z=z: z)
            if z > H.top_z(s):
                continue
            ys.append(H.half_breadth(s, z) - 0.24)
    y_out = min(ys) - 0.05
    return (round(y_out - STAIR_W, 3), round(y_out, 3))


def compute_bk():
    s_q = P5.s_of_x(P5.X_FRONT, P5.zqd)
    zq = P5.zqd(s_q)
    s_p = P5.s_of_x(P5.X_FRONT, P5.zpd)
    zp = P5.zpd(s_p)
    half_q = H.hull_point(s_q, zq)[1] - 0.24
    half_p = H.hull_point(s_p, zp)[1] - 0.24
    yq = H.hull_point(s_q, zq + 1.0)[1] - 0.10
    return dict(zq=zq, zp=zp, yq=yq, door_top=zq + 0.12 - 0.05 + P5.DOOR_H, half_p=half_p, half_q=half_q)


def remove(name):
    ob = bpy.data.objects.get(name)
    if ob is None:
        return False
    me = ob.data
    bpy.data.objects.remove(ob, do_unlink=True)
    if me is not None and me.users == 0:
        bpy.data.meshes.remove(me)
    return True


def rebuild_cutter_in_place(core):
    """CUT_GUNPORTS nesnesini koru (gövdedeki boolean ona bağlı), yalnız mesh'ini yenile."""
    old = bpy.data.objects["CUT_GUNPORTS"]
    dummy = bpy.data.objects.new("_dummy_hull", bpy.data.meshes.new("_dummy_hull"))
    core.objects.link(dummy)
    new = H.build_port_cutters(core, dummy)
    old_me = old.data
    old.data = new.data
    bpy.data.objects.remove(new, do_unlink=True)
    dm = dummy.data
    bpy.data.objects.remove(dummy, do_unlink=True)
    bpy.data.meshes.remove(dm)
    if old_me.users == 0:
        bpy.data.meshes.remove(old_me)


def main():
    if "--render-only" in sys.argv:
        bpy.ops.wm.open_mainfile(filepath=str(ROOT / "Blender" / "versions" / f"{SHIP}_{VER}.blend"))
        return P5.render_v005(bpy.context.scene)

    P5.STAIR_Y = corner_stair_y()
    bpy.ops.wm.open_mainfile(filepath=str(ROOT / "Blender" / "versions" / f"{SHIP}_{SRC_VER}.blend"))
    sc = bpy.context.scene
    M = P5.ensure_materials()
    C = {c.name: c for c in bpy.data.collections}
    core, socks = C["10_HULL_CORE"], C["30_SOCKETS"]

    replaced = ["CORE_STAIRS_POOP_S", "CORE_STAIRS_POOP_P", "CORE_POOP_BALUSTRADE", "CORE_POOP_BREAST_PLINTH",
                "CORE_GUNPORT_FRAMES"]
    for n in replaced:
        remove(n)
    rebuild_cutter_in_place(core)
    H.build_port_frames(core, M)
    stairs, stairs_info = P5.build_stairs(core, M)
    bk = compute_bk()
    P5.build_balustrade(core, M, bk)

    captain = bpy.data.objects["SOCK_STATION_CAPTAIN"].location.copy()
    lantern = bpy.data.objects["SOCKET_LANTERN_STERN"].location.copy()
    before = {o.name: tuple(round(v, 4) for v in o.location) for o in bpy.data.objects if o.type == "EMPTY"}
    P5.update_sockets(socks, captain, lantern, stairs_info, bk)
    bpy.context.view_layer.update()
    moved = [{"socket": n, "from": list(before[n]), "to": [round(v, 4) for v in bpy.data.objects[n].location]}
             for n in before if tuple(round(v, 4) for v in bpy.data.objects[n].location) != before[n]]
    ucx = P5.rebuild_collision(C["40_COLLISION"], bk, stairs_info)

    # kontrol: mürettebat noktaları merdiven ayak izine düşmesin
    conflicts = []
    for st in stairs_info:
        ya, yb = st["y"]
        for o in bpy.data.objects:
            if o.type == "EMPTY" and o.name.startswith("SOCK_CREW_") and "_QD_" in o.name:
                p = o.location
                if P5.X_FRONT - 0.3 <= p.x <= st["x_bottom"] + 0.35 and ya - 0.3 <= p.y <= yb + 0.3:
                    conflicts.append({"crew": o.name, "stair": st["side"], "loc": [round(v, 3) for v in p]})

    out = ROOT / "Blender" / "versions" / f"{SHIP}_{VER}.blend"
    if out.exists():
        raise SystemExit(f"{out} zaten var; versiyonlu kayıt üzerine yazılmaz.")
    bpy.ops.wm.save_as_mainfile(filepath=str(out), compress=True)

    H.VERSION = VER
    ap = ROOT / "reports" / f"scene_audit_{VER}.json"
    rep = H.audit(sc, ap)
    rep["stairs"] = {"layout": "köşeler (sancak/iskele), borda duvarına yaslı", "y_edges_abs_m": list(P5.STAIR_Y),
                     "info": stairs_info, "crew_conflicts": conflicts, "qd_gun_x": list(P5.QD_PORT_X)}
    rep["collision"] = {"count": len(ucx), "max_verts": max(len(o.data.vertices) for o in ucx),
                        "by_purpose": {p: sum(1 for o in ucx if o["ucx_purpose"] == p) for p in sorted({o["ucx_purpose"] for o in ucx})}}
    rep["pass"] = {"name": "pass_v006_stairs_corners", "source": f"Blender/versions/{SHIP}_{SRC_VER}.blend",
                   "pass_changes": {"rebuilt": replaced + ["CUT_GUNPORTS (mesh, yerinde)", "UCX_*"],
                                    "sockets_moved": moved},
                   "manifest_version": P5.MANIFEST_VERSION, "geometry_changed": "stairs/rails/port frames; hull shell unchanged"}
    ap.write_text(json.dumps(rep, indent=2, ensure_ascii=False), encoding="utf-8")
    print("STAIR_Y", P5.STAIR_Y, [(s["side"], s["angle_deg"], s["y"]) for s in stairs_info])
    print("MOVED", len(moved), [m["socket"] for m in moved][:12], "...")
    print("CONFLICTS", conflicts)
    print("UCX", rep["collision"])

    if "--no-render" not in sys.argv:
        P5.render_v005(sc)


if __name__ == "__main__":
    main()
