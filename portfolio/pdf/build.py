import json, os, sys
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
from reportlab.platypus import Paragraph, Frame
from reportlab.lib.styles import ParagraphStyle
sys.path.insert(0,'/home/claude/recard'); from keep import KEEP
G='/usr/share/fonts/truetype/google-fonts/'
pdfmetrics.registerFont(TTFont('Lora',G+'Lora-Variable.ttf'))
pdfmetrics.registerFont(TTFont('Pop',G+'Poppins-Regular.ttf')); pdfmetrics.registerFont(TTFont('PopM',G+'Poppins-Medium.ttf')); pdfmetrics.registerFont(TTFont('PopSB',G+'Poppins-Bold.ttf'))
W,H=960,540
BG,CARD,INK,MUTE,GOLD,LILAC=HexColor('#141A33'),HexColor('#1C2446'),HexColor('#F4EFE6'),HexColor('#B9B4CF'),HexColor('#F2C97D'),HexColor('#C9B8F0')
OUT='/home/claude/recard/out/'; man=json.load(open(OUT+'manifest.json'))
files={stem:fn for (s,stem,n),(s2,fn,n2) in zip(KEEP,man)}
names={stem:n for s,stem,n in KEEP}
PACKS=[('koi-garden','Koi Garden','Animated pond decor','A pond and garden set built around koi. Most pieces are animated: koi swim around the pond, the bowl and the tea table, and the windsock flaps in the wind.'),
('rosewick-garden','Rosewick Garden','Cottage garden furniture','Garden seating, a rose trellis and arbor, a birdbath, a flower wheelbarrow and a lantern with a flickering flame.'),
('cozy-bedroom','Cozy Bedroom','Bedroom furniture','A quilted bed, a bedside table and a wall shelf with plants and books.'),
('nightbloom-nook','Nightbloom Nook','Reading nook furniture','A tall bookshelf, a writing desk, a potted moonbloom, a nightstand and an animated moon clock.'),
('night-wings','Night Wings','Wearable wing cosmetics','Six wing cosmetics for HMCCosmetics: feather, duskbat, frost, fairy, dragon and petal wings.'),
('halloween-festival','Halloween Festival','Halloween decor','A harvest market, a witch\'s corner, a graveyard and spooky critters. Jack-o\'-lanterns, lamps and candles flicker.'),
('witching-hour','Witching Hour','Animated witch decor','A candle ring, a ghost lantern and a floating wisp, all with moving flames and glow.'),
('moonlit-ballroom','Moonlit Ballroom','Animated ghost ballroom','A ghost pianist, waltzing ghosts, a ghost portrait, a floating candelabra, a spirit lantern and a little ghost.'),
('frostlight','Frostlight Market','Winter night market','A market stall, a cocoa cart, gifts and crates, benches, and glowing lanterns and garland lights.')]
SECT={'koi-garden':'Everyday','rosewick-garden':'Everyday','cozy-bedroom':'Everyday','nightbloom-nook':'Everyday','night-wings':'Cosmetics','halloween-festival':'Holiday','witching-hour':'Holiday','moonlit-ballroom':'Holiday','frostlight':'Holiday'}
cache={}
def img(fn):
    if fn not in cache:
        im=Image.open(OUT+fn); im.seek(0); im=im.convert('RGB')
        p=f'/tmp/claude-0/pf_{fn}.jpg'; im.resize((540,540),Image.LANCZOS).save(p,quality=88); cache[fn]=p
    return cache[fn]
def rimg(c,path,x,y,w,h,r=8):
    c.saveState(); p=c.beginPath(); p.roundRect(x,y,w,h,r); c.clipPath(p,stroke=0,fill=0); c.drawImage(path,x,y,w,h); c.restoreState()
def bg(c,num=None):
    c.setFillColor(BG); c.rect(0,0,W,H,fill=1,stroke=0)
    if num:
        c.setFont('Pop',8); c.setFillColor(MUTE); c.drawRightString(W-36,22,f'Mistbloom Studios  ·  {num}')
def para(c,text,x,y,w,h,size=11,color=MUTE,font='Pop',lead=1.5):
    st=ParagraphStyle('p',fontName=font,fontSize=size,leading=size*lead,textColor=color)
    f=Frame(x,y,w,h,leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0,showBoundary=0); f.addFromList([Paragraph(text,st)],c)
def badge(c,x,y):
    c.setFillColor(HexColor('#141A33')); c.setFillAlpha(0.8); c.roundRect(x,y,50,13,6,fill=1,stroke=0); c.setFillAlpha(1)
    c.setFillColor(GOLD); c.setFont('PopSB',6.5); c.drawCentredString(x+25,y+4,'ANIMATED')
def grid(c,stems,x0,ytop,cols,cell,gap):
    for i,s in enumerate(stems):
        r,k=divmod(i,cols); x=x0+k*(cell+gap); y=ytop-(r+1)*cell-r*gap
        rimg(c,img(files[s]),x,y,cell,cell,6)
        if files[s].endswith('.gif'): badge(c,x+cell-54,y+cell-17)
c=canvas.Canvas('/mnt/user-data/outputs/Mistbloom-Portfolio.pdf',pagesize=(W,H))
c.setTitle('Mistbloom Studios Portfolio'); c.setAuthor('Zinguin, Mistbloom Studios')
# cover
bg(c)
mosaic=[stem for stem in ['koi-garden-01-pond','halloween-festival-05-potion-stall','moonlit-ballroom-ghost-pianist','frostlight-1-market-stall','night-wings-5-nightwyrm','rosewick-garden-08-arbor-arch']]
cell=150
for i,s in enumerate(mosaic):
    rimg(c,img(files[s]),W/2-3*cell-12.5+i*(cell+5),40,cell,cell,8)
logo=ImageReader('mistbloom-logo.png'); lw=420; c.drawImage(logo,(W-lw)/2,330,lw,lw*332/1200,mask='auto')
c.setFillColor(GOLD); c.setFont('PopSB',11); c.drawCentredString(W/2,300,'P O R T F O L I O')
c.setFillColor(INK); c.setFont('Lora',30); c.drawCentredString(W/2,255,'3D furniture, decor and cosmetics for Minecraft')
c.setFillColor(MUTE); c.setFont('Pop',12); c.drawCentredString(W/2,228,'By Zinguin  ·  9 packs  ·  96 pieces  ·  37 animated')
c.showPage()
# about
bg(c,2)
c.setFillColor(GOLD); c.setFont('PopSB',10); c.drawString(60,470,'A B O U T')
c.setFillColor(INK); c.setFont('Lora',28); c.drawString(60,430,'Hi, I\'m Zinguin.')
para(c,'I run Mistbloom Studios, where I design 3D furniture, decor and wearable cosmetics for Minecraft servers. Each piece comes as a Blockbench model, packaged so it drops straight into a server running Nexo. My home style is cozy, night-sky fantasy: soft purples, warm lantern light and small details you notice up close.',60,300,400,115,size=11.5,color=MUTE)
items=[('Furniture and decor','Placeable 3D pieces with seats, storage and light toggles, plus animated pieces like candles, ghosts and koi.'),
('Cosmetics','Wings and other wearables for HMCCosmetics, each with its own permission.'),
('Animation','Looping idle animations through ModelEngine and animated textures, from swimming koi to flickering flames.'),
('Tools','Blockbench, Nexo, ModelEngine, HMCCosmetics.')]
y=440
for t,d in items:
    c.setFillColor(CARD); c.roundRect(520,y-78,380,72,8,fill=1,stroke=0)
    c.setFillColor(INK); c.setFont('PopSB',12); c.drawString(538,y-28,t)
    para(c,d,538,y-74,345,40,size=9.5,color=MUTE,lead=1.4); y-=86
stats=[('9','packs'),('96','pieces'),('37','animated')]
for i,(n,l) in enumerate(stats):
    x=60+i*135; c.setFillColor(GOLD); c.setFont('Lora',34); c.drawString(x,190,n); c.setFillColor(MUTE); c.setFont('Pop',10); c.drawString(x,172,l)
c.setFillColor(MUTE); c.setFont('Pop',9.5); c.drawString(60,120,'Packs in this portfolio')
c.setFont('PopM',10); c.setFillColor(INK)
for i,(k,t,sub,d) in enumerate(PACKS):
    c.drawString(60+(i%3)*150,98-(i//3)*18,t)
c.showPage()
page=3
# packs
for k,title,sub,desc in PACKS:
    stems=[s for s2,s,n in KEEP if s.startswith(k)]
    anim=sum(files[s].endswith('.gif') for s in stems)
    bg(c,page); page+=1
    cov=f'/home/claude/mb-portfolio/portfolio/behance/covers/{k}.jpg'
    rimg(c,cov,48,250,300,235,10)
    c.setFillColor(GOLD); c.setFont('PopSB',8.5); c.drawString(48,222,f'{SECT[k].upper()}  ·  {sub.upper()}')
    t=Image.open(f'/home/claude/recard/titles/p_{k}.png'); t=t.crop(t.getbbox()); th=34; tw=t.width*th/t.height
    if tw>300: tw=300; th=t.height*tw/t.width
    tp=f'/tmp/claude-0/pt_{k}.png'; t.save(tp); c.drawImage(tp,48,182,tw,th,mask='auto')
    para(c,desc,48,90,300,82,size=10.5)
    c.setFillColor(MUTE); c.setFont('Pop',9); c.drawString(48,62,f'{len(stems)} pieces' + (f'  ·  {anim} animated' if anim else '') + '  ·  Made for Nexo')
    first=stems[:12]; cols=4; cell=128; gap=8
    rows=(len(first)+cols-1)//cols
    gh=rows*cell+(rows-1)*gap; ytop=H/2+gh/2
    grid(c,first,384,ytop,cols,cell,gap)
    # names under? captions via title on card already
    c.showPage()
    rest=stems[12:]
    while rest:
        chunk=rest[:21]; rest=rest[21:]
        bg(c,page); page+=1
        c.setFillColor(GOLD); c.setFont('PopSB',8.5); c.drawString(48,500,f'{title.upper()}  ·  CONTINUED')
        import math; rows=math.ceil(len(chunk)/7); cols=math.ceil(len(chunk)/rows); cell=118 if rows>2 else 150; gap=8
        gw=cols*cell+(cols-1)*gap; gh=rows*cell+(rows-1)*gap
        grid(c,chunk,(W-gw)/2,min(480,H/2+gh/2),cols,cell,gap)
        c.showPage()
c.save(); print('pages',page-1)
