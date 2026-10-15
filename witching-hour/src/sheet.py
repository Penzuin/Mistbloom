from PIL import Image, ImageDraw, ImageFont
import sys
sys.argv = ["x"]
from preview import body, worn, bg, BG
from pieces import PIECES
import os
F = "/root/wings"
def font(n, s):
    for p in (f"{F}/{n}", f"/root/wings/fonts/{n}", f"/usr/share/fonts/truetype/{n}"):
        if os.path.exists(p): return ImageFont.truetype(p, s)
    import glob
    g = glob.glob(f"/root/**/{n}", recursive=True)
    return ImageFont.truetype(g[0], s) if g else ImageFont.load_default()
tiles = []
for key, title, slot, lore, mk in PIECES:
    m = mk()
    cam = (0.6, 0.3, 1.0) if slot == "BACKPACK" else (-0.6, 0.25, -1.0)
    im = body().render(ppu=11, cam=cam, frame=1, extra=worn(key, slot, m))
    tiles.append((title, slot, im))
W, H = 3 * 560, 2 * 640
sh = Image.new("RGBA", (W, H), BG + (255,)); d = ImageDraw.Draw(sh)
f1, f2 = font("Poppins-Medium.ttf", 30), font("Poppins-Medium.ttf", 20)
for i, (t, slot, im) in enumerate(tiles):
    x0, y0 = (i % 3) * 560, (i // 3) * 640
    im.thumbnail((520, 540))
    sh.alpha_composite(im, (x0 + (560 - im.width) // 2, y0 + 20 + (540 - im.height) // 2))
    d.text((x0 + 280, y0 + 575), t, font=f1, fill=(240, 232, 255), anchor="mm")
    d.text((x0 + 280, y0 + 612), slot.lower(), font=f2, fill=(170, 160, 210), anchor="mm")
sh.convert("RGB").save("draft_sheet.png")
