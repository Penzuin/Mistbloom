"""Find faces that z-fight: two faces of different elements facing the same way, on (almost) the same
plane, overlapping in area. Works on the compiled model units with rotations applied."""
import sys, itertools, numpy as np
from engine import _face_corners, _rx, _ry, _rz
from shapely.geometry import Polygon

NORM = {"north": (0, 0, -1), "south": (0, 0, 1), "east": (1, 0, 0), "west": (-1, 0, 0), "up": (0, 1, 0), "down": (0, -1, 0)}

def quads(m, names=None):
    out = []
    for i, e in enumerate(m.elements):
        for f in e["faces"]:
            cs = [np.array(p, float) for p in _face_corners(e, f)]
            n = np.array(NORM[f], float)
            if "rotation" in e:
                r = e["rotation"]; M = {"x": _rx, "y": _ry, "z": _rz}[r["axis"]](r["angle"]); o = np.array(r["origin"])
                cs = [M @ (p - o) + o for p in cs]; n = M @ n
            out.append((i, f, cs, n, len(e["faces"]) == 2))
    return out

def check(m, gap=0.12, label=lambda i: str(i)):
    Q = quads(m); hits = []
    for (i, f, A, na, ca), (j, g, B, nb, cb) in itertools.combinations(Q, 2):
        if i == j: continue
        dot = float(na @ nb)
        if abs(abs(dot) - 1) > 1e-3: continue
        d = abs(float((B[0] - A[0]) @ na))
        if d > gap: continue
        u = A[1] - A[0]; u /= np.linalg.norm(u); v = np.cross(na, u)
        pa = Polygon([(float((p - A[0]) @ u), float((p - A[0]) @ v)) for p in A])
        pb = Polygon([(float((p - A[0]) @ u), float((p - A[0]) @ v)) for p in B])
        a = pa.intersection(pb).area
        if a > 1e-3:
            hits.append((label(i), f, label(j), g, round(d, 3), round(a, 2), "same" if dot > 0 else "opposite"))
    return hits

if __name__ == "__main__":
    import pieces
    for name in sys.argv[1:]:
        m = getattr(pieces, name)()
        for h in check(m):
            if h[6] == "same": print(name, h)
