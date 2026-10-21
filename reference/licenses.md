# Licenses: what is safe to use for shipped commercial assets

*Checked 2026-10-21 against primary sources (LICENSE files, Hugging Face model cards, vendor terms) unless marked. Not legal advice. When a project ships commercially, have someone read the actual license text for every tool in its pipeline.*

## Quick verdicts

✅ = clear for commercial use · ⚠️ = usable with conditions or needs a read · ❌ = don't use for shipped assets

### Background removal

| Tool | Verdict | Notes |
|---|---|---|
| **BiRefNet** (code + weights) | ✅ | MIT. Keep the notice |
| rembg `birefnet-general` | ✅ | MIT (BiRefNet) |
| rembg `isnet-general-use`, `u2net` | ⚠️ | Code Apache-2.0; weights license not stated (likely fine, unverified) |
| **rembg default model (`bria-rmbg`)** | ❌ | **rembg's default is RMBG-2.0: always pass `-m birefnet-general`** |
| **RMBG-2.0** (BRIA) | ❌ | CC BY-NC 4.0; commercial use needs a paid BRIA agreement |
| BEN2 base | ✅ | MIT (the full BEN2 model is commercial, sold separately) |

### Image → 3D

| Model | Verdict | Notes |
|---|---|---|
| **TRELLIS.2 / TRELLIS** (self-hosted) | ⚠️ | Code and weights MIT, **but the pipeline depends on NVIDIA nvdiffrast**, whose license (§3.3) allows use "for research or evaluation purposes only and not for any direct or indirect monetary gain". TRELLIS v1 also uses diff-gaussian-rasterization (Inria, non-commercial). TRELLIS.2's default background remover is RMBG-2.0 (❌, avoid with pre-cut RGBA input) and it needs gated DINOv3 (license "other"). **Get a legal read before self-hosting it for a commercial product.** |
| TRELLIS.2 via **fal** hosted endpoint | ⚠️ | You're using fal's service; check fal's commercial terms for the endpoint. It moves the dependency question to the vendor |
| **Step1X-3D** | ✅ | Apache-2.0 code and weights (texture-stage dependencies not audited) |
| **TripoSG, TripoSR** | ✅ | MIT; geometry only (TripoSG) / draft quality (TripoSR) |
| Stable Fast 3D, SPAR3D | ⚠️ | Stability Community License: free only if annual revenue < US$1M; Enterprise license above |
| **Hunyuan3D 2.0 / 2.1** (open weights) | ❌ for worldwide releases | Tencent community license **excludes the EU, UK and South Korea** (use of outputs there is unlicensed, §5(c)); >1M MAU needs a Tencent license; outputs may not be used to improve other AI models |
| Hunyuan3D 2.5 / 3.x / Omni / PolyGen | ⚠️ | Unverified (primary files blocked/missing). Assume 2.x restrictions. The 3.x versions are hosted-only; read Tencent Cloud / fal terms |
| Pixal3D | ⚠️ | MIT per research report (license file not re-checked); built on TRELLIS.2, so it inherits the nvdiffrast question |
| SAM 3D Objects | ⚠️ | SAM License; outputs are Gaussian splats |
| PartPacker (NVIDIA) | ❌ | Non-commercial |

> **General rule for self-hosted 3D models:** many 3D pipelines pull in NVIDIA nvdiffrast, Inria Gaussian-splatting rasterizers or other research-licensed CUDA extensions for rendering and texture baking. Check `setup.sh` / `requirements.txt`, not just the top-level LICENSE.

### Hosted 3D vendors

| Vendor | Verdict | Notes |
|---|---|---|
| **Meshy paid plans** | ✅ | You own the output (ToS 3.2); can keep it private |
| Meshy free plan | ⚠️ | Output licensed CC BY 4.0: credit Meshy in the shipped product |
| **Tripo paid plans** | ⚠️ | Commercial use per secondary sources; ToS page blocked (403). Read the ToS before shipping |
| Tripo free plan | ❌ until verified | Conflicting reports (non-commercial / Tripo retains rights) |
| Hunyuan 3.x hosted, Rodin | ⚠️ | Terms not read |

### Rigging and animation

| Tool | Verdict | Notes |
|---|---|---|
| **UniRig** | ✅ | MIT code and weights (training dataset terms unchecked) |
| SkinTokens | ✅ (per research report) | MIT |
| **MagicArticulate** (Seed3D) | ✅ | Apache-2.0 |
| Puppeteer (Seed3D) | ⚠️ | Code Apache-2.0; weights unverified |
| **RigAnything** | ❌ | Adobe Research License: research and teaching only |
| Mixamo | ⚠️ | Primary terms unreachable. Secondary: OK in games, no redistribution of raw files, AI-training use banned (2021 Additional Terms). Manual only |
| HY-Motion (Tencent) | ⚠️ | Unverified; likely Tencent territory terms |
| Kimodo SMPL-X model, SMPL/SMPL-X | ❌ | Research licenses |
| Quaternius animation library | ✅ | CC0 (free tier) |

### Depth, normals, segmentation, layers

| Tool | Verdict | Notes |
|---|---|---|
| **Depth Anything 3 Small / Base** | ✅ | Apache-2.0 |
| Depth Anything 3 Large / Giant | ❌ | CC BY-NC 4.0 |
| **Depth Anything V2 Small** | ✅ | Apache-2.0 |
| Depth Anything V2 Base / Large | ❌ | CC BY-NC 4.0 |
| Marigold | ⚠️ | Code Apache-2.0; weights OpenRAIL++-M (use restrictions; read Attachment A) |
| **SAM 2** | ✅ | Apache-2.0 |
| SAM 3 | ⚠️ | Custom SAM License: commercial use OK in principle; end-use (military, weapons) and trade-control restrictions |
| **Qwen-Image-Layered, Qwen-Image-Edit-2511** | ✅ | Apache-2.0 |
| **Wan 2.2 / Wan2.2-Animate** | ✅ | Apache-2.0, plus a use policy (no unlawful/harmful use) |
| LayerDiffuse | ⚠️ | Code Apache-2.0; weights CreativeML OpenRAIL-M + base model license |

### 2D tools

| Tool | Verdict | Notes |
|---|---|---|
| **Laigter** | ✅ as a tool | GPL-3.0 covers the program, not your output maps. Don't redistribute modified builds without source |
| **PixelOE** | ✅ | Apache-2.0 |
| **unfake.js** | ✅ | MIT |
| **vtracer** | ✅ | MIT |
| **free-tex-packer-core** | ✅ | MIT |
| Real-ESRGAN | ✅ | BSD-3 |
| Spine / TexturePacker / Live2D | Paid | Per-seat or revenue-tier licenses |

### Image generators

| Generator | Verdict | Notes |
|---|---|---|
| OpenAI Sunburst | ⚠️ | OpenAI terms assign output rights to the user (primary page not reachable at research time). No trademarks/likeness |
| Meta Muse Image | ⚠️ | fal tags "Commercial use"; Meta's terms not reachable. Consumer-app outputs carry an invisible watermark |

## Red flags (checklist before shipping)

- [ ] No **RMBG-2.0** anywhere, including rembg's default model and TRELLIS.2's default preprocessing
- [ ] No **CC BY-NC** depth weights (DA3 Large/Giant, DA2 Base/Large)
- [ ] No **Hunyuan3D open-weight** outputs if the product ships in the EU, UK or South Korea, or will exceed 1M MAU
- [ ] **Self-hosted TRELLIS/TRELLIS.2:** legal sign-off on nvdiffrast (and diff-gaussian-rasterization for v1), or use a hosted vendor
- [ ] Stability SF3D/SPAR3D only while annual revenue < US$1M
- [ ] Meshy free-tier assets credited (CC BY 4.0), or regenerate on a paid plan
- [ ] No Tripo free-tier assets until its ToS is verified
- [ ] No RigAnything outputs
- [ ] Mixamo files not redistributed raw, and never used for AI training
- [ ] Every shipped asset has a manifest entry: tool, version, license, date

Full audit with source URLs: research report in `research/2026-10-21/` and the table above (sources listed per row in the audit; key URLs below).

## Key primary sources

- nvdiffrast: https://raw.githubusercontent.com/NVlabs/nvdiffrast/main/LICENSE.txt
- TRELLIS / TRELLIS.2: https://github.com/microsoft/TRELLIS , https://github.com/microsoft/TRELLIS.2
- Hunyuan3D 2.0 / 2.1: https://raw.githubusercontent.com/Tencent-Hunyuan/Hunyuan3D-2/main/LICENSE.txt , https://raw.githubusercontent.com/Tencent-Hunyuan/Hunyuan3D-2.1/main/LICENSE
- RMBG-2.0: https://huggingface.co/briaai/RMBG-2.0
- BiRefNet: https://raw.githubusercontent.com/ZhengPeng7/BiRefNet/main/LICENSE
- Depth Anything 3: https://huggingface.co/depth-anything/DA3-SMALL (and -BASE, -LARGE, -GIANT)
- Stable Fast 3D: https://raw.githubusercontent.com/Stability-AI/stable-fast-3d/main/LICENSE.md
- Step1X-3D: https://raw.githubusercontent.com/stepfun-ai/Step1X-3D/main/LICENSE
- UniRig: https://raw.githubusercontent.com/VAST-AI-Research/UniRig/main/LICENSE
- RigAnything: https://raw.githubusercontent.com/Isabella98Liu/RigAnything/main/LICENSE.md
- SAM 3: https://raw.githubusercontent.com/facebookresearch/sam3/main/LICENSE
- Qwen-Image: https://raw.githubusercontent.com/QwenLM/Qwen-Image/main/LICENSE
- Wan 2.2: https://huggingface.co/Wan-AI/Wan2.2-Animate-14B
- Meshy ToS: https://www.meshy.ai/cs/terms-of-use
- Laigter: https://raw.githubusercontent.com/azagaya/laigter/master/LICENSE
