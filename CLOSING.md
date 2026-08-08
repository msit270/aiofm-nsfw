# Closing note — personal build, 2026-08-08

Two days: run 5 (config derivation + pack), run 6 (reference diff +
black-frame repro), and today's owner session (AB_CU rounds 1–3 + landing).

## What's in the build (pack v4, sha256 a122699c…)

- `OFMTech_NSFW_Personal.json` (member sha 752030f7…): flat, character-
  neutral, Z-native end to end. Base **8 steps / cfg 1.0** (the D verdict —
  close-up picked by eye, FB +.040, PT flat), 617 tiled refine denoise .25,
  euler_ancestral face pass at denoise .50, neutral-prompt 768 hands, eyes
  pass, mouth stage deleted, shift dial exposed at 3.0.
- The close-up defect is fixed at the DEFAULTS level — close-ups no longer
  need a manual widget change. The old 30/cfg2 base survives in docs as a
  body-leaning alternative (denser freckling, blotchy on CU).
- Vendored luna + lunaskye, LUSTIFY V9 fallback slot, one-line install via
  the live sellable gist + `AIOFM_PACK_URL`.
- Docs synced to shipped values: CONFIG-SPEC, README-PERSONAL, CHECKLIST.
- Pod launch carries the black-frame mitigation
  (`--disable-async-offload` + `CUBLAS_WORKSPACE_CONFIG=:4096:8`),
  persisted in /etc/environment; not a proven cure — re-render on black.

## Still open, honestly

- **Negatives are inert at cfg 1.0** (mechanism confirmed from ComfyUI
  source). Any negative steering — including run-6's +.020 anti-AI
  negative — needs base cfg ≥1.5, which reopens close-up blotch risk.
  Documented tension, not resolved.
- **Black-frame root cause** remains OPEN. This session: 15/15 pc-family
  arms clean under the mitigation flags. Run-6's deterministic repro is
  ref-family + composition-change + family-interleave; pc-only daily use
  should rarely see it. Re-render on black still clears it.
- **den .45** is dead on close-up (identity moves off the Luna family;
  measured, attributed) but measured +.028–.049 on FB at 30-step bases.
  No per-comp denoise preset was built — simplicity won. If body texture
  ever disappoints, that's the first widget to revisit (body only).
- **S18** (euler_ancestral tiled): likeness-flat on CU, old metric edge
  was FB-band; never applied. Still just sheeted.
- **Generalisation beyond Luna is UNPROVEN** (single-LoRA pod). The
  checklist is the mitigation.
- Run-6 reference adoptables not landed: shift ladder 6/7 (+.023),
  anti-AI negative (+.020, needs cfg>1), and the pyramid-base hybrid.

## If you come back to it, in order

1. **Live on D for a week of real close-ups.** Collect rejects; they'll
   say whether CU needs a texture pass (arm F, 30/1.5, is the standing
   alternative — its sheet is already rendered).
2. **The pyramid-base hybrid** — run 6's real finding: the reference wins
   likeness architecturally (full-frame LoRA-active regeneration at every
   scale, +.07–.08 cos class). Biggest measured headroom of anything left.
3. **V10/Krea2 session** (runbook ready): core ≥0.26 + torch 2.10 —
   2.10 has the cuBLAS thread-safety fix, so re-run the black-frame
   matrix there; the mitigation may retire.
4. **Retrain luna on Z-Image base** — unlocks real negatives and base
   diversity; lunaskye is the weak link if SDXL ever returns.

Evidence for everything above: `results/ab_cu/` (15 arms, gated graphs,
scores, sheets), `notes/CU-base-defect.md`, `results/run5/PACK.txt`
lineage, REPORT-RUN5/RUN6. All on GitHub (`personal-max`).
