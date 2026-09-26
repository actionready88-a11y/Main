"""Top varyantları — ayrı varlık paketi (gemide KULLANILMAZ), FBX olarak teslim.

Çalıştırma (depo kökünden):
    python3 OTTOMAN_FRIGATE_1780_ISTANBUL/scripts/make_cannon_variants.py [--no-render]

Kullanıcı (2026-09-26): "birkaç ekstra varyant üret ama bu gemide kullanma, FBX dosyası olarak kalsın".
Kullanıcının verdiği YouTube videosu bu ortamdan açılamadı; kullanıcı "dönem varyantlarını üret" seçeneğini seçti.
Varyantlar (ölçüler TAHMİN; dönem tipleri genel bilgi, kaynaklı değer değil):
  1. MOD_CANNON_BRONZE_OTTOMAN_A — süslü tunç uzun top (kulplu/"yunus", kabartma kuşaklı, lale ağızlı) + truck kızak.
  2. MOD_CARRONADE_A — kısa, geniş ağızlı karronad; kızak yerine alt/üst kızaklı sürgü (slide) ve yükseliş vidası.
  3. MOD_SWIVEL_GUN_A — küpeşte döner topu: çatal (yoke), mil (pintle), dümen kolu.
  4. MOD_FIELD_GUN_SAHI_A — şahi tipi sahra topu: tunç namlu, uzun kuyruklu kundak, parmaklı tekerlekler.
  5. MOD_MORTAR_A — kısa havan, muyluları kıçta, blok yatakta.
Her varyant: namlu ve kundak ayrı mesh (namlu pivotu muylu ekseninde, kundağın çocuğu), SOCKET_MUZZLE / SOCKET_TOUCHHOLE
mesh soketleri, UCX. Çıktılar:
  Blender/versions/CANNON_VARIANTS_v001.blend
  FBX/Modules/Cannons/SM_<Varyant>.fbx  (+ FBX/export_manifest_cannon_variants.json)
  renders/cannon_variants/*.png
"""

import hashlib
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


P20 = _load("pass_v020", "pass_v020_cannon_realistic.py")
P5, H, P15 = P20.P5, P20.H, P20.P15
ROOT = H.ROOT
V = Vector
OUT_FBX = ROOT / "FBX" / "Modules" / "Cannons"
OUT_BLEND = ROOT / "Blender" / "versions" / "CANNON_VARIANTS_v001.blend"
OUT_RENDER = ROOT / "renders" / "cannon_variants"


# --- Malzemeler ---------------------------------------------------------------------------
def bronze_material():
    name = "MAT_Bronze_Patina"
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    N, Lk = m.node_tree.nodes, m.node_tree.links
    b = N["Principled BSDF"]
    tc = N.new("ShaderNodeTexCoord")
    n = N.new("ShaderNodeTexNoise")
    n.inputs["Scale"].default_value = 6.0
    n.inputs["Detail"].default_value = 10.0
    Lk.new(tc.outputs["Object"], n.inputs["Vector"])
    ramp = N.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.45
    ramp.color_ramp.elements[0].color = (0.55, 0.36, 0.14, 1)      # parlak tunç
    ramp.color_ramp.elements[1].position = 0.75
    ramp.color_ramp.elements[1].color = (0.20, 0.30, 0.22, 1)      # yeşil patina
    Lk.new(n.outputs["Fac"], ramp.inputs["Fac"])
    Lk.new(ramp.outputs["Color"], b.inputs["Base Color"])
    rr = N.new("ShaderNodeMapRange")
    rr.inputs["To Min"].default_value = 0.25
    rr.inputs["To Max"].default_value = 0.6
    Lk.new(n.outputs["Fac"], rr.inputs["Value"])
    Lk.new(rr.outputs["Result"], b.inputs["Roughness"])
    b.inputs["Metallic"].default_value = 0.9
    return m


def mats():
    M = {"iron": P20.iron_material(), "bronze": bronze_material()}
    for nm, col in (("MAT_Carriage_RedOchre", (0.28, 0.06, 0.035)), ("MAT_Timber_Oak", (0.12, 0.08, 0.05))):
        if nm not in bpy.data.materials:
            H.plank_material(nm, col, tuple(c * 0.45 for c in col), plank_w=0.3, rough=0.65, bump=0.12)
    M["carriage"] = bpy.data.materials["MAT_Carriage_RedOchre"]
    M["oak"] = bpy.data.materials["MAT_Timber_Oak"]
    return M


# --- Genel yardımcılar ------------------------------------------------------------------------
LX = Matrix.Rotation(math.radians(90), 4, "Y")          # lathe Z → +X


def barrel_generic(bm, L, R, bore, xb, rings, muzzle="swell", button=True):
    """Parametrik namlu (muylu ekseni orijinde). L: taban→ağız, R: taban yarıçapı; rings: [(x_oran, yükseklik)]."""
    xm = xb + L
    p = []
    if button:
        p += [(0.0, xb - 0.24 * R / 0.19), (0.05 * R / 0.19, xb - 0.235 * R / 0.19), (0.055 * R / 0.19, xb - 0.19 * R / 0.19),
              (0.03 * R / 0.19, xb - 0.14 * R / 0.19), (0.03 * R / 0.19, xb - 0.12 * R / 0.19)]
    else:
        p += [(0.0, xb - 0.03)]
    p += [(R * 0.5, xb - 0.10 * R / 0.19), (R * 0.85, xb - 0.04 * R / 0.19), (R * 0.97, xb), (R * 1.06, xb + 0.01), (R * 1.06, xb + 0.04),
          (R, xb + 0.05)]
    for fr, h in rings:                                   # astragal/halkalar
        x = xb + L * fr
        rr = R * (1 - 0.30 * fr)
        p += [(rr, x - 0.03), (rr + h, x - 0.02), (rr + h, x + 0.02), (rr, x + 0.03)]
    rm = R * 0.62
    if muzzle == "swell":
        p += [(rm, xm - 0.30), (rm * 0.95, xm - 0.2), (rm * 1.15, xm - 0.07), (rm * 1.22, xm - 0.02), (rm * 1.12, xm)]
    elif muzzle == "tulip":                               # lale ağız (Osmanlı süslemesi)
        p += [(rm * 0.95, xm - 0.45), (rm * 0.9, xm - 0.32), (rm * 1.05, xm - 0.20), (rm * 1.30, xm - 0.08), (rm * 1.42, xm - 0.02),
              (rm * 1.35, xm)]
    else:                                                 # karronad/havan: düz ağız
        p += [(rm * 1.02, xm - 0.05), (rm * 1.08, xm - 0.02), (rm * 1.05, xm)]
    p += [(bore / 2 + 0.01, xm), (bore / 2, xm - 0.02), (bore / 2, xm - L * 0.8), (0.0, xm - L * 0.8 - 0.02)]
    P5.lathe(bm, p, 40, LX)
    return xm


def trunnions(bm, r, y, zoff=-0.01, length=0.13):
    for sgn in (1, -1):
        m = Matrix.Translation((0, sgn * y, zoff)) @ Matrix.Rotation(math.radians(-90 * sgn), 4, "X")
        P5.lathe(bm, [(0.0, 0.0), (r * 1.55, 0.0), (r * 1.55, 0.02), (r, 0.035), (r, length), (r * 0.6, length + 0.006), (0.0, length + 0.007)], 20, m)


def spoked_wheel(bm_w, bm_i, c, r, w, spokes=12):
    """Parmaklı tekerlek (ekseni Y): jant + ispitler + göbek + demir lastik."""
    T = Matrix.Translation(c) @ Matrix.Rotation(math.radians(-90), 4, "X")
    P5.lathe(bm_w, [(r * 0.86, -w / 2), (r - 0.02, -w / 2), (r - 0.02, w / 2), (r * 0.86, w / 2)], 36, T)       # jant (felloe)
    P5.lathe(bm_i, [(r - 0.02, -w / 2 - 0.005), (r, -w / 2), (r, w / 2), (r - 0.02, w / 2 + 0.005)], 36, T)     # demir lastik
    P5.lathe(bm_w, [(0.0, -w * 0.9), (0.10, -w * 0.9), (0.13, -w * 0.5), (0.13, w * 0.5), (0.10, w * 0.9), (0.0, w * 0.9)], 20, T)  # göbek
    for k in range(spokes):
        a = 2 * math.pi * k / spokes
        d = V((math.cos(a), 0.0, math.sin(a)))
        P15.tube(bm_w, [c + d * 0.12, c + d * (r * 0.87)], 0.022, seg=6)


def finalize(name, parts):
    return P20.finalize(name, parts)


def place(col, name, me, loc=(0, 0, 0), parent=None):
    ob = bpy.data.objects.new(name, me)
    col.objects.link(ob)
    ob.location = loc
    if parent is not None:
        ob.parent = parent
    return ob


def socket(col, name, parent, loc, rot=(0, 0, 0)):
    e = bpy.data.objects.new(name, None)
    e.empty_display_type = "SINGLE_ARROW"
    e.empty_display_size = 0.2
    col.objects.link(e)
    e.parent = parent
    e.location = loc
    e.rotation_euler = rot
    return e


def ucx(col, name, owner, pts):
    o = P15.C3.convex(name, pts, col, "gun")
    o.name = o.data.name = name
    o["owner_mesh"] = owner.name
    o.parent = owner
    o.matrix_parent_inverse = owner.matrix_world.inverted()
    return o


def bbox_pts(obs):
    pts = []
    for o in obs:
        pts += [o.matrix_world @ V(c) for c in o.bound_box]
    return pts


# --- Varyantlar -----------------------------------------------------------------------------------
def v_bronze_ottoman(col, M):
    """Süslü tunç uzun top: 12 librelik sınıfı (çap 0,117 m), 2,9 m; yunus kulplar, kabartma kuşaklar, lale ağız."""
    bm = bmesh.new()
    L, R, bore = 2.90, 0.205, 0.117
    xb = -L * 3 / 7
    xm = barrel_generic(bm, L, R, bore, xb, [(0.05, 0.012), (0.10, 0.02), (0.30, 0.018), (0.34, 0.012), (0.52, 0.016), (0.56, 0.01),
                                              (0.66, 0.012), (0.70, 0.02)], muzzle="tulip")
    trunnions(bm, 0.062, R * 0.83)
    for sgn in (1, -1):                                   # "yunus" kulplar (tutamak) — kıvrık halka
        pts = []
        for k in range(15):
            a = math.pi * k / 14
            pts.append(V((0.08 + 0.16 * math.cos(a), sgn * 0.06, R * 0.95 + 0.14 * math.sin(a))))
        P15.tube(bm, pts, 0.022, seg=8)
    for fr in (0.18, 0.44, 0.62):                          # kabartma kuşak (rumi dalga)
        x0 = xb + L * fr
        rr = R * (1 - 0.30 * fr) + 0.004
        pts = [V((x0 + 0.05 * math.sin(6 * math.pi * k / 48), rr * math.cos(2 * math.pi * k / 48), rr * math.sin(2 * math.pi * k / 48)))
               for k in range(49)]
        P15.tube(bm, pts, 0.009, seg=5)
    bar = finalize("MOD_CANNON_BRONZE_OTTOMAN_A_BARREL", [(bm, M["bronze"])])
    car = P20.build_carriage(M["iron"], M["carriage"])
    car.name = "MOD_CANNON_BRONZE_OTTOMAN_A_CARRIAGE"
    return bar, car, xm, xb + 0.16, (P20.TRUN_X, P20.TRUN_Z + 0.03)


def v_carronade(col, M):
    """Karronad: 24 librelik sınıfı (çap 0,147 m), 1,25 m; alt taraftaki kulak (loop) ile sürgüye bağlı."""
    bm = bmesh.new()
    L, R, bore = 1.25, 0.23, 0.147
    xb = -0.55
    xm = barrel_generic(bm, L, R, bore, xb, [(0.12, 0.012), (0.55, 0.01)], muzzle="flat", button=True)
    P5.aabox(bm, -0.09, 0.09, -0.06, 0.06, -R - 0.10, -R + 0.02)          # alt kulak
    P5.lathe(bm, [(0.0, -0.09), (0.035, -0.09), (0.035, 0.09), (0.0, 0.09)], 12,
             Matrix.Translation((0, 0, -R - 0.06)) @ Matrix.Rotation(math.radians(90), 4, "X"))   # pim
    bar = finalize("MOD_CARRONADE_A_BARREL", [(bm, M["iron"])])
    bw, bi = bmesh.new(), bmesh.new()
    P5.aabox(bw, -0.95, 0.55, -0.26, 0.26, 0.42, 0.54)                    # üst kızak (bed)
    for sgn in (1, -1):
        P5.aabox(bw, -0.30, 0.45, sgn * 0.12 - 0.05, sgn * 0.12 + 0.05, 0.54, 0.70)   # kulak yanakları
    P5.aabox(bw, -1.25, 0.70, -0.30, 0.30, 0.20, 0.36)                    # alt sürgü (slide)
    for sgn in (1, -1):
        P5.aabox(bw, -1.25, 0.70, sgn * 0.26 - 0.03, sgn * 0.26 + 0.03, 0.36, 0.44)   # kılavuz
    for x in (-1.05, 0.55):
        P5.aabox(bw, x - 0.08, x + 0.08, -0.34, 0.34, 0.0, 0.20)           # ayaklar
    for sgn in (1, -1):                                                     # arka makaralar (trucks)
        P5.lathe(bw, [(0.0, 0.0), (0.12, 0.0), (0.12, 0.08), (0.0, 0.08)], 20,
                 Matrix.Translation((-1.05, sgn * 0.38, 0.12)) @ Matrix.Rotation(math.radians(-90 * sgn), 4, "X"))
    P5.lathe(bi, [(0.0, 0.0), (0.02, 0.0), (0.02, 0.45), (0.05, 0.47), (0.05, 0.5), (0.0, 0.5)], 12,
             Matrix.Translation((-0.80, 0.0, 0.42)))                         # yükseliş vidası
    car = finalize("MOD_CARRONADE_A_CARRIAGE", [(bw, M["oak"]), (bi, M["iron"])])
    return bar, car, xm, xb + 0.14, (0.10, 0.54 + R + 0.06)


def v_swivel(col, M):
    """Döner top: yarım librelik sınıfı (çap 0,045 m), 0,95 m; çatal, mil ve kıçta kol."""
    bm = bmesh.new()
    L, R, bore = 0.95, 0.065, 0.045
    xb = -0.38
    xm = barrel_generic(bm, L, R, bore, xb, [(0.2, 0.006), (0.55, 0.005)], muzzle="swell", button=False)
    trunnions(bm, 0.022, R * 0.8, length=0.05)
    P15.tube(bm, [V((xb - 0.02, 0, 0)), V((xb - 0.55, 0, -0.05)), V((xb - 0.62, 0, -0.07))], 0.016, seg=8)   # dümen kolu
    bar = finalize("MOD_SWIVEL_GUN_A_BARREL", [(bm, M["bronze"])])
    bi = bmesh.new()
    pts = []
    for k in range(17):                                                     # çatal (U)
        a = math.pi * k / 16
        pts.append(V((0.0, 0.11 * math.cos(a), 0.10 - 0.11 * math.sin(a))))
    P15.tube(bi, pts, 0.018, seg=8)
    P5.lathe(bi, [(0.0, -0.45), (0.028, -0.45), (0.028, -0.02), (0.04, 0.0), (0.0, 0.0)], 12, Matrix())   # mil (pintle)
    P5.lathe(bi, [(0.0, -0.50), (0.07, -0.50), (0.07, -0.40), (0.0, -0.40)], 12, Matrix())                  # küpeşte soketi
    car = finalize("MOD_SWIVEL_GUN_A_YOKE", [(bi, M["iron"])])
    return bar, car, xm, xb + 0.06, (0.0, 0.10)


def v_sahi(col, M):
    """Şahi tipi sahra topu: tunç, çap 0,09 m, 2,1 m; uzun kuyruklu kundak, parmaklı tekerlekler (r 0,68 m)."""
    bm = bmesh.new()
    L, R, bore = 2.10, 0.15, 0.09
    xb = -L * 3 / 7
    xm = barrel_generic(bm, L, R, bore, xb, [(0.08, 0.012), (0.3, 0.014), (0.55, 0.012), (0.72, 0.016)], muzzle="tulip")
    trunnions(bm, 0.045, R * 0.85, length=0.10)
    bar = finalize("MOD_FIELD_GUN_SAHI_A_BARREL", [(bm, M["bronze"])])
    bw, bi = bmesh.new(), bmesh.new()
    zt = 1.02
    for sgn in (1, -1):                                                     # kuyruklu yanaklar (trail)
        y0, y1 = sorted((sgn * 0.13, sgn * 0.21))
        pts = [(0.30, zt - 0.02), (0.15, zt + 0.02), (-0.20, zt - 0.05), (-2.30, 0.06), (-2.45, 0.0), (-2.40, 0.16), (-0.20, zt - 0.28),
               (0.28, zt - 0.30)]
        f0 = [bw.verts.new((x, y0, z)) for x, z in pts]
        f1 = [bw.verts.new((x, y1, z)) for x, z in pts]
        bw.faces.new(f0)
        bw.faces.new(list(reversed(f1)))
        n = len(pts)
        for k in range(n):
            bw.faces.new([f0[k], f0[(k + 1) % n], f1[(k + 1) % n], f1[k]])
    P5.aabox(bw, -0.15, 0.10, -0.62, 0.62, 0.62, 0.74)                      # dingil yatağı
    P5.lathe(bi, [(0.0, -0.75), (0.035, -0.75), (0.035, 0.75), (0.0, 0.75)], 12,
             Matrix.Translation((-0.02, 0.0, 0.68)) @ Matrix.Rotation(math.radians(-90), 4, "X"))   # dingil
    for sgn in (1, -1):
        spoked_wheel(bw, bi, V((-0.02, sgn * 0.62, 0.68)), 0.68, 0.09)
    for x in (-0.9, -1.6):
        P5.aabox(bw, x - 0.05, x + 0.05, -0.18, 0.18, 0.50 if x > -1 else 0.30, 0.60 if x > -1 else 0.40)   # travers
    car = finalize("MOD_FIELD_GUN_SAHI_A_CARRIAGE", [(bw, M["oak"]), (bi, M["iron"])])
    return bar, car, xm, xb + 0.14, (0.10, zt - 0.02)


def v_mortar(col, M):
    """Havan: çap 0,33 m (13 inç sınıfı), 0,95 m; muylular kıç ucunda, meşe blok yatak."""
    bm = bmesh.new()
    L, R, bore = 0.95, 0.30, 0.33
    xb = -0.12
    xm = barrel_generic(bm, L, R, bore, xb, [(0.15, 0.02), (0.6, 0.015)], muzzle="flat", button=False)
    trunnions(bm, 0.075, R * 0.95, zoff=0.0, length=0.12)
    bar = finalize("MOD_MORTAR_A_BARREL", [(bm, M["iron"])])
    bw, bi = bmesh.new(), bmesh.new()
    P5.aabox(bw, -0.75, 0.75, -0.55, 0.55, 0.0, 0.30)
    for sgn in (1, -1):
        P5.aabox(bw, -0.35, 0.40, sgn * 0.42 - 0.10, sgn * 0.42 + 0.10, 0.30, 0.62)
        P5.aabox(bi, -0.12, 0.12, sgn * 0.42 - 0.105, sgn * 0.42 + 0.105, 0.60, 0.64)
    car = finalize("MOD_MORTAR_A_BED", [(bw, M["oak"]), (bi, M["iron"])])
    return bar, car, xm, xb + 0.08, (0.0, 0.62)


VARIANTS = [("MOD_CANNON_BRONZE_OTTOMAN_A", v_bronze_ottoman, 0.0), ("MOD_CARRONADE_A", v_carronade, 0.0),
            ("MOD_SWIVEL_GUN_A", v_swivel, 0.0), ("MOD_FIELD_GUN_SAHI_A", v_sahi, 0.0), ("MOD_MORTAR_A", v_mortar, math.radians(45))]


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.unit_settings.system = "METRIC"
    col = bpy.data.collections.new("22_MODULES_CANNONS")
    sc.collection.children.link(col)
    ccol = bpy.data.collections.new("40_COLLISION")
    sc.collection.children.link(ccol)
    M = mats()
    OUT_FBX.mkdir(parents=True, exist_ok=True)
    manifest = {"source_blend": str(OUT_BLEND.relative_to(ROOT)), "blender": bpy.app.version_string, "unit": "metre (1 BU = 1 m)",
                "axes_blender": "X ileri (namlu), Y sol, Z yukarı", "fbx_settings": {}, "variants": [],
                "note": "gemide kullanılmaz (kullanıcı kararı); ölçüler TAHMİN"}
    roots = []
    for k, (name, fn, elev) in enumerate(VARIANTS):
        bar_me, car_me, xm, xtouch, (tx, tz) = fn(col, M)
        root = place(col, name, car_me, loc=(0.0, k * 3.0, 0.0))
        bv = root.modifiers.new("Bevel", "BEVEL")
        bv.width = 0.012
        bv.segments = 2
        bv.limit_method = "ANGLE"
        root["module_family"] = "CannonVariant"
        root["used_on_ship"] = False
        bar = place(col, f"{name}_BARREL", bar_me, loc=(tx, 0.0, tz), parent=root)
        bar.rotation_euler = (0.0, -elev, 0.0)
        bar["pivot"] = "muylu ekseni (yerel Y)"
        socket(col, f"SOCKET_{name}_MUZZLE", bar, (xm + 0.02, 0, 0), rot=(0, math.radians(90), 0))
        socket(col, f"SOCKET_{name}_TOUCHHOLE", bar, (xtouch, 0, 0.2))
        bpy.context.view_layer.update()
        u = ucx(ccol, f"UCX_{name}_00", root, bbox_pts([root, bar]))
        roots.append((root, bar, u))
        def tris(me):
            me.calc_loop_triangles()
            return len(me.loop_triangles)
        dg = bpy.context.evaluated_depsgraph_get()
        car_ev = root.evaluated_get(dg).to_mesh()
        manifest["variants"].append({"name": name, "tris_barrel": tris(bar_me), "tris_carriage": tris(car_ev)})
        root.evaluated_get(dg).to_mesh_clear()
    # FBX: her varyant ayrı dosya, orijin sıfırda
    for root, bar, u in roots:
        loc = root.location.copy()
        root.location = (0, 0, 0)
        bpy.context.view_layer.update()
        bpy.ops.object.select_all(action="DESELECT")
        for o in [root, bar, u] + [c for c in bar.children]:
            o.select_set(True)
        path = OUT_FBX / f"SM_{root.name}.fbx"
        settings = dict(use_selection=True, apply_unit_scale=True, apply_scale_options="FBX_SCALE_UNITS", axis_forward="-Z", axis_up="Y",
                        mesh_smooth_type="FACE", use_mesh_modifiers=True, add_leaf_bones=False, use_triangles=True,
                        object_types={"MESH", "EMPTY"}, bake_space_transform=False)
        bpy.ops.export_scene.fbx(filepath=str(path), **settings)
        manifest["fbx_settings"] = {k: (sorted(v) if isinstance(v, set) else v) for k, v in settings.items()}
        h = hashlib.sha256(path.read_bytes()).hexdigest()[:16]
        for v in manifest["variants"]:
            if v["name"] == root.name:
                v.update({"fbx": str(path.relative_to(ROOT)), "sha256_16": h, "bytes": path.stat().st_size})
        root.location = loc
    OUT_BLEND.parent.mkdir(parents=True, exist_ok=True)
    if OUT_BLEND.exists():
        raise SystemExit(f"{OUT_BLEND} zaten var; versiyonlu kayıt üzerine yazılmaz.")
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT_BLEND), compress=True)
    (ROOT / "FBX" / "export_manifest_cannon_variants.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print("VARIANTS", json.dumps(manifest["variants"], ensure_ascii=False))
    if "--no-render" not in sys.argv:
        render(sc)


def render(sc):
    H.setup_render(sc, fast=True)
    OUT_RENDER.mkdir(parents=True, exist_ok=True)
    floor = bpy.data.meshes.new("_floor")
    floor.from_pydata([(-6, -4, 0), (6, -4, 0), (6, 16, 0), (-6, 16, 0)], [], [(0, 1, 2, 3)])
    fo = bpy.data.objects.new("_floor", floor)
    sc.collection.objects.link(fo)
    fm, _, _ = H.principled("MAT_Floor", (0.30, 0.28, 0.25), rough=0.8)
    floor.materials.append(fm)
    sc.camera = H.camera(sc, "CAM_all", V((7.5, 18.0, 5.5)), V((-0.2, 6.0, 0.5)), lens=35)
    sc.render.filepath = str(OUT_RENDER / "cannon_variants_genel.png")
    bpy.ops.render.render(write_still=True)
    for k, (name, _, _) in enumerate(VARIANTS):
        y = k * 3.0
        sc.camera = H.camera(sc, f"CAM_{name}", V((2.4, y + 2.6, 1.7)), V((0.0, y, 0.6)), lens=35)
        sc.render.filepath = str(OUT_RENDER / f"{name}.png")
        bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    main()
