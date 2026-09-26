"""Pass v014 — CannonBattery modülü: 9 librelik top + ahşap kızak (truck carriage), v013 üzerine.

Çalıştırma (depo kökünden):
    python3 OTTOMAN_FRIGATE_1780_ISTANBUL/scripts/pass_v014_cannon_9pdr.py [--no-render | --render-only]

Kullanıcı kararı (2026-09-26): Hull_B'den sonra sırayla top modülü → direkler/arma → kamara içi.
Kaynak / tahmin:
  - HMS Lyme (1748): 24 × 9 librelik [İKİNCİL: Wikipedia/RMG, arama özeti] → modül 9 librelik.
  - 9 librelik namlu çapı 4,2 inç (0,107 m) [İKİNCİL: IMA "Original 18th Century 9-Pounder Demi Culverin",
    arama özeti].
  - Namlu boyu, kızak ölçüleri, teker çapları, muylu yüksekliği: TAHMİN (lumbar merkezine göre ayarlandı;
    lumbar merkezi dünyada güverteden (0,55 + 0,28) × 1,10 = 0,91 m).
Modül yapısı: kızak ve namlu ayrı mesh (namlu muylu ekseninde döner). Toplar yalnız varsayılan takılı
soketlere konur (20 borda + 4 kovalama); alt güverte soketleri boş kalır (yükseltme).
Soket yerel ekseni: +X namlu yönü (dışa), Z yukarı, orijin güvertede kızak merkezi.
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


P13 = _load("pass_v013", "pass_v013_hull_b_lower_deck.py")
P5, H, K = P13.P5, P13.H, P13.K
SRC_VER, VER = "v013", "v014"
ROOT, SHIP = H.ROOT, H.SHIP_ID
MANIFEST_VERSION = 12
P5.MANIFEST_VERSION = MANIFEST_VERSION

# --- Ölçüler (metre, gerçek boy; gemi ölçeğinden bağımsız) ----------------------------
BORE = 0.107               # 4,2 inç [İKİNCİL]
L_BARREL = 2.44            # taban halkasından ağıza, TAHMİN (8 ft)
TRUN_FROM_BREECH = L_BARREL * 3 / 7   # TAHMİN (dönem oranı yaklaşık)
TRUN_Z = 0.86              # muylu ekseni güverteden, TAHMİN (lumbar merkezi 0,91)
TRUN_X = 0.30              # muylu ekseni, soket orijininden ileri (dışa)
R_BREECH = 0.185
TRUN_R, TRUN_L = 0.055, 0.12
CHEEK_T, CHEEK_GAP = 0.11, 0.40   # yanak kalınlığı, iki yanak arası
CAR_X0, CAR_X1 = -0.78, 0.52      # kızak arka/ön ucu
WHEEL_R_F, WHEEL_R_R, WHEEL_W = 0.21, 0.19, 0.10
AXLE_X_F, AXLE_X_R = 0.36, -0.60
SEG = 28


def barrel_profile():
    """(yarıçap, x) — x muylu ekseninden (ileri +). Dökme demir, halka ve kuşaklarla."""
    xb = -TRUN_FROM_BREECH          # taban halkası (breech)
    xm = L_BARREL - TRUN_FROM_BREECH  # ağız
    r = R_BREECH
    pts = [
        (0.0, xb - 0.215), (0.035, xb - 0.215), (0.050, xb - 0.20), (0.055, xb - 0.175), (0.030, xb - 0.15),  # kaskabel topuzu
        (0.030, xb - 0.12), (0.075, xb - 0.10), (0.125, xb - 0.07), (0.160, xb - 0.03), (r - 0.01, xb),
        (r + 0.012, xb), (r + 0.012, xb + 0.035), (r, xb + 0.045),                                        # taban halkası
        (r - 0.010, xb + 0.35), (r - 0.002, xb + 0.36), (r - 0.002, xb + 0.39), (r - 0.012, xb + 0.40),     # 1. takviye halkası
        (r - 0.020, -0.08), (r - 0.012, -0.07), (r - 0.012, -0.04), (r - 0.030, -0.03),                    # 2. takviye başı
        (r - 0.040, 0.30), (r - 0.032, 0.31), (r - 0.032, 0.34), (r - 0.052, 0.35),                        # kovan halkası
        (r - 0.075, xm - 0.30), (r - 0.066, xm - 0.26), (r - 0.060, xm - 0.20),                            # boyun
        (r - 0.050, xm - 0.12), (r - 0.045, xm - 0.04), (r - 0.042, xm - 0.015), (r - 0.052, xm),          # ağız şişkinliği
        (BORE / 2 + 0.006, xm), (BORE / 2, xm - 0.02), (BORE / 2, xm - 0.45), (0.0, xm - 0.46),            # namlu içi
    ]
    return pts


def build_barrel(M):
    bm = bmesh.new()
    rot = Matrix.Rotation(math.radians(90), 4, "Y")    # lathe Z → X
    P5.lathe(bm, barrel_profile(), SEG, rot)
    n_body = len(bm.faces)
    for sgn in (1, -1):                                   # muylular + kök bilezikleri
        m = Matrix.Translation((0, sgn * (R_BREECH - 0.03), -0.015)) @ Matrix.Rotation(math.radians(-90 * sgn), 4, "X")
        P5.lathe(bm, [(0.0, 0.0), (TRUN_R + 0.025, 0.0), (TRUN_R + 0.025, 0.03), (TRUN_R, 0.035),
                      (TRUN_R, TRUN_L + 0.03), (0.0, TRUN_L + 0.03)], 16, m)
    # falya deliği (touch hole) çıkıntısı
    xb = -TRUN_FROM_BREECH
    P5.aabox(bm, xb + 0.14, xb + 0.20, -0.025, 0.025, R_BREECH - 0.02, R_BREECH + 0.012)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new("MOD_CANNON_9PDR_A_BARREL")
    bm.to_mesh(me)
    bm.free()
    me.materials.append(M["iron"])
    for p in me.polygons:
        p.use_smooth = True
    me.set_sharp_from_angle(angle=math.radians(35))
    _uv(me)
    return me, n_body


def wheel(bm, cx, cy, r, w):
    m = Matrix.Translation((cx, cy - w / 2, r)) @ Matrix.Rotation(math.radians(-90), 4, "X")
    P5.lathe(bm, [(0.0, 0.0), (r * 0.30, 0.0), (r * 0.32, -0.02), (r - 0.02, 0.0), (r, 0.015), (r, w - 0.015),
                  (r - 0.02, w), (r * 0.32, w + 0.02), (r * 0.30, w), (0.0, w)], 20, m)


def build_carriage(M):
    bm_w, bm_i = bmesh.new(), bmesh.new()
    y_in = CHEEK_GAP / 2
    # yanaklar (basamaklı brackets): önden arkaya alçalan 3 basamak
    steps = [(TRUN_X - 0.14, CAR_X1, TRUN_Z - 0.02), (-0.18, TRUN_X - 0.14, TRUN_Z - 0.08),
             (-0.48, -0.18, TRUN_Z - 0.20), (CAR_X0, -0.48, TRUN_Z - 0.32)]
    z_bot = 0.19
    for sgn in (1, -1):
        y0, y1 = sorted((sgn * y_in, sgn * (y_in + CHEEK_T)))
        for xa, xb, zt in steps:
            P5.aabox(bm_w, xa, xb, y0, y1, z_bot, zt)
        # muylu yuvası üst tahtası yerine yanak ucu yuvarlatması: ön alt pah
        P5.aabox(bm_w, CAR_X1 - 0.10, CAR_X1, y0, y1, z_bot - 0.06, z_bot)
    # dingiller (axletrees) ve taban (bed) + nişan takozu (quoin)
    half = y_in + CHEEK_T + 0.06
    for ax, r in ((AXLE_X_F, WHEEL_R_F), (AXLE_X_R, WHEEL_R_R)):
        P5.aabox(bm_w, ax - 0.08, ax + 0.08, -half, half, r - 0.07, r + 0.07)
    P5.aabox(bm_w, -0.66, 0.10, -y_in, y_in, 0.49, 0.54)                  # taban tahtası (stool bed)
    P5.aabox(bm_w, -0.70, -0.34, -0.12, 0.12, 0.54, 0.665)                # quoin (takoz)
    P5.aabox(bm_w, -0.80, -0.70, -0.035, 0.035, 0.58, 0.63)               # takoz sapı
    P5.aabox(bm_w, CAR_X1 - 0.06, CAR_X1, -y_in, y_in, z_bot, z_bot + 0.28)   # ön travers (transom)
    n_wood = 0
    # tekerler (trucks) — ahşap
    for ax, r in ((AXLE_X_F, WHEEL_R_F), (AXLE_X_R, WHEEL_R_R)):
        for sgn in (1, -1):
            wheel(bm_w, ax, sgn * (half + WHEEL_W / 2 + 0.005), r, WHEEL_W)
    # demir: muylu kapakları (capsquares), halka cıvataları, dingil pimleri
    for sgn in (1, -1):
        yc = sgn * (y_in + CHEEK_T / 2)
        P5.aabox(bm_i, TRUN_X - 0.09, TRUN_X + 0.09, yc - CHEEK_T / 2 - 0.005, yc + CHEEK_T / 2 + 0.005, TRUN_Z + 0.045, TRUN_Z + 0.065)
        P5.aabox(bm_i, TRUN_X - 0.10, TRUN_X - 0.08, yc - CHEEK_T / 2 - 0.005, yc + CHEEK_T / 2 + 0.005, TRUN_Z - 0.10, TRUN_Z + 0.065)
        P5.aabox(bm_i, TRUN_X + 0.08, TRUN_X + 0.10, yc - CHEEK_T / 2 - 0.005, yc + CHEEK_T / 2 + 0.005, TRUN_Z - 0.10, TRUN_Z + 0.065)
        for xr in (-0.30, 0.20):                          # yan halka cıvataları (palanga)
            yy = sgn * (y_in + CHEEK_T + 0.01)
            P5.lathe(bm_i, [(0.045, -0.012), (0.045, 0.012), (0.030, 0.012), (0.030, -0.012), (0.045, -0.012)], 10,
                     Matrix.Translation((xr, yy + sgn * 0.045, 0.40)) @ Matrix.Rotation(math.radians(90), 4, "X"))
        for ax, r in ((AXLE_X_F, WHEEL_R_F), (AXLE_X_R, WHEEL_R_R)):
            yy = sgn * (half + WHEEL_W + 0.02)
            P5.aabox(bm_i, ax - 0.015, ax + 0.015, min(yy, yy - sgn * 0.02), max(yy, yy - sgn * 0.02), r - 0.04, r + 0.04)
    merged = bmesh.new()
    for idx, b in enumerate((bm_w, bm_i)):
        tmp = bpy.data.meshes.new("_tmp")
        bmesh.ops.recalc_face_normals(b, faces=b.faces)
        b.to_mesh(tmp)
        b.free()
        tmp.polygons.foreach_set("material_index", [idx] * len(tmp.polygons))
        merged.from_mesh(tmp)
        bpy.data.meshes.remove(tmp)
    me = bpy.data.meshes.new("MOD_CANNON_9PDR_A_CARRIAGE")
    merged.to_mesh(me)
    merged.free()
    me.materials.append(M["carriage"])
    me.materials.append(M["iron"])
    me.set_sharp_from_angle(angle=math.radians(35))
    _uv(me)
    return me, n_wood


def _uv(me):
    tmp = bpy.data.objects.new("_tmp_uv", me)
    H.build_uv_fallback(tmp)
    bpy.data.objects.remove(tmp)


def ensure_carriage_material():
    if "MAT_Carriage_RedOchre" not in bpy.data.materials:
        H.plank_material("MAT_Carriage_RedOchre", (0.28, 0.06, 0.035), (0.13, 0.03, 0.02), plank_w=0.3, rough=0.65, bump=0.12)
    return bpy.data.materials["MAT_Carriage_RedOchre"]


def installed_sockets():
    out = []
    for o in bpy.data.objects:
        if o.type != "EMPTY" or not o.name.startswith("SOCKET_CANNON_"):
            continue
        if o.name.startswith("SOCKET_CANNON_LOWER_"):
            continue
        out.append(o)
    return sorted(out, key=lambda o: o.name)


def deck_hit(sc, dg, p):
    """p'nin altındaki güverte üst yüzeyi (CORE_DECK_*)."""
    o = Vector(p) + Vector((0, 0, 0.6))
    for _ in range(6):
        ok, loc, nrm, idx, ob, mat = sc.ray_cast(dg, o, Vector((0, 0, -1)), distance=2.0)
        if not ok:
            return None
        if ob.name.startswith("CORE_DECK_"):
            return loc.z
        o = loc - Vector((0, 0, 0.002))
    return None


def fix_socket_heights(sc):
    """Top ve mürettebat soketlerini güverte kamburluğunun üstüne oturt (v004'ten beri orta hat yüksekliğindeydi)."""
    dg = bpy.context.evaluated_depsgraph_get()
    fixed, miss = [], []
    for o in bpy.data.objects:
        if o.type != "EMPTY" or not o.name.startswith(("SOCKET_CANNON_", "SOCK_CREW_")):
            continue
        z = deck_hit(sc, dg, o.location)
        if z is None:
            miss.append(o.name)
            continue
        if abs(z - o.location.z) > 0.002:
            fixed.append(round(z - o.location.z, 3))
            o.location.z = z
            o["manifest_version"] = MANIFEST_VERSION
    return fixed, miss


def place_gun(col, sock, car_me, bar_me, tag):
    car = bpy.data.objects.new(f"MOD_CANNON_9PDR_A_{tag}", car_me)
    col.objects.link(car)
    car.matrix_world = sock.matrix_world.copy()
    car["module_family"] = "CannonBattery"
    car["gun_type"] = "9pdr_long_truck"
    car["socket"] = sock.name
    car["recoil_local_x_m"] = -1.0          # TAHMİN, brok halatı ile sınırlı
    car["elevation_deg"] = [-6.0, 9.0]      # TAHMİN (takoz)
    bar = bpy.data.objects.new(f"MOD_CANNON_9PDR_A_{tag}_BARREL", bar_me)
    col.objects.link(bar)
    bar.parent = car
    bar.location = (TRUN_X, 0.0, TRUN_Z)
    bar["pivot"] = "trunnion_axis (yerel Y)"
    sock["installed_module"] = car.name
    sock["manifest_version"] = MANIFEST_VERSION
    return car, bar


def render(sc, preview_upgrade=True):
    H.setup_render(sc, fast=True)
    out = ROOT / "renders" / VER
    out.mkdir(parents=True, exist_ok=True)
    V = Vector
    DWL = P13.DWL
    D = V((0, 0, DWL))
    if preview_upgrade:
        # yalnız önizleme: alt güverte yükseltmesi (kaydedilmez) — kapaklar açık, toplar takılı
        car_me = bpy.data.meshes["MOD_CANNON_9PDR_A_CARRIAGE"]
        bar_me = bpy.data.meshes["MOD_CANNON_9PDR_A_BARREL"]
        col = bpy.data.collections["22_MODULES_CANNONS"]
        for o in [o for o in bpy.data.objects if o.name.startswith("SOCKET_CANNON_LOWER_")]:
            tag = o.name[len("SOCKET_CANNON_"):]
            car = bpy.data.objects.new(f"PREVIEW_{tag}", car_me)
            col.objects.link(car)
            car.matrix_world = o.matrix_world.copy()
            bar = bpy.data.objects.new(f"PREVIEW_{tag}_B", bar_me)
            col.objects.link(bar)
            bar.parent = car
            bar.location = (TRUN_X, 0.0, TRUN_Z)
            lid = bpy.data.objects.get(f"MOD_PORT_LID_{tag}")
            if lid:
                R = lid.matrix_world.to_3x3() @ Matrix.Rotation(math.radians(80), 3, "X")
                lid.rotation_euler = R.to_euler()
    for o in bpy.data.objects:
        if o.name.startswith("SOCK_LANTERN_LOWER_"):
            lamp = bpy.data.lights.new(o.name + "_L", "POINT")
            lamp.energy = 700
            lamp.color = (1.0, 0.72, 0.45)
            lamp.shadow_soft_size = 0.08
            lo = bpy.data.objects.new("LGT_" + o.name, lamp)
            lo.location = o.matrix_world @ V((0.0, 0.285, -0.13))
            sc.collection.objects.link(lo)
    fill = bpy.data.lights.new("LowerDeckFill", "AREA")     # yalnız önizleme: alt güverte dolgu ışığı
    fill.energy = 900
    fill.size = 14.0
    fill.color = (1.0, 0.8, 0.6)
    fo = bpy.data.objects.new("LGT_LowerDeckFill", fill)
    fo.location = V((0.0, 0.0, P13.zl(0.45) * K + DWL + 1.85))
    sc.collection.objects.link(fo)
    g = bpy.data.objects["SOCKET_CANNON_S_05"].matrix_world
    views = [
        ("top_yakin", g @ V((-2.6, 2.2, 1.9)), g @ V((0.2, 0, 0.7)), 35),
        ("top_yan", g @ V((0.2, 3.2, 1.0)), g @ V((0.2, 0, 0.6)), 35),
        ("bel_toplar", V((-12.0, 0.0, 6.0)) + D, V((6.0, 2.5, 2.0)) + D, 24),
        ("guverte", V((18, 12, 28)) * K + D, V((-4, 0, 3.0)) * K + D, 30),
        ("bas_omzu", V((34, 26, 12)) * K + D, V((1, 0, 1.2)) * K + D, 35),
        ("yukseltme_onizleme", V((-6, 30, 4)) * K + D, V((1, 0, 0.8)) * K + D, 35),
        ("alt_guverte_yukseltme", V((-9.2, 0.6, 1.53)) * K + D, V((8.0, -0.4, 1.1)) * K + D, 16),
    ]
    for name, loc, tgt, lens in views:
        sc.camera = H.camera(sc, f"CAM14_{name}", loc, tgt, lens=lens)
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
    M = P5.ensure_materials()
    M["carriage"] = ensure_carriage_material()
    col = bpy.data.collections["22_MODULES_CANNONS"]
    bar_me, _ = build_barrel(M)
    car_me, _ = build_carriage(M)
    fixed, miss = fix_socket_heights(sc)
    print("SOCKET_Z_FIX", len(fixed), "range", (min(fixed), max(fixed)) if fixed else None, "MISS", miss)
    bpy.context.view_layer.update()
    placed = []
    for s in installed_sockets():
        tag = s.name[len("SOCKET_CANNON_"):]
        car, bar = place_gun(col, s, car_me, bar_me, tag)
        placed.append(car.name)
    # namlu soketleri (UE statik mesh soketi; ana örnek: S_01)
    master = bpy.data.objects["MOD_CANNON_9PDR_A_S_01_BARREL"]
    xm = L_BARREL - TRUN_FROM_BREECH
    xb = -TRUN_FROM_BREECH
    for name, loc in (("SOCKET_GUN_MUZZLE", (xm + 0.02, 0, 0)), ("SOCKET_GUN_TOUCHHOLE", (xb + 0.17, 0, R_BREECH + 0.02))):
        e = bpy.data.objects.new(name, None)
        e.empty_display_type = "SINGLE_ARROW"
        e.empty_display_size = 0.2
        col.objects.link(e)
        e.parent = master
        e.location = loc
        e.rotation_euler = (0, math.radians(90), 0) if "MUZZLE" in name else (0, 0, 0)
        e["mesh_socket_of"] = "MOD_CANNON_9PDR_A_BARREL"
        e["manifest_version"] = MANIFEST_VERSION
    for o in bpy.data.objects:
        if o.type == "EMPTY" and o.name.startswith("SOCKET_CANNON_LOWER_"):
            o["module_family_accepts"] = "MOD_CANNON_9PDR_A"
            o["manifest_version"] = MANIFEST_VERSION

    # denetim: namlu ağzı lumbarda mı (yerel), mürettebat noktası kızakla çakışıyor mu
    bpy.context.view_layer.update()
    muzzle_check = []
    for n in placed:
        car = bpy.data.objects[n]
        s = bpy.data.objects[car["socket"]]
        if "CHASE" in s.name:
            continue
        mw = car.children[0].matrix_world
        muz = mw @ Vector((xm, 0, 0))
        loc = s.matrix_world.inverted() @ muz
        muzzle_check.append({"gun": n, "muzzle_local_x": round(loc.x, 3), "muzzle_z_world": round(muz.z, 3)})
    crew_hits = []
    for o in bpy.data.objects:
        if o.type == "EMPTY" and o.name.startswith("SOCK_CREW_") and not o.name.startswith("SOCK_CREW_LOWER_"):
            g = bpy.data.objects.get(o.get("gun_socket", ""))
            if not g:
                continue
            p = g.matrix_world.inverted() @ o.matrix_world.translation
            if CAR_X0 - 0.15 < p.x < CAR_X1 + 0.15 and abs(p.y) < CHEEK_GAP / 2 + CHEEK_T + WHEEL_W + 0.15:
                crew_hits.append(o.name)

    bpy.ops.wm.save_as_mainfile(filepath=str(out), compress=True)
    H.VERSION = VER
    ap = ROOT / "reports" / f"scene_audit_{VER}.json"
    rep = H.audit(sc, ap)
    dg = bpy.context.evaluated_depsgraph_get()

    def tris(me):
        me.calc_loop_triangles()
        return len(me.loop_triangles)

    rep["cannon_v014"] = {
        "module": "MOD_CANNON_9PDR_A", "installed": len(placed), "lower_deck_sockets_empty": 20,
        "tris": {"barrel": tris(bar_me), "carriage": tris(car_me)},
        "dims_m": {"bore": BORE, "barrel_length": L_BARREL, "trunnion_height": TRUN_Z, "carriage_length": round(CAR_X1 - CAR_X0, 2),
                   "wheel_r_front": WHEEL_R_F, "wheel_r_rear": WHEEL_R_R},
        "sources": {"bore": "İKİNCİL (IMA arama özeti, 4,2 inç)", "others": "TAHMİN"},
        "muzzle_check": muzzle_check, "crew_inside_carriage": crew_hits,
        "socket_z_fix": {"count": len(fixed), "min_m": min(fixed) if fixed else 0, "max_m": max(fixed) if fixed else 0, "missed": miss},
    }
    rep["pass"] = {"name": "pass_v014_cannon_9pdr", "source": f"Blender/versions/{SHIP}_{SRC_VER}.blend",
                   "pass_changes": {"modules_added": placed, "mesh_sockets": ["SOCKET_GUN_MUZZLE", "SOCKET_GUN_TOUCHHOLE"]},
                   "manifest_version": MANIFEST_VERSION, "geometry_changed": "yalnız modül eklendi"}
    ap.write_text(json.dumps(rep, indent=2, ensure_ascii=False), encoding="utf-8")
    c = rep["cannon_v014"]
    print("GUNS", c["installed"], "TRIS", c["tris"], "CREW_HITS", crew_hits)
    print("MUZZLE", [(m["gun"][-6:], m["muzzle_local_x"]) for m in muzzle_check[:4]])
    if "--no-render" not in sys.argv:
        render(sc)


if __name__ == "__main__":
    main()
