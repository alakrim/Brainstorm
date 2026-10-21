# Engine import: Godot 4 and Unity 6

How to get processed assets into the engines, **unattended** where possible. *Researched 2026-10-21 against Godot **4.7.2-stable** (2026-08-18) and Unity **6.6** (6000.6.6f1) with glTFast **6.20.0**.* Items marked **(unverified)** weren't confirmed in primary docs; test them on one asset first.

## Format matrix

| | Godot 4.7 | Unity 6 |
|---|---|---|
| Static props | **GLB** (native importer) | **GLB** via glTFast (`com.unity.cloud.gltfast`), or FBX |
| Rigged humanoid | **GLB** + BoneMap / `SkeletonProfileHumanoid` retarget | **FBX** (glTFast doesn't create Humanoid Avatars; convert GLB → FBX with Blender) |
| Draco mesh compression | ❌ **not supported** (import error) | ✅ |
| Meshopt compression | ❌ not supported | ✅ |
| KTX2 / Basis textures in glTF | (unverified); test first | ✅ |
| WebP textures in glTF | ✅ (`EXT_texture_webp` extension present) | (unverified) |
| Auto mesh LODs | ✅ **on by default** at import (meshoptimizer) | ✅ Mesh LOD generator (opt-in, Unity 6.x; source mesh ≥256 tris) |

**Rule:** for Godot, ship plain GLBs: no Draco or meshopt, PNG/JPEG (or WebP) textures. Let Godot compress textures (VRAM Compressed) and generate LODs at import. For Unity, Draco/meshopt GLBs are fine through glTFast.

## Godot 4.7

### Static props (GLB)

- Mesh LODs are generated automatically (`Meshes > Generate LODs`). Disable per mesh if they cause artifacts, especially on skinned meshes. Tune with project setting `Rendering > Mesh LOD > LOD Change > Threshold Pixels`.
- **Collision via node-name suffixes**, set in Blender before export (case-insensitive; `-`, `_` or `$` separator):

| Suffix | Result |
|---|---|
| `-col` | Keeps the mesh, adds a static trimesh collider (accurate, slow) |
| `-convcol` | Keeps the mesh, adds a convex collider |
| `-colonly` / `-convcolonly` | Replaces the mesh with a StaticBody3D collider (trimesh / convex) |
| `-rigid` | Imports as RigidBody3D |
| `-occ` / `-occonly` | Occluder |
| `-navmesh` | Navigation mesh |
| `-noimp` | Skip node/animation |
| `-loop` / `-cycle` | Looping animation clip |

  Pattern for AI props: export a simplified copy of the mesh named `<name>-convcolonly` next to the render mesh. Alternatively, use Advanced Import Settings → mesh → `Generate > Physics` (Body Type Static/Dynamic/Area, Shape Type including convex decomposition).
- Textures: 3D defaults to VRAM Compressed (S3TC/BPTC on desktop, ETC2/ASTC on mobile). Godot on mobile/web may not show textures over 4096²; use `Process > Size Limit`.

### Rigged characters

1. Advanced Import Settings → `Skeleton3D` → **Retarget → Bone Map** → new `BoneMap` → Profile **`SkeletonProfileHumanoid`** (auto-maps by name; red/magenta = problem).
2. Rest Fixer: **Overwrite Axis** (needed to share animations; can damage odd rests), **Fix Silhouette** for A-pose, `Apply Node Transform`, `Normalize Position Tracks`.
3. Remove Tracks: `Except Bone Transform`, `Unimportant Positions`; use `Unmapped Bones` removal only for animation libraries (it can freeze accessories in scenes).
4. Shared clips: import clip-only GLBs as **Animation Library** with the same BoneMap, then add the library to the character's `AnimationPlayer`.
5. Mixamo-named rigs (`mixamorig:`): use **MixaBridge** (asset library 5096, MIT, Godot 4.4+). Mixamo isn't covered by the official docs.
6. State logic: `AnimationTree` with a state machine; `animation_tree["parameters/playback"].travel("Run")`. Root motion: set the root-motion track, then apply `get_root_motion_position()` in `CharacterBody3D`.

### Automating imports

- **Per-project rules:** `EditorScenePostImport` script, assigned as the scene's *Custom Script* import option:

```gdscript
# res://tools/post_import.gd
@tool
extends EditorScenePostImport

func _post_import(scene: Node) -> Object:
    for n in scene.find_children("*", "MeshInstance3D", true, false):
        if n.name.ends_with("_nocast"):
            n.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
    return scene
```

- **Project-wide rules:** an `EditorScenePostImportPlugin` registered by an `EditorPlugin` (`add_scene_post_import_plugin`), with `_pre_process` / `_post_process`.
- **Headless CLI:**

```bash
GODOT=/opt/godot/Godot_v4.7.2-stable_linux.x86_64
"$GODOT" --headless --path ./game --import                         # import all assets, then exit
"$GODOT" --headless --path ./game -s res://tools/check_assets.gd   # run a SceneTree tool script
"$GODOT" --headless --path ./game --export-release "Android" build/game.apk   # preset in export_presets.cfg
```

- Commit `*.import` sidecar files; never commit `.godot/imported/`. The `.import` `[params]` keys aren't documented for hand-editing (unverified). Prefer post-import scripts.

### 2D

```gdscript
# SpriteFrames from a horizontal strip
var frames := SpriteFrames.new()
frames.add_animation("run")
frames.set_animation_speed("run", 8.0)
frames.set_animation_loop_mode("run", SpriteFrames.LOOP_LINEAR)   # 4.7; set_animation_loop is deprecated
var sheet := load("res://sprites/hero_run.png")
for i in 6:
    var t := AtlasTexture.new()
    t.atlas = sheet
    t.region = Rect2(i * 64, 0, 64, 64)
    frames.add_frame("run", t)
ResourceSaver.save(frames, "res://sprites/hero.tres")
```

- **Lit sprites:** `CanvasTexture` (`diffuse_texture`, `normal_texture`, `specular_texture`, `specular_shininess` > 1). Needs a Light2D; raise the light's `height`.
- **Tiles:** `TileMapLayer` (TileMap is deprecated). Build a `TileSet` + `TileSetAtlasSource` by script (`create_tile`, `add_source`, `set_cell`); isometric via TileSet `tile_shape`/`tile_layout`.
- **Parallax:** **`Parallax2D`** (`ParallaxBackground` is deprecated): `scroll_scale`, `repeat_size`, `repeat_times`, `autoscroll`.
- 2D textures: Lossless compression, mipmaps off; pixel art → `default_texture_filter = Nearest`.

## Unity 6

### Static props

- GLB via **glTFast** (install `com.unity.cloud.gltfast`); supports Draco, meshopt, KTX2/Basis.
- FBX via the built-in ModelImporter: `generateMeshLods = true` (Unity 6 Mesh LOD generator; ≥256-tri source; don't mix with `_LODn`-named meshes), `addCollider` for MeshColliders. Use `convex = true` for dynamic bodies.
- Mobile textures: **ASTC** (iOS A8+, Android ES 3.1/Vulkan), ETC2 fallback. PC: BC7.

### Rigged humanoids

1. Get **FBX** (Tripo/Meshy export it) or convert:

```python
# blender -b -P glb_to_fbx.py -- in.glb out.fbx
import bpy, sys
src, dst = sys.argv[sys.argv.index("--") + 1:][:2]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
bpy.ops.export_scene.fbx(filepath=dst, bake_anim=True,
                         add_leaf_bones=False,          # extra leaf bones confuse Humanoid mapping
                         use_armature_deform_only=True)
```

2. Rig → Animation Type **Humanoid**, Avatar Definition *Create From This Model* → Configure to fix mapping. Clip FBXs: Humanoid, *Copy From Other Avatar*.
3. Automate with an `AssetPostprocessor`:

```csharp
// Assets/Editor/ModelImportRules.cs
using UnityEditor;

public class ModelImportRules : AssetPostprocessor
{
    void OnPreprocessModel()
    {
        var mi = (ModelImporter)assetImporter;
        bool character = assetPath.Contains("/Characters/");
        mi.animationType = character ? ModelImporterAnimationType.Human
                                     : ModelImporterAnimationType.Generic;
        mi.importAnimation = character;
        mi.generateMeshLods = !character;   // Unity 6 Mesh LOD generator
        mi.addCollider = false;             // add simplified colliders explicitly
        mi.isReadable = false;
        mi.globalScale = 1f;
    }
}
```

4. Animator Controllers by script: `AnimatorController.CreateAnimatorControllerAtPath`, `AddParameter`, `layers[0].stateMachine.AddState`, `AddTransition`.

### Headless

```bash
"$UNITY" -batchmode -nographics -quit -projectPath ./unity-project \
  -executeMethod AssetPipeline.ImportAll -logFile import.log
```

`-nographics` needs `-logFile` to see output. Force re-import from the method with `AssetDatabase.ImportAsset(path, ImportAssetOptions.ForceUpdate)`.

### 2D

```csharp
// Assets/Editor/SpriteImportRules.cs — pixel-art sprite defaults
using UnityEditor;

public class SpriteImportRules : AssetPostprocessor
{
    void OnPreprocessTexture()
    {
        if (!assetPath.Contains("/Sprites/")) return;
        var ti = (TextureImporter)assetImporter;
        ti.textureType = TextureImporterType.Sprite;
        ti.spriteImportMode = SpriteImportMode.Multiple;
        ti.spritePixelsPerUnit = 100;
        ti.filterMode = UnityEngine.FilterMode.Point;
        ti.textureCompression = TextureImporterCompression.Uncompressed;
        ti.mipmapEnabled = false;
    }
}
```

- **Slicing by script:** `TextureImporter.spritesheet` is obsolete. Use `ISpriteEditorDataProvider` via `SpriteDataProviderFactories` → `SetSpriteRects` → `Apply()` → `SaveAndReimport()`.
- **Normal maps:** Secondary Texture `_NormalMap` (`TextureImporter.secondarySpriteTextures` by script) + Sprite-Lit-Default material + URP 2D Renderer.
- Tilemap: Grid (Isometric layout for iso) + `Tilemap.SetTile`.

## Triangle and texture budgets (starting points)

From vendor/community guides; no official engine numbers exist.

| Asset | Mobile | PC / console |
|---|---|---|
| Small prop | 300–1,500 tris | 1k–10k |
| Hero prop | 1.5k–5k | 10k–50k |
| Character | 3k–10k | 20k–80k |
| Prop textures | 256–1024² | 1024–2048² |
| Character textures | 1024–2048² | 2048–4096² |
| VR standalone (Quest) | avatar < 10k, scene ~250k total | — |

## gltf-transform cheatsheet

```bash
npx -y @gltf-transform/cli inspect in.glb
npx -y @gltf-transform/cli resize in.glb out.glb --width 1024 --height 1024
npx -y @gltf-transform/cli webp in.glb out.glb                        # Godot OK; test in Unity
npx -y @gltf-transform/cli etc1s in.glb out.glb --quality 255         # KTX2/Basis (needs KTX-Software); Unity
npx -y @gltf-transform/cli uastc in.glb out.glb --level 4 --zstd 18   # KTX2 high quality (normals); Unity
npx -y @gltf-transform/cli meshopt in.glb out.glb --level medium      # Unity only
npx -y @gltf-transform/cli draco in.glb out.glb                       # Unity only
```

## Sources

Godot: docs.godotengine.org/en/stable (advanced_import_settings, node_type_customization, mesh_lod, command_line_tutorial, import_process, importing_images, retargeting_3d_skeletons, animation_tree, class_editorscenepostimport, class_editorscenepostimportplugin, class_spriteframes, class_parallax2d, class_canvastexture, class_tilemaplayer) · github.com/godotengine/godot/tree/4.7/modules/gltf/extensions · godotengine.org/asset-library/asset/5096 (MixaBridge)

Unity: unity.com/releases/editor/whats-new/6000.6.6 · docs.unity3d.com/6000.5 (EditorCommandLineArguments, AssetPostprocessor, ModelImporter, TextureImporter, AnimatorController, Tilemap.SetTile, LODGroup, texture-choose-format-by-platform) · docs.unity3d.com/6000.4/Documentation/Manual/lod/mesh-lod-generator.html · docs.unity3d.com/Manual/Sprite-data-provider-api.html · github.com/atteneder/glTFast (CHANGELOG 6.20.0)

Tools: gltf-transform.dev/cli · docs.blender.org (command line, export_scene.fbx)
