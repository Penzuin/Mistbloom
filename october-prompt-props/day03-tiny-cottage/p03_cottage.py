"""Day 3 Miniature - Tiny Cottage (v2 redesign, Oct 21 2026).
Storybook cottage: cream plaster between dark timber corner posts, thick thatched roof with a straw ridge
roll and overhangs, stone chimney, teal round-top door under a little hood, flower boxes, a stepped bush,
on a grass block with a stone path."""
import math
import numpy as np
from engine import Model, SIDES, _blank
from px import PAL, hx, material, card_art, _uv, C, despeckle

PAL["grass"] = [hx(c) for c in ("#b4e070", "#8cc850", "#6aa63c", "#4e8430", "#365e24")]
PAL["soil"] = [hx(c) for c in ("#b48a62", "#966c48", "#785236", "#5a3c28", "#3e281a")]
PAL["plaster"] = [hx(c) for c in ("#fffaf0", "#f6ead2", "#e4d2b0", "#c8b08a", "#9e8666")]
PAL["timber"] = [hx(c) for c in ("#a87a50", "#8a603e", "#6e4a30", "#543624", "#3a2418")]
PAL["thatch"] = [hx(c) for c in ("#ffe8a0", "#f0cc6c", "#d6a84a", "#ae8236", "#7c5a26")]
PAL["door"] = [hx(c) for c in ("#9ee4dc", "#5cc2bc", "#38a09e", "#287a7c", "#1a5458")]
PAL["window"] = [hx(c) for c in ("#fff8c8", "#ffe07a", "#f4b444", "#c8802a", "#8c521c")]

# walls and roof geometry
WX0, WX1, WZ0, WZ1, WY0, WY1 = 2, 14, 5, 11, 3, 10
ZC = (WZ0 + WZ1) / 2
HALF = (WZ1 - WZ0) / 2
PLATE = WY1 + 1                      # top of the timber plate
RIDGE = PLATE + HALF


def plain(mat, base=2, edge=True, detail=None):
    return material(mat, "plain", base=base, edge=edge, detail=detail)


# ---------------------------------------------------------------- base
def grass_base():
    dirt = plain("soil")
    path = [(7, 0), (8, 0), (8, 1), (9, 1), (7, 2), (8, 2)]          # stepping stones in front of the step
    tufts = [(2, 6), (12, 7), (14, 3), (1, 13), (5, 14), (13, 14), (10, 2)]
    blooms = {(3, 1): "pink", (11, 0): "yellow", (14, 10): "white", (1, 9): "yellow"}

    def f(w, h, face, key):
        if face == "up":
            t = np.full((h, w), 1, int)
            u, v, _ = _uv()
            img = None
            for (a, b) in tufts:                                       # 2 px grass tufts, darker
                t[(u == a) & ((v == b) | (v == b + 1))] = 2
            t[0, :] = 0; t[:, 0] = 0; t[:, -1] = 2; t[-1, :] = 2      # light NW rim, dark SE rim
            img = np.zeros((h, w, 4), np.uint8)
            for k in range(5):
                img[t == k] = C("grass", k)
            for (a, b) in path:
                img[(u == a) & (v == b)] = C("stone", 1 if (a + b) % 2 else 2)
            for (a, b), mat in blooms.items():
                img[(u == a) & ((v == b) | (v == b + 1))] = C(mat, 1)
            return img
        img = dirt(w, h, face, key)
        if face in SIDES:
            u, v, _ = _uv()
            img[0, :] = C("grass", 1)
            for x in range(w):                                        # grass lip hangs 1 or 2 px, in 2-3 px runs
                if (u[0, x] // 3) % 2 == 0:
                    img[1, x] = C("grass", 2)
        return img
    return f


def foundation():
    """Cut stone course: 2 px tall blocks, staggered joints, calm."""
    def d(t, u, v, face, w, h):
        t[:, :] = 2
        if face in SIDES:
            t[(u + (v % 2) * 2) % 4 == 3] = 3
    return plain("stone", detail=d)


# ---------------------------------------------------------------- house
def walls():
    plaster = plain("plaster", base=1)

    def window(img, c0, r0, shut=True):
        """2 wide x 3 tall lit glass with a timber header and a mullion row."""
        img[r0 - 1, c0:c0 + 2] = C("timber", 2)
        img[r0:r0 + 3, c0:c0 + 2] = C("window", 2)
        img[r0, c0:c0 + 2] = C("window", 1)
        img[r0 + 1, c0:c0 + 2] = C("window", 1)
        if shut:
            img[r0 - 1:r0 + 3, c0 - 1] = C("door", 2)
            img[r0 - 1:r0 + 3, c0 + 2] = C("door", 2)
            img[r0 - 1, c0 - 1] = img[r0 - 1, c0 + 2] = C("door", 1)

    def f(w, h, face, key):
        img = plaster(w, h, face, key)
        if face not in SIDES:
            return img
        if face == "north":
            window(img, 2, 2)
            window(img, 8, 2)
        elif face in ("east", "west"):
            window(img, w // 2 - 1, 2, shut=False)
        else:
            window(img, 3, 2); window(img, 7, 2)
        return img
    return f


def post():
    """Dark timber post: vertical grain, light end-grain cap on top."""
    wood = material("timber", "woodv")

    def f(w, h, face, key):
        img = wood(w, h, face, key)
        if face == "up":
            img[:] = C("timber", 1)
            img[0, :] = C("timber", 0)
        return img
    return f


def plate():
    return material("timber", "wood")


def gable():
    plaster = plain("plaster", base=1)

    def f(w, h, face, key):
        img = plaster(w, h, face, key)
        if face in ("east", "west"):
            img[:] = C("plaster", 1)
            c = w // 2
            img[:, c - 1:c + 1] = C("timber", 2)                       # king post
            img[c - 2:c, c - 1:c + 1] = C("window", 1)                 # little attic window, 2x2
            img[c - 2, c - 1:c + 1] = C("window", 0)
        return img
    return f


def thatch():
    """Thick thatch: straw courses 3 px tall, each with a lit top row, strands, and a shadow row under it.
    Edge faces show cut straw ends."""
    def f(w, h, face, key):
        img = _blank(w, h)
        if face == "up":
            for j in range(h):
                k = j % 3
                for i in range(w):
                    off = (j // 3) * 2
                    if k == 2:
                        t = 3                                      # shadow under each course
                    else:
                        t = 2 if (i + off) % 3 == 0 else 1         # 2 px straw strands
                    img[j, i] = C("thatch", t)
            img[:, 0] = C("thatch", 2)
            img[:, -1] = C("thatch", 3)
        elif face == "down":
            img[:] = C("thatch", 3)
        else:
            img[:] = C("thatch", 2)
            for i in range(w):
                if (i // 2) % 2 == 0:
                    img[-1, i] = C("thatch", 3)                       # ragged cut ends
            img[0, :] = C("thatch", 1)
        return img
    return f


def ridge_roll():
    def f(w, h, face, key):
        img = _blank(w, h)
        img[:] = C("thatch", 2)
        if face == "up":
            img[:] = C("thatch", 1)
            for i in range(w):
                if (i // 2) % 3 == 0:
                    img[:, i] = C("thatch", 2)                        # binding bands
        elif face in SIDES:
            img[0, :] = C("thatch", 1)
            img[-1, :] = C("thatch", 3)
            if face in ("north", "south"):
                for i in range(w):
                    if (i // 2) % 3 == 0:
                        img[:, i] = C("thatch", 3)
        else:
            img[:] = C("thatch", 3)
        return img
    return f


def chimney():
    def d(t, u, v, face, w, h):
        t[:, :] = 2
        if face in SIDES:
            row = v // 2
            t[v % 2 == 1] = 2
            t[(v % 2 == 1)] = 3
            t[(v % 2 == 0) & ((u + row) % 3 == 2)] = 3
    return plain("stone", detail=d)


def chimney_cap():
    def d(t, u, v, face, w, h):
        if face == "up":
            t[1:-1, 1:-1] = 4
    return plain("stone", base=1, detail=d)


def door():
    """Teal plank door with a round top (corners painted as timber frame), brass knob."""
    planks = material("door", "woodv")

    def f(w, h, face, key):
        img = planks(w, h, face, key)
        if face == "north":
            img[0, 0] = img[0, -1] = C("timber", 2)
            img[0, 1:-1] = C("door", 1)
            img[h // 2, w - 2] = C("gold", 1)                         # knob (a real feature)
            img[h // 2 + 1, w - 2] = C("gold", 3)
            img[:, w // 2 - 1] = C("door", 3)                         # centre seam
        elif face == "up":
            img[:] = C("door", 2)
        return img
    return f


def hood():
    return material("timber", "wood")


def flower_box():
    box = material("timber", "wood")

    def f(w, h, face, key):
        img = box(w, h, face, key)
        if face == "up":
            img[:] = C("grass", 3)
        return img
    return f


BLOOMS = ["py", "gg"]
BLOOMS_P = {"p": ("pink", 1), "y": ("yellow", 1), "g": ("leaf", 2)}
BLOOMS2 = ["wp", "gg"]
BLOOMS2_P = {"p": ("pink", 1), "w": ("white", 1), "g": ("leaf", 2)}


def bush():
    """Leafy clumps lit top-left; 2 px clumps, no lone dots."""
    def d(t, u, v, face, w, h):
        t[:, :] = 2
        if face in SIDES:
            t[(v % 3 == 2) & ((u // 2) % 2 == 0)] = 3
            t[(v % 3 == 0) & ((u // 2) % 2 == 1)] = 1
        elif face == "up":
            t[:, :] = 1
            t[h // 2:, w // 2:] = 2
    return material("leaf", "plain", detail=d)


IVY = [
    "LL",
    "gL",
    "gb",
    ".b",
    "Lg",
    "gb",
]
IVY_P = {"L": ("leaf", 1), "g": ("leaf", 2), "b": ("leaf", 3)}


def build():
    m = Model("tiny_cottage")
    m.box([0, 0, 0], [16, 2, 16], grass_base())                                   # grass block
    m.box([1, 2, 4], [15, 3, 12], foundation())                                  # stone course (1 px overhang)
    m.box([WX0, WY0, WZ0], [WX1, WY1, WZ1], walls())                              # plaster walls
    for x, z in ((1, 4), (13, 4), (1, 10), (13, 10)):                             # timber corner posts
        m.box([x, 3, z], [x + 2, WY1, z + 2], post())
    m.box([1, WY1, 3], [15, PLATE, 13], plate())                                  # top plate
    s = HALF * math.sqrt(2)
    m.box([WX0 + 0.5, PLATE - s / 2, ZC - s / 2], [WX1 - 0.5, PLATE + s / 2, ZC + s / 2], gable(),
          rot=("x", 45, [8, PLATE, ZC]))                                          # gable ends
    L = HALF * math.sqrt(2) + 1.5
    m.box([0, RIDGE, ZC - L], [16, RIDGE + 2, ZC + 1], thatch(), rot=("x", -45, [8, RIDGE, ZC]))   # front slope
    m.box([0, RIDGE + 0.01, ZC - 1], [16, RIDGE + 2, ZC + L], thatch(), rot=("x", 45, [8, RIDGE, ZC]))  # back
    m.box([-0.5, RIDGE + 1, ZC - 1.5], [16.5, RIDGE + 3, ZC + 1.5], ridge_roll())                 # ridge roll
    m.box([10, 9, 9], [12, RIDGE + 4, 11], chimney())                             # stone chimney
    m.box([9.5, RIDGE + 4, 8.5], [12.5, RIDGE + 5, 11.5], chimney_cap())         # cap (1 px overhang)
    m.box([6, 3, 4.5], [10, 9, 5], door(), faces=("north", "up"))  # door
    m.box([5, 9, 3], [11, 10, 5], hood())                                         # door hood
    m.box([6, 2, 1], [10, 3, 4], plain("stone", base=1))                          # front step
    m.box([10, 5, 4], [12, 6, 5], flower_box())                                   # flower boxes
    m.box([4, 5, 4], [6, 6, 5], flower_box())
    m.card([10, 6, 4.5], [12, 7, 4.5], card_art(BLOOMS, BLOOMS_P))               # blooms
    m.card([4, 6, 4.5], [6, 7, 4.5], card_art(BLOOMS2, BLOOMS2_P))
    m.box([0, 2, 1], [4, 5, 3], bush())                                           # round bush: crossed boxes
    m.box([1, 2, 0], [3, 5, 4], bush())
    m.box([1, 5, 1], [3, 6, 3], bush())
    m.card([15.1, 3, 6], [15.1, 9, 8], card_art(IVY, IVY_P))                 # ivy up the corner post
    return m
