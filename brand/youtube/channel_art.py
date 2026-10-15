"""Mistbloom Studios YouTube channel art: banner (2560x1440, logo inside the 1546x423 safe area),
profile picture (800x800) and video watermark (150x150)."""
import math, os, random, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
sys.path.insert(0, "/home/claude/ghostball")
import pieces as P

B = "/home/claude/mistbloom/brand/logo-v2/"
OUT = "/home/claude/ghostball/youtube/"
W, H = 2560, 1440
SAFE = ((W - 1546) // 2, (H - 423) // 2, (W + 1546) // 2, (H + 423) // 2)   # visible on every device
DESK = (0, SAFE[1], W, SAFE[3])                                             # visible on desktop
NIGHT = (20, 26, 51)

def crop(im): return im.crop(im.getbbox())
def fit(im, w=None, h=None):
    s = min((w or 1e9) / im.width, (h or 1e9) / im.height)
    return im.resize((max(1, round(im.width * s)), max(1, round(im.height * s))), Image.LANCZOS)

def sky():
    im = Image.new("RGBA", (W, H), NIGHT + (255,))
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(g)
    d.ellipse((-W * .15, -H * .2, W * .45, H * .75), fill=(111, 91, 196, 60))
    d.ellipse((W * .6, -H * .1, W * 1.2, H * .7), fill=(78, 62, 154, 70))
    d.ellipse((W * .3, H * .45, W * .7, H * .85), fill=(242, 201, 125, 18))
    im.alpha_composite(g.filter(ImageFilter.GaussianBlur(W / 10)))
    rng = random.Random(9); d = ImageDraw.Draw(im)
    for _ in range(520):
        x, y = rng.uniform(0, W), rng.uniform(0, H)
        r = rng.choice([1.2, 1.6, 2.2, 2.8])
        d.ellipse((x - r, y - r, x + r, y + r), fill=(243, 238, 255, rng.randint(70, 210)))
    for _ in range(14):                                   # a few four-point twinkles
        x, y = rng.uniform(0, W), rng.uniform(0, H * .9); r = rng.uniform(6, 12)
        d.polygon([(x, y - r), (x + r * .25, y - r * .25), (x + r, y), (x + r * .25, y + r * .25), (x, y + r),
                   (x - r * .25, y + r * .25), (x - r, y), (x - r * .25, y - r * .25)], fill=(255, 236, 190, 170))
    mist = Image.new("RGBA", (W, H), (0, 0, 0, 0)); md = ImageDraw.Draw(mist)
    for k in range(7):
        x = k * W / 6 - 300
        md.ellipse((x, SAFE[3] - 120 + 40 * math.sin(k * 1.7), x + 900, SAFE[3] + 160), fill=(159, 179, 217, 40))
    im.alpha_composite(mist.filter(ImageFilter.GaussianBlur(60)))
    return im

def banner():
    im = sky()
    # logo in the safe area
    logo = fit(crop(Image.open(B + "mistbloom-logo-horizontal-transparent.png").convert("RGBA")), w=1120, h=300)
    lx, ly = (W - logo.width) // 2, SAFE[1] + 26
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); a = logo.split()[3].point(lambda v: v * 0.5)
    sl = Image.new("RGBA", logo.size, (5, 8, 20, 255)); sl.putalpha(a); sh.alpha_composite(sl, (lx, ly + 12))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14)))
    im.alpha_composite(logo, (lx, ly))
    f = ImageFont.truetype("/usr/share/fonts/truetype/google-fonts/Poppins-Medium.ttf", 40)
    d = ImageDraw.Draw(im)
    txt = "Cozy fantasy furniture, cosmetics & menus for Minecraft servers"
    tw = d.textlength(txt, font=f)
    d.text(((W - tw) / 2 + 2, ly + logo.height + 22 + 2), txt, font=f, fill=(8, 6, 24))
    d.text(((W - tw) / 2, ly + logo.height + 22), txt, font=f, fill=(214, 204, 240))
    # pack pieces at the desktop edges (outside the phone crop, inside the desktop band)
    ms = {m.name: m for m in P.all_models()}
    left = [("floating_candelabra_lit", 260), ("ghost_lantern_lit", 170), ("wisp", 170)]
    right = [("ghost_piano", 270), ("waltzing_ghosts", 230)]
    x = 70
    for name, h in left:
        r = fit(crop(ms[name].render(ppu=14, frame=1)), h=h)
        im.alpha_composite(r, (x, SAFE[3] - r.height - 30)); x += r.width + 20
    x = W - 70
    for name, h in right:
        r = fit(crop(ms[name].render(ppu=14, frame=1)), h=h)
        x -= r.width
        im.alpha_composite(r, (x, SAFE[3] - r.height - 30)); x -= 20
    return im.convert("RGB")

def avatar():
    a = Image.open(B + "mistbloom-avatar-square.png").convert("RGB")
    return a.resize((800, 800), Image.LANCZOS)

def watermark():
    S = 600
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.ellipse((10, 10, S - 10, S - 10), fill=NIGHT + (235,), outline=(201, 184, 240, 255), width=18)
    mk = fit(crop(Image.open(B + "mistbloom-mark-transparent.png").convert("RGBA")), w=S * .62, h=S * .62)
    im.alpha_composite(mk, ((S - mk.width) // 2, (S - mk.height) // 2))
    return im.resize((150, 150), Image.LANCZOS)

if __name__ == "__main__":
    b = banner(); b.save(OUT + "mistbloom-yt-banner.png", optimize=True)
    avatar().save(OUT + "mistbloom-yt-avatar.png")
    watermark().save(OUT + "mistbloom-yt-watermark.png")
    # preview with the safe area marked
    p = b.copy(); d = ImageDraw.Draw(p)
    d.rectangle(SAFE, outline=(255, 80, 80), width=6); d.rectangle(DESK, outline=(80, 255, 120), width=4)
    p.resize((1280, 720)).save(OUT + "banner_guides.png")
    print([os.path.getsize(OUT + n) for n in ("mistbloom-yt-banner.png", "mistbloom-yt-avatar.png", "mistbloom-yt-watermark.png")])
