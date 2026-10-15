"""Hollowmere market extras. Front faces NORTH (-z). Max 14 elements per model."""
import math, random
import engine
from engine import Model, wood, solid, T, _blank, SIDES, art, tinted, stripes, scallop, board, FONT5
from hero3 import bark, iron, painted_jack, panels, flask, pump_skin, shop_sign
from hero2 import moon_board
from spooky import VINE
from hero3 import BAT
from critters import gnarl, chain

FONT5.update({
    "H": ["1001", "1001", "1111", "1001", "1001"],
    "O": ["0110", "1001", "1001", "1001", "0110"],
    "L": ["100", "100", "100", "100", "111"],
    "W": ["10001", "10001", "10101", "11011", "10001"],
    "C": ["0111", "1000", "1000", "1000", "0111"],
    "N": ["1001", "1101", "1011", "1001", "1001"],
    "D": ["1110", "1001", "1001", "1001", "1110"],
    "S": ["0111", "1000", "0110", "0001", "1110"],
    "Y": ["10001", "01010", "00100", "00100", "00100"],
    "P": ["1110", "1001", "1110", "1000", "1000"],
    "I": ["111", "010", "010", "010", "111"],
    "G": ["0111", "1000", "1011", "1001", "0111"],
})


# ------------------------------------------------------------------ painters
def autumn():
    """Dense autumn foliage: pumpkin, rust, caramel and a little moss, in leaf clusters."""
    cols = [("pump", 1), ("pump", 2), ("rust", 2), ("caramel", 1), ("rust", 3), ("moss", 2)]
    def f(w, h, fc, key):
        rng = random.Random(key)
        img = _blank(w, h)
        img[:, :] = T("pump", 3)
        for _ in range(max(2, w * h // 5)):
            x, y = rng.randrange(w), rng.randrange(h)
            c = rng.choice(cols)
            img[y, x] = T(*c)
            if x + 1 < w: img[y, x + 1] = T(c[0], c[1] + 1)
        return img
    return f


def bunting():
    """Sagging string with dyeable pennants (non-neutral ramp) and little bat flags (coal, stays dark)."""
    def f(w, h, fc, key):
        img = _blank(w, h)
        curve = lambda x: int(round(1 + 2.2 * math.sin(math.pi * x / (w - 1))))
        nflags = (w - 3) // 8
        first = (w - (nflags * 8 - 1)) // 2                                       # equal margin at both ends
        spans = [(x0, x0 + 6) for x0 in range(first, first + nflags * 8, 8)]
        def sag(x):                                                               # flat across each flag's top
            for a, b in spans:
                if a <= x <= b:
                    return curve(a + 3)
            return curve(x)
        n = 0
        for x0, _ in spans:
            top = sag(x0 + 3)
            bat = n % 2 == 1
            for y in range(top + 1, min(h, top + 9)):
                half = (top + 9 - y) * 3.4 / 8
                for x in range(x0, x0 + 7):
                    if abs(x - (x0 + 3)) <= half:
                        img[y, x] = T("coal", 2 if y < top + 7 else 3) if bat else T("fur", 1 if y < top + 7 else 2)
            if bat and top + 3 < h:                                               # tiny bat cut-out
                for (dx, dy) in ((1, 2), (2, 3), (3, 3), (4, 3), (5, 2), (3, 4)):
                    img[top + dy, x0 + dx] = T("gold", 1)
            n += 1
        for x in range(w):                                                        # the string, one unbroken line:
            a, b = sorted((sag(x), sag(max(0, x - 1))))                           # where it steps down a row, both
            img[a:b + 1, x] = T("cream", 3)                                       # rows are filled so the pieces join
        return img
    return f


def big_sign(text):
    """Name board: lettering on the front, plain planks on the back, little pumpkin dots if there is room."""
    b = board(text, ramp="ebony", ink="cream", trim="gold")
    plain = board(None, ramp="ebony", trim="gold")
    tw = sum(len(FONT5[c][0]) + 1 for c in text) - 1
    def f(w, h, fc, key):
        if fc == "south":
            return plain(w, h, fc, key)
        img = b(w, h, fc, key)
        if fc == "north" and w - tw >= 14:
            for (x, y) in ((3, h // 2), (w - 4, h // 2)):
                img[y - 1:y + 1, x - 1:x + 1] = T("pump", 1)
        return img
    return f


ARROW_R = ["11111110", "11111111", "11111110"]


# ------------------------------------------------------------------ pieces
def hollow_arch():
    m = Model("hollow_arch", floor=-16)
    m.box([-15, -16, 5], [-10, 22, 11], gnarl())                                  # twisted posts
    m.box([26, -16, 5], [31, 22, 11], gnarl())
    m.box([-16, -16, 4], [-9, -12, 12], gnarl())                                  # root feet
    m.box([25, -16, 4], [32, -12, 12], gnarl())
    m.box([-16, 22, 4.5], [32, 25, 11.5], gnarl())                                # crossbeam
    m.box([-11, 15, 7], [-3, 17, 9], gnarl(), rot=("z", -45, [-10, 16, 8]))       # knee braces
    m.box([19, 15, 7], [27, 17, 9], gnarl(), rot=("z", 45, [26, 16, 8]))
    m.box([-6, 13, 7], [22, 20, 8], big_sign("HALLOWEEN"), res=2)                # hanging name board
    m.card([-4, 20, 7.5], [-2, 22, 7.5], chain(), res=3)                          # board chains
    m.card([18, 20, 7.5], [20, 22, 7.5], chain(), res=3)
    m.box([-16, 25, 4], [-9, 31, 11], painted_jack(True), emit=15, res=2)                # jack lanterns on the posts
    m.box([25, 25, 4], [32, 31, 11], painted_jack(True), emit=15, res=2)
    m.card([1, 25, 8], [15, 31, 8], BAT)                                          # bat on the beam
    m.card([-15.1, -12, 4.9], [-10.1, 6, 4.9], VINE)                              # ivy up a post
    return m


def bat_bunting():
    m = Model("bat_bunting", dye=(235, 120, 40))
    m.dyebox([-16, 4, 8], [32, 16, 8], bunting(), card=True)                      # 3-wide pennant string
    m.card([-16, 4, 8.06], [32, 16, 8.06], engine.neutral_overlay(bunting()))["overlay"] = True   # bats show from behind too
    m.box([-16, 13.5, 7], [-14.5, 16, 9], iron())                                  # end hooks
    m.box([30.5, 13.5, 7], [32, 16, 9], iron())
    return m


def welcome_sign():
    m = Model("welcome_sign", floor=-16)
    m.box([6.5, -16, 6.5], [9.5, 16, 9.5], gnarl())                               # post
    m.box([4, -16, 4], [12, -14, 12], solid("slate", 3))                          # stone at the base
    m.box([-5, 2, 5], [21, 10, 6.5], big_sign("WELCOME"), res=2)                  # main board, in front of the post
    D = 5 / 2 ** 0.5 / 2                                                          # half side of a diamond as tall as a board
    m.box([-4, -6, 5], [13, -1, 6.5], big_sign("CANDY"), res=2)                    # arrow boards
    m.box([13 - D, -3.5 - D, 5.35], [13 + D, -3.5 + D, 6.15], wood("ebony", plank=2),
          rot=("z", 45, [13, -3.5, 5.75]))                                         # point: half sits inside the board end
    m.box([3, -14, 5], [22, -9, 6.5], big_sign("SPOOKS"), res=2)
    m.box([3 - D, -11.5 - D, 5.35], [3 + D, -11.5 + D, 6.15], wood("ebony", plank=2),
          rot=("z", 45, [3, -11.5, 5.75]))
    m.box([4.5, 16, 4.5], [11.5, 22, 11.5], painted_jack(True), emit=15, res=2)          # jack on top
    m.box([7.6, 22, 7.6], [8.4, 23.4, 8.4], bark("stem"))
    m.card([2, 10, 7.4], [8, 15, 7.4], VINE)
    return m


def harvest_wreath():
    m = Model("harvest_wreath")
    z0, z1 = 14, 16
    m.box([5, 12.5, z0], [11, 15, z1], autumn())                                  # octagon ring of leaves
    m.box([5, 1, z0], [11, 3.5, z1], autumn())
    m.box([1, 5, z0], [3.5, 11, z1], autumn())
    m.box([12.5, 5, z0], [15, 11, z1], autumn())
    for (cx, cy, a) in ((3.6, 12.4, 45), (12.4, 12.4, -45), (3.6, 3.6, -45), (12.4, 3.6, 45)):
        m.box([cx - 2.6, cy - 1.25, z0 + 0.1], [cx + 2.6, cy + 1.25, z1 - 0.1], autumn(), rot=("z", a, [cx, cy, 15]))
    m.box([3, 1.2, 12.5], [6, 4.2, 14], pump_skin())                         # little pumpkin
    m.box([10.5, 1.5, 12.8], [12.5, 3.8, 14], solid("gourd", 1))                  # gourd
    BOW = solid("plum", 2)
    m.box([7.2, 12.6, 12.8], [8.8, 14.4, 13.8], BOW)                              # bow knot, centred on the top
    m.box([4.0, 12.9, 13.0], [7.2, 14.9, 13.6], BOW, rot=("z", -22.5, [7.2, 13.5, 13.3]))   # left loop, tilted up
    m.box([8.8, 12.9, 13.0], [12.0, 14.9, 13.6], BOW, rot=("z", 22.5, [8.8, 13.5, 13.3]))    # right loop, mirrored
    m.card([6, 9.0, 13.45], [10, 12.6, 13.45], art([                                # two ribbon tails
        "..aaaa..", "..a..a..", ".aa..aa.", ".a....a.", "aa....aa", "a......a", "a......a"],
        {"a": ("plum", 3)}), res=2)
    return m


def _stall(name, ramp, trim):
    from hero3 import stall
    return stall(name, ramp, trim)


def potion_stall_moss():
    return _stall("potion_stall_moss", "moss", "pump")


def potion_stall_ember():
    return _stall("potion_stall_ember", "pump", "plum")


def all_models():
    return [hollow_arch(), bat_bunting(), welcome_sign(), harvest_wreath(), potion_stall_moss(), potion_stall_ember()]
