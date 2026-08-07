# Run 3 — DoD 5: the eye regression, resolved by experiment

**One line: `620:110 device=cpu` stays (7ce1539 NOT reverted); the dual-loader
idea is refuted by its own experiment; the eye cost is real, small on the full
graph, and inseparable from the fix — trade-off sheets delivered.**

## The experiment (all full-graph, guarded bytes, 16-token placeholder, cold, fixed seeds)

| arm | face/mouth encodes | eye encodes | eye-band vs DEFAULT (mean / max / >4-level px) |
|---|---|---|---|
| `R3_DEFAULT_16` | GPU | GPU | — (the pre-fix reference) |
| `R3_AB_guard_16` | **cpu** | **cpu** | 0.515 / 85 / 3.19 % |
| `R3_DUAL_16` | **cpu** | GPU | 0.515 / 85 / 3.19 % — **identical to the cpu row** |

`DUAL vs CPU` directly: mean 0.009, max 2 levels, 0.06 % of pixels — noise.
**Moving the eye-prompt encodes back to the GPU changed nothing.** The eye
difference between the fixed and unfixed configs therefore does NOT enter
through the eye-prompt conditioning; it enters through the eyes stage's INPUT
IMAGE — the face-pass output — which necessarily changes when the face encode
moves to cpu, because changing the face encode IS the fix. V-track's reading
("622:406 amplifies the tiny conditioning change") was half right: it
amplifies the tiny *input-image* change; the conditioning path is insensitive
here. No loader arrangement can keep the fix and the pre-fix eyes.

## The decision

Keep cpu. The alternatives, priced with this run's data:
- **Revert to default**: pristine eyes, but the black-face failure reopens at
  the common bands (30–32, 44–50, 60–96, 166 measured; the guard converts
  those crashes into loud degraded deliveries — a black-faced image with a
  warning is still not sellable output for an ordinary-length prompt).
- **Dual loader**: identical pixels to full-cpu plus an extra resident encoder
  and a subgraph edit. Strictly worse. Rejected; the ready patch
  (`tools/polish/apply_dualclip.py`) stays unapplied, kept only as the record.
- **Keep cpu**: bands closed (46/103/110 verified healthy again today at YOLO
  0.90 class), the silent eye-pass black-hole failure stays cured (V §9b), and
  the cost is the eye-band delta above.

## What the cost looks like today (full graph, not the probe)

Full-frame: 2.97 % of pixels differ at all; eye band: mean 0.5 levels, max 85,
3.2 % of eye-band pixels move more than 4 levels. Milder than V's probe-graph
figures (12.8 % / max 135) — the probe's frozen base amplified it.

Sheets, 1:1, labelled:
- `results/run3/sheets/R3_EYES_default_cpu_dual.png` — today's three rows.
- `results/crash/V/out/V_SHEET_EYES_face_sheet1of1.png` — the probe-graph
  worst case (catchlight crossing the pupil), kept for the owner's eye.

The owner can overrule by `git revert 7ce1539` (accepting the reopened bands)
— the guard and everything else in this run stands either way.
