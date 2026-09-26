"""Prosedürel malzemeleri UE 5.8 için döşenebilir doku setlerine bake eder (BaseColor / Normal / ORM).

Çalıştırma (depo kökünden):
    python3 OTTOMAN_FRIGATE_1780_ISTANBUL/scripts/bake_tile_textures.py [vNNN]

Kullanıcı sırası (2026-09-26): … → "LOD ve doku bake".
Yöntem: gemideki malzemelerin UV'leri metre ölçeklidir (tahta genişliği, ek aralıkları metre cinsinden). Her prosedürel
malzeme TILE_M × TILE_M metrelik bir düzleme bake edilir; UE'de malzeme UV × (1 / TILE_M) ile döşenir.
Düzlemde iki UV haritası var: "UVMap" (metre; malzemenin okuduğu, active_render) ve "BakeUV" (0–1; bake hedefi).
ORM paketleme standardı: R = AO (düzlemde 1,0), G = Roughness, B = Metallic (Principled değeri). Normal: DirectX
için yeşil kanal ters çevrilir (_context/MODULAR_SHIP_STANDARD.md: "Unreal için DirectX normal").
Sınırlar: gürültü desenleri periyodik değildir → 4 m'de bir hafif dikiş olabilir. Gövdenin su hattı altı tonu
(dünya Z'sine bağlı) bake'e girmez; UE malzemesinde world-position ile verilir. Kurt figürü (normal yönlü renk)
bake edilmez. Sabit renkli Principled malzemeler (yaldız, demir siyah, boya) manifestte parametre olarak listelenir.
Çıktı: Textures/tiles/T_<Mat>_{BC,N,ORM}.png + reports/texture_manifest_<ver>.json
"""

import json
import sys
from pathlib import Path

import bpy  # noqa: I001
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SHIP = "OTTOMAN_FRIGATE_1780_ISTANBUL"
VER = next((a for a in sys.argv[1:] if a.startswith("v0")), "v026")
RES = 2048
TILE_M = 4.0
OUT = ROOT / "Textures" / "tiles"
SKIP = {"MAT_Figure_WolfGrey"}


def procedural(mat):
    if not mat.use_nodes:
        return False
    return any(n.type.startswith("TEX_") and n.type != "TEX_IMAGE" for n in mat.node_tree.nodes)


def principled_values(mat):
    b = next((n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None) if mat.use_nodes else None
    if b is None:
        return None
    col = b.inputs["Base Color"].default_value
    return {"base_color_linear": [round(c, 4) for c in col[:3]], "roughness": round(b.inputs["Roughness"].default_value, 3),
            "metallic": round(b.inputs["Metallic"].default_value, 3),
            "emission": [round(c, 3) for c in b.inputs["Emission Color"].default_value[:3]],
            "emission_strength": round(b.inputs["Emission Strength"].default_value, 3)}


def make_plane():
    me = bpy.data.meshes.new("_bake_plane")
    s = TILE_M
    me.from_pydata([(0, 0, 5), (s, 0, 5), (s, s, 5), (0, s, 5)], [], [(0, 1, 2, 3)])
    uv_m = me.uv_layers.new(name="UVMap")
    uv_b = me.uv_layers.new(name="BakeUV")
    for li, (u, v) in zip(range(4), ((0, 0), (1, 0), (1, 1), (0, 1))):
        uv_m.data[li].uv = (u * s, v * s)
        uv_b.data[li].uv = (u, v)
    uv_m.active_render = True
    me.uv_layers.active = uv_b
    ob = bpy.data.objects.new("_bake_plane", me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def bake_one(ob, mat, kind):
    img = bpy.data.images.new(f"_bake_{mat.name}_{kind}", RES, RES, alpha=False, float_buffer=(kind == "N"))
    if kind == "N":
        img.colorspace_settings.name = "Non-Color"
    nt = mat.node_tree
    tn = nt.nodes.new("ShaderNodeTexImage")
    tn.image = img
    for n in nt.nodes:
        n.select = False
    tn.select = True
    nt.nodes.active = tn
    sc = bpy.context.scene
    bs = sc.render.bake
    bs.margin = 4
    bs.use_selected_to_active = False
    if kind == "BC":
        bs.use_pass_direct = False
        bs.use_pass_indirect = False
        bs.use_pass_color = True
        bpy.ops.object.bake(type="DIFFUSE", pass_filter={"COLOR"}, uv_layer="BakeUV")
    elif kind == "R":
        bpy.ops.object.bake(type="ROUGHNESS", uv_layer="BakeUV")
    else:
        bs.normal_space = "TANGENT"
        bpy.ops.object.bake(type="NORMAL", uv_layer="BakeUV")
    arr = np.array(img.pixels[:], dtype=np.float32).reshape(RES, RES, 4)
    nt.nodes.remove(tn)
    bpy.data.images.remove(img)
    return arr


def save_png(arr, path, srgb):
    img = bpy.data.images.new("_save", RES, RES, alpha=False)
    img.colorspace_settings.name = "sRGB" if srgb else "Non-Color"
    img.pixels.foreach_set(arr.astype(np.float32).ravel())
    img.filepath_raw = str(path)
    img.file_format = "PNG"
    img.save()
    bpy.data.images.remove(img)


def main():
    bpy.ops.wm.open_mainfile(filepath=str(ROOT / "Blender" / "versions" / f"{SHIP}_{VER}.blend"))
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = 4
    used = set()
    for o in sc.objects:
        if o.type == "MESH" and not o.name.startswith(("UCX_", "CUT_")):
            for m in o.data.materials:
                if m:
                    used.add(m)
    ob = make_plane()
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = {"ship_id": SHIP, "version": VER, "tile_m": TILE_M, "resolution": RES,
                "ue_usage": f"UV × {1 / TILE_M:g} ile döşe; ORM: R=AO G=Roughness B=Metallic; Normal: DirectX (G ters)",
                "baked": {}, "constant": {}, "not_baked": {}}
    for mat in sorted(used, key=lambda m: m.name):
        if mat.name in SKIP:
            manifest["not_baked"][mat.name] = "renk yüzey normaline bağlı (figür); UE'de ayrı malzeme"
            continue
        if not procedural(mat):
            pv = principled_values(mat)
            img = next((n.image.filepath for n in mat.node_tree.nodes if n.type == "TEX_IMAGE" and n.image), None) if mat.use_nodes else None
            if img:
                manifest["constant"][mat.name] = {"image": img, **(pv or {})}
            else:
                manifest["constant"][mat.name] = pv
            continue
        ob.data.materials.clear()
        ob.data.materials.append(mat)
        bc = bake_one(ob, mat, "BC")
        rough = bake_one(ob, mat, "R")
        nrm = bake_one(ob, mat, "N")
        nrm[..., 1] = 1.0 - nrm[..., 1]                     # OpenGL → DirectX
        pv = principled_values(mat) or {"metallic": 0.0}
        orm = np.ones_like(bc)
        orm[..., 0] = 1.0
        orm[..., 1] = rough[..., 0]
        orm[..., 2] = pv["metallic"]
        base = mat.name.replace("MAT_", "T_")
        paths = {}
        for kind, arr, srgb in (("BC", bc, True), ("N", nrm, False), ("ORM", orm, False)):
            p = OUT / f"{base}_{kind}.png"
            save_png(arr, p, srgb)
            paths[kind] = str(p.relative_to(ROOT))
        manifest["baked"][mat.name] = {**paths, "metallic_const": pv["metallic"],
                                       "roughness_mean": round(float(rough[..., 0].mean()), 3)}
        print("BAKED", mat.name)
    mp = ROOT / "reports" / f"texture_manifest_{VER}.json"
    mp.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print("MANIFEST", mp, len(manifest["baked"]), len(manifest["constant"]))


if __name__ == "__main__":
    main()
