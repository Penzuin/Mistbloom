"""October Prompt Props - model engine (Mistbloom Studios).
Copy of claude/inktober/engine.py, keeping the parts the vanilla-res pieces need
(boxes, cards, atlas bake, item-model JSON, preview renderer)."""
import json, math
import numpy as np
from PIL import Image

NS = "inkprops"
CREDIT = "October Prompt Props by Mistbloom Studios"

NFRAMES = 8
FRAMETIMES = [3] * 8
STATE = {"frame": 0}
SIDES = ("north", "south", "east", "west")


def animated(fn):
    fn.animated = True
    return fn


def fr():
    return STATE["frame"]


def _blank(w, h):
    return np.zeros((h, w, 4), np.uint8)


def sprite(draw, mirror_back=True):
    cache = {}
    def f(w, h, face, key):
        k = fr(); ck = (w, h, k)
        if ck not in cache:
            cache[ck] = draw(w, h, k)
        img = cache[ck].copy()
        if mirror_back and face in ("south", "west", "down"):
            img = img[:, ::-1].copy()
        return img
    return animated(f)


class Model:
    def __init__(self, name, floor=0):
        self.name, self.floor, self.elements = name, floor, []

    def box(self, frm, to, mat, faces=None, rot=None, emit=0, over=None, res=1, name=None):
        fs = faces or ("north", "south", "east", "west", "up", "down")
        e = {"from": list(map(float, frm)), "to": list(map(float, to)),
             "faces": {f: (over or {}).get(f, mat) for f in fs}, "emit": emit, "res": res, "name": name}
        if any(getattr(p, "noshade", False) for p in e["faces"].values()):
            e["shade"] = False
        if rot:
            axis, ang, org = rot
            e["rotation"] = {"angle": ang, "axis": axis, "origin": list(map(float, org))}
        self.elements.append(e)
        return e

    def card(self, frm, to, painter, rot=None, emit=0, res=1, name=None):
        flat = [i for i in range(3) if frm[i] == to[i]]
        assert len(flat) == 1, "card needs exactly one flat axis"
        fs = {0: ("east", "west"), 1: ("up", "down"), 2: ("north", "south")}[flat[0]]
        return self.box(frm, to, painter, faces=fs, rot=rot, emit=emit, res=res, name=name)

    def check(self, cap=14):
        n = len(self.elements)
        assert n <= cap, f"{self.name}: {n} elements (cap {cap})"
        for e in self.elements:
            for v in e["from"] + e["to"]:
                assert -16.05 <= v <= 32.05
            r = e.get("rotation")
            if r:
                assert r["angle"] in (-45, -22.5, 0, 22.5, 45)
            assert e.get("res", 1) == 1
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
                    ok = False; break
                pos[k] = (x, y); x += w; rowh = max(rowh, h)
            if ok:
                break
        atlas = np.zeros((S, S, 4), np.uint8)
        self.uv = {}
        for k, (i, f, w, h, painter) in enumerate(items):
            px, py = pos[k]
            STATE["pos"], STATE["normal"] = texel_world(self.elements[i], f, w, h)
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
            je = {}
            if e.get("name"):
                je["name"] = e["name"]
            je["from"], je["to"] = e["from"], e["to"]
            if "rotation" in e:
                je["rotation"] = e["rotation"]
            if e["emit"]:
                je["light_emission"] = e["emit"]
            if e.get("shade") is False:
                je["shade"] = False
            fcs = {}
            for f in e["faces"]:
                x1, y1, x2, y2 = self.uv[(i, f)]
                k = 16 / self.S
                fcs[f] = {"uv": [round(x1 * k, 4), round(y1 * k, 4), round(x2 * k, 4), round(y2 * k, 4)], "texture": "#0"}
            je["faces"] = fcs
            els.append(je)
        return {"credit": CREDIT, "texture_size": [self.S, self.S],
                "textures": {"0": tex, "particle": tex}, "elements": els, "display": self.display()}

    def render(self, ppu=6, cam=(-0.62, 0.62, -1.0), frame=0):
        if not hasattr(self, "atlas") or getattr(self, "_frame", None) != frame:
            self.bake(frame); self._frame = frame
        c = np.array(cam, float); c /= np.linalg.norm(c)
        fwd = -c
        right = np.cross(fwd, [0, 1, 0]); right /= np.linalg.norm(right)
        up = np.cross(right, fwd)
        self._cam = (right, up, fwd)
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
        self._origin = (minx, miny)
        W = int(math.ceil((sx.max() - minx) * ppu)) + 4
        H = int(math.ceil((sy.max() - miny) * ppu)) + 4
        img = np.zeros((H, W, 4), np.uint8)
        zb = np.full((H, W), np.inf)
        shade = {"up": 1.0, "down": 0.5, "north": 0.8, "south": 0.8, "east": 0.62, "west": 0.62}
        for pass_ in (0, 1):
            seq = quads if pass_ == 0 else sorted(quads, key=lambda q: -np.mean([p @ fwd for p in q[0]]))
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
                k = 1.0 if (emit >= 10 or self.elements[i].get("shade") is False) else shade[f]
                if "rotation" in self.elements[i] and f in ("up", "down"):
                    k = 0.95 if f == "up" else 0.5
                if len(self.elements[i]["faces"]) == 2:
                    k = max(k, 0.9)
                col = tex[..., :3].astype(float) * k
                region = img[y0:y1, x0:x1]
                if pass_ == 0:
                    region[m, :3] = np.clip(col[m], 0, 255).astype(np.uint8); region[m, 3] = 255; sub[m] = z[m]
                else:
                    aa = (al[m] / 255.0)[:, None]
                    base = region[m, :3].astype(float)
                    empty = (region[m, 3] == 0)[:, None]
                    mixed = np.where(empty, col[m], col[m] * aa + base * (1 - aa))
                    region[m, :3] = np.clip(mixed, 0, 255).astype(np.uint8)
                    region[m, 3] = np.maximum(region[m, 3], al[m])
        return Image.fromarray(img)


def texel_world(e, f, w, h):
    c = _face_corners(e, f)
    n = _NORMALS[f]
    if "rotation" in e:
        r = e["rotation"]
        M = {"x": _rx, "y": _ry, "z": _rz}[r["axis"]](r["angle"])
        o = np.array(r["origin"])
        c = [M @ (p - o) + o for p in c]
        n = M @ n
    u = (np.arange(w) + 0.5) / w
    v = (np.arange(h) + 0.5) / h
    P = c[0][None, None, :] + u[None, :, None] * (c[1] - c[0])[None, None, :] + v[:, None, None] * (c[3] - c[0])[None, None, :]
    return P, n


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
