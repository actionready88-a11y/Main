"""Pass v004 — oynanış soketleri (v003 üzerine; geometri değişmez).

Çalıştırma (depo kökünden):
    python3 OTTOMAN_FRIGATE_1780_ISTANBUL/scripts/pass_v004_gameplay_sockets.py [--no-render]

Kullanıcı kararları (2026-09-25):
  - Toplar mürettebatla doldurulur/ateşlenir; emir: oyuncu → 2. kaptan → topçu subayı.
  - Baş kovalama: 2 lumbar kalır; pruvaya ayrıca çarpma mahmuzu (ram) gelecek.
Eklenenler:
  - SOCKET_RAM (pruva, su hattı; oynanış modülü, tarihsel değil)
  - SOCKET_HELM (dümen dolabı yeri, kıç kasarası)
  - SOCK_STATION_CAPTAIN / SECOND_CAPTAIN / GUNNERY_OFFICER
  - Her top soketine 4 mürettebat noktası: SOCK_CREW_<top>_A..D
    (A nişancı/gun captain, B doldurucu, C tokmakçı-süngerci, D manivela). Kişi sayısı oyun parametresi.
  - Top soketlerine özel özellikler: battery_group, slot, mount_id (ada bağlı kararlı UUID5)
Düzeltme (manifest sürümü artar):
  - v001-v003'te borda top soketleri ters yöne bakıyordu (+X gemi içine). Standart +Y = sancak:
    sancak topları +Y'ye (Rz +90°), iskele topları -Y'ye (Rz -90°) bakacak şekilde düzeltildi.
"""

import importlib.util
import json
import math
import sys
import uuid
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("hull_v001", HERE / "build_hull_v001.py")
H = importlib.util.module_from_spec(spec)
spec.loader.exec_module(H)

SRC_VER, VER = "v003", "v004"
ROOT, SHIP = H.ROOT, H.SHIP_ID
MANIFEST_VERSION = 2  # v001-v003 = 1; top soketi yön düzeltmesi ile 2
NS_UUID = uuid.UUID("6f1c7c1e-2b0a-4b8e-9a51-0d2f6b7e1780")

# Top yerel eksenleri: +X namlu yönü, +Y namlunun solu, Z yukarı.
CREW = {  # rol: (x, y) metre, top pivotuna göre
    "A": ("gun_captain", (-1.9, 0.0)),
    "B": ("loader", (0.1, 0.95)),
    "C": ("rammer_sponger", (0.1, -0.95)),
    "D": ("handspike", (-1.0, 0.95)),
}


def empty(name, loc, col, rot=(0, 0, 0), shape="PLAIN_AXES", size=0.25):
    e = bpy.data.objects.new(name, None)
    e.empty_display_type = shape
    e.empty_display_size = size
    e.location = loc
    e.rotation_euler = rot
    col.objects.link(e)
    return e


def battery_group(name):
    if "CHASE_BOW" in name:
        return "CHASE_BOW"
    if "CHASE_STERN" in name:
        return "CHASE_STERN"
    side = "STARBOARD" if "_S_" in name else "PORT"
    return f"{side}_{'QD' if '_QD_' in name else 'MAIN'}"


def main():
    bpy.ops.wm.open_mainfile(filepath=str(ROOT / "Blender" / "versions" / f"{SHIP}_{SRC_VER}.blend"))
    sc = bpy.context.scene
    col = bpy.data.collections["30_SOCKETS"]
    fixed, added = [], []

    names = sorted(o.name for o in bpy.data.objects if o.type == "EMPTY" and o.name.startswith("SOCKET_CANNON_"))
    guns = [bpy.data.objects[n] for n in names]
    for g in guns:
        n = g.name
        if n.startswith(("SOCKET_CANNON_S_", "SOCKET_CANNON_P_")):
            want = math.radians(90) if n.startswith("SOCKET_CANNON_S_") else math.radians(-90)
            if abs(g.rotation_euler.z - want) > 1e-4:
                fixed.append({"socket": n, "old_rz_deg": round(math.degrees(g.rotation_euler.z), 2),
                              "new_rz_deg": round(math.degrees(want), 2)})
                g.rotation_euler.z = want
        g["battery_group"] = battery_group(n)
        g["slot"] = "SLOT_" + n[len("SOCKET_"):]
        g["mount_id"] = str(uuid.uuid5(NS_UUID, n))
        g["manifest_version"] = MANIFEST_VERSION
    bpy.context.view_layer.update()

    # mürettebat noktaları
    for g in guns:
        tag = g.name[len("SOCKET_CANNON_"):]
        mw = g.matrix_world.copy()
        for key, (role, (lx, ly)) in CREW.items():
            p = mw @ Vector((lx, ly, 0.0))
            e = empty(f"SOCK_CREW_{tag}_{key}", p, col, rot=g.rotation_euler.copy(), shape="SINGLE_ARROW", size=0.35)
            e["crew_role"] = role
            e["gun_socket"] = g.name
            e["battery_group"] = g["battery_group"]
            added.append(e.name)

    # ram, dümen, komuta istasyonları
    zr = -0.35
    e = empty("SOCKET_RAM", (H.bow_x(zr) + 0.05, 0.0, zr), col, shape="ARROWS", size=0.8)
    e["module_family"] = "MOD_RAM"
    e["note"] = "oynanış modülü; 18. yy frigate'inde tarihsel değil"
    e["mount_id"] = str(uuid.uuid5(NS_UUID, "SOCKET_RAM"))
    added.append(e.name)

    def on_deck(s, y, deck="gun"):
        z = H.deck_z(s) + (H.QD_H if deck == "qd" else 0.0) + 0.10
        x, _ = H.hull_point(s, z)
        return Vector((x, y, z))

    for name, s, y, deck, role in (
        ("SOCKET_HELM", 0.20, 0.0, "qd", "helm"),
        ("SOCK_STATION_CAPTAIN", 0.15, 0.0, "qd", "captain"),
        ("SOCK_STATION_SECOND_CAPTAIN", 0.31, -1.8, "qd", "second_captain"),
        ("SOCK_STATION_GUNNERY_OFFICER", 0.52, 0.0, "gun", "gunnery_officer"),
    ):
        e = empty(name, on_deck(s, y, deck), col, rot=(0, 0, 0), shape="SINGLE_ARROW", size=0.6)
        e["station_role"] = role
        e["command_chain"] = ["player", "second_captain", "gunnery_officer"] if role != "helm" else []
        e["mount_id"] = str(uuid.uuid5(NS_UUID, name))
        added.append(e.name)

    out = ROOT / "Blender" / "versions" / f"{SHIP}_{VER}.blend"
    if out.exists():
        raise SystemExit(f"{out} zaten var; versiyonlu kayıt üzerine yazılmaz.")
    bpy.ops.wm.save_as_mainfile(filepath=str(out), compress=True)

    H.VERSION = VER
    ap = ROOT / "reports" / f"scene_audit_{VER}.json"
    rep = H.audit(sc, ap)
    # kontrol: mürettebat noktaları güverte içinde mi (orta hattan uzaklık < iç yarı en)
    outside = []
    for n in added:
        if not n.startswith("SOCK_CREW_"):
            continue
        o = bpy.data.objects[n]
        s = max(0.0, min(1.0, (o.location.x - H.stern_x(o.location.z)) / (H.bow_x(o.location.z) - H.stern_x(o.location.z))))
        _, y = H.hull_point(s, o.location.z)
        if abs(o.location.y) > y - 0.35:
            outside.append(n)
    rep["gameplay_sockets"] = {
        "manifest_version": MANIFEST_VERSION,
        "guns": len(guns), "crew_points": sum(1 for n in added if n.startswith("SOCK_CREW_")),
        "stations": [n for n in added if n.startswith(("SOCK_STATION_", "SOCKET_HELM"))],
        "ram": "SOCKET_RAM",
        "battery_groups": {g: sum(1 for x in guns if x["battery_group"] == g) for g in sorted({x["battery_group"] for x in guns})},
        "crew_points_outside_deck": outside,
        "cannon_rotation_fix": fixed,
    }
    rep["pass"] = {"name": "pass_v004_gameplay_sockets", "source": f"Blender/versions/{SHIP}_{SRC_VER}.blend",
                   "pass_changes": {"added_sockets": len(added), "rotated_sockets": len(fixed)},
                   "geometry_changed": False}
    ap.write_text(json.dumps(rep, indent=2, ensure_ascii=False), encoding="utf-8")
    gs = rep["gameplay_sockets"]
    print("guns", gs["guns"], "crew", gs["crew_points"], "groups", gs["battery_groups"],
          "fixed", len(fixed), "outside", outside)

    if "--no-render" not in sys.argv:
        render_socket_preview(sc)


def render_socket_preview(sc):
    """Soketleri renkli işaretlerle gösteren önizleme (yalnız render; .blend'e kaydedilmez)."""
    import bmesh
    palette = {"crew": (0.2, 0.9, 0.3), "station": (1.0, 0.85, 0.1), "ram": (1.0, 0.15, 0.1), "gun": (0.2, 0.55, 1.0)}
    mats = {}
    for k, c in palette.items():
        m = bpy.data.materials.new(f"PREVIEW_{k}")
        m.use_nodes = True
        b = m.node_tree.nodes["Principled BSDF"]
        b.inputs["Base Color"].default_value = (*c, 1)
        b.inputs["Emission Color"].default_value = (*c, 1)
        b.inputs["Emission Strength"].default_value = 2.0
        mats[k] = m
    prev = bpy.data.collections.new("PREVIEW_MARKERS")
    sc.collection.children.link(prev)

    def marker(o, kind, r):
        bm = bmesh.new()
        if kind == "gun":  # namlu yönünü gösteren ok: silindir + koni
            bmesh.ops.create_cone(bm, cap_ends=True, segments=10, radius1=0.12, radius2=0.12, depth=1.2,
                                  matrix=Matrix.Translation((0.6, 0, 0.3)) @ Matrix.Rotation(math.radians(90), 4, "Y"))
            bmesh.ops.create_cone(bm, cap_ends=True, segments=10, radius1=0.28, radius2=0.0, depth=0.5,
                                  matrix=Matrix.Translation((1.4, 0, 0.3)) @ Matrix.Rotation(math.radians(90), 4, "Y"))
        else:
            bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=r,
                                      matrix=Matrix.Translation((0, 0, r)))
        me = bpy.data.meshes.new(f"MK_{o.name}")
        bm.to_mesh(me)
        bm.free()
        me.materials.append(mats[kind])
        ob = bpy.data.objects.new(f"MK_{o.name}", me)
        ob.matrix_world = o.matrix_world.copy()
        prev.objects.link(ob)

    for o in list(sc.objects):
        if o.type != "EMPTY":
            continue
        if o.name.startswith("SOCK_CREW_"):
            marker(o, "crew", 0.18)
        elif o.name.startswith(("SOCK_STATION_", "SOCKET_HELM")):
            marker(o, "station", 0.35)
        elif o.name == "SOCKET_RAM":
            marker(o, "ram", 0.45)
        elif o.name.startswith("SOCKET_CANNON_"):
            marker(o, "gun", 0)
    for name in ("CORE_DECK_QUARTER", "CORE_DECK_FORECASTLE", "CORE_BREAST_RAIL_QD", "CORE_BREAST_RAIL_FC"):
        ob = bpy.data.objects.get(name)
        if ob:
            ob.hide_render = True  # kasara güvertelerini gizle ki alttaki batarya görünsün
    H.setup_render(sc, fast=True)
    out = ROOT / "renders" / VER
    out.mkdir(parents=True, exist_ok=True)
    for name, loc, tgt, lens in (("soketler_ust", (0.5, 0.01, 48), (0.5, 0, 1.5), 32),
                                 ("soketler_3_4", (24, 20, 18), (-2, 0, 2.0), 30)):
        sc.camera = H.camera(sc, f"CAM_{name}", loc, tgt, lens=lens)
        sc.render.filepath = str(out / f"{SHIP}_{VER}_{name}.png")
        bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    main()
