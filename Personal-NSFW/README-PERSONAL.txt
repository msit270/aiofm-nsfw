AIOFM NSFW — PERSONAL BUILD
===========================

This is the owner's personal build. It is NOT the sellable pack and must
never be published to buyers. Differences from the sellable:

1. Workflow: OFMTech_NSFW_Personal.json — a flat (no-subgraph) graph.
   The Z-Image Turbo model + the "luna" character LoRA drive the base
   composition AND every sampling pass (base, tiled refine, polish upscale,
   hands, face, mouth, eyes). The SDXL stages of the sellable pipeline are
   not in the render path.
2. Base checkpoint slot: the installer fetches LUSTIFY ZENITH (V9) from
   Civitai (version 3045803) with your API key. The primary workflow does
   not use it; it is installed for SDXL fallback experiments. The slot is
   swappable: change LUSTIFY_VERSION_ID / LUSTIFY_SHA256 / LUSTIFY_BYTES /
   LUSTIFY_FILE at the top of aiofm_setup.sh (or override them as env vars)
   and re-run the installer.
3. Character LoRAs luna.safetensors + lunaskye.safetensors are VENDORED in
   this pack (loras/) and installed to models/loras — they are private and
   never fetched from any external service.

Install (one line, same bootstrap as the sellable, different pack URL):

  AIOFM_PACK_URL=<your-personal-pack-url> bash <(wget -qO- <gist-raw-url>)

Keys expected on the pod BEFORE install, exactly like the sellable:
  /workspace/.hf_token        (HuggingFace read token — model pull)
  /workspace/.civitai_token   (Civitai API key — V9 fetch)

Prompting notes (measured this run, results/run5/):
- The character LoRA overrides prompted hair colour/style; describing the
  real hair ("long straight blonde hair with dark roots, curtain bangs")
  helps the base compose consistently with what the LoRA will render.
- Turbo runs at cfg 1 / 8 steps / res_multistep / simple everywhere.
  Raising cfg on Z passes is wrong (guidance-distilled); the 30-step/cfg-2
  base variant is a denser-freckle taste option (see the sheets).
- LoRA strength stays 1.0. Strength 0.8 produced a black frame + server
  poisoning once this run (unexplained, n=1) — treat as unsafe.
