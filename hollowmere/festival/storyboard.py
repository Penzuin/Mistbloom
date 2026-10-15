import sys, math
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
import shots as S, render as R
from PIL import Image, ImageDraw, ImageFont
from concurrent.futures import ProcessPoolExecutor
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
def frame_img(args):
    name, f = args
    x, y, z, yaw, pitch = f
    d = (-math.sin(math.radians(yaw)) * math.cos(math.radians(pitch)), -math.sin(math.radians(pitch)), math.cos(math.radians(yaw)) * math.cos(math.radians(pitch)))
    return R.shot((x, y, z), (x + d[0], y + d[1], z + d[2]), 480, 270, 70, 400 if name.endswith(('arrival', 'goodnight')) else 150)
if __name__ == '__main__':
    frames = S.bake()
    jobs, labels = [], []
    for s in S.SHOTS:
        fr = frames[s['name']]
        for t in (0, 0.5, 1):
            jobs.append((s['name'], fr[min(len(fr) - 1, int(t * (len(fr) - 1)))]))
    with ProcessPoolExecutor(6) as ex:
        imgs = list(ex.map(frame_img, jobs))
    durs = {n: d for n, d, p in S.durations()}
    try: F1, F2 = ImageFont.truetype(FONT, 20), ImageFont.truetype(FONT, 15)
    except Exception: F1 = F2 = ImageFont.load_default()
    rows = len(S.SHOTS)
    sheet = Image.new('RGB', (1460, rows * 330 + 10), (18, 14, 30))
    d = ImageDraw.Draw(sheet)
    for r, s in enumerate(S.SHOTS):
        y0 = r * 330 + 10
        d.text((10, y0), f"{r + 1}. {s['name']}  ({durs[s['name']]:.0f} s)  -  {s['purpose']}", font=F1, fill=(255, 190, 110))
        for c in range(3):
            sheet.paste(imgs[r * 3 + c], (10 + c * 485, y0 + 32))
            d.text((16 + c * 485, y0 + 36), ('start', 'middle', 'end')[c], font=F2, fill=(230, 230, 240))
    sheet.save('/home/claude/festival/storyboard.png')
    print(sheet.size, sum(durs.values()))
