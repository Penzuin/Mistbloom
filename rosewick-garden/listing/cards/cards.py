"""Rosewick Garden piece cards (brand/ICON_STYLE.md): one Hibiscus-style card per piece on a midnight-blue
garden-at-dusk floor with warm light bands, hard texel shadows falling right, the piece's name in Minecraft Title
Generator lettering (first word big in rose pink, the rest small in sage green). The lit stake lantern also gets a GIF."""
import json, os, sys
import numpy as np
from PIL import Image
sys.path.insert(0, "/home/claude/hfship/thumb"); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import compose as C
from rrender import render

A = "/home/claude/rosewick/build/Rosewick-Garden/Nexo/pack/assets"; M = A + "/rosewick/models/furniture/"
HERE = os.path.dirname(os.path.abspath(__file__)); T = HERE + "/titles"; OUT = HERE + "/out"
S = 1024
FLOOR_MID, FLOOR_EDGE, BAND = np.array([74, 86, 146]), np.array([32, 36, 84]), np.array([236, 204, 172])
SHADOW, SHADOW_A = (18, 20, 50), 0.55
SPLIT = json.load(open(HERE + "/split.json"))
ORDER = ["garden_bench", "garden_chair", "tea_table", "potting_table", "seed_cabinet", "tool_rack", "rose_trellis",
         "arbor_arch", "birdbath", "flower_box", "wheelbarrow", "sundial", "picnic_blanket", "stake_lantern"]
MODEL = {"stake_lantern": "stake_lantern_lit"}
TINT = {"garden_bench": (143, 176, 106), "garden_chair": (143, 176, 106), "picnic_blanket": (200, 70, 85)}
# stake_lantern_lit.png.mcmeta: frame index and ticks
ANIM = [(0, 3), (1, 2), (2, 4), (3, 2), (4, 3), (5, 3), (2, 2), (1, 3), (4, 2), (3, 3)]

def background():
    y, x = np.mgrid[0:S, 0:S].astype(float)
    d = np.sqrt(((x - S * 0.55) / S) ** 2 + ((y - S * 0.42) / S) ** 2)
    t = np.clip((d - 0.18) / 0.55, 0, 1)[..., None]
    img = FLOOR_MID * (1 - t) + FLOOR_EDGE * t
    k = y + (x - S / 2) * -0.22
    for lo, hi, a in ((250, 590, 0.20), (590, 640, 0.09)):
        m = ((k > lo) & (k < hi))[..., None]
        img = np.where(m, img * (1 - a) + BAND * a, img)
    return Image.fromarray(img.astype(np.uint8)).convert("RGBA")

def word(w, kind):
    return C.clean(Image.open(f"{T}/w_{w.replace(' ', '_')}_{kind}.png"), 5000 if kind == "big" else 20000)

def title(pid):
    b, s = SPLIT[pid]
    big = word(b, "big")
    if not s: return big
    small = word(s, "small")
    sh = round(big.height * 0.62)
    small = small.resize((round(small.width * sh / small.height), sh), Image.LANCZOS)
    if small.width > big.width * 1.15:
        f = big.width * 1.15 / small.width
        small = small.resize((round(small.width * f), round(small.height * f)), Image.LANCZOS)
    ov = round(big.height * 0.35)
    W = max(big.width, small.width); H = big.height + small.height - ov
    t = Image.new("RGBA", (W, H))
    t.alpha_composite(big, ((W - big.width) // 2, 0)); t.alpha_composite(small, ((W - small.width) // 2, big.height - ov))
    return t

def card(pid, frame=0):
    model, shadow = render(M + MODEL.get(pid, pid) + ".json", A, ppu=44, frame=frame, tint=TINT.get(pid))
    img = background()
    bb = model.getbbox()
    k = min(560 / (bb[3] - bb[1]), 640 / (bb[2] - bb[0]))
    model = model.resize((round(model.width * k), round(model.height * k)), Image.LANCZOS)
    shadow = shadow.resize(model.size, Image.LANCZOS)
    bb = model.getbbox()
    xy = (round(S / 2 - (bb[0] + bb[2]) / 2), round(660 - bb[3]))
    sh = Image.new("RGBA", model.size, SHADOW + (0,)); sh.putalpha(shadow.point(lambda v: int(v * SHADOW_A)))
    img.alpha_composite(sh, xy); img.alpha_composite(model, xy)
    t = title(pid)
    th = 250 if SPLIT[pid][1] else 170
    tw = min(900, round(t.width * th / t.height))
    t = t.resize((tw, round(t.height * tw / t.width)), Image.LANCZOS)
    img.alpha_composite(t, ((S - tw) // 2, S - t.height - 44))
    return img.convert("RGB")

def gif(pid, path):
    cache = {}
    for f, _ in ANIM:
        if f not in cache: cache[f] = card(pid, f)
    frames = [cache[f] for f, _ in ANIM]; ms = [ticks * 50 for _, ticks in ANIM]
    strip = Image.new("RGB", (S, S * len(cache)))
    for i, f in enumerate(cache.values()): strip.paste(f, (0, S * i))
    pal = strip.quantize(colors=256, method=Image.Quantize.MEDIANCUT)
    g = [f.quantize(palette=pal, dither=Image.Dither.FLOYDSTEINBERG) for f in frames]
    base_rgb, base_idx = np.array(frames[0]).astype(int), np.array(g[0])
    for i in range(1, len(g)):
        same = np.abs(np.array(frames[i]).astype(int) - base_rgb).sum(2) == 0
        idx = np.array(g[i]); idx[same] = base_idx[same]
        im = Image.fromarray(idx, "P"); im.putpalette(g[0].getpalette()); g[i] = im
    g[0].save(path, save_all=True, append_images=g[1:], duration=ms, loop=0, optimize=False, disposal=1)

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    only = sys.argv[1:]
    for i, pid in enumerate(ORDER, 1):
        if only and pid not in only: continue
        base = f"{OUT}/rosewick-garden-{i:02d}-{pid.replace('_', '-')}"
        card(pid).save(base + ".png")
        if pid == "stake_lantern": gif(pid, base + ".gif")
        print(base)
