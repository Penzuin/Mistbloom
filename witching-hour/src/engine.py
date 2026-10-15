"""Mistbloom cosmetics engine (shared with Moonlit Wardrobe).

Item-model JSON from boxes and flat cards, one baked atlas per model, Nexo-safe
checks, and an orthographic preview renderer that follows the game's UV rules.
Authored in player pixels: 1 px = 1.6 model units (one skin pixel once the head
layer scales the model by 0.625).
"""
import json, math, os
import numpy as np
from PIL import Image

NS = "mistbloom"
P = 1.6
RES = 1 / P


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
    "navy":     ["#6f7fc8", "#4f5ca6", "#3a4383", "#262c5c"],
    "midnight": ["#4a4f86", "#363a6b", "#262950", "#181a36"],
    "mist":     ["#f2eefc", "#d9d2f0", "#b8afd8", "#8f86b8"],
    "violet":   ["#d2b4f2", "#a986d8", "#7f5fb4", "#563c86"],
    "plum":     ["#c78ab8", "#9e6494", "#784672", "#522c50"],
    "moon":     ["#fffbe0", "#fdf0b4", "#f2d982", "#cfae5e"],
    "gold":     ["#fff3b4", "#ffd879", "#efb257", "#bf8343"],
    "amber":    ["#fffbe8", "#fff0b0", "#ffd77a", "#f7ae54"],
    "moonglow": ["#eafaff", "#bfe8fb", "#8ccbed", "#5b9bd0"],
    "cream":    ["#fff8e6", "#f9e6c4", "#e8cb9c", "#c7a477"],
    "leather":  ["#c08a5e", "#9c6b48", "#7a5038", "#573829"],
    "silver":   ["#eef0fa", "#c4cbdd", "#8890a8", "#565d74"],
    "coal":     ["#6e6a80", "#545066", "#3d3a4d", "#2a2838"],
    "blush":    ["#ffd2dc", "#ffb3c4", "#f593ab", "#d97391"],
    "wool":     ["#ffffff", "#e6e6ea", "#c8c8d0", "#a4a4b0"],
    "lav":      ["#f4eefe", "#dccef5", "#bba7e6", "#9077c4"],
    "glass":    ["#f6fdff", "#d4f0fb", "#a8d8ef", "#7fb0d8"],
    # wing ramps
    "dusk":     ["#b58bd0", "#8a5fae", "#653f8a", "#432862"],   # bat membrane
    "batbone":  ["#7a6a8e", "#5a4c70", "#3e3352", "#272036"],
    "wyrm":     ["#7fe0b4", "#3fb486", "#2a8566", "#1b5a4a"],   # nightwyrm teal
    "scale":    ["#4a4f62", "#33374a", "#222534", "#151722"],
    "ice":      ["#ffffff", "#dff6ff", "#a9dcf6", "#6fb2e6"],
    "petal":    ["#fff0fb", "#f6c9ea", "#dd9bd6", "#a970b8"],
    "petal2":   ["#f2ecff", "#cdbcf6", "#a690e2", "#7863b8"],
}.items()}

NFRAMES = 6
FRAMETIMES = [3, 3, 2, 3, 4, 3]
STATE = {"frame": 0}
SIDES = ("north", "south", "east", "west")


def animated(fn):
    fn.animated = True
    return fn


def fr():
    return STATE["frame"]


def T(ramp, tone, a=255):
    tone = max(0, min(6, int(round(tone))))
    r, g, b = RAMPS[ramp][tone]
    return (r, g, b, a)


def _blank(w, h):
    return np.zeros((h, w, 4), np.uint8)


def toon(ramp, tone=2, pattern=None, tint=False):
    """Clean cartoon shading for small solid parts."""
    def f(w, h, face, key):
        img = _blank(w, h)
        for y in range(h):
            for x in range(w):
                t = tone + (pattern(x, y, w, h, face) if pattern else 0)
                if face in SIDES:
                    if y == 0 and h > 2:
                        t -= 1
                    elif y == h - 1 and h > 2:
                        t += 1
                elif face == "up":
                    t -= 1
                else:
                    t += 2
                img[y, x] = T(ramp, t)
        return img
    f.tint = tint
    return f


def solid(ramp, tone=2):
    def f(w, h, face, key):
        img = _blank(w, h)
        img[:, :] = T(ramp, tone + (1 if face in ("east", "west") else 0) + (2 if face == "down" else 0))
        return img
    return f


def art_px(rows, pal):
    def f(w, h, face, key):
        img = _blank(w, h)
        ah, aw = len(rows), len(rows[0])
        for y in range(h):
            for x in range(w):
                ch = rows[min(ah - 1, int(y * ah / h))][min(aw - 1, int(x * aw / w))]
                if ch != ".":
                    img[y, x] = T(*pal[ch])
        return img
    return f


def twinkle(ramp="moon"):
    rows = ["..a..", "..b..", "abcba", "..b..", "..a.."]
    def f(W, H, face, key):
        k = fr()
        img = _blank(W, H)
        for y in range(H):
            for x in range(W):
                ch = rows[int(y * 5 / H)][int(x * 5 / W)]
                if ch == "a" and k not in (2, 5):
                    img[y, x] = T(ramp, 1)
                elif ch == "b":
                    img[y, x] = T(ramp, 0)
                elif ch == "c":
                    img[y, x] = T("amber", 0)
        return img
    return animated(f)


def _px(v):
    return [float(a) * P for a in v]


# ------------------------------------------------------------------- model
class Model:
    def __init__(self, name, kind="back", dye=None, scale=1.0):
        self.name, self.kind, self.elements, self.dye = name, kind, [], dye
        self.scale = scale          # head display scale, pivoting on the chest (model centre)

    def _u(self, v):
        """final player pixels -> compiled model units (pre-scale about the 8,8,8 pivot)."""
        return [8 + (float(a) * P - 8) / self.scale for a in v]

    def box(self, frm, to, mat, faces=None, rot=None, emit=0, res=RES):
        fs = faces or ("north", "south", "east", "west", "up", "down")
        e = {"from": list(map(float, frm)), "to": list(map(float, to)),
             "faces": {f: mat for f in fs}, "emit": emit, "res": res}
        if rot:
            axis, ang, org = rot
            e["rotation"] = {"angle": ang, "axis": axis, "origin": list(map(float, org))}
        self.elements.append(e)
        return e

    # player-pixel helpers
    def b(self, lo, hi, painter, rot=None, emit=0, faces=None, res=None, tpp=1):
        """Box in final player pixels; tpp = texels per final pixel."""
        r = (rot[0], rot[1], self._u(rot[2])) if rot else None
        res = res or tpp * self.scale / P
        return self.box(self._u(lo), self._u(hi), painter, faces=faces, rot=r, emit=emit, res=res)

    def c(self, lo, hi, painter, rot=None, emit=0, res=None, tpp=1):
        flat = [i for i in range(3) if lo[i] == hi[i]]
        assert len(flat) == 1, "card needs exactly one flat axis"
        fs = {0: ("east", "west"), 1: ("up", "down"), 2: ("north", "south")}[flat[0]]
        return self.b(lo, hi, painter, rot=rot, emit=emit, faces=fs, res=res, tpp=tpp)

    def check(self):
        n = len(self.elements)
        assert n < 15, f"{self.name}: {n} elements (cap 14)"
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
        for S in (16, 32, 64, 128, 256, 512, 1024, 2048):
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

        def fit(rx, ry, size):
            s = min(4.0, size / ext)
            R = _rx(rx) @ _ry(ry)
            t = np.clip(-(R @ ((c - 8) * s)), -80, 80)
            return {"rotation": [rx, ry, 0], "translation": [round(float(v), 3) for v in t],
                    "scale": [round(s, 4)] * 3}
        kind = self.kind
        if kind == "back":
            return {
                # gui shows the piece from behind, a little turned
                "gui": fit(15, 160, 15.5), "ground": fit(0, 0, 8.0), "fixed": fit(0, 180, 14.0),
                # HMC backpack: marker armor stand riding the player, head ~2.43 blocks above chest
                "head": {"rotation": [0, 0, 0], "translation": [0, BACK_DROP, 0], "scale": [self.scale] * 3},
                "thirdperson_righthand": fit(10, 160, 8.0), "firstperson_righthand": fit(0, 160, 8.0),
            }
        d = {"gui": fit(20, 200, 15.0), "ground": fit(0, 0, 8.0), "fixed": fit(0, 180, 14.0)}
        if kind in ("hat", "balloon"):
            # authored on the player's head: 1 px = 1.6 units, head = 1.6..14.4
            d["head"] = {"rotation": [0, 0, 0], "translation": [0, 0, 0], "scale": [self.scale] * 3}
        if kind == "hand":
            # held items: authored standing upright around the model centre, handle at the top
            # rotation x 90 stands the model upright in the hand; translation is (side, forward, up)
            hand = getattr(self, "hand", None) or {"rotation": [90, 0, 0], "translation": [0, 0, 0], "scale": [0.375] * 3}
            d["thirdperson_righthand"] = d["thirdperson_lefthand"] = hand
            d["firstperson_righthand"] = d["firstperson_lefthand"] = {
                "rotation": [0, -10, 0], "translation": [1, 2, 0], "scale": [0.55] * 3}
            d["head"] = {"rotation": [0, 0, 0], "translation": [0, 0, 0], "scale": [1, 1, 1]}
        return d

    def to_json(self, tex, credit):
        els = []
        k = 16 / self.S
        for i, e in enumerate(self.elements):
            je = ({"name": e["name"]} if e.get("name") else {})
            je.update({"from": [round(v, 4) for v in e["from"]], "to": [round(v, 4) for v in e["to"]]})
            if "rotation" in e:
                je["rotation"] = {**e["rotation"], "origin": [round(v, 4) for v in e["rotation"]["origin"]]}
            if e["emit"]:
                je["light_emission"] = e["emit"]
            faces = {}
            for f in e["faces"]:
                x1, y1, x2, y2 = self.uv[(i, f)]
                faces[f] = {"uv": [round(x1 * k, 4), round(y1 * k, 4), round(x2 * k, 4), round(y2 * k, 4)],
                            "texture": "#0"}
                if getattr(e["faces"][f], "tint", False):
                    faces[f]["tintindex"] = 0
            je["faces"] = faces
            els.append(je)
        return {"credit": credit, "texture_size": [self.S, self.S],
                "textures": {"0": tex, "particle": tex}, "elements": els, "display": self.display()}

    def export(self, root, credit):
        self.bake()
        tdir = os.path.join(root, "assets", NS, "textures", "cosmetics")
        mdir = os.path.join(root, "assets", NS, "models", "cosmetics")
        idir = os.path.join(root, "assets", NS, "items")
        for d in (tdir, mdir, idir):
            os.makedirs(d, exist_ok=True)
        vid = self.name
        if self.is_animated():
            frames = [self.bake(k).copy() for k in range(NFRAMES)]
            self.bake(0)
            Image.fromarray(np.concatenate(frames, 0)).save(os.path.join(tdir, vid + ".png"))
            json.dump({"animation": {"interpolate": False, "frames": [
                {"index": i, "time": t} for i, t in enumerate(FRAMETIMES)]}},
                open(os.path.join(tdir, vid + ".png.mcmeta"), "w"), indent=1)
        else:
            Image.fromarray(self.atlas).save(os.path.join(tdir, vid + ".png"))
        json.dump(self.to_json(f"{NS}:cosmetics/{vid}", credit), open(os.path.join(mdir, vid + ".json"), "w"), indent=1)
        model = {"type": "minecraft:model", "model": f"{NS}:cosmetics/{vid}"}
        if self.dye:
            r, g, b = self.dye
            model["tints"] = [{"type": "minecraft:dye", "default": (r << 16) | (g << 8) | b}]
        json.dump({"model": model}, open(os.path.join(idir, vid + ".json"), "w"), indent=1)

    # ------------------------------------------------------------ render
    def render(self, ppu=6, cam=(-0.62, 0.5, -1.0), frame=0, dye=None, extra=()):
        scene = [(self, 0.0)] + list(extra)
        for m, _ in scene:
            m.bake(frame)
        c = np.array(cam, float); c /= np.linalg.norm(c)
        fwd = -c
        right = np.cross(fwd, [0, 1, 0]); right /= np.linalg.norm(right)
        up = np.cross(right, fwd)
        quads = []
        for m, dy in scene:
            for i, e in enumerate(m.elements):
                for f in e["faces"]:
                    corners = _face_corners(e, f)
                    n = _NORMALS[f]
                    sc = getattr(m, "scale", 1.0)
                    if "rotation" in e:
                        r = e["rotation"]
                        M = {"x": _rx, "y": _ry, "z": _rz}[r["axis"]](r["angle"])
                        o = np.array(r["origin"])
                        corners = [M @ (p - o) + o for p in corners]
                        n = M @ n
                    corners = [8 + (p - 8) * sc + np.array([0, dy, 0]) for p in corners]
                    if len(e["faces"]) != 2 and np.dot(n, c) <= 0:
                        continue
                    if len(e["faces"]) == 2 and np.dot(n, c) <= 0:
                        continue   # cards: draw only the face looking at the camera
                    quads.append((corners, m, i, f, e["emit"]))
        pts = np.array([p for q in quads for p in q[0]])
        sx, sy = pts @ right, -(pts @ up)
        minx, miny = sx.min(), sy.min()
        W = int(math.ceil((sx.max() - minx) * ppu)) + 4
        H = int(math.ceil((sy.max() - miny) * ppu)) + 4
        img = np.zeros((H, W, 4), np.uint8)
        zb = np.full((H, W), np.inf)
        shade = {"up": 1.0, "down": 0.5, "north": 0.8, "south": 0.8, "east": 0.62, "west": 0.62}
        for pass_ in (0, 1):
            seq = quads if pass_ == 0 else sorted(quads, key=lambda q: -np.mean([p @ fwd for p in q[0]]))
            for corners, m, i, f, emit in seq:
                Pp = np.array([[(p @ right - minx) * ppu + 2, (-(p @ up) - miny) * ppu + 2, p @ fwd] for p in corners])
                o, e1, e2 = Pp[0], Pp[1] - Pp[0], Pp[3] - Pp[0]
                A = np.array([[e1[0], e2[0]], [e1[1], e2[1]]])
                if abs(np.linalg.det(A)) < 1e-9:
                    continue
                Ai = np.linalg.inv(A)
                x0, x1 = int(max(0, Pp[:, 0].min())), int(min(W, Pp[:, 0].max() + 1))
                y0, y1 = int(max(0, Pp[:, 1].min())), int(min(H, Pp[:, 1].max() + 1))
                if x1 <= x0 or y1 <= y0:
                    continue
                gx, gy = np.meshgrid(np.arange(x0, x1) + 0.5, np.arange(y0, y1) + 0.5)
                dx, dyy = gx - o[0], gy - o[1]
                a = Ai[0, 0] * dx + Ai[0, 1] * dyy
                b = Ai[1, 0] * dx + Ai[1, 1] * dyy
                msk = (a >= 0) & (a <= 1) & (b >= 0) & (b <= 1)
                z = o[2] + a * e1[2] + b * e2[2]
                u1, v1, u2, v2 = m.uv[(i, f)]
                tx = np.clip((u1 + a * (u2 - u1)).astype(int), u1, u2 - 1)
                ty = np.clip((v1 + b * (v2 - v1)).astype(int), v1, v2 - 1)
                tex = m.atlas[ty, tx]
                al = tex[..., 3]
                msk &= (al >= 200) if pass_ == 0 else ((al > 8) & (al < 200))
                sub = zb[y0:y1, x0:x1]
                msk &= z < sub - 1e-6
                if not msk.any():
                    continue
                k = 1.0 if emit >= 8 else shade[f]
                col = tex[..., :3].astype(float) * k
                if getattr(m.elements[i]["faces"][f], "tint", False):
                    col = col * (np.array(dye or m.dye or (255, 255, 255), float) / 255)
                region = img[y0:y1, x0:x1]
                if pass_ == 0:
                    region[msk, :3] = np.clip(col[msk], 0, 255).astype(np.uint8)
                    region[msk, 3] = 255
                    sub[msk] = z[msk]
                else:
                    aa = (al[msk] / 255.0)[:, None]
                    base = region[msk, :3].astype(float)
                    empty = (region[msk, 3] == 0)[:, None]
                    mixed = np.where(empty, col[msk], col[msk] * aa + base * (1 - aa))
                    region[msk, :3] = np.clip(mixed, 0, 255).astype(np.uint8)
                    region[msk, 3] = np.maximum(region[msk, 3], al[msk])
        return Image.fromarray(img)


BACK_DROP = -62.08

_NORMALS = {"north": np.array([0, 0, -1.]), "south": np.array([0, 0, 1.]), "east": np.array([1., 0, 0]),
            "west": np.array([-1., 0, 0]), "up": np.array([0, 1., 0]), "down": np.array([0, -1., 0])}


def _face_corners(e, f):
    (x0, y0, z0), (x1, y1, z1) = e["from"], e["to"]
    Pt = lambda x, y, z: np.array([x, y, z], float)
    return {
        "north": [Pt(x1, y1, z0), Pt(x0, y1, z0), Pt(x0, y0, z0), Pt(x1, y0, z0)],
        "south": [Pt(x0, y1, z1), Pt(x1, y1, z1), Pt(x1, y0, z1), Pt(x0, y0, z1)],
        "east":  [Pt(x1, y1, z1), Pt(x1, y1, z0), Pt(x1, y0, z0), Pt(x1, y0, z1)],
        "west":  [Pt(x0, y1, z0), Pt(x0, y1, z1), Pt(x0, y0, z1), Pt(x0, y0, z0)],
        "up":    [Pt(x0, y1, z0), Pt(x1, y1, z0), Pt(x1, y1, z1), Pt(x0, y1, z1)],
        "down":  [Pt(x0, y0, z1), Pt(x1, y0, z1), Pt(x1, y0, z0), Pt(x0, y0, z0)],
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
