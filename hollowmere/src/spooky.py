"""Hollowmere palette and painters (Halloween harvest fair)."""
import math, random
import numpy as np
import engine
from engine import _blank, T, SIDES, fr, animated, art, solid, wood

engine.RAMPS.update({k: engine._ramp7(v) for k, v in {
    "pumpkin":  ["#ffc46b", "#f99a3e", "#d9692c", "#9e4527"],
    "plum":     ["#c79be0", "#9b6cc4", "#6f479a", "#472c6b"],
    "moss":     ["#b8d98a", "#8ab865", "#5f8f4a", "#3e6338"],
    "bone":     ["#fbf3e2", "#e9dcc0", "#cbb894", "#9c8a6a"],
    "brew":     ["#e6ffb0", "#b4f26e", "#74cf52", "#3f9a4a"],
    "ebony":    ["#6e5a6a", "#4f3f52", "#36293c", "#221a29"],
    "hay":      ["#ffe7a1", "#f2c96b", "#d4a24a", "#a4773a"],
    "slate":    ["#b4b0c4", "#8e8aa2", "#6c6882", "#4a4760"],
    "candle":   ["#fffdf2", "#fff1c7", "#f6d999", "#d9b06e"],
    "rust":     ["#d58a64", "#b0644a", "#874636", "#5c2f2a"],
    "denim":    ["#9cb3d9", "#7590bf", "#566fa0", "#3c4f7a"],
}.items()})


def pumpkin_skin(face=None, lit=False, stem_top=True):
    """Ribbed pumpkin shaded darker toward the face edges so blocky lobes read as round."""
    def f(w, h, fc, key):
        img = _blank(w, h)
        rib = max(2, w // 5)
        for y in range(h):
            for x in range(w):
                d = abs((x + 0.5) / w - 0.5) * 2            # 0 centre .. 1 edge
                tone = 1 + (1 if d > 0.55 else 0) + (1 if d > 0.85 else 0)
                if x % rib == 0:
                    tone += 1                                 # rib groove
                if fc in SIDES and (y == 0 or y == h - 1):
                    tone += 1
                if fc in SIDES and 0 < y < h - 1 and d < 0.3 and y < h // 3 and x % rib != 0:
                    tone = 0                                  # soft highlight
                img[y, x] = T("pumpkin", tone)
        if fc == "up" and stem_top:
            cx, cy = w // 2, h // 2
            for y in range(h):
                for x in range(w):
                    if abs(x - cx) + abs(y - cy) <= max(1, w // 6):
                        img[y, x] = T("pumpkin", 3)
        if fc == "down":
            img[:, :] = T("pumpkin", 4)
        return img
    return f


def brew():
    """Bubbling witch brew: green swirl with popping bubbles, 6 frames."""
    def f(w, h, fc, key):
        k = fr()
        img = _blank(w, h)
        for y in range(h):
            for x in range(w):
                v = (x * 3 + y * 5 + k * 2) % 9
                img[y, x] = T("brew", 1 if v < 3 else 2 if v < 7 else 3)
        rng = random.Random(7)
        for i in range(max(2, w * h // 12)):
            bx, by, ph = rng.randrange(w), rng.randrange(h), rng.randrange(6)
            if (k - ph) % 6 < 2:
                img[by, bx] = T("brew", 0)
        return img
    return animated(f)


def hay():
    def f(w, h, fc, key):
        rng = random.Random(key)
        img = _blank(w, h)
        for y in range(h):
            for x in range(w):
                img[y, x] = T("hay", rng.choice([1, 2, 2, 3]))
        if fc in SIDES:
            for y in (1, h - 2):
                if 0 <= y < h:
                    img[y, :] = T("rust", 3)        # twine bands
        return img
    return f


def stone(ramp="slate", moss=True):
    """Weathered stone with cracks and moss creeping up from the bottom."""
    def f(w, h, fc, key):
        rng = random.Random(key)
        img = _blank(w, h)
        for y in range(h):
            for x in range(w):
                img[y, x] = T(ramp, rng.choice([1, 2, 2, 2, 3]))
        if fc in SIDES:
            x = rng.randrange(max(1, w))
            for y in range(1, min(h, 5)):
                x = max(0, min(w - 1, x + rng.choice([-1, 0, 1])))
                img[y, x] = T(ramp, 5)
            if moss:
                for x in range(w):
                    for y in range(max(0, h - 1 - rng.randrange(1, 3)), h):
                        if rng.random() < 0.7:
                            img[y, x] = T("moss", rng.choice([2, 3]))
        return img
    return f


def plaid(a="plum", b="ebony"):
    def f(w, h, fc, key):
        img = _blank(w, h)
        for y in range(h):
            for x in range(w):
                c = a if (x // 2 + y // 2) % 2 == 0 else b
                tone = 1 if (x % 4 == 0 or y % 4 == 0) else 2
                img[y, x] = T(c, tone)
        return img
    return f


def sack(face=False):
    """Burlap sack head with stitched smile on the north side."""
    def f(w, h, fc, key):
        rng = random.Random(key)
        img = _blank(w, h)
        for y in range(h):
            for x in range(w):
                img[y, x] = T("bone", 2 + ((x + y) % 2) + (1 if rng.random() < 0.08 else 0))
        if face and fc == "north" and w >= 5 and h >= 5:
            ey = h // 3
            img[ey, w // 2 - 2] = img[ey, w // 2 + 1] = T("ebony", 6)   # button eyes
            my = ey + 2
            for x in range(w // 2 - 2, w // 2 + 2):
                img[my, x] = T("ebony", 4)
                if x % 2 == 0 and my - 1 > ey:
                    img[my - 1, x] = T("ebony", 4)                       # stitches
        return img
    return f


def candle_flame():
    """Tiny 3x5 flame, 6-frame flicker."""
    rows_a = [".a.", "aba", "aba", "bcb", ".b."]
    rows_b = ["..a", ".ab", "aba", "bcb", ".b."]
    def f(w, h, fc, key):
        k = fr()
        rows = rows_b if k in (1, 4) else rows_a
        img = _blank(w, h)
        for y in range(h):
            for x in range(w):
                ch = rows[int(y * 5 / h)][int(x * 3 / w)]
                if ch == "a":
                    img[y, x] = T("ember", 2)
                elif ch == "b":
                    img[y, x] = T("ember", 1)
                elif ch == "c":
                    img[y, x] = T("candle", 0)
        return img
    return animated(f)


def wax(ramp="candle"):
    def f(w, h, fc, key):
        img = _blank(w, h)
        img[:, :] = T(ramp, 1)
        if fc in SIDES:
            img[0, :] = T(ramp, 0)
            for x in range(0, w, 2):
                img[min(h - 1, 1 + (x % 3 == 0)), x] = T(ramp, 0)        # drips
            img[-1, :] = T(ramp, 3)
        return img
    return f


BAT = art([
    "a.........a",
    "aa..a.a..aa",
    "abaaaaaaaba",
    ".aaaecea..",
    "..a.aaa.a..",
    ".....a.....",
], {"a": ("ebony", 4), "b": ("plum", 3), "c": ("ebony", 5), "e": ("pumpkin", 0)})

LEAF = art([
    "...aa",
    "..aba",
    ".abaa",
    "abaa.",
    "a....",
], {"a": ("moss", 2), "b": ("moss", 0)})

VINE = art([
    "..a.....",
    ".a.b....",
    ".a.bb...",
    "..a.....",
    "...a....",
    "...a.b..",
    "..a.bb..",
    "..a.....",
    "...a....",
    "...a....",
], {"a": ("moss", 3), "b": ("moss", 1)})

STRAW = art([
    "a.b.a",
    "ab.ba",
    ".aba.",
    "..a..",
], {"a": ("hay", 1), "b": ("hay", 3)})

COBWEB = art([
    "a...a...a",
    ".a..a..a.",
    "..aaaaa..",
    "aaa.a.aaa",
    "..aaaaa..",
    ".a..a..a.",
    "a...a...a",
], {"a": ("bone", 0, 190)})
