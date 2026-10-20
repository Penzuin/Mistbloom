"""Moonlit Ballroom: redesigned Floating Candelabra, Ghost Lantern and Portrait of Lady Wispwell
(user, Oct 19 2026). Same pack style, palette and resolution as the original; the ghost
characters (hand, lantern ghost, Lady Wispwell's painting) keep their original sprites.
Front faces north (-z); the portrait's back is on z=16. Every model <= 14 elements."""
from engine import Model, solid, wood, candle_p, moonflame, pane_arch, art, sprite, T, _blank
import sprites as S
from pieces import EBONY, BSILVER, gilt

GOLD = solid("gold", 1)
GOLD_D = solid("gold", 2)

def floating_candelabra(lit=False):
    """A gilded five-point candelabra held up by the friendly ghost hand: baluster stem with a gold
    knop, two arms sweeping up into drip cups, three candles stepped in height."""
    m = Model("floating_candelabra_lit" if lit else "floating_candelabra")
    m.crossed(8, 0.5, 8, 6, 7, sprite(S.ghost_hand), emit=10, res=3)                 # the hand holding it up
    m.box([7.25, 6, 7.25], [8.75, 15, 8.75], BSILVER, res=2)                          # stem
    m.box([6.5, 9, 6.5], [9.5, 10.5, 9.5], GOLD, res=2)                               # knop
    m.box([2.5, 14, 7.25], [8, 15, 8.75], BSILVER, rot=("z", -22.5, [8, 14.5, 8]), res=2)   # left arm, sweeping up
    m.box([8, 14, 7.25], [13.5, 15, 8.75], BSILVER, rot=("z", 22.5, [8, 14.5, 8]), res=2)   # right arm
    m.box([1.25, 16.25, 6.5], [4.25, 17.25, 9.5], GOLD, res=2)                        # side drip cups
    m.box([11.75, 16.25, 6.5], [14.75, 17.25, 9.5], GOLD, res=2)
    m.box([2, 17.25, 7.25], [3.5, 21.25, 8.75], candle_p(), res=2)
    m.box([12.5, 17.25, 7.25], [14, 21.25, 8.75], candle_p(), res=2)
    m.box([7.25, 15, 7.25], [8.75, 23.5, 8.75], candle_p(), res=2)                    # tall centre candle on the stem
    if lit:
        for x, y in ((2.75, 21.25), (13.25, 21.25), (8, 23.5)):
            m.card([x - 1, y, 8], [x + 1, y + 3, 8], moonflame(), rot=("y", 45, [x, y, 8]), emit=15, res=2)
    return m

def ghost_lantern(lit=False):
    """A taller gothic lantern: stepped base, arched glass panes between four corner posts, a gold
    eave, a stepped three-tier roof and a gold finial. The little ghost still lives inside.
    No two faces share a plane: the glass sits 0.1 inside the posts, base and eave, and has no
    top face; roof tiers and finial have no bottom faces, so nothing sits flush."""
    m = Model("ghost_lantern_lit" if lit else "ghost_lantern")
    m.box([4, 0, 4], [12, 1, 12], BSILVER, res=2)                                     # base
    m.box([4.75, 1, 4.75], [11.25, 1.75, 11.25], GOLD_D, faces=("north", "south", "east", "west", "up"), res=2)
    m.card([5.75, 1.85, 8], [10.25, 8.85, 8], sprite(S.lantern_ghost), emit=12 if lit else 6, res=4)
    m.box([5.1, 1.85, 5.1], [10.9, 10.9, 10.9], pane_arch(lit), faces=("north", "south", "east", "west"), res=2)
    for i, (x, z) in enumerate(((4.4, 4.4), (10.6, 4.4), (4.4, 10.6), (10.6, 10.6))):
        m.box([x, 1.75, z], [x + 1, 11, z + 1], BSILVER, faces=("north", "south", "east", "west"), res=2)   # corner posts
    m.box([4, 11, 4], [12, 11.75, 12], GOLD, res=2)                                   # eave
    SIDES5 = ("north", "south", "east", "west", "up")
    m.box([4.5, 11.75, 4.5], [11.5, 12.75, 11.5], shingles(), faces=SIDES5, res=3)     # bell roof: tiers stepping in
    m.box([5.25, 12.75, 5.25], [10.75, 13.75, 10.75], shingles(), faces=SIDES5, res=3) # more each time, shingled
    m.box([6.25, 13.75, 6.25], [9.75, 14.5, 9.75], shingles(), faces=SIDES5, res=3)
    m.box([7, 14.5, 7], [9, 15.75, 9], GOLD, faces=SIDES5, res=2)                     # gold finial
    m.card([6.5, 15.5, 8], [9.5, 18, 8], RING, res=2)                                  # hanging ring
    return m

def shingles():
    """blacksilver roof tier in clean bands: lit top edge, mid body, darker bottom edge where it
    overhangs; the top face is lighter. No ticks or dots."""
    def f(w, h, face, key):
        img = _blank(w, h)
        if face == "up":
            img[:, :] = T("blacksilver", 1.5)
            img[0, :] = T("blacksilver", 0.5); img[:, 0] = T("blacksilver", 0.5)
            return img
        img[:, :] = T("blacksilver", 2.5)
        img[0, :] = T("blacksilver", 1)
        img[-1, :] = T("blacksilver", 4)
        return img
    return f

RING = art([
    ".aaaa.",
    "a....a",
    "a....a",
    ".a..a.",
    "..aa..",
], {"a": ("gold", 1)})

CREST = art([
    "......dd......",
    "....ddbbdd....",
    "...dbbccbbd...",
    "..dbmdcedmbd..",
    ".dbm.dmmd.mbd.",
    "dbm...dd...mbd",
    "dddddddddddddd",
], {"d": ("gold", 3), "b": ("gold", 0), "m": ("gold", 2), "c": ("violet", 0), "e": ("violet", 3)})

def gilt2(side):
    """carved gilt moulding, 6 texels across at res 3: bright outer bead, light slope, a bead row,
    a shaded cove, a dark groove and a lit inner lip. The top and left rails catch the light, the
    bottom and right rails sit half a step darker; the outer side faces step from light to dark."""
    lift = {"top": -0.5, "left": -0.5, "bottom": 1.0, "right": 1.0}[side]
    PROFILE = [0.5, 1.5, None, 3.0, 5.0, 2.0]        # outer -> inner; None = bead row
    def f(w, h, face, key):
        img = _blank(w, h)
        horiz = side in ("top", "bottom")
        if face != "north":
            base = {"up": 0.5, "down": 3.5, "west": 1.5, "east": 3.0, "south": 4.0}[face]
            L, Tn = (w, h) if face in ("up", "down") or horiz else (h, w)
            for y in range(h):
                for x in range(w):
                    t = y if face not in ("up", "down") else (x if not horiz else y)
                    tone = base + lift + (0.5 if y == h - 1 and face not in ("up", "down") else 0) - (0.5 if y == 0 else 0)
                    img[y, x] = T("gold", tone)
            return img
        L, Tn = (w, h) if horiz else (h, w)
        for t in range(Tn):
            k = min(len(PROFILE) - 1, int(t * len(PROFILE) / Tn))
            for l in range(L):
                p = PROFILE[k]
                tone = (0.5 if (l // 2) % 2 else 3.0) if p is None else p
                tone += lift
                tt = t if side in ("top", "left") else Tn - 1 - t
                x, y = (l, tt) if horiz else (tt, l)
                img[y, x] = T("gold", tone)
        return img
    return f

ROSETTE = art([
    ".abba.",
    "abccba",
    "bcddcb",
    "bcddcb",
    "abccba",
    ".abba.",
], {"a": ("gold", 3), "b": ("gold", 2), "c": ("gold", 0), "d": ("violet", 1)})

def ghost_portrait():
    """Taller gilt frame with corner rosettes, an arched scroll crest with a violet gem, and a name
    plate. Lady Wispwell's painting is the original."""
    m = Model("ghost_portrait")
    m.box([2, 3, 15], [14, 21, 16], EBONY)                                            # backing board
    m.card([2, 3, 14.6], [14, 21, 14.6], sprite(S.portrait, mirror_back=False), res=3.5)   # the painting
    m.box([0, 1, 14], [2, 23, 16], gilt2("left"), res=2.5)                              # carved frame
    m.box([14, 1, 14], [16, 23, 16], gilt2("right"), res=2.5)
    m.box([2, 21, 14], [14, 23, 16], gilt2("top"), res=2.5)
    m.box([2, 1, 14], [14, 3, 16], gilt2("bottom"), res=2.5)
    for i, (x, y) in enumerate(((-0.5, 0.5), (13.5, 0.5), (-0.5, 20.5), (13.5, 20.5))):
        m.box([x, y, 13.5], [x + 3, y + 3, 14], ROSETTE, faces=("north", "east", "west", "up", "down"), res=2)   # corner rosettes
    m.card([1, 23, 15], [15, 30, 15], CREST, res=2)                                   # arched crest
    m.box([5, 1.4, 13.6], [11, 2.6, 14], solid("gold", 0), res=2)                     # name plate
    return m

NEW = [lambda: floating_candelabra(False), lambda: floating_candelabra(True),
       lambda: ghost_lantern(False), lambda: ghost_lantern(True), ghost_portrait]
