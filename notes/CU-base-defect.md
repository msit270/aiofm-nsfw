# STANDING DEFECT — shipped base is owner-rejected on close-ups

2026-08-08, first owner-eye session on the installed personal build.

## The finding

The owner looked at `results/ab_cu/AB_CU_sheet_face1to1.png` (arm A =
the live/shipped config, bit-identical to run-6 P_CU) and rejected it:

> "Arm A — the live config — looks terrible and overbaked, blotchy
> clustered speckle across the forehead and cheeks."

This is S12 (REPORT-RUN5: "close-up caveat on the 30/cfg2 base — goes
blotchy on face-filling comps"), but its status changes: run 5 shipped
30/cfg2 as the default with S12 as a documented caveat plus a manual
fallback (drop to 8/cfg1 on close-ups). The owner's verdict now is that
**close-ups are their primary composition** and the installed default
produces rejects there. A defaults-level fix is required regardless of
where the 617-denoise question lands.

## Evidence chain

- Arm A render: `results/ab_cu/A_base_CU/img_00001_.png` — base 30/cfg2,
  pixel-identical (max abs diff 0) to run-6 P_CU across boots/servers.
- Round-1 A/B (A vs den045 vs S18) is CONFOUNDED for close-up judgement:
  all three arms carried the 30/cfg2 base, so the dominant variable was
  the base defect, not the tested widget. Owner caught this; scores kept
  as instrument readings only.
- Round 2 (`tools/ab_cu2.py`, arms D-G) corrects the base first:
  {8/cfg1.0, 30/cfg1.5} x {den .25, .45} — 30/cfg1.5-on-CU is exactly
  the run-5 open item "the one untested arm that could dissolve S12".

## Round-2 verdict (owner, 2026-08-08)

Owner picked **D (base 8/cfg1.0, 617 den .25) as default candidate**,
gated on: (1) identity check on the sheet (D's composition drifts at the
same seed), (2) body regression check on FB/PT vs current PC1 — if D
regresses body, D becomes a CLOSE-UP PRESET, not the global default.
Round 3 (`tools/ab_cu3.py`, arms H–O) renders PC1 / D-base / F / G on
FB+PT. NOTHING is applied to the live workflow until the owner looks.

Owner's eye on round 2: D over E, "genuinely marginal". The .21 cos gap
between them was then attributed by measurement (below).

## The D/E .21 gap, attributed (2026-08-08)

- NOT framing: re-scored on the exact 1:1 sheet crops, the gap holds
  (D .752 vs E .546). Same detector variant (full@320), similar det.
- Same-image reframing moves cos only ±.02 (crop-vs-full
  self-consistency: A .921, D .979, E .943 — cos of the same face
  embedded from crop vs full frame).
- Mostly REAL facial-geometry change: cos(D,E)=.7735 — the two arms are
  as far from each other as two independent Luna reference renders
  (zref band .78–.83); E sits .55–.60 from EVERY Luna anchor
  (A .600, M2_luna_CU .596, centroid .550) while D sits .74–.76.
- Instrument spread at CU is real but bounded: B/C agree .8465 pairwise
  yet differ .07 to centroid → treat CU cos gaps under ~.07 as noise.
  .21 is 3x outside that.
- Mechanism (INFERENCE, unproven): at CU the face spans ~3 of 617's
  896x1152 tiles, so .45 per-tile repaint recomposes features with
  partial-face context; on FB the face fits in one tile — where .45
  helped (+.049, run 6). Eye-vs-instrument divergence explained:
  ArcFace reads geometry and tolerates texture; the owner's 1:1 read
  was predominantly texture. Both readings are true of different things.

## Round-3 result (body regression, instrument)

vs PC1 baselines (H_pc1_FB .7590 / I_pc1_PT .7469 — both reproduced
run-6 pc scores exactly):

  J D-base FB .7987 (+.040)   K D-base PT .7447 (−.002)
  L F FB      .7815 (+.023)   M F PT      .7237 (−.023)
  N G FB      .7869 (+.028)   O G PT      .6819 (−.065)

bodyHF flat across arms (9.35–10.10 vs PC1 9.62/9.50). On the
instrument D-base does NOT regress body. Prompt adherence and look are
the owner's call from AB_BODY_sheet_FB/PT.png. cfg-1.0 arms rendered
with the negative branch inert (see below); the FB/PT sheets are the
place that would show any adherence cost.

## Negative branch at cfg 1.0 (owner question, answered from source)

ComfyUI `comfy/samplers.py::sampling_function` (lines 369–375): when
`cond_scale` is (isclose to) 1.0 and `disable_cfg1_optimization` is
unset, `uncond_ = None` — the negative conditioning is never evaluated.
So under D's base the negative branch is INERT (and skipped for speed).
What depends on it today:

1. The shipped base negative ("bad quality … watermark, text") — run-5
   PROVEN live at cfg 2 (76.2% pixel steer from a negative-only edit).
   Under D it does nothing. This is the only place negatives were ever
   live in PC1: every detail pass already runs cfg 1 (guidance-
   distilled), so their negative inputs are already inert.
2. The run-6 adoptable "anti-AI negative" (+.020) requires a cfg>1
   base — unusable wherever the 8/cfg1 base runs.
3. README/CONFIG-SPEC text "negatives live on base at cfg 2" needs
   updating whichever way this lands.
4. F/G (cfg 1.5) keep the negative branch live — if the owner ends up
   preferring cfg 1.5 for body, negatives survive on body comps.

## Preset-switch design (build ONLY if owner picks preset over default)

One INT primitive titled `COMPOSITION PRESET  1=CLOSE-UP  2=BODY`
feeding Impact `ImpactSwitch` value selectors (Impact pack already in
the graph — node 56 is ImpactConditionalBranch):

- ZB_k.steps: switch{1: 8, 2: 30} (widget converted to input)
- ZB_k.cfg:   switch{1: 1.0, 2: 2.0 or owner's round-3 pick}
- 619:617.denoise: only if owner adopts different den per comp;
  currently .25 both sides — no switch needed.

Document both value sets in the workflow's MarkdownNote (node 67) +
CONFIG-SPEC, per composition, so no widget numbers need remembering.
