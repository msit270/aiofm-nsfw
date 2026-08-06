# R1-DENOISE — does denoise move as well as steps?

**Short answer: yes, and it moves a different thing.** Steps controls how much
the face pass *fabricates*. Denoise controls how much of the incoming face
*survives*. They are independent levers on `#114`, only one of them costs time,
and the owner's freckle question turns out to be about neither — not about
`X2` at all, and not about `#114`.

**The five things worth knowing, each with the section that proves it:**

1. **`X2` is not Luna.** Both LoRA stacks are `"None"` in its own submitted
   graph. The tile he formed his opinion from is a different woman. **§1**
2. **Luna's freckles die at `#98 UltimateSDUpscale`**, two stages before
   `#114` runs — measured with six taps in one render and a resolution control
   in both directions. **No `#114` setting can bring them back**, so the
   denoise choice is purely about how the skin looks. **§3**
3. **The pick is `#114 denoise` 0.80 → 0.35.** At 0.80 the cheek still reads as
   orange peel; at 0.35 it reads as skin, keeps the pore texture that was in
   the image before the pass, and is the only setting that carries a surviving
   pigment mark through. It costs nothing. **§5b**
4. **"400.7 s → 189.3 s" was cache, not steps.** Cold against cold on the same
   two graphs it is 417.5 s → 388.9 s, **−6.9 %**. **§6**
5. **`#87 ImageBlend` is innocent of this too** — it is a pass-through of
   `#91`, and `#91` nearly *doubles* the freckles rather than removing them.
   This retracts an inference I sent earlier in the run. **§3**

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
as much is not the value you would choose otherwise.

The size of the first half, from **P3's** resolution sweep
(`results/cfg/compare/sweep_metrics.json`, arms `sw_cf1.5` / `sw_cf1.0` — *not*
P2's `CF_crop_*` arms, which are void): band-pass energy on `#114`'s footprint
runs **5.311 at cf 3** and **4.196 at cf 1.5**, against **2.862** for the
untouched input. And from my own arms' server log, which needs no one else's
numbers: `#114`'s crop is **2688x3456 = 9.29 MP at cf 3** and
**2010x2859 = 5.75 MP at cf 1.5**, a **38 % cut** in what the pass diffuses.
**The decision sheet is built on the graph that ships.**

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

| tile | `#114` settings | LoRAs | freckles at 1:1 |
|---|---|---|---|
| **base render** (before `#114`) | — | yes | **present** — discrete, crisp, flat brown marks |
| `L0b_baseline_loras` | steps 30, denoise 0.80 | yes | **gone** — buried under a mat of pale raised bumps |
| `L1b_steps08_loras` — *what shipped* | steps 8, denoise 0.80 | yes | **gone** — smooth skin, a faint mottle, no discrete marks |
| `X2_steps08_denoise050` | steps 8, denoise 0.50 | **no** | n/a — different person |

**Verdict, in the terms he asked for — present / reduced / gone:**

* **In `X2` itself: not answerable.** It is a different woman. The question
  cannot be put to that tile.
* **In `X2`'s settings rendered in his configuration (`Z1`, denoise 0.50 with
  both Luna LoRAs): GONE.** No discrete brown marks in the nose/upper-cheek
  crop.
* **In what he shipped before (`L0b`, steps 30 / denoise 0.80): GONE.**
* **In what he shipped yesterday (`L1b`, steps 8 / denoise 0.80): GONE.**
* **In `Z2` (denoise 0.35): REDUCED, not gone** — one distinct brown mark
  survives, and it is the only arm in which anything does.

**So the trade he is worried about was already made, by a lever he was not
looking at.** Denoise 0.50 is not what removed them.

**Where my eye and my number disagree, and which I am trusting.** Applying one
consistent pigment rule (§below) the base render's mask is **3.394 %**
pigment-covered and `L1b`'s is **2.43 %** — a 28 % drop, not an erasure. I am
trusting the pictures, for a stated reason: the rule cannot tell a **discrete
freckle** from a **low-amplitude mottle**, and at 1:1 the base render has the
first and `L1b` has only the second. The same rule scores `L0b` at **8.525 %**
— higher than the base render that actually contains the freckles — because the
dark interstices between the raised bumps satisfy it. A rule that ranks the
bumpiest arm as the most freckled is not measuring freckles.

So the precise statement is: **the discrete flat brown marks are gone in both
delivered arms; a faint pigment mottle survives and does not read as freckles.**

**And they are gone before `#114` runs at all** — §3 locates it at
`#98 UltimateSDUpscale`, two stages upstream. Which means **no setting on
`#114` can bring them back**, and the denoise decision is purely about how the
skin looks.

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

## One pigment rule, applied to every arm

Used for every "pigment %" figure in this report. Over a **fixed pixel mask** —
the same three rectangles on every arm, covering nose and both upper cheeks and
nothing else, `mask_px = 251,750` — in CIELAB (D65), against a median-filtered
local background whose radius is scaled so the *physical* scale matches when an
image is at a different resolution:

* **pigment** = locally darker (`L* < L*_bg − 2.0`) **and** locally more yellow
  (`b* > b*_bg + 0.6`). This is what a flat brown mark looks like.
* **bright-blob** = locally brighter (`L* > L*_bg + 2.0`). This is what the
  raised-bump defect looks like — convex and light, the opposite of a pore.

| arm | pigment % | bright-blob % | chroma b\* RMS | luma L\* RMS |
|---|---|---|---|---|
| **base render** `619:601`, LoRAs *(1792x2304)* | 3.394 | **3.751** | 0.743 | 1.429 |
| `L0b` steps 30 / den 0.80 / cf 3, LoRAs | 8.525 | **20.910** | 1.148 | 2.862 |
| `L1b` steps 8 / den 0.80 / cf 3, LoRAs | 2.430 | **7.777** | 0.716 | 1.485 |
| `A0` steps 30 / den 0.80 / cf 3, no LoRAs | 13.350 | **26.639** | 1.630 | 3.858 |
| `X2` steps 8 / den 0.50 / cf 3, no LoRAs | 3.930 | **9.034** | 0.795 | 1.617 |
| `B035` steps 30 / den 0.35 / cf 3, no LoRAs | 4.042 | **10.725** | 0.783 | 1.768 |

The **bright-blob column is the one this rule measures honestly**, and it is
unambiguous: the base render carries 3.75 % and `#114` at the old settings
turns that into 20.9 % with the LoRAs and 26.6 % without. **The face pass
roughly five- to seven-times the bright-blob coverage of the image it is
handed.** The pigment column is contaminated as described above and should be
read only within a row-pair of similar bumpiness.

## What I could not do defensibly: count the freckles individually

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
**My four decision arms did not split: `#165` ran in all of `Z0`, `Z1`, `Z2`
and `Z3`** (`1844x803`, `1848x798`, `1860x792`, `1877x786`, no `[filter]` line
in any of them), so they are comparable to each other across the whole face
box. `L0b` and `L1b` also ran it. **`X2` is the only tile on the sheet that
dropped it** — one more reason that tile is not comparable, on top of having no
LoRAs. Each arm's `meta.json` carries `mouth_pass.ran` and the raw log lines it
was derived from, so the verdict can be re-derived rather than trusted.

One caveat on my own reading: I am inferring "no `[filter]` line means it ran"
from six arms where the two signals agree. If `#648` also logs on a pass under
some condition I have not seen, that inference is wrong — but the detailer
crop-region line, which I use as the actual verdict, is direct evidence either
way.

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

## The answer: **`#98 UltimateSDUpscale`**. Not `#87`, and not `#114`.

One render, shipped settings, both Luna LoRAs, six `SaveImage` taps injected
into the submitted prompt only (6 nodes added, 0 removed, **0 existing nodes
changed** — so `#505`'s output is what it would have been without them).
Cold: `/free` on an empty queue, `execution_cached` 0 nodes, 270.5 s.
`results/face/taps/TAP_cf15_denoise080/`.

| # | stage | resolution | pigment % | bright-blob % | freckles at 1:1 |
|---|---|---|---|---|---|
| 1 | base generator `619:601` | 1792x2304 | 3.394 | 3.751 | **present**, discrete brown marks |
| 2 | `587:92 HandDetailer` | 1792x2304 | 3.394 | 3.751 | **present** — *bit-identical to 1* |
| 3 | `587:91` skin-detail model | 1792x2304 | **6.581** | 10.512 | **present and stronger** |
| 4 | `587:87 ImageBlend` | 1792x2304 | 6.581 | 10.512 | **present** — *bit-identical to 3* |
| 5 | `587:98 UltimateSDUpscale` | 2688x3456 | **2.087** | 3.142 | **GONE** |
| 6 | `620:137` into `#114` | 2688x3456 | 2.096 | 3.172 | gone |
| 7 | delivered `#505` | 2688x3456 | 3.252 | **8.191** | gone; bumps added |

Three things fall straight out of that table, and none of them was known:

1. **`#92 HandDetailer` changes nothing in the face region** — stages 1 and 2
   are identical to four significant figures, and the two PNGs are the same
   size on disk. It is a hand pass and it behaves like one.
2. **`#87 ImageBlend` at `blend_factor 1` is a pass-through of `#91`** —
   stages 3 and 4 are identical. That is what `results/face/ARMS.md` inferred
   from the widget value; this measures it.
3. **The skin-detail model does not destroy the freckles, it nearly doubles
   them** — 3.394 → 6.581. `#87` is innocent of this charge as well as of the
   bumps. My earlier inference that the loss was in the `#87`/`#91` region was
   **wrong, and this retracts it.**

**The loss is entirely at stage 4 → 5: `#98 UltimateSDUpscale`, 1.5x, 2 steps,
denoise 0.08.** Pigment 6.581 → 2.087, bright-blob 10.512 → 3.142. Stage 5 → 6
is flat, so `ImageColorMatch+` is not involved. Stage 6 → 7 is `#114`, and what
it does is **raise bright-blob 3.172 → 8.191** — it adds the bumps; it does not
remove pigment that has already gone.

### The resolution confound, closed with a control in both directions

Stages 1–4 are 1792x2304 and stages 5–7 are 2688x3456, so a per-pixel statistic
could shift across that boundary for reasons that have nothing to do with
`#98`. Main flagged this and was right to. Closed by resampling the *same
image* across the boundary — a pure geometric LANCZOS resize, no diffusion, no
new detail — and re-measuring:

| image | measured at | pigment % | bright-blob % |
|---|---|---|---|
| stage 1, native | 1792x2304 | 3.394 | 3.751 |
| stage 1, **LANCZOS → 2688** | 2688x3456 | 3.323 | 3.596 |
| stage 4, native | 1792x2304 | 6.581 | 10.512 |
| stage 4, **LANCZOS → 2688** | 2688x3456 | **6.261** | 9.698 |
| stage 5, native | 2688x3456 | 2.087 | 3.142 |
| stage 5, **LANCZOS → 1792** | 1792x2304 | **2.122** | 2.847 |

The measure moves by **2–5 % relative** under a pure resize, in either
direction. So at matched scale the step across `#98` is **6.261 → 2.087, a
67 % loss**, and it is not the resampling. The pictures agree: at matched
display scale the discrete brown dots on the cheek in stage 4 are simply absent
in stage 5, with two or three faint remnants.

**Picture: `results/face/R1_where_freckles_die_1to1.png`** — seven tiles, same
anatomical box, and the header states in orange which tiles are display-scaled
and which are native, plus the matched-scale numbers, because a reader will
otherwise attribute all of the crispness step to `#98`.

### What this means for the owner's decision — it simplifies it

**Luna's freckles are gone two stages before `#114` runs. No value of `#114`
`denoise`, `steps` or `bbox_crop_factor` can bring them back.** The denoise
choice is therefore *only* about how the skin looks, and the freckle question
moves to a different node entirely.

If he wants the freckles, the lever is **`#98 UltimateSDUpscale`** — and that is
his decision and another run's job. I have not touched it, not tested it, and I
am not recommending a value. Logged, not chased.

### Determinism, again, from the same pair

Duplicate drivers submitted the identical 94-node graph twice more; both ran
**warm** (57 cached, 150.5 s and 149.9 s) against the cold run's 270.5 s. **All seven
outputs — every tap and the delivered frame — compare at mean absolute
difference 0.0000 and maximum 0 levels, both times.** The duplicates' PNGs were
deleted and the cold run kept; the comparisons are recorded in the arm's
`meta.json`.

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

# 5. The arms, and what denoise actually does on the shipping graph

Four arms, all with `lunaskye.safetensors` on `#618` and `luna.safetensors` on
`#116` at strength 1, all on `74c0f11` (`#114` `bbox_crop_factor` 1.5, `#105`
empty), seed 12345, the same freckle-bearing prompt as the rest of the grid.
`Z0` is the tap render; its six `SaveImage` sinks change no executed node's
inputs, so its `#505` output is a legitimate tile.

Measured over the same fixed nose/cheek mask, with the image `#114` **receives**
as the reference line — which is the number that matters, because the question
is whether the pass improves what it is handed or damages it:

| arm | `#114` | pigment % | **bright-blob %** | chroma b\* RMS | luma L\* RMS |
|---|---|---|---|---|---|
| — | *the input, `620:137`* | 2.096 | *3.172* | 0.799 | 1.262 |
| `L0b` *(cf 3)* | steps 30, den 0.80 | 8.525 | **20.910** | 1.148 | 2.862 |
| `L1b` *(cf 3)* | steps 8, den 0.80 | 2.430 | **7.777** | 0.716 | 1.485 |
| `Z0` | steps 8, den 0.80 | 3.252 | **8.191** | 0.736 | 1.459 |
| `Z2` | steps 8, den 0.35 | 0.729 | **1.681** | 0.563 | 0.972 |

**The line that decides it: `Z2`'s bright-blob coverage is 1.681 %, and the
image the pass was handed is 3.172 %.** At denoise 0.35 `#114` stops adding
bumps altogether — it comes out *below* its own input. At denoise 0.80 it comes
out at 8.191 %, roughly 2.6x what it received. Steps 30 at denoise 0.80 (`L0b`)
is 20.9 %, 6.6x.

**And denoise is the only `#114` setting that preserves anything of Luna.** The
handful of pigment marks that survive `#98` are visible in the tap of
`620:137`; at denoise 0.35 one of them comes through into the delivered frame
as a distinct brown mark on the cheek, and at denoise 0.80 it is gone. That is
the mechanism from §4 showing up in the image: denoise decides how much of the
input survives, so it is the *only* lever that can carry a real mark through.

**One honest negative: cf 1.5 does not improve this particular measure.** `Z0`
(cf 1.5) is 8.191 % against `L1b`'s (cf 3) 7.777 % on the same mask, with
denoise and steps identical. That is a **cheek** measurement and R3's case for
cf 1.5 is about the **philtrum, lips, chin and the jaw seam** — different
regions, and I am not contradicting it. But on the nose and upper cheeks, at
denoise 0.80, cf 1.5 is not the improvement; **denoise is.**

### cf 1.5 did engage, confirmed from the server's own log

`Detailer: segment upscale … crop region (w, h) x 1.0` lines inside each arm's
own `/history` execution window:

| arm | `#607` SDXL face | **`#114` Z-Image face** | `#165` mouth |
|---|---|---|---|
| `L0b`, `L1b`, `X2` *(cf 3)* | 1432x1840 | **2688x3456** = 9.29 MP | 1956x790 / 1827x768 / — |
| `Z0`, `Z1`, `Z2` *(cf 1.5)* | 1432x1840 | **2010x2859** = 5.75 MP | 1844x803 / 1848x798 / 1860x792 |

**cf 3 → 1.5 cuts what `#114` diffuses in one pass by 38 %**, 9.29 MP → 5.75 MP.
That is the server saying so, not my arithmetic.

**And `#165` ran in all four of my arms** (no `[filter]` line, and a wide
`x 1.0` crop present in each), so the four decision tiles do **not** split on
the mouth pass and are comparable across the whole face box. `X2` on the sheet
**did** drop it (`value=1773063` against the 1,700,000 gate) — one more reason
that tile is not comparable, on top of having no LoRAs.

### The full ladder

| arm | `#114` | pigment % | **bright-blob %** | luma L\* RMS *(fine texture)* | exec |
|---|---|---|---|---|---|
| — | *the input, `620:137`* | 2.096 | *3.172* | *1.262* | — |
| `Z0` | steps 8, den **0.80** | 3.252 | **8.191** | 1.459 | 270.5 s cold / 150.5 + 149.9 s warm |
| `Z1` | steps 8, den **0.50** | 0.652 | **1.659** | 0.883 | 145.2 s warm |
| `Z2` | steps 8, den **0.35** | 0.729 | **1.681** | **0.972** | 145.6 s warm |

**The step is between 0.80 and 0.50, not between 0.50 and 0.35.** Bright-blob
falls 8.191 → 1.659 and then stops moving. That matches the schedule
arithmetic in §4: at denoise 0.80 the pass starts at step 2 of a 10-step
schedule — near the top of the noise ladder — while 0.50 starts at 8 of 16 and
0.35 at 14 of 22, which are much closer to each other.

**But 0.35 is the better of the two, on two counts and both visible.** Its fine
texture is *higher* than 0.50's (luma RMS 0.972 against 0.883) — less
re-diffusion means more of the input's real pore structure survives — and it is
the only arm in which the pigment mark below the right eye, plainly present in
the `620:137` tap, **comes through into the delivered frame.** At 0.50 that
mark is gone. At 0.80 it is gone.

---

# 5b. The recommendation: **`#114 denoise` 0.80 → 0.35. Leave steps at 8.**

`OFMTech-NSFW/OFMTech_NSFW.json`, subgraph `5. Face & Mouth Detail (Z-Image)`,
node `#114`, `widgets_values[9]`, `0.8` → `0.35`. One float. **Nothing was
applied by me.**

**The sheet: `results/face/R1denoise_face_sheet1of1.png`** — 7 tiles, tight
face crop, 940x1180 each, 1:1 native, identical pinned box, all seven verified
byte-identical to their source crops. Row 1 is the three cf-3 tiles he has
already seen; rows 2–3 are the four cf-1.5 arms on the graph that ships. The
banner says which is which, and that `X2` has no LoRAs.

**In plain language about the skin, which is what he asked for.**

At the shipped **denoise 0.80** (`Z0`) the cheeks, nose and brow carry a fine
granular crust — much fainter than the 30-step render, but the surface still
reads like *orange peel* rather than skin. It is the same defect as before at
lower amplitude: small pale raised specks packed edge to edge, catching the
light. It is the pass adding texture that is not there.

At **denoise 0.35** (`Z2`) that is gone. The cheek is skin: even, with the fine
pore-scale texture that was already in the image before the face pass, lit
smoothly. The eyelashes are separate strands. The iris has structure in it
instead of being a flat disc. **And there is a small brown mark below the right
eye that is not in any of the 0.80 arms** — it is plainly there in the tap of
`620:137`, so it is real, and 0.35 is the only setting that carries it through.

**Denoise 0.50 (`Z1`) is the near miss.** It is almost as clean, but it is
*softer*: fine texture measures 0.883 against 0.35's 0.972, and the brown mark
is gone. It is the arm I would call airbrushed of the three. If the owner looks
at `Z2` and finds it too smooth, `Z1` is not the answer — `Z1` is smoother.

**Steps 30 at the same denoise (`Z3`) puts some of the crust back** — 3.364 %
bright-blob against `Z2`'s 1.681 % — and costs 53 s. It is the control that
shows the two levers are independent, and it is not the pick.

**What this does not do, and he should know before choosing:** it does **not**
bring back Luna's freckles. Those die at `#98`, two stages earlier (§3). The
one mark that `Z2` recovers is a survivor, not a restoration. If the freckles
matter more than the skin, the next investigation is `#98`, not `#114`.

**Cost: nothing.** In a matched 57-node cache, denoise 0.50 → 0.35 is 145.2 s
against 145.6 s. Denoise is free, from the source (§4) and from the clock.

**Where I would look next if he wants more texture than `Z2` gives.** Not a
higher denoise — that brings the crust back, which is what he rejected. The
texture ceiling is set by what `#98` hands `#114`, and `#98` is also what
removed the freckles. Both of his complaints point at the same node.

---

# 6. Timing — **the 189.3 s figure does not survive a cold cache**

The owner's question: `L0b` 400.7 s against `L1b` 189.3 s, but at 38 against 57
cached nodes. He asked for the real speedup with the cache cleared, or the word
unmeasured.

**The health control answers half of it directly, and it is not what the warm
numbers suggested.** It resubmitted `L1b`'s own `api_graph.json`
byte-identically after `POST /free {"unload_models": true, "free_memory": true}`
on an empty queue:

```
results/face/control/R1_control_L1b_repeat/meta.json
  status            success
  exec_seconds      388.9
  cached_nodes      0            <- genuinely cold, not "fewer cached"
  vs L1b's PNG      mean abs diff 0.0000, max 0 levels, 0.000 % of pixels over 8
```

**`L1b` cold is 388.9 s, not 189.3 s.** The 189.3 s was a warm figure with 57
nodes — including the entire base generator, both upscales and four VAE nodes —
served from cache. Against `L0b`'s 400.7 s at 38 cached, the honest reading of
the original pair is that **it compared a heavily cache-assisted run against a
partly cache-assisted one and the 53 % was mostly cache, not steps.**

That same control is worth keeping for a second reason: **two identical graphs,
one warm at 03:02 and one cold at 13:56, produced a delivered frame differing
by mean 0.0000 and maximum 0 levels.** This pipeline is bit-deterministic under
a fixed seed across a cold/warm boundary and an eleven-hour gap. Reported as
mean and maximum absolute difference, as a control on the instrument — this is
not the banned method, which is verifying that a *change* is inert by matching
output.

## The steps lever, measured properly: a matched-cache trio on the shipping graph

`Z1`, `Z2` and `Z3` ran back to back with **byte-identical `execution_cached`
sets** — 57 nodes, the same 57 node ids in all three, asserted not assumed. So
these three are comparable on time to each other:

| arm | `#114` | exec | cached |
|---|---|---|---|
| `Z1` | steps 8, denoise **0.50** | **145.2 s** | 57 (identical set) |
| `Z2` | steps 8, denoise **0.35** | **145.6 s** | 57 (identical set) |
| `Z3` | **steps 30**, denoise 0.35 | **198.7 s** | 57 (identical set) |

* **Denoise costs nothing: 145.2 s against 145.6 s, 0.4 s apart.** That is the
  source reading in §4 confirmed on the clock, in the owner's configuration,
  on the graph that ships.
* **Steps 30 → 8 saves 53.1 s of sampling, −26.7 %,** on a matched cache. That
  is the honest size of the steps lever once model loading is held constant —
  and it is a *sampling* figure, not a whole-render figure.

## What the cold/warm gap actually is, and why the old numbers were so large

The same graph, cold against warm:

| graph | cold | warm | difference |
|---|---|---|---|
| `L1b` (cf 3, steps 8, den 0.80) | **388.9 s** (0 cached) | 190.1 s (56 cached) | **198.8 s** |
| `Z0`/tap (cf 1.5, steps 8, den 0.80) | **270.5 s** (0 cached) | 150.5 and 149.9 s (57 cached) | **~120 s** |

**Roughly 120–200 s of a cold render on this pod is model loading, not
sampling.** That is larger than either lever under discussion, which is exactly
why every cross-cache comparison in this project has come out wrong. A number
from a warm run and a number from a cold run are not comparable even when they
are the same graph.

## The steps lever measured twice, independently, and the two agree

**Cold**, both from `/free` on an empty queue, both **0 cached**, both denoise
0.35, cf 1.5, LoRAs — and each re-render compared to its own arm's delivered
PNG at **mean absolute difference 0.0000, maximum 0 levels**, so they are the
same renders:

| arm | `#114` | cold exec |
|---|---|---|
| `Z2` | steps **8**, denoise 0.35 | **262.6 s** |
| `Z3` | steps **30**, denoise 0.35 | **315.5 s** |
| | | **−52.9 s, −16.8 % of the whole render** |

**Warm**, byte-identical 57-node cache sets: **−53.1 s.**

**52.9 s and 53.1 s.** Two measurements of the same lever from opposite cache
regimes, agreeing to 0.2 s. **That is the size of the steps lever**, and I am
confident in it in a way I am not confident in any single cold delta.

## Two cold deltas I will NOT quote as measurements, and why

* **cf 3 → cf 1.5, cold: `L1b` 388.9 s → `Z0` 270.5 s (−118.4 s).** That is
  *larger* than the ~38 s R3 measured for the pass itself, and `Z0` was also
  writing six extra full-resolution PNGs. Either something else got cheaper too
  or a single cold pair carries tens of seconds of load-time variance. **I am
  not claiming cf 1.5 saves 30 %.**
* **steps 30 → 8 at cf 3, cold: 417.5 s → 388.9 s (−28.6 s).** This one is
  *backwards on physics*: at cf 3 the pass diffuses 9.29 MP against 5.75 MP at
  cf 1.5, so 22 fewer steps should save **more** at cf 3, not half as much.
  Since the cf-1.5 pair is confirmed twice at ~53 s, the cf-3 cold pair's
  28.6 s is best read as that variance showing up.

**The conclusion the owner needs survives all of it**, because it does not
depend on any single cold delta: **the whole-render speedup from steps 30 → 8
is around 50 s — a sixth of a cold render, not a half.**

## The owner's own pair, cold against cold: **−6.9 %, not −53 %**

`L0b`'s own `api_graph.json` resubmitted byte-identically after `/free` on an
empty queue. It came back `success`, **0 cached nodes**, and **mean absolute
difference 0.0000 / maximum 0 levels** against `L0b`'s delivered PNG — so it is
the same render, not a re-roll.

| | what he was shown | **cold, 0 cached** |
|---|---|---|
| `L0b` steps 30, denoise 0.80, cf 3 | 400.7 s *(38 cached)* | **417.5 s** |
| `L1b` steps 8, denoise 0.80, cf 3 | 189.3 s *(57 cached)* | **388.9 s** |
| difference | −211.4 s, **−53 %** | **−28.6 s, −6.9 %** |

**The 53 % was cache.** With the cache cleared on both sides, changing `#114`
steps from 30 to 8 makes the whole render **6.9 % faster**, not 53 %.

**And I would not quote even the 28.6 s as the size of the steps lever** — see
the section above: it is backwards on physics against the cf-1.5 pair, which
was measured twice at ~53 s. What this pair establishes is the thing the owner
actually needs, and it does not depend on the exact delta: **with the cache
cleared on both sides, changing steps changes the render by tens of seconds out
of ~400, not by half.**

`HANDOFF.md` §4 currently carries two claims that both need this correction:
*"26 % faster, a lower bound"* (from `A0` 397.8 s at 31 cached against `C_08`
294.1 s at 8 cached — also not cold-vs-cold) and *"400.7 s → 189.3 s"*. Neither
pair had matched caches, and the phrase *"a lower bound"* is not supportable
when the faster arm had 23 fewer nodes cached in a regime where caching is
worth 120–200 s. **Steps 8 is still the right setting. It is a ~53 s saving on
a ~300–400 s render, and the pack should not promise 26 % or 53 %.**

---

# 7. Method and provenance

* Every arm is a scratch copy of `OFMTech-NSFW/OFMTech_NSFW.json`, built by an
  asserting script that checks **both** the `widgets_values` array length and
  the value currently at the index before writing. A desync aborts the build.
  `#114` has 29 entries = 28 widgets + the synthetic `control_after_generate`
  companion that `seed` (widget 3) drags in; index 5 = `steps` held `8`,
  index 9 = `denoise` held `0.8`, both verified against the file.
* Every arm passes `python3 tools/preflight/integrity.py <arm.json>` with
  **0 problems** before submission. All four did.
* Every arm is converted to API format by the real frontend —
  `tools/browser_harness/run.js --no-submit --api-out`, i.e.
  `app.loadGraphData()` + `app.graphToPrompt()` in Chromium against the live
  server, the same call the Run button makes. Nothing reached the server during
  conversion.
* Every submitted prompt is diffed against another submitted prompt with a
  node-by-node, input-by-input comparison:
  `Z1` and `Z2` differ from `Z0` by **exactly one input** (`620:114.denoise`);
  `Z3` by **two** (`denoise` + `steps`); `Z0` differs from `L1b` by exactly two
  (`620:114.bbox_crop_factor` 3 → 1.5 and `620:105.text` → `''`); and the tap
  arm differs from `Z0` by **six nodes added, zero removed, zero existing nodes
  changed**, so `#505`'s output is unaffected by the taps.
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
* **Every arm was checked for the two known server-fault signatures after it
  landed** — a large constant region at RGB (53, 47, 43), a black frame, or no
  variance in the face box — because a foreign job can poison the resident
  model between my renders and the failure is silent. All four came back
  `flat=0.00001 black=0.00000 faceStd≈44.5`, and the check is recorded in each
  `meta.json` under `health`.
* **Two duplicate drivers of my own were alive without my noticing**, which is
  why the tap render exists three times and the health control twice. Every
  duplicate was compared against the run I kept — mean 0.0000, max 0 levels, on
  all seven tap outputs both times — and then deleted. No conclusion in this
  report rests on a render whose `prompt_id` does not resolve in `/history`.
  It also cost the shared GPU about four wasted renders, which was my error.
* **Hash comparison of rendered output is not used as a verification method
  anywhere in this report.** Images are compared for equality in four places —
  the two base renders, the health control, the duplicate tap runs, and the
  cold timing re-runs — and every one is reported as mean and maximum absolute
  difference over the full frame. All four are controls on the instrument. None
  is used to argue that a change is inert.

---

# 8. What I could not establish, and where I would not guess

* **The whole run is one prompt, one seed, one composition** — a tight
  head-and-shoulders portrait with the face nearly filling the frame. Every
  claim about how the skin looks is about that face. `#98`'s effect on
  freckles, in particular, may well depend on how large the face sits in frame,
  because the 1.5x upscale is a fixed ratio and the freckles are a fixed
  physical size on the face.
* **I did not test `#98`.** I located it and stopped, as instructed. I do not
  know which part of it removes the pigment — the upscale model, the 1.5x
  resize, or the 2-step tiled re-diffusion at denoise 0.08 — and I am not
  guessing. Nor do I know whether any setting of it can preserve the freckles
  without costing something else.
* **cf 1.5 versus cf 3 on the cheek.** My mask says cf 1.5 is very slightly
  *worse* (8.191 % against 7.777 % bright-blob at identical steps and denoise).
  I report it because it is what I measured, but it is one region on one face
  and it is not the region R3's case rests on. **I am not claiming cf 1.5 is
  wrong**; I am claiming denoise is the lever for the cheek.
* **Denoise below 0.35 is untested.** The ladder stops there because that is
  what the brief asked for. 0.35 already sits below its own input on the
  bright-blob measure, so there may be nothing left to win, but I have not
  looked.
* **The freckle count is not a freckle count** (§1). I published the numbers
  and the reason they are not trustworthy rather than either hiding them or
  leaning on them.
* **Two arms in this run were rendered by a duplicate driver I had not noticed
  was still alive**, which is how the tap render came to exist twice. Both
  copies were compared (mean 0.0000, max 0) and one was deleted. Nothing was
  concluded from a render whose provenance I could not name, and every arm's
  `prompt_id` in `meta.json` resolves in `/history`.
* **The mouth and lips are not my finding to make.** `#165` ran in all four
  decision arms so they are internally comparable, but R3 owns the lip damage
  and I have deliberately not re-litigated it from my crops.
