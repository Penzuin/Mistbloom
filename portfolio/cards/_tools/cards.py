"""Hibiscus-style piece cards for Frostlight Night Market and Nightbloom Nook (Carrd gallery).

One camera, texel-by-texel hard sun shadow, midnight blue floor with two light bands,
Minecraft Title Generator lettering (lavender top word, gold small word).

usage: python3 cards.py frost|nook <titles dir> <out dir>
"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
PACK, TDIR, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
sys.path.insert(0, os.path.join(HERE, PACK))
import engine as E
os.makedirs(OUT, exist_ok=True)

if PACK == "frost":
    import pieces as P1, pieces2 as P2
    PIECES = {
        "market_stall":    (lambda: P1.market_stall("market_stall_red"), ("market", "stall")),
        "cocoa_cart":      (P1.cocoa_cart, ("cocoa", "cart")),
        "festive_pine":    (P1.festive_pine, ("festive", "pine")),
        "lantern_post":    (lambda: P1.lantern_post(True), ("lantern", "post")),
        "snowman":         (P1.snowman, ("snowman", None)),
    }
    PREFIX = "frostlight"
    TICKS = E.FRAMETIMES
else:
    import pieces as P1
    PIECES = {
        "moonfire_hearth": (lambda: P1.moonfire_hearth(True), ("moonfire", "hearth")),
        "moon_daybed":     (P1.moon_daybed, ("moon", "daybed")),
        "reading_armchair": (P1.reading_armchair, ("reading", "armchair")),
        "tall_bookshelf":  (P1.tall_bookshelf, ("tall", "bookshelf")),
        "floor_lamp":      (lambda: P1.floor_lamp(True), ("floor", "lamp")),
    }
    PREFIX = "nightbloom-nook"
    TICKS = E.FRAMETIMES

S, SS = 1024, 3
CAM = (-0.55, 0.75, -1.0)
LIGHT = (-0.45, -1.5, 0.3)
FLOOR_MID = np.array([70, 88, 146])
FLOOR_EDGE = np.array([30, 38, 82])
BAND = np.array([98, 118, 178])
SHADOW = (18, 22, 56)
SHADOW_A = 0.55
BOX_W, BOX_H, BOX_BOTTOM = 640, 500, 640


def basis(cam):
    c = np.array(cam, float); c /= np.linalg.norm(c)
    fwd = -c
    right = np.cross(fwd, [0, 1, 0]); right /= np.linalg.norm(right)
    up = np.cross(right, fwd)
    return c, fwd, right, up


def corners(e, f):
    cs = [np.array(p, float) for p in E._face_corners(e, f)]
    if "rotation" in e:
        r = e["rotation"]
        M = {"x": E._rx, "y": E._ry, "z": E._rz}[r["axis"]](r["angle"])
        o = np.array(r["origin"])
        cs = [M @ (p - o) + o for p in cs]
    return cs


def visible_points(m, c):
    pts = []
    for e in m.elements:
        for f in e["faces"]:
            n = E._NORMALS[f]
            if "rotation" in e:
                r = e["rotation"]
                n = {"x": E._rx, "y": E._ry, "z": E._rz}[r["axis"]](r["angle"]) @ n
            if len(e["faces"]) != 2 and np.dot(n, c) <= 0:
                continue
            pts += corners(e, f)
    return np.array(pts)


def render_piece(m, frame, ppu):
    c, fwd, right, up = basis(CAM)
    img = m.render(ppu=ppu, cam=CAM, frame=frame)
    pts = visible_points(m, c)
    minx, miny = (pts @ right).min(), (-(pts @ up)).min()
    to_px = lambda p: ((p @ right - minx) * ppu + 2, (-(p @ up) - miny) * ppu + 2)
    floor = min(min(e["from"][1], e["to"][1]) for e in m.elements)
    L = np.array(LIGHT, float); L /= np.linalg.norm(L)
    quads = []
    for i, e in enumerate(m.elements):
        for f in e["faces"]:
            cs = corners(e, f)
            u1, v1, u2, v2 = m.uv[(i, f)]
            a = m.atlas[v1:v2, u1:u2, 3]
            H, W = a.shape
            for ty in range(H):
                for tx in range(W):
                    if a[ty, tx] < 128:
                        continue
                    q = []
                    for da, db in ((0, 0), (1, 0), (1, 1), (0, 1)):
                        p = cs[0] + (tx + da) / W * (cs[1] - cs[0]) + (ty + db) / H * (cs[3] - cs[0])
                        g = p + L * ((p[1] - floor) / -L[1]); g[1] = floor
                        q.append(to_px(g))
                    quads.append(q)
    allp = np.array([p for q in quads for p in q] + [(0, 0), (img.width, img.height)])
    ox, oy = -min(0, allp[:, 0].min()) + 4, -min(0, allp[:, 1].min()) + 4
    Wc = int(max(allp[:, 0].max(), img.width) + ox + 4)
    Hc = int(max(allp[:, 1].max(), img.height) + oy + 4)
    sh = Image.new("L", (Wc, Hc), 0)
    d = ImageDraw.Draw(sh)
    for q in quads:
        d.polygon([(x + ox, y + oy) for x, y in q], fill=255)
    out = Image.new("RGBA", (Wc, Hc), (0, 0, 0, 0))
    out.alpha_composite(img, (int(round(ox)), int(round(oy))))
    return out, sh


def render(key, ppu):
    m = PIECES[key][0]()
    n = E.NFRAMES if m.is_animated() else 1
    frames, sh = [], None
    for f in range(n):
        im, s = render_piece(m, f, ppu * SS)
        frames.append(im); sh = sh or s
    small = lambda im: im.resize((round(im.width / SS), round(im.height / SS)), Image.LANCZOS)
    return [small(f) for f in frames], small(sh)


def background():
    y, x = np.mgrid[0:S, 0:S].astype(float)
    d = np.sqrt(((x - S * 0.55) / S) ** 2 + ((y - S * 0.42) / S) ** 2)
    t = np.clip((d - 0.18) / 0.55, 0, 1)[..., None]
    img = FLOOR_MID * (1 - t) + FLOOR_EDGE * t
    k = y + (x - S / 2) * -0.22
    for lo, hi, a in ((260, 600, 0.30), (600, 650, 0.12)):
        msk = ((k > lo) & (k < hi))[..., None]
        img = np.where(msk, img * (1 - a) + BAND * a, img)
    return Image.fromarray(img.astype(np.uint8)).convert("RGBA")


def clean(img):
    a = np.array(img)
    lab, n = ndimage.label(a[..., 3] > 8)
    sizes = ndimage.sum(np.ones_like(lab), lab, range(1, n + 1))
    keep = np.isin(lab, [i + 1 for i, s in enumerate(sizes) if s > 5000])
    a[~keep] = 0
    im = Image.fromarray(a)
    return im.crop(im.getbbox())


def title(top, small, top_h=132):
    t = clean(Image.open(f"{TDIR}/t_{top}.png"))
    t = t.resize((round(t.width * top_h / t.height), top_h), Image.LANCZOS)
    if t.width > 820:
        t = t.resize((820, round(t.height * 820 / t.width)), Image.LANCZOS)
    if not small:
        return t
    s = clean(Image.open(f"{TDIR}/s_{small}.png"))
    sh = round(top_h * 0.665)
    s = s.resize((round(s.width * sh / s.height), sh), Image.LANCZOS)
    ov = round(sh * 0.35)
    W = max(t.width, s.width)
    c = Image.new("RGBA", (W, t.height + s.height - ov), (0, 0, 0, 0))
    c.alpha_composite(t, ((W - t.width) // 2, 0))
    c.alpha_composite(s, ((W - s.width) // 2, t.height - ov))
    return c


def shadow_layer(sh):
    l = Image.new("RGBA", sh.size, SHADOW + (0,))
    l.putalpha(sh.point(lambda v: int(v * SHADOW_A)))
    return l


_cache = {}


def card(key, f=0):
    if key not in _cache:
        fr, _ = render(key, 5)
        bb = fr[0].getbbox()
        ppu = 5 * min(BOX_W / (bb[2] - bb[0]), BOX_H / (bb[3] - bb[1]))
        _cache[key] = render(key, ppu)
    frames, sh = _cache[key]
    img = background()
    bb = frames[0].getbbox()
    x = round(S / 2 - (bb[0] + bb[2]) / 2)
    y = round(BOX_BOTTOM - bb[3])
    img.alpha_composite(shadow_layer(sh), (x, y))
    img.alpha_composite(frames[f % len(frames)], (x, y))
    t = title(*PIECES[key][1])
    img.alpha_composite(t, ((S - t.width) // 2, S - t.height - 46))
    return img.convert("RGB")


def gif(frames_rgb, path, ms):
    strip = Image.new("RGB", (S, S * len(frames_rgb)))
    for k, fr in enumerate(frames_rgb):
        strip.paste(fr, (0, S * k))
    pal = strip.quantize(colors=256, method=Image.Quantize.MEDIANCUT)
    g = [fr.quantize(palette=pal, dither=Image.Dither.FLOYDSTEINBERG) for fr in frames_rgb]
    base_rgb, base_idx = np.array(frames_rgb[0]).astype(int), np.array(g[0])
    for k in range(1, len(g)):
        same = np.abs(np.array(frames_rgb[k]).astype(int) - base_rgb).sum(2) == 0
        idx = np.array(g[k]); idx[same] = base_idx[same]
        im = Image.fromarray(idx, "P"); im.putpalette(g[0].getpalette()); g[k] = im
    g[0].save(path, save_all=True, append_images=g[1:], duration=ms, loop=0, optimize=False, disposal=1)


if __name__ == "__main__":
    only = sys.argv[4:] or list(PIECES)
    for n, key in enumerate(PIECES, 1):
        if key not in only:
            continue
        name = f"{OUT}/{PREFIX}-{n}-{key.replace('_', '-')}"
        c0 = card(key)
        c0.save(name + ".png")
        c0.save(name + ".jpg", quality=90)
        if len(_cache[key][0]) > 1:
            gif([card(key, k) for k in range(E.NFRAMES)], name + ".gif", [t * 50 for t in TICKS])
        print(key, "done", flush=True)
