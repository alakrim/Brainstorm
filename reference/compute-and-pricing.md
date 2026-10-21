# Compute and pricing

*Prices fetched 2026-10-21 from vendor pricing pages (RunPod page dated 2026-10-08). They change often. Re-check before quoting a budget.*

## Decision rule

| Job | Use | Why |
|---|---|---|
| A named model with a hosted endpoint, < ~50 assets | **fal** (or Replicate) per-call API | No setup, pay per output, no idle billing |
| Custom Python (Blender, depth, matting, batch scripts) on GPU | **Modal** | Per-second billing, scale to zero, Python-native; $30/month free credits on Starter |
| Batches of hundreds of assets on one model | **RunPod pod** (L40S/A100/4090), destroyed after the batch | Cheapest $/hour; keep the model warm for the whole queue |
| Cheapest possible, can tolerate interruption | Vast.ai interruptible + checkpointing | 50%+ cheaper; hosts vary in reliability |
| CPU work (Blender cleanup, rendering, pixel snapping, vectorizing, icons) | The agent's own container / CI | Free; no GPU needed |

## Hosted per-call prices (asset-relevant)

| Task | Endpoint | Price |
|---|---|---|
| Image gen | Meta Muse Image (fal) | $0.01/image |
| Image gen | OpenAI `gpt-image-2.5-sunburst` / `-flare` | $30/1M image output tokens (~$0.01–0.21/image); Batch half |
| Image → 3D | fal `fal-ai/trellis-2` | $0.25 / $0.30 / $0.35 (512/1024/1536p) |
| Image → 3D | fal `fal-ai/trellis` (v1) | $0.02 |
| Image → 3D | fal `fal-ai/hunyuan3d-v3/image-to-3d` | $0.225–0.525 |
| Image → 3D | fal Meshy 6 | $0.80 |
| Image → 3D | Tripo API H3.1 | 20–50 credits (~$0.20–0.50); quad +5 |
| Image → 3D | Meshy API | 30 credits textured (~$0.60 derived) |
| Auto-rig | Tripo / Meshy | 25 credits (~$0.25) / 5 credits |
| Animation clip | Tripo / Meshy | 10 credits / 3 credits |
| Depth | Replicate Depth Anything 3 Mono | ~$0.001 |
| Background removal | Replicate | ~$0.0005 |
| Vectorize | Recraft | $0.01 |

## GPU $/hour (on-demand)

| GPU (VRAM) | RunPod pod secure / community | RunPod serverless | Modal | Replicate | Lambda |
|---|---|---|---|---|---|
| RTX 4090 (24 GB) | $0.89 / $0.34 | $1.10 | — | — | — |
| L4 (24 GB) | $0.59 / $0.44 | $0.69 | $0.80 | — | — |
| L40S (48 GB) | $1.09 / $0.79 | $1.75 | $1.95 | $3.51 | — |
| A100 80 GB | $1.79 / $1.19 | $2.72 | $2.50 | $5.04 | — |
| H100 80 GB | $2.89–3.99 / $1.99–2.69 | $4.79 | $3.95 | $5.49 | $3.29–4.29 |

VRAM needs: TRELLIS.2 ≥24 GB (L40S, A100, 4090 borderline); Hunyuan3D 2.1 shape+texture 29 GB; UniRig 8 GB; SkinTokens 14 GB; BiRefNet 3.5 GB; Depth Anything 3 Small/Base < 4 GB.

## Billing gotchas

- **fal custom apps / serverless** bill setup **and idle** time (`keep_alive` default 60 s). fal's **hosted model endpoints** bill per output, which is what you usually want.
- **Modal** bills from container start through model load. Pre-bake weights into the image and use `.map()` for batches.
- **RunPod pods** bill until destroyed. Agents must destroy pods in a `finally` block. A forgotten A100 costs ~$43/day.
- **Replicate public models:** setup/idle free; private deployments bill online time.
- **Cold starts:** loading a 4B model takes tens of seconds to minutes. Never do one asset per cold start in a batch.

## Agent setup cheatsheet

| Platform | Install | Auth env var |
|---|---|---|
| fal | `pip install fal-client` | `FAL_KEY` |
| Replicate | `pip install replicate` | `REPLICATE_API_TOKEN` |
| Modal | `pip install modal && modal setup` | `MODAL_TOKEN_ID` / `MODAL_TOKEN_SECRET` |
| RunPod | `runpodctl config --apiKey <key>` | `RUNPOD_API_KEY` |
| OpenAI | `pip install openai` | `OPENAI_API_KEY` |
| Tripo | REST (`developers.tripo3d.com`) | API key header |
| Meshy | REST (`docs.meshy.ai`) | Bearer token |

fal example (image → 3D):

```python
import fal_client
url = fal_client.upload_file("cutout/crate.png")
result = fal_client.subscribe("fal-ai/trellis-2", arguments={"image_url": url})
print(result)  # contains a GLB URL (field name per the endpoint's API schema)
```

Check each endpoint's API tab on fal for exact argument and output field names before scripting.

## Budget examples

| Project | Assets | Pipeline | Estimate |
|---|---|---|---|
| Small mobile game | 40 props, 6 rigged characters, 30 icons/UI | fal TRELLIS.2 + Tripo rig/anim + Muse/Sunburst | ~40×$0.60 + 6×$1.10 + images ≈ **$35–45** |
| Mid-size isometric game | 300 props, 20 characters pre-rendered to 8-dir sprites | Self-hosted TRELLIS.2 batch + Tripo rigging + CPU rendering | ~$15 GPU + 20×$1.10 + images ≈ **$50–80** |

Image generation, retries and human review time are the real cost drivers. Track `$/accepted asset`, not `$/call`.
