"""Moonlit Ballroom in-game showcase: generates a datapack that builds a floating haunted manor
with an immersive ballroom (Selling Test server, Minecraft 26.2) and places the pack's furniture.

World origin O = (100, 210, 100). Visitors arrive at the south end of the island (low z) and walk
toward +z (south) through the gate, the foyer gallery and into the ballroom.
"""
import json, math, os, random, shutil

OX, OY, OZ = 100, 210, 100
NS = "moonball"
rng = random.Random(7)
cmds = []          # build function
place = []         # furniture function


def W(x, y, z):
    return f"{OX + x} {OY + y} {OZ + z}"


def fill(x1, y1, z1, x2, y2, z2, block, mode=""):
    xa, xb = sorted((x1, x2)); ya, yb = sorted((y1, y2)); za, zb = sorted((z1, z2))
    # split along z so no fill exceeds 32768 blocks
    vol_per_z = (xb - xa + 1) * (yb - ya + 1)
    step = max(1, 32000 // vol_per_z)
    z = za
    while z <= zb:
        z2_ = min(zb, z + step - 1)
        cmds.append(f"fill {W(xa, ya, z)} {W(xb, yb, z2_)} {block}{(' ' + mode) if mode else ''}")
        z = z2_ + 1


def setb(x, y, z, block):
    cmds.append(f"setblock {W(x, y, z)} {block}")


# ===================================================================== island
CX, CZ, RX, RZ = 32, 46, 36, 54

def island():
    for x in range(CX - RX - 2, CX + RX + 3):
        for z in range(CZ - RZ - 2, CZ + RZ + 3):
            d = math.hypot((x - CX) / RX, (z - CZ) / RZ)
            n = 0.08 * math.sin(x * 0.7) + 0.06 * math.cos(z * 0.5) + 0.04 * math.sin((x + z) * 1.3)
            if d > 1 + n:
                continue
            depth = int(3 + 22 * max(0.0, 1 - d) ** 0.9 + rng.randint(0, 2))
            top = "minecraft:grass_block"
            r = rng.random()
            if r < 0.10:
                top = "minecraft:podzol"
            elif r < 0.16:
                top = "minecraft:coarse_dirt"
            elif r < 0.20:
                top = "minecraft:moss_block"
            cmds.append(f"fill {W(x, -depth, z)} {W(x, -4, z)} minecraft:{'deepslate' if depth > 12 else 'stone'}")
            cmds.append(f"fill {W(x, -3, z)} {W(x, -1, z)} minecraft:dirt")
            setb(x, 0, z, top)
            if depth > 14 and rng.random() < 0.25:
                setb(x, -depth - 1, z, "minecraft:pointed_dripstone[vertical_direction=down,thickness=tip]")
            elif depth > 8 and rng.random() < 0.12:
                setb(x, -depth - 1, z, "minecraft:hanging_roots")


# ===================================================================== gardens & path
def dead_tree(x, z, h):
    fill(x, 1, z, x, h, z, "minecraft:stripped_dark_oak_log")
    for dx, dz, L in ((1, 0, 3), (-1, 0, 2), (0, 1, 2), (0, -1, 3)):
        y = h - rng.randint(0, 2)
        for k in range(1, L + 1):
            setb(x + dx * k, y + (1 if k == L else 0), z + dz * k, "minecraft:dark_oak_fence")
    setb(x + 1, h - 3, z, "minecraft:cobweb")


def gardens():
    # path from the arrival point (z=-6) to the door (z=24)
    fill(29, 0, -6, 35, 0, 23, "minecraft:gravel")
    fill(30, 0, -6, 34, 0, 23, "minecraft:mossy_cobblestone")
    fill(31, 0, -6, 33, 0, 23, "minecraft:cobblestone")
    for z in range(-6, 24, 2):
        setb(rng.choice((30, 34)), 0, z, "minecraft:moss_block")
    # low garden walls with posts along the path
    for side in (27, 37):
        fill(side, 1, -4, side, 1, 22, "minecraft:mossy_stone_brick_wall")
        for z in (-4, 2, 8, 14, 20):
            fill(side, 1, z, side, 2, z, "minecraft:polished_deepslate")
    # gate: two tall pillars with an arch of iron bars and hanging soul lanterns
    for x in (28, 36):
        fill(x, 1, 6, x, 6, 6, "minecraft:polished_deepslate")
        setb(x, 7, 6, "minecraft:chiseled_deepslate")
        setb(x, 8, 6, "minecraft:soul_lantern")
    fill(29, 7, 6, 35, 7, 6, "minecraft:iron_bars")
    fill(30, 8, 6, 34, 8, 6, "minecraft:iron_bars")
    setb(32, 6, 6, "minecraft:chain")
    setb(32, 5, 6, "minecraft:soul_lantern[hanging=true]")
    setb(29, 1, 6, "minecraft:iron_bars"); setb(29, 2, 6, "minecraft:iron_bars")
    setb(35, 1, 6, "minecraft:iron_bars"); setb(35, 2, 6, "minecraft:iron_bars")
    # dead trees, pumpkins and graves on the lawns
    for x, z, h in ((12, -2, 8), (52, 4, 9), (16, 14, 7), (49, 17, 8), (8, 28, 7), (58, 34, 8), (6, 70, 8), (60, 80, 7)):
        dead_tree(x, z, h)
    for x, z in ((24, 0), (40, 2), (22, 12), (42, 15), (20, 20), (44, 22), (26, -3), (38, -5)):
        setb(x, 1, z, rng.choice(["minecraft:jack_o_lantern[facing=north]", "minecraft:carved_pumpkin[facing=north]",
                                  "minecraft:pumpkin"]))
    for x, z in ((10, 6), (14, 8), (18, 4), (50, 10), (54, 12), (46, 6)):
        setb(x, 1, z, "minecraft:mossy_stone_brick_wall")
        setb(x, 2, z, "minecraft:stone_brick_slab")
        setb(x, 0, z + 1, "minecraft:podzol")
    for x, z in ((22, 6), (42, 9), (15, 18), (50, 20), (24, 18), (40, 19)):
        setb(x, 1, z, rng.choice(["minecraft:dead_bush", "minecraft:fern", "minecraft:azure_bluet", "minecraft:lily_of_the_valley"]))


# ===================================================================== manor shell
X0, X1, Z0, Z1 = 6, 58, 24, 92        # outer walls
WALL_H = 18
MIDX = 32

def manor_shell():
    # floor
    fill(X0, 0, Z0, X1, 0, Z1, "minecraft:polished_deepslate")
    # walls
    for (a, b, c, d) in ((X0, Z0, X1, Z0), (X0, Z1, X1, Z1), (X0, Z0, X0, Z1), (X1, Z0, X1, Z1)):
        fill(a, 1, b, c, 2, d, "minecraft:deepslate_bricks")
        fill(a, 3, b, c, WALL_H - 1, d, "minecraft:dark_oak_planks")
        fill(a, WALL_H, b, c, WALL_H, d, "minecraft:deepslate_tiles")
    # timber columns every 6 blocks on the long walls, at the corners and on the front
    for z in range(Z0, Z1 + 1, 6):
        for x in (X0, X1):
            fill(x, 3, z, x, WALL_H - 1, z, "minecraft:stripped_dark_oak_log")
    for x in range(X0, X1 + 1, 6):
        for z in (Z0, Z1):
            fill(x, 3, z, x, WALL_H - 1, z, "minecraft:stripped_dark_oak_log")
    # tall lancet windows (violet glass) between the columns on the long walls
    for z in range(Z0 + 3, Z1 - 1, 6):
        for x in (X0, X1):
            fill(x, 4, z - 1, x, 13, z + 1, "minecraft:purple_stained_glass_pane")
            setb(x, 14, z, "minecraft:purple_stained_glass_pane")
    # pitched roof of deepslate tile stairs, stepped wooden vault underneath
    half = (X1 - X0) // 2
    for i in range(half + 1):
        y = WALL_H + 1 + i
        fill(X0 - 1 + i, y, Z0 - 1, X0 - 1 + i, y, Z1 + 1, "minecraft:deepslate_tile_stairs[facing=east]")
        fill(X1 + 1 - i, y, Z0 - 1, X1 + 1 - i, y, Z1 + 1, "minecraft:deepslate_tile_stairs[facing=west]")
        if i < half:
            fill(X0 + i, y, Z0, X0 + i, y, Z1, "minecraft:dark_oak_planks")
            fill(X1 - i, y, Z0, X1 - i, y, Z1, "minecraft:dark_oak_planks")
    fill(MIDX, WALL_H + 1 + half, Z0 - 1, MIDX, WALL_H + 1 + half, Z1 + 1, "minecraft:deepslate_tile_slab")
    # gable ends
    for z in (Z0, Z1):
        for i in range(half):
            y = WALL_H + 1 + i
            fill(X0 + i + 1, y, z, X1 - i - 1, y, z, "minecraft:deepslate_bricks")
    # front gable: round violet rose window
    for dy in range(-4, 5):
        for dx in range(-4, 5):
            r = math.hypot(dx, dy)
            if r <= 4.3:
                blk = "minecraft:magenta_stained_glass" if (r < 1.5 or 2.8 < r < 3.3) else "minecraft:purple_stained_glass"
                setb(MIDX + dx, WALL_H + 9 + dy, Z0, blk)
    # front porch: steps, a deep arch and the doorway
    fill(28, 0, Z0 - 3, 36, 0, Z0 - 1, "minecraft:polished_deepslate")
    fill(29, 1, Z0 - 2, 35, 1, Z0 - 2, "minecraft:deepslate_tile_slab")
    fill(30, 1, Z0, 34, 5, Z0, "minecraft:air")
    fill(29, 6, Z0, 35, 6, Z0, "minecraft:chiseled_deepslate")
    setb(30, 5, Z0, "minecraft:deepslate_tile_stairs[facing=east,half=top]")
    setb(34, 5, Z0, "minecraft:deepslate_tile_stairs[facing=west,half=top]")
    for x in (28, 36):
        fill(x, 1, Z0 - 1, x, 7, Z0 - 1, "minecraft:polished_deepslate")
        setb(x, 8, Z0 - 1, "minecraft:soul_lantern")
    fill(29, 1, Z0 + 1, 35, 1, Z0 + 1, "minecraft:air")
    # four corner towers with pointed caps and a lantern on top
    for tx, tz in ((X0, Z0), (X1, Z0), (X0, Z1), (X1, Z1)):
        x0, z0 = tx - 2, tz - 2
        fill(x0, 1, z0, x0 + 4, 24, z0 + 4, "minecraft:deepslate_bricks", "outline")
        fill(x0, 10, z0 + 2, x0, 14, z0 + 2, "minecraft:purple_stained_glass_pane")
        fill(x0 + 4, 10, z0 + 2, x0 + 4, 14, z0 + 2, "minecraft:purple_stained_glass_pane")
        fill(x0 + 2, 10, z0, x0 + 2, 14, z0, "minecraft:purple_stained_glass_pane")
        fill(x0 + 2, 10, z0 + 4, x0 + 2, 14, z0 + 4, "minecraft:purple_stained_glass_pane")
        for k in range(3):
            fill(x0 + k, 25 + k, z0 + k, x0 + 4 - k, 25 + k, z0 + 4 - k, "minecraft:deepslate_tiles")
        setb(x0 + 2, 28, z0 + 2, "minecraft:deepslate_tile_wall")
        setb(x0 + 2, 29, z0 + 2, "minecraft:soul_lantern")
        setb(x0 + 2, 23, z0 + 2, "minecraft:light[level=12]")


# ===================================================================== foyer (z 25..36)
FZ0, FZ1 = Z0 + 1, 36

def foyer():
    for x in range(X0 + 1, X1):
        for z in range(FZ0, FZ1 + 1):
            if (x + z) % 2 == 0:
                setb(x, 0, z, "minecraft:polished_blackstone")
    fill(X0 + 1, 0, FZ0, X1 - 1, 0, FZ1, "minecraft:calcite", "replace minecraft:polished_deepslate")
    fill(X0 + 1, 12, FZ0, X1 - 1, 12, FZ1, "minecraft:dark_oak_planks")            # low foyer ceiling
    fill(X0 + 1, 11, FZ0, X1 - 1, 11, FZ0, "minecraft:dark_oak_slab[type=top]")
    # wall dividing foyer and ballroom, with a wide arch
    fill(X0 + 1, 1, FZ1 + 1, X1 - 1, 11, FZ1 + 1, "minecraft:dark_oak_planks")
    fill(X0 + 1, 1, FZ1 + 1, X1 - 1, 2, FZ1 + 1, "minecraft:deepslate_bricks")
    fill(28, 1, FZ1 + 1, 36, 8, FZ1 + 1, "minecraft:air")
    fill(27, 9, FZ1 + 1, 37, 9, FZ1 + 1, "minecraft:chiseled_deepslate")
    setb(28, 8, FZ1 + 1, "minecraft:deepslate_tile_stairs[facing=east,half=top]")
    setb(36, 8, FZ1 + 1, "minecraft:deepslate_tile_stairs[facing=west,half=top]")
    # runner carpet
    fill(31, 1, FZ0 + 1, 33, 1, FZ1 + 1, "minecraft:purple_carpet")
    # wainscot along the side walls + gallery spots
    for x in (X0 + 1, X1 - 1):
        fill(x, 1, FZ0, x, 3, FZ1, "minecraft:dark_oak_trapdoor[facing=%s,half=bottom,open=true]" % ("east" if x < MIDX else "west"))
    # hanging chandeliers in the foyer
    for x in (20, 44):
        fill(x, 9, 30, x, 11, 30, "minecraft:chain")
        setb(x, 8, 30, "minecraft:soul_lantern[hanging=true]")
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            setb(x + dx, 9, 30 + dz, "minecraft:end_rod[facing=up]")
    # welcome sign above the inner arch and info signs by the door
    for x, y, lines in ((24, 3, ['"Welcome to the"', '"Moonlit Ballroom"', '"by Mistbloom"', '"Studios"']),
                        (40, 3, ['"Friendly ghosts"', '"6 animated pieces"', '"Plain Nexo"', '"No add-ons needed"'])):
        msg = ",".join(f'{{"text":{l},"color":"#f2c97d"}}' for l in lines)
        setb(x, y, FZ0, "minecraft:dark_oak_wall_sign[facing=south]{front_text:{has_glowing_text:1b,color:\"yellow\",messages:[%s]}}" % msg)
    # cobwebs in the corners and soft light
    for x, z in ((X0 + 1, FZ0), (X1 - 1, FZ0), (X0 + 1, FZ1), (X1 - 1, FZ1)):
        setb(x, 10, z, "minecraft:cobweb"); setb(x, 9, z, "minecraft:cobweb")
    for x in range(12, 56, 10):
        setb(x, 6, 30, "minecraft:light[level=10]")


# ===================================================================== ballroom (z 38..91)
BZ0, BZ1 = FZ1 + 2, Z1 - 1
DANCE = (32, 62)

def ballroom():
    # floor: dark parquet, amethyst ring, dark checker inside, a glowing star at the centre
    for x in range(X0 + 1, X1):
        for z in range(BZ0, BZ1 + 1):
            d = math.hypot(x - DANCE[0], z - DANCE[1])
            if d <= 0.9:
                b = "minecraft:sea_lantern"
            elif d < 12.5:
                b = "minecraft:polished_blackstone" if (x + z) % 2 else "minecraft:deepslate_tiles"
            elif d < 14.0:
                b = "minecraft:amethyst_block"
            else:
                b = "minecraft:dark_oak_planks" if ((x // 2 + z) % 2) else "minecraft:spruce_planks"
            if b != "minecraft:polished_deepslate":
                setb(x, 0, z, b)
    for a in range(8):                                          # star points
        t = a * math.pi / 4
        for r in (1.6, 2.6):
            setb(round(DANCE[0] + r * math.cos(t)), 0, round(DANCE[1] + r * math.sin(t)), "minecraft:amethyst_block")
    # pillars and balconies along both long walls
    for z in range(BZ0 + 2, BZ1 - 6, 8):
        for x in (12, 52):
            fill(x, 1, z, x, 17, z, "minecraft:deepslate_tiles")
            setb(x, 1, z, "minecraft:chiseled_deepslate"); setb(x, 17, z, "minecraft:chiseled_deepslate")
            setb(x, 12, z + (1 if x < MIDX else 1), "minecraft:soul_lantern")
    for (xa, xb, rail) in ((X0 + 1, 11, 12), (53, X1 - 1, 52)):
        fill(xa, 8, BZ0, xb, 8, 75, "minecraft:dark_oak_slab[type=top]")
        fill(rail, 9, BZ0, rail, 9, 75, "minecraft:dark_oak_fence", "replace minecraft:air")
    # stairs up to the balconies: rise toward -z from z=83 (floor) to z=76, landing on the balcony at z=75
    for i in range(8):
        z = 83 - i
        fill(X0 + 1, i + 1, z, X0 + 3, i + 1, z, "minecraft:dark_oak_stairs[facing=north]")
        fill(X1 - 3, i + 1, z, X1 - 1, i + 1, z, "minecraft:dark_oak_stairs[facing=north]")
        if i:
            fill(X0 + 1, 1, z, X0 + 3, i, z, "minecraft:dark_oak_planks")
            fill(X1 - 3, 1, z, X1 - 1, i, z, "minecraft:dark_oak_planks")
    # three chandeliers on long chains from the vault
    for cz in (50, 64, 78):
        fill(MIDX, 14, cz, MIDX, 44, cz, "minecraft:chain")
        setb(MIDX, 13, cz, "minecraft:soul_lantern[hanging=true]")
        for k in range(8):
            t = k * math.pi / 4
            x, z = MIDX + round(3 * math.cos(t)), cz + round(3 * math.sin(t))
            setb(x, 15, z, "minecraft:chain")
            setb(x, 14, z, "minecraft:soul_lantern[hanging=true]")
        fill(MIDX - 3, 16, cz, MIDX + 3, 16, cz, "minecraft:dark_oak_fence")
        fill(MIDX, 16, cz - 3, MIDX, 16, cz + 3, "minecraft:dark_oak_fence")
        setb(MIDX, 16, cz, "minecraft:chain")
    # stage at the far end
    fill(16, 1, 82, 48, 1, BZ1, "minecraft:dark_oak_planks")
    fill(16, 1, 82, 48, 1, 82, "minecraft:dark_oak_stairs[facing=north]")
    fill(16, 2, 91, 48, 9, 91, "minecraft:purple_wool")                      # velvet backdrop
    for x in range(16, 49, 2):
        fill(x, 2, 90, x, 9, 90, "minecraft:purple_wool")                      # pleats
    fill(16, 10, 90, 48, 10, 91, "minecraft:dark_oak_slab[type=top]")
    # the glowing moon above the stage
    for dy in range(-7, 8):
        for dx in range(-7, 8):
            r = math.hypot(dx, dy)
            if r <= 7.2:
                b = "minecraft:sea_lantern"
                if (dx + 2) ** 2 + (dy - 2) ** 2 <= 3 or (dx - 3) ** 2 + (dy + 2) ** 2 <= 2:
                    b = "minecraft:light_gray_concrete"
                setb(MIDX + dx, 18 + dy, 91, b)
    # side tables for the lanterns, banquet benches
    for z in (46, 54, 70, 78):
        for x in (14, 50):
            setb(x, 1, z, "minecraft:dark_oak_fence")
    # cobwebs high in the corners, soft invisible light
    for x, z in ((X0 + 1, BZ0), (X1 - 1, BZ0), (X0 + 1, BZ1), (X1 - 1, BZ1)):
        for y in (15, 16, 17):
            setb(x, y, z, "minecraft:cobweb")
    for x in range(14, 52, 9):
        for z in range(44, 88, 9):
            setb(x, 5, z, "minecraft:light[level=9]")


# ===================================================================== furniture
def furn(iid, x, y, z, yaw, model=None):
    """Spawn Nexo furniture the way Nexo stores it: an item display at the block centre with the
    nexo:furniture key, the item model, no display transform."""
    model = model or iid
    place.append(
        f'summon minecraft:item_display {OX + x + 0.5} {OY + y + 0.5} {OZ + z + 0.5} '
        f'{{Rotation:[{float(yaw)}f,0f],item_display:"none",Tags:["moonball_show"],Invulnerable:1b,'
        f'item:{{id:"minecraft:paper",count:1,components:{{"minecraft:item_model":"{NS}:{model}"}}}},'
        f'BukkitValues:{{"nexo:furniture":"{NS}_{iid}"}}}}')

# yaw: 0 -> front faces north (-z, toward arriving visitors), 180 -> faces south, 90 -> east, 270 -> west
def furniture():
    place.append("minecraft:kill @e[type=item_display,tag=moonball_show]")
    # path lanterns on the wall posts
    for z in (2, 8, 14, 20):
        furn("ghost_lantern", 27, 3, z, 270, "ghost_lantern_lit")
        furn("ghost_lantern", 37, 3, z, 90, "ghost_lantern_lit")
    # foyer: candelabras and the portrait gallery
    furn("floating_candelabra", 24, 1, 30, 0, "floating_candelabra_lit")
    furn("floating_candelabra", 40, 1, 30, 0, "floating_candelabra_lit")
    for z in (28, 33):
        furn("ghost_portrait", X0 + 1, 5, z, 90)      # on the west wall, facing east
        furn("ghost_portrait", X1 - 1, 5, z, 270)     # on the east wall, facing west
    furn("wisp", 32, 1, 26, 0)
    # ballroom: five dancing couples on the floor
    for dx, dz in ((0, 0), (-8, -2), (8, -2), (-5, 7), (5, 7)):
        furn("waltzing_ghosts", DANCE[0] + dx, 1, DANCE[1] + dz, 0)
    # pianist on the stage, candelabras either side
    furn("ghost_piano", 30, 2, 86, 0)
    for x in (22, 42):
        furn("floating_candelabra", x, 2, 86, 0, "floating_candelabra_lit")
    # lanterns on the side tables
    for z in (46, 54, 70, 78):
        furn("ghost_lantern", 14, 2, z, 90, "ghost_lantern_lit")
        furn("ghost_lantern", 50, 2, z, 270, "ghost_lantern_lit")
    # portraits above the balconies
    for z in (48, 64, 80):
        furn("ghost_portrait", X0 + 1, 11, z, 90)
        furn("ghost_portrait", X1 - 1, 11, z, 270)
    # wisps watching from the balconies and the stage edge
    for x, y, z in ((9, 9, 52), (55, 9, 60), (9, 9, 70), (55, 9, 44), (20, 2, 84), (44, 2, 84)):
        furn("wisp", x, y, z, 0)


# ===================================================================== ambience (tick)
BALL = (OX + X0, OY - 2, OZ + BZ0, X1 - X0, 40, BZ1 - BZ0)       # x y z dx dy dz
ISLE = (OX - 10, OY - 40, OZ - 20, 90, 100, 140)

def sel(box, extra=""):
    x, y, z, dx, dy, dz = box
    return f"@a[x={x},y={y},z={z},dx={dx},dy={dy},dz={dz}{extra}]"

# an original waltz in A minor (3/4); index 0 = F#3 on a note block, pitch = 2^((n-12)/12)
N = {"F#3": 0, "G3": 1, "A3": 3, "B3": 5, "C4": 6, "D4": 8, "E4": 10, "F4": 11, "G4": 13, "G#4": 14, "A4": 15,
     "B4": 17, "C5": 18, "D5": 20, "E5": 22, "F5": 23}
MELODY = [  # one list per bar: (beats, note)
    [(1, "E4"), (1, "A4"), (1, "B4")], [(2, "C5"), (1, "B4")], [(1, "A4"), (1, "E4"), (1, "A4")], [(3, "G4")],
    [(1, "D4"), (1, "G4"), (1, "A4")], [(2, "B4"), (1, "A4")], [(1, "G4"), (1, "E4"), (1, "G4")], [(3, "E4")],
    [(1, "E4"), (1, "A4"), (1, "B4")], [(2, "C5"), (1, "D5")], [(1, "E5"), (1, "D5"), (1, "C5")], [(3, "B4")],
    [(1, "C5"), (1, "B4"), (1, "A4")], [(2, "G4"), (1, "B4")], [(1, "A4"), (1, "C5"), (1, "B4")], [(3, "A4")],
]
CHORDS = ["Am", "Am", "F", "G", "G", "Em", "C", "E", "Am", "Am", "F", "G", "F", "G", "Am", "Am"]
CH = {"Am": ("A3", ["A3", "C4", "E4"]), "F": ("F4", ["A3", "C4", "F4"]), "G": ("G4", ["B3", "D4", "G4"]),
      "Em": ("E4", ["B3", "E4", "G4"]), "C": ("C4", ["C4", "E4", "G4"]), "E": ("E4", ["B3", "E4", "G#4"])}
BEAT = 8          # ticks per beat

def pitch(n):
    return round(2 ** ((N[n] - 12) / 12), 4)

def ps(sound, n, vol):
    return f"execute as {sel(BALL)} at @s run playsound minecraft:block.note_block.{sound} record @s ~ ~ ~ {vol} {pitch(n)}"

def music_functions():
    beats = {}
    b = 0
    for bar, notes in enumerate(MELODY):
        root, chord = CH[CHORDS[bar]]
        t = 0
        for length, note in notes:
            beats.setdefault(b + t, []).append(ps("harp", note, 0.7))
            t += length
        beats.setdefault(b, []).append(ps("bass", root, 0.9))
        for k in (1, 2):
            beats.setdefault(b + k, []).extend(ps("pling", c, 0.18) for c in chord[:2])
        if bar in (7, 15):
            beats.setdefault(b + 2, []).append(ps("chime", "E5", 0.35))
        b += 3
    total = b
    files = {}
    disp = []
    for k in range(total):
        files[f"music/b{k}"] = beats.get(k, [])
        disp.append(f"execute if score #beat moonball matches {k} run function moonball:music/b{k}")
    files["music/beat"] = disp + [f"scoreboard players add #beat moonball 1",
                                   f"execute if score #beat moonball matches {total}.. run scoreboard players set #beat moonball 0"]
    return files

def tick_function():
    return [
        "scoreboard players add #t moonball 1",
        f"execute if score #t moonball matches {BEAT}.. if entity {sel(BALL)} run function moonball:music/beat",
        f"execute if score #t moonball matches {BEAT}.. run scoreboard players set #t moonball 0",
        # arrival title (once per visit)
        f"execute as {sel(ISLE, ',tag=!moonball_in')} run title @s times 20 70 30",
        f"execute as {sel(ISLE, ',tag=!moonball_in')} run title @s subtitle {{\"text\":\"a Mistbloom Studios showcase\",\"color\":\"#9fb3d9\"}}",
        f"execute as {sel(ISLE, ',tag=!moonball_in')} run title @s title {{\"text\":\"Moonlit Ballroom\",\"color\":\"#f2c97d\"}}",
        f"tag {sel(ISLE, ',tag=!moonball_in')} add moonball_in",
        f"tag @a[tag=moonball_in] remove moonball_out",
        f"execute as @a[tag=moonball_in] unless entity @s[x={ISLE[0]},y={ISLE[1]},z={ISLE[2]},dx={ISLE[3]},dy={ISLE[4]},dz={ISLE[5]}] run tag @s remove moonball_in",
        # ambient particles (cheap, only when someone is on the island)
        f"execute if entity {sel(ISLE)} positioned {OX + 32} {OY + 1} {OZ + 8} run particle minecraft:cloud ~ ~ ~ 14 0.3 14 0.003 2",
        f"execute if entity {sel(ISLE)} positioned {OX + 32} {OY + 6} {OZ + 8} run particle minecraft:white_ash ~ ~ ~ 16 6 16 0 4",
        f"execute if entity {sel(BALL)} positioned {OX + DANCE[0]} {OY + 3} {OZ + DANCE[1]} run particle minecraft:end_rod ~ ~ ~ 9 2 9 0.004 1",
        f"execute if entity {sel(BALL)} positioned {OX + 32} {OY + 12} {OZ + 64} run particle minecraft:soul ~ ~ ~ 18 4 22 0.002 1",
        # a friendly hint now and then
        f"execute if score #t moonball matches 0 if score #beat moonball matches 0 run title {sel(BALL)} actionbar {{\"text\":\"Right-click the ghosts. They're friendly!\",\"color\":\"#c9b8f0\"}}",
    ]


def write_datapack(root):
    shutil.rmtree(root, ignore_errors=True)
    fdir = os.path.join(root, "data", NS, "function")
    os.makedirs(os.path.join(fdir, "music"), exist_ok=True)
    os.makedirs(os.path.join(root, "data", "minecraft", "tags", "function"), exist_ok=True)
    json.dump({"pack": {"description": "Moonlit Ballroom showcase - Mistbloom Studios", "pack_format": 94,
                        "min_format": 1, "max_format": 9999, "supported_formats": [1, 9999]}},
              open(os.path.join(root, "pack.mcmeta"), "w"), indent=1)
    island(); gardens(); manor_shell(); foyer(); ballroom(); furniture()
    parts = [cmds[i:i + 3000] for i in range(0, len(cmds), 3000)]     # panel upload limit ~1 MB per file
    for k, part in enumerate(parts):
        open(os.path.join(fdir, f"build_{k}.mcfunction"), "w").write("\n".join(part) + "\n")
    open(os.path.join(fdir, "build.mcfunction"), "w").write("\n".join(f"function moonball:build_{k}" for k in range(len(parts))) + "\n")
    open(os.path.join(fdir, "furniture.mcfunction"), "w").write("\n".join(place) + "\n")
    open(os.path.join(fdir, "tick.mcfunction"), "w").write("\n".join(tick_function()) + "\n")
    open(os.path.join(fdir, "load.mcfunction"), "w").write("scoreboard objectives add moonball dummy\n")
    for name, lines in music_functions().items():
        open(os.path.join(fdir, name + ".mcfunction"), "w").write("\n".join(lines) + "\n")
    json.dump({"values": [f"{NS}:tick"]}, open(os.path.join(root, "data/minecraft/tags/function/tick.json"), "w"))
    json.dump({"values": [f"{NS}:load"]}, open(os.path.join(root, "data/minecraft/tags/function/load.json"), "w"))
    print(len(cmds), "build commands,", len(place), "furniture commands")

if __name__ == "__main__":
    write_datapack("datapack/moonball_showcase")
