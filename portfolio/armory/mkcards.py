import numpy as np
from PIL import Image
from scipy import ndimage
S=1024; R='/home/claude/armory/renders/'; O='/home/claude/armory/cards/'
F={"mid":np.array([104,66,132]),"edge":np.array([52,30,78]),"band":np.array([214,170,200])}
def background():
    y,x=np.mgrid[0:S,0:S].astype(float)
    d=np.sqrt(((x-S*0.55)/S)**2+((y-S*0.42)/S)**2); t=np.clip((d-0.18)/0.55,0,1)[...,None]
    img=F["mid"]*(1-t)+F["edge"]*t; k=y+(x-S/2)*-0.22
    for lo,hi,a in ((250,590,0.18),(590,640,0.08)):
        m=((k>lo)&(k<hi))[...,None]; img=np.where(m,img*(1-a)+F["band"]*a,img)
    return Image.fromarray(img.astype(np.uint8)).convert("RGBA")
def place(img,m,h,cx,base):
    m=m.resize((round(m.width*h/m.height),h),Image.LANCZOS)
    a=np.array(m)[...,3]; sh=Image.new('RGBA',m.size,(30,16,46,0)); sh.putalpha(Image.fromarray((a*0.5).astype(np.uint8)))
    sh=sh.transform(sh.size,Image.AFFINE,(1,0.9,-0.9*sh.height,0,1,0)) if False else sh
    img.alpha_composite(sh,(round(cx-m.width/2)+14,base-h+10)); img.alpha_composite(m,(round(cx-m.width/2),base-h))
def gold(name):
    t=Image.open(f'/home/claude/recard/titles/g_armory-{name}.png'); t=t.crop(t.getbbox())
    a=np.array(t); lab,k=ndimage.label(a[...,3]>8); sz=ndimage.sum(np.ones_like(lab),lab,range(1,k+1))
    a[~np.isin(lab,[i+1 for i,s in enumerate(sz) if s>200])]=0; t=Image.fromarray(a); t=t.crop(t.getbbox())
    h=86; w=round(t.width*h/t.height)
    if w>940: h=round(h*940/w); w=940
    return t.resize((w,h),Image.LANCZOS)
for sid in ['warden','ranger','blackened','sentinel','tide','vigil','hound','smith','grove']:
    img=background()
    place(img,Image.open(R+sid+'_back.png'),500,700,740)
    place(img,Image.open(R+sid+'_front.png'),640,400,790)
    t=gold(sid); img.alpha_composite(t,((S-t.width)//2,870-t.height//2))
    img.convert('RGB').resize((720,720),Image.LANCZOS).save(O+f'armory-{sid}.jpg',quality=90)
