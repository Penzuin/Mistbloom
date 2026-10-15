"""Moonlit Ballroom title slide (PNG) + 5 s animated version (MP4), Mistbloom style."""
import math, os, random, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
sys.path.insert(0, "/home/claude/ghostball")
import sprites as S
from build import night_bg, font, sans, GOLD, PARCH, PETAL

W, H, FPS, DUR = 1920, 1080, 30, 5.0
HERE = os.path.dirname(os.path.abspath(__file__))
MARK = Image.open("/home/claude/mistbloom/brand/logo-v2/mistbloom-mark-transparent.png").convert("RGBA")
MARK = MARK.crop(MARK.getbbox()).resize((74, 74), Image.LANCZOS)

COUPLE = [Image.fromarray(S.waltz(620, 620, k)) for k in range(8)]
NOTES = [Image.fromarray(S.notes(150, 180, k)) for k in range(8)]

def arch_layer():
    """A tall lancet window of moonlight behind the dancers: the ballroom's own window shape."""
    cx, hw, spring, bot = W / 2, 330, 700, 1080
    R = hw * 1.3
    cl = cx - hw + R                                          # centre of the left arc
    a_apex = math.acos((cx - cl) / R)
    left = [(cl + R * math.cos(t), spring - R * math.sin(t)) for t in np.linspace(math.pi, a_apex, 40)]
    right = [(2 * cx - x, y) for x, y in reversed(left)]
    outline = [(cx - hw, bot)] + left + right + [(cx + hw, bot)]
    L = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(L).polygon(outline, fill=(150, 120, 220, 60))
    out = L.filter(ImageFilter.GaussianBlur(45))
    out.alpha_composite(L.filter(ImageFilter.GaussianBlur(4)))
    fr = Image.new("RGBA", (W, H), (0, 0, 0, 0)); fd = ImageDraw.Draw(fr)
    fd.line(outline, fill=(201, 184, 240, 110), width=4, joint="curve")
    inner = [(cx + (x - cx) * 0.94, y + 16) for x, y in outline]
    fd.line(inner, fill=(242, 201, 125, 60), width=2, joint="curve")
    out.alpha_composite(fr)
    return out

BG = night_bg(W, H, seed=11, moon=True)
BG.alpha_composite(arch_layer())
mist = Image.new("RGBA", (W, H), (0, 0, 0, 0))
ImageDraw.Draw(mist).ellipse((-200, H - 190, W + 200, H + 220), fill=(159, 179, 217, 60))
BG.alpha_composite(mist.filter(ImageFilter.GaussianBlur(50)))
rng = random.Random(3)
TWINK = [(rng.uniform(0, W), rng.uniform(0, H * .6), rng.uniform(0, 6.28), rng.uniform(1.5, 3.5)) for _ in range(40)]

def spaced(d, text, f, y, fill, track):
    widths = [d.textlength(c, font=f) for c in text]
    total = sum(widths) + track * (len(text) - 1)
    x = (W - total) / 2
    for c, w in zip(text, widths):
        d.text((x + 2, y + 2), c, font=f, fill=(8, 6, 24)); d.text((x, y), c, font=f, fill=fill); x += w + track

def title_text(im, a=1.0):
    t = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(t)
    spaced(d, "MISTBLOOM STUDIOS PRESENTS", sans(26), 70, GOLD, 9)
    f = font(150); txt = "Moonlit Ballroom"
    tw = d.textlength(txt, font=f); x = (W - tw) / 2
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(sh).text((x, 112), txt, font=f, fill=(242, 201, 125, 150))
    t.alpha_composite(sh.filter(ImageFilter.GaussianBlur(18)))
    d.text((x + 4, 118), txt, font=f, fill=(8, 6, 24)); d.text((x, 112), txt, font=f, fill=PARCH)
    spaced(d, "friendly ghosts that waltz all night", sans(30), 975, PETAL, 2)
    d2 = ImageDraw.Draw(t)
    sub = "A Halloween furniture pack for Nexo"
    tw = d2.textlength(sub, font=sans(22)); d2.text(((W - tw) / 2, 1020), sub, font=sans(22), fill=(185, 176, 214))
    if a < 1:
        t.putalpha(t.split()[3].point(lambda v: int(v * a)))
    im.alpha_composite(t)

def frame(t, still=False):
    im = BG.copy(); d = ImageDraw.Draw(im)
    for x, y, ph, sp in TWINK:
        r = 2.2 + 1.2 * math.sin(ph + t * sp)
        S.sparkle(d, x, y, 2 + 4 * max(0, math.sin(ph + t * sp)), a=200)
    k = 0 if still else int(t / 0.15) % 8
    c = COUPLE[k]; bob = 0 if still else int(6 * math.sin(t * 2.1))
    im.alpha_composite(c, ((W - c.width) // 2, 370 + bob))
    n = NOTES[k]
    im.alpha_composite(n, (W // 2 + 150, 350 + int(8 * math.sin(t * 1.7))))
    a = 1 if still else max(0.0, min(1.0, (t - 0.3) / 0.9))
    title_text(im, a)
    im.alpha_composite(MARK, (W - 110, H - 106))
    if not still:
        fo = max(0.0, min(1.0, (t - (DUR - 0.5)) / 0.5))
        if fo: im.alpha_composite(Image.new("RGBA", (W, H), (10, 12, 26, int(255 * fo))))
    return im.convert("RGB")

if __name__ == "__main__":
    frame(0, still=True).save(os.path.join(HERE, "moonlit-ballroom-title.png"))
    fd = os.path.join(HERE, "tframes"); os.makedirs(fd, exist_ok=True)
    for i in range(int(DUR * FPS)):
        frame(i / FPS).save(f"{fd}/f{i:04d}.png")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", f"{fd}/f%04d.png", "-c:v", "libx264",
                    "-pix_fmt", "yuv420p", "-crf", "16", "-preset", "slow", "-movflags", "+faststart",
                    os.path.join(HERE, "moonlit-ballroom-title.mp4")], check=True)
    print("ok")
