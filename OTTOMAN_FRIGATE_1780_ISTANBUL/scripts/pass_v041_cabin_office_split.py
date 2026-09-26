"""v041 — Kızıl Sancak iç düzeni 1: kıç kamarası → CaptainOffice (makam) + kaptan kamarası + çırak rıhtımı.

    python3.11 OTTOMAN_FRIGATE_1780_ISTANBUL/scripts/pass_v041_cabin_office_split.py [--no-render | --render-only]

Onaylı plan: reports/KIZIL_SANCAK_UYARLAMA_PLANI.md §4 (Gate A). Kaynak kurallar (kullanıcı tasarım paketi, Ek Cilt II):
- s. 98 "Kaptan kamarası ve CaptainOffice ayrımı": kaptan kamarası (yaşam) ile makam ayrı alanlardır; "kaptan
  kamarası makam alanıdır, kişisel miras değildir".
- s. 99 "Vasiyet Yolcusu için junior yaşam alanı": genç CharacterID junior yolcu / çırak rıhtımı kullanır.
- s. 81 oda kimlikleri: CompartmentID ≠ RoomLabel ≠ OperationalStationID ≠ WatertightZoneID.
Yerleşim (kıç kasarası altı, x −20,6…−15,3 m):
- Makam: kıç pencereli büyük kamara (x < −16,55). Toplantı/harita masası yerinde; çalışma masası ve büfe ön
  bölmelerin arka yüzüne taşınır; sancak (duvar), ferman kutusu, yazı rafı (göz göz), mühür kutusu eklenir.
- Kaptan kamarası (iskele-ön, 1,2 × 2,3 m): asma yatak + sandık yerinde; lavabo dolabı, kitap rafı, askı.
- Çırak rıhtımı (sancak-ön): dar ranza, deniz sandığı, ders/harita tahtası.
- Bölmeler: kızıl boyalı tahta + altın kuşak, kapılı (çarpışmaya hazır: savaşta sökülebilir işaretli). Kıç topları
  (x −18,8, y ±2,1) makamda kalır — dönemin gerçeği (kamara topları); mürettebat soketleri bölmenin arkasında.
- Ad levhası (v040): 4 cm aşağı (harf üstü pencere pervazına giriyordu).
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
sp = importlib.util.spec_from_file_location("pass_v033", HERE / "pass_v033_facet_cleanup.py")
P33 = importlib.util.module_from_spec(sp)
sp.loader.exec_module(P33)
P31 = P33.P31
RS, QA, LODS, H = P31.RS, P31.QA, P31.LODS, P31.H
ROOT, SHIP = P31.ROOT, P31.SHIP
SRC_VER, VER = "v040", "v041"
V = Vector
sys.path.insert(0, str(HERE))
import interior_kit as IK  # noqa: E402

IK.RS = RS
X_PART = -16.55          # enine bölme (yan kabinlerin arka yüzü)
X_BULK = -15.36          # kıç kasarası ön bölmesi (içeri yüz)
Y_PASS = 1.10            # koridor yarı eni
DOOR = (0.0, 0.62, 1.78)


def mw(o):
    return o.matrix_basis.copy() if o.parent is None else o.matrix_world.copy()


def bvh(names):
    dg = bpy.context.evaluated_depsgraph_get()
    vs, fs = [], []
    for n in names:
        o = bpy.data.objects[n]
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        M = mw(o)
        base = len(vs)
        vs += [M @ v.co for v in me.vertices]
        fs += [tuple(base + i for i in p.vertices) for p in me.polygons]
        ev.to_mesh_clear()
    return BVHTree.FromPolygons(vs, fs)


FLOOR = CEIL = HULL = None


def floor_z(x, y):
    hit = FLOOR.ray_cast(V((x, y, 6.0)), V((0, 0, -1)), 4.0)
    return hit[0].z if hit[0] is not None else 3.9


def ceil_z(x, y):
    hit = CEIL.ray_cast(V((x, y, 4.5)), V((0, 0, 1)), 4.0)
    return hit[0].z if hit[0] is not None else 6.25


def hull_y(x, z, s):
    hit = HULL.ray_cast(V((x, 0.0, z)), V((0, s, 0)), 8.0)
    return abs(hit[0].y) if hit[0] is not None else 3.5


def move(name, dx, dy, rot=None):
    """Nesneyi ve aynı adlı soketini taşır; taban eğimi (sheer) için Z düzeltmesi."""
    out = []
    for n in (name, "SOCK_INTERIOR_" + name.replace("MOD_CABIN_", "")):
        o = bpy.data.objects.get(n)
        if not o:
            continue
        p = mw(o).translation
        dz = floor_z(p.x + dx, p.y + dy) - floor_z(p.x, p.y)
        o.location = o.location + V((dx, dy, dz))
        if rot is not None:
            o.rotation_euler.z += rot
        out.append(n)
    for o in [o for o in bpy.data.objects if o.name.startswith(name + "_LOD")]:
        o.location = bpy.data.objects[name].location.copy()
        o.rotation_euler = bpy.data.objects[name].rotation_euler.copy()
    return out


def partitions(M, col):
    bm = bmesh.new()
    rep = {}
    for s in (1, -1):
        z0 = floor_z(X_PART, s * 2.2)
        z1 = ceil_z(X_PART, s * 2.2) - 0.01
        yh = hull_y(X_PART + 0.3, (z0 + z1) / 2, s) - 0.02
        # enine: koridordan bordaya
        IK.plank_partition(bm, (X_PART, s * Y_PASS), (X_PART, s * yh), z0, z1, mat=0, trim_mat=1)
        # boyuna: bölmeden kıç kasarası duvarına, kapılı
        zb = floor_z((X_PART + X_BULK) / 2, s * Y_PASS)
        L = X_BULK - X_PART
        IK.plank_partition(bm, (X_PART, s * Y_PASS), (X_BULK, s * Y_PASS), zb, z1, mat=0, trim_mat=1,
                           door=(L / 2, DOOR[1], DOOR[2]))
        rep["P" if s < 0 else "S"] = {"hull_y": round(yh, 2), "z": [round(z0, 2), round(z1, 2)]}
    ob = IK.finish("MOD_CABIN_PARTITIONS_A", bm, [M["red"], M["gilt"]], col,
                   {"room": "captain_quarters", "clear_for_action": "sökülebilir (savaş hazırlığında kaldırılır)",
                    "note": "Ek Cilt II s. 98: kaptan kamarası ile CaptainOffice ayrı fiziksel alanlardır"})
    # çarpışma: her bölme için ince kutu UCX
    geom = __import__("geom")
    ucol = bpy.data.collections["40_COLLISION"]
    k = 0
    for s in (1, -1):
        z0, z1 = floor_z(X_PART, s * 2.2), ceil_z(X_PART, s * 2.2)
        yh = rep["P" if s < 0 else "S"]["hull_y"]
        for (x0, x1, y0, y1) in ((X_PART - 0.03, X_PART + 0.03, s * Y_PASS, s * yh),
                                 (X_PART, X_PART + 0.28, s * Y_PASS - 0.03, s * Y_PASS + 0.03),
                                 (X_BULK - 0.28, X_BULK, s * Y_PASS - 0.03, s * Y_PASS + 0.03)):
            pts = [V((x, y, z)) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)]
            geom.convex_ucx(f"UCX_MOD_CABIN_PARTITIONS_A_{k:02d}", pts, ucol, "wall", owner=ob.name)
            k += 1
    rep["ucx"] = k
    return ob, rep


def office_props(M, col):
    """Makam: sancak (duvar), yazı rafı, ferman kutusu, mühür kutusu."""
    rep = {}
    # yazı rafı (göz göz) — sancak tarafı bölmenin arka yüzünde, çalışma masasının üstünde
    bm = bmesh.new()
    x = X_PART - 0.04 - 0.14
    zc = floor_z(x, 2.75) + 1.55
    IK.box(bm, (x, 2.75, zc), (0.28, 1.10, 0.62), r=0.01, mat=0)
    for i in range(4):
        for j in range(3):
            IK.box(bm, (x - 0.13, 2.75 - 0.41 + i * 0.275, zc - 0.2 + j * 0.2), (0.05, 0.24, 0.17), r=0.006, mat=1)   # göz içi (koyu)
            IK.box(bm, (x - 0.16, 2.75 - 0.41 + i * 0.275, zc - 0.2 + j * 0.2 - 0.02), (0.02, 0.16, 0.10), r=0.003, mat=2)  # rulo/yazı
    IK.finish("MOD_OFFICE_LETTER_RACK_A", bm, [M["wood"], M["dark"], M["paper"]], col,
              {"room": "captain_office", "interact": "orders_and_letters", "socket": "SOCK_INTERIOR_LETTER_RACK_A"})
    # ferman kutusu (altın işlemeli) + mühür kutusu — çalışma masası üstünde
    desk = bpy.data.objects["MOD_CABIN_DESK_A"]
    dws = [mw(desk) @ v.co for v in desk.data.vertices]
    dc = sum(dws, V()) / len(dws)
    dt = BVHTree.FromPolygons(dws, [tuple(p.vertices) for p in desk.data.polygons])

    def dtop_at(x, y):
        hit = dt.ray_cast(V((x, y, dc.z + 2.0)), V((0, 0, -1)), 4.0)
        return hit[0].z if hit[0] is not None else dc.z
    dtop = dtop_at(dc.x, dc.y - 0.30)
    bm = bmesh.new()
    IK.box(bm, (dc.x, dc.y - 0.30, dtop + 0.06), (0.22, 0.40, 0.12), r=0.012, mat=0)
    IK.box(bm, (dc.x, dc.y - 0.30, dtop + 0.125), (0.23, 0.41, 0.012), r=0.004, mat=1)
    IK.lathe(bm, [(0.0, 0.0), (0.045, 0.0), (0.045, 0.05), (0.03, 0.06), (0.0, 0.065)], V((dc.x - 0.02, dc.y + 0.28, dtop_at(dc.x - 0.02, dc.y + 0.28))), mat=1)
    IK.finish("MOD_OFFICE_FERMAN_BOX_A", bm, [M["red_velvet"], M["gilt"]], col,
              {"room": "captain_office", "interact": "ferman_and_seals",
               "note": "Kızıl Deniz Meclisi fermanları ve mühürleri (makamın malı; kaptanın kişisel mirası değil)"})
    # sancak: iskele bölmesinin arka yüzünde asılı (Kızıl Sancak dokusu)
    x = X_PART - 0.05
    z0 = floor_z(x, -2.3)
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    W, Hh = 1.50, 1.00
    rows, cols = 10, 16
    grid = []
    for i in range(rows + 1):
        v = i / rows
        row = []
        for j in range(cols + 1):
            u = j / cols
            y = -2.3 + (u - 0.5) * W
            z = z0 + 1.35 + v * Hh
            row.append((bm.verts.new(V((x - 0.012 * math.sin(math.pi * u * 3) * (1 - v), y, z))), (u, v)))
        grid.append(row)
    for i in range(rows):
        for j in range(cols):
            q = [grid[i][j], grid[i][j + 1], grid[i + 1][j + 1], grid[i + 1][j]]
            f = bm.faces.new([a[0] for a in q])
            f.smooth = True
            for lp, a in zip(f.loops, q):
                lp[uvl].uv = a[1]
    IK.cyl(bm, (x - 0.03, -2.3 - W / 2 - 0.08, z0 + 1.35 + Hh + 0.02), (x - 0.03, -2.3 + W / 2 + 0.08, z0 + 1.35 + Hh + 0.02), 0.015, mat=1)
    for s in (-1, 1):
        IK.lathe(bm, [(0.0, 0.0), (0.028, 0.0), (0.03, 0.02), (0.0, 0.05)], V((x - 0.03, -2.3 + s * (W / 2 + 0.10), z0 + 1.35 + Hh + 0.02)),
                 (0, s, 0), mat=1)
    IK.finish("MOD_OFFICE_BANNER_A", bm, [bpy.data.materials["MAT_Flag_KizilSancak_A"], M["gilt"]], col,
              {"room": "captain_office", "design": "Kızıl Sancak (makam sancağı)", "socket": "SOCK_INTERIOR_BANNER_A"})
    rep["office_props"] = ["MOD_OFFICE_LETTER_RACK_A", "MOD_OFFICE_FERMAN_BOX_A", "MOD_OFFICE_BANNER_A"]
    return rep


def captain_cabin_props(M, col):
    """Kaptan kamarası (iskele-ön): lavabo dolabı, kitap rafı, askı."""
    bm = bmesh.new()
    x = X_BULK - 0.24
    y = -Y_PASS - 0.30
    z0 = floor_z(x, y)
    IK.box(bm, (x, y, z0 + 0.42), (0.44, 0.46, 0.84), r=0.012, mat=0)                      # dolap
    basin = [(0.0, 0.0)] + [(0.10 + 0.08 * math.sin(math.pi / 2 * t), 0.065 * (1 - math.cos(math.pi / 2 * t))) for t in [i / 10 for i in range(11)]] \
        + [(0.176, 0.066)] + [(0.17 - 0.07 * t, 0.058 - 0.046 * t) for t in [i / 6 for i in range(1, 7)]] + [(0.0, 0.012)]
    IK.lathe(bm, basin, V((x, y, z0 + 0.84)), mat=1)   # pirinç leğen (sık profil)
    ibrik = [(0.0, 0.0)] + [(0.05 + 0.012 * math.sin(math.pi * t), 0.16 * t) for t in [i / 12 for i in range(13)]] + [(0.042, 0.19), (0.0, 0.2)]
    IK.lathe(bm, ibrik, V((x + 0.08, y + 0.14, z0 + 0.84)), mat=1)  # ibrik
    # kitap rafı (bordaya)
    zr = z0 + 1.55
    IK.box(bm, (X_BULK - 0.16, -2.85, zr), (0.26, 0.9, 0.03), r=0.006, mat=0)
    for k in range(9):
        h = 0.20 + 0.04 * ((k * 7) % 3)
        IK.box(bm, (X_BULK - 0.16, -3.2 + k * 0.08, zr + 0.015 + h / 2), (0.18, 0.06, h), r=0.006, mat=2 if k % 2 else 3)
    # askı
    for k in range(3):
        IK.tube(bm, [(X_PART + 0.03, -1.35 - k * 0.25, z0 + 1.7), (X_PART + 0.09, -1.35 - k * 0.25, z0 + 1.72),
                     (X_PART + 0.11, -1.35 - k * 0.25, z0 + 1.80)], 0.009, mat=1)
    IK.finish("MOD_CABIN_WASHSTAND_SHELF_A", bm, [M["wood"], M["brass"], M["leather_red"], M["leather_dark"]], col,
              {"room": "captain_cabin", "interact": "rest"})


def junior_berth(M, col):
    """Çırak / junior rıhtımı (sancak-ön): dar ranza, deniz sandığı, ders tahtası."""
    bm = bmesh.new()
    yh = 3.35
    x0, x1 = X_PART + 0.06, X_BULK - 0.02
    xc = (x0 + x1) / 2
    y0 = Y_PASS + 0.75
    z0 = floor_z(xc, 2.4)
    # ranza kasası (bordaya boyuna), yatak, battaniye
    L = yh - y0 - 0.05
    yc = y0 + L / 2
    IK.box(bm, (xc, yc, z0 + 0.25), (x1 - x0, L, 0.08), r=0.012, mat=0)
    IK.box(bm, (xc, y0 + 0.02, z0 + 0.35), (x1 - x0, 0.05, 0.28), r=0.01, mat=0)
    IK.box(bm, (xc, yc, z0 + 0.34), (x1 - x0 - 0.1, L - 0.08, 0.10), r=0.04, mat=1)       # yatak
    IK.box(bm, (xc + 0.03, yc + 0.25, z0 + 0.405), (x1 - x0 - 0.12, L * 0.55, 0.035), r=0.015, mat=2)   # kızıl battaniye
    for dx in (-1, 1):
        for yy in (y0 + 0.05, yh - 0.1):
            IK.box(bm, (xc + dx * (x1 - x0) / 2 * 0.85, yy, z0 + 0.12), (0.06, 0.06, 0.24), r=0.01, mat=0)
    # deniz sandığı (ayakucu, koridor tarafı)
    IK.box(bm, (xc, Y_PASS + 0.35, z0 + 0.22), (0.62, 0.40, 0.44), r=0.02, mat=0)
    IK.box(bm, (xc, Y_PASS + 0.35, z0 + 0.45), (0.64, 0.42, 0.03), r=0.01, mat=3)
    # ders / harita tahtası (kıç kasarası duvarı)
    IK.box(bm, (X_BULK - 0.02, 2.4, z0 + 1.35), (0.025, 0.9, 0.62), r=0.006, mat=0)
    IK.box(bm, (X_BULK - 0.035, 2.4, z0 + 1.35), (0.01, 0.8, 0.52), r=0.003, mat=4)
    IK.finish("MOD_CABIN_JUNIOR_BERTH_A", bm, [M["wood"], M["canvas"], M["red_velvet"], M["iron"], M["paper"]], col,
              {"room": "junior_berth", "interact": "rest_study", "socket": "SOCK_INTERIOR_JUNIOR_BERTH_A",
               "note": "Ek Cilt II s. 99: genç CharacterID (Vasiyet Yolcusu) junior/çırak rıhtımı kullanır"})


def rooms(col):
    zf = floor_z(-18.0, 0.0)
    zc = ceil_z(-18.0, 0.0)
    out = []
    out.append(IK.room("ROOM_CAPTAIN_OFFICE", (-20.25, -3.45, zf), (X_PART - 0.03, 3.45, zc), col,
                       "CMP_POOP_AFT_01", "Kaptan Makamı (CaptainOffice)", "STN_CAPTAIN_OFFICE", "WTZ_AFT_UPPER", "gun_deck_poop",
                       {"authority": "makam — kaptanlık görevine bağlı, kişisel miras değil (Ek Cilt II s. 98)",
                        "contains": "harita/toplantı masası, çalışma masası, yazı rafı, ferman kutusu, sancak, kıç topları"}).name)
    out.append(IK.room("ROOM_CAPTAIN_CABIN", (X_PART, -3.45, zf), (X_BULK, -Y_PASS, zc), col,
                       "CMP_POOP_AFT_02P", "Kaptan Kamarası (yaşam)", "STN_CAPTAIN_REST", "WTZ_AFT_UPPER", "gun_deck_poop",
                       {"contains": "asma yatak, sandık, lavabo dolabı, kitap rafı"}).name)
    out.append(IK.room("ROOM_JUNIOR_BERTH", (X_PART, Y_PASS, zf), (X_BULK, 3.45, zc), col,
                       "CMP_POOP_AFT_02S", "Çırak / Junior Rıhtımı", "STN_JUNIOR_BERTH", "WTZ_AFT_UPPER", "gun_deck_poop",
                       {"character_rule": "genç CharacterID (Vasiyet Yolcusu) — Ek Cilt II s. 99"}).name)
    out.append(IK.room("ROOM_CABIN_PASSAGE", (X_PART, -Y_PASS, zf), (X_BULK, Y_PASS, zc), col,
                       "CMP_POOP_AFT_03", "Kamara Koridoru", "STN_NONE", "WTZ_AFT_UPPER", "gun_deck_poop").name)
    return out


def mats():
    M = {"red": bpy.data.materials["MAT_Bulwark_InnerRed"], "gilt": bpy.data.materials["MAT_Trim_Gilt"],
         "wood": bpy.data.materials["MAT_Furniture_Mahogany"], "paper": bpy.data.materials["MAT_Paper_Chart"],
         "brass": bpy.data.materials["MAT_Brass"], "canvas": bpy.data.materials["MAT_Canvas"],
         "iron": bpy.data.materials["MAT_Iron_Black"], "red_velvet": bpy.data.materials["MAT_Orn_Velvet_Crimson"]}
    M["dark"] = IK.mat("MAT_Wood_DarkStain", (0.035, 0.022, 0.015), 0.6)
    M["red"] = IK.mat("MAT_Panel_KizilLacquer", (0.32, 0.045, 0.035), 0.42)          # Kızıl Sancak kızıl cila (konsept paleti)
    M["canvas"] = IK.mat("MAT_Linen_Mattress", (0.62, 0.56, 0.45), 0.8)
    M["leather_red"] = IK.mat("MAT_Leather_Crimson", (0.28, 0.03, 0.025), 0.55)
    M["leather_dark"] = IK.mat("MAT_Leather_Dark", (0.06, 0.035, 0.02), 0.5)
    return M


def render(sc):
    H.setup_render(sc, fast=True)
    sc.cycles.samples = 32
    out = ROOT / "renders" / VER
    out.mkdir(parents=True, exist_ok=True)
    # yalnız render (kayda geçmez): kamara üstündeki her şeyi gizle — süsleme/yelken sürücüleri önce kaldırılır
    for o in bpy.data.objects:
        if o.type != "MESH":
            continue
        ws = [o.matrix_world @ V(c) for c in o.bound_box]
        hide = (min(w.z for w in ws) > 6.2 and max(w.x for w in ws) < -8.0) or o.name in (
            "CORE_DECK_POOP", "MOD_ORN_CABIN_CEILING", "CORE_POOP_BALUSTRADE", "MOD_STERN_GALLERY_A", "CORE_DECK_BEAMS_UPPER") \
            or o.name.startswith(("MOD_SAIL_", "MOD_RIG_", "MOD_LANTERN_STERN", "MOD_FLAG_"))
        if hide:
            if o.animation_data:
                for fc in list(o.animation_data.drivers):
                    o.animation_data.drivers.remove(fc)
            o.hide_render = True
    for name, loc, energy in (("L_OFIS", (-18.0, 0.0, 5.8), 260), ("L_KAMARA", (-15.95, -2.3, 5.8), 60), ("L_CIRAK", (-15.95, 2.3, 5.8), 60)):
        lt = bpy.data.objects.new(name, bpy.data.lights.new(name, "POINT"))
        lt.data.energy, lt.data.shadow_soft_size = energy, 0.3
        lt.data.color = (1.0, 0.82, 0.6)
        lt.location = loc
        sc.collection.objects.link(lt)
    shots = (("kamara_ust", V((-17.4, 0.0, 12.5)), V((-17.6, 0.0, 4.0)), 28),
             ("makam", V((-16.2, -0.6, 5.6)), V((-19.5, 0.9, 4.6)), 22),
             ("ciraK_rihtimi", V((-15.95, -0.9, 5.25)), V((-15.95, 2.9, 4.35)), 24))
    for name, loc, tgt, lens in shots:
        sc.camera = H.camera(sc, f"CAM41_{name}", loc, tgt, lens=lens)
        sc.render.filepath = str(out / f"{SHIP}_{VER}_{name.lower()}.png")
        bpy.ops.render.render(write_still=True)


def main():
    global FLOOR, CEIL, HULL
    if "--render-only" in sys.argv:
        bpy.ops.wm.open_mainfile(filepath=str(ROOT / "Blender" / "versions" / f"{SHIP}_{VER}.blend"))
        return render(bpy.context.scene)
    out = ROOT / "Blender" / "versions" / f"{SHIP}_{VER}.blend"
    if out.exists():
        raise SystemExit(f"{out} zaten var; versiyonlu kayıt üzerine yazılmaz.")
    bpy.ops.wm.open_mainfile(filepath=str(ROOT / "Blender" / "versions" / f"{SHIP}_{SRC_VER}.blend"))
    sc = bpy.context.scene
    bpy.context.view_layer.update()
    FLOOR = bvh(["CORE_DECK_GUN"])
    CEIL = bvh(["CORE_DECK_POOP", "MOD_ORN_CABIN_CEILING"])
    HULL = bvh(["CORE_HULL_SHELL"])
    col = bpy.data.collections["24_MODULES_DECOR"]
    rcol = IK.ensure_col("35_ROOMS")
    M = mats()
    rep = {}
    # ad levhası düzeltmesi
    nb = bpy.data.objects["MOD_ORN_STERN_NAMEBOARD"]
    nb.location.z -= 0.04
    for o in [o for o in bpy.data.objects if o.name.startswith("MOD_ORN_STERN_NAMEBOARD_LOD")]:
        o.location.z -= 0.04
    # eşyaları makama taşı
    rep["moved"] = {"desk": move("MOD_CABIN_DESK_A", X_PART - 0.03 - (-15.44), 0.0),
                    "desk_chair": move("MOD_CABIN_CHAIR_A_DESK", X_PART - 0.03 - (-15.44), 0.0),
                    "sideboard": move("MOD_CABIN_SIDEBOARD_A", X_PART - 0.03 - (-15.41), -3.95)}
    for n in ("MOD_CABIN_DESK_A", "MOD_CABIN_CHAIR_A_DESK", "MOD_CABIN_SIDEBOARD_A", "MOD_CABIN_TABLE_A"):
        bpy.data.objects[n]["clear_for_action"] = "savaşta istiflenir (kıç topu mürettebat alanı)"
    for n, r in (("MOD_CABIN_DESK_A", "captain_office"), ("MOD_CABIN_CHAIR_A_DESK", "captain_office"), ("MOD_CABIN_SIDEBOARD_A", "captain_office"),
                 ("MOD_CABIN_TABLE_A", "captain_office"), ("MOD_CABIN_STERN_BENCH_A", "captain_office"),
                 ("MOD_CABIN_COT_A", "captain_cabin"), ("MOD_CABIN_CHEST_A_01", "captain_cabin")):
        bpy.data.objects[n]["room"] = r
    for k in range(1, 5):
        bpy.data.objects[f"MOD_CABIN_CHAIR_A_0{k}"]["room"] = "captain_office"
    ob, rep["partitions"] = partitions(M, col)
    rep.update(office_props(M, col))
    captain_cabin_props(M, col)
    junior_berth(M, col)
    rep["rooms"] = rooms(rcol)
    new = ["MOD_CABIN_PARTITIONS_A", "MOD_OFFICE_LETTER_RACK_A", "MOD_OFFICE_FERMAN_BOX_A", "MOD_OFFICE_BANNER_A",
           "MOD_CABIN_WASHSTAND_SHELF_A", "MOD_CABIN_JUNIOR_BERTH_A"]
    LODS.build_lods(sc, only=set(new))
    bpy.ops.wm.save_as_mainfile(filepath=str(out), compress=True)
    H.VERSION = VER
    ap = ROOT / "reports" / f"scene_audit_{VER}.json"
    arep = H.audit(sc, ap)
    arep["interior_v041"] = rep
    arep["pass"] = {"name": "pass_v041_cabin_office_split", "source": f"Blender/versions/{SHIP}_{SRC_VER}.blend"}
    ap.write_text(json.dumps(arep, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    qa = QA.audit(sc, top=60)
    (ROOT / "reports" / f"kalite_testi_{VER}.json").write_text(json.dumps(qa, indent=1, ensure_ascii=False), encoding="utf-8")
    print("V041", json.dumps(rep, ensure_ascii=False, default=str))
    print("V041 QA", json.dumps(qa["summary"], ensure_ascii=False))
    for r in [r for r in qa["objects"] if r["fail"] or r["floating_islands"]]:
        print(f"  HATA {r['name']} facet={r['facet_m']}m sag={r['worst_sag_mm']}mm havada={r['floating_islands'][:3]}")
    if "--no-render" not in sys.argv:
        render(sc)


if __name__ == "__main__":
    main()
