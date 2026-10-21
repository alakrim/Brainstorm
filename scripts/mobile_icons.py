#!/usr/bin/env python3
"""mobile_icons.py - app icon sets for iOS, Android (adaptive + legacy), Play Store and Godot.

From ONE 1024x1024 source, or from a foreground PNG plus a background colour/PNG, writes:

  <out>/ios/AppIcon-1024.png            1024x1024 RGB, alpha removed (flattened on background)
  <out>/ios/Contents.json               single-size AppIcon.appiconset descriptor (Xcode 14+)
  <out>/android/res/mipmap-{mdpi,hdpi,xhdpi,xxhdpi,xxxhdpi}/
        ic_launcher_foreground.png      adaptive layer, 108dp = 108/162/216/324/432 px
        ic_launcher_background.png      adaptive layer, same sizes
        ic_launcher_monochrome.png      themed-icon layer (Android 13+), same sizes
        ic_launcher.png                 legacy square icon, 48dp = 48/72/96/144/192 px
        ic_launcher_round.png           legacy round icon, same sizes
  <out>/android/res/mipmap-anydpi-v26/ic_launcher.xml        adaptive-icon XML
  <out>/android/res/mipmap-anydpi-v26/ic_launcher_round.xml
  <out>/android/play-store/ic_launcher-512.png   Play Store icon, 512x512
  <out>/godot/                          icon_192.png (main), adaptive_fg/bg/mono_432.png
  <out>/preview.png                     circle / squircle / square mask preview
  <out>/icons.json                      manifest of everything written

Usage
-----
    python mobile_icons.py --source icon1024.png --out build/icons
    python mobile_icons.py --source icon1024.png --bg-color "#1b1f3b" --out build/icons
    python mobile_icons.py --foreground logo.png --background "#ffcc00" --out build/icons
    python mobile_icons.py --foreground logo.png --background bg_pattern.png --out build/icons
    # Copy <out>/android/res/* into app/src/main/res/ ; Unity: assign layers/sizes in
    # Player Settings > Icons ; Godot: use the files in <out>/godot in the Android export preset.

Options
    --source PNG           single art file (square, 1024 recommended)
    --foreground PNG       foreground art with transparency (logo/character), instead of --source
    --background C|PNG     "#rrggbb" or an image (cover-fitted); default: average border colour
                           of --source, or white with --foreground only
    --bg-color #rrggbb     alias of --background for a colour
    --fg-box-dp N          size (dp) of the safe box the foreground is scaled into (default 66)
    --fg-scale F           override: foreground content height/width as fraction of the 108dp layer
    --fg-canvas            foreground is already a full 108dp layer: use as-is, do not scale
    --icon-fill F          how much of the iOS/Play square the foreground content fills
                           (default 0.72; only for --foreground mode)
    --legacy-crop-dp N     centre part of the 108dp layer used for legacy icons (default 80)
    --fit box|circle       box (default): content bbox fits the --fg-box-dp square (Android docs
                           say 66x66 dp); circle: every opaque pixel must lie inside a circle of
                           that diameter (safest against round masks; shrinks square art a lot)
    --source-layout box|bleed
                           --source only. box (default): art is scaled into the safe box on a
                           flat background layer. bleed: the whole source is the background
                           layer (covers 108 dp, launchers crop to the central 72 dp), no
                           foreground, no monochrome layer
    --mono-from alpha|luma monochrome source: alpha channel of the foreground (default if the
                           foreground has transparency) or difference from the background colour
    --mono-threshold N     luma mode: ignore colour differences below N (0-255, default 48)

Facts used (researched 2026-10-21)
  * Android adaptive icons: layers are 108x108 dp, the system masks the outer 18 dp on each side;
    keep the logo inside the 66x66 dp safe zone; XML at res/mipmap-anydpi-v26/ic_launcher.xml
    with <background>, <foreground>, optional <monochrome> (Android 13+ themed icons).
    https://developer.android.com/develop/ui/views/launch/icon_design_adaptive
  * Densities: mdpi 1x, hdpi 1.5x, xhdpi 2x, xxhdpi 3x, xxxhdpi 4x => 108/162/216/324/432 px;
    legacy 48dp => 48/72/96/144/192 px.
  * Godot 4 Android export: main icon >= 192x192, adaptive foreground/background >= 432x432,
    themed (monochrome) >= 432x432.
    https://docs.godotengine.org/en/stable/tutorials/export/exporting_for_android.html
  * iOS App Store icon: 1024x1024 PNG, no transparency, no baked rounded corners (the system
    masks it). (From general knowledge: the Apple HIG page could not be fetched as text, so
    this is UNVERIFIED against the live page.)  Play Store icon: 512x512 PNG (also from general
    knowledge; check "Google Play icon design specifications").

Caveat: for an opaque --source the monochrome layer is a guess (pixels that differ from the
border colour); supply --foreground with transparency for a clean themed-icon silhouette.

Dependencies: Python 3.8+, Pillow.

Tested 2026-10-21 (Python 3.13.16, Pillow 12.3.0): both modes (--source, and --foreground +
colour / PNG background); the script verifies its own output (sizes, no alpha on iOS/Play,
foreground bbox inside the safe zone, XML parses). See scripts/README.md.
"""
import argparse
import json
import os
import sys
import xml.etree.ElementTree as ET

from PIL import Image, ImageChops, ImageDraw, ImageStat

DENSITIES = [("mdpi", 1.0), ("hdpi", 1.5), ("xhdpi", 2.0), ("xxhdpi", 3.0), ("xxxhdpi", 4.0)]
LAYER_DP = 108
LEGACY_DP = 48
MASTER = 1728  # 108 dp * 16 : supersampled master canvas, downscaled per density


def parse_color(s):
    s = s.lstrip("#")
    if len(s) == 3:
        s = "".join(c * 2 for c in s)
    return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))


def alpha_bbox(im, thr=8):
    a = im.getchannel("A").point(lambda v: 255 if v > thr else 0)
    return a.getbbox()


def fit_center(im, box, canvas):
    """Scale `im` to fit inside box x box (keep aspect), centre on a transparent canvas x canvas."""
    w, h = im.size
    s = box / max(w, h)
    nw, nh = max(1, round(w * s)), max(1, round(h * s))
    r = im.resize((nw, nh), Image.LANCZOS)
    out = Image.new("RGBA", (canvas, canvas), (0, 0, 0, 0))
    out.alpha_composite(r, ((canvas - nw) // 2, (canvas - nh) // 2))
    return out


def circle_fit_scale(content, canvas, diameter_px):
    """Largest scale at which every opaque pixel of `content` (centred) lies inside a circle."""
    a = content.getchannel("A").point(lambda v: 255 if v > 8 else 0)
    n = 256  # work at low resolution
    lo, hi = 0.05, 4.0
    for _ in range(14):
        mid = (lo + hi) / 2
        w, h = a.size
        k = mid * diameter_px / max(w, h) * (n / canvas)
        tw, th = max(1, round(w * k)), max(1, round(h * k))
        m = Image.new("L", (n, n), 0)
        m.paste(a.resize((tw, th), Image.BILINEAR).point(lambda v: 255 if v > 64 else 0),
                ((n - tw) // 2, (n - th) // 2))
        outside = Image.new("L", (n, n), 255)
        ImageDraw.Draw(outside).ellipse((n / 2 - diameter_px / canvas * n / 2, n / 2 - diameter_px / canvas * n / 2,
                                         n / 2 + diameter_px / canvas * n / 2, n / 2 + diameter_px / canvas * n / 2), fill=0)
        if ImageChops.multiply(m, outside).getbbox() is None and (tw <= n and th <= n):
            lo = mid
        else:
            hi = mid
    return lo


def border_color(im):
    rgba = im.convert("RGBA")
    w, h = rgba.size
    t = max(2, min(w, h) // 64)
    strips = [rgba.crop((0, 0, w, t)), rgba.crop((0, h - t, w, h)),
              rgba.crop((0, 0, t, h)), rgba.crop((w - t, 0, w, h))]
    tot, n = [0, 0, 0], 0
    for s in strips:
        raw = s.tobytes()  # RGBA bytes
        for i in range(0, len(raw), 4):
            if raw[i + 3] > 128:
                tot[0] += raw[i]; tot[1] += raw[i + 1]; tot[2] += raw[i + 2]; n += 1
    if n == 0:
        return (255, 255, 255)
    return tuple(int(round(v / n)) for v in tot)


def make_background(spec, canvas, default):
    if spec is None:
        return Image.new("RGBA", (canvas, canvas), default + (255,))
    if os.path.isfile(spec):
        im = Image.open(spec).convert("RGBA")
        s = canvas / min(im.size)                      # cover-fit
        im = im.resize((max(canvas, round(im.width * s)), max(canvas, round(im.height * s))), Image.LANCZOS)
        l, t = (im.width - canvas) // 2, (im.height - canvas) // 2
        im = im.crop((l, t, l + canvas, t + canvas))
        flat = Image.new("RGBA", im.size, default + (255,))
        flat.alpha_composite(im)
        return flat
    return Image.new("RGBA", (canvas, canvas), parse_color(spec) + (255,))


def flatten(im, bg_rgb):
    bg = Image.new("RGBA", im.size, tuple(bg_rgb) + (255,))
    bg.alpha_composite(im.convert("RGBA"))
    return bg.convert("RGB")


def mono_alpha(art, bg_rgb, mode, threshold):
    """Alpha mask of the shape to show in themed (monochrome) icons."""
    if mode == "alpha":
        return art.getchannel("A")
    flat = flatten(art, bg_rgb)
    diff = ImageChops.difference(flat, Image.new("RGB", flat.size, tuple(bg_rgb))).convert("L")
    return diff.point(lambda v: max(0, min(255, (v - threshold) * 4)))


def apply_mask(im, shape):
    w, h = im.size
    m = Image.new("L", (w * 4, h * 4), 0)
    d = ImageDraw.Draw(m)
    if shape == "circle":
        d.ellipse((0, 0, w * 4 - 1, h * 4 - 1), fill=255)
    elif shape == "squircle":
        d.rounded_rectangle((0, 0, w * 4 - 1, h * 4 - 1), radius=int(w * 4 * 0.26), fill=255)
    else:  # legacy rounded square
        d.rounded_rectangle((0, 0, w * 4 - 1, h * 4 - 1), radius=int(w * 4 * 0.16), fill=255)
    m = m.resize((w, h), Image.LANCZOS)
    out = im.convert("RGBA")
    out.putalpha(ImageChops.multiply(out.getchannel("A"), m))
    return out


def save(im, path, files):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im.save(path)
    files.append(dict(path=os.path.abspath(path), size=list(im.size), mode=im.mode))


def adaptive_xml(with_mono):
    lines = ['<?xml version="1.0" encoding="utf-8"?>',
             '<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">',
             '    <background android:drawable="@mipmap/ic_launcher_background" />',
             '    <foreground android:drawable="@mipmap/ic_launcher_foreground" />']
    if with_mono:
        lines.append('    <monochrome android:drawable="@mipmap/ic_launcher_monochrome" />')
    lines.append('</adaptive-icon>')
    return "\n".join(lines) + "\n"


def verify(out, files, safe_dp, bleed_mode=False):
    problems = []
    for f in files:
        p = f["path"]
        if p.endswith(".png"):
            with Image.open(p) as im:
                if list(im.size) != f["size"]:
                    problems.append("size mismatch " + f["path"])
                if ("ios" in p or "play-store" in p) and im.mode != "RGB":
                    problems.append("alpha present in " + f["path"])
    if not any(f["path"].endswith("AppIcon-1024.png") for f in files):
        problems.append("missing iOS icon")
    # every foreground layer: content inside the safe zone
    for name, scale in DENSITIES:
        px = round(LAYER_DP * scale)
        p = os.path.join(out, "android", "res", "mipmap-" + name, "ic_launcher_foreground.png")
        with Image.open(p) as im:
            if im.size != (px, px):
                problems.append("foreground size wrong in " + name)
            bb = alpha_bbox(im.convert("RGBA"), thr=16)
            if bb and safe_dp and not bleed_mode:
                m = (LAYER_DP - safe_dp) / 2 / LAYER_DP * px
                if bb[0] < m - 1.5 or bb[1] < m - 1.5 or bb[2] > px - m + 1.5 or bb[3] > px - m + 1.5:
                    problems.append("foreground exceeds safe zone in %s: bbox %s" % (name, bb))
    for xml in ("ic_launcher.xml", "ic_launcher_round.xml"):
        try:
            ET.parse(os.path.join(out, "android", "res", "mipmap-anydpi-v26", xml))
        except Exception as e:  # noqa
            problems.append("bad XML %s: %s" % (xml, e))
    return problems


def main(argv=None):
    ap = argparse.ArgumentParser(description="Generate iOS / Android / Play Store / Godot app icons.")
    ap.add_argument("--source")
    ap.add_argument("--foreground")
    ap.add_argument("--background")
    ap.add_argument("--bg-color")
    ap.add_argument("--out", required=True)
    ap.add_argument("--fg-box-dp", type=float, default=66.0)
    ap.add_argument("--fg-scale", type=float)
    ap.add_argument("--fg-canvas", action="store_true")
    ap.add_argument("--fit", choices=("box", "circle"), default="box")
    ap.add_argument("--source-layout", choices=("box", "bleed"), default="box")
    ap.add_argument("--mono-threshold", type=int, default=48)
    ap.add_argument("--icon-fill", type=float, default=0.72)
    ap.add_argument("--legacy-crop-dp", type=float, default=80.0)
    ap.add_argument("--mono-from", choices=("alpha", "luma"))
    a = ap.parse_args(argv)
    if bool(a.source) == bool(a.foreground):
        ap.error("give exactly one of --source or --foreground")
    bgspec = a.background or a.bg_color

    src = Image.open(a.source or a.foreground).convert("RGBA")
    if a.source and (src.width != src.height):
        print("WARNING: source is %dx%d, not square; it will be fitted, not stretched" % src.size, file=sys.stderr)
    if a.source and min(src.size) < 1024:
        print("WARNING: source smaller than 1024 px; the iOS icon will be upscaled", file=sys.stderr)

    default_bg = border_color(src) if a.source else (255, 255, 255)
    if bgspec and not os.path.isfile(bgspec):
        default_bg = parse_color(bgspec)

    # ---- adaptive master layers (108 dp canvas)
    bleed = bool(a.source) and a.source_layout == "bleed"
    mono_art = None
    if bleed:
        bg_master = make_background(a.source, MASTER, default_bg)
        fg_master = Image.new("RGBA", (MASTER, MASTER), (0, 0, 0, 0))
        mono_master, mono_mode = None, "none"
    else:
        if a.fg_canvas:
            fg_master = src.resize((MASTER, MASTER), Image.LANCZOS)
            art_for_mono = fg_master
        else:
            content = src
            bb = alpha_bbox(src) if a.foreground else None
            if bb:
                content = src.crop(bb)
            if a.fg_scale:
                box_px = round(MASTER * a.fg_scale)
            elif a.fit == "circle":
                box_px = round(MASTER * circle_fit_scale(content, MASTER, MASTER * a.fg_box_dp / LAYER_DP)
                               * a.fg_box_dp / LAYER_DP)
            else:
                box_px = round(MASTER * a.fg_box_dp / LAYER_DP)
            fg_master = fit_center(content, box_px, MASTER)
            art_for_mono = fit_center(content, box_px, MASTER)
        bg_master = make_background(bgspec, MASTER, default_bg)
        has_alpha = src.getchannel("A").getextrema()[0] < 250
        mono_mode = a.mono_from or ("alpha" if has_alpha else "luma")
        # luma mode compares the art with ITS OWN background (border colour of the source)
        ref_bg = default_bg
        m_alpha = mono_alpha(art_for_mono, ref_bg, mono_mode, a.mono_threshold)
        mono_master = Image.new("RGBA", (MASTER, MASTER), (0, 0, 0, 0))
        mono_master.putalpha(m_alpha)
    composite = bg_master.copy()
    composite.alpha_composite(fg_master)

    files = []
    out = a.out

    def P(*parts):
        return os.path.join(out, *parts)

    res = lambda d, n: P("android", "res", "mipmap-" + d, n)
    for name, scale in DENSITIES:
        px = round(LAYER_DP * scale)
        save(fg_master.resize((px, px), Image.LANCZOS), res(name, "ic_launcher_foreground.png"), files)
        save(bg_master.resize((px, px), Image.LANCZOS).convert("RGB"), res(name, "ic_launcher_background.png"), files)
        if mono_master is not None:
            save(mono_master.resize((px, px), Image.LANCZOS), res(name, "ic_launcher_monochrome.png"), files)
    # legacy icons: central part of the 108 dp layer, rounded square / circle
    crop = a.legacy_crop_dp / LAYER_DP
    c0 = round(MASTER * (1 - crop) / 2)
    legacy_master = composite.crop((c0, c0, MASTER - c0, MASTER - c0))
    for name, scale in DENSITIES:
        px = round(LEGACY_DP * scale)
        sq = legacy_master.resize((px, px), Image.LANCZOS)
        save(apply_mask(sq, "legacy"), res(name, "ic_launcher.png"), files)
        save(apply_mask(sq, "circle"), res(name, "ic_launcher_round.png"), files)
    xdir = P("android", "res", "mipmap-anydpi-v26")
    os.makedirs(xdir, exist_ok=True)
    for fn in ("ic_launcher.xml", "ic_launcher_round.xml"):
        with open(os.path.join(xdir, fn), "w") as f:
            f.write(adaptive_xml(mono_master is not None))
        files.append(dict(path=os.path.abspath(os.path.join(xdir, fn)), size=None, mode="xml"))

    # ---- iOS / Play store square (full bleed, opaque)
    if a.source:
        square = flatten(src.resize((1024, 1024), Image.LANCZOS) if src.size != (1024, 1024) else src,
                         default_bg)
    else:
        content = src.crop(alpha_bbox(src)) if alpha_bbox(src) else src
        sq = bg_master.resize((1024, 1024), Image.LANCZOS)
        sq.alpha_composite(fit_center(content, round(1024 * a.icon_fill), 1024))
        square = sq.convert("RGB")
    save(square, P("ios", "AppIcon-1024.png"), files)
    contents = {"images": [{"filename": "AppIcon-1024.png", "idiom": "universal",
                            "platform": "ios", "size": "1024x1024"}],
                "info": {"author": "xcode", "version": 1}}
    os.makedirs(P("ios"), exist_ok=True)
    with open(P("ios", "Contents.json"), "w") as f:
        json.dump(contents, f, indent=2)
    save(square.resize((512, 512), Image.LANCZOS), P("android", "play-store", "ic_launcher-512.png"), files)

    # ---- Godot export preset files
    save(apply_mask(legacy_master.resize((192, 192), Image.LANCZOS), "legacy"), P("godot", "icon_192.png"), files)
    save(fg_master.resize((432, 432), Image.LANCZOS), P("godot", "adaptive_fg_432.png"), files)
    save(bg_master.resize((432, 432), Image.LANCZOS).convert("RGB"), P("godot", "adaptive_bg_432.png"), files)
    if mono_master is not None:
        save(mono_master.resize((432, 432), Image.LANCZOS), P("godot", "adaptive_mono_432.png"), files)

    # ---- preview sheet: adaptive composite visible area under three masks + legacy 192
    vis = composite.crop((round(MASTER * 18 / 108),) * 2 + (round(MASTER * 90 / 108),) * 2)
    cell = 216
    sheet = Image.new("RGBA", (cell * 4 + 50, cell + 20), (70, 70, 70, 255))
    for i, shape in enumerate(("circle", "squircle", "square")):
        v = vis.resize((cell, cell), Image.LANCZOS)
        v = apply_mask(v, shape) if shape != "square" else v
        sheet.alpha_composite(v, (10 + i * (cell + 10), 10))
    sheet.alpha_composite(square.resize((cell, cell), Image.LANCZOS).convert("RGBA"), (10 + 3 * (cell + 10), 10))
    save(sheet.convert("RGB"), P("preview.png"), files)

    problems = verify(os.path.abspath(out), files, a.fg_box_dp if not (a.fg_canvas or a.fg_scale) else None, bleed)
    manifest = dict(mode="source" if a.source else "foreground+background", mono_from=mono_mode,
                    background_default_rgb=list(default_bg), files=[
                        dict(f, path=os.path.relpath(f["path"], os.path.abspath(out))) for f in files],
                    problems=problems)
    with open(P("icons.json"), "w") as f:
        json.dump(manifest, f, indent=2)
    print("wrote %d files to %s ; verify: %s" % (len(files), out, "OK" if not problems else problems))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
