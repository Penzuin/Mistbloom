import random, math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
W, H = 1500, 500
y = np.linspace(0, 1, H)[:, None]
top, bot = np.array([20, 26, 51]), np.array([58, 44, 112])
img = (top + (bot - top) * y ** 1.3)
img = np.repeat(img[:, None, :], W, 1).reshape(H, W, 3)
im = Image.fromarray(img.astype(np.uint8)).convert("RGBA")
d = ImageDraw.Draw(im); rng = random.Random(5)
for _ in range(170):
    x, yy = rng.uniform(0, W), rng.uniform(0, H) ** 1.5 / H ** 0.5
    r = rng.choice((0.8, 1, 1, 1.4)); a = rng.randint(90, 220)
    d.ellipse((x - r, yy - r, x + r, yy + r), fill=(246, 241, 231, a))
mist = Image.new("RGBA", (W, H), (0, 0, 0, 0)); md = ImageDraw.Draw(mist)
md.ellipse((-200, H - 150, W + 200, H + 160), fill=(159, 179, 217, 70))
im.alpha_composite(mist.filter(ImageFilter.GaussianBlur(40)))
glow = Image.new("RGBA", (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(glow)
gd.ellipse((560, 60, 1060, 400), fill=(242, 201, 125, 40))
im.alpha_composite(glow.filter(ImageFilter.GaussianBlur(80)))
logo = Image.open("/home/claude/mistbloom/brand/logo-v2/mistbloom-logo-horizontal-transparent.png")
logo = logo.crop(logo.getbbox())
lw = 640; logo = logo.resize((lw, round(logo.height * lw / logo.width)), Image.LANCZOS)
im.alpha_composite(logo, (810 - lw // 2, 205 - logo.height // 2))
# a few pack pieces on the right, same renders as the store icon
R = "/home/claude/hollow/thumb/r"
for name, cx, by, h in (("jack_o_lantern_lit", 1255, 455, 120), ("pumpkin_lamp_lit", 1395, 470, 300), ("black_cat", 1160, 465, 105),
                         ("candy_bucket", 1320, 480, 80)):
    p = Image.open(f"{R}/{name}.png"); p = p.crop(p.getbbox())
    p = p.resize((round(p.width * h / p.height), h), Image.LANCZOS)
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).ellipse((cx - p.width * .45, by - 10, cx + p.width * .45, by + 8), fill=(10, 8, 30, 120))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(6)))
    im.alpha_composite(p, (int(cx - p.width / 2), by - h))
im.convert("RGB").save("mistbloom-x-banner.png")
a = Image.open("/home/claude/mistbloom/brand/logo-v2/mistbloom-avatar-square.png").resize((400, 400), Image.LANCZOS)
a.save("mistbloom-x-avatar.png")
print("ok")
