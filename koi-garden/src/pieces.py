"""Mistbloom - Koi Garden set, 12 pieces. Triad: teak wood + garden stone + dyeable cushions,
brass for tiny accents, classic koi (kohaku / sanke / showa / chagoi / magoi)."""
import math
import numpy as np
from engine import (Model, Koi, MI, solid, wood, endgrain, capped, stone, fabric, overlay,
                    panel, wave, tail_card, fin_card, pect_card)
import arts

# ------------------------------------------------------------- helpers
def cross(m, name, cx, y, cz, w, h, paint, res=1):
    for k, ang in ((1, 45), (2, -45)):
        m.plane(f'{name}_{("a", "b")[k - 1]}', (cx - w / 2, y, cz), 'z', (w, h), paint, res=res, rot=('y', ang, (cx, y, cz)))

def flip(p):
    """mirror a card painter horizontally"""
    def q(c):
        p(c)
        c.M[:] = c.M[:, ::-1]; c.T[:] = c.T[:, ::-1]; c.A[:] = c.A[:, ::-1]
    return q

def transpose(p):
    def q(c):
        # paint on a transposed context then swap back
        from engine import Ctx
        h, w = c.h, c.w
        c.h, c.w = w, h
        c.M = np.full((w, h), -1, int); c.T = np.full((w, h), 2.0); c.A = np.full((w, h), 255, int)
        c.u, c.v = c.v.T, c.u.T
        p(c)
        c.M, c.T, c.A = c.M.T.copy(), c.T.T.copy(), c.A.T.copy()
        c.h, c.w = h, w
        c.u, c.v = c.v.T, c.u.T
    return q

def koi3d(m, name, axis, head, nose, L, cy, cw, hh, hw, pattern, rot=None,
          tail='v', dorsal=True, pect=True, res=2):
    """head/body cubes + tail/dorsal/pectoral cards; every part shares the koi's rotation."""
    k = Koi(axis, head, nose, L, cy, cw, hh, hw, pattern)
    along = lambda t: nose - head * t * L
    def span(t0, t1):
        a, b = along(t0), along(t1)
        return min(a, b), max(a, b)
    a0, a1 = span(0.0, 0.28)
    b0, b1 = span(0.25, 0.92)
    if axis == 'x':
        m.cube(f'{name}_head', (a0, cy - hh * 0.85, cw - hw * 0.85), (a1, cy + hh * 0.85, cw + hw * 0.85), k.painter('head'), res=res, rot=rot)
        m.cube(f'{name}_body', (b0, cy - hh, cw - hw), (b1, cy + hh, cw + hw), k.painter('body'), res=res, rot=rot)
    else:
        m.cube(f'{name}_head', (cw - hw * 0.85, cy - hh * 0.85, a0), (cw + hw * 0.85, cy + hh * 0.85, a1), k.painter('head'), res=res, rot=rot)
        m.cube(f'{name}_body', (cw - hw, cy - hh, b0), (cw + hw, cy + hh, b1), k.painter('body'), res=res, rot=rot)
    fm = k.fin_mat()
    t0, t1 = span(0.86, 1.36)
    tl = t1 - t0
    grows_pos = head == -1   # tail extends toward +axis
    if tail == 'v':
        p = tail_card(fm)
        th = hh * 2.6
        if axis == 'x':
            m.plane(f'{name}_tail', (t0, cy - th / 2, cw), 'z', (tl, th), p if grows_pos else flip(p), res=res, rot=rot)
        else:
            m.plane(f'{name}_tail', (cw, cy - th / 2, t0), 'x', (tl, th), p if grows_pos else flip(p), res=res, rot=rot)
    else:  # flat tail lying on the water
        tw = hw * 3.0
        p = tail_card(fm)
        if axis == 'x':
            m.plane(f'{name}_tail', (t0, cy + hh * 0.2, cw - tw / 2), 'y', (tl, tw), p if grows_pos else flip(p), res=res, rot=rot)
        else:
            q = transpose(p)
            # y-plane art: u along x, v along z(top=north). tail grows along z.
            m.plane(f'{name}_tail', (cw - tw / 2, cy + hh * 0.2, t0), 'y', (tw, tl), q if grows_pos else _vflip(q), res=res, rot=rot)
    if dorsal:
        d0, d1 = span(0.36, 0.72)
        dh = hh * 0.9
        p = fin_card(fm)
        # fin leans toward the tail
        lean_ok = head == 1
        if axis == 'x':
            m.plane(f'{name}_top_fin', (d0, cy + hh - 0.1, cw), 'z', (d1 - d0, dh), p if lean_ok else flip(p), res=res, rot=rot)
        else:
            m.plane(f'{name}_top_fin', (cw, cy + hh - 0.1, d0), 'x', (d1 - d0, dh), p if not lean_ok else flip(p), res=res, rot=rot)
    if pect:
        p0, p1 = span(0.24, 0.42)
        pw = hw * 3.4
        if axis == 'x':
            m.plane(f'{name}_fins', (p0, cy - hh * 0.55, cw - pw / 2), 'y', (p1 - p0, pw), pect_card(fm), res=res, rot=rot)
        else:
            m.plane(f'{name}_fins', (cw - pw / 2, cy - hh * 0.55, p0), 'y', (pw, p1 - p0), transpose(pect_card(fm)), res=res, rot=rot)
    return k

def _vflip(p):
    def q(c):
        p(c)
        c.M[:] = c.M[::-1]; c.T[:] = c.T[::-1]; c.A[:] = c.A[::-1]
    return q

WOOD = wood('teak')
CAP = capped(wood('teak'), endgrain('teak'))

# ================================================================= pieces
def koi_statue():
    m = Model('koi_statue', 'Leaping Koi Statue')
    m.box('base', (1, 0, 1), (14, 2, 14), stone(course=2, moss=0.4), skip=['down'])
    m.box('plinth', (3, 2, 3), (10, 5, 10), stone(course=2.5), skip=['down'])
    m.box('cap', (2, 7, 2), (12, 1.5, 12), stone(course=2))
    m.box('mound', (4, 8.5, 4), (8, 3, 8), {'up': stone(course=8), '*': overlay(stone(course=8), wave())}, skip=['down'])
    cross(m, 'splash', 8, 9.5, 8, 11, 6, arts.splash(), res=2)
    rot = ('z', 45, (8, 16, 8))
    koi3d(m, 'koi', 'x', 1, 16, 13, 16, 8, 2.1, 1.8, 'kohaku', rot=rot)
    cross(m, 'moss', 2.8, 2, 13.2, 4, 3, arts.grass(), res=2)
    m.meta = {'hitbox': ['0,0,0', '0,1,0'], 'size': '1x2'}
    return m

def koi_lilypad():
    m = Model('koi_lilypad', 'Koi & Lily Pad')
    m.plane('pad', (0.5, 0.15, 0.5), 'y', (12, 12), arts.lilypad(0.6), res=2)
    m.plane('pad_small', (10, 0.25, 1.5), 'y', (5.5, 5.5), arts.lilypad(2.4), res=2)
    m.box('pod', (4.6, 0.15, 4.6), (2, 1.4, 2), {'up': solid('yellow', 1.4), '*': solid('lily', 1.6)}, res=2, skip=['down'])
    cross(m, 'lotus', 5.6, 0.4, 5.6, 6, 5, arts.petal_fan(), res=2)
    m.plane('lotus_ring', (2.6, 0.6, 2.6), 'y', (6, 6), arts.petal_ring(), res=2)
    koi3d(m, 'koi', 'x', -1, 1.5, 11, 1.85, 12.5, 1.4, 1.7, 'sanke', rot=('y', 22.5, (8, 1.85, 12.5)))
    m.meta = {'hitbox': [], 'size': '1x1 (walk-through)'}
    return m

def glass():
    def p(c):
        c.fill('glass', 1.6)
        c.A[:] = 45
        if c.face == 'up':
            c.A[:] = 0
            k = c.res
            ring = np.zeros((c.h, c.w), bool); ring[:k] = ring[-k:] = True; ring[:, :k] = ring[:, -k:] = True
            c.M[ring] = MI['brass']; c.T[ring] = 1.6; c.A[ring] = 255
            c.M[~ring] = -1
        elif c.face != 'down':
            c.M[:c.res] = MI['brass']; c.T[:c.res] = 1.4; c.A[:c.res] = 255
            # one soft vertical highlight streak (structured)
            x = c.w // 4
            c.T[c.res + 1:, x:x + c.res] = 0.2; c.A[c.res + 1:, x:x + c.res] = 150
    return p

def water(alpha=150, rip=True):
    def p(c):
        c.fill('water', 2.0); c.A[:] = alpha
        if c.face == 'up' and rip:
            arts.ripples(c, [(c.w * 0.3, c.h * 0.35, 2.2 * c.res), (c.w * 0.7, c.h * 0.7, 3 * c.res),
                             (c.w * 0.75, c.h * 0.25, 1.4 * c.res)], tone=1.0)
            c.T[c.M == MI['water']] -= 0.25
    return p

def koi_bowl():
    m = Model('koi_bowl', 'Koi Bowl on Teak Stand')
    m.box('top', (1, 4, 1), (14, 1.5, 14), CAP)
    for i, (x, z) in enumerate(((2, 2), (11, 2), (2, 11), (11, 11))):
        m.box(('leg_back_left', 'leg_back_right', 'leg_front_left', 'leg_front_right')[i], (x, 0, z), (3, 4, 3), WOOD, skip=['up', 'down'])
    m.box('glass', (2.5, 5.5, 2.5), (11, 8, 11), glass(), res=2)
    m.box('pebbles', (3, 5.5, 3), (10, 1, 10), stone(course=1), skip=['down'])
    m.box('water', (3, 6.5, 3), (10, 5, 10), water(70), res=2, skip=['down'])
    koi3d(m, 'koi_a', 'x', -1, 4.2, 6.5, 9.2, 6.5, 0.9, 0.8, 'kohaku', tail='v', dorsal=False, pect=False, rot=('y', 22.5, (7.5, 9.2, 6.5)))
    koi3d(m, 'koi_b', 'z', 1, 12.4, 6, 7.8, 9.8, 0.8, 0.7, 'chagoi', tail='v', dorsal=False, pect=False)
    cross(m, 'weed', 11.3, 6.5, 4.3, 3, 4.5, arts.grass(every=1, minh=0.5), res=2)
    m.meta = {'hitbox': ['0,0,0'], 'size': '1x1'}
    return m

def plaque_board():
    def front(c):
        arts_wood = wood('teak', plank=3)
        arts_wood(c)
        if c.face == 'south':
            panel(1)(c)
            # carved ripple band across the lower third, half-step darker
            for x in range(2, c.w - 2):
                y = int(round(c.h * 0.78 + 0.8 * math.sin(x * 0.9)))
                c.set(x, y, tone=3.0)
            # gold crescent moon inlay, top right
            yy, xx = np.mgrid[0:c.h, 0:c.w]
            cx, cy = c.w - 3.6, 3.4
            d1 = np.hypot(xx - cx, yy - cy); d2 = np.hypot(xx - cx - 0.9, yy - cy + 0.6)
            moon = (d1 < 1.7) & (d2 > 1.4)
            c.M[moon] = MI['brass']; c.T[moon] = 1.0
    return front

def koi_plaque():
    m = Model('koi_plaque', 'Twin Koi Wall Plaque')
    m.box('board', (1, 2, 0), (14, 11, 1.5), plaque_board())
    m.box('cap', (0, 13, 0), (16, 1.5, 2.5), CAP)
    m.box('ledge', (0.5, 1, 0), (15, 1, 2.2), WOOD)
    m.plane('rope', (4, 14.5, 0.8), 'z', (8, 3.5), arts.rope_v(), res=2)
    m.box('nail', (7.5, 17.5, 0.3), (1, 1, 1), solid('brass', 1.5))
    koi3d(m, 'koi_a', 'x', -1, 2.6, 7.6, 9.6, 2.1, 1.15, 0.6, 'kohaku', dorsal=False, pect=False, rot=('z', 22.5, (7.5, 9.6, 2.1)))
    koi3d(m, 'koi_b', 'x', 1, 13.4, 7.6, 5.4, 2.1, 1.15, 0.6, 'showa', dorsal=False, pect=False, rot=('z', 22.5, (8.5, 5.4, 2.1)))
    cross(m, 'bud', 2.6, 2, 1.3, 2.6, 3.5, arts.petal_fan(), res=2)
    m.meta = {'hitbox': ['0,0,0'], 'size': 'wall, 1x1', 'wall': True}
    return m

def pond_water():
    def p(c):
        c.fill('water', 2.2)
        arts.ripples(c, [(6, 7, 2.5), (19, 18, 3.5), (21, 6, 1.8), (8, 20, 1.5)], tone=1.2)
        # soft deep centre, structured rings (half-step)
        yy, xx = np.mgrid[0:c.h, 0:c.w]
        d = np.hypot(xx - c.w / 2, yy - c.h / 2)
        c.T[(d < c.w * 0.28) & (c.T > 2)] += 0.5
    return p

def koi_pond():
    m = Model('koi_pond', 'Koi Pond Basin')
    rim = stone(course=2.5, moss=0.5)
    m.box('rim_n', (0, 0, 0), (32, 5, 3), rim, skip=['down'])
    m.box('rim_s', (0, 0, 29), (32, 5, 3), rim, skip=['down'])
    m.box('rim_w', (0, 0, 3), (3, 5, 26), rim, skip=['down'])
    m.box('rim_e', (29, 0, 3), (3, 5, 26), rim, skip=['down'])
    m.box('water', (3, 0, 3), (26, 3.5, 26), pond_water(), skip=['down', 'north', 'south', 'east', 'west'])
    koi3d(m, 'koi_a', 'x', 1, 23, 12, 3.4, 11, 1.2, 1.7, 'kohaku', tail='h', dorsal=False, pect=False, rot=('y', 22.5, (17, 3.4, 11)))
    koi3d(m, 'koi_b', 'z', -1, 8, 11, 3.3, 9, 1.1, 1.5, 'showa', tail='h', dorsal=False, pect=False, rot=('y', -22.5, (9, 3.3, 14)))
    m.plane('pad_a', (17, 3.6, 18), 'y', (8, 8), arts.lilypad(2.2), res=2)
    m.plane('pad_b', (22, 3.65, 5), 'y', (5, 5), arts.lilypad(4.0), res=2)
    cross(m, 'lotus', 21, 3.7, 22, 5, 4.5, arts.petal_fan(), res=2)
    cross(m, 'reeds', 5.2, 3.5, 26.5, 6, 14, arts.reeds(), res=2)
    m.meta = {'hitbox': ['0,0,0', '1,0,0', '0,0,1', '1,0,1'], 'size': '2x2'}
    return m

def koi_stepping_stone():
    m = Model('koi_stepping_stone', 'Garden Stepping Stones')
    r1 = ('y', 22.5, (7, 0, 7)); r2 = ('y', -22.5, (12.5, 0, 13))
    m.box('stone_a', (1, 0, 2), (12, 1.4, 10), stone(course=8), rot=r1, skip=['down'])
    m.box('stone_a_top', (2, 1.4, 3), (10, 0.8, 8), stone(course=8), rot=r1, skip=['down'])
    m.box('stone_b', (10, 0, 11), (5.5, 1, 4.5), stone(course=8), rot=r2, skip=['down'])
    m.box('stone_b_top', (10.75, 1, 11.75), (4, 0.5, 3), stone(course=8), rot=r2, skip=['down'])
    m.box('pebble_a', (13, 0, 3.5), (1.5, 1, 1.5), solid('stone', 1.6), skip=['down'])
    m.box('pebble_b', (2, 0, 13), (1.2, 0.8, 1.2), solid('stone', 2.2), skip=['down'])
    cross(m, 'moss', 6, 0, 13.5, 5, 2.5, arts.grass(every=1, minh=0.4), res=2)
    m.meta = {'hitbox': [], 'size': '1x1 (walk-through)'}
    return m

def koi_lilypads():
    m = Model('koi_lilypads', 'Lily Pad Cluster')
    m.plane('pad_a', (0.5, 0.1, 1), 'y', (10, 10), arts.lilypad(0.4), res=2)
    m.plane('pad_b', (8, 0.2, 7), 'y', (7.5, 7.5), arts.lilypad(2.8), res=2)
    m.plane('pad_c', (1.5, 0.3, 10), 'y', (5.5, 5.5), arts.lilypad(5.0), res=2)
    m.plane('pad_d', (11, 0.15, 1), 'y', (4, 4), arts.lilypad(1.5), res=2)
    m.plane('pad_curl', (9.5, 0.4, 11), 'y', (5, 5), arts.lilypad(3.6), res=2, rot=('x', 22.5, (12, 0.4, 13.5)))
    m.box('pod', (4.5, 0.1, 5), (2, 1.3, 2), {'up': solid('yellow', 1.4), '*': solid('lily', 1.6)}, res=2, skip=['down'])
    cross(m, 'lotus', 5.5, 0.3, 6, 6, 5, arts.petal_fan(), res=2)
    m.plane('lotus_ring', (2.5, 0.55, 3), 'y', (6, 6), arts.petal_ring(), res=2)
    m.box('stem', (11.4, 0.2, 9.9), (0.8, 3.2, 0.8), solid('lily', 2.2), res=2, skip=['down'])
    cross(m, 'bud', 11.8, 3.2, 10.3, 2.8, 3.6, arts.petal_fan(), res=2)
    m.meta = {'hitbox': [], 'size': '1x1 (walk-through)'}
    return m

def moss_clump():
    def p(c):
        c.fill('moss', 2.0)
        yy, xx = np.mgrid[0:c.h, 0:c.w]
        if c.face == 'up':
            c.T += 0.35 * ((yy // 2) % 2) - 0.15
        else:
            c.T += 0.5 * (yy / max(c.h - 1, 1))
    return p

def koi_reeds():
    m = Model('koi_reeds', 'Pond Reeds & Cattails')
    m.box('clump', (3, 0, 3), (10, 1.5, 10), moss_clump(), skip=['down'])
    m.box('rock', (9, 0, 2), (5, 2.5, 4), stone(course=8), rot=('y', 22.5, (11.5, 0, 4)), skip=['down'])
    cross(m, 'cattails', 6.5, 1.5, 7, 8, 22, arts.reeds(), res=1)
    cross(m, 'iris', 10.5, 1.5, 10, 6, 15, arts.reeds(heads=False, flower='yellow'), res=1)
    cross(m, 'grass', 6.5, 1.5, 12, 5, 10, arts.grass(every=1), res=1)
    m.plane('pad', (0.5, 0.1, 9.5), 'y', (6, 6), arts.lilypad(0.9), res=2)
    m.meta = {'hitbox': [], 'size': '1x1, 1.5 tall (walk-through)'}
    return m

def koi_inlay_rail():
    def p(c):
        wood('teak', plank=2)(c)
        if c.face == 'north':  # back face: twin koi inlay chasing each other
            arts.koi_sprite(c, 3, 0, 'kohaku', rot=1)                 # nose left
            arts.koi_sprite(c, c.w - 15, 1, 'showa', rot=3)          # nose right
    return p

def koi_bench():
    m = Model('koi_bench', 'Koi Garden Bench')
    for i, (x, z, h) in enumerate(((2, 9, 6), (27, 9, 6), (2, 2.5, 17), (27, 2.5, 17))):
        m.box(('leg_front_left', 'leg_front_right', 'post_left', 'post_right')[i], (x, 0, z), (3, h, 3), WOOD, skip=['down'])
    m.box('seat', (0, 6, 1.5), (32, 2, 12.5), WOOD)
    m.box('apron', (5, 4, 10.5), (22, 2, 1.5), overlay(WOOD, wave(only=['south'])), skip=['up', 'down'])
    m.box('cushion', (5.5, 8, 5.5), (21, 2, 7.5), fabric(), tint=True)
    m.box('cap_l', (1.5, 17, 2), (4, 1.5, 4), CAP)
    m.box('cap_r', (26.5, 17, 2), (4, 1.5, 4), CAP)
    m.box('rail', (5, 14, 3), (22, 3, 2), overlay(WOOD, wave(only=['south', 'north'])))
    m.box('back', (5, 8, 3.5), (22, 7, 1), koi_inlay_rail(), res=1, skip=['up', 'down'])
    m.box('back_cush_l', (6, 8.5, 4.5), (10, 6, 2), fabric(), tint=True)
    m.box('back_cush_r', (16, 8.5, 4.5), (10, 6, 2), fabric(), tint=True)
    m.plane('ivy', (1.95, 0, 9), 'x', (3, 6), arts.ivy(), res=2)
    m.meta = {'hitbox': ['0,0,0', '1,0,0'], 'seats': ['0,0,0', '1,0,0'], 'size': '2x1, dyeable cushions'}
    return m

def table_top():
    def p(c):
        wood('teak', plank=4)(c)
        if c.face == 'up':
            yy, xx = np.mgrid[0:c.h, 0:c.w] + 0.5
            cx, cy = c.w / 2, c.h / 2
            r = np.hypot(xx - cx, yy - cy)
            R = c.w * 0.40
            pool = r < R
            c.M[pool] = MI['water']; c.T[pool] = 2.4
            ring = np.abs(r - R) < 0.7
            c.M[ring] = MI['brass']; c.T[ring] = 1.3
            if arts.FRAME[0] is not None:
                arts.ripples(c, [(cx - 6, cy + 5, 3), (cx + 7, cy - 4, 2.5)], tone=1.3)
            rr = R * 0.52
            # while baking the animated strip the two koi swim one lap round the pool per loop
            ph = 0.0 if arts.FRAME[0] is None else -2 * math.pi * arts.FRAME[0][0] / arts.FRAME[0][1]
            arts.koi_field(c, arts.arc(cx, cy, rr, 0.2 + ph, 0.2 + 2.4 + ph), 2.5, 'kohaku')
            arts.koi_field(c, arts.arc(cx, cy, rr, 0.2 + math.pi + ph, 0.2 + math.pi + 2.4 + ph), 2.5, 'showa')
    return p

def koi_table():
    m = Model('koi_table', 'Koi Pool Tea Table')
    m.box('top', (0, 6, 0), (16, 1.5, 16), {'up': table_top(), '*': WOOD}, res=2)
    for i, (x, z) in enumerate(((2, 2), (11, 2), (2, 11), (11, 11))):
        m.box(('leg_back_left', 'leg_back_right', 'leg_front_left', 'leg_front_right')[i], (x, 0, z), (3, 6, 3), WOOD, skip=['up', 'down'])
    m.box('apron', (2.5, 4.5, 2.5), (11, 1.5, 11), overlay(WOOD, wave()), skip=['up'])
    m.box('pot', (0.5, 7.5, 0.5), (3, 2.5, 3), {'up': solid('moss', 2.6), '*': overlay(solid('clay', 2), panel(0))}, skip=['down'])
    cross(m, 'sprout', 2, 9.5, 2, 4, 4.5, arts.sprout(), res=2)
    m.box('cup', (12.6, 7.5, 12.6), (2.4, 2, 2.4), {'up': lambda c: (c.fill('kwhite', 1.6), c.mask(np.ones((c.h, c.w), bool), tone=1.6),
                                                     _cup_top(c)), '*': _cup_side}, res=2, skip=['down'])
    m.meta = {'hitbox': ['0,0,0'], 'size': '1x1'}
    return m

def _cup_top(c):
    c.M[1:-1, 1:-1] = MI['moss']; c.T[1:-1, 1:-1] = 2.4  # green tea

def _cup_side(c):
    c.fill('kwhite', 1.8)
    c.M[1:2] = MI['water']; c.T[1:2] = 2.0  # blue band

def screen_panel(pattern, y0, flipy=False, flipx=False):
    def p(c):
        if c.face in ('north', 'south'):
            c.fill('paper', 1.6)
            yy, xx = np.mgrid[0:c.h, 0:c.w]
            pool = (yy >= y0 - 2) & (yy <= y0 + 13)
            c.M[pool] = MI['water']; c.T[pool] = 0.9 + 0.3 * ((yy[pool] // 2) % 2)  # pale pool wash
            # ripple dashes, light teal
            for y in (2 + y0 % 3, c.h - 4 - y0 % 2):
                for x in range(2, c.w - 2):
                    if (x + y) % 4 < 2: c.set(x, y, mat='water', tone=1.2)
            arts.koi_sprite(c, 1, y0, pattern, flipx=flipx, flipy=flipy)
            fr = (xx == 0) | (xx == c.w - 1) | (yy == 0) | (yy == c.h - 1)
            c.M[fr] = MI['teak']; c.T[fr] = 2.2
        else:
            wood('teak', plank=1)(c)
    return p

def koi_screen():
    m = Model('koi_screen', 'Koi Folding Screen')
    panels = (('l', -4, ('y', 22.5, (4, 2, 7.5)), 'kohaku', 8, True),
              ('c', 4, None, 'showa', 5, False),
              ('r', 12, ('y', -22.5, (12, 2, 7.5)), 'sanke', 9, True))
    for n, x, rot, pat, y0, fy in panels:
        m.box(f'panel_{n}', (x, 2, 7), (8, 26, 1), screen_panel(pat, y0, flipy=fy, flipx=(n == 'r')), rot=rot)
        m.box(f'foot_{n}', (x + 0.5, 0, 6), (7, 2, 3), WOOD, rot=rot, skip=['down'])
        m.box(f'cap_{n}', (x - 0.25, 28, 6.75), (8.5, 1.5, 1.5), CAP, rot=rot)
    m.plane('ivy', (-3.5, 2, 8.05), 'z', (3, 10), arts.ivy(), res=2, rot=('y', 22.5, (4, 2, 7.5)))
    m.meta = {'hitbox': ['0,0,0', '0,1,0'], 'size': '1x2'}
    return m

def koi_streamer():
    m = Model('koi_streamer', 'Koi Streamer Pole')
    m.box('base', (4, 0, 4), (8, 3, 8), stone(course=3, moss=0.5), skip=['down'])
    m.box('pole', (7, 3, 7), (2, 27, 2), WOOD, skip=['down'])
    m.box('cap', (6.5, 30, 6.5), (3, 1.2, 3), CAP)
    m.box('ball', (7.25, 31.2, 7.25), (1.5, 0.75, 1.5), solid('brass', 1.4), res=2)
    m.plane('cloth', (9, 18.5, 8), 'z', (5, 11), arts.streamer(), res=1, rot=('z', -22.5, (9, 29.5, 8)))
    koi3d(m, 'koi_big', 'x', -1, 9, 13, 24, 8, 1.9, 1.9, 'magoi', dorsal=False, pect=False, rot=('z', -22.5, (9, 24, 8)))
    koi3d(m, 'koi_small', 'x', -1, 9, 10, 17, 8, 1.5, 1.5, 'kohaku', dorsal=False, pect=False, rot=('z', -22.5, (9, 17, 8)))
    cross(m, 'moss', 5, 3, 11, 3.5, 2.5, arts.grass(), res=2)
    m.meta = {'hitbox': ['0,0,0', '0,1,0'], 'size': '1x2'}
    return m

ALL = [koi_statue, koi_lilypad, koi_bowl, koi_plaque, koi_pond, koi_stepping_stone,
       koi_lilypads, koi_reeds, koi_bench, koi_table, koi_screen, koi_streamer]
