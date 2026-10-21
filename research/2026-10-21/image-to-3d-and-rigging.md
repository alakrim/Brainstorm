# Raw research: image → game-ready 3D (props and rigged characters) (2026-10-21)

> Raw report from a research agent, kept for traceability. "Verified" = primary source read (GitHub README, docs, license text, vendor pricing page). "Secondary" = vendor/aggregator blog. Spot-checked by the orchestrator on 2026-10-21: fal `trellis-2` pricing ($0.25/0.30/0.35) and Tripo rig pricing (25 credits, Rig Check free, bone specs) confirmed. Curated guidance lives in `workflows/3d-props.md` and `workflows/3d-rigged-characters.md`.

## 0. Summary

- **Best open-source image-to-3D:** Microsoft **TRELLIS.2** (MIT, 4B params, PBR GLB, 24 GB VRAM). **Pixal3D** (Tencent ARC, MIT, May 2026, TRELLIS.2 backbone, multi-view Sep 2026) is newest; treat as experimental.
- **Hunyuan3D open weights are a licensing trap for worldwide games.** Tencent Community License (2.1 text read directly): does not apply in the EU, UK or South Korea; §5(c) makes using outputs outside the Territory unlicensed; 1M MAU cap; outputs may not be used to improve other AI models. Hunyuan 3.0/3.1 are hosted-only (no weights).
- **TRELLIS.2 catch:** default pipeline downloads `briaai/RMBG-2.0` (CC BY-NC 4.0) for background removal and needs gated `facebook/dinov3-vitl16-pretrain-lvd1689m` (license "other"). Pass a pre-cut RGBA image (the code uses non-trivial alpha directly and skips background removal).
- **Best per dollar hosted, props:** fal TRELLIS.2 $0.25–0.35; Tripo H3.1 standard texture + quad ≈ $0.35; Hunyuan 3.1 on fal $0.225–0.525.
- **Rigged characters hosted:** Tripo (Rigging v3.0, creatures supported, 25 credits) and Meshy (humanoid-only auto-rig, 5 credits). Open-source rigging (UniRig, SkinTokens, Puppeteer) is MIT/Apache, single rented GPU.
- **Mixamo:** usable manually, but terms ban using outputs to train AI, no automation API, reported "maintenance mode". Don't build bulk pipelines on it.

## 1. Open-source image-to-3D

| Model | Repo | License | VRAM | Time | Texture | Input |
|---|---|---|---|---|---|---|
| **TRELLIS.2** (Dec 2025) | microsoft/TRELLIS.2 | MIT (+ RMBG-2.0/DINOv3 caveats) | 24 GB, Linux | H100: 512³ ~3 s, 1024³ ~17 s, 1536³ ~60 s | PBR (base color, roughness, metallic, opacity), up to 4096²; exports OPAQUE by default | Single image |
| **Pixal3D** (May/Sep 2026) | TencentARC/Pixal3D | MIT | `--low_vram` flag | Reseller: 6–7 min | PBR GLB | Single or multi-view with camera poses |
| **Hunyuan3D 2.1** (Jun 2025) | Tencent-Hunyuan/Hunyuan3D-2.1 | Tencent Community License | 10 GB shape, 21 GB texture, 29 GB both | ~1 min hosted | PBR | Single; `2mv` variant takes 4 views |
| Hunyuan3D-Omni / Part | Tencent-Hunyuan | Community License | 10 GB | — | Geometry / parts | Image + control |
| **Step1X-3D** (May 2025) | stepfun-ai/Step1X-3D | Apache 2.0 | 27–29 GB | ~152 s | Texture (not PBR) | Single |
| Direct3D-S2 | DreamTech | MIT (secondary) | 10–24 GB | — | Geometry only | Single |
| TripoSG | VAST-AI-Research | MIT (secondary) | ~8 GB | — | Geometry only | Single |
| TripoSR / SF3D / SPAR3D | VAST / Stability | TripoSR MIT; SF3D/SPAR3D Stability Community (free < $1M revenue) | 6–7 GB | <1 s | Basic | Draft quality |
| PartCrafter | wgsxm/PartCrafter | MIT | 8 GB | — | Geometry, multiple parts | Single |
| SAM 3D Objects | facebookresearch/sam-3d-objects | SAM License | — | — | Gaussian splats, not mesh | Image + mask |
| PartPacker | NVIDIA | Non-commercial | — | — | — | Avoid |

Running on rented GPUs:
- ComfyUI: `visualbruno/ComfyUI-Trellis2` (MIT, active to Sep 2026; shape, multi-view, texturing, quad remesh, UV unwrap, simplify, fill holes, weld; supports Pixal3D) and `PozzettiAndrea/ComfyUI-TRELLIS2` (ComfyUI Manager; T-pose/RMBG workflows). `visualbruno/ComfyUI-Hunyuan3d-2-1`.
- Raw: `git clone -b main https://github.com/microsoft/TRELLIS.2.git --recursive && . ./setup.sh --new-env --basic --flash-attn --nvdiffrast --nvdiffrec --cumesh --o-voxel --flexgemm` (PyTorch 2.6, CUDA 12.4; `ATTN_BACKEND=xformers` without flash-attn).
- Pixal3D: `python inference.py --image in.png --output out.glb [--low_vram] [--resolution 1024]`; `python inference_mv.py --views_dir <dir> --output out.glb`.
- No official RunPod/Modal template for TRELLIS.2; write your own image + handler.
- Self-hosted marginal cost ≈ $0.01–0.03/asset (estimate); cold start and model load dominate — keep a warm pod for batches.

Hosted endpoints:

| Endpoint | Price |
|---|---|
| fal `fal-ai/trellis-2` | $0.25 (512p) / $0.30 (1024p) / $0.35 (1536p) — **verified** |
| fal `fal-ai/trellis` (v1) | $0.02 — **verified** |
| fal `fal-ai/hunyuan3d-v3/image-to-3d` | Geometry $0.225, Normal $0.375, LowPoly $0.45; +$0.15 each for PBR / multi-view / custom face count |
| fal Meshy 6 image-to-3D | $0.80 |
| fal Tripo H3.1 | $0.20 / $0.30 / $0.40; +$0.05 quad (secondary) |
| fal hyper3d/rodin | ~$0.40 (snippet) |
| Replicate `fishwowater/trellis2` | ~$0.89/run on A100 (community) |

## 2. Paid APIs

| Service | Cost | Texturing | Retopo / low-poly | Rig / animation | Formats | API | Rights |
|---|---|---|---|---|---|---|---|
| **Meshy** (7.1, 6, 6-lite) | Image-to-3D: mesh 20 cr, textured 30, 8K 35; 6-lite 5/15; remesh 5; UV 5; retexture 10–15. ~$0.02/credit derived (unverified) → textured ≈ $0.60. fal $0.80 | Up to 8K; `remove_lighting` | Smart Topology, Remesh, quad; `lowpoly` model type retires 2026-10-30 | Auto-rig 5 cr (**humanoid only**); animation 3 cr/action; text-to-motion 3–10; `pose_mode: a-pose/t-pose` | FBX, GLB, OBJ, STL, USDZ, Blend | Pro and above | Free tier CC BY 4.0; paid: you own |
| **Tripo** (H3.1, P2, Rig v3.0) | ~$0.01/credit. H3.1: 20 / 30 / 40 / 50 (8K). Quad +5, smart low-poly +10, detailed geometry +20, parts +20 → standard + quad ≈ $0.35 | PBR, 8K, delighting | Smart low-poly 500–20k faces; quad FBX up to 150k; **P2 (2026-09-21)** native quad ≤25k quads | Rig Check free; auto-rig **25 cr**; animation presets 10 cr. Rig types: biped, quadruped, hexapod, octopod, avian, serpentine, aquatic, others. Bone specs (biped): Tripo, Mixamo, + v3.0 ActorCore, Unity, Unreal, VRM | GLB, FBX | Yes | Free tier reportedly non-commercial; paid commercial |
| **Hunyuan 3D hosted** | Tencent Cloud ~25 cr (+10 options), full ≈ $1 (secondary); fal $0.225–0.525; 20 free/day on site | 4K PBR | Face count 40k–1.5M | — | GLB, OBJ | Tencent Cloud, fal, Replicate | Hosted terms not read |
| **Rodin / Hyper3D** (Gen-2.5) | ~$0.40 fal; direct pricing unclear | PBR | Quad, Smart Low-Poly (Creator $30/mo) | — | GLB, FBX, OBJ, USDZ, STL | Business plan ($120/mo) | Paid plans only |

Quality: no independent benchmark. Scenario recommends Hunyuan 3.1 Pro / Rodin Gen-2.5 / Hitem3D 3.0 for realism; Tripo 3.1 / P2 / Meshy 7.1 for game-ready meshes; TRELLIS.2 for complex topologies and stylized characters. A Meshy-employee comparison: Tripo best geometry/topology, Meshy best textures.

## 3. Input preparation

1. Single subject, whole object in frame, plain contrasting background (similar fg/bg color can delete parts).
2. Flat neutral lighting, no cast shadows or rim lights.
3. Characters: front-facing, **A-pose** (easier for generators, avoids armpit merging) or T-pose; limbs separated; empty hands. Godot's humanoid reference is T-pose; "Fix Silhouette" handles A-pose.
4. Props: 3/4 or front view, whole object visible.
5. Higher input resolution helps textures (TRELLIS.2 downsizes to 1024).

Background removal: **BiRefNet** (MIT code; variants HR 2048², matting, dynamic; ~3.5 GB FP16). RMBG-2.0 is CC BY-NC (built on BiRefNet).

Multi-view: hosted generators accept extra views (Meshy main + 3 auxiliary; Tripo multiview; Hunyuan 3.1 +$0.15; Hunyuan3D-2mv). From one image: MV-Adapter (Apache 2.0, 6 views at 768px, ~14 GB); Qwen-Image-Edit "Multiple Angles" LoRA (96 poses; fal/Replicate `qwen/qwen-edit-multiangle`; license unverified); Zero123++ (older). Cheapest: prompt Sunburst/Muse for front/side/back with the front image as reference. Props: single view is fine. Characters: a back view materially improves the back texture.

## 4. Post-processing

Raw AI mesh issues: dense triangle soup (50k–2M tris), baked lighting, non-manifold edges, small holes, no LODs, 2K–8K textures, no collision.

Polycount rules of thumb (industry, not sourced):

| Asset | Mobile/web | PC/console |
|---|---|---|
| Small prop | 300–3k | 2k–10k |
| Hero prop | 3k–10k | 10k–50k |
| Character | 5k–15k | 15k–60k |
| LODs | 100% / 50% / 25% / 10% | same |

| Step | Tools |
|---|---|
| Cleanup | PyMeshLab / trimesh; ComfyUI-Trellis2 nodes |
| Decimate | Blender Decimate; `gltfpack -si` |
| Quad retopo | Blender QuadriFlow; Instant Meshes; AutoRemesher (MIT, Jul 2026); API: Meshy Remesh, Tripo quad / P2 |
| UV | Blender Smart UV; xatlas; Meshy UV (5 cr) |
| Bake | Blender Cycles selected-to-active (headless) |
| Compress | gltf-transform (`optimize --texture-compress webp`, `meshopt`, `draco`); gltfpack |
| Export | GLB (Godot and Unity); FBX for Unity Humanoid |

Engine caveat: Godot support for `EXT_meshopt_compression` unverified; Unity glTFast supports it. Test imports before committing to compression.

Headless Blender: `pip install bpy` (one specific Python version per release) or `blender -b -P script.py -- args`. See `scripts/blender/`.

## 5. Rigging and animation

| Tool | Humanoid | Non-humanoid | Cost / license | Notes |
|---|---|---|---|---|
| **UniRig** | Yes | Yes | MIT, 8 GB | OBJ/FBX/GLB/VRM in; FBX out, merge → rigged GLB. README says superseded by SkinTokens |
| **SkinTokens** (Feb 2026) | Yes | Claimed | MIT, 14 GB | `python demo.py --input in.glb --output out.glb`; bone naming undocumented → manual mapping |
| **Puppeteer** | Yes | Yes | Apache 2.0 | Old stack (PyTorch 2.1.1, CUDA 11.8); video-guided animation |
| **Tripo Rig v3.0** | Yes | Yes (7 types + others) | 25 cr ≈ $0.25 | Mixamo/Unity/Unreal/ActorCore/VRM bone specs |
| **Meshy Rigging** | Biped only | No | 5 cr | Textured GLB, +Z facing, <300k faces; returns walk/run |
| **Mixamo** | Yes | No | Free | Manual only; AI-training ban |
| **AccuRIG 2** | Yes | Limited | Free (ActorCore account to export) | FBX/USD; Unity/Unreal presets |
| Anything World | Yes | Claims | Pricing conflicts | — |

Animation sources: Mixamo (manual); Meshy library (500+ clips, 3 cr each, text-to-motion); Tripo presets (90+ biped, creature walks, 10 cr each); **Quaternius Universal Animation Library (CC0)**; HY-Motion 1.0 (Tencent, 24–26 GB, license unverified — likely territory-limited); Kimodo (NVIDIA, code Apache, model licenses split, SMPL-X model research-only, NPZ output); GVHMR video-to-motion (SMPL licenses).

Godot retargeting (4.7 docs): Skeleton3D → Retarget → BoneMap + `SkeletonProfileHumanoid` (auto-map) → fix warnings → Rest Fixer with Overwrite Axis (+ Fix Silhouette for A-pose) → Remove Tracks. Reference: T-pose, +Z facing, Y-up. Alternative: `RetargetModifier3D` (4.4+). **MixaBridge** (MIT, Godot 4.4+) auto-maps Mixamo bones and builds an AnimationLibrary. Pitfall: Mixamo characters stuck in T-pose after mapping.

Unity: glTFast bypasses the Rig tab, so no Humanoid for GLB. Convert rigged GLB → FBX in Blender, then Rig → Humanoid → Configure Avatar; or `AvatarBuilder.BuildHumanAvatar` in code.

Creatures: Tripo Rigging or UniRig/SkinTokens/Puppeteer; generic rigs, clips authored for that skeleton.

## 6. Recommended pipelines

Costs assume ~2 attempts per accepted asset, excluding 2D generation and human time.

**A. Props**

| Tier | Pipeline | $/asset |
|---|---|---|
| Cheapest open-source | Image → BiRefNet RGBA → TRELLIS.2 on rented 4090/L40S → headless Blender cleanup/decimate/UV/bake → gltf-transform | ~$0.03–0.10 + setup |
| Best quality per $ | Tripo H3.1 standard + quad (~$0.35) or fal TRELLIS.2 1024p ($0.30); low-poly via Tripo smart low-poly / P2 or Meshy 6-lite → Blender + gltf-transform | ~$0.30–0.70 |
| Zero-setup API | fal TRELLIS.2 / Hunyuan 3.1 / Meshy / Tripo → minimal Blender | ~$0.30–0.80 |

**B. Rigged characters**

| Tier | Pipeline | $/asset |
|---|---|---|
| Cheapest open-source | A-pose turnaround → BiRefNet → TRELLIS.2 / Pixal3D MV → Blender retopo/UV/bake → UniRig or SkinTokens → weight fixes → Quaternius CC0 / manual Mixamo clips → engine | ~$0.10–0.30 + significant human time |
| Best quality per $ | Tripo H3.1/P2 + quad (~$0.35) → Rig v3.0 ($0.25) → 3–5 presets ($0.30–0.50). Humanoid alternative: Meshy (~$0.60 + $0.10 rig + $0.06/clip) | ~$0.80–1.10 |
| Zero-setup API | Meshy or Tripo end-to-end by script → engine humanoid import | ~$0.80–1.50 |

Run a **5-asset bake-off** on your own art style across 2–3 vendors before committing; all published comparisons are vendor-driven.

## 7. License risk register

Hunyuan3D open weights (territory/MAU/§5(c)); Hunyuan 3.x hosted (terms not read); RMBG-2.0 (NC, loaded by TRELLIS.2 default); DINOv3 (gated "other"); Meshy free tier (CC BY); Tripo free tier (non-commercial); Mixamo (AI-training ban, no automation policy); SF3D/SPAR3D (<$1M revenue); PartPacker (NC); SMPL/SMPL-X/Kimodo SMPL-X model (research); HY-Motion (unverified); SAM 3D (SAM License, splats).

## 8. Unverified

Tripo billing page and free-tier terms; Rodin per-generation pricing; Meshy $/credit for API; Kaedim/CSM/Luma/Stability hosted; TRELLIS.2 speed on 4090/L40S; Godot meshopt support; `quadriflow_remesh` in bpy 5.x; Instant Meshes CLI; gltfpack flags; independent quality ranking; Mixamo current terms; Anything World pricing; RigAnything.

## Sources

github.com/microsoft/TRELLIS.2 · huggingface.co/microsoft/TRELLIS.2-4B · github.com/TencentARC/Pixal3D · github.com/Tencent-Hunyuan/Hunyuan3D-2.1 (LICENSE) · github.com/Tencent-Hunyuan/Hunyuan3D-Omni · github.com/stepfun-ai/Step1X-3D · github.com/wgsxm/PartCrafter · github.com/facebookresearch/sam-3d-objects · app.cinevva.com/guides/ai-3d-model-generation-timeline-2026 (secondary) · triposr.org/blog/hunyuan3d-versions (secondary) · 3daistudio.com/blog/pixal3d-vs-trellis-2-vs-hunyuan-3d-comparison (secondary) · help.scenario.com/en/articles/comparing-generative-3d-models · github.com/visualbruno/ComfyUI-Trellis2 · github.com/PozzettiAndrea/ComfyUI-TRELLIS2 · docs.meshy.ai/en/api/pricing · docs.meshy.ai/en/api/rigging-and-animation · meshy.ai/pricing · developers.tripo3d.com/en/models/v3-1 · developers.tripo3d.com/en/models/rig · developers.tripo3d.com/en/models/animation · aws.amazon.com/marketplace/pp/prodview-hwlbvx7vubh7c · fal.ai/models/fal-ai/trellis-2 · fal.ai/models/fal-ai/hunyuan3d-v3/image-to-3d · fal.ai/models/fal-ai/meshy/v6/image-to-3d · poyo.ai/ru/comparison/ai-3d-api-pricing (secondary) · replicate.com/collections/3d-models · hyper3d.ai/pricing · runpod.io/pricing · modal.com/pricing · github.com/ZhengPeng7/BiRefNet · github.com/huanngzh/MV-Adapter · replicate.com/qwen/qwen-edit-multiangle · github.com/VAST-AI-Research/UniRig · github.com/VAST-AI-Research/SkinTokens · github.com/Seed3D/Puppeteer · Adobe Mixamo Additional Terms (2021 PDF) · 80.lv (AccuRIG 2) · github.com/Tencent-Hunyuan/HY-Motion-1.0 · github.com/nv-tlabs/kimodo · github.com/zju3dv/GVHMR · docs.godotengine.org/en/stable/tutorials/assets_pipeline/retargeting_3d_skeletons.html · github.com/donmccurdy/glTF-Transform · github.com/zeux/meshoptimizer · pypi.org/project/bpy · digitalproduction.com/2026/07/28/autoremesher-final-goes-mit · docs.meshy.ai/api/image-to-3d.md · help.scenario.com/en/articles/image-to-3d-best-practices
