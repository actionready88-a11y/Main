"""Tersane — LOD'ları ana blend'den ayrı dosyada saklama (GitHub 100 MB dosya sınırı).

v043'te ana blend 99,5 MB oldu; bunun ≈ 55 MB'ı `50_LODS` koleksiyonundaki türetilmiş LOD mesh'leriydi.
v044'ten itibaren her sürüm iki dosya yazar:
    <SHIP>_vNNN.blend       → sahne (LOD0 + çarpışma + soketler), LOD'suz
    <SHIP>_vNNN_LOD.blend   → yalnız `50_LODS` koleksiyonu (LOD1..n); UE dışa aktarımında ana dosyaya eklenir (Append)

Pass zinciri:
    bpy.ops.wm.open_mainfile(<önceki ana blend>)
    lod_store.load(<önceki ana blend yolu>)        # önceki LOD dosyası varsa 50_LODS'u geri ekler
    ... yeni modüller, LODS.build_lods(only=yeni) ...
    lod_store.save_split(<yeni ana blend yolu>)    # LOD dosyasını yazar, ana dosyayı LOD'suz kaydeder
"""

from pathlib import Path

import bpy

COL = "50_LODS"


def lod_path(main_path):
    p = Path(main_path)
    return p.with_name(p.stem + "_LOD.blend")


def load(prev_main_path, col_name=COL):
    """Önceki sürümün LOD dosyasını sahneye ekler. Koleksiyon zaten doluysa (eski tek dosya düzeni) dokunmaz."""
    col = bpy.data.collections.get(col_name)
    if col is not None and len(col.all_objects) > 0:
        return {"source": "main_blend", "objects": len(col.all_objects)}
    lp = lod_path(prev_main_path)
    if not lp.exists():
        return {"source": None, "objects": 0}
    if col is not None:
        bpy.data.collections.remove(col)
    with bpy.data.libraries.load(str(lp), link=False) as (src, dst):
        dst.collections = [c for c in src.collections if c == col_name]
    col = bpy.data.collections.get(col_name)
    if col is None:
        return {"source": str(lp.name), "objects": 0}
    sc = bpy.context.scene
    if col.name not in sc.collection.children:
        sc.collection.children.link(col)
    return {"source": lp.name, "objects": len(col.all_objects)}


def make_relative(main_path):
    """Doku yollarını blend'e göre göreli yapar (//../../Textures/...). Mutlak bulut yolu (/home/user/...) kullanıcının
    bilgisayarında bulunmaz → Blender'da pembe malzeme. Kaydetmeden önce çağrılır."""
    base = Path(main_path).parent
    n = 0
    for im in bpy.data.images:
        if im.source not in {"FILE", "SEQUENCE", "TILED"} or not im.filepath or im.filepath.startswith("//") or im.packed_file:
            continue
        try:
            im.filepath = bpy.path.relpath(bpy.path.abspath(im.filepath), start=str(base))
            n += 1
        except ValueError:
            pass
    return n


def save_split(main_path, col_name=COL):
    """50_LODS'u <main>_LOD.blend'e yazar, sahneden çıkarır, ana dosyayı kaydeder. Sahnede LOD kalmaz."""
    main_path = Path(main_path)
    lp = lod_path(main_path)
    if main_path.exists() or lp.exists():
        raise SystemExit(f"{main_path.name} / {lp.name} zaten var; versiyonlu kayıt üzerine yazılmaz.")
    make_relative(main_path)
    col = bpy.data.collections.get(col_name)
    n = 0
    if col is not None and len(col.all_objects) > 0:
        bpy.data.libraries.write(str(lp), {col}, path_remap="RELATIVE_ALL", compress=True)
        meshes = set()
        for o in list(col.all_objects):
            if o.data is not None:
                meshes.add(o.data)
            bpy.data.objects.remove(o, do_unlink=True)
            n += 1
        for me in meshes:
            if me.users == 0:
                bpy.data.meshes.remove(me)
        bpy.data.collections.remove(col)
    bpy.ops.wm.save_as_mainfile(filepath=str(main_path), compress=True, relative_remap=True)
    return {"lod_file": lp.name if n else None, "lod_objects": n,
            "main_mb": round(main_path.stat().st_size / 1e6, 1),
            "lod_mb": round(lp.stat().st_size / 1e6, 1) if n else 0.0}
