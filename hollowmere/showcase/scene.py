"""Hollowmere showcase scene for the Selling Test server -> list of console commands.
Pieces are display-only item_display entities tagged hollowmere_showcase (remove with
/kill @e[tag=hollowmere_showcase]); the real furniture is the Nexo items."""
import json, random, sys
sys.path.insert(0, "/home/claude/hollow")
import importlib

CX, GY, CZ = -1450, 68, -340        # centre block column, ground block y
FLOORS, DYES = {}, {}
for mod in "hero3 harvest witchy graveyard critters market".split():
    for m in importlib.import_module(mod).all_models():
        FLOORS[m.name] = m.floor
        DYES[m.name] = m.dye

def W(dx, dz):                      # block world coords
    return CX + dx, CZ + dz

cmds, lights, placed = [], [], []
X1, X2, Z1, Z2 = W(-14, -13)[0], W(14, 15)[0], W(-14, -13)[1], W(14, 15)[1]

def fill(x1, y1, z1, x2, y2, z2, block, extra=""):
    cmds.append(f"fill {x1} {y1} {z1} {x2} {y2} {z2} {block}{extra}")

def setb(dx, y, dz, block):
    x, z = W(dx, dz); cmds.append(f"setblock {x} {y} {z} {block}")

def rect(dx1, dz1, dx2, dz2, y, block, extra=""):
    (x1, z1), (x2, z2) = W(dx1, dz1), W(dx2, dz2)
    fill(x1, y, z1, x2, y, z2, block, extra)

# ---------------------------------------------------------------- terrain
fill(X1, GY - 6, Z1, X2, GY - 1, Z2, "minecraft:dirt")
fill(X1, GY, Z1, X2, GY, Z2, "minecraft:grass_block")
fill(X1, GY + 1, Z1, X2, GY + 11, Z2, "minecraft:air")
fill(X1, GY + 12, Z1, X2, GY + 22, Z2, "minecraft:air")
rng = random.Random(31)
for _ in range(26):                                                   # patchy autumn ground
    dx, dz = rng.randint(-13, 13), rng.randint(-12, 14)
    rect(dx, dz, dx + rng.randint(0, 2), dz + rng.randint(0, 2), GY, rng.choice(
        ["minecraft:coarse_dirt", "minecraft:podzol", "minecraft:rooted_dirt"]), " replace minecraft:grass_block")
rect(6, 2, 13, 11, GY, "minecraft:podzol")                            # graveyard soil
rect(-13, 1, -7, 11, GY, "minecraft:moss_block")                      # witch's garden
rect(-1, 2, 1, 15, GY, "minecraft:dirt_path")                         # the lane
rect(-5, -5, 5, 4, GY, "minecraft:stone_bricks")                      # market square
for _ in range(30):
    setb(rng.randint(-5, 5), GY, rng.randint(-5, 4), rng.choice(
        ["minecraft:mossy_stone_bricks", "minecraft:cracked_stone_bricks", "minecraft:mossy_cobblestone"]))
rect(-1, 5, 1, 5, GY, "minecraft:stone_bricks"); rect(-1, 1, 1, 1, GY, "minecraft:mossy_stone_bricks")
rect(6, 6, 7, 6, GY, "minecraft:dirt_path"); rect(2, 6, 5, 6, GY, "minecraft:dirt_path")      # path to graveyard
rect(-6, 6, -2, 6, GY, "minecraft:dirt_path")                                                 # path to the witch

# hedge around the lot, gap at the entrance
L = "minecraft:dark_oak_leaves[persistent=true]"
for y in (GY + 1, GY + 2):
    rect(-14, -13, 14, -13, y, L); rect(-14, -13, -14, 15, y, L); rect(14, -13, 14, 15, y, L)
    rect(-14, 15, -3, 15, y, L); rect(3, 15, 14, 15, y, L)

# witch's hut corner (west wall + north wall)
for y in range(GY + 1, GY + 4):
    rect(-13, 1, -13, 11, y, "minecraft:spruce_planks"); rect(-13, 1, -8, 1, y, "minecraft:spruce_planks")
for dz in (1, 4, 8, 11):
    for y in range(GY + 1, GY + 5): setb(-13, y, dz, "minecraft:stripped_dark_oak_log")
setb(-8, GY + 1, 1, "minecraft:stripped_dark_oak_log"); setb(-8, GY + 2, 1, "minecraft:stripped_dark_oak_log")
setb(-8, GY + 3, 1, "minecraft:stripped_dark_oak_log")
rect(-13, 1, -13, 11, GY + 4, "minecraft:dark_oak_slab[type=bottom]")
setb(-13, GY + 2, 6, "minecraft:purple_stained_glass_pane[north=true,south=true]")
for (dx, dz) in ((-8, 8), (-8, 4), (-7, -8)):
    setb(dx, GY + 1, dz, "minecraft:barrel[facing=up]")
for dx in (-2, 2):                                                    # bunting posts
    for y in range(GY + 1, GY + 4): setb(dx, y, 9, "minecraft:dark_oak_fence")
for (dx, dz) in ((4, -11), (-10, -11), (12, 13), (-12, 13)):          # a few dry bushes
    setb(dx, GY + 1, dz, "minecraft:dead_bush")
for (dx, dz) in ((9, 11), (12, 3), (-11, -3), (10, -4)):
    setb(dx, GY + 1, dz, "minecraft:carved_pumpkin[facing=south]")

# ---------------------------------------------------------------- furniture
def put(name, dx, dz, yaw=0, y=None, light=0, ly=0):
    by = GY + 1 if y is None else y
    x, z = W(dx, dz)
    ey = by + 0.5 - FLOORS[name] / 16
    comps = {"minecraft:item_model": f"hollowmere:{name}"}
    if DYES[name]:
        r, g, b = DYES[name]; comps["minecraft:dyed_color"] = (r << 16) | (g << 8) | b
    item = json.dumps({"id": "minecraft:paper", "count": 1, "components": comps}, separators=(",", ":"))
    cmds.append(f'summon minecraft:item_display {x + 0.5} {ey:g} {z + 0.5} '
                f'{{Tags:["hollowmere_showcase"],Rotation:[{yaw}f,0f],item_display:"none",item:{item}}}')
    placed.append(name)
    if light:
        lights.append((x, int(by) + ly, z, light))

# entrance and lane (visitors walk in from the south, looking north)
put("hollow_arch", 0, 13, 0, light=13, ly=2)
put("hanging_spider", -1, 13, 0, y=GY + 1.4)
put("welcome_sign", -3, 13, 0, light=10, ly=3)
put("pumpkin_pile", 3, 13, 0)
put("jack_o_lantern_lit", 2, 14, 0, light=14, ly=1)
put("candy_bucket", 2, 11, 90)
put("jack_o_lantern_lit", -2, 9, 0, y=GY + 4, light=14, ly=1)
put("jack_o_lantern_lit", 2, 9, 0, y=GY + 4, light=14, ly=1)
put("bat_bunting", 0, 9, 0, y=GY + 3)
put("pumpkin_lamp_lit", -3, 7, 180, light=15, ly=3)
put("pumpkin_lamp_lit", 3, 3, 0, light=15, ly=3)
put("hay_bale_seat", -2, 4, -90)
put("black_cat", -2, 4, -90, y=GY + 1 + 11.5 / 16)
put("crow_post", 3, 8, 90)

# market square
put("cauldron_lit", 0, -1, 0, light=12, ly=1)
put("skull_candle", 2, -2, 90, light=12)
put("candle_cluster", -2, 0, -90, light=12)
put("potion_stall", -6, -1, -90, light=10, ly=1)
put("potion_stall_moss", 6, -1, 90, light=10, ly=1)
put("potion_stall_ember", 0, -7, 0, light=10, ly=1)
put("jack_o_lantern", -3, 3, 0)
put("cushion_stool", 2, 2, 90)

# graveyard (east)
for dx in range(7, 13):
    put("iron_fence", dx, 2, 0)
for dz in (3, 4, 5, 7, 8, 9, 10):
    put("iron_fence", 6, dz, 90)
put("tombstone", 9, 4, 90, light=8, ly=1)
put("tombstone_cross", 9, 7, 90)
put("tombstone", 11, 6, 90, light=8, ly=1)
put("coffin", 10, 9, 0)
put("ghost_lantern_lit", 7, 3, 90, light=13)
put("ghost_lantern_lit", 12, 10, 90, light=13)
put("mushroom_ring", 12, 4, 0, light=7)
put("dead_tree", 12, 7, 90, light=12, ly=2)
put("owl_perch", 8, 10, 90)

# witch's corner (west)
put("spellbook_lectern", -10, 5, -90, light=8, ly=1)
put("witch_hat_stand", -10, 8, -90)
put("cushion_stool", -9, 6, -90)
put("crystal_ball", -8, 8, -90, y=GY + 2, light=9)
put("potion_trio", -8, 4, -90, y=GY + 2, light=6)
put("potion_shelf", -12, 6, -90, y=GY + 2)
put("harvest_wreath", -12, 9, -90, y=GY + 2)
put("cobweb_corner", -12, 2, -90, y=GY + 2)
put("witch_broom", -12, 10, -90)
put("cauldron", -11, 3, -90)
put("ghost_lantern", -9, 10, -90)

# harvest corner (north)
put("pumpkin_cart", -4, -9, 0)
put("haystack", 5, -10, 0)
put("scarecrow", 9, -9, 0)
put("cider_cask", 3, -10, 0)
put("caramel_apple_tray", -7, -8, 0, y=GY + 2)
put("gourd_basket", -8, -10, 0)
put("pumpkin_lamp", -11, -8, 0)

for (x, y, z, lv) in lights:
    cmds.append(f"setblock {x} {y} {z} minecraft:light[level={lv}]")

if __name__ == "__main__":
    allm = set(FLOORS)
    print("missing:", sorted(allm - set(placed)), file=sys.stderr)
    print(len(cmds), "commands", file=sys.stderr)
    json.dump(cmds, open("/home/claude/hollow/showcase/cmds.json", "w"))
