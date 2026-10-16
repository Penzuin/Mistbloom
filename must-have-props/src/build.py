"""Cozy Bedroom (free pack): Nexo config, resource pack and download zip. Mistbloom Studios."""
import glob, os, re, shutil, zipfile
import yaml
import pieces as P
from engine import NS

VERSION = "1.0"
NAMEC, TAGC = "#e8c48a", "#b8b0a2"
PACK = "Must-Have Props"
ZIPNAME = "Must-Have-Props"


def S(name, lore, **kw):
    d = dict(name=name, lore=lore, barriers=None, interaction=None, seats=None, storage=None,
             light=None, place="floor", sound="wood")
    d.update(kw)
    return d


TOGGLE = "Right-click to turn the light on and off."
# piece order = how they're grouped in the listing: storage & clutter, lights, outdoor & town
SPEC = {
    "wooden_crate": S("Wooden Crate", ["An oak crate with a braced side.", "Holds 27 slots."],
                      barriers=[(0, 0, 0)], storage=(3, "Wooden Crate")),
    "crate_stack": S("Crate Stack", ["Two crates with a smaller one on top."],
                     barriers=[(0, 0, 0), (1, 0, 0), (0, 1, 0)]),
    "oak_barrel": S("Oak Barrel", ["A round oak barrel with iron hoops.", "Holds 27 slots."],
                    barriers=[(0, 0, 0)], storage=(3, "Oak Barrel")),
    "grain_sacks": S("Grain Sacks", ["Three burlap sacks tied with twine."],
                     interaction=[(0, 0, 0, 1, 0.8)], sound="wool"),
    "apple_basket": S("Apple Basket", ["A wicker basket full of apples."],
                      interaction=[(0, 0, 0, 0.8, 0.8)], sound="wool"),
    "book_pile": S("Book Pile", ["A stack of five old books."],
                   interaction=[(0, 0, 0, 0.7, 0.6)], sound="wool"),
    "iron_lantern": S("Iron Lantern", ["An iron lantern with a candle inside.", TOGGLE],
                      interaction=[(0, 0, 0, 0.5, 0.9)], light=15, sound="metal"),
    "hanging_lantern": S("Hanging Lantern", ["An iron lantern on a short chain.", TOGGLE],
                         interaction=[(0, 0, 0, 0.5, 1)], light=15, place="roof", sound="metal"),
    "candle_cluster": S("Candle Cluster", ["Three candles on an iron dish.", TOGGLE],
                        interaction=[(0, 0, 0, 0.7, 0.5)], light=12, sound="metal"),
    "street_lamp": S("Street Lamp", ["A two-block iron street lamp.", TOGGLE],
                     barriers=[(0, 0, 0)], light=15, light_at=(0, 1, 0), sound="metal"),
    "signpost": S("Signpost", ["A spruce post with two arrow boards."],
                  interaction=[(0, 0, 0, 1, 1.6)]),
    "wheelbarrow": S("Wheelbarrow", ["A wooden wheelbarrow full of hay."],
                     interaction=[(0, 0, 0, 1, 0.75), (1, 0, 0, 1, 0.75)]),
    "park_bench": S("Park Bench", ["Spruce slats on iron ends.", "Seats two."],
                    barriers=[(0, 0, 0), (1, 0, 0)], seats=[(0, 0.4, 0), (1, 0.4, 0)], sound="metal"),
    "notice_board": S("Notice Board", ["A spruce board with notes pinned up."],
                      interaction=[(0, 0, 0, 1, 1.6)]),
}
ORDER = ["street_lamp", "iron_lantern", "hanging_lantern", "candle_cluster",           # lights
         "signpost", "notice_board", "park_bench", "wheelbarrow",                       # outdoor & town
         "wooden_crate", "crate_stack", "oak_barrel", "grain_sacks", "apple_basket", "book_pile"]  # storage & clutter
assert sorted(ORDER) == sorted(SPEC)
SOUNDS = {"wood": "block.wood", "wool": "block.wool", "metal": "block.lantern"}


def _off(t):
    return ",".join(str(v) for v in t)


def nexo_yaml():
    out = {}
    for iid in ORDER:
        s = SPEC[iid]
        f = {"restricted_rotation": "VERY_STRICT", "preview_placement": True,
             "block_sounds": {f"{k}_sound": f"{SOUNDS[s['sound']]}.{k}" for k in ("place", "break", "hit", "step", "fall")},
             "limited_placing": {"floor": s["place"] == "floor", "wall": s["place"] == "wall", "roof": s["place"] == "roof"}}
        if s["barriers"]:
            f["hitbox"] = {"barriers": [_off(b) for b in s["barriers"]]}
        else:
            f["hitbox"] = {"interactions": [f"{x},{y},{z} {w:g},{h:g}" for x, y, z, w, h in s["interaction"]]}
        if s["seats"]:
            f["seats"] = [_off(x) for x in s["seats"]]
        if s["storage"]:
            f["storage"] = {"type": "STORAGE", "rows": s["storage"][0], "title": f"<{NAMEC}>{s['storage'][1]}",
                            "open_sound": "block.barrel.open", "close_sound": "block.barrel.close"}
        if s["light"]:
            f["lights"] = {"toggleable": True, "toggled_item_model": f"{NS}:{iid}_lit", "lights": [f"{_off(s.get('light_at', (0, 0, 0)))} {s['light']}"]}
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

Everyday props for any build: storage, clutter, lights and town pieces

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
