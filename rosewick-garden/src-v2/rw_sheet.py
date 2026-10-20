"""contact sheet of every Rosewick v2 piece, two views each"""
import sys
from PIL import Image
import rw_pieces as P, render
from rw_build import apply_tint
ims = []
for f in P.ALL:
    m = f(); m.bake(); apply_tint(m, m.name)
    for yaw in (35, 215):
        ims.append(render.render(m, yaw, 30, 10))
cols = 6
W = max(i.width for i in ims); H = max(i.height for i in ims)
rows = (len(ims) + cols - 1) // cols
s = Image.new('RGBA', (cols * W, rows * H), (198, 198, 198, 255))
for k, im in enumerate(ims):
    x, y = (k % cols) * W, (k // cols) * H
    s.paste(im, (x + (W - im.width) // 2, y + H - im.height), im)
s.convert('RGB').save(sys.argv[1]); print(s.size)
