# 3D static props and environment pieces (image → GLB)

*Researched 2026-10-21. Prices were verified on vendor pages that day unless marked. Re-check if this is more than ~3 months old.*

## TL;DR

| Situation | Use | ~Cost per accepted asset |
|---|---|---|
| Under ~50 props, no infrastructure | **fal `fal-ai/trellis-2`** at 1024p ($0.30/call), then headless Blender cleanup | $0.30–0.70 |
| Low-poly / clean quad topology needed (mobile, stylized) | **Tripo H3.1** standard texture + quad (~$0.35), or **Tripo P2** (native quads, ≤25k) | $0.35–0.80 |
| Hundreds of props | **TRELLIS.2 self-hosted** on a rented 24 GB+ GPU (RunPod L40S/4090/A100 pod, or Modal) | $0.03–0.10 + one-off setup |
| Quick draft / blockout | fal `fal-ai/trellis` (v1, $0.02) | $0.02–0.05 |

Before committing a project to one vendor, run a **5-asset bake-off** on your own art style across 2–3 options (e.g. fal TRELLIS.2, Tripo H3.1, Meshy 6). Every published comparison was written by a vendor.

**Do not use Hunyuan3D open weights (2.0/2.1/Omni/Part) for a game shipped worldwide.** The Tencent license excludes the EU, UK and South Korea, and §5(c) makes using the outputs outside that territory unlicensed. See `reference/licenses.md`.

## Pipeline

```
1. Source image       Sunburst/Muse → single prop, flat light, plain bg     (00-source-images.md)
2. Cutout             BiRefNet (MIT) → RGBA PNG                              (~$0.0005)
3. Image → 3D         fal trellis-2 | Tripo | self-hosted TRELLIS.2           ($0.02–0.40)
4. Inspect            scripts/check_glb.py → tris, textures, scale
5. Clean + optimize   scripts/blender/glb_cleanup.py → weld, decimate, origin, LODs
6. Compress           gltf-transform (resize textures, webp/ktx2)
7. Engine import      reference/engine-import.md (Godot / Unity)
```

### 1. Source image

Use the "3D prop" framing block from [`00-source-images.md`](00-source-images.md). Points specific to 3D:

- **Flat, shadowless lighting.** The model bakes visible lighting into the texture.
- **Whole object visible with margin.** Cropped parts come back as holes or invented geometry.
- **Three-quarter view from slightly above** gives the model the most information for one image. For objects with a distinctive back (signs, cabinets), also generate a back view and use a multi-view endpoint.
- Avoid thin transparent parts (glass, wire fences, hair strands). Model them by hand or as alpha cards.

### 2. Cutout

Run BiRefNet (MIT) yourself, or use `rembg` with the `birefnet-general` or `isnet-general-use` model. Sunburst can output a transparent PNG directly.

**Important for self-hosted TRELLIS.2:** its default pipeline loads `briaai/RMBG-2.0`, which is **non-commercial (CC BY-NC 4.0)**. If you pass an RGBA image with a real alpha channel, TRELLIS.2 uses it as-is and skips its own background removal. Always pass a pre-cut RGBA PNG. The config still references RMBG-2.0 at load time; check that the weights aren't used, or remove the reference.

### 3. Image → 3D: options

| Option | Quality notes | Price | Output | Notes |
|---|---|---|---|---|
| **fal `fal-ai/trellis-2`** | Strong geometry, full PBR (base color, roughness, metallic) | $0.25 (512p) / **$0.30 (1024p)** / $0.35 (1536p) | GLB | Easiest start. Pay per call, no setup |
| **Tripo H3.1** (API) | Best topology per vendor tests; delighting | 20 credits (no texture) / 30 (standard) / 40 (detailed); +5 quad; +10 smart low-poly; ≈ $0.01/credit | GLB, FBX | Smart low-poly 500–20k faces. **Tripo P2** (Sep 2026): native quads ≤25k, good for hard-surface |
| **Meshy 6 / 7.1** (API) | Best textures per vendor tests | 30 credits textured (≈ $0.60 derived); 6-lite 15 credits; fal Meshy 6 $0.80 | GLB, FBX, OBJ, USDZ | Remesh/quad 5 credits. API needs Pro plan or above. The `lowpoly` model type retires 2026-10-30 |
| **Hunyuan 3.1** (hosted, fal) | Highly rated for realism | $0.225 geometry → $0.525 with PBR | GLB | Hosted terms unread; see license note above |
| **TRELLIS.2 self-hosted** | Same as fal | ~$0.01–0.03 compute (+ cold start) | GLB up to 4096² textures | MIT. 24 GB VRAM, Linux, CUDA 12.4. Exports opaque materials by default |
| **Pixal3D** (TencentARC, MIT) | Newer, TRELLIS.2 backbone, multi-view with camera poses | Self-host | GLB PBR | Experimental; try only if you need multi-view conditioning |
| Step1X-3D (Apache 2.0) | Decent; non-PBR texture | Self-host, 27–29 GB | GLB | License-clean fallback |
| fal `fal-ai/trellis` (v1) | Older, lower detail | $0.02 | GLB | Blockouts, background props |

#### Self-hosting TRELLIS.2 (batches)

```bash
# On a rented Linux GPU with ≥24 GB VRAM (RunPod L40S/A100/4090 pod)
git clone -b main https://github.com/microsoft/TRELLIS.2.git --recursive
cd TRELLIS.2
. ./setup.sh --new-env --basic --flash-attn --nvdiffrast --nvdiffrec --cumesh --o-voxel --flexgemm
# PyTorch 2.6 / CUDA 12.4. Without flash-attn support: export ATTN_BACKEND=xformers
# Needs Hugging Face access to the gated facebook/dinov3-vitl16-pretrain-lvd1689m
```

Or use ComfyUI with `visualbruno/ComfyUI-Trellis2` (MIT). Its nodes also do quad remesh, UV unwrap, simplify and hole filling.

Rules for cost: keep the pod warm for the whole batch (model load dominates), process the whole queue, then **destroy the pod**. Example: 300 props × ~1 min on an L40S community pod ($0.79/h) ≈ $4 compute.

### 4. Inspect

```bash
python scripts/check_glb.py raw/crate.glb --budget mobile
```

Typical raw AI output: 50k–2M triangles, 2K–4K textures, arbitrary scale and origin, sometimes small holes.

### 5. Clean and optimize

```bash
blender -b -P scripts/blender/glb_cleanup.py -- raw/crate.glb clean/crate.glb --target-tris 3000 --lods 0.5,0.25
```

(See [`scripts/README.md`](../scripts/README.md) for exact options and test status.)

Triangle budgets (industry rules of thumb):

| Asset | Mobile / web | PC / console |
|---|---|---|
| Small prop | 300–3k | 2k–10k |
| Hero prop / large environment piece | 3k–10k | 10k–50k |
| LOD chain | LOD0 100%, LOD1 ~50%, LOD2 ~25%, LOD3 ~10% | same |

When to do more than decimate:
- **Quad topology needed** (it will be deformed, or artists will edit it): use the vendor's quad remesh (Tripo +5 credits, Meshy Remesh 5 credits), or QuadriFlow / Instant Meshes / AutoRemesher (MIT) in Blender, then bake.
- **Heavy decimation (<10%) on a textured mesh:** bake the high-poly base color and normal onto the low-poly in Blender Cycles (selected-to-active). Plain decimation keeps the UVs but smears detail.
- **Collision:** don't use the render mesh. Let the engine generate a convex or simplified collider (see `reference/engine-import.md`).

### 6. Compress

```bash
npm i -g @gltf-transform/cli
gltf-transform resize clean/crate.glb tmp.glb --width 1024 --height 1024     # mobile: 512–1024, PC: 2048
gltf-transform webp tmp.glb out/crate.glb                                    # or: ktx2 (needs KTX-Software)
```

Test compressed GLBs in the target engine before batch-processing. Engine support for Draco, meshopt and KTX2 differs; see `reference/engine-import.md`.

### 7. Engine import

See [`reference/engine-import.md`](../reference/engine-import.md).

## Measured results

*Add real numbers from projects here: date, project, vendor, assets, accept rate, $/accepted asset, time.*

| Date | Project | Pipeline | Assets | Accept rate | $/accepted | Notes |
|---|---|---|---|---|---|---|
| | | | | | | |

## Sources

See `research/2026-10-21/image-to-3d-and-rigging.md` for full sources and the unverified list.
