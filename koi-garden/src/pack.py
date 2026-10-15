"""Koi Garden - one pack. Builds every piece, its icon, the Nexo items file, the ModelEngine
blueprints for the moving pieces and the buyer folder.

Moving pieces:
  * ModelEngine furniture (Nexo `modelengine_id`): the whole piece lives in the blueprint and its
    idle animation loops as soon as it's placed. Water on these is an animated texture strip.
  * Tea table: plain animated texture (the koi painted in the pool swim round it).
Still pieces: bench (dyeable), plaque, screen, stepping stones.
"""
import base64, io, json, math, os, shutil
import numpy as np
from PIL import Image
import arts, pieces, sprites, me, addon
from engine import turn
from build import dump, HAND, CUSHION_DEFAULT
from addon import without, pond_open_middle, koi_pair, koi_bowl_swim, koi_leap, koi_streamer_wind, koi_school, swim

NS, SET = 'mistbloom', 'koi_garden'
ROOT = 'out/Koi-Garden'
A = f'{ROOT}/Nexo/pack/assets/{NS}'
BP = f'{ROOT}/ModelEngine/blueprints/mistbloom'
WATER_FRAMES, WATER_TICKS = 8, 4      # 1.6 s ripple loop
TABLE_FRAMES, TABLE_TICKS = 32, 3     # 4.8 s, one lap of the pool

# ------------------------------------------------------------------ extra rigs for this pack
def bone_xyz(x, y, z):
    """model px -> ModelEngine entity space (block centre at x=z=0)"""
    return (x - 8, y, z - 8)

def lilypad_rig():
    m = pieces.koi_lilypad()
    rig = me.Rig('mistbloom_koi_lilypad', m, length=4.0)
    rig.bone('base', (0, 0, 0))
    c = math.cos(math.radians(22.5)); s = math.sin(math.radians(22.5))
    def rot(x, z):            # the koi is turned 22.5 deg about (8, 12.5)
        dx, dz = x - 8, z - 12.5
        return 8 + dx * c + dz * s, 12.5 - dx * s + dz * c
    bx, bz = rot(7.0, 12.5); tx, tz = rot(1.5 + 0.86 * 11, 12.5)
    rig.bone('koi', bone_xyz(bx, 1.85, bz))
    rig.bone('koi_tail', bone_xyz(tx, 1.85, tz), 'koi')
    rig.assign(lambda n: 'koi_tail' if n == 'koi_tail' else 'koi' if n.startswith('koi_') else 'base')
    n = 32
    rig.bones['koi'].key('rotation', me.rot_keys(4.0, y=(4, 1, 0, 0), n=n))
    rig.bones['koi'].key('position', [(4.0 * i / n, (0, 0.15 * math.sin(2 * math.pi * i / n), 0)) for i in range(n + 1)])
    rig.bones['koi_tail'].key('rotation', me.rot_keys(4.0, y=(18, 3, 0.6, 0), n=n))
    return rig

def lilypads_rig():
    m = pieces.koi_lilypads()
    rig = me.Rig('mistbloom_koi_lilypads', m, length=6.0)
    rig.bone('base', (0, 0, 0))
    groups = {'pad_a': (5.5, 0.1, 6), 'pad_b': (11.75, 0.2, 10.75), 'pad_c': (4.25, 0.3, 12.75),
              'pad_d': (13, 0.15, 3), 'pad_curl': (12, 0.4, 13.5), 'bud': (11.8, 0.2, 10.3)}
    for g, p in groups.items():
        rig.bone(g, bone_xyz(*p))
    def rule(n):
        if n.startswith(('pod', 'lotus')): return 'pad_a'      # the lotus sits on the big pad
        if n.startswith(('stem', 'bud')): return 'bud'
        for g in ('pad_curl', 'pad_a', 'pad_b', 'pad_c', 'pad_d'):
            if n == g: return g
        return 'base'
    rig.assign(rule)
    n = 24
    for i, g in enumerate(('pad_a', 'pad_b', 'pad_c', 'pad_d', 'pad_curl')):
        ph = i * 1.3
        rig.bones[g].key('position', [(6.0 * k / n, (0, 0.12 * math.sin(2 * math.pi * k / n + ph), 0)) for k in range(n + 1)])
        rig.bones[g].key('rotation', me.rot_keys(6.0, x=(1.5, 1, ph, 0), z=(1.5, 1, ph + 1.1, 0), y=(3, 1, ph, 0), n=n))
    rig.bones['bud'].key('rotation', me.rot_keys(6.0, x=(3, 2, 0.4, 0), z=(4, 1, 0, 0), n=n))
    return rig

def reeds_rig():
    m = pieces.koi_reeds()
    rig = me.Rig('mistbloom_koi_reeds', m, length=4.0)
    rig.bone('base', (0, 0, 0))
    for g, p in {'cattails': (6.5, 1.5, 7), 'iris': (10.5, 1.5, 10), 'grass': (6.5, 1.5, 12)}.items():
        rig.bone(g, bone_xyz(*p))
    rig.assign(lambda n: next((g for g in ('cattails', 'iris', 'grass') if n.startswith(g)), 'base'))
    n = 32
    rig.bones['cattails'].key('rotation', me.rot_keys(4.0, z=(4, 1, 0, 0), x=(2.5, 2, 0.5, 0), n=n))
    rig.bones['iris'].key('rotation', me.rot_keys(4.0, z=(5, 1, 0.9, 0), x=(3, 2, 1.4, 0), n=n))
    rig.bones['grass'].key('rotation', me.rot_keys(4.0, z=(6, 2, 1.8, 0), x=(3, 1, 0.2, 0), n=n))
    return rig

def rename(fn, name):
    def f():
        r = fn(); r.name = name
        if 'school' in r.bones:              # pond/bowl reuse the circling pivot from the school rig
            b = r.bones.pop('school'); b.name = 'swim'; r.bones = {'swim': b, **r.bones}
            for c in r.bones.values():
                if c.parent == 'school': c.parent = 'swim'
        return r
    return f

# ------------------------------------------------------------------ the pack, in listing order
# id, source piece in pieces.py, item name, lore, kind, extra
#   kind 'me': (rig fn, furniture fn or None, koi offset px)   'table': animated texture   'still': nothing moves
PIECES = [
    ('koi_pond', 'koi_pond', 'Koi Pond', 'A stone pond with two koi swimming in circles.',
     'me', (rename(koi_pair, 'mistbloom_koi_pond'), pond_open_middle, (8, 0, 8))),
    ('koi_school', None, 'Koi School', 'Three koi swimming in a circle.',
     'me', (rename(koi_school, 'mistbloom_koi_school'), None, (0, 0, 0))),
    ('koi_statue', 'koi_statue', 'Leaping Koi Statue', 'A koi leaping off a stone plinth, tail swishing.',
     'me', (rename(koi_leap, 'mistbloom_koi_statue'), lambda: without(pieces.koi_statue, ['koi_'], 's', ''), (0, 0, 0))),
    ('koi_bowl', 'koi_bowl', 'Koi Bowl', 'Two koi swimming round a glass bowl on a teak stand.',
     'me', (rename(koi_bowl_swim, 'mistbloom_koi_bowl'), lambda: without(pieces.koi_bowl, ['koi_'], 'b', ''), (0, 0, 0))),
    ('koi_and_lily_pad', 'koi_lilypad', 'Koi and Lily Pad', 'A koi resting under a lotus, flicking its tail.',
     'me', (rename(lilypad_rig, 'mistbloom_koi_and_lily_pad'), None, (0, 0, 0))),
    ('koi_lily_pads', 'koi_lilypads', 'Lily Pads', 'Lily pads with a lotus and a bud, bobbing on the water.',
     'me', (rename(lilypads_rig, 'mistbloom_koi_lily_pads'), None, (0, 0, 0))),
    ('koi_reeds', 'koi_reeds', 'Pond Reeds', 'Cattails and yellow iris swaying by the water.',
     'me', (rename(reeds_rig, 'mistbloom_koi_reeds'), None, (0, 0, 0))),
    ('koi_streamer', 'koi_streamer', 'Koi Streamer', 'Two koi windsocks and a cloth streamer flapping on a teak pole.',
     'me', (rename(koi_streamer_wind, 'mistbloom_koi_streamer'), None, (0, 0, 0))),
    ('koi_tea_table', 'koi_table', 'Koi Tea Table', 'A tea table with two koi swimming round the pool on top.', 'table', None),
    ('koi_bench', 'koi_bench', 'Koi Bench', 'Seats two. Dye it to change the cushions.', 'still', None),
    ('koi_folding_screen', 'koi_screen', 'Koi Folding Screen', 'A three-panel screen painted with koi.', 'still', None),
    ('koi_wall_plaque', 'koi_plaque', 'Koi Wall Plaque', 'A teak plaque with two carved koi.', 'still', None),
    ('koi_stepping_stones', 'koi_stepping_stone', 'Stepping Stones', 'Two flat stones for a garden path.', 'still', None),
]
# thin or flat pieces get a click box instead of a solid barrier
INTERACT = {'koi_wall_plaque': '0,0,0 1,1.2'}
STILL_MODEL = {p.__name__: p for p in pieces.ALL}

# ------------------------------------------------------------------ ModelEngine furniture
Y_SHIFT = 0    # Nexo spawns ModelEngine furniture on the block floor (checked in game: entity y = floor top)

def build_rig(rig_fn, furn_fn, off):
    rig = rig_fn(); m = rig.model
    ox, _, oz = off
    if ox or oz:
        for e in m.els: addon.move(e, ox, oz)
        for b in rig.bones.values():
            if b.name != 'base':
                b.origin = (b.origin[0] + ox, b.origin[1], b.origin[2] + oz)
    if furn_fn:
        fm = furn_fn()
        names = {e.name for e in m.els}
        assert not names & {e.name for e in fm.els}
        m.els += fm.els; rig.bones['base'].els += fm.els
    rig.shift = (rig.shift[0], rig.shift[1] + Y_SHIFT, rig.shift[2])
    for b in rig.bones.values():
        b.origin = (b.origin[0], b.origin[1] + Y_SHIFT, b.origin[2])
    return turn_rig(rig)

def turn_rig(rig):
    """half turn the whole rig (geometry, pivots, keyframes) so its front faces -z"""
    turn(rig.model)
    sx, sy, sz = rig.shift
    # turn() mirrors about model x=z=8; entity space is model + shift, so keep shift = (-8, y, -8)
    assert (sx, sz) == (-8, -8)
    for b in rig.bones.values():
        b.origin = (-b.origin[0], b.origin[1], -b.origin[2])
        for ch, frames in b.anim.items():
            b.anim[ch] = [(t, (-x, y, -z)) for t, (x, y, z) in frames]
    return rig

def has_water(rig):
    return any(e.name == 'water' or e.name.startswith(('mound', 'splash')) for e in rig.model.els)

def bake_rig(rig_fn, furn_fn, off):
    rig = build_rig(rig_fn, furn_fn, off)
    if not has_water(rig):
        rig.model.bake(); return rig, None
    strips, layout = [], None
    for f in range(WATER_FRAMES):
        arts.FRAME[0] = (f, WATER_FRAMES)
        rig = build_rig(rig_fn, furn_fn, off); rig.model.bake()
        lay = [(e.name, tuple(sorted(e.uv.items()))) for e in rig.model.els]
        assert layout is None or lay == layout, 'uv layout changed between frames'
        layout = lay; strips.append(rig.model.atlas)
    arts.FRAME[0] = None
    return rig, np.concatenate(strips, axis=0)

def write_blueprint(rig, strip):
    d = rig.bbmodel()
    d['outliner'] = [g for g in d['outliner'] if g['children']]      # drop empty bones
    if strip is not None:
        S = rig.model.size
        buf = io.BytesIO(); Image.fromarray(strip, 'RGBA').save(buf, 'PNG', optimize=True)
        d['textures'][0].update({'height': S * WATER_FRAMES, 'uv_height': S, 'frame_time': WATER_TICKS,
                                 'source': 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode()})
    os.makedirs(BP, exist_ok=True)
    with open(f'{BP}/{rig.name}.bbmodel', 'w') as f:
        json.dump(d, f, indent='\t')

# ------------------------------------------------------------------ Nexo models + icons
def w(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f: f.write(dump(data))

def nexo_model(name, m, strip=None, ticks=None):
    """still (or texture-animated) Nexo model, its inventory icon and the item definition"""
    w(f'{A}/models/{SET}/{name}.json', m.export(NS, f'item/{SET}/{name}'))
    os.makedirs(f'{A}/textures/item/{SET}', exist_ok=True)
    Image.fromarray(strip if strip is not None else m.atlas, 'RGBA').save(f'{A}/textures/item/{SET}/{name}.png', optimize=True)
    if strip is not None:
        w(f'{A}/textures/item/{SET}/{name}.png.mcmeta', {'animation': {'frametime': ticks, 'interpolate': False}})
    placed = {'type': 'minecraft:model', 'model': f'{NS}:{SET}/{name}'}
    if any(e.tint for e in m.els):
        placed['tints'] = [{'type': 'minecraft:dye', 'default': CUSHION_DEFAULT}]
    w(f'{A}/items/{SET}/{name}.json', {'model': {
        'type': 'minecraft:select', 'property': 'minecraft:display_context',
        'cases': [{'when': HAND, 'model': {'type': 'minecraft:model', 'model': f'{NS}:item/{SET}/{name}_icon'}}],
        'fallback': placed}})

def icon(name, img):
    img.save(f'{A}/textures/item/{SET}/{name}_icon.png', optimize=True)
    w(f'{A}/models/item/{SET}/{name}_icon.json',
      {'parent': 'minecraft:item/generated', 'textures': {'layer0': f'{NS}:item/{SET}/{name}_icon'}})

def table_strip():
    strips, layout, m = [], None, None
    for f in range(TABLE_FRAMES):
        arts.FRAME[0] = (f, TABLE_FRAMES)
        m = turn(pieces.koi_table()); m.bake()
        lay = [(e.name, tuple(sorted(e.uv.items()))) for e in m.els]
        assert layout is None or lay == layout
        layout = lay; strips.append(m.atlas)
    arts.FRAME[0] = None
    return m, np.concatenate(strips, axis=0)

# ------------------------------------------------------------------ items file
SOUNDS = {'wood': ['koi_bench', 'koi_tea_table', 'koi_folding_screen', 'koi_wall_plaque', 'koi_streamer', 'koi_bowl'],
          'stone': ['koi_pond', 'koi_statue', 'koi_stepping_stones'],
          'grass': ['koi_and_lily_pad', 'koi_lily_pads', 'koi_reeds', 'koi_school']}

def sound(iid):
    return next(k for k, v in SOUNDS.items() if iid in v)

def flipz(b, y=None):
    """pieces.py hitboxes were written for the unturned model: the half turn moves +z parts to -z"""
    bx, by, bz = b.split(',')
    bz = str(-int(bz)) if int(bz) else '0'
    return f'{bx},{y or by},{bz}'

def yml_entry(iid, title, lore, kind, meta, dyeable):
    y = [f'{iid}:', f'  itemname: "<#f2e6cc>{title}"']
    y += ['  material: LEATHER_HORSE_ARMOR', f'  color: {CUSHION_DEFAULT >> 16},{CUSHION_DEFAULT >> 8 & 255},{CUSHION_DEFAULT & 255}'] if dyeable \
        else ['  material: PAPER']
    y += ['  lore:', f'    - "<gray>{lore}"', '    - "<#9fb3d9>Koi Garden"',
          '  Components:', f'    item_model: {NS}:{SET}/{iid}', '  Mechanics:', '    furniture:']
    if kind == 'me':
        y += [f'      modelengine_id: mistbloom_{iid}']
    # NONE on every piece so Nexo spawns them all at the block centre (ModelEngine models hang from that point too)
    y += ['      properties:', '        display_transform: NONE']
    y += ['      restricted_rotation: VERY_STRICT']
    s = sound(iid)
    y += ['      block_sounds:'] + [f'        {k}_sound: block.{s}.{k}' for k in ('place', 'break', 'hit', 'step', 'fall')]
    wall = meta.get('wall')
    y += ['      limited_placing:', f'        floor: {"false" if wall else "true"}', f'        wall: {"true" if wall else "false"}',
          '        roof: false', '      hitbox:']
    if iid in INTERACT:
        y += ['        interactions:', f'          - {INTERACT[iid]}']
    elif meta['hitbox']:
        y += ['        barriers:'] + [f'          - {flipz(b)}' for b in meta['hitbox']]
    else:
        y += ['        interactions:', '          - 0,0,0 1,0.4']
    if meta.get('seats'):
        y += ['      seats:'] + [f'        - {flipz(s, y="0.5")}' for s in meta['seats']]
    return y + ['']

# ------------------------------------------------------------------ main
def main():
    shutil.rmtree(ROOT, ignore_errors=True)
    icons = sprites.render_all()
    yml = ['# Koi Garden by Mistbloom Studios', '']
    for iid, src, title, lore, kind, extra in PIECES:
        still = STILL_MODEL.get(src)
        if still:
            m = turn(still()); m.check(); meta = m.meta
        else:
            m, meta = None, {'hitbox': []}
        if kind == 'me':
            rig_fn, furn_fn, off = extra
            rig, strip = bake_rig(rig_fn, furn_fn, off)
            assert rig.name == f'mistbloom_{iid}', rig.name
            write_blueprint(rig, strip)
            # the inventory icon and the dropped/held item still use the still model
            nexo_model(iid, m) if m else None
            print(f'{iid:20s} ModelEngine  {len(rig.model.els)} elements', 'animated water' if strip is not None else '')
        elif kind == 'table':
            m, strip = table_strip(); m.check()
            nexo_model(iid, m, strip, TABLE_TICKS)
            print(f'{iid:20s} animated texture  {TABLE_FRAMES} frames')
        else:
            nexo_model(iid, m)
            print(f'{iid:20s} still')
        icon(iid, icons[src or iid])
        dyeable = bool(m) and any(e.tint for e in m.els)
        yml += yml_entry(iid, title, lore, kind, meta, dyeable)
    # koi school has no still model: its item is just the icon
    w(f'{A}/items/{SET}/koi_school.json', {'model': {'type': 'minecraft:model', 'model': f'{NS}:item/{SET}/koi_school_icon'}})
    write_docs()
    os.makedirs(f'{ROOT}/Nexo/items', exist_ok=True)
    open(f'{ROOT}/Nexo/items/mistbloom_koi_garden.yml', 'w').write('\n'.join(yml))

README = """Koi Garden - Mistbloom Studios
==================================================

{names}.

INSTALL - Drag and Drop (Nexo + ModelEngine)
--------------
1. Copy Nexo/items/mistbloom_koi_garden.yml into plugins/Nexo/items/
2. Copy the Nexo/pack/assets/ folder into plugins/Nexo/pack/assets/
3. Copy the ModelEngine/blueprints/mistbloom/ folder into plugins/ModelEngine/blueprints/
4. Run /meg reload, then /nexo reload all, then /nexo inventory to grab the pieces.

Requires Minecraft 1.21.4 or newer
"""

def write_docs():
    """README.txt and LICENSE.txt, plain text with CRLF line endings"""
    names = ', '.join(p[2] for p in PIECES)
    crlf = lambda t: t.replace('\r\n', '\n').replace('\n', '\r\n')
    open(f'{ROOT}/README.txt', 'w', newline='').write(crlf(README.format(names=names)))
    open(f'{ROOT}/LICENSE.txt', 'w', newline='').write(crlf(open('LICENSE.txt', newline='').read()))

if __name__ == '__main__':
    main()
