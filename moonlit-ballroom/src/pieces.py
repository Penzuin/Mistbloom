"""Moonlit Ballroom - starter set (Mistbloom Studios).

Spooky-cute: friendly translucent ghosts with calm happy faces, ebony + gilt ballroom furniture,
cold moonglass candlelight. Front of every piece faces NORTH (-z). Wall pieces put their back on z=16.
Ghosts are flip-book animated textures (8 frames, 1.2 s loop) so everything runs on plain Nexo.
"""
import math
import numpy as np
from engine import (Model, T, _blank, solid, wood, panel, candle_p, moonflame, pane_arch, art, sprite, SIDES)
import sprites as S

EBONY = wood("ebony", plank=2)
BSILVER = solid("blacksilver", 2)

# ------------------------------------------------------------------ painters
def gilt():
    """Gilded frame moulding: bead-and-reel rhythm, light top edge, dark inner lip."""
    def f(w, h, face, key):
        img = _blank(w, h)
        horiz = w >= h
        L, Tn = (w, h) if horiz else (h, w)
        for t in range(Tn):
            for l in range(L):
                tone = 1.5
                if t == 0:
                    tone = 0.5
                elif t == Tn - 1:
                    tone = 3
                elif Tn > 3 and t == Tn // 2:
                    tone = 1 if (l % 3) else 2.5          # bead row
                x, y = (l, t) if horiz else (t, l)
                img[y, x] = T("gold", tone)
        return img
    return f

def parquet():
    """Ballroom floor seen from above: rosewood/ebony herringbone, a gilt ring and a pale moon rune
    circle round the edge; sides are a dark ebony skirting."""
    def f(w, h, face, key):
        img = _blank(w, h)
        if face != "up":
            img[:, :] = T("ebony", 3)
            img[0, :] = T("gold", 2)
            return img
        cx, cy = (w - 1) / 2, (h - 1) / 2
        R = min(w, h) / 2
        for y in range(h):
            for x in range(w):
                d = math.hypot(x - cx, y - cy) / R
                hb = ((x + y) // 3 + (x - y) // 3) % 2
                img[y, x] = T("rosewood", 2 if hb else 2.5)
                if 0.80 < d < 0.86:
                    img[y, x] = T("gold", 1)
                elif 0.88 < d < 0.97:
                    a = math.atan2(y - cy, x - cx)
                    if int((a + math.pi) / (2 * math.pi) * 24) % 2 == 0:
                        img[y, x] = T("moonglass", 1)
                    else:
                        img[y, x] = T("ebony", 3)
                elif d < 0.18:
                    img[y, x] = T("gold", 0 if d < 0.08 else 2)
        return img
    return f

def keys():
    """Piano keyboard from above: ivory keys with black keys in the 2-3 pattern; ebony cheeks."""
    PAT = [1, 1, 0, 1, 1, 1, 0]
    def f(w, h, face, key):
        img = _blank(w, h)
        if face != "up":
            img[:, :] = T("ebony", 2)
            return img
        img[:, :] = T("ebony", 3)
        for x in range(1, w - 1):
            img[: h - 1, x] = T("ivory", 0 if x % 2 else 1)
            if x % 2 == 0:
                img[: h - 1, x] = T("ivory", 2)
        for x in range(1, w - 1, 2):
            if PAT[(x // 2) % 7] and h > 3:
                img[h // 2:h - 1, x] = T("soot", 3)
        return img
    return f

def piano_body():
    """Upright piano case: ebony with two gilt-inlaid panels and a little crescent in the top one."""
    g = panel("ebony", front=("north",), rows=2, inlay="gold")
    def f(w, h, face, key):
        img = g(w, h, face, key)
        if face == "north" and w > 20 and h > 12:
            cx, cy, r = (w - 1) / 2, h * 0.27, min(w, h) * 0.13
            for y in range(h):
                for x in range(w):
                    d1 = math.hypot(x - cx, y - cy); d2 = math.hypot(x - cx - r * 0.45, y - cy + r * 0.25)
                    if d1 <= r and d2 > r * 0.8:
                        img[y, x] = T("gold", 1)
        return img
    return f

def velvet():
    def f(w, h, face, key):
        img = _blank(w, h)
        for y in range(h):
            for x in range(w):
                tone = 1.5 + (0.5 if (y // 2) % 2 else 0)
                if min(x, y, w - 1 - x, h - 1 - y) == 0:
                    tone += 0.5
                img[y, x] = T("velvet", tone)
        if face == "up" and w > 4 and h > 4:
            img[h // 2, w // 2] = T("gold", 1)
        return img
    return f

def ghost_body(face_sprite=None, alpha=175, rim=True):
    """Translucent moonlit body for 3D ghosts. Optional animated face sprite on the north face."""
    def base(w, h, face):
        img = _blank(w, h)
        for y in range(h):
            for x in range(w):
                t = y / max(1, h - 1)
                c = np.array(S.BODY) * (1 - 0.15 * t) + np.array(S.SHADE) * 0.15 * t
                a = alpha
                if rim and (min(x, w - 1 - x) == 0 or (face == "up" and min(y, h - 1 - y) == 0)):
                    c, a = np.array(S.RIM), 215
                img[y, x] = (*c.astype(int), a)
        if face == "down":
            img[:, :, :3] = (img[:, :, :3] * 0.8).astype(np.uint8)
        return img
    def f(w, h, face, key):
        img = base(w, h, face)
        if face == "north" and face_sprite is not None:
            fs = face_sprite(w, h, face, key)
            m = fs[..., 3] > 40
            img[m] = fs[m]
        return img
    if face_sprite is not None:
        f.animated = True
    return f

SHEET = art([
    "aaaaaaaaaa",
    "abbbbbbbba",
    "ab.b.bb.ba",
    "abbbbbbbba",
    "abb.b.b.ba",
    "abbbbbbbba",
    "aaaaaaaaaa",
], {"a": ("parchment", 1), "b": ("parchment", 3), ".": ("soot", 1)})

CREST = art([
    "....aa....",
    "...abba...",
    ".a.abba.a.",
    "abbbbbbbba",
    ".aaaaaaaa.",
], {"a": ("gold", 2), "b": ("gold", 0)})

RING = art([
    ".aaa.",
    "a...a",
    "a...a",
    ".aaa.",
], {"a": ("blacksilver", 1)})


# ------------------------------------------------------------------ pieces
def waltzing_ghosts():
    m = Model("waltzing_ghosts")
    floor = parquet()
    m.box([-3, 0, 0], [19, 1, 16], floor)                                       # round-ish dance floor
    m.box([0, 0, -3], [16, 0.9, 19], floor)                                     # (plus-section, no coplanar faces)
    m.card([-2, 1.15, -2], [18, 1.15, 18], sprite(S.wisp_ring), emit=10, res=2) # sparkle circle
    m.card([-3, 0.6, 8], [19, 28.6, 8], sprite(S.waltz), emit=12, res=2.25)     # the dancing couple
    return m


def ghost_piano():
    m = Model("ghost_piano")
    m.box([1, 0, 6], [31, 21, 15], piano_body())                               # case
    m.box([0.5, 21, 5.5], [31.5, 22.5, 15.5], wood("ebony", plank=2, base=1))   # lid
    m.box([1, 10, 1.5], [31, 12, 6], wood("ebony"), over={"up": keys()}, res=1) # keybed + keys
    m.box([2, 0, 2], [4, 10, 4], EBONY)                                         # front legs
    m.box([28, 0, 2], [30, 10, 4], EBONY)
    m.box([13, 0.5, 5], [19, 1.5, 6], solid("gold", 1), res=2)                   # pedals
    m.card([9, 13, 5.9], [23, 19, 5.9], SHEET, rot=("x", -22.5, [16, 13, 5.9]))  # sheet music
    m.box([8, 0, -7], [24, 5, -1], panel("ebony", front=("north", "east", "west")))   # bench
    m.box([7.5, 5, -7.5], [24.5, 6.5, -0.5], velvet())                          # bench cushion
    m.card([7, 6, -4], [25, 24, -4], sprite(S.pianist), emit=12, res=2)          # the pianist
    m.card([20, 22.5, 11], [28, 32, 11], sprite(S.notes), emit=12, res=2.5)      # drifting notes
    m.box([3, 22.5, 9], [4.5, 25, 10.5], candle_p(), res=2)                      # little candle
    m.crossed(3.75, 25, 9.75, 2, 3, moonflame(), emit=15, res=2)
    return m


def floating_candelabra(lit=False):
    m = Model("floating_candelabra_lit" if lit else "floating_candelabra")
    m.crossed(8, 0.5, 8, 6, 6, sprite(S.wisp_tail), emit=10, res=3)              # a curl of ghost mist holds it up
    m.box([7.25, 6, 7.25], [8.75, 14, 8.75], BSILVER, res=2)                     # stem
    m.box([6, 14, 6], [10, 15, 10], solid("gold", 1))                            # drip cup
    m.box([1.5, 15, 7.25], [14.5, 16, 8.75], BSILVER, res=2)                     # arm bar
    m.box([1.5, 16, 6.5], [4.5, 17, 9.5], solid("gold", 1), res=2)               # side cups
    m.box([11.5, 16, 6.5], [14.5, 17, 9.5], solid("gold", 1), res=2)
    m.box([2.25, 17, 7.25], [3.75, 21, 8.75], candle_p(), res=2)
    m.box([12.25, 17, 7.25], [13.75, 21, 8.75], candle_p(), res=2)
    m.box([7.25, 16, 7.25], [8.75, 23, 8.75], candle_p(), res=2)                 # tall centre candle
    if lit:                                                                      # one flame card each, turned to face the corner
        for x, y in ((3, 21), (13, 21), (8, 23)):
            m.card([x - 1, y, 8], [x + 1, y + 3, 8], moonflame(), rot=("y", 45, [x, y, 8]), emit=15, res=2)
    m.card([1, 0.6, 1], [15, 0.6, 15], sprite(S.wisp_ring), emit=10, res=2)      # spectral ring below
    return m


def ghost_lantern(lit=False):
    m = Model("ghost_lantern_lit" if lit else "ghost_lantern")
    m.box([4.5, 0, 4.5], [11.5, 1, 11.5], BSILVER, res=2)
    m.card([5.25, 1, 8], [10.75, 8.4, 8], sprite(S.lantern_ghost), emit=12 if lit else 6, res=4)
    m.box([4.5, 1, 4.5], [11.5, 10, 11.5], pane_arch(lit), res=2, faces=SIDES + ("up",))
    top = m.lantern_roof(8, 10, 8, 7)
    m.box([7.5, top - 0.5, 7.5], [8.5, top + 1.5, 8.5], solid("blacksilver", 1), res=2)
    m.card([6.75, top + 1, 8], [9.25, top + 3, 8], RING, res=2)
    return m


def ghost_portrait():
    m = Model("ghost_portrait")
    m.box([2, 4, 15], [14, 20, 16], EBONY)                                       # backing board
    m.card([2, 4, 14.6], [14, 20, 14.6], sprite(S.portrait, mirror_back=False), res=3.5)   # the painting
    G = gilt()
    m.box([0, 2, 14], [2, 22, 16], G)                                            # frame
    m.box([14, 2, 14], [16, 22, 16], G)
    m.box([2, 20, 14], [14, 22, 16], G)
    m.box([2, 2, 14], [14, 4, 16], G)
    m.card([4, 22, 15], [12, 26, 15], CREST, res=2)                              # crest
    m.box([5.5, 2.4, 13.6], [10.5, 3.6, 14], solid("gold", 0), res=2)             # name plate
    return m


HEM = art([
    "aaaaaaaaaaaaaaaa",
    "aaaaaaaaaaaaaaaa",
    "aaaaaaaaaaaaaaaa",
    ".aa..aaa..aaa.aa",
    "..a...a....a..a.",
], {"a": ("ivory", 0, 228)})


def wisp():
    """A little floating ghost pet: rounded body from three crossed boxes, glowing,
    a calm blinking face and a scalloped hem all round."""
    m = Model("wisp")
    face = sprite(S.wisp_face, mirror_back=False)
    m.box([4, 6, 3], [12, 13, 13], ghost_body(face, 228, False), res=3, emit=10)             # deep box (face on the front)
    m.box([3, 6, 4], [13, 13, 12], ghost_body(None, 228, False), res=2, emit=10)                 # wide box
    m.box([4, 4.5, 4], [12, 15, 12], ghost_body(None, 228, False), res=2, emit=10)               # tall box: dome + belly
    m.card([3.5, 1.5, 3.4], [12.5, 6, 3.4], HEM, res=2, emit=10)                 # scalloped hem, four sides
    m.card([3.5, 1.5, 12.6], [12.5, 6, 12.6], HEM, res=2, emit=10)
    m.card([3.4, 1.5, 3.5], [3.4, 6, 12.5], HEM, res=2, emit=10)
    m.card([12.6, 1.5, 3.5], [12.6, 6, 12.5], HEM, res=2, emit=10)
    m.card([9.5, 14.2, 3.9], [12.5, 17.2, 3.9], art([
        "aa.aa", "abbba", ".aba.", "abbba", "aa.aa"], {"a": ("violet", 1), "b": ("violet", 3)}), res=2)  # little bow
    return m


def all_models():
    return [waltzing_ghosts(), ghost_piano(), floating_candelabra(False), floating_candelabra(True),
            ghost_lantern(False), ghost_lantern(True), ghost_portrait(), wisp()]
