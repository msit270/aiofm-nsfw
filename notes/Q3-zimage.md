# Q3 — Z-Image detail passes: quality menu (run 4, 2026-08-07)

Status: IN PROGRESS — arms rendering. This header section is settled; per-lever
sections are filled as arms land.

Recommend-only. Nothing in `OFMTech-NSFW/`, the workflow JSON, or `dist/` was
touched. Evidence: `results/run4/quality/Q3/<arm>/` (submitted graph, verbatim
history, PNGs incl. four tap points, full server log, 2 s nvidia-smi samples).

## The three passes, read from the shipping conversion

Node ids and shipped values quoted from `results/run3/guard/api_guarded.json`
and re-verified identical in `api_final.json` (see "base bytes" below):

| pass | node | class | steps | denoise | cfg | sampler | scheduler | guide/max | feather | noise_mask/feather | seed | detector path |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| face | `620:114` | FaceDetailer | **8** | **0.35** | **1** | euler_ancestral | kl_optimal | 1024/1024 | 18 | True/20 | 1111111 | `620:107` bbox face, SAM `620:108`, bbox_crop_factor 1.5 |
| mouth | `620:165` | FaceDetailer | **8** | **0.35** | **1** | euler_ancestral | kl_optimal | 1808/1808 | 3 | True/20 | 1111111 | `621:161` bbox lips (thr 0.7), SAM `621:160`, crop_factor 3, hook `620:648` SEGS≤4M |
| eyes | `622:406` | DetailerForEachDebug | **8** | **0.42** | **1** | euler | beta | 1920/1920 | 2 | True/20 | 1111112 | MediaPipe FaceMesh eyes+pupils → `622:408` MaskToSEGS, on the `622:414` 1920px face crop |

A correction to my own brief: the mouth SAMPLER is `620:165` (API id under
host 620), not under host 621 — host 621 holds only its prompts/detectors
(`621:166/167/161/160`) and the after-mouth colormatch `621:163`. The eyes
sampler is under 622 as expected. All three sample the Z-Image Turbo model:
`620:113 UNETLoader zimage.safetensors` → `116` LoRA stack → each pass's
`model` input. cfg is 1 everywhere and stays 1 in every arm (settled;
HANDOFF §"cfg=1 negatives", STATE §8, notes/R3-decisions.md §2).

Downstream-wired output slots (trap STATE #10 — measure the wired slot):
`620:114` slot 0 → `620:111`; `620:165` slot 0 → `621:163`; `622:406` slot 0 →
`622:401`. All measurements below are on slot-0/tap or delivered images, never
`cropped_refined`.

## Base bytes — a protocol note the next agent needs

Q-PROTOCOL says base arms on `results/run3/guard/api_guarded.json` ("the
current shipping bytes"). That file predates two shipped changes: the eyes
feather (`622:664 FeatherMask` → `622:418.mask`, commit 72f95ba) and the mouth
ceiling (`620:648.max_value` 1.7M → 4M, commit 07d61b2). Proof:
`api_guarded.json` vs the verified fresh-buyer conversion
(`results/run3/fresh/fresh-buyer-api_graph.json`) differs on exactly those two
plus the four buyer-typed values; **`api_final.json` differs on the four
buyer-typed values only.** So arms here are based on `api_final.json` + those
four buyer values (both Luna LoRAs, the balcony 483 prompt seed 12345 fixed,
the 60-token `620:106` face prompt) + `pick_list "0"` — i.e. the baseline arm's
graph IS the verified buyer render graph, 0 other differences (asserted in
code, `tools/q3.py`). Four SaveImage taps (620:137 face-in, 620:114 face-out
slot 0, 620:111 mouth-in, 621:163 eyes-in) are identical in every arm,
including the baseline.

The three pass settings are byte-identical between `api_guarded.json` and
`api_final.json`; the sweep itself is unaffected by the base choice, but the
mouth and eye-band evidence would not have matched shipped output on the
older file.

## Findings so far (baseline arm)

**Baseline (`A0_baseline`)**: success, cold (`execution_cached: []`),
**313.5 s** server-side, arm-server VRAM peak **29,752 MiB** (whole-GPU peak
75,011 MiB with the resident :18188 instance). Output 2688×3456. Face detected
at (812,282)-(1142,718), conf 0.867 — the face is ~330×436 px, ~12 % of frame
width (full-body balcony composition).

**Detailer segment-upscale lines (trap STATE #11), baseline, in order:**

```
SDXL face 619:607 : seg 176x233 | crop region (530, 699)  x 1.831 -> (970, 1280)
hands     587:92  : seg 224x154 | crop region (336, 231)  x 3.048 -> (1024, 704)
Z face    620:114 : seg 329x433 | crop region (493, 650)  x 1.576 -> (776, 1024)
Z eyes    622:406 : seg 956x137 | crop region (1459, 411) x 1.316 -> (1920, 540)
```

On this composition the guide/max interplay ENGAGES as an upscale (unlike the
R1/R3 portrait renders where it clamped to ×1.0): the face pass samples the
493×650 crop at 776×1024 (~0.79 MP), the eye pass samples at 1920×540. The
identity `min(guide/min(seg), max/max(crop×up)) = 1.576` reproduces the logged
factor exactly.

**The mouth pass is a no-op on this buyer-default composition.** The lips
detector logs `0: 640x512 (no detections)` (server.log:403); there is no mouth
`segment upscale` line and no `[filter]` line; TAP111 vs TAP163 differ by max
1 level on 0.086 % of pixels — the colormatch's numerical residue, no sampling.
The face is too small for the lips model at `bbox_threshold 0.7`. Consequence:
(a) the mouth-steps lever is measured on a second baseline (`P0_portrait_
baseline`) using the OTHER shipped buyer default — `api_final.json`'s own 483
placeholder portrait prompt — where lips do detect; (b) menu item: on
full-body/small-face renders, mouth quality is whatever the face pass leaves —
no dedicated pass runs. n=1 composition; threshold sensitivity unmeasured.

**Baseline texture numbers** (nose/cheek rect [861,434]-[1092,609], R1's
CIELAB rule at radius 7 px ≈ 2 % of face width): pigment 0.925 %, bright-blob
3.579 % (absolute values are composition-specific and only comparable within
this sweep). Sight-read of the baseline face at 2×: discrete brown freckles across
nose and both cheeks, structured irises with catchlights, lash and brow
strands resolved, fine pore texture on the nose, lips slightly soft with faint
vertical texture. No bump-crust visible at this scale.

## Untested possibility (no pack installs permitted): GGUF text encoder

`models/text_encoders/qwen-4b-zimage-heretic-q8.gguf` ships in the pack and
nothing loads it: ComfyUI core `CLIPLoader` does not enumerate `.gguf`, and no
GGUF loader pack is installed. Swapping the Z-Image text encoder to this file
would need city96-style `ComfyUI-GGUF` (a new pack — out of scope, banned) and
would change conditioning on all three passes. Provenance + licence read from
the HF API this session, raw responses under `results/run4/quality/licences/`:
sha256 `70af2493…f1ef3` matches `Lockout/qwen3-4b-heretic-zimage` (created
2025-11-30, licence tag **apache-2.0**; byte-identical mirror
`ItBitter/qwen3-4b-heretic-zimage`). Card: "the actual TE from z-image
[run] through heretic … abliterated." Upstream `Tongyi-MAI/Z-Image-Turbo`:
apache-2.0. A V2 ("lower KLD") exists in the same repo, different bytes. See
`licences/qwen-4b-zimage-heretic-q8_PROVENANCE.md`. Whether an abliterated
encoder changes NSFW-prompt adherence on the detail passes is UNKNOWN — no
claim is made.

## Arms (planned; results appended as they land)

One variable per arm vs `A0_baseline` (P_M_steps16 vs `P0_portrait_baseline`),
fresh server per arm on :19188 under the flock, cold asserted from
`execution_cached: []`, fixed seeds throughout.

| arm | change | lever |
|---|---|---|
| A0_baseline | — (ships) | reference, n=1 |
| F_steps12 / F_steps16 | face steps 8→12 / 8→16 | 1 |
| F_den030 / F_den045 | face denoise 0.35→0.30 / →0.45 | 2 |
| F_res_multistep / F_euler | face sampler euler_ancestral→res_multistep / →euler (scheduler kl_optimal held) | 3 |
| E_steps16 | eyes steps 8→16 | 4 |
| P0_portrait_baseline | 483 prompt → shipped placeholder portrait (2nd baseline) | 5 |
| P_M_steps16 | portrait + mouth steps 8→16 | 5 |

**Unmeasured cells at the yield point** (resume on `.track1_gate_done`):
face denoise 0.30 / 0.45 (lever 2), face sampler res_multistep / euler
(lever 3), eyes steps 16 (lever 4), portrait baseline + portrait mouth
steps 16 (lever 5). Nothing below this line claims anything about those.

**Scheduling note (2026-08-07 ~13:39):** orchestrator priority interrupt —
track 1's gate starved on the lock behind three Q drivers. F_steps16 was
mid-render and was allowed to finish; the driver is stopped in the between-arms
window after it, and resumes on the `.track1_gate_done` sentinel. Fresh-process
per arm means the pause cannot contaminate any comparison.

## Lever 1 — face-pass steps (8 ships; 12, 16 swept) — COMPLETE, n=1 per cell

Sheets: `results/run4/quality/Q3/sheets/Q3_L1_face_steps_{face,skin}_sheet1of1.png`
(+ `_eyeband.png`, `_mouthband.png`), all 1:1-verified, baseline marked.

| arm (n=1 each) | exec s (cold) | VRAM MiB | tap114 face %>8 | tap114 PSNR | pigment % | bright-blob % | lapvar face | final eye-band %>8 |
|---|---|---|---|---|---|---|---|---|
| **steps 8 (ships)** | 313.5 | 29752 | — | — | 1.324 | 3.883 | 219.3 | — |
| steps 12 | 290.1 | 29752 | 0.17 | 42.7 dB | 1.511 | 4.604 | 220.9 | 0.75 |
| steps 16 | 285.5 | 25112 | 1.16 | 40.2 dB | 1.729 | 5.098 | 222.0 | 1.33 |

(pigment/blob/lapvar measured on TAP114, the pass's wired output, fixed
nose/cheek rect; "final eye-band" is the delivered frame, where the eye pass
re-renders on the changed input — the R3-eyes coupling, and the diff maps show
exactly that: iris/catchlight hotspots plus diffuse sub-8-level texture.)

**Cost: effectively zero on this composition.** The pass samples 776×1024 at
~4.9 it/s; 8→16 steps is ≈ +1.6 s of sampling. Whole-render deltas
(313.5→285.5 s) are cold-run noise, not the lever — the ladder got FASTER as
steps rose, which is physically backwards and disqualifies the whole-render
number (R1 §6's variance).

**Effect: monotonic speckle densification, direction of the known crust.**
pigment +14 %/+31 % rel, bright-blob +19 %/+31 % rel at steps 12/16; broadband
lapvar flat (+1 %). At 3× the steps-16 cheek carries visibly more small dark
freckle-like marks AND more bright micro-speckle than baseline; the marks look
freckle-like, not raised-bump — but R1 §1 proved this exact metric pair
cannot distinguish added freckle-like speckle from early crust (at steps 30
the same trend ends in the bump mat, blob ~2× at 3.364 vs Z2's 1.681 on R1's
composition). Freckle placement is unchanged; the additions are new marks.

**Recommendation: leave steps at 8.** The lever is free in time but the only
measurable movement is toward the defect the owner already paid to remove
(steps 30→8, HANDOFF §4). If the owner LIKES the denser speckle on the sheet,
steps 12 is the safer of the two increments (blob +19 % vs +31 %). What would
change this: the owner reading the steps-16 cheek tile as better freckle
character rather than incipient crust — that is precisely the judgement I am
not allowed to make.

### Lever 1 raw log (was the in-flight partial)

`F_steps12` (steps 8→12): success, cold, **290.1 s** (baseline 313.5 s — the
23 s gap is cold-run noise, not the lever; R1 §6 puts single-cold-pair
variance at tens of seconds). VRAM peak 29,752 MiB — identical to baseline.
The face pass samples the same `(493, 650) x 1.576 -> (776, 1024)` crop
(segment-upscale line identical to baseline), ~4.9 it/s, so 8→12 steps costs
**≈ 0.8 s of sampling**. Direct effect at `620:114`'s wired output (TAP114):
face box 0.17 % of pixels >8 levels, PSNR 42.7 dB. Delivered frame: face
0.31 % >8, eye band 0.75 % >8 (the eye pass re-rendering on a marginally
changed input — R3-eyes coupling, visible in the diff map as iris/catchlight
hotspots), mouth band 0.06 %. Texture: pigment 1.51 vs 1.32 (+14 % rel),
bright-blob 4.60 vs 3.88 (+18.6 % rel — direction of the steps-30 crust,
magnitude tiny), lapvar face 220.9 vs 219.3 (+0.7 %), flat-skin lapvar 147.8
vs 147.3. Sight-read at 2×: I could not honestly tell the tiles apart —
freckles identical in count and placement; the amplified diff shows diffuse
sub-8-level texture inside the noise-mask region and the eye hotspots.
(A first side-by-side glance "saw" denser freckles on steps-12; the diff map
refutes that — recorded as a caution against sight-reads without a diff.)

Prior art this sweep builds on, not re-litigates: steps 30→8 removed the
bump-crust defect (HANDOFF §4, R1 §5: steps 30 at den 0.35 puts crust back,
3.364 % vs 1.681 % bright-blob); denoise 0.80→0.35 shipped after R1's ladder
(0.50 = "airbrushed" near-miss, softer than 0.35; below 0.35 untested — that
is what F_den030 tests); cf 1.5 shipped after R3-decisions. The sampler lever
is new: the vendor's own Z-Image-Turbo template pairs `res_multistep/simple`,
while the graph ships `euler_ancestral/kl_optimal` — no recorded reason.
