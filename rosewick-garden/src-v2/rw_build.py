"""Rosewick Garden v2 build: rebuilt models into the existing v1.1 Nexo pack layout.
Item ids, the yml mechanics (seats, storage, dye, lantern toggle) and item definitions are kept;
models, textures and inventory icons are replaced. Writes out/Rosewick-Garden and the buyer zip."""
import json, os, shutil, zipfile
import numpy as np
from PIL import Image
import engine, render, rw_pieces as P, rw_arts as A
from engine import turn

SRC = '/home/claude/rw2/rosewick-garden/Rosewick-Garden'
OUT = '/home/claude/rw2/out/Rosewick-Garden'
ZIP = '/home/claude/rw2/out/Mistbloom_Rosewick_Garden_v2.0.zip'
AS = OUT + '/Nexo/pack/assets/rosewick'
FN = {f.__name__: f for f in P.ALL[:-1]}
FN['stake_lantern_lit'] = lambda: P.stake_lantern(True)
FLAME = [(0, 3), (1, 2), (2, 4), (3, 2), (0, 2), (2, 3), (1, 3), (3, 3)]   # frame index, ticks

def dump(d):
    return json.dumps(d, indent=1)

def build_model(name):
    m = turn(FN[name]())
    m.check()
    return m

TINT = {'garden_bench': (143, 176, 106), 'garden_chair': (143, 176, 106), 'picnic_blanket': (200, 70, 85)}

def apply_tint(m, name):
    """multiply the dye-tinted faces by the item's default colour (for icons and previews only)"""
    rgb = TINT.get(name)
    if not rgb:
        return m
    a = m.atlas.astype(float)
    for e in m.els:
        if e.tint:
            for fc in e.faces():
                x0, y0, x1, y1 = [int(round(v)) for v in e.uv[fc]]
                a[min(y0, y1):max(y0, y1), min(x0, x1):max(x0, x1), :3] *= np.array(rgb) / 255
    m.atlas = a.astype(np.uint8)
    return m

def icon(name):
    """32x32 inventory icon rendered from the unturned model, front three-quarter view"""
    m = FN[name](); m.bake(); apply_tint(m, name)
    im = render.render(m, 35, 30, 2, ss=1, pad=1)
    bb = im.getbbox(); im = im.crop(bb)
    k = 30 / max(im.size)
    im = im.resize((max(1, round(im.width * k)), max(1, round(im.height * k))), Image.LANCZOS)
    a = np.array(im); a[..., 3] = np.where(a[..., 3] > 110, 255, 0); im = Image.fromarray(a)
    out = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
    out.paste(im, ((32 - im.width) // 2, 32 - im.height - 1), im)
    return out

def main():
    shutil.rmtree(OUT, ignore_errors=True)
    shutil.copytree(SRC, OUT)
    for f in os.listdir(AS + '/textures/furniture'):
        os.remove(f'{AS}/textures/furniture/{f}')
    report = []
    for name in FN:
        m = build_model(name)
        if name == 'stake_lantern_lit':
            frames = []
            for f in range(4):
                A.FRAME[0] = (f, 4)
                mm = build_model(name); mm.bake(); frames.append(mm.atlas)
            A.FRAME[0] = None
            model = m.export('rosewick', f'furniture/{name}')
            Image.fromarray(np.concatenate(frames, axis=0), 'RGBA').save(f'{AS}/textures/furniture/{name}.png', optimize=True)
            open(f'{AS}/textures/furniture/{name}.png.mcmeta', 'w').write(dump({'animation': {
                'interpolate': False, 'frames': [{'index': i, 'time': t} for i, t in FLAME]}}))
        else:
            model = m.export('rosewick', f'furniture/{name}')
            Image.fromarray(m.atlas, 'RGBA').save(f'{AS}/textures/furniture/{name}.png', optimize=True)
        open(f'{AS}/models/furniture/{name}.json', 'w').write(dump(model))
        if name != 'stake_lantern_lit':
            icon(name).save(f'{AS}/textures/item/{name}.png', optimize=True)
        report.append((name, len(m.els)))
    # README version line
    rd = open(f'{OUT}/README.txt', encoding='utf-8').read() if os.path.exists(f'{OUT}/README.txt') else ''
    if os.path.exists(ZIP): os.remove(ZIP)
    with zipfile.ZipFile(ZIP, 'w', zipfile.ZIP_DEFLATED) as z:
        for root, _, files in os.walk(OUT):
            for f in sorted(files):
                p = os.path.join(root, f); z.write(p, os.path.relpath(p, os.path.dirname(OUT)))
    for n, k in report:
        print(f'{n:20s} {k:2d} elements')
    print(ZIP)

if __name__ == '__main__':
    main()
