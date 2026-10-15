"""Seal the Hollowmere showcase lot inside a closed film studio: black box walls + ceiling,
a ragged forest backdrop, a glowing moon on the back wall, end-rod stars and soft fill light."""
import json, random
CX, GY, CZ = -1450, 68, -340
X1, X2 = CX - 18, CX + 18          # studio walls
Z1, Z2 = CZ - 17, CZ + 23          # extra room on the south side for the camera
TOP = GY + 28                      # ceiling
LX1, LX2, LZ1, LZ2 = CX - 14, CX + 14, CZ - 13, CZ + 15     # the existing lot (hedge line)
rng = random.Random(7)
c = [f"forceload add {X1} {Z1} {X2} {Z2}"]
F = lambda x1, y1, z1, x2, y2, z2, b, m="": c.append(f"fill {x1} {y1} {z1} {x2} {y2} {z2} {b}{(' ' + m) if m else ''}")

# clear and floor the bands around the lot (the lot itself is left untouched)
bands = [(X1 + 1, Z1 + 1, X2 - 1, LZ1 - 1), (X1 + 1, LZ2 + 1, X2 - 1, Z2 - 1),
         (X1 + 1, LZ1, LX1 - 1, LZ2), (LX2 + 1, LZ1, X2 - 1, LZ2)]
for (a, b, d, e) in bands:
    F(a, GY + 1, b, d, TOP - 1, e, "minecraft:air")
    F(a, GY - 6, b, d, GY - 1, e, "minecraft:dirt")
    F(a, GY, b, d, GY, e, "minecraft:grass_block")
F(LX1, GY + 23, LZ1, LX2, TOP - 1, LZ2, "minecraft:air")              # top up the lot's clearance
# the box
B = "minecraft:black_concrete"
F(X1, GY - 6, Z1, X1, TOP, Z2, B); F(X2, GY - 6, Z1, X2, TOP, Z2, B)
F(X1, GY - 6, Z1, X2, TOP, Z1, B); F(X1, GY - 6, Z2, X2, TOP, Z2, B)
F(X1, TOP, Z1, X2, TOP, Z2, B)

# ragged forest backdrop between the hedge and the walls (north, west, east)
LEAVES = ["minecraft:dark_oak_leaves[persistent=true]", "minecraft:spruce_leaves[persistent=true]",
          "minecraft:dark_oak_leaves[persistent=true]"]
def strip(x1, z1, x2, z2):
    F(x1, GY + 1, z1, x2, GY + rng.randint(5, 13), z2, rng.choice(LEAVES))
for x in range(X1 + 1, X2):                                   # north band, 3 deep
    strip(x, Z1 + 1, x, LZ1 - 1)
for z in range(LZ1, LZ2 + 1, 1):                              # west and east bands
    strip(X1 + 1, z, LX1 - 1, z); strip(LX2 + 1, z, X2 - 1, z)
for z in range(LZ2 + 1, LZ2 + 4):                             # wrap the south corners a little
    strip(X1 + 1, z, X1 + 4, z); strip(X2 - 4, z, X2 - 1, z)
# bare dead trees poking above the canopy
for (x, z, h) in ((CX - 9, Z1 + 2, 19), (CX + 6, Z1 + 2, 21), (X1 + 2, CZ - 4, 18), (X2 - 2, CZ + 2, 20),
                  (X1 + 2, CZ + 9, 16), (X2 - 2, CZ - 9, 17), (CX - 1, Z1 + 1, 15)):
    F(x, GY + 1, z, x, GY + h, z, "minecraft:dark_oak_log")
    F(x - 1, GY + h - 3, z, x - 2, GY + h - 2, z, "minecraft:dark_oak_fence")
    F(x + 1, GY + h - 5, z, x + 2, GY + h - 4, z, "minecraft:dark_oak_fence")
# moon on the back wall
mx, my, mz, R = CX + 7, GY + 20, Z1 + 1, 4.6
for dy in range(-5, 6):
    w = int((R * R - dy * dy) ** 0.5) if R * R >= dy * dy else -1
    if w >= 0:
        F(mx - w, my + dy, mz, mx + w, my + dy, mz, "minecraft:pearlescent_froglight")
for (dx, dy) in ((-2, 1), (1, -2), (2, 2), (-1, -1)):                 # a few soft craters
    c.append(f"setblock {mx + dx} {my + dy} {mz} minecraft:ochre_froglight")
# stars on the ceiling and upper walls
for _ in range(70):
    x, z = rng.randint(X1 + 1, X2 - 1), rng.randint(Z1 + 1, Z2 - 1)
    c.append(f"setblock {x} {TOP - 1} {z} minecraft:end_rod[facing=down] keep")
for _ in range(24):
    x, y = rng.randint(X1 + 2, X2 - 2), rng.randint(GY + 15, TOP - 2)
    if abs(x - mx) > 6 or abs(y - my) > 6:
        c.append(f"setblock {x} {y} {Z1 + 1} minecraft:end_rod[facing=south] keep")
# soft, invisible fill light so the corners aren't pitch black on camera
for dx in range(-12, 13, 6):
    for dz in range(-12, 16, 6):
        c.append(f"setblock {CX + dx} {GY + 5} {CZ + dz} minecraft:light[level=7] keep")
for dx in range(-12, 13, 8):                                          # camera area
    c.append(f"setblock {CX + dx} {GY + 4} {CZ + 19} minecraft:light[level=6] keep")
c.append(f"forceload remove {X1} {Z1} {X2} {Z2}")
json.dump(c, open("/home/claude/hollow/showcase/studio_cmds.json", "w"))
print(len(c), "commands; max fill volume:",
      max((abs(int(p[3]) - int(p[0])) + 1) * (abs(int(p[4]) - int(p[1])) + 1) * (abs(int(p[5]) - int(p[2])) + 1)
          for p in (x.split()[1:7] for x in c if x.startswith("fill"))))
