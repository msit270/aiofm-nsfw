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

## A2 — the length ladder

_(filled in as they run)_
