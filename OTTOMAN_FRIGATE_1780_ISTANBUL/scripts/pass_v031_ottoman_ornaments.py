"""v031 — Osmanlı süslemeleri (iç + dış), modüler ve açılıp kapanabilir.

    python3.11 OTTOMAN_FRIGATE_1780_ISTANBUL/scripts/pass_v031_ottoman_ornaments.py [--no-render | --render-only]

Kullanıcı isteği: "gemiyi süsle iç dış Osmanlı motifleriyle … gemi fazla sade duruyor".
Desenler prosedürel çizimdir (scripts/make_ottoman_ornaments.py → Textures/ornaments/); üslup esinlidir, belirli bir tarihî
eserin kopyası değildir [TAHMİN: yerleşim ve renkler; 18. yy Osmanlı kalemişi/çini/rumi üslubu].

Dış:  MOD_ORN_FRIEZE_HULL_{S,P}     kırmızı kuşak boyunca altın rumi sarmaşık frizi (gövde yüzeyine oturur)
      MOD_ORN_STERN_PANELS          kıç tabanı (counter) rumi şemse panoları + kıç korkuluğu frizi
      MOD_ORN_STERN_CREST           kıç ortasında 3B altın hilal-yıldız arma, rumi kanatlı yeşil madalyon
      MOD_ORN_POOP_FRONT            kasara alnı: dört rumi pano + lale frizi (belden görünür)
      MOD_ORN_ROSETTES_CATHEAD      kedi başı uçlarında 3B altın rozet
      MOD_ORN_FINIALS_POOP          kıç korkuluğu köşelerinde altın alem
İç (kaptan kamarası): MOD_ORN_CABIN_WALLS (İznik çini kuşağı + kalemişi + lale frizi), MOD_ORN_CABIN_CEILING (kalemişi),
      MOD_ORN_CABIN_CARPET (Uşak üslubu halı), MOD_ORN_CABIN_CUSHIONS (sedir minderleri + yastıklar)
Anahtar: 00_CONTROLS/CTRL_SUSLEME, özellik `susleme_acik` (1 açık / 0 kapalı), sürücülerle (Auto Run gerekmez).
Kalite: her pass sonunda Tersane kalite testi (reports/kalite_testi_v031.json).
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


P13 = _load("pass_v013", "pass_v013_hull_b_lower_deck.py")
H = P13.H
SRC_VER, VER = "v030", "v031"
ROOT, SHIP = H.ROOT, H.SHIP_ID
TEX = ROOT / "Textures" / "ornaments"
V = Vector
MANIFEST_VERSION = 31
COL = "25_MODULES_ORNAMENT"


# ------------------------------------------------------------------ malzemeler
def _img(name, noncolor=False):
    p = TEX / name
    im = bpy.data.images.get(name) or bpy.data.images.load(str(p))
    if noncolor:
        im.colorspace_settings.name = "Non-Color"
    return im


def orn_mat(name, tex, gilded=True, rough=0.5, bump=0.35, metal_rough=0.28, height=True):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(bsdf.outputs[0], out.inputs[0])
    bc = nt.nodes.new("ShaderNodeTexImage")
    bc.image = _img(f"{tex}_BC.png")
    nt.links.new(bc.outputs["Color"], bsdf.inputs["Base Color"])
    rough_v = nt.nodes.new("ShaderNodeValue")
    rough_v.outputs[0].default_value = rough
    if gilded:                                   # altın maskesi renkten: G > 0,2 ve R − B > 0,42 (doğrusal)
        sep = nt.nodes.new("ShaderNodeSeparateColor")
        nt.links.new(bc.outputs["Color"], sep.inputs[0])
        rb = nt.nodes.new("ShaderNodeMath")
        rb.operation = "SUBTRACT"
        nt.links.new(sep.outputs[0], rb.inputs[0])
        nt.links.new(sep.outputs[2], rb.inputs[1])
        m1 = nt.nodes.new("ShaderNodeMapRange")
        m1.inputs["From Min"].default_value, m1.inputs["From Max"].default_value = 0.36, 0.46
        nt.links.new(rb.outputs[0], m1.inputs["Value"])
        m2 = nt.nodes.new("ShaderNodeMapRange")
        m2.inputs["From Min"].default_value, m2.inputs["From Max"].default_value = 0.16, 0.24
        nt.links.new(sep.outputs[1], m2.inputs["Value"])
        mask = nt.nodes.new("ShaderNodeMath")
        mask.operation = "MULTIPLY"
        nt.links.new(m1.outputs[0], mask.inputs[0])
        nt.links.new(m2.outputs[0], mask.inputs[1])
        nt.links.new(mask.outputs[0], bsdf.inputs["Metallic"])
        mix = nt.nodes.new("ShaderNodeMix")
        mix.data_type = "FLOAT"
        nt.links.new(mask.outputs[0], mix.inputs["Factor"])
        nt.links.new(rough_v.outputs[0], mix.inputs["A"])
        mix.inputs["B"].default_value = metal_rough
        nt.links.new(mix.outputs["Result"], bsdf.inputs["Roughness"])
    else:
        nt.links.new(rough_v.outputs[0], bsdf.inputs["Roughness"])
    if height and (TEX / f"{tex}_H.png").exists():
        hi = nt.nodes.new("ShaderNodeTexImage")
        hi.image = _img(f"{tex}_H.png", noncolor=True)
        bp = nt.nodes.new("ShaderNodeBump")
        bp.inputs["Strength"].default_value = bump
        bp.inputs["Distance"].default_value = 0.004
        nt.links.new(hi.outputs["Color"], bp.inputs["Height"])
        nt.links.new(bp.outputs["Normal"], bsdf.inputs["Normal"])
    m["ue_textures"] = f"Textures/ornaments/{tex}_BC/_H (UE: H → normal bake; metallic maskesi renkten)"
    return m


def mats():
    return {
        "frieze_rumi": orn_mat("MAT_Orn_Frieze_Rumi", "T_Orn_Frieze_Rumi_A", rough=0.5, bump=0.5),
        "frieze_lale": orn_mat("MAT_Orn_Frieze_Lale", "T_Orn_Frieze_Lale_A", rough=0.5, bump=0.4),
        "panel": orn_mat("MAT_Orn_Panel_Rumi", "T_Orn_Panel_Rumi_A", rough=0.5, bump=0.6),
        "kalemisi": orn_mat("MAT_Orn_Kalemisi", "T_Orn_Kalemisi_A", gilded=True, rough=0.62, bump=0.15),
        "iznik": orn_mat("MAT_Orn_Iznik", "T_Orn_Iznik_Tile_A", gilded=False, rough=0.12, bump=0.12),
        "carpet": orn_mat("MAT_Orn_Carpet_Usak", "T_Orn_Carpet_Usak_A", gilded=False, rough=0.95, height=False),
        "gilt": bpy.data.materials["MAT_Trim_Gilt"],
        "green": _plain("MAT_Orn_Enamel_Green", (0.012, 0.075, 0.05), 0.35),
        "red": _plain("MAT_Orn_Enamel_Red", (0.19, 0.01, 0.015), 0.4),
        "velvet": _plain("MAT_Orn_Velvet_Crimson", (0.16, 0.012, 0.02), 0.8),
    }


def _plain(name, col, rough):
    m = bpy.data.materials.get(name)
    if m:
        return m
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*col, 1)
    b.inputs["Roughness"].default_value = rough
    return m


# ------------------------------------------------------------------ yardımcılar
def bvh_of(names, booleans=True):
    dg = bpy.context.evaluated_depsgraph_get()
    saved = []
    if not booleans:
        for n in names:
            for m in bpy.data.objects[n].modifiers:
                if m.type == "BOOLEAN":
                    saved.append((m, m.show_viewport))
                    m.show_viewport = False
        dg.update()
    vs, ps, polymat, off = [], [], [], 0
    for n in names:
        o = bpy.data.objects[n]
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        vs += [o.matrix_world @ v.co for v in me.vertices]
        for p in me.polygons:
            ps.append(tuple(i + off for i in p.vertices))
            mat = ev.material_slots[p.material_index].material if p.material_index < len(ev.material_slots) else None
            polymat.append((n, mat.name if mat else ""))
        off += len(me.vertices)
        ev.to_mesh_clear()
    for m, s in saved:
        m.show_viewport = s
    return BVHTree.FromPolygons(vs, ps), polymat


def new_object(name, me, col, **props):
    old = bpy.data.objects.get(name)
    if old:
        ome = old.data
        bpy.data.objects.remove(old, do_unlink=True)
        if ome and ome.users == 0:
            bpy.data.meshes.remove(ome)
    ob = bpy.data.objects.new(name, me)
    col.objects.link(ob)
    ob["module_family"] = "OrnamentSet"
    ob["variant"] = "OTTOMAN_A"
    ob["manifest_version"] = MANIFEST_VERSION
    ob["default_enabled"] = True
    for k, v in props.items():
        ob[k] = v
    return ob


class Patch:
    """Yüzeye ışınla oturan ızgara (dekal/kaplama). ray(u, v) → (başlangıç, yön); uv(u, v) → doku koordinatı."""

    def __init__(self, name, mat):
        self.name = name
        self.bm = bmesh.new()
        self.uv = self.bm.loops.layers.uv.new("UVMap")
        self.mats = [mat]

    def add(self, tree, us, vs_, ray, uv, offset=0.005, max_jump=3.0, mat_index=0, accept=None):
        grid = {}
        du = abs(us[1] - us[0]) if len(us) > 1 else 0.1
        dv = abs(vs_[1] - vs_[0]) if len(vs_) > 1 else 0.1
        for i, u in enumerate(us):
            for j, v in enumerate(vs_):
                o, d = ray(u, v)
                if o is None:
                    continue
                loc, n, idx, dist = tree.ray_cast(o, d, 20.0)
                if loc is None or (accept and not accept(idx, loc)):
                    continue
                if n.dot(d) > 0:
                    n = -n
                grid[(i, j)] = (loc + n * offset, uv(u, v))
        verts = {k: self.bm.verts.new(p) for k, (p, _) in grid.items()}
        nq = 0
        lim = max_jump * max(du, dv) * 1.5
        for i in range(len(us) - 1):
            for j in range(len(vs_) - 1):
                ks = [(i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)]
                if not all(k in verts for k in ks):
                    continue
                ps = [grid[k][0] for k in ks]
                if max((ps[a] - ps[(a + 1) % 4]).length for a in range(4)) > lim:
                    continue
                f = self.bm.faces.new([verts[k] for k in ks])
                f.smooth = True
                f.material_index = mat_index
                for lp, k in zip(f.loops, ks):
                    lp[self.uv].uv = grid[k][1]
                nq += 1
        for k, vv in list(verts.items()):
            if not vv.link_faces:
                self.bm.verts.remove(vv)
        return nq

    def finish(self, col, **props):
        bmesh.ops.recalc_face_normals(self.bm, faces=self.bm.faces)
        me = bpy.data.meshes.new(self.name)
        self.bm.to_mesh(me)
        self.bm.free()
        for m in self.mats:
            me.materials.append(m)
        return new_object(self.name, me, col, **props)


def extrude_shape(bm, pts2d, frame, depth, z0=0.0, mat=0, bevel_rows=True):
    """2B kapalı çokgeni (u, v) çerçevede (origin, U, Vv, N) N yönünde depth kadar kabartır (ön yüz + yan duvar)."""
    o, U, Vv, N = frame
    base = [bm.verts.new(o + U * u + Vv * v + N * z0) for u, v in pts2d]
    top = [bm.verts.new(o + U * u + Vv * v + N * (z0 + depth)) for u, v in pts2d]
    fs = []
    n = len(pts2d)
    for k in range(n):
        fs.append(bm.faces.new([base[k], base[(k + 1) % n], top[(k + 1) % n], top[k]]))
    try:
        fs.append(bm.faces.new(top))
    except ValueError:
        pass
    for f in fs:
        f.material_index = mat
        f.smooth = True                               # keskinlik: sharp_from_angle (üst kenar 90°)
    return fs


def circle2d(cx, cy, r, n):
    return [(cx + r * math.cos(2 * math.pi * k / n), cy + r * math.sin(2 * math.pi * k / n)) for k in range(n)]


def crescent2d(R, r, off, n=96):
    """Hilal: merkezdeki R çemberinden (off, 0) merkezli r çemberi çıkarılır (sağa açık). Kesişim noktalarından iki yay."""
    x = (R * R - r * r + off * off) / (2 * off)
    y = math.sqrt(max(R * R - x * x, 1e-9))
    th = math.atan2(y, x)
    pts = [(R * math.cos(th + (2 * math.pi - 2 * th) * k / n), R * math.sin(th + (2 * math.pi - 2 * th) * k / n)) for k in range(n + 1)]
    ph = math.atan2(y, x - off)
    for k in range(1, n):
        a = (2 * math.pi - ph) - (2 * math.pi - 2 * ph) * k / n
        pts.append((off + r * math.cos(a), r * math.sin(a)))
    return pts


def star2d(cx, cy, r_out, r_in, points=8):
    out = []
    for k in range(points * 2):
        r = r_out if k % 2 == 0 else r_in
        a = math.pi / 2 + math.pi * k / points
        out.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return out


def ogee2d(w, h, n=48):
    r = []
    for k in range(n + 1):
        t = k / n
        a = -math.pi / 2 + math.pi * t
        # sivri kemerli madalyon: yan eğriler, üst/alt uçlar sivri
        x = w / 2 * math.cos(a) ** 1.5 if math.cos(a) > 0 else 0.0
        y = h / 2 * math.sin(a)
        r.append((x, y))
    return r + [(-x, y) for x, y in reversed(r[1:-1])]


def rumi_wing2d(s, n=96):
    """Rumi kanat (çatal uçlu kıvrık yaprak) — arma yanları için."""
    pts = []
    for k in range(n + 1):
        t = k / n
        pts.append((s * t, s * (0.28 * math.sin(math.pi * t) + 0.10 * math.sin(2 * math.pi * t))))
    for k in range(n, -1, -1):
        t = k / n
        pts.append((s * t * 0.96, s * (-0.06 * math.sin(math.pi * t) + 0.04 * math.sin(3 * math.pi * t))))
    return pts


# ------------------------------------------------------------------ 0. kuşak tahtası / lumbar çakışması (kullanıcı bildirimi)
def _islands_world(o):
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bm.verts.index_update()
    bm.faces.index_update()
    out = []
    for fs in RS.islands(bm):
        vs = list({v for f in fs for v in f.verts})
        out.append((fs[0].material_index, [v.index for v in vs]))
    bm.free()
    return out


def port_boxes():
    fr = bpy.data.objects["CORE_GUNPORT_FRAMES"]
    out = []
    for mat, idx in _islands_world(fr):
        ps = [fr.matrix_world @ fr.data.vertices[i].co for i in idx]
        out.append((min(p.x for p in ps), max(p.x for p in ps), max(p.z for p in ps), 1 if sum(p.y for p in ps) > 0 else -1))
    return out


def band_top_fn(sgn):
    """x → altın silmenin (CORE_MOULDING_BAND_LOW) dış yüz üst kotu."""
    tree, _ = bvh_of(["CORE_MOULDING_BAND_LOW"])
    cache = {}

    def f(x):
        k = round(x, 2)
        if k in cache:
            return cache[k]
        top = None
        for j in range(300):
            z = 4.1 + j * 0.005
            loc, *_ = tree.ray_cast(V((x, sgn * 9.0, z)), V((0, -sgn, 0)), 12.0)
            if loc is not None:
                top = z
        cache[k] = top
        return top
    return f


def fix_channels():
    """Ön direk kuşak tahtası lumbar açıklıklarını kesiyordu (baş lumbar çerçevesi tahtanın üstüne taşıyordu) → tahta
    altın silmenin üstüne, sheer'i izleyerek taşınır; bigot, savlo, çarmıh alt ucu, zincir levhası tepesi, UCX ve tırmanma
    soketi birlikte. Tüm direklerde: lumbar önünden geçen zincir levhaları lumbarın 3 cm üstünde biter."""
    ports = port_boxes()
    rep = {}
    for mast in ("FORE", "MAIN", "MIZZEN"):
        o = bpy.data.objects[f"MOD_RIG_STANDING_{mast}_A"]
        me, mw, mi = o.data, o.matrix_world, o.matrix_world.inverted()
        W_ = lambda i: mw @ me.vertices[i].co  # noqa: E731
        isl = _islands_world(o)
        chans = [(m, idx) for m, idx in isl if m == 3]
        info = {"raised": False, "plates_shortened": 0}
        for sgn in (1, -1):
            ch = [(m, idx) for m, idx in chans if (sum(W_(i).y for i in idx) > 0) == (sgn > 0)]
            if not ch:
                continue
            cps = [W_(i) for i in ch[0][1]]
            cx0, cx1 = min(p.x for p in cps), max(p.x for p in cps)
            cz0, cz1 = min(p.z for p in cps), max(p.z for p in cps)
            clash = [p for p in ports if p[3] == sgn and p[1] > cx0 and p[0] < cx1 and p[2] > cz0 - 0.005]
            dzf = lambda x: 0.0  # noqa: E731
            if clash:
                bt = band_top_fn(sgn)

                def dzf(x, bt=bt, cz0=cz0):
                    t = bt(min(max(x, cx0 + 0.05), cx1 - 0.05))
                    return max(0.0, (t + 0.006) - cz0) if t is not None else 0.0
                info["raised"] = True
                info[f"dz_{'S' if sgn > 0 else 'P'}"] = [round(dzf(cx0 + 0.1), 3), round(dzf(cx1 - 0.1), 3)]
            tops = [sk.location.z for sk in bpy.data.objects if sk.type == "EMPTY" and sk.name == f"SOCK_CLIMB_{mast}_{'S' if sgn > 0 else 'P'}_LOWER_TOP"]
            z_top = tops[0] if tops else cz1 + 12.0
            for m, idx in isl:
                ps = [W_(i) for i in idx]
                if (sum(p.y for p in ps) > 0) != (sgn > 0):
                    continue
                xs = [p.x for p in ps]
                if max(xs) < cx0 - 0.4 or min(xs) > cx1 + 0.4:
                    continue
                zmin, zmax = min(p.z for p in ps), max(p.z for p in ps)
                xc = sum(xs) / len(xs)
                if m == 3:                                        # tahta: köşe başına eğim
                    for i in idx:
                        p = W_(i)
                        me.vertices[i].co = mi @ (p + V((0, 0, dzf(p.x))))
                elif m == 2 and zmax - zmin > 0.4 and zmax < cz1 + 0.2:   # zincir levhası
                    d = dzf(xc)
                    hit = [pb for pb in ports if pb[3] == sgn and pb[0] - 0.06 < xc < pb[1] + 0.06]
                    new_bot = (max(pb[2] for pb in hit) + 0.03) if hit else None
                    for i in idx:
                        p = W_(i)
                        if p.z > zmax - 0.15:
                            p = p + V((0, 0, d))
                        elif new_bot is not None and p.z < new_bot:
                            p = V((p.x, p.y, new_bot + (p.z - zmin) * 0.02))
                        me.vertices[i].co = mi @ p
                    if new_bot is not None:
                        info["plates_shortened"] += 1
                elif zmin > cz0 - 0.05 and zmax < cz1 + 1.3:          # bigotlar + savlolar: tam kayma
                    d = dzf(xc)
                    for i in idx:
                        me.vertices[i].co = mi @ (W_(i) + V((0, 0, d)))
                elif m == 0 and zmin < cz1 + 1.3 and zmax - zmin > 2.0:  # çarmıh/patrisa: dipte tam, tepede 0 (doğru kalır)
                    for i in idx:
                        p = W_(i)
                        t = (p.z - zmin) / (zmax - zmin)
                        me.vertices[i].co = mi @ (p + V((0, 0, dzf(p.x) * (1.0 - t))))
                elif m == 0 and zmin > cz1 + 0.5 and zmax < z_top and zmax - zmin < 2.0:   # iskalarya: çarmıh üstünde kalır
                    for i in idx:
                        p = W_(i)
                        t = min(max((p.z - (cz1 + 0.95)) / (z_top - (cz1 + 0.95)), 0.0), 1.0)
                        me.vertices[i].co = mi @ (p + V((0, 0, dzf(p.x) * (1.0 - t))))
            if info["raised"]:
                for u in bpy.data.objects:
                    if u.name.startswith(f"UCX_MOD_RIG_STANDING_{mast}_A_"):
                        um = u.matrix_world
                        for v in u.data.vertices:
                            p = um @ v.co
                            if (p.y > 0) == (sgn > 0) and cx0 - 0.4 < p.x < cx1 + 0.4 and p.z < cz1 + 1.3:
                                v.co = um.inverted() @ (p + V((0, 0, dzf(p.x))))
                for sk in bpy.data.objects:
                    if sk.type == "EMPTY" and sk.name.startswith(f"SOCK_CLIMB_{mast}_") and (sk.location.y > 0) == (sgn > 0) \
                            and sk.location.z < cz1 + 1.3:
                        sk.location.z += dzf(sk.location.x)
        me.update()
        rep[mast] = info
    return rep


# ------------------------------------------------------------------ dış
def band_columns(tree, polymat, sgn, xs, zlo=3.2, zhi=8.4, step=0.01, matname="MAT_Hull_RedBand"):
    cols = {}
    for x in xs:
        run = []
        z = zlo
        while z <= zhi:
            loc, n, idx, d = tree.ray_cast(V((x, sgn * 9.0, z)), V((0, -sgn, 0)), 12.0)
            if loc is not None and polymat[idx] == ("CORE_HULL_SHELL", matname) and n.y * sgn > 0.3:
                run.append(z)
            elif run:
                break
            z += step
        if len(run) >= 8:
            cols[x] = (run[0] + 0.012, run[-1] - 0.012)
    return cols


def hull_frieze(M, col):
    tree, polymat = bvh_of(["CORE_HULL_SHELL"])
    sc = bpy.context.scene
    dg = bpy.context.evaluated_depsgraph_get()
    obs, rep = [], {}
    for sgn, tag in ((1, "S"), (-1, "P")):
        xs = [round(-19.6 + 0.05 * k, 3) for k in range(int((21.2 + 19.6) / 0.05))]
        cols = band_columns(tree, polymat, sgn, xs)
        hs = sorted(t - b for b, t in cols.values())
        hmed = hs[len(hs) // 2] if hs else 0.3
        tile = hmed * 8.0
        # önünde başka nesne (lumbar çerçevesi, kuşak tahtası) olan sütunlar atlanır
        keep = {}
        for x, (zb, zt) in cols.items():
            zm = (zb + zt) / 2
            ok, loc, n, fi, ob, _ = sc.ray_cast(dg, V((x, sgn * 9.0, zm)), V((0, -sgn, 0)), distance=12.0)
            if ok and ob.name == "CORE_HULL_SHELL":
                keep[x] = (zb, zt)
        pt = Patch(f"MOD_ORN_FRIEZE_HULL_{tag}", M["frieze_rumi"])
        xs_k = sorted(keep)
        # ardışık sütun grupları (boşluklar lumbar/kuşak tahtası)
        runs, cur = [], []
        for x in xs_k:
            if cur and x - cur[-1] > 0.051:
                runs.append(cur)
                cur = []
            cur.append(x)
        if cur:
            runs.append(cur)
        nq = 0
        for run in runs:
            if len(run) < 3:
                continue
            vs_ = [k / 10 for k in range(11)]

            def ray(u, v, run=run):
                zb, zt = keep[u]
                return V((u, sgn * 9.0, zb + (zt - zb) * v)), V((0, -sgn, 0))
            nq += pt.add(tree, run, vs_, ray, lambda u, v: ((u + 19.6) / tile * sgn, v), offset=0.004,
                         accept=lambda idx, loc: polymat[idx][0] == "CORE_HULL_SHELL")
        ob = pt.finish(col, socket="SOCKET_ORN_HULL_FRIEZE", ue_note="gövde kırmızı kuşağı boyunca dekal-kabartma şerit")
        obs.append(ob)
        rep[tag] = {"columns": len(cols), "visible": len(keep), "quads": nq, "tile_m": round(tile, 2)}
    return obs, rep


def stern_panels(M, col):
    tree, polymat = bvh_of(["CORE_HULL_SHELL", "MOD_STERN_GALLERY_A"])
    pt = Patch("MOD_ORN_STERN_PANELS", M["panel"])
    pt.mats.append(M["frieze_rumi"])
    n = 0
    for yc in (-2.05, 0.0, 2.05):                      # kıç tabanı (counter) üç şemse panosu
        w, z0, z1 = 1.75, 3.05, 4.50
        us = [yc - w / 2 + w * k / 56 for k in range(57)]
        vs_ = [z0 + (z1 - z0) * k / 48 for k in range(49)]
        n += pt.add(tree, us, vs_, lambda u, v: (V((-26.0, u, v)), V((1, 0, 0))),
                    lambda u, v, yc=yc: ((u - (yc - w / 2)) / w, (v - z0) / (z1 - z0)), offset=0.006,
                    accept=lambda idx, loc: polymat[idx][0] == "CORE_HULL_SHELL")
    us = [-3.3 + 6.6 * k / 160 for k in range(161)]       # kıç korkuluğu frizi
    vs_ = [6.70 + 0.46 * k / 8 for k in range(9)]
    n += pt.add(tree, us, vs_, lambda u, v: (V((-26.0, u, v)), V((1, 0, 0))),
                lambda u, v: ((u + 3.3) / (0.46 * 8), (v - 6.70) / 0.46), offset=0.006, mat_index=1)
    return pt.finish(col, socket="SOCKET_ORN_STERN"), n


def stern_crest(M, col):
    """Kıç ortası arma: yeşil sivri madalyon + altın çerçeve + altın hilal-yıldız + iki rumi kanat (3B kabartma)."""
    sc = bpy.context.scene
    dg = bpy.context.evaluated_depsgraph_get()
    zc, yc = 7.42, 0.0
    ok, loc, n, fi, ob, _ = sc.ray_cast(dg, V((-26.0, 0.6, zc)), V((1, 0, 0)), distance=10.0)
    x_face = (loc.x if ok else -21.05) - 0.02
    # kıç feneri direği (y=0) önünde kalmak için
    ok2, loc2, *_ = sc.ray_cast(dg, V((-26.0, 0.0, zc)), V((1, 0, 0)), distance=10.0)
    if ok2:
        x_face = min(x_face, loc2.x - 0.02)
    o = V((x_face, yc, zc))
    U, Vv, N = V((0, 1, 0)), V((0, 0, 1)), V((-1, 0, 0))
    bm = bmesh.new()
    extrude_shape(bm, ogee2d(0.78, 0.92, 160), (o, U, Vv, N), 0.05, 0.0, mat=1)         # yeşil madalyon
    ring_o = ogee2d(0.86, 1.00, 160)
    # altın çerçeve: dış ve iç sivri kemer arası (şerit) — iki kabartma
    extrude_shape(bm, ring_o, (o, U, Vv, N), 0.035, 0.0, mat=0)
    extrude_shape(bm, crescent2d(0.24, 0.20, 0.07, 96), (o + U * -0.02, U, Vv, N), 0.035, 0.05, mat=0)
    extrude_shape(bm, star2d(0.20, 0.0, 0.085, 0.036, 8), (o, U, Vv, N), 0.035, 0.05, mat=0)
    for s in (1, -1):                                   # rumi kanatlar
        w = rumi_wing2d(0.62)
        pts = [(s * (0.40 + x), 0.05 + y) for x, y in w]
        if s < 0:
            pts.reverse()
        extrude_shape(bm, pts, (o, U, Vv, N), 0.03, 0.0, mat=0)
        w2 = rumi_wing2d(0.42)
        pts2 = [(s * (0.40 + x), -0.12 - 0.6 * y) for x, y in w2]
        if s < 0:
            pts2.reverse()
        extrude_shape(bm, pts2, (o, U, Vv, N), 0.028, 0.0, mat=0)
    # tepe alemi (lale tomurcuğu) — lathe
    RS_lathe(bm, [(0.0, 0.0), (0.03, 0.02), (0.05, 0.08), (0.045, 0.14), (0.02, 0.20), (0.0, 0.24)],
             o + Vv * 0.50 + N * 0.03, Vv, mat=0)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new("MOD_ORN_STERN_CREST")
    bm.to_mesh(me)
    bm.free()
    for m in (M["gilt"], M["green"]):
        me.materials.append(m)
    RS.sharp_from_angle_keep(me, 35)
    geo_uv(me)
    return new_object("MOD_ORN_STERN_CREST", me, col, socket="SOCKET_ORN_STERN_CREST",
                      note="hilal-yıldız: 1793 donanma sancağı ile uyumlu [İKİNCİL]; madalyon ve kanatlar üslup esinli [TAHMİN]")


def RS_lathe(bm, prof, base, axis, mat=0):
    """Kiriş sapması kuralına göre dilimli lathe (axis yönünde)."""
    rmax = max(r for r, _ in prof)
    seg = RS.required_segments(rmax, 0.0015, 12, 64)
    q = V((0, 0, 1)).rotation_difference(axis.normalized()).to_matrix().to_4x4()
    T = Matrix.Translation(base) @ q
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
            for k in range(seg):
                fs.append(bm.faces.new([a[0], b[(k + 1) % seg], b[k]]))
        elif len(b) == 1 and len(a) > 1:
            for k in range(seg):
                fs.append(bm.faces.new([a[k], a[(k + 1) % seg], b[0]]))
        elif len(a) > 1 and len(b) > 1:
            for k in range(seg):
                fs.append(bm.faces.new([a[k], a[(k + 1) % seg], b[(k + 1) % seg], b[k]]))
    for f in fs:
        f.material_index = mat
        f.smooth = True
    return fs


def geo_uv(me):
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


def poop_front(M, col):
    tree, polymat = bvh_of(["CORE_POOP_BULKHEAD"])
    pt = Patch("MOD_ORN_POOP_FRONT", M["panel"])
    pt.mats.append(M["frieze_lale"])
    n = 0
    for y0, y1 in ((0.72, 1.92), (2.08, 3.20), (-1.92, -0.72), (-3.20, -2.08)):
        z0, z1 = 4.55, 5.78
        us = [y0 + (y1 - y0) * k / 16 for k in range(17)]
        vs_ = [z0 + (z1 - z0) * k / 16 for k in range(17)]
        n += pt.add(tree, us, vs_, lambda u, v: (V((-13.5, u, v)), V((-1, 0, 0))),
                    lambda u, v, y0=y0, y1=y1: ((u - y0) / (y1 - y0), (v - z0) / (z1 - z0)), offset=0.006)
    us = [-3.35 + 6.7 * k / 90 for k in range(91)]
    vs_ = [5.97 + 0.30 * k / 4 for k in range(5)]
    n += pt.add(tree, us, vs_, lambda u, v: (V((-13.5, u, v)), V((-1, 0, 0))),
                lambda u, v: ((u + 3.35) / 2.4, (v - 5.97) / 0.30), offset=0.006, mat_index=1)
    return pt.finish(col, socket="SOCKET_ORN_POOP_FRONT"), n


def rosette_mesh(bm, c, n_axis, r, mat=0, petals=8):
    """3B rozet: kabartma yapraklar + kubbe göbek (kiriş sapması kuralıyla)."""
    N = n_axis.normalized()
    U = N.cross(V((0, 0, 1)))
    if U.length < 1e-3:
        U = N.cross(V((1, 0, 0)))
    U.normalize()
    W = N.cross(U)
    for k in range(petals):
        a = 2 * math.pi * k / petals
        pts = []
        for j in range(25):
            t = j / 24
            ang = a + (t - 0.5) * (2 * math.pi / petals) * 0.9
            rr = r * (0.35 + 0.65 * math.sin(math.pi * t) ** 0.6)
            pts.append((rr * math.cos(ang), rr * math.sin(ang)))
        pts = [(0.0, 0.0)] + pts
        extrude_shape(bm, pts, (c, U, W, N), r * 0.18, 0.0, mat=mat)
    RS_lathe(bm, [(r * 0.30, 0.0), (r * 0.30, r * 0.12), (r * 0.22, r * 0.24), (r * 0.10, r * 0.31), (0.0, r * 0.33)],
             c + N * (r * 0.16), N, mat=mat)


def cathead_rosettes(M, col):
    sc = bpy.context.scene
    dg = bpy.context.evaluated_depsgraph_get()
    ch = bpy.data.objects["CORE_CATHEADS"]
    bb = [ch.matrix_world @ V(c) for c in ch.bound_box]
    xc = (min(p.x for p in bb) + max(p.x for p in bb)) / 2
    zc = (min(p.z for p in bb) + max(p.z for p in bb)) / 2
    bm = bmesh.new()
    n = 0
    for sgn in (1, -1):
        ok, loc, nrm, fi, ob, _ = sc.ray_cast(dg, V((xc, sgn * 8.0, zc)), V((0, -sgn, 0)), distance=6.0)
        if ok and ob.name == "CORE_CATHEADS":
            rosette_mesh(bm, loc + V((0, sgn * 0.002, 0)), V((0, sgn, 0)), 0.14)
            n += 1
    me = bpy.data.meshes.new("MOD_ORN_ROSETTES_CATHEAD")
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(M["gilt"])
    RS.sharp_from_angle_keep(me, 35)
    geo_uv(me)
    return new_object("MOD_ORN_ROSETTES_CATHEAD", me, col, socket="SOCKET_ORN_CATHEAD"), n


def poop_finials(M, col):
    sc = bpy.context.scene
    dg = bpy.context.evaluated_depsgraph_get()
    bal = bpy.data.objects["CORE_POOP_BALUSTRADE"]
    bb = [bal.matrix_world @ V(c) for c in bal.bound_box]
    x0, x1 = min(p.x for p in bb), max(p.x for p in bb)
    y1 = max(p.y for p in bb)
    bm = bmesh.new()
    placed = []
    for x in (x0 + 0.06, x1 - 0.06):
        for y in (y1 - 0.06, -(y1 - 0.06)):
            best = None
            for dx in [k * 0.03 for k in range(-6, 7)]:
                for dy in [k * 0.03 for k in range(-5, 6)]:
                    ok, loc, nrm, fi, ob, _ = sc.ray_cast(dg, V((x + dx, y + dy, 10.0)), V((0, 0, -1)), distance=4.0)
                    if ok and ob.name == "CORE_POOP_BALUSTRADE" and nrm.z > 0.9 and (best is None or loc.z > best.z):
                        best = loc
            if best is None:
                continue
            RS_lathe(bm, [(0.0, 0.0), (0.045, 0.0), (0.045, 0.02), (0.025, 0.04), (0.055, 0.10), (0.06, 0.14), (0.045, 0.19),
                          (0.02, 0.24), (0.012, 0.27), (0.02, 0.29), (0.0, 0.33)], best - V((0, 0, 0.004)), V((0, 0, 1)), mat=0)
            placed.append([round(c, 2) for c in best])
    me = bpy.data.meshes.new("MOD_ORN_FINIALS_POOP")
    bm.to_mesh(me)
    bm.free()
    me.materials.append(M["gilt"])
    RS.sharp_from_angle_keep(me, 35)
    geo_uv(me)
    return new_object("MOD_ORN_FINIALS_POOP", me, col, socket="SOCKET_ORN_FINIALS"), placed


# ------------------------------------------------------------------ iç (kamara)
CAB_X0, CAB_X1 = -19.25, -15.45


def floor_ceiling(x, y=1.2):
    t, _ = FC_TREES["deck"]
    lf, *_ = t.ray_cast(V((x, y, 5.4)), V((0, 0, -1)), 3.0)
    t, _ = FC_TREES["ceil"]
    lc, *_ = t.ray_cast(V((x, y, 5.4)), V((0, 0, 1)), 3.0)
    return (lf.z if lf is not None else None), (lc.z if lc is not None else None)


FC_TREES = {}


def cabin(M, col):
    FC_TREES["deck"] = bvh_of(["CORE_DECK_GUN"])
    FC_TREES["ceil"] = bvh_of(["CORE_DECK_POOP"])
    hull, _ = bvh_of(["CORE_HULL_SHELL"])
    bulk, _ = bvh_of(["CORE_POOP_BULKHEAD"])
    rep = {}
    walls = Patch("MOD_ORN_CABIN_WALLS", M["iznik"])
    walls.mats += [M["kalemisi"], M["frieze_lale"]]

    def bands(zf, zc):
        return [(zf + 0.55, zf + 1.00, 0), (zf + 1.00, zc - 0.30, 1), (zc - 0.28, zc - 0.05, 2)]
    xs = [CAB_X0 + (CAB_X1 - CAB_X0) * k / 76 for k in range(77)]
    fc = {x: floor_ceiling(x) for x in xs}
    n = 0
    for sgn in (1, -1):
        for bi in range(3):
            def ray(u, v, bi=bi, sgn=sgn):
                zf, zc = fc[u]
                if zf is None or zc is None:
                    return None, None
                z0, z1, _ = bands(zf, zc)[bi]
                return V((u, 0.0, z0 + (z1 - z0) * v)), V((0, sgn, 0))
            vs_ = [k / 8 for k in range(9)]
            tiles = (0.6, 1.2, 0.26 * 8)[bi]

            def uv(u, v, bi=bi, tiles=tiles):
                zf, zc = fc[u]
                z0, z1, _ = bands(zf, zc)[bi]
                hgt = z1 - z0
                return ((u - CAB_X0) / tiles, v * (hgt / tiles if bi < 2 else 1.0))
            n += walls.add(hull, xs, vs_, ray, uv, offset=0.006, mat_index=bi)
    # ön perde (kasara bölmesi) kıç yüzü
    ys = [-3.3 + 6.6 * k / 66 for k in range(67)]
    zf_b, zc_b = floor_ceiling(-15.6, 1.8)
    for bi in range(3):
        z0, z1, _ = bands(zf_b, zc_b)[bi]
        tiles = (0.6, 1.2, 0.26 * 8)[bi]
        vs_ = [z0 + (z1 - z0) * k / 8 for k in range(9)]
        n += walls.add(bulk, ys, vs_, lambda u, v: (V((-17.0, u, v)), V((1, 0, 0))),
                       lambda u, v, z0=z0, z1=z1, tiles=tiles, bi=bi: ((u + 3.3) / tiles, (v - z0) / (tiles if bi < 2 else (z1 - z0))),
                       offset=0.006, mat_index=bi)
    rep["walls_quads"] = n
    wo = walls.finish(col, room="great_cabin")
    # tavan
    ceil = Patch("MOD_ORN_CABIN_CEILING", M["kalemisi"])
    ct, _ = FC_TREES["ceil"]
    xs2 = [-20.15 + (CAB_X1 - -20.15) * k / 47 for k in range(48)]
    ys2 = [-3.1 + 6.2 * k / 62 for k in range(63)]
    rep["ceiling_quads"] = ceil.add(ct, xs2, ys2, lambda u, v: (V((u, v, 5.4)), V((0, 0, 1))),
                                    lambda u, v: (u / 1.2, v / 1.2), offset=0.006)
    co = ceil.finish(col, room="great_cabin")
    # halı
    carpet = Patch("MOD_ORN_CABIN_CARPET", M["carpet"])
    dt, _ = FC_TREES["deck"]
    cx0, cx1, cy0, cy1 = -19.0, -15.9, -1.25, 1.25
    rep["carpet_quads"] = carpet.add(dt, [cx0 + (cx1 - cx0) * k / 40 for k in range(41)], [cy0 + (cy1 - cy0) * k / 32 for k in range(33)],
                                     lambda u, v: (V((u, v, 5.2)), V((0, 0, -1))),
                                     lambda u, v: ((u - cx0) / (cx1 - cx0), (v - cy0) / (cy1 - cy0)), offset=0.004)
    cpo = carpet.finish(col, room="great_cabin")
    sol = cpo.modifiers.new("Solidify", "SOLIDIFY")
    sol.thickness = 0.008
    sol.offset = 1.0
    bv = cpo.modifiers.new("Bevel", "BEVEL")
    bv.width, bv.segments, bv.limit_method, bv.harden_normals = 0.003, 3, "ANGLE", True
    # sedir minderleri + yastıklar
    sc = bpy.context.scene
    dg = bpy.context.evaluated_depsgraph_get()
    bench = bpy.data.objects["MOD_CABIN_STERN_BENCH_A"]
    bb = [bench.matrix_world @ V(c) for c in bench.bound_box]
    bx0, bx1 = min(p.x for p in bb), max(p.x for p in bb)
    by0, by1 = min(p.y for p in bb), max(p.y for p in bb)
    ok, loc, *_ = sc.ray_cast(dg, V(((bx0 + bx1) / 2 + 0.05, 0.0, 6.0)), V((0, 0, -1)), distance=3.0)
    zseat = loc.z if ok else max(p.z for p in bb)
    bm = bmesh.new()
    wseg = (by1 - by0 - 0.04) / 3
    for k in range(3):
        y0 = by0 + 0.02 + k * wseg
        cushion(bm, V(((bx0 + bx1) / 2 + 0.03, y0 + wseg / 2, zseat + 0.045)), (bx1 - bx0 - 0.02) / 2 + 0.02, wseg / 2 - 0.01, 0.045, 0)
    for k, yy in enumerate((by0 + 0.30, 0.0, by1 - 0.30)):
        pillow(bm, V((bx0 + 0.10, yy, zseat + 0.20)), 0.16, 0.10, 0.20, 1 if k != 1 else 2)
    for yy in (by0 + 0.08, by1 - 0.08):
        RS_lathe(bm, [(0.0, 0.0), (0.075, 0.004), (0.095, 0.03), (0.10, 0.21), (0.095, 0.39), (0.075, 0.416), (0.0, 0.42)],
                 V(((bx0 + bx1) / 2 + 0.05 - 0.21, yy, zseat + 0.10)), V((1, 0, 0)), mat=1)
    me = bpy.data.meshes.new("MOD_ORN_CABIN_CUSHIONS")
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    for m in (M["velvet"], M["frieze_lale"], M["iznik"]):
        me.materials.append(m)
    RS.sharp_from_angle_keep(me, 50)
    geo_uv(me)
    cu = new_object("MOD_ORN_CABIN_CUSHIONS", me, col, room="great_cabin")
    return [wo, co, cpo, cu], rep


def cushion(bm, c, hx, hy, hz, mat, n=10):
    """Yuvarlak kenarlı minder: süper-elipsoit (kiriş sapması küçük, yumuşak)."""
    r = bmesh.ops.create_uvsphere(bm, u_segments=72, v_segments=36, radius=1.0)
    for v in r["verts"]:
        x, y, z = v.co
        e = 0.3                                         # kutuya yakın elipsoit (üs)
        sx = math.copysign(abs(x) ** e, x)
        sy = math.copysign(abs(y) ** e, y)
        sz = math.copysign(abs(z) ** 0.6, z)
        v.co = c + V((sx * hx, sy * hy, sz * hz))
    for f in {f for v in r["verts"] for f in v.link_faces}:
        f.material_index = mat
        f.smooth = True


def pillow(bm, c, hx, hy, hz, mat):
    r = bmesh.ops.create_uvsphere(bm, u_segments=64, v_segments=32, radius=1.0)
    for v in r["verts"]:
        x, y, z = v.co
        v.co = c + V((math.copysign(abs(x) ** 0.8, x) * hx * 0.5, math.copysign(abs(y) ** 0.45, y) * hy * 1.4,
                      math.copysign(abs(z) ** 0.45, z) * hz))
    for f in {f for v in r["verts"] for f in v.link_faces}:
        f.material_index = mat
        f.smooth = True


# ------------------------------------------------------------------ anahtar
def switch(obs):
    ctl_col = bpy.data.collections.get("00_CONTROLS") or bpy.data.collections.new("00_CONTROLS")
    if ctl_col.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(ctl_col)
    ctrl = bpy.data.objects.get("CTRL_SUSLEME") or bpy.data.objects.new("CTRL_SUSLEME", None)
    if ctrl.name not in ctl_col.objects:
        ctl_col.objects.link(ctrl)
    ctrl.empty_display_type = "CIRCLE"
    ctrl.empty_display_size = 0.8
    ctrl.location = (0.0, 0.0, 41.5)
    ctrl["susleme_acik"] = 1
    ctrl.id_properties_ui("susleme_acik").update(min=0, max=1, soft_min=0, soft_max=1, step=1,
                                                 description="1 = Osmanlı süslemeleri açık, 0 = kapalı (sade gemi)")
    for o in obs:
        for path in ("hide_viewport", "hide_render"):
            o.driver_remove(path)
            fc = o.driver_add(path)
            d = fc.driver
            d.type = "SCRIPTED"
            v = d.variables.new()
            v.name = "acik"
            v.type = "SINGLE_PROP"
            v.targets[0].id_type = "OBJECT"
            v.targets[0].id = ctrl
            v.targets[0].data_path = '["susleme_acik"]'
            d.expression = "acik < 0.5"
    return len(obs)


# ------------------------------------------------------------------ render
def render(sc):
    H.setup_render(sc, fast=True)
    sc.cycles.samples = 24
    out = ROOT / "renders" / VER
    out.mkdir(parents=True, exist_ok=True)
    lamp = bpy.data.objects.get("LGT_CabinFill31")
    if lamp is None:
        ld = bpy.data.lights.new("LGT_CabinFill31", "AREA")
        ld.energy, ld.size = 220, 1.6
        lamp = bpy.data.objects.new("LGT_CabinFill31", ld)
        sc.collection.objects.link(lamp)
        lamp.location = (-17.6, 0.0, 5.95)
    views = [
        ("baskasarasi_kupeste", V((9.0, 5.0, 5.2)), V((12.6, 2.9, 4.2)), 28),      # kullanıcının gösterdiği açı
        ("lumbar_kusak", V((4.0, 7.2, 4.9)), V((6.5, 4.9, 4.1)), 35),
        ("kic_arma", V((-26.5, 6.5, 8.2)), V((-20.8, 0.0, 6.2)), 35),
        ("sancak_friz", V((-2.0, 12.5, 6.0)), V((4.0, 4.9, 4.8)), 32),
        ("kasara_alni", V((-9.0, 1.2, 5.6)), V((-15.3, -0.4, 5.3)), 24),
        ("kamara_ic", V((-15.9, -2.6, 5.7)), V((-19.4, 1.4, 4.9)), 16),
        ("bas_rozet", V((20.5, 8.0, 7.6)), V((17.1, 4.8, 7.1)), 35),
        ("ambar_ficilar", V((3.4, 0.0, -0.3)), V((7.0, -2.0, -1.4)), 22),
        ("top_palanga", None, None, 32),
    ]
    hold = bpy.data.objects.get("LGT_HoldFill31")
    if hold is None:
        ld = bpy.data.lights.new("LGT_HoldFill31", "AREA")
        ld.energy, ld.size = 400, 2.5
        hold = bpy.data.objects.new("LGT_HoldFill31", ld)
        sc.collection.objects.link(hold)
        hold.location = (5.0, -0.5, 0.55)
    g = bpy.data.objects["SOCKET_CANNON_S_05"].matrix_world
    views[-1] = ("top_palanga", g @ V((-1.6, -1.0, 1.4)), g @ V((0.2, 0.3, 0.55)), 32)
    for name, loc, tgt, lens in views:
        sc.camera = H.camera(sc, f"CAM31_{name}", loc, tgt, lens=lens)
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
    col = bpy.data.collections.get(COL) or bpy.data.collections.new(COL)
    if col.name not in sc.collection.children:
        sc.collection.children.link(col)
    M = mats()
    rep, obs = {}, []
    rep["channels"] = fix_channels()
    o2, rep["hull_frieze"] = hull_frieze(M, col)
    obs += o2
    o, rep["stern_panel_quads"] = stern_panels(M, col)
    obs.append(o)
    obs.append(stern_crest(M, col))
    o, rep["poop_front_quads"] = poop_front(M, col)
    obs.append(o)
    o, rep["cathead_rosettes"] = cathead_rosettes(M, col)
    obs.append(o)
    o, rep["finials"] = poop_finials(M, col)
    obs.append(o)
    o4, rep["cabin"] = cabin(M, col)
    obs += o4
    P30 = _load("pass_v030", "pass_v030_quality_surface.py")
    fl = QA.floating_islands([bpy.data.objects["MOD_CANNON_TACKLES_TOOLS_A"], bpy.data.objects["CORE_HULL_SHELL"]] +
                             [bpy.data.objects[f"MOD_RIG_STANDING_{m}_A"] for m in ("FORE", "MAIN", "MIZZEN")],
                             bpy.context.evaluated_depsgraph_get())
    if "MOD_CANNON_TACKLES_TOOLS_A" in fl:
        rep["hooks_reattached"] = P30.attach_islands("MOD_CANNON_TACKLES_TOOLS_A", ["CORE_HULL_SHELL"], max_gap=0.25,
                                                     only_near=fl["MOD_CANNON_TACKLES_TOOLS_A"])
    rep["objects"] = {o.name: len(o.data.polygons) for o in obs}
    rep["switch_driven"] = switch(obs)
    lod = LODS.build_lods(sc, only={o.name for o in obs})
    rep["lods"] = len(lod)
    bpy.ops.wm.save_as_mainfile(filepath=str(out), compress=True)
    H.VERSION = VER
    ap = ROOT / "reports" / f"scene_audit_{VER}.json"
    arep = H.audit(sc, ap)
    arep["ornaments_v031"] = rep
    arep["pass"] = {"name": "pass_v031_ottoman_ornaments", "source": f"Blender/versions/{SHIP}_{SRC_VER}.blend",
                    "manifest_version": MANIFEST_VERSION}
    ap.write_text(json.dumps(arep, indent=2, ensure_ascii=False), encoding="utf-8")
    qa = QA.audit(sc, top=60)
    (ROOT / "reports" / f"kalite_testi_{VER}.json").write_text(json.dumps(qa, indent=1, ensure_ascii=False), encoding="utf-8")
    new_q = [r for r in qa["objects"] if r["name"].startswith("MOD_ORN_")]
    print("V031", json.dumps({k: v for k, v in rep.items() if k != "objects"}, ensure_ascii=False))
    print("V031 objects", json.dumps(rep["objects"], ensure_ascii=False))
    print("V031 QA", json.dumps(qa["summary"], ensure_ascii=False))
    print("V031 QA_ORN", json.dumps([(r["name"], r["fail"], r["facet_m"], r["worst_sag_mm"], r["floating_islands"][:2]) for r in new_q],
                                    ensure_ascii=False))
    if "--no-render" not in sys.argv:
        render(sc)


if __name__ == "__main__":
    main()
