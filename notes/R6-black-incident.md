# R6 black-frame incident (2026-08-08, boot1 of :19188 work server)

Sequence (results/run6/*/meta.json mtimes, same boot, arms serialized,
/free unload_models+free_memory before every arm):

healthy: R_FB, R_FB(cache), R_PT, R_CU, R_COZY, P_FB, P_PT, P_CU, P_COZY
BLACK:   R_str08_FB      <- FIRST black; LoRA strength 0.8 arm
healthy: P_cnneg_FB      <- pc graph, INTERLEAVED, clean
BLACK:   R_pcneg_FB      (ref graph, strength 1.0)
BLACK:   R_FB_canary     (EXACT graph that rendered healthy 17 min earlier)

All four ref-graph PNGs black in each black arm (stage1 224x288 included
-> the die happens at/before the first sampler, not in upscaling).
Server flags: --disable-xformers --disable-async-offload (run-5 daily
mitigation flags active — did NOT prevent it).

Data points vs the run-5 dossier (notes/D-blackrender-verdict.md):
1. SECOND independent occurrence of the exact run-5 phase-2 signature:
   a strength-0.8 Z arm black-frames, subsequent Z renders on the same
   family stay black ("NaN poisoning"). Run-5's D matrix called the
   str08 theory non-reproduced (40/40 healthy); tonight it recurred on
   the FIRST str08 render of the session.
2. NEW datapoint the run-5 dossier did not have: pc-graph Z renders
   INTERLEAVED between black ref-graph renders stayed clean (P_cnneg_FB
   healthy between R_str08 and R_pcneg). The two graph families share
   the UNET file but differ in TE (GGUF heretic vs safetensors CPU),
   VAE (UltraFlux vs ae) and sampler stack (RES4LYF vs core). If this
   is state poisoning, it lives in something per-model-object/per-node
   -family (RES4LYF sampler state? GGUF TE? UltraFlux VAE decode?),
   NOT in global CUDA context — or it is time-clustered coincidence
   again (3 consecutive ref arms in a 4-min window).
3. "Per-graph deterministic within a boot" is REFUTED as stated:
   R_FB healthy and R_FB_canary black are the same graph in one boot.
   The run-5 formulation needs weakening to "sticky after first
   occurrence within a boot (per family?)".
Mitigation applied: fresh boot (boot2), re-render with canary brackets
(batch1b), black-check every arm — per run-5 protocol.

## CORRECTION (same session, retro-scan with fixed detector)

The original blackcheck threshold (mean<2 AND std<2) MISSED one event:
P_COZY (pc graph, cozy prompt, boot1) is black too — mean 3.01 (the pc
chain's ESRGAN/USDU/colormatch post-processing lifts a black base frame
slightly off zero). Detector now mean<8 & std<6; full retro-scan of all
arms confirms the complete black list is: P_COZY, R_str08_FB(+_b2),
R_pcneg_FB(+_b2), R_FB_canary(+_b2).

Corrected boot1 timeline: the FIRST black was P_COZY (pc family),
BEFORE R_str08. P_cnneg_FB (pc family) was healthy again after it.
So boot1 saw blacks in BOTH families; the claim "pc arms immune" is
WRONG. What remains reproduced 2/2 boots: R_FB + P_FB healthy ->
str08 black on its first render -> ALL subsequent ref-family arms
black including the exact graph healthy earlier the same boot.
P_COZY (boot1 only so far) is a separate event pending re-render.

## ISOLATION COMPLETE (boots 4-8) — deterministic repro recipe found

Probe results (every arm black-checked; all evidence results/run6/):
- boot4: P_COZY re-render HEALTHY (boot1 P_COZY black = sporadic
  run-5-class die, 1/2 boots, NOT part of the pattern below).
- boot5: str08 FIRST render: HEALTHY. R_FB@1.0 after it: HEALTHY.
- boot6: stockvae first: HEALTHY; stockTE second: HEALTHY; R_FB third:
  HEALTHY (falsifies the pure composition-change hypothesis).
- boot7: stockTE first: HEALTHY (bit-identical to boot6's second-position
  render — order does not change bits when healthy).
- boot8 (decisive): R_FB@1.0 -> str08 -> R_FB, NO pc-family render in
  the boot: ALL HEALTHY.

RULE (fits all 8 boots, no counterexample):
a ref-family render black-frames  iff
  (a) an earlier ref-family render with a DIFFERENT model composition
      (LoRA strength, VAE file, or TE file) ran this boot, AND
  (b) >=1 pc-family render (different TE/VAE stack) ran BETWEEN them.
After the first black, EVERY later ref-family render that boot is black
(sticky, 6/6) regardless of composition. Prompt/negative text changes
never trigger (R_pcneg healthy when unpoisoned, boot3). pc-family
renders are never triggered by this mechanism.

Reproduced instances: str08-after-P 2/2 boots; stockvae-after-P 1/1;
plus P_hereticTE_FB (pc graph given the ref's GGUF TE) rendered a
healthy frame with a BLACK FACE — the FaceDetailer sub-render died
(same class as run-5's "black-faced PT arm").

MECHANISM (inference, not proven): the common component in every
triggered black is the GGUF text encoder (ComfyUI-GGUF CLIPLoaderGGUF,
qwen heretic q8). Interleaved pc renders force its eviction (/free is
called before every arm); the reload+re-patch path then yields NaN/zero
conditioning -> black from the FIRST sampler step (stage1 224x288 is
already black in every event), poisoned loader cache -> sticky until
restart. Explains: pc immunity (safetensors TE), text-change safety
(no reload), P_hereticTE face-black (GGUF TE + LoRA-stack clip patch),
boots 5-8 health (no eviction between ref arms).
NOT tested: encode-only probe; ComfyUI-GGUF version bisect; whether
--disable-async-offload matters here. -> root-cause session items.

OPERATIONAL RULE for this pod until fixed: never interleave the two
graph families in one boot when the ref-family composition will change;
one composition per boot is always safe; re-boot clears it.


## Final consolidated black list (verifier-reconciled, all 8 boots)

12 arms, nothing else: P_COZY (pc family, sporadic, healthy on re-render)
+ 11 ref-family hard zeros: R_str08_FB, R_str08_FB_b2, R_str08_FB_b3,
R_pcneg_FB, R_pcneg_FB_b2, R_FB_canary, R_FB_canary_b2, R_FB_canary2_b3,
R_stockvae_FB, R_stockTE_FB, R_FB_after08_b3.
Triggers: R_str08_FB (b1), R_str08_FB_b2, R_stockvae_FB. Sticky-after: 6.
(The 8-arm list in the CORRECTION above was chronological, pre-boot-3.)
Reader warning: meta.json `ok` is true even for black arms — blackness
lives only in the `black` field / retro-scan. Early-arm metas (boot1)
predate the corrected threshold; results/run6/scores.json rows with
cos=None mark the same arms. P_hereticTE2_FB (confetti, mean 120) is
correctly NOT black — corrupted, not zeroed.
