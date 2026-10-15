"""Halloween Festival piece cards: one Hibiscus-style icon per piece, on the same dusky-plum floor and
warm light bands as the store icon, hard sun shadow, the piece's name in Minecraft Title Generator lettering
(main word in the pumpkin gradient, second word in small lilac type). Animated pieces also get a GIF."""
import importlib, json, os, sys
import numpy as np
from PIL import Image
sys.path.insert(0, "/home/claude/hfship/hollowmere/src")
sys.path.insert(0, "/home/claude/hfship/thumb")
import pieces_render as PR
import compose as C
import configs

T = "/home/claude/hfship/titles"
OUT = "/home/claude/hfship/cards"
S = 1024
SPLIT = json.load(open("/home/claude/hfship/split.json"))
MODELS = {}
for mod in "hero3 harvest witchy graveyard critters market".split():
    for m in importlib.import_module(mod).all_models():
        MODELS[m.name] = m

def title(pid):
    big = C.clean(Image.open(f"{T}/{pid}_big.png"))
    if not os.path.exists(f"{T}/{pid}_small.png"):
        return big
    small = C.clean(Image.open(f"{T}/{pid}_small.png"), 20000)
    sh = round(big.height * 0.62)                       # second word in small type, same letter height on every card
    small = small.resize((round(small.width * sh / small.height), sh), Image.LANCZOS)
    if small.width > big.width * 1.15:
        f = big.width * 1.15 / small.width
        small = small.resize((round(small.width * f), round(small.height * f)), Image.LANCZOS)
    ov = round(big.height * 0.35)
    W = max(big.width, small.width); H = big.height + small.height - ov
    t = Image.new("RGBA", (W, H))
    t.alpha_composite(big, ((W - big.width) // 2, 0))
    t.alpha_composite(small, ((W - small.width) // 2, big.height - ov))
    return t

def card(pid, frame=0, cache={}):
    spec = configs.SPEC[pid]
    mname = spec["toggle"] or spec["model"] or pid
    m = MODELS[mname]
    key = (pid, frame)
    model, shadow = PR.render_piece(m, frame=frame)
    img = C.background()
    bb = model.getbbox()
    k = min(560 / (bb[3] - bb[1]), 640 / (bb[2] - bb[0]))   # piece fills the top of the card
    if pid not in cache:
        cache[pid] = k
    k = cache[pid]
    model = model.resize((round(model.width * k), round(model.height * k)), Image.LANCZOS)
    shadow = shadow.resize(model.size, Image.LANCZOS)
    bb = model.getbbox()
    xy = (round(S / 2 - (bb[0] + bb[2]) / 2), round(660 - bb[3]))
    if spec["place"] not in ("wall", "roof"):                # nothing floating or wall-hung throws a floor shadow
        sh = Image.new("RGBA", model.size, C.SHADOW + (0,))
        sh.putalpha(shadow.point(lambda v: int(v * C.SHADOW_A)))
        img.alpha_composite(sh, xy)
    img.alpha_composite(model, xy)
    t = title(pid)
    th = 250 if os.path.exists(f"{T}/{pid}_small.png") else 170
    tw = min(900, round(t.width * th / t.height))
    t = t.resize((tw, round(t.height * tw / t.width)), Image.LANCZOS)
    img.alpha_composite(t, ((S - tw) // 2, S - t.height - 44))
    return img.convert("RGB")

def gif(pid, path):
    mname = configs.SPEC[pid]["toggle"] or pid
    frames = [card(pid, k) for k in range(len(C.FRAMES_MS))]
    strip = Image.new("RGB", (S, S * len(frames)))
    for i, f in enumerate(frames):
        strip.paste(f, (0, S * i))
    pal = strip.quantize(colors=256, method=Image.Quantize.MEDIANCUT)
    g = [f.quantize(palette=pal, dither=Image.Dither.FLOYDSTEINBERG) for f in frames]
    base_rgb, base_idx = np.array(frames[0]).astype(int), np.array(g[0])
    for i in range(1, len(g)):                               # unchanged pixels keep frame 0's index: no shimmer
        same = np.abs(np.array(frames[i]).astype(int) - base_rgb).sum(2) == 0
        idx = np.array(g[i]); idx[same] = base_idx[same]
        im = Image.fromarray(idx, "P"); im.putpalette(g[0].getpalette()); g[i] = im
    g[0].save(path, save_all=True, append_images=g[1:], duration=C.FRAMES_MS, loop=0, optimize=False, disposal=1)

if __name__ == "__main__":
    only = sys.argv[1:]
    for i, pid in enumerate(configs.SPEC, 1):
        if only and pid not in only:
            continue
        base = f"{OUT}/halloween-festival-{i:02d}-{pid.replace('_', '-')}"
        card(pid).save(base + ".png")
        m = MODELS[configs.SPEC[pid]["toggle"] or pid]
        if m.is_animated():
            gif(pid, base + ".gif")
        print(base, "animated" if m.is_animated() else "")
