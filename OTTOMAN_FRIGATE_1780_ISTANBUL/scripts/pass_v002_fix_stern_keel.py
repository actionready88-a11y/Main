"""Pass v002 — kıç ve omurga bağlantı düzeltmesi (v001 üzerine, tüm gemi yeniden kurulmaz).

Çalıştırma (depo kökünden):
    python3 OTTOMAN_FRIGATE_1700_ISTANBUL/scripts/pass_v002_fix_stern_keel.py [--no-render]

Kullanıcı bulgusu (v001 ölçülü pafta):
  1. Kıçta su hattında dümen/kıç bodoslaması gövdeden kopuk görünüyor.
  2. Başta omurga ile bodoslama arasında açıklık var.
Kök neden: Subdivision gövde kabuğunun kıç ve baş kenarlarını ~0,3 m içeri çekiyordu
(crease yoktu); omurga bodoslamadan ~0,9 m önce bitiyordu.

Değişen nesneler (yalnız bunlar silinip yeniden üretilir):
  CORE_HULL_SHELL (kenar crease + ayna altı malzemesi), CORE_KEEL, CORE_STEM,
  CORE_STERNPOST, MOD_RUDDER_STERNPOST_A, UCX_CORE_HULL_SHELL_00..03.
Soket transformları değişmez.
"""

import importlib.util
import json
import sys
from pathlib import Path

import bpy

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("hull_v001", HERE / "build_hull_v001.py")
H = importlib.util.module_from_spec(spec)
spec.loader.exec_module(H)

SRC_VER, VER = "v001", "v002"
ROOT = H.ROOT
SHIP = H.SHIP_ID

MAT_NAMES = {
    "hull": "MAT_Hull_TarredOak", "band": "MAT_Hull_RedBand", "inner": "MAT_Bulwark_InnerRed",
    "deck": "MAT_Deck_Pine", "gold": "MAT_Trim_Gilt", "yellow": "MAT_Trim_YellowOchre",
    "timber": "MAT_Timber_Oak", "iron": "MAT_Iron_Black", "dark": "MAT_PortInterior",
}
REPLACE = ["CORE_HULL_SHELL", "CORE_KEEL", "CORE_STEM", "CORE_STERNPOST", "MOD_RUDDER_STERNPOST_A"]


def remove(name):
    ob = bpy.data.objects.get(name)
    if ob is None:
        return False
    me = ob.data
    bpy.data.objects.remove(ob, do_unlink=True)
    if me is not None and me.users == 0:
        bpy.data.meshes.remove(me)
    return True


def socket_snapshot():
    return {o.name: [round(v, 5) for v in (*o.location, *o.rotation_euler)]
            for o in bpy.data.objects if o.type == "EMPTY"}


def render_only():
    """Kaydedilmiş v002'yi açıp yalnız render setini üretir (geometriye dokunmaz)."""
    bpy.ops.wm.open_mainfile(filepath=str(ROOT / "Blender" / "versions" / f"{SHIP}_{VER}.blend"))
    H.VERSION = VER
    sc = bpy.context.scene
    H.setup_render(sc, fast=True)
    H.render_views(sc, ROOT / "renders" / VER)


def main():
    if "--render-only" in sys.argv:
        return render_only()
    src = ROOT / "Blender" / "versions" / f"{SHIP}_{SRC_VER}.blend"
    bpy.ops.wm.open_mainfile(filepath=str(src))
    sc = bpy.context.scene
    before_sockets = socket_snapshot()
    M = {k: bpy.data.materials[v] for k, v in MAT_NAMES.items() if v in bpy.data.materials}
    C = {c.name: c for c in bpy.data.collections}

    removed = [n for n in REPLACE if remove(n)]
    removed += [o.name for o in list(bpy.data.objects) if o.name.startswith("UCX_CORE_HULL_SHELL")]
    for n in [n for n in removed if n.startswith("UCX_")]:
        remove(n)

    hull = H.build_hull_shell(C["10_HULL_CORE"], M)
    mod = hull.modifiers.new("GunPorts", "BOOLEAN")
    mod.operation = "DIFFERENCE"
    mod.object = bpy.data.objects["CUT_GUNPORTS"]
    mod.solver = "EXACT"
    H.build_backbone(C["10_HULL_CORE"], M)
    H.build_rudder(C["24_MODULES_DECOR"], M)
    H.build_collision(C["40_COLLISION"], hull)

    after_sockets = socket_snapshot()
    moved = [n for n in before_sockets if before_sockets[n] != after_sockets.get(n)]

    out = ROOT / "Blender" / "versions" / f"{SHIP}_{VER}.blend"
    if out.exists():
        raise SystemExit(f"{out} zaten var; versiyonlu kayıt üzerine yazılmaz.")
    bpy.ops.wm.save_as_mainfile(filepath=str(out), compress=True)

    H.VERSION = VER
    audit_path = ROOT / "reports" / f"scene_audit_{VER}.json"
    rep = H.audit(sc, audit_path)
    rep["pass"] = {
        "name": "pass_v002_fix_stern_keel",
        "source": f"Blender/versions/{SHIP}_{SRC_VER}.blend",
        "pass_changes": {"replaced": REPLACE, "regenerated_collision": sorted(n for n in removed if n.startswith("UCX_")),
                         "unchanged": "diğer tüm nesneler v001'den aynen"},
        "reason": "kıç/dümen kopukluğu ve baş omurga açıklığı (kullanıcı bulgusu)",
        "sockets_moved": moved,
    }
    audit_path.write_text(json.dumps(rep, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(rep["checks"]["bounds_m"]), "tris", rep["checks"]["render_tris_total"], "sockets_moved", moved)

    if "--no-render" not in sys.argv:
        H.setup_render(sc, fast=True)
        H.render_views(sc, ROOT / "renders" / VER)


if __name__ == "__main__":
    main()
