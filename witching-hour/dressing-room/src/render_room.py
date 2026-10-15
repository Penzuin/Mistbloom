"""Preview renderer for the Witching Hour dressing room.

Blocks come from room.py; the six cosmetics are the real Witching Hour models (textured),
placed exactly as the datapack's item displays place them. An optional figure (Zinguin wearing
a set) stands on the dais to show what the wardrobe camera sees.
"""
import os, sys, math, copy, hashlib
import numpy as np
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
WH = "/root/mb/witching-hour/src"
FEST = "/root/fest/hollowmere/festival"
sys.path.insert(0, HERE)
sys.path.insert(0, WH)
import room as RM
import engine as E                      # Witching Hour engine
from pieces import PIECES
from player import player
import preview as WP

sys.path.insert(0, FEST)
import importlib.util
_spec = importlib.util.spec_from_file_location("fest_render_shapes", os.path.join(FEST, "render.py"))
# the festival renderer imports its own engine/festival modules; only borrow its block tables
_src = open(os.path.join(FEST, "render.py")).read()
_ns = {"__file__": os.path.join(FEST, "render.py")}
exec(_src.split("_MODELS = None")[0].replace("import festival as F\nimport engine as E\n", ""), _ns)
COL, FACES, DIRS = dict(_ns["COL"]), _ns["FACES"], _ns["DIRS"]
base, props, _shapes = _ns["base"], _ns["props"], _ns["shapes"]

COL.update({
    "polished_deepslate": (74, 74, 78), "polished_deepslate_slab": (74, 74, 78), "polished_deepslate_wall": (74, 74, 78),
    "deepslate_bricks": (66, 66, 70), "deepslate_brick_stairs": (66, 66, 70), "deepslate_brick_slab": (66, 66, 70),
    "chiseled_deepslate": (56, 56, 60), "purple_terracotta": (122, 72, 90), "stripped_dark_oak_log": (98, 76, 52),
    "deepslate_tile_slab": (54, 54, 60), "black_carpet": (28, 26, 34), "purple_carpet": (126, 50, 176),
    "yellow_stained_glass_pane": (236, 210, 90), "sea_lantern": (190, 214, 206), "amethyst_cluster": (186, 132, 232),
    "amethyst_block": (134, 96, 190), "purple_candle": (128, 60, 176), "dark_oak_wall_sign": (70, 48, 28),
    "dark_oak_sign": (70, 48, 28), "lightning_rod": (200, 120, 80), "spruce_trapdoor": (112, 82, 48),
    "dark_oak_door": (66, 44, 24), "skeleton_skull": (214, 210, 194), "purple_stained_glass": (122, 60, 170),
    "yellow_stained_glass": (236, 210, 90),
})
EMIT = {"lantern": 1.0, "candle": 0.8, "purple_candle": 0.8, "sea_lantern": 1.0, "amethyst_cluster": 0.6}
LIGHT_COLOR = np.array([1.0, 0.74, 0.46])
AMBIENT = np.array([0.30, 0.31, 0.44])


def shapes(b):
    n, p = base(b), props(b)
    if n.endswith("_carpet"):
        return [((0, 0, 0), (1, 0.0625, 1))]
    if n.endswith("_wall_sign"):
        f = p.get("facing", "north")
        return [{"east": ((0, 0.28, 0), (0.12, 0.78, 1)), "west": ((0.88, 0.28, 0), (1, 0.78, 1)),
                 "south": ((0, 0.28, 0), (1, 0.78, 0.12)), "north": ((0, 0.28, 0.88), (1, 0.78, 1))}[f]]
    if n.endswith("_sign"):
        return [((0.46, 0, 0.46), (0.54, 0.6, 0.54)), ((0, 0.5, 0.45), (1, 1.05, 0.55))]
    if n == "amethyst_cluster":
        return [((0.2, 0, 0.2), (0.8, 0.45, 0.8))]
    if n == "purple_candle":
        return [((0.3, 0, 0.3), (0.7, 0.4, 0.7))]
    if n == "skeleton_skull":
        return [((0.25, 0, 0.25), (0.75, 0.5, 0.75))]
    if n == "lightning_rod":
        return [((0.44, 0, 0.44), (0.56, 1, 0.56))]
    if n == "spruce_trapdoor":
        return [((0, 0.81, 0), (1, 1, 1))]
    if n == "polished_deepslate_wall":
        return [((0.25, 0, 0.25), (0.75, 1, 0.75))]
    return _shapes(b)


def opaque(b):
    s = shapes(b)
    return len(s) == 1 and s[0] == ((0, 0, 0), (1, 1, 1)) and "leaves" not in b and "_pane" not in b


# ------------------------------------------------------------------ models
_MOD = {}


def model(key):
    if key not in _MOD:
        mk = {k: f for k, _, _, _, f in PIECES}[key]
        m = mk()
        m.bake(1)
        _MOD[key] = m
    return _MOD[key]


def hand_scale(m):
    return 1.6 * m.display()["thirdperson_lefthand"]["scale"][0]


def yaw_R(yaw):
    phi = math.radians(180 - yaw)
    return np.array([[math.cos(phi), 0, math.sin(phi)], [0, 1, 0], [-math.sin(phi), 0, math.cos(phi)]])


def display_transform(d):
    """For a display dict: (model, sc, tilt matrix, entity position) - the same numbers the datapack uses.
    World point of model point p = pos + Ryaw @ (tilt @ (p - 8)) * sc / 25.6"""
    m = model(d["id"])
    sc = getattr(m, "scale", 1.0) * d.get("mult", 1.0)          # hand items show at lantern-block size, upright as authored
    tilt = np.eye(3)
    lo, hi = m.bounds()
    pts = np.array([[a, b, c] for a in (lo[0], hi[0]) for b in (lo[1], hi[1]) for c in (lo[2], hi[2])])
    tp = (tilt @ (pts - 8).T).T
    tlo, thi = tp.min(0), tp.max(0)
    if d["anchor"] == "pivot":
        a = np.zeros(3)
    elif d["anchor"] == "top":
        a = np.array([(tlo[0] + thi[0]) / 2, thi[1], (tlo[2] + thi[2]) / 2])
    elif d["anchor"] == "bottom":
        a = np.array([(tlo[0] + thi[0]) / 2, tlo[1], (tlo[2] + thi[2]) / 2])
    else:
        a = (tlo + thi) / 2
    R = yaw_R(d["yaw"])
    pos = np.array(d["target"]) - R @ (a * sc / 25.6)
    return m, sc, tilt, pos


def model_quads(m, world_fn, cam, scale_inside=1.0, dy=0.0):
    out = []
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
            corners = [8 + (np.array(p) - 8) * scale_inside + np.array([0, dy, 0]) for p in corners]
            wc = np.array([world_fn(p) for p in corners])
            wn = world_fn(np.array(nrm, float) + 8, normal=True)
            if np.dot(wn, cam - wc.mean(0)) <= 0:
                continue
            out.append((wc, None, (m, i, f), wn, 1.0 if e["emit"] >= 10 else 0, tuple(wc.mean(0))))
    return out


def figure(cam, set_=("witch_hat", "moonlit_broom", "ghostlight_lantern", "wisp")):
    """Zinguin on the dais wearing a set, built in the head-slot frame like the listing previews."""
    x, y, z, yaw, _ = RM.NPC
    head = np.array([x, y + 0.0625 + 1.75, z])
    R = yaw_R(yaw)
    def wf(p, normal=False):
        v = R @ (np.array(p, float) - 8)
        return v / np.linalg.norm(v) if normal else head + v / 25.6
    body = WP.body()
    body.bake(1)
    q = model_quads(body, wf, cam)
    slot = {k: s for k, _, s, _, _ in PIECES}
    for key in set_:
        for (mm, dy) in WP.worn(key, slot[key], model(key)):
            mm.bake(1)
            q += model_quads(mm, wf, cam, getattr(mm, "scale", 1.0), dy)
    return q


def display_quads(cam):
    q = []
    for d in RM.DISPLAYS:
        m, sc, tilt, pos = display_transform(d)
        R = yaw_R(d["yaw"])
        def wf(p, normal=False, R=R, tilt=tilt, pos=pos, sc=sc):
            v = R @ (tilt @ (np.array(p, float) - 8))
            return v / np.linalg.norm(v) if normal else pos + v * sc / 25.6
        q += model_quads(m, wf, cam)
    return q


# ------------------------------------------------------------------ blocks
def lit_pane(V, x, y, z, b):
    if "stained_glass" not in b:
        return False
    return any(base(V.get((x + dx, y, z + dz), ("", ""))[0]) == "sea_lantern" for dx, dz in ((0, 1), (0, -1), (1, 0), (-1, 0)))


def block_quads(V, cam, max_dist=120, cut_y=None):
    quads = []
    cam = np.array(cam)
    for (x, y, z), (b, r) in V.items():
        if cut_y is not None and y > cut_y:
            continue
        if (x - cam[0]) ** 2 + (y - cam[1]) ** 2 + (z - cam[2]) ** 2 > max_dist ** 2:
            continue
        n = base(b)
        sh = shapes(b)
        if not sh:
            continue
        col = COL.get(n, (255, 0, 255))
        h = int(hashlib.md5(f"{x},{y},{z}".encode()).hexdigest()[:2], 16) / 255.0
        col = tuple(min(255, max(0, c * (0.92 + 0.16 * h))) for c in col)
        emit = EMIT.get(n, 0)
        if lit_pane(V, x, y, z, b):
            emit = 1.0
            emit = 0.75
            col = (232, 196, 104) if n.startswith("yellow") else (150, 96, 206)
        full = sh == [((0, 0, 0), (1, 1, 1))]
        for (lo, hi) in sh:
            for f, (nrm, fn) in FACES.items():
                d = DIRS[f]
                nb = V.get((x + d[0], y + d[1], z + d[2]))
                if full and nb and opaque(nb[0]) and not (cut_y is not None and y + d[1] > cut_y):
                    continue
                corners = np.array(fn(lo, hi)) + np.array([x, y, z])
                if np.dot(np.array(nrm), cam - corners.mean(0)) <= 0:
                    continue
                fcol = col
                if n == "grass_block" and f != "up":
                    fcol = COL["dirt"]
                if n.endswith("_log") and "stripped" not in n and f in ("up", "down") and props(b).get("axis", "y") == "y":
                    fcol = tuple(c * 1.3 for c in col)
                quads.append((corners, fcol, None, nrm, emit,
                              (x + 0.5 + d[0] * 0.6, y + 0.5 + d[1] * 0.6, z + 0.5 + d[2] * 0.6)))
    return quads


def light_field(V, bbox):
    (x0, y0, z0, x1, y1, z1) = bbox
    gx, gy, gz = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1), np.arange(z0, z1 + 1), indexing="ij")
    L = np.zeros(gx.shape, np.float32)
    lv = {"lantern": 15, "sea_lantern": 15, "amethyst_cluster": 5, "purple_candle": 12, "candle": 12}
    for (x, y, z), (b, r) in V.items():
        n = base(b)
        l = int(props(b).get("level", 15)) if n == "light" else lv.get(n, 0)
        if l:
            L = np.maximum(L, l - (np.abs(gx - x) + np.abs(gy - y) + np.abs(gz - z)))
    for d in RM.DISPLAYS:                    # the glowing cosmetics light their alcoves a little
        if d["id"] in ("wisp", "ghostlight_lantern"):
            x, y, z = (int(math.floor(v)) for v in d["target"])
            L = np.maximum(L, 10 - (np.abs(gx - x) + np.abs(gy - y) + np.abs(gz - z)))
    return np.clip(L, 0, 15), (x0, y0, z0)


def render(cam, target, quads, LF, w=1280, h=720, fov=70, sky=True, indoor=False):
    cam = np.array(cam, float); target = np.array(target, float)
    fwd = target - cam; fwd /= np.linalg.norm(fwd)
    right = np.cross(fwd, [0, 1, 0])
    if np.linalg.norm(right) < 1e-6:
        right = np.array([1.0, 0, 0])
    right /= np.linalg.norm(right)
    up = np.cross(right, fwd)
    fpx = (h / 2) / math.tan(math.radians(fov / 2))
    img = np.zeros((h, w, 3), np.float32)
    if sky:
        t = np.linspace(0, 1, h)[:, None]
        img[:] = ((1 - t) * np.array([10, 12, 32]) + t * np.array([36, 30, 66]))[:, None, :][:, 0, :][:, None, :]
        rs = np.random.RandomState(3)
        for _ in range(300):
            img[rs.randint(0, h), rs.randint(0, w)] = (200 + rs.randint(55),) * 3
    zb = np.full((h, w), np.inf, np.float32)
    lf, (lx0, ly0, lz0) = LF
    amb = AMBIENT * (0.55 if indoor else 1.0)
    shade = {"up": 1.0, "down": 0.55, "north": 0.82, "south": 0.82, "east": 0.68, "west": 0.68}
    def lightat(p):
        i, j, k = int(math.floor(p[0])) - lx0, int(math.floor(p[1])) - ly0, int(math.floor(p[2])) - lz0
        if 0 <= i < lf.shape[0] and 0 <= j < lf.shape[1] and 0 <= k < lf.shape[2]:
            return lf[i, j, k]
        return 0.0
    quads = sorted(quads, key=lambda q: -float(np.sum((q[0].mean(0) - cam) ** 2)))   # far first, so see-through texels blend right
    for (corners, col, tex, nrm, emit, lp) in quads:
        rel = corners - cam
        zc = rel @ fwd
        if (zc < 0.12).any():
            continue
        sx = (rel @ right) / zc * fpx + w / 2
        sy = -(rel @ up) / zc * fpx + h / 2
        if sx.max() < 0 or sx.min() > w or sy.max() < 0 or sy.min() > h:
            continue
        x0, x1 = int(max(0, sx.min())), int(min(w, sx.max() + 1))
        y0, y1 = int(max(0, sy.min())), int(min(h, sy.max() + 1))
        if x1 <= x0 or y1 <= y0:
            continue
        gx, gy = np.meshgrid(np.arange(x0, x1) + 0.5, np.arange(y0, y1) + 0.5)
        P = np.stack([sx, sy], 1)
        hit = np.zeros(gx.shape, bool); A = np.zeros(gx.shape); B = np.zeros(gx.shape); Z = np.zeros(gx.shape)
        uv = {0: (0, 0), 1: (1, 0), 2: (1, 1), 3: (0, 1)}
        for (i0, i1, i2) in ((0, 1, 2), (0, 2, 3)):
            p0, p1, p2 = P[i0], P[i1], P[i2]
            den = (p1[1] - p2[1]) * (p0[0] - p2[0]) + (p2[0] - p1[0]) * (p0[1] - p2[1])
            if abs(den) < 1e-9:
                continue
            l0 = ((p1[1] - p2[1]) * (gx - p2[0]) + (p2[0] - p1[0]) * (gy - p2[1])) / den
            l1 = ((p2[1] - p0[1]) * (gx - p2[0]) + (p0[0] - p2[0]) * (gy - p2[1])) / den
            l2 = 1 - l0 - l1
            m = (l0 >= -1e-4) & (l1 >= -1e-4) & (l2 >= -1e-4)
            iz = l0 / zc[i0] + l1 / zc[i1] + l2 / zc[i2]
            zz = 1 / np.where(iz == 0, 1e-9, iz)
            a = (l0 * uv[i0][0] / zc[i0] + l1 * uv[i1][0] / zc[i1] + l2 * uv[i2][0] / zc[i2]) * zz
            bb = (l0 * uv[i0][1] / zc[i0] + l1 * uv[i1][1] / zc[i1] + l2 * uv[i2][1] / zc[i2]) * zz
            A = np.where(m, a, A); B = np.where(m, bb, B); Z = np.where(m, zz, Z); hit |= m
        sub = zb[y0:y1, x0:x1]
        m = hit & (Z < sub)
        if not m.any():
            continue
        nl = np.array(nrm, float); nl /= (np.linalg.norm(nl) or 1)
        fname = min(DIRS, key=lambda k: -np.dot(DIRS[k], nl))
        bl = lightat(lp) / 15.0
        lit = amb * (0.6 + 0.4 * max(0.0, nl[1])) * shade[fname] + LIGHT_COLOR * (bl ** 1.5) * 1.2
        if tex is None:
            c = np.array(col, float) / 255.0
            c = c * (0.75 + 0.3 * emit) if emit else c * lit
            pix = np.broadcast_to(c, (m.sum(), 3))
        else:
            mdl, i, f = tex
            u1, v1, u2, v2 = mdl.uv[(i, f)]
            tx = np.clip((u1 + A * (u2 - u1)).astype(int), u1, u2 - 1)
            ty = np.clip((v1 + B * (v2 - v1)).astype(int), v1, v2 - 1)
            t = mdl.atlas[ty, tx]
            al = t[..., 3].astype(float) / 255.0
            m &= al >= 0.15
            if not m.any():
                continue
            c = t[..., :3][m].astype(float) / 255.0
            pix = c if emit else c * np.maximum(lit, 0.35)
            a_ = al[m][:, None]
            if (a_ < 0.98).any():                  # translucent texels (the wisp) blend over what's behind
                region = img[y0:y1, x0:x1]
                region[m] = np.clip(pix * 255 * a_ + region[m] * (1 - a_), 0, 255)
                solid = m.copy(); solid[m] = al[m] >= 0.98
                sub[solid] = Z[solid]
                continue
        img[y0:y1, x0:x1][m] = np.clip(pix * 255, 0, 255)
        sub[m] = Z[m]
    out = np.asarray(img).astype(float)
    bright = np.clip(out.max(2) - 228, 0, 27) / 27.0
    glow = Image.fromarray((bright[..., None] * np.array([255, 190, 120])).astype(np.uint8)).filter(ImageFilter.GaussianBlur(8))
    return Image.fromarray(np.clip(out + np.asarray(glow).astype(float) * 0.8, 0, 255).astype(np.uint8))


_C = {}


def scene(with_island=True):
    key = ("V", with_island)
    if key not in _C:
        V = RM.build_all(with_island)
        _C[key] = (dict(V), light_field(V, (-26, -4, -26, 26, 20, 32)))
    return _C[key]


def shot(cam, target, w=1280, h=720, fov=70, with_figure=False, indoor=False, cut_y=None, island=True, sky=True):
    V, LF = scene(island)
    q = block_quads(V, cam, cut_y=cut_y) + display_quads(np.array(cam, float))
    if with_figure:
        q += figure(np.array(cam, float))
    return render(cam, target, q, LF, w, h, fov, sky=sky, indoor=indoor)
