"""Scene renderer for festival previews: blocks + the real Halloween piece models (textured),
night lighting from every light source, perspective camera (MC fov 70) or a far 'overview' camera.

render(cam_pos, target, w, h) -> PIL image. Coordinates are the festival's local frame.
"""
import os, sys, math, json, importlib, hashlib
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
HM = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src')
sys.path.insert(0, HM)
import festival as F
import engine as E

COL = {
 "andesite": (136, 136, 136), "barrel": (110, 80, 48), "bookshelf": (110, 80, 50), "campfire": (240, 150, 60),
 "candle": (230, 210, 170), "carved_pumpkin": (214, 120, 30), "chiseled_stone_bricks": (118, 118, 118),
 "coarse_dirt": (112, 80, 56), "cobblestone": (118, 118, 118), "cobblestone_stairs": (118, 118, 118), "cobblestone_wall": (118, 118, 118),
 "cracked_stone_bricks": (112, 112, 112), "dark_oak_door": (66, 44, 24), "dark_oak_fence": (66, 44, 24), "dark_oak_log": (58, 44, 30),
 "dark_oak_planks": (70, 48, 26), "dark_oak_slab": (70, 48, 26), "dark_oak_stairs": (70, 48, 26), "deepslate": (70, 70, 74),
 "deepslate_tile_stairs": (54, 54, 60), "deepslate_tile_wall": (54, 54, 60), "deepslate_tiles": (54, 54, 60), "dirt": (122, 86, 58),
 "dirt_path": (148, 120, 70), "fern": (80, 110, 50), "grass_block": (112, 128, 62), "gravel": (128, 122, 118), "hanging_roots": (150, 110, 80),
 "hay_block": (196, 162, 40), "iron_chain": (70, 74, 84), "jack_o_lantern": (232, 150, 40), "lantern": (250, 200, 110), "moss_block": (90, 112, 46),
 "mossy_cobblestone": (104, 118, 92), "mossy_cobblestone_wall": (104, 118, 92), "mossy_stone_bricks": (106, 118, 96), "pale_hanging_moss": (190, 196, 186),
 "pale_oak_leaves": (196, 200, 192), "pale_oak_log": (190, 184, 178), "podzol": (96, 66, 30), "pointed_dripstone": (130, 104, 90),
 "polished_andesite": (132, 134, 134), "pumpkin": (200, 118, 26), "purple_stained_glass_pane": (122, 60, 170), "red_mushroom": (190, 40, 36),
 "rooted_dirt": (130, 92, 66), "spruce_planks": (112, 82, 48), "spruce_slab": (112, 82, 48), "spruce_stairs": (112, 82, 48),
 "spruce_trapdoor": (100, 74, 44), "stone": (120, 120, 120), "stone_brick_slab": (122, 122, 122), "stone_brick_stairs": (122, 122, 122),
 "stone_brick_wall": (122, 122, 122), "stone_bricks": (122, 122, 122), "tuff": (108, 110, 100),
 "short_grass": (98, 122, 52), "leaf_litter": (150, 96, 44), "firefly_bush": (70, 96, 44), "dark_oak_leaves": (52, 84, 34),
 "cobblestone_slab": (118, 118, 118), "spruce_fence": (100, 74, 44), "stripped_spruce_log": (150, 112, 70),
}
EMIT = {"jack_o_lantern": 1.0, "lantern": 1.0, "campfire": 0.8, "candle": 0.8, "purple_stained_glass_pane": 0.0}
LIGHT_COLOR = np.array([1.0, 0.72, 0.42])        # warm firelight
MOON = np.array([0.36, 0.42, 0.62])              # cold moonlight ambient

def base(b): return b.split('[')[0].split('{')[0].replace('minecraft:', '')
def props(b):
    if '[' not in b: return {}
    return dict(kv.split('=') for kv in b.split('[')[1].split(']')[0].split(','))

def shapes(b):
    """List of (lo, hi) boxes in block units for a block state; [] = invisible."""
    n, p = base(b), props(b)
    if n in ('light', 'air'): return []
    if n.endswith('_slab'):
        return [((0, 0.5, 0), (1, 1, 1))] if p.get('type') == 'top' else [((0, 0, 0), (1, 0.5, 1))]
    if n.endswith('_stairs'):
        top = p.get('half') == 'top'
        slab = ((0, 0.5, 0), (1, 1, 1)) if top else ((0, 0, 0), (1, 0.5, 1))
        y0, y1 = (0, 0.5) if top else (0.5, 1)
        f = p.get('facing', 'north')
        q = {'north': ((0, y0, 0), (1, y1, 0.5)), 'south': ((0, y0, 0.5), (1, y1, 1)),
             'west': ((0, y0, 0), (0.5, y1, 1)), 'east': ((0.5, y0, 0), (1, y1, 1))}[f]
        return [slab, q]
    if n.endswith('_fence') or n.endswith('_wall') or n in ('iron_chain', 'end_rod'):
        w = 0.19 if n.endswith('_fence') else 0.25 if n.endswith('_wall') else 0.06
        hh = 1.0
        return [((0.5 - w, 0, 0.5 - w), (0.5 + w, hh, 0.5 + w))]
    if n.endswith('_pane'):
        return [((0.44, 0, 0), (0.56, 1, 1))] if p.get('north') == 'true' else [((0, 0, 0.44), (1, 1, 0.56))]
    if n.endswith('_trapdoor'):
        f = p.get('facing', 'north')
        return [{'east': ((0, 0, 0), (0.19, 1, 1)), 'west': ((0.81, 0, 0), (1, 1, 1)),
                 'south': ((0, 0, 0), (1, 1, 0.19)), 'north': ((0, 0, 0.81), (1, 1, 1))}[f]]
    if n.endswith('_door'):
        f = p.get('facing', 'east')
        return [{'east': ((0, 0, 0), (0.19, 1, 1)), 'west': ((0.81, 0, 0), (1, 1, 1)),
                 'south': ((0, 0, 0), (1, 1, 0.19)), 'north': ((0, 0, 0.81), (1, 1, 1))}[f]]
    if n == 'lantern':
        return [((0.31, 0.06 if p.get('hanging') == 'true' else 0, 0.31), (0.69, 0.56 if p.get('hanging') == 'true' else 0.5, 0.69))]
    if n == 'campfire': return [((0, 0, 0), (1, 0.44, 1))]
    if n == 'candle': return [((0.35, 0, 0.35), (0.65, 0.4, 0.65))]
    if n == 'leaf_litter': return [((0, 0, 0), (1, 0.06, 1))]
    if n == 'short_grass': return [((0.2, 0, 0.45), (0.8, 0.55, 0.55)), ((0.45, 0, 0.2), (0.55, 0.55, 0.8))]
    if n == 'firefly_bush': return [((0.1, 0, 0.1), (0.9, 0.8, 0.9))]
    if n in ('fern', 'red_mushroom', 'hanging_roots', 'pale_hanging_moss', 'pointed_dripstone'):
        return [((0.3, 0, 0.3), (0.7, 0.8, 0.7))]
    return [((0, 0, 0), (1, 1, 1))]

def opaque(b):
    s = shapes(b)
    return len(s) == 1 and s[0] == ((0, 0, 0), (1, 1, 1)) and 'leaves' not in b

FACES = {  # name: (normal, corner fn on box lo/hi)
    'up': ((0, 1, 0), lambda lo, hi: [(lo[0], hi[1], lo[2]), (hi[0], hi[1], lo[2]), (hi[0], hi[1], hi[2]), (lo[0], hi[1], hi[2])]),
    'down': ((0, -1, 0), lambda lo, hi: [(lo[0], lo[1], lo[2]), (lo[0], lo[1], hi[2]), (hi[0], lo[1], hi[2]), (hi[0], lo[1], lo[2])]),
    'north': ((0, 0, -1), lambda lo, hi: [(hi[0], hi[1], lo[2]), (lo[0], hi[1], lo[2]), (lo[0], lo[1], lo[2]), (hi[0], lo[1], lo[2])]),
    'south': ((0, 0, 1), lambda lo, hi: [(lo[0], hi[1], hi[2]), (hi[0], hi[1], hi[2]), (hi[0], lo[1], hi[2]), (lo[0], lo[1], hi[2])]),
    'west': ((-1, 0, 0), lambda lo, hi: [(lo[0], hi[1], lo[2]), (lo[0], hi[1], hi[2]), (lo[0], lo[1], hi[2]), (lo[0], lo[1], lo[2])]),
    'east': ((1, 0, 0), lambda lo, hi: [(hi[0], hi[1], hi[2]), (hi[0], hi[1], lo[2]), (hi[0], lo[1], lo[2]), (hi[0], lo[1], hi[2])]),
}
DIRS = {'up': (0, 1, 0), 'down': (0, -1, 0), 'north': (0, 0, -1), 'south': (0, 0, 1), 'west': (-1, 0, 0), 'east': (1, 0, 0)}

_MODELS = None
def models():
    global _MODELS
    if _MODELS is None:
        _MODELS = {}
        for mod in "hero3 harvest witchy graveyard critters market".split():
            for m in importlib.import_module(mod).all_models():
                m.bake(0)
                _MODELS[m.name] = m
    return _MODELS

def light_field(V, PIECES, bbox):
    """Approximate block light (0..15) on a grid: each source adds max(0, L - manhattan distance)."""
    (x0, y0, z0, x1, y1, z1) = bbox
    shp = (x1 - x0 + 1, y1 - y0 + 1, z1 - z0 + 1)
    gx, gy, gz = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1), np.arange(z0, z1 + 1), indexing='ij')
    L = np.zeros(shp, np.float32)
    srcs = []
    for (x, y, z), (b, r) in V.items():
        n = base(b)
        if n == 'light':
            srcs.append((x, y, z, int(props(b).get('level', 15))))
        elif n in ('jack_o_lantern', 'lantern', 'campfire'):
            srcs.append((x, y, z, 15 if n != 'campfire' else 14))
        elif n == 'candle':
            srcs.append((x, y, z, 9))
    for (x, y, z, l) in srcs:
        d = np.abs(gx - x) + np.abs(gy - y) + np.abs(gz - z)
        L = np.maximum(L, l - d)
    return np.clip(L, 0, 15), (x0, y0, z0)

def build_quads(V, PIECES, cam, max_dist=140):
    quads = []   # (corners[4x3], color or None, tex (model, i, f) or None, normal, emit, light_pos)
    cam = np.array(cam)
    for (x, y, z), (b, r) in V.items():
        if (x - cam[0]) ** 2 + (y - cam[1]) ** 2 + (z - cam[2]) ** 2 > max_dist ** 2:
            continue
        n = base(b)
        sh = shapes(b)
        if not sh: continue
        col = COL.get(n, (255, 0, 255))
        h = int(hashlib.md5(f"{x},{y},{z}".encode()).hexdigest()[:2], 16) / 255.0
        col = tuple(min(255, max(0, c * (0.9 + 0.2 * h))) for c in col)
        full = sh == [((0, 0, 0), (1, 1, 1))]
        for (lo, hi) in sh:
            for f, (nrm, fn) in FACES.items():
                d = DIRS[f]
                if full and (x + d[0], y + d[1], z + d[2]) in V and opaque(V[(x + d[0], y + d[1], z + d[2])][0]):
                    continue
                c = fn(lo, hi)
                corners = np.array(c) + np.array([x, y, z])
                if np.dot(np.array(nrm), cam - corners.mean(0)) <= 0:
                    continue
                fcol = col
                if n == 'grass_block' and f != 'up': fcol = COL['dirt']
                if n.endswith('_log') and f in ('up', 'down') and props(b).get('axis', 'y') == 'y': fcol = tuple(c * 1.25 for c in col)
                quads.append((corners, fcol, None, nrm, EMIT.get(n, 0), (x + 0.5 + d[0] * 0.6, y + 0.5 + d[1] * 0.6, z + 0.5 + d[2] * 0.6)))
    MD = models()
    for (name, x, y, z, yaw) in PIECES:
        m = MD[name]
        fl = m.floor
        cx, cy, cz = x + 0.5, y + 0.5 - fl / 16, z + 0.5
        phi = math.radians(180 - yaw)
        R = np.array([[math.cos(phi), 0, math.sin(phi)], [0, 1, 0], [-math.sin(phi), 0, math.cos(phi)]])
        for i, e in enumerate(m.elements):
            for f in e["faces"]:
                corners = E._face_corners(e, f)
                nrm = E._NORMALS[f]
                if "rotation" in e:
                    rr = e["rotation"]
                    Mx = {"x": E._rx, "y": E._ry, "z": E._rz}[rr["axis"]](rr["angle"])
                    o = np.array(rr["origin"])
                    corners = [Mx @ (p - o) + o for p in corners]
                    nrm = Mx @ nrm
                wc = np.array([R @ ((np.array(p) - 8) / 16) + (cx, cy, cz) for p in corners])
                wn = R @ np.array(nrm, float)
                two = len(e["faces"]) == 2
                if not two and np.dot(wn, cam - wc.mean(0)) <= 0:
                    continue
                quads.append((wc, None, (m, i, f), wn, 1.0 if e["emit"] >= 10 else 0, tuple(wc.mean(0))))
    return quads

def render(cam, target, w=960, h=540, fov=70, quads=None, lightinfo=None, sky=True):
    cam = np.array(cam, float); target = np.array(target, float)
    fwd = target - cam; fwd /= np.linalg.norm(fwd)
    right = np.cross(fwd, [0, 1, 0]); right /= np.linalg.norm(right)
    up = np.cross(right, fwd)
    fpx = (h / 2) / math.tan(math.radians(fov / 2))
    img = np.zeros((h, w, 3), np.float32)
    if sky:
        t = np.linspace(0, 1, h)[:, None]
        img[:] = ((1 - t) * np.array([10, 12, 32]) + t * np.array([34, 30, 64]))[:, None, :][:, 0, :][:, None, :]
        rs = np.random.RandomState(3)
        for _ in range(260):
            sx, sy = rs.randint(0, w), rs.randint(0, int(h * 0.8))
            img[sy, sx] = (200 + rs.randint(55),) * 3
    zb = np.full((h, w), np.inf, np.float32)
    LF, (lx0, ly0, lz0) = lightinfo
    shade = {"up": 1.0, "down": 0.5, "north": 0.8, "south": 0.8, "east": 0.65, "west": 0.65}
    def lightat(p):
        i, j, k = int(math.floor(p[0])) - lx0, int(math.floor(p[1])) - ly0, int(math.floor(p[2])) - lz0
        if 0 <= i < LF.shape[0] and 0 <= j < LF.shape[1] and 0 <= k < LF.shape[2]:
            return LF[i, j, k]
        return 0.0
    for (corners, col, tex, nrm, emit, lp) in quads:
        rel = corners - cam
        zc = rel @ fwd
        if (zc < 0.15).any():
            continue
        sx = (rel @ right) / zc * fpx + w / 2
        sy = -(rel @ up) / zc * fpx + h / 2
        if sx.max() < 0 or sx.min() > w or sy.max() < 0 or sy.min() > h:
            continue
        x0, x1 = int(max(0, sx.min())), int(min(w, sx.max() + 1))
        y0, y1 = int(max(0, sy.min())), int(min(h, sy.max() + 1))
        if x1 <= x0 or y1 <= y0: continue
        # split quad into 2 triangles, barycentric with perspective-correct (a,b) params on the quad
        gx, gy = np.meshgrid(np.arange(x0, x1) + 0.5, np.arange(y0, y1) + 0.5)
        P = np.stack([sx, sy], 1)
        best_m = np.zeros(gx.shape, bool); A = np.zeros(gx.shape); B = np.zeros(gx.shape); Z = np.zeros(gx.shape)
        for (i0, i1, i2) in ((0, 1, 2), (0, 2, 3)):
            p0, p1, p2 = P[i0], P[i1], P[i2]
            den = (p1[1] - p2[1]) * (p0[0] - p2[0]) + (p2[0] - p1[0]) * (p0[1] - p2[1])
            if abs(den) < 1e-9: continue
            l0 = ((p1[1] - p2[1]) * (gx - p2[0]) + (p2[0] - p1[0]) * (gy - p2[1])) / den
            l1 = ((p2[1] - p0[1]) * (gx - p2[0]) + (p0[0] - p2[0]) * (gy - p2[1])) / den
            l2 = 1 - l0 - l1
            m = (l0 >= -1e-4) & (l1 >= -1e-4) & (l2 >= -1e-4)
            # perspective-correct
            iz = l0 / zc[i0] + l1 / zc[i1] + l2 / zc[i2]
            zz = 1 / np.where(iz == 0, 1e-9, iz)
            uv = {0: (0, 0), 1: (1, 0), 2: (1, 1), 3: (0, 1)}
            a = (l0 * uv[i0][0] / zc[i0] + l1 * uv[i1][0] / zc[i1] + l2 * uv[i2][0] / zc[i2]) * zz
            bb = (l0 * uv[i0][1] / zc[i0] + l1 * uv[i1][1] / zc[i1] + l2 * uv[i2][1] / zc[i2]) * zz
            A = np.where(m, a, A); B = np.where(m, bb, B); Z = np.where(m, zz, Z); best_m |= m
        sub = zb[y0:y1, x0:x1]
        m = best_m & (Z < sub)
        if not m.any(): continue
        # lighting
        nl = np.array(nrm, float)
        fname = min(DIRS, key=lambda k: -np.dot(DIRS[k], nl))
        bl = lightat(lp) / 15.0
        lit = MOON * (0.55 + 0.45 * max(0.0, nl[1])) * shade[fname] + LIGHT_COLOR * (bl ** 1.6) * 1.15
        if tex is None:
            c = np.array(col, float) / 255.0
            if emit: c = c * (0.85 + 0.3 * emit)
            else: c = c * lit
            pix = np.broadcast_to(c, (m.sum(), 3))
        else:
            mdl, i, f = tex
            u1, v1, u2, v2 = mdl.uv[(i, f)]
            tx = np.clip((u1 + A * (u2 - u1)).astype(int), u1, u2 - 1)
            ty = np.clip((v1 + B * (v2 - v1)).astype(int), v1, v2 - 1)
            t = mdl.atlas[ty, tx]
            m &= t[..., 3] >= 128
            if not m.any(): continue
            c = t[..., :3][m].astype(float) / 255.0
            pix = c * (1.0 if emit else 1.0) if emit else c * lit
        region = img[y0:y1, x0:x1]
        region[m] = np.clip(pix * 255, 0, 255)
        sub[m] = Z[m]
    out = Image.fromarray(img.astype(np.uint8))
    # soft glow around bright pixels (lanterns, flames)
    arr = np.asarray(out).astype(float)
    bright = np.clip(arr.max(2) - 170, 0, 85) / 85.0
    glow = Image.fromarray((bright[..., None] * np.array([255, 170, 80])).astype(np.uint8)).filter(ImageFilter.GaussianBlur(9))
    out = Image.fromarray(np.clip(arr + np.asarray(glow).astype(float) * 0.9, 0, 255).astype(np.uint8))
    return out

_CACHE = {}
def scene():
    if 'q' not in _CACHE:
        V = F.build_all()
        LF = light_field(V, F.PIECES, (-40, -6, -46, 40, 24, 50))
        _CACHE.update(V=V, LF=LF)
    return _CACHE['V'], _CACHE['LF']

def shot(cam, target, w=960, h=540, fov=70, dist=150):
    V, LF = scene()
    q = build_quads(V, F.PIECES, cam, dist)
    return render(cam, target, w, h, fov, q, LF)

if __name__ == '__main__':
    import time
    t = time.time()
    img = shot((-40, 34, -70), (0, 0, 2), 1280, 720, 60, 400)
    img.save('/home/claude/festival/prev_overview.png'); print('overview', time.time() - t)
