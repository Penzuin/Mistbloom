"""Frame-aware ghost sprites for Moonlit Ballroom (drawn at 4x, box-downsampled to texel size).

Ghost look (Mistbloom cute profile): soft moonlit spirits, translucent, one clean bell silhouette,
small calm faces (happy closed eyes, light blush), no googly eyes, no big chibi heads.
"""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

SS = 4                                     # supersample factor
BODY = (234, 240, 255)                     # moonlit white
SHADE = (196, 204, 240)                    # lavender shade
RIM = (250, 252, 255)
INK = (70, 58, 92)
BLUSH = (255, 150, 180)
HAT = (44, 36, 56)
GOLD = (238, 196, 110)
VIOLET = (178, 140, 224)
GLOW = (190, 220, 255)


def _canvas(w, h):
    return Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))


def _finish(im, w, h, glow=0.0):
    if glow:
        a = im.split()[3].filter(ImageFilter.GaussianBlur(3 * SS))
        halo = Image.new("RGBA", im.size, GLOW + (0,))
        halo.putalpha(a.point(lambda v: int(v * glow)))
        halo.alpha_composite(im)
        im = halo
    return np.array(im.resize((w, h), Image.BOX), np.uint8)


def _bell(cx, top, s, hem_w, height, sway=0.0, scallops=4):
    """Bell-shaped ghost outline: round head into a flared, scalloped hem. Returns polygon pts."""
    r = 8 * s
    pts = []
    for a in np.linspace(math.pi, 2 * math.pi, 18):                 # head dome
        pts.append((cx + r * math.cos(a), top + r + r * math.sin(a)))
    hem_y = top + height
    for t in np.linspace(0, 1, 10):                                  # right flank
        x = cx + r + (hem_w - r) * t ** 1.6 + sway * t ** 2
        pts.append((x, top + r + (hem_y - top - r) * t))
    n = scallops
    xs = np.linspace(cx + hem_w + sway, cx - hem_w + sway, n * 6 + 1)
    for i, x in enumerate(xs):                                       # scalloped hem
        ph = (i % 6) / 6
        pts.append((x, hem_y + 3 * s * math.sin(math.pi * ph)))
    for t in np.linspace(1, 0, 10):                                  # left flank
        x = cx - r - (hem_w - r) * t ** 1.6 + sway * t ** 2
        pts.append((x, top + r + (hem_y - top - r) * t))
    return pts


def ghost(d, cx, top, s, alpha=175, face="front", look=0.0, hat=False, flower=False, hem=1.0, sway=0.0,
          height=None, eyes="happy"):
    """Draw one ghost. face: 'front', 'back', 'over' (back with head turned to the viewer)."""
    height = height or 26 * s
    hem_w = 13 * s * hem
    pts = _bell(cx, top, s, hem_w, height, sway)
    d.polygon(pts, fill=BODY + (alpha,))
    # soft shade on the far side and a rim light
    shade = [(x + 2.5 * s, y + 2 * s) for x, y in pts]
    d.line(pts + [pts[0]], fill=RIM + (min(255, alpha + 60),), width=max(1, int(1.6 * s)))
    hy = top + 8 * s
    if face in ("front", "over"):
        fx = cx + look * 4 * s
        ey = hy + 1 * s
        if eyes == "happy":
            for ex in (fx - 3.4 * s, fx + 3.4 * s):
                d.arc([ex - 2 * s, ey - 1.6 * s, ex + 2 * s, ey + 2.4 * s], 200, 340, fill=INK + (255,), width=max(1, int(1.2 * s)))
        elif eyes == "wink":
            ex = fx - 3.4 * s
            d.arc([ex - 2 * s, ey - 1.6 * s, ex + 2 * s, ey + 2.4 * s], 200, 340, fill=INK + (255,), width=max(1, int(1.2 * s)))
            ex = fx + 3.4 * s
            d.line([ex - 2 * s, ey + 0.6 * s, ex + 2 * s, ey + 0.6 * s], fill=INK + (255,), width=max(1, int(1.2 * s)))
        elif eyes == "dot":
            for ex in (fx - 3.2 * s, fx + 3.2 * s):
                d.ellipse([ex - 1.1 * s, ey - 1.4 * s, ex + 1.1 * s, ey + 1.4 * s], fill=INK + (255,))
        for ex in (fx - 5.4 * s, fx + 5.4 * s):
            d.ellipse([ex - 1.8 * s, ey + 2.4 * s, ex + 1.8 * s, ey + 3.8 * s], fill=BLUSH + (150,))
        d.arc([fx - 1.6 * s, ey + 2.2 * s, fx + 1.6 * s, ey + 4.6 * s], 20, 160, fill=INK + (255,), width=max(1, int(1.0 * s)))
    if hat:
        hx = cx + (look * 1.5 * s if face != "back" else 0)
        d.rectangle([hx - 4.6 * s, top - 7 * s, hx + 4.6 * s, top + 0.6 * s], fill=HAT + (235,))
        d.rectangle([hx - 4.6 * s, top - 1.6 * s, hx + 4.6 * s, top + 0.0 * s], fill=VIOLET + (235,))
        d.rounded_rectangle([hx - 7.4 * s, top - 0.2 * s, hx + 7.4 * s, top + 1.6 * s], radius=0.8 * s, fill=HAT + (235,))
    if flower:
        fx = cx + (5.5 * s if face != "back" else -5.5 * s)
        fy = top + 2.5 * s
        for a in range(5):
            t = a * 2 * math.pi / 5
            px, py = fx + 1.8 * s * math.cos(t), fy + 1.8 * s * math.sin(t)
            d.ellipse([px - 1.5 * s, py - 1.5 * s, px + 1.5 * s, py + 1.5 * s], fill=VIOLET + (240,))
        d.ellipse([fx - 1 * s, fy - 1 * s, fx + 1 * s, fy + 1 * s], fill=GOLD + (255,))
    return hy


def sparkle(d, x, y, r, a=230, col=(255, 248, 210)):
    d.polygon([(x, y - r), (x + r * 0.3, y - r * 0.3), (x + r, y), (x + r * 0.3, y + r * 0.3),
               (x, y + r), (x - r * 0.3, y + r * 0.3), (x - r, y), (x - r * 0.3, y - r * 0.3)], fill=col + (a,))


# --------------------------------------------------------------- waltzing couple
def waltz(w, h, k, n=8):
    """A friendly ghost couple turning one full waltz circle over n frames: the gentleman in a
    little top hat, the lady with a violet flower and a swishing hem. Hands joined, rising and
    falling on the beat, a few sparkles trailing behind."""
    im = _canvas(w, h)
    d = ImageDraw.Draw(im)
    W, H = w * SS, h * SS
    th = 2 * math.pi * k / n
    R = W * 0.22
    base_s = W / 60
    bob = -1.6 * base_s * math.sin(2 * th) - 1.2 * base_s
    people = []
    for who, ph in (("lead", 0.0), ("lady", math.pi)):
        a = th + ph
        x = W / 2 + R * math.cos(a) + 0.55 * R * math.sin(a) * (1 if who == 'lead' else 1)
        depth = math.sin(a)                         # +1 = far side
        s = base_s * (1.0 - 0.10 * depth)
        people.append((depth, who, x, s, a))
    people.sort(key=lambda p: -p[0])                # far first
    hands = []
    for depth, who, x, s, a in people:
        top = H * 0.40 + bob + depth * 2.2 * s
        if depth > 0.35:
            face = "front"
        elif depth < -0.35:
            face = "back"
        else:
            face = "front"
        look = -math.cos(a) * 0.8                   # turn the face toward the partner
        hem = 0.85 if who == "lead" else 1.1
        sway = (-math.sin(th) * 4 * s) if who == "lady" else 0
        alpha = 165 if depth > 0 else 190
        ghost(d, x, top, s, alpha=alpha, face=face, look=look, hat=(who == "lead"),
              flower=(who == "lady"), hem=hem, sway=sway, height=30 * s)
        hands.append((x, top + 15 * s, s, depth))
    # joined arms: two soft strokes meeting between the dancers
    (x1, y1, s1, d1), (x2, y2, s2, d2) = hands
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2 - 3 * base_s
    for (x, y, s, dp) in hands:
        d.line([(x, y), (mx, my)], fill=BODY + (215,), width=int(2.6 * s))
    d.ellipse([mx - 2.2 * base_s, my - 2.2 * base_s, mx + 2.2 * base_s, my + 2.2 * base_s], fill=RIM + (240,))
    # the lady's other hand rests on the gentleman's shoulder: a short arc from her toward him
    lx, ly = (x1, y1) if True else (x2, y2)
    # sparkle trail, rotating opposite the couple
    for j in range(5):
        a = -th * 0.5 + j * 2 * math.pi / 5
        sx = W / 2 + W * 0.40 * math.cos(a)
        sy = H * 0.93 + H * 0.03 * math.sin(a) - (j % 2) * H * 0.03
        on = (k + j) % 3 != 0
        sparkle(d, sx, sy, (2.6 if on else 1.4) * base_s, a=230 if on else 120)
    return _finish(im, w, h, glow=0.55)


# --------------------------------------------------------------- pianist (seen from behind, peeking back)
def pianist(w, h, k, n=8):
    im = _canvas(w, h)
    d = ImageDraw.Draw(im)
    W, H = w * SS, h * SS
    s = W / 34
    sway = 2.2 * s * math.sin(2 * math.pi * k / n)
    top = H * 0.16 + 0.8 * s * abs(math.sin(4 * math.pi * k / n))
    cx = W / 2 + sway * 0.4
    # arms reaching forward to the keys (drawn first, behind the body), bouncing alternately
    for side, ph in ((-1, 0.0), (1, 0.5)):
        lift = 2.2 * s * max(0.0, math.sin(2 * math.pi * (k / n * 2 + ph)))
        x0, y0 = cx + side * 8 * s, top + 15 * s
        x1, y1 = cx + side * 12 * s, top + 22 * s - lift
        d.line([(x0, y0), (x1, y1)], fill=BODY + (190,), width=int(3 * s))
        d.ellipse([x1 - 2 * s, y1 - 2 * s, x1 + 2 * s, y1 + 2 * s], fill=RIM + (220,))
    ghost(d, cx, top, s, alpha=185, face="over", look=0.7 * math.copysign(1, math.sin(2 * math.pi * k / n) + 0.3),
          height=24 * s, hem=1.15, sway=sway)
    # a tiny bow tie peeking at the neck (from behind: just the knot tails)
    return _finish(im, w, h, glow=0.5)


def notes(w, h, k, n=8):
    """Music notes drifting up and fading."""
    im = _canvas(w, h)
    d = ImageDraw.Draw(im)
    W, H = w * SS, h * SS
    s = W / 20
    for j in range(3):
        u = ((k / n) + j / 3) % 1
        x = W * (0.25 + 0.25 * j) + 2 * s * math.sin(2 * math.pi * u + j)
        y = H * (0.92 - 0.8 * u)
        a = int(255 * (1 - u) ** 0.7)
        col = (GOLD if j != 1 else (200, 225, 255))
        d.ellipse([x - 2.2 * s, y - 1.6 * s, x + 2.2 * s, y + 1.6 * s], fill=col + (a,))
        d.line([(x + 2 * s, y), (x + 2 * s, y - 7 * s)], fill=col + (a,), width=int(1.2 * s))
        if j == 0:
            d.line([(x + 2 * s, y - 7 * s), (x + 5 * s, y - 5 * s)], fill=col + (a,), width=int(1.2 * s))
    return _finish(im, w, h, glow=0.3)


# --------------------------------------------------------------- portrait
def portrait(w, h, k, n=8):
    """An original painted portrait: a gracious ghost lady with a lace collar, pearls and a teacup.
    Candlelight flickers across the varnish."""
    im = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 255))
    d = ImageDraw.Draw(im)
    W, H = w * SS, h * SS
    for y in range(H):                                     # deep violet painted ground
        t = y / H
        c = (int(52 + 20 * t), int(36 + 12 * t), int(78 + 18 * t), 255)
        d.line([(0, y), (W, y)], fill=c)
    flick = 0.5 + 0.5 * math.sin(2 * math.pi * k / n * 2)
    d.ellipse([W * 0.12, H * 0.08, W * 0.88, H * 0.66], fill=(120, 96, 150, int(70 + 30 * flick)))
    s = W / 44
    cx, top = W / 2, H * 0.20
    ghost(d, cx, top, s, alpha=215, face="front", height=40 * s, hem=1.35,
          eyes="happy")
    # lace collar + pearls
    cy = top + 20 * s
    for i in range(7):
        x = cx - 6 * s + i * 2 * s
        d.ellipse([x - 1.4 * s, cy - 1.1 * s, x + 1.4 * s, cy + 1.6 * s], fill=(255, 250, 240, 255))
    for i in range(6):
        x = cx - 5 * s + i * 2 * s
        d.ellipse([x - 0.7 * s, cy + 2.1 * s, x + 0.7 * s, cy + 3.5 * s], fill=(236, 232, 255, 255))
    # teacup held in a little hand
    tx, ty = cx + 5 * s, top + 30 * s
    d.ellipse([tx - 2.5 * s, ty - 1.5 * s, tx + 2.5 * s, ty + 1.5 * s], fill=RIM + (230,))
    d.rounded_rectangle([tx - 3 * s, ty - 4 * s, tx + 3 * s, ty], radius=1.2 * s, fill=(255, 248, 236, 255))
    d.rectangle([tx - 3 * s, ty - 3 * s, tx + 3 * s, ty - 2.2 * s], fill=VIOLET + (255,))
    d.arc([tx + 2 * s, ty - 3.6 * s, tx + 5 * s, ty - 0.8 * s], 270, 90, fill=(255, 248, 236, 255), width=int(0.9 * s))
    for j in range(2):
        u = ((k / n) + j / 2) % 1
        d.arc([tx - 1.2 * s + j * s, ty - 8 * s - 2 * s * u, tx + 0.8 * s + j * s, ty - 5 * s - 2 * s * u], 90, 270,
              fill=(240, 240, 255, int(160 * (1 - u))), width=int(0.8 * s))
    # varnish glint
    d.line([(W * 0.08, H * 0.12), (W * 0.2, H * 0.04)], fill=(255, 255, 255, int(40 + 50 * flick)), width=int(1.2 * s))
    return np.array(im.resize((w, h), Image.BOX), np.uint8)


# --------------------------------------------------------------- small ghosts
def lantern_ghost(w, h, k, n=8):
    im = _canvas(w, h)
    d = ImageDraw.Draw(im)
    W, H = w * SS, h * SS
    s = W / 30
    top = H * 0.16 + 2.2 * s * math.sin(2 * math.pi * k / n)
    ghost(d, W / 2, top, s, alpha=210, face="front", height=24 * s, hem=1.0,
          sway=1.5 * s * math.sin(2 * math.pi * k / n + 1), eyes="happy" if k % 8 != 3 else "dot")
    return _finish(im, w, h, glow=0.7)


def wisp_face(w, h, k, n=8):
    """Face for the 3D wisp pet (north face): calm dot eyes that blink once per loop, blush, tiny smile."""
    im = _canvas(w, h)
    d = ImageDraw.Draw(im)
    W, H = w * SS, h * SS
    s = W / 20
    fx, ey = W / 2, H * 0.45
    if k == 6:
        for ex in (fx - 3.4 * s, fx + 3.4 * s):
            d.arc([ex - 1.8 * s, ey - 1.6 * s, ex + 1.8 * s, ey + 1.8 * s], 20, 160, fill=INK + (255,), width=int(1.0 * s))
    else:
        for ex in (fx - 3.4 * s, fx + 3.4 * s):
            d.ellipse([ex - 1.2 * s, ey - 1.6 * s, ex + 1.2 * s, ey + 1.6 * s], fill=INK + (255,))
            d.ellipse([ex - 0.6 * s, ey - 1.2 * s, ex + 0.1 * s, ey - 0.4 * s], fill=(255, 255, 255, 255))
    for ex in (fx - 5.8 * s, fx + 5.8 * s):
        d.ellipse([ex - 1.8 * s, ey + 2.2 * s, ex + 1.8 * s, ey + 3.6 * s], fill=BLUSH + (170,))
    d.arc([fx - 1.6 * s, ey + 1.6 * s, fx + 1.6 * s, ey + 4.2 * s], 20, 160, fill=INK + (255,), width=int(0.9 * s))
    return np.array(im.resize((w, h), Image.BOX), np.uint8)


def wisp_tail(w, h, k, n=8):
    im = _canvas(w, h)
    d = ImageDraw.Draw(im)
    W, H = w * SS, h * SS
    pts = []
    for i in range(24):
        t = i / 23
        x = W / 2 + W * 0.28 * math.sin(2 * math.pi * (t * 0.8 - k / n)) * t
        y = H * 0.05 + H * 0.9 * t
        pts.append((x, y))
    for i in range(len(pts) - 1):
        wdt = int(W * 0.34 * (1 - i / len(pts)) + 2)
        d.line([pts[i], pts[i + 1]], fill=BODY + (170,), width=wdt)
    return _finish(im, w, h, glow=0.4)


def wisp_ring(w, h, k, n=8):
    """Flat ring of drifting spectral sparkles (seen from above)."""
    im = _canvas(w, h)
    d = ImageDraw.Draw(im)
    W, H = w * SS, h * SS
    for j in range(8):
        a = 2 * math.pi * (j / 8 + k / n / 2)
        r = W * 0.40
        x, y = W / 2 + r * math.cos(a), H / 2 + r * math.sin(a)
        on = (j + k) % 2 == 0
        sparkle(d, x, y, W * (0.06 if on else 0.035), a=220 if on else 120, col=(220, 236, 255))
    return _finish(im, w, h, glow=0.4)


def ghost_hand(w, h, k, n=8):
    """A friendly translucent glove-hand holding the candelabra stem from below."""
    im = _canvas(w, h)
    d = ImageDraw.Draw(im)
    W, H = w * SS, h * SS
    s = W / 16
    off = 0.6 * s * math.sin(2 * math.pi * k / n)
    d.rounded_rectangle([W * 0.18, H * 0.30 + off, W * 0.82, H * 0.62 + off], radius=3 * s, fill=BODY + (190,))
    for i in range(4):
        x = W * 0.24 + i * W * 0.15
        d.rounded_rectangle([x, H * 0.18 + off, x + W * 0.12, H * 0.42 + off], radius=1.4 * s, fill=BODY + (190,))
    # cuff fading into mist
    for i in range(6):
        d.rounded_rectangle([W * 0.3, H * 0.6 + i * H * 0.06 + off, W * 0.7, H * 0.68 + i * H * 0.06 + off],
                            radius=2 * s, fill=BODY + (max(0, 170 - i * 28),))
    return _finish(im, w, h, glow=0.4)
