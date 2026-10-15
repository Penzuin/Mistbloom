"""Mistbloom logo set: flower mark + Blockbench-rendered title (Minecraft Title Generator, Block Serif)."""
import random, os, sys
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
TITLE = "/root/mtg/out_colour"
OUT = os.path.join(HERE, "out_colour"); os.makedirs(OUT, exist_ok=True)
NIGHT = (20, 26, 51)


def load(p):
    im = Image.open(p).convert("RGBA")
    return im.crop(im.getbbox())


def fit(im, w=None, h=None):
    s = min((w or 1e9) / im.width, (h or 1e9) / im.height)
    return im.resize((max(1, round(im.width * s)), max(1, round(im.height * s))), Image.LANCZOS)


def sky(W, H, seed=3, stars=True):
    im = Image.new("RGBA", (W, H), NIGHT + (255,))
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(g)
    d.ellipse((-W * .2, -H * .5, W * .55, H * .45), fill=(111, 91, 196, 70))
    d.ellipse((W * .55, -H * .4, W * 1.25, H * .4), fill=(78, 62, 154, 70))
    d.ellipse((W * .2, H * .55, W * .8, H * 1.2), fill=(242, 201, 125, 16))
    im.alpha_composite(g.filter(ImageFilter.GaussianBlur(W / 9)))
    m = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(m).ellipse((-W * .1, H * .78, W * 1.1, H * 1.15), fill=(120, 140, 210, 34))
    im.alpha_composite(m.filter(ImageFilter.GaussianBlur(W / 25)))
    if stars:
        rng = random.Random(seed); d = ImageDraw.Draw(im)
        for _ in range(int(W * H / 15000)):
            x, y = rng.uniform(0, W), rng.uniform(0, H * .7); r = rng.choice([1, 1.5, 2, 2.5]) * min(W, H) / 1100
            d.ellipse((x - r, y - r, x + r, y + r), fill=(243, 238, 255, rng.randint(60, 200)))
    return im


def shadow(base, im, xy, blur=18, off=14, alpha=120):
    s = Image.new("RGBA", base.size, (0, 0, 0, 0))
    k = Image.new("RGBA", im.size, (5, 8, 20, alpha)); k.putalpha(im.split()[3].point(lambda v: v * alpha // 255))
    s.alpha_composite(k, (xy[0], xy[1] + off))
    base.alpha_composite(s.filter(ImageFilter.GaussianBlur(blur)))
    base.alpha_composite(im, xy)


def glow(base, cx, cy, r, col=(242, 201, 125), a=70):
    g = Image.new("RGBA", base.size, (0, 0, 0, 0))
    ImageDraw.Draw(g).ellipse((cx - r, cy - r, cx + r, cy + r), fill=col + (a,))
    base.alpha_composite(g.filter(ImageFilter.GaussianBlur(r * .45)))


def stacked(W, H, mark, title, bg=True, mark_h=.42, title_w=.78, gap=.02):
    base = sky(W, H) if bg else Image.new("RGBA", (W, H), (0, 0, 0, 0))
    m = fit(mark, h=H * mark_h); t = fit(title, w=W * title_w)
    total = m.height + H * gap + t.height
    y0 = int((H - total) / 2)
    (shadow if bg else Image.Image.alpha_composite.__get__)  # noqa
    if bg:
        shadow(base, m, ((W - m.width) // 2, y0), off=0, alpha=60)
        shadow(base, t, ((W - t.width) // 2, int(y0 + m.height + H * gap)))
    else:
        base.alpha_composite(m, ((W - m.width) // 2, y0))
        base.alpha_composite(t, ((W - t.width) // 2, int(y0 + m.height + H * gap)))
    return base


def horizontal(W, H, mark, title, bg=True):
    base = sky(W, H) if bg else Image.new("RGBA", (W, H), (0, 0, 0, 0))
    m = fit(mark, h=H * .86); t = fit(title, w=W * .66, h=H * .8)
    gap = int(W * .015); total = m.width + gap + t.width
    x0 = (W - total) // 2
    put = shadow if bg else (lambda b, i, xy, **k: b.alpha_composite(i, xy))
    put(base, m, (x0, (H - m.height) // 2), off=0, alpha=60) if bg else put(base, m, (x0, (H - m.height) // 2))
    put(base, t, (x0 + m.width + gap, (H - t.height) // 2))
    return base


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "test"
    title = load(f"{TITLE}/col_title.png")
    smooth = load(os.path.join(HERE, "mark_2000.png"))
    px = smooth  # original flower mark, unchanged
    if which == "all":
        O = lambda n: os.path.join(OUT, n)
        stacked(2400, 1800, px, title).convert("RGB").save(O("mistbloom-logo-primary.png"))
        stacked(2400, 1800, px, title, bg=False).save(O("mistbloom-logo-transparent.png"))
        horizontal(3000, 900, px, title).convert("RGB").save(O("mistbloom-logo-horizontal.png"))
        horizontal(3000, 900, px, title, bg=False).save(O("mistbloom-logo-horizontal-transparent.png"))
        t = Image.new("RGBA", (title.width + 80, title.height + 80), (0, 0, 0, 0)); t.alpha_composite(title, (40, 40))
        t.save(O("mistbloom-wordmark-transparent.png"))
        mk = Image.new("RGBA", (2000, 2000), (0, 0, 0, 0)); mm = fit(px, h=1800); mk.alpha_composite(mm, ((2000 - mm.width) // 2, (2000 - mm.height) // 2))
        mk.save(O("mistbloom-mark-transparent.png"))
        S = 1024
        av = sky(S, S, seed=7, stars=True)
        mm = fit(px, h=S * .7); av.alpha_composite(mm, ((S - mm.width) // 2, (S - mm.height) // 2))
        circ = Image.new("L", (S, S), 0); ImageDraw.Draw(circ).ellipse((0, 0, S - 1, S - 1), fill=255)
        av.convert("RGB").save(O("mistbloom-avatar-square.png"))
        av.putalpha(circ); av.save(O("mistbloom-avatar-round.png"))
        # small-size check sheet
        sheet = sky(1800, 700, stars=False); d = ImageDraw.Draw(sheet)
        x = 40
        for w in (600, 360, 200, 120):
            im = fit(stacked(2400, 1800, px, title, bg=False), w=w)
            sheet.alpha_composite(im, (x, 60)); x += w + 40
        x = 40
        for s_ in (256, 128, 64, 32):
            a2 = Image.open(O("mistbloom-avatar-round.png")).resize((s_, s_), Image.LANCZOS)
            sheet.alpha_composite(a2, (x, 520 - s_ // 2 + 60)); x += s_ + 40
        h2 = fit(horizontal(3000, 900, px, title, bg=False), w=700); sheet.alpha_composite(h2, (1060, 480))
        sheet.convert("RGB").save(O("mistbloom-size-check.png"))
        print("exported")
    if which == "test":
        a = stacked(1600, 1200, smooth, title); b = stacked(1600, 1200, px, title)
        s = Image.new("RGBA", (3240, 1200), (0, 0, 0, 255)); s.alpha_composite(a, (0, 0)); s.alpha_composite(b, (1640, 0))
        s.convert("RGB").save(os.path.join(OUT, "test_marks.png"))
