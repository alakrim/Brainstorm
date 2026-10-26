# Image → Asset Workflows

A research-backed playbook for turning **AI-generated images** (OpenAI Sunburst, Meta Muse Image) into **game and app assets**: 2D, 2.5D and 3D, for **Godot 4**, **Unity 6** and **mobile apps**.

Built for AI art-lead and orchestrator agents (and humans) starting a new project. **Agents: read [`AGENTS.md`](AGENTS.md) first.**

*Last full research pass: 2026-10-21.*

## Pick a workflow

| I need… | Workflow | Default pipeline | ~$/asset* |
|---|---|---|---|
| Any asset: good source images | [`workflows/00-source-images.md`](workflows/00-source-images.md) | Muse for volume, Sunburst for masters/edits/transparency | $0.01–0.20 |
| **3D props / environment pieces** | [`workflows/3d-props.md`](workflows/3d-props.md) | BiRefNet cutout → fal TRELLIS.2 or Tripo → Blender cleanup → gltf-transform | $0.30–0.70 (bulk self-hosted: $0.03–0.10) |
| **3D rigged + animated characters** | [`workflows/3d-rigged-characters.md`](workflows/3d-rigged-characters.md) | A-pose turnaround → Tripo 3D + Rig v3.0 + presets (Meshy for humanoids) | $0.90–1.10 |
| **Ready-made CC0 3D (characters, props, buildings)** | [`reference/free-3d-asset-sources.md`](reference/free-3d-asset-sources.md) | Verified KayKit / CC0 packs (jsDelivr) → hash-check → `check_glb.py` → gltf-transform | ~$0 |
| **2.5D: 2D sprites lit by dynamic lights** | [`workflows/2.5d.md#a`](workflows/2.5d.md#a-lit-sprites-normal-maps-for-2d-lighting) | Cutout → Laigter / Depth Anything 3 → normal map | ~$0 |
| **2.5D: 8-direction / isometric sprites** | [`workflows/2.5d.md#b`](workflows/2.5d.md#b-pre-rendered-3d--2d-sprites-dead-cells--isometric-rpg-style) | Image → rigged 3D → headless Blender ortho renders → sprite sheets | $0.30–1.10 per character |
| **2.5D: isometric tiles** | [`workflows/2.5d.md#c`](workflows/2.5d.md#c-isometric-tiles-and-props) | Reference-locked generation + snapping, or 3D → render | $0–0.40 |
| **2.5D: parallax backgrounds** | [`workflows/2.5d.md#d`](workflows/2.5d.md#d-parallax-layers) | Qwen-Image-Layered or depth bands + SAM → inpaint | $0.03–0.07 |
| **2.5D: animate one illustration** | [`workflows/2.5d.md#e`](workflows/2.5d.md#e-2d-skeletal--cutout-animation) | Split parts → Skeleton2D / Unity 2D Animation / Spine | $0 + time |
| 2D sprites / pixel art | [`workflows/2d-sprites.md`](workflows/2d-sprites.md) | Cutout → pixel snap / downscale → pack | ~$0.001 |
| Mobile app icons, illustrations, vectors | [`workflows/mobile-app-assets.md`](workflows/mobile-app-assets.md) | Sunburst → icon script / vtracer → optimize | ~$0.01–0.05 |

\* Beyond the source image, assuming ~2 attempts per accepted asset. Human review time not included.

## Reference

| File | Contents |
|---|---|
| [`reference/licenses.md`](reference/licenses.md) | Which models/tools are safe for commercial shipping, and red flags |
| [`reference/compute-and-pricing.md`](reference/compute-and-pricing.md) | Hosted APIs vs GPU rental, prices, billing gotchas, agent setup |
| [`reference/engine-import.md`](reference/engine-import.md) | Godot 4 / Unity 6 import settings, retargeting, headless automation |
| [`reference/free-3d-asset-sources.md`](reference/free-3d-asset-sources.md) | Verified CC0 / permissive 3D packs (KayKit via jsDelivr): licenses, formats, rigging, fetch script |
| [`scripts/`](scripts/README.md) | Tested CPU helper scripts: GLB check/cleanup/LODs, sprite rendering, normal maps, pixel snap, mobile icons |
| [`research/`](research/) | Raw dated research reports with full source lists |

## Key findings (2026-10-21)

1. **Hosted per-call APIs beat GPU rental for small batches.** fal TRELLIS.2 ($0.30), Tripo (~$0.35 + $0.25 rig) and Meshy cost less than the setup time of a self-hosted model under ~50 assets. Self-hosting only pays off at hundreds of assets.
2. **The best open image-to-3D model is TRELLIS.2 (MIT), but self-hosting it commercially needs a legal sign-off.** Its install depends on NVIDIA nvdiffrast, whose license is research/evaluation only. Its default background remover (RMBG-2.0) is also non-commercial; pass a pre-cut RGBA image. Hosted endpoints move these questions to the vendor. Step1X-3D (Apache-2.0) is the license-clean self-host fallback.
3. **Avoid Hunyuan3D open weights for worldwide releases.** The license excludes the EU, UK and South Korea, including use of the outputs there.
4. **Tripo is the most complete rigging API:** creatures as well as humanoids, and Mixamo/Unity/Unreal bone naming. Mixamo has no API and is manual only.
5. **Unity Humanoid needs FBX.** glTFast GLB imports skip the Avatar rig setup. Godot retargets GLB directly with `SkeletonProfileHumanoid`.
6. **Godot 4.7 can't import Draco- or meshopt-compressed GLBs**; Unity (glTFast) can. Ship plain GLBs to Godot and let both engines generate mesh LODs at import.
7. **For consistent multi-direction sprites, render them from 3D.** Generating frames as images drifts.
8. **Source-image discipline matters most:** flat lighting, plain background, A-pose, fixed style and subject blocks, references for every asset in a set.
9. **`gpt-image-1` retires 2026-10-23**, and `gpt-image-1.5`/`-mini` on 2026-12-01. Use `gpt-image-2.5-sunburst`/`-flare`.

## Open questions / next research

- An independent quality bake-off (Tripo H3.1/P2 vs Meshy 7.1 vs TRELLIS.2 vs Hunyuan 3.1) on our own art style. Results go in each workflow's "Measured results" table.
- A ready-made Modal/RunPod container for TRELLIS.2 + UniRig, so batches start in minutes.
- Sunburst's maximum number of reference images and Batch API support (sources conflict); Muse Image transparency and resolution.
- Real-world rig quality of UniRig/SkinTokens vs Tripo on stylized characters.

## Repo layout

```
AGENTS.md                 how agents should use and update this repo
workflows/                decision-ready pipelines, one per asset type
reference/                licenses, compute/pricing, engine import
scripts/                  tested CPU helper scripts
research/YYYY-MM-DD/      raw research reports (sources, unverified items)
```
