AIOFM NSFW — PERSONAL BUILD
===========================

This is the owner's personal build. It is NOT the sellable pack and must
never be published to buyers. Differences from the sellable:

1. Workflow: OFMTech_NSFW_Personal.json — a flat (no-subgraph) graph,
   CHARACTER-NEUTRAL (pick your LoRA in the Lora Loader Stack widget; type
   your trigger + face prompt where the placeholders say so). Z-Image
   Turbo drives the base AND every sampling pass. The SDXL stages are not
   in the render path. The mouth stage is DELETED (measured: it only ever
   fired where it was useless and was blocked by its own area ceiling on
   open-mouth close-ups). Hands use a neutralized prompt + 768 sampling
   (measured: the old "detailed fingers/fingernails" prompt caused the
   overbaked look). See CONFIG-SPEC.txt for every setting's
   general-vs-specific mark and CHARACTER-SWAP-CHECKLIST.txt before
   loading a new character.
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
- LIGHT IS GENERATED AT THE BASE, not recoverable downstream (measured).
  The two sentence patterns that moved it most, at intact identity:
  film-stock: "shot on Kodak Portra 400, gentle flash falloff, candid
  unstaged documentary feel" (best single frame of the run), or
  direction: "lit by <source> from the <side>, soft directional light,
  deep natural shadows, gentle highlight rolloff". One such sentence per
  prompt; stacking dilutes.
- The base ModelSamplingAuraFlow "shift" dial ships at 3.0 (the model
  default). 4.5-6.0 = wider tonal range/deeper shadow masses (S15 sheet).
- Base 30 steps / cfg 2 is the shipped default (your S3 pick). KNOWN
  CAVEAT: on close-up face-filling compositions it can go blotchy
  (S12) — drop to 8 steps / cfg 1 for close-ups, or lower cfg to 1.5.
- The character LoRA overrides prompted hair colour/style; describing the
  real hair ("long straight blonde hair with dark roots, curtain bangs")
  helps the base compose consistently with what the LoRA will render.
- Detail passes run cfg 1 / 8 steps; raising cfg on the DETAIL passes is
  wrong (guidance-distilled). Only the BASE runs cfg 2 (negatives live).
- LoRA strength ships 1.0 (range 0.7-1.0).
- KNOWN ISSUE — intermittent black frames/faces (~5% on the tuning pod,
  time-clustered; did NOT reproduce in a 40-probe controlled replay, so
  the cause is environmental and OPEN — full story in the run-5 report).
  Recommended daily launch (mechanism-targeted, compatibility-proven,
  NOT a proven cure):
    CUBLAS_WORKSPACE_CONFIG=:4096:8 python main.py --disable-async-offload
  If a render comes back black anyway: restart ComfyUI and re-render —
  that cleared every occurrence. Do NOT use --force-fp32 without also
  passing --use-pytorch-cross-attention (xformers has no fp32 kernel).
