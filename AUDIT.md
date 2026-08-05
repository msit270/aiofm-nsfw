# AUDIT.md — defects in OFMTech_NSFW.json

Ranked by how much it would matter **if true**. Every item states what I read in
the file, what I infer from it, and how to settle it.

Marks: **[F]** read from the file · **[I]** inference · **[?]** unresolved.

Severity: **S1** wrong output a buyer would not notice · **S2** wasted
time/VRAM · **S3** correctness risk only if something is changed · **S4** cosmetic.

---

## A0 — **As shipped, this file renders with an empty prompt and seed 0** · **S1, worst in the file**

This is the answer to "the entry node is unconnected — either that is the bug,
or it is fed some other way." It is fed some other way, and **the feed is broken**.

**[F]** `#483 INSTARAW_RealityPromptGenerator` is not fed by its image inputs at
all. Its prompt batch arrives from a client-side panel via `node.properties`. In
this file:

```
properties.prompt_batch_data  =  "[]"          ← the key the pack reads
properties.prompt_queue_data  =  <9,991-char JSON, 6 real prompt entries>
```

**[F]** `grep -rl "prompt_queue_data" ComfyUI_INSTARAW/` returns **zero files**.
`prompt_batch_data` returns four (`js/advanced_image_loader.js`,
`js/batch_image_generator.js`, `js/reality_prompt_generator.js`,
`nodes/input_nodes/reality_prompt_generator.py`).

So the six saved prompts are **orphaned data under a key no code in the shipped
pack reads.** The key that *is* read holds an empty array.

**[F]** `nodes/input_nodes/reality_prompt_generator.py:224-227`:

```python
# 7) If prompt_batch is empty, return valid empty lists (no exception)
if generation_count == 0:
    print("[RPG] Warning: Prompt batch is empty. Returning empty prompt lists.")
    return ([""], [""], [0], 0, resolved)
```

It does not raise. It returns an empty positive, an empty negative, and **seed 0**.

**[F]** Those three outputs are wired straight into sg1:
`#483.0` → `#619.value` → `#590` → `#599` (**positive conditioning**);
`#483.1` → `#619.value_1` → `#605` → `#606` (**negative conditioning**);
`#483.2` → `#619.seed` → `#592 KSampler.seed`.

**[I] Consequence:** open this file, hit Queue without touching the panel, and it
generates from an **empty prompt at seed 0**. It also **defeats the shipped
negative prompt** — `#605`'s widget default
`"bad quality, worst quality, low quality,"` is overridden by the empty string,
because a linked input always wins over a widget.

**[F] And the six orphaned prompts are not even NSFW character prompts.** All six
are interior/scene photography — walk-in closets, a home theatre, "a group of
people floating on a…". All carry `seed: 1111111`, `repeat_count: 1`. They read
as demo content from an unrelated test, not this product's content.

**Why this went unnoticed [I]:** in day-to-day use the author drives the panel by
hand, which repopulates `prompt_batch_data` in the live session. The defect only
manifests on a **fresh load of the saved file** — i.e. exactly what a buyer does.

**This is the single most important thing to fix before anyone else opens this
file.** `PROPOSALS.md` P0 covers it, and it is the one item there that does **not**
need a GPU.

---

## A0b — `#483`'s `widgets_values` has 6 entries; the current pack creates 5 widgets · **S3**

**[F]** `widgets_values: ["", "", "", "[]", "[]", false]` — six entries.

**[F]** The pack's `INPUT_TYPES` defines three widget-typed inputs
(`gemini_api_key`, `grok_api_key`, `aspect_label`), and
`js/reality_prompt_generator.js` adds two more serializing widgets
(`prompt_batch_data` at `:1157`, `sdxl_mode` at `:1167`). **Three plus two is five.**

Corroboration **[F]**: the node's own
`properties.ue_properties.widget_ue_connectable` lists exactly three names —
`gemini_api_key`, `grok_api_key`, `aspect_label`.

**[I]** The file was saved by a **different build of the pack** than the one in
this folder. This is the `widgets_values` desync from the trap list — not on a
subgraph host (those are clean, see the bottom table), but on the entry node.

It is currently defused by accident: `onConfigure`
(`js/reality_prompt_generator.js:9174`) overwrites the widget from the property
rather than trusting the serialized value. **But no widget value on this node can
be trusted as authored**, including `aspect_label`, which is saved as `""` rather
than its declared default `"1:1"`.

---

## A1 — Pure VAE round-trip in sg1 wastes two full VAE passes at ~1434×1843 · **S2**

**[F]** In sg1:

- `#607 FaceDetailerPipe` `out[0] image` → `#597 VAEEncode.pixels`
- `#597 VAEEncode` `out[0] LATENT` → `#616 VAEDecode.samples`
- `#616 VAEDecode` `out[0] IMAGE` → `#617 UltimateSDUpscale.image`

Nothing sits between the encode and the decode. `#597` and `#616` both take
`vae` from `#613.2`, the same VAE.

**[I]** This is a no-op in intent: image → latent → image. It costs one VAE
encode plus one VAE decode at roughly 1434×1843 (§12 of `MAP.md`), and applies
one extra lossy VAE round-trip to every generated image.

**Why it is probably historical**: a sampler almost certainly used to sit between
them and was deleted, leaving the encode/decode pair orphaned.

**Settle it**: delete `#597` and `#616`, wire `#607.0` → `#617.0`. This is a
*graph-diff-provable* change on every node except the two removed — see
`PROPOSALS.md` P4. It is **not** provably inert on pixels, because a VAE
round-trip is lossy, so it needs an A/B pair for your eye.

---

## A2 — sg1's `denoise` is driven by a bypassed node with nothing to pass through · **S3**

**[F]**
- sg6 `#637 PrimitiveFloat`, `widgets_values: [0.5]`, `mode: 4` (bypassed).
- `#637` `out[0]` → sg6 output slot 1 (`FLOAT`).
- Root: `#647`(sg6) `out[1]` → `#619`(sg1) `in[5] denoise`, link **1504**.
- `#619`'s `inputs[5]` carries `"widget": {"name": "denoise"}` **and** a link.
- `#619`'s `widgets_values` is `[]` — no stored fallback on the host.
- Inside sg1, `#592 KSampler.denoise` is wired from the subgraph input, and its
  own `widgets_values` ends in `1`.

**[I]** A bypassed `PrimitiveFloat` has no input of type FLOAT to forward, so the
link resolves to nothing. The most likely outcome is that `#592`'s own widget
value of `1` is used, which is the correct value for txt2img from an empty
latent — so the graph probably behaves correctly today **by accident**.

**Why it still matters**: the wire says the denoise is externally controlled, and
it is not. Anyone who un-bypasses `#637` to "turn denoise back on" silently sets
the base sampler to **0.5**, which on an empty latent produces a half-noised
image. The safe state and the obvious-looking state are opposites.

**[?]** I cannot confirm from here whether ComfyUI falls back to the widget or
raises "Required input is missing". `PROPOSALS.md` P13 tests both.

---

## A3 — `#87 ImageBlend` at `blend_factor: 1.0` discards one of its two inputs · **S1**

**[F]** In sg0:
- `#92 FaceDetailer` "HandDetailer" `out[0]` → `#87.image1` **and** → `#91.image`
- `#90 UpscaleModelLoader` = `x1_ITF_SkinDiffDetail_Lite_v1.pth` → `#91 ImageUpscaleWithModel`
- `#91` `out[0]` → `#87.image2`
- `#87 ImageBlend` `widgets_values: [1, "normal"]`

**[I]** ComfyUI's core `ImageBlend` computes
`image1 * (1 - blend_factor) + blended * blend_factor`, and `normal` mode returns
`image2`. At `blend_factor = 1.0` the output is **exactly `image2`** and `image1`
contributes nothing.

So `#87` is a no-op passthrough of `#91`, and the skin-detail filter is applied
at **100% strength** with no blend back toward the un-filtered image.

**Why this reads as unintended**: you do not place an `ImageBlend` node, wire both
the original and the filtered version into it, and then set the factor so the
original is discarded. The node exists precisely to allow partial blending. A
value like 0.5 is the conventional use of `x1_ITF_SkinDiffDetail`.

This is a **quality** call, which I cannot make. `PROPOSALS.md` P19 produces the
A/B ladder at 0.0 / 0.25 / 0.5 / 0.75 / 1.0 for you to look at.

---

## A4 — sg2's face detailer prompt is an unfilled placeholder · **S1**

**[F]** sg2 `#106 CLIPTextEncode`, titled "Face Detailer Prompt":

```
"widgets_values": ["TRIGGER, PROMT FOR YOUR MODEL"]
```

`#106` `out[0]` → `#114 FaceDetailer.positive`.

That literal string — including the typo `PROMT` — is the positive conditioning
for the face detail pass on **every render**, at denoise **0.8**, which is the
highest denoise of any detailer in the graph.

**[I]** This is template text the author left for the buyer to replace, and it
was never replaced. At denoise 0.8 the face is substantially regenerated, so the
conditioning is not incidental.

Note the asymmetry: the *negative* (`#105`) is a properly written prompt. Only
the positive is a placeholder.

**Also [F]**: `#105`/`#106` take `clip` from `#110 CLIPLoader` **directly**, while
`#114` takes `clip` from sg2's input (i.e. through the `#116` "Your ZIT LoRa"
stack). A buyer's Z-Image LoRA therefore does not affect these two encodes.

**Fix**: this is a content decision, not a structural one — it needs your text.
Flagged in `QUESTIONS.md` Q2.

---

## A5 — the dead ControlNet path is also *mis-wired*, so "revive it" is not a one-click change · **S3**

**[F]** In sg6, all three nodes are `mode: 4`:

```
#639 ControlNetLoader  out[0] ==> #638.2 (control_net), #641.0
#641 SetUnionControlNetType  in[0] <== #639.0   out[0] ==> (none)
#638 ControlNetApplyAdvanced in[2] control_net <== #639.0
```

`#641` sits **in parallel** with `#638`, not in series. Its output is connected to
nothing.

**[I]** `#639` loads `controlnet-union-sdxl-promax.safetensors` — a *union*
ControlNet, which requires `SetUnionControlNetType` to select a mode before use.
`#641` is set to `depth`. Because `#638` reads the raw loader output instead of
`#641`'s, **the union type is never applied**.

So the ControlNet path is not merely switched off: as wired, un-bypassing it
would run a union ControlNet with no type set. Whatever this produces, it is not
what the `depth` setting implies.

This changes the verdict question. It is not "revive or delete" — it is "repair
and revive, or delete". See `PROPOSALS.md` P12 for the repair, and my
recommendation to **delete** in `QUESTIONS.md` Q3.

---

## A6 — sg6's latent switch may evaluate its dead branch · **S2** **[?]**

**[F]**
- `#636 INSTARAW_LatentSwitch`, `widgets_values: [false]`, not bypassed.
  `in[0] input_true` ← `#631`; `in[1] input_false` ← `#635 EmptyLatentImage`.
- `#631 VAEEncode` is `mode: 4` (bypassed). Its `pixels` ← `#632`, `vae` ← sg6 input.
- `#632 INSTARAW_ImageListFromBatch` is **not** bypassed. Its `images` ← `#630`.
- `#630 INSTARAW_ImageResizeFill` is `mode: 4`, and its `image` and
  `background_image` inputs have **no link at all**.

**[I]** Two possible failures, depending on facts I cannot check here:

1. `#631` is a bypassed `VAEEncode`. It outputs LATENT; its inputs are IMAGE and
   VAE. Neither matches LATENT, so bypass has nothing to forward and
   `#636.input_true` resolves to nothing. If `input_true` is a **required** input,
   the prompt is invalid and the graph fails to queue.
2. If `INSTARAW_LatentSwitch` does not declare lazy evaluation, ComfyUI resolves
   *all* inputs before executing the node, so the dead `#632` branch is walked
   even though `boolean` is `false`.

Since the graph presumably runs for you today, (1) is probably not happening —
which implies `input_true` is optional, or the switch is lazy, or both. **[?]**

`PROPOSALS.md` P13 resolves this by reading the pack source and by queueing the
graph unchanged.

---

## A7 — Wired inputs override widgets in four places · **S3**

The `CLAUDE.md` trap is present. In each case the widget value shown in the UI is
**not** what runs. All **[F]**:

| Node | Widget says | Actually driven by | Real value |
|---|---|---|---|
| sg0 `#98 UltimateSDUpscale` | `tile_width` 512, `tile_height` 512 | `#99 GetImageSize` of `#87` | the **full image dimensions** |
| sg4 `#415 MediaPipe-FaceMeshPreprocessor` | `resolution` 512 | `#399 GetImageSize` of `#414` | **1920** |
| sg4 `#401 INSTARAW_ImageResizeFill` | 512 × 512 | `#400 GetImageSize` of `#404` | the original crop size |
| sg4 `#404 ImageCrop` | 512, 512, 0, 0 | `#403 MaskBoundingBox+` | the detected face bbox |

`#404`, `#401` and `#415` are correct by design — that is how a crop/detail/
composite loop is supposed to work.

**`#98` is the one that matters.** Setting `tile_width`/`tile_height` to the whole
image means UltimateSDUpscale's tile size **scales with input resolution**. At the
current ladder that is ~1792×2304 tiles against a 1.5× target, so tiling is
nearly meaningless and peak VRAM tracks the full frame. A buyer who raises the
base resolution gets a quadratic VRAM increase from a node whose widgets say a
fixed 512. See `PROPOSALS.md` P11.

Also note sg6 `#635 EmptyLatentImage`: width/height are wired from `#625`/`#628`
**and** the widgets read 896/1152, which **agree**. No defect — recorded so the
next reader does not have to re-check.

---

## A8 — `#418 ImageCompositeMasked` in sg4 has no mask · **S1**

**[F]** sg4 `#418 ImageCompositeMasked`: `destination` ← `#431`, `source` ←
`#401`, `x`/`y` ← `#403`, and **`in[2] mask` has no link**.

**[I]** With no mask, the resized detailed crop is pasted back as a hard
rectangle. Every other detail pass in this graph goes through Impact's
`FaceDetailer`, which feathers (`feather` 18 in sg2, 9 in sg0, 2 in sg4's
`#406`). The final composite in sg4 does not.

`#406 DetailerForEachDebug` has a `feather` of 2 internally, but that feathers the
eye SEGS *within* the crop, not the crop's own boundary against the full frame.

Whether a seam is visible depends on how much `#406` changed the crop at denoise
0.42 — a quality question. `PROPOSALS.md` P14 proposes wiring a feathered mask and
gives the A/B.

---

## A9 — Nine nodes are wired to nothing and one is fully orphaned · **S2/S4**

**[F]** From a backwards reachability walk from `#505 SaveImage` across all
subgraph boundaries, these contribute to no output at all:

| Node | Where | Note |
|---|---|---|
| `#583 DetailerPipeToBasicPipe` | sg2 | **no input link and no output links**, and *not* bypassed |
| `#604 INSTARAW_BooleanBypass` | sg1 | 4 outputs unconnected |
| `#614 PrimitiveBoolean` "ENABLE IMAGE FILTERING?" | sg1 | feeds only `#604` |
| `#627 PrimitiveFloat` | sg6 | feeds only `#629`/`#633` |
| `#629 INSTARAW_BooleanBypass` | sg6 | 4 outputs unconnected |
| `#633 INSTARAW_FloatSwitch` | sg6 | output unconnected |
| `#634 INSTARAW_BooleanBypass` | sg6 | 4 outputs unconnected |
| `#641 SetUnionControlNetType` | sg6 | output unconnected — see A5 |
| `#645 INSTARAW_BrandingNode` | sg6 | bypassed, no inputs or outputs at all |

**[?]** The three `INSTARAW_BooleanBypass` nodes and `#614` are very likely
**client-side controls** that toggle other nodes' bypass state from the browser —
the pack ships `js/boolean_bypass.js` and `js/group_bypass_detector.js`. If so
they are not dead, they are UI, and deleting them would remove the "ENABLE IMAGE
FILTERING?" switch a buyer is meant to use. **Do not delete these until the pack
source confirms their mechanism.**

`#583` has no such excuse — it has no links in either direction.

---

## A10 — Development instrumentation runs on every render · **S2**

**[F]** 13 output-type nodes that are not the product:

| Type | Count | Ids |
|---|---|---|
| `Image Comparer (rgthree)` | 7 | `#104`,`#118`,`#164`,`#419` (root), `#96` (sg0), `#237`,`#241` (sg5, bypassed) |
| `PreviewImage` | 4 | `#22` (root), `#395`,`#396` (sg4), `#642` (sg6, bypassed) |
| `PreviewAny` | 1 | `#481` (root) |
| `INSTARAW_PromptBatchPreview` | 1 | `#480` (root) |

**[I]** ComfyUI executes output nodes unconditionally, so the 9 non-bypassed ones
each cost a PNG encode and a temp-file write of a full-resolution image every
run. The four root comparers each hold two ~2688×3456 images.

This is a **packaging** problem more than a speed one: a buyer opening this
workflow sees eleven preview panels and no indication which is the deliverable.
See `PROPOSALS.md` P16.

---

## A11 — Loader duplication · **S2** **[?]**

**[F]** Same file loaded by multiple nodes: `sam_vit_b_01ec64.pth` ×4 (3 live),
`bbox/face_yolov8m.pt` ×3, `4x-UltraSharpV2.pth` ×2,
`dmd2_sdxl_4step_lora_fp16.safetensors` ×2. Full table in `MAP.md` §13.

**[I]** ComfyUI caches loader outputs keyed on class and input values, so the
duplicates are probably deduplicated at execution and cost little VRAM. I cannot
confirm the cache behaviour across subgraph boundaries from here.

The real cost is **drift**: three `face_yolov8m` providers can be changed
independently, and `#611`/`#107`/`#426` are already pinned to three different
`comfyui-impact-subpack` versions in their metadata (`1.3.2`, `1.3.5`, and one
inside sg4). Nothing enforces that they stay the same file.

`PROPOSALS.md` P15 measures this before anything is consolidated.

---

## A12 — Node metadata spans wildly different pack versions · **S3**

**[F]** From `properties.cnr_id` / `ver`:

- `comfy-core`: **0.3.15 → 0.3.70**, plus six nodes tagged `0.15.1`, one `0.17.2`.
- `comfyui-impact-pack`: `8.8.1`, `8.25.1`, `8.28.2`, and a raw SHA `cd34cfdd…`.
- `comfyui-impact-subpack`: `1.2.9`, `1.3.2`, `1.3.5`.
- `comfyui_essentials`: two different SHAs.
- `comfyui_ultimatesdupscale`: `1.1.2` and `1.3.3` — the graph's **two**
  `UltimateSDUpscale` nodes were placed against different versions of the pack.
- `rgthree-comfy`: `1.0.2508012353` and `1.0.2510052058`.

**[I]** These are timestamps of when each node was last placed, not requirements —
ComfyUI writes the installed version into `properties` at edit time. They do not
constrain anything on their own.

But they do mean this file was assembled across a long period and **has never been
opened-and-resaved wholesale against one pack set**. Two `UltimateSDUpscale` nodes
from versions `1.1.2` and `1.3.3` both carry **21 `widgets_values`**, which is
reassuring; if the widget list had changed between those versions, one of them
would now be misaligned.

The `0.15.1` / `0.17.2` tags are **not** core versions in the `0.3.x` series and I
cannot account for them. **[?]** Flagged in `QUESTIONS.md` Q4.

The practical floor is **core ≥ 0.3.70** (`#614 PrimitiveBoolean`) — higher than
the `0.3.66` the setup script enforces. See `SETUP.md`.

---

## A13 — 13 duplicate link records, no ambiguity · **S4**

**[F]** Thirteen subgraph output slots receive more than one link record — sg2
slot 2 has **seven**, sg1 slot 4 has six, sg1 slot 5 has five.

I checked every one: **all resolve to a single distinct origin**. There is no
case where two different producers feed one output slot, so there is no
ambiguity about which value wins.

This is file bloat and an artifact of repeated rewiring in the editor. Harmless.
Recorded so it is not mistaken for a defect later.

---

## A14 — `#506` is titled "Hand Prompt" but is the negative · **S4**

**[F]** sg0 has two `CLIPTextEncode` nodes titled "Hand Prompt":
- `#93` → `#92.positive`, text `"Detailed hand, detailed fingers, …"`
- `#506` → `#92.negative`, text `""`

Cosmetic, but in a graph being sold it is exactly the kind of thing that costs a
support ticket.

Also **[F]**: `#93` encodes with sg0's `clip_1` (the LoRA'd CLIP from `#618`)
while `#506` encodes with `clip` (raw from `#613`). The positive and negative for
the same detailer are encoded with two different CLIPs. Probably harmless for an
empty negative; would matter if a buyer fills it in.

---

## A15 — `INSTALL MODELS.txt` step 1 is now stale · **S4**

**[F]** `INSTALL MODELS.txt` lines 6–12 tell the buyer that `lipsv1`, `pussy2`
and `nipple` "will need to be moved to the bbox holder".

**[F]** `aiofm_setup.sh` lines 838–844 already hardlink every `.pt` in
`models/ultralytics/` into `models/ultralytics/bbox/`.

**[I]** The manual step is redundant when the setup script has run. Worse, the
names do not match the files the script fetches: the doc says `pussy2`, the file
is `pussyV2.pt`; the doc says `lipsv1`, the file is `lips_v1.pt`. A buyer
following the text literally will look for files that do not exist.

Details in `SETUP.md`.

---

---

## A21 — the graph is not reproducible from the seed it exposes · **S1**

**[F]** Two independent noise seeds drive the samplers:

| Node | Seed | `control_after_generate` | Wired? |
|---|---|---|---|
| sg1 `#592 KSampler` | from `#483.seed_list` | `"randomize"` (widget, overridden by link) | **yes** |
| sg1 `#600 KSamplerAdvanced` | `578361683541099` | **`"randomize"`** | **no** — widget only |
| sg1 `#617 UltimateSDUpscale` | `34651603` | `"fixed"` | no |
| sg0 `#98 UltimateSDUpscale` | `1966745044` | `"fixed"` | no |
| all five detailers | fixed values | `"fixed"` | no |

`#600` has no `seed` input slot at all **[F]** — its `noise_seed` is widget-only,
and it is set to randomize after every run.

**[I]** So the hires-fix pass reseeds itself on every queue regardless of what the
prompt generator's `seed_list` says. Two runs with an identical RPG seed produce
different images. For a product where the user picks a seed to reproduce a result
they liked, that is a defect, not a preference.

The fix is a one-widget change (`"randomize"` → `"fixed"`), or better, wire
`#600.noise_seed` from the same `seed_list` so both samplers move together. See
`PROPOSALS.md` P10.

## A22 — the face is detailed twice, and the second pass probably erases the first · **S2**

**[F]** Five live detailer passes, in execution order:

| # | Node | Stage | Target | Model | Denoise | guide/max |
|---|---|---|---|---|---|---|
| 1 | `#607 FaceDetailerPipe` | sg1 | **face** (`face_yolov8m`) | SDXL + PAG | **0.45** | 1280/1280 |
| 2 | `#92 FaceDetailer` | sg0 | hands (`hand_yolov8s`) | SDXL | 0.42 | 1024/1024 |
| 3 | `#114 FaceDetailer` | sg2 | **face** (`face_yolov8m`) | Z-Image | **0.80** | 1024/1024 |
| 4 | `#165 FaceDetailer` | sg2 | mouth (`lips_v1`) | Z-Image | 0.35 | 1808/1808 |
| 5 | `#406 DetailerForEachDebug` | sg4 | eyes (FaceMesh) | Z-Image | 0.42 | 1920/1920 |

Passes 1 and 3 detail **the same region with the same detector**.

**[I]** Pass 1 runs at ~1434×1843. Between it and pass 3 the image goes through
`#617` (×1.25) and `#98` (×1.5). Pass 3 then re-detects the same face and
resamples it at **denoise 0.80** — the highest in the graph — on a Z-Image model,
against the placeholder prompt from A4.

At 0.8 denoise, very little of pass 1's output survives. So pass 1 may be paying a
full detailer pass to produce detail that pass 3 discards.

I cannot confirm this without rendering. It is the highest-value ablation in
`PROPOSALS.md` (P11) and the most likely source of free speed.

## A23 — a bbox-only detector is wired into a segmentation input · **S2** **[?]**

**[F]** sg2 `#107 UltralyticsDetectorProvider` loads **`bbox/face_yolov8m.pt`**.
Its `out[1] SEGM_DETECTOR` is wired to `#114 FaceDetailer.segm_detector_opt`,
while its `out[0] BBOX_DETECTOR` goes to `#114.bbox_detector`. So one bbox model
feeds both the bbox and the segm slot of the same detailer.

**[F]** The same pattern appears in sg5 `#171` (`bbox/nipple.pt` → `#176`
`bbox_detector` *and* `segm_detector_opt`), which is bypassed.

**[F] These two are the outliers.** The other five providers — `#611` (sg1),
`#161` (sg3), `#426` (sg4), `#89` (sg0), `#246` (sg5) — all leave
`SEGM_DETECTOR` **unconnected**.

**[I]** A `yolov8m` *detection* checkpoint has no mask head, so it cannot produce
real segmentation. Impact Subpack returns both wrapper objects unconditionally, so
this will not fail at load; what it does at *detect* time — degrade gracefully,
return empty masks, or throw — I cannot determine without running it.

That five of seven providers leave the slot empty suggests `#107`'s and `#171`'s
connections were made by accident, likely by dragging from the wrong output.

**Settle it:** disconnect `#107.out[1]` from `#114.segm_detector_opt`, graph-diff
to confirm nothing else moved, and A/B the face. If identical, the link was inert
and should go for clarity. Added as a sub-task of `PROPOSALS.md` P7, which already
touches the face passes.

---

# Findings in `ComfyUI_INSTARAW` itself

These are not workflow defects, but the pack ships with the workflow and I read
its source, so they belong in the same audit. All verified directly.

## A16 — 23 HTTP routes registered on the ComfyUI server with `Access-Control-Allow-Origin: *` · **S1 (security)**

**[F]** `nodes/api_nodes/creative_api.py:22-26`:

```python
CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
}
```

**[F]** 23 `routes.post/get/options` registrations across `nodes/`, including
`/instaraw/generate_creative_prompts`, `/instaraw/generate_character_description`,
`/instaraw/get_random_prompts`, `/instaraw/batch_upload`, `/instaraw/migrate_images`,
`/instaraw/view/{filename}`.

**[I]** With a wildcard origin, **any web page open in the buyer's browser can POST
to their ComfyUI's `/instaraw/*` endpoints.** Some of those routes relay
user-supplied Gemini/xAI API keys to third parties, and `/instaraw/view/{filename}`
and `/instaraw/batch_upload` touch the filesystem.

ComfyUI is usually bound to localhost, which limits but does not eliminate this —
a malicious page can still reach `127.0.0.1:8188` from the user's own browser, and
on a rented pod the port is often exposed.

I am not equipped to judge how exploitable each route is, and I did not test any
of them. But **this ships to customers today** and it should get a deliberate
decision rather than an accidental one. Recommend scoping the origin to the
ComfyUI host before sale.

## A17 — `requirements.txt` will downgrade numpy for the whole ComfyUI install · **S1 (packaging)**

**[F]** Lines 29–98 of `requirements.txt` are a **verbatim paste of MediaPipe's own
pip-compile lockfile**, header comment included:

```
#    pip-compile --output-file=mediapipe/opensource_only/requirements_lock_3_12.txt …
```

Consequences, all **[F]** line references:

| Line | Pin | Problem |
|---|---|---|
| 2 | `# Note: torch and numpy are already included with ComfyUI` | **contradicted by line 63 in the same file** |
| 63 | `numpy==1.26.4` | hard pin — downgrades numpy env-wide. Highest blast radius in the file. |
| 73 | `opencv-contrib-python==4.10.0.84` | the **non-headless** build. `comfyui_controlnet_aux` — required by this graph — installs the *headless* OpenCV. Mixing the two distributions in one env is a known breakage. |
| 6 vs 79 | `Pillow` vs `pillow==10.4.0` | same package, twice, one pinned |
| 10 vs 89 | `scipy` vs `scipy==1.13.1` | same |
| 81 | `protobuf==4.25.5` | commonly clashes with packs wanting protobuf ≥5 |
| 13–14 | `#google-genai>=1.51.0` / `google-genai~=1.43.0` | someone deliberately pinned *down*; ComfyUI core's API nodes also depend on this |
| 102 | `mediapipe==0.10.14` | pinned "for compatibility with comfyui_controlnet_aux" — but **mediapipe is imported by zero files in this pack** |

**This directly collides with `aiofm_setup.sh`'s design.** That script filters
`torch|torchvision|torchaudio|onnxruntime|onnxruntime-gpu` out of every pack's
requirements (line 996) precisely to stop this class of damage — but **numpy and
opencv are not in its skip list**, and `ComfyUI_INSTARAW` is not in `NODE_REPOS`
at all, so it is never even passed through that filter.

Handling in `SETUP.md`.

## A18 — no LICENSE file, and an attribution that needs resolving before sale · **S1 (legal, not technical)**

**[F]** There is no `LICENSE`, `pyproject.toml`, or `setup.py` anywhere in the pack.

**[F]** `js/image_filter.js:18-19` credits *"Based on original work by chrisgoringe
(cg-image-filter)"* and links that repository. `INSTARAW_ImageFilter` — `#603` — is
a live node in sg1's main path.

**[F]** Meanwhile `branding_node.py:5-6` and `nsfw_detector.py:3-4` assert
"PROPRIETARY SOFTWARE - ALL RIGHTS RESERVED".

I am not a lawyer and this is not legal advice. But "no licence file" plus
"derived from a named third-party project" plus "all rights reserved" plus "we
are going to sell this" is a combination worth a deliberate check.

## A19 — three unprompted network fetches, one of them on first UI load · **S2**

**[F]** `nodes/nsfw_nodes/nsfw_detector.py:52` calls `download_model_if_missing()`
**from inside `INPUT_TYPES`**, with the exception swallowed:

```python
@classmethod
def INPUT_TYPES(cls):
    try: download_model_if_missing()
    except Exception: pass
```

`INPUT_TYPES` is called whenever ComfyUI builds `/object_info` — i.e. **on first UI
load**, whether or not the node is used. It fetches
`https://d2xl8ijk56kv4u.cloudfront.net/models/nudenet.onnx`.

Also **[F]**:
- `js/reality_prompt_generator.js:935,1528` fetches a **22 MB** prompts database
  from `instara.s3.us-east-1.amazonaws.com` with `cache: "no-store"`.
- `js/batch_image_generator.js:47-68` injects **PhotoSwipe 5.4.3 from the jsdelivr
  CDN** at runtime — an unpinned third-party script inside the buyer's ComfyUI.

None of these is a mid-*render* download, so none blocks a queue. But the
nudenet fetch fires unprompted on a fresh install, and an unpinned CDN script is a
supply-chain surface on a product you are selling.

## A20 — an identical hidden watermark in three JS files · **S4 (informational)**

**[F]** Exactly three files contain **417 zero-width characters** each:
`js/boolean_bypass.js`, `js/branding_node.js`, `js/image_filter.js`. Every other
file in `js/` has zero.

It is inert data, not code, and it transmits nothing by itself. **[I]** it looks
like an authorship/build fingerprint. You should simply know it is there and
decide whether it ships.

---

## Checked and clean — recorded so nobody re-does this work

| Trap from `CLAUDE.md` | Result |
|---|---|
| **Subgraph host `widgets_values` desync** | **Cannot occur.** All 7 definitions have `"widgets": []`; all 7 hosts have `"widgets_values": []`. Nothing is promoted, so nothing can shift. **[F]** |
| **`seed` dragging `control_after_generate`** | **Absent.** sg1's `#592 KSampler` holds all 7 widget entries in correct order with `"randomize"` at index 1, and `seed` is linked from the subgraph input. **[F]** |
| **`ImageResizeKJv2` lanczos-on-GPU** | **Not applicable.** No `ImageResizeKJv2` in this file — the pack (`ComfyUI-KJNodes`) is not used at all. **[F]** |
| **`DrawMaskOnImage` widget order** | **Not applicable.** No such node in this file. **[F]** |
| **`DownloadAndLoadSAM2Model` fp16 rename** | **Not applicable.** No such node in this file; all four SAM loads are Impact `SAMLoader` with `sam_vit_b_01ec64.pth`. **[F]** |
| Ambiguous multi-origin subgraph outputs | **None** — all 13 duplicated slots are single-origin (A13). **[F]** |
| Muted nodes | **None.** 24 bypassed (`mode:4`), 0 muted (`mode:2`). **[F]** |
