import sys; sys.path.insert(0, "/root/props/src")
import numpy as np, pieces as P
from PIL import Image
CAM = (-0.55, 0.75, -1.0)
names = sys.argv[1:] or None
ms = [m for m in P.all_models() if (m.name.endswith("_lit") or m.name.split("_lit")[0] not in P.LIGHTS) and (not names or m.name in names)]
ims = []
for m in ms:
    im = m.render(ppu=14, cam=CAM, frame=2)
    bg = Image.new("RGBA", im.size, (150, 140, 120, 255)); bg.alpha_composite(im); ims.append(bg)
W = 5; cw = max(i.width for i in ims); ch = max(i.height for i in ims)
o = Image.new("RGB", (cw * W, ch * ((len(ims) + W - 1) // W)), (150, 140, 120))
for i, im in enumerate(ims):
    o.paste(im, ((i % W) * cw + (cw - im.width) // 2, (i // W) * ch + (ch - im.height)))
o.save("/root/props/media/preview.png"); print(o.size)
