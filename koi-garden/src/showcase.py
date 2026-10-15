"""Koi Garden showcase sheet: flat set colour, lighter border with a wave scroll,
3/4 views, soft offset drop shadow."""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import pieces, render

BG = (34, 74, 82)        # deep pond teal
BORDER = (52, 104, 113)
SCROLL = (88, 150, 158)
TEXT = (246, 236, 214)
SUB = (170, 206, 208)
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf'
FONT2 = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'

def wave_band(d, x0, y0, x1, y1, horiz=True):
    P = 46
    if horiz:
        mid = (y0 + y1) / 2; a = (y1 - y0) * 0.22
        pts = [(x, mid - a * math.sin(2 * math.pi * (x - x0) / P)) for x in range(int(x0), int(x1))]
        d.line(pts, fill=SCROLL, width=3)
        for k in range(int((x1 - x0) / P) + 1):
            cx = x0 + k * P + P * 0.43; cy = mid + a * 0.4
            d.arc([cx - a * 0.9, cy - a * 0.9, cx + a * 0.9, cy + a * 0.9], 200, 520, fill=SCROLL, width=3)
    else:
        mid = (x0 + x1) / 2; a = (x1 - x0) * 0.22
        pts = [(mid - a * math.sin(2 * math.pi * (y - y0) / P), y) for y in range(int(y0), int(y1))]
        d.line(pts, fill=SCROLL, width=3)
        for k in range(int((y1 - y0) / P) + 1):
            cy = y0 + k * P + P * 0.43; cx = mid + a * 0.4
            d.arc([cx - a * 0.9, cy - a * 0.9, cx + a * 0.9, cy + a * 0.9], 110, 430, fill=SCROLL, width=3)

def build(path='out/koi_garden_showcase.png', cols=4, cell=(330, 330)):
    models = [f() for f in pieces.ALL]
    rows = math.ceil(len(models) / cols)
    B, head = 44, 120
    W = cols * cell[0] + 2 * B
    H = rows * (cell[1] + 40) + 2 * B + head
    im = Image.new('RGBA', (W, H), BORDER + (255,))
    d = ImageDraw.Draw(im)
    d.rectangle([B, B, W - B, H - B], fill=BG)
    wave_band(d, B, 6, W - B, B - 6)
    wave_band(d, B, H - B + 6, W - B, H - 6)
    wave_band(d, 6, B, B - 6, H - B, horiz=False)
    wave_band(d, W - B + 6, B, W - 6, H - B, horiz=False)
    f1 = ImageFont.truetype(FONT, 54); f2 = ImageFont.truetype(FONT2, 20); f3 = ImageFont.truetype(FONT2, 17)
    d.text((W / 2, B + 52), 'KOI GARDEN', font=f1, fill=TEXT, anchor='mm')
    d.text((W / 2, B + 96), 'Mistbloom decoration set  ·  12 pieces  ·  teak · garden stone · classic koi', font=f2, fill=SUB, anchor='mm')
    for i, m in enumerate(models):
        m.check(); m.bake()
        r = render.render(m, 35, 28, 14)
        r.thumbnail((cell[0] - 30, cell[1] - 30), Image.LANCZOS)
        cx = B + (i % cols) * cell[0] + cell[0] // 2
        cy = B + head + (i // cols) * (cell[1] + 40) + cell[1] // 2
        x = cx - r.width // 2; y = cy - r.height // 2
        sh = Image.new('RGBA', r.size, (0, 0, 0, 0))
        a = np.array(r)[..., 3]
        sh.putalpha(Image.fromarray((a * 0.45).astype(np.uint8)))
        sh = sh.filter(ImageFilter.GaussianBlur(5))
        im.alpha_composite(sh, (x + 9, y + 10))
        im.alpha_composite(r, (x, y))
        d.text((cx, cy + cell[1] // 2 + 10), m.title, font=f3, fill=TEXT, anchor='mm')
    im.convert('RGB').save(path)
    return path

if __name__ == '__main__':
    print(build())
