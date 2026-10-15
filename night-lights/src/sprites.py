"""Night Lights sprites (Mistbloom Studios): drawn at 4x, box-downsampled to texel size.

Glowing night things with one strong, simple shape. No faces (user: the sleepy faces were
not meant for everything).
Every sprite is an 8-frame loop at 3 ticks a frame, like the other Mistbloom packs.
"""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

SS = 4
STAR = (255, 228, 140)
STAR_SH = (238, 182, 92)
STAR_HI = (255, 248, 214)
MOON = (250, 240, 200)
MOON_SH = (222, 200, 150)
JELLY = (196, 172, 248)
JELLY_HI = (236, 226, 255)
JELLY_DEEP = (150, 120, 220)


def _canvas(w, h):
    return Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))


def _finish(im, w, h, glow=0.0, col=(255, 236, 170), lit=True):
    """Soft halo round the shape (kept clear of the card edges), then downsample."""
    if glow and lit:
        a = im.split()[3].filter(ImageFilter.GaussianBlur(2.2 * SS))
        halo = Image.new("RGBA", im.size, col + (0,))
        halo.putalpha(a.point(lambda v: int(v * glow)))
        halo.alpha_composite(im)
        im = halo
    arr = np.array(im.resize((w, h), Image.BOX), np.uint8)
    a = arr[..., 3].astype(float)
    a[a < 14] = 0                                    # no faint wash reaching the edges (pack standard)
    a[0, :] = a[-1, :] = 0
    a[:, 0] = a[:, -1] = 0
    arr[..., 3] = a.astype(np.uint8)
    return arr


def _star_pts(cx, cy, R, r, rot=-90, round_=0.0):
    pts = []
    for i in range(10):
        ang = math.radians(rot + i * 36)
        rad = R if i % 2 == 0 else r
        pts.append((cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
    return pts


def _twinkle(d, x, y, r, a):
    d.polygon([(x, y - r), (x + r * 0.28, y - r * 0.28), (x + r, y), (x + r * 0.28, y + r * 0.28),
               (x, y + r), (x - r * 0.28, y + r * 0.28), (x - r, y), (x - r * 0.28, y - r * 0.28)],
              fill=(255, 250, 224, a))


def _spark(w, h, k, phase, n=8):
    im = _canvas(w, h)
    d = ImageDraw.Draw(im)
    W, H = w * SS, h * SS
    on = (k + phase) % 4
    r = W * (0.40, 0.30, 0.18, 0.0)[on]
    if r > 0:
        _twinkle(d, W / 2, H / 2, r, 240)
    return _finish(im, w, h, glow=0.5)


def twinkle_a(w, h, k, n=8):
    return _spark(w, h, k, 0)


def twinkle_b(w, h, k, n=8):
    return _spark(w, h, k, 2)


def tentacles(w, h, k, n=8, lit=True):
    """Four soft ribbons drifting under the jelly's bell; they fade out before the card's edges."""
    im = _canvas(w, h)
    d = ImageDraw.Draw(im)
    W, H = w * SS, h * SS
    th = 2 * math.pi * k / n
    for j, off in enumerate((-0.30, -0.10, 0.10, 0.30)):
        x0 = W / 2 + off * W
        pts = [(x0 + math.sin(th + t * 5 + j) * W * 0.05 * t, H * 0.02 + t * H * 0.86) for t in np.linspace(0, 1, 14)]
        col = (JELLY if j % 2 else JELLY_DEEP) + (int(230 if lit else 170),)
        d.line(pts, fill=col, width=max(2, int(W / 18)))
    arr = _finish(im, w, h, glow=0.4 if lit else 0, col=(206, 190, 255), lit=lit)
    fade = np.linspace(1, 0, arr.shape[0]) ** 0.6                          # thin out towards the tips
    arr[..., 3] = (arr[..., 3] * fade[:, None]).astype(np.uint8)
    return arr


def tentacles_unlit(w, h, k, n=8):
    return tentacles(w, h, k, n, lit=False)
