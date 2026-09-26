"""Pass v011 — kıç kasarası platformu kalkar; dümenli kıç üstü ve kaptan kamarası ana güverte seviyesine iner.

Çalıştırma (depo kökünden):
    python3 OTTOMAN_FRIGATE_1780_ISTANBUL/scripts/pass_v011_lower_stern.py [--no-render | --render-only]

Kullanıcı kararı (2026-09-26): "Kıç kasarası altında açık alan kalmayacak; orayı tamamen düzle ve bu kısmı
(kıç üstü + kapılı bölme) aşağı taşı; eski kapıyı kapat; merdivenleri aşağı doğru uzat; ek bir platform
olmayacak." Seçenek 1: kıç üstü, kasara yüksekliği civarına iner; "kamara yüksekliği daha da artırılabilir".
Uygulama (tasarım uzayında kurulur, ×1,10 ile dünyaya):
  - Kıç kasarası (güverte, ön korkuluk, merdivenler, v010 duvarı) kaldırıldı; o bölge düz ana güverte,
    borda üst kenarı bel yüksekliğinde.
  - Kıç üstü güverte ana güvertenin POOP_ABOVE_GUN = 2,40 m (tasarım; dünyada 2,64 m) üstünde.
    Altında kaptan kamarası (ana güverte seviyesi), kapısı belden girilen ön duvarda.
  - Köşe merdivenleri ana güverteden doğrudan kıç üstüne (11 basamak).
  - Gövde kabuğu, kuşaklar, silmeler ve batarya güvertesi yeniden üretildi (kıç üst yapısı değişti;
    su hattı altı aynı: kesit formülü ZM altında değişmez).
  - Toplar: kıç kasarası 3 librelikleri (4) kaldırıldı (güvertesi yok). Ana batarya bordada 11:
    10'u belde (x = -10,05 … 9,55 tasarım), 1'i baş kasarası altında (14,25). Kıç kovalama topları
    kamaranın kıç pencerelerinden (y = ±1,9) ateşler; aynadaki eski kovalama lumbarları kapatıldı.
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


P5 = _load("pass_v005", "pass_v005_stern.py")
P4 = P5.P4
SS = _load("ship_scale", "ship_scale.py")
H, C3 = P5.H, P5.C3
K = SS.SHIP_SCALE
SK = Matrix.Scale(K, 4)
SRC_VER, VER = "v010", "v011"
ROOT, SHIP = H.ROOT, H.SHIP_ID
MANIFEST_VERSION = 9

POOP_ABOVE_GUN = 2.40      # tasarım
GUN12_X = 14.25
WAIST_GUNS = (-10.05, 9.55, 10)
CHASE_STERN_Y = 1.90       # kıç pencere ekseni
ORIG_TOP_V001 = P5.ORIG_TOP  # v001 top_z (kıç ve baş kasaralı)


# --- Yeni kıç profili (tasarım) ----------------------------------------------------
def shape_top(s):
    """Kıç kasarasız v001 profili: bel, baş kasarası aynı."""
    waist = H.deck_z(s) + 1.70
    castle = H.deck_z(s) + H.QD_H + 1.10
    w_fc = H.smooth(H.S_FC - 0.03, H.S_FC + 0.02, s)
    return waist + (castle - waist) * w_fc


def zgun(s):
    return H.deck_z(s)


def zpoop(s):
    return H.deck_z(s) + POOP_ABOVE_GUN


P5.zqd = zgun             # kamara zemini = ana güverte
P5.zpd = zpoop
P5.POOP_H = POOP_ABOVE_GUN
P5.S_POOP = P5.s_of_x(P5.X_FRONT, lambda s: zgun(s) + 1.0)


def poop_w(s):
    return 1.0 - H.smooth(P5.S_POOP + 0.01, P5.S_POOP + 0.05, s)


def top_v011(s):
    t0 = shape_top(s)
    return t0 + (zpoop(s) + P5.RIM_H - t0) * poop_w(s)


def half_breadth_v011(s, z):
    bmax = H.B / 2 * H.plan(s)
    if z <= H.ZM:
        t = min((H.ZM - z) / (H.ZM - H.ZK), 1.0)
        n = H.fullness(s)
        y = bmax * max(1.0 - t ** n, 0.0) ** (1.0 / n)
    else:
        top_o = shape_top(s)
        t = min((z - H.ZM) / (top_o - H.ZM), 1.0)
        y = bmax * (1.0 - H.TUMBLE * t ** 1.6)
        if z > top_o:
            y -= 0.04 * (z - top_o)
    return max(y * H.stern_close(s, z), 0.0)


def port_positions_v011():
    ports = []
    xs = list(np.linspace(*WAIST_GUNS)) + [GUN12_X]
    for k, x in enumerate(xs):
        s = (x - H.stern_x(2)) / (H.bow_x(2) - H.stern_x(2))
        ports.append(("MAIN", k + 1, x, s, H.deck_z(s) + H.PORT_SILL + H.PORT_H / 2))
    return ports


H.top_z = top_v011
H.half_breadth = half_breadth_v011
H.port_positions = port_positions_v011

# kıç aynası çerçevesi (kamara ana güverte seviyesinde)
P5.Z0 = zgun(0.0)
P5.O_T = Vector((H.stern_x(P5.Z0), 0.0, P5.Z0))
P5.WIN_V = (P5.v_of_z(P5.Z0 + 0.75), P5.v_of_z(P5.Z0 + 1.75))


def FT(u, v, w):
    return P5.O_T + P5.U_T * u + P5.V_T * v + P5.N_T * w


P5.FT = FT
P5.STAIR_RUN = 2.70
P5.STAIR_STEPS = 11


def corner_stair_y():
    ys = []
    for i in range(13):
        x = P5.X_FRONT + P5.STAIR_RUN * i / 12
        z_lo = zgun(P5.s_of_x(x, zgun))
        z_hi = zpoop(P5.s_of_x(x, zpoop)) + P5.RIM_H
        for k in range(9):
            z = z_lo + (z_hi - z_lo) * k / 8
            s = P5.s_of_x(x, lambda s, z=z: z)
            if z > H.top_z(s):
                continue
            ys.append(H.half_breadth(s, z) - 0.24)
    y_out = min(ys) - 0.05
    return (round(y_out - 0.90, 3), round(y_out, 3))


# --- Yardımcılar -----------------------------------------------------------------
def remove(name):
    ob = bpy.data.objects.get(name)
    if ob is None:
        return False
    me = ob.data
    bpy.data.objects.remove(ob, do_unlink=True)
    if me is not None and me.users == 0:
        bpy.data.meshes.remove(me)
    return True


def to_world(ob):
    """Tasarım uzayında kurulan nesneyi dünya ölçeğine taşı (mesh + konum + UV)."""
    ob.location = ob.location * K
    if ob.type == "MESH":
        ob.data.transform(SK)
        for uvl in ob.data.uv_layers:
            for d in uvl.data:
                d.uv = d.uv * K


REMOVE = ["CORE_HULL_SHELL", "CUT_GUNPORTS", "CUT_STERN_WINDOWS", "CORE_GUNPORT_FRAMES", "CORE_MOULDING_RAIL",
          "CORE_WALE_MAIN", "CORE_WALE_LOWER", "CORE_MOULDING_BAND_LOW", "CORE_DECK_GUN", "CORE_DECK_QUARTER",
          "CORE_BREAST_RAIL_QD", "CORE_STAIRS_QD_S", "CORE_STAIRS_QD_P", "CORE_GREAT_CABIN_BULKHEAD",
          "CORE_DECK_POOP", "CORE_POOP_BULKHEAD", "CORE_POOP_BULKHEAD_TRIM", "CORE_STAIRS_POOP_S", "CORE_STAIRS_POOP_P",
          "CORE_POOP_BALUSTRADE", "CORE_POOP_BREAST_PLINTH", "MOD_STERN_GALLERY_A", "MOD_HELM_WHEEL_A", "MOD_LANTERN_STERN_A"]


def build_geometry(C, M):
    core = C["10_HULL_CORE"]
    before = set(bpy.data.objects)
    hull = H.build_hull_shell(core, M)
    cut = H.build_port_cutters(core, hull)
    # aynadaki eski kıç kovalama lumbarlarını kapat (toplar artık kamara pencerelerinden ateşler)
    bm = bmesh.new()
    bm.from_mesh(cut.data)
    islands, seen = [], set()
    for v in bm.verts:
        if v.index in seen:
            continue
        stack, isl = [v], []
        while stack:
            a = stack.pop()
            if a.index in seen:
                continue
            seen.add(a.index)
            isl.append(a)
            stack += [e.other_vert(a) for e in a.link_edges]
        islands.append(isl)
    kill = [v for isl in islands if sum(p.co.x for p in isl) / len(isl) < -17.0 for v in isl]
    bmesh.ops.delete(bm, geom=kill, context="VERTS")
    bm.to_mesh(cut.data)
    bm.free()
    cut.hide_set(True)
    cut.hide_viewport = True
    P5.build_stern_window_cutter(core, hull)
    H.build_port_frames(core, M)
    H.band_strip("CORE_WALE_MAIN", lambda s: H.deck_z(s) + 0.15, 0.34, 0.12, core, M["hull"], 0.01, 0.985)
    H.band_strip("CORE_WALE_LOWER", lambda s: H.deck_z(s) - 0.55, 0.26, 0.10, core, M["hull"], 0.01, 0.975)
    H.band_strip("CORE_MOULDING_BAND_LOW", lambda s: H.deck_z(s) + 1.30, 0.07, 0.06, core, M["gold"], 0.005, 0.99)
    H.band_strip("CORE_MOULDING_RAIL", lambda s: H.top_z(s) - 0.06, 0.12, 0.10, core, M["yellow"], 0.003, 0.995)
    H.deck_surface("CORE_DECK_GUN", 0.02, 0.975, H.deck_z, core, M["deck"])
    P5.build_poop_deck(core, M)
    _, bk = P5.build_bulkhead(core, M)
    P5.STAIR_Y = corner_stair_y()
    _, stairs_info = P5.build_stairs(core, M)
    P5.build_balustrade(core, M, bk)
    sock = Vector((H.stern_x(P5.Z0), 0.0, P5.Z0))
    _, lantern_loc = P5.build_stern_gallery(C["24_MODULES_DECOR"], M, sock)
    hx = P5.X_FRONT - 1.9
    helm_loc = Vector((hx, 0.0, P5.deck_top(hx, 0.0, "poop")))
    _, helm_station = P5.build_helm(C["23_MODULES_DECK"], M, helm_loc)
    P5.build_lantern(M, lantern_loc)
    new = [o for o in bpy.data.objects if o not in before]
    for o in new:
        to_world(o)
    return new, bk, stairs_info, dict(sock=sock, lantern=lantern_loc, helm=helm_loc, helm_station=helm_station)


def set_world(name, loc_design, col, **props):
    e = bpy.data.objects.get(name)
    if e is None:
        e = P4.empty(name, Vector(loc_design) * K, col, shape="SPHERE", size=0.2 * K)
    old = [round(v, 3) for v in e.location]
    e.location = Vector(loc_design) * K
    for k, v in props.items():
        e[k] = v
    e["manifest_version"] = MANIFEST_VERSION
    return {"socket": name, "from": old, "to": [round(v, 3) for v in e.location]}


def update_sockets(col, bk, stairs_info, locs):
    moved, deleted = [], []
    for o in list(bpy.data.objects):
        if o.type != "EMPTY":
            continue
        n = o.name
        if ("_QD_" in n and (n.startswith("SOCKET_CANNON_") or n.startswith("SOCK_CREW_"))) \
                or n.startswith(("SOCK_NAVLINK_QD_STAIR_", "SOCK_NAVLINK_GREAT_CABIN_")) \
                or n in ("SOCKET_CANNON_S_12", "SOCKET_CANNON_P_12") or n.startswith(("SOCK_CREW_S_12_", "SOCK_CREW_P_12_")):
            deleted.append(n)
            bpy.data.objects.remove(o, do_unlink=True)
    for kind, idx, x, s, z in H.port_positions():
        _, y = H.hull_point(s, z)
        for side, tag in ((1, "S"), (-1, "P")):
            g = bpy.data.objects[f"SOCKET_CANNON_{tag}_{idx:02d}"]
            moved.append(set_world(g.name, (x, side * (y - 1.2), H.deck_z(s)), col))
    for tag, side in (("S", 1), ("P", -1)):
        moved.append(set_world(f"SOCKET_CANNON_CHASE_STERN_{tag}", (H.stern_x(2.5) + 1.2, side * CHASE_STERN_Y, H.deck_z(0.0)), col,
                               note="kamara kıç penceresinden ateşler"))
    bpy.context.view_layer.update()
    for g in [o for o in bpy.data.objects if o.type == "EMPTY" and o.name.startswith("SOCKET_CANNON_")]:
        g["slot"] = "SLOT_" + g.name[len("SOCKET_"):]
        tag = g.name[len("SOCKET_CANNON_"):]
        for key, (role, (lx, ly)) in P4.CREW.items():
            c = bpy.data.objects.get(f"SOCK_CREW_{tag}_{key}")
            if c:
                c.location = g.matrix_world @ (Vector((lx, ly, 0.0)) * K)
                c["manifest_version"] = MANIFEST_VERSION
    moved.append(set_world("SOCKET_STERN_MODULE", locs["sock"], col))
    moved.append(set_world("SOCKET_LANTERN_STERN", locs["lantern"], col))
    moved.append(set_world("SOCKET_HELM", locs["helm"], col))
    moved.append(set_world("SOCK_STATION_CAPTAIN", locs["helm_station"], col, station_role="captain"))
    xs2 = P5.X_FRONT - 0.7
    moved.append(set_world("SOCK_STATION_SECOND_CAPTAIN", (xs2, 0.0, P5.deck_top(xs2, 0.0, "poop")), col))
    xf = H.stern_x(zpoop(0.0)) + 0.75
    moved.append(set_world("SOCKET_FLAG_STERN", (xf, 0.0, P5.deck_top(xf, 0.0, "poop")), col))
    for st in stairs_info:
        sgn = 1 if st["side"] == "S" else -1
        ym = sgn * (P5.STAIR_Y[0] + P5.STAIR_Y[1]) / 2
        moved.append(set_world(f"SOCK_NAVLINK_POOP_STAIR_{st['side']}_BOTTOM", (st["x_bottom"] + 0.35, ym, st["z_bottom"]), col))
        moved.append(set_world(f"SOCK_NAVLINK_POOP_STAIR_{st['side']}_TOP", (P5.X_FRONT - 0.35, ym, st["z_top"]), col))
    for end, dx in (("OUT", 0.6), ("IN", -0.6)):
        moved.append(set_world(f"SOCK_NAVLINK_CABIN_DOOR_{end}", (P5.X_FRONT + dx, 0.0, bk["zq"] + 0.12), col,
                               room="captain_cabin (kıç üstü altı, ana güverte seviyesi)"))
    for n in ("SOCK_STATION_GUNNERY_OFFICER",):
        bpy.data.objects[n]["manifest_version"] = MANIFEST_VERSION
    return [m for m in moved if m["from"] != m["to"]], deleted


def rebuild_collision(col, bk, stairs_info):
    keep = []
    for o in list(col.objects):
        if not o.name.startswith("UCX_"):
            continue
        p = o.get("ucx_purpose")
        cx = sum((o.matrix_world @ v.co).x for v in o.data.vertices) / max(len(o.data.vertices), 1)
        if p == "rail_fc" or (p == "stairs" and cx > 5.0):
            keep.append(o)
            continue
        me = o.data
        bpy.data.objects.remove(o, do_unlink=True)
        bpy.data.meshes.remove(me)
    parts = C3.hull_slices(6)
    parts += C3.deck_slices(0.02, 0.975, H.deck_z, 10, "deck_gun")
    parts += C3.deck_slices(H.S_FC, 0.985, lambda s: H.deck_z(s) + H.QD_H, 2, "deck_forecastle")
    parts += C3.deck_slices(0.004, P5.s_of_x(P5.X_FRONT, zpoop), zpoop, 2, "deck_poop")
    parts += C3.bulwark_slices(14)
    pts = []
    for z in np.linspace(H.deck_z(0.0), H.top_z(0.0), 6):
        y = H.half_breadth(0.0, z)
        for dx in (0.0, 0.30):
            pts += [Vector((H.stern_x(z) + dx, y, z)), Vector((H.stern_x(z) + dx, -y, z))]
    parts.append((pts, "transom"))
    zq, zp, yq, dt = bk["zq"], bk["zp"], bk["yq"], bk["door_top"]
    for y0, y1, z0, z1 in ((-yq, -P5.DOOR_W / 2, zq, zp), (P5.DOOR_W / 2, yq, zq, zp), (-P5.DOOR_W / 2, P5.DOOR_W / 2, dt, zp)):
        parts.append(([Vector((x, y, z)) for x in (P5.X_FRONT - 0.12, P5.X_FRONT) for y in (y0, y1) for z in (z0, z1)], "bulkhead"))
    for st in stairs_info:
        ya, yb = st["y"]
        parts.append(([Vector((x, y, z)) for y in (ya, yb) for (x, z) in ((st["x_bottom"], st["z_bottom"]), (st["x_top"], st["z_top"]),
                                                                           (st["x_top"], st["z_bottom"]))], "stairs"))
    s_front_top = P5.s_of_x(P5.X_FRONT - 0.05, lambda s: H.top_z(s))
    edges = np.linspace(s_front_top, 0.004, 4)
    for sgn in (1, -1):
        for a, b in zip(edges[:-1], edges[1:]):
            pts = []
            for s in (a, b):
                z = H.top_z(s)
                x = P5.x_at(s, z)
                y = H.half_breadth(s, z) - 0.12
                pts += [Vector((x, sgn * (y + dy), z + dz)) for dy in (-0.08, 0.08) for dz in (0.0, P5.RAIL_H + 0.09)]
            parts.append((pts, "rail_poop"))
    zt = H.top_z(0.0)
    xt = H.stern_x(zt) + 0.12
    yt = H.half_breadth(0.004, zt)
    parts.append(([Vector((xt + dx, y, zt + dz)) for dx in (-0.08, 0.08) for y in (-yt, yt) for dz in (0.0, P5.RAIL_H + 0.9)], "rail_poop"))
    for y0, y1 in P5.front_rail_segments(bk["half_p"] + 0.22):
        parts.append(([Vector((x, y, z)) for x in (P5.X_FRONT - 0.14, P5.X_FRONT) for y in (y0, y1)
                       for z in (zp, zp + P5.RIM_H + P5.RAIL_H + 0.1)], "rail_poop"))
    made = [C3.convex(f"UCX_TMP_{k}", [p * K for p in pts], col, purpose) for k, (pts, purpose) in enumerate(parts)]
    order = sorted(keep, key=lambda o: o.name) + made
    order = made + sorted(keep, key=lambda o: o.name)
    for i, o in enumerate(order):
        o.name = f"_tmp_ucx_{i}"
    for i, o in enumerate(order):
        o.name = f"UCX_CORE_HULL_SHELL_{i:02d}"
        o.data.name = o.name
    return order


def crew_conflicts(stairs_info):
    out = []
    for st in stairs_info:
        ya, yb = [c * K for c in st["y"]]
        x0, x1 = st["x_top"] * K, st["x_bottom"] * K
        for o in bpy.data.objects:
            if o.type == "EMPTY" and o.name.startswith("SOCK_CREW_"):
                p = o.location
                if x0 - 0.2 <= p.x <= x1 + 0.2 and ya - 0.2 <= p.y <= yb + 0.2 and abs(p.z - st["z_bottom"] * K) < 1.0:
                    out.append({"crew": o.name, "stair": st["side"], "loc": [round(v, 2) for v in p]})
    return out


def render(sc):
    H.setup_render(sc, fast=True)
    out = ROOT / "renders" / VER
    out.mkdir(parents=True, exist_ok=True)
    lamp = bpy.data.lights.new("CabinLamp", "POINT")
    lamp.energy = 500
    lo = bpy.data.objects.new("LGT_CabinLamp", lamp)
    lo.location = Vector((-16.0, 0.0, 4.3)) * K
    sc.collection.objects.link(lo)
    V = Vector
    views = [
        ("bel_kica", (0.0, -3.0, 6.0), (-14.5, 0.0, 3.6), 30, None),
        ("kic_yakin", (-27, 11, 7.0), (-17.5, 0, 4.0), 40, None),
        ("kic_omzu", (-34, -24, 12), (-4, 0, 2.5), 35, None),
        ("kic_ust_guverte", (-8.0, 7.0, 10.5), (-15.5, 0, 5.0), 28, None),
        ("kamara_ici", (-14.3, 1.0, 3.9), (-18.5, -0.6, 3.6), 18, None),
        ("guverte", (18, 12, 28), (-4, 0, 3.0), 30, None),
        ("iskele_profil", (1.5, -80, 2.3), (1.5, 0, 2.3), None, 48),
        ("sancak_profil", (1.5, 80, 2.3), (1.5, 0, 2.3), None, 48),
        ("kic", (-60, 0, 2.3), (0, 0, 2.3), None, 27),
        ("bas", (60, 0, 2.3), (0, 0, 2.3), None, 27),
    ]
    for name, loc, tgt, lens, osc in views:
        if osc:
            cam = H.camera(sc, f"CAM11_{name}", V(loc) * K, V(tgt) * K, ortho=osc * K)
        else:
            cam = H.camera(sc, f"CAM11_{name}", V(loc) * K, V(tgt) * K, lens=lens)
        sc.camera = cam
        sc.render.filepath = str(out / f"{SHIP}_{VER}_{name}.png")
        bpy.ops.render.render(write_still=True)


def main():
    if "--render-only" in sys.argv:
        bpy.ops.wm.open_mainfile(filepath=str(ROOT / "Blender" / "versions" / f"{SHIP}_{VER}.blend"))
        return render(bpy.context.scene)
    bpy.ops.wm.open_mainfile(filepath=str(ROOT / "Blender" / "versions" / f"{SHIP}_{SRC_VER}.blend"))
    sc = bpy.context.scene
    assert abs(float(sc.get("ship_scale", 1.0)) - K) < 1e-6
    M = P5.ensure_materials()
    C = {c.name: c for c in bpy.data.collections}
    removed = [n for n in REMOVE if remove(n)]
    new, bk, stairs_info, locs = build_geometry(C, M)
    moved, deleted = update_sockets(C["30_SOCKETS"], bk, stairs_info, locs)
    ucx = rebuild_collision(C["40_COLLISION"], bk, stairs_info)
    conflicts = crew_conflicts(stairs_info)

    out = ROOT / "Blender" / "versions" / f"{SHIP}_{VER}.blend"
    if out.exists():
        raise SystemExit(f"{out} zaten var; versiyonlu kayıt üzerine yazılmaz.")
    bpy.ops.wm.save_as_mainfile(filepath=str(out), compress=True)

    H.VERSION = VER
    ap = ROOT / "reports" / f"scene_audit_{VER}.json"
    rep = H.audit(sc, ap)
    zq, zp = bk["zq"], bk["zp"]
    rep["stern_v011"] = {
        "poop_deck_above_gun_deck_world_m": round(POOP_ABOVE_GUN * K, 3),
        "cabin_clear_height_center_world_m": round(((zp + 0.12 - 0.10) - (zq + 0.12)) * K, 3),
        "poop_front_x_world": round(P5.X_FRONT * K, 3),
        "stairs": [{**s, "x_bottom": round(s["x_bottom"] * K, 3), "x_top": round(s["x_top"] * K, 3),
                    "z_bottom": round(s["z_bottom"] * K, 3), "z_top": round(s["z_top"] * K, 3),
                    "riser_m": round(s["riser_m"] * K, 3), "y": [round(c * K, 3) for c in s["y"]]} for s in stairs_info],
        "stairs_crew_conflicts": conflicts,
        "guns_per_side_main": len(H.port_positions()), "main_gun_x_design": [round(p[2], 2) for p in H.port_positions()],
        "chase": {"bow": 2, "stern": 2},
    }
    rep["pass"] = {"name": "pass_v011_lower_stern", "source": f"Blender/versions/{SHIP}_{SRC_VER}.blend",
                   "pass_changes": {"removed": removed, "rebuilt_or_added": [o.name for o in new], "sockets_deleted": deleted,
                                    "sockets_moved": len(moved), "ucx": len(ucx)},
                   "manifest_version": MANIFEST_VERSION, "geometry_changed": "kıç üst yapısı; su hattı altı aynı"}
    ap.write_text(json.dumps(rep, indent=2, ensure_ascii=False), encoding="utf-8")
    st = rep["stern_v011"]
    print("POOP", st["poop_deck_above_gun_deck_world_m"], "CABIN", st["cabin_clear_height_center_world_m"])
    print("STAIRS", [(s["side"], s["angle_deg"], s["riser_m"], s["y"]) for s in st["stairs"]])
    print("CONFLICTS", conflicts)
    print("GUNS", st["guns_per_side_main"], st["main_gun_x_design"])
    print("DELETED", len(deleted), "MOVED", len(moved), "UCX", len(ucx), "BOUNDS", rep["checks"]["bounds_m"])
    if "--no-render" not in sys.argv:
        render(sc)


if __name__ == "__main__":
    main()
