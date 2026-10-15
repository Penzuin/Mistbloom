"""Hollowmere hero pieces, v2. Front faces NORTH (-z)."""
import random
import numpy as np
import engine
from engine import Model, wood, solid, stripes, scallop, T, _blank, fr, animated, SIDES, art
from spooky import (pumpkin_skin, brew, hay, stone, plaid, sack, candle_flame, wax,
                    BAT, LEAF, VINE, STRAW, COBWEB)

# ------------------------------------------------------------------ painters
FACE = [
    "................",
    "................",
    "...##......##...",
    "..####....####..",
    ".######..######.",
    "................",
    ".......##.......",
    "......####......",
    "................",
    ".##..........##.",
    ".###.######.###.",
    "..############..",
    "....###..###....",
    "................",
]


def carved():
    """Pumpkin skin with the face cut out; the cut edge shows pale flesh, so the carving has depth."""
    base = pumpkin_skin(stem_top=False)
    def f(w, h, fc, key):
        img = base(w, h, fc, key)
        if fc != "north":
            return img
        hole = np.zeros((h, w), bool)
        for y in range(h):
            for x in range(w):
                hole[y, x] = FACE[int(y * 14 / h)][int(x * 16 / w)] == "#"
        for y in range(h):
            for x in range(w):
                if hole[y, x]:
                    img[y, x, 3] = 0
                elif (y > 0 and hole[y - 1, x]) or (x > 0 and hole[y, x - 1]):
                    img[y, x] = T("hay", 0)          # cut flesh catching the light
                elif (y + 1 < h and hole[y + 1, x]):
                    img[y, x] = T("pumpkin", 4)      # shadow above each cut
        return img
    return f


def glow_core(lit=True):
    def f(w, h, fc, key):
        img = _blank(w, h)
        k = fr() if lit else 0
        for y in range(h):
            for x in range(w):
                if lit:
                    img[y, x] = T("candle", (0, 1, 0, 2, 1, 0)[(k + x // 2 + y) % 6])
                else:
                    img[y, x] = T("ebony", 5 + (x + y) % 2)
        return img
    return animated(f) if lit else f


def cast_iron(seed=0):
    """Dark hammered iron: mottled dents, a rivet band and a cool highlight."""
    def f(w, h, fc, key):
        rng = random.Random(key)
        img = _blank(w, h)
        for y in range(h):
            for x in range(w):
                img[y, x] = T("coal", 2 if rng.random() < 0.85 else rng.choice([1, 3]))
        if fc in SIDES and h >= 4:
            for x in range(2, w - 1, 4):
                img[1, x] = T("coal", 0)             # rivets
            hx = max(1, w // 4)
            img[2:h - 1, hx] = T("slate", 3)         # specular streak
        return img
    return f


def bark(ramp="ebony"):
    def f(w, h, fc, key):
        rng = random.Random(key)
        img = _blank(w, h)
        vertical = h >= w
        for y in range(h):
            for x in range(w):
                a = x if vertical else y
                tone = 2 + (a % 3 == 0) + (1 if rng.random() < 0.12 else 0) - (1 if rng.random() < 0.08 else 0)
                img[y, x] = T(ramp, tone)
        return img
    return f


def patch_art():
    return art([
        "aaaaa",
        "abbba",
        "abcba",
        "abbba",
        "aaaaa",
    ], {"a": ("rust", 1), "b": ("denim", 1), "c": ("denim", 2)})


CROW = art([
    "...aa..",
    "..abca.",
    ".aaaa..",
    "aaaaa..",
    ".aaa...",
], {"a": ("ebony", 5), "b": ("pumpkin", 0), "c": ("hay", 1)})

MOON_BOARD = None


def moon_board():
    """Wooden sign with a gold crescent moon and three little stars."""
    base = wood("ebony", plank=2)
    def f(w, h, fc, key):
        img = base(w, h, fc, key)
        if fc not in ("north", "south") or w < 8 or h < 6:
            return img
        img[0, :] = img[-1, :] = T("gold", 2)
        img[:, 0] = img[:, -1] = T("gold", 2)
        cx, cy, r = w // 2 - 1, h // 2, min(w, h) * 0.32
        for y in range(h):
            for x in range(w):
                d1 = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
                d2 = ((x - cx - r * 0.55) ** 2 + (y - cy + r * 0.25) ** 2) ** 0.5
                if d1 <= r and d2 > r * 0.85:
                    img[y, x] = T("gold", 0 if d1 < r * 0.6 else 1)
        for (sx, sy) in ((w - 4, 2), (w - 3, h - 3), (3, 2)):
            if 0 < sx < w - 1 and 0 < sy < h - 1:
                img[sy, sx] = T("candle", 0)
        return img
    return f


RING = art([
    ".aaa.",
    "a...a",
    "a...a",
    ".aaa.",
], {"a": ("coal", 1)})

TENDRIL = art([
    "..aa..",
    ".a..a.",
    ".a.aa.",
    "..a...",
    "...a..",
    "....a.",
], {"a": ("moss", 2)})


# ------------------------------------------------------------------ building blocks
def round_pumpkin(m, lo, hi, carved_face=True, lit=False, emit=15, stem=True):
    """Pumpkin rounded on every axis: 3 tiers of crossed lobes, glowing core, curled stem.
    10-12 elements."""
    (x0, y0, z0), (x1, y1, z1) = lo, hi
    W, H, D = x1 - x0, y1 - y0, z1 - z0
    ix, iz, iy = W * 0.13, D * 0.13, H * 0.14
    if carved_face:
        m.box([x0 + 2 * ix, y0 + 1.6 * iy, z0 + 1.2 * iz], [x1 - 2 * ix, y1 - 1.6 * iy, z1 - 1.5 * iz],
              glow_core(lit), emit=emit if lit else 0)
    face_p = carved() if carved_face else pumpkin_skin(stem_top=False)
    m.box([x0 + ix, y0 + 0.9 * iy, z0], [x1 - ix, y1 - 0.9 * iy, z1], face_p, res=2)          # front/back lobe
    m.box([x0, y0 + 1.1 * iy, z0 + iz], [x1, y1 - 1.1 * iy, z1 - iz], pumpkin_skin(stem_top=False),
          faces=("east", "west", "south", "up", "down") if carved_face else None, res=2)          # side lobe
    m.box([x0 + 1.6 * ix, y0, z0 + 1.1 * iz], [x1 - 1.6 * ix, y0 + 1.6 * iy, z1 - 1.1 * iz], pumpkin_skin(), res=2)
    m.box([x0 + 1.1 * ix, y0 + 0.15, z0 + 1.6 * iz], [x1 - 1.1 * ix, y0 + 1.4 * iy, z1 - 1.6 * iz], pumpkin_skin(), res=2)
    m.box([x0 + 1.6 * ix, y1 - 1.6 * iy, z0 + 1.1 * iz], [x1 - 1.6 * ix, y1, z1 - 1.1 * iz], pumpkin_skin(), res=2)
    m.box([x0 + 1.1 * ix, y1 - 1.4 * iy, z0 + 1.6 * iz], [x1 - 1.1 * ix, y1 - 0.15, z1 - 1.6 * iz], pumpkin_skin(), res=2)
    if stem:
        cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
        sw = max(1.0, W * 0.12)
        m.box([cx - sw / 2, y1 - 0.5, cz - sw / 2], [cx + sw / 2, y1 + 1.5, cz + sw / 2], bark("moss"))
        m.box([cx - sw / 2, y1 + 1.2, cz - sw / 2], [cx + sw / 2, y1 + 2.8, cz + sw / 2], bark("moss"),
              rot=("z", -22.5, [cx, y1 + 1.2, cz]))
        m.card([cx, y1 - 0.3, cz - 0.2], [cx + W * 0.32, y1 + W * 0.22, cz - 0.2], LEAF, rot=("y", 22.5, [cx, y1, cz]))
        m.card([cx - W * 0.35, y1 - 0.2, cz + 0.6], [cx, y1 + W * 0.3, cz + 0.6], TENDRIL, rot=("y", -22.5, [cx, y1, cz]))


# ------------------------------------------------------------------ pieces
def jack_o_lantern(lit=False):
    m = Model("jack_o_lantern_lit" if lit else "jack_o_lantern")
    round_pumpkin(m, [2, 0, 3], [14, 10, 13], lit=lit)
    return m


def cauldron(lit=False):
    m = Model("cauldron_lit" if lit else "cauldron")
    IR = cast_iron()
    for ang, (x, z) in ((0, (7.25, 1.5)), (120, (2.0, 11.0)), (240, (12.5, 11.0))):
        m.box([x, 0, z], [x + 1.5, 1, z + 1.5], solid("coal", 3))                     # feet
        m.box([x, 0.5, z], [x + 1.5, 3.5, z + 1.5], solid("coal", 2), rot=("x", 22.5 if z < 5 else -22.5, [x + 0.75, 3.5, z + 0.75]))
    m.box([4.5, 2, 3.5], [11.5, 3.6, 12.5], IR)                                       # base, crossed
    m.box([3.5, 2.2, 4.5], [12.5, 3.4, 11.5], IR)
    m.box([1.5, 3.4, 3.2], [14.5, 8.6, 12.8], IR)                                     # belly, crossed
    m.box([3.2, 3.6, 1.5], [12.8, 8.4, 14.5], IR)
    m.box([2.5, 8.5, 3.5], [13.5, 10, 12.5], IR)                                      # shoulder
    m.box([3.5, 8.4, 2.5], [12.5, 10.1, 13.5], IR)
    rim = solid("coal", 1)
    m.box([1.75, 10, 1.75], [14.25, 11.5, 3.25], rim)                                 # flared rim
    m.box([1.75, 10, 12.75], [14.25, 11.5, 14.25], rim)
    m.box([1.75, 10, 3.25], [3.25, 11.5, 12.75], rim)
    m.box([12.75, 10, 3.25], [14.25, 11.5, 12.75], rim)
    m.card([0.4, 6, 6], [0.4, 9, 10], RING)                                           # ring handles
    m.card([15.6, 6, 6], [15.6, 9, 10], RING)
    m.box([3.25, 10.2, 3.25], [12.75, 10.7, 12.75], brew(), emit=11, faces=("up",))     # brew surface
    m.box([5, 10.4, 6], [6.6, 11.6, 7.6], solid("brew", 1), emit=11)                  # bubbles
    m.box([9.2, 10.4, 9.6], [10.4, 11.2, 10.8], solid("brew", 0), emit=11)
    m.box([7.6, 10.4, 4.6], [8.4, 10.9, 5.4], solid("brew", 0), emit=11)
    bub = art([".a..", "a.a.", ".a.a", "..a.", ".a..", "a..."], {"a": ("brew", 0, 170)})
    m.card([5, 11, 8], [10, 17, 8], bub, rot=("y", 45, [8, 11, 8]))
    m.card([6, 11.5, 8], [11, 16.5, 8], bub, rot=("y", -45, [8, 11, 8]))
    m.box([10.5, 10, 9.5], [11.5, 17, 10.5], wood("oak"), rot=("x", -22.5, [11, 10, 10]))  # ladle handle
    m.box([9.5, 16.5, 4.8], [12.5, 17.5, 5.8], wood("oak"), rot=("x", -22.5, [11, 10, 10]))
    m.box([4.5, 0, 7.25], [11.5, 1.4, 8.75], wood("spruce"), rot=("y", 22.5, [8, 0, 8]))  # kindling
    m.box([7.25, 0, 4.5], [8.75, 1.4, 11.5], wood("spruce"), rot=("y", -45, [8, 0, 8]))
    if lit:
        m.card([5, 0.8, 8], [11, 3.4, 8], candle_flame(), rot=("y", 45, [8, 0, 8]), emit=15)
        m.card([5, 0.8, 8], [11, 3.4, 8], candle_flame(), rot=("y", -45, [8, 0, 8]), emit=15)
    return m


def scarecrow():
    m = Model("scarecrow", floor=-16)
    m.box([7, -16, 7], [9, 21, 9], bark("spruce"))                                       # post
    m.box([-6, 10, 7.2], [22, 11.8, 8.8], bark("spruce"))                                # crossbar
    shirt = plaid("plum", "ebony")
    m.box([3.5, -1, 5.2], [12.5, 11, 10.8], shirt)                                        # torso, crossed for a rounder chest
    m.box([4.2, -0.5, 4.6], [11.8, 10.5, 11.4], shirt)
    m.card([5, 2, 4.5], [8, 5, 4.5], patch_art())                                         # stitched patches
    m.card([9, 6, 4.5], [11.5, 8.5, 4.5], patch_art())
    m.box([-4, 8.5, 6], [3.5, 12.5, 10], shirt, rot=("z", 22.5, [3.5, 12.5, 8]))          # droopy sleeves
    m.box([12.5, 8.5, 6], [20, 12.5, 10], shirt, rot=("z", -22.5, [12.5, 12.5, 8]))
    m.box([-4.4, 8.3, 5.8], [-3.2, 12.7, 10.2], solid("rust", 2, bevel=False), rot=("z", 22.5, [3.5, 12.5, 8]))  # cuff ties
    m.box([19.2, 8.3, 5.8], [20.4, 12.7, 10.2], solid("rust", 2, bevel=False), rot=("z", -22.5, [12.5, 12.5, 8]))
    m.card([-7, 3, 8], [-3, 8, 8], STRAW, rot=("z", 22.5, [-5, 8, 8]))                   # straw spilling out
    m.card([19, 3, 8], [23, 8, 8], STRAW, rot=("z", -22.5, [21, 8, 8]))
    m.box([4, -5, 6], [12, -1, 10], solid("denim", 2))                                    # short trousers
    m.card([4, -9, 7.9], [8, -5, 7.9], STRAW)
    m.card([8, -9, 8.1], [12, -5, 8.1], STRAW)
    m.box([3.3, 0.5, 4.4], [12.7, 1.5, 11.6], solid("rust", 2, bevel=False))              # rope belt
    m.box([4, 11.5, 4.6], [12, 19, 11.4], sack(face=True))                                # sack head, crossed
    m.box([4.6, 12, 4.2], [11.4, 18.6, 11.8], sack(), faces=("east", "west", "south", "up", "down"))
    m.box([5.5, 11, 5.5], [10.5, 12, 10.5], solid("rust", 2, bevel=False))                # gathered neck
    m.card([4, 10.5, 4.6], [12, 12.5, 4.6], STRAW)
    m.box([1, 19, 1], [15, 19.8, 15], solid("ebony", 3), rot=("x", -22.5 / 2 if False else 0, [8, 19, 8]))  # wide brim
    m.box([4.5, 19.8, 4.5], [11.5, 22.5, 11.5], solid("ebony", 2))
    m.box([4.4, 19.8, 4.4], [11.6, 20.8, 11.6], solid("plum", 1, bevel=False))            # band
    m.box([5.5, 22, 5.5], [10.5, 25, 10.5], solid("ebony", 2), rot=("z", 22.5, [8, 22, 8]))
    m.box([7.5, 24, 6.5], [10.5, 27, 9.5], solid("ebony", 2), rot=("z", 45, [9, 24, 8]))    # bent tip
    m.box([16, 13.5, 7], [19, 16, 9], solid("ebony", 5))                                   # crow on the arm
    m.box([18, 15.5, 7.25], [20.5, 18, 8.75], solid("ebony", 5))
    m.box([20.5, 16.2, 7.75], [22, 16.8, 8.25], solid("pumpkin", 0, bevel=False))
    m.card([13, 13, 8], [16, 16, 8], art(["aa..", ".aaa", "..aa"], {"a": ("ebony", 4)}))
    return m


def pumpkin_lamp(lit=False):
    m = Model("pumpkin_lamp_lit" if lit else "pumpkin_lamp", floor=-16)
    st = stone()
    m.box([3, -16, 3], [13, -14, 13], st)                                                 # stepped plinth
    m.box([4, -14, 4], [12, -12.5, 12], st)
    m.box([5.5, -12.5, 5.5], [10.5, -11, 10.5], cast_iron())
    IR = cast_iron()
    m.box([6.75, -11, 6.75], [9.25, 27, 9.25], IR)                                        # post
    for y in (-6, 4, 14):
        m.box([6.25, y, 6.25], [9.75, y + 1, 9.75], solid("coal", 1))                    # turned rings
    m.box([5.75, 2, 5.75], [10.25, 3.5, 10.25], solid("pumpkin", 3))                      # painted collar
    m.box([8, 25.5, 7.1], [21, 27, 8.9], IR)                                              # crook arm
    m.box([19.5, 23.5, 7.1], [21, 26, 8.9], IR)                                           # hook drop
    m.box([9, 21, 7.4], [16, 22.2, 8.6], IR, rot=("z", 45, [9, 21, 8]))                   # brace
    m.box([6.25, 27, 6.25], [9.75, 29, 9.75], IR)                                         # cap
    m.box([7, 29, 7], [9, 31, 9], solid("pumpkin", 2), rot=("y", 45, [8, 29, 8]))         # finial
    chain = art([".a.", "a.a", ".a.", ".b.", "b.b", ".b."], {"a": ("coal", 1), "b": ("coal", 3)})
    m.card([19.75, 19.5, 8], [20.75, 23.5, 8], chain, res=3)
    round_pumpkin(m, [15.5, 12, 4], [25, 19.6, 12], lit=lit, stem=False)                  # hanging jack
    m.box([19.6, 19.4, 7.4], [20.8, 20.2, 8.6], bark("moss"))
    m.card([4, 6, 6.6], [7, 14, 6.6], VINE)                                               # ivy
    m.card([9.4, 15, 9.6], [12, 23, 9.6], VINE)
    m.card([-4, 21, 8], [5, 26, 8], BAT, rot=("y", -22.5, [0, 24, 8]))
    return m


def mini_jack(m, x, y, z, s=3.0, lit=True):
    m.box([x, y, z], [x + s, y + s * 0.85, z + s], carved(), emit=10 if lit else 0, res=4)
    m.box([x + s / 2 - 0.3, y + s * 0.85, z + s / 2 - 0.3], [x + s / 2 + 0.3, y + s * 0.85 + 0.8, z + s / 2 + 0.3], solid("moss", 3, bevel=False))


def potion_stall():
    m = Model("potion_stall", floor=-16)
    m.box([-14, -16, 2.5], [30, -2, 14], wood("ebony", border=True))                     # counter
    m.box([-14.5, -16, 2], [30.5, -14.5, 14.5], solid("ebony", 4))                        # kick plate
    m.box([-14.5, -6, 2], [30.5, -5, 2.5], solid("gold", 2, bevel=False))                 # brass trim
    m.box([-16, -2, 0], [32, 0, 16], wood("ebony", plank=2))                              # top
    for x in (-15, 29):
        for z in (1, 13):
            m.box([x, 0, z], [x + 2, 25, z + 2], bark("ebony"))
    roof = {"up": stripes("plum", "bone", 3), "down": stripes("plum", "bone", 3),
            "north": solid("plum", 3), "south": solid("plum", 3)}
    m.box([-16, 26, -6], [32, 27.5, 8], solid("plum", 3), over=roof, rot=("x", -22.5, [8, 28, 8]))
    m.box([-16, 26, 8], [32, 27.5, 22], solid("plum", 3), over=roof, rot=("x", 22.5, [8, 28, 8]))
    m.box([-16, 27.5, 7.25], [32, 29.5, 8.75], bark("ebony"))                             # ridge
    m.box([6.5, 29, 6.5], [9.5, 31.5, 9.5], solid("plum", 2), rot=("z", 22.5, [8, 29, 8]))  # crooked finial
    m.card([-16, 19, -5.4], [32, 22.5, -5.4], scallop("plum", "pumpkin"))                 # scalloped hem
    m.box([-1, 13.5, -1.75], [17, 19.5, -0.75], moon_board())                             # shop sign
    m.card([2, 19.5, -1.25], [3, 22, -1.25], art(["a", "a"], {"a": ("coal", 2)}))
    m.card([13, 19.5, -1.25], [14, 22, -1.25], art(["a", "a"], {"a": ("coal", 2)}))
    for x, y in ((-12, 15), (22, 15)):                                                    # hanging mini jacks
        m.card([x + 1, y + 2.5, -3], [x + 2, 21, -3], art(["a", "a"], {"a": ("coal", 2)}))
        mini_jack(m, x, y - 0.5, -4.5, 3)
    m.card([-6, 10, -3], [3, 15, -3], BAT)
    # goods
    m.box([-11, 0, 4], [-6, 3.5, 9], cast_iron())                                          # little cauldron
    m.box([-10.5, 3.2, 4.5], [-6.5, 3.6, 8.5], brew(), emit=10, faces=("up",))
    glass = {"up": solid("rust", 2)}
    for (x, z, c, hgt) in ((-3, 5, "brew", 5), (-0.5, 7.5, "plum", 4), (2, 5, "pumpkin", 6)):
        m.box([x, 0, z], [x + 2, hgt - 1.5, z + 2], solid(c, 1), emit=6)                 # potions
        m.box([x + 0.5, hgt - 1.5, z + 0.5], [x + 1.5, hgt, z + 1.5], solid("bone", 2), over=glass)
    m.box([8, 0, 6], [14, 1.5, 10], solid("plum", 3), over={"up": solid("bone", 0)})       # spellbook
    m.box([8.2, 1.5, 6.2], [13.8, 2.6, 9.8], solid("ebony", 3), over={"up": solid("bone", 1)})
    mini_jack(m, 22, 0, 6, 5)
    m.box([17, 0, 9], [18.5, 4, 10.5], wax())                                             # candle
    m.card([17, 4, 9.75], [18.5, 6, 9.75], candle_flame(), emit=15)
    m.card([25, 8, 2], [31, 14, 2], COBWEB)
    return m


def all_models():
    return [jack_o_lantern(False), jack_o_lantern(True), cauldron(False), cauldron(True),
            scarecrow(), pumpkin_lamp(False), pumpkin_lamp(True), potion_stall()]
