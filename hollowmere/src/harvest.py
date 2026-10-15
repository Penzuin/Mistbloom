"""Hollowmere harvest batch. Front faces NORTH (-z). Max 14 elements per model."""
import random
import engine
from engine import Model, wood, solid, stripes, T, _blank, fr, SIDES, art, wheel, staves
from hero3 import pump_skin, bark, iron, plaid2, LEAF, CURL, glow_core, painted_jack, leaf_tex
from spooky import hay, STRAW

engine.RAMPS.update({k: engine._ramp7(v) for k, v in {
    "apple":   ["#ff8a8a", "#e04b4b", "#ad2e3c", "#701e2e"],
    "caramel": ["#ffd79a", "#e8a95a", "#b97636", "#7f4b25"],
    "wicker":  ["#e8c88f", "#c99f62", "#9d7442", "#6b4b2c"],
    "gourd":   ["#fff3b0", "#f2d65c", "#c9a63a", "#8b7128"],
    "squash":  ["#b9d98c", "#7fae5a", "#55813f", "#36572c"],
}.items()})


# ------------------------------------------------------------------ painters
def wicker():
    def f(w, h, fc, key):
        img = _blank(w, h)
        for y in range(h):
            for x in range(w):
                over = ((x // 2) + (y // 2)) % 2 == 0
                img[y, x] = T("wicker", 1 if over else 3)
                if (x % 2 == 1) and over:
                    img[y, x] = T("wicker", 2)
        if fc == "down":
            img[:, :] = T("wicker", 4)
        return img
    return f


def apple(caramel=True):
    def f(w, h, fc, key):
        img = _blank(w, h)
        img[:, :] = T("apple", 1)
        if fc in SIDES:
            img[0, :] = T("apple", 0)
            if caramel:
                cut = h // 2
                img[cut:, :] = T("caramel", 1)
                for x in range(0, w, 2):
                    img[cut - 1, x] = T("caramel", 1)               # caramel drips
                img[-1, :] = T("caramel", 3)
            img[1, max(0, w // 3)] = T("apple", 0)                  # shine
        if fc == "up":
            img[:, :] = T("apple", 2)
            img[h // 2, w // 2] = T("caramel", 3)
        if fc == "down":
            img[:, :] = T("caramel", 3) if caramel else T("apple", 4)
        return img
    return f


def candy():
    cols = ["plum", "pump", "brew", "blush", "candle"]
    def f(w, h, fc, key):
        rng = random.Random(key)
        img = _blank(w, h)
        for y in range(h):
            for x in range(w):
                img[y, x] = T(rng.choice(cols), rng.choice([1, 1, 2]))
        return img
    return f


def wrapper(c="plum"):
    def f(w, h, fc, key):
        img = _blank(w, h)
        img[:, :] = T(c, 1)
        if fc in ("north", "south", "up") and w >= 3:
            img[:, ::2] = T(c, 0)                                    # twisted stripes
        return img
    return f


def gourd_skin(ramp="gourd"):
    def f(w, h, fc, key):
        img = _blank(w, h)
        for y in range(h):
            for x in range(w):
                img[y, x] = T(ramp, 1 if (x + y // 2) % 3 else 2)
        if fc == "down":
            img[:, :] = T(ramp, 4)
        return img
    return f


def blanket():
    def f(w, h, fc, key):
        img = _blank(w, h)
        for y in range(h):
            for x in range(w):
                img[y, x] = T("plum" if (x // 3) % 2 == 0 else "bone", 2 if (y % 4) else 3)
        if fc in SIDES and h >= 2:
            for x in range(0, w, 2):
                img[-1, x] = T("pump", 1)                            # little tassels
        return img
    return f


def chalk(word_rows):
    def f(w, h, fc, key):
        img = _blank(w, h)
        img[:, :] = T("coal", 3)
        if w > 4 and h > 4:
            img[0, :] = img[-1, :] = T("spruce", 2)
            img[:, 0] = img[:, -1] = T("spruce", 2)
        if fc == "north":
            for gy, row in enumerate(word_rows):
                for gx, ch in enumerate(row):
                    x, y = 2 + gx, 2 + gy
                    if ch != "." and x < w - 1 and y < h - 1:
                        img[y, x] = T({"a": "bone", "o": "pump", "g": "brew"}[ch], 0)
        return img
    return f


def loose_hay():
    """Loose piled hay: streaky stalks, no twine bands."""
    def f(w, h, fc, key):
        rng = random.Random(key)
        img = _blank(w, h)
        for y in range(h):
            for x in range(w):
                img[y, x] = T("hay", 2)
        for i in range(w * h // 3):
            x, y = rng.randrange(w), rng.randrange(h)
            L = rng.randint(1, 3)
            tone = rng.choice([0, 1, 3])
            for k in range(L):
                yy = y + k if fc in SIDES else y
                xx = x if fc in SIDES else x + k
                if 0 <= yy < h and 0 <= xx < w:
                    img[yy, xx] = T("hay", tone)
        if fc == "down":
            img[:, :] = T("hay", 4)
        return img
    return f


def cask():
    """Barrel lying along x: planks run along the length, iron hoops near the ends; end caps show rings."""
    def f(w, h, fc, key):
        img = _blank(w, h)
        if fc in ("east", "west"):
            cx, cy = (w - 1) / 2, (h - 1) / 2
            for y in range(h):
                for x in range(w):
                    d = max(abs(x - cx) / max(cx, 1), abs(y - cy) / max(cy, 1))
                    img[y, x] = T("oak", 1 if d < 0.4 else 2 if d < 0.75 else 3)
                    if 0.86 < d:
                        img[y, x] = T("iron", 2)
            return img
        for y in range(h):
            for x in range(w):
                img[y, x] = T("oak", 1 + (y // 2) % 2 + (1 if y % 2 == 0 else 0))
        for hx in (2, 3, w - 4, w - 3):
            if 0 <= hx < w:
                img[:, hx] = T("iron", 2)
        mid = w // 2
        img[:, mid] = T("iron", 3)
        return img
    return f


# ------------------------------------------------------------------ builders
def pumpkin(m, lo, hi, stem=True, ramp_skin=None):
    """Plain round pumpkin: crossed body, low crown, stem. 3-4 elements."""
    (x0, y0, z0), (x1, y1, z1) = lo, hi
    W, H, D = x1 - x0, y1 - y0, z1 - z0
    sk = ramp_skin or pump_skin()
    top2 = y1 - H * .04                                       # the two crossed halves keep >= 0.4px apart
    m.box([x0, y0 + max(H * .1, .4), z0 + D * .12], [x1, top2 - max(H * .1, .4), z1 - D * .12], sk, res=2)
    m.box([x0 + W * .12, y0, z0], [x1 - W * .12, top2, z1], sk, res=2)
    if stem:
        cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
        s = max(0.8, W * .14)
        m.box([cx - s / 2, y1 - H * .1, cz - s / 2], [cx + s / 2, y1 + H * .18, cz + s / 2], bark("stem"),
              rot=("z", -22.5, [cx, y1, cz]))


# ------------------------------------------------------------------ pieces
def pumpkin_pile():
    m = Model("pumpkin_pile")
    pumpkin(m, [1, 0, 3], [10, 7, 12])                                            # big
    pumpkin(m, [8.5, 0, 1.5], [15, 5, 7.5])                                       # medium, front right
    pumpkin(m, [9, 0, 9], [14.5, 4.5, 14.5], stem=False)                          # small, back
    pumpkin(m, [9.5, 4.5, 9.5], [13.5, 7.5, 13.5], ramp_skin=gourd_skin("squash"))  # green squash on top
    return m


def gourd_basket():
    m = Model("gourd_basket")
    m.box([3, 0, 4], [13, 5, 12], wicker())                                       # basket
    RIM = solid("wicker", 3)                                                       # rim: four solid strips, so there is
    m.box([2.5, 4.6, 3.5], [13.5, 6, 4.5], RIM)                                    # no hollow to see through
    m.box([2.5, 4.6, 11.5], [13.5, 6, 12.5], RIM)
    m.box([2.5, 4.6, 4.5], [3.5, 6, 11.5], RIM)
    m.box([12.5, 4.6, 4.5], [13.5, 6, 11.5], RIM)
    m.box([2.6, 5, 7.4], [3.6, 11, 8.6], solid("wicker", 2))                      # arched handle
    m.box([12.4, 5, 7.4], [13.4, 11, 8.6], solid("wicker", 2))
    m.box([2.6, 10.6, 7.4], [13.4, 11.6, 8.6], solid("wicker", 2))
    m.box([4, 4.5, 5], [7.5, 7.5, 8.5], gourd_skin("gourd"))                      # gourds peeking out
    m.box([7.5, 4.5, 8], [11.5, 7, 11.5], gourd_skin("squash"))
    m.box([8.5, 4.5, 4.5], [12, 8, 7.5], pump_skin())
    m.box([5.4, 7.5, 6.4], [6.2, 9, 7.2], bark("stem"), rot=("z", 22.5, [5.8, 7.5, 6.8]))  # gourd neck
    return m


def hay_bale_seat():
    m = Model("hay_bale_seat")
    m.box([1, 0, 3], [15, 8, 13], hay())                                          # bale
    m.box([3.5, 7.9, 2.5], [12.5, 8.4, 13.5], blanket(), faces=("up", "north", "south"))   # blanket, centred on the bale
    m.box([3.5, 4.5, 2.4], [12.5, 8.4, 2.5], blanket(), faces=("north",))          # hangs down the front...
    m.box([3.5, 4.5, 13.5], [12.5, 8.4, 13.6], blanket(), faces=("south",))        # ...and the back, the same
    pumpkin(m, [11, 8, 9], [14.5, 11, 12.5])                                      # little pumpkin on the corner
    m.card([0, 6, 8], [3, 10, 8], STRAW, rot=("y", 22.5, [1.5, 8, 8]))
    m.card([13, 6, 4], [16, 10, 4], STRAW, rot=("y", -22.5, [14.5, 8, 4]))
    return m


def haystack():
    m = Model("haystack", floor=-16)
    LH = loose_hay()
    m.box([-1, -16, 2], [17, -6, 14], LH)                                         # broad base, crossed
    m.box([2, -16, -1], [14, -6.5, 17], LH)
    m.box([1, -7, 3], [15, 1, 13], LH, rot=("y", 45, [8, -7, 8]))                 # shoulder, turned 45 so the ledge breaks up
    m.box([3, -1, 4], [13, 4, 12], LH)                                            # top, crossed
    m.box([4, -1.2, 3], [12, 3.8, 13], LH)
    m.box([5.5, 4, 6], [10.5, 6, 10], LH, rot=("y", 22.5, [8, 4, 8]))            # tuft
    m.box([10.5, -7, 3.5], [11.5, 12, 4.5], wood("oak"), rot=("z", -22.5, [11, -7, 4]))   # pitchfork
    m.box([9, 12, 3.5], [13, 12.8, 4.5], iron(), rot=("z", -22.5, [11, -7, 4]))
    for x in (9, 10.6, 12.2):
        m.box([x, 12.8, 3.6], [x + 0.8, 16.5, 4.4], iron(), rot=("z", -22.5, [11, -7, 4]))  # tines
    m.card([-2, -12, 8], [2, -7, 8], STRAW, rot=("y", 45, [0, -9, 8]))
    return m


def pumpkin_cart():
    m = Model("pumpkin_cart")
    m.box([-6, 4, 3], [22, 7, 13], wood("spruce", border=True))                  # cart bed, 2 wide
    m.box([-6, 7, 2.5], [22, 10, 3.5], wood("spruce"))                            # side rails
    m.box([-6, 7, 12.5], [22, 10, 13.5], wood("spruce"))
    m.box([2, 0, 1.5], [10, 8, 2.5], wheel())                                     # wheels
    m.box([2, 0, 13.5], [10, 8, 14.5], wheel())
    m.box([22, 5, 6.5], [30, 6.2, 7.5], wood("oak"))                              # handles
    m.box([22, 5, 8.5], [30, 6.2, 9.5], wood("oak"))
    pumpkin(m, [-4, 7, 4], [5, 13, 12])
    pumpkin(m, [6, 7, 4.5], [13, 11.5, 11.5], stem=False)
    m.box([14, 7, 5], [20, 10.5, 11], gourd_skin("squash"))
    m.box([-6.5, 7, 3.5], [-5.5, 10, 12.5], wood("spruce"))                       # tailboard
    return m


def caramel_apple_tray():
    m = Model("caramel_apple_tray")
    m.box([2, 0, 3], [14, 1.2, 13], wood("oak", border=True))                     # tray
    m.box([1.5, 1.2, 2.5], [14.5, 2, 3.5], wood("oak"))                           # raised lip
    m.box([1.5, 1.2, 12.5], [14.5, 2, 13.5], wood("oak"))
    for (x, z, c) in ((3, 5, True), (7.5, 4.5, True), (4, 9, True), (9, 9, False)):
        m.box([x, 1.2, z], [x + 3.5, 4.4, z + 3.5], apple(c))
        m.box([x + 1.5, 4.4, z + 1.5], [x + 2, 7.4, z + 2], wood("oak"))           # sticks
    m.box([12, 1.2, 4], [13.5, 3.5, 11.5], solid("caramel", 2), faces=SIDES + ("up",))   # caramel bar
    return m


def cider_cask():
    m = Model("cider_cask")
    m.box([1.5, 0, 3], [3.5, 4, 13], wood("spruce"))                              # cradle legs
    m.box([12.5, 0, 3], [14.5, 4, 13], wood("spruce"))
    m.box([1, 3, 3.5], [15, 12, 12.5], cask())                                     # barrel on its side, crossed
    m.box([1.2, 4, 2.4], [14.8, 11, 13.6], cask())
    m.box([0.5, 6, 7], [1, 8, 9], solid("gold", 2))                               # tap on the end
    m.box([-1.5, 6.4, 7.5], [0.5, 7.6, 8.5], solid("gold", 2))
    m.box([-1.5, 4.8, 7.6], [-0.5, 6.4, 8.4], solid("gold", 3, bevel=False))      # spout
    m.box([-2.5, 0, 6.5], [0.5, 3, 9.5], solid("bone", 1), over={"up": solid("caramel", 2)})   # mug catching the drip
    m.box([9.5, 12, 6], [12.5, 15, 9], apple(False))                              # apple on top
    m.box([10.8, 15, 7.3], [11.2, 16, 7.7], bark("stem"))
    m.box([4, 12, 5], [7.5, 13, 9], solid("caramel", 1), over={"up": solid("bone", 1)})   # folded cloth
    return m


def candy_bucket():
    m = Model("candy_bucket")
    m.box([4, 0, 4], [12, 7, 12], painted_jack(False), res=2)                            # jack-o'-lantern bucket
    m.box([3.4, 0.5, 5], [12.6, 6.5, 11], pump_skin(), faces=("east", "west", "up", "down"))
    m.box([4.5, 7, 4.5], [11.5, 8.5, 11.5], candy())                              # heaped candy
    m.box([5.5, 8.5, 5.5], [10, 9.5, 10], candy())
    m.box([3.8, 6, 7.6], [4.6, 12, 8.4], iron())                                  # handle
    m.box([11.4, 6, 7.6], [12.2, 12, 8.4], iron())
    m.box([3.8, 11.4, 7.6], [12.2, 12.2, 8.4], iron())
    m.box([12.5, 0, 3], [15, 1, 4.5], wrapper("plum"), rot=("y", 22.5, [13.7, 0, 3.7]))   # spilled sweets
    m.box([1, 0, 11.5], [3.5, 1, 13], wrapper("brew"), rot=("y", -22.5, [2.2, 0, 12.2]))
    m.box([13, 0, 11], [14.5, 1, 12.5], wrapper("pump"))
    return m


def all_models():
    return [pumpkin_pile(), gourd_basket(), hay_bale_seat(), haystack(), pumpkin_cart(),
            caramel_apple_tray(), cider_cask(), candy_bucket()]
