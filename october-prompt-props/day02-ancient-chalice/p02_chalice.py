"""Day 2 Relic - Ancient Chalice Gold chalice with a ruby on a stone pedestal, red altar cloth, moss and ivy.."""
import numpy as np
from engine import Model, SIDES
from px import PAL, hx, material, card_art, _uv, C, inset, lobes, despeckle

PAL["chalgold"] = [hx(c) for c in ("#fff4b0", "#ffd650", "#e8a82a", "#b0701c", "#744614")]
PAL["ruby"] = [hx(c) for c in ("#ffb4c0", "#f43a52", "#c0142e", "#7c0a20", "#4a0614")]
PAL["wine"] = [hx(c) for c in ("#d04868", "#a02446", "#741434", "#500c24", "#320616")]


def _cut(t, u, v, face, w, h):
    t[:, :] = 2
    a, b = u, v
    row = b // 4
    joint_h = (b % 4 == 3)
    joint_v = ((a + (row % 2) * 3) % 6 == 5) & ~joint_h
    t[(b % 4 == 0)] = 1
    t[joint_h] = 3
    t[joint_v] = 3
    blk = ((a + (row % 2) * 3) // 6 * 7 + row * 3) % 5
    t[(blk == 0) & ~joint_h & ~joint_v & (b % 4 != 0)] = 3
    t[(blk == 0) & (b % 4 == 0) & ~joint_v] = 2
    if face == "up":
        t[:, :] = 2
        t[(b % 6 == 5) | ((a + (b // 6 % 2) * 4) % 8 == 7)] = 3
    t[:, :] = despeckle(t)


def clean(img):
    h, w = img.shape[:2]
    out = img.copy()
    key = img[..., 0].astype(int) * 65536 + img[..., 1].astype(int) * 256 + img[..., 2]
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            nb = {key[y - 1, x], key[y + 1, x], key[y, x - 1], key[y, x + 1]}
            if len(nb) == 1 and key[y, x] not in nb:
                out[y, x] = img[y - 1, x]
    for y in range(h):
        for x in range(w):
            if 0 < y < h - 1 and 0 < x < w - 1:
                continue
            nbs = [(yy, xx) for yy, xx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)) if 0 <= yy < h and 0 <= xx < w]
            ks = {key[a, b] for a, b in nbs}
            if len(nbs) >= 3 and len(ks) == 1 and key[y, x] not in ks:
                out[y, x] = img[nbs[0]]
    return out


def stone(carve=None, moss=(), coins=()):
    def d(t, u, v, face, w, h):
        _cut(t, u, v, face, w, h)
        if carve:
            carve(t, face, w, h)
    st = material("stone", "plain", detail=d)

    def f(w, h, face, key):
        img = clean(st(w, h, face, key))
        if face == "up":
            u, v, _ = _uv()
            for (a, b, c, e) in moss:
                mk = (u >= a) & (u < b) & (v >= c) & (v < e)
                img[mk] = C("moss", 2)
                img[mk & (v == c)] = C("moss", 1)
                img[mk & (v == e - 1) & (u > a)] = C("moss", 3)
            for (a, b) in coins:
                img[(u == a) & (v == b)] = C("chalgold", 0)
                img[((u == a + 1) & (v == b)) | ((u == a) & (v == b + 1))] = C("chalgold", 1)
                img[(u == a + 1) & (v == b + 1)] = C("chalgold", 3)
        return img
    return f


def plinth_carve(t, face, w, h):
    if face in SIDES:
        t[:, :] = 2


def body_carve(t, face, w, h):
    if face in SIDES:
        t[:, :] = 2
        inset(t, 1, 1, w - 2, h - 2)
        t[2:h - 2, 2:w - 2] = 3


def cornice_carve(t, face, w, h):
    if face in SIDES:
        t[:, :] = 2
        t[-1, :] = 3
        t[-1, ::3] = 4
        t[-1, 1::3] = 4


def gold(top_rim=True):
    def f(w, h, face, key):
        t = np.full((h, w), 2, int)
        if face in SIDES:
            if w >= 4:
                t[:, 0] = 1; t[:, 1] = 0; t[:, -2] = 3; t[:, -1] = 3
            else:
                t[:, 0] = 1; t[:, -1] = 3
            if h >= 3:
                t[0, :] = np.maximum(0, t[0, :] - 1)
                t[-1, :] = np.minimum(4, t[-1, :] + 1)
        elif face == "up":
            t[:, :] = 1
            t[:, -1] = 2; t[-1, :] = 2
        else:
            t[:, :] = 3
        img = np.zeros((h, w, 4), np.uint8)
        for k in range(5):
            img[t == k] = C("chalgold", k)
        return img
    return f


def bowl():
    g = gold()

    def f(w, h, face, key):
        img = g(w, h, face, key)
        if face == "up":
            u, v, _ = _uv()
            iu, iv = u - u.min(), v - v.min()
            inner = (iu >= 1) & (iu < w - 1) & (iv >= 1) & (iv < h - 1)
            img[~inner] = C("chalgold", 1)
            img[~inner & ((iu == w - 1) | (iv == h - 1))] = C("chalgold", 2)
            img[inner] = C("wine", 2)
            img[inner & ((iu == 1) | (iv == 1))] = C("wine", 4)
            img[inner & (iu >= 3) & (iu <= 4) & (iv >= 3) & (iv <= 4)] = C("wine", 1)
            img[inner & (iu == 3) & (iv == 3)] = C("wine", 0)
        return img
    return f


def cloth(front=False):
    def f(w, h, face, key):
        t = np.full((h, w), 2, int)
        if face in SIDES:
            prof = ([1, 1, 2, 3, 3] * 3)[:w] if w >= 5 else ([1] + [2] * (w - 2) + [3] if w >= 3 else [2] * w)
            t[:, :] = np.array(prof)[None, :]
        elif face == "up":
            t[:, :] = 1; t[-1, :] = 2
        else:
            t[:, :] = 3
        img = np.zeros((h, w, 4), np.uint8)
        for k in range(5):
            img[t == k] = C("red", k)
        if front and face in ("north", "south"):
            img[-3, :] = C("chalgold", 1)
            img[-2, :] = C("chalgold", 3)
            img[-1, ::2] = C("chalgold", 2)
            img[-1, 1::2] = (0, 0, 0, 0)
        return img
    return f


MOSS_DRAPE = ["MMMMMM", "MmMMmM", "m.Mm.m", "..m.m."]
IVY = [".LL..", "LLgb.", "..bLL", "gb.Lg", "Lgb..", "..b.."]
MOSS_P = {"M": ("moss", 1), "m": ("moss", 2)}
IVY_P = {"L": ("leaf", 1), "g": ("leaf", 2), "b": ("leaf", 3)}


def ruby():
    def d(t, u, v, face, w, h):
        t[:, :] = 2
        if face == "north":
            t[0, 0] = 0
            t[-1, :] = 3
            t[:, -1] = 3
    return material("ruby", "plain", edge=False, detail=d)


def build():
    m = Model("ancient_chalice")
    m.box([0, 0, 0], [16, 2, 16], stone(carve=plinth_carve, moss=((0, 5, 0, 2), (0, 2, 2, 6), (12, 16, 13, 16)),
                                         coins=((4, 3), (12, 3), (2, 12))))
    m.box([2, 2, 2], [14, 3, 14], stone(carve=plinth_carve))
    m.box([3, 3, 3], [13, 10, 13], stone(carve=body_carve))
    m.box([2, 10, 2], [14, 12, 14], stone(carve=cornice_carve, moss=((10, 14, 10, 14),)))
    m.box([5, 12, 1.5], [10, 12.5, 7], cloth())
    m.box([5, 6, 1.5], [10, 12, 2], cloth(front=True))
    m.card([13.1, 6, 4], [13.1, 10, 10], card_art(MOSS_DRAPE, MOSS_P))
    m.card([10, 3, 2.5], [15, 9, 2.5], card_art(IVY, IVY_P), rot=("y", 22.5, [12.5, 3, 2.5]))
    m.box([5, 12, 5], [11, 13, 11], gold())
    m.box([7, 13, 7], [9, 16, 9], gold())
    m.box([6, 16, 6], [10, 18, 10], gold())                     # bowl base (cup tapers down)
    m.box([5, 18, 5], [11, 21, 11], gold())
    m.box([4, 21, 4], [12, 23, 12], bowl())
    m.box([7, 18.5, 4.5], [9, 20.5, 5], ruby(), emit=4)
    return m
