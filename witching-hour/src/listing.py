"""Store listing images for Witching Hour (Mistbloom style), all on the Zinguin skin."""
import math, os, random, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from preview import body, worn
from pieces import PIECES

OUT = "listing"
os.makedirs(OUT, exist_ok=True)
GF = "/usr/share/fonts/truetype/google-fonts/"
NIGHT, BLOOM, PETAL, GOLD, PARCH = (20, 26, 51), (78, 62, 154), (201, 184, 240), (242, 201, 125), (246, 241, 231)
EMBER = (255, 184, 77)
BY = {k: (k, t, s, l, mk) for k, t, s, l, mk in PIECES}
CHIPS = {
    "witch_hat": ["Glowing moon pin", "Twinkling star charm", "Wide brim"],
    "candle_crown": ["5 flickering candles", "Amethyst studs"],
    "ghostlight_lantern": ["Glowing ghost", "Hangs from your hand"],
    "grimoire": ["Glowing moon clasp", "Ribbon bookmark"],
    "wisp": ["Floats beside you", "No ModelEngine needed"],
    "moonlit_broom": ["Glowing lantern", "Ribbon bow"],
}
SLOT = {"HELMET": "Hat", "BACKPACK": "Back", "OFFHAND": "Off-hand", "BALLOON": "Balloon"}


def font(name, size, wght=None):
    f = ImageFont.truetype(GF + name, size)
    if wght:
        try:
            f.set_variation_by_axes([wght])
        except Exception:
            pass
    return f


def sky(W, H, seed=7):
    im = Image.new("RGBA", (W, H), NIGHT + (255,))
    g = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(g)
    d.ellipse((W * 0.18, H * 0.25, W * 0.82, H * 1.2), fill=BLOOM + (110,))
    d.ellipse((W * 0.3, H * 0.75, W * 0.7, H * 1.25), fill=EMBER + (26,))
    im.alpha_composite(g.filter(ImageFilter.GaussianBlur(W // 8)))
    d = ImageDraw.Draw(im); r = random.Random(seed)
    for _ in range(int(W * H / 22000)):
        x, y = r.randrange(W), r.randrange(int(H * 0.85))
        d.point((x, y), fill=(255, 250, 230, r.randrange(60, 200)))
    return im


def shadowed(base, im, pos):
    sh = Image.new("RGBA", base.size, (0, 0, 0, 0))
    blk = Image.new("RGBA", im.size, (8, 6, 20, 0)); blk.putalpha(im.split()[3].point(lambda v: 90 if v else 0))
    sh.alpha_composite(blk, (pos[0] + 10, pos[1] + 12))
    base.alpha_composite(sh.filter(ImageFilter.GaussianBlur(8)))
    base.alpha_composite(im, pos)


def outfit_extras(keys):
    ex = []
    for k in keys:
        key, t, s, l, mk = BY[k]
        ex += worn(key, s, mk())
    return ex


def on_player(keys, cam, ppu, frame=1):
    return body().render(ppu=ppu, cam=cam, frame=frame, extra=outfit_extras(keys))


def fitted(im, w, h):
    s = min(w / im.width, h / im.height, 1.0)
    return im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS) if s < 1 else im


def chip(d, x, y, text, f):
    w = d.textlength(text, font=f) + 28
    d.rounded_rectangle((x, y, x + w, y + 40), radius=20, fill=(46, 40, 92), outline=(110, 96, 180), width=2)
    d.text((x + 14, y + 20), text, font=f, fill=PETAL, anchor="lm")
    return x + w + 12


def footer(d, W, H):
    d.text((W - 40, H - 34), "Witching Hour  |  Mistbloom Studios", font=font("Lora-Italic-Variable.ttf", 26),
           fill=PETAL, anchor="rb")


OUTFIT = ["witch_hat", "moonlit_broom", "ghostlight_lantern", "wisp"]
FRONT, BACK = (-0.6, 0.25, -1.0), (0.6, 0.3, 1.0)


def cover():
    W, H = 1920, 1080
    im = sky(W, H)
    hero = fitted(on_player(OUTFIT, FRONT, 14), 900, 820)
    shadowed(im, hero, ((W - hero.width) // 2, H - hero.height - 30))
    for i, k in enumerate(("candle_crown", "grimoire")):
        side = on_player([k], FRONT if k == "candle_crown" else (-0.4, 0.2, -1.0), 7.5)
        x = 140 if i == 0 else W - 140 - side.width
        shadowed(im, side, (x, H - side.height - 120))
    d = ImageDraw.Draw(im)
    d.text((W // 2, 60), "Witching Hour", font=font("Lora-Variable.ttf", 92, 700), fill=PARCH, anchor="mt")
    d.text((W // 2, 175), "6 WITCHY COSMETICS  |  HMCCOSMETICS  |  WEAR THEM ALL YEAR", font=font("Poppins-Medium.ttf", 24),
           fill=PETAL, anchor="mt")
    d.text((W - 40, 36), "Mistbloom Studios", font=font("Lora-Italic-Variable.ttf", 30), fill=PETAL, anchor="rt")
    return im


def thumbnail():
    S = 1024
    im = sky(S, S, seed=11)
    hero = fitted(on_player(OUTFIT, FRONT, 12), 760, 760)
    shadowed(im, hero, ((S - hero.width) // 2, S - hero.height - 24))
    d = ImageDraw.Draw(im)
    d.text((S // 2, 50), "Witching Hour", font=font("Lora-Variable.ttf", 104, 700), fill=PARCH, anchor="mt")
    d.text((S // 2, 178), "6 witchy cosmetics", font=font("Poppins-Medium.ttf", 36), fill=PETAL, anchor="mt")
    return im


def card(key):
    _, title, slot, lore, mk = BY[key]
    W, H = 1600, 900
    im = sky(W, H, seed=hash(key) % 100)
    cam = BACK if slot == "BACKPACK" else FRONT
    big = fitted(on_player([key], cam, 15), 760, 820)
    shadowed(im, big, (60 + (780 - big.width) // 2, H - big.height - 40))
    solo = mk().render(ppu=22 if slot != "BACKPACK" else 11, cam=(-0.6, 0.35, -1.0) if slot != "BACKPACK" else (0.6, 0.3, 1.0), frame=1)
    solo.thumbnail((420, 380))
    shadowed(im, solo, (1150 - solo.width // 2, 440 + (380 - solo.height) // 2))
    d = ImageDraw.Draw(im)
    d.text((900, 140), title, font=font("Lora-Variable.ttf", 64, 700), fill=PARCH, anchor="lm")
    d.text((902, 215), lore, font=font("Poppins-Medium.ttf", 30), fill=PETAL, anchor="lm")
    x, y = 902, 268
    f = font("Poppins-Medium.ttf", 22)
    for c in [SLOT[slot]] + CHIPS[key]:
        if x + d.textlength(c, font=f) + 28 > W - 40:
            x, y = 902, y + 54
        x = chip(d, x, y, c, f)
    footer(d, W, H)
    return im


def features():
    W, H = 1920, 1080
    im = sky(W, H, seed=21)
    hero = fitted(on_player(["candle_crown", "grimoire", "wisp"], FRONT, 13), 720, 900)
    shadowed(im, hero, (120 + (720 - hero.width) // 2, H - hero.height - 60))
    d = ImageDraw.Draw(im)
    d.text((960, 140), "Not a costume", font=font("Lora-Variable.ttf", 66, 700), fill=PARCH, anchor="lm")
    d.text((962, 210), "Witchy pieces players keep wearing after October.", font=font("Poppins-Medium.ttf", 26),
           fill=PETAL, anchor="lm")
    rows = [
        ("Every slot covered", "2 hats, a back piece, 2 off-hand items and a balloon"),
        ("HMCCosmetics ready", "menu, permissions and one config per plugin"),
        ("Nexo, ItemsAdder or Oraxen", "or no items plugin at all"),
        ("Animated", "flickering candles, glowing ghosts, twinkling charms"),
        ("No ModelEngine needed", "the wisp is a plain item model"),
        ("Light on performance", "14 cubes or fewer per model, Blockbench files included"),
    ]
    y = 285
    for head, sub in rows:
        d.ellipse((962, y + 8, 982, y + 28), fill=GOLD)
        d.text((1004, y), head, font=font("Poppins-Medium.ttf", 32), fill=PARCH)
        d.text((1004, y + 44), sub, font=font("Poppins-Medium.ttf", 23), fill=PETAL)
        y += 112
    footer(d, W, H)
    return im


def spin(name, keys, frames=24, size=520, ppu=6.2, solo=None):
    out = []
    for i in range(frames):
        a = 2 * math.pi * i / frames - 2.6
        cam = (math.sin(a), 0.25, math.cos(a))
        r = (solo.render(ppu=ppu, cam=cam, frame=(i // 2) % 6) if solo is not None
             else body().render(ppu=ppu, cam=cam, frame=(i // 2) % 6, extra=outfit_extras(keys)))
        bg = Image.new("RGB", (size, size), NIGHT)
        g = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        ImageDraw.Draw(g).ellipse((size * .15, size * .2, size * .85, size * .95), fill=BLOOM + (120,))
        g = g.filter(ImageFilter.GaussianBlur(60))
        bg.paste(g, (0, 0), g)
        r.thumbnail((size - 20, size - 20))
        bg.paste(r, ((size - r.width) // 2, (size - r.height) // 2), r)
        out.append(bg.convert("P", palette=Image.ADAPTIVE, colors=160))
    out[0].save(os.path.join(OUT, f"{name}-spin.gif"), save_all=True, append_images=out[1:], duration=90, loop=0, disposal=2)


if __name__ == "__main__":
    which = sys.argv[1:] or ["cover", "cards", "features", "gifs"]
    if "cover" in which:
        cover().convert("RGB").save(os.path.join(OUT, "witching-hour-cover.png"))
        thumbnail().convert("RGB").save(os.path.join(OUT, "witching-hour-thumbnail.png"))
    if "cards" in which:
        for n, (key, *_) in enumerate(PIECES, 1):
            card(key).convert("RGB").save(os.path.join(OUT, f"witching-hour-{n}-{key.replace('_', '-')}.png"))
    if "features" in which:
        features().convert("RGB").save(os.path.join(OUT, "witching-hour-features.png"))
    if "gifs" in which:
        spin("witching-hour-outfit", OUTFIT, ppu=7)
        for key, t, s, l, mk in PIECES:
            spin(key.replace("_", "-"), None, solo=mk(), ppu=26 if s != "BACKPACK" else 12, size=420)
    print("done")
