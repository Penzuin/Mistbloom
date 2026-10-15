"""Hollowmere hero pieces, v3 (after art-director review 1). Front faces NORTH (-z)."""
import random
import numpy as np
import engine
from engine import Model, wood, solid, stripes, scallop, T, _blank, fr, animated, SIDES, art
from spooky import hay, stone, sack, candle_flame, wax, STRAW, COBWEB
from hero2 import moon_board

engine.FONT5.update({
    "H": ["1001", "1001", "1111", "1001", "1001"], "O": ["0110", "1001", "1001", "1001", "0110"],
    "L": ["100", "100", "100", "100", "111"], "W": ["10001", "10001", "10101", "11011", "10001"],
    "C": ["0111", "1000", "1000", "1000", "0111"], "N": ["1001", "1101", "1011", "1001", "1001"],
    "D": ["1110", "1001", "1001", "1001", "1110"], "S": ["0111", "1000", "0110", "0001", "1110"],
    "Y": ["10001", "01010", "00100", "00100", "00100"], "P": ["1110", "1001", "1110", "1000", "1000"],
    "I": ["111", "010", "010", "010", "111"], "G": ["0111", "1000", "1011", "1001", "0111"],
})


def shop_sign(text, ramp="ebony"):
    """Wooden sign: gold trim, lettering on the front only; the back is plain planks with the trim.
    The lettering (5 rows plus its 1-row drop shadow) sits dead centre, so the margins above and
    below match and the left/right margins match (size the box so w - text width is even)."""
    plain = engine.board(None, ramp=ramp, trim="gold")
    glyphs = [engine.FONT5[c] for c in text]
    tw = sum(len(g[0]) + 1 for g in glyphs) - 1
    def f(w, h, fc, key):
        img = plain(w, h, fc, key)
        if fc != "north" or w < 6 or h < 7:
            return img
        x, y0 = (w - tw) // 2, (h - 6) // 2
        for g in glyphs:
            for gy, row in enumerate(g):
                for gx, ch in enumerate(row):
                    if ch == "1":
                        img[y0 + gy, x + gx] = T("cream", 0)
                        if gy == 4 or g[gy + 1][gx] == "0":
                            img[y0 + gy + 1, x + gx] = T(ramp, 5)
            x += len(g[0]) + 1
        return img
    f.text_width = tw
    return f


engine.RAMPS.update({k: engine._ramp7(v) for k, v in {
    "jackglow": ["#fff6c2", "#ffd25a", "#ffab3a", "#f07a24"],
    "pump":     ["#ffcf7a", "#ffa040", "#e0702a", "#a84722"],
    "iron":     ["#a9a5c4", "#6d6988", "#45415b", "#26233a"],
    "stem":     ["#b3a05a", "#857a3c", "#5f5a2e", "#3d3a22"],
}.items()})

# ------------------------------------------------------------------ painters
FACE = [                     # 16 x 14 carving mask
    "................",
    "................",
    "..###......###..",
    "..###......###..",
    "...##......##...",
    "................",
    ".......##.......",
    "................",
    ".#............#.",
    ".###.######.###.",
    "..############..",
    "...###....###...",
    "................",
    "................",
]


def pump_skin(top_stem=False):
    """Pumpkin rind: vertical ribs with a lit crest and shadowed groove, clean flat tones."""
    def f(w, h, fc, key):
        img = _blank(w, h)
        rib = max(3, w // 4)
        for y in range(h):
            for x in range(w):
                p = x % rib
                tone = 1 if p == rib // 2 else (3 if p == 0 else 2)
                img[y, x] = T("pump", tone)
        if fc == "down":
            img[:, :] = T("pump", 4)
        if fc == "up":
            # lid: the same rind tone, with rib grooves running in toward a small stem socket
            import math
            cx, cy = (w - 1) / 2, (h - 1) / 2
            for y in range(h):
                for x in range(w):
                    a = math.degrees(math.atan2(y - cy, x - cx)) % 45
                    r = max(abs(x - cx) / max(cx, 1), abs(y - cy) / max(cy, 1))
                    groove = (a < 7 or a > 38) and r > 0.25
                    img[y, x] = T("pump", 3 if groove else 2)
                    if r <= 0.22:
                        img[y, x] = T("pump", 3)
        return img
    return f


def smooth_rind():
    """Face plate rind: smooth, with only two soft ribs at the plate edges so the carving reads clean."""
    def f(w, h, fc, key):
        img = _blank(w, h)
        img[:, :] = T("pump", 2)
        if fc == "north":
            img[:, :2] = T("pump", 3); img[:, -2:] = T("pump", 3)
            img[:max(1, h // 8), :] = T("pump", 1)
        return img
    return f


def carved(lit=False):
    """Carved face, painted solid: no cut-outs and no hollow behind the face, so the face can never
    look see-through. Unlit: the openings are deep shadow with the cut rind wall catching light at
    the bottom. Lit: the openings glow and flicker, and the rind is a little deeper so they pop.
    The mask goes on at a whole-pixel scale, centred, so both halves of the face match exactly
    (give the face an even pixel width)."""
    base = pump_skin()
    def f(w, h, fc, key):
        img = base(w, h, fc, key)
        if fc != "north":
            return img
        if lit:
            img[..., :3] = (img[..., :3].astype(float) * 0.8).astype(img.dtype)
        s = max(1, min(w // 16, h // 14))
        ox, oy = (w - 16 * s) // 2, (h - 14 * s) // 2
        hole = np.zeros((h, w), bool)
        for y in range(h):
            for x in range(w):
                fx, fy = (x - ox) // s, (y - oy) // s
                hole[y, x] = 0 <= fx < 16 and 0 <= fy < 14 and FACE[fy][fx] == "#" and x - ox >= 0 and y - oy >= 0
        k = fr() if lit else 0
        inner = (1, 0, 1, 2, 0, 1)[k]
        for y in range(h):
            for x in range(w):
                nb = [(y + dy, x + dx) for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1))]
                if hole[y, x]:
                    edge = any(not (0 <= yy < h and 0 <= xx < w and hole[yy, xx]) for yy, xx in nb)
                    if lit:
                        img[y, x] = T("jackglow", inner + 1 if edge else inner)
                    else:
                        img[y, x] = T("ebony", 6)
                elif any(0 <= yy < h and 0 <= xx < w and hole[yy, xx] for yy, xx in nb):
                    img[y, x] = T("pump", 4)                              # dark rim around every cut
        return img
    if lit:
        f.animated = True
    return f


def inner_rind(lit=False):
    """Second carving layer behind the face: same cuts shrunk by 1px, dark orange inner wall."""
    def f(w, h, fc, key):
        img = _blank(w, h)
        img[:, :] = T("pump", 4) if not lit else T("jackglow", 3)
        hole = np.zeros((h, w), bool)
        for y in range(h):
            for x in range(w):
                hole[y, x] = FACE[int(y * 14 / h)][int(x * 16 / w)] == "#"
        shrunk = hole.copy()
        for y in range(h):
            for x in range(w):
                if hole[y, x] and not all(0 <= y + dy < h and 0 <= x + dx < w and hole[y + dy, x + dx]
                                          for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    shrunk[y, x] = False
        img[shrunk, 3] = 0
        img[~hole, 3] = 0
        return img
    return f


def rim_iron():
    def f(w, h, fc, key):
        img = _blank(w, h)
        img[:, :] = T("iron", 3)
        if fc == "up":
            img[:, :] = T("iron", 2)
            img[0, :] = img[-1, :] = T("iron", 1)
        if fc in SIDES and h >= 2:
            img[0, :] = T("iron", 1)
        return img
    return f


def glow_core(lit=True):
    """Inside of the pumpkin: warm yellow at the centre, orange toward the walls, gentle flicker."""
    def f(w, h, fc, key):
        img = _blank(w, h)
        k = fr() if lit else 0
        cx, cy = (w - 1) / 2, (h - 1) / 2 + (0.5 if k in (2, 5) else 0)
        for y in range(h):
            for x in range(w):
                d = max(abs(x - cx) / max(cx, 1), abs(y - cy) / max(cy, 1))
                if lit:
                    r = (0.45, 0.5, 0.4, 0.48, 0.55, 0.42)[k]
                    img[y, x] = T("jackglow", 0 if d < r * 0.5 else 1 if d < r else 2 if d < 0.8 else 3)
                else:
                    img[y, x] = T("ebony", 5 if d < 0.6 else 6)
        return img
    return animated(f) if lit else f


def iron():
    """Three flat iron tones: lit top band, body, shadow handled by baked light."""
    def f(w, h, fc, key):
        img = _blank(w, h)
        img[:, :] = T("iron", 2)
        if fc in SIDES and h >= 3:
            img[0, :] = T("iron", 0)
            img[1, :] = T("iron", 1)
        if fc == "up":
            img[:, :] = T("iron", 1)
        if fc == "down":
            img[:, :] = T("iron", 4)
        return img
    return f


def brew_top():
    def f(w, h, fc, key):
        k = fr()
        img = _blank(w, h)
        cx, cy = (w - 1) / 2, (h - 1) / 2
        for y in range(h):
            for x in range(w):
                d = max(abs(x - cx) / cx, abs(y - cy) / cy)
                swirl = (int((x - cx) * 0.7 + (y - cy) * 0.7 + k) % 4 == 0)
                tone = 3 if d > 0.82 else (1 if swirl else 2)
                img[y, x] = T("brew", tone)
        return img
    return animated(f)


def plaid2():
    def f(w, h, fc, key):
        img = _blank(w, h)
        for y in range(h):
            for x in range(w):
                tone = 2
                if x % 4 == 0: tone = 1
                if y % 4 == 0: tone = 1 if tone == 2 else 0
                if x % 4 == 2 and y % 4 == 2: tone = 3
                img[y, x] = T("plum", tone)
        if fc in SIDES and h > 3:
            img[-1, :] = T("plum", 5)
        return img
    return f


PATCH = art([
    "aaaaa",
    "abbba",
    "abcba",
    "abbba",
    "aaaaa",
], {"a": ("rust", 1), "b": ("denim", 1), "c": ("denim", 2)})


def bark(ramp="ebony"):
    def f(w, h, fc, key):
        img = _blank(w, h)
        vertical = h >= w
        for y in range(h):
            for x in range(w):
                a = x if vertical else y
                img[y, x] = T(ramp, 2 + (1 if a % 3 == 0 else 0))
        return img
    return f


def check(a="plum", la=1, lb=3, size=3):
    """Large, low-contrast checks with a darker hem row."""
    def f(w, h, fc, key):
        img = _blank(w, h)
        for y in range(h):
            for x in range(w):
                c = (x // size + y // size) % 2
                tone = la if c else lb - 1
                if x % size == 0 or y % size == 0:
                    tone += 1 if c else 0
                img[y, x] = T(a, tone)
        if fc in SIDES and h > 3:
            img[-1, :] = T(a, 5)
        return img
    return f


def sack_face(res_face=True):
    """Burlap sack head with a calm, hand-stitched face (smooth burlap, no checker weave)."""
    def f(w, h, fc, key):
        rng = random.Random(key)
        img = _blank(w, h)
        img[:, :] = T("bone", 2)
        for y in range(h):
            for x in range(w):
                r = rng.random()
                if r < 0.06:
                    img[y, x] = T("bone", 1)                         # light fibre
                elif r < 0.10:
                    img[y, x] = T("bone", 3)                         # dark fibre
        if fc in SIDES and h > 6:
            for x in range(0, w, 2):
                img[h - 2, x] = T("rust", 3)                         # gathered hem stitches
        if fc == "east" and w > 6:
            for y in range(2, h - 3, 2):
                img[y, w // 2] = T("rust", 3)                        # side seam
        if fc == "north" and w >= 12 and h >= 12:
            ey = int(h * 0.38)
            for ex in (int(w * 0.25), int(w * 0.6)):
                img[ey:ey + 3, ex:ex + 3] = T("ebony", 5)            # stitched buttons
                img[ey + 1, ex + 1] = T("ebony", 3)
                img[ey, ex] = T("slate", 1)
                img[ey - 2, ex:ex + 3] = T("ebony", 4)               # calm stitched brows
            nx, ny = w // 2, int(h * 0.56)
            img[ny, nx - 1:nx + 1] = T("rust", 2)                    # little sewn nose
            img[ny + 1, nx - 1:nx + 1] = T("rust", 3)
            my = int(h * 0.72)
            img[my, int(w * 0.35):int(w * 0.66)] = T("ebony", 4)     # straight mouth
        return img
    return f


def panels(ramp="ebony", trim="bone"):
    """Framed counter panels with a contrasting trim border."""
    base = wood(ramp, plank=2)
    def f(w, h, fc, key):
        img = base(w, h, fc, key)
        if fc not in ("north", "south") or w < 12 or h < 8:
            return img
        n = max(1, w // 14)
        pw = w / n
        for i in range(n):
            x0, x1 = int(i * pw) + 2, int((i + 1) * pw) - 2
            img[2, x0:x1] = img[h - 3, x0:x1] = T(trim, 2)
            img[2:h - 2, x0] = img[2:h - 2, x1 - 1] = T(trim, 2)
            img[3, x0 + 1:x1 - 1] = T(ramp, 5)
        return img
    return f


def potion_banner():
    def f(w, h, fc, key):
        img = _blank(w, h)
        img[:, :] = T("plum", 2)
        img[:, 0] = img[:, -1] = T("gold", 2)
        for x in range(w):                                        # swallowtail hem
            depth = 1 if abs(x - (w - 1) / 2) < w * 0.18 else 0
            for y in range(h - 1 - depth, h):
                img[y, x, 3] = 0
        cx = w // 2
        shape = ["..a..", "..a..", ".aaa.", "abbba", "abbba", ".aaa."]
        y0 = max(1, h // 2 - 4)
        for gy, row in enumerate(shape):
            for gx, ch in enumerate(row):
                x, y = cx - 2 + gx, y0 + gy
                if ch != "." and 0 <= x < w and 0 <= y < h:
                    img[y, x] = T("bone", 0) if ch == "a" else T("brew", 1)
        return img
    return f


BAT = art([
    "aa.........aa",
    ".aaa..a.a..aaa.",
    "..aaaaaaaaaaa..",
    "...aaaebeaaa...",
    "....aaaaaaa....",
    "......a.a......",
], {"a": ("ebony", 4), "b": ("ebony", 6), "e": ("pump", 0)})
BAT = art([r.ljust(15, ".")[:15] for r in [  # plum-rimmed so it reads against the night
    "aa...........aa",
    ".aaa..a.a..aaa.",
    "..aaaaaaaaaaa..",
    "...aaaebeaaa...",
    "....aaaaaaa....",
    "......a.a......"]], {"a": ("plum", 4), "b": ("ebony", 6), "e": ("pump", 0)})

LEAF = art([
    "....aa",
    "..aaba",
    ".aabaa",
    "aabaa.",
    "abaa..",
    "a.....",
], {"a": ("moss", 2), "b": ("moss", 0)})

CURL = art([
    ".aaa..",
    "a...a.",
    "a.a..a",
    "a..a.a",
    ".aa..a",
    ".....a",
    "....a.",
], {"a": ("moss", 3)})

WISP = art([
    "..a.",
    ".a..",
    ".a..",
    "..a.",
    "...a",
    "..a.",
    ".a..",
], {"a": ("brew", 0, 200)})

RING = art([
    ".aaa.",
    "a...a",
    "a...a",
    "a...a",
    ".aaa.",
], {"a": ("iron", 1)})

IVY = art([
    "..ab....",
    ".a......",
    ".a.bb...",
    "..a.....",
    "...a....",
    "...a.bb.",
    "..a.....",
    ".bba....",
    "...a....",
], {"a": ("moss", 3), "b": ("moss", 1)})


def halo_card():
    def f(w, h, fc, key):
        img = _blank(w, h)
        cx, cy = (w - 1) / 2, (h - 1) / 2
        for y in range(h):
            for x in range(w):
                d = ((x - cx) / cx) ** 2 + ((y - cy) / cy) ** 2
                if d < 1:
                    img[y, x] = T("jackglow", 1, int(38 * (1 - d) ** 1.5))
        return img
    return f


def leaf_tex():
    def f(w, h, fc, key):
        img = _blank(w, h)
        img[:, :] = T("moss", 2)
        if fc == "up" and w > 2:
            img[h // 2, :] = T("moss", 0)            # midrib
            img[:, 0] = T("moss", 3)
        if fc == "down":
            img[:, :] = T("moss", 4)
        return img
    return f


def fluted():
    def f(w, h, fc, key):
        img = _blank(w, h)
        for x in range(w):
            img[:, x] = T("iron", (1, 2, 3, 2)[x % 4])
        return img
    return f


SMOKE = art([
    "...aa.",
    "..aa..",
    ".aa...",
    ".aab..",
    "..aab.",
    "...aa.",
    "..aa..",
    ".aa...",
], {"a": ("brew", 0, 150), "b": ("brew", 1, 150)})


def rim_top():
    """Cauldron rim: iron ring on top with an open centre so the brew below shows through."""
    def f(w, h, fc, key):
        img = _blank(w, h)
        img[:, :] = T("iron", 2)
        if fc in SIDES and h >= 2:
            img[0, :] = T("iron", 0)
        if fc == "up":
            b = max(1, round(min(w, h) * 0.13))
            img[:, :] = T("iron", 1)
            img[0, :] = img[-1, :] = img[:, 0] = img[:, -1] = T("iron", 0)
            img[b:h - b, b:w - b, 3] = 0
            img[b, b:w - b] = T("iron", 3); img[b:h - b, b] = T("iron", 3)   # inner shadow edge
        if fc == "down":
            img[:, :] = T("iron", 4)
        return img
    return f


def bubbling():
    """Brew surface with bubbles baked in (no extra cubes needed)."""
    base = brew_top()
    def f(w, h, fc, key):
        img = base(w, h, fc, key)
        k = fr()
        for (bx, by, ph) in ((0.3, 0.35, 0), (0.62, 0.6, 2), (0.45, 0.25, 4), (0.7, 0.3, 1)):
            x, y = int(bx * w), int(by * h)
            if (k - ph) % 6 < 3 and 0 < x < w - 1 and 0 < y < h - 1:
                img[y, x] = T("brew", 0); img[y - 1, x] = T("brew", 0, 255)
                img[y, x + 1] = T("brew", 1)
        return img
    f.animated = True
    return f


def patched_plaid():
    base = plaid2()
    def f(w, h, fc, key):
        img = base(w, h, fc, key)
        if fc in SIDES and h > 8:
            img[-4:-2, :] = T("rust", 2)                                 # rope belt
            img[-3, ::3] = T("rust", 3)
            img[0, ::2] = T("hay", 1); img[1, 1::3] = T("hay", 2)        # straw poking out at the collar
        if fc == "north" and w >= 8 and h >= 8:
            for (px, py) in ((1, h // 4), (w - 5, h // 2 + 1)):
                img[py:py + 4, px:px + 4] = T("denim", 1)
                img[py, px:px + 4] = img[py + 3, px:px + 4] = T("rust", 1)
                img[py:py + 4, px] = img[py:py + 4, px + 3] = T("rust", 1)
        return img
    return f


def painted_jack(lit=True):
    """Single-box mini jack: the face is painted (glowing when lit) rather than cut out."""
    base = pump_skin()
    def f(w, h, fc, key):
        img = base(w, h, fc, key)
        if fc != "north":
            return img
        k = fr() if lit else 0
        if lit:
            img[..., :3] = (img[..., :3].astype(float) * 0.78).astype(img.dtype)   # deeper rind so the glow pops
        # Place the carving mask at a whole-pixel scale, centred, never resampled, so the face
        # keeps its exact shape (use res= on the box so the face texture is at least 14 x 10).
        s = max(1, min(w // 16, h // 14))
        ox, oy = (w - 16 * s) // 2, (h - 14 * s) // 2
        for y in range(h):
            for x in range(w):
                fx, fy = (x - ox) // s, (y - oy) // s
                if 0 <= fx < 16 and 0 <= fy < 14 and FACE[fy][fx] == "#":
                    img[y, x] = T("jackglow", (1, 0, 1, 2, 0, 1)[k]) if lit else T("ebony", 6)
        return img
    if lit:
        f.animated = True
    return f


def flask():
    def f(w, h, fc, key):
        img = _blank(w, h)
        img[:, :] = T("brew", 1)
        if fc in SIDES:
            img[: max(1, h // 4), :] = T("brew", 2)                  # meniscus band
            img[1:h - 1, max(1, w // 4)] = T("brew", 0)              # glass glint
            if fc == "north" and w >= 6 and h >= 6:
                y0 = h // 2
                img[y0:y0 + 3, 1:w - 1] = T("bone", 1)               # label
                img[y0 + 1, 2:w - 2] = T("plum", 3)
        return img
    return f


# ------------------------------------------------------------------ builders
def jack(m, lo, hi, lit=False, emit=15, stem=True, ribs=True, halo=True, lite=False):
    """Rounded jack-o'-lantern: 5 tapered tiers, side ribs, glowing hollow, twisted stem."""
    (x0, y0, z0), (x1, y1, z1) = lo, hi
    W, H, D = x1 - x0, y1 - y0, z1 - z0
    X = lambda f: x0 + W * f
    Y = lambda f: y0 + H * f
    Z = lambda f: z0 + D * f
    fw = float(int(W * 0.8))                                                                    # whole units -> even px width, symmetric face
    m.box([X(.5) - fw / 2, Y(.14), Z(.0)], [X(.5) + fw / 2, Y(.84), Z(.5)], carved(lit), res=2,
          emit=12 if lit else 0)                                                                # face band, solid
    m.box([X(.0), Y(.20), Z(.10)], [X(1.0), Y(.78), Z(.90)], pump_skin(), res=2)               # widest band, closed all round
    m.box([X(.18), Y(.0), Z(.16)], [X(.82), Y(.16), Z(.84)], pump_skin(), res=2)                 # bottom taper
    if not lite:
        m.box([X(.05), Y(.05), Z(.24)], [X(.95), Y(.21), Z(.76)], pump_skin(), res=2)
    m.box([X(.07), Y(.82), Z(.17)], [X(.93), Y(.93), Z(.83)], pump_skin(), res=2)                # shoulder
    if not lite:
        m.box([X(.17), Y(.79), Z(.07)], [X(.83), Y(.96), Z(.93)], pump_skin(), res=2)            # crossed: octagon from above
        m.box([X(.28), Y(.92), Z(.28)], [X(.72), Y(1.0), Z(.72)], pump_skin(), res=2)            # low crown
    if stem:
        cx, cz = X(.5), Z(.5)
        s = max(1.4, W * .14)
        m.box([cx - s / 2, Y(.95), cz - s / 2], [cx + s / 2, Y(1.0) + H * .16, cz + s / 2], bark("stem"),
              rot=("y", 22.5, [cx, Y(1.0), cz]))
        m.box([cx - s / 2, Y(1.0) + H * .12, cz - s / 2], [cx + s / 2, Y(1.0) + H * .28, cz + s / 2], bark("stem"),
              rot=("z", -22.5, [cx, Y(1.0) + H * .12, cz]))
        m.box([cx - s * .7, Y(1.0) + H * .26, cz - s * .7], [cx + s * .7, Y(1.0) + H * .33, cz + s * .7], bark("stem"))  # knot
        m.box([cx + s * .3, Y(.99), cz - W * .14], [cx + W * .30, Y(.99) + .7, cz + W * .02], leaf_tex(),
              rot=("y", 22.5, [cx, Y(1), cz]))                                                       # solid leaf
        m.card([cx - W * .34, Y(.94), cz + .5], [cx, Y(.94) + W * .36, cz + .5], CURL, rot=("y", -22.5, [cx, Y(1), cz]))


# ------------------------------------------------------------------ pieces
def jack_o_lantern(lit=False):
    m = Model("jack_o_lantern_lit" if lit else "jack_o_lantern")
    jack(m, [1.5, 0, 2], [14.5, 11, 14], lit=lit)
    return m


def cauldron(lit=False):
    m = Model("cauldron_lit" if lit else "cauldron")
    IR = iron()
    for (x, z) in ((7.25, 2.6), (3.2, 10.6), (11.3, 10.6)):
        m.box([x, 0, z], [x + 1.5, 3, z + 1.5], IR)                                            # short legs
    m.box([4.5, 2.2, 4.5], [11.5, 3.4, 11.5], IR)                                              # narrow base
    m.box([3, 3.2, 3], [13, 4.6, 13], IR)                                                      # lower curve
    m.box([1.5, 4.4, 3], [14.5, 8.6, 13], IR)                                                  # belly bulge, crossed
    m.box([3, 4.6, 1.5], [13, 8.4, 14.5], IR)
    m.box([3, 8.4, 3], [13, 9.8, 13], IR)                                                      # upper curve, pulls in
    m.box([2.4, 9.8, 2.4], [13.6, 11.2, 13.6], rim_top())                                      # rolled lip, open centre
    m.box([3.6, 10.7, 3.6], [12.4, 11.0, 12.4], bubbling(), emit=12, faces=("up",))           # brew, near the brim
    m.box([10.6, 9.5, 9.6], [11.6, 18, 10.6], wood("oak"), rot=("x", -22.5, [11.1, 9.5, 10.1]))   # ladle
    if lit:
        m.card([4.5, 0, 8], [11.5, 3.2, 8], candle_flame(), rot=("y", 45, [8, 0, 8]), emit=15)   # small fire under the pot
        m.card([4.5, 0, 8], [11.5, 3.2, 8], candle_flame(), rot=("y", -45, [8, 0, 8]), emit=15)
    m.box([4.5, 0, 7.3], [11.5, 1.2, 8.7], wood("spruce"), rot=("y", 22.5, [8, 0, 8]))         # kindling
    return m


def scarecrow():
    m = Model("scarecrow", floor=-16)
    m.box([7, -16, 7], [9, 18, 9], bark("spruce"))                                            # post
    m.box([3.5, 10.5, 7.2], [19.5, 12, 8.8], bark("spruce"))                                  # crossbar, hidden in the sleeve
    m.box([3.5, -1.5, 5], [12.5, 11, 11], patched_plaid())                                     # patched shirt
    m.box([-3.5, 9, 6], [3.5, 12.5, 10], plaid2(), rot=("z", 22.5, [3.5, 12.5, 8]))           # one arm droops
    m.box([12.5, 9.5, 6], [19.5, 13, 10], plaid2())
    m.card([-5.5, 5.5, 8], [-2.5, 9, 8], STRAW, rot=("z", 22.5, [-4, 9, 8]))                  # straw tufts at the cuffs
    m.card([19.5, 9, 8], [22.5, 12.5, 8], STRAW, rot=("z", -45, [21, 11, 8]))
    m.box([4, -5.5, 5.8], [12, -1.5, 10.2], solid("denim", 2))                                # short trousers
    m.box([4, 11.5, 4.5], [12, 19.5, 11.5], sack_face(), res=2)                               # sack head
    m.box([1.5, 19.3, 2], [14.5, 20.1, 14], solid("ebony", 3))                                # wide brim
    m.box([4.5, 20.1, 5], [11.5, 23.5, 11], solid("ebony", 2))                                # crown
    m.box([5.5, 23, 6], [10, 26.5, 10], solid("ebony", 2), rot=("z", 22.5, [7.75, 23, 8]))   # floppy tip
    m.box([14, 13, 6.5], [19, 16.6, 9.5], crow_body(), rot=("z", -22.5, [16.5, 13, 8]))      # crow perched on the arm
    m.box([17.4, 15.8, 6.75], [20.6, 19, 9.25], crow_head())
    return m


def crow_body():
    def f(w, h, fc, key):
        img = _blank(w, h)
        img[:, :] = T("ebony", 5)
        if fc in SIDES:
            img[0, :] = T("ebony", 4)                                    # soft sheen
            if fc in ("north", "south") and w >= 4:
                img[1:h - 1, 0] = T("ebony", 6)                          # folded wing edge
                img[h - 1, :2] = T("ebony", 3)                           # tail tips
        return img
    return f


def crow_head():
    def f(w, h, fc, key):
        img = _blank(w, h)
        img[:, :] = T("ebony", 5)
        if fc in ("north", "south") and w >= 3 and h >= 3:
            ex = w - 2 if fc == "north" else 1
            img[h // 3, ex] = T("hay", 0)                                # bright eye
            bx = w - 1 if fc == "north" else 0
            img[h // 2, bx] = T("pump", 1)                               # beak, seen from the side
        if fc == "east" and w >= 2 and h >= 3:
            img[h // 2 - 1:h // 2 + 1, w // 2 - 1:w // 2 + 1] = T("pump", 1)  # beak, front on
        if fc == "up":
            img[:, :] = T("ebony", 4)
        return img
    return f


def pumpkin_lamp(lit=False):
    m = Model("pumpkin_lamp_lit" if lit else "pumpkin_lamp", floor=-16)
    m.box([3, -16, 3], [13, -13, 13], stone())                                                # mossy plinth
    m.box([6, -13, 6], [10, 26, 10], fluted())                                                # fluted post
    m.box([5.2, 0.5, 5.2], [10.8, 2.2, 10.8], solid("pump", 2))                              # painted collar
    m.box([5, 25, 5], [11, 27, 11], iron())                                                   # flared cap
    m.box([6.6, 27, 6.6], [9.4, 29.6, 9.4], solid("pump", 1))                                 # finial ball
    m.box([9, 24, 7], [24.5, 25.6, 9], iron())                                                # arm
    m.box([22.9, 21.5, 7], [24.5, 24, 9], iron())                                             # hook
    m.card([-6, 21, 8], [6, 26, 8], BAT, rot=("y", -22.5, [0, 23.5, 8]))
    m.card([23.2, 18.5, 8], [24.2, 21.5, 8], art([".a.", "a.a", ".a.", ".b.", "b.b", ".b."],
                                                 {"a": ("iron", 1), "b": ("iron", 3)}), res=3)
    jack(m, [17, 7.5, 2], [30.5, 18.7, 14], lit=lit, stem=False, lite=True)                   # big hanging lantern
    return m


def stall(name, ramp="plum", trim="pump"):
    """Market stall. The roof is two mirror-image panels hinged on one ridge line, so both slopes
    match exactly; the posts stop inside the roof's thickness and never come out through the top."""
    import math
    m = Model(name, floor=-16)
    m.box([-14, -16, 2.5], [30, -2, 14], panels())                                            # framed counter
    m.box([-16, -2, 0], [32, 0, 16], wood("ebony", plank=2))                                  # top
    RY, ZR, L, TH = 31.0, 8.0, 15.0, 1.5                                                      # ridge height/z, panel length, thickness
    tn, cs = math.tan(math.radians(22.5)), math.cos(math.radians(22.5))
    under = lambda z: RY - abs(ZR - z) * tn - TH / cs                                         # roof underside at z
    for x in (-15, 29):
        for z in (1, 13):
            m.box([x, 0, z], [x + 2, round(under(z + 1) + 0.4, 2), z + 2], bark("ebony"))   # posts end inside the roof
    stripe = stripes(ramp, "bone", 3)
    roof = {"up": stripe, "down": stripe, "north": solid(ramp, 3), "south": solid(ramp, 3)}
    m.box([-16, RY - TH, ZR - L], [32, RY, ZR], solid(ramp, 3), over=roof, rot=("x", -22.5, [8, RY, ZR]))
    m.box([-16, RY - TH, ZR], [32, RY, ZR + L], solid(ramp, 3), over=roof, rot=("x", 22.5, [8, RY, ZR]))
    zv = -5.1
    m.box([-16, 20.5, zv - 0.3], [32, round(under(zv) + 0.25, 2), zv + 0.3], scallop(ramp, trim))   # valance, tucked under the eave
    sign = shop_sign("POTIONS")
    wpx = 40 + ((40 - sign.text_width) % 2)                                                   # even margins left and right
    m.box([8 - wpx / 4, 13, -2.8], [8 + wpx / 4, 18, -1.4], sign, res=2)                      # shop sign, 10 px tall: equal margins
    m.box([-4.5, 0, 4.5], [1.5, 7, 10.5], flask(), emit=12)                                  # hero potion
    m.box([-3, 7, 6], [0, 9.5, 9], solid("rust", 2))                                          # cork
    m.box([20, 0, 4], [27, 6, 10], painted_jack(True), emit=10, res=2)                        # glowing jack on the counter
    m.box([23, 6, 6.5], [24, 8, 7.5], bark("stem"), rot=("z", -22.5, [23.5, 6, 7]))           # its stem
    return m


def potion_stall():
    return stall("potion_stall", "plum", "pump")


def all_models():
    return [jack_o_lantern(False), jack_o_lantern(True), cauldron(False), cauldron(True),
            scarecrow(), pumpkin_lamp(False), pumpkin_lamp(True), potion_stall()]
