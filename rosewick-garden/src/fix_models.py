"""Rosewick Garden v1.0 -> v1.1 model fixes (z-fighting, floating wheel, open wheelbarrow corners).
Usage: python3 fix_models.py <models/furniture dir>   (edits in place)"""
import json, sys, copy, os
D = sys.argv[1]

def load(n): return json.load(open(os.path.join(D, n + ".json")))
def save(n, m): json.dump(m, open(os.path.join(D, n + ".json"), "w"), indent=1)

def card_axis(e):
    return next(a for a in range(3) if e["from"][a] == e["to"][a])

def move_card(m, i, value):
    e = m["elements"][i]; a = card_axis(e)
    e["from"][a] = e["to"][a] = value

def split(m, i, axis, cuts):
    """Split box i along axis at the given coordinates, keeping the texture mapping continuous."""
    e = m["elements"].pop(i)
    lo, hi = e["from"][axis], e["to"][axis]
    edges = [lo] + list(cuts) + [hi]
    # which uv component runs along this axis for each face (u = index 0/2, v = 1/3), and its direction
    along = {0: {"up": ("u", 1), "down": ("u", 1), "north": ("u", -1), "south": ("u", 1)},
             2: {"up": ("v", 1), "down": ("v", -1), "east": ("u", -1), "west": ("u", 1)}}[axis]
    end_faces = {0: ("west", "east"), 2: ("north", "south")}[axis]
    out = []
    for k in range(len(edges) - 1):
        p = copy.deepcopy(e); p["from"][axis], p["to"][axis] = edges[k], edges[k + 1]
        t0, t1 = (edges[k] - lo) / (hi - lo), (edges[k + 1] - lo) / (hi - lo)
        for f, fc in p["faces"].items():
            if f in along:
                comp, sgn = along[f]; j = 0 if comp == "u" else 1
                a, b = fc["uv"][j], fc["uv"][j + 2]
                if sgn < 0: t0_, t1_ = 1 - t1, 1 - t0
                else: t0_, t1_ = t0, t1
                fc["uv"][j], fc["uv"][j + 2] = a + (b - a) * t0_, a + (b - a) * t1_
        if k > 0: p["faces"].pop(end_faces[0], None)
        if k < len(edges) - 2: p["faces"].pop(end_faces[1], None)
        out.append(p)
    for k, p in enumerate(out): m["elements"].insert(i + k, p)

# --- arbor: rose garlands sat 0.1 off the posts
m = load("arbor_arch"); move_card(m, 16, 1.6); move_card(m, 17, 14.4); save("arbor_arch", m)
# --- birdbath: ivy card 0.05 off the pedestal; bird head flush with its body
m = load("birdbath"); move_card(m, 13, 10.4)
m["elements"][11]["from"][2], m["elements"][11]["to"][2] = 1.9, 4.85; save("birdbath", m)
# --- flower box: front roses card
m = load("flower_box"); move_card(m, 7, 3.6); save("flower_box", m)
# --- bench: seat/armrests flush with the back posts, ivy card, back cushion bottoms
m = load("garden_bench"); E = m["elements"]
E[0]["to"][2] = 12.7; E[0]["from"][0] = -5.6; E[0]["to"][0] = 21.6
E[3]["to"][2] = 12.7; E[7]["to"][2] = 12.7; E[10]["to"][2] = 12.3
move_card(m, 15, 22.9)
E[13]["from"][1] = 11.3; E[14]["from"][1] = 11.3
save("garden_bench", m)
# --- chair: seat flush with the back posts on two sides, ivy card
m = load("garden_chair"); E = m["elements"]
E[6]["to"][2] = 14.7; E[6]["from"][0] = 1.3; E[6]["to"][0] = 14.7
move_card(m, 12, 15.4); save("garden_chair", m)
# --- trellis: rose card under the top rail
m = load("rose_trellis"); move_card(m, 5, 6.1); save("rose_trellis", m)
# --- seed cabinet / lanterns / sundial: ivy cards 0.05 off the side
m = load("seed_cabinet"); move_card(m, 11, 15.4); save("seed_cabinet", m)
m = load("stake_lantern"); move_card(m, 10, 9.4); save("stake_lantern", m)
m = load("stake_lantern_lit"); move_card(m, 12, 9.4); save("stake_lantern_lit", m)
m = load("sundial"); move_card(m, 4, 11.4); save("sundial", m)
# --- tea table: the crossed top and crossed feet shared their planes -> split the cross pieces
m = load("tea_table")
split(m, 5, 2, [6.5, 9.5]); del m["elements"][6]      # feet: drop the middle (inside the other foot)
split(m, 1, 2, [3.0, 13.0]); del m["elements"][2]      # top: drop the middle (inside the other slab)
save("tea_table", m)
# --- tool rack: three tool cards in one plane
m = load("tool_rack"); move_card(m, 8, 6.1); move_card(m, 9, 5.7); move_card(m, 10, 5.3); save("tool_rack", m)
# --- wheelbarrow: wheel floated 1 px, wheel faces fought, legs flush with handles, open tub corners
m = load("wheelbarrow"); E = m["elements"]
for i in (0, 1, 2):
    E[i]["from"][1] -= 1.05; E[i]["to"][1] -= 1.05
    if "rotation" in E[i]: E[i]["rotation"]["origin"][1] -= 1.05
E[1]["from"][0], E[1]["to"][0] = 7.4, 8.6
for i in (4, 6):
    E[i]["from"][0] -= 0.35; E[i]["to"][0] += 0.35
for i in (10, 11):
    E[i]["from"][2], E[i]["to"][2] = 2.0, 14.0
save("wheelbarrow", m)
print("ok")
