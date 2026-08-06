# WS4 — questions

Per the brief I did not stop to ask. Each carries my best guess, my reasoning,
the lower-risk option I took, and — where a patch exists — the exact patch, so
answering is a yes/no rather than a re-derivation.

---

## Q-A — should the Z-Image text encodes run through the buyer's ZIT LoRA stack?

**The fact.** All three Z-Image text encodes take the **raw** `#110 CLIPLoader`
output, while all three Z-Image samplers take the **LoRA'd** model from `#116`
"Your ZIT LoRa":

| encode | stage | clip source |
|---|---|---|
| `#105`/`#106` (face) | sg5 | `#110` direct, sg5 links 191/192 |
| `#166`/`#167` (mouth) | sg4 | `#110` via `#620[2]` → root link 1423 |
| `#394`/`#398` (eyes) | sg6 | `#110` via `#620[2]` → root link 1429 |

`#114.clip` and `#165.clip` *do* receive the LoRA'd CLIP (sg5 links 209/319 from
`-10[3]`), but Impact Pack only uses that CLIP when the node's `wildcard` string
is non-empty (`ComfyUI-Impact-Pack/modules/impact/core.py:267`), and both
wildcards are `""`. So the LoRA'd CLIP is currently consumed by nothing.

**Net effect:** a buyer's Z-Image LoRA reaches the UNet of all three Z-Image
passes and the text encoder of none.

**My guess:** this is unintended, and the encodes should go through `#116`.
`#649`'s buyer note says the ZIT slot is "the slot your character's *likeness*
lives in", which argues for the LoRA affecting the prompt encoding too.

**Why I did not ship it.** The argument is stronger than "no-op at defaults", and
it comes from the actual LoRA files on this pod. Main read their safetensors
headers directly (8-byte length prefix + JSON header, no tensor load) and counted
keys matching `lora_te`, `text_encoder`, `text_model`, `te.`, `conditioner` or
`clip`:

| file | keys | text-encoder keys | arch metadata |
|---|---|---|---|
| `luna.safetensors` | 480 | **0** | `zimage` |
| `x_gen_weights.safetensors` | 480 | **0** | `zimage` |
| `primary_net_v2.safetensors` | 720 | **0** | `zimage` |
| `lunaskye.safetensors` | 2364 | **0** | `sdxl_1.0` |
| `dmd2_sdxl_4step_lora_fp16.safetensors` | 2364 | **0** | — |
| `sdxl_tdd_lora_weights.safetensors` | 2364 | **0** | — |

Every Z-Image LoRA's keys are `diffusion_model.layers.N.*` only; every SDXL
LoRA's are `lora_unet_*` only. So:

- **For these files the rewire is a no-op even with a LoRA loaded**, not merely
  at the all-`"None"` default. There is no text-encoder tensor for it to carry.
- **Caveat that must travel with that:** this is a property of these six files,
  not of Z-Image LoRAs in general. A buyer could bring a LoRA with a
  text-encoder component, and then the wiring would matter. The risk is real but
  **latent and not demonstrable with anything on this pod.**
- Independently, `rgthree-comfy/py/lora_stack.py:36-44` returns `(model, clip)`
  untouched when every slot is `"None"`, which is the shipped state of `#116`
  (`["None", 1, "None", 0.9, "None", 0.9, "None", 1]`).

Against that: the rewire requires editing `linkIds` on subgraph IO slots.
`litegraph/src/subgraph/SubgraphOutput.ts` maintains those arrays as explicit
state (`this.linkIds[0] = link.id`, and `disconnect()` carries the comment
*"should never have more than one connection"*). A desynced IO `linkIds` array is
the same class of corruption as this run's shipped blocker.

**Zero demonstrable benefit against a non-zero risk of breaking graph load is
the wrong trade for a first-time buyer.**

**Counter-intuitive corollary, worth recording so nobody "discovers" it later and
files it as a defect:** `#618` "Your SDXL LoRa" fans its **CLIP** output to
`#587` and `#619`, but with any of the three SDXL LoRA files above that CLIP is
bit-identical to `#613`'s, because none of them has text-encoder tensors either.
The SDXL CLIP path is inert *for these files* by the same mechanism, and that is
not a bug.

**The patch, if you want it** (three independent pieces, smallest first):

1. *sg5 face only.* In subgraph `d6db378b-…`, repoint links 191 and 192 from
   `origin_id: 110, origin_slot: 0` to `origin_id: -10, origin_slot: 3`; remove
   191 and 192 from `#110.outputs[0].links`; append them to the `linkIds` of the
   sg5 input definition named `clip`.
2. *mouth.* In root, repoint link 1423 from `620[2]` to `116[1]`; move the id
   between the two `outputs[].links` arrays accordingly.
3. *eyes.* Same for root link 1429.

Pieces 2 and 3 touch only root node `outputs[].links`, not subgraph IO
`linkIds`, so they are the lower-risk two despite looking bigger.

**Action taken:** changed nothing. Logged.

---

## Q-B — should `#106`'s placeholder text stay?

**Yes, and I left it.** Root `#649` `MarkdownNote` instructs the buyer to replace
`TRIGGER, PROMPT FOR YOUR MODEL` by hand, quoting the exact string. The
placeholder and the instruction are a matched pair; changing one without the
other is worse than leaving both.

**But note what it costs while unreplaced.** `#114` runs at denoise **0.80** —
the highest in the graph — and `cfg = 1`, which means classifier-free guidance is
off and the **negative prompt `#105` is not applied at all**. So the face is
substantially regenerated under the literal tokens "TRIGGER, PROMPT FOR YOUR
MODEL" and nothing else. The A/B in `WS4-report.md` shows what that does.

If you want a change here that is not "inventing content", the honest options
are: (a) empty string, (b) route `#483`'s positive prompt into `#106` so the
face pass inherits the buyer's own prompt. (b) is the more interesting idea and
needs your call; it is not a change I should make unilaterally.

**Action taken:** left the text exactly as-is.

---

## Q-C — `AUDIT.md`, `QUESTIONS.md` and `STATE.md` contain claims that are now false

Not questions so much as corrections that need an owner. I did not edit those
files — they are not mine.

1. `AUDIT.md` A4 and `QUESTIONS.md` Q2 quote the placeholder as
   `"TRIGGER, PROMT FOR YOUR MODEL"` and call `PROMT` a typo. The file says
   **`PROMPT`**; `grep -c PROMT` returns 0. There is no typo.
2. `AUDIT.md` A21 records `#600 KSamplerAdvanced` `control_after_generate` as
   `"randomize"`. The file says **`"fixed"`**. STATE.md's unfixed-list entry
   "`#600` reseeds itself every run" is false for the current file.
3. `AUDIT.md` A5, `QUESTIONS.md` Q3 and STATE.md's unfixed list all describe a
   ControlNet/IPAdapter/depth path that **no longer exists**.
4. `AUDIT.md` A23's `#107[1] → #114.segm_detector_opt` link **no longer exists**.
5. `AUDIT.md` A1 and STATE.md give the round-trip resolution as ~1434x1843. It
   is **1432x1840** — `#594 VAEEncode` crops to a multiple of 8 first
   (`comfy/sd.py:847-857`).
6. `CLAUDE.md`'s graph description (132 nodes, 24 bypassed, stages all named
   "Dont touch!!!") does not describe this file. It is **109 nodes, one bypassed
   node**, and all seven stages are named.

**Action taken:** recorded in `WS4-report.md`. Someone who owns those documents
should fold them in.

---

## Q-D — `#87 ImageBlend` blend_factor 1.0

Confirmed a genuine no-op: `blend_mode "normal"` returns `image2`, and at
`blend_factor 1.0` `image1` drops out entirely
(`comfy_extras/nodes_post_processing.py:44-52`). The skin-detail filter
`x1_ITF_SkinDiffDetail_Lite_v1` therefore runs at 100% strength.

**My guess:** unintended — you do not wire both the original and the filtered
image into a blend node and then set the factor so the original is discarded.

**A/B run so you can look rather than read an argument.** Arm `D_skinblend_050`
is arm `B` with the single input `587:87.blend_factor` changed from 1.0 to 0.5;
the submitted graph is at `results/ws4/D_skinblend_050/api_graph.json`.

| | full frame | face crop |
|---|---|---|
| PSNR | 33.88 dB | 29.05 dB |
| SSIM | 0.924 | 0.780 |
| mean abs diff | 2.97 levels | — |
| pixels differing > 1 level | 80.4 % | — |
| pixels differing > 8 levels | 7.9 % | 24.5 % |

- filter at 100 % (shipped): `/workspace/nsfw-fix/results/ws4/B_no_vae_roundtrip/HasMetadata_00005_.png`
- filter at 50 %: `/workspace/nsfw-fix/results/ws4/D_skinblend_050/HasMetadata_00011_.png`

(`results/ws4/metrics_A3_blend_D_vs_B.json`.) Note this is a whole-frame skin
filter, so the difference is spread across the image rather than concentrated —
80.4 % of pixels move, but only 7.9 % move by more than 8 levels. Prompt id
`9760ac4e-a238-4516-a382-67df4ebdcc18`.

**Action taken:** changed nothing in the workflow. It is a quality call and the
A/B pair is the deliverable.

---

## Q-E — should the graph ship with a detailer whose negative prompt cannot apply?

**The fact.** `#114 FaceDetailer` runs at `cfg = 1` (widgets_values index 6, on a
29-entry array that maps exactly onto `impact_pack.py:735-786`). At cfg 1 there
is no classifier-free guidance, so **the negative conditioning is not applied at
all**.

`#105 "Face Detailer Negative Prompt"` is a fully written, carefully specific
prompt — `"deformed, ugly, blurry, bad anatomy, disfigured, extra eyes, cropped
face, out of frame, deformed piercing, bad piercing, watermark, text"` — and it
does nothing.

**Why this matters for a buyer specifically.** Root `#649` tells the buyer to
fill in the *positive* prompt on this node. A buyer who opens the subgraph to do
that will see a populated negative prompt sitting next to it and will reasonably
assume it is protecting them. It is not. If they later add "extra fingers" to it
because they are seeing bad hands, nothing will change and they will have no way
to find out why.

**My guess:** cfg 1 is deliberate — Z-Image with a distilled/low-CFG sampler
(`euler_ancestral` + `kl_optimal` at 30 steps) is a normal cfg-1 configuration,
and the same pattern appears on `#165` Mouth Detailer (cfg 1) and `#406` eyes
(cfg 1). So the negative prompts are the accident, not the cfg.

**Action taken:** changed nothing — raising cfg is output-changing and is your
call, and deleting the negative text would destroy information. Two low-risk
options for you: retitle `#105` to say it is inactive at cfg 1, or raise cfg and
A/B it. I did not do either unilaterally.

Note the same applies to `#167` "Mouth Detailer Negative Prompt", which is
already empty — consistent with someone having worked this out for that node and
not the others.
