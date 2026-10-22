# October Prompt Props: shipping one day (from Day 2, Oct 21 2026)

Pipeline per day: fix model -> buyer zip -> icon + turntable GIF + post image -> Payhip form -> user picks files and clicks Add Product.

- Model: `claude/inktober/v/pNN_*.py`. Engine/px copies used to build: `claude/inktober/ship/engine.py`, `px.py` (engine adds element names and the 14-element check).
- Buyer zip: `ship/build_pack.py` (edit OUT, NAMES, yml text). Each day gets its own yml file (`inkprops_<piece>.yml`) so it doesn't overwrite earlier days. README/LICENSE CRLF.
- Icon/GIF: `ship/icon.py` (sage floor matching Toffee Apples, texel shadow to the right). `python3 icon.py p02_chalice titles/title.png listing/1-x-icon.png 25`; `icon.turntable(m, path, ppu=19, cx=300, base_y=488)` -> 640px, 36 frames, 80 ms.
- Title: real Minecraft Title Generator via `/root/mtg/title.py` (from repo `brand/logo-v2/build/title.py`, patched to accept `cam` and `zoom` per job). Day-series title job: one line, front-on `"cam": [0,-60,-1100], "zoom": 3.2`, `customBorder` #1E0A04, gradient from the piece's main material. Strip hairlines: keep connected parts over 5000 px.
  Setup: clone Blockbench v5.2.2, `npm ci --ignore-scripts && npm run build-web`; clone ewanhowell5195/MinecraftTitleGenerator; plugin from JannisX11/blockbench-plugins `plugins/minecraft_title_generator/`, add `http://localhost:8765/mtgrepo` as first root and `window.__mtg = {get format(){return format}, fonts, variables, initialLoad, addText, getFontTextures, getDefaultDialogArgs, loadRenderAngle}` before the final `})()`; serve /bb and /mtgrepo on 8765; `pip install playwright && playwright install chromium`.
- Post image = the store icon. Files go to `Downloads\<Piece> Upload`.
- Payhip: title "<Piece> | Free Nexo Furniture", price 0, description copied from Toffee Apples with the piece lines changed, tick the October Prompt Props collection.
