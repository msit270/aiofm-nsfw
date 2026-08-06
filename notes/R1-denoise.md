# R1-DENOISE — does denoise move as well as steps?

**Short answer: yes, and it moves a different thing.** Steps controls how much
the face pass *fabricates*. Denoise controls how much of the incoming face
*survives*. They are independent levers on `#114`, only one of them costs time,
and the owner's freckle question turns out to be about the second one — not the
first, and not about `X2` at all.

**Nothing was applied by this workstream.** `OFMTech-NSFW/OFMTech_NSFW.json` is
untouched by me. Every arm is a scratch copy or a scratch API graph.

Steps is not reopened here. `2e4e8e9` stands.

## Which graph each arm was rendered on — read this before comparing any two tiles

The shipped graph changed twice while this work was in flight. Every arm is
labelled with the graph it ran on, on the sheet and in its `meta.json`.

| | `#114` `bbox_crop_factor` | `#105` negative | arms |
|---|---|---|---|
| **`2e4e8e9`** (workflow `8d50f636…`) | 3 | text | `L0b`, `L1b`, `X2` and the whole earlier grid |
| **`74c0f11`** (workflow `a811b5d6…`) | **1.5** | empty | `TAP`, `Z1`, `Z2`, `Z3` — the decision arms |

I rebased onto `74c0f11` **before rendering anything**, at a cost of zero
wasted renders, because cf is not an independent axis from denoise: cf sets how
many pixels the pass fabricates and denoise sets how much of the input it is
allowed to destroy. A denoise value chosen against a pass that fabricates twice
as much is not the value you would choose otherwise. P2's own sweep shows the
size of that: band-pass energy on `#114`'s footprint runs 5.311 at cf 3
(2688x3456) and 4.196 at cf 1.5 (1945x2749), against 2.862 for the untouched
input. **The decision sheet is built on the graph that ships.**

`#105` going empty is inert at cfg 1 — `comfy/samplers.py` never evaluates the
uncond — so it does not affect any comparison here.

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

So I rendered `Z1_cf15_denoise050`: the same denoise with
`lunaskye.safetensors` on `#618` and `luna.safetensors` on `#116`, both at
strength 1, on the graph that now ships.

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

Worth noting what that tap already rules out: `619:601` sits **downstream of
`#607 FaceDetailerPipe`**, the SDXL face pass, inside the base generator
(`619:596 → 619:607 → 619:597 → … → 619:602 → 619:603 → 619:601`, read from the
API graph). Confirmed in the log, where `#607`'s own crop appears as
`crop region (1432, 1840) x 1.0` in the runs where it was not served from
cache. **So a face pass at 20 steps / denoise 0.45 preserves the freckles
intact.** Whatever destroys them is later than that.

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

Incidentally that corroborates R3 from a different direction: the objects my
counter kept picking up on `L0b`'s cheek are **filaments and reddish-brown
debris sitting on the skin**, which is the same class of artefact R3 describes
on the philtrum and lips. I was not looking for them and my rule found them
because they are the only high-contrast small dark objects in that region.

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

# 2. `#165 Mouth Detailer` ran in the LoRA arms and did not run in the grid — and the `[filter]` line means the opposite of what it looks like

Main warned that `#648`'s size guard silently drops the lips segment when its
crop area exceeds 1,700,000, logging `[filter] value=… / True, 0, 1700000`. I
checked it against my own arms rather than take the count, and found the log
line is **the failure signal, not the measurement**: runs where the mouth pass
*does* run carry **no `[filter]` line at all**, and instead show a second
`Detailer: … crop region (w, h) x 1.0` with a wide, short crop. So counting
`[filter]` lines counts drops only; absence is a pass, not missing data.

Verdict taken from the detailer lines themselves — `x 1.0` crop regions inside
each arm's own `/history` execution window:

| arm | `x 1.0` crop regions logged | `#165` |
|---|---|---|
| `L0b_baseline_loras` | 1432x1840, 2688x3456, **1956x790** | **ran** |
| `L1b_steps08_loras` | 2688x3456, **1827x768** | **ran** |
| `A0_baseline` | 1432x1840, 2688x3456 | dropped (`value=1933356`) |
| `C_zface_steps_08` | 1432x1840, 2688x3456 | dropped (`value=1861888`) |
| `B_zface_denoise_035` | 2688x3456 | dropped (`value=1797291`) |
| `X2_steps08_denoise050` | 2688x3456 | dropped (`value=1773063`) |

`1432x1840` is `#607`, the SDXL face pass, absent when it was served from
cache. `2688x3456` is `#114` at cf 3. The wide one is `#165`.

**So the LoRA arms and the no-LoRA grid differ in whether the mouth pass ran,
on top of differing in LoRA.** That is a second reason not to compare a lip or
chin region across those two sets — and it was not known when the grid was
read. It does **not** touch the freckle finding: my crop is nose and upper
cheeks, and every stage of that evidence is upstream of `#165` entirely.

It does affect the **contact sheet**, whose tight face box includes the mouth.
Each arm's `meta.json` carries `mouth_pass.ran` and the raw log lines it was
derived from; if my four decision arms split on it, the sheet says so.

---

# 3. Where the freckles die — the tap render

## The prediction, and why the tap is designed the way it is

Before the tap ran there was already one piece of evidence pointing upstream of
`#114`. P3's baseline arm (`results/cfg/00-baseline-full/`) ran **with both
Luna LoRAs** at shipped settings and saved `P3_in_face` — a tap on `620:137`,
the image `#114` receives. Its base render is still in `temp/`. Over a fixed
nose/cheek mask on that composition, with the filter radius scaled so the
physical scale matches:

| P3 stage | pigment % of mask | bright-blob % of mask |
|---|---|---|
| base render `619:601` (1792x2304) | **3.085** | 9.006 |
| into `#114`, `620:137` (2688x3456) | **1.117** | 6.869 |
| delivered `#505` (2688x3456) | 8.814 | 25.178 |

"pigment" = locally darker **and** locally more yellow; "bright-blob" = locally
brighter, which is the raised-bump defect. **Two thirds of the pigment is gone
before `#114` is reached.** The rise at `#505` is the bump field, not restored
freckles — the same over-count established in §1, where the dark interstices
between bumps satisfy the pigment rule.

That measurement crosses a resolution change (1792x2304 → 2688x3456), which on
its own could shift a per-pixel statistic. So the tap is designed to give
**same-resolution comparisons on both sides of the change**: stages 1–4 are all
1792x2304, stages 5–7 all 2688x3456. Comparing 1 → 4 and 5 → 6 is scale-free;
only 4 → 5 crosses it, and that step *is* the upscale.

*(Tap result filled in below when the render lands.)*

---

# 4. Why denoise and steps are different levers, from the source

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

# 5. The arms

*(Filled in when they land.)*

---

# 6. Timing

*(Filled in when the matched cold pair lands.)*

---

# 7. Method and provenance

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
* `POST /free {"unload_models": true, "free_memory": true}` **only** when
  `queue_running == 0 and queue_pending == 0`. The server is shared with three
  other agents; freeing under someone else's render would give them a cold
  start and corrupt their measurements. That constraint is why the queue, not
  the GPU, was the limiting resource for this workstream.
* **A health control ran before the four arms and gated them.** The server has
  failed twice today from the same cause with two different symptoms — once
  returning a flat grey face with `status: success`, once crashing loudly at
  `622:403 MaskBoundingBox+` (`ComfyUI_essentials/mask.py:184`, `x.min()` on an
  all-zero mask). So after `/free` I resubmitted `L1b`'s own `api_graph.json`
  **byte-identically** and compared the result to `L1b`'s delivered PNG. The
  script exits without spending the window if that control does not come back
  matching. This is a control on the instrument reported as mean and maximum
  absolute difference — **not** a hash check, and not a proof that any change
  is inert.
* **No `POST /api/interrupt`. No `POST /api/queue {"clear": true}`.** No queue
  item was deleted, so `execution.py:1218-1229`'s `wipe_queue()` path was never
  reachable.
* **Hash comparison of rendered output is not used as a verification method
  anywhere in this report.** The one place two images are compared for equality
  — the two base renders — is reported as mean and maximum absolute difference
  over the full frame, and it is a control on the instrument, not a proof that
  a change is inert.
