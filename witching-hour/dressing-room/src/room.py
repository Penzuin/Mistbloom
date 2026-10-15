"""Witching Hour dressing room - an HMCCosmetics wardrobe build for the Witching Hour cosmetics.

Story: the witch's dressing parlour. Before midnight she walks the runner past her six
alcoves (two hats, the broom, the lantern, the grimoire and the wisp), steps up onto the
round dais and checks the look against the glowing moon window.

Wardrobe: the player's clone stands on the dais facing the door, the camera floats over the
runner 6 blocks away, so the moon window is the backdrop of every try-on.

Palette "Witch's Parlour"
  base    polished deepslate (floor border, wainscot, dais, plinth), deepslate bricks outside
  frame   dark oak log, stripped dark oak (posts, plates, tie beams, purlin)
  walls   purple terracotta panels between the frame
  floor   spruce planks field, black carpet runner
  roof    deepslate tiles, dark oak lining inside
  accent  violet (purple glass, purple carpet, amethyst, purple candles), moon gold (yellow glass)
  light   warm lanterns + purple candles, hidden light blocks, sea lanterns only behind glass
  motif   the crescent moon appears once: the round window behind the dais

Local frame: x across (centre 0), y up (0 = floor block), z from the door (-) to the back wall (+).
"""
import math

M = "minecraft:"
V = {}            # (x, y, z) -> (block, role)
DISPLAYS = []     # dicts: id, slot, target (x, y, z), anchor ('center'|'bottom'), yaw, scale, tilt
SIGNS = []        # (x, y, z, block_state, lines, click_command or None)
NOTES = {}

WARDROBE_ID = "witching_hour"
NPC = (0.5, 2.0, 12.5, 180.0, 0.0)          # stands on the dais carpet, facing the door
VIEWER = (0.5, 1.6, 8.5, 0.0, 6.0)          # camera floats over the runner, 4 blocks out (eye ~3.2)
LEAVE = (0.5, 1.0, 2.5, 0.0, 0.0)           # back on the runner, facing the dais
ARRIVE = (0.5, 0.0, -12.5, 0.0, 5.0)        # end of the island path, facing the door


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


def log(axis="y", stripped=False):
    return M + ("stripped_" if stripped else "") + f"dark_oak_log[axis={axis}]"


PD, PDSLAB, PDWALL = M + "polished_deepslate", M + "polished_deepslate_slab", M + "polished_deepslate_wall"
DB, DBSTAIR, DBSLAB = M + "deepslate_bricks", M + "deepslate_brick_stairs", M + "deepslate_brick_slab"
CHIS = M + "chiseled_deepslate"
TERRA = M + "purple_terracotta"
DOP, DOSTAIR, DOSLAB, DOFENCE = M + "dark_oak_planks", M + "dark_oak_stairs", M + "dark_oak_slab", M + "dark_oak_fence"
SPR = M + "spruce_planks"
TILE, TSTAIR, TSLAB = M + "deepslate_tiles", M + "deepslate_tile_stairs", M + "deepslate_tile_slab"
SEA = M + "sea_lantern"


def glass(color):
    return M + f"{color}_stained_glass"


def pane(color, plane):
    """plane 'x' = pane spans x (sits in a z wall), 'z' = spans z (sits in an x wall)."""
    sides = "east=true,west=true" if plane == "x" else "north=true,south=true"
    return M + f"{color}_stained_glass_pane[{sides}]"


POSTS_Z = (-1, 3, 7, 11, 15)
BAYS = ((0, 2), (4, 6), (8, 10))
SIDES = (-1, 1)


def interior(x, z):
    """Cells with air at y 1..6 inside the room."""
    if abs(x) <= 6 and 0 <= z <= 14:
        return True
    if abs(x) in (7, 8) and any(a <= z <= b for a, b in BAYS):
        return True
    if abs(x) == 7 and 12 <= z <= 14:
        return True
    return False


# ===================================================================== shell
def foundation():
    # y 0: one slab of polished deepslate under everything, plinth stairs round the outside
    box(-10, 0, -2, 10, 0, 17, PD, "structure")
    for x in range(-10, 11):
        put(x, 0, -2, st(DBSTAIR, "south"), "structure")
        put(x, 0, 17, st(DBSTAIR, "north"), "structure")
    for z in range(-2, 18):
        put(-10, 0, z, st(DBSTAIR, "east", shape=None), "structure")
        put(10, 0, z, st(DBSTAIR, "west"), "structure")
    for (x, z, f, s) in ((-10, -2, "east", "outer_right"), (10, -2, "west", "outer_left"),
                         (-10, 17, "east", "outer_left"), (10, 17, "west", "outer_right")):
        put(x, 0, z, st(DBSTAIR, f, shape=s), "structure")
    put(0, 0, -2, PD, "structure")          # door step
    # floor field and border
    for x in range(-8, 9):
        for z in range(0, 15):
            if not interior(x, z):
                continue
            field = abs(x) <= 5 and 1 <= z <= 13
            put(x, 0, z, SPR if field else PD, "fill")


def walls():
    for s in SIDES:
        X = 9 * s
        for z in range(-1, 17):
            put(X, 1, z, PD, "structure")
            for y in range(2, 6):
                put(X, y, z, TERRA, "fill")
            put(X, 6, z, log("z", True), "frame")
        for z in (-1, 16):
            for y in range(1, 7):
                put(X, y, z, log("y"), "frame")
        # inner fill: piers between bays, the solid strip behind the dais, wall above the bays
        for z in range(-1, 16):
            for x in (7 * s, 8 * s):
                if interior(x, z):
                    continue
                for y in range(1, 7):
                    put(x, y, z, PD if y == 1 else TERRA, "fill")
        for z in POSTS_Z[1:4]:
            for y in range(1, 7):
                put(7 * s, y, z, log("y"), "frame")
        # bays: lintel line, little pointed arch, light up in the apex
        for (a, b) in BAYS:
            for z in range(a, b + 1):
                put(8 * s, 5, z, TERRA, "fill")
                put(8 * s, 6, z, TERRA, "fill")
                put(7 * s, 6, z, log("z", True), "frame")
            put(7 * s, 5, a, st(DOSTAIR, "north", "top"), "trim")
            put(7 * s, 5, b, st(DOSTAIR, "south", "top"), "trim")
        # wall plate over the dais strip
        for z in range(12, 15):
            put(8 * s, 6, z, log("z", True), "frame")
    # front wall z = -1
    for x in range(-8, 9):
        put(x, 1, -1, PD, "structure")
        for y in range(2, 6):
            put(x, y, -1, TERRA, "fill")
        put(x, 6, -1, log("x", True), "frame")
    for x in (-3, 3, -1, 1):
        for y in range(1, 6):
            put(x, y, -1, log("y"), "frame")
    put(0, 1, -1, M + "dark_oak_door[facing=south,half=lower,hinge=left,open=false]", "structure")
    put(0, 2, -1, M + "dark_oak_door[facing=south,half=upper,hinge=left,open=false]", "structure")
    for x in (-1, 0, 1):
        put(x, 3, -1, log("x", True), "frame")
    # front lancets either side of the door (x = +-6)
    for x in (-6, 6):
        put(x, 2, -1, pane("purple", "x"), "glass")
        put(x, 3, -1, pane("purple", "x"), "glass")
        put(x, 4, -1, pane("purple", "x"), "glass")
    # back wall: inner face z = 15, outer face z = 16
    for x in range(-8, 9):
        put(x, 1, 15, PD, "structure")
        for y in range(2, 7):
            put(x, y, 15, TERRA, "fill")
    for x in range(-9, 10):
        put(x, 1, 16, PD, "structure")
        for y in range(2, 6):
            put(x, y, 16, TERRA, "fill")
        put(x, 6, 16, log("x", True), "frame")
    for x in (-5, 5):
        for y in range(1, 7):
            put(x, y, 15, log("y"), "frame")


MOON_ART = {        # y: row from x = -3 to 3; Y gold, P violet, . frame
    8: "..YPP..",
    7: ".YPPPP.",
    6: "YYPPPPP",
    5: "YYPPPPP",
    4: "YYPPPPP",
    3: ".YPPPP.",
    2: "..YPP..",
}


def moon_window():
    """Round window behind the dais, a gold crescent on violet, sea lanterns behind the glass."""
    cy = 5
    for x in range(-4, 5):
        for y in range(1, 10):
            row = MOON_ART.get(y)
            c = row[x + 3] if row and -3 <= x <= 3 else "."
            if c != ".":
                put(x, y, 15, glass("yellow" if c == "Y" else "purple"), "glass")
                put(x, y, 16, SEA, "light")

            elif math.hypot(x, y - cy) <= 4.3:
                put(x, y, 15, DOP, "frame")
                put(x, y, 16, DOP, "frame")
    # outside, the window is covered by a plain panel between the back posts (one moon is enough)
    for x in range(-4, 5):
        put(x, 1, 17, PD, "structure")
        for y in range(2, 6):
            put(x, y, 17, TERRA, "fill")
        put(x, 6, 17, log("x", True), "frame")
    for x in range(-3, 4):                    # carry the panel up the gable over the top of the window, tiled cap
        top = 9                               # one flat-topped panel, the window tops out at y 9
        for y in range(7, top + 1):
            put(x, y, 17, TERRA, "fill")
        put(x, top + 1, 17, st(TSTAIR, "north"), "roof")
    NOTES["moon"] = (0, cy, 15)


def gables():
    """Gable ends at z = -1 (front) and z = 15/16 (back), framed edge, king post, small crescent window."""
    for z, mat in ((-1, TERRA), (15, TERRA), (16, TERRA)):
        for k in range(0, 10):
            y = 7 + k
            for x in range(-(9 - k), 10 - k):
                if (x, y, z) in V:
                    continue
                edge = abs(x) == 9 - k
                put(x, y, z, DOP if edge else mat, "frame" if edge else "fill")
    for y in range(7, 16):
        put(0, y, -1, log("y"), "frame")
    for y in range(10, 16):
        put(0, y, 16, log("y"), "frame")


def roof():
    for z in range(-2, 18):
        for k in range(0, 10):
            y = 7 + k
            put(-(10 - k), y, z, st(TSTAIR, "east"), "roof")
            put(10 - k, y, z, st(TSTAIR, "west"), "roof")
            if k >= 1:
                for x in (-(10 - k), 10 - k):
                    if (x, y - 1, z) not in V:
                        put(x, y - 1, z, DOP, "roof")          # wood lining under the tiles
        put(0, 16, z, TILE, "roof")
        put(0, 17, z, TSLAB + "[type=bottom]", "trim")
        put(-10, 6, z, DOSLAB + "[type=top]", "trim")           # soffit under the eaves
        put(10, 6, z, DOSLAB + "[type=top]", "trim")
    put(0, 18, -2, M + "lightning_rod[facing=up]", "trim")      # finials at both ridge ends
    put(0, 18, 17, M + "lightning_rod[facing=up]", "trim")


def exterior():
    # front and back posts stand proud of the wall on the plinth
    for x in (-9, -3, 3, 9):
        put(x, 0, -2, PD, "structure")
        for y in range(1, 7):
            put(x, y, -2, log("y"), "frame")
    for x in (-9, -5, 5, 9):
        put(x, 0, 17, PD, "structure")
        for y in range(1, 7):
            put(x, y, 17, log("y"), "frame")
    # side buttresses at the inner posts
    for s in SIDES:
        for z in POSTS_Z[1:4]:
            put(10 * s, 1, z, DB, "structure")
            put(10 * s, 2, z, DB, "structure")
            put(10 * s, 3, z, st(DBSTAIR, "east" if s < 0 else "west"), "structure")
        # side lancets by the dais, glowing from both sides
        for y in range(2, 5):
            put(8 * s, y, 13, glass("purple"), "glass")
            put(9 * s, y, 13, SEA, "light")
            put(10 * s, y, 13, glass("purple"), "glass")
        put(10 * s, 1, 13, DBSLAB + "[type=top]", "trim")
        put(10 * s, 5, 13, st(DBSTAIR, "east" if s < 0 else "west", "top"), "trim")
    # door hood: dark oak bracket roof over the door
    for x in (-1, 0, 1):
        put(x, 4, -2, DOSLAB + "[type=bottom]", "trim")
    put(-1, 3, -2, st(DOSTAIR, "east", "top"), "trim")
    put(1, 3, -2, st(DOSTAIR, "west", "top"), "trim")
    put(-2, 2, -2, M + "lantern[hanging=false]", "light")     # lanterns on fence posts either side of the door
    put(2, 2, -2, M + "lantern[hanging=false]", "light")
    put(-2, 1, -2, DOFENCE, "structure")
    put(2, 1, -2, DOFENCE, "structure")


# ===================================================================== interior
def ceiling():
    for z in POSTS_Z[1:4]:
        for x in range(-8, 9):
            put(x, 7, z, log("x", True), "frame")
    for z in range(0, 15):
        if z not in POSTS_Z:
            put(0, 7, z, log("z", True), "frame")
    # lanterns along the aisle hang from the purlin, the chandelier over the dais on a chain
    for z in (1, 5, 9):
        put(0, 6, z, M + "lantern[hanging=true]", "light")
    put(0, 6, 12, M + "iron_chain[axis=y]", "light")
    put(0, 5, 12, M + "lantern[hanging=true]", "light")


def dais():
    cx, cz = 0, 12
    for x in range(-3, 4):
        for z in range(9, 15):
            r = math.hypot(x - cx, z - cz)
            if r <= 1.6:
                put(x, 1, z, PD, "structure")
                put(x, 2, z, M + "purple_carpet", "furniture")
            elif r <= 2.55:
                put(x, 1, z, PDSLAB + "[type=bottom]", "structure")
    # candle stands framing the figure
    for x in (-5, 5):
        put(x, 1, 13, PDWALL, "furniture")
        put(x, 2, 13, PDWALL, "furniture")
        put(x, 3, 13, M + "purple_candle[candles=4,lit=true]", "light")
    # amethyst on the strips beside the dais
    for s in SIDES:
        put(7 * s, 1, 12, M + "amethyst_block", "trim")
        put(7 * s, 2, 12, M + "amethyst_cluster[facing=up]", "light")
        put(7 * s, 1, 14, M + "amethyst_block", "trim")
        put(7 * s, 2, 14, M + "amethyst_cluster[facing=up]", "light")
    NOTES["dais"] = (cx, 2, cz)


def runner():
    for z in range(0, 9):
        for x in (-1, 0, 1):
            put(x, 1, z, M + "black_carpet", "furniture")


def displays():
    """The six alcoves. Left (west): hat, crown, broom. Right (east): lantern, grimoire, wisp.
    Each alcove: a glowing violet lancet in its back wall, the cosmetic in front of it at the
    alcove mouth, a candle shelf in one back corner and a nameplate in the other."""
    face = {-1: 270.0, 1: 90.0}            # left alcoves face east, right face west
    for s_ in SIDES:
        for (a, b) in BAYS:
            z = a + 1
            for y in range(2, 5):
                put(8 * s_, y, z, glass("purple"), "glass")
                put(9 * s_, y, z, SEA, "light")
                put(10 * s_, y, z, glass("purple"), "glass")          # the lancet shows outside too
            put(10 * s_, 1, z, DBSLAB + "[type=top]", "trim")
            put(10 * s_, 5, z, st(DBSTAIR, "east" if s_ < 0 else "west", "top"), "trim")
            sh = a if (s_, a) == (-1, 8) else b      # the broom alcove keeps its shelf on the other side
            put(8 * s_, 3, sh, DOSLAB + "[type=top]", "furniture")
            put(8 * s_, 4, sh, M + "purple_candle[candles=2,lit=true]", "light")

    def cx(s_):                             # centre of the alcove-mouth block on that side
        return 7 * s_ + 0.5
    # hat stands: chiseled deepslate base, dark oak post, a skeleton skull for a head; the hat sits on the skull
    for (s_, z, key) in ((-1, 1, "witch_hat"), (-1, 5, "candle_crown")):
        put(7 * s_, 1, z, CHIS, "furniture")
        put(7 * s_, 2, z, DOFENCE, "furniture")
        put(7 * s_, 3, z, M + f"skeleton_skull[rotation={12 if s_ < 0 else 4}]", "furniture")
        # the witch hat's brim is 1.2 wide: nudge it 0.1 toward the aisle so it clears the lancet glass
        nudge = 0.1 * -s_ if key == "witch_hat" else 0.0
        DISPLAYS.append(dict(id=key, target=(cx(s_) + nudge, 3.25, z + 0.5), anchor="pivot", yaw=face[s_]))
    # broom hangs diagonally across its lancet like a trophy, on a dark oak rail
    put(-7, 1, 9, PDSLAB + "[type=bottom]", "furniture")
    DISPLAYS.append(dict(id="moonlit_broom", target=(-6.85, 3.1, 9.5), anchor="center", yaw=270.0))
    # ghostlight lantern hangs on a chain from the alcove's arch
    put(7, 5, 1, DOP, "furniture")                                     # hanger block in the arch apex
    put(7, 4, 1, M + "iron_chain[axis=y]", "furniture")
    DISPLAYS.append(dict(id="ghostlight_lantern", target=(cx(1), 3.98, 1.5), anchor="top", yaw=face[1]))
    # grimoire on a lectern-height pedestal
    put(7, 1, 5, CHIS, "furniture")
    put(7, 2, 5, PDSLAB + "[type=bottom]", "furniture")
    DISPLAYS.append(dict(id="grimoire", target=(cx(1), 2.5, 5.5), anchor="bottom", yaw=180.0, mult=1.6))   # cover to the aisle
    # wisp floats over an amethyst cluster
    put(7, 1, 9, CHIS, "furniture")
    put(7, 2, 9, M + "amethyst_cluster[facing=up]", "light")
    DISPLAYS.append(dict(id="wisp", target=(cx(1), 3.75, 9.5), anchor="center", yaw=face[1]))
    names = {"witch_hat": ("Moonlit", "Witch Hat"), "candle_crown": ("Candle", "Crown"),
             "moonlit_broom": ("Moonlit", "Broom"), "ghostlight_lantern": ("Ghostlight", "Lantern"),
             "grimoire": ("Moon", "Grimoire"), "wisp": ("", "Wisp")}
    for d in DISPLAYS:
        x, _, z = d["target"]
        s_ = -1 if x < 0 else 1
        a = next(a for a, b in BAYS if a <= z <= b + 1)
        f = "east" if s_ < 0 else "west"
        zs = a + 2 if d["id"] == "moonlit_broom" else a
        SIGNS.append((8 * s_, 2, zs, M + f"dark_oak_wall_sign[facing={f}]", names[d["id"]], None))
    # the try-on sign stands by the runner, just behind the wardrobe camera
    SIGNS.append((-2, 1, 7, M + "dark_oak_sign[rotation=8]",
                  ("Witching Hour", "~ try it on ~", "", "click me"), f"cosmetics wardrobes {WARDROBE_ID}"))
    # welcome board inside the door
    SIGNS.append((-2, 2, 0, M + "dark_oak_wall_sign[facing=south]",
                  ("Witching Hour", "dressing room", "", "Mistbloom Studios"), None))


def hidden_lights():
    for s in SIDES:
        for (a, b) in BAYS:
            if (7 * s, 4, (a + b) // 2) not in V:
                put(7 * s, 4, (a + b) // 2, M + "light[level=12]", "light")
            else:
                put(7 * s, 3, a, M + "light[level=12]", "light")
        put(7 * s, 4, 13, M + "light[level=11]", "light")
    for z in (2, 6, 10):
        for x in (-4, 4):
            put(x, 5, z, M + "light[level=13]", "light")
    put(0, 4, 10, M + "light[level=12]", "light")
    for x in (-3, 3):                                          # fill light over the floor between the alcoves
        for z in (4, 7, 10):
            put(x, 3, z, M + "light[level=12]", "light")             # key light on the figure's face


def build_room():
    V.clear(); DISPLAYS.clear(); SIGNS.clear(); NOTES.clear()
    foundation(); walls(); moon_window(); gables(); roof(); exterior()
    ceiling(); dais(); runner(); displays(); hidden_lights()
    # signs become blocks too (text is written by the datapack)
    for (x, y, z, b, lines, cmd) in SIGNS:
        put(x, y, z, b, "furniture")
    return V


# ===================================================================== island for the Selling Test showcase
IRX, IRZ, ICZ = 22, 26, 3


def edge(x, z):
    return 1 + 0.05 * math.sin(x * 0.55 + 1.3) + 0.045 * math.cos(z * 0.43) + 0.03 * math.sin((x - z) * 0.9)


def island():
    """Small floating isle; its grass top is y = -1 so the room's plinth sits on it."""
    for x in range(-IRX - 3, IRX + 4):
        for z in range(ICZ - IRZ - 3, ICZ + IRZ + 4):
            e = edge(x, z)
            d = math.hypot(x / IRX, (z - ICZ) / IRZ)
            if d > e:
                continue
            k = max(0.0, 1 - d / e)
            depth = int(3 + 20 * k ** 0.75 + 2 * math.sin(x * 0.7) * math.cos(z * 0.5))
            if (x, 0, z) not in V:
                put(x, -1, z, M + "grass_block", "terrain")
            else:
                put(x, -1, z, M + "dirt", "terrain")
            for y in range(-2, -depth - 2, -1):
                b = M + "dirt" if y >= -3 else M + "stone" if y >= -8 else M + "tuff" if y >= -13 else M + "deepslate"
                put(x, y, z, b, "terrain")
            h = (x * 73 + z * 37) % 23
            if depth >= 9 and h == 0:
                put(x, -depth - 2, z, M + "hanging_roots", "nature")
    # path from the landing to the door step
    for z in range(-20, -2):
        for x in range(-2, 3):
            if (x, -1, z) in V:
                put(x, -1, z, M + ("dirt_path" if abs(x) <= 1 else "coarse_dirt"), "terrain")
    # two lamp posts where the path meets the plinth
    for x in (-3, 3):
        put(x, 0, -6, PDWALL, "structure")
        put(x, 1, -6, PDWALL, "structure")
        put(x, 2, -6, M + "lantern[hanging=false]", "light")
    # bushes along the foundation (about half its length), never touching windows
    Lf = M + "dark_oak_leaves[persistent=true]"
    for z in range(-1, 17):
        if z % 3 != 1 and z != 13:
            put(-11, 0, z, Lf, "nature")
            put(11, 0, z, Lf, "nature")
    for x in (-8, -7, -6, 6, 7, 8):
        put(x, 0, -3, Lf, "nature")
    # hidden light over open grass so nothing spawns
    for x in range(-IRX, IRX + 1, 6):
        for z in range(ICZ - IRZ, ICZ + IRZ + 1, 6):
            if V.get((x, -1, z), ("", ""))[0] == M + "grass_block" and (x, 0, z) not in V:
                put(x, 0, z, M + "light[level=9]", "light")


def build_all(with_island=True):
    build_room()
    if with_island:
        island()
    return V
