"""Day 4 Cactus - Potted Cactus. Vanilla-res style, 13 elements.
Chunky saguaro (painted ribs, spine pins) with two arms, a pink bloom on top, in a terracotta pot:
foot -> body with a painted zigzag band -> thick rolled rim, soil and pebbles."""
import numpy as np
from engine import Model, SIDES
from px import PAL, hx, material, card_art, _uv, C, lobes

PAL["soil2"] = [hx(c) for c in ("#9a7454", "#7a5a40", "#5c422e", "#402e20", "#2a1e14")]


def clean(img):
    h, w = img.shape[:2]
    k = img[..., 0].astype(int) * 65536 + img[..., 1].astype(int) * 256 + img[..., 2]
    out = img.copy()
    for y in range(h):
        for x in range(w):
            nb = [(a, b) for a, b in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)) if 0 <= a < h and 0 <= b < w]
            ks = {k[a, b] for a, b in nb}
            if len(nb) >= 3 and len(ks) == 1 and k[y, x] not in ks:
                out[y, x] = img[nb[0]]
    return out


def ribs(n, spines=True):
    def d(t, u, v, face, w, h):
        t[:, :] = 2
        if face in SIDES:
            lobes(t, n)
        elif face == "up":
            t[:, :] = 1
            t[-1, :] = 2; t[:, -1] = 2
    base = material("cactus", "plain", detail=d)

    def f(w, h, face, key):
        img = clean(base(w, h, face, key))
        if spines and face in SIDES:
            edges = [round(i * w / n) for i in range(n + 1)]
            for i in range(n):
                cx = (edges[i] + edges[i + 1]) // 2
                for y in range(2 + (i % 2) * 2, h - 1, 4):
                    img[y, cx] = C("cream", 0)
        return img
    return f


def pot_body():
    def d(t, u, v, face, w, h):
        t[:, :] = 2
        if face in SIDES:
            t[1, :] = 3
    b = material("terracotta", "plain", detail=d)

    def f(w, h, face, key):
        img = clean(b(w, h, face, key))
        if face in SIDES:
            c = np.arange(w)
            img[3, :] = C("cream", 2)
            teeth = (c % 4 == 1) | (c % 4 == 2)
            img[4, teeth] = C("cream", 3)
        return img
    return f


def pot_foot():
    def d(t, u, v, face, w, h):
        t[:, :] = 3
    return material("terracotta", "plain", detail=d)


def rim():
    def d(t, u, v, face, w, h):
        t[:, :] = 1
        if face in SIDES:
            t[1:, :] = 2
            t[-1, :] = 3
        if face == "up":
            iu, iv = u - u.min(), v - v.min()
            soil = (iu >= 2) & (iu <= w - 3) & (iv >= 2) & (iv <= h - 3)
            t[~soil & ((iu == w - 1) | (iv == h - 1))] = 2
    base = material("terracotta", "plain", detail=d)
    pebbles = (((3, 9), "stone"), ((10, 10), "white"), ((10, 4), "stone"), ((4, 4), "yellow"))

    def f(w, h, face, key):
        img = base(w, h, face, key)
        if face == "up":
            u, v, _ = _uv()
            iu, iv = u - u.min(), v - v.min()
            soil = (iu >= 2) & (iu <= w - 3) & (iv >= 2) & (iv <= h - 3)
            img[soil] = C("soil2", 2)
            img[soil & ((iv == 2) | (iu == 2))] = C("soil2", 4)
            img[soil & ((iv == h - 3) | (iu == w - 3))] = C("soil2", 1)
            for (a, b), mat in pebbles:
                img[(iu >= a) & (iu <= a + 1) & (iv >= b) & (iv <= b + 1)] = C(mat, 2)
                img[(iu == a) & (iv == b)] = C(mat, 0)
                img[(iu == a + 1) & (iv == b + 1)] = C(mat, 3)
        return img
    return f


FLOWER = [
    ".pPPp.",
    "pPPPPp",
    "PPyYPP",
    "PPyyPP",
    "pPPPPp",
    ".pPPp.",
]
FLOWER_P = {"p": ("pink", 2), "P": ("pink", 1), "y": ("yellow", 2), "Y": ("yellow", 0)}
BUD = [
    ".PP.",
    "PPPp",
    "pPpp",
    ".gg.",
]
BUD2 = [
    "PPp",
    "pPp",
    ".g.",
]
BUD_P = {"p": ("pink", 2), "P": ("pink", 1), "g": ("cactus", 3)}


def build():
    m = Model("potted_cactus")
    m.box([3, 0, 3], [13, 1, 13], pot_foot())
    m.box([2, 1, 2], [14, 7, 14], pot_body())
    m.box([1, 7, 1], [15, 10, 15], rim())
    m.box([5, 10, 5], [11, 25, 11], ribs(3))
    m.box([6, 25, 6], [10, 26, 10], ribs(2, spines=False))
    m.box([1, 14, 6.5], [5, 17, 9.5], ribs(1, spines=False), faces=("north", "south", "west", "up", "down"))
    m.box([1, 17, 6.5], [4, 23, 9.5], ribs(1))
    m.box([11, 17, 6.5], [15, 20, 9.5], ribs(1, spines=False), faces=("north", "south", "east", "up", "down"))
    m.box([12, 20, 6.5], [15, 24, 9.5], ribs(1))
    m.card([5, 26.05, 5], [11, 26.05, 11], card_art(FLOWER, FLOWER_P), rot=("y", 22.5, [8, 26, 8]))
    m.crossed(2.5, 23, 8, 4, 4, card_art(BUD, BUD_P))
    m.card([12, 24, 8], [15, 27, 8], card_art(BUD2, BUD_P))
    return m
