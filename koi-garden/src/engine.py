"""Model builder for the Mistbloom Koi Garden set.

Cubes + flat cards, one baked atlas per model, 1 texel per unit (res=2 for
half-texel detail), structured painting, Nexo-safe check(), Java model export.
"""
import json, math, zlib
import numpy as np
from PIL import Image

# ---------------------------------------------------------------- palette
# 4 anchors per ramp (hi, base, shade, outline) -> continuous 7-step tone 0..6
ANCH = {
    'teak':   ['#cf9566', '#a8683f', '#7c4729', '#502a17'],
    'stone':  ['#cfccc2', '#a9a69c', '#83817a', '#5a5853'],
    'moss':   ['#97c45e', '#6c9c3f', '#4b752b', '#2f4d1a'],
    'lily':   ['#b3d462', '#82ad3c', '#5b8429', '#3a5719'],
    'cream':  ['#fbf1dc', '#e6d6b4', '#c8b18a', '#93805c'],
    'kwhite': ['#ffffff', '#f3eee6', '#d8cfc1', '#a4998a'],
    'korange':['#ffb15a', '#f2772a', '#c9521a', '#8a3210'],
    'kblack': ['#55505c', '#38343e', '#25222b', '#16141a'],
    'water':  ['#7ccbd0', '#4596a3', '#2d6f7e', '#1b4957'],
    'glass':  ['#f0fbff', '#c5e6ee', '#94c6d3', '#62a0b2'],
    'brass':  ['#f6d47c', '#d6a642', '#a37626', '#6c4c16'],
    'pink':   ['#ffd6e3', '#f49cba', '#d26a90', '#94405f'],
    'reed':   ['#c6cc6c', '#99a443', '#6c7829', '#454e18'],
    'cattail':['#a8714a', '#7d4f30', '#5a361f', '#3a2112'],
    'grey':   ['#ffffff', '#e6e6e6', '#c6c6c6', '#9c9c9c'],   # dyeable
    'paper':  ['#fdf7e7', '#f0e4c7', '#d8c7a1', '#ab966e'],
    'clay':   ['#e09a6e', '#c0714a', '#94502f', '#62321b'],
    'yellow': ['#ffe68a', '#f2c84a', '#c99a2a', '#8a6614'],
    'rope':   ['#e2c793', '#c3a066', '#977745', '#64492a'],
}
MATS = list(ANCH)
MI = {m: i for i, m in enumerate(MATS)}

def _hex(h):
    return np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)], float)

_A = np.array([[_hex(h) for h in ANCH[m]] for m in MATS])  # (M,4,3)

def colour(mat_idx, tone):
    """vectorised: mat_idx int array, tone float array (0..6) -> rgb"""
    t = np.clip(tone, 0, 6) / 2.0
    i0 = np.clip(np.floor(t).astype(int), 0, 2)
    f = (t - i0)[..., None]
    a = _A[mat_idx, i0]
    b = _A[mat_idx, i0 + 1]
    return a * (1 - f) + b * f

def rgb(mat, tone=2):
    return tuple(int(v) for v in colour(np.array(MI[mat]), np.array(float(tone))))

def num(v, nd=2):
    """tidy number: 14.844999 -> 14.84, 6.0 -> 6"""
    r = round(float(v), nd)
    return int(r) if r == int(r) else r

def seed(*k):
    return zlib.crc32('|'.join(map(str, k)).encode())

# --------------------------------------------------------------- faces
FACES = ['north', 'south', 'east', 'west', 'up', 'down']
OPP = {'north': 'south', 'south': 'north', 'east': 'west', 'west': 'east'}

def turn(model):
    """Half turn about the block centre so the piece's front faces -z, the way Nexo and
    ModelEngine show furniture facing the player. Faces keep their painted look."""
    for e in model.els:
        (fx, fy, fz), (tx, ty, tz) = e.f, e.t
        e.f, e.t = (16 - tx, fy, 16 - tz), (16 - fx, ty, 16 - fz)
        if e.rot:
            ax, ang, (ox, oy, oz) = e.rot
            e.rot = (ax, ang if ax == 'y' else -ang, (16 - ox, oy, 16 - oz))
        e.turned = not getattr(e, 'turned', False)
    return model
SHADE = {'up': -0.6, 'north': 0.0, 'south': 0.0, 'east': 0.5, 'west': 0.5, 'down': 1.0}

def face_point(face, f, t, u, v):
    """Minecraft auto-UV convention: (u,v) in 0..1 across face -> element xyz."""
    x1, y1, z1 = f; x2, y2, z2 = t
    X = lambda a: x1 + (x2 - x1) * a
    Y = lambda a: y1 + (y2 - y1) * a
    Z = lambda a: z1 + (z2 - z1) * a
    if face == 'north': return (X(1 - u), Y(1 - v), z1)
    if face == 'south': return (X(u), Y(1 - v), z2)
    if face == 'east':  return (x2, Y(1 - v), Z(1 - u))
    if face == 'west':  return (x1, Y(1 - v), Z(u))
    if face == 'up':    return (X(u), y2, Z(v))
    if face == 'down':  return (X(u), y1, Z(1 - v))

def face_dims(face, f, t):
    dx, dy, dz = (t[0] - f[0], t[1] - f[1], t[2] - f[2])
    return {'north': (dx, dy), 'south': (dx, dy), 'east': (dz, dy), 'west': (dz, dy),
            'up': (dx, dz), 'down': (dx, dz)}[face]


class Ctx:
    """Paint target for one face. M = material index (-1 transparent), T = tone, A = alpha."""
    def __init__(self, el, face, w, h):
        self.el, self.face, self.w, self.h = el, face, w, h
        self.res = el.res
        self.M = np.full((h, w), -1, int)
        self.T = np.full((h, w), 2.0)
        self.A = np.full((h, w), 255, int)
        self.rng = np.random.default_rng(seed(el.model, el.name, face))
        yy, xx = np.mgrid[0:h, 0:w]
        self.u = (xx + 0.5) / w
        self.v = (yy + 0.5) / h
        # element-space coordinates of every pixel centre
        f, t = el.f, el.t
        if getattr(el, 'turned', False):
            # painters (koi patterns, eyes, ripples) work in the model's original, unturned space
            f, t = (16 - t[0], f[1], 16 - t[2]), (16 - f[0], t[1], 16 - f[2])
        P = face_point(face, f, t, self.u, self.v)
        self.P = [np.broadcast_to(np.asarray(c, float), (h, w)) for c in P]

    def fill(self, mat, tone=2.0):
        self.M[:] = MI[mat]; self.T[:] = tone

    def set(self, x, y, mat=None, tone=None, add=None, alpha=None):
        if 0 <= x < self.w and 0 <= y < self.h:
            if mat is not None: self.M[y, x] = MI[mat]
            if tone is not None: self.T[y, x] = tone
            if add is not None: self.T[y, x] += add
            if alpha is not None: self.A[y, x] = alpha

    def hline(self, y, x0, x1, **k):
        for x in range(int(x0), int(x1) + 1): self.set(x, int(y), **k)

    def vline(self, x, y0, y1, **k):
        for y in range(int(y0), int(y1) + 1): self.set(int(x), y, **k)

    def rect(self, x0, y0, x1, y1, **k):
        for x in range(int(x0), int(x1) + 1):
            self.set(x, int(y0), **k); self.set(x, int(y1), **k)
        for y in range(int(y0), int(y1) + 1):
            self.set(int(x0), y, **k); self.set(int(x1), y, **k)

    def mask(self, m, **k):
        if 'mat' in k: self.M[m] = MI[k['mat']]
        if 'tone' in k: self.T[m] = k['tone']
        if 'add' in k: self.T[m] += k['add']
        if 'alpha' in k: self.A[m] = k['alpha']


class El:
    def __init__(self, model, name, f, t, paint, res=1, rot=None, tint=False,
                 skip=(), plane=None, shade=True, emit=0):
        self.model, self.name, self.f, self.t = model, name, tuple(f), tuple(t)
        self.paint, self.res, self.rot, self.tint = paint, res, rot, tint
        self.skip, self.plane, self.shade, self.emit = set(skip), plane, shade, emit

    def faces(self):
        if self.plane:
            return {'x': ['east', 'west'], 'y': ['up', 'down'], 'z': ['south', 'north']}[self.plane]
        return [f for f in FACES if f not in self.skip]


class Model:
    def __init__(self, name, title=''):
        self.name, self.title, self.els = name, title or name, []
        self.meta = {}

    def cube(self, name, f, t, paint, **k):
        e = El(self.name, name, f, t, paint, **k); self.els.append(e); return e

    def box(self, name, origin, size, paint, **k):
        f = origin; t = tuple(o + s for o, s in zip(origin, size))
        return self.cube(name, f, t, paint, **k)

    def plane(self, name, origin, axis, size, paint, res=1, rot=None, tint=False):
        """Zero-thickness card. size=(a,b): z-plane (x,y); y-plane (x,z); x-plane (z,y)."""
        a, b = size; x, y, z = origin
        t = {'z': (x + a, y + b, z), 'y': (x + a, y, z + b), 'x': (x, y + b, z + a)}[axis]
        e = El(self.name, name, origin, t, paint, res=res, rot=rot, tint=tint,
               plane=axis, shade=False)
        self.els.append(e); return e

    # ---------------------------------------------------------- checks
    def check(self):
        n = len(self.els)
        assert n <= 19, f'{self.name}: {n} elements (max 19)'
        for e in self.els:
            for c in e.f + e.t:
                assert -16 <= c <= 32, f'{self.name}/{e.name}: coord {c} out of -16..32'
            if e.rot:
                ax, ang, org = e.rot
                assert ax in 'xyz' and ang in (-45, -22.5, 0, 22.5, 45), f'{e.name}: bad rotation {e.rot}'
            for fc in e.faces():
                fw, fh = face_dims(fc, e.f, e.t)
                pw, ph = math.ceil(round(fw * e.res, 3)), math.ceil(round(fh * e.res, 3))
                assert pw <= 32 and ph <= 32, f'{self.name}/{e.name}/{fc}: face {pw}x{ph}px > 32'
        return n

    # ---------------------------------------------------------- bake
    def bake(self):
        rects = []  # (el, face, img)
        for e in self.els:
            imgs = {}
            for fc in e.faces():
                if e.plane and fc in ('north', 'west', 'down'):
                    continue  # back side shares the front card's pixels
                fw, fh = face_dims(fc, e.f, e.t)
                w = max(1, math.ceil(round(fw * e.res, 3)))
                h = max(1, math.ceil(round(fh * e.res, 3)))
                # a turned element (see turn()) is painted as the face it was before the half turn
                pf = OPP[fc] if getattr(e, 'turned', False) and not e.plane and fc in OPP else fc
                c = Ctx(e, pf, w, h)
                p = e.paint
                if isinstance(p, dict):
                    p = p.get(pf, p.get('*'))
                p(c)
                if getattr(e, 'turned', False) and fc in ('up', 'down'):
                    c.M[:] = c.M[::-1, ::-1].copy(); c.T[:] = c.T[::-1, ::-1].copy(); c.A[:] = c.A[::-1, ::-1].copy()
                if e.shade:
                    c.T += SHADE[fc]
                rgbv = colour(np.clip(c.M, 0, None), c.T)
                img = np.zeros((h, w, 4), np.uint8)
                img[..., :3] = np.clip(rgbv, 0, 255)
                img[..., 3] = np.where(c.M < 0, 0, c.A)
                imgs[fc] = img
            if e.plane:
                front = {'x': 'east', 'y': 'up', 'z': 'south'}[e.plane]
                back = {'east': 'west', 'up': 'down', 'south': 'north'}[front]
                imgs[back] = None  # alias
                e._alias = (back, front)
            for fc, img in imgs.items():
                if img is not None:
                    rects.append((e, fc, img))
        # shelf pack, tallest first
        rects.sort(key=lambda r: (-r[2].shape[0], -r[2].shape[1]))
        size = 16
        while True:
            pos, x, y, sh, ok = {}, 0, 0, 0, True
            for e, fc, img in rects:
                h, w = img.shape[:2]
                if x + w > size:
                    x, y, sh = 0, y + sh, 0
                if y + h > size or w > size:
                    ok = False; break
                pos[(id(e), fc)] = (x, y, w, h)
                x += w; sh = max(sh, h)
            if ok: break
            size *= 2
        atlas = np.zeros((size, size, 4), np.uint8)
        for e, fc, img in rects:
            x, y, w, h = pos[(id(e), fc)]
            atlas[y:y + h, x:x + w] = img
        for e in self.els:
            e.uv = {}
            for fc in e.faces():
                key = fc
                if e.plane and fc == e._alias[0]:
                    key = e._alias[1]
                x, y, w, h = pos[(id(e), key)]
                e.uv[fc] = (x, y, x + w, y + h)
        self.atlas = atlas
        self.size = size
        return atlas

    # ---------------------------------------------------------- export
    def export(self, ns, tex_path, credit='Mistbloom'):
        self.bake()
        s = 16.0 / self.size
        els = []
        for e in self.els:
            faces = {}
            for fc in e.faces():
                x0, y0, x1, y1 = e.uv[fc]
                fd = {'uv': [num(x0 * s, 3), num(y0 * s, 3), num(x1 * s, 3), num(y1 * s, 3)],
                      'texture': '#0'}
                if e.tint:
                    fd['tintindex'] = 0
                faces[fc] = fd
            d = {'name': e.name, 'from': [num(v) for v in e.f], 'to': [num(v) for v in e.t], 'faces': faces}
            if e.plane:
                d['shade'] = False
            if e.emit:
                d['light_emission'] = e.emit
            if e.rot:
                ax, ang, org = e.rot
                d['rotation'] = {'angle': num(ang), 'axis': ax, 'origin': [num(v) for v in org]}
            els.append(d)
        return {
            'credit': credit,
            'texture_size': [self.size, self.size],
            'textures': {'0': f'{ns}:{tex_path}', 'particle': f'{ns}:{tex_path}'},
            'elements': els,
            'display': {
                'thirdperson_righthand': {'rotation': [75, 45, 0], 'translation': [0, 2.5, 0], 'scale': [0.375] * 3},
                'firstperson_righthand': {'rotation': [0, 45, 0], 'scale': [0.4] * 3},
                'ground': {'translation': [0, 3, 0], 'scale': [0.25] * 3},
                'gui': {'rotation': [30, 225, 0], 'scale': [0.625] * 3},
                'fixed': {'scale': [1, 1, 1]},
            },
        }


# =========================================================== painters
def solid(mat, tone=2.0):
    def p(c): c.fill(mat, tone)
    return p

def wood(mat='teak', plank=4, grain=True, seams=True, along=None):
    """Light structured wood: 5 soft bands, planks with own half-step tone,
    staggered butt joints, long grain streaks, the odd knot. No outline."""
    return lambda c: _wood(c, mat, plank, grain, seams, along)

def _wood(c, mat, plank, grain, seams, along):
    c.fill(mat, 2.0)
    w, h = c.w, c.h
    alongx = (w >= h) if along is None else along == 'u'
    L, W = (w, h) if alongx else (h, w)
    pw = max(2, plank * c.res)
    rng = c.rng
    G = np.zeros((W, L))
    G += 0.18 * np.sin(np.arange(L)[None, :] / max(L, 1) * math.pi * 5 + rng.uniform(0, 6))
    nplanks = max(1, math.ceil(W / pw))
    for k in range(nplanks):
        a0, a1 = k * pw, min(W, (k + 1) * pw)
        G[a0:a1] += rng.choice([-0.5, 0.0, 0.0, 0.5])
        if seams and k > 0:
            G[a0] += 1.0
        if seams and L >= 14:
            j = int((k * 7 + rng.integers(3, 9)) % (L - 4)) + 2
            G[a0:a1, j] += 1.0
        if grain:
            for _ in range(max(1, L // 8)):
                r = rng.integers(a0, a1)
                s0 = rng.integers(0, max(1, L - 4)); ln = rng.integers(3, max(4, L // 2))
                G[r, s0:s0 + ln] += 0.6
        if L >= 10 and rng.random() < 0.2:
            r = rng.integers(a0, a1); s = rng.integers(2, L - 2)
            G[r, s] += 1.4
            G[r, s + 1] += 0.7
    c.T = 2.0 + (G if alongx else G.T)

def endgrain(mat='teak'):
    def p(c):
        c.fill(mat, 2.0)
        cx, cy = (c.w - 1) / 2, (c.h - 1) / 2
        yy, xx = np.mgrid[0:c.h, 0:c.w]
        d = np.maximum(abs(xx - cx) / max(cx, .5), abs(yy - cy) / max(cy, .5))
        r = np.floor(d * 3).astype(int)
        c.T = 1.6 + 0.5 * (r % 2)
    return p

def capped(side, top):
    """different painter for up/down vs sides"""
    return {'up': top, 'down': top, '*': side}

def stone(mat='stone', course=4, moss=0.0):
    def p(c):
        c.fill(mat, 2.0)
        rng = c.rng
        ch = max(2, int(round(course * c.res)))
        for r0 in range(0, c.h, ch):
            x = -int(rng.integers(0, 6 * c.res))
            while x < c.w:
                ln = int(rng.integers(5, 10)) * c.res
                t = rng.choice([-0.4, 0.0, 0.0, 0.35])
                x0, x1 = max(0, x), min(c.w, x + ln)
                c.T[r0:r0 + ch, x0:x1] += t
                if x + ln < c.w:
                    c.T[r0:r0 + ch, x + ln - 1] = 3.0  # vertical joint
                # top-left highlight on each stone
                c.T[r0, x0:x1] -= 0.35
                x += ln
            if r0 > 0:
                c.T[r0 - 1, :] = 3.0  # bed joint
        if moss > 0 and c.face != 'down':
            # moss creeping along the top edge / top face patches (structured runs)
            yy, xx = np.mgrid[0:c.h, 0:c.w]
            if c.face == 'up':
                m = ((xx + yy * 2) % 9 < 2) & (np.sin(xx * 0.7) + np.cos(yy * 0.9) > 1.2 - moss)
            else:
                edge = (1.2 + 1.2 * np.sin(xx * 0.9 + 1.3)) * moss * c.res
                m = yy < edge
            c.mask(m, mat='moss', tone=2.0)
    return p

def fabric(mat='grey', stitch=True):
    def p(c):
        c.fill(mat, 1.5)
        yy, xx = np.mgrid[0:c.h, 0:c.w]
        L = max(c.w, c.h)
        band = (xx if c.w >= c.h else yy)
        c.T += 0.2 * ((band // (4 * c.res)) % 2)
        # puffed corners slightly darker
        k = 2 * c.res
        corner = ((xx < k) | (xx >= c.w - k)) & ((yy < k) | (yy >= c.h - k))
        c.T[corner] += 0.5
        if stitch and c.w > 6 and c.h > 4 and c.face == 'up':
            m = ((xx == 1) | (xx == c.w - 2) | (yy == 1) | (yy == c.h - 2)) & \
                (xx >= 1) & (xx <= c.w - 2) & (yy >= 1) & (yy <= c.h - 2) & (((xx + yy) % 2) == 0)
            c.T[m] = 2.4
    return p

def overlay(base, *fx):
    def p(c):
        base(c)
        for f in fx: f(c)
    return p

# --- motifs (applied as overlays) ---
def panel(inset=1):
    def f(c):
        i = inset * c.res
        if c.w > 2 * i + 2 and c.h > 2 * i + 2:
            c.rect(i, i, c.w - 1 - i, c.h - 1 - i, tone=3.0)
    return f

def wave(only=None, amp=None):
    """carved wave scroll band, one half-step darker than the surface."""
    def f(c):
        if only and c.face not in only: return
        h, w = c.h, c.w
        if h < 3 or w < 6: return
        mid = (h - 1) / 2
        a = amp if amp is not None else max(0.8, h / 4)
        P = 6 * c.res
        for x in range(w):
            y = mid - a * math.sin(2 * math.pi * x / P)
            c.set(x, int(round(y)), tone=3.0)
        # curls under each crest
        for k in range(-1, w // P + 2):
            cx = k * P + P / 4 + P * 0.18
            for t in np.linspace(0, 2 * math.pi * 0.8, 10):
                r = a * 0.7
                c.set(int(round(cx + r * math.cos(t))), int(round(mid + r * 0.9 + r * math.sin(t) - a * 0.4)), tone=3.0)
    return f


# ======================================================== koi painters
PATTERNS = {
    # list of (t0, t1, mat) patches over the back, t=0 at the nose
    'kohaku': {'base': 'kwhite', 'patch': [(0.04, 0.2, 'korange'), (0.32, 0.55, 'korange'), (0.66, 0.8, 'korange')], 'spots': []},
    'sanke':  {'base': 'kwhite', 'patch': [(0.1, 0.3, 'korange'), (0.45, 0.68, 'korange')], 'spots': [(0.38, 0.3), (0.62, -0.4), (0.78, 0.2)]},
    'showa':  {'base': 'kblack', 'patch': [(0.0, 0.22, 'korange'), (0.4, 0.6, 'korange')], 'spots': [], 'belly': 'kwhite'},
    'chagoi': {'base': 'korange', 'patch': [], 'spots': []},
    'magoi':  {'base': 'kblack', 'patch': [], 'spots': [], 'belly': 'kwhite'},
}

class Koi:
    """Describes one koi in model space so every part paints one continuous pattern.
    axis: 'x' or 'z' (body length axis in element space), head: +1/-1 direction of the nose,
    nose: coordinate of the nose tip, length: nose->tail-root length, cy: body centre height,
    cw: body centre on the across axis."""
    def __init__(self, axis, head, nose, length, cy, cw, half_h, half_w, pattern='kohaku', eye=True):
        self.axis, self.head, self.nose, self.length = axis, head, nose, length
        self.cy, self.cw, self.hh, self.hw = cy, cw, half_h, half_w
        self.pat = PATTERNS[pattern]; self.pname = pattern; self.eye = eye

    def tq(self, P):
        X, Y, Z = P
        al = X if self.axis == 'x' else Z
        ac = Z if self.axis == 'x' else X
        t = (self.nose - al) * self.head / self.length
        return t, (Y - self.cy) / self.hh, (ac - self.cw) / self.hw

    def painter(self, part='body'):
        pat = self.pat
        def p(c):
            t, yv, wv = self.tq(c.P)
            M = np.full((c.h, c.w), MI[pat['base']])
            T = np.full((c.h, c.w), 1.8)
            # patches on the back with wobbly edges
            wob = 0.04 * np.sin(wv * 3.1 + t * 9)
            for t0, t1, m in pat['patch']:
                inside = (t > t0 + wob) & (t < t1 - wob) & (yv > -0.25 + 0.3 * np.cos(t * 20))
                M[inside] = MI[m]
            for ts, ws in pat['spots']:
                d = ((t - ts) / 0.05) ** 2 + ((wv - ws) / 0.55) ** 2
                M[(d < 1) & (yv > -0.1)] = MI['kblack']
            belly = pat.get('belly', 'kwhite')
            M[yv < -0.55] = MI[belly]
            if pat['base'] == 'kblack':
                # showa/magoi: white flanks blending in
                M[(yv < -0.2) & (M == MI['kblack'])] = MI[belly]
            # soft dorsal light and scale rows (structured, every 2px, half-step)
            T -= 0.35 * np.clip(yv, 0, 1)
            if c.res >= 2:
                yy, xx = np.mgrid[0:c.h, 0:c.w]
                T[((xx + (yy // 2) % 2 * 2) % 4 == 0) & (yy % 2 == 0)] += 0.35
            c.M[:] = M; c.T[:] = T
            # eyes on the head sides
            if part == 'head' and self.eye and c.face in (('north', 'south') if self.axis == 'x' else ('east', 'west')):
                m = (abs(t - 0.1) < 0.045) & (abs(yv - 0.25) < 0.3)
                c.mask(m, mat='kblack', tone=4.5)
            if part == 'head' and c.face in (('east', 'west') if self.axis == 'x' else ('north', 'south')):
                # mouth on the nose face
                m = (abs(yv + 0.2) < 0.22) & (abs(wv) < 0.45)
                c.mask(m, mat='korange' if pat['base'] != 'korange' else 'kwhite', tone=3.5)
        return p

    def fin_mat(self):
        return {'kohaku': 'kwhite', 'sanke': 'kwhite', 'showa': 'kblack', 'chagoi': 'korange', 'magoi': 'kblack'}[self.pname]


def card(fn):
    """Plane painter from a pixel function fn(c, X, Y) on a grid where (0,0)=top-left of the card."""
    def p(c):
        fn(c)
    return p

def tail_card(mat, edge='korange'):
    """koi tail fan, root at the left edge-centre, flaring to the right (z-plane art)."""
    def p(c):
        w, h = c.w, c.h
        yy, xx = np.mgrid[0:h, 0:w]
        u = (xx + 0.5) / w; v = (yy + 0.5) / h - 0.5
        spread = 0.12 + 0.42 * u
        notch = (u > 0.7) & (abs(v) < (u - 0.7) * 0.9)
        m = (abs(v) < spread) & ~notch
        c.M[m] = MI[mat]; c.T[m] = 1.7
        # fin rays every 2px, half-step darker
        rays = m & (((np.arctan2(v, u + 0.25) * 9).astype(int) % 2) == 0)
        c.T[rays] += 0.5
        tip = m & (u > 0.72)
        if edge and mat == 'kwhite':
            c.M[tip & (abs(v) > 0.3)] = MI[edge]
    return p

def fin_card(mat):
    """small rounded fin, root along the bottom edge."""
    def p(c):
        w, h = c.w, c.h
        yy, xx = np.mgrid[0:h, 0:w]
        u = (xx + 0.5) / w - 0.5; v = 1 - (yy + 0.5) / h
        m = (u * u * 3.2 + v * v) < 1.0
        m &= (u > -0.5 + v * 0.45)
        c.M[m] = MI[mat]; c.T[m] = 1.7
        c.T[m & (xx % 2 == 0)] += 0.4
    return p

def pect_card(mat):
    """horizontal pectoral fins crossing under the body (y-plane), fins at both across-ends."""
    def p(c):
        w, h = c.w, c.h
        yy, xx = np.mgrid[0:h, 0:w]
        u = (xx + 0.5) / w; v = (yy + 0.5) / h
        m = (((u - 0.5) ** 2) * 6 + ((v - 0.5) ** 2) * 0.9) < 1  # long axis across
        m &= (abs(v - 0.5) > 0.3)
        c.M[m] = MI[mat]; c.T[m] = 1.8
        c.T[m & (xx % 2 == 0)] += 0.4
    return p
