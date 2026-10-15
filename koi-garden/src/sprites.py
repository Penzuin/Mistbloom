"""16x16 hand-drawn item icons (sprite16 style): per-part auto shading from the top-left,
1-px outline in the darkest step of the neighbouring material's own hue, no extras."""
import math
import numpy as np
from PIL import Image, ImageDraw
from engine import ANCH

RAMP = {m: v for m, v in ANCH.items()}  # (highlight, base, shade, outline)
REG = {}

def sp(name):
    def d(f):
        REG[name] = f; return f
    return d

def _rgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))

class Sprite:
    def __init__(self):
        self.part = np.full((16, 16), -1, int)
        self.mat = np.full((16, 16), '', object)
        self.force = {}
        self.n = 0

    def _put(self, mask, m):
        self.n += 1
        self.part[mask] = self.n; self.mat[mask] = m
        for (x, y) in list(self.force):
            if mask[y, x]: del self.force[(x, y)]

    def R(self, x0, y0, x1, y1, m):
        k = np.zeros((16, 16), bool); k[max(0, y0):y1 + 1, max(0, x0):x1 + 1] = True; self._put(k, m)

    def E(self, cx, cy, rx, ry, m, hole=None):
        yy, xx = np.mgrid[0:16, 0:16] + 0.5
        k = ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2 <= 1
        if hole: k &= ((xx - cx) / hole[0]) ** 2 + ((yy - cy) / hole[1]) ** 2 > 1
        self._put(k, m)

    def P(self, pts, m):
        im = Image.new('L', (16, 16), 0); ImageDraw.Draw(im).polygon(pts, fill=1)
        self._put(np.array(im).astype(bool), m)

    def C(self, pts, m, w=1):
        k = np.zeros((16, 16), bool)
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            n = int(math.ceil(max(abs(x1 - x0), abs(y1 - y0)))) + 1
            for i in range(n):
                t = i / max(n - 1, 1)
                x = x0 + (x1 - x0) * t; y = y0 + (y1 - y0) * t
                for dx in range(w):
                    for dy in range(w):
                        xi, yi = int(round(x - (w - 1) / 2 + dx)), int(round(y - (w - 1) / 2 + dy))
                        if 0 <= xi < 16 and 0 <= yi < 16: k[yi, xi] = True
        self._put(k, m)

    def L(self, x0, y0, x1, y1, m, w=1):
        self.C([(x0, y0), (x1, y1)], m, w)

    def D(self, x, y, m, t=1):
        if 0 <= x < 16 and 0 <= y < 16:
            if self.part[y, x] < 0:
                self.n += 1; self.part[y, x] = self.n
            self.mat[y, x] = m; self.force[(x, y)] = t

    def clear(self, x, y):
        self.part[y, x] = -1; self.mat[y, x] = ''; self.force.pop((x, y), None)

    def image(self):
        out = np.zeros((16, 16, 4), np.uint8)
        P = self.part
        def same(x, y, p):
            return 0 <= x < 16 and 0 <= y < 16 and P[y, x] == p
        for y in range(16):
            for x in range(16):
                p = P[y, x]
                if p < 0: continue
                m = self.mat[y, x]
                tl = not same(x, y - 1, p) or not same(x - 1, y, p)
                br = not same(x, y + 1, p) or not same(x + 1, y, p)
                t = 1
                if tl and not br: t = 0
                elif br and not tl: t = 2
                if (x, y) in self.force: t = self.force[(x, y)]
                out[y, x, :3] = _rgb(RAMP[m][t]); out[y, x, 3] = 255
        for y in range(16):
            for x in range(16):
                if P[y, x] >= 0: continue
                for dx, dy in ((0, 1), (1, 0), (0, -1), (-1, 0)):
                    xx, yy = x + dx, y + dy
                    if 0 <= xx < 16 and 0 <= yy < 16 and P[yy, xx] >= 0:
                        out[y, x, :3] = _rgb(RAMP[self.mat[yy, xx]][3]); out[y, x, 3] = 255
                        break
        return Image.fromarray(out, 'RGBA')

# ------------------------------------------------------------ helpers
def koi(s, x, y, ln=8, d=1, pat='kohaku'):
    """small horizontal koi; (x,y) = nose; d=+1 swims right (nose at x), -1 swims left."""
    base = {'kohaku': 'kwhite', 'sanke': 'kwhite', 'showa': 'kblack', 'chagoi': 'korange', 'magoi': 'kblack'}[pat]
    bx = x - d * (ln * 0.45)
    s.E(bx + 0.5, y + 0.5, ln * 0.45, 1.6, base)
    tx = x - d * ln
    s.P([(tx + d * 1.5 + 0.5, y + 0.5), (tx - d * 0.6 + 0.5, y - 1.6), (tx - d * 0.6 + 0.5, y + 2.6)], base if pat != 'showa' else 'kwhite')
    if pat in ('kohaku', 'sanke', 'showa'):
        s.D(x - d * 1, y, 'korange', 1); s.D(x - d * 1, y - 1 + 1, 'korange', 0)
        s.D(x - d * 4, y - 1 + 1, 'korange', 1); s.D(x - d * 5, y, 'korange', 1)
    if pat == 'sanke': s.D(x - d * 3, y, 'kblack', 1)
    if pat == 'showa': s.D(x - d * 3, y + 1, 'kwhite', 0); s.D(x - d * 5, y + 1, 'kwhite', 1)
    s.D(int(x - d * 1), y - 1 if False else y, 'kblack' if pat != 'showa' else 'kwhite', 2)

# ------------------------------------------------------------ icons
@sp('koi_statue')
def _(s):
    s.R(3, 14, 12, 15, 'stone'); s.R(5, 10, 10, 13, 'stone'); s.R(4, 9, 11, 9, 'stone')
    s.P([(4, 9), (6, 6), (8, 8), (10, 6), (12, 9)], 'water')
    s.D(6, 6, 'kwhite', 0); s.D(10, 6, 'kwhite', 0)
    s.P([(5, 7), (10, 2), (12, 1), (14, 2), (13, 4), (8, 9)], 'kwhite')
    s.P([(6, 8), (2, 7), (4, 11)], 'kwhite')
    s.P([(9, 3), (11, 2), (12, 3), (10, 5)], 'korange'); s.P([(6, 6), (8, 5), (9, 6), (7, 8)], 'korange')
    s.D(12, 3, 'kblack', 2)

@sp('koi_lilypad')
def _(s):
    s.E(8, 11, 7, 4, 'lily'); s.clear(14, 11); s.clear(13, 11)
    s.D(8, 11, 'lily', 2); s.D(5, 10, 'lily', 2); s.D(10, 12, 'lily', 2)
    s.E(10, 6, 2.5, 2.5, 'pink'); s.D(10, 6, 'yellow', 0); s.D(9, 5, 'pink', 0)
    koi(s, 2, 10, 9, -1, 'sanke')

@sp('koi_bowl')
def _(s):
    s.R(2, 12, 13, 12, 'teak'); s.R(3, 13, 4, 15, 'teak'); s.R(11, 13, 12, 15, 'teak')
    s.R(3, 4, 12, 11, 'glass'); s.R(4, 6, 11, 11, 'water')
    s.R(3, 3, 12, 3, 'brass')
    koi(s, 10, 8, 6, 1, 'chagoi')
    s.D(4, 5, 'glass', 0); s.D(4, 7, 'glass', 0)

@sp('koi_plaque')
def _(s):
    s.C([(4, 4), (8, 1), (12, 4)], 'rope'); s.D(8, 1, 'brass', 0)
    s.R(1, 4, 14, 5, 'teak'); s.R(2, 6, 13, 13, 'teak'); s.R(1, 14, 14, 14, 'teak')
    koi(s, 4, 8, 8, -1, 'kohaku')
    koi(s, 12, 11, 8, 1, 'showa')

@sp('koi_pond')
def _(s):
    s.R(1, 4, 14, 14, 'stone'); s.R(3, 6, 12, 12, 'water')
    s.D(1, 4, 'moss', 1); s.D(2, 4, 'moss', 0); s.D(13, 14, 'moss', 2); s.D(14, 4, 'moss', 1)
    koi(s, 11, 8, 7, 1, 'kohaku')
    s.E(5.5, 11, 1.6, 1.2, 'lily')
    s.L(2, 1, 2, 5, 'reed'); s.L(3, 0, 3, 5, 'reed'); s.R(2, 1, 2, 2, 'cattail')

@sp('koi_stepping_stone')
def _(s):
    s.E(6.5, 7, 5.5, 3.5, 'stone'); s.E(11.5, 12, 3.5, 2.5, 'stone')
    s.L(4, 7, 8, 7, 'stone'); s.D(5, 6, 'stone', 0)
    s.L(2, 13, 2, 11, 'moss'); s.L(4, 13, 5, 11, 'moss'); s.D(3, 12, 'moss', 0)

@sp('koi_lilypads')
def _(s):
    s.E(5.5, 10, 4.5, 3, 'lily'); s.clear(9, 10); s.clear(8, 10)
    s.E(11.5, 7, 3.5, 2.5, 'lily')
    s.E(11, 13.5, 2.5, 1.6, 'lily')
    s.D(5, 10, 'lily', 2); s.D(11, 7, 'lily', 2)
    s.E(5.5, 6.5, 2.5, 2.2, 'pink'); s.D(5, 6, 'yellow', 0); s.D(4, 5, 'pink', 0)
    s.L(13, 6, 13, 2, 'lily'); s.E(13, 2, 1.2, 1.6, 'pink')

@sp('koi_reeds')
def _(s):
    s.R(2, 13, 13, 15, 'moss')
    for x, top, head in ((3, 4, True), (5, 1, False), (7, 2, True), (9, 5, False), (11, 3, True), (12, 7, False)):
        s.L(x, top, x, 12, 'reed')
        if head: s.R(x, top + 1, x, top + 3, 'cattail')
    s.D(9, 4, 'yellow', 0); s.D(8, 5, 'yellow', 1)

@sp('koi_bench')
def _(s):
    s.R(1, 3, 2, 14, 'teak'); s.R(13, 3, 14, 14, 'teak')
    s.R(0, 2, 3, 2, 'teak'); s.R(12, 2, 15, 2, 'teak')
    s.R(3, 4, 12, 5, 'teak')
    s.R(3, 6, 12, 8, 'cream')
    s.R(0, 10, 15, 11, 'teak')
    s.R(2, 8, 13, 9, 'cream')
    s.R(4, 12, 11, 12, 'teak')
    s.D(6, 4, 'korange', 1); s.D(7, 4, 'kwhite', 0); s.D(9, 5, 'kblack', 1)

@sp('koi_table')
def _(s):
    s.P([(1, 7), (7, 4), (14, 7), (8, 10)], 'teak')
    s.E(7.5, 7, 4, 1.8, 'water')
    s.D(6, 7, 'kwhite', 0); s.D(7, 7, 'korange', 1); s.D(9, 7, 'kblack', 1); s.D(10, 6, 'korange', 1)
    s.R(1, 8, 7, 9, 'teak'); s.R(8, 9, 14, 9, 'teak')
    s.R(2, 10, 3, 14, 'teak'); s.R(12, 10, 13, 13, 'teak'); s.R(7, 11, 8, 15, 'teak')
    s.R(11, 3, 13, 5, 'kwhite'); s.D(12, 3, 'moss', 1)

@sp('koi_screen')
def _(s):
    for x0, pat in ((0, 'kohaku'), (5, 'showa'), (10, 'sanke')):
        s.R(x0, 1, x0 + 5, 13, 'teak'); s.R(x0 + 1, 2, x0 + 4, 12, 'paper')
        s.R(x0 + 1, 5, x0 + 4, 10, 'water')
        base = 'kblack' if pat == 'showa' else 'kwhite'
        s.L(x0 + 2.5, 5, x0 + 2.5, 9, base, 2)
        s.D(x0 + 2, 6, 'korange', 1); s.D(x0 + 3, 8, 'korange', 1)
        if pat == 'sanke': s.D(x0 + 3, 7, 'kblack', 1)
        s.R(x0, 14, x0 + 5, 15, 'teak')

@sp('koi_streamer')
def _(s):
    s.R(2, 1, 3, 13, 'teak'); s.R(2, 0, 3, 0, 'brass')
    s.R(0, 13, 5, 15, 'stone')
    s.P([(4, 2), (14, 4), (15, 6), (13, 7), (4, 6)], 'kblack')
    s.D(5, 3, 'kwhite', 0); s.D(5, 4, 'kblack', 2)
    s.P([(4, 8), (12, 10), (13, 12), (11, 12), (4, 11)], 'kwhite')
    s.D(7, 9, 'korange', 1); s.D(8, 10, 'korange', 1); s.D(10, 10, 'korange', 1); s.D(5, 9, 'kblack', 2)

def render_all():
    out = {}
    for k, f in REG.items():
        s = Sprite(); f(s); out[k] = s.image()
    return out

def preview(path, icons, scale=8, cols=6):
    n = len(icons); rows = math.ceil(n / cols)
    pad = 12
    sheet = Image.new('RGBA', (cols * (16 * scale + pad) + pad, rows * (16 * scale + pad) + pad), (198, 198, 198, 255))
    for i, (k, im) in enumerate(icons.items()):
        x = pad + (i % cols) * (16 * scale + pad); y = pad + (i // cols) * (16 * scale + pad)
        sheet.alpha_composite(im.resize((16 * scale, 16 * scale), Image.NEAREST), (x, y))
    sheet.save(path)

if __name__ == '__main__':
    ic = render_all(); preview('out/koi_garden_icons.png', ic)
