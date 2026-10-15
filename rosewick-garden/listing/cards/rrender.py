"""Rosewick card renderer: raw Minecraft JSON models -> supersampled RGBA render + texel-exact hard floor shadow
(every opaque texel projected onto the floor along LIGHT, same screen frame as the model)."""
import json, math, os, sys
import numpy as np
from PIL import Image
sys.path.insert(0, "/home/claude/rosewick/tools")
from jrender import corners, rotm, NORM, load_tex

CAM = (-0.55, 0.75, -1.0)
LIGHT = np.array([-0.45, -1.5, 0.3])
SHADE = {"up": 1.0, "down": 0.55, "north": 0.86, "south": 0.86, "east": 0.7, "west": 0.7}

def quads(path, assets, frame):
    m = json.load(open(path)); texs = m["textures"]; cache = {}
    def tex(key):
        ref = key.lstrip("#")
        while ref in texs: ref = texs[ref].lstrip("#") if texs[ref].startswith("#") else texs[ref]
        if ref not in cache: cache[ref] = load_tex(assets, ref, frame)
        return cache[ref]
    out = []
    for e in m["elements"]:
        R = None
        if "rotation" in e:
            r = e["rotation"]; R = rotm(r["axis"], r["angle"]); o = np.array(r["origin"], float)
        for fn, fc in e["faces"].items():
            cs = [np.array(p, float) for p in corners(e["from"], e["to"], fn)]; n = np.array(NORM[fn], float)
            if R is not None: cs = [R @ (p - o) + o for p in cs]; n = R @ n
            out.append((cs, n, fc["uv"], fc.get("rotation", 0), tex(fc["texture"]), fn, fc.get("tintindex") is not None))
    return out

def _raster(img, zb, cs2, z3, T, uv, rot, shade, tint, mask_only=False, layer='opaque'):
    H, W = (zb.shape if zb is not None else img.shape[:2])
    sx = [p[0] for p in cs2]; sy = [p[1] for p in cs2]
    x0, x1 = max(0, int(math.floor(min(sx)))), min(W - 1, int(math.ceil(max(sx))))
    y0, y1 = max(0, int(math.floor(min(sy)))), min(H - 1, int(math.ceil(max(sy))))
    if x1 < x0 or y1 < y0: return
    A = np.array(cs2[0]); M = np.array([np.array(cs2[1]) - A, np.array(cs2[3]) - A]).T
    if abs(np.linalg.det(M)) < 1e-9: return
    Mi = np.linalg.inv(M)
    ys, xs = np.mgrid[y0:y1 + 1, x0:x1 + 1]
    st = np.stack([xs + 0.5 - A[0], ys + 0.5 - A[1]], -1) @ Mi.T
    s, t = st[..., 0], st[..., 1]
    inside = (s >= -1e-6) & (s <= 1 + 1e-6) & (t >= -1e-6) & (t <= 1 + 1e-6)
    if not inside.any(): return
    ss, tt = s, t
    for _ in range((rot // 90) % 4): ss, tt = tt, 1 - ss
    h, w = T.shape[:2]
    u = uv[0] + (uv[2] - uv[0]) * ss; v = uv[1] + (uv[3] - uv[1]) * tt
    px = np.clip(np.floor(u / 16 * w + 1e-6).astype(int), 0, w - 1); py = np.clip(np.floor(v / 16 * h + 1e-6).astype(int), 0, h - 1)
    col = T[py, px]
    ok = inside & (col[..., 3] > 0.1)
    if mask_only:
        img[y0:y1 + 1, x0:x1 + 1][ok] = 1.0; return
    z = z3[0] + s * (z3[1] - z3[0]) + t * (z3[3] - z3[0])
    zs = zb[y0:y1 + 1, x0:x1 + 1]; ok &= z > zs - 1e-4
    a = col[..., 3]
    ok &= (a >= 0.99) if layer == 'opaque' else (a < 0.99)
    rgb = col[..., :3] * shade
    if tint is not None: rgb = rgb * np.array(tint) / 255
    sub = img[y0:y1 + 1, x0:x1 + 1]
    if layer == 'opaque':
        sub[ok, :3] = rgb[ok]; sub[ok, 3] = 1; zs[ok] = z[ok]
    else:
        al = a[ok][:, None]
        sub[ok, :3] = sub[ok, :3] * sub[ok, 3:4] * (1 - al) + rgb[ok] * al
        na = al[:, 0] + sub[ok, 3] * (1 - al[:, 0])
        sub[ok, :3] = sub[ok, :3] / np.maximum(na[:, None], 1e-6); sub[ok, 3] = na

def render(path, assets, ppu=24, frame=0, tint=None, shadow=True, cam=CAM, light=LIGHT):
    q = quads(path, assets, frame)
    c = np.array(cam, float); c /= np.linalg.norm(c)
    right = np.cross([0, 1, 0], c); right /= np.linalg.norm(right); up = np.cross(c, right)
    floor = min(0.0, min(p[1] for cs, *_ in q for p in cs))
    L = np.array(light, float); L /= np.linalg.norm(L)
    proj = lambda p: (p @ right * ppu, -(p @ up) * ppu, p @ c)
    floorpt = lambda p: np.array([p[0] + L[0] * (p[1] - floor) / -L[1], floor, p[2] + L[2] * (p[1] - floor) / -L[1]])
    pts = [p for cs, *_ in q for p in cs]
    if shadow: pts += [floorpt(p) for p in pts]
    P = np.array([proj(p)[:2] for p in pts]); mn = P.min(0) - 6; mx = P.max(0) + 6
    W, H = int(mx[0] - mn[0]), int(mx[1] - mn[1])
    img = np.zeros((H, W, 4)); zb = np.full((H, W), -1e9); sh = np.zeros((H, W, 1))
    for cs, n, uv, rot, T, fn, tinted in q:
        if shadow:
            _raster(sh, None, [np.array(proj(floorpt(p))[:2]) - mn for p in cs], None, T, uv, rot, 1, None, mask_only=True)
    vis = [x for x in q if np.dot(x[1], c) > 1e-6]
    for layer, faces in (("opaque", vis), ("translucent", sorted(vis, key=lambda x: np.mean([p @ c for p in x[0]])))):
        for cs, n, uv, rot, T, fn, tinted in faces:
            pr = [proj(p) for p in cs]
            _raster(img, zb, [np.array(p[:2]) - mn for p in pr], [p[2] for p in pr], T, uv, rot, SHADE.get(fn, 0.8),
                    tint if tinted else None, layer=layer)
    model = Image.fromarray((img * 255).astype(np.uint8), "RGBA")
    shadow_im = Image.fromarray((sh[..., 0] * 255).astype(np.uint8), "L")
    return model, shadow_im
