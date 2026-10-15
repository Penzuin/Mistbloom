"""Mistbloom Koi Garden - Animated add-on.
Separate ids and files from the base set; nothing here overwrites the originals.
 * ModelEngine blueprints: swimming koi with idle animations
 * Nexo furniture: still-water pieces re-made with rippling animated water (koi left out where
   the ModelEngine koi take their place)
"""
import json, math, os, re, shutil, zipfile
import numpy as np
from PIL import Image
import arts, pieces, sprites, me
from engine import Model
from pieces import koi3d, cross, WOOD, CAP, stone, solid
from build import dump, HAND

NS, SET = 'mistbloom', 'koi_garden_animated'
OUT = 'out/addon'
PACK = f'{OUT}/plugins/Nexo/pack/external_packs/mistbloom_koi_garden_animated'
A = f'{PACK}/assets/{NS}'
FRAMES, FRAMETIME = 8, 4          # 8 frames x 4 ticks = 1.6 s ripple loop

# ======================================================= ModelEngine koi
def koi_rule(koi_names):
    def rule(n):
        for k in koi_names:
            if n.startswith(k + '_'):
                return f'{k}_tail' if n.endswith('_tail') else k
        return 'base'
    return rule

def swim(rig, spin, koi, tail_root, wiggle_cycles, wig=5, tail=22, bob=0.0, bob_cycles=1, phase=0.0):
    """body wiggle + tail swish (+ optional bob) for one koi bone."""
    L = rig.length
    n = wiggle_cycles * 8
    rig.bones[koi].key('rotation', me.rot_keys(L, y=(wig, wiggle_cycles, phase, 0), n=n))
    if bob:
        rig.bones[koi].key('position', [(t, (0, v, 0)) for t, v in
                                          [(L * i / (bob_cycles * 8), bob * math.sin(2 * math.pi * i / 8 + phase))
                                           for i in range(bob_cycles * 8 + 1)]])
    rig.bones[f'{koi}_tail'].key('rotation', me.rot_keys(L, y=(tail, wiggle_cycles, phase + math.pi / 2, 0), n=n))

def spin_keys(L, start=0.0):
    return [(L * i / 4, (0, start + 90 * i, 0)) for i in range(5)]

def koi_pair():
    """Two koi circling just under the surface - sits in the Koi Pond (animated)."""
    m = Model('mistbloom_koi_pair', 'Swimming Koi Pair')
    r, L = 5, 10
    koi3d(m, 'koi_a', 'x', -1, 8 - 0.55 * L, L, 3.3, 8 + r, 1.2, 1.7, 'kohaku', tail='h', dorsal=False, pect=False)
    koi3d(m, 'koi_b', 'x', 1, 8 + 0.55 * L, L, 3.2, 8 - r, 1.1, 1.5, 'showa', tail='h', dorsal=False, pect=False)
    rig = me.Rig(m.name, m, length=12.0)
    rig.bone('school', (0, 0, 0))
    rig.bone('base', (0, 0, 0))
    rig.bone('koi_a', (0, 3.3, r), 'school'); rig.bone('koi_a_tail', (0.86 * L - 0.55 * L, 3.3, r), 'koi_a')
    rig.bone('koi_b', (0, 3.2, -r), 'school'); rig.bone('koi_b_tail', (-(0.86 * L - 0.55 * L), 3.2, -r), 'koi_b')
    rig.assign(koi_rule(['koi_a', 'koi_b']))
    rig.bones['school'].key('rotation', spin_keys(12.0))
    swim(rig, 'school', 'koi_a', None, 18)
    swim(rig, 'school', 'koi_b', None, 18, phase=1.3)
    return rig

def koi_bowl_swim():
    """A kohaku and a little orange koi circling inside the Koi Bowl (animated)."""
    m = Model('mistbloom_koi_bowl_swim', 'Bowl Koi')
    r = 2.0
    koi3d(m, 'koi_a', 'x', -1, 8 - 0.55 * 6, 6, 9.4, 8 + r, 0.85, 0.75, 'kohaku', dorsal=False, pect=False)
    koi3d(m, 'koi_b', 'x', 1, 8 + 0.55 * 5, 5, 8.2, 8 - r, 0.75, 0.65, 'chagoi', dorsal=False, pect=False)
    rig = me.Rig(m.name, m, length=8.0)
    rig.bone('school', (0, 0, 0)); rig.bone('base', (0, 0, 0))
    rig.bone('koi_a', (0, 9.4, r), 'school'); rig.bone('koi_a_tail', (0.31 * 6, 9.4, r), 'koi_a')
    rig.bone('koi_b', (0, 8.2, -r), 'school'); rig.bone('koi_b_tail', (-0.31 * 5, 8.2, -r), 'koi_b')
    rig.assign(koi_rule(['koi_a', 'koi_b']))
    rig.bones['school'].key('rotation', spin_keys(8.0))
    swim(rig, 'school', 'koi_a', None, 12, wig=4, tail=25)
    swim(rig, 'school', 'koi_b', None, 14, wig=4, tail=28, phase=0.8)
    return rig

def koi_leap():
    """The statue koi, rocking on its splash with a swishing tail - sits on the statue (animated)."""
    m = Model('mistbloom_koi_leap', 'Leaping Koi')
    L = 13
    koi3d(m, 'koi', 'x', 1, 16, L, 16, 8, 2.1, 1.8, 'kohaku')
    rig = me.Rig(m.name, m, length=3.0)
    rig.bone('base', (0, 0, 0))
    rig.bone('koi', (0, 16, 0)); rig.bone('koi_tail', (16 - 0.86 * L - 8, 16, 0), 'koi')
    rig.assign(koi_rule(['koi']))
    n = 24
    rig.bones['koi'].key('rotation', me.rot_keys(3.0, z=(5, 1, 0, 45), y=(4, 2, 0.5, 0), n=n))
    rig.bones['koi'].key('position', [(3.0 * i / n, (0, 1.0 * math.sin(2 * math.pi * i / n + 1.2), 0)) for i in range(n + 1)])
    rig.bones['koi_tail'].key('rotation', me.rot_keys(3.0, y=(26, 3, 0, 0), n=n))
    return rig

def koi_streamer_wind():
    """The whole streamer pole, koi windsocks flapping in gusts. A stand-alone animated version."""
    m = Model('mistbloom_koi_streamer_wind', 'Koi Streamer (windy)')
    m.box('base', (4, 0, 4), (8, 3, 8), stone(course=3, moss=0.5), skip=['down'])
    m.box('pole', (7, 3, 7), (2, 27, 2), WOOD, skip=['down'])
    m.box('cap', (6.5, 30, 6.5), (3, 1.2, 3), CAP)
    m.box('ball', (7.25, 31.2, 7.25), (1.5, 0.75, 1.5), solid('brass', 1.4), res=2)
    cross(m, 'moss', 5, 3, 11, 3.5, 2.5, arts.grass(), res=2)
    m.plane('flag_cloth', (9, 18.5, 8), 'z', (5, 11), arts.streamer(), res=1)
    koi3d(m, 'koi_big', 'x', -1, 9, 13, 24, 8, 1.9, 1.9, 'magoi', dorsal=False, pect=False)
    koi3d(m, 'koi_small', 'x', -1, 9, 10, 17, 8, 1.5, 1.5, 'kohaku', dorsal=False, pect=False)
    rig = me.Rig(m.name, m, length=4.0)
    rig.bone('base', (0, 0, 0))
    rig.bone('flag', (1, 29.5, 0))
    rig.bone('koi_big', (1, 24, 0)); rig.bone('koi_big_tail', (1 + 0.86 * 13, 24, 0), 'koi_big')
    rig.bone('koi_small', (1, 17, 0)); rig.bone('koi_small_tail', (1 + 0.86 * 10, 17, 0), 'koi_small')
    def rule(n):
        if n.startswith('flag'): return 'flag'
        return koi_rule(['koi_big', 'koi_small'])(n)
    rig.assign(rule)
    n = 32
    rig.bones['flag'].key('rotation', me.rot_keys(4.0, z=(9, 2, 0.3, -22.5), x=(10, 3, 0, 0), n=n))
    rig.bones['koi_big'].key('rotation', me.rot_keys(4.0, z=(9, 1, 0, -22.5), y=(12, 2, 0.4, 0), x=(6, 3, 0, 0), n=n))
    rig.bones['koi_big_tail'].key('rotation', me.rot_keys(4.0, y=(22, 4, 1.0, 0), z=(6, 2, 0, 0), n=n))
    rig.bones['koi_small'].key('rotation', me.rot_keys(4.0, z=(11, 1, 1.4, -22.5), y=(14, 2, 2.0, 0), x=(7, 3, 1.0, 0), n=n))
    rig.bones['koi_small_tail'].key('rotation', me.rot_keys(4.0, y=(26, 5, 0.3, 0), z=(7, 2, 1.0, 0), n=n))
    return rig

def koi_school():
    """Three koi circling - drop it in any real pond (spawn it on the pond floor)."""
    m = Model('mistbloom_koi_school', 'Koi School')
    r, L = 10, 12
    pats = (('koi_a', 'kohaku', 4.0), ('koi_b', 'showa', 2.6), ('koi_c', 'sanke', 5.2))
    for name, pat, cy in pats:
        koi3d(m, name, 'x', -1, 8 - 0.55 * L, L, cy, 8 + r, 1.3, 1.6, pat)
    rig = me.Rig(m.name, m, length=15.0)
    rig.bone('base', (0, 0, 0))
    for i, (name, pat, cy) in enumerate(pats):
        rig.bone(f'{name}_path', (0, 0, 0))
        rig.bone(name, (0, cy, r), f'{name}_path')
        rig.bone(f'{name}_tail', (0.31 * L, cy, r), name)
        rig.bones[f'{name}_path'].key('rotation', spin_keys(15.0, start=120 * i))
    rig.assign(koi_rule([p[0] for p in pats]))
    for i, (name, pat, cy) in enumerate(pats):
        swim(rig, None, name, None, 20, wig=6, tail=24, bob=0.6, bob_cycles=3, phase=i * 1.1)
    return rig

RIGS = [koi_pair, koi_bowl_swim, koi_leap, koi_streamer_wind, koi_school]

# ======================================================= animated-water furniture
def without(model_fn, prefixes, new_name, title):
    m = model_fn()
    m.els = [e for e in m.els if not any(e.name.startswith(p) for p in prefixes)]
    m.name, m.title = new_name, title
    return m

def move(e, dx, dz):
    e.f = (e.f[0] + dx, e.f[1], e.f[2] + dz); e.t = (e.t[0] + dx, e.t[1], e.t[2] + dz)
    if e.rot:
        ax, ang, o = e.rot; e.rot = (ax, ang, (o[0] + dx, o[1], o[2] + dz))

def pond_open_middle():
    """pond without koi, big lily pad + lotus moved into the corner so the swimming koi have room"""
    m = without(pieces.koi_pond, ['koi_'], 'koi_pond_animated', '')
    for e in m.els:
        if e.name == 'pad_a' or e.name.startswith('lotus'):
            move(e, -13.5, -14.5)
    return m

VARIANTS = [
    ('koi_pond_animated', 'Koi Pond Basin (rippling)', pond_open_middle,
     'koi_pond', 'Water ripples. Add the Swimming Koi Pair for fish.', 'mistbloom_koi_pair'),
    ('koi_bowl_animated', 'Koi Bowl (rippling)', lambda: without(pieces.koi_bowl, ['koi_'], 'koi_bowl_animated', ''),
     'koi_bowl', 'Water ripples. Add the Bowl Koi for fish.', 'mistbloom_koi_bowl_swim'),
    ('koi_statue_animated', 'Koi Splash Statue', lambda: without(pieces.koi_statue, ['koi_'], 'koi_statue_animated', ''),
     'koi_statue', 'The splash, waiting for its Leaping Koi.', 'mistbloom_koi_leap'),
    ('koi_table_animated', 'Koi Pool Tea Table (rippling)', pieces.koi_table,
     'koi_table', 'The little pool on top ripples.', None),
]

def bake_animated(fn):
    frames, layout = [], None
    for f in range(FRAMES):
        arts.FRAME[0] = (f, FRAMES)
        m = fn(); m.bake()
        lay = [(e.name, tuple(sorted(e.uv.items()))) for e in m.els]
        assert layout is None or lay == layout, 'uv layout changed between frames'
        layout = lay; frames.append(m.atlas)
    arts.FRAME[0] = None
    return m, np.concatenate(frames, axis=0)

def seal(icon):
    """small water-drop seal in the corner so the rippling variants are told apart in inventories"""
    im = icon.copy(); px = im.load()
    for (x, y, c) in ((14, 13, (124, 203, 208)), (13, 14, (69, 150, 163)), (14, 14, (69, 150, 163)), (15, 14, (45, 111, 126)),
                      (14, 15, (27, 73, 87)), (13, 15, (45, 111, 126)), (15, 15, (27, 73, 87))):
        px[x, y] = c + (255,)
    return im

def w(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, 'w').write(dump(data))

MOB_TPL = """{id}:
  Type: ARMOR_STAND
  # {title}
  Health: 1
  Options:
    Marker: true
    Invisible: true
    Invincible: true
    NoGravity: true
    Silent: true
    Persistent: true
    Despawn: false
    PreventOtherDrops: true
  Skills:
  - model{{m={id}}} @self ~onSpawn
  - model{{m={id}}} @self ~onLoad
"""

def main():
    shutil.rmtree(OUT, ignore_errors=True)
    os.makedirs('out/previews', exist_ok=True)
    icons = sprites.render_all()
    # ---- ModelEngine blueprints + MythicMobs
    mobs = ['# Mistbloom - Koi Garden, animated koi (ModelEngine)', '# Spawn with: /mm m spawn <name> 1 <world>,<x>,<y>,<z>', '']
    for fn in RIGS:
        rig = fn()
        w(f'{OUT}/plugins/ModelEngine/blueprints/mistbloom/{rig.name}.bbmodel', rig.bbmodel())
        mobs.append(MOB_TPL.format(id=rig.name, title=rig.model.title))
    os.makedirs(f'{OUT}/plugins/MythicMobs/mobs', exist_ok=True)
    open(f'{OUT}/plugins/MythicMobs/mobs/mistbloom_koi_animated.yml', 'w').write('\n'.join(mobs))
    # ---- animated water furniture
    yml = ['# Mistbloom - Koi Garden (animated add-on)', '# Works alongside the base set; nothing here replaces it.', '']
    for vid, title, fn, base_icon, lore, partner in VARIANTS:
        m, strip = bake_animated(fn)
        m.check()
        m.title = title
        model = m.export(NS, f'item/{SET}/{vid}')
        w(f'{A}/models/{SET}/{vid}.json', model)
        os.makedirs(f'{A}/textures/item/{SET}', exist_ok=True)
        Image.fromarray(strip, 'RGBA').save(f'{A}/textures/item/{SET}/{vid}.png', optimize=True)
        open(f'{A}/textures/item/{SET}/{vid}.png.mcmeta', 'w').write(dump({'animation': {'frametime': FRAMETIME, 'interpolate': False}}))
        seal(icons[base_icon]).save(f'{A}/textures/item/{SET}/{vid}_icon.png', optimize=True)
        w(f'{A}/models/item/{SET}/{vid}_icon.json', {'parent': 'minecraft:item/generated', 'textures': {'layer0': f'{NS}:item/{SET}/{vid}_icon'}})
        w(f'{A}/items/{SET}/{vid}.json', {'model': {
            'type': 'minecraft:select', 'property': 'minecraft:display_context',
            'cases': [{'when': HAND, 'model': {'type': 'minecraft:model', 'model': f'{NS}:item/{SET}/{vid}_icon'}}],
            'fallback': {'type': 'minecraft:model', 'model': f'{NS}:{SET}/{vid}'}}})
        meta = m.meta
        yml += [f'{vid}:', f'  itemname: "<#f2e6cc>{title}"', '  material: PAPER', '  lore:', f'    - "<gray>{lore}"', '    - "<#9fb3d9>Koi Garden"',
                '  Components:', f'    item_model: {NS}:{SET}/{vid}', '  Mechanics:', '    furniture:',
                '      properties:', '        display_transform: NONE', '      rotatable: true',
                '      limited_placing:', '        floor: true', '        wall: false', '        roof: false',
                '      hitbox:', '        barriers:'] + [f'          - {b}' for b in meta['hitbox']] + ['']
        # preview of the water animation
        prev = []
        for f in range(FRAMES):
            m.atlas = strip[f * m.size:(f + 1) * m.size]
            import render
            prev.append(render.on_bg(render.render(m, 35, 40, 12)).convert('P', palette=Image.ADAPTIVE))
        prev[0].save(f'out/previews/{vid}.gif', save_all=True, append_images=prev[1:], duration=FRAMETIME * 50, loop=0)
    os.makedirs(f'{OUT}/plugins/Nexo/items', exist_ok=True)
    open(f'{OUT}/plugins/Nexo/items/mistbloom_koi_garden_animated.yml', 'w').write('\n'.join(yml))
    w(f'{PACK}/pack.mcmeta', {'pack': {'pack_format': 46, 'description': 'Mistbloom - Koi Garden (animated add-on)'}})
    z = 'out/mistbloom_koi_garden_animated.zip'
    if os.path.exists(z): os.remove(z)
    with zipfile.ZipFile(z, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(OUT):
            for f in sorted(files):
                p = os.path.join(root, f); zf.write(p, os.path.relpath(p, OUT))
    return z

if __name__ == '__main__':
    print(main())
