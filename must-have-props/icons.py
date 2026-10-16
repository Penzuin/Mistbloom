"""Must-Have Props store images (Hibiscus style, see claude/brand/ICON_STYLE.md):
main 1024 icon + animated GIF/WebP + one piece icon per piece.
Real renders at one camera and one scale, hard sun shadows tinted from the floor, Minecraft Title
Generator lettering. Shadows are projected box by box; flat floor pieces (the rug) and flat cards
(the plant) get none.
"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, "/root/props/src")
import engine as E
import pieces as P

S = 1024
OUT = "/root/props/media"
TITLES = "/root/props/titles"
os.makedirs(OUT, exist_ok=True)
CAM = (-0.55, 0.75, -1.0)
LIGHT = np.array([-0.45, -1.5, 0.3])
SS = 3
PPU = 7 * SS
FLOOR_MID = np.array([116, 128, 108])    # soft sage-grey: neutral, oak and iron both read on it
FLOOR_EDGE = np.array([70, 80, 64])
BAND = np.array([146, 156, 132])
SHADOW = (34, 40, 30)
SHADOW_A = 0.55
NO_SHADOW = {"hanging_lantern"}   # flat floor pieces and wall pieces (they float in the image)

MODELS = {n: getattr(P, n) for n in ["wooden_crate", "crate_stack", "oak_barrel", "grain_sacks", "apple_basket",
                                      "book_pile", "signpost", "wheelbarrow", "park_bench", "notice_board"]}
for _n in P.LIGHTS:
    MODELS[_n] = (lambda fn: (lambda: fn(True)))(getattr(P, _n))
GLOW = {n: 1 for n in P.LIGHTS}   # warm pools of light under the lit pieces


def basis(cam):
    c = np.array(cam, float); c /= np.linalg.norm(c)
    fwd = -c
    right = np.cross(fwd, [0, 1, 0]); right /= np.linalg.norm(right)
    up = np.cross(right, fwd)
    return c, fwd, right, up


def _rot(e, pts):
    if "rotation" not in e:
        return pts
    r = e["rotation"]
    M = {"x": E._rx, "y": E._ry, "z": E._rz}[r["axis"]](r["angle"])
    o = np.array(r["origin"])
    return [M @ (p - o) + o for p in pts]


def hull(pts):
    pts = sorted(set(map(tuple, np.round(pts, 4))))
    if len(pts) < 3:
        return pts
    def cross(o, a, b): return (a[0]-o[0])*(b[1]-o[1]) - (a[1]-o[1])*(b[0]-o[0])
    lo, up = [], []
    for p in pts:
        while len(lo) >= 2 and cross(lo[-2], lo[-1], p) <= 0: lo.pop()
        lo.append(p)
    for p in reversed(pts):
        while len(up) >= 2 and cross(up[-2], up[-1], p) <= 0: up.pop()
        up.append(p)
    return lo[:-1] + up[:-1]


def render_piece(m, frame=0):
    """Model image + shadow mask on the same canvas."""
    c, fwd, right, up = basis(CAM)
    img = m.render(ppu=PPU, cam=CAM, frame=frame)
    pts = []
    for e in m.elements:
        for f in e["faces"]:
            n = E._NORMALS[f]
            if "rotation" in e:
                r = e["rotation"]
                n = {"x": E._rx, "y": E._ry, "z": E._rz}[r["axis"]](r["angle"]) @ n
            if len(e["faces"]) != 2 and np.dot(n, c) <= 0:
                continue
            pts += _rot(e, E._face_corners(e, f))
    pts = np.array(pts)
    minx, miny = (pts @ right).min(), (-(pts @ up)).min()
    to_px = lambda p: ((p @ right - minx) * PPU + 2, (-(p @ up) - miny) * PPU + 2)
    L = LIGHT / np.linalg.norm(LIGHT)
    floor = min(0.0, min(min(e["from"][1], e["to"][1]) for e in m.elements))
    polys = []
    if m.name not in NO_SHADOW:
        for e in m.elements:
            a, b = np.array(e["from"]), np.array(e["to"])
            if e.get("noshadow") or (np.abs(b - a) < 1e-6).any():          # flat cards (the plant) cast no box shadow
                continue
            cs = _rot(e, [np.array([x, y, z]) for x in (a[0], b[0]) for y in (a[1], b[1]) for z in (a[2], b[2])])
            proj = []
            for p in cs:
                t = (p[1] - floor) / -L[1]
                g = p + L * t; g[1] = floor
                proj.append(to_px(g))
            polys.append(hull(np.array(proj)))
    allp = np.array([q for poly in polys for q in poly] + [(0, 0), (img.width, img.height)])
    ox, oy = -min(0, allp[:, 0].min()) + 4, -min(0, allp[:, 1].min()) + 4
    W = int(max(allp[:, 0].max(), img.width) + ox + 4)
    H = int(max(allp[:, 1].max(), img.height) + oy + 4)
    sh = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(sh)
    for poly in polys:
        if len(poly) >= 3:
            d.polygon([(x + ox, y + oy) for x, y in poly], fill=255)
    model = Image.new("RGBA", (W, H))
    model.alpha_composite(img, (int(round(ox)), int(round(oy))))
    if m.name == "props_scene":
        _cache[("room_off",)] = (int(round(ox)), int(round(oy)))
    return model, sh


def background():
    y, x = np.mgrid[0:S, 0:S].astype(float)
    d = np.sqrt(((x - S * 0.55) / S) ** 2 + ((y - S * 0.42) / S) ** 2)
    t = np.clip((d - 0.18) / 0.55, 0, 1)[..., None]
    img = FLOOR_MID * (1 - t) + FLOOR_EDGE * t
    k = y + (x - S / 2) * -0.22
    for lo, hi, a in ((260, 600, 0.26), (600, 650, 0.1)):
        msk = ((k > lo) & (k < hi))[..., None]
        img = np.where(msk, img * (1 - a) + BAND * a, img)
    return Image.fromarray(img.astype(np.uint8)).convert("RGBA")


_cache = {}


def piece(name, frame=0, scale=1.0):
    key = (name, frame)
    if key not in _cache:
        _cache[key] = render_piece(MODELS[name](), frame)
    m, s = _cache[key]
    f = scale / SS
    size = (round(m.width * f), round(m.height * f))
    return m.resize(size, Image.LANCZOS), s.resize(size, Image.LANCZOS)


def crop(p):
    im = Image.open(p).convert("RGBA")
    a = np.array(im)[..., 3]; a[a < 40] = 0
    arr = np.array(im); arr[..., 3] = a
    im = Image.fromarray(arr)
    return im.crop(im.getbbox())


def title(name, small_ratio=0.62, overlap=0.35, small_w=None):
    big = crop(f"{TITLES}/{name}_big.png")
    if not os.path.exists(f"{TITLES}/{name}_small.png"):
        return big
    small = crop(f"{TITLES}/{name}_small.png")
    if small_w:                                         # second word ~80% as wide as the main word
        tw = round(big.width * small_w)
        small = small.resize((tw, round(small.height * tw / small.width)), Image.LANCZOS)
    else:
        sh_ = round(big.height * small_ratio)
        small = small.resize((round(small.width * sh_ / small.height), sh_), Image.LANCZOS)
        if small.width < big.width * 0.5:                  # short second words ("lamp") stay readable
            f = big.width * 0.5 / small.width
            small = small.resize((round(small.width * f), round(small.height * f)), Image.LANCZOS)
        if small.width > big.width * 1.15:
            f = big.width * 1.15 / small.width
            small = small.resize((round(small.width * f), round(small.height * f)), Image.LANCZOS)
    ov = round(big.height * overlap)
    W, H = max(big.width, small.width), big.height + small.height - ov
    t = Image.new("RGBA", (W, H))
    t.alpha_composite(big, ((W - big.width) // 2, 0))
    t.alpha_composite(small, ((W - small.width) // 2, big.height - ov))
    return t


def glow(img, m, xy, name, k):
    """A soft warm pool of lamplight on the floor round a lit piece (it really lights the floor in game)."""
    if name not in GLOW:
        return
    bb = m.getbbox()
    cx, cy = xy[0] + (bb[0] + bb[2]) / 2, xy[1] + bb[3] - (bb[3] - bb[1]) * 0.12
    rx = (bb[2] - bb[0]) * 1.25
    y, x = np.mgrid[0:S, 0:S].astype(float)
    d = np.sqrt(((x - cx) / rx) ** 2 + ((y - cy) / (rx * 0.5)) ** 2)
    a = np.clip(1 - d, 0, 1) ** 1.5 * 0.6 * k
    layer = np.zeros((S, S, 4), np.uint8)
    layer[..., :3] = (255, 214, 140)
    layer[..., 3] = (a * 255).astype(np.uint8)
    img.alpha_composite(Image.fromarray(layer, "RGBA"))


def put(img, m, s, xy, name):
    if name not in NO_SHADOW:
        sh = Image.new("RGBA", m.size, SHADOW + (0,))
        sh.putalpha(s.point(lambda v: int(v * SHADOW_A)))
        img.alpha_composite(sh, xy)


# (piece, x of piece centre, y of piece bottom) -- back row first
LAYOUT = [("wardrobe", 175, 455), ("wall_shelf", 400, 230), ("quilted_bed", 690, 430),
          ("braided_rug", 520, 660), ("bedside_table", 330, 640), ("floor_cushions", 700, 650), ("toadstool_lamp", 880, 640)]
SCALE = 1.6


# ---- the main icon is one real room, rendered as a single scene so pieces overlap correctly.
# World units are model pixels (16 per block). +z is the back wall, +x is screen-left.
# The bed is turned 90 degrees so its headboard sits against the back wall (players can rotate
# furniture in game), with the bedside table on one side, the lamp on the other, the shelf on
# the wall above the headboard, the wardrobe along the back wall, and the rug at the foot of the
# bed with the floor cushions on it.
ROOM = [  # (piece, (dx, dy, dz), turned): one row per group, back to front, in listing order.
    # Lights at the back (the street lamp is the tallest piece); the hanging lantern hangs in the air, no shadow.
    ("street_lamp", (76, 0, 84), False), ("iron_lantern", (50, 0, 84), False), ("hanging_lantern", (24, 18, 84), False),
    ("candle_cluster", (0, 0, 84), False),
    # Outdoor & town in the middle
    ("signpost", (96, 0, 36), False), ("notice_board", (70, 0, 36), False), ("park_bench", (20, 0, 36), False),
    ("wheelbarrow", (-28, 0, 36), False),
    # Storage & clutter at the front
    ("wooden_crate", (104, 0, -12), False), ("crate_stack", (62, 0, -12), False), ("oak_barrel", (36, 0, -12), False),
    ("grain_sacks", (12, 0, -12), False), ("apple_basket", (-12, 0, -12), False), ("book_pile", (-34, 0, -12), False),
]
_TURN = {"east": "south", "west": "north", "south": "west", "north": "east", "up": "up", "down": "down"}
_UNTURN = {v: k for k, v in _TURN.items()}


def _turned(painter):
    """Paint a turned face as the face it was before the turn, so panels and shading stay put."""
    def f(w, h, face, key):
        return painter(w, h, _UNTURN[face], key)
    for a in ("animated", "is_animated", "_animated"):
        if hasattr(painter, a):
            setattr(f, a, getattr(painter, a))
    f.__dict__.update(getattr(painter, "__dict__", {}))
    return f


def room_model():
    room = E.Model("props_scene")
    for name, (dx, dy, dz), turned in ROOM:
        m = MODELS[name]()
        for e in m.elements:
            e = dict(e, faces=dict(e["faces"]))
            a, b = list(e["from"]), list(e["to"])
            if turned:                       # 90 degrees: old +x (head) becomes +z (back wall)
                a, b = [16 - b[2], a[1], a[0]], [16 - a[2], b[1], b[0]]
                e["faces"] = {_TURN[k]: _turned(p) for k, p in e["faces"].items()}
                assert "rotation" not in e
            e["from"] = [a[0] + dx, a[1] + dy, a[2] + dz]
            e["to"] = [b[0] + dx, b[1] + dy, b[2] + dz]
            if "rotation" in e:
                r = dict(e["rotation"]); o = r["origin"]
                r["origin"] = [o[0] + dx, o[1] + dy, o[2] + dz]
                e["rotation"] = r
            if name in NO_SHADOW:
                e["noshadow"] = True
            room.elements.append(e)
    return room


def main_icon(frame=0):
    img = background()
    key = ("room", frame)
    if key not in _cache:
        _cache[key] = render_piece(room_model(), frame)
    m, s = _cache[key]
    bb = m.getbbox()
    k = min(940 / (bb[2] - bb[0]), 690 / (bb[3] - bb[1]))
    m = m.resize((round(m.width * k), round(m.height * k)), Image.LANCZOS)
    s = s.resize(m.size, Image.LANCZOS)
    bb = m.getbbox()
    xy = (round(S / 2 - (bb[0] + bb[2]) / 2), round(735 - bb[3]))
    sh = Image.new("RGBA", m.size, SHADOW + (0,))
    sh.putalpha(s.point(lambda v: int(v * SHADOW_A)))
    img.alpha_composite(sh, xy)
    _room_glow(img, m, xy, k)
    img.alpha_composite(m, xy)
    t = title("main", small_w=0.5, overlap=0.3)
    tw = 640
    t = t.resize((tw, round(t.height * tw / t.width)), Image.LANCZOS)
    img.alpha_composite(t, ((S - tw) // 2, S - t.height - 30))
    return img.convert("RGB")


def _room_glow(img, m, xy, k):
    """Warm pool under the lamp: find the lamp's foot in the scene image by projecting it."""
    c, fwd, right, up = basis(CAM)
    room = room_model()
    pts = []
    for e in room.elements:
        for f in e["faces"]:
            n = E._NORMALS[f]
            if "rotation" in e:
                r = e["rotation"]
                n = {"x": E._rx, "y": E._ry, "z": E._rz}[r["axis"]](r["angle"]) @ n
            if len(e["faces"]) != 2 and np.dot(n, c) <= 0:
                continue
            pts += _rot(e, E._face_corners(e, f))
    pts = np.array(pts)
    minx, miny = (pts @ right).min(), (-(pts @ up)).min()
    off = _cache.get(("room_off",), (0, 0))
    y, x = np.mgrid[0:S, 0:S].astype(float)
    a = np.zeros((S, S))
    for name, (dx, dy, dz), turned in ROOM:
        if name not in GLOW:
            continue
        foot = np.array([dx + 8.0, 0.0, dz + 8.0])
        px = (foot @ right - minx) * PPU + 2
        py = (-(foot @ up) - miny) * PPU + 2
        cx, cy = xy[0] + (px + off[0]) * k, xy[1] + (py + off[1]) * k
        rx = 85 if name != "street_lamp" else 110
        d = np.sqrt(((x - cx) / rx) ** 2 + ((y - cy) / (rx * 0.5)) ** 2)
        a = np.maximum(a, np.clip(1 - d, 0, 1) ** 1.5 * 0.5)
    layer = np.zeros((S, S, 4), np.uint8)
    layer[..., :3] = (255, 214, 140)
    layer[..., 3] = (a * 255).astype(np.uint8)
    img.alpha_composite(Image.fromarray(layer, "RGBA"))


def main_icon_old(frame=0):
    img = background()
    items = []
    for name, cx, by in LAYOUT:
        m, s = piece(name, frame, SCALE)
        bb = m.getbbox()
        items.append((name, m, s, (round(cx - (bb[0] + bb[2]) / 2), round(by - bb[3])), bb))
    lo = min(xy[0] + bb[0] for _, _, _, xy, bb in items)
    hi = max(xy[0] + bb[2] for _, _, _, xy, bb in items)
    dx = round(S / 2 - (lo + hi) / 2)                  # centre the pieces (not their shadows) over the title
    items = [(n, m, s, (xy[0] + dx, xy[1]), bb) for n, m, s, xy, bb in items]
    for n, m, s, xy, bb in items:
        glow(img, m, xy, n, 1.0)
    for n, m, s, xy, bb in items:
        put(img, m, s, xy, n)
    for n, m, s, xy, bb in items:
        img.alpha_composite(m, xy)
    t = title("main", small_w=0.5, overlap=0.3)
    tw = 560
    t = t.resize((tw, round(t.height * tw / t.width)), Image.LANCZOS)
    img.alpha_composite(t, ((S - tw) // 2, S - t.height - 36))
    return img.convert("RGB")


def piece_icon(name, frame=0):
    img = background()
    m, s = piece(name, frame, 1.0)
    bb = m.getbbox()
    k = min((470 if name in NO_SHADOW else 560) / (bb[3] - bb[1]), 680 / (bb[2] - bb[0]))
    m = m.resize((round(m.width * k), round(m.height * k)), Image.LANCZOS)
    s = s.resize(m.size, Image.LANCZOS)
    bb = m.getbbox()
    lift = 90 if name in NO_SHADOW else 0               # ceiling pieces hang clear of the floor
    xy = (round(S / 2 - (bb[0] + bb[2]) / 2), round(650 - lift - bb[3]))
    glow(img, m, xy, name, 1.0)
    put(img, m, s, xy, name)
    img.alpha_composite(m, xy)
    t = title(name)
    tw = min(900 if "_" not in name else 760, round(t.width * 270 / t.height))
    t = t.resize((tw, round(t.height * tw / t.width)), Image.LANCZOS)
    img.alpha_composite(t, ((S - tw) // 2, S - t.height - 40))
    return img.convert("RGB")


def animate(frames_fn, gif, webp):
    frames = [frames_fn(k) for k in range(E.NFRAMES)]
    frames[0].save(webp, save_all=True, append_images=frames[1:], duration=150, loop=0, quality=92, method=6)
    strip = Image.new("RGB", (S, S * len(frames)))
    for k, f in enumerate(frames):
        strip.paste(f, (0, S * k))
    pal = strip.quantize(colors=256, method=Image.Quantize.MEDIANCUT)
    g = [f.quantize(palette=pal, dither=Image.Dither.FLOYDSTEINBERG) for f in frames]
    base_rgb, base_idx = np.array(frames[0]).astype(int), np.array(g[0])
    for k in range(1, len(g)):                          # lock static pixels so nothing shimmers
        same = np.abs(np.array(frames[k]).astype(int) - base_rgb).sum(2) == 0
        idx = np.array(g[k]); idx[same] = base_idx[same]
        im = Image.fromarray(idx, "P"); im.putpalette(g[0].getpalette()); g[k] = im
    g[0].save(gif, save_all=True, append_images=g[1:], duration=150, loop=0, optimize=False, disposal=1)


ORDER = [n for n, _, _ in ROOM]   # same order as the main image: lights, outdoor & town, storage & clutter

if __name__ == "__main__":
    which = sys.argv[1:] or ["main", "pieces", "anim"]
    if "main" in which:
        main_icon().save(f"{OUT}/must-have-props-icon.png")
    if "pieces" in which:
        for i, n in enumerate(ORDER, 1):
            piece_icon(n).save(f"{OUT}/must-have-props-{i:02d}-{n.replace('_', '-')}.png")
    if "anim" in which:
        animate(main_icon, f"{OUT}/must-have-props-icon-animated.gif", f"{OUT}/must-have-props-icon-animated.webp")
    print("done")
