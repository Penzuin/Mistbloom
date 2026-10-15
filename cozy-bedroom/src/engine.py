"""Moonlit Ballroom - model engine (Mistbloom Studios).

Ported from the Nightbloom Nook engine: builds Minecraft Java block-model JSON (1.21.4+ item
models) from boxes and flat cards, paints ONE atlas per model procedurally, supports flip-book
animated textures (.png.mcmeta), validates Nexo-safe limits and renders an orthographic preview
that follows the game's own UV and rotation rules.
"""
import json, math, os, random
import numpy as np
from PIL import Image

NS = "cozybedroom"

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
    "ebony":       ["#5a4660", "#433348", "#2f2334", "#1b131f"],
    "rosewood":    ["#a0607a", "#7e4660", "#5c3248", "#3a2030"],
    "blacksilver": ["#c4cbdd", "#8890a8", "#565d74", "#2a2e3c"],
    "gold":        ["#fff1b0", "#ffd677", "#eeb156", "#bc8243"],
    "cream":       ["#fff8e8", "#f6e6c8", "#e4cba0", "#c4a67a"],
    "parchment":   ["#fbf5e6", "#efe2c4", "#d9c39b", "#b49d74"],
    "moonglass":   ["#e6f6ff", "#b2e0f8", "#7ac0e6", "#4a86ba"],
    "nightglass":  ["#46506c", "#323a54", "#232a40", "#141a2c"],
    "violet":      ["#c09ae0", "#9466c2", "#6c4698", "#432868"],
    "velvet":      ["#9a6ad0", "#7a4cb0", "#5a348a", "#3c2262"],
    "navy":        ["#6a7fc4", "#4c5ca2", "#37437e", "#262e5a"],
    "soot":        ["#4a4352", "#38323f", "#28232e", "#1a1620"],
    "ivory":       ["#fffdf6", "#f1ecdf", "#d8d0bd", "#b3aa94"],
    "rose":        ["#f39cab", "#d47589", "#ab566e", "#7b3d53"],
    "moss":        ["#a6d47e", "#7db35f", "#5a9049", "#406b3a"],
    "honey":       ["#f2cf98", "#d8a46a", "#ad7a4a", "#7a5032"],
    "linen":       ["#fffdf7", "#f4ede0", "#ddd2be", "#b8ab95"],
    "lilac":       ["#e8dcff", "#c9b4f2", "#a088d6", "#7462ac"],
    "sage":        ["#d6e6c4", "#acc896", "#83a571", "#5c7d52"],
    "toad":        ["#ffc2c8", "#f08f9e", "#c9667c", "#8e4459"],
    "clay":        ["#f0b28c", "#d38660", "#a95f42", "#74402e"],
    "lampglow":    ["#fffbe8", "#ffe9b4", "#ffcf80", "#e8a458"],
}.items()}

PANE_ALPHA = {True: 85, False: 140}

# ---------------------------------------------------------------- animation
NFRAMES = 8
FRAMETIMES = [3] * 8              # 8 frames x 3 ticks = a 1.2 s waltz bar
STATE = {"frame": 0}

def animated(fn):
    fn.animated = True
    return fn

def fr():
    return STATE["frame"]

def T(ramp, tone, a=255):
    tone = max(0, min(6, int(round(tone))))
    r, g, b = RAMPS[ramp][tone]
    return (r, g, b, a)

SIDES = ("north", "south", "east", "west")

def _blank(w, h):
    return np.zeros((h, w, 4), np.uint8)

# ------------------------------------------------------------------- painters
def solid(ramp, tone=2, bevel=True):
    def f(w, h, face, key):
        img = _blank(w, h)
        img[:, :] = T(ramp, tone)
        if bevel and face in SIDES and h > 2:
            img[0, :] = T(ramp, tone - 1)
        if face == "down":
            img[:, :] = T(ramp, tone + 1)
        if face == "up":
            img[:, :] = T(ramp, tone - 1)
        return img
    return f

def wood(ramp="ebony", plank=3, base=2):
    """Lightly textured planks: half-step bands, staggered joints, grain streaks. No outlines."""
    def f(w, h, face, key):
        rng = random.Random(key)
        img = _blank(w, h)
        horiz = w >= h
        L, Tn = (w, h) if horiz else (h, w)
        off = rng.randrange(7)
        for t in range(Tn):
            pi = t // plank
            b = base + [0, 1, 0, 1][(pi + off) % 4] * 0.5
            joint = (5 + pi * 9 + off) % 13
            for l in range(L):
                tone = b
                if t % plank == plank - 1 and plank > 1:
                    tone += 0.5
                if (l + pi * 5 + off) % 11 in (2, 3, 4, 5, 6) and t % plank == 0:
                    tone -= 0.5
                if L > 9 and l % 13 == joint:
                    tone += 0.5
                x, y = (l, t) if horiz else (t, l)
                img[y, x] = T(ramp, tone)
        if face == "down":
            img[:, :, :3] = (img[:, :, :3] * 0.85).astype(np.uint8)
        return img
    return f

def panel(ramp="ebony", front=("north",), rows=1, inlay=None):
    """Inset frame motif on the front faces: groove one half-step darker, lighter field."""
    g = wood(ramp, plank=3)
    def f(w, h, face, key):
        img = g(w, h, face, key)
        if face not in front or w < 6 or h < 5:
            return img
        bh = h / rows
        for r in range(rows):
            y0, y1 = int(round(r * bh)) + 1, int(round((r + 1) * bh)) - 2
            x0, x1 = 1, w - 2
            if y1 - y0 < 2:
                continue
            for x in range(x0, x1 + 1):
                img[y0, x] = T(inlay or ramp, 3 if not inlay else 2); img[y1, x] = T(inlay or ramp, 1)
            for y in range(y0, y1 + 1):
                img[y, x0] = T(inlay or ramp, 3 if not inlay else 2); img[y, x1] = T(inlay or ramp, 1)
        return img
    return f

def candle_p():
    def f(w, h, face, key):
        img = _blank(w, h)
        img[:, :] = T("cream", 0 if face == "up" else 1)
        if face in SIDES:
            img[0, :] = T("cream", 0)
            img[-1, :] = T("cream", 3)
            if h > 3 and w > 1:
                img[1, w // 2] = T("cream", 0)
        if face == "up":
            img[h // 2, w // 2] = T("soot", 2)
        return img
    return f

def moonflame(big=False):
    """Cold flame: white core, moonglass, violet base. Sways over the 8-frame loop."""
    PROFILE = [1, 1, 2, 3, 3, 4, 4, 3] if not big else [1, 2, 3, 4, 5, 5, 6, 6, 5, 4]
    SWAY = [0, 1, 1, 0, -1, -1, 0, 1]
    TOPCUT = [0, 1, 0, 2, 1, 0, 1, 0]
    def f(w, h, face, key):
        k = fr() % 8
        img = _blank(w, h)
        rows = len(PROFILE)
        for y in range(h):
            if int(y * rows / h) < TOPCUT[k]:
                continue
            r = max(0, min(rows - 1, int(y * rows / h)))
            half = PROFILE[r] * w / (2 * max(PROFILE) + 1)
            c = (w - 1) / 2 + SWAY[k] * (1 - r / (rows - 1)) * w / 6
            for x in range(w):
                dx = abs(x - c)
                if dx > half + 0.5:
                    continue
                if r >= rows - 1:
                    img[y, x] = T("violet", 2)
                elif dx < half * 0.35 and r > 1:
                    img[y, x] = (255, 255, 255, 255)
                elif dx < half * 0.7:
                    img[y, x] = T("moonglass", 2)
                else:
                    img[y, x] = T("moonglass", 4)
        return img
    return animated(f)

def pane_arch(lit=True):
    """Elven lantern glass: blacksilver frame, pointed arch in the top 42%, transom low."""
    ga = PANE_ALPHA[lit]
    gl = "moonglass" if lit else "nightglass"
    def f(w, h, face, key):
        img = _blank(w, h)
        if face in ("up", "down"):
            img[:, :] = T("blacksilver", 3)
            return img
        fr_ = T("blacksilver", 2)
        img[:, :] = fr_
        x0, x1 = 1, w - 2
        apex = max(1, int(round(h * 0.10)))
        shoulder = int(round(h * 0.42))
        half = (x1 - x0 + 1) / 2
        cx = (x0 + x1) / 2
        R = half * 1.55
        for y in range(1, h - 1):
            for x in range(x0, x1 + 1):
                inside = True
                if y < shoulder:
                    yy = shoulder - y
                    inside = (math.hypot(x - (cx + half - R), yy) <= R) and (math.hypot((cx - half + R) - x, yy) <= R) and y >= apex
                if inside:
                    tone = 1 if (x + y) % 9 else 0
                    if x == x0 or y == apex:
                        tone = 2
                    img[y, x] = T(gl, tone, ga)
        img[int(round(h * 0.78)), :] = fr_
        return img
    return f

def art(rows, pal):
    """rows of chars; '.' transparent; pal maps char -> (ramp, tone[, alpha]). Mirrored on back faces."""
    def f(w, h, face, key):
        img = _blank(w, h)
        ah, aw = len(rows), len(rows[0])
        mirror = face in ("south", "west", "down")
        for y in range(h):
            for x in range(w):
                sx = int(x * aw / w)
                ch = rows[int(y * ah / h)][aw - 1 - sx if mirror else sx]
                if ch != ".":
                    img[y, x] = T(*pal[ch])
        return img
    return f

def roof_tri(tone=2):
    return art([
        "....aa....",
        "...abba...",
        "...abbb...",
        "..abbbbb..",
        "..abbbbbb.",
        ".abbbbbbb.",
        ".abbbbbbbb",
        "abbbbbbbbb",
        "cccccccccc",
    ], {"a": ("blacksilver", tone - 1), "b": ("blacksilver", tone + 1), "c": ("blacksilver", tone + 2)})

def sprite(draw, mirror_back=True):
    """Wrap a frame-aware RGBA sprite generator draw(w, h, frame) -> uint8 (h, w, 4).
    Back faces mirror so a card reads correctly from both sides."""
    cache = {}
    def f(w, h, face, key):
        k = fr()
        ck = (w, h, k)
        if ck not in cache:
            cache[ck] = draw(w, h, k)
        img = cache[ck].copy()
        if mirror_back and face in ("south", "west", "down"):
            img = img[:, ::-1].copy()
        return img
    return animated(f)

# ------------------------------------------------------------------ model
class Model:
    def __init__(self, name, floor=0):
        self.name, self.floor, self.elements = name, floor, []

    def box(self, frm, to, mat, faces=None, rot=None, emit=0, over=None, res=1):
        fs = faces or ("north", "south", "east", "west", "up", "down")
        e = {"from": list(map(float, frm)), "to": list(map(float, to)),
             "faces": {f: (over or {}).get(f, mat) for f in fs}, "emit": emit, "res": res}
        if rot:
            axis, ang, org = rot
            e["rotation"] = {"angle": ang, "axis": axis, "origin": list(map(float, org))}
        self.elements.append(e)
        return e

    def card(self, frm, to, painter, rot=None, emit=0, res=1):
        flat = [i for i in range(3) if frm[i] == to[i]]
        assert len(flat) == 1, "card needs exactly one flat axis"
        fs = {0: ("east", "west"), 1: ("up", "down"), 2: ("north", "south")}[flat[0]]
        return self.box(frm, to, painter, faces=fs, rot=rot, emit=emit, res=res)

    def crossed(self, cx, y0, cz, w, h, painter, emit=0, res=1):
        for a in (45, -45):
            self.card([cx - w / 2, y0, cz], [cx + w / 2, y0 + h, cz], painter, rot=("y", a, [cx, y0, cz]), emit=emit, res=res)

    def lantern_roof(self, cx, top, cz, w):
        hw = w / 2 + 0.25
        L = hw * math.sqrt(2)
        tri = roof_tri()
        self.card([cx - hw, top, cz - hw], [cx + hw, top + L, cz - hw], tri, rot=("x", 45, [cx, top, cz - hw]), res=2)
        self.card([cx - hw, top, cz + hw], [cx + hw, top + L, cz + hw], tri, rot=("x", -45, [cx, top, cz + hw]), res=2)
        self.card([cx + hw, top, cz - hw], [cx + hw, top + L, cz + hw], tri, rot=("z", 45, [cx + hw, top, cz]), res=2)
        self.card([cx - hw, top, cz - hw], [cx - hw, top + L, cz + hw], tri, rot=("z", -45, [cx - hw, top, cz]), res=2)
        return top + hw

    # ---------------------------------------------------------- checks
    def check(self):
        n = len(self.elements)
        assert n <= 19, f"{self.name}: {n} elements (cap 19)"
        for e in self.elements:
            for v in e["from"] + e["to"]:
                assert -16.05 <= v <= 32.05, f"{self.name}: coord {v} out of -16..32"
            r = e.get("rotation")
            if r:
                assert r["angle"] in (-45, -22.5, 0, 22.5, 45), f"{self.name}: angle {r['angle']}"
            for f in e["faces"]:
                w, h = self.face_dims(e, f)
                assert w <= 64 and h <= 64, f"{self.name}: face {w}x{h} too big"
        return n

    def bounds(self):
        a = np.array([e["from"] for e in self.elements] + [e["to"] for e in self.elements])
        return a.min(0), a.max(0)

    @staticmethod
    def face_dims(e, f):
        d = np.array(e["to"]) - np.array(e["from"])
        w, h = {"north": (d[0], d[1]), "south": (d[0], d[1]), "east": (d[2], d[1]),
                "west": (d[2], d[1]), "up": (d[0], d[2]), "down": (d[0], d[2])}[f]
        r = e.get("res", 1)
        return max(1, int(math.ceil(w * r - 0.1))), max(1, int(math.ceil(h * r - 0.1)))

    def is_animated(self):
        return any(getattr(p, "animated", False) for e in self.elements for p in e["faces"].values())

    def bake(self, frame=0):
        STATE["frame"] = frame
        items = []
        for i, e in enumerate(self.elements):
            for f, painter in e["faces"].items():
                w, h = self.face_dims(e, f)
                items.append((i, f, w, h, painter))
        order = sorted(range(len(items)), key=lambda k: (-items[k][3], -items[k][2], k))
        for S in (16, 32, 64, 128, 256, 512):
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
            atlas[py:py + h, px:px + w] = painter(w, h, f, f"{self.name}-{i}-{f}")
            self.uv[(i, f)] = (px, py, px + w, py + h)
        self.atlas, self.S = atlas, S
        return atlas

    def display(self):
        lo, hi = self.bounds()
        ext = (hi - lo).max()
        c = (lo + hi) / 2
        def tr(rx, ry, fit):
            s = min(4.0, fit / ext)
            R = _rx(rx) @ _ry(ry)
            t = np.clip(-(R @ ((c - 8) * s)), -80, 80)
            return {"rotation": [rx, ry, 0], "translation": [round(float(v), 3) for v in t], "scale": [round(s, 4)] * 3}
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
                faces[f] = {"uv": [round(x1 * k, 4), round(y1 * k, 4), round(x2 * k, 4), round(y2 * k, 4)], "texture": "#0"}
            je["faces"] = faces
            els.append(je)
        return {"credit": "Cozy Bedroom by Mistbloom Studios", "texture_size": [self.S, self.S],
                "textures": {"0": tex, "particle": tex}, "elements": els, "display": self.display()}

    def export(self, root):
        vid = self.name
        self.bake()
        tdir = os.path.join(root, "assets", NS, "textures", "furniture")
        mdir = os.path.join(root, "assets", NS, "models", "furniture")
        idir = os.path.join(root, "assets", NS, "items")
        for d in (tdir, mdir, idir):
            os.makedirs(d, exist_ok=True)
        if self.is_animated():
            frames = [self.bake(k).copy() for k in range(NFRAMES)]
            uv0 = dict(self.uv)
            self.bake(0)
            assert self.uv == uv0, "UV layout changed between frames"
            Image.fromarray(np.concatenate(frames, 0)).save(os.path.join(tdir, vid + ".png"))
            with open(os.path.join(tdir, vid + ".png.mcmeta"), "w") as fh:
                json.dump({"animation": {"interpolate": False, "frames": [
                    {"index": i, "time": t} for i, t in enumerate(FRAMETIMES)]}}, fh, indent=1)
        else:
            Image.fromarray(self.atlas).save(os.path.join(tdir, vid + ".png"))
        with open(os.path.join(mdir, vid + ".json"), "w") as fh:
            json.dump(self.to_json(f"{NS}:furniture/{vid}"), fh, indent=1)
        with open(os.path.join(idir, vid + ".json"), "w") as fh:
            json.dump({"model": {"type": "minecraft:model", "model": f"{NS}:furniture/{vid}"}}, fh, indent=1)
        return vid

    # ---------------------------------------------------------- render
    def render(self, ppu=6, cam=(-0.62, 0.62, -1.0), frame=0):
        if not hasattr(self, "atlas") or getattr(self, "_frame", None) != frame:
            self.bake(frame)
            self._frame = frame
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
                quads.append((corners, i, f, n, e["emit"]))
        pts = np.array([p for q in quads for p in q[0]])
        sx, sy = pts @ right, -(pts @ up)
        minx, miny = sx.min(), sy.min()
        W = int(math.ceil((sx.max() - minx) * ppu)) + 4
        H = int(math.ceil((sy.max() - miny) * ppu)) + 4
        img = np.zeros((H, W, 4), np.uint8)
        zb = np.full((H, W), np.inf)
        shade = {"up": 1.0, "down": 0.5, "north": 0.8, "south": 0.8, "east": 0.62, "west": 0.62}
        # pass 0: opaque texels; pass 1: translucent texels, sorted back to front
        trans = []
        for pass_ in (0, 1):
            seq = quads
            if pass_ == 1:
                seq = sorted(quads, key=lambda q: -np.mean([p @ fwd for p in q[0]]))
            for corners, i, f, n, emit in seq:
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
                m &= (al >= 250) if pass_ == 0 else ((al > 8) & (al < 250))
                sub = zb[y0:y1, x0:x1]
                m &= z < sub - 1e-6
                if not m.any():
                    continue
                k = 1.0 if emit >= 10 else shade[f]
                if "rotation" in self.elements[i] and f in ("up", "down"):
                    k = 0.95 if f == "up" else 0.5
                if len(self.elements[i]["faces"]) == 2:
                    k = max(k, 0.9)
                col = tex[..., :3].astype(float) * k
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

def _rx(a):
    t = math.radians(a); c, s = math.cos(t), math.sin(t)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])

def _ry(a):
    t = math.radians(a); c, s = math.cos(t), math.sin(t)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])

def _rz(a):
    t = math.radians(a); c, s = math.cos(t), math.sin(t)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
