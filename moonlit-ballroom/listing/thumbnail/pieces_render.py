"""Render each Moonlit Ballroom piece Hibiscus-style: one camera, one scale, hard cast shadow.

Each output is an RGBA PNG plus a separate shadow mask (same canvas), so the composer can
tint the shadow to the floor colour. Shadows are real projections of every cube onto the
floor along one sun direction, so floating pieces get detached shadows.
"""
import math, sys, os, json
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, "/root/mb/moonlit-ballroom/src")
import engine as E
import pieces as P

CAM = (-0.55, 0.75, -1.0)          # a little more top-down than the cover, like the reference
LIGHT = np.array([-0.45, -1.5, 0.3])   # sun from the upper left: short shadows falling right
SS = 3                              # supersample, scaled down later for clean edges
PPU = 7 * SS

def basis(cam):
    c = np.array(cam, float); c /= np.linalg.norm(c)
    fwd = -c
    right = np.cross(fwd, [0, 1, 0]); right /= np.linalg.norm(right)
    up = np.cross(right, fwd)
    return c, fwd, right, up

def visible_points(m, c):
    pts = []
    for e in m.elements:
        for f in e["faces"]:
            corners = E._face_corners(e, f)
            if "rotation" in e:
                r = e["rotation"]
                M = {"x": E._rx, "y": E._ry, "z": E._rz}[r["axis"]](r["angle"])
                o = np.array(r["origin"])
                corners = [M @ (p - o) + o for p in corners]
                n = M @ E._NORMALS[f]
            else:
                n = E._NORMALS[f]
            if len(e["faces"]) != 2 and np.dot(n, c) <= 0:
                continue
            pts += corners
    return np.array(pts)

def box_corners(e):
    a, b = np.array(e["from"], float), np.array(e["to"], float)
    cs = [np.array([x, y, z]) for x in (a[0], b[0]) for y in (a[1], b[1]) for z in (a[2], b[2])]
    if "rotation" in e:
        r = e["rotation"]
        M = {"x": E._rx, "y": E._ry, "z": E._rz}[r["axis"]](r["angle"])
        o = np.array(r["origin"])
        cs = [M @ (p - o) + o for p in cs]
    return cs

def hull(pts):
    pts = sorted(set(map(tuple, np.round(pts, 4))))
    if len(pts) < 3:
        return pts
    def cross(o, a, b): return (a[0]-o[0])*(b[1]-o[1]) - (a[1]-o[1])*(b[0]-o[0])
    lo, up = [], []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0: lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(up) >= 2 and cross(up[-2], up[-1], p) <= 0: up.pop()
        up.append(p)
    return lo[:-1] + up[:-1]

def render_piece(m, frame=0, floor=0.0):
    c, fwd, right, up = basis(CAM)
    img = m.render(ppu=PPU, cam=CAM, frame=frame)
    pts = visible_points(m, c)
    minx, miny = (pts @ right).min(), (-(pts @ up)).min()
    to_px = lambda p: ((p @ right - minx) * PPU + 2, (-(p @ up) - miny) * PPU + 2)
    L = LIGHT / np.linalg.norm(LIGHT)
    polys, alphas = [], []
    for e in m.elements:
        cs = box_corners(e)
        proj = []
        for p in cs:
            t = (p[1] - floor) / -L[1]
            g = p + L * t
            g[1] = floor
            proj.append(g)
        scr = [to_px(g) for g in proj]
        polys.append(hull(np.array(scr)))
    # canvas big enough for model + shadow
    allp = np.array([q for poly in polys for q in poly] + [(0, 0), (img.width, img.height)])
    ox, oy = -min(0, allp[:, 0].min()) + 4, -min(0, allp[:, 1].min()) + 4
    W = int(max(allp[:, 0].max(), img.width) + ox + 4)
    H = int(max(allp[:, 1].max(), img.height) + oy + 4)
    sh = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(sh)
    for poly in polys:
        if len(poly) >= 3:
            d.polygon([(x + ox, y + oy) for x, y in poly], fill=255)
    model = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    model.alpha_composite(img, (int(round(ox)), int(round(oy))))
    # floor contact point in canvas px (centre of the footprint), for layout
    return model, sh

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "/root/thumb/r"
    os.makedirs(out, exist_ok=True)
    picks = {"waltzing_ghosts": P.waltzing_ghosts(), "ghost_piano": P.ghost_piano(),
             "floating_candelabra_lit": P.floating_candelabra(True), "ghost_lantern_lit": P.ghost_lantern(True),
             "ghost_portrait": P.ghost_portrait(), "wisp": P.wisp()}
    for name, m in picks.items():
        floor = min(min(e["from"][1], e["to"][1]) for e in m.elements)
        floor = min(floor, 0.0)
        for k in range(E.NFRAMES):                      # every animation frame (geometry is fixed, textures move)
            mod, sh = render_piece(m, frame=k, floor=floor)
            mod.save(f"{out}/{name}_f{k}.png")
            if k == 0:
                mod.save(f"{out}/{name}.png"); sh.save(f"{out}/{name}_shadow.png")
        print(name, mod.size, "floor", floor)
