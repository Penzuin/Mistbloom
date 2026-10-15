"""Moonlit Ballroom showcase film: 11 MistCam shots written straight into scenes.yml.
Coordinates are local to the hall origin O (x across, y up, z from the gate to the stage)."""
import math, sys
sys.path.insert(0, "/home/claude/ghostball")
from hall import O

def w(p):
    return (O[0] + p[0], O[1] + p[1], O[2] + p[2])

def aim(cam, tgt):
    dx, dy, dz = tgt[0] - cam[0], tgt[1] - cam[1], tgt[2] - cam[2]
    yaw = math.degrees(math.atan2(-dx, dz))
    pitch = -math.degrees(math.atan2(dy, math.hypot(dx, dz)))
    return yaw, pitch

# name, look-at target (local), [(camera local, seconds to next, easing)], closed, purpose
SHOTS = []
def shot(name, tgt, pts, purpose, closed=False):
    SHOTS.append((name, tgt, pts, closed, purpose))

shot("ball-01-island", (0.5, 9, 6), [((-32, 24, -28), 4, "ease-in"), ((-22, 17, -38), 4, "ease-out"), ((-7, 10, -31), 1, "linear")],
     "Wide establishing drift: the floating isle and the hall in the night sky")
shot("ball-02-gate", (0.5, 2.6, -5.5), [((-1.2, 3.4, -26), 7, "ease-in-out"), ((-0.6, 2.5, -12.2), 1, "linear")],
     "Push in low along the path, through the gate, toward the tower door")
shot("ball-03-lantern", (3.5, 2.5, -12.5), [((1.6, 2.9, -15.2), 5, "ease-in-out"), ((1.6, 2.9, -10.2), 1, "linear")],
     "Slide past a Ghost Lantern on its plinth (product close-up)")
shot("ball-04-doorway", (0.5, 1.7, 11.5), [((0.5, 2.6, -5.4), 6, "ease-in-out"), ((0.5, 2.9, 3.5), 1, "linear")],
     "Through the vestibule and the passage: the dance floor reveal")
orbit = []
for i in range(12):
    a = math.radians(-90 + i * 30)
    orbit.append(((0.5 + 3.6 * math.cos(a), 3.4, 11.5 + 3.6 * math.sin(a)), 1, "linear"))
shot("ball-05-waltz-orbit", (0.5, 1.8, 11.5), orbit, "Full circle around the couple on the amethyst medallion (12 s, loops)", closed=True)
shot("ball-06-couple", (-2.5, 1.6, 15.5), [((-3.6, 2.1, 12.0), 6, "ease-in-out"), ((-0.4, 2.1, 12.9), 1, "linear")],
     "Low tracking shot past a waltzing couple (product close-up)")
shot("ball-07-portrait", (-4.7, 4.5, 8.5), [((-0.8, 4.3, 6.4), 5, "ease-in-out"), ((-0.8, 4.3, 10.6), 1, "linear")],
     "Slide along the west wall on Lady Wispwell's portrait")
shot("ball-08-stage", (0.5, 2.9, 22.5), [((0.5, 2.6, 13.5), 7, "ease-out"), ((0.5, 3.0, 18.3), 1, "linear")],
     "Glide up the hall to the Ghost Pianist and the candelabras")
shot("ball-09-candelabra", (-3.5, 2.9, 21.5), [((-4.2, 3.1, 19.4), 3, "ease-in"), ((-3.0, 3.2, 18.9), 3, "ease-out"), ((-1.6, 3.1, 19.8), 1, "linear")],
     "Slow arc around a lit Floating Candelabra on the stage (product close-up)")
shot("ball-10-back", (0.5, 7, 24), [((11, 4, 36), 8, "ease-in-out"), ((7, 15, 40), 1, "linear")],
     "Outside, rising past the moon window and the roof")
shot("ball-11-goodnight", (0.5, 2.6, 22.5), [((0.5, 4.2, 17.0), 9, "ease-in-out"), ((0.5, 3.0, 0.5), 1, "linear")],
     "Dolly back down the hall past the dancers and out through the doorway (end card)")

def yaml_out():
    L = ["scenes:"]
    total = 0
    for name, tgt, pts, closed, _ in SHOTS:
        T = w(tgt)
        L += [f"  {name}:", "    world: world", f"    closed: {'true' if closed else 'false'}",
              f"    look-at: {T[0]:.4f} {T[1]:.4f} {T[2]:.4f}", "    points:"]
        for k, (c, sec, ease) in enumerate(pts):
            C = w(c)
            yaw, pitch = aim(C, T)
            ticks = int(round(sec * 20))
            if closed or k < len(pts) - 1:
                total += ticks
            L.append(f"    - {C[0]:.4f} {C[1]:.4f} {C[2]:.4f} {yaw:.3f} {pitch:.3f} {ticks} {ease}")
    return "\n".join(L) + "\n", total

def durations():
    out = []
    for name, tgt, pts, closed, purpose in SHOTS:
        segs = pts if closed else pts[:-1]
        out.append((name, sum(int(round(s * 20)) for _, s, _ in segs) / 20, purpose))
    return out

if __name__ == "__main__":
    y, total = yaml_out()
    open(sys.argv[1] if len(sys.argv) > 1 else "scenes.yml", "w").write(y)
    for n, s, p in durations():
        print(f"{n:22s} {s:5.1f}s  {p}")
    print("total", total / 20, "s")
