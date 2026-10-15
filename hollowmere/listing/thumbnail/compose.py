"""Halloween Festival store icon, Hibiscus layout (recipe in brand/ICON_STYLE.md):
flat dusky-plum floor with two hard-edged warm light bands, every piece at one scale in a loose arc,
hard sun shadows tinted from the floor, Minecraft Title Generator title at the bottom."""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage

S = 1024
R = "/home/claude/hollow/thumb/r"
T = "/home/claude/hollow/thumb/t"
SS = 3
SCALE = 1.0

FLOOR_MID = np.array([104, 66, 132])     # dusky plum
FLOOR_EDGE = np.array([52, 30, 78])      # deeper towards the corners
BAND = np.array([196, 120, 112])         # warm lantern light band
SHADOW = (36, 18, 52)
SHADOW_A = 0.55
NO_SHADOW = set()
FRAMES_MS = [100, 150, 100, 100, 200, 100]   # engine FRAMETIMES (2,3,2,2,4,2 ticks)

# (piece, centre x, bottom y)  -- back row first so the front row overlaps it
LAYOUT = [
    ("pumpkin_lamp_lit", 215, 560),
    ("scarecrow", 850, 550),
    ("potion_stall", 545, 500),
    ("tombstone", 125, 680),
    ("jack_o_lantern_lit", 300, 722),
    ("black_cat", 470, 748),
    ("cauldron_lit", 640, 736),
    ("candy_bucket", 815, 706),
    ("crystal_ball", 940, 672),
]


def background():
    y, x = np.mgrid[0:S, 0:S].astype(float)
    d = np.sqrt(((x - S * 0.55) / S) ** 2 + ((y - S * 0.42) / S) ** 2)
    t = np.clip((d - 0.18) / 0.55, 0, 1)[..., None]
    img = FLOOR_MID * (1 - t) + FLOOR_EDGE * t
    k = y + (x - S / 2) * -0.22
    for lo, hi, a in ((250, 590, 0.22), (590, 640, 0.10)):
        m = ((k > lo) & (k < hi))[..., None]
        img = np.where(m, img * (1 - a) + BAND * a, img)
    return Image.fromarray(img.astype(np.uint8)).convert("RGBA")


def piece(name, frame=None):
    import os
    p = f"{R}/{name}_f{frame}.png" if frame is not None and os.path.exists(f"{R}/{name}_f{frame}.png") else f"{R}/{name}.png"
    m = Image.open(p); s = Image.open(f"{R}/{name}_shadow.png")
    f = SCALE / SS
    size = (round(m.width * f), round(m.height * f))
    return m.resize(size, Image.LANCZOS), s.resize(size, Image.LANCZOS)


def clean(im, min_px=5000):
    """Drop stray Blockbench hairlines: keep only big connected pieces of the title render."""
    a = np.array(im)[..., 3] > 0
    lab, n = ndimage.label(a)
    sizes = ndimage.sum(a, lab, range(1, n + 1))
    keep = np.isin(lab, [i + 1 for i, s in enumerate(sizes) if s >= min_px])
    arr = np.array(im); arr[..., 3] = np.where(keep, arr[..., 3], 0)
    out = Image.fromarray(arr)
    return out.crop(out.getbbox())


def title():
    big = clean(Image.open(f"{T}/w_halloween.png"))
    small = clean(Image.open(f"{T}/w_festival_small.png"), 20000)
    sw = round(big.width * 0.80)
    small = small.resize((sw, round(small.height * sw / small.width)), Image.LANCZOS)
    top_of_small = big.height - round(small.height * 0.35)
    out = Image.new("RGBA", (big.width, top_of_small + small.height), (0, 0, 0, 0))
    out.alpha_composite(big, (0, 0))
    out.alpha_composite(small, ((big.width - sw) // 2, top_of_small))
    return out


def main(out="/home/claude/hollow/thumb/halloween-festival-thumbnail.png", frame=None):
    img = background()
    boxes = []
    for name, cx, by in LAYOUT:
        m, _ = piece(name)
        x0 = int(cx - m.width / 2); bb = m.getbbox()
        boxes.append((x0 + bb[0], x0 + bb[2]))
    dx = round(S / 2 - (min(b[0] for b in boxes) + max(b[1] for b in boxes)) / 2)
    placed = []
    for name, cx, by in LAYOUT:
        m, s = piece(name, frame)
        xy = (int(cx - m.width / 2) + dx, int(by - m.height))
        placed.append((m, xy))
        if name not in NO_SHADOW:
            sh = Image.new("RGBA", m.size, SHADOW + (0,))
            sh.putalpha(s.point(lambda v: int(v * SHADOW_A)))
            img.alpha_composite(sh, xy)
    for m, xy in placed:
        img.alpha_composite(m, xy)
    t = TITLE
    tw = 800
    t = t.resize((tw, round(t.height * tw / t.width)), Image.LANCZOS)
    img.alpha_composite(t, ((S - tw) // 2, S - t.height - 40))
    if out is None:
        return img.convert("RGB")
    img.convert("RGB").save(out)
    return out


def animate(gif="/home/claude/hollow/thumb/halloween-festival-thumbnail-animated.gif",
            webp="/home/claude/hollow/thumb/halloween-festival-thumbnail-animated.webp"):
    frames = [main(out=None, frame=k) for k in range(len(FRAMES_MS))]
    frames[0].save(webp, save_all=True, append_images=frames[1:], duration=FRAMES_MS, loop=0, quality=92, method=6)
    strip = Image.new("RGB", (S, S * len(frames)))
    for k, f in enumerate(frames):
        strip.paste(f, (0, S * k))
    pal = strip.quantize(colors=256, method=Image.Quantize.MEDIANCUT)
    g = [f.quantize(palette=pal, dither=Image.Dither.FLOYDSTEINBERG) for f in frames]
    base_rgb, base_idx = np.array(frames[0]).astype(int), np.array(g[0])
    for k in range(1, len(g)):                       # unchanged pixels keep frame 0's index: no shimmer
        same = np.abs(np.array(frames[k]).astype(int) - base_rgb).sum(2) == 0
        idx = np.array(g[k]); idx[same] = base_idx[same]
        im = Image.fromarray(idx, "P"); im.putpalette(g[0].getpalette()); g[k] = im
    g[0].save(gif, save_all=True, append_images=g[1:], duration=FRAMES_MS, loop=0, optimize=False, disposal=1)
    return gif, webp


TITLE = title()

if __name__ == "__main__":
    o = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else "/home/claude/hollow/thumb/halloween-festival-thumbnail.png"
    print(main(o))
    if "--animate" in sys.argv:
        print(animate())
