"""v036 — Bozkurt figürü B3: yele tek oyma kütle + patinalı döküm bronz.

    python3.11 OTTOMAN_FRIGATE_1780_ISTANBUL/scripts/pass_v036_figurehead_bozkurt_b3.py [--no-render | --render-only]

Kullanıcı (v035): "figür olmamış" — yele tutamları yakından "solucan" gibi; altın kenar çizgileri bunu büyütüyordu.
Ücretsiz hazır varlık arandı: bu ortamın ağ politikası Sketchfab / Poly Haven / Free3D / Printables vb.'ye çıkışı
engelliyor, GitHub'da uygun (CC0/CC-BY, yüksek çözünürlüklü) kurt başı yok → Blender'da yeniden zorlandı.
 1. Figür kaynağı scripts/wolf_sdf2.py: tutamlar birbirine yumuşak kaynar (oyma/döküm yele kütlesi), kabarma düşük.
 2. Malzeme MAT_Figure_WolfBronzePatina: çukurlar koyu yeşil-siyah patina, çıkıntılar aşınmış sıcak bronz,
    pürüzlülük çukurda yüksek / çıkıntıda düşük (altın kenar çizgisi yok; altın yalnız kaide kuşağında).
 3. clean_mats(): diş/dil/göz sınırındaki tek-yüz malzeme tırtıkları temizlenir.
Baş parmaklıkları v035'teki gibi kalır (yeniden kurulmaz). v035 pass'i değişmeden kaynak olarak kullanılır.
"""

import importlib.util
import json
import sys
from pathlib import Path

import bpy  # noqa: I001

HERE = Path(__file__).resolve().parent
sp = importlib.util.spec_from_file_location("pass_v035", HERE / "pass_v035_figurehead_bozkurt_b2.py")
P35 = importlib.util.module_from_spec(sp)
sp.loader.exec_module(P35)
sys.path.insert(0, str(HERE))
import wolf_sdf2 as WS2  # noqa: E402

ROOT, SHIP = P35.ROOT, P35.SHIP
SRC_VER, VER = "v035", "v036"


class _WS:
    """v035 build() WS.build/WS.S kullanır → v036 kaynağına yönlendir, mesh() çıktısına malzeme süzgeci ekle."""
    S = WS2.S

    @staticmethod
    def build(voxel):
        g = WS2.build(voxel)
        raw = g.mesh

        def mesh(step=1):
            v, f, fm = raw(step)
            return v, f, WS2.clean_mats(f, fm)
        g.mesh = mesh
        return g


def mat_wolf():
    m = bpy.data.materials.get("MAT_Figure_WolfBronzePatina") or bpy.data.materials.new("MAT_Figure_WolfBronzePatina")
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        if n.type not in ("BSDF_PRINCIPLED", "OUTPUT_MATERIAL"):
            nt.nodes.remove(n)
    b = nt.nodes["Principled BSDF"]
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    ramp = nt.nodes.new("ShaderNodeValToRGB")                    # çukur → patina, çıkıntı → aşınmış bronz
    e0, e1 = ramp.color_ramp.elements
    e0.position, e0.color = 0.492, (0.018, 0.028, 0.024, 1)
    e1.position, e1.color = 0.528, (0.36, 0.22, 0.10, 1)
    mid = ramp.color_ramp.elements.new(0.508)
    mid.color = (0.10, 0.075, 0.045, 1)
    nt.links.new(geo.outputs["Pointiness"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    rr = nt.nodes.new("ShaderNodeMapRange")
    rr.inputs["From Min"].default_value, rr.inputs["From Max"].default_value = 0.492, 0.528
    rr.inputs["To Min"].default_value, rr.inputs["To Max"].default_value = 0.62, 0.30
    nt.links.new(geo.outputs["Pointiness"], rr.inputs["Value"])
    nt.links.new(rr.outputs["Result"], b.inputs["Roughness"])
    b.inputs["Metallic"].default_value = 0.85
    m["ue_note"] = "UE: pointiness yok → curvature/AO bake ile BC + ORM (patina maskesi)"
    return m


def keep_rails():
    out = {}
    for s in ("S", "P"):
        o = bpy.data.objects[f"CORE_HEAD_RAIL_{s}"]
        out[s] = {"kept_from": SRC_VER, "verts": len(o.data.vertices)}
    return out


P35.SRC_VER, P35.VER = SRC_VER, VER
P35.WS = _WS
P35.mat_wolf = mat_wolf
P35.rebuild_head_rails = keep_rails


def main():
    P35.main()
    if "--render-only" in sys.argv:
        return
    ap = ROOT / "reports" / f"scene_audit_{VER}.json"
    a = json.loads(ap.read_text(encoding="utf-8"))
    fh = a.pop("figurehead_v035")
    fh["replaced"] = "MOD_FIGUREHEAD_BOZKURT_B (v035, altın kenarlı tüp tutamlar)"
    fh["material"] = "MAT_Figure_WolfBronzePatina"
    a["figurehead_v036"] = fh
    a["pass"] = {"name": "pass_v036_figurehead_bozkurt_b3", "source": f"Blender/versions/{SHIP}_{SRC_VER}.blend"}
    ap.write_text(json.dumps(a, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
