"""Previews of Witching Hour on the Zinguin skin."""
import copy, os, sys
import numpy as np
from PIL import Image
from engine import P
from player import player
from pieces import PIECES

HERE = os.path.dirname(os.path.abspath(__file__))
BG = (24, 22, 44)


def body(bust=False):
    m = player(os.path.join(HERE, "zinguin.png"), slim=True)
    if bust:
        m.elements = m.elements[:m.bust_n]
    return m


def placed(m, anchor_px, target_px, sc=1.0):
    """Copy of a model, scaled by sc about the model centre, moved so anchor lands on target."""
    c = copy.copy(m)
    c.elements = copy.deepcopy(m.elements)
    c.scale = sc
    a = np.array(anchor_px, float) * P
    t = np.array(target_px, float) * P
    shift = (t - 8) / sc + 8 - a
    for e in c.elements:
        e["from"] = list(np.array(e["from"]) + shift)
        e["to"] = list(np.array(e["to"]) + shift)
        if "rotation" in e:
            e["rotation"] = dict(e["rotation"], origin=list(np.array(e["rotation"]["origin"]) + shift))
    return c


def worn(key, slot, m):
    """(model, dy) render extras, positioned the way the slot shows it."""
    if slot == "HELMET":
        return [(m, 0)]
    if slot == "BACKPACK":
        return [(m, -16)]
    if slot == "BALLOON":
        return [(placed(m, (5, 5, 5), (17.5, 13.0, 9.5), 0.85), 0)]
    if slot == "OFFHAND":
        # same as the model's thirdperson display: centre at the fist, then (side, forward, up)
        h = m.display()["thirdperson_lefthand"]
        tx, tf, tu = h["translation"]
        fist = np.array((-1.0, -11.0, 3.0))
        target = fist + np.array((-tx, tu, -tf)) / 1.0
        return [(placed(m, (5, 5, 5), tuple(target), 1.6 * h["scale"][0]), 0)]
    return [(m, 0)]


def bg(im):
    b = Image.new("RGBA", im.size, BG + (255,)); b.alpha_composite(im); return b


VIEWS = [(-0.6, 0.25, -1.0), (0.0, 0.1, -1.0), (0.6, 0.3, 1.0)]

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "preview")
    os.makedirs(out, exist_ok=True)
    only = sys.argv[2:]
    for key, title, slot, lore, mk in PIECES:
        if only and key not in only:
            continue
        m = mk()
        tiles = [bg(body().render(ppu=9, cam=c, frame=1, extra=worn(key, slot, m))) for c in VIEWS]
        tiles.append(bg(m.render(ppu=26, cam=(-0.6, 0.35, -1.0), frame=1)))
        W = sum(t.width for t in tiles) + 20 * (len(tiles) + 1)
        H = max(t.height for t in tiles) + 40
        sheet = Image.new("RGBA", (W, H), BG + (255,))
        x = 20
        for t in tiles:
            sheet.alpha_composite(t, (x, 20 + (H - 40 - t.height) // 2)); x += t.width + 20
        sheet.save(os.path.join(out, f"{key}.png"))
        print("ok", key)
