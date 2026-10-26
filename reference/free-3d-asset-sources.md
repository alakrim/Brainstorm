# Free ready-made 3D asset sources (CC0 and permissive)

*Checked 2026-10-26 from the sandbox, through jsDelivr only. Every row below was verified that day unless marked **(unverified)**. Raw URL log: [`research/2026-10-26/cc0-3d-asset-sources.md`](../research/2026-10-26/cc0-3d-asset-sources.md). Provenance manifest: [`research/2026-10-26/manifest.json`](../research/2026-10-26/manifest.json). Not legal advice.*

## When to use a ready-made pack instead of image → 3D

| Use a ready-made pack when… | Use image → 3D ([`3d-rigged-characters.md`](../workflows/3d-rigged-characters.md), [`3d-props.md`](../workflows/3d-props.md)) when… |
|---|---|
| The subject exists in a pack (a humanoid adventurer, a skeleton, a dungeon piece, a building, furniture) | You need a unique subject, a specific look or your own brand design |
| You need a rig and a shared animation set without paying for rigging | The pack's style clashes with the game's look |
| You want $0 and no per-asset review of model provenance | You can pay $0.30–1.10 per accepted asset and do rig QA |
| The license must be simple (CC0: no attribution, no per-model chain) | You are ready to log and check each model's license |

Mixed approach that works: a pack for base characters, animations and set dressing, and generated props for the unique items. Keep the pack and the generated set in the same style block where you can.

## Verified packs

All KayKit packs are by Kay Lousberg, CC0 1.0 (`LICENSE.txt` in each pack, same license line in each: "License: (Creative Commons Zero, CC0)"). Sizes are the sum of the repo files on `main` as listed by jsDelivr on 2026-10-26.

| Pack (repo: `KayKit-Game-Assets/…@main`) | Contents | License | Formats in the repo | Repo size | Rigged / animated? | Best for |
|---|---|---|---|---|---|---|
| **Character Pack: Adventures 1.0** (`KayKit-Character-Pack-Adventures-1.0`) | 5 characters (Barbarian, Knight, Mage, Rogue, Rogue_Hooded); 27 weapon and prop glTFs | CC0 | GLB (characters); glTF + bin (props); PNG atlas | 18.8 MB | **Yes.** 41-joint skin. Knight.glb has **76 clips**. README says 4 free characters and 75 animations (repo has 5 and 76) | Heroes, NPCs, adventurers |
| **Character Pack: Skeletons 1.0** (`KayKit-Character-Pack-Skeletons-1.0`) | 4 skeletons (Mage, Minion, Rogue, Warrior); 13 weapon and shield glTFs | CC0 | GLB; glTF + bin; PNG | 19.6 MB | **Yes.** Same 41 joint names as Adventures. Skeleton_Warrior.glb has **95 clips** | Enemies, undead |
| **Medieval Hexagon Pack 1.0** (`KayKit-Medieval-Hexagon-Pack-1.0`) | Hex tiles (roads, rivers, coasts), buildings in 4 colours, nature and props | CC0 | glTF + bin; OBJ | 29.9 MB | No (static) | Hex strategy maps, village builders |
| **Dungeon Remastered 1.0** (`KayKit-Dungeon-Remastered-1.0`) | About 200 modular dungeon pieces: walls, floors, stairs, doors, chests, barrels, banners | CC0 | GLB (files named `*.gltf.glb`); OBJ | 17.0 MB | No (static) | Dungeon levels and interiors |
| **Prototype Bits 1.0** (`KayKit-Prototype-Bits-1.0`) | 64+ generic prototyping models | CC0 | glTF + bin; OBJ | 2.3 MB | No (static) | Greyboxing, placeholders |
| **Halloween Bits 1.0** (`KayKit-Halloween-Bits-1.0`) | 60+ spooky models (cemetery) | CC0 | glTF + bin; OBJ | 3.3 MB | No (static) | Graveyards, horror |
| **Furniture Bits 1.0** (`KayKit-Furniture-Bits-1.0`) | 50+ furniture pieces | CC0 | glTF + bin; OBJ | 2.1 MB | No (static) | Interiors |
| **City Builder Bits 1.0** (`KayKit-City-Builder-Bits-1.0`) | 32+ city buildings and props | CC0 | glTF + bin; OBJ | 3.9 MB | No (static) | City builders, RTS |
| **Space Base Bits 1.0** (`KayKit-Space-Base-Bits-1.0`) | 48+ modular space base pieces | CC0 | glTF + bin; OBJ | 4.0 MB | No (static) | Sci-fi bases |
| **Restaurant Bits 1.0** (`KayKit-Restaurant-Bits-1.0`) | 140+ food and kitchen models, by ingredient and cooking state | CC0 | glTF + bin; OBJ | 9.4 MB | No (static) | Cooking games, kitchens |

Notes:
- **FBX:** every README says FBX is included. None of the 10 GitHub repos contains an `.fbx` file. **(unverified: whether the itch.io download has FBX)**.
- **Other KayKit repos:** 26 other names were tried at `@main` and returned 404. Four exist and are in the table above. Others may exist under other names or branches **(unverified)**.
- **Triangles and textures** (repo script `scripts/check_glb.py`): Knight.glb has 6,952 triangles and one 1024 PNG of 14 KB. Skeleton_Warrior.glb has 5,934 triangles, two materials and one 1024 PNG.

### Other permissive GitHub sources (samples and references, check each model)

| Source | What is verified | Use it for | Caveat |
|---|---|---|---|
| **KhronosGroup/glTF-Sample-Assets** (`@main`) | Repo docs CC-BY-4.0. Per-model `LICENSE.md`. **Fox**: model CC0; rig and animation CC-BY-4.0 (tomkranis); glTF conversion CC-BY-4.0 (AsoboStudio, scurest) | Reference files, loader and pipeline tests | Not all CC0. Attribution needed for Fox's rig and animation. Read each model's license |
| **three.js `examples/models`** (`mrdoob/three.js@dev`) | Code MIT. **RobotExpressive**: CC0 1.0 (Quaternius model, modified by Don McCurdy) | Test and sample characters | Soldier, Xbot and Michelle: license **not verified** here (likely Mixamo-derived, check before shipping) |
| **pmndrs/assets** (`@main`) | Repo LICENSE: CC0 1.0. Models are optimized with `gltf-transform optimize` and saved as GLB | Examples of optimized GLBs | Per-model origin **(unverified)** |
| **Quaternius** (CC0 packs on quaternius.com) | Not on GitHub at the paths checked. The `quaternius.github.io` repo is only the website (README "# quaternius.com", no packs, no LICENSE) | (use the site directly) | **(unverified in this sandbox)**; licensed CC0 per the RobotExpressive README |
| KenneyNL (CC0 packs on kenney.nl) | Not found on GitHub at `@master` | (use the site directly) | **(unverified in this sandbox)** |

## How to fetch them reproducibly

Two URL patterns (both reachable from this sandbox; raw.githubusercontent.com also worked):

```
Listing:  https://data.jsdelivr.com/v1/packages/gh/<owner>/<repo>@<ref>?structure=flat
File:     https://cdn.jsdelivr.net/gh/<owner>/<repo>@<ref>/<path>
```

- Each listing entry has `name`, `size` and `hash` (base64 SHA-256). Check each download against `hash`.
- jsDelivr refuses listings for repos over 50 MB (HTTP 403). Those repos have to be fetched file by file.
- `@main` is a moving branch. For a reproducible build, pin the commit SHA or tag if you have it, and record the per-file hash (`manifest.json`). Commit SHAs were not available through the allowed endpoints; **(unverified: pinning by commit SHA on jsDelivr)**.

Script (tested 2026-10-26 on small files from Adventures and Prototype Bits; hash check passed):

```bash
#!/usr/bin/env bash
# Usage: fetch-kaykit.sh <owner/repo> <ref> <dest-dir> <path-regex>
# Lists the repo via jsDelivr, downloads each matching file from the CDN, checks its sha256.
set -euo pipefail
REPO=${1:?owner/repo}; REF=${2:-main}; DEST=${3:?dest dir}; RE=${4:-'\.glb$'}
mkdir -p "$DEST"
LIST=$(mktemp); trap 'rm -f "$LIST"' EXIT
curl -sfS "https://data.jsdelivr.com/v1/packages/gh/$REPO@$REF?structure=flat" -o "$LIST"
node -e '
const fs = require("fs");
const d = JSON.parse(fs.readFileSync(process.argv[1], "utf8"));
const re = new RegExp(process.argv[2]);
for (const f of d.files) if (re.test(f.name)) console.log([f.name, f.hash, f.size].join("\t"));
' "$LIST" "$RE" | while IFS=$'\t' read -r path hash size; do
  out="$DEST/$(basename "$path")"
  curl -sfS "https://cdn.jsdelivr.net/gh/$REPO@$REF$path" -o "$out"
  got=$(openssl dgst -sha256 -binary "$out" | base64)
  if [ "$got" != "$hash" ]; then echo "HASH MISMATCH: $out" >&2; rm -f "$out"; exit 1; fi
  echo "ok  $out  $size bytes"
done
```

Example (all humanoid characters of the Adventures pack, about 18 MB):

```bash
./fetch-kaykit.sh KayKit-Game-Assets/KayKit-Character-Pack-Adventures-1.0 main assets/kaykit/adventures '/Characters/gltf/.*\.glb$'
```

Then log each file to the asset manifest (URL, bytes, SHA-256, license, date), as in `AGENTS.md`.

## Tips for using these packs

1. **One rig, one clip set (for humanoids).** Verified on Knight.glb and Skeleton_Warrior.glb: both have the same 41 joint names, and all 76 Knight clip names exist in the Skeleton file (the skeleton file adds 19 more). So one animation setup can drive these humanoids by clip name, without retargeting. Verified on 2 of 9 characters. Check the rest pose before you rely on it **(unverified: other characters, rest pose)**.
2. **Adventurer weapons are built in.** Knight.glb has `1H_Sword`, `2H_Sword`, `1H_Sword_Offhand`, and four shields as child meshes of `handslot.r` and `handslot.l`. glTF has no visibility property, so show or hide them in code (`node.visible`). The pack also ships weapons as separate glTFs (`Assets/gltf/`) if you want to attach them yourself.
3. **Skeleton weapons are separate.** The skeleton GLBs have empty `handslot.r` and `handslot.l` bones (verified on Skeleton_Warrior.glb). Attach the `Assets/gltf/Skeleton_*.gltf` files to those bones in code.
4. **Size is animation.** In Knight.glb, 79% of the binary chunk (1.33 MB of 1.69 MB) is animation sampler data for 76 clips. The 1024 texture is 14 KB. Strip the clips you do not use first, then compress.
5. **Measured compression (2026-10-26, gltf-transform CLI 4.5.1):** `gltf-transform optimize Knight.glb out.glb --compress meshopt --texture-compress false --simplify false --join false --flatten false --instance false` takes Knight.glb from 3,659,532 B (3.66 MB) to 2,028,872 B (2.03 MB). Reproduced 2026-10-26 in the sandbox; the original number came from the Bannerfall project. Clip stripping is **not yet measured**.
6. **Meshopt has an engine cost.** The meshopt output is not loadable by Godot 4.7 (see [`AGENTS.md`](../AGENTS.md) rule 6). For three.js, the GLTFLoader needs the meshopt decoder registered **(unverified in this sandbox)**.
7. **FBX is missing from the GitHub copies.** Unity Humanoid needs FBX (see [`engine-import.md`](engine-import.md)). For Unity, get the FBX from the itch.io download **(unverified)**. Godot and three.js load the GLB directly.
8. **Mind the README counts.** Adventures README: 4 characters and 75 animations. The repo has 5 characters and Knight has 76 clips. Skeletons README: 90+ animations; Skeleton_Warrior has 95. Trust the files, not the blurbs.
9. **Credit is optional for KayKit (CC0)**, but keep each pack's `LICENSE.txt` next to the assets. Check every non-KayKit source per model: Khronos Fox has CC-BY parts, and three.js Soldier, Xbot and Michelle are unverified.

## Measured results

| Date | Project | Asset | Input | Result | Tool |
|---|---|---|---|---|---|
| 2026-10-26 | Bannerfall (reported) and asset-pipeline sandbox (re-run) | KayKit Adventures `Knight.glb` | 3,659,532 B, 76 clips | 2,028,872 B with meshopt (no texture or simplify changes) | `@gltf-transform/cli` 4.5.1 |
