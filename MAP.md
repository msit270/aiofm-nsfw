# MAP.md — OFMTech_NSFW.json, structural description

Source: `OFMTech_NSFW.json` (346,228 bytes, `version: 0.4`, `revision: 0`).
Everything below is traced from that file. Node ids are given as `#id`; subgraph
ids `sg0`–`sg6` are **array indices into `definitions.subgraphs`**, matching the
numbering already in use in `CLAUDE.md`.

Claims are marked:
- **[F]** fact — read directly from the file, quotable.
- **[I]** inference — derived from [F] plus documented ComfyUI semantics. Not verified here.
- **[?]** unsure — flagged, needs the pod session or an upstream source read.

---

## 0. Headline corrections to the starting map

The hypothesis in `CLAUDE.md` was close on content but **wrong on order and on two
stage descriptions**. Corrections, each with evidence:

| Claim in CLAUDE.md | Status | Evidence |
|---|---|---|
| Run order `sg6 → sg1 → sg3/sg2 → sg4 → sg0` | **Wrong** | `sg0` runs **third**, not last. `#587`(sg0) outputs feed `#620`(sg2) inputs 0 and 1. sg0 is between sg1 and sg2. |
| sg5 "entirely dead" | **Half right** | All 11 nodes are `mode:4` **[F]**, but sg5 sits *on the output path*: `#623`(sg5) `out[0]` → `#505 SaveImage`. It passes its input through by bypass **[I]**. It is dead *logic* on a live *wire*. |
| sg5 = "pussy, nipples, breasts" (three detailers) | **Wrong** | There are **two** `FaceDetailer` nodes: `#256` "Pussy Detailer" and `#176` "Nipples Detailer". "Breasts" is only the title of a comparer, `#241` "Before \| After: Breasts". |
| sg2 = "second model family (UNET/CLIP/VAE)" | **Right, and now identified** | `#113 UNETLoader` = `zimage.safetensors`; `#110 CLIPLoader` = `qwen.safetensors`, type `lumina2`; `#109 VAELoader` = `ae.safetensors`. This is **Z-Image**, not a second SDXL. |
| sg6 = "inputs, latent, …" | **Partly** | sg6 has no image input at all. Its two `ImageResizeFill` nodes have `image` and `background_image` **unlinked** **[F]**. It is a resolution/latent source, not an input stage. |
| sg3 "exists to feed sg2" | **Half right** | It feeds sg2 (detector + SAM + prompts) **and** it contains `#163 ImageColorMatch+`, which consumes sg2's *output* and feeds sg4. sg3 straddles the sg2 boundary in both directions. |

Confirmed as stated: 132 nodes total, 24 bypassed, 0 muted **[F]**; 7 Image
Comparers (4 at root); 7 `UltralyticsDetectorProvider`, 4 `SAMLoader`, 4
`UpscaleModelLoader` **[F]**.

### The highest-priority audit item came back clean

`CLAUDE.md` flags subgraph-host `widgets_values` desync as "the single
highest-value thing to audit in this file". **It cannot occur in this file.** **[F]**

- All seven subgraph definitions have `"widgets": []`.
- All seven host nodes at root have `"widgets_values": []`.
- The only host with widget-typed inputs is `#619` (sg1): `value`, `seed`,
  `denoise`, `value_1` — and **all four carry links** (1369, 1373, 1504, 1376).

There are no promoted widget values stored anywhere, so there is nothing to shift
out of alignment. The `seed`/`control_after_generate` trap is likewise absent:
sg1's inner `#592 KSampler` holds a full, correctly-ordered 7-entry
`widgets_values`, with `control_after_generate` intact at index 1.

This is a genuine negative result, not an unchecked box. The *related* risk that
**is** present — wired inputs overriding widgets — is real and covered in
`AUDIT.md`.

---

## 1. True execution order

The root graph **looks cyclic** and its saved `order` field is therefore
misleading. `#619`(sg1) feeds `#647`(sg6) `positive`/`negative`, and `#647` feeds
`#619` `positive`/`negative`/`latent_image`/`denoise` **[F]**. Same pattern between
`#620`(sg2) and `#116` (LoRA stack), and between `#620` and `#621`(sg3).

These are not real cycles. They resolve once subgraphs are flattened, because
different *interior* nodes sit on each side of the boundary. The saved root
`order` (`#587`=10, `#619`=12) is an artifact of that apparent cycle and should
not be trusted.

Real data-flow order:

```
  sg1 loaders  ──►  root LoRA  ──►  sg6  ──►  sg1 sampling  ──►  sg0
  (#613 SDXL)      (#618)         (latent)   (gen+hires+face)    (hands+upscale)
                                                                      │
        SaveImage ◄── sg5 ◄── sg4 ◄── sg3 ◄── sg2 ◄────────────────────┘
         (#505)    (dead,   (eyes)  (colour) (face+mouth,
                  passthru)                   Z-Image)
```

Written out:

1. **`#613 CheckpointLoaderSimple`** (inside sg1) — the true root of the graph.
2. **`#618 Lora Loader Stack (rgthree)`** "Your SDXL LoRa" (root).
3. **sg6** — resolution, empty latent; ControlNet/IPAdapter bypassed passthrough.
4. **sg1** — base sample → hires fix → face pass → upscale → manual image filter.
5. **sg0** — hand detail, skin detail, second upscale.
6. **sg3 (loaders half)** — lips detector, SAM, mouth prompts.
7. **sg2** — face detail + mouth detail on Z-Image, with colour matching.
8. **sg3 (colormatch half)** — `#163`.
9. **sg4** — eyes.
10. **sg5** — fully bypassed, passes through. **[I]**
11. **`#505 SaveImage`** → `Instaraw/SDXL/Metadata/HasMetadata`.

---

## 2. Proposed stage names

The seven subgraphs are all named `"Dont touch!!!"` **[F]**. Proposed replacements,
ordered by execution:

| # | id | Proposed name | One line |
|---|---|---|---|
| 1 | sg6 | **Canvas & Routing** | Sets 896×1152, makes the empty latent; ControlNet/IPAdapter/depth rig present but dead. |
| 2 | sg1 | **Base Generator (SDXL)** | Checkpoint, PAG, base sample, DMD2 hires fix, face pass, Ultimate upscale, manual filter. |
| 3 | sg0 | **Hands, Skin & Second Upscale (SDXL)** | Hand detailer, skin-detail filter, a second UltimateSDUpscale. |
| 4 | sg3 | **Mouth Resources & Colour Reconcile** | Lips detector + SAM + mouth prompts for sg2; plus the third colour match. |
| 5 | sg2 | **Face & Mouth Detail (Z-Image)** | Z-Image UNET + Qwen CLIP; face detail, mouth detail, colour matched either side. |
| 6 | sg4 | **Eyes (FaceMesh crop/composite)** | Crops the face, upscales to 1920, MediaPipe mesh → eye SEGS, detail, composite back. |
| 7 | sg5 | **Anatomy Detailers — DEAD** | Pussy + nipple detailers on SDXL. All 11 nodes bypassed; wire passes through. |

Only two group titles exist anywhere in the file, both in sg6 **[F]**:
`#01 ControlNet` and `#02 Image to Image / Text to Image - Logic`. Those are the
author's own labels for sg6's two halves and support the "Canvas & Routing" name.

---

## 3. Root graph — 18 nodes

**Feeds:** nothing (top level). **Produces:** `#505 SaveImage`.

| Node | Type | Role |
|---|---|---|
| `#483` | `INSTARAW_RealityPromptGenerator` | Entry node. All 5 image inputs unlinked. See §10. |
| `#480` | `INSTARAW_PromptBatchPreview` | Preview of `#483`'s three list outputs. |
| `#481` | `PreviewAny` | Displays `#480`'s summary. |
| `#22` | `PreviewImage` | Shows sg1's image output. |
| `#104`,`#118`,`#164`,`#419` | `Image Comparer (rgthree)` | Dev instrumentation. |
| `#116` | `Lora Loader Stack (rgthree)` "Your ZIT LoRa" | **Z-Image** LoRA stack. All 4 slots `"None"`. |
| `#618` | `Lora Loader Stack (rgthree)` "Your SDXL LoRa" | **SDXL** LoRA stack. All 4 slots `"None"`. |
| `#505` | `SaveImage` | `Instaraw/SDXL/Metadata/HasMetadata`. |
| `#587`,`#619`,`#620`,`#621`,`#622`,`#623`,`#647` | subgraph hosts | sg0, sg1, sg2, sg3, sg4, sg5, sg6 respectively. |

Both LoRA stacks ship with every slot set to `"None"` **[F]** — they are empty
mount points for the buyer's own LoRAs, which matches step 5 of `INSTALL MODELS.txt`
("Upload your two LoRA SDXLs + ZIMAGE to …/models/loras").

**The two model families are separated cleanly by these two stacks**: `#618`
carries SDXL into sg6/sg1/sg0, `#116` carries Z-Image into sg2/sg4.

---

## 4. sg6 — **Canvas & Routing** (host `#647`, 22 nodes, 13 bypassed)

**In:** `vae`←sg1, `positive`←sg1 `#599`, `negative`←sg1 `#606`, `model`←`#618`.
**Out:** `output`(LATENT)→sg1, `FLOAT`→sg1 `denoise`, `positive`/`negative`→sg1,
`MODEL`→sg1 + sg0.

### Live path (9 nodes)

| Node | Type | Value |
|---|---|---|
| `#625` | `PrimitiveInt` "Width" | **896** |
| `#628` | `PrimitiveInt` "Height" | **1152** |
| `#635` | `EmptyLatentImage` | 896×1152×1; width/height **also wired** from `#625`/`#628` — widgets agree with links here **[F]** |
| `#636` | `INSTARAW_LatentSwitch` | boolean `false` → selects `input_false` = `#635` **[I]** |
| `#632` | `INSTARAW_ImageListFromBatch` | fed by bypassed `#630`; see AUDIT |
| `#627` | `PrimitiveFloat` | 1 |
| `#633` | `INSTARAW_FloatSwitch` | output unconnected — dead |
| `#629`,`#634` | `INSTARAW_BooleanBypass` | all outputs unconnected — UI-side controls **[?]** |

**So the graph is txt2img.** The img2img branch (`#631 VAEEncode`) is dead twice
over: the node is bypassed **and** `#636`'s switch is set to `false` **[F]**.

### Dead path (13 bypassed nodes)

`#639 ControlNetLoader` (`controlnet-union-sdxl-promax.safetensors`) →
`#641 SetUnionControlNetType` (`depth`) → `#638 ControlNetApplyAdvanced`
(0.6 / 0 / 0.4); `#626`,`#630 INSTARAW_ImageResizeFill`; `#640
DepthAnythingV2Preprocessor` (`depth_anything_v2_vitl.pth`, 896);
`#642 PreviewImage` "DepthMap"; `#646 LoadImage` (`ComfyUI_00101_ (1).png`);
`#643 IPAdapter` + `#644 IPAdapterUnifiedLoader` (`PLUS FACE (portraits)`);
`#637 PrimitiveFloat` (0.5); `#645 INSTARAW_BrandingNode` "Powered by 🍑".

**Bypass passthrough is clean for the two that matter [I]:**
- `#638` bypassed → `positive`/`negative` pass straight from sg6's inputs to its
  outputs, so sg1's own `#599`/`#606` conditioning reaches sg1's KSampler unmodified.
- `#644`→`#643` bypassed → `MODEL` passes from sg6's `model` input to its output,
  so `#618`'s SDXL model reaches sg1 and sg0 unmodified.

**`#637` is the exception and it is not clean** — it is a `PrimitiveFloat` with no
inputs, so bypassing it leaves nothing to pass through. Its output is sg6's
`FLOAT`, which is sg1's `denoise`. See `AUDIT.md` A2.

---

## 5. sg1 — **Base Generator (SDXL)** (host `#619`, 28 nodes, 0 bypassed)

The largest stage and the one that does the real generation.

**In:** `value`(pos prompt)←`#483`, `value_1`(neg)←`#483`, `seed`←`#483`,
`positive`/`negative`/`latent_image`/`denoise`←sg6, `clip`←`#618`,
`model`←sg6, `model_1`←`#618`.
**Out:** `CONDITIONING`(`#599`)→sg6, `IMAGE`→root+sg0, `CONDITIONING_1`(`#606`)→sg6,
`MODEL`/`CLIP`/`VAE` (all raw from `#613`)→sg0, sg5, sg6.

### Loaders
- `#613 CheckpointLoaderSimple` — **`SDXLNSFW.safetensors`**. Feeds MODEL/CLIP/VAE
  to the whole graph.
- `#610 LoraLoader` — `dmd2_sdxl_4step_lora_fp16.safetensors` @ 1.0/1.0, feeding
  **only** `#600`.
- `#611 UltralyticsDetectorProvider` — `bbox/face_yolov8m.pt`.
- `#612 UpscaleModelLoader` — `4x-UltraSharpV2.pth`.
- `#615 UpscaleModelLoader` — `4x_NMKD-Superscale-SP_178000_G.pth`.

### Chain

| Step | Node | Settings |
|---|---|---|
| Model prep | `#608 ModelSamplingDiscrete` → `#609 PerturbedAttentionGuidance` | `eps`, zsnr `false`; PAG scale **1.0** |
| Prompts | `#590`/`#605 PrimitiveStringMultiline` → `#599`/`#606 CLIPTextEncode` | pos from `#483`; neg default `"bad quality, worst quality, low quality,"` |
| **Base sample** | `#592 KSampler` | **40 steps, cfg 4, `dpmpp_2m_sde`/`karras`**, seed wired from `#483` |
| Decode | `#591 VAEDecode` | |
| **Hires fix** | `#593 ImageUpscaleWithModel` (NMKD 4x) → `#595 ImageScaleBy` (lanczos **0.4**) → `#594 VAEEncode` | net **1.6×** → ≈1434×1843 **[I, arithmetic]** |
| **Hires sample** | `#600 KSamplerAdvanced` | **steps 70, start 66 → 4 effective steps**, cfg **1**, `lcm`/`normal`, on the **DMD2** model `#610` |
| Decode | `#596 VAEDecode` | |
| **Face pass** | `#598 ToDetailerPipeSDXL` → `#607 FaceDetailerPipe` | guide/max 1280, 20 steps, cfg 3, denoise **0.45**, bbox_dilation 30, `face_yolov8m` |
| **Round trip** | `#597 VAEEncode` → `#616 VAEDecode` | **nothing between them — pure no-op, see AUDIT A1** |
| **Upscale** | `#617 UltimateSDUpscale` | 1.25×, 25 steps, cfg 4.5, denoise 0.25, tile 896×1152, `4x-UltraSharpV2`, on `#618`'s plain SDXL model |
| **Manual filter** | `#602 BatchFromImageList` → `#603 INSTARAW_ImageFilter` → `#601 ImageListFromBatch` | timeout 600, `"send none"`, `"Run selector normally"` |

`#614 PrimitiveBoolean` "ENABLE IMAGE FILTERING?" = `true` → `#604
INSTARAW_BooleanBypass`, whose four outputs are all unconnected. **[?]** — this only
makes sense as a client-side bypass toggle for `#603`.

**Three distinct sampler configurations run here** on three different models:
plain SDXL+PAG (`#592`), DMD2 4-step (`#600`), plain SDXL from the LoRA stack
(`#617`). `#598` builds its detailer pipe from `#609` (PAG). That is four separate
model variants resident in one stage.

---

## 6. sg0 — **Hands, Skin & Second Upscale (SDXL)** (host `#587`, 15 nodes, 0 bypassed)

**In:** `image_b`←sg1 IMAGE, `clip`←sg1 CLIP (raw), `clip_1`←`#618` CLIP,
`vae`←sg1 VAE, `model`←sg6 MODEL, `model_1`←sg1 MODEL (raw).
**Out:** `IMAGE`(`#87`)→sg2 `reference`; `IMAGE_1`(`#98`)→sg2 `image`.

| Node | Type | Settings |
|---|---|---|
| `#89` | `UltralyticsDetectorProvider` | `bbox/hand_yolov8s.pt` |
| `#88` | `SAMLoader` | `sam_vit_b_01ec64.pth`, AUTO |
| `#93` | `CLIPTextEncode` "Hand Prompt" | `"Detailed hand, detailed fingers, detailed fingernails, girl hand, natural skin texture,"` |
| `#506` | `CLIPTextEncode` "Hand Prompt" | **empty — this is the negative**, mistitled |
| `#92` | `FaceDetailer` "HandDetailer" | 1024/1024, 30 steps, cfg 3, denoise **0.42**, `vertical-2` hint, cycle **2** |
| `#90`→`#91` | `UpscaleModelLoader`+`ImageUpscaleWithModel` | `x1_ITF_SkinDiffDetail_Lite_v1.pth` (1× detail filter) |
| `#87` | `ImageBlend` | **blend_factor 1.0, `normal`** — see AUDIT A3 |
| `#97` | `LoraLoader` | `dmd2_sdxl_4step_lora_fp16.safetensors` (second copy) |
| `#100` | `UpscaleModelLoader` | `4x-UltraSharpV2.pth` (second copy) |
| `#99` | `GetImageSize` | of `#87` → wires `#98` tile size |
| `#508`/`#509` | `CLIPTextEncode` | `"Detailed skin, high quality"` / empty |
| `#98` | `UltimateSDUpscale` | **1.5×, 2 steps, cfg 1, `lcm`/`sgm_uniform`, denoise 0.08** |
| `#96` | `Image Comparer (rgthree)` | instrumentation |

Two things stand out and are carried into `AUDIT.md`:
- `#98`'s `tile_width`/`tile_height` widgets read **512/512** but both slots are
  **wired** from `#99 GetImageSize` **[F]**. The real tile size is the full image
  dimension, so it scales with resolution.
- `#98` runs **2 steps at denoise 0.08**. Whether that is a meaningful refinement
  or a very expensive no-op is a pod question, not a static one.

---

## 7. sg3 — **Mouth Resources & Colour Reconcile** (host `#621`, 5 nodes, 0 bypassed)

**In:** `image`←sg2 `image` out, `reference`←sg2 `IMAGE_1` out, `clip`←sg2 CLIP.
**Out:** `IMAGE`→sg4; `CONDITIONING`/`CONDITIONING_1`→sg2; `SAM_MODEL`→sg2;
`BBOX_DETECTOR`→sg2.

| Node | Type | Value |
|---|---|---|
| `#160` | `SAMLoader` | `sam_vit_b_01ec64.pth`, AUTO |
| `#161` | `UltralyticsDetectorProvider` | **`bbox/lips_v1.pt`** |
| `#166` | `CLIPTextEncode` "Mouth Detailer Prompt" | `"realistic detailed mouth"` |
| `#167` | `CLIPTextEncode` "Mouth Detailer Negative Prompt" | empty |
| `#163` | `ImageColorMatch+` | LAB, strength 1, `auto`, 0 |

**This is not one stage, it is two half-stages sharing a box.** `#160`/`#161`/`#166`/`#167`
are *resources consumed by sg2*. `#163` is a *post-process on sg2's output* that
feeds sg4. That is why the sg2↔sg3 boundary looks cyclic at host level.

`#166`/`#167` encode with sg2's Qwen CLIP, so the mouth prompts are Z-Image
conditioning **[F]** — correct, since the mouth detailer `#165` runs on Z-Image.

---

## 8. sg2 — **Face & Mouth Detail (Z-Image)** (host `#620`, 12 nodes, 0 bypassed)

**In:** `image`←sg0 `#98`, `reference`←sg0 `#87`, `model`←`#116`, `clip`←`#116`,
`positive`/`negative`←sg3, `bbox_detector`/`sam_model_opt`←sg3.
**Out:** `IMAGE`(`#137`)→sg3 `reference`; `MODEL`/`CLIP`/`VAE`→`#116`, sg4;
`IMAGE_1`(`#111`)→sg3 `reference` + comparers; `image`(`#165`)→sg3 `image`.

### The second model family, identified

| Node | Type | File |
|---|---|---|
| `#113` | `UNETLoader` | **`zimage.safetensors`**, `default` |
| `#110` | `CLIPLoader` | **`qwen.safetensors`**, type **`lumina2`**, `default` |
| `#109` | `VAELoader` | **`ae.safetensors`** |

`#113`'s MODEL output goes **only** to sg2's own output, not to either detailer
**[F]**. Both detailers take `model` from sg2's *input*, which is `#116` "Your ZIT
LoRa" at root, which in turn is fed from sg2's output. Flattened, the chain is
`#113 → #116 → #114/#165` — the Z-Image LoRA stack sits in the middle. Same for CLIP
via `#110`.

### Chain

`#137 ImageColorMatch+` (image = sg0's upscale, reference = sg0's pre-upscale)
→ `#114 FaceDetailer` → `#111 ImageColorMatch+` (back to `#137`)
→ `#165 FaceDetailer` "Mouth Detailer" → out.

| Node | Settings |
|---|---|
| `#107` `UltralyticsDetectorProvider` | `bbox/face_yolov8m.pt` (also supplies `segm_detector_opt`) |
| `#108` `SAMLoader` | `sam_vit_b_01ec64.pth` |
| `#106` "Face Detailer Prompt" | **`"TRIGGER, PROMT FOR YOUR MODEL"`** — unfilled placeholder, see AUDIT A4 |
| `#105` "Face Detailer Negative Prompt" | `"deformed, ugly, blurry, bad anatomy, disfigured, extra eyes, cropped face, out of frame, deformed piercing, bad piercing, watermark, text"` |
| `#114` `FaceDetailer` | 1024/1024, 30 steps, cfg 1, `euler_ancestral`/`kl_optimal`, denoise **0.8**, feather 18 |
| `#165` `FaceDetailer` "Mouth Detailer" | 1808/1808, 8 steps, cfg 1, `euler_ancestral`/`kl_optimal`, denoise **0.35**, sam_threshold 0.6 |
| `#583` `DetailerPipeToBasicPipe` | **fully orphaned** — no input link, no output links, not bypassed |

`#105`/`#106` encode with `#110`'s CLIP **directly**, bypassing the `#116` LoRA
stack, while `#114` receives the LoRA'd CLIP on its `clip` slot **[F]**. So a
buyer's Z-Image LoRA affects the detailer's internal re-encode but not the
prompts as encoded. **[I]**

**Three `ImageColorMatch+` passes** exist across sg2+sg3 (`#137`, `#111`, `#163`),
one before the face pass and one after each detail pass. **[I]** this is
compensating for colour drift when a Z-Image detailer paints into an SDXL image.

---

## 9. sg4 — **Eyes** (host `#622`, 21 nodes, 0 bypassed)

**In:** `clip`←sg2 CLIP, `vae`←sg2 VAE, `images`←sg3 `#163`, `model`←sg2 MODEL.
**Out:** `IMAGE`(`#418`)→sg5→**SaveImage**; `IMAGE_1`(`#431`)→comparers.

Runs on **Z-Image**, like sg2 **[F]** — `model`/`clip`/`vae` all come from sg2.

Crop → upscale → mesh → detail → shrink → composite:

| Step | Node | Detail |
|---|---|---|
| 1 | `#431 INSTARAW_ImageListFromBatch` | splits the incoming batch |
| 2 | `#426` + `#424 BboxDetectorSEGS` | `bbox/face_yolov8m.pt`; threshold 0.6, dilation 10, crop_factor 3 |
| 3 | `#407 SegsToCombinedMask` → `#403 MaskBoundingBox+` | face bbox → x/y/w/h |
| 4 | `#404 ImageCrop` | crops the face; **all four widgets overridden by links** from `#403` |
| 5 | `#414 ImageResize+` | **upscales crop to 1920**, lanczos, keep proportion |
| 6 | `#415 MediaPipe-FaceMeshPreprocessor` | max_faces 10, conf 0.2; **`resolution` widget 512 overridden by link** = 1920 |
| 7 | `#410 MediaPipeFaceMeshToSEGS` → `#402` → `#408 MaskToSEGS` | eye/iris mesh regions → SEGS |
| 8 | `#406 DetailerForEachDebug` | 1920/1920, 8 steps, cfg 1, `euler`/`beta`, denoise **0.42**, on `#413` LoRA stack (all `"None"`) |
| 9 | `#401 INSTARAW_ImageResizeFill` | **shrinks back**; width/height wired from `#400 GetImageSize` |
| 10 | `#418 ImageCompositeMasked` | pastes back at `#403`'s x/y — **`mask` input unconnected** |

`#395`/`#396 PreviewImage` are dev instrumentation.

`#418`'s unconnected `mask` **[F]** means the composite is a hard rectangular paste
with no feathering **[I]**. Every other detailer in this graph uses Impact's
feathered masking; this one does not.

---

## 10. sg5 — **Anatomy Detailers — DEAD** (host `#623`, 11 nodes, **11 bypassed**)

**In:** `clip`←sg1 CLIP, `image`←sg4, `model`←sg1 MODEL, `vae`←sg1 VAE.
**Out:** `image`→**`#505 SaveImage`**.

Runs on **SDXL** (sg1's raw checkpoint outputs), not Z-Image **[F]**.

| Node | Type | Value |
|---|---|---|
| `#246` | `UltralyticsDetectorProvider` | `bbox/pussyV2.pt` |
| `#171` | `UltralyticsDetectorProvider` | `bbox/nipple.pt` |
| `#249` | `SAMLoader` | `sam_vit_b_01ec64.pth` |
| `#174` | `LoraLoader` | `DetailedNipples.safetensors` @ 1.0/1.0 |
| `#240` | `CLIPTextEncode` "Pussy Detailer Prompt" | populated |
| `#242` | `CLIPTextEncode` "Nipples Detailer Prompt" | `"Detailed nipples, breasts, natural skin texture, details."` |
| `#276` | `CLIPTextEncode` | empty, shared negative |
| `#256` | `FaceDetailer` "Pussy Detailer" | 1808/1808, 30 steps, cfg 3, denoise 0.42, bbox_dilation **104** |
| `#176` | `FaceDetailer` "Nipples Detailer" | 1808/1808, 30 steps, cfg 3, denoise 0.42, feather **80** |
| `#237`,`#241` | `Image Comparer (rgthree)` | instrumentation |

Live chain when enabled: `#256` → `#176` → out.
Bypassed: `#176`'s `image` output resolves back through `#256` to sg5's `image`
input **[I]**, so **the final saved image is sg4's `#418` output**.

This is the only stage that is entirely switched off, and it is switched off on
the last wire before `SaveImage`.

---

## 11. The entry node `#483 INSTARAW_RealityPromptGenerator`

**[F]** from the file:
- `order: 0`; all five image inputs (`images`, `images2`, `images3`, `images4`,
  `character_image`) have **no link**.
- `widgets_values: ["", "", "", "[]", "[]", false]`
- Outputs: `prompt_list_positive` → `#480` + `#619`(sg1 `value`);
  `prompt_list_negative` → `#480` + `#619`(sg1 `value_1`);
  `seed_list` → `#480` + `#619`(sg1 `seed`);
  `generation_count` and `resolved_mode` → **unconnected**.

So this node supplies the positive prompt, the negative prompt, and the seed for
the entire pipeline. Nothing else feeds sg1's prompts — `#590`/`#605` inside sg1
have their `value` slots wired from the subgraph input **[F]**, so their own widget
strings (`""` and the default negative) are overridden when a link is present.

The two `"[]"` widget values are JSON-empty arrays **[I]**, consistent with
list-shaped state that is populated client-side rather than typed in.

**Interpretation is deferred to `AUDIT.md` A5 / `QUESTIONS.md` Q1** — resolving
whether the unconnected image inputs are a defect or the intended state requires
the pack source, which is being read separately.

---

## 12. Resolution ladder **[I — arithmetic from widget values, not measured]**

| Stage | Operation | Result |
|---|---|---|
| sg6 `#635` | EmptyLatentImage | **896 × 1152** |
| sg1 `#593` | 4× NMKD | 3584 × 4608 |
| sg1 `#595` | ×0.4 lanczos | ≈1434 × 1843 |
| sg1 `#617` | UltimateSDUpscale ×1.25 | ≈1792 × 2304 |
| sg0 `#98` | UltimateSDUpscale ×1.5 | ≈**2688 × 3456** |

sg2, sg3, sg4 and sg5 do not resize the full frame, so ≈2688×3456 (~9.3 MP) is
the saved size. Rounding inside `ImageScaleBy` and `UltimateSDUpscale` may shift
these by a few pixels; **the pod session should read the actual output dimensions
rather than trusting this table**.

Note the 3584×4608 intermediate at step 2 — a 16.5 MP RGB tensor materialised
only to be scaled down to 8.7% of its pixel count. See `PROPOSALS.md` P2.

---

## 13. Loader duplication — which are genuinely the same file

**[F]** from widget values:

| File | Loaded by | Distinct loads |
|---|---|---|
| `sam_vit_b_01ec64.pth` | `#88`(sg0), `#108`(sg2), `#160`(sg3), `#249`(sg5, bypassed) | **4 → 3 live** |
| `bbox/face_yolov8m.pt` | `#611`(sg1), `#107`(sg2), `#426`(sg4) | **3** |
| `4x-UltraSharpV2.pth` | `#612`(sg1), `#100`(sg0) | **2** |
| `dmd2_sdxl_4step_lora_fp16.safetensors` | `#610`(sg1), `#97`(sg0) | **2** |
| `bbox/hand_yolov8s.pt` | `#89`(sg0) | 1 |
| `bbox/lips_v1.pt` | `#161`(sg3) | 1 |
| `4x_NMKD-Superscale-SP_178000_G.pth` | `#615`(sg1) | 1 |
| `x1_ITF_SkinDiffDetail_Lite_v1.pth` | `#90`(sg0) | 1 |
| `bbox/nipple.pt`, `bbox/pussyV2.pt` | `#171`, `#246` (sg5, bypassed) | 2 dead |

Seven `UltralyticsDetectorProvider` = 3× face_yolov8m + hand + lips + nipple +
pussyV2. **[I]** ComfyUI caches loaders by class + inputs, so identical loaders
are likely deduplicated at execution; the cost of duplication is graph clarity
and the risk of them drifting apart, more than VRAM. Confirming that is a pod
task (`PROPOSALS.md` P15).

---

## 14. Node packs in use **[F]** — from `properties.cnr_id`

| `cnr_id` | Nodes | `ver` values seen |
|---|---|---|
| `comfy-core` | 63 | 0.3.15 … **0.3.70**, plus 0.15.1 (6), 0.17.2, 0.3.44, 0.3.60, 0.3.62, 0.3.68 |
| `comfyui-impact-pack` | 18 | `8.8.1`, `8.25.1`, `8.28.2`, `cd34cfd…` |
| `comfyui-impact-subpack` | 7 | `1.2.9`, `1.3.2`, `1.3.5` |
| `rgthree-comfy` | 10 | `1.0.2508012353`, `1.0.2510052058` |
| `comfyui_essentials` | 5 | `33ff89f…`, `9d9f4be…` |
| `comfyui_controlnet_aux` | 2 | `1.0.6`, `12f3564…` |
| `comfyui_ipadapter_plus` | 2 | `2.0.0` |
| `comfyui_ultimatesdupscale` | 2 | `1.1.2`, `1.3.3` |
| `instara-io/ComfyUI_INSTARAW` | 1 (`#645`) | `12afb90…` |
| *(no cnr_id)* | 15 | all `INSTARAW_*` except `#645` |

The spread of `ver` values is a record of when each node was last placed, not a
requirement. The **highest** core version present is `0.3.70` (`#614
PrimitiveBoolean`), which sets the practical floor. See `SETUP.md`.

---

## 15. What I am not sure about

1. **[?]** `INSTARAW_BooleanBypass` (`#604`, `#629`, `#634`) — every instance has
   all four outputs unconnected. They only make sense as client-side controls that
   toggle other nodes' bypass state (`js/boolean_bypass.js` and
   `js/group_bypass_detector.js` exist in the pack). Not confirmed from source here.
2. **[?]** Whether `INSTARAW_LatentSwitch` (`#636`) declares lazy inputs. If it
   does not, its unselected `input_true` branch is still evaluated — see AUDIT A6.
3. **[?]** `CLIPLoader` type `lumina2` for a Qwen text encoder driving Z-Image. I
   cannot check ComfyUI's supported type list from here.
4. **[?]** Exact bypass-resolution behaviour for `#637` (AUDIT A2) — whether the
   downstream widget default is used or the prompt errors.
5. **[?]** Whether identical loaders are deduplicated at runtime (§13).
6. **[?]** The final output dimensions (§12) are arithmetic, not measured.
