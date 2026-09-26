"""Tersane — gemiden bağımsız bmesh geometri yardımcıları (Blender 4.x/5.x bpy).

Kullanım:  import sys; sys.path.append("<skill>/scripts"); import geom
Tüm fonksiyonlar dünya ya da yerel koordinatta çalışır; birim metre.
"""

import math

import bmesh
import bpy
from mathutils import Matrix, Vector

V = Vector


def box8(bm, c):
    """8 köşeli kutu. c: alt 4 (saat yönü) + üst 4 köşe."""
    v = [bm.verts.new(p) for p in c]
    for f in ((0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)):
        bm.faces.new([v[i] for i in f])


def aabox(bm, x0, x1, y0, y1, z0, z1):
    box8(bm, [V((x0, y0, z0)), V((x1, y0, z0)), V((x1, y1, z0)), V((x0, y1, z0)),
              V((x0, y0, z1)), V((x1, y0, z1)), V((x1, y1, z1)), V((x0, y1, z1))])


def obox(bm, c, X, Y, Z, sx, sy, sz):
    """Yönlü kutu: merkez c, eksenler X/Y/Z, yarı boyutlar."""
    pts = []
    for dz in (-sz, sz):
        for dx, dy in ((-sx, -sy), (sx, -sy), (sx, sy), (-sx, sy)):
            pts.append(c + X * dx + Y * dy + Z * dz)
    box8(bm, pts)


def lathe(bm, profile, seg, mat=Matrix()):
    """(yarıçap, z) profilini yerel Z etrafında döndürür; `mat` ile yerleştirir. r=0 noktaları kapak olur."""
    rings = []
    for r, z in profile:
        if r < 1e-6:
            rings.append([bm.verts.new(mat @ V((0.0, 0.0, z)))])
        else:
            rings.append([bm.verts.new(mat @ V((r * math.cos(2 * math.pi * k / seg), r * math.sin(2 * math.pi * k / seg), z)))
                          for k in range(seg)])
    for a, b in zip(rings[:-1], rings[1:]):
        if len(a) == 1 and len(b) == 1:
            continue
        if len(a) == 1:
            for k in range(seg):
                bm.faces.new([a[0], b[(k + 1) % seg], b[k]])
        elif len(b) == 1:
            for k in range(seg):
                bm.faces.new([a[k], a[(k + 1) % seg], b[0]])
        else:
            for k in range(seg):
                bm.faces.new([a[k], a[(k + 1) % seg], b[(k + 1) % seg], b[k]])


def axis_matrix(origin, axis):
    """Yerel Z'yi `axis` yönüne çeviren dönüşüm (lathe'i bir doğrultuya yatırmak için)."""
    q = V((0, 0, 1)).rotation_difference(V(axis).normalized())
    return Matrix.Translation(V(origin)) @ q.to_matrix().to_4x4()


def tube(bm, pts, r, seg=6):
    """Nokta dizisi boyunca yuvarlak halat (uçlar kapalı)."""
    pts = [V(p) for p in pts]
    rings = []
    for i, p in enumerate(pts):
        a, b = pts[max(i - 1, 0)], pts[min(i + 1, len(pts) - 1)]
        t = (b - a).normalized()
        u = t.cross(V((0, 0, 1)))
        if u.length < 1e-3:
            u = t.cross(V((1, 0, 0)))
        u.normalize()
        w = t.cross(u)
        rings.append([bm.verts.new(p + (u * math.cos(2 * math.pi * k / seg) + w * math.sin(2 * math.pi * k / seg)) * r)
                      for k in range(seg)])
    for r0, r1 in zip(rings[:-1], rings[1:]):
        for k in range(seg):
            bm.faces.new([r0[k], r0[(k + 1) % seg], r1[(k + 1) % seg], r1[k]])
    bm.faces.new(list(reversed(rings[0])))
    bm.faces.new(rings[-1])


def spar(bm, p0, p1, r0, r1, seg=16, rmid=None):
    """p0→p1 konik ağaç (direk, seren, cıvadıra)."""
    d = V(p1) - V(p0)
    prof = [(0.0, 0.0), (r0, 0.0)] + ([(rmid, d.length / 2)] if rmid else []) + [(r1, d.length), (0.0, d.length)]
    lathe(bm, prof, seg, axis_matrix(p0, d))


def uv_box_fallback(me):
    """UV'si olmayan yüzlere metre ölçekli kutu projeksiyonu (tile doku ile uyumlu)."""
    if not me.uv_layers:
        me.uv_layers.new(name="UVMap")
    uv = me.uv_layers.active.data
    for p in me.polygons:
        n = p.normal
        for li in p.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            if abs(n.z) > max(abs(n.x), abs(n.y)):
                uv[li].uv = (co.x, co.y)
            elif abs(n.y) > abs(n.x):
                uv[li].uv = (co.x, co.z)
            else:
                uv[li].uv = (co.y, co.z)


def finish(name, parts, col, sharp_deg=35, bevel=None, smooth=True):
    """parts: [(bmesh, malzeme)] → tek nesne; normal düzeltme, pürüzsüz/keskin kenar, UV, isteğe bağlı bevel."""
    merged = bmesh.new()
    mats = []
    for idx, (b, mat) in enumerate(parts):
        bmesh.ops.recalc_face_normals(b, faces=b.faces)     # ters yüz (ör. kırmızı görünen kapak) önlemi
        tmp = bpy.data.meshes.new("_tmp")
        b.to_mesh(tmp)
        b.free()
        tmp.polygons.foreach_set("material_index", [idx] * len(tmp.polygons))
        merged.from_mesh(tmp)
        bpy.data.meshes.remove(tmp)
        mats.append(mat)
    me = bpy.data.meshes.new(name)
    merged.to_mesh(me)
    merged.free()
    for m in mats:
        me.materials.append(m)
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
    me.set_sharp_from_angle(angle=math.radians(sharp_deg))
    uv_box_fallback(me)
    ob = bpy.data.objects.new(name, me)
    col.objects.link(ob)
    if bevel:
        m = ob.modifiers.new("Bevel", "BEVEL")
        m.width = bevel
        m.segments = 2
        m.limit_method = "ANGLE"
    return ob


def convex_ucx(name, pts, col, purpose, owner=None, max_verts=64):
    """Dışbükey UCX. Köşe sınırını aşarsa örnekleri seyreltir. Ad: UCX_<RenderMesh>_NN."""
    for step in (1, 2, 3, 4, 6, 8):
        bm = bmesh.new()
        for p in pts[::step]:
            bm.verts.new(p)
        bmesh.ops.convex_hull(bm, input=bm.verts)
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
        if len(bm.verts) <= max_verts or step == 8:
            break
        bm.free()
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    col.objects.link(ob)
    ob.display_type = "WIRE"
    ob.hide_render = True
    ob["ucx_purpose"] = purpose
    if owner:
        ob["owner_mesh"] = owner
    return ob


def rename_two_phase(objs, fmt):
    """`.001` çakışmasız sıralı yeniden adlandırma: fmt.format(i=...)"""
    for i, o in enumerate(objs):
        o.name = f"_tmp_rn_{i}"
    for i, o in enumerate(objs):
        o.name = fmt.format(i=i)
        if o.data is not None:
            o.data.name = o.name
