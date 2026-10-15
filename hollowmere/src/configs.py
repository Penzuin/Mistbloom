"""Hollowmere item table -> Nexo item config."""
import re
import yaml

NS = "hollowmere"
INK = "#ffb15c"          # pumpkin orange for item names


def S(name, lore, **kw):
    d = dict(name=name, lore=lore if isinstance(lore, list) else [lore], model=None, tall=False, barriers=None,
             interaction=(1, 1), seats=None, light=None, toggle=None, states=None, storage=None,
             click=None, place="floor", sound="wood", dye=None)
    d.update(kw)
    return d


SPEC = {
    # centrepieces
    "jack_o_lantern": S("Jack-o'-Lantern", ["A big carved pumpkin.", "Right-click to light the candle."],
        barriers=[(0, 0, 0)], light=((0, 1, 0), 14), toggle="jack_o_lantern_lit", place="any"),
    "cauldron": S("Witch's Cauldron", ["An iron pot of bubbling brew.", "Right-click to light the fire."],
        barriers=[(0, 0, 0)], light=((0, 1, 0), 12), toggle="cauldron_lit", sound="metal",
        click=("minecraft:block.brewing_stand.brew", 0.8, "The brew bubbles and hisses...")),
    "scarecrow": S("Scarecrow", ["A patched scarecrow with a crow friend.", "Three blocks tall."],
        tall=True, barriers=[(0, 0, 0), (0, 1, 0), (0, 2, 0)],
        click=("minecraft:entity.parrot.imitate.ravager", 1.4, "Caw!")),
    "pumpkin_lamp": S("Pumpkin Lamp Post", ["A street lamp with a hanging jack-o'-lantern.", "Right-click to switch it on or off."],
        tall=True, barriers=[(0, 0, 0), (0, 1, 0), (0, 2, 0)], light=((0, 3, 0), 15), toggle="pumpkin_lamp_lit",
        sound="metal"),
    "potion_stall": S("Potion Stall", ["A 3-wide market stall for brews and charms.", "Sneak + right-click to change the awning."],
        tall=True, barriers=[(-1, 0, 0), (0, 0, 0), (1, 0, 0)], light=((0, 1, 0), 10),
        states=[("plum_awning", "potion_stall"), ("moss_awning", "potion_stall_moss"),
                ("pumpkin_awning", "potion_stall_ember")]),
    "hollow_arch": S("Halloween Arch", ["A gnarled entrance arch with a hanging sign.", "Three wide, three tall."],
        tall=True, barriers=[(-1, 0, 0), (-1, 1, 0), (-1, 2, 0), (1, 0, 0), (1, 1, 0), (1, 2, 0)],
        light=((0, 2, 0), 13)),
    "dead_tree": S("Lantern Tree", ["A spooky old tree hung with jack-o'-lanterns."],
        barriers=[(0, 0, 0), (0, 1, 0)], light=((0, 2, 0), 12)),

    # harvest
    "pumpkin_pile": S("Pumpkin Pile", ["A heap of pumpkins in every size."], barriers=[(0, 0, 0)]),
    "gourd_basket": S("Gourd Basket", ["A wicker basket of autumn gourds."], interaction=(0.75, 0.75), place="any"),
    "hay_bale_seat": S("Hay Bale Seat", ["A hay bale with a plaid blanket.", "Sit down and rest."],
        barriers=[(0, 0, 0)], seats=[(0, -0.08, 0)], sound="grass"),      # blanket top at 8.4px
    "haystack": S("Haystack", ["A big pile of hay with a pitchfork."], tall=True, barriers=[(0, 0, 0), (0, 1, 0)], sound="grass"),
    "pumpkin_cart": S("Pumpkin Cart", ["A wooden hand cart full of pumpkins."], barriers=[(0, 0, 0), (1, 0, 0)]),
    "caramel_apple_tray": S("Caramel Apple Tray", ["Sticky caramel apples on a tray."], interaction=(0.85, 0.5), place="any",
        click=("minecraft:entity.generic.eat", 1.2, "Sweet, sticky and crunchy.")),
    "cider_cask": S("Cider Cask", ["A barrel of hot apple cider.", "Right-click to pour a cup."], barriers=[(0, 0, 0)],
        click=("minecraft:item.bottle.fill", 1.0, "You pour a cup of hot apple cider.")),
    "candy_bucket": S("Trick-or-Treat Bucket", ["A jack-o'-lantern bucket full of sweets.", "Right-click to open (9 slots)."],
        interaction=(0.9, 0.8), place="any", storage=(1, "Trick-or-Treat Bucket")),

    # witchy
    "spellbook_lectern": S("Spellbook Lectern", ["An open book of spells on a carved stand."], barriers=[(0, 0, 0)],
        light=((0, 1, 0), 8), click=("minecraft:item.book.page_turn", 1.0, "The pages turn on their own...")),
    "crystal_ball": S("Crystal Ball", ["A swirling orb on a brass stand."], interaction=(0.65, 0.65), place="any",
        light=((0, 0, 0), 9), sound="glass",
        click=("minecraft:block.amethyst_block.chime", 0.9, "You see... more candy in your future.")),
    "potion_shelf": S("Potion Shelf", ["A wall shelf of bottles and jars.", "Place it on a wall. Right-click to open (18 slots)."],
        interaction=(1, 1), place="wall", storage=(2, "Potion Shelf"), sound="glass"),
    "potion_trio": S("Potion Trio", ["Three brews for your counter."], interaction=(0.75, 0.55), place="any", sound="glass",
        light=((0, 0, 0), 6)),
    "witch_broom": S("Witch's Broom", ["A broom leaning against the wall."], tall=True, interaction=(0.75, 2.2)),
    "witch_hat_stand": S("Witch Hat Stand", ["A pointy hat on a stand.", "Dyeable hat."], barriers=[(0, 0, 0)], dye=(110, 70, 160)),
    "candle_cluster": S("Candle Cluster", ["A puddle of candles in a cosy group."], interaction=(0.65, 0.75), place="any",
        light=((0, 0, 0), 12)),

    # graveyard
    "tombstone": S("Tombstone", ["A mossy headstone with a candle and a pumpkin."], barriers=[(0, 0, 0)], sound="stone",
        light=((0, 1, 0), 8)),
    "tombstone_cross": S("Cross Tombstone", ["A stone cross with ivy and flowers."], barriers=[(0, 0, 0)], sound="stone"),
    "iron_fence": S("Graveyard Fence", ["A spiked iron fence panel."], barriers=[(0, 0, 0)], sound="metal"),
    "coffin": S("Coffin", ["A lidded coffin with a pumpkin on top.", "Right-click to open (27 slots)."],
        barriers=[(0, 0, 0), (1, 0, 0)], storage=(3, "Coffin")),
    "ghost_lantern": S("Ghost Lantern", ["A little ghost trapped in a lantern.", "Right-click to switch it on or off."],
        interaction=(0.45, 0.9), place="any", light=((0, 0, 0), 13), toggle="ghost_lantern_lit", sound="metal"),
    "mushroom_ring": S("Glowshroom Ring", ["A fairy ring of glowing mushrooms."], interaction=(0.9, 0.4), light=((0, 0, 0), 7),
        sound="grass"),

    # critters and decor
    "black_cat": S("Black Cat", ["A cat with a bell collar.", "Dyeable fur."], interaction=(0.65, 0.95), place="any",
        dye=(58, 52, 72), click=("minecraft:entity.cat.purr", 1.0, "Purrrr...")),
    "owl_perch": S("Owl Perch", ["A sleepy-eyed owl on its perch."], barriers=[(0, 0, 0), (0, 1, 0)],
        click=("minecraft:entity.parrot.ambient", 0.6, "Hoo!")),
    "crow_post": S("Crow Post", ["A crow perched on a post."], barriers=[(0, 0, 0)],
        click=("minecraft:entity.parrot.imitate.ravager", 1.4, "Caw! Caw!")),
    "cobweb_corner": S("Corner Cobweb", ["A dusty web for a corner.", "Place it on a wall."], interaction=(1, 1), place="wall"),
    "hanging_spider": S("Hanging Spider", ["A friendly spider on a silk thread.", "Hangs from a ceiling."],
        interaction=(0.6, 0.85), place="roof"),
    "skull_candle": S("Skull Candle", ["A melting candle on a skull."], interaction=(0.65, 1.05), place="any", sound="stone",
        light=((0, 0, 0), 12)),
    "cushion_stool": S("Cushion Stool", ["A tufted stool with tassels.", "Dyeable cushion."], barriers=[(0, 0, 0)],
        seats=[(0, 0.16, 0)], dye=(150, 72, 170)),                                      # cushion top at ~12px
    "bat_bunting": S("Bat Bunting", ["A 3-wide string of pennants and bats.", "Dyeable pennants."],
        interaction=[((-1, 0.25, 0), 1, 0.75), ((0, 0.25, 0), 1, 0.75), ((1, 0.25, 0), 1, 0.75)],
        place="any", dye=(235, 120, 40)),
    "welcome_sign": S("Welcome Signpost", ["A signpost pointing to candy and spooks."], tall=True,
        barriers=[(0, 0, 0), (0, 1, 0), (0, 2, 0)], light=((0, 3, 0), 10)),
    "harvest_wreath": S("Harvest Wreath", ["An autumn leaf wreath with a bow.", "Place it on a wall."], interaction=(0.9, 0.9),
        place="wall", sound="grass"),
}

SOUNDS = {"wood": "block.wood", "metal": "block.lantern", "stone": "block.stone", "glass": "block.glass",
          "grass": "block.grass"}


def _off(t):
    return ",".join(str(v) for v in t)


def nexo():
    out = {}
    for iid, s in SPEC.items():
        f = {"restricted_rotation": "VERY_STRICT", "preview_placement": True,
             "block_sounds": {f"{k}_sound": f"{SOUNDS[s['sound']]}.{k}" for k in ("place", "break", "hit", "step", "fall")}}
        if s["tall"]:
            f["properties"] = {"translation": "0,1,0"}
        if s["place"] != "any":
            f["limited_placing"] = {"floor": s["place"] == "floor", "wall": s["place"] == "wall", "roof": s["place"] == "roof"}
        if s["barriers"]:
            f["hitbox"] = {"barriers": [_off(b) for b in s["barriers"]]}
        else:                                            # Nexo key is `interactions`: a list of "x,y,z width,height"
            boxes = s["interaction"] if isinstance(s["interaction"], list) else [((0, 0, 0),) + tuple(s["interaction"])]
            f["hitbox"] = {"interactions": [f"{_off(o)} {w},{h}" for (o, w, h) in boxes]}
        if s["seats"]:
            f["seats"] = [_off(x) for x in s["seats"]]
        if s["light"]:
            l = {"toggleable": bool(s["toggle"])}
            if s["toggle"]:
                l["toggled_item_model"] = f"{NS}:{s['toggle']}"
            l["lights"] = [f"{_off(s['light'][0])} {s['light'][1]}"]
            f["lights"] = l
        if s["states"]:
            f["states"] = {"condition": "isSneaking()"}
            for name, model in s["states"]:
                f["states"][name] = {"type": "ITEM_MODEL", "item_model": f"{NS}:{model}"}
        if s["storage"]:
            f["storage"] = {"type": "STORAGE", "rows": s["storage"][0], "title": f"<{INK}>{s['storage'][1]}",
                            "open_sound": "block.barrel.open", "close_sound": "block.barrel.close"}
        if s["click"]:
            snd, pitch, msg = s["click"]
            f["clickActions"] = [{"conditions": [], "actions": [
                f"{{source=BLOCKS volume=0.6 pitch={pitch}}} [sound] {snd}", f"[actionbar] <{INK}>{msg}"]}]
        item = {"itemname": f"<{INK}>{s['name']}", "lore": [f"<gray>{l}" for l in s["lore"]] + ["<dark_gray>Halloween"],
                "material": "LEATHER_HORSE_ARMOR" if s["dye"] else "PAPER"}
        if s["dye"]:
            item["color"] = ",".join(map(str, s["dye"]))
        item["Components"] = {"item_model": f"{NS}:{iid}"}
        item["Mechanics"] = {"furniture": f}
        out[f"{NS}_{iid}"] = item
    head = ("# Halloween market set by Mistbloom Studios\n"
            "# Nexo 1.28+ (furniture states, light lists and click actions).\n"
            "# Dyeable pieces: dye them like leather in a crafting table before placing, or change `color`.\n\n")
    txt = yaml.safe_dump(out, sort_keys=False, allow_unicode=True, width=200)
    return head + re.sub(r"\n(hollowmere_)", r"\n\n\1", txt)
