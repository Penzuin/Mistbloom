"""Moonlit Ballroom starter set: Nexo config, resource pack, Blockbench-free release ZIP and listing media."""
import copy, glob, json, math, os, random, re, shutil, zipfile
import numpy as np
import yaml
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import pieces as P
from engine import NS, Model, NFRAMES, FRAMETIMES, wood

VERSION = "1.1"
NAMEC, TAGC, GOLDC = "#c9b8f0", "#9fb3d9", "#f2c97d"


def S(name, lore, **kw):
    d = dict(name=name, lore=lore, barriers=None, interaction=(1, 1), seats=None, light=None, toggle=None,
             click=None, place="floor", sound="wood")
    d.update(kw)
    return d


SPEC = {
    "waltzing_ghosts": S("Waltzing Ghosts", ["A friendly ghost couple who never", "stop waltzing."],
        interaction=(1.4, 1.8), light=((0, 0, 0), 8),
        click=("minecraft:block.amethyst_block.chime", 1.2, "The ghosts keep on dancing.")),
    "ghost_piano": S("Ghost Pianist", ["An upright piano with a cheerful", "ghost at the keys."],
        barriers=[(0, 0, 0), (-1, 0, 0), (0, 1, 0), (-1, 1, 0)], light=((0, 2, 0), 6),
        click=("minecraft:block.note_block.harp", 0.8, "A soft waltz drifts through the hall.")),
    "floating_candelabra": S("Floating Candelabra", ["Three moonfire candles held up", "by a curl of ghost mist.", "Right-click to light or snuff."],
        interaction=(0.6, 1.5), light=((0, 1, 0), 13), toggle="floating_candelabra_lit", sound="metal", place="any"),
    "ghost_lantern": S("Ghost Lantern", ["A little ghost living in a lantern.", "Right-click to wake its glow."],
        interaction=(0.5, 0.9), light=((0, 0, 0), 12), toggle="ghost_lantern_lit", sound="metal", place="any"),
    "ghost_portrait": S("Portrait of Lady Wispwell", ["She was the life of every ball.", "Candlelight dances across the canvas."],
        interaction=(1, 1.6), place="wall",
        click=("minecraft:entity.allay.ambient_without_item", 1.0, "Lady Wispwell gives you a gracious nod.")),
    "wisp": S("Wisp", ["A little ghost who follows the music."],
        interaction=(0.6, 0.9), light=((0, 0, 0), 6), place="any", sound="wool",
        click=("minecraft:entity.allay.item_given", 1.2, "The wisp does a happy little twirl.")),
}

SOUNDS = {"wood": "block.wood", "metal": "block.lantern", "wool": "block.wool", "stone": "block.stone"}


def _off(t):
    return ",".join(str(v) for v in t)


def nexo_yaml():
    out = {}
    for iid, s in SPEC.items():
        f = {"restricted_rotation": "VERY_STRICT", "preview_placement": True,
             "block_sounds": {f"{k}_sound": f"{SOUNDS[s['sound']]}.{k}" for k in ("place", "break", "hit", "step", "fall")}}
        if s["place"] != "any":
            f["limited_placing"] = {"floor": s["place"] == "floor", "wall": s["place"] == "wall", "roof": s["place"] == "roof"}
        f["hitbox"] = {"barriers": [_off(b) for b in s["barriers"]]} if s["barriers"] else \
                      {"interactions": [f"0,0,0 {s['interaction'][0]},{s['interaction'][1]}"]}   # Nexo key is `interactions` (a list)
        if s["light"]:
            l = {"toggleable": bool(s["toggle"])}
            if s["toggle"]:
                l["toggled_item_model"] = f"{NS}:{s['toggle']}"
            l["lights"] = [f"{_off(s['light'][0])} {s['light'][1]}"]
            f["lights"] = l
        if s["click"]:
            snd, pitch, msg = s["click"]
            f["clickActions"] = [{"conditions": [], "actions": [
                f"{{source=BLOCKS volume=0.6 pitch={pitch}}} [sound] {snd}"]}]
        out[f"{NS}_{iid}"] = {
            "itemname": f"<{NAMEC}>{s['name']}",
            "lore": [f"<gray>{l}" for l in s["lore"]] + [f"<{TAGC}>Moonlit Ballroom"],
            "material": "PAPER",
            "Components": {"item_model": f"{NS}:{iid}"},
            "Mechanics": {"furniture": f},
        }
    head = (f"# Moonlit Ballroom v{VERSION} by Mistbloom Studios - Nexo\n"
            "# Minecraft 1.21.4+.\n\n")
    txt = yaml.safe_dump(out, sort_keys=False, allow_unicode=True, width=200)
    return head + re.sub(rf"\n({NS}_)", r"\n\n\1", txt)


README = """Moonlit Ballroom - Mistbloom Studios
==================================================

Friendly animated ghosts for your Halloween builds made in Nexo

INSTALL - Drag and Drop (Nexo)
--------------
1. Copy Nexo/items/moonball.yml into plugins/Nexo/items/
2. Copy the Nexo/pack/assets/ folder into plugins/Nexo/pack/assets/
3. Run /nexo reload all, then /nexo inventory to grab the pieces.

Requires Minecraft 1.21.4 or newer
"""

LICENSE = """Moonlit Ballroom - Mistbloom Studios
License: use on ONE server network you own or operate. You may edit the files for your own server.
You may not resell, redistribute, share or claim these assets (original or edited) as your own.
"""


def package():
    ROOT, STAGE = "dist", "stage"
    shutil.rmtree(ROOT, ignore_errors=True); shutil.rmtree(STAGE, ignore_errors=True)
    models = P.all_models()
    for m in models:
        m.check(); m.export(STAGE)
    shutil.copytree(os.path.join(STAGE, "assets"), f"{ROOT}/Nexo/pack/assets")
    os.makedirs(f"{ROOT}/Nexo/items")
    open(f"{ROOT}/Nexo/items/{NS}.yml", "w").write(nexo_yaml())
    open(f"{ROOT}/README.txt", "w", newline="\r\n").write(README)   # plain text, Windows line endings for Notepad
    open(f"{ROOT}/LICENSE.txt", "w", newline="\r\n").write(LICENSE)
    names = {m.name for m in models}
    txt = open(f"{ROOT}/Nexo/items/{NS}.yml").read()
    yaml.safe_load(txt)
    for ref in re.findall(rf"{NS}:([a-z_]+)", txt):
        assert ref in names, ref
    for m in models:
        t = f"{ROOT}/Nexo/pack/assets/{NS}/textures/furniture/{m.name}.png"
        assert os.path.exists(t) and (not m.is_animated() or os.path.exists(t + ".mcmeta")), t
    z = f"Moonlit-Ballroom-Starter-v{VERSION}.zip"
    with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in sorted(glob.glob(f"{ROOT}/**/*", recursive=True)):
            if os.path.isfile(p):
                zf.write(p, os.path.join("Moonlit-Ballroom", os.path.relpath(p, ROOT)))
    print(len(models), "models,", len(SPEC), "items ->", z, os.path.getsize(z) // 1024, "KB")
    return z


# ------------------------------------------------------------------ media
NIGHT, PETAL, MIST, GOLD, PARCH = (20, 18, 44), (201, 184, 240), (159, 179, 217), (242, 201, 125), (246, 241, 231)

def font(size, bold=True):
    for p in ("/usr/share/fonts/truetype/google-fonts/Lora-Variable.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"):
        if os.path.exists(p):
            f = ImageFont.truetype(p, size)
            try:
                f.set_variation_by_name("Bold")
            except Exception:
                pass
            return f
    return ImageFont.load_default()

def sans(size):
    for p in ("/usr/share/fonts/truetype/google-fonts/Poppins-Medium.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def night_bg(W, H, seed=3, moon=False):
    y = np.linspace(0, 1, H)[:, None]
    top, bot = np.array(NIGHT, float), np.array([48, 36, 86], float)
    g = (top * (1 - y) + bot * y)[:, None, :].repeat(W, 1).reshape(H, W, 3)
    img = Image.fromarray(g.astype(np.uint8)).convert("RGBA")
    d = ImageDraw.Draw(img)
    rng = random.Random(seed)
    for _ in range(int(W * H / 3500)):
        x, yy = rng.randrange(W), rng.randrange(int(H * 0.7))
        r = rng.choice([1, 1, 2])
        d.ellipse([x - r, yy - r, x + r, yy + r], fill=(236, 230, 255, rng.randrange(70, 200)))
    # big soft moon
    if moon:
        mo = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        md = ImageDraw.Draw(mo)
        r = H * 0.09
        cx, cy = W * 0.88, H * 0.42
        md.ellipse([cx - r * 1.8, cy - r * 1.8, cx + r * 1.8, cy + r * 1.8], fill=(255, 246, 220, 40))
        img.alpha_composite(mo.filter(ImageFilter.GaussianBlur(30)))
        md = ImageDraw.Draw(img)
        md.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 246, 222, 255))
        md.ellipse([cx - r * 0.55, cy - r * 0.4, cx - r * 0.25, cy - r * 0.1], fill=(240, 228, 200, 255))
        md.ellipse([cx + r * 0.2, cy + r * 0.25, cx + r * 0.45, cy + r * 0.5], fill=(240, 228, 200, 255))
    return img

def place(scene, m, dx, dz, dy=0):
    for e in m.elements:
        e = copy.deepcopy(e)
        e["from"] = [e["from"][0] + dx, e["from"][1] + dy, e["from"][2] + dz]
        e["to"] = [e["to"][0] + dx, e["to"][1] + dy, e["to"][2] + dz]
        if "rotation" in e:
            o = e["rotation"]["origin"]
            e["rotation"]["origin"] = [o[0] + dx, o[1] + dy, o[2] + dz]
        scene.elements.append(e)

def shadowed(base, im, xy):
    a = im.split()[3]
    sh = Image.new("RGBA", im.size, (6, 6, 20, 0)); sh.putalpha(a.point(lambda v: 110 if v else 0))
    base.alpha_composite(sh.filter(ImageFilter.GaussianBlur(7)), (xy[0] + 10, xy[1] + 12))
    base.alpha_composite(im, xy)

def fit(im, w, h):
    s = min(w / im.width, h / im.height)
    return im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.NEAREST)

def centered(d, text, f, y, W, fill):
    tw = d.textlength(text, font=f)
    d.text(((W - tw) / 2 + 3, y + 3), text, font=f, fill=(8, 6, 24))
    d.text(((W - tw) / 2, y), text, font=f, fill=fill)

def ballroom(frame):
    sc = Model("scene")
    sc.box([-20, -2, -24], [92, 0, 44], wood("ebony", plank=4, base=2))
    sc.box([-20, 0, 44], [92, 40, 46], wood("rosewood", plank=4, base=3))
    place(sc, P.ghost_piano(), -16, 26)
    place(sc, P.ghost_portrait(), 24, 28, 14)
    place(sc, P.ghost_portrait(), 44, 28, 14)
    place(sc, P.floating_candelabra(True), 18, 30)
    place(sc, P.floating_candelabra(True), 64, 30)
    place(sc, P.waltzing_ghosts(), 30, 2)
    place(sc, P.ghost_lantern(True), 70, 0)
    place(sc, P.wisp(), 6, -8)
    return sc.render(ppu=6, frame=frame)

def cover(frame=0, W=1920, H=1080):
    bg = night_bg(W, H, moon=True)
    im = fit(ballroom(frame), W - 200, H - 300)
    shadowed(bg, im, ((W - im.width) // 2, H - im.height - 40))
    d = ImageDraw.Draw(bg)
    centered(d, "Moonlit Ballroom", font(104), 40, W, GOLD)
    centered(d, "Friendly waltzing ghosts  ·  6 animated Halloween pieces", sans(32), 180, W, PARCH)
    return bg

LABELS = {"waltzing_ghosts": "Waltzing Ghosts", "ghost_piano": "Ghost Pianist", "floating_candelabra_lit": "Floating Candelabra",
          "ghost_lantern_lit": "Ghost Lantern", "ghost_portrait": "Lady Wispwell's Portrait", "wisp": "Wisp"}

def pieces_sheet(frame=1):
    ms = {m.name: m for m in P.all_models()}
    cw, ch = 400, 430
    W, H = cw * 3 + 80, ch * 2 + 200
    bg = night_bg(W, H, 7)
    d = ImageDraw.Draw(bg)
    centered(d, "What's in the starter set", font(56), 40, W, GOLD)
    f = sans(24)
    for k, n in enumerate(LABELS):
        x, y = 40 + (k % 3) * cw, 150 + (k // 3) * ch
        ov = Image.new("RGBA", bg.size, (0, 0, 0, 0))
        ImageDraw.Draw(ov).rounded_rectangle([x + 10, y, x + cw - 10, y + ch - 20], 22, fill=(201, 184, 240, 18), outline=GOLD + (90,), width=2)
        bg.alpha_composite(ov)
        im = fit(ms[n].render(ppu=14, frame=frame), cw - 70, ch - 110)
        shadowed(bg, im, (x + (cw - im.width) // 2, y + 20 + (ch - 110 - im.height) // 2))
        tw = d.textlength(LABELS[n], font=f)
        d.text((x + (cw - tw) / 2, y + ch - 70), LABELS[n], font=f, fill=PARCH)
    return bg

def waltz_gif(out):
    frames = []
    for k in range(NFRAMES):
        sc = Model("gif")
        sc.box([-10, -2, -8], [44, 0, 26], wood("ebony", plank=4, base=2))
        place(sc, P.waltzing_ghosts(), 0, 2)
        place(sc, P.wisp(), 24, -4)
        im = fit(sc.render(ppu=12, frame=k), 820, 520)
        bg = night_bg(900, 600, 9)
        shadowed(bg, im, ((900 - im.width) // 2, 600 - im.height - 30))
        frames.append(bg.convert("RGB").quantize(colors=255, method=Image.MEDIANCUT))
    frames[0].save(out, save_all=True, append_images=frames[1:], duration=[t * 50 for t in FRAMETIMES], loop=0)

if __name__ == "__main__":
    import sys
    if "media" not in sys.argv:
        z = package()
    os.makedirs("media", exist_ok=True)
    cover().convert("RGB").save("media/moonlit-ballroom-cover.png")
    pieces_sheet().convert("RGB").save("media/moonlit-ballroom-pieces.png")
    waltz_gif("media/moonlit-ballroom-waltz.gif")
    print("media ok")
