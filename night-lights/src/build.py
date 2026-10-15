"""Night Lights (free pack): Nexo config, resource pack and download zip. Mistbloom Studios."""
import glob, os, re, shutil, zipfile
import yaml
import pieces as P
from engine import NS

VERSION = "1.0"
NAMEC, TAGC = "#c9b8f0", "#9fb3d9"

# id: (name, lore, light level, place, interaction box w,h)
SPEC = {
    "star_lamp":            ("Star Lamp", ["A brass lamp with a glowing star on top.", "Right-click to turn the light on and off."], 12, "floor", (0.8, 1.3)),
    "moon_jelly_jar":       ("Moon Jelly Jar", ["A little moon jelly glowing in a corked jar.", "Right-click to turn the light on and off."], 11, "floor", (0.7, 0.8)),
    "crescent_moon_sconce": ("Crescent Moon Sconce", ["A crescent moon hanging from a brass bracket.", "Right-click to turn the light on and off."], 12, "wall", (0.8, 1.0)),
}


def nexo_yaml():
    out = {}
    for iid, (name, lore, light, place, (iw, ih)) in SPEC.items():
        f = {
            "restricted_rotation": "VERY_STRICT",
            "preview_placement": True,
            "block_sounds": {f"{k}_sound": f"block.lantern.{k}" for k in ("place", "break", "hit", "step", "fall")},
            "limited_placing": {"floor": place == "floor", "wall": place == "wall", "roof": False},
            "hitbox": {"interactions": [f"0,0,0 {iw},{ih}"]},
            "lights": {"toggleable": True, "toggled_item_model": f"{NS}:{iid}_lit", "lights": [f"0,0,0 {light}"]},
        }
        out[f"{NS}_{iid}"] = {
            "itemname": f"<{NAMEC}>{name}",
            "lore": [f"<gray>{l}" for l in lore] + [f"<{TAGC}>Night Lights"],
            "material": "PAPER",
            "Components": {"item_model": f"{NS}:{iid}"},
            "Mechanics": {"furniture": f},
        }
    head = f"# Night Lights v{VERSION} by Mistbloom Studios - Nexo\n# Minecraft 1.21.4+.\n\n"
    txt = yaml.safe_dump(out, sort_keys=False, allow_unicode=True, width=200)
    return head + re.sub(rf"\n({NS}_)", r"\n\n\1", txt)


# the user's own README template (see claude/brand/PACK_STANDARDS.md)
README = """Night Lights - Mistbloom Studios
==================================================

Glowing night lights for your builds made in Nexo

INSTALL - Drag and Drop (Nexo)
--------------
1. Copy Nexo/items/nightlights.yml into plugins/Nexo/items/
2. Copy the Nexo/pack/assets/ folder into plugins/Nexo/pack/assets/
3. Run /nexo reload all, then /nexo inventory to grab the pieces.

Requires Minecraft 1.21.4 or newer
"""

LICENSE = """Night Lights - Mistbloom Studios
License: free to use on any server you own or run. You may edit the files for your own servers.
Please don't reupload, resell or share these files (original or edited). Link people to the Mistbloom Studios page instead.
"""


def package(out_dir="."):
    ROOT, STAGE = os.path.join(out_dir, "dist"), os.path.join(out_dir, "stage")
    shutil.rmtree(ROOT, ignore_errors=True); shutil.rmtree(STAGE, ignore_errors=True)
    models = P.all_models()
    for m in models:
        m.check(); m.export(STAGE)
    shutil.copytree(os.path.join(STAGE, "assets"), f"{ROOT}/Nexo/pack/assets")
    os.makedirs(f"{ROOT}/Nexo/items")
    open(f"{ROOT}/Nexo/items/{NS}.yml", "w").write(nexo_yaml())
    open(f"{ROOT}/README.txt", "w", newline="\r\n").write(README)
    open(f"{ROOT}/LICENSE.txt", "w", newline="\r\n").write(LICENSE)
    names = {m.name for m in models}
    txt = open(f"{ROOT}/Nexo/items/{NS}.yml").read()
    yaml.safe_load(txt)
    for ref in re.findall(rf"{NS}:([a-z_]+)", txt):
        assert ref in names, ref
    for m in models:
        t = f"{ROOT}/Nexo/pack/assets/{NS}/textures/furniture/{m.name}.png"
        assert os.path.exists(t) and (not m.is_animated() or os.path.exists(t + ".mcmeta")), t
    z = os.path.join(out_dir, f"Night-Lights-v{VERSION}.zip")
    with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in sorted(glob.glob(f"{ROOT}/**/*", recursive=True)):
            if os.path.isfile(p):
                zf.write(p, os.path.join("Night-Lights", os.path.relpath(p, ROOT)))
    print(len(models), "models,", len(SPEC), "items ->", z, os.path.getsize(z) // 1024, "KB")
    return z


if __name__ == "__main__":
    package()
