import sys, glob, os
sys.path.insert(0, os.path.dirname(__file__))
from jrender import render
from PIL import Image, ImageDraw
A = sys.argv[1]; out = sys.argv[2]; tint = (143,176,106)
fs = sorted(glob.glob(A + "/rosewick/models/furniture/*.json"))
cams = [(-1,0.8,-1.2),(1,0.6,1.2)]
tiles=[]
for f in fs:
    row=[render(f, A, cam=c, ppu=10, tint=tint, bg=(205,220,180,255)) for c in cams]
    tiles.append((os.path.basename(f)[:-5], row))
cw = max(r.width for _,rs in tiles for r in rs)+10; ch = max(r.height for _,rs in tiles for r in rs)+24
cols=4
S = Image.new("RGB", (cols*2*cw, ((len(tiles)+cols-1)//cols)*ch), (230,235,220)); d=ImageDraw.Draw(S)
for i,(n,rs) in enumerate(tiles):
    x=(i%cols)*2*cw; y=(i//cols)*ch
    for j,r in enumerate(rs): S.paste(r,(x+j*cw,y+20))
    d.text((x+4,y+4),n,fill=(0,0,0))
S.save(out)
