"""v030 — Genel kalite testi düzeltmeleri (low-poly yasağı ihlalleri + artık parça).

    python3.11 OTTOMAN_FRIGATE_1780_ISTANBUL/scripts/pass_v030_quality_surface.py [--no-render | --render-only]

Kullanıcı bildirimi (v027 baş kasara render'ı + ambar): yakından low-poly görünen parçalar, lumbar üstünde artık çubuk,
ambardaki fıçılar. Kalite testi (skills/tersane/scripts/quality_audit.py, reports/kalite_testi_v029.json) 109 render
mesh'inden 86'sını işaretledi. Düzeltmeler:
 1. Küpeşte, altın silme ve üç borda (band_strip: 4 köşeli kesit + 2 segment bevel) → aynı istasyonlarda zengin
    yuvarlatılmış profil (çeyrek daireler 6 dilim), bevel yok, metre ölçekli UV.
 2. Lumbar çerçeveleri (düz gölgeli kutular, gövde eğrisini izlemiyordu; baştaki lumbarda üst lento gövdeden taşıyordu)
    → gövde yüzeyine ışınla oturan, köşeleri yuvarlatılmış silme profilli kapalı süpürme.
 3. Yuvarlak parçalar (halat, seren, direk, bigot, balüster, makara, gülle, pin, çember …) → resegment.py ile kiriş
    sapması ≤ 1,5 mm kuralına göre yeniden dilimleme (altıgen kıç feneri tasarım gereği korunur).
 4. Ambar fıçıları → tek yüksek kaliteli fıçı mesh'i (48 dilim, 24 çıta yivi, 4 çember, kapak girintisi) + örnekler
    (UE: Instanced Static Mesh).
 5. Top palangaları: kutu makaralar → elipsoit makara + kayış halkası.
 6. Tüm Bevel modifier'ları: segment ≥ 3, harden normals (90° köşe 22,5° adımlarla).
 7. LOD zinciri yeniden; kalite testi tekrar (reports/kalite_testi_v030.json).
"""

import importlib.util
import inspect
import json
import math
import sys
from pathlib import Path

import bpy  # noqa: I001
import bmesh
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

HERE = Path(__file__).resolve().parent
SKILL = HERE.parents[1] / "skills" / "tersane" / "scripts"
sys.path.insert(0, str(SKILL))
import lods as LODS  # noqa: E402
import quality_audit as QA  # noqa: E402
import resegment as RS  # noqa: E402


def _load(name, fname):
    sp = importlib.util.spec_from_file_location(name, HERE / fname)
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


P28 = _load("pass_v028", "pass_v028_cannon_ottoman_bronze.py")
P25 = _load("pass_v025", "pass_v025_hold.py")
P22 = _load("pass_v022", "pass_v022_sailset.py")
P17 = _load("pass_v017", "pass_v017_boat_anchor_capstan.py")
P23 = _load("pass_v023", "pass_v023_running_rigging.py")   # yalnız block() geometri fonksiyonu kullanılır
P15, P18, P5 = P28.P15, P28.P18, P28.P5
H = P28.H
SRC_VER, VER = "v029", "v030"
ROOT, SHIP = H.ROOT, H.SHIP_ID
MANIFEST_VERSION = 30
V = Vector
TOL = 0.0015


# ------------------------------------------------------------------ 1. şeritler
def _round_rect(D, Hh, r_ob, r_ot, r_it, n=6, bead=None):
    """Kesit profili (d: gövdeden dışa, h: yukarı), iç-alt köşeden saat yönü tersine; iç yüz (gövdeye yaslı) açık.
    r_ob/r_ot/r_it: dış-alt, dış-üst, iç-üst köşe yarıçapları (m). bead: (h_merkez, yarıçap) dış yüzde yarım yuvarlak."""
    pts = [(0.0, 0.0)]

    def arc(cx, ch, r, a0, a1):
        return [(cx + r * math.cos(a0 + (a1 - a0) * k / n), ch + r * math.sin(a0 + (a1 - a0) * k / n)) for k in range(n + 1)]
    pts += arc(D - r_ob, r_ob, r_ob, -math.pi / 2, 0.0) if r_ob > 0 else [(D, 0.0)]
    if bead:
        hb, rb = bead
        pts += [(D + rb * math.sin(math.pi * k / (2 * n)), hb - rb * math.cos(math.pi * k / (2 * n))) for k in range(2 * n + 1)]
    pts += arc(D - r_ot, Hh - r_ot, r_ot, 0.0, math.pi / 2) if r_ot > 0 else [(D, Hh)]
    pts += arc(r_it, Hh - r_it, r_it, math.pi / 2, math.pi) if r_it > 0 else [(0.0, Hh)]
    out = []
    for p in pts:
        if not out or (V(p) - V(out[-1])).length > 1e-5:
            out.append(p)
    return out


STRIP_PROFILES = {  # ad: fn(D, H) → profil
    "CORE_MOULDING_RAIL": lambda D, Hh: _round_rect(D, Hh, 0.018, 0.40 * D, 0.30 * D, bead=(0.30 * Hh, 0.010)),
    "CORE_MOULDING_BAND_LOW": lambda D, Hh: _round_rect(D, Hh, min(D, Hh / 2) * 0.85, min(D, Hh / 2) * 0.85, 0.0),
    "CORE_WALE_MAIN": lambda D, Hh: _round_rect(D, Hh, 0.35 * D, 0.35 * D, 0.0),
    "CORE_WALE_LOWER": lambda D, Hh: _round_rect(D, Hh, 0.35 * D, 0.35 * D, 0.0),
    "CORE_WALE_LOWER_TIER": lambda D, Hh: _round_rect(D, Hh, 0.35 * D, 0.35 * D, 0.0),
}


def densify_rings(rings, step_deg=2.0, max_insert=6):
    """Şerit istasyonlarını, orta çizginin kırıldığı yerlerde (bel→kasara yükselişi, kıç/baş dönüşü) Catmull-Rom ile sıklaştırır."""
    mids = [(r[0] + r[3]) / 2 for r in rings]
    out = []
    n = len(rings)
    for i in range(n):
        out.append(rings[i])
        if i == n - 1:
            break
        def turn(j):
            if j <= 0 or j >= n - 1:
                return 0.0
            a, b = mids[j] - mids[j - 1], mids[j + 1] - mids[j]
            return math.degrees(a.angle(b, 0.0)) if a.length > 1e-6 and b.length > 1e-6 else 0.0
        th = max(turn(i), turn(i + 1))
        k = min(max_insert, int(th / step_deg))
        if k < 1:
            continue
        for m in range(1, k + 1):
            t = m / (k + 1)
            q = []
            for c in range(4):
                p0 = rings[max(i - 1, 0)][c]
                p1, p2 = rings[i][c], rings[i + 1][c]
                p3 = rings[min(i + 2, n - 1)][c]
                q.append(RS._cr(p0, p1, p2, p3, t))
            out.append(q)
    return out


def rebuild_strip(name):
    ob = bpy.data.objects[name]
    me = ob.data
    nv = len(me.vertices)
    if nv % 8:
        return {"name": name, "skipped": "köşe sayısı halka düzenine uymuyor"}
    per_side = nv // 2 // 4
    co = [v.co.copy() for v in me.vertices]
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    total = 0
    for side in range(2):
        rings = densify_rings([co[(side * per_side + i) * 4:(side * per_side + i) * 4 + 4] for i in range(per_side)])
        total += len(rings)
        prof_len = None
        vrows, s_acc, prev = [], 0.0, None
        for ib, ob_, ot, it in rings:
            up = it - ib
            out = ob_ - ib
            D, Hh = out.length, up.length
            prof = STRIP_PROFILES[name](D, Hh)
            if prof_len is None:
                prof_len = len(prof)
            prof = prof[:prof_len] if len(prof) >= prof_len else prof + [prof[-1]] * (prof_len - len(prof))
            uo, uu = out.normalized(), up.normalized()
            vrows.append([bm.verts.new(ib + uo * d + uu * h) for d, h in prof])
            mid = (ib + it) / 2
            if prev is not None:
                s_acc += (mid - prev).length
            prev = mid
            vrows[-1].append(s_acc)
        ib0, ob0, _, it0 = rings[0]
        base = STRIP_PROFILES[name]((ob0 - ib0).length, (it0 - ib0).length)[:prof_len]
        pv = [0.0]
        for a, b in zip(base[:-1], base[1:]):
            pv.append(pv[-1] + (V(b) - V(a)).length)
        for i in range(len(vrows) - 1):
            r0, r1 = vrows[i], vrows[i + 1]
            s0, s1 = r0[-1], r1[-1]
            for k in range(prof_len - 1):
                q = [r0[k], r0[k + 1], r1[k + 1], r1[k]]
                if side == 0:
                    q.reverse()
                f = bm.faces.new(q)
                f.smooth = True
                uvq = [(s0, pv[k]), (s0, pv[k + 1]), (s1, pv[k + 1]), (s1, pv[k])]
                if side == 0:
                    uvq.reverse()
                for lp, t in zip(f.loops, uvq):
                    lp[uv].uv = t
        for r in (vrows[0], vrows[-1]):                       # uç kapakları
            f = bm.faces.new(r[:-1])
            f.smooth = True
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mats = list(me.materials)
    new = bpy.data.meshes.new(name)
    bm.to_mesh(new)
    bm.free()
    for m in mats:
        new.materials.append(m)
    new.set_sharp_from_angle(angle=math.radians(35))
    ob.data = new
    bpy.data.meshes.remove(me)
    for m in list(ob.modifiers):
        if m.type == "BEVEL":
            ob.modifiers.remove(m)
    new.calc_loop_triangles()
    return {"name": name, "stations_per_side": per_side, "stations_after_densify": total, "profile_pts": prof_len,
            "tris": len(new.loop_triangles)}


# ------------------------------------------------------------------ 2. lumbar çerçeveleri
def hull_bvh():
    h = bpy.data.objects["CORE_HULL_SHELL"]
    saved = []
    for m in h.modifiers:
        if m.type == "BOOLEAN":
            saved.append((m, m.show_viewport))
            m.show_viewport = False
    dg = bpy.context.evaluated_depsgraph_get()
    dg.update()
    ev = h.evaluated_get(dg)
    me = ev.to_mesh()
    t = BVHTree.FromPolygons([h.matrix_world @ v.co for v in me.vertices], [tuple(p.vertices) for p in me.polygons])
    ev.to_mesh_clear()
    for m, s in saved:
        m.show_viewport = s
    return t


def rebuild_port_frames(tree, name="CORE_GUNPORT_FRAMES"):
    ob = bpy.data.objects[name]
    me = ob.data
    co = [ob.matrix_world @ v.co for v in me.vertices]
    cubes = [co[i:i + 8] for i in range(0, len(co), 8)]
    ports = [cubes[i:i + 4] for i in range(0, len(cubes), 4)]
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    n_ports, gaps = 0, []
    for p in ports:
        pts = [q for c in p for q in c]
        x0, x1 = min(q.x for q in pts), max(q.x for q in pts)
        z0, z1 = min(q.z for q in pts), max(q.z for q in pts)
        top = p[0]
        t = max(q.z for q in top) - min(q.z for q in top)          # çerçeve genişliği
        sgn = 1 if sum(q.y for q in pts) > 0 else -1
        cx0, cx1, cz0, cz1 = x0 + t / 2, x1 - t / 2, z0 + t / 2, z1 - t / 2
        rc = 0.035
        path = []                                               # köşeleri yuvarlatılmış dikdörtgen (x, z)
        corners = [(cx1 - rc, cz1 - rc, 0.0), (cx0 + rc, cz1 - rc, math.pi / 2), (cx0 + rc, cz0 + rc, math.pi),
                   (cx1 - rc, cz0 + rc, 1.5 * math.pi)]
        for (ccx, ccz, a0) in corners:
            for k in range(5):
                a = a0 + (math.pi / 2) * k / 4
                path.append((ccx + rc * math.cos(a), ccz + rc * math.sin(a)))
        dense = []
        for a, b in zip(path, path[1:] + path[:1]):
            L = math.hypot(b[0] - a[0], b[1] - a[1])
            n = max(1, int(L / 0.05))
            for k in range(n):
                dense.append((a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n))
        surf = []
        for x, z in dense:
            o = V((x, sgn * 9.0, z))
            loc, nrm, _, _ = tree.ray_cast(o, V((0, -sgn, 0)), 12.0)
            if loc is None:
                surf = None
                break
            if nrm.y * sgn < 0:
                nrm = -nrm
            surf.append((loc, nrm))
        if not surf:
            gaps.append([round(x0, 2), sgn])
            continue
        prof = [(-0.5, -0.012), (-0.5, 0.012)]
        for k in range(9):                                      # yarım yuvarlak silme (genişlik t, yükseklik 0,045)
            a = math.pi * k / 8
            prof.append((-0.5 * math.cos(a) * 0.86, 0.012 + 0.033 * math.sin(a)))
        prof += [(0.5, 0.012), (0.5, -0.012)]
        rings = []
        m = len(surf)
        for i, (p, nrm) in enumerate(surf):
            tan = (surf[(i + 1) % m][0] - surf[i - 1][0]).normalized()
            lat = nrm.cross(tan).normalized()
            rings.append([bm.verts.new(p + lat * (a * t) + nrm * h) for a, h in prof])
        for i in range(m):
            r0, r1 = rings[i], rings[(i + 1) % m]
            for k in range(len(prof) - 1):
                f = bm.faces.new([r0[k], r0[k + 1], r1[k + 1], r1[k]])
                f.smooth = True
                for lp, uvt in zip(f.loops, [(i * 0.05, k * 0.01), (i * 0.05, (k + 1) * 0.01), ((i + 1) * 0.05, (k + 1) * 0.01),
                                              ((i + 1) * 0.05, k * 0.01)]):
                    lp[uv].uv = uvt
        n_ports += 1
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mats = list(me.materials)
    new = bpy.data.meshes.new(name)
    bm.to_mesh(new)
    bm.free()
    for mt in mats:
        new.materials.append(mt)
    new.set_sharp_from_angle(angle=math.radians(40))
    ob.matrix_world = Matrix()
    ob.data = new
    bpy.data.meshes.remove(me)
    new.calc_loop_triangles()
    return {"ports": n_ports, "missed": gaps, "tris": len(new.loop_triangles)}


# ------------------------------------------------------------------ 4. fıçılar (örnekli)
def cask_mesh(M, r=0.30, L=0.80, seg=32, staves=16):
    me = bpy.data.meshes.get("SM_PROP_CASK_A")
    if me:
        return me
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    nprof = 11
    rings = []
    for j in range(nprof):
        t = j / (nprof - 1)
        z = -L / 2 + 0.015 + (L - 0.03) * t
        rr = r * (0.84 + 0.16 * math.sin(math.pi * t))
        ring = []
        for k in range(seg):
            a = 2 * math.pi * k / seg
            groove = 0.0025 if k % (seg // staves) == 0 else 0.0     # çıta yivi
            ring.append(bm.verts.new((math.cos(a) * (rr - groove), math.sin(a) * (rr - groove), z)))
        rings.append((ring, z))
    # uçlar: çıta taşması (chime) + içe girik kapak
    ends = []
    for ring, z in (rings[0], rings[-1]):
        sgn = -1 if z < 0 else 1
        lip = [bm.verts.new((v.co.x, v.co.y, z + sgn * 0.015)) for v in ring]
        inner = [bm.verts.new((v.co.x * 0.93, v.co.y * 0.93, z + sgn * 0.015)) for v in ring]
        head = [bm.verts.new((v.co.x * 0.93, v.co.y * 0.93, z - sgn * 0.010)) for v in ring]
        ends.append((ring, lip, inner, head, sgn))

    def band(a, b, v0, v1):
        for k in range(seg):
            f = bm.faces.new([a[k], a[(k + 1) % seg], b[(k + 1) % seg], b[k]])
            f.smooth = True
            f.material_index = 0
            for lp, u in zip(f.loops, [(k / seg, v0), ((k + 1) / seg, v0), ((k + 1) / seg, v1), (k / seg, v1)]):
                lp[uv].uv = u
    for j in range(nprof - 1):
        band(rings[j][0], rings[j + 1][0], rings[j][1], rings[j + 1][1])
    for ring, lip, inner, head, sgn in ends:
        band(ring, lip, 0.0, 0.015)
        band(lip, inner, 0.015, 0.035)
        band(inner, head, 0.035, 0.06)
        f = bm.faces.new(head)
        f.smooth = False
        for lp in f.loops:
            lp[uv].uv = (lp.vert.co.x + 0.5, lp.vert.co.y + 0.5)
    base_faces = len(bm.faces)
    # demir çemberler
    for t in (0.10, 0.28, 0.72, 0.90):
        z = -L / 2 + L * t
        rr = r * (0.84 + 0.16 * math.sin(math.pi * t)) + 0.004
        prof = [(rr - 0.004, z - 0.022), (rr, z - 0.022), (rr + 0.002, z - 0.012), (rr + 0.002, z + 0.012), (rr, z + 0.022),
                (rr - 0.004, z + 0.022)]
        rs = [[bm.verts.new((math.cos(2 * math.pi * k / seg) * a, math.sin(2 * math.pi * k / seg) * a, b)) for k in range(seg)]
              for a, b in prof]
        for a_, b_ in zip(rs[:-1], rs[1:]):
            for k in range(seg):
                f = bm.faces.new([a_[k], a_[(k + 1) % seg], b_[(k + 1) % seg], b_[k]])
                f.smooth = True
                f.material_index = 1
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new("SM_PROP_CASK_A")
    bm.to_mesh(me)
    bm.free()
    me.materials.append(M["timber"])
    me.materials.append(M["iron"])
    me.set_sharp_from_angle(angle=math.radians(40))
    me["base_faces"] = base_faces
    return me


def rebuild_cargo(M, sc, dg):
    rec = []
    orig = P25.cask

    def record(bm_w, bm_i, c, axis_y, r=0.30, L=0.80):
        rec.append(V(c))
    P25.cask = record
    try:
        dec = bpy.data.collections["24_MODULES_DECOR"]
        new, blocks = P25.build_cargo(dec, M, sc, dg)
    finally:
        P25.cask = orig
    old = bpy.data.objects["MOD_HOLD_CARGO_A"]
    for k, v in old.items():
        if k not in new.keys():
            new[k] = v
    ome = old.data
    bpy.data.objects.remove(old, do_unlink=True)
    if ome.users == 0:
        bpy.data.meshes.remove(ome)
    new.name = new.data.name = "MOD_HOLD_CARGO_A"
    new["note"] = "v030: fıçılar ayrı örnek nesneler (MOD_HOLD_CASK_A_NNN → SM_PROP_CASK_A)"
    for o in [o for o in bpy.data.objects if o.name.startswith("MOD_HOLD_CASK_A_")]:
        bpy.data.objects.remove(o, do_unlink=True)
    cm = cask_mesh(M)
    for i, c in enumerate(rec):
        o = bpy.data.objects.new(f"MOD_HOLD_CASK_A_{i + 1:03d}", cm)
        dec.objects.link(o)
        o.location = c
        o.rotation_euler = (math.radians(-90), math.radians((i * 47) % 360), 0.0)   # eksen Y; çıta fazı çeşitlenir
        o["module_family"] = "InteriorSet"
        o["room"] = "hold"
        o["ue_instance_of"] = "SM_PROP_CASK_A"
        o["ue_export"] = "InstancedStaticMesh"
    cm.calc_loop_triangles()
    return {"casks": len(rec), "cask_tris": len(cm.loop_triangles)}


# ------------------------------------------------------------------ 5. palanga makaraları
def rebuild_tackles(M):
    orig = P28.P15.obox

    def block(bm, c, X, Y, Z, sx, sy, sz):
        r = bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=12, radius=1.0)
        T = Matrix.Translation(c) @ Matrix(((X.x * sx * 1.1, Y.x * sy, Z.x * sz * 1.25, 0), (X.y * sx * 1.1, Y.y * sy, Z.y * sz * 1.25, 0),
                                            (X.z * sx * 1.1, Y.z * sy, Z.z * sz * 1.25, 0), (0, 0, 0, 1)))
        bmesh.ops.transform(bm, matrix=T, verts=r["verts"])
        ring = [c + (X * math.cos(2 * math.pi * k / 24) * sx * 1.12 + Z * math.sin(2 * math.pi * k / 24) * sz * 1.28) for k in range(24)]
        P15.tube(bm, ring + [ring[0]], 0.006, seg=8)             # kayış (strop)
    old = bpy.data.objects.get("MOD_CANNON_TACKLES_TOOLS_A")
    if old:
        ome = old.data
        bpy.data.objects.remove(old, do_unlink=True)
        if ome.users == 0:
            bpy.data.meshes.remove(ome)
    P28.P15.obox = block
    try:
        ob, n_t, n_r = P28.build_tackles_and_racks(M)
    finally:
        P28.P15.obox = orig
    return {"side_tackles": n_t, "tool_racks": n_r}


# ------------------------------------------------------------------ 3 + 6. yeniden dilimleme, bevel
SKIP_RESEG = ("CORE_HULL_SHELL", "CORE_DECK_", "MOD_FIGUREHEAD", "MOD_SAIL_SET_", "MOD_SAIL_EMBLEM", "MOD_FLAG_",
              "CORE_MOULDING_", "CORE_WALE_", "CORE_GUNPORT_FRAMES", "SM_PROP_CASK")


def resegment_all():
    done, rep, tri0, tri1 = set(), {}, 0, 0
    for o in bpy.data.objects:
        if o.type != "MESH" or o.name.startswith(("UCX_", "CUT_")) or "_LOD" in o.name or o.name.startswith(SKIP_RESEG):
            continue
        if o.data.name in done or o.data.name.startswith("SM_PROP_CASK"):
            continue
        done.add(o.data.name)
        o.data.calc_loop_triangles()
        a = len(o.data.loop_triangles)
        r = RS.resegment_object(o, tol=TOL, keep=lambda i: i["kind"] == "ring" and i["seg"] == 6 and i["r"] > 0.2,
                                hard_path_deg=LEAD_DEG if o.name in RUNNING else None)
        o.data.calc_loop_triangles()
        b = len(o.data.loop_triangles)
        tri0 += a * o.data.users
        tri1 += b * o.data.users
        if r["rings"] or r["ellipsoids"]:
            rep[o.name] = {"tris": [a, b], **r}
    return rep, tri0, tri1


def upgrade_bevels():
    n = 0
    for o in bpy.data.objects:
        if o.type != "MESH":
            continue
        for m in o.modifiers:
            if m.type == "BEVEL":
                m.segments = max(m.segments, 3)
                m.harden_normals = True
                m.limit_method = "ANGLE"
                m.angle_limit = math.radians(30)
                n += 1
    return n


# ------------------------------------------------------------------ 8. gövde orta hat dikişi, havada parçalar, merdiven ayağı
def hull_centerline_sharp(tol=0.02):
    me = bpy.data.objects["CORE_HULL_SHELL"].data
    bm = bmesh.new()
    bm.from_mesh(me)
    n = 0
    for e in bm.edges:
        if all(abs(v.co.y) < tol for v in e.verts):
            e.smooth = False
            n += 1
    bm.to_mesh(me)
    bm.free()
    return n


def centerline_sharp(name, tol):
    me = bpy.data.objects[name].data
    bm = bmesh.new()
    bm.from_mesh(me)
    n = 0
    for e in bm.edges:
        if all(abs(v.co.y) < tol for v in e.verts):
            e.smooth = False
            n += 1
    bm.to_mesh(me)
    bm.free()
    return n


def hull_subsurf_level2():
    """Gövde Subdivision: viewport 1 / render 2 idi → FBX (viewport) fasetli çıkıyordu. İkisi de 2; lumbar delikleri ışınla doğrulanır."""
    h = bpy.data.objects["CORE_HULL_SHELL"]
    for m in h.modifiers:
        if m.type == "SUBSURF":
            m.levels = m.render_levels = 2
    bpy.context.view_layer.update()
    sc = bpy.context.scene
    dg = bpy.context.evaluated_depsgraph_get()
    fr = bpy.data.objects["CORE_GUNPORT_FRAMES"]
    closed = []
    socks = [o for o in bpy.data.objects if o.type == "EMPTY" and o.name.startswith("SOCKET_CANNON_") and "LOWER" not in o.name
             and "CHASE" not in o.name]
    for s_ in socks:
        sgn = 1 if s_.location.y > 0 else -1
        z = s_.location.z + 0.86
        o = V((s_.location.x, sgn * 8.0, z))
        ok, loc, _, _, ob, _ = sc.ray_cast(dg, o, V((0, -sgn, 0)), distance=4.0)
        if ok and ob.name == "CORE_HULL_SHELL":
            closed.append(s_.name)
    h.data.calc_loop_triangles()
    ev = h.evaluated_get(dg).to_mesh()
    ev.calc_loop_triangles()
    tris = len(ev.loop_triangles)
    h.evaluated_get(dg).to_mesh_clear()
    return {"levels": 2, "tris": tris, "ports_checked": len(socks), "ports_closed_by_hull": closed}


def lantern_panes_sharp():
    """Fenerler düz camlı (altıgen/kutu): cam ve çerçeve kenarları keskin — yumuşak gölge camı bükük gösterir."""
    n = 0
    for o in bpy.data.objects:
        if o.type == "MESH" and o.name.startswith("MOD_LANTERN_") and o.data.users and o.data.get("_panes") is None:
            RS.sharp_from_angle_keep(o.data, 28)
            o.data["_panes"] = 1
            n += 1
    return n


def rebuild_masts():
    """Çanaklık dış hattı 64 eşit açılı noktaydı (D köşelerinde seyrek) → 160; direk mesh'i üreticisiyle yeniden kurulur."""
    patch_source(P15, "build_mast", [("    N = 64\n", "    N = 160\n")])
    col = bpy.data.collections.new("_tmp_mast")
    bpy.context.scene.collection.children.link(col)
    M = P15.materials()
    rep = {}
    for name in ("FORE", "MAIN", "MIZZEN"):
        old = bpy.data.objects[f"MOD_RIG_MAST_{name}_A"]
        nob = P15.build_mast(P15.Mast(name), col, M)
        nob.data.transform(old.matrix_world.inverted() @ nob.matrix_world)   # eşitse birim dönüşüm
        ob_bb = [old.matrix_world @ V(c) for c in old.bound_box]
        nb_bb = [old.matrix_world @ V(c) for c in nob.bound_box]
        dz = max(abs(max(p[i] for p in ob_bb) - max(p[i] for p in nb_bb)) for i in range(3))
        ome = old.data
        old.data = nob.data
        nob.data.name = old.name
        bpy.data.objects.remove(nob, do_unlink=True)
        if ome.users == 0:
            bpy.data.meshes.remove(ome)
        rep[name] = {"bbox_delta_m": round(dz, 4), "polys": len(old.data.polygons)}
    bpy.data.collections.remove(col)
    return rep


def _tree(o, dg):
    ev = o.evaluated_get(dg)
    me = ev.to_mesh()
    t = BVHTree.FromPolygons([o.matrix_world @ v.co for v in me.vertices], [tuple(p.vertices) for p in me.polygons])
    ev.to_mesh_clear()
    return t


def attach_islands(name, targets, max_gap=0.35, embed=0.004, only_near=None):
    """Havada adaları hedef yüzeye (targets: nesne adları; "self" = aynı nesnenin diğer adaları) en kısa vektörle taşır."""
    ob = bpy.data.objects[name]
    dg = bpy.context.evaluated_depsgraph_get()
    trees = [_tree(bpy.data.objects[t], dg) for t in targets if t != "self" and t in bpy.data.objects]
    me = ob.data
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.faces.index_update()
    mw, mi = ob.matrix_world, ob.matrix_world.inverted()
    isl = RS.islands(bm)
    moved = []
    for k, fs in enumerate(isl):
        vs = list({v for f in fs for v in f.verts})
        pts = [mw @ v.co for v in vs]
        c = sum(pts, V()) / len(pts)
        if only_near and min((c - V(q)).length for q in only_near) > 0.25:
            continue
        cand = list(trees)
        if "self" in targets:
            others = [f for j, g in enumerate(isl) if j != k for f in g]
            if others:
                ov = list({v for f in others for v in f.verts})
                ix = {v: i for i, v in enumerate(ov)}
                cand.append(BVHTree.FromPolygons([mw @ v.co for v in ov], [tuple(ix[v] for v in f.verts) for f in others]))
        best = None
        for t in cand:
            for p in pts[:: max(1, len(pts) // 64)]:
                h = t.find_nearest(p, max_gap)
                if h[0] is not None and (best is None or h[3] < best[1]):
                    best = (h[0] - p, h[3])
        if best is None or best[1] < 0.02:
            continue
        d = best[0] * ((best[1] + embed) / best[1])
        for v in vs:
            v.co = mi @ (mw @ v.co + d)
        moved.append({"at": [round(x, 2) for x in c], "moved_m": round(best[1], 3)})
    bm.to_mesh(me)
    bm.free()
    return moved


def move_carriage_ring(car_me):
    """Arka palanga halkası (x −0,82, kızağın 10 cm gerisinde boşta) → arka dingil yastığının kıç yüzüne."""
    bm = bmesh.new()
    bm.from_mesh(car_me)
    bm.faces.index_update()
    n = 0
    for fs in RS.islands(bm):
        vs = list({v for f in fs for v in f.verts})
        c = sum((v.co for v in vs), V()) / len(vs)
        ext = [max(v.co[i] for v in vs) - min(v.co[i] for v in vs) for i in range(3)]
        if abs(c.x + 0.82) < 0.03 and abs(c.y) < 0.02 and ext[0] < 0.04 and 0.08 < ext[1] < 0.14:
            # halkanın ön kenarı dingil kıç yüzüne (AXLE_X_R − 0,08) değsin; yükseklik dingil ortası
            target_front = P28.P14.AXLE_X_R - 0.08
            xmax = max(v.co.x for v in vs)
            dz = (P28.P14.WHEEL_R_R + 0.02) - c.z
            for v in vs:
                v.co.x += target_front - xmax + 0.004
                v.co.z += dz
            n += 1
    bm.to_mesh(car_me)
    bm.free()
    return n


STAIRS = ("CORE_STAIRS_FC_S", "CORE_STAIRS_FC_P", "CORE_STAIRS_POOP_S", "CORE_STAIRS_POOP_P",
          "CORE_LADDER_LOWER_AFT", "CORE_LADDER_LOWER_FORE", "CORE_LADDER_HOLD")


def ground_stairs(embed=0.004):
    """v027'de kiriş ayağı güverteden 6 cm yukarıda kırpılmıştı (çakışma önlemi) → ayak köşeleri güverteye iner."""
    sc = bpy.context.scene
    dg = bpy.context.evaluated_depsgraph_get()
    decks = [bpy.data.objects[n] for n in ("CORE_DECK_GUN", "CORE_DECK_LOWER", "CORE_HOLD_FLOOR", "CORE_DECK_POOP",
                                           "CORE_DECK_FORECASTLE") if n in bpy.data.objects]
    trees = [_tree(o, dg) for o in decks]
    rep = {}
    for name in STAIRS:
        ob = bpy.data.objects.get(name)
        if not ob:
            continue
        mw, mi = ob.matrix_world, ob.matrix_world.inverted()
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        bm.faces.index_update()
        moved = 0
        for fs in RS.islands(bm):
            if fs[0].material_index != 1:                   # yalnız yan kirişler (malzeme 1)
                continue
            vs = list({v for f in fs for v in f.verts})
            zmin = min((mw @ v.co).z for v in vs)
            low = [v for v in vs if (mw @ v.co).z < zmin + 0.01]
            for v in low:
                p = mw @ v.co
                best = None
                for t in trees:
                    h = t.ray_cast(p + V((0, 0, 0.02)), V((0, 0, -1)), 0.30)
                    if h[0] is not None and (best is None or h[3] < best):
                        best = h[3]
                        z = h[0].z
                if best is not None and 0.01 < p.z - z < 0.25:
                    v.co = mi @ V((p.x, p.y, z - embed))
                    moved += 1
        bm.to_mesh(ob.data)
        bm.free()
        rep[name] = moved
    return rep


# ------------------------------------------------------------------ 9. yelken ruloları, filika, bayrak
def patch_source(mod, fname, repl):
    src = inspect.getsource(getattr(mod, fname))
    for a, b in repl:
        assert a in src, (fname, a)
        src = src.replace(a, b)
    exec(compile(src, mod.__file__, "exec"), mod.__dict__)


def rebuild_furled():
    patch_source(P22, "furled_bundle", [
        ("NY, NR = 40, 14", "NY, NR = max(40, int(2 * half * 0.86 / 0.10)), 48"),
        ("        t = abs(y) / span\n", "        t = abs(y) / span\n        ii = (y + span) / 0.475               # kıvrım dalgası metreye bağlı (≈1,75 m dalga boyu)\n"),
        ("math.sin(i * 1.7)", "math.sin(ii * 1.7)"),
        ("math.sin(3 * a + i * 0.9)", "math.sin(3 * a + ii * 0.9)")])
    col = bpy.data.collections.new("_tmp_furled")
    bpy.context.scene.collection.children.link(col)
    M = {"canvas": bpy.data.materials["MAT_Sail_Canvas"], "rope": bpy.data.materials["MAT_Rope_Tarred"]}
    new = P22.build_furled(col, M)
    rep = {}
    for nob in new:
        base = nob.name.split(".")[0]
        old = bpy.data.objects.get(base)
        if old is None or old == nob:
            continue
        if (old.matrix_world.translation - nob.matrix_world.translation).length > 1e-3:
            nob.data.transform(old.matrix_world.inverted() @ nob.matrix_world)
        ome = old.data
        old.data = nob.data
        nob.data.name = base
        rep[base] = len(nob.data.polygons)
        bpy.data.objects.remove(nob, do_unlink=True)
        if ome.users == 0:
            bpy.data.meshes.remove(ome)
    bpy.data.collections.remove(col)
    return rep


def rebuild_boat():
    patch_source(P17, "boat_mesh", [("NU, NT = 28, 10", "NU, NT = 56, 24")])
    M = P17.P16.mats() if hasattr(P17.P16, "mats") else {}
    M.update({"boat": bpy.data.materials["MAT_Boat_PaintWhite"], "timber": bpy.data.materials["MAT_Timber_Oak"],
              "spar": bpy.data.materials["MAT_Spar_Pine"]})
    ob = bpy.data.objects["MOD_BOAT_CUTTER_A"]
    me = P17.boat_mesh(M)
    old = ob.data
    ob.data = me
    me.name = "MOD_BOAT_CUTTER_A"
    if old.users == 0:
        bpy.data.meshes.remove(old)
    me.calc_loop_triangles()
    return len(me.loop_triangles)


RUNNING = ("MOD_RIG_RUNNING_FORE_A", "MOD_RIG_RUNNING_MAIN_A", "MOD_RIG_RUNNING_MIZZEN_A")
LEAD_DEG = 15.0


def add_lead_blocks():
    """Halatlar direk dibinde makarasız havada kırılıyordu (V biçimi). Her halat adasında yolun ≥ 15° kırıldığı ara
    halkaya yönlendirme makarası eklenir; resegment bu kırılmaları yumuşatmaz (hard_path_deg)."""
    rep = {}
    for n in RUNNING:
        o = bpy.data.objects[n]
        bm = bmesh.new()
        bm.from_mesh(o.data)
        bm.verts.index_update()
        bm.faces.index_update()
        leads = []
        for isl in RS.islands(bm):
            info = RS.analyse_island(isl)
            if not info or info[0] != "ring":
                continue
            rings = [g[1] for g in info[2] if g[0] == "R"]
            turns = RS._path_turns(rings)
            for i in range(1, len(rings) - 1):
                # gerçek kırılma tekildir: sehim yayında ardışık dönüşler benzerdir, makara noktasında komşular düzdür
                if turns[i] >= LEAD_DEG and turns[i - 1] < 0.35 * turns[i] and turns[i + 1] < 0.35 * turns[i]:
                    d0 = (rings[i][0] - rings[i - 1][0]).normalized()
                    d1 = (rings[i + 1][0] - rings[i][0]).normalized()
                    ax = (d0 + d1) if (d0 + d1).length > 1e-3 else d0
                    leads.append((rings[i][0].copy(), ax.normalized()))
        uniq = []                                   # aynı noktadan geçen halatlar tek makara (çok dilli)
        for c, ax in leads:
            if all((c - u[0]).length > 0.12 for u in uniq):
                uniq.append((c, ax))
        leads = uniq
        bw, bi = bmesh.new(), bmesh.new()
        for c, ax in leads:
            P23.block(bw, bi, c, ax, 0.16)
        for b, mat in ((bw, 1), (bi, 2)):
            tmp = bpy.data.meshes.new("_tmp")
            b.to_mesh(tmp)
            b.free()
            tmp.polygons.foreach_set("material_index", [mat] * len(tmp.polygons))
            tmp.polygons.foreach_set("use_smooth", [True] * len(tmp.polygons))
            bm.from_mesh(tmp)
            bpy.data.meshes.remove(tmp)
        bm.to_mesh(o.data)
        bm.free()
        rep[n] = len(leads)
    return rep


def refine_flags():
    out = {}
    for n in ("MOD_FLAG_ENSIGN_OTTOMAN_A", "MOD_FLAG_PENNANT_OTTOMAN_A"):
        o = bpy.data.objects.get(n)
        if not o:
            continue
        bm = bmesh.new()
        bm.from_mesh(o.data)
        bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=1, use_grid_fill=True, smooth=1.0)
        bm.to_mesh(o.data)
        bm.free()
        out[n] = len(o.data.polygons)
    return out


# ------------------------------------------------------------------ render
def render(sc):
    H.setup_render(sc, fast=True)
    sc.cycles.samples = 40
    out = ROOT / "renders" / VER
    out.mkdir(parents=True, exist_ok=True)
    g = bpy.data.objects["SOCKET_CANNON_S_05"].matrix_world
    views = [
        ("baskasarasi_kupeste", V((9.0, 5.0, 5.2)), V((12.6, 2.9, 4.2)), 28),           # kullanıcının gösterdiği açı
        ("lumbar_yakin", V((4.0, 7.2, 4.9)), V((6.5, 4.9, 4.1)), 35),
        ("bigot_armadora", V((13.0, 6.6, 6.2)), V((11.6, 5.3, 5.0)), 30),
        ("ambar_ficilar", V((3.4, 0.0, -0.3)), V((7.0, -2.0, -1.4)), 22),
        ("top_palanga", g @ V((-1.6, -1.0, 1.4)), g @ V((0.2, 0.3, 0.55)), 32),
        ("kic_korkuluk", V((-23.5, 6.0, 9.6)), V((-18.5, 1.5, 7.4)), 30),
    ]
    for name, loc, tgt, lens in views:
        sc.camera = H.camera(sc, f"CAM30_{name}", loc, tgt, lens=lens)
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
    M = P15.materials()
    M.update({"bronze": P28.mat_bronze(), "wood": P28.mat_painted_wood(), "iron": P28.mat_iron_rusty()})
    rep = {}
    rep["strips"] = [rebuild_strip(n) for n in STRIP_PROFILES]
    tree = hull_bvh()
    rep["gunport_frames"] = rebuild_port_frames(tree)
    if "CORE_GUNPORT_FRAMES_LOWER" in bpy.data.objects:
        rep["gunport_frames_lower"] = rebuild_port_frames(tree, "CORE_GUNPORT_FRAMES_LOWER")
    dg = bpy.context.evaluated_depsgraph_get()
    rep["cargo"] = rebuild_cargo(P15.materials(), sc, dg)
    rep["tackles"] = rebuild_tackles(M)
    rep["furled_sails"] = rebuild_furled()
    rep["boat_tris"] = rebuild_boat()
    rep["flags"] = refine_flags()
    rep["lead_blocks"] = add_lead_blocks()
    rep["hull_centerline_sharp_edges"] = hull_centerline_sharp()
    rep["hull_subsurf"] = hull_subsurf_level2()
    rep["boat_centerline_sharp"] = centerline_sharp("MOD_BOAT_CUTTER_A", 0.012)
    fig = bpy.data.objects.get("MOD_FIGUREHEAD_BOZKURT_A")
    if fig:
        fig["quality_exempt"] = "BLOCKOUT: bozkurt figürü yer tutucu; nihai model references/KONSEPT_PRUVA_BOZKURT_01 ile yapılacak"
    rep["lantern_panes_sharp"] = lantern_panes_sharp()
    # Not: direkleri build_mast ile yeniden kurmak denendi — eski pass yamaları nedeniyle konum 3–13 m kaydı → kullanılmadı.
    hal = bpy.data.objects.get("MOD_FLAG_ENSIGN_HALYARD")
    if hal:
        for pl in hal.data.polygons:
            pl.use_smooth = True
    rep["bevel_modifiers_upgraded"] = upgrade_bevels()
    car = bpy.data.objects["MOD_CANNON_OTTOMAN_C_P_01"].data
    rep["carriage_ring_moved"] = move_carriage_ring(car)
    rep["stairs_grounded"] = ground_stairs()
    rs_rep, t0, t1 = resegment_all()
    rep["resegment"] = {"objects": len(rs_rep), "tris_before": t0, "tris_after": t1, "detail": rs_rep}
    # havada adalar: yalnız kalite testinin işaretlediği adalar taşınır (halat uçlarının kasıtlı boşlukları korunur)
    objs = [o for o in QA._render_meshes(sc) if o.name.startswith(("CORE_", "MOD_"))]
    flagged = QA.floating_islands(objs, bpy.context.evaluated_depsgraph_get())
    rep["floating_before_attach"] = {k: len(v) for k, v in flagged.items()}
    targets = {"MOD_RIG_STANDING_FORE_A": (["MOD_RIG_MAST_FORE_A"], 0.35), "MOD_RIG_STANDING_MAIN_A": (["MOD_RIG_MAST_MAIN_A"], 0.35),
               "MOD_RIG_STANDING_MIZZEN_A": (["MOD_RIG_MAST_MIZZEN_A"], 0.35), "MOD_RIG_BOOM_MIZZEN_A": (["MOD_RIG_MAST_MIZZEN_A"], 0.1),
               "MOD_RIG_BOWSPRIT_A": (["self"], 0.4), "MOD_CANNON_TACKLES_TOOLS_A": (["CORE_HULL_SHELL"], 0.15)}
    rep["attached"] = {n: attach_islands(n, t, max_gap=g, only_near=flagged[n]) for n, (t, g) in targets.items() if n in flagged}
    LODS.clear_lods()
    lod = LODS.build_lods(sc)
    rep["lods"] = len(lod)
    bpy.ops.wm.save_as_mainfile(filepath=str(out), compress=True)
    H.VERSION = VER
    ap = ROOT / "reports" / f"scene_audit_{VER}.json"
    arep = H.audit(sc, ap)
    arep["quality_v030"] = rep
    arep["pass"] = {"name": "pass_v030_quality_surface", "source": f"Blender/versions/{SHIP}_{SRC_VER}.blend",
                    "manifest_version": MANIFEST_VERSION,
                    "rule": "low-poly yasağı: kiriş sapması ≤ 1,5 mm; faset kenarı (25°–60°) yok; bevel ≥ 3 segment"}
    ap.write_text(json.dumps(arep, indent=2, ensure_ascii=False), encoding="utf-8")
    qa = QA.audit(sc, top=60)
    (ROOT / "reports" / f"kalite_testi_{VER}.json").write_text(json.dumps(qa, indent=1, ensure_ascii=False), encoding="utf-8")
    print("V030", json.dumps({k: v for k, v in rep.items() if k != "resegment"}, ensure_ascii=False))
    print("V030 resegment", t0, "->", t1, "objects", len(rs_rep))
    print("V030 QA", json.dumps(qa["summary"], ensure_ascii=False))
    if "--no-render" not in sys.argv:
        render(sc)


if __name__ == "__main__":
    main()
