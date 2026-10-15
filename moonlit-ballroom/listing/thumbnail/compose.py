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

def piece(name):
    m = Image.open(f"{R}/{name}.png")
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

def main(out="/root/thumb/moonlit-ballroom-thumbnail-hibiscus.png"):
    img = background()
    # every shadow first, so no shadow falls on top of a piece
    placed = []
    for name, cx, by in LAYOUT:
        m, s = piece(name)
        xy = (int(cx - m.width / 2), int(by - m.height))
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
    img.convert("RGB").save(out)
    return out

if __name__ == "__main__":
    print(main())
