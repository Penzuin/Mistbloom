"""Frostlight Night Market - tiny model engine.

Builds Minecraft Java block-model JSON (1.21.4+ item models) from boxes and flat
cards, paints one texture atlas per model procedurally (1 texel per model unit),
validates Nexo-safe limits and renders an orthographic preview that follows the
game's own UV and rotation rules.
"""
import json, math, os, random
import numpy as np
from PIL import Image

NS = "hollowmere"

# --------------------------------------------------------------------- palette
def _rgb(h):
    return np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)], float)

def _ramp7(hexes):
    c = [_rgb(h) for h in hexes]
    out = []
    for i in range(3):
        out += [c[i], (c[i] + c[i + 1]) / 2]
    out.append(c[3])
    return [tuple(int(round(v)) for v in x) for x in out]

RAMPS = {k: _ramp7(v) for k, v in {
    "spruce":    ["#c08a5e", "#9c6b48", "#7a5038", "#573829"],
    "oak":       ["#e6bd86", "#cb9d66", "#a97c4e", "#7f5a3a"],
    "snow":      ["#ffffff", "#f4f3ff", "#dfdcf6", "#bdb8e2"],
    "cranberry": ["#ff8f9c", "#ef6a7e", "#cc4d67", "#94375a"],
    "cream":     ["#fff8e6", "#f9e6c4", "#e8cb9c", "#c7a477"],
    "pine":      ["#8fd0a0", "#67b183", "#4b8e6b", "#356a54"],
    "iron":      ["#c6c3dc", "#a29fbd", "#807d9e", "#5d5a7a"],
    "gold":      ["#fff3b4", "#ffd879", "#efb257", "#bf8343"],
    "amber":     ["#fffbe8", "#fff0b0", "#ffd77a", "#f7ae54"],
    "dimamber":  ["#b5a5a8", "#968793", "#776b7c", "#594f63"],
    "frost":     ["#d8ebff", "#b2d0fb", "#8cb0ec", "#6c8bcc"],
    "copper":    ["#ffb98c", "#ec9468", "#c8714f", "#94523e"],
    "ember":     ["#fffbd1", "#ffcf6e", "#ff8d5a", "#d4545a"],
    "ash":       ["#9d97a6", "#7f7989", "#625d6d", "#474353"],
    "cocoa":     ["#c08566", "#9a644c", "#784a3a", "#55342b"],
    "blush":     ["#ffd2dc", "#ffb3c4", "#f593ab", "#d97391"],
    "coal":      ["#6e6a80", "#545066", "#3d3a4d", "#2a2838"],
    "carrot":    ["#ffc27a", "#ffa055", "#f07f3f", "#c45e33"],
}.items()}

# ---------------------------------------------------------------- animation
NFRAMES = 6
STATE = {"frame": 0}
FRAMETIMES = [2, 3, 2, 2, 4, 2]   # ticks; irregular so it reads as a real flicker

def animated(fn):
    fn.animated = True
    return fn

def fr():
    return STATE["frame"]

def T(ramp, tone, a=255):
    tone = max(0, min(6, tone))
    r, g, b = RAMPS[ramp][tone]
    return (r, g, b, a)

SIDES = ("north", "south", "east", "west")

# ------------------------------------------------------------------- painters
# A painter is f(w, h, face, key) -> uint8 array (h, w, 4)

def _blank(w, h):
    return np.zeros((h, w, 4), np.uint8)

def solid(ramp, tone=2, bevel=True):
    def f(w, h, face, key):
        img = _blank(w, h)
        img[:, :] = T(ramp, tone)
        if bevel and face in SIDES and h > 2:
            img[0, :] = T(ramp, tone - 1)
            img[-1, :] = T(ramp, tone + 1)
        if face == "down":
            img[:, :] = T(ramp, tone + 1)
        return img
    return f

def _snow_px(img, x, y, face):
    img[y, x] = T("snow", 0 if (y // 2) % 3 else 1)

def snow():
    def f(w, h, face, key):
        img = _blank(w, h)
        for y in range(h):
            for x in range(w):
                tone = 0 if ((x + 2 * y) % 9) else 1
                if face == "up" and (y // 3) % 3 == 2 and (x + y) % 5 == 0:
                    tone = 2
                img[y, x] = T("snow", tone)
        if face in SIDES and h > 1:
            img[-1, :] = T("snow", 2)
        if face == "down":
            img[:, :] = T("snow", 3)
        return img
    return f

def wood(ramp="spruce", border=False, cap=0, up_snow=None, plank=3):
    """Planks with half-step tones, grain streaks and staggered butt joints.
    cap: rows of snow drifting over the top of side faces (and a snowy top)."""
    if up_snow is None:
        up_snow = cap > 0
    def f(w, h, face, key):
        rng = random.Random(key)
        img = _blank(w, h)
        if face == "up" and up_snow:
            return snow()(w, h, face, key)
        horiz = w >= h
        L, Tn = (w, h) if horiz else (h, w)
        off = rng.randrange(7)
        for t in range(Tn):
            pi = t // plank
            base = [2, 3, 2, 4][(pi + off) % 4] / 2 + 1.5  # 2.5 / 3 / 2.5 / 3.5
            base = int(round(base))
            joint = (7 + pi * 9 + off) % 13
            for l in range(L):
                tone = base
                if t % plank == 0:
                    tone -= 1
                if (l + pi * 5 + off) % 11 in (3, 4, 5, 6) and t % plank == 1:
                    tone += 1
                if L > 8 and l % 13 == joint:
                    tone += 1
                x, y = (l, t) if horiz else (t, l)
                img[y, x] = T(ramp, tone)
        if face == "down":
            img[:, :, :3] = (img[:, :, :3] * 0.8).astype(np.uint8)
        if border and w > 3 and h > 3:
            for (x, y) in [(x, 0) for x in range(w)] + [(x, h - 1) for x in range(w)] + \
                          [(0, y) for y in range(h)] + [(w - 1, y) for y in range(h)]:
                img[y, x] = T(ramp, 4)
        if cap and face in SIDES:
            for x in range(w):
                depth = cap + (1 if (x + rng.randrange(1) + len(key)) % 5 in (1, 2) else 0)
                for y in range(min(depth, h)):
                    _snow_px(img, x, y, face)
                if depth < h:
                    pass
        return img
    return f

def stripes(a="cranberry", b="cream", width=4, edge=None):
    def f(w, h, face, key):
        img = _blank(w, h)
        if face in SIDES and h <= 2 and edge:
            img[:, :] = T(edge, 3)
            return img
        for y in range(h):
            for x in range(w):
                col = a if (x // width) % 2 == 0 else b
                tone = 1 if (y % 6) else 2
                if face == "down":
                    tone = 3
                img[y, x] = T(col, tone)
        return img
    return f

def glow(ramp="amber", frame="iron", bars=True, flicker=True):
    R0 = [0.75, 0.82, 0.62, 0.78, 0.88, 0.68]
    R1 = [1.15, 1.2, 1.02, 1.12, 1.25, 1.08]
    def f(w, h, face, key):
        img = _blank(w, h)
        k = fr() if flicker else 0
        cx, cy = (w - 1) / 2, (h - 1) / 2 + (0.5 if k in (2, 5) else 0)
        for y in range(h):
            for x in range(w):
                d = abs(x - cx) / max(cx, 1) + abs(y - cy) / max(cy, 1)
                tone = 0 if d < R0[k] else (1 if d < R1[k] else 2)
                img[y, x] = T(ramp, tone)
        if frame and face in SIDES and w > 3 and h > 3:
            img[0, :] = img[-1, :] = T(frame, 4)
            img[:, 0] = img[:, -1] = T(frame, 4)
            if bars:
                img[h // 2, :] = T(frame, 3)
        return img
    return animated(f) if flicker and ramp != "dimamber" else f

def pine(ornaments=True, cap=2):
    cols = ["cranberry", "gold", "frost", "cranberry"]
    def f(w, h, face, key):
        img = _blank(w, h)
        if face == "up":
            return snow()(w, h, face, key)
        for y in range(h):
            for x in range(w):
                tone = 2
                if (x + 2 * (y % 3)) % 5 == 0:
                    tone = 1
                if (x - y) % 6 == 0:
                    tone = 3
                img[y, x] = T("pine", tone)
        if face in SIDES:
            if ornaments:
                for y in range(cap + 2, h - 1, 4):
                    for x in range((y * 3) % 5, w, 5):
                        c = cols[(x // 5 + y // 4) % len(cols)]
                        img[y, x] = T(c, 0)
                        if y + 1 < h:
                            img[y + 1, x] = T(c, 2)
            for x in range(w):
                d = cap + (1 if x % 4 in (1, 2) else 0)
                for y in range(min(d, h)):
                    _snow_px(img, x, y, face)
            img[-1, :] = T("pine", 4)
        if face == "down":
            img[:, :] = T("pine", 5)
        return img
    return f

def gift(color="cranberry", ribbon="gold"):
    def f(w, h, face, key):
        img = _blank(w, h)
        for y in range(h):
            for x in range(w):
                img[y, x] = T(color, 1 if (x + y) % 4 else 2)
        if face in SIDES:
            img[0, :] = T(color, 0)
            img[-1, :] = T(color, 3)
        if face != "down":
            cx = w // 2
            img[:, max(0, cx - 1):cx + 1] = T(ribbon, 1)
            if face == "up":
                cy = h // 2
                img[max(0, cy - 1):cy + 1, :] = T(ribbon, 1)
        else:
            img[:, :] = T(color, 4)
        return img
    return f

def mug(body="cream", band="cranberry"):
    def f(w, h, face, key):
        img = _blank(w, h)
        img[:, :] = T(body, 1)
        if face in SIDES:
            img[0, :] = T(body, 0)
            if h > 2:
                img[1, :] = T(band, 1)
            img[-1, :] = T(body, 3)
        if face == "up":
            img[:, :] = T("cocoa", 2)
            img[0, :] = img[-1, :] = T(body, 0)
            img[:, 0] = img[:, -1] = T(body, 0)
            if w >= 4 and h >= 4:
                img[1, 1] = T("snow", 0)   # marshmallow
        return img
    return f

FONT5 = {
    "M": ["10001", "11011", "10101", "10001", "10001"],
    "A": ["00100", "01010", "10001", "11111", "10001"],
    "R": ["11110", "10001", "11110", "10100", "10010"],
    "K": ["10010", "10100", "11000", "10100", "10010"],
    "E": ["11111", "10000", "11110", "10000", "11111"],
    "T": ["11111", "00100", "00100", "00100", "00100"],
    " ": ["000", "000", "000", "000", "000"],
}

def board(text=None, emblem=None, ramp="spruce", ink="cream", trim="gold"):
    """Wooden board with a gold trim; front/back faces carry pixel text or an emblem."""
    base = wood(ramp, plank=2)
    def f(w, h, face, key):
        img = base(w, h, face, key)
        if face not in ("north", "south") or w < 6 or h < 5:
            return img
        img[0, :] = img[-1, :] = T(trim, 2)
        img[:, 0] = img[:, -1] = T(trim, 2)
        if text:
            glyphs = [FONT5[c] for c in text]
            tw = sum(len(g[0]) + 1 for g in glyphs) - 1
            x0, y0 = (w - tw) // 2, (h - 5) // 2 + 1
            x = x0
            for g in glyphs:
                for gy, row in enumerate(g):
                    for gx, ch in enumerate(row):
                        if ch == "1" and 0 <= x + gx < w and 0 <= y0 + gy < h:
                            img[y0 + gy, x + gx] = T(ink, 0)
                            if y0 + gy + 1 < h - 1 and (gy == 4 or g[gy + 1][gx] == "0"):
                                img[y0 + gy + 1, x + gx] = T(ramp, 5)
                x += len(g[0]) + 1
        if emblem == "flake":
            cx, cy = w // 2, h // 2
            for d in range(-2, 3):
                for (x, y) in [(cx + d, cy), (cx, cy + d), (cx + d, cy + d), (cx + d, cy - d)]:
                    if 1 <= x < w - 1 and 1 <= y < h - 1:
                        img[y, x] = T("frost", 0 if abs(d) < 2 else 2)
        return img
    return f

def wheel():
    def f(w, h, face, key):
        img = _blank(w, h)
        if face not in ("north", "south"):
            img[:, :] = T("spruce", 4)
            return img
        cx, cy = (w - 1) / 2, (h - 1) / 2
        r = min(w, h) / 2
        for y in range(h):
            for x in range(w):
                d = math.hypot(x - cx, y - cy)
                if d > r:
                    continue
                if d > r - 1.2:
                    img[y, x] = T("iron", 3)
                elif d < 1.2:
                    img[y, x] = T("gold", 2)
                elif abs(x - cx) < 0.6 or abs(y - cy) < 0.6 or abs(abs(x - cx) - abs(y - cy)) < 0.6:
                    img[y, x] = T("spruce", 2)
        return img
    return f

# --------------------------------------------------------- card art (cutouts)
def art(rows, pal):
    """rows of chars; '.' transparent; pal maps char -> (ramp, tone[, alpha])"""
    def f(w, h, face, key):
        img = _blank(w, h)
        ah, aw = len(rows), len(rows[0])
        for y in range(h):
            for x in range(w):
                ch = rows[int(y * ah / h)][int(x * aw / w)]
                if ch != ".":
                    img[y, x] = T(*pal[ch])
        return img
    return f

def bulbs(lit=True, spacing=4):
    cols = ["amber", "cranberry", "frost", "gold", "blush"]
    def f(w, h, face, key):
        img = _blank(w, h)
        img[0, :] = T("pine", 3)
        for i, x in enumerate(range(1, w - 1, spacing)):
            c = cols[i % len(cols)]
            img[1, x] = T("iron", 3)
            dim = lit and (i * 2 + fr()) % 5 == 0
            for y in range(2, min(h, 4)):
                if not lit:
                    img[y, x] = T("iron", 3 if y == 2 else 4)
                else:
                    img[y, x] = T(c, (2 if dim else 0) if y == 2 else (3 if dim else 1))
        return img
    return animated(f) if lit else f

def flame():
    """8x10 flame; 6 frames sway, dip and stretch."""
    PROFILE = [1, 1, 2, 3, 3, 4, 5, 5, 4, 3]           # half-widths-ish per row, top->bottom
    SWAY = [0, 1, 1, 0, -1, -1]
    TOPCUT = [0, 1, 0, 2, 0, 1]
    def f(w, h, face, key):
        k = fr()
        img = _blank(w, h)
        rows = len(PROFILE)
        for y in range(h):
            r = int(y * rows / h)
            if r < TOPCUT[k]:
                continue
            half = PROFILE[r]
            shift = round(SWAY[k] * (1 - r / (rows - 1)) * 1.5)
            c = (w - 1) / 2 + shift
            for x in range(w):
                dx = abs(x - c)
                if dx > half / 2 + 0.6:
                    continue
                inner = dx < half / 2 - 0.9
                core = dx < half / 2 - 1.8 and r > 3
                if r == rows - 1:
                    img[y, x] = T("ember", 3)
                elif core:
                    img[y, x] = T("ember", 0)
                elif inner:
                    img[y, x] = T("ember", 1)
                else:
                    img[y, x] = T("ember", 2 + (1 if (x + k) % 3 == 0 else 0))
        return img
    return animated(f)

def star_card():
    def f(w, h, face, key):
        k = fr()
        img = _blank(w, h)
        rows = ["..a..", ".aba.", "abcba", ".aba.", "a...a"]
        for y in range(h):
            for x in range(w):
                ch = rows[int(y * 5 / h)][int(x * 5 / w)]
                if ch == "a":
                    img[y, x] = T("gold", 1 if k in (1, 4) else 2)
                elif ch == "b":
                    img[y, x] = T("gold", 0)
                elif ch == "c":
                    img[y, x] = T("amber", 0)
        return img
    return animated(f)

def embers():
    def f(w, h, face, key):
        k = fr()
        img = _blank(w, h)
        for y in range(h):
            for x in range(w):
                v = (x * 7 + y * 13 + k * 5) % 11
                img[y, x] = T("ember", 0 if v == 0 else 2 if v < 4 else 3 if v < 9 else 4)
        return img
    return animated(f)

def scallop(ramp="cranberry", alt="cream"):
    """Bunting with a soft scalloped edge, alternating colors."""
    def f(w, h, face, key):
        img = _blank(w, h)
        for x in range(w):
            seg = x // 4
            col = ramp if seg % 2 == 0 else alt
            lx = x % 4
            depth = h if lx in (1, 2) else h - 1
            for y in range(depth):
                img[y, x] = T(col, 1 if y < depth - 1 else 2)
        return img
    return f

def cookie():
    def f(w, h, face, key):
        img = _blank(w, h)
        img[:, :] = T("cocoa", 1)
        if face == "up":
            img[0, :] = img[-1, :] = T("snow", 1)
            img[:, 0] = img[:, -1] = T("snow", 1)
            if w > 2 and h > 2:
                img[h // 2, w // 2] = T("cranberry", 1)
        elif face in SIDES:
            img[0, :] = T("cocoa", 0)
        return img
    return f

def snowball(face_on=None):
    """Soft snow with lavender shading; optional cute face on the north side."""
    def f(w, h, face, key):
        img = _blank(w, h)
        for y in range(h):
            for x in range(w):
                edge = min(x, y, w - 1 - x, h - 1 - y)
                tone = 0 if edge >= 2 else 1 if edge == 1 else 2
                if face == "down":
                    tone = 3
                img[y, x] = T("snow", tone)
        if face == "north" and face_on == "face" and w >= 5 and h >= 4:
            if w >= 7:
                ex1, ey = w // 2 - 1, 2
            else:
                ex1, ey = (w - 1) // 2 - 1, max(1, h // 2 - 1)
            ex2 = w - 1 - ex1
            img[ey, ex1] = img[ey, ex2] = T("coal", 6)                 # eyes
            cy = ey + 2
            if cy < h and ex1 - 1 >= 0:
                img[cy, ex1 - 1] = img[cy, ex2 + 1] = T("blush", 1)      # rosy cheeks
        if face == "north" and face_on == "buttons" and h >= 4:
            for y in (h // 3, (2 * h) // 3):
                img[y, w // 2] = T("coal", 2)
        return img
    return f



def neutral_overlay(p, neutral=("cream", "snow", "gold", "coal", "blush", "iron")):
    """Keeps only the pixels drawn from neutral ramps; everything else becomes transparent."""
    keep = {RAMPS[r][t] for r in neutral for t in range(7)}
    def f(w, h, face, key):
        img = p(w, h, face, key).copy()
        rgb = img[..., :3]
        mask = np.zeros((h, w), bool)
        for c in keep:
            mask |= np.all(rgb == np.array(c, np.uint8), axis=-1)
        img[~mask, 3] = 0
        return img
    if getattr(p, "animated", False):
        f.animated = True
    return f

def pane(lit=True):
    """Lantern glass: opaque iron frame and transom, see-through warm (lit) or cool (unlit) glass."""
    def f(w, h, face, key):
        img = _blank(w, h)
        if face in ("up", "down"):
            img[:, :] = T("iron", 3)
            return img
        img[:, :] = T("amber", 1, 70) if lit else T("frost", 2, 105)
        if w > 4 and h > 4:
            for x in range(1, w - 1):
                if (x + 1) % 4 == 0:
                    img[1:h - 1, x][::3] = T("snow", 0, 120 if lit else 150)   # soft glint
            img[0, :] = img[-1, :] = T("iron", 4)
            img[:, 0] = img[:, -1] = T("iron", 4)
            img[(h * 2) // 3, :] = T("iron", 4)
        return img
    return f

def candle():
    def f(w, h, face, key):
        img = _blank(w, h)
        img[:, :] = T("cream", 0 if face == "up" else 1)
        if face in SIDES:
            img[0, :] = T("cream", 0)
            if h > 3:
                img[1, w // 2] = T("cream", 0)      # little wax drip
        if face == "up":
            img[h // 2, w // 2] = T("coal", 4)       # wick
        return img
    return f

def _fill_neutral(p, neutral=("cream", "snow", "gold", "coal", "blush", "iron")):
    """Painter output with neutral pixels swapped for the face's most common dyed color."""
    keep = {RAMPS[r][t] for r in neutral for t in range(7)}
    def f(w, h, face, key):
        img = p(w, h, face, key).copy()
        rgb = img[..., :3]
        mask = np.zeros((h, w), bool)
        for c in keep:
            mask |= np.all(rgb == np.array(c, np.uint8), axis=-1)
        rest = rgb[~mask & (img[..., 3] > 0)]
        if len(rest):
            vals, counts = np.unique(rest.reshape(-1, 3), axis=0, return_counts=True)
            rgb[mask] = vals[counts.argmax()]
        return img
    return f

def tinted(p):
    """Grayscale version of a painter, tinted in game by the item's dye color."""
    def f(w, h, face, key):
        img = p(w, h, face, key).astype(float)
        lum = img[..., :3] @ np.array([0.3, 0.55, 0.15])
        mx = max(lum.max(), 1)
        g = np.clip((lum / mx) ** 0.55 * 255, 0, 255)
        out = img.copy()
        out[..., 0] = out[..., 1] = out[..., 2] = g
        return out.astype(np.uint8)
    f.tint = True
    if getattr(p, "animated", False):
        f.animated = True
    return f

FONT3 = {
    "A": ["010", "101", "111", "101", "101"], "C": ["011", "100", "100", "100", "011"],
    "E": ["111", "100", "110", "100", "111"], "F": ["111", "100", "110", "100", "100"],
    "G": ["011", "100", "101", "101", "011"], "I": ["111", "010", "010", "010", "111"],
    "O": ["010", "101", "101", "101", "010"], "R": ["110", "101", "110", "101", "101"],
    "S": ["011", "100", "010", "001", "110"], "T": ["111", "010", "010", "010", "010"],
}

def chalkboard(text, side="north"):
    def f(w, h, face, key):
        img = _blank(w, h)
        if face not in ("north", "south"):
            img[:, :] = T("oak", 2)          # plain wooden edges, no lettering bleed
            return img
        img[:, :] = T("coal", 2)
        if w > 4 and h > 4:
            img[0, :] = img[-1, :] = T("oak", 2)
            img[:, 0] = img[:, -1] = T("oak", 2)
        if face == side:
            tw = len(text) * 4 - 1
            x0, y0 = (w - tw) // 2, max(1, (h - 5) // 2 - 1)
            for n, ch in enumerate(text):
                for gy, row in enumerate(FONT3[ch]):
                    for gx, c in enumerate(row):
                        if c == "1" and 0 <= x0 + n * 4 + gx < w and y0 + gy < h:
                            img[y0 + gy, x0 + n * 4 + gx] = T("cream", 0)
            yy = y0 + 7
            if yy < h - 1:
                for x in range(2, w - 2):
                    if x % 3 != 0:
                        img[yy, x] = T(["blush", "frost", "gold"][(x // 3) % 3], 1)
        return img
    return f

def diag(a="cranberry", b="snow", width=2):
    def f(w, h, face, key):
        img = _blank(w, h)
        for y in range(h):
            for x in range(w):
                c = a if ((x + y) // width) % 2 == 0 else b
                img[y, x] = T(c, 1)
        return img
    return f

def gingerbread():
    def f(w, h, face, key):
        img = _blank(w, h)
        img[:, :] = T("cocoa", 1)
        if face in SIDES:
            img[0, :] = T("snow", 0)
            for x in range(0, w, 2):
                img[1, x] = T("snow", 0)
            if face == "north" and w >= 8 and h >= 5:
                cx = w // 2
                img[h - 4:h, cx - 1:cx + 1] = T("cranberry", 2)
                img[2:4, 1:3] = T("amber", 1); img[2:4, w - 3:w - 1] = T("amber", 1)
            elif face != "north" and w >= 6 and h >= 5:
                img[2:4, w // 2 - 1:w // 2 + 1] = T("amber", 1)
            for x in range(1, w, 3):
                img[-1, x] = T(["blush", "pine", "gold"][x % 3], 0)
        return img
    return f

def staves():
    def f(w, h, face, key):
        img = _blank(w, h)
        if face in ("up", "down"):
            img[:, :] = T("oak", 2 if face == "up" else 4)
            if face == "up":
                img[0, :] = img[-1, :] = T("oak", 4); img[:, 0] = img[:, -1] = T("oak", 4)
            return img
        for x in range(w):
            for y in range(h):
                img[y, x] = T("oak", 1 + (x // 3) % 2 + (1 if x % 3 == 0 else 0))
        for y in (2, h - 3):
            if 0 <= y < h:
                img[y, :] = T("iron", 3)
        return img
    return f

def logs(tone=0):
    def f(w, h, face, key):
        img = _blank(w, h)
        if face in ("east", "west"):
            cx, cy = (w - 1) / 2, (h - 1) / 2 + tone * 0
            for y in range(h):
                for x in range(w):
                    d = max(abs(x - cx), abs(y - cy))
                    img[y, x] = T("oak", 0 if d < 0.8 else 1 if d < 1.6 else 3) if d < max(cx, cy) - 0.4 else T("spruce", 3)
            return img
        for y in range(h):
            for x in range(w):
                img[y, x] = T("spruce", 2)
                if x % 3 == 0 and (y + x // 3) % 3 != 0:
                    img[y, x] = T("spruce", 3)
                if (x * 5 + y * 7) % 17 == 0:
                    img[y, x] = T("spruce", 1)
        if face == "up":
            img[0, :] = T("snow", 0)
        return img
    return f

def bauble_top():
    cols = ["cranberry", "frost", "gold", "pine", "blush"]
    def f(w, h, face, key):
        if face != "up":
            return wood("oak", border=True)(w, h, face, key)
        img = _blank(w, h)
        img[:, :] = T("oak", 4)
        for y in range(1, h - 1, 3):
            for x in range(1 + (y // 3) % 2, w - 1, 3):
                c = cols[(x + y) % len(cols)]
                img[y:y + 2, x:x + 2] = T(c, 1)
                img[y, x] = T(c, 0)
        img[0, :] = img[-1, :] = T("oak", 2); img[:, 0] = img[:, -1] = T("oak", 2)
        return img
    return f

def globe_glass():
    def f(w, h, face, key):
        img = _blank(w, h)
        img[:, :] = T("frost", 1, 62)
        for y in range(h):
            for x in range(w):
                if (x * 5 + y * 3) % 7 == 0:
                    img[y, x] = T("snow", 0, 235)
        if face in SIDES and w > 2:
            img[1:min(h, 4), 1] = T("snow", 0, 170)
        return img
    return f

def plush(face_on=False, belly=False, ear=False):
    def f(w, h, face, key):
        img = _blank(w, h)
        for y in range(h):
            for x in range(w):
                img[y, x] = T("cocoa", 1 + ((x + y) % 4 == 0))
        if belly and face == "north" and w >= 5 and h >= 4:
            cx, cy = (w - 1) / 2, (h - 1) / 2 + 0.5
            for y in range(h):
                for x in range(w):
                    if ((x - cx) / (w * 0.32)) ** 2 + ((y - cy) / (h * 0.36)) ** 2 <= 1:
                        img[y, x] = T("cream", 1)
        if ear and face == "north" and w >= 1:
            img[h // 2:, :] = T("blush", 1)
        if face_on and face == "north" and w >= 5 and h >= 4:
            img[:, :] = T("cocoa", 1)
            ex1 = (w - 1) // 2 - 1
            ex2 = w - 1 - ex1
            ey = 2 if h >= 6 else 1
            img[ey, ex1] = img[ey, ex2] = T("coal", 6)              # button eyes
            if ex1 - 1 >= 0 and ey + 1 < h:
                img[ey + 1, ex1 - 1] = img[ey + 1, ex2 + 1] = T("blush", 0)   # soft cheeks
        return img
    return f

def flags():
    """Triangle pennants: every other flag takes the dye, the rest stay cream."""
    def f(w, h, face, key):
        img = _blank(w, h)
        img[0, :] = T("cream", 3)
        for x0 in range(0, w - 3, 5):
            dyed = (x0 // 5) % 2 == 0
            for y in range(1, h):
                half = (h - y) * 2.2 / h
                for x in range(x0, x0 + 5):
                    if abs(x - (x0 + 2)) <= half and x < w:
                        img[y, x] = T("frost", 1 if y < h - 2 else 2) if dyed else T("cream", 0 if y < h - 2 else 1)
        return img
    return f

def boot():
    """Skate boot: dyed leather with cream cuff, laces and sole."""
    def f(w, h, face, key):
        img = _blank(w, h)
        img[:, :] = T("frost", 1)
        if face in SIDES:
            img[0:2, :] = T("cream", 0)
            img[-1, :] = T("cream", 2)
            if face == "north" and w >= 3:
                for y in range(3, h - 1, 2):
                    img[y, w // 2 - 1:w // 2 + 1] = T("cream", 1)
        if face == "up":
            img[:, :] = T("cream", 1)
        return img
    return f

def plate():
    def f(w, h, face, key):
        img = _blank(w, h)
        img[:, :] = T("cream", 0)
        if face == "up":
            img[0, :] = img[-1, :] = T("frost", 2); img[:, 0] = img[:, -1] = T("frost", 2)
        elif face in SIDES:
            img[:, :] = T("frost", 2)
        return img
    return f

FLAME = art([
    "...a....",
    "...aa...",
    "..aba...",
    "..abba..",
    ".abbba..",
    ".abcbba.",
    "abccbba.",
    "abcccba.",
    ".bcccb..",
    "..ddd...",
], {"a": ("ember", 2), "b": ("ember", 1), "c": ("ember", 0), "d": ("ember", 4)})

STAR = art([
    "..a..",
    ".aba.",
    "abcba",
    ".aba.",
    "a...a",
], {"a": ("gold", 2), "b": ("gold", 0), "c": ("amber", 0)})

BOW = art([
    "aa..aa",
    "abaaba",
    ".abba.",
    ".a..a.",
], {"a": ("gold", 2), "b": ("gold", 0)})

WREATH = art([
    "..aaaa..",
    ".abaaba.",
    "aa....aa",
    "ab....ca",
    "aa....aa",
    ".aba.ab.",
    "..arra..",
    "...rr...",
], {"a": ("pine", 2), "b": ("pine", 0), "c": ("cranberry", 1), "r": ("cranberry", 1)})

STEAM = art([
    ".a.",
    "a..",
    ".a.",
    "..a",
    ".a.",
], {"a": ("snow", 1, 150)})

def _light(tile, face):
    """Baked lighting: soft top-down gradient, contact shadow, crisp edges. Gives blocky parts volume."""
    t = tile.astype(float)
    h, w = t.shape[:2]
    fac = np.ones((h, w))
    if face in SIDES:
        if h > 1:
            ys = np.arange(h) / (h - 1)
            fac *= (1.10 - 0.32 * ys ** 1.2)[:, None]
        if h > 3:
            fac[0, :] *= 1.12
            fac[1, :] *= 1.04
            fac[-1, :] *= 0.82
        if w > 3:
            fac[:, 0] *= 0.9
            fac[:, -1] *= 0.9
    elif face == "up":
        if w > 3 and h > 3:
            fac[0, :] *= 0.93; fac[-1, :] *= 0.93; fac[:, 0] *= 0.93; fac[:, -1] *= 0.93
        fac *= 1.04
    t[..., :3] = np.clip(t[..., :3] * fac[..., None], 0, 255)
    return t.astype(np.uint8)


# ------------------------------------------------------------------ model
class Model:
    def __init__(self, name, floor=0, dye=None):
        self.name, self.floor, self.elements = name, floor, []
        self.dye = dye  # default dye color (r,g,b) when the model has tinted faces

    def box(self, frm, to, mat, faces=None, rot=None, emit=0, over=None, res=1):
        """over: {face: painter} overrides; faces: subset of faces to keep."""
        fs = faces or ("north", "south", "east", "west", "up", "down")
        e = {"from": list(map(float, frm)), "to": list(map(float, to)),
             "faces": {f: (over or {}).get(f, mat) for f in fs}, "emit": emit, "res": res}
        if rot:
            axis, ang, org = rot
            e["rotation"] = {"angle": ang, "axis": axis, "origin": list(map(float, org))}
        self.elements.append(e)
        return e

    def dyebox(self, frm, to, painter, rot=None, neutral=None, card=False, res=1):
        """Dyeable part with a neutral base: a tinted element plus an untinted overlay
        (0.15 px larger) that keeps ribbons, cuffs and cream stripes their own color."""
        kw = {"neutral": neutral} if neutral else {}
        ov = neutral_overlay(painter, **kw)
        base_p = _fill_neutral(painter, **kw)
        if card:
            self.card(frm, to, tinted(base_p), rot=rot, res=res)
            flat = [i for i in range(3) if frm[i] == to[i]][0]
            f2, t2 = list(frm), list(to)
            f2[flat] -= 0.15; t2[flat] -= 0.15
            self.card(f2, t2, ov, rot=rot, res=res)["overlay"] = True
        else:
            self.box(frm, to, tinted(base_p), rot=rot, res=res)
            d = 0.15
            self.box([v - d for v in frm], [v + d for v in to], ov, rot=rot, res=res)["overlay"] = True

    def lantern(self, lo, hi, lit, candle_w=None):
        """Glass lantern body with a candle and (when lit) a crossed, flickering flame.
        Inner parts come first so they draw before the translucent glass."""
        (x0, y0, z0), (x1, y1, z1) = lo, hi
        cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
        W, H = x1 - x0, y1 - y0
        cw = candle_w or max(1.25, round(W * 0.3 * 4) / 4)
        chh = max(1.0, round(H * 0.28 * 4) / 4)
        self.box([cx - cw / 2, y0, cz - cw / 2], [cx + cw / 2, y0 + chh, cz + cw / 2], candle(), res=2,
                 faces=("north", "south", "east", "west", "up"))
        if lit:
            fw = min(W * 0.62, 3.5)
            fh = min(H - chh - 0.4, fw * 1.6)
            for a in (45, -45):
                self.card([cx - fw / 2, y0 + chh, cz], [cx + fw / 2, y0 + chh + fh, cz], flame(),
                          rot=("y", a, [cx, y0 + chh, cz]), emit=15, res=3)
        self.box(lo, hi, pane(lit), res=2)

    def card(self, frm, to, painter, rot=None, emit=0, res=1):
        """Zero-thickness card. The flat axis is the one with from == to."""
        flat = [i for i in range(3) if frm[i] == to[i]]
        assert len(flat) == 1, "card needs exactly one flat axis"
        fs = {0: ("east", "west"), 1: ("up", "down"), 2: ("north", "south")}[flat[0]]
        e = self.box(frm, to, painter, faces=fs, rot=rot, emit=emit, res=res)
        e["card"] = True
        return e

    # ---------------------------------------------------------- checks
    def check(self):
        import zcheck
        zcheck.fix(self)                                     # no coplanar faces (z-fighting) in shipped models
        n = len(self.elements)
        assert n <= 14, f"{self.name}: {n} elements (cap 14)"
        for e in self.elements:
            for v in e["from"] + e["to"]:
                assert -16.05 <= v <= 32.05, f"{self.name}: coord {v} out of -16..32"
            r = e.get("rotation")
            if r:
                assert r["angle"] in (-45, -22.5, 0, 22.5, 45), f"{self.name}: angle {r['angle']}"
        return n

    def bounds(self):
        a = np.array([e["from"] for e in self.elements] + [e["to"] for e in self.elements])
        return a.min(0), a.max(0)

    # ---------------------------------------------------------- texture
    @staticmethod
    def face_dims(e, f):
        d = np.array(e["to"]) - np.array(e["from"])
        w, h = {"north": (d[0], d[1]), "south": (d[0], d[1]), "east": (d[2], d[1]),
                "west": (d[2], d[1]), "up": (d[0], d[2]), "down": (d[0], d[2])}[f]
        r = e.get("res", 1)
        return max(1, int(math.ceil(w * r - 1e-6))), max(1, int(math.ceil(h * r - 1e-6)))

    def is_animated(self):
        return any(getattr(p, "animated", False) for e in self.elements for p in e["faces"].values())

    def bake(self, frame=0):
        STATE["frame"] = frame
        items = []
        for i, e in enumerate(self.elements):
            for f, painter in e["faces"].items():
                w, h = self.face_dims(e, f)
                items.append((i, f, w, h, painter))
        order = sorted(range(len(items)), key=lambda k: (-items[k][3], -items[k][2]))
        for S in (32, 64, 128, 256, 512, 1024, 2048):
            pos, x, y, rowh, ok = {}, 0, 0, 0, True
            for k in order:
                _, _, w, h, _ = items[k]
                if x + w > S:
                    x, y, rowh = 0, y + rowh, 0
                if y + h > S or w > S:
                    ok = False
                    break
                pos[k] = (x, y)
                x += w
                rowh = max(rowh, h)
            if ok:
                break
        atlas = np.zeros((S, S, 4), np.uint8)
        self.uv = {}
        for k, (i, f, w, h, painter) in enumerate(items):
            px, py = pos[k]
            tile = painter(w, h, f, f"{self.name}-{i}-{f}")
            e = self.elements[i]
            if not e.get("card") and not e.get("overlay") and not e.get("flat") and e["emit"] < 10:
                tile = _light(tile, f)
            atlas[py:py + h, px:px + w] = tile
            self.uv[(i, f)] = (px, py, px + w, py + h)
        self.atlas, self.S = atlas, S
        return atlas

    # ---------------------------------------------------------- export
    def display(self):
        lo, hi = self.bounds()
        ext = (hi - lo).max()
        c = (lo + hi) / 2
        def tr(rx, ry, fit):
            s = min(4.0, fit / ext)
            R = _rx(rx) @ _ry(ry)
            t = -(R @ ((c - 8) * s))
            t = np.clip(t, -80, 80)
            return {"rotation": [rx, ry, 0], "translation": [round(float(v), 3) for v in t],
                    "scale": [round(s, 4)] * 3}
        return {"gui": tr(30, 225, 15.0), "ground": tr(0, 0, 8.0), "fixed": tr(0, 180, 14.0),
                "thirdperson_righthand": tr(75, 45, 6.0), "firstperson_righthand": tr(0, 45, 7.0),
                "head": tr(0, 0, 14.0)}

    def to_json(self, tex):
        els = []
        for i, e in enumerate(self.elements):
            je = {"from": e["from"], "to": e["to"]}
            if "rotation" in e:
                je["rotation"] = e["rotation"]
            if e["emit"]:
                je["light_emission"] = e["emit"]
            faces = {}
            for f in e["faces"]:
                x1, y1, x2, y2 = self.uv[(i, f)]
                k = 16 / self.S
                faces[f] = {"uv": [round(x1 * k, 4), round(y1 * k, 4), round(x2 * k, 4), round(y2 * k, 4)],
                            "texture": "#0"}
                if getattr(e["faces"][f], "tint", False):
                    faces[f]["tintindex"] = 0
            je["faces"] = faces
            els.append(je)
        return {"credit": "Mistbloom Studios", "texture_size": [self.S, self.S],
                "textures": {"0": tex, "particle": tex}, "elements": els,
                "display": self.display()}

    def export(self, root, variant=None):
        vid = self.name if variant is None else variant
        self.bake()
        tdir = os.path.join(root, "assets", NS, "textures", "furniture")
        mdir = os.path.join(root, "assets", NS, "models", "furniture")
        idir = os.path.join(root, "assets", NS, "items")
        for d in (tdir, mdir, idir):
            os.makedirs(d, exist_ok=True)
        if self.is_animated():
            frames = [self.bake(k).copy() for k in range(NFRAMES)]
            self.bake(0)
            Image.fromarray(np.concatenate(frames, 0)).save(os.path.join(tdir, vid + ".png"))
            with open(os.path.join(tdir, vid + ".png.mcmeta"), "w") as fh:
                json.dump({"animation": {"interpolate": False, "frames": [
                    {"index": i, "time": t} for i, t in enumerate(FRAMETIMES)]}}, fh, indent=1)
        else:
            Image.fromarray(self.atlas).save(os.path.join(tdir, vid + ".png"))
        with open(os.path.join(mdir, vid + ".json"), "w") as fh:
            json.dump(self.to_json(f"{NS}:furniture/{vid}"), fh, indent=1)
        with open(os.path.join(idir, vid + ".json"), "w") as fh:
            model = {"type": "minecraft:model", "model": f"{NS}:furniture/{vid}"}
            if self.dye:
                r, g, b = self.dye
                model["tints"] = [{"type": "minecraft:dye", "default": (r << 16) | (g << 8) | b}]
            json.dump({"model": model}, fh, indent=1)
        return vid


def _rx(a):
    t = math.radians(a); c, s = math.cos(t), math.sin(t)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])

def _ry(a):
    t = math.radians(a); c, s = math.cos(t), math.sin(t)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])

def _rz(a):
    t = math.radians(a); c, s = math.cos(t), math.sin(t)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


_NORMALS = {"north": np.array([0, 0, -1.]), "south": np.array([0, 0, 1.]), "east": np.array([1., 0, 0]),
            "west": np.array([-1., 0, 0]), "up": np.array([0, 1., 0]), "down": np.array([0, -1., 0])}

def _face_corners(e, f):
    (x0, y0, z0), (x1, y1, z1) = e["from"], e["to"]
    P = lambda x, y, z: np.array([x, y, z], float)
    return {
        "north": [P(x1, y1, z0), P(x0, y1, z0), P(x0, y0, z0), P(x1, y0, z0)],
        "south": [P(x0, y1, z1), P(x1, y1, z1), P(x1, y0, z1), P(x0, y0, z1)],
        "east":  [P(x1, y1, z1), P(x1, y1, z0), P(x1, y0, z0), P(x1, y0, z1)],
        "west":  [P(x0, y1, z0), P(x0, y1, z1), P(x0, y0, z1), P(x0, y0, z0)],
        "up":    [P(x0, y1, z0), P(x1, y1, z0), P(x1, y1, z1), P(x0, y1, z1)],
        "down":  [P(x0, y0, z1), P(x1, y0, z1), P(x1, y0, z0), P(x0, y0, z0)],
    }[f]

def render(self, ppu=6, cam=(-0.62, 0.62, -1.0), frame=0, dye=None):
    self.bake(frame)
    c = np.array(cam, float); c /= np.linalg.norm(c)
    fwd = -c
    right = np.cross(fwd, [0, 1, 0]); right /= np.linalg.norm(right)
    up = np.cross(right, fwd)
    quads = []
    for i, e in enumerate(self.elements):
        for f in e["faces"]:
            corners = _face_corners(e, f)
            if "rotation" in e:
                r = e["rotation"]
                M = {"x": _rx, "y": _ry, "z": _rz}[r["axis"]](r["angle"])
                o = np.array(r["origin"])
                corners = [M @ (p - o) + o for p in corners]
                n = M @ _NORMALS[f]
            else:
                n = _NORMALS[f]
            if len(e["faces"]) != 2 and np.dot(n, c) <= 0:
                continue
            quads.append((corners, i, f, e["emit"]))
    pts = np.array([p for q in quads for p in q[0]])
    sx, sy = pts @ right, -(pts @ up)
    minx, miny = sx.min(), sy.min()
    W = int(math.ceil((sx.max() - minx) * ppu)) + 4
    H = int(math.ceil((sy.max() - miny) * ppu)) + 4
    img = np.zeros((H, W, 4), np.uint8)
    zb = np.full((H, W), np.inf)
    shade = {"up": 1.0, "down": 0.5, "north": 0.8, "south": 0.8, "east": 0.62, "west": 0.62}
    dyec = np.array(dye or self.dye or (255, 255, 255), float) / 255
    for pass_ in (0, 1):
        for corners, i, f, emit in quads:
            P = np.array([[(p @ right - minx) * ppu + 2, (-(p @ up) - miny) * ppu + 2, p @ fwd] for p in corners])
            o, e1, e2 = P[0], P[1] - P[0], P[3] - P[0]
            A = np.array([[e1[0], e2[0]], [e1[1], e2[1]]])
            if abs(np.linalg.det(A)) < 1e-9:
                continue
            Ai = np.linalg.inv(A)
            x0, x1 = int(max(0, P[:, 0].min())), int(min(W, P[:, 0].max() + 1))
            y0, y1 = int(max(0, P[:, 1].min())), int(min(H, P[:, 1].max() + 1))
            if x1 <= x0 or y1 <= y0:
                continue
            gx, gy = np.meshgrid(np.arange(x0, x1) + 0.5, np.arange(y0, y1) + 0.5)
            dx, dy = gx - o[0], gy - o[1]
            a = Ai[0, 0] * dx + Ai[0, 1] * dy
            b = Ai[1, 0] * dx + Ai[1, 1] * dy
            m = (a >= 0) & (a <= 1) & (b >= 0) & (b <= 1)
            z = o[2] + a * e1[2] + b * e2[2]
            u1, v1, u2, v2 = self.uv[(i, f)]
            tx = np.clip((u1 + a * (u2 - u1)).astype(int), u1, u2 - 1)
            ty = np.clip((v1 + b * (v2 - v1)).astype(int), v1, v2 - 1)
            tex = self.atlas[ty, tx]
            al = tex[..., 3]
            m &= (al >= 200) if pass_ == 0 else ((al > 8) & (al < 200))
            sub = zb[y0:y1, x0:x1]
            m &= z < sub - 1e-6
            if not m.any():
                continue
            k = 1.0 if emit >= 10 else shade[f]
            col = tex[..., :3].astype(float) * k
            if getattr(self.elements[i]["faces"][f], "tint", False):
                col = col * dyec
            region = img[y0:y1, x0:x1]
            if pass_ == 0:
                region[m, :3] = np.clip(col[m], 0, 255).astype(np.uint8)
                region[m, 3] = 255
                sub[m] = z[m]
            else:
                aa = (al[m] / 255.0)[:, None]
                base = region[m, :3].astype(float)
                empty = (region[m, 3] == 0)[:, None]
                mixed = np.where(empty, col[m], col[m] * aa + base * (1 - aa))
                region[m, :3] = np.clip(mixed, 0, 255).astype(np.uint8)
                region[m, 3] = np.maximum(region[m, 3], al[m])
    return Image.fromarray(img)

Model.render = render
