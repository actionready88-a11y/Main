"""v046 — Pruva mahmuzu (ram) + figür yuvası; baş parmaklıkları kaldırıldı.

    python3.11 OTTOMAN_FRIGATE_1780_ISTANBUL/scripts/pass_v046_bow_ram_cradle.py [--no-render | --render-only]

Kullanıcı (v045 render): "figür emanet gibi duruyor; bir Ram yap, ona yuva tarzı bir şey yapıp figürü oraya yerleştir;
kurt figürünün etrafındaki çubuk gibi görünenleri de kaldır".
1. CORE_HEAD_RAIL_S/P (figür yanındaki altın çubuklar) + LOD/UCX kaldırılır.
2. MOD_BOW_RAM_A: bodoslamadan öne uzanan tek parça mahmuz. Alt kenar su hattından (bodoslama dibi) öne-yukarı
   süpürülür, uç x ≈ 25,9'da bronz kaplı sivri burun. Üst yüzey figürün alt çizgisini izleyen içbükey yuva; kenarları
   figürün karnını sarar (figür yuvaya gömülü görünür). Pençeler burnun üstüne basar.
   Kesit: süperelips (köşeli-yuvarlak), üstte yuva çukuru; 2,5 cm'de bir kesit, faset eşiği altında.
   Süs: yuva ağzında altın boyalı dudak, altında kızıl bant, alt kenarda bronz sakal şeridi; kalas dokusu için kutu UV.
   Yuvanın arka yarısında 46 cm yan duvar: montaj bloğu ve göğüs altı yuvanın içinde kalır.
3. SOCKET_RAM mahmuz burnuna taşınır (oyunda çarpma noktası); UCX dışbükey gövde, LOD.
Ölçüler [TAHMİN, figür alt profiline göre; Osmanlı kadırga "mahmuz"undan esinli, birebir değil].
"""

import importlib.util
import json
import math
import sys
from pathlib import Path

import bpy  # noqa: I001
import bmesh
from mathutils import Vector
from mathutils.bvhtree import BVHTree

HERE = Path(__file__).resolve().parent


def _load(name, file):
    sp = importlib.util.spec_from_file_location(name, HERE / file)
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


PT = _load("figmount_taslak", "pass_v04X_figurehead_mount_TASLAK.py")
P31 = PT.P31
RS, QA, LODS, H = P31.RS, P31.QA, P31.LODS, P31.H
ROOT, SHIP = P31.ROOT, P31.SHIP
SRC_VER, VER = "v045", "v046"
V = Vector
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT.parent / "skills" / "tersane" / "scripts"))
import lod_store  # noqa: E402

FIG = "MOD_FIGUREHEAD_KURT_D"
NAME = "MOD_BOW_RAM_A"
X0, XTIP = 19.55, 25.95
DX = 0.025
NLOOP = 192
DENSE = 1024
DISH_TAB = [(19.55, 0.40), (20.8, 0.72), (22.2, 0.72), (23.3, 0.28), (24.0, 0.17), (24.9, 0.12), (25.95, 0.02)]   # yuva kenarı − orta
SEAT = 0.03          # yuva orta çizgisi figür altının bu kadar altında (ince gölge çizgisi)


def lerp_tab(tab, x):
    """Catmull-Rom (uçlarda kenetli) — düğümlerde teğet sürekli, faset üretmez."""
    if x <= tab[0][0]:
        return tab[0][1]
    if x >= tab[-1][0]:
        return tab[-1][1]
    for i in range(len(tab) - 1):
        if tab[i][0] <= x <= tab[i + 1][0]:
            break
    (x1, p1), (x2, p2) = tab[i], tab[i + 1]
    x0, p0 = tab[i - 1] if i > 0 else (x1 - (x2 - x1), p1)
    x3, p3 = tab[i + 2] if i + 2 < len(tab) else (x2 + (x2 - x1), p2)
    h = x2 - x1
    m1 = (p2 - p0) / (x2 - x0) * h
    m2 = (p3 - p1) / (x3 - x1) * h
    t = (x - x1) / h
    t2, t3 = t * t, t * t * t
    return (2 * t3 - 3 * t2 + 1) * p1 + (t3 - 2 * t2 + t) * m1 + (-2 * t3 + 3 * t2) * p2 + (t3 - t2) * m2


def figure_underside():
    """Figür orta şerit (|y|<0,3) alt kotu, x adımlı; pençe bölgesinde pençe altı."""
    f = bpy.data.objects[FIG]
    ws = [f.matrix_world @ v.co for v in f.data.vertices]
    tab = {}
    for w in ws:
        if abs(w.y) < 0.30:
            k = round(w.x / 0.1) * 0.1
            tab[k] = min(tab.get(k, 99.0), w.z)
    xs = sorted(tab)
    # 3'lü medyan yumuşatma
    sm = []
    for i, x in enumerate(xs):
        win = sorted(tab[xs[j]] for j in range(max(0, i - 1), min(len(xs), i + 2)))
        sm.append((x, win[len(win) // 2]))
    return sm, min(xs), max(xs)


def profiles(under, fx0, fx1):
    """Orta çizgi üst kotu (yuva), alt kot (sakal), üst/alt yarı genişlik — x → değer tabloları."""
    top = [(X0, 4.95), (20.4, 4.85), (21.0, 4.72)]
    for x, z in under:
        if fx0 + 0.05 <= x <= 24.95:
            top.append((x, z - SEAT))
    top += [(25.25, 3.72), (25.6, 3.62), (XTIP, 3.52)]
    top.sort()
    zs = [z for _, z in top]                                  # 9'lu ortalama (figür örnek gürültüsü)
    top = [(x, sum(zs[max(0, i - 4):i + 5]) / len(zs[max(0, i - 4):i + 5])) if 2 < i < len(top) - 3 else (x, zs[i])
           for i, (x, _) in enumerate(top)]
    # pençe sonrası kısa sıçramaları düzle: tepe çizgisi pençe bölgesinde düşer, sonra burun
    bot = [(X0, -0.30), (20.2, 0.05), (21.2, 0.85), (22.4, 1.75), (23.6, 2.55), (24.7, 3.05), (25.5, 3.32), (XTIP, 3.46)]
    hw_top = [(X0, 0.62), (21.0, 0.56), (22.5, 0.50), (23.6, 0.46), (24.4, 0.34), (25.2, 0.20), (XTIP, 0.02)]
    hw_bot = [(X0, 0.20), (21.5, 0.16), (23.5, 0.12), (25.0, 0.08), (XTIP, 0.015)]
    return top, bot, hw_top, hw_bot


def section(x, T):
    top, bot, hwt, hwb = T
    zt, zb = lerp_tab(top, x), lerp_tab(bot, x)
    ht, hb = lerp_tab(hwt, x), lerp_tab(hwb, x)
    n = 3.2                                           # süperelips üssü (köşeli-yuvarlak)
    pts, meta = [], []
    for i in range(DENSE):
        a = 2 * math.pi * i / DENSE - math.pi / 2     # alt orta'dan başla
        u, v = math.cos(a), math.sin(a)
        Y = math.copysign(abs(u) ** (2 / n), u)
        Z = math.copysign(abs(v) ** (2 / n), v)
        s = (Z + 1) / 2                               # 0 alt, 1 üst
        hw = hb + (ht - hb) * s ** 0.75
        dish = lerp_tab(DISH_TAB, x)
        z = zb + (zt + dish - zb) * s
        if Z > 0:
            z -= dish * (1 - Y * Y) * Z ** 6          # üstte yuva çukuru, kenarlar yüksek
        pts.append(V((x, Y * hw, z)))
        meta.append(((1 - s) * (zt + dish - zb), abs(Y)))
    # yay uzunluğu + eğrilik ağırlığıyla NLOOP noktaya yeniden örnekle (ne orta ne köşe seyrek kalsın)
    cum = [0.0]
    n_ = len(pts)
    for i in range(n_):                        # ağırlık = yay uzunluğu + 0,15 m × dönüş açısı (köşeler de sık kalır)
        a, b, c = pts[i - 1], pts[i], pts[(i + 1) % n_]
        d0, d1 = b - a, c - b
        turn = d0.angle(d1, 0.0) if d0.length > 1e-9 and d1.length > 1e-9 else 0.0
        cum.append(cum[-1] + d1.length + 0.15 * turn)
    L = cum[-1]
    out, om, j = [], [], 0
    for k in range(NLOOP):
        t = L * k / NLOOP
        while cum[j + 1] < t:
            j += 1
        f = (t - cum[j]) / max(cum[j + 1] - cum[j], 1e-9)
        a, b = pts[j], pts[(j + 1) % DENSE]
        ma, mb = meta[j], meta[(j + 1) % DENSE]
        out.append(a.lerp(b, f))
        om.append((ma[0] + (mb[0] - ma[0]) * f, ma[1] + (mb[1] - ma[1]) * f))
    return out, (zt, zb, ht), om


def smooth_path(pts, step):
    """Yay uzunluğuyla eşit aralıklı yeniden örnekle + 2 tur Chaikin (uçlar sabit)."""
    out = [pts[0]]
    acc = 0.0
    for a, b in zip(pts, pts[1:]):
        acc += (b - a).length
        if acc >= step:
            out.append(b)
            acc = 0.0
    if out[-1] != pts[-1]:
        out.append(pts[-1])
    for _ in range(2):
        nw = [out[0]]
        for a, b in zip(out, out[1:]):
            nw += [a.lerp(b, 0.25), a.lerp(b, 0.75)]
        nw.append(out[-1])
        out = nw
    return out


def build_ram(M, col):
    under, fx0, fx1 = figure_underside()
    T = profiles(under, fx0, fx1)
    bm = bmesh.new()
    rings = []
    L_DZ = bm.verts.layers.float.new("dz")
    L_AY = bm.verts.layers.float.new("ay")
    xs, x = [], X0
    while x <= XTIP + 1e-6:                    # dik iniş (yuva dudağı → burun) bölgesinde 8 mm kesit
        xs.append(x)
        x += 0.008 if 23.9 <= x <= 24.95 else DX
    info = []
    for x in xs[:-1]:
        pts, inf, meta = section(x, T)
        ring = [bm.verts.new(p) for p in pts]
        for v, (dz, ay) in zip(ring, meta):
            v[L_DZ], v[L_AY] = dz, ay
        rings.append(ring)
        info.append((x,) + inf)
    tip = bm.verts.new(V((XTIP + 0.02, 0.0, lerp_tab(T[0], XTIP) - 0.02)))
    for r0, r1 in zip(rings, rings[1:]):
        for i in range(NLOOP):
            j = (i + 1) % NLOOP
            bm.faces.new((r0[i], r0[j], r1[j], r1[i]))
    for i in range(NLOOP):
        bm.faces.new((rings[-1][i], rings[-1][(i + 1) % NLOOP], tip))
    back = bm.faces.new(list(reversed(rings[0])))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    # malzeme bölgeleri: 0 katranlı meşe, 1 kızıl bant, 2 altın, 3 bronz burun
    for f in bm.faces:
        c = f.calc_center_median()
        dz = sum(v[L_DZ] for v in f.verts) / len(f.verts)
        ay = sum(v[L_AY] for v in f.verts) / len(f.verts)
        if c.x > 25.15:
            f.material_index = 3
        elif dz < 0.07 and ay > 0.45:
            f.material_index = 2                                     # altın dudak (yuva ağzı)
        elif 0.14 < dz < 0.42 and ay > 0.8 and 20.3 < c.x < 24.9:
            f.material_index = 1                                     # kızıl yan bant
    back.material_index = 0
    geom = __import__("interior_kit")
    geom.RS = RS
    # bronz sakal şeridi: alt kenar boyunca
    path = smooth_path([V((x, 0.0, lerp_tab(T[1], x) - 0.012)) for x in [20.1 + 0.01 * k for k in range(int((25.7 - 20.1) / 0.01) + 1)]], 0.03)
    geom.tube(bm, path, 0.045, mat=3)
    # bronz burun halkaları
    for x in (25.15, 25.45):
        pts, _, _ = section(x, T)
        cen = sum(pts, V()) / len(pts)
        ring = [p + (p - cen).normalized() * 0.018 for p in pts[::2]]
        geom.tube(bm, ring + ring[:2], 0.02, mat=3)
    me = bpy.data.meshes.new(NAME)
    bm.to_mesh(me)
    bm.free()
    for m in (M["hull"], M["red"], M["gilt"], M["bronze"]):
        me.materials.append(m)
    for p in me.polygons:
        p.use_smooth = True
    geom.box_uv(me)
    ob = bpy.data.objects.new(NAME, me)
    col.objects.link(ob)
    ob["module_family"] = "Hull/BowRam"
    ob["socket"] = "SOCKET_RAM"
    ob["note"] = ("Pruva mahmuzu + figür yuvası (v046). Kullanıcı: figür emanet gibi durmasın, Ram'e yuva. "
                  "Oyunda çarpma (ram) noktası burundaki SOCKET_RAM.")
    return ob, T, {"sections": len(rings), "top_center_z": {round(x, 2): round(zt, 2) for x, zt, zb, ht in info[::20]}}


def render(sc):
    H.setup_render(sc, fast=True)
    sc.cycles.samples = 48
    out = ROOT / "renders" / VER
    out.mkdir(parents=True, exist_ok=True)
    c = V((23.2, 0.0, 4.4))
    for name, loc, tgt, lens in (("mahmuz_yan", c + V((0.4, 9.0, 0.2)), c + V((0, 0, -0.6)), 35),
                                 ("mahmuz_on", c + V((6.8, 3.6, 1.0)), c, 35),
                                 ("mahmuz_alt", c + V((3.5, -4.0, -2.6)), c + V((0.3, 0, 0.2)), 32),
                                 ("yuva_ust", c + V((-1.6, 2.4, 3.6)), c + V((0.4, 0, 0.3)), 32),
                                 ("bas_omzu", V((34.0, 14.0, 9.0)), V((21.0, 0.0, 5.0)), 35)):
        sc.camera = H.camera(sc, f"CAM46_{name}", loc, tgt, lens=lens)
        sc.render.filepath = str(out / f"{SHIP}_{VER}_{name}.png")
        bpy.ops.render.render(write_still=True)


def main():
    main_out = ROOT / "Blender" / "versions" / f"{SHIP}_{VER}.blend"
    if "--render-only" in sys.argv:
        bpy.ops.wm.open_mainfile(filepath=str(main_out))
        return render(bpy.context.scene)
    if main_out.exists() or lod_store.lod_path(main_out).exists():
        raise SystemExit(f"{main_out} zaten var; versiyonlu kayıt üzerine yazılmaz.")
    src = ROOT / "Blender" / "versions" / f"{SHIP}_{SRC_VER}.blend"
    bpy.ops.wm.open_mainfile(filepath=str(src))
    sc = bpy.context.scene
    rep = {"lod_load": lod_store.load(src)}
    rep["removed"] = PT.drop(("CORE_HEAD_RAIL_S", "CORE_HEAD_RAIL_P", "UCX_CORE_HEAD_RAIL"))
    M = {"hull": bpy.data.materials["MAT_Hull_TarredOak"], "red": bpy.data.materials["MAT_Hull_RedBand"],
         "gilt": bpy.data.materials["MAT_Trim_Gilt"], "bronze": bpy.data.materials["MAT_Bronze_Ottoman"]}
    col = bpy.data.objects["CORE_STEM"].users_collection[0]
    ob, T, rep["ram"] = build_ram(M, col)
    dg = bpy.context.evaluated_depsgraph_get()
    dg.update()
    me = ob.data
    pts = [v.co.copy() for v in me.vertices]
    tr = BVHTree.FromPolygons(pts, [tuple(p.vertices) for p in me.polygons])
    f = bpy.data.objects[FIG]
    fp = [f.matrix_world @ v.co for v in f.data.vertices]
    tf = BVHTree.FromPolygons(fp, [tuple(p.vertices) for p in f.data.polygons])
    # figür–yuva teması: figür alt noktalarının yuva yüzeyine uzaklığı
    under = [p for p in fp[::7] if abs(p.y) < 0.3]
    near = [tr.find_nearest(p, 1.0)[3] for p in under]
    near = [d for d in near if d is not None]
    rep["figure_seat"] = {"touches": bool(tr.overlap(tf)), "p10_gap_m": round(sorted(near)[len(near) // 10], 3) if near else None}
    st = bpy.data.objects["CORE_STEM"]
    ev = st.evaluated_get(dg).to_mesh()
    ts = BVHTree.FromPolygons([st.matrix_world @ v.co for v in ev.vertices], [tuple(p.vertices) for p in ev.polygons])
    st.evaluated_get(dg).to_mesh_clear()
    rep["stem_joined"] = bool(ts.overlap(tr))
    bs = bpy.data.objects["MOD_RIG_BOWSPRIT_A"]
    tb = BVHTree.FromPolygons([bs.matrix_world @ v.co for v in bs.data.vertices], [tuple(p.vertices) for p in bs.data.polygons])
    rep["bowsprit_clash"] = bool(tb.overlap(tr))
    s = bpy.data.objects.get("SOCKET_RAM")
    if s:
        s.location = V((XTIP, 0.0, lerp_tab(T[0], XTIP) - 0.02))
        s["mount"] = "mahmuz burnu (v046)"
        s["installed_module"] = NAME
        rep["socket_ram"] = [round(c, 2) for c in s.location]
    geom = __import__("geom")
    step = max(1, len(pts) // 3000)
    u = geom.convex_ucx(f"UCX_{NAME}_00", pts[::step], bpy.data.collections["40_COLLISION"], "ram", owner=NAME)
    rep["ucx_verts"] = len(u.data.vertices)
    LODS.build_lods(sc, only={NAME})
    me.calc_loop_triangles()
    rep["tris"] = len(me.loop_triangles)
    H.VERSION = VER
    ap = ROOT / "reports" / f"scene_audit_{VER}.json"
    arep = H.audit(sc, ap)
    arep["bow_ram_v046"] = rep
    arep["pass"] = {"name": "pass_v046_bow_ram_cradle", "source": f"Blender/versions/{SHIP}_{SRC_VER}.blend"}
    qa = QA.audit(sc, top=60)
    (ROOT / "reports" / f"kalite_testi_{VER}.json").write_text(json.dumps(qa, indent=1, ensure_ascii=False), encoding="utf-8")
    rep["save"] = lod_store.save_split(main_out)
    ap.write_text(json.dumps(arep, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    print("V046", json.dumps(rep, ensure_ascii=False, default=str))
    print("V046 QA", json.dumps(qa["summary"], ensure_ascii=False))
    for x in [x for x in qa["objects"] if x["fail"] or x["floating_islands"]]:
        print(f"  HATA {x['name']} facet={x['facet_m']}m sag={x['worst_sag_mm']}mm havada={x['floating_islands'][:3]}")
    if "--no-render" not in sys.argv:
        render(sc)


if __name__ == "__main__":
    main()
