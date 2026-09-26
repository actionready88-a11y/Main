"""Tersane — LOD zinciri üretici (UE için).

    import lods
    rapor = lods.build_lods(bpy.context.scene, min_tris=2000, ratios={"default": (0.5, 0.2), "CORE_HULL_SHELL": (0.5, 0.2, 0.08)})

Kural (MODULAR_SHIP_STANDARD): gövde %100/%50/%20/%8, büyük modüller %100/%50/%20; aynı orijin/bounds/soket uzayı.
Yöntem: modifier yığını uygulanmış kopya → Decimate (collapse). Paylaşılan mesh'ler bir kez (orijinde) üretilir.
Çıktı: `50_LODS` koleksiyonunda gizli `<Kaynak>_LOD<n>` nesneleri. Geometri değişince önce eski LOD'ları sil
(`clear_lods()`), sonra yeniden üret.
"""

import bpy


def _tris(me):
    me.calc_loop_triangles()
    return len(me.loop_triangles)


def clear_lods(col_name="50_LODS"):
    col = bpy.data.collections.get(col_name)
    if not col:
        return 0
    n = 0
    for o in list(col.objects):
        me = o.data
        bpy.data.objects.remove(o, do_unlink=True)
        if me is not None and me.users == 0:
            bpy.data.meshes.remove(me)
        n += 1
    return n


def build_lods(sc, min_tris=2000, ratios=None, col_name="50_LODS"):
    ratios = ratios or {"default": (0.5, 0.2), "CORE_HULL_SHELL": (0.5, 0.2, 0.08)}
    col = bpy.data.collections.get(col_name) or bpy.data.collections.new(col_name)
    if col.name not in sc.collection.children:
        try:
            sc.collection.children.link(col)
        except RuntimeError:
            pass
    dg = bpy.context.evaluated_depsgraph_get()
    done, report = set(), []
    srcs = [o for o in sc.objects if o.type == "MESH" and not o.name.startswith(("UCX_", "CUT_")) and "_LOD" not in o.name]
    for o in sorted(srcs, key=lambda o: o.name):
        shared = o.data.users > 1
        key = o.data.name if shared else o.name
        if key in done:
            continue
        done.add(key)
        base = bpy.data.meshes.new_from_object(o.evaluated_get(dg))
        t0 = _tris(base)
        if t0 < min_tris:
            bpy.data.meshes.remove(base)
            continue
        entry = {"source": key, "shared_mesh": shared, "lod0_tris": t0, "lods": []}
        for i, r in enumerate(ratios.get(o.name, ratios["default"]), 1):
            tmp = bpy.data.objects.new(f"{key}_LOD{i}", base.copy())
            col.objects.link(tmp)
            dec = tmp.modifiers.new("Decimate", "DECIMATE")
            dec.decimate_type = "COLLAPSE"
            dec.ratio = r
            final = bpy.data.meshes.new_from_object(tmp.evaluated_get(bpy.context.evaluated_depsgraph_get()))
            tmp.modifiers.clear()
            old = tmp.data
            tmp.data = final
            final.name = tmp.name
            bpy.data.meshes.remove(old)
            if not shared:
                tmp.matrix_world = o.matrix_world.copy()
            tmp["lod_of"], tmp["lod_index"], tmp["lod_ratio"] = key, i, r
            tmp.hide_viewport = tmp.hide_render = True
            entry["lods"].append({"name": tmp.name, "tris": _tris(final)})
        bpy.data.meshes.remove(base)
        report.append(entry)
    return report
