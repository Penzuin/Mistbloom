"""Cozy Bedroom (free pack) - Mistbloom Studios.

A warm cottage bedroom: honey oak, cream linen and lilac fabrics. Seven pieces, all real 3D:
Quilted Bed (2 blocks, seats two), Bedside Table (9 slots), Toadstool Lamp (light on/off),
Braided Rug (2x2), Wall Shelf (books and a swaying plant), Wardrobe (2 tall, 27 slots) and
Floor Cushions (seats one).

Front of every piece faces NORTH (-z). The bed runs along +x (the block to its right).
The wall shelf puts its back on z=16.
Pack standards: no coplanar overlaps, rounded stepped shapes instead of plain boxes,
rotations only at 22.5 / 45 degrees, faces only on characters (none here).
"""
import math, zlib
import numpy as np
from PIL import Image, ImageDraw
from engine import Model, T, _blank, wood, panel, sprite, animated, fr, SIDES

OAK = wood("honey", plank=2)
OAK_DARK = wood("honey", plank=2, base=3)


def _rng(key):
    return np.random.default_rng(zlib.crc32(key.encode()))


# ------------------------------------------------------------------ painters
def linen(ramp="linen", tone=1, seam=False):
    """Soft cloth: gentle shading, a lighter top, a faint stitched seam round the big faces."""
    def f(w, h, face, key):
        img = _blank(w, h)
        rng = _rng(key)
        base = tone + (0.6 if face in ("east", "west") else 0) + (1.5 if face == "down" else 0) - (0.4 if face == "up" else 0)
        img[:, :] = T(ramp, base)
        for p in rng.integers(0, w * h, max(1, w * h // 9)):
            y, x = divmod(int(p), w)
            img[y, x] = T(ramp, base + 0.5)
        if face in SIDES and h > 2:
            img[-1, :] = T(ramp, base + 1)
        if seam and w > 4 and h > 4:
            for x in range(1, w - 1):
                if x % 2 == 0:
                    img[1, x] = T(ramp, base + 1); img[-2, x] = T(ramp, base + 1)
        return img
    return f


def quilt(top_rows=None):
    """Patchwork quilt: lilac, sage and cream squares with darker stitch lines. The draped sides
    carry the same squares and a hemmed bottom edge."""
    cols = [("lilac", 1), ("linen", 1), ("sage", 1), ("linen", 1), ("lilac", 2), ("sage", 2)]
    def f(w, h, face, key):
        img = _blank(w, h)
        sq = 6
        for y in range(h):
            for x in range(w):
                i = (x // sq) + (y // sq) * 2
                ramp, tone = cols[i % len(cols)]
                if face in ("east", "west"):
                    tone += 0.6
                if face == "down":
                    tone += 1.5
                if x % sq == 0 or y % sq == 0:
                    tone += 0.8
                img[y, x] = T(ramp, tone)
        if face in SIDES and h > 2:
            img[-1, :] = T("lilac", 3)
        return img
    return f


def stripes(ramp="lilac", alt="linen"):
    def f(w, h, face, key):
        img = _blank(w, h)
        for y in range(h):
            for x in range(w):
                u = x if face in ("up", "down", "north", "south") else y
                r = ramp if (u // 2) % 3 else alt
                t = 1 + (0.6 if face in ("east", "west") else 0) + (1.4 if face == "down" else 0)
                img[y, x] = T(r, t)
        return img
    return f


def brass(tone=1):
    def f(w, h, face, key):
        img = _blank(w, h)
        img[:, :] = T("gold", tone + 0.6)
        if face == "up":
            img[:, :] = T("gold", tone)
        if face == "down":
            img[:, :] = T("gold", tone + 2)
        return img
    return f


def drawers(rows=2):
    """Bedside table front: two drawer panels with a darker gap between them."""
    p = panel("honey", front=("north",), rows=rows)
    def f(w, h, face, key):
        img = p(w, h, face, key)
        return img
    return f


def book(ramp, band="gold"):
    """A book: coloured cover on the sides, cream page edges on top and the fore-edge, gold
    bands across the spine."""
    def f(w, h, face, key):
        img = _blank(w, h)
        if face in ("up", "east"):
            img[:, :] = T("parchment", 1 if face == "up" else 2)
            if face == "east":
                for y in range(0, h, 2):
                    img[y, :] = T("parchment", 2.5)
            img[:, 0] = T(ramp, 2); img[:, -1] = T(ramp, 2)
            return img
        img[:, :] = T(ramp, 1.6 if face in ("north", "south") else 2.2)
        if face == "west" and h > 5:                      # the spine
            for y in (1, h - 2):
                img[y, :] = T(band, 1)
        if face == "down":
            img[:, :] = T(ramp, 3)
        return img
    return f


def mug():
    def f(w, h, face, key):
        img = _blank(w, h)
        img[:, :] = T("linen", 1 if face != "down" else 2.5)
        if face in SIDES and h > 3:
            img[1, :] = T("lilac", 2)                      # a lilac stripe round the mug
        if face == "up":
            img[:, :] = T("clay", 3)                       # tea
            img[0, :] = img[-1, :] = T("linen", 1)
            img[:, 0] = img[:, -1] = T("linen", 1)
        return img
    return f


def toadcap(lit, spots=0):
    """Toadstool cap: rose with a few round cream spots placed evenly (spots = spots per side);
    lit, the gills underneath glow warm with a slow shimmer and the rim catches the light."""
    def f(w, h, face, key):
        img = _blank(w, h)
        rng = _rng(key)
        k = fr() % 8
        warm = 0 if lit else 1.2
        base = 1.1 + warm + (0.6 if face in ("east", "west") else 0) - (0.5 if face == "up" else 0)
        img[:, :] = T("toad", base)
        if face in SIDES and h > 2:
            img[0, :] = T("toad", base - 0.4)                 # a soft highlight along the top edge
        spot = T("linen", 0 if lit else 1.3)
        if spots and face in SIDES and h >= 3:
            for j in range(spots):
                sz = 3 if h >= 4 else 2
                x = int(round((j + 0.5) * w / spots)) - sz // 2 - (j % 2)
                y = (h - sz) // 2
                img[y:y + sz, x:x + sz] = spot
                img[y, x:x + sz] = T("linen", 0)
        if spots and face == "up" and w >= 4:
            c = w // 2 - 1
            img[c:c + 2, c:c + 2] = spot
        if face == "down":                                 # underside: the glowing gills
            for y in range(h):
                for x in range(w):
                    rr = math.hypot(x - (w - 1) / 2, y - (h - 1) / 2) / max(1, w / 2)
                    g = (0.2 + rr * 1.5) if lit else 3.4
                    if int(math.degrees(math.atan2(y - (h - 1) / 2, x - (w - 1) / 2)) // 15) % 2:
                        g += 0.45
                    img[y, x] = T("lampglow", g)
            if lit:
                for j, p in enumerate(rng.integers(0, w * h, 6)):
                    if (j + k) % 4 == 0:
                        y, x = divmod(int(p), w)
                        img[y, x] = (255, 252, 236, 255)
        elif lit and face in SIDES and h > 2:
            img[-1, :] = T("lampglow", 0.8 + (0.5 if k % 4 < 2 else 0))   # glow catching the rim
        return img
    return animated(f) if lit else f


def doors(ramp="honey", rows=(0.7, 0.3)):
    """Wardrobe front: two doors split down the middle, each with a tall upper and a short lower
    inset panel. Other faces are plain planks."""
    g = wood(ramp, plank=3)
    def f(w, h, face, key):
        img = g(w, h, face, key)
        if face != "north":
            return img
        mid = w // 2
        img[:, mid - 1] = T(ramp, 3.4)                     # the gap between the doors
        for x0, x1 in ((1, mid - 3), (mid + 1, w - 2)):
            y = 1
            for frac in rows:
                y1 = y + int(round((h - 2) * frac)) - 2
                if y1 - y >= 2 and x1 - x0 >= 2:
                    img[y, x0:x1 + 1] = T(ramp, 3); img[y1, x0:x1 + 1] = T(ramp, 1)
                    img[y:y1 + 1, x0] = T(ramp, 3); img[y:y1 + 1, x1] = T(ramp, 1)
                    img[y + 1:y1, x0 + 1:x1] = T(ramp, 1.6)
                y = y1 + 2
        return img
    return f


def tuft(ramp="lilac", tone=1):
    """Cushion cloth: clean soft shading, a deep button tuft in the middle of the top with four
    stitched seams running out from it, and cream piping round the top edge of the sides."""
    def f(w, h, face, key):
        img = _blank(w, h)
        base = tone + (0.6 if face in ("east", "west") else 0) + (1.5 if face == "down" else 0) - (0.3 if face == "up" else 0)
        img[:, :] = T(ramp, base)
        if face == "up" and w >= 6:
            c = w // 2 - 1
            img[1:-1, c:c + 2] = T(ramp, base + 0.8)                  # two seams crossing at the button
            img[c:c + 2, 1:-1] = T(ramp, base + 0.8)
            img[0, :] = img[-1, :] = T(ramp, base - 0.3)              # puffed edges catch the light
            img[:, 0] = img[:, -1] = T(ramp, base - 0.3)
            img[c:c + 2, c:c + 2] = T(ramp, base + 2.2)               # the button
        if face in SIDES and h > 2:
            img[0, :] = T("linen", 1)                                 # cream piping
            img[-1, :] = T(ramp, base + 0.6)
        return img
    return f


def stem(lit):
    def f(w, h, face, key):
        img = _blank(w, h)
        img[:, :] = T("linen", (0.5 if lit else 1.2) + (0.6 if face in ("east", "west") else 0))
        if face in SIDES and w > 2:
            img[:, 0] = T("linen", 2)
        return img
    return f


def rug_disc():
    """Round braided rug drawn on a flat box: concentric braided rings (lilac, cream, sage), the
    corners outside the circle left clear, only the middle of each side edge drawn."""
    ring_cols = [("lilac", 1.5), ("linen", 1), ("lilac", 1), ("sage", 1), ("linen", 1), ("lilac", 2)]
    def f(w, h, face, key):
        img = _blank(w, h)
        if face in ("up", "down"):
            cx, cy, R = (w - 1) / 2, (h - 1) / 2, min(w, h) / 2 - 0.3
            for y in range(h):
                for x in range(w):
                    d = math.hypot(x - cx, y - cy)
                    if d > R:
                        continue
                    ring = int(d / 3.2)
                    ramp, tone = ring_cols[ring % len(ring_cols)]
                    ang = math.atan2(y - cy, x - cx)
                    if int(ang * max(4, d) / 1.6) % 2:                  # braid twist: short even stitches
                        tone += 0.4
                    if face == "down":
                        tone += 1.5
                    img[y, x] = T(ramp, tone)
        return img
    return f


def pot():
    def f(w, h, face, key):
        img = _blank(w, h)
        img[:, :] = T("clay", 1.2 + (0.6 if face in ("east", "west") else 0) + (1.5 if face == "down" else 0))
        if face in SIDES and h > 3:
            img[0, :] = T("clay", 0.6)
            img[1, :] = T("clay", 0.6)
        if face == "up":
            img[:, :] = T("soot", 2)
            img[0, :] = img[-1, :] = T("clay", 1)
            img[:, 0] = img[:, -1] = T("clay", 1)
        return img
    return f


def _plant(w, h, k):
    """Trailing pothos: leafy stems that sway a little over the 8 frames."""
    S = 4
    im = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    sway = math.sin(k / 8 * 2 * math.pi) * 0.9 * S
    base_x, base_y = w * S / 2, h * S - 1
    stems = [(-0.38, 0.95), (-0.18, 1.0), (0.0, 0.85), (0.2, 0.95), (0.4, 0.75), (-0.5, 0.6), (0.48, 0.5)]
    for i, (dx, ht) in enumerate(stems):
        tipx = base_x + dx * w * S + sway * (0.6 + 0.4 * ht)
        tipy = base_y - ht * (h - 1.5) * S
        pts = [(base_x + (tipx - base_x) * t + math.sin(t * 3 + i) * S * 0.3, base_y + (tipy - base_y) * t) for t in np.linspace(0, 1, 7)]
        d.line(pts, fill=(70, 120, 66, 255), width=max(1, S // 2))
        for j, (px, py) in enumerate(pts[2:], 2):
            side = 1 if (j + i) % 2 else -1
            lx, ly = px + side * S * 0.9, py - S * 0.2
            col = (124, 186, 98, 255) if (j + i) % 3 else (160, 206, 120, 255)
            d.ellipse([lx - S * 1.0, ly - S * 0.7, lx + S * 1.0, ly + S * 0.7], fill=col)
    arr = np.array(im.resize((w, h), Image.BOX), np.uint8)
    a = arr[..., 3]
    a[a < 70] = 0
    a[a >= 70] = 255
    arr[0, :, 3] = 0; arr[:, 0, 3] = 0; arr[:, -1, 3] = 0
    return arr


PLANT = sprite(_plant)


# ------------------------------------------------------------------ pieces
def quilted_bed():
    """Honey-oak bed two blocks long: panelled headboard with a rounded cap, low footboard,
    cream mattress, patchwork quilt with the sheet turned down, two plump pillows and a striped
    throw folded across the foot."""
    m = Model("quilted_bed")
    for x0 in (0.5, 29.5):                                                    # turned legs
        for z0 in (0.5, 13.5):
            m.box([x0, 0, z0], [x0 + 2, 2.5, z0 + 2], OAK_DARK, res=2)
    m.box([0.25, 2.5, 0.25], [31.75, 5, 15.75], panel("honey", front=("north", "south"), rows=1), res=2)   # frame
    m.box([29.75, 5, 2], [32, 15, 14], panel("honey", front=("west",), rows=2), res=2)                     # headboard
    m.box([30, 15, 2], [31.75, 16.25, 14], OAK, res=2)                                                      # cap
    for z0 in (0.25, 14):                                                     # corner posts, taller than the panel
        m.box([29.75, 5, z0], [32, 17.5, z0 + 1.75], OAK_DARK, res=2)
    m.box([0, 5, 0.25], [1.75, 9.5, 15.75], panel("honey", front=("east",), rows=1), res=2)                # footboard
    m.box([1.75, 5, 0.75], [29.75, 8, 15.25], linen("linen", 1, seam=True), res=2)                         # mattress
    m.box([1.9, 5.5, 0.5], [20.5, 9, 15.5], quilt(), res=2)                                                # quilt, draped over the sides
    m.box([20.5, 6.5, 0.5], [22.25, 9.25, 15.5], linen("linen", 0.6), res=2)                               # sheet turned down
    for z0 in (1.5, 8.5):                                                     # two plump pillows, rounded by a second layer
        m.box([23, 8, z0], [29.25, 9.75, z0 + 6], linen("linen", 0.8, seam=True), res=2)
        m.box([23.75, 9.75, z0 + 0.75], [28.5, 10.5, z0 + 5.25], linen("linen", 0.5), res=2)
    m.box([3.5, 9, 0.25], [9.5, 10, 15.75], stripes("lilac", "linen"), res=2)  # throw folded over the foot
    return m


def bedside_table():
    """Two-drawer bedside table in honey oak with brass knobs, a little book stack and a mug of tea."""
    m = Model("bedside_table")
    for x0 in (2.25, 12):
        for z0 in (2.25, 12):
            m.box([x0, 0, z0], [x0 + 1.75, 2, z0 + 1.75], OAK_DARK, res=2)
    m.box([2.25, 2, 2.25], [13.75, 11.5, 13.75], drawers(2), res=2)            # body
    m.box([1.5, 11.5, 1.5], [14.5, 12.5, 14.5], OAK, res=2)                    # top with an overhang
    for y0 in (4.4, 8.6):                                                      # brass knobs
        m.box([7.25, y0, 1.6], [8.75, y0 + 1.25, 2.25], brass(1), res=4)
    m.box([3, 12.5, 4], [9, 13.5, 11], book("violet"), res=2)                  # book stack
    m.box([3.5, 13.5, 4.5], [8.25, 14.25, 10.25], book("sage"), res=2)
    m.box([10, 12.5, 5], [12.5, 15.5, 7.5], mug(), res=4)                      # mug of tea
    m.box([12.5, 13.25, 5.75], [13.25, 14.75, 6.75], linen("linen", 1), res=4) # mug handle
    return m


def toadstool_lamp(lit=True):
    """A toadstool lamp: wooden foot, cream stem and a rounded rose cap with cream spots.
    Lit, the cap's gills glow warm underneath and the rim catches the light."""
    m = Model("toadstool_lamp_lit" if lit else "toadstool_lamp")
    em = 15 if lit else 0
    m.box([4.5, 0, 4.5], [11.5, 0.75, 11.5], OAK, res=2)                      # foot
    m.box([5.25, 0.75, 5.25], [10.75, 1.5, 10.75], OAK_DARK, res=2)
    m.box([6.5, 1.5, 6.5], [9.5, 5, 9.5], stem(lit), res=4)                   # stem, a touch wider at the base
    m.box([6.85, 5, 6.85], [9.15, 7.5, 9.15], stem(lit), res=4)
    tiers = ((2.5, 13.5, 7.25, 8.75, 3), (3.5, 12.5, 8.75, 10, 2), (5, 11, 10, 11, 1), (6.5, 9.5, 11, 11.6, 1))
    for a, b, y0, y1, n in tiers:                                         # a wide, rounded dome
        m.box([a, y0, a], [b, y1, b], toadcap(lit, n), emit=em, res=3)
    return m


def braided_rug():
    """A round braided rug in lilac, cream and sage rings. Covers 2 x 2 blocks."""
    m = Model("braided_rug")
    m.box([-8, 0, -8], [24, 0.3, 24], rug_disc(), faces=("up", "down"), res=2)   # a flat disc; no square edges
    return m


def wall_shelf():
    """An oak wall shelf on two brackets with leaning books and a little pothos that sways."""
    m = Model("wall_shelf")
    m.box([0.5, 6, 9.5], [15.5, 7, 16], OAK, res=2)                         # shelf board
    for x0 in (2, 12.5):                                                     # brackets
        m.box([x0, 3, 14.5], [x0 + 1.5, 6, 16], OAK_DARK, res=2)
        m.box([x0, 4.5, 12.5], [x0 + 1.5, 6, 14.5], OAK_DARK, res=2)
    m.box([1.25, 7, 10.5], [2.5, 12.5, 15.5], book("violet"), res=2)        # books
    m.box([2.5, 7, 10.5], [3.6, 11.5, 15.5], book("sage"), res=2)
    m.box([3.6, 7, 10.75], [4.85, 12, 15.25], book("rose"), res=2)
    m.box([5.2, 7, 10.75], [6.3, 11, 15.25], book("navy"), rot=("z", -22.5, [5.2, 7, 13]), res=2)   # leaning
    m.box([10, 7, 11], [13.5, 9.75, 14.5], pot(), res=4)                     # pot
    m.crossed(11.75, 9.6, 12.75, 6, 6.5, PLANT, res=4)                        # swaying pothos
    return m


def wardrobe():
    """A two-block-tall honey oak wardrobe: two panelled doors with brass knobs, a moulded crown
    and short feet. Opens 27 storage slots."""
    m = Model("wardrobe")
    for x0 in (1, 13.25):                                                    # feet
        for z0 in (3, 13):
            m.box([x0, 0, z0], [x0 + 1.75, 1.5, z0 + 1.75], OAK_DARK, res=2)
    m.box([1, 2.5, 3], [15, 29.5, 15], doors("honey"), res=2)                 # body
    m.box([0.5, 1.5, 2.5], [15.5, 2.5, 15.5], OAK, res=2)                     # plinth
    m.box([0.5, 29.5, 2.5], [15.5, 30.5, 15.5], OAK, res=2)                   # crown
    m.box([1.25, 30.5, 3.25], [14.75, 31.25, 15], OAK_DARK, res=2)            # crown step
    for x0 in (6.25, 8.75):                                                   # brass knobs
        m.box([x0, 15, 2.4], [x0 + 1, 16.25, 3], brass(1), res=4)
    return m


def floor_cushions():
    """Two plump floor cushions stacked up: a lilac one with a sage one on top, turned a little,
    each with a button tuft and cream piping. Seats one."""
    m = Model("floor_cushions")
    m.box([1.5, 0, 1.5], [14.5, 3.5, 14.5], tuft("lilac", 1), res=2)
    m.box([2.5, 3.5, 2.5], [13.5, 4.25, 13.5], tuft("lilac", 0.8), res=2)       # the rounded top
    r = ("y", 22.5, [8, 6, 8])
    m.box([3.25, 4.25, 3.25], [12.75, 7, 12.75], tuft("sage", 1), rot=r, res=2)
    m.box([4.25, 7, 4.25], [11.75, 7.6, 11.75], tuft("sage", 0.8), rot=r, res=2)
    return m


def all_models():
    return [quilted_bed(), bedside_table(), toadstool_lamp(False), toadstool_lamp(True), braided_rug(), wall_shelf(),
            wardrobe(), floor_cushions()]


if __name__ == "__main__":
    for mm in all_models():
        print(f"{mm.name:22s} {mm.check():2d} elements  animated={mm.is_animated()}")
