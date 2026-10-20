"""Rosewick Garden v2 (Oct 19 2026): all 14 pieces rebuilt in the Mistbloom house style.
Soft streak birch, soft stone, copper, hand-drawn flowers. Every model <= 14 elements.
Built with the front facing +z (south); pack.py half-turns them so the front faces the player."""
import numpy as np
from engine import Model, MI, solid, capped, pxmat
from arts import grass, ivy, rows_art
import rw_arts as A

# ------------------------------------------------------------------ materials
WOOD = pxmat('birch', 'wood')
WOODV = pxmat('birch', 'woodv')
ENDG = pxmat('birch', 'plain', base=1)
POST = capped(WOODV, ENDG)
RAIL = capped(WOOD, WOOD)
STONE = pxmat('stone', 'tile', block=4)
STONE_BIG = pxmat('stone', 'tile', block=8)
CLAY = pxmat('clay', 'plain')

GNOMON = ["c....", "cc...", "ccc..", "cccc."]
HANDLE = ["..hhh..", ".h...h.", "h.....h"]

def pot(): return {'up': A.soil_top(), '*': CLAY}

def fabric(mat='grey'):
    """tufted cushion tiles lit top-left, shadowed bottom-right, a button in the middle"""
    def d(t, u, v, c):
        if c.face != 'down':
            tu, tv = u % 5, v % 5
            t[(tu == 4) | (tv == 4)] = 3
            t[((tu == 0) | (tv == 0)) & (tu < 4) & (tv < 4)] = 1
            t[(tu == 2) & (tv == 2)] = 3
    return pxmat(mat, 'plain', base=2, detail=d)

def cross(m, name, cx, y, cz, w, h, paint):
    for k, ang in ((1, 45), (2, -45)):
        m.plane(f'{name}_{"ab"[k - 1]}', (cx - w / 2, y, cz), 'z', (w, h), paint, rot=('y', ang, (cx, y, cz)))

def shift(m, dx=0.0, dy=0.0, dz=0.0):
    for e in m.els:
        e.f = (e.f[0] + dx, e.f[1] + dy, e.f[2] + dz); e.t = (e.t[0] + dx, e.t[1] + dy, e.t[2] + dz)
        if e.rot:
            ax, ang, o = e.rot; e.rot = (ax, ang, (o[0] + dx, o[1] + dy, o[2] + dz))
    return m

# ================================================================== pieces
def garden_bench():
    m = Model('garden_bench', 'Garden Bench')
    m.box('post_left', (1, 0, 2), (3, 18, 3), POST, skip=['down'])
    m.box('post_right', (28, 0, 2), (3, 18, 3), POST, skip=['down'])
    m.box('leg_front_left', (1, 0, 11.5), (3, 11, 3), WOODV, skip=['down'])
    m.box('leg_front_right', (28, 0, 11.5), (3, 11, 3), WOODV, skip=['down'])
    m.box('seat', (0, 5.5, 2.5), (32, 2.5, 12.5), RAIL)
    m.box('arm_left', (0.5, 10, 2.5), (4, 1.5, 12.5), RAIL)
    m.box('arm_right', (27.5, 10, 2.5), (4, 1.5, 12.5), RAIL)
    m.box('rail', (4, 15, 2), (24, 2.5, 3), RAIL)
    m.box('back', (4, 8, 2.75), (24, 7, 1.5), A.lattice_face(), skip=['up', 'down'])
    m.box('stretcher', (4, 1.5, 12), (24, 1.5, 2), WOOD, skip=['down'])
    m.box('cushion', (4.5, 8, 5), (23, 2, 9), fabric(), tint=True, skip=['down'])
    m.plane('roses', (0, 2, 14.9), 'z', (5, 9), A.rose_vine(1.4, 1))
    return shift(m, dx=-8)

def garden_chair():
    m = Model('garden_chair', 'Garden Chair')
    m.box('post_left', (1, 0, 2), (3, 20, 3), POST, skip=['down'])
    m.box('post_right', (12, 0, 2), (3, 20, 3), POST, skip=['down'])
    m.box('leg_front_left', (1, 0, 12), (3, 6, 3), WOODV, skip=['down', 'up'])
    m.box('leg_front_right', (12, 0, 12), (3, 6, 3), WOODV, skip=['down', 'up'])
    m.box('seat', (0.5, 6, 1.5), (15, 2, 14), RAIL)
    m.box('rail', (4, 16.5, 2), (8, 2.5, 3), RAIL)
    m.box('back', (4, 10, 2.75), (8, 6.5, 1.5), A.lattice_face(), skip=['up', 'down'])
    m.box('stretcher', (4, 1.5, 12.5), (8, 1.5, 2), WOOD, skip=['down'])
    m.box('cushion', (2, 8, 4.5), (12, 2, 10), fabric(), tint=True, skip=['down'])
    m.plane('roses', (11.5, 0.5, 15.4), 'z', (5, 7), A.rose_vine(1.4, 2))
    return m

def tea_table():
    """reshaped: round stepped top on a turned pedestal (bulb and collar), crossed feet,
    teapot with a spout, a cup and a vase of roses"""
    m = Model('tea_table', 'Garden Tea Table')
    m.box('top_a', (0.5, 13, 2), (15, 1.5, 12), RAIL)
    m.box('top_b', (2, 13.25, 0.5), (12, 1, 15), RAIL)
    m.box('collar', (5.5, 11.5, 5.5), (5, 1.5, 5), RAIL)
    m.box('column', (6.75, 4, 6.75), (2.5, 7.5, 2.5), WOODV, skip=['up', 'down'])
    m.box('bulb', (5.75, 2, 5.75), (4.5, 3, 4.5), RAIL)
    m.box('foot_a', (2, 0, 6.5), (12, 2, 3), RAIL)
    m.box('foot_b', (6.75, 0, 2), (2.5, 1.75, 12), RAIL)
    m.box('teapot', (5, 14.5, 6), (4, 3.5, 4), {'up': solid('kwhite', 1.0), '*': _teapot_side}, skip=['down'])
    m.box('teapot_lid', (5.75, 18, 6.75), (2.5, 1, 2.5), solid('rose', 2.0), skip=['down'])
    m.box('spout', (9, 15.5, 7.5), (2, 1, 1), solid('kwhite', 1.0), rot=('z', 22.5, (9, 16, 8)))
    m.box('cup', (10.5, 14.5, 10), (2, 1.5, 2), {'up': _tea_top, '*': solid('kwhite', 1.0)}, skip=['down'])
    m.box('vase', (2.5, 14.5, 3), (2, 2.5, 2), {'up': A.soil_top(), '*': A.patina()}, skip=['down'])
    cross(m, 'flowers', 3.5, 17, 4, 7, 9, A.rose_bush())
    return m

def _teapot_side(c):
    c.fill('kwhite', 1.0)
    c.M[1:3] = MI['rose']; c.T[1:3] = 2.0
    c.T[-1] = 2.0

def _tea_top(c):
    c.fill('kwhite', 1.0); c.M[1:-1, 1:-1] = MI['clay']; c.T[1:-1, 1:-1] = 2.0

def _cake_side(c):
    c.fill('cream', 1.0); c.M[c.h // 2] = MI['pink']; c.T[c.h // 2] = 2.0

def potting_table():
    m = Model('potting_table', 'Potting Table')
    m.box('post_left', (1, 0, 2), (2.5, 28, 2.5), POST, skip=['down'])
    m.box('post_right', (12.5, 0, 2), (2.5, 28, 2.5), POST, skip=['down'])
    m.box('leg_front_left', (1, 0, 11.5), (2.5, 12, 2.5), WOODV, skip=['down', 'up'])
    m.box('leg_front_right', (12.5, 0, 11.5), (2.5, 12, 2.5), WOODV, skip=['down', 'up'])
    m.box('top', (0, 12, 1.5), (16, 2, 13.5), RAIL)
    m.box('shelf', (1.5, 3, 2.5), (13, 1.5, 11), RAIL)
    m.box('back', (3.5, 14, 2.25), (9, 6, 1), A.carved(WOOD, faces=('south',), min_size=6), skip=['down'])
    m.box('upper_shelf', (1, 20, 1), (14, 1.5, 4.5), RAIL)
    m.box('pot', (8.5, 14, 7), (3.5, 3, 3.5), pot(), skip=['down'])
    cross(m, 'sprout', 10.25, 17, 8.75, 6, 8, A.daisy())
    m.box('pot_top', (3, 21.5, 2), (3, 2.5, 3), pot(), skip=['down'])
    m.plane('lavender', (2, 24, 3.5), 'z', (5, 8), A.lavender())
    return m

def seed_cabinet():
    """reshaped: raised on four short legs under a base frame, frame-and-panel body with carved
    rose sides, a drawer front, a crown with an overhang, lavender on top"""
    m = Model('seed_cabinet', 'Seed Cabinet')
    for i, (x, z) in enumerate(((1, 3), (13, 3), (1, 13), (13, 13))):
        m.box(('leg_back_left', 'leg_back_right', 'leg_front_left', 'leg_front_right')[i], (x, 0, z), (2, 2.5, 2), WOODV, skip=['up'])
    m.box('base', (0.5, 2.5, 2.5), (15, 1.5, 13), RAIL)
    m.box('body', (1, 4, 3), (14, 15, 12), {'south': A.drawers(3, 3), '*': A.carved(WOOD, faces=('east', 'west'))})
    m.box('stile_left', (0.5, 4, 13.5), (2, 15, 2), WOODV)
    m.box('stile_right', (13.5, 4, 13.5), (2, 15, 2), WOODV)
    m.box('top', (0, 19, 2), (16, 1.5, 14), RAIL)
    m.box('crown', (1, 20.5, 3), (14, 1, 12), RAIL)
    m.box('pot', (6, 21.5, 7), (4, 3, 4), pot(), skip=['down'])
    cross(m, 'lavender', 8, 24.5, 9, 5, 7, A.lavender())
    return m

def tool_rack():
    """reshaped: a clear rake (long handle, wide head with tines), a spade with a T grip,
    and a copper watering can on the crate"""
    m = Model('tool_rack', 'Garden Tool Rack')
    m.box('post_left', (1, 0, 7), (2.5, 21, 2.5), POST, skip=['down'])
    m.box('post_right', (12.5, 0, 7), (2.5, 21, 2.5), POST, skip=['down'])
    m.box('top_bar', (0, 17, 6.5), (16, 2, 3.5), RAIL)
    m.box('peg_bar', (3.5, 12, 8), (9, 1.5, 1.5), WOOD)
    m.box('crate', (3.5, 0, 5.5), (9, 5, 7), A.carved(WOOD, faces=('south',), min_size=7), skip=['down'])
    m.box('rake_handle', (5, 4, 9.75), (1, 13, 1), A.handle())
    m.box('rake_head', (3, 15.5, 9.5), (5, 1.25, 1.5), A.iron(2))
    m.plane('rake_tines', (3, 13.5, 10.9), 'z', (5, 2), rows_art(["I.I.I", "I.I.I"], {"I": ("iron", 2)}))
    m.box('spade_handle', (10, 6, 9.75), (1, 10, 1), A.handle())
    m.box('spade_grip', (9, 16, 9.75), (3, 1, 1), WOOD)
    m.box('spade_blade', (9.25, 3, 9.5), (2.5, 3.5, 1.5), A.iron(1))
    m.box('can', (4.5, 5, 7), (4, 3.5, 3), A.patina())
    m.box('can_spout', (8.5, 6.5, 8), (3, 1, 1), A.copper(), rot=('z', 22.5, (8.5, 7, 8.5)))
    return m

def rose_trellis():
    m = Model('rose_trellis', 'Rose Trellis')
    m.box('planter', (0.5, 0, 5), (15, 5, 6), {'up': A.soil_top(), '*': A.carved(WOOD, faces=('south', 'north'), min_size=5)}, skip=['down'])
    m.box('post_left', (1, 5, 7), (2, 24, 2), WOODV, skip=['down', 'up'])
    m.box('post_right', (13, 5, 7), (2, 24, 2), WOODV, skip=['down', 'up'])
    m.box('cap', (0, 29, 6.5), (16, 1.5, 3), RAIL)
    m.plane('lattice', (3, 5, 8), 'z', (10, 24), A.lattice_card())
    m.plane('roses_front', (1, 5, 9.4), 'z', (14, 24), A.rose_vine(1.0, 0))
    m.plane('roses_back', (1, 5, 6.6), 'z', (14, 24), A.rose_vine(1.0, 3))
    m.box('rose_a', (4, 20, 9.3), (2.5, 2.5, 1.2), _rose_box)
    m.box('rose_b', (9.5, 12, 9.3), (2.5, 2.5, 1.2), _rose_box)
    return m

def _rose_box(c):
    c.fill('rose', 2.0)
    if c.face == 'south':
        c.T[0, :] = 1.0; c.T[:, 0] = 1.0; c.T[c.h // 2, c.w // 2] = 6.0

def arbor_arch():
    m = Model('arbor_arch', 'Rose Arbor')
    for i, (x, z) in enumerate(((1, 2), (28.5, 2), (1, 11.5), (28.5, 11.5))):
        m.box(('post_back_left', 'post_back_right', 'post_front_left', 'post_front_right')[i],
              (x, 0, z), (2.5, 30, 2.5), WOODV, skip=['down', 'up'])
    m.box('beam_back', (0, 30, 1.5), (32, 2.5, 3.5), RAIL)
    m.box('beam_front', (0, 30, 11), (32, 2.5, 3.5), RAIL)
    for k, x in enumerate((4, 15, 26)):
        m.box(f'rafter_{k}', (x, 32.5, 0), (2, 1.5, 16), RAIL)
    m.plane('lattice_left', (2.25, 2, 4.5), 'x', (7, 26), A.lattice_card())
    m.plane('lattice_right', (29.75, 2, 4.5), 'x', (7, 26), A.lattice_card())
    m.plane('roses_left', (3.9, 4, 3), 'x', (10, 26), A.rose_vine(1.1, 1))
    m.plane('roses_right', (28.1, 4, 3), 'x', (10, 26), A.rose_vine(1.1, 2))
    m.plane('garland', (0, 25, 14.9), 'z', (32, 8), A.rose_vine(1.3, 0, horizontal=True))
    return shift(m, dx=-8, dy=-16)

def birdbath():
    """reshaped: stepped stone base with moss, a column with a collar, a two-tier copper bowl
    with patina, and the bluebird on the rim"""
    m = Model('birdbath', 'Copper Birdbath')
    m.box('base', (2, 0, 2), (12, 2, 12), A.mossy(STONE), skip=['down'])
    m.box('base_top', (3.5, 2, 3.5), (9, 1.5, 9), STONE, skip=['down'])
    m.box('column', (6, 3.5, 6), (4, 7.5, 4), STONE, skip=['down', 'up'])
    m.box('collar', (5, 11, 5), (6, 1.5, 6), STONE)
    m.box('bowl', (3.5, 12.5, 3.5), (9, 1.5, 9), A.patina(2))
    m.box('basin', (1.5, 14, 1.5), (13, 2, 13), {'up': A.basin_top(), '*': A.patina(2)})
    m.box('bird_body', (12, 16, 5), (2.5, 2.5, 4), A.bird_body(), skip=['down'])
    m.box('bird_head', (12.25, 18, 8.5), (2, 2, 2), solid('bird', 2.0), skip=['down'])
    m.box('bird_beak', (12.75, 18.5, 10.5), (1, 0.75, 1), solid('yellow', 1.0))
    m.plane('bird_tail', (13.25, 17, 2.75), 'x', (2.5, 2), rows_art(["bbb", "b.b"], {"b": ("bird", 3)}))
    cross(m, 'grass', 4, 2, 13, 5, 4, grass())
    return m

def flower_box():
    m = Model('flower_box', 'Flower Box')
    m.box('box', (0, 1, 4), (16, 7, 8), {'up': A.soil_top(), '*': A.carved(WOOD, faces=('east', 'west'), min_size=7)})
    m.box('foot_left', (1, 0, 4.5), (2, 1, 7), WOOD, skip=['up'])
    m.box('foot_right', (13, 0, 4.5), (2, 1, 7), WOOD, skip=['up'])
    cross(m, 'roses', 3.5, 8, 8, 7, 9, A.rose_bush())
    cross(m, 'lavender', 8.5, 8, 7, 5, 10, A.lavender())
    cross(m, 'daisies', 12.5, 8, 9, 6, 8, A.daisy())
    m.plane('front_roses', (1, 1.5, 12.4), 'z', (14, 6), A.rose_vine(1.6, 2))
    return m

def wheelbarrow():
    """reshaped: a tub with a sloped front board, handles running back to the legs, a big
    crossed wheel under the nose, sunflowers and roses"""
    m = Model('wheelbarrow', 'Wheelbarrow of Blooms')
    m.box('tub', (3, 5, 1), (10, 5, 9), {'up': A.soil_top(), '*': A.carved(WOOD, faces=('east', 'west'), min_size=5)})
    m.box('nose', (3, 6, 9.5), (10, 4, 2.5), WOOD, rot=('x', 22.5, (8, 6, 9.5)))
    m.box('leg_left', (3.5, 0, 1.5), (1.5, 5, 1.5), WOODV, skip=['up'])
    m.box('leg_right', (11, 0, 1.5), (1.5, 5, 1.5), WOODV, skip=['up'])
    m.box('handle_left', (3.5, 6.5, -3), (1.5, 1.5, 4), WOOD)
    m.box('handle_right', (11, 6.5, -3), (1.5, 1.5, 4), WOOD)
    m.box('wheel_a', (7, 0, 9.5), (2, 7, 5), A.wheel())
    m.box('wheel_b', (7.25, 1, 8.5), (1.5, 5, 7), A.wheel())
    m.box('axle', (5.5, 2.75, 11.25), (5, 1.5, 1.5), A.iron(2))
    cross(m, 'sunflowers', 5.5, 10, 4, 7, 13, A.sunflower())
    cross(m, 'roses', 9.5, 10, 7, 7, 9, A.rose_bush())
    return m

def sundial():
    """reshaped: mossy stepped base, a column with a middle band, a wide cap, a copper dial
    with patina and a gnomon, ivy up the column"""
    m = Model('sundial', 'Sundial')
    m.box('base', (1, 0, 1), (14, 2, 14), A.mossy(STONE_BIG), skip=['down'])
    m.box('plinth', (3, 2, 3), (10, 1.5, 10), STONE, skip=['down'])
    m.box('column', (5.5, 3.5, 5.5), (5, 9, 5), STONE, skip=['down', 'up'])
    m.box('band', (4.75, 7, 4.75), (6.5, 1.5, 6.5), STONE)
    m.box('cap', (3.5, 12.5, 3.5), (9, 1.5, 9), STONE)
    m.box('dial', (4, 14, 4), (8, 0.75, 8), {'up': A.dial_top(), '*': A.patina()}, skip=['down'])
    m.plane('gnomon', (8, 14.75, 5), 'x', (5, 4), rows_art(GNOMON, {"c": ("copper", 1)}))
    m.plane('ivy', (4.5, 3.5, 11.4), 'z', (5, 8), ivy())
    cross(m, 'grass', 3, 2, 13, 4, 3, grass())
    return m

def picnic_blanket():
    m = Model('picnic_blanket', 'Picnic Blanket')
    m.box('blanket', (-4, 0, -4), (24, 0.5, 24), A.gingham(), tint=True, skip=['down'])
    m.box('basket', (2, 0.5, 3), (6, 4, 4.5), A.wicker(), skip=['down'])
    m.box('lid', (1.75, 4.5, 2.75), (6.5, 1, 5), A.cream_cloth())
    m.plane('basket_handle', (1.5, 5.5, 5.25), 'z', (7, 3), rows_art(HANDLE, {"h": ("birchside", 2)}))
    m.box('cup_a', (11, 0.5, 9), (1.5, 1.5, 1.5), {'up': _tea_top, '*': solid('kwhite', 1.0)}, skip=['down'])
    m.box('cup_b', (13.5, 0.5, 10.5), (1.5, 1.5, 1.5), {'up': _tea_top, '*': solid('kwhite', 1.0)}, skip=['down'])
    m.box('plate', (9, 0.5, 3), (4, 0.25, 4), solid('kwhite', 1.0), skip=['down'])
    m.box('sandwich', (9.75, 0.75, 3.75), (2.5, 1, 2.5), {'up': solid('cream', 0.0), '*': _sandwich_side}, skip=['down'])
    cross(m, 'daisies', 15, 0.5, 3, 6, 8, A.daisy())
    return m

def _sandwich_side(c):
    c.fill('cream', 1.0); c.M[c.h // 2] = MI['moss']; c.T[c.h // 2] = 2.0

def stake_lantern(lit=False):
    m = Model('stake_lantern_lit' if lit else 'stake_lantern', 'Stake Lantern')
    m.box('stake', (7, 0, 7), (2, 16, 2), WOODV, skip=['down'])
    m.box('base', (5.5, 16, 5.5), (5, 1.5, 5), A.patina())
    m.box('candle', (7.25, 17.5, 7.25), (1.5, 2.5, 1.5), solid('cream', 1.0))
    if lit:
        m.box('flame', (7.5, 20, 7.5), (1, 1.5, 1), A.flame(), emit=15)
    m.box('glass', (6, 17.5, 6), (4, 6, 4), _lantern_glass(lit), emit=10 if lit else 0)
    m.box('roof', (5, 23.5, 5), (6, 1.5, 6), A.patina())
    m.box('roof_top', (6, 25, 6), (4, 1.5, 4), A.copper())
    m.box('finial', (7.5, 26.5, 7.5), (1, 1.5, 1), A.copper(1))
    m.plane('roses', (5.5, 2, 9.4), 'z', (5, 10), A.rose_vine(1.3, 5))
    return m

def _lantern_glass(lit):
    g = A.glass(lit)
    def p(c):
        g(c)
        if c.face not in ('up', 'down'):
            for x in (0, c.w - 1):
                c.M[:, x] = MI['copper']; c.T[:, x] = 2.0; c.A[:, x] = 255
    return p

ALL = [garden_bench, garden_chair, tea_table, potting_table, seed_cabinet, tool_rack, rose_trellis,
       arbor_arch, birdbath, flower_box, wheelbarrow, sundial, picnic_blanket, stake_lantern,
       lambda: stake_lantern(True)]
