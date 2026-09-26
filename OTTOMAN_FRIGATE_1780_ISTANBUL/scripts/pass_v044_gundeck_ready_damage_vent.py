"""v044 — Kızıl Sancak iç düzeni 4: top güvertesi hazır servis dolapları, güverte başına 2 hasar kontrol istasyonu,
havalandırma (rüzgâr hortumu / windsail), oda kimlikleri. LOD'lar artık ayrı dosyada (`_LOD.blend`).

    python3.11 OTTOMAN_FRIGATE_1780_ISTANBUL/scripts/pass_v044_gundeck_ready_damage_vent.py [--no-render | --render-only]

Onaylı plan: reports/KIZIL_SANCAK_UYARLAMA_PLANI.md §4 (Gate A). Kaynak kurallar (kullanıcı tasarım paketi, Ek Cilt II):
- s. 112 / 115: cephanelik, hazırlama odası ve **hazır servis dolabı** ayrı fiziksel alanlar. Hazır dolap top başında,
  kapaklı ve sınırlı sayıda torba alır → top çiftleri arasında, bordaya dayalı kilitli sandık (6 torba [TAHMİN]).
- s. 87: hasar kontrol stokları fiziksel ve dağıtılmıştır → her güvertede kıç ve baş tarafta birer istasyon.
- s. 97: havalandırma → ana ambar ağzından alt güverteye inen kanvas rüzgâr hortumu; ızgarada kapaklı hortum ağzı.
Tarihî karşılık [İKİNCİL: Lavery, "The Arming and Fitting of English Ships of War 1600–1815"]: "windsail" — üstte
rüzgâra açık kanatlı ağız, çemberli kanvas hortum, ambar ağzından aşağı; top başında kapaklı barut kutuları.
Ölçüler oyuna uyarlanmış [TAHMİN].

Dosya boyutu: v043 ana blend 99,5 MB (GitHub sınırı 100 MB). ≈ 55 MB'ı türetilmiş LOD'lardı → v044'ten itibaren
`skills/tersane/scripts/lod_store.py` ile `<SHIP>_vNNN_LOD.blend` ayrı yazılır.
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


def _load(name, file):
    sp = importlib.util.spec_from_file_location(name, HERE / file)
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


P42 = _load("pass_v042", "pass_v042_lower_deck_life.py")
P43 = _load("pass_v043", "pass_v043_hold_magazine.py")
P31 = P42.P31
RS, QA, LODS, H = P31.RS, P31.QA, P31.LODS, P31.H
ROOT, SHIP = P31.ROOT, P31.SHIP
SRC_VER, VER = "v043", "v044"
V = Vector
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT.parent / "skills" / "tersane" / "scripts"))
import interior_kit as IK  # noqa: E402
import lod_store  # noqa: E402

IK.RS = RS
T = P42.T                  # P42 yardımcıları (fz, halfw) bu sözlüğü okur
SKIPPED = {}
HOLE = (-1.65, -0.85, -0.40, 0.40)     # ana ambar ızgarasında hortum ağzı (x0, x1, y0, y1)
WS_X, WS_Y, WS_R = -1.25, 0.0, 0.30


def mw(o):
    return o.matrix_basis.copy() if o.parent is None else o.matrix_world.copy()


def fits(build, mat_world, tree=None):
    """build(bm) yerel çizer; mat_world ile taşınmış kopya engellerle çakışmıyorsa True."""
    tmp = bmesh.new()
    build(tmp)
    bmesh.ops.transform(tmp, matrix=mat_world, verts=tmp.verts)
    ok = bool(tmp.faces) and not (tree or T["obst"]).overlap(BVHTree.FromBMesh(tmp))
    tmp.free()
    return ok


# ------------------------------------------------------------------ 1. hazır servis dolapları (top çiftleri arası)
def _locker(b):
    """Yerel: taban merkezde, sırt +y (bordaya), ön −y."""
    IK.box(b, (0, 0, 0.27), (0.62, 0.40, 0.46), r=0.012, mat=0)                  # gövde
    for y in (-0.15, 0.15):
        IK.box(b, (0, y, 0.02), (0.62, 0.06, 0.04), r=0.008, mat=0)               # kızak ayaklar
    IK.box(b, (0, 0, 0.528), (0.66, 0.44, 0.045), r=0.01, mat=1)                   # kızıl kapak
    IK.box(b, (0, 0, 0.503), (0.665, 0.445, 0.012), r=0.003, mat=2)               # bakır kapak kenarı (kıvılcımsız)
    IK.box(b, (0, -0.205, 0.465), (0.05, 0.014, 0.10), r=0.003, mat=3)            # asma kilit dili
    IK.box(b, (0, -0.216, 0.415), (0.048, 0.022, 0.055), r=0.006, mat=3)          # asma kilit
    for x in (-0.2, 0.2):
        IK.box(b, (x, 0.205, 0.49), (0.08, 0.014, 0.06), r=0.003, mat=3)          # menteşe
    IK.box(b, (0, -0.204, 0.30), (0.20, 0.008, 0.085), r=0.002, mat=5)            # pirinç levha
    for s in (-1, 1):                                                              # halat kulplar
        IK.tube(b, [V((s * 0.311, -0.10, 0.40)), V((s * 0.345, -0.08, 0.34)), V((s * 0.36, 0.0, 0.32)),
                    V((s * 0.345, 0.08, 0.34)), V((s * 0.311, 0.10, 0.40))], 0.012, mat=4)


def ready_lockers(M, icol):
    me = bpy.data.meshes.get("SM_PROP_READY_LOCKER_A")
    if me is None:
        bm = bmesh.new()
        _locker(bm)
        me = bpy.data.meshes.new("SM_PROP_READY_LOCKER_A")
        bm.to_mesh(me)
        bm.free()
        for m in (M["oak"], M["red"], M["copper"], M["iron"], M["rope"], M["brass"]):
            me.materials.append(m)
        IK.box_uv(me)
        for p in me.polygons:
            p.use_smooth = True
    guns = {}
    for o in bpy.data.objects:
        if o.type == "MESH" and o.data.name == "MOD_CANNON_OTTOMAN_C_BARREL" and "CHASE" not in o.name:
            t = mw(o).translation
            guns.setdefault(1 if t.y > 0 else -1, []).append(t.x)
    placed, names = [], []
    for s, xs in guns.items():
        xs.sort()
        for i in (1, 3, 5, 7):                     # 2-3, 4-5, 6-7, 8-9 top çiftleri arası: bordada 4, gemide 8
            if i + 1 >= len(xs):
                continue
            xm = 0.5 * (xs[i] + xs[i + 1])
            done = False
            for dx in (0.0, 0.25, -0.25, 0.45, -0.45):
                for inset in (0.28, 0.40, 0.55, 0.75, 1.0, 1.3):
                    x = xm + dx
                    z0 = P42.fz(x, s * 2.5, deck="gun")
                    y = s * (P42.halfw(x, z0 + 0.45) - inset)
                    zs = [P42.fz(x + ax, y + ay, deck="gun") for ax in (-0.31, 0.31) for ay in (-0.2, 0.2)]
                    z = max(zs) - 0.004
                    mat = Matrix.Translation((x, y, z)) @ Matrix.Rotation(0.0 if s > 0 else math.pi, 4, "Z")
                    if fits(_locker, mat):
                        tag = "S" if s > 0 else "P"
                        n = f"MOD_READY_LOCKER_{tag}_{len([p for p in placed if p[0] == tag]) + 1:02d}"
                        ob = bpy.data.objects.new(n, me)
                        ob.matrix_world = mat
                        icol.objects.link(ob)
                        ob["module"] = "ready_service_locker"
                        ob["interact"] = "ready_service_cartridges"
                        ob["capacity_cartridges"] = 6
                        ob["capacity_note"] = "sınırlı: 2 topun yaklaşık 3'er atımı [TAHMİN]; ikmal hazırlama odasından"
                        ob["rule"] = "Ek Cilt II s. 112/115: hazır servis dolabı cephanelik ve hazırlama odasından ayrı fiziksel alan"
                        ob["guns_served"] = f"{tag}_{i:02d},{tag}_{i + 1:02d}"
                        placed.append((tag, round(x, 2), round(y, 2), round(z, 2)))
                        names.append(n)
                        done = True
                        break
                if done:
                    break
            if not done:
                SKIPPED["ready_locker"] = SKIPPED.get("ready_locker", 0) + 1
    return {"placed": placed, "objects": names}


# ------------------------------------------------------------------ 2. hasar kontrol istasyonları (güverte başına 2)
def damage_stations(M, col):
    P43.T["obst"] = T["obst"]
    rep = {}
    groups = {
        ("gun_deck", "GUN", "A"): [(-9.0, 1.5), (-9.0, -1.5), (-12.6, 1.4), (-12.6, -1.4), (-8.8, 2.4), (-8.8, -2.4)],
        ("gun_deck", "GUN", "F"): [(4.3, 1.6), (4.3, -1.6), (9.6, 1.5), (9.6, -1.5), (3.6, 2.2), (3.6, -2.2)],
        ("lower_deck", "LOWER", "A"): [(-11.0, 2.4), (-11.0, -2.4), (-5.2, 1.5), (-5.2, -1.5), (-9.5, 3.4), (-9.5, -3.4), (-3.4, 2.6), (-3.4, -2.6)],
        ("lower_deck", "LOWER", "F"): [(8.4, 1.8), (8.4, -1.8), (4.8, 1.6), (4.8, -1.6), (2.6, 2.4), (2.6, -2.4), (6.0, 3.2), (6.0, -3.2)],
    }
    for (deck, tag, end), cands in groups.items():
        name = f"MOD_DAMAGE_STATION_{tag}_{end}"
        dk = "gun" if deck == "gun_deck" else "lower"
        ok = None
        for (x, y) in cands:
            if P43.damage_station(M, col, name, x, y, lambda a, b, dk=dk: P42.fz(a, b, deck=dk), deck):
                ok = [x, y, round(P42.fz(x, y, deck=dk), 2)]
                break
        rep[name] = ok
        T.setdefault("dc", {})[name] = ok
    rep["skipped_candidates"] = dict(P43.SKIPPED)
    return rep


# ------------------------------------------------------------------ 3. havalandırma: rüzgâr hortumu
def cut_grating():
    g = bpy.data.objects["CORE_HATCH_GRATING_MAIN"]
    bm = bmesh.new()
    bm.from_mesh(g.data)
    Mi = g.matrix_world
    x0, x1, y0, y1 = HOLE
    kill = [f for f in bm.faces if x0 < (Mi @ f.calc_center_median()).x < x1 and y0 < (Mi @ f.calc_center_median()).y < y1]
    n = len(kill)
    bmesh.ops.delete(bm, geom=kill, context="FACES")
    loose = [v for v in bm.verts if not v.link_faces]
    bmesh.ops.delete(bm, geom=loose, context="VERTS")
    bm.to_mesh(g.data)
    bm.free()
    g.data.update()
    g["note_v044"] = "ızgarada rüzgâr hortumu ağzı açıldı (kasalı); UE: hortum kaldırılınca kapak tahtası (MOD_VENT_WINDSAIL_A içinde)"
    zt = max((Mi @ v.co).z for v in g.data.vertices)
    return {"faces_removed": n, "grating_top": round(zt, 3)}


def _windsail(b, z_bot, z_top, deck_z):
    x, y, r = WS_X, WS_Y, WS_R
    # alt: kasalı ağız çerçevesi (ızgara deliğini örter)
    x0, x1, y0, y1 = HOLE
    zt = deck_z
    w = 0.09
    IK.box(b, ((x0 + x1) / 2, y0 - w / 2 + 0.03, zt + 0.05), (x1 - x0 + 2 * w - 0.06, w, 0.10), r=0.008, mat=1)
    IK.box(b, ((x0 + x1) / 2, y1 + w / 2 - 0.03, zt + 0.05), (x1 - x0 + 2 * w - 0.06, w, 0.10), r=0.008, mat=1)
    IK.box(b, (x0 - w / 2 + 0.03, (y0 + y1) / 2, zt + 0.05), (w, y1 - y0 - 0.06, 0.10), r=0.008, mat=1)
    IK.box(b, (x1 + w / 2 - 0.03, (y0 + y1) / 2, zt + 0.05), (w, y1 - y0 - 0.06, 0.10), r=0.008, mat=1)
    # çemberli kanvas hortum (alt ucu genişleyen etek)
    z_mouth = z_top - 1.25
    prof = [(0.0, z_bot + 0.004), (r * 1.30, z_bot), (r * 1.30, z_bot + 0.012)]
    prof += [(r * (1.0 + 0.30 * (0.5 + 0.5 * math.cos(math.pi * t))), z_bot + 0.012 + 0.538 * t)     # yumuşak etek
             for t in [k / 14 for k in range(1, 15)]]
    zc = z_bot + 0.55
    while zc < z_mouth - 0.1:
        zn = min(zc + 0.9, z_mouth - 0.1)
        prof += [(r * 0.985, (zc + zn) / 2), (r, zn - 0.03)]
        zc = zn
    prof += [(r, z_mouth), (0.0, z_mouth)]
    IK.lathe(b, [(rr, zz - z_bot) for rr, zz in prof], V((x, y, z_bot)), mat=0)
    hz = z_bot + 0.55
    while hz < z_mouth - 0.2:                                                   # çemberler (tahta halka)
        IK.lathe(b, [(r - 0.002, -0.012), (r + 0.012, -0.012), (r + 0.016, 0.0), (r + 0.012, 0.012), (r - 0.002, 0.012)], V((x, y, hz)), mat=2)
        hz += 0.9
    # üst ağız: +x yönüne açık kanvas çatı (açıklık ±55°) + iki kanat
    seg = IK.seg_for(r, 24)
    a0, a1 = math.radians(55), math.radians(305)
    nz = 12
    rows = []
    for j in range(nz + 1):
        zz = z_mouth + (z_top - z_mouth) * j / nz
        row = []
        for i in range(seg + 1):
            a = a0 + (a1 - a0) * i / seg
            row.append(b.verts.new((x + r * math.cos(a), y + r * math.sin(a), zz)))
        rows.append(row)
    fs = []
    for j in range(nz):
        for i in range(seg):
            f = b.faces.new((rows[j][i], rows[j][i + 1], rows[j + 1][i + 1], rows[j + 1][i]))
            f.material_index = 0
            fs.append(f)
    # kanatlar: açıklığın iki kenarından dışa, hafif kavisli
    for side, a in ((1, a0), (-1, a1)):
        e = V((math.cos(a), math.sin(a), 0))
        out = (V((1, 0, 0)) * 0.75 + e * 0.65).normalized()
        wr = []
        nw = 10
        for j in range(nz + 1):
            zz = z_mouth + (z_top - z_mouth) * j / nz
            row = []
            for k in range(nw + 1):
                s = k / nw
                p = V((x, y, zz)) + e * r + out * (0.62 * s) + V((0, 0, 0.05 * math.sin(math.pi * s)))
                row.append(b.verts.new(p))
            wr.append(row)
        for j in range(nz):
            for k in range(nw):
                f = b.faces.new((wr[j][k], wr[j][k + 1], wr[j + 1][k + 1], wr[j + 1][k]))
                f.material_index = 0
                fs.append(f)
    bmesh.ops.solidify(b, geom=fs, thickness=0.006)
    # tepe: kapalı konik başlık
    IK.lathe(b, [(0.0, 0.0), (r + 0.02, 0.0), (r + 0.02, 0.02), (0.05, 0.30), (0.0, 0.31)], V((x, y, z_top - 0.005)), mat=0)
    IK.lathe(b, [(r + 0.005, -0.015), (r + 0.024, -0.015), (r + 0.028, 0.0), (r + 0.024, 0.015), (r + 0.005, 0.015)], V((x, y, z_top)), mat=2)


def windsail(M, col, z_bot, z_top, deck_z, mast_pt, guys):
    bm = bmesh.new()
    grating = None

    def build(b):
        _windsail(b, z_bot, z_top, deck_z)
    ok = fits(build, Matrix.Identity(4), T["ws_obst"])
    if not ok:
        SKIPPED["windsail"] = 1
        bm.free()
        hits = [n for n in T["ws_names"] if fits(build, Matrix.Identity(4), P42.bvh([n])) is False]
        return {"placed": False, "clash_with": hits}
    grating = cut_grating()
    deck_z = grating["grating_top"]
    build(bm)
    top = V((WS_X, WS_Y, z_top + 0.31))
    IK.tube(bm, [top, top.lerp(mast_pt, 0.5), mast_pt], 0.011, mat=3)          # asma halatı → mizana istralyası
    wt = []
    for side, a in ((1, math.radians(55)), (-1, math.radians(305))):
        e = V((math.cos(a), math.sin(a), 0))
        out = (V((1, 0, 0)) * 0.75 + e * 0.65).normalized()
        wt.append(V((WS_X, WS_Y, z_top - 1.25)) + e * WS_R + out * 0.62)
    for p0, g in zip(wt, guys):                                                 # kanat gergi halatları → güverte halkası
        IK.tube(bm, IK.catenary(p0, g + V((0, 0, 0.05)), 0.10, n=24), 0.008, mat=3)
        IK.lathe(bm, [(0.018, 0.0), (0.03, 0.0), (0.03, 0.012), (0.018, 0.012)], g, mat=4)       # göz-cıvata tabanı
        IK.cyl(bm, g + V((0, 0, 0.01)), g + V((0, 0, 0.05)), 0.008, mat=4)
    IK.finish("MOD_VENT_WINDSAIL_A", bm, [M["canvas_vent"], M["oak"], M["oak_light"], M["rope"], M["iron"]], col,
              {"module": "ventilation", "interact": "windsail_raise_lower",
               "note": "Ek Cilt II s. 97: havalandırma — ana ambar ağzından alt güverteye rüzgâr hortumu (windsail); "
                       "ağız +x (baş) yönüne; oyunda rüzgâra göre döndürülebilir (Z ekseni, merkez hortum ekseni)",
               "pivot_hint": [WS_X, WS_Y, z_top]})
    return {"placed": True, "z": [round(z_bot, 2), round(z_top + 0.31, 2)], "stay_point": [round(c, 2) for c in mast_pt], "grating": grating}


# ------------------------------------------------------------------ oda / istasyon kimlikleri
def rooms(col, lockers):
    out = []

    def R(name, lo, hi, cmp, label, stn, wtz, deck, extra=None):
        out.append(IK.room(name, lo, hi, col, cmp, label, stn, wtz, deck, extra).name)
    for tag, x, y, z in lockers["placed"]:
        n = len([o for o in out if o.startswith(f"STATION_READY_SERVICE_{tag}")]) + 1
        R(f"STATION_READY_SERVICE_{tag}{n}", (x - 0.45, y - 0.35, z), (x + 0.45, y + 0.35, z + 0.9), "CMP_GUN_MID",
          f"Hazır Servis Dolabı {tag}{n}", "STN_READY_SERVICE", "WTZ_UPPER", "gun_deck", {"rule": "Ek Cilt II s. 112/115"})
    labels = {"GUN_A": ("Top güvertesi kıç", "CMP_GUN_AFT", "WTZ_UPPER", "gun_deck"),
              "GUN_F": ("Top güvertesi baş", "CMP_GUN_FWD", "WTZ_UPPER", "gun_deck"),
              "LOWER_A": ("Alt güverte kıç", "CMP_LOWER_MID_AFT", "WTZ_LOWER_MID", "lower_deck"),
              "LOWER_F": ("Alt güverte baş", "CMP_LOWER_MID_FWD", "WTZ_LOWER_MID", "lower_deck")}
    for name, p in T.get("dc", {}).items():
        if not p:
            continue
        key = name.replace("MOD_DAMAGE_STATION_", "")
        lab, cmp, wtz, deck = labels[key]
        x, y, z = p
        R(f"STATION_DAMAGE_CONTROL_{key}", (x - 0.8, y - 0.5, z), (x + 0.8, y + 0.5, z + 1.2), cmp, f"Hasar Kontrol — {lab}",
          "STN_DAMAGE_CONTROL", wtz, deck, {"rule": "Ek Cilt II s. 87", "stock": "tapa, kalafat üstüpüsü, yedek kereste, kova"})
    h = bpy.data.objects.get("MOD_DAMAGE_STATION_HOLD_A")
    if h:
        bb = [mw(h) @ V(c) for c in h.bound_box]
        lo = V([min(v[i] for v in bb) for i in range(3)])
        hi = V([max(v[i] for v in bb) for i in range(3)])
        R("STATION_DAMAGE_CONTROL_HOLD", lo - V((0.3, 0.3, 0)), hi + V((0.3, 0.3, 0.2)), "CMP_HOLD_MID", "Hasar Kontrol — Ambar",
          "STN_DAMAGE_CONTROL", "WTZ_HOLD", "hold", {"rule": "Ek Cilt II s. 87"})
    if T.get("ws", {}).get("placed"):
        R("STATION_VENT_WINDSAIL", (WS_X - 0.6, -0.6, 2.4), (WS_X + 0.6, 0.6, 4.5), "CMP_GUN_MID", "Havalandırma — Rüzgâr Hortumu",
          "STN_VENTILATION", "WTZ_UPPER", "gun_deck", {"rule": "Ek Cilt II s. 97", "serves": "ROOM_CREW_BERTH, ROOM_CREW_MESS"})
    return out


def mats():
    M = {"rope": bpy.data.materials["MAT_Rope_Tarred"], "iron": bpy.data.materials["MAT_Iron_Black"],
         "brass": bpy.data.materials["MAT_Brass"], "oak": IK.mat_wood(),
         "red": bpy.data.materials.get("MAT_Panel_KizilLacquer") or IK.mat("MAT_Panel_KizilLacquer", (0.32, 0.045, 0.035), 0.42)}
    M["oak_light"] = IK.mat_wood("MAT_Wood_Pine_Spare", (0.55, 0.40, 0.22), (0.38, 0.26, 0.13), 0.7)
    M["copper"] = IK.mat("MAT_Copper", (0.62, 0.30, 0.18), 0.35, 1.0)
    M["oakum"] = IK.mat("MAT_Oakum", (0.22, 0.16, 0.09), 0.9)
    M["canvas_vent"] = IK.mat("MAT_Canvas_Windsail", (0.60, 0.55, 0.45), 0.85)
    return M


def render(sc):
    H.setup_render(sc, fast=True)
    sc.cycles.samples = 32
    out = ROOT / "renders" / VER
    out.mkdir(parents=True, exist_ok=True)

    def strip(o):
        if o.animation_data:
            for fc in list(o.animation_data.drivers):
                o.animation_data.drivers.remove(fc)
    shots_gun = (("top_guvertesi_ust", V((0.0, 0.0, 34.0)), V((0.0, 0.0, 3.3)), 30),
                 ("hazir_dolap", V((-4.6, 1.2, 4.9)), V((-2.4, 4.0, 3.6)), 24),
                 ("ruzgar_hortumu", V((-7.8, -3.6, 5.2)), V((-1.2, 0.0, 7.4)), 20),
                 ("hasar_top_guv", None, None, 24))
    # 1) top güvertesi: kıç/baş kasara, yelken ve arma gizli (üstten okunur)
    hidden = []
    for o in bpy.data.objects:
        if o.type != "MESH":
            continue
        ws = [o.matrix_world @ V(c) for c in o.bound_box]
        if o.name.startswith(("MOD_SAIL_", "MOD_FLAG_")) or (min(w.z for w in ws) > 5.3 and not o.name.startswith("MOD_RIG_MAST")):
            strip(o)
            o.hide_render = True
            hidden.append(o)
    dc = T.get("dc", {})
    for name, loc, tgt, lens in shots_gun:
        if name == "hasar_top_guv":
            p = dc.get("MOD_DAMAGE_STATION_GUN_A") or dc.get("MOD_DAMAGE_STATION_GUN_F")
            if not p:
                continue
            x, y, z = p
            loc, tgt = V((x + 2.6, y - math.copysign(2.4, y), z + 1.7)), V((x, y, z + 0.5))
        if name == "top_guvertesi_ust":
            for o in bpy.data.objects:
                if o.type == "MESH" and (o.name.startswith(("MOD_RIG_", "CORE_POOP", "CORE_FORECASTLE", "CORE_QUARTER")) or "ROUNDHOUSE" in o.name):
                    strip(o)
                    o.hide_render = True
        sc.camera = H.camera(sc, f"CAM44_{name}", loc, tgt, lens=lens)
        sc.render.filepath = str(out / f"{SHIP}_{VER}_{name}.png")
        bpy.ops.render.render(write_still=True)
    # 2) alt güverte hasar istasyonları (üst güverte gizli)
    for o in bpy.data.objects:
        if o.type != "MESH":
            continue
        ws = [o.matrix_world @ V(c) for c in o.bound_box]
        if (min(w.z for w in ws) > 2.95) or o.name in ("CORE_DECK_GUN", "CORE_DECK_BEAMS_UPPER", "CORE_HATCH_GRATING_MAIN", "CORE_SHOT_RACKS",
                                                        "CORE_KNEES_LOWER_DECK") or o.name.startswith(("MOD_RIG_", "MOD_CANNON", "MOD_PUMP", "MOD_CAPSTAN")):
            strip(o)
            o.hide_render = True
    for i, x in enumerate(range(-17, 18, 4)):
        lt = bpy.data.objects.new(f"L_ALT_{i}", bpy.data.lights.new(f"L_ALT_{i}", "POINT"))
        lt.data.energy, lt.data.shadow_soft_size, lt.data.color = 220, 0.4, (1.0, 0.84, 0.62)
        lt.location = (x, 0.0, 2.8)
        sc.collection.objects.link(lt)
    for key in ("MOD_DAMAGE_STATION_LOWER_A", "MOD_DAMAGE_STATION_LOWER_F"):
        p = dc.get(key)
        if not p:
            continue
        x, y, z = p
        name = "hasar_alt_" + key[-1].lower()
        sc.camera = H.camera(sc, f"CAM44_{name}", V((x + 2.4, y - math.copysign(2.2, y), z + 1.5)), V((x, y, z + 0.5)), lens=24)
        sc.render.filepath = str(out / f"{SHIP}_{VER}_{name}.png")
        bpy.ops.render.render(write_still=True)


def main():
    main_out = ROOT / "Blender" / "versions" / f"{SHIP}_{VER}.blend"
    if "--render-only" in sys.argv:
        bpy.ops.wm.open_mainfile(filepath=str(main_out))
        rep = json.loads((ROOT / "reports" / f"scene_audit_{VER}.json").read_text(encoding="utf-8"))["interior_v044"]
        T["dc"] = {k: v for k, v in rep["damage_control"].items() if k.startswith("MOD_")}
        return render(bpy.context.scene)
    if main_out.exists() or lod_store.lod_path(main_out).exists():
        raise SystemExit(f"{main_out} zaten var; versiyonlu kayıt üzerine yazılmaz.")
    src = ROOT / "Blender" / "versions" / f"{SHIP}_{SRC_VER}.blend"
    bpy.ops.wm.open_mainfile(filepath=str(src))
    sc = bpy.context.scene
    rep = {"lod_load": lod_store.load(src)}
    bpy.context.view_layer.update()
    T["floor_lo"] = P42.bvh(["CORE_DECK_LOWER"])
    T["floor_gun"] = P42.bvh(["CORE_DECK_GUN"])
    T["ceil_lo"] = P42.bvh(["CORE_DECK_GUN", "CORE_DECK_BEAMS_UPPER"])
    T["hull"] = P42.bvh(["CORE_HULL_SHELL"])
    skip = ("CORE_DECK_", "CORE_HULL_SHELL", "UCX_", "CUT_", "ROOM_", "MOD_SAIL_", "MOD_FLAG_", "MOD_ORN_FRIEZE", "CORE_MOULDING",
            "CORE_WALE", "MOD_RIG_RUNNING", "MOD_RIG_STANDING", "MOD_RIG_STAYS", "SOCK", "L_")
    obst, ws_obst = [], []
    for o in bpy.data.objects:
        if o.type != "MESH" or "_LOD" in o.name or o.hide_get():
            continue
        ws = [mw(o) @ V(c) for c in o.bound_box]
        lo = V([min(w[i] for w in ws) for i in range(3)])
        hi = V([max(w[i] for w in ws) for i in range(3)])
        if not o.name.startswith(skip) and lo.z < 7.0 and hi.z > 0.8:
            obst.append(o.name)
        if (not o.name.startswith(("UCX_", "CUT_", "MOD_SAIL_", "MOD_FLAG_", "CORE_HATCH_GRATING_MAIN", "CORE_DECK_GUN", "CORE_HULL_SHELL"))
                and lo.x < 1.8 and hi.x > -2.3 and lo.y < 1.2 and hi.y > -1.2 and lo.z < 16.5 and hi.z > 2.3):
            ws_obst.append(o.name)
    obst += ["CORE_DECK_BEAMS_UPPER"]
    T["obst"] = P42.bvh(obst)
    T["ws_obst"] = P42.bvh(ws_obst)
    T["ws_names"] = ws_obst
    col = bpy.data.collections["24_MODULES_DECOR"]
    icol = IK.ensure_col("27_GUNDECK_INSTANCES")
    rcol = IK.ensure_col("35_ROOMS")
    M = mats()
    rep["obstacle_objects"] = len(obst)
    rep["ready_lockers"] = ready_lockers(M, icol)
    rep["damage_control"] = damage_stations(M, col)
    g = bpy.data.objects["CORE_HATCH_GRATING_MAIN"]
    deck_z = max((g.matrix_world @ v.co).z for v in g.data.vertices)
    stay = bpy.data.objects["MOD_RIG_STAYS_A"]                                   # hortum mizana istralyasına asılır
    sz = [(stay.matrix_world @ v.co).z for v in stay.data.vertices
          if abs((stay.matrix_world @ v.co).x - WS_X) < 0.35 and abs((stay.matrix_world @ v.co).y) < 0.3 and (stay.matrix_world @ v.co).z < 12]
    stay_z = min(sz) if sz else 8.1
    mast_pt = V((WS_X, 0.0, stay_z - 0.01))
    guys = [V((-0.25, s * 2.25, P42.fz(-0.25, s * 2.25, deck="gun"))) for s in (1, -1)]
    T["ws"] = windsail(M, col, 2.45, stay_z - 0.90, deck_z, mast_pt, guys)
    rep["windsail"] = dict(T["ws"], obstacles=len(ws_obst))
    rep["skipped_for_clash"] = SKIPPED
    rep["rooms"] = rooms(rcol, rep["ready_lockers"])
    new = {"MOD_VENT_WINDSAIL_A", "CORE_HATCH_GRATING_MAIN"} | {n for n in rep["damage_control"] if n.startswith("MOD_")}
    new |= set(rep["ready_lockers"]["objects"][:1])
    for n in ("CORE_HATCH_GRATING_MAIN",):                                      # değişen geometri → eski LOD'lar silinir
        for o in [o for o in bpy.data.objects if o.name.startswith(n + "_LOD")]:
            bpy.data.objects.remove(o, do_unlink=True)
    rep["lods"] = len(LODS.build_lods(sc, only=new) or [])
    H.VERSION = VER
    ap = ROOT / "reports" / f"scene_audit_{VER}.json"
    arep = H.audit(sc, ap)
    arep["interior_v044"] = rep
    arep["pass"] = {"name": "pass_v044_gundeck_ready_damage_vent", "source": f"Blender/versions/{SHIP}_{SRC_VER}.blend"}
    qa = QA.audit(sc, top=60)
    (ROOT / "reports" / f"kalite_testi_{VER}.json").write_text(json.dumps(qa, indent=1, ensure_ascii=False), encoding="utf-8")
    rep["save"] = lod_store.save_split(main_out)
    ap.write_text(json.dumps(arep, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    print("V044", json.dumps(rep, ensure_ascii=False, default=str))
    print("V044 QA", json.dumps(qa["summary"], ensure_ascii=False))
    for r in [r for r in qa["objects"] if r["fail"] or r["floating_islands"]]:
        print(f"  HATA {r['name']} facet={r['facet_m']}m sag={r['worst_sag_mm']}mm havada={r['floating_islands'][:3]}")
    if "--no-render" not in sys.argv:
        render(sc)


if __name__ == "__main__":
    main()
