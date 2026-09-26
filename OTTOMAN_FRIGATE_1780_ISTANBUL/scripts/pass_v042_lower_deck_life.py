"""v042 — Kızıl Sancak iç düzeni 2: kaptan dairesi düzeltmesi + alt güverte yaşamı, ocak, su, sanitasyon.

Kullanıcı (v041 sonrası): "çırak rıhtımının kaptan kamarasında ne işi var; oradaki 2 topu da kaldır; toplam top 20+2
kalsın" → kıç topları silindi, çırak rıhtımı alt güvertede subay odası kabinine (S1) taşındı, sancak-ön bölme kalktı.

    python3.11 OTTOMAN_FRIGATE_1780_ISTANBUL/scripts/pass_v042_lower_deck_life.py [--no-render | --render-only]

Onaylı plan: reports/KIZIL_SANCAK_UYARLAMA_PLANI.md §4 (Gate A). Kaynak kurallar (kullanıcı tasarım paketi, Ek Cilt II):
- s. 95 "Hamak, hot-bunking ve vardiya dinlenmesi": güverte yalnız zemin değildir; mürettebat kapasitesi uzun süreli
  yaşamla belirlenir; hamak ve vardiya gerçek dinlenmeyi etkiler → kıçta asılı (nöbet dışı uyuyan) ve sarılı hamaklar.
- s. 96 "Galley, sanitasyon ve içme suyu noktaları"; s. 97 "Hastane, havalandırma ve atölye alanları".
- s. 81 oda kimlikleri (CompartmentID ≠ RoomLabel ≠ OperationalStationID ≠ WatertightZoneID).
Yerleşim (alt güverte, taban ≈ 1,0–1,9 m, tavan ≈ 3,1–4,0 m):
- Mürettebat yatakhanesi (x −11,3…0): 2,6 m kanca arası hamaklar, 0,6 m sıra aralığı [TAHMİN; dönemin 14 inç
  (0,36 m) kişi başı aralığı [İKİNCİL: Lavery, "Nelson's Navy"] oyunda geçiş için genişletildi].
- Yemek bölümü (x 0…8): bordaya dayalı, iple asılı sofralar + sıralar + deniz sandıkları.
- Subay odası (gunroom, x −18…−11,8): 4 perdeli subay kabini (asma yatak + sandık), ortada sofra.
- Revir (x 14,2…17,5): kanvas perde, 2 asma yatak, cerrah sandığı, leğen, şişe rafı.
- Atölyeler (x 8,4…11,8, bordalarda): marangoz (iskele), yelkenci (sancak).
- Ocak (galley, x 10…11,4 orta): tuğla ocak, demir üst levha, iki bakır kazan, üst güverteden çıkan baca, su fıçısı.
- Üst güverte: içme suyu fıçısı (scuttlebutt), baş kasarası altında baş tuvaletleri.
Her parça yerleştirilmeden önce mevcut nesnelerle üçgen düzeyinde çakışma testinden geçer; çakışan atlanır ve raporlanır.
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
SRC_VER, VER = "v041", "v042"
V = Vector
sys.path.insert(0, str(HERE))
import interior_kit as IK  # noqa: E402

IK.RS = RS
T = {}
SKIPPED = {}


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


def fz(x, y, deck="lower"):
    t = T["floor_lo"] if deck == "lower" else T["floor_gun"]
    hit = t.ray_cast(V((x, y, 6.0 if deck == "lower" and False else (2.9 if deck == "lower" else 7.0))), V((0, 0, -1)), 6.0)
    return hit[0].z if hit[0] is not None else (1.1 if deck == "lower" else 3.3)


def cz(x, y):
    hit = T["ceil_lo"].ray_cast(V((x, y, fz(x, y) + 0.3)), V((0, 0, 1)), 4.0)
    return hit[0].z if hit[0] is not None else fz(x, y) + 2.0


def halfw(x, z):
    hit = T["hull"].ray_cast(V((x, 0.0, z)), V((0, 1, 0)), 8.0)
    return hit[0].y if hit[0] is not None else 3.0


def try_add(dst, key, build):
    """build(bm) geçici bmesh'e çizer; engellerle çakışmıyorsa dst'ye eklenir."""
    tmp = bmesh.new()
    build(tmp)
    if len(tmp.faces) == 0:
        tmp.free()
        return False
    tree = BVHTree.FromBMesh(tmp)
    if T["obst"].overlap(tree):
        SKIPPED[key] = SKIPPED.get(key, 0) + 1
        tmp.free()
        return False
    me = bpy.data.meshes.new("_tmp")
    tmp.to_mesh(me)
    tmp.free()
    dst.from_mesh(me)
    bpy.data.meshes.remove(me)
    return True


def try_shift(dst, key, make, shifts=(0.0, 0.35, -0.35, 0.7, -0.7)):
    """make(dx) → build(bm) — çakışırsa X yönünde kaydırarak yeniden dener."""
    for dx in shifts:
        before = SKIPPED.get(key, 0)
        if try_add(dst, key, make(dx)):
            SKIPPED[key] = before
            return True
        SKIPPED[key] = before
    SKIPPED[key] = SKIPPED.get(key, 0) + 1
    return False


# ------------------------------------------------------------------ 1. mürettebat yatakhanesi (hamak)
def crew_berth(M, col):
    bm = bmesh.new()
    hung = rolled = 0
    k = 0
    for x0 in (-11.1, -8.2, -5.3, -2.4):
        x1 = x0 + 2.6
        for s in (1, -1):
            for r in range(7):
                y = s * (0.95 + 0.6 * r)
                zc = min(cz(x0, y), cz(x1, y)) - 0.01
                if abs(y) > min(halfw(x0, zc - 0.6), halfw(x1, zc - 0.6)) - 0.55:
                    continue
                k += 1
                if (k * 7) % 10 < 7:                           # ~%70 asılı (nöbet dışı uyuyan vardiya)
                    ok = try_shift(bm, "hammock", lambda dx, x0=x0, x1=x1, y=y: (lambda b: _hung(b, x0 + dx, x1 + dx, y, min(cz(x0 + dx, y), cz(x1 + dx, y)) - 0.01)),
                                   shifts=(0.0, 0.25, -0.25))
                    hung += ok
                else:
                    ok = try_shift(bm, "hammock_rolled", lambda dx, x0=x0, x1=x1, y=y: (lambda b: _rolled(b, x0 + dx, x1 + dx, y, min(cz(x0 + dx, y), cz(x1 + dx, y)) - 0.01)),
                                   shifts=(0.0, 0.25, -0.25))
                    rolled += ok
    IK.finish("MOD_CREW_HAMMOCKS_A", bm, [M["linen"], M["rope"], M["iron"]], col,
              {"room": "crew_berth", "interact": "sleep", "hung": hung, "rolled": rolled,
               "note": "Ek Cilt II s. 95: hamak/vardiya; asılı = nöbet dışı uyuyan vardiya, sarılı = nöbetteki vardiya"})
    return {"hung": hung, "rolled": rolled}


def _hooks(b, pts):
    for p in pts:                                            # kanca: düz sap + yumuşak yay
        arc = [p + V((0.025 - 0.025 * math.cos(a), 0, -0.05 - 0.025 * math.sin(a))) for a in [math.pi * i / 10 for i in range(11)]]
        IK.tube(b, [p, p + V((0, 0, -0.03))] + arc, 0.007, mat=2, seg=8)


def _hung(b, x0, x1, y, zc):
    p0, p1 = V((x0, y, zc - 0.08)), V((x1, y, zc - 0.08))
    _hooks(b, [V((x0, y, zc)), V((x1, y, zc))])
    IK.hammock(b, p0, p1, sag=0.26, width=0.60, mat_cloth=0, mat_rope=1)


def _rolled(b, x0, x1, y, zc):
    _hooks(b, [V((x0 + 0.6, y, zc)), V((x1 - 0.6, y, zc))])
    zr = zc - 0.24
    IK.rolled_hammock(b, V((x0 + 0.75, y, zr)), V((x1 - 0.75, y, zr)), 0.11, mat_cloth=0, mat_rope=1)
    for xx in (x0 + 0.62, x1 - 0.62):
        IK.tube(b, [V((xx, y, zc - 0.08)), V((xx + (0.12 if xx < x1 - 1 else -0.12), y, zr + 0.05))], 0.006, mat=1, seg=6)


# ------------------------------------------------------------------ 2. yemek bölümü
def mess(M, col):
    bm = bmesh.new()
    n = 0
    for x in (1.6, 3.0, 5.6, 8.9):
        for s in (1, -1):
            z = fz(x, s * 3.5)
            yo = halfw(x, z + 0.7) - 0.12
            yi = yo - 1.5
            ok = try_shift(bm, "mess_table", lambda dx, x=x, s=s, yo=yo, yi=yi: (lambda b: _table(b, x + dx, s, fz(x + dx, s * (yo + yi) / 2), yo, yi)))
            n += ok
    IK.finish("MOD_CREW_MESS_A", bm, [M["oak"], M["rope"], M["iron"], M["pewter"]], col,
              {"room": "crew_mess", "interact": "eat", "tables": n})
    return {"tables": n}


def _table(b, x, s, z, yo, yi):
    yc = s * (yo + yi) / 2
    L = yo - yi
    IK.box(b, (x, yc, z + 0.72), (0.52, L, 0.04), r=0.01, mat=0)                         # tabla
    IK.box(b, (x, s * (yo - 0.03), z + 0.66), (0.40, 0.05, 0.08), r=0.008, mat=0)          # bordaya çıta
    for dx in (-0.2, 0.2):
        IK.tube(b, [V((x + dx, s * (yi + 0.05), z + 0.74)), V((x + dx, s * (yi + 0.05), cz(x + dx, s * (yi + 0.05)) - 0.02))], 0.007, mat=1, seg=6)
    for dx in (-0.55, 0.55):                                                              # iki yanda sıra
        IK.box(b, (x + dx, yc, z + 0.43), (0.26, L - 0.1, 0.04), r=0.008, mat=0)
        for yy in (s * (yi + 0.12), s * (yo - 0.15)):
            IK.box(b, (x + dx, yy, z + 0.21), (0.20, 0.04, 0.42), r=0.006, mat=0)
    for k in range(3):                                                                     # kalay tabak + maşrapa
        yy = s * (yi + 0.3 + 0.45 * k)
        IK.lathe(b, [(0.0, 0.0), (0.09, 0.0), (0.11, 0.02), (0.0, 0.012)], V((x - 0.12, yy, z + 0.74)), mat=3)
        IK.lathe(b, [(0.0, 0.0), (0.04, 0.0), (0.042, 0.11), (0.0, 0.10)], V((x + 0.14, yy, z + 0.74)), mat=3)


# ------------------------------------------------------------------ 3. subay odası (gunroom)
def gunroom(M, col):
    bm = bmesh.new()
    xs = (-17.6, -14.9, -12.1)
    rep = {"cabins": 0}
    for s in (1, -1):
        z = fz(-15.0, s * 2.2)
        zc = cz(-15.0, s * 2.2) - 0.02
        # boyuna perde (kapı aralıklı): iki kabin
        for a, b_ in ((xs[0], xs[1]), (xs[1], xs[2])):
            door = (b_ - a) * 0.5
            IK.curtain(bm, (a, s * 2.2), (a + door - 0.35, s * 2.2), z + 0.02, zc, folds=6, depth=0.03, mat=0)
            IK.curtain(bm, (a + door + 0.35, s * 2.2), (b_, s * 2.2), z + 0.02, zc, folds=6, depth=0.03, mat=0)
            IK.cyl(bm, (a, s * 2.2, zc - 0.03), (b_, s * 2.2, zc - 0.03), 0.018, mat=2)
        for xx in xs:                                                                       # enine perde
            w = halfw(xx, z + 1.0) - 0.05
            IK.curtain(bm, (xx, s * 2.2), (xx, s * w), z + 0.02, zc, folds=5, depth=0.03, mat=0)
        for a, b_ in ((xs[0], xs[1]), (xs[1], xs[2])):
            xm = (a + b_) / 2
            w = halfw(xm, z + 1.0)
            ym = s * (2.2 + w) / 2
            ok = try_shift(bm, "officer_cot", lambda dx, xm=xm, ym=ym, s=s: (lambda b: _cot(b, xm + dx, ym, None, None, s)))
            rep["cabins"] += ok
    # orta sofra + sıralar
    z = fz(-15.0, 0.0)
    ok = try_add(bm, "gunroom_table", lambda b: _gun_table(b, z))
    rep["table"] = ok
    ob = IK.finish("MOD_GUNROOM_A", bm, [M["screen"], M["linen"], M["iron"], M["oak"], M["rope"]], col,
                   {"room": "gunroom", "clear_for_action": "perdeler savaşta toplanır"})
    return rep


def _cot(b, xm, ym, z, zc, s):
    L, W = 1.85, 0.72
    z = fz(xm, ym)
    IK.box(b, (xm, ym, z + 1.0), (L, W, 0.30), r=0.05, mat=1)                                # kanvas asma yatak
    for dx in (-L / 2, L / 2):
        IK.cyl(b, (xm + dx * 0.97, ym - W / 2, z + 1.12), (xm + dx * 0.97, ym + W / 2, z + 1.12), 0.018, mat=3)
        top = V((xm + dx * 0.6, ym, 0))
        top.z = cz(top.x, top.y) - 0.02
        for dy in (-W / 2, W / 2):
            IK.tube(b, [V((xm + dx * 0.97, ym + dy, z + 1.12)), top], 0.006, mat=4, seg=6)
    zs = fz(xm, ym - s * 0.15) - 0.005
    IK.box(b, (xm, ym - s * 0.15, zs + 0.22), (0.7, 0.42, 0.44), r=0.02, mat=3)             # sandık


def _gun_table(b, z):
    IK.box(b, (-15.0, 0.0, z + 0.74), (3.6, 0.9, 0.05), r=0.012, mat=3)
    for dx in (-1.5, 1.5):
        IK.box(b, (-15.0 + dx, 0.0, z + 0.36), (0.08, 0.7, 0.72), r=0.01, mat=3)
    for dy in (-0.75, 0.75):
        IK.box(b, (-15.0, dy, z + 0.43), (3.2, 0.28, 0.04), r=0.01, mat=3)
        for dx in (-1.3, 1.3):
            IK.box(b, (-15.0 + dx, dy, z + 0.21), (0.05, 0.22, 0.42), r=0.006, mat=3)


# ------------------------------------------------------------------ 4. revir
def sickbay(M, col):
    bm = bmesh.new()
    x = 14.2
    z = fz(15.5, 0.0)
    zc = cz(x, 0.0) - 0.02
    w = halfw(x, z + 1.0) - 0.05
    IK.curtain(bm, (x, -w), (x, -0.45), z + 0.02, zc, folds=8, depth=0.035, mat=0)
    IK.curtain(bm, (x, 0.45), (x, w), z + 0.02, zc, folds=8, depth=0.035, mat=0)
    IK.cyl(bm, (x, -w, zc - 0.03), (x, w, zc - 0.03), 0.018, mat=2)
    rep = {"cots": 0}
    for s in (1, -1):
        ym = s * 1.15
        zc2 = cz(15.5, ym)
        ok = try_shift(bm, "sick_cot", lambda dx, ym=ym, s=s: (lambda b: _cot(b, 15.5 + dx, ym, None, None, s)))
        rep["cots"] += ok
    zz = fz(16.9, 0.0)
    rep["chest"] = try_add(bm, "surgeon_chest", lambda b: (IK.box(b, (16.9, 0.0, zz + 0.25), (0.5, 0.9, 0.5), r=0.02, mat=3),
                                                          IK.box(b, (16.9, 0.0, zz + 0.51), (0.52, 0.92, 0.03), r=0.01, mat=5),
                                                          IK.bucket(b, (16.9, 0.75, zz), 0.13, 0.26, mat=3, band=2)))
    IK.finish("MOD_SICKBAY_A", bm, [M["screen"], M["linen"], M["iron"], M["oak"], M["rope"], M["brass"]], col,
              {"room": "sickbay", "interact": "treat_wounded",
               "note": "Ek Cilt II s. 97: hastane ayrı fiziksel alan; baş tarafı, havadar"})
    return rep


# ------------------------------------------------------------------ 4b. çırak yatakhanesi (ayrı bölme)
def junior_dorm(M, col):
    """Alt güverte, ocak/atölyeler ile revir arası (x 12,0…14,15), pruva direğinin iki yanı: kanvas perdeli ayrı
    bölme, her yanda iki katlı ranza + sandıklar, ders/harita tahtası. Subay odasından ve kaptan dairesinden ayrı."""
    bm = bmesh.new()
    x0, x1 = 12.0, 14.15
    rep = {"bunks": 0}
    z = fz(13.0, 0.0)
    zc = cz(x0, 1.5) - 0.02
    w = halfw(x0, z + 1.0) - 0.05
    IK.curtain(bm, (x0, -w), (x0, -0.75), z + 0.02, zc, folds=7, depth=0.03, mat=0)
    IK.curtain(bm, (x0, 0.75), (x0, w), z + 0.02, zc, folds=7, depth=0.03, mat=0)
    IK.cyl(bm, (x0, -w, zc - 0.03), (x0, w, zc - 0.03), 0.018, mat=2)
    for s in (1, -1):
        def bunk(b, dx, inset, s=s):
            xa, xb = x0 + 0.12 + dx, x1 - 0.08 + dx
            xm = (xa + xb) / 2
            L = xb - xa
            zz = fz(xm, s * 3.2) - 0.005
            yo = halfw(xm, zz + 0.9) - inset
            yi = yo - 0.78
            ym = s * (yo + yi) / 2
            for h in (0.32, 1.22):                                            # iki kat
                IK.box(b, (xm, ym, zz + h), (L, 0.78, 0.06), r=0.012, mat=3)
                IK.box(b, (xm, ym, zz + h + 0.08), (L - 0.08, 0.70, 0.10), r=0.04, mat=1)
                IK.box(b, (xm, s * (yi + 0.02), zz + h + 0.14), (L, 0.04, 0.22), r=0.01, mat=3)
            for xx in (xa + 0.04, xb - 0.04):
                IK.box(b, (xx, s * (yi + 0.04), zz + 0.9), (0.07, 0.07, 1.8), r=0.012, mat=3)
            IK.box(b, (xm, s * (yi - 0.28), zz + 0.2), (0.62, 0.38, 0.40), r=0.02, mat=3)   # sandık
        ok = False
        for inset in (0.08, 0.30, 0.55, 0.80):
            ok = try_shift(bm, "junior_bunk", lambda dx, inset=inset: (lambda b: bunk(b, dx, inset)), shifts=(0.0, -0.15, 0.15))
            if ok:
                SKIPPED["junior_bunk"] = 0
                rep.setdefault("inset_m", []).append(inset)
                break
        rep["bunks"] += 2 * ok
    zb = fz(x0 + 0.05, -1.3)
    rep["board"] = try_add(bm, "junior_board", lambda b: (IK.box(b, (x0 + 0.06, -1.3, zb + 1.35), (0.03, 0.9, 0.62), r=0.006, mat=3),
                                                        IK.box(b, (x0 + 0.08, -1.3, zb + 1.35), (0.01, 0.8, 0.52), r=0.003, mat=4)))
    IK.finish("MOD_JUNIOR_DORM_A", bm, [M["screen"], M["linen"], M["iron"], M["oak"], bpy.data.materials["MAT_Paper_Chart"]], col,
              {"room": "junior_berth", "interact": "rest_study",
               "note": "Ek Cilt II s. 99: genç CharacterID çırak rıhtımı; kullanıcı: subay kabininden ayrı"})
    return rep


# ------------------------------------------------------------------ 5. atölyeler
def workshops(M, col):
    bm = bmesh.new()
    rep = {}
    x = 10.1
    for s, kind in ((-1, "carpenter"), (1, "sailmaker")):
        w = halfw(x, fz(x, s * 3.8) + 0.8)
        yb = s * (w - 0.45)
        z = min(fz(x - 1.1, yb - s * 0.6), fz(x + 1.1, yb - s * 0.6), fz(x, yb)) - 0.005
        if kind == "carpenter":
            rep[kind] = try_add(bm, kind, lambda b, z=z, yb=yb, s=s: _carpenter(b, x, yb, z, s))
        else:
            rep[kind] = try_add(bm, kind, lambda b, z=z, yb=yb, s=s: _sailmaker(b, x, yb, z, s))
    IK.finish("MOD_WORKSHOPS_A", bm, [M["oak"], M["iron"], M["linen"], M["rope"]], col,
              {"room": "workshops", "interact": "repair", "note": "Ek Cilt II s. 97: atölye alanları (marangoz, yelkenci)"})
    return rep


def _carpenter(b, x, yb, z, s):
    IK.box(b, (x, yb, z + 0.82), (2.0, 0.62, 0.08), r=0.012, mat=0)
    for dx in (-0.9, 0.9):
        for dy in (-0.25, 0.25):
            IK.box(b, (x + dx, yb + dy, z + 0.39), (0.08, 0.08, 0.78), r=0.01, mat=0)
    IK.box(b, (x + 0.75, yb - s * 0.36, z + 0.86), (0.18, 0.12, 0.16), r=0.01, mat=1)           # mengene
    IK.cyl(b, (x + 0.75, yb - s * 0.43, z + 0.88), (x + 0.75, yb - s * 0.62, z + 0.88), 0.012, mat=1)
    IK.box(b, (x - 0.3, yb, z + 0.87), (0.6, 0.12, 0.02), r=0.004, mat=1)                      # testere
    for k in range(3):                                                                          # yedek kereste
        IK.box(b, (x, yb + s * 0.05, z + 0.08 + 0.09 * k), (2.3, 0.22, 0.08), r=0.01, mat=0)


def _sailmaker(b, x, yb, z, s):
    IK.box(b, (x, yb, z + 0.45), (2.2, 0.36, 0.06), r=0.012, mat=0)
    for dx in (-1.0, 1.0):
        IK.box(b, (x + dx, yb, z + 0.21), (0.07, 0.30, 0.42), r=0.01, mat=0)
    for k in range(3):                                                                          # kanvas topları
        IK.cyl(b, (x - 0.9 + 0.62 * k, yb - s * 0.55, z + 0.15), (x - 0.35 + 0.62 * k, yb - s * 0.55, z + 0.15), 0.14, mat=2)
    IK.box(b, (x + 0.2, yb, z + 0.52), (1.2, 0.30, 0.06), r=0.03, mat=2)                        # işlenen yelken parçası


# ------------------------------------------------------------------ 6. ocak (galley) + su
def galley(M, col):
    bm = bmesh.new()
    x, y = 10.7, 0.0
    z = fz(x, y)
    zc = cz(x, y)
    gz = fz(x, y, deck="gun")
    rep = {}

    def stove(b):
        IK.box(b, (x, y, z + 0.45), (1.40, 1.20, 0.90), r=0.02, mat=0)                           # tuğla gövde
        IK.box(b, (x, y, z + 0.93), (1.46, 1.26, 0.06), r=0.012, mat=1)                          # demir üst levha
        IK.box(b, (x - 0.71, y, z + 0.38), (0.04, 0.55, 0.40), r=0.008, mat=1)                   # ocak kapağı
        for dy in (-0.3, 0.3):                                                                   # bakır kazanlar
            body = [(0.0, 0.0)] + [(0.24 + 0.04 * math.sin(math.pi / 2 * t), 0.05 * t) for t in [i / 6 for i in range(7)]] \
                + [(0.28, 0.38), (0.27, 0.395), (0.26, 0.40), (0.0, 0.40)]
            IK.lathe(b, body, V((x + 0.1, y + dy, z + 0.96)), mat=2)
            lid = [(0.0, 0.0), (0.27, 0.0)] + [(0.27 - 0.24 * t, 0.07 * math.sin(math.pi / 2 * t)) for t in [i / 10 for i in range(1, 11)]] \
                + [(0.03, 0.08), (0.035, 0.12), (0.0, 0.13)]
            IK.lathe(b, lid, V((x + 0.1, y + dy, z + 1.36)), mat=2)
    rep["stove"] = try_add(bm, "galley_stove", stove)
    if rep["stove"]:                                   # baca: kiriş/güverte deliğinden geçtiği için çakışma testine girmez
        IK.cyl(bm, (x + 0.45, y, z + 0.96), (x + 0.45, y, gz + 1.7), 0.12, mat=1)
        IK.lathe(bm, [(0.0, 0.0), (0.16, 0.0), (0.2, 0.08), (0.0, 0.14)], V((x + 0.45, y, gz + 1.7)), mat=1)
        IK.lathe(bm, [(0.0, 0.0), (0.26, 0.0), (0.26, 0.03), (0.13, 0.05), (0.0, 0.05)], V((x + 0.45, y, gz)), mat=1)   # güverte yakası
    zz = fz(x - 1.3, 1.2)
    rep["water_cask"] = try_add(bm, "galley_water", lambda b: (_cask(b, (x - 1.3, 1.2, zz), 0.30, 0.8, M), IK.bucket(b, (x - 1.3, -1.1, zz), 0.14, 0.28, mat=3, band=1)))
    IK.finish("MOD_GALLEY_A", bm, [M["brick"], M["iron"], M["copper"], M["oak"]], col,
              {"room": "galley", "interact": "cook", "note": "Ek Cilt II s. 96: galley ve içme suyu noktası; baca üst güverteden çıkar"})
    return rep


def _cask(b, c, r, h, M):
    c = V(c)
    prof = [(0.0, 0.0), (r * 0.82, 0.0)] + [(r * (0.82 + 0.18 * math.sin(math.pi * t)), h * t) for t in [i / 12 for i in range(13)]] + [(0.0, h)]
    IK.lathe(b, prof, c, mat=3)
    for t in (0.12, 0.3, 0.7, 0.88):
        rr = r * (0.82 + 0.18 * math.sin(math.pi * t)) + 0.004
        IK.lathe(b, [(rr - 0.004, h * t - 0.015), (rr, h * t - 0.015), (rr, h * t + 0.015), (rr - 0.004, h * t + 0.015)], c, mat=1)


def deck_water_and_heads(M, col):
    bm = bmesh.new()
    rep = {"scuttlebutt": False}
    for (x, y) in ((3.2, -1.4), (3.2, 1.4), (-1.3, 1.9), (5.0, -1.5)):
        z = fz(x, y, deck="gun")

        def sb(b, x=x, y=y, z=z):
            _cask(b, (x, y, z), 0.36, 0.95, M)
            IK.box(b, (x, y, z + 0.965), (0.62, 0.62, 0.03), r=0.01, mat=3)
            IK.tube(b, [V((x + 0.1, y, z + 0.99)), V((x + 0.25, y, z + 1.02)), V((x + 0.4, y + 0.05, z + 1.05))], 0.012, mat=1, seg=8)
            IK.lathe(b, [(0.0, 0.0), (0.05, 0.0), (0.055, 0.08), (0.0, 0.07)], V((x - 0.1, y + 0.1, z + 0.98)), mat=4)
        if try_add(bm, "scuttlebutt", sb):
            rep["scuttlebutt"] = [x, y]
            T["water_xy"] = (x, y, z)
            break
    rep["heads"] = 0
    for s in (1, -1):
        x, y = 18.9, s * 1.35
        z = fz(x, y, deck="gun")

        def seat(b, x=x, y=y, z=z):
            IK.box(b, (x, y, z + 0.23), (0.62, 0.55, 0.46), r=0.02, mat=3)
            IK.lathe(b, [(0.12, 0.0), (0.16, 0.0), (0.16, 0.012), (0.12, 0.012)], V((x, y, z + 0.46)), mat=3)
        rep["heads"] += try_add(bm, "heads", seat)
    IK.finish("MOD_DECK_WATER_HEADS_A", bm, [M["oak"], M["iron"], M["linen"], M["oak"], M["pewter"]], col,
              {"room": "deck_services", "interact": "drink/sanitation",
               "note": "Ek Cilt II s. 96: içme suyu noktası (scuttlebutt) ve baş tuvaletleri"})
    return rep


# ------------------------------------------------------------------ 0. kaptan dairesi düzeltmesi (kullanıcı, v041 sonrası)
def fix_quarters(M, col):
    """Kullanıcı: "çırak rıhtımının kaptan kamarasında ne işi var; oradaki 2 topu da kaldır; toplam top 20+2 kalsın".
    - Kıç topları (MOD_CANNON_OTTOMAN_C_CHASE_STERN_P/S + namlu) ve soketleri silinir → 20 borda + 2 baş topu.
    - Çırak rıhtımı kaptan dairesinden çıkar (alt güvertede subay odası kabini S1'e taşınır, bkz. rooms()).
    - Sancak-ön bölme kalkar; çalışma masası + sandalye eski köşesine döner; yazı rafı kıç kasarası duvarına."""
    rep = {"removed": []}
    for n in [o.name for o in bpy.data.objects if o.name.startswith(("MOD_CANNON_OTTOMAN_C_CHASE_STERN", "SOCKET_CANNON_CHASE_STERN",
                                                                     "SOCK_CREW_CHASE_STERN", "MOD_CABIN_JUNIOR_BERTH_A",
                                                                     "ROOM_JUNIOR_BERTH", "SOCK_INTERIOR_JUNIOR_BERTH"))]:
        o = bpy.data.objects[n]
        me = o.data if o.type == "MESH" else None
        bpy.data.objects.remove(o, do_unlink=True)
        if me is not None and me.users == 0:
            bpy.data.meshes.remove(me)
        rep["removed"].append(n)
    # sancak bölmesi (y > 0) ve UCX'leri
    part = bpy.data.objects["MOD_CABIN_PARTITIONS_A"]
    bm = bmesh.new()
    bm.from_mesh(part.data)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if (mw(part) @ v.co).y > 0.3], context="VERTS")
    bm.to_mesh(part.data)
    bm.free()
    for o in [o for o in bpy.data.objects if o.name.startswith("MOD_CABIN_PARTITIONS_A_LOD")]:
        bpy.data.objects.remove(o, do_unlink=True)
    for n in ("UCX_MOD_CABIN_PARTITIONS_A_00", "UCX_MOD_CABIN_PARTITIONS_A_01", "UCX_MOD_CABIN_PARTITIONS_A_02"):
        o = bpy.data.objects.get(n)
        if o:
            bpy.data.objects.remove(o, do_unlink=True)
    # masa + sandalye eski köşeye (v041'deki taşımanın tersi: dx = +1.14)
    desk = bpy.data.objects["MOD_CABIN_DESK_A"]
    p0 = mw(desk).translation
    dz_desk = fz(p0.x + 1.14, p0.y, deck="gun") - fz(p0.x, p0.y, deck="gun")
    for n in ("MOD_CABIN_DESK_A", "SOCK_INTERIOR_DESK_A", "MOD_CABIN_CHAIR_A_DESK", "SOCK_INTERIOR_CHAIR_A_DESK",
              "MOD_OFFICE_FERMAN_BOX_A"):
        o = bpy.data.objects.get(n)
        if o:
            q = mw(o).translation
            o.location.x += 1.14
            o.location.z += dz_desk if n == "MOD_OFFICE_FERMAN_BOX_A" else fz(q.x + 1.14, q.y, deck="gun") - fz(q.x, q.y, deck="gun")
    rack = bpy.data.objects["MOD_OFFICE_LETTER_RACK_A"]
    rack.location.x += (-15.36 - 0.16) - (-16.55 - 0.04 - 0.14)
    # iki duvar da kıça (−X) bakar: yön aynı, yalnız öteleme
    for o in [o for o in bpy.data.objects if o.name.startswith(("MOD_OFFICE_LETTER_RACK_A_LOD", "MOD_OFFICE_FERMAN_BOX_A_LOD"))]:
        bpy.data.objects.remove(o, do_unlink=True)
    room = bpy.data.objects.get("ROOM_CAPTAIN_OFFICE")
    if room:
        room["contains"] = "harita/toplantı masası, çalışma masası (sancak-ön köşe), yazı rafı, ferman kutusu, büfe, sancak"
        room["note_v042"] = "kıç topları kaldırıldı (kullanıcı: toplam 20+2)"
    guns = [o for o in bpy.data.objects if o.type == "MESH" and o.data.name == "MOD_CANNON_OTTOMAN_C_BARREL"]
    rep["guns_total"] = len(guns)
    rep["guns_chase"] = sorted(o.name for o in guns if "CHASE" in o.name)
    return rep


# ------------------------------------------------------------------ oda kimlikleri
def rooms(col):
    out = []

    def R(name, lo, hi, cmp, label, stn, wtz, deck, extra=None):
        out.append(IK.room(name, lo, hi, col, cmp, label, stn, wtz, deck, extra).name)
    R("ROOM_CREW_BERTH", (-11.4, -5.3, 1.0), (0.0, 5.3, 3.2), "CMP_LOWER_MID_AFT", "Mürettebat Yatakhanesi", "STN_REST_WATCH",
      "WTZ_LOWER_MID", "lower_deck", {"rule": "Ek Cilt II s. 95 — MaximumEmergencyPersons ≠ SustainableCrewCapacity"})
    R("ROOM_CREW_MESS", (0.0, -5.3, 1.0), (8.3, 5.3, 3.3), "CMP_LOWER_MID_FWD", "Mürettebat Yemek Bölümü", "STN_MESS", "WTZ_LOWER_MID", "lower_deck")
    R("ROOM_GUNROOM", (-18.0, -2.2, 1.4), (-11.7, 2.2, 3.9), "CMP_LOWER_AFT", "Subay Odası (Gunroom)", "STN_OFFICERS_MESS", "WTZ_LOWER_AFT", "lower_deck")
    for s, tag in ((1, "S"), (-1, "P")):
        for i, (a, b) in enumerate(((-17.6, -14.9), (-14.9, -12.1)), 1):
            lo = (a, min(s * 2.2, s * 4.3), 1.4)
            hi = (b, max(s * 2.2, s * 4.3), 3.9)
            R(f"ROOM_OFFICER_CABIN_{tag}{i}", lo, hi, f"CMP_LOWER_AFT_{tag}{i}", f"Subay Kabini {tag}{i}", "STN_OFFICER_REST", "WTZ_LOWER_AFT", "lower_deck")
    R("ROOM_JUNIOR_BERTH", (12.0, -4.3, 1.4), (14.15, 4.3, 3.5), "CMP_LOWER_FWD_J", "Çırak Yatakhanesi", "STN_JUNIOR_BERTH", "WTZ_LOWER_FWD",
      "lower_deck", {"character_rule": "genç CharacterID (Vasiyet Yolcusu) — Ek Cilt II s. 99",
                     "note": "kullanıcı: kaptan dairesinde ve subay kabinleriyle iç içe olmaz → ayrı perdeli yatakhane (pruva direği iki yanı)"})
    R("ROOM_SICKBAY", (14.2, -3.4, 1.6), (17.6, 3.4, 3.6), "CMP_LOWER_FWD", "Revir", "STN_SURGEON", "WTZ_LOWER_FWD", "lower_deck",
      {"rule": "Ek Cilt II s. 97"})
    R("ROOM_WORKSHOP_CARPENTER", (8.6, -4.9, 1.2), (11.8, -2.6, 3.3), "CMP_LOWER_FWD_P", "Marangoz Atölyesi", "STN_CARPENTER", "WTZ_LOWER_FWD", "lower_deck")
    R("ROOM_WORKSHOP_SAILMAKER", (8.6, 2.6, 1.2), (11.8, 4.9, 3.3), "CMP_LOWER_FWD_S", "Yelkenci Atölyesi", "STN_SAILMAKER", "WTZ_LOWER_FWD", "lower_deck")
    R("ROOM_GALLEY", (9.4, -1.2, 1.2), (11.8, 1.6, 3.3), "CMP_LOWER_FWD_C", "Ocak (Galley)", "STN_COOK", "WTZ_LOWER_FWD", "lower_deck",
      {"rule": "Ek Cilt II s. 96", "fire_boundary": "tuğla ocak; baca üst güverteden"})
    if "water_xy" in T:
        x, y, z = T["water_xy"]
        R("STATION_WATER_SCUTTLEBUTT", (x - 0.5, y - 0.5, z), (x + 0.5, y + 0.5, z + 1.2), "CMP_GUN_MID", "İçme Suyu Noktası",
          "STN_WATER_POINT", "WTZ_UPPER", "gun_deck")
    R("ROOM_HEADS", (18.5, -1.8, 3.9), (19.4, 1.8, 5.8), "CMP_GUN_FWD", "Baş Tuvaletleri", "STN_SANITATION", "WTZ_UPPER", "gun_deck")
    return out


def mats():
    M = {"rope": bpy.data.materials["MAT_Rope_Tarred"], "iron": bpy.data.materials["MAT_Iron_Black"],
         "oak": IK.mat_wood(), "brass": bpy.data.materials["MAT_Brass"]}
    M["linen"] = IK.mat("MAT_Linen_Mattress", (0.62, 0.56, 0.45), 0.8)
    M["screen"] = IK.mat("MAT_Canvas_Screen", (0.55, 0.49, 0.38), 0.85)
    M["pewter"] = IK.mat("MAT_Pewter", (0.42, 0.42, 0.40), 0.35, 0.8)
    M["copper"] = IK.mat("MAT_Copper", (0.62, 0.30, 0.18), 0.35, 1.0)
    b = bpy.data.materials.get("MAT_Brick_Galley")
    if b is None:
        b = bpy.data.materials.new("MAT_Brick_Galley")
        b.use_nodes = True
        nt = b.node_tree
        bs = nt.nodes["Principled BSDF"]
        br = nt.nodes.new("ShaderNodeTexBrick")
        tc = nt.nodes.new("ShaderNodeTexCoord")
        nt.links.new(tc.outputs["Object"], br.inputs["Vector"])
        br.inputs["Color1"].default_value = (0.42, 0.14, 0.08, 1)
        br.inputs["Color2"].default_value = (0.32, 0.10, 0.06, 1)
        br.inputs["Mortar"].default_value = (0.55, 0.52, 0.46, 1)
        br.inputs["Scale"].default_value = 6.0
        nt.links.new(br.outputs["Color"], bs.inputs["Base Color"])
        bs.inputs["Roughness"].default_value = 0.85
        b["ue_note"] = "UE: tuğla deseni prosedürel (Brick Texture) → BC/N bake"
    M["brick"] = b
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
        big = max(w.z for w in ws) - min(w.z for w in ws)
        hide = (min(w.z for w in ws) > 2.95) or o.name in ("CORE_DECK_GUN", "CORE_DECK_BEAMS_UPPER", "CORE_HATCH_GRATING_MAIN",
                                                             "CORE_SHOT_RACKS", "CORE_KNEES_LOWER_DECK") \
            or o.name.startswith(("MOD_SAIL_", "MOD_RIG_", "MOD_FLAG_", "MOD_CANNON", "MOD_DECK_WATER", "MOD_CAPSTAN", "MOD_PUMP"))
        if hide:
            if o.animation_data:
                for fc in list(o.animation_data.drivers):
                    o.animation_data.drivers.remove(fc)
            o.hide_render = True
    for i, x in enumerate(range(-17, 18, 4)):
        lt = bpy.data.objects.new(f"L_ALT_{i}", bpy.data.lights.new(f"L_ALT_{i}", "POINT"))
        lt.data.energy, lt.data.shadow_soft_size, lt.data.color = 220, 0.4, (1.0, 0.84, 0.62)
        lt.location = (x, 0.0, 2.8)
        sc.collection.objects.link(lt)
    shots = (("alt_guverte_kic", V((-7.0, 0.0, 20.0)), V((-7.0, 0.0, 1.5)), 30),
             ("alt_guverte_bas", V((8.5, 0.0, 20.0)), V((8.5, 0.0, 1.5)), 30),
             ("yatakhane", V((-0.4, -3.8, 2.4)), V((-8.5, 1.5, 2.3)), 22),
             ("ocak_atolye", V((6.4, -3.4, 2.5)), V((11.2, 1.0, 1.9)), 24),
             ("subay_odasi", V((-11.9, -1.0, 2.8)), V((-16.5, 1.5, 2.2)), 22),
             ("cirak_yatakhanesi", V((11.2, -0.3, 2.7)), V((13.6, 3.4, 2.0)), 24))
    for name, loc, tgt, lens in shots:
        sc.camera = H.camera(sc, f"CAM42_{name}", loc, tgt, lens=lens)
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
    T["floor_lo"] = bvh(["CORE_DECK_LOWER"])
    T["floor_gun"] = bvh(["CORE_DECK_GUN"])
    T["ceil_lo"] = bvh(["CORE_DECK_GUN", "CORE_DECK_BEAMS_UPPER"])
    T["hull"] = bvh(["CORE_HULL_SHELL"])
    M0 = mats()
    pre = fix_quarters(M0, bpy.data.collections["24_MODULES_DECOR"])
    skip = ("CORE_DECK_", "CORE_HULL_SHELL", "UCX_", "CUT_", "ROOM_", "MOD_SAIL_", "MOD_FLAG_", "MOD_ORN_FRIEZE", "CORE_MOULDING",
            "CORE_WALE", "MOD_RIG_RUNNING", "MOD_RIG_STANDING", "MOD_RIG_STAYS")
    obst = []
    for o in bpy.data.objects:
        if o.type != "MESH" or "_LOD" in o.name or o.name.startswith(skip) or o.hide_get():
            continue
        ws = [mw(o) @ V(c) for c in o.bound_box]
        if min(w.z for w in ws) < 7.0 and max(w.z for w in ws) > 0.8:
            obst.append(o.name)
    obst += ["CORE_DECK_BEAMS_UPPER"]
    T["obst"] = bvh(obst)
    col = bpy.data.collections["24_MODULES_DECOR"]
    rcol = IK.ensure_col("35_ROOMS")
    M = mats()
    rep = {"obstacle_objects": len(obst)}
    rep["quarters_fix"] = pre
    rep["crew_berth"] = crew_berth(M, col)
    rep["mess"] = mess(M, col)
    rep["gunroom"] = gunroom(M, col)
    rep["sickbay"] = sickbay(M, col)
    rep["workshops"] = workshops(M, col)
    rep["junior_dorm"] = junior_dorm(M, col)
    rep["galley"] = galley(M, col)
    rep["deck"] = deck_water_and_heads(M, col)
    rep["skipped_for_clash"] = SKIPPED
    rep["rooms"] = rooms(rcol)
    new = {"MOD_CREW_HAMMOCKS_A", "MOD_CREW_MESS_A", "MOD_GUNROOM_A", "MOD_SICKBAY_A", "MOD_WORKSHOPS_A", "MOD_GALLEY_A",
           "MOD_DECK_WATER_HEADS_A", "MOD_JUNIOR_DORM_A", "MOD_CABIN_PARTITIONS_A", "MOD_OFFICE_LETTER_RACK_A", "MOD_OFFICE_FERMAN_BOX_A"}
    LODS.build_lods(sc, only=new)
    bpy.ops.wm.save_as_mainfile(filepath=str(out), compress=True)
    H.VERSION = VER
    ap = ROOT / "reports" / f"scene_audit_{VER}.json"
    arep = H.audit(sc, ap)
    arep["interior_v042"] = rep
    arep["pass"] = {"name": "pass_v042_lower_deck_life", "source": f"Blender/versions/{SHIP}_{SRC_VER}.blend"}
    ap.write_text(json.dumps(arep, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    qa = QA.audit(sc, top=60)
    (ROOT / "reports" / f"kalite_testi_{VER}.json").write_text(json.dumps(qa, indent=1, ensure_ascii=False), encoding="utf-8")
    print("V042", json.dumps(rep, ensure_ascii=False, default=str))
    print("V042 QA", json.dumps(qa["summary"], ensure_ascii=False))
    for r in [r for r in qa["objects"] if r["fail"] or r["floating_islands"]]:
        print(f"  HATA {r['name']} facet={r['facet_m']}m sag={r['worst_sag_mm']}mm havada={r['floating_islands'][:3]}")
    if "--no-render" not in sys.argv:
        render(sc)


if __name__ == "__main__":
    main()
