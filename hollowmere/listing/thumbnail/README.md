# Halloween Festival store icon (Hibiscus layout, same recipe as Moonlit Ballroom)

1. `pieces_render.py` renders 9 pieces with the pack engine (`../../src`) at one camera and one scale, plus a hard sun-shadow mask per piece (every frame for the animated ones).
2. Title: Minecraft Title Generator in Blockbench 5.2.2 web, driven by `brand/logo-v2/build/title.py jobs.json <outdir>`.
   HALLOWEEN = Minecraft Ten, top type, gradient #FFE9A8 > #FF9A3C > #B8401C (pumpkin).
   FESTIVAL = small type, gradient #F6ECFF > #C9A8F5 > #6E46B8 (lilac), rendered at w 7000.
   FESTIVAL is 80% of HALLOWEEN's width and overlaps its bottom by 35%; stray hairlines removed. Result: `title.png`.
   Plugin patch: before the final `})()` add `window.__mtg = { get format() { return format }, fonts, variables, initialLoad, addText, getFontTextures, getDefaultDialogArgs, loadRenderAngle }`; roots[0] pointed at a local copy of the font repo.
3. `compose.py [out.png] --animate`: dusky plum floor with two warm hard-edged bands, shadows first (55%), back row (lamp post, potion stall, scarecrow) then front row, title at the bottom. `--animate` writes the GIF/WebP at the in-game flicker timing (100/150/100/100/200/100 ms) with unchanged pixels locked so nothing shimmers.
