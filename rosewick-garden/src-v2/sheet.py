from PIL import Image; import glob, sys
fs=sorted(glob.glob('out/renders/*.png')); ims=[Image.open(f) for f in fs]
h=300; ims=[i.resize((round(i.width*h/i.height),h), Image.NEAREST) for i in ims]
cols=3; rows=(len(ims)+cols-1)//cols; W=max(sum(i.width for i in ims[r*cols:(r+1)*cols]) for r in range(rows))
s=Image.new('RGB',(W,rows*h),(198,198,198))
for r in range(rows):
  x=0
  for i in ims[r*cols:(r+1)*cols]: s.paste(i,(x,r*h)); x+=i.width
s.save(sys.argv[1]); print(s.size)
