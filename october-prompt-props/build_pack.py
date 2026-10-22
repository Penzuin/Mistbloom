import json, os, re, shutil, zipfile
from PIL import Image
import p02_chalice

OUT = "Ancient Chalice"
NAMES = ["plinth", "step", "pedestal", "cornice", "cloth_top", "cloth_front", "moss", "ivy",
         "cup_foot", "cup_stem", "cup_base", "cup_bowl", "cup_rim", "ruby"]

def dump(o):
    s = json.dumps(o, indent="\t")
    return re.sub(r"\[\s+([-\d.,\s\"#a-z:/_]+?)\s+\]", lambda m: "[" + ", ".join(x.strip() for x in m.group(1).split(",")) + "]", s) + "\n"

m = p02_chalice.build()
assert m.check(14) == len(NAMES)
for e, n in zip(m.elements, NAMES):
    e["name"] = n
m.bake()
shutil.rmtree(OUT, ignore_errors=True)
a = f"{OUT}/Nexo/pack/assets/inkprops"
for d in ("models/furniture", "textures/furniture", "items"):
    os.makedirs(f"{a}/{d}")
Image.fromarray(m.atlas).save(f"{a}/textures/furniture/ancient_chalice.png", optimize=True)
open(f"{a}/models/furniture/ancient_chalice.json", "w").write(dump(m.to_json("inkprops:furniture/ancient_chalice")))
open(f"{a}/items/ancient_chalice.json", "w").write(dump({"model": {"type": "minecraft:model", "model": "inkprops:furniture/ancient_chalice"}}))
os.makedirs(f"{OUT}/Nexo/items")
open(f"{OUT}/Nexo/items/inkprops_chalice.yml", "w").write("""# October Prompt Props - Mistbloom Studios
# One free piece for each day of the October drawing prompts.

inkprops_ancient_chalice:
  itemname: <#f0aa22>Ancient Chalice
  lore:
  - <gray>A gold chalice with a ruby, left on a mossy stone pedestal.
  - <dark_gray>October Prompt Props
  material: PAPER
  Components:
    item_model: inkprops:ancient_chalice
  Mechanics:
    furniture:
      restricted_rotation: VERY_STRICT
      preview_placement: true
      block_sounds:
        place_sound: block.stone.place
        break_sound: block.stone.break
        hit_sound: block.stone.hit
        step_sound: block.stone.step
        fall_sound: block.stone.fall
      limited_placing:
        floor: true
        wall: false
        roof: false
      hitbox:
        barriers:
        - 0,0,0
        - 0,1,0
""")
crlf = lambda s: s.replace("\r\n", "\n").replace("\n", "\r\n")
open(f"{OUT}/README.txt", "w", newline="").write(crlf("""Ancient Chalice - Mistbloom Studios
==================================================

A gold chalice on a mossy stone pedestal. Day 2 (Relic) of October Prompt Props.

INSTALL - Drag and Drop (Nexo)
--------------
1. Copy Nexo/items/inkprops_chalice.yml into plugins/Nexo/items/
2. Copy the Nexo/pack/assets/ folder into plugins/Nexo/pack/assets/
3. Run /nexo reload all, then /nexo inventory to grab the pieces.

Requires Minecraft 1.21.4 or newer
"""))
open(f"{OUT}/LICENSE.txt", "w", newline="").write(crlf("""Ancient Chalice - License
Copyright (c) 2026 Mistbloom Studios. All rights reserved.

This pack is free. Downloading it gives you a non-exclusive, non-transferable license to:
  - use the model, texture and config on Minecraft servers you own or manage
    (any number of servers, including networks and monetised servers);
  - edit, recolor and adapt them for those servers;
  - show them in screenshots, videos and streams.

You may not:
  - resell, share, re-upload or redistribute the files, edited or not,
    on their own or as part of another pack;
  - claim the work as your own.

Questions: discord.gg/QUJ8ntw7eS
"""))
zp = "Ancient-Chalice.zip"
if os.path.exists(zp): os.remove(zp)
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for root, _, files in os.walk(OUT):
        for f in sorted(files):
            p = os.path.join(root, f); z.write(p, p)
print(open(zp,"rb") and os.path.getsize(zp))
