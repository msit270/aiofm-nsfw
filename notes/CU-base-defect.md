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

## Open

- Owner judges round 2; then decide the shipped CU regime (default
  change vs per-composition preset) and 617 denoise on top of it.
- If neither corrected base survives the owner's eye on close-ups, the
  base regime hunt reopens (steps/cfg grid, shift dial, sampler).
