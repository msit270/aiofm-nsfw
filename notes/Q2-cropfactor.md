# Q2 — bbox_crop_factor on `620:114` (the face pass)

**STATUS: PARTIAL — 3 of 7 arms rendered.** Run paused at 13:38 UTC on the
orchestrator's instruction to yield the GPU to Track 1's fresh-install gate
(arm C was allowed to finish; nothing was killed mid-render). Arms D–G resume
when `/workspace/nsfw-fix/.track1_gate_done` appears. Every number below is
from a completed, cold arm; the unmeasured cells are listed, not estimated.

The question (owner recorded cf as UNTESTED, not failed): what does
`620:114.bbox_crop_factor` actually do to quality and time on the CURRENT
shipping bytes? Shipped value read from `results/run3/guard/api_guarded.json`:
**1.5** — that is the baseline arm. cfg 1 / steps 8 / denoise 0.35 untouched
(settled, Q-PROTOCOL).

## Method (protocol-conforming)

- Graphs: `r3.py::guarded_graph` byte-for-byte — `v_mk.norm` on
  `api_guarded.json`, `v_mk.set_loras` (luna / lunaskye), 60-token buyer
  prompt into `620:106` (verbatim `620:106.text` from
  `results/run3/fresh/fresh-buyer-api_graph.json`, `v_tok.count == 60`),
  `619:603.pick_list = "0"`, TAP163. **One variable per arm** —
  `620:114.inputs.bbox_crop_factor` — proven per arm by an input-wise graph
  diff against the baseline arm's graph, stored in each `meta.json`
  (`graph_diff_vs_baseline_arm`).
- Fresh ComfyUI process per arm on **19188** under an exclusive flock on
  `.gpu_lock`; server killed and reaped before release. 18188 never touched.
- Cold verified per arm: `execution_cached == []` in the history entry
  (recorded in `meta.json`; "cold" column below).
- Fixed seeds (shipped: `620:114` 1111111, eyes 1111112, SDXL side as in file).
- Evidence per arm under `results/run4/quality/Q2/<arm>/`: `api_graph.json`,
  `history.json`, delivered PNG (`n505__*`), mouth-stage tap (`nTAP163__*`),
  `server.log`, `meta.json` (incl. the sliced detailer/detector log lines).

**n = 1 per cell** so far. The cf 1.5 repeat (arm G) is the same-window
noise-floor control; until it lands, no "vs baseline" delta here can be
attributed to crop factor rather than fresh-process run-to-run noise. That is
why it is in the design.

## Grid so far (server-side exec seconds; face-pass "Detailer: segment upscale" line verbatim)

| arm | cf | status | exec s | cold | face-pass segment upscale (620:114) | sampled px |
|---|---|---|---|---|---|---|
| A_cf15_baseline (SHIPS) | 1.5 | success | 266.6 | yes (`[]`) | `force inpaint` + `(690.9, 921.1) \| crop (1036, 1381) x 1.0 -> (1036, 1381)` | 1.43 MP |
| B_cf10 | 1.0 | success | 262.0 | yes (`[]`) | `(690.9, 921.1) \| crop (690, 921) x 1.1119 -> (767, 1024)` | 0.79 MP |
| C_cf20 | 2.0 | success | 273.5 | yes (`[]`) | `force inpaint` + `(690.9, 921.1) \| crop (1381, 1842) x 1.0 -> (1381, 1842)` | 2.54 MP |
| D_cf25 | 2.5 | **UNMEASURED** | — | — | — | — |
| E_cf30 | 3.0 | **UNMEASURED** | — | — | — | — |
| F_cf35 | 3.5 | **UNMEASURED** | — | — | — | — |
| G_cf15_repeat (noise floor) | 1.5 | **UNMEASURED** | — | — | — | — |

What the three measured lines already establish (trap #11 confirmed live on
the shipping config):

- The face detection handed to `620:114` is **identical to 7 significant
  digits across arms** — bbox (690.8927, 921.08136) in A, B and C — so the
  pass's input is cf-independent, as the wiring says it should be.
- At cf ≥ 1.5 the guide_size/max_size pair claws the scale to ≤ 1.0 and
  `force_inpaint` clamps it back to exactly 1.0, so **the crop is sampled at
  native resolution and cf alone sets the sampled area**: 0.79 → 1.43 → 2.54 MP
  across 1.0 → 1.5 → 2.0. No image-bound clamp yet at cf 2.0 (crop 1381x1842 =
  bbox x 2.0 exactly).
- At cf 1.0 the claw-back lands **above** 1.0 (x1.1119), i.e. the crop is
  genuinely upscaled before sampling — the only arm so far that does not hit
  the force-inpaint clamp.
- Downstream detections move with the face-pass output (mouth bbox 305.7 A /
  311.9 B / 304.9 C; eyes-stage crop 1420/1444/1442) — consistent with cf
  changing what the mouth/eyes stages receive. All five detector stages fired
  in all three arms; the eyes guard reports eyes ran (`622:662` outputs
  `["True"]` in each history entry, 5 `# of Detected SEGS` lines per arm).
- Time so far moves ~+4–7 s per 1.1 MP of extra face-pass area (262.0 →
  266.6 → 273.5 s), n = 1 per cell — treat as a trend, not a measurement,
  until D–F extend the curve and G bounds the noise.

## Objective deltas so far (q2_analyze.py; vs baseline arm A)

Common face box = union of per-image YOLO detections + 8% pad =
(963, 430)–(1764, 1513) on the 2688x3456 delivered frame. Face detected at
conf ~0.90 in all three arms; faces did not move (union 691x934 across arms).

| arm | full PSNR dB | full %px>8 | face-crop PSNR dB | face %px>8 | modal_frac | flat_frac | luma_sd |
|---|---|---|---|---|---|---|---|
| A_cf15_baseline | — | — | — | — | 0.03987 | 0.04486 | 66.423 |
| B_cf10 | 46.41 | 0.64 | 36.14 | 6.88 | 0.03987 | 0.04483 | 66.423 |
| C_cf20 | 46.62 | 0.61 | 36.35 | 6.56 | 0.03987 | 0.04487 | 66.421 |

(Health numbers are this session's own implementation — comparable only to
each other, per the B-factor-grid warning about cross-session health scales.)
All three renders are healthy by these metrics: modal colour is blown-out
white (255,255,255) at ~4% of frame in every arm — identical across arms, i.e.
the modal region sits outside the face composite — and nothing resembles the
23.5% constant-fill failure mode. The deltas concentrate in the
face crop (~36 dB, ~6.5–6.9% of face pixels moving >8 levels) as expected for
a face-pass-only change. **Interpretation is BLOCKED on arm G**: fresh-process
run-to-run noise on the sibling pipeline sat near 48.7 dB full-frame, close to
the ~46.5 dB measured here, so the full-frame numbers may be mostly noise; the
face-crop numbers look larger than plausible noise but I will not claim that
until G measures it on this graph, this box, this session.

## Sight-read so far (PARTIAL — 1:1 sheets `q2cf_face_sheet1of1.png` / `q2cf_skin_sheet1of1.png`)

Same composition, same face, no structural change, no artifacts in any arm.
Differences are subtle and local to the detailed region: **B (cf 1.0)** reads
slightly softer — skin micro-texture a touch smoother, freckles marginally
weaker, eye catchlights slightly different. **C (cf 2.0)** is very close to
baseline; subtle texture/catchlight differences only. I would not rank any of
the three as visibly better or worse at sheet scale; none of this is a
quality verdict — the owner looks at the images.

## Unmeasured cells / what resumes

- cf 2.5, 3.0, 3.5 arms (D/E/F) — including where the crop hits the image
  bound (the crop-region print will reveal the face-pass canvas size; at cf 2.0
  it has not clamped yet, so the canvas is ≥1381x1842).
- cf 1.5 repeat (G) — the same-window noise floor that gates every conclusion
  above.
- Contact sheets and this note will be rebuilt over all 7 arms when the run
  completes; the current sheets carry a red PARTIAL banner.

No shipped value was changed. RECOMMEND-ONLY; recommendation deferred until
the full grid exists.
