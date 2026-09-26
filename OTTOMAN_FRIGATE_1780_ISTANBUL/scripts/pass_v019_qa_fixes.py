"""Pass v019 — Kalite denetimi düzeltmeleri, v018 üzerine (geometri değişmez).

Çalıştırma (depo kökünden):
    python3 OTTOMAN_FRIGATE_1780_ISTANBUL/scripts/pass_v019_qa_fixes.py

Denetimde bulunanlar (v018):
  1. UCX_MOD_BOAT_CUTTER_A_00: 294 köşe (proje sınırı 64) → filika kabuğundan seyreltilmiş örneklerle yeniden kuruldu.
  2. Tırmanma UCX'leri (v015) rota adıyla adlandırılmıştı (UCX_MAIN_S_LOWER_00 …); UE'nin UCX_<RenderMesh>_NN
     kuralına uymuyordu → UCX_MOD_RIG_STANDING_{MAST}_A_NN, rota adı `climb_route` özelliğinde.
Sonra tüm UCX'ler için köşe sınırı, sahip mesh varlığı ve ad kuralı yeniden denetlenir.
"""

import importlib.util
import json
from pathlib import Path

import bpy  # noqa: I001
from mathutils import Vector

HERE = Path(__file__).resolve().parent


def _load(name, fname):
    sp = importlib.util.spec_from_file_location(name, HERE / fname)
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


P13 = _load("pass_v013", "pass_v013_hull_b_lower_deck.py")
H, C3 = P13.H, P13.C3
SRC_VER, VER = "v018", "v019"
ROOT, SHIP = H.ROOT, H.SHIP_ID
MAX_VERTS = 64


def main():
    out = ROOT / "Blender" / "versions" / f"{SHIP}_{VER}.blend"
    if out.exists():
        raise SystemExit(f"{out} zaten var; versiyonlu kayıt üzerine yazılmaz.")
    bpy.ops.wm.open_mainfile(filepath=str(ROOT / "Blender" / "versions" / f"{SHIP}_{SRC_VER}.blend"))
    sc = bpy.context.scene
    col = bpy.data.collections["40_COLLISION"]
    changes = []
    # 1) filika UCX
    old = bpy.data.objects["UCX_MOD_BOAT_CUTTER_A_00"]
    n_old = len(old.data.vertices)
    boat = bpy.data.objects["MOD_BOAT_CUTTER_A"]
    pts = [boat.matrix_world @ v.co for v in boat.data.vertices]
    xs = sorted(p.x for p in pts)
    x0, x1 = xs[0], xs[-1]
    sample = []
    for k in range(7):
        a = x0 + (x1 - x0) * k / 6
        sl = [p for p in pts if abs(p.x - a) < (x1 - x0) / 12]
        if not sl:
            continue
        for key in (lambda p: p.y, lambda p: -p.y, lambda p: p.z, lambda p: -p.z):
            sample.append(max(sl, key=key))
        sample.append(max(sl, key=lambda p: p.z + abs(p.y)))
        sample.append(max(sl, key=lambda p: p.z - abs(p.y)) if False else min(sl, key=lambda p: p.z - abs(p.y)))
    me_old = old.data
    bpy.data.objects.remove(old, do_unlink=True)
    bpy.data.meshes.remove(me_old)
    u = C3.convex("UCX_MOD_BOAT_CUTTER_A_00", sample, col, "boat")
    u.name = u.data.name = "UCX_MOD_BOAT_CUTTER_A_00"
    u["owner_mesh"] = "MOD_BOAT_CUTTER_A"
    changes.append({"ucx": u.name, "verts_before": n_old, "verts_after": len(u.data.vertices)})
    # 2) tırmanma UCX adları
    climb = sorted([o for o in col.objects if o.get("ucx_purpose") == "climb_shrouds"], key=lambda o: o.name)
    counts = {}
    for o in climb:
        route = o["owner_mesh"]
        mast = route.split("_")[0]
        owner = f"MOD_RIG_STANDING_{mast}_A"
        o["climb_route"] = route
        o["owner_mesh"] = owner
        o.name = f"_tmp_{o.name}"
    for o in climb:
        owner = o["owner_mesh"]
        taken = {x.name for x in col.objects if x.name.startswith(f"UCX_{owner}_")}
        i = counts.get(owner, len(taken))
        while f"UCX_{owner}_{i:02d}" in taken:
            i += 1
        counts[owner] = i + 1
        new = f"UCX_{owner}_{i:02d}"
        changes.append({"ucx_renamed": o.name[len("_tmp_"):], "to": new, "climb_route": o["climb_route"]})
        o.name = o.data.name = new
    # 3) denetim
    ucx = [o for o in bpy.data.objects if o.name.startswith("UCX_")]
    over = [(o.name, len(o.data.vertices)) for o in ucx if len(o.data.vertices) > MAX_VERTS]
    no_owner = [o.name for o in ucx if o.get("owner_mesh") and o["owner_mesh"] not in bpy.data.objects]
    bad_name = [o.name for o in ucx if o.get("owner_mesh") and not o.name.startswith(f"UCX_{o['owner_mesh']}_")
                and not o.name.startswith("UCX_CORE_HULL_SHELL_")]
    bpy.ops.wm.save_as_mainfile(filepath=str(out), compress=True)
    H.VERSION = VER
    ap = ROOT / "reports" / f"scene_audit_{VER}.json"
    rep = H.audit(sc, ap)
    rep["qa_v019"] = {"changes": changes, "ucx_total": len(ucx), "ucx_over_limit": over, "ucx_owner_missing": no_owner,
                      "ucx_bad_name": bad_name, "max_verts": max(len(o.data.vertices) for o in ucx)}
    rep["pass"] = {"name": "pass_v019_qa_fixes", "source": f"Blender/versions/{SHIP}_{SRC_VER}.blend",
                   "geometry_changed": False, "pass_changes": {"ucx_rebuilt": 1, "ucx_renamed": len(climb)}}
    ap.write_text(json.dumps(rep, indent=2, ensure_ascii=False), encoding="utf-8")
    print("QA", json.dumps({k: v for k, v in rep["qa_v019"].items() if k != "changes"}, ensure_ascii=False), changes[0])


if __name__ == "__main__":
    main()
