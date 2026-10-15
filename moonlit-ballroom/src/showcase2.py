"""Moonlit Ballroom showcase v2: writes the compact hall, its furniture and the updated ambience
into the existing moonball_showcase datapack. The v1 build_* functions stay untouched as the backup
(run `function moonball:build` to bring the old manor back)."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import hall

OX, OY, OZ = hall.O
NS = "moonball"
FRAGILE = ("lantern", "chain", "lily_of_the_valley", "azure_bluet", "carpet", "sign", "end_rod", "hanging_roots",
           "potted_", "carved_pumpkin", "leaves", "gravel")

def split_commands():
    V = hall.build_all()
    solid = {p: v for p, v in V.items() if not any(k in v[0] for k in FRAGILE)}
    fragile = {p: v for p, v in V.items() if p not in solid}
    out = []
    for group in (solid, fragile):
        hall.V.clear(); hall.V.update(group)
        out.append([c + " strict" for c in hall.commands()])
    hall.build_all()
    return out

def clear_old():
    """Air out the v1 manor box (x 92..170, y 182..258, z 88..204) in fills under 32768 blocks."""
    cmds = []
    for y in range(182, 259, 3):
        cmds.append(f"fill 92 {y} 88 170 {min(y + 2, 258)} 204 minecraft:air strict")
    cmds.append("kill @e[type=item,x=88,y=170,z=84,dx=90,dy=100,dz=130]")
    cmds.append("kill @e[type=falling_block,x=88,y=170,z=84,dx=90,dy=100,dz=130]")
    return cmds

place = []
def furn(iid, x, y, z, yaw, model=None):
    model = model or iid
    place.append(
        f'summon minecraft:item_display {OX + x + 0.5} {OY + y + 0.5} {OZ + z + 0.5} '
        f'{{Rotation:[{float(yaw)}f,0f],item_display:"none",Tags:["moonball_show"],Invulnerable:1b,'
        f'item:{{id:"minecraft:paper",count:1,components:{{"minecraft:item_model":"{NS}:{model}"}}}},'
        f'BukkitValues:{{"nexo:furniture":"{NS}_{iid}"}}}}')

# Facing: the model's front points the way the entity looks (vanilla yaw: 0 south, 90 west,
# 180 north, 270 east), same as Nexo's own placement. Checked in game Oct 14 (portraits).
def furniture():
    place.append("kill @e[type=item_display,tag=moonball_show]")
    for z in (-13, -10):                                   # ghost lanterns on the path plinths, facing the path
        furn("ghost_lantern", -3, 2, z, 270, "ghost_lantern_lit")
        furn("ghost_lantern", 3, 2, z, 90, "ghost_lantern_lit")
    furn("wisp", -2, 1, -2, 180)                           # greeter in the vestibule, facing the door
    for x, z in ((0, 11), (-3, 15), (3, 15)):              # three couples, one on the medallion
        furn("waltzing_ghosts", x, 1, z, 180)
    furn("ghost_piano", -1, 2, 22, 180)                    # stage, keys toward the hall
    for x in (-4, 4):
        furn("floating_candelabra", x, 2, 21, 180, "floating_candelabra_lit")
    furn("wisp", 3, 2, 23, 180)
    for z in (8, 16):                                      # portrait gallery, faces into the room
        furn("ghost_portrait", -5, 4, z, 270)
        furn("ghost_portrait", 5, 4, z, 90)
    furn("ghost_lantern", -5, 2, 12, 270, "ghost_lantern_lit")  # side tables
    furn("ghost_lantern", 5, 2, 12, 90, "ghost_lantern_lit")
    # piano hitbox (Nexo barriers 0,0,0 / -1,0,0 / 0,1,0 / -1,1,0 turned to yaw 180)
    for x, y, z in ((0, 0, 0), (-1, 0, 0), (0, 1, 0), (-1, 1, 0)):
        place.append(f"setblock {OX - 1 - x} {OY + 2 + y} {OZ + 22 - z} minecraft:barrier")
    return place

BALL = (OX - 6, OY - 1, OZ, 12, 22, 24)
ISLE = (OX - 18, OY - 25, OZ - 27, 36, 60, 56)
def sel(b, extra=""):
    x, y, z, dx, dy, dz = b
    return f"@a[x={x},y={y},z={z},dx={dx},dy={dy},dz={dz}{extra}]"

def tick():
    return [
        "scoreboard players add #t moonball 1",
        f"execute if score #t moonball matches 8.. if entity {sel(BALL)} run function moonball:music/beat",
        "execute if score #t moonball matches 8.. run scoreboard players set #t moonball 0",
        f"execute as {sel(ISLE, ',tag=!moonball_in')} run title @s times 20 70 30",
        f"execute as {sel(ISLE, ',tag=!moonball_in')} run title @s subtitle {{\"text\":\"a Mistbloom Studios showcase\",\"color\":\"#9fb3d9\"}}",
        f"execute as {sel(ISLE, ',tag=!moonball_in')} run title @s title {{\"text\":\"Moonlit Ballroom\",\"color\":\"#f2c97d\"}}",
        f"tag {sel(ISLE, ',tag=!moonball_in')} add moonball_in",
        f"execute as @a[tag=moonball_in] unless entity @s[x={ISLE[0]},y={ISLE[1]},z={ISLE[2]},dx={ISLE[3]},dy={ISLE[4]},dz={ISLE[5]}] run tag @s remove moonball_in",
        f"execute if entity {sel(ISLE)} positioned {OX} {OY + 1} {OZ - 4} run particle minecraft:cloud ~ ~ ~ 12 0.3 18 0.003 1",
        f"execute if entity {sel(ISLE)} positioned {OX} {OY + 8} {OZ + 4} run particle minecraft:white_ash ~ ~ ~ 12 6 18 0 3",
        f"execute if entity {sel(BALL)} positioned {OX} {OY + 3} {OZ + 13} run particle minecraft:end_rod ~ ~ ~ 3 1.5 3 0.003 1",
        f"execute if entity {sel(BALL)} positioned {OX} {OY + 7} {OZ + 12} run particle minecraft:soul ~ ~ ~ 4 2 10 0.002 1",
    ]

def write(fdir):
    solid, fragile = split_commands()
    files = {}
    parts = [solid[i:i + 3000] for i in range(0, len(solid), 3000)]
    for k, p in enumerate(parts):
        files[f"hall_{k}"] = p
    files["hall_details"] = fragile
    files["hall_clear_old"] = clear_old()
    files["hall"] = [f"function moonball:hall_{k}" for k in range(len(parts))] + ["function moonball:hall_details"]
    files["hall_furniture"] = furniture()
    files["tick"] = tick()
    for n, lines in files.items():
        open(os.path.join(fdir, n + ".mcfunction"), "w").write("\n".join(lines) + "\n")
    print({n: len(l) for n, l in files.items()})
    return list(files)

if __name__ == "__main__":
    write(sys.argv[1])
