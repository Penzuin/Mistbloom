"""Store icon / post image for one October Prompt Props piece (matches Day 1). No GIF."""
import sys, importlib
import numpy as np
from PIL import Image
import engine as E

S = 1024
FLOOR_MID = np.array([120, 147, 103.]); FLOOR_EDGE = np.array([70, 96, 64.])
BAND = 9.0; SHADOW = np.array([44, 62, 40.]); SHADOW_A = 0.55
CAM = (-0.62, 0.62, -1.0); LIGHT = (-0.95, -1.3, -0.05)

def background(size=S):
    y, x = np.mgrid[0:size, 0:size] / size
    t = np.clip(np.sqrt((x - 0.55) ** 2 + (y - 0.55) ** 2) / 0.78, 0, 1) ** 1.6
    img = FLOOR_MID[None, None] * (1 - t[..., None]) + FLOOR_EDGE[None, None] * t[..., None]
    band = ((y > 0.14 + 0.19 * x) & (y < 0.48 + 0.26 * x)) | ((y > 0.66 + 0.16 * x) & (y < 0.70 + 0.16 * x))
    img[band] += BAND
    return np.clip(img, 0, 255)

def shadow_mask(m, ppu, light, ox, oy, size):
    right, up, fwd = m._cam; minx, miny = m._origin
    L = np.array(light, float); L /= np.linalg.norm(L)
    mask = np.zeros((size, size), bool); sub = 4
    for i, e in enumerate(m.elements):
        for f in e["faces"]:
            w, h = m.face_dims(e, f)
            P, _ = E.texel_world(e, f, w * sub, h * sub)
            u1, v1, u2, v2 = m.uv[(i, f)]
            ty = np.clip(v1 + (np.arange(h * sub) // sub), v1, v2 - 1)
            tx = np.clip(u1 + (np.arange(w * sub) // sub), u1, u2 - 1)
            P = P[m.atlas[ty[:, None], tx[None, :], 3] > 128]
            if not len(P): continue
            Q = P - L[None] * (P[:, 1:2] / L[1])
            sx = ((Q @ right) - minx) * ppu + 2 + ox; sy = (-(Q @ up) - miny) * ppu + 2 + oy
            for dx in (0, 0.5):
                for dy in (0, 0.5):
                    xi = np.floor(sx + dx).astype(int); yi = np.floor(sy + dy).astype(int)
                    ok = (xi >= 0) & (xi < size) & (yi >= 0) & (yi < size)
                    mask[yi[ok], xi[ok]] = True
    from scipy import ndimage
    return ndimage.binary_closing(mask, structure=np.ones((5, 5)), iterations=2)

def compose(m, ppu, cx, base_y, size=S):
    big = m.render(ppu=ppu, cam=CAM)
    right, up, fwd = m._cam; minx, miny = m._origin
    fc = np.array([8.0, 0.0, 8.0])
    ox = int(round(cx - ((fc @ right - minx) * ppu + 2))); oy = int(round(base_y - ((-(fc @ up) - miny) * ppu + 2)))
    out = background(size); mk = shadow_mask(m, ppu, LIGHT, ox, oy, size)
    out[mk] = out[mk] * (1 - SHADOW_A) + SHADOW * SHADOW_A
    img = Image.fromarray(out.astype(np.uint8)).convert("RGBA"); img.alpha_composite(big, (ox, oy))
    return img

if __name__ == "__main__":
    m = importlib.import_module(sys.argv[1]).build(); out = sys.argv[2]; ppu = float(sys.argv[3])
    icon = compose(m, ppu, 492, 640)
    if len(sys.argv) > 4:
        t = Image.open(sys.argv[4]).convert("RGBA"); t = t.crop(t.getbbox())
        t = t.resize((860, round(t.height * 860 / t.width)), Image.LANCZOS)
        icon.alpha_composite(t, ((S - t.width) // 2, 905 - t.height // 2))
    icon.convert("RGB").save(out)
