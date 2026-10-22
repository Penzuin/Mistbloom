"""Store icon, turntable GIF and post image for one October Prompt Props piece (copy of ship/icon.py)."""
import math, sys, importlib
import numpy as np
from PIL import Image
import engine as E

S = 1024
FLOOR_MID = np.array([120, 147, 103.])
FLOOR_EDGE = np.array([70, 96, 64.])
BAND = 9.0
SHADOW = np.array([44, 62, 40.])
SHADOW_A = 0.55


def background(size=S):
    y, x = np.mgrid[0:size, 0:size] / size
    d = np.sqrt((x - 0.55) ** 2 + (y - 0.55) ** 2) / 0.78
    t = np.clip(d, 0, 1) ** 1.6
    img = FLOOR_MID[None, None] * (1 - t[..., None]) + FLOOR_EDGE[None, None] * t[..., None]
    band = ((y > 0.14 + 0.19 * x) & (y < 0.48 + 0.26 * x)) | ((y > 0.66 + 0.16 * x) & (y < 0.70 + 0.16 * x))
    img[band] += BAND
    return np.clip(img, 0, 255)


def compose(m, cam, light, ppu, size, cx, base_y):
    bg = background(size)
    big = m.render(ppu=ppu, cam=cam)
    right, up, fwd = m._cam
    minx, miny = m._origin
    floor_c = np.array([8.0, 0.0, 8.0])
    fx = (floor_c @ right - minx) * ppu + 2
    fy = (-(floor_c @ up) - miny) * ppu + 2
    ox, oy = int(round(cx - fx)), int(round(base_y - fy))
    mk = shadow_mask_offset(m, ppu, light, ox, oy, size)
    out = bg.copy()
    out[mk] = out[mk] * (1 - SHADOW_A) + SHADOW * SHADOW_A
    img = Image.fromarray(out.astype(np.uint8)).convert("RGBA")
    img.alpha_composite(big, (ox, oy))
    return img


def shadow_mask_offset(m, ppu, light, ox, oy, size):
    right, up, fwd = m._cam
    minx, miny = m._origin
    L = np.array(light, float); L /= np.linalg.norm(L)
    mask = np.zeros((size, size), bool)
    sub = 4
    for i, e in enumerate(m.elements):
        for f in e["faces"]:
            w, h = m.face_dims(e, f)
            P, _ = E.texel_world(e, f, w * sub, h * sub)
            u1, v1, u2, v2 = m.uv[(i, f)]
            ty = np.clip(v1 + (np.arange(h * sub) // sub), v1, v2 - 1)
            tx = np.clip(u1 + (np.arange(w * sub) // sub), u1, u2 - 1)
            al = m.atlas[ty[:, None], tx[None, :], 3]
            P = P[al > 128]
            if not len(P):
                continue
            Q = P - L[None] * (P[:, 1:2] / L[1])
            sx = ((Q @ right) - minx) * ppu + 2 + ox
            sy = (-(Q @ up) - miny) * ppu + 2 + oy
            for dx in (0, 0.5):
                for dy in (0, 0.5):
                    xi = np.floor(sx + dx).astype(int); yi = np.floor(sy + dy).astype(int)
                    ok = (xi >= 0) & (xi < size) & (yi >= 0) & (yi < size)
                    mask[yi[ok], xi[ok]] = True
    from scipy import ndimage
    mask = ndimage.binary_closing(mask, structure=np.ones((5, 5)), iterations=2)
    return mask


def rot_y(v, a):
    c, s = math.cos(a), math.sin(a)
    x, y, z = v
    return (c * x + s * z, y, -s * x + c * z)


CAM = (-0.62, 0.62, -1.0)
LIGHT = (-0.95, -1.3, -0.05)


def title_img(path, width):
    t = Image.open(path).convert("RGBA")
    t = t.crop(t.getbbox())
    return t.resize((width, round(t.height * width / t.width)), Image.LANCZOS)


def turntable(m, path, size=640, frames=36, ms=80, ppu=15.5, cx=310, base_y=440):
    imgs = []
    for k in range(frames):
        a = 2 * math.pi * k / frames
        cam, light = rot_y(CAM, a), rot_y(LIGHT, a)
        imgs.append(compose(m, cam, light, ppu, size, cx, base_y).convert("RGB"))
    W = imgs[0].width
    strip = Image.new("RGB", (W, size * len(imgs)))
    for k, im in enumerate(imgs):
        strip.paste(im, (0, k * size))
    pal = strip.quantize(colors=255, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    q = [im.quantize(palette=pal, dither=Image.Dither.NONE) for im in imgs]
    q[0].save(path, save_all=True, append_images=q[1:], duration=ms, loop=0, disposal=1, optimize=False)
    return imgs


if __name__ == "__main__":
    mod = importlib.import_module(sys.argv[1]); title_path = sys.argv[2]; out = sys.argv[3]
    m = mod.build()
    ppu = float(sys.argv[4]) if len(sys.argv) > 4 else 24
    icon = compose(m, CAM, LIGHT, ppu, S, 492, 640)
    t = title_img(title_path, 860)
    icon.alpha_composite(t, ((S - t.width) // 2, 905 - t.height // 2))
    icon.convert("RGB").save(out)
