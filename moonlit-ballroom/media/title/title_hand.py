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
    if closed: pts = pts + [pts[0]]
    dense = []
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        n = max(1, int(math.hypot(x1 - x0, y1 - y0) / (1.5 * S)))
        dense += [(x0 + (x1 - x0) * k / n, y0 + (y1 - y0) * k / n) for k in range(n)]
    for i, (x, y) in enumerate(dense):
        r = S * w * max(0.7, 0.85 + 0.25 * nz(i * 0.03, seed + 7, 2)) / 2
        d.ellipse([x - r, y - r, x + r, y + r], fill=col + (alpha,))

def bez(p0, p1, p2, p3, n=30):
    out = []
    for i in range(n + 1):
        t = i / n; u = 1 - t
        out.append((u**3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t**3 * p3[0],
                    u**3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t**3 * p3[1]))
    return out

TEX = None
def wash(base, pts, col, alpha=255, grad=None, edge=0.35, blur=1.2, tw=0.14):
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
    return (g - 128) / 128 * 0.5 + (big - 128) / 128

# ------------------------------------------------------------------ scene pieces
def background(im):
    d = ImageDraw.Draw(im)
    y = np.linspace(0, 1, H)[:, None, None]
    top, bot = np.array([44, 32, 78.]), np.array([70, 48, 104.])
    arr = np.broadcast_to(top * (1 - y) + bot * y, (H, W, 3)).copy()
    arr += (TEX[..., None] * 9)
    im.paste(Image.fromarray(arr.clip(0, 255).astype(np.uint8)).convert("RGBA"))
    # wall panels: soft vertical bands with hand-ruled edges
    for k, x in enumerate(range(-80 * S, W, 300 * S)):
        pts = [(x + 40 * S, 120 * S), (x + 250 * S, 120 * S), (x + 250 * S, 700 * S), (x + 40 * S, 700 * S)]
        wash(im, pts, (82, 58, 120), 70, edge=0.5, blur=3)
        ink(d, wobble([(x + 40 * S, 120 * S), (x + 40 * S, 700 * S)], 1.2, k), 1.4, alpha=70, seed=k)
        ink(d, wobble([(x + 250 * S, 120 * S), (x + 250 * S, 700 * S)], 1.2, k + 50), 1.4, alpha=70, seed=k + 3)

def window(im):
    d = ImageDraw.Draw(im)
    cx, hw, spring, bot = W / 2, 300 * S, 470 * S, 760 * S
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
    glow(sky, cx - 120 * S, 320 * S, 150 * S, (255, 240, 205), 90)
    wash(sky, ellipse_pts(cx - 120 * S, 320 * S, 80 * S, 80 * S), (252, 242, 214), 255, edge=0.12)
    sd = ImageDraw.Draw(sky)
    for (dx, dy, r) in ((-30, -20, 16), (25, 30, 11), (40, -35, 8)):
        wash(sky, ellipse_pts(cx + (-120 + dx) * S, (320 + dy) * S, r * S, r * S), (232, 218, 186), 200, edge=0.3)
    ink(sd, wobble(ellipse_pts(cx - 120 * S, 320 * S, 80 * S, 80 * S), 0.8, 5), 1.6, alpha=110, seed=5)
    sky.putalpha(ImageChops.multiply(sky.split()[3], mask))
    im.alpha_composite(sky)
    # mullions and frame
    ink(d, wobble([(cx, spring - Rr * 0.97 + 30 * S), (cx, bot)], 1.0, 3), 5, alpha=255)
    ink(d, wobble([(cx - hw, 520 * S), (cx + hw, 520 * S)], 1.0, 4), 4, alpha=255)
    ink(d, wobble(shape, 1.4, 1), 6.5, alpha=255, seed=1)
    inner = [(cx + (x - cx) * 0.93, y + 22 * S) for x, y in shape]
    ink(d, wobble(inner, 1.0, 2), 2.2, col=(242, 201, 125), alpha=170, seed=2)
    # sill
    sill = [(cx - hw - 30 * S, bot), (cx + hw + 30 * S, bot), (cx + hw + 22 * S, bot + 26 * S), (cx - hw - 22 * S, bot + 26 * S)]
    wash(im, sill, (96, 74, 128), 255, edge=0.4)
    ink(d, wobble(sill, 1, 9), 3, seed=9, closed=True)

def floor(im):
    d = ImageDraw.Draw(im)
    hz, vx = 780 * S, W / 2
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
            wash(im, q, (196, 182, 226), 120 + 20 * min(r, 5), edge=0.35, blur=1.5)
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
    # gold tie-back with a tassel
    tx, ty = x0 + sgn * 150 * S, edge_tie
    tie = ellipse_pts(tx - sgn * 70 * S, ty, 95 * S, 22 * S)
    wash(im, tie, (226, 178, 96), 255, edge=0.4)
    ink(d, wobble(tie, 0.8, 71), 2.6, seed=71)
    tas = [(tx - sgn * 10 * S, ty + 10 * S), (tx + sgn * 14 * S, ty + 10 * S), (tx + sgn * 26 * S, ty + 110 * S), (tx - sgn * 22 * S, ty + 110 * S)]
    wash(im, tas, (226, 178, 96), 255, edge=0.4)
    for k in range(5):
        ink(d, [(tx - sgn * 14 * S + sgn * k * 9 * S, ty + 40 * S), (tx - sgn * 18 * S + sgn * k * 10 * S, ty + 108 * S)], 1.2, alpha=150)
    ink(d, wobble(tas, 0.6, 72), 2.4, seed=72, closed=True)

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
    m = wash(im, pts, (247, 245, 255), 255, grad=(1.0, 0.93), edge=0.10, tw=0.04)
    # shade on the side away from the moon, plus a moonlit rim
    off = 22 * S if who == "lady" else 26 * S
    shade = Image.new("L", (W, H), 0); ImageDraw.Draw(shade).polygon([(x + off, y + 6 * S) for x, y in pts], fill=255)
    shade = ImageChops.subtract(m, shade).filter(ImageFilter.GaussianBlur(8 * S))
    lay = Image.new("RGBA", (W, H), (176, 160, 226, 0)); lay.putalpha(shade.point(lambda v: int(v * 0.55)))
    im.alpha_composite(lay)
    ink(d, wobble(pts, 1.1, seed), 4.2, seed=seed, closed=True)
    # face
    fx, fy = shear(cx, top + w * 0.50)
    fx += (10 * S if who == "lady" else -10 * S)
    for ex in (fx - w * 0.17, fx + w * 0.17):
        ink(d, wobble(ellipse_pts(ex, fy + 6 * S, w * 0.075, w * 0.06, 20, math.pi * 1.1, math.pi * 1.9), 0.3, seed + 3), 4.6, seed=seed + 3)
        if who == "lady":
            for k in (-1, 0, 1):
                a = math.pi * 1.5 + k * 0.45
                x1, y1 = ex + w * 0.075 * math.cos(a), fy + 6 * S + w * 0.06 * math.sin(a)
                ink(d, [(x1, y1), (x1 + k * 5 * S, y1 - 10 * S)], 1.8)
    for bx in (fx - w * 0.27, fx + w * 0.27):
        wash(im, ellipse_pts(bx, fy + w * 0.11, w * 0.07, w * 0.04), (244, 150, 178), 170, edge=0, blur=4)
    ink(d, wobble(ellipse_pts(fx, fy + w * 0.07, w * 0.05, w * 0.045, 16, 0.2, math.pi - 0.2), 0.2, seed + 4), 3.6, seed=seed + 4)
    return shear, fx, fy

def flower(im, x, y, r, seed):
    d = ImageDraw.Draw(im)
    for k in range(2):
        a = math.pi * (0.75 + 0.5 * k)
        lf = bez((x, y), (x + r * 1.6 * math.cos(a - 0.4), y + r * 1.6 * math.sin(a - 0.4)), (x + r * 2.2 * math.cos(a), y + r * 2.2 * math.sin(a)),
                 (x + r * 2.4 * math.cos(a), y + r * 2.4 * math.sin(a)), 12)
        lf += bez(lf[-1], (x + r * 1.6 * math.cos(a + 0.4), y + r * 1.6 * math.sin(a + 0.4)), (x, y), (x, y), 12)
        wash(im, lf, (120, 168, 120), 255, edge=0.4); ink(d, wobble(lf, 0.3, seed + k), 1.8, seed=seed + k)
    for k in range(5):
        a = k * 2 * math.pi / 5 - math.pi / 2
        p = ellipse_pts(x + r * 0.75 * math.cos(a), y + r * 0.75 * math.sin(a), r * 0.62, r * 0.62)
        wash(im, p, (170, 132, 226), 255, edge=0.45)
        ink(d, wobble(p, 0.3, seed + 10 + k), 1.8, seed=seed + 10 + k)
    c = ellipse_pts(x, y, r * 0.38, r * 0.38)
    wash(im, c, (246, 204, 118), 255, edge=0.4); ink(d, c, 1.6)

def top_hat(im, x, y, w, tilt, seed):
    """Hat sits centred on (x, y) = middle of the crown of the head; tilt in radians."""
    d = ImageDraw.Draw(im)
    def rot(px, py):
        c, s = math.cos(tilt), math.sin(tilt)
        return (x + px * c - py * s, y + px * s + py * c)
    hh = w * 0.95
    crown = [rot(-w * 0.36, 0), rot(-w * 0.40, -hh), rot(w * 0.40, -hh), rot(w * 0.36, 0)]
    crown = bez(crown[0], crown[0], crown[1], crown[1], 6) + bez(crown[1], rot(0, -hh - w * 0.06), rot(0, -hh - w * 0.06), crown[2], 16) + bez(crown[2], crown[2], crown[3], crown[3], 6)
    brim = [rot(w * 0.62 * math.cos(a), w * 0.10 * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 50)]
    wash(im, brim, (46, 36, 64), 255, edge=0.3)
    wash(im, crown, (52, 40, 72), 255, edge=0.35)
    band = [rot(-w * 0.37, -w * 0.10), rot(w * 0.37, -w * 0.10), rot(w * 0.38, -w * 0.26), rot(-w * 0.38, -w * 0.26)]
    wash(im, band, (170, 132, 226), 255, edge=0.3)
    hl = [rot(-w * 0.26, -w * 0.32), rot(-w * 0.18, -w * 0.32), rot(-w * 0.20, -hh + w * 0.1), rot(-w * 0.27, -hh + w * 0.1)]
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

def collar(im, cx, y, w, shear, seed):
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

def arm(im, p0, p1, p2, width, seed, hand=True):
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
    wash(im, p, (247, 245, 255), 255, edge=0.1, tw=0.04)
    ink(d, wobble(left, 0.4, seed), 2.8, seed=seed)
    ink(d, wobble(right, 0.4, seed + 1), 2.8, seed=seed + 1)
    if hand:
        hp = ellipse_pts(p2[0], p2[1], width * 0.75, width * 0.7)
        wash(im, hp, (250, 248, 255), 255, edge=0.12, tw=0.04)
        ink(d, wobble(hp, 0.3, seed + 2), 2.6, seed=seed + 2, closed=True)

def note(im, x, y, s, col, seed, tilt=0.0):
    d = ImageDraw.Draw(im)
    head = ellipse_pts(x, y, 15 * S * s, 11 * S * s)
    head = [(x + (px - x) * math.cos(-0.4) - (py - y) * math.sin(-0.4), y + (px - x) * math.sin(-0.4) + (py - y) * math.cos(-0.4)) for px, py in head]
    wash(im, head, col, 255, edge=0.4)
    ink(d, wobble(head, 0.2, seed), 2.2, seed=seed, closed=True)
    ink(d, wobble([(x + 13 * S * s, y - 4 * S * s), (x + 15 * S * s + tilt, y - 70 * S * s)], 0.3, seed + 1), 3.0)
    flag = bez((x + 15 * S * s + tilt, y - 70 * S * s), (x + 40 * S * s, y - 56 * S * s), (x + 34 * S * s, y - 36 * S * s), (x + 28 * S * s, y - 26 * S * s), 14)
    ink(d, wobble(flag, 0.2, seed + 2), 3.0)

def sparkle(im, x, y, r, seed, col=(255, 236, 180)):
    d = ImageDraw.Draw(im)
    p = []
    for k in range(8):
        a = k * math.pi / 4 - math.pi / 2; rr = r if k % 2 == 0 else r * 0.3
        p.append((x + rr * math.cos(a), y + rr * math.sin(a)))
    p = bez(p[0], p[1], p[1], p[2], 6) + bez(p[2], p[3], p[3], p[4], 6) + bez(p[4], p[5], p[5], p[6], 6) + bez(p[6], p[7], p[7], p[0], 6)
    glow(im, x, y, r * 1.4, col, 60)
    wash(im, p, col, 255, edge=0.3); ink(d, wobble(p, 0.2, seed), 1.8, seed=seed, closed=True)

def wisp(im, x, y, s, seed, flip=1):
    d = ImageDraw.Draw(im)
    body = [(x + 30 * S * s * math.cos(a), y + 28 * S * s * math.sin(a)) for a in np.linspace(math.pi * 0.9, math.pi * 2.1, 30)]
    tail = bez(body[-1], (x + flip * 40 * S * s, y + 40 * S * s), (x + flip * 10 * S * s, y + 70 * S * s), (x - flip * 30 * S * s, y + 62 * S * s), 20)
    tail += bez(tail[-1], (x - flip * 10 * S * s, y + 50 * S * s), (x - 30 * S * s, y + 30 * S * s), body[0], 20)
    p = body + tail
    glow(im, x, y, 60 * S * s, (210, 214, 255), 50)
    wash(im, p, (246, 246, 255), 230, edge=0.1)
    ink(d, wobble(p, 0.4, seed), 2.6, seed=seed, closed=True)
    for ex in (x - 9 * S * s, x + 9 * S * s):
        e = ellipse_pts(ex, y - 2 * S * s, 3.2 * S * s, 4.2 * S * s)
        wash(im, e, INK, 255, edge=0, blur=0.5)
    wash(im, ellipse_pts(x - 17 * S * s, y + 8 * S * s, 5 * S * s, 3 * S * s), (244, 150, 178), 150, edge=0, blur=2)
    wash(im, ellipse_pts(x + 17 * S * s, y + 8 * S * s, 5 * S * s, 3 * S * s), (244, 150, 178), 150, edge=0, blur=2)

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
def main(out):
    global TEX
    TEX = paper()
    im = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    background(im); window(im); floor(im)
    chandelier(im, 520 * S, 250 * S, 0.75); chandelier(im, W - 520 * S, 250 * S, 0.75)
    # dancers: lady on the left, gentleman on the right, holding hands between them
    r = 125 * S
    lx, rx = W / 2 - 205 * S, W / 2 + 205 * S
    ltop, rtop = 470 * S, 440 * S
    lw, lh, rw, rh = 2 * r * 0.95, 400 * S * 0.95, 2 * r, 400 * S
    # her raised outer arm and his hand-on-hip arm go behind the bodies
    _, shL0 = ghost_outline(lx, ltop, lw, lh, 0.30, -60 * S)
    _, shR0 = ghost_outline(rx, rtop, rw, rh, -0.26, 55 * S)
    p = shL0(lx - r * 0.9, ltop + r * 1.75)
    arm(im, p, (p[0] - 110 * S, p[1] - 40 * S), (p[0] - 120 * S, p[1] - 150 * S), 22 * S, 330)
    q = shR0(rx + r * 0.95, rtop + r * 1.8)
    arm(im, q, (q[0] + 90 * S, q[1] + 30 * S), (q[0] + 30 * S, q[1] + 110 * S), 22 * S, 340, hand=False)
    shL, fxL, fyL = ghost(im, lx, ltop, lw, lh, 0.30, -60 * S, 11, "lady")
    shR, fxR, fyR = ghost(im, rx, rtop, rw, rh, -0.26, 55 * S, 23, "gent")
    # joined hands at chest height in the gap
    hp = (W / 2, ltop + r * 2.15)
    arm(im, shL(lx + r * 0.85, ltop + r * 1.85), (hp[0] - 50 * S, hp[1] - 10 * S), (hp[0] - 6 * S, hp[1]), 22 * S, 300)
    arm(im, shR(rx - r * 0.85, rtop + r * 1.9), (hp[0] + 50 * S, hp[1] - 6 * S), (hp[0] + 8 * S, hp[1] - 4 * S), 22 * S, 310)
    collar(im, lx, ltop + r * 1.72, lw * 0.62, shL, 400)
    hx, hy = shL(lx, ltop)
    flower(im, hx + 78 * S, hy + 30 * S, 26 * S, 410)
    bx, by = shR(rx, rtop + r * 1.78)
    bow_tie(im, bx - 6 * S, by, 34 * S, 420)
    # hat: centred on the crown of his head, tilted with his lean
    hx, hy = shR(rx, rtop)
    top_hat(im, hx, hy + 14 * S, 170 * S, -math.atan(0.26 * 0.35) * 0.6, 430)
    # music, sparkles, wisps
    note(im, W / 2 + 450 * S, 660 * S, 1.2, (242, 201, 125), 500, tilt=4 * S)
    note(im, W / 2 + 545 * S, 575 * S, 0.9, (196, 182, 236), 510)
    note(im, W / 2 - 590 * S, 470 * S, 1.0, (196, 182, 236), 520)
    for (x, y, r, s) in ((W / 2 - 420, 900, 22, 600), (W / 2 + 400, 940, 18, 601), (W / 2 - 300, 330, 14, 602), (W / 2 + 330, 300, 12, 603), (W / 2 + 20, 990, 16, 604)):
        sparkle(im, x * S if x > 100 else x, y * S, r * S, s)
    wisp(im, 560 * S, 760 * S, 1.2, 700, 1); wisp(im, W - 470 * S, 860 * S, 1.0, 710, -1)
    curtain(im, "L"); curtain(im, "R")
    lettering(im)
    banner(im, W / 2, 978 * S, "friendly ghosts for your Halloween builds")
    # tiny signature-style credit
    f = ImageFont.truetype(FD + "PatrickHand-Regular.ttf", 30 * S)
    d = ImageDraw.Draw(im)
    d.text((W - 330 * S, H - 52 * S), "Mistbloom Studios", font=f, fill=(236, 226, 250, 220))
    # paper grain over everything
    grain = (128 + TEX * 20).clip(0, 255).astype(np.uint8)
    g = Image.merge("RGBA", [Image.fromarray(grain)] * 3 + [Image.new("L", (W, H), 34)])
    im = Image.blend(im, Image.composite(g, im, Image.new("L", (W, H), 255)), 0.12)
    out_im = im.convert("RGB").resize((1920, 1080), Image.LANCZOS)
    out_im.save(out)

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "moonlit-ballroom-title.png"))
    print("ok")
