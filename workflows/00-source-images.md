# 00 — Source images: generating asset-ready images

Every workflow in this repo starts from a generated image. A good source image saves more time and money than any later step. The 3D and 2.5D tools work only as well as their input.

*Researched 2026-10-21. Re-check prices and model IDs if this is more than ~3 months old.*

## The two generators

| | OpenAI **Sunburst** (`gpt-image-2.5-sunburst`) | Meta **Muse Image** (`muse-image-1.0`) |
|---|---|---|
| Access | OpenAI Images API and Responses API; also Replicate, OpenRouter | fal (`meta/muse-image/text-to-image`, `meta/muse-image/edit`); Meta Model API `https://api.meta.ai/v1` (reported) |
| Price | Token-billed: $30 per 1M image output tokens, $8 per 1M image input tokens. Batch is half price. Roughly $0.01 (low) to $0.21 (high quality) per 1024² image (third-party estimate). Log `usage` from each call to get the real number | **$0.01 per image** flat (fal, verified) |
| Transparent PNG | **Yes**: `background: "transparent"` with png/webp output | **No** (not documented). Use a flat chroma background and cut it out |
| Max resolution | Up to 3840 px edge, 8.3 MP total, aspect 1:3–3:1 (above 2560×1440 is "experimental") | Not documented; fal samples are 2048×1152. `size` sets aspect ratio only |
| Editing / references | Precise edits with masks; multiple reference images (OpenAI shows 4; OpenRouter says 16) | Conversational edits, multi-image composition (3+ references shown) |
| Best at | Exact edits, keeping a subject identical, transparency, text | Cheap volume, composition from references |
| Sibling | `gpt-image-2.5-flare`: same price, faster, less precise | — |

**Deprecations (verified on OpenAI's deprecations page):** `gpt-image-1` retires **2026-10-23**. `gpt-image-1.5`, `gpt-image-1-mini` and `chatgpt-image-latest` retire **2026-12-01**. Don't build on them.

### Which one to use

- **Bulk exploration and concept variants:** Muse Image ($0.01 flat).
- **The final "master" image for each asset:** Sunburst at medium/high quality. Use it when the asset needs a transparent background, an exact edit, or must match a reference.
- **Turnaround views of a character** (front → side/back): Sunburst edit with the front view as reference. Identity preservation is its strength.
- **Large batches where turnaround time doesn't matter:** Sunburst via the Batch API (half price).

Licensing: both vendors indicate commercial use of outputs is allowed (OpenAI terms assign output rights to the user; fal tags Muse "Commercial use"). Neither primary terms page could be read during research **(unverified)**. Ownership is contractual, not a copyright guarantee. Avoid trademarked characters, logos and real people's likenesses.

Provenance: Meta adds an invisible watermark to Muse output in its consumer apps. Whether API output carries it is unknown.

## Prompt blocks

Write these once per project and paste them **verbatim** into every prompt. Changing the wording changes the result.

### Style block (one per project)

```
STYLE: <e.g. stylized hand-painted, chunky proportions, soft cel shading,
2px dark outline, limited palette of warm earth tones>. Even, flat, neutral
lighting from the front. No cast shadows, no rim light, no ambient occlusion
baked in, no text, no logos, no watermark.
```

Flat lighting matters most for 3D and 2.5D: image-to-3D models bake whatever lighting they see into the texture, and 2D normal-map lighting needs an unlit base.

### Subject block (one per character or prop family)

```
SUBJECT: <name>, <age/build/silhouette>, <hair>, <outfit with materials and
colors>, <distinctive features>. Empty hands.
```

### Framing blocks (pick by target workflow)

| Target | Framing block |
|---|---|
| 3D prop | `Single object, centered, whole object fully visible with margin, three-quarter view from slightly above, orthographic, plain flat light-gray background, no ground plane, no shadow.` |
| 3D character | `Full body, front view, A-pose with arms 30–45° away from the body, legs slightly apart, fingers spread, facing camera, orthographic, no perspective distortion, plain flat light-gray background, no shadow.` |
| Turnaround view (edit call) | `Same character as the reference image, identical proportions, outfit and colors. Show the <side/back> view, same A-pose, same scale and baseline, orthographic.` |
| 2D sprite / 2.5D lit sprite | `Single <subject>, <side/three-quarter> view, centered, full figure visible, flat even lighting, plain #00FF00 green background` (or transparent with Sunburst) |
| Isometric tile/prop | `Isometric view, 2:1 dimetric projection, camera 30° above horizon rotated 45°, single tile footprint, consistent with reference image, transparent background` |
| Parallax scene | `Wide side-scrolling game background, clearly separated foreground, midground and far background, no characters, flat even lighting` |
| App icon | `App icon artwork, full-bleed square, single centered glyph with generous padding, no rounded corners, no text` |

### Background choice

- Use **Sunburst transparent PNG** when available. It's the cleanest.
- Otherwise use **flat light gray** for 3D input: neutral, and it won't tint edges. Use **#00FF00 green** for 2D sprites that need a cutout, unless the subject itself is green.
- Then run background removal anyway (BiRefNet, see `reference/licenses.md`). Many 3D pipelines expect clean RGBA.

## Consistency across a set

1. Generate the **hero reference** first: one image per character, or one style-defining prop. Get it approved.
2. Generate every other asset as an **edit/reference call** that includes the hero reference image plus the style block.
3. For characters, generate the front view, then side and back as separate edit calls referencing the front. This locks proportions better than asking for a turnaround sheet in one image.
4. Don't ask for sprite sheets or grids in one image. Frames drift. Generate frames individually and assemble them with a script.
5. Keep a `manifest.json` per asset: model ID, prompt, reference image hashes, size/quality, cost (`usage`), date.

## Resolution guidance

| Target | Generate at |
|---|---|
| Image-to-3D input | 1024–2048 px square (TRELLIS.2 downsizes to 1024 internally; extra resolution helps hosted texture stages) |
| 2D sprite / pixel art | 2–4× the final size, then downscale/snap |
| Parallax background | Final width or wider; tile edges to be made seamless later |
| App icon | 1024×1024 |
