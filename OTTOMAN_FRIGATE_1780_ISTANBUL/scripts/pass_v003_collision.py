"""Pass v003 — oyun çarpışması (UCX) yeniden kurulumu (v002 üzerine; geometri değişmez).

Çalıştırma (depo kökünden):
    python3 OTTOMAN_FRIGATE_1700_ISTANBUL/scripts/pass_v003_collision.py [--no-render]

Kullanıcı bulgusu (Blender viewport): gövde "tel örgü / yırtık" görünüyor.
Kök neden: v001/v002 UCX parçaları yoğun render mesh'inin dışbükey kabuğuydu:
  - viewport'ta görünür bırakılmıştı (WIRE),
  - binlerce ince üçgen içeriyordu (UE için uygun değil),
  - alçak beli kasaralar arasında kapak gibi örtüyordu (yürünebilir güverte engeli).
Yeni düzen (hepsi UE adlandırması `UCX_CORE_HULL_SHELL_NN`, amaç `ucx_purpose` özelliğinde):
  - hull     : su altı → batarya güvertesi, 6 dilim, analitik gövdeden seyrek noktalar
  - deck_*   : batarya/kıç kasarası/baş kasarası güverteleri, sheer + kamburluğu izleyen dilimler
  - bulwark_*: küpeşte duvarları (düşmeyi engeller), borda başına dilimler
  Bel üstü açık kalır. `40_COLLISION` ve kesici nesneler viewport'ta gizli.
"""

import importlib.util
import json
import sys
from pathlib import Path

import bpy  # noqa: I001
import bmesh
import numpy as np
from mathutils import Vector

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("hull_v001", HERE / "build_hull_v001.py")
H = importlib.util.module_from_spec(spec)
spec.loader.exec_module(H)

SRC_VER, VER = "v002", "v003"
ROOT, SHIP = H.ROOT, H.SHIP_ID
MAX_VERTS = 64  # UCX başına üst sınır (proje hedefi)


def convex(name, pts, col, purpose):
    bm = bmesh.new()
    for p in pts:
        bm.verts.new(p)
    bmesh.ops.convex_hull(bm, input=bm.verts)
    loose = [v for v in bm.verts if not v.link_faces]
    bmesh.ops.delete(bm, geom=loose, context="VERTS")
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    col.objects.link(ob)
    ob.display_type = "WIRE"
    ob.hide_render = True
    ob["ucx_purpose"] = purpose
    return ob


def hull_slices(n=6):
    out = []
    edges = np.linspace(0.0, 1.0, n + 1)
    for k in range(n):
        pts = []
        for s in (edges[k], edges[k + 1]):
            top = H.deck_z(s)
            for z in np.linspace(H.ZK, top, 9):
                x, y = H.hull_point(s, z)
                y = max(y, 0.15)
                pts += [Vector((x, y, z)), Vector((x, -y, z))]
            # omurga altı
            pts.append(Vector((H.hull_point(s, H.ZK)[0], 0.0, -H.T)))
        out.append((pts, "hull"))
    return out


def deck_slices(s0, s1, z_fn, n, purpose, inset=0.24):
    out = []
    edges = np.linspace(s0, s1, n + 1)
    for k in range(n):
        pts = []
        for s in (edges[k], edges[k + 1]):
            z = z_fn(s)
            x, y = H.hull_point(s, z)
            w = max(y - inset, 0.3)
            pts += [Vector((x, w, z)), Vector((x, -w, z)), Vector((x, 0.0, z + 0.12)),
                    Vector((x, w, z - 0.25)), Vector((x, -w, z - 0.25))]
        out.append((pts, purpose))
    return out


def bulwark_slices(n=14):
    out = []
    edges = np.linspace(0.02, 0.98, n + 1)
    for side in (1, -1):
        for k in range(n):
            pts = []
            for s in (edges[k], edges[k + 1]):
                for z in (H.deck_z(s), H.top_z(s)):
                    x, y = H.hull_point(s, z)
                    pts += [Vector((x, side * y, z)), Vector((x, side * (y - 0.26), z))]
            out.append((pts, "bulwark_starboard" if side > 0 else "bulwark_port"))
    return out


def main():
    bpy.ops.wm.open_mainfile(filepath=str(ROOT / "Blender" / "versions" / f"{SHIP}_{SRC_VER}.blend"))
    sc = bpy.context.scene
    col = bpy.data.collections["40_COLLISION"]
    old = [o.name for o in col.objects if o.name.startswith("UCX_")]
    for n in old:
        ob = bpy.data.objects[n]
        me = ob.data
        bpy.data.objects.remove(ob, do_unlink=True)
        if me.users == 0:
            bpy.data.meshes.remove(me)

    parts = hull_slices(6)
    parts += deck_slices(0.02, 0.975, H.deck_z, 10, "deck_gun")
    parts += deck_slices(0.004, H.S_QD, lambda s: H.deck_z(s) + H.QD_H, 4, "deck_quarter")
    parts += deck_slices(H.S_FC, 0.985, lambda s: H.deck_z(s) + H.QD_H, 2, "deck_forecastle")
    parts += bulwark_slices(14)
    made = []
    for k, (pts, purpose) in enumerate(parts):
        made.append(convex(f"UCX_CORE_HULL_SHELL_{k:02d}", pts, col, purpose))

    # viewport temizliği: çarpışma ve kesiciler varsayılan gizli
    def layer_coll(lc, name):
        if lc.collection.name == name:
            return lc
        for ch in lc.children:
            r = layer_coll(ch, name)
            if r:
                return r
    layer_coll(bpy.context.view_layer.layer_collection, "40_COLLISION").hide_viewport = True
    cut = bpy.data.objects.get("CUT_GUNPORTS")
    if cut:
        cut.hide_set(True)
        cut.hide_viewport = True

    out = ROOT / "Blender" / "versions" / f"{SHIP}_{VER}.blend"
    if out.exists():
        raise SystemExit(f"{out} zaten var; versiyonlu kayıt üzerine yazılmaz.")
    bpy.ops.wm.save_as_mainfile(filepath=str(out), compress=True)

    H.VERSION = VER
    ap = ROOT / "reports" / f"scene_audit_{VER}.json"
    rep = H.audit(sc, ap)
    ucx = [{"name": o.name, "purpose": o["ucx_purpose"], "verts": len(o.data.vertices),
            "tris": sum(len(p.vertices) - 2 for p in o.data.polygons)} for o in made]
    rep["collision"] = {
        "count": len(ucx), "max_verts": max(u["verts"] for u in ucx),
        "over_limit": [u["name"] for u in ucx if u["verts"] > MAX_VERTS],
        "by_purpose": {p: sum(1 for u in ucx if u["purpose"] == p) for p in sorted({u["purpose"] for u in ucx})},
        "total_tris": sum(u["tris"] for u in ucx), "parts": ucx,
        "waist_open": True, "viewport_hidden": True,
    }
    rep["pass"] = {"name": "pass_v003_collision", "source": f"Blender/versions/{SHIP}_{SRC_VER}.blend",
                   "pass_changes": {"removed": old, "added": [o.name for o in made],
                                    "visibility": ["40_COLLISION hide_viewport", "CUT_GUNPORTS hide_viewport"]},
                   "geometry_changed": False}
    ap.write_text(json.dumps(rep, indent=2, ensure_ascii=False), encoding="utf-8")
    c = rep["collision"]
    print("UCX", c["count"], "max_verts", c["max_verts"], "over", c["over_limit"], "tris", c["total_tris"], c["by_purpose"])

    if "--no-render" not in sys.argv:
        render_collision_preview(sc, made)


def render_collision_preview(sc, made):
    """Çarpışmayı renkli yarı saydam gösteren önizleme (yalnız render için; .blend'e kaydedilmez)."""
    colors = {"hull": (0.1, 0.5, 1.0), "deck_gun": (0.2, 0.9, 0.3), "deck_quarter": (0.2, 0.9, 0.3),
              "deck_forecastle": (0.2, 0.9, 0.3), "bulwark_port": (1.0, 0.6, 0.1), "bulwark_starboard": (1.0, 0.6, 0.1)}
    mats = {}
    for p, c in colors.items():
        m = bpy.data.materials.new(f"PREVIEW_UCX_{p}")
        m.use_nodes = True
        b = m.node_tree.nodes["Principled BSDF"]
        b.inputs["Base Color"].default_value = (*c, 1)
        b.inputs["Alpha"].default_value = 0.55
        b.inputs["Emission Color"].default_value = (*c, 1)
        b.inputs["Emission Strength"].default_value = 0.4
        mats[p] = m
    for o in made:
        o.hide_render = False
        o.display_type = "SOLID"
        o.data.materials.append(mats[o["ucx_purpose"]])
    for o in sc.objects:
        if o.type == "MESH" and not o.name.startswith(("UCX_", "CUT_")):
            o.hide_render = True
    H.setup_render(sc, fast=True)
    out = ROOT / "renders" / VER
    out.mkdir(parents=True, exist_ok=True)
    for name, loc, tgt, lens in (("collision_3_4", (30, 24, 16), (0, 0, 0.5), 35),
                                 ("collision_ust", (4, 10, 45), (0, 0, 1.5), 40)):
        sc.camera = H.camera(sc, f"CAM_{name}", loc, tgt, lens=lens)
        sc.render.filepath = str(out / f"{SHIP}_{VER}_{name}.png")
        bpy.ops.render.render(write_still=True)
    sc.camera = H.camera(sc, "CAM_col_profil", (0, -80, 1.0), (0, 0, 1.0), ortho=44)
    sc.render.filepath = str(out / f"{SHIP}_{VER}_collision_profil.png")
    bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    main()
