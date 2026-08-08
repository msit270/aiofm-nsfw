# R6 — Structural diff: MarlAI reference vs pc_final (STEP 1)

Sources: reference/MarlAI_ImageGen_ZImage.json (sha 8cccce5b…, fully
traced in REF-PREFLIGHT.md) vs the shipped pc_final graph
(/workspace/run5/pc_final_api.json, 66 nodes, = pack member 2fd45381…;
luna-loaded variant results/run5/M2/M2_luna_*/api_graph.json).
Every claim below is read from those files; judgement lines marked (J).

## What is IDENTICAL

- Generator: zimage.safetensors — BYTE-IDENTICAL file on this pod
  (official Z-Image-Turbo bf16, hash-matched to Comfy-Org).
- TE family: Qwen (lumina2 type) — but different weights (below).
- Character LoRA slot: model-side LoRA into every sampling pass
  (ref #105 model-only; pc #116 rgthree stack model+clip — Z LoRAs
  carry no TE keys, so effectively model-only in both).
- One base composition pass + progressive enlargement with
  re-sampling; portrait 7:9 aspect both (896x1152 vs 112x144 start).
- ModelSamplingAuraFlow shift control present in both.
- Both deliver a single SaveImage frame.

## Pipeline shapes side by side

REF (MarlAI): 112x144 draft (euler_ancestral 9st cfg1 shift3, custom
exponential flow sigmas) -> latent x2 -> 224x288 ClownsharK 5st den0.7
CFG2 (perlin init, DetailBoost 1.2, bongmath, eta .52) -> decode ->
re-encode (UltraFlux VAE) -> +noise 0.3 -> IterativeLatentUpscale x3
(5 hops, euler/beta 9st den0.6 cfg1, shift 6) -> 672x864 -> latent to
896x1152 -> +noise 0.4 -> ClownsharK 9st den0.5 cfg1 shift7 DB1.4 ->
latent to 1344x1728 -> +noise 0.2 -> ClownsharK 9st den0.5 cfg1 shift7
DB1.2 -> decode -> SAVE 1344x1728.
7 model passes, ALL full-frame, ALL with the character LoRA, den
0.5-0.7 at every scale. No detectors, no crops, no composites, no
colormatch, no ESRGAN. 3 model files total (+VAE, TE).

PC_FINAL: 483 prompts -> base 896x1152 (res_multistep/simple 30st
CFG2 shift3, live short negative) -> decode -> NMKD 4x ESRGAN ->
x0.4 lanczos (=1434x1843) -> USDU tiled 1.25x den0.25 8st cfg1 ->
selector -> HANDS FaceDetailer (768, den .42, cycle 2, neutral prompt)
-> skin ESRGAN 1x + ImageBlend 1.0 -> USDU tiled 1.5x den0.08 2st cfg1
-> colormatch -> FACE FaceDetailer (1024, den .50, ea/kl_optimal) ->
colormatch -> EYES (MediaPipe mesh -> crop -> 1920 detailer den .42
euler/beta -> feathered composite) -> SAVE 2688x3456.
1 full-frame gen + 2 low-denoise tiled refines + 3 surgical region
passes. ~12 model files (detectors, SAM, 3 ESRGAN, etc.).

## The differences, ranked by how likely each explains a visible gap

1. MULTI-SCALE FULL-FRAME REGENERATION vs ONE-SHOT + SURGICAL REPAIR.
   The ref re-imagines the ENTIRE frame with the character LoRA active
   at den 0.5-0.7 at every scale up to final; light, skin, and identity
   are GENERATED at each resolution. pc_final generates once at
   896x1152, then protects it (den .25/.08 tiled; face/eyes/hands are
   crop-and-composite). Run 5 proved both halves of why this matters:
   likeness rises when Z+luna repaints (zusdu617 den .25 EARNS its
   keep; den085 scored best SDXL number), and "the chain flattens
   whatever the base gives" (light is generated, not recovered).
   The ref is built entirely out of the mechanism run 5 found to win.
   (J: most likely single explanation of "best output I've ever seen".)

2. VAE: UltraFlux fine-tune EVERYWHERE vs stock ae.safetensors.
   Every ref encode/decode runs through a 4K-trained Flux-VAE
   fine-tune whose whole pitch is recovered micro-texture/sharpness.
   pc_final ships stock ae. Cheapest possible adoption (one loader
   swap; latent-compatible: 16ch f8, scaling 0.3611/shift 0.1159).

3. NEGATIVE PROMPT CONTENT at the composition stage. Ref: ~600-term
   Chinese anti-AI-look block (anti plastic skin / influencer-face /
   studio-look / over-retouch) — live ONLY where cfg=2: the 224x288
   S1b pass that fixes composition + gross appearance. pc_final:
   "bad quality, worst quality, low quality, deformed, extra fingers,
   watermark, text" at its cfg-2 base. Run 5 proved negatives at cfg 2
   steer 76.2% of pixels — pc_final has the mechanism live and feeds
   it seven generic words. Directly adoptable as TEXT.
   (J: high-leverage for exactly the owner's "photographic beats
   detailed" taste; the block reads like that rule written out.)

4. RES4LYF SAMPLING MACHINERY: ClownsharKSampler_Beta with bongmath,
   eta 0.52, perlin initial noise, DetailBoost 1.2-1.4 (steps 1-3),
   beta57 scheduler; plus inter-stage latent noise injection
   (0.3/0.4/0.2). pc_final: plain res_multistep/simple + ea/kl_optimal.
   The ref actively re-seeds texture between scales and boosts detail
   inside the sampler. Adoptable only as a machinery import (pack now
   installed) — cannot be expressed as widget changes on pc nodes.

5. SHIFT LADDER 3 -> 6 -> 7 with resolution, vs constant 3.0.
   Ref raises AuraFlow shift as scale grows (higher shift = sigmas
   spend longer in structure/low-freq at the hi-res passes — run 5's
   own shift tiles measured the lighting/depth direction at 4.5/6).
   pc_final exposes one global dial at 3.0. Adoptable as per-stage
   shift on the two USDU model inputs (one extra MSAuraFlow node).

6. TEXT ENCODER WEIGHTS: abliterated "heretic" Qwen3-4B (q8 GGUF, GPU)
   vs stock qwen.safetensors (fp, CPU). Different conditioning vectors
   for identical text. Unknown visual direction; the heretic edit
   targets refusal behavior, not aesthetics — but it is 1 of only 4
   model files the ref uses, so it cannot be ruled out from the file.
   Adoptable (CLIPLoaderGGUF now installed).

7. LoRA STRENGTH 0.8 vs 1.0 (widget-level; A/B tiles both).

8. WHAT THE REF SIMPLY DOESN'T DO (do-not-credit list, step 4 input):
   no hands pass, no eyes pass, no mouth logic, no NSFW anatomy
   support, no colormatch, no ESRGAN sharpening, no selector/batching,
   final res 1344x1728 = 27% of pc_final's 2688x3456 pixel count
   (downscaled viewing hides smoothing; sheets must compare at
   matched scale AND native crops). Draft at 112x144 also means
   near-zero prompt-layout control fidelity at composition time.

9. Inert differences (noted, no impact expected): dead ae.safetensors
   loader in ref; bypassed ControlNet patch + safetensors TE; dead
   448x576 resize branch; landscape latent Set never Get; ref
   IterativeLatentUpscale temp previews; TE on CPU vs GPU.

## Adoption candidates in one line each (feeds PROPOSALS after A/B)
- A. Swap ae -> UltraFlux VAE in pc_final (1 widget).
- B. Replace the 7-word base negative with the anti-AI block (text).
- C. Per-stage shift ladder on the tiled refines (1 node + 2 links).
- D. Raise tiled-refine denoise toward 0.4-0.5 with noise injection
     (the ref's "regenerate, don't protect" move) — the S18/den085
     evidence already pointed this direction.
- E. RES4LYF samplers in base/face slots (machinery import).
- F. Heretic GGUF TE swap (1 loader).
