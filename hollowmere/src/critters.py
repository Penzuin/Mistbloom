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
    """Soft fur. With face=True the north face gets a calm cat face: two round gold eyes with
    centred slit pupils and matching glints, a small pink nose and a tiny mouth - all mirrored."""
    def f(w, h, fc, key):
        rng = random.Random(key)
        img = _blank(w, h)
        img[:, :] = T("fur", 2)
        for _ in range(max(1, w * h // 9)):
            img[rng.randrange(h), rng.randrange(w)] = T("fur", rng.choice((1, 3)))
        if fc == "up":
            img[:, :] = T("fur", 1)
        if face and fc == "north" and w >= 12 and h >= 9:
            img[:, :] = T("fur", 2)                                   # clean face, no speckle
            ey, cx = 1, w // 2                                        # w even: mirror line between cx-1 and cx
            eye = [".111.", "11111", "11011", "12022", ".222."]        # solid gold eye, shaded lower half
            for side in (-1, 1):
                x0 = cx - 6 if side < 0 else cx + 1                     # cols 1-5 and 8-12 on a 14px face
                for yy, row in enumerate(eye):
                    r = row if side < 0 else row[::-1]
                    for xx, ch in enumerate(r):
                        if ch == "1":
                            img[ey + yy, x0 + xx] = T("gold", 1)
                        elif ch == "2":
                            img[ey + yy, x0 + xx] = T("gold", 3)
                        elif ch == "0":
                            img[ey + yy, x0 + xx] = T("coal", 6)        # small pupil, 1 x 2
                img[ey + 1, x0 + (1 if side < 0 else 3)] = T("cream", 0)  # glint, mirrored
            img[ey + 5, cx - 1:cx + 1] = T("blush", 2)                  # nose
            img[ey + 6, cx - 1:cx + 1] = T("coal", 5)                   # little mouth
            img[ey + 7, cx - 2] = img[ey + 7, cx + 1] = T("coal", 5)
            for yy in (ey + 5, ey + 7):                                 # whiskers
                img[yy, 0:2] = T("cream", 1); img[yy, w - 2:w] = T("cream", 1)
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
    """Owl head: pale facial disc around each eye, big gold eyes, pupils and glints mirrored
    exactly about the centre line, small orange beak between them."""
    def f(w, h, fc, key):
        img = _blank(w, h)
        img[:, :] = T("owl", 2)
        if fc == "up":
            img[:, :] = T("owl", 3)
        if fc == "north" and w >= 8 and h >= 6:
            mid = (w - 1) / 2
            off = w * 0.24
            ey = h * 0.45
            for y in range(h):
                for x in range(w):
                    d = min(math.hypot(x - (mid - off), y - ey), math.hypot(x - (mid + off), y - ey))
                    if d < 3.0:
                        img[y, x] = T("owl", 0)                          # facial discs
                    if d < 2.1:
                        img[y, x] = T("gold", 1)
                    if d < 1.3:
                        img[y, x] = T("coal", 6)
            L = int(mid - off) - 1                                        # mirrored glints
            img[int(ey) - 1, L] = img[int(ey) - 1, w - 1 - L] = T("snow", 0)
            c0 = int(mid)                                                 # beak on the centre line
            img[int(ey) + 1:int(ey) + 3, c0:c0 + (2 if w % 2 == 0 else 1)] = T("pump", 1)
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

WALL_LEGS = art([                 # 4 jointed legs a side, all meeting under the body (centre)
    "a..........a",
    ".a........a.",
    "..a......a..",
    "aa.aaaaaa.aa",
    "..aaaaaaaa..",
    "aa.aaaaaa.aa",
    "..a......a..",
    ".a........a.",
    "a..........a",
], {"a": ("plum", 3)})


SKULL_FACE = [            # 16 x 14 (left half shown, mirrored); s socket, g ember, h brow light, d cheek shade, n nose
    "........",
    "........",
    "...hhh..",
    "...sss..",
    "..sssss.",
    "..ssgss.",
    "..sssss.",
    "...sss..",
    "..ddddd.",
    ".......n",
    "......nn",
    "......n.",
    "........",
    "........",
]


def skull():
    """Cranium. Front: two big rounded eye sockets with a tiny ember deep inside, a lit brow above
    them, soft cheek shadow below, and an upside-down heart nose - drawn from a mirrored mask."""
    mask = [r + r[::-1] for r in SKULL_FACE]          # force perfect left/right symmetry
    def f(w, h, fc, key):
        rng = random.Random(key)
        img = _blank(w, h)
        img[:, :] = T("bone", 1)
        if fc != "north":
            for _ in range(w * h // 14):
                img[rng.randrange(h), rng.randrange(w)] = T("bone", 2)
        if fc == "up":
            img[:, :] = T("bone", 0)
        if fc == "north" and w >= 16 and h >= 14:
            ox, oy = (w - 16) // 2, (h - 14) // 2
            img[:, :] = T("bone", 1)
            img[-2:, :] = T("bone", 2)                                             # under the cheekbones
            for y, row in enumerate(mask):
                for x, ch in enumerate(row):
                    px = (oy + y, ox + x)
                    if ch == "s":
                        top = y > 0 and mask[y - 1][x] != "s"
                        img[px] = T("ebony", 5 if top else 6)                      # deep socket, rim catches a little light
                    elif ch == "g":
                        img[px] = T("pump", 1)                                     # ember glint
                    elif ch == "h":
                        img[px] = T("bone", 0)
                    elif ch == "d":
                        img[px] = T("bone", 2)
                    elif ch == "n":
                        img[px] = T("ebony", 5)
        return img
    return f


def jaw():
    """Lower jaw: a soft shadow line where it meets the skull, then three neat teeth with thin
    grey gaps (no black holes), mirrored so the middle tooth sits dead centre."""
    def f(w, h, fc, key):
        img = _blank(w, h)
        img[:, :] = T("bone", 2)
        if fc == "north" and w >= 12 and h >= 4:
            img[0, :] = T("bone", 3)                                              # where the jaw tucks under
            img[1:3, 1:w - 1] = T("bone", 0)                                      # tooth row
            for x in (1, 4, 7, 10):
                img[1:3, x] = T("bone", 3)                                        # gaps between teeth
            img[3, 1:w - 1] = T("bone", 3)                                        # shadow under the teeth
        if fc == "up":
            img[:, :] = T("bone", 1)
        return img
    return f


DRIP = art([                 # wax run down the middle of the forehead, stops between the eyes
    "aaaaaa",
    "aaaaaa",
    ".aaa.a",
    "..a...",
], {"a": ("candle", 1)})


def cushion():
    """Tufted cushion: dye-able cloth (non-neutral 'fur' ramp) with cream piping and gold buttons.
    Shaded like a soft pillow: the top domes up (light centre, darker toward the piping), each
    button sits in a dimple with a shadow below it, the sides roll from a lit shoulder into shade."""
    def f(w, h, fc, key):
        img = _blank(w, h)
        img[:, :] = T("fur", 1)
        if fc == "up":
            cx, cy = (w - 1) / 2, (h - 1) / 2
            for y in range(h):
                for x in range(w):
                    d = max(abs(x - cx) / max(cx, 1), abs(y - cy) / max(cy, 1))
                    img[y, x] = T("fur", 0 if d < 0.35 else 1 if d < 0.7 else 2)
            if w >= 6:
                for (x, y) in ((w // 3, h // 3), (w - 1 - w // 3, h // 3), (w // 3, h - 1 - h // 3),
                               (w - 1 - w // 3, h - 1 - h // 3), (w // 2, h // 2)):
                    img[y, x] = T("gold", 1)                                    # button
                    if y + 1 < h:
                        img[y + 1, x] = T("fur", 3)                              # its little dimple shadow
            img[0, :] = img[:, 0] = T("cream", 0)                                  # piping, lit edges
            img[-1, :] = img[:, -1] = T("cream", 2)
        elif fc in SIDES:
            tones = [1, 2, 3, 4] if h >= 5 else [2, 3]
            for y in range(1, h - 1):
                t = tones[min(len(tones) - 1, (y - 1) * len(tones) // max(1, h - 2))]
                img[y, :] = T("fur", t)
                img[y, 2::4] = T("fur", t + 1)                                     # gathered folds
            img[0, :] = T("cream", 1)
            img[-1, :] = T("cream", 3)
        elif fc == "down":
            img[:, :] = T("fur", 4)
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
        if fc == "up" and max(w, h) >= 2.5 * min(w, h):                   # top of a long branch: lit bark
            along_x = w >= h
            for y in range(h):
                for x in range(w):
                    a, b = (x, y) if along_x else (y, x)
                    n = min(w, h)
                    tone = 1 if b < n / 2 else 2                          # lit half / turning half
                    if (a + 3 * b) % 7 == 0:
                        tone += 1                                         # grain streaks
                    if b in (0, n - 1) and n > 2:
                        tone += 1                                         # edges roll away
                    img[y, x] = T("ebony", tone)
            return img
        if fc == "up":                                                    # sawn end: growth rings, a crack,
            cx, cy = (w - 1) / 2, (h - 1) / 2                             # dark bark round the rim
            for y in range(h):
                for x in range(w):
                    r = max(abs(x - cx), abs(y - cy))
                    edge = x in (0, w - 1) or y in (0, h - 1)
                    img[y, x] = T("ebony", 4 if edge else (2 if int(r) % 2 == 0 else 3))
            if w >= 3 and h >= 3:
                img[int(cy), int(cx)] = T("ebony", 5)                     # heart
                for k in range(1, max(2, min(w, h) // 2)):
                    if int(cx) + k < w - 1:
                        img[int(cy) - (k % 2 == 0 and int(cy) > 0), int(cx) + k] = T("ebony", 5)   # drying crack
        return img
    return f


def chain():
    return art([".a.", "a.a", ".a.", ".b.", "b.b", ".b."], {"a": ("iron", 1), "b": ("iron", 3)})


# ------------------------------------------------------------------ pieces
def black_cat():
    m = Model("black_cat", dye=(58, 52, 72))
    m.box([4.5, 0, 7], [11.5, 6, 13], tinted(fur()))                             # haunches
    m.box([5.5, 0, 5], [10.5, 8.5, 9], tinted(fur()))                             # chest, sitting up
    m.dyebox([4.5, 8, 4], [11.5, 13, 9], fur(face=True), res=2)                          # head (eyes stay gold)
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


def plumage(sheen=True):
    """Crow feathers: near-black with a cool violet sheen on the lit rows and overlapping scale rows."""
    def f(w, h, fc, key):
        img = _blank(w, h)
        img[:, :] = T("ebony", 5)
        for y in range(h):
            for x in range(w):
                if (x + (y // 2) * 2) % 4 == 0 and y % 2 == 1:
                    img[y, x] = T("ebony", 6)                                      # feather edges
        if fc in SIDES and h >= 3 and sheen:
            img[0, :] = T("ebony", 4)                                              # lit top edge
            img[0, ::5] = T("plum", 5)                                             # a hint of violet sheen
        if fc == "up":
            img[:, :] = T("ebony", 4)
        if fc == "down":
            img[:, :] = T("ebony", 6)
        return img
    return f


def crow_face():
    """Crow head (faces east): bright eye with a glint on both sides, near the beak."""
    base = plumage()
    def f(w, h, fc, key):
        img = base(w, h, fc, key)
        if fc in ("north", "south") and w >= 6 and h >= 6:
            ex = w - 3 if fc == "south" else 1                                     # toward the beak on both sides
            ey = h // 2 - 1
            img[ey:ey + 2, ex:ex + 2] = T("hay", 0)
            img[ey, ex + (1 if fc == "south" else 0)] = T("cream", 0)               # glint
            img[ey + 1, ex + (0 if fc == "south" else 1)] = T("ebony", 6)           # pupil
        return img
    return f


def crow_post():
    """A single crow perched upright on top of a stick, side-on (faces east), pumpkin at the foot."""
    m = Model("crow_post", floor=0)
    m.box([7, 0, 7], [9, 16, 9], bark("spruce"))                                  # the stick
    m.box([6.4, 16, 6.4], [9.6, 16.8, 9.6], bark("spruce"))                       # little top block it grips
    m.box([7.3, 16.8, 6.9], [8.6, 17.6, 9.1], solid("iron", 3, bevel=False))      # feet
    m.box([5.2, 17.6, 6], [10.2, 21.8, 10], plumage())                            # body
    m.box([9.6, 18.2, 6.5], [11.2, 21.4, 9.5], plumage())                         # full breast
    m.box([4.8, 18.4, 5.7], [10, 21.6, 6.0], plumage(), rot=("z", 22.5, [10, 21.6, 8]))     # folded wings, tips down and back
    m.box([4.8, 18.4, 10.0], [10, 21.6, 10.3], plumage(), rot=("z", 22.5, [10, 21.6, 8]))
    m.box([1.2, 17.6, 7], [5.6, 18.6, 9], plumage(sheen=False), rot=("z", 22.5, [5.6, 18.6, 8]))   # tail, sloping down
    m.box([8.4, 21.2, 6.25], [12.4, 25.2, 9.75], crow_face(), res=2)              # head
    m.box([12.4, 22.6, 7.3], [14.8, 23.6, 8.7], solid("iron", 4))                  # beak, upper
    m.box([12.4, 22.0, 7.5], [14.0, 22.6, 8.5], solid("iron", 5, bevel=False))    # beak, lower
    m.box([2.5, 0, 2.5], [7, 3.5, 7], pump_skin())                                # pumpkin at the foot
    m.box([4.4, 3.5, 4.4], [5.1, 4.6, 5.1], bark("stem"))
    m.card([9.1, 2.5, 9.1], [9.1, 10.5, 12.5], VINE)                              # ivy up the back
    return m


def cobweb_corner():
    m = Model("cobweb_corner")
    m.card([0, 0, 15.9], [16, 16, 15.9], web("tr"), res=2)                      # big web on the wall
    m.card([0.1, 0, 0], [0.1, 16, 16], web("tl"), res=2)                        # and wrapping the side
    m.card([10.75, 6, 15.4], [11.25, 13, 15.4], thread())                         # tiny spider on its thread
    m.card([8, 1.75, 14.95], [14, 6.25, 14.95], WALL_LEGS, res=2)                 # legs flat on the web, under the body
    m.box([9.8, 3.5, 13.6], [12.2, 5.5, 14.6], spider_body())
    m.box([10.3, 2.4, 13.1], [11.7, 3.6, 13.7], spider_head())
    return m


def spider_leg(tip_at_start=True):
    """Shaded leg: lit top, dark underside, a sheen line along the upper edge of the sides,
    a lighter knee band in the middle and a violet tip at the outer end."""
    def f(w, h, fc, key):
        img = _blank(w, h)
        along_x = w >= h
        L = w if along_x else h
        for y in range(h):
            for x in range(w):
                t = x if along_x else y
                tone = 5
                if fc == "up":
                    tone = 3
                elif fc == "down":
                    tone = 6
                elif fc in SIDES:
                    across = y if along_x else x
                    n = h if along_x else w
                    tone = 4 if across == 0 else (6 if across == n - 1 else 5)
                if L >= 6 and abs(t - L // 2) == 0:
                    tone -= 1                                          # knee
                img[y, x] = T("ebony", tone)
                start = tip_at_start != (fc == "north")                  # north faces run east-to-west
                tip = t < 2 if start else t >= L - 2
                if tip and L >= 6:
                    img[y, x] = T("plum", 3 if fc == "up" else 4)
        return img
    return f


def hanging_spider():
    """A round spider dangling on its thread: plump abdomen, head with eyes, eight legs fanned out
    and angled down from the sides of the head (four each side, mirrored), two little fangs."""
    m = Model("hanging_spider")
    m.card([7.75, 9, 9.5], [8.25, 16, 9.5], thread())                              # silk thread from the ceiling
    m.box([5.5, 5.5, 7.6], [10.5, 9.5, 12.4], spider_body(), res=2)               # plump abdomen
    m.box([6.3, 5.0, 4.4], [9.7, 7.8, 7.8], spider_head(), res=2)                 # head with eyes
    for z in (5.0, 6.2, 7.4, 8.6):                                                 # 4 legs a side, rooted inside head/body
        a = 45 if z in (5.0, 8.6) else 22.5
        m.box([1.4, 5.9, z - 0.3], [7.0, 6.5, z + 0.3], spider_leg(True), res=2,
              rot=("z", a, [6.6, 6.2, z]))                                         # left legs, tips down
        m.box([9.0, 5.9, z - 0.3], [14.6, 6.5, z + 0.3], spider_leg(False), res=2,
              rot=("z", -a, [9.4, 6.2, z]))                                        # right legs, mirrored
    m.box([7.1, 4.3, 4.1], [7.7, 5.0, 4.6], solid("bone", 1))                      # tiny fangs
    m.box([8.3, 4.3, 4.1], [8.9, 5.0, 4.6], solid("bone", 1))
    return m


def skull_candle():
    m = Model("skull_candle")
    m.box([3, 0, 3], [13, 0.8, 13], solid("iron", 2))                            # iron dish
    m.box([4, 3, 4.5], [12, 10, 12], skull(), res=2)                             # cranium
    m.box([5, 0.8, 4.2], [11, 3.4, 10], jaw(), res=2)                                   # jaw
    m.box([3.6, 4.8, 5.5], [4.2, 7.5, 10], solid("bone", 2))                     # cheek bones
    m.box([11.8, 4.8, 5.5], [12.4, 7.5, 10], solid("bone", 2))
    m.box([6.5, 10, 7], [9.5, 14, 10], wax())                                    # candle on the crown
    m.card([6.5, 8.6, 4.45], [9.5, 10.4, 4.45], DRIP, res=2)                       # wax dripping down the brow
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
    m.dyebox([2.7, 8.5, 2.7], [13.3, 11.5, 13.3], cushion(), res=2)                      # plump tufted cushion
    m.box([3.4, 11.5, 3.4], [12.6, 12.3, 12.6], tinted(cushion()), faces=("up", "north", "south", "east", "west"))
    m.box([2.1, 6.2, 2.1], [3.1, 8.6, 3.1], tassel())                             # corner tassels
    m.box([12.9, 6.2, 2.1], [13.9, 8.6, 3.1], tassel())
    m.box([4, 4, 6], [7, 6.5, 9], pump_skin())                               # tiny pumpkin on the shelf
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
    m.box([1, 2, 1], [4.5, 5, 4.5], pump_skin())                             # pumpkin among the roots
    return m


def all_models():
    return [black_cat(), owl_perch(), crow_post(), cobweb_corner(), hanging_spider(), skull_candle(),
            cushion_stool(), dead_tree()]
