"""Rosewick Garden v2 card art and face painters. Hand-placed pixel art at 16 px per block,
5-tone ramps, light from the top left, no lone noise pixels (see claude/brand/WOOD_STYLE.md)."""
import numpy as np
from engine import MI, pxmat
from arts import rows_art, _put, STEP, grass, ivy
import arts

FRAME = arts.FRAME

# ------------------------------------------------------------------ flowers (cross cards)
ROSE_BUSH = [
    "..L....",
    ".LRD.L.",
    ".RRD.RD",
    "..g.RRD",
    ".gGg.g.",
    "g.G.gG.",
    "..G..G.",
    "..G.G..",
    "...G...",
]
LAVENDER = [
    "..l..",
    ".lL.l",
    ".Ll.L",
    "l.Ll.",
    "L.l.l",
    "g.L.g",
    ".gGg.",
    "..G..",
    ".gG..",
    "..G..",
]
DAISY = [
    ".w....",
    "wYw.w.",
    ".w.wYw",
    ".g..w.",
    ".G.g..",
    "gG.G..",
    ".GG...",
    "..G...",
]
SUNFLOWER = [
    "..yyy..",
    ".yOOOy.",
    "yOdddOy",
    "yOdddOy",
    ".yOOOy.",
    "..yyy..",
    "...G...",
    ".gGG...",
    "g..G...",
    "...Gg..",
    "...G.gg",
    "...G...",
    "..gG...",
]
FL_PAL = {"L": ("rose", 1), "R": ("rose", 2), "D": ("rose", 3),
          "l": ("lavender", 1), "w": ("kwhite", 1), "Y": ("yellow", 1),
          "y": ("yellow", 1), "O": ("yellow", 2), "d": ("soil", 2),
          "g": ("moss", 1), "G": ("moss", 3)}
FL_PAL_L = dict(FL_PAL, L=("lavender", 3))

def rose_bush(): return rows_art(ROSE_BUSH, FL_PAL)
def lavender(): return rows_art(LAVENDER, FL_PAL_L)
def daisy(): return rows_art(DAISY, FL_PAL)
def sunflower(): return rows_art(SUNFLOWER, FL_PAL)

# ------------------------------------------------------------------ climbing roses
def rose_vine(density=1.0, seed=0, horizontal=False):
    """climbing rose card: wandering dark stems, 2x2 leaves lit top-left, 3x3 roses
    (dark heart, mid ring, lit top-left petals). Placed on a staggered grid, not at random."""
    def p(c):
        if horizontal:
            # paint on a transposed card, then swap back, so the stems run sideways
            from engine import MI as _MI
            h, w = c.h, c.w
            M0, T0, A0 = c.M, c.T, c.A
            c.h, c.w = w, h
            c.M = np.full((w, h), -1, int); c.T = np.full((w, h), 2.0); c.A = np.full((w, h), 255, int)
            _draw(c)
            M1, T1, A1 = c.M.T.copy(), c.T.T.copy(), c.A.T.copy()
            c.h, c.w = h, w
            c.M, c.T, c.A = M0, T0, A0
            sel = M1 >= 0
            c.M[sel] = M1[sel]; c.T[sel] = T1[sel]
            return
        _draw(c)
    def _draw(c):
        W, H = c.w, c.h
        # stems: two wandering vertical vines
        for k, x0 in enumerate((W // 4, (3 * W) // 4)):
            for y in range(H):
                x = x0 + (1 if ((y + 3 * k + seed) // 5) % 2 else 0)
                _put(c, x, y, 'moss', 4)
                if (y + k * 2 + seed) % 4 == 1:
                    s = -1 if ((y + k + seed) // 4) % 2 else 1
                    for dx, dy, ti in ((s, 0, 2), (2 * s, 0, 1 if s < 0 else 2), (s, -1, 1), (2 * s, -1, 1)):
                        _put(c, x + dx, y + dy, 'moss', ti)
        # roses on a staggered grid
        step = max(5, int(7 / max(density, 0.3)))
        for j, y in enumerate(range(2 + seed % 3, H - 2, step)):
            for i, x in enumerate(range(2 + (j % 2) * (step // 2), W - 2, step)):
                for dx, dy, ti in ((0, 0, 1), (1, 0, 2), (2, 0, 2), (0, 1, 2), (1, 1, 4), (2, 1, 3),
                                   (0, 2, 2), (1, 2, 3), (2, 2, 3)):
                    _put(c, x + dx - 1, y + dy - 1, 'rose', ti)
    return p

# ------------------------------------------------------------------ face painters
def lattice_face(wood='birch'):
    """birch lattice painted on a box face: diagonal slats over a dark recess, framed"""
    base = pxmat(wood, 'woodv')
    def p(c):
        base(c)
        if c.face in ('up', 'down') or c.w < 6 or c.h < 4:
            return
        yy, xx = np.mgrid[0:c.h, 0:c.w]
        inner = (yy >= 1) & (yy <= c.h - 2) & (xx >= 1) & (xx <= c.w - 2)
        a = (xx + yy) % 5 == 0
        b = (xx - yy) % 5 == 0
        c.T[inner] = STEP[4]
        c.T[inner & b] = STEP[2]
        c.T[inner & a] = STEP[1]
    return p

def lattice_card(wood='birch'):
    """see-through lattice panel card: framed, diagonal slats, the rest clear"""
    side = 'birchside' if wood == 'birch' else 'woodside'
    def p(c):
        yy, xx = np.mgrid[0:c.h, 0:c.w]
        frame = (yy == 0) | (yy == c.h - 1) | (xx == 0) | (xx == c.w - 1)
        a = (xx + yy) % 5 == 0
        b = (xx - yy) % 5 == 0
        m = frame | a | b
        c.M[m] = MI[side]
        c.T[m] = STEP[2]
        c.T[a & ~frame] = STEP[1]
        c.T[b & ~frame & ~a] = STEP[3]
        c.T[frame] = STEP[2]
        c.T[(yy == 0) & m] = STEP[1]
    return p

def gingham():
    """dyeable gingham (tinted grey): 2 px checks, stripe crossings darkest, a lit fringe row"""
    def p(c):
        yy, xx = np.mgrid[0:c.h, 0:c.w]
        X, Y, _ = [np.asarray(q).astype(int) for q in c.P] if False else (xx, yy, None)
        sx = (xx // 2) % 2 == 0
        sy = (yy // 2) % 2 == 0
        c.M[:] = MI['grey']
        c.T[:] = STEP[0]
        c.T[sx ^ sy] = STEP[2]
        c.T[sx & sy] = STEP[3]
        if c.face not in ('up', 'down'):
            c.T[:] = STEP[3]
    return p

def drawers(rows=3, cols=3):
    """seed-cabinet front: soft birch with a grid of carved drawers (dark top/left recess
    edge, lit bottom/right edge) and a brass knob in each"""
    base = pxmat('birch', 'wood')
    def p(c):
        base(c)
        if c.face != 'south':
            return
        W, H = c.w, c.h
        cw, ch = (W - 1) / cols, (H - 1) / rows
        for r in range(rows):
            for k in range(cols):
                x0, y0 = int(round(1 + k * cw)), int(round(1 + r * ch))
                x1, y1 = int(round(1 + (k + 1) * cw)) - 2, int(round(1 + (r + 1) * ch)) - 2
                for x in range(x0, x1 + 1):
                    _put(c, x, y0, 'birchside', 4); _put(c, x, y1, 'birchside', 1)
                for y in range(y0, y1 + 1):
                    _put(c, x0, y, 'birchside', 4); _put(c, x1, y, 'birchside', 1)
                for x in range(x0 + 1, x1):
                    for y in range(y0 + 1, y1):
                        _put(c, x, y, 'birchside', 2)
                _put(c, (x0 + x1) // 2, (y0 + y1) // 2, 'brass', 1)
    return p

def soil_top(flowers=None):
    def p(c):
        c.fill('soil', STEP[2])
        if c.face == 'up':
            yy, xx = np.mgrid[0:c.h, 0:c.w]
            c.T[((xx + 2 * yy) % 5 == 0)] = STEP[3]
            c.T[((xx + 2 * yy) % 5 == 1)] = STEP[1]
    return p

def copper(base=2):
    def p(c):
        c.fill('copper', STEP[base])
        if c.face == 'up':
            c.T[0, :] = STEP[base - 1]; c.T[:, 0] = STEP[base - 1]
        elif c.face != 'down':
            c.T[0, :] = STEP[base - 1]
            if c.h >= 3:
                c.T[-1, :] = STEP[min(4, base + 1)]
    return p

def basin_top():
    """copper rim around a water dish with two ripple dashes"""
    def p(c):
        c.fill('copper', STEP[2])
        if c.face != 'up':
            copper()(c); return
        c.T[0, :] = STEP[1]; c.T[:, 0] = STEP[1]
        c.M[2:-2, 2:-2] = MI['water']; c.T[2:-2, 2:-2] = STEP[2]
        c.T[2, 2:-2] = STEP[4]; c.T[2:-2, 2] = STEP[4]
        for y, x0 in ((c.h // 2, 4), (c.h - 4, c.w // 2)):
            if 2 < y < c.h - 2:
                c.T[y, x0:x0 + 2] = STEP[0]
    return p

def dial_top():
    """copper sundial plate: lit rim, hour ticks round the edge in 2 px runs"""
    def p(c):
        copper()(c)
        if c.face != 'up':
            return
        W, H = c.w, c.h
        for x in range(2, W - 2, 3):
            c.T[1, x:x + 2] = STEP[3]; c.T[H - 2, x:x + 2] = STEP[3]
        for y in range(2, H - 2, 3):
            c.T[y:y + 2, 1] = STEP[3]; c.T[y:y + 2, W - 2] = STEP[3]
    return p

def glass(lit=False):
    def p(c):
        c.fill('glass', STEP[1])
        c.A[:] = 70
        if lit:
            c.M[:] = MI['yellow']; c.T[:] = STEP[0]; c.A[:] = 140
        if c.face not in ('up', 'down') and c.w >= 3:
            c.T[1:-1, 1] = STEP[0]; c.A[1:-1, 1] = 200
    return p

def flame():
    """4-frame candle flame, swaying a pixel left and right"""
    def p(c):
        f = 0 if FRAME[0] is None else FRAME[0][0]
        c.fill('yellow', STEP[0])
        shift = (0, 1, 0, -1)[f % 4]
        c.M[:] = -1
        for y in range(c.h):
            for x in range(c.w):
                cx = (c.w - 1) / 2 + (shift * y / max(c.h - 1, 1) if c.h > 1 else 0)
                if abs(x - cx) <= 0.6 + 0.4 * (y / max(c.h - 1, 1)):
                    c.set(x, y, mat='korange' if y == c.h - 1 else 'yellow', tone=STEP[0 if y < c.h - 1 else 1])
    return p

def bird_body():
    """bluebird: blue back and wings, orange chest on the front face"""
    def p(c):
        c.fill('bird', STEP[2])
        if c.face == 'up':
            c.T[:, :] = STEP[1]
        elif c.face in ('south', 'east', 'west'):
            c.T[0, :] = STEP[1]
        if c.face == 'south':
            c.M[c.h // 2:, :] = MI['korange']; c.T[c.h // 2:, :] = STEP[1]
        if c.face in ('east', 'west') and c.h >= 2:
            c.T[1:, :] = STEP[3]
    return p

RAKE = [
    "IIIIIII",
    "I.I.I.I",
    "I.I.I.I",
]
SHEARS = [
    ".i...i.",
    "..i.i..",
    "...b...",
    "..h.h..",
    ".h...h.",
    ".h...h.",
]
def rake_head(): return rows_art(RAKE, {"I": ("iron", 2)})
def shears(): return rows_art(SHEARS, {"i": ("iron", 1), "b": ("brass", 1), "h": ("rose", 3)})

def iron(base=2):
    def p(c):
        c.fill('iron', STEP[base])
        if c.face != 'down':
            c.T[0, :] = STEP[base - 1]
    return p

def handle():
    return pxmat('birch', 'woodv')

def fabric_plain(mat='grey'):
    def p(c):
        c.fill(mat, STEP[1])
        if c.face not in ('up', 'down'):
            c.T[-1, :] = STEP[3]
            c.T[0, :] = STEP[0]
    return p

def cream_cloth():
    """basket lid cloth: cream with a rose stripe"""
    def p(c):
        c.fill('cream', STEP[1])
        if c.face == 'up':
            c.M[:, c.w // 2 - 1:c.w // 2 + 1] = MI['rose']; c.T[:, c.w // 2 - 1:c.w // 2 + 1] = STEP[2]
    return p

def wicker():
    """woven basket: alternating 2x2 over-under blocks in birch"""
    def p(c):
        yy, xx = np.mgrid[0:c.h, 0:c.w]
        c.M[:] = MI['birchside']
        w = ((xx // 2) + (yy // 2)) % 2 == 0
        c.T[:] = STEP[2]
        c.T[w] = STEP[1]
        c.T[(yy % 2 == 1) & ~w] = STEP[3]
    return p

def wheel():
    """wheel side: birch rim ring, iron hub, spokes in 2 px runs"""
    def p(c):
        pxmat('birch', 'wood')(c)
        if c.face in ('east', 'west'):
            yy, xx = np.mgrid[0:c.h, 0:c.w]
            cx, cy = (c.w - 1) / 2, (c.h - 1) / 2
            r = np.maximum(abs(xx - cx), abs(yy - cy))
            c.T[r >= r.max() - 0.6] = STEP[3]
            hub = r < 1
            c.M[hub] = MI['iron']; c.T[hub] = STEP[2]
    return p


# ================================================== extra texturing (Oct 19 2026, "add more texturing")
ROSE_CARVE = [
    ".DDDD.",
    "D.LL.D",
    "DL.DLD",
    "DLD.LD",
    "D.LL.D",
    ".DDDD.",
    "..D...",
    ".DLD..",
]

def carved(base, faces=('south', 'north', 'east', 'west'), min_size=9):
    """wrap a face painter: a carved rose medallion (dark recess, lit edge) centred on big faces"""
    def p(c):
        base(c)
        if c.face not in faces or c.w < min_size or c.h < min_size:
            return
        h, w = len(ROSE_CARVE), len(ROSE_CARVE[0])
        art = ROSE_CARVE if c.h >= h + 1 else ROSE_CARVE[:6]
        h = len(art)
        if c.h < h or c.w < w:
            return
        x0, y0 = (c.w - w) // 2, (c.h - h) // 2
        for y, row in enumerate(art):
            for x, ch in enumerate(row):
                if ch == 'D':
                    c.T[y0 + y, x0 + x] = STEP[4]
                elif ch == 'L':
                    c.T[y0 + y, x0 + x] = STEP[1]
    return p

def patina(base=2):
    """copper with verdigris running down from the top edge in 2 px wide drips of set lengths"""
    LENS = (3, 1, 4, 2, 0)
    def p(c):
        copper(base)(c)
        if c.face in ('down',):
            return
        if c.face == 'up':
            yy, xx = np.mgrid[0:c.h, 0:c.w]
            m = ((xx // 2 + yy // 2) % 4 == 0) & ((xx + yy) % 2 == 0)
            m |= ((xx // 2 + yy // 2) % 4 == 0) & ((xx + yy) % 2 == 1)
            m &= ((xx == 0) | (yy == 0) | (xx == c.w - 1) | (yy == c.h - 1))
            c.M[m] = MI['verdi']; c.T[m] = STEP[2]
            return
        for x in range(c.w):
            n = min(c.h, LENS[(x // 2) % len(LENS)])
            if n:
                c.M[:n, x] = MI['verdi']; c.T[:n, x] = STEP[1]; c.T[n - 1, x] = STEP[2]
    return p

def mossy(base):
    """stone with moss creeping over the top edge in 2 px runs (sides) and corner clusters (top)"""
    DEP = (2, 1, 0, 1, 2, 0)
    def p(c):
        base(c)
        if c.face == 'down':
            return
        if c.face == 'up':
            yy, xx = np.mgrid[0:c.h, 0:c.w]
            edge = (xx <= 1) | (yy <= 1) | (xx >= c.w - 2) | (yy >= c.h - 2)
            m = edge & (((xx // 2) + (yy // 2)) % 3 == 0)
            c.M[m] = MI['moss']; c.T[m] = STEP[2]
            return
        for x in range(c.w):
            n = min(c.h, DEP[(x // 2) % len(DEP)])
            if n:
                c.M[:n, x] = MI['moss']; c.T[:n, x] = STEP[1 if n == 1 else 2]; c.T[0, x] = STEP[1]
    return p

def soil_top(flowers=None):
    """dark soil with even furrows and little 2 px pebbles"""
    def p(c):
        c.fill('soil', STEP[2])
        if c.face == 'up':
            yy, xx = np.mgrid[0:c.h, 0:c.w]
            c.T[((xx + 2 * yy) % 5 == 0)] = STEP[3]
            c.T[((xx + 2 * yy) % 5 == 1)] = STEP[1]
            peb = ((xx % 7 == 2) | (xx % 7 == 3)) & (yy % 5 == 1) & (((xx // 7) + yy // 5) % 2 == 0)
            c.M[peb] = MI['stone']; c.T[peb] = STEP[1]
    return p
