import sys, os, pieces, render
from PIL import Image
os.makedirs('out/renders', exist_ok=True)
names = sys.argv[1:]
for fn in pieces.ALL:
    if names and fn.__name__ not in names: continue
    m = fn(); n = m.check(); m.bake()
    a = render.on_bg(render.render(m, 35, 28, 14))
    b = render.on_bg(render.render(m, 215, 28, 14))
    W = a.width + b.width; H = max(a.height, b.height)
    s = Image.new('RGBA', (W, H), (198,198,198,255)); s.paste(a, (0,0)); s.paste(b, (a.width,0))
    s.save(f'out/renders/{m.name}.png'); print(m.name, n, 'els atlas', m.size)
