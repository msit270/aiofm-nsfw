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

_(Results table and the recommendation follow in the sections below, filled in
as arms return.)_
