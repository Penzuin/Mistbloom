"""Writes the whdr_showcase datapack: the Witching Hour dressing room on Selling Test (Minecraft 26.2).

  function whdr:build      forceloads the area, island + room (solid blocks), then details, then displays + signs
  function whdr:displays   the six cosmetics as item displays (tag whdr_show)
  function whdr:clear      removes everything again
  function whdr:arrive     tp to the island path, facing the door
  whdr:tick                arrival title + a few sparkles over the dais while someone is inside
"""
import os, sys, json, shutil, math
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import room as RM
import render_room as R

NS = "whdr"
O = (-1450, 150, -760)
OX, OY, OZ = O
FRAGILE = ("lantern", "chain", "candle", "door", "trapdoor", "hanging_roots", "light[", "carpet", "sign", "skull",
           "_pane", "fence", "_wall[", "slab", "stairs", "leaves", "amethyst_cluster", "lightning_rod", "dirt_path")


def is_fragile(b):
    return any(k in b for k in FRAGILE) or b.endswith("_wall")


def connect(V):
    """strict placement skips shape updates, so fence and wall connections are worked out here."""
    out = dict(V)
    sides = {"north": (0, -1), "south": (0, 1), "west": (-1, 0), "east": (1, 0)}
    def base(b): return b.split("[")[0]
    def kind(b):
        n = base(b)
        if n.endswith("_fence"): return "fence"
        if n.endswith("_wall"): return "wall"
        return None
    for (x, y, z), (b, r) in V.items():
        k = kind(b)
        if not k:
            continue
        con = {}
        for f, (dx, dz) in sides.items():
            nb = V.get((x + dx, y, z + dz), (None, None))[0]
            con[f] = nb is not None and (kind(nb) == k or R.opaque(nb))
        if k == "fence":
            st = ",".join(f"{f}={'true' if con[f] else 'false'}" for f in sides)
        else:
            st = ",".join(f"{f}={'low' if con[f] else 'none'}" for f in sides) + ",up=true"
        out[(x, y, z)] = (base(b) + "[" + st + "]", r)
    return out


def runs(V):
    """Vertical runs of identical blocks per column, merged along x into fills."""
    segs, cols = [], {}
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
    out, i = [], 0
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


def f(v):
    return f"{v:.4f}".rstrip("0").rstrip(".") + "f"


def displays():
    out = ["minecraft:kill @e[type=item_display,tag=whdr_show]"]
    for d in RM.DISPLAYS:
        m, sc, tilt, pos = R.display_transform(d)
        s = 0.625 * sc
        item = {"id": "minecraft:paper", "count": 1, "components": {"minecraft:item_model": f"mistbloom:{d['id']}"}}
        glow = d["id"] in ("wisp", "ghostlight_lantern", "candle_crown")
        bright = ",brightness:{sky:15,block:15}" if glow else ""
        x, y, z = OX + pos[0], OY + pos[1], OZ + pos[2]
        out.append(
            f'summon minecraft:item_display {x:.4f} {y:.4f} {z:.4f} {{Tags:["whdr_show"],Rotation:[{f(d["yaw"])},0f],'
            f'item_display:"none",view_range:2f{bright},'
            f'transformation:{{left_rotation:[0f,0f,0f,1f],right_rotation:[0f,0f,0f,1f],translation:[0f,0f,0f],'
            f'scale:[{f(s)},{f(s)},{f(s)}]}},item:{json.dumps(item, separators=(",", ":"))}}}')
    return out


def snbt_text(t, cmd=None):
    q = json.dumps(t)
    if cmd:
        return f'{{text:{q},click_event:{{action:"run_command",command:"{cmd}"}}}}'
    return q


def signs():
    out = []
    for (x, y, z, b, lines, cmd) in RM.SIGNS:
        lines = list(lines) + [""] * (4 - len(lines))
        msgs = ",".join(snbt_text(t, cmd if (cmd and k == 0) or (cmd and t) else None) for k, t in enumerate(lines))
        out.append(f"setblock {OX + x} {OY + y} {OZ + z} {b}"
                   f"{{is_waxed:1b,front_text:{{has_glowing_text:1b,color:\"white\",messages:[{msgs}]}}}} replace")
    return out


BOX = (OX - 26, OY - 28, OZ - 27, OX + 26, OY + 20, OZ + 33)
FL = (OX - 26, OZ - 27, OX + 26, OZ + 33)


def clear():
    x0, y0, z0, x1, y1, z1 = BOX
    out = [f"forceload add {FL[0]} {FL[1]} {FL[2]} {FL[3]}", "minecraft:kill @e[type=item_display,tag=whdr_show]"]
    for y in range(y0, y1 + 1, 6):
        out.append(f"fill {x0} {y} {z0} {x1} {min(y + 5, y1)} {z1} minecraft:air strict")
    out.append(f"forceload remove {FL[0]} {FL[1]} {FL[2]} {FL[3]}")
    return out


def tick():
    room = f"x={OX - 9},y={OY},z={OZ - 1},dx=18,dy=8,dz=17"
    isle = f"x={OX - 24},y={OY - 6},z={OZ - 25},dx=48,dy=30,dz=56"
    return [
        f"execute as @a[{isle},tag=!whdr_in] run title @s times 15 60 25",
        f"execute as @a[{isle},tag=!whdr_in] run title @s subtitle {{\"text\":\"dressing room\",\"color\":\"#c9b8f0\"}}",
        f"execute as @a[{isle},tag=!whdr_in] run title @s title {{\"text\":\"Witching Hour\",\"color\":\"#e8c8ff\"}}",
        f"tag @a[{isle},tag=!whdr_in] add whdr_in",
        f"execute as @a[tag=whdr_in] unless entity @s[{isle}] run tag @s remove whdr_in",
        f"execute if entity @a[{room}] positioned {OX + 0.5} {OY + 2.3} {OZ + 12.5} run particle minecraft:end_rod ~ ~ ~ 1.2 0.6 1.2 0.002 1",
        f"execute if entity @a[{room}] positioned {OX + 7.5} {OY + 3.9} {OZ + 9.5} run particle minecraft:witch ~ ~ ~ 0.2 0.2 0.2 0.01 1",
    ]


def write(root):
    shutil.rmtree(root, ignore_errors=True)
    fdir = os.path.join(root, "data", NS, "function")
    os.makedirs(fdir)
    os.makedirs(os.path.join(root, "data", "minecraft", "tags", "function"))
    json.dump({"pack": {"description": "Witching Hour dressing room - Mistbloom Studios", "pack_format": 94,
                        "min_format": 1, "max_format": 9999, "supported_formats": [1, 9999]}},
              open(os.path.join(root, "pack.mcmeta"), "w"), indent=1)
    V = connect(RM.build_all(True))
    sign_cells = {(x, y, z) for (x, y, z, *_) in RM.SIGNS}
    V = {p: v for p, v in V.items() if p not in sign_cells}          # signs go in last, with their text
    solid = {p: v for p, v in V.items() if not is_fragile(v[0])}
    fragile = {p: v for p, v in V.items() if p not in solid}
    sc, fc = runs(solid), runs(fragile)
    files = {}
    parts = [sc[i:i + 4000] for i in range(0, len(sc), 4000)]
    for k, p in enumerate(parts):
        files[f"build_{k}"] = p
    files["details"] = fc
    files["build"] = ([f"forceload add {FL[0]} {FL[1]} {FL[2]} {FL[3]}"]
                      + [f"function {NS}:build_{k}" for k in range(len(parts))]
                      + [f"function {NS}:details", f"function {NS}:signs", f"function {NS}:displays",
                         f"forceload remove {FL[0]} {FL[1]} {FL[2]} {FL[3]}"])
    files["signs"] = signs()
    files["displays"] = displays()
    files["clear"] = clear()
    files["tick"] = tick()
    x, y, z, yaw, pitch = RM.ARRIVE
    files["arrive"] = [f"tp @s {OX + x} {OY + y} {OZ + z} {yaw:g} {pitch:g}"]
    for n, lines in files.items():
        open(os.path.join(fdir, n + ".mcfunction"), "w").write("\n".join(lines) + "\n")
    json.dump({"values": [f"{NS}:tick"]}, open(os.path.join(root, "data/minecraft/tags/function/tick.json"), "w"))
    return {n: len(l) for n, l in files.items()}


def wardrobe_yml(world="world", menu="witching_hour"):
    def loc(p):
        x, y, z, yaw, pitch = p
        return (f"    world: \"{world}\"\n    x: {OX + x}\n    y: {OY + y}\n    z: {OZ + z}\n"
                f"    yaw: {yaw:g}\n    pitch: {pitch:g}\n")
    return ("# Witching Hour dressing room (Selling Test). Open it with /cosmetics wardrobes witching_hour\n"
            "# or click the \"try it on\" sign by the runner.\n"
            f"{RM.WARDROBE_ID}:\n"
            "  # only works from inside the room\n"
            "  distance: 14\n"
            "  permission: \"hmccosmetics.wardrobe.witching_hour\"\n"
            f"  default-menu: {menu}\n"
            "  # the clone stands on the dais facing the door\n"
            f"  npc-location:\n{loc(RM.NPC)}"
            "  # the camera floats over the runner, 4 blocks back\n"
            f"  viewer-location:\n{loc(RM.VIEWER)}"
            "  # you step back onto the runner when you leave\n"
            f"  leave-location:\n{loc(RM.LEAVE)}")


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "out")
    print(write(os.path.join(out, "whdr_showcase")))
    open(os.path.join(out, "witching_hour.yml"), "w").write(wardrobe_yml())
