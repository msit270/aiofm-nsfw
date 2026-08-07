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

## G-batch closeout (all arms, canaries bit-identical, zero black frames)

- **Negative liveness at cfg 2: PROVEN behaviourally** — editing ONLY the
  negative string changed 76.2% of pixels (>8 levels) on the deterministic
  pipeline. Caveat that matters for use: a negative cannot override a
  DIRECT positive conflict ("black silk slip dress" in the positive kept
  the dress black against "black dress" in the negative). Negatives steer
  everything the positive doesn't nail down.
- **S4 retest on the shipping graph**: res_multistep+simple on the face
  pass = cos .776, faceHF 10.28, f-lap 641 vs PC1 euler_ancestral's 9.73 /
  549. On the ship arch the baseline face was SOFT and rms added welcome
  freckling (your S4 verdict); on PC the base already carries texture and
  rms stacks more. METRIC vs CONSTRAINT-2 tension flagged: my judgement is
  euler_ancestral for the default; S11 sheet has both tiles — your call.
- PC-H (literal hybrid, SDXL face treatment on Z-30 base): cos .723,
  faceHF 8.23 — the softest face of the family; costs SDXL residency
  (~7 GB + its load time) and re-imports the SDXL identity pull.
- den 0.35 vs 0.50 on PC: .761/9.79 vs .799/9.73 — 0.50 keeps identity
  AND softness (the higher repaint replaces 30-step crunch with
  euler_ancestral's cleaner rendering).

## CLOSE-UP REGIME FINDING (constraint-2 failure on CU, 2026-08-08 ~00:0x)

G_PC1_CU (base 30/cfg2): the face texture goes blotchy/crusty at close-up —
large raised-looking patches across forehead/cheeks/chin; reads PROCESSED
(MY JUDGEMENT), cos drops to 0.658. The same config is clean on FB (0.799)
and PT (0.740, photographic-read: good directional window light, natural
skin — MY JUDGEMENT; verifier flagged these lines missing, added here).
Mechanism (consistent with trap #11 + F research): on close-ups the face is
huge, the detail passes sample it at native resolution, and the 30-step
cfg-2 base's dense texture compounds through the chain — the old
"steps-30 crust" regime returns, composition-gated.
Consequence: base 30/cfg2 (the S3 pick) is COMPOSITION-SENSITIVE, not just
character-specific. Candidate resolutions, pending batch I's cfg-1.5 arm:
(a) default 8/cfg1 with 30/cfg2 as the documented full-body/texture option;
(b) middle setting (cfg 1.5) if I_cfg15 holds FB texture without CU crust.
S12 sheet is the decision artifact. Verifier-3's other fixes adopted: the
"fast 30-step bars" exclusion rationale was wrong (they are healthy
detailer-crop bars — the 11-12 s base figure itself stands); negproof's
negative addition was ", black dress, black clothing, dark fabric" and its
graph also drops the 8 tap sinks (verified inert).
