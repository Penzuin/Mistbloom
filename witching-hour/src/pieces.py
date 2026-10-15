"""Witching Hour - six witchy cosmetics for HMCCosmetics by Mistbloom Studios.

Things a witch would actually own, so they work all year and feel right at Halloween:
a moonlit witch hat, a candle crown, a ghost in a lantern, a grimoire, a little wisp
that floats beside you, and a broom with a lantern hanging off it.

Authored in player pixels on the head (head = 1..9 on every axis, front = low z).
Every model stays under 15 elements.
"""
import math
from engine import Model, T, _blank, fr, RAMPS, _ramp7, animated

K = 2  # texels per pixel

RAMPS.update({k: _ramp7(v) for k, v in {
    "witch":  ["#5b4a8c", "#3f3270", "#2b2152", "#1a1434"],   # hat fabric, deep violet
    "band":   ["#e6d6ff", "#bfa6ee", "#9278cf", "#6450a0"],
    "brass":  ["#fff1c2", "#f2c97d", "#c8903f", "#7d5523"],
    "wax":    ["#fbf6ff", "#e6dcfa", "#c6b6ec", "#9a86c8"],
    "flame":  ["#fffbe6", "#ffe6a0", "#ffb84d", "#e0742c"],
    "ghost":  ["#ffffff", "#eef2ff", "#cfd8fb", "#a6b2e8"],
    "iron":   ["#7a7590", "#57526e", "#3b3750", "#25222f"],
    "pane":   ["#f2fbff", "#cfe9fb", "#a4cdee", "#6f9fd2"],
    "page":   ["#fffaf0", "#f4e8d2", "#e2cfae", "#b89e78"],
    "cover":  ["#6e4a8a", "#52356e", "#3a2452", "#241536"],
    "wood":   ["#8a6a5a", "#6a4e44", "#4c3631", "#30211f"],
    "straw":  ["#fff0b8", "#f2d27a", "#d4a64e", "#9a7230"],
    "wispr":  ["#ffffff", "#ebe6ff", "#cdc3f6", "#a194dc"],
    "orb":    ["#ffffff", "#fff6d6", "#ffe39a", "#f2c06a"],
    "amethyst": ["#f0dcff", "#c79cf0", "#9a66d6", "#6a3ea8"],
}.items()})


def hsh(x, y, s=0):
    return ((x * 73856093) ^ (y * 19349663) ^ (s * 83492791)) & 0xFFFF


def face_tone(face, base):
    return base + {"up": -1, "down": 2, "north": 0, "south": 0, "east": 1, "west": 1}[face]


def nm(m, *names):
    for e, n in zip(m.elements[-len(names):], names):
        e["name"] = n


# ------------------------------------------------------------------ painters
def fabric(ramp, base=2, stars=0.0, seed=1, rim=True, stitch=None):
    """Woven cloth: soft dither, darker edge line, optional tiny gold stars and a stitch row."""
    def f(W, H, face, key):
        img = _blank(W, H)
        t0 = face_tone(face, base)
        for y in range(H):
            for x in range(W):
                n = hsh(x, y, seed + len(face))
                t = t0 + (1 if n % 11 == 0 else 0) - (1 if n % 17 == 0 else 0)
                if rim and W > 3 and H > 3 and (x in (0, W - 1) or y in (0, H - 1)):
                    t += 1
                if stitch is not None and face != "up" and face != "down" and y == int(H * stitch) and x % 3 != 2:
                    t -= 2
                img[y, x] = T(ramp, t)
                if stars and face != "down" and 0 < x < W - 1 and 0 < y < H - 1 and n % int(1 / stars) == 0:
                    img[y, x] = T("brass", 1)
        return img
    return f


def round_fabric(ramp, base=2, stars=0.0, seed=1):
    """Cloth on a cone tier: darker towards the corners so the box reads round, rare 1-texel stars."""
    def f(W, H, face, key):
        img = _blank(W, H)
        t0 = face_tone(face, base)
        for y in range(H):
            for x in range(W):
                n = hsh(x, y, seed + len(face))
                t = t0
                if face in SIDES4:
                    e = abs((x + 0.5) / W * 2 - 1)
                    t += 2 if e > 0.8 else (1 if e > 0.5 else 0)
                    if y == H - 1:
                        t += 1
                elif face == "up":
                    t = base + 1
                t += 1 if n % 13 == 0 else 0
                img[y, x] = T(ramp, t)
                if stars and face in SIDES4 and 0 < x < W - 1 and 0 < y < H - 1 and n % int(1 / stars) == 0:
                    img[y, x] = T("brass", 0)
        return img
    return f


def disc(ramp, base=2, seed=1):
    """Round brim: a disc on the top and bottom faces, only the middle of each side drawn."""
    def f(W, H, face, key):
        img = _blank(W, H)
        if face in ("up", "down"):
            cx, cy, r = (W - 1) / 2, (H - 1) / 2, min(W, H) / 2 - 0.2
            for y in range(H):
                for x in range(W):
                    d = math.hypot(x - cx, y - cy) / r
                    if d <= 1:
                        t = base + (1 if face == "down" else 0) + (1 if d > 0.88 else 0) - (1 if 0.6 < d < 0.8 and face == "up" else 0)
                        t += 1 if (d < 0.85 and hsh(x, y, seed) % 15 == 0) else 0
                        img[y, x] = T(ramp, t)
        else:
            for y in range(H):
                for x in range(W):
                    if abs((x + 0.5) / W - 0.5) < 0.07:
                        img[y, x] = T(ramp, base + 2)
        return img
    return f


SIDES4 = ("north", "south", "east", "west")


def metal(ramp="brass", base=1, engrave=False):
    def f(W, H, face, key):
        img = _blank(W, H)
        t0 = face_tone(face, base)
        for y in range(H):
            for x in range(W):
                t = t0
                if W > 2 and H > 2 and (x in (0, W - 1) or y in (0, H - 1)):
                    t += 2
                elif y == 1 and face != "down":
                    t -= 1
                if engrave and H > 3 and face in ("north", "south", "east", "west") and y == H // 2 and x % 4 in (1, 2):
                    t += 2
                img[y, x] = T(ramp, t)
        return img
    return f


def wax(seed=0):
    """Candle wax with drips running down from the top edge."""
    def f(W, H, face, key):
        img = _blank(W, H)
        t0 = face_tone(face, 1)
        drips = [(hsh(i, seed, 7) % max(1, H - 2)) + 1 for i in range(W)]
        for y in range(H):
            for x in range(W):
                t = t0 + (1 if y > H * 0.7 else 0)
                if face in ("north", "south", "east", "west"):
                    if y < drips[x] and (x % 3 != 1 or y < 2):
                        t = t0 - 1
                    if y == drips[x]:
                        t = t0 - 2
                    if x == 0 or x == W - 1:
                        t += 1
                elif face == "up":
                    t = 2 if 0 < x < W - 1 and 0 < y < H - 1 else 0
                img[y, x] = T("wax", t)
        return img
    return f


def flame(seed=0):
    """Small candle flame: pale core, gold body, amber base; the tip flickers."""
    def f(W, H, face, key):
        k = (fr() + seed) % 6
        img = _blank(W, H)
        top = [0, 1, 0, 1, 1, 0][k]
        for y in range(H):
            for x in range(W):
                if y < top:
                    continue
                if y == top and W > 1 and x != (W // 2 if k % 2 else (W - 1) // 2):
                    continue
                if face in ("up", "down"):
                    img[y, x] = T("flame", 1)
                    continue
                r = (y - top) / max(1, H - 1 - top)
                t = 0 if r < 0.35 else (1 if r < 0.7 else 2)
                if y == H - 1:
                    t = 3
                img[y, x] = T("flame", t)
        return img
    return animated(f)


def art(rows, pal, back=None):
    """Pixel art scaled onto a face; '.' is clear (or the back painter shows through)."""
    def f(W, H, face, key):
        img = back(W, H, face, key) if back else _blank(W, H)
        ah, aw = len(rows), len(rows[0])
        for y in range(H):
            for x in range(W):
                ch = rows[min(ah - 1, int(y * ah / H))][min(aw - 1, int(x * aw / W))]
                if ch != "." and ch in pal:
                    img[y, x] = T(*pal[ch]) if len(pal[ch]) != 4 else pal[ch]
        return img
    return f


def glow_pulse(ramp, tone=1, alpha=255):
    def f(W, H, face, key):
        img = _blank(W, H)
        t = tone + (0 if fr() in (0, 1, 2) else 1)
        img[:, :] = T(ramp, t, alpha)
        return img
    return animated(f)


MOON = ["..aab.",
        ".ab...",
        "ab....",
        "ab....",
        ".ab...",
        "..aab."]


def moon_card():
    pal = {"a": ("moon", 0), "b": ("moon", 2)}
    rows = MOON
    def f(W, H, face, key):
        img = art(rows, pal)(W, H, face, key)
        if fr() in (3, 4):
            img[img[..., 3] > 0] = (255, 252, 230, 255)
        return img
    return animated(f)


STAR = ["..a..", "..a..", "aabaa", "..a..", "..a.."]


def star_card():
    def f(W, H, face, key):
        k = fr()
        rows = STAR if k not in (2, 5) else [".....", "..a..", ".aba.", "..a..", "....."]
        return art(rows, {"a": ("brass", 1), "b": ("moon", 0)})(W, H, face, key)
    return animated(f)


# ------------------------------------------------------------------ 1. witch hat
def witch_hat():
    m = Model("witch_hat", "hat", scale=1.25)
    m.b((-5, 8.7, -5), (15, 9.3, 15), disc("witch", 2, seed=3), tpp=K)
    nm(m, "brim")
    tiers = [(8.4, 9.3, 11.3, 5.0), (7.2, 11.3, 13.1, 5.3), (6.0, 13.1, 14.7, 5.7),
             (4.8, 14.7, 16.1, 6.1), (3.6, 16.1, 17.3, 6.6)]
    for i, (w, y0, y1, zc) in enumerate(tiers):
        m.b((5 - w / 2, y0, zc - w / 2), (5 + w / 2, y1, zc + w / 2),
            round_fabric("witch", 2 if i < 3 else 1, stars=1 / 31, seed=5 + i), tpp=K)
    nm(m, "crown_1", "crown_2", "crown_3", "crown_4", "crown_5")
    m.b((0.7, 9.3, 0.7), (9.3, 10.7, 9.3), round_fabric("band", 2, seed=8), tpp=K)
    nm(m, "band")
    o1 = (5, 17.3, 6.6)
    m.b((3.75, 17.3, 5.35), (6.25, 19.3, 7.85), round_fabric("witch", 1, seed=13), rot=("x", 22.5, o1), tpp=K)
    ox, oy, oz = 5, 17.3 + 2 * math.cos(math.radians(22.5)), 6.6 + 2 * math.sin(math.radians(22.5))
    m.b((4.25, oy, oz - 0.75), (5.75, oy + 1.8, oz + 0.75), round_fabric("witch", 1, seed=17),
        rot=("x", 45, (ox, oy, oz)), tpp=K)
    nm(m, "tip", "tip_bend")
    m.c((3.8, 9.0, 0.6), (6.2, 11.4, 0.6), moon_card(), emit=12, tpp=K)
    tx, ty, tz = ox, oy + 1.8 * math.cos(math.radians(45)), oz + 1.8 * math.sin(math.radians(45))
    m.c((tx, ty - 2.0, tz), (tx, ty, tz + 0.12), art(["a"], {"a": ("brass", 2)}), tpp=K)
    m.c((tx - 1.1, ty - 4.1, tz + 0.06), (tx + 1.1, ty - 1.9, tz + 0.06), star_card(), emit=15, tpp=K)
    nm(m, "moon_charm", "thread", "star_charm")
    return m


# ------------------------------------------------------------------ 2. candle crown
def studded():
    """Brass band with a row of little amethyst studs."""
    def f(W, H, face, key):
        img = metal("brass", 1)(W, H, face, key)
        if face in SIDES4 and H >= 2:
            yy = H // 2
            for x in range(2, W - 2, 5):
                img[yy, x] = T("amethyst", 1)
                if yy + 1 < H - 1:
                    img[yy + 1, x] = T("amethyst", 3)
        return img
    return f


def candle_crown():
    m = Model("candle_crown", "hat", scale=1.0)
    ring = studded()
    m.b((0.55, 7.9, 0.55), (9.45, 9.2, 1.2), ring, tpp=K)
    m.b((0.55, 7.9, 8.8), (9.45, 9.2, 9.45), ring, tpp=K)
    m.b((0.55, 7.9, 1.2), (1.2, 9.2, 8.8), ring, tpp=K)
    m.b((8.8, 7.9, 1.2), (9.45, 9.2, 8.8), ring, tpp=K)
    nm(m, "band_front", "band_back", "band_left", "band_right")
    candles = [  # x0, z0, size, height  (front centre tallest, then sides, then back)
        (4.3, 0.5, 1.4, 4.4, "middle"), (1.5, 1.4, 1.2, 3.1, "front_left"), (7.3, 1.4, 1.2, 3.1, "front_right"),
        (2.2, 6.4, 1.1, 2.3, "back_left"), (6.7, 6.4, 1.1, 2.3, "back_right")]
    for i, (x, z, s, h, n) in enumerate(candles):
        y0 = 8.4 if z < 1 else 9.0
        m.b((x, y0, z), (x + s, y0 + h, z + s), wax(i), tpp=K)
        nm(m, f"candle_{n}")
    for i, (x, z, s, h, n) in enumerate(candles):
        y0 = (8.4 if z < 1 else 9.0) + h
        fs = 1.0 if s > 1.3 else 0.9
        cx, cz = x + s / 2, z + s / 2
        m.b((cx - fs / 2, y0, cz - fs / 2), (cx + fs / 2, y0 + fs * 2.0, cz + fs / 2), flame(i), emit=15, tpp=K)
        nm(m, f"flame_{n}")
    return m


# ------------------------------------------------------------------ 3. ghostlight lantern
GHOST_FACE = ["......",
              "......",
              ".a..a.",
              "..bb..",
              "......",
              "......"]


def ghost_body(alpha=235, face=True, skirt=False, ramp="ghost"):
    def f(W, H, fc, key):
        img = _blank(W, H)
        k = fr()
        t0 = (0 if fc == "up" else 1) + (1 if k in (4, 5) else 0)
        for y in range(H):
            for x in range(W):
                t = t0 + (1 if y > H * 0.8 else 0)
                if fc in SIDES4 and (x in (0, W - 1)):
                    t += 1
                if skirt and fc in SIDES4 and y >= H - 2:
                    wave = int(1.5 + 1.5 * math.sin((x + k) * 1.3))
                    if H - 1 - y < wave:
                        continue
                img[y, x] = T(ramp, t, alpha)
        if face and fc == "north" and W >= 6:
            ey = int(H * 0.45)
            ink, blush = (58, 52, 92, 255), (246, 178, 206, 255)
            for ex in (int(W * 0.22), W - 1 - int(W * 0.22) - 1):
                img[ey, ex] = img[ey, ex + 1] = ink           # closed, sleepy eyes
                if k not in (2, 3) and ey + 1 < H:
                    img[ey + 2 if ey + 2 < H else ey + 1, ex + (0 if ex < W // 2 else 1)] = blush
        return img
    return animated(f)


def glass_pane():
    """Translucent glass with an iron frame drawn round each face."""
    def f(W, H, face, key):
        img = _blank(W, H)
        for y in range(H):
            for x in range(W):
                edge = x in (0, 1, W - 2, W - 1) or y in (0, 1, H - 2, H - 1)
                mid = face not in ("up", "down") and (x == W // 2)
                if edge or mid:
                    img[y, x] = T("iron", face_tone(face, 2) + (1 if x in (0, W - 1) or y in (0, H - 1) else 0))
                elif face in ("up", "down"):
                    img[y, x] = T("iron", 3)
                else:
                    shine = (x - y) in (0, 1) and 2 < x < W * 0.45
                    img[y, x] = T("pane", 0 if shine else 2, 120 if not shine else 200)
        return img
    return f


def ghostlight_lantern():
    m = Model("ghostlight_lantern", "hand")
    iron = metal("iron", 1)
    m.b((1.8, 0, 1.8), (8.2, 0.9, 8.2), iron, tpp=K)
    m.b((2.4, 0.9, 2.4), (7.6, 7.1, 7.6), glass_pane(), tpp=K)
    nm(m, "base", "glass")
    m.b((3.2, 1.4, 3.2), (6.8, 5.8, 6.8), ghost_body(250, True, True), emit=15, tpp=K)
    nm(m, "ghost")
    m.b((1.8, 7.1, 1.8), (8.2, 7.9, 8.2), iron, tpp=K)
    m.b((3.0, 7.9, 3.0), (7.0, 8.7, 7.0), iron, tpp=K)
    m.b((4.4, 8.7, 4.4), (5.6, 9.5, 5.6), metal("brass", 1), tpp=K)
    nm(m, "cap", "cap_top", "finial")
    m.b((3.1, 9.0, 4.7), (3.6, 11.2, 5.3), iron, tpp=K)
    m.b((6.4, 9.0, 4.7), (6.9, 11.2, 5.3), iron, tpp=K)
    m.b((3.1, 11.2, 4.7), (6.9, 11.7, 5.3), iron, tpp=K)
    nm(m, "handle_left", "handle_right", "handle_top")
    # the handle bar sits inside the closed hand, centred on the arm; the lantern hangs below
    m.hand = {"rotation": [90, 0, 0], "translation": [0, -2.0, -2.9], "scale": [0.375] * 3}
    return m


# ------------------------------------------------------------------ 4. grimoire
COVER = ["gggggggggggg",
         "g..........g",
         "g.s......s.g",
         "g..........g",
         "g..........g",
         "g..........g",
         "g..........g",
         "g..........g",
         "g..........g",
         "g.s......s.g",
         "g..........g",
         "gggggggggggg"]


def belt():
    """Leather belt round the waist: only the outer ring of the top/bottom faces is drawn."""
    def f(W, H, face, key):
        img = _blank(W, H)
        for y in range(H):
            for x in range(W):
                if face in ("up", "down") and 1 < x < W - 2 and 1 < y < H - 2:
                    continue
                t = face_tone(face, 2) + (1 if y == H - 1 else 0)
                img[y, x] = T("leather", t)
        if face == "north":                      # little brass buckle at the front
            cx, cy = W // 2, H // 2
            for x in range(cx - 2, cx + 2):
                for y in range(max(0, cy - 1), min(H, cy + 2)):
                    if x in (cx - 2, cx + 1) or y in (cy - 1, cy + 1):
                        img[y, x] = T("brass", 1)
        return img
    return f


def grimoire():
    """Hangs from the side of a belt on the left hip, cover facing out, tilted back on its strap.
    Back slot, so it follows the body and not the arm. Authored in player pixels; the back slot
    sits 10 px lower. The arm ends at y -11, so the book starts below it and never touches it."""
    m = Model("grimoire", "back", scale=1.0)
    Y = 10.0                                     # player y -> back-slot model y
    hook = (-0.2, -12.9 + Y, 6.2)
    rot = ("x", 22.5, hook)
    cov = art(COVER, {"g": ("brass", 2), "s": ("brass", 1)}, back=fabric("cover", 2, seed=21, rim=False))
    z0, z1, y0, y1 = 4.4, 8.0, -17.9 + Y, -12.9 + Y
    m.b((-0.9, y0, z0), (-0.55, y1, z1), cov, rot=rot, tpp=K)      # outer cover
    m.b((0.15, y0, z0), (0.5, y1, z1), cov, rot=rot, tpp=K)        # cover against the leg
    m.b((-0.9, y0, z1 - 0.4), (0.5, y1, z1), fabric("cover", 2, seed=22), rot=rot, tpp=K)
    nm(m, "cover_outer", "cover_inner", "spine")

    def pages(W, H, face, key):
        img = _blank(W, H)
        for yy in range(H):
            for xx in range(W):
                t = face_tone(face, 1)
                if face in ("north", "up", "down") and (xx if face == "north" else yy) % 2 == 1:
                    t += 1
                img[yy, xx] = T("page", t)
        return img
    m.b((-0.55, y0 + 0.2, z0 + 0.15), (0.15, y1 - 0.2, z1 - 0.4), pages, rot=rot, tpp=K)
    nm(m, "pages")
    c = metal("brass", 1)
    m.b((-1.05, y1 - 0.6, z0 - 0.1), (0.65, y1 + 0.1, z0 + 0.7), c, rot=rot, tpp=K)
    m.b((-1.05, y0 - 0.1, z0 - 0.1), (0.65, y0 + 0.6, z0 + 0.7), c, rot=rot, tpp=K)
    nm(m, "corner_top", "corner_bottom")
    m.b((-1.0, (y0 + y1) / 2 - 0.55, z0 - 0.25), (0.6, (y0 + y1) / 2 + 0.55, z0 + 0.2),
        fabric("band", 3, seed=25), rot=rot, tpp=K)
    nm(m, "clasp_strap")
    mz, my = (z0 + z1) / 2 - 0.15, (y0 + y1) / 2
    m.c((-0.95, my - 1.25, mz - 1.25), (-0.95, my + 1.25, mz + 1.25), moon_card(), emit=12, rot=rot, tpp=K)
    nm(m, "moon_clasp")
    # strap from the side of the belt down to the book, and the belt itself
    m.b((-0.45, -13.2 + Y, 5.95), (0.35, -10.6 + Y, 6.45), metal("leather", 1), tpp=K)
    m.b((0.6, -11.3 + Y, 2.55), (9.4, -10.5 + Y, 7.45), belt(), tpp=K)
    nm(m, "belt_strap", "belt")
    return m


# ------------------------------------------------------------------ 5. wisp (balloon)
def wisp():
    m = Model("wisp", "balloon", scale=1.0)
    m.b((2.6, 9, 2.6), (7.4, 9.7, 7.4), ghost_body(185, False, ramp="wispr"), emit=15, tpp=K)
    m.b((2, 5, 2), (8, 9, 8), ghost_body(185, True, ramp="wispr"), emit=15, tpp=K)
    m.b((1.7, 2.4, 1.7), (8.3, 5, 8.3), ghost_body(175, False, True, ramp="wispr"), emit=15, tpp=K)
    nm(m, "head_top", "head", "skirt")
    m.b((4.3, 9.5, 4.6), (5.9, 11.3, 6.2), ghost_body(200, False, ramp="wispr"), emit=15,
        rot=("z", -22.5, (5.1, 9.5, 5.4)), tpp=K)
    m.b((5.2, 10.9, 4.9), (6.2, 12.0, 5.9), ghost_body(215, False, ramp="wispr"), emit=15,
        rot=("z", -45, (5.7, 10.9, 5.4)), tpp=K)
    nm(m, "tuft", "tuft_curl")
    m.b((2.6, 0.6, 5.2), (4.2, 2.4, 6.8), ghost_body(150, False, True, ramp="wispr"), emit=15, tpp=K)
    m.b((5.6, 1.2, 3.2), (7.0, 2.4, 4.6), ghost_body(150, False, True, ramp="wispr"), emit=15, tpp=K)
    nm(m, "tail_left", "tail_right")
    m.c((7.8, 8.8, 4.6), (9.8, 10.8, 4.6), star_card(), emit=15, tpp=K)
    nm(m, "star")
    return m


# ------------------------------------------------------------------ 6. moonlit broom (back)
def straw(seed=0, ragged=True, flare=False):
    """Bristles: one strand per texel column, light/dark alternating, darker toward the binding."""
    def f(W, H, face, key):
        img = _blank(W, H)
        for y in range(H):
            for x in range(W):
                if face in ("up", "down"):
                    img[y, x] = T("straw", 3 if (x + y) % 2 else 2)
                    continue
                side = 1 if face in ("east", "west") else 0
                strand = (x + hsh(x, 9, seed)) % 3
                t = (0, 1, 2)[strand] + side
                if hsh(x, y // 2, seed) % 9 == 0:
                    t += 1
                if not flare and y < 2:
                    t += 1
                if ragged:
                    cut = hsh(x, 1, seed + 3) % 4
                    if y >= H - cut:
                        continue
                img[y, x] = T("straw", t)
        return img
    return f


def mini_lantern():
    def f(W, H, face, key):
        img = _blank(W, H)
        k = fr()
        for y in range(H):
            for x in range(W):
                if face in ("up", "down") or x in (0, W - 1):
                    img[y, x] = T("iron", 2)
                elif x == W // 2 and face in SIDES4 and W > 3:
                    img[y, x] = T("iron", 1)
                else:
                    img[y, x] = T("flame", 0 if (y == H // 2 and k in (1, 4)) else 1)
        return img
    return animated(f)


def wood_grain(seed=0):
    def f(W, H, face, key):
        img = _blank(W, H)
        t0 = face_tone(face, 2)
        for y in range(H):
            for x in range(W):
                t = t0 + (1 if (y // 3 + x) % 4 == 0 else 0) - (1 if hsh(x, y, seed) % 19 == 0 else 0)
                img[y, x] = T("wood", t)
        return img
    return f


def moonlit_broom():
    m = Model("moonlit_broom", "back", scale=1.0)
    A = 45
    O = (5.0, 4.5, 8.0)
    rot = ("z", A, O)
    m.b((4.55, 0.0, 7.55), (5.45, 17.0, 8.45), wood_grain(1), rot=rot, tpp=K)
    m.b((4.4, 16.6, 7.4), (5.6, 18.0, 8.6), wood_grain(2), rot=rot, tpp=K)
    nm(m, "handle", "handle_knob")
    m.b((3.4, -0.6, 7.1), (6.6, 0.5, 8.9), fabric("band", 2, seed=31), rot=rot, tpp=K)
    m.b((3.3, -5.2, 7.05), (6.7, -0.6, 8.95), straw(1, ragged=False), rot=rot, tpp=4)
    m.b((2.5, -7.6, 6.6), (7.5, -5.0, 9.4), straw(2, flare=True), rot=rot, tpp=4)
    nm(m, "binding", "bristles", "bristles_tip")
    # a ribbon bow on the binding (faces the back, where people see it)
    bow = ["aa..aa",
           "abbbba",
           "aabbaa",
           "..ab..",
           ".a..a."]
    m.c((3.6, -1.8, 9.0), (6.4, 0.6, 9.0), art(bow, {"a": ("band", 2), "b": ("band", 1)}), rot=rot, tpp=K)
    nm(m, "bow")
    # little lantern hanging from the top of the handle
    s, c = math.sin(math.radians(A)), math.cos(math.radians(A))
    hx, hy = O[0] - (15.6 - O[1]) * s, O[1] + (15.6 - O[1]) * c
    m.c((hx, hy - 1.4, 8.0), (hx, hy, 8.12), art(["a"], {"a": ("iron", 2)}), tpp=K)
    m.b((hx - 0.9, hy - 1.9, 7.1), (hx + 0.9, hy - 1.4, 8.9), metal("iron", 1), tpp=K)
    m.b((hx - 0.7, hy - 3.8, 7.3), (hx + 0.7, hy - 1.9, 8.7), mini_lantern(), emit=15, tpp=4)
    m.b((hx - 0.9, hy - 4.2, 7.1), (hx + 0.9, hy - 3.8, 8.9), metal("iron", 1), tpp=K)
    nm(m, "lantern_hook", "lantern_cap", "lantern_light", "lantern_base")
    return m


PIECES = [
    ("witch_hat", "Moonlit Witch Hat", "HELMET", "A tall witch hat with a glowing crescent pin.", witch_hat),
    ("candle_crown", "Candle Crown", "HELMET", "A brass circlet of dripping candles.", candle_crown),
    ("ghostlight_lantern", "Ghostlight Lantern", "OFFHAND", "A sleepy ghost glowing in a lantern.", ghostlight_lantern),
    ("grimoire", "Moon Grimoire", "BACKPACK", "A spellbook that hangs at your hip.", grimoire),
    ("wisp", "Wisp", "BALLOON", "A little ghost that floats beside you.", wisp),
    ("moonlit_broom", "Moonlit Broom", "BACKPACK", "A broom with a lantern hanging off the end.", moonlit_broom),
]

if __name__ == "__main__":
    for key, title, slot, lore, mk in PIECES:
        m = mk()
        print(f"{key:20s} {slot:9s} {m.check():2d} elements")
