import math, sys
import numpy as np
from PIL import Image, ImageDraw
import hall

COL = {"grass_block":(92,140,62),"dirt":(122,86,58),"stone":(125,125,125),"tuff":(108,110,100),"deepslate":(72,72,78),
 "deepslate_bricks":(78,78,84),"polished_deepslate":(88,88,94),"deepslate_tiles":(52,52,60),"deepslate_tile_stairs":(52,52,60),
 "deepslate_tile_slab":(52,52,60),"dark_oak_log":(62,46,32),"stripped_dark_oak_log":(96,72,48),"dark_oak_planks":(70,48,28),
 "dark_oak_stairs":(70,48,28),"calcite":(222,222,216),"polished_blackstone":(48,42,52),"polished_blackstone_stairs":(48,42,52),
 "polished_blackstone_wall":(48,42,52),"polished_blackstone_slab":(48,42,52),"polished_deepslate_stairs":(88,88,94),
 "deepslate_brick_stairs":(78,78,84),"purple_stained_glass_pane":(128,64,178),"purple_stained_glass":(128,64,178),
 "white_stained_glass":(235,240,250),"sea_lantern":(200,230,235),"amethyst_block":(140,100,190),"soul_lantern":(90,200,220),
 "iron_bars":(150,150,155),"iron_chain":(120,120,130),"chiseled_deepslate":(70,70,76),"gravel":(130,124,120),"coarse_dirt":(110,80,56),
 "dark_oak_leaves":(48,80,30),"lily_of_the_valley":(240,240,240),"azure_bluet":(200,220,240),"carved_pumpkin":(220,130,30),
 "hanging_roots":(150,110,80),"dark_oak_trapdoor":(70,48,28),"dark_oak_fence":(70,48,28),"end_rod":(240,240,230),"dark_oak_wall_sign":(70,48,28)}

def base(b):
    return b.split("[")[0].split("{")[0].replace("minecraft:","")

def render(V, view="front", cut=None, scale=6):
    # isometric, camera from (-x,-z) front-left (front) or (+x,+z) back-right
    pts=[]
    for (x,y,z),(b,r) in V.items():
        n=base(b)
        if n in ("air","light") or r=="air": continue
        if cut is not None and y>cut: continue
        if y < -4: continue
        if view=="back": x,z=-x,-z
        pts.append((x,y,z,n))
    # sort back to front: far = larger x+z ... camera at -x,-z looking +x+z; draw far first
    pts.sort(key=lambda p:(-(p[0]+p[2]), p[1]))
    def proj(x,y,z): return ((x-z)*scale*0.866, -(y)*scale - (x+z)*scale*0.5)
    xs=[proj(*p[:3]) for p in pts]
    minx=min(a for a,b in xs)-20; maxx=max(a for a,b in xs)+20; miny=min(b for a,b in xs)-20; maxy=max(b for a,b in xs)+20
    W,H=int(maxx-minx),int(maxy-miny)
    img=Image.new("RGB",(W,H),(20,18,40)); d=ImageDraw.Draw(img)
    for x,y,z,n in pts:
        c=np.array(COL.get(n,(255,0,255)),float)
        cx,cy=proj(x,y,z); cx-=minx; cy-=miny
        s=scale
        top=[(cx,cy-s),(cx+0.866*s,cy-0.5*s),(cx,cy),(cx-0.866*s,cy-0.5*s)]
        left=[(cx-0.866*s,cy-0.5*s),(cx,cy),(cx,cy+s),(cx-0.866*s,cy+0.5*s)]
        right=[(cx,cy),(cx+0.866*s,cy-0.5*s),(cx+0.866*s,cy+0.5*s),(cx,cy+s)]
        # faces visible: top, -x (left), -z (right) for camera at -x,-z
        d.polygon(top,fill=tuple(int(v) for v in c))
        d.polygon(left,fill=tuple(int(v*0.72) for v in c))
        d.polygon(right,fill=tuple(int(v*0.86) for v in c))
    return img

def plan(V, y=1, s=10):
    xs=[p[0] for p in V]; zs=[p[2] for p in V]
    x0,x1,z0,z1=min(xs),max(xs),min(zs),max(zs)
    img=Image.new("RGB",((x1-x0+1)*s,(z1-z0+1)*s),(20,18,40)); d=ImageDraw.Draw(img)
    for (x,yy,z),(b,r) in V.items():
        if yy not in (y,y-1): continue
        n=base(b)
        if n in ("air","light"): continue
        if yy==y-1 and (x,y,z) in V and base(V[(x,y,z)][0]) not in ("air","light"): continue
        c=COL.get(n,(255,0,255))
        if yy==y-1: c=tuple(int(v*0.55) for v in c)
        d.rectangle([(x-x0)*s,(z-z0)*s,(x-x0+1)*s-1,(z-z0+1)*s-1],fill=c)
    return img

if __name__=="__main__":
    V=hall.build_all()
    print("blocks",len(V),"commands",len(hall.commands()))
    print("leaks",hall.flood_gaps()[:10])
    fl=hall.floating(); print("floating",len(fl),sorted(fl)[:15])
    names={}
    for b,r in V.values():
        if r in ("terrain","nature","light","air"): continue
        names[base(b)]=names.get(base(b),0)+1
    print("palette",sorted(names.items(),key=lambda x:-x[1]))
    render(V,"front",scale=9).save("/tmp/claude-0/h_front.png")
    render(V,"back",scale=9).save("/tmp/claude-0/h_back.png")
    plan(V,1).save("/tmp/claude-0/h_plan.png")
