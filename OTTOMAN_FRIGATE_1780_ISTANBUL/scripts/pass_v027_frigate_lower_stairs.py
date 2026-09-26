"""Pass v027 — Frigate kararı: alt güverte 3+3 top yükseltmesi, dengeli yerleşim; merdiven/ambar ağzı çakışmaları, v026 üzerine.

Çalıştırma (depo kökünden):
    python3 OTTOMAN_FRIGATE_1780_ISTANBUL/scripts/pass_v027_frigate_lower_stairs.py [--no-render | --render-only]

Kullanıcı (2026-09-26):
  - "Gemi frigate olacak; kalyon ve hat gemisi ayrıntıları eklenmeyecek; frigate gelişip hat gemisi olamayacak."
  - "20+4 topumuz var; alta en fazla 6 top daha eklenebilsin (yükseltilmiş ama hat gemisi değil)."
  - "6 topu dengeli yerleştir, üstteki 20 topla uyumlu atış yapabilsin."
  - "Alt güverteye açılan kapaklarla merdivenler iç içe girmiş, düzeltelim."
Uygulama:
  1. Alt batarya 10+10 → 3+3. Tutulan lumbarlar x = -5,06 / -0,27 / +4,52 m (dünya): bordada simetrik, eşit aralıklı
     (4,8 m), üç topun ortalaması üst bataryanın merkezine denk (-0,27 / -0,26 m) → boyuna denge; her biri iki üst
     lumbarın tam arasında (şaşırtmalı) → açık kapak üst topların atış hattını kapatmaz, geri tepme alanları çakışmaz.
     Silinen: 14 lumbar kesicisi/çerçevesi, 14 kapak, 14 top soketi + 56 mürettebat soketi. Kalanlar 01–03 olarak
     yeniden numaralandı.
  2. Uyumlu atış: tüm borda top soketlerine (üst 20 + alt 6) `fire_group` = BROADSIDE_STARBOARD / BROADSIDE_PORT ve
     `fire_level` (upper/lower) verildi; oyun tek emirle bordayı ateşler, alt toplar yükseltme alınınca gruba katılır.
  3. Merdivenler: 7 merdivenin (kıç üstü 2, baş kasarası 2, alt güverte 2, ambar 1) yan kirişleri eğim yüzünden
     güverte kalınlığına/koaminge ve alt güverte tavanına giriyordu. Kirişler taban ve üst güverte düzlemlerinde
     kırpılarak yeniden kuruldu (basamak, tırabzan ve konumlar aynı).
  4. Etkilenen türev parçalar yenilendi: asma dirsekler, halka cıvataları/brok halatları, LOD'lar.
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


def _load(name, fname):
    sp = importlib.util.spec_from_file_location(name, HERE / fname)
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


P18 = _load("pass_v018", "pass_v018_battery_dressing.py")
P26 = _load("pass_v026", "pass_v026_lods.py")
P13, P5, H = P18.P13, P18.P5, P18.H
SRC_VER, VER = "v026", "v027"
ROOT, SHIP = H.ROOT, H.SHIP_ID
MANIFEST_VERSION = 23
P5.MANIFEST_VERSION = MANIFEST_VERSION
V = Vector
K = P13.K
KEEP = (3, 5, 7)                  # v013 alt lumbar indeksleri (dünya x = -5,06 / -0,27 / +4,52)
STAIRS = ["CORE_STAIRS_POOP_S", "CORE_STAIRS_POOP_P", "CORE_STAIRS_FC_S", "CORE_STAIRS_FC_P",
          "CORE_LADDER_LOWER_AFT", "CORE_LADDER_LOWER_FORE", "CORE_LADDER_HOLD"]


# --- 1) Alt batarya 3+3 -------------------------------------------------------------------------
_ORIG_LOWER = P13.lower_ports


def kept_ports():
    allp = _ORIG_LOWER()
    return [(kind, n + 1, x, s, z) for n, (kind, idx, x, s, z) in enumerate([p for p in allp if p[1] in KEEP])]


def remove_obj(name):
    o = bpy.data.objects.get(name)
    if o is None:
        return False
    me = o.data
    bpy.data.objects.remove(o, do_unlink=True)
    if me is not None and getattr(me, "users", 1) == 0:
        bpy.data.meshes.remove(me)
    return True


def rebuild_lower_ports(core, M):
    orig = P13.lower_ports
    P13.lower_ports = kept_ports
    try:
        cut_old = bpy.data.objects["CUT_GUNPORTS_LOWER"]
        bm = bmesh.new()
        for kind, idx, x, s, z in kept_ports():
            _, y = H.hull_point(s, z)
            for side in (1, -1):
                r = bmesh.ops.create_cube(bm, size=1.0)
                bmesh.ops.scale(bm, vec=(H.PORT_W, 1.2, H.PORT_H), verts=r["verts"])
                bmesh.ops.translate(bm, vec=(x, side * y, z), verts=r["verts"])
        bm.transform(P13.SHIFT @ Matrix.Scale(K, 4))
        old_me = cut_old.data
        new_me = bpy.data.meshes.new("CUT_GUNPORTS_LOWER")
        bm.to_mesh(new_me)
        bm.free()
        cut_old.data = new_me
        bpy.data.meshes.remove(old_me)
        remove_obj("CORE_GUNPORT_FRAMES_LOWER")
        orig_pp = H.port_positions
        H.port_positions = kept_ports
        fr = H.build_port_frames(core, M)
        H.port_positions = orig_pp
        fr.name = fr.data.name = "CORE_GUNPORT_FRAMES_LOWER"
        P13.place(fr)
        H.build_uv_fallback(fr)
    finally:
        P13.lower_ports = orig
    removed, renamed = [], []
    new_idx = {old: n + 1 for n, old in enumerate(KEEP)}
    for tag in ("S", "P"):
        for old in range(1, 11):
            base = f"LOWER_{tag}_{old:02d}"
            if old not in KEEP:
                for n in (f"MOD_PORT_LID_{base}", f"SOCKET_PORT_LID_{base}", f"SOCKET_CANNON_{base}"):
                    if remove_obj(n):
                        removed.append(n)
                for key in "ABCD":
                    if remove_obj(f"SOCK_CREW_{base}_{key}"):
                        removed.append(f"SOCK_CREW_{base}_{key}")
    for tag in ("S", "P"):                                   # iki aşamalı yeniden adlandırma
        for old in KEEP:
            base = f"LOWER_{tag}_{old:02d}"
            for pre in ("MOD_PORT_LID_", "SOCKET_PORT_LID_", "SOCKET_CANNON_"):
                o = bpy.data.objects.get(pre + base)
                if o:
                    o.name = "_tmp_" + o.name
            for key in "ABCD":
                o = bpy.data.objects.get(f"SOCK_CREW_{base}_{key}")
                if o:
                    o.name = "_tmp_" + o.name
    for tag in ("S", "P"):
        for old in KEEP:
            ob, nb = f"LOWER_{tag}_{old:02d}", f"LOWER_{tag}_{new_idx[old]:02d}"
            for pre in ("MOD_PORT_LID_", "SOCKET_PORT_LID_", "SOCKET_CANNON_"):
                o = bpy.data.objects.get("_tmp_" + pre + ob)
                if o:
                    o.name = pre + nb
                    renamed.append(o.name)
            for key in "ABCD":
                o = bpy.data.objects.get(f"_tmp_SOCK_CREW_{ob}_{key}")
                if o:
                    o.name = f"SOCK_CREW_{nb}_{key}"
                    o["gun_socket"] = f"SOCKET_CANNON_{nb}"
            g = bpy.data.objects.get(f"SOCKET_CANNON_{nb}")
            if g:
                g["slot"] = f"SLOT_CANNON_{nb}"
                g["port_lid"] = f"MOD_PORT_LID_{nb}"
                g["upgrade"] = "lower_deck_battery_limited"
                g["upgrade_max_guns"] = 6
            lid = bpy.data.objects.get(f"MOD_PORT_LID_{nb}")
            if lid:
                lid["socket"] = f"SOCKET_PORT_LID_{nb}"
            ls = bpy.data.objects.get(f"SOCKET_PORT_LID_{nb}")
            if ls:
                ls["gun_socket"] = f"SOCKET_CANNON_{nb}"
    return removed, renamed


def fire_groups():
    n = 0
    for o in bpy.data.objects:
        if o.type == "EMPTY" and o.name.startswith("SOCKET_CANNON_") and "CHASE" not in o.name:
            side = "STARBOARD" if o.location.y > 0 else "PORT"
            o["fire_group"] = f"BROADSIDE_{side}"
            o["fire_level"] = "lower" if "LOWER" in o.name else "upper"
            o["manifest_version"] = MANIFEST_VERSION
            n += 1
    st = bpy.data.objects.get("SOCK_STATION_LOWER_BATTERY_OFFICER")
    if st:
        st["note"] = "alt güverte 3+3 top yükseltmesi alındığında aktif"
        st["manifest_version"] = MANIFEST_VERSION
    return n


# --- 3) Merdivenler ---------------------------------------------------------------------------------
def stair_params(ob):
    """Basamak üst yüzlerinden p0 (alt uç), p1 (üst uç), genişlik, basamak sayısı (dünya)."""
    me = ob.data
    mw = ob.matrix_world
    tops = []
    for p in me.polygons:
        if p.material_index != 0:
            continue
        n = (mw.to_3x3() @ p.normal).normalized()
        if n.z > 0.9:
            tops.append((mw @ p.center, p))
    tops.sort(key=lambda t: t[0].z)
    groups = []
    for c, p in tops:
        if groups and abs(groups[-1][0][0].z - c.z) < 0.03:
            groups[-1].append((c, p))
        else:
            groups.append([(c, p)])
    centers = []
    widths = []
    for g in groups:
        c = sum((x[0] for x in g), V()) / len(g)
        vs = [mw @ me.vertices[i].co for x in g for i in x[1].vertices]
        centers.append(c)
        widths.append(max(v.y for v in vs) - min(v.y for v in vs))
    n = len(centers)
    c1, cn = centers[0], centers[-1]
    rise = (cn.z - c1.z) / (n - 1)
    u = V((cn.x - c1.x, cn.y - c1.y, 0.0))
    tread = u.length / (n - 1)
    u.normalize()
    p0 = V((c1.x, c1.y, c1.z - rise)) - u * (tread / 2)
    p1 = V((cn.x, cn.y, cn.z)) + u * (tread / 2)
    return p0, p1, max(widths) + 0.04, n


def stair_clipped(bms, p0, p1, width, n, k=1.0):
    """P8.stair ile aynı biçim; yan kirişler taban ve üst güverte düzlemlerinde kırpılır (güverteye/koaminge girmez)."""
    bt, bs, bh = bms
    d = p1 - p0
    u = V((d.x, d.y, 0.0))
    run = u.length
    u.normalize()
    w = V((-u.y, u.x, 0.0))
    rise, tread = d.z / n, run / n
    hw = width / 2 - 0.02 * k
    for i in range(1, n + 1):
        a = p0 + u * (tread * (i - 1) - 0.03 * k)
        b = p0 + u * (tread * i)
        z = p0.z + rise * i
        c = [V((q.x, q.y, z - 0.05 * k)) for q in (a - w * hw, b - w * hw, b + w * hw, a + w * hw)]
        c += [V((q.x, q.y, z)) for q in (a - w * hw, b - w * hw, b + w * hw, a + w * hw)]
        P5.box8(bt, c)
    tan = d.z / run
    h = 0.30 * k / math.cos(math.atan(tan))
    for side in (-1, 1):                                    # kiriş: (mesafe, yükseklik) çokgeni, kırpılmış
        o = w * side * (width / 2 - 0.03 * k)
        top = lambda s: p0.z + s * tan + 0.02 * k          # noqa: E731
        zf = p0.z + 0.06 * k                                 # ayak: kamburluk ve sheer yüzünden güverteye gömülmesin
        s_a = (zf - p0.z + h - 0.02 * k) / tan
        s_e = run - 0.14 * k                                 # üst uç: kasara/güverte alın kirişine değmesin
        poly = [(0.0, zf), (s_a, zf), (s_e, top(s_e) - h), (s_e, top(s_e)), (0.0, max(top(0.0), zf + 0.02 * k))]
        pts = [p0 + u * s + o for s, _ in poly]
        ring0 = [bs.verts.new(V((p.x, p.y, z))) for p, (_, z) in zip(pts, poly)]
        ring1 = [bs.verts.new(v.co + w * 0.06 * k * side) for v in ring0]
        bs.faces.new(ring0)
        bs.faces.new(list(reversed(ring1)))
        m = len(ring0)
        for j in range(m):
            bs.faces.new([ring0[j], ring0[(j + 1) % m], ring1[(j + 1) % m], ring1[j]])
    hr = 0.95 * k
    posts = [p0 + u * (0.05 * k) + V((0, 0, rise)), p1 - u * (0.10 * k)]
    for side in (-1, 1):
        o = w * side * (width / 2 - 0.03 * k)
        for p in posts:
            q = p + o
            P5.aabox(bh, q.x - 0.05 * k, q.x + 0.05 * k, q.y - 0.05 * k, q.y + 0.05 * k, q.z, q.z + hr + 0.08 * k)
        for j in range(1, 5):
            q = posts[0].lerp(posts[1], j / 5) + o
            P5.aabox(bh, q.x - 0.02 * k, q.x + 0.02 * k, q.y - 0.02 * k, q.y + 0.02 * k, q.z, q.z + hr)
        a = posts[0] + o + V((0, 0, hr))
        b = posts[1] + o + V((0, 0, hr))
        dd = (b - a).normalized()
        pp = dd.cross(w).normalized() * 0.04 * k
        c = [a - w * 0.04 * k - pp, b - w * 0.04 * k - pp, b + w * 0.04 * k - pp, a + w * 0.04 * k - pp]
        c += [q + pp * 2 for q in c]
        P5.box8(bh, c)


def rebuild_stairs(core, M):
    out = []
    for name in STAIRS:
        ob = bpy.data.objects.get(name)
        if ob is None:
            continue
        p0, p1, width, n = stair_params(ob)
        bms = (bmesh.new(), bmesh.new(), bmesh.new())
        stair_clipped(bms, p0, p1, width, n, k=K)
        merged = bmesh.new()
        for idx, b in enumerate(bms):
            me = bpy.data.meshes.new("_tmp")
            bmesh.ops.recalc_face_normals(b, faces=b.faces)
            b.to_mesh(me)
            b.free()
            me.polygons.foreach_set("material_index", [idx] * len(me.polygons))
            merged.from_mesh(me)
            bpy.data.meshes.remove(me)
        new = P5.finish("_tmp_stair", merged, core, [M["deck"], M["timber"], M["yellow"]], bevel=0.008)
        old_me = ob.data
        ob.data = new.data
        ob.data.name = name
        ob.matrix_world = Matrix.Identity(4)
        mods = [m for m in new.modifiers]
        ob.modifiers.clear()
        bv = ob.modifiers.new("Bevel", "BEVEL")
        bv.width = 0.008
        bv.segments = 2
        bv.limit_method = "ANGLE"
        bpy.data.objects.remove(new, do_unlink=True)
        if old_me.users == 0:
            bpy.data.meshes.remove(old_me)
        ang = math.degrees(math.atan2(p1.z - p0.z, (V((p1.x, p1.y, 0)) - V((p0.x, p0.y, 0))).length))
        out.append({"stair": name, "steps": n, "angle_deg": round(ang, 1), "bottom": [round(v, 2) for v in p0], "top": [round(v, 2) for v in p1]})
    return out


def overlaps(names, exclude_prefix=("UCX_", "CUT_")):
    dg = bpy.context.evaluated_depsgraph_get()

    def bvh(o):
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        t = BVHTree.FromPolygons([o.matrix_world @ v.co for v in me.vertices], [tuple(p.vertices) for p in me.polygons])
        ev.to_mesh_clear()
        return t
    others = [o for o in bpy.data.objects if o.type == "MESH" and not o.hide_render and not o.name.startswith(exclude_prefix)
              and o.name not in names and o.name.startswith(("CORE_", "MOD_"))]
    res = []
    trees = {o.name: bvh(o) for o in others}
    for n in names:
        o = bpy.data.objects.get(n)
        if not o:
            continue
        t = bvh(o)
        for m, tm in trees.items():
            k = len(t.overlap(tm))
            if k:
                res.append({"stair": n, "with": m, "pairs": k})
    return res


# --- 4) Türev parçalar -------------------------------------------------------------------------------
def rebuild_derived(core, M):
    for n in ("CORE_KNEES_LOWER_DECK", "CORE_RING_BOLTS", "MOD_CANNON_BREECHING_S_A", "MOD_CANNON_BREECHING_P_A"):
        remove_obj(n)
    knees, placed, skipped = P18.build_knees(core, M)
    obs, n_b, n_r = P18.build_bolts_and_breeching(core, None, M)
    lods = bpy.data.collections["50_LODS"]
    for o in list(lods.objects):
        me = o.data
        bpy.data.objects.remove(o, do_unlink=True)
        if me.users == 0:
            bpy.data.meshes.remove(me)
    return {"knees": 2 * len(placed), "ring_bolts": n_b, "breeching": n_r}


def render(sc):
    H.setup_render(sc, fast=True)
    out = ROOT / "renders" / VER
    out.mkdir(parents=True, exist_ok=True)
    for o in bpy.data.objects:
        if o.name.startswith(("SOCK_LANTERN_LOWER_", "SOCK_LANTERN_HOLD_")):
            lamp = bpy.data.lights.new(o.name + "_L", "POINT")
            lamp.energy = 700
            lamp.color = (1.0, 0.72, 0.45)
            lo = bpy.data.objects.new("LGT_" + o.name, lamp)
            lo.location = o.location + V((0, 0, -0.2))
            sc.collection.objects.link(lo)
    fill = bpy.data.lights.new("Fill", "AREA")
    fill.energy = 900
    fill.size = 14
    fo = bpy.data.objects.new("LGT_Fill", fill)
    fo.location = V((0, 0, 2.6))
    sc.collection.objects.link(fo)
    views = [
        ("iskele_profil", V((1.5, -85, 4.2)), V((1.5, 0, 4.2)), None, 52),
        ("ambar_agzi_ust", V((-4.2, 2.4, 5.6)), V((-6.6, 0, 3.3)), 30, None),
        ("merdiven_alt", V((-3.2, 2.2, 1.9)), V((-6.6, 0, 2.4)), 24, None),
        ("baskasarasi_merdiven", V((9.0, 5.0, 5.2)), V((12.6, 2.9, 4.2)), 28, None),
        ("alt_guverte", V((-9.5, 0.4, 2.55)), V((8.0, -0.3, 1.8)), 16, None),
    ]
    for name, loc, tgt, lens, osc in views:
        cam = H.camera(sc, f"CAM27_{name}", loc, tgt, ortho=osc, lens=lens or 50)
        sc.camera = cam
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
    M = P18.P17.mats()
    core = bpy.data.collections["10_HULL_CORE"]
    before = overlaps(STAIRS)
    # v016'da güverte mesh'i yenilenince EXACT boolean sessizce başarısız oldu → ambar ağızları kapalıydı. FLOAT çözücü.
    solver_fix = []
    for dn, mn in (("CORE_DECK_GUN", "Hatches"), ("CORE_DECK_LOWER", "HatchHold")):
        m = bpy.data.objects[dn].modifiers.get(mn)
        if m:
            m.solver = "FLOAT"
            solver_fix.append(f"{dn}.{mn}")
    removed, renamed = rebuild_lower_ports(core, M)
    n_fg = fire_groups()
    stairs = rebuild_stairs(core, M)
    derived = rebuild_derived(core, M)
    bpy.context.view_layer.update()
    after = overlaps(STAIRS)
    lower = sorted(o.name for o in bpy.data.objects if o.type == "EMPTY" and o.name.startswith("SOCKET_CANNON_LOWER_"))
    lx = sorted({round(bpy.data.objects[n].location.x, 2) for n in lower})
    upper_x = sorted({round(o.location.x, 2) for o in bpy.data.objects if o.type == "EMPTY" and o.name.startswith("SOCKET_CANNON_S_")})
    dg = bpy.context.evaluated_depsgraph_get()
    hatch_check = {}
    for nm, x, z0 in (("aft", -6.6, 5.0), ("main_grating", -1.6, 5.0), ("fore", 7.2, 5.0), ("hold", -1.6, 2.4)):
        ok, loc, _, _, ob, _ = sc.ray_cast(dg, V((x, 0.1, z0)), V((0, 0, -1)), distance=2.2)
        hatch_check[nm] = ob.name if ok else "açık (isabet yok)"
    report_lods = P26.build_lods(sc)
    bpy.ops.wm.save_as_mainfile(filepath=str(out), compress=True)
    H.VERSION = VER
    ap = ROOT / "reports" / f"scene_audit_{VER}.json"
    rep = H.audit(sc, ap)
    rep["v027"] = {
        "lower_battery": {"guns": len(lower), "x_world": lx, "mean_x": round(sum(lx) / len(lx), 3),
                          "upper_battery_mean_x": round(sum(upper_x) / len(upper_x), 3),
                          "stagger_to_nearest_upper_m": [round(min(abs(x - u) for u in upper_x), 2) for x in lx],
                          "removed": len(removed), "renamed": renamed},
        "fire_groups_set": n_fg, "stairs": stairs,
        "stair_overlaps_before": before, "stair_overlaps_after": after,
        "derived": derived, "lods_rebuilt": len(report_lods), "boolean_solver_fix": solver_fix,
        "hatch_open_check": hatch_check,
    }
    rep["pass"] = {"name": "pass_v027_frigate_lower_stairs", "source": f"Blender/versions/{SHIP}_{SRC_VER}.blend",
                   "manifest_version": MANIFEST_VERSION,
                   "geometry_changed": "alt lumbarlar 10+10 → 3+3; merdiven kirişleri kırpıldı; dirsek/cıvata/LOD yenilendi"}
    ap.write_text(json.dumps(rep, indent=2, ensure_ascii=False), encoding="utf-8")
    r = rep["v027"]
    print("LOWER", r["lower_battery"]["x_world"], r["lower_battery"]["mean_x"], r["lower_battery"]["upper_battery_mean_x"],
          r["lower_battery"]["stagger_to_nearest_upper_m"], "removed", r["lower_battery"]["removed"])
    print("OVERLAP before", len(before), "after", after)
    print("DERIVED", derived, "LODS", r["lods_rebuilt"], "HATCH", hatch_check)
    if "--no-render" not in sys.argv:
        render(sc)


if __name__ == "__main__":
    main()
