"""Store icon, turntable GIF and post image for one October Prompt Props piece.
Matches Day 1 (Toffee Apples): sage floor with soft corner falloff and two hard light bands,
hard texel shadow falling right, piece large, Title Generator title at the bottom."""
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


def shadow_mask(m, cam, ppu, light, img_size):
    """Project every opaque texel onto the floor (y = 0) along the light, in the render's screen space."""
    right, up, fwd = m._cam
    minx, miny = m._origin
    L = np.array(light, float); L /= np.linalg.norm(L)
    H, W = img_size[1], img_size[0]
    mask = np.zeros((H, W), bool)
    for i, e in enumerate(m.elements):
        for f in e["faces"]:
            w, h = m.face_dims(e, f)
            sub = 4
            P, _ = E.texel_world(e, f, w * sub, h * sub)
            u1, v1, u2, v2 = m.uv[(i, f)]
            ty = np.clip(v1 + (np.arange(h * sub) // sub), v1, v2 - 1)
            tx = np.clip(u1 + (np.arange(w * sub) // sub), u1, u2 - 1)
            al = m.atlas[ty[:, None], tx[None, :], 3]
            P = P[al > 128]
            if not len(P):
                continue
            Q = P - L[None] * (P[:, 1:2] / L[1])
            sx = ((Q @ right) - minx) * ppu + 2
            sy = (-(Q @ up) - miny) * ppu + 2
            for ox in (0, 0.5):
                for oy in (0, 0.5):
                    xi = np.floor(sx + ox).astype(int); yi = np.floor(sy + oy).astype(int)
                    ok = (xi >= 0) & (xi < W) & (yi >= 0) & (yi < H)
                    mask[yi[ok], xi[ok]] = True
    return mask


def scene(m, cam, ppu, light, size, cx, base_y, pad=400):
    """Floor + shadow + piece. The piece's footprint centre lands at (cx, base_y)."""
    big = m.render(ppu=ppu, cam=cam)
    W, H = big.width + 2 * pad, big.height + 2 * pad
    canvas = Image.new("RGBA", (W, H))
    canvas.alpha_composite(big, (pad, pad))
    mk = shadow_mask(m, cam, ppu, light, (big.width, big.height))
    # widen shadow canvas so the shadow can leave the piece's box
    m_full = np.zeros((H, W), bool)
    # re-project into the padded canvas
    right, up, fwd = m._cam
    minx, miny = m._origin
    floor_c = np.array([8.0, 0.0, 8.0])
    fx = (floor_c @ right - minx) * ppu + 2 + pad
    fy = (-(floor_c @ up) - miny) * ppu + 2 + pad
    return canvas, mk, (fx, fy), pad


def compose(m, cam, light, ppu, size, cx, base_y):
    bg = background(size)
    big = m.render(ppu=ppu, cam=cam)
    right, up, fwd = m._cam
    minx, miny = m._origin
    floor_c = np.array([8.0, 0.0, 8.0])
    fx = (floor_c @ right - minx) * ppu + 2
    fy = (-(floor_c @ up) - miny) * ppu + 2
    ox, oy = int(round(cx - fx)), int(round(base_y - fy))
    # shadow, computed on a canvas the size of the output
    m_size = (size, size)
    mk_local = shadow_mask_offset(m, ppu, light, ox, oy, size)
    out = bg.copy()
    out[mk_local] = out[mk_local] * (1 - SHADOW_A) + SHADOW * SHADOW_A
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
LIGHT = (-0.95, -1.3, -0.05)      # direction the light travels; shadows fall to the right on screen


def title_img(path, width):
    t = Image.open(path).convert("RGBA")
    t = t.crop(t.getbbox())
    return t.resize((width, round(t.height * width / t.width)), Image.LANCZOS)


if __name__ == "__main__":
    mod = importlib.import_module(sys.argv[1]); title_path = sys.argv[2]; out = sys.argv[3]
    m = mod.build()
    ppu = float(sys.argv[4]) if len(sys.argv) > 4 else 24
    icon = compose(m, CAM, LIGHT, ppu, S, 492, 640)
    t = title_img(title_path, 860)
    icon.alpha_composite(t, ((S - t.width) // 2, 905 - t.height // 2))
    icon.convert("RGB").save(out)


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
