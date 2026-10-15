"""A skinned player for previews, built from a standard 64x64 Minecraft skin.

Same layout as the old stand-in figure: 1 skin pixel = 1.6 units, the player
faces north (-z), so the back (where the wings go) is the south side.
"""
import numpy as np
from PIL import Image
from engine import Model, P

SKIN_RES = 8          # texels per unit, high enough that nearest scaling looks even


def _painter(skin, rect, flip_x=False, flip_y=False):
    x, y, w, h = rect
    crop = skin[y:y + h, x:x + w]
    if flip_x:
        crop = crop[:, ::-1]
    if flip_y:
        crop = crop[::-1]

    def f(W, H, face, key):
        iy = (np.arange(H) * h // H).clip(0, h - 1)
        ix = (np.arange(W) * w // W).clip(0, w - 1)
        return crop[iy][:, ix]
    return f


def _faces(skin, u, v, w, h, d):
    """Standard skin box layout -> painter per face (front = north)."""
    return {
        "up": _painter(skin, (u + d, v, w, d), True, True),
        "down": _painter(skin, (u + d + w, v, w, d), True, False),
        "east": _painter(skin, (u, v + d, d, h)),                 # player's right side
        "north": _painter(skin, (u + d, v + d, w, h)),            # front
        "west": _painter(skin, (u + d + w, v + d, d, h)),         # player's left side
        "south": _painter(skin, (u + 2 * d + w, v + d, w, h)),    # back
    }


def player(skin_path="zinguin.png", slim=True):
    skin = np.array(Image.open(skin_path).convert("RGBA"))
    if skin.shape[0] == 32:   # old 64x32 skins: mirror the right limbs for the left
        skin = np.concatenate([skin, np.zeros_like(skin)], 0)
        skin[48:64, 16:32] = skin[16:32, 0:16]
        skin[48:64, 32:48] = skin[16:32, 40:56]
    aw = 3 if slim else 4
    m = Model("player", "x")

    def part(lo, hi, uv, dims, grow=0.0):
        g = grow * P
        lo = [a * P - g for a in lo]
        hi = [a * P + g for a in hi]
        e = {"from": lo, "to": hi, "faces": _faces(skin, *uv, *dims), "emit": 0, "res": SKIN_RES}
        m.elements.append(e)

    # body x 1..9, y -11..1, z 3..7 in skin pixels (matches the old figure)
    base = [
        ((1, 1, 1), (9, 9, 9), (0, 0), (8, 8, 8)),                          # head
        ((1, -11, 3), (9, 1, 7), (16, 16), (8, 12, 4)),                     # torso
        ((9, -11, 3), (9 + aw, 1, 7), (40, 16), (aw, 12, 4)),               # right arm
        ((1 - aw, -11, 3), (1, 1, 7), (32, 48), (aw, 12, 4)),               # left arm
    ]
    over = [
        ((1, 1, 1), (9, 9, 9), (32, 0), (8, 8, 8), 0.5),                    # hat
        ((1, -11, 3), (9, 1, 7), (16, 32), (8, 12, 4), 0.25),               # jacket
        ((9, -11, 3), (9 + aw, 1, 7), (40, 32), (aw, 12, 4), 0.25),         # right sleeve
        ((1 - aw, -11, 3), (1, 1, 7), (48, 48), (aw, 12, 4), 0.25),         # left sleeve
    ]
    legs = [
        ((5, -23, 3), (9, -11, 7), (0, 16), (4, 12, 4)),                    # right leg
        ((1, -23, 3), (5, -11, 7), (16, 48), (4, 12, 4)),                   # left leg
    ]
    pants = [
        ((5, -23, 3), (9, -11, 7), (0, 32), (4, 12, 4), 0.25),
        ((1, -23, 3), (5, -11, 7), (0, 48), (4, 12, 4), 0.25),
    ]
    for lo, hi, uv, d in base:
        part(lo, hi, uv, d)
    for lo, hi, uv, d, g in over:
        part(lo, hi, uv, d, g)
    m.bust_n = len(m.elements)       # head + torso + arms (+ their overlays)
    for lo, hi, uv, d in legs:
        part(lo, hi, uv, d)
    for lo, hi, uv, d, g in pants:
        part(lo, hi, uv, d, g)
    return m
