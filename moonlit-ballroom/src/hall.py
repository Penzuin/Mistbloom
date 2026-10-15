"""Moonlit Ballroom showcase v2 - a small moonlit dance hall on a floating isle.

Story: friendly ghosts still hold their nightly waltz in a little elven dance hall that drifted
into the sky. Palette (Elven Night): base deepslate bricks + polished deepslate plinth, frame dark
oak / stripped dark oak + polished blackstone trim, wall fill calcite, roof deepslate tiles,
accents amethyst + purple glass + iron, cold light only (soul lanterns, hidden light, sea lantern
behind glass for the moon window).

Local frame: x across (centre 0), y up (0 = floor / ground level), z from the front (path, -z)
to the back (stage, +z). World = O + local.
"""
import math, random
from collections import deque

O = (132, 210, 130)
rng = random.Random(11)

V = {}        # (x,y,z) -> (block, role)

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

M = "minecraft:"
DSB, PDS, LOG, SLOG, PBS, CALC, TILE = (M + "deepslate_bricks", M + "polished_deepslate", M + "dark_oak_log",
    M + "stripped_dark_oak_log", M + "polished_blackstone", M + "calcite", M + "deepslate_tiles")
TSTAIR, TSLAB, PBSTAIR, PBWALL = M + "deepslate_tile_stairs", M + "deepslate_tile_slab", M + "polished_blackstone_stairs", M + "polished_blackstone_wall"
PDSTAIR = M + "polished_deepslate_stairs"
GLASS, AMETHYST = M + "purple_stained_glass_pane[north=true,south=true]", M + "amethyst_block"

# hall (dominant mass): frame posts on x=+-7, wall fill on x=+-6, interior x -5..5, z 1..23
HX, HZ0, HZ1, WALL_TOP = 7, 0, 24, 8

def st(b, facing, half="bottom", shape=None):
    s = f"{b}[facing={facing},half={half}" + (f",shape={shape}" if shape else "") + "]"
    return s

def log(axis="y", stripped=False):
    return (SLOG if stripped else LOG) + f"[axis={axis}]"

# ===================================================================== island
def island():
    cx, cz, rx, rz = 0, 6, 15, 24
    for x in range(-rx - 2, rx + 3):
        for z in range(cz - rz - 2, cz + rz + 3):
            d = math.hypot((x - cx) / rx, (z - cz) / rz)
            edge = 1 + 0.06 * math.sin(x * 0.9 + 1) + 0.05 * math.cos(z * 0.6)
            if d > edge:
                continue
            depth = int(2 + 18 * max(0.0, 1 - d / edge) ** 0.8)
            put(x, 0, z, M + "grass_block", "terrain")
            for y in range(-1, -depth - 1, -1):
                b = M + "dirt" if y >= -2 else M + "stone" if y >= -7 else M + "tuff" if y >= -11 else M + "deepslate"
                put(x, y, z, b, "terrain")
            if depth >= 8 and (x * 7 + z * 3) % 9 == 0:
                put(x, -depth - 1, z, M + "hanging_roots", "nature")

# ===================================================================== path & garden
def garden():
    # 3-wide flagstone path, banded edge: path -> gravel -> coarse dirt -> grass
    for z in range(-17, -6):
        for x in range(-1, 2):
            put(x, 0, z, PDS if (z % 2 == 0 and x == 0) else DSB, "terrain")
        for x in (-2, 2):
            put(x, 0, z, M + "gravel", "terrain")
        for x in (-3, 3):
            put(x, 0, z, M + "coarse_dirt", "terrain")
    # gate: two pillars with caps, a pointed arch of iron bars, lanterns on chains
    for x in (-3, 3):
        box(x, 1, -16, x, 4, -16, PDS, "structure")
        put(x, 5, -16, M + "chiseled_deepslate", "trim")
        put(x, 6, -16, PBWALL, "trim")
        put(x, 7, -16, M + "soul_lantern", "light")
    for x in range(-2, 3):
        put(x, 5, -16, M + "iron_bars[east=true,west=true]", "trim")
    put(-1, 6, -16, M + "iron_bars[east=true,west=true]", "trim")
    put(0, 6, -16, M + "iron_bars[east=true,west=true]", "trim")
    put(1, 6, -16, M + "iron_bars[east=true,west=true]", "trim")
    put(0, 4, -16, M + "iron_chain", "trim")
    put(0, 3, -16, M + "soul_lantern[hanging=true]", "light")
    # low lantern plinths along the path (ghost lanterns sit on these)
    for z in (-13, -10):
        for x in (-3, 3):
            put(x, 1, z, PDS, "structure")
    # base planting along 50% of the foundation: dark oak leaf bushes + white and blue flowers
    for z in (2, 3, 10, 11, 18, 19):
        for x in (-9, 9):
            put(x, 1, z, M + "dark_oak_leaves[persistent=true]", "nature")
    for z in (6, 14, 22):
        for x in (-9, 9):
            put(x, 1, z, M + "lily_of_the_valley", "nature")
    for z in (-12, -9, -7):
        for x in (-4, 4):
            put(x, 1, z, M + "azure_bluet", "nature")
    # two bare trees, branches attached to the trunk
    for (tx, tz, h, s) in ((-11, -6, 7, 1), (11, 16, 8, -1)):
        box(tx, 1, tz, tx, h, tz, log(), "nature")
        put(tx + s, h - 2, tz, log("x"), "nature"); put(tx + 2 * s, h - 2, tz, log("x"), "nature")
        put(tx + 2 * s, h - 1, tz, M + "dark_oak_fence", "nature")
        put(tx, h - 3, tz + 1, log("z"), "nature"); put(tx, h - 3, tz + 2, log("z"), "nature")
        put(tx, h - 2, tz + 2, M + "dark_oak_fence", "nature")
        put(tx - s, h, tz, log("x"), "nature")
    # carved pumpkins tucked into the bushes (the Halloween note)
    for (x, z) in ((-9, 1), (9, 9), (-4, -8)):
        put(x, 1, z, M + "carved_pumpkin[facing=north]", "nature")


# ===================================================================== hall
def hall():
    # plinth: polished deepslate ring one wider than the wall, stair skirt outside it
    for z in range(HZ0 - 1, HZ1 + 2):
        put(-HX - 1, 0, z, st(PDSTAIR, "east"), "structure"); put(HX + 1, 0, z, st(PDSTAIR, "west"), "structure")
    for x in range(-HX, HX + 1):
        put(x, 0, HZ1 + 1, st(PDSTAIR, "north"), "structure")
    box(-HX, 0, HZ0, HX, 0, HZ1, PDS, "structure")
    # walls: deepslate brick base (y1-2), calcite fill (y3-7), set back 1 behind the frame
    for x in (-6, 6):
        box(x, 1, HZ0, x, 2, HZ1, DSB, "fill"); box(x, 3, HZ0, x, 7, HZ1, CALC, "fill")
    for z in (HZ0, HZ1):
        box(-6, 1, z, 6, 2, z, DSB, "fill"); box(-6, 3, z, 6, 7, z, CALC, "fill")
    # frame: posts every 4 on the long sides and at the corners, plate beams on top
    for z in range(HZ0, HZ1 + 1, 4):
        for x in (-HX, HX):
            box(x, 1, z, x, 7, z, log(), "frame")
    for x in (-HX, HX):
        box(x, WALL_TOP, HZ0, x, WALL_TOP, HZ1, log("z"), "frame")
    for z in (HZ0, HZ1):
        box(-HX, WALL_TOP, z, HX, WALL_TOP, z, log("x"), "frame")
        for x in (-3, 3):
            box(x, 1, z if z == HZ1 else z, x, 7, z, log(), "frame")
    # bays between posts: brick wainscot stair at the foot, lancet window with sill and pointed head
    for z0 in range(HZ0, HZ1, 4):
        for x, out in ((-HX, "west"), (HX, "east")):
            inw = "east" if out == "west" else "west"
            for z in range(z0 + 1, z0 + 4):
                put(x, 1, z, st(M + "deepslate_brick_stairs", inw), "trim")
            zc = z0 + 2
            box(x + (1 if x < 0 else -1), 3, zc, x + (1 if x < 0 else -1), 6, zc, GLASS, "glass")
            put(x, 2, zc, st(PBSTAIR, inw, "top"), "trim")                        # sill
            put(x, 7, zc - 1, st(PBSTAIR, "south", "top"), "trim")                # pointed head
            put(x, 7, zc + 1, st(PBSTAIR, "north", "top"), "trim")
            put(x, 7, zc, PBWALL, "trim")
            # buttress against each inner post
        for x, s in ((-HX - 1, "east"), (HX + 1, "west")):
            if z0 > HZ0:
                box(x, 1, z0, x, 2, z0, DSB, "structure")
                put(x, 3, z0, st(M + "deepslate_brick_stairs", s), "structure")
    # back wall: moon window (sea lanterns behind white glass), framed in blackstone
    for dy in range(-3, 4):
        for dx in range(-3, 4):
            r = math.hypot(dx, dy)
            y = 5 + dy
            if r <= 3.2:
                put(dx, y, HZ1, M + "white_stained_glass", "glass")
                put(dx, y, HZ1 + 1, M + "sea_lantern", "light")
            elif r <= 3.9 and y >= 1:
                put(dx, y, HZ1, PBS, "trim")
    for dy in range(-4, 5):
        for dx in range(-4, 5):
            if 3.2 < math.hypot(dx, dy) <= 4.3 and (dx, 5 + dy, HZ1 + 1) not in V and 5 + dy >= 1:
                put(dx, 5 + dy, HZ1 + 1, PBS, "trim")                              # hides the lanterns outside


RTOP = {8: 8, 7: 9, 6: 11, 5: 12, 4: 14, 3: 15, 2: 17, 1: 18, 0: 20}   # 3:2 pitch, eaves y8 -> ridge y20
DORMERS = (6, 18)                                                       # over the bay windows below

def rtop(d):
    return RTOP[d]

def roof():
    """Steep 3:2 deepslate-tile roof along z, 1-block overhang with a stair soffit, blackstone ridge,
    blackstone bargeboards on the gable rakes, finials, and four lancet dormers."""
    for x in range(-HX - 1, HX + 2):
        d = abs(x)
        top = rtop(d)
        face = "east" if x < 0 else "west"
        for z in range(HZ0 - 1, HZ1 + 2):
            rake = z in (HZ0 - 1, HZ1 + 1)
            if x == 0:
                put(x, top - 1, z, TILE, "roof"); put(x, top - 2, z, TILE, "roof")
                put(x, top, z, PBWALL, "trim")
                continue
            put(x, top, z, st(PBSTAIR if rake else TSTAIR, face), "trim" if rake else "roof")
            for y in (top - 1, top - 2):
                if V.get((x, y, z), ("", ""))[1] != "frame":
                    put(x, y, z, TILE, "roof")
        if d == HX + 1:
            for z in range(HZ0 - 1, HZ1 + 2):
                put(x, top - 1, z, st(TSTAIR, "west" if x < 0 else "east", "top"), "roof")   # soffit
    # finials on both gable peaks
    for z in (HZ0 - 1, HZ1 + 1):
        put(0, rtop(0) + 1, z, PBWALL, "trim"); put(0, rtop(0) + 2, z, M + "end_rod[facing=up]", "light")
    # gable infill: calcite between a dark oak frame, two violet vents in the back gable
    for z in (HZ0, HZ1):
        for x in range(-6, 7):
            for y in range(WALL_TOP + 1, rtop(abs(x)) - 2):
                if (x, y, z) not in V:
                    put(x, y, z, CALC, "fill")
        box(0, WALL_TOP + 1, z, 0, rtop(0) - 3, z, log(), "frame")
        for x in (-4, 4):
            box(x, WALL_TOP + 1, z, x, rtop(4) - 3, z, log(), "frame")
        for x in range(-6, 7):                                             # collar beam across the gable
            if WALL_TOP + 4 <= rtop(abs(x)) - 3:
                put(x, WALL_TOP + 4, z, log("x"), "frame")
    for y in (13, 14):
        put(-2, y, HZ1, M + "purple_stained_glass", "glass"); put(2, y, HZ1, M + "purple_stained_glass", "glass")
    for c in DORMERS:
        for sgn in (-1, 1):
            dormer(c, sgn)


def dormer(c, sgn):
    """Small gabled lancet dormer on the roof slope, centred on bay z=c; sgn -1 = west side."""
    face_in = "east" if sgn < 0 else "west"
    X = lambda k: sgn * k
    # open the roof where the dormer sits
    for k in (5, 6):
        for z in range(c - 1, c + 2):
            for y in range(WALL_TOP + 1, 13):
                V.pop((X(k), y, z), None)
    # cheeks (side walls) and corner posts
    for z in (c - 1, c + 1):
        box(X(6), WALL_TOP + 1, z, X(6), 11, z, log(), "frame")
        box(X(5), WALL_TOP + 1, z, X(5), 11, z, CALC, "fill")
    # face: lancet window with a blackstone sill and pointed head
    put(X(6), WALL_TOP + 1, c, st(PBSTAIR, "west" if sgn < 0 else "east", "top"), "trim")
    box(X(6), 10, c, X(6), 11, c, M + "purple_stained_glass_pane[north=true,south=true]", "glass")
    put(X(6), 12, c, PBWALL, "trim")
    # little gable roof running in x, overhanging the face by one
    for k in (7, 6, 5):
        put(X(k), 11, c - 2, st(TSTAIR, "south"), "roof"); put(X(k), 11, c + 2, st(TSTAIR, "north"), "roof")
        put(X(k), 12, c - 1, st(TSTAIR, "south"), "roof"); put(X(k), 12, c + 1, st(TSTAIR, "north"), "roof")
        put(X(k), 13, c, TSLAB + "[type=bottom]", "roof")
        if k == 7:
            put(X(k), 10, c - 2, st(TSTAIR, "north", "top"), "roof"); put(X(k), 10, c + 2, st(TSTAIR, "south", "top"), "roof")
            put(X(k), 11, c - 1, st(TSTAIR, "north", "top"), "roof"); put(X(k), 11, c + 1, st(TSTAIR, "south", "top"), "roof")
            put(X(k), 12, c, st(TSTAIR, face_in, "top"), "roof")
        else:
            put(X(k), 12, c, TILE, "roof")
    put(X(6), 12, c, PBWALL, "trim")


# ===================================================================== entrance tower (secondary mass)
TX, TZ0, TZ1, TTOP = 3, -6, 0, 13

def tower():
    box(-TX - 1, 0, TZ0 - 1, TX + 1, 0, TZ1, PDS, "structure")
    for x in range(-TX - 1, TX + 2):
        put(x, 0, TZ0 - 2, st(PDSTAIR, "south"), "structure")
    box(-TX, 1, TZ0, TX, TTOP, TZ1 - 1, DSB, "fill")
    clear(-TX + 1, 1, TZ0 + 1, TX - 1, TTOP - 1, TZ1 - 1)               # hollow vestibule
    for x in (-TX, TX):                                                  # polished corner quoins
        for z in (TZ0,):
            for y in range(1, TTOP + 1):
                put(x, y, z, PDS if y % 2 else DSB, "frame")
    for y in (5, 10):                                                     # string courses
        for x in range(-TX - 1, TX + 2):
            put(x, y, TZ0 - 1, st(PBSTAIR, "south", "top"), "trim")
        for z in range(TZ0, TZ1):
            put(-TX - 1, y, z, st(PBSTAIR, "east", "top"), "trim")
            put(TX + 1, y, z, st(PBSTAIR, "west", "top"), "trim")
    # door: 3 wide, pointed head, dark oak frame, soul lanterns either side
    clear(-1, 1, TZ0, 1, 3, TZ0)
    put(-1, 4, TZ0, st(PBSTAIR, "east", "top"), "trim"); put(1, 4, TZ0, st(PBSTAIR, "west", "top"), "trim")
    clear(0, 4, TZ0, 0, 4, TZ0)
    put(0, 4, TZ0, M + "air", "air")
    for x in (-2, 2):
        box(x, 1, TZ0 - 1, x, 3, TZ0 - 1, log(), "frame")
        put(x, 4, TZ0 - 1, M + "soul_lantern", "light")
    # passage into the hall
    clear(-1, 1, TZ1, 1, 3, TZ1)
    put(-1, 4, TZ1, st(PBSTAIR, "east", "top"), "trim"); put(1, 4, TZ1, st(PBSTAIR, "west", "top"), "trim")
    # upper windows: amethyst moon roundel on the front, lancets on the sides
    for (dx, dy) in ((0, 7), (-1, 7), (1, 7), (0, 6), (0, 8)):
        put(dx, dy, TZ0, M + "purple_stained_glass", "glass")
    for z in (-4, -2):
        for x in (-TX, TX):
            box(x, 7, z, x, 8, z, GLASS, "glass")
    # belfry: open arches with iron bars
    for x in (-1, 0, 1):
        box(x, 11, TZ0, x, 12, TZ0, M + "iron_bars[east=true,west=true]", "trim")
    for z in (-4, -3, -2):
        for x in (-TX, TX):
            box(x, 11, z, x, 12, z, M + "iron_bars[north=true,south=true]", "trim")
    # vestibule floor and lights
    for x in range(-2, 3):
        for z in range(TZ0 + 1, TZ1):
            put(x, 0, z, PBS if (x + z) % 2 else CALC, "fill")
    put(0, 9, -3, M + "iron_chain", "trim"); put(0, 8, -3, M + "soul_lantern[hanging=true]", "light")
    box(-2, 9, TZ0 + 1, 2, 9, TZ1 - 1, M + "dark_oak_planks", "frame")                 # vestibule ceiling
    put(0, 9, -3, M + "iron_chain", "trim")
    # spire: eave ring, then tapering stages of 2, 3 and 4 blocks, needle tip
    for x in range(-TX - 1, TX + 2):
        put(x, TTOP + 1, TZ0 - 1, st(TSTAIR, "south"), "roof"); put(x, TTOP + 1, TZ1, st(TSTAIR, "north"), "roof")
    for z in range(TZ0 - 1, TZ1 + 1):
        put(-TX - 1, TTOP + 1, z, st(TSTAIR, "east"), "roof"); put(TX + 1, TTOP + 1, z, st(TSTAIR, "west"), "roof")
    box(-TX, TTOP + 1, TZ0, TX, TTOP + 1, TZ1 - 1, TILE, "roof")
    box(-2, TTOP + 2, TZ0 + 1, 2, TTOP + 3, TZ1 - 2, TILE, "roof")
    box(-1, TTOP + 4, TZ0 + 2, 1, TTOP + 6, TZ1 - 3, TILE, "roof")
    for z in range(TZ0 + 1, TZ1 - 1):
        put(-3, TTOP + 2, z, st(TSTAIR, "east"), "roof"); put(3, TTOP + 2, z, st(TSTAIR, "west"), "roof")
    for x in range(-2, 3):
        put(x, TTOP + 2, TZ0, st(TSTAIR, "south"), "roof"); put(x, TTOP + 2, TZ1 - 1, st(TSTAIR, "north"), "roof")
    for z in range(TZ0 + 2, TZ1 - 2):
        put(-2, TTOP + 4, z, st(TSTAIR, "east"), "roof"); put(2, TTOP + 4, z, st(TSTAIR, "west"), "roof")
    for x in range(-1, 2):
        put(x, TTOP + 4, TZ0 + 1, st(TSTAIR, "south"), "roof"); put(x, TTOP + 4, TZ1 - 2, st(TSTAIR, "north"), "roof")
    box(0, TTOP + 7, -3, 0, TTOP + 10, -3, PBWALL, "trim")
    put(0, TTOP + 11, -3, M + "end_rod[facing=up]", "light")


# ===================================================================== interior
def interior():
    # floor: blackstone border, calcite/deepslate checker field, amethyst medallion under the dancers
    for x in range(-5, 6):
        for z in range(1, HZ1):
            if abs(x) == 5 or z in (1, HZ1 - 1):
                b = PBS
            elif (x + z) % 2:
                b = CALC
            else:
                b = PDS
            put(x, 0, z, b, "fill")
    for (mx, mz) in ((0, 11),):
        for dx in range(-1, 2):
            for dz in range(-1, 2):
                put(mx + dx, 0, mz + dz, AMETHYST, "trim")
    # violet runner from the door to the dance medallion
    for z in range(1, 9):
        put(0, 1, z, M + "purple_carpet", "trim")
    # potted ferns at the stage corners
    for x in (-5, 5):
        put(x, 2, 23, M + "potted_fern", "nature")
    # stage: raised dark oak dais at the back with a stair front edge
    box(-5, 1, 19, 5, 1, HZ1 - 1, M + "dark_oak_planks", "fill")
    for x in range(-5, 6):
        put(x, 1, 19, st(M + "dark_oak_stairs", "south"), "trim")
    # wainscot: open dark oak trapdoors on the side walls
    for z in range(1, HZ1):
        if z % 4 == 2:
            continue                                                        # leave window bays open
        for x, f in ((-5, "east"), (5, "west")):
            for y in (1, 2):
                if (x, y, z) not in V:
                    put(x, y, z, M + f"dark_oak_trapdoor[facing={f},half=bottom,open=true]", "trim")
    # tie beams and king posts every 4 (trusses carry the frame inside), fence braces
    for z in range(4, HZ1, 4):
        box(-6, WALL_TOP, z, 6, WALL_TOP, z, log("x", True), "frame")
        box(0, WALL_TOP + 1, z, 0, rtop(0) - 3, z, log(stripped=True), "frame")
        for k in (2, 4):                                          # queen posts from the tie beam to the rafters
            box(k, WALL_TOP + 1, z, k, rtop(k) - 3, z, M + "dark_oak_fence", "frame")
            box(-k, WALL_TOP + 1, z, -k, rtop(k) - 3, z, M + "dark_oak_fence", "frame")
    # two chandeliers on chains from the tie beams: blackstone cross, four soul lanterns
    for cz in (8, 16):
        put(0, 7, cz, M + "iron_chain", "trim")
        put(0, 6, cz, PBWALL, "trim")
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            put(dx, 6, cz + dz, PBS + "_slab[type=top]" if False else M + "polished_blackstone_slab[type=top]", "trim")
            put(2 * dx, 6, cz + 2 * dz, M + "polished_blackstone_slab[type=top]", "trim")
            put(2 * dx, 5, cz + 2 * dz, M + "soul_lantern[hanging=true]", "light")
    # side tables for the ghost lanterns (blackstone wall + slab top)
    for x in (-5, 5):
        put(x, 1, 12, PBWALL, "trim")
    # hidden light so every floor block reads >= 8
    for x in (-3, 0, 3):
        for z in range(2, HZ1, 3):
            put(x, 4, z, M + "light[level=11]", "light")
    for x in (-1, 1):
        put(x, 4, -3, M + "light[level=11]", "light")
    # welcome signs in the vestibule
    for x, f, lines in ((-2, "east", ("Welcome to the", "Moonlit Ballroom", "~", "Mistbloom Studios")),
                        (2, "west", ("Friendly ghosts", "6 animated pieces", "Plain Nexo", "no add-ons"))):
        msg = ",".join('{"text":"%s","color":"#f2c97d"}' % l for l in lines)
        put(x, 2, -4, M + 'dark_oak_wall_sign[facing=%s]{front_text:{has_glowing_text:1b,messages:[%s]}}' % (f, msg), "trim")



def details():
    # swan-neck lantern crooks on the side posts (the repeated motif, 3 per side)
    for z in (4, 12, 20):
        for sgn in (-1, 1):
            put(sgn * 8, 6, z, M + "dark_oak_fence", "trim")
            put(sgn * 9, 6, z, M + "dark_oak_fence", "trim")
            put(sgn * 9, 5, z, M + "soul_lantern[hanging=true]", "light")
    # tower: corbel band under the eave ring
    for x in range(-TX - 1, TX + 2):
        put(x, TTOP, TZ0 - 1, st(PBSTAIR, "north", "top"), "trim")
    for z in range(TZ0 - 1, TZ1):
        put(-TX - 1, TTOP, z, st(PBSTAIR, "east", "top"), "trim"); put(TX + 1, TTOP, z, st(PBSTAIR, "west", "top"), "trim")
    # tower: corner pinnacles on the eave ring
    for x in (-TX - 1, TX + 1):
        put(x, TTOP + 1, TZ0 - 1, PBS, "trim")
        put(x, TTOP + 2, TZ0 - 1, PBWALL, "trim")
        put(x, TTOP + 3, TZ0 - 1, M + "end_rod[facing=up]", "light")
    # tower: stepped corner buttresses at the front
    for x, f in ((-TX - 1, "west"), (TX + 1, "east")):
        box(x, 1, TZ0 - 1, x, 3, TZ0 - 1, DSB, "structure")
        put(x, 4, TZ0 - 1, st(M + "deepslate_brick_stairs", "north"), "structure")
    # door hood: blackstone slab canopy on two iron chains
    # front gable face (visible beside the tower): small lancets either side
    for x in (-5, 5):
        box(x, 4, HZ0, x, 6, HZ0, GLASS.replace("north=true,south=true", "east=true,west=true"), "glass")
        put(x, 3, HZ0 - 1, st(PBSTAIR, "north", "top"), "trim")
    # roof ridge cresting: small iron spikes between the trusses


def build_all():
    V.clear()
    island(); garden(); hall(); roof(); tower(); interior(); details()
    # every interior cell of hall and vestibule must be air
    for (x, y, z) in list(V):
        if -5 <= x <= 5 and 1 <= y <= 7 and 1 <= z <= HZ1 - 1 and V[(x, y, z)][1] in ("terrain",):
            V.pop((x, y, z))
    return V


# ===================================================================== checks
def flood_gaps():
    """Flood from the middle of the hall through air; it may leave only through the doors."""
    solid = {p for p, (b, r) in V.items() if r != "air" and "light[" not in b}
    solid |= {(x, y, TZ0) for x in (-1, 0, 1) for y in (1, 2, 3, 4)}       # treat the front door as shut
    start = (0, 3, 10)
    seen, q, leaks = {start}, deque([start]), set()
    while q:
        x, y, z = q.popleft()
        for d in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
            n = (x + d[0], y + d[1], z + d[2])
            if n in seen or n in solid:
                continue
            if not (-8 <= n[0] <= 8 and 0 <= n[1] <= 26 and TZ0 - 2 <= n[2] <= HZ1 + 2):
                leaks.add((x, y, z))
                continue
            seen.add(n); q.append(n)
    door = {(x, y, TZ0) for x in (-1, 0, 1) for y in (1, 2, 3, 4)}
    return sorted(leaks)


def floating():
    solid = {p for p, (b, r) in V.items() if r not in ("air",) and "light[" not in b}
    ground = {p for p in solid if p[1] <= 0}
    seen, q = set(ground), deque(ground)
    while q:
        x, y, z = q.popleft()
        for d in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
            n = (x + d[0], y + d[1], z + d[2])
            if n in solid and n not in seen:
                seen.add(n); q.append(n)
    return [p for p in solid - seen]


# ===================================================================== commands
def commands():
    """Merge runs along x into fills."""
    out = []
    keys = sorted(V, key=lambda p: (p[1], p[2], p[0]))
    i = 0
    while i < len(keys):
        x, y, z = keys[i]
        b = V[keys[i]][0]
        j = i
        while j + 1 < len(keys) and keys[j + 1] == (keys[j][0] + 1, y, z) and V[keys[j + 1]][0] == b:
            j += 1
        x2 = keys[j][0]
        wx, wy, wz = O[0] + x, O[1] + y, O[2] + z
        if x2 == x:
            out.append(f"setblock {wx} {wy} {wz} {b}")
        else:
            out.append(f"fill {wx} {wy} {wz} {O[0] + x2} {wy} {wz} {b}")
        i = j + 1
    return out
