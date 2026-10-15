import addon, pieces, arts
from addon import without
def scene(fn, off):
    arts.FRAME[0] = (0, 8); m = fn(); m.bake(); arts.FRAME[0] = None
    return (m, off)
jobs = [
    (addon.koi_pair, scene(addon.pond_open_middle, (-16, 0, -16)), 10),
    (addon.koi_bowl_swim, scene(lambda: without(pieces.koi_bowl, ['koi_'], 'b', ''), (-8, 0, -8)), 14),
    (addon.koi_leap, scene(lambda: without(pieces.koi_statue, ['koi_'], 's', ''), (-8, 0, -8)), 11),
    (addon.koi_streamer_wind, None, 9),
    (addon.koi_school, None, 8),
]
import sys
only = sys.argv[1:]
for fn, sc, scale in jobs:
    if only and fn.__name__ not in only: continue
    rig = fn(); rig.model.bake()
    rig.gif2(f'out/previews/{rig.name}.gif', fps=10, scene=sc, scale=scale)
    print(rig.name)
