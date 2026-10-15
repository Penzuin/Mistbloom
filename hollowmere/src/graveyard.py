"""Hollowmere graveyard batch (cute, not gory). Front faces NORTH (-z). Max 14 elements."""
import random
import engine
from engine import Model, wood, solid, T, _blank, fr, animated, SIDES, art
from hero3 import bark, iron, candle_flame, wax, pump_skin
from spooky import stone, VINE
from harvest import pumpkin

engine.RAMPS.update({k: engine._ramp7(v) for k, v in {
    "ghost": ["#ffffff", "#eef6ff", "#cfdcf5", "#9fb0d6"],
    "shroom": ["#c8fff3", "#7ff0d6", "#3fc2b0", "#257f7a"],
    "lilac": ["#f1d9ff", "#d0a6f2", "#a575d6", "#6f4aa0"],
}.items()})


def headstone(text=True, cross=False):
    base = stone("slate", moss=False)
    RIP = ["##..###.###",
           "#.#..#..#.#",
           "##...#..###",
           "#.#..#..#..",
           "#.#.###.#.."]
    def f(w, h, fc, key):
        img = base(w, h, fc, key)
        if fc == "north" and text and w >= 12 and h >= 8:
            x0, y0 = (w - 11) // 2, 2
            for gy, row in enumerate(RIP):
                for gx, ch in enumerate(row):
                    if ch == "#":
                        img[y0 + gy, x0 + gx] = T("slate", 5)          # engraved letters
            for x in range(x0 + 2, x0 + 9):
                img[y0 + 7, x] = T("slate", 4)                          # line under
        return img
    return f


def ghost(lit=True):
    """Little round ghost with a sleepy smile; north face shows the face."""
    def f(w, h, fc, key):
        img = _blank(w, h)
        img[:, :] = T("ghost", 1)
        if fc in SIDES:
            img[-1, ::2] = T("ghost", 2)                                 # wavy hem
            if fc == "north" and w >= 8 and h >= 10:
                ey = h // 3
                img[ey:ey + 2, w // 4:w // 4 + 2] = T("ebony", 5)
                img[ey:ey + 2, w - 2 - w // 4:w - w // 4] = T("ebony", 5)
                img[ey + 3, w // 2 - 1:w // 2 + 1] = T("ebony", 4)          # tiny "o" mouth
                img[ey + 2, 1:3] = img[ey + 2, w - 3:w - 1] = T("blush", 1)
        return img
    return f


def mesh_glass(lit=True):
    def f(w, h, fc, key):
        img = _blank(w, h)
        if fc in ("up", "down"):
            img[:, :] = T("iron", 3)
            return img
        img[:, :] = T("shroom", 1, 45) if lit else T("frost", 2, 60)
        img[0, :] = img[-1, :] = T("iron", 3)
        img[:, 0] = img[:, -1] = T("iron", 3)
        return img
    return f


def cap(ramp="shroom"):
    def f(w, h, fc, key):
        img = _blank(w, h)
        img[:, :] = T(ramp, 1)
        if fc == "up":
            for (x, y) in ((1, 1), (w - 2, h // 2), (w // 2, h - 2)):
                if 0 <= x < w and 0 <= y < h:
                    img[y, x] = T(ramp, 0)                               # glowing spots
        if fc == "down":
            img[:, :] = T(ramp, 3)
            img[::2, :] = T(ramp, 2)                                     # gills
        return img
    return f


def coffin_wood():
    base = wood("ebony", plank=2)
    def f(w, h, fc, key):
        img = base(w, h, fc, key)
        if fc == "up" and w >= 10 and h >= 6:
            cx, cy = w // 2, h // 2
            for x in range(cx - 3, cx + 4):
                img[cy, x] = T("plum", 4)                                # little cross inlay, dark and subtle
            for y in range(cy - 2, cy + 3):
                img[y, cx - 1] = T("plum", 4)
            img[0, :] = img[-1, :] = img[:, 0] = img[:, -1] = T("ebony", 1)
        return img
    return f


# ------------------------------------------------------------------ pieces
def tombstone():
    m = Model("tombstone", floor=0)
    m.box([1.5, 0, 6], [14.5, 2, 12], stone("slate", moss=True))                  # mossy plinth
    m.box([3, 2, 7.5], [13, 13, 10.5], headstone(), res=2)                        # engraved slab
    m.box([4, 13, 7.5], [12, 15, 10.5], stone("slate", moss=False))               # rounded top, stepped
    m.box([5.5, 15, 7.5], [10.5, 16, 10.5], stone("slate", moss=False))
    m.card([10, 2, 7.0], [12.8, 8, 7.0], VINE)                                    # ivy creeping up
    m.box([1.5, 2, 3], [5.5, 5, 7], pump_skin())                             # pumpkin offering
    m.box([3.1, 5, 4.6], [3.9, 6, 5.4], bark("stem"))
    m.box([11, 2, 3.5], [12.5, 5, 5], wax())
    m.card([11, 5, 4.25], [12.5, 7, 4.25], candle_flame(), emit=15)
    return m


def tombstone_cross():
    m = Model("tombstone_cross", floor=0)
    m.box([3, 0, 5.5], [13, 1.5, 12.5], stone("slate", moss=True))                # stepped base
    m.box([4.5, 1.5, 6.5], [11.5, 3.5, 11.5], stone("slate", moss=False))
    m.box([6.5, 3.5, 7.5], [9.5, 18, 10.5], stone("slate", moss=False))           # upright
    m.box([2.5, 11, 7.85], [13.5, 14, 10.15], stone("slate", moss=False))         # arms, centred on the upright (a touch thinner)
    m.box([5.5, 10, 7.1], [10.5, 15, 7.5], stone("slate", moss=False))            # centre boss, on the front of the crossing
    m.card([1, 1.5, 5.4], [6, 6, 5.4], art(["..a.b..", ".aaabb.", "..ab...", "..c....", ".cc....", "..c...."],
                                          {"a": ("lilac", 1), "b": ("blush", 1), "c": ("moss", 2)}))   # flowers
    m.card([6.6, 3.5, 7.1], [9.4, 9.8, 7.1], VINE)                                 # ivy climbing the front of the upright
    return m


def iron_fence():
    m = Model("iron_fence")
    for x in (0, 14):
        m.box([x, 0, 7], [x + 2, 16, 9], iron())                                  # posts
        m.box([x + 0.4, 16, 7.4], [x + 1.6, 18, 8.6], solid("iron", 1), rot=("y", 45, [x + 1, 16, 8]))   # spear tips
    m.box([2, 3, 7.25], [14, 4, 8.75], iron())                                      # rails
    m.box([2, 12, 7.25], [14, 13, 8.75], iron())
    for x in (3.5, 6.5, 9.5, 12.5):
        m.box([x - 0.4, 0, 7.6], [x + 0.4, 15, 8.4], iron())                      # bars
    m.card([2, 5, 6.8], [6, 11, 6.8], VINE)
    return m


def coffin():
    m = Model("coffin")
    m.box([-6, 0, 4], [0, 5, 12], coffin_wood())                                  # head end
    m.box([0, 0, 2.5], [6, 5, 13.5], coffin_wood())                               # shoulders, widest
    m.box([6, 0, 3.5], [22, 5, 12.5], coffin_wood())                              # long taper to the foot
    m.box([-6.4, 5, 3.6], [0, 6.4, 12.4], coffin_wood())                          # lid follows the shape
    m.box([0, 5, 2.1], [6, 6.4, 13.9], coffin_wood())
    m.box([6, 5, 3.1], [22.4, 6.4, 12.9], coffin_wood())
    m.box([1, 2, 2.1], [5, 3, 2.5], solid("gold", 2, bevel=False))               # brass handles
    m.box([12, 2, 3.1], [16, 3, 3.5], solid("gold", 2, bevel=False))
    m.box([16, 6.4, 6], [20, 9.4, 10], pump_skin())                          # pumpkin resting on the lid
    m.box([17.6, 9.4, 7.6], [18.4, 10.4, 8.4], bark("stem"))
    m.box([1.2, 6.4, 6.8], [3.8, 7.0, 9.2], art(["cbcb", "bcbc", "cbcb"], {"b": ("plum", 4), "c": ("moss", 3)}), res=1)  # small dried posy
    return m


def ghost_lantern(lit=False):
    """Floor lantern: sits flat on the ground on a wide iron foot (no hanging drop finial)."""
    m = Model("ghost_lantern_lit" if lit else "ghost_lantern")
    d = -1.5                                                                      # whole lantern lowered onto its foot
    m.card([7.5, 11 , 8], [8.5, 14.5, 8], art([".a.", "a.a", ".a.", ".b.", "b.b", ".b."],
                                            {"a": ("iron", 1), "b": ("iron", 3)}), res=3)   # carry ring
    m.box([5, 11 + d, 5], [11, 12.5 + d, 11], iron())                             # cap
    m.box([6, 12.5 + d, 6], [10, 13 + d, 10], iron())
    m.box([6, 4.5 + d, 6.2], [10, 9.5 + d, 9.8], ghost(lit), emit=15 if lit else 0, res=3)   # little ghost inside
    m.box([6.8, 3.2 + d, 7], [9.2, 4.5 + d, 9], ghost(lit), emit=15 if lit else 0, res=3)     # wisp tail
    m.box([5.5, 3 + d, 5.5], [10.5, 11 + d, 10.5], mesh_glass(lit))               # glass cage
    m.box([5, 2 + d, 5], [11, 3 + d, 11], iron())                                 # base
    m.box([4.5, 0, 4.5], [11.5, 0.5, 11.5], iron())                               # wide foot, flat on the ground
    return m


def mushroom_ring():
    m = Model("mushroom_ring")
    for (x, z, s, hgt, r) in ((2, 3, 3, 4, "shroom"), (10, 2, 2.4, 3, "lilac"), (12, 9, 3.2, 5, "shroom"),
                               (5, 11, 2.4, 3.5, "lilac"), (7.5, 6.5, 1.8, 2.5, "shroom"), (1.5, 9, 1.8, 2, "shroom")):
        m.box([x + s * .35, 0, z + s * .35], [x + s * .65, hgt, z + s * .65], solid("bone", 1))   # stems
        m.box([x, hgt, z], [x + s, hgt + s * .45, z + s], cap(r), emit=11)                       # glowing caps
    return m


def all_models():
    return [tombstone(), tombstone_cross(), iron_fence(), coffin(), ghost_lantern(False), ghost_lantern(True),
            mushroom_ring()]
