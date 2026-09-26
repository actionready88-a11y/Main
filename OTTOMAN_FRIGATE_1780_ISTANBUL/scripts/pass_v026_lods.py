"""Pass v026 — LOD zinciri, v025 üzerine.

Çalıştırma (depo kökünden):
    python3 OTTOMAN_FRIGATE_1780_ISTANBUL/scripts/pass_v026_lods.py

Kullanıcı sırası (2026-09-26): … ambar içi → "LOD ve doku bake".
_context/MODULAR_SHIP_STANDARD.md: Hull LOD0 %100, LOD1 ~%50, LOD2 ~%20, LOD3 ~%8; büyük modüller %100/%50/%20;
her LOD aynı origin, bounds ve socket uzayını korur.
Yöntem: her benzersiz render mesh'i için modifier yığını uygulanmış kopya (LOD0 ile aynı biçim) → Decimate (collapse)
ile LOD1/LOD2 (gövde kabuğu için LOD3). Paylaşılan mesh'ler (top, kapak, fener, sandalye…) bir kez üretilir.
LOD'lar 50_LODS koleksiyonunda, gizli; ad kuralı `<Kaynak>_LOD<n>`; `lod_of`, `lod_ratio` özellikleri.
2.000 üçgenin altındaki mesh'ler için LOD üretilmez (UE otomatik ekran boyutu eşikleri yeterli).
"""

import importlib.util
import json
from pathlib import Path

import bpy  # noqa: I001

HERE = Path(__file__).resolve().parent
_sp = importlib.util.spec_from_file_location("hull_v001", HERE / "build_hull_v001.py")
H = importlib.util.module_from_spec(_sp)
_sp.loader.exec_module(H)
SRC_VER, VER = "v025", "v026"
ROOT, SHIP = H.ROOT, H.SHIP_ID
MIN_TRIS = 2000
RATIOS = {"default": (0.5, 0.2), "CORE_HULL_SHELL": (0.5, 0.2, 0.08)}


def tris_of(me):
    me.calc_loop_triangles()
    return len(me.loop_triangles)


def build_lods(sc):
    """Sahnedeki render mesh'leri için LOD kopyaları üretir (50_LODS); rapor listesi döndürür."""
    lods = bpy.data.collections["50_LODS"]
    dg = bpy.context.evaluated_depsgraph_get()
    done_data, report = {}, []
    srcs = [o for o in sc.objects if o.type == "MESH" and not o.name.startswith(("UCX_", "CUT_")) and not o.name.endswith(tuple(f"_LOD{i}" for i in range(4)))]
    for o in sorted(srcs, key=lambda o: o.name):
        key = o.data.name if o.data.users > 1 else o.name
        if key in done_data:
            continue
        ev = o.evaluated_get(dg)
        base = bpy.data.meshes.new_from_object(ev)
        t0 = tris_of(base)
        if t0 < MIN_TRIS:
            bpy.data.meshes.remove(base)
            done_data[key] = None
            continue
        shared = o.data.users > 1
        ratios = RATIOS.get(o.name, RATIOS["default"])
        entry = {"source": key, "shared_mesh": shared, "lod0_tris": t0, "lods": []}
        for i, r in enumerate(ratios, 1):
            me = base.copy()
            me.name = f"{key}_LOD{i}"
            tmp = bpy.data.objects.new(f"{key}_LOD{i}", me)
            lods.objects.link(tmp)
            dec = tmp.modifiers.new("Decimate", "DECIMATE")
            dec.decimate_type = "COLLAPSE"
            dec.ratio = r
            dec.use_collapse_triangulate = False
            dg2 = bpy.context.evaluated_depsgraph_get()
            final = bpy.data.meshes.new_from_object(tmp.evaluated_get(dg2))
            tmp.modifiers.clear()
            old = tmp.data
            tmp.data = final
            final.name = f"{key}_LOD{i}"
            bpy.data.meshes.remove(old)
            if not shared:
                tmp.matrix_world = o.matrix_world.copy()
            tmp["lod_of"] = key
            tmp["lod_index"] = i
            tmp["lod_ratio"] = r
            tmp.hide_viewport = True
            tmp.hide_render = True
            entry["lods"].append({"name": tmp.name, "tris": tris_of(final)})
        bpy.data.meshes.remove(base)
        done_data[key] = entry
        report.append(entry)
    return report


def main():
    out = ROOT / "Blender" / "versions" / f"{SHIP}_{VER}.blend"
    if out.exists():
        raise SystemExit(f"{out} zaten var; versiyonlu kayıt üzerine yazılmaz.")
    bpy.ops.wm.open_mainfile(filepath=str(ROOT / "Blender" / "versions" / f"{SHIP}_{SRC_VER}.blend"))
    sc = bpy.context.scene
    report = build_lods(sc)
    bpy.ops.wm.save_as_mainfile(filepath=str(out), compress=True)
    H.VERSION = VER
    ap = ROOT / "reports" / f"scene_audit_{VER}.json"
    rep = H.audit(sc, ap)
    lod0 = sum(e["lod0_tris"] for e in report)
    rep["lods_v026"] = {"sources_with_lods": len(report), "min_tris": MIN_TRIS, "ratios": RATIOS,
                        "sum_lod0_tris_unique": lod0,
                        "sum_lod1_tris_unique": sum(e["lods"][0]["tris"] for e in report),
                        "sum_lod2_tris_unique": sum(e["lods"][1]["tris"] for e in report),
                        "entries": report,
                        "note": "toplamlar benzersiz mesh üzerinden (paylaşılan top/kapak vb. bir kez sayılır)"}
    rep["pass"] = {"name": "pass_v026_lods", "source": f"Blender/versions/{SHIP}_{SRC_VER}.blend", "geometry_changed": False}
    ap.write_text(json.dumps(rep, indent=2, ensure_ascii=False), encoding="utf-8")
    r = rep["lods_v026"]
    print("V026", r["sources_with_lods"], r["sum_lod0_tris_unique"], r["sum_lod1_tris_unique"], r["sum_lod2_tris_unique"])
    print([(e["source"], e["lod0_tris"], [l["tris"] for l in e["lods"]]) for e in sorted(report, key=lambda e: -e["lod0_tris"])[:8]])


if __name__ == "__main__":
    main()
