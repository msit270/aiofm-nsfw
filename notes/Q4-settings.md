# Q4 — other shipped settings: what is leaving quality on the table

**COMPLETE: all 7 arms rendered, cold, on current shipping bytes + the buyer
prompt.** Six levers were scoped to Q4 (everything except `#114`
bbox_crop_factor → Q2, and the Z-Image passes' steps/denoise/sampler → Q3).
Settled items were not re-litigated: cfg 1 on Z passes, D1 revert, two-LoRA
design, `#114` 8/0.35 as shipped default, the crash guard.

**The sheets to look at (1:1, verified byte-identical to source, baseline
tile marked, every tile labelled with the change + server-side seconds):**

- `results/run4/quality/Q4_sheets/Q4_face_sheet1of1.png` (7 tiles, 408×538)
- `results/run4/quality/Q4_sheets/Q4_skin_sheet1of1.png` (7 tiles, 300×300,
  same chest patch x=960 y=798 on every arm)

Per-arm evidence: `results/run4/quality/Q4/<arm>/` — submitted `api_graph.json`,
verbatim `history.json` (`execution_cached: []` in every arm), delivered
`n505__*.png` + post-mouth `nTAP163__*.png`, `server.log`, `vram_samples.json`
(2 s cadence), timestamped `ws.json`, `meta.json` (summary + USDU/Detailer log
extracts + per-node VRAM attribution). `metrics.json` holds every number below.

**Every cell is n=1.** One render per arm, one composition, one seed (12345).
R4 measured this pipeline's fixed-seed run-to-run difference at exactly zero
on its graph and session; that was not re-proven here, so treat small deltas
as directional.

---

## 0. Method, and two deviations recorded

Protocol (`notes/Q-PROTOCOL.md`) followed: exclusive flock on `.gpu_lock` for
every GPU step; a FRESH `/venv/main/bin/python main.py --port 19188
--disable-auto-launch --disable-xformers --output-directory
/workspace/trackQ/output` per arm (18188 never touched); cold by construction
and verified from `execution_cached`; server killed and port confirmed quiet
before the lock released; VRAM ≥ 50 GB gate before boot.

**Deviation 1 — base graph.** The protocol names
`results/run3/guard/api_guarded.json` as "the current shipping bytes". That
file predates two shipped output-changing fixes (`620:648` mouth ceiling
1.7M→4M, `07d61b2`; `622:664 FeatherMask` → `622:418.mask`, `72f95ba`). Arms
were built from **`api_final.json`**, which differs from the buyer-verified
conversion (`results/run3/fresh/fresh-buyer-api_graph.json`) in exactly the
four buyer-typed inputs. The builder asserts the finished baseline equals the
fresh-buyer graph except `619:603.pick_list` `""`→`"0"` and the added `TAP163`
SaveImage on `621:163`. Mutations follow `r3.py::guarded_graph` (`v_mk.norm`,
`v_mk.set_loras` — lunaskye on `#618`, luna on `#116`; buyer `#483` batch and
`#106` text copied from the fresh graph). Each arm graph-diffed vs baseline
with `tools/graph_diff/graph_diff.py`: **exactly the intended inputs, nothing
else** (`<arm>/graph_diff_vs_baseline.txt`).

**Deviation 2 — scheduling.** Mid-batch, the orchestrator ordered track 2 to
yield the lock queue to track 1's gate. Q4 stopped between arms (driver
blocked in flock, holding nothing), waited on the `.track1_gate_done`
sentinel, and resumed. Consequence for timing: arms rendered in **two
windows** — pre-yield (`baseline_ships` 269.7 s, `blend87_050` 270.3 s) and
post-yield (283.5–289.8 s). Every post-yield arm shifted +14–20 s **uniformly,
regardless of which node changed**, so the offset is environmental (this GPU
also serves other tracks' servers), not the changes. Compare timings only
within a window; all arms are equally cold (fresh process each).

Traps honoured: deltas measured on the delivered `505` frame (STATE trap #10),
`TAP163` kept for attribution; `Detailer: segment upscale` + USDU tiling lines
read from each arm's own log, not from widgets (trap #11); no output hashing —
graph diffs prove arm identity, pixel numbers are descriptive only.
**Licences:** no arm recommends any model file (settings only), so the
protocol's licence-flag requirement is not triggered.

Face boxes are detected per image with the graph's own `face_yolov8m.pt`
(CPU). All non-`steps60` arms re-detect within 2.1 px of the baseline box
(conf 0.865±0.002); `steps60` moved 23.9 px (see §5). Texture uses R4's
instrument verbatim over masks fixed from the baseline: a **frame-wide skin
mask (2.90 Mpx — the well-powered one)** and a face mask (0.061 Mpx — counts
there are 11–16 discrete events, quantized; two different images even tied
exactly once, so read face-mask texture as coarse).

Health: every arm `flat_frac` ≤ 0.013 vs the ~0.999 poisoned signature —
no silent-grey render anywhere.

---

## 1. Summary table

Baseline: 269.7 s, peak 22,328 MiB, face (812,282)-(1144,720) conf 0.865.
"face >8" = % of face-crop pixels differing from baseline by >8 levels.

| arm | change | exec s | peak MiB | full PSNR/SSIM | face PSNR/SSIM | face >8 |
|---|---|---|---|---|---|---|
| `baseline_ships` | none (ships) | 269.7 | 22328 | — | — | — |
| `blend87_050` | `#87` blend 1.0→0.5 | 270.3 | 21752 | 38.48 / 0.951 | 35.19 / 0.908 | 7.8 % |
| `usdu617_dn015` | `#617` denoise 0.25→0.15 | 287.1 | 22072 | 35.81 / 0.925 | 31.41 / 0.853 | 16.1 % |
| `usdu617_dn035` | `#617` denoise 0.25→0.35 | 287.5 | 22360 | 33.96 / 0.917 | 30.03 / 0.803 | 29.3 % |
| `usdu98_tile1024` | `#98` tile whole-frame→1024² | 289.8 | 22136 | 32.71 / 0.901 | 28.97 / 0.793 | 33.2 % |
| `base592_steps60` | `#592` steps 40→60 | 284.4 | 22392 | 17.00 / 0.767 | 18.11 / 0.512 | 86.8 % |
| `face607_dn030` | `#607` denoise 0.45→0.30 | 283.5 | 22296 | 36.62 / 0.928 | 28.09 / 0.768 | 31.3 % |

A structural fact that held for **every** arm: the post-mouth `TAP163` deltas
equal the delivered-frame deltas to 0.01 dB. The eyes stage recomposites only
the small feathered face box, so frame-wide, every change is fully formed
before the eyes stage — and no arm disturbed the eyes-stage skip/run decision.

---

## 2. `#87 ImageBlend` — skin filter blend (shipped 1.0)

**Shipped:** `blend_factor 1.0`, `normal`. By
`comfy_extras/nodes_post_processing.py:44-46` normal mode is
`image1·(1−f)+image2·f`: at 1.0 the output **is exactly** the
`x1_ITF_SkinDiffDetail_Lite_v1`-filtered image (`587:91`); the unfiltered
hand-detailed frame contributes nothing. 0.5 is a straight average. The old
run-2 A/B (`results/ws4/D_skinblend_050`) is superseded (measured on the
no-round-trip graph, later reverted; `#114` at steps 30; misaligned fixed face
box) — this is the re-render on current bytes.

**Cost:** none. 270.3 vs 269.7 s (same window), peak VRAM equal-or-lower.

**Objective:** full 38.48 dB / 2.0 % >8; face 35.19 dB / 7.8 % >8. Frame skin
texture: fine_rms −4.6 % (1.755→1.675), dark pores −10.5 % (5772→5164/Mpx),
bright blobs −9.4 % (59.8→54.2/Mpx) — the filter's fine-grain layer at half
amplitude, exactly as the linear mix predicts.

**Sight-read (describe only):** same composition to the pixel outside
texture; freckles, moles, necklace, hair identical. The 0.5 tiles are
smoother — the salt-and-pepper micro-speckle across chest and cheeks is
roughly halved; freckles persist; no seams or artifacts.

**Recommendation:** the cleanest menu knob found — "skin grain strength" at
`#87.blend_factor` (1.0 ships / 0.5 / 0.0), zero time, zero VRAM, one widget.
Changing the shipped default is a look call on the sheet — the owner's, not
mine. n=1.

---

## 3. `#617 UltimateSDUpscale` denoise (shipped 0.25)

**Shipped, confirmed from the file:** denoise 0.25, 25 steps, cfg 4.5,
dpmpp_2m_sde/karras, ×1.25, tile 896×1152 (grid 2×2 per its own log lines),
seam_fix NONE. This is the pass R4 identified as the amplifier behind D1.

**Cost:** none measurable — 287.1/287.5 s vs sibling post-yield arms
283.5–289.8 s (denoise does not change the step count).

**Objective, both directions:**

| | 0.15 | 0.25 (ships) | 0.35 |
|---|---|---|---|
| face PSNR / >8 vs ships | 31.41 dB / 16.1 % | — | 30.03 dB / 29.3 % |
| frame fine_rms | 1.715 (−2.3 %) | 1.755 | 1.741 (−0.8 %) |
| frame pores /Mpx | 5631 (−2.4 %) | 5772 | 5376 (−6.9 %) |
| frame blobs /Mpx | 63.2 (+5.7 %) | 59.8 | 56.6 (−5.4 %) |

Note the asymmetry: 0.35 moves the face nearly twice as far as 0.15
(29.3 % vs 16.1 % beyond 8 levels) — more re-diffusion compounds harder
through the downstream passes.

**Sight-read:** same composition both directions (face centre within 2 px).
0.15 reads slightly softer/flatter in skin micro-contrast than ships; 0.35
reads slightly more contrasty with marginally more visible spot/mole events
on the chest patch; neither shows artifacts or structure changes. The
differences are subtle at 1:1 — sheet inspection is genuinely needed.

**Recommendation:** menu item "first-upscale strength" (0.15 / 0.25 ships /
0.35). No timing or VRAM cost either way. If the owner's D1 concern ("face
crunchiness") ever resurfaces, 0.15 is the arm that attenuates what `#617`
amplifies — but that is a look call; both pairs are on the sheet. n=1 per
cell.

---

## 4. `#98` whole-image tiling — QUESTIONS Q8 **ANSWERED** (shipped: tile = frame)

**What actually happens (log + source, no longer inference):** the 512×512
widgets never execute — `tile_width/height` are wired from `587:99
GetImageSize`, so the tile equals the whole pre-upscale frame. Both from the
main 18188 log and from my baseline's own server log:
`Canva 2688x3456 / Image 1792x2304 / Tile size: 1792x2304 / Tiles amount: 4 /
Grid: 2x2 / Seams fix: NONE`. Each of those 4 diffusion calls samples at
**1856×2368** (`ultimate-upscale.py:157-158`) ≈ 4.4 MP — and tile size tracks
whatever resolution the buyer renders, which is Q8's VRAM concern.

**The arm** (`tile_width=tile_height=1024`, replacing the `#99` links; `#99`
falls out of execution): its log reads `Tile size: 1024x1024 / Tiles amount:
12 / Grid: 4x3` with `#617` untouched — single variable confirmed in
execution.

**VRAM, measured (2 s sampling, per-pid, node-window attribution):**

- `#98` window: **18,776 → 12,856 MiB (−5.9 GiB)**, and the two following
  windows (`620:137`, `620:110`) dropped from 18.8/16.5 GiB to 10.2 GiB.
- Run peak: unchanged (22,136 vs 22,328 MiB) — on this box at this resolution
  **the run peak lives in the eyes/final stage, not in `#98`**. Fixed tiles
  cap the `#98` hump (making it resolution-independent); they do not lower
  this graph's peak on this composition. Both facts matter for a product
  shipped to unknown hardware; n=1.

**Timing:** 289.8 s vs 283.5–287.5 s siblings — the 12-tile sampling (2-step
LCM per tile) costs nothing measurable. The ~88 s ESRGAN phase inside `#98`
is untouched by tile size.

**Seams — the kill criterion — probed objectively:** gradient band/flank
ratio at every tile boundary (x=1024,2048; y=1024,2048,3072), arm vs
baseline, plus off-boundary controls (`usdu98_tile1024/seam_probe.json`).
Baseline ratios ~0.98–1.01; tile-arm ratios **0.70–0.83** — no ridge at any
boundary; boundaries are marginally *smoother* than flanks (mask_blur 12
signature), the opposite of a seam. Sight-read agrees: the chest patch
straddles x=1024 and shows no line; the face (which straddles y=~282–720, no
boundary) is seam-free; skin reads comparable to baseline, slightly smoother.

**Why the face still moved 33 % >8:** retiling changes the noise/crop
geometry of the whole substrate that the face/mouth passes then re-diffuse —
composition is identical (face centre 2.1 px), texture re-rolls. It is a
different-but-equivalent-looking render of the same image, not a degraded one
— but that equivalence judgement is the owner's, from the sheet.

**Recommendation:** the strongest candidate here for an actual default
change: fixed 1024 tiles make `#98`'s VRAM independent of buyer resolution,
cost nothing in time, and show no seams at denoise 0.08 — on n=1. Before any
default change: one repeat at a higher base resolution (the case Q8 worried
about) to confirm the hump-capping holds where it matters, and the owner's
eye on the sheet. Until then it is a safe menu item.

---

## 5. `#592 KSampler` steps 40 → 60 (shipped 40)

**Cost:** +8–14 s within its window (284.4 s; the 20 extra steps of the base
pass at 896×1152 are cheap on this GPU). VRAM unchanged.

**Objective:** this arm is **not a refinement — it is a different render.**
Full frame 17.0 dB / 82.7 % >8; face 18.1 dB / 86.8 % >8; face centre moved
23.9 px; global tone warmed (median RGB [126,88,67]→[144,105,78]); frame
fine_rms +56 % (1.755→2.734), blobs +55 %, pores +7 %.

**Mechanism (source-level, not speculation):** `dpmpp_2m_sde` is an SDE
sampler — changing the step count changes the entire stochastic trajectory,
not just convergence; and `#600 KSamplerAdvanced` afterwards re-noises from
step 66/1000 regardless. There is no "same image, more converged" to be had
from this lever on this sampler.

**Sight-read:** same subject and pose, but the dress strap position, necklace
routing, freckle field and overall warmth all differ — a sibling image.
Freckles and texture read stronger/warmer than baseline.

**Recommendation:** do **not** present "+50 % steps" as a quality upgrade in
the menu — it is a re-roll switch with a time cost. If the owner wants
variation, the seed already provides it honestly. The one menu-honest framing
would be "alternate render of the same prompt", and the seed does that for
free. n=1, but the mechanism is structural.

---

## 6. `#607 FaceDetailerPipe` denoise 0.45 → 0.30 (shipped 0.45; the pass stays — settled)

**Cost:** none (283.5 s, sibling window 283.5–289.8; VRAM unchanged).
Trap #11 check: its `Detailer: segment upscale` line is unchanged between
arms (crop (531,694) ×1.845 → (979,1280) both) — denoise moved, sampled
resolution did not.

**Objective:** face 28.09 dB / 31.3 % >8 — for a *face-only* lever this is
the largest face movement of the non-steps arms (compare: `#617`±0.10 gave
16–29 %). Downstream compounding is visible outside the face too (frame
3.8 % >8, chest texture shifts): `#607` output feeds sg0's hand/skin/upscale
chain, so the whole frame re-rolls slightly. Face-mask texture (coarse):
blobs 263→247, pores 12887→12591, fine_rms 4.12→4.02.

**Sight-read:** identical composition (1.8 px); the 0.30 face reads slightly
softer/more even on the cheeks with marginally fewer freckle-scale events
than ships; eyes/mouth structure unchanged.

**Recommendation:** viable menu item ("SDXL face pass strength" 0.30 / 0.45
ships). The 0.60 direction was not spent an arm (budget) and remains
unmeasured. n=1.

---

## 7. Facts the owner did not ask for but should have on file

- **Peak VRAM of the whole graph is set by the eyes/final stage (~22.3 GiB
  window), not by either USDU** — every arm, both windows. The `#98`
  whole-frame tiling is a *scaling* risk (tile tracks buyer resolution), not
  the current peak on this box/resolution.
- **`#617`'s own log:** tile 896×1152, grid 2×2, per-call 960×1216 — already
  reasonably tiled; its VRAM window is 12.8 GiB.
- The eyes stage contributes nothing measurable frame-wide in any arm
  (tap ≈ final everywhere) — its output is the feathered face recomposite.
- Timing across all arms sits at 269.7–289.8 s cold with a uniform +14–20 s
  environmental offset between the two session windows; no lever cost
  measurable time except `steps60` (+~14 s within-window, the only arm that
  adds NFE).

## 8. What was NOT measured

- `#607` denoise 0.60 (one direction only was spent).
- `#98` fixed tiles at any resolution other than the shipped ladder; the
  higher-resolution repeat is the confirming experiment for Q8's VRAM story.
- Any second sample of anything (n=1 per cell, one composition, one seed).
- No image was judged for quality by me anywhere — descriptions only; the
  sheets are the deliverable and the look is the owner's.
