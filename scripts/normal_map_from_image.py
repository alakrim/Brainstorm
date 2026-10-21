#!/usr/bin/env python3
"""normal_map_from_image.py - tangent-space normal map for a 2D sprite (numpy + Pillow).

Height source: luminance of the sprite itself (default) or a supplied height/depth PNG
(e.g. Depth Anything output; white = near/high). Gradients come from a Sobel filter,
optionally after a Gaussian blur. Transparent pixels never create fake edges: their height
is filled from the nearest opaque pixels before filtering and their output is the flat
normal (128,128,255) with the sprite's alpha copied over.

Usage
-----
    python normal_map_from_image.py sprite.png sprite_n.png
    python normal_map_from_image.py sprite.png sprite_n.png --height-map depth.png \\
        --strength 4 --blur 1.5 --bevel 0.3
    python normal_map_from_image.py sprite.png sprite_n.png --flip-y     # DirectX / Y-down output
    python normal_map_from_image.py --self-test                          # checks the conventions

Options
    --height-map PNG      use this image (luminance) as height instead of the sprite
    --invert-height       black = high (some depth models output far = white)
    --strength S          slope multiplier (default 2.0; 1 = per-pixel slope of a 0..1 height)
    --blur SIGMA          Gaussian sigma in px applied to the height first (default 1.0; 0 off)
    --auto-contrast       stretch the height to 0..1 over opaque pixels before filtering
    --bevel B             add B * blurred-alpha to the height (rounded edge look, default 0)
    --bevel-radius PX     blur radius of that alpha bevel (default 4)
    --alpha-threshold A   0..255; pixels with alpha <= A count as transparent (default 8)
    --flip-y              invert the green channel (DirectX convention). Default output is
                          OpenGL convention (green = +Y = up), which is what Godot 4 and
                          Unity expect.
    --flip-x              invert the red channel (rarely needed)
    --no-alpha            write an RGB PNG without alpha

Green-channel convention (researched 2026-10-21)
    * Godot 4 CanvasTexture.normal_texture: "Godot expects the normal map to use X+, Y+,
      and Z+ coordinates." i.e. OpenGL style, green points UP.
      https://docs.godotengine.org/en/stable/classes/class_canvastexture.html
      (comparison table of engines linked there:
       http://wiki.polycount.com/wiki/Normal_Map_Technical_Details#Common_Swizzle_Coordinates)
    * Unity: "Unity uses Y+ normal maps, sometimes known as OpenGL format."
      https://docs.unity3d.com/6000.0/Documentation/Manual/StandardShaderMaterialParameterNormalMap.html
      URP 2D lights read the normal map as a sprite Secondary Texture named _NormalMap with
      Texture Type = Normal Map and sRGB off:
      https://docs.unity3d.com/6000.0/Documentation/Manual/urp/SecondaryTextures.html
      The URP 2D page does not state the Y direction itself; the Y+ statement above is from
      the general Unity docs (UNVERIFIED for the 2D renderer: put a light above the sprite
      in-engine and check that the top edges are lit; if not, rerun with --flip-y).
      Unity's importer also has a "Flip Green Channel" switch
      (https://docs.unity3d.com/ScriptReference/TextureImporter-flipGreenChannel.html).
    * DirectX style (Y-, used by Unreal, 3ds Max, some baker tools) needs --flip-y.
    So the default here (no flag) already suits both Godot 4 and Unity.
    In image space this means: where the height rises toward the top of the image, the pixel
    is greener than 128; where it rises to the right, the pixel is redder than 128.

Dependencies: Python 3.8+, numpy, Pillow.  (No scipy: blur and Sobel are done in numpy.)

Tested 2026-10-21 (Python 3.13.16, numpy 2.5.3, Pillow 12.3.0): --self-test (synthetic
hemisphere: sign of R/G at the right/top edges for default and --flip-y, flat result under
transparent areas, alpha preserved) and a real sprite rendered by render_sprite_directions.py
with luminance height and with a supplied depth map. Results in scripts/README.md.
"""
import argparse
import sys

import numpy as np
from PIL import Image


# ------------------------------------------------------------------ filters
def gaussian_kernel(sigma):
    r = max(1, int(np.ceil(sigma * 3)))
    x = np.arange(-r, r + 1, dtype=np.float64)
    k = np.exp(-(x * x) / (2 * sigma * sigma))
    return k / k.sum()


def blur(a, sigma):
    if sigma <= 0:
        return a
    k = gaussian_kernel(sigma)
    r = len(k) // 2
    p = np.pad(a, ((r, r), (0, 0)), mode="edge")
    a = sum(k[i] * p[i:i + a.shape[0]] for i in range(len(k)))
    p = np.pad(a, ((0, 0), (r, r)), mode="edge")
    return sum(k[i] * p[:, i:i + a.shape[1]] for i in range(len(k)))


def sobel(h):
    """Return (dh/dx, dh/drow) per pixel (Sobel / 8). Rows grow downward."""
    p = np.pad(h, 1, mode="edge")
    tl, tc, tr = p[:-2, :-2], p[:-2, 1:-1], p[:-2, 2:]
    ml, mr = p[1:-1, :-2], p[1:-1, 2:]
    bl, bc, br = p[2:, :-2], p[2:, 1:-1], p[2:, 2:]
    gx = ((tr + 2 * mr + br) - (tl + 2 * ml + bl)) / 8.0
    gy = ((bl + 2 * bc + br) - (tl + 2 * tc + tr)) / 8.0
    return gx, gy


def fill_transparent(h, opaque, iters=64):
    """Replace heights under transparent pixels by the nearest opaque value (iterative dilation)."""
    h = h.copy()
    known = opaque.copy()
    h[~known] = 0
    for _ in range(iters):
        if known.all():
            break
        pad_h = np.pad(h * known, 1, mode="edge")
        pad_k = np.pad(known.astype(np.float64), 1, mode="constant")
        s = sum(pad_h[1 + dy:1 + dy + h.shape[0], 1 + dx:1 + dx + h.shape[1]]
                for dy in (-1, 0, 1) for dx in (-1, 0, 1))
        c = sum(pad_k[1 + dy:1 + dy + h.shape[0], 1 + dx:1 + dx + h.shape[1]]
                for dy in (-1, 0, 1) for dx in (-1, 0, 1))
        new = (~known) & (c > 0)
        h[new] = s[new] / c[new]
        known = known | new
    if not known.all():  # fully isolated: fall back to mean opaque height
        h[~known] = h[opaque].mean() if opaque.any() else 0.5
    return h


# ------------------------------------------------------------------ core
def luminance(rgb):
    return 0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]


def make_normal_map(height, alpha, strength=2.0, blur_sigma=1.0, flip_y=False, flip_x=False,
                    auto_contrast=False, bevel=0.0, bevel_radius=4.0, alpha_threshold=8):
    """height: float (H,W) in 0..1; alpha: float (H,W) in 0..255 (or None).

    Returns uint8 (H,W,3). Convention: OpenGL (green = +Y up) unless flip_y.
    """
    h = height.astype(np.float64)
    if alpha is None:
        opaque = np.ones(h.shape, bool)
        a01 = np.ones(h.shape)
    else:
        opaque = alpha > alpha_threshold
        a01 = np.clip(alpha / 255.0, 0, 1)
    if auto_contrast and opaque.any():
        lo, hi = h[opaque].min(), h[opaque].max()
        if hi > lo:
            h = np.clip((h - lo) / (hi - lo), 0, 1)
    if not opaque.all():
        h = fill_transparent(h, opaque)
    if bevel > 0:
        h = h + bevel * blur(np.where(opaque, a01, 0.0), bevel_radius)
    h = blur(h, blur_sigma)
    gx, gy = sobel(h)
    # height z(x, y_up): n ~ (-dz/dx, -dz/dy_up, 1) and y_up = -row  =>  ny = +dz/drow
    nx = -gx * strength
    ny = gy * strength
    if flip_y:
        ny = -ny
    if flip_x:
        nx = -nx
    nz = np.ones_like(nx)
    ln = np.sqrt(nx * nx + ny * ny + nz * nz)
    n = np.stack([nx / ln, ny / ln, nz / ln], axis=-1)
    rgb = np.clip(np.round((n * 0.5 + 0.5) * 255.0), 0, 255).astype(np.uint8)
    rgb[~opaque] = (128, 128, 255)
    return rgb


# ------------------------------------------------------------------ self test
def self_test():
    n = 64
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float64)
    r2 = ((xx - n / 2 + 0.5) ** 2 + (yy - n / 2 + 0.5) ** 2) / (n / 2.5) ** 2
    height = np.sqrt(np.clip(1 - r2, 0, None))        # hemisphere, tall in the middle
    alpha = np.where(r2 < 1, 255.0, 0.0)
    ok = True

    def check(name, cond):
        nonlocal ok
        print("%-62s %s" % (name, "ok" if cond else "FAIL"))
        ok &= bool(cond)

    gl = make_normal_map(height, alpha, strength=4, blur_sigma=0)
    dx = make_normal_map(height, alpha, strength=4, blur_sigma=0, flip_y=True)
    c = n // 2
    right, left, top, bottom = gl[c, c + 16], gl[c, c - 16], gl[c - 16, c], gl[c + 16, c]
    check("OpenGL: right side of dome leans right (R > 128)", right[0] > 140)
    check("OpenGL: left side leans left (R < 128)", left[0] < 116)
    check("OpenGL: top of dome leans up (G > 128, green = +Y)", top[1] > 140)
    check("OpenGL: bottom of dome leans down (G < 128)", bottom[1] < 116)
    check("flip-y: green inverted (top G < 128), red unchanged", dx[c - 16, c][1] < 116 and dx[c, c + 16][0] > 140)
    check("centre of dome is flat (~128,128,255)", abs(int(gl[c, c][0]) - 128) < 6 and gl[c, c][2] > 250)
    check("transparent corner is flat (128,128,255)", tuple(gl[0, 0]) == (128, 128, 255))
    check("all normals unit length (+-1.5%)",
          np.abs(np.linalg.norm(gl.astype(float) / 255 * 2 - 1, axis=-1)[alpha > 0] - 1).max() < 0.015)
    return 0 if ok else 1


# ------------------------------------------------------------------ CLI
def load_height(path, size, invert):
    im = Image.open(path)
    if im.mode in ("I;16", "I", "F"):
        a = np.asarray(im, dtype=np.float64)
        a = (a - a.min()) / max(a.max() - a.min(), 1e-9)
    else:
        if im.mode in ("RGBA", "LA"):
            bg = Image.new("RGBA", im.size, (0, 0, 0, 255))
            bg.alpha_composite(im.convert("RGBA"))
            im = bg
        a = np.asarray(im.convert("L"), dtype=np.float64) / 255.0
    if (a.shape[1], a.shape[0]) != size:
        a = np.asarray(Image.fromarray((a * 255).astype(np.uint8)).resize(size, Image.BICUBIC), dtype=np.float64) / 255.0
    return 1.0 - a if invert else a


def main(argv=None):
    ap = argparse.ArgumentParser(description="Tangent-space normal map from a sprite (luminance or depth).")
    ap.add_argument("input", nargs="?")
    ap.add_argument("output", nargs="?")
    ap.add_argument("--height-map")
    ap.add_argument("--invert-height", action="store_true")
    ap.add_argument("--strength", type=float, default=2.0)
    ap.add_argument("--blur", type=float, default=1.0)
    ap.add_argument("--auto-contrast", action="store_true")
    ap.add_argument("--bevel", type=float, default=0.0)
    ap.add_argument("--bevel-radius", type=float, default=4.0)
    ap.add_argument("--alpha-threshold", type=int, default=8)
    ap.add_argument("--flip-y", action="store_true")
    ap.add_argument("--flip-x", action="store_true")
    ap.add_argument("--no-alpha", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()
    if not a.input or not a.output:
        ap.error("input and output are required (or use --self-test)")

    im = Image.open(a.input).convert("RGBA")
    arr = np.asarray(im, dtype=np.float64)
    alpha = arr[..., 3]
    if a.height_map:
        height = load_height(a.height_map, im.size, a.invert_height)
    else:
        height = luminance(arr[..., :3] / 255.0)
        if a.invert_height:
            height = 1.0 - height
    # a fully opaque input has no silhouette to respect
    alpha_in = alpha if alpha.min() < 255 else None
    rgb = make_normal_map(height, alpha_in, a.strength, a.blur, a.flip_y, a.flip_x,
                          a.auto_contrast, a.bevel, a.bevel_radius, a.alpha_threshold)
    if a.no_alpha:
        out = Image.fromarray(rgb, "RGB")
    else:
        out = Image.fromarray(np.dstack([rgb, alpha.astype(np.uint8)]), "RGBA")
    out.save(a.output)
    opq = alpha > a.alpha_threshold
    n = rgb[opq].astype(float) / 255 * 2 - 1 if opq.any() else np.zeros((1, 3))
    print("wrote %s  size=%dx%d  convention=%s  mean(nx,ny)=(%.3f,%.3f)" % (
        a.output, im.width, im.height, "DirectX (Y-)" if a.flip_y else "OpenGL (Y+)",
        n[:, 0].mean(), n[:, 1].mean()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
