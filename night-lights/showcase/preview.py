"""Rough iso preview of the showcase voxels (colour per block) with furniture as glowing markers."""
import sys
from PIL import Image, ImageDraw
import showcase as SC
COL = {"grass_block":(86,140,70),"moss_block":(90,120,50),"dirt":(120,85,60),"rooted_dirt":(130,95,70),"stone":(125,125,125),
 "andesite":(140,140,135),"tuff":(105,105,95),"mossy_cobblestone":(95,115,85),"deepslate":(70,70,75),"dirt_path":(150,125,80),
 "deepslate_tiles":(55,55,60),"dark_oak_planks":(70,48,30),"calcite":(225,225,220),"polished_deepslate":(75,75,80),
 "stripped_dark_oak_log":(95,70,45),"dark_oak_stairs":(60,40,25),"dark_oak_slab":(60,40,25),"cherry_log":(70,40,45),
 "cherry_leaves":(240,170,200),"purple_carpet":(130,60,170),"purple_stained_glass_pane":(150,90,200),"chiseled_bookshelf":(150,110,70),
 "cobblestone":(120,120,120)}
def col(b):
    n=b.split("[")[0]
    for k,v in COL.items():
        if n==k: return v
    return (200,200,120) if "flower" in n or n in ("allium","azure_bluet","lily_of_the_valley") else (110,170,90)
def render(V, pieces, yaw_view=1, s=10):
    W,H=900,700; im=Image.new("RGB",(W,H),(20,24,48)); d=ImageDraw.Draw(im)
    def P(x,y,z): return (W/2+(x*yaw_view - z)*s*0.866, H*0.45+(x*yaw_view + z)*s*0.5 - y*s)
    keys=sorted(V, key=lambda p:(p[0]*yaw_view+p[2], p[1]))
    for (x,y,z) in keys:
        c=col(V[(x,y,z)])
        top=[P(x,y+1,z),P(x+1,y+1,z),P(x+1,y+1,z+1),P(x,y+1,z+1)]
        if yaw_view==1:
            l=[P(x,y+1,z+1),P(x+1,y+1,z+1),P(x+1,y,z+1),P(x,y,z+1)]
            r=[P(x+1,y+1,z),P(x+1,y+1,z+1),P(x+1,y,z+1),P(x+1,y,z)]
        else:
            l=[P(x,y+1,z+1),P(x+1,y+1,z+1),P(x+1,y,z+1),P(x,y,z+1)]
            r=[P(x,y+1,z),P(x,y+1,z+1),P(x,y,z+1),P(x,y,z)]
        d.polygon(top,fill=c); d.polygon(l,fill=tuple(int(v*.7) for v in c)); d.polygon(r,fill=tuple(int(v*.55) for v in c))
    for m,x,y,z,_,_ in pieces:
        cx,cy=P(x+.5,y+.5,z+.5); d.ellipse([cx-4,cy-4,cx+4,cy+4],fill=(255,230,120))
    return im
V=SC.build_all()
# view from the north-west looking south-east: flip z so arrival side is in front
Vf={(x,y,-z):b for (x,y,z),b in V.items()}
pf=[(m,x,y,-z,a,b) for m,x,y,z,a,b in SC.PIECES]
render(Vf,pf).save(sys.argv[1])
