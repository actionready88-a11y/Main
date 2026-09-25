"""Referans bir .blend dosyasının kalite denetimi (yerelde, kullanıcının Blender'ında çalışır).

Amaç: lisanslı bir referans gemiyi (ör. Fab varlığı) repoya KOPYALAMADAN kalite hedeflerini
çıkarmak: üçgen bütçesi, nesne/modül ayrımı, malzeme ve doku yapısı, doku çözünürlükleri,
UV kanalları, texel yoğunluğu, LOD/collision adlandırması.

Windows örneği (tek satır):
  "C:\\Program Files\\Blender Foundation\\Blender 5.2\\blender.exe" --background "D:\\yol\\ship.blend"
      --python "C:\\Users\\Murat\\Main\\OTTOMAN_FRIGATE_1700_ISTANBUL\\scripts\\inspect_reference_blend.py"
      -- --out "C:\\Users\\Murat\\Main\\OTTOMAN_FRIGATE_1700_ISTANBUL\\reports\\reference_audit\\age_of_sail" --render

Çıktı: <out>/reference_audit.json, <out>/reference_audit.md ve --render verilirse <out>/renders/*.png
Repoya yalnız bu çıktılar gönderilir; .blend ve doku dosyaları gönderilmez.
Blender 4.2+ ve 5.x ile uyumlu.
"""

import json
import math
import os
import sys
from collections import Counter, defaultdict

import bpy
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[argv.index("--out") + 1] if "--out" in argv else os.path.join(os.path.dirname(bpy.data.filepath), "reference_audit")
DO_RENDER = "--render" in argv
os.makedirs(OUT, exist_ok=True)

sc = bpy.context.scene
dg = bpy.context.evaluated_depsgraph_get()


def tri_count(ob):
    ev = ob.evaluated_get(dg)
    try:
        me = ev.to_mesh()
    except RuntimeError:
        return 0, 0, 0.0
    me.calc_loop_triangles()
    tris = len(me.loop_triangles)
    verts = len(me.vertices)
    area = sum(p.area for p in me.polygons)
    ev.to_mesh_clear()
    return tris, verts, area


def images_of_material(mat):
    out = []
    if not mat or not mat.use_nodes or not mat.node_tree:
        return out
    stack = [mat.node_tree]
    seen = set()
    while stack:
        nt = stack.pop()
        if nt in seen:
            continue
        seen.add(nt)
        for n in nt.nodes:
            if n.type == "TEX_IMAGE" and n.image:
                links = [l.to_socket.name for o in n.outputs for l in o.links]
                out.append({"image": n.image.name, "to": links,
                            "colorspace": n.image.colorspace_settings.name,
                            "interpolation": n.interpolation, "projection": n.projection})
            elif n.type == "GROUP" and n.node_tree:
                stack.append(n.node_tree)
    return out


def node_types(mat):
    if not mat or not mat.use_nodes or not mat.node_tree:
        return {}
    return dict(Counter(n.bl_idname for n in mat.node_tree.nodes))


# --- Nesneler --------------------------------------------------------------
objects = []
by_collection = defaultdict(lambda: {"objects": 0, "tris": 0})
mat_users = defaultdict(list)
mat_area = defaultdict(float)
total_tris = 0
bb_min = Vector((1e9, 1e9, 1e9))
bb_max = Vector((-1e9, -1e9, -1e9))
name_patterns = Counter()
for ob in sc.objects:
    e = {"name": ob.name, "type": ob.type, "parent": ob.parent.name if ob.parent else None,
         "collections": [c.name for c in ob.users_collection],
         "hide_render": ob.hide_render, "scale": [round(v, 4) for v in ob.scale],
         "rotation_deg": [round(math.degrees(v), 2) for v in ob.rotation_euler]}
    for pre in ("UCX_", "UBX_", "USP_", "LOD", "SOCKET_", "SM_", "SK_"):
        if ob.name.upper().startswith(pre) or f"_{pre}" in ob.name.upper():
            name_patterns[pre] += 1
    if ob.type == "MESH":
        tris, verts, area = tri_count(ob)
        e.update({"tris": tris, "verts": verts, "surface_m2": round(area, 3),
                  "modifiers": [f"{m.type}:{m.name}" for m in ob.modifiers],
                  "uv_layers": [u.name for u in ob.data.uv_layers],
                  "materials": [m.name if m else None for m in ob.data.materials],
                  "dimensions_m": [round(v, 3) for v in ob.dimensions],
                  "shade_smooth_ratio": round(sum(p.use_smooth for p in ob.data.polygons) / max(len(ob.data.polygons), 1), 3),
                  "custom_normals": ob.data.has_custom_normals,
                  "vertex_colors": [a.name for a in getattr(ob.data, "color_attributes", [])]})
        if not ob.hide_render:
            total_tris += tris
            for c in ob.users_collection:
                by_collection[c.name]["objects"] += 1
                by_collection[c.name]["tris"] += tris
            for corner in ob.bound_box:
                w = ob.matrix_world @ Vector(corner)
                bb_min = Vector(map(min, bb_min, w))
                bb_max = Vector(map(max, bb_max, w))
            for m in ob.data.materials:
                if m:
                    mat_users[m.name].append(ob.name)
                    mat_area[m.name] += area / max(len(ob.data.materials), 1)
    elif ob.type == "CURVE":
        e.update({"bevel_depth": ob.data.bevel_depth, "resolution": ob.data.resolution_u,
                  "splines": len(ob.data.splines)})
    objects.append(e)

# --- Malzemeler ve dokular ---------------------------------------------------
materials = []
for m in bpy.data.materials:
    if m.users == 0:
        continue
    imgs = images_of_material(m)
    materials.append({"name": m.name, "users": mat_users.get(m.name, []), "images": imgs,
                      "node_types": node_types(m),
                      "blend_method": getattr(m, "blend_method", None),
                      "approx_surface_m2": round(mat_area.get(m.name, 0.0), 2)})

images = []
for im in bpy.data.images:
    if im.type != "IMAGE":
        continue
    images.append({"name": im.name, "size": list(im.size), "filepath": im.filepath,
                   "packed": im.packed_file is not None, "colorspace": im.colorspace_settings.name,
                   "file_format": im.file_format, "users": im.users,
                   "exists": im.packed_file is not None or os.path.exists(bpy.path.abspath(im.filepath))})

# texel yoğunluğu (kaba): malzemenin en büyük dokusu / kapladığı alanın karekökü
texel = []
img_size = {i["name"]: max(i["size"]) for i in images}
for m in materials:
    sizes = [img_size.get(i["image"], 0) for i in m["images"]]
    if sizes and m["approx_surface_m2"] > 0:
        texel.append({"material": m["name"], "max_texture_px": max(sizes),
                      "px_per_m_if_unique_uv": round(max(sizes) / math.sqrt(m["approx_surface_m2"]), 1),
                      "note": "tiling/trim UV kullanılıyorsa gerçek yoğunluk daha yüksektir"})

report = {
    "file": bpy.data.filepath,
    "blender": bpy.app.version_string,
    "unit_system": sc.unit_settings.system, "unit_scale": sc.unit_settings.scale_length,
    "render_engine": sc.render.engine,
    "totals": {"objects": len(sc.objects),
               "by_type": dict(Counter(o.type for o in sc.objects)),
               "render_tris": total_tris,
               "materials": len(materials), "images": len(images),
               "image_sizes": dict(Counter(f"{i['size'][0]}x{i['size'][1]}" for i in images)),
               "bounds_m": {"min": [round(v, 3) for v in bb_min], "max": [round(v, 3) for v in bb_max],
                            "size": [round(a - b, 3) for a, b in zip(bb_max, bb_min)]},
               "name_patterns": dict(name_patterns)},
    "collections": {k: v for k, v in sorted(by_collection.items(), key=lambda kv: -kv[1]["tris"])},
    "top_objects_by_tris": sorted([o for o in objects if o.get("tris")], key=lambda o: -o["tris"])[:40],
    "materials": materials,
    "images": images,
    "texel_estimate": texel,
    "objects": objects,
}
with open(os.path.join(OUT, "reference_audit.json"), "w", encoding="utf-8") as f:
    json.dump(report, f, indent=2, ensure_ascii=False)

# --- Kısa Markdown özeti --------------------------------------------------------
t = report["totals"]
lines = [f"# Referans denetimi: {os.path.basename(bpy.data.filepath)}", "",
         f"- Blender {report['blender']}, birim {t['bounds_m']['size']} (m, sahne sınırları)",
         f"- Nesne: {t['objects']} {t['by_type']}",
         f"- Render üçgeni: {t['render_tris']:,}",
         f"- Malzeme: {t['materials']}, doku: {t['images']} — boyutlar: {t['image_sizes']}",
         f"- Ad kalıpları: {t['name_patterns']}", "", "## En ağır 15 nesne", "",
         "| Nesne | Üçgen | Malzemeler | UV | Modifier |", "|---|---|---|---|---|"]
for o in report["top_objects_by_tris"][:15]:
    lines.append(f"| {o['name']} | {o['tris']:,} | {', '.join(filter(None, o['materials']))} | {len(o['uv_layers'])} | {', '.join(o['modifiers'])} |")
lines += ["", "## Koleksiyonlar", "", "| Koleksiyon | Nesne | Üçgen |", "|---|---|---|"]
for k, v in report["collections"].items():
    lines.append(f"| {k} | {v['objects']} | {v['tris']:,} |")
lines += ["", "## Malzemeler", "", "| Malzeme | Dokular (bağlandığı giriş) |", "|---|---|"]
for m in materials:
    lines.append(f"| {m['name']} | {'; '.join(i['image'] + ' → ' + ','.join(i['to']) for i in m['images'])} |")
with open(os.path.join(OUT, "reference_audit.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")

# --- İsteğe bağlı renderlar ------------------------------------------------------
if DO_RENDER:
    rdir = os.path.join(OUT, "renders")
    os.makedirs(rdir, exist_ok=True)
    engines = [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items]
    sc.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in engines else "BLENDER_EEVEE"
    sc.render.resolution_x, sc.render.resolution_y = 1600, 900
    sc.render.film_transparent = False
    center = (bb_min + bb_max) / 2
    size = bb_max - bb_min
    span = max(size.x, size.y)
    if not any(o.type == "LIGHT" and not o.hide_render for o in sc.objects):
        sun = bpy.data.lights.new("AUDIT_Sun", "SUN"); sun.energy = 3.0
        so = bpy.data.objects.new("AUDIT_Sun", sun)
        so.rotation_euler = (math.radians(50), math.radians(10), math.radians(-35))
        sc.collection.objects.link(so)
    long_axis_x = size.x >= size.y
    views = {
        "on": Vector((1, 0, 0)) if long_axis_x else Vector((0, -1, 0)),
        "arka": Vector((-1, 0, 0)) if long_axis_x else Vector((0, 1, 0)),
        "sol": Vector((0, -1, 0)) if long_axis_x else Vector((-1, 0, 0)),
        "sag": Vector((0, 1, 0)) if long_axis_x else Vector((1, 0, 0)),
        "uc_ceyrek": Vector((0.8, 0.7, 0.45)).normalized(),
        "guverte": Vector((0.3, 0.25, 1.0)).normalized(),
    }
    for name, d in views.items():
        cam = bpy.data.cameras.new(f"AUDIT_{name}")
        ortho = name in ("on", "arka", "sol", "sag")
        if ortho:
            cam.type = "ORTHO"
            cam.ortho_scale = span * 1.15 if name in ("sol", "sag") else max(size.z, min(size.x, size.y)) * 1.4
        else:
            cam.lens = 35
        cam.clip_end = span * 20
        ob = bpy.data.objects.new(f"AUDIT_{name}", cam)
        ob.location = center + d * span * 1.6
        ob.rotation_euler = (center - ob.location).to_track_quat("-Z", "Y").to_euler()
        sc.collection.objects.link(ob)
        sc.camera = ob
        sc.render.filepath = os.path.join(rdir, f"ref_{name}.png")
        bpy.ops.render.render(write_still=True)

print(f"[inspect_reference_blend] tamam → {OUT}")
