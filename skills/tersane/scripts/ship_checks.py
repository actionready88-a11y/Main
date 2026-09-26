"""Tersane — gemi sahnesi denetimleri (her pass sonunda çalıştır, sonucu audit JSON'a ekle).

Komut satırı (bpy kurulu Python ya da blender -b):
    python3 ship_checks.py <gemi.blend> [--stairs CORE_STAIRS_A,CORE_LADDER_B] [--holes x,y,z0;x,y,z0] [--out rapor.json]

Kod içinden:
    import ship_checks as chk
    chk.bvh_overlaps(["CORE_STAIRS_POOP_S"])          → [{"stair":..,"with":..,"pairs":..}]   (hedef: boş liste)
    chk.holes_open([(-6.6, 0.1, 5.0)])                 → [{"at":.., "hit":None|nesne}]         (ambar ağzı açık mı)
    chk.ucx_audit()                                    → köşe sınırı, ad kuralı, sahip mevcut
    chk.snap_to_deck(prefixes=("SOCKET_CANNON_","SOCK_CREW_"))  → soketleri güverte yüzeyine oturtur
    chk.boolean_modifiers()                            → EXACT çözücülü boolean listesi (sessiz hata riski)

Dersler: EXACT boolean mesh değişince sessizce başarısız olabilir (delik açılmaz) → ince güvertede FLOAT + ışın testi.
Soketler orta hat yüksekliğinde kalırsa kamburluk/sheer yüzünden 0,1–0,3 m havada/gömülü olur → snap_to_deck.
"""

import json
import sys

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

V = Vector


def _bvh(o, dg):
    ev = o.evaluated_get(dg)
    me = ev.to_mesh()
    t = BVHTree.FromPolygons([o.matrix_world @ v.co for v in me.vertices], [tuple(p.vertices) for p in me.polygons])
    ev.to_mesh_clear()
    return t


def bvh_overlaps(names, prefixes=("CORE_", "MOD_"), skip=("UCX_", "CUT_", "_LOD")):
    dg = bpy.context.evaluated_depsgraph_get()
    others = [o for o in bpy.data.objects if o.type == "MESH" and not o.hide_render and o.name.startswith(prefixes)
              and o.name not in names and not any(s in o.name for s in skip)]
    trees = {o.name: _bvh(o, dg) for o in others}
    out = []
    for n in names:
        o = bpy.data.objects.get(n)
        if o is None:
            continue
        t = _bvh(o, dg)
        for m, tm in trees.items():
            k = len(t.overlap(tm))
            if k:
                out.append({"stair": n, "with": m, "pairs": k})
    return out


def holes_open(points, distance=2.2):
    """points: [(x, y, z_başlangıç)] — aşağı ışın; isabet yoksa delik açık."""
    sc = bpy.context.scene
    dg = bpy.context.evaluated_depsgraph_get()
    res = []
    for x, y, z0 in points:
        ok, loc, _, _, ob, _ = sc.ray_cast(dg, V((x, y, z0)), V((0, 0, -1)), distance=distance)
        res.append({"at": [x, y, z0], "hit": ob.name if ok else None})
    return res


def ucx_audit(max_verts=64):
    ucx = [o for o in bpy.data.objects if o.name.startswith("UCX_")]
    return {
        "count": len(ucx),
        "max_verts": max((len(o.data.vertices) for o in ucx), default=0),
        "over_limit": [(o.name, len(o.data.vertices)) for o in ucx if len(o.data.vertices) > max_verts],
        "owner_missing": [o.name for o in ucx if o.get("owner_mesh") and o["owner_mesh"] not in bpy.data.objects],
        "bad_name": [o.name for o in ucx if o.get("owner_mesh") and not o.name.startswith(f"UCX_{o['owner_mesh']}_")],
    }


def deck_hit(x, y, z_top, deck_prefix="CORE_DECK_", tries=6, step=2.0):
    sc = bpy.context.scene
    dg = bpy.context.evaluated_depsgraph_get()
    o = V((x, y, z_top))
    for _ in range(tries):
        ok, loc, _, _, ob, _ = sc.ray_cast(dg, o, V((0, 0, -1)), distance=step)
        if not ok:
            return None
        if ob.name.startswith(deck_prefix):
            return loc.z
        o = loc - V((0, 0, 0.002))
    return None


def snap_to_deck(prefixes=("SOCKET_CANNON_", "SOCK_CREW_"), lift=0.6):
    fixed, miss = [], []
    for o in bpy.data.objects:
        if o.type != "EMPTY" or not o.name.startswith(prefixes):
            continue
        z = deck_hit(o.location.x, o.location.y, o.location.z + lift)
        if z is None:
            miss.append(o.name)
        elif abs(z - o.location.z) > 0.002:
            fixed.append((o.name, round(z - o.location.z, 3)))
            o.location.z = z
    return {"fixed": len(fixed), "range": (min((f[1] for f in fixed), default=0), max((f[1] for f in fixed), default=0)),
            "missed": miss}


def boolean_modifiers():
    return [{"object": o.name, "modifier": m.name, "solver": m.solver, "cutter": m.object.name if m.object else None}
            for o in bpy.data.objects if o.type == "MESH" for m in o.modifiers if m.type == "BOOLEAN"]


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    blend = argv[0]
    bpy.ops.wm.open_mainfile(filepath=blend)
    stairs, holes, out = [], [], None
    for i, a in enumerate(argv):
        if a == "--stairs":
            stairs = argv[i + 1].split(",")
        if a == "--holes":
            holes = [tuple(float(v) for v in h.split(",")) for h in argv[i + 1].split(";")]
        if a == "--out":
            out = argv[i + 1]
    rep = {"blend": blend, "ucx": ucx_audit(), "booleans": boolean_modifiers()}
    if stairs:
        rep["stair_overlaps"] = bvh_overlaps(stairs)
    if holes:
        rep["holes"] = holes_open(holes)
    txt = json.dumps(rep, indent=2, ensure_ascii=False)
    if out:
        open(out, "w", encoding="utf-8").write(txt)
    print(txt)


if __name__ == "__main__":
    main()
