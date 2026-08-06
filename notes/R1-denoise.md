# R1-DENOISE — does denoise move as well as steps?

**Short answer: yes, and it moves a different thing.** Steps controls how much
the face pass *fabricates*. Denoise controls how much of the incoming face
*survives*. They are independent levers on `#114`, only one of them costs time,
and the owner's freckle question turns out to be about the second one — not the
first, and not about `X2` at all.

**Nothing was applied.** `OFMTech-NSFW/OFMTech_NSFW.json` is untouched by this
workstream; it is still `sha256 8d50f636b7…458966` (steps 8, commit `2e4e8e9`).
Every arm is a scratch copy or a scratch API graph.

Steps is not reopened here. `2e4e8e9` stands.

---

# 1. The thing the owner is waiting on: **DO LUNA'S FRECKLES SURVIVE IN X2?**

## The question cannot be asked of `X2`, because `X2` is not Luna

Read out of `results/face/arms/X2_steps08_denoise050/api_graph.json` — the
exact prompt that was submitted:

```json
"116": {"inputs": {"lora_01": "None", ...}}      <- Z-Image LoRA slot: empty
"618": {"inputs": {"lora_01": "None", ...}}      <- SDXL   LoRA slot: empty
```

`results/face/ARMS.md` states it as policy for the whole grid: *"Both LoRA
stacks left at the shipped `None`. No LoRA is loaded in any arm."* The face in
that tile is a visibly different person from `L0b`/`L1b` — brunette against
blonde, different features. **His judgement of that tile was sound about that
image and cannot transfer to Luna.**

So I rendered `X2L_loras_steps08_denoise050`: the same two settings with
`lunaskye.safetensors` on `#618` and `luna.safetensors` on `#116`, both at
strength 1.

## The freckles are real, and they are destroyed before the delivered image

The graph's own root comparer `#419 Image Comparer (rgthree)` takes
`image_a = 619:601` — the base generator's output, upstream of the entire
hands/skin/upscale and Z-Image half — and writes it to `temp/` on **every**
run. Those files are still on disk. No new render was needed to establish this.

`L0b`'s and `L1b`'s base renders are **bit-identical**: mean absolute
difference 0.0000, maximum 0 levels, over the full 1792x2304 frame. They must
be — the two arms' submitted prompts differ by exactly one input
(`620:114.steps` 30 → 8; graph diff, one difference, nothing else). That
doubles as a determinism control for this composition.

**In that base render Luna has dense, crisp, flat brown freckles across the
nose, cheeks, under-eyes and forehead.** The owner is right that they are a
trained character feature. They are there.

In the delivered images, over the identical crop:

| tile | `#114` settings | LoRAs | freckles |
|---|---|---|---|
| **base render** (before `#114`) | — | yes | **present** — crisp flat brown marks |
| `L0b_baseline_loras` | steps 30, denoise 0.80 | yes | **gone** |
| `L1b_steps08_loras` — *what ships now* | steps 8, denoise 0.80 | yes | **gone** |
| `X2_steps08_denoise050` | steps 8, denoise 0.50 | **no** | n/a — different person |

**Verdict, in the terms he asked for: GONE. But the trade he is worried about
was already made, by a lever he was not looking at.** Denoise 0.50 is not what
removed them. They were gone at the settings he shipped before, and they are
gone at the settings he shipped yesterday.

## `HANDOFF.md` says something about this that is not true of his configuration

`HANDOFF.md` §4 says that at steps 8 *"freckles [come] back as flat brown
marks"*. That is true of the **no-LoRA grid**, where the freckles are
prompt-driven and the comparison is `A0` → `C_zface_steps_08`. It is **not**
true of his own configuration. In `L0b` → `L1b` the freckles are gone in both.

The sentence he needs is: **what looks like freckles in the shipped 30-step
render is the defect.** At 4x, `L0b`'s cheek is a dense mat of pale *raised*
bumps with light tops. At arm's length that mat reads as freckling — which is
very likely why nobody caught this — but there is no flat brown mark anywhere
in the nose/upper-cheek region. Steps 8 removed the mat. It did not restore
anything underneath, because by then there was nothing underneath.

*(Main is correcting `HANDOFF.md`; this paragraph is my independent statement
of the same correction, from `L0b`/`L1b` and their shared base render.)*

## What I could not do defensibly: count them

The brief allowed a count if the rule was defensible. I wrote one:

> CIELAB (D65). Local background = 51 px median of each channel — about 2 % of
> face width, far larger than a freckle and far smaller than the cheek's
> shading gradient. A pixel is a freckle candidate if `L* < L*_bg − 2.0`
> (locally darker) **and** `b* > b*_bg + 0.6` (locally more yellow — pigment,
> not shadow). 8-connected components, kept if `25 ≤ area ≤ 1500 px`. Counted
> only inside a fixed pixel mask, the same three rectangles on every arm,
> covering nose and both upper cheeks and nothing else (`mask_px = 251,750`).

| arm | marks | per Mpx | area % of mask | chroma b\* band RMS | luma L\* band RMS |
|---|---|---|---|---|---|
| `L0b_baseline_loras` (steps 30, den 0.80) | 224 | 890 | 6.13 | 1.148 | 2.862 |
| `L1b_steps08_loras` (steps 8, den 0.80) | 59 | 234 | 1.38 | 0.716 | 1.485 |
| `X2_steps08_denoise050` *(no LoRAs)* | 92 | 365 | 1.88 | 0.795 | 1.617 |
| `A0_baseline` *(no LoRAs, steps 30)* | 289 | 1148 | 10.17 | 1.630 | 3.858 |
| `C_zface_steps_08` *(no LoRAs, steps 8)* | 200 | 794 | 5.91 | 1.184 | 2.488 |
| `B_zface_denoise_035` *(no LoRAs, den 0.35)* | 88 | 350 | 1.71 | 0.783 | 1.768 |

**Then I looked at what it had counted, and it is not freckles.** Cropping the
six largest components in each arm at 4x: in `L0b` they are stray fine hairs,
an eyelash shadow, a brown filament artifact and the dark interstices between
the raised bumps; in `L1b` they are the nose's own shading edge and the nostril
shadow. Not one is a freckle.

So the table above is **a dark-mark count that over-counts on bumpy arms**, and
I am not calling it a freckle count. It is reported because I ran it and
because the direction it points is not wrong; the finding rests on the crops.
This is the second time in this project a table has ranked arms confidently on
something it was not measuring.

## The picture

```
results/face/R1_freckles_nose_cheeks_1to1.png
```

Nose + upper cheeks, **720x440 native pixels, 1:1, identical box on every
tile** (`x1180,y1540` on the delivered 2688x3456). Base render top-left. The
base tile is 1792x2304 so it is enlarged **x1.5 nearest-neighbour** and
labelled as such on the tile; nothing else on the sheet is resized, and each
paste is asserted byte-equal to its source crop.

---

# 2. Where the freckles die — the tap render

*(Section filled in when the tap lands; see §6 for status.)*

---

# 3. Why denoise and steps are different levers, from the source

`#114` is a `FaceDetailer` and its sampling goes through the Impact Pack, not
ComfyUI's `KSampler` node. Both agree, and I read both rather than take the
previous session's word:

`ComfyUI-Impact-Pack/modules/impact/impact_sampling.py:198-211`,
`ksampler_wrapper` with no refiner:

```python
advanced_steps = math.floor(steps / denoise)
start_at_step  = advanced_steps - steps
end_at_step    = start_at_step + steps
```

`comfy/samplers.py:1145-1155`, `KSampler.set_steps`, does the same thing:
`new_steps = int(steps/denoise)`, then `self.sigmas = sigmas[-(steps + 1):]`.

**The executed step count is always `steps`, whatever denoise is.** Denoise
only chooses *where on a longer schedule the pass starts*:

| `#114` setting | schedule length | starts at step | runs |
|---|---|---|---|
| steps 30, denoise 0.80 *(old shipped)* | 37 | 7 | 30 |
| steps 8, denoise 0.80 *(shipped now)* | 10 | 2 | 8 |
| steps 8, denoise 0.50 | 16 | 8 | 8 |
| steps 8, denoise 0.35 | 22 | 14 | 8 |
| steps 30, denoise 0.35 | 85 | 55 | 30 |

Two things follow, and they are the whole answer to the brief's question:

1. **Denoise is free in time and steps is not.** Confirmed empirically in
   P2's matched-cache regime: denoise 0.35 / 0.50 / 0.65 all landed at
   290.7 / 291.6 / 290.8 s with an identical 57-node, 10-heavy cache, while
   steps 30 → 16 in the same regime saved 67.5 s.
2. **Denoise is the only lever that decides how much of the incoming face
   survives.** Steps 8 and steps 30 at the same denoise 0.80 both start the
   pass at ~80 % of the way up the noise schedule. That is why changing steps
   fixed the bumps and did nothing for the freckles: it changed how carefully
   the pass re-invents the face, not how much of the real face it was allowed
   to keep.

Note that steps 8 / denoise 0.35 and steps 30 / denoise 0.35 start at
14/22 = 0.636 and 55/85 = 0.647 of their schedules — practically the same
noise level. So `Y1` and `Y2` should differ in *fabricated texture*, not in
*how much input survived*. Whether that prediction holds is on the sheet.

---

# 4. The arms

*(Filled in when they land.)*

---

# 5. Timing

*(Filled in when the matched cold pair lands.)*

---

# 6. Method and provenance

* Every arm is a scratch copy of `OFMTech-NSFW/OFMTech_NSFW.json`, built by an
  asserting script that checks **both** the `widgets_values` array length and
  the value currently at the index before writing. A desync aborts the build.
  `#114` has 29 entries = 28 widgets + the synthetic `control_after_generate`
  companion that `seed` (widget 3) drags in; index 5 = `steps` held `8`,
  index 9 = `denoise` held `0.8`, both verified against the file.
* Every arm passes `python3 tools/preflight/integrity.py <arm.json>` with
  **0 problems** before submission. All three did.
* Every arm is converted to API format by the real frontend —
  `tools/browser_harness/run.js --no-submit --api-out`, i.e.
  `app.loadGraphData()` + `app.graphToPrompt()` in Chromium against the live
  server, the same call the Run button makes. Nothing reached the server during
  conversion.
* Every submitted prompt is diffed against the submitted prompt of an arm that
  has already rendered cleanly (`L1b` or `L0b`) with a node-by-node,
  input-by-input comparison. **Each new arm shows exactly one difference,
  `620:114.denoise`, and nothing else.** The tap arm shows six added
  `SaveImage` nodes, zero removed, and zero existing nodes changed.
* `inputs.pick_list = "0"` on `619:603 INSTARAW_ImageFilter` and the removal of
  the frontend-only `419.inputs.rgthree_comparer` are applied **to the
  submitted prompt only, identically in every arm**. No arm's workflow file
  contains either.
* Same seed (12345, `seed_control: fixed`) and the same freckle-bearing prompt
  as the rest of the grid, taken verbatim from `L1b`'s submitted graph.
* `POST /free {"unload_models": true, "free_memory": true}` before each timed
  run, **only** when `queue_running == 0 and queue_pending == 0`. The server is
  shared with three other agents; freeing under someone else's render would
  give them a cold start and corrupt their measurements.
* **No `POST /api/interrupt`. No `POST /api/queue {"clear": true}`.** No queue
  item was deleted, so `execution.py:1218-1229`'s `wipe_queue()` path was never
  reachable.
* **Hash comparison of rendered output is not used as a verification method
  anywhere in this report.** The one place two images are compared for equality
  — the two base renders — is reported as mean and maximum absolute difference
  over the full frame, and it is a control on the instrument, not a proof that
  a change is inert.
