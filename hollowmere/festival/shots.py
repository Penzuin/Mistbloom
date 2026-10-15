"""Halloween Festival film: 11 MistCam shots in festival-local coordinates.
Each point: (camera xyz, seconds to the next point, easing, aim xyz or None).
A shot either locks the lens on one target (look) or aims each point at its own target."""
import math, sys, json, subprocess
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
import festival as F

def aim(cam, tgt):
    dx, dy, dz = tgt[0] - cam[0], tgt[1] - cam[1], tgt[2] - cam[2]
    return math.degrees(math.atan2(-dx, dz)), -math.degrees(math.atan2(dy, math.hypot(dx, dz)))

SHOTS = []
def shot(name, pts, purpose, look=None, closed=False):
    SHOTS.append(dict(name=name, pts=pts, purpose=purpose, look=look, closed=closed))

lx = F.lane_x
cat = (lx(-21) - 3 + 0.5, 1.45, -22 + 0.5)
BFX, BFZ = F.BF

shot("hf-01-arrival", [((-46, 30, -78), 4.5, "ease-in", None), ((-30, 20, -64), 4.5, "ease-out", None), ((-16, 12, -56), 1, "linear", None)],
     "Wide establishing drift: the festival island glowing in the night sky", look=(0.5, 2, -6))
shot("hf-02-gate", [((0.5, 2.0, -46), 7, "ease-in-out", None), ((0.5, 2.6, -37.2), 1, "linear", None)],
     "Low push up the entry path to the Hollow Arch and the welcome sign", look=(0.5, 2.2, -32.5))
lane = []
for z, sec in ((-31.5, 2.6), (-25.5, 2.6), (-19.0, 2.8), (-12.5, 1)):
    x = lx(int(z)) + 0.5
    lane.append(((x, 2.3, z), sec, "linear", (lx(int(z) + 7) + 0.5, 1.9, z + 7)))
lane[0] = (lane[0][0], lane[0][1], "ease-in", lane[0][3])
lane[2] = (lane[2][0], lane[2][1], "ease-out", lane[2][3])
shot("hf-03-lane", lane, "Dolly down the lantern lane under the bat bunting, between the pumpkin lamp posts")
arc = []
for k, a in enumerate((-65, -35, -5, 25)):
    r = math.radians(a)
    arc.append(((cat[0] + 2.4 * math.cos(r), 1.8, cat[2] + 2.4 * math.sin(r)), 1.7 if k < 3 else 1, "linear", None))
shot("hf-04-cat", arc, "Slow arc round the black cat on the hay bale seat (product close-up)", look=cat)
orb = []
for k in range(7):
    a = math.radians(30 + k * 30)
    orb.append(((BFX + 0.5 + 6.2 * math.cos(a), 3.2, BFZ + 0.5 + 6.2 * math.sin(a)), 1.4 if k < 6 else 1, "linear", None))
shot("hf-05-bonfire", orb, "Half orbit round the bonfire and its hay bale circle", look=(BFX + 0.5, 1.4, BFZ + 0.5))
mk = []
for k in range(12):
    a = math.radians(-90 + k * 30)
    mk.append(((0.5 + 4.2 * math.cos(a), 2.7, 0.5 + 4.2 * math.sin(a)), 1, "linear", None))
shot("hf-06-market-orbit", mk, "Full orbit round the bubbling cauldron, the three potion stalls turning behind it (loops)",
     look=(0.5, 1.35, 0.5), closed=True)
f = (math.sqrt(0.5), math.sqrt(0.5))            # the purple stall at (-6,-6) faces (+x,+z)
c0 = (-5.5 + f[0] * 3.1, -5.5 + f[1] * 3.1)
side = (f[1], -f[0])
shot("hf-07-stall", [((c0[0] + side[0] * 2.2, 2.0, c0[1] + side[1] * 2.2), 5, "ease-in-out", None),
                     ((c0[0] - side[0] * 2.2, 2.0, c0[1] - side[1] * 2.2), 1, "linear", None)],
     "Slide across the front of the plum potion stall (product close-up)", look=(-5.5, 1.7, -5.5))
shot("hf-08-witch", [((-10.0, 3.0, 3.0), 7, "ease-in-out", None), ((-13.6, 2.5, 1.4), 1, "linear", None)],
     "Push in on the witch's porch: lectern, crystal ball, broom and hat stand", look=(-18.3, 1.9, 0.2))
shot("hf-09-graveyard", [((19.6, 1.7, -10.0), 4, "ease-in", None), ((19.6, 1.9, 0.5), 4, "ease-out", None), ((19.6, 1.8, 9.8), 1, "linear", None)],
     "Low dolly between the rows of graves, the ruined chapel holding steady behind them", look=(24.5, 2.4, 0.5))
shot("hf-10-patch", [((-3.5, 2.6, 19.5), 4, "ease-in", (-6.5, 2.4, 23.5)), ((0.5, 6.5, 16.5), 4, "ease-out", (-3, 2.2, 28)),
                     ((0.5, 12.5, 15.5), 1, "linear", (0.5, 4.5, 36))],
     "Crane up from the scarecrow over the pumpkin patch to the barn")
shot("hf-11-goodnight", [((0.5, 4.2, -5.5), 5, "ease-in", (0.5, 1.6, 0.5)), ((0.5, 8.5, -30), 5, "ease-out", (0.5, 2, -4)),
                         ((0.5, 22, -62), 1, "linear", (0.5, 3, -2))],
     "Pull back from the cauldron, up the lane and out past the gate, rising away from the island (end card)")

def scene_lines(local=True):
    """MistCam scene text; local=True for the bake harness, else world coordinates."""
    O = (0, 0, 0) if local else F.O
    out = []
    for s in SHOTS:
        hdr = f"scene {s['name']} {'true' if s['closed'] else 'false'}"
        if s['look']:
            L = s['look']; hdr += f" {L[0] + O[0]:.4f} {L[1] + O[1]:.4f} {L[2] + O[2]:.4f}"
        out.append(hdr)
        for (c, sec, ease, tgt) in s['pts']:
            yaw, pitch = aim(c, tgt or s['look'])
            out.append(f"pt {c[0] + O[0]:.4f} {c[1] + O[1]:.4f} {c[2] + O[2]:.4f} {yaw:.3f} {pitch:.3f} {int(round(sec * 20))} {ease}")
    return out

def bake():
    open('/home/claude/festival/bake/shots.txt', 'w').write("\n".join(scene_lines()) + "\n")
    SP = '/tmp/claude-0/-home-claude/9f7f58b1-a823-586e-b665-a3c618f69e70/scratchpad'
    subprocess.run(['java', '-cp', f'/home/claude/mistcam/build/classes:{SP}/stubout:/home/claude/festival/bake', 'Bake',
                    '/home/claude/festival/bake/shots.txt', '/home/claude/festival/bake/frames.txt'], check=True, capture_output=True)
    frames = {}
    for line in open('/home/claude/festival/bake/frames.txt'):
        n, i, x, y, z, yaw, pitch = line.split()
        frames.setdefault(n, []).append((float(x), float(y), float(z), float(yaw), float(pitch)))
    return frames

def yaml_scenes():
    L = []
    for s in SHOTS:
        L += [f"  {s['name']}:", "    world: world", f"    closed: {'true' if s['closed'] else 'false'}"]
        if s['look']:
            T = [s['look'][k] + F.O[k] for k in range(3)]
            L.append(f"    look-at: {T[0]:.4f} {T[1]:.4f} {T[2]:.4f}")
        L.append("    points:")
        for (c, sec, ease, tgt) in s['pts']:
            yaw, pitch = aim(c, tgt or s['look'])
            W = [c[k] + F.O[k] for k in range(3)]
            L.append(f"    - {W[0]:.4f} {W[1]:.4f} {W[2]:.4f} {yaw:.3f} {pitch:.3f} {int(round(sec * 20))} {ease}")
    return L

def durations():
    out = []
    for s in SHOTS:
        segs = s['pts'] if s['closed'] else s['pts'][:-1]
        out.append((s['name'], sum(int(round(p[1] * 20)) for p in segs) / 20, s['purpose']))
    return out
