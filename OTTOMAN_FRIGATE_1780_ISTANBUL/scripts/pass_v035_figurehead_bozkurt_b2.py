"""v035 — Bozkurt figürü B2 (SDF yontusu, tek parça) + baş parmaklıkları yeniden.

    python3.11 OTTOMAN_FRIGATE_1780_ISTANBUL/scripts/pass_v035_figurehead_bozkurt_b2.py [--no-render | --render-only]

Kullanıcı: v034 figürü "çok kötü, low poly'den de kötü"; baş parmaklıkları "gemiden ayrı duruyor".
 1. Figür: scripts/wolf_sdf.py (skills/tersane/scripts/sdf_sculpt.py) — anatomik kurt başı (kafatası %55 / burun %45),
    açık çene, kavisli köpek dişleri, burun delikleri, hırlama kıvrımları, çatık kaş, oyuklu kulaklar; yüzeye yatan ~320
    tüy tutamı (boyun/yele, yanak, tepe, boğaz); altın gadroon kuşaklı ve rumi sarmallı kaide. Tek SDF alanı → tek parça,
    kapalı mesh (kopuk küçük kırıntılar atılır ve raporlanır) → azaltma (hero bütçe).
 2. Baş parmaklıkları: arka uçları bordadan 0,67 m uzaktaydı ve kesit 4 köşeli kutuydu → figür kaidesinden başlayıp
    borda yüzeyine gömülen Bezier yol, yuvarlatılmış silme profili (kiriş sapması kuralı), her yanda baş kıvrımına inen
    iki destek (head timber).
"""

import importlib.util
import json
import math
import sys
from pathlib import Path

import bpy  # noqa: I001
import bmesh
import numpy as np
from mathutils import Matrix, Quaternion, Vector
from mathutils.bvhtree import BVHTree

HERE = Path(__file__).resolve().parent
sp = importlib.util.spec_from_file_location("pass_v033", HERE / "pass_v033_facet_cleanup.py")
P33 = importlib.util.module_from_spec(sp)
sp.loader.exec_module(P33)
P31 = P33.P31
RS, QA, LODS, H = P31.RS, P31.QA, P31.LODS, P31.H
ROOT, SHIP = P31.ROOT, P31.SHIP
SRC_VER, VER = "v034", "v035"
sys.path.insert(0, str(HERE))
import wolf_sdf as WS  # noqa: E402
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
    # (metaball yüzeyi eleman yarıçapının ≈0,67'sinde oluşur; yarıçaplar buna göre)
    # kaide ve göğüs — baş kıvrımına ve baş parmaklıklarına oturur
    ell((-0.14, 0, 0.02), (0.72, 0.62, 0.30), (1, 0, 0), 2.4)
    ell((-0.05, 0, 0.30), (0.70, 0.52, 0.58), (1, 0, 0.4), 2.4)
    ell((0.25, 0, 0.70), (0.62, 0.46, 0.52), (1, 0, 0.8), 2.4)
    # kafatası (iri) + ağır kaş kemerleri
    ell((0.62, 0, 1.12), (0.52, 0.42, 0.40), (1, 0, 0.1), 2.6)
    for s_ in (1, -1):
        ell((0.94, 0.16 * s_, 1.27), (0.22, 0.12, 0.09), (1, 0.25 * s_, 0.3), 2.0)
        # elmacık tüy tutamları (geriye taranmış)
        for k in range(3):
            ell((0.78 - 0.10 * k, (0.30 + 0.03 * k) * s_, 1.02 - 0.10 * k), (0.34, 0.11, 0.09), (-1, 0.55 * s_, -0.35), 1.6)
        # kulaklar: geriye yatık, yassı, sivri (metaball içinde)
        ell((0.56, 0.25 * s_, 1.50), (0.36, 0.13, 0.05), (-0.55, 0.18 * s_, 0.85), 2.2)
    # geniş burun (namlu) + burun sırtı + dudak yanları
    ell((1.20, 0, 1.08), (0.48, 0.22, 0.18), (1, 0, -0.10), 2.4)
    ell((1.16, 0, 1.21), (0.42, 0.16, 0.10), (1, 0, -0.12), 1.8)
    for s_ in (1, -1):
        ell((1.26, 0.12 * s_, 1.00), (0.36, 0.10, 0.10), (1, 0, -0.12), 1.8)
    # alt çene (açık, tok çene ucu)
    ell((1.08, 0, 0.80), (0.46, 0.18, 0.13), (1, 0, -0.45), 2.4)
    ell((1.38, 0, 0.68), (0.14, 0.14, 0.10), (1, 0, -0.3), 2.2)
    # ağız boşluğu ve göz çukurları (negatif)
    ell((1.18, 0, 0.93), (0.42, 0.13, 0.075), (1, 0, -0.25), 3.0, neg=True)
    for s_ in (1, -1):
        ball((1.00, 0.215 * s_, 1.17), 0.065, 3.0, neg=True)
    # yele: 3 sıra iri alev tutamı, enseden göğse geriye-aşağı savrulur
    for row in range(3):
        n = 9
        for i in range(n):
            t = i / (n - 1)
            base = V((0.46 - 0.78 * t - 0.06 * row, 0, 1.44 - 1.10 * t - 0.05 * row))
            for s_ in (1, -1):
                side = (0.12 + 0.12 * row) + 0.14 * math.sin(math.pi * min(1.0, t * 1.2))
                c = base + V((0, side * s_, 0.02))
                d = V((-0.9, (0.25 + 0.2 * row) * s_, -0.30 - 0.45 * t))
                ell(c, (0.46 - 0.14 * t - 0.05 * row, 0.10, 0.07), d, 1.5)
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
        nt = m.node_tree
        for n in nt.nodes:
            if n.type == "VALTORGB":
                n.color_ramp.elements[0].position, n.color_ramp.elements[1].position = 0.515, 0.565
            if n.type == "MIX" and n.data_type == "RGBA":
                n.inputs["A"].default_value = (0.055, 0.075, 0.085, 1)
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


TARGET_TRIS = 260000


# ------------------------------------------------------------------ baş parmaklıkları
def _bvh(names):
    dg = bpy.context.evaluated_depsgraph_get()
    vs, ps, off = [], [], 0
    for n in names:
        o = bpy.data.objects[n]
        ev = o.evaluated_get(dg)
        m = ev.to_mesh()
        vs += [o.matrix_world @ v.co for v in m.vertices]
        ps += [tuple(i + off for i in pl.vertices) for pl in m.polygons]
        off += len(m.vertices)
        ev.to_mesh_clear()
    return BVHTree.FromPolygons(vs, ps)


def _profile(w=0.10, h=0.12, r=0.032, seg=6):
    """Kapalı yuvarlatılmış dikdörtgen silme kesiti (yerel: x yana, y yukarı)."""
    pts = []
    for cx, cy, a0 in ((w / 2 - r, h / 2 - r, 0.0), (-w / 2 + r, h / 2 - r, math.pi / 2), (-w / 2 + r, -h / 2 + r, math.pi),
                       (w / 2 - r, -h / 2 + r, 1.5 * math.pi)):
        for k in range(seg + 1):
            a = a0 + (math.pi / 2) * k / seg
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def _sweep(bm, path, prof, mat, uv):
    rings = []
    n = len(path)
    for i, p in enumerate(path):
        t = (path[min(i + 1, n - 1)] - path[max(i - 1, 0)]).normalized()
        up = V((0, 0, 1)) - t * t.z
        if up.length < 1e-6:
            up = V((0, 1, 0))
        up.normalize()
        side = t.cross(up)
        rings.append([bm.verts.new(p + side * x + up * y) for x, y in prof])
    m = len(prof)
    acc = [0.0]
    for a, b in zip(path[:-1], path[1:]):
        acc.append(acc[-1] + (b - a).length)
    fs = []
    for i in range(n - 1):
        for k in range(m):
            f = bm.faces.new([rings[i][k], rings[i][(k + 1) % m], rings[i + 1][(k + 1) % m], rings[i + 1][k]])
            for lp, t in zip(f.loops, [(acc[i], k / m), (acc[i], (k + 1) / m), (acc[i + 1], (k + 1) / m), (acc[i + 1], k / m)]):
                lp[uv].uv = t
            fs.append(f)
    fs.append(bm.faces.new(list(reversed(rings[0]))))
    fs.append(bm.faces.new(rings[-1]))
    for f in fs:
        f.material_index = mat
        f.smooth = True
    return rings


def _bezier(p0, p1, p2, p3, step=0.04):
    L = (p1 - p0).length + (p2 - p1).length + (p3 - p2).length
    n = max(8, int(L / step))
    out = []
    for i in range(n + 1):
        t = i / n
        out.append(p0 * (1 - t) ** 3 + p1 * 3 * (1 - t) ** 2 * t + p2 * 3 * (1 - t) * t ** 2 + p3 * t ** 3)
    return out


def rebuild_head_rails():
    hull = _bvh(["CORE_HULL_SHELL"])
    knee = _bvh(["CORE_HEAD_KNEE"])
    rep = {}
    for tag, s in (("S", 1), ("P", -1)):
        ob = bpy.data.objects[f"CORE_HEAD_RAIL_{tag}"]
        A = O + V((-0.28, 0.30 * s, 0.03))                                   # kaide içinde başlar
        loc, nrm, _, _ = hull.ray_cast(V((20.1, 6.0 * s, 5.15)), V((0, -s, 0)), 8.0)   # baş kovalama lumbarının önü
        if loc is None:
            rep[tag] = "gövde bulunamadı"
            continue
        B = loc + V((0, -0.03 * s, 0))                                       # bordaya 3 cm gömülü
        P1 = A + V((-1.2, 0.35 * s, -0.35))
        P2 = B + V((1.0, -0.55 * s, 0.05))
        path = _bezier(A, P1, P2, B)
        bm = bmesh.new()
        uv = bm.loops.layers.uv.new("UVMap")
        _sweep(bm, path, _profile(), 0, uv)
        n_sup = 0
        for t in (0.30, 0.58):
            i = int(t * (len(path) - 1))
            R = path[i] + V((0, 0, -0.05))
            hit = knee.ray_cast(V((R.x, 0.0, R.z + 0.5)), V((0, 0, -1)), 6.0)
            if hit[0] is None:
                continue
            K = V((R.x - 0.10, 0.15 * s, hit[0].z - 0.06))
            if (R - K).length < 0.15:
                continue
            mid = (R + K) / 2 + V((0, 0.06 * s, 0.05))
            spath = _bezier(R + V((0, 0, 0.03)), mid, mid, K + V((0, 0, -0.03)), 0.03)
            circ = [(0.042 * math.cos(2 * math.pi * k / 20), 0.042 * math.sin(2 * math.pi * k / 20)) for k in range(20)]
            _sweep(bm, spath, circ, 1, uv)
            n_sup += 1
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        old = ob.data
        me = bpy.data.meshes.new(ob.name)
        bm.to_mesh(me)
        bm.free()
        me.materials.append(bpy.data.materials["MAT_Trim_Gilt"])
        me.materials.append(bpy.data.materials["MAT_Timber_Oak"])
        RS.sharp_from_angle_keep(me, 40)
        ob.matrix_world = Matrix()
        ob.data = me
        if old.users == 0:
            bpy.data.meshes.remove(old)
        for m in list(ob.modifiers):
            ob.modifiers.remove(m)
        rep[tag] = {"aft_on_hull": [round(c, 2) for c in B], "length_m": round(sum((b - a).length for a, b in zip(path[:-1], path[1:])), 2),
                    "supports": n_sup}
    return rep


def build():
    """SDF yontusu → tek parça mesh (figür-yerel → dünya: + O)."""
    g = WS.build(0.006)
    v, f, fm = g.mesh()
    lab, cnt = WS.S.components(v, f)
    big = int(cnt.argmax())
    keep = lab == big
    dropped = {"islands": int(len(cnt) - 1), "faces": int((~keep).sum())}
    f, fm = f[keep], fm[keep]
    used = np.unique(f)
    remap = -np.ones(len(v), dtype=np.int64)
    remap[used] = np.arange(len(used))
    v, f = v[used], remap[f]
    mats = [mat_wolf(), bpy.data.materials["MAT_Figure_EyeAmber"], bpy.data.materials["MAT_Figure_Ivory"],
            bpy.data.materials["MAT_Figure_Tongue"], bpy.data.materials["MAT_Figure_NoseBlack"], bpy.data.materials["MAT_Trim_Gilt"]]
    me = WS.S.to_blender(NAME + "_hi", v + np.array(O), f, fm, mats)
    tmp = bpy.data.objects.new("_wolf_hi", me)
    bpy.context.scene.collection.objects.link(tmp)
    dc = tmp.modifiers.new("Decimate", "DECIMATE")
    dc.decimate_type, dc.ratio = "COLLAPSE", min(1.0, TARGET_TRIS / max(len(f), 1))
    dc.use_collapse_triangulate = True
    dg = bpy.context.evaluated_depsgraph_get()
    dg.update()
    out = bpy.data.meshes.new_from_object(tmp.evaluated_get(dg))
    out.name = NAME
    bpy.data.objects.remove(tmp, do_unlink=True)
    bpy.data.meshes.remove(me)
    for pl in out.polygons:
        pl.use_smooth = True
    P31.geo_uv(out)
    bm = bmesh.new()
    bm.from_mesh(out)
    bm.faces.index_update()
    n_isl = len(RS.islands(bm))
    manifold = all(e.is_manifold for e in bm.edges)
    bm.free()
    out["pieces"] = "tek SDF alanı (gövde, kaide, kulak, göz, diş, dil, burun, tüy tutamları)"
    out["islands_after_merge"] = n_isl
    out["manifold"] = manifold
    out["dropped_loose_blobs"] = dropped["islands"]
    out["dropped_faces"] = dropped["faces"]
    out["fur_clumps"] = json.dumps(getattr(g, "fur_stats", {}))
    out["parts_embedded"] = 0
    out["pieces_merged"] = 1
    return out


def render(sc):
    H.setup_render(sc, fast=True)
    sc.cycles.samples = 32
    out = ROOT / "renders" / VER
    out.mkdir(parents=True, exist_ok=True)
    for name, loc, tgt, lens in (("bozkurt_yan", O + V((0.9, 5.2, 1.0)), O + V((0.8, 0, 1.0)), 50),
                                 ("bozkurt_on", O + V((4.6, 2.4, 1.6)), O + V((0.8, 0, 1.0)), 45),
                                 ("bas_omzu", V((34.0, 14.0, 9.0)), V((21.0, 0.0, 6.5)), 35),
                                 ("parmaklik", V((25.5, 5.5, 9.5)), V((21.8, 0.6, 5.3)), 30)):
        sc.camera = H.camera(sc, f"CAM35_{name}", loc, tgt, lens=lens)
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
    old = bpy.data.objects.get("MOD_FIGUREHEAD_BOZKURT_A") or bpy.data.objects["MOD_FIGUREHEAD_BOZKURT_B"]
    col = old.users_collection[0]
    props = {k: v for k, v in old.items() if k not in ("quality_exempt", "quality")}
    for o in [o for o in bpy.data.objects if o.name.startswith(("MOD_FIGUREHEAD_BOZKURT_", "UCX_MOD_FIGUREHEAD_BOZKURT_"))]:
        me = o.data
        bpy.data.objects.remove(o, do_unlink=True)
        if me is not None and me.users == 0:
            bpy.data.meshes.remove(me)
    me = build()
    ob = bpy.data.objects.new(NAME, me)
    rails = rebuild_head_rails()
    col.objects.link(ob)
    for k, v in props.items():
        ob[k] = v
    ob["motif"] = "bozkurt (Sea Wolf konsepti) — hırlayan baş, yele, tunç + altın"
    ob["quality"] = "nihai model B2 (SDF yontusu, tek parça); UE için normal/ORM bake önerilir (malzeme pointiness kullanır)"
    s = bpy.data.objects.get("SOCKET_FIGUREHEAD")
    if s:
        s["installed_module"] = NAME
    # çarpışma: dışbükey UCX (≤ 64 köşe)
    ucx_col = bpy.data.collections["40_COLLISION"]
    pts = [v.co.copy() for v in me.vertices]
    P31.RS  # noqa: B018
    geom = __import__("geom")
    u = geom.convex_ucx(f"UCX_{NAME}_00", pts[::90], ucx_col, "figurehead", owner=NAME)
    # cıvadıra ile boşluk
    dg = bpy.context.evaluated_depsgraph_get()
    bs = bpy.data.objects["MOD_RIG_BOWSPRIT_A"]
    evb = bs.evaluated_get(dg).to_mesh()
    tb = BVHTree.FromPolygons([bs.matrix_world @ v.co for v in evb.vertices], [tuple(p.vertices) for p in evb.polygons])
    bs.evaluated_get(dg).to_mesh_clear()
    gap = min(tb.find_nearest(p, 5.0)[3] for p in pts[::5])
    for o in [o for o in bpy.data.objects if o.name.startswith(("CORE_HEAD_RAIL_S_LOD", "CORE_HEAD_RAIL_P_LOD"))]:
        bpy.data.objects.remove(o, do_unlink=True)
    LODS.build_lods(sc, only={NAME, "CORE_HEAD_RAIL_S", "CORE_HEAD_RAIL_P"})
    me.calc_loop_triangles()
    bpy.ops.wm.save_as_mainfile(filepath=str(out), compress=True)
    H.VERSION = VER
    ap = ROOT / "reports" / f"scene_audit_{VER}.json"
    arep = H.audit(sc, ap)
    arep["figurehead_v035"] = {"module": NAME, "tris": len(me.loop_triangles), "ucx_verts": len(u.data.vertices),
                               "pieces_merged": me["pieces_merged"], "islands_after_merge": me["islands_after_merge"],
                               "manifold": bool(me["manifold"]), "parts_embedded": me["parts_embedded"],
                               "dropped_loose_blobs": me["dropped_loose_blobs"], "dropped_faces": me["dropped_faces"],
                               "fur_clumps": json.loads(me["fur_clumps"]), "head_rails": rails,
                               "min_gap_to_bowsprit_m": round(gap, 3), "replaced": "MOD_FIGUREHEAD_BOZKURT_B (v034)"}
    arep["pass"] = {"name": "pass_v035_figurehead_bozkurt_b2", "source": f"Blender/versions/{SHIP}_{SRC_VER}.blend"}
    ap.write_text(json.dumps(arep, indent=2, ensure_ascii=False), encoding="utf-8")
    qa = QA.audit(sc, top=60)
    (ROOT / "reports" / f"kalite_testi_{VER}.json").write_text(json.dumps(qa, indent=1, ensure_ascii=False), encoding="utf-8")
    r = next(x for x in qa["objects"] if x["name"] == NAME)
    print("V035", json.dumps(arep["figurehead_v035"], ensure_ascii=False))
    print("V035 QA", json.dumps(qa["summary"], ensure_ascii=False), "figür:", r["fail"], r["facet_m"], r["worst_sag_mm"], r["floating_islands"][:3])
    if "--no-render" not in sys.argv:
        render(sc)


if __name__ == "__main__":
    main()
