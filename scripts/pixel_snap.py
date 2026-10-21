#!/usr/bin/env python3
"""pixel_snap.py - turn a generated "fake pixel art" image into real pixel art on a true grid.

AI image models draw pixel-art-looking images whose "pixels" are blurry, uneven and not
aligned to a grid. This script:
  1. finds (or is told) the logical pixel size and grid phase,
  2. resamples each grid cell to ONE colour (median / mode / mean of the cell centre),
  3. thresholds alpha to 0/255 (no semi-transparent pixels),
  4. reduces the palette to N colours (Pillow median-cut, k-means refined, or octree),
  5. writes the true-resolution PNG plus an integer nearest-neighbour upscale for preview.
Import the true-resolution PNG in Godot/Unity with filter = Nearest (point) and no
compression/mipmaps, then scale it by an integer factor in the engine.

Usage
-----
    python pixel_snap.py in.png out.png                       # auto-detect pixel size, 16 colours
    python pixel_snap.py in.png out.png --pixel-size 16 --colors 12
    python pixel_snap.py in.png out.png --target-size 64      # longest side becomes 64 px
    python pixel_snap.py in.png out.png --target-size 48x64 --colors 24 --quantizer kmeans
    python pixel_snap.py in.png out.png --detect-only         # just print the detected grid
    python pixel_snap.py in.png out.png --key-color "#ffffff" --key-tol 30   # flat bg -> transparent

Options
    --pixel-size S         logical pixel size in source pixels (may be fractional, e.g. 15.7)
    --target-size W[xH]    output grid size (alternative to --pixel-size; one number = longest side)
    --offset X,Y           grid phase in source pixels (default: detected, else 0,0)
    --method median|mode|mean
                           how a cell becomes one colour (default median; mode = most frequent
                           colour after 5-bit reduction, crispest on clean inputs)
    --center F             fraction of each cell (0.1-1.0) sampled, centred (default 0.6; this
                           skips blurry cell borders)
    --colors N             palette size (default 16; 0 = keep all colours)
    --quantizer mediancut|kmeans|octree|libimagequant
                           Pillow quantizers; kmeans = median cut refined with 10 k-means
                           iterations (default); libimagequant only if Pillow has it
    --dither               Floyd-Steinberg dithering when mapping to the palette (default off)
    --alpha-threshold A    cells with mean alpha below A (0-255) become transparent (default 128)
    --key-color #RRGGBB    treat this colour as background -> transparent (for flat backgrounds)
    --key-tol T            colour distance tolerance for --key-color (default 24)
    --trim                 crop fully transparent border rows/columns of the result
    --preview-scale K      integer nearest-neighbour upscale for <out>_preview.png (default 8, 0 = off)

Detection: edge profile of columns/rows -> autocorrelation peak -> least-squares grid fit.
It works on clean-ish grids; if the result looks wrong, pass --pixel-size / --target-size and
check <out>_preview.png.

Better alternatives for hard cases (this script is a deliberately small, dependency-light
baseline; verify licences before shipping, see reference/licenses.md):
  * PixelOE (contrast-aware outline expansion, several downscale modes, pip install pixeloe):
    https://github.com/KohakuBlueleaf/PixelOE
  * unfake.js (browser/JS) and its Python port `unfake` (pip install unfake): automatic scale
    and grid detection, Wu colour quantization, runs/edge-aware cleanup:
    https://github.com/jenissimo/unfake.js  and  https://pypi.org/project/unfake/
  * Aseprite extensions such as DeAI PixelKit for manual touch-up.

Dependencies: Python 3.8+, numpy, Pillow (>= 9.1 for Image.Quantize/Dither enums).

Tested 2026-10-21 (Python 3.13.16, numpy 2.5.3, Pillow 12.3.0) on a synthetic 40x40
pixel-art sprite blown up to ~15.7 px per pixel with bicubic blur, noise, an offset and a
flat background: detection, grid recovery rate and palette size are in scripts/README.md.
"""
import argparse
import json
import math
import sys

import numpy as np
from PIL import Image, features

QUANT = {
    "mediancut": (Image.Quantize.MEDIANCUT, 0),
    "kmeans": (Image.Quantize.MEDIANCUT, 10),
    "octree": (Image.Quantize.FASTOCTREE, 0),
    "libimagequant": (Image.Quantize.LIBIMAGEQUANT, 0),
}


# ------------------------------------------------------------------ detection
def edge_profile(gray, axis):
    """Sum of absolute neighbour differences across `axis` (0 = per column, 1 = per row)."""
    d = np.abs(np.diff(gray, axis=1 - axis)) if axis == 0 else np.abs(np.diff(gray, axis=0))
    return d.sum(axis=0) if axis == 0 else d.sum(axis=1)


def detect_period(profile, min_p=3.0, max_p=None):
    """Estimate (period, phase) of a grid from an edge profile; None if no clear grid."""
    e = np.asarray(profile, dtype=np.float64)
    n = len(e)
    if n < 16 or e.max() <= 0:
        return None
    max_p = max_p or n / 4.0
    x = e - e.mean()
    ac = np.correlate(x, x, mode="full")[n - 1:]
    ac /= ac[0] if ac[0] > 0 else 1
    lo, hi = int(math.ceil(min_p)), int(min(max_p, n // 2))
    if hi <= lo + 1:
        return None
    seg = ac[lo:hi]
    # local maxima, then the first one that is a strong fraction of the best one
    peaks = [i for i in range(1, len(seg) - 1) if seg[i] >= seg[i - 1] and seg[i] > seg[i + 1]]
    if not peaks:
        return None
    best = max(seg[i] for i in peaks)
    if best < 0.1:
        return None
    first = next(i for i in peaks if seg[i] >= 0.6 * best)
    a, b, c = seg[first - 1], seg[first], seg[first + 1]
    denom = a - 2 * b + c
    frac = 0.5 * (a - c) / denom if denom != 0 else 0.0
    s0 = lo + first + frac
    # refine with a comb search around s0: boundaries should be strong, cell middles weak
    idx = np.arange(n, dtype=np.float64)
    best = (-1e18, s0, 0.0)
    for s in np.arange(0.85 * s0, 1.15 * s0 + 1e-9, 0.02):
        for p in np.arange(0.0, s, 0.25):
            edges = p + s * np.arange(int((n + 1 - p) / s) + 1)
            edges = edges[(edges >= 1) & (edges <= n)]
            if len(edges) < 3:
                continue
            on = np.interp(edges - 1.0, idx, e).mean()
            mid = edges[:-1] + s / 2.0
            mid = mid[mid <= n]
            off = np.interp(mid - 1.0, idx, e).mean() if len(mid) else 0.0
            score = on - off
            if score > best[0]:
                best = (score, float(s), float(p))
    return best[1], best[2]


def detect_grid(rgb):
    gray = rgb.astype(np.float64).mean(axis=2)
    rx = detect_period(edge_profile(gray, 0))
    ry = detect_period(edge_profile(gray, 1))
    return rx, ry


# ------------------------------------------------------------------ sampling
def cell_edges(length, size, phase):
    """Boundaries of cells along one axis; cells at least half inside the image are kept."""
    start = phase - size * math.ceil(phase / size) if phase > 0 else phase
    first = start if start + size * 0.5 > 0 else start + size
    n = int(round((length - first) / size))
    return [first + i * size for i in range(n + 1)]


def sample_cells(rgb, alpha, sx, sy, ox, oy, center, method, a_thr):
    h, w = alpha.shape
    ex, ey = cell_edges(w, sx, ox), cell_edges(h, sy, oy)
    ny, nx = len(ey) - 1, len(ex) - 1
    out = np.zeros((ny, nx, 4), np.uint8)
    for j in range(ny):
        y0, y1 = ey[j], ey[j + 1]
        cy, hy = (y0 + y1) / 2, (y1 - y0) * center / 2
        ya, yb = int(max(0, math.floor(cy - hy))), int(min(h, max(math.ceil(cy + hy), math.floor(cy - hy) + 1)))
        for i in range(nx):
            x0, x1 = ex[i], ex[i + 1]
            cx, hx = (x0 + x1) / 2, (x1 - x0) * center / 2
            xa, xb = int(max(0, math.floor(cx - hx))), int(min(w, max(math.ceil(cx + hx), math.floor(cx - hx) + 1)))
            if ya >= yb or xa >= xb:
                continue
            a = alpha[ya:yb, xa:xb]
            if a.mean() < a_thr:
                continue
            px = rgb[ya:yb, xa:xb].reshape(-1, 3)
            solid = a.reshape(-1) >= a_thr
            if solid.any():
                px = px[solid]
            if method == "mean":
                col = px.mean(axis=0)
            elif method == "mode":
                q = (px >> 3).astype(np.int32)
                key = (q[:, 0] << 10) | (q[:, 1] << 5) | q[:, 2]
                vals, cnt = np.unique(key, return_counts=True)
                m = vals[cnt.argmax()]
                sel = px[key == m]
                col = sel.mean(axis=0)
            else:
                col = np.median(px, axis=0)
            out[j, i, :3] = np.clip(np.round(col), 0, 255)
            out[j, i, 3] = 255
    return out


# ------------------------------------------------------------------ palette
def reduce_palette(grid, colors, quantizer, dither):
    """grid: (H,W,4) uint8 with binary alpha. Returns (new grid, palette list of hex)."""
    opaque = grid[..., 3] > 0
    if not opaque.any():
        return grid, []
    uniq = np.unique(grid[opaque][:, :3], axis=0)
    if colors and colors < len(uniq):
        m, km = QUANT[quantizer]
        if m == Image.Quantize.LIBIMAGEQUANT and not features.check_feature("libimagequant"):
            print("WARNING: this Pillow build has no libimagequant; using kmeans instead", file=sys.stderr)
            m, km = QUANT["kmeans"]
        src = Image.fromarray(grid[opaque][:, :3].reshape(1, -1, 3), "RGB")
        if m == Image.Quantize.FASTOCTREE or m == Image.Quantize.LIBIMAGEQUANT:
            qimg = src.quantize(colors=colors, method=m, dither=Image.Dither.NONE)
        else:
            qimg = src.quantize(colors=colors, method=m, kmeans=km, dither=Image.Dither.NONE)
        full = Image.fromarray(grid[..., :3], "RGB").quantize(
            palette=qimg, dither=Image.Dither.FLOYDSTEINBERG if dither else Image.Dither.NONE)
        rgb = np.asarray(full.convert("RGB"))
        grid = grid.copy()
        grid[..., :3] = rgb
        grid[~opaque] = 0
    cols = np.unique(grid[grid[..., 3] > 0][:, :3], axis=0)
    return grid, ["#%02x%02x%02x" % tuple(c) for c in cols]


# ------------------------------------------------------------------ main
def parse_size(s):
    if "x" in s.lower():
        w, h = s.lower().split("x")
        return int(w), int(h)
    return int(s), None


def main(argv=None):
    ap = argparse.ArgumentParser(description="Snap fake pixel art to a true pixel grid.")
    ap.add_argument("input")
    ap.add_argument("output")
    ap.add_argument("--pixel-size", type=float)
    ap.add_argument("--target-size")
    ap.add_argument("--offset")
    ap.add_argument("--method", choices=("median", "mode", "mean"), default="median")
    ap.add_argument("--center", type=float, default=0.6)
    ap.add_argument("--colors", type=int, default=16)
    ap.add_argument("--quantizer", choices=sorted(QUANT), default="kmeans")
    ap.add_argument("--dither", action="store_true")
    ap.add_argument("--alpha-threshold", type=int, default=128)
    ap.add_argument("--key-color")
    ap.add_argument("--key-tol", type=float, default=24.0)
    ap.add_argument("--trim", action="store_true", help="crop fully transparent border cells")
    ap.add_argument("--preview-scale", type=int, default=8)
    ap.add_argument("--detect-only", action="store_true")
    a = ap.parse_args(argv)
    if not 0.1 <= a.center <= 1.0:
        ap.error("--center must be between 0.1 and 1.0")

    im = Image.open(a.input).convert("RGBA")
    arr = np.asarray(im).copy()
    rgb, alpha = arr[..., :3], arr[..., 3].astype(np.float64)
    if a.key_color:
        kc = np.array([int(a.key_color.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4)], dtype=np.float64)
        dist = np.sqrt(((rgb.astype(np.float64) - kc) ** 2).sum(axis=2))
        alpha = np.where(dist <= a.key_tol, 0.0, alpha)
    h, w = alpha.shape

    info = dict(input=a.input, source_size=[w, h])
    det = detect_grid(rgb)
    info["detected"] = None
    if det[0] and det[1]:
        info["detected"] = dict(pixel_size_x=round(det[0][0], 3), pixel_size_y=round(det[1][0], 3),
                                offset_x=round(det[0][1], 3), offset_y=round(det[1][1], 3))
    if a.detect_only:
        print(json.dumps(info))
        return 0 if info["detected"] else 1

    ox = oy = 0.0
    if a.target_size:
        tw, th = parse_size(a.target_size)
        if th is None:  # longest side
            if w >= h:
                tw, th = tw, max(1, round(tw * h / w))
            else:
                tw, th = max(1, round(tw * w / h)), tw
        sx, sy = w / tw, h / th
    elif a.pixel_size:
        sx = sy = a.pixel_size
        if info["detected"] and abs(info["detected"]["pixel_size_x"] - a.pixel_size) < 0.1 * a.pixel_size:
            ox, oy = info["detected"]["offset_x"], info["detected"]["offset_y"]
    else:
        if not info["detected"]:
            print("ERROR: could not detect a pixel grid; pass --pixel-size or --target-size", file=sys.stderr)
            return 1
        d = info["detected"]
        sx, sy = d["pixel_size_x"], d["pixel_size_y"]
        if abs(sx - sy) < 0.05 * max(sx, sy):
            sx = sy = (sx + sy) / 2
        ox, oy = d["offset_x"], d["offset_y"]
    if a.offset:
        ox, oy = [float(v) for v in a.offset.split(",")]

    grid = sample_cells(rgb, alpha, sx, sy, ox, oy, a.center, a.method, a.alpha_threshold)
    grid, palette = reduce_palette(grid, a.colors, a.quantizer, a.dither)
    if a.trim and (grid[..., 3] > 0).any():
        ys, xs = np.where(grid[..., 3] > 0)
        grid = np.ascontiguousarray(grid[ys.min():ys.max() + 1, xs.min():xs.max() + 1])
    Image.fromarray(grid, "RGBA").save(a.output)
    gh, gw = grid.shape[:2]
    if a.preview_scale > 0:
        prev = Image.fromarray(grid, "RGBA").resize((gw * a.preview_scale, gh * a.preview_scale), Image.NEAREST)
        pp = a.output.rsplit(".", 1)[0] + "_preview.png"
        prev.save(pp)
        info["preview"] = pp
    info.update(output=a.output, grid_size=[gw, gh], pixel_size=[round(sx, 3), round(sy, 3)],
                offset=[round(ox, 3), round(oy, 3)], colors=len(palette), palette=palette,
                opaque_pixels=int((grid[..., 3] > 0).sum()))
    print(json.dumps(info))
    return 0


if __name__ == "__main__":
    sys.exit(main())
