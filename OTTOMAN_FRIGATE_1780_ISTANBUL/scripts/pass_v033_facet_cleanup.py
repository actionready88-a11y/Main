"""v033 — kalan küçük fasetlerin temizliği (kullanıcı: "kalan küçük fasetleri de düzelt").

    python3.11 OTTOMAN_FRIGATE_1780_ISTANBUL/scripts/pass_v033_facet_cleanup.py

 1. Süslemeler: alem/arma lathe profilleri sıklaştırılır (resegment), hilal/madalyon/kanat eğrileri 2–2,5× (arma yeniden).
 2. Sedir minderleri: süper-elipsoit köşeleri (3,6 mm) → 8 segment bevelli yuvarlak kutu.
 3. Kıç panoları, tavan kaplaması: iç köşeler Laplace yumuşatma (kenar sabit) — alttaki gövde fasetini izlemesin.
 4. Direk çanaklık kenarı (D biçimi, 64 nokta → 16 mm): dış/iç halkalar kapalı Catmull-Rom ile 3× sıklaştırılır.
 5. Flandra: yumuşak alt bölme. (Filikada denendi, sert kenarlarda gövdeyi şişirdi → uygulanmadı.)
v031/v032 betikleri değiştirilmez.
"""

import importlib.util
import inspect
import json
import math
from pathlib import Path

import bpy  # noqa: I001
import bmesh
from mathutils import Vector

HERE = Path(__file__).resolve().parent
sp = importlib.util.spec_from_file_location("pass_v032", HERE / "pass_v032_frieze_continuous.py")
P32 = importlib.util.module_from_spec(sp)
sp.loader.exec_module(P32)
P31 = P32.P31                                    # v032 yamaları (arma yönü) uygulanmış v031 modülü
RS, QA, LODS = P31.RS, P31.QA, P31.LODS
ROOT, SHIP = P31.ROOT, P31.SHIP
SRC_VER, VER = "v032", "v033"
V = Vector


_SRC = {}


def _file_src(fn_name):
    """Fonksiyonun kaynağı v031 dosyasından (exec ile yeniden tanımlanmış fonksiyonda inspect yanlış satır okur)."""
    if fn_name not in _SRC:
        text = Path(P31.__file__).read_text(encoding="utf-8")
        a = text.index(f"\ndef {fn_name}(") + 1
        b = text.find("\ndef ", a + 5)
        _SRC[fn_name] = text[a:b if b > 0 else len(text)]
        if fn_name == "stern_crest":            # v032 yön yaması
            _SRC[fn_name] = _SRC[fn_name].replace("    U, Vv, N = V((0, 1, 0)), V((0, 0, 1)), V((-1, 0, 0))",
                                                  "    U, Vv, N = V((0, -1, 0)), V((0, 0, 1)), V((-1, 0, 0))")
    return _SRC[fn_name]


def patch_default(fn_name, old, new):
    src = _file_src(fn_name)
    assert old in src, (fn_name, old)
    _SRC[fn_name] = src.replace(old, new)
    exec(compile(_SRC[fn_name], P31.__file__, "exec"), P31.__dict__)


def drop(name):
    for o in [o for o in bpy.data.objects if o.name == name or o.name.startswith(name + "_LOD")]:
        me = o.data
        bpy.data.objects.remove(o, do_unlink=True)
        if me is not None and me.users == 0:
            bpy.data.meshes.remove(me)


def rounded_box(bm, c, hx, hy, hz, r, mat):
    ret = bmesh.ops.create_cube(bm, size=1.0)
    vs = ret["verts"]
    for v in vs:
        v.co = c + V((v.co.x * 2 * hx, v.co.y * 2 * hy, v.co.z * 2 * hz))
    edges = list({e for v in vs for e in v.link_edges})
    res = bmesh.ops.bevel(bm, geom=vs + edges, offset=r, segments=8, profile=0.5, affect="EDGES", clamp_overlap=True)
    fs = list({f for v in vs if v.is_valid for f in v.link_faces} | set(res.get("faces", [])))
    for f in fs:
        f.material_index = mat
        f.smooth = True


def rebuild_cushions(M, col):
    """Minderleri bevelli yuvarlak kutu olarak yeniden kur (yastıklar ve silindir yastıklar aynı kalır)."""
    ob = bpy.data.objects["MOD_ORN_CABIN_CUSHIONS"]
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.faces.index_update()
    removed = 0
    for fs in RS.islands(bm):
        if fs[0].material_index != 0:
            continue
        vs = list({v for f in fs for v in f.verts})
        lo = V((min(v.co.x for v in vs), min(v.co.y for v in vs), min(v.co.z for v in vs)))
        hi = V((max(v.co.x for v in vs), max(v.co.y for v in vs), max(v.co.z for v in vs)))
        c, h = (lo + hi) / 2, (hi - lo) / 2
        bmesh.ops.delete(bm, geom=vs, context="VERTS")
        rounded_box(bm, c, h.x, h.y, h.z, min(h.z * 0.8, 0.035), 0)
        removed += 1
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(ob.data)
    bm.free()
    RS.sharp_from_angle_keep(ob.data, 50)
    P31.geo_uv(ob.data)
    return removed


def smooth_patch(name, iters=12, factor=0.5):
    ob = bpy.data.objects[name]
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    inner = [v for v in bm.verts if not v.is_boundary and all(len(e.link_faces) == 2 for e in v.link_edges)]
    for _ in range(iters):
        bmesh.ops.smooth_vert(bm, verts=inner, factor=factor, use_axis_x=True, use_axis_y=True, use_axis_z=True)
    bm.to_mesh(ob.data)
    bm.free()
    return len(inner)


def _cr(p0, p1, p2, p3, t):
    return RS._cr(p0, p1, p2, p3, t)


def densify_loop(pts, k=3):
    n = len(pts)
    out = []
    for i in range(n):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[(i + 1) % n], pts[(i + 2) % n]
        for j in range(k):
            out.append(_cr(p0, p1, p2, p3, j / k))
    return out


def mast_tops():
    """Çanaklık: 64 ışınla örneklenmiş D biçimli halka levha (4 halka: dış/iç × üst/alt). Açıya göre sıralanıp 3× sıklaştırılır."""
    rep = {}
    for mast in ("FORE", "MAIN", "MIZZEN"):
        ob = bpy.data.objects[f"MOD_RIG_MAST_{mast}_A"]
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        bm.faces.index_update()
        best = None
        for fs in RS.islands(bm):
            vs = list({v for f in fs for v in f.verts})
            if len(vs) % 2 or len(vs) < 128:
                continue
            ext = [max(v.co[i] for v in vs) - min(v.co[i] for v in vs) for i in range(3)]
            flat = sorted(range(3), key=lambda i: ext[i])[0]
            if ext[flat] < 0.2 and sorted(ext)[1] > 1.0 and (best is None or len(vs) > len(best[1])):
                best = (fs, vs, flat)
        if best is None:
            rep[mast] = "bulunamadı"
            bm.free()
            continue
        fs, vs, ax = best
        mat = fs[0].material_index
        c = sum((v.co for v in vs), V()) / len(vs)
        hv = [v.co[ax] for v in vs]
        mid = (max(hv) + min(hv)) / 2
        u_ax, v_ax = [i for i in range(3) if i != ax]
        # iç/dış: merkezden uzaklığa göre ikiye (aynı açıdaki iki nokta)
        loops = {}
        for top in (True, False):
            ring = [v for v in vs if (v.co[ax] > mid) == top]
            ring.sort(key=lambda v: math.atan2(v.co[v_ax] - c[v_ax], v.co[u_ax] - c[u_ax]))
            n = len(ring) // 2
            if n * 2 != len(ring):
                break
            pairs = [sorted(ring[2 * i:2 * i + 2], key=lambda v: (V((v.co[u_ax] - c[u_ax], v.co[v_ax] - c[v_ax])).length)) for i in range(n)]
            loops[(top, "i")] = [p[0].co.copy() for p in pairs]
            loops[(top, "o")] = [p[1].co.copy() for p in pairs]
        if len(loops) != 4:
            rep[mast] = "halka yapısı uymadı"
            bm.free()
            continue
        bmesh.ops.delete(bm, geom=vs, context="VERTS")
        L = {k: [bm.verts.new(p) for p in densify_loop(v)] for k, v in loops.items()}
        m = len(L[(True, "o")])
        newf = []
        for a, b in (((True, "i"), (True, "o")), ((False, "o"), (False, "i")), ((True, "o"), (False, "o")), ((False, "i"), (True, "i"))):
            A, B = L[a], L[b]
            for k in range(m):
                newf.append(bm.faces.new([A[k], B[k], B[(k + 1) % m], A[(k + 1) % m]]))
        for f in newf:
            f.material_index = mat
            f.smooth = True
        bmesh.ops.recalc_face_normals(bm, faces=newf)
        bm.to_mesh(ob.data)
        bm.free()
        RS.sharp_from_angle_keep(ob.data, 35)
        rep[mast] = {"ring_pts": m}
    return rep


def smooth_subdiv(name, mat_index=None, cuts=1):
    ob = bpy.data.objects[name]
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    faces = [f for f in bm.faces if mat_index is None or f.material_index == mat_index]
    edges = list({e for f in faces for e in f.edges})
    bmesh.ops.subdivide_edges(bm, edges=edges, cuts=cuts, use_grid_fill=True, smooth=1.0)
    bm.to_mesh(ob.data)
    bm.free()
    return len(faces)


def main():
    out = ROOT / "Blender" / "versions" / f"{SHIP}_{VER}.blend"
    if out.exists():
        raise SystemExit(f"{out} zaten var; versiyonlu kayıt üzerine yazılmaz.")
    bpy.ops.wm.open_mainfile(filepath=str(ROOT / "Blender" / "versions" / f"{SHIP}_{SRC_VER}.blend"))
    sc = bpy.context.scene
    col = bpy.data.collections[P31.COL]
    M = P31.mats()
    rep = {}
    # 1. arma: eğri çözünürlüğü
    patch_default("crescent2d", "def crescent2d(R, r, off, n=96):", "def crescent2d(R, r, off, n=240):")
    patch_default("rumi_wing2d", "def rumi_wing2d(s, n=96):", "def rumi_wing2d(s, n=200):")
    patch_default("stern_crest", "ogee2d(0.78, 0.92, 160)", "ogee2d(0.78, 0.92, 320)")
    patch_default("stern_crest", "ring_o = ogee2d(0.86, 1.00, 160)", "ring_o = ogee2d(0.86, 1.00, 320)")
    drop("MOD_ORN_STERN_CREST")
    P31.stern_crest(M, col)
    # 2. minder
    rep["cushions_rebuilt"] = rebuild_cushions(M, col)
    # 3. yama yumuşatma
    rep["smoothed"] = {n: smooth_patch(n) for n in ("MOD_ORN_STERN_PANELS", "MOD_ORN_CABIN_CEILING")}
    # süsleme lathe'leri (alem, arma tepesi, rozet göbeği, silindir yastık): profil sıklaştırma
    rep["orn_resegment"] = {o.name: RS.resegment_object(o) for o in col.objects if o.type == "MESH" and "_LOD" not in o.name}
    # 4. çanaklıklar
    rep["mast_tops"] = mast_tops()
    # 5. filika gövdesi ve flandra
    # filika: yumuşak alt bölme sert kenarlarda gövdeyi şişirdi (7 → 45 mm) → uygulanmaz
    rep["pennant_faces"] = smooth_subdiv("MOD_FLAG_PENNANT_OTTOMAN_A")
    # süsleme anahtarı yeni arma nesnesine
    P31.switch([o for o in col.objects if o.type == "MESH" and "_LOD" not in o.name])
    # değişen nesnelerin LOD'ları
    changed = ["MOD_ORN_STERN_CREST", "MOD_ORN_CABIN_CUSHIONS", "MOD_ORN_STERN_PANELS", "MOD_ORN_CABIN_CEILING",
               "MOD_RIG_MAST_FORE_A", "MOD_RIG_MAST_MAIN_A", "MOD_RIG_MAST_MIZZEN_A"]
    for n in changed:
        for o in [o for o in bpy.data.objects if o.name.startswith(n + "_LOD")]:
            bpy.data.objects.remove(o, do_unlink=True)
    LODS.build_lods(sc, only=set(changed))
    bpy.ops.wm.save_as_mainfile(filepath=str(out), compress=True)
    P31.H.VERSION = VER
    ap = ROOT / "reports" / f"scene_audit_{VER}.json"
    arep = P31.H.audit(sc, ap)
    arep["facets_v033"] = rep
    arep["pass"] = {"name": "pass_v033_facet_cleanup", "source": f"Blender/versions/{SHIP}_{SRC_VER}.blend"}
    ap.write_text(json.dumps(arep, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    qa = QA.audit(sc, top=60)
    (ROOT / "reports" / f"kalite_testi_{VER}.json").write_text(json.dumps(qa, indent=1, ensure_ascii=False), encoding="utf-8")
    print("V033", json.dumps({k: v for k, v in rep.items() if k != "orn_resegment"}, ensure_ascii=False, default=str))
    print("V033 QA", json.dumps(qa["summary"], ensure_ascii=False))
    for r in sorted([r for r in qa["objects"] if r["fail"]], key=lambda r: -r["facet_m"]):
        print(f"  HATA {r['name']} facet={r['facet_m']}m sag={r['worst_sag_mm']}mm flat={r['flat_ratio']} havada={r['floating_islands'][:2]}")


if __name__ == "__main__":
    main()
