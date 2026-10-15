"""Config files for Night Wings, written the way you'd write them by hand:
short ids, one-line lore, list items indented, a blank line between entries."""
from engine import NS

PURPLE = "#c9b8ff"

# One short lore line per wing. Keep these plain - players read them in a menu.
LORE = {
    "starfeather_wings": "Soft pearl feathers with gold trim.",
    "duskbat_wings": "Leathery bat wings with a red glow.",
    "frostlight_wings": "Wings made of glowing ice.",
    "bloomfairy_wings": "Shimmery fairy wings.",
    "nightwyrm_wings": "Dragon wings with green veins.",
    "petal_wings": "Night flower petals that softly glow.",
}

_SPECIAL = set(":#{}[],&*!|>'\"%@`")


def _scalar(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    s = str(v)
    needs = (s == "" or s[0] in _SPECIAL or s[0] in "-?" or ": " in s or " #" in s
             or s.lower() in ("yes", "no", "true", "false", "null", "on", "off") or s.strip() != s)
    if needs:
        return "'" + s.replace("'", "''") + "'"
    return s


def yaml(d, indent=0, gap=False):
    """Tiny YAML writer: 2-space indent, list items indented under their key."""
    pad = " " * indent
    out = []
    for i, (k, v) in enumerate(d.items()):
        if gap and i:
            out.append("")
        if isinstance(v, dict):
            out.append(f"{pad}{k}:")
            out.append(yaml(v, indent + 2))
        elif isinstance(v, list):
            if all(not isinstance(x, (dict, list)) for x in v) and len(v) <= 3 and all(isinstance(x, int) for x in v):
                out.append(f"{pad}{k}: [{', '.join(str(x) for x in v)}]")
            else:
                out.append(f"{pad}{k}:")
                for x in v:
                    out.append(f"{pad}  - {_scalar(x)}")
        else:
            out.append(f"{pad}{k}: {_scalar(v)}")
    return "\n".join(out)


def lore(m):
    return [f"<gray>{LORE[m.name]}", "<dark_gray>Back cosmetic" + (", dyeable" if m.dye else "")]


# ------------------------------------------------------------------ items plugins
def nexo_items(entries):
    out = {}
    for m, title, _ in entries:
        it = {"itemname": f"<{PURPLE}>{title}", "lore": lore(m),
              "material": "LEATHER_HORSE_ARMOR" if m.dye else "PAPER"}
        if m.dye:
            it["color"] = ",".join(map(str, m.dye))
        it["Components"] = {"item_model": f"{NS}:{m.name}"}
        out[m.name] = it
    return ("# Night Wings - Nexo items\n"
            "# These are only used by HMCCosmetics, you don't need to give them out.\n\n" + yaml(out, gap=True) + "\n")


def oraxen_items(entries):
    out = {}
    for m, title, _ in entries:
        it = {"itemname": f"<{PURPLE}>{title}", "lore": lore(m),
              "material": "LEATHER_HORSE_ARMOR" if m.dye else "PAPER"}
        if m.dye:
            it["color"] = "#%02x%02x%02x" % m.dye
        it["components"] = {"item_model": f"{NS}:{m.name}"}
        it["Pack"] = {"generate_model": False, "exclude_from_item_model": True}
        out[m.name] = it
    return ("# Night Wings - Oraxen items\n"
            "# These are only used by HMCCosmetics, you don't need to give them out.\n\n" + yaml(out, gap=True) + "\n")


def ia_items(entries):
    items = {}
    for m, title, _ in entries:
        it = {"display_name": f"&d{title}", "lore": [f"&7{LORE[m.name]}", "&8Back cosmetic"],
              "resource": {"material": "LEATHER_HORSE_ARMOR" if m.dye else "PAPER", "generate": False,
                           "model_path": f"cosmetics/{m.name}"}}
        if m.dye:
            it["specific_properties"] = {"leather_horse_armor": {"color": ",".join(map(str, m.dye))}}
        items[m.name] = it
    return ("# Night Wings - ItemsAdder items\n\n" + yaml({"info": {"namespace": NS}}) + "\n\n"
            + "items:\n" + yaml(items, 2, gap=True) + "\n")


# ------------------------------------------------------------------ HMCCosmetics
def hmc_cosmetics(entries, plugin):
    out = {}
    for m, title, _ in entries:
        c = {"slot": "BACKPACK", "permission": f"hmccosmetics.{m.name}"}
        if m.dye:
            c["dyeable"] = True
        item = {}
        if plugin == "none":
            item["material"] = "LEATHER_HORSE_ARMOR" if m.dye else "PAPER"
            item["model-id"] = f"{NS}:{m.name}"
            if m.dye:
                item["color"] = "#%02x%02x%02x" % m.dye
        else:
            item["material"] = {"nexo": f"nexo:{m.name}", "oraxen": f"oraxen:{m.name}",
                                "itemsadder": f"itemsadder:{NS}:{m.name}"}[plugin]
        item.update({"name": f"<{PURPLE}>{title}", "lore": lore(m)})
        c["item"] = item
        out[m.name] = c
    head = "# Night Wings - HMCCosmetics\n"
    if plugin == "none":
        head += "# Uses the resource pack in this folder, no items plugin needed.\n"
    head += "# Permission for each one is hmccosmetics.<id>, e.g. hmccosmetics.starfeather_wings\n\n"
    return head + yaml(out, gap=True) + "\n"


def hmc_menu(entries):
    items = {"title_icon": {
        "slots": [4], "type": "empty",
        "item": {"material": "PHANTOM_MEMBRANE", "name": f"<{PURPLE}><b>Night Wings</b>",
                 "lore": ["<gray>Pick a pair to wear."]}}}
    slots = [19, 20, 21, 23, 24, 25]
    for slot, (m, title, _) in zip(slots, entries):
        items[m.name] = {
            "slots": [slot], "type": "cosmetic", "cosmetic": m.name,
            "item": {"material": f"hmccosmetics:{m.name}",
                     "lore": ["", "<yellow>Click to wear"]},
            "locked-item": {"material": "GRAY_STAINED_GLASS_PANE", "name": f"<gray>{title}",
                            "lore": ["", "<red>Locked"]}}
    items["back_button"] = {
        "slots": [40], "type": "empty", "item": {"material": "ARROW", "name": "<gray>Back"},
        "actions": {"any": ["[MENU] defaultmenu_backpacks", "[SOUND] minecraft:ui.button.click 1 1"]}}
    return ("# Night Wings menu - open it with /cosmetic menu night_wings\n"
            "# The back button goes to defaultmenu_backpacks, change it if your menu is called something else.\n\n"
            + yaml({"title": f"<{PURPLE}>Night Wings", "rows": 5}) + "\n\nitems:\n" + yaml(items, 2, gap=True) + "\n")
