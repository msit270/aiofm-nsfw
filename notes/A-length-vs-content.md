# TRACK A — is the face-prompt crash LENGTH or WORDS?

## **ANSWER: it is the LENGTH — specifically the TOKEN COUNT of the conditioning. No content I tested changed the outcome at any length.**

Every prompt whose tokenised length is **30, 31, 32, or 44 and above** crashes.
Every other length measured — 11, 12, 13, 14, 16, 20, 25, 26, 27, 28, 29, 33, 34,
35, 36, 37, 38, 39, 40, 41, 42, 43 — renders clean. **Its lower edge is exact; its top edge does not appear to
exist within reach**: 43 is clean and **44, 45, 46, 47, 48 and 49 all crash** —
six consecutive lengths, unbroken. So the upper region reads as a genuine
threshold at 44, not a band. Above 49 is unmeasured. **Across every cold arm in this run and eight unrelated content families there
is not one token count that gave two different outcomes.** That is a strong
statement about the lengths and content I measured; it is not a proof that no
string anywhere could break the pattern. Six completely
different 30-token strings all crash, including `"a woman's face"` (which renders
clean at 12 tokens) padded to 30 with repetitions of the word `the`, and they all
produce **bit-identical** output.

**Every crashing arm in the entire run — 18 of them, at 30, 31, 32, 44, 45, 46 and 47 tokens, across every content family and every crashing length — has a `621:163` that is
bit-identical to every other** (`max_abs_diff 0` over 2688×3456×3;
`results/crash/A/crash_identity.txt`). Once a prompt lands in a band the
conditioning stops affecting the image at all.

**In words the answer is "neither":** the word-count ladder is non-monotone (17
and 18 words crash, 19–23 are clean, 24 and 25 crash), and at a fixed 17 words
one stranger's description crashes while another is clean. Word count does not
predict anything. Token count predicts everything measured so far.

**What the crashing image is:** `620:114 FaceDetailer` returns a **pure black,
face-shaped hole** — exactly `(0,0,0)` over 1.57 M pixels, hair and background
untouched. `620:111 ImageColorMatch+` then colour-matches that black to the flat
`(56,51,47)` seen downstream. `face_yolov8m.pt` still scores the remaining head
silhouette at **0.466**, under the graph's **0.6**, so `622:424` returns zero
SEGS, `622:407` hands `622:403` an all-zero mask, and `MaskBoundingBox+` calls
`.min()` on an empty index tensor. Sheet: `results/crash/A/A4_contact_sheet.png`.

**SCOPE — read this before quoting any number here.** Everything below was
measured on **one instance, `127.0.0.1:18188`**, held constant across every arm.
Track D, on a third ComfyUI built from the shipped tarball, ran the same crash arm
and got a **clean render 3/3**. So the reproducer is environment-dependent, and
the specific token bands here may be a property of this box rather than of the
graph. What is instance-independent is the *method* and the *shape* of the result:
within one instance, outcome is a function of conditioning token count alone.
**Do not quote "30–32 and 44+" as a universal.**

Server: `127.0.0.1:18188` only. Nothing in this file touched 28191 or Track D's ports.
Graph: FROZEN. Every arm is an in-memory mutation of an already-submitted API
graph; `OFMTech-NSFW/OFMTech_NSFW.json` (`a811b5d6…`) was not edited.

---

## Method

### Where the arms branch from

Every arm below is a copy of `results/r4/R4_CF15_filled/api_graph.json` — the
**shipping** graph (`a811b5d6…`, `#114 bbox_crop_factor 1.5`) with the owner's
LoRAs loaded (`lunaskye` on `#618`, `luna` on `#116`), which crashed at
`622:403` on 2026-08-06 as `dd94393a`. Its clean twin,
`results/r4/R4_CF15_placeholder/api_graph.json`, differs from it in
`620:106.inputs.text` and nothing else.

### Tokenizer — the graph's own, and it is **not** the one the node label claims

`620:110 CLIPLoader` is set to `qwen.safetensors`, `type: lumina2`. **The
`lumina2` setting is not what decides the tokenizer.** `comfy/sd.py:1300`
dispatches on `detect_te_model(state_dict)` first and only uses `clip_type` as a
sub-discriminator. `qwen.safetensors` has
`model.layers.0.post_attention_layernorm.weight` shape `[2560]` **and**
`model.layers.0.self_attn.q_norm.weight`, which is `sd.py:1240` →
`TEModel.QWEN3_4B` → `sd.py:1382` → **`comfy.text_encoders.z_image.ZImageTokenizer`**
(a `Qwen2Tokenizer` over `comfy/text_encoders/qwen25_tokenizer`).

Two consequences, both measured not assumed:

* Token counts below are produced by instantiating that exact class offline.
* `Qwen3Tokenizer` is built with `max_length=99999999`, `pad_to_max_length=False`,
  `has_start_token=False`, `has_end_token=False`
  (`comfy/text_encoders/z_image.py:6-11`). **There is no 77-token limit and no
  truncation anywhere on this path.** 77 is a CLIP number and does not apply.
* `ZImageTokenizer` wraps every prompt in
  `<|im_start|>user\n{}<|im_end|>\n<|im_start|>assistant\n`, which costs a fixed
  **8 tokens**. So `tokens = 8 + content tokens`; the empty string is 8.

Reference counts (measured):

| string | tokens |
|---|---|
| `""` (empty) | 8 |
| `luna, ` | 12 |
| `a woman's face` | 12 |
| `TRIGGER, PROMPT FOR YOUR MODEL` (shipped placeholder) | 16 |
| the known-crashing string | **46** |

### Ladder token counts (measured with the same tokenizer)

| words | tokens | prefix |
|---|---|---|
| 0 | 8 | — |
| 1 | 11 | `luna,` |
| 2 | 12 | `luna, a` |
| 3 | 13 | `luna, a young` |
| 4 | 14 | `luna, a young woman` |
| 5 | 15 | `… with` |
| 6 | 16 | `… light` |
| 7 | 19 | `… freckles` |
| 8 | 20 | `… across` |
| 10 | 22 | `… her nose` |
| 12 | 25 | `… and cheeks,` |
| 14 | 27 | `… natural skin` |
| 16 | 29 | `… texture with` |
| 20 | 35 | `… visible pores, detailed eyes,` |
| 24 | 45 | `… photorealistic portrait photograph, 85mm` |
| 25 | 46 | the full string |

The crashing string is 25 words. The brief's ladder asked for up to 32 words;
32 does not exist, so the top rung is 25.

---

## A1 — the cheap probe, and it PASSED its validation gate

**Used: the probe.** Full renders were not needed.

**Design.** `620:106` feeds exactly one input, `620:114.positive`, and is not an
ancestor of `620:137` (walked the submitted graph: `620:137` has 47 ancestors,
none of them `620:10x`). So the base is rendered **once** and frozen:

| step | what | result |
|---|---|---|
| `A0_base_tap137` | graph pruned to the 47 ancestors of `620:137` + a `SaveImage` tap | success, 288.6 s, `cached 0`, 2688×3456, `luma_sd 59.77` |

That PNG is copied to `/workspace/ComfyUI/input/trackA_base137.png`
(`sha256 592894cd…`) and every arm loads it through a `LoadImage` wired into
`620:114.image` and `620:111.reference` in place of `620:137`. The arm graph is
then pruned to the ancestors of `505 SaveImage` plus a second `SaveImage` tap on
`621:163`; 38 nodes.

**The gate the brief demanded, both halves, before any result was read:**

| arm | `620:106.text` | expected | got | prompt_id |
|---|---|---|---|---|
| `A1_gate_crashstring` | the known-crashing 25-word string | crash at `622:403` | **error, `622:403 MaskBoundingBox+`, `RuntimeError: min(): Expected reduction dim to be specified for input.numel() == 0.`**, 61.7 s, `cached 0` | `19d04a85-30b5-4a4e-96b0-2865fd55597f` |
| `A1_gate_placeholder` | `TRIGGER, PROMPT FOR YOUR MODEL` | clean | **success**, 79.3 s, `cached 0`, image `HasMetadata_00060_.png`, `luma_sd 59.67`, `flat_frac 0.188` | `2dbc564d-a7dd-493c-b4c8-714332531d24` |

Same node, same exception text, same class as the four full-render crashes on
record. **Gate passed.** Cost per arm ~62–85 s instead of ~250 s.

One thing the probe does *not* reproduce and I am flagging it rather than
burying it: with the SDXL half pruned, `618`/the SDXL checkpoint are not resident,
so VRAM pressure is lower than in a full render. It did not stop the crash
reproducing, but it means the probe is not a memory-pressure model.

**A third check nobody asked for, because the gate is a two-cell test and I
wanted a continuous one.** The probe's clean arm produces the *whole* pipeline
output at `505`, so it can be compared pixel-for-pixel with the full render of
the same prompt (`R4_CF15_placeholder`, `HasMetadata_00059_.png`, 2688×3456):

```
A1_gate_placeholder (probe)  vs  R4_CF15_placeholder (full render)
  max_abs_diff 127   mean_abs_diff 0.735 levels   PSNR 44.93 dB
  fraction of pixels differing by more than 8 levels: 0.445 %
```

44.93 dB is a little below this project's measured run-to-run floor of ~48.7 dB,
which is what you would expect from forcing the base through an 8-bit PNG on the
way in. So the probe is not bit-exact with a full render and I am not claiming it
is — it is faithful to under one 8-bit level on average over 99.5 % of the frame,
on top of passing the crash/clean gate.

---

## A4 — what the failing detector is actually looking at

**Do this even if nothing else finishes** — so it was done second, right after the
gate, and it is the strongest thing in this file.

`621:163` is the exact image handed to `622:424`; `622:431` between them is only
`INSTARAW_ImageListFromBatch`, a batch→list reshape that does not touch pixels.
The tap fired on **both** arms, including the crashing one.

Then, offline, no ComfyUI: `YOLO('bbox/face_yolov8m.pt')(pil, conf=t)` — which is
literally the graph's own call (`ComfyUI-Impact-Subpack/modules/subcore.py:319-325`,
`inference_bbox`: `pred = model(image, conf=confidence, device=device)`).

| image | 0.6 *(the graph's value)* | 0.5 | 0.4 | 0.3 | 0.2 | 0.1 | highest conf |
|---|---|---|---|---|---|---|---|
| base `620:137` (before the face pass) | 1 | 1 | 1 | 1 | 1 | 1 | **0.894** |
| CLEAN arm `621:163` (placeholder) | 1 | 1 | 1 | 1 | 1 | 1 | **0.895** |
| CRASHING arm `621:163` | **0** | **0** | 1 | 1 | 1 | 1 | **0.466** |

Boxes, for scale: clean `[855.7, 789.7, 2193.1, 2697.6]`, crash
`[847.9, 809.5, 2185.9, 2725.1]` — the same head, within ~30 px. The detector has
not lost the head. It has lost confidence, from 0.895 to 0.466, and the graph's
threshold is 0.6.

### What the crashing image looks like, in plain language

**The face is gone. It is a solid, flat, dark grey-brown blob with a soft edge,
in the exact shape of the face** — jaw, chin and hairline outline preserved, and
nothing inside it. No eyes, no nose, no mouth, no skin texture, no shading. The
blonde hair around it, the shoulders and the background are untouched and still
photographic. It looks like someone has cut the face out and filled the hole with
a single dark colour.

Objectively: `flat_frac` (fraction of horizontally adjacent pixel pairs differing
by < 0.5 of an 8-bit level) is **0.359** on the crashing image against **0.188**
on the clean one and **0.186** on the base — a huge featureless region appearing
where a face was.

### So which of the brief's two worlds is this? **Both halves are true and they matter differently**

* *"crashing image has NO face a human would recognise → the face pass destroyed
  it."* **Yes.** A human shown this would say there is no face. `620:114` at
  denoise 0.80, cfg 1, with this prompt as its only conditioning, replaced the
  face with a void. That is the root cause and it is upstream of the detector.
* *"crashing image has an obvious face but YOLO scores it under 0.6 → a
  threshold problem."* **Also literally true, and it is why it is a crash rather
  than a bad image.** YOLO still fires at **0.466** on the head silhouette (hair
  outline + head shape are intact), so it is only the 0.6 threshold that turns
  "badly damaged face" into "zero detections". At threshold ≤ 0.4 this same image
  detects, `622:407` gets a non-empty mask, and `622:403` never sees an empty
  index tensor.

**The practical consequence, stated carefully:** lowering `622:424.threshold` to
0.4 would very likely convert this crash into a *completed render of a faceless
image*, which is a different defect, not a fix. **[I]** The fix has to be both:
a guard at the empty-mask boundary so the pipeline degrades instead of dying,
*and* whatever stops `620:114` erasing the face. Track A's job is the second.

Sheet: `results/crash/A/A4_contact_sheet.png` (2776×2354, both panels at 1:1,
same pixel region, red header because the two panels are different
configurations). Raw numbers: `results/crash/A/yolo_A4.json`.

---

## A2 — the length ladder, and it does not behave like a ladder

Same words, same order, truncated. Ascending. `POST /free {"unload_models":true,
"free_memory":true}` before every arm; **every arm reports `execution_cached: []`**
(the `cached` column below is the length of that list). After **every** error arm
the driver re-ran a byte-identical known-clean arm before continuing — the
`CTL_placeholder_*` rows — and every one came back clean, so no result here sits
on an unproven server.

`conf @621:163` is not from the graph. It is the graph's own detector run offline
on that arm's `621:163` tap — `YOLO('bbox/face_yolov8m.pt')(pil, conf=0.1)`,
highest confidence returned. **The graph's threshold is 0.6**, so `n@0.6` is the
number of SEGS `622:424` produces, and `n@0.6 = 0` is exactly the condition that
empties the mask and kills `622:403`.

| arm | words | tokens | status | exec s | cached | conf @621:163 | n@0.6 | flat_frac | prompt_id |
|---|---|---|---|---|---|---|---|---|---|
| `A0_base_tap137` | 0 | — | success | 288.6 | 0 | — | None | None | `24792430-0cd0-422f-9a05-86fdbdc0be13` |
| `A1_gate_placeholder` | 5 | — | success | 79.3 | 0 | 0.8953 | 1 | 0.1876 | `2dbc564d-a7dd-493c-b4c8-714332531d24` |
| `L_w01` | 1 | 11 | success | 83.3 | 0 | 0.8956 | 1 | 0.1877 | `e1bc802e-aa98-4e6e-a879-ae0cb7699e06` |
| `L_w02` | 2 | 12 | success | 61.7 | 0 | 0.8955 | 1 | 0.1878 | `19a9ddb5-2c4d-4144-b578-acc03c05f83a` |
| `L_w03` | 3 | 13 | success | 78.7 | 0 | 0.8956 | 1 | 0.1877 | `20f74567-7dd1-492d-9e6f-bb6222706eb7` |
| `L_w04` | 4 | 14 | success | 73.3 | 0 | 0.8956 | 1 | 0.1876 | `60f32dfc-f4b7-4199-ae3c-fee4a2d1b9a5` |
| `L_w06` | 6 | 16 | success | 71.4 | 0 | 0.8957 | 1 | 0.1878 | `572d2e9e-75c3-4064-abde-777776faeb4a` |
| `L_w08` | 8 | 20 | success | 53.9 | 0 | 0.8946 | 1 | 0.186 | `ab70ad85-b7a9-465e-9473-b13c6f0de022` |
| `L_w12` | 12 | 25 | success | 74.9 | 0 | 0.8946 | 1 | 0.1865 | `a3203c74-0bc5-4f50-b006-a4cec3f56460` |
| `L_w16` | 16 | 29 | success | 77.6 | 0 | 0.8945 | 1 | 0.1859 | `5901322d-016a-4790-ad36-ed92d833fb7f` |
| `L_w17` | 17 | 30 | **ERROR 622:403** | 56.9 | 0 | 0.4656 | 0 | 0.3591 | `43870c71-3563-4132-bfbe-b3cd8440e8ab` |
| `L_w18` | 18 | 32 | **ERROR 622:403** | 62.1 | 0 | 0.4656 | 0 | 0.3591 | `91fb3cbb-f66b-424c-b3c8-ca3d64a56a66` |
| `L_w19` | 19 | 33 | success | 61.5 | 0 | 0.8949 | 1 | 0.186 | `88cb5e94-56cf-4ccb-ad6d-d126953b63bc` |
| `L_w20` | 20 | 35 | success | 75.2 | 0 | 0.8948 | 1 | 0.186 | `6e284102-bfbb-470d-b038-95fca0abc442` |
| `L_w21` | 21 | 38 | success | 76.1 | 0 | 0.8948 | 1 | 0.1861 | `fe20c212-383e-421c-88de-fc17256576f1` |
| `L_w22` | 22 | 39 | success | 81.8 | 0 | 0.8949 | 1 | 0.1862 | `c2e847c0-22f9-4053-a238-7259b4df7645` |
| `L_w23` | 23 | 41 | success | 60.1 | 0 | 0.8948 | 1 | 0.1859 | `568d2865-fbf1-4412-807c-51aac4736199` |
| `L_w24` | 24 | 45 | **ERROR 622:403** | 56.7 | 0 | 0.4656 | 0 | 0.3591 | `ee211b4e-c623-4060-8e94-9d9ee52bf17f` |
| `A1_gate_crashstring` | 25 | — | **ERROR 622:403** | 61.7 | 0 | 0.4656 | 0 | 0.3591 | `19d04a85-30b5-4a4e-96b0-2865fd55597f` |
| `CTL_placeholder_after_w17` | 5 | — | success | 79.7 | 0 | 0.8953 | 1 | 0.1876 | `26550005-e817-48e8-8db5-c9996ff0f451` |
| `CTL_placeholder_after_w18` | 5 | — | success | 80.6 | 0 | 0.8953 | 1 | 0.1876 | `0b7a90f7-a14c-4761-a7c9-36d0ab4d3b3d` |
| `CTL_placeholder_after_w24` | 5 | — | success | 69.3 | 0 | 0.8953 | 1 | 0.1876 | `88c2e96f-a527-442b-aeb5-891eaecb6908` |

*(`A1_gate_crashstring` is the full 25-word string; the table's tokeniser column
only auto-fills for the `L_w*` names — measured directly it is **46 tokens**.
`A1_gate_placeholder` and the `CTL_*` rows are the 4-word shipped placeholder,
16 tokens; the "5 words" in their word column is the naive whitespace split of
`TRIGGER, PROMPT FOR YOUR MODEL`. Every arm's full `/history` JSON, including the
verbatim traceback, is in `results/crash/A/history/`.)*

### The result: **17 and 18 crash; 19, 20, 21, 22 and 23 are clean; 24 and 25 crash again**

```
words   1  2  3  4  6  8 12 16 |17 18| 19 20 21 22 23 |24 25|
tokens 11 12 13 14 16 20 25 29 |30 32| 33 35 38 39 41 |45 46|
        .  .  .  .  .  .  .  . | X  X |  .  .  .  .  . | X  X |
```

**That is not monotone, and a non-monotone crash set cannot be produced by a
length threshold of any kind.** (It *is* produced by two narrow bands of
unsafe **token** counts — see the T section. Words 17 and 18 are 30 and 32
tokens; words 19–23 are 33–41; words 24 and 25 are 45 and 46. The word ladder
looks erratic only because words map onto tokens unevenly.) 19 words / 33 tokens is *longer* than 17 words /
30 tokens on both counts and it renders clean. There is no cut-off T such that
"crashes iff length ≥ T".

The first crash is at **17 words / 30 tokens**. That number is worth having and
it is what I used to set the length of the A3 controls, but it is a first
occurrence, not a boundary. **30 is not a round number**, it is not 77 — and 77
could not have applied anyway, because `620:110` resolves to a Qwen3-4B
`ZImageTokenizer` with `max_length=99999999` and no truncation on any path.
Subtracting the fixed 8-token chat template leaves 22 content tokens, which is
not round either.

### The transition is a cliff at every crossing, in both directions

Face confidence at `621:163` is **0.8944–0.8957 on all thirteen clean arms** and
**0.4656 on all four crashing arms**. Nothing in between, at any word count. The
pixel measurements agree:

```
L_w16 vs A1_gate_placeholder   max 59   mean  0.23 levels   PSNR 50.94 dB   <- 16 words barely moves the frame
L_w16 vs L_w24                 max 182  mean 34.16 levels   PSNR 14.35 dB   <- crossing destroys it
L_w01 vs A1_gate_placeholder   max 27   mean  0.10 levels   PSNR 56.40 dB
```

### Past a crossing the output stops depending on the prompt at all

```
L_w17 vs L_w18                 max_abs_diff 0   mean 0.00000    (2688 x 3456 x 3)
L_w17 vs L_w24                 max_abs_diff 0   mean 0.00000
L_w17 vs A1_gate_crashstring   max_abs_diff 0   mean 0.00000
```

Four different prompts, 17 / 18 / 24 / 25 words, **bit-identical** output.

Controls that this is determinism and not a stuck server: the three
`CTL_placeholder_*` health arms are likewise bit-identical to
`A1_gate_placeholder` (every seed in the graph is `fixed` and the base image is
frozen, so that is expected) — **and the clean arms are *not* identical to each
other**: `L_w01` vs the placeholder is PSNR 56.40 and `L_w16` vs the placeholder
is 50.94. The pipeline does respond to the prompt, continuously, right up to the
moment it collapses.

**What that rules out.** It is not "the prompt steers the sample somewhere that
isn't a face" — that story predicts prompt-dependent garbage. This is a single
attractor: cross into it from any direction and you get the identical frame.

### The failure output is a mathematically flat constant

A 600×600 patch at the centre of the face box, on the crashing frame:

```
mean RGB (56, 51, 47)     std (0.000, 0.000, 0.000)     unique colours in 360,000 px: 1
that exact RGB triple covers 16.97 % of the whole 2688 x 3456 frame
```

Standard deviation **exactly zero** over 360,000 pixels. That is not a diffusion
model drawing the wrong thing; that is a fill.

Two offline checks on what could and could not produce it, both against the
graph's own `ae.safetensors` (`620:109`):

* **Not a VAE decode of a constant latent.** Decoding `torch.full((1,16,32,32), v)`
  for v ∈ {−1000, −100, −30, −10, −5, −3, −2, −1, −0.5, 0, 0.5, 1, 2, 3, 5, 10,
  30, 100, 1000} never gives a flat image — residual spatial sd is 2.3–14.5
  levels at every value, and the closest colour (v = −1000 → RGB 58, 3, 44) is
  still ~18 levels off with sd ≈ 14.
* **Not a NaN falling through to `SaveImage`.** `np.clip(255*nan, 0, 255).astype(uint8)`
  is `0` — black — not (56, 51, 47).

**[I] So something substitutes a solid fill for the face crop rather than a model
output being decoded.** I have not identified what and will not name a mechanism
I cannot point at a line for. The `TAP114_*` arms below tap `620:114`'s raw
output, before `620:111`'s colour match, to localise it.


---

## A3 — content control, and it turned the answer over

Seven arms, all at **17 words** — the first word count that crashes — each
differing from every other arm in `620:106.inputs.text` and nothing else
(`results/crash/A/graph_diffs.txt`). `POST /free` before each; every one reports
`execution_cached: []`; every error arm was followed by a byte-identical
known-clean control and all of those came back clean.

Four are *content controls*: a completely different subject, no `luna`, no
freckles, no camera words. Three are *swap controls*: the *clean* 16-word prefix
with a different 17th word, so word count **and** token count both match the
crashing `L_w17` exactly.

| arm | words | tokens | status | exec s | cached | conf @621:163 | n@0.6 | flat_frac | prompt_id |
|---|---|---|---|---|---|---|---|---|---|
| `A3_C1_fisherman_w17` | 17 | 34 | success | 79.9 | 0 | 0.8944 | 1 | 0.1855 | `185cb8f6-1890-4bfa-b216-88b9b4fea7c7` |
| `A3_C2_gardener_w17` | 17 | 30 | **ERROR 622:403** | 41.5 | 0 | 0.4656 | 0 | 0.3591 | `c71446c4-68eb-4c68-a4cf-63a9d00d7188` |
| `A3_C3_locomotive_w17` | 17 | 35 | success | 83.7 | 0 | 0.8942 | 1 | 0.1862 | `719863c8-1fe1-40f0-b68c-a8a201834b2e` |
| `A3_C4_committee_w17` | 17 | 26 | success | 75.1 | 0 | 0.8954 | 1 | 0.1879 | `a69e50d1-972b-4f41-925f-c31c0717417b` |
| `A3_swap_fine` | 17 | 30 | **ERROR 622:403** | 49.6 | 0 | 0.4656 | 0 | 0.3591 | `ac2c390f-03c5-4058-9487-6af06a18d175` |
| `A3_swap_Tuesday` | 17 | 30 | **ERROR 622:403** | 57.3 | 0 | 0.4656 | 0 | 0.3591 | `8e988367-7988-4604-a269-1ddd42c6e28a` |
| `A3_swap_obvious` | 17 | 30 | **ERROR 622:403** | 52.9 | 0 | 0.4656 | 0 | 0.3591 | `164d181c-5446-4915-9931-c9af9bfdd3ee` |

The strings, in full:

```
A3_C1_fisherman_w17   a bearded fisherman in his sixties, deep lines around the eyes, sun-darkened forehead, grey stubble along the
A3_C2_gardener_w17    an elderly gardener with a broad flat nose, heavy grey eyebrows, deep creases on both cheeks, a
A3_C3_locomotive_w17  a rusting freight locomotive parked on overgrown sidings, bramble climbing the couplings, chipped enamel plates, oil stains
A3_C4_committee_w17   the committee approved the revised schedule on Tuesday and asked the treasurer to circulate a summary before
A3_swap_fine          luna, a young woman with light freckles across her nose and cheeks, natural skin texture with fine
A3_swap_Tuesday       luna, a young woman with light freckles across her nose and cheeks, natural skin texture with Tuesday
A3_swap_obvious       luna, a young woman with light freckles across her nose and cheeks, natural skin texture with obvious
```

### The result is not "words" and it is not "length as a threshold"

Same-length-different-content came back **split**, and the split is not random —
it lines up exactly with the **token** count:

* `A3_C2_gardener_w17` shares **no words** with the crashing string, describes a
  different person, and **crashes**. It is 30 tokens.
* `A3_C1_fisherman_w17` (34 tokens), `A3_C3_locomotive_w17` (35 tokens) and
  `A3_C4_committee_w17` (26 tokens) are **clean**.
* All three swap arms are 30 tokens and **all three crash** — including
  `A3_swap_Tuesday`, which is a grammatically broken sentence
  (`…natural skin texture with Tuesday`), and `A3_swap_obvious`. So it is not
  the word `visible`, and it is not the meaning of the clause.

Put the ladder and A3 together and every crashing arm so far is **30, 32, 45 or
46 tokens**, and every clean arm is 11–29, 33, 34, 35, 38, 39 or 41:

```
tokens   11 12 13 14 16 20 25 26 29 |30| 31? |32| 33 34 35 38 39 41 |45 46|
outcome   .  .  .  .  .  .  .  .  . | X |  ?  | X |  .  .  .  .  .  . | X  X |
n crashing strings measured at 30 tokens: 5, sharing no common vocabulary
```

**Five unrelated strings at 30 tokens all crash. Nine strings at other lengths,
including two longer 17-word ones, are all clean.** That is not a content
effect. It also is not a threshold, because 33, 34, 35, 38, 39 and 41 tokens are
all clean and 30 is not.

### And the crashing frames are the same pixels regardless of what the words were

```
A3_C2_gardener_w17  vs  L_w17     max_abs_diff 0   mean 0.00000   (2688 x 3456 x 3)
```

A description of an elderly male gardener and a description of a freckled young
woman, run through the same face pass, produce **bit-identical** output. The
conditioning has stopped mattering entirely.

### One more thing this exposes about `#106` — it barely matters even when it works

On the clean side, changing `620:106` moves the frame by about as much as
re-running the graph would:

```
A3_C1_fisherman_w17 vs A1_gate_placeholder   PSNR 48.27 dB   mean 0.35 levels   0.25 % of pixels beyond 8 levels
A3_C1_fisherman_w17 vs L_w16                 PSNR 48.48 dB   mean 0.31 levels   0.28 %
L_w19               vs A1_gate_placeholder   PSNR 49.01 dB   mean 0.27 levels   0.23 %
```

This project's measured run-to-run floor is ~48.7 dB. So a 17-word description of
a **bearded fisherman**, applied at denoise 0.80 to a young woman's face, changes
the output by roughly the noise floor — the rendered face is still recognisably
the same woman (`results/crash/A/thumbs/A3_C1_fisherman_w17__tap163_facebox_half.png`).
Corroborates R4 §2's 1.28 %. **So `#106` has almost no semantic authority over
the image, and can still detonate the pass.** Whatever this is, it is not the
model "listening to the prompt and drawing something else".

### The experiment this forces — `T_tok*`

Content is now the *controlled* variable and length is the one under test. Fixed
phrase `"a woman's face"` (12 tokens, known clean) plus k repetitions of the
single-token word `" the"`, giving **exactly** 12+k tokens with the semantics
held as constant as I can make them. Sweeping 26–36, then 44–47.

* If 30 and 32 crash and 29, 31, 33 do not → **it is the token count**, full stop.
* If none of them crash → 30 tokens is not sufficient on its own and the five
  hits are an interaction I have not isolated.

Results below.

---

## Where the black comes from — `620:114` localised by a tap

Two arms, graph truncated at `621:163` so they cannot reach `622:403`, each with
a `SaveImage` on **`620:114`'s raw output** (before `620:111`'s colour match).
Both cold, both `success`.

| arm | `620:106.text` | exact-(0,0,0) fraction of frame | unique colours in a 600×600 centre patch |
|---|---|---|---|
| `TAP114_w17` | the 17-word / 30-token crashing string | **0.1694** | **1** — `[0, 0, 0]` |
| `TAP114_placeholder` | the shipped placeholder | **0.0000** | 39,957 |

**`620:114 FaceDetailer` returns a pure-black, face-shaped region.** Not dark, not
noisy — exactly `(0, 0, 0)` over 1.57 million pixels, with the hair, shoulders and
background around it untouched. `results/crash/A/thumbs/TAP114_w17__*.png`.

### Which also explains the (56, 51, 47) that shows up two nodes later

`620:111 ImageColorMatch+` is a **global** per-channel mean/std transfer
(`ComfyUI_essentials/image.py:1220-1241`: `matched = nan_to_num((image - image_mean)
/ image_std) * nan_to_num(reference_std) + reference_mean`, statistics taken over
the whole frame). A black hole covering 17 % of the image drags the frame
statistics, and the affine map sends `0` to a lifted constant. That is the
(56, 51, 47) seen at `621:163`. Nothing is "filling" the face at that stage; it is
black being colour-matched.

### And it rules NaN out, which the earlier evidence could not

`compute_mean_std` uses plain `tensor.mean()`. **A single NaN anywhere in
`620:114`'s output would make `image_mean` NaN, `(image - mean)/std` NaN,
`nan_to_num` would send the whole thing to 0, and every pixel of `621:163` would
be the same constant.** It is not — the hair and background at `621:163` are
normal, detailed pixels. So `620:114` emitted **honest zeros, not NaNs**.

That matters because "a NaN poisoned the render" is the story `HANDOFF.md` §7.1
tells about the *other* failure mode, and this is not that. The pass ran to
completion: the server log shows the face pass doing its normal thing —
`Detailer: force inpaint` · `Detailer: segment upscale for ((1340.1992,
1906.2034)) | crop region (2010, 2859) x 1.0` · eight sampler steps at ~2.5 s/it ·
`[Impact Pack] vae decoded in 1.4s` — and no warning of any kind. Then the mouth
pass finds no lips (no second `Detailer:` line at all in a crashing block, against
three `Detailer:` lines in every clean one) and `622:424` finds no face.

**[I] What I have not identified** is why eight steps of the Z-Image sampler on a
2010×2859 crop return black for a 30-token conditioning and a face for a 29- or
34-token one. That is a model/sampler question, not a graph question, and it is
the right thing to hand to whoever owns the Z-Image side.

---

## T — the token-count sweep, with content held constant

The design. Fixed phrase **`"a woman's face"`** — 12 tokens, and already on record
as clean at that length (R4's narrowing arm B, and again here) — plus *k*
repetitions of the single-token word `" the"`. That gives **exactly 12+k tokens**
with the semantic content held as close to constant as a prompt can be. So token
count is the only variable that moves.

Preceded by `CTL_recovery_before_T` (the shipped placeholder, byte-identical
graph, **success, 79.0 s, `cached 0`**) because the previous health control had
failed — see `A-questions.md`. Every arm below is cold, every error arm was
followed by a clean byte-identical control.

| arm | text | tokens | status | exec | cached | conf @621:163 |
|---|---|---|---|---|---|---|
| `T_tok29` | `a woman's face` + 17×`the` | 29 | success | 74.4 s | 0 | 0.8954 |
| `T_tok30` | + 18×`the` | **30** | **ERROR `622:403`** | 48.1 s | 0 | 0.4656 |
| `T_tok31` | + 19×`the` | **31** | **ERROR `622:403`** | 71.6 s | 0 | 0.4656 |
| `T_tok32` | + 20×`the` | **32** | **ERROR `622:403`** | 56.9 s | 0 | 0.4656 |
| `T_tok33` | + 21×`the` | 33 | success | 76.4 s | 0 | 0.8952 |
| `T_tok46` | + 34×`the` | **46** | **ERROR `622:403`** | 61.4 s | 0 | 0.4656 |

`T_tok30`, `T_tok31`, `T_tok32` and `T_tok46` are all **bit-identical** to
`L_w17` (`max_abs_diff 0` over 2688×3456×3) — a string of the word `the` and a
seven-clause character description produce the same pixels.

### The pooled map — every arm, every content family, one row per token count

```
tok  verdict  n  arms
  11  clean    1  L_w01
  12  clean    1  L_w02
  13  clean    1  L_w03
  14  clean    1  L_w04
  16  clean   19  A1_gate_placeholder, CTL_placeholder_after_w17, CTL_placeholder_after_w18, CTL_placeholder_after_w24, L_w06, CTL_placeholder_after_A3_C2_gardener_w17, CTL_placeholder_after_A3_swap_Tuesday, CTL_placeholder_after_A3_swap_fine, CTL_placeholder_after_A3_swap_obvious, CTL_recovery_before_T, CTL_placeholder_after_T_tok30, CTL_placeholder_after_T_tok31, CTL_placeholder_after_T_tok32, CTL_placeholder_after_T_tok45, CTL_placeholder_after_T_tok46, CTL_placeholder_after_T_tok44, CTL_placeholder_after_T_tok47, CTL_placeholder_after_REP2_w17__warm2, CTL_placeholder_after_T_tok48
  20  clean    1  L_w08
  25  clean    1  L_w12
  26  clean    2  A3_C4_committee_w17, T_tok26
  27  clean    1  T_tok27
  28  clean    1  T_tok28__warm2
  29  clean    2  L_w16, T_tok29
  30  CRASH    7  L_w17, A3_C2_gardener_w17, A3_swap_fine, A3_swap_Tuesday, A3_swap_obvious, T_tok30, REP2_w17
  31  CRASH    1  T_tok31
  32  CRASH    2  L_w18, T_tok32
  33  clean    3  L_w19, T_tok33, REP2_w19
  34  clean    2  A3_C1_fisherman_w17, T_tok34
  35  clean    3  L_w20, A3_C3_locomotive_w17, T_tok35
  36  clean    1  T_tok36
  37  clean    1  T_tok37
  38  clean    1  L_w21
  39  clean    1  L_w22
  40  clean    1  T_tok40
  41  clean    1  L_w23
  42  clean    1  T_tok42
  43  clean    1  T_tok43
  44  CRASH    1  T_tok44
  45  CRASH    2  L_w24, T_tok45
  46  CRASH    2  A1_gate_crashstring, T_tok46
  47  CRASH    1  T_tok47
  48  CRASH    1  T_tok48
  49  CRASH    1  T_tok49

MIXED (same token count, different outcome): none
```

**Not one MIXED cell.** Every token count measured more than once agrees with
itself, across families that share no vocabulary:

* **30 tokens — 6 arms, 6 crashes.** A character description, a stranger's face,
  three grammatically-broken swaps (`…texture with Tuesday`), and pure filler.
* **33 tokens — 2 arms, both clean.** A character description and pure filler.
* **35 tokens — 2 arms, both clean.** A character description and a locomotive.
* **29 tokens — 2 arms, both clean.** **32 tokens — 2 arms, both crash.**
* **16 tokens — 13 arms, all clean.** (The shipped placeholder and every health
  control.)

Sheet: **`results/crash/A/T_token_sweep_sheet.png`** — the same prompt at 26–49
tokens. 26–29 clean · **30, 31, 32 crash** · 33–37, 40, 42, 43 clean ·
**44, 45, 46, 47, 48, 49 crash**. Nothing changes between panels except how
many times the word `the` is repeated.

### So the answer to A3, in one sentence

**It is the length, measured in tokens, and it is not a threshold — the unsafe
lengths are the band [30, 32] and everything from 44 up; content has no effect whatsoever, and
five different 17-word prompts split clean/crash purely on their token count.**

### Two things this does NOT say

* **It is not "long prompts are unsafe".** 33, 34, 35, 38, 39 and 41 tokens are
  all clean and all longer than 32. A buyer's prompt can be *lengthened* out of
  the crash — adding one word to a 30-token prompt is a workaround.
* **The bands are not yet fully mapped.** The wide sweep (13–28, 34–44, 47–50 in
  the `T` family) is queued; until it lands I only claim the values in the table
  above. **[I]** Two bands of width 3 and 2 at 30–32 and 45–46 look like they
  ought to mean something — the gap is 11 — but I have no
  mechanism for it and will not invent one.

---

## What this means for the graph that ships

Every live `CLIPTextEncode` on this encoder, token-counted with the encoder's own
tokeniser against the **frozen** `OFMTech-NSFW/OFMTech_NSFW.json` (`a811b5d6…`).
All five resolve to `620:110` in the API graph, so all five are exposed to the
same bands:

| node | title | text | tokens | |
|---|---|---|---|---|
| `#106` | Face Detailer Prompt | `TRIGGER, PROMPT FOR YOUR MODEL` | **16** | safe |
| `#105` | Face Detailer Negative | `""` | 8 | safe (and unused — see below) |
| `#166` | Mouth Detailer Prompt | `realistic detailed mouth` | 12 | safe |
| `#167` | Mouth Detailer Negative | `""` | 8 | safe |
| `#394` | Eye Negative Prompt | `""` | 8 | safe |
| `#398` | Eye Positive Prompt | `perfect eyes, round pupils, round iris, symmetrical eyes, realistic eyes, perfect circles, round` | **28** | **safe by two tokens** |

**As shipped, nothing is in a band.** But `#398` sits **two tokens below [30, 32]**
and it is not a field anyone is told to leave alone. Adding "and clear" to the eye
prompt would put it at 31 and silently black out the eye pass.
**[I]** I have not rendered that; it is a prediction from the map, and it is the
single cheapest arm anyone could run to test whether the bands are a property of
the encoder rather than of `620:114` specifically.

One dead one worth writing down: `sg7 · Anatomy Detailers`, `#240 Pussy Detailer
Prompt`, is **31 tokens** — inside the band. That whole subgraph is bypassed, so
it does nothing today, but anyone reviving it is one render from the same crash.

The negatives being empty is not a safety margin, it is a no-op: `#114` and
`#165` run at **cfg 1**, and `comfy/samplers.py:370` skips the uncond pass
entirely when `cond_scale` is 1. The positive is the only conditioning that is
evaluated at all.

### The practical shape of the risk

A buyer following root `#649` §3 — *"replace `TRIGGER, PROMPT FOR YOUR MODEL`
with your LoRA's trigger word and a short description"* — is writing a string of
unknown token length into `#106`. Five of the 38 lengths between 11 and 48 are
known-fatal. **[I]** If the bands are exactly [30, 32] ∪ [44, …] then that is
5 in 38, and a "short description" lands in exactly that range. This is not a
rare corner.

**The workaround is one word.** Adding or deleting a single word moves the count
out of the band — 33 tokens is clean, 29 is clean. That is worth knowing before
any deeper fix exists.

**Two independent defects, and both need fixing:**

1. **`622:403 MaskBoundingBox+` turns "detector found nothing" into a
   `RuntimeError`.** `ComfyUI_essentials/mask.py:184` calls `.min()` on an empty
   index tensor. Any cause of an undetectable face is a dead render instead of a
   bad one. This is the one that makes the other one fatal.
2. **`620:114` returns a black crop at certain conditioning lengths.** That is the
   actual fault and it is upstream of everything else. It is a Z-Image /
   sampler-level question, not a graph-wiring one.

Lowering `622:424.threshold` from 0.6 to 0.4 would make the crashing image detect
(it scores 0.466) — but that converts a crash into **a delivered image with no
face**. That is not a fix, and I would not ship it as one.


---

## A4, re-read as the decisive experiment — and it refutes marginal detection

The coordinator's hypothesis after Track D failed to reproduce on a third
instance: *the long prompt does not destroy the face, it pushes YOLO's confidence
to sit near 0.6, so the outcome flips between boxes.* **The numbers say no.**

### 1. Max confidence, crashing vs clean

`YOLO('bbox/face_yolov8m.pt')(pil, conf=t)` — the graph's own call
(`ComfyUI-Impact-Subpack/modules/subcore.py:319-325`) — on the `621:163` tap, the
exact image handed to `622:424`:

| image | 0.6 *(graph)* | 0.5 | 0.4 | 0.3 | 0.2 | 0.1 | **max conf** |
|---|---|---|---|---|---|---|---|
| base `620:137`, before the face pass | 1 | 1 | 1 | 1 | 1 | 1 | **0.8936** |
| CLEAN arm (placeholder, 16 tok) | 1 | 1 | 1 | 1 | 1 | 1 | **0.8953** |
| CRASHING arm (25 words, 46 tok) | **0** | **0** | 1 | 1 | 1 | 1 | **0.4656** |

### 2. Does confidence vary smoothly with token count? **No. It is a two-valued step, and there is nothing in between.**

Across **every** ladder, content-control and token-sweep arm — 22 distinct token
counts from 11 to 47 — the offline confidence takes exactly two values:

```
every CLEAN arm    conf 0.8942 - 0.8957   (spread 0.0015 over 30 arms)
every CRASHING arm conf 0.4656447172164917 (identical to 16 digits, 14 arms)
```

It is identical to sixteen digits on the crashing side because **the crashing
frames are bit-identical to each other** (`max_abs_diff 0` over 2688×3456×3,
`results/crash/A/crash_identity.txt`) — 14 arms, six different content families,
six different token counts. There is no arm at 0.7, none at 0.55, none at 0.62.
`T_token_sweep_sheet.png` shows the whole thing at one glance: 26–29 clean,
**30–32 crash**, 33–36 clean, **44–47 crash**, with nothing varying but the number
of repetitions of the word `the`.

**A marginal-detection story predicts a gradient and predicts intermediate
confidences. Neither exists here.** What exists is a bimodal switch upstream of
the detector.

### 3. What the crashing tap looks like, in one sentence

**There is no face a person would see: the face is a solid, flat, dark-brown
shape with a soft edge, in the exact outline of the face, with nothing inside it
— no eyes, no nose, no mouth, no skin — and the blonde hair, shoulders and
background around it completely normal and photographic.**

And the mechanism is not "the detector is too strict", because I tapped one node
earlier: **`620:114 FaceDetailer` hands out pure `(0,0,0)`** over 16.94 % of the
frame (`TAP114_w17`: one unique colour in a 600×600 centre patch, against 39,957
on the placeholder control). The `(56,51,47)` at `621:163` is `620:111
ImageColorMatch+`'s global affine map applied to that black. **The face is
destroyed before the detector ever sees it.** YOLO's 0.466 is the score of the
hair-and-head silhouette with a hole where the face was, not of a marginally
detected face.

### What this does and does not say about Track D's non-reproduction

* **It does not rescue marginal detection.** On this instance the split is
  0.895 / 0.466 with an empty middle, and the cause is a black fill from
  `620:114`, not a detector decision.
* **[I] Where the instance-dependence must live, then, is in `620:114`** — whether
  that pass returns a face or returns black for a given conditioning length. On a
  box where it returns a face you get 0.895 and a clean render, which is exactly
  what Track D reports. That is a *different* claim from "confidence drifts across
  0.6", and it is testable cheaply: run Track D's instance with a `SaveImage` on
  `620:114` and measure the exact-black fraction. If it is 0.0000 there, the bands
  simply do not exist on that box.
* **One thing genuinely is close to the line and I want it on the record:** 0.466
  against a 0.6 threshold is not a wide margin. If the black fill happened but
  covered slightly less of the face, the same damaged frame could score above 0.6,
  `622:424` would fire, and the render would **complete with a ruined face**
  instead of crashing. So `622:424`'s threshold does control *crash vs bad image*
  — it just does not control *clean vs damaged*.

### The strongest single piece of evidence that this is length, not detection

`E398_tok31`. `620:106` left at the **safe 16-token placeholder**; the *eye*
prompt `622:398` padded from its shipped 28 tokens to **31** — three repetitions
of `the`, nothing else changed (`graph_diffs`-clean, one input).

```
E398_tok31       success  83.7 s  cached 0   exact-black pixels: 0.44 %  PSNR 31.21 dB vs control
E398_tok28_ctl   success  59.0 s  cached 0   exact-black pixels: 0.00000 %
```

**The eyes came back as two solid black holes** — 40,874 pixels, bbox
(1024,1569)–(1979,1672), perfectly inside the eye masks, the rest of the face
untouched. Sheet: `results/crash/A/E398_eyes_sheet.png`.

Three consequences:

1. **The bands are not a property of `620:114`.** They hit a *different* detailer,
   with a *different* prompt, at a *different* denoise, on the same encoder. This
   is an encoder/model-level effect on this pipeline.
2. **It does not always crash. Sometimes it ships.** This arm returned
   `status: success` and a complete 2688×3456 image with black eyes. The face
   pass crashes only because `622:403` happens to sit downstream of it; the eye
   pass has nothing downstream to trip, so the defect is delivered silently.
3. **The shipped eye prompt is 28 tokens — two from the band**, and it is not a
   field anyone is warned about.



---

## Repeats — both load-bearing arms reproduce

`REP_w17` and its control were voided (warm cache, above). Re-run cold on an
attested server:

| arm | tokens | expected | got |
|---|---|---|---|
| `REP2_w17` | 30 | crash, matching `L_w17` | **ERROR `622:403`**, 58.2 s, `cached 0`, tap bit-identical to `L_w17` |
| `REP2_w19` | 33 | clean, matching `L_w19` | **success**, 69.8 s, `cached 0` |

`REP2_w19` matters most: the non-monotone word ladder rested on a single clean
observation at 19 words, and rule 6 says a single observation is not a pattern.
It repeats.

---

## A side finding that is probably the "poisoned server", and it reproduced 2/2

Twice in this run a health control failed. Both times the arm was the **shipped
16-token placeholder**, on a graph byte-identical to controls that had already
passed eight times, and both times it died at `622:403` with the same
`RuntimeError`. Both times the arm's own metadata says why:

```
CTL_placeholder_after_REP_w17    error  cached 16   vram_free_after_free 39.7 GiB
CTL_placeholder_after_REP2_w17   error  cached 16   vram_free_after_free 31.4 GiB

cached node ids, IDENTICAL in both:
  116, 620:105, 620:107, 620:108, 620:109, 620:110, 620:113, 620:648,
  621:160, 621:161, 621:166, 621:167, 622:394, 622:398, 622:426, BASE
```

Both immediately followed a **crashing** arm. Both had a `vram_free` well below
the 50–75 GiB every healthy arm reports, i.e. `POST /free` had **not been applied
yet** when the prompt was submitted.

**Why that can happen at all.** `/free` frees nothing itself. `server.py`'s
handler only sets flags on the prompt queue; ComfyUI's prompt worker consumes
them later (`main.py` → `q.get_flags()` → `unload_all_models()` and `e.reset()`).
Submit before the worker gets there and the prompt runs against the **previous
arm's execution cache**. `620:114` is *not* in the cached set — the face pass
re-ran — so this is not "it reused the crashing face"; it is a safe prompt
producing the failure on a server whose cache was never cleared.

**[I] I think this is the thing `HANDOFF.md` §7.1 has been calling a poisoned
server.** It fits R4's 13:17–13:37 window, where three prompts from two different
agents across three different graphs all died at `622:403` and `POST /free`
restored bit-identical output. On this reading the "poison" is not a NaN sitting
in a weight — it is a stale execution cache after a crash, and `/free` cures it
because `free_memory` calls `e.reset()`. **2/2 is a reproduction, not a proof**,
and I have not isolated *which* of the 16 cached nodes matters.

**And a proper free cures it, 2/2.** Both times, re-running the identical arm
after waiting for the VRAM to actually come back gave `success`, `cached 0`, and
an image bit-identical to every other placeholder control
(`CTL_recovery_before_T`, 79.0 s; `CTL_placeholder_after_REP2_w17__warm2`,
74.9 s). So the server was never damaged — only its cache was stale.

**What it means operationally, and it is not subtle:** `POST /free` followed by a
2-second sleep is **not** enough. `drive.py` now polls `/system_stats` until the
VRAM has actually come back, and discards and re-runs any arm whose
`execution_cached` is non-empty. Both failures above were caught by that guard on
the second occurrence; the first is what taught me to write it.

---

## Index — where everything is

All under `results/crash/A/`.

| what | where |
|---|---|
| every arm's submitted API graph, metadata and images | `arms/<ARM>/{api_graph.json,meta.json,*.png}` |
| every arm's raw `/history/<prompt_id>` (this is where the tracebacks are) | `history/<ARM>__<prompt_id>.json` |
| the `621:163` face region of every arm, committed | `thumbs/<ARM>__tap163_facebox_half.png` |
| **A4 sheet** — crash vs clean at 1:1, red header | `A4_contact_sheet.png` |
| **A2 sheet** — the whole word ladder, 19 panels | `A2_ladder_sheet.png` |
| **A3 sheet** — the seven 17-word prompts | `A3_content_sheet.png` |
| **T sheet** — the token sweep, identical content, length only | `T_token_sweep_sheet.png` |
| offline YOLO at 0.6/0.5/0.4/0.3/0.2/0.1 for the A4 pair and the base | `yolo_A4.json` |
| offline YOLO for **every** arm | `arm_yolo.json` |
| the pooled token map | `token_map.txt`, `token_map.json` |
| every crashing arm compared pixel-for-pixel | `crash_identity.txt` |
| every arm re-tokenised from its **submitted** graph | `arm_audit.txt` |
| graph diffs proving one input differs per pair | `graph_diffs.txt` |
| the driver, builders and analysis | `tools/` |

**The `T_tok` wide sweep (36, 37, 40, 42, 43, 44, 47, 48, 49, 50, 24, 18) was
still in flight when this was written**, because the GPU is shared with another
agent's server and arms slowed from ~70 s to ~120 s. Whatever landed after this
commit is on disk but not in the tables. To fold it in, with no re-rendering:

```bash
python3 results/crash/A/tools/analyse.py              # offline YOLO on any new taps
python3 results/crash/A/tools/tokmap.py > results/crash/A/token_map.txt
python3 results/crash/A/tools/refresh_map_in_notes.py # rewrites the map in this file
python3 results/crash/A/tools/sheet_tok.py            # rebuilds the token sheet
```

Those only read what is already saved; none of them touches a server.

Arm families: `A0_` base tap · `A1_gate_` the probe validation · `L_w*` the word
ladder · `A3_C*` content controls · `A3_swap_*` same-word-and-token swaps ·
`T_tok*` the token sweep · `TAP114_*` the `620:114` taps · `CTL_*` health controls
· `REP*`/`E398_*` repeats and the prediction test.

**VOID arms, kept on disk only for the trail.** Anything whose `meta.json` says
`cached` is not 0 was not cold and is excluded from every table and every map:
`CTL_placeholder_after_REP_w17`, `CTL_placeholder_after_REP2_w17` and `T_tok28`.
`REP_w17` is void too — it was cold, but the control after it failed, and rule 2
voids everything back to the last good control; it is re-run as `REP2_w17`.

**A naming trap.** The `__warm2` suffix marks the **second attempt**, which is the
**good, cold** one — the bare name is the discarded warm run. So
`T_tok28__warm2` and `CTL_placeholder_after_REP2_w17__warm2` are the valid arms.
Bad naming on my part; every tool filters on `cached == 0` rather than on the
name, so nothing downstream is affected.

