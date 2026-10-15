"""ModelEngine rig: bones + keyframed animations -> Blockbench .bbmodel (generic/free format),
plus a preview renderer that plays the animation the way Blockbench/ModelEngine do
(animation x/y rotations are applied negated, z as-is; bones rotate in ZYX order)."""
import base64, io, json, math, uuid
import numpy as np
from PIL import Image
from engine import face_point
import render as R

NSU = uuid.UUID('6f1c2a7e-0b5d-4c3e-9a7b-2d7e5f0c9a11')
def uid(*k):
    return str(uuid.uuid5(NSU, '/'.join(map(str, k))))

class Bone:
    def __init__(self, name, origin, parent=None):
        self.name, self.origin, self.parent = name, tuple(origin), parent
        self.els = []
        self.anim = {}   # channel -> list of (time, (x,y,z))

    def key(self, channel, frames):
        self.anim[channel] = frames
        return self

class Rig:
    """Elements are engine El objects in engine space (block = 0..16); `shift` moves them into
    entity space (feet at 0, block centre at x=z=0)."""
    def __init__(self, name, model, shift=(-8, 0, -8), length=4.0):
        self.name, self.model, self.shift, self.length = name, model, shift, length
        self.bones = {}

    def bone(self, name, origin, parent=None):
        b = Bone(name, origin, parent); self.bones[name] = b; return b

    def assign(self, rule):
        for e in self.model.els:
            self.bones[rule(e.name)].els.append(e)

    # ------------------------------------------------------------ export
    def bbmodel(self):
        m = self.model
        if not hasattr(m, 'atlas'): m.bake()
        sx, sy, sz = self.shift
        S = m.size
        elements = []
        for e in m.els:
            faces = {}
            for fc in ('north', 'east', 'south', 'west', 'up', 'down'):
                if fc in e.uv:
                    x0, y0, x1, y1 = e.uv[fc]
                    faces[fc] = {'uv': [x0, y0, x1, y1], 'texture': 0}
                else:
                    faces[fc] = {'uv': [0, 0, 0, 0], 'texture': None}
            d = {'name': e.name, 'box_uv': False, 'rescale': False, 'locked': False,
                 'render_order': 'default', 'allow_mirror_modeling': True,
                 'from': [r(e.f[0] + sx), r(e.f[1] + sy), r(e.f[2] + sz)],
                 'to': [r(e.t[0] + sx), r(e.t[1] + sy), r(e.t[2] + sz)],
                 'autouv': 0, 'color': 0, 'origin': [0, 0, 0], 'faces': faces,
                 'type': 'cube', 'uuid': uid(self.name, 'el', e.name)}
            if e.rot:
                ax, ang, org = e.rot
                d['rotation'] = [ang if ax == 'x' else 0, ang if ax == 'y' else 0, ang if ax == 'z' else 0]
                d['origin'] = [r(org[0] + sx), r(org[1] + sy), r(org[2] + sz)]
            elements.append(d)

        def group(b):
            kids = [uid(self.name, 'el', e.name) for e in b.els]
            kids += [group(c) for c in self.bones.values() if c.parent == b.name]
            return {'name': b.name, 'origin': list(b.origin), 'color': 0, 'uuid': uid(self.name, 'bone', b.name),
                    'export': True, 'mirror_uv': False, 'isOpen': True, 'locked': False,
                    'visibility': True, 'autouv': 0, 'children': kids}
        outliner = [group(b) for b in self.bones.values() if b.parent is None]

        buf = io.BytesIO(); Image.fromarray(m.atlas, 'RGBA').save(buf, 'PNG', optimize=True)
        tex = {'path': '', 'name': f'{self.name}.png', 'folder': '', 'namespace': '', 'id': '0',
               'width': S, 'height': S, 'uv_width': S, 'uv_height': S, 'particle': False,
               'render_mode': 'default', 'render_sides': 'auto', 'frame_time': 1,
               'frame_order_type': 'loop', 'frame_order': '', 'frame_interpolate': False,
               'visible': True, 'internal': True, 'saved': False, 'uuid': uid(self.name, 'tex'),
               'relative_path': '', 'source': 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode()}
        animators = {}
        for b in self.bones.values():
            if not b.anim: continue
            kfs = []
            for ch, frames in b.anim.items():
                for t, (x, y, z) in frames:
                    kfs.append({'channel': ch, 'data_points': [{'x': r(x), 'y': r(y), 'z': r(z)}],
                                'uuid': uid(self.name, b.name, ch, t), 'time': r(t), 'color': -1,
                                'interpolation': 'linear'})
            animators[uid(self.name, 'bone', b.name)] = {'name': b.name, 'type': 'bone', 'keyframes': kfs}
        anim = {'uuid': uid(self.name, 'idle'), 'name': 'idle', 'loop': 'loop', 'override': False,
                'length': self.length, 'snapping': 20, 'selected': False, 'anim_time_update': '',
                'blend_weight': '', 'start_delay': '', 'loop_delay': '', 'animators': animators}
        return {'meta': {'format_version': '4.10', 'model_format': 'free', 'box_uv': False},
                'name': self.name, 'model_identifier': '', 'visible_box': [1, 1, 0],
                'variable_placeholders': '', 'variable_placeholder_buttons': [],
                'timeline_setups': [], 'unhandled_root_fields': {},
                'resolution': {'width': S, 'height': S},
                'elements': elements, 'outliner': outliner, 'textures': [tex], 'animations': [anim]}

    # ------------------------------------------------------------ playback
    def sample(self, b, ch, t):
        fr = b.anim.get(ch)
        if not fr: return (0.0, 0.0, 0.0)
        t = t % self.length
        for (t0, v0), (t1, v1) in zip(fr, fr[1:]):
            if t0 <= t <= t1:
                f = (t - t0) / (t1 - t0) if t1 > t0 else 0
                return tuple(a + (c - a) * f for a, c in zip(v0, v1))
        return fr[-1][1]

    def bone_fn(self, name, t):
        """returns function mapping a point (entity space) through this bone and its parents."""
        b = self.bones[name]
        rx, ry, rz = self.sample(b, 'rotation', t)
        px, py, pz = self.sample(b, 'position', t)
        a, bb, c = math.radians(-rx), math.radians(-ry), math.radians(rz)
        Rx = np.array([[1, 0, 0], [0, math.cos(a), -math.sin(a)], [0, math.sin(a), math.cos(a)]])
        Ry = np.array([[math.cos(bb), 0, math.sin(bb)], [0, 1, 0], [-math.sin(bb), 0, math.cos(bb)]])
        Rz = np.array([[math.cos(c), -math.sin(c), 0], [math.sin(c), math.cos(c), 0], [0, 0, 1]])
        M = Rz @ Ry @ Rx   # three.js 'ZYX' order
        o = np.array(b.origin, float); off = np.array([px, py, pz])
        parent = self.bone_fn(b.parent, t) if b.parent else (lambda p: p)
        return lambda p: parent(o + M @ (np.asarray(p, float) - o) + off)

    def posed(self, t, scene=None):
        m = self.model
        if not hasattr(m, 'atlas'): m.bake()
        sx, sy, sz = self.shift
        out = []
        for b in self.bones.values():
            fn = self.bone_fn(b.name, t)
            for e in b.els:
                for fc in e.faces():
                    pts = []
                    for u, v in ((0, 0), (1, 0), (1, 1), (0, 1)):
                        p = R._rot(face_point(fc, e.f, e.t, u, v), e.rot)
                        pts.append(fn((p[0] + sx, p[1] + sy, p[2] + sz)))
                    out.append((np.array(pts), e.uv[fc], 0))
        if scene is not None:
            sm, (ox, oy, oz) = scene
            for e in sm.els:
                for fc in e.faces():
                    pts = [R._rot(face_point(fc, e.f, e.t, u, v), e.rot) for u, v in ((0, 0), (1, 0), (1, 1), (0, 1))]
                    out.append((np.array(pts) + np.array([ox, oy, oz]), e.uv[fc], 1))
        return out

    def gif2(self, path, fps=10, scene=None, yaw=35, pitch=32, scale=10, pad=8):
        n = int(round(self.length * fps))
        atlases = [self.model.atlas] + ([scene[0].atlas] if scene else [])
        posed = [self.posed(i / fps, scene) for i in range(n)]
        a, p = math.radians(yaw), math.radians(pitch)
        cdir = np.array([math.cos(p) * math.sin(a), math.sin(p), math.cos(p) * math.cos(a)])
        right = np.array([math.cos(a), 0, -math.sin(a)]); up = np.cross(cdir, right)
        xs = [P @ right * scale for fr in posed for P, _, _ in fr]; ys = [-(P @ up) * scale for fr in posed for P, _, _ in fr]
        xs = np.concatenate(xs); ys = np.concatenate(ys)
        bounds = (xs.min(), xs.max(), ys.min(), ys.max())
        frames = []
        for fr in posed:
            im = render_multi(fr, atlases, yaw, pitch, scale, pad, bounds)
            bg = Image.new('RGBA', im.size, (198, 198, 198, 255)); bg.alpha_composite(im)
            frames.append(bg.convert('P', palette=Image.ADAPTIVE))
        frames[0].save(path, save_all=True, append_images=frames[1:], duration=int(1000 / fps), loop=0)
        return frames

    def frame(self, t, yaw=35, pitch=28, scale=10, pad=10, bounds=None):
        """Render one animation frame. Reuses render.render via a temporary posed model."""
        m = self.model
        if not hasattr(m, 'atlas'): m.bake()
        posed = []
        sx, sy, sz = self.shift
        for b in self.bones.values():
            fn = self.bone_fn(b.name, t)
            for e in b.els:
                for fc in e.faces():
                    pts = []
                    for u, v in ((0, 0), (1, 0), (1, 1), (0, 1)):
                        p = R._rot(face_point(fc, e.f, e.t, u, v), e.rot)
                        p = (p[0] + sx, p[1] + sy, p[2] + sz)
                        pts.append(fn(p))
                    posed.append((np.array(pts), e.uv[fc]))
        return render_quads(posed, m.atlas, yaw, pitch, scale, pad, bounds)

    def gif(self, path, fps=12, **k):
        n = int(self.length * fps)
        # fixed bounds so the camera doesn't jump
        frames = [self.frame(i / fps, **k) for i in range(n)]
        W = max(f.width for f in frames); H = max(f.height for f in frames)
        out = []
        for f in frames:
            bg = Image.new('RGBA', (W, H), (198, 198, 198, 255))
            bg.alpha_composite(f, ((W - f.width) // 2, (H - f.height) // 2))
            out.append(bg.convert('P', palette=Image.ADAPTIVE))
        out[0].save(path, save_all=True, append_images=out[1:], duration=int(1000 / fps), loop=0)
        return frames

def r(v):
    v = round(float(v), 3)
    return int(v) if v == int(v) else v

def render_quads(quads, atlas, yaw, pitch, scale, pad, bounds, ss=2):
    """Minimal copy of render.render working on already-posed world quads."""
    class Fake: pass
    tex = atlas.astype(float)
    a, p = math.radians(yaw), math.radians(pitch)
    cdir = np.array([math.cos(p) * math.sin(a), math.sin(p), math.cos(p) * math.cos(a)])
    right = np.array([math.cos(a), 0, -math.sin(a)]); up = np.cross(cdir, right)
    s = scale * ss
    q2 = []
    for P, uv in quads:
        q2.append((P @ right * s, -(P @ up) * s, P @ cdir, uv))
    if bounds is None:
        allx = np.concatenate([q[0] for q in q2]); ally = np.concatenate([q[1] for q in q2])
        bounds = (allx.min(), allx.max(), ally.min(), ally.max())
    else:
        bounds = tuple(v * ss for v in bounds)
    ox, oy = -bounds[0] + pad * ss, -bounds[2] + pad * ss
    W = int(bounds[1] - bounds[0] + 2 * pad * ss) + 1; H = int(bounds[3] - bounds[2] + 2 * pad * ss) + 1
    img = np.zeros((H, W, 4)); zb = np.full((H, W), -1e9); trans = []
    uvp = [(0, 0), (1, 0), (1, 1), (0, 1)]
    for sx, sy, d, uv in q2:
        sx = sx + ox; sy = sy + oy
        for tri in ((0, 1, 2), (0, 2, 3)):
            X = sx[list(tri)]; Y = sy[list(tri)]; D = d[list(tri)]
            UV = np.array([uvp[i] for i in tri], float)
            x0, x1 = int(max(0, math.floor(X.min()))), int(min(W - 1, math.ceil(X.max())))
            y0, y1 = int(max(0, math.floor(Y.min()))), int(min(H - 1, math.ceil(Y.max())))
            if x1 < x0 or y1 < y0: continue
            den = (Y[1] - Y[2]) * (X[0] - X[2]) + (X[2] - X[1]) * (Y[0] - Y[2])
            if abs(den) < 1e-9: continue
            yy, xx = np.mgrid[y0:y1 + 1, x0:x1 + 1] + 0.5
            l0 = ((Y[1] - Y[2]) * (xx - X[2]) + (X[2] - X[1]) * (yy - Y[2])) / den
            l1 = ((Y[2] - Y[0]) * (xx - X[2]) + (X[0] - X[2]) * (yy - Y[2])) / den
            l2 = 1 - l0 - l1
            m = (l0 >= -1e-6) & (l1 >= -1e-6) & (l2 >= -1e-6)
            if not m.any(): continue
            z = l0 * D[0] + l1 * D[1] + l2 * D[2]
            fu = l0 * UV[0, 0] + l1 * UV[1, 0] + l2 * UV[2, 0]
            fv = l0 * UV[0, 1] + l1 * UV[1, 1] + l2 * UV[2, 1]
            u0, v0, u1, v1 = uv
            px = np.clip((u0 + fu * (u1 - u0)).astype(int), u0, u1 - 1)
            py = np.clip((v0 + fv * (v1 - v0)).astype(int), v0, v1 - 1)
            col = tex[py, px]; al = col[..., 3]
            sub = (slice(y0, y1 + 1), slice(x0, x1 + 1))
            op = m & (al >= 250) & (z > zb[sub])
            img[sub][op] = col[op]; zb[sub][op] = z[op]
            semi = m & (al > 8) & (al < 250)
            if semi.any(): trans.append((float(D.mean()), sub, semi, z, col))
    trans.sort(key=lambda t: t[0])
    for _, sub, semi, z, col in trans:
        vis = semi & (z > zb[sub]); a_ = col[..., 3:4] / 255.0
        dst = img[sub]; bl = dst.copy()
        bl[..., :3] = dst[..., :3] * (1 - a_) + col[..., :3] * a_
        bl[..., 3] = np.maximum(dst[..., 3], col[..., 3] + dst[..., 3] * (1 - a_[..., 0]))
        dst[vis] = bl[vis]
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), 'RGBA')
    return im.resize((W // ss, H // ss), Image.BOX)

def wave(n, amp, period, phase=0.0, base=0.0):
    """n+1 evenly spaced (t, value) samples of a sine over one period"""
    return [(period * i / n, base + amp * math.sin(2 * math.pi * i / n + phase)) for i in range(n + 1)]

def rot_keys(length, x=None, y=None, z=None, n=16):
    """combine per-axis (amp, cycles, phase, base) sines into rotation keyframes over the loop."""
    out = []
    for i in range(n + 1):
        t = length * i / n
        v = []
        for ax in (x, y, z):
            if ax is None: v.append(0.0); continue
            amp, cyc, ph, base = ax
            v.append(base + amp * math.sin(2 * math.pi * cyc * i / n + ph))
        out.append((t, tuple(v)))
    return out


def render_multi(quads, atlases, yaw, pitch, scale, pad, bounds):
    """render quads that may sample from different atlases (koi rig + furniture scene)."""
    # pack the atlases side by side into one texture, offsetting uvs
    H = max(a.shape[0] for a in atlases); W = sum(a.shape[1] for a in atlases)
    big = np.zeros((H, W, 4), np.uint8); offs = []; x = 0
    for a in atlases:
        big[:a.shape[0], x:x + a.shape[1]] = a; offs.append(x); x += a.shape[1]
    q = [(P, (uv[0] + offs[k], uv[1], uv[2] + offs[k], uv[3])) for P, uv, k in quads]
    return render_quads(q, big, yaw, pitch, scale, pad, bounds)
