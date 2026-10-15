"""Night Lights mini showcase (Selling Test server): a small floating island with a reading nook.

Writes the datapack `nl_showcase` (namespace nlshow):
  nlshow:build      island + nook (solid blocks first, then fragile ones), all `strict`
  nlshow:furniture  10 display-only Night Lights pieces (tag nl_show) + light blocks
  nlshow:clear      removes everything inside the showcase box
  nlshow:arrive     tp to the path start, facing the nook
  nlshow:tick       arrival title, fireflies, soft mist
Local axes: x east, z south, y up. The visitor arrives from the north and walks south.
usage: python3 showcase.py <out dir>
"""
import json, math, os, sys, zlib

O = (200, 150, 400)                 # top grass layer of the island
OX, OY, OZ = O
V = {}                              # (x, y, z) local -> block state string


def put(x, y, z, b):
    V[(x, y, z)] = b


def box(x0, y0, z0, x1, y1, z1, b):
    for x in range(min(x0, x1), max(x0, x1) + 1):
        for y in range(min(y0, y1), max(y0, y1) + 1):
            for z in range(min(z0, z1), max(z0, z1) + 1):
                put(x, y, z, b)


def h(x, z, k=0):
    return (zlib.crc32(f"{x},{z},{k}".encode()) % 1000) / 1000.0


# ---------------------------------------------------------------- island
RX, RZ, CZ = 9.5, 11.5, -0.5


def inside(x, z):
    wob = 0.06 * math.sin(x * 1.3 + z * 0.7) + 0.05 * math.cos(z * 1.1 - x * 0.4)
    return ((x / RX) ** 2 + ((z - CZ) / RZ) ** 2) <= 1 + wob


def island():
    for x in range(-11, 12):
        for z in range(-13, 13):
            if not inside(x, z):
                continue
            d = math.sqrt((x / RX) ** 2 + ((z - CZ) / RZ) ** 2)
            depth = int(1 + (1 - min(d, 1)) ** 0.8 * 9 + h(x, z) * 2)
            for k in range(depth + 1):
                y = -k
                if k == 0:
                    b = "moss_block" if (d > 0.86 and h(x, z, 1) < 0.35) else "grass_block"
                elif k <= 2:
                    b = "dirt" if h(x, z, k) > 0.2 else "rooted_dirt"
                elif k == depth:
                    b = "deepslate" if depth > 6 else "tuff"
                else:
                    r = h(x, z, k + 7)
                    b = "stone" if r < 0.45 else ("andesite" if r < 0.7 else ("tuff" if r < 0.88 else "mossy_cobblestone"))
                put(x, y, z, b)
            if d > 0.75 and h(x, z, 9) < 0.22:                 # a few roots under the rim
                put(x, -depth - 1, z, "hanging_roots")


# ---------------------------------------------------------------- path and garden
def garden():
    for z in range(-12, 3):
        for x in (-1, 0, 1):
            if inside(x, z):
                put(x, 0, z, "dirt_path")
    for z in range(-11, 2, 2):                                  # stepping-stone edge
        for x in (-2, 2):
            if inside(x, z) and h(x, z, 3) < 0.5:
                put(x, 0, z, "moss_block")
    flowers = ["lily_of_the_valley", "azure_bluet", "allium", "short_grass", "short_grass", "fern"]
    for x in range(-9, 10):
        for z in range(-12, 12):
            if not inside(x, z) or V.get((x, 0, z)) not in ("grass_block", "moss_block"):
                continue
            if abs(x) <= 2 and z < 3:
                continue
            if -6 <= x <= 6 and 1 <= z <= 9:
                continue
            r = h(x, z, 4)
            if r < 0.30:
                put(x, 1, z, flowers[int(h(x, z, 5) * len(flowers))])
    # small cherry tree, west side
    tx, tz = -6, -3
    box(tx, 1, tz, tx, 4, tz, "cherry_log[axis=y]")
    put(tx + 1, 3, tz, "cherry_log[axis=x]")
    for dx in range(-2, 3):
        for dz in range(-2, 3):
            for dy in (4, 5, 6):
                r = abs(dx) + abs(dz) + (dy - 5) * 1.5
                if r <= 3.2 - (dy == 6) * 1.2 and h(tx + dx, tz + dz, dy) < 0.9:
                    if (dx, dz) != (0, 0) or dy > 4:
                        put(tx + dx, dy, tz + dz, "cherry_leaves[persistent=true]")
    put(tx - 1, 1, tz + 1, "pink_petals[flower_amount=4,facing=north]")
    put(tx + 1, 1, tz - 1, "pink_petals[flower_amount=3,facing=east]")
    # mossy boulder, east side
    for (x, y, z, b) in ((6, 1, -4, "mossy_cobblestone"), (7, 1, -4, "cobblestone"), (6, 1, -5, "mossy_cobblestone"),
                         (6, 2, -4, "moss_carpet"), (7, 2, -4, "moss_carpet"), (6, 2, -5, "moss_carpet")):
        put(x, y, z, b)
    # welcome sign at the path start
    put(2, 1, -10, "dark_oak_sign[rotation=8]")


# ---------------------------------------------------------------- reading nook
LOG, LOGX, PLANK = "stripped_dark_oak_log[axis=y]", "stripped_dark_oak_log[axis=x]", "dark_oak_planks"


def nook():
    # floor (sits in the grass layer)
    box(-4, 0, 3, 4, 0, 7, "deepslate_tiles")
    box(-3, 0, 3, 3, 0, 6, PLANK)
    box(-1, 1, 4, 1, 1, 5, "purple_carpet")
    # back wall z=7
    box(-4, 1, 7, 4, 1, 7, "polished_deepslate")
    box(-3, 2, 7, 3, 5, 7, "calcite")
    for x in (-4, 4):
        box(x, 1, 7, x, 5, 7, LOG)
        box(x, 1, 3, x, 4, 3, LOG)                              # front posts
    box(-1, 2, 7, 1, 4, 7, "purple_stained_glass_pane[east=true,west=true]")   # window
    box(-2, 2, 7, -2, 4, 7, "calcite")
    box(2, 2, 7, 2, 4, 7, "calcite")
    box(-1, 5, 7, 1, 5, 7, LOGX)                                # lintel
    put(0, 1, 7, "polished_deepslate")
    box(-1, 1, 8, 1, 1, 8, "dark_oak_trapdoor[facing=south,half=top,open=false]")   # sill outside (fragile)
    # side walls x=±4, z 4..6
    for x in (-4, 4):
        box(x, 1, 4, x, 1, 6, "polished_deepslate")
        box(x, 2, 4, x, 4, 6, "calcite")
        put(x, 3, 5, "purple_stained_glass_pane[north=true,south=true]")     # small side window
        box(x, 5, 4, x, 5, 6, "calcite")
        put(x, 6, 5, "calcite")                                 # gable point
        put(x, 6, 4, "calcite")
        put(x, 6, 6, "calcite")
    box(-4, 5, 3, 4, 5, 3, LOGX)                                # front beam over the opening
    # gable roof, ridge along x at z=5
    for x in range(-5, 6):
        put(x, 5, 2, "dark_oak_stairs[facing=south,half=bottom]")
        put(x, 6, 3, "dark_oak_stairs[facing=south,half=bottom]")
        put(x, 7, 4, "dark_oak_stairs[facing=south,half=bottom]")
        put(x, 7, 5, "dark_oak_slab[type=bottom]")
        put(x, 7, 6, "dark_oak_stairs[facing=north,half=bottom]")
        put(x, 6, 7, "dark_oak_stairs[facing=north,half=bottom]")
        put(x, 5, 8, "dark_oak_stairs[facing=north,half=bottom]")
    box(-3, 6, 4, 3, 6, 6, PLANK)                               # ceiling under the ridge
    # bench under the window, bookshelves as side tables
    for x in (-1, 0, 1):
        put(x, 1, 6, "dark_oak_stairs[facing=south,half=bottom]")
    put(-2, 1, 6, "chiseled_bookshelf[facing=north,slot_0_occupied=true,slot_1_occupied=true,slot_3_occupied=true,slot_5_occupied=true]")
    put(2, 1, 6, "chiseled_bookshelf[facing=north,slot_0_occupied=true,slot_2_occupied=true,slot_4_occupied=true,slot_5_occupied=true]")
    # potted plants on the front corners
    put(-3, 1, 3, "potted_fern")
    put(3, 1, 3, "potted_azure_bluet")


# ---------------------------------------------------------------- furniture
NS = "nightlights"
PIECES = [  # model, x, y, z, yaw, light level
    ("crescent_moon_sconce_lit", -3, 3, 6, 180, 12),
    ("crescent_moon_sconce_lit", 3, 3, 6, 180, 12),
    ("moon_jelly_jar_lit", -2, 2, 6, 180, 11),
    ("moon_jelly_jar_lit", 2, 2, 6, 180, 11),
    ("star_lamp_lit", -3, 1, 5, 180, 12),
    ("star_lamp_lit", 3, 1, 5, 180, 12),
    ("moon_jelly_jar_lit", -2, 1, -8, 180, 11),
    ("moon_jelly_jar_lit", 2, 1, -5, 180, 11),
    ("moon_jelly_jar_lit", -2, 1, -2, 180, 11),
    ("star_lamp_lit", 2, 1, -1, 180, 12),
]


def furniture():
    out = ["kill @e[type=item_display,tag=nl_show]"]
    for model, x, y, z, yaw, light in PIECES:
        iid = model.replace("_lit", "")
        out.append(
            f'summon minecraft:item_display {OX + x + 0.5} {OY + y + 0.5} {OZ + z + 0.5} '
            f'{{Rotation:[{float(yaw)}f,0f],item_display:"none",Tags:["nl_show"],Invulnerable:1b,'
            f'item:{{id:"minecraft:paper",count:1,components:{{"minecraft:item_model":"{NS}:{model}"}}}},'
            f'BukkitValues:{{"nexo:furniture":"{NS}_{iid}"}}}}')
        out.append(f"setblock {OX + x} {OY + y} {OZ + z} minecraft:light[level={light}]")
    return out


SIGN = ('data merge block {x} {y} {z} {{front_text:{{has_glowing_text:1b,color:"light_blue",messages:['
        '{{"text":""}},{{"text":"Night Lights","color":"#f2c97d"}},{{"text":"Mistbloom Studios","color":"#c9b8f0"}},{{"text":""}}]}}}}')

FRAGILE = ("lily_of_the_valley", "azure_bluet", "allium", "short_grass", "fern", "pink_petals", "potted_", "carpet",
           "sign", "hanging_roots", "trapdoor", "leaves", "pane")


def commands(group):
    return [f"setblock {OX + x} {OY + y} {OZ + z} minecraft:{b} strict" for (x, y, z), b in sorted(group.items(), key=lambda kv: (kv[0][1], kv[0][0], kv[0][2]))]


def build_all():
    V.clear()
    island(); garden(); nook()
    return V


BOX = (OX - 13, OY - 14, OZ - 15, OX + 13, OY + 10, OZ + 14)


def tick():
    x0, y0, z0, x1, y1, z1 = BOX
    sel = f"@a[x={x0},y={y0},z={z0},dx={x1 - x0},dy={y1 - y0 + 10},dz={z1 - z0}"
    return [
        f'execute as {sel},tag=!nl_in] run title @s times 20 70 30',
        f'execute as {sel},tag=!nl_in] run title @s subtitle {{"text":"a Mistbloom Studios showcase","color":"#9fb3d9"}}',
        f'execute as {sel},tag=!nl_in] run title @s title {{"text":"Night Lights","color":"#f2c97d"}}',
        f'tag {sel},tag=!nl_in] add nl_in',
        f'execute as @a[tag=nl_in] unless entity @s[x={x0},y={y0},z={z0},dx={x1 - x0},dy={y1 - y0 + 10},dz={z1 - z0}] run tag @s remove nl_in',
        f'execute if entity {sel}] positioned {OX} {OY + 2} {OZ} run particle minecraft:firefly ~ ~ ~ 8 1.5 10 0 1',
        f'execute if entity {sel}] positioned {OX} {OY + 1} {OZ - 2} run particle minecraft:cloud ~ ~ ~ 8 0.2 9 0.002 1',
    ]


def write(out):
    fdir = os.path.join(out, "data", "nlshow", "function")
    tdir = os.path.join(out, "data", "minecraft", "tags", "function")
    os.makedirs(fdir, exist_ok=True); os.makedirs(tdir, exist_ok=True)
    build_all()
    solid = {p: b for p, b in V.items() if not any(k in b for k in FRAGILE)}
    fragile = {p: b for p, b in V.items() if p not in solid}
    sx, sy, sz = OX + 2, OY + 1, OZ - 10
    x0, y0, z0, x1, y1, z1 = BOX
    files = {
        "build_0": [f"forceload add {x0} {z0} {x1} {z1}"] + commands(solid),
        "build_1": commands(fragile) + [SIGN.format(x=sx, y=sy, z=sz)],
        "build": ["function nlshow:build_0", "function nlshow:build_1"],
        "furniture": furniture(),
        "clear": ["kill @e[type=item_display,tag=nl_show]"] +
                 [f"fill {x0} {y} {z0} {x1} {y} {z1} minecraft:air strict" for y in range(y1, y0 - 1, -1)],
        "arrive": [f"tp @s {OX + 0.5} {OY + 1} {OZ - 10.5} 0 8"],
        "tick": tick(),
    }
    for n, lines in files.items():
        open(os.path.join(fdir, n + ".mcfunction"), "w").write("\n".join(lines) + "\n")
    json.dump({"values": ["nlshow:tick"]}, open(os.path.join(tdir, "tick.json"), "w"))
    json.dump({"pack": {"description": "Night Lights showcase - Mistbloom Studios", "pack_format": 94,
                        "min_format": 1, "max_format": 9999, "supported_formats": [1, 9999]}},
              open(os.path.join(out, "pack.mcmeta"), "w"), indent=1)
    print({n: len(l) for n, l in files.items()})


if __name__ == "__main__":
    write(sys.argv[1])
