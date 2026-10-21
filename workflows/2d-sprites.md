# 2D sprites, pixel art and UI elements

*Researched 2026-10-21. Lower priority than 2.5D/3D for current projects; see also `2.5d.md` (lit sprites, pre-rendered sprites).*

## TL;DR

```
1. Generate at 2–4× final size, flat bg (green/transparent), style + subject blocks   (00-source-images.md)
2. Cutout: BiRefNet / rembg (commercial-safe models only)
3a. Painted sprites: downscale with Lanczos to final size
3b. Pixel art: scripts/pixel_snap.py, or PixelOE / unfake.js; one palette per character
4. Animation frames: route B in 2.5d.md (3D → render) > skeletal (2.5d.md E) > per-frame edit calls
5. Pack: sprite sheet + JSON → Godot SpriteFrames / Unity Sprite Atlas
```

Cost beyond image generation: ~$0.0005–0.01 per sprite.

## Background removal

| Model | License for shipping | How |
|---|---|---|
| **BiRefNet** (general / HR / matting) | Code MIT; weights license to confirm (see `reference/licenses.md`) | Self-host (~3.5 GB VRAM) or `rembg -m birefnet-general` |
| **rembg `birefnet-general`** | MIT | `pip install "rembg[cpu]"`, then `rembg p -m birefnet-general in/ out/` (runs on CPU). **Always pass `-m`**: rembg's default model is the non-commercial RMBG-2.0 |
| rembg `isnet-general-use` | Code Apache-2.0, weights unstated | Lighter/faster alternative |
| Replicate background remover | ~$0.0005/image | Zero setup |
| ❌ **RMBG-2.0 / rembg `bria-rmbg`** | **CC BY-NC**: needs a paid BRIA license | Don't use for shipped assets |

Sunburst can output transparent PNGs directly, which skips this step.

## Pixel art

Generated "pixel art" is not on a real pixel grid: pixels drift, there are anti-aliased edges and hundreds of colors. Always snap it.

| Tool | License | Use |
|---|---|---|
| **PixelOE** | Apache-2.0 | `pixeloe.pixelize in.png --target_size 64 --patch_size 8`. Edge-aware, keeps outlines |
| **unfake.js** / `unfake` (PyPI) / unfake-core (Rust) | MIT | Auto-detects the grid, snaps, reduces palette (`maxColors`) |
| `scripts/pixel_snap.py` | this repo | Simple, dependency-light fallback |
| Pixelorama | MIT | Free pixel editor for manual fixes |
| Retro Diffusion | Paid Aseprite extension | Pixel-native generation |
| PixelLab | Hosted, API + MCP | Pixel-native characters, 4/8 directions, tilesets |

Rules:
- Never run AI upscalers (Real-ESRGAN) on pixel art. Scale with integer nearest-neighbour only.
- Lock one palette per character (or per game) and apply it to every frame.
- Godot: set texture filter to **Nearest** (project setting `rendering/textures/canvas_textures/default_texture_filter`). Unity: Filter Mode **Point**, Compression **None**, Pixels Per Unit consistent.

## Animation frames (cheapest to most consistent)

1. **Per-frame edit calls** (Sunburst edit with the idle frame as reference, "same character, pose: <...>"): cheap but drifts. OK for 2–4 frame idles and UI.
2. **Image-to-video** (e.g. Wan 2.2 class models) → `ffmpeg -i clip.mp4 -vf fps=12 f_%03d.png` → cutout → snap. Medium consistency; license and price per model unverified.
3. **2D skeletal rig** (`2.5d.md` E): consistent, few parts.
4. **3D → pre-rendered sprites** (`2.5d.md` B): fully consistent, any number of directions.

## Packing

- Godot imports a plain sheet: `SpriteFrames` → "Add frames from sprite sheet" (or by script; see `reference/engine-import.md`). `AtlasTexture` for UI.
- Unity: Sprite Mode Multiple → Slice by grid (or by script via `ISpriteEditorDataProvider`), then a **Sprite Atlas**.
- TexturePacker ($49.99 perpetual, indie discount) if you need trimming, polygon packing and exporters. `scripts/blender/render_sprite_directions.py` can assemble simple grid sheets + JSON.

## Painted / HD sprites

- Upscale with Real-ESRGAN (BSD-3; `RealESRGAN_x4plus_anime_6B` for illustrated art) only when the source is smaller than the target.
- Downscale with Lanczos; keep 1–2 px of transparent padding to avoid bleeding in atlases.

## Sources

`research/2026-10-21/2.5d-and-2d-tooling.md`
