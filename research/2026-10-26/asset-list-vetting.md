# Raw research: vetting a shared asset-source list for Bannerfall (2026-10-26)

Raw notes. Conclusions are in [`reference/free-3d-asset-sources.md`](../../reference/free-3d-asset-sources.md) (new section "Shared list vetting") and in the Bannerfall project file `docs/ASSETS.md`. Checked from the sandbox on 2026-10-26. Fetch method is given per source. "curl" means a direct HTTPS request through the agent proxy. "WebFetch" means a model-summarised fetch, so quoted text from it is a paraphrase and is marked as such. "WebSearch" means a secondary source.

Sandbox reachability (HTTP status of the first request):

| URL | Status | Note |
|---|---|---|
| kaylousberg.itch.io/kaykit-adventurers, /kaykit-dungeon | 200 / 200 | A later retry of the Adventurers page returned 429; text was taken from the first successful request |
| quaternius.com, /packs/rpgcharacters.html, /license.html | 200 | |
| kenney.nl/assets, /rpg-base, /tiny-town, /roguelike-rpg-pack, /1-bit-pack | 200 | |
| polyhaven.com, api.polyhaven.com | 200 | |
| ambientcg.com | 200 | |
| api.ambientcg.com | TLS failure (`no alternative certificate subject name matches target host name`) | Used `https://ambientcg.com/api/v2/full_json?...` instead, which works |
| game-icons.net; data.jsdelivr.com `game-icons/icons@master` | 200 | |
| poly.pizza | 403 (curl and WebFetch) | Unverified |
| sonniss.com/gameaudiogdc, /gdc-bundle-license | 403 (curl) | WebFetch of the license page worked (see below) |
| github.com/Orama-Interactive/Pixelorama | 403 | raw.githubusercontent.com and jsDelivr worked |
| ansimuz.itch.io/sunny-land-pixel-art-game-asset | 404 | Unverified URL |
| bfxr.net, jfxr.frozenfractal.com | 200 | Pages carry no license text in the HTML we could read |
| opengameart.org, lpc.opengameart.org, opengameart.org/content/tiny-16-basic | 200 | |
| pixelfrog-assets.itch.io/tiny-swords, pixel-boy.itch.io/ninja-adventure-asset-pack | 200 | |
| ldtk.io, mapeditor.org | 200 | |
| raw.githubusercontent.com (RPGAtlas, Pixelorama, ldtk, rot.js) | 200 (rot.js LICENSE at `master`: 404) | |
| rot.js npm metadata via cdn.jsdelivr.net/npm/rot-js/package.json | 200 | |

---

## 1. KayKit

**KayKit Adventurers** (`kaylousberg.itch.io/kaykit-adventurers`). Repo `KayKit-Game-Assets/KayKit-Character-Pack-Adventures-1.0@main`, LICENSE at `addons/kaykit_character_pack_adventures/LICENSE.txt` (jsDelivr, curl):

> License: (Creative Commons Zero, CC0)
> http://creativecommons.org/publicdomain/zero/1.0/
> This content is free to use in personal, educational and commercial projects.

itch page text (curl): "Free for personal and commercial use, no attribution required. (CC0 Licensed)". Low-poly, rigged characters with animations (Brainstorm research).

**KayKit Dungeon Remastered** (`kaylousberg.itch.io/kaykit-dungeon`, curl): "Free for personal and commercial use, no attribution required. (CC0)". "Yes, all included game assets are public domain (Creative Commons Zero) licensed." Formats listed on the page: FBX, OBJ, DAE, GLTF.

**KayKit Godot asset library, user "KayKit Game Assets"**: not checked (unverified). The packs are CC0 on the itch and jsDelivr pages.

## 2. Quaternius

**Site license** (`quaternius.com/license.html`, curl). Page title "Quaternius Asset License (QAL) v1.0", "Last updated: 8/28/2026". Summary:

> You can use these assets, free of charge, in personal, educational, and commercial games and other projects, with no credit required. You just can't resell or redistribute the assets themselves.

Section 2 grants the right to "Publish, distribute, sell, sublicense, and otherwise commercially exploit that Product, without owing us any fee, royalty, or credit" and states "No attribution is required."

Section 3(a): "You may not extract, repackage, sublicense, sell, or otherwise redistribute the Assets (in original or modified form) as a standalone asset, asset pack, stock file, template, or similar product, whether for free or for payment... It does not restrict distributing a completed Product that merely incorporates the Assets."

Section 7: changes "will not apply retroactively to Assets you've already obtained under an earlier version."

**Per-pack licenses (pack pages, curl):**

| Pack | Page URL | Models (page) | License line on page | Formats on page |
|---|---|---|---|---|
| RPG Character Pack | quaternius.com/packs/rpgcharacters.html | 6, "Animated", "Textured" | **CC0** | FBX, OBJ, Blend, glTF |
| Ultimate Monsters | quaternius.com/packs/ultimatemonsters.html | 50 | **CC0** | FBX (first formats block) |
| Cute Monsters | quaternius.com/packs/cutemonsters.html | 21 | **CC0** | FBX |
| Knight Character | quaternius.com/packs/knightcharacter.html | 10 | **CC0** | FBX |
| Ultimate Modular Characters | quaternius.com/packs/ultimatemodularcharacters.html | 11 | **CC0** | FBX |
| Bestiary Dungeon Monsters Kit | quaternius.com/packs/bestiarydungeonmonsterskit.html | 7 | **QAL** | FBX |

The pack pages are the per-pack authority. The site-wide QAL (updated 8/28/2026) appears on at least one newer pack. Read each pack page before download.

**Programmatic access.** Downloads are not reachable from the pages we could read. The pack pages link to Patreon, Discord, Twitter/X and ArtStation, and a "Download" button with no direct file URL. No GitHub mirror was found at the paths checked (see the Brainstorm reference). **(unverified: direct file URLs; no programmatic download path was found.)**

## 3. Kenney

**License** (`kenney.nl/support`, curl):

> Yes, all game assets on the asset pages are public domain licensed (CC0). You're free to use them, even in commercial projects.
> Attribution is not required, but if you choose to give credit you can do so by mentioning "Kenney". Do not use our logo...

Each asset page (curl) carries the line "License — Creative Commons CC0".

**2D packs checked** (zip sizes from HEAD, `content-length`):

| Pack | Page | Category | Zip bytes | Tile / format note |
|---|---|---|---|---|
| RPG Base | kenney.nl/assets/rpg-base | 2D | 1,553,446 | Category 2D, 230 files |
| Tiny Town | kenney.nl/assets/tiny-town | 2D | 182,243 | 2D, 16 px tiles |
| Roguelike/RPG pack | kenney.nl/assets/roguelike-rpg-pack | 2D | 715,373 | 16x16, 1700 files |
| 1-Bit Pack | kenney.nl/assets/1-bit-pack | 2D | 657,579 | 16x16 |
| UI Pack | kenney.nl/assets/ui-pack | 2D | 1,229,750 | 430 files |

**3D packs checked** (HEAD, all 200):

| Pack | Page category | Zip bytes | Zip URL |
|---|---|---|---|
| Nature Kit | 3D | 10,537,521 | `https://kenney.nl/media/pages/assets/nature-kit/37ac38a37b-1677698939/kenney_nature-kit.zip` |
| Fantasy Town Kit 2.0 | 3D, "160×" files | 3,854,691 | `https://kenney.nl/media/pages/assets/fantasy-town-kit/efe948d309-1754222374/kenney_fantasy-town-kit_2.0.zip` |
| Mini Dungeon | 3D, "30×" files | 1,796,820 | `https://kenney.nl/media/pages/assets/mini-dungeon/6cd72dc849-1785314274/kenney_mini-dungeon.zip` |
| Blocky Characters | 3D, "20×" files | 2,148,510 | `https://kenney.nl/media/pages/assets/blocky-characters/8369c0cf30-1749547469/kenney_blocky-characters_20.zip` |
| Mini Characters | 3D, "25×" files | 2,403,059 | `https://kenney.nl/media/pages/assets/mini-characters/bfc7e272b4-1774770718/kenney_mini-characters.zip` |

Format and polygon count were not inspected (no download). Nature Kit's "Files 3" parse was ignored. The zip was not opened. **(unverified: model format, poly count, visual style.)**

**Audio:** Interface Sounds (`kenney.nl/assets/interface-sounds`, CC0, zip 834,536 B), Music Jingles (`kenney.nl/assets/music-jingles`, CC0, zip 1,239,525 B). Both pages: "Category Audio, License Creative Commons CC0".

**Not on GitHub at the paths checked** (Brainstorm reference). Site is the source.

## 4. Poly Haven

**License** (`polyhaven.com/license`, curl). Page text includes "CC0 means absolute freedom." and "You do not need to give credit or attribution when using them (although it is appreciated)." API `info` field `license` is `null` (site-wide policy applies).

**API.** `https://api.polyhaven.com/assets?t=textures` returned 869 texture entries. `https://api.polyhaven.com/files/<id>` returns per-map URLs. Verified 1k JPG diffuse URLs:

| Asset | Categories / tags | 1k diffuse URL | Bytes (HEAD) |
|---|---|---|---|
| grass_path_2 (Grass Path 2, Rob Tuytel) | terrain, natural, outdoor; grass, pathway, path, stones | `https://dl.polyhaven.org/file/ph-assets/Textures/jpg/1k/grass_path_2/grass_path_2_diff_1k.jpg` | 716,010 |
| dirt_floor (Dirt Floor) | outdoor, natural, terrain; dirt, ground, brown, uneven | `https://dl.polyhaven.org/file/ph-assets/Textures/jpg/1k/dirt_floor/dirt_floor_diff_1k.jpg` | 903,417 |
| cobblestone_floor_08 (Cobblestone Floor 08) | floor, outdoor, man made; cobblestone, smooth, old, moss, pavement | `https://dl.polyhaven.org/file/ph-assets/Textures/jpg/1k/cobblestone_floor_08/cobblestone_floor_08_diff_1k.jpg` | 585,727 |
| brown_mud_02 (alternative dirt) | terrain, natural, outdoor | `https://dl.polyhaven.org/file/ph-assets/Textures/jpg/1k/brown_mud_02/brown_mud_02_diff_1k.jpg` | 527,741 |

Poly Haven's `files` payload also lists nor_gl, nor_dx, rough_ao, arm, AO and gltf per asset. Only the diffuse is needed for a stylized look.

## 5. ambientCG

**License** (`ambientcg.com`, curl, FAQ text): "Yes. All assets are released under the Creative Commons CC0 license, making them free to use without attribution - even in commercial circumstances."

**API.** `api.ambientcg.com` fails TLS through the proxy. The same endpoint on the main host works: `https://ambientcg.com/api/v2/full_json?type=Material&q=grass&limit=40&include=downloadData,statisticsData` (`numberOfResults` for the Material type at the time was 2037).

**Download URL pattern** (HEAD verified): `https://ambientcg.com/get?file=<AssetId>_1K-JPG.zip`.

| Asset | Tags | Zip bytes (HEAD) |
|---|---|---|
| Grass005 | clean, grass, green | 10,442,657 |
| PavingStones141 | cobblestone, floor, medieval | 9,235,036 |
| Ground110 | brown, dirt, dry | 10,415,140 |

The zips hold several maps each (color, normal, roughness, displacement). Use the color map only for a stylized look.

## 6. game-icons.net

**License** (`raw.githubusercontent.com/game-icons/icons/master/license.txt`, curl):

> Icons provided under the Creative Commons 3.0 BY or CC0 if mentioned below.
> ... Please, include a mention "Icons made by {author}" in your derivative work.

Some contributors are marked CC0 in the file, including "Viscious Speed ... - CC0" and "Zeromancer - CC0". Other contributors are CC BY 3.0. **Per-contributor check is needed.**

**Listing** (`https://data.jsdelivr.com/v1/packages/gh/game-icons/icons@master?structure=flat`): 4,229 SVG files in 37 contributor folders (4,236 files total).

**File pattern:** `https://cdn.jsdelivr.net/gh/game-icons/icons@master/<contributor>/<icon>.svg`

Did not check `game-icons.net/about/license.html` content.

## 7. Sonniss GDC audio bundle

**Via WebFetch of `https://sonniss.com/gdc-bundle-license`** (paraphrase from a model summary, not verbatim; the page returns 403 to curl). The summary cites "Version 2.0, effective 27 August 2026", with these quoted fragments:

- "Licensee may use and modify the licensed sound effects for personal and commercial projects" and "without attribution to the original creator". Summary: commercial use allowed, no attribution required.
- Restriction (c): "Licensee may not distribute, publish, sub-license or otherwise supply the sound effects as sound effects". "Re-designed and manipulated sounds remain licensed material under this Agreement." Summary: no redistribution as a sound library.

Bundle size and contents **(unverified)**.

## 8. Poly Pizza

`poly.pizza` returns 403 to curl and WebFetch. **Unverified.** WebSearch results (secondary, not the site): credit pages on itch.io and flat.social list Poly Pizza models under **CC-BY 3.0** with "via Poly Pizza" credits, and some CC0 items came from other sites. Per-model license must be checked on each model page.

## 9. Tools and engine-side

- **bfxr.net / jfxr.frozenfractal.com**: pages reached (200), no license text in HTML. GitHub LICENSE paths (`increpare/bfxr`, `ChevyRay/jfxr`) returned 404 via raw and jsDelivr. **(unverified: license of both.)**
- **jsfxr**: the TMHSDigital catalog lists "jsfxr ... Unlicense" (secondary).
- **LDtk**: `raw.githubusercontent.com/deepnight/ldtk/master/LICENSE` → "MIT License, Copyright (c) 2020, Sébastien Benard - Deepnight Games" (verified).
- **Tiled**: `cdn.jsdelivr.net/gh/mapeditor/tiled@master/LICENSE.GPL` → "GNU GENERAL PUBLIC LICENSE Version 2, June 1991" (verified). The GPL covers Tiled itself, not the maps made with it. That reading is general understanding, not legal advice.
- **Pixelorama**: `raw.githubusercontent.com/Orama-Interactive/Pixelorama/master/LICENSE` → "MIT License, Copyright (c) 2019-present Orama Interactive and contributors" (verified).
- **rot.js**: npm metadata `rot-js 2.2.1, license BSD-3-Clause` (verified via jsDelivr npm). GitHub LICENSE at `master` returned 404 **(unverified at repo level)**.

## 10. 2D pixel packs and OpenGameArt

| Source | URL | License (quoted) | Fit |
|---|---|---|---|
| Pixel Frog Tiny Swords | pixelfrog-assets.itch.io/tiny-swords | Page: "Feel free to use this asset pack in both personal and commercial projects" and "Crediting is not required", then "You may not redistribute, resell, or ...". Download list: "TS_old version_CC0 Licensed" for the older version | Poor: 2D pixel, 64 px grid |
| pixel-boy Ninja Adventure | pixel-boy.itch.io/ninja-adventure-asset-pack | "They are released under the Creative Commons Zero (CC0) license." | Poor: 2D top-down pixel |
| 0x72 DungeonTileset II | 0x72.itch.io/dungeontileset-ii | "You can use this tileset for whatever you like (CC-0)." Itch license field: "Creative Commons Zero v1.0 Universal" | Poor: 2D 16x16 pixel |
| ansimuz Sunny Land | the given itch URL returns 404 | WebSearch (secondary): OpenGameArt listings show CC0 for the artwork, and the bundled music is credited CC-BY | Poor: 2D pixel. Unverified URL |
| LPC (Liberated Pixel Cup) | lpc.opengameart.org | "dual licensed under CC BY-SA 3.0 and GPLv3" | Poor: 2D pixel; share-alike |
| OpenGameArt tiny-16-basic | opengameart.org/content/tiny-16-basic | "License(s): CC-BY 4.0 CC-BY 3.0 OGA-BY 3.0" | Poor: 2D tiles; attribution, mixed |

## 11. Code references

**RPGAtlas** (`github.com/DriftwoodGaming/RPGAtlas`, README and LICENSE via raw.githubusercontent.com, main branch):

- LICENSE: GNU GENERAL PUBLIC LICENSE Version 3, 29 June 2007. README: "RPGAtlas is free software, licensed under the GNU General Public License v3.0 (or later)".
- README features (verbatim fragments): "HD-2D renderer (tilted perspective, dynamic lights and shadows, animated water, day/night, weather, full post-processing)"; "Per-map opt-in WebGL2 mode: tilted perspective camera, extruded terrain, billboard sprites, bloom, depth of field, distance fog and point lights (events named `light #rrggbb radius`)"; "procedural chiptune music & sound effects"; "Play Together ... room code"; "no accounts, no email, no personal information"; "free-text chat is off by default with instant mute + report + owner kick/ban"; "players connect only to a server (never to each other...)".
- Structure (README): `src/renderer/` is the three.js HD-2D renderer; `js/sfx.js` holds procedural SFX and generative music; `js/assets.js` holds procedural tiles and sprites.
- **Do not copy code** into the MIT codebase. Concepts only, reimplemented independently.

**TMHSDigital/Free-Game-Dev-Assets** (`raw.githubusercontent.com/.../main/README.md`): a CC0-metadata catalog. Safe starting points it lists: Kenney (modular 3D, CC0), Quaternius (CC0), KayKit (CC0), ambientCG (CC0), Poly Haven (CC0), Kenney Music Jingles (CC0), Abstraction Music Loop Bundle (CC0 per catalog), jsfxr (Unlicense). Secondary; each item still needs its own source check.

**opengameart.org/content/tiny-16-basic** is listed above.
