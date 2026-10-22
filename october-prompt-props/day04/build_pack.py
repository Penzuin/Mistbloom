import json, os, re, shutil, zipfile
from PIL import Image
import p04_cactus

OUT = "Potted Cactus"
NAMES = ["pot_foot", "pot_body", "pot_rim", "stem", "crown", "left_elbow", "left_arm",
         "right_elbow", "right_arm", "bloom", "bud_a", "bud_b", "small_bud"]

def dump(o):
    s = json.dumps(o, indent="\t")
    return re.sub(r"\[\s+([-\d.,\s\"#a-z:/_]+?)\s+\]", lambda m: "[" + ", ".join(x.strip() for x in m.group(1).split(",")) + "]", s) + "\n"

m = p04_cactus.build()
assert m.check(14) == len(NAMES)
for e, n in zip(m.elements, NAMES):
    e["name"] = n
m.bake()
shutil.rmtree(OUT, ignore_errors=True)
a = f"{OUT}/Nexo/pack/assets/inkprops"
for d in ("models/furniture", "textures/furniture", "items"):
    os.makedirs(f"{a}/{d}")
Image.fromarray(m.atlas).save(f"{a}/textures/furniture/potted_cactus.png", optimize=True)
open(f"{a}/models/furniture/potted_cactus.json", "w").write(dump(m.to_json("inkprops:furniture/potted_cactus")))
open(f"{a}/items/potted_cactus.json", "w").write(dump({"model": {"type": "minecraft:model", "model": "inkprops:furniture/potted_cactus"}}))
os.makedirs(f"{OUT}/Nexo/items")
open(f"{OUT}/Nexo/items/inkprops_cactus.yml", "w").write("""# October Prompt Props - Mistbloom Studios
# One free piece for each day of the October drawing prompts.

inkprops_potted_cactus:
  itemname: <#7cbc4c>Potted Cactus
  lore:
  - <gray>A two armed cactus with a pink flower on top,
  - <gray>in a painted terracotta pot.
  - <dark_gray>October Prompt Props
  material: PAPER
  Components:
    item_model: inkprops:potted_cactus
  Mechanics:
    furniture:
      restricted_rotation: VERY_STRICT
      preview_placement: true
      block_sounds:
        place_sound: block.decorated_pot.place
        break_sound: block.decorated_pot.break
        hit_sound: block.decorated_pot.hit
        step_sound: block.decorated_pot.step
        fall_sound: block.decorated_pot.fall
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
open(f"{OUT}/README.txt", "w", newline="").write(crlf("""Potted Cactus - Mistbloom Studios
==================================================

A two armed cactus in a terracotta pot. Day 4 (Cactus) of October Prompt Props.

INSTALL - Drag and Drop (Nexo)
--------------
1. Copy Nexo/items/inkprops_cactus.yml into plugins/Nexo/items/
2. Copy the Nexo/pack/assets/ folder into plugins/Nexo/pack/assets/
3. Run /nexo reload all, then /nexo inventory to grab the pieces.

Requires Minecraft 1.21.4 or newer
"""))
open(f"{OUT}/LICENSE.txt", "w", newline="").write(crlf("""Potted Cactus - License
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
zp = "Potted-Cactus.zip"
if os.path.exists(zp): os.remove(zp)
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for root, _, files in os.walk(OUT):
        for f in sorted(files):
            p = os.path.join(root, f); z.write(p, p)
print(os.path.getsize(zp))
