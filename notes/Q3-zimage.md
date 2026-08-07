# Q3 — Z-Image detail passes: quality menu (run 4, 2026-08-07) — COMPLETE

**One line: of the five levers swept around the settled 8/0.35/cfg-1 baseline,
only the face-pass SAMPLER moves the image visibly; steps and denoise nudge
texture by percents in directions already known to end badly, and the eyes-
and mouth-pass step counts are dead levers. Two composition findings matter
more than any dial: the mouth pass never runs on small-face renders, and the
face pass samples at a different resolution regime per composition.**

Recommend-only: nothing in `OFMTech-NSFW/`, the workflow JSON, or `dist/` was
touched. cfg stayed 1 in every arm (settled; guidance-distilled Turbo).
n = 1 render per cell throughout — every number below is a single cold render
per configuration; treat magnitudes as indicative, directions as measured.

## The three passes, quoted from the shipping conversion

Read from `results/run3/guard/api_guarded.json`, re-verified byte-identical in
`api_final.json`:

| pass | node | class | steps | denoise | cfg | sampler | scheduler | guide/max | feather | noise_mask_feather | seed |
|---|---|---|---|---|---|---|---|---|---|---|---|
| face | `620:114` | FaceDetailer | 8 | 0.35 | 1 | euler_ancestral | kl_optimal | 1024/1024 | 18 | 20 | 1111111 |
| mouth | `620:165` | FaceDetailer | 8 | 0.35 | 1 | euler_ancestral | kl_optimal | 1808/1808 | 3 | 20 | 1111111 |
| eyes | `622:406` | DetailerForEachDebug | 8 | 0.42 | 1 | euler | beta | 1920/1920 | 2 | 20 | 1111112 |

Correction to my own brief: the mouth SAMPLER is `620:165` (host 620), not
under host 621 — host 621 holds only its prompts/detectors (`621:166/167`,
`621:161/160`) and the after-mouth colormatch `621:163`. All three passes
draw the model from `620:113 UNETLoader zimage.safetensors` → `116` LoRA
stack. Downstream-wired output slots (trap STATE #10): slot 0 on all three
(`620:114→620:111`, `620:165→621:163`, `622:406→622:401`); every measurement
here is on slot-0 taps or the delivered frame, never `cropped_refined`.

## Base bytes — a protocol correction the next agent needs

Q-PROTOCOL names `api_guarded.json` as "the current shipping bytes". It
predates two shipped changes: the eyes feather (`622:664 FeatherMask` →
`622:418.mask`) and the mouth ceiling (`620:648.max_value` 1.7M→4M). Proof:
`api_final.json` differs from the verified fresh-buyer conversion
(`results/run3/fresh/fresh-buyer-api_graph.json`) on exactly the four
buyer-typed values; `api_guarded.json` differs on those four plus the two
changes above. Arms here are based on **`api_final.json`** + the four buyer
values (both Luna LoRAs; balcony 483 prompt, seed 12345 fixed; the 60-token
`620:106` face prompt) + `pick_list "0"`, so the baseline graph IS the
verified buyer render graph with 0 other differences (asserted in
`tools/q3.py`). Four SaveImage taps — 620:137 face-in, 620:114 face-out,
620:111 mouth-in, 621:163 eyes-in — are identical in every arm. The three
pass settings are byte-identical between the two guard files, so the sweep is
unaffected by the base choice, but mouth/eye-band evidence on `api_guarded`
would not have matched shipped output.

## Method and validity (all arms)

Fresh server per arm on :19188 under the flock; `execution_cached: []`
verified on all 10 arms; evidence per arm under `results/run4/quality/Q3/
<arm>/` (submitted graph, verbatim history, server log, 2 s nvidia-smi
samples, 5 PNGs). Structural check (`tools/q3_checks.py`, ALL PASS): every
face-lever arm's TAP137 is **byte-identical** to the baseline's (max abs diff
0 — seven independent cold processes reproduced everything upstream of the
face pass bit-exactly), E_steps16's four pre-eye taps are byte-identical, and
P_M's three pre-mouth taps are byte-identical to P0's. So each variable
expressed itself only downstream of its own pass. (This is same-window
determinism corroboration, not the banned inertness-by-hash method — the
changed stage is REQUIRED to differ, and does.)

**Timing.** Cold whole-render times spread 285.5–313.5 s across arms whose
sampling differs by ≤ 2 s — ±5 % cold noise (R1 §6), so whole-render deltas
are NOT lever costs. The honest lever costs come from the sampling loop rate:
the face pass runs ~4.9 it/s at its sampled size, so steps 8→12→16 costs
≈ +0.8 s / +1.6 s. Denoise and sampler changes are time-free. VRAM: arm-server
peak 25,110–29,752 MiB across all arms (2 s sampling; the two recurring values
look like allocator variance in USDU tiling, not a lever effect — no arm
stood out).

**Composition matters more than any dial (trap STATE #11, measured).** The
`Detailer: segment upscale` lines per arm:
- Balcony full-body (all A0/F/E arms, identical line in every one):
  face seg 329×433, `crop (493, 650) x 1.576 -> (776, 1024)` — the guide/max
  1024 pair ENGAGES as an upscale; the pass samples 0.79 MP. Eyes:
  seg 956×137, `crop (1459, 411) x 1.316 -> (1920, 540)`.
  **Mouth: no line — the lips detector logs `0: 640x512 (no detections)`**
  (bbox_threshold 0.7, face ~330 px wide); TAP111 vs TAP163 differ by max
  1 level (colormatch residue). **The mouth pass is a no-op on this
  buyer-default composition.**
- Portrait (P0/P_M; the shipped 483 placeholder prompt): face seg 690×921,
  `crop (1036, 1381) x 1.0` — clamped, sampled at native 1.43 MP, no upscale;
  mouth RUNS: lips seg 305×132, `crop (916, 398) x 1.974 -> (1808, 785)`;
  eyes `x 1.352 -> (1920, 616)`; and the HANDS pass finds no hand (its
  detector logs the no-detection line instead). So which detail passes
  actually run, and at what sampling resolution, flips with framing — a menu
  fact bigger than any of the step/denoise dials below.

## Results by lever (metrics on TAP114 = the face pass's wired output, fixed
nose/cheek rect [861,434]-[1092,609], R1's CIELAB rule, radius 7 px;
"final eye-band" on the delivered frame; per-arm JSON in each arm dir)

### Lever 3 — face-pass sampler (euler_ancestral ships) — THE ONLY LIVE LEVER

| arm | face %>8 (tap114) | PSNR | pigment % | bright-blob % | lapvar face | lapvar skin | exec s |
|---|---|---|---|---|---|---|---|
| **euler_ancestral (ships)** | — | — | 1.324 | 3.883 | 219.3 | 147.3 | 313.5 |
| euler | 4.28 | 37.7 dB | 1.846 (+39 %) | 6.122 (+58 %) | 226.0 | 154.8 | 302.2 |
| res_multistep | 9.96 | 35.5 dB | 3.302 (+149 %) | 10.696 (+175 %) | 239.2 | 170.0 | 303.6 |

Sight-read (describe-only): **res_multistep transforms the face** — freckles
become dense, dark, clumped masses spreading to regions the baseline leaves
clear (nose bridge, between brows, chin), a reddish mottle appears on the
cheek centres, the whole complexion reads warmer/darker and heavily textured.
Depending on taste this is "rich lived-in skin" or "blotchy/irritated"; at 3×
the cheek mottle reads to me closer to irritation, but that is exactly the
judgement reserved for the owner. **euler** is the midpoint: denser fine
freckling than shipped, crisper micro-texture, a faint cheek mottle, no heavy
clumping. **euler_ancestral (ships) is the cleanest/smoothest of the three.**
Sheets: `sheets/Q3_L3_face_sampler_*`. Cost: none (same step count; exec
deltas are noise). Caveats: kl_optimal was held constant to keep one variable,
so `res_multistep + simple` — the vendor template's actual pairing
(R3-decisions §2) — is UNTESTED; and the eye pass re-renders on the changed
face (R3-eyes coupling), so eye-band deltas (6.5 %/13.9 % >8) include both
effects.

**Menu entry:** if the owner wants more freckle/texture character from the
face pass, the sampler is the lever that actually does something, and the L3
face sheet is the decision artifact. If the shipped look is right, ship stays.

### Lever 1 — face-pass steps (8 ships; 12, 16) — free, moves toward the known crust

| arm | face %>8 (tap114) | PSNR | pigment % | bright-blob % | lapvar face | exec s |
|---|---|---|---|---|---|---|
| **8 (ships)** | — | — | 1.324 | 3.883 | 219.3 | 313.5 |
| 12 | 0.17 | 42.7 dB | 1.511 (+14 %) | 4.604 (+19 %) | 220.9 | 290.1 |
| 16 | 1.16 | 40.2 dB | 1.729 (+31 %) | 5.098 (+31 %) | 222.0 | 285.5 |

Monotonic speckle densification — more freckle-coloured marks AND more bright
micro-blobs, broadband lapvar flat. The added marks look freckle-like at 3×,
not raised-bump, but this metric pair cannot distinguish added speckle from
early crust (R1 §1), and the trajectory ends at the steps-30 bump mat the
owner already paid to remove. Freckle placement is unchanged; additions are
new marks. Sampling cost ≈ +0.8 s/+1.6 s. Diff maps show the eye pass
amplifying the change into iris/catchlight micro-structure (0.75 %/1.33 %
eye-band >8) — sub-visible at 1:1 on the band sheets. My first side-by-side
glance "saw" denser freckles where the diff map showed 0.31 % — recorded as a
caution on sight-reads without a diff. **Recommendation: keep 8; 12 only if
the owner reads the L1 sheet's speckle as character rather than crust.**

### Lever 2 — face-pass denoise (0.35 ships; 0.30, 0.45) — confirms 0.35 as the knee

| arm | face %>8 (tap114) | PSNR | pigment % | bright-blob % | lapvar skin | exec s |
|---|---|---|---|---|---|---|
| **0.35 (ships)** | — | — | 1.324 | 3.883 | 147.3 | 313.5 |
| 0.30 | 0.05 | 46.7 dB | 1.354 (+2 %) | 4.236 (+9 %) | 149.3 | 295.9 |
| 0.45 | 0.46 | 43.1 dB | 1.376 (+4 %) | 3.675 (−5 %) | 142.3 | 305.5 |

0.30 is a near no-op — R1's "there may be nothing left to win below 0.35" now
measured. 0.45 moves the OTHER way: bright-blob down, flat-skin lapvar −3.4 %
— the beginning of the smoothing/airbrush direction that R1 documented at
0.50 ("the near miss... softer... the arm I would call airbrushed"). The
shipped 0.35 sits at the knee between the speckle direction (steps up) and
the airbrush direction (denoise up). Time-free. **Recommendation: no change;
this lever is done being litigated — both sides of 0.35 are now measured.**

### Lever 4 — eyes-pass steps (8 ships; 16) — DEAD LEVER

Pre-eye taps byte-identical; the delivered frame differs by **max 4 levels on
0.015 % of pixels** (face PSNR 70.5 dB). Mechanistically coherent: `622:406`
runs plain `euler` — a deterministic ODE solver — so more steps refine the
same trajectory instead of changing the noise sequence (unlike
euler_ancestral on the face pass, which is why face steps DO move pixels).
Costs ~2 s for nothing. Sheets: `Q3_L4_eyes_steps_*`. **Recommendation:
skip; eye-pass step count buys nothing measurable at denoise 0.42.**

### Lever 5 — mouth-pass steps (8 ships; 16, on the portrait where lips detect) — DEAD DIAL, LIVE DETECTOR FINDING

P0 (portrait baseline) vs P_M (mouth steps 16): pre-mouth taps byte-identical;
after-mouth tap differs max 14 levels on 0.57 % of the frame; mouth-band
0.01 % >8, PSNR 55 dB; the L5 mouth-band tiles are indistinguishable at 1:1.
The change is confined to the SAM lips mask and is tiny. **Recommendation:
skip the dial.** The real mouth-quality lever is upstream: on the full-body
buyer default the lips detector (thr 0.7) finds nothing and `620:165` never
samples — mouth quality on that class of render is whatever `620:114` leaves.
If mouth quality on full-body renders matters, the follow-up arm is
`621:161`-side threshold (0.7 → ~0.5) or a detector swap, not steps — one
render each, same harness, UNTESTED here (arm cap).

## Unmeasured cells (stated per protocol)

Face-pass `noise_mask`/`feather`/`noise_mask_feather` variants (the brief's
lever 5) — traded for the portrait pair after the mouth no-op discovery.
`res_multistep + simple` (vendor pairing). Mouth-detector threshold on
full-body. Everything is n=1; nothing here was replicated.

## Untested possibility (no pack installs permitted): GGUF text encoder

`models/text_encoders/qwen-4b-zimage-heretic-q8.gguf` (4.28 GB) ships and
nothing loads it: core `CLIPLoader` does not enumerate `.gguf` and no GGUF
loader pack is installed (verified `custom_nodes` listing). Swapping the
Z-Image text encoder to it needs a city96-style `ComfyUI-GGUF` pack and would
change conditioning on all three passes — effect UNKNOWN, no claim made.
Provenance/licence read from the HF API this session (raw responses under
`results/run4/quality/licences/`): sha256 `70af2493…f1ef3` matches
`Lockout/qwen3-4b-heretic-zimage` (2025-11-30, licence tag **apache-2.0**;
byte-identical mirror `ItBitter/…`); card: "the actual TE from z-image [run]
through heretic … abliterated"; upstream `Tongyi-MAI/Z-Image-Turbo`
apache-2.0. A V2 ("lower KLD") exists in the same repo, different bytes. See
`licences/qwen-4b-zimage-heretic-q8_PROVENANCE.md`.

## The ranked menu

1. **Face sampler `620:114` (owner eyeballs `Q3_L3_face_sampler_face_sheet1of1.png`).**
   The only lever with a visible payoff either way. euler = moderately denser
   freckle/texture; res_multistep = heavy freckle character + cheek mottle
   (risk: reads as blotchy). Free in time. If shipped look is right, change
   nothing.
2. **Face steps 12** — only if the L1 sheet's extra speckle reads as
   character; direction is the old defect, cost ≈ +0.8 s.
3. **Mouth detector coverage on full-body renders** (untested follow-up):
   threshold 0.7 → ~0.5 on `621:161`'s consumer path, one arm, before anyone
   tunes mouth-pass dials that currently never execute on such renders.
4. **`res_multistep + simple`** (vendor pairing, untested) — only if the
   owner likes the res_multistep direction but wants it on-template.
5. **Denoise, eye steps, mouth steps: leave alone** — measured dead or
   knee-confirmed.
6. **GGUF encoder swap** — untested possibility, apache-2.0 chain recorded;
   needs a pack decision first.

## Evidence index

- Arms: `results/run4/quality/Q3/{A0_baseline,F_steps12,F_steps16,F_den030,
  F_den045,F_res_multistep,F_euler,E_steps16,P0_portrait_baseline,
  P_M_steps16}/` — api_graph.json, history.json, meta.json (incl. per-arm
  `detailer_log_lines` and VRAM peaks), server.log, vram_samples.csv, 5 PNGs.
- Sheets (all 1:1-verified, baseline tile marked, labels carry the change +
  cold exec seconds): `results/run4/quality/Q3/sheets/Q3_L{1..5}_*`.
- Per-arm deltas: `<arm>/deltas_vs_A0_baseline.json`
  (`P_M_steps16/deltas_vs_P0_portrait_baseline.json`).
- Tools: `results/run4/quality/Q3/tools/{q3.py,q3_analyze.py,q3_checks.py,
  q3_sheets.py,q3_table.py}`; sampler enums snapshot
  `tools/object_info_detailers.json` (res_multistep/euler/kl_optimal all
  valid on this 0.15.1 instance — checked before the sampler arms ran).
- Scheduling: track-1 priority interrupt honoured mid-queue (driver stopped
  between arms after F_steps16, resumed on `.track1_gate_done`); fresh-
  process-per-arm makes the pause unable to contaminate comparisons.
