# P2-RENDER — face quality grid: the arm list

Written **before any render was submitted**, as briefed. Everything below is
read out of `OFMTech-NSFW/OFMTech_NSFW.json` at
`sha256 f1ac7e55d375380033f6b0acc67ee0f4706dd618303075f86213fc09e6beb22e`
(`master` @ `73f3d5c`, i.e. **D1 reverted** — `#597`/`#616` present, sg
`2. Base Generator (SDXL)` has 28 nodes, confirmed).

**Nothing here ships.** Every arm is a scratch copy under the session
scratchpad. `OFMTech-NSFW/OFMTech_NSFW.json` is not touched by this workstream.

---

## The complaint and where it can come from

The face is worked on **four** times between the base sample and the save, not
twice. All four are read from the file:

| # | node | stage | what it does | steps | cfg | denoise |
|---|---|---|---|---|---|---|
| 1 | `#607 FaceDetailerPipe` | sg `2. Base Generator (SDXL)` | SDXL face pass, inside the base generator | 20 | 3 | **0.45** |
| 2 | `#91`+`#87 ImageBlend` | sg `3. Hands, Skin & Second Upscale (SDXL)` | `x1_ITF_SkinDiffDetail_Lite_v1.pth` skin-detail model, blended at **factor 1** | — | — | — |
| 3 | `#98 UltimateSDUpscale` | sg 3 | 1.5x upscale re-diffusion | 2 | 1 | 0.08 |
| 4 | `#114 FaceDetailer` | sg `5. Face & Mouth Detail (Z-Image)` | Z-Image face pass | **30** | 1 | **0.80** |

Run order, from the root links (`1381`, `1398/1399`, `1421`, `1445`):
`#619 base gen` → `#587 hands/skin/upscale` → `#620 face+mouth` → `#622 eyes` →
`#505 SaveImage` (`#623` anatomy is `mode: 4`, bypassed).

Two things I read in the file that bear directly on the complaint and that I
had not been told:

* **`#87 ImageBlend` at `blend_factor: 1` is not a blend.** `image1` is `#92
  HandDetailer`'s output, `image2` is `#91 ImageUpscaleWithModel` running
  `x1_ITF_SkinDiffDetail_Lite_v1.pth` (`#90 UpscaleModelLoader`). At factor 1
  the output *is* `image2`. A dedicated **skin-detail amplifier runs at full
  strength with nothing blended back**, on the whole frame, before the face
  pass ever sees it. That is arm D.
* **The mouth pass in the same subgraph already uses the turbo design point.**
  `#165 Mouth Detailer` is the same `FaceDetailer` class on the same
  `zimage.safetensors` model and runs **steps 8, denoise 0.35**. `#114`, the
  face, runs **steps 30, denoise 0.80**. Same stage, same model, same sampler
  and scheduler (`euler_ancestral` / `kl_optimal`), same cfg 1. That is an
  internal control for arm C, in the file, independent of P3's hash
  identification of the model as **Z-Image-TURBO**.
* Also noted, not an arm of mine: `#114`'s positive conditioning is `#106
  CLIPTextEncode` = `"TRIGGER, PROMPT FOR YOUR MODEL"`. At denoise 0.80 the
  face is being re-generated for 30 steps against a placeholder string. WS4
  logged this as D2 and it is documented buyer-facing text, so I am not
  changing it — but it is context for why 0.80 may be doing harm.

---

## Fixed across every arm

**Seed.** `#483 INSTARAW_RealityPromptGenerator` batch entry `default-01`,
`"seed": 12345`, `"seed_control": "fixed"` — the shipped values, unchanged.
Every `control_after_generate` in the graph is `"fixed"`; the two detailers
under test carry their own fixed seeds (`#114` = `1111111`, `#607` =
`100097229797074`).

**Prompt.** The shipped batch entry with **one clause added**, so the render
exercises the complaint (the owner's framing: some texture is intended):

> positive: `photorealistic portrait photograph of a young woman standing in soft window light, natural skin texture with visible pores, light freckles across her nose and cheeks, detailed eyes, detailed hands at her sides, looking at the camera, 85mm lens, shallow depth of field`
>
> negative: `bad quality, worst quality, low quality, deformed, extra fingers, watermark, text`

The only difference from the shipped text is `light freckles across her nose
and cheeks, ` inserted after `visible pores, `. Negative prompt is the shipped
string verbatim.

**LoRAs.** Both stacks left at the shipped `"None"` — `#618` (SDXL) and `#116`
(ZIT). No LoRA is loaded in any arm.

**`pick_list`.** `inputs.pick_list = "0"` is set on `619:603
INSTARAW_ImageFilter` **in the submitted API prompt only, identically in every
arm. No arm's workflow file contains it.** Without it `#603` opens the
selector, waits 600 s and aborts the render
(`ComfyUI_INSTARAW/nodes/.../image_filter.py`, per WS4). The batch is B=1 so
`"0"` is the only valid pick.

**How each arm's API graph is produced.** Scratch workflow JSON →
`app.loadGraphData()` → `app.graphToPrompt(app.rootGraph)` in a real Chromium
against the live ComfyUI — the same conversion the Run button performs — then
POSTed to `/prompt`. Every arm passes
`python3 tools/preflight/integrity.py <arm.json>` with **0 problems** before
submission (all 8 confirmed at time of writing), and every arm's API graph is
diffed against the baseline's with `tools/graph_diff/graph_diff.py` to prove
only the intended input moved.

**This is A/B evidence about how the face looks. It is not a claim that the
workflow works.** The project rule is "browser or it didn't happen", and main
has separately proven the buyer journey in a real browser (Phase 0). My renders
are driven through a modified API prompt and press no Run button; they must not
be read as that proof.

---

## Phase 1 — one variable at a time (8 renders, no cross product)

| arm | changed | file |
|---|---|---|
| `A0_baseline` | nothing (shipped graph + fixed seed + freckle prompt) | — |
| `A_drop_sdxl_face_pass` | `#607 FaceDetailerPipe` **removed** from sg 2 | link `1232` re-originated to `#596[0]`; links `1255`,`1256` deleted; sg 2 → 27 nodes |
| `B_zface_denoise_065` | `#114` `widgets_values[9]` denoise `0.80 → 0.65` | |
| `B_zface_denoise_050` | `#114` denoise `0.80 → 0.50` | |
| `B_zface_denoise_035` | `#114` denoise `0.80 → 0.35` | |
| `C_zface_steps_16` | `#114` `widgets_values[5]` steps `30 → 16` | |
| `C_zface_steps_08` | `#114` steps `30 → 8` | the model's design point |
| `D_skinblend_075` | `#87` `widgets_values[0]` blend_factor `1 → 0.75` | |

### Widget-index check, done before indexing anything

`/object_info` on the live server says `FaceDetailer` has **28 widgets** in
order `guide_size, guide_size_for, max_size, seed, steps, cfg, sampler_name,
scheduler, denoise, feather, …`. `seed` is widget 3, so its synthetic
`control_after_generate` companion occupies array index 4 and shifts everything
after it by one. `#114.widgets_values` has **29** entries = 28 + 1. That
reconciles, so:

* index 5 = `steps` — file holds `30` ✓
* index 6 = `cfg` — file holds `1` ✓ (**not touched; cfg 1 is required by this model**)
* index 9 = `denoise` — file holds `0.8` ✓

`FaceDetailerPipe` is the same 28+1 = 29 and `#607` matches (index 9 = `0.45`).
`ImageBlend` has 2 widgets (`blend_factor`, `blend_mode`) and `#87` has 2
entries, index 0 = `1` ✓. The builder asserts the array length **and** the
existing value at the index before writing; a desync aborts the build.

### `#598` after `#607` is removed

`#598 ToDetailerPipeSDXL`'s only output link was `1256` → `#607`. I **left the
node in place, orphaned**, rather than delete it: its `clip` inputs `1367` and
`1368` are the *only* internal consumers of sg-2 input slot 4, so deleting it
would strand a declared subgraph input. It costs nothing at run time —
`execution.py:727` walks the execution list backwards from `execute_outputs`
only, and `validate_prompt` (`execution.py:1014-1063`) validates output nodes
and their dependencies only, so an unreferenced node is neither validated nor
executed. Its detector `#611 UltralyticsDetectorProvider` has no other consumer
either and therefore also stops loading in this arm.

## Phase 2 — combinations, chosen after Phase 1

Built but only rendered if Phase 1 justifies them:
`E_dropA_denoise050`, `F_dropA_denoise050_skin075`,
`G_dropA_denoise050_steps16`, `H_skinblend_050`. The exact set will be picked
from the Phase 1 winners; whichever run, they are listed with their measured
results in `notes/P2-render.md`.

## Timing discipline

`execution_cached` is read from `/history` for every arm and recorded in each
`meta.json` as `cached_nodes`. Arms whose cache state does not match are **not
compared on time**. A wrong "+31 % slower" conclusion came out of exactly this
last run.

## Output layout

`results/face/arms/<arm_name>/` — `*.png`, `api_graph.json`, `meta.json`
(`arm`, `changed`, `prompt_id`, `exec_seconds`, `cached_nodes`). Nothing else
is written under `results/face/` except this file.
