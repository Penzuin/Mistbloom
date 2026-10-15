import sys; sys.path.insert(0,'/home/claude/festival')
import render as R
from PIL import Image
VIEWS = {
 'gate':   ((1.5, 3.2, -40), (0.5, 1.8, -24)),
 'bonfire':((8, 5, -30), (17, 1, -22)),
 'square': ((-9, 6, -12), (0.5, 1, 1)),
 'cottage':((-6, 5, -9), (-21, 3, 0)),
 'graves': ((8, 5, -10), (24, 2, 0)),
 'patch':  ((0, 7, 8), (0, 2, 30)),
 'back':   ((40, 30, 70), (0, 0, 0)),
}
tiles = []
for k, (c, t) in VIEWS.items():
    im = R.shot(c, t, 640, 360, 70, 160 if k != 'back' else 400)
    im.save(f'/home/claude/festival/v_{k}.png'); tiles.append(im)
sheet = Image.new('RGB', (1280, 360 * 4))
for i, im in enumerate(tiles): sheet.paste(im, ((i % 2) * 640, (i // 2) * 360))
sheet.save('/home/claude/festival/views.png')
