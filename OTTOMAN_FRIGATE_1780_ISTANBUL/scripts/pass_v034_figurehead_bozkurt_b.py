"""v034 — Bozkurt figürü, nihai model B (kullanıcı konsepti: references/KONSEPT_PRUVA_BOZKURT_01.webp "Sea Wolf").

    python3.11 OTTOMAN_FRIGATE_1780_ISTANBUL/scripts/pass_v034_figurehead_bozkurt_b.py [--no-render | --render-only]

Konsept: pruvada, cıvadıranın altında öne uzanan, ağzı açık hırlayan kurt başı; koyu mavimsi tunç, altın vurgular,
geriye savrulan yele. v021 blockout'u (oturan köpek biçimi, skin modifier) kaldırılır.
Tek parça: parçalar önce ayrı kurulur, sonra EXACT boolean birleşimiyle tek kapalı mesh olur (oyunlarda pruva figürü tek
parça; SOCKET_FIGUREHEAD'e takılan modül de tek parça değişir).
Yöntem: metaball yontma (kafatası, burun, açık çene, kaş kemeri, elmacık, boyun/göğüs, 22 yele tutamı) → mesh →
voxel remesh + yumuşatma → azaltma (oyun bütçesi). Kulak, diş, göz, dil, burun ayrı parçalar. Üslup ve ölçüler [TAHMİN].
"""

import importlib.util
import json
import math
import sys
from pathlib import Path

import bpy  # noqa: I001
import bmesh
from mathutils import Matrix, Quaternion, Vector
from mathutils.bvhtree import BVHTree

HERE = Path(__file__).resolve().parent
sp = importlib.util.spec_from_file_location("pass_v033", HERE / "pass_v033_facet_cleanup.py")
P33 = importlib.util.module_from_spec(sp)
sp.loader.exec_module(P33)
P31 = P33.P31
RS, QA, LODS, H = P31.RS, P31.QA, P31.LODS, P31.H
ROOT, SHIP = P31.ROOT, P31.SHIP
SRC_VER, VER = "v033", "v034"
V = Vector
O = V((24.25, 0.0, 5.55))            # SOCKET_FIGUREHEAD (baş kıvrımının üst ucu)
NAME = "MOD_FIGUREHEAD_BOZKURT_B"


def q_dir(d, roll=0.0):
    """Yerel +X'i d yönüne çeviren dönüş (metaball elipsoidi için)."""
    q = V((1, 0, 0)).rotation_difference(V(d).normalized())
    return q @ Quaternion(V((1, 0, 0)), roll)


def sculpt_mball():
    mb = bpy.data.metaballs.new("_mb_wolf")
    mb.resolution = mb.render_resolution = 0.018
    mb.threshold = 0.6

    def ell(c, r, d=(1, 0, 0), stiff=2.0, neg=False):
        e = mb.elements.new(type="ELLIPSOID")
        e.co = V(c)
        e.radius = 1.0
        e.size_x, e.size_y, e.size_z = r
        e.rotation = q_dir(d)
        e.stiffness = stiff
        e.use_negative = neg
        return e

    def ball(c, r, stiff=2.0, neg=False):
        e = mb.elements.new(type="BALL")
        e.co = V(c)
        e.radius = r
        e.stiffness = stiff
        e.use_negative = neg
    # göğüs ve boyun (baş kıvrımına oturur, öne-yukarı uzanır)
    # (metaball yüzeyi eleman yarıçapının ≈0,67'sinde oluşur → yarıçaplar buna göre; kopukluk olmasın diye köprü elemanları)
    ell((-0.10, 0, 0.30), (0.62, 0.46, 0.56), (1, 0, 0.55), 2.4)
    ell((0.05, 0, 0.52), (0.52, 0.42, 0.50), (1, 0, 0.8), 2.4)
    ell((0.24, 0, 0.78), (0.54, 0.40, 0.46), (1, 0, 0.9), 2.4)
    ell((0.45, 0, 1.00), (0.46, 0.36, 0.40), (1, 0, 0.5), 2.4)
    # kaide: baş kıvrımı üstünde yassı, geniş taban — baş parmaklıklarının uçları buna oturur (eski blockout kaidesinin yeri)
    ell((-0.14, 0, 0.02), (0.72, 0.62, 0.30), (1, 0, 0), 2.4)
    # kafatası, kaş kemeri, elmacık
    ell((0.62, 0, 1.16), (0.34, 0.27, 0.26), (1, 0, 0.15), 2.4)
    for s in (1, -1):
        ell((0.84, 0.12 * s, 1.27), (0.12, 0.08, 0.055), (1, 0.2 * s, 0.25), 1.6)
        ell((0.76, 0.18 * s, 1.06), (0.17, 0.09, 0.11), (1, 0.3 * s, -0.2), 1.8)
    # üst burun (namlu): kafatasından öne, uca doğru incelir
    for k in range(7):
        t = k / 6
        ball((0.88 + 0.52 * t, 0, 1.12 - 0.05 * t), 0.155 - 0.075 * t, 2.4)
    ell((1.14, 0, 1.17), (0.30, 0.12, 0.075), (1, 0, -0.08), 1.8)            # burun sırtı
    # alt çene (açık, ~24° aşağı)
    for k in range(6):
        t = k / 5
        ball((0.86 + 0.42 * t, 0, 0.94 - 0.19 * t), 0.115 - 0.05 * t, 2.2)
    # ağız boşluğu (negatif) ve göz çukurları
    ell((1.10, 0, 0.98), (0.28, 0.075, 0.05), (1, 0, -0.18), 3.0, neg=True)
    for s in (1, -1):
        ball((0.87, 0.165 * s, 1.18), 0.045, 3.0, neg=True)
    # yele: ense ve boyun boyunca geriye-aşağı savrulan tutamlar (alev/rumi biçimi)
    n = 11
    for i in range(n):
        t = i / (n - 1)
        base = V((0.52 - 0.62 * t, 0, 1.30 - 0.95 * t))
        for s in (1, -1):
            side = 0.10 + 0.20 * math.sin(math.pi * min(1.0, t * 1.2))
            c = base + V((0, side * s, 0.04))
            d = V((-0.9, 0.35 * s, -0.25 - 0.4 * t))
            ell(c, (0.34 - 0.10 * t, 0.070, 0.050), d, 1.4)
    return mb


def mball_to_mesh(mb):
    ob = bpy.data.objects.new("_wolf_mb", mb)
    bpy.context.scene.collection.objects.link(ob)
    dg = bpy.context.evaluated_depsgraph_get()
    dg.update()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    bpy.data.objects.remove(ob, do_unlink=True)
    bpy.data.metaballs.remove(mb)
    tmp = bpy.data.objects.new("_wolf_tmp", me)
    bpy.context.scene.collection.objects.link(tmp)
    rm = tmp.modifiers.new("Remesh", "REMESH")
    rm.mode, rm.voxel_size, rm.adaptivity = "VOXEL", 0.010, 0.0
    sm = tmp.modifiers.new("Smooth", "CORRECTIVE_SMOOTH")
    sm.iterations, sm.factor, sm.use_only_smooth = 8, 0.5, True
    dc = tmp.modifiers.new("Decimate", "DECIMATE")
    dc.decimate_type, dc.ratio = "COLLAPSE", 0.30
    dg = bpy.context.evaluated_depsgraph_get()
    dg.update()
    out = bpy.data.meshes.new_from_object(tmp.evaluated_get(dg))
    bpy.data.objects.remove(tmp, do_unlink=True)
    bpy.data.meshes.remove(me)
    return out


def cone(bm, base, tip, r, seg=16, mat=0):
    d = tip - base
    q = V((0, 0, 1)).rotation_difference(d.normalized()).to_matrix().to_4x4()
    T = Matrix.Translation(base) @ q
    L = d.length
    prof = [(r, 0.0), (r * 0.8, L * 0.45), (r * 0.35, L * 0.85), (0.0, L)]
    rings = [[bm.verts.new(T @ V((rr * math.cos(2 * math.pi * k / seg), rr * math.sin(2 * math.pi * k / seg), z)))
              for k in range(seg)] if rr > 0 else [bm.verts.new(T @ V((0, 0, z)))] for rr, z in prof]
    fs = [bm.faces.new(list(reversed(rings[0])))]
    for a, b in zip(rings[:-1], rings[1:]):
        for k in range(seg):
            if len(b) == 1:
                fs.append(bm.faces.new([a[k], a[(k + 1) % seg], b[0]]))
            else:
                fs.append(bm.faces.new([a[k], a[(k + 1) % seg], b[(k + 1) % seg], b[k]]))
    for f in fs:
        f.material_index = mat
        f.smooth = True


def sphere(bm, c, r, mat, scale=(1, 1, 1), seg=24):
    res = bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=seg // 2, radius=r)
    for v in res["verts"]:
        v.co = c + V((v.co.x * scale[0], v.co.y * scale[1], v.co.z * scale[2]))
    for f in {f for v in res["verts"] for f in v.link_faces}:
        f.material_index = mat
        f.smooth = True


def ear(bm, base, s, mat):
    """Sivri, arkaya yatık kulak: üçgen kesitli, içi oyuk görünümlü (iki katman)."""
    pts = []
    tip = base + V((-0.16, 0.06 * s, 0.30))
    for k in range(13):
        t = k / 12
        a = math.pi * t
        pts.append(base + V((0.10 * math.cos(a), 0.035 * s * math.sin(a) * 0.5, 0.0)) + (tip - base) * (math.sin(a) ** 6) * 0)
    # kulak: taban elipsinden uca lathe benzeri daralma
    d = tip - base
    q = V((0, 0, 1)).rotation_difference(d.normalized()).to_matrix().to_4x4()
    T = Matrix.Translation(base) @ q
    L = d.length
    seg = 20
    rings = []
    for j in range(9):
        t = j / 8
        rx, ry = 0.10 * (1 - t) ** 0.8, 0.045 * (1 - t) ** 0.8
        if j == 8:
            rings.append([bm.verts.new(T @ V((0, 0, L)))])
            break
        rings.append([bm.verts.new(T @ V((rx * math.cos(2 * math.pi * k / seg), ry * math.sin(2 * math.pi * k / seg), L * t)))
                      for k in range(seg)])
    fs = [bm.faces.new(list(reversed(rings[0])))]
    for a, b in zip(rings[:-1], rings[1:]):
        for k in range(seg):
            if len(b) == 1:
                fs.append(bm.faces.new([a[k], a[(k + 1) % seg], b[0]]))
            else:
                fs.append(bm.faces.new([a[k], a[(k + 1) % seg], b[(k + 1) % seg], b[k]]))
    for f in fs:
        f.material_index = mat
        f.smooth = True


def mat_wolf():
    m = bpy.data.materials.get("MAT_Figure_WolfBronzeGilt")
    if m:
        return m
    m = bpy.data.materials.new("MAT_Figure_WolfBronzeGilt")
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    ramp = nt.nodes.new("ShaderNodeValToRGB")                 # sivri/çıkıntı → altın, çukur → koyu tunç
    ramp.color_ramp.elements[0].position, ramp.color_ramp.elements[1].position = 0.50, 0.56
    nt.links.new(geo.outputs["Pointiness"], ramp.inputs["Fac"])
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.inputs["A"].default_value = (0.035, 0.05, 0.06, 1)    # koyu mavimsi tunç
    mix.inputs["B"].default_value = (0.78, 0.55, 0.20, 1)     # altın
    nt.links.new(ramp.outputs["Color"], mix.inputs["Factor"])
    nt.links.new(mix.outputs["Result"], b.inputs["Base Color"])
    b.inputs["Metallic"].default_value = 0.9
    rr = nt.nodes.new("ShaderNodeMapRange")
    rr.inputs["To Min"].default_value, rr.inputs["To Max"].default_value = 0.42, 0.25
    nt.links.new(ramp.outputs["Color"], rr.inputs["Value"])
    nt.links.new(rr.outputs["Result"], b.inputs["Roughness"])
    m["ue_note"] = "UE: pointiness yok → bake (BC/ORM) ya da vertex color/curvature maskesi"
    return m


def _obj(name, bm, mats):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for m in mats:
        me.materials.append(m)
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def keep_largest(me):
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.faces.index_update()
    isl = sorted(RS.islands(bm), key=len, reverse=True)
    drop = [v for fs in isl[1:] for v in {v for f in fs for v in f.verts}]
    if drop:
        bmesh.ops.delete(bm, geom=list(set(drop)), context="VERTS")
    bm.to_mesh(me)
    bm.free()
    return len(isl) - 1


def build():
    """Önce parçalar (gövde, kulaklar, gözler, dişler, burun, dil) ayrı nesne olarak kurulur, sonra EXACT boolean
    birleşimiyle TEK kapalı mesh'e dönüştürülür (oyunda pruva figürü tek parça; modül değişimi de tek parça)."""
    mats = [mat_wolf(), bpy.data.materials["MAT_Figure_EyeAmber"], bpy.data.materials["MAT_Figure_Ivory"],
            bpy.data.materials["MAT_Figure_Tongue"], bpy.data.materials["MAT_Figure_NoseBlack"]]
    body_me = mball_to_mesh(sculpt_mball())
    dropped = keep_largest(body_me)
    body_me.materials.clear()
    for m in mats:
        body_me.materials.append(m)
    for pl in body_me.polygons:
        pl.material_index = 0
        pl.use_smooth = True
    body = bpy.data.objects.new("_wolf_body", body_me)
    bpy.context.scene.collection.objects.link(body)
    parts = []
    for s in (1, -1):
        bm = bmesh.new()
        ear(bm, V((0.50, 0.15 * s, 1.36)), s, 0)
        parts.append(_obj(f"_ear_{s}", bm, mats))
        bm = bmesh.new()
        sphere(bm, V((0.872, 0.160 * s, 1.18)), 0.046, 1)                    # göz: oyuğa değer
        parts.append(_obj(f"_eye_{s}", bm, mats))
        bm = bmesh.new()
        cone(bm, V((1.25, 0.065 * s, 1.08)), V((1.27, 0.070 * s, 0.95)), 0.021, 16, 2)   # üst köpek dişi
        cone(bm, V((1.15, 0.045 * s, 0.76)), V((1.19, 0.060 * s, 0.93)), 0.019, 16, 2)   # alt köpek dişi (kök çenede)
        parts.append(_obj(f"_fang_{s}", bm, mats))
        for k in range(4):
            x = 1.00 + 0.055 * k
            bm = bmesh.new()
            cone(bm, V((x, 0.080 * s, 1.14)), V((x, 0.085 * s, 1.03)), 0.012, 12, 2)     # taban diş etine gömülü
            parts.append(_obj(f"_tu_{s}_{k}", bm, mats))
            bm = bmesh.new()
            cone(bm, V((x - 0.02, 0.066 * s, 0.82 - 0.02 * k)), V((x - 0.02, 0.070 * s, 0.925 - 0.02 * k)), 0.011, 12, 2)
            parts.append(_obj(f"_tl_{s}_{k}", bm, mats))
    bm = bmesh.new()
    sphere(bm, V((1.40, 0, 1.10)), 0.058, 4, (1.1, 1.0, 0.8))
    parts.append(_obj("_nose", bm, mats))
    bm = bmesh.new()
    sphere(bm, V((1.05, 0, 0.95)), 0.10, 3, (1.8, 0.55, 0.30))
    parts.append(_obj("_tongue", bm, mats))
    # gövdeye değmeyen parça, yüzeye en yakın doğrultuda 8 mm gömülene kadar taşınır (tek parça birleşim için)
    tree = BVHTree.FromPolygons([v.co.copy() for v in body_me.vertices], [tuple(pl.vertices) for pl in body_me.polygons])
    embedded = 0
    for p in parts:
        pv = [v.co.copy() for v in p.data.vertices]
        pt = BVHTree.FromPolygons(pv, [tuple(pl.vertices) for pl in p.data.polygons])
        if tree.overlap(pt):
            continue
        best = None
        for q in pv:
            loc, nrm, _, d = tree.find_nearest(q, 1.0)
            if loc is not None and (best is None or d < best[1]):
                best = (loc - q, d)
        if best is None:
            continue
        mv = best[0].normalized() * (best[1] + 0.008)
        p.data.transform(Matrix.Translation(mv))
        embedded += 1
    for p in parts:
        md = body.modifiers.new(p.name, "BOOLEAN")
        md.operation, md.object, md.solver = "UNION", p, "EXACT"
        md.use_self = False
        md.material_mode = "TRANSFER"
    dg = bpy.context.evaluated_depsgraph_get()
    dg.update()
    me = bpy.data.meshes.new_from_object(body.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg)
    me.name = NAME
    for o in parts + [body]:
        pm = o.data
        bpy.data.objects.remove(o, do_unlink=True)
        if pm.users == 0:
            bpy.data.meshes.remove(pm)
    if me.materials[0] is None or len(me.materials) < len(mats):
        me.materials.clear()
        for m in mats:
            me.materials.append(m)
    me.transform(Matrix.Translation(O))
    for pl in me.polygons:
        pl.use_smooth = True
    RS.sharp_from_angle_keep(me, 60)
    P31.geo_uv(me)
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.faces.index_update()
    n_isl = len(RS.islands(bm))
    manifold = all(e.is_manifold for e in bm.edges)
    bm.free()
    me["pieces_merged"] = len(parts) + 1
    me["islands_after_merge"] = n_isl
    me["manifold"] = manifold
    me["dropped_loose_blobs"] = dropped
    me["parts_embedded"] = embedded
    return me


def render(sc):
    H.setup_render(sc, fast=True)
    sc.cycles.samples = 32
    out = ROOT / "renders" / VER
    out.mkdir(parents=True, exist_ok=True)
    for name, loc, tgt, lens in (("bozkurt_yan", O + V((0.9, 5.2, 1.0)), O + V((0.8, 0, 1.0)), 50),
                                 ("bozkurt_on", O + V((4.6, 2.4, 1.6)), O + V((0.8, 0, 1.0)), 45),
                                 ("bas_omzu", V((34.0, 14.0, 9.0)), V((21.0, 0.0, 6.5)), 35)):
        sc.camera = H.camera(sc, f"CAM34_{name}", loc, tgt, lens=lens)
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
    old = bpy.data.objects["MOD_FIGUREHEAD_BOZKURT_A"]
    col = old.users_collection[0]
    props = {k: v for k, v in old.items() if k not in ("quality_exempt", "quality")}
    for o in [o for o in bpy.data.objects if o.name.startswith("MOD_FIGUREHEAD_BOZKURT_A") or o.name.startswith("UCX_MOD_FIGUREHEAD_BOZKURT_A")]:
        me = o.data
        bpy.data.objects.remove(o, do_unlink=True)
        if me is not None and me.users == 0:
            bpy.data.meshes.remove(me)
    me = build()
    ob = bpy.data.objects.new(NAME, me)
    col.objects.link(ob)
    for k, v in props.items():
        ob[k] = v
    ob["motif"] = "bozkurt (Sea Wolf konsepti) — hırlayan baş, yele, tunç + altın"
    ob["quality"] = "nihai model B (metaball yontma + remesh); UE için normal/ORM bake önerilir"
    s = bpy.data.objects.get("SOCKET_FIGUREHEAD")
    if s:
        s["installed_module"] = NAME
    # çarpışma: dışbükey UCX (≤ 64 köşe)
    ucx_col = bpy.data.collections["40_COLLISION"]
    pts = [v.co.copy() for v in me.vertices]
    P31.RS  # noqa: B018
    geom = __import__("geom")
    u = geom.convex_ucx(f"UCX_{NAME}_00", pts[::40], ucx_col, "figurehead", owner=NAME)
    # cıvadıra ile boşluk
    dg = bpy.context.evaluated_depsgraph_get()
    bs = bpy.data.objects["MOD_RIG_BOWSPRIT_A"]
    evb = bs.evaluated_get(dg).to_mesh()
    tb = BVHTree.FromPolygons([bs.matrix_world @ v.co for v in evb.vertices], [tuple(p.vertices) for p in evb.polygons])
    bs.evaluated_get(dg).to_mesh_clear()
    gap = min(tb.find_nearest(p, 5.0)[3] for p in pts[::5])
    LODS.build_lods(sc, only={NAME})
    me.calc_loop_triangles()
    bpy.ops.wm.save_as_mainfile(filepath=str(out), compress=True)
    H.VERSION = VER
    ap = ROOT / "reports" / f"scene_audit_{VER}.json"
    arep = H.audit(sc, ap)
    arep["figurehead_v034"] = {"module": NAME, "tris": len(me.loop_triangles), "ucx_verts": len(u.data.vertices),
                               "pieces_merged": me["pieces_merged"], "islands_after_merge": me["islands_after_merge"],
                               "manifold": bool(me["manifold"]), "parts_embedded": me["parts_embedded"],
                               "dropped_loose_blobs": me["dropped_loose_blobs"],
                               "min_gap_to_bowsprit_m": round(gap, 3), "replaced": "MOD_FIGUREHEAD_BOZKURT_A (blockout)"}
    arep["pass"] = {"name": "pass_v034_figurehead_bozkurt_b", "source": f"Blender/versions/{SHIP}_{SRC_VER}.blend"}
    ap.write_text(json.dumps(arep, indent=2, ensure_ascii=False), encoding="utf-8")
    qa = QA.audit(sc, top=60)
    (ROOT / "reports" / f"kalite_testi_{VER}.json").write_text(json.dumps(qa, indent=1, ensure_ascii=False), encoding="utf-8")
    r = next(x for x in qa["objects"] if x["name"] == NAME)
    print("V034", json.dumps(arep["figurehead_v034"], ensure_ascii=False))
    print("V034 QA", json.dumps(qa["summary"], ensure_ascii=False), "figür:", r["fail"], r["facet_m"], r["worst_sag_mm"], r["floating_islands"][:3])
    if "--no-render" not in sys.argv:
        render(sc)


if __name__ == "__main__":
    main()
