"""Night Wings store icon + piece icons (Hibiscus style): violet floor with hard-edged light
bands, every wing rendered with one camera at one scale, no shadows (wings float),
Minecraft Title Generator titles. Also animated GIFs at the textures' frame times."""
import numpy as np
from PIL import Image

S = 1024
R, T = "/root/nwicon/r", "/root/nwicon/t"
OUT = "/root/nwicon/out"
FRAMES, TICKS = 6, [3, 3, 2, 3, 4, 3]
KEYS = ["starfeather_wings", "duskbat_wings", "frostlight_wings", "bloomfairy_wings", "nightwyrm_wings", "petal_wings"]
FLOOR_MID, FLOOR_EDGE, BAND = np.array([86, 68, 156]), np.array([36, 28, 84]), np.array([122, 104, 198])

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

def crop(p):
    im = Image.open(p).convert("RGBA")
    arr = np.array(im); arr[..., 3][arr[..., 3] < 40] = 0
    a = arr[..., 3] > 0
    cols = a.sum(0); rows = a.sum(1)
    keep_c = cols > 0.06 * rows.max()            # drop stray hairline columns from the generator
    keep_r = rows > 0.06 * cols.max()
    arr[:, ~keep_c, 3] = 0; arr[~keep_r, :, 3] = 0
    from scipy import ndimage
    lab, n = ndimage.label(arr[..., 3] > 0)
    sizes = ndimage.sum(np.ones_like(lab), lab, range(1, n + 1))
    for i, sz in enumerate(sizes, 1):
        if sz < 0.002 * lab.size:                   # thin slivers, not letters
            arr[..., 3][lab == i] = 0
    im = Image.fromarray(arr)
    return im.crop(im.getbbox())

def title(name):
    big, small = crop(f"{T}/{name}_big.png"), crop(f"{T}/{name}_small.png")
    sh = round(big.height * 0.62)
    small = small.resize((round(small.width * sh / small.height), sh), Image.LANCZOS)
    if small.width > big.width * 1.15:
        f = big.width * 1.15 / small.width
        small = small.resize((round(small.width * f), round(small.height * f)), Image.LANCZOS)
    ov = round(big.height * (0.35 if big.width < big.height * 4 else 0.2))   # long words: less overlap
    W, H = max(big.width, small.width), big.height + small.height - ov
    t = Image.new("RGBA", (W, H))
    t.alpha_composite(big, ((W - big.width) // 2, 0))
    t.alpha_composite(small, ((W - small.width) // 2, big.height - ov))
    return t

def put_title(img, name):
    t = title(name)
    tw = min(900, round(t.width * 270 / t.height))
    t = t.resize((tw, round(t.height * tw / t.width)), Image.LANCZOS)
    img.alpha_composite(t, ((S - tw) // 2, S - t.height - 40))

def wing(key, frame, k):
    im = Image.open(f"{R}/{key}_f{frame}.png")
    return im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)

# main icon: two rows of three, back row higher, one scale for all
LAYOUT = [("starfeather_wings", 205, 370), ("frostlight_wings", 512, 350), ("petal_wings", 819, 370),
          ("duskbat_wings", 215, 680), ("bloomfairy_wings", 512, 700), ("nightwyrm_wings", 809, 680)]
MAIN_K = 0.42

def main_icon(frame=0):
    img = background()
    for key, cx, by in LAYOUT:
        m = wing(key, frame, MAIN_K)
        img.alpha_composite(m, (round(cx - m.width / 2), round(by - m.height)))
    put_title(img, "main")
    return img.convert("RGB")

def piece_icon(key, frame=0):
    img = background()
    m = wing(key, frame, 1.0)
    k = min(600 / m.height, 760 / m.width)
    m = m.resize((round(m.width * k), round(m.height * k)), Image.LANCZOS)
    img.alpha_composite(m, (round(S / 2 - m.width / 2), round(660 - m.height)))
    put_title(img, key)
    return img.convert("RGB")

def gif(frames, path):
    strip = Image.new("RGB", (S, S * len(frames)))
    for i, f in enumerate(frames):
        strip.paste(f, (0, S * i))
    pal = strip.quantize(colors=256, method=Image.Quantize.MEDIANCUT)
    g = [f.quantize(palette=pal, dither=Image.Dither.NONE) for f in frames]
    base_rgb, base_idx = np.array(frames[0]).astype(int), np.array(g[0])
    for i in range(1, len(g)):
        same = np.abs(np.array(frames[i]).astype(int) - base_rgb).sum(2) == 0
        idx = np.array(g[i]); idx[same] = base_idx[same]
        im = Image.fromarray(idx, "P"); im.putpalette(g[0].getpalette()); g[i] = im
    g[0].save(path, save_all=True, append_images=g[1:], duration=[t * 50 for t in TICKS], loop=0, optimize=False, disposal=1)

if __name__ == "__main__":
    import os, sys
    os.makedirs(OUT, exist_ok=True)
    main_icon().save(f"{OUT}/night-wings-thumbnail.png")
    for i, key in enumerate(KEYS, 1):
        piece_icon(key).save(f"{OUT}/night-wings-{i}-{key.replace('_wings', '')}.png")
    if "--gif" in sys.argv:
        gif([main_icon(k) for k in range(FRAMES)], f"{OUT}/night-wings-thumbnail-animated.gif")
    print("ok")
