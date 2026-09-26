"""Pass v009 — baş kasarası merdivenleri sağ/sol köşelere (v008 üzerine; gövde kabuğu değişmez).

Çalıştırma (depo kökünden):
    python3 OTTOMAN_FRIGATE_1780_ISTANBUL/scripts/pass_v009_fc_stairs_corners.py [--no-render | --render-only]

Kullanıcı isteği (2026-09-26, iki görselle): baş kasarası merdivenleri kıç üstündekiler gibi olsun;
sağ ve sol köşelere, borda duvarına yaslı.
Kısıt: köşe merdivenleri 11. topun ön mürettebatının yerine düşüyordu. Ana bataryanın 1-11. topları
x = -13,4 … 9,55 (tasarım) arasında eşit aralıkla yeniden dizildi (aralık 2,36 → 2,30 m; 11. top
0,69 m geri). 12. top baş kasarası altında (14,25) kalır. Top sayısı değişmez.
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
_sp = importlib.util.spec_from_file_location("pass_v008", HERE / "pass_v008_access_stairs.py")
P8 = importlib.util.module_from_spec(_sp)
_sp.loader.exec_module(P8)
P5, H, C3, K = P8.P5, P8.H, P8.C3, P8.K

SRC_VER, VER = "v008", "v009"
ROOT, SHIP = H.ROOT, H.SHIP_ID
P8.VER = VER
MANIFEST_VERSION = 7
P8.MANIFEST_VERSION = MANIFEST_VERSION
GUN11_X = 9.55  # tasarım


def port_positions_v009():
    ports = []
    xs = list(np.linspace(-13.4, GUN11_X, 11)) + [P8.GUN12_X]
    for k, x in enumerate(xs):
        s = (x - H.stern_x(2)) / (H.bow_x(2) - H.stern_x(2))
        ports.append(("MAIN", k + 1, x, s, H.deck_z(s) + H.PORT_SILL + H.PORT_H / 2))
    for kind, idx, x, s, z in P5.port_positions_v005():
        if kind == "QD":
            ports.append((kind, idx, x, s, z))
    return ports


H.port_positions = port_positions_v009


def remove(name):
    ob = bpy.data.objects.get(name)
    if ob is None:
        return False
    me = ob.data
    bpy.data.objects.remove(ob, do_unlink=True)
    if me is not None and me.users == 0:
        bpy.data.meshes.remove(me)
    return True


def relocate_main_guns(core, M):
    old = bpy.data.objects["CUT_GUNPORTS"]
    dummy = bpy.data.objects.new("_dummy_hull", bpy.data.meshes.new("_dummy_hull"))
    core.objects.link(dummy)
    new = H.build_port_cutters(core, dummy)
    new.data.transform(P8.SK)
    old_me = old.data
    old.data = new.data
    bpy.data.objects.remove(new, do_unlink=True)
    dm = dummy.data
    bpy.data.objects.remove(dummy, do_unlink=True)
    bpy.data.meshes.remove(dm)
    if old_me.users == 0:
        bpy.data.meshes.remove(old_me)
    remove("CORE_GUNPORT_FRAMES")
    frames = H.build_port_frames(core, M)
    frames.data.transform(P8.SK)
    H.build_uv_fallback(frames)
    moved = []
    for kind, idx, x, s, z in H.port_positions():
        if kind != "MAIN":
            continue
        _, y = H.hull_point(s, z)
        for side, tag in ((1, "S"), (-1, "P")):
            g = bpy.data.objects[f"SOCKET_CANNON_{tag}_{idx:02d}"]
            new_loc = Vector((x, side * (y - 1.2), H.deck_z(s))) * K
            if (g.location - new_loc).length < 1e-4:
                continue
            old_loc = [round(v, 3) for v in g.location]
            g.location = new_loc
            g["manifest_version"] = MANIFEST_VERSION
            bpy.context.view_layer.update()
            for key, (role, (lx, ly)) in P5.P4.CREW.items():
                c = bpy.data.objects[f"SOCK_CREW_{tag}_{idx:02d}_{key}"]
                c.location = g.matrix_world @ (Vector((lx, ly, 0.0)) * K)
                c["manifest_version"] = MANIFEST_VERSION
            moved.append({"socket": g.name, "from": old_loc, "to": [round(v, 3) for v in g.location]})
    return moved


def corner_y(x_f):
    """Dış kenar: koşu boyunca iç borda yüzünün (duvarın olduğu yüksekliklerde) en dar yerinden 5 cm içeride."""
    ys = []
    for i in range(13):
        x = x_f - P8.RUN * i / 12
        z_lo = P8.zlev(P8.s_of_x(x, lambda s: P8.zlev(s, "gun")), "gun")
        z_hi = P8.zlev(P8.s_of_x(x, lambda s: P8.zlev(s, "fc")), "fc") + P5.RIM_H
        for k in range(9):
            z = z_lo + (z_hi - z_lo) * k / 8
            s = P8.s_of_x(x, lambda s, z=z: z)
            if z > H.top_z(s):
                continue
            ys.append(H.half_breadth(s, z) - 0.24)
    y_out = min(ys) - 0.05
    return (y_out - P8.STAIR_W, y_out)


def build_fc(core, M):
    _, x_f = P8.edges()
    y_in, y_out = corner_y(x_f)
    infos = {}
    objs = []
    for sgn, tag in ((1, "S"), (-1, "P")):
        yc = sgn * (y_in + y_out) / 2
        p1 = Vector((x_f, yc, P8.deck_top(x_f + 0.05, yc, "fc")))
        p0 = Vector((x_f - P8.RUN, yc, P8.deck_top(x_f - P8.RUN, yc, "gun")))
        bms = (bmesh.new(), bmesh.new(), bmesh.new())
        infos[f"FC_{tag}"] = P8.stair(bms, p0, p1)
        infos[f"FC_{tag}"]["y"] = sorted((sgn * y_in, sgn * y_out))
        objs.append(P8.merge_finish(f"CORE_STAIRS_FC_{tag}", list(zip(bms, (M["deck"], M["timber"], M["yellow"]))), core))
    xr = x_f + 0.08
    wf = P8.inner_half(xr, "fc") - 0.02
    segs = [(-(y_in - 0.05), y_in - 0.05)]
    bm_r, bm_p, bm_f = bmesh.new(), bmesh.new(), bmesh.new()
    for y0, y1 in segs:
        za, zb = P8.deck_top(xr, y0, "fc") - 0.03, P8.deck_top(xr, y1, "fc") - 0.03
        P5.box8(bm_p, [Vector((xr - 0.07, y0, za)), Vector((xr + 0.07, y0, za)), Vector((xr + 0.07, y1, zb)), Vector((xr - 0.07, y1, zb)),
                       Vector((xr - 0.07, y0, za + P5.RIM_H)), Vector((xr + 0.07, y0, za + P5.RIM_H)),
                       Vector((xr + 0.07, y1, zb + P5.RIM_H)), Vector((xr - 0.07, y1, zb + P5.RIM_H))])
        ys = [y0 + 0.08 + (y1 - y0 - 0.16) * t / 12 for t in range(13)]
        P5.rail_run(bm_r, [(xr, yy, za + (zb - za) * (yy - y0) / (y1 - y0) + P5.RIM_H) for yy in ys])
    zb_edge = P8.zlev(H.S_FC, "fc")
    P5.aabox(bm_f, x_f - 0.08, x_f + 0.02, -wf, wf, zb_edge - 0.30, zb_edge - 0.10)
    objs.append(P8.merge_finish("CORE_BREAST_RAIL_FC", [(bm_r, M["yellow"]), (bm_p, M["inner"]), (bm_f, M["yellow"])],
                                core, sharp=50, bevel=None))
    return objs, infos, [dict(key="FC", x=xr, segs=segs, level="fc")]


def replace_fc_collision(col, infos, rails):
    removed = []
    for o in list(col.objects):
        if not o.name.startswith("UCX_"):
            continue
        p = o.get("ucx_purpose")
        cx = sum((o.matrix_world @ v.co).x for v in o.data.vertices) / max(len(o.data.vertices), 1)
        if p == "rail_fc" or (p == "stairs" and cx > 5.0):
            removed.append(o.name)
            me = o.data
            bpy.data.objects.remove(o, do_unlink=True)
            bpy.data.meshes.remove(me)
    made = P8.add_collision(col, infos, rails)
    # adları sıkıştır: önce geçici, sonra 00..N sıralı (mevcut sıra korunur, yeniler sona)
    ucx = [o for o in col.objects if o.name.startswith("UCX_")]
    order = sorted([o for o in ucx if o not in made], key=lambda o: o.name) + made
    for i, o in enumerate(order):
        o.name = f"_tmp_ucx_{i}"
    for i, o in enumerate(order):
        o.name = f"UCX_CORE_HULL_SHELL_{i:02d}"
        o.data.name = o.name
    return removed, made


def main():
    if "--render-only" in sys.argv:
        bpy.ops.wm.open_mainfile(filepath=str(ROOT / "Blender" / "versions" / f"{SHIP}_{VER}.blend"))
        return P8.render(bpy.context.scene)
    bpy.ops.wm.open_mainfile(filepath=str(ROOT / "Blender" / "versions" / f"{SHIP}_{SRC_VER}.blend"))
    sc = bpy.context.scene
    M = P5.ensure_materials()
    C = {c.name: c for c in bpy.data.collections}
    core = C["10_HULL_CORE"]
    for n in ("CORE_STAIRS_FC_S", "CORE_STAIRS_FC_P", "CORE_BREAST_RAIL_FC"):
        remove(n)
    moved = relocate_main_guns(core, M)
    objs, infos, rails = build_fc(core, M)
    P8.add_sockets(C["30_SOCKETS"], infos)
    removed, made = replace_fc_collision(C["40_COLLISION"], infos, rails)
    # çakışma kontrolü: yeni baş kasarası + mevcut kıç kasarası merdivenleri
    qd = json.loads((ROOT / "reports" / "scene_audit_v008.json").read_text(encoding="utf-8"))["access_stairs"]["stairs_world"]
    all_infos = dict(infos)
    for k in ("QD_S", "QD_P"):
        all_infos[k] = {"bottom": [c / K for c in qd[k]["bottom"]], "top": [c / K for c in qd[k]["top"]]}
    conflicts = P8.crew_conflicts(all_infos)

    out = ROOT / "Blender" / "versions" / f"{SHIP}_{VER}.blend"
    if out.exists():
        raise SystemExit(f"{out} zaten var; versiyonlu kayıt üzerine yazılmaz.")
    bpy.ops.wm.save_as_mainfile(filepath=str(out), compress=True)

    H.VERSION = VER
    ap = ROOT / "reports" / f"scene_audit_{VER}.json"
    rep = H.audit(sc, ap)
    world = {k: {**v, "bottom": [round(c * K, 3) for c in v["bottom"]], "top": [round(c * K, 3) for c in v["top"]],
                 "y": [round(c * K, 3) for c in v["y"]], "riser_m": round(v["riser_m"] * K, 3)} for k, v in infos.items()}
    rep["fc_stairs"] = {"layout": "köşeler (sancak/iskele), borda duvarına yaslı", "stairs_world": world,
                        "crew_conflicts_all_access_stairs": conflicts,
                        "main_battery_x_design": [round(p[2], 3) for p in H.port_positions() if p[0] == "MAIN"]}
    rep["pass"] = {"name": "pass_v009_fc_stairs_corners", "source": f"Blender/versions/{SHIP}_{SRC_VER}.blend",
                   "pass_changes": {"rebuilt": ["CORE_STAIRS_FC_S", "CORE_STAIRS_FC_P", "CORE_BREAST_RAIL_FC", "CORE_GUNPORT_FRAMES",
                                                "CUT_GUNPORTS (mesh, yerinde)"],
                                    "guns_moved": moved, "ucx_removed": removed, "ucx_added": [o.name for o in made]},
                   "manifest_version": MANIFEST_VERSION, "geometry_changed": "FC stairs/rail, gun ports 1-11; hull shell unchanged"}
    ap.write_text(json.dumps(rep, indent=2, ensure_ascii=False), encoding="utf-8")
    print("FC", [(k, v["angle_deg"], v["y"]) for k, v in world.items()])
    print("GUNS MOVED", len(moved), "CONFLICTS", conflicts)
    print("UCX -", len(removed), "+", len(made))
    if "--no-render" not in sys.argv:
        P8.render(sc)


if __name__ == "__main__":
    main()
