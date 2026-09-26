"""Ortografik renderlara modelden ölçülen boyut çizgilerini ekler.

Çalıştırma: python3 OTTOMAN_FRIGATE_1780_ISTANBUL/scripts/annotate_views.py v001
Ölçüler .blend içindeki değerlendirilmiş (modifier uygulanmış) geometriden alınır.
Kamera parametreleri build_hull_v001.py render_views() ile aynıdır.
"""

import sys
from pathlib import Path

import bpy  # noqa: I001
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SHIP_ID = "OTTOMAN_FRIGATE_1780_ISTANBUL"
VER = sys.argv[-1] if sys.argv[-1].startswith("v0") else "v001"
W, H, CAM_Z = 1600, 900, 2.3
SCALE = {"bas": 28.0, "kic": 28.0, "iskele_profil": 50.0, "sancak_profil": 50.0}
CX = {"x": 0.0}  # profil kamerasının X merkezi (ölçümden)
FONT = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 22)
FONT_S = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
FONT_T = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
INK, WL = (255, 214, 90), (90, 200, 255)


def measure():
    global CAM_Z
    bpy.ops.wm.open_mainfile(filepath=str(ROOT / "Blender" / "versions" / f"{SHIP_ID}_{VER}.blend"))
    k = float(bpy.context.scene.get("ship_scale", 1.0))  # v007+: dünya = k × tasarım
    for key in SCALE:
        SCALE[key] *= k
    CAM_Z *= k
    dg = bpy.context.evaluated_depsgraph_get()

    def pts(name):
        ob = bpy.data.objects[name]
        me = ob.evaluated_get(dg).to_mesh()
        out = [ob.matrix_world @ v.co for v in me.vertices]
        return out

    hull = pts("CORE_HULL_SHELL")
    allp = []
    for ob in bpy.context.scene.objects:
        if ob.type == "MESH" and not ob.hide_render and not ob.name.startswith(("UCX_", "CUT_")):
            allp += pts(ob.name)
    near_wl = [p for p in hull if abs(p.z) < 0.06]
    m = {
        "x_min": min(p.x for p in allp), "x_max": max(p.x for p in allp),
        "z_min": min(p.z for p in allp), "z_max": max(p.z for p in allp),
        "hull_x_min": min(p.x for p in hull), "hull_x_max": max(p.x for p in hull),
        "wl_x_min": min(p.x for p in near_wl), "wl_x_max": max(p.x for p in near_wl),
        "beam": 2 * max(abs(p.y) for p in hull),
        "wl_beam": 2 * max(abs(p.y) for p in near_wl),
    }
    mid = [p for p in hull if abs(p.x) < 0.4]
    m["waist_rail"] = max(p.z for p in mid)
    qd = [p for p in hull if p.x < m["hull_x_min"] + 1.0]
    m["stern_rail"] = max(p.z for p in qd)
    deck = pts("CORE_DECK_GUN")
    m["gundeck_mid"] = max(p.z for p in deck if abs(p.x) < 0.4 and abs(p.y) < 0.3)
    return m


def to_px(view, lat, z):
    ppm = W / SCALE[view]
    if view in ("iskele_profil", "sancak_profil"):
        lat = lat - CX["x"]
    if view == "sancak_profil":
        lat = -lat
    return W / 2 + lat * ppm, H / 2 - (z - CAM_Z) * ppm


def render_ortho(out_dir):
    """Ölçü görünüşleri için geniş kadrajlı ortografik renderlar (build betiğiyle aynı ışık)."""
    import math
    from mathutils import Vector
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = 48
    sc.cycles.use_denoising = True
    sc.render.resolution_x, sc.render.resolution_y = W, H
    if not sc.world:
        sc.world = bpy.data.worlds.new("World")
    sc.world.color = (0.20, 0.205, 0.21)
    if not any(o.type == "LIGHT" for o in sc.objects):
        sun = bpy.data.lights.new("Sun", "SUN"); sun.energy = 3.2
        so = bpy.data.objects.new("LGT_Sun", sun)
        so.rotation_euler = (math.radians(50), math.radians(12), math.radians(-35))
        sc.collection.objects.link(so)
        # sancak tarafı için dolgu (ölçü paftasında iki profil de okunur olsun)
        fill = bpy.data.lights.new("SunFill", "SUN"); fill.energy = 2.0
        fo = bpy.data.objects.new("LGT_SunFill", fill)
        fo.rotation_euler = (math.radians(55), math.radians(-12), math.radians(145))
        sc.collection.objects.link(fo)
    cams ={"bas": ((60, 0), 0), "kic": ((-60, 0), 0),
            "iskele_profil": ((CX["x"], -80), 1), "sancak_profil": ((CX["x"], 80), 1)}
    paths = {}
    for view, ((x, y), prof) in cams.items():
        cam = bpy.data.cameras.new(f"CAMDIM_{view}")
        cam.type = "ORTHO"; cam.ortho_scale = SCALE[view]; cam.clip_end = 500
        ob = bpy.data.objects.new(f"CAMDIM_{view}", cam)
        ob.location = (x, y, CAM_Z)
        tgt = Vector((CX["x"] if prof else 0, 0, CAM_Z))
        ob.rotation_euler = (tgt - ob.location).to_track_quat("-Z", "Y").to_euler()
        sc.collection.objects.link(ob)
        sc.camera = ob
        p = out_dir / f"_src_{view}.png"
        sc.render.filepath = str(p)
        bpy.ops.render.render(write_still=True)
        paths[view] = p
    return paths


def arrow_h(d, view, a, b, z, label, off=0):
    (x1, y), (x2, _) = to_px(view, a, z), to_px(view, b, z)
    y += off
    d.line([(x1, y), (x2, y)], fill=INK, width=3)
    for x in (x1, x2):
        d.line([(x, y - 12), (x, y + 12)], fill=INK, width=3)
    tw = d.textlength(label, font=FONT)
    d.rectangle([((x1 + x2) / 2 - tw / 2 - 6, y - 34), ((x1 + x2) / 2 + tw / 2 + 6, y - 6)], fill=(20, 20, 24))
    d.text(((x1 + x2) / 2 - tw / 2, y - 33), label, font=FONT, fill=INK)


def arrow_v(d, view, lat, z1, z2, label, right=True):
    (x, y1), (_, y2) = to_px(view, lat, z1), to_px(view, lat, z2)
    d.line([(x, y1), (x, y2)], fill=INK, width=3)
    for y in (y1, y2):
        d.line([(x - 12, y), (x + 12, y)], fill=INK, width=3)
    tx = x + 14 if right else x - 14 - d.textlength(label, font=FONT_S)
    d.rectangle([(tx - 4, (y1 + y2) / 2 - 13), (tx + d.textlength(label, font=FONT_S) + 4, (y1 + y2) / 2 + 13)], fill=(20, 20, 24))
    d.text((tx, (y1 + y2) / 2 - 11), label, font=FONT_S, fill=INK)


def waterline(d, view):
    _, y = to_px(view, 0, 0.0)
    d.line([(0, y), (W, y)], fill=WL, width=2)
    d.text((12, y - 26), "Su hattı Z = 0", font=FONT_S, fill=WL)


def title(d, text, sub):
    d.rectangle([(0, 0), (W, 70)], fill=(20, 20, 24))
    d.text((20, 8), text, font=FONT_T, fill=(240, 240, 240))
    d.text((20, 42), sub, font=FONT_S, fill=(180, 180, 180))


def f(v):
    return f"{v:.2f}".replace(".", ",") + " m"


def main():
    m = measure()
    CX["x"] = (m["x_min"] + m["x_max"]) / 2
    out = ROOT / "renders" / VER / "olculu"
    out.mkdir(parents=True, exist_ok=True)
    srcs = render_ortho(out)
    sub = f"{SHIP_ID} {VER} · ölçüler modelden ölçüldü · 1 birim = 1 m"
    files = []
    for view, name in (("iskele_profil", "SOL (İSKELE) PROFİL"), ("sancak_profil", "SAĞ (SANCAK) PROFİL")):
        im = Image.open(srcs[view]).convert("RGB")
        d = ImageDraw.Draw(im)
        waterline(d, view)
        arrow_h(d, view, m["x_min"], m["x_max"], m["z_min"] - 0.6, f"Toplam boy (baş kıvrımı ve dümen dahil) {f(m['x_max'] - m['x_min'])}", off=40)
        arrow_h(d, view, m["wl_x_min"], m["wl_x_max"], 0.0, f"Su hattı boyu {f(m['wl_x_max'] - m['wl_x_min'])}", off=-6)
        arrow_h(d, view, m["hull_x_min"], m["hull_x_max"], m["z_max"] + 0.5, f"Gövde boyu (küpeşte) {f(m['hull_x_max'] - m['hull_x_min'])}")
        side = 1 if view == "iskele_profil" else -1
        arrow_v(d, view, side * 1.0, m["z_min"], 0.0, f"Su çekimi {f(-m['z_min'])}")
        arrow_v(d, view, side * 3.5, 0.0, m["gundeck_mid"], f"Batarya güv. (orta) {f(m['gundeck_mid'])}")
        arrow_v(d, view, side * -3.5, 0.0, m["waist_rail"], f"Bel küpeştesi {f(m['waist_rail'])}", right=False)
        arrow_v(d, view, side * (m["hull_x_min"] + 2.0), 0.0, m["stern_rail"], f"Kıç küpeştesi {f(m['stern_rail'])}")
        title(d, name, sub)
        p = out / f"{SHIP_ID}_{VER}_{view}_olculu.png"
        im.save(p)
        files.append(p)
    for view, name in (("bas", "ÖN (BAŞ) GÖRÜNÜŞ"), ("kic", "ARKA (KIÇ) GÖRÜNÜŞ")):
        im = Image.open(srcs[view]).convert("RGB")
        d = ImageDraw.Draw(im)
        waterline(d, view)
        arrow_h(d, view, -m["beam"] / 2, m["beam"] / 2, m["z_min"] - 0.3, f"En (azami) {f(m['beam'])}", off=30)
        arrow_h(d, view, -m["wl_beam"] / 2, m["wl_beam"] / 2, 0.0, f"Su hattı eni {f(m['wl_beam'])}", off=-6)
        arrow_v(d, view, m["beam"] / 2 + 0.8, m["z_min"], 0.0, f"Su çekimi {f(-m['z_min'])}")
        arrow_v(d, view, m["beam"] / 2 + 0.8, 0.0, m["z_max"], f"Su üstü yükseklik {f(m['z_max'])}")
        arrow_v(d, view, -m["beam"] / 2 - 0.8, m["z_min"], m["z_max"], f"Toplam yükseklik {f(m['z_max'] - m['z_min'])}", right=False)
        title(d, name, sub)
        p = out / f"{SHIP_ID}_{VER}_{view}_olculu.png"
        im.save(p)
        files.append(p)
    # 2x2 pafta
    ims = [Image.open(p) for p in files]
    sheet = Image.new("RGB", (W * 2, H * 2))
    order = [2, 3, 0, 1]  # ön, arka / sol, sağ
    for k, idx in enumerate(order):
        sheet.paste(ims[idx], ((k % 2) * W, (k // 2) * H))
    sp = out / f"{SHIP_ID}_{VER}_olculu_pafta.png"
    sheet.save(sp)
    for p in srcs.values():
        p.unlink()
    print({k: round(v, 3) for k, v in m.items()})
    print(*files, sp, sep="\n")


if __name__ == "__main__":
    main()
