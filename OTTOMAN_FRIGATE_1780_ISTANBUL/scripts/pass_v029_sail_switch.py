"""v029 — Yelken aç/kapa anahtarı (Blender içinden, betik çalıştırmadan).

    python3.11 OTTOMAN_FRIGATE_1780_ISTANBUL/scripts/pass_v029_sail_switch.py

Kurulum:
- `00_CONTROLS/CTRL_YELKEN` boş nesnesi; özel özellik `yelken_acik` (0 = sarılı, 1 = açık).
- Her yelken nesnesinin hide_viewport/hide_render değeri sürücüyle (driver) bu özelliğe bağlı.
  Basit ifade sürücüsü olduğundan "Auto Run Python Scripts" izni GEREKMEZ.
- Outliner düzeni: 21_MODULES_SAILS/SAILS_SARILI ve SAILS_ACIK alt koleksiyonları.
- `yelken_anahtari.py` metin bloğu: 3D Görünüm → N paneli → "Gemi" sekmesinde "Yelkenleri Aç/Sar" butonu.
  (Auto Run kapalıysa: Scripting sekmesi → yelken_anahtari.py → Run Script, bir kez.)
Kullanım: Outliner'da CTRL_YELKEN seç → Object Properties → Custom Properties → yelken_acik 0/1.
Yedek yol: Outliner'da 21_MODULES_SAILS/SAILS_SARILI ve SAILS_ACIK koleksiyonlarının onay kutuları.
"""

import json
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[1]
SHIP = "OTTOMAN_FRIGATE_1780_ISTANBUL"
SRC = ROOT / "Blender" / "versions" / f"{SHIP}_v028.blend"
VER = "v029"


def ensure_col(name, parent):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in parent.children:
        parent.children.link(c)
    return c


def drive(o, path, ctrl, expr):
    o.driver_remove(path)
    fc = o.driver_add(path)
    d = fc.driver
    d.type = "SCRIPTED"
    v = d.variables.new()
    v.name = "acik"
    v.type = "SINGLE_PROP"
    v.targets[0].id_type = "OBJECT"
    v.targets[0].id = ctrl
    v.targets[0].data_path = '["yelken_acik"]'
    d.expression = expr


PANEL = '''# Yelken anahtarı — 3D Görünüm > N paneli > "Gemi" sekmesi.
import bpy


def _apply(acik):
    c = bpy.data.objects.get("CTRL_YELKEN")
    if c is None:
        return
    c["yelken_acik"] = int(acik)
    c.update_tag()
    for o in bpy.data.objects:
        st = o.get("sail_state")
        if st in ("furled", "set"):
            gizle = (st == "furled") == bool(acik)
            if not (o.animation_data and o.animation_data.drivers):
                o.hide_viewport = o.hide_render = gizle
            o.update_tag()
    bpy.context.scene.frame_set(bpy.context.scene.frame_current)


class GEMI_OT_yelken(bpy.types.Operator):
    bl_idname = "gemi.yelken_toggle"
    bl_label = "Yelkenleri Aç/Sar"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        c = bpy.data.objects.get("CTRL_YELKEN")
        _apply(0 if c and c.get("yelken_acik", 0) else 1)
        return {"FINISHED"}


class GEMI_PT_yelken(bpy.types.Panel):
    bl_label = "Yelkenler"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Gemi"

    def draw(self, context):
        c = bpy.data.objects.get("CTRL_YELKEN")
        col = self.layout.column()
        if c is None:
            col.label(text="CTRL_YELKEN yok")
            return
        col.label(text="Durum: " + ("AÇIK" if c.get("yelken_acik", 0) else "SARILI"))
        col.operator("gemi.yelken_toggle", icon="MOD_CLOTH")
        col.prop(c, \'["yelken_acik"]\', text="yelken_acik (0/1)")


def register():
    for cl in (GEMI_OT_yelken, GEMI_PT_yelken):
        try:
            bpy.utils.register_class(cl)
        except ValueError:
            pass


register()
'''


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SRC))
    sc = bpy.context.scene
    ctl_col = ensure_col("00_CONTROLS", sc.collection)
    ctrl = bpy.data.objects.get("CTRL_YELKEN")
    if ctrl is None:
        ctrl = bpy.data.objects.new("CTRL_YELKEN", None)
        ctl_col.objects.link(ctrl)
    ctrl.empty_display_type = "SPHERE"
    ctrl.empty_display_size = 0.8
    ctrl.location = (0.0, 0.0, 40.0)
    ctrl["yelken_acik"] = 0
    ui = ctrl.id_properties_ui("yelken_acik")
    ui.update(min=0, max=1, soft_min=0, soft_max=1, step=1,
              description="0 = yelkenler sarılı (varsayılan), 1 = yelkenler açık")
    ctrl["aciklama"] = "yelken_acik: 0 sarılı / 1 açık — sürücüler tüm yelken ve amblemleri günceller"

    sails = bpy.data.collections["21_MODULES_SAILS"]
    subs = {"furled": ensure_col("SAILS_SARILI", sails), "set": ensure_col("SAILS_ACIK", sails)}
    n = {"furled": 0, "set": 0}
    for o in list(bpy.data.objects):
        st = o.get("sail_state")
        if st not in subs:
            continue
        for c in list(o.users_collection):
            if c != subs[st]:
                c.objects.unlink(o)
        if o.name not in subs[st].objects:
            subs[st].objects.link(o)
        # açıkken gizlenecek olan: sarılı; kapalıyken gizlenecek olan: açık yelken
        expr = "acik > 0.5" if st == "furled" else "acik < 0.5"
        drive(o, "hide_viewport", ctrl, expr)
        drive(o, "hide_render", ctrl, expr)
        n[st] += 1

    txt = bpy.data.texts.get("yelken_anahtari.py") or bpy.data.texts.new("yelken_anahtari.py")
    txt.clear()
    txt.write(PANEL)
    txt.use_module = True
    compile(PANEL, "yelken_anahtari.py", "exec")

    # test: her yelkenin iki sürücüsü de CTRL_YELKEN'e bağlı mı; ifadeye göre iki durumda kaç yelken görünür.
    # (Başsız modda sürücü sonucu orijinal nesneye yazılmaz, fcurve.evaluate önbellek döndürür → yapı doğrulanır.)
    bad, checks = [], {}
    for st, c in subs.items():
        for o in c.objects:
            for f in o.animation_data.drivers:
                t = f.driver.variables[0].targets[0]
                if not (f.driver.is_valid and t.id == ctrl and t.data_path == '["yelken_acik"]'):
                    bad.append((o.name, f.data_path))
    for val in (1, 0):
        vis = {st: sum(1 for o in c.objects
                       if not eval(o.animation_data.drivers[0].driver.expression, {}, {"acik": val}))
               for st, c in subs.items()}
        checks[f"yelken_acik={val}"] = {"gorunen_sarili": vis["furled"], "gorunen_acik": vis["set"]}
    checks["hatali_surucu"] = bad
    ctrl["yelken_acik"] = 0
    out = ROOT / "Blender" / "versions" / f"{SHIP}_{VER}.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(out))
    rep = {"version": VER, "source": SRC.name, "control": "CTRL_YELKEN.yelken_acik", "driven": n, "checks": checks}
    (ROOT / "reports" / f"scene_audit_{VER}.json").write_text(json.dumps(rep, indent=2, ensure_ascii=False), encoding="utf-8")
    print("V029", json.dumps(rep, ensure_ascii=False))


if __name__ == "__main__":
    main()
