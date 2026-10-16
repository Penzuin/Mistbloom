"""Must-Have Props - Mistbloom Studios.

A neutral, vanilla-friendly prop set that fits any server: oak, spruce, iron, burlap and wax.
Storage & clutter: Wooden Crate (27 slots), Crate Stack, Oak Barrel (27 slots), Grain Sacks,
Apple Basket, Book Pile. Lights (on/off, flickering flame): Iron Lantern, Hanging Lantern,
Candle Cluster, Street Lamp. Outdoor & town: Signpost, Wheelbarrow, Park Bench (seats two),
Notice Board.

Front of every piece faces NORTH (-z). Two-wide pieces run along +x.
Pack standards: no coplanar overlaps, rounded or chamfered shapes instead of plain boxes,
rotations only at 22.5 / 45 degrees, flames never reach the edge of their card.
"""
import math, zlib
import numpy as np
from PIL import Image, ImageDraw
from engine import Model, T, _blank, wood, solid, sprite, animated, fr, SIDES, PANE_ALPHA

OAK = wood("oak", plank=3)
OAK_DARK = wood("oak", plank=3, base=3)
SPRUCE = wood("spruce", plank=3)
SPRUCE_DARK = wood("spruce", plank=3, base=3)
IRON = solid("darkiron", 2)
IRON_LIGHT = solid("iron", 2)


def _rng(key):
    return np.random.default_rng(zlib.crc32(key.encode()))


# ------------------------------------------------------------------ painters
def crate(ramp="oak", brace=True):
    """Crate boards: planks inside a darker frame, a diagonal brace across each side."""
    g = wood(ramp, plank=3)
    def f(w, h, face, key):
        img = g(w, h, face, key)
        if w < 5 or h < 5:
            return img
        edge = T(ramp, 3.5)
        img[0, :] = img[-1, :] = edge
        img[:, 0] = img[:, -1] = edge
        if face in SIDES and brace:
            for x in range(1, w - 1):
                y = int(round((x - 1) * (h - 3) / max(1, w - 3))) + 1
                if 0 < y < h - 1:
                    img[y, x] = T(ramp, 1)
                    if y + 1 < h - 1:
                        img[y + 1, x] = T(ramp, 3)
        return img
    return f


def staves(ramp="oak", hoops=(0.18, 0.82)):
    """Barrel sides: vertical staves and dark iron hoops. The top is a round plank lid."""
    def f(w, h, face, key):
        img = _blank(w, h)
        rng = _rng(key)
        if face in ("up", "down"):
            for y in range(h):
                for x in range(w):
                    img[y, x] = T(ramp, 1.5 + (0.5 if (y // 3) % 2 else 0) + (1.5 if face == "down" else 0))
            img[0, :] = img[-1, :] = T(ramp, 3.5)
            img[:, 0] = img[:, -1] = T(ramp, 3.5)
            return img
        side = 0.5 if face in ("east", "west") else 0
        for x in range(w):
            t = 1.5 + side + (0.5 if (x // 2) % 2 else 0) + rng.choice([0, 0, 0.5])
            img[:, x] = T(ramp, t)
            if x % 2 == 1:
                img[:, x] = T(ramp, t + 0.5)
        for frac in hoops:
            y = int(round(frac * (h - 1)))
            img[y, :] = T("darkiron", 2)
            if y + 1 < h:
                img[y + 1, :] = T("darkiron", 3)
        return img
    return f


def burlap(tone=1, tie=False):
    """Burlap sack cloth: a soft cross weave, darker at the bottom; tie = the twine band."""
    def f(w, h, face, key):
        img = _blank(w, h)
        base = tone + (0.6 if face in ("east", "west") else 0) + (1.4 if face == "down" else 0) - (0.3 if face == "up" else 0)
        for y in range(h):
            for x in range(w):
                img[y, x] = T("burlap", base + (0.4 if (x + y) % 2 else 0))
        if face in SIDES and h > 3:
            img[-1, :] = T("burlap", base + 1)
            if w > 6:
                img[1:-1, w // 2] = T("burlap", base + 0.8)                    # sewn seam
        if tie:
            img[:, :] = T("burlap", base + 0.6)
            if face in SIDES:
                img[h // 2, :] = T("spruce", 1)
                if h > 3:
                    img[h // 2 + 1, :] = T("spruce", 2)
        return img
    return f


def wicker():
    def f(w, h, face, key):
        img = _blank(w, h)
        side = 0.5 if face in ("east", "west") else 0
        for y in range(h):
            for x in range(w):
                img[y, x] = T("hay", 2 + side + (0.8 if ((x // 2) + y) % 2 else 0))
        if face in SIDES:
            img[0, :] = T("oak", 2)                                 # rolled rim
        return img
    return f


def apples(dense=True):
    """A heap of red apples seen from above: round 4x4 apples with a highlight, some with a stalk."""
    def f(w, h, face, key):
        img = _blank(w, h)
        img[:, :] = T("apple", 3)
        rng = _rng(key)
        disc = [".##.", "####", "####", ".##."]
        for cy in range(0, h, 4):
            for cx in range(-2 * ((cy // 4) % 2), w, 4):
                for dy in range(4):
                    for dx in range(4):
                        y, x = cy + dy, cx + dx
                        if disc[dy][dx] == "#" and 0 <= y < h and 0 <= x < w:
                            img[y, x] = T("apple", 1 if dy < 2 else 2)
                if 0 <= cy + 1 < h and 0 <= cx + 1 < w:
                    img[cy + 1, cx + 1] = T("apple", 0)
                if rng.random() < 0.35 and 0 <= cy < h and 0 <= cx + 2 < w:
                    img[cy, cx + 2] = T("spruce", 2)
        return img
    return f


def apple():
    """One apple: red with a lighter cheek, a stalk and a leaf on top."""
    def f(w, h, face, key):
        img = _blank(w, h)
        img[:, :] = T("apple", 1.6 + (0.6 if face in ("east", "west") else 0) + (1 if face == "down" else 0))
        if face in SIDES:
            img[0, :] = T("apple", 1.2)
            img[1:3, 1:3] = T("apple", 0.5)
            img[-1, :] = T("apple", 2.6)
        if face == "up":
            img[:, :] = T("apple", 1.2)
            c = w // 2
            img[c - 1:c + 1, c - 1:c + 1] = T("apple", 2.6)
            img[c - 1, c - 1] = T("spruce", 2)
            img[c - 1, c:c + 2] = T("leaf", 1)
        return img
    return f


def book(ramp, band="gold"):
    """A book: coloured cover, cream page edges on top and the fore-edge, gold spine bands."""
    def f(w, h, face, key):
        img = _blank(w, h)
        if face in ("up", "east"):
            img[:, :] = T("paper", 1 if face == "up" else 2)
            if face == "east":
                for y in range(0, h, 2):
                    img[y, :] = T("paper", 2.5)
            img[:, 0] = img[:, -1] = T(ramp, 2)
            img[0, :] = img[-1, :] = T(ramp, 2)
            return img
        img[:, :] = T(ramp, 1.6 if face in ("north", "south") else 2.2)
        if face == "west" and w > 5:                                 # the spine
            for x in (1, w - 2):
                img[:, x] = T(band, 1)
        if face == "down":
            img[:, :] = T(ramp, 3)
        return img
    return f


def glass(lit=True):
    """Lantern glass: warm and see-through when lit, cool grey when out; a thin frame line."""
    a = PANE_ALPHA[lit]
    g = "warmglass" if lit else "coldglass"
    def f(w, h, face, key):
        img = _blank(w, h)
        for y in range(h):
            for x in range(w):
                img[y, x] = T(g, 1 if (x + 2 * y) % 7 else 0, a)
        if face in ("up", "down"):
            img[:, :] = T("darkiron", 2)
        return img
    return f


def _flame(w, h, k):
    """Warm candle flame that flickers: white core, gold, an orange tip. Stays clear of the edges."""
    S = 6
    im = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    sway = [0, 0.6, 1, 0.4, -0.4, -1, -0.6, 0][k] * S * 0.35
    tall = [1, 0.94, 1.04, 0.9, 1, 1.06, 0.92, 0.98][k]
    cx, base = w * S / 2, h * S - S * 0.8
    top = base - (h - 1.6) * S * tall
    rx = w * S * 0.30
    def drop(scale, col):
        t = top + (base - top) * (1 - scale)
        pts = []
        for i in range(25):
            a = i / 24 * 2 * math.pi
            # teardrop: round bottom, pointed top that leans with the sway
            yy = math.cos(a)
            xx = math.sin(a)
            y = base - (base - t) * (0.5 - 0.5 * yy)
            r = rx * scale * (0.25 + 0.75 * math.sqrt(max(0, (y - t) / max(1, base - t))))
            x = cx + xx * r + sway * (1 - (y - t) / max(1, base - t))
            pts.append((x, y))
        d.polygon(pts, fill=col)
    drop(1.0, (255, 150, 40, 255))
    drop(0.8, (255, 214, 90, 255))
    drop(0.45, (255, 250, 220, 255))
    arr = np.array(im.resize((w, h), Image.BOX), np.uint8)
    a = arr[..., 3]
    a[a < 90] = 0
    a[a >= 90] = 255
    arr[0, :, 3] = 0; arr[-1, :, 3] = 0; arr[:, 0, 3] = 0; arr[:, -1, 3] = 0
    return arr


FLAME = sprite(_flame)


def wax(tone=0.5):
    """Candle wax with a drip down the side and a dark wick on top."""
    def f(w, h, face, key):
        img = _blank(w, h)
        img[:, :] = T("paper", tone + (0.6 if face in ("east", "west") else 0) + (1.5 if face == "down" else 0))
        if face in SIDES and h > 3 and w > 1:
            x = (zlib.crc32(key.encode()) % max(1, w - 1))
            img[0:max(2, h // 3), x] = T("paper", tone - 0.5)
            img[0, :] = T("paper", tone - 0.5)
        if face == "up":
            img[h // 2, w // 2] = T("darkiron", 3)
        return img
    return f


def chain():
    def f(w, h, face, key):
        img = _blank(w, h)
        for y in range(h):
            img[y, :] = T("darkiron", 1 if (y // 2) % 2 else 2.5)
        return img
    return f


def stone():
    def f(w, h, face, key):
        img = _blank(w, h)
        rng = _rng(key)
        base = 1.5 + (0.6 if face in ("east", "west") else 0) - (0.4 if face == "up" else 0) + (1.4 if face == "down" else 0)
        img[:, :] = T("stone", base)
        for p in rng.integers(0, w * h, max(1, w * h // 6)):
            y, x = divmod(int(p), w)
            img[y, x] = T("stone", base + rng.choice([-0.5, 0.5, 1]))
        if face in SIDES and h > 2:
            img[0, :] = T("stone", base - 0.5)
        return img
    return f


def sign_board(ramp="spruce"):
    """Signpost arrow board: planks with two rows of carved letters (no real words)."""
    g = wood(ramp, plank=4, base=1)
    def f(w, h, face, key):
        img = g(w, h, face, key)
        if face in ("north", "south") and w > 8 and h >= 4:
            rng = _rng(key)
            for row in ((h - 1) // 3, 2 * (h - 1) // 3 + 1)[: 2 if h >= 6 else 1]:
                x = 2
                while x < w - 3:
                    n = int(rng.integers(1, 4))
                    img[row, x:x + n] = T("spruce", 4)
                    x += n + 1
        return img
    return f


def notices():
    """Notice board face: spruce frame round a cork panel with pinned paper notes."""
    def f(w, h, face, key):
        img = SPRUCE_DARK(w, h, face, key)
        if face != "north" or w < 8 or h < 8:
            return img
        img[1:-1, 1:-1] = T("clay", 2)
        rng = _rng(key)
        for y in range(1, h - 1):
            for x in range(1, w - 1):
                if (x * 7 + y * 3) % 5 == 0:
                    img[y, x] = T("clay", 2.5)
        papers = [(2, 2, 7, 8), (9, 1, 14, 6), (16, 3, 22, 9), (3, 10, 9, 15), (11, 8, 17, 15), (19, 11, 25, 16)]
        for x0, y0, x1, y1 in papers:
            if x1 >= w - 1 or y1 >= h - 1:
                continue
            img[y0:y1, x0:x1] = T("paper", 1)
            img[y0, x0:x1] = T("paper", 0)
            for yy in range(y0 + 2, y1 - 1, 2):
                img[yy, x0 + 1:x1 - 1 - int(rng.integers(0, 2))] = T("spruce", 3)
            img[y0, (x0 + x1) // 2] = T("red", 1)                      # pin
        return img
    return f


def wheel():
    """Wheel side: spruce spokes inside an iron rim; the tread faces are iron."""
    def f(w, h, face, key):
        img = _blank(w, h)
        if face not in ("north", "south"):
            img[:, :] = T("darkiron", 2 + (0.5 if face == "down" else 0))
            return img
        cx, cy = (w - 1) / 2, (h - 1) / 2
        img[:, :] = T("spruce", 3.5)
        for y in range(h):
            for x in range(w):
                if abs(x - cx) < 0.8 or abs(y - cy) < 0.8 or abs(abs(x - cx) - abs(y - cy)) < 0.8:
                    img[y, x] = T("oak", 1)
        img[0, :] = img[-1, :] = T("darkiron", 2)
        img[:, 0] = img[:, -1] = T("darkiron", 2)
        img[int(cy):int(cy) + 2, int(cx):int(cx) + 2] = T("darkiron", 3)
        return img
    return f


def hay():
    def f(w, h, face, key):
        img = _blank(w, h)
        rng = _rng(key)
        base = 1.5 + (0.5 if face in ("east", "west") else 0)
        img[:, :] = T("hay", base)
        for _ in range(w * h // 3):
            y, x = int(rng.integers(0, h)), int(rng.integers(0, w))
            img[y, x:x + 2] = T("hay", base + rng.choice([-1, 1]))
        return img
    return f


# ------------------------------------------------------------------ pieces
def wooden_crate():
    """An oak crate with darker corner posts, framed plank sides and a diagonal brace. Opens 27 slots."""
    m = Model("wooden_crate")
    m.box([1, 0, 1], [15, 13.5, 15], crate("oak"), res=2)
    for x0, z0 in ((0.5, 0.5), (13.5, 0.5), (0.5, 13.5), (13.5, 13.5)):
        m.box([x0, 0, z0], [x0 + 2, 14, z0 + 2], OAK_DARK, res=2)
    m.box([0.75, 14, 0.75], [15.25, 15, 15.25], crate("oak", brace=False), res=2)       # lid
    return m


def crate_stack():
    """Two crates side by side with a smaller spruce crate set on top, turned a little."""
    m = Model("crate_stack")
    m.box([1, 0, 1], [15, 14, 15], crate("oak"), res=2)
    m.box([0.75, 14, 0.75], [15.25, 15, 15.25], crate("oak", brace=False), res=2)
    m.box([17, 0, 2], [30, 11, 14.5], crate("spruce"), res=2)
    m.box([16.75, 11, 1.75], [30.25, 12, 14.75], crate("spruce", brace=False), res=2)
    m.box([3, 15, 3.5], [12.5, 23, 12.5], crate("spruce"), rot=("y", 22.5, [8, 15, 8]), res=2)
    m.box([2.75, 23, 3.25], [12.75, 23.75, 12.75], crate("spruce", brace=False), rot=("y", 22.5, [8, 15, 8]), res=2)
    return m


def oak_barrel():
    """A round oak barrel: bulging staves, iron hoops and a plank lid. Opens 27 slots.
    Each section is two crossed boxes (a stepped circle); the second one sits 0.25 inside top and
    bottom so no two faces share a plane."""
    m = Model("oak_barrel")
    def ring(r_out, r_in, y0, y1, hoops):
        m.box([8 - r_out, y0, 8 - r_in], [8 + r_out, y1, 8 + r_in], staves(hoops=hoops), res=2)
        m.box([8 - r_in, y0 + 0.25, 8 - r_out], [8 + r_in, y1 - 0.25, 8 + r_out], staves(hoops=hoops), res=2)
    ring(5.5, 4, 0, 3.25, (0.5,))
    ring(6.5, 5, 3, 13, (0.12, 0.88))
    ring(5.5, 4, 12.75, 15.5, (0.4,))
    return m


def grain_sacks():
    """Three burlap sacks tied with twine at the neck: two standing, one leaning against them."""
    m = Model("grain_sacks")
    for (x0, z0, hgt) in ((1.5, 5, 9.5), (8.5, 7.5, 8)):
        m.box([x0, 0, z0], [x0 + 6.5, hgt, z0 + 6.5], burlap(2), res=2)                          # body
        m.box([x0 + 0.75, hgt, z0 + 0.75], [x0 + 5.75, hgt + 1.25, z0 + 5.75], burlap(1.6), res=2)  # soft shoulder
        m.box([x0 + 2, hgt + 1.25, z0 + 2], [x0 + 4.5, hgt + 2.5, z0 + 4.5], burlap(tie=True), res=4)  # twine neck
        m.box([x0 + 1.5, hgt + 2.5, z0 + 1.5], [x0 + 5, hgt + 3.5, z0 + 5], burlap(1.4), res=4)     # flared top
    lean = ("z", -22.5, [11, 0, 4])
    m.box([9, 0, 0.75], [14.5, 7.5, 6], burlap(2.2), rot=lean, res=2)
    m.box([9.75, 7.5, 1.5], [13.75, 8.5, 5.25], burlap(1.8), rot=lean, res=2)
    return m


def apple_basket():
    """A round wicker basket heaped with red apples, with a bent handle over the top."""
    m = Model("apple_basket")
    m.box([4, 0, 4], [12, 1, 12], wicker(), res=2)
    m.box([3, 1, 4.5], [13, 6, 11.5], wicker(), over={"up": apples()}, res=4)          # round basket: two crossed boxes
    m.box([4.5, 1.25, 3], [11.5, 5.75, 13], wicker(), over={"up": apples()}, res=4)
    # apples: each a slightly different size and height so no two faces share a plane
    for (x, z, y, s) in ((5, 5.25, 6, 2.75), (8.25, 4.5, 6.1, 2.6), (10.75, 6.25, 6.2, 2.8), (5.75, 8.75, 6.05, 2.7),
                         (9.25, 8.75, 6.15, 2.65), (7.25, 6.75, 7.9, 2.75)):
        m.box([x - s / 2, y, z - s / 2], [x + s / 2, y + s, z + s / 2], apple(), res=4)
    for x0 in (3.5, 11.75):                                                          # handle
        m.box([x0, 6, 7.4], [x0 + 0.75, 12, 8.6], OAK_DARK, res=4)
    m.box([3.5, 12, 7.4], [12.5, 12.75, 8.6], OAK_DARK, res=4)
    return m


def book_pile():
    """A loose stack of five books in red, blue, green and brown, each set at a slightly different angle."""
    m = Model("book_pile")
    stack = [("red", 3, 3, 13, 12, 2, 0), ("blue", 4, 3.5, 12.5, 11, 1.75, 22.5), ("spruce", 3.5, 4, 12, 11.5, 2.25, 0),
             ("green", 4.5, 4.5, 11.5, 10.5, 1.5, -22.5), ("red", 5, 5, 11, 10, 1.5, 0)]
    y = 0
    for ramp, x0, z0, x1, z1, t, ang in stack:
        rot = ("y", ang, [8, y, 8]) if ang else None
        m.box([x0, y, z0], [x1, y + t, z1], book(ramp), rot=rot, res=2)
        y += t
    return m


def _lantern_head(m, x0, y0, z0, size, lit, em, roof=True):
    """A square iron lantern: base plate, four corner posts, glass, a candle with a flame and a stepped roof."""
    s = size
    x1, z1 = x0 + s, z0 + s
    hgt = s * 1.25
    m.box([x0, y0, z0], [x1, y0 + 1, z1], IRON, res=2)
    for px, pz in ((x0, z0), (x1 - 1, z0), (x0, z1 - 1), (x1 - 1, z1 - 1)):
        m.box([px, y0 + 1, pz], [px + 1, y0 + 1 + hgt, pz + 1], IRON, res=4)
    m.box([x0 + 0.5, y0 + 1, z0 + 0.5], [x1 - 0.5, y0 + 1 + hgt, z1 - 0.5], glass(lit), emit=em, res=2)
    cx, cz = x0 + s / 2, z0 + s / 2
    cw = max(1.5, s * 0.25)
    m.box([cx - cw / 2, y0 + 1, cz - cw / 2], [cx + cw / 2, y0 + 1 + hgt * 0.35, cz + cw / 2], wax(), res=4)
    if lit:
        m.crossed(cx, y0 + 1 + hgt * 0.35, cz, s * 0.45, hgt * 0.45, FLAME, emit=15, res=4)
    top = y0 + 1 + hgt
    if roof:
        m.box([x0 - 0.5, top, z0 - 0.5], [x1 + 0.5, top + 1, z1 + 0.5], IRON, res=2)
        m.box([x0 + 0.75, top + 1, z0 + 0.75], [x1 - 0.75, top + 2, z1 - 0.75], IRON, res=2)
        m.box([cx - 1, top + 2, cz - 1], [cx + 1, top + 2.75, cz + 1], IRON, res=4)
    return top + 2.75


def iron_lantern(lit=True):
    """A dark iron lantern with a candle inside and a carry ring on top. Light on or off."""
    m = Model("iron_lantern_lit" if lit else "iron_lantern")
    top = _lantern_head(m, 4.5, 0, 4.5, 7, lit, 15 if lit else 0)
    m.box([7.5, top, 7.6], [8.5, top + 2, 8.4], IRON, res=4)                         # ring
    return m


def hanging_lantern(lit=True):
    """The same lantern hung from the ceiling on a short iron chain. Light on or off."""
    m = Model("hanging_lantern_lit" if lit else "hanging_lantern")
    top = _lantern_head(m, 4.5, -3, 4.5, 7, lit, 15 if lit else 0)
    n, y = 4, top                                                                             # chain: alternating flat links
    step = (15.5 - top) / n
    for i in range(n):
        a, b = (7.3, 7.85) if i % 2 == 0 else (7.85, 7.3)
        m.box([a, y, b], [16 - a, y + step, 16 - b], chain(), res=4)
        y += step
    m.box([6, 15.5, 6], [10, 16, 10], IRON, res=4)                                         # ceiling plate
    return m


def candle_cluster(lit=True):
    """Three cream candles of different heights on a round iron dish, tallest at the back. Light on or off."""
    m = Model("candle_cluster_lit" if lit else "candle_cluster")
    m.box([3.5, 0, 5], [12.5, 0.75, 11], IRON, res=2)                                     # round dish
    m.box([5, 0.1, 3.5], [11, 0.5, 12.5], IRON, res=2)
    for (x, z, hgt) in ((6, 9.5, 7), (10, 9, 5), (7.75, 5.5, 3.5)):
        m.box([x - 1.25, 0.75, z - 1.25], [x + 1.25, 0.75 + hgt, z + 1.25], wax(), res=4)
        if lit:
            m.crossed(x, 0.75 + hgt, z, 2.5, 3.5, FLAME, emit=15, res=4)
    return m


def street_lamp(lit=True):
    """A two-block iron street lamp on a stone footing, with a lantern head. Light on or off."""
    m = Model("street_lamp_lit" if lit else "street_lamp")
    m.box([4.5, 0, 4.5], [11.5, 2, 11.5], stone(), res=2)
    m.box([5.5, 2, 5.5], [10.5, 3, 10.5], IRON, res=2)
    m.box([7, 3, 7], [9, 21, 9], IRON, res=2)
    m.box([6.5, 21, 6.5], [9.5, 22, 9.5], IRON, res=2)
    _lantern_head(m, 4.5, 22, 4.5, 7, lit, 15 if lit else 0, roof=False)
    m.box([4, 31, 4], [12, 32, 12], IRON, res=2)                                          # cap
    return m


def signpost():
    """A spruce signpost with two arrow boards pointing different ways, on a small stone footing."""
    m = Model("signpost")
    m.box([6, 0, 6], [10, 1.5, 10], stone(), res=2)
    m.box([7, 1.5, 7], [9, 24, 9], SPRUCE_DARK, res=2)
    m.box([6.5, 24, 6.5], [9.5, 25, 9.5], SPRUCE, res=2)
    m.box([1.5, 18, 6], [13, 22, 7], sign_board(), res=2)                                # board one, points east
    m.box([13, 18.75, 6], [14.5, 21.25, 7], sign_board(), res=2)
    m.box([14.5, 19.5, 6], [15.5, 20.5, 7], sign_board(), res=2)
    flip = ("y", -22.5, [8, 12, 8])                                                     # board two, points west
    m.box([3.5, 12, 9], [15, 16, 10], sign_board(), rot=flip, res=2)
    m.box([2, 12.75, 9], [3.5, 15.25, 10], sign_board(), rot=flip, res=2)
    m.box([1, 13.5, 9], [2, 14.5, 10], sign_board(), rot=flip, res=2)
    return m


def wheelbarrow():
    """A wooden wheelbarrow full of hay, with an iron-rimmed wheel at the front and two handles."""
    m = Model("wheelbarrow")
    m.box([4, 5, 2], [20, 6, 14], SPRUCE, res=2)                                         # floor
    m.box([4, 6, 2], [20, 10, 3], SPRUCE, res=2)                                         # sides
    m.box([4, 6, 13], [20, 10, 14], SPRUCE, res=2)
    m.box([3, 6, 2], [4, 10, 14], SPRUCE_DARK, res=2)                                    # back
    m.box([20, 6, 2], [21, 10.5, 14], SPRUCE_DARK, res=2)                                # front
    m.box([4, 6, 3], [20, 10.75, 13], hay(), res=2)                                      # hay load
    m.box([20.5, 1.75, 6.5], [29.5, 7.25, 8.5], wheel(), res=4)                          # wheel: a stepped circle
    m.box([22.25, 0, 6.75], [27.75, 9, 8.25], wheel(), res=4)
    m.box([20, 4, 6], [25, 5, 9], IRON, res=4)                                     # axle bracket
    for z0 in (2.25, 12.75):
        m.box([-4, 7, z0], [4, 8, z0 + 1], SPRUCE_DARK, res=2)                          # handles
        m.box([4.5, 0, z0 + 0.25], [5.5, 5, z0 + 0.75], SPRUCE_DARK, res=4)             # legs
    return m


def park_bench():
    """A two-block park bench: spruce slats on dark iron ends with armrests. Seats two."""
    m = Model("park_bench")
    for x0 in (1, 29.5):
        m.box([x0, 0, 4], [x0 + 1.5, 6.5, 12], IRON, res=2)                              # iron end
        m.box([x0, 9.5, 3], [x0 + 1.5, 10.5, 11.5], IRON, res=2)                         # armrest, stops at the back post
        m.box([x0, 6.5, 11.5], [x0 + 1.5, 17, 13], IRON, res=2)                          # back post
        m.box([x0, 6.5, 4], [x0 + 1.5, 9.5, 5], IRON, res=2)                             # arm support
    for z0, z1 in ((3.5, 6.25), (6.75, 9.5), (10, 11.5)):
        m.box([2.5, 6.5, z0], [29.5, 7.5, z1], SPRUCE, res=2)                            # seat slats
    m.box([2.5, 9, 11.75], [29.5, 11.5, 12.75], SPRUCE, res=2)                           # back slats
    m.box([2.5, 12.5, 11.75], [29.5, 15, 12.75], SPRUCE, res=2)
    return m


def notice_board():
    """A standing spruce notice board with a little roof and paper notes pinned to the cork."""
    m = Model("notice_board")
    for x0 in (1.5, 13):
        m.box([x0, 0, 7], [x0 + 1.5, 23, 9], SPRUCE_DARK, res=2)                         # legs
    m.box([1, 9, 7.5], [15, 21, 8.5], notices(), res=2)                                  # board
    m.box([0, 23, 5.5], [16, 24, 10.5], SPRUCE, res=2)                                   # roof
    m.box([1.5, 24, 6.5], [14.5, 25, 9.5], SPRUCE_DARK, res=2)
    return m


LIGHTS = ("iron_lantern", "hanging_lantern", "candle_cluster", "street_lamp")


def all_models():
    out = [wooden_crate(), crate_stack(), oak_barrel(), grain_sacks(), apple_basket(), book_pile()]
    for fn in (iron_lantern, hanging_lantern, candle_cluster, street_lamp):
        out += [fn(False), fn(True)]
    out += [signpost(), wheelbarrow(), park_bench(), notice_board()]
    return out


if __name__ == "__main__":
    for mm in all_models():
        print(f"{mm.name:22s} {mm.check():2d} elements  animated={mm.is_animated()}")
