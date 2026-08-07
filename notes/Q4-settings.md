# Q4 — other shipped settings: what is leaving quality on the table

**STATUS: PARTIAL — 2 of 7 arms rendered.** Q4 yielded the GPU queue to the
track-1 fresh-install gate on the orchestrator's instruction (flock is not
FIFO; three Q drivers re-acquiring in a loop can starve the gate). The driver
was stopped while blocked in `flock` — holding no lock, no server booted, no
partial evidence — and resumes on the sentinel
`/workspace/nsfw-fix/.track1_gate_done`. Completed arms are unaffected: fresh
process per arm means a pause between arms cannot contaminate anything.

**Rendered:** `baseline_ships`, `blend87_050`.
**Built, graph-diffed, UNMEASURED:** `usdu617_dn015`, `usdu617_dn035`,
`usdu98_tile1024`, `base592_steps60`, `face607_dn030`. Nothing below makes any
claim about those five beyond static facts.

Everything here is n=1 per cell unless marked otherwise. Descriptions of images
are sight-reads, never quality verdicts — the owner judges the sheets.

---

## 0. Method, and one deviation from the protocol text

Per `notes/Q-PROTOCOL.md`: every GPU step under an exclusive flock on
`.gpu_lock`; a FRESH `/venv/main/bin/python main.py --port 19188` per arm
(never 18188), `--disable-xformers` matching every production server on this
pod; output to `/workspace/trackQ/output`; server killed and port confirmed
quiet before the lock releases. Cold is by construction and verified:
**every rendered arm reports `execution_cached: []`** in its history entry
(recorded in `meta.json.cached_nodes`). VRAM ≥ 50 GB gate checked before boot.

**Deviation, recorded with proof.** The protocol names
`results/run3/guard/api_guarded.json` as "the current shipping bytes, guarded
conversion". Measured this session, that file predates two shipped
output-changing fixes: `620:648.max_value` 1.7M→4M (mouth ceiling, `07d61b2`)
and `622:664 FeatherMask` → `622:418.mask` (eyes feather, `72f95ba`). Arms are
built instead from **`api_final.json`** in the same directory, which differs
from the buyer-verified conversion
(`results/run3/fresh/fresh-buyer-api_graph.json`) in exactly the four
buyer-typed inputs. The builder **asserts** the finished baseline equals the
fresh-buyer graph except `619:603.pick_list` `""`→`"0"` (selector
short-circuit, standing practice) and the added `TAP163` SaveImage on
`621:163` (post-mouth tap, same as r3.py). Assertion output is in the build
log; the graphs are the proof.

Mutation path is `r3.py::guarded_graph`'s: `v_mk.norm`, `v_mk.set_loras`
(lunaskye on `#618`, luna on `#116`), buyer `#483` batch data and `#106` face
prompt copied from the fresh-buyer graph, seed 12345 fixed, all sampler seeds
`fixed` (R4 §3). Each arm's submitted graph is diffed against the baseline
with `tools/graph_diff/graph_diff.py`; every diff shows **exactly the intended
inputs and nothing else** (`<arm>/graph_diff_vs_baseline.txt`).

Traps honoured: deltas are measured on the delivered `505` frame — the slot
wired downstream (STATE.md trap #10) — with the `TAP163` tap kept for
attribution; `Detailer: segment upscale` and USDU tiling lines are extracted
from each arm's own server log rather than inferred from widgets (trap #11);
no rendered-output hashing is used as verification anywhere — inertness claims
rest on graph diffs only, pixel numbers are descriptive.

**Licences:** no arm recommends any model file. All seven graphs reference
only files already in the shipped pack. The protocol's licence-flag
requirement is therefore not triggered; nothing under
`results/run4/quality/licences/` is Q4's.

**Face crops** are detected per image with the graph's own
`bbox/face_yolov8m.pt` on CPU (never the WS4 hardcoded square). Texture
figures use R4's instrument verbatim (blobs/pores/fine_rms/blob_rms over a
skin mask fixed from the baseline) so they sit on the same scale as
`notes/R4-defects.md` — but note the compositions differ, so compare
directions, not absolute values, across reports.

Evidence per arm under `results/run4/quality/Q4/<arm>/`: `api_graph.json`
(submitted), `history.json` (verbatim entry incl. `execution_cached`),
`n505__*.png` + `nTAP163__*.png`, `server.log`, `vram_samples.json` (2 s
cadence, per-pid), `ws.json` (timestamped node stream), `meta.json` (summary +
log extracts + VRAM attribution). Sheets under
`results/run4/quality/Q4_sheets/` (1:1 verified; baseline tile marked).

---

## 1. `#87 ImageBlend` — the skin filter blend — **MEASURED**

**Shipped:** `blend_factor 1.0`, mode `normal`. By
`comfy_extras/nodes_post_processing.py:44-46`, normal mode is
`image1·(1−f) + image2·f`, so at 1.0 the output **is exactly** `587:91` — the
`x1_ITF_SkinDiffDetail_Lite_v1` filtered image — and `image1` (the
hand-detailed, unfiltered frame from `587:92`) contributes nothing. 0.5 is a
straight average. The old run-2 A/B (`results/ws4/D_skinblend_050`) is
superseded three ways: it was measured against the no-round-trip graph (later
reverted), at `#114` steps 30/denoise 0.8, with the misaligned fixed face box.
This is the re-render on current bytes the owner asked for.

**Arm `blend87_050`** (`blend_factor 0.5`): success, **270.3 s** vs baseline
269.7 s — no measurable time cost, as expected (the filter model runs either
way; only the mix changes). Peak VRAM 21,752 vs 22,328 MiB (same profile).
Healthy: flat_frac 0.0128, median RGB [127,91,68].

Objective deltas vs baseline (n=1 pair, fixed seed; run-to-run noise on this
pipeline was exactly zero in R4's controls, but that was that graph/session —
not re-proven here):

| | full frame | face crop (332×438 det.) |
|---|---|---|
| PSNR / SSIM | 36.63 dB / 0.9358 | 35.19 dB / 0.9078 |
| mean abs / max | 2.20 / 155 | 3.26 / 94 |
| >1 level / >8 levels | 63.7 % / 5.3 % | 88.1 % / 7.8 % |

(Full-frame figures from `metrics.json`; the change is frame-wide by
construction and then **compounds through the downstream passes** — `#98`,
colormatch, face `#114`, mouth `#165`, eyes — which is why the face, 800 px
above the measured skin patch, moves at all. The TAP163 pair confirms the
difference is already present pre-eyes.)

R4 texture instrument over the frame-wide skin mask (2.90 Mpx, fixed from
baseline): fine_rms 1.755 → 1.675 (−4.6 %), dark pores/Mpx 5772 → 5164
(−10.5 %), bright blobs/Mpx 59.8 → 54.2 (−9.4 %). Face-mask (0.061 Mpx):
blobs 263 → 181 (−31 %), pores ≈ unchanged (12887 → 12854), fine_rms 4.12 →
3.82.

**Sight-read** (describe, not judge): same composition, freckle and mole
layout identical, necklace and hair structure unchanged. The 0.5 tiles are
visibly smoother: the fine salt-and-pepper micro-speckle across chest and
cheeks is roughly halved in amplitude; freckles persist; no seams, no
artifacts, no structural change. Sheets:
`Q4_sheets/Q4_face_sheet1of1.png`, `Q4_sheets/Q4_skin_sheet1of1.png`.

**Recommendation (menu item):** expose `#87.blend_factor` as the "skin grain
strength" knob — 1.0 (ships) / 0.5 / 0.0 with the descriptions above. Free:
zero time, zero VRAM, one widget. If the owner prefers 0.5 as default, that is
an output-changing default and needs his eye on the sheet, not mine.

---

## 2. `#617 UltimateSDUpscale` denoise — **UNMEASURED (arms built)**

**Shipped, confirmed from `api_guarded.json`/`api_final.json`:** denoise
**0.25** (stored 0.25000000000000006), 25 steps, cfg 4.5, dpmpp_2m_sde/karras,
upscale_by 1.25, tile 896×1152, seam_fix NONE. This node re-diffuses the whole
frame right after the base generator + SDXL face pass; the R4/D1 record shows
its denoise is the amplifier that turned the "inert" VAE round-trip into a
30 dB change, which is why it earned two arms.

Arms `usdu617_dn015` (0.15) and `usdu617_dn035` (0.35): built, single-input
graph-diffs on record. **No render yet; no expectations stated.** Baseline
`#617` VRAM window 12,822 MiB; tile sampling ~12 s of the ~55–90 s the node
spends (the rest is the 4x-UltraSharp model pass), so neither arm should move
time much — that is a prediction to check, not a result.

---

## 3. `#98` whole-image tiling (QUESTIONS Q8) — log question **ANSWERED**, arm **UNMEASURED**

**What actually happens, from logs and source — Q8's mechanics are settled:**

- The 512×512 widgets never execute. `587:98.tile_width/height` are wired from
  `587:99 GetImageSize` reading `587:87`'s output: **tile = the whole
  pre-upscale frame, 1792×2304**.
- USDU then tiles the ×1.5 canvas (2688×3456) as `ceil(3456/2304)=2` ×
  `ceil(2688/1792)=2` → **4 tiles**, each a 1792×2304 region, each sampled at
  **1856×2368** (`ultimate-upscale.py:157-158`: `ceil((tile+padding)/64)·64`,
  padding 32) ≈ 4.4 MP / ~68.7k latent tokens per diffusion call.
- Verbatim from **my baseline's own server log** (and byte-matching lines in
  `user/comfyui_18188.log` from an earlier agent's render of the same bytes):
  `Canva size: 2688x3456 / Image size: 1792x2304 / Tile size: 1792x2304 /
  Tiles amount: 4 / Grid: 2x2 / Seams fix mode: NONE`. First USDU `#617` for
  contrast: `Tile size: 896x1152 / Grid: 2x2`.
- So VRAM in `#98`'s window scales with the buyer's frame, exactly as Q8
  suspected — **but on this box at this resolution the run's peak is not in
  `#98`**. Baseline per-node VRAM windows (2 s sampling, this pod, n=1):
  `#592/#600` base ≈ 7.8–7.9 GiB → `#593` 4x-upscale 12.4 GiB → `#617`
  12.8 GiB → **`#98` 18.8 GiB** → Z-Image face/mouth 19.9 GiB → **eyes/final
  stage 22.3 GiB — the run peak** (first reached in the `622:400` window,
  +266.8 s of 269.7). Attribution is sample-to-node-window matching from the
  ws stream; 2 s cadence, so ±1 window.
- Timing inside `#98`: the tile sampling is ~9–12 s; the ESRGAN
  (4x-UltraSharpV2) phase is ~88 s. Changing tile size cannot touch the ESRGAN
  phase.

**Arm `usdu98_tile1024`** (tile_width=tile_height=1024 constants replacing the
`#99` links; `#99` drops out of execution — it is not an OUTPUT_NODE): grid
becomes 3×4 = 12 tiles at 1088×1088 (~1.2 MP, 18.5k tokens per call). What it
answers when rendered: whether `#98`'s window VRAM drops toward
resolution-independence, what the 12-tile sampling costs in time, and — the
kill criterion — whether visible tile seams appear at denoise 0.08 with
seam_fix NONE. **No render yet.**

---

## 4. `#592 KSampler` steps 40 → 60 — **UNMEASURED (arm built)**

Shipped: 40 steps, cfg 4, dpmpp_2m_sde/karras, denoise 1.0 (wired from
`647:627 PrimitiveFloat = 1`). The base image then passes through `#600`
(KSamplerAdvanced, LCM/TDD window 66→1000, cfg 1) before decode. Arm
`base592_steps60` is the owner's "+50 % steps" menu candidate; single-input
diff on record. **No render yet.**

---

## 5. `#607 FaceDetailerPipe` denoise 0.45 → 0.30 — **UNMEASURED (arm built)**

Shipped: denoise 0.45, 20 steps, cfg 3, guide 1280, crop factor 3 — the first
of the double face detail; the delete question is settled (stays; R4/ws4
showed pass 1 survives into the final image). The arm varies denoise only, per
the owner's menu allowance. Direction 0.30 chosen as the lower-risk lighter
touch; 0.60 was not spent an arm. **No render yet.** The
`Detailer: segment upscale` line from its log will confirm the sampled crop
resolution is unchanged (denoise does not affect crop; trap #11).

---

## 6. Baseline instrumentation (facts, n=1)

- `baseline_ships`: success, **269.7 s** server-side cold — consistent with
  the 271 s the DoD-1 fresh-install gate measured rendering these bytes,
  wall 270.3 s, boot excluded, `execution_cached: []`, peak VRAM
  22,328 MiB, healthy (flat_frac 0.0015 vs poisoned signature ~0.999).
- Face: (812,282)-(1144,720), conf 0.865 — full-body composition, face is
  332×438 of 2688×3456.
- `blend87_050` re-detected within 1–2 px of the baseline box (conf 0.865 both)
  — compositions identical, crops comparable.

## 7. What remains

Five arms render once `.track1_gate_done` appears (driver `render-all` skips
recorded cold successes). Then: metrics + texture for each, VRAM/tile findings
for `#98`, full 7-tile sheets, and this file rewritten with the five open
sections filled and per-lever recommendations completed. Q4 recommends only —
no workflow file, no `OFMTech-NSFW/`, no `dist/` was touched.
