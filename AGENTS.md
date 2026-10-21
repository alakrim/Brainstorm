# Operating guide for art/design agents

You are an art lead or orchestrator agent starting a project that needs game or app assets. This repo holds research already done on turning generated images into 2D, 2.5D and 3D assets. Read this file first, then follow the links.

## How to use this repo

1. **Pick the workflow.** Open [`README.md`](README.md) and use the decision table to find the workflow file for the asset type you need.
2. **Check the source images.** Every workflow starts from a generated image. [`workflows/00-source-images.md`](workflows/00-source-images.md) covers which generator to use, prompt blocks that give asset-ready images, and consistency across a set.
3. **Check licenses before you commit to a tool.** [`reference/licenses.md`](reference/licenses.md) lists which models are safe for commercial shipping. Never use a non-commercial (NC) model on assets that will ship.
4. **Check compute.** [`reference/compute-and-pricing.md`](reference/compute-and-pricing.md) covers hosted APIs vs rented GPUs and when to use each.
5. **Bring assets into the engine.** [`reference/engine-import.md`](reference/engine-import.md) has the Godot 4 and Unity 6 import settings and scripts for unattended imports.

## Rules

- **Prove the pipeline on one asset first.** Run a single asset end to end and check it in the engine before you batch. Most failures (wrong scale, flipped normals, wrong normal-map convention, broken rig) show up on the first asset.
- **Hosted API first, GPU rental second.** For under ~50 assets, a per-call hosted endpoint (fal, Replicate, the vendor API) is cheaper and faster than standing up a GPU. Rent a GPU (RunPod, Modal) for batches of hundreds or for models with no hosted endpoint.
- **Pin versions and log everything.** For every generated asset, record the model ID and version, prompt, reference images, seed (if any), tool settings, and cost. Write it to a `manifest.json` (or `.csv`) next to the assets. This makes assets reproducible and gives evidence of provenance if licensing is questioned.
- **Lock style and identity up front.** Write one style block and one subject block per character or asset family. Reuse them verbatim, together with the same reference images, for every asset in the set.
- **Keep source files.** Keep the original generated image, the raw model output (e.g. untouched GLB), and the cleaned asset. Never overwrite the raw output.
- **Prices and versions move fast.** Every price and version here carries the date it was researched. If a date is more than ~3 months old, re-check the vendor page before you quote a budget, and update this repo.

## Contributing back

This repo improves only if projects feed back what they learn. At the end of a session:

- If a workflow step failed, needed a workaround, or a tool changed, edit the workflow file and add a dated note.
- If you measured real cost or time per asset, add it to the "Measured results" section of that workflow, with the date and project name.
- Put new raw research in `research/<YYYY-MM-DD>/` and move only conclusions into `workflows/` or `reference/`.
- Mark anything you could not verify **(unverified)**.
