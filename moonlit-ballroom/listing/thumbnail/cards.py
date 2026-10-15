"""One card per Moonlit Ballroom piece, in the store-icon style (Hibiscus layout):
same lavender floor + moonlight bands, one piece large in the middle with its hard sun shadow,
two-tone Minecraft-style name at the bottom (lavender top word, gold small word).
usage: python3 cards.py <titles dir> <out dir> [--animate]
"""
import sys, os
import numpy as np
from PIL import Image
from scipy import ndimage
import pieces_render as PR
import compose as C
import engine as E
import pieces as P

TDIR, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
S, SS = 1024, 3
BOX_W, BOX_H = 700, 520          # space the piece may fill
BOX_BOTTOM = 650                 # floor line the piece stands on
TOP_H = 132                      # letter height of the lavender word on every card
SMALL_RATIO = 0.665              # gold word height vs lavender word (same as the store icon)

CARDS = [  # file name, model, top word, small word, shadow
    ("waltzing-ghosts",     lambda: P.waltzing_ghosts(),         "waltzing", "ghosts",     False),
    ("ghost-pianist",       lambda: P.ghost_piano(),             "ghost",    "pianist",    True),
    ("floating-candelabra", lambda: P.floating_candelabra(True), "floating", "candelabra", False),
    ("ghost-lantern",       lambda: P.ghost_lantern(True),       "ghost",    "lantern",    True),
    ("lady-wispwell",       lambda: P.ghost_portrait(),          "lady",     "wispwell",   True),
    ("wisp",                lambda: P.wisp(),                    "wisp",     None,         True),
]

def clean(img):
    """crop to the word and drop stray Blockbench hairlines (keep big connected parts only)"""
    a = np.array(img)
    lab, n = ndimage.label(a[..., 3] > 8)
    sizes = ndimage.sum(np.ones_like(lab), lab, range(1, n + 1))
    keep = np.isin(lab, [i + 1 for i, s in enumerate(sizes) if s > 5000])
    a[~keep] = 0
    im = Image.fromarray(a)
    return im.crop(im.getbbox())

def title(top, small):
    t = clean(Image.open(f"{TDIR}/t_{top}.png"))
    t = t.resize((round(t.width * TOP_H / t.height), TOP_H), Image.LANCZOS)
    if not small:
        return t
    s = clean(Image.open(f"{TDIR}/s_{small}.png"))
    sh = round(TOP_H * SMALL_RATIO)
    s = s.resize((round(s.width * sh / s.height), sh), Image.LANCZOS)
    ov = round(sh * 0.35)
    W = max(t.width, s.width)
    c = Image.new("RGBA", (W, t.height + s.height - ov), (0, 0, 0, 0))
    c.alpha_composite(t, ((W - t.width) // 2, 0))
    c.alpha_composite(s, ((W - s.width) // 2, t.height - ov))
    return c

MAX_H = {"wisp": 380, "ghost-lantern": 450}   # small pieces: don't blow them up to piano size

def render(make, box_h=BOX_H):
    """render at a size that fits the box without upscaling (crisp pixels)"""
    m = make()
    floor = min(0.0, min(min(e["from"][1], e["to"][1]) for e in m.elements))
    PR.PPU = 7 * SS
    probe, _ = PR.render_piece(m, 0, floor)
    bb = probe.getbbox()
    k = min(BOX_W * SS / (bb[2] - bb[0]), box_h * SS / (bb[3] - bb[1]))
    PR.PPU = 7 * SS * k
    frames = []
    for f in range(E.NFRAMES):
        mod, sh = PR.render_piece(m, f, floor)
        frames.append(mod)
    return frames, sh

def card(frames, sh, ttl, shadow, f=0):
    img = C.background()
    m = frames[f]
    size = (round(m.width / SS), round(m.height / SS))
    m, s = m.resize(size, Image.LANCZOS), sh.resize(size, Image.LANCZOS)
    bb = frames[0].resize(size, Image.LANCZOS).getbbox()
    x = round(S / 2 - (bb[0] + bb[2]) / 2)
    y = round(BOX_BOTTOM - bb[3])
    if shadow:
        sl = Image.new("RGBA", size, C.SHADOW + (0,))
        sl.putalpha(s.point(lambda v: int(v * C.SHADOW_A)))
        img.alpha_composite(sl, (x, y))
    img.alpha_composite(m, (x, y))
    img.alpha_composite(ttl, ((S - ttl.width) // 2, S - ttl.height - 46))
    return img.convert("RGB")

def gif(frames_rgb, path):
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
    g[0].save(path, save_all=True, append_images=g[1:], duration=150, loop=0, optimize=False, disposal=1)

if __name__ == "__main__":
    anim = "--animate" in sys.argv
    for name, make, top, small, shadow in CARDS:
        frames, sh = render(make, MAX_H.get(name, BOX_H))
        ttl = title(top, small)
        still = card(frames, sh, ttl, shadow)
        still.save(f"{OUT}/moonlit-ballroom-{name}.png")
        if anim:
            gif([card(frames, sh, ttl, shadow, f) for f in range(len(frames))], f"{OUT}/moonlit-ballroom-{name}.gif")
        print(name, "done")
