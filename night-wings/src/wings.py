"""Mistbloom Night Wings v2 - six premium wing cosmetics for HMCCosmetics.

v2 rules
- Authored in FINAL player pixels (what you see on the player). The model is compiled
  pre-shrunk and shown at head-display scale 1.3, pivoting on the chest, so the wings can
  spread ~19 px from the spine and stand well above the head while staying inside the
  -16..32 model box.
- 2 texels per pixel (the "32x" look of premium wing packs): smooth curves, thin veins,
  real feather and facet shading.
- Spine x = 5, back surface z = 7, shoulder line y = 11. Wings: 19 px wide, 34 px tall
  (y 24 .. -10), bending back at the wrist (inner 22.5 deg, outer 45 deg).
- No straps: one small jewel where the wings meet. Every model < 19 elements.
"""
import math
from engine import Model, T, _blank, fr, art_px, twinkle, RAMPS, _ramp7

K = 2                      # texels per pixel
S = 1.3                    # head display scale
SPINE, ZB = 5.0, 7.2
GW, GH = 19, 34            # wing grid in pixels
TOP = 24.0                 # grid row 0 = y 24; the shoulder line (y = 11) is grid y 13
CURVE = [(0, 9, 22.5), (9, 19, 45)]
POLISH = True              # v2.3 pixel-polish pass on every wing texture

RAMPS.update({k: _ramp7(v) for k, v in {
    "pearl":   ["#ffffff", "#e8e2f6", "#c2b8e0", "#7a6ea6"],      # angel (tinted base stays light)
    "nightbat": ["#a98ac8", "#7c5ea6", "#553f7e", "#33244f"],
    "batbone": ["#d8c6ec", "#b39bd2", "#8a72ac", "#5e4b7c"],
    "crimbat": ["#d47a9c", "#a8507a", "#7c365c", "#4e2040"],
    "emerald": ["#b6ffd9", "#5ef0a8", "#22c07c", "#127a52"],
    "onyx":    ["#3a3f52", "#262a3a", "#181b27", "#0d0f17"],
    "frost":   ["#ffffff", "#e3f7ff", "#ace0f8", "#6aaee0"],
    "rosepet": ["#fff2fa", "#f8cce8", "#e49ad0", "#b56aa8"],
    "lilpet":  ["#f6f0ff", "#d8c8fa", "#ad97e8", "#7a64bc"],
    "iris1":   ["#fff6fc", "#ffd6f0", "#f4a8dc", "#c97ab8"],
    "iris2":   ["#f8f4ff", "#ddd0ff", "#b7a2f0", "#8a72cc"],
    "iris3":   ["#f2fcff", "#ccf0ff", "#98d6f4", "#62a6dc"],
    "mauvebat": ["#c28ab0", "#985e8e", "#70426e", "#482a4a"],
    "steel":   ["#a6c4e6", "#6e93c4", "#45689c", "#22385e"],
    "violpet": ["#c9a6ec", "#9c76cc", "#7452a8", "#4a3278"],
}.items()})
RAMPS["iridb"] = [(247, 168, 216), (236, 164, 232), (214, 168, 244), (184, 176, 248),
                  (156, 192, 246), (128, 210, 238), (112, 226, 222)]          # pink -> lilac -> teal (body)
RAMPS["iridl"] = [(255, 226, 244), (250, 224, 252), (238, 226, 255), (226, 232, 255),
                  (214, 240, 255), (204, 248, 252), (200, 252, 244)]          # same hues, light (rim)
RAMPS["iridbm"] = [tuple((a + b) // 2 for a, b in zip(RAMPS["iridb"][i], RAMPS["iridb"][min(6, i + 1)]))
                   for i in range(7)]                                        # in-between body tones
RAMPS["iridd"] = [(196, 104, 170), (180, 104, 190), (156, 108, 206), (128, 118, 210),
                  (100, 136, 206), (76, 158, 196), (62, 172, 176)]            # same hues, dark (vein edge)


# ------------------------------------------------------------------ raster kit (pixel coords, K texels/px)
class Grid:
    def __init__(self, w=GW, h=GH):
        self.w, self.h, self.px = w * K, h * K, {}

    def pts(self):
        for ty in range(self.h):
            for tx in range(self.w):
                yield tx, ty, (tx + 0.5) / K, (ty + 0.5) / K

    def put(self, tx, ty, v):
        if 0 <= tx < self.w and 0 <= ty < self.h and v:
            self.px[(tx, ty)] = v

    def blade(self, root, tip, width, fn, belly=0.5, round_tip=False, clip=None):
        """Tapering blade root->tip (pixel coords). fn(t, a, d, half, x, y):
        t along 0..1, d signed distance from the centre line in px, a = |d|/half."""
        (rx, ry), (tx_, ty_) = root, tip
        dx, dy = tx_ - rx, ty_ - ry
        L2 = dx * dx + dy * dy
        L = math.sqrt(L2)
        for tx, ty, x, y in self.pts():
            if clip and not clip(x, y):
                continue
            px, py = x - rx, y - ry
            t = (px * dx + py * dy) / L2
            if not 0 <= t <= 1:
                continue
            d = (px * dy - py * dx) / L
            if round_tip:
                half = width * min(1, t / 0.1) ** 0.5
                if t > 0.7:
                    half *= math.sqrt(max(0, 1 - ((t - 0.7) / 0.3) ** 2))
            else:
                half = width * math.sin(math.pi * t ** (belly / 0.5 * 0.7))
                if t < 0.985:
                    half = max(half, 0.26 + 0.24 * (1 - t / 0.985) * min(1.0, width))   # tapers 2 -> 1 texel
            if abs(d) <= half:
                self.put(tx, ty, fn(t, abs(d) / max(half, 1e-6), d, half, x, y))

    def outline(self, fn):
        """Repaint every silhouette pixel (touching empty space) with fn(value)."""
        edge = [(p, v) for p, v in self.px.items()
                if any((p[0] + a, p[1] + b) not in self.px for a, b in ((0, 1), (1, 0), (-1, 0), (0, -1)))]
        for p, v in edge:
            nv = fn(v)
            if nv:
                self.px[p] = nv
        return self

    PROTECT = ("moon", "gold", "amber", "cream", "onyx")   # glints, gems, eyespots, claws stay crisp

    def polish(self, aa=0.5):
        """Pixel-polish pass:
        1. fill single-pixel notches in the silhouette (3+ filled side neighbours),
        2. clear speckle: a pixel unlike all four side neighbours, which all agree and are
           the same material, takes their value (protected accent colours are kept),
        3. anti-alias staircases: an empty inside-corner pixel on a diagonal edge gets a
           soft, partly transparent copy of the edge colour."""
        px = self.px
        O4 = ((0, 1), (1, 0), (0, -1), (-1, 0))
        for _ in range(2):                                   # 1. notch fill
            add = {}
            xs = [p[0] for p in px]; ys = [p[1] for p in px]
            if not xs:
                return self
            for x in range(min(xs), max(xs) + 1):
                for y in range(min(ys), max(ys) + 1):
                    if (x, y) in px:
                        continue
                    nb = [px[(x + a, y + b)] for a, b in O4 if (x + a, y + b) in px]
                    if len(nb) >= 3:
                        add[(x, y)] = max(set(nb), key=nb.count)
            px.update(add)
        fix = {}                                             # 2. speckle
        for (x, y), v in px.items():
            if v[0] in self.PROTECT:
                continue
            nb = [px.get((x + a, y + b)) for a, b in O4]
            if None in nb or nb.count(nb[0]) != 4:
                continue
            n = nb[0]
            if n != v and n[0] == v[0]:
                fix[(x, y)] = n
        px.update(fix)
        soft = {}                                            # 3. staircase AA
        xs = [p[0] for p in px]; ys = [p[1] for p in px]
        for x in range(min(xs) - 1, max(xs) + 2):
            for y in range(min(ys) - 1, max(ys) + 2):
                if (x, y) in px:
                    continue
                for (a, b), (c, d) in (((-1, 0), (0, -1)), ((1, 0), (0, -1)), ((-1, 0), (0, 1)), ((1, 0), (0, 1))):
                    n1, n2 = px.get((x + a, y + b)), px.get((x + c, y + d))
                    diag = px.get((x + a + c, y + b + d))
                    opp1, opp2 = px.get((x - a, y - b)), px.get((x - c, y - d))
                    if n1 and n2 and diag and not opp1 and not opp2:   # inside corner of a step
                        base = n1 if n1[0] not in self.PROTECT else n2
                        if base[0] in self.PROTECT:
                            break
                        alpha = base[2] if len(base) > 2 else 255
                        soft[(x, y)] = (base[0], base[1], max(30, int(alpha * aa)))
                        break
        soft = {}                                            # (edge AA disabled: solid colours only, no halos in game)
        mid = {}                                             # 4. interior step smoothing
        for (x, y), v in px.items():
            if v[0] in self.PROTECT or (x, y) in soft:
                continue
            for (a, b), (c, d) in (((-1, 0), (0, -1)), ((1, 0), (0, -1)), ((-1, 0), (0, 1)), ((1, 0), (0, 1))):
                n1, n2, dg = px.get((x + a, y + b)), px.get((x + c, y + d)), px.get((x + a + c, y + b + d))
                o1, o2 = px.get((x - a, y - b)), px.get((x - c, y - d))
                if not (n1 and n2 and dg and o1 and o2):
                    continue
                if n1 == n2 == dg and o1 == o2 == v and n1[0] == v[0] and abs(n1[1] - v[1]) >= 2:
                    al = (v[2] if len(v) > 2 else 255 + (n1[2] if len(n1) > 2 else 255)) // 1
                    t = round((v[1] + n1[1]) / 2)
                    mid[(x, y)] = (v[0], t) + ((v[2],) if len(v) > 2 else ())
                    break
        px.update(mid)
        return self

    def tidy(self):
        for (x, y) in list(self.px):
            if sum((x + a, y + b) in self.px for a in (-1, 0, 1) for b in (-1, 0, 1) if a or b) <= 1:
                del self.px[(x, y)]
        return self


def inside(x, y, poly):
    c = False
    j = len(poly) - 1
    for i in range(len(poly)):
        xi, yi = poly[i]; xj, yj = poly[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            c = not c
        j = i
    return c


def dseg(x, y, a, b):
    (ax, ay), (bx, by) = a, b
    dx, dy = bx - ax, by - ay
    t = max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / (dx * dx + dy * dy)))
    cx, cy = ax + t * dx, ay + t * dy
    side = (x - ax) * dy - (y - ay) * dx
    return math.hypot(x - cx, y - cy), t, side


def bow(a, b, toward, amount, n=32):
    mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
    vx, vy = toward[0] - mx, toward[1] - my
    L = math.hypot(vx, vy) or 1
    cx, cy = mx + vx / L * amount * 2, my + vy / L * amount * 2
    return [((1 - t) ** 2 * a[0] + 2 * (1 - t) * t * cx + t * t * b[0],
             (1 - t) ** 2 * a[1] + 2 * (1 - t) * t * cy + t * t * b[1])
            for t in (i / n for i in range(1, n + 1))]


def curve(pts, n=40):
    """Smooth Catmull-Rom polyline through control points (pixel coords)."""
    out = []
    P = [pts[0]] + list(pts) + [pts[-1]]
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for j in range(n):
            t = j / n
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * ((2 * p1[k]) + (-p0[k] + p2[k]) * t + (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * t2
                                    + (-p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]) * t3) for k in (0, 1)))
    out.append(pts[-1])
    return out


def at(path, u):
    seg = [math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(path, path[1:])]
    d = max(0.0, min(1.0, u)) * sum(seg)
    for (a, b), L in zip(zip(path, path[1:]), seg):
        if d <= L and L > 0:
            t = d / L
            return a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
        d -= L
    return path[-1]


# ------------------------------------------------------------------ cards
def seg_card(build, x0, tint=False, anim=False, cache=None):
    cache = {} if cache is None else cache
    def make(side):
        def f(W, H, face, key):
            k = fr()
            if k not in cache:
                g0 = build(k).tidy()
                if getattr(g0, "outline_fn", None):
                    g0.outline(g0.outline_fn)
                if POLISH:
                    g0.polish()
                cache[k] = g0
            g = cache[k]
            img = _blank(W, H)
            for y in range(H):
                for x in range(W):
                    tx = x if face == "south" else W - 1 - x
                    wx = x0 * K + ((W - 1 - tx) if side == "L" else tx)
                    v = g.px.get((wx, y))
                    if v:
                        img[y, x] = T(*v)
            return img
        f.tint = tint
        if anim:
            f.animated = True
        return f
    return make


def nm(m, *names):
    """Give the last len(names) parts readable names (shown in Blockbench)."""
    for e, n in zip(m.elements[-len(names):], names):
        e["name"] = n


def fold_pair(m, build, segs=CURVE, z=ZB, emit=0, tint=False, anim=False, h=GH, top=TOP, label="wing"):
    cache = {}
    for side in ("L", "R"):
        px, pz = SPINE, z
        for i, (x0, x1, sweep) in enumerate(segs):
            w = x1 - x0
            paint = seg_card(build, x0, tint, anim, cache)(side)
            c, s_ = math.cos(math.radians(sweep)), math.sin(math.radians(sweep))
            if side == "L":
                m.c((px - w, top - h, pz), (px, top, pz), paint, rot=("y", sweep, (px, top, pz)), emit=emit, tpp=K)
                nm(m, f"left_{label}" + ("" if len(segs) == 1 else ("_inner", "_outer")[i]))
                px -= w * c
            else:
                m.c((px, top - h, pz), (px + w, top, pz), paint, rot=("y", -sweep, (px, top, pz)), emit=emit, tpp=K)
                nm(m, f"right_{label}" + ("" if len(segs) == 1 else ("_inner", "_outer")[i]))
                px += w * c
            pz += w * s_


def jewel(m, pal, emit=13, y=10.2, z=ZB + 0.8):
    m.c((4.1, y, z), (5.9, y + 1.8, z), art_px([".a.", "aba", ".a."], pal), emit=emit)
    nm(m, "jewel")


def sparkle(m, x, y, ramp="moon", z=ZB + 3.5):
    m.c((x, y, z), (x + 2, y + 2, z), twinkle(ramp), emit=15)
    nm(m, "sparkle_left" if x < SPINE else "sparkle_right")


# ------------------------------------------------------------------ 3D accent blocks (v2.2)
def block(ramp, base=2, out=None, alpha=255, light=True):
    """Cube painter in the wing palette: lit top, mid fronts, shaded sides, dark underside,
    a 1-texel outline in the given darkest shade, and a highlight row along the top edge."""
    def f(W, H, face, key):
        tone = {"up": base - 1, "down": base + 2, "north": base, "south": base,
                "east": base + 1, "west": base + 1}[face]
        img = _blank(W, H)
        for y in range(H):
            for x in range(W):
                if out and W > 2 and H > 2 and (x in (0, W - 1) or y in (0, H - 1)):
                    img[y, x] = T(out[0], out[1], 255)
                elif light and y == 1 and face != "down":
                    img[y, x] = T(ramp, max(0, tone - 1), alpha)
                else:
                    img[y, x] = T(ramp, min(6, max(0, tone)), alpha)
        return img
    return f


def faceted(lit, dark, alpha=230):
    """Crystal cube: bright frost on the front/top faces, dark steel-blue on the sides and
    underside (the same lit/dark facet split the wing crystals use)."""
    def f(W, H, face, key):
        img = _blank(W, H)
        ramp, tone = (lit if face in ("up", "south", "north") else dark)
        if face == "up":
            tone = max(0, tone - 1)
        if face == "down":
            tone = min(6, tone + 1)
        for y in range(H):
            for x in range(W):
                edge = x in (0, W - 1) or y in (0, H - 1)
                img[y, x] = T(ramp, min(6, tone + (1 if edge and W > 3 and H > 3 else 0)), alpha)
        return img
    return f


def wrist_points(wrist, sweep=22.5, z=ZB + 0.1):
    """World positions (px) of the left and right wrist on the inner wing segment."""
    c, s_ = math.cos(math.radians(sweep)), math.sin(math.radians(sweep))
    wx, wy = wrist
    y = TOP - wy
    return [(SPINE - wx * c, y, z + wx * s_, sweep), (SPINE + wx * c, y, z + wx * s_, -sweep)]


def knuckle(m, wrist, painter, size=1.4, z=ZB + 0.1, emit=0):
    """A small 3D knuckle at each wrist, turned with its wing segment."""
    h = size / 2
    for x, y, zz, ang in wrist_points(wrist, z=z):
        m.b((x - h, y - h, zz - h), (x + h, y + h, zz + h), painter, rot=("y", ang, (x, y, zz)),
            emit=emit, tpp=K)
        nm(m, "left_knuckle" if x < SPINE else "right_knuckle")


def claw(m, wrist, painter, length=2.4, w=0.7, z=ZB + 0.1, emit=0):
    """A claw jutting up and outward from each wrist knuckle (tilted 22.5 deg on z)."""
    h = w / 2
    for x, y, zz, ang in wrist_points(wrist, z=z):
        tilt = 22.5 if ang < 0 else -22.5        # lean outward on each side
        m.b((x - h, y + 0.4, zz - h), (x + h, y + 0.4 + length, zz + h), painter,
            rot=("z", tilt, (x, y + 0.4, zz)), emit=emit, tpp=K)
        nm(m, "left_claw" if x < SPINE else "right_claw")


# ============================================================ 1. STARFEATHER (dyeable angel)
SF_ARM = curve([(0.0, 14.0), (4.5, 8.5), (10.0, 4.2), (15.0, 1.6), (18.7, 0.4)])
SF_SIL = curve([(18.7, 0.3), (18.9, 6.0), (18.0, 13.0), (16.0, 20.5), (13.0, 27.0),
                (9.6, 33.6), (7.4, 31.0), (5.0, 25.5), (2.6, 20.5), (0.4, 17.4)], 30)
SF_POLY = SF_ARM + SF_SIL


def _starfeather(k):
    """Seraph wing with a clear 3-tier hierarchy, each tier a value step darker:
    coverts (lightest) -> secondaries -> primaries. Every feather ends in a rounded point
    with a 1-texel highlight on its leading edge and a shadow on its trailing edge; a dark
    lavender line sits under each covert row; the whole wing has a dark outline."""
    g = Grid()
    clip = lambda x, y: inside(x, y, SF_POLY)
    for tx, ty, x, y in g.pts():                       # deep base between feathers
        if clip(x, y) and min(math.hypot(x - a, y - b) for a, b in SF_SIL[::3]) > 2.0:
            g.put(tx, ty, ("pearl", 6))

    def flight(base, shaft):
        def fn(t, a, d, half, x, y):
            if half - abs(d) < 0.5:
                return ("pearl", base - 2 if d < 0 else min(6, base + 2))   # leading highlight / trailing shadow
            if shaft and abs(d) < 0.28 and t < 0.84:
                return ("pearl", base - 2)                          # shaft
            return ("pearl", min(6, base + (1 if t > 0.78 else 0)))
        return fn

    n = 9
    for i in range(n):                                  # outer primaries first, inner on top
        s = 1 - i / (n - 1)
        r = at(SF_ARM, 0.06 + 0.9 * s)
        tip = at(SF_SIL[2:], 1 - s)
        primary = s > 0.45
        g.blade(r, tip, 2.35, flight(5 if primary else 3, primary), round_tip=True, clip=clip)   # primaries ~62% value

    def covert(t, a, d, half, x, y):
        if t > 0.8 or (d > 0 and half - d < 0.5):
            return ("pearl", 5)                         # one clean dark lavender line under each scallop
        return ("pearl", 0 if t < 0.55 else 1)
    for L, w, cnt in ((6.6, 2.0, 7), (4.3, 1.75, 6), (2.5, 1.45, 5)):
        for j in reversed(range(cnt)):
            s = 0.02 + 0.93 * j / (cnt - 1)
            rx, ry = at(SF_ARM, s)
            ang = math.radians(102 - 52 * s)
            g.blade((rx, ry - 0.2), (rx + L * math.cos(ang), ry + L * math.sin(ang)), w, covert,
                    round_tip=True, clip=clip)
    for i in range(240):                                # bright leading edge
        x, y = at(SF_ARM, i / 239)
        g.put(int(x * K), int(y * K), ("pearl", 0))
    g.outline_fn = lambda v: ("pearl", 6)
    return g


def _sf_rim(k):
    """Untinted pale-gold rim along the arm with a shimmer sliding down it."""
    g = Grid()
    for i in range(300):
        u = i / 299
        x, y = at(SF_ARM, u)
        lit = abs(u - k / 5.0) < 0.07
        g.put(int(x * K), int(y * K) - 1, ("moon", 0 if lit else 2, 255))
        if lit:
            g.put(int(x * K), int(y * K) - 2, ("moon", 1, 200))
    return g


def starfeather():
    m = Model("starfeather_wings", dye=(252, 248, 255), scale=S)
    fold_pair(m, _starfeather, tint=True)
    fold_pair(m, _sf_rim, z=ZB + 0.08, emit=13, anim=True, label="gold_trim")   # gold trim keeps its colour when dyed
    m.b((3.1, 8.8, ZB - 0.3), (6.9, 12.4, ZB + 1.2), block("gold", 1, ("gold", 5)), emit=6, tpp=K)     # 3D gold clasp
    nm(m, "clasp")
    m.b((4.1, 9.7, ZB + 1.2), (5.9, 11.5, ZB + 2.0), block("moon", 1, ("gold", 5)),
        rot=("z", 45, (5.0, 10.6, ZB + 1.6)), emit=15, tpp=K)                                    # diamond moon gem
    nm(m, "moon_gem")
    sparkle(m, -8.5, 20.5)
    sparkle(m, 16.5, 12.0)
    return m


# ============================================================ 2. DUSKBAT (vampire bat)
def membrane(arm, wrist, tips, bows, sag_toward, mem, bone, rim, notches=(), veins=(), vein=None):
    """Bat/dragon wing at 2x: arm root->wrist, finger bones wrist->tips, scalloped trailing
    edge bowing toward the wrist, membrane shaded by distance to the nearest bone; optional
    tears (notches) in the trailing edge and faint vein lines branching off the bones."""
    g = Grid()
    outline = list(arm) + [tips[0]]
    for i in range(len(tips) - 1):
        outline += bow(tips[i], tips[i + 1], sag_toward, bows[i])
    outline += bow(tips[-1], arm[0], sag_toward, bows[-1])
    bones = [(arm[j], arm[j + 1]) for j in range(len(arm) - 1)] + [(wrist, t) for t in tips]
    nbone_arm = len(arm) - 1
    isbone = set()
    for tx, ty, x, y in g.pts():
        best = min(((dseg(x, y, a, b), i) for i, (a, b) in enumerate(bones)), key=lambda h: h[0][0])
        (d, t, side), i = best
        r = 0.55 if i < nbone_arm else 0.42 * (1 - 0.5 * t) + 0.1
        if d <= r:
            g.put(tx, ty, bone(i < nbone_arm, t, side, d / r))
            isbone.add((tx, ty))
        elif inside(x, y, outline):
            if any(math.hypot(x - nx, y - ny) < nr for nx, ny, nr in notches):
                continue                                   # torn notch
            v = mem(d, x, y)
            if vein and any(dseg(x, y, a, b)[0] < 0.22 for a, b in veins):
                v = vein(v)
            g.put(tx, ty, v)
    for (tx, ty), v in list(g.px.items()):              # trailing / outer edge rim
        if (tx, ty) in isbone:
            continue
        if any((tx + a, ty + b) not in g.px for a, b in ((0, 1), (1, 0), (-1, 0), (0, -1))) and ty > 4:
            g.px[(tx, ty)] = rim(tx, ty, v)
    return g


def _branches(wrist, tips, sag, spots=(0.42, 0.68), length=2.6, turn=0.55):
    """Short vein lines branching off each finger toward the trailing edge."""
    out = []
    for tip in tips[1:]:
        dx, dy = tip[0] - wrist[0], tip[1] - wrist[1]
        L = math.hypot(dx, dy)
        ux, uy = dx / L, dy / L
        for s_ in spots:
            px, py = wrist[0] + dx * s_, wrist[1] + dy * s_
            sx, sy = sag[0] - px, sag[1] - py           # bend toward the membrane centre
            sl = math.hypot(sx, sy) or 1
            bx, by = ux * (1 - turn) + sx / sl * turn, uy * (1 - turn) + sy / sl * turn
            bl = math.hypot(bx, by)
            out.append(((px, py), (px + bx / bl * length, py + by / bl * length)))
    return out


def _bat(k):
    """Vampire bat: long finger bones, deep scallops with two small tears, faint veins,
    and a two-step crimson -> mauve -> plum fade out from the body."""
    wrist = (8.4, 3.2)
    arm = curve([(0.0, 14.5), (3.8, 9.4), (wrist[0], wrist[1])], 12)
    tips = [(18.8, 8.0), (18.4, 21.5), (12.6, 33.4), (4.4, 28.6)]
    bows = [3.2, 3.6, 3.0, 2.8]
    sag = (8.0, 12.0)

    def mem(d, x, y):
        body = 2.2 * (1 - x / 19.0)
        sagv = 0 if d < 1.0 else 0.8 if d < 2.6 else 1.5
        tone = max(0, min(6, round(0.6 + body + sagv)))
        p = (7.5 - x - 0.25 * (y - 14)) / 5.0              # 1 near the body -> 0 outward
        if p > 0.62:
            return ("crimbat", tone)                       # crimson -> mauve -> plum, two clean steps
        if p > 0.3:
            return ("mauvebat", tone)
        return ("nightbat", tone)

    def bone(is_arm, t, side, a):
        return ("batbone", 1 if a < 0.5 else 2)

    def tear(i, frac, depth):                             # notch just inside a scallop's middle
        pts = bow(tips[i], tips[i + 1], sag, bows[i])
        x, y = pts[int(len(pts) * frac)]
        vx, vy = sag[0] - x, sag[1] - y
        L = math.hypot(vx, vy)
        return (x + vx / L * depth, y + vy / L * depth, 0.75)

    g = membrane(arm, wrist, tips, bows, sag, mem, bone,
                 rim=lambda tx, ty, v: (v[0], 5) if v[0] in ("nightbat", "mauvebat", "crimbat") else v,
                 notches=[tear(0, 0.55, 0.35), tear(1, 0.45, 0.35)],
                 veins=_branches(wrist, tips, sag),
                 vein=lambda v: (v[0], max(0, v[1] - 1)))
    for (x, y) in ((8.0, 1.6), (8.5, 2.2), (7.5, 1.2)):  # thumb claw
        g.put(int(x * K), int(y * K), ("cream", 1))
    g.outline_fn = lambda v: ("nightbat", 6) if v[0] in ("nightbat", "mauvebat", "crimbat") else None
    return g


def duskbat():
    m = Model("duskbat_wings", scale=S)
    fold_pair(m, _bat, z=ZB + 0.1)
    knuckle(m, (8.4, 3.2), block("batbone", 1), size=1.7)
    claw(m, (8.4, 3.2), block("cream", 1, ("leather", 5)), length=2.0, w=0.6)
    jewel(m, {"a": ("plum", 1), "b": ("blush", 0)}, emit=10)
    return m


# ============================================================ 3. FROSTLIGHT ICE
FROST_ARM = curve([(0.0, 14.5), (4.5, 9.0), (9.5, 4.8)], 12)
FROST_SHARDS = [   # (arm position, tip, width): large crystals laid out like flight feathers
    (0.95, (18.9, 0.8), 2.5), (0.82, (18.9, 9.6), 2.8), (0.66, (17.4, 18.4), 2.9),
    (0.48, (13.6, 26.4), 2.2), (0.30, (9.0, 32.6), 1.8), (0.12, (3.6, 29.4), 1.3),
]


def _ice(k):
    """Six large faceted crystals along a rising arm. Each crystal has a bright lit face
    and a dark steel-blue shaded face so the facets read as 3D, bright cut edges, a dark
    outline. A glint hops from crystal to crystal (one per frame) and the tips sparkle on
    two frames."""
    g = Grid()
    order = list(reversed(FROST_SHARDS))
    for i, (s_, tip, w) in enumerate(order):
        root = at(FROST_ARM, s_)
        lit_now = (5 - i) == k                            # glint hops root crystal -> wing tip
        def fn(t, a, d, half, x, y, lit_now=lit_now):
            if lit_now and abs(t - 0.55) < 0.22 and a < 0.5:
                return ("frost", 0, 250)                  # the hopping glint
            if half - abs(d) < 0.45:
                return ("frost", 0, 240) if d < 0 else ("steel", 1, 235)   # cut edges
            if abs(d) < 0.25 and t < 0.9:
                return ("frost", 0, 235)                  # ridge
            if d < 0:
                return ("frost", 1 if a > 0.45 else 2, 200)               # lit face
            return ("steel", 3 if a < 0.5 else 2, 215)                    # dark steel-blue face
        g.blade(root, tip, w, fn, belly=0.4)
    for i in range(120):                                   # frosted arm
        x, y = at(FROST_ARM, i / 119)
        g.put(int(x * K), int(y * K), ("frost", 0, 245))
        g.put(int(x * K), int(y * K) + 1, ("frost", 2, 230))
    g.outline_fn = lambda v: ("steel", 5, 245)
    if k in (2, 5):                                        # tip sparkles
        for _, (tx_, ty_), _w in FROST_SHARDS:
            cx, cy = min(int(tx_ * K), g.w - 2), min(int(ty_ * K), g.h - 2)
            for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
                g.put(cx + dx, cy + dy, ("frost", 0, 255))
    return g


def frostlight():
    m = Model("frostlight_wings", scale=S)
    fold_pair(m, _ice, z=ZB + 0.1, emit=11, anim=True)
    ice = faceted(("frost", 1), ("steel", 3))
    m.b((4.0, 5.6, ZB + 0.1), (6.0, 10.2, ZB + 2.1), ice, rot=("y", 45, (5.0, 7.9, ZB + 1.1)), emit=10, tpp=K)   # centre spire
    m.b((2.5, 5.4, ZB + 0.3), (4.1, 8.8, ZB + 1.9), ice, rot=("z", 22.5, (3.3, 5.4, ZB + 1.1)), emit=10, tpp=K)   # leaning left
    m.b((5.9, 5.4, ZB + 0.3), (7.5, 8.8, ZB + 1.9), ice, rot=("z", -22.5, (6.7, 5.4, ZB + 1.1)), emit=10, tpp=K)  # leaning right
    nm(m, "crystal_middle", "crystal_left", "crystal_right")
    sparkle(m, -7.5, 21.5, "ice")
    sparkle(m, 15.5, 18.0, "ice")
    return m


# ============================================================ 4. BLOOMFAIRY (iridescent swallowtail)
SHIFT = [0.0, 0.4, 0.8, 1.2, 0.8, 0.4]                   # slow colour drift through the gradient
FORE_ROOT = (0.3, 16.6)
FORE_POLY = [FORE_ROOT] + curve([(18.6, 0.6), (18.8, 5.2), (17.6, 10.6), (14.4, 14.8), (9.0, 17.6),
                                  (3.4, 18.8), (0.6, 18.2)], 16)
FORE_VEINS = [math.atan2(y - FORE_ROOT[1], x - FORE_ROOT[0])
              for x, y in ((18.6, 1.4), (18.4, 6.4), (16.4, 11.6), (11.6, 15.8), (5.8, 18.0))]
EYE = (14.2, 6.4)


def _fairy_hue(t, k, lo=0.0):
    return max(0, min(6, round(lo + t * (6.4 - lo) - 0.2 + SHIFT[k])))


def _fairy_up(k):
    """Broad triangular forewing with a rounded outer edge: radiating veins with darker
    outlines, a pink -> lilac -> teal gradient that slowly drifts, a dark eyespot ringed
    in gold near the tip, a bright inner rim and a crisp dark outline."""
    g = Grid(19, 19)
    band = (k % 6) / 6
    for tx, ty, x, y in g.pts():
        if not inside(x, y, FORE_POLY):
            continue
        dx, dy = x - FORE_ROOT[0], y - FORE_ROOT[1]
        r = math.hypot(dx, dy)
        t = min(1.0, r / 23.0)
        hue = _fairy_hue(t, k)
        e = math.hypot(x - EYE[0], y - EYE[1])
        if e < 0.85:
            g.put(tx, ty, ("onyx", 1, 245)); continue      # dark eyespot
        if e < 1.5:
            g.put(tx, ty, ("gold", 1, 250)); continue      # gold ring
        ang = math.atan2(dy, dx)
        off = min(abs(ang - va) for va in FORE_VEINS) * r
        if off < 0.22:
            v = ("iridl", hue, 230)                        # vein
        elif off < 0.5:
            v = ("iridd", hue, 175)                        # vein outline
        elif abs(t - band) < 0.035:
            v = ("iridl", hue, 175)                        # shimmer sweep
        else:
            v = ("iridb", hue, 150)
        g.put(tx, ty, v)
    for (tx, ty), v in list(g.px.items()):                 # bright inner rim one texel inside the outline
        if any((tx + a, ty + b) not in g.px for a in (-2, 0, 2) for b in (-2, 0, 2)) and v[0] in ("iridb", "iridd"):
            g.px[(tx, ty)] = ("iridl", v[1], 240)
    g.outline_fn = lambda v: ("iridd", v[1], 245) if v[0].startswith("irid") else None
    return g


def _fairy_paint(k, L, t, a, d, half, lo):
    hue = _fairy_hue(t, k, lo)
    hf = lo + t * (6.4 - lo) - 0.2 + SHIFT[k]                # continuous hue, for in-between tones
    frac = hf - math.floor(hf)
    if half - abs(d) < 0.42:
        return ("iridl", hue, 245)
    if abs(d) < 0.2 and t < 0.9:
        return ("iridl", hue, 230)
    if abs(d) < 0.5 and t < 0.9:
        return ("iridd", hue, 175)
    if abs(t - ((k + 3) % 6) / 6) < 0.04:
        return ("iridl", hue, 175)
    if 0.3 < frac < 0.7:
        return ("iridbm", max(0, min(6, math.floor(hf))), 150)     # blend between two bands
    return ("iridb", hue, 150)


def _fairy_lo(k):
    """Swallowtail hindwing: a rounded violet-teal paddle narrowing into a long tail."""
    g = Grid(14, 20)
    lobe = ((0.6, 2.6), (9.0, 11.6))
    tail = ((7.4, 10.0), (12.4, 19.8))
    L1 = math.hypot(lobe[1][0] - lobe[0][0], lobe[1][1] - lobe[0][1])
    g.blade(*lobe, 3.6, lambda t, a, d, h, x, y: _fairy_paint(k, L1, t, a, d, h, 3.0), round_tip=True)
    g.blade(*tail, 1.25, lambda t, a, d, h, x, y: _fairy_paint(k, L1, t, a, d, h, 4.5), belly=0.4)
    g.outline_fn = lambda v: ("iridd", v[1], 245) if v[0].startswith("irid") else None
    return g


def bloomfairy():
    m = Model("bloomfairy_wings", scale=S)
    fold_pair(m, _fairy_up, [(0, 19, 22.5)], z=ZB + 0.1, emit=9, anim=True, h=19, top=TOP, label="upper_wing")
    fold_pair(m, _fairy_lo, [(0, 14, 22.5)], z=ZB + 0.35, emit=9, anim=True, h=20, top=11.0, label="lower_wing")
    m.b((4.4, 5.6, ZB + 0.3), (5.6, 10.0, ZB + 1.5), block("iris2", 1, ("iridd", 3)), emit=10, tpp=K)   # thorax
    m.b((4.5, 10.0, ZB + 0.4), (5.5, 11.0, ZB + 1.4), block("moon", 1, ("gold", 5)), emit=15, tpp=K)    # glowing head bead
    nm(m, "body", "head")
    sparkle(m, -6.5, 21.0)
    sparkle(m, 13.0, 3.5)
    return m


# ============================================================ 5. NIGHTWYRM (black & emerald dragon)
def _wyrm(k):
    """Black-and-emerald dragon wing: emerald veins that pulse outward from the body,
    a glow hugging every bone, a pulsing emerald trailing edge, spikes along the arm and
    a hooked bone claw at the wrist."""
    wrist = (9.2, 3.6)
    arm = curve([(0.0, 14.2), (4.0, 9.6), (wrist[0], wrist[1])], 12)
    tips = [(18.8, 1.8), (18.8, 16.4), (14.0, 31.6), (5.0, 30.0)]
    pulse = [0, 1, 1, 2, 1, 1][k]
    wave = k / 5.0                                       # pulse front travelling body -> tips

    def mem(d, x, y):
        if d < 0.5:
            return ("emerald", 6)                        # thin dark-green glow hugging each vein
        return ("onyx", 0 if d < 1.2 else 1 if d < 3.2 else 2)

    def bone(is_arm, t, side, a):
        if is_arm:
            return ("onyx", 0) if (side < 0 and a > 0.45) else ("onyx", 2)
        dd = abs(t - wave)
        if dd < 0.08:
            return ("emerald", 0)                        # bright pulse front
        if dd < 0.18:
            return ("emerald", 2)
        return ("emerald", 4 if a < 0.4 else 6)          # dim glowing vein

    def rim(tx, ty, v):
        return ("emerald", pulse) if v[0] != "onyx" or v[1] < 3 else v

    g = membrane(arm, wrist, tips, [3.4, 3.8, 3.2, 3.0], (9.0, 13.0), mem, bone, rim)
    wx, wy = int(wrist[0] * K), int(wrist[1] * K)          # hooked claw at the wrist
    for i, (dx, dy) in enumerate(((0, -1), (0, -2), (1, -3), (1, -4), (2, -5), (3, -5), (4, -4))):
        g.put(wx + dx, wy + dy, ("onyx", 3) if i >= 5 else ("cream", 1 if i < 3 else 0))
        if i < 4:
            g.put(wx + dx + 1, wy + dy, ("cream", 2))
    return g


def nightwyrm():
    m = Model("nightwyrm_wings", scale=S)
    fold_pair(m, _wyrm, z=ZB + 0.1, emit=6, anim=True)
    knuckle(m, (9.2, 3.6), block("onyx", 0), size=1.8)
    claw(m, (9.2, 3.6), block("cream", 1, ("onyx", 4)), length=2.6, w=0.7)
    m.b((4.0, 8.2, ZB - 0.3), (6.0, 12.6, ZB + 0.6), block("onyx", 1, ("emerald", 3)), emit=5, tpp=K)            # spine plate, emerald rim
    nm(m, "spine_plate")
    for y0 in (8.8, 10.6):                                                                          # emerald ridge spikes
        m.b((4.5, y0, ZB + 0.5), (5.5, y0 + 1.0, ZB + 1.5), block("emerald", 1, ("emerald", 6)),
            rot=("z", 45, (5.0, y0 + 0.5, ZB + 1.0)), emit=13, tpp=K)
        nm(m, "spine_spike_top" if y0 > 10 else "spine_spike_bottom")
    return m


# ============================================================ 6. MISTBLOOM PETAL (signature)
PETALS = [   # (root, tip, width, ramp): deep violet inner petals behind two pale feature petals
    ((0.4, 13.2), (10.4, 1.6), 2.5, "violpet"), ((0.4, 14.8), (16.0, 22.8), 2.8, "violpet"),
    ((0.4, 15.4), (10.0, 27.4), 2.2, "violpet"),
    ((0.4, 13.6), (18.9, 6.0), 3.1, "rosepet"), ((0.4, 14.2), (18.9, 15.6), 3.1, "lilpet"),
]


def _petals(k):
    """Five long night-flower petals: three deep-violet inner petals behind two pale outer
    feature petals, each deep at the root and pale at the tip, a glowing moon vein with
    pollen motes drifting out along it, and a dark outline in the petal's own colour."""
    g = Grid()
    vein = [1, 1, 0, 0, 1, 2][k]
    for j, (r, tip, w, ramp) in enumerate(PETALS):
        def fn(t, a, d, half, x, y, ramp=ramp, j=j):
            mote = (k / 6 + j * 0.37) % 1
            if abs(t - mote) < 0.035 and abs(d) < 0.6:
                return ("amber", 0)                     # pollen mote drifting along the vein
            if abs(t - mote) < 0.035 and abs(d) < 1.0:
                return ("amber", 2)
            if abs(d) < 0.25 and 0.06 < t < 0.86:
                return ("moon", vein)
            tone = 4 if t < 0.22 else 3 if t < 0.4 else 2 if t < 0.62 else 1 if t < 0.86 else 0
            if half - abs(d) < 0.5:
                tone = min(6, tone + 3)
            elif d < 0 and a > 0.55:
                tone = max(0, tone - 1)
            return (ramp, tone)
        g.blade(r, tip, w, fn, belly=0.62)
    for p in [p for p, v in g.px.items() if p[0] <= 1 and v[0] in ("moon", "amber")]:
        del g.px[p]                                     # no stray glow pixel at the spine edge
    g.outline_fn = lambda v: (v[0], 6) if v[0] in ("violpet", "rosepet", "lilpet") else None
    return g


FLOWER = ([
    "..a..",
    ".aba.",
    "abcba",
    ".aba.",
    "..a..",
], {"a": ("rosepet", 1), "b": ("rosepet", 0), "c": ("moon", 0)})


def mistbloom():
    m = Model("petal_wings", scale=S)
    fold_pair(m, _petals, z=ZB + 0.1, emit=7, anim=True)
    m.c((2.6, 6.0, ZB + 0.9), (7.4, 10.8, ZB + 0.9), art_px(*FLOWER), emit=15)                # soft glow behind
    nm(m, "glow")
    cx, cy, cz = 5.0, 8.4, ZB + 1.3
    pet = block("rosepet", 2, ("rosepet", 5))
    for dx, dy, w, h in ((0, 0.95, 1.2, 1.1), (0, -0.95, 1.2, 1.1), (0.95, 0, 1.1, 1.2), (-0.95, 0, 1.1, 1.2)):
        m.b((cx + dx - w / 2, cy + dy - h / 2, cz - 0.4), (cx + dx + w / 2, cy + dy + h / 2, cz + 0.4), pet,
            emit=8, tpp=K)                                                                       # four bud petals
    m.b((cx - 0.6, cy - 0.6, cz - 0.2), (cx + 0.6, cy + 0.6, cz + 0.7), block("moon", 0), emit=15, tpp=K)  # glowing heart
    nm(m, "bud_top", "bud_bottom", "bud_right", "bud_left", "bud_center")
    sparkle(m, -6.0, 22.0)
    sparkle(m, 15.0, 22.5)
    return m


WINGS = [
    ("starfeather_wings", "Starfeather Wings", "Seraph wings: three tiers of pearl feathers, a shimmering gold rim and a 3D gold clasp with a moon gem.", starfeather),
    ("duskbat_wings", "Duskbat Wings", "Vampire-bat wings with torn scallops, veins, a crimson glow and 3D wrist claws.", duskbat),
    ("frostlight_wings", "Frostlight Wings", "Faceted ice crystals with a glint hopping between them, crowned by a 3D crystal cluster.", frostlight),
    ("bloomfairy_wings", "Bloomfairy Wings", "Iridescent swallowtail wings with gold-ringed eyespots and a glowing 3D fairy body.", bloomfairy),
    ("nightwyrm_wings", "Nightwyrm Wings", "Black-and-emerald dragon wings with pulsing veins, 3D claws and a ridged spine plate.", nightwyrm),
    ("petal_wings", "Mistbloom Petal Wings", "Deep violet and pale petals with drifting pollen and a glowing 3D flower bud.", mistbloom),
]
