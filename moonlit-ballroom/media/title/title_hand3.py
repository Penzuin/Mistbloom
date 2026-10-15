"""Moonlit Ballroom title slide, hand-drawn storybook style.
Drawn at 2x with wobbly ink lines, watercolour washes and paper grain, then scaled to 1920x1080."""
import math, os, random, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops

S = 2
W, H = 1920 * S, 1080 * S
HERE = os.path.dirname(os.path.abspath(__file__))
FD = "/home/claude/ghostball/fonts/"
INK = (40, 28, 62)
rng = np.random.default_rng(21)
R = random.Random(21)

# ------------------------------------------------------------------ brush helpers
def nz(t, seed, oct=3):
    r = random.Random(seed); v = 0
    for k in range(oct):
        f = 1.3 * 2 ** k; v += math.sin(t * f + r.uniform(0, 6.28)) / 2 ** k
    return v

def wobble(pts, amp=3.0, seed=0):
    amp *= random.Random(seed * 7 + 1).uniform(0.7, 1.6)       # every stroke has its own unsteadiness
    out = []
    n = len(pts)
    for i, (x, y) in enumerate(pts):
        a, b = pts[max(0, i - 1)], pts[min(n - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]; L = math.hypot(dx, dy) or 1
        o = amp * S * nz(i * 0.22, seed)
        out.append((x - dy / L * o, y + dx / L * o))
    return out

def ink(d, pts, w=3.0, col=INK, alpha=235, seed=0, closed=False):
    """Pressure-varying ink stroke: width swells and thins along the line."""
    if closed:                                                 # hand-closed shapes overshoot their start a little
        k = max(2, len(pts) // 14)
        pts = pts + pts[:k]
        closed = False
    dense = []
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        n = max(1, int(math.hypot(x1 - x0, y1 - y0) / (1.5 * S)))
        dense += [(x0 + (x1 - x0) * k / n, y0 + (y1 - y0) * k / n) for k in range(n)]
    n = len(dense); tp = max(6, n // 8)
    for i, (x, y) in enumerate(dense):
        taper = 1.0 if closed else max(0.25, min(1.0, i / tp, (n - 1 - i) / tp))
        r = S * w * taper * max(0.75, 0.9 + 0.15 * nz(i * 0.02, seed + 7, 2)) / 2
        d.ellipse([x - r, y - r, x + r, y + r], fill=col + (alpha,))

def bez(p0, p1, p2, p3, n=30):
    out = []
    for i in range(n + 1):
        t = i / n; u = 1 - t
        out.append((u**3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t**3 * p3[0],
                    u**3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t**3 * p3[1]))
    return out

TEX = None
def wash(base, pts, col, alpha=255, grad=None, edge=0.25, blur=1.2, tw=0.05):
    """Watercolour fill: textured, slightly darker at the edges, optional vertical fade."""
    global TEX
    m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).polygon(pts, fill=255)
    m = m.filter(ImageFilter.GaussianBlur(blur * S))
    bb = m.getbbox()
    if not bb: return m
    x0, y0, x1, y1 = bb
    mm = np.asarray(m.crop(bb), float) / 255
    tex = np.clip(TEX[y0:y1, x0:x1], -1.2, 1.2)
    a = mm * (1 - tw + tw * tex)
    if grad:
        yy = np.linspace(grad[0], grad[1], y1 - y0)[:, None]; a = a * yy
    inner = np.asarray(m.crop(bb).filter(ImageFilter.GaussianBlur(9 * S)), float) / 255
    rim = np.clip(mm - inner, 0, 1)
    c = np.array(col, float)[None, None, :] * (1 - edge * rim[..., None])
    layer = np.dstack([np.clip(c, 0, 255), np.clip(a * alpha, 0, 255)]).astype(np.uint8)
    base.alpha_composite(Image.fromarray(layer, "RGBA"), (x0, y0))
    return m

def glow(base, cx, cy, r, col, a):
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(g).ellipse([cx - r, cy - r, cx + r, cy + r], fill=col + (a,))
    base.alpha_composite(g.filter(ImageFilter.GaussianBlur(r * 0.5)))

def ellipse_pts(cx, cy, rx, ry, n=60, a0=0, a1=2 * math.pi):
    return [(cx + rx * math.cos(a0 + (a1 - a0) * i / n), cy + ry * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]

# ------------------------------------------------------------------ textures
def paper():
    g = rng.normal(0, 1, (H // 2, W // 2))
    g = np.asarray(Image.fromarray(((g * 18) + 128).clip(0, 255).astype(np.uint8)).resize((W, H), Image.BILINEAR), float)
    big = rng.normal(0, 1, (H // 64, W // 64))
    big = np.asarray(Image.fromarray(((big * 40) + 128).clip(0, 255).astype(np.uint8)).resize((W, H), Image.BICUBIC), float)
    return (g - 128) / 128 * 0.35 + (big - 128) / 128 * 0.35

# ------------------------------------------------------------------ scene pieces
def background(im):
    """Flat painted wall lit from the window (right) and a warm sconce (left); hand-ruled wainscot."""
    d = ImageDraw.Draw(im)
    yy, xx = np.mgrid[0:H, 0:W].astype(float)
    base = np.array([52, 38, 86.])
    cool = np.exp(-(((xx - 1180 * S) / (700 * S)) ** 2 + ((yy - 520 * S) / (520 * S)) ** 2))
    warm = np.exp(-(((xx - 90 * S) / (330 * S)) ** 2 + ((yy - 540 * S) / (300 * S)) ** 2))
    arr = base[None, None, :] * (0.78 + 0.32 * cool[..., None]) + np.array([60, 34, 0.])[None, None, :] * warm[..., None] * 0.55
    arr += TEX[..., None] * 3
    im.paste(Image.fromarray(arr.clip(0, 255).astype(np.uint8)).convert("RGBA"))
    # wainscot rail and panels below it
    rail = 600 * S
    wash(im, [(0, rail), (W, rail), (W, 780 * S), (0, 780 * S)], (40, 28, 66), 150, edge=0.05, blur=2)
    ink(d, wobble([(0, rail), (W, rail)], 0.6, 31), 2.6, seed=31)
    x = 30 * S; k = 0
    while x < W:
        pw = (150 + 12 * (k % 3)) * S
        p = [(x, rail + 30 * S), (x + pw, rail + 30 * S), (x + pw, 750 * S), (x, 750 * S)]
        ink(d, wobble(p, 0.5, 100 + k), 1.4, alpha=110, seed=100 + k, closed=True)
        x += pw + 34 * S; k += 1

def sconce(im, x, y):
    """Brass wall sconce: backplate screwed to the wall, swan-neck arm, drip cup, candle, flame."""
    d = ImageDraw.Draw(im)
    cxp, cup_y = x + 52 * S, y - 26 * S
    glow(im, cxp, cup_y - 80 * S, 170 * S, (255, 196, 120), 70)
    plate = bez((x + 2 * S, y - 48 * S), (x + 27 * S, y - 38 * S), (x + 24 * S, y + 42 * S), (x - 1 * S, y + 45 * S), 20)
    plate += bez((x - 1 * S, y + 45 * S), (x - 25 * S, y + 36 * S), (x - 24 * S, y - 42 * S), (x + 2 * S, y - 48 * S), 20)
    wash(im, plate, (196, 150, 72), 255, edge=0.45); ink(d, wobble(plate, 0.3, 801), 2.4, seed=801, closed=True)
    for yy in (y - 30 * S, y + 30 * S):
        sc = ellipse_pts(x, yy, 3 * S, 3 * S, 10); wash(im, sc, (120, 90, 40), 255, edge=0)
    arm_top = bez((x + 6 * S, y + 10 * S), (x + 40 * S, y + 22 * S), (x + 56 * S, y + 4 * S), (cxp, cup_y + 6 * S), 24)
    ink(d, wobble(arm_top, 0.6, 806), 7, col=(130, 94, 42)); ink(d, [(px_ - 1.5 * S, py_ - 1.5 * S) for px_, py_ in arm_top], 3.0, col=(226, 184, 100))
    cup = ellipse_pts(cxp, cup_y, 22 * S, 7 * S)
    wash(im, [(cxp - 22 * S, cup_y), (cxp + 22 * S, cup_y), (cxp + 12 * S, cup_y + 12 * S), (cxp - 12 * S, cup_y + 12 * S)], (196, 150, 72), 255, edge=0.4)
    c = [(cxp - 9 * S, cup_y - 52 * S), (cxp + 9 * S, cup_y - 52 * S), (cxp + 9 * S, cup_y - 2 * S), (cxp - 9 * S, cup_y - 2 * S)]
    c[0] = (c[0][0] + 1 * S, c[0][1] + 5 * S)                                   # candle burned down unevenly
    wash(im, c, (246, 236, 214), 255, edge=0.3); ink(d, wobble(c, 0.5, 802), 1.8, seed=802, closed=True)
    for (dx_, L) in ((-9, 16), (5, 26)):                                         # wax drips
        drip = bez((cxp + dx_ * S, cup_y - 46 * S), (cxp + (dx_ - 2) * S, cup_y - (46 - L * 0.6) * S), (cxp + (dx_ + 3) * S, cup_y - (46 - L) * S), (cxp + (dx_ + 4) * S, cup_y - (46 - L) * S), 10)
        drip += [(p[0] + 4 * S, p[1]) for p in drip[::-1]]
        wash(im, drip, (252, 244, 226), 255, edge=0.2, tw=0); ink(d, wobble(drip, 0.2, 805 + dx_), 1.3, alpha=200)
    wash(im, cup, (214, 166, 84), 255, edge=0.45); ink(d, wobble(cup, 0.2, 803), 2.0, seed=803, closed=True)
    ink(d, [(cxp, cup_y - 52 * S), (cxp, cup_y - 60 * S)], 1.4)
    glow(im, cxp, cup_y - 76 * S, 26 * S, (255, 220, 150), 160)
    fl = bez((cxp, cup_y - 54 * S), (cxp - 13 * S, cup_y - 66 * S), (cxp - 4 * S, cup_y - 86 * S), (cxp + 7 * S, cup_y - 99 * S), 12)
    fl += bez((cxp + 7 * S, cup_y - 99 * S), (cxp + 4 * S, cup_y - 84 * S), (cxp + 13 * S, cup_y - 70 * S), (cxp, cup_y - 54 * S), 12)
    wash(im, fl, (255, 214, 130), 255, edge=0.1, blur=0.6)

def window(im):
    d = ImageDraw.Draw(im)
    cx, hw, spring, bot = 1180 * S, 250 * S, 480 * S, 760 * S
    Rr = hw * 1.35; cl = cx - hw + Rr
    a_ap = math.acos((cx - cl) / Rr)
    left = [(cl + Rr * math.cos(t), spring - Rr * math.sin(t)) for t in np.linspace(math.pi, a_ap, 40)]
    right = [(2 * cx - x, y) for x, y in reversed(left)]
    shape = [(cx - hw, bot)] + left + right + [(cx + hw, bot)]
    # moonlight beam onto the floor
    beam = [(cx - hw * 0.9, bot), (cx + hw * 0.9, bot), (cx + hw * 1.9, H), (cx - hw * 1.9, H)]
    b = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(b).polygon(beam, fill=(214, 200, 255, 40))
    im.alpha_composite(b.filter(ImageFilter.GaussianBlur(40 * S)))
    # night sky inside the window
    wash(im, shape, (30, 34, 82), 255, edge=0.2, blur=0.8)
    sky = Image.new("RGBA", (W, H), (0, 0, 0, 0)); sd = ImageDraw.Draw(sky)
    for _ in range(70):
        x, yy = R.uniform(cx - hw, cx + hw), R.uniform(spring - Rr * 0.9, bot)
        r = R.choice([1.2, 1.8, 2.5]) * S; sd.ellipse([x - r, yy - r, x + r, yy + r], fill=(240, 236, 255, R.randrange(120, 240)))
    mask = Image.new("L", (W, H), 0); ImageDraw.Draw(mask).polygon(shape, fill=255)
    glow(sky, cx + 110 * S, 345 * S, 150 * S, (255, 240, 205), 90)
    wash(sky, ellipse_pts(cx + 110 * S, 345 * S, 70 * S, 70 * S), (252, 242, 214), 255, edge=0.12)
    sd = ImageDraw.Draw(sky)
    for (dx, dy, r) in ((-30, -20, 16), (25, 30, 11), (40, -35, 8)):
        wash(sky, ellipse_pts(cx + (110 + dx * 0.8) * S, (345 + dy * 0.8) * S, r * S, r * S), (232, 218, 186), 200, edge=0.3)
    ink(sd, wobble(ellipse_pts(cx + 110 * S, 345 * S, 70 * S, 70 * S), 0.8, 5), 1.6, alpha=110, seed=5)
    sky.putalpha(ImageChops.multiply(sky.split()[3], mask))
    im.alpha_composite(sky)
    # mullions and frame
    ink(d, wobble([(cx + 2 * S, spring - Rr * 0.97 + 32 * S), (cx + 1 * S, bot)], 0.8, 3), 5, alpha=255)
    ink(d, wobble([(cx - hw + 2 * S, 518 * S), (cx + hw - 2 * S, 521 * S)], 0.8, 4), 4, alpha=255)
    ink(d, wobble([(cx - hw + 3 * S, 650 * S), (cx + hw - 3 * S, 652 * S)], 0.7, 5), 2.6, alpha=200)
    ink(d, wobble(shape, 0.8, 1), 6.5, alpha=255, seed=1)
    inner = [(cx + (x - cx) * 0.93, y + 22 * S) for x, y in shape]
    ink(d, wobble(inner, 1.0, 2), 2.2, col=(242, 201, 125), alpha=170, seed=2)
    # sill
    sill = [(cx - hw - 30 * S, bot), (cx + hw + 30 * S, bot), (cx + hw + 22 * S, bot + 26 * S), (cx - hw - 22 * S, bot + 26 * S)]
    wash(im, sill, (96, 74, 128), 255, edge=0.4)
    ink(d, wobble(sill, 1, 9), 3, seed=9, closed=True)

def floor(im):
    d = ImageDraw.Draw(im)
    hz, vx = 780 * S, 1180 * S
    wash(im, [(0, hz), (W, hz), (W, H), (0, H)], (58, 40, 86), 255, edge=0.1)
    rows = [hz]
    y = hz; step = 26 * S
    while y < H:
        y += step; rows.append(y); step *= 1.32
    ncols = 14
    for r in range(len(rows) - 1):
        y0, y1 = rows[r], rows[r + 1]
        for c in range(-ncols, ncols):
            def X(c, y):
                return vx + (c * 170 * S) * (y - (hz - 420 * S)) / (H - (hz - 420 * S))
            if (r + c) % 2: continue
            q = [(X(c, y0), y0), (X(c + 1, y0), y0), (X(c + 1, y1), y1), (X(c, y1), y1)]
            wash(im, q, (150, 132, 186), 70 + 12 * min(r, 5), edge=0.2, blur=1.5)
    for r, yy in enumerate(rows[1:]):
        ink(d, wobble([(0, yy), (W, yy)], 0.8, 40 + r), 1.2, alpha=60, seed=40 + r)
    # skirting board
    sk = [(0, hz - 14 * S), (W, hz - 14 * S), (W, hz + 4 * S), (0, hz + 4 * S)]
    wash(im, sk, (34, 24, 52), 255, edge=0.2)
    ink(d, wobble([(0, hz - 14 * S), (W, hz - 14 * S)], 0.8, 77), 2.4, seed=77)

def curtain(im, side):
    d = ImageDraw.Draw(im)
    sgn = 1 if side == "L" else -1
    x0 = 0 if side == "L" else W
    edge_top, edge_tie, bottom = 330 * S, 560 * S, H + 20 * S
    # outer shape: falls straight, pinched at the tie-back, flares to the floor
    inner = bez((x0 + sgn * 330 * S, -10), (x0 + sgn * 300 * S, 250 * S), (x0 + sgn * 120 * S, 470 * S), (x0 + sgn * 150 * S, edge_tie), 30)
    inner += bez((x0 + sgn * 150 * S, edge_tie), (x0 + sgn * 190 * S, 760 * S), (x0 + sgn * 330 * S, 900 * S), (x0 + sgn * 300 * S, bottom), 30)
    pts = [(x0 - sgn * 20 * S, -20)] + inner + [(x0 - sgn * 20 * S, bottom)]
    wash(im, pts, (98, 44, 92), 255, edge=0.45)
    # folds
    for k in range(5):
        f = 0.15 + 0.17 * k
        fold = [(x0 + sgn * (330 * S * f), -10), (x0 + sgn * 300 * S * f, 300 * S), (x0 + sgn * 140 * S * f + sgn * 10 * S, edge_tie),
                (x0 + sgn * 300 * S * f + sgn * 20 * S, 900 * S), (x0 + sgn * 290 * S * f, bottom)]
        fp = bez(fold[0], fold[1], fold[1], fold[2], 20) + bez(fold[2], fold[3], fold[3], fold[4], 20)[1:]
        shade = [(x + sgn * 22 * S, y) for x, y in fp[::-1]]
        wash(im, fp + shade, (70, 28, 66), 150, edge=0.2, blur=6)
        ink(d, wobble(fp, 1.2, 60 + k), 1.6, alpha=120, seed=60 + k)
    ink(d, wobble(inner, 1.5, 70), 4.5, seed=70)
    # gold tie-back: a cord band wrapped round the pinched curtain, knot and tassel at the inner edge
    tx, ty = x0 + sgn * 150 * S, edge_tie
    far = x0 - sgn * 30 * S
    top = bez((tx, ty - 12 * S), (tx + (far - tx) * 0.35, ty + 2 * S), (tx + (far - tx) * 0.7, ty + 4 * S), (far, ty - 6 * S), 24)
    botm = bez((far, ty + 18 * S), (tx + (far - tx) * 0.7, ty + 28 * S), (tx + (far - tx) * 0.35, ty + 26 * S), (tx, ty + 12 * S), 24)
    band = top + botm
    wash(im, band, (226, 178, 96), 255, edge=0.4)
    ink(d, wobble(top, 0.4, 71), 2.4, seed=71); ink(d, wobble(botm, 0.4, 73), 2.4, seed=73)
    for k in range(1, 8):                                     # twisted-cord ticks
        u = k / 8; x1 = tx + (far - tx) * u
        ink(d, [(x1 - 6 * S, ty - 6 * S + 10 * S * u), (x1 + 6 * S, ty + 18 * S + 6 * S * u)], 1.2, alpha=130)
    for k, (ox, oy, ang) in enumerate(((-9, -4, -0.6), (9, -2, 0.5))):
        lob = [(tx + ox * S + 15 * S * math.cos(t) * math.cos(ang) - 9 * S * math.sin(t) * math.sin(ang),
                ty + oy * S + 15 * S * math.cos(t) * math.sin(ang) + 9 * S * math.sin(t) * math.cos(ang)) for t in np.linspace(0, 2 * math.pi, 22)]
        wash(im, lob, (220, 170, 88), 255, edge=0.45, tw=0); ink(d, wobble(lob, 0.4, 74 + k), 2.0, seed=74 + k, closed=True)
    knot = ellipse_pts(tx, ty + 2 * S, 8 * S, 9 * S, 16)
    wash(im, knot, (200, 150, 70), 255, edge=0.4, tw=0); ink(d, wobble(knot, 0.3, 77), 1.8, seed=77, closed=True)
    cord = [(tx, ty + 16 * S), (tx + sgn * 3 * S, ty + 46 * S)]
    ink(d, cord, 3.0, col=(170, 128, 60))
    cap = ellipse_pts(tx + sgn * 3 * S, ty + 58 * S, 13 * S, 14 * S)
    wash(im, cap, (226, 178, 96), 255, edge=0.45); ink(d, wobble(cap, 0.3, 75), 2.0, seed=75, closed=True)
    cx_ = tx + sgn * 3 * S
    skirt = [(cx_ - 11 * S, ty + 66 * S), (cx_ + 11 * S, ty + 66 * S), (cx_ + 22 * S, ty + 140 * S), (cx_ - 22 * S, ty + 140 * S)]
    wash(im, skirt, (226, 178, 96), 255, edge=0.4)
    for k in range(7):
        u = k / 6
        ink(d, [(cx_ - 9 * S + 18 * S * u, ty + 70 * S), (cx_ - 19 * S + 38 * S * u, ty + 136 * S)], 1.1, alpha=150)
    ink(d, wobble(skirt, 0.3, 76), 2.2, seed=76, closed=True)

def chandelier(im, cx, top, s=1.0):
    d = ImageDraw.Draw(im)
    cy = top + 150 * S * s
    ink(d, wobble([(cx, 0), (cx, cy - 30 * S * s)], 0.6, 80), 2.4, col=(120, 110, 140), seed=80)
    glow(im, cx, cy - 40 * S * s, 190 * S * s, (255, 214, 140), 55)
    arm = ellipse_pts(cx, cy, 120 * S * s, 26 * S * s)
    ink(d, wobble(arm, 0.6, 81), 4, col=(196, 150, 70), seed=81)
    wash(im, ellipse_pts(cx, cy + 6 * S * s, 26 * S * s, 34 * S * s), (214, 168, 84), 255, edge=0.45)
    for k, a in enumerate(np.linspace(0, math.pi, 5)):
        x = cx + 120 * S * s * math.cos(a); y = cy + 26 * S * s * math.sin(a) - 6 * S * s
        c = [(x - 9 * S * s, y - 50 * S * s), (x + 9 * S * s, y - 50 * S * s), (x + 9 * S * s, y), (x - 9 * S * s, y)]
        wash(im, c, (246, 236, 214), 255, edge=0.3)
        ink(d, wobble(c, 0.4, 90 + k), 1.6, seed=90 + k, closed=True)
        glow(im, x, y - 66 * S * s, 26 * S * s, (180, 220, 255), 120)
        fl = bez((x, y - 50 * S * s), (x - 12 * S * s, y - 64 * S * s), (x - 2 * S * s, y - 78 * S * s), (x, y - 88 * S * s), 12)
        fl += bez((x, y - 88 * S * s), (x + 4 * S * s, y - 76 * S * s), (x + 12 * S * s, y - 64 * S * s), (x, y - 50 * S * s), 12)
        wash(im, fl, (170, 214, 255), 255, edge=0.1, blur=0.6)
    for k, a in enumerate(np.linspace(0.3, math.pi - 0.3, 4)):             # little crystal drops
        x = cx + 110 * S * s * math.cos(a); y = cy + 24 * S * s * math.sin(a) + 30 * S * s
        ink(d, [(x, y - 26 * S * s), (x, y - 6 * S * s)], 1, alpha=120)
        wash(im, ellipse_pts(x, y, 6 * S * s, 9 * S * s), (220, 230, 255), 230, edge=0.3)

# ------------------------------------------------------------------ the ghosts
def ghost_outline(cx, top, w, h, lean, sway, lobes=3, hem_amp=0.06):
    """Rounded head, sides that ease outward, a soft wavy hem. lean shears the body sideways, sway curls the hem."""
    r = w / 2; hy = top + r; bot = top + h
    def shear(x, y):
        t = (y - top) / h
        return (x + lean * (bot - y) * 0.35 + sway * t ** 3, y)
    pts = []
    pts += [(cx + r * math.cos(a), hy - r * math.sin(a)) for a in np.linspace(math.pi, 0, 40)]           # head, left -> right
    pts += bez((cx + r, hy), (cx + r * 1.02, hy + h * 0.35), (cx + r * 1.12, bot - h * 0.2), (cx + r * 1.16, bot), 25)[1:]
    n = 80
    for i in range(1, n):                                                                              # hem, right -> left
        u = i / n
        x = cx + r * 1.16 - 2 * r * 1.16 * u
        y = bot + h * hem_amp * (0.5 - 0.5 * math.cos(2 * math.pi * lobes * u)) - h * 0.012 * math.sin(math.pi * u)
        pts.append((x, y))
    pts += bez((cx - r * 1.16, bot), (cx - r * 1.12, bot - h * 0.2), (cx - r * 1.02, hy + h * 0.35), (cx - r, hy), 25)[1:]
    return [shear(x, y) for x, y in pts], shear

def ghost(im, cx, top, w, h, lean, sway, seed, who):
    d = ImageDraw.Draw(im)
    pts, shear = ghost_outline(cx, top, w, h, lean, sway)
    # soft shadow on the floor
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse([cx - w * 0.6 + sway * 0.5, top + h * 1.2, cx + w * 0.6 + sway * 0.5, top + h * 1.29], fill=(20, 10, 40, 90))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14 * S)))
    glow(im, cx, top + h * 0.5, w * 0.9, (220, 210, 255), 50)
    m = wash(im, pts, (247, 245, 255), 255, grad=None, edge=0.10, tw=0.0)
    # shade on the side away from the moon, plus a moonlit rim
    off = 22 * S if who == "lady" else 26 * S
    shade = Image.new("L", (W, H), 0); ImageDraw.Draw(shade).polygon([(x + off, y + 6 * S) for x, y in pts], fill=255)
    shade = ImageChops.subtract(m, shade).filter(ImageFilter.GaussianBlur(8 * S))
    lay = Image.new("RGBA", (W, H), (176, 160, 226, 0)); lay.putalpha(shade.point(lambda v: int(v * 0.55)))
    im.alpha_composite(lay)
    rim = Image.new("L", (W, H), 0); ImageDraw.Draw(rim).polygon([(x - 9 * S, y + 7 * S) for x, y in pts], fill=255)
    rim = ImageChops.subtract(m, rim).filter(ImageFilter.GaussianBlur(2 * S))
    lay = Image.new("RGBA", (W, H), (255, 255, 255, 0)); lay.putalpha(rim.point(lambda v: int(v * 0.9)))
    im.alpha_composite(lay)
    ink(d, wobble(pts, 1.1, seed), 4.6, seed=seed, closed=True)
    # face
    fx, fy = shear(cx, top + w * 0.50)
    if who == "lady":
        fx += 12 * S
        # closed, dreamy eyes: two slightly different arcs, lashes only on the outer corners
        eyes = [(fx - w * 0.18, fy + 8 * S, w * 0.072, 0.10), (fx + w * 0.15, fy + 3 * S, w * 0.066, -0.14)]
        for k, (ex, ey, rw, tilt) in enumerate(eyes):
            arc = ellipse_pts(ex, ey, rw, rw * 0.72, 18, math.pi * 1.08 + tilt, math.pi * 1.92 + tilt)
            ink(d, wobble(arc, 0.25, seed + 3 + k), 4.4, seed=seed + 3 + k)
            ox, oy = arc[0] if k == 0 else arc[-1]
            sg = -1 if k == 0 else 1
            ink(d, [(ox, oy), (ox + sg * 9 * S, oy - 6 * S)], 2.0)
            ink(d, [(ox - sg * 3 * S, oy - 4 * S), (ox + sg * 4 * S, oy - 13 * S)], 1.8)
        # small open smile, a touch off-centre
        mx, my = fx - 4 * S, fy + w * 0.13
        sm = bez((mx - 13 * S, my - 2 * S), (mx - 6 * S, my + 12 * S), (mx + 8 * S, my + 11 * S), (mx + 14 * S, my - 4 * S), 14)
        wash(im, sm + [(mx - 13 * S, my - 2 * S)], (190, 96, 120), 255, edge=0.2, tw=0)
        ink(d, wobble(sm + [(mx - 13 * S, my - 2 * S)], 0.2, seed + 6), 2.8, seed=seed + 6)
        blushes = [(fx - w * 0.30, fy + w * 0.12), (fx + w * 0.24, fy + w * 0.08)]
    else:
        fx -= 14 * S
        # open eyes glancing toward her (left), shines in the same corner, one a hair bigger
        for k, (ex, ey, rr) in enumerate(((fx - w * 0.17, fy + 2 * S, 1.0), (fx + w * 0.13, fy + 4 * S, 1.0))):
            e = ellipse_pts(ex, ey, 11 * S * rr, 15 * S * rr, 24)
            wash(im, e, INK, 255, edge=0, blur=0.6, tw=0)
            wash(im, ellipse_pts(ex - 4 * S * rr, ey - 6 * S * rr, 4 * S * rr, 4.5 * S * rr, 12), (255, 255, 255), 255, edge=0, blur=0.4, tw=0)
            wash(im, ellipse_pts(ex + 3 * S * rr, ey + 6 * S * rr, 1.8 * S, 1.8 * S, 8), (255, 255, 255), 220, edge=0, blur=0.3, tw=0)
        # eyebrows: one raised, smitten
        ink(d, wobble(bez((fx - w * 0.24, fy - 22 * S), (fx - w * 0.2, fy - 32 * S), (fx - w * 0.14, fy - 33 * S), (fx - w * 0.10, fy - 28 * S), 10), 0.2, seed + 8), 2.4)
        ink(d, wobble(bez((fx + w * 0.07, fy - 24 * S), (fx + w * 0.11, fy - 30 * S), (fx + w * 0.16, fy - 30 * S), (fx + w * 0.19, fy - 25 * S), 10), 0.2, seed + 9), 2.4)
        # lopsided grin, higher on one side
        mx, my = fx - 2 * S, fy + w * 0.14
        gr = bez((mx - 20 * S, my - 1 * S), (mx - 8 * S, my + 10 * S), (mx + 8 * S, my + 8 * S), (mx + 18 * S, my - 9 * S), 16)
        ink(d, wobble(gr, 0.2, seed + 4), 3.4, seed=seed + 4)
        ink(d, [(mx + 18 * S, my - 9 * S), (mx + 23 * S, my - 12 * S)], 2.2)
        blushes = [(fx - w * 0.31, fy + w * 0.10), (fx + w * 0.25, fy + w * 0.12)]
    # blush: soft patch with three quick pencil hatches, every hatch a different angle
    rr = random.Random(seed)
    for bx, by in blushes:
        wash(im, ellipse_pts(bx, by, w * 0.065, w * 0.036), (244, 150, 178), 150, edge=0, blur=5, tw=0)
        for k in range(3):
            x1 = bx - 12 * S + k * 10 * S + rr.uniform(-2, 2) * S
            ink(d, [(x1, by + 7 * S), (x1 + rr.uniform(5, 9) * S, by - rr.uniform(6, 10) * S)], 1.6, col=(214, 104, 140), alpha=200)
    return shear, fx, fy

def flower(im, x, y, r, seed):
    d = ImageDraw.Draw(im)
    rr = random.Random(seed)
    for k, (a, L) in enumerate(((math.pi * 0.70, 2.5), (math.pi * 1.18, 1.9))):
        tip = (x + r * L * math.cos(a), y + r * L * math.sin(a))
        lf = bez((x, y), (x + r * 1.3 * math.cos(a - 0.5), y + r * 1.3 * math.sin(a - 0.5)), (tip[0], tip[1]), tip, 12)
        lf += bez(tip, (x + r * 1.1 * math.cos(a + 0.45), y + r * 1.1 * math.sin(a + 0.45)), (x, y), (x, y), 12)
        wash(im, lf, (112, 160, 112), 255, edge=0.4, tw=0); ink(d, wobble(lf, 0.3, seed + k), 1.8, seed=seed + k)
        ink(d, [(x, y), ((x + tip[0]) / 2, (y + tip[1]) / 2)], 1.0, alpha=140)
    angs = [-1.75, -0.45, 0.62, 1.95, 3.15]
    for k, a in enumerate(angs):
        pr = r * rr.uniform(0.52, 0.72)
        dist = r * rr.uniform(0.62, 0.82)
        px, py = x + dist * math.cos(a), y + dist * math.sin(a)
        p = [(px + pr * math.cos(t) * (1.15 if k == 2 else 1), py + pr * 0.85 * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 26)]
        col = (176, 136, 228) if k != 3 else (150, 112, 206)              # one petal turned, in shadow
        wash(im, p, col, 255, edge=0.45, tw=0)
        ink(d, wobble(p, 0.4, seed + 10 + k), 1.8, seed=seed + 10 + k, closed=True)
        ink(d, [(x + dist * 0.35 * math.cos(a), y + dist * 0.35 * math.sin(a)), (x + dist * 0.85 * math.cos(a), y + dist * 0.85 * math.sin(a))], 1.0, alpha=110)
    c = ellipse_pts(x + 2 * S, y - 1 * S, r * 0.36, r * 0.31)
    wash(im, c, (246, 204, 118), 255, edge=0.4, tw=0); ink(d, wobble(c, 0.3, seed + 20), 1.6, seed=seed + 20, closed=True)
    for k in range(4):
        wash(im, ellipse_pts(x + rr.uniform(-6, 8) * S, y + rr.uniform(-5, 5) * S, 1.6 * S, 1.6 * S, 8), (186, 132, 60), 255, edge=0, tw=0)

def top_hat(im, x, y, w, tilt, seed):
    """Hat sits centred on (x, y) = middle of the crown of the head; tilt in radians."""
    d = ImageDraw.Draw(im)
    def rot(px, py):
        c, s = math.cos(tilt), math.sin(tilt)
        return (x + px * c - py * s, y + px * s + py * c)
    hh = w * 0.62
    crown = [rot(-w * 0.31, 0), rot(-w * 0.34, -hh), rot(w * 0.34, -hh), rot(w * 0.31, 0)]
    crown = bez(crown[0], crown[0], crown[1], crown[1], 6) + bez(crown[1], rot(0, -hh - w * 0.06), rot(0, -hh - w * 0.06), crown[2], 16) + bez(crown[2], crown[2], crown[3], crown[3], 6)
    brim = [rot(w * 0.6 * math.cos(a), w * 0.09 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 50)]
    wash(im, brim, (46, 36, 64), 255, edge=0.3, tw=0, blur=0.6)
    wash(im, crown, (52, 40, 72), 255, edge=0.35, tw=0, blur=0.6)
    band = [rot(-w * 0.315, -w * 0.07), rot(w * 0.315, -w * 0.07), rot(w * 0.325, -w * 0.19), rot(-w * 0.325, -w * 0.19)]
    wash(im, band, (170, 132, 226), 255, edge=0.3)
    hl = [rot(-w * 0.24, -w * 0.24), rot(-w * 0.18, -w * 0.24), rot(-w * 0.19, -hh + w * 0.08), rot(-w * 0.25, -hh + w * 0.08)]
    wash(im, hl, (120, 108, 150), 160, edge=0, blur=3)
    ink(d, wobble(brim, 0.4, seed), 3.2, seed=seed, closed=True)
    ink(d, wobble(crown, 0.5, seed + 1), 3.4, seed=seed + 1)
    ink(d, wobble([band[0], band[1]], 0.3, seed + 2), 1.6, alpha=160)
    ink(d, wobble([band[3], band[2]], 0.3, seed + 3), 1.6, alpha=160)

def bow_tie(im, x, y, w, seed):
    d = ImageDraw.Draw(im)
    L = [(x, y), (x - w, y - w * 0.55), (x - w * 1.05, y + w * 0.5)]
    Rr = [(x, y), (x + w, y - w * 0.5), (x + w * 1.05, y + w * 0.55)]
    for t, k in ((L, 0), (Rr, 1)):
        p = bez(t[0], t[1], t[1], t[1], 6) + bez(t[1], t[1], t[2], t[2], 6) + bez(t[2], t[2], t[0], t[0], 6)
        wash(im, p, (150, 110, 214), 255, edge=0.45); ink(d, wobble(p, 0.3, seed + k), 2.4, seed=seed + k)
    k = ellipse_pts(x, y, w * 0.24, w * 0.3)
    wash(im, k, (126, 90, 190), 255, edge=0.4); ink(d, k, 2.0)

def _collar(im, cx, y, w, shear, seed):
    d = ImageDraw.Draw(im)
    n = 7
    for i in range(n):
        u = (i + 0.5) / n
        x, yy = shear(cx - w / 2 + w * u, y + 10 * S * math.sin(math.pi * u))
        p = ellipse_pts(x, yy, w / n * 0.62, w / n * 0.5, 20, 0, math.pi)
        p = [(x - w / n * 0.62, yy)] + p
        wash(im, p, (255, 252, 255), 255, edge=0.3)
        ink(d, wobble(p, 0.2, seed + i), 1.6, seed=seed + i)
        dot = ellipse_pts(x, yy + w / n * 0.22, 2.4 * S, 2.4 * S, 10); ink(d, dot, 1.0, alpha=160)

def arm(im, p0, p1, p2, width, seed, hand=True, fill_only=False):
    """A soft ghostly sleeve from p0 curving through p1 to a round hand at p2."""
    d = ImageDraw.Draw(im)
    c = bez(p0, p1, p1, p2, 30)
    left, right = [], []
    for i, (x, y) in enumerate(c):
        a, b = c[max(0, i - 1)], c[min(len(c) - 1, i + 1)]
        dx, dy = b[0] - a[0], b[1] - a[1]; L = math.hypot(dx, dy) or 1
        ww = width * (1 - 0.45 * i / len(c))
        left.append((x - dy / L * ww, y + dx / L * ww)); right.append((x + dy / L * ww, y - dx / L * ww))
    p = left + right[::-1]
    wash(im, p, (247, 245, 255), 255, edge=0.1, tw=0.0)
    if fill_only:
        return
    ink(d, wobble(left, 0.4, seed), 2.8, seed=seed)
    ink(d, wobble(right, 0.4, seed + 1), 2.8, seed=seed + 1)
    if hand:
        hp = ellipse_pts(p2[0], p2[1], width * 0.75, width * 0.7)
        wash(im, hp, (250, 248, 255), 255, edge=0.12, tw=0.04)
        ink(d, wobble(hp, 0.3, seed + 2), 2.6, seed=seed + 2, closed=True)

def note(im, x, y, s, col, seed, tilt=0.0):
    d = ImageDraw.Draw(im)
    def head(hx, hy, rot):
        h = ellipse_pts(hx, hy, 14 * S * s, 10 * S * s, 24)
        h = [(hx + (px - hx) * math.cos(rot) - (py - hy) * math.sin(rot), hy + (px - hx) * math.sin(rot) + (py - hy) * math.cos(rot)) for px, py in h]
        wash(im, h, col, 255, edge=0.4, tw=0); ink(d, wobble(h, 0.3, seed + int(hx) % 97), 2.2, seed=seed, closed=True)
    if tilt >= 0:     # single eighth note, leaning
        head(x, y, -0.5)
        top = (x + 13 * S * s + tilt, y - 68 * S * s)
        ink(d, wobble([(x + 12 * S * s, y - 4 * S * s), top], 0.4, seed + 1), 2.8)
        flag = bez(top, (top[0] + 22 * S * s, top[1] + 10 * S * s), (top[0] + 26 * S * s, top[1] + 30 * S * s), (top[0] + 14 * S * s, top[1] + 44 * S * s), 14)
        ink(d, wobble(flag, 0.3, seed + 2), 3.0)
    else:             # two eighths joined by a sagging beam
        x2, y2 = x + 52 * S * s, y - 14 * S * s
        head(x, y, -0.35); head(x2, y2, -0.6)
        t1, t2 = (x + 12 * S * s, y - 62 * S * s), (x2 + 12 * S * s, y2 - 60 * S * s)
        ink(d, wobble([(x + 12 * S * s, y - 4 * S * s), t1], 0.4, seed + 3), 2.6)
        ink(d, wobble([(x2 + 12 * S * s, y2 - 4 * S * s), t2], 0.4, seed + 4), 2.6)
        beam = bez(t1, ((t1[0] + t2[0]) / 2, (t1[1] + t2[1]) / 2 + 5 * S * s), ((t1[0] + t2[0]) / 2, (t1[1] + t2[1]) / 2 + 5 * S * s), t2, 10)
        ink(d, beam, 6.5)

def sparkle(im, x, y, r, seed, col=(255, 236, 180)):
    d = ImageDraw.Draw(im)
    p = []
    for k in range(8):
        a = k * math.pi / 4 - math.pi / 2; rr = r if k % 2 == 0 else r * 0.3
        p.append((x + rr * math.cos(a), y + rr * math.sin(a)))
    p = bez(p[0], p[1], p[1], p[2], 6) + bez(p[2], p[3], p[3], p[4], 6) + bez(p[4], p[5], p[5], p[6], 6) + bez(p[6], p[7], p[7], p[0], 6)
    glow(im, x, y, r * 1.4, col, 60)
    wash(im, p, col, 255, edge=0.3); ink(d, wobble(p, 0.2, seed), 1.8, seed=seed, closed=True)

def wisp(im, x, y, s, seed, flip=1, peek=False):
    d = ImageDraw.Draw(im)
    r = 30 * S * s
    head = [(x + r * math.cos(a), y + r * math.sin(a)) for a in np.linspace(math.pi * 0.25, -math.pi * 1.25, 40)]
    tip = (x + flip * 46 * S * s, y + 78 * S * s)
    tail = bez(head[-1], (x - r * 0.9, y + 40 * S * s), (x + flip * 10 * S * s, y + 70 * S * s), tip, 18)
    tail += bez(tip, (x + flip * 30 * S * s, y + 52 * S * s), (x + r * 0.95, y + 36 * S * s), head[0], 18)[1:]
    p = head + tail[1:]
    if peek:          # lean toward the dancers
        p = [(x + (px - x) * math.cos(-0.25) - (py - y) * math.sin(-0.25), y + (px - x) * math.sin(-0.25) + (py - y) * math.cos(-0.25)) for px, py in p]
    glow(im, x, y, 60 * S * s, (210, 214, 255), 50)
    wash(im, p, (247, 246, 255), 255, edge=0.1, tw=0.0)
    ink(d, wobble(p, 0.3, seed), 2.6, seed=seed, closed=True)
    look = -5 * S * s if peek else 0
    for k, ex in enumerate((x - 10 * S * s, x + 7 * S * s)):
        e = ellipse_pts(ex + look, y - 3 * S * s + k * 2 * S, (3.6 - 0.5 * k) * S * s, (4.8 - 0.5 * k) * S * s)
        wash(im, e, INK, 255, edge=0, blur=0.5, tw=0)
        wash(im, ellipse_pts(ex + look - 1.2 * S, y - 5 * S * s + k * 2 * S, 1.2 * S, 1.2 * S, 8), (255, 255, 255), 255, edge=0, tw=0)
    mo = ellipse_pts(x - 3 * S * s + look, y + 9 * S * s, 3.4 * S * s, 4.4 * S * s, 14)        # a small "oh!"
    wash(im, mo, (120, 60, 90), 255, edge=0, tw=0)
    for bx in (x - 19 * S * s, x + 15 * S * s):
        wash(im, ellipse_pts(bx, y + 8 * S * s, 5 * S * s, 3 * S * s), (244, 150, 178), 150, edge=0, blur=2, tw=0)

# ------------------------------------------------------------------ lettering
def lettering(im):
    f = ImageFont.truetype(FD + "HennyPenny-Regular.ttf", 132 * S)
    text = "Moonlit Ballroom"
    rr = random.Random(9)
    widths = [f.getlength(c) for c in text]
    total = sum(widths) - 4 * S * len(text)
    x = (W - total) / 2; base = 62 * S
    for i, c in enumerate(text):
        if c == " ":
            x += widths[i] - 4 * S; continue
        g = Image.new("RGBA", (int(widths[i] + 120 * S), int(260 * S)), (0, 0, 0, 0))
        gd = ImageDraw.Draw(g)
        for dx, dy in [(a, b) for a in range(-5, 6, 2) for b in range(-5, 8, 2)]:          # ink outline + drop
            gd.text((60 * S + dx * S, 40 * S + dy * S), c, font=f, fill=INK + (255,))
        gd.text((60 * S, 40 * S), c, font=f, fill=(250, 238, 214, 255))
        gm = Image.new("L", g.size, 0); ImageDraw.Draw(gm).text((60 * S, 40 * S), c, font=f, fill=255)
        hi = Image.new("RGBA", g.size, (242, 201, 125, 0))                                 # gold-ish shading on the lower half
        yy = np.linspace(0, 1, g.size[1])[:, None]
        sh = (np.asarray(gm, float) * np.clip((yy - 0.42) * 2.2, 0, 1) * 0.55).astype(np.uint8)
        hi.putalpha(Image.fromarray(sh)); g.alpha_composite(hi)
        g = g.rotate(rr.uniform(-4, 4), resample=Image.BICUBIC, expand=False)
        im.alpha_composite(g, (int(x - 60 * S), int(base - 40 * S + rr.uniform(-6, 6) * S)))
        x += widths[i] - 4 * S

def banner(im, cx, y, text):
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype(FD + "PatrickHand-Regular.ttf", 40 * S)
    tw = f.getlength(text); hw = tw / 2 + 60 * S
    top = bez((cx - hw, y), (cx - hw / 2, y - 14 * S), (cx + hw / 2, y - 14 * S), (cx + hw, y), 30)
    botm = bez((cx + hw, y + 62 * S), (cx + hw / 2, y + 48 * S), (cx - hw / 2, y + 48 * S), (cx - hw, y + 62 * S), 30)
    for sgn in (-1, 1):                                                                       # ribbon tails
        ex = cx + sgn * hw
        tail = [(ex, y + 10 * S), (ex + sgn * 70 * S, y + 22 * S), (ex + sgn * 46 * S, y + 50 * S), (ex + sgn * 72 * S, y + 80 * S), (ex, y + 70 * S)]
        wash(im, tail, (196, 150, 80), 255, edge=0.4); ink(d, wobble(tail, 0.3, 200 + sgn), 2.6, seed=200 + sgn, closed=True)
    p = top + botm
    wash(im, p, (242, 201, 125), 255, edge=0.35); ink(d, wobble(p, 0.4, 210), 3, seed=210, closed=True)
    # text follows the ribbon's gentle curve
    x = cx - tw / 2
    for c in text:
        cw = f.getlength(c)
        u = (x + cw / 2 - (cx - hw)) / (2 * hw)
        yy = y + 4 * S - 14 * S * math.sin(math.pi * u) * 0.75
        d.text((x, yy), c, font=f, fill=INK + (255,)); x += cw

# ------------------------------------------------------------------ compose
def reflection(im, box):
    """Faint mirrored copy of the dancers on the polished floor."""
    x0, y0, x1, y1 = box
    part = im.crop(box).transpose(Image.FLIP_TOP_BOTTOM)
    a = np.linspace(0.22, 0, part.height)[:, None] * np.ones((1, part.width))
    part.putalpha(Image.fromarray((np.asarray(part.split()[3], float) * a).astype(np.uint8)))
    im.alpha_composite(part.filter(ImageFilter.GaussianBlur(3 * S)), (x0, y1 - 10 * S))

def main(out):
    global TEX
    TEX = paper()
    im = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    background(im); window(im); floor(im)
    sconce(im, 70 * S, 600 * S)
    # moonlight pool on the floor in front of the window
    pool = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(pool).ellipse([700 * S, 880 * S, 1500 * S, 1060 * S], fill=(210, 200, 255, 50))
    im.alpha_composite(pool.filter(ImageFilter.GaussianBlur(40 * S)))
    dancers = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    r = 125 * S
    lx, rx = 700 * S, 1080 * S
    ltop, rtop = 470 * S, 440 * S
    lw, lh, rw, rh = 2 * r * 0.95, 400 * S * 0.95, 2 * r, 400 * S
    _, shL0 = ghost_outline(lx, ltop, lw, lh, 0.30, -60 * S)
    _, shR0 = ghost_outline(rx, rtop, rw, rh, -0.26, 55 * S)
    # joined hands: both arms start inside the bodies so no seam shows at the shoulder
    hp = ((lx + rx) / 2, ltop + r * 2.15)
    arm(dancers, shL0(lx + r * 0.45, ltop + r * 1.8), (hp[0] - 60 * S, hp[1] - 14 * S), (hp[0] - 6 * S, hp[1]), 22 * S, 300)
    arm(dancers, shR0(rx - r * 0.45, rtop + r * 1.85), (hp[0] + 60 * S, hp[1] - 10 * S), (hp[0] + 8 * S, hp[1] - 4 * S), 22 * S, 310)
    shL, fxL, fyL = ghost(dancers, lx, ltop, lw, lh, 0.30, -60 * S, 11, "lady")
    shR, fxR, fyR = ghost(dancers, rx, rtop, rw, rh, -0.26, 55 * S, 23, "gent")
    # redraw the two hands on top so the clasp reads in front of the bodies
    for (hx_, hy_), sd in (((hp[0] - 6 * S, hp[1]), 302), ((hp[0] + 8 * S, hp[1] - 4 * S), 312)):
        hpnts = ellipse_pts(hx_, hy_, 22 * S * 0.75, 22 * S * 0.7)
        wash(dancers, hpnts, (250, 248, 255), 255, edge=0.12, tw=0)
        ink(ImageDraw.Draw(dancers), wobble(hpnts, 0.3, sd), 2.6, seed=sd, closed=True)
    hx, hy = shL(lx, ltop)
    flower(dancers, hx + 78 * S, hy + 30 * S, 26 * S, 410)
    bx, by = shR(rx, rtop + r * 1.78)
    bow_tie(dancers, bx - 6 * S, by, 34 * S, 420)
    # top hat: brim wider than the head, seated a third of the way down the dome, centred on his centreline
    brim_y = rtop + r * 0.36
    hx, _ = shR(rx, brim_y)
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse([hx - r * 0.78, brim_y + 4 * S, hx + r * 0.78, brim_y + 30 * S], fill=(150, 134, 200, 120))
    dancers.alpha_composite(sh.filter(ImageFilter.GaussianBlur(6 * S)))
    top_hat(dancers, hx, brim_y, 230 * S, -math.atan(0.26 * 0.35) * 0.6, 430)
    bb = dancers.getbbox()
    im.alpha_composite(dancers)
    reflection(im, (bb[0], bb[1] + int((bb[3] - bb[1]) * 0.55), bb[2], bb[3]))
    note(im, 1452 * S, 640 * S, 0.95, (242, 201, 125), 500, tilt=-1)
    note(im, 1560 * S, 520 * S, 0.75, (206, 192, 240), 510, tilt=7 * S)
    wisp(im, 1688 * S, 700 * S, 1.15, 710, 1, peek=True)   # peeking out from behind the curtain
    curtain(im, "R")
    # title, two staggered lines, left
    f = ImageFont.truetype(FD + "HennyPenny-Regular.ttf", 150 * S)
    def word(text, x, y, rot):
        tw = int(f.getlength(text)) + 80 * S
        g = Image.new("RGBA", (tw, 260 * S), (0, 0, 0, 0)); gd = ImageDraw.Draw(g)
        for dx, dy in [(a, b) for a in range(-6, 7, 2) for b in range(-6, 10, 2)]:
            gd.text((40 * S + dx * S, 30 * S + dy * S), text, font=f, fill=INK + (255,))
        gd.text((40 * S, 30 * S), text, font=f, fill=(250, 238, 214, 255))
        gm = Image.new("L", g.size, 0); ImageDraw.Draw(gm).text((40 * S, 30 * S), text, font=f, fill=255)
        yy = np.linspace(0, 1, g.size[1])[:, None]
        hi = Image.new("RGBA", g.size, (238, 190, 110, 0))
        hi.putalpha(Image.fromarray((np.asarray(gm, float) * np.clip((yy - 0.45) * 2.4, 0, 1) * 0.6).astype(np.uint8)))
        g.alpha_composite(hi)
        g = g.rotate(rot, resample=Image.BICUBIC, expand=True)
        im.alpha_composite(g, (int(x), int(y)))
    word("Moonlit", 70 * S, 40 * S, 3)
    word("Ballroom", 170 * S, 190 * S, 3)
    d = ImageDraw.Draw(im)
    fs = ImageFont.truetype(FD + "PatrickHand-Regular.ttf", 42 * S)
    d.text((300 * S, 432 * S), "a Halloween pack for Nexo", font=fs, fill=(236, 222, 246, 255))
    # artist-style signature with the flower mark, bottom left
    mk = Image.open("/home/claude/mistbloom/brand/logo-v2/mistbloom-mark-transparent.png").convert("RGBA")
    mk = mk.crop(mk.getbbox()).resize((60 * S, 60 * S), Image.LANCZOS)
    im.alpha_composite(mk, (60 * S, H - 100 * S))
    sig = ImageFont.truetype(FD + "PatrickHand-Regular.ttf", 34 * S)
    gs = Image.new("RGBA", (500 * S, 80 * S), (0, 0, 0, 0)); ImageDraw.Draw(gs).text((0, 0), "mistbloom studios", font=sig, fill=(232, 222, 248, 230))
    im.alpha_composite(gs.rotate(4, resample=Image.BICUBIC, expand=False), (130 * S, H - 92 * S))
    grain = (128 + TEX * 30).clip(0, 255).astype(np.uint8)
    g = Image.merge("RGBA", [Image.fromarray(grain)] * 3 + [Image.new("L", (W, H), 255)])
    im = Image.blend(im, g, 0.05)
    im.convert("RGB").resize((1920, 1080), Image.LANCZOS).save(out)

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "moonlit-ballroom-title.png"))
    print("ok")
