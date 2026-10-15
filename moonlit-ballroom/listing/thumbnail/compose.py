"""Moonlit Ballroom store icon in the Hibiscus layout:
flat floor-colour background with soft hard-edged light bands, every piece at the same scale
scattered in a loose arc, hard sun shadows tinted from the floor, Minecraft-style title at the bottom.
"""
import numpy as np
from PIL import Image

S = 1024
R = "/root/thumb/r"
SS = 3                       # pieces were rendered at 3x
SCALE = 1.34                 # one scale for every piece

FLOOR_MID = np.array([112, 92, 182])    # dusky lavender floor
FLOOR_EDGE = np.array([60, 42, 122])     # deeper violet towards the corners
BAND = np.array([140, 122, 208])         # moonlight band
SHADOW = (34, 22, 80)                    # shadows: floor colour pushed dark and cool
SHADOW_A = 0.55
NO_SHADOW = {"floating_candelabra_lit", "waltzing_ghosts"}   # user: these read better without one

def background():
    y, x = np.mgrid[0:S, 0:S].astype(float)
    # radial-ish falloff from a point above centre, like Hibiscus's warm corner tint
    d = np.sqrt(((x - S * 0.55) / S) ** 2 + ((y - S * 0.42) / S) ** 2)
    t = np.clip((d - 0.18) / 0.55, 0, 1)[..., None]
    img = FLOOR_MID * (1 - t) + FLOOR_EDGE * t
    # two straight moonlight bands running across at a shallow angle (hard edges, low contrast)
    k = y + (x - S / 2) * -0.22
    for lo, hi, a in ((260, 600, 0.30), (600, 650, 0.12)):
        m = ((k > lo) & (k < hi))[..., None]
        img = np.where(m, img * (1 - a) + BAND * a, img)
    return Image.fromarray(img.astype(np.uint8)).convert("RGBA")

def piece(name, frame=None):
    m = Image.open(f"{R}/{name}.png" if frame is None else f"{R}/{name}_f{frame}.png")
    s = Image.open(f"{R}/{name}_shadow.png")
    f = SCALE / SS
    size = (round(m.width * f), round(m.height * f))
    return m.resize(size, Image.LANCZOS), s.resize(size, Image.LANCZOS)

# (piece, x of canvas centre, y of canvas bottom) -- back row first so the front row overlaps it
LAYOUT = [
    ("ghost_piano",             250, 452),
    ("ghost_portrait",          838, 428),
    ("waltzing_ghosts",         548, 510),
    ("floating_candelabra_lit", 150, 712),
    ("ghost_lantern_lit",       410, 716),
    ("wisp",                    742, 712),
]

def main(out="/root/thumb/moonlit-ballroom-thumbnail-hibiscus.png", frame=None):
    img = background()
    # centre the group of pieces on the canvas (shadows ignored: they trail off to the right)
    boxes = []
    for name, cx, by in LAYOUT:
        m, s = piece(name)
        x0, y0 = int(cx - m.width / 2), int(by - m.height)
        bb = m.getbbox()
        boxes.append((x0 + bb[0], x0 + bb[2]))
    dx = round(S / 2 - (min(b[0] for b in boxes) + max(b[1] for b in boxes)) / 2)
    # every shadow first, so no shadow falls on top of a piece
    placed = []
    for name, cx, by in LAYOUT:
        m, s = piece(name, frame)
        xy = (int(cx - m.width / 2) + dx, int(by - m.height))
        placed.append((m, xy))
        if name in NO_SHADOW:
            continue
        sh = Image.new("RGBA", m.size, SHADOW + (0,))
        sh.putalpha(s.point(lambda v: int(v * SHADOW_A)))
        img.alpha_composite(sh, xy)
    for m, xy in placed:
        img.alpha_composite(m, xy)
    # title
    t = Image.open("/root/thumb/t/title_combo_clean.png")
    tw = 780
    t = t.resize((tw, round(t.height * tw / t.width)), Image.LANCZOS)
    img.alpha_composite(t, ((S - tw) // 2, S - t.height - 34))
    if out is None:
        return img.convert("RGB")
    print("shifted right by", dx, "px")
    img.convert("RGB").save(out)
    return out

def animate(gif="/root/thumb/moonlit-ballroom-thumbnail-animated.gif", webp="/root/thumb/moonlit-ballroom-thumbnail-animated.webp"):
    """8-frame loop at the in-game speed (3 ticks = 150 ms a frame)."""
    frames = [main(out=None, frame=k) for k in range(8)]
    frames[0].save(webp, save_all=True, append_images=frames[1:], duration=150, loop=0, lossless=False, quality=92, method=6)
    # one shared palette for every frame so the background doesn't shimmer
    strip = Image.new("RGB", (S, S * 8))
    for k, f in enumerate(frames):
        strip.paste(f, (0, S * k))
    pal = strip.quantize(colors=256, method=Image.Quantize.MEDIANCUT)
    g = [f.quantize(palette=pal, dither=Image.Dither.FLOYDSTEINBERG) for f in frames]
    # pixels that don't really change keep frame 0's exact palette index, so dither can't shimmer
    import numpy as np
    base_rgb, base_idx = np.array(frames[0]).astype(int), np.array(g[0])
    for k in range(1, len(g)):
        same = np.abs(np.array(frames[k]).astype(int) - base_rgb).sum(2) == 0
        idx = np.array(g[k]); idx[same] = base_idx[same]
        im = Image.fromarray(idx, "P"); im.putpalette(g[0].getpalette()); g[k] = im
    g[0].save(gif, save_all=True, append_images=g[1:], duration=150, loop=0, optimize=False, disposal=1)
    return gif, webp

if __name__ == "__main__":
    import sys
    print(main())
    if "--animate" in sys.argv:
        print(animate())
