import json, os, re, shutil, zipfile
from PIL import Image
import p03_cottage

OUT = "Tiny Cottage"
NAMES = ["grass", "foundation", "walls", "post_1", "post_2", "post_3", "post_4", "top_plate", "gable",
         "roof_front", "roof_back", "ridge", "chimney", "chimney_cap", "door", "door_hood", "step",
         "flower_box_1", "flower_box_2", "blooms_1", "blooms_2", "bush_1", "bush_2", "bush_top", "ivy"]

def dump(o):
    s = json.dumps(o, indent="\t")
    return re.sub(r"\[\s+([-\d.,\s\"#a-z:/_]+?)\s+\]", lambda m: "[" + ", ".join(x.strip() for x in m.group(1).split(",")) + "]", s) + "\n"

m = p03_cottage.build()
assert m.check(25) == len(NAMES)
for e, n in zip(m.elements, NAMES):
    e["name"] = n
m.bake()
shutil.rmtree(OUT, ignore_errors=True)
a = f"{OUT}/Nexo/pack/assets/inkprops"
for d in ("models/furniture", "textures/furniture", "items"):
    os.makedirs(f"{a}/{d}")
Image.fromarray(m.atlas).save(f"{a}/textures/furniture/tiny_cottage.png", optimize=True)
open(f"{a}/models/furniture/tiny_cottage.json", "w").write(dump(m.to_json("inkprops:furniture/tiny_cottage")))
open(f"{a}/items/tiny_cottage.json", "w").write(dump({"model": {"type": "minecraft:model", "model": "inkprops:furniture/tiny_cottage"}}))
os.makedirs(f"{OUT}/Nexo/items")
open(f"{OUT}/Nexo/items/inkprops_cottage.yml", "w").write("""# October Prompt Props - Mistbloom Studios
# One free piece for each day of the October drawing prompts.

inkprops_tiny_cottage:
  itemname: <#dc7452>Tiny Cottage
  lore:
  - <gray>A thatched cottage with a teal door and flower boxes.
  - <dark_gray>October Prompt Props
  material: PAPER
  Components:
    item_model: inkprops:tiny_cottage
  Mechanics:
    furniture:
      restricted_rotation: VERY_STRICT
      preview_placement: true
      block_sounds:
        place_sound: block.wood.place
        break_sound: block.wood.break
        hit_sound: block.wood.hit
        step_sound: block.wood.step
        fall_sound: block.wood.fall
      limited_placing:
        floor: true
        wall: false
        roof: false
      hitbox:
        barriers:
        - 0,0,0
""")
crlf = lambda s: s.replace("\r\n", "\n").replace("\n", "\r\n")
open(f"{OUT}/README.txt", "w", newline="").write(crlf("""Tiny Cottage - Mistbloom Studios
==================================================

A little thatched cottage with a teal door and flower boxes. Day 3 (Miniature) of October Prompt Props.

INSTALL - Drag and Drop (Nexo)
--------------
1. Copy Nexo/items/inkprops_cottage.yml into plugins/Nexo/items/
2. Copy the Nexo/pack/assets/ folder into plugins/Nexo/pack/assets/
3. Run /nexo reload all, then /nexo inventory to grab the pieces.

Requires Minecraft 1.21.4 or newer
"""))
open(f"{OUT}/LICENSE.txt", "w", newline="").write(crlf("""Tiny Cottage - License
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
zp = "listing/Tiny-Cottage.zip"
if os.path.exists(zp): os.remove(zp)
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for root, _, files in os.walk(OUT):
        for f in sorted(files):
            p = os.path.join(root, f); z.write(p, p)
print(os.path.getsize(zp))
