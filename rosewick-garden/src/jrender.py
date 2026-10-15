"""Render raw Minecraft JSON block/item models (elements + textures) with a z-buffer.
render(model_path, assets_root, cam=(-1,0.8,-1.2), ppu=12, tint=None, frame=0) -> RGBA PIL image"""
import json, math, os
import numpy as np
from PIL import Image

NORM = {"north": (0,0,-1), "south": (0,0,1), "east": (1,0,0), "west": (-1,0,0), "up": (0,1,0), "down": (0,-1,0)}
SHADE = {"up": 1.0, "down": 0.5, "north": 0.8, "south": 0.8, "east": 0.6, "west": 0.6}

def corners(f, t, face):
    x0,y0,z0 = f; x1,y1,z1 = t
    # order: top-left, top-right, bottom-right, bottom-left as seen from outside (MC uv convention)
    return {
     "north": [(x1,y1,z0),(x0,y1,z0),(x0,y0,z0),(x1,y0,z0)],
     "south": [(x0,y1,z1),(x1,y1,z1),(x1,y0,z1),(x0,y0,z1)],
     "west":  [(x0,y1,z0),(x0,y1,z1),(x0,y0,z1),(x0,y0,z0)],
     "east":  [(x1,y1,z1),(x1,y1,z0),(x1,y0,z0),(x1,y0,z1)],
     "up":    [(x0,y1,z0),(x1,y1,z0),(x1,y1,z1),(x0,y1,z1)],
     "down":  [(x0,y0,z1),(x1,y0,z1),(x1,y0,z0),(x0,y0,z0)],
    }[face]

def rotm(axis, ang):
    a = math.radians(ang); c, s = math.cos(a), math.sin(a)
    if axis == "x": return np.array([[1,0,0],[0,c,-s],[0,s,c]])
    if axis == "y": return np.array([[c,0,s],[0,1,0],[-s,0,c]])
    return np.array([[c,-s,0],[s,c,0],[0,0,1]])

def load_tex(assets, ref, frame=0):
    ns, p = ref.split(":") if ":" in ref else ("minecraft", ref)
    im = Image.open(os.path.join(assets, ns, "textures", p + ".png")).convert("RGBA")
    w, h = im.size
    if h > w:
        n = h // w; im = im.crop((0, (frame % n) * w, w, (frame % n) * w + w))
    return np.asarray(im).astype(float) / 255

def render(path, assets, cam=(-1, 0.8, -1.2), ppu=12, tint=None, frame=0, bg=None):
    m = json.load(open(path))
    texs = {k: v for k, v in m["textures"].items()}
    cache = {}
    def tex(key):
        ref = key.lstrip("#")
        while ref in texs: ref = texs[ref].lstrip("#") if texs[ref].startswith("#") else texs[ref]
        if ref not in cache: cache[ref] = load_tex(assets, ref, frame)
        return cache[ref]
    c = np.array(cam, float); c /= np.linalg.norm(c)
    right = np.cross([0,1,0], c); right /= np.linalg.norm(right)
    up = np.cross(c, right)
    quads = []
    for e in m["elements"]:
        R = None
        if "rotation" in e:
            r = e["rotation"]; R = rotm(r["axis"], r["angle"]); o = np.array(r["origin"], float)
        for fn, fc in e["faces"].items():
            cs = [np.array(p, float) for p in corners(e["from"], e["to"], fn)]
            n = np.array(NORM[fn], float)
            if R is not None:
                cs = [R @ (p - o) + o for p in cs]; n = R @ n
            uv = fc.get("uv")
            if uv is None:
                continue
            quads.append((cs, n, uv, fc.get("rotation", 0), tex(fc["texture"]), fn, fc.get("tintindex")))
    allp = np.array([p for q in quads for p in q[0]])
    P = lambda p: np.array([np.dot(p, right), np.dot(p, up), np.dot(p, c)])
    proj = np.array([P(p) for p in allp])
    mn, mx = proj.min(0), proj.max(0)
    W = int((mx[0]-mn[0]) * ppu) + 8; H = int((mx[1]-mn[1]) * ppu) + 8
    img = np.zeros((H, W, 4)); zb = np.full((H, W), -1e9)
    for cs, n, uv, rot, T, fn, ti in quads:
        facing = np.dot(n, c)
        pc = [P(p) for p in cs]
        sx = [(q[0]-mn[0]) * ppu + 4 for q in pc]; sy = [(mx[1]-q[1]) * ppu + 4 for q in pc]
        x0, x1 = int(max(0, math.floor(min(sx)))), int(min(W-1, math.ceil(max(sx))))
        y0, y1 = int(max(0, math.floor(min(sy)))), int(min(H-1, math.ceil(max(sy))))
        if x1 < x0 or y1 < y0: continue
        A = np.array([sx[0], sy[0]]); U = np.array([sx[1]-sx[0], sy[1]-sy[0]]); V = np.array([sx[3]-sx[0], sy[3]-sy[0]])
        M = np.array([U, V]).T
        if abs(np.linalg.det(M)) < 1e-6: continue
        Mi = np.linalg.inv(M)
        ys, xs = np.mgrid[y0:y1+1, x0:x1+1]
        d = np.stack([xs + 0.5 - A[0], ys + 0.5 - A[1]], -1)
        st = d @ Mi.T
        s, t = st[..., 0], st[..., 1]
        inside = (s >= 0) & (s <= 1) & (t >= 0) & (t <= 1)
        if not inside.any(): continue
        z0 = pc[0][2]; zU = pc[1][2]-z0; zV = pc[3][2]-z0
        z = z0 + s * zU + t * zV
        # uv rotation
        for _ in range((rot // 90) % 4):
            s, t = t, 1 - s
        h, w = T.shape[:2]
        u = uv[0] + (uv[2]-uv[0]) * s; v = uv[1] + (uv[3]-uv[1]) * t
        px = np.clip((u / 16 * w).astype(int), 0, w-1); py = np.clip((v / 16 * h).astype(int), 0, h-1)
        col = T[py, px]
        ok = inside & (col[..., 3] > 0.1) & (z > zb[y0:y1+1, x0:x1+1] - 1e-4)
        if facing <= 0 and not (fn in ("north","south","east","west","up","down")):
            pass
        if facing < -1e-6:
            # back face: MC culls back faces of elements
            continue
        rgb = col[..., :3] * SHADE.get(fn, 0.8)
        if ti is not None and tint is not None:
            rgb = rgb * np.array(tint) / 255
        sub = img[y0:y1+1, x0:x1+1]; zsub = zb[y0:y1+1, x0:x1+1]
        sub[ok, :3] = rgb[ok]; sub[ok, 3] = 1; zsub[ok] = z[ok]
    out = Image.fromarray((img * 255).astype(np.uint8), "RGBA")
    if bg:
        b = Image.new("RGBA", out.size, bg); b.alpha_composite(out); out = b
    return out
