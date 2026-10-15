"""Writes the hfest_showcase datapack (Selling Test, Minecraft 26.2).

  function hfest:build      island + buildings (solid blocks), then details (plants, lanterns, lights)
  function hfest:furniture  the 119 Halloween pieces as display-only item_displays (tag hfest_show)
  function hfest:clear      removes everything again (air over the whole box + the pieces)
  hfest:tick                arrival title + ambience particles (runs only while someone is on the island)
"""
import os, sys, json, shutil
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
import festival as F
import checks as C

NS = "hfest"
OX, OY, OZ = F.O
FRAGILE = ("lantern", "chain", "candle", "door", "trapdoor", "short_grass", "fern", "mushroom", "firefly_bush",
           "leaf_litter", "hanging_roots", "dripstone", "hanging_moss", "light[", "campfire", "carved_pumpkin", "jack_o_lantern",
           "pumpkin", "_pane", "fence", "_wall[", "cobblestone_wall", "_wall\"", "slab", "stairs", "barrel", "bookshelf", "hay_block", "leaves")

def is_fragile(b):
    return any(k in b for k in FRAGILE) or b.endswith("_wall")

sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
import render as RR

def connect(V):
    """strict placement skips shape updates, so work out fence and wall connections here."""
    out = dict(V)
    sides = {"north": (0, -1), "south": (0, 1), "west": (-1, 0), "east": (1, 0)}
    def base(b): return b.split("[")[0]
    def kind(b):
        n = base(b)
        if n.endswith("_fence") and "nether" not in n: return "fence"
        if n.endswith("_wall"): return "wall"
        if n.endswith("_pane"): return "pane"
        return None
    def solid(b):
        return RR.opaque(b) or "leaves" in b
    for (x, y, z), (b, r) in V.items():
        k = kind(b)
        if k not in ("fence", "wall"):
            continue
        con = {}
        for f, (dx, dz) in sides.items():
            nb = V.get((x + dx, y, z + dz), (None, None))[0]
            c = nb is not None and (kind(nb) == k or solid(nb))
            con[f] = c
        if k == "fence":
            st = ",".join(f"{f}={'true' if con[f] else 'false'}" for f in sides)
        else:
            above = V.get((x, y + 1, z), (None, None))[0]
            straight = (con["north"] and con["south"] and not con["east"] and not con["west"]) or \
                       (con["east"] and con["west"] and not con["north"] and not con["south"])
            up = (not straight) or (above is not None and RR.base(above) not in ("light", "air"))
            st = ",".join(f"{f}={'low' if con[f] else 'none'}" for f in sides) + f",up={'true' if up else 'false'}"
        out[(x, y, z)] = (base(b) + "[" + st + "]", r)
    return out

def runs(V):
    """Vertical runs of identical blocks per column, then merged along x into fills."""
    segs = []
    cols = {}
    for (x, y, z), (b, r) in V.items():
        cols.setdefault((x, z), []).append((y, b))
    for (x, z), lst in cols.items():
        lst.sort()
        i = 0
        while i < len(lst):
            y0, b = lst[i]
            j = i
            while j + 1 < len(lst) and lst[j + 1][0] == lst[j][0] + 1 and lst[j + 1][1] == b:
                j += 1
            segs.append((z, y0, lst[j][0], b, x))
            i = j + 1
    segs.sort()
    out = []
    i = 0
    while i < len(segs):
        z, y0, y1, b, x = segs[i]
        j = i
        while j + 1 < len(segs) and segs[j + 1][:4] == (z, y0, y1, b) and segs[j + 1][4] == segs[j][4] + 1:
            j += 1
        x2 = segs[j][4]
        if (x2, y1) == (x, y0):
            out.append(f"setblock {OX + x} {OY + y0} {OZ + z} {b} strict")
        else:
            out.append(f"fill {OX + x} {OY + y0} {OZ + z} {OX + x2} {OY + y1} {OZ + z} {b} strict")
        i = j + 1
    return out

def furniture():
    out = ["minecraft:kill @e[type=item_display,tag=hfest_show]"]
    for (name, x, y, z, yaw) in F.PIECES:
        fl = C.INV[name]['floor']
        dye = C.INV[name]['dye']
        comps = {"minecraft:item_model": f"hollowmere:{name}"}
        if dye and dye != "None":
            rgb = [int(v) for v in str(dye).strip("()[] ").split(",")]
            comps["minecraft:dyed_color"] = (rgb[0] << 16) | (rgb[1] << 8) | rgb[2]
        item = json.dumps({"id": "minecraft:paper", "count": 1, "components": comps}, separators=(",", ":"))
        ex, ey, ez = OX + x + 0.5, OY + y + 0.5 - fl / 16, OZ + z + 0.5
        out.append(f'summon minecraft:item_display {ex:g} {ey:g} {ez:g} {{Tags:["hfest_show"],Rotation:[{float(yaw)}f,0f],'
                   f'item_display:"none",item:{item}}}')
    return out

BOX = (OX - 40, OY - 40, OZ - 46, OX + 40, OY + 24, OZ + 50)

def clear():
    x0, y0, z0, x1, y1, z1 = BOX
    out = ["minecraft:kill @e[type=item_display,tag=hfest_show]"]
    for y in range(y0, y1 + 1, 4):
        out.append(f"fill {x0} {y} {z0} {x1} {min(y + 3, y1)} {z1} minecraft:air strict")
    return out

ISLE = (OX - 36, OY - 6, OZ - 44, 72, 40, 92)       # x y z dx dy dz selector box
GRAVE = (OX + 14, OY, OZ - 11, 18, 10, 22)

def sel(b, extra=""):
    x, y, z, dx, dy, dz = b
    return f"@a[x={x},y={y},z={z},dx={dx},dy={dy},dz={dz}{extra}]"

def tick():
    bfx, bfz = F.BF
    return [
        f"execute as {sel(ISLE, ',tag=!hfest_in')} run title @s times 20 70 30",
        f"execute as {sel(ISLE, ',tag=!hfest_in')} run title @s subtitle {{\"text\":\"a Mistbloom Studios showcase\",\"color\":\"#c9b8f0\"}}",
        f"execute as {sel(ISLE, ',tag=!hfest_in')} run title @s title {{\"text\":\"Halloween Festival\",\"color\":\"#ffb15c\"}}",
        f"tag {sel(ISLE, ',tag=!hfest_in')} add hfest_in",
        f"execute as @a[tag=hfest_in] unless entity @s[x={ISLE[0]},y={ISLE[1]},z={ISLE[2]},dx={ISLE[3]},dy={ISLE[4]},dz={ISLE[5]}] run tag @s remove hfest_in",
        f"execute if entity {sel(ISLE)} positioned {OX} {OY + 6} {OZ} run particle minecraft:white_ash ~ ~ ~ 26 5 30 0 4",
        f"execute if entity {sel(ISLE)} positioned {OX + 21} {OY + 1.2} {OZ} run particle minecraft:soul ~ ~ ~ 5 0.4 8 0.004 1",
        f"execute if entity {sel(ISLE)} positioned {OX + 26} {OY + 2} {OZ + 0.5} run particle minecraft:end_rod ~ ~ ~ 1.5 1.5 3 0.002 1",
        f"execute if entity {sel(ISLE)} positioned {OX - 24.5} {OY + 1.6} {OZ - 10.5} run particle minecraft:witch ~ ~ ~ 0.3 0.2 0.3 0.01 1",
        f"execute if entity {sel(ISLE)} positioned {OX + 0.5} {OY + 1.6} {OZ + 0.5} run particle minecraft:effect ~ ~ ~ 0.2 0.1 0.2 0.01 1",
        f"execute if entity {sel(ISLE)} positioned {OX + bfx + 0.5} {OY + 3} {OZ + bfz + 0.5} run particle minecraft:lava ~ ~ ~ 0.4 0.2 0.4 0 1",
        f"execute if entity {sel(ISLE)} positioned {OX} {OY + 0.3} {OZ - 2} run particle minecraft:cloud ~ ~ ~ 28 0.2 34 0.002 1",
    ]

def write(root):
    shutil.rmtree(root, ignore_errors=True)
    fdir = os.path.join(root, "data", NS, "function")
    os.makedirs(fdir)
    os.makedirs(os.path.join(root, "data", "minecraft", "tags", "function"))
    json.dump({"pack": {"description": "Halloween Festival showcase - Mistbloom Studios", "pack_format": 94,
                        "min_format": 1, "max_format": 9999, "supported_formats": [1, 9999]}},
              open(os.path.join(root, "pack.mcmeta"), "w"), indent=1)
    V = connect(F.build_all())
    solid = {p: v for p, v in V.items() if not is_fragile(v[0])}
    fragile = {p: v for p, v in V.items() if p not in solid}
    sc, fc = runs(solid), runs(fragile)
    files = {}
    parts = [sc[i:i + 4000] for i in range(0, len(sc), 4000)]
    for k, p in enumerate(parts):
        files[f"build_{k}"] = p
    dparts = [fc[i:i + 4000] for i in range(0, len(fc), 4000)]
    for k, p in enumerate(dparts):
        files[f"details_{k}"] = p
    files["build"] = [f"function {NS}:build_{k}" for k in range(len(parts))] + [f"function {NS}:details_{k}" for k in range(len(dparts))]
    files["furniture"] = furniture()
    files["clear"] = clear()
    files["tick"] = tick()
    files["arrive"] = [f"tp @s {OX + 0.5} {OY + 1} {OZ - 38.5} 0 5"]
    for n, lines in files.items():
        open(os.path.join(fdir, n + ".mcfunction"), "w").write("\n".join(lines) + "\n")
    json.dump({"values": [f"{NS}:tick"]}, open(os.path.join(root, "data/minecraft/tags/function/tick.json"), "w"))
    states = sorted({v[0] for v in V.values()})
    return {n: len(l) for n, l in files.items()}, states

if __name__ == "__main__":
    counts, states = write("/home/claude/festival/datapack/hfest_showcase")
    print(counts, len(states), "block states")
    json.dump(states, open("/home/claude/festival/states.json", "w"))
