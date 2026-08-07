# PC — the reconciled config (owner S1+S3 verdicts), 2026-08-08

## The owner's question answered

**zusdu617 is the OLD SDXL architecture** — full SDXL front half (40-step
base, TDD refine, SDXL face pass #607) with only the #617 tiled refine
swapped to the Z model. Its S1-winning face is born SDXL-smooth and only
gently Z-textured afterwards.

**Reconciling with the S3 pick (Z base 30/cfg2) is therefore an
architecture choice, not a settings merge.** Two readings built:

- **PC (primary, Z-native)**: Z base 30 steps / cfg 2 (S3 pick) with the
  soft-face essence replicated Z-natively — face pass stays euler_ancestral
  (Q3: the smoothest sampler) with denoise raised 0.35→0.50 so it repaints
  the 30-step base's crunch with the smoother rendering. Body-texture
  channel (Z-USDU 617/98, res_multistep) exactly as the S3 winner.
- **PC-H (literal, hybrid)**: Z-30 base + the retained SDXL face treatment
  (607 + SDXL refine + SDXL 98). Costs SDXL residency (~7 GB + load time);
  rendered as a comparison tile.

## The two direct questions

- **30-step cost**: base sampling 11-12 s at 30 steps/cfg 2 vs ~2 s at
  8/cfg 1 (from the arms' own tqdm sampler lines; the fast "30-step" bars
  in the log are the black-frame failures, which die early). On a ~150 s
  render that is ≈ +10 s / +7%.
- **cfg 2 negatives**: YES, live on the base pass. Mechanism:
  `comfy/samplers.py:370` skips the uncond only when cond_scale is
  exactly 1.0; at 2.0 the negative conditioning is evaluated every step.
  PC wires `ZB_neg` from the 483 negative string (was: empty). Visual
  proof: the G_PC_negproof arm (negative += "black dress, black clothing")
  — see its tile.

## First measurements (G batch, per-arm evidence results/run5/G/)

| arm | cos | faceHF | bodyHF | f-lap | photographic read (MY JUDGEMENT) |
|---|---|---|---|---|---|
| G_PC1_FB | 0.799 | 9.73 | 9.60 | 549 | face softer than LUNA-Z, close to zusdu617's class; body keeps S3 texture; reads photographed |
| (LUNA-Z FB, rejected S1) | 0.733 | 10.35 | 9.66 | 756 | too hard/processed (owner verdict) |
| (zusdu617, S1 pick) | 0.674 | 7.24 | 6.73 | 116 | soft, photographic, but plastic SDXL body |

PC1 likeness 0.799 is the highest full-pipeline number of the run — noted
as INSTRUMENT data (cos-to-Luna), not the goal (constraint 1).

## Character-generality marks for PC's deltas

- base steps 30 / cfg 2: **character-specific-leaning** — the dense
  freckle/texture gain was judged on Luna; on a clear-skinned character
  30/cfg2 may render noise. Documented default with 8/cfg1 as the marked
  fallback; swap-checklist item.
- live negatives at cfg 2: **character-general** (mechanism-level).
- face pass euler_ancestral + denoise 0.50: sampler choice
  **character-general** (smoothness class); denoise 0.50
  **character-specific-leaning** (how much base crunch to repaint depends
  on the character's skin; range 0.35-0.55, checklist item).
- Z-USDU 617/98 res_multistep + denoise 0.25/0.08: **character-general**
  (structure), texture intensity partly character-fed.
