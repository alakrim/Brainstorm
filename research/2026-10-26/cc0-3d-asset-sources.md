# Raw research: verified CC0 / permissive 3D asset sources (2026-10-26)

Raw notes. Conclusions are in [`reference/free-3d-asset-sources.md`](../../reference/free-3d-asset-sources.md). Every URL below was requested from the sandbox on 2026-10-26 (about 20:00 UTC). Only jsDelivr endpoints were used (`data.jsdelivr.com` listings, `cdn.jsdelivr.net/gh/...` files). github.com, codeload and the GitHub API were not used.

Sandbox notes:
- jsDelivr refuses listings for repos over 50 MB (HTTP 403, "Package size exceeded the configured limit of 50 MB"). Large repos can only be read file by file.
- jsDelivr listings report `version: main` and do not give a commit SHA. The listing `hash` field is a base64 SHA-256 per file. Downloaded files were checked against it (see "Downloads" below).
- Byte totals below come from the listing `size` fields. "MB" means 10^6 bytes.

---

## 1. KayKit packs on jsDelivr (`KayKit-Game-Assets/<repo>@main`)

### 1a. Flat listings

URL pattern: `https://data.jsdelivr.com/v1/packages/gh/KayKit-Game-Assets/<repo>@main?structure=flat`

| Repo | HTTP | Files | Total bytes | Extensions (count) | Top-level path in repo |
|---|---|---|---|---|---|
| KayKit-Character-Pack-Adventures-1.0 | 200 | 72 | 18.75 MB | glb 5, gltf 27, bin 27, png 12, txt 1 | `addons/kaykit_character_pack_adventures/` |
| KayKit-Character-Pack-Skeletons-1.0 | 200 | 34 | 19.63 MB | glb 4, gltf 13, bin 13, png 3, txt 1 | `addons/kaykit_character_pack_skeletons/` |
| KayKit-Medieval-Hexagon-Pack-1.0 | 200 | 996 | 29.87 MB | obj 263, gltf 221, bin 221, mtl 263, png 27, txt 1 | `addons/kaykit_medieval_hexagon_pack/` |
| KayKit-Dungeon-Remastered-1.0 | 200 | 622 | 17.01 MB | glb 203 (named `*.gltf.glb`, except `chest.glb`, `floor_tile_big_spikes.glb`), obj 208, mtl 208, png 2, txt 1 | `addons/kaykit_dungeon_remastered/` |
| KayKit-Prototype-Bits-1.0 | 200 | 302 | 2.32 MB | gltf 72, bin 72, obj 77, mtl 77, png 3, txt 1 | `addons/kaykit_prototype_bits/` |
| KayKit-Halloween-Bits-1.0 | 200 | 270 | 3.27 MB | gltf 63, bin 63, obj 70, mtl 70, png 3, txt 1 | `addons/kaykit_halloween_bits/` |
| KayKit-Furniture-Bits-1.0 (new, see 1d) | 200 | 216 | 2.08 MB | gltf 53, bin 53, obj 53, mtl 53, png 3, txt 1 | `addons/kaykit_furniture_bits/` |
| KayKit-City-Builder-Bits-1.0 (new) | 200 | 208 | 3.89 MB | gltf 41, bin 41, obj 61, mtl 61, png 3, txt 1 | `addons/kaykit_city_builder_bits/` |
| KayKit-Space-Base-Bits-1.0 (new) | 200 | 264 | 4.01 MB | gltf 57, bin 57, obj 73, mtl 73, png 3, txt 1 | `addons/kaykit_space_base_bits/` |
| KayKit-Restaurant-Bits-1.0 (new) | 200 | 592 | 9.38 MB | gltf 144, bin 144, obj 150, mtl 150, png 3, txt 1 | `addons/kaykit_restaurant_bits/` |

Format notes:
- No `.fbx` file appears in any of the 10 listings. Every README (see 1c) says FBX is included. Either the GitHub copy omits FBX, or jsDelivr omits it. **(unverified: which is true)**.
- The `.gltf` files are `.gltf` + `.bin` pairs. The `.glb` files are single binaries.
- PNG files per pack: 2 to 27 (Adventures 12, Skeletons 3, Hexagon 27, Dungeon 2, the Bits packs 3). Knight's texture is one 1024x1024 atlas PNG of 14 KB, matching the README's "single gradient atlas" claim.

Folder layout detail:
- Adventures: characters in `Characters/gltf/` (5 .glb). Weapons and props in `Assets/gltf/` (27 .gltf + .bin: arrow, axe_1handed, axe_2handed, crossbow_1handed, crossbow_2handed, dagger, mug_empty, mug_full, quiver, shield_badge(+_color), shield_round(+_barbarian,+_color), shield_spikes(+_color), shield_square(+_color), smokebomb, spellbook_closed/open, staff, sword_1handed, sword_2handed(+_color), wand, arrow_bundle).
- Skeletons: characters in `Characters/gltf/` (4 .glb: Skeleton_Mage, Skeleton_Minion, Skeleton_Rogue, Skeleton_Warrior). Weapons in `Assets/gltf/` (13 .gltf: Skeleton_Arrow, Skeleton_Arrow_Broken, Skeleton_Arrow_Broken_Half, Skeleton_Arrow_Half, Skeleton_Axe, Skeleton_Blade, Skeleton_Crossbow, Skeleton_Quiver, Skeleton_Shield_Large_A/B, Skeleton_Shield_Small_A/B, Skeleton_Staff).
- Hexagon: `Assets/gltf/buildings/{blue 18, green 18, neutral 21, red 18, yellow 18}`, `decoration/nature` 42, `decoration/props` 26, `tiles/base` 5, `tiles/coast` 5 (+5 waterless), `tiles/rivers` 15 (+15 waterless), `tiles/roads` 15 (gltf file counts).
- Dungeon Remastered: all 203 .glb in `Assets/gltf/` (banners, barrels, barriers, beds, bottles, boxes, candles, chests, coins, columns, crates, floors, keg, keys, pillars, plates, rubble, shelves, stairs and more).

### 1b. LICENSE.txt (exact text)

URL pattern: `https://cdn.jsdelivr.net/gh/KayKit-Game-Assets/<repo>@main/<path>/LICENSE.txt`

All return HTTP 200. The license line is the same in each file:
- `License: (Creative Commons Zero, CC0)` followed by `http://creativecommons.org/publicdomain/zero/1.0/`
- `This content is free to use in personal, educational and commercial projects.`
- Credit is requested, not required. Wording differs by pack:
  - Adventures: "Support me by using a brand resource provided in this pack or by crediting Kay Lousberg, www.kaylousberg.com (this is not mandatory)".
  - Dungeon Remastered, Halloween, Prototype, Furniture, City Builder, Space Base, Restaurant, Medieval Hexagon: "Support me by crediting Kay Lousberg, www.kaylousberg.com (this is not mandatory)".
  - Skeletons: same as the others, with the intro "This characters here thanks to…".

| Repo | LICENSE.txt path | HTTP | Creation date in file |
|---|---|---|---|
| Adventures | `addons/kaykit_character_pack_adventures/LICENSE.txt` | 200 | 13/03/2023 |
| Skeletons | `addons/kaykit_character_pack_skeletons/LICENSE.txt` | 200 | 02/02/2024 |
| Medieval Hexagon | `addons/kaykit_medieval_hexagon_pack/LICENSE.txt` | 200 | 26/04/2024 |
| Dungeon Remastered | `addons/kaykit_dungeon_remastered/Assets/LICENSE.txt` | 200 | 13/03/2023 |
| Prototype Bits | `addons/kaykit_prototype_bits/Assets/LICENSE.txt` | 200 | 14/09/2023 |
| Halloween Bits | `addons/kaykit_halloween_bits/Assets/LICENSE.txt` | 200 | 06/10/2023 |
| Furniture Bits | `addons/kaykit_furniture_bits/Assets/LICENSE.txt` | 200 | 08/09/2023 |
| City Builder Bits | `addons/kaykit_city_builder_bits/Assets/LICENSE.txt` | 200 | 25/08/2023 |
| Space Base Bits | `addons/kaykit_space_base_bits/Assets/LICENSE.txt` | 200 | 01/09/2023 |
| Restaurant Bits | `addons/kaykit_restaurant_bits/Assets/LICENSE.txt` | 200 | 29/09/2023 |

Root-level `LICENSE` in the Adventures repo: `https://cdn.jsdelivr.net/gh/KayKit-Game-Assets/KayKit-Character-Pack-Adventures-1.0@main/LICENSE` returned 404. The license is only in the addon folder.

### 1c. Root README.md (claims)

URL pattern: `https://cdn.jsdelivr.net/gh/KayKit-Game-Assets/<repo>@main/README.md`. All 10 repos return HTTP 200.

Claims that matter, quoted or closely paraphrased from the README:
- **Adventures:** "4 (+2 in the EXTRA tier) stylised low-poly character assets… fully rigged and animated… 75 animations… 25+ accessories." Free repo contents: 5 .glb characters (Barbarian, Knight, Mage, Rogue, Rogue_Hooded). **Mismatch: README says 4 free characters, the repo has 5.** Single 1024 gradient atlas, downsizable to 128. Formats: FBX, GLTF.
- **Skeletons:** "4 (+2 in EXTRA) … fully rigged and animated … 90+ animations … 10+ accessories". Repo has 4 characters (matches). **Animation count is also understated: Skeleton_Warrior.glb has 95 clips (see section 3).**
- **Medieval Hexagon:** "over 200 stylised medieval hexagonal tiles, buildings, and props". Buildings in 4 colours (blue, red, green, yellow). "A bunch of units (in the extra version)". No units in the free repo. Formats FBX, GLTF.
- **Dungeon Remastered:** "over 200 stylised 3D Dungeon assets and props". Formats FBX, GLTF, OBJ.
- **Prototype Bits:** "64+ low poly models" for prototyping. Formats OBJ, FBX, GLTF.
- **Halloween Bits:** "60+ low poly models", spooky set (cemetery). Formats OBJ, FBX, GLTF.
- **Furniture Bits:** "50+ low poly models", furniture. Formats OBJ, FBX, GLTF.
- **City Builder Bits:** "32+ low poly models", city building. Formats OBJ, FBX, GLTF.
- **Space Base Bits:** "48+ low poly models", modular space bases. Formats OBJ, FBX, GLTF.
- **Restaurant Bits:** "140+ low poly models", food by ingredient and cooking state. Formats OBJ, FBX, GLTF.

None of the static-prop READMEs claims rigging or animation.

### 1d. Name guesses (`KayKit-Game-Assets/<name>@main`, 30 total)

Listing URL: `https://data.jsdelivr.com/v1/packages/gh/KayKit-Game-Assets/<name>@main?structure=flat`

| # | Name guessed | HTTP | Result |
|---|---|---|---|
| 1 | KayKit-Character-Pack-Adventurers-1.0 | 404 | no (correct spelling is "Adventures") |
| 2 | KayKit-Furniture-Bits-1.0 | 200 | **exists**, 216 files |
| 3 | KayKit-City-Builder-Bits-1.0 | 200 | **exists**, 208 files |
| 4 | KayKit-Space-Base-Bits-1.0 | 200 | **exists**, 264 files |
| 5 | KayKit-Restaurant-Bits-1.0 | 200 | **exists**, 592 files |
| 6 | KayKit-Platformer-Pack-1.0 | 404 | no |
| 7 | KayKit-Forest-Nature-Pack-1.0 | 404 | no |
| 8 | KayKit-Dungeon-Pack-1.0 | 404 | no |
| 9 | KayKit-Medieval-Builder-Pack-1.0 | 404 | no |
| 10 | KayKit-Racing-Bits-1.0 | 404 | no |
| 11 | KayKit-Space-Base-Pack-1.0 | 404 | no |
| 12 | KayKit-Character-Pack-Adventures-2.0 | 404 | no |
| 13 | KayKit-Character-Pack-Adventures-1.1 | 404 | no |
| 14 | KayKit-Skeletons-1.0 | 404 | no |
| 15 | KayKit-Animations-1.0 | 404 | no |
| 16 | KayKit-Animation-Pack-1.0 | 404 | no |
| 17 | KayKit-Character-Pack-Mages-1.0 | 404 | no |
| 18 | KayKit-Character-Pack-Animals-1.0 | 404 | no |
| 19 | KayKit-Character-Pack-Monsters-1.0 | 404 | no |
| 20 | KayKit-Space-Characters-1.0 | 404 | no |
| 21 | KayKit-Modular-Dungeon-1.0 | 404 | no |
| 22 | KayKit-Dungeon-Remastered-1.1 | 404 | no |
| 23 | KayKit-Prototype-Bits-1.1 | 404 | no |
| 24 | KayKit-Halloween-Bits-1.1 | 404 | no |
| 25 | KayKit-Medieval-Hexagon-Pack-2.0 | 404 | no |
| 26 | KayKit-Forest-Pack-1.0 | 404 | no |
| 27 | KayKit-Sports-Bits-1.0 | 404 | no |
| 28 | KayKit-Ultimate-Pack-1.0 | 404 | no |
| 29 | KayKit-Game-Assets (org-level name) | 404 | no |
| 30 | KayKit-Starter-Kit-1.0 | 404 | no |

Only `@main` was tried. A 404 here means "no such repo at @main", not "no such repo". **(unverified: other branches or other names)**. Real KayKit packs such as Forest/Nature, Platformer, or Animation packs may exist under other names.

New packs found: Furniture Bits, City Builder Bits, Space Base Bits, Restaurant Bits. All four are CC0 per their LICENSE.txt (section 1b) and their READMEs.

---

## 2. Other permissive sources (GitHub-hosted, via jsDelivr)

### 2a. KhronosGroup/glTF-Sample-Assets (per-model licenses)

| URL | HTTP | Size | Note |
|---|---|---|---|
| `data.jsdelivr.com/v1/packages/gh/KhronosGroup/glTF-Sample-Assets@main?structure=flat` | 403 | 278 B | "Package size exceeded the configured limit of 50 MB" |
| `cdn.jsdelivr.net/gh/KhronosGroup/glTF-Sample-Assets@main/README.md` | 200 | 6,294 B | Index of models. Says the repo docs are CC-BY-4.0 and that each model's `README.md`/`LICENSE.md` is the authority |
| `…/Models/Fox/README.md` | 200 | 1,782 B | Credits (see below) |
| `…/Models/Fox/LICENSE.md` | 200 | 1,061 B | Per-file-group licences (see below) |
| `…/Models/Fox/glTF-Binary/Fox.glb` | 200 | 162,852 B | Downloaded to scratchpad and not analysed |
| `…/LICENSE` (root) | 404 | 77 B | no root license file of that name |
| `…/LICENSE.md` (root) | 404 | 80 B | none |

Fox license detail (verbatim structure from `Models/Fox/LICENSE.md`): three entries, all under "All files directly associated with the model including all text, image and binary files":
- CC0-1.0 (model), credited "2014, Public. … PixelMannen for Model".
- CC-BY-4.0 (rigging and animation), credited "tomkranis for Rigging & Animation".
- CC-BY-4.0 (glTF conversion), credited "@AsoboStudio and @scurest for Conversion to glTF".
- The metadata files are CC-BY-4.0.

So Fox is **not purely CC0**. Rig and animation need attribution. The README says "Multiple animations cycles: Survey, Walk, Run."

### 2b. mrdoob/three.js (examples/models)

| URL | HTTP | Size | Note |
|---|---|---|---|
| `data.jsdelivr.com/v1/packages/gh/mrdoob/three.js@dev?structure=flat` | 403 | 244 B | >50 MB limit |
| `cdn.jsdelivr.net/gh/mrdoob/three.js@dev/README.md` | 200 | — | |
| `…/three.js@dev/LICENSE` | 200 | 1,081 B | MIT, "Copyright © 2010-2026 three.js authors" (code licence) |
| `…/three.js@r170/README.md` | 200 | — | tag `r170` exists on CDN (tags work) |
| `…/examples/models/gltf/RobotExpressive/README.md` | 200 | 364 B | "Model by Tomás Laulhé (Quaternius). … CC0 1.0." Modifications by Don McCurdy (3 facial morph targets, FBX2GLTF conversion, duplicate materials removed) |
| `…/examples/models/gltf/RobotExpressive/RobotExpressive.glb` | 200 | 463,988 B | body not kept |
| `…/examples/models/gltf/Soldier.glb` | 200 | 2,160,468 B | header "glTF" checked, body not kept |
| `…/examples/models/gltf/Xbot.glb` | 200 | 2,930,032 B | body not kept |
| `…/examples/models/gltf/Michelle.glb` | 200 | 3,276,888 B | body not kept |
| `…/examples/models/gltf/Fox.glb` | 404 | — | path wrong, not chased |
| `…/examples/models/gltf/LICENSE`, `…/gltf/README.md`, `…/models/README.md`, `…/RobotExpressive/LICENSE` | 404 | — | no per-folder license files |

Soldier, Xbot and Michelle are not verified as CC0. The three.js repo has no per-model license text at the paths tried. Their origin is not checked here. **(unverified: license of Soldier, Xbot, Michelle; likely Mixamo-derived terms, check before shipping)**.

Note for the transient GETs: Soldier, Xbot, Michelle and RobotExpressive were fetched once to check status and size. About 8.8 MB was transferred in total and discarded.

### 2c. pmndrs/assets (optimized GLB examples, CC0 repo)

| URL | HTTP | Size | Note |
|---|---|---|---|
| `data.jsdelivr.com/v1/packages/gh/pmndrs/assets@main?structure=flat` | 403 | 246 B | >50 MB limit |
| `cdn.jsdelivr.net/gh/pmndrs/assets@main/LICENSE` | 200 | 7,048 B | Full CC0 1.0 Universal text |
| `…/pmndrs/assets@main/README.md` | 200 | 6,412 B | "Models: A selection of models optimized with gltf-transform optimize and converted to glb." Imported as `@pmndrs/assets/models/suzi.glb` |
| `…/pmndrs/assets@master/LICENSE` and README | 200 | same | |

Repo-level license is CC0 1.0. Per-model origin is not checked. Models are not inspected. **(unverified: per-model origin)**.

### 2d. Quaternius

| URL | HTTP | Note |
|---|---|---|
| `data.jsdelivr.com/v1/packages/gh/Quaternius/quaternius.github.io@main?structure=flat` | 403 | >50 MB |
| `cdn.jsdelivr.net/gh/Quaternius/quaternius.github.io@main/README.md` | 200 | content is "# quaternius.com" (17 bytes), just a site repo |
| `…/quaternius.github.io@main/LICENSE` and `LICENSE.md` (and @master) | 404 | no license file |

The Quaternius site repo does not contain the packs and does not state a license here. Quaternius is CC0 per the RobotExpressive README (section 2b). The Quaternius license for other packs is **(unverified)** in this sandbox.

### 2e. Other candidates tried

| Repo | HTTP | Note |
|---|---|---|
| KhronosGroup/glTF-Sample-Models@master listing | 403 | >50 MB. Not chased |
| KenneyNL/kenney-assets@master listing | 404 | not found at master. Not chased. Kenney's own site is CC0 **(unverified in this sandbox)** |

---

## 3. Inside the GLBs (verification on two characters)

Downloads (full files, both saved in the scratchpad, not in the repo):

| File | Source URL | Bytes (listing = local) | sha256 (base64) matches listing hash |
|---|---|---|---|
| Knight.glb | `cdn.jsdelivr.net/gh/KayKit-Game-Assets/KayKit-Character-Pack-Adventures-1.0@main/addons/kaykit_character_pack_adventures/Characters/gltf/Knight.glb` | 3,659,532 | yes |
| Skeleton_Warrior.glb | `cdn.jsdelivr.net/gh/KayKit-Game-Assets/KayKit-Character-Pack-Skeletons-1.0@main/addons/kaykit_character_pack_skeletons/Characters/gltf/Skeleton_Warrior.glb` | 4,863,620 | yes |

Range requests were tried first to read only the GLB JSON chunk. For Knight, the range response was correct. For Skeleton_Warrior, the range response returned bytes that were not the file header, and that was not investigated further. Full downloads were used instead. This is more than the "one character file" budget in the task: two character files, about 8.5 MB.

Parsing: `scripts/check_glb.py` (repo script) and a stdlib-only parser (`glbinfo.py`, kept in the scratchpad).

### Knight.glb (Adventures)
- GLB version 2. JSON chunk 1,972,652 B, BIN chunk 1,686,852 B. `extensionsUsed` and `extensionsRequired` are absent (plain GLB, no Draco, no meshopt).
- Triangles 6,952. Vertices 7,024. 15 meshes. 57 nodes. 1 skin with 41 joints. 1 material. 1 image: 1024x1024 PNG, 14 KB.
- **76 animations** (README says 75). Total 8,712 channels. Animation sampler data uses 8,767 bufferViews, which is 1,331,056 B, or **78.9% of the BIN chunk**.
- Weapon and shield nodes are children of the hand slot bones:
  - `handslot.r` children: `1H_Sword`, `2H_Sword` (both meshes).
  - `handslot.l` children: `1H_Sword_Offhand`, `Badge_Shield`, `Rectangle_Shield`, `Round_Shield`, `Spike_Shield` (all meshes).
  - Other mesh nodes: `Knight_Helmet`, `Knight_Cape`, plus skinned `Knight_ArmLeft`, `Knight_ArmRight`, `Knight_Body`, `Knight_Head`, `Knight_LegLeft`, `Knight_LegRight`.
- No `visible` flag appears in `extras` or `extensions` (core glTF has no visibility property). Showing or hiding weapons is done in engine code.

### Skeleton_Warrior.glb (Skeletons)
- JSON chunk 2,443,308 B. Triangles 5,934. 10 meshes. 52 nodes. 1 skin with 41 joints. 2 materials (skeleton, Glow). 1 image: 1024x1024 PNG, 17 KB.
- **95 animations** (README says 90+).
- `handslot.l` and `handslot.r` have **no children**. No weapon meshes are built in. Weapons are separate files in `Assets/gltf/Skeleton_*.gltf` (13 files). Attachment to the hand bone happens in game code.

### Cross-character comparison (Knight vs Skeleton_Warrior)
- Joint sets: both have 41 joints with identical names. Shared 41, only-in-one 0.
- Animation names: Knight 76, Skeleton_Warrior 95, shared 76 (every Knight clip name exists in the Skeleton file). Skeleton-only: 19 clips (`Death_C_Skeletons`, `Skeletons_Awaken_*`, `Spawn_*`, `Taunt`, `Taunt_Longer`, `Idle_B`, `Idle_Combat`, `Running_C`, `Walking_D_Skeletons`, and others).
- **Caveats:** only 2 of 9 characters were compared. Name equality is not proof of identical rest pose or bone lengths. Retargeting-free within the pack is verified for these two only. **(unverified: Barbarian, Mage, Rogue, Rogue_Hooded, Skeleton_Mage, Skeleton_Minion, Skeleton_Rogue)**.

### Measured optimization (re-run today)
- Command as given in the task, with gltf-transform CLI 4.5.1 installed from the npm registry into the scratchpad (`npm install @gltf-transform/cli@4.5.1`; registry returned 200):
  `gltf-transform optimize Knight.glb knight-opt.glb --compress meshopt --texture-compress false --simplify false --join false --flatten false --instance false`
- Result: 3,659,532 B to **2,028,872 B** (log: "3.66 MB → 2.03 MB"). Reproduces the user-reported 2.03 MB.
- Not re-measured: the 76-to-fewer animation strip. Upper bound from the BIN breakdown: about 1.33 MB of raw animation sampler data (before meshopt) plus the matching accessor and bufferView JSON. The actual saving is **(unverified)** until measured.
- Textures are not the problem. The 1024 PNG is 14 KB.

---

## 4. Provenance log

Manifest for this session: `research/2026-10-26/manifest.json`.

Per AGENTS.md, "pin versions": jsDelivr branch URLs (`@main`) are mutable. The commit SHA was not available through the allowed endpoints. Pin by the per-file SHA-256 from the jsDelivr listing (in the manifest) and re-check the listing before reuse.

---

## 5. Unverified / not done

- FBX: README claims, GitHub listing has none. **(unverified)**
- Rig and animation of the non-character packs (static props): not in README; not checked per file. Treated as static.
- Adventures README "4 characters" vs 5 in the repo, and "75 animations" vs 76 in Knight: recorded as found; the repo content is taken as the truth.
- Skeleton weapon attachment to `handslot.r`/`.l` at runtime: verified only that the GLB has no weapon children; the game-side attachment logic is in the pack docs, not checked.
- Three.js models other than RobotExpressive: license not verified (section 2b).
- Mixamo: not checked here. Repo-level notes in `reference/licenses.md` apply.
- Quaternius packs (not the site repo): not on GitHub at the paths tried; not verified.
- gltf-transform meshopt output loads in three.js only with the meshopt decoder registered. Not tested in this sandbox. **(unverified)**
- Godot 4.7 meshopt import limit: taken from `AGENTS.md` (repo rule 6), not re-tested here.
