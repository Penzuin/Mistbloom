# Mistbloom logo v2 - how it's built

The name is made with Ewan Howell's **Minecraft Title Generator** Blockbench plugin
(github.com/ewanhowell5195/MinecraftTitleGenerator), running inside Blockbench 5.2.2 web.

Plugin default font (**Minecraft Ten**), border, depth and overlay. Only the colours are set,
using the plugin's Gradient texture option (user asked: default font, no Cracked texture, brand colours):
- "mistbloom": type Top, gradient #F4EEFF -> #C9B8F0 -> #7A64CC (Moonpetal)
- "studios": second text, type Small, row 1, gradient #FFF6D8 -> #F2C97D -> #C8903F (Lantern Gold)

The flower is the original Mistbloom mark, unchanged.

Rebuild: clone Blockbench + the plugin and font repo, build Blockbench web, serve it locally,
then `title.py colour.json <outdir>` (jobs read their settings from the plugin's own dialog), `mark.py`, `compose.py all`.
