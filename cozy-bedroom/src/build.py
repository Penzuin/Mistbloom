"""Cozy Bedroom (free pack): Nexo config, resource pack and download zip. Mistbloom Studios."""
import glob, os, re, shutil, zipfile
import yaml
import pieces as P
from engine import NS

VERSION = "1.0"
NAMEC, TAGC = "#c9b8f0", "#9fb3d9"
PACK = "Cozy Bedroom"
ZIPNAME = "Cozy-Bedroom"


def S(name, lore, **kw):
    d = dict(name=name, lore=lore, barriers=None, interaction=None, seats=None, storage=None,
             light=None, place="floor", sound="wood")
    d.update(kw)
    return d


SPEC = {
    "quilted_bed": S("Quilted Bed", ["A honey oak bed with a patchwork quilt.", "Seats two."],
                     barriers=[(0, 0, 0), (1, 0, 0)], seats=[(0, 0.55, 0), (1, 0.55, 0)]),
    "bedside_table": S("Bedside Table", ["A two-drawer table with books and a mug of tea.", "Holds 9 slots."],
                       barriers=[(0, 0, 0)], storage=(1, "Bedside Table")),
    "toadstool_lamp": S("Toadstool Lamp", ["A rose toadstool that glows from underneath.", "Right-click to turn the light on and off."],
                        interaction=(0.7, 0.8), light=12),
    "braided_rug": S("Braided Rug", ["A round braided rug in lilac, cream and sage."],
                     interaction=(2, 0.1), sound="wool"),
    "wall_shelf": S("Wall Shelf", ["An oak shelf with books and a little pothos."],
                    interaction=(1, 1), place="wall"),
    "wardrobe": S("Cottage Wardrobe", ["A tall oak wardrobe with two panelled doors.", "Holds 27 slots."],
                  barriers=[(0, 0, 0), (0, 1, 0)], storage=(3, "Cottage Wardrobe")),
    "floor_cushions": S("Floor Cushions", ["A lilac cushion with a sage one on top.", "Seats one."],
                        interaction=(1, 0.5), seats=[(0, 0.45, 0)], sound="wool"),
}
SOUNDS = {"wood": "block.wood", "wool": "block.wool"}


def _off(t):
    return ",".join(str(v) for v in t)


def nexo_yaml():
    out = {}
    for iid, s in SPEC.items():
        f = {"restricted_rotation": "VERY_STRICT", "preview_placement": True,
             "block_sounds": {f"{k}_sound": f"{SOUNDS[s['sound']]}.{k}" for k in ("place", "break", "hit", "step", "fall")},
             "limited_placing": {"floor": s["place"] == "floor", "wall": s["place"] == "wall", "roof": False}}
        if s["barriers"]:
            f["hitbox"] = {"barriers": [_off(b) for b in s["barriers"]]}
        else:
            f["hitbox"] = {"interactions": [f"0,0,0 {s['interaction'][0]},{s['interaction'][1]}"]}
        if s["seats"]:
            f["seats"] = [_off(x) for x in s["seats"]]
        if s["storage"]:
            f["storage"] = {"type": "STORAGE", "rows": s["storage"][0], "title": f"<{NAMEC}>{s['storage'][1]}",
                            "open_sound": "block.barrel.open", "close_sound": "block.barrel.close"}
        if s["light"]:
            f["lights"] = {"toggleable": True, "toggled_item_model": f"{NS}:{iid}_lit", "lights": [f"0,0,0 {s['light']}"]}
        out[f"{NS}_{iid}"] = {
            "itemname": f"<{NAMEC}>{s['name']}",
            "lore": [f"<gray>{l}" for l in s["lore"]] + [f"<{TAGC}>{PACK}"],
            "material": "PAPER",
            "Components": {"item_model": f"{NS}:{iid}"},
            "Mechanics": {"furniture": f},
        }
    head = f"# {PACK} v{VERSION} by Mistbloom Studios - Nexo\n# Minecraft 1.21.4 to 1.26.2.\n\n"
    txt = yaml.safe_dump(out, sort_keys=False, allow_unicode=True, width=200)
    return head + re.sub(rf"\n({NS}_)", r"\n\n\1", txt)


# the user's own README template (see claude/brand/PACK_STANDARDS.md)
README = f"""{PACK} - Mistbloom Studios
==================================================

A cozy cottage bedroom set for your Nexo builds

INSTALL - Drag and Drop (Nexo)
--------------
1. Copy Nexo/items/{NS}.yml into plugins/Nexo/items/
2. Copy the Nexo/pack/assets/ folder into plugins/Nexo/pack/assets/
3. Run /nexo reload all, then /nexo inventory to grab the pieces.

Requires Minecraft 1.21.4 or newer
"""

LICENSE = f"""{PACK} - Mistbloom Studios
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
    shutil.rmtree(STAGE)
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
    z = os.path.join(out_dir, f"{ZIPNAME}-v{VERSION}.zip")
    with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in sorted(glob.glob(f"{ROOT}/**/*", recursive=True)):
            if os.path.isfile(p):
                zf.write(p, os.path.join(ZIPNAME, os.path.relpath(p, ROOT)))
    print(len(models), "models,", len(SPEC), "items ->", z, os.path.getsize(z) // 1024, "KB")
    return z


if __name__ == "__main__":
    package()
