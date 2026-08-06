# P2-RENDER — the face quality grid

**Nothing in this workstream was shipped.** `OFMTech-NSFW/OFMTech_NSFW.json` is
untouched; every arm is a scratch copy of it. The recommendation at the end is a
recommendation, not a change.

**What this evidence is.** A/B renders driven through a modified API prompt,
submitted to `/prompt` over HTTP. It is evidence about **how the face looks**.
It is **not** a claim that the workflow works — that is main's Phase 0 browser
proof of the buyer journey, which pressed the real Run button. My driver never
does, and the two must not be conflated.

Baseline: `master` @ `73f3d5c`, workflow
`sha256 f1ac7e55d375380033f6b0acc67ee0f4706dd618303075f86213fc09e6beb22e` —
**D1 reverted**, `#597`/`#616` present, sg `2. Base Generator (SDXL)` = 28
nodes, all confirmed by reading the file. Arm list, seed, prompt and method:
`results/face/ARMS.md`. Judgement calls: `notes/P2-render-questions.md`.

---

# The headline

**The overbaked face is not "detail turned up too far". It is a whole-frame
re-diffusion at roughly a third of the delivered resolution, pasted back inside
a mask, with a visible edge.** Three independent observations say so:

1. **A hard seam at the face-detector boundary, in the delivered image.**
2. **Removing the first face pass (`#607`) changes nothing about it.**
3. **P3-CFG's before/after tap of `#114`: the input is clean, the output is
   blistered.** (Theirs, not mine — cited because it is the strongest single
   datum and it is not mine to claim.)

---

# Finding 1 — the damage has an edge, and the edge is `#114`'s paste region

Band-pass energy (difference of Gaussians at 1 px and 4 px, RMS in 8-bit
levels) measured in clean bands either side of the jaw, well away from hair and
background:

| arm | detected face box (graph's own `face_yolov8m.pt`) | inside, just above jaw | outside, just below jaw |
|---|---|---|---|
| `A0_baseline` | x800–2228 y696–**2685**, conf 0.903 | **5.87** | **0.87** |
| `A_drop_sdxl_face_pass` | x794–2227 y686–**2677**, conf 0.903 | **6.15** | **0.87** |

A **~7x step in high-frequency energy** across a line that lands on the bbox
the graph's own detector returns, on both arms, with the outside value
identical to two decimal places. Row-by-row, the transition runs from ~7.0 at
y2670 to ~0.85 at y2705 — a ~30-row feather, consistent with `#114`'s
`feather 18` / `noise_mask_feather 20`.

The left edge shows the same step, smaller because that region is hair and
shadow: ~1.0–1.5 outside x800, ~2.4–3.1 inside from x810.

**The picture version of the same fact:**
`results/p2_evidence/A0_baseline_highfreq_map.png` — band-pass energy over
16 px blocks across the whole frame. It is a **bright silhouette of the head on
a near-black body and background**. The neck, shoulders, chest and background
carry no bumps at all; the cheek, temple and mouth are covered
(`results/p2_evidence/A0_baseline_six_regions_1to1.png`, six regions at 1:1).

**What this rules out.** `#87 ImageBlend` runs on the **whole frame**. A
whole-frame filter cannot produce a boundary that follows the face detector's
bbox. It remains possible that `#87` amplifies existing structure and the neck
simply has none to amplify — arm H (`#87` at 0.50) tests that directly by
measuring whether the *neck* moves when the blend moves. But the depositor of
the texture is a face-detailer composite, and arm A rules out `#607`.

**The seam is itself a defect.** It is a visible straight line across the jaw
in the delivered `#505` output, not only a measurement.

---

# Finding 2 — arm A: the D3 re-measurement against the D1-free baseline

**This is the re-measurement the owner asked for by name, and it is a stop
signal. The improvement does not survive, because there was never an
improvement — only a change.**

Arm `A_drop_sdxl_face_pass` removes `#607 FaceDetailerPipe` (SDXL, denoise
0.45) from sg 2 and re-originates link 1232 at `#596[0]`. Graph diff against
the baseline's submitted prompt: **exactly two differences** — `619:607`
removed, `619:597.inputs.pixels` `["619:607", 0]` → `["619:596", 0]`. Nothing
else moved.

**How it looks.** Side by side at 1:1
(`results/p2_evidence/A0_vs_A_drop607_face_1to1.png`): the field of bright
raised bumps is **still there, at the same density, in the same places**. Eye
and eyelash detail shift slightly. The skin complaint is untouched. Asked to
pick the better one I would decline; pressed, I would say the arm-A side is a
touch more stippled.

Supporting numbers, not carrying the argument — bright-blob density over a
fixed skin mask inside the detected face box:

| | baseline | `#607` removed |
|---|---|---|
| bright blobs / megapixel | 764 | **800** |
| blob-band RMS | 4.30 | **4.42** |
| fine-band RMS | 4.23 | 4.38 |
| face-crop PSNR / SSIM vs baseline | — | 31.02 dB / 0.900 |
| face pixels moving > 8 levels | — | 19.8 % |

The change is real. It is not an improvement.

**Timing: no claim, deliberately.** Baseline 397.8 s at **31** cached nodes;
arm A 386.2 s at **11**. Cache states do not match, which is exactly the
condition that produced last run's wrong "+31 % slower". The 11.6 s gap is not
evidence. If the cost of `#607` is wanted, it needs a matched-cache pair or two
cold runs.

**Eye colour: a clean negative.** P1 flagged dE76 7.13 / 8.31 between their B
and C. Arm A moves mean iris Lab by **0.96** (left) and **1.09** (right) —
below their 1.68–3.38 noise band. Removing the SDXL face pass leaves eye colour
alone.

---

# Finding 3 — the mouth is not overbaked, it is destroyed

`results/p2_evidence/A0_baseline_mouth_1to1.png`. At 1:1 the lips and chin
carry a dense overlay of **geometric structures — rectangles, hexagons,
dot-matrix grids, ladder patterns — plus hair-like filaments**, as if a texture
from a different image were composited over them. This is not a subtler version
of the skin complaint; it is a different and worse artefact, and I have not
seen it reported anywhere in this project.

WS4's baseline, rendered from the unmodified shipped prompt at a **wider
framing**, shows the bumps on the chin but **not** the geometric structures.
Detected face box there: 654x891. Mine: 1428x1989.

**Inference, labelled as such:** the severity tracks how large the face is in
frame. `#114` runs `guide_size`/`max_size` **1024** with `bbox_crop_factor 3`,
which on a tight portrait clamps the crop to the full 2688x3456 frame (P3-CFG
measured `cropped_refined` at exactly that). So the whole frame is downsampled
to fit 1024 — about **0.38x** on my composition — re-diffused at denoise 0.80
for 30 steps, and scaled back up ~2.6x. Real pore detail cannot survive that
downsample; the sampler invents replacement texture at low resolution; the
upscale enlarges every invented blob. On WS4's wider framing the same
1024 target is a much gentler ratio.

If that holds, **a buyer shooting close-up portraits gets a materially worse
result than one shooting wider, from the same graph and the same settings.**
Arm E (`guide_size`/`max_size` 1024 → 1808 → 2048) is the test.

The lips are hit by **two** passes at two different working resolutions —
`#114` at 1024 and `#165 Mouth Detailer` at 1808 — which may be why the mouth
is the worst region rather than merely a bad one.

---

# Finding 4 — the graph contains its own counter-example

Read straight out of the converted API graph, so no widget-index arithmetic is
involved:

| | `#114` face | `#165` mouth | `#607` SDXL face |
|---|---|---|---|
| `guide_size` / `max_size` | **1024 / 1024** | **1808 / 1808** | 1280 / 1280 |
| `steps` | **30** | **8** | 20 |
| `cfg` | 1 | 1 | 3 |
| `denoise` | **0.80** | **0.35** | 0.45 |
| `sampler` / `scheduler` | euler_ancestral / kl_optimal | euler_ancestral / kl_optimal | dpmpp_2m_sde / karras |
| `bbox_crop_factor` | 3 | 3 | 3 |

`#114` and `#165` are the **same node class, in the same subgraph, on the same
`zimage.safetensors`, with the same sampler, scheduler and cfg**. The mouth
pass runs at 1808 on a small region with 8 steps and denoise 0.35. The face
pass runs at 1024 on a much larger region with 30 steps and denoise 0.80. Both
of those asymmetries point the same way and neither depends on identifying the
model.

They also survive if the model identification is wrong — which it is not:
P3-CFG hashed `zimage.safetensors` to Z-Image-**TURBO**, a guidance-distilled
model whose own templates use 8 steps. Whoever tuned the mouth used the design
point. The face never got the same treatment.

---

# Widget-index reconciliation, done before any index was written

`/object_info` on the live server: `FaceDetailer` has **28 widgets**, ordered
`guide_size, guide_size_for, max_size, seed, steps, cfg, sampler_name,
scheduler, denoise, feather, …`. `seed` is widget 3, so its synthetic
`control_after_generate` companion occupies **array index 4** and shifts
everything after it. `#114.widgets_values` has **29** entries = 28 + 1. That
reconciles, and each index was then checked against the value actually in the
file:

* index 5 = `steps` → file holds `30` ✓
* index 6 = `cfg` → file holds `1` ✓ (**never touched — cfg 1 is required by a
  guidance-distilled model; at cfg 1 the uncond branch is not evaluated at all.
  P3 owns that question and I have no cfg arm.**)
* index 9 = `denoise` → file holds `0.8` ✓
* index 15 = `bbox_crop_factor` → `3`, and confirmed independently as
  `620:114.inputs.bbox_crop_factor` in the converted API graph, where
  `graphToPrompt` has already done the widget-to-name mapping

`FaceDetailerPipe` is likewise 28 + 1 = 29 and `#607` matches. `ImageBlend` has
2 widgets and `#87` has 2 entries, index 0 = `blend_factor` = `1`. The arm
builder asserts the array length **and** the current value at the index before
writing; a desync aborts the build rather than writing a float into a string
slot.

---

# Method, stated once

* Each arm is a **scratch copy** of the workflow, built by an asserting script.
* Every arm passes `python3 tools/preflight/integrity.py` with **0 problems**
  before submission. All 13 built arms did.
* Each arm is converted to API format by `app.loadGraphData()` +
  `app.graphToPrompt(app.rootGraph)` in a real Chromium against the live
  ComfyUI — the same call the Run button makes — not by hand-editing JSON.
* Each arm's API graph is diffed against the baseline's with
  `tools/graph_diff/graph_diff.py`. **Every arm showed exactly the intended
  difference and nothing else.**
* `inputs.pick_list = "0"` is set on `619:603 INSTARAW_ImageFilter` **in the
  submitted prompt only, identically in every arm**. No arm's workflow file
  contains it. Without it `#603` opens the selector, waits 600 s and aborts.
* `419.inputs.rgthree_comparer` is stripped from every submitted prompt. It is
  a frontend-only widget absent from the node's `INPUT_TYPES`, carrying stale
  preview URLs that differ per browser session; stripping it makes all arms
  identical on that node. It changes no executed node's inputs.
* Same seed (**12345**, `seed_control: fixed`) and same prompt in every arm.
* Both LoRA stacks at the shipped `"None"` in every grid arm.
* `execution_cached` is read from `/history` for every arm and recorded in its
  `meta.json`. **Arms whose cache state does not match are not compared on
  time.**
* **No `POST /api/interrupt`. No `POST /api/queue {"clear": true}`.** The
  server is shared; other agents' work was never at risk from this workstream.
* **Hash comparison of rendered output is not used as a verification method
  anywhere in this report.**

## One caveat that applies to every arm equally

`#114`'s positive conditioning is `#106 CLIPTextEncode` =
`"TRIGGER, PROMPT FOR YOUR MODEL"`, a placeholder. At cfg 1 the uncond branch
is not evaluated, so **that placeholder is the entire steering signal** for 30
steps at denoise 0.80. It is a **constant across my whole grid**, so relative
comparisons between arms are valid — but my **absolute baseline may be worse
than a buyer's would be** if they typed a real prompt there. P3 is testing that
variable; I am not duplicating it.

---

# Arms and results

Renders land into `results/face/arms/<arm>/` — PNG, `api_graph.json`,
`meta.json` (`arm`, `changed`, `prompt_id`, `exec_seconds`, `cached_nodes`).
P2-SHEET builds the owner's contact sheets from exactly that layout.

## The grid

`blobs/mpx` = bright convex blobs per megapixel over a **single skin mask
computed once from the baseline and reused for every arm** — the defect.
`pores/mpx` = dark fine minima over the same pixels — the texture the owner
wants. `seam` = ratio of band-pass RMS just inside the detected face box to
just outside it, across the jaw; 1.0 would mean no visible composite edge.

| arm | changed | blobs/mpx ↓ | pores/mpx ↑ | seam ↓ | exec | cache |
|---|---|---|---|---|---|---|
| `A0_baseline` | — | **764** | 16 471 | 6.76 | 397.8 s | 31 (0 heavy) |
| `A_drop_sdxl_face_pass` | `#607` removed | 800 | 16 286 | 7.10 | 386.2 s | 11 (0 heavy) |
| `D_skinblend_075` | `#87` 1 → 0.75 | 702 | 17 548 | 6.31 | 292.0 s | 57 (10 heavy) |
| `H_skinblend_050` | `#87` 1 → 0.50 | 702 | 17 906 | 5.96 | 291.6 s | 57 (10 heavy) |
| `C_zface_steps_16` | steps 30 → 16 | 552 | 19 339 | 5.45 | **224.1 s** | 57 (10 heavy) |
| `B_zface_denoise_065` | denoise 0.80 → 0.65 | 465 | 19 241 | 4.97 | 290.8 s | 57 (10 heavy) |
| **`C_zface_steps_08`** | **steps 30 → 8** | **239** | **23 213** | 3.57 | **294.1 s** | 8 (0 heavy) |
| `B_zface_denoise_050` | denoise 0.80 → 0.50 | **157** | 23 050 | 3.35 | 291.6 s | 57 (10 heavy) |
| `B_zface_denoise_035` | denoise 0.80 → 0.35 | **62** | 24 810 | 2.40 | 290.7 s | 57 (10 heavy) |

Both ladders are **monotonic** and the two columns move in **opposite
directions** — fewer invented blobs *and* more genuine fine pore detail. That
is the signature of the pass no longer fabricating lesions, not of a smoothing
filter, which would drop both.

## Timing: what can and cannot be said

`execution_cached` was read for every arm, and then — because a bare count is
not enough — I checked **which** nodes were cached. Two clean regimes:

* **0 heavy nodes cached** (`A0_baseline`, `A_drop_sdxl_face_pass`,
  `C_zface_steps_08`): every sampler, detailer, VAE node and upscaler ran from
  scratch. Only loaders and text encoders were warm.
* **10 heavy nodes cached** (all six others): `KSampler`, `KSamplerAdvanced`,
  `FaceDetailerPipe`, `UltimateSDUpscale`, `ImageUpscaleWithModel` and 4 VAE
  nodes — the whole base generator served from cache.

**Comparisons only within a regime.**

* Warm regime, identical 57/10 cache state: `#87` at 0.75 → **292.0 s**, `#87`
  at 0.50 → **291.6 s**, denoise 0.50 → **291.6 s**, denoise 0.65 → 290.8 s,
  denoise 0.35 → 290.7 s, **steps 16 → 224.1 s**. Halving *steps* saves
  **67.5 s**; halving *denoise* saves **nothing**.
* Cold regime: baseline **397.8 s** vs steps 8 **294.1 s** = **−103.7 s
  (−26 %)**, and `C_08` additionally had 23 *fewer* loaders warm, so that is a
  **lower bound**.
* `A_drop_sdxl_face_pass` 386.2 s vs baseline 397.8 s: cache counts 11 vs 31,
  both 0 heavy. I make **no timing claim** for removing `#607`.

**Why denoise is free, from the source.** `comfy/samplers.py`,
`KSampler.set_steps`: when `denoise < 1` it computes
`new_steps = int(steps/denoise)`, builds that longer schedule, and keeps
`sigmas[-(steps + 1):]`. The executed step count is **always `steps`**. Denoise
moves *where on the schedule* the pass starts, at identical cost. Measured and
explained agree.

## What each lever actually does

**`#607` (the SDXL face pass, arm A) — not the problem.** Removing it leaves
the bumps at the same density (764 → 800) and the seam unchanged (6.76 →
7.10). Full write-up in Finding 2.

**`#87` (the skin amplifier) — not the problem, and this is a disproof rather
than an absence of evidence.** Halving it moves the defect 8 % against steps'
69 %. The alternative I had left open was that `#87` reaches the neck but finds
nothing to amplify there. It does reach it: changing `blend_factor` moves neck
and shoulder pixels by **mean 1.6–2.5 levels, max 15, 0.13–1.70 % over 8
levels**. And yet neck band-pass RMS is **0.94 / 0.99 / 0.96** at blend 1.0 /
0.75 / 0.50 — flat. It reaches the neck, changes it, and creates no bumps
there. P3-CFG reached the same verdict from a before/after tap inside a single
run; these are two independent routes.

The two families are also separable by the *variance* of the change they cause
outside the mask, which identifies the mechanism:

| arm | neck delta, signed mean / std per channel | reading |
|---|---|---|
| `C_zface_steps_08` (`#114` only) | −0.90/0.30, −0.92/0.27, −0.77/0.42 | near-uniform offset |
| `C_zface_steps_16` (`#114` only) | −0.62/0.49, −0.03/0.18, −0.29/0.45 | near-uniform offset |
| `D_skinblend_075` (`#87`) | +0.25/1.98, +0.12/2.31, +0.27/2.15 | per-pixel |
| `H_skinblend_050` (`#87`) | −0.14/2.30, −0.76/2.91, +0.78/2.23 | per-pixel |

So **a change confined to `#114`'s mask still moves every pixel of the
delivered image** — by about one level, uniformly — through the downstream
global `ImageColorMatch+` nodes, not because the pass wrote outside its mask.

**`#114 steps` — the strongest single lever, and the only one that also saves
time.** 30 → 16 is not enough (552 blobs/mpx, still visibly speckled). 30 → 8
takes it to 239 and reads as skin.

**`#114 denoise` — the strongest lever on the defect, and free.** 0.65 → 0.50 →
0.35 gives 465 → 157 → 62 blobs/mpx at zero time cost. At 0.35 it is very
clean but starting to look waxy, and the freckles fade.

**`#114 guide_size` / `max_size` — inert. Do not touch them.** Verified in
`ComfyUI-Impact-Pack/modules/impact/core.py:287-325` with the bbox from the
server log (1297x1833) and crop region 2688x3456: `guide_size_for` is `True`
so `upscale = guide_size / min(bbox_w, bbox_h)`; guide 1024 gives 0.789 and
`force_inpaint` clamps `upscale <= 1.0` to exactly 1.0. Raising the pair is
**self-cancelling**: guide 1808 gives 1.394, but `new_h = 3456 x 1.394 = 4818`
exceeds `max_size 1808`, so the safeguard multiplies by `1808/4818` → 0.523 →
clamped to 1.0 again. Guide 2048 → 1.579 → 0.593 → 1.0. Raising `guide_size`
alone against a large `max_size` *would* engage and would sample **more**
pixels (1808 with max_size 4096 → 3186x4096 ≈ 13 MP). There is no setting of
that pair that lowers the working resolution. **`bbox_crop_factor` is the only
lever that can.** Two arms testing it are in the grid.

## The seam is a separate defect and no arm removes it

The composite edge at the face-box boundary tracks the bump density but never
goes away: 6.76 baseline, 5.45 at steps 16, 3.57 at steps 8, 3.35 at denoise
0.50, 2.40 at denoise 0.35. Even the cleanest arm leaves the pasted region
**2.4x** more textured than the skin 40 rows below it, with a straight
horizontal transition across the jaw. Lowering the settings makes the pasted
region less unlike its surroundings; it does not stop it being a paste.
**Whatever is decided about steps and denoise, that boundary wants its own
fix** and it is visible in the delivered `#505` output.

## The gold lower-lip artifact did not reproduce

P1-ANALYSIS found a ~16x12 px gold object below the lower lip in WS4's
`D_skinblend_050`, segmented by `(R+G)/2 − B > 65` — 54 px there against 0 in
their other three arms. I reproduced their measurement exactly on the WS4
images (54 / 0 / 0 / 0) so the object is certainly in that render.

It does **not** reproduce here. Across every arm, in three windows — P1's
literal `x1371-1386 y1183-1194`, my composition's actual sub-lip window
`x1420-1640 y2355-2430`, and the whole mouth `x1300-1800 y2150-2450` — the
count is **0 px**, including `H_skinblend_050`, which is P1's exact setting.
The only arms with *any* yellow pixels in the mouth region are
`A_drop_sdxl_face_pass` (10 px) and `C_zface_steps_08` (12 px), **neither of
which touches `#87`**.

So "the blend change reliably provokes it" is not supported. It occurred once,
on one composition and one prompt. The reason to leave `#87` alone is simply
that turning it down does not fix the skin.

## Eye colour: lightness, not hue

Mean iris Lab over a fixed window, and dE76 against the baseline:

| arm | L* | a* | b* | dE76 |
|---|---|---|---|---|
| `A0_baseline` | 24.16 | 4.24 | 5.96 | — |
| `D_skinblend_075` | 24.53 | 4.14 | 6.11 | 0.41 |
| `A_drop_sdxl_face_pass` | 23.34 | 4.00 | 5.52 | 0.96 |
| `H_skinblend_050` | 25.79 | 4.30 | 6.50 | 1.72 |
| `C_zface_steps_16` | 26.97 | 4.35 | 6.12 | 2.82 |
| `C_zface_steps_08` | 27.44 | 5.15 | 5.76 | 3.40 |
| `B_zface_denoise_065` | 27.81 | 4.36 | 6.31 | 3.67 |
| `B_zface_denoise_050` | 29.88 | 4.06 | 5.63 | 5.73 |
| `B_zface_denoise_035` | 31.56 | 4.06 | 5.39 | 7.42 |

**a\* and b\* barely move at all** (4.0–5.2 and 5.4–6.5 across the whole grid).
The entire change is in **L\***, which rises monotonically as the pass is
weakened: the iris gets **lighter**, it does not change colour. Read the other
way round: the shipped 30-step / 0.80 pass is **darkening the eyes** relative
to what the base generator produced. Removing `#607` leaves them alone (0.96).


---

# Six arms are void, and a control is why I know

**A byte-identical resubmission of an arm that had already succeeded came back
broken.** That is the whole finding, and it invalidated two conclusions I had
already drawn and one I was about to send.

At **02:11:21** the server logged, inside a Z-Image face pass that was **not
mine** (bbox 1297x1833, 30 steps, one of P3-CFG's isolated runs):

```
[Impact Pack] vae decoded in 22.5s
ComfyUI-Impact-Pack/modules/impact/utils.py:155: RuntimeWarning:
  invalid value encountered in cast
  return Image.fromarray(np.clip(255. * image.cpu().numpy()...).astype(np.uint8))
```

That is **NaN reaching `tensor2pil`**. Every arm of mine that ran *before* that
timestamp succeeded. Every arm that ran *after* it came back with the face
replaced by a flat region of **RGB (53, 47, 43)** covering **23.5 %** of the
frame — the same constant and the same coverage in all of them, which is
consistent with an all-zero latent being VAE-decoded.

| arm | finished | result |
|---|---|---|
| `B_zface_denoise_035` | 01:59:04 | clean |
| **— NaN in another workstream's run —** | **02:11:21** | |
| `CF_crop_1.5` | 02:16:19 | flat face |
| `CF_crop_1.0` | 02:18:38 | flat face |
| `X_steps08_denoise050` | 02:21:34 | flat face |
| `X_steps08_denoise065` | 02:24:30 | flat face |
| `L0_baseline_loras` | 02:30:38 | crash at `622:403 MaskBoundingBox+` |
| `L1_steps08_loras` | 02:33:31 | crash at `622:403 MaskBoundingBox+` |

**The control.** `Z_control_steps08_repeat` resubmits `C_zface_steps_08`'s own
`api_graph.json`. The two files compare equal and hash to the same
`906fb53bcddf57bb`. The original ran at 01:30 and produced the best face in the
grid. The control ran at 02:38 and produced the flat face — differing from the
original by mean **35.7 levels** with **95.2 %** of pixels over 8. Same graph,
same seed, 68 minutes apart.

**So the six arms above are `void`, not failed.** Each is marked
`"void": true` with a reason in its `meta.json` so no contact sheet shows a
faceless tile as a result.

## Two conclusions I retracted

1. **"`bbox_crop_factor` 1.5 and 1.0 are catastrophic."** Wrong. That lever is
   **unmeasured**, not closed.
2. **"Loading the buyer's LoRAs crashes the shipped graph."** Not established.
   The `RuntimeError: min(): Expected reduction dim to be specified for
   input.numel() == 0` at `622:403 MaskBoundingBox+` came after the graph's own
   YOLO logged `no detections` twice — which is what a featureless region gives
   you. I held this one back and I am glad I did; it would have been the
   biggest product claim of the run and it would have been false.

**What tipped me off was not a better theory.** It was that **four different
parameter changes produced a bit-identical constant**, which no story about
parameters can explain. I had a plausible mechanism, a log line that fit it and
two arms agreeing — all of it wrong. One resubmission of a file already on disk
settled it in five minutes.

## One real defect this did surface

`622:403 MaskBoundingBox+` in the Eyes stage has **no empty-mask guard**. When
`#424 BboxDetectorSEGS` finds no face, `#407 SegsToCombinedMask` yields an empty
mask and `MaskBoundingBox+` calls `min()` on a zero-element tensor and throws.
So *anything* that makes the face undetectable — a bad model state, an unusual
crop, an unlucky prompt — turns into a **hard crash with no image**, rather than
a degraded one. That fragility is in the shipped graph independently of what
triggered it here, and it is worth a guard. I am **not** claiming to know how
often a buyer would hit it.

---

# The recommendation

## Ship `#114 FaceDetailer` `steps` **30 → 8**. Nothing else.

`OFMTech-NSFW/OFMTech_NSFW.json`, subgraph `5. Face & Mouth Detail (Z-Image)`,
node `#114`, `widgets_values[5]`. One integer.

**Why, in plain language about the skin.** In the shipped render the cheeks,
nose, brow and temple are covered in small **bright, raised, whitish bumps with
shiny tops**, packed edge to edge, with a few larger red-brown lesions among
them. They are the wrong shape to be pores: a pore is a tiny *dark dent*, and
these are *convex and light*. The freckles the prompt asks for are in there
somewhere but they are drowned. At 30 steps the mouth is worse still — the lips
and chin carry grids, hexagons and dot-matrix patterns that look like a
photograph of a circuit board laid over the face.

At 8 steps that field is gone. The skin reads as skin: soft, with fine texture,
and the freckles come back as **flat brown marks on the nose and cheek** — the
thing that was asked for. The lips look like lips again. The eyelashes are
strands instead of scribble. It is a little softer than the shipped render, and
someone hunting for grain will notice; but the grain it loses was never pores,
it was damage.

**16 is not a compromise, it is a third of the problem left in.** I rendered it
specifically to find a middle ground and it does not provide one — 552
blobs/mpx against the baseline's 764, and at 1:1 the white speckle is still
plainly there with a blemish on the nose.

**And it is faster.** 294.1 s against the baseline's 397.8 s — **−103.7 s,
−26 %** — with every sampler, detailer and VAE node running from scratch in
both, and 23 *more* loaders to warm in the faster arm. So that figure is a
**lower bound**. The matched-cache pair agrees: 30 → 16 steps alone saved
67.5 s. **This change makes the face better and the render faster, and those
two things almost never point the same way.**

## The alternative, if the owner wants cleaner still

`#114 denoise` **0.80 → 0.50** scores better on the defect than steps 8 (157
blobs/mpx against 239) and **costs nothing in time** — `comfy/samplers.py`
`KSampler.set_steps` always builds `steps + 1` sigmas, so denoise moves where on
the schedule the pass starts without changing how many steps run. To my eye it
is slightly waxier than steps 8 and it lightens the iris more (dE76 5.73 against
3.40, all of it in `L*`). **0.35 is too far** — very clean, but the freckles
start to disappear.

The combination — steps 8 **and** denoise 0.50 — is the obvious next thing to
look at and **I could not test it**: both attempts are void. It should be the
first render of the next session.

## Where I could not tell, and where I would not guess

* **Whether 8 is softer than the owner wants is his call, not mine.** I can say
  the defect is gone and the freckles are back. I cannot say whether he wants
  more grain than that, and the honest answer is that the contact sheet should
  decide it, not me.
* **The LoRA configuration is unconfirmed.** Both confirmation arms are void.
  Everything I measured is with both stacks at the shipped `"None"`.
* **Every arm shares the `"TRIGGER, PROMPT FOR YOUR MODEL"` placeholder** on
  `#106`. At cfg 1 that is the entire steering signal. It is constant across the
  grid so the comparisons hold, but my absolute baseline may be worse than a
  buyer's who typed a real prompt. P3 owns that variable.
* **One prompt, one seed, one composition** — a tight head-and-shoulders
  portrait. The defect is worse the larger the face sits in frame.

## What not to do

* **Do not remove `#607`.** Measured, twice now. It does not fix the skin.
* **Do not touch `#87 ImageBlend`.** Measured. 8 % against steps' 69 %, and the
  neck test shows it is not the cause.
* **Do not touch `#114 guide_size` / `max_size`.** Inert, and self-cancelling if
  raised — read from `impact/core.py`, not from a render.
* **Do not raise `#114 cfg`.** Not my lane, and the model is guidance-distilled.

## Two things that still want fixing and are not mine to fix

1. **The composite seam.** Every arm leaves a visible straight edge across the
   jaw where the detailer's paste region ends — band-pass energy 6.76x higher
   inside than outside at baseline, still 3.57x at steps 8, 2.40x at denoise
   0.35. Lowering the settings makes the paste blend in better; it never stops
   being a paste. It is in the delivered image.
2. **`MaskBoundingBox+` has no empty-mask guard**, so an undetectable face is a
   crash rather than a degraded render.

---

# After the repair — the three re-runs, and they change one thing

Main ran `POST /free {"unload_models": true, "free_memory": true}` on an empty
queue and resubmitted the control himself (`ff369e90`). It came back
**mean absolute difference 0.0000, maximum 0 levels, 0.000 % of pixels over 8**
against the original `C_zface_steps_08` — from a **cold** run, 0 cached nodes,
78 minutes later. The instrument was repaired.

That control is worth keeping for a second reason: it **proves this pipeline is
bit-deterministic under fixed seeds for my prompt**, from a cold cache, on my
own graph. I had been leaning on WS4's determinism result, measured on a
different prompt. **This is not the banned method** — the ban is on verifying
that a *change* is inert by hashing output. This is two identical graphs used as
a control on the instrument, and it is reported as mean and max absolute
difference over the full frame, not as a hash match.

Three arms were then re-run into fresh directories.

## The combination is worse than steps 8 alone, and the metric disagrees with me

`X2_steps08_denoise050` — steps 8 **and** denoise 0.50, 185.3 s.

| arm | blobs/mpx | pores/mpx | how it looks |
|---|---|---|---|
| `A0_baseline` | 764 | 16 471 | white foam, lesions |
| **`C_zface_steps_08`** | 239 | 23 213 | **skin, with fine texture and freckles** |
| `B_zface_denoise_050` | 157 | 23 050 | cleaner, freckles fading |
| `X2_steps08_denoise050` | **48** | **24 024** | smoothest — and almost airbrushed |

**On every number, `X2` is the best arm in the grid. Looking at it, it is not.**
The skin has lost most of its visible texture, the freckles have gone from flat
brown marks to barely-there, and the iris is the lightest of any arm. The owner
asked for visible pores and freckles; `X2` gives neither.

This is the clearest illustration in my run of why he says metrics tell you
something changed, not whether it looks better. My `pores/mpx` column counts
dark fine minima — at `X2`'s smoothness those are as likely to be sensor-grade
noise as pores, and the count rises while the *thing being counted* disappears.
**I would not ship `X2`, and I would not have known that from the table.**

## The confirmation pair — the fix works in the configuration the owner runs

`L0b_baseline_loras` and `L1b_steps08_loras`, with `lunaskye.safetensors` on
`#618` and `luna.safetensors` on `#116` at strength 1. These change two things
at once (settings **and** LoRAs) and are **not** grid arms — they are only ever
compared with each other.

| arm | blobs/mpx | pores/mpx | seam | exec |
|---|---|---|---|---|
| `L0b_baseline_loras` (shipped) | 404 | 12 232 | 4.82x | 400.7 s |
| `L1b_steps08_loras` (steps 8) | **133** | 13 874 | **2.29x** | 189.3 s |

Both succeeded. **First: the LoRAs do not crash anything** — which retires the
false alarm completely, not merely on suspicion.

**Second, and this is the point of the pair: the defect is present with the
owner's own LoRAs loaded, and steps 8 fixes it there too.** At the shipped
settings the Luna character's cheeks and brow carry the same field of white
raised bumps. At steps 8 the skin reads as skin, with freckles as flat brown
marks and natural lashes and brows
(`results/p2_evidence/CONFIRMATION_loras_shipped_vs_steps8.png`). The
recommendation transfers.

## Final answer

**Ship `#114 FaceDetailer` `steps` 30 → 8. Alone. Not with a denoise change.**

Confirmed with LoRAs loaded and without. Better skin, freckles back, lips
readable again, and faster — **−103.7 s (−26 %) as a lower bound** without
LoRAs, and 400.7 s → 189.3 s in the LoRA pair, though those two sat in
different cache states (38 vs 57) so I offer that second figure as direction,
not as a measurement.

Everything else measured — `#607`, `#87`, `guide_size`/`max_size` — should be
left exactly as it is. `bbox_crop_factor` is **unmeasured**, not cleared.
