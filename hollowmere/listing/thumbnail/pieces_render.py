"""Render Halloween Festival pieces for the Hibiscus-style store icon (same recipe as Moonlit Ballroom):
one camera, one scale, plus a hard sun-shadow mask (every cube projected onto the floor)."""
import os, sys, importlib
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, "/home/claude/hollow")
import engine as E

CAM = (-0.55, 0.75, -1.0)
LIGHT = np.array([-0.45, -1.5, 0.3])
SS = 3
PPU = 7 * SS

PICKS = {   # name: (module, function, lit)
    "scarecrow": ("hero3", "scarecrow", None),
    "potion_stall": ("hero3", "potion_stall", None),
    "pumpkin_lamp_lit": ("hero3", "pumpkin_lamp", True),
    "dead_tree": ("critters", "dead_tree", None),
    "tombstone": ("graveyard", "tombstone", None),
    "cauldron_lit": ("hero3", "cauldron", True),
    "jack_o_lantern_lit": ("hero3", "jack_o_lantern", True),
    "black_cat": ("critters", "black_cat", None),
    "candy_bucket": ("harvest", "candy_bucket", None),
    "pumpkin_pile": ("harvest", "pumpkin_pile", None),
    "witch_hat_stand": ("witchy", "witch_hat_stand", None),
    "crystal_ball": ("witchy", "crystal_ball", None),
}


def basis(cam):
    c = np.array(cam, float); c /= np.linalg.norm(c)
    fwd = -c
    right = np.cross(fwd, [0, 1, 0]); right /= np.linalg.norm(right)
    up = np.cross(right, fwd)
    return c, fwd, right, up


def _rot(e, pts):
    if "rotation" not in e:
        return pts
    r = e["rotation"]
    M = {"x": E._rx, "y": E._ry, "z": E._rz}[r["axis"]](r["angle"])
    o = np.array(r["origin"])
    return [M @ (p - o) + o for p in pts]


def visible_points(m, c):
    pts = []
    for e in m.elements:
        for f in e["faces"]:
            corners = _rot(e, [np.array(p, float) for p in E._face_corners(e, f)])
            n = E._NORMALS[f]
            if "rotation" in e:
                r = e["rotation"]
                n = {"x": E._rx, "y": E._ry, "z": E._rz}[r["axis"]](r["angle"]) @ n
            if len(e["faces"]) != 2 and np.dot(n, c) <= 0:
                continue
            pts += corners
    return np.array(pts)


def hull(pts):
    pts = sorted(set(map(tuple, np.round(pts, 4))))
    if len(pts) < 3:
        return pts
    cross = lambda o, a, b: (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    lo, up = [], []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0: lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(up) >= 2 and cross(up[-2], up[-1], p) <= 0: up.pop()
        up.append(p)
    return lo[:-1] + up[:-1]


def render_piece(m, frame=0):
    floor = min(0.0, min(min(e["from"][1], e["to"][1]) for e in m.elements), float(m.floor))
    c, fwd, right, up = basis(CAM)
    img = m.render(ppu=PPU, cam=CAM, frame=frame)
    pts = visible_points(m, c)
    minx, miny = (pts @ right).min(), (-(pts @ up)).min()
    to_px = lambda p: ((p @ right - minx) * PPU + 2, (-(p @ up) - miny) * PPU + 2)
    L = LIGHT / np.linalg.norm(LIGHT)
    polys = []
    for e in m.elements:
        a, b = np.array(e["from"], float), np.array(e["to"], float)
        cs = _rot(e, [np.array([x, y, z]) for x in (a[0], b[0]) for y in (a[1], b[1]) for z in (a[2], b[2])])
        proj = []
        for p in cs:
            g = p + L * ((p[1] - floor) / -L[1]); g[1] = floor
            proj.append(g)
        polys.append(hull(np.array([to_px(g) for g in proj])))
    allp = np.array([q for poly in polys for q in poly] + [(0, 0), (img.width, img.height)])
    ox, oy = -min(0, allp[:, 0].min()) + 4, -min(0, allp[:, 1].min()) + 4
    W = int(max(allp[:, 0].max(), img.width) + ox + 4)
    H = int(max(allp[:, 1].max(), img.height) + oy + 4)
    sh = Image.new("L", (W, H), 0); d = ImageDraw.Draw(sh)
    for poly in polys:
        if len(poly) >= 3:
            d.polygon([(x + ox, y + oy) for x, y in poly], fill=255)
    model = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    model.alpha_composite(img, (int(round(ox)), int(round(oy))))
    return model, sh


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "/home/claude/hollow/thumb/r"
    os.makedirs(out, exist_ok=True)
    for name, (mod, fn, lit) in PICKS.items():
        f = getattr(importlib.import_module(mod), fn)
        m = f(lit) if lit is not None else f()
        m.check()
        animated = m.is_animated()
        for k in range(E.NFRAMES if animated else 1):
            mi, sh = render_piece(m, frame=k)
            mi.save(f"{out}/{name}_f{k}.png")
            if k == 0:
                mi.save(f"{out}/{name}.png"); sh.save(f"{out}/{name}_shadow.png")
        print(name, mi.size, "animated" if animated else "")
