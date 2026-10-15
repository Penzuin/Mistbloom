"""Halloween Festival showcase - a harvest night festival on a floating isle (Selling Test).

Story: once a year the village of the hollow drifts up into the night sky and opens its lantern lane,
potion market, witch's porch, graveyard and pumpkin patch to anyone brave enough to visit.

Palette "Hallow Harvest" (one roof material per building):
  base   cobblestone / mossy cobblestone (mossy only in the bottom course)
  frame  dark oak log, stripped dark oak
  walls  spruce planks (cottage, barn), stone bricks (chapel)
  roofs  deepslate tiles (cottage, chapel), dark oak (barn)
  accent orange (jack o'lanterns, pumpkins) and violet (purple glass, amethyst)
  light  warm: jack o'lanterns, lanterns, candles, campfires + hidden light blocks

Local frame: x across (centre 0), y up (0 = ground), z from the gate (front, -z) to the barn (back, +z).
World = O + local. The Halloween furniture are display-only item_display entities tagged hfest_show.
"""
import math, random, json, os
from collections import deque

O = (-1450, 150, -560)
rng = random.Random(1031)
M = "minecraft:"
V = {}          # (x,y,z) -> (block, role)
PIECES = []     # (name, x, y, z, yaw)  y = block the piece stands in (float allowed)
NOTES = {}      # zone -> list of anchor points used by the camera planner

def put(x, y, z, b, role):
    V[(x, y, z)] = (b, role)

def box(x1, y1, z1, x2, y2, z2, b, role):
    for x in range(min(x1, x2), max(x1, x2) + 1):
        for y in range(min(y1, y2), max(y1, y2) + 1):
            for z in range(min(z1, z2), max(z1, z2) + 1):
                put(x, y, z, b, role)

def clear(x1, y1, z1, x2, y2, z2):
    for x in range(min(x1, x2), max(x1, x2) + 1):
        for y in range(min(y1, y2), max(y1, y2) + 1):
            for z in range(min(z1, z2), max(z1, z2) + 1):
                V.pop((x, y, z), None)

def st(b, facing, half="bottom", shape=None):
    return f"{b}[facing={facing},half={half}" + (f",shape={shape}" if shape else "") + "]"

def log(axis="y", kind="dark_oak", stripped=False):
    return M + ("stripped_" if stripped else "") + f"{kind}_log[axis={axis}]"

def piece(name, x, z, yaw, y=1.0):
    PIECES.append((name, x, y, z, yaw))

COB, MCOB, SB, MSB, CSB = M + "cobblestone", M + "mossy_cobblestone", M + "stone_bricks", M + "mossy_stone_bricks", M + "cracked_stone_bricks"
SPR, DOP = M + "spruce_planks", M + "dark_oak_planks"
TILE, TSTAIR, TSLAB = M + "deepslate_tiles", M + "deepslate_tile_stairs", M + "deepslate_tile_slab"
DOSTAIR, DOSLAB, DOFENCE = M + "dark_oak_stairs", M + "dark_oak_slab", M + "dark_oak_fence"
SBSTAIR, SBSLAB, SBWALL = M + "stone_brick_stairs", M + "stone_brick_slab", M + "stone_brick_wall"
COBWALL, MCOBWALL = M + "cobblestone_wall", M + "mossy_cobblestone_wall"
JACK = lambda f: M + f"jack_o_lantern[facing={f}]"
PGLASS = lambda ax: M + ("purple_stained_glass_pane[north=true,south=true]" if ax == "z" else "purple_stained_glass_pane[east=true,west=true]")

OPP = {"north": "south", "south": "north", "east": "west", "west": "east"}

# ===================================================================== island
IRX, IRZ, ICZ = 34, 42, 2

def edge(x, z):
    return 1 + 0.05 * math.sin(x * 0.55 + 1.3) + 0.045 * math.cos(z * 0.43) + 0.03 * math.sin((x - z) * 0.9)

def on_island(x, z, margin=0.0):
    return math.hypot(x / IRX, (z - ICZ) / IRZ) <= edge(x, z) - margin

def island():
    for x in range(-IRX - 3, IRX + 4):
        for z in range(ICZ - IRZ - 3, ICZ + IRZ + 4):
            e = edge(x, z)
            d = math.hypot(x / IRX, (z - ICZ) / IRZ)
            if d > e:
                continue
            k = max(0.0, 1 - d / e)
            depth = int(3 + 30 * k ** 0.75 + 2 * math.sin(x * 0.7) * math.cos(z * 0.5))
            put(x, 0, z, M + "grass_block", "terrain")
            for y in range(-1, -depth - 1, -1):
                b = M + "dirt" if y >= -2 else M + "stone" if y >= -8 else M + "tuff" if y >= -14 else M + "deepslate"
                put(x, y, z, b, "terrain")
            # roots and drips hang from the underside, only under deep rock
            h = (x * 73 + z * 37) % 23
            if depth >= 10 and h == 0:
                put(x, -depth - 1, z, M + "hanging_roots", "nature")
            elif depth >= 16 and h == 7:
                put(x, -depth - 1, z, M + "pointed_dripstone[vertical_direction=down,thickness=frustum]", "nature")
                put(x, -depth - 2, z, M + "pointed_dripstone[vertical_direction=down,thickness=tip]", "nature")
    # rim boulders: a few mossy rock humps on the edge so the outline isn't a flat plate
    for (bx, bz, r) in ((-30, -14, 2), (29, -22, 2), (-25, 28, 3), (31, 14, 2), (-33, 6, 2), (12, -36, 2)):
        for x in range(bx - r, bx + r + 1):
            for z in range(bz - r, bz + r + 1):
                if math.hypot(x - bx, z - bz) <= r + 0.3 and (x, 0, z) in V:
                    hgt = 1 if math.hypot(x - bx, z - bz) > r - 0.8 else 2
                    for y in range(1, hgt + 1):
                        put(x, y, z, M + ("mossy_cobblestone" if y == hgt else "cobblestone"), "terrain")

def ground(x, z, b):
    if (x, 0, z) in V:
        put(x, 0, z, b, "terrain")

def band_path(points, width=1, core=M + "dirt_path", edge_b=M + "coarse_dirt"):
    """Path along a polyline: core within `width`, one block of banded edge outside it."""
    cells = set()
    for (x1, z1), (x2, z2) in zip(points, points[1:]):
        n = max(abs(x2 - x1), abs(z2 - z1)) * 2 + 1
        for i in range(n + 1):
            t = i / n
            cells.add((round(x1 + (x2 - x1) * t), round(z1 + (z2 - z1) * t)))
    core_cells, edge_cells = set(), set()
    for (cx, cz) in cells:
        for dx in range(-width - 1, width + 2):
            for dz in range(-width - 1, width + 2):
                d = max(abs(dx), abs(dz))
                (core_cells if d <= width else edge_cells).add((cx + dx, cz + dz))
    for c in edge_cells - core_cells:
        if V.get((c[0], 0, c[1]), ("", ""))[0] == M + "grass_block":
            ground(c[0], c[1], edge_b)
    for c in core_cells:
        if V.get((c[0], 0, c[1]), ("", ""))[0] in (M + "grass_block", M + "coarse_dirt", M + "gravel"):
            ground(c[0], c[1], core)
    return core_cells

# ===================================================================== trees
def bare_tree(tx, tz, h, lean=1, kind="dark_oak", moss=False):
    """Twisted bare tree: trunk, two forks, branch tips of fences; every part touches the trunk."""
    box(tx, 1, tz, tx, h, tz, log("y", kind), "nature")
    put(tx + lean, h, tz, log("x", kind), "nature")                         # crooked top
    put(tx + lean, h + 1, tz, log("y", kind), "nature")
    put(tx + lean, h + 2, tz, M + f"{kind}_fence", "nature")
    for (dx, dz, yy, ln) in ((lean, 0, h - 2, 3), (0, 1, h - 4, 2), (0, -1, h - 1, 2)):
        ax = "x" if dx else "z"
        for i in range(1, ln + 1):
            put(tx + dx * i, yy, tz + dz * i, log(ax, kind), "nature")
        put(tx + dx * ln, yy + 1, tz + dz * ln, M + f"{kind}_fence", "nature")
        put(tx + dx * (ln + 1), yy + 1, tz + dz * (ln + 1), M + f"{kind}_fence", "nature")
        if moss:
            put(tx + dx * ln, yy - 1, tz + dz * ln, M + "pale_hanging_moss[tip=true]", "nature")
    # root flare
    for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        if (tx + dx + dz) % 2 == 0:
            put(tx + dx, 1, tz + dz, log("x" if dx else "z", kind), "nature")

def pale_tree(tx, tz, h):
    """Pale oak with a ragged ghost-white crown and hanging moss under it."""
    box(tx, 1, tz, tx + 1, h, tz + 1, log("y", "pale_oak"), "nature")
    for y in range(h - 2, h + 3):
        r = 3.2 if y < h + 1 else 2.2
        for dx in range(-3, 5):
            for dz in range(-3, 5):
                cx, cz = dx - 0.5, dz - 0.5
                dd = math.hypot(cx, cz)
                if dd <= r and (tx + dx, y, tz + dz) not in V:
                    if dd < r - 1 or y > h or (dx * 5 + dz * 3 + y) % 4 != 0:   # ragged outer edge, lower crown only
                        put(tx + dx, y, tz + dz, M + "pale_oak_leaves[persistent=true]", "nature")
    for (dx, dz) in ((-2, 0), (3, 1), (0, 3), (1, -2), (-1, 2)):
        if (tx + dx, h - 2, tz + dz) in V:
            put(tx + dx, h - 3, tz + dz, M + "pale_hanging_moss[tip=true]", "nature")

# ===================================================================== gate + lane
GATE_Z = -33

def lane_x(z):
    return round(2.5 * math.sin((z - GATE_Z) * math.pi / 21))

def gate_and_lane():
    pts = [(0, -41), (0, GATE_Z)] + [(lane_x(z), z) for z in range(GATE_Z, -9)] + [(0, -9)]
    band_path(pts, 1)
    # gateposts: cobble plinth, stone brick shaft, jack o'lantern cap on a slab collar
    for x in (-3, 3):
        put(x, 0, GATE_Z, COB, "structure")
        box(x, 1, GATE_Z, x, 2, GATE_Z, SB, "structure")
        put(x, 1, GATE_Z, MSB, "structure")
        put(x, 3, GATE_Z, SBWALL, "trim")
        put(x, 4, GATE_Z, JACK("north"), "light")
        for (dx, f) in ((-1, "east"), (1, "west")):
            put(x + dx, 1, GATE_Z, st(SBSTAIR, f), "structure")
    # low field walls running out from the posts (mossy course at the bottom only)
    for s in (-1, 1):
        for x in range(4, 10):
            put(s * x, 1, GATE_Z, MCOBWALL, "structure")
            if x in (6, 9):
                put(s * x, 2, GATE_Z, COBWALL, "structure")
        put(s * 9, 3, GATE_Z, M + "lantern", "light")
    piece("hollow_arch", 0, GATE_Z, 180)
    piece("welcome_sign", -5, GATE_Z - 2, 180)
    piece("pumpkin_pile", 5, GATE_Z - 2, 180)
    piece("jack_o_lantern_lit", 6, GATE_Z - 1, 200)
    piece("jack_o_lantern", -6, GATE_Z - 1, 160)
    # lantern lane: lamp posts alternate sides, arms over the path
    for z, side in ((-29, -1), (-24, 1), (-19, -1), (-14, 1)):
        x = lane_x(z) + side * 3
        piece("pumpkin_lamp_lit", x, z, 180 if side < 0 else 0)
    # bat bunting strung between fence posts across the lane, twice
    for z in (-26, -16):
        xc = lane_x(z)
        for s in (-2, 2):
            box(xc + s, 1, z, xc + s, 3, z, DOFENCE, "trim")
            put(xc + s, 4, z, M + "lantern", "light")
        piece("bat_bunting", xc, z, 180, y=3)
    # lane dressing: seat + cat, crow post, candy bucket, pumpkins, gourds
    xc = lane_x(-21)
    piece("hay_bale_seat", xc - 3, -21, 270)
    piece("black_cat", xc - 3, -22, 250)                   # on the ground beside the bale
    piece("crow_post", lane_x(-22) + 3, -22, 90)
    piece("candy_bucket", lane_x(-28) + 3, -28, 120)
    piece("pumpkin_pile", lane_x(-12) - 3, -12, 300)
    piece("gourd_basket", lane_x(-31) - 3, -31, 230)
    piece("jack_o_lantern_lit", lane_x(-17) + 3, -17, 110)
    piece("caramel_apple_tray", lane_x(-25) - 3, -25, 270, y=2)
    put(lane_x(-25) - 3, 1, -25, M + "barrel[facing=up]", "furniture")
    # spooky tree by the gate with the hanging spider on its branch
    bare_tree(7, -28, 7, lean=-1)
    piece("hanging_spider", 5, -28, 0, y=4)      # hangs from the branch log at y5
    bare_tree(-8, -20, 6, lean=1, moss=True)
    NOTES["gate"] = (0, 2, GATE_Z)
    NOTES["cat"] = (lane_x(-21) - 3, 1.5, -21)

# ===================================================================== market square
SQ_R = 10

def square():
    for x in range(-SQ_R, SQ_R + 1):
        for z in range(-SQ_R, SQ_R + 1):
            r = math.hypot(x, z)
            if r > SQ_R + 0.4:
                continue
            if r > SQ_R - 0.6:
                b = MSB                                 # border ring
            elif r <= 2.3:
                b = M + "polished_andesite"             # hearth circle
            elif r <= 3.1:
                b = SB
            elif x == 0 or z == 0:
                b = M + "polished_andesite"             # four spokes pointing at the exits
            else:
                b = SB
            ground(x, z, b)
    for x in (-1, 0, 1):                                 # exit thresholds
        for (a, b) in ((x, -SQ_R - 1), (x, SQ_R + 1), (-SQ_R - 1, x), (SQ_R + 1, x)):
            ground(a, b, M + "dirt_path")
    for (ex, ez, yaw) in ((0, -SQ_R, 180), (0, SQ_R, 0), (-SQ_R, 0, 90), (SQ_R, 0, 270)):
        for s_ in (-2, 2):
            px, pz = (ex + s_, ez) if ex == 0 else (ex, ez + s_)
            box(px, 1, pz, px, 3, pz, DOFENCE, "trim")
            put(px, 4, pz, M + "lantern", "light")
        piece("bat_bunting", ex, ez, yaw, y=3)
    piece("cauldron_lit", 0, 0, 180)
    # four skull candles on stone posts round the cauldron
    for (x, z, yaw) in ((-2, -2, 315), (2, -2, 45), (-2, 2, 225), (2, 2, 135)):
        piece("skull_candle", x, z, yaw)
    # stalls on the diagonals, all facing the cauldron
    piece("potion_stall", -6, -6, 315)
    piece("potion_stall_moss", -6, 6, 225)
    piece("potion_stall_ember", 6, 6, 135)
    # cider corner (south-east): cask, barrel table with candles, two stools
    piece("cider_cask", 7, -5, 45)
    put(5, 1, -7, M + "barrel[facing=up]", "furniture")
    piece("candle_cluster", 5, -7, 45, y=2)
    piece("cushion_stool", 4, -8, 20)
    piece("cushion_stool", 6, -9, 70)
    # lamp posts at the four exits, arm over the path
    piece("pumpkin_lamp_lit", -6, -8, 180)
    piece("pumpkin_lamp_lit", 8, 6, 270)
    piece("pumpkin_lamp_lit", -8, 2, 90)
    piece("pumpkin_lamp_lit", 2, 8, 0)
    NOTES["square"] = (0, 1.5, 0)

# ===================================================================== witch's cottage
CW0, CW1, CZ0, CZ1 = -28, -20, -4, 4      # walls x -28..-20 (9), z -4..4 (9); gable faces east
CTOP = 5                                  # wall plate

def gable_roof_x(x0, x1, z0, z1, eave_y, stair, solid, slab, rake_trim, ridge_trim):
    """Steep gable roof with the ridge along x. Pitch 1:1 then 2:1 near the top (witch-hat profile).
    1-block overhang on the long sides (soffit of upside-down stairs) and rakes at both gable ends."""
    zc = (z0 + z1) / 2
    half = (z1 - z0) // 2 + 1
    prof = []                         # (dz from the eave, y)
    y = eave_y
    for i in range(half + 1):
        prof.append((i, y))
        y += 1 if i < half - 2 else 2
    for x in range(x0 - 1, x1 + 2):
        rake = x in (x0 - 1, x1 + 1)
        for i, yy in prof:
            for zz, f in ((z0 - 1 + i, "south"), (z1 + 1 - i, "north")):
                if zz > zc + 0.01 and f == "south" or zz < zc - 0.01 and f == "north":
                    continue
                if abs(zz - zc) < 0.01:
                    for fy in range(prof[i - 1][1], yy + 1):
                        put(x, fy, zz, solid, "roof")
                    put(x, yy + 1, zz, ridge_trim, "trim")
                    continue
                put(x, yy, zz, st(rake_trim if rake else stair, f), "trim" if rake else "roof")
                if i > 0:                 # fill under the steeper courses so there is no gap
                    prev = prof[i - 1][1]
                    for fy in range(prev + 1, yy):
                        put(x, fy, zz, solid, "roof")
                if i == 0:
                    put(x, yy - 1, zz, st(stair, OPP[f], "top"), "roof")   # soffit under the overhang
    return prof

def cottage():
    # plinth one wider than the walls
    box(CW0 - 1, 0, CZ0 - 1, CW1 + 1, 0, CZ1 + 1, COB, "structure")
    box(CW0, 1, CZ0, CW1, 1, CZ1, MCOB, "fill")                # mossy bottom course only
    box(CW0, 2, CZ0, CW1, CTOP - 1, CZ1, SPR, "fill")
    # frame: corner posts + mid posts, plate beams
    for x in (CW0, CW1):
        for z in (CZ0, 0, CZ1):
            box(x, 1, z, x, CTOP, z, log("y"), "frame")
    for z in (CZ0, CZ1):
        box(CW0, 1, z, CW0, CTOP, z, log("y"), "frame")
        box(-24, 1, z, -24, CTOP, z, log("y"), "frame")
        box(CW0, CTOP, z, CW1, CTOP, z, log("x"), "frame")
    for x in (CW0, CW1):
        box(x, CTOP, CZ0, x, CTOP, CZ1, log("z"), "frame")
    # hollow inside
    clear(CW0 + 1, 1, CZ0 + 1, CW1 - 1, CTOP + 6, CZ1 - 1)
    box(CW0 + 1, 0, CZ0 + 1, CW1 - 1, 0, CZ1 - 1, DOP, "fill")    # floor
    # windows: purple glass recessed, spruce trapdoor shutters, stone sill
    for z in (-2, 2):                                             # east gable face beside the door
        put(CW1, 3, z, PGLASS("x"), "glass")
        put(CW1 + 1, 2, z, st(M + "cobblestone_stairs", "west", "top"), "trim")
        put(CW1 + 1, 3, z + (1 if z > 0 else -1), M + "spruce_trapdoor[facing=east,half=bottom,open=true]", "trim")
    for x in (-26, -22):                                          # long sides
        for z, f in ((CZ0, "north"), (CZ1, "south")):
            box(x, 2, z, x, 3, z, PGLASS("z"), "glass")
            put(x, 1, z + (-1 if f == "north" else 1), st(M + "cobblestone_stairs", OPP[f], "top"), "trim")
    # door + lintel on the east gable, step in front
    put(CW1, 1, 0, M + "dark_oak_door[facing=east,half=lower,hinge=left]", "trim")
    put(CW1, 2, 0, M + "dark_oak_door[facing=east,half=upper,hinge=left]", "trim")
    put(CW1, 3, 0, log("z"), "frame")
    # roof: deepslate tile, witch-hat profile, ridge along x, gable faces east toward the square
    prof = gable_roof_x(CW0, CW1 + 3, CZ0, CZ1, CTOP + 1, TSTAIR, TILE, TSLAB, M + "dark_oak_stairs", M + "deepslate_tile_wall")
    for x in range(CW0, CW1 + 1):
        for z in (CZ0, CZ1):
            for fy in range(CTOP + 1, prof[1][1]):
                put(x, fy, z, SPR, "fill")
    # gable infill (both ends) under the roof, framed: spruce with a round purple window
    for x in (CW0, CW1):
        for zz in range(CZ0 + 1, CZ1):
            i = min(zz - (CZ0 - 1), (CZ1 + 1) - zz)
            for fy in range(CTOP + 1, prof[i][1]):
                if (x, fy, zz) not in V:
                    put(x, fy, zz, SPR, "fill")
        put(x, CTOP + 3, 0, PGLASS("x"), "glass")
        put(x, CTOP + 2, 0, PGLASS("x"), "glass")
    # porch: the roof runs on over the porch (x -19..-17), carried by two log posts
    box(CW1 + 1, 0, CZ0, CW1 + 3, 0, CZ1, DOP, "structure")
    for z in (CZ0, CZ1):
        box(CW1 + 3, 1, z, CW1 + 3, CTOP, z, log("y"), "frame")
        put(CW1 + 3, CTOP - 1, z + (1 if z < 0 else -1), st(DOSTAIR, "south" if z < 0 else "north", "top"), "trim")  # brackets
    box(CW1 + 1, CTOP, CZ0, CW1 + 3, CTOP, CZ0, log("x"), "frame")
    box(CW1 + 1, CTOP, CZ1, CW1 + 3, CTOP, CZ1, log("x"), "frame")
    box(CW1 + 3, CTOP, CZ0, CW1 + 3, CTOP, CZ1, log("z"), "frame")
    put(CW1 + 3, CTOP - 1, 0, M + "lantern[hanging=true]", "light")
    # chimney through the north slope, campfire on top for real smoke
    cx, cz = -26, CZ0 + 1
    for y in range(1, prof[-1][1] + 3):
        if (cx, y, cz) not in V or V[(cx, y, cz)][1] in ("roof", "fill", "frame"):
            put(cx, y, cz, COB if y > 1 else MCOB, "structure")
    put(cx, prof[-1][1] + 3, cz, M + "campfire[lit=true,signal_fire=false]", "light")
    # interior: lit, and furnished with blocks (camera sees it through the door)
    put(-21, 1, -3, M + "barrel[facing=up]", "furniture")
    put(-27, 1, 3, M + "bookshelf", "furniture"); put(-27, 2, 3, M + "bookshelf", "furniture")
    for (x, z) in ((-26, -2), (-22, 2)):
        put(x, 1, z, M + "light[level=12]", "light")
    # porch pieces (all face east, toward the square)
    piece("spellbook_lectern", -18, -2, 270)
    put(-18, 1, 2, M + "barrel[facing=up]", "furniture")
    piece("crystal_ball", -18, 2, 270, y=2)
    piece("cushion_stool", -18, 1, 250)
    piece("harvest_wreath", -19, 0, 270, y=3)          # wall piece on the gable above the door
    piece("potion_shelf", -19, -1, 270, y=2)            # hung on the east wall, between door and window
    piece("witch_broom", -17, 1, 290)
    piece("witch_hat_stand", -18, 3, 270)
    piece("cobweb_corner", -19, -4, 270, y=4)           # corner of the wall and the porch beam
    piece("ghost_lantern", -17, 3, 270)
    # path from the square to the porch step
    band_path([(-11, 0), (-16, 0)], 1)
    NOTES["porch"] = (-18, 2, 0)

def witch_garden():
    # herb garden south-west of the cottage (front side, -z), picket fence with a gate
    x0, x1, z0, z1 = -29, -19, -14, -7
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            ground(x, z, M + ("moss_block" if (z - z0) % 3 else "rooted_dirt"))
    for x in range(x0, x1 + 1):
        for z in (z0, z1):
            if not (z == z1 and x in (-22, -23)):
                put(x, 1, z, DOFENCE, "trim")
    for z in range(z0, z1 + 1):
        put(x0, 1, z, DOFENCE, "trim"); put(x1, 1, z, DOFENCE, "trim")
    for (x, z) in ((x0, z0), (x1, z0), (x0, z1), (x1, z1)):
        put(x, 2, z, M + "lantern", "light")
    piece("cauldron", -25, -11, 30)
    put(-25, 0, -11, M + "campfire[lit=true]", "light")     # under the pot, smoke curls up through it
    piece("mushroom_ring", -21, -12, 0)
    put(-27, 1, -9, log("y"), "furniture")                  # stump table
    piece("potion_trio", -27, -9, 40, y=2)
    for (x, z) in ((-28, -13), (-20, -9), (-28, -8)):
        put(x, 1, z, M + "red_mushroom", "nature")
    for (x, z) in ((-23, -13), (-26, -13)):
        put(x, 1, z, M + "fern", "nature")
    NOTES["garden"] = (-25, 1.5, -11)

# ===================================================================== graveyard + chapel ruin
GX0, GX1, GZ0, GZ1 = 14, 32, -11, 11

def graveyard():
    for x in range(GX0, GX1 + 1):
        for z in range(GZ0, GZ1 + 1):
            if (x, 0, z) in V:
                ground(x, z, M + ("moss_block" if x <= GX0 + 1 else "podzol"))
    band_path([(SQ_R + 1, 0), (24, 0)], 1, core=M + "gravel", edge_b=M + "podzol")
    # front wall with a gateway on the path
    for z in range(GZ0, GZ1 + 1):
        if abs(z) <= 1:
            continue
        put(GX0, 1, z, MCOBWALL, "structure")
        if z in (GZ0, -2, 2, GZ1):
            put(GX0, 2, z, COBWALL, "structure")
    for z in (-2, 2):
        put(GX0, 3, z, M + "lantern", "light")
    # iron fence along the two sides
    for x in range(GX0 + 1, 31, 1):
        for z, yaw in ((GZ0, 0), (GZ1, 180)):
            if (x, 0, z) in V:
                piece("iron_fence", x, z, yaw)
    # rows of graves facing west (toward the visitors), mounds of coarse dirt in front of each
    graves = [("tombstone", 18, -7), ("tombstone_cross", 18, -4), ("tombstone", 18, 4), ("tombstone_cross", 18, 7),
              ("tombstone_cross", 21, -8), ("tombstone", 21, -5), ("tombstone", 21, 5), ("tombstone_cross", 21, 8)]
    for name, x, z in graves:
        piece(name, x, z, 90)
        ground(x - 1, z, M + "rooted_dirt")
    piece("coffin", 24, -7, 0)
    for x in (23, 24, 25):
        ground(x, -8, M + "coarse_dirt")
    piece("ghost_lantern_lit", 23, -2, 90, y=2); put(23, 1, -2, SB, "structure")     # flank the chapel door
    piece("ghost_lantern_lit", 23, 2, 90, y=2); put(23, 1, 2, SB, "structure")
    piece("dead_tree", 29, 8, 90)
    piece("mushroom_ring", 27, -9, 0)
    piece("ghost_lantern", 25, 8, 90)
    chapel()
    NOTES["graves"] = (20, 1.5, 0)

def chapel():
    """Ruined chapel at the back of the graveyard: west gable with a pointed door still standing,
    side walls broken down in steps toward the back, roof only over the apse end."""
    x0, x1, z0, z1 = 25, 31, -4, 4
    box(x0 - 1, 0, z0 - 1, x1 + 1, 0, z1 + 1, COB, "structure")
    box(x0, 0, z0 + 1, x1 - 1, 0, z1 - 1, SB, "fill")
    def wall_h(x, z):
        if x == x0:                       # west gable stands to full height
            return 7 - abs(z) // 2 if abs(z) <= 3 else 5
        if x == x1:
            return 6
        return [5, 4, 3, 2, 3, 4][(x - x0) % 6] if abs(z) == 4 else 0     # broken side walls
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            if not (x in (x0, x1) or z in (z0, z1)):
                continue
            h = wall_h(x, z)
            for y in range(1, h + 1):
                b = MSB if y == 1 else (CSB if (x in (x0, x1) and z in (z0, z1) and y == 2) else SB)
                put(x, y, z, b, "fill")
    # corner buttresses
    for x in (x0, x1):
        for z in (z0 - 1, z1 + 1):
            box(x, 1, z, x, 2, z, SB, "structure")
            put(x, 3, z, st(SBSTAIR, "south" if z < 0 else "north"), "structure")
    # pointed doorway on the west gable
    for y in (1, 2):
        for z in (-1, 0, 1):
            V.pop((x0, y, z), None)
    V.pop((x0, 3, 0), None)
    put(x0, 3, -1, st(SBSTAIR, "north", "top"), "trim"); put(x0, 3, 1, st(SBSTAIR, "south", "top"), "trim")
    put(x0, 5, 0, M + "purple_stained_glass_pane[north=true,south=true]", "glass")
    put(x0, 6, 0, SBSLAB, "trim")
    # apse roof (back two bays only), deepslate tiles, ridge along x
    for x in (x1 - 1, x1):
        for i, z in enumerate(range(z0 - 1, 1)):
            put(x, 5 + i, z, st(TSTAIR, "south"), "roof")
            put(x, 5 + i, -z, st(TSTAIR, "north"), "roof")
        put(x, 10, 0, TILE, "roof")
    for z in range(z0, z1 + 1):                 # back gable and the side walls meet the roof
        ry = 5 + (z - (z0 - 1)) if z <= 0 else 5 + ((z1 + 1) - z)
        for y in range(1, ry):
            if (x1, y, z) not in V:
                put(x1, y, z, SB, "fill")
    for z in (z0, z1):
        ry = 6
        for y in range(1, ry):
            if (x1 - 1, y, z) not in V:
                put(x1 - 1, y, z, SB, "fill")
    # inside: altar of stone with candles, ivy at the wall foot
    box(29, 1, -1, 29, 1, 1, M + "chiseled_stone_bricks", "furniture")
    put(29, 2, -1, M + "candle[candles=3,lit=true]", "light"); put(29, 2, 1, M + "candle[candles=2,lit=true]", "light")
    piece("tombstone_cross", 30, 0, 90)
    piece("owl_perch", 27, -4, 90, y=4)                 # on the broken north wall top (wall h=3 at x=27)
    put(28, 3, 0, M + "light[level=12]", "light")

# ===================================================================== pumpkin patch + barn
PZ0, PZ1 = 14, 30

def pumpkin_patch():
    band_path([(0, SQ_R + 1), (0, 34)], 1)
    for z in range(PZ0, PZ1 + 1):
        for x in range(-16, 17):
            if abs(x) <= 2 or (x, 0, z) not in V:
                continue
            row = (z - PZ0) % 3
            ground(x, z, M + ("coarse_dirt" if row == 1 else "rooted_dirt"))
            if row == 1 and (x * 7 + z * 3) % 3 == 0:
                b = "pumpkin" if (x * 5 + z) % 7 else "carved_pumpkin[facing=north]"
                if (x, z) in ((-12, 18), (11, 24), (-5, 27), (14, 15)):
                    b = "jack_o_lantern[facing=north]"
                put(x, 1, z, M + b, "nature")
            elif row != 1 and (x * 3 + z * 5) % 4 == 0:
                put(x, 1, z, M + "short_grass", "nature")
    # scarecrow in the middle of the field, facing the square
    for x in (-1, 0, 1):
        V.pop((x - 7, 1, 23), None)
    piece("scarecrow", -7, 23, 180)
    piece("pumpkin_cart", 7, 17, 160)
    piece("gourd_basket", -4, 16, 200)
    piece("haystack", -11, 29, 170)
    piece("pumpkin_pile", 9, 27, 180)
    for (x, z) in ((-8, 23), (-6, 23), (8, 17), (6, 17), (9, 27), (-4, 16)):
        V.pop((x, 1, z), None)
    for (x, z) in ((-12, 29), (-10, 29), (-11, 28), (-11, 30), (-12, 30), (-10, 30), (5, 18), (6, 18), (7, 18), (8, 18), (9, 18)):
        V.pop((x, 1, z), None)
    NOTES["patch"] = (-7, 2, 23)

BX0, BX1, BZ0, BZ1 = -6, 6, 32, 40

def barn():
    """Gambrel-roof barn (dark oak), spruce walls between log posts, big open doorway with hay inside."""
    box(BX0 - 1, 0, BZ0 - 1, BX1 + 1, 0, BZ1 + 1, COB, "structure")
    box(BX0, 1, BZ0, BX1, 1, BZ1, MCOB, "fill")
    box(BX0, 2, BZ0, BX1, 5, BZ1, SPR, "fill")
    for x in (BX0, -2, 2, BX1):
        for z in (BZ0, BZ1):
            box(x, 1, z, x, 6, z, log("y"), "frame")
    for z in (BZ0, 36, BZ1):
        for x in (BX0, BX1):
            box(x, 1, z, x, 6, z, log("y"), "frame")
    for z in (BZ0, BZ1):
        box(BX0, 6, z, BX1, 6, z, log("x"), "frame")
    for x in (BX0, BX1):
        box(x, 6, BZ0, x, 6, BZ1, log("z"), "frame")
    clear(BX0 + 1, 1, BZ0 + 1, BX1 - 1, 12, BZ1 - 1)
    box(BX0 + 1, 0, BZ0 + 1, BX1 - 1, 0, BZ1 - 1, SPR, "fill")
    # doorway 3 wide x 4 tall in the front gable
    clear(-1, 1, BZ0, 1, 4, BZ0)
    put(0, 5, BZ0, log("x"), "frame"); put(-1, 5, BZ0, log("x"), "frame"); put(1, 5, BZ0, log("x"), "frame")
    for x in (-2, 2):
        put(x, 4, BZ0 - 1, st(DOSTAIR, "east" if x < 0 else "west", "top"), "trim")
    # gambrel roof along z: steep lower slope then shallow upper slope, overhang + soffit
    prof = [(0, 7, "s"), (1, 8, "s"), (2, 9, "s"), (3, 10, "s"), (4, 10, "f"), (5, 11, "s"), (6, 11, "f"), (7, 12, "r")]
    for z in range(BZ0 - 1, BZ1 + 2):
        rake = z in (BZ0 - 1, BZ1 + 1)
        for i, y, kind in prof:
            for x, f in ((BX0 - 1 + i, "east"), (BX1 + 1 - i, "west")):
                if kind == "r":
                    put(0, y, z, DOP, "roof"); put(0, y - 1, z, DOP, "roof"); put(0, y + 1, z, DOSLAB, "trim")
                    continue
                if kind == "s":
                    put(x, y, z, st(M + ("spruce_stairs" if rake else "dark_oak_stairs"), f), "trim" if rake else "roof")
                else:
                    put(x, y, z, DOSLAB if not rake else M + "spruce_slab", "roof")
                    put(x, y - 1, z, DOP, "roof")
                if i == 0:
                    put(x, y - 1, z, st(DOSTAIR, OPP[f], "top"), "roof")
                elif kind == "s":
                    put(x, y - 1, z, DOP, "roof")
    # gable infill front and back with a loft door + jack o'lantern
    for z in (BZ0, BZ1):
        for x in range(BX0 + 1, BX1):
            lvl = dict((BX0 - 1 + i, yy) for i, yy, k in prof)[-abs(x)]
            for y in range(7, lvl):
                if (x, y, z) not in V:
                    put(x, y, z, SPR, "fill")
        put(0, 8, z, JACK("north" if z == BZ0 else "south"), "light")
        put(0, 9, z, log("x"), "frame")
    # hay inside, lanterns
    for (x, z, h) in ((-4, 38, 3), (-3, 38, 2), (4, 38, 2), (-4, 37, 1), (3, 38, 3), (4, 37, 1)):
        box(x, 1, z, x, h, z, M + "hay_block[axis=y]", "furniture")
    put(0, 6, 36, M + "lantern[hanging=true]", "light")
    for y in range(7, 11):
        put(0, y, 36, M + "iron_chain", "trim")
    put(-3, 2, BZ0 - 1, M + "lantern", "light"); put(-3, 1, BZ0 - 1, M + "hay_block[axis=y]", "furniture")
    put(3, 1, BZ0 - 1, M + "hay_block[axis=x]", "furniture"); put(3, 2, BZ0 - 1, M + "carved_pumpkin[facing=north]", "nature")
    piece("pumpkin_lamp", 4, BZ0 - 3, 0)
    put(0, 3, 36, M + "light[level=12]", "light")
    NOTES["barn"] = (0, 2, BZ0)

# ===================================================================== bonfire circle + carving tables
BF = (17, -22)

def bonfire():
    bx, bz = BF
    for x in range(bx - 5, bx + 6):
        for z in range(bz - 5, bz + 6):
            r = math.hypot(x - bx, z - bz)
            if r <= 5.3 and (x, 0, z) in V:
                ground(x, z, M + ("gravel" if r <= 1.6 else "coarse_dirt" if r <= 2.6 else "dirt_path" if r <= 4.6 else "coarse_dirt"))
    # fire: lit campfires in a plus, a stone kerb ring, a log tripod over it
    for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        put(bx + dx, 1, bz + dz, M + "campfire[lit=true]", "light")
    put(bx, 1, bz, M + "stripped_spruce_log[axis=y]", "structure")       # stacked centre: log + raised fire
    put(bx, 2, bz, M + "campfire[lit=true]", "light")
    for (dx, dz) in ((1, 1), (-1, 1), (1, -1), (-1, -1)):                 # leaning logs round the stack
        put(bx + dx, 1, bz + dz, M + "spruce_fence", "structure")
    for (dx, dz) in ((2, 0), (-2, 0), (0, 2), (0, -2), (2, 1), (2, -1), (-2, 1), (-2, -1), (1, 2), (-1, 2), (1, -2), (-1, -2)):
        put(bx + dx, 1, bz + dz, M + "cobblestone_slab[type=bottom]", "trim")
    # four hay bale seats facing the fire, a cat-free circle of friends
    for (dx, dz, yaw) in ((0, -4, 0), (0, 4, 180), (-4, 0, 270), (4, 0, 90)):
        piece("hay_bale_seat", bx + dx, bz + dz, yaw)
    piece("jack_o_lantern_lit", bx + 3, bz - 3, 315)
    piece("pumpkin_pile", bx - 3, bz + 3, 135)
    piece("candy_bucket", bx + 3, bz + 3, 225)
    piece("cushion_stool", bx - 3, bz - 3, 45)
    band_path([(4, -12), (bx - 4, bz + 1)], 0, core=M + "dirt_path", edge_b=M + "coarse_dirt")
    NOTES["bonfire"] = (bx, 1.5, bz)

CT = (-15, -26)

def carving_tables():
    tx, tz = CT
    for x in range(tx - 4, tx + 5):
        for z in range(tz - 3, tz + 4):
            if (x, 0, z) in V:
                ground(x, z, M + ("coarse_dirt" if abs(z - tz) <= 2 else "rooted_dirt"))
    # two trestle tables (spruce slab tops on dark oak fence legs), pumpkins waiting to be carved
    for row in (tz - 1, tz + 1):
        for x in range(tx - 2, tx + 3):
            put(x, 2, row, M + "spruce_slab[type=bottom]", "furniture")
        for x in (tx - 2, tx + 2):
            put(x, 1, row, DOFENCE, "furniture")
    put(tx - 1, 3, tz - 1, M + "carved_pumpkin[facing=east]", "furniture")
    put(tx + 1, 3, tz - 1, M + "jack_o_lantern[facing=east]", "light")
    put(tx, 3, tz + 1, M + "pumpkin", "furniture")
    put(tx + 2, 3, tz + 1, M + "carved_pumpkin[facing=east]", "furniture")
    piece("candle_cluster", tx - 2, tz + 1, 270, y=2.5)
    piece("gourd_basket", tx - 2, tz - 1, 270, y=2.5)
    piece("pumpkin_pile", tx + 4, tz, 90)
    piece("cushion_stool", tx, tz - 2, 0)
    piece("cushion_stool", tx, tz + 2, 180)
    band_path([(lane_x(-26) - 2, -26), (tx + 4, tz)], 0)
    NOTES["carving"] = (tx, 2, tz)

# ===================================================================== hills + ground cover
def _noise(x, z, f=0.13, seed=0.0):
    return (math.sin(x * f + seed) * math.cos(z * f * 1.3 + seed * 2) + math.sin((x + z) * f * 0.7 + seed * 3)) / 2

def hills_and_cover():
    trunks = [(x, z) for (x, y, z), (b, r) in V.items() if y == 1 and "_log[axis=y]" in b and r == "nature"]
    piece_cells = {(round(p[1]), round(p[3])) for p in PIECES}
    for (x, y, z), (b, r) in list(V.items()):
        if y != 0 or b != M + "grass_block":
            continue
        if (x, 1, z) in V or (x, z) in piece_cells:
            continue
        rr = math.hypot(x / IRX, (z - ICZ) / IRZ) / edge(x, z)
        # keep 3 blocks clear of anything built
        near = any(V.get((x + dx, yy, z + dz), ("", "terrain"))[1] not in ("terrain", "nature", "light")
                   for dx in range(-3, 4) for dz in range(-3, 4) for yy in (0, 1))
        near = near or any(abs(px - x) <= 3 and abs(pz - z) <= 3 for (px, pz) in piece_cells)
        h = 0
        if not near and rr > 0.55 and rr < 0.93:
            n = _noise(x, z)
            h = 2 if n > 0.62 else 1 if n > 0.3 else 0
        for yy in range(1, h + 1):
            put(x, yy - 1, z, M + "dirt", "terrain")
            put(x, yy, z, M + "grass_block", "terrain")
        top = h
        # ground cover in patches (low-frequency field), leaf litter under trees, fireflies near the rim
        d_tree = min((math.hypot(x - tx, z - tz) for (tx, tz) in trunks), default=99)
        k = (x * 928371 + z * 1237) % 1000 / 1000
        if near and rr < 0.55:
            continue
        if d_tree <= 3.2 and k < 0.55:
            put(x, top + 1, z, M + f"leaf_litter[facing={'north' if k < 0.3 else 'east'},segment_amount={1 + int(k * 7) % 4}]", "nature")
        elif rr > 0.78 and k < 0.035:
            put(x, top + 1, z, M + "firefly_bush", "nature")
        elif _noise(x, z, 0.21, 1.7) > 0.15 and k < 0.42:
            put(x, top + 1, z, M + ("fern" if k < 0.08 else "short_grass"), "nature")

def base_planting():
    """Leaf bushes along the foundations of the cottage, barn and chapel (about half their length)."""
    L = M + "dark_oak_leaves[persistent=true]"
    for z in range(CZ0 - 1, CZ1 + 2):
        if z % 3 != 0:
            put(CW0 - 2, 1, z, L, "nature")
    for x in range(CW0, CW1 + 1, 2):
        put(x, 1, CZ1 + 2, L, "nature")
    for z in range(BZ0 + 1, BZ1 + 1):
        if z % 3:
            put(BX0 - 2, 1, z, L, "nature"); put(BX1 + 2, 1, z, L, "nature")
    for z in (-5, -6, 5, 6):
        put(31, 1, z, L, "nature")

# ===================================================================== trees, lights, assembly
def trees():
    pale_tree(-21, 17, 8)
    pale_tree(17, 22, 9)
    pale_tree(-26, -25, 7)
    bare_tree(25, -17, 8, lean=-1, moss=True)
    bare_tree(-14, 34, 7, lean=1)
    bare_tree(14, 33, 6, lean=-1, moss=True)
    bare_tree(23, -26, 6, lean=1)
    bare_tree(-22, -31, 6, lean=-1, moss=True)

def light_grid():
    """Hidden light (level 9) every 7 blocks over open ground so nothing spawns, and fill light for the camera."""
    for x in range(-IRX, IRX + 1, 7):
        for z in range(ICZ - IRZ, ICZ + IRZ + 1, 7):
            if on_island(x, z, 0.04) and (x, 1, z) not in V and (x, 0, z) in V:
                put(x, 1, z, M + "light[level=9]", "light")

def piece_lights():
    lv = {"pumpkin_lamp_lit": (3, 15), "jack_o_lantern_lit": (1, 13), "cauldron_lit": (1, 12), "skull_candle": (0, 11),
          "candle_cluster": (0, 11), "potion_stall": (1, 10), "potion_stall_moss": (1, 10), "potion_stall_ember": (1, 10),
          "ghost_lantern_lit": (0, 13), "crystal_ball": (0, 9), "spellbook_lectern": (1, 8), "hollow_arch": (2, 13),
          "welcome_sign": (3, 10), "dead_tree": (2, 12)}
    for name, x, y, z, yaw in PIECES:
        if name in lv:
            dy, l = lv[name]
            p = (x, int(y) + dy, z)
            if p not in V:
                put(*p, M + f"light[level={l}]", "light")

def build_all():
    V.clear(); PIECES.clear(); NOTES.clear()
    island(); gate_and_lane(); square(); cottage(); witch_garden(); graveyard(); pumpkin_patch(); barn(); trees()
    bonfire(); carving_tables(); base_planting(); piece_lights(); light_grid(); hills_and_cover()
    plants = ("short_grass", "fern", "leaf_litter", "firefly_bush", "red_mushroom")
    for (name, x, y, z, yaw) in PIECES:                 # no grass poking through the furniture
        for dx in (-1, 0, 1):
            for dz in (-1, 0, 1):
                for yy in (int(y), int(y) + 1):
                    if any(k in V.get((x + dx, yy, z + dz), ("", ""))[0] for k in plants):
                        V.pop((x + dx, yy, z + dz))
    return V
