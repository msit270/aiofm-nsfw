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
