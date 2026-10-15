"""Builder checks for the dressing room: floating blocks, sealed room, interior light, display clearance, palette."""
import math
from collections import deque, Counter
import numpy as np
import room as RM
import render_room as R

NONSOLID = ("light", "air")
def base(b): return b.split("[")[0].replace("minecraft:", "")

def floating(V, ground_y):
    solid = {p for p, (b, r) in V.items() if base(b) not in NONSOLID}
    seeds = {p for p in solid if p[1] <= ground_y or V[p][1] == "terrain"}
    seen, q = set(seeds), deque(seeds)
    while q:
        x, y, z = q.popleft()
        for d in ((1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)):
            n = (x+d[0], y+d[1], z+d[2])
            if n in solid and n not in seen:
                seen.add(n); q.append(n)
    return sorted(solid - seen)

def leaks(V, start, bounds):
    solid = {p for p, (b, r) in V.items() if base(b) not in NONSOLID}
    (x0, y0, z0, x1, y1, z1) = bounds
    seen, q, out = {start}, deque([start]), []
    while q:
        x, y, z = q.popleft()
        for d in ((1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)):
            n = (x+d[0], y+d[1], z+d[2])
            if n in seen or n in solid: continue
            if not (x0 <= n[0] <= x1 and y0 <= n[1] <= y1 and z0 <= n[2] <= z1):
                out.append((x, y, z)); continue
            seen.add(n); q.append(n)
    return out, seen

def run(island=False):
    V = RM.build_all(island)
    fl = floating(V, 0)
    print("floating:", len(fl), fl[:12])
    lk, room = leaks(V, (0, 3, 5), (-10, 0, -2, 10, 18, 17))
    print("leaks:", len(lk), lk[:8], "| interior air cells:", len(room))
    # light on every walkable cell (air with a solid-ish block under it)
    LF, (lx, ly, lz) = R.light_field(V, (-12, -2, -4, 12, 20, 20))
    dark = []
    for (x, y, z) in room:
        if 1 <= y <= 3 and (x, y - 1, z) in V and base(V[(x, y - 1, z)][0]) not in NONSOLID:
            l = LF[x - lx, y - ly, z - lz]
            if l < 8: dark.append(((x, y, z), int(l)))
    print("walkable cells under light 8:", len(dark), dark[:10])
    # displays: every model box must sit in air (not inside a solid block)
    solid = {p for p, (b, r) in V.items() if base(b) not in NONSOLID and "chain" not in b}
    for d in RM.DISPLAYS:
        m, sc, tilt, pos = R.display_transform(d)
        lo, hi = m.bounds()
        pts = np.array([[a, b, c] for a in (lo[0], hi[0]) for b in (lo[1], hi[1]) for c in (lo[2], hi[2])])
        w = np.array([pos + R.yaw_R(d["yaw"]) @ (tilt @ (p - 8)) * sc / 25.6 for p in pts])
        wl, wh = w.min(0) + 0.03, w.max(0) - 0.03
        hit = [(x, y, z) for x in range(math.floor(wl[0]), math.ceil(wh[0])) for y in range(math.floor(wl[1]), math.ceil(wh[1]))
               for z in range(math.floor(wl[2]), math.ceil(wh[2])) if (x, y, z) in solid]
        print(f"  {d['id']:20s} box {wl.round(2)}..{wh.round(2)} clips: {[(h, base(V[h][0])) for h in hit]}")
    # NPC and viewer cells must be air
    for name, p in (("npc", RM.NPC), ("viewer", RM.VIEWER), ("leave", RM.LEAVE)):
        cells = [(math.floor(p[0]), math.floor(p[1]) + k, math.floor(p[2])) for k in (0, 1)]
        print(f"  {name} cells:", [(c, base(V[c][0]) if c in V else "air") for c in cells])
    pal = Counter(base(b) for b, r in V.values() if r not in ("terrain", "nature", "light"))
    print("palette:", pal.most_common())
    return V

if __name__ == "__main__":
    run(False)
