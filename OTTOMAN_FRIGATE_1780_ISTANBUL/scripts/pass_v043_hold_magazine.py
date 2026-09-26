"""v043 — Kızıl Sancak iç düzeni 3: ambar — cephanelik, barut hazırlama odası, ışık penceresi, gülle sandıkları,
erzak deposu, ambar hasar kontrol istasyonu.

    python3.11 OTTOMAN_FRIGATE_1780_ISTANBUL/scripts/pass_v043_hold_magazine.py [--no-render | --render-only]

Onaylı plan: reports/KIZIL_SANCAK_UYARLAMA_PLANI.md §4 (Gate A). Kaynak kurallar (kullanıcı tasarım paketi, Ek Cilt II):
- s. 112 "Cephanelik ve hazırlama odası ayrımı": cephanelik, hazırlama odası ve hazır servis dolabı ayrı fiziksel alanlar;
  toplam barut ile servis edilebilir/hazırlanmış barut ayrılır.
- s. 113 "Kaplar, mühür, nem ve saklama": ContainerClosed ≠ Sealed ≠ Dry → fıçılar mühürlü, rafta, zeminden yüksek.
- s. 116 "Yangın tehdidi ve sınır soğutması": ıslak perde, ışık penceresi (alev cephaneliğe girmez).
- s. 87 "Hasar kontrol istasyonları ve dağıtılmış stok".
Tarihî karşılık [İKİNCİL: Lavery, "The Arming and Fitting of English Ships of War 1600–1815"]: baş ambarında kurşun
kaplı cephanelik, önünde dolum (filling) odası, camlı "light room" feneri, bakır çemberli barut fıçıları.
Ölçüler oyuna uyarlanmış [TAHMİN].
Yerleşim (ambar tabanı ≈ −1,5…−0,8 m, kiriş altı ≈ 0,9…1,5 m):
- Hazırlama odası x 10,65…11,95; cephanelik x 11,95…14,2 (pruva direği dibi içinden geçer).
- Erzak/peksimet deposu x −14,0…−12,35 (kıç), bölme + kapı.
- Gülle sandıkları: yük bloğunun iki yanında (y ≈ ±3,3), ana direk civarı.
- Hasar kontrol istasyonu: ambar merdiveni yanında.
"""

import importlib.util
import json
import math
import sys
from pathlib import Path

import bpy  # noqa: I001
import bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree

HERE = Path(__file__).resolve().parent
sp = importlib.util.spec_from_file_location("pass_v033", HERE / "pass_v033_facet_cleanup.py")
P33 = importlib.util.module_from_spec(sp)
sp.loader.exec_module(P33)
P31 = P33.P31
RS, QA, LODS, H = P31.RS, P31.QA, P31.LODS, P31.H
ROOT, SHIP = P31.ROOT, P31.SHIP
SRC_VER, VER = "v042", "v043"
V = Vector
sys.path.insert(0, str(HERE))
import interior_kit as IK  # noqa: E402

IK.RS = RS
T = {}
SKIPPED = {}
X_AFT, X_MID, X_FWD = 10.65, 11.95, 14.2


def mw(o):
    return o.matrix_basis.copy() if o.parent is None else o.matrix_world.copy()


def bvh(names):
    dg = bpy.context.evaluated_depsgraph_get()
    vs, fs = [], []
    for n in names:
        o = bpy.data.objects.get(n)
        if o is None or o.type != "MESH":
            continue
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        M = o.matrix_world
        b = len(vs)
        vs += [M @ v.co for v in me.vertices]
        fs += [tuple(b + i for i in p.vertices) for p in me.polygons]
        ev.to_mesh_clear()
    return BVHTree.FromPolygons(vs, fs)


def fz(x, y):
    hit = T["floor"].ray_cast(V((x, y, 0.4)), V((0, 0, -1)), 3.0)
    return hit[0].z if hit[0] is not None else -1.2


def cz(x, y):
    hit = T["ceil"].ray_cast(V((x, y, fz(x, y) + 0.3)), V((0, 0, 1)), 4.0)
    return hit[0].z if hit[0] is not None else fz(x, y) + 2.2


def halfw(x, z):
    hit = T["hull"].ray_cast(V((x, 0.0, z)), V((0, 1, 0)), 8.0)
    return hit[0].y if hit[0] is not None else 3.0


def try_add(dst, key, build):
    tmp = bmesh.new()
    build(tmp)
    if not tmp.faces:
        tmp.free()
        return False
    if T["obst"].overlap(BVHTree.FromBMesh(tmp)):
        SKIPPED[key] = SKIPPED.get(key, 0) + 1
        tmp.free()
        return False
    me = bpy.data.meshes.new("_tmp")
    tmp.to_mesh(me)
    tmp.free()
    dst.from_mesh(me)
    bpy.data.meshes.remove(me)
    return True


def clear_box(lo, hi):
    """Eksen hizalı kutunun engellerle çakışmadığını sınar (örnek nesneler için)."""
    tmp = bmesh.new()
    IK.box(tmp, ((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, (lo[2] + hi[2]) / 2), (hi[0] - lo[0], hi[1] - lo[1], hi[2] - lo[2]), r=0.0, segs=1)
    ok = not T["obst"].overlap(BVHTree.FromBMesh(tmp))
    tmp.free()
    return ok


# ------------------------------------------------------------------ paylaşılan örnek ağlar (UE: instanced static mesh)
def powder_barrel_mesh(M):
    me = bpy.data.meshes.get("SM_PROP_POWDER_BARREL_A")
    if me:
        return me
    bm = bmesh.new()
    r, h = 0.21, 0.52
    prof = [(0.0, 0.0), (r * 0.80, 0.0)] + [(r * (0.80 + 0.20 * math.sin(math.pi * t)), h * t) for t in [i / 14 for i in range(15)]] + [(0.0, h)]
    IK.lathe(bm, prof, V((0, 0, 0)), mat=0)
    for t in (0.1, 0.24, 0.76, 0.9):                                          # bakır çember (kıvılcım çıkarmaz)
        rr = r * (0.80 + 0.20 * math.sin(math.pi * t)) + 0.003
        IK.lathe(bm, [(rr - 0.004, h * t - 0.012)] + [(rr + 0.002 * math.sin(math.pi * k / 6), h * t - 0.012 + 0.024 * k / 6) for k in range(7)]
                 + [(rr - 0.004, h * t + 0.012)], V((0, 0, 0)), mat=1)
    IK.box(bm, (0, 0, h + 0.004), (0.10, 0.10, 0.01), r=0.003, mat=2)       # mühür (kurşun)
    me = bpy.data.meshes.new("SM_PROP_POWDER_BARREL_A")
    bm.to_mesh(me)
    bm.free()
    for m in (M["oak"], M["copper"], M["lead"]):
        me.materials.append(m)
    IK.box_uv(me)
    RS.sharp_from_angle_keep(me, 35)
    me["note"] = "barut fıçısı: bakır çember, kurşun mühür (Ek Cilt II s. 113: Sealed ≠ ContainerClosed)"
    return me


def shot_pile_mesh(M):
    me = bpy.data.meshes.get("SM_PROP_SHOT_PILE_A")
    if me:
        return me
    bm = bmesh.new()
    r = 0.061                                                                 # 9 librelik gülle çapı ≈ 0,12 m [İKİNCİL]
    n = 0
    for layer, (nx, ny) in enumerate(((5, 4), (4, 3), (3, 2), (2, 1))):
        for i in range(nx):
            for j in range(ny):
                c = V(((i - (nx - 1) / 2) * 2 * r, (j - (ny - 1) / 2) * 2 * r, r + layer * r * 1.414))
                ret = bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=10, radius=r)
                bmesh.ops.translate(bm, vec=c, verts=ret["verts"])
                n += 1
    for f in bm.faces:
        f.smooth = True
    me = bpy.data.meshes.new("SM_PROP_SHOT_PILE_A")
    bm.to_mesh(me)
    bm.free()
    me.materials.append(M["iron"])
    IK.box_uv(me)
    me["shot_count"] = n
    return me


def place_instances(me, col, prefix, spots, props):
    out = []
    for k, (p, rz) in enumerate(spots):
        o = bpy.data.objects.new(f"{prefix}_{k + 1:03d}", me)
        o.location = p
        o.rotation_euler.z = rz
        col.objects.link(o)
        for a, b in props.items():
            o[a] = b
        out.append(o.name)
    return out


# ------------------------------------------------------------------ 1. cephanelik + hazırlama odası
def magazine(M, col, icol):
    rep = {}
    bm = bmesh.new()
    zmid = fz(12.5, 0.8)
    walls = []
    for x, door_y in ((X_AFT, 1.45), (X_MID, -1.45), (X_FWD, None)):
        z0 = fz(x, 1.5) - 0.02
        z1 = cz(x, 1.5) - 0.01
        w = halfw(x, (z0 + z1) / 2) - 0.03
        L = 2 * w
        door = None if door_y is None else (door_y + w, 0.70, 1.62)
        IK.plank_partition(bm, (x, -w), (x, w), z0, z1, t=0.06, mat=0, trim_mat=1, door=door)
        walls.append((x, round(w, 2)))
    # kurşun kaplı zemin (cephanelik) + ahşap ızgara zemin (hazırlama)
    for (xa, xb, mat) in ((X_MID + 0.04, X_FWD - 0.04, 0), (X_AFT + 0.04, X_MID - 0.04, 1)):
        xm = (xa + xb) / 2
        z = fz(xm, 1.2)
        w = halfw(xm, z + 0.3) - 0.08
        IK.box(bm, (xm, 0.0, z + 0.03), (xb - xa, 2 * w, 0.06), r=0.01, mat=mat)
    # ışık penceresi: orta duvarda camlı kutu, fener hazırlama odası tarafında
    zw = fz(X_MID, 1.2) + 1.25
    IK.box(bm, (X_MID, 1.2, zw), (0.12, 0.62, 0.52), r=0.012, mat=1)
    IK.box(bm, (X_MID, 1.2, zw), (0.13, 0.50, 0.40), r=0.004, mat=3)
    IK.lathe(bm, [(0.0, 0.0), (0.07, 0.0), (0.075, 0.02), (0.06, 0.2), (0.075, 0.22), (0.0, 0.28)], V((X_MID - 0.22, 1.2, zw - 0.14)), mat=2)
    IK.box(bm, (X_MID - 0.14, 1.2, zw - 0.16), (0.2, 0.2, 0.03), r=0.006, mat=1)
    # hazırlama odası: dolum tezgâhı, fişek rafları, ölçekler, ıslak perde
    xb_ = (X_AFT + X_MID) / 2
    zf = fz(xb_, -2.0)
    wb = halfw(xb_, zf + 0.5) - 0.12

    def bench(b):
        IK.box(b, (xb_, -wb + 0.32, zf + 0.86), (1.0, 0.6, 0.06), r=0.012, mat=1)
        for dx in (-0.42, 0.42):
            IK.box(b, (xb_ + dx, -wb + 0.32, zf + 0.43), (0.07, 0.5, 0.86), r=0.01, mat=1)
        for k in range(3):                                                    # bakır ölçekler
            IK.lathe(b, [(0.0, 0.0), (0.05, 0.0), (0.055, 0.12), (0.052, 0.13), (0.0, 0.01)], V((xb_ - 0.3 + 0.3 * k, -wb + 0.22, zf + 0.89)), mat=2)
    rep["filling_bench"] = try_add(bm, "filling_bench", bench)

    def racks(b):
        yr = wb - 0.2
        for h in (0.6, 1.05, 1.5):
            IK.box(b, (xb_, yr, zf + h), (1.05, 0.34, 0.03), r=0.006, mat=1)
            for k in range(8):                                                # flanel fişek torbaları
                IK.cyl(b, (xb_ - 0.42 + 0.12 * k, yr - 0.12, zf + h + 0.02), (xb_ - 0.42 + 0.12 * k, yr + 0.12, zf + h + 0.02), 0.05, mat=4)
        for dx in (-0.5, 0.5):
            IK.box(b, (xb_ + dx, yr, zf + 0.85), (0.05, 0.34, 1.7), r=0.008, mat=1)
    rep["cartridge_racks"] = try_add(bm, "cartridge_racks", racks)
    zc = cz(X_AFT, 1.45) - 0.03
    IK.curtain(bm, (X_AFT - 0.08, 1.45 - 0.45), (X_AFT - 0.08, 1.45 + 0.45), fz(X_AFT, 1.45) + 0.05, zc, folds=5, depth=0.025, mat=5)
    IK.cyl(bm, (X_AFT - 0.08, 1.45 - 0.5, zc), (X_AFT - 0.08, 1.45 + 0.5, zc), 0.015, mat=6)
    IK.finish("MOD_MAGAZINE_ROOMS_A", bm, [M["lead"], M["oak"], M["copper"], M["glass"], M["flannel"], M["wet_canvas"], M["iron"]], col,
              {"room": "magazine", "fire_boundary": "kurşun kaplı bölme; ışık penceresi (alev cephaneliğe girmez); ıslak perde",
               "rule": "Ek Cilt II s. 112–116"})
    rep["walls"] = walls
    # barut fıçıları: iki kat, bordaya dayalı raflar (örnek ağ)
    bme = bmesh.new()
    spots = []
    for s in (1, -1):
        for x in [X_MID + 0.35 + 0.46 * i for i in range(5)]:
            z = fz(x, s * 2.2)
            w = halfw(x, z + 0.5)
            for row, dy in enumerate((0.34, 0.80)):
                y = s * (w - dy)
                if abs(y) < 0.9:
                    continue
                for tier in (0.06, 0.66):
                    lo = (x - 0.22, y - 0.22, z + tier + 0.01)
                    hi = (x + 0.22, y + 0.22, z + tier + 0.54)
                    if clear_box(lo, hi):
                        spots.append((V((x, y, z + tier)), 0.37 * (row + tier)))
            # raf (üst kat için)
            IK.box(bme, (x, s * (w - 0.57), z + 0.63), (0.46, 1.0, 0.04), r=0.008, mat=0)
            IK.box(bme, (x, s * (w - 0.57), z + 0.31), (0.06, 1.0, 0.62), r=0.008, mat=0)
    IK.finish("MOD_MAGAZINE_RACKS_A", bme, [M["oak"]], col, {"room": "magazine"})
    pb = powder_barrel_mesh(M)
    rep["powder_barrels"] = len(place_instances(pb, icol, "MOD_MAGAZINE_POWDER_BARREL", spots,
                                               {"room": "magazine", "PowderBatchID": "PB_SANCAKKALE_A", "sealed": True,
                                                "note": "Ek Cilt II s. 111: PowderBatchID ≠ PowderChargeID"}))
    return rep


# ------------------------------------------------------------------ 2. erzak / peksimet deposu (kıç)
def bread_room(M, col):
    bm = bmesh.new()
    x = -12.35
    z0 = fz(x, 1.5) - 0.02
    z1 = cz(x, 1.5) - 0.01
    w = halfw(x, (z0 + z1) / 2) - 0.03
    IK.plank_partition(bm, (x, -w), (x, w), z0, z1, t=0.05, mat=0, trim_mat=0, door=(w + 0.0, 0.70, 1.6))
    n = 0
    for i, xx in enumerate((-13.7, -13.15)):
        for s in (1, -1):
            for j in range(3):
                y = s * (0.9 + 0.62 * j)
                z = fz(xx, y)
                if abs(y) > halfw(xx, z + 0.4) - 0.4:
                    continue
                if (i + j) % 2 == 0:
                    ok = try_add(bm, "sack", lambda b, xx=xx, y=y, z=z: (IK.box(b, (xx, y, z + 0.24), (0.5, 0.42, 0.48), r=0.12, mat=1),
                                                                         IK.box(b, (xx, y, z + 0.67), (0.46, 0.38, 0.4), r=0.11, mat=1)))
                else:
                    ok = try_add(bm, "crate", lambda b, xx=xx, y=y, z=z: (IK.box(b, (xx, y, z + 0.25), (0.52, 0.5, 0.5), r=0.012, mat=0),
                                                                          IK.box(b, (xx, y, z + 0.51), (0.54, 0.52, 0.03), r=0.008, mat=2)))
                n += ok
    IK.finish("MOD_HOLD_BREAD_ROOM_A", bm, [M["oak"], M["sack"], M["iron"]], col,
              {"room": "bread_room", "note": "kuru erzak (peksimet, un, bakliyat); zeminden yüksek, kuru"})
    return {"items": n, "wall_half_w": round(w, 2)}


# ------------------------------------------------------------------ 3. gülle sandıkları
def shot_lockers(M, col, icol):
    bm = bmesh.new()
    spots = []
    for x in (-0.3, 0.6, 3.0, 4.0):
        for s in (1, -1):
            z = fz(x, s * 3.3)
            w = halfw(x, z + 0.4)
            y = s * (w - 0.55)
            lo, hi = (x - 0.42, y - 0.36, z + 0.01), (x + 0.42, y + 0.36, z + 0.62)
            if not clear_box(lo, hi):
                continue
            IK.box(bm, (x, y, z + 0.15), (0.80, 0.66, 0.30), r=0.012, mat=0)       # alçak sandık
            IK.box(bm, (x, y, z + 0.04), (0.84, 0.70, 0.08), r=0.012, mat=0)
            spots.append((V((x, y, z + 0.08)), 0.0))
    IK.finish("MOD_HOLD_SHOT_LOCKERS_A", bm, [M["oak"]], col, {"room": "shot_locker", "note": "9 librelik gülle yığınları"})
    me = shot_pile_mesh(M)
    names = place_instances(me, icol, "MOD_HOLD_SHOT_PILE", spots, {"room": "shot_locker", "shot_count": me["shot_count"]})
    return {"lockers": len(spots), "shot": len(spots) * me["shot_count"], "objects": names}


# ------------------------------------------------------------------ 4. hasar kontrol istasyonu (ambar)
def damage_station(M, col, name, x, y, z_of, deck):
    bm = bmesh.new()
    z = z_of(x, y)

    def st(b):
        IK.box(b, (x, y, z + 0.40), (0.9, 0.55, 0.80), r=0.015, mat=0)              # dolap
        IK.box(b, (x, y - math.copysign(0.28, y), z + 0.40), (0.86, 0.02, 0.74), r=0.006, mat=1)   # kızıl boyalı kapak
        for k in range(4):                                                        # tapalar
            IK.plug(b, (x - 0.3 + 0.2 * k, y, z + 0.81), 0.05, 0.022, 0.14, mat=2)
        IK.bucket(b, (x + 0.62, y, z), 0.13, 0.27, mat=2, band=3)
        IK.box(b, (x - 0.02, y, z + 0.84 + 0.06), (0.95, 0.18, 0.06), r=0.01, mat=2)  # yedek kereste
        IK.box(b, (x - 0.02, y, z + 0.84 + 0.13), (0.95, 0.16, 0.06), r=0.01, mat=2)
        IK.cyl(b, (x + 0.38, y - 0.12, z + 0.83), (x + 0.38, y + 0.12, z + 0.83), 0.06, mat=4)   # kalafat üstüpü rulosu
    ok = try_add(bm, name, st)
    if ok:
        IK.finish(name, bm, [M["oak"], M["red"], M["oak_light"], M["iron"], M["oakum"]], col,
                  {"room": "damage_control", "deck": deck, "interact": "damage_control_stock",
                   "note": "Ek Cilt II s. 87: hasar kontrol stokları fiziksel ve dağıtılmıştır (tapa, kalafat, kereste, kova)"})
    else:
        bm.free()
    return ok


def rooms(col):
    out = []

    def R(name, lo, hi, cmp, label, stn, wtz, deck, extra=None):
        out.append(IK.room(name, lo, hi, col, cmp, label, stn, wtz, deck, extra).name)
    zf, zc = fz(13.0, 1.0), cz(13.0, 1.0)
    R("ROOM_MAGAZINE", (X_MID, -3.4, zf), (X_FWD, 3.4, zc), "CMP_HOLD_FWD_MAG", "Cephanelik", "STN_MAGAZINE", "WTZ_HOLD_FWD", "hold",
      {"fire_boundary": "kurşun kaplı", "rule": "Ek Cilt II s. 112 — cephanelik ≠ hazırlama odası ≠ hazır dolap",
       "access": "yetkili (topçu başı); çıplak alev yasak"})
    R("ROOM_FILLING", (X_AFT, -3.9, zf), (X_MID, 3.9, zc), "CMP_HOLD_FWD_FILL", "Barut Hazırlama Odası", "STN_FILLING", "WTZ_HOLD_FWD", "hold",
      {"rule": "Ek Cilt II s. 112/114 — mühimmat çıkarma atomik ve rotalı", "wet_curtain": True})
    R("STATION_LIGHT_ROOM", (X_MID - 0.35, 0.85, zf + 0.9), (X_MID + 0.1, 1.55, zf + 1.6), "CMP_HOLD_FWD_FILL", "Işık Penceresi",
      "STN_LIGHT_ROOM", "WTZ_HOLD_FWD", "hold", {"note": "fener camın arkasında; cephaneliğe alev girmez"})
    R("ROOM_BREAD_ROOM", (-14.0, -3.3, fz(-13.2, 1.0)), (-12.35, 3.3, cz(-13.2, 1.0)), "CMP_HOLD_AFT", "Erzak / Peksimet Deposu",
      "STN_STORES", "WTZ_HOLD_AFT", "hold")
    R("ROOM_SHOT_LOCKER", (-0.8, -4.6, fz(1.0, 3.0)), (4.5, 4.6, fz(1.0, 3.0) + 0.8), "CMP_HOLD_MID_SIDES", "Gülle Sandıkları",
      "STN_SHOT_SUPPLY", "WTZ_HOLD_MID", "hold")
    R("ROOM_HOLD_CARGO", (-12.2, -2.6, fz(0.0, 0.0)), (10.45, 2.6, cz(0.0, 0.0)), "CMP_HOLD_MID", "Ana Ambar (su, erzak fıçıları)",
      "STN_HOLD", "WTZ_HOLD_MID", "hold")
    return out


def mats():
    M = {"iron": bpy.data.materials["MAT_Iron_Black"], "glass": bpy.data.materials["MAT_Glass_Lantern"],
         "red": bpy.data.materials.get("MAT_Panel_KizilLacquer") or IK.mat("MAT_Panel_KizilLacquer", (0.32, 0.045, 0.035), 0.42)}
    M["oak"] = IK.mat_wood()
    M["oak_light"] = IK.mat_wood("MAT_Wood_Pine_Spare", (0.55, 0.40, 0.22), (0.38, 0.26, 0.13), 0.7)
    M["lead"] = IK.mat("MAT_Lead_Sheet", (0.17, 0.18, 0.20), 0.72, 0.55)     # donuk, oksitli kurşun levha
    M["copper"] = IK.mat("MAT_Copper", (0.62, 0.30, 0.18), 0.35, 1.0)
    M["flannel"] = IK.mat("MAT_Flannel_Cartridge", (0.62, 0.55, 0.40), 0.9)
    M["wet_canvas"] = IK.mat("MAT_Canvas_Wet", (0.30, 0.28, 0.24), 0.35)
    M["sack"] = IK.mat("MAT_Sack_Hessian", (0.45, 0.36, 0.22), 0.9)
    M["oakum"] = IK.mat("MAT_Oakum", (0.22, 0.16, 0.09), 0.9)
    return M


def render(sc):
    H.setup_render(sc, fast=True)
    sc.cycles.samples = 32
    out = ROOT / "renders" / VER
    out.mkdir(parents=True, exist_ok=True)
    for o in bpy.data.objects:
        if o.type != "MESH":
            continue
        ws = [o.matrix_world @ V(c) for c in o.bound_box]
        hide = (min(w.z for w in ws) > 0.55) or o.name in ("CORE_DECK_LOWER", "CORE_DECK_BEAMS_LOWER", "CORE_DECK_GUN", "CORE_DECK_BEAMS_UPPER",
                                                            "CORE_KNEES_LOWER_DECK", "CORE_WALE_LOWER_TIER") \
            or o.name.startswith(("MOD_SAIL_", "MOD_RIG_", "MOD_FLAG_", "MOD_CANNON", "MOD_PUMP", "MOD_CAPSTAN", "MOD_CREW_", "MOD_GALLEY",
                                  "MOD_GUNROOM", "MOD_SICKBAY", "MOD_WORKSHOPS", "MOD_JUNIOR", "CORE_LADDER_LOWER"))
        if hide:
            if o.animation_data:
                for fc in list(o.animation_data.drivers):
                    o.animation_data.drivers.remove(fc)
            o.hide_render = True
    for i, x in enumerate((-13.2, -9, -5, -1, 3, 7, 11.3, 13.2)):
        lt = bpy.data.objects.new(f"L_AMB_{i}", bpy.data.lights.new(f"L_AMB_{i}", "POINT"))
        lt.data.energy, lt.data.shadow_soft_size, lt.data.color = 140, 0.4, (1.0, 0.84, 0.62)
        lt.location = (x, 0.0, 0.4)
        sc.collection.objects.link(lt)
    shots = (("ambar_ust", V((0.0, 0.0, 26.0)), V((0.0, 0.0, -1.0)), 24),
             ("cephanelik", V((10.9, -2.8, 0.7)), V((13.6, 1.8, -0.5)), 22),
             ("hazirlama", V((12.6, 2.6, 0.8)), V((11.0, -2.2, -0.4)), 22),
             ("erzak_gulle", V((-10.8, -3.8, 0.6)), V((-13.4, 1.6, -0.8)), 24))
    for name, loc, tgt, lens in shots:
        sc.camera = H.camera(sc, f"CAM43_{name}", loc, tgt, lens=lens)
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
    bpy.context.view_layer.update()
    T["floor"] = bvh(["CORE_HOLD_FLOOR"])
    T["ceil"] = bvh(["CORE_DECK_LOWER", "CORE_DECK_BEAMS_LOWER"])
    T["hull"] = bvh(["CORE_HULL_SHELL"])
    obst = []
    for o in bpy.data.objects:
        if o.type != "MESH" or "_LOD" in o.name or o.name.startswith(("CORE_HULL_SHELL", "CORE_HOLD_FLOOR", "UCX_", "CUT_", "MOD_SAIL_", "MOD_FLAG_")):
            continue
        ws = [mw(o) @ V(c) for c in o.bound_box]
        if min(w.z for w in ws) < 1.6 and max(w.z for w in ws) > -1.7 and max(w.x for w in ws) - min(w.x for w in ws) < 45:
            obst.append(o.name)
    T["obst"] = bvh(obst)
    col = bpy.data.collections["24_MODULES_DECOR"]
    icol = IK.ensure_col("26_HOLD_INSTANCES")
    rcol = IK.ensure_col("35_ROOMS")
    M = mats()
    rep = {"obstacles": len(obst)}
    rep["magazine"] = magazine(M, col, icol)
    rep["bread_room"] = bread_room(M, col)
    rep["shot_lockers"] = shot_lockers(M, col, icol)
    rep["damage_station_hold"] = damage_station(M, col, "MOD_DAMAGE_STATION_HOLD_A", -3.1, 3.4, fz, "hold") or \
        damage_station(M, col, "MOD_DAMAGE_STATION_HOLD_A", -3.1, -3.4, fz, "hold")
    rep["skipped_for_clash"] = SKIPPED
    rep["rooms"] = rooms(rcol)
    new = {"MOD_MAGAZINE_ROOMS_A", "MOD_MAGAZINE_RACKS_A", "MOD_HOLD_BREAD_ROOM_A", "MOD_HOLD_SHOT_LOCKERS_A", "MOD_DAMAGE_STATION_HOLD_A"}
    new |= {o.name for o in icol.objects if o.name.endswith("_001")}
    LODS.build_lods(sc, only=new)
    bpy.ops.wm.save_as_mainfile(filepath=str(out), compress=True)
    H.VERSION = VER
    ap = ROOT / "reports" / f"scene_audit_{VER}.json"
    arep = H.audit(sc, ap)
    arep["interior_v043"] = rep
    arep["pass"] = {"name": "pass_v043_hold_magazine", "source": f"Blender/versions/{SHIP}_{SRC_VER}.blend"}
    ap.write_text(json.dumps(arep, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    qa = QA.audit(sc, top=60)
    (ROOT / "reports" / f"kalite_testi_{VER}.json").write_text(json.dumps(qa, indent=1, ensure_ascii=False), encoding="utf-8")
    print("V043", json.dumps({k: (v if k != "shot_lockers" else {a: b for a, b in v.items() if a != "objects"}) for k, v in rep.items()},
                             ensure_ascii=False, default=str))
    print("V043 QA", json.dumps(qa["summary"], ensure_ascii=False))
    for r in [r for r in qa["objects"] if r["fail"] or r["floating_islands"]]:
        print(f"  HATA {r['name']} facet={r['facet_m']}m sag={r['worst_sag_mm']}mm havada={r['floating_islands'][:3]}")
    if "--no-render" not in sys.argv:
        render(sc)


if __name__ == "__main__":
    main()
