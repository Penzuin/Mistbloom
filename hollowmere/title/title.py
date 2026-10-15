"""Halloween Festival title card (1920x1080), Mistbloom style.
Night sky + moon, layered spooky hills and trees, bat bunting, the pack's own pieces rendered
in front, and the hand-lettered-looking title with a warm pumpkin glow."""
import math, os, random, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageChops

sys.path.insert(0, "/home/claude/hollow")
HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "fonts")
W, H = 1920, 1080
TITLE_FONT = os.environ.get("TF", "Griffy-Regular.ttf")

PUMP = (255, 150, 60); PUMP_HI = (255, 214, 120); PLUM = (88, 52, 130); INK = (22, 12, 34)
CREAM = (255, 238, 210); LILAC = (205, 180, 240)


def F(name, size):
    p = os.path.join(FONTS, name)
    if os.path.exists(p):
        return ImageFont.truetype(p, size)
    return ImageFont.truetype(f"/usr/share/fonts/truetype/{name}", size)


def inter(size, weight="SemiBold"):
    import glob
    c = glob.glob(f"/usr/share/fonts/**/Inter-{weight}.*", recursive=True) or glob.glob("/usr/share/fonts/**/Inter*.ttf", recursive=True)
    return ImageFont.truetype(c[0], size)


# ---------------------------------------------------------------- background
def sky(seed=7):
    y = np.linspace(0, 1, H)[:, None]
    top, mid, bot = np.array([14, 10, 30]), np.array([46, 22, 66]), np.array([120, 52, 70])
    c = np.where(y < 0.6, top + (mid - top) * (y / 0.6), mid + (bot - mid) * ((y - 0.6) / 0.4))
    img = np.repeat(c[:, None, :], W, 1).reshape(H, W, 3)
    im = Image.fromarray(img.astype(np.uint8)).convert("RGBA")
    d = ImageDraw.Draw(im)
    rng = random.Random(seed)
    for _ in range(260):                                     # stars, denser near the top
        x, yy = rng.uniform(0, W), rng.uniform(0, H) ** 1.6 / H ** 0.6
        r = rng.choice((1, 1, 1, 1.5, 2))
        a = rng.randint(90, 230)
        d.ellipse((x - r, yy - r, x + r, yy + r), fill=(255, 245, 225, a))
    return im


def moon(im, cx, cy, r):
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0)); g = ImageDraw.Draw(glow)
    for k, a in ((3.2, 26), (2.2, 40), (1.5, 70)):
        g.ellipse((cx - r * k, cy - r * k, cx + r * k, cy + r * k), fill=(255, 210, 150, a))
    im.alpha_composite(glow.filter(ImageFilter.GaussianBlur(r * 0.6)))
    m = Image.new("RGBA", (W, H), (0, 0, 0, 0)); md = ImageDraw.Draw(m)
    md.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(255, 236, 196, 255))
    for fx, fy, fs in ((.38, -.42, .10), (-.30, .36, .13), (.46, .30, .07), (-.52, -.12, .06), (.10, .58, .05)):
        x, y, s = cx + fx * r, cy + fy * r, fs * r                # a few faint craters, off to the edges
        md.ellipse((x - s, y - s, x + s, y + s), fill=(246, 222, 182, 255))
    im.alpha_composite(m.filter(ImageFilter.GaussianBlur(1.2)))


def hills(im, base, amp, color, seed, trees=0, blur=0):
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    rng = random.Random(seed)
    ph = [rng.uniform(0, 6.28) for _ in range(3)]
    pts = [(x, base - amp * (0.6 * math.sin(x / 260 + ph[0]) + 0.3 * math.sin(x / 120 + ph[1]) + 0.1 * math.sin(x / 47 + ph[2])))
           for x in range(-10, W + 20, 10)]
    d.polygon(pts + [(W + 20, H), (-10, H)], fill=color)
    for _ in range(trees):                                   # bare crooked trees on the ridge
        x = rng.uniform(40, W - 40)
        y = min(p[1] for p in pts if abs(p[0] - x) < 12) + 4
        h = rng.uniform(80, 170)
        tree(d, x, y, h, color, rng)
    im.alpha_composite(L.filter(ImageFilter.GaussianBlur(blur)) if blur else L)


def tree(d, x, y, h, color, rng):
    """Hand-drawn style bare tree: leaning, tapered trunk that wobbles as it rises, uneven limbs
    (never mirrored pairs), a broken stub or two, and thin curling twigs at the tips."""
    lean = rng.uniform(-14, 14)
    _limb(d, x, y, h, -90 + lean, max(4, h / 7), color, rng, 0)
    d.polygon([(x - h / 9, y + 3), (x - h / 22, y - h / 12), (x + h / 22, y - h / 12), (x + h / 7, y + 3)], fill=color)   # root flare


def _limb(d, x, y, length, ang, w, color, rng, depth):
    steps = max(3, int(length / 9))
    pts_l, pts_r = [], []
    a = ang
    for k in range(steps + 1):
        t = k / steps
        ww = w * (1 - 0.75 * t) / 2
        nx, ny = math.cos(math.radians(a + 90)), math.sin(math.radians(a + 90))
        pts_l.append((x + nx * ww, y + ny * ww)); pts_r.append((x - nx * ww, y - ny * ww))
        if k < steps:
            a += rng.uniform(-9, 9) + (2.5 if depth else 0) * (1 if ang > -90 else -1)   # wobble, outer limbs droop
            x += math.cos(math.radians(a)) * length / steps
            y += math.sin(math.radians(a)) * length / steps
            if depth < 3 and k >= 1 and rng.random() < (0.42 if depth == 0 else 0.3):
                side = rng.choice((-1, 1))
                _limb(d, x, y, length * rng.uniform(0.35, 0.62), a + side * rng.uniform(22, 55), ww * 1.5,
                      color, rng, depth + 1)
    d.polygon(pts_l + pts_r[::-1], fill=color)
    if depth >= 2 or length < 18:                          # curling twig at the tip
        tw = [(x, y)]
        for _ in range(4):
            a += rng.choice((-1, 1)) * rng.uniform(15, 35)
            x += math.cos(math.radians(a)) * length * 0.12; y += math.sin(math.radians(a)) * length * 0.12
            tw.append((x, y))
        d.line(tw, fill=color, width=2)


def mist(im, y, strength=70):
    m = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(m).ellipse((-300, y - 90, W + 300, y + 120), fill=(190, 150, 210, strength))
    im.alpha_composite(m.filter(ImageFilter.GaussianBlur(60)))


# ---------------------------------------------------------------- bunting
def bat_shape(d, cx, cy, s, fill):
    pts = [(-1, 0), (-.75, -.28), (-.55, -.05), (-.38, -.32), (-.18, -.08), (0, -.22), (.18, -.08), (.38, -.32),
           (.55, -.05), (.75, -.28), (1, 0), (.55, .1), (.35, .32), (.12, .14), (0, .34), (-.12, .14), (-.35, .32), (-.55, .1)]
    d.polygon([(cx + px * s, cy + py * s) for px, py in pts], fill=fill)
    d.polygon([(cx - .12 * s, cy - .2 * s), (cx - .06 * s, cy - .36 * s), (cx, cy - .22 * s), (cx + .06 * s, cy - .36 * s),
               (cx + .12 * s, cy - .2 * s)], fill=fill)


def bunting(im, y0, sag, n=13):
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    yy = lambda x: y0 + sag * math.sin(math.pi * x / W)
    d.line([(x, yy(x)) for x in range(0, W + 1, 8)], fill=(40, 24, 50, 255), width=4)
    for i in range(n):
        x = (i + 0.5) * W / n; y = yy(x)
        if i % 2 == 0:
            col = [PUMP, PLUM, (120, 170, 90)][(i // 2) % 3]
            d.polygon([(x - 34, y), (x + 34, y), (x, y + 74)], fill=col + (255,))
            d.polygon([(x - 34, y), (x + 34, y), (x + 28, y + 8), (x - 28, y + 8)], fill=tuple(int(c * .75) for c in col) + (255,))
        else:
            bat_shape(d, x, y + 26, 40, (26, 16, 36, 255))
            d.ellipse((x - 9, y + 13, x - 5, y + 17), fill=(255, 190, 90, 255)); d.ellipse((x + 5, y + 13, x + 9, y + 17), fill=(255, 190, 90, 255))
    im.alpha_composite(L)


# ---------------------------------------------------------------- the pack's pieces
def piece(mod, name, ppu, cam=(-0.62, 0.45, -1), lit=False):
    import importlib
    fn = getattr(importlib.import_module(mod), name)
    m = fn(True) if lit else fn()
    m.check()
    img = m.render(ppu=ppu, cam=cam, frame=0)
    return img.crop(img.getbbox())


def glow_at(im, cx, cy, r, color=(255, 170, 70), a=110):
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(g).ellipse((cx - r, cy - r, cx + r, cy + r), fill=color + (a,))
    im.alpha_composite(g.filter(ImageFilter.GaussianBlur(r * 0.45)))


def place(im, sprite, cx, bottom, shadow=True):
    x, y = int(cx - sprite.width / 2), int(bottom - sprite.height)
    if shadow:
        s = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(s).ellipse((x + sprite.width * .1, bottom - 16, x + sprite.width * .9, bottom + 14), fill=(10, 4, 16, 150))
        im.alpha_composite(s.filter(ImageFilter.GaussianBlur(8)))
    im.alpha_composite(sprite, (x, y))


# ---------------------------------------------------------------- lettering
def gradient_text(text, font, top, bot, stroke=10):
    d0 = ImageDraw.Draw(Image.new("L", (1, 1)))
    l, t, r, b = d0.textbbox((0, 0), text, font=font, stroke_width=stroke)
    w, h = r - l + 40, b - t + 40
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).text((20 - l, 20 - t), text, font=font, fill=255)
    out_mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(out_mask).text((20 - l, 20 - t), text, font=font, fill=255, stroke_width=stroke, stroke_fill=255)
    grad = np.zeros((h, w, 4), np.uint8)
    yy = np.linspace(0, 1, h)[:, None]
    for k in range(3):
        grad[..., k] = (top[k] + (bot[k] - top[k]) * yy).astype(np.uint8)
    grad[..., 3] = np.array(mask)
    fill = Image.fromarray(grad)
    # inner highlight band along the top edge of each letter
    hl = ImageChops.subtract(mask, mask.transform(mask.size, Image.AFFINE, (1, 0, 0, 0, 1, -5)))
    hlimg = Image.new("RGBA", (w, h), (255, 246, 220, 0)); hlimg.putalpha(hl.point(lambda v: int(v * 0.55)))
    outline = Image.new("RGBA", (w, h), INK + (0,)); outline.putalpha(out_mask)
    drop = Image.new("RGBA", (w, h), (8, 2, 14, 0)); drop.putalpha(out_mask)
    res = Image.new("RGBA", (w, h + 12), (0, 0, 0, 0))
    res.alpha_composite(drop, (0, 10))
    res.alpha_composite(outline, (0, 0))
    res.alpha_composite(fill, (0, 0))
    res.alpha_composite(hlimg, (0, 0))
    return res, out_mask


def title(im, y_word, y_sub):
    f1 = F(TITLE_FONT, int(os.environ.get("TS", "230")))
    word, mask = gradient_text("Halloween", f1, PUMP_HI, (232, 96, 40), stroke=12)
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gm = Image.new("RGBA", mask.size, (255, 140, 50, 0)); gm.putalpha(mask.point(lambda v: int(v * 0.8)))
    x = (W - word.width) // 2
    glow.alpha_composite(gm, (x, y_word))
    im.alpha_composite(glow.filter(ImageFilter.GaussianBlur(28)))
    im.alpha_composite(word, (x, y_word))
    # "FESTIVAL" on a plum ribbon
    f2 = F("CinzelDecorative-Bold.ttf", 74)
    d = ImageDraw.Draw(im)
    txt = "Festival"
    tw = d.textlength(txt, font=f2)
    rw, rh = tw + 170, 104
    rx, ry = (W - rw) / 2, y_sub
    rib = Image.new("RGBA", (W, H), (0, 0, 0, 0)); rd = ImageDraw.Draw(rib)
    for side in (-1, 1):                                     # ribbon tails
        ex = rx - 70 if side < 0 else rx + rw + 70
        bx = rx + 30 if side < 0 else rx + rw - 30
        rd.polygon([(bx, ry + 22), (ex, ry + 22), (ex + side * -26, ry + rh / 2 + 22), (ex, ry + rh + 22), (bx, ry + rh + 22)],
                   fill=(58, 30, 84, 255))
    rd.rounded_rectangle((rx, ry, rx + rw, ry + rh), 18, fill=PLUM + (255,), outline=(255, 196, 110, 255), width=4)
    rd.rounded_rectangle((rx + 10, ry + 10, rx + rw - 10, ry + rh - 10), 12, outline=(255, 196, 110, 110), width=2)
    im.alpha_composite(rib)
    d = ImageDraw.Draw(im)
    d.text(((W - tw) / 2 + 3, ry + 14 + 4), txt, font=f2, fill=(20, 8, 30))
    d.text(((W - tw) / 2, ry + 14), txt, font=f2, fill=CREAM)
    for sx in (rx + 38, rx + rw - 38):                       # little stars on the ribbon
        star(d, sx, ry + rh / 2, 10, (255, 205, 120))


def star(d, x, y, r, col):
    pts = []
    for k in range(10):
        a = math.pi / 2 + k * math.pi / 5
        rr = r if k % 2 == 0 else r * 0.45
        pts.append((x + rr * math.cos(a), y - rr * math.sin(a)))
    d.polygon(pts, fill=col)


def spaced(d, text, f, y, fill, track):
    widths = [d.textlength(c, font=f) for c in text]
    total = sum(widths) + track * (len(text) - 1)
    x = (W - total) / 2
    for c, w in zip(text, widths):
        d.text((x + 2, y + 2), c, font=f, fill=(8, 4, 16)); d.text((x, y), c, font=f, fill=fill); x += w + track


# ---------------------------------------------------------------- compose
def compose():
    im = sky()
    moon(im, W // 2, 330, 150)
    hills(im, 700, 50, (42, 22, 58, 255), 1, trees=5, blur=1.5)
    mist(im, 720, 60)
    hills(im, 800, 40, (28, 14, 40, 255), 2, trees=4)
    mist(im, 820, 50)
    hills(im, 900, 22, (18, 8, 26, 255), 3)
    bunting(im, -20, 70)

    # pack pieces along the front
    # (module, piece, height px, lit, centre x, ground y)
    cast = [("hero3", "pumpkin_lamp", 540, True, 265, 1000),
            ("harvest", "pumpkin_pile", 150, False, 450, 1020),
            ("critters", "black_cat", 190, False, 600, 1015),
            ("harvest", "candy_bucket", 120, False, 960, 1040),
            ("graveyard", "tombstone", 190, False, 1330, 1010),
            ("hero3", "jack_o_lantern", 190, True, 1530, 1030),
            ("hero3", "cauldron", 230, True, 1755, 1010)]
    for mod, n, hgt, lit, cx, bot in cast:
        cam = (-0.62, 0.42, -1) if cx < W / 2 else (0.62, 0.42, -1)
        sp = piece(mod, n, 24, cam, lit)
        sp = sp.resize((max(1, round(sp.width * hgt / sp.height)), hgt), Image.NEAREST)
        if lit:
            glow_at(im, cx, bot - hgt * 0.5, max(sp.width, hgt) * 0.55)
        place(im, sp, cx, bot)

    title(im, 300, 560)
    d = ImageDraw.Draw(im)
    spaced(d, "MISTBLOOM STUDIOS PRESENTS", inter(28, "SemiBold"), 205, (255, 205, 130), 8)
    tag = "A Spooky-Cozy Halloween market for Nexo  ·  38 furniture pieces"
    f = inter(30, "Medium"); tw = d.textlength(tag, font=f)
    d.text(((W - tw) / 2 + 2, 700 + 2), tag, font=f, fill=(8, 4, 16)); d.text(((W - tw) / 2, 700), tag, font=f, fill=LILAC)
    mark = Image.open("/home/claude/mistbloom/brand/logo-v2/mistbloom-mark-transparent.png").convert("RGBA")
    mark = mark.crop(mark.getbbox()).resize((74, 74), Image.LANCZOS)
    im.alpha_composite(mark, (W - 110, H - 106))
    return im


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "halloween-festival-title.png")
    compose().convert("RGB").save(out)
    print(out)
