"""Witching Hour store icon + piece icons, Hibiscus style (see claude/brand/ICON_STYLE.md).

Every cosmetic rendered on its own at one camera and one scale, hard sun shadow tinted from the
floor (none under floating pieces), midnight blue floor with two hard-edged light bands, blocky
Minecraft Title Generator title at the bottom (lavender word, gold small word).

usage (from this folder): python3 icons.py <titles dir> <out dir> [--animate]
"""
import os, sys, copy
import numpy as np
from PIL import Image
from scipy import ndimage

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "src"))
sys.path.insert(0, "/root/mb/moonlit-ballroom/listing/thumbnail")
import engine as E                      # Witching Hour engine
import pieces as P
import pieces_render as PR              # one-camera render + shadow projection (Moonlit icon tooling)
PR.E = E                                # use the Witching Hour engine's geometry helpers

TDIR, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
S, SS = 1024, 3

FLOOR_MID = np.array([70, 88, 146])     # midnight blue floor (the purple hat vanished on plum)
FLOOR_EDGE = np.array([30, 38, 82])     # deeper towards the corners
BAND = np.array([98, 118, 178])         # moonlight band
SHADOW = (18, 22, 56)
SHADOW_A = 0.55

BY = {k: mk for k, t, s, l, mk in P.PIECES}
FLOATS = {"wisp"}                        # floating pieces get no shadow
BACK_VIEW = {"moonlit_broom"}           # worn on the back: show it from behind, like on the player
NAMES = {"witch_hat": ("witch", "hat"), "candle_crown": ("candle", "crown"),
         "ghostlight_lantern": ("ghostlight", "lantern"), "grimoire": ("moon", "grimoire"),
         "wisp": ("wisp", None), "moonlit_broom": ("moonlit", "broom")}
FILES = {"witch_hat": "1-witch-hat", "candle_crown": "2-candle-crown", "ghostlight_lantern": "3-ghostlight-lantern",
         "grimoire": "4-moon-grimoire", "wisp": "5-wisp", "moonlit_broom": "6-moonlit-broom"}


def model(key):
    m = BY[key]()
    if key == "grimoire":
        m.elements = [e for e in m.elements if e.get("name") not in ("belt", "belt_strap")]
    m.scale = 1.0                        # shape only; the head-display scale isn't part of the look
    return m


def background():
    y, x = np.mgrid[0:S, 0:S].astype(float)
    d = np.sqrt(((x - S * 0.55) / S) ** 2 + ((y - S * 0.42) / S) ** 2)
    t = np.clip((d - 0.18) / 0.55, 0, 1)[..., None]
    img = FLOOR_MID * (1 - t) + FLOOR_EDGE * t
    k = y + (x - S / 2) * -0.22
    for lo, hi, a in ((260, 600, 0.30), (600, 650, 0.12)):
        m = ((k > lo) & (k < hi))[..., None]
        img = np.where(m, img * (1 - a) + BAND * a, img)
    return Image.fromarray(img.astype(np.uint8)).convert("RGBA")


def render_piece(m, frame, floor, cam, light):
    """model render + a hard shadow cast texel by texel (transparent texels cast nothing),
    in the same canvas frame as pieces_render.render_piece"""
    from PIL import ImageDraw
    c, fwd, right, up = PR.basis(cam)
    img = m.render(ppu=PR.PPU, cam=cam, frame=frame)
    m.bake(frame)
    pts = PR.visible_points(m, c)
    minx, miny = (pts @ right).min(), (-(pts @ up)).min()
    to_px = lambda p: ((p @ right - minx) * PR.PPU + 2, (-(p @ up) - miny) * PR.PPU + 2)
    L = np.array(light, float); L /= np.linalg.norm(L)
    quads = []
    for i, e in enumerate(m.elements):
        for f in e["faces"]:
            cs = [np.array(p, float) for p in E._face_corners(e, f)]
            if "rotation" in e:
                r = e["rotation"]
                Mx = {"x": E._rx, "y": E._ry, "z": E._rz}[r["axis"]](r["angle"])
                o = np.array(r["origin"])
                cs = [Mx @ (p - o) + o for p in cs]
            u1, v1, u2, v2 = m.uv[(i, f)]
            a = m.atlas[v1:v2, u1:u2, 3]
            H, W = a.shape
            for ty in range(H):
                for tx in range(W):
                    if a[ty, tx] < 128:
                        continue
                    q = []
                    for (da, db) in ((0, 0), (1, 0), (1, 1), (0, 1)):
                        aa, bb = (tx + da) / W, (ty + db) / H
                        p = cs[0] + aa * (cs[1] - cs[0]) + bb * (cs[3] - cs[0])
                        t = (p[1] - floor) / -L[1]
                        g = p + L * t
                        g[1] = floor
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
    model_ = Image.new("RGBA", (Wc, Hc), (0, 0, 0, 0))
    model_.alpha_composite(img, (int(round(ox)), int(round(oy))))
    return model_, sh


LIGHT = (-0.45, -1.5, 0.3)              # sun from the upper left, shadows fall to the right


def render(key, ppu):
    """all animation frames + shadow mask at the given pixels per unit (supersampled)"""
    m = model(key)
    back = key in BACK_VIEW
    cam = (0.55, 0.75, 1.0) if back else PR.CAM
    light = (0.45, -1.5, -0.3) if back else LIGHT      # mirrored so the shadow still falls right on screen
    PR.PPU = ppu * SS
    floor = min(min(e["from"][1], e["to"][1]) for e in m.elements)
    frames = []
    for f in range(E.NFRAMES):
        mod, sh = render_piece(m, f, floor, cam, light)
        frames.append(mod)
    small = lambda im: im.resize((round(im.width / SS), round(im.height / SS)), Image.LANCZOS)
    return [small(f) for f in frames], small(sh)


def clean(img):
    a = np.array(img)
    lab, n = ndimage.label(a[..., 3] > 8)
    sizes = ndimage.sum(np.ones_like(lab), lab, range(1, n + 1))
    keep = np.isin(lab, [i + 1 for i, s in enumerate(sizes) if s > 5000])
    a[~keep] = 0
    im = Image.fromarray(a)
    return im.crop(im.getbbox())


def title(top, small, top_h):
    t = clean(Image.open(f"{TDIR}/t_{top}.png"))
    t = t.resize((round(t.width * top_h / t.height), top_h), Image.LANCZOS)
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


# ------------------------------------------------------------------ piece icons (cards)
BOX_W, BOX_H, BOX_BOTTOM = 640, 500, 640
MAX_H = {"wisp": 360, "ghostlight_lantern": 470, "candle_crown": 420}


def fit_ppu(key, box_h):
    frames, _ = render(key, 7)
    bb = frames[0].getbbox()
    return 7 * min(BOX_W / (bb[2] - bb[0]), box_h / (bb[3] - bb[1]))


def card(key, f=None, cache={}):
    if key not in cache:
        cache[key] = render(key, fit_ppu(key, MAX_H.get(key, BOX_H)))
    frames, sh = cache[key]
    img = background()
    m = frames[0 if f is None else f]
    bb = frames[0].getbbox()
    x = round(S / 2 - (bb[0] + bb[2]) / 2)
    y = round(BOX_BOTTOM - bb[3]) - (40 if key in FLOATS else 0)
    if key not in FLOATS:
        img.alpha_composite(shadow_layer(sh), (x, y))
    img.alpha_composite(m, (x, y))
    ttl = title(*NAMES[key], 132)
    img.alpha_composite(ttl, ((S - ttl.width) // 2, S - ttl.height - 46))
    return img.convert("RGB")


# ------------------------------------------------------------------ main store icon (full set)
SCALE_PPU = 13.0                                       # one scale for every piece
LAYOUT = [  # key, x of piece centre, y of piece bottom   (back row first)
    ("moonlit_broom",      235, 545),
    ("witch_hat",          540, 450),
    ("wisp",               840, 360),
    ("candle_crown",       330, 715),
    ("ghostlight_lantern", 600, 715),
    ("grimoire",           810, 690),
]


def main_icon(f=None, cache={}):
    if not cache:
        for key, *_ in LAYOUT:
            cache[key] = render(key, SCALE_PPU)
    img = background()
    placed = []
    for key, cx, by in LAYOUT:
        frames, sh = cache[key]
        bb = frames[0].getbbox()
        placed.append((key, frames, sh, (round(cx - (bb[0] + bb[2]) / 2), round(by - bb[3]))))
    lo = min(xy[0] + fr[0].getbbox()[0] for _, fr, _, xy in placed)
    hi = max(xy[0] + fr[0].getbbox()[2] for _, fr, _, xy in placed)
    dx = round(S / 2 - (lo + hi) / 2)                  # centre the pieces (not their shadows)
    for key, frames, sh, (x, y) in placed:
        if key not in FLOATS:
            img.alpha_composite(shadow_layer(sh), (x + dx, y))
    for key, frames, sh, (x, y) in placed:
        img.alpha_composite(frames[0 if f is None else f], (x + dx, y))
    ttl = title("witching", "hour", 170)
    ttl = ttl.resize((min(780, ttl.width), round(ttl.height * min(780, ttl.width) / ttl.width)), Image.LANCZOS)
    img.alpha_composite(ttl, ((S - ttl.width) // 2, S - ttl.height - 34))
    return img.convert("RGB")


def gif(frames_rgb, path, ms=None):
    ms = ms or [t * 50 for t in (3, 3, 2, 3, 4, 3)]     # the textures' own frame times (ticks)
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


FRAME_MS = 150                                          # frametime 3 ticks, same as the textures

if __name__ == "__main__":
    anim = "--animate" in sys.argv
    main_icon().save(f"{OUT}/witching-hour-icon.png")
    if anim:
        gif([main_icon(k) for k in range(E.NFRAMES)], f"{OUT}/witching-hour-icon.gif")
    for key in FILES:
        card(key).save(f"{OUT}/witching-hour-{FILES[key]}.png")
        if anim:
            gif([card(key, k) for k in range(E.NFRAMES)], f"{OUT}/witching-hour-{FILES[key]}.gif")
        print(key, "done")
