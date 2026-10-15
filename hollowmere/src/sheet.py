import sys
from PIL import Image, ImageDraw, ImageFont
import importlib, os
hero = importlib.import_module(os.environ.get("MOD", "hero3"))
F=ImageFont.truetype("/usr/share/fonts/truetype/google-fonts/Poppins-Medium.ttf",22) if __import__('os').path.exists("/usr/share/fonts/truetype/google-fonts/Poppins-Medium.ttf") else ImageFont.truetype("/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf",22)
models=hero.all_models()
VIEWS=[("front 3/4",(-0.62,0.5,-1)),("other side",(0.7,0.45,-1)),("back",(0.5,0.45,1))]
rows=[]
for m in models:
    n=m.check()
    tiles=[]
    for name,cam in VIEWS:
        im=m.render(ppu=14,cam=cam,frame=0)
        t=Image.new("RGBA",(360,360),(30,24,48,255))
        s=min(330/im.width,300/im.height); im=im.resize((max(1,int(im.width*s)),max(1,int(im.height*s))),Image.NEAREST)
        t.alpha_composite(im,((360-im.width)//2,10+(300-im.height)//2))
        ImageDraw.Draw(t).text((10,326),name,font=F,fill=(200,190,230))
        tiles.append(t)
    r=Image.new("RGBA",(360*3,400),(20,16,34,255)); ImageDraw.Draw(r).text((10,6),f"{m.name}  ({n} elements)",font=F,fill=(255,190,110))
    for k,t in enumerate(tiles): r.alpha_composite(t,(k*360,40))
    rows.append(r)
out=Image.new("RGB",(1080,400*len(rows)),(20,16,34))
for k,r in enumerate(rows): out.paste(r.convert("RGB"),(0,400*k))
out.save(sys.argv[1]); print(out.size)
