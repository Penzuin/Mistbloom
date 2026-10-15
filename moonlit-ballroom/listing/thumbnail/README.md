# Store icon, Hibiscus-style layout (v2)

1. `pieces_render.py` renders every piece with the ballroom engine (`../../src`) at one camera and one scale,
   plus a hard sun shadow mask (each cube projected onto the floor along one light direction).
2. Title: Minecraft Title Generator in Blockbench web, driven by `brand/logo-v2/build/title.py`.
   The plugin needs a one-line patch at the end exposing its internals as `window.__mtg`
   (format, fonts, variables, initialLoad, addText, getFontTextures, getDefaultDialogArgs, loadRenderAngle).
   `jobs3.json` = MOONLIT (gradient #FFF8E6 > #C9B8F0 > #5B45B0, Minecraft Ten, top type),
   `jobs4.json` = BALLROOM (gradient #FFF6D8 > #F2C97D > #C8903F, small type, rendered at w 7000 so it stays sharp).
   BALLROOM is scaled to 80% of MOONLIT's width and overlaps its bottom by 35%; stray Blockbench hairlines removed
   (keep only connected pieces over 5000 px). Result: `title.png`.
3. `compose.py` lays it out: lavender floor with a soft corner falloff and two hard-edged moonlight bands,
   shadows first (floor colour pushed dark, 55%), pieces on top, back row then front row, title at the bottom.
