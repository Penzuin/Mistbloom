import sys, json, math
from collections import deque, Counter
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
import festival as F
INV = json.load(open(__import__('os').path.join(__import__('os').path.dirname(__import__('os').path.abspath(__file__)), 'pieces.json')))

def base(b): return b.split('[')[0].split('{')[0].replace('minecraft:', '')
NONSOLID = ('light', 'air')

def piece_box(name, x, y, z, yaw):
    """World-space AABB (local frame) of a placed piece, from its model bounds."""
    lo = [float(v) for v in INV[name]['bounds'][0].strip('[]').split()] if isinstance(INV[name]['bounds'][0], str) else INV[name]['bounds'][0]
    hi = [float(v) for v in INV[name]['bounds'][1].strip('[]').split()] if isinstance(INV[name]['bounds'][1], str) else INV[name]['bounds'][1]
    fl = INV[name]['floor']
    ey = y + 0.5 - fl / 16                       # entity centre y (block y + 0.5 - floor)
    cx, cz = x + 0.5, z + 0.5
    f = (-math.sin(math.radians(yaw)), math.cos(math.radians(yaw)))
    # model (mx, mz) relative to centre (8,8) px; model -z -> f, model +x -> (-fz, fx)
    pts = []
    for mx in (lo[0], hi[0]):
        for mz in (lo[2], hi[2]):
            ux, uz = (mx - 8) / 16, (mz - 8) / 16
            wx = cx + ux * (-f[1]) + (-uz) * f[0]
            wz = cz + ux * (f[0]) + (-uz) * f[1]
            pts.append((wx, wz))
    y0 = ey + (lo[1] - 8) / 16; y1 = ey + (hi[1] - 8) / 16
    return (min(p[0] for p in pts), y0, min(p[1] for p in pts), max(p[0] for p in pts), y1, max(p[1] for p in pts))

def floating(V):
    solid = {p for p, (b, r) in V.items() if base(b) not in NONSOLID}
    ground = {p for p in solid if p[1] <= 0 and (p[0], p[1] - 1, p[2]) in solid or p[1] < 0}
    seen, q = set(ground), deque(ground)
    while q:
        x, y, z = q.popleft()
        for d in ((1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)):
            n = (x+d[0], y+d[1], z+d[2])
            if n in solid and n not in seen:
                seen.add(n); q.append(n)
    return sorted(solid - seen)

def flood(V, start, bounds, openings):
    solid = {p for p, (b, r) in V.items() if base(b) not in NONSOLID}
    solid |= set(openings)
    seen, q, leaks = {start}, deque([start]), []
    (x0, y0, z0, x1, y1, z1) = bounds
    while q:
        x, y, z = q.popleft()
        for d in ((1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)):
            n = (x+d[0], y+d[1], z+d[2])
            if n in seen or n in solid: continue
            if not (x0 <= n[0] <= x1 and y0 <= n[1] <= y1 and z0 <= n[2] <= z1):
                leaks.append((x, y, z)); continue
            seen.add(n); q.append(n)
    return leaks

def run():
    V = F.build_all()
    fl = floating(V)
    print('floating:', len(fl), fl[:25])
    # cottage: door + windows count as shut (glass/doors are solid already)
    print('cottage leaks:', flood(V, (-24, 2, 0), (-30, 0, -7, -14, 18, 7), [])[:10])
    used = Counter(p[0] for p in F.PIECES)
    print('models unused:', sorted(set(INV) - set(used)))
    print('pieces:', len(F.PIECES), dict(used))
    # pieces: footing and overlaps
    boxes = [(p, piece_box(*p)) for p in F.PIECES]
    solid = {k for k, (b, r) in V.items() if base(b) not in NONSOLID}
    issues = []
    for p, bx in boxes:
        name, x, y, z, yaw = p
        # blocks inside the piece box (shrunk a little) = collision with the build
        hit = []
        for bx_ in range(math.floor(bx[0] + 0.05), math.ceil(bx[3] - 0.05)):
            for by in range(math.floor(bx[1] + 0.05), math.ceil(bx[4] - 0.05)):
                for bz in range(math.floor(bx[2] + 0.05), math.ceil(bx[5] - 0.05)):
                    if (bx_, by, bz) in solid:
                        hit.append((bx_, by, bz, base(V[(bx_, by, bz)][0])))
        if hit:
            issues.append(('inside blocks', name, (x, y, z), hit[:4]))
        # footing: floor pieces need solid under their base
        if INV[name]['bounds'] and bx[1] == math.floor(bx[1]) and (x, int(bx[1]) - 1, z) not in solid and name not in ('hanging_spider', 'bat_bunting', 'cobweb_corner'):
            issues.append(('no footing', name, (x, y, z), int(bx[1]) - 1))
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            a, b = boxes[i][1], boxes[j][1]
            ov = [min(a[3+k], b[3+k]) - max(a[k], b[k]) for k in range(3)]
            if all(o > 0.08 for o in ov) and boxes[i][0][0] != 'iron_fence':
                issues.append(('overlap', boxes[i][0][0], boxes[i][0][1:4], boxes[j][0][0], boxes[j][0][1:4], [round(o, 2) for o in ov]))
    for it in issues: print(*it)
    pal = Counter(base(b) for b, r in V.values() if r not in ('terrain', 'nature', 'light'))
    print('palette:', pal.most_common())
    return V, boxes

if __name__ == '__main__':
    run()
