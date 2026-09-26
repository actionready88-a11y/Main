"""Pass v016 — Kaptan kamarası içi (kıç üstü altı), v015 üzerine.

Çalıştırma (depo kökünden):
    python3 OTTOMAN_FRIGATE_1780_ISTANBUL/scripts/pass_v016_cabin_interior.py [--no-render | --render-only]

Kullanıcı kararı (2026-09-26): Hull_B → top → arma → "kamara içi". Kamara v011'de kıç üstünün altında, kapısı belde.
Eşyalar ayrı modül nesneleridir (orijin = zemin soketi) ve takas edilebilir:
  masa + 4 sandalye, yazı masası + sandalye, asma yatak (cot), büfe, 2 sandık, kıç pencere sediri, asma fener,
  masada harita/pergel. Kıç kovalama toplarının mürettebat noktaları boş bırakılır (denetimle doğrulanır).
Ölçüler oynanış/tasarım TAHMİNİ (mobilya için tarihsel kaynak kullanılmadı).
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


P15 = _load("pass_v015", "pass_v015_rigset.py")
P14, P13 = P15.P14, P15.P13
P5, H, K, C3 = P13.P5, P13.H, P13.K, P15.C3
SRC_VER, VER = "v015", "v016"
ROOT, SHIP = H.ROOT, H.SHIP_ID
MANIFEST_VERSION = 14
P5.MANIFEST_VERSION = MANIFEST_VERSION
DWL = P13.DWL
V = Vector

# kamara iç sınırları (dünya); ön duvarın kıç yüzü ve kıç aynası iç yüzü (TAHMİN payları)
X_FWD = (P5.X_FRONT - 0.10) * K
LAYOUT = {  # ad: (x, y, dönüş derece) dünya — yerleşim kıç kovalama mürettebat noktalarına göre ayarlandı
    "TABLE": (-17.55, 0.0, 0.0),
    "CHAIR_1": (-18.62, 0.0, 0.0), "CHAIR_2": (-16.48, 0.0, 180.0),
    "CHAIR_3": (-17.05, 0.78, -90.0), "CHAIR_4": (-17.05, -0.78, 90.0),
    "DESK": (-15.76, 2.75, 180.0), "DESK_CHAIR": (-16.35, 2.75, 0.0),
    "COT": (-15.85, -2.35, 90.0),
    "SIDEBOARD": (-15.67, 1.20, 180.0),
    "CHEST_1": (-15.85, -2.35, 90.0),
    "BENCH": (-19.63, 0.0, 0.0),
    "LANTERN": (-17.55, 0.0, 0.0),
}


def mats():
    M = P15.materials()
    if "MAT_Furniture_Mahogany" not in bpy.data.materials:
        H.plank_material("MAT_Furniture_Mahogany", (0.20, 0.07, 0.035), (0.09, 0.03, 0.015), plank_w=0.35, rough=0.35, seam=0.0005, bump=0.05)
    if "MAT_Fabric_Crimson" not in bpy.data.materials:
        H.principled("MAT_Fabric_Crimson", (0.28, 0.03, 0.03), rough=0.9)
    if "MAT_Brass" not in bpy.data.materials:
        H.principled("MAT_Brass", (0.70, 0.52, 0.22), rough=0.3, metal=1.0)
    if "MAT_Canvas" not in bpy.data.materials:
        H.principled("MAT_Canvas", (0.62, 0.57, 0.46), rough=0.95)
    if "MAT_Paper_Chart" not in bpy.data.materials:
        H.principled("MAT_Paper_Chart", (0.74, 0.66, 0.50), rough=0.9)
    for k, n in (("maho", "MAT_Furniture_Mahogany"), ("fabric", "MAT_Fabric_Crimson"), ("brass", "MAT_Brass"),
                 ("canvas", "MAT_Canvas"), ("paper", "MAT_Paper_Chart")):
        M[k] = bpy.data.materials[n]
    return M


# --- Mesh yardımcıları (yerel, dünya metre; orijin zeminde) ----------------------------
def box(bm, x0, x1, y0, y1, z0, z1):
    P5.aabox(bm, x0, x1, y0, y1, z0, z1)


def turned_leg(bm, x, y, z0, h, r):
    prof = [(0.0, z0), (r * 0.8, z0), (r, z0 + 0.03), (r * 0.7, z0 + h * 0.15), (r * 0.9, z0 + h * 0.35), (r * 0.6, z0 + h * 0.55),
            (r * 0.75, z0 + h * 0.8), (r * 1.1, z0 + h * 0.86), (r * 1.1, z0 + h), (0.0, z0 + h)]
    P5.lathe(bm, prof, 10, Matrix.Translation((x, y, 0)))


def make_mesh(name, parts):
    merged = bmesh.new()
    mlist = []
    for idx, (b, mat) in enumerate(parts):
        bmesh.ops.recalc_face_normals(b, faces=b.faces)
        me = bpy.data.meshes.new("_tmp")
        b.to_mesh(me)
        b.free()
        me.polygons.foreach_set("material_index", [idx] * len(me.polygons))
        merged.from_mesh(me)
        bpy.data.meshes.remove(me)
        mlist.append(mat)
    me = bpy.data.meshes.new(name)
    merged.to_mesh(me)
    merged.free()
    for m in mlist:
        me.materials.append(m)
    me.set_sharp_from_angle(angle=math.radians(35))
    tmp = bpy.data.objects.new("_tmp_uv", me)
    H.build_uv_fallback(tmp)
    bpy.data.objects.remove(tmp)
    return me


def table_mesh(M):
    bw, bp, bb = bmesh.new(), bmesh.new(), bmesh.new()
    L, Wd, Ht = 1.70, 0.90, 0.76
    box(bw, -L / 2, L / 2, -Wd / 2, Wd / 2, Ht - 0.045, Ht)                  # tabla
    box(bw, -L / 2 + 0.06, L / 2 - 0.06, -Wd / 2 + 0.06, Wd / 2 - 0.06, Ht - 0.14, Ht - 0.045)   # etek
    for sx in (-1, 1):
        for sy in (-1, 1):
            turned_leg(bw, sx * (L / 2 - 0.10), sy * (Wd / 2 - 0.10), 0.0, Ht - 0.045, 0.045)
    box(bp, -0.45, 0.25, -0.30, 0.25, Ht, Ht + 0.004)                          # açık harita
    for k, (x, y) in enumerate(((0.45, 0.18), (0.55, -0.12))):                 # dürülmüş haritalar
        P5.lathe(bp, [(0.0, -0.30), (0.03, -0.30), (0.03, 0.30), (0.0, 0.30)], 10,
                 Matrix.Translation((x, y, Ht + 0.03)) @ Matrix.Rotation(math.radians(90), 4, "X"))
    for a in (-12, 12):                                                         # pergel
        box(bb, -0.10, 0.10, -0.004, 0.004, Ht + 0.004, Ht + 0.010)
        bb.verts.ensure_lookup_table()
        bmesh.ops.rotate(bb, cent=V((0, 0, Ht)), matrix=Matrix.Rotation(math.radians(a), 3, "Z"), verts=bb.verts[-8:])
    bmesh.ops.translate(bb, vec=(-0.05, 0.05, 0.0), verts=bb.verts)
    return make_mesh("MOD_CABIN_TABLE_A", [(bw, M["maho"]), (bp, M["paper"]), (bb, M["brass"])])


def chair_mesh(M):
    bw, bf = bmesh.new(), bmesh.new()
    S, Hs = 0.44, 0.45
    for sx in (-1, 1):
        for sy in (-1, 1):
            turned_leg(bw, sx * (S / 2 - 0.04), sy * (S / 2 - 0.04), 0.0, Hs - 0.04, 0.022)
    box(bw, -S / 2, S / 2, -S / 2, S / 2, Hs - 0.04, Hs)
    box(bf, -S / 2 + 0.03, S / 2 - 0.03, -S / 2 + 0.03, S / 2 - 0.03, Hs, Hs + 0.04)   # minder
    for sy in (-1, 1):                                                          # arkalık dikmeleri (−X tarafı)
        box(bw, -S / 2, -S / 2 + 0.04, sy * (S / 2 - 0.04) - 0.02, sy * (S / 2 - 0.04) + 0.02, Hs, Hs + 0.50)
    box(bw, -S / 2, -S / 2 + 0.035, -S / 2 + 0.04, S / 2 - 0.04, Hs + 0.42, Hs + 0.50)
    for k in (-1, 0, 1):
        box(bw, -S / 2 + 0.005, -S / 2 + 0.03, k * 0.10 - 0.025, k * 0.10 + 0.025, Hs + 0.06, Hs + 0.42)
    return make_mesh("MOD_CABIN_CHAIR_A", [(bw, M["maho"]), (bf, M["fabric"])])


def desk_mesh(M):
    bw, bb, bp = bmesh.new(), bmesh.new(), bmesh.new()
    L, Dp, Ht = 1.25, 0.65, 0.78
    box(bw, -Dp / 2, Dp / 2, -L / 2, L / 2, Ht - 0.04, Ht)
    for sy in (-1, 1):                                                          # iki çekmeceli ayak
        y0, y1 = sorted((sy * (L / 2), sy * (L / 2 - 0.40)))
        box(bw, -Dp / 2 + 0.02, Dp / 2 - 0.02, y0, y1, 0.0, Ht - 0.04)
        for k in range(3):
            z0 = 0.06 + k * 0.22
            box(bw, Dp / 2 - 0.02, Dp / 2 + 0.005, y0 + 0.03, y1 - 0.03, z0, z0 + 0.19)
            P5.lathe(bb, [(0.0, 0.0), (0.012, 0.0), (0.016, 0.02), (0.0, 0.03)], 8,
                     Matrix.Translation((Dp / 2 + 0.005, (y0 + y1) / 2, z0 + 0.095)) @ Matrix.Rotation(math.radians(90), 4, "Y"))
    box(bw, -Dp / 2 + 0.02, -Dp / 2 + 0.05, -L / 2 + 0.4, L / 2 - 0.4, 0.25, Ht - 0.04)   # arka pano
    box(bp, -0.15, 0.15, -0.25, 0.20, Ht, Ht + 0.03)                            # seyir defteri
    P5.lathe(bb, [(0.0, 0.0), (0.035, 0.0), (0.035, 0.05), (0.02, 0.07), (0.0, 0.07)], 10, Matrix.Translation((0.05, 0.40, Ht)))  # mürekkep hokkası
    return make_mesh("MOD_CABIN_DESK_A", [(bw, M["maho"]), (bb, M["brass"]), (bp, M["paper"])])


def cot_mesh(M, hang):
    bc, br, bw = bmesh.new(), bmesh.new(), bmesh.new()
    L, Wd = 1.90, 0.80
    zc = 0.85
    box(bc, -L / 2, L / 2, -Wd / 2, Wd / 2, zc - 0.20, zc)                     # kanvas beşik
    box(bw, -L / 2 - 0.03, -L / 2, -Wd / 2, Wd / 2, zc - 0.22, zc + 0.02)
    box(bw, L / 2, L / 2 + 0.03, -Wd / 2, Wd / 2, zc - 0.22, zc + 0.02)
    box(bc, -L / 2 + 0.05, -L / 2 + 0.45, -Wd / 2 + 0.06, Wd / 2 - 0.06, zc, zc + 0.10)   # yastık
    for sx in (-1, 1):
        for sy in (-1, 1):
            P15.tube(br, [V((sx * L / 2, sy * Wd / 2, zc)), V((sx * (L / 2 - 0.25), 0.0, hang))], 0.008, seg=4)
    return make_mesh("MOD_CABIN_COT_A", [(bc, M["canvas"]), (br, M["rope"]), (bw, M["maho"])])


def chest_mesh(M):
    bw, bi = bmesh.new(), bmesh.new()
    L, Wd, Ht = 0.95, 0.52, 0.50
    box(bw, -L / 2, L / 2, -Wd / 2, Wd / 2, 0.0, Ht - 0.10)
    box(bw, -L / 2 - 0.01, L / 2 + 0.01, -Wd / 2 - 0.01, Wd / 2 + 0.01, Ht - 0.10, Ht)       # kapak
    for x in (-L / 2 + 0.15, L / 2 - 0.15):
        box(bi, x - 0.025, x + 0.025, -Wd / 2 - 0.015, Wd / 2 + 0.015, -0.001, Ht + 0.005)
    for sx in (-1, 1):
        box(bi, sx * (L / 2 + 0.01) - 0.01, sx * (L / 2 + 0.01) + 0.01, -0.08, 0.08, Ht - 0.20, Ht - 0.17)
    box(bi, -0.04, 0.04, Wd / 2 + 0.01, Wd / 2 + 0.02, Ht - 0.16, Ht - 0.06)
    return make_mesh("MOD_CABIN_CHEST_A", [(bw, M["timber"]), (bi, M["iron"])])


def sideboard_mesh(M):
    bw, bb, bg = bmesh.new(), bmesh.new(), bmesh.new()
    L, Dp, Ht = 1.10, 0.48, 0.92
    box(bw, -Dp / 2, Dp / 2, -L / 2, L / 2, 0.08, Ht)
    box(bw, -Dp / 2 - 0.02, Dp / 2 + 0.03, -L / 2 - 0.02, L / 2 + 0.02, Ht, Ht + 0.035)
    box(bw, -Dp / 2 + 0.02, Dp / 2 - 0.02, -L / 2 + 0.02, L / 2 - 0.02, 0.0, 0.08)
    for sy in (-1, 1):                                                          # kapaklar
        y0, y1 = sorted((sy * 0.02, sy * (L / 2 - 0.03)))
        box(bw, Dp / 2, Dp / 2 + 0.02, y0, y1, 0.14, Ht - 0.06)
        P5.lathe(bb, [(0.0, 0.0), (0.01, 0.0), (0.014, 0.02), (0.0, 0.03)], 8,
                 Matrix.Translation((Dp / 2 + 0.02, sy * 0.06, Ht * 0.6)) @ Matrix.Rotation(math.radians(90), 4, "Y"))
    for k, y in enumerate((-0.30, -0.18, 0.25)):                                # sürahi ve kadehler
        r, h = (0.06, 0.24) if k == 0 else (0.03, 0.12)
        P5.lathe(bg, [(0.0, 0.0), (r * 0.7, 0.0), (r, h * 0.3), (r * 0.5, h * 0.8), (r * 0.6, h), (0.0, h)], 12,
                 Matrix.Translation((0.0, y, Ht + 0.035)))
    return make_mesh("MOD_CABIN_SIDEBOARD_A", [(bw, M["maho"]), (bb, M["brass"]), (bg, M["glass"])])


def bench_mesh(M, length):
    bw, bf = bmesh.new(), bmesh.new()
    Dp, Ht = 0.55, 0.45
    box(bw, -Dp / 2, Dp / 2, -length / 2, length / 2, 0.0, Ht - 0.05)
    for k in range(4):                                                          # dolap kapak panoları
        y = -length / 2 + (k + 0.5) * length / 4
        box(bw, Dp / 2, Dp / 2 + 0.015, y - length / 8 + 0.03, y + length / 8 - 0.03, 0.06, Ht - 0.10)
    box(bf, -Dp / 2 + 0.02, Dp / 2 - 0.02, -length / 2 + 0.02, length / 2 - 0.02, Ht - 0.05, Ht + 0.06)
    for k in range(3):
        y = -length / 3 + k * length / 3
        box(bf, -Dp / 2, -Dp / 2 + 0.14, y - 0.22, y + 0.22, Ht + 0.06, Ht + 0.42)    # yaslanma minderi
    return make_mesh("MOD_CABIN_STERN_BENCH_A", [(bw, M["maho"]), (bf, M["fabric"])])


def lantern_mesh(M, drop):
    bb, bg = bmesh.new(), bmesh.new()
    P15.tube(bb, [V((0, 0, 0)), V((0, 0, -drop))], 0.008, seg=4)                # zincir (basit)
    z = -drop
    P5.lathe(bb, [(0.0, z), (0.10, z), (0.12, z - 0.05), (0.02, z - 0.05)], 12, Matrix())
    for k in range(4):
        a = math.pi / 2 * k + math.pi / 4
        box(bb, 0.09 * math.cos(a) - 0.008, 0.09 * math.cos(a) + 0.008, 0.09 * math.sin(a) - 0.008, 0.09 * math.sin(a) + 0.008,
            z - 0.30, z - 0.05)
    P5.lathe(bb, [(0.0, z - 0.30), (0.11, z - 0.30), (0.11, z - 0.33), (0.0, z - 0.34)], 12, Matrix())
    P5.lathe(bg, [(0.0, z - 0.06), (0.075, z - 0.06), (0.075, z - 0.29), (0.0, z - 0.29)], 12, Matrix())
    return make_mesh("MOD_LANTERN_HANGING_A", [(bb, M["brass"]), (bg, M["lamp"])])


# --- Yerleşim ---------------------------------------------------------------------------
def floor_z(sc, dg, x, y):
    return P14.deck_hit(sc, dg, V((x, y, 4.75)))


def ceiling_z(sc, dg, x, y, zf):
    ok, loc, *_ = sc.ray_cast(dg, V((x, y, zf + 0.3)), V((0, 0, 1)), distance=4.0)
    return loc.z if ok else zf + 2.5


def place(col, col_s, name, me, x, y, rz, z, **props):
    ob = bpy.data.objects.new(name, me)
    col.objects.link(ob)
    ob.location = V((x, y, z))
    ob.rotation_euler = (0, 0, math.radians(rz))
    ob["module_family"] = "InteriorSet"
    ob["room"] = "captain_cabin"
    ob["socket"] = "SOCK_INTERIOR_" + name[len("MOD_CABIN_"):] if name.startswith("MOD_CABIN_") else "SOCK_INTERIOR_" + name
    for k, v in props.items():
        ob[k] = v
    P13.set_socket(ob["socket"], ob.location, col_s, shape="PLAIN_AXES", size=0.2, rot=(0, 0, math.radians(rz)),
                   module_family="InteriorSet", room="captain_cabin")
    return ob


def world_bbox(ob):
    pts = [ob.matrix_world @ V(c) for c in ob.bound_box]
    return (min(p.x for p in pts), max(p.x for p in pts), min(p.y for p in pts), max(p.y for p in pts),
            min(p.z for p in pts), max(p.z for p in pts))


S0_FIX = 0.006   # güverte kıç ucu: kabuk kalınlığı içinde biter (0,02 / 0,012'de aynayla arasında boşluk kalıyordu)


def fix_deck_gaps(core, ucx_col, M):
    """CORE_DECK_GUN ve CORE_DECK_LOWER kıç uçlarını aynaya uzat (mesh yerinde; modifier'lar korunur) + UCX dolgusu."""
    out = {}
    for name, s_old, zfn in (("CORE_DECK_GUN", 0.02, P13.zu), ("CORE_DECK_LOWER", 0.012, P13.zl)):
        ob = bpy.data.objects[name]
        s1 = 0.975 if name == "CORE_DECK_GUN" else 0.972
        tmp = H.deck_surface("_tmp_deck", S0_FIX, s1, zfn, core, M["deck"])
        P13.place(tmp)
        old = ob.data
        ob.data = tmp.data
        ob.data.name = name
        bpy.data.objects.remove(tmp, do_unlink=True)
        if old.users == 0:
            bpy.data.meshes.remove(old)
        x0 = P13.x_at(S0_FIX, zfn(S0_FIX)) * K
        x1 = P13.x_at(s_old, zfn(s_old)) * K
        pts = []
        for s in (S0_FIX, s_old + 0.004):
            z = zfn(s)
            x, y = H.hull_point(s, z)
            w = max(y - 0.24, 0.3)
            pts += [P13.W(V((x, yy, z + dz))) for yy in (-w, w) for dz in (0.0, -0.25)] + [P13.W(V((x, 0.0, z + 0.12)))]
        u = C3.convex(f"UCX_FILL_{name}", pts, ucx_col, "deck_gun" if name == "CORE_DECK_GUN" else "deck_lower")
        u["owner_mesh"] = "CORE_HULL_SHELL"
        out[name] = {"gap_closed_world_m": round(x1 - x0, 3), "ucx": "UCX_CORE_HULL_SHELL_* (dolgu, ucx_purpose=" + u["ucx_purpose"] + ")"}
    # UCX adlarını Hull Core düzeninde yeniden sırala
    core_ucx = sorted([o for o in ucx_col.objects if o.name.startswith("UCX_CORE_HULL_SHELL_")], key=lambda o: o.name)
    core_ucx += [o for o in ucx_col.objects if o.name.startswith("UCX_FILL_")]
    for i, o in enumerate(core_ucx):
        o.name = f"_tmp_ucx_{i}"
    for i, o in enumerate(core_ucx):
        o.name = o.data.name = f"UCX_CORE_HULL_SHELL_{i:02d}"
    return out


def main_build():
    sc = bpy.context.scene
    M = mats()
    C = {c.name: c for c in bpy.data.collections}
    col, col_s, ucx_col = C["24_MODULES_DECOR"], C["30_SOCKETS"], C["40_COLLISION"]
    gaps = fix_deck_gaps(C["10_HULL_CORE"], ucx_col, M)
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    zf = {k: floor_z(sc, dg, x, y) for k, (x, y, _) in LAYOUT.items()}
    miss = [k for k, v in zf.items() if v is None]
    assert not miss, f"zemin bulunamadı: {miss}"
    xt, yt, _ = LAYOUT["TABLE"]
    zc = ceiling_z(sc, dg, xt, yt, zf["TABLE"])
    xc, yc, _ = LAYOUT["COT"]
    zc_cot = ceiling_z(sc, dg, xc, yc, zf["COT"])
    stern_in = [o for o in bpy.data.objects if o.name == "CORE_HULL_SHELL"]
    obs = []
    t_me, c_me, d_me = table_mesh(M), chair_mesh(M), desk_mesh(M)
    obs.append(place(col, col_s, "MOD_CABIN_TABLE_A", t_me, *LAYOUT["TABLE"][:2], LAYOUT["TABLE"][2], zf["TABLE"], interact="chart_table"))
    for k in range(1, 5):
        x, y, r = LAYOUT[f"CHAIR_{k}"]
        obs.append(place(col, col_s, f"MOD_CABIN_CHAIR_A_{k:02d}", c_me, x, y, r, zf[f"CHAIR_{k}"], interact="sit"))
    obs.append(place(col, col_s, "MOD_CABIN_DESK_A", d_me, *LAYOUT["DESK"][:2], LAYOUT["DESK"][2], zf["DESK"], interact="captain_log"))
    x, y, r = LAYOUT["DESK_CHAIR"]
    obs.append(place(col, col_s, "MOD_CABIN_CHAIR_A_DESK", c_me, x, y, r, zf["DESK_CHAIR"], interact="sit"))
    obs.append(place(col, col_s, "MOD_CABIN_COT_A", cot_mesh(M, zc_cot - zf["COT"] - 0.12), *LAYOUT["COT"][:2], LAYOUT["COT"][2],
                     zf["COT"], interact="sleep"))
    obs.append(place(col, col_s, "MOD_CABIN_SIDEBOARD_A", sideboard_mesh(M), *LAYOUT["SIDEBOARD"][:2], LAYOUT["SIDEBOARD"][2], zf["SIDEBOARD"]))
    ch_me = chest_mesh(M)
    for k in (1,):
        x, y, r = LAYOUT[f"CHEST_{k}"]
        obs.append(place(col, col_s, f"MOD_CABIN_CHEST_A_{k:02d}", ch_me, x, y, r, zf[f"CHEST_{k}"], interact="loot"))
    x, y, r = LAYOUT["BENCH"]
    obs.append(place(col, col_s, "MOD_CABIN_STERN_BENCH_A", bench_mesh(M, 1.70), x, y, r, zf["BENCH"], interact="sit"))
    x, y, _ = LAYOUT["LANTERN"]
    lan = place(col, col_s, "MOD_LANTERN_HANGING_A_01", lantern_mesh(M, 0.35), x, y, 0.0, zc - 0.02, light="point (UE)")
    obs.append(lan)
    bpy.context.view_layer.update()

    # denetimler: mürettebat noktası çakışması, duvar/tavan taşması
    conflicts, outside = [], []
    boxes = {o.name: world_bbox(o) for o in obs}
    for o in bpy.data.objects:
        if o.type == "EMPTY" and o.name.startswith("SOCK_CREW_CHASE_STERN_"):
            p = o.location
            for n, (x0, x1, y0, y1, z0, z1) in boxes.items():
                if x0 - 0.25 < p.x < x1 + 0.25 and y0 - 0.25 < p.y < y1 + 0.25 and z0 - 0.5 < p.z < z1:
                    conflicts.append({"crew": o.name, "furniture": n})
    for n, (x0, x1, y0, y1, z0, z1) in boxes.items():
        for x in (x0, x1):
            for y in (y0, y1):
                zd = (z0 + 0.3 - DWL) / K
                s = P13.s_of_x(x / K, lambda s_: zd)
                half = H.hull_point(s, zd)[1] * K - 0.24 * K
                if abs(y) > half or x > X_FWD + 0.02 or x < H.stern_x(zd) * K + 0.30:
                    outside.append(n)
    outside = sorted(set(outside))
    # çarpışma: mobilya kutuları (sandalyeler dahil; fener ve yatak halatı hariç)
    ucx = []
    for o in obs:
        if o.name.startswith("MOD_LANTERN"):
            continue
        x0, x1, y0, y1, z0, z1 = boxes[o.name]
        pts = [V((x, y, z)) for x in (x0, x1) for y in (y0, y1) for z in (z0, min(z1, z0 + 1.2))]
        u = C3.convex(f"UCX_{o.name}_00", pts, ucx_col, "furniture")
        u["owner_mesh"] = o.name
        u.name = u.data.name = f"UCX_{o.name}_00"
        ucx.append(u.name)
    return obs, conflicts, outside, ucx, dict(floor_table=zf["TABLE"], ceiling_table=zc, gaps=gaps)


def render(sc):
    H.setup_render(sc, fast=True)
    out = ROOT / "renders" / VER
    out.mkdir(parents=True, exist_ok=True)
    lan = bpy.data.objects["MOD_LANTERN_HANGING_A_01"]
    for loc, e in ((lan.location + V((0, 0, -0.55)), 700), (V((-19.3, 0.0, lan.location.z - 0.8)), 350),
                   (V((-16.2, 2.4, lan.location.z - 0.5)), 250), (V((-16.2, -2.4, lan.location.z - 0.5)), 250)):
        lamp = bpy.data.lights.new("CabinPreview", "POINT")
        lamp.energy = e
        lamp.color = (1.0, 0.78, 0.55)
        lo = bpy.data.objects.new("LGT_CabinPreview", lamp)
        lo.location = loc
        sc.collection.objects.link(lo)
    zf = bpy.data.objects["MOD_CABIN_TABLE_A"].location.z
    views = [
        ("kamara_kica", V((-15.7, -0.9, zf + 1.65)), V((-20.0, 0.4, zf + 0.7)), 18),
        ("kamara_masa", V((-19.4, 2.2, zf + 1.7)), V((-16.6, -0.6, zf + 0.55)), 18),
        ("kamara_yazi_masasi", V((-17.9, 1.2, zf + 1.55)), V((-15.8, 3.1, zf + 0.7)), 20),
        ("kamara_yatak", V((-18.4, -1.0, zf + 1.6)), V((-16.0, -3.1, zf + 0.7)), 20),
    ]
    for name, loc, tgt, lens in views:
        sc.camera = H.camera(sc, f"CAM16_{name}", loc, tgt, lens=lens)
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
    obs, conflicts, outside, ucx, dims = main_build()
    bpy.ops.wm.save_as_mainfile(filepath=str(out), compress=True)
    H.VERSION = VER
    ap = ROOT / "reports" / f"scene_audit_{VER}.json"
    rep = H.audit(sc, ap)
    rep["cabin_v016"] = {"objects": [o.name for o in obs], "crew_conflicts": conflicts, "outside_room": outside,
                         "ucx": ucx, "clear_height_at_table_m": round(dims["ceiling_table"] - dims["floor_table"], 3),
                         "sources": "mobilya ölçüleri TAHMİN", "deck_stern_gap_fix": dims["gaps"]}
    rep["pass"] = {"name": "pass_v016_cabin_interior", "source": f"Blender/versions/{SHIP}_{SRC_VER}.blend",
                   "pass_changes": {"modules_added": [o.name for o in obs], "ucx_added": len(ucx)},
                   "manifest_version": MANIFEST_VERSION, "geometry_changed": "iç mekân modülleri; CORE_DECK_GUN/LOWER kıç ucu aynaya uzatıldı (boşluk düzeltmesi)"}
    ap.write_text(json.dumps(rep, indent=2, ensure_ascii=False), encoding="utf-8")
    print("GAPS", dims["gaps"])
    print("CABIN", len(obs), "CONFLICTS", conflicts, "OUTSIDE", outside, "H", rep["cabin_v016"]["clear_height_at_table_m"])
    if "--no-render" not in sys.argv:
        render(sc)


if __name__ == "__main__":
    main()
