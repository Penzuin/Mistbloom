"""Koi Garden animated pieces as ModelEngine furniture.

Nexo's `modelengine_id` hides the placed item and shows the ModelEngine model instead, so each
blueprint here carries the whole piece: the furniture (rippling water baked into an animated
texture strip) in a still `base` bone plus the swimming koi bones from addon.py.
Placing the item is all a buyer does; the idle animation loops on its own.
"""
import base64, io, json, os, shutil
import numpy as np
from PIL import Image
import arts, pieces, addon, me
from addon import without, pond_open_middle, FRAMES, FRAMETIME

OUT = 'out/addon'
BP = f'{OUT}/plugins/ModelEngine/blueprints/mistbloom'

# (item id, blueprint, title, lore, rig fn, furniture fn or None, koi offset in px, hitbox source)
PIECES = [
    ('koi_pond_animated', 'mistbloom_koi_pond_animated', 'Koi Pond Basin (animated)',
     'Two koi circle under the rippling water.', addon.koi_pair, pond_open_middle, (8, 0, 8), pieces.koi_pond),
    ('koi_bowl_animated', 'mistbloom_koi_bowl_animated', 'Koi Bowl (animated)',
     'Two little koi swim round the bowl.', addon.koi_bowl_swim,
     lambda: without(pieces.koi_bowl, ['koi_'], 'koi_bowl_animated', ''), (0, 0, 0), pieces.koi_bowl),
    ('koi_statue_animated', 'mistbloom_koi_statue_animated', 'Leaping Koi Statue (animated)',
     'The koi rocks on its splash, tail swishing.', addon.koi_leap,
     lambda: without(pieces.koi_statue, ['koi_'], 'koi_statue_animated', ''), (0, 0, 0), pieces.koi_statue),
    ('koi_streamer_animated', 'mistbloom_koi_streamer_animated', 'Koi Streamer (animated)',
     'Koi windsocks flapping in the wind.', addon.koi_streamer_wind, None, (0, 0, 0), pieces.koi_streamer),
    ('koi_school', 'mistbloom_koi_school', 'Koi School',
     'Three koi swimming in a slow circle. Set it in any pond.', addon.koi_school, None, (0, 0, 0), None),
]

ITEM_MODEL = {'koi_streamer_animated': 'mistbloom:koi_garden/koi_streamer',
              'koi_school': 'mistbloom:koi_garden_animated/koi_school'}
Y_SHIFT = -8   # Nexo centres a floor piece's display entity half a block up; ModelEngine hangs the model from it


def build_rig(rig_fn, furn_fn, off, name):
    rig = rig_fn()
    rig.name = name
    m = rig.model
    ox, oy, oz = off
    if ox or oz:
        for e in m.els:
            addon.move(e, ox, oz)
        for b in rig.bones.values():
            if b.parent is None and b.name != 'base':
                b.origin = (b.origin[0] + ox, b.origin[1], b.origin[2] + oz)
        # child bones carry absolute origins too
        for b in rig.bones.values():
            if b.parent is not None:
                b.origin = (b.origin[0] + ox, b.origin[1], b.origin[2] + oz)
    if furn_fn:
        fm = furn_fn()
        names = {e.name for e in m.els}
        for e in fm.els:
            assert e.name not in names, e.name
        m.els += fm.els
        rig.bones['base'].els += fm.els
    rig.shift = (rig.shift[0], rig.shift[1] + Y_SHIFT, rig.shift[2])
    for b in rig.bones.values():
        b.origin = (b.origin[0], b.origin[1] + Y_SHIFT, b.origin[2])
    return rig


def bake(rig_fn, furn_fn, off, name):
    """bake every ripple frame with the same uv layout; returns the rig and the frame strip"""
    if furn_fn is None:
        rig = build_rig(rig_fn, None, off, name); rig.model.bake()
        return rig, None
    strips, layout, rig = [], None, None
    for f in range(FRAMES):
        arts.FRAME[0] = (f, FRAMES)
        rig = build_rig(rig_fn, furn_fn, off, name)
        rig.model.bake()
        lay = [(e.name, tuple(sorted(e.uv.items()))) for e in rig.model.els]
        assert layout is None or lay == layout, 'uv layout changed between frames'
        layout = lay
        strips.append(rig.model.atlas)
    arts.FRAME[0] = None
    return rig, np.concatenate(strips, axis=0)


def bbmodel(rig, strip):
    d = rig.bbmodel()
    if strip is not None:
        S = rig.model.size
        buf = io.BytesIO(); Image.fromarray(strip, 'RGBA').save(buf, 'PNG', optimize=True)
        t = d['textures'][0]
        t.update({'height': S * FRAMES, 'uv_height': S, 'frame_time': FRAMETIME,
                  'source': 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode()})
    return d


def nexo_yml():
    y = ['# Mistbloom - Koi Garden, animated pieces (ModelEngine)', '']
    for vid, bp, title, lore, *_ , src in PIECES:
        hit = src().meta['hitbox'] if src else []
        y += [f'{vid}:', f'  itemname: "<#f2e6cc>{title}"', '  material: PAPER', '  lore:',
              f'    - "<gray>{lore}"', '    - "<#9fb3d9>Koi Garden"',
              '  Components:', f'    item_model: {ITEM_MODEL.get(vid, "mistbloom:koi_garden_animated/" + vid)}',
              '  Mechanics:', '    furniture:', f'      modelengine_id: {bp}',
              '      limited_placing:', '        floor: true', '        wall: false', '        roof: false',
              '      hitbox:']
        if hit:
            y += ['        barriers:'] + [f'          - {b}' for b in hit]
        else:
            y += ['        interactions:', '          - 0,0,0 1,0.4']
        y.append('')
    return y


def main():
    shutil.rmtree(BP, ignore_errors=True)
    shutil.rmtree(f'{OUT}/plugins/MythicMobs', ignore_errors=True)
    os.makedirs(BP, exist_ok=True)
    for vid, bp, title, lore, rig_fn, furn_fn, off, src in PIECES:
        rig, strip = bake(rig_fn, furn_fn, off, bp)
        with open(f'{BP}/{bp}.bbmodel', 'w') as f:
            json.dump(bbmodel(rig, strip), f, indent='\t')
        print(bp, len(rig.model.els), 'elements', 'animated water' if strip is not None else '')
    # inventory icon for the koi school (it has no placed Nexo model of its own)
    A = f'{OUT}/plugins/Nexo/pack/external_packs/mistbloom_koi_garden_animated/assets/mistbloom'
    os.makedirs(f'{A}/items/koi_garden_animated', exist_ok=True)
    json.dump({'model': {'type': 'minecraft:model', 'model': 'mistbloom:item/koi_garden/koi_plaque_icon'}},
              open(f'{A}/items/koi_garden_animated/koi_school.json', 'w'), indent='\t')
    # Nexo items: the ModelEngine pieces plus the rippling tea table from addon.py
    old = open(f'{OUT}/plugins/Nexo/items/mistbloom_koi_garden_animated.yml').read()
    table = old[old.index('koi_table_animated:'):]
    open(f'{OUT}/plugins/Nexo/items/mistbloom_koi_garden_animated.yml', 'w').write('\n'.join(nexo_yml()) + '\n' + table)

if __name__ == '__main__':
    main()
