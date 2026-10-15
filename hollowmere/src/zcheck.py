"""Z-fighting checker/fixer (v2): works in model space with rotations applied.

Two faces fight when they point the same way (or one is a double-sided card), lie within
GAP units of the same plane and overlap. Minecraft's depth buffer can't separate faces a
few hundredths of a unit apart at distance, so "nudged by 0.05" is still a fight - the fix
either deletes a face that is hidden anyway, or opens a real gap.
"""
import importlib, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from shapely.geometry import Polygon

GAP = 0.3          # model units (1/16 block); anything closer is treated as coplanar
MOVE = 0.4         # how far a clashing face or card is pushed
AXIS = {"east": (0, 1), "west": (0, -1), "up": (1, 1), "down": (1, -1), "south": (2, 1), "north": (2, -1)}


def _quads(m):
    import engine as E
    out = []
    for i, e in enumerate(m.elements):
        if e.get("overlay"):
            continue
        for f in e["faces"]:
            cs = [np.array(p, float) for p in E._face_corners(e, f)]
            n = np.array(E._NORMALS[f], float)
            if "rotation" in e:
                r = e["rotation"]
                M = {"x": E._rx, "y": E._ry, "z": E._rz}[r["axis"]](r["angle"])
                o = np.array(r["origin"], float)
                cs = [M @ (p - o) + o for p in cs]
                n = M @ n
            out.append((i, f, cs, n / np.linalg.norm(n), bool(e.get("card"))))
    return out


def _uv(cs, n):
    u = cs[1] - cs[0]; u = u / np.linalg.norm(u)
    v = np.cross(n, u)
    return u, v


def clashes(m):
    q = _quads(m)
    res = []
    for a in range(len(q)):
        ia, fa, ca, na, carda = q[a]
        for b in range(a + 1, len(q)):
            ib, fb, cb, nb, cardb = q[b]
            if ia == ib:
                continue
            d = float(np.dot(na, nb))
            if abs(d) < 0.999 or (d < 0 and not (carda or cardb)):
                continue
            if abs(float(np.dot(na, cb[0] - ca[0]))) > GAP:
                continue
            u, v = _uv(ca, na)
            pa = Polygon([(float(np.dot(p, u)), float(np.dot(p, v))) for p in ca]).convex_hull
            pb = Polygon([(float(np.dot(p, u)), float(np.dot(p, v))) for p in cb]).convex_hull
            ov = pa.intersection(pb).area
            if ov > 0.02:
                res.append(dict(a=ia, fa=fa, b=ib, fb=fb, area=ov, aa=pa.area, ab=pb.area,
                                carda=carda, cardb=cardb, na=na, nb=nb, ca=ca, cb=cb))
    return res


def _inset(e, f, amount):
    ax, d = AXIS[f]
    if d > 0:
        e["to"][ax] = max(e["from"][ax] + 0.05, e["to"][ax] - amount)
    else:
        e["from"][ax] = min(e["to"][ax] - 0.05, e["from"][ax] + amount)


def _candidates(m, c):
    """Possible edits for one clash, as functions that mutate a model copy."""
    out = []
    if c["carda"] or c["cardb"]:
        ci = c["a"] if c["carda"] else c["b"]
        card = m.elements[ci]
        flat = [k for k in range(3) if abs(card["from"][k] - card["to"][k]) < 1e-6][0]
        for amt in (0.4, -0.4, 0.8, -0.8, 1.2, -1.2):
            def mv(mm, ci=ci, flat=flat, amt=amt):
                mm.elements[ci]["from"][flat] += amt; mm.elements[ci]["to"][flat] += amt
            out.append((f"move card el{ci} {amt:+} on {'xyz'[flat]}", mv))
        return out
    small, sf, sa, big, bf = (c["a"], c["fa"], c["aa"], c["b"], c["fb"]) if c["aa"] <= c["ab"] else \
                             (c["b"], c["fb"], c["ab"], c["a"], c["fa"])
    if c["area"] >= 0.9 * sa and len(m.elements[small]["faces"]) > 1:
        out.append((f"drop el{small}.{sf}", lambda mm, i=small, f=sf: mm.elements[i]["faces"].pop(f)))
    # growing a face never opens a see-through seam, so try that before shrinking anything
    for i, f in ((small, sf), (big, bf)):
        out.append((f"grow el{i}.{f}", lambda mm, i=i, f=f: _inset(mm.elements[i], f, -MOVE)))
    for i, f in ((small, sf), (big, bf)):
        out.append((f"inset el{i}.{f}", lambda mm, i=i, f=f: _inset(mm.elements[i], f, MOVE)))
    return out


def _ok(mm, lo, hi, thick):
    """Reject edits that squash a part or push geometry past the model's original outline."""
    for e, t0 in zip(mm.elements, thick):
        for k in range(3):
            t = e["to"][k] - e["from"][k]
            if t0[k] > 1e-6 and t < min(0.5, t0[k]) - 1e-6:
                return False
            if e["from"][k] < lo[k] - 1e-6 or e["to"][k] > hi[k] + 1e-6:
                return False
    return True


def fix(m, verbose=False):
    import copy
    log = []
    lo = [min(e["from"][k] for e in m.elements) for k in range(3)]
    hi = [max(e["to"][k] for e in m.elements) for k in range(3)]
    thick = [[e["to"][k] - e["from"][k] for k in range(3)] for e in m.elements]
    for _ in range(40):
        cl = clashes(m)
        if not cl:
            break
        best = None
        for name, edit in _candidates(m, cl[0]):
            mm = copy.deepcopy(m)
            try:
                edit(mm)
            except Exception:
                continue
            if not _ok(mm, lo, hi, thick):
                continue
            n = len(clashes(mm))
            if best is None or n < best[0]:
                best = (n, name, mm)
            if n == 0:
                break
        if best is None or best[0] >= len(cl):
            if best is None: break
        m.elements = best[2].elements
        log.append(best[1])
        if best[0] >= len(cl) and len(log) > 30:
            break
    if verbose:
        for l in log: print("   ", m.name, l)
        for c in clashes(m): print("   LEFT", m.name, c["a"], c["fa"], c["b"], c["fb"], round(c["area"], 2))
    return m


if __name__ == "__main__":
    tot = 0
    for mod in sys.argv[1:]:
        for m in importlib.import_module(mod).all_models():
            raw = clashes(m)
            fix(m, verbose=bool(os.environ.get("V")))
            left = clashes(m)
            tot += len(left)
            if raw:
                print(f"{mod}.{m.name}: {len(raw)} clashes -> {len(left)} left")
    print("remaining:", tot)
