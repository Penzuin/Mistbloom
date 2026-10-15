"""Depth-buffered orthographic preview renderer for engine.Model (translucency aware)."""
import math
import numpy as np
from PIL import Image, ImageFilter
from engine import face_point

def _rot(p, rot):
    if not rot: return p
    ax, ang, org = rot
    a = math.radians(ang)
    ca, sa = math.cos(a), math.sin(a)
    x, y, z = p[0] - org[0], p[1] - org[1], p[2] - org[2]
    if ax == 'x': y, z = y * ca - z * sa, y * sa + z * ca
    elif ax == 'y': x, z = x * ca + z * sa, -x * sa + z * ca
    else: x, y = x * ca - y * sa, x * sa + y * ca
    return (x + org[0], y + org[1], z + org[2])

def render(model, yaw=35, pitch=28, scale=12, ss=2, centre=None, pad=10):
    if not hasattr(model, 'atlas'): model.bake()
    tex = model.atlas.astype(float)
    a, p = math.radians(yaw), math.radians(pitch)
    cdir = np.array([math.cos(p) * math.sin(a), math.sin(p), math.cos(p) * math.cos(a)])
    right = np.array([math.cos(a), 0, -math.sin(a)])
    up = np.cross(cdir, right)
    s = scale * ss
    quads = []
    for e in model.els:
        for fc in e.faces():
            pts = [_rot(face_point(fc, e.f, e.t, u, v), e.rot) for u, v in ((0, 0), (1, 0), (1, 1), (0, 1))]
            P = np.array(pts) - np.array(centre or (8, 8, 8))
            sx = P @ right * s; sy = -(P @ up) * s; d = P @ cdir
            quads.append((sx, sy, d, e.uv[fc]))
    allx = np.concatenate([q[0] for q in quads]); ally = np.concatenate([q[1] for q in quads])
    ox, oy = -allx.min() + pad * ss, -ally.min() + pad * ss
    W = int(allx.max() - allx.min() + 2 * pad * ss) + 1
    H = int(ally.max() - ally.min() + 2 * pad * ss) + 1
    img = np.zeros((H, W, 4)); zb = np.full((H, W), -1e9)
    trans = []
    for sx, sy, d, uv in quads:
        sx = sx + ox; sy = sy + oy
        uvp = [(0, 0), (1, 0), (1, 1), (0, 1)]
        for tri in ((0, 1, 2), (0, 2, 3)):
            X = sx[list(tri)]; Y = sy[list(tri)]; D = d[list(tri)]
            UV = np.array([uvp[i] for i in tri], float)
            x0, x1 = int(max(0, math.floor(X.min()))), int(min(W - 1, math.ceil(X.max())))
            y0, y1 = int(max(0, math.floor(Y.min()))), int(min(H - 1, math.ceil(Y.max())))
            if x1 < x0 or y1 < y0: continue
            den = (Y[1] - Y[2]) * (X[0] - X[2]) + (X[2] - X[1]) * (Y[0] - Y[2])
            if abs(den) < 1e-9: continue
            yy, xx = np.mgrid[y0:y1 + 1, x0:x1 + 1] + 0.5
            l0 = ((Y[1] - Y[2]) * (xx - X[2]) + (X[2] - X[1]) * (yy - Y[2])) / den
            l1 = ((Y[2] - Y[0]) * (xx - X[2]) + (X[0] - X[2]) * (yy - Y[2])) / den
            l2 = 1 - l0 - l1
            m = (l0 >= -1e-6) & (l1 >= -1e-6) & (l2 >= -1e-6)
            if not m.any(): continue
            z = l0 * D[0] + l1 * D[1] + l2 * D[2]
            fu = l0 * UV[0, 0] + l1 * UV[1, 0] + l2 * UV[2, 0]
            fv = l0 * UV[0, 1] + l1 * UV[1, 1] + l2 * UV[2, 1]
            u0, v0, u1, v1 = uv
            px = np.clip((u0 + fu * (u1 - u0)).astype(int), u0, u1 - 1)
            py = np.clip((v0 + fv * (v1 - v0)).astype(int), v0, v1 - 1)
            col = tex[py, px]
            al = col[..., 3]
            sub = (slice(y0, y1 + 1), slice(x0, x1 + 1))
            opaque = m & (al >= 250) & (z > zb[sub])
            img[sub][opaque] = col[opaque]
            zb[sub][opaque] = z[opaque]
            semi = m & (al > 8) & (al < 250)
            if semi.any():
                trans.append((float(D.mean()), sub, semi, z, col))
    trans.sort(key=lambda t: t[0])
    for _, sub, semi, z, col in trans:
        vis = semi & (z > zb[sub])
        a_ = col[..., 3:4] / 255.0
        dst = img[sub]
        blended = dst.copy()
        blended[..., :3] = dst[..., :3] * (1 - a_) + col[..., :3] * a_
        blended[..., 3] = np.maximum(dst[..., 3], col[..., 3] + dst[..., 3] * (1 - a_[..., 0]))
        dst[vis] = blended[vis]
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), 'RGBA')
    if ss > 1:
        im = im.resize((W // ss, H // ss), Image.BOX)
    return im

def on_bg(im, bg=(198, 198, 198)):
    b = Image.new('RGBA', im.size, bg + (255,))
    b.alpha_composite(im)
    return b
