"""Hollowmere critters & decor batch. Front faces NORTH (-z). Max 14 elements per model."""
import math, random
import engine
from engine import Model, wood, solid, T, _blank, fr, animated, SIDES, art, tinted
from hero3 import bark, iron, candle_flame, wax, crow_body, crow_head, painted_jack, pump_skin
from spooky import stone, VINE, BAT
from harvest import pumpkin

engine.RAMPS.update({k: engine._ramp7(v) for k, v in {
    "owl":  ["#f2d3a2", "#c99a64", "#93653f", "#5e3f2a"],
    "fur":  ["#d6d3de", "#a9a5b6", "#7b7790", "#55516a"],   # greyscale-ish; tinted in game
}.items()})


# ------------------------------------------------------------------ painters
def fur(face=False):
    """Soft fur; the north face of the head gets gold eyes, a blush nose and a little 'w' mouth."""
    def f(w, h, fc, key):
        rng = random.Random(key)
        img = _blank(w, h)
        img[:, :] = T("fur", 2)
        for _ in range(max(1, w * h // 9)):
            img[rng.randrange(h), rng.randrange(w)] = T("fur", rng.choice((1, 3)))
        if fc == "up":
            img[:, :] = T("fur", 1)
        if face and fc == "north" and w >= 6 and h >= 5:
            ey = h // 3
            for ex in (w // 4 - 1 + 1, w - w // 4 - 2):
                img[ey:ey + 2, ex:ex + 2] = T("gold", 1)
                img[ey:ey + 2, ex + 1 - (ex > w // 2)] = T("coal", 6)          # slit pupils
            cx = w // 2
            img[ey + 2, cx - 1:cx + 1] = T("blush", 2)                           # nose
            img[ey + 3, cx - 2] = img[ey + 3, cx + 1] = T("coal", 5)              # 'w' mouth
            img[ey + 4 if ey + 4 < h else ey + 3, cx - 1:cx + 1] = T("coal", 5)
            img[ey + 2, 0] = img[ey + 2, w - 1] = T("cream", 0)                   # whisker tips
        return img
    return f


def ear(inner=True):
    def f(w, h, fc, key):
        img = _blank(w, h)
        img[:, :] = T("fur", 3)
        if inner and fc == "north" and w >= 2:
            img[1:, w // 2 - (w > 2):w // 2 + 1] = T("blush", 1)
        return img
    return f


def feathers():
    def f(w, h, fc, key):
        img = _blank(w, h)
        img[:, :] = T("owl", 2)
        for y in range(h):
            for x in range(w):
                if (y % 3 == 1) and ((x + y // 3) % 3 == 0):
                    img[y, x] = T("owl", 4)                                       # little chevrons
        if fc == "north" and w >= 6:
            cx = w / 2
            for y in range(h):
                for x in range(w):
                    if abs(x + .5 - cx) < w * 0.32 and y > h * 0.15:
                        img[y, x] = T("owl", 0 if (x + y) % 3 else 1)              # pale breast
        if fc == "up":
            img[:, :] = T("owl", 3)
        return img
    return f


def owl_face():
    def f(w, h, fc, key):
        img = _blank(w, h)
        img[:, :] = T("owl", 2)
        if fc == "up":
            img[:, :] = T("owl", 3)
        if fc == "north" and w >= 8 and h >= 6:
            ey = h // 2 - 1
            for cx in (w // 4 + 0.5, w - w // 4 - 0.5):
                for y in range(h):
                    for x in range(w):
                        d = math.hypot(x + .5 - cx - .5, y + .5 - ey - 1)
                        if d < 2.6:
                            img[y, x] = T("owl", 0)                              # facial disc
                        if d < 1.7:
                            img[y, x] = T("gold", 1)
                        if d < 0.8:
                            img[y, x] = T("coal", 6)
                ix, iy = int(cx) - 1, ey
                if 0 <= ix < w and 0 <= iy < h:
                    img[iy, ix] = T("snow", 0)                                    # glint
            img[ey + 2:ey + 4, w // 2 - 1:w // 2 + 1] = T("pump", 1)              # beak
        return img
    return f


def web(corner="tl"):
    """Corner cobweb: 5 spokes from the anchor corner and 3 sagging threads between them."""
    def f(w, h, fc, key):
        img = _blank(w, h)
        flip = (corner == "tr") ^ (fc in ("south", "west"))
        ox = (w - 1) if flip else 0
        R = max(w, h) * 0.95
        angs = [4, 25, 46, 67, 86]
        for s_ in angs:                                                           # spokes
            for t in range(int(R * 1.4)):
                x = ox + (t * math.cos(math.radians(s_))) * (-1 if flip else 1)
                y = t * math.sin(math.radians(s_))
                if 0 <= round(x) < w and 0 <= round(y) < h and math.hypot(x - ox, y) <= R:
                    img[round(y), round(x)] = T("snow", 1, 225)
        for rr in (R * .38, R * .72):                                   # sagging rings
            for k in range(len(angs) - 1):
                a0, a1 = math.radians(angs[k]), math.radians(angs[k + 1])
                for i in range(25):
                    u = i / 24
                    a = a0 + (a1 - a0) * u
                    r = rr * (1 - 0.12 * math.sin(math.pi * u))
                    x = ox + r * math.cos(a) * (-1 if flip else 1)
                    y = r * math.sin(a)
                    if 0 <= round(x) < w and 0 <= round(y) < h:
                        img[round(y), round(x)] = T("snow", 2, 190)
        return img
    return f


def thread():
    def f(w, h, fc, key):
        img = _blank(w, h)
        img[:, w // 2] = T("snow", 2, 200)
        return img
    return f


def spider_body():
    def f(w, h, fc, key):
        img = _blank(w, h)
        img[:, :] = T("ebony", 5)
        if fc == "up" and w >= 4:
            img[h // 3:h // 3 + 2, w // 2 - 1:w // 2 + 1] = T("pump", 1)          # little orange mark
            img[0, :] = T("ebony", 4)
        if fc in SIDES and h > 2:
            img[-1, :] = T("ebony", 6)
        return img
    return f


def spider_head():
    def f(w, h, fc, key):
        img = _blank(w, h)
        img[:, :] = T("ebony", 5)
        if fc == "north" and w >= 4 and h >= 3:
            img[h // 2 - 1, w // 4] = img[h // 2 - 1, w - 1 - w // 4] = T("snow", 0)
            img[h // 2, w // 4] = img[h // 2, w - 1 - w // 4] = T("plum", 1)
        return img
    return f


LEGS = art([
    "..aa...aa..",
    ".a..a.a..a.",
    "a...aaa...a",
    "..aa...aa..",
    ".a..a.a..a.",
    "a...aaa...a",
], {"a": ("plum", 3)})


def skull():
    def f(w, h, fc, key):
        rng = random.Random(key)
        img = _blank(w, h)
        img[:, :] = T("bone", 1)
        for _ in range(w * h // 14):
            img[rng.randrange(h), rng.randrange(w)] = T("bone", 2)
        if fc == "up":
            img[:, :] = T("bone", 0)
        if fc == "north" and w >= 8 and h >= 6:
            ey = h // 2 - 1
            for ex in (w // 4 - 1, w - w // 4 - 2):
                img[ey:ey + 3, ex:ex + 3] = T("ebony", 5)                         # round sockets
                img[ey, ex] = img[ey, ex + 2] = T("bone", 2)
                img[ey + 1, ex + 1] = T("pump", 1)                                # tiny glow inside
            img[ey + 3:ey + 5, w // 2 - 1:w // 2 + 1] = T("ebony", 4)             # nose
            img[ey + 3, w // 2 - 1] = T("bone", 2)
        return img
    return f


def jaw():
    def f(w, h, fc, key):
        img = _blank(w, h)
        img[:, :] = T("bone", 2)
        if fc == "north" and w >= 5:
            img[0, :] = T("bone", 0)
            img[0, 1:w - 1:2] = T("ebony", 4)                                     # teeth gaps
        return img
    return f


DRIP = art([
    "aaaaaaa",
    "aa.aaa.",
    "a..a.a.",
    "a....a.",
    ".....a.",
], {"a": ("candle", 1)})


def cushion():
    """Tufted cushion: dye-able cloth (non-neutral 'fur' ramp) with cream piping and gold buttons."""
    def f(w, h, fc, key):
        img = _blank(w, h)
        img[:, :] = T("fur", 1)
        if fc == "up" and w >= 6:
            for (x, y) in ((w // 3, h // 3), (w - 1 - w // 3, h // 3), (w // 3, h - 1 - h // 3),
                           (w - 1 - w // 3, h - 1 - h // 3), (w // 2, h // 2)):
                img[y, x] = T("gold", 1)
                if x + 1 < w: img[y, x + 1] = T("fur", 3)
            img[0, :] = img[-1, :] = img[:, 0] = img[:, -1] = T("cream", 1)       # piping
        if fc in SIDES:
            img[0, :] = T("cream", 1)
            img[-1, :] = T("cream", 2)
            img[1:-1, :] = T("fur", 2)
        return img
    return f


def tassel():
    def f(w, h, fc, key):
        img = _blank(w, h)
        img[:, :] = T("gold", 2)
        img[0, :] = T("gold", 1)
        return img
    return f


def gnarl():
    """Dead-tree bark: dark wood with knots and a few moss flecks."""
    def f(w, h, fc, key):
        rng = random.Random(key)
        img = _blank(w, h)
        vertical = h >= w
        for y in range(h):
            for x in range(w):
                a = x if vertical else y
                img[y, x] = T("ebony", 3 + (1 if (a + (y if vertical else x) // 5) % 3 == 0 else 0))
        for _ in range(max(1, w * h // 40)):
            x, y = rng.randrange(w), rng.randrange(h)
            img[y, x] = T("ebony", 5)
        if fc in SIDES:
            for _ in range(max(1, w * h // 60)):
                img[rng.randrange(h), rng.randrange(w)] = T("moss", 2)
        if fc == "up":
            img[:, :] = T("ebony", 2)
        return img
    return f


def chain():
    return art([".a.", "a.a", ".a.", ".b.", "b.b", ".b."], {"a": ("iron", 1), "b": ("iron", 3)})


# ------------------------------------------------------------------ pieces
def black_cat():
    m = Model("black_cat", dye=(58, 52, 72))
    m.box([4.5, 0, 7], [11.5, 6, 13], tinted(fur()))                             # haunches
    m.box([5.5, 0, 5], [10.5, 8.5, 9], tinted(fur()))                             # chest, sitting up
    m.dyebox([4.5, 8, 4], [11.5, 13, 9], fur(face=True))                          # head (eyes stay gold)
    m.box([4.8, 12.4, 5.5], [7, 15, 7], tinted(ear()), rot=("z", 22.5, [5.9, 13, 6.25]))     # ears
    m.box([9, 12.4, 5.5], [11.2, 15, 7], tinted(ear()), rot=("z", -22.5, [10.1, 13, 6.25]))
    m.box([5.6, 0, 3.4], [7.6, 1.6, 5.2], tinted(fur()))                          # front paws
    m.box([8.4, 0, 3.4], [10.4, 1.6, 5.2], tinted(fur()))
    m.box([11, 0, 9.5], [14.5, 1.6, 12], tinted(fur()))                           # tail along the floor...
    m.box([13, 1.4, 7.5], [14.6, 6.5, 9.5], tinted(fur()), rot=("x", 22.5, [13.8, 1.4, 8.5]))  # ...curling up
    m.box([5.4, 7.6, 4.6], [10.6, 8.6, 9], solid("pump", 2, bevel=False))         # collar
    m.box([7.2, 6.4, 4.1], [8.8, 7.8, 4.6], solid("gold", 1))                     # bell
    return m


def owl_perch():
    m = Model("owl_perch")
    m.box([4, 0, 4], [12, 1.5, 12], gnarl())                                      # stump base
    m.box([7, 1.5, 7], [9, 9, 9], gnarl())                                        # post
    m.box([2, 9, 7.2], [14, 10.5, 8.8], gnarl())                                  # crossbar perch
    m.box([5, 10.5, 5.5], [11, 16, 10], feathers())                               # owl body
    m.box([4.6, 11, 6], [5.4, 15, 9.5], solid("owl", 3))                          # folded wings
    m.box([10.6, 11, 6], [11.4, 15, 9.5], solid("owl", 3))
    m.box([4.5, 16, 5], [11.5, 20.5, 10], owl_face(), res=2)                      # big round-eyed head
    m.box([4.5, 20.5, 6.5], [6, 22, 8], solid("owl", 3), rot=("z", 22.5, [5.25, 20.5, 7.25]))   # ear tufts
    m.box([10, 20.5, 6.5], [11.5, 22, 8], solid("owl", 3), rot=("z", -22.5, [10.75, 20.5, 7.25]))
    m.box([6, 10.5, 4.6], [7, 11, 5.6], solid("pump", 2, bevel=False))            # toes
    m.box([9, 10.5, 4.6], [10, 11, 5.6], solid("pump", 2, bevel=False))
    m.box([12, 10.5, 7.5], [13.5, 12, 8.5], solid("moss", 2))                     # little leaf tuft on the bar
    m.card([2.5, 1.5, 3.9], [7, 6, 3.9], VINE)
    return m


def crow_post():
    m = Model("crow_post", floor=0)
    m.box([6.5, 0, 6.5], [9.5, 18, 9.5], bark("spruce"))                          # post
    m.box([0, 13, 7], [16, 15, 9], bark("spruce"))                                # cross rail
    m.box([6, 18, 6], [10, 18.6, 10], solid("ebony", 3))                          # cap
    m.box([0.5, 15, 6.75], [5, 18, 9.25], crow_body(), rot=("z", 22.5, [2.75, 15, 8]))     # crow one, facing west
    m.box([0, 17.4, 7], [2.8, 20.2, 9], crow_head())
    m.box([11, 15, 6.75], [15.5, 18, 9.25], crow_body(), rot=("z", -22.5, [13.25, 15, 8]))  # crow two, facing east
    m.box([13.6, 17.4, 7], [16.4, 20.2, 9], crow_head())
    m.box([3, 0, 3], [7.5, 3.5, 7.5], solid("pump", 2))                           # pumpkin at the foot
    m.box([4.9, 3.5, 4.9], [5.6, 4.6, 5.6], bark("stem"))
    m.card([9.6, 3, 9.6], [9.6, 11, 13.6], VINE)                                  # ivy up the back
    m.card([7, 9, 6.4], [12, 12.5, 6.4], art(["aaaaaaaaaa", "a.b.b.b..a", "a.bb.b.b.a", "aaaaaaaaaa"],
                                           {"a": ("ebony", 2), "b": ("bone", 1)}), res=2)   # tiny "SHOO" tag
    return m


def cobweb_corner():
    m = Model("cobweb_corner")
    m.card([0, 0, 15.95], [16, 16, 15.95], web("tr"), res=2)                      # big web on the wall
    m.card([0.05, 0, 0], [0.05, 16, 16], web("tl"), res=2)                        # and wrapping the side
    m.card([10.75, 5.5, 15.9], [11.25, 13, 15.9], thread())                         # tiny spider on its thread
    m.box([9.8, 4, 14.4], [12.2, 6, 15.6], spider_body())
    m.box([10.3, 3.2, 14.2], [11.7, 4.2, 15.2], spider_head())
    m.card([8.5, 3, 14.9], [13.5, 6.5, 14.9], LEGS)
    return m


def hanging_spider():
    m = Model("hanging_spider")
    m.card([7.75, 8, 8], [8.25, 16, 8], thread())                                   # silk thread from the ceiling
    m.box([6, 4.5, 6], [10, 8, 10], spider_body())                                # plump abdomen
    m.box([6.6, 3, 4.8], [9.4, 5.2, 7], spider_head())                            # head with shiny eyes
    m.card([2.5, 2.5, 8], [13.5, 8.5, 8], LEGS)                                  # legs, crossed
    m.card([8, 2.5, 2.5], [8, 8.5, 13.5], LEGS)
    m.box([7.2, 2.4, 4.6], [7.8, 3, 5], solid("bone", 1))                         # tiny fangs
    m.box([8.2, 2.4, 4.6], [8.8, 3, 5], solid("bone", 1))
    return m


def skull_candle():
    m = Model("skull_candle")
    m.box([3, 0, 3], [13, 0.8, 13], solid("iron", 2))                            # iron dish
    m.box([4, 3, 4.5], [12, 10, 12], skull(), res=2)                             # cranium
    m.box([5, 0.8, 4.2], [11, 3.4, 10], jaw())                                   # jaw
    m.box([3.6, 4.8, 5.5], [4.2, 7.5, 10], solid("bone", 2))                     # cheek bones
    m.box([11.8, 4.8, 5.5], [12.4, 7.5, 10], solid("bone", 2))
    m.box([6.5, 10, 7], [9.5, 14, 10], wax())                                    # candle on the crown
    m.card([5.5, 7.6, 4.45], [9.5, 10.4, 4.45], DRIP)                       # wax dripping down the brow
    m.box([5.8, 10, 6.3], [10.2, 10.6, 10.7], solid("candle", 1))                # wax pool
    m.card([6.5, 14, 8.5], [9.5, 17, 8.5], candle_flame(), emit=15, rot=("y", 45, [8, 14, 8.5]))
    m.card([6.5, 14, 8.5], [9.5, 17, 8.5], candle_flame(), emit=15, rot=("y", -45, [8, 14, 8.5]))
    return m


def cushion_stool():
    m = Model("cushion_stool", dye=(150, 72, 170))
    for (x, z) in ((3.5, 3.5), (10.5, 3.5), (3.5, 10.5), (10.5, 10.5)):
        m.box([x, 0, z], [x + 2, 7, z + 2], wood("ebony", plank=2))               # legs
    m.box([3, 3, 3], [13, 4, 13], bark("ebony"), faces=("north", "south", "east", "west", "up"))   # stretcher shelf
    m.box([2.5, 7, 2.5], [13.5, 8.5, 13.5], wood("ebony", plank=2))               # seat
    m.dyebox([2.7, 8.5, 2.7], [13.3, 11.5, 13.3], cushion())                      # plump tufted cushion
    m.box([3.4, 11.5, 3.4], [12.6, 12.3, 12.6], tinted(cushion()), faces=("up", "north", "south", "east", "west"))
    m.box([2.1, 6.2, 2.1], [3.1, 8.6, 3.1], tassel())                             # corner tassels
    m.box([12.9, 6.2, 2.1], [13.9, 8.6, 3.1], tassel())
    m.box([4, 4, 6], [7, 6.5, 9], solid("pump", 2))                               # tiny pumpkin on the shelf
    return m


def dead_tree():
    m = Model("dead_tree")
    m.box([3, 0, 3], [13, 2, 13], gnarl())                                        # root flare
    m.box([1, 0, 6], [15, 1, 10], gnarl())
    m.box([5, 2, 5], [11, 16, 11], gnarl())                                       # lower trunk
    m.box([6, 16, 6], [10, 26, 10], gnarl(), rot=("z", -22.5, [8, 16, 8]))        # upper trunk leans
    m.box([9, 12, 7], [18, 14, 9], gnarl(), rot=("z", 22.5, [9, 13, 8]))          # east branch
    m.box([-3, 17, 7], [7, 19, 9], gnarl(), rot=("z", -22.5, [7, 18, 8]))         # west branch
    m.box([10, 25, 7], [16, 26.5, 8.5], gnarl(), rot=("z", 45, [10, 25, 8]))      # crown twig
    m.card([16.5, 8.5, 8], [17.5, 13.5, 8], chain(), res=3)                       # hanging lanterns: chains...
    m.box([15, 4.5, 6.5], [19, 8.5, 10.5], painted_jack(True), emit=15, res=4)           # ...and little lit jacks
    m.card([-2.5, 10.5, 8], [-1.5, 17, 8], chain(), res=3)
    m.box([-4, 7, 6.5], [0, 11, 10.5], painted_jack(True), emit=15, res=4)
    m.box([1, 2, 1], [4.5, 5, 4.5], solid("pump", 2))                             # pumpkin among the roots
    return m


def all_models():
    return [black_cat(), owl_perch(), crow_post(), cobweb_corner(), hanging_spider(), skull_candle(),
            cushion_stool(), dead_tree()]
