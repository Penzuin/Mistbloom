import json, sys, glob, os
import numpy as np
from shapely.geometry import Polygon
sys.path.insert(0, os.path.dirname(__file__))
from jrender import corners, rotm, NORM
GAP=0.3
def quads(m):
    out=[]
    for i,e in enumerate(m["elements"]):
        R=None
        if "rotation" in e: r=e["rotation"]; R=rotm(r["axis"],r["angle"]); o=np.array(r["origin"],float)
        flat = sum(1 for a in range(3) if e["from"][a]==e["to"][a])>0
        for f in e["faces"]:
            cs=[np.array(p,float) for p in corners(e["from"],e["to"],f)]; n=np.array(NORM[f],float)
            if R is not None: cs=[R@(p-o)+o for p in cs]; n=R@n
            out.append((i,f,cs,n,flat))
    return out
for path in sorted(glob.glob(sys.argv[1]+"/*.json")):
    q=quads(json.load(open(path))); hits=[]
    for a in range(len(q)):
        for b in range(a+1,len(q)):
            ia,fa,ca,na,fla=q[a]; ib,fb,cb,nb,flb=q[b]
            if ia==ib: continue
            d=float(np.dot(na,nb))
            if abs(d)<0.999 or (d<0 and not(fla or flb)): continue
            if abs(float(np.dot(na,cb[0]-ca[0])))>GAP: continue
            u=ca[1]-ca[0]; u/=np.linalg.norm(u); v=np.cross(na,u)
            pa=Polygon([(p@u,p@v) for p in ca]).convex_hull; pb=Polygon([(p@u,p@v) for p in cb]).convex_hull
            ov=pa.intersection(pb).area
            if ov>0.05: hits.append((ia,fa,ib,fb,round(ov,2)))
    print(os.path.basename(path), len(hits), hits[:8])
