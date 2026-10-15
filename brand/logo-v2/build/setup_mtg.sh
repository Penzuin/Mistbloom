#!/bin/sh
# Rebuilds the local Minecraft Title Generator used by title.py (Blockbench 5.2.2 web + MTG plugin 1.10.4).
# Serves on localhost:8765: /bb/ = Blockbench web build, /mtgrepo/ = the title generator's font repo.
set -e
D=${1:-/root/mtgsetup}
mkdir -p "$D" /root/mtg /root/mtgserve
cd "$D"
[ -d bb ] || git clone -q --depth 1 -b v5.2.2 https://github.com/JannisX11/blockbench.git bb
[ -d plugins ] || git clone -q --depth 1 https://github.com/JannisX11/blockbench-plugins.git plugins
[ -d mtgrepo ] || git clone -q --depth 1 https://github.com/ewanhowell5195/MinecraftTitleGenerator.git mtgrepo
[ -d bb/dist ] || (cd bb && npm ci --ignore-scripts && npm run build-web)
# patch: fonts from the local repo first, and expose the plugin's functions as window.__mtg
python3 - "$D/plugins/plugins/minecraft_title_generator/minecraft_title_generator.js" <<'PY'
import sys
s = open(sys.argv[1]).read()
s = s.replace("    roots: [\n      `https://raw.githubusercontent.com/${repo}/${branch}`,",
              "    roots: [\n      `http://localhost:8765/mtgrepo`,\n      `https://raw.githubusercontent.com/${repo}/${branch}`,", 1)
s = s.replace("  Plugin.register(id, {", "  window.__mtg = { fonts, variables, getDefaultDialogArgs, addText, getFontTextures, loadRenderAngle, initialLoad }\n"
              "  Object.defineProperty(window.__mtg, 'format', { get: () => format })\n  Plugin.register(id, {", 1)
open('/root/mtg/mtg.js', 'w').write(s)
PY
ln -sfn "$D/bb" /root/mtgserve/bb; ln -sfn "$D/mtgrepo" /root/mtgserve/mtgrepo
cd /root/mtgserve && nohup python3 -m http.server 8765 > /root/mtgserve.log 2>&1 &
echo "serving on http://localhost:8765 - now run: python3 title.py jobs.json outdir"
