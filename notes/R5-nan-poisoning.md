# run-5 lesson — NaN poisoning on a persistent server, second occurrence

2026-08-07 ~21:4x. On the persistent :19188 arm server, the arm
`zref_P_12345_str08` (Z-Image Turbo + luna at `LoraLoaderModelOnly`
strength **0.8** — the only 0.8-strength use all session) produced an
all-black frame in 4.1 s. Every Z-Image-UNET render queued after it on the
same process was corrupted:

- `B_fix610` (pipeline arm): SDXL taps T01–T08 healthy, then the Z face pass
  output blacked out the face region — exactly the run-3 crash-guard
  failure-state look. Final frame delivered with a black face.
- `zbref_P_12345` (z_image base + luna): psychedelic confetti garbage.

SDXL-family sampling on the same process stayed healthy throughout — the
corruption lived in the Z-Image side (model-patcher state, is the belief;
not re-proven).

**Containment:** drivers + server killed; poisoned outputs deleted; 13 rows
purged from likeness_scores.json; batch BC2 re-runs everything post-str08 on
a fresh process with two canaries (zref_P_12345 re-render must be
bit-identical to batch A's copy — checked in-script, batch aborts on
mismatch).

**Rules adopted for the rest of run 5:**
1. Any arm that produces a black/garbage frame → kill the server before
   rendering anything else; everything since the last canary is suspect.
2. LoRA strength 0.8 on the Z UNET is PARKED — reproduce only on a
   throwaway server, last, if at all. (Whether 0.8 itself was the trigger
   or a coincidence is UNPROVEN; n=1.)
3. Canary sentinel arms (cheap known-good render, bit-compare) bracket
   every multi-arm batch from now on. This is the same-window determinism
   guard doing double duty as a poisoning detector.

Run-4's Q-PROTOCOL used fresh-server-per-arm precisely to make this class
of failure impossible; the persistent-server speedup traded that away. The
canary-bracket keeps most of the speed and catches the failure class after
the fact instead of preventing it — acceptable for a personal run, not for
product gates.
