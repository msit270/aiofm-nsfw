# Phase-4 fresh-context verification — A17 (+A18 where touched)

Verifier round 3, 2026-08-08. All re-derivation independent: own graph walker,
own tqdm parser, own cv2 pixel diff (/workspace/run5/venv). Nothing rendered.

## 1. Both readings rendered — VERIFIED

- G/G_PC1_{FB,PT,CU} and G/G_PCH_FB all have history.json with
  status success / completed=True / no execution_error message.
- Graph walk (upstream from final SaveImage `505`):
  - **G_PCH_FB**: `619:607` (FaceDetailerPipe, the SDXL face pass) IS
    reachable from 505 — chain 619:596 (VAEDecode of SDXL refine 619:600)
    → 619:607 → 619:597 VAEEncode → downstream. Also live: SDXL refine
    619:600 (KSamplerAdvanced lcm, steps 66→70 = 4 steps), SDXL checkpoint
    619:613, SDXL-fed 587:92 hands and 587:98 USDU (via 587:97 LoraLoader).
    Base is ZB_k (Z, 30 steps / cfg 2, 896x1152); the OLD SDXL 40-step base
    619:592 is NOT reachable from 505 (it feeds only tap T01_base591).
  - **G_PC1_FB/PT/CU**: `619:607` present but unreachable from 505 AND from
    every tap — fully dead. Live sampler set: ZB_k + Z-family detailers/USDU
    (620:114, 620:165, 622:406, 619:617, 587:92, 587:98) only.

## 2. 30-vs-8-step base cost — NUMBER VERIFIED; rationale in MD corrected

Own parser on /workspace/run5/server_19188.log: 77 `got prompt` markers (one
embedded mid-tqdm-line at log line 1845 — naive line-splitting mis-segments;
corrected). Segments matched to arms by exact `Prompt executed in X seconds`
== meta.json exec_s.

- Base bars (first completed bar of each segment whose base ran):
  G_PC1_FB 30/30 [00:11, 2.50it/s]; PT [00:12, 2.47]; CU [00:12, 2.25];
  den035 [00:12, 2.22]; negproof [00:12, 2.33]. → **"11-12 s" verified.**
- 8-step/cfg1 side: canaryG / canaryG2 ARE the 8-step cfg-1 Z base at the
  same 896x1152: 8/8 [00:01, 5.02 / 4.94 it/s] ≈ **1.6 s**. MD quotes
  "~2 s" — slight overstatement of the fast side; delta 12−1.6 ≈ +10.4 s
  ≈ +7% of ~150 s, so the "+10 s / +7%" conclusion stands.
- Per-step rate 2.5 it/s (cfg 2) vs 5.0 it/s (cfg 1) = exactly the 2×
  model-call cost of live negatives — consistent with the mechanism claim.
- **MD error (does not change the number)**: "the fast '30-step' bars in the
  log are the black-frame failures, which die early" is FALSE. Every fast
  30/30 bar (1-2 s @ 11-19 it/s) maps by exec-time to a healthy `ok` arm
  (A0 itself has four; B_mouth05, D_sdxlfix, E_v9fix, G_PCH etc.) — they are
  small detailer-crop bars. Base-only probe arms (zbref_P_12345, exec 15.7 s,
  ok) carry the SLOW 11-12 s bars. The slow-bar = base identification is
  correct (by first-bar position), but the stated exclusion rationale is
  misattributed. rms/PCH show no base bar (base cached from the previous FB
  arm); den035 re-ran the base because CU executed in between (single-entry
  node cache) — all consistent.

## 3. Negative-liveness — VERIFIED both ways (one scope nit)

- Pixel recompute (cv2, int16, per-pixel max-channel |diff| > 8 levels):
  **76.2%** on G_PC1_FB vs G_PC_negproof_FB finals (3456x2688). Matches the
  claim exactly. (Per-channel counting would give 66.5% — the published
  number is the max-channel reading.)
- Graph diff: among common nodes, ONLY 483.prompt_batch_data
  negative_prompt and 505 SaveImage filename_prefix differ. **Nit:** the
  negproof graph also OMITS the 8 TAP SaveImage sink nodes present in
  PC1_FB; sinks are consumed by nothing (verified), so attribution of the
  pixel delta to the negative stands, but "differ only in negative+prefix"
  is not literally true at file level. The actual negative addition is
  "black dress, black clothing, dark fabric" — MD quotes only the first two
  terms.
- Mechanism: /workspace/ComfyUI/comfy/samplers.py line 370 is exactly
  `if math.isclose(cond_scale, 1.0) and model_options.get("disable_cfg1_optimization", False) == False:`
  → uncond dropped only at cfg 1. MD's "samplers.py:370" citation is exact.
- Determinism bracket: batchG.log `[canaryG] max_abs_diff=0` (line 2) and
  `[canaryG2] max_abs_diff=0` (line 11). VERIFIED.

## 4. Metric rows — ALL VERIFIED (likeness_scores.json / tap_metrics.json)

| arm | cos claimed/found | faceHF claimed/found | other |
|---|---|---|---|
| G_PC1_FB | .799 / .7987 | 9.73 / 9.732 | bodyHF 9.60/9.598, f-lap 549/548.5 |
| G_PC_den035_FB | .761 / .7607 | 9.79 / 9.789 | |
| G_PC_rms_FB | .776 / .7763 | 10.28 / 10.279 | f-lap 641/641.5 |
| G_PCH_FB | .723 / .7233 | 8.23 / 8.234 | |
| D_lunaz_FB (ref) | .733 / .7327 | 10.35 / 10.35 | bodyHF 9.66, f-lap 756 ✓ |
| C_zusdu617 (ref) | .674 / .6744 | 7.24 / 7.24 | bodyHF 6.73, f-lap 116 ✓ |

"PC1 0.799 is the highest full-pipeline number of the run" — verified by
ranking every HasMetadata final in likeness_scores.json (next: rms .7763).

## 5. A18 spot-check (where touched by this MD)

- Judgement marking: table column is literally "photographic read
  (MY JUDGEMENT)" — marked. ✓
- S4 tension: "METRIC vs CONSTRAINT-2 tension flagged: my judgement is
  euler_ancestral for the default; S11 sheet has both tiles — your call"
  — explicit. ✓ (SHEETS/S11_reconciliation_faces.png exists.)
- **Gap**: G_PC1_PT and G_PC1_CU carry NO photographic-read line anywhere
  ("photographic read" greps only to ACCEPTANCE.md and this MD; per-arm
  meta.json has none). den035/rms/PCH get reads only via closeout bullets.
  A18's "every rendered arm" is not met for PT/CU.

## Verdict

**ISSUES (minor — no measured claim overturned).**
1. MD's black-frame explanation of fast 30/30 bars is factually wrong
   (they are healthy detailer-crop bars); the 11-12 s base figure itself is
   correct and independently re-derived.
2. "~2 s" for the 8-step base is measured 1.6 s (canary bars) — the +10 s /
   +7% conclusion survives.
3. negproof pair also drops the 8 tap sinks (inert, verified) and the MD
   under-quotes the negative addition (omits ", dark fabric").
4. A18 gap: no photographic-read line for G_PC1_PT / G_PC1_CU.

A17's substantive requirements — both readings rendered with the claimed
topology, base cost from sampler log lines, negative-liveness proven by
mechanism line AND behavioural arm — are all MET.
