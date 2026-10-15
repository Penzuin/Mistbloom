"""Night Lights (free pack) - Mistbloom Studios.

Three small glowing night lights, modelled in 3D (no flat picture cards for the main shapes),
each with a lit and an unlit model for the Nexo light toggle.
Front of every piece faces NORTH (-z). The wall piece puts its back on z=16.
Glowing surfaces are painted textures with a slow 8-frame shimmer (3 ticks a frame).
Pack standards: no coplanar overlaps, every card sits clear of solid parts and fades out
before its edges, rotations only at 22.5 / 45 degrees.
"""
import math, zlib
import numpy as np
from engine import Model, T, _blank, solid, wood, sprite, animated, fr, SIDES
import sprites as S

BASE_WOOD = wood("ebony", plank=2)
BASE_WOOD2 = wood("rosewood", plank=2)


def _rng(key):
    return np.random.default_rng(zlib.crc32(key.encode()))


# ------------------------------------------------------------------ painters
def brass(tone=1):
    """Polished brass: lit top edge, darker bottom edge, one soft vertical highlight stripe."""
    def f(w, h, face, key):
        img = _blank(w, h)
        img[:, :] = T("gold", tone + 0.6)
        if face in SIDES:
            if h > 2:
                img[0, :] = T("gold", tone - 0.6)
                img[-1, :] = T("gold", tone + 1.6)
            if w > 3:
                img[:, max(0, w // 3 - 1)] = T("gold", tone - 0.4)
        elif face == "up":
            img[:, :] = T("gold", tone)
            img[0, :] = T("gold", tone - 0.8)
        else:
            img[:, :] = T("gold", tone + 2)
        return img
    return f


def glow(ramp, lit, core=0.0, edge=2.0, dull=2.2, sparkle=True, spots=None, alpha=255):
    """Self-lit surface: bright core fading to a warmer edge on the big faces, edges a step darker,
    a few sparkle texels that hop around over the 8 frames. Unlit = the same pattern, dimmer."""
    shift = 0 if lit else dull
    def f(w, h, face, key):
        img = _blank(w, h)
        k = fr() % 8
        rng = _rng(key)
        cx, cy = (w - 1) / 2, (h - 1) / 2
        big = face in ("north", "south")
        for y in range(h):
            for x in range(w):
                if big:
                    d = min(1.0, math.hypot((x - cx) / max(1, w / 2), (y - cy) / max(1, h / 2)))
                    tone = core + (edge - core) * d ** 1.4
                else:
                    tone = edge + 0.4
                    if face == "up":
                        tone = edge - 0.3
                    if face == "down":
                        tone = edge + 1.2
                img[y, x] = T(ramp, tone + shift, alpha)
        if spots:
            n, sramp, stone = spots
            for p in rng.integers(0, max(1, w * h), n):
                y, x = divmod(int(p), w)
                if 0 < x < w - 1 and 0 < y < h - 1:
                    img[y, x] = T(sramp, stone + shift, alpha)
        if sparkle and lit and big and w > 3 and h > 3:
            for j, p in enumerate(rng.integers(0, w * h, 8)):
                if (j + k) % 4 == 0:
                    y, x = divmod(int(p), w)
                    img[y, x] = (255, 255, 246, alpha)
        return img
    return animated(f) if (sparkle and lit) else f


def jar_glass(base=34):
    """Clear jar glass: faint blue tint, bright rim lines and one diagonal glint."""
    def f(w, h, face, key):
        img = _blank(w, h)
        img[:, :] = T("moonglass", 1, base)
        if face in SIDES:
            img[:, 0] = T("moonglass", 0, 120)
            img[:, -1] = T("moonglass", 0, 120)
            img[-1, :] = T("moonglass", 0, 140)
            for i in range(h):
                x, y = 1 + i // 2, 1 + i
                if 0 < x < w - 1 and y < h - 1 and i < h * 0.45:
                    img[y, x] = (255, 255, 255, 120)
        if face == "down":
            img[:, :] = T("moonglass", 2, 110)
        return img
    return f


def cork():
    def f(w, h, face, key):
        img = _blank(w, h)
        rng = _rng(key)
        img[:, :] = T("parchment", 3)
        for p in rng.integers(0, w * h, max(2, w * h // 5)):
            y, x = divmod(int(p), w)
            img[y, x] = T("parchment", 4 if p % 2 else 2)
        if face in SIDES and h > 2:
            img[0, :] = T("parchment", 2)
        return img
    return f


def ribbon():
    def f(w, h, face, key):
        img = _blank(w, h)
        img[:, :] = T("violet", 1)
        if face == "up":
            img[:, :] = T("violet", 0)
        return img
    return f


def crescent_face(lit, X0, X1, Y0, Y1, cx, cy, Ro, dx, Ri):
    """Smooth crescent painted to match the 3D body behind it: inside the outer circle and outside
    the offset inner one. Edges anti-aliased, glow strongest along the middle of the band, three soft
    craters, sparkle texels that hop over the 8 frames. Card edges stay clear."""
    shift = 0 if lit else 2.2
    def f(w, h, face, key):
        img = _blank(w, h)
        k = fr() % 8
        rng = _rng("crescent")
        craters = [(cx - Ro * 0.62, cy + Ro * 0.18, 0.55), (cx - Ro * 0.48, cy - Ro * 0.38, 0.4), (cx - Ro * 0.25, cy + Ro * 0.62, 0.32)]
        sp = rng.integers(0, w * h, 10)
        for j in range(h):
            for i in range(w):
                cov, tone_acc = 0, 0.0
                for (a, b) in ((0.25, 0.25), (0.75, 0.25), (0.25, 0.75), (0.75, 0.75)):
                    u = (i + a) / w
                    wx = X1 - u * (X1 - X0) if face == "north" else X0 + u * (X1 - X0)
                    wy = Y1 - (j + b) / h * (Y1 - Y0)
                    ro = math.hypot(wx - cx, wy - cy)
                    ri = math.hypot(wx - (cx + dx), wy - cy)
                    if ro <= Ro and ri >= Ri:
                        cov += 1
                        band = min(Ro - ro, ri - Ri)                      # distance to the nearest edge
                        tone_acc += 2.0 - min(1.0, band / 1.1) * 2.0
                        for (qx, qy, qr) in craters:
                            if math.hypot(wx - qx, wy - qy) < qr:
                                tone_acc += 1.0
                if cov:
                    t = tone_acc / cov
                    img[j, i] = T("ivory", t + shift, int(255 * cov / 4))
        if lit:
            for n_, p in enumerate(sp):
                y, x = divmod(int(p), w)
                if img[y, x, 3] == 255 and (n_ + k) % 4 == 0:
                    img[y, x] = (255, 255, 246, 255)
        img[0, :, 3] = img[-1, :, 3] = 0
        img[:, 0, 3] = img[:, -1, 3] = 0
        return img
    return animated(f) if lit else f


# ------------------------------------------------------------------ pieces
def star_lamp(lit=True):
    """A brass lamp stand on a stepped wooden foot, holding a chunky four-point star that glows."""
    m = Model("star_lamp_lit" if lit else "star_lamp")
    m.box([4, 0, 4], [12, 1, 12], BASE_WOOD, res=2)                          # foot
    m.box([4.75, 1, 4.75], [11.25, 1.75, 11.25], BASE_WOOD2, res=2)          # second step
    m.box([6, 1.75, 6], [10, 2.25, 10], brass(1), res=2)                     # collar
    m.box([7.25, 2.25, 7.25], [8.75, 9, 8.75], brass(1), res=2)              # stem
    m.box([6.75, 5, 6.75], [9.25, 5.75, 9.25], brass(0), res=2)              # turned knob
    m.box([6.5, 9, 6.5], [9.5, 9.75, 9.5], brass(1), res=2)                  # cup
    star = glow("gold", lit, core=0.0, edge=2.2)
    arm = glow("gold", lit, core=0.6, edge=2.4, sparkle=False)
    em = 15 if lit else 0
    m.box([6.25, 12.75, 7], [9.75, 16.25, 9], star, rot=("z", 45, [8, 14.5, 8]), emit=em, res=3)   # centre diamond
    for frm, to in (([7.1, 16.25, 7.3], [8.9, 17.75, 8.7]), ([7.55, 17.75, 7.55], [8.45, 19.25, 8.45]),   # up ray + tip
                    ([7.1, 10.25, 7.3], [8.9, 12.75, 8.7]),                                               # down ray, into the cup
                    ([4.5, 13.6, 7.3], [6.25, 15.4, 8.7]), ([3, 14.05, 7.55], [4.5, 14.95, 8.45]),      # left ray + tip
                    ([9.75, 13.6, 7.3], [11.5, 15.4, 8.7]), ([11.5, 14.05, 7.55], [13, 14.95, 8.45])):  # right ray + tip
        m.box(frm, to, arm, emit=em, res=3)
    for ang in (45, -45):                                                     # diagonal rays: an eight-point star, not a cross
        m.box([7.35, 10.6, 7.45], [8.65, 18.4, 8.55], arm, rot=("z", ang, [8, 14.5, 8]), emit=em, res=3)
        m.box([7.7, 9.6, 7.7], [8.3, 19.4, 8.3], arm, rot=("z", ang, [8, 14.5, 8]), emit=em, res=3)   # thin points
    if lit:                                                                   # a little twinkle
        m.card([1.5, 18, 8], [3.5, 20, 8], sprite(S.twinkle_a), emit=15, res=4)
    return m


def moon_jelly_jar(lit=True):
    """A corked glass jar with a ribbon round the neck and a moon jelly glowing inside."""
    m = Model("moon_jelly_jar_lit" if lit else "moon_jelly_jar")
    em = 15 if lit else 0
    bell = glow("violet", lit, core=0.0, edge=1.4, alpha=200, spots=(3, "ivory", 0))
    bell_top = glow("violet", lit, core=0.0, edge=1.0, alpha=200, sparkle=False)
    for (lo, hi, y0, y1, p) in ((7.25, 8.75, 6.5, 6.9, bell_top),      # a rounded dome: four soft steps
                                (6.5, 9.5, 6.0, 6.5, bell),
                                (5.9, 10.1, 5.2, 6.0, bell),
                                (5.5, 10.5, 4.8, 5.2, bell_top)):    # frilly rim
        m.box([lo, y0, lo], [hi, y1, hi], p, emit=em, res=4)
    m.crossed(8, 0.9, 8, 4.75, 3.7, sprite(S.tentacles if lit else S.tentacles_unlit), emit=em, res=6)
    m.box([4.5, 0, 4.5], [11.5, 0.5, 11.5], jar_glass(), res=2)                  # thick base
    m.box([4.5, 0.5, 4.5], [11.5, 8, 11.5], jar_glass(), res=2, faces=SIDES)     # body
    m.box([5.25, 8, 5.25], [10.75, 8.75, 10.75], jar_glass(95), res=2, faces=SIDES + ("down", "up"))   # shoulder
    m.box([6, 8.75, 6], [10, 9.75, 10], jar_glass(110), res=2, faces=SIDES)        # neck
    m.box([5.9, 9.1, 5.9], [10.1, 9.4, 10.1], ribbon(), res=4)                # ribbon round the neck
    m.box([6.75, 9.5, 6.75], [9.25, 10.5, 9.25], cork(), res=4)                   # cork
    return m


def crescent_moon_sconce(lit=True):
    """A brass wall bracket holding a chunky 3D crescent moon by its thick back (no thin hanging rod)."""
    m = Model("crescent_moon_sconce_lit" if lit else "crescent_moon_sconce")
    em = 15 if lit else 0
    Ro, dx, Ri, cy = 4.6, 2.2, 3.9, 12.5
    a_ = (Ro * Ro - Ri * Ri + dx * dx) / (2 * dx)                             # where the two circles meet: the horn tips
    cx = 8 + (Ro - a_) / 2                                                   # moon centred on the wall plate
    m.box([6, 9.5, 15.25], [10, 15.5, 16], brass(1), res=2)                  # wall plate
    m.box([6.5, 10, 15], [9.5, 15, 15.25], brass(0), res=2)                   # raised centre of the plate
    m.box([7.5, cy - 0.6, 11.6], [8.5, cy + 0.6, 15], brass(1), res=2)       # arm straight out from the plate
    m.box([5.4, cy - 0.6, 11.6], [7.5, cy + 0.6, 12.6], brass(1), res=2)     # crossbar into the moon's thick back
    m.box([7.25, cy - 0.85, 14.4], [8.75, cy + 0.85, 15], brass(0), res=2)   # collar where the arm meets the plate
    moon = glow("ivory", lit, core=0.6, edge=2.4, sparkle=False)
    segs = [(0, 2.35, 2.4), (22.5, 2.15, 2.2), (-22.5, 2.15, 2.2), (45, 1.55, 2.0), (-45, 1.55, 2.0)]
    for ang, thick, L in segs:
        frm = [cx - Ro + 0.3, cy - L / 2, 10.4]
        to = [cx - Ro + 0.3 + thick, cy + L / 2, 11.6]
        rot = None if ang == 0 else ("z", ang, [cx, cy, 11])
        m.box(frm, to, moon, rot=rot, emit=em, res=4)
    X0, X1, Y0, Y1 = cx - Ro - 0.25, cx + a_ + 0.3, cy - Ro - 0.25, cy + Ro + 0.25
    face = crescent_face(lit, X0, X1, Y0, Y1, cx, cy, Ro, dx, Ri)
    m.box([X0, Y0, 10.2], [X1, Y1, 10.2], face, faces=("north",), emit=em, res=5)        # smooth front
    m.box([X0, Y0, 11.8], [X1, Y1, 11.8], face, faces=("south",), emit=em, res=5)        # and back
    return m


def all_models():
    out = []
    for fn in (star_lamp, moon_jelly_jar, crescent_moon_sconce):
        out += [fn(False), fn(True)]
    return out
