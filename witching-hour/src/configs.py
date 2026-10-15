"""Config files for Witching Hour, written the way you'd write them by hand:
short ids, one-line lore, list items indented, a blank line between entries."""
from engine import NS
from pieces import PIECES

PURPLE = "#c9b8ff"
LORE = {key: lore for key, _, _, lore, _ in PIECES}
SLOT_WORD = {"HELMET": "Hat", "BACKPACK": "Back cosmetic", "OFFHAND": "Off-hand cosmetic", "BALLOON": "Balloon"}

# Wisp floats a little above and beside the shoulder. HMCC's default balloon sits much higher.
BALLOON_OFFSET = "0.7,1.2,0.7"

_SPECIAL = set(":#{}[],&*!|>'\"%@`")


def _scalar(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    s = str(v)
    needs = (s == "" or s[0] in _SPECIAL or s[0] in "-?" or ": " in s or " #" in s
             or s.lower() in ("yes", "no", "true", "false", "null", "on", "off") or s.strip() != s
             or (s.replace(".", "").replace(",", "").replace("-", "").isdigit()))
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
            if all(isinstance(x, int) for x in v) and len(v) <= 3:
                out.append(f"{pad}{k}: [{', '.join(str(x) for x in v)}]")
            else:
                out.append(f"{pad}{k}:")
                for x in v:
                    out.append(f"{pad}  - {_scalar(x)}")
        else:
            out.append(f"{pad}{k}: {_scalar(v)}")
    return "\n".join(out)


def lore(m, slot):
    return [f"<gray>{LORE[m.name]}", f"<dark_gray>{SLOT_WORD[slot]}"]


# ------------------------------------------------------------------ items plugins
def nexo_items(entries):
    out = {}
    for m, title, slot in entries:
        out[m.name] = {"itemname": f"<{PURPLE}>{title}", "lore": lore(m, slot), "material": "PAPER",
                       "Components": {"item_model": f"{NS}:{m.name}"}}
    return ("# Witching Hour - Nexo items\n"
            "# These are only used by HMCCosmetics, you don't need to give them out.\n\n" + yaml(out, gap=True) + "\n")


def oraxen_items(entries):
    out = {}
    for m, title, slot in entries:
        out[m.name] = {"itemname": f"<{PURPLE}>{title}", "lore": lore(m, slot), "material": "PAPER",
                       "components": {"item_model": f"{NS}:{m.name}"},
                       "Pack": {"generate_model": False, "exclude_from_item_model": True}}
    return ("# Witching Hour - Oraxen items\n"
            "# These are only used by HMCCosmetics, you don't need to give them out.\n\n" + yaml(out, gap=True) + "\n")


def ia_items(entries):
    items = {}
    for m, title, slot in entries:
        items[m.name] = {"display_name": f"&d{title}", "lore": [f"&7{LORE[m.name]}", f"&8{SLOT_WORD[slot]}"],
                         "resource": {"material": "PAPER", "generate": False, "model_path": f"cosmetics/{m.name}"}}
    return ("# Witching Hour - ItemsAdder items\n\n" + yaml({"info": {"namespace": NS}}) + "\n\n"
            + "items:\n" + yaml(items, 2, gap=True) + "\n")


# ------------------------------------------------------------------ HMCCosmetics
def hmc_cosmetics(entries, plugin):
    out = {}
    for m, title, slot in entries:
        c = {"slot": slot, "permission": f"hmccosmetics.{m.name}"}
        if slot == "BALLOON":
            c["show-lead"] = False
            c["balloon-offset"] = BALLOON_OFFSET
        item = {}
        if plugin == "none":
            item["material"] = "PAPER"
            item["model-id"] = f"{NS}:{m.name}"
        else:
            item["material"] = {"nexo": f"nexo:{m.name}", "oraxen": f"oraxen:{m.name}",
                                "itemsadder": f"itemsadder:{NS}:{m.name}"}[plugin]
        item.update({"name": f"<{PURPLE}>{title}", "lore": lore(m, slot)})
        c["item"] = item
        out[m.name] = c
    head = "# Witching Hour - HMCCosmetics\n"
    if plugin == "none":
        head += "# Uses the resource pack in this folder, no items plugin needed.\n"
    head += "# Permission for each one is hmccosmetics.<id>, e.g. hmccosmetics.witch_hat\n"
    head += "# The wisp floats beside you with no lead. Move it with balloon-offset (x, y, z in blocks).\n\n"
    return head + yaml(out, gap=True) + "\n"


def hmc_menu(entries):
    items = {"title_icon": {
        "slots": [4], "type": "empty",
        "item": {"material": "hmccosmetics:witch_hat", "name": f"<{PURPLE}><b>Witching Hour</b>",
                 "lore": ["<gray>Pick something witchy to wear."]}}}
    slots = [19, 20, 21, 23, 24, 25]
    for slot, (m, title, cslot) in zip(slots, entries):
        items[m.name] = {
            "slots": [slot], "type": "cosmetic", "cosmetic": m.name,
            "item": {"material": f"hmccosmetics:{m.name}",
                     "lore": ["", "<yellow>Click to wear"]},
            "locked-item": {"material": "GRAY_STAINED_GLASS_PANE", "name": f"<gray>{title}",
                            "lore": ["", "<red>Locked"]}}
    items["close_button"] = {
        "slots": [40], "type": "empty", "item": {"material": "BARRIER", "name": "<gray>Close"},
        "actions": {"any": ["[CLOSE]", "[SOUND] minecraft:ui.button.click 1 1"]}}
    return ("# Witching Hour menu - open it with /cosmetic menu witching_hour\n\n"
            + yaml({"title": f"<{PURPLE}>Witching Hour", "rows": 5}) + "\n\nitems:\n" + yaml(items, 2, gap=True) + "\n")
