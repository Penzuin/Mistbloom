"""Find z-fighting: coplanar, overlapping faces that point the same way (or a card lying on another face)."""
import importlib, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
AX = {"east": (0, 1), "west": (0, -1), "up": (1, 1), "down": (1, -1), "south": (2, 1), "north": (2, -1)}
EPS = 0.01

def faces(e):
    for f in e["faces"]:
        a, d = AX[f]
        c = e["to"][a] if d > 0 else e["from"][a]
        o = [i for i in range(3) if i != a]
        yield f, a, d, c, [(e["from"][i], e["to"][i]) for i in o]

def overlap(r1, r2):
    area = 1
    for (a0, a1), (b0, b1) in zip(r1, r2):
        s = min(a1, b1) - max(a0, b0)
        if s <= 0.001: return 0
        area *= s
    return area

def check(m):
    out = []
    els = m.elements
    for i in range(len(els)):
        for j in range(i + 1, len(els)):
            A, B = els[i], els[j]
            if A.get("overlay") or B.get("overlay"): continue
            if A.get("rotation") != B.get("rotation"): continue
            for fa, ax, da, ca, ra in faces(A):
                for fb, bx, db, cb, rb in faces(B):
                    if ax != bx or abs(ca - cb) > EPS: continue
                    card = A.get("card") or B.get("card")
                    if da != db and not card: continue
                    ar = overlap(ra, rb)
                    if ar > 0.01:
                        out.append(f"  {m.name}: el{i} {fa} vs el{j} {fb} @ {'xyz'[ax]}={ca:g} (area {ar:.2f})")
    return out

if __name__ == "__main__":
    tot = 0
    for mod in sys.argv[1:]:
        M = importlib.import_module(mod)
        for m in M.all_models():
            r = check(m); tot += len(r)
            for line in r: print(mod, line)
    print("issues:", tot)


def _vol(e):
    v = 1
    for i in range(3): v *= max(e["to"][i] - e["from"][i], 0.001)
    return v


def fix(m, step=0.05):
    """Resolve every clash: inset the smaller box's clashing face behind the larger one, or lift a card off the face."""
    for _ in range(10):
        clashes = []
        els = m.elements
        for i in range(len(els)):
            for j in range(i + 1, len(els)):
                A, B = els[i], els[j]
                if A.get("overlay") or B.get("overlay") or A.get("rotation") != B.get("rotation"):
                    continue
                for fa, ax, da, ca, ra in faces(A):
                    for fb, bx, db, cb, rb in faces(B):
                        if ax == bx and abs(ca - cb) <= EPS and overlap(ra, rb) > 0.01 and \
                                (da == db or A.get("card") or B.get("card")):
                            clashes.append((A, B, ax, da, db))
        if not clashes:
            return m
        for A, B, ax, da, db in clashes:
            if A.get("card") or B.get("card"):
                c = A if A.get("card") else B                 # nudge the card off the surface
                c["from"][ax] += step; c["to"][ax] += step
            else:
                s = A if _vol(A) < _vol(B) else B             # tuck the smaller part's face in
                if da > 0: s["to"][ax] -= step
                else: s["from"][ax] += step
    return m
