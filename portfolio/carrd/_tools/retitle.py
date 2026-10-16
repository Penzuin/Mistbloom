import numpy as np, os, json, sys
from PIL import Image, ImageSequence
from scipy import ndimage
from keep import KEEP
S=1024
TH={'rosewick-garden':((250,590,.20),(590,640,.09)),'halloween-festival':((250,590,.22),(590,640,.10)),'cozy-bedroom':((260,600,.26),(600,650,.10))}
DEF=((260,600,.30),(600,650,.12))
y,x=np.mgrid[0:S,0:S].astype(float)
T=np.clip((np.sqrt(((x-S*0.55)/S)**2+((y-S*0.42)/S)**2)-0.18)/0.55,0,1)
K=y+(x-S/2)*-0.22
def basis(pack,size):
    A=np.zeros((S,S))
    for lo,hi,a in TH.get(pack,DEF): A[(K>lo)&(K<hi)]=a
    B=np.stack([(1-T)*(1-A),T*(1-A),A],-1)
    if size!=S:
        B=np.stack([np.asarray(Image.fromarray(B[...,i].astype(np.float32)).resize((size,size),Image.LANCZOS)) for i in range(3)],-1)
    return B
def fit(a,B):
    n=a.shape[0]; m=np.zeros(a.shape[:2],bool); e=int(n*0.07)
    m[:int(n*.13)]=True; m[:,:e]=True; m[:,-e:]=True
    for it in range(4):
        X=B[m]; cols=np.stack([np.linalg.lstsq(X,a[...,c][m],rcond=None)[0] for c in range(3)],1)
        bg=B@cols; r=np.abs(bg-a).sum(-1)
        m=m&(r<12)
    return bg, cols
def title_box(a,bg):
    n=a.shape[0]; f=n/S
    d=(np.abs(a-bg).sum(-1)>40)
    d[:int(700*f)]=False
    lab,k=ndimage.label(ndimage.binary_dilation(d,iterations=max(2,int(6*f))))
    box=None
    for i,sl in enumerate(ndimage.find_objects(lab),1):
        ys,xs=sl
        if ys.stop>=n-int(100*f) and ys.start>=n-int(330*f):
            b=(xs.start,ys.start,xs.stop,ys.stop)
            box=b if box is None else (min(box[0],b[0]),min(box[1],b[1]),max(box[2],b[2]),max(box[3],b[3]))
    return box
def content_bottom(a,bg,x0,x1,ylim):
    d=(np.abs(a-bg).sum(-1)>40)[:ylim,x0:x1]
    rows=np.nonzero(d.sum(1)>2)[0]
    return rows.max() if len(rows) else 0
def gold(stem,n):
    t=Image.open(f'titles/g_{stem}.png'); t=t.crop(t.getbbox())
    a=np.array(t); lab,k=ndimage.label(a[...,3]>8); sizes=ndimage.sum(np.ones_like(lab),lab,range(1,k+1))
    keep=np.isin(lab,[i+1 for i,s in enumerate(sizes) if s>200]); a[~keep]=0; t=Image.fromarray(a); t=t.crop(t.getbbox())
    h=round(86*n/S); w=round(t.width*h/t.height); mw=round(940*n/S)
    if w>mw: h=round(h*mw/w); w=mw
    return t.resize((w,h),Image.LANCZOS)
def process(frames,pack,stem):
    n=frames[0].shape[0]; B=basis(pack,n)
    bg,cols=fit(frames[0],B)
    box=title_box(frames[0],bg)
    pad=int(6*n/S)
    x0,y0,x1,y1=max(0,box[0]-pad),box[1]-pad,min(n,box[2]+pad),n
    t=gold(stem,n)
    tx=(n-t.width)//2; ty=round(870*n/S-t.height/2)
    out=[]
    for a in frames:
        b=a.copy(); b[y0:y1,x0:x1]=bg[y0:y1,x0:x1]
        im=Image.fromarray(np.clip(b,0,255).astype(np.uint8)).convert('RGBA'); im.alpha_composite(t,(tx,ty)); out.append(im.convert('RGB'))
    cb=content_bottom(frames[0],bg,tx,tx+t.width,y0)
    return out,box,cb,ty
def save_gif(frs,path,durs,size=512):
    frs=[f.resize((size,size),Image.LANCZOS) for f in frs]
    strip=Image.new('RGB',(size,size*len(frs)))
    for k,f in enumerate(frs): strip.paste(f,(0,size*k))
    pal=strip.quantize(colors=256,method=Image.Quantize.MEDIANCUT)
    g=[f.quantize(palette=pal,dither=Image.Dither.FLOYDSTEINBERG) for f in frs]
    base_rgb,base_idx=np.array(frs[0]).astype(int),np.array(g[0])
    for k in range(1,len(g)):
        same=np.abs(np.array(frs[k]).astype(int)-base_rgb).sum(2)<=6
        idx=np.array(g[k]); idx[same]=base_idx[same]; im=Image.fromarray(idx,'P'); im.putpalette(g[0].getpalette()); g[k]=im
    g[0].save(path,save_all=True,append_images=g[1:],duration=durs,loop=0,optimize=False,disposal=1)
if __name__=='__main__':
    os.makedirs('out',exist_ok=True); report=[]; man=[]
    only=sys.argv[1:]
    for sec,stem,name in KEEP:
        if only and stem not in only: continue
        pack=next(p for p in ['koi-garden','rosewick-garden','cozy-bedroom','night-wings','halloween-festival','witching-hour','moonlit-ballroom','nightbloom-nook','frostlight'] if stem.startswith(p))
        slug=name.lower().replace("'",'').replace(' ','-')
        gp=f'src/{stem}.gif'
        anim=os.path.exists(gp) and Image.open(gp).n_frames>1
        if anim:
            g=Image.open(gp); frs=[]; durs=[]
            for fr in ImageSequence.Iterator(g):
                frs.append(np.asarray(fr.convert('RGB')).astype(float)); durs.append(fr.info.get('duration',100))
            out,box,cb,ty=process(frs,pack,stem)
            fn=f'{slug}.gif'; size=512; step=1
            while True:
                save_gif(out[::step],'out/'+fn,[d*step for d in durs[::step]],size)
                if os.path.getsize('out/'+fn)<1.9e6: break
                if size>400: size-=56
                else: step+=1
        else:
            a=np.asarray(Image.open(f'src/{stem}.png').convert('RGB')).astype(float)
            out,box,cb,ty=process([a],pack,stem)
            fn=f'{slug}.jpg'; out[0].resize((720,720),Image.LANCZOS).save('out/'+fn,quality=88,optimize=True)
        man.append((sec,fn,name)); report.append((stem,box,cb,ty,os.path.getsize('out/'+fn)//1024))
        print(stem,fn,box,'content_bottom',cb,'title_top',ty, 'OVERLAP' if cb>=ty-4 else '')
    if not only: json.dump(man,open('out/manifest.json','w'),indent=1)
