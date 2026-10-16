import numpy as np, json, os, sys
from PIL import Image, ImageSequence
sys.path.insert(0,'/home/claude/recard'); sys.argv=['x']
import retitle as R
from keep import KEEP
OUT='/home/claude/recard/out/'; man=json.load(open(OUT+'manifest.json'))
packs=['koi-garden','rosewick-garden','cozy-bedroom','night-wings','halloween-festival','witching-hour','moonlit-ballroom','nightbloom-nook','frostlight']
res=[]; os.makedirs('/tmp/claude-0/mo',exist_ok=True)
for (sec,stem,name),(s2,fn,n2) in zip(KEEP,man):
    if not fn.endswith('.gif'): continue
    pack=next(p for p in packs if stem.startswith(p))
    g=Image.open(OUT+fn); fr=[np.asarray(f.convert('RGB')).astype(float) for f in ImageSequence.Iterator(g)]
    n=fr[0].shape[0]; B=R.basis(pack,n); bg,_=R.fit(fr[0],B)
    lim=int(n*0.76)
    m=np.zeros((n,n),bool)
    for f in fr: m|=(np.abs(f-bg).sum(-1)>45)
    m[lim:]=False
    ys,xs=np.nonzero(m); y0,y1,x0,x1=ys.min(),ys.max(),xs.min(),xs.max()
    cx,cy=(x0+x1)/2,(y0+y1)/2; side=max(x1-x0,y1-y0)*1.12+8; side=min(side,n)
    tl=int(n*0.79); side=min(side,tl); l=int(np.clip(cx-side/2,0,n-side)); t=int(np.clip(cy-side/2,0,tl-side)); side=int(side)
    # pick 3 most different frames
    D=lambda a,b: np.abs(fr[a]-fr[b]).mean()
    pick=[0]
    while len(pick)<4 and len(pick)<len(fr):
        pick.append(max((i for i in range(len(fr)) if i not in pick), key=lambda i:min(D(i,j) for j in pick)))
    pick=sorted(pick)
    paths=[]
    for k,i in enumerate(pick):
        im=Image.fromarray(fr[i].astype(np.uint8)).crop((l,t,l+side,t+side)).resize((360,360),Image.LANCZOS)
        p=f'/tmp/claude-0/mo/{fn[:-4]}_{k}.jpg'; im.save(p,quality=90); paths.append(p)
    diff=np.mean([D(pick[0],j) for j in pick[1:]])
    res.append({'stem':stem,'name':name,'pack':pack,'frames':paths,'n':len(fr),'diff':round(float(diff),2)})
json.dump(res,open('motion.json','w'),indent=1)
for r in res: print(r['name'],r['n'],r['diff'])
