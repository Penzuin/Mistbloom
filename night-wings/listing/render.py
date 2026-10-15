import sys, os
sys.path.insert(0, "/root/nw"); os.chdir("/root/nw")
from wings import WINGS
from PIL import Image
out = "/root/nwicon/r"; os.makedirs(out, exist_ok=True)
CAM = (0.5, 0.28, 1.0)
for key, title, blurb, mk in WINGS:
    m = mk()
    for k in range(6):
        im = m.render(ppu=12, cam=CAM, frame=k)
        im.save(f"{out}/{key}_f{k}.png")
    print(key, im.size)
