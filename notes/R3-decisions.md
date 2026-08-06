# R3 — the three held decisions, taken

Handed over with *"judgement goes whichever way is safest for a first-time
buyer"*. All three are below with the evidence each rests on. Where a claim
comes from inference rather than from a file or a command output, it is
labelled.

**Licensing is untouched.** `QUESTIONS.md` §0 is intact and I started nothing
on it.

---

## 0 · The three decisions

| | decision | applied? |
|---|---|---|
| **1** | `#105`'s negative prompt **emptied**, and a `MarkdownNote` **#652** added *inside* sg `5. Face & Mouth Detail (Z-Image)` explaining why | **yes**, commit `a806ce3` |
| **2** | **cfg stays at 1** on `#114`, `#165`, `#406`. The existing evidence supports it. | nothing to apply |
| **3** | `bbox_crop_factor` is now **measured**, not unmeasured. **`#114` `3 → 1.5` recommended.** | **no** — you look at the images first |

Workflow `sha256`: `8d50f636…458966` → **`0be499d3b0e82af5b8e53abd0d2aa67a85e6e449b9a6605e1200f853a0995e02`**.

---

## 1 · Decision 1 — `#105` emptied, and the note

### The string that was removed, preserved verbatim

```
deformed, ugly, blurry, bad anatomy, disfigured, extra eyes, cropped face, out of frame, deformed piercing, bad piercing, watermark, text
```

137 characters. It is also in `notes/P3-cfg.md` §3, `notes/WS4-questions.md` Q-E
and in git history at `2e4e8e9:OFMTech-NSFW/OFMTech_NSFW.json`.

### Why it cannot act — read, not taken from the previous report

`comfy/samplers.py:369-370`, which I opened myself:

```python
def sampling_function(model, x, timestep, uncond, cond, cond_scale, model_options={}, seed=None):
    if math.isclose(cond_scale, 1.0) and model_options.get("disable_cfg1_optimization", False) == False:
        uncond_ = None
```

At cfg 1 the uncond conditioning is replaced with `None` **before**
`calc_cond_batch` is called. The tokens are encoded by CLIP and then discarded.

Two things had to hold for that to bite, and I checked both rather than
assuming them:

* **`620:105` has exactly one consumer.** Scanning every input of every node in
  the API graph: `620:114.negative`, and nothing else. `620:114.inputs.cfg` is
  `1`.
* **Nothing in this chain sets `disable_cfg1_optimization`.** `grep` over
  `comfy/` and `comfy_extras/` says the flag is only ever set by
  `sample_euler_ancestral_cfg_pp` (`k_diffusion/sampling.py:1244`),
  `sample_dpmpp_2s_ancestral_cfg_pp` (`:1294`), `sample_dpmpp_2m_cfg_pp`
  (`:1337`), `sample_gradient_estimation` (`:1451`), `sample_euler_pp`
  (`nodes_advanced_samplers.py:66`) and SAG (`nodes_sag.py:177`). `#114` and
  `#165` run plain `euler_ancestral`, `#406` plain `euler`. And
  `620:114.model` traces `116 Lora Loader Stack (rgthree)` ← `620:113
  UNETLoader zimage.safetensors` — no patcher in between.

### Proved inert without a render

The sanctioned method, not output hashing. Both graphs are real
`app.graphToPrompt` conversions captured by `tools/browser_harness/run.js
--no-submit`:

```
before  results/browser/20260806-124727-OFMTech_NSFW/api_graph.json
after   results/browser/20260806-125050-OFMTech_NSFW/api_graph.json

RESULT: DIFFERENT — 1 difference(s): value_changed=1
  value_changed   620:105.inputs.text  (CLIPTextEncode)
                    A: "deformed, ugly, blurry, bad anatomy, …"
                    B: ""
```

**A control was needed and it changed the answer.** My first diff reported
*two* differences — the second being `419.inputs.rgthree_comparer` on the root
Image Comparer. Rather than explain it, I ran the harness a second time on the
**identical** file and diffed run against run:

```
RESULT: DIFFERENT — 1 difference(s): input_added=1
  input_added     419.inputs.rgthree_comparer  (Image Comparer (rgthree))
```

So that field flips on its own between two loads of the same workflow — it is
browser state (the stale `rgthree.compare._temp_*` names of `HANDOFF.md` §7.4)
and not attributable to any edit. Without the control I would have reported a
second difference I could not account for.

Node **#652 does not appear in the API graph at all** — 88 nodes on both sides,
no `MarkdownNote` class_type. A note is frontend-only.

`tools/preflight/integrity.py`: **0 problems**.
`tools/browser_harness/run.js --no-submit`: **PASS**, twice.

### Why a note and not `ConditioningZeroOut`

As instructed, and I agree with the reason: `ConditioningZeroOut` is the more
correct construction and is what ComfyUI's own turbo template uses, but it
means adding a wired node and editing subgraph IO — the class of edit that
produced this project's browser blocker. A `MarkdownNote` has **no inputs and
no outputs**; it touches no link, no slot and no subgraph IO. The diff is 28
insertions / 4 deletions.

### Where the note is

`MarkdownNote #652`, **inside** sg `5. Face & Mouth Detail (Z-Image)`, at
`[2810, 5570]`, size `[680, 560]` — immediately to the right of `#105` (x
2102–2766) and `#106` (x 2102–2777), in the same vertical band, so it is in
view when the buyer follows `#649`'s instruction to "open 5. Face & Mouth
Detail, find *Face Detailer Prompt*". Colours `#432`/`#653`, matching the three
existing buyer-facing notes so it reads as part of the same set. The placement
was collision-checked in code against every node box in the subgraph and both
IO nodes before it was written.

**Verified in a real browser, not from the JSON.**
`results/r3_crop/R3_note_in_subgraph.png` — a Chromium session loads the
shipped workflow, enters the subgraph host `#620` the way a buyer does, and
reports the subgraph's node list as `[137, 107, 108, 111, 165, 114, 106, 105,
110, 109, 113, 648, 652]`. The screenshot shows the breadcrumb reading
**5. Face & Mouth Detail (Z-Image)**, *Face Detailer Negative Prompt* with an
**empty** box, *Face Detailer Prompt* still reading `TRIGGER, PROMPT FOR YOUR
MODEL`, and the note rendered in full and legible immediately to their right.
Nothing was sent to `/prompt`; five of other agents' renders were active at the
time and were not disturbed.

### The exact wording

> ## The negative prompt boxes in here are empty on purpose
>
> The face, mouth and eye passes run on **Z-Image Turbo** (`zimage.safetensors`,
> loaded on the left). Turbo models are built for speed, and the trade they make
> is that **they have no negative prompt at all.**
>
> Anything you type into a negative box on these three passes is thrown away
> before the model ever sees it. Nothing is broken and nothing is ignoring you —
> the words genuinely never arrive. **Leave the boxes empty.**
>
> ### Say what you *don't* want in the positive box instead
>
> **Face Detailer Prompt** is the only thing steering this pass, so it has to
> carry both halves. Turn each "not that" into a "this":
>
> * instead of a negative `blurry` → put `sharp focus` in the positive
> * instead of a negative `bad teeth` → put `clean even teeth` in the positive
> * instead of a negative `extra eyes` → describe the eyes you *do* want
>
> ### Do not turn `cfg` up to make the negatives work
>
> It looks like the fix and it is not one. `cfg` is **1** on both detailers in
> here, and on the eye pass in **6. Eyes**, because 1 is the setting this model
> was built for. Turning it up does not usefully switch the negative prompt back
> on — that was measured, not assumed — and it runs the model outside what it was
> trained to do.
>
> If a pass gives you something you don't want, change the **positive** prompt or
> your LoRA. Not `cfg`, and not the negative box.

Every factual claim in it is checked against the file: `#114` cfg 1 steps 8,
`#165` cfg 1 steps 8, `#406` cfg 1 steps 8 (read from both
`OFMTech_NSFW.json` and the executed API graph), and all three take their model
from `620:113 UNETLoader zimage.safetensors` through `116`.

It deliberately does **not** say raising cfg will wreck the image, because §2
below shows it does not.

### One sentence added to root `#649`

Inserted after the existing "*One thing you must fill in*" paragraph:

> Put what you want **avoided** in that same box. The *negative* prompt boxes
> on the face, mouth and eye passes do nothing at all — there is a note next to
> them inside that box explaining why.

The note inside sg 5 is the load-bearing half; this is the pointer that gets
them to it.

---

## 2 · Decision 2 — cfg stays at 1

**Nothing was re-rendered.** All figures below come from `notes/P3-cfg.md` and
`results/cfg/`, which were already on disk. What I added is two tight 1:1 crops
so the cost is visible rather than tabulated, and my own read of them.

### What raising cfg costs — look at this

**`results/cfg/compare/R3_cfg_cost_worstregion_1to1.png`** — cfg 1.0 / 1.5 /
3.0 side by side, 600×600 each, **1:1, no downscaling** (every tile verified
byte-identical to its source crop). The region is not chosen for flattery: it is
the densest 600×600 window of pixels differing by more than 8 levels between
cfg 1.0 and cfg 3.0 — 3.65 % of that window, against 0.575 % over the whole face
box. **The worst place to look.**

| comparison | max Δ | px >8 levels | PSNR | SSIM |
|---|---|---|---|---|
| face `#114` cfg 1.0 → 1.5 | 40 | 0.038 % | 52.24 dB | 0.9979 |
| face `#114` cfg 1.0 → **3.0** | 89 | **0.575 %** | 44.56 dB | 0.9938 |
| mouth `#165` cfg 1.0 → 3.0 | 13 | 0.001 % | 55.53 dB | 0.9983 |
| eyes `#406` cfg 1.0 → 3.0 | 33 | 0.140 % | 50.34 dB | 0.9982 |

**What I see, at 1:1, in the worst region: nothing.** The three tiles are the
same image to my eye. Same blistered bubble-wrap pore texture on the nose bridge
and cheeks, same lashes, same iris. I could not pick cfg 3.0 out of a line-up.
So P3's finding survives an independent look — raising cfg does **not** visibly
break the image, and it does not fix anything either.

### Is there anything behind the door?

**`results/cfg/compare/R3_negative_when_live_worstregion_1to1.png`** — the same
treatment for the question that actually decides this: at cfg 1.5, where the
negative *is* evaluated, negative empty versus the shipped 12-token string.
Worst 600×600 window again (0.37 % of it changed).

| stage, cfg 1.5, negative ON vs OFF | max Δ | px >8 levels | PSNR | SSIM |
|---|---|---|---|---|
| face `#114` | 67 | **0.048 %** | 52.21 dB | 0.9983 |
| mouth `#165` | 12 | **0.000 %** | 57.23 dB | 0.9987 |
| eyes `#406` | 13 | **0.000 %** | 56.91 dB | 0.9990 |

**Two images I cannot tell apart.** Turning that professional-looking negative
prompt on, at a cfg where it genuinely runs, buys nothing.

### The decision, and why it is the safe one

**Leave cfg at 1 on `#114`, `#165` and `#406`. Empty the negatives. Say so on
canvas.** The evidence supports it and I checked before writing it down:

* Raising cfg is **off-design**. `zimage.safetensors` is byte-for-byte
  Z-Image-**Turbo** by sha256 against the publisher's manifest
  (`2407613050b809ff…825574a6`), the vendor's own quick-start says
  `guidance_scale=0.0, # Guidance should be 0 for the Turbo models`, ComfyUI's
  shipped turbo template runs cfg 1 where the base template runs cfg 4, and the
  checkpoint contains no guidance tensors to fall back on. That argument comes
  from a hash, a vendor statement and a source line — none of it from a render.
* Raising cfg has **no payoff**. The thing you would raise it *for* — making the
  negative live — moves 0.048 % / 0.000 % / 0.000 % of pixels.
* So the trade is: leave a documented operating point, for nothing.

For a first-time buyer the safest position is the one the model vendor
documents, with the dead control removed and the reason written down where they
will hit it.

### The caveat I owe this section

**These arms were rendered on the 30-step graph**, before `2e4e8e9` shipped
steps 8. You can see it in the crops — the bubble-wrap texture is the
steps-30 defect. That does **not** weaken the decision, because the decision
rests on the mechanism (`samplers.py:370` is step-independent) and on the model's
identity, not on the magnitude of any pixel difference. But **the specific
numbers in the tables above have not been re-measured at steps 8** and I am not
going to imply otherwise. I was told not to re-render this and did not.

---

## 3 · Decision 3 — `bbox_crop_factor`, measured

Six earlier arms were void — rendered after a server-side NaN at 02:11:21 and
returning a flat RGB(53,47,43) face with `status: success`. The lever was
**unmeasured, not closed**. It is measured now.

### Method

Three full-pipeline renders on top of the **shipped steps 8**, built from
`results/face/arms/C_zface_steps_08/api_graph.json`, which
`tools/graph_diff/graph_diff.py` proves is `A0_baseline` with exactly one input
changed (`620:114.inputs.steps` 30 → 8) — i.e. the graph now on disk plus the
freckle prompt and seed 12345 the whole face grid used. Seed 12345 batch,
`#114` seed 1111111, cfg 1, denoise 0.8, LoRAs `None`. Arms differ from each
other in `bbox_crop_factor` **only**; the builder asserts every other input
before writing.

`inputs.pick_list = "0"` on `619:603` **in the submitted prompt only**. Nothing
was interrupted and the queue was never cleared; other agents' prompts ran
alongside mine throughout.

### The server-health control came first, and it passed

Arm 0 was a **byte-identical resubmission** of `C_zface_steps_08`'s graph. It
returned `max abs diff 0` against that arm's 01:30 image over 2688×3456×3, and
its face box carries normal skin statistics (mean RGB 143.3/108.7/93.2, σ ≈ 47)
rather than the flat-grey poison signature (0.012 % of the box within ±2 levels
of RGB(53,47,43); 0.00 % black pixels). All three arms were checked for that
signature. **None of them is void.** This is a machine-health check, not a
verification method — nothing about crop factor rests on it.

### The mechanism, from the server's own log

The detector found the same face box in every arm — `(1430.5049, 1999.827)` —
so only the crop moved:

| arm | logged crop region | pixels diffused in one pass |
|---|---|---|
| **cf 3 (shipped)** | `crop region (2688, 3456) x 1.0` | **9.29 MP** (clamped to the whole frame) |
| cf 1.5 | `crop region (2145, 2999) x 1.0` | 6.43 MP |
| cf 1.0 | `crop region (1430, 1999) x 1.0` | 2.86 MP |

All three log `force inpaint` and `x 1.0`, so all three sample at native crop
size — `modules/impact/core.py:315-320` clamps the computed downscale back to
1.0. **The face itself therefore occupies the same number of pixels in every
arm; what changes is the size of the canvas the model is asked to diffuse in one
go.** Z-Image is a ~1024-class model, so at cf 3 it is being handed roughly 36×
its trained area.

### "A cleaner number may just mean it did less" — checked, and it is not that

This was the right thing to be suspicious of, so I did not answer it with a
metric. `results/r3_crop/R3_crop_diffmap_vs_cf3.png` maps where each arm differs
from the shipped one. **Both maps light up the entire face silhouette** —
forehead to chin, ears included — not a shrinking central patch and not a ring.
The refined footprint is the SAM face mask in all three arms, and the crop
factor does not shrink it.

*A tap of `620:137` — the image entering `#114` — was queued to turn that from a
strong reading of the difference maps into a direct measurement of the refined
footprint. It was still behind four other agents' prompts when this was written;
if it landed, the result is appended at the end of this section.*

### What I see, at 1:1

Three sheets, every tile verified byte-identical to its source crop:

* **`results/r3_crop/R3_crop_face_1to1.png`** — 940×1180 face, all three arms
* **`results/r3_crop/R3_crop_eyesnose_1to1.png`** — 600×600 nose, philtrum, mouth
* **`results/r3_crop/R3_crop_jawseam_1to1.png`** — 600×600 jaw, across the mask edge

**cf 3, the shipped setting, is producing visible damage on the face.** In the
nose/mouth crop the philtrum and upper lip are covered in a fibrous, hairy,
granular growth and the lips are broken up with white filaments and red debris.
It reads as a skin condition. The cheeks carry white blobs and a sandpaper
texture; the freckles are lost in the noise. In the jaw crop the mask seam is a
**hard diagonal line** with blistered skin on one side and smooth skin on the
other. This is the shipped graph at steps 8 — steps 8 reduced this defect
(`HANDOFF.md` §4: 764 → 239 blobs/MP) but plainly did not remove it.

**cf 1.5 is the same face, without the damage.** Skin looks like skin, pores are
visible and individual rather than blistered, lips have fine vertical texture,
lashes are strands, eyebrows resolve into hairs. The seam drops to a soft
transition. One real defect survives: a raised yellowish blister on the lower
lip.

**cf 1.0 is cleaner still and noticeably softer.** Pore structure around the
nose and upper lip is largely gone and the skin edges toward waxy; eyebrow edges
soften. The lip blister is smaller. The seam is almost invisible.

### Cost

`#114`'s own pass, measured between its `segment upscale` line and its
`vae decoded` line in `/workspace/ComfyUI/user/comfyui_18188.log`:

| arm | `#114` pass | of which VAE decode | whole prompt | cached nodes |
|---|---|---|---|---|
| **cf 3 (shipped)** | **67.8 s** (incl. a 4.4 s cold Lumina2 load) | **22.6 s** | 289.3 s | 38 |
| cf 1.5 | **24.9 s** | 1.2 s | 144.9 s | 57 |
| cf 1.0 | **8.4 s** | 0.4 s | 124.4 s | 57 |

The cf 1.5 and cf 1.0 arms have identical cache state (57) so they are
comparable to each other directly. The control arm is **not** comparable on
whole-prompt time — it was the first render after a 9½-hour idle and loaded 38
fewer nodes from cache — which is why the per-pass figure is given. Even after
subtracting its model load, `#114` costs ~63 s at cf 3 against ~25 s at cf 1.5.
The 22.6 s VAE decode of a 9.3 MP crop is pure overhead bought by the clamp.

### Recommendation: `#114 bbox_crop_factor` **3 → 1.5**

Not 1.0, and the reason is your own stated preference rather than a metric. You
rejected `steps 8 + denoise 0.50` — which won every column — because it was
"almost airbrushed, freckles reduced to barely-there", and you asked for visible
pores and freckles. **cf 1.0 has the same character.** It is the cleanest arm
and it is also the one that has given up the texture you asked for. cf 1.5
removes the blistering, the fibrous upper lip and most of the seam while keeping
pore structure, and it still cuts `#114` from ~63 s to ~25 s.

cf 1.5 also keeps a 25 % context margin on each side of the face box. At cf 1.0
the crop **is** the detector's box, so the model inpaints a face with no
surrounding context at all. Nothing in these three renders shows that hurting —
*this is inference from geometry, not something I measured* — but it is a reason
to prefer 1.5 when 1.5 already gets most of the benefit.

**Not applied.** One integer, sg `5. Face & Mouth Detail (Z-Image)`, `#114`,
`widgets_values[15]`, `3 → 1.5`. (Index 15 verified: `FaceDetailer` has 28
widgets, `seed` at index 3 drags its `control_after_generate` companion into
index 4, the array has 29 entries, and index 15 currently reads `3`.) You look
at the images first.

### What would kill this, and what is untested

* **One image, one seed, one framing.** The clamp to the full frame happens
  because `bbox × 3` exceeds the image; a differently framed subject changes
  that arithmetic. This needs a second and third character before it ships.
* `#165 Mouth Detailer` also carries `bbox_crop_factor 3`, on a bbox small
  enough that it does not clamp. **Not tested, not changed.**
* If the lower crop makes the composited face detach in colour or focus from
  the surrounding skin on some other image, that kills it. I did not see it here.

---

## 4 · Scope

* **Licensing: untouched.** `QUESTIONS.md` §0 intact.
* Only `OFMTech-NSFW/OFMTech_NSFW.json` was edited, in one commit (`a806ce3`),
  for Decision 1. Decisions 2 and 3 changed no shipped file.
* `619:600 KSamplerAdvanced` on the SDXL half runs cfg 1 with the **buyer's own**
  typed negative wired in. It looks like `#105` and it is not: the same encode
  also feeds `619:592` at cfg 4 and `619:617` at cfg 4.5, where it does apply.
  Emptying it would be wrong. Left alone, flagged in `notes/R3-questions.md`.
* `#648`'s title reads "Mouth SEGS size guard **(see note)**" and there is no
  such note anywhere in the workflow — I searched every `Note` and
  `MarkdownNote`. Not mine to fix this run; recorded.

## 5 · Files

```
OFMTech-NSFW/OFMTech_NSFW.json                       edited  (a806ce3)
results/browser/20260806-124727-…/api_graph.json     before graph
results/browser/20260806-125017-…/api_graph.json     after graph
results/browser/20260806-125050-…/api_graph.json     after graph, 2nd run = the control
results/cfg/compare/R3_cfg_cost_worstregion_1to1.png       cfg 1.0 / 1.5 / 3.0, worst region, 1:1
results/cfg/compare/R3_negative_when_live_worstregion_1to1.png  negative ON vs OFF at cfg 1.5, 1:1
results/r3_crop/R3_control_cf3/    R3_cf1.5/    R3_cf1.0/     api_graph.json, meta.json, PNG
results/r3_crop/R3_crop_face_1to1.png   R3_crop_eyesnose_1to1.png   R3_crop_jawseam_1to1.png
results/r3_crop/R3_crop_mouth_1to1.png  R3_crop_diffmap_vs_cf3.png
```
