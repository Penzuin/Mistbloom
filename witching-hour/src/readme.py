SLOT_WORDS = {"HELMET": "hat", "BACKPACK": "back", "OFFHAND": "off-hand", "BALLOON": "balloon"}


def readme(entries, version):
    names = "\n".join(f"- {t} (`{m.name}`), {SLOT_WORDS[s]}" for m, t, s in entries)
    most = max(len(m.elements) for m, *_ in entries)
    return f"""# Witching Hour

by Mistbloom Studios, version {version}

Thanks for picking up Witching Hour! It's six witchy cosmetics for HMCCosmetics. They're
not costumes, they're things a witch would actually own, so they fit your server all year
and feel right at home when Halloween comes round. The flames, glows and the little ghosts
are animated on the player's game, not your server.

## What's inside

{names}

## You'll need

- Paper or Purpur 1.21.4+
- HMCCosmetics 2.9+
- Nexo, ItemsAdder 4 or Oraxen (or none of them, see below)
- ModelEngine is not needed. The wisp uses a normal item model.

## Installing

Open the folder for the items plugin you use and copy what's inside its `plugins` folder
into your server's `plugins` folder. Let it merge with what's already there.

- **Nexo:** run `/nexo reload all`, then `/cosmetic reload`
- **ItemsAdder:** run `/iazip`, then `/cosmetic reload`
- **Oraxen:** run `/oraxen reload all`, then `/cosmetic reload`
- **No items plugin:** add `Mistbloom_Witching_Hour_ResourcePack.zip` to your server's
  resource pack, then run `/cosmetic reload`

## Using them

- Open the menu with `/cosmetic menu witching_hour`. To link it from your main cosmetics
  menu, add a button with the action `[MENU] witching_hour`.
- Each one has its own permission: `hmccosmetics.<id>`, so `hmccosmetics.witch_hat` for the
  hat. They work well as crate, rank or event rewards.
- To give one straight to someone: `/cosmetic apply <id> <player>`
- The two hats both use the helmet slot, and the lantern and grimoire both use the off-hand,
  so players pick one of each.

## If something looks off

- **The wisp floats too high, too low or too close:** change `balloon-offset` on `wisp` in
  `cosmetics/witching_hour.yml`. It's x, y, z in blocks and ships at `0.7,1.2,0.7`.
- **A hat sits too high or too low:** open its `.bbmodel` in Blockbench, go to Display, pick
  Head and change the Y translation.
- **The lantern or grimoire sits oddly in the hand:** same place, but pick Third Person Left
  Hand. The lantern ships hanging from the fist; move it with the translation values.
- **Still stuck?** Message me with your server version, HMCCosmetics version, which items
  plugin you use and a screenshot, and I'll help you out.

## Performance

Each model is {most} cubes or fewer with one texture. All the animation is texture-based,
so it costs your server nothing.

Please read `LICENSE.txt` before using the pack. Have fun with them!
"""
