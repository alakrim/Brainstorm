# Mobile app (non-game) assets: icons, illustrations, vectors

*Researched 2026-10-21.*

## TL;DR

| Asset | Pipeline |
|---|---|
| **App icon** | Sunburst 1024² full-bleed artwork (no text, no rounded corners) → `scripts/mobile_icons.py` → iOS 1024 no-alpha PNG + Android adaptive layers (108 dp, 66 dp safe zone) + Play Store 512 |
| **Flat illustration / spot art / empty states** | Generate → vtracer (free) → SVGO → SVG/VectorDrawable |
| **Complex illustration** | Generate at final 3× size → PNG/WebP at @1x/@2x/@3x, or Recraft vectorize ($0.01/call) |
| **Simple animation** | Vectorize → animate in LottieFiles / After Effects + Bodymovin. AI image-to-Lottie is a rough draft only |
| **UI icons (glyphs)** | Prefer an existing open icon set (Material Symbols, Lucide, Phosphor). Generating small glyphs is rarely worth it |

## 1. Generate

- **Sunburst** for anything that needs transparency or exact edits (`background: "transparent"`, png/webp).
- **Muse Image** ($0.01) for exploring illustration styles. No documented transparency, so use a flat background and cut it out.
- Lock a style block for the whole app so all illustrations match.
- Keep text out of images. Add it in the UI (localization, accessibility).

## 2. App icons

**iOS** (Xcode 14+): one **1024×1024 PNG**, "Single Size" in the AppIcon asset. **No alpha channel** (the App Store rejects it: ITMS-90717) and **no pre-rounded corners**; the system applies the mask.

**Android adaptive icons** (verified, developer.android.com):
- Foreground and background layers, each **108×108 dp**; vector drawables preferred.
- **Safe zone: central 66×66 dp.** The outer 18 dp per side can be masked or used for parallax.
- Logo between 48 and 66 dp.
- Pixel sizes: mdpi 108 · hdpi 162 · xhdpi 216 · xxhdpi 324 · xxxhdpi 432.
- Add a **monochrome** layer (108 dp) for Android 13+ themed icons.
- Play Store listing icon: 512×512 PNG.

Generate the foreground glyph and background separately (or cut the glyph out with BiRefNet). Then:

```bash
python scripts/mobile_icons.py --foreground glyph.png --background "#1E88E5" --out build/icons
```

Framework tools that do the same: `flutter_launcher_icons` (Flutter), `@capacitor/assets` (Capacitor), icon.kitchen (web UI). Check their maintenance status before adopting.

## 3. Vectorize

| Tool | Cost | Best for |
|---|---|---|
| **vtracer** (MIT) | Free, local | Flat, limited-color art and icons. `pip install vtracer` or `cargo install vtracer-cli`. Tune `filter_speckle`, `color_precision`, `layer_difference` |
| potrace (GPL) | Free | Monochrome logos/glyphs |
| **Recraft vectorize API** | **$0.01/call** | Complex, multi-color illustrations |
| Vectorizer.ai API | $0.05–0.20/image by volume; free test mode | Highest-fidelity traces |

Generate flat art for vectorization: "flat vector illustration, solid fills, no gradients, no texture, limited palette of N colors". vtracer output is then often good enough without paying for an API.

Android can't use SVG directly. Convert to VectorDrawable (Android Studio's Vector Asset tool, or `vd-tool`); simple paths convert cleanly.

## 4. Export and optimize

| Output | Tool |
|---|---|
| PNG | `oxipng -o 4 --strip safe --alpha *.png` |
| SVG | `svgo -f in/ -o out/` |
| WebP / AVIF (photos, large illustrations) | `cwebp -q 85`, `avifenc`, or `sharp` (Node) |
| iOS raster | @1x/@2x/@3x in an asset catalog (or a single PDF/SVG vector with "Preserve Vector Data") |
| Android raster | drawable-mdpi/hdpi/xhdpi/xxhdpi/xxxhdpi (1×/1.5×/2×/3×/4×) |

## 5. Provenance

Keep `manifest.json` entries (model ID, prompt, date, output hash) for every shipped asset. App store reviews and legal checks increasingly ask about AI-generated content.

## Sources

`research/2026-10-21/generators-compute-mobile.md`
