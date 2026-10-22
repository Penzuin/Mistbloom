"""Vanilla-resolution house style. Copy of claude/inktober/px.py.
16 px per block, 5-tone palettes, world-space patterns, directional bevel only, no gradients."""
import zlib
import numpy as np
from engine import STATE, SIDES, _blank, sprite, animated, fr


def hx(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))


PAL = {k: [hx(c) for c in v] for k, v in {
    "walnut":   ["#c98a5e", "#a8683f", "#8a4f2c", "#6c3a20", "#4a2616"],
    "oak":      ["#e2b979", "#c99a5b", "#a87a42", "#835b2e", "#5c3e1e"],
    "spruce":   ["#a87c52", "#8a6040", "#6e4a30", "#543622", "#3a2416"],
    "bark":     ["#8a6a4a", "#6e5038", "#563c2a", "#402c1e", "#2a1c12"],
    "stone":    ["#c8c8c0", "#a8a8a2", "#8c8c88", "#6e6e6c", "#4e4e50"],
    "darkstone": ["#8c8698", "#6c6678", "#54505e", "#403c48", "#2c2832"],
    "moss":     ["#a6c45a", "#82a340", "#628232", "#486426", "#32461c"],
    "leaf":     ["#9ccc58", "#78ac3e", "#58882e", "#406624", "#2c4818"],
    "iron":     ["#e6e6e6", "#bcbcc0", "#94949a", "#6c6c74", "#46464e"],
    "gold":     ["#fff3a0", "#ffd84a", "#f0aa22", "#c27a18", "#8a4e12"],
    "red":      ["#ff8a78", "#e8483e", "#c02c2e", "#8c1c24", "#5a1018"],
    "cream":    ["#fffbea", "#f4e8c8", "#e0cca0", "#c4a878", "#9a7e56"],
    "paper":    ["#fffdf4", "#f4ecd2", "#e2d4ae", "#c6b286", "#9c865e"],
}.items()}


def C(mat, t, a=255):
    t = max(0, min(4, int(t)))
    r, g, b = PAL[mat][t]
    return (r, g, b, a)


def _h(*v):
    return zlib.crc32(np.array(v, np.int64).tobytes()) & 0xffff


def _uv():
    P, n = STATE["pos"], STATE["normal"]
    ax = int(np.argmax(np.abs(n)))
    if ax == 1:
        u, v = P[..., 0], P[..., 2]
    elif ax == 0:
        u, v = P[..., 2], -P[..., 1]
    else:
        u, v = P[..., 0], -P[..., 1]
    return np.floor(u).astype(int), np.floor(v).astype(int), ax


def _paint(mat, tones, alpha=255):
    h, w = tones.shape
    img = np.zeros((h, w, 4), np.uint8)
    for t in range(5):
        img[tones == t] = C(mat, t, alpha)
    return img


def despeckle(t):
    t = t.copy()
    h, w = t.shape
    if h < 2 or w < 2:
        return t
    for _ in range(2):
        out = t.copy()
        for y in range(h):
            for x in range(w):
                nb = [t[yy, xx] for yy, xx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)) if 0 <= yy < h and 0 <= xx < w]
                if len(nb) >= 2 and all(n != t[y, x] for n in nb):
                    vals, cnt = np.unique(nb, return_counts=True)
                    if cnt.max() >= len(nb) - (1 if len(nb) == 4 else 0):
                        out[y, x] = vals[cnt.argmax()]
        t = out
    return t


def bevel(tones, face, top=True, bottom=True, sides=True):
    h, w = tones.shape
    if h < 3 or w < 3:
        if face in SIDES and h >= 2 and top:
            tones[0, :] = np.maximum(0, tones[0, :] - 1)
        return tones
    if top:
        tones[0, :] = np.maximum(0, tones[0, :] - 1)
    if sides:
        tones[1:, 0] = np.maximum(0, tones[1:, 0] - 1)
        tones[1:, -1] = np.minimum(4, tones[1:, -1] + 1)
    if bottom:
        tones[-1, 1:] = np.minimum(4, tones[-1, 1:] + 1)
    return tones


def inset(t, x0, y0, x1, y1, raised=False):
    d, l = (1, -1) if not raised else (-1, 1)
    t[y0, x0:x1 + 1] += d; t[y0:y1 + 1, x0] += d
    t[y1, x0 + 1:x1 + 1] += l; t[y0 + 1:y1 + 1, x1] += l
    np.clip(t, 0, 4, out=t)
    return t


def lobes(t, n, hi=True):
    h, w = t.shape
    edges = [round(i * w / n) for i in range(n + 1)]
    for i in range(n):
        a, b = edges[i], edges[i + 1]
        if i > 0:
            t[:, a] = np.minimum(4, t[:, a] + 1)
        if hi and b - a >= 3 and h >= 4:
            t[1, a + 1:b - 1] = np.maximum(0, t[1, a + 1:b - 1] - 1)
            t[2:max(3, h // 3), a + 1] = np.maximum(0, t[2:max(3, h // 3), a + 1] - 1)
        if b - a >= 3:
            t[h - 2:, b - 2:b - 1] = np.minimum(4, t[h - 2:, b - 2:b - 1] + 1)
    return t


def material(mat, kind="plain", base=2, edge=True, alpha=255, detail=None):
    def f(w, h, face, key):
        u, v, ax = _uv()
        t = np.full((h, w), base, int)
        if kind in ("wood", "woodv"):
            vert = kind == "woodv" or (ax != 1 and h > 2 * w)
            along, across = (v, u) if vert else (u, v)
            if ax == 1:
                along, across = u, v
            plank = 4
            seam = (across % plank) == plank - 1
            g = np.array([[_h(a // 5, b, 7) for a, b in zip(ra, rb)] for ra, rb in zip(along, across)])
            streak = (g % 9 == 0) & (across % plank != plank - 1)
            t = np.where(streak, base + 1, t)
            t = np.where((g % 17 == 5) & ~seam, base - 1, t)
            t = np.where(seam, base + 1, t)
            joint = (along + (across // plank) * 5) % 12 == 0
            t = np.where(joint & ~seam, base + 1, t)
        t = despeckle(t)
        if detail is not None:
            detail(t, u, v, face, w, h)
        t = np.clip(t, 0, 4)
        if edge:
            t = bevel(t, face)
        if face == "down":
            t = np.minimum(4, t + 1)
        return _paint(mat, t, alpha)
    return f


def card_art(rows, pal):
    def f(w, h, face, key):
        img = _blank(w, h)
        ah, aw = len(rows), len(rows[0])
        mir = face in ("south", "west")
        for y in range(h):
            for x in range(w):
                ch = rows[int(y * ah / h)][int(x * aw / w)] if not mir else rows[int(y * ah / h)][aw - 1 - int(x * aw / w)]
                if ch != ".":
                    img[y, x] = C(*pal[ch])
        return img
    return f
