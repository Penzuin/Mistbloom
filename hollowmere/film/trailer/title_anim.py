"""Animated Halloween Festival title for the trailer: slow push-in, twinkling stars, title fades in."""
import math, os, random, sys, subprocess
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, "/home/claude/hollow/title")
import title as T

FPS, DUR = 60, 5.5
full = T.compose()
_title, _spaced = T.title, T.spaced
T.title = lambda *a, **k: None
T.spaced = lambda *a, **k: None
ImageDraw.ImageDraw._text_orig = ImageDraw.ImageDraw.text
base = None
def _no_tag(self, xy, text, *a, **k):          # also hide the tagline on the base layer
    if "Spooky-Cozy" in str(text): return
    return self._text_orig(xy, text, *a, **k)
ImageDraw.ImageDraw.text = _no_tag
base = T.compose()
ImageDraw.ImageDraw.text = ImageDraw.ImageDraw._text_orig
W, H = full.size
rng = random.Random(9)
stars = [(rng.uniform(0, W), rng.uniform(0, H * 0.55), rng.uniform(0, 6.28), rng.uniform(1.2, 3.0)) for _ in range(46)]

def frame(t):
    a = min(1.0, max(0.0, (t - 0.35) / 1.0)); a = a * a * (3 - 2 * a)
    im = Image.blend(base, full, a)
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    for x, y, ph, sp in stars:
        v = max(0.0, math.sin(ph + t * sp)) ** 3
        if v > 0.05:
            r = 1 + 2.5 * v
            d.line((x - r * 2, y, x + r * 2, y), fill=(255, 240, 210, int(200 * v)), width=1)
            d.line((x, y - r * 2, x, y + r * 2), fill=(255, 240, 210, int(200 * v)), width=1)
            d.ellipse((x - 1.5, y - 1.5, x + 1.5, y + 1.5), fill=(255, 248, 230, int(255 * v)))
    im.alpha_composite(ov)
    z = 1.0 + 0.035 * (t / DUR)                      # gentle push-in
    cw, ch = W / z, H / z
    im = im.crop(((W - cw) / 2, (H - ch) / 2 + (H - ch) * 0.1, (W + cw) / 2, (H + ch) / 2 + (H - ch) * 0.1))
    return im.resize((W, H), Image.LANCZOS).convert("RGB")

if __name__ == "__main__":
    out = sys.argv[1]
    os.makedirs("tframes", exist_ok=True)
    for i in range(int(DUR * FPS)):
        frame(i / FPS).save(f"tframes/f{i:04d}.png")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-framerate", str(FPS), "-i", "tframes/f%04d.png", "-c:v", "libx264",
                    "-pix_fmt", "yuv420p", "-crf", "14", "-preset", "medium", out], check=True)
    print(out)
