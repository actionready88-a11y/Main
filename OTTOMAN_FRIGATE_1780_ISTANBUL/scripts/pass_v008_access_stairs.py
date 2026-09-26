"""Pass v008 — ana güverteden (bel) kıç kasarasına ve baş kasarasına merdivenler (v007 üzerine).

Çalıştırma (depo kökünden):
    python3 OTTOMAN_FRIGATE_1780_ISTANBUL/scripts/pass_v008_access_stairs.py [--no-render | --render-only]

Kullanıcı kararı (2026-09-26): "Her yer gezilebilir" için önce bel → kasara merdivenleri.
Geometri tasarım uzayında (Lyme ölçeği) kurulur ve v007 oyun ölçeğiyle (×1,10) dünyaya taşınır.
Yerleşim kısıtları:
  - Kıç kasarası: bordalarda batarya topları ve mürettebatı var → iki merdiven kasara ön kenarında,
    orta hattın iki yanında (|y| 0,35-1,25 m tasarım), kıça doğru yükselir.
  - Baş kasarası: kenar tasarımda x ≈ 13,1 m; açık beldeki en öndeki borda topu (12. top, x = 12,6) ve
    ön direk (x ≈ 12,0, orta hat) bu bölgede. 12. top baş kasarası altına alındı (x = 14,25 tasarım;
    lumbar, soket ve mürettebat birlikte). Merdivenler ön direğin iki yanında (|y| 0,45-1,35) başa doğru yükselir.
  - İki kasaranın ön korkuluğu kıç üstü stiliyle (kaide + torna balüster) yeniden; merdiven başlarında boşluk.
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


P5 = _load("pass_v005", "pass_v005_stern.py")
SS = _load("ship_scale", "ship_scale.py")
H, C3 = P5.H, P5.C3
K = SS.SHIP_SCALE
SRC_VER, VER = "v007", "v008"
ROOT, SHIP = H.ROOT, H.SHIP_ID
MANIFEST_VERSION = 6
SK = Matrix.Scale(K, 4)

STAIR_W = 0.90
RUN = 2.40
STEPS = 10
QD_BAND = (0.35, 1.25)       # |y|, tasarım
FC_BAND = (0.45, 1.35)       # |y|, tasarım (ön direğin iki yanı)
GUN12_X = 14.25              # tasarım; baş kasarası altı, arka mürettebatı merdiven başının önünde
P5.QD_PORT_X = (-10.00, -7.70)   # v006 kararı


def port_positions_v008():
    ports = []
    for kind, idx, x, s, z in P5.port_positions_v005():
        if kind == "MAIN" and idx == 12:
            x = GUN12_X
            s = (x - H.stern_x(2)) / (H.bow_x(2) - H.stern_x(2))
            z = H.deck_z(s) + H.PORT_SILL + H.PORT_H / 2
        ports.append((kind, idx, x, s, z))
    return ports


H.port_positions = port_positions_v008


def x_at(s, z):
    return H.stern_x(z) + s * (H.bow_x(z) - H.stern_x(z))


def s_of_x(x, zfn):
    lo, hi = 0.0, 1.0
    for _ in range(60):
        mid = (lo + hi) / 2
        if x_at(mid, zfn(mid)) < x:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def zlev(s, level):
    return H.deck_z(s) + (H.QD_H if level in ("qd", "fc") else 0.0)


def deck_top(x, y, level):
    zf = lambda s: zlev(s, level)  # noqa: E731
    s = s_of_x(x, zf)
    z = zf(s)
    half = H.hull_point(s, z)[1] - 0.24
    v = min(abs(y) / half, 1.0)
    return z + 0.12 * (1 - v * v)


def inner_half(x, level):
    zf = lambda s: zlev(s, level)  # noqa: E731
    s = s_of_x(x, zf)
    return H.hull_point(s, zf(s))[1] - 0.24


# --- Genel merdiven ---------------------------------------------------------------
def stair(bms, p0, p1, width=STAIR_W, n=STEPS):
    """p0: alt uç (alt güverte, merdiven ekseni), p1: üst uç (üst güverte kenarı). Tasarım uzayı."""
    bt, bs, bh = bms
    d = p1 - p0
    u = Vector((d.x, d.y, 0.0))
    run = u.length
    u.normalize()
    w = Vector((-u.y, u.x, 0.0))
    rise, tread = d.z / n, run / n
    hw = width / 2 - 0.02
    for k in range(1, n + 1):
        a = p0 + u * (tread * (k - 1) - 0.03)
        b = p0 + u * (tread * k)
        z = p0.z + rise * k
        c = [Vector((q.x, q.y, z - 0.05)) for q in (a - w * hw, b - w * hw, b + w * hw, a + w * hw)]
        c += [Vector((q.x, q.y, z)) for q in (a - w * hw, b - w * hw, b + w * hw, a + w * hw)]
        P5.box8(bt, c)
    slope = (p1 - p0).normalized()
    down = slope.cross(w).normalized()
    if down.z > 0:
        down = -down
    for side in (-1, 1):
        o = w * side * (width / 2 - 0.03)
        a0 = p0 - u * 0.10 + o + Vector((0, 0, -0.02))
        a1 = p1 + o + Vector((0, 0, -0.02))
        c = [a0, a1, a1 + down * 0.30, a0 + down * 0.30]
        c += [q + w * 0.06 for q in c]
        P5.box8(bs, c)
    hr = 0.95
    posts = [p0 + u * 0.05 + Vector((0, 0, rise)), p1 - u * 0.10]
    for side in (-1, 1):
        o = w * side * (width / 2 - 0.03)
        for p in posts:
            q = p + o
            P5.aabox(bh, q.x - 0.05, q.x + 0.05, q.y - 0.05, q.y + 0.05, q.z, q.z + hr + 0.08)
        for k in range(1, 5):
            q = posts[0].lerp(posts[1], k / 5) + o
            P5.aabox(bh, q.x - 0.02, q.x + 0.02, q.y - 0.02, q.y + 0.02, q.z, q.z + hr)
        a = posts[0] + o + Vector((0, 0, hr))
        b = posts[1] + o + Vector((0, 0, hr))
        dd = (b - a).normalized()
        pp = dd.cross(w).normalized() * 0.04
        c = [a - w * 0.04 - pp, b - w * 0.04 - pp, b + w * 0.04 - pp, a + w * 0.04 - pp]
        c += [q + pp * 2 for q in c]
        P5.box8(bh, c)
    info = dict(bottom=[round(v, 3) for v in p0], top=[round(v, 3) for v in p1],
                angle_deg=round(math.degrees(math.atan2(d.z, run)), 1), riser_m=round(rise, 3), tread_m=round(tread, 3))
    return info


def merge_finish(name, parts, col, sharp=40, bevel=0.008):
    """parts: [(bmesh, material)] → tek nesne; tasarım uzayından dünyaya (×K)."""
    merged = bmesh.new()
    mats = []
    for idx, (b, mat) in enumerate(parts):
        b.transform(SK)
        me = bpy.data.meshes.new("_tmp")
        b.to_mesh(me)
        b.free()
        me.polygons.foreach_set("material_index", [idx] * len(me.polygons))
        merged.from_mesh(me)
        bpy.data.meshes.remove(me)
        mats.append(mat)
    return P5.finish(name, merged, col, mats, sharp=sharp, bevel=bevel)


# --- Kasara kenarları ------------------------------------------------------------------
def edges():
    zq = zlev(H.S_QD, "qd")
    zf = zlev(H.S_FC, "fc")
    return x_at(H.S_QD, zq), x_at(H.S_FC, zf)


def build_all(core, M):
    x_q, x_f = edges()
    infos = {}
    objs = []
    # kıç kasarası merdivenleri (orta hattın iki yanı, kıça doğru yükselir)
    for sgn, tag in ((1, "S"), (-1, "P")):
        yc = sgn * (QD_BAND[0] + QD_BAND[1]) / 2
        p1 = Vector((x_q, yc, deck_top(x_q - 0.05, yc, "qd")))
        p0 = Vector((x_q + RUN, yc, deck_top(x_q + RUN, yc, "gun")))
        bms = (bmesh.new(), bmesh.new(), bmesh.new())
        infos[f"QD_{tag}"] = stair(bms, p0, p1)
        infos[f"QD_{tag}"]["y"] = sorted((sgn * QD_BAND[0], sgn * QD_BAND[1]))
        objs.append(merge_finish(f"CORE_STAIRS_QD_{tag}", list(zip(bms, (M["deck"], M["timber"], M["yellow"]))), core))
    # baş kasarası merdivenleri (ön direğin iki yanı, başa doğru yükselir)
    for sgn, tag in ((1, "S"), (-1, "P")):
        yc = sgn * (FC_BAND[0] + FC_BAND[1]) / 2
        p1 = Vector((x_f, yc, deck_top(x_f + 0.05, yc, "fc")))
        p0 = Vector((x_f - RUN, yc, deck_top(x_f - RUN, yc, "gun")))
        bms = (bmesh.new(), bmesh.new(), bmesh.new())
        infos[f"FC_{tag}"] = stair(bms, p0, p1)
        infos[f"FC_{tag}"]["y"] = sorted((sgn * FC_BAND[0], sgn * FC_BAND[1]))
        objs.append(merge_finish(f"CORE_STAIRS_FC_{tag}", list(zip(bms, (M["deck"], M["timber"], M["yellow"]))), core))

    # ön korkuluklar (kaide + torna balüster), merdiven başlarında boşluk
    rails = []
    for key, x_edge, level, gaps, dx in (
        ("QD", x_q, "qd", [(QD_BAND[0] - 0.05, QD_BAND[1] + 0.05)], -0.08),
        ("FC", x_f, "fc", [(FC_BAND[0] - 0.05, FC_BAND[1] + 0.05)], 0.08),
    ):
        xr = x_edge + dx
        wf = inner_half(xr, level) - 0.02
        cuts = sorted([(-b, -a) for a, b in gaps] + list(gaps))
        segs, y = [], -wf
        for a, b in cuts:
            if a > y:
                segs.append((y, min(a, wf)))
            y = max(y, b)
        if y < wf:
            segs.append((y, wf))
        segs = [(a, b) for a, b in segs if b - a > 0.30]
        bm_r, bm_p, bm_f = bmesh.new(), bmesh.new(), bmesh.new()
        for y0, y1 in segs:
            za, zb = deck_top(xr, y0, level) - 0.03, deck_top(xr, y1, level) - 0.03
            P5.box8(bm_p, [Vector((xr - 0.07, y0, za)), Vector((xr + 0.07, y0, za)), Vector((xr + 0.07, y1, zb)), Vector((xr - 0.07, y1, zb)),
                           Vector((xr - 0.07, y0, za + P5.RIM_H)), Vector((xr + 0.07, y0, za + P5.RIM_H)),
                           Vector((xr + 0.07, y1, zb + P5.RIM_H)), Vector((xr - 0.07, y1, zb + P5.RIM_H))])
            ys = [y0 + 0.08 + (y1 - y0 - 0.16) * t / 5 for t in range(6)]
            P5.rail_run(bm_r, [(xr, yy, za + (zb - za) * (yy - y0) / (y1 - y0) + P5.RAIL_H * 0 + P5.RIM_H) for yy in ys])
        # kenarın altındaki alın kirişi
        zb_edge = zlev(H.S_QD if key == "QD" else H.S_FC, level)
        x0, x1 = sorted((x_edge - 0.02 * (1 if key == "QD" else -1), x_edge + 0.08 * (1 if key == "QD" else -1)))
        P5.aabox(bm_f, x0, x1, -wf, wf, zb_edge - 0.30, zb_edge - 0.10)
        rails.append(dict(key=key, x=xr, segs=segs, level=level))
        objs.append(merge_finish(f"CORE_BREAST_RAIL_{key}", [(bm_r, M["yellow"]), (bm_p, M["inner"]), (bm_f, M["yellow"])],
                                 core, sharp=50, bevel=None))
    return objs, infos, rails


def relocate_gun12(core, socks, M):
    """12. top çiftini baş kasarası altına taşı: kesici mesh'i yerinde, çerçeveler, soketler, mürettebat."""
    old = bpy.data.objects["CUT_GUNPORTS"]
    dummy = bpy.data.objects.new("_dummy_hull", bpy.data.meshes.new("_dummy_hull"))
    core.objects.link(dummy)
    new = H.build_port_cutters(core, dummy)
    new.data.transform(SK)
    old_me = old.data
    old.data = new.data
    bpy.data.objects.remove(new, do_unlink=True)
    dm = dummy.data
    bpy.data.objects.remove(dummy, do_unlink=True)
    bpy.data.meshes.remove(dm)
    if old_me.users == 0:
        bpy.data.meshes.remove(old_me)
    fr = bpy.data.objects.get("CORE_GUNPORT_FRAMES")
    if fr:
        me = fr.data
        bpy.data.objects.remove(fr, do_unlink=True)
        if me.users == 0:
            bpy.data.meshes.remove(me)
    frames = H.build_port_frames(core, M)
    frames.data.transform(SK)
    H.build_uv_fallback(frames)
    moved = []
    for kind, idx, x, s, z in H.port_positions():
        if not (kind == "MAIN" and idx == 12):
            continue
        _, y = H.hull_point(s, z)
        dz = H.deck_z(s)
        for side, tag in ((1, "S"), (-1, "P")):
            g = bpy.data.objects[f"SOCKET_CANNON_{tag}_12"]
            old_loc = [round(v, 3) for v in g.location]
            g.location = Vector((x, side * (y - 1.2), dz)) * K
            g["manifest_version"] = MANIFEST_VERSION
            bpy.context.view_layer.update()
            for key, (role, (lx, ly)) in P5.P4.CREW.items():
                c = bpy.data.objects[f"SOCK_CREW_{tag}_12_{key}"]
                c.location = g.matrix_world @ (Vector((lx, ly, 0.0)) * K)
                c["manifest_version"] = MANIFEST_VERSION
            moved.append({"socket": g.name, "from": old_loc, "to": [round(v, 3) for v in g.location]})
    return moved


def add_sockets(col, infos):
    added = []
    for key, st in infos.items():
        p0, p1 = Vector(st["bottom"]), Vector(st["top"])
        u = Vector((p1.x - p0.x, p1.y - p0.y, 0)).normalized()
        for end, loc in (("BOTTOM", p0 - u * 0.35), ("TOP", p1 + u * 0.35)):
            name = f"SOCK_NAVLINK_{key.split('_')[0]}_STAIR_{key.split('_')[1]}_{end}"
            e, _ = P5.set_socket(name, loc * K, col, shape="SPHERE", size=0.2 * K, link="stairs",
                                 pair=f"SOCK_NAVLINK_{key.split('_')[0]}_STAIR_{key.split('_')[1]}")
            e["manifest_version"] = MANIFEST_VERSION
            added.append(name)
    return added


def add_collision(col, infos, rails):
    start = len([o for o in col.objects if o.name.startswith("UCX_")])
    made = []
    k = start
    for key, st in infos.items():
        p0, p1 = Vector(st["bottom"]), Vector(st["top"])
        u = Vector((p1.x - p0.x, p1.y - p0.y, 0)).normalized()
        w = Vector((-u.y, u.x, 0)) * (STAIR_W / 2)
        flat = Vector((p1.x, p1.y, p0.z))
        pts = [p * K for p in (p0 - w, p0 + w, p1 - w, p1 + w, flat - w, flat + w)]
        made.append(C3.convex(f"UCX_CORE_HULL_SHELL_{k:02d}", pts, col, "stairs"))
        k += 1
    for r in rails:
        for y0, y1 in r["segs"]:
            za = deck_top(r["x"], y0, r["level"])
            zb = deck_top(r["x"], y1, r["level"])
            pts = [Vector((x, y, z)) * K for x in (r["x"] - 0.08, r["x"] + 0.08) for (y, z0) in ((y0, za), (y1, zb))
                   for z in (z0, z0 + P5.RIM_H + P5.RAIL_H + 0.1)]
            made.append(C3.convex(f"UCX_CORE_HULL_SHELL_{k:02d}", pts, col, f"rail_{r['key'].lower()}"))
            k += 1
    return made


def crew_conflicts(infos, margin=0.20):
    out = []
    for key, st in infos.items():
        p0, p1 = Vector(st["bottom"]) * K, Vector(st["top"]) * K
        u = Vector((p1.x - p0.x, p1.y - p0.y, 0))
        L = u.length
        u.normalize()
        w = Vector((-u.y, u.x, 0))
        for o in bpy.data.objects:
            if o.type == "EMPTY" and o.name.startswith("SOCK_CREW_"):
                d = o.location - p0
                a, b = d.dot(u), d.dot(w)
                # üst ucun ötesi üst güvertenin altıdır (tavan 2 m+), merdiven değil
                if not (-margin <= a <= L and abs(b) <= STAIR_W * K / 2 + margin and abs(d.z) < 2.5):
                    continue
                # merdivenin o noktadaki alt yüzü (kiriş derinliği dahil) baş hizasının üstündeyse altından geçilir
                t = min(max(a / L, 0.0), 1.0)
                underside = p0.z + (p1.z - p0.z) * t - 0.35 * K
                if underside - o.location.z >= 1.90 * K:
                    continue
                out.append({"crew": o.name, "stair": key, "along": round(a, 2), "side": round(b, 2),
                            "headroom_m": round(underside - o.location.z, 2)})
    return out


def render(sc):
    H.setup_render(sc, fast=True)
    out = ROOT / "renders" / VER
    out.mkdir(parents=True, exist_ok=True)
    x_q, x_f = edges()
    views = [
        ("bel_kica", (4.0, -3.2, 5.8), (x_q - 1.0, 0.0, 3.6), 30),
        ("bel_basa", (4.0, 3.2, 5.8), (x_f + 0.5, 0.0, 3.8), 30),
        ("guverte", (18, 12, 28), (-4, 0, 3.0), 30),
        ("bas_omzu", (34, 26, 13), (1, 0, 1.5), 35),
        ("kic_omzu", (-34, -24, 12), (-4, 0, 2.5), 35),
    ]
    for name, loc, tgt, lens in views:
        sc.camera = H.camera(sc, f"CAM8_{name}", Vector(loc) * K, Vector(tgt) * K, lens=lens)
        sc.render.filepath = str(out / f"{SHIP}_{VER}_{name}.png")
        bpy.ops.render.render(write_still=True)


def main():
    if "--render-only" in sys.argv:
        bpy.ops.wm.open_mainfile(filepath=str(ROOT / "Blender" / "versions" / f"{SHIP}_{VER}.blend"))
        return render(bpy.context.scene)
    bpy.ops.wm.open_mainfile(filepath=str(ROOT / "Blender" / "versions" / f"{SHIP}_{SRC_VER}.blend"))
    sc = bpy.context.scene
    assert abs(float(sc.get("ship_scale", 1.0)) - K) < 1e-6, "v007 ölçeği bekleniyor"
    M = P5.ensure_materials()
    C = {c.name: c for c in bpy.data.collections}
    replaced = [n for n in ("CORE_BREAST_RAIL_QD", "CORE_BREAST_RAIL_FC") if bpy.data.objects.get(n)]
    for n in replaced:
        ob = bpy.data.objects[n]
        me = ob.data
        bpy.data.objects.remove(ob, do_unlink=True)
        if me.users == 0:
            bpy.data.meshes.remove(me)
    gun_moved = relocate_gun12(C["10_HULL_CORE"], C["30_SOCKETS"], M)
    objs, infos, rails = build_all(C["10_HULL_CORE"], M)
    added = add_sockets(C["30_SOCKETS"], infos)
    ucx = add_collision(C["40_COLLISION"], infos, rails)
    conflicts = crew_conflicts(infos)

    out = ROOT / "Blender" / "versions" / f"{SHIP}_{VER}.blend"
    if out.exists():
        raise SystemExit(f"{out} zaten var; versiyonlu kayıt üzerine yazılmaz.")
    bpy.ops.wm.save_as_mainfile(filepath=str(out), compress=True)

    H.VERSION = VER
    ap = ROOT / "reports" / f"scene_audit_{VER}.json"
    rep = H.audit(sc, ap)
    world = {k: {**v, "bottom": [round(c * K, 3) for c in v["bottom"]], "top": [round(c * K, 3) for c in v["top"]],
                 "riser_m": round(v["riser_m"] * K, 3), "tread_m": round(v["tread_m"] * K, 3)} for k, v in infos.items()}
    rep["access_stairs"] = {"stairs_world": world, "crew_conflicts": conflicts,
                            "rails": [{"key": r["key"], "segments_design": [[round(a, 2), round(b, 2)] for a, b in r["segs"]]} for r in rails]}
    rep["pass"] = {"name": "pass_v008_access_stairs", "source": f"Blender/versions/{SHIP}_{SRC_VER}.blend",
                   "pass_changes": {"replaced": replaced, "added": [o.name for o in objs if o.name not in replaced],
                                    "sockets_added": added, "ucx_added": [o.name for o in ucx],
                                    "gun12_moved_under_forecastle": gun_moved, "rebuilt": ["CUT_GUNPORTS (mesh, yerinde)", "CORE_GUNPORT_FRAMES"]},
                   "manifest_version": MANIFEST_VERSION, "geometry_changed": "stairs, breast rails, gun 12 ports/frames; hull shell unchanged"}
    ap.write_text(json.dumps(rep, indent=2, ensure_ascii=False), encoding="utf-8")
    print("STAIRS", [(k, v["angle_deg"], round(v["riser_m"] * K, 3)) for k, v in infos.items()])
    print("RAILS", [(r["key"], [(round(a, 2), round(b, 2)) for a, b in r["segs"]]) for r in rails])
    print("CONFLICTS", conflicts)
    print("UCX+", len(ucx), "SOCK+", len(added))
    if "--no-render" not in sys.argv:
        render(sc)


if __name__ == "__main__":
    main()
