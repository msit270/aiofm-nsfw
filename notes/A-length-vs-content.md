# TRACK A — is the face-prompt crash LENGTH or WORDS?

**ANSWER: _(not yet established — run in progress)_**

Server: `127.0.0.1:18188` only. Nothing in this file touched 28191.
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
length threshold of any kind.** 19 words / 33 tokens is *longer* than 17 words /
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

## A3 — content control

_(running)_
