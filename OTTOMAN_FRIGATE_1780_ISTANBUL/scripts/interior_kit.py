"""İç düzen parça kütüphanesi (Kızıl Sancak iç yerleşimi, v041+).

Kalite kuralı (skills/tersane): yuvarlak parçalar kiriş sapması ≤ 1,5 mm (RS.required_segments), kutu kenarları
≥ 3 dilim pah, yumuşak gölge + keskin kenar (sharp_from_angle_keep). Ölçüler metre; +X baş, +Z yukarı.
Oda kimlikleri: Ek Cilt II s. 81 — CompartmentID ≠ RoomLabel ≠ OperationalStationID ≠ WatertightZoneID.
"""

import math

import bmesh
import bpy
from mathutils import Matrix, Vector

V = Vector
RS = None            # pass betiği atar (skills/tersane/scripts/resegment)


def seg_for(r, lo=8, hi=64):
    return RS.required_segments(max(r, 1e-4), 0.0015, lo, hi)


# ------------------------------------------------------------------ temel katılar
def box(bm, c, size, r=0.008, mat=0, segs=3):
    """Pahlı kutu: c merkez, size (sx, sy, sz) tam boyut."""
    ret = bmesh.ops.create_cube(bm, size=1.0)
    vs = ret["verts"]
    sx, sy, sz = size
    for v in vs:
        v.co = V(c) + V((v.co.x * sx, v.co.y * sy, v.co.z * sz))
    r = min(r, 0.45 * min(size))
    if r > 0.004:                                        # çeyrek yay dilimi: kiriş sapması ≤ 1,5 mm
        segs = max(segs, math.ceil((math.pi / 2) / math.acos(max(1 - 0.0015 / r, -1.0))))
    edges = list({e for v in vs for e in v.link_edges})
    res = bmesh.ops.bevel(bm, geom=vs + edges, offset=r, segments=segs, profile=0.5, affect="EDGES", clamp_overlap=True)
    fs = list({f for v in vs if v.is_valid for f in v.link_faces} | set(res.get("faces", [])))
    for f in fs:
        f.material_index = mat
        f.smooth = True
    return fs


def cyl(bm, p0, p1, r, mat=0, caps=True, r1=None):
    """p0→p1 silindir/koni (kapaklı)."""
    p0, p1 = V(p0), V(p1)
    r1 = r if r1 is None else r1
    seg = seg_for(max(r, r1))
    ax = (p1 - p0)
    L = ax.length
    q = V((0, 0, 1)).rotation_difference(ax.normalized()).to_matrix().to_4x4()
    T = Matrix.Translation(p0) @ q
    a = [bm.verts.new(T @ V((r * math.cos(2 * math.pi * k / seg), r * math.sin(2 * math.pi * k / seg), 0))) for k in range(seg)]
    b = [bm.verts.new(T @ V((r1 * math.cos(2 * math.pi * k / seg), r1 * math.sin(2 * math.pi * k / seg), L))) for k in range(seg)]
    fs = [bm.faces.new([a[k], a[(k + 1) % seg], b[(k + 1) % seg], b[k]]) for k in range(seg)]
    if caps:
        fs.append(bm.faces.new(list(reversed(a))))
        fs.append(bm.faces.new(b))
    for f in fs:
        f.material_index = mat
        f.smooth = True
    return fs


def lathe(bm, prof, base, axis=(0, 0, 1), mat=0):
    """prof: [(r, z)] — r=0 uçlar kutup."""
    rmax = max(r for r, _ in prof)
    seg = seg_for(rmax, 12)
    q = V((0, 0, 1)).rotation_difference(V(axis).normalized()).to_matrix().to_4x4()
    T = Matrix.Translation(V(base)) @ q
    rings = []
    for r, z in prof:
        if r < 1e-6:
            rings.append([bm.verts.new(T @ V((0, 0, z)))])
        else:
            rings.append([bm.verts.new(T @ V((r * math.cos(2 * math.pi * k / seg), r * math.sin(2 * math.pi * k / seg), z)))
                          for k in range(seg)])
    fs = []
    for a, b in zip(rings[:-1], rings[1:]):
        if len(a) == 1 and len(b) > 1:
            fs += [bm.faces.new([a[0], b[(k + 1) % seg], b[k]]) for k in range(seg)]
        elif len(b) == 1 and len(a) > 1:
            fs += [bm.faces.new([a[k], a[(k + 1) % seg], b[0]]) for k in range(seg)]
        elif len(a) > 1:
            fs += [bm.faces.new([a[k], a[(k + 1) % seg], b[(k + 1) % seg], b[k]]) for k in range(seg)]
    for f in fs:
        f.material_index = mat
        f.smooth = True
    return fs


def tube(bm, pts, r, mat=0, seg=None):
    """Nokta dizisi boyunca halat/boru (paralel taşıma çerçevesi, kapaklı)."""
    pts = [V(p) for p in pts]
    seg = seg or seg_for(r, 6)
    t0 = (pts[1] - pts[0]).normalized()
    n = t0.orthogonal().normalized()
    rings = []
    prev = t0
    for i, p in enumerate(pts):
        t = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        n = prev.rotation_difference(t) @ n
        n = (n - t * n.dot(t)).normalized()
        b = t.cross(n)
        prev = t
        rings.append([bm.verts.new(p + (n * math.cos(2 * math.pi * k / seg) + b * math.sin(2 * math.pi * k / seg)) * r) for k in range(seg)])
    fs = []
    for a, b in zip(rings[:-1], rings[1:]):
        fs += [bm.faces.new([a[k], a[(k + 1) % seg], b[(k + 1) % seg], b[k]]) for k in range(seg)]
    fs.append(bm.faces.new(list(reversed(rings[0]))))
    fs.append(bm.faces.new(rings[-1]))
    for f in fs:
        f.material_index = mat
        f.smooth = True
    return fs


def catenary(p0, p1, sag, n=16):
    p0, p1 = V(p0), V(p1)
    return [p0.lerp(p1, t) + V((0, 0, -sag * 4 * t * (1 - t))) for t in (i / (n - 1) for i in range(n))]


# ------------------------------------------------------------------ bileşik parçalar
def plank_partition(bm, a, b, z0, z1, t=0.035, plank=0.18, gap=0.004, door=None, mat=0, trim_mat=None):
    """a→b doğrultusunda (yatay, 2B) tahta bölme; door=(merkez_mesafe, en, yükseklik) açıklık + kasa."""
    a, b = V((a[0], a[1], 0)), V((b[0], b[1], 0))
    d = (b - a)
    L = d.length
    u = d.normalized()
    nrm = V((-u.y, u.x, 0))
    ang = math.atan2(u.y, u.x)
    n = max(1, int(L / plank))
    w = L / n
    trim_mat = mat if trim_mat is None else trim_mat
    for k in range(n):
        s0, s1 = k * w, (k + 1) * w
        sc = (s0 + s1) / 2
        zt = z1
        zb = z0
        if door:
            dc, dw, dh = door
            if abs(sc - dc) < dw / 2:
                zb = z0 + dh                                # kapı üstü tahta
                if zb >= z1 - 0.02:
                    continue
        c = a + u * sc + V((0, 0, (zb + zt) / 2))
        fs = box(bm, (0, 0, 0), (w - gap, t, zt - zb), r=0.004, mat=mat)
        vs = list({v for f in fs for v in f.verts})
        bmesh.ops.rotate(bm, verts=vs, cent=V((0, 0, 0)), matrix=Matrix.Rotation(ang, 3, "Z"))
        bmesh.ops.translate(bm, verts=vs, vec=c)
    # üst ve alt kuşak + kapı kasası
    for zc, hh in ((z1 - 0.04, 0.08), (z0 + 0.05, 0.10)):
        segs = [(0.0, L)]
        if door and zc < z0 + door[2]:
            dc, dw, _ = door
            segs = [(0.0, dc - dw / 2), (dc + dw / 2, L)]
        for s0, s1 in segs:
            if s1 - s0 < 0.02:
                continue
            c = a + u * ((s0 + s1) / 2) + nrm * 0.0 + V((0, 0, zc))
            fs = box(bm, (0, 0, 0), (s1 - s0, t + 0.02, hh), r=0.006, mat=trim_mat)
            vs = list({v for f in fs for v in f.verts})
            bmesh.ops.rotate(bm, verts=vs, cent=V((0, 0, 0)), matrix=Matrix.Rotation(ang, 3, "Z"))
            bmesh.ops.translate(bm, verts=vs, vec=c)
    if door:
        dc, dw, dh = door
        for s in (dc - dw / 2 - 0.035, dc + dw / 2 + 0.035):
            c = a + u * s + V((0, 0, z0 + dh / 2))
            fs = box(bm, (0, 0, 0), (0.07, t + 0.03, dh), r=0.006, mat=trim_mat)
            vs = list({v for f in fs for v in f.verts})
            bmesh.ops.rotate(bm, verts=vs, cent=V((0, 0, 0)), matrix=Matrix.Rotation(ang, 3, "Z"))
            bmesh.ops.translate(bm, verts=vs, vec=c)
        c = a + u * dc + V((0, 0, z0 + dh + 0.035))
        fs = box(bm, (0, 0, 0), (dw + 0.14, t + 0.03, 0.07), r=0.006, mat=trim_mat)
        vs = list({v for f in fs for v in f.verts})
        bmesh.ops.rotate(bm, verts=vs, cent=V((0, 0, 0)), matrix=Matrix.Rotation(ang, 3, "Z"))
        bmesh.ops.translate(bm, verts=vs, vec=c)


def hammock(bm, p0, p1, sag=0.22, width=0.62, mat_cloth=0, mat_rope=1, rows=30, cols=12):
    """Asılı hamak: kumaş yatak (zincir eğrisi + enine çukur) + iki uçta halat demeti (kirişe)."""
    p0, p1 = V(p0), V(p1)
    L = (p1 - p0).length
    u = (p1 - p0).normalized()
    side = V((0, 0, 1)).cross(u).normalized()
    inset = 0.35
    c0, c1 = p0 + u * inset + V((0, 0, -0.30)), p1 - u * inset + V((0, 0, -0.30))
    grid = []
    for i in range(rows + 1):
        t = i / rows
        ctr = c0.lerp(c1, t) + V((0, 0, -sag * 4 * t * (1 - t)))
        wt = width * (0.55 + 0.45 * math.sin(math.pi * t) ** 0.5)
        row = []
        for j in range(cols + 1):
            s = j / cols - 0.5
            dip = -0.10 * (1 - (2 * s) ** 2) * math.sin(math.pi * t)
            row.append(bm.verts.new(ctr + side * (s * wt) + V((0, 0, dip))))
        grid.append(row)
    fs = []
    for i in range(rows):
        for j in range(cols):
            fs.append(bm.faces.new([grid[i][j], grid[i][j + 1], grid[i + 1][j + 1], grid[i + 1][j]]))
    for f in fs:
        f.material_index = mat_cloth
        f.smooth = True
    # kalınlık yerine iki yüz: arka yüz kopyası (UE iki yüzlü malzeme de olur)
    for end, row in ((p0, grid[0]), (p1, grid[-1])):
        for v in row[::4]:
            tube(bm, [v.co.lerp(end, t) for t in (0.0, 0.25, 0.5, 0.75, 1.0)], 0.006, mat=mat_rope, seg=6)
    return fs


def rolled_hammock(bm, p0, p1, r=0.11, mat_cloth=0, mat_rope=1):
    p0, p1 = V(p0), V(p1)
    cyl(bm, p0, p1, r, mat=mat_cloth)
    L = (p1 - p0).length
    for t in (0.2, 0.5, 0.8):
        c = p0.lerp(p1, t)
        u = (p1 - p0).normalized()
        prof = [(0.0, -0.012)] + [(r + 0.002 + 0.006 * math.cos(a), 0.012 * math.sin(a)) for a in [-math.pi / 2 + math.pi * i / 8 for i in range(9)]] + [(0.0, 0.012)]
        lathe(bm, prof, c, u, mat=mat_rope)


def bucket(bm, c, r=0.14, h=0.28, mat=0, band=1):
    c = V(c)
    lathe(bm, [(0.0, 0.0), (r * 0.82, 0.0), (r * 0.86, 0.01), (r, h), (r * 0.94, h), (r * 0.80, 0.012), (0.0, 0.012)], c, mat=mat)
    for z in (0.05, h - 0.05):
        rr = r * 0.84 + (r - r * 0.84) * z / h + 0.004
        lathe(bm, [(rr - 0.004, z - 0.012), (rr, z - 0.012), (rr, z + 0.012), (rr - 0.004, z + 0.012)], c, mat=band)


def plug(bm, c, r0=0.05, r1=0.02, h=0.14, mat=0):
    lathe(bm, [(0.0, 0.0), (r0, 0.0), (r0, 0.01), (r1, h), (0.0, h)], V(c), mat=mat)


def curtain(bm, a, b, z0, z1, folds=10, depth=0.05, mat=0, rows=10):
    """Kanvas perde (kıvrımlı, tek katman)."""
    a, b = V((a[0], a[1], 0)), V((b[0], b[1], 0))
    u = (b - a)
    nrm = V((-u.normalized().y, u.normalized().x, 0))
    cols = folds * 20
    grid = []
    for i in range(rows + 1):
        z = z0 + (z1 - z0) * i / rows
        grid.append([bm.verts.new(a + u * (j / cols) + nrm * depth * math.sin(2 * math.pi * folds * j / cols) + V((0, 0, z)))
                     for j in range(cols + 1)])
    for i in range(rows):
        for j in range(cols):
            f = bm.faces.new([grid[i][j], grid[i][j + 1], grid[i + 1][j + 1], grid[i + 1][j]])
            f.material_index = mat
            f.smooth = True


# ------------------------------------------------------------------ nesne + oda kimliği
def box_uv(me, scale=1.0):
    """Kutu izdüşümü UV (dünya metresi; ahşap/kumaş dokuları için tutarlı yoğunluk)."""
    if not me.uv_layers:
        me.uv_layers.new(name="UVMap")
    uv = me.uv_layers.active.data
    for p in me.polygons:
        n = p.normal
        ax = max(range(3), key=lambda i: abs(n[i]))
        for li in p.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            if ax == 2:
                uv[li].uv = (co.x * scale, co.y * scale)
            elif ax == 1:
                uv[li].uv = (co.x * scale, co.z * scale)
            else:
                uv[li].uv = (co.y * scale, co.z * scale)


def finish(name, bm, mats, col, props=None):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    if not me.uv_layers:
        box_uv(me)
    for m in mats:
        me.materials.append(m)
    RS.sharp_from_angle_keep(me, 35)
    old = bpy.data.objects.get(name)
    if old:
        om = old.data
        bpy.data.objects.remove(old, do_unlink=True)
        if om and om.users == 0:
            bpy.data.meshes.remove(om)
    ob = bpy.data.objects.new(name, me)
    col.objects.link(ob)
    ob["module_family"] = "InteriorSet"
    ob["variant"] = "KIZIL_SANCAK_A"
    for k, v in (props or {}).items():
        ob[k] = v
    return ob


def room(name, lo, hi, col, compartment, label, station, wt_zone, deck, extra=None):
    """Oda kimliği boşu (UE: kutu tetik/hacim). lo/hi dünya köşeleri."""
    lo, hi = V(lo), V(hi)
    e = bpy.data.objects.get(name) or bpy.data.objects.new(name, None)
    if e.name not in col.objects:
        col.objects.link(e)
    e.empty_display_type = "CUBE"
    e.location = (lo + hi) / 2
    e.scale = (hi - lo) / 2
    for k, v in {"CompartmentID": compartment, "RoomLabel": label, "OperationalStationID": station,
                 "WatertightZoneID": wt_zone, "Deck": deck, "size_m": [round(x, 2) for x in (hi - lo)]}.items():
        e[k] = v
    for k, v in (extra or {}).items():
        e[k] = v
    return e


def ensure_col(name, parent=None):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    par = parent or bpy.context.scene.collection
    if c.name not in [x.name for x in par.children]:
        try:
            par.children.link(c)
        except RuntimeError:
            pass
    return c


def mat(name, color, rough=0.6, metal=0.0):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    return m


def mat_wood(name="MAT_Wood_Oak_Interior", base=(0.30, 0.17, 0.08), dark=(0.16, 0.085, 0.04), rough=0.62):
    """İç eşya ahşabı: derzsiz, lif yönlü gürültü (nesne koordinatı; UV ölçeğinden bağımsız). UE: BC bake."""
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1.0, 1.0, 14.0)        # lif: bir eksende sık
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 6.0
    nz.inputs["Detail"].default_value = 8.0
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (*dark, 1)
    ramp.color_ramp.elements[1].color = (*base, 1)
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], nz.inputs["Vector"])
    nt.links.new(nz.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = rough
    m["ue_note"] = "UE: prosedürel lif → BC bake"
    return m
