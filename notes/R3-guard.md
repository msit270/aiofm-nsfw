# Run 3 — the guard, and what the 103–120 "band" turned out to be

**One line: the eyes-stage no-face guard is applied and proven (deterministic
forced pair, fold-diff inert, byte-identical happy path pending in this run's
arms); and the "103–120 tokens still crashes" claim was probe-only — the full
88-node graph has never crashed there, including today.**

## The guard (commit 6de805d)

C-fix-design C1 + C1b, applied by `tools/guard/apply_guard.py`:
`622:660 ImpactIsNotEmptySEGS` → `622:661 ImpactConditionalBranch` (lazy), plus
`622:662 PreviewAny` titled "eyes ran? False = no face found, eye detail
SKIPPED" so a fired guard lands in `/history` outputs and on the canvas.

Proofs, all in `results/run3/guard/` and `results/run3/arms/`:
- P1 `integrity.py`: 0 problems.
- P2 real-browser `--no-submit`: exit 0; the `*`-typed output converted fine
  (C-fix-design §4.4's one risk did not materialize).
- P3 fold-diff vs the pre-guard browser export: **IDENTICAL, 0 differences**;
  unfolded delta exactly +660/+661/+662 and 419.image_b/505.images repointed.
- **The deterministic pair** (bistability-independent): `622:424.threshold`
  forced to 0.99 so the detector finds nothing on a healthy image —
  - `R3_FORCED_unguard` (pre-guard bytes): **error at 622:403**, the exact
    CRASH.md exception, cold, 232.3 s.
  - `R3_FORCED_guard` (guarded bytes): **success**, all 15 eyes-stage nodes
    absent from the ws `executing` stream, 660/661/662 present,
    `outputs["622:662"].text == ["False"]`, and the delivered PNG is
    **pixel-equal (max abs diff 0)** to the same-run 621:163 tap — the
    passthrough is byte-exact, verified within one run (not cross-run hashing).

## The bands, on the full graph, today (2026-08-07, :18188, all cold)

| arm | config | tokens | result |
|---|---|---|---|
| `R3_PC_head_103` | shipping (cpu) | 103 | **success, healthy** — eyes ran |
| `R3_PC_mid_46` | device default | 46 | **error 622:403** — the same-day positive control |
| `R3_GUARD_mid46` | guarded, device default | 46 | success, eyes ran (**the face pass came up healthy — bistable flip**, not guard rescue; the rescue proof is the forced pair) |

**Correction to HANDOFF's "103–120 still crashes, fix or no fix":** every arm
in that band (V track, 8/8 errors) was the **probe graph** — frozen base image,
SDXL half skipped. The full-graph arms V ran were only at 32/46 tokens. The
full graph at 103 tokens had never been run until `R3_PC_head_103`, and it
rendered clean. The probe's base image is not the full graph's base image, and
the bistability's inputs differ. What survives: the crash mechanism ("detector
finds nothing" → RuntimeError) is real on the full graph (R3_PC_mid_46 today),
and the guard closes the mechanism itself, at every prompt length, because it
guards the *detection result*, not a token count.

## The bistability moved again

`R3_PC_mid_46` errored (execution_start 00:48:29 UTC); `R3_GUARD_mid46` (same
config + guard, execution_start 01:01:25 UTC) rendered a healthy face — the coin flips arm to arm on the same process
now, not only process to process. Nothing that claims "X reproduces" or "X is
clean" is trustworthy here without a same-window control, and even then only
statistically. This is why the guard's proof is the FORCED pair.
