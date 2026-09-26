"""v032 — v031 renderlarından iki düzeltme:
 1. Gövde rumi frizi kesintisiz: v031'de zincir levhası/savlo/bigot önündeki sütunlar atlanıyor, frizde koyu boşluklar
    kalıyordu → yalnız lumbar çerçevesi ve top arkasında kesilir.
 2. Kıç arması aynalanmıştı (arkadan bakınca sancak solda): hilal-yıldız bayraktaki gibi — yıldız hilalin açık tarafında.
v031 betiği değiştirilmez; düzeltmeler kaynak yamasıyla uygulanır.

    python3.11 OTTOMAN_FRIGATE_1780_ISTANBUL/scripts/pass_v032_frieze_continuous.py
"""

import importlib.util
import json
from pathlib import Path

import bpy

HERE = Path(__file__).resolve().parent
sp = importlib.util.spec_from_file_location("pass_v031", HERE / "pass_v031_ottoman_ornaments.py")
P31 = importlib.util.module_from_spec(sp)
sp.loader.exec_module(P31)
ROOT, SHIP = P31.ROOT, P31.SHIP


def patch_source(mod, fname, repl):
    import inspect
    src = inspect.getsource(getattr(mod, fname))
    for a, b in repl:
        assert a in src, (fname, a)
        src = src.replace(a, b)
    exec(compile(src, mod.__file__, "exec"), mod.__dict__)


patch_source(P31, "hull_frieze", [(
    """            if ok and ob.name == "CORE_HULL_SHELL":
                keep[x] = (zb, zt)""",
    """            if not (ok and ob.name.startswith(("CORE_GUNPORT_FRAMES", "MOD_CANNON_"))):
                keep[x] = (zb, zt)""")])
patch_source(P31, "stern_crest", [("    U, Vv, N = V((0, 1, 0)), V((0, 0, 1)), V((-1, 0, 0))",
                                   "    U, Vv, N = V((0, -1, 0)), V((0, 0, 1)), V((-1, 0, 0))   # arkadan bakana göre")])
SRC_VER, VER = "v031", "v032"


def main():
    out = ROOT / "Blender" / "versions" / f"{SHIP}_{VER}.blend"
    if out.exists():
        raise SystemExit(f"{out} zaten var; versiyonlu kayıt üzerine yazılmaz.")
    bpy.ops.wm.open_mainfile(filepath=str(ROOT / "Blender" / "versions" / f"{SHIP}_{SRC_VER}.blend"))
    sc = bpy.context.scene
    col = bpy.data.collections[P31.COL]
    M = P31.mats()
    for tag in ("S", "P"):                       # eski frizin LOD'ları
        for o in [o for o in bpy.data.objects if o.name.startswith(f"MOD_ORN_FRIEZE_HULL_{tag}_LOD")]:
            bpy.data.objects.remove(o, do_unlink=True)
    obs, rep = P31.hull_frieze(M, col)
    old = bpy.data.objects.get("MOD_ORN_STERN_CREST")
    for o in [o for o in bpy.data.objects if o.name.startswith("MOD_ORN_STERN_CREST_LOD")]:
        bpy.data.objects.remove(o, do_unlink=True)
    crest = P31.stern_crest(M, col)
    obs.append(crest)
    P31.switch([bpy.data.objects[o.name] for o in obs] + [o for o in col.objects if not o.name.startswith("MOD_ORN_FRIEZE_HULL")])
    P31.LODS.build_lods(sc, only={o.name for o in obs})
    bpy.ops.wm.save_as_mainfile(filepath=str(out), compress=True)
    P31.H.VERSION = VER
    ap = ROOT / "reports" / f"scene_audit_{VER}.json"
    arep = P31.H.audit(sc, ap)
    arep["frieze_v032"] = rep
    arep["pass"] = {"name": "pass_v032_frieze_continuous", "source": f"Blender/versions/{SHIP}_{SRC_VER}.blend"}
    ap.write_text(json.dumps(arep, indent=2, ensure_ascii=False), encoding="utf-8")
    qa = P31.QA.audit(sc, top=60)
    (ROOT / "reports" / f"kalite_testi_{VER}.json").write_text(json.dumps(qa, indent=1, ensure_ascii=False), encoding="utf-8")
    print("V032", json.dumps(rep), json.dumps(qa["summary"], ensure_ascii=False))


if __name__ == "__main__":
    main()
