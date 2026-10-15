import sys, math
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
import festival as F, shots as S, checks as C, render as R

def box_dist(p, lo, hi):
    d = [max(lo[k] - p[k], 0, p[k] - hi[k]) for k in range(3)]
    return math.sqrt(sum(v * v for v in d))

def clearance(p, V, pboxes):
    best, what = 9.0, None
    bx, by, bz = math.floor(p[0]), math.floor(p[1]), math.floor(p[2])
    for x in range(bx - 1, bx + 2):
        for y in range(by - 1, by + 2):
            for z in range(bz - 1, bz + 2):
                b = V.get((x, y, z))
                if not b: continue
                for lo, hi in R.shapes(b[0]):
                    d = box_dist(p, (x + lo[0], y + lo[1], z + lo[2]), (x + hi[0], y + hi[1], z + hi[2]))
                    if d < best: best, what = d, C.base(b[0])
    for (name, *_), bb in pboxes:
        d = box_dist(p, bb[:3], bb[3:])
        if d < best: best, what = d, name
    return best, what

def run():
    V = F.build_all()
    pboxes = [(p, C.piece_box(*p)) for p in F.PIECES]
    frames = S.bake()
    ok = True
    for name, fr in frames.items():
        worst = min(((clearance(f[:3], V, pboxes), i) for i, f in enumerate(fr)), key=lambda t: t[0][0])
        (d, what), i = worst
        flag = '' if d >= 0.35 else '  <-- TOO CLOSE'
        if d < 0.35: ok = False
        print(f"{name:20s} {len(fr)/20:5.1f}s  min clearance {d:4.2f} ({what}) at frame {i}{flag}")
    return frames, ok

if __name__ == '__main__':
    run()
