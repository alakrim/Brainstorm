# scripts/

Small, tested helper scripts for turning AI-generated images and 3D models into game/app assets
(Godot 4, Unity 6, mobile apps). Copy the ones you need into a project. Every script has a docstring
at the top with usage, dependencies and what was tested. All run on CPU.

Last tested: **2026-10-21**, Linux x86_64 container, no GPU, Python 3.13.16, numpy 2.5.3, Pillow 12.3.0.
Blender: **`pip install bpy` = 5.2.2 LTS** (Python 3.13) and the **Blender 4.5.9 LTS** Linux tarball
(from download.blender.org).

| Script | What it does | Dependencies | Exact command | Test status (2026-10-21) |
|---|---|---|---|---|
| `check_glb.py` | Reports triangles, vertices, materials, texture sizes, skins/joints, animations, rest-pose bounding box; flags problems against `--budget mobile\|pc` (exit 1 on FAIL). | Python stdlib only | `python check_glb.py model.glb --budget mobile` (`--json` for machine output) | Tested on DamagedHelmet, Fox, CesiumMan, Avocado (Khronos glTF-Sample-Assets) and on outputs of `glb_cleanup.py`. See results below. |
| `blender/glb_cleanup.py` | Headless Blender: import GLB, join meshes, weld, remove loose geometry / tiny islands, optional recalc normals, apply scale, bottom-centre origin at world origin, decimate to `--target-tris`, optional Smart UV + Cycles-CPU bake of base colour (+ normal map) from the original high-poly, optional LODs, export GLB, JSON summary. | Blender 4.x/5.x **or** `pip install bpy numpy` | `blender -b -P blender/glb_cleanup.py -- in.glb out.glb --target-tris 5000 --recalc-normals --bake --bake-size 1024 --lods 0.5,0.25,0.1`<br>or `python blender/glb_cleanup.py in.glb out.glb ...` | Tested with bpy 5.2.2 (pip) and Blender 4.5.9 binary. Decimate, weld, island removal, bake (base colour + normal), LODs (files and nodes modes), rigged models (animations kept) all ran. Numbers below. |
| `blender/render_sprite_directions.py` | Headless Blender: ortho camera at configurable elevation (30 deg 3/4 or 35.264 isometric), transparent film, camera-locked key light, flat/shaded/toon look, N directions, every Kth frame of each animation; PNGs `{action}_{dir}_{frame:03d}.png`, optional `sheet.png` + `sheet.json` (frame rects). | Blender or `pip install bpy numpy` (no Pillow needed). Workbench/EEVEE also need libEGL + Mesa in a headless container (see Caveats) | `blender -b -P blender/render_sprite_directions.py -- model.glb out_dir --directions 8 --elevation 30 --size 256 --frame-step 2 --spritesheet`<br>CPU-only without GL: add `--engine cycles` | Tested with bpy 5.2.2 and Blender 4.5.9: workbench (default), cycles, eevee, looks shaded/flat/toon, outline, isometric + yaw offset, sheet + JSON. |
| `normal_map_from_image.py` | Tangent-space normal map from a sprite (luminance) or a supplied height/depth PNG; Sobel + Gaussian blur, strength, alpha-aware (no silhouette artefacts), alpha bevel, `--flip-y` for DirectX. Default output = OpenGL (green up), which Godot 4 and Unity expect. | numpy, Pillow | `python normal_map_from_image.py sprite.png sprite_n.png --strength 3`<br>`python normal_map_from_image.py sprite.png n.png --height-map depth.png`<br>`python normal_map_from_image.py --self-test` | `--self-test` passes 8/8 convention checks; run on a real rendered sprite (luminance and depth map). |
| `pixel_snap.py` | Snaps "fake pixel art" to a true pixel grid: auto-detect (or give) pixel size / target size, per-cell median/mode/mean colour, alpha threshold, palette reduction (Pillow median-cut / k-means / octree), integer nearest-neighbour preview upscale. | numpy, Pillow | `python pixel_snap.py in.png out.png --colors 16 --trim`<br>`python pixel_snap.py in.png out.png --target-size 64` | Tested on a synthetic 40x40 sprite blown up 15.7x with blur, noise and offset: grid auto-detected, 92.5% of pixels match the ground truth. **Caveat (orchestrator re-test 2026-10-21):** auto-detection mis-read a simple blocky sprite with few edges (true pixel size 12 → detected ~50×62); `--pixel-size 12` / `--target-size 40` then snapped it exactly. Pass `--pixel-size` or `--target-size` whenever the intended resolution is known, and use `--detect-only` to check detection first. |
| `mobile_icons.py` | From one 1024 source (or foreground PNG + background colour/PNG): iOS 1024 PNG without alpha + `Contents.json`, Android adaptive foreground/background/monochrome layers at mdpi..xxxhdpi (108/162/216/324/432 px, foreground scaled into the 66 dp safe zone), legacy square + round icons (48/72/96/144/192), Play Store 512, `mipmap-anydpi-v26/ic_launcher.xml`, Godot export-preset files, `preview.png` mask preview. Verifies its own output. | Pillow | `python mobile_icons.py --source icon1024.png --out build/icons`<br>`python mobile_icons.py --foreground logo.png --background "#1b1f3b" --out build/icons` | Tested in `--source` (box and bleed layouts) and `--foreground` + colour / PNG background modes; built-in verification passes (sizes, no alpha on iOS/Play, safe zone, XML parses). |

## Test results (actual numbers)

Inputs: Khronos glTF-Sample-Assets (`DamagedHelmet`, `Fox`, `CesiumMan`, `Avocado` from
`github.com/KhronosGroup/glTF-Sample-Assets`, `glTF-Binary` variants) and PNGs generated with Pillow.

**check_glb.py**

| Input | Tris | Verts | Notes |
|---|---|---|---|
| DamagedHelmet | 15,452 | 14,556 | 1 material, 5 JPEG textures 2048x2048; `--budget mobile`: FAIL (tris > 15,000, 5 textures > 1024). |
| Fox | 576 | 1,728 | 24 joints, 3 animations (Survey 3.42 s, Walk 0.71 s, Run 1.16 s), no NORMAL attribute (WARN), size 25 x 79 x 155 units (WARN: not metres). |
| CesiumMan | 4,672 | 3,273 | 19 joints, 1 animation, skinned rest-pose bbox 1.138 x 1.507 x 0.312 m; `--budget pc`: PASS. |
| Avocado | 682 | 406 | 3 PNG textures 2048x2048; 0.043 x 0.063 x 0.028 m, `--budget pc`: PASS. |

**glb_cleanup.py**

| Run | Result |
|---|---|
| DamagedHelmet `--target-tris 3000 --recalc-normals --bake --bake-normal --bake-size 1024 --jpeg --lods 0.5,0.25` (bpy 5.2.2) | tris 15,452 -> 3,000, verts 14,556 -> 1,985 (5,895 verts welded); bbox bottom-centred (min Y 0.0); bake 3.2 s (CPU): 1024 base colour + 1024 normal replace five 2048 textures; file 3.77 MB -> 0.44 MB; LOD1 1,500 tris, LOD2 750 tris (`h_LOD1.glb`, `h_LOD2.glb`). |
| DamagedHelmet `--target-tris 5000 --recalc-normals` (no bake) | 15,452 -> 4,999 tris; file grew 3.77 -> 8.18 MB because the AUTO exporter re-encoded one JPEG as PNG (use `--jpeg`). |
| DamagedHelmet, Blender 4.5.9 binary, `--target-tris 4000 --bake --bake-size 512 --lods 0.5,0.25` | 15,452 -> 3,999 tris; LODs 1,998 and 999; bake 0.8 s. |
| CesiumMan (skinned) `--target-tris 1500 --lods 0.5,0.25` | 4,672 -> 1,500 tris; 19 joints and the animation kept; rest-pose bbox 1.138 x 1.507 x 0.312 m moved to bottom-centre; LODs 750 / 374 tris. `--lod-mode nodes` writes `CesiumMan_LOD0/1/2` in one GLB (2,624 tris total). |
| Fox (skinned) `--target-tris 300 --bake --bake-size 512` | 576 -> 300 tris, 3 animations kept, bake 0.1 s. Blender 4.5.9: `--target-tris 400` -> 400 tris, 3 animations kept. |
| Avocado `--height 0.5 --weld 0.00001` | height 0.063 -> 0.5 m, 43 verts welded. |
| Synthetic GLB (sphere + stray triangle + doubled seam verts) `--min-island-tris 5` | 1,987 -> 482 verts (1,502 welded), 1 floating-island face removed, bbox 1 x 1 x 1 at origin. |

**render_sprite_directions.py**

- CesiumMan, 8 directions, 128 px, `--frame-step 8`, `--spritesheet`: 56 frames, `sheet.png` 896 x 1024, `sheet.json` with rects; 73.2 pixels per unit.
- Fox (3 actions), 8 directions, 128 px, `--frame-step 8 --outline --spritesheet`: 144 frames, sheet 1408 x 3072.
- Direction convention verified with Fox (faces glTF +Z): `S` faces the camera, `W` faces screen-left, `E` faces screen-right, `N` is the back.
- Timing (4 CPU cores): workbench about 0.03 s/frame at 128 px; cycles 8 samples about 0.06 s/frame; EEVEE on Mesa software GL about 6 s/frame at 192 px (use workbench).

**normal_map_from_image.py**: self-test checks R > 128 on the right of a dome, G > 128 at the top (OpenGL, green up), inverted green with `--flip-y`, flat centre, flat transparent corner, unit-length normals. A Fox sprite rendered by the sprite script gave sensible maps from luminance and from a blurred-silhouette depth map.

**pixel_snap.py**: detected pixel size 15.72 x 15.72 (truth 15.7), phase 9.0 / 4.5 (truth 9 / 5); output grid 28 x 34 after `--trim`, 8 colours, 92.5% of opaque pixels within colour distance 70 of the ground truth. `mode`, `mean`, `octree`, dither, `--target-size` and `--colors 0` paths run. `libimagequant` is not in this Pillow build and the script falls back to k-means with a warning.

**mobile_icons.py**: 34 files per run (28 in `bleed` layout): iOS 1024 RGB (no alpha), Play 512, 5 densities x (foreground, background, monochrome, legacy, round), XML, Godot files, preview.

## Caveats and decisions

- **LOD naming** (details in `glb_cleanup.py` docstring): Unity creates a LODGroup automatically from `Name_LOD0`, `Name_LOD1`... meshes grouped in an imported **FBX** (docs name only FBX; glTFast behaviour for GLB is unverified). Godot 4 has no LOD name suffix for glTF (its suffix list is `-col`, `-convcol`, `-colonly`, `-occ`, `-navmesh`, `-noimp`, `-loop` etc.), generates LODs itself on import, and recommends Visibility Ranges (HLOD) for hand-made LODs. Default here: separate files `out_LOD1.glb`... (works in both engines); `--lod-mode nodes` additionally writes Unity-style names in one GLB.
- **Rigged models**: `glb_cleanup.py` does not apply scale and does not rescale (`--height`) rigged models (it would break animation); it moves the armature to the origin instead, and deletes the helper "bone shape" icosphere meshes the glTF importer creates (otherwise they get joined into the model).
- **Decimation and textures**: Collapse decimation stretches existing UVs at high reduction. For heavy reductions use `--bake`, which rebuilds UVs (Smart UV project) and bakes colour/normal from the original. Baked islands are many and small at very low triangle counts (3,000 tris helmet); check the result in the engine.
- **Headless GL**: Workbench and EEVEE need libEGL plus Mesa. In this container they failed until `apt-get install libegl1 libgl1 libglx-mesa0 libgl1-mesa-dri libegl-mesa0` (Ubuntu 24.04) was run; `--engine cycles` needs none of that. This apt install is an environment change made during testing, not part of the repo.
- **Blender versions**: the EEVEE engine id is `BLENDER_EEVEE_NEXT` in 4.2-4.5 and `BLENDER_EEVEE` in 5.x (the sprite script tries both). The pip `bpy` wheel needs a matching Python (5.2.2: Python 3.13; 4.x: 3.11). `Material.use_nodes` prints a deprecation warning on 5.x (harmless until Blender 6).
- **Not tested**: Unity/Godot import of the outputs (no engine in the container), Godot/Unity LOD behaviour, `--jpeg` with textures that need alpha, GLBs with Draco/meshopt compression (pip `bpy` could not find the Draco/meshopt bridge libraries; `check_glb.py` reads them but `glb_cleanup.py` cannot import or export compressed meshes in that build), multi-skin GLBs, sparse accessors in `check_glb.py`.
- **Untrusted inputs**: the test GLBs were downloaded into an isolated directory and read with `python -I` / Blender; do the same for third-party files.
- **Licences**: the Khronos sample assets used for testing have their own licences (see the repo's per-model license files); none are copied into this repo.
