"""Builds the Mistbloom Koi Garden pack: models, textures, icons, item definitions and the Nexo items file."""
import json, os, re, shutil, zipfile
from PIL import Image
import pieces, sprites

NS, SET = 'mistbloom', 'koi_garden'
PACK = 'out/pack/plugins/Nexo/pack/external_packs/mistbloom_koi_garden'
A = f'{PACK}/assets/{NS}'
CUSHION_DEFAULT = 0xE8D9B8  # cream when undyed

HAND = ['gui', 'firstperson_righthand', 'firstperson_lefthand', 'thirdperson_righthand', 'thirdperson_lefthand', 'head']

# grouping + a line of lore for each piece
SECTIONS = [
    ('Decor', [
        ('koi_statue', 'Caught mid-leap over carved stone waves.'),
        ('koi_lilypad', 'Resting in the shade of a lotus.'),
        ('koi_bowl', 'A little koi in a brass-rimmed bowl.'),
        ('koi_plaque', 'Two koi, forever chasing each other.'),
    ]),
    ('Pond', [
        ('koi_pond', 'A small stone pond. Takes up 2x2.'),
        ('koi_stepping_stone', 'For crossing the garden with dry feet.'),
        ('koi_lilypads', 'Lily pads with an open lotus and a bud.'),
        ('koi_reeds', 'Reeds and cattails for the pond edge.'),
    ]),
    ('Furniture', [
        ('koi_bench', 'Seats two. Dye it to change the cushions.'),
        ('koi_table', 'A low tea table with a koi pool inlay.'),
        ('koi_screen', 'A three-panel screen painted with koi.'),
        ('koi_streamer', 'Koi windsocks flying from a teak pole.'),
    ]),
]

def dump(data):
    """Tab-indented JSON with short lists kept on one line."""
    txt = json.dumps(data, indent='\t')
    txt = re.sub(r'\[\s+([^\[\]{}]*?)\s+\]', lambda m: '[' + re.sub(r',\s+', ', ', m.group(1)) + ']', txt)
    # faces on one line each, the way Blockbench writes them
    txt = re.sub(r'\{\s+("uv": \[[^\]]*\],)\s+("texture": "#0")(,)?\s*("tintindex": 0)?\s+\}',
                 lambda m: '{' + m.group(1) + ' ' + m.group(2) + (', ' + m.group(4) if m.group(4) else '') + '}', txt)
    return txt + '\n'

def w(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        f.write(dump(data))

def main():
    shutil.rmtree('out/pack', ignore_errors=True)
    icons = sprites.render_all()
    models = {f.__name__: f() for f in pieces.ALL}
    yml = ['# Mistbloom - Koi Garden', '']
    for title, items in SECTIONS:
        yml += [f'# --- {title} ---', '']
        for name, lore in items:
            m = models[name]
            m.check()
            model = m.export(NS, f'item/{SET}/{name}')
            w(f'{A}/models/{SET}/{name}.json', model)
            os.makedirs(f'{A}/textures/item/{SET}', exist_ok=True)
            Image.fromarray(m.atlas, 'RGBA').save(f'{A}/textures/item/{SET}/{name}.png', optimize=True)
            icons[name].save(f'{A}/textures/item/{SET}/{name}_icon.png', optimize=True)
            w(f'{A}/models/item/{SET}/{name}_icon.json',
              {'parent': 'minecraft:item/generated', 'textures': {'layer0': f'{NS}:item/{SET}/{name}_icon'}})
            dyeable = any(e.tint for e in m.els)
            placed = {'type': 'minecraft:model', 'model': f'{NS}:{SET}/{name}'}
            if dyeable:
                placed['tints'] = [{'type': 'minecraft:dye', 'default': CUSHION_DEFAULT}]
            w(f'{A}/items/{SET}/{name}.json', {'model': {
                'type': 'minecraft:select', 'property': 'minecraft:display_context',
                'cases': [{'when': HAND, 'model': {'type': 'minecraft:model', 'model': f'{NS}:item/{SET}/{name}_icon'}}],
                'fallback': placed}})

            meta = m.meta
            yml += [f'{name}:',
                    f'  itemname: "<#f2e6cc>{m.title}"',
                    f'  material: {"LEATHER_HORSE_ARMOR" if dyeable else "PAPER"}',
                    '  lore:',
                    f'    - "<gray>{lore}"',
                    '    - "<#9fb3d9>Koi Garden"',
                    '  Components:',
                    f'    item_model: {NS}:{SET}/{name}',
                    '  Mechanics:',
                    '    furniture:',
                    '      properties:',
                    '        display_transform: NONE',
                    '      rotatable: true',
                    '      limited_placing:']
            if meta.get('wall'):
                yml += ['        wall: true', '        floor: false', '        roof: false']
            else:
                yml += ['        floor: true', '        wall: false', '        roof: false']
            yml += ['      hitbox:']
            if meta['hitbox']:
                yml += ['        barriers:'] + [f'          - {b}' for b in meta['hitbox']]
            else:
                yml += ['        interactions:      # no barrier, you can walk over it',
                        '          - 0,0,0 1,0.3']
            if meta.get('seats'):
                yml += ['      seats:'] + [f'        - {s}' for s in meta['seats']]
            yml.append('')
    os.makedirs('out/pack/plugins/Nexo/items', exist_ok=True)
    open('out/pack/plugins/Nexo/items/mistbloom_koi_garden.yml', 'w').write('\n'.join(yml))
    with open(f'{PACK}/pack.mcmeta', 'w') as f:
        f.write(dump({'pack': {'pack_format': 46, 'description': 'Mistbloom - Koi Garden'}}))
    z = 'out/mistbloom_koi_garden.zip'
    if os.path.exists(z): os.remove(z)
    with zipfile.ZipFile(z, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk('out/pack'):
            for fn_ in sorted(files):
                p = os.path.join(root, fn_)
                zf.write(p, os.path.relpath(p, 'out/pack'))
    return z

if __name__ == '__main__':
    print(main())
