# P3-CFG — the three Z-Image detail passes run at cfg 1, and the negatives beside them

One question: is `cfg = 1` on `#114 FaceDetailer`, `#165 FaceDetailer` "Mouth
Detailer" and `#406 DetailerForEachDebug` a constraint of the model or an
accident, and what should be done about the negative prompts sitting next to
them.

**Nothing in the graph was changed.** Every render below was submitted to
`/prompt` as an API graph; the workflow file on disk is untouched.

---

## 0 · The answer

**`cfg = 1` is required by the model.** `zimage.safetensors` is byte-for-byte
Z-Image-**Turbo**, a guidance-distilled model whose vendor documents
`guidance_scale = 0.0`. The negatives are not dead by oversight — they are dead
**by necessity**. Raising cfg is not a fix; it is driving the model out of the
operating point it was distilled to.

That answer comes from the model file, the vendor, ComfyUI's shipped templates
and ComfyUI's sampler source — **not** from a render, and it does not depend on
one. A/B arms were commissioned to show you *what* raising cfg looks like; at
the time of writing they are still queued behind other agents on the shared pod
(§5). Their absence changes nothing in §7.

**Recommendation: empty the negatives and note it on canvas** — option 2 of the
three. Emptying `#105` is provably output-inert (the string never reaches the
model at cfg 1), it makes the graph consistent with `#167` and `#394` which are
already empty, and it matches ComfyUI's own reference implementation for this
model. The on-canvas note is the half that actually protects the buyer. Full
reasoning, including why *"leave it and document it"* is weaker, in §7.

---

## 1 · The model is Z-Image-Turbo, identified by hash

`#113 UNETLoader` loads `zimage.safetensors`
(`OFMTech_NSFW.json`, subgraph `"5. Face & Mouth Detail (Z-Image)"`,
`widgets_values: ["zimage.safetensors", "default"]`).

The file carries **no `__metadata__`** — I read the safetensors header directly:
48,920-byte header, 453 tensors, `__metadata__: null`. So the name is the only
label on it, and the name says nothing about which Z-Image it is.

    $ sha256sum /workspace/ComfyUI/models/diffusion_models/zimage.safetensors
    2407613050b809ffdff18a4ac99af83ea6b95443ecebdf80e064a79c825574a6

Against the publisher's manifests, fetched live from the HuggingFace API:

| repo | file | size | sha256 |
|---|---|---|---|
| `Comfy-Org/z_image_turbo` | `split_files/diffusion_models/z_image_turbo_bf16.safetensors` | 12,309,866,400 | `2407613050b809ff…825574a6` **← match** |
| `Comfy-Org/z_image` (base) | `split_files/diffusion_models/z_image_bf16.safetensors` | 12,309,866,400 | `996a67d3ff666946…830263dee` — no match |

The two candidates are **exactly the same byte length**, so size alone would
never have distinguished them. The hash does.

> This is identifying a model file against its publisher's manifest. It is not
> the banned method — the ban is on hashing *rendered output* to prove a change
> is inert, and nothing in this report does that.

The text encoder matches too: `qwen.safetensors` is 8,044,982,048 bytes, exactly
`Comfy-Org`'s `split_files/text_encoders/qwen_3_4b.safetensors` (identical in
both repos), which is consistent with `#110 CLIPLoader`'s `type: "lumina2"` —
`comfy/sd.py:1385-1388` routes a detected `QWEN3_4B` encoder to
`comfy.text_encoders.z_image.ZImageTokenizer` unless the CLIP type is Flux.

**The workflow's own note may already have known.** Root `#649 MarkdownNote`
calls the second LoRA slot *"Your **ZIT** LoRa"* and says it "drives the face,
mouth and eyes at full resolution". *Inference, labelled as such:* ZIT reads as
Z-Image Turbo, which would mean the author knew which variant this was and the
knowledge simply never reached the negative prompt nodes. The expansion is not
written anywhere in the file, so I cannot state it as fact.

## 2 · Turbo means cfg 1, from three independent sources

**(a) ComfyUI's own shipped templates, on disk on this pod.** Templates package
0.9.4 ships both variants and sets them differently:

    comfyui_workflow_templates_media_other/templates/image_z_image_turbo.json
      KSampler #3  widgets_values = [0, "randomize", 8, 1, "res_multistep", "simple", 1]
                                                     ^steps 8  ^cfg 1

    comfyui_workflow_templates_media_image/templates/image_z_image.json   (BASE)
      KSampler #69 widgets_values = [..., "randomize", 25, 4, "res_multistep", "simple", 1]
                                                       ^steps 25 ^cfg 4
      MarkdownNote #86 and #76:  "- Steps: 30～50\n- cfg:  3～5"
      CLIPTextEncode #71 (negative) = ""     <- empty in the BASE template too

Note the base template also encodes cfg **3–5**. That is where the value 3 in my
render arms comes from — it is what a buyer lands on if they read Z-Image
documentation without noticing which variant they hold.

**And the turbo template does not give the user a negative prompt at all.** In
`image_z_image_turbo.json` the KSampler's `negative` input is not a text box —
it is `#33 ConditioningZeroOut` applied to the *positive* encode `#27`:

    #33 ConditioningZeroOut   conditioning <- #27 (CLIPTextEncode)
    #3  KSampler              positive <- #27,  negative <- #33

There is exactly one text box in that template. The base template, by contrast,
has a real negative `CLIPTextEncode` (`#71`, shipped empty). ComfyUI's own
reference implementation for this exact model therefore **removes the negative
as a user-facing control**. That is the strongest single argument about what our
`#105` should look like.

**The model has no guidance input either.** I read the tensor shapes out of the
file: `cap_embedder.1.weight` is `[3840, 2560]`, so `dim = 3840`, which is what
selects `class ZImage(Lumina2)` in `comfy/supported_models.py:1093` (and with it
`sampling_settings shift: 3.0`, matching the templates' explicit
`ModelSamplingAuraFlow [3]` — so this graph is not missing that node). There are
**zero tensors with `guidance` in the key**. Unlike Flux-dev there is no
distilled guidance-scale embedding to turn up instead. CFG is the only guidance
mechanism the architecture has, and this checkpoint is trained not to need it.

**(b) The vendor.** `huggingface.co/Tongyi-MAI/Z-Image-Turbo` quick-start code
carries the comment `guidance_scale=0.0, # Guidance should be 0 for the Turbo
models`, uses `num_inference_steps=9` ("8 DiT forwards"), and describes the
model as a distilled version of Z-Image trained with Decoupled-DMD. Guidance
distillation is precisely the technique that removes the need for a negative
branch. (`guidance_scale=0` in diffusers is the same operating point as `cfg=1`
in ComfyUI.)

**(c) ComfyUI's sampler, on this pod.** `comfy/samplers.py:370`:

```python
def sampling_function(model, x, timestep, uncond, cond, cond_scale, model_options={}, seed=None):
    if math.isclose(cond_scale, 1.0) and model_options.get("disable_cfg1_optimization", False) == False:
        uncond_ = None
```

At cfg 1 the uncond is not merely arithmetically cancelled — **it is never
evaluated**. The negative's tokens are encoded by CLIP and then thrown away
before the transformer is called.

**The one escape hatch is closed.** `disable_cfg1_optimization` is only ever set
by: the `*_cfg_pp` sampler variants and `res_multistep`/`gradient_estimation`
(`comfy/k_diffusion/sampling.py:1261, 1306, 1351, 1390, 1465`), `sample_euler_pp`
(`comfy_extras/nodes_advanced_samplers.py:75`), and SelfAttentionGuidance
(`comfy_extras/nodes_sag.py:177`). This graph's three passes use
`euler_ancestral`, `euler_ancestral` and `euler` — none of them — and their model
comes straight from `#113 UNETLoader` through `116 Lora Loader Stack (rgthree)`,
which applies LoRA weights and does not touch `model_options`. `#619:609
PerturbedAttentionGuidance` is on the **SDXL** branch and cannot reach them.

## 3 · The file already half-knew

Only **one** of the three negatives is written:

| node | title | text |
|---|---|---|
| `#105` (sg 5) | Face Detailer Negative Prompt | `"deformed, ugly, blurry, bad anatomy, disfigured, extra eyes, cropped face, out of frame, deformed piercing, bad piercing, watermark, text"` |
| `#167` (sg 4) | Mouth Detailer Negative Prompt | `""` |
| `#394` (sg 6) | Eye Negative Prompt | `""` |

Two of three are already empty. That is corroboration from the file itself, not
inference from me: somebody worked this out for the mouth and the eyes and did
not carry it back to the face.

**And this is exactly the node the buyer is sent to.** Root `#649` tells them:

> "Open **5. Face & Mouth Detail**, find *Face Detailer Prompt*, and replace
> `TRIGGER, PROMPT FOR YOUR MODEL` with your LoRA's trigger word …"

`#106` (the positive they are told to edit) and `#105` (the dead negative) sit
side by side in the same subgraph. No note anywhere in the file mentions cfg or
the negative — I searched every `MarkdownNote` and `Note` in the workflow.

## 4 · What each pass actually sees — this decides whether the negative would even help

Read from the server's own log, `/workspace/ComfyUI/user/comfyui_18188.log`,
for my baseline run:

    Detailer: force inpaint
    Detailer: segment upscale for ((1297.1787, 1833.2556)) | crop region (2688, 3456) x 1.0 -> (2688, 3456)   <- #114 face
    Detailer: segment upscale for ((536.4098, 278.19226)) | crop region (1609, 834) x 1.1236852 -> (1808, 937) <- #165 mouth
    Detailer: segment upscale for ((843, 157))            | crop region (1353, 471) x 1.4190894 -> (1920, 668) <- #406 eyes

So:

- **`#165` samples a 1808×937 mouth region and `#406` a 1920×668 eye region.**
  In those two, `"out of frame"` and `"cropped face"` have **no referent** —
  there is no frame edge in a mouth crop, and the region genuinely *is* a
  cropped face, so as a negative that token pushes away from the thing being
  made. See the correction below about `"watermark"` and `"text"`, which do
  turn out to have a referent.
- **`#114` is different, and not in the way I expected.** The face bbox is
  1297×1833, `bbox_crop_factor 3` blows that past the image bounds, so the crop
  region clamps to the **whole 2688×3456 frame**; `force_inpaint: true` then
  forces `upscale = 1.0` (`modules/impact/core.py:315-320`), so it diffuses the
  entire frame at native resolution for 30 steps. `#649` calling it "the single
  most expensive pass in the workflow" is correct, and understated.

  But `noise_mask: true` with `sam_model_opt` wired means only the SAM face mask
  is re-denoised — `modules/impact/impact_sampling.py:133` passes
  `denoise_mask=noise_mask` and lines 291-296 composite the unmasked region back
  in latent space. So the model *sees* the whole frame as context but can only
  *change* the face. A negative saying `"watermark, text"` could not remove a
  watermark from a corner even at cfg 5, because those pixels are masked out of
  the update.

  **Measured, from the tapped input `620:137` against output slot 0 (`image`) —
  the slot actually wired downstream to `620:111`.** Saved as
  `results/cfg/compare/114_change_extent.json` and
  `114_changed_gt8_levels_1to1.png`:

  | change threshold | share of the 2688×3456 frame |
  |---|---|
  | > 0 levels | 16.27 % |
  | > 2 levels | 14.51 % |
  | > 8 levels | **9.08 %** |
  | > 16 levels | 4.14 % |

  The `> 8 levels` map is a clean silhouette of the face and nothing else — that
  is the SAM mask, and it is the only region the pass edits. Outside the mask the
  output is **bit-identical** to the input (flat-patch 1–4 px DoG RMS: background
  2.685 → 2.685, wall 1.572 → 1.572).

  > **Correction I made to myself, recorded because it nearly went into other
  > people's numbers.** I first measured this on output **slot 1,
  > `cropped_refined`**, and got 99.05 % of pixels changed, which I reported to
  > main as whole-frame VAE round-trip damage. That was wrong. Slot 1 is the raw
  > VAE-decoded crop, so it carries round-trip drift over everything it contains
  > — and for this image it contains the whole frame. Slot 0 composites the
  > refined region back in *pixel* space. The `> 8 levels` figure barely moves
  > (9.51 % → 9.08 %) so the artefact conclusion is unaffected, but "percentage of
  > pixels changed" is 6× different depending on which output slot you sample.
  > Anyone measuring a detailer this way should sample the slot that is wired
  > onward.

### The correction I owe this section

I expected to conclude that all four whole-image tokens were meaningless here.
Looking at the actual render, **two of them are not.** `#114` at the shipped
settings produces, inside the SAM mask and along its boundary, a blistered
"bubble-wrap" pore texture, a hard visible seam where the mask ends, and faint
reddish **script-like marks**. All four 1:1 crops are in
`results/cfg/compare/`:

| file | what it shows |
|---|---|
| `baseline_114_input_mouthregion_1to1.png` | the image entering `#114` — clean, smooth skin |
| `baseline_114_output_mouthregion_1to1.png` | the same region leaving `#114` — blistered |
| `baseline_114_output_maskseam_1to1.png` | the right cheek: hard mask seam, and the text-like marks |
| `baseline_final_maskseam_1to1.png` | the same region in root `#505`'s delivered image — **still there** |

So `"text"` and arguably `"watermark"` do have a referent: this pass really does
hallucinate text-like marks. That makes `#105` *more* convincing to a buyer, not
less — they will see something that looks exactly like what the negative claims
to prevent, and editing the negative will do nothing.

**Answer to the owner's plain-terms question: still no, but for a sharper
reason.** Of the twelve tokens, `out of frame` and `cropped face` cannot act on
a masked face region and `cropped face` actively describes what is being made;
`deformed piercing, bad piercing` presumes a piercing. `text` and `watermark`
have a referent but only because the pass is generating the artefact itself —
and you do not fix a generator that is producing junk by adding a term telling
it not to. That leaves `deformed, ugly, blurry, bad anatomy, disfigured, extra
eyes` — generic quality words on an inpaint whose composition is already fixed
by the image underneath. Even if cfg 1 were not a constraint, this string is
close to inert semantically, and the artefacts the buyer would be reaching for
it to fix have a different cause (see §5.4).

## 5 · The A/B renders

### Method

- One full pipeline run at the shipped settings (`00-baseline-full/`, status
  `success`, 337.7 s, 57 nodes `execution_cached`) with extra `SaveImage` nodes
  **added to the submitted prompt only** tapping the image that enters each of
  the three passes. `inputs.pick_list = "0"` was set on `#603
  INSTARAW_ImageFilter` in the submitted prompt only, never in the file.
- Each arm then re-runs **only the node under test**, fed that same tapped image
  through `LoadImage`, with every other input — seed, steps, sampler, scheduler,
  denoise, detector, SAM model, LoRA stack, positive prompt — copied unchanged
  from the API graph. So arms differ from each other in **cfg and negative text
  only**.
- Seeds are fixed in the file and identical across arms: `#114` and `#165`
  `seed = 1111111`, `#406` `seed = 1111112`.
- Positive prompts, unchanged across arms: `#106` `"TRIGGER, PROMPT FOR YOUR
  MODEL"` (the shipped placeholder), `#166` `"realistic detailed mouth"`, `#398`
  `"perfect eyes, round pupils, round iris, symmetrical eyes, realistic eyes,
  perfect circles, round"`.
- The base graph is `results/phase0/api_graph.json`. I verified it against the
  current `OFMTech_NSFW.json`: of 323 literal (non-link) inputs across 88 nodes,
  **319 match exactly**; the four that differ are the two `Lora Loader Stack`
  `lora_01` slots (`luna.safetensors`, `lunaskye.safetensors`, shipped as
  `"None"`) and the typed prompt batch — i.e. the shipped file plus exactly what
  a buyer fills in. Every cfg, seed, sampler and prompt matches.
- I do **not** report timings as evidence. Arms were queued behind other agents'
  work and `execution_cached` counts differ between them.

### Harness fidelity

The isolated `face cfg 1.0, negative as shipped` arm reproduced the full
pipeline's own `#114` output exactly (max abs difference 0 over 2688×3456).
Noted as a sanity check on the harness only — per the project's standing rule I
am not treating identical output as proof of anything.

### Arms

| stage | arm | cfg | negative | status |
|---|---|---|---|---|
| face `#114` | `face_cfg1.0_negshipped` | 1.0 | as shipped | **complete** — 185.5 s |
| face `#114` | `face_cfg1.5_negshipped` | 1.5 | as shipped | queued |
| face `#114` | `face_cfg1.5_negempty` | 1.5 | `""` | queued |
| face `#114` | `face_cfg3.0_negshipped` | 3.0 | as shipped | queued |
| face `#114` | `faceX_cfg1.0_realpositive_negshipped` | 1.0 | as shipped, **positive replaced with a real prompt** | queued |
| mouth `#165` | `mouth_cfg1.0_negempty` | 1.0 | `""` (shipped) | queued |
| mouth `#165` | `mouth_cfg1.5_negempty` | 1.5 | `""` | queued |
| mouth `#165` | `mouth_cfg1.5_negfilled` | 1.5 | `#105`'s string | queued |
| mouth `#165` | `mouth_cfg3.0_negfilled` | 3.0 | `#105`'s string | queued |
| eyes `#406` | `eyes_cfg1.0_negempty` | 1.0 | `""` (shipped) | queued |
| eyes `#406` | `eyes_cfg1.5_negempty` | 1.5 | `""` | queued |
| eyes `#406` | `eyes_cfg1.5_negfilled` | 1.5 | `#105`'s string | queued |
| eyes `#406` | `eyes_cfg3.0_negfilled` | 3.0 | `#105`'s string | queued |

> **Status, stated plainly rather than papered over.** At the time of writing
> only the cfg 1.0 reference arm has returned. The remaining twelve are queued
> behind other agents' work on a shared pod and had not executed. Their exact
> submitted `api_graph.json` and `submission.json` (with prompt id) are on disk
> under `results/cfg/<arm>/`, so whoever picks this up can collect them from
> `/history` without re-deriving anything.
>
> **This does not weaken §7.** The recommendation does not rest on these arms. It
> rests on the model identification (§1), the vendor and template evidence (§2a,
> §2b) and the sampler source (§2c) — none of which needs a render. The arms were
> commissioned to show the owner *what raising cfg costs*, which is a picture
> for him to look at, not the basis of the argument. If they never run, the
> argument stands and the picture is missing.

**Every queued graph was verified after submission**, read back out of its own
`api_graph.json`, so a later session can collect them without re-checking:

| arm | node | cfg | guide/max | crop_factor | seed | nodes | positive |
|---|---|---|---|---|---|---|---|
| `face_cfg1.5_negshipped` | `620:114` | 1.5 | 1024/1024 | 3 | 1111111 | 12 | placeholder |
| `face_cfg3.0_negshipped` | `620:114` | 3.0 | 1024/1024 | 3 | 1111111 | 12 | placeholder |
| `faceX_cfg1.0_realpositive…` | `620:114` | 1.0 | 1024/1024 | 3 | 1111111 | 11 | **real prompt** |
| `mouth_cfg1.5_negfilled` | `620:165` | 1.5 | 1808/1808 | 3 | 1111111 | 13 | `realistic detailed mouth` |
| `eyes_cfg3.0_negfilled` | `622:406` | 3.0 | 1920/1920 | n/a | 1111112 | 22 | `perfect eyes, …` |
| `sw_gs2048` | `620:114` | 1 | **2048/2048** | 3 | 1111111 | 12 | placeholder |
| `sw_gs4096` | `620:114` | 1 | **4096/4096** | 3 | 1111111 | 12 | placeholder |
| `sw_cf1.5` | `620:114` | 1 | 1024/1024 | **1.5** | 1111111 | 12 | placeholder |
| `sw_cf1.0` | `620:114` | 1 | 1024/1024 | **1.0** | 1111111 | 12 | placeholder |

Seeds identical within each stage, so nothing but the named variable moves.

### The `cfg 1.0 + empty negative` arm was cancelled deliberately

It was queued and I cancelled it (only ever my own prompt id) to make room when
priorities shifted. Its purpose was to corroborate that the negative is inert at
cfg 1 by showing an identical image — which is the shape of the verification
method this project bans, and which §2c already proves from source. Losing it
costs nothing.

## 5b · `guide_size` / `bbox_crop_factor` on `#114` — asked for mid-run

Main asked for a `guide_size`/`max_size` sweep at 1024 / 1408 / 1808 / 2048 on
the premise that `#114` downsamples its crop to `max_size` and scales back up
~3.4×. **That premise is wrong**, and I said so before running anything so the
prediction can be checked against me rather than taken on trust.

### The mechanism, from source and from the log

`modules/impact/core.py:291-320`:

```python
if guide_size_for_bbox:
    upscale = guide_size / min(bbox_w, bbox_h)
new_w, new_h = int(w * upscale), int(h * upscale)
if new_w > max_size or new_h > max_size:
    upscale *= max_size / max(new_w, new_h)
    new_w, new_h = int(w * upscale), int(h * upscale)
if not force_inpaint:
    if upscale <= 1.0:   -> "segment skip", the pass does nothing
else:
    if upscale <= 1.0:   -> upscale = 1.0; new_w = w; new_h = h
```

`#114` has `force_inpaint: true`, so any computed **downscale is clamped back up
to 1.0** and the crop is sampled at native size. After the `max_size` cap the
bbox term cancels and the scale reduces to `max_size / max(crop_w, crop_h)`.

Both halves are visible in the same log file. `#114` (clamped):

    Detailer: force inpaint
    Detailer: segment upscale for ((1297.18, 1833.26)) | crop region (2688, 3456) x 1.0 -> (2688, 3456)

`#165`, where it is an upscale and therefore not clamped:

    Detailer: segment upscale for ((536.4, 278.2)) | crop region (1609, 834) x 1.1236852407455444 -> (1808, 937)

and `1808 / 1609 = 1.12368524…` exactly. `#406` gives a third confirmation:
logged `x 1.4190894945648536` on `crop region (1353, 471)` with `max_size 1920`,
and `1920 / 1353 = 1.41908949…`. Formula confirmed three times on live output.

So on `#114`, with a crop region 3456 px tall, `max_size` has **no effect at all
below 3456**. 1408, 1808 and 2048 would each burn a render to reproduce the
shipped image. The lever only engages above 3456, and the only way to make this
pass sample *smaller* is `bbox_crop_factor`.

### Predictions, registered before the renders returned

| arm | change | predicted `Detailer:` log | predicted sampling size |
|---|---|---|---|
| `face_cfg1.0_negshipped` | shipped (1024/1024, cf 3) | `force inpaint`, `x 1.0` | 2688×3456 |
| `sw_gs2048` | guide=max=2048 | `force inpaint`, `x 1.0` | 2688×3456 — **identical output to shipped** |
| `sw_gs4096` | guide=max=4096 | `x 1.185…` | ≈3186×4096 |
| `sw_cf1.5` | `bbox_crop_factor` 1.5 | `force inpaint`, `x 1.0` | ≈1945×2750 |
| `sw_cf1.0` | `bbox_crop_factor` 1.0 | `force inpaint`, `x 1.0` | ≈1297×1833 |

### Why the direction is probably backwards

Z-Image is a ~1024-class model. At the shipped settings `#114` diffuses
**2688×3456 = 9.3 megapixels in a single pass**, roughly 36× the training area,
at denoise 0.8 for 30 steps. Repeated micro-structure — bumps, grids, hexagons,
ladders — is the classic signature of sampling far above native resolution.
Raising `guide_size` pushes further out; `bbox_crop_factor` is what pulls back.

This also re-explains the WS4 vs P2-RENDER difference without any downsample
ratio: both ran at native crop resolution (WS4's smaller face gives a crop
region of roughly 1962×2673, P2-RENDER's clamps to 2688×3456), so the variable
is the absolute pixel count being diffused in one pass, 5.2 MP versus 9.3 MP.
Since the crop clamps to the frame as soon as `bbox × 3` exceeds it, tighter
framing is strictly worse and saturates at the whole frame. *That last paragraph
is inference from geometry; the sweep tests it.*

### Results

> **Not yet returned.** All four sweep arms are queued on a shared pod behind
> other agents' work. Their submitted `api_graph.json` and prompt ids are under
> `results/cfg/sw_*/`. The analysis is scripted and takes one command once they
> land: it reads each arm's `Detailer:` log lines out of
> `/workspace/ComfyUI/user/comfyui_18188.log` within that prompt's execution
> window, computes 1–4 px DoG RMS on the edit footprint and on four fixed
> patches, and writes 1:1 mouth crops plus a contact sheet to
> `results/cfg/compare/`.
>
> The predictions above are registered and unedited. Score them against the log
> lines, not against my prose.

**Reference numbers already measured**, so the sweep has something to be
compared against. 1–4 px DoG RMS, luma, on the shipped arm at guide/max 1024:

| region | input `620:137` | output `#114` |
|---|---|---|
| edit footprint (the SAM mask, 9.08 % of frame) | 3.912 | **5.841** |
| everything else | 4.143 | 4.202 |
| mouth + cheek patch (1100,1500,900,600) | 2.714 | **4.530** |
| forehead patch (1250,600,700,400) | 2.754 | 3.589 |
| blurred background patch (100,200,500,500) | 2.685 | 2.685 |
| wall / sill patch (100,2800,500,500) | 1.572 | 1.572 |

The two background patches are **bit-identical** before and after, and the edit
footprint gains ~49 % band energy. `5.841` sits against P2-RENDER's independently
measured `5.87` inside the face — two rigs, no shared machinery, same number.
The pass injects 1–4 px structure only where it edits, worst at the mouth.

## 6 · Adjacent finding, not investigated

Listing every cfg-bearing node in the API graph turned up **two more cfg-1
samplers, on the SDXL half**:

| node | class | cfg | steps | sampler | negative source | negative text |
|---|---|---|---|---|---|---|
| `619:600` | `KSamplerAdvanced` | 1 | 70 | `lcm` | `619:606` | **the buyer's own negative prompt**, linked from `619:605` ← `#483` |
| `587:98` | `UltimateSDUpscale` | 1 | 2 | `lcm` | `587:509` | `""` |

Both run on `sdxl_tdd_lora_weights.safetensors` (`619:610`, `587:97`). `587:509`
is already empty, the same pattern as `#167`/`#394`. `619:600` is not: the
buyer's typed negative is wired into a cfg-1 sampler.

It is not as bad as it first looks — the *same* `619:606` encode also feeds
`619:592 KSampler` at cfg 4 and `619:617 UltimateSDUpscale` at cfg 4.5, where it
does apply. So the buyer's negative is doing real work in this pipeline, just
not at `619:600`. **I did not test this.** Different model family, different
distillation, outside my brief. Someone should decide whether `619:600` deserves
the same treatment.

Two things already on record that this run confirms rather than discovers:

- `QUESTIONS.md` §1.1 established that the `clip` input on all three Z-Image
  detailers is consumed by nothing, because Impact only uses it when `wildcard
  != ""` and all three wildcards are empty (`modules/impact/core.py:268` is the
  only use). I re-checked that line and it holds. It also means emptying `#105`
  cannot disturb anything through that path.
- `notes/WS4-questions.md` Q-E reached the same conclusion about `#105` being
  inert and guessed *"cfg 1 is deliberate … so the negative prompts are the
  accident, not the cfg"*. That guess is now established: §1 and §2 above turn it
  from a guess into a fact with a hash, a vendor statement and a source line
  behind it. WS4's suggested option "raise cfg and A/B it" is the one that
  should now be struck.

## 7 · Recommendation

**Empty the negatives and note it on canvas.** That is option 2 of the three you
offered. Not "raise cfg", and not "leave it and document it".

### Why not raise cfg

This one is not a judgement call. `zimage.safetensors` is byte-identical to
Z-Image-**Turbo** (§1), the vendor's own quick-start says
`guidance_scale=0.0, # Guidance should be 0 for the Turbo models`, ComfyUI's
shipped turbo template runs cfg 1 against cfg 4 for the base model, and the
checkpoint contains **no guidance tensors at all** — there is no distilled
guidance input to fall back on. Raising cfg does not switch a feature on. It
drives a model outside the operating point it was distilled to. Anything in
`PROPOSALS.md` or `notes/WS4-questions.md` that offers "raise cfg and A/B it" as
an option should be struck.

### Why not just leave it and document it

Because a note beside a fully-written negative is the weakest of the three. The
buyer is sent to that exact subgraph by root `#649` — *"Open 5. Face & Mouth
Detail, find Face Detailer Prompt…"* — and `#105` sits next to `#106` reading
`"deformed, ugly, blurry, bad anatomy, disfigured, extra eyes, cropped face, out
of frame, deformed piercing, bad piercing, watermark, text"`. That is not a
neutral empty field they might wonder about. It is a specific, confident,
professional-looking list, and it does nothing.

And they **will** reach for it, because the pipeline produces exactly the
defects it names. `#114` at shipped settings puts a blistered pore texture, a
hard mask seam and faint text-like marks on the face, and they survive into the
delivered image (§4). A buyer seeing that, finding `watermark, text` already in
the negative, will conclude the negative needs strengthening. It will not help.
That is the trap, and a note pinned nearby does not spring it — notes are read
once, the field is read every time.

### Why emptying is safe

Emptying `#105` is the only change anywhere in this area that is **provably
output-inert**, and provable without a GPU. `comfy/samplers.py:370` sets
`uncond_ = None` at cfg 1 before the model is called, and nothing in this
graph's model chain sets `disable_cfg1_optimization` (§2c). The string never
reaches the transformer, so its contents cannot affect a pixel. Verification is
a graph diff showing exactly one changed string plus that source line. No
render, no risk, and per the project's standing rule I am **not** proposing to
confirm it by comparing rendered output.

It also makes the graph self-consistent — `#167` and `#394` are already empty,
so somebody reached this conclusion twice and stopped — and it matches ComfyUI's
own reference implementation for this exact model, which does not expose a
negative box at all (§2a).

Nothing is lost by emptying it. The string is now recorded verbatim in this
report, in `notes/WS4-questions.md` Q-E and in git history.

### But the note is the load-bearing half

An empty box with no explanation invites a buyer to fill it in, which is the
same trap one step later. The note is why this is option 2 and not "delete the
text". Suggested wording, to be rewritten in your voice:

> **The face, mouth and eye passes run on Z-Image Turbo, which has no negative
> prompt.**
> Turbo is a *distilled* model. It is built to run at **cfg 1**, where
> classifier-free guidance is off and the negative prompt is never evaluated —
> anything typed into a negative box on these three passes is discarded before
> the model sees it. The boxes are left empty deliberately.
>
> **Do not raise cfg to make them work.** Turbo degrades above cfg 1; that is
> what distillation traded away for speed.
>
> **Put everything — what you want *and* what you want avoided — in the positive
> prompt.** At cfg 1 the positive prompt is the only steering the model gets.

### One thing that follows and matters more than the negative

Because the positive is the *only* conditioning at cfg 1, `#106` shipping as the
placeholder `"TRIGGER, PROMPT FOR YOUR MODEL"` is far more damaging here than
the same placeholder would be on a normal cfg model, where a negative branch
would dilute it. `#649` already tells the buyer to replace it; on the evidence
of §1–§2 that instruction is not a nicety, it is the single most load-bearing
sentence in the buyer-facing documentation, and it deserves to be stated as a
requirement rather than a step 3.

### What not to do

Do **not** rewire `#105` through a `ConditioningZeroOut`, the way ComfyUI's
turbo template does. It is the more "correct" construction and it is equally
inert, but it means adding a node and editing subgraph IO — and `STATE.md`
records that exactly that class of edit inside a subgraph produced this run's
browser blocker. An empty string reaches the same buyer-visible outcome with no
structural change at all.

### Scope

This recommendation covers `#105`, `#167` and `#394` only. `619:600` on the SDXL
half (§6) has the same shape but a different model and a different distillation,
and carries the **buyer's own** typed negative rather than a hard-coded one. I
did not test it and it needs its own decision.

## 8 · Files

Everything is under `results/cfg/`, one directory per arm, each containing the
exact submitted `api_graph.json` and its `submission.json` (prompt id).
Comparison crops are in `results/cfg/compare/` at **1:1, no downscaling**, with
`metrics.json` beside them.
