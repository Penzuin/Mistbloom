"""Koi Garden piece cards, Hibiscus style (claude/brand/ICON_STYLE.md): one 1024 card per piece,
midnight-blue floor with two hard-edged light bands, the piece large with a hard sun shadow cast
texel by texel, its name in Minecraft Title Generator lettering (first word big, rest in small gold).
Moving pieces also get a GIF of their in-game loop.

usage: python3 cards.py <titles dir> <out dir> [--gif] [ids...]
"""
import math, os, sys
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
import arts, pieces, pack as P
from engine import face_point, turn
import render as R
import me

TDIR, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
S, SS = 1024, 3
FLOOR_MID, FLOOR_EDGE, BAND = np.array([70, 88, 146]), np.array([30, 38, 82]), np.array([98, 118, 178])
SHADOW, SHADOW_A = (18, 22, 56), 0.55
YAW, PITCH = 215, 30            # 3/4 view of the piece's front (fronts face -z)
BOX_W, BOX_H, BOX_BOTTOM = 640, 500, 640
NO_SHADOW = {'koi_wall_plaque', 'koi_lily_pads', 'koi_stepping_stones'}   # wall piece and flat floor pieces
WALL = {'koi_wall_plaque'}
GIF_FPS = 10

def words(title):
    w = title.split(' ', 1)
    return w[0].lower(), (w[1].lower() if len(w) > 1 else None)

# ------------------------------------------------------------------ geometry
def basis():
    a, p = math.radians(YAW), math.radians(PITCH)
    cdir = np.array([math.cos(p) * math.sin(a), math.sin(p), math.cos(p) * math.cos(a)])
    right = np.array([math.cos(a), 0, -math.sin(a)])
    return cdir, right, np.cross(cdir, right)

def still_quads(m):
    """world quads of a still model, entity space like the rigs (block centre at x=z=0)"""
    if not hasattr(m, 'atlas'): m.bake()
    out = []
    for e in m.els:
        for fc in e.faces():
            pts = [R._rot(face_point(fc, e.f, e.t, u, v), e.rot) for u, v in ((0, 0), (1, 0), (1, 1), (0, 1))]
            out.append((np.array(pts) - np.array([8, 0, 8]), e.uv[fc], 0))
    return out

def shadow_polys(quads, atlas, light, floor):
    """every opaque texel of every face projected onto the floor along the light"""
    L = np.array(light, float); L /= np.linalg.norm(L)
    polys = []
    for Pq, uv, _ in quads:
        x0, y0, x1, y1 = uv
        a = atlas[y0:y1, x0:x1, 3]
        H, W = a.shape
        if not H or not W: continue
        o, du, dv = Pq[0], Pq[1] - Pq[0], Pq[3] - Pq[0]
        for ty, tx in zip(*np.nonzero(a >= 128)):
            q = []
            for da, db in ((0, 0), (1, 0), (1, 1), (0, 1)):
                p = o + du * (tx + da) / W + dv * (ty + db) / H
                t = (p[1] - floor) / -L[1]
                g = p + L * t; g[1] = floor
                q.append(g)
            polys.append(np.array(q))
    return polys

def light_dir():
    cdir, right, up = basis()
    h = right * 0.45 - np.array([cdir[0], 0, cdir[2]]) * 0.3
    return (h[0], -1.5, h[2])            # sun from the upper left: shadows fall right and back

def draw(quads, atlas, ppu, floor, shadow=True, bounds=None):
    """model image + shadow mask in one frame; returns (model RGBA, shadow L, bounds)"""
    cdir, right, up = basis()
    polys = shadow_polys(quads, atlas, light_dir(), floor) if shadow else []
    if bounds is None:
        pts = np.concatenate([q[0] for q in quads] + polys) if polys else np.concatenate([q[0] for q in quads])
        xs, ys = pts @ right * ppu, -(pts @ up) * ppu
        bounds = (xs.min(), xs.max(), ys.min(), ys.max())
    pad = 8
    img = me.render_quads([(q[0], q[1]) for q in quads], atlas, YAW, PITCH, ppu, pad, bounds, ss=SS)
    sh = Image.new('L', img.size, 0); d = ImageDraw.Draw(sh)
    for q in polys:
        d.polygon([(float(p @ right * ppu - bounds[0] + pad), float(-(p @ up) * ppu - bounds[2] + pad)) for p in q], fill=255)
    return img, sh, bounds

# ------------------------------------------------------------------ pieces
def frames(iid):
    """list of (quads, atlas) for each GIF frame (one frame for still pieces) and the loop length"""
    _, src, title, lore, kind, extra = next(p for p in P.PIECES if p[0] == iid)
    if kind == 'me':
        rig, strip = P.bake_rig(*extra)
        n = max(1, int(round(rig.length * GIF_FPS)))
        S_ = rig.model.size
        out = []
        for k in range(n):
            t = k / GIF_FPS
            atlas = rig.model.atlas
            if strip is not None:
                f = int(t * 20 / P.WATER_TICKS) % P.WATER_FRAMES
                atlas = strip[f * S_:(f + 1) * S_]
            out.append(([(q[0], q[1], 0) for q in rig.posed(t)], atlas))
        return out, rig.length
    if kind == 'table':
        m, strip = P.table_strip()
        S_ = m.size
        qs = still_quads(m)
        n = int(P.TABLE_FRAMES * P.TABLE_TICKS / 20 * GIF_FPS)
        return [(qs, strip[(int(k / GIF_FPS * 20 / P.TABLE_TICKS) % P.TABLE_FRAMES) * S_:][:S_]) for k in range(n)], \
            P.TABLE_FRAMES * P.TABLE_TICKS / 20
    m = turn(P.STILL_MODEL[src]()); m.bake()
    return [(still_quads(m), m.atlas)], 0

def floor_of(quads):
    return min(q[0][:, 1].min() for q in quads)

def background():
    y, x = np.mgrid[0:S, 0:S].astype(float)
    d = np.sqrt(((x - S * 0.55) / S) ** 2 + ((y - S * 0.42) / S) ** 2)
    t = np.clip((d - 0.18) / 0.55, 0, 1)[..., None]
    img = FLOOR_MID * (1 - t) + FLOOR_EDGE * t
    k = y + (x - S / 2) * -0.22
    for lo, hi, a in ((260, 600, 0.30), (600, 650, 0.12)):
        m = ((k > lo) & (k < hi))[..., None]
        img = np.where(m, img * (1 - a) + BAND * a, img)
    return Image.fromarray(img.astype(np.uint8)).convert('RGBA')

def clean(img):
    a = np.array(img)
    lab, n = ndimage.label(a[..., 3] > 8)
    sizes = ndimage.sum(np.ones_like(lab), lab, range(1, n + 1))
    keep = np.isin(lab, [i + 1 for i, s in enumerate(sizes) if s > 2000])
    a[~keep] = 0
    im = Image.fromarray(a)
    return im.crop(im.getbbox())

def title_img(top, small, top_h=132, max_w=900):
    t = clean(Image.open(f'{TDIR}/t_{top}.png'))
    t = t.resize((round(t.width * top_h / t.height), top_h), Image.LANCZOS)
    if small:
        s = clean(Image.open(f'{TDIR}/s_{small.replace(" ", "_")}.png'))
        sh = round(top_h * 0.665)
        s = s.resize((round(s.width * sh / s.height), sh), Image.LANCZOS)
        ov = round(sh * 0.35)
        W = max(t.width, s.width)
        c = Image.new('RGBA', (W, t.height + s.height - ov), (0, 0, 0, 0))
        c.alpha_composite(t, ((W - t.width) // 2, 0))
        c.alpha_composite(s, ((W - s.width) // 2, t.height - ov))
        t = c
    if t.width > max_w:
        t = t.resize((max_w, round(t.height * max_w / t.width)), Image.LANCZOS)
    return t

def shadow_layer(sh):
    l = Image.new('RGBA', sh.size, SHADOW + (0,))
    l.putalpha(sh.point(lambda v: int(v * SHADOW_A)))
    return l

def cards(iid, gif=False):
    title = next(p for p in P.PIECES if p[0] == iid)[2]
    fr, length = frames(iid)
    q0, a0 = fr[0]
    floor = floor_of(q0)
    shadow = iid not in NO_SHADOW
    # one scale for the whole loop: fit the first frame into the box
    img, _, _ = draw(q0, a0, 10, floor, shadow=False)
    bb = img.getbbox()
    ppu = 10 * min(BOX_W / (bb[2] - bb[0]), BOX_H / (bb[3] - bb[1]))
    _, _, bounds = draw(q0, a0, ppu, floor, shadow)
    # widen the bounds so every frame of the loop fits
    cdir, right, up = basis()
    pts = np.concatenate([q[0] for f in fr[::max(1, len(fr) // 12)] for q in f[0]])
    xs, ys = pts @ right * ppu, -(pts @ up) * ppu
    bounds = (min(bounds[0], xs.min()), max(bounds[1], xs.max()), min(bounds[2], ys.min()), max(bounds[3], ys.max()))
    ttl = title_img(*words(title))
    out = []
    ref = None
    for quads, atlas in (fr if gif else fr[:1]):
        m, sh, _ = draw(quads, atlas, ppu, floor, shadow, bounds)
        if ref is None:
            ref = m.getbbox()
            x = round(S / 2 - (ref[0] + ref[2]) / 2); y = round(BOX_BOTTOM - ref[3])
        c = background()
        if shadow:
            c.alpha_composite(shadow_layer(sh), (x, y))
        c.alpha_composite(m, (x, y))
        c.alpha_composite(ttl, ((S - ttl.width) // 2, S - ttl.height - 46))
        out.append(c.convert('RGB'))
    return out

def save_gif(frames_rgb, path, size=512):
    frames_rgb = [f.resize((size, size), Image.LANCZOS) for f in frames_rgb]
    strip = Image.new('RGB', (size, size * len(frames_rgb)))
    for k, f in enumerate(frames_rgb): strip.paste(f, (0, size * k))
    pal = strip.quantize(colors=256, method=Image.Quantize.MEDIANCUT)
    g = [f.quantize(palette=pal, dither=Image.Dither.FLOYDSTEINBERG) for f in frames_rgb]   # dither the floor gradient; still pixels are locked below
    base_rgb, base_idx = np.array(frames_rgb[0]).astype(int), np.array(g[0])
    for k in range(1, len(g)):                      # unchanged pixels keep frame 0's index: no shimmer
        same = np.abs(np.array(frames_rgb[k]).astype(int) - base_rgb).sum(2) == 0
        idx = np.array(g[k]); idx[same] = base_idx[same]
        im = Image.fromarray(idx, 'P'); im.putpalette(g[0].getpalette()); g[k] = im
    g[0].save(path, save_all=True, append_images=g[1:], duration=int(1000 / GIF_FPS), loop=0, optimize=False, disposal=1)

if __name__ == '__main__':
    gif = '--gif' in sys.argv
    only = [a for a in sys.argv[3:] if not a.startswith('--')]
    for i, p in enumerate(P.PIECES, 1):
        iid, kind = p[0], p[4]
        if only and iid not in only: continue
        base = f'{OUT}/koi-garden-{i:02d}-{iid.replace("koi_", "").replace("_", "-")}'
        moving = kind != 'still'
        fr = cards(iid, gif and moving)
        fr[0].save(base + '.png')
        if gif and moving:
            save_gif(fr, base + '.gif')
        print(base, 'gif' if gif and moving else '')
