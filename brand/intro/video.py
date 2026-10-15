"""Mistbloom Studios intro card, 1920x1080 @30fps, timed to the sonic logo (logo hit at 1.45 s)."""
import math, os, random, subprocess, sys
from PIL import Image, ImageDraw, ImageFilter

W, H, FPS, DUR, HIT = 1920, 1080, 30, 4.6, 1.45
B = "/home/claude/mistbloom/brand/logo-v2/"
OUT = sys.argv[1] if len(sys.argv) > 1 else "frames"
os.makedirs(OUT, exist_ok=True)
NIGHT = (20, 26, 51)

def fit(im, w=None, h=None):
    s = min((w or 1e9) / im.width, (h or 1e9) / im.height)
    return im.resize((max(1, round(im.width * s)), max(1, round(im.height * s))), Image.LANCZOS)

def crop(im):
    return im.crop(im.getbbox())

mark = fit(crop(Image.open(B + "mistbloom-mark-transparent.png").convert("RGBA")), h=470)
word = fit(crop(Image.open(B + "mistbloom-wordmark-transparent.png").convert("RGBA")), w=1060)

def sky():
    im = Image.new("RGBA", (W, H), NIGHT + (255,))
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(g)
    d.ellipse((-W * .2, -H * .5, W * .55, H * .45), fill=(111, 91, 196, 70))
    d.ellipse((W * .55, -H * .4, W * 1.25, H * .4), fill=(78, 62, 154, 70))
    d.ellipse((W * .2, H * .55, W * .8, H * 1.2), fill=(242, 201, 125, 16))
    im.alpha_composite(g.filter(ImageFilter.GaussianBlur(W / 9)))
    return im
BG = sky()
rng = random.Random(5)
STARS = [(rng.uniform(0, W), rng.uniform(0, H * .75), rng.choice([1.2, 1.6, 2.2, 2.8]), rng.uniform(0, 6.28), rng.uniform(1.5, 4))
         for _ in range(150)]
MIST = Image.new("RGBA", (W * 2, 420), (0, 0, 0, 0))
dm = ImageDraw.Draw(MIST)
for k in range(9):
    x = k * W * 2 / 8 - 200
    dm.ellipse((x, 120 + 60 * math.sin(k), x + 900, 380), fill=(159, 179, 217, 46))
MIST = MIST.filter(ImageFilter.GaussianBlur(60))

def ease(x):
    x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)

def alpha(im, a):
    if a >= 1: return im
    c = im.copy(); c.putalpha(c.split()[3].point(lambda v: int(v * a))); return c

def frame(i):
    t = i / FPS
    im = BG.copy(); d = ImageDraw.Draw(im)
    sa = ease(t / 0.8)
    for x, y, r, ph, sp in STARS:
        a = int(sa * (90 + 110 * (0.5 + 0.5 * math.sin(ph + t * sp))))
        d.ellipse((x - r, y - r, x + r, y + r), fill=(243, 238, 255, a))
    # mist drifting along the bottom
    m = alpha(MIST, 0.4 + 0.6 * ease(t / 1.2))
    im.alpha_composite(m, (int(-W * 0.5 + 40 * t), H - 380))
    # lantern glow behind the flower, pulses on the hit
    cx, cy = W // 2, 400
    pulse = math.exp(-max(0, t - HIT) / 0.5) if t >= HIT else 0
    ga = 40 * ease((t - 0.3) / 1.1) + 70 * pulse
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    rr = 260 + 60 * pulse
    ImageDraw.Draw(g).ellipse((cx - rr, cy - rr, cx + rr, cy + rr), fill=(242, 201, 125, int(ga)))
    im.alpha_composite(g.filter(ImageFilter.GaussianBlur(110)))
    # flower blooms: rises and opens from 0.4 s, settles on the hit
    p = ease((t - 0.35) / (HIT - 0.35))
    s = 0.82 + 0.18 * p + 0.03 * pulse
    mk = fit(mark, h=int(mark.height * s))
    mk = alpha(mk, p)
    im.alpha_composite(mk, (cx - mk.width // 2, int(cy - mk.height // 2 + 30 * (1 - p))))
    # sparkle burst at the hit
    if t >= HIT:
        k = (t - HIT) / 0.9
        if k < 1:
            sp = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ds = ImageDraw.Draw(sp)
            for j in range(10):
                ang = j * 2 * math.pi / 10 + 0.3
                rad = 180 + 260 * ease(k)
                x, y = cx + rad * math.cos(ang), cy + rad * 0.75 * math.sin(ang)
                r = 14 * (1 - k)
                ds.polygon([(x, y - r), (x + r * .3, y - r * .3), (x + r, y), (x + r * .3, y + r * .3), (x, y + r),
                            (x - r * .3, y + r * .3), (x - r, y), (x - r * .3, y - r * .3)], fill=(255, 240, 200, int(230 * (1 - k))))
            im.alpha_composite(sp)
    # wordmark rises in just after the hit
    q = ease((t - HIT + 0.05) / 0.55)
    if q > 0:
        wm = alpha(word, q)
        im.alpha_composite(wm, (W // 2 - wm.width // 2, int(700 + 26 * (1 - q))))
    # fade out to night at the end
    fo = ease((t - (DUR - 0.55)) / 0.55)
    if fo > 0:
        im.alpha_composite(Image.new("RGBA", (W, H), (10, 12, 26, int(255 * fo))))
    return im.convert("RGB")

for i in range(int(DUR * FPS)):
    frame(i).save(f"{OUT}/f{i:04d}.png")
print("frames", int(DUR * FPS))
