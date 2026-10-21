# Raw research: source image generators, GPU hosting, mobile app assets (2026-10-21)

> Raw report from a research agent, kept for traceability. Tags: **[V]** verified on a primary page, **[S]** search snippet / secondary source, **[U]** unverified or conflicting. Curated guidance lives in `workflows/` and `reference/`.

## 0. Time-sensitive

- **`gpt-image-1` retires 2026-10-23** [V, OpenAI deprecations page].
- `gpt-image-1.5`, `gpt-image-1-mini`, `chatgpt-image-latest` retire **2026-12-01** [V]. Replacements: `gpt-image-2.5-sunburst`, `gpt-image-2.5-flare`.
- `dall-e-2` / `dall-e-3` retired 2026-05-12 [V].

## 1. Source image generators

### OpenAI "Sunburst" — `gpt-image-2.5-sunburst`

Published model ID in the GPT-Image-2.5 family, alongside `gpt-image-2.5-flare` (faster). Release ~2026-09-08 [S]. Positioned for precise editing and reference-subject preservation; slower than Flare.

| Attribute | Finding | Status |
|---|---|---|
| API | OpenAI Images API + Responses API; also OpenRouter, Vercel AI Gateway, Runware, Replicate (`openai/gpt-image-2.5-sunburst`) | [V]/[S] |
| Price | Image input $8/1M tokens, output $30/1M, cached input $2/1M. Batch $4 in / $15 out | [V] |
| Per image | Token-billed; third-party estimates for same-rate gpt-image-2 at 1024²: ~$0.006 low, ~$0.053 medium, ~$0.211 high | [S] |
| Batch | OpenAI table lists Batch rates; a community report says gpt-image-2 Batch unsupported | [U] |
| Max resolution | Custom WxH, edges multiple of 16, max edge 3840, max 8,294,400 px, aspect 1:3–3:1; >2560×1440 "experimental" | [V] |
| Transparent background | Yes: `background: "transparent"` with png/webp | [V] |
| Editing / inpainting | Yes; mask (alpha, same size/format) applies to first image | [V] |
| Reference images | Up to 16 per OpenRouter; OpenAI guide shows 4, no stated max | [U] |
| Multi-view / sprite sheets | No official feature | [S] |
| Commercial use | OpenAI terms assign output rights to user (primary page 403); org verification required | [U] |

### Meta "Muse Image"

Launched 2026-07-07 (Meta Superintelligence Labs; codename "Mango" [S]). Consumer-first (Meta AI app, meta.ai, Instagram, WhatsApp). "Agentic": plans composition, can search the web, self-revises.

- **fal:** `meta/muse-image/text-to-image` and `meta/muse-image/edit`, **$0.01/image**, tagged "Commercial use" [V].
- **Meta Model API** (reseller-reported): model `muse-image-1.0`, base `https://api.meta.ai/v1`, `/images/generations`, `/images/edits`, `/responses`; `size` sets aspect only; webp/png/jpeg; $0.01/image, failed/safety-removed not billed [S].

| Attribute | Finding | Status |
|---|---|---|
| Max resolution | Not stated; fal sample 2048×1152 | [U] |
| Transparent background | Not stated — plan on chroma-key or matting | [U] |
| Editing | Conversational, draw-on-photo, legible text | [V] |
| Reference images | Multiple references ("composition from multiple reference images"); fal sample used 3 | [V]/[U] |
| Commercial use | fal tags "Commercial use"; Meta terms not reachable | [U] |
| Provenance | Invisible "Content Seal" watermark in consumer apps; not C2PA/SynthID-compatible; API output status unknown | [S]/[U] |

Alternatives: `gpt-image-2` (same token price); Nano Banana 2 on fal $0.08/image [V].

### Prompt tips for asset-ready output [U until tested]

- **Canonical character block** pasted verbatim in every prompt (age, build, hair, outfit materials, palette, silhouette).
- **Neutral pose:** "A-pose, arms slightly away from body, upright, relaxed face, flat even lighting".
- **Orthographic views:** "orthographic front view, no perspective distortion, same scale, same baseline". Generate side/back as separate edit calls referencing the front view — locks proportions better than one turnaround sheet.
- **Isolated object:** "single object centered, isolated, plain neutral gray (or #00FF00) background, no ground plane". With OpenAI request transparent PNG directly.
- **Style lock:** fixed style block reused in every prompt, same reference image across the set.
- **Sprite sheets:** expect grid drift; generate frames individually with a reference, then assemble by script.
- Avoid text/logos in art; add text in engine.
- **Mobile icons:** full-bleed square, centered glyph, no rounded corners (OS applies mask).

## 2. Hosted inference and GPU rental

### On-demand GPU $/hour

| GPU | RunPod pod (secure / community) | Modal | Replicate | Lambda | HF Endpoints | fal |
|---|---|---|---|---|---|---|
| RTX 4090 | $0.89 / $0.34 | — | — | — | — | — |
| RTX A6000 | $0.59 / $0.33 | — | — | $1.09 | — | — |
| L4 | $0.59 / $0.44 | $0.80 | — | — | $0.70–0.80 | — |
| A10/A10G | — | $1.10 | — | $1.29 | $1.00 | — |
| L40S | $1.09 / $0.79 | $1.95 | $3.51 | — | $1.80 | — |
| A100 80GB | $1.79 / $1.19 | $2.50 | $5.04 | $2.79 (8× SXM) | $2.50–3.60 | — |
| H100 80GB | $2.89–3.99 / $1.99–2.69 | $3.95 | $5.49 | $3.29–4.29 | $10.00 (GCP) | $4.50 list |
| H200 | — | $4.54 | $5.49 | — | $5.00 | $6.00 |

RunPod serverless/hr: 4090 $1.10, L4 $0.69, L40S $1.75, A100 $2.72, H100 $4.79 [V].

### Billing and cold starts

| Platform | Billing | Idle | Cold start |
|---|---|---|---|
| RunPod serverless | Per second | Active workers billed (up to 30% off) | FlashBoot claims sub-200 ms; third-party test ~10–15 s [U] |
| RunPod pods | Hourly rate | While running | n/a |
| Modal | Per second incl. boot | Until `scaledown_window` (default 60 s); scale to zero free | Container ~1 s, model load longer; $30/mo free credit (Starter) |
| fal serverless (custom apps) | Per second incl. setup/idle | `keep_alive` default 60 s | PENDING/DOCKER_PULL unbilled; 5xx not charged |
| Replicate public models | Per second of processing | Setup/idle free | Can cold-boot |
| Vast.ai | Per second, no minimum | While running | Interruptible 50%+ cheaper, preemptible |
| HF Inference Endpoints | Per minute while deployed | — | — |
| HF ZeroGPU | Free / PRO $9/mo | Quota | — |

### Agent-friendliness

| Platform | Setup | Notes |
|---|---|---|
| fal | `pip install fal-client`, `FAL_KEY` | Hosted endpoints per call; sync + queue APIs; best for named models |
| Modal | `pip install modal`, `modal setup` | Python decorators define GPU functions; best for custom code; `.map()` for batches |
| Replicate | Python/Node clients, `REPLICATE_API_TOKEN` | Easy hosted open models |
| RunPod | `runpodctl config --apiKey` | Pod lifecycle via CLI |
| Vast.ai | `pip install vastai`, `vastai set api-key` | Scriptable; host reliability varies |
| Lambda | REST, bearer auth | Launch rate-limited |

### Recommendations

- **Bursts (a few dozen assets):** fal for hosted models (fal TRELLIS image-to-3D listed $0.02/generation [V]); Modal for custom Python.
- **Batches (hundreds):** RunPod secure pod (L4 $0.59/h, A100 $1.79/h) or Modal `.map()`; destroy pod after. Example: 500 assets × 10 s GPU ≈ 1.4 GPU-h ≈ $0.82 on L4 (+~2× for retries/idle). Vast.ai interruptible with checkpointing for cheapest.

## 3. Mobile (non-game) assets

### Vectorization

| Tool | Type | Price | Notes |
|---|---|---|---|
| vtracer | MIT, Rust + Python/Node bindings | Free | `pip install vtracer`, `cargo install vtracer-cli`; color clustering default, `--clustering bw`; tune `filter_speckle`, `color_precision`, `gradient_step` |
| potrace | Open source (GPL), B/W | Free | Monochrome logos [U] |
| Recraft vectorize | API | **$0.01/call** [V] | `POST https://external.api.recraft.ai/v1/images/vectorize` |
| Vectorizer.ai | API | $0.05–0.20/image by volume; free test mode [V] | SVG, PDF, EPS, DXF, PNG |

### App icons

- **iOS:** one 1024×1024 PNG, Single Size AppIcon (Xcode 14+). No alpha, no pre-rounded corners (ITMS-90717) [S].
- **Android adaptive** [V]: foreground + background layers 108×108 dp; safe zone 66×66 dp centered; outer 18 dp reserved for mask/parallax; logo 48–66 dp; px: mdpi 108, hdpi 162, xhdpi 216, xxhdpi 324, xxxhdpi 432; monochrome layer 108 dp for themed icons. Play Store icon 512×512 [U].
- Tooling (verify): flutter_launcher_icons, @capacitor/assets, icon.kitchen.

### Lottie

LottieFiles AI: raster-to-vector, prompt-to-animation. Individual $19.99/user/mo (300 AI credits), Team $24.99 (600) [V]. Output is a rough draft; hand-clean.

### Optimization

| Tool | Use |
|---|---|
| oxipng (MIT) | `oxipng -o 4 --strip safe --alpha *.png` |
| SVGO (MIT) | `svgo` SVG minify |
| cwebp / avifenc / sharp | WebP/AVIF encode (squoosh-cli status unverified) |

### Recommended pipeline

1. Generate with Sunburst (native transparent PNG, precise edits) or Muse ($0.01, reference-heavy composition). Pin model ID; log prompt + `usage`.
2. Background: Sunburst transparent; Muse → chroma green → matting.
3. Normalize: crop/center/pad by script.
4. Vectorize: vtracer (flat art) or Recraft $0.01 (complex).
5. Icons: iOS 1024 no-alpha; Android 108 dp layers, 66 dp safe zone.
6. Optimize: oxipng, SVGO, WebP/AVIF; @1x/@2x/@3x and density buckets.
7. Provenance: keep model IDs, prompts, output hashes.

## 4. Open items

Sunburst reference max and Batch support; Muse transparency, max resolution, reference limit, license text, API watermark; OpenAI terms primary text; Apple icon rules primary text; RunPod cold start; Vast.ai live prices; capacitor-assets/icon.kitchen maintenance.

## 5. Sources

OpenAI: developers.openai.com/api/docs/pricing · developers.openai.com/api/docs/guides/image-generation · developers.openai.com/api/docs/deprecations
Sunburst/Muse: openrouter.ai/openai/gpt-image-2.5-sunburst · hackernoon.com (GPT Image 2.5 Sunburst on Replicate) · engadget.com (Muse Image) · fal.ai/models/meta/muse-image/edit · letsdatascience.com (fal opens Muse) · orcarouter.ai/blog/muse-image · fal.ai/pricing
Hosting: runpod.io/pricing · docs.runpod.io/runpodctl/overview · modal.com/pricing · modal.com/docs/guide/cold-start · replicate.com/pricing · docs.fal.ai · docs.lambda.ai/api/cloud · lambda.ai/pricing · vast.ai/pricing · docs.vast.ai/cli/get-started · huggingface.co/docs/inference-endpoints/en/pricing
Mobile: github.com/visioncortex/vtracer · recraft.ai/docs/api-reference/endpoints · vectorizer.ai/pricing · developer.android.com/develop/ui/views/launch/icon_design_adaptive · developer.apple.com/documentation/xcode/configuring-your-app-icon · lottiefiles.com/pricing · github.com/shssoichiro/oxipng · github.com/svg/svgo
