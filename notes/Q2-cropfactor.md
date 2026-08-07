# Q2 — bbox_crop_factor on `620:114` (the face pass): measured

**COMPLETE — 7 arms, all cold, all successful.** The owner recorded
`bbox_crop_factor` as UNTESTED. It is now tested on the CURRENT shipping bytes
(`results/run3/guard/api_guarded.json`, shipped value **1.5**), one variable
per arm, buyer-default everything else. **No shipped value was changed.
RECOMMEND-ONLY.**

**The one-line result:** the render is fully deterministic (the cf 1.5 repeat
is **bit-identical** to the baseline, `max_abs_diff 0` over 2688x3456x3), so
every pixel difference in the ladder is the crop factor and nothing else.
Crop factor buys **time**, superlinearly (face-pass sampling 1 s → 29 s across
cf 1.0 → 3.5), and moves the face **sideways, not up**: every value produces a
healthy, complete render whose face differs from the shipped one by a similar
amount (~35.6–36.4 dB over the face crop). By eye, cf 1.0 is the only value
that changes the character of the face (softer); 2.0–3.5 reshuffle
micro-detail within the baseline's family.

## Method

- Base graph: `r3.py::guarded_graph` byte-for-byte — `v_mk.norm` on the
  guarded conversion, `v_mk.set_loras` (luna/lunaskye), the 60-token buyer
  prompt into `620:106` (verbatim from
  `results/run3/fresh/fresh-buyer-api_graph.json`; `v_tok.count == 60`),
  `619:603.pick_list = "0"`, TAP163 tap. Fixed shipped seeds (`620:114`
  1111111, eyes 1111112). cfg stays 1 everywhere (settled).
- **One variable per arm**: `620:114.inputs.bbox_crop_factor`. Proven per arm
  by an input-wise graph diff against the baseline arm's graph, stored in each
  `meta.json` (`graph_diff_vs_baseline_arm`); the diff is `[]` for the two
  cf 1.5 arms and exactly one entry for the rest.
- Fresh ComfyUI process per arm on **19188** under an exclusive flock on
  `.gpu_lock`; server killed and reaped before release; 18188 never touched.
  Cold verified per arm: `execution_cached == []` in every history entry.
- Evidence per arm in `results/run4/quality/Q2/<arm>/`: submitted
  `api_graph.json`, verbatim `history.json`, delivered PNG (`n505__*`),
  mouth-stage tap (`nTAP163__*`), full `server.log`, `meta.json` with the
  sliced detector/detailer log lines. Sheets + metrics in
  `results/run4/quality/Q2/` (`q2cf_face_sheet1of1.png`,
  `q2cf_skin_sheet1of1.png`, `q2cf_eyeband_A_B_F.png`,
  `q2cf_overview_downscaled.png`, `q2_metrics.json`,
  `q2_sampler_breakdown.json`).

**n per cell: n=1 for cf 1.0/2.0/2.5/3.0/3.5; n=2 for cf 1.5** (baseline A
first, repeat G last, bracketing the session). A and G came out
**bit-identical**, so the same-window pixel noise floor is **zero** and n=1 on
the other cells suffices for pixel claims. For **total** exec time it does
not: A vs G differ by 4.2 s at identical work, and one arm (D) shows a
~40 s overhead excursion, so totals carry real wobble; the per-stage sampler
times below are the clean timing signal.

## The grid

Face detection handed to `620:114` was identical to 7 significant digits in
every arm — bbox (690.8927, 921.08136) on the 2688x3456 canvas (the Z-Image
stages run at full delivered resolution). `force_inpaint: true` clamps the
sampling scale to exactly 1.0 at cf ≥ 1.5 (trap #11 confirmed live), so cf
alone sets the sampled area; cf 1.0 is the only arm whose claw-back lands
above 1.0 (x1.1119 — the crop is genuinely resampled up).

| arm | cf | `Detailer: segment upscale` (620:114, verbatim crop/scale) | sampled | face sampler | all-sampler sum | exec s (total) | cold | lowvram |
|---|---|---|---|---|---|---|---|---|
| B_cf10 | 1.0 | crop (690, 921) x 1.1119 -> (767, 1024) | 0.79 MP | **1 s** | 64 s | 262.0 | yes | 0 |
| **A_cf15_baseline (SHIPS)** | **1.5** | crop (1036, 1381) x 1.0 (force inpaint) | 1.43 MP | **3 s** | 66 s | 266.6 | yes | 0 |
| G_cf15_repeat | 1.5 | identical to A | 1.43 MP | **3 s** | 70 s | 270.8 | yes | 0 |
| C_cf20 | 2.0 | crop (1381, 1842) x 1.0 (force inpaint) | 2.54 MP | **6 s** | 72 s | 273.5 | yes | 0 |
| D_cf25 | 2.5 | crop (1727, 2302) x 1.0 (force inpaint) | 3.98 MP | **11 s** | 77 s | 321.4* | yes | 0 |
| E_cf30 | 3.0 | crop (2072, 2763) x 1.0 (force inpaint) | 5.73 MP | **19 s** | 85 s | 299.9 | yes | 0 |
| F_cf35 | 3.5 | crop (2418, 3223) x 1.0 (force inpaint) | 7.79 MP | **29 s** | 93 s | 316.4 | yes | **18 patches** |

\* D's total is an overhead excursion, not sampler work: its sampler sum (77 s)
sits exactly on the monotone curve; its non-sampler overhead (244 s) is ~40 s
above every other arm's (198–223 s). Read totals as ±tens of seconds at n=1;
read the sampler columns as the measurement.

Timing structure (from the tqdm sampler traces in each arm's `server.log`,
segmented per sampler; `q2_sampler_breakdown.json`): every arm runs the
identical 14-sampler sequence, and **exactly one number moves — the face-pass
8-step sampler**: 1 → 3 → 6 → 11 → 19 → 29 s across the ladder (~area^1.5,
consistent with attention cost). Mouth (8-step, 3 s) and eyes (8-step, 2 s)
never move. The remaining growth with cf sits in overhead (VAE round-trip of
the growing crop, SAM, compositing), visible as E/F overheads ~215/223 s vs
~200 s at cf ≤ 2.

Downstream effects, per arm: mouth and eyes stages always fired (eyes guard
`622:662 = ["True"]` in all 7 histories; mouth segment 1.39–1.45 MPx, under
the 1.7M ceiling in every arm). Hand detector found nothing in any arm (hands
out of frame; `(no detections)`). Mouth/eye detections shift by a few px per
arm because they run on the face pass's output — the causal chain is visible
in the logs.

**VRAM note:** F (cf 3.5) is the one arm with a memory event — a single
partial unload (14.65 MB freed, **18 lowvram patches**) at the face pass, on a
96 GB card booted at ~52 GB free. CTL3 precedent (B-factor grid) says lowvram
patching alone did not change this graph family's output (4/4 bit-identical
under 0→85 patches), so F's image stands, flagged. But it means **cf ≥ 3
carries a real lowvram/OOM risk on buyer-sized cards**: force_inpaint samples
the crop at native size, and cf 3.5 is a 7.8 MP latent.

## Objective deltas (q2_analyze.py; all vs baseline A; common YOLO-union face box (963,430)–(1764,1513))

| arm | cf | full PSNR dB | full %px>8 | face PSNR dB | face %px>8 | face conf | modal_frac |
|---|---|---|---|---|---|---|---|
| G_cf15_repeat | 1.5 | **inf (max_abs_diff 0)** | 0.00 | **inf (0)** | 0.00 | 0.900 | 0.03987 |
| B_cf10 | 1.0 | 46.41 | 0.64 | 36.14 | 6.88 | 0.900 | 0.03987 |
| C_cf20 | 2.0 | 46.62 | 0.61 | 36.35 | 6.56 | 0.899 | 0.03987 |
| D_cf25 | 2.5 | 46.72 | 0.59 | 36.43 | 6.27 | 0.901 | 0.03987 |
| E_cf30 | 3.0 | 46.47 | 0.66 | 36.20 | 7.10 | 0.900 | 0.03987 |
| F_cf35 | 3.5 | 45.83 | 0.69 | 35.56 | 7.42 | 0.899 | 0.03987 |

- **G bit-identical to A** is the load-bearing row: zero same-window noise, so
  the other rows are pure cf effect.
- All arms healthy: modal colour white (255,255,255) at ~4% of frame,
  identical across arms (this session's own health scale; flat_frac ~0.0448,
  luma_sd ~66.42 everywhere). Nothing resembling the 23.5% constant-fill
  failure mode. Face found at conf ~0.90 everywhere; faces did not move
  (7-arm YOLO union is 691x934).
- Distances are **lateral, not ordered**: B vs C differ from each other
  (36.24 dB face) as much as either differs from A. Each cf lands on a
  different-but-equally-distant micro-rendition; there is no "further in cf =
  further from baseline" gradient until the mild dip at F.
- The metric's furthest-from-baseline is **F (cf 3.5)**; second is B (cf 1.0).

## Sight-read (1:1 sheets; face `q2cf_face_sheet1of1.png`, eye band `q2cf_eyeband_A_B_F.png`, skin/lips `q2cf_skin_sheet1of1.png`)

- **cf 1.0 is the one that looks different in kind**: skin reads smoother /
  more beauty-filtered, freckles weaker, lash and iris detail softer, and the
  eye shape is subtly more open than baseline. Consistent with its mechanics
  (smallest context, and the only arm resampled at x1.11 rather than native).
- **cf 2.0–3.5 stay in the baseline's family**: same sharpness class, same
  features; freckle placement, catchlights and individual hair strands
  reshuffle. At sheet scale I could not rank any of them above or below the
  baseline — they are alternates, not improvements or regressions.
- **Where metric and eye disagree, I rank by sight**: the metric says F
  (cf 3.5) is furthest from baseline, but to my eye **B (cf 1.0) is the most
  visibly different** (softness and eye shape are perceptually salient; F's
  larger pixel distance is spread across relit micro-texture). I am not
  judging which is *better* — the owner looks at the images; the sheets are
  1:1-verified for exactly that.

## Recommendation (recommend-only; shipped value untouched)

1. **Keep 1.5 as the shipped default.** It is second-cheapest, visually in the
   sharp family, and the repeat proves the configuration is deterministic.
2. **Do not raise cf as a quality lever.** 2.0–3.5 buy no visible improvement
   at sheet scale, cost +6 to +26 s of pure face-pass sampling (plus growing
   VAE overhead), and at 3.5 the pass already nudged a 96 GB card into
   lowvram patching — on buyer cards that is an OOM/lowvram risk with
   force_inpaint sampling 7.8 MP at native size.
3. **cf 1.0 is a legitimate "softer face" menu entry, not a speed lever**: it
   saves only ~2 s (within total-time wobble) but visibly softens skin/lashes
   and subtly opens the eyes. If that look is wanted, it is the cheapest way
   to get it; as a default it drifts furthest from the shipped look.
4. If a menu entry for cf is written, the honest copy is: "changes *which*
   face micro-rendition you get, and the render time — not how good the face
   is. 1.5 ships; 1.0 = softer look; above 2.0 = pay seconds for a sideways
   change."

## Provenance notes

- Arms ran A→B→C (13:09–13:38 UTC), paused on the orchestrator's instruction
  to yield the GPU to Track 1's gate (arm C completed normally; nothing was
  killed mid-render), resumed D→E→F→G (15:08–16:17) after the
  `.track1_gate_done` sentinel. Fresh-process-per-arm means the pause cannot
  contaminate arms; the bracketing cf 1.5 pair (first arm / last arm, either
  side of the pause) is bit-identical, which is the strongest available
  evidence the session window was stable.
- The driver initially held the lock while waiting out a low-VRAM window
  (32.4 GB free < the 50 GB gate, other tracks' servers resident) and was
  stopped for it; it was rebuilt to wait for VRAM *before* taking the lock
  (bounded 5-min re-check after acquisition). `results/run4/quality/Q2/RUN.log`
  is the full timeline.
- Timing comparisons here are between arms with matching cache state (all
  cold, fresh process, `execution_cached == []` recorded per arm), per
  STATE.md trap #7. Detailer resolutions are read from the `Detailer: segment
  upscale` server-log lines, not inferred from widgets, per trap #11. All
  pixel measurements are on slot-0 composites (the delivered 505 frame), per
  trap #10. No rendered-output hashing anywhere; the bit-identity claims are
  full-array `max_abs_diff` comparisons.
