"""Masaüstüne devir paketi: iki zip (GitHub tek dosya sınırı 100 MB).

    python3.11 OTTOMAN_FRIGATE_1780_ISTANBUL/scripts/make_handoff_zip.py [vNNN]

1) <GEMI>_<v>_1_blend_betik_belge.zip : son .blend, scripts/, reports/ (md+json), KALDIGIM_YER, CLAUDE.md, ship_spec,
   _context/, son sürüm renderları, Tersane skill (skills/tersane + tersane.zip)
2) <GEMI>_<v>_2_doku_referans_fbx.zip : Textures/, references/, FBX/
Eski .blend sürümleri ve eski renderlar pakete girmez (git geçmişinde durur).
"""
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
SHIP = ROOT.name


def latest():
    vs = sorted(ROOT.glob(f"Blender/versions/{SHIP}_v*.blend"))
    return vs[-1].stem.split("_")[-1]


def add_tree(z, base, rel_root, skip=("__pycache__",)):
    base = Path(base)
    if base.is_file():
        z.write(base, base.relative_to(rel_root))
        return
    for p in sorted(base.rglob("*")):
        if p.is_file() and not any(s in p.parts for s in skip):
            z.write(p, p.relative_to(rel_root))


def main():
    v = sys.argv[1] if len(sys.argv) > 1 else latest()
    out = ROOT / "TESLIM"
    out.mkdir(exist_ok=True)
    for old in out.glob("*.zip"):
        old.unlink()
    z1 = out / f"{SHIP}_{v}_1_blend_betik_belge.zip"
    with zipfile.ZipFile(z1, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        add_tree(z, ROOT / "Blender" / "versions" / f"{SHIP}_{v}.blend", REPO)
        for d in ("scripts", "reports", "_context", f"renders/{v}"):
            if (ROOT / d).exists():
                add_tree(z, ROOT / d, REPO)
        for f in ("KALDIGIM_YER.md", "CLAUDE.md", "ship_spec.yaml"):
            if (ROOT / f).exists():
                add_tree(z, ROOT / f, REPO)
        add_tree(z, REPO / "skills" / "tersane", REPO)
        if (REPO / "skills" / "tersane.zip").exists():
            add_tree(z, REPO / "skills" / "tersane.zip", REPO)
    z2 = out / f"{SHIP}_{v}_2_doku_referans_fbx.zip"
    with zipfile.ZipFile(z2, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for d in ("Textures", "references", "FBX"):
            if (ROOT / d).exists():
                add_tree(z, ROOT / d, REPO)
    for p in (z1, z2):
        print(p.relative_to(REPO), round(p.stat().st_size / 1e6, 1), "MB")


if __name__ == "__main__":
    main()
