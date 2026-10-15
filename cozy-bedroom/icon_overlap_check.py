import sys; sys.path.insert(0,'/root/bedroom'); sys.path.insert(0,'/root/bedroom/src')
import numpy as np, icons as I
from PIL import Image, ImageDraw
def masks(room):
    c, fwd, right, up = I.basis(I.CAM)
    by = {}
    for name, (dx,dy,dz), turned in room:
        I.ROOM[:] = [(name,(dx,dy,dz),turned)]
        m = I.room_model()
        polys=[]
        for e in m.elements:
            a,b=np.array(e["from"]),np.array(e["to"])
            cs=I._rot(e,[np.array([x,y,z]) for x in (a[0],b[0]) for y in (a[1],b[1]) for z in (a[2],b[2])])
            polys.append(I.hull(np.array([(p@right*4+800, -(p@up)*4+800) for p in cs])))
        im=Image.new("L",(1600,1600)); d=ImageDraw.Draw(im)
        for p in polys:
            if len(p)>=3: d.polygon([tuple(q) for q in p], fill=255)
        by[name]=np.array(im)>0
    return by
def report(room):
    saved=list(I.ROOM); by=masks(room); I.ROOM[:]=saved
    ns=list(by); bad=[]
    for i in range(len(ns)):
        for j in range(i+1,len(ns)):
            ov=(by[ns[i]]&by[ns[j]]).sum()
            if ov: bad.append((ns[i],ns[j],int(ov)))
    return bad
if __name__=="__main__":
    print(report(list(I.ROOM)))
