"""Hollowmere witchy batch. Front faces NORTH (-z). Max 14 elements per model."""
import random
import engine
from engine import Model, wood, solid, T, _blank, fr, animated, SIDES, art, tinted
from hero3 import bark, iron, candle_flame, wax
from harvest import loose_hay, apple, pumpkin
from spooky import COBWEB

engine.RAMPS.update({k: engine._ramp7(v) for k, v in {
    "page":  ["#fffaf0", "#f3e6cc", "#dcc7a2", "#b49f7c"],
    "cryst": ["#f3e6ff", "#c9a8f5", "#9a6be0", "#5e3aa8"],
    "teal":  ["#c8fff0", "#6fe0c4", "#36a891", "#1f6b62"],
}.items()})


def bottle(liquid="brew", fill=0.65, cork=True):
    """Glass bottle: coloured liquid up to `fill`, pale glass above, cork on top, label band."""
    def f(w, h, fc, key):
        img = _blank(w, h)
        cut = int(h * (1 - fill))
        img[:, :] = T(liquid, 1)
        img[:cut, :] = T("frost", 1, 230)
        if fc in SIDES:
            if cut < h: img[cut, :] = T(liquid, 0)                    # meniscus
            if w >= 3 and h >= 4:
                img[1:h - 1, max(1, w // 4)] = T("snow", 0, 210)     # glint
            if fc == "north" and w >= 4 and h >= 6:
                ly = cut + (h - cut) // 2
                img[ly:ly + 2, :] = T("page", 1)                     # label
        if fc == "up":
            img[:, :] = T("rust", 2) if cork else T("frost", 1, 230)  # cork, or glass shoulder
        if fc == "down":
            img[:, :] = T(liquid, 3)
        return img
    return f


def pages():
    def f(w, h, fc, key):
        img = _blank(w, h)
        img[:, :] = T("page", 1)
        if fc == "up":
            for y in range(1, h - 1, 2):
                for x in range(1, w - 1):
                    if (x + y) % 5:
                        img[y, x] = T("ebony", 3) if (x * 3 + y) % 7 else T("plum", 2)   # scribbled spells
            img[:, 0] = img[:, -1] = T("page", 2)
        if fc in SIDES:
            for y in range(h):
                img[y, :] = T("page", 1 + y % 2)                     # page edges
        return img
    return f


def crystal(lit=True):
    def f(w, h, fc, key):
        k = fr()
        img = _blank(w, h)
        cx, cy = (w - 1) / 2, (h - 1) / 2
        for y in range(h):
            for x in range(w):
                d = max(abs(x - cx) / max(cx, 1), abs(y - cy) / max(cy, 1))
                swirl = int((x - cx) * 0.8 - (y - cy) * 0.6 + k) % 5 == 0
                tone = 0 if d < 0.25 else (1 if swirl else 2) if d < 0.75 else 3
                img[y, x] = T("cryst", tone, 235)
        if fc in SIDES and w > 2:
            img[1, 1] = T("snow", 0)                                  # highlight
        return img
    return animated(f)


def hat_felt():
    def f(w, h, fc, key):
        img = _blank(w, h)
        img[:, :] = T("cream", 1)
        if fc in SIDES and h > 2:
            img[-1, :] = T("cream", 2)
        return img
    return tinted(f)


def broom_bristles():
    base = loose_hay()
    def f(w, h, fc, key):
        img = base(w, h, fc, key)
        if fc in SIDES:
            for x in range(0, w, 2):
                img[-1, x, 3] = 0                                     # ragged ends
        return img
    return f


# ------------------------------------------------------------------ pieces
def spellbook_lectern():
    m = Model("spellbook_lectern")
    m.box([3, 0, 4], [13, 1.5, 12], bark("ebony"))                                # foot
    m.box([6.5, 1.5, 6.5], [9.5, 10, 9.5], bark("ebony"))                         # carved column
    m.box([5.5, 4, 5.5], [10.5, 5.2, 10.5], solid("gold", 2))                     # brass ring
    m.box([2, 10, 3], [14, 11.2, 13], wood("ebony", plank=2), rot=("x", -22.5, [8, 10.6, 8]))   # slanted desk
    m.box([2.6, 11.2, 4], [7.9, 12.4, 12], pages(), rot=("x", -22.5, [8, 10.6, 8]))           # open book
    m.box([8.1, 11.2, 4], [13.4, 12.4, 12], pages(), rot=("x", -22.5, [8, 10.6, 8]))
    m.box([2.3, 10.9, 3.6], [13.7, 11.3, 12.4], solid("plum", 3), rot=("x", -22.5, [8, 10.6, 8]))  # cover
    m.box([7.7, 6, 13.4], [8.3, 11.2, 13.8], solid("pump", 1, bevel=False), rot=("x", -22.5, [8, 10.6, 8]))   # ribbon
    m.box([12, 1.5, 9.5], [13.5, 4.5, 11], wax())                                 # candle stub on the foot
    m.card([12, 4.5, 10.25], [13.5, 6.5, 10.25], candle_flame(), emit=15)
    return m


def crystal_ball():
    m = Model("crystal_ball")
    m.box([4, 0, 4], [12, 1.5, 12], bark("ebony"))                               # base, crossed
    m.box([5, 0.2, 3], [11, 1.3, 13], bark("ebony"))
    m.box([6, 1.5, 6], [10, 3.2, 10], solid("gold", 2))                           # brass cup
    m.box([5.2, 3.2, 7.4], [6.2, 5.6, 8.6], solid("gold", 1))                     # claws gripping the orb
    m.box([9.8, 3.2, 7.4], [10.8, 5.6, 8.6], solid("gold", 1))
    m.box([7.4, 3.2, 5.2], [8.6, 5.6, 6.2], solid("gold", 1))
    m.box([7.4, 3.2, 9.8], [8.6, 5.6, 10.8], solid("gold", 1))
    m.box([5, 3.6, 5.6], [11, 9.6, 10.4], crystal(), emit=10)                     # round orb: crossed + a 45 turn
    m.box([5.6, 3.6, 5], [10.4, 9.6, 11], crystal(), emit=10)
    m.box([5.4, 4.0, 5.4], [10.6, 9.2, 10.6], crystal(), emit=10, rot=("y", 45, [8, 4, 8]))
    m.box([6, 3.2, 6], [10, 10.2, 10], crystal(), emit=10)                        # top and bottom curve
    return m


def potion_shelf():
    m = Model("potion_shelf")
    m.box([1, 5, 12], [15, 6, 16], wood("ebony", plank=2))                        # lower shelf
    m.box([1, 11, 12], [15, 12, 16], wood("ebony", plank=2))                      # upper shelf
    m.box([2, 2, 15], [3, 13, 16], iron())                                        # wall brackets
    m.box([13, 2, 15], [14, 13, 16], iron())
    m.box([2, 6, 13], [4.5, 10, 15], bottle("brew"))                              # bottles
    m.box([5.5, 6, 12.6], [8, 9, 15], bottle("plum", 0.5))
    m.box([9.5, 6, 13], [11.5, 10.5, 15], bottle("pump", 0.8))
    m.box([3, 12, 13], [6, 15, 15], bottle("teal", 0.6))
    m.box([7.5, 12, 12.8], [9.5, 16, 15], bottle("apple", 0.7))
    m.box([11, 12, 13.2], [13.5, 14, 15], solid("ebony", 3), over={"up": solid("bone", 1)})   # jar of eyes
    m.card([12, 1, 15.9], [16, 6, 15.9], COBWEB)
    m.card([0, 2, 15.9], [3, 6, 15.9], art(["..a..", ".aba.", "abba.", ".bb..", "..c..", "..c.."],
                                         {"a": ("moss", 1), "b": ("moss", 3), "c": ("hay", 2)}))   # herb bunch
    return m


def potion_trio():
    m = Model("potion_trio")
    m.box([2.5, 0, 6.5], [6.5, 4, 10.5], bottle("brew", 0.75, cork=False))      # round flask, crossed
    m.box([3, 0.3, 6], [6, 3.7, 11], bottle("brew", 0.75, cork=False))
    m.box([3.9, 4, 7.9], [5.1, 6.5, 9.1], bottle("brew", 0.0))                  # neck + cork
    m.box([8, 0, 4], [10, 6, 6], bottle("plum", 0.8, cork=False))               # tall thin bottle
    m.box([8.5, 6, 4.5], [9.5, 8.5, 5.5], bottle("plum", 0.0))
    m.box([10, 0, 9], [13.5, 3, 12.5], bottle("pump", 0.6, cork=False))         # squat jar
    m.box([9.7, 3, 8.7], [13.8, 3.8, 12.8], solid("rust", 2))                   # jar lid
    m.box([11, 3.8, 10.2], [12.5, 4.4, 11.2], solid("rust", 1))                 # lid knob
    m.box([11.5, 0, 5.5], [13.5, 0.6, 7.5], solid("gold", 1), rot=("y", 22.5, [12.5, 0, 6.5]))   # a coin
    return m


def witch_broom():
    m = Model("witch_broom", floor=-16)
    m.box([7, -11, 9.5], [9, 19, 11.5], bark("spruce"), rot=("x", -22.5, [8, -11, 10.5]))   # handle leaning on the wall
    m.box([4, -16, 5.5], [12, -7, 11.5], broom_bristles())                        # bristles, crossed
    m.box([4.6, -15.8, 4.8], [11.4, -7.5, 12.2], broom_bristles())
    m.box([5.8, -7.5, 6.8], [10.2, -4.5, 10.2], broom_bristles())                 # bound top
    m.box([5.4, -8, 6.4], [10.6, -6.8, 10.6], solid("plum", 2, bevel=False))      # ribbon tie
    m.box([7.4, -6.8, 6.4], [8.6, -9.5, 6.6], solid("plum", 1, bevel=False)) if False else None
    m.box([0.5, -16, 1.5], [5, -12, 6], solid("pump", 2))                         # tiny pumpkin by the bristles
    m.box([2.4, -12, 3.4], [3.2, -11, 4.2], bark("stem"))
    return m


def witch_hat_stand():
    m = Model("witch_hat_stand", dye=(110, 70, 160))
    m.box([4, 0, 4], [12, 1.2, 12], bark("ebony"))                               # base
    m.box([7.25, 1.2, 7.25], [8.75, 9, 8.75], bark("ebony"))                      # pole
    m.box([1, 9, 1], [15, 9.8, 15], hat_felt())                                   # wide brim
    m.box([4, 9.8, 4], [12, 13, 12], hat_felt())                                  # crown tiers
    m.box([5, 13, 5], [11, 16, 11], hat_felt())
    m.box([6, 16, 6], [10, 19, 10], hat_felt(), rot=("z", 22.5, [8, 16, 8]))
    m.box([6.5, 18.5, 6.5], [9.5, 21.5, 9.5], hat_felt(), rot=("z", 45, [8, 18.5, 8]))   # bent tip
    m.box([3.9, 9.8, 3.9], [12.1, 11, 12.1], solid("pump", 2, bevel=False))       # band (keeps its colour)
    m.box([7, 9.8, 3.6], [9, 11.2, 3.9], solid("gold", 1, bevel=False))           # buckle
    return m


def candle_cluster():
    m = Model("candle_cluster")
    m.box([3, 0, 4], [13, 0.6, 12], solid("candle", 2), faces=("up", "north", "south", "east", "west"))   # wax puddle
    for (x, z, hgt, w) in ((4, 6, 7, 2), (7, 5, 10, 2.2), (10, 7, 5, 2), (6, 9, 4, 1.6), (9.5, 10, 8, 1.8)):
        m.box([x, 0.6, z], [x + w, hgt, z + w], wax())
        m.card([x, hgt, z + w / 2], [x + w, hgt + 2, z + w / 2], candle_flame(), emit=15)
    return m


def all_models():
    return [spellbook_lectern(), crystal_ball(), potion_shelf(), potion_trio(), witch_broom(),
            witch_hat_stand(), candle_cluster()]
