# 3D rigged and animated characters (image → rigged GLB/FBX)

*Researched 2026-10-21. Prices were verified on vendor pages that day unless marked. Re-check if this is more than ~3 months old.*

## TL;DR

| Situation | Use | ~Cost per accepted character |
|---|---|---|
| **Default (humanoids and creatures)** | **Tripo end to end**: image → 3D (H3.1 or P2, + quad) → Rigging v3.0 with the bone spec matching your engine → preset animations | $0.90–1.10 |
| Humanoids only, best textures | **Meshy**: image-to-3D (`pose_mode: a-pose`) → auto-rig → library animations | $0.80–1.00 |
| Many characters, low budget, someone can fix weights | TRELLIS.2 (self-host, after the nvdiffrast license sign-off in `3d-props.md`; otherwise fal TRELLIS.2) → retopo → **UniRig / SkinTokens** (MIT) → CC0 animation library | $0.10–0.60 + human time |
| Hero character | Any of the above as a base, then manual retopo/rig/weights by an artist | — |

Rigging is where AI output most often needs a human. Budget review time for every character: check deformation at shoulders, hips and knees in an idle, walk, run and attack clip.

## Pipeline

```
1. Source images     front A-pose master + side/back views (edit calls)        (00-source-images.md)
2. Cutout            BiRefNet → RGBA
3. Image → 3D        Tripo / Meshy (multi-view) | TRELLIS.2 / Pixal3D
4. Topology          quad remesh to budget (vendor option, or Blender) → UV → bake
5. Rig               Tripo Rig v3.0 | Meshy auto-rig | UniRig / SkinTokens | AccuRIG / Mixamo (manual)
6. Animate           vendor presets | Quaternius CC0 | Mixamo (manual) | text-to-motion
7. Engine            Godot: BoneMap + SkeletonProfileHumanoid | Unity: FBX → Humanoid Avatar
```

### 1. Source images

Use the "3D character" framing from [`00-source-images.md`](00-source-images.md):

- **A-pose**, arms 30–45° from the body, legs slightly apart, fingers spread, front-facing, orthographic, flat light, plain background, empty hands. A-pose avoids merged armpits. Godot's "Fix Silhouette" corrects A-pose to its T-pose reference at import.
- **No loose capes, long open coats, floor-length hair or held weapons** in the base mesh. They fuse with the body and break skinning. Make weapons separate props and attach them to a hand bone in the engine.
- Generate **side and back views** as Sunburst edit calls referencing the front. A back view materially improves the back texture. All hosted vendors accept multi-view input (Meshy: main + up to 3 auxiliary views; Tripo multiview; Hunyuan 3.1 +$0.15).
- Alternatives for extra views: Qwen-Image-Edit "Multiple Angles" LoRA (fal/Replicate `qwen/qwen-edit-multiangle`; license unverified) or MV-Adapter (Apache 2.0, objects).

### 2–3. Image → 3D

| Option | Price | Notes |
|---|---|---|
| **Tripo H3.1** | 30 credits standard texture, +5 quad ≈ $0.35 | Delighting, PBR, GLB/FBX. **P2** (Sep 2026): native quad meshes up to 25k quads, good for deformation |
| **Meshy 6 / 7.1** | 30 credits ≈ $0.60 (derived) | `pose_mode: "a-pose"` or `"t-pose"` forces the pose; `remove_lighting` default on. Model must face +Z for rigging |
| **TRELLIS.2** (fal $0.30 or self-hosted) | $0.30 / ~$0.02 | Good stylized characters; triangle soup, so retopo is needed before rigging |
| Pixal3D (MIT, self-host) | — | Multi-view with camera poses; experimental |

### 4. Topology for deformation

AI meshes are dense triangle soup. Skinning works much better on even quad topology with edge loops at the joints.

- **Simplest:** the vendor's quad output (Tripo quad +5 credits / P2; Meshy Remesh 5 credits) at the target face count.
- **Self-hosted:** Blender QuadriFlow, Instant Meshes or AutoRemesher (MIT) → Smart UV → Cycles bake of base color and normal from the original. Start from `scripts/blender/glb_cleanup.py` (decimate/UV/bake).
- Budgets (rules of thumb): mobile 5k–15k triangles, PC/console 15k–60k for the body.

### 5. Rigging options

| Tool | Humanoid | Creatures | Cost / license | Automatable | Notes |
|---|---|---|---|---|---|
| **Tripo Rigging v3.0** | ✓ | ✓ biped, quadruped, hexapod, octopod, avian, serpentine, aquatic, others | 25 credits (~$0.25); Rig Check free | API | **Bone specs for bipeds: Tripo, Mixamo, Unity, Unreal, ActorCore, VRM.** Choose Mixamo or Unity to minimize retargeting. GLB or FBX out |
| **Meshy auto-rig** | ✓ | ✗ | 5 credits | API (Pro+) | Needs textured model, +Z facing, <300k faces. Returns walk/run clips |
| **UniRig** (VAST) | ✓ | ✓ | MIT, 8 GB VRAM | Script | FBX out; merge step gives rigged GLB. Skinning suffers if the skeleton misses tails or wings. README says it is superseded by SkinTokens |
| **SkinTokens** (VAST, Feb 2026) | ✓ | claimed | MIT, 14 GB VRAM | `python demo.py --input in.glb --output out.glb` | Bone naming undocumented, so humanoid retargeting needs a manual bone map |
| **Puppeteer** (Seed3D) | ✓ | ✓ | Apache 2.0 | Script | Old stack (PyTorch 2.1.1, CUDA 11.8) |
| **AccuRIG 2** (Reallusion) | ✓ | limited | Free (ActorCore account to export) | Manual desktop | FBX, Unity/Unreal presets |
| **Mixamo** (Adobe) | ✓ | ✗ | Free | **Manual only** | No API or bulk-use policy. Terms ban using outputs to train AI. Reported "maintenance mode". Don't build pipelines on it |

### 6. Animation sources

| Source | License / cost | Use for |
|---|---|---|
| **Tripo animation presets** | 10 credits each; 90+ biped, plus creature locomotion | Pairs with Tripo rigs, incl. creatures |
| **Meshy animation library** | 3 credits/action, 500+ clips, text-to-motion for bipeds | Pairs with Meshy rigs |
| **Quaternius Universal Animation Library** | CC0 (free portion; paid tiers) | License-clean humanoid basics |
| **Mixamo** | Free, manual download | Humanoid clips; keep away from any AI training |
| HY-Motion 1.0 (Tencent, text-to-motion) | License unverified, likely Tencent territory terms | Avoid until the license is checked |
| Kimodo (NVIDIA, text-to-motion) | Code Apache; SMPL-X model research-only | Prototyping only |
| GVHMR (video-to-motion) | SMPL body-model licenses | Prototyping only |

### 7. Engine import

**Godot 4** (details in `reference/engine-import.md`):
1. Import GLB → Advanced Import Settings → select `Skeleton3D` → Retarget → new `BoneMap` with **`SkeletonProfileHumanoid`** (auto-maps Mixamo/Unity-style names).
2. Fix any red/yellow bone mappings.
3. Enable **Rest Fixer → Overwrite Axis**, plus **Fix Silhouette** for A-pose models.
4. Import shared animation clips into an `AnimationLibrary` using the same BoneMap.
5. For Mixamo-named rigs, **MixaBridge** (MIT, Godot 4.4+) automates the mapping.

**Unity 6:**
- glTFast imports bypass the Rig tab, so there is **no Humanoid Avatar for GLB**. Get **FBX** from the vendor (Tripo/Meshy both export FBX) or convert GLB → FBX with headless Blender, then Rig → Animation Type **Humanoid** → Configure Avatar.
- Tripo's **Unity bone spec** gives the cleanest automatic Avatar mapping.
- Automate with an `AssetPostprocessor` (see `reference/engine-import.md`).

**Creatures (non-humanoid):** neither engine's humanoid retargeting applies. Use the vendor's creature clips (Tripo) or author clips for that exact skeleton. Import as generic rigs.

## Checklist before accepting a character

- [ ] Faces +Z (Godot/glTF forward), Y-up, feet on origin, real-world scale (≈1.6–1.9 m for an adult human)
- [ ] Triangle count and texture size within budget (`scripts/check_glb.py --budget mobile|pc`)
- [ ] Idle, walk, run, plus one extreme pose (crouch/attack) with no candy-wrapper twisting or mesh tearing
- [ ] Bone names match the chosen spec; humanoid mapping all green in Godot / Avatar valid in Unity
- [ ] Manifest records vendor, task IDs, bone spec, clips used and their licenses

## Measured results

| Date | Project | Pipeline | Characters | Accept rate | $/accepted | Rig fix time | Notes |
|---|---|---|---|---|---|---|---|
| | | | | | | | |

## Sources

See `research/2026-10-21/image-to-3d-and-rigging.md`.
