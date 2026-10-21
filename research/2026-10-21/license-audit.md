# Raw research: license audit (2026-10-21)

> Raw report from a license-verification agent. Curated verdicts: `reference/licenses.md`. The nvdiffrast clause was re-checked by the orchestrator on the same day: "Nvidia Source Code License (1-Way Commercial)", §3.3 "only may be used or intended for use non-commercially", where non-commercially means "for research or evaluation purposes only and not for any direct or indirect monetary gain"; only NVIDIA and its affiliates may use it commercially.

| Item | Code | Weights | Commercial outputs | Key restrictions | Source |
|---|---|---|---|---|---|
| BiRefNet | MIT | MIT | Yes | Keep notice | raw.githubusercontent.com/ZhengPeng7/BiRefNet/main/LICENSE ; huggingface.co/ZhengPeng7/BiRefNet |
| rembg (tool) | MIT | Per model | n/a | Default model is bria-rmbg (RMBG-2.0, NC) | raw.githubusercontent.com/danielgatis/rembg/main/README.md |
| isnet-general-use | Apache-2.0 (DIS) | Not stated | Likely, unverified | DIS5K dataset terms unread | github.com/xuebinqin/DIS |
| u2net | Apache-2.0 | Not verified | Likely, unverified | | raw.githubusercontent.com/xuebinqin/U-2-Net/master/LICENSE |
| RMBG-2.0 | — | CC BY-NC 4.0 | NO without BRIA agreement | | huggingface.co/briaai/RMBG-2.0 |
| BEN2 base | MIT | MIT | Yes | Full model sold separately | huggingface.co/PramaLLC/BEN2 |
| Hunyuan3D-2.0 | Tencent Hunyuan 3D 2.0 Community License | same | Inside Territory, < 1M MAU | Excludes EU/UK/KR (1(l), 5(c)); >1M MAU needs license (§4); no improving other AI (5(b)); AUP; Tencent claims no output rights (6(d)) | raw.githubusercontent.com/Tencent-Hunyuan/Hunyuan3D-2/main/LICENSE.txt |
| Hunyuan3D-2.1 | Tencent Hunyuan 3D 2.1 Community License (2025-06-13) | tencent-hunyuan-community | Same | Same | raw.githubusercontent.com/Tencent-Hunyuan/Hunyuan3D-2.1/main/LICENSE |
| Hunyuan3D 2.5/3.0/Omni/PolyGen | Unverified | Unverified | Unverified | Assume 2.x terms | huggingface.co/tencent/Hunyuan3D-Omni |
| TRELLIS | MIT | MIT | MIT parts yes | nvdiffrast NVIDIA 1-Way Commercial (non-commercial for others); diffoctreerast from diff-gaussian-rasterization (Inria, NC); FlexiCubes upstream license unverified | raw.githubusercontent.com/microsoft/TRELLIS/main/LICENSE ; raw.githubusercontent.com/NVlabs/nvdiffrast/main/LICENSE.txt ; raw.githubusercontent.com/graphdeco-inria/diff-gaussian-rasterization/main/LICENSE.md |
| TRELLIS.2 | MIT | MIT | MIT parts yes | nvdiffrast (NC); nvdiffrec own license unread; O-Voxel/FlexGEMM/CuMesh no license found | raw.githubusercontent.com/microsoft/TRELLIS.2/main/README.md |
| Stable Fast 3D | Stability Community | same | < US$1M revenue | Enterprise license above | raw.githubusercontent.com/Stability-AI/stable-fast-3d/main/LICENSE.md |
| SPAR3D | Stability Community | same | Same | Card wording conflicts with license text | huggingface.co/stabilityai/stable-point-aware-3d |
| TripoSG | MIT | MIT | Yes | | raw.githubusercontent.com/VAST-AI-Research/TripoSG/main/LICENSE |
| TripoSR | MIT | MIT | Yes | | raw.githubusercontent.com/VAST-AI-Research/TripoSR/main/LICENSE |
| Step1X-3D | Apache-2.0 | Apache-2.0 | Yes | | raw.githubusercontent.com/stepfun-ai/Step1X-3D/main/LICENSE |
| Depth Anything V2 | Apache-2.0 | Small Apache; Base/Large CC BY-NC | Small only | | huggingface.co/depth-anything/Depth-Anything-V2-*-hf |
| Depth Anything 3 | Apache-2.0 | Small/Base Apache; Large/Giant CC BY-NC | Small/Base only | Metric/Mono/Nested not checked | huggingface.co/depth-anything/DA3-* |
| SAM 2 | Apache-2.0 | Apache-2.0 | Yes | | raw.githubusercontent.com/facebookresearch/sam2/main/LICENSE |
| SAM 3 | SAM License (2025-11-19) | same | Probably yes | End-use (military, weapons, espionage), trade control, no reverse engineering | raw.githubusercontent.com/facebookresearch/sam3/main/LICENSE |
| Qwen-Image-Edit-2511 | Apache-2.0 | Apache-2.0 | Yes | | huggingface.co/Qwen/Qwen-Image-Edit-2511 |
| Qwen-Image-Layered | Apache-2.0 | Apache-2.0 | Yes | | huggingface.co/Qwen/Qwen-Image-Layered |
| Wan 2.2 / Animate-14B | Apache-2.0 | Apache-2.0 | Yes | Use policy | huggingface.co/Wan-AI/Wan2.2-Animate-14B |
| UniRig | MIT | MIT | Yes | Articulation-XL2.0 dataset unchecked | raw.githubusercontent.com/VAST-AI-Research/UniRig/main/LICENSE |
| RigAnything | Adobe Research License | same | NO | Research/teaching only | raw.githubusercontent.com/Isabella98Liu/RigAnything/main/LICENSE.md |
| Puppeteer | Apache-2.0 | Unverified | Code yes | | raw.githubusercontent.com/Seed3D/Puppeteer/main/LICENSE |
| MagicArticulate | Apache-2.0 | Apache-2.0 | Yes | | raw.githubusercontent.com/Seed3D/MagicArticulate/main/LICENSE |
| Marigold | Apache-2.0 | OpenRAIL++-M | Yes, with use restrictions | Attachment A placeholder in fetched file | raw.githubusercontent.com/prs-eth/Marigold/main/LICENSE-MODEL.txt |
| LayerDiffuse | Apache-2.0 | CreativeML OpenRAIL-M | Likely | Base model licenses | huggingface.co/LayerDiffusion/layerdiffusion-v1 |
| free-tex-packer-core | MIT | — | Yes | | github.com/odrick/free-tex-packer-core |
| Laigter | GPL-3.0 | — | Tool yes | GPL covers program, not outputs | raw.githubusercontent.com/azagaya/laigter/master/LICENSE |
| PixelOE | Apache-2.0 (one listing says MIT) | — | Yes | | github.com/KohakuBlueleaf/PixelOE |
| unfake.js | MIT | — | Yes | | github.com/jenissimo/unfake.js |
| vtracer | MIT | — | Yes | | github.com/visioncortex/vtracer |
| Mixamo | Unverified | — | Secondary: games OK, no raw redistribution | Primary pages 403/404 | community.adobe.com (Mixamo commercial games thread) |
| Meshy free | ToS 3.2: CC BY 4.0 | — | Yes with credit | No competing AI training (2.6(xi)) | meshy.ai/cs/terms-of-use |
| Meshy paid | Customer owns output | — | Yes | | meshy.ai/cs/terms-of-use |
| Tripo | Unverified (403) | — | Paid yes (secondary); free conflicting | | tripo3d.ai help pages (blocked) |
