"""Card art and flat-painting helpers for the Koi Garden set (all structured, no speckle)."""
import math
import numpy as np
from engine import MI, PATTERNS

def _line(c, x0, y0, x1, y1, mat, tone):
    n = int(math.ceil(max(abs(x1 - x0), abs(y1 - y0)))) + 1
    for i in range(n):
        t = i / max(n - 1, 1)
        c.set(int(round(x0 + (x1 - x0) * t)), int(round(y0 + (y1 - y0) * t)), mat=mat, tone=tone)

def grass(mat='moss', every=2, minh=0.35):
    def p(c):
        rng = c.rng
        for xb in range(0, c.w, every):
            hgt = (minh + (1 - minh) * rng.random()) * (c.h - 1)
            lean = rng.choice([-1.5, -0.8, 0, 0.8, 1.5]) * c.res
            n = int(hgt) + 1
            for i in range(n):
                f = i / max(n - 1, 1)
                x = int(round(xb + lean * f * f))
                c.set(x, c.h - 1 - i, mat=mat, tone=2.6 - 1.4 * f)
    return p

def reeds(heads=True, flower=None):
    def p(c):
        rng = c.rng
        xs = list(range(1, c.w - 1, 2))
        for k, xb in enumerate(xs):
            hgt = (0.55 + 0.45 * rng.random()) * (c.h - 1)
            lean = rng.choice([-2, -1, 1, 2]) * c.res
            n = int(hgt) + 1
            for i in range(n):
                f = i / max(n - 1, 1)
                c.set(int(round(xb + lean * f)), c.h - 1 - i, mat='reed', tone=2.6 - 1.3 * f)
            top_x = int(round(xb + lean)); top_y = c.h - n
            if heads and k % 2 == 0:
                for j in range(2 * c.res, 6 * c.res):
                    for dx in range(-(c.res // 2), c.res // 2 + 1) if c.res > 1 else (0,):
                        c.set(top_x + dx, top_y + j, mat='cattail', tone=1.6 + 0.25 * (j % 2))
            elif flower and k % 3 == 1:
                fy = top_y + 1
                for dx, dy, t in ((0, 0, 1.4), (-1, 1, 2), (1, 1, 2), (0, 1, 1.2), (0, 2, 2.4)):
                    c.set(top_x + dx, fy + dy, mat=flower, tone=t)
    return p

def lilypad(notch_dir=0.0, rim=True):
    def p(c):
        u = c.u - 0.5; v = c.v - 0.5
        r = np.sqrt(u * u + v * v); a = np.arctan2(v, u)
        da = np.abs((a - notch_dir + np.pi) % (2 * np.pi) - np.pi)
        m = (r < 0.48) & ~((da < 0.32) & (r > 0.03))
        c.M[m] = MI['lily']; c.T[m] = 2.0
        # veins every 45 deg, half-step darker
        # no veins or pixel rim: at 16 px per block both alias into scattered dots on the round edge.
        # One clean light disc in the middle, darker outer band.
        if rim:
            c.T[m & (r < 0.30)] = 1.4
    return p

def petal_fan(mat='pink'):
    """standing lotus petals (z-plane), bottom-centre root."""
    def p(c):
        u = c.u - 0.5; v = 1 - c.v
        for ang, length, wid, tone in ((0, 0.95, 0.17, 1.6), (0.5, 0.8, 0.16, 2.0), (-0.5, 0.8, 0.16, 2.0),
                                       (1.0, 0.55, 0.14, 2.4), (-1.0, 0.55, 0.14, 2.4)):
            ca, sa = math.cos(ang), math.sin(ang)
            pu = u * ca - v * sa * -1 if False else (u * ca + v * sa)
            pv = -u * sa + v * ca
            m = (pv > 0) & (pv < length) & (np.abs(pu) < wid * np.sin(np.clip(pv / length, 0, 1) * np.pi) ** 0.6)
            c.M[m] = MI[mat]
            c.T[m] = tone + 0.8 * (pv[m] / length > 0.75)
            c.T[m & (pv < length * 0.3)] = 0.6  # pale heart
    return p

def petal_ring(mat='pink', n=8):
    def p(c):
        u = c.u - 0.5; v = c.v - 0.5
        r = np.sqrt(u * u + v * v); a = np.arctan2(v, u)
        k = (a % (2 * np.pi / n)) / (2 * np.pi / n) - 0.5
        width = 0.5 * np.sin(np.clip((r - 0.08) / 0.4, 0, 1) * np.pi) ** 0.7
        m = (r > 0.08) & (r < 0.48) & (np.abs(k) < width * 0.9)
        c.M[m] = MI[mat]; c.T[m] = 1.9
        c.T[m & (r > 0.38)] = 2.7
        c.T[m & (r < 0.17)] = 0.6
    return p

def splash():
    """carved-water splash crest card (z-plane), foam tips."""
    def p(c):
        u = c.u; v = 1 - c.v
        # three crest bumps
        ph = 0.0 if FRAME[0] is None else 2 * np.pi * FRAME[0][0] / FRAME[0][1]
        crest = 0.35 + 0.45 * np.abs(np.sin(u * np.pi * 1.5 + 0.3 + (0 if FRAME[0] is None else 0.25 * np.sin(ph)))) ** 0.8
        m = v < crest
        c.M[m] = MI['water']; c.T[m] = 2.2 - 1.2 * v[m]
        foam = m & (v > crest - 0.16)
        c.M[foam] = MI['kwhite']; c.T[foam] = 1.6
        # curl lines inside, one half-step lighter
        curl = m & ~foam & (np.abs(np.sin(u * 9 + v * 6 - ph)) < 0.18)
        c.T[curl] -= 0.6
    return p

def rope_v():
    def p(c):
        w, h = c.w, c.h
        pts = [(0, h - 1), (w // 2, 0), (w - 1, h - 1)]
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            n = int(math.ceil(max(abs(x1 - x0), abs(y1 - y0)))) + 1
            for i in range(n):
                t = i / max(n - 1, 1)
                x = int(round(x0 + (x1 - x0) * t)); y = int(round(y0 + (y1 - y0) * t))
                c.set(x, y, mat='rope', tone=1.6 + 0.8 * (i % 2))
    return p

def ivy():
    def p(c):
        rng = c.rng
        x = c.w / 2
        for y in range(c.h - 1, -1, -1):
            x = c.w / 2 + (c.w / 3) * math.sin(y * 0.55)
            c.set(int(round(x)), y, mat='moss', tone=3.0)
            if y % 3 == 0:
                side = 1 if (y // 3) % 2 else -1
                for dx, dy, t in ((side, 0, 1.6), (side * 2, 0, 2.2), (side, -1, 1.2)):
                    c.set(int(round(x)) + dx, y + dy, mat='moss', tone=t)
    return p

def streamer():
    def p(c):
        cols = ['korange', 'kwhite', 'water', 'yellow', 'pink']
        for x in range(c.w):
            mat = cols[(x // max(1, c.w // 5)) % 5]
            ln = c.h - 1 - (2 if x % 2 else 0) - (x % 3)
            for y in range(ln):
                c.set(x, y, mat=mat, tone=1.7 + 0.5 * ((y // 3) % 2))
    return p

def ribbon():
    """streamer cloth flying sideways: coloured bands run along its length, ragged tail end"""
    def p(c):
        cols = ['korange', 'kwhite', 'water', 'yellow', 'pink']
        for y in range(c.h):
            mat = cols[(y * 5) // max(1, c.h)]
            for x in range(c.w - (2 if y % 2 else 0) - (y % 3)):
                c.set(x, y, mat=mat, tone=1.7 + 0.5 * ((x // 3) % 2))
    return p

def sprout():
    def p(c):
        cx = c.w // 2
        for y in range(c.h - 1, 1, -1):
            c.set(cx, y, mat='moss', tone=2.6)
        for (dx, dy) in ((-1, 3), (-2, 2), (1, 5), (2, 4), (-1, 7), (1, 1), (0, 0), (-3, 3), (3, 5)):
            if 0 <= dy < c.h:
                c.set(cx + dx, dy, mat='moss', tone=1.4 if dx < 0 else 2.0)
    return p

# ------------------------------------------------- 2D koi (top view) painting
def koi_field(c, path, W, pattern, outline_mat=None):
    """Paint a top-view koi following `path` (list of (x,y) pixel points from nose to tail tip).
    W = half body width in px. Returns mask painted."""
    P = np.array(path, float)
    seg = np.r_[0, np.cumsum(np.hypot(*np.diff(P, axis=0).T))]
    S = seg / seg[-1]
    yy, xx = np.mgrid[0:c.h, 0:c.w] + 0.5
    d2 = (xx[..., None] - P[:, 0]) ** 2 + (yy[..., None] - P[:, 1]) ** 2
    k = d2.argmin(-1)
    s = S[k]
    # signed lateral distance
    k2 = np.clip(k, 0, len(P) - 2)
    tx = P[k2 + 1, 0] - P[k2, 0]; ty = P[k2 + 1, 1] - P[k2, 1]
    tl = np.hypot(tx, ty) + 1e-9
    dx = xx - P[k, 0]; dy = yy - P[k, 1]
    lat = (dx * ty - dy * tx) / tl
    dist = np.abs(lat)
    end_ok = (k > 0) | ((dx * tx + dy * ty) >= -0.3)
    end_ok &= (k < len(P) - 1) | ((dx * tx + dy * ty) <= 0.3)
    hw = np.where(s < 0.22, W * np.sqrt(np.clip(s / 0.22, 0.05, 1)),
         np.where(s < 0.5, W, np.where(s < 0.78, W * (1 - (s - 0.5) / 0.28 * 0.72), 0)))
    body = (dist <= hw) & (s < 0.78) & end_ok
    ts = np.clip((s - 0.76) / 0.24, 0, 1)
    tail = (s >= 0.74) & (dist <= W * (0.28 + 0.9 * ts)) & end_ok & ~((ts > 0.7) & (dist < W * (ts - 0.7) * 2.2))
    fins = (np.abs(s - 0.3) < 0.07) & (dist > W * 0.9) & (dist < W * 1.75) & end_ok
    pat = PATTERNS[pattern]
    base = pat['base']
    M = c.M; T = c.T
    fm = {'kohaku': 'kwhite', 'sanke': 'kwhite', 'showa': 'kblack', 'chagoi': 'korange', 'magoi': 'kblack'}[pattern]
    for m, mat, tone in ((fins, fm, 1.4), (tail, fm, 1.5), (body, base, 1.8)):
        M[m] = MI[mat]; T[m] = tone
    for t0, t1, mat in pat['patch']:
        pm = body & (s > t0) & (s < t1) & (dist < W * (0.75 + 0.25 * np.sin(s * 30)))
        M[pm] = MI[mat]
    for ts_, ws in pat['spots']:
        pm = body & (np.abs(s - ts_) < 0.035) & (np.abs(lat - ws * W) < W * 0.35)
        M[pm] = MI['kblack']
    if pattern in ('showa',):
        pm = body & (np.abs(s - 0.68) < 0.06)
        M[pm] = MI['kwhite']
    T[body & (dist < W * 0.25)] -= 0.4   # spine light
    T[(body | tail) & (dist > hw - 0.9) & ~fins] += 0.6  # edge half-step darker
    T[tail & (dist > W * 0.4) & (s > 0.85)] += 0.3
    return body | tail | fins

def arc(cx, cy, r, a0, a1, n=40):
    return [(cx + r * math.cos(a0 + (a1 - a0) * i / (n - 1)), cy + r * math.sin(a0 + (a1 - a0) * i / (n - 1))) for i in range(n)]

FRAME = [None]   # (frame, frames) while baking an animated variant; None = still
GLINT = 12

def ripples(c, centres, mat='water', tone=1.0):
    yy, xx = np.mgrid[0:c.h, 0:c.w] + 0.5
    water = c.M == MI[mat]
    if FRAME[0] is None:
        for cx, cy, r in centres:
            d = np.hypot(xx - cx, (yy - cy) * 1.15)
            m = (np.abs(d - r) < 0.55) & water
            c.T[m] = tone
        return
    f, n = FRAME[0]
    base = float(np.median(c.T[water])) if water.any() else 2.0
    for i, (cx, cy, r) in enumerate(centres):
        ph = ((f / n) + i * 0.37) % 1.0
        for lag in (0.0, 0.5):           # two rings per drop, half a cycle apart
            p = (ph + lag) % 1.0
            rr = 0.6 + p * r * 1.9
            d = np.hypot(xx - cx, (yy - cy) * 1.15)
            m = (np.abs(d - rr) < 0.55) & water
            c.T[m] = tone + (base - tone) * p   # fades back into the water as it spreads
    # slow diagonal glint sweeping across the surface
    g = ((xx.astype(int) + yy.astype(int) - int(f * GLINT / n * 2)) % GLINT == 0) & water
    c.T[g] -= 0.35

# ------------------------------------------------- pixel-art koi (for res-1 faces)
KOI_TPL = ["..bb..",
           ".bppb.",
           ".bppb.",
           "fbbbbf",
           ".bbpb.",
           ".ppbb.",
           ".bppb.",
           "..bp..",
           "..bb..",
           "..bb..",
           ".ffff.",
           "ff..ff"]
KOI_COL = {'kohaku': ('kwhite', 'korange', 'kwhite', []),
           'showa':  ('kblack', 'korange', 'kwhite', [(4, 2), (6, 3)]),
           'sanke':  ('kwhite', 'korange', 'kwhite', [(4, 1), (7, 3), (2, 2)]),
           'chagoi': ('korange', 'korange', 'korange', [])}

def koi_sprite(c, x0, y0, pattern, rot=0, flipx=False, flipy=False):
    """stamp the 6x12 nose-up koi; rot in quarter turns (counter-clockwise)."""
    b, p_, f, spots = KOI_COL[pattern]
    g = np.array([list(r) for r in KOI_TPL])
    for (yy, xx) in spots:
        if g[yy, xx] in 'bp': g[yy, xx] = 'k'
    if flipx: g = g[:, ::-1]
    if flipy: g = g[::-1]
    g = np.rot90(g, rot)
    mats = {'b': b, 'p': p_, 'f': f, 'k': 'kblack'}
    h, w = g.shape
    for y in range(h):
        row = g[y]
        filled = [x for x in range(w) if row[x] != '.']
        for x in range(w):
            ch = row[x]
            if ch == '.': continue
            tone = 1.5 if ch == 'f' else 1.8
            if filled and (x == filled[0] or x == filled[-1]) and ch != 'f': tone += 0.5
            c.set(x0 + x, y0 + y, mat=mats[ch], tone=tone)


# ---------------------------------------------- pixel drawings (vanilla-res house style)
def rows_art(rows, pal):
    """Card or face painter from a pixel drawing. '.' is clear. pal: char -> (mat, tone 0..4).
    Back faces mirror so the card reads right from both sides."""
    STEP = (0, 1.0, 2.0, 4.0, 6.0)
    def p(c):
        ah, aw = len(rows), len(rows[0])
        mir = c.face in ('north', 'west', 'down')
        for y in range(c.h):
            for x in range(c.w):
                ax = int(x * aw / c.w)
                ch = rows[int(y * ah / c.h)][aw - 1 - ax if mir else ax]
                if ch != '.':
                    m, t = pal[ch]
                    c.set(x, y, mat=m, tone=STEP[t])
    return p

LOTUS = [
    "...PP...",
    ".P.LP.P.",
    ".PLLPPD.",
    "PLLLPPDD",
    ".PPPPPD.",
    "..gGGg..",
]
LOTUS_PAL = {"P": ("pink", 2), "L": ("pink", 1), "D": ("pink", 3), "g": ("lily", 2), "G": ("lily", 3)}

def petal_fan(mat='pink'):
    return rows_art(LOTUS, LOTUS_PAL)

BUD = [
    "..P..",
    ".LPD.",
    ".LPD.",
    "..g..",
]
def bud():
    return rows_art(BUD, LOTUS_PAL)


# ================================================ detailed foliage (Oct 19 2026 redraw)
# Everything below is hand-placed pixel art at 16 px per block: 5-tone ramps, outlines as
# continuous lines, highlights on the top-left, no lone noise pixels.
STEP = (0, 1.0, 2.0, 4.0, 6.0)

def _put(c, x, y, mat, ti):
    c.set(x, y, mat=mat, tone=STEP[max(0, min(4, ti))])

PAD12 = [
    "...OOOOOO...",
    ".OOLLLLLLOO.",
    ".OLLPPPPPPO.",
    "OLPVPPPPPVPO",
    "OLPPVPPPVPPO",
    "OLPPPVCOOOOO",
    "OLPPPCC.....",
    "OPPPPVCOOOOO",
    "OPPPVPPPVPPO",
    ".OPVPPPPPVO.",
    ".OOPPPPPPOO.",
    "...OOOOOO...",
]
PAD8 = [
    "..OOOO..",
    ".OLLLLO.",
    "OLVPPVPO",
    "OLPCOOOO",
    "OPPC....",
    "OPVPOOOO",
    ".OPPPVO.",
    "..OOOO..",
]
PAD6 = [
    ".OOOO.",
    "OLLLPO",
    "OLPPPO",
    "OLPCOO",
    "OPPPO.",
    ".OOOO.",
]
PAD_PAL = {"O": 3, "L": 1, "P": 2, "V": 3, "C": 4}

def lilypad(notch_dir=0.0, rim=True):
    """hand-drawn pad (12, 8 or 6 px): dark outline, lit top-left inner edge, diagonal veins,
    a V notch to the stem. notch_dir picks the quarter turn so pads don't all face one way."""
    def p(c):
        art = PAD12 if c.w >= 11 else PAD8 if c.w >= 7 else PAD6
        g = np.array([list(r) for r in art])
        # only mirror across the top-left/bottom-right diagonal, so the light stays top-left;
        # notch_dir picks notch-right or notch-down
        if int(round(notch_dir / (np.pi / 2))) % 2:
            g = g.T
        n = g.shape[0]
        for y in range(c.h):
            for x in range(c.w):
                ch = g[min(n - 1, y * n // c.h), min(n - 1, x * n // c.w)]
                if ch != '.':
                    _put(c, x, y, 'lily', PAD_PAL[ch])
    return p

LOTUS = [
    "....LP....",
    "..P.WLP.P.",
    ".PL.WLPD.D",
    ".LWLLPPDPD",
    "LWLLYYPPDD",
    ".LLPYYPPD.",
    "..PPPPPD..",
    "...gGGg...",
]
LOTUS_PAL = {"W": ("pink", 0), "L": ("pink", 1), "P": ("pink", 2), "D": ("pink", 3),
             "Y": ("yellow", 1), "g": ("lily", 2), "G": ("lily", 3)}

def petal_fan(mat='pink'):
    return rows_art(LOTUS, LOTUS_PAL)

BUD = [
    "..L..",
    ".LPD.",
    ".WPD.",
    ".LPD.",
    "..PD.",
    "..g..",
]
def bud():
    return rows_art(BUD, LOTUS_PAL)

def petal_ring(mat='pink', n=8):
    """top view of the open lotus: 8 pointed petals, pale tips, yellow seed head"""
    def p(c):
        W, H = c.w, c.h
        cx, cy = (W - 1) / 2, (H - 1) / 2
        yy, xx = np.mgrid[0:H, 0:W]
        dx, dy = xx - cx, yy - cy
        r = np.hypot(dx, dy); a = np.arctan2(dy, dx)
        k = (a % (2 * np.pi / n)) / (2 * np.pi / n) - 0.5
        R = min(W, H) / 2
        m = (r < R) & (np.abs(k) < 0.42 * (1 - r / R) + 0.12)
        c.M[m] = MI[mat]; c.T[m] = STEP[2]
        c.T[m & (r > R * 0.6)] = STEP[1]
        c.T[m & ((dx + dy) > 0) & (r > R * 0.3)] = STEP[3]
        ctr = r < R * 0.32
        c.M[ctr] = MI['yellow']; c.T[ctr] = STEP[1]
    return p

def grass(mat='moss', every=1, minh=0.35):
    """tidy tuft: blades of set heights, every other blade bends at the tip, dark base, lit tips"""
    HS = (1.0, 0.6, 0.85, 0.45, 0.95, 0.7, 0.55, 0.9)
    def p(c):
        for x in range(0, c.w, max(1, every)):
            n = max(1, int(round(HS[x % len(HS)] * c.h)))
            bend = 1 if x % 2 else -1
            for i in range(n):
                f = i / max(n - 1, 1)
                xx = x + (bend if (i == n - 1 and n >= 3) else 0)
                ti = 3 if f < 0.34 else 2 if f < 0.7 else 1
                _put(c, xx, c.h - 1 - i, mat, ti)
    return p

def reeds(heads=True, flower=None):
    """cattails / iris: 1 px stalks lit on the tips, long reed blades leaning out from the base,
    cattail heads 2 px wide (lit left column), or iris flowers"""
    def p(c):
        W, H = c.w, c.h
        stalks = [(1, 1.0), (3, 0.78), (W - 3, 0.9), (W - 2, 0.62)] if W >= 6 else [(1, 1.0), (W - 2, 0.8)]
        # blades first (behind): lean outwards, reed colour
        for x0, lean, hf in ((0, -1, 0.55), (W // 2, 1, 0.7), (W - 1, 1, 0.45), (2, -1, 0.4)):
            n = int(hf * H)
            for i in range(n):
                f = i / max(n - 1, 1)
                x = int(round(x0 + lean * 2 * f * f))
                _put(c, x, H - 1 - i, 'reed', 3 if f < 0.4 else 2 if f < 0.8 else 1)
        for k, (x, hf) in enumerate(stalks):
            n = int(hf * H)
            top = H - n
            for i in range(n):
                f = i / max(n - 1, 1)
                _put(c, x, H - 1 - i, 'moss', 3 if f < 0.5 else 2)
            if heads and k % 2 == 0 and n > 8:
                for j in range(1, 6):
                    _put(c, x, top + j, 'cattail', 1)
                    _put(c, x + 1, top + j, 'cattail', 2 if j < 5 else 3)
                _put(c, x, top + 1, 'cattail', 0)
            elif flower and k % 2 == 0:
                fy = top
                for dx, dy, ti in ((0, 0, 1), (-1, 1, 2), (1, 1, 2), (0, 1, 0), (0, 2, 3), (-1, 2, 3), (1, 2, 3)):
                    _put(c, x + dx, fy + dy, flower, ti)
    return p

def ivy():
    """vine with paired leaves: dark stem wandering down the card, 2x2 leaves lit top-left"""
    def p(c):
        W, H = c.w, c.h
        cx = W // 2
        for y in range(H):
            x = cx + (1 if (y // 4) % 2 and W >= 4 else 0)
            _put(c, x, y, 'moss', 4)
            if y % 3 == 1:
                s = -1 if (y // 3) % 2 else 1
                lx = x + s
                for ddx, ddy, ti in ((0, 0, 2), (s, 0, 1 if s < 0 else 2), (0, -1, 1), (s, -1, 1 if s < 0 else 2), (s, 1, 3)):
                    _put(c, lx + ddx, y + ddy, 'moss', ti)
    return p

SPROUT = [
    "W...L",
    "LL.LD",
    ".LGD.",
    "..G..",
    "..G..",
    "..G..",
]
def sprout():
    return rows_art(SPROUT, {"W": ("moss", 0), "L": ("moss", 1), "D": ("moss", 3), "G": ("moss", 3)})
