"""Pass v020 — Gerçekçi top modülü MOD_CANNON_9PDR_B (v014'teki A'nın yerine), v019 üzerine.

Çalıştırma (depo kökünden):
    python3 OTTOMAN_FRIGATE_1780_ISTANBUL/scripts/pass_v020_cannon_realistic.py [--no-render | --render-only]

Kullanıcı (2026-09-26): "topları değiştirebiliriz, daha gerçekçi top modelleri kullanalım".
A modeli kaba kutulardan ve basit bir namlu profilinden oluşuyordu. B modelinde:
  - Namlu: kaskabel topuzu ve boynu, taban halkası (ogee), falya astragalı ve falya yastığı, 1. ve 2. takviye
    halkaları, kovan kuşağı ve astragalı, ağız astragalı, boyun, ağız şişkinliği ve dudak; iç namlu. 48 dilim.
    Muylular kök bilezikli (rimbase).
  - Kızak: tek parça basamaklı yanaklar (profil + kalınlık, pahlı), muylu yuvası, ön travers, dingiller ve
    dingil başları, bombeli tekerler + demir göbek + perno, taban tahtası, sap tutamaklı nişan takozu,
    menteşeli muylu kapakları, brok ve palanga halkaları, cıvata başları.
  - Malzeme: dökme demir (pürüzlülük ve hafif pas gürültüsü), kızak kırmızı aşı boyası (A ile aynı).
Pivot, soket ve ana ölçüler A ile aynı (muylu yüksekliği 0,86 m, muylu x = 0,30 m); brok halatları ve
mürettebat noktaları değişmez. Ölçüler: namlu çapı 0,107 m [İKİNCİL], diğerleri TAHMİN.
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


P14 = _load("pass_v014", "pass_v014_cannon_9pdr.py")
P15 = _load("pass_v015", "pass_v015_rigset.py")
P13, P5, H = P14.P13, P14.P5, P14.H
SRC_VER, VER = "v019", "v020"
ROOT, SHIP = H.ROOT, H.SHIP_ID
MANIFEST_VERSION = 17
V = Vector

BORE, L = P14.BORE, P14.L_BARREL
TRUN_X, TRUN_Z = P14.TRUN_X, P14.TRUN_Z
XB = -P14.TRUN_FROM_BREECH           # taban halkası (muylu eksenine göre)
XM = L + XB                          # ağız
SEG = 48


def barrel_profile():
    xb, xm = XB, XM
    x1 = xb + L * 2 / 7              # 1. takviye halkası
    x2 = xb + L * 0.52               # 2. takviye halkası
    xc = xb + L * 0.62               # kovan astragalı
    p = [
        (0.0, xb - 0.235), (0.022, xb - 0.232), (0.040, xb - 0.222), (0.052, xb - 0.205), (0.055, xb - 0.185),   # topuz
        (0.050, xb - 0.165), (0.036, xb - 0.150), (0.030, xb - 0.140), (0.030, xb - 0.122),                       # boyun
        (0.048, xb - 0.115), (0.090, xb - 0.098), (0.128, xb - 0.075), (0.155, xb - 0.048), (0.172, xb - 0.022),  # kaskabel
        (0.180, xb - 0.006), (0.190, xb), (0.198, xb + 0.008), (0.200, xb + 0.020), (0.200, xb + 0.036),          # taban halkası
        (0.193, xb + 0.044), (0.190, xb + 0.052), (0.187, xb + 0.060),
        (0.186, xb + 0.110), (0.191, xb + 0.115), (0.192, xb + 0.128), (0.187, xb + 0.133),                       # falya astragalı
        (0.184, xb + 0.200), (0.180, x1 - 0.030), (0.186, x1 - 0.026), (0.186, x1 - 0.018), (0.192, x1 - 0.012),
        (0.192, x1 + 0.020), (0.186, x1 + 0.026), (0.176, x1 + 0.032), (0.174, x1 + 0.040),                       # 1. takviye halkası
        (0.166, x2 - 0.030), (0.171, x2 - 0.026), (0.176, x2 - 0.020), (0.176, x2 + 0.012), (0.168, x2 + 0.018),
        (0.152, x2 + 0.024), (0.150, x2 + 0.032),                                                                  # 2. takviye halkası
        (0.144, xc - 0.020), (0.148, xc - 0.016), (0.153, xc - 0.008), (0.153, xc + 0.004), (0.148, xc + 0.012),
        (0.143, xc + 0.016),                                                                                        # kovan astragalı
        (0.118, xm - 0.300), (0.123, xm - 0.296), (0.124, xm - 0.286), (0.119, xm - 0.281), (0.112, xm - 0.276),   # ağız astragalı
        (0.108, xm - 0.240), (0.109, xm - 0.200), (0.114, xm - 0.160), (0.123, xm - 0.110), (0.131, xm - 0.070),   # boyun + şişkinlik
        (0.136, xm - 0.045), (0.138, xm - 0.030), (0.138, xm - 0.014), (0.132, xm - 0.006), (0.126, xm),          # dudak
        (BORE / 2 + 0.010, xm), (BORE / 2 + 0.003, xm - 0.004), (BORE / 2, xm - 0.012), (BORE / 2, xm - 0.55),
        (0.0, xm - 0.58),
    ]
    return p


def iron_material():
    name = "MAT_Iron_Cast"
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    N, Lk = nt.nodes, nt.links
    b = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord")
    n1 = N.new("ShaderNodeTexNoise")
    n1.inputs["Scale"].default_value = 18.0
    n1.inputs["Detail"].default_value = 8.0
    Lk.new(tc.outputs["Object"], n1.inputs["Vector"])
    rr = N.new("ShaderNodeMapRange")
    rr.inputs["To Min"].default_value = 0.32
    rr.inputs["To Max"].default_value = 0.68
    Lk.new(n1.outputs["Fac"], rr.inputs["Value"])
    Lk.new(rr.outputs["Result"], b.inputs["Roughness"])
    n2 = N.new("ShaderNodeTexNoise")
    n2.inputs["Scale"].default_value = 4.0
    n2.inputs["Detail"].default_value = 10.0
    Lk.new(tc.outputs["Object"], n2.inputs["Vector"])
    ramp = N.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.62
    ramp.color_ramp.elements[1].position = 0.78
    Lk.new(n2.outputs["Fac"], ramp.inputs["Fac"])
    mix = N.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.inputs["A"].default_value = (0.028, 0.027, 0.026, 1)
    mix.inputs["B"].default_value = (0.11, 0.055, 0.03, 1)        # hafif pas
    Lk.new(ramp.outputs["Color"], mix.inputs["Factor"])
    Lk.new(mix.outputs["Result"], b.inputs["Base Color"])
    b.inputs["Metallic"].default_value = 0.85
    bump = N.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.08
    Lk.new(n1.outputs["Fac"], bump.inputs["Height"])
    Lk.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m


def finalize(name, parts, sharp=30):
    merged = bmesh.new()
    mats = []
    for idx, (b, mat) in enumerate(parts):
        bmesh.ops.recalc_face_normals(b, faces=b.faces)
        me = bpy.data.meshes.new("_tmp")
        b.to_mesh(me)
        b.free()
        me.polygons.foreach_set("material_index", [idx] * len(me.polygons))
        merged.from_mesh(me)
        bpy.data.meshes.remove(me)
        mats.append(mat)
    me = bpy.data.meshes.new(name)
    merged.to_mesh(me)
    merged.free()
    for mt in mats:
        me.materials.append(mt)
    for p in me.polygons:
        p.use_smooth = True
    me.set_sharp_from_angle(angle=math.radians(sharp))
    tmp = bpy.data.objects.new("_tmp_uv", me)
    H.build_uv_fallback(tmp)
    bpy.data.objects.remove(tmp)
    return me


def build_barrel(iron):
    bm = bmesh.new()
    P5.lathe(bm, barrel_profile(), SEG, Matrix.Rotation(math.radians(90), 4, "Y"))
    for sgn in (1, -1):                                   # muylu + kök bileziği
        m = Matrix.Translation((0, sgn * 0.150, -0.012)) @ Matrix.Rotation(math.radians(-90 * sgn), 4, "X")
        P5.lathe(bm, [(0.0, 0.0), (0.086, 0.0), (0.086, 0.018), (0.080, 0.028), (0.060, 0.034), (0.055, 0.040),
                      (0.055, 0.150), (0.052, 0.156), (0.030, 0.160), (0.0, 0.161)], 24, m)
    # falya yastığı ve deliği
    top = 0.186
    c = V((XB + 0.160, 0.0, top - 0.004))
    P5.lathe(bm, [(0.0, 0.0), (0.030, 0.0), (0.030, 0.012), (0.012, 0.016), (0.008, 0.010), (0.0, 0.010)], 16, P5.axis_matrix(c, V((0, 0, 1))))
    return finalize("MOD_CANNON_9PDR_B_BARREL", [(bm, iron)])


def bracket(bm, y0, y1):
    """Yanak: X-Z profilinden Y kalınlığında. Muylu yuvası yarım daire."""
    zb = 0.19
    zt = TRUN_Z - 0.03
    notch_c = V((TRUN_X, TRUN_Z - 0.012))
    pts = [(-0.80, zb + 0.02), (-0.76, zb), (0.50, zb), (0.55, zb + 0.06), (0.56, zb + 0.20), (0.53, zt - 0.10),
           (0.48, zt)]
    xn1, xn0 = TRUN_X + 0.062, TRUN_X - 0.062
    pts.append((xn1, zt))
    for k in range(1, 12):                                # yuva (aşağı yarım daire)
        a = math.pi * k / 12
        pts.append((notch_c.x + 0.062 * math.cos(a), notch_c.y - 0.062 * math.sin(a)))
    pts.append((xn0, zt))
    pts += [(TRUN_X - 0.16, zt), (TRUN_X - 0.16, zt - 0.12), (-0.12, zt - 0.12), (-0.12, zt - 0.24), (-0.44, zt - 0.24),
            (-0.44, zt - 0.36), (-0.74, zt - 0.36), (-0.79, zt - 0.40), (-0.80, zt - 0.45)]
    f0 = [bm.verts.new((x, y0, z)) for x, z in pts]
    f1 = [bm.verts.new((x, y1, z)) for x, z in pts]
    bm.faces.new(f0)
    bm.faces.new(list(reversed(f1)))
    n = len(pts)
    for k in range(n):
        bm.faces.new([f0[k], f0[(k + 1) % n], f1[(k + 1) % n], f1[k]])


def truck(bm_w, bm_i, cx, cy, r, w, sgn):
    m = Matrix.Translation((cx, cy - w / 2, r)) @ Matrix.Rotation(math.radians(-90), 4, "X")
    P5.lathe(bm_w, [(0.0, 0.0), (0.07, 0.0), (0.08, 0.004), (r - 0.025, 0.004), (r - 0.006, 0.012), (r, 0.03),
                    (r, w - 0.03), (r - 0.006, w - 0.012), (r - 0.025, w - 0.004), (0.08, w - 0.004), (0.07, w), (0.0, w)], 28, m)
    face = cy + sgn * w / 2
    P5.lathe(bm_i, [(0.0, 0.0), (0.075, 0.0), (0.075, 0.018), (0.050, 0.024), (0.0, 0.026)], 20,
             Matrix.Translation((cx, face, r)) @ Matrix.Rotation(math.radians(-90 * sgn), 4, "X"))           # göbek kapağı
    P15.obox(bm_i, V((cx, face + sgn * 0.04, r + 0.05)), V((0, 0, 1)), V((0, 1, 0)), V((1, 0, 0)), 0.045, 0.008, 0.012)  # perno


def build_carriage(iron, wood):
    bw, bi = bmesh.new(), bmesh.new()
    y_in, t = 0.20, 0.11
    for sgn in (1, -1):
        y0, y1 = sorted((sgn * y_in, sgn * (y_in + t)))
        bracket(bw, y0, y1)
    half = y_in + t + 0.05
    for ax, r in ((P14.AXLE_X_F, P14.WHEEL_R_F), (P14.AXLE_X_R, P14.WHEEL_R_R)):
        P5.aabox(bw, ax - 0.08, ax + 0.08, -half, half, r - 0.05, r + 0.09)                     # dingil
        for sgn in (1, -1):
            P5.lathe(bw, [(0.0, 0.0), (0.045, 0.0), (0.045, 0.14), (0.0, 0.14)], 16,
                     Matrix.Translation((ax, sgn * half, r)) @ Matrix.Rotation(math.radians(-90 * sgn), 4, "X"))
            truck(bw, bi, ax, sgn * (half + 0.065), r, 0.10, sgn)
        P5.aabox(bi, ax - 0.085, ax + 0.085, -half + 0.02, half - 0.02, r + 0.09, r + 0.10)   # dingil demiri
    P5.aabox(bw, 0.40, 0.52, -y_in, y_in, 0.30, 0.64)                                           # ön travers
    P5.aabox(bw, -0.66, 0.12, -y_in, y_in, 0.46, 0.51)                                          # taban tahtası
    q = [V((-0.72, -0.13, 0.51)), V((-0.30, -0.13, 0.51)), V((-0.30, 0.13, 0.51)), V((-0.72, 0.13, 0.51)),
         V((-0.72, -0.13, 0.66)), V((-0.30, -0.13, 0.58)), V((-0.30, 0.13, 0.58)), V((-0.72, 0.13, 0.66))]
    P5.box8(bw, q)                                                                             # nişan takozu (eğimli)
    P5.lathe(bw, [(0.0, 0.0), (0.02, 0.0), (0.02, 0.10), (0.028, 0.11), (0.028, 0.14), (0.0, 0.15)], 12,
             Matrix.Translation((-0.72, 0.0, 0.60)) @ Matrix.Rotation(math.radians(-90), 4, "Y"))   # takoz sapı
    for sgn in (1, -1):
        yc = sgn * (y_in + t / 2)
        # muylu kapağı: muylunun üstünden geçen yay biçimli lama + menteşe + kama
        arc = []
        for k in range(13):
            a = math.pi * k / 12
            arc.append(V((TRUN_X + 0.068 * math.cos(a), yc, TRUN_Z - 0.012 + 0.068 * math.sin(a))))
        for dy in (-0.035, 0.035):
            P15.tube(bi, [p + V((0, dy, 0)) for p in arc], 0.010, seg=6)
        P15.obox(bi, V((TRUN_X - 0.09, yc, TRUN_Z - 0.03)), V((1, 0, 0)), V((0, 1, 0)), V((0, 0, 1)), 0.025, t / 2 + 0.006, 0.03)
        P15.obox(bi, V((TRUN_X + 0.09, yc, TRUN_Z - 0.03)), V((1, 0, 0)), V((0, 1, 0)), V((0, 0, 1)), 0.022, t / 2 + 0.006, 0.025)
        # halkalar (brok ve palanga) ve cıvata başları
        yo = sgn * (y_in + t + 0.004)
        for xr, zr in ((-0.28, 0.42), (0.22, 0.46)):
            ring = []
            for k in range(12):
                a = 2 * math.pi * k / 12
                ring.append(V((xr + 0.045 * math.cos(a), yo + sgn * 0.02, zr - 0.05 + 0.045 * math.sin(a))))
            P15.tube(bi, ring + [ring[0]], 0.010, seg=5)
            P5.lathe(bi, [(0.0, 0.0), (0.022, 0.0), (0.018, 0.012), (0.0, 0.014)], 10,
                     Matrix.Translation((xr, yo, zr)) @ Matrix.Rotation(math.radians(-90 * sgn), 4, "X"))
        for xr, zr in ((-0.62, 0.30), (-0.30, 0.42), (0.05, 0.55), (0.42, 0.40), (0.42, 0.62), (-0.62, 0.42)):
            P5.lathe(bi, [(0.0, 0.0), (0.018, 0.0), (0.015, 0.010), (0.0, 0.012)], 8,
                     Matrix.Translation((xr, yo, zr)) @ Matrix.Rotation(math.radians(-90 * sgn), 4, "X"))
    ring = []                                                                                   # arka palanga halkası
    for k in range(12):
        a = 2 * math.pi * k / 12
        ring.append(V((-0.82, 0.045 * math.cos(a), 0.40 + 0.045 * math.sin(a))))
    P15.tube(bi, ring + [ring[0]], 0.011, seg=5)
    return finalize("MOD_CANNON_9PDR_B_CARRIAGE", [(bw, wood), (bi, iron)], sharp=35)


def swap_guns(bar_me, car_me):
    swapped = []
    old_meshes = set()
    for o in list(bpy.data.objects):
        if not o.name.startswith("MOD_CANNON_9PDR_A_") or o.name.endswith("_BARREL") or o.type != "MESH":
            continue
        tag = o.name[len("MOD_CANNON_9PDR_A_"):]
        old_meshes.add(o.data)
        o.data = car_me
        o.name = f"MOD_CANNON_9PDR_B_{tag}"
        o["gun_type"] = "9pdr_long_truck_B"
        for ch in o.children:
            if ch.type == "MESH":
                old_meshes.add(ch.data)
                ch.data = bar_me
                ch.name = f"MOD_CANNON_9PDR_B_{tag}_BARREL"
        s = bpy.data.objects.get(o.get("socket", ""))
        if s:
            s["installed_module"] = o.name
            s["manifest_version"] = MANIFEST_VERSION
        swapped.append(o.name)
    for me in old_meshes:
        if me.users == 0:
            bpy.data.meshes.remove(me)
    for o in bpy.data.objects:
        if o.type == "EMPTY" and o.name.startswith("SOCKET_CANNON_LOWER_"):
            o["module_family_accepts"] = "MOD_CANNON_9PDR_B"
            o["manifest_version"] = MANIFEST_VERSION
    mu = bpy.data.objects.get("SOCKET_GUN_MUZZLE")
    th = bpy.data.objects.get("SOCKET_GUN_TOUCHHOLE")
    if mu:
        mu.location = (XM + 0.02, 0.0, 0.0)
        mu["mesh_socket_of"] = "MOD_CANNON_9PDR_B_BARREL"
        mu["manifest_version"] = MANIFEST_VERSION
    if th:
        th.location = (XB + 0.160, 0.0, 0.205)
        th["mesh_socket_of"] = "MOD_CANNON_9PDR_B_BARREL"
        th["manifest_version"] = MANIFEST_VERSION
    return swapped


def render(sc):
    H.setup_render(sc, fast=True)
    out = ROOT / "renders" / VER
    out.mkdir(parents=True, exist_ok=True)
    g = bpy.data.objects["SOCKET_CANNON_S_05"].matrix_world
    views = [
        ("top_arka", g @ V((-2.3, 1.1, 1.35)), g @ V((0.1, 0.0, 0.62)), 32),
        ("top_yan", g @ V((-0.6, -2.0, 1.15)), g @ V((-0.1, 0.1, 0.6)), 30),
        ("top_ust", g @ V((-0.2, 0.9, 2.3)), g @ V((0.0, 0.0, 0.7)), 30),
        ("bel_toplar", V((-12.0, 0.0, 6.0)), V((6.0, 2.5, 3.0)), 24),
    ]
    for name, loc, tgt, lens in views:
        sc.camera = H.camera(sc, f"CAM20_{name}", loc, tgt, lens=lens)
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
    iron = iron_material()
    wood = bpy.data.materials["MAT_Carriage_RedOchre"]
    bar_me = build_barrel(iron)
    car_me = build_carriage(iron, wood)
    swapped = swap_guns(bar_me, car_me)
    bpy.ops.wm.save_as_mainfile(filepath=str(out), compress=True)
    H.VERSION = VER
    ap = ROOT / "reports" / f"scene_audit_{VER}.json"
    rep = H.audit(sc, ap)

    def tris(me):
        me.calc_loop_triangles()
        return len(me.loop_triangles)

    rep["cannon_v020"] = {"module": "MOD_CANNON_9PDR_B", "replaced": len(swapped),
                          "tris": {"barrel": tris(bar_me), "carriage": tris(car_me)},
                          "tris_A": {"barrel": 2172, "carriage": 1912},
                          "muzzle_local_x": round(TRUN_X + XM, 3), "sources": "namlu çapı İKİNCİL; profil ve kızak TAHMİN"}
    rep["pass"] = {"name": "pass_v020_cannon_realistic", "source": f"Blender/versions/{SHIP}_{SRC_VER}.blend",
                   "manifest_version": MANIFEST_VERSION, "geometry_changed": "top modülü A → B (aynı pivot ve soketler)"}
    ap.write_text(json.dumps(rep, indent=2, ensure_ascii=False), encoding="utf-8")
    print("V020", json.dumps(rep["cannon_v020"], ensure_ascii=False))
    if "--no-render" not in sys.argv:
        render(sc)


if __name__ == "__main__":
    main()
