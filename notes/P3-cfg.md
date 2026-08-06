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
**by necessity**. Raising cfg is not a fix; it is a regression, and the renders
below show what it costs.

<!--HEADLINE-->


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

<!--RESULTS-->

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

<!--RECOMMENDATION-->

## 8 · Files

Everything is under `results/cfg/`, one directory per arm, each containing the
exact submitted `api_graph.json` and its `submission.json` (prompt id).
Comparison crops are in `results/cfg/compare/` at **1:1, no downscaling**, with
`metrics.json` beside them.
