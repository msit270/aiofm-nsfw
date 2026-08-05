# WS4 — the five known-but-unfixed defects

Owner: WS4. Branch `fix/run2`.
Authoritative file: `/workspace/nsfw-fix/OFMTech-NSFW/OFMTech_NSFW.json`.

**Note on node ids and file size in Part 1.** The structural analysis below was
done against the file as it stood at the start of my session. WS1 then landed
`41e77f9`, which restructured subgraph "2. Base Generator (SDXL)"'s IO and
several root links. I re-verified every node id, link id and widget index I rely
on against the post-`41e77f9` file before touching anything, and captured API
graphs from both: they are **identical across all 88 nodes and every input**, so
nothing in Part 1 is invalidated. My own two commits then took it to 107 nodes.

Every claim below is traceable to a node id, a link id, or a file:line. Where I
am inferring, it is marked **[I]**. Where I have not verified, it says so.

Every claim below is traceable to a node id, a link id, or a file:line. Where I
am inferring, it is marked **[I]**. Where I have not verified, it says so.

---

## Verdict table

| | Defect as stated in STATE.md | My verdict | Action |
|---|---|---|---|
| D1 | `#597`→`#616` pure VAE round-trip | **Confirmed** | Output-changing. A/B, then ship |
| D2 | `#106` placeholder at denoise 0.8 | **Confirmed, but it is documented buyer-facing content** | Do not change text. Evidence render + logged question |
| D3 | Face detailed twice (0.45 then 0.80) | **Confirmed** | Ablation A/B only — quality call is the user's |
| D4 | `#600` reseeds every run | **FALSE for the current file.** Real residual defect is `#592` | Ship the `#592` fix (provably inert) |
| D5 | ControlNet path mis-wired | **Moot — the path no longer exists** | No action. Documented |

---

## Baseline facts I established first

These correct several stale claims in CLAUDE.md, STATE.md, AUDIT.md and
QUESTIONS.md.

**Node census (current file).** 109 nodes total, not 132:

| container | nodes |
|---|---|
| ROOT | 17 |
| 1. Canvas & Routing | 4 |
| 2. Base Generator (SDXL) | 28 |
| 3. Hands, Skin & Second Upscale (SDXL) | 14 |
| 4. Mouth Resources & Colour Reconcile | 5 |
| 5. Face & Mouth Detail (Z-Image) | 12 |
| 6. Eyes (FaceMesh crop/composite) | 18 |
| 7. Anatomy Detailers - DISABLED | 11 |

**Exactly one node is bypassed or muted in the whole file**: root `#623`, the
host for "7. Anatomy Detailers - DISABLED", `mode: 4`. CLAUDE.md's "24 bypassed
nodes" and "sg6 has 13 bypassed" are stale by a whole graph revision.

**The seven subgraphs are already named.** CLAUDE.md's core complaint ("all
seven stages are named `Dont touch!!!`") no longer applies to this file.

---

## D1 — `#597 VAEEncode` → `#616 VAEDecode` with nothing between · **CONFIRMED**

### Evidence

Inside subgraph `3ff96466-…` ("2. Base Generator (SDXL)"), from the link list:

```
1232:   607[0] -> 597[0]   IMAGE     (FaceDetailerPipe.image -> VAEEncode.pixels)
1233:   613[2] -> 597[1]   VAE
1260:   597[0] -> 616[0]   LATENT    (VAEEncode -> VAEDecode.samples)
1261:   613[2] -> 616[1]   VAE
1262:   616[0] -> 617[0]   IMAGE     (VAEDecode -> UltimateSDUpscale.image)
```

`#597.outputs[0].links == [1260]` — link 1260 is its **only** consumer.
`#616.outputs[0].links == [1262]` — its only consumer is `#617.image`.
`#597` and `#616` both take `vae` from `#613` slot 2 (the same
`CheckpointLoaderSimple`, `SDXLNSFW.safetensors`). Nothing else touches either
node. `#617 UltimateSDUpscale.image` is an `IMAGE` input, so `#607.image` can
feed it directly.

### Resolution at that point in the chain — I re-derived it rather than trusting "~1434x1843"

- `#635 EmptyLatentImage` (subgraph "1. Canvas & Routing"), driven by `#625
  Width = 896` and `#628 Height = 1152` (both `PrimitiveInt`, both wired to
  `#635` via links 1476/1477). → base **896x1152**.
- `#593 ImageUpscaleWithModel` with `#615` = `4x_NMKD-Superscale-SP_178000_G.pth`
  → 3584x4608 **[I]** (assumes the model's scale is 4, which its name states;
  not verified by loading it).
- `#595 ImageScaleBy`, `widgets_values: ["lanczos", 0.4]`. `nodes.py:1903-1904`:
  `width = round(samples.shape[3] * scale_by)` → `round(1433.6)=1434`,
  `round(1843.2)=1843`.
- `#594 VAEEncode` → `comfy/sd.py:1008` calls `vae_encode_crop_pixels`, which at
  `sd.py:847-857` crops each spatial dim down to a multiple of the encoder's
  spacial compression (8 for the SDXL VAE): **1434→1432, 1843→1840**.
- So `#596 VAEDecode`, `#607`, `#597`, `#616` all operate at **1432x1840**, not
  1434x1843. STATE.md and AUDIT.md A1 both say ~1434x1843; that is the size
  *before* `#594`'s crop. Minor, but it means removing `#597`/`#616` changes
  **no** resolution — `#594` already did the rounding. The round-trip is purely
  lossy, not resizing.

### Verdict

Real. Costs one full VAE encode + one full VAE decode at 1432x1840 on every
render and applies an extra lossy VAE round-trip to every image.

**Not provably inert on pixels** — a VAE round-trip is lossy. Requires an A/B.
Graph-diff proves the change touches nothing but the two deleted nodes.

---

## D2 — `#106` placeholder driving the face pass at denoise 0.8 · **CONFIRMED, but deliberate**

### Evidence

`#106 CLIPTextEncode`, title `"Face Detailer Prompt"`, in subgraph
`d6db378b-…` ("5. Face & Mouth Detail (Z-Image)"):

```
widgets_values: ["TRIGGER, PROMPT FOR YOUR MODEL"]
inputs[0] clip  link=192
outputs[0] CONDITIONING links=[199]   ->  #114 FaceDetailer.positive
```

**Spelling: the file says `PROMPT`, not `PROMT`.** `grep -c "PROMT"` on the
workflow returns **0**. `AUDIT.md` A4 quotes `"TRIGGER, PROMT FOR YOUR MODEL"`
and calls `PROMT` "the typo"; `QUESTIONS.md` Q2 repeats it. **Both documents are
wrong on this point.** There is no typo in the file.

There are exactly two occurrences of the string `TRIGGER` in the workflow:
- `/definitions/subgraphs[2]/nodes[6]/widgets_values[0]` → `#106`.
- `/nodes[14]/widgets_values[0]` → root `#649`, a `MarkdownNote`.

### The MarkdownNote is what settles this

Root `#649` (`MarkdownNote`), verbatim:

> ## 3 · One thing you must fill in
> Open **5. Face & Mouth Detail**, find *Face Detailer Prompt*, and replace
> `TRIGGER, PROMPT FOR YOUR MODEL` with your LoRA's trigger word and a short
> description of your character. That node drives the single most expensive
> pass in the workflow.

So the placeholder is **documented, intentional, buyer-facing template text**,
and the note quotes it with the same spelling the node carries. Changing the
text would desynchronise the node from its own instructions.

### Denoise confirmed independently

`#114 FaceDetailer` `widgets_values`:
`[1024, true, 1024, 1111111, "fixed", 30, 1, "euler_ancestral", "kl_optimal", 0.8, 18, true, true, 0.5, 10, 3, "center-1", 0, 0.93, 0, 0.7, "False", 10, "", 1, false, 20, false, false]`
— 29 entries.

Mapped against `ComfyUI-Impact-Pack/modules/impact/impact_pack.py:735-786`
(`FaceDetailer.INPUT_TYPES`), skipping the 8 link-typed inputs (`image`, `model`,
`clip`, `vae`, `positive`, `negative`, `bbox_detector`, `sam_model_opt`,
`segm_detector_opt`, `detailer_hook`, `scheduler_func_opt`) and adding the one
synthetic `control_after_generate` companion after `seed`, the widget list is
exactly 29 long and index **9 is `denoise` = 0.80**. The count matching exactly
is the check that there is no widget desync on this node.

### The `clip` sub-question — confirmed, and it is broader than QUESTIONS.md Q2 says

`#106.clip` is link **192**, and inside sg5 link 192 is `110[0] -> 106[0]`.
`#110` is the raw `CLIPLoader` (`qwen.safetensors`, type `lumina2`). Same for
`#105` via link 191.

Meanwhile `#114.clip` is link **209** = `-10[3]`, i.e. the subgraph's `clip`
input, fed from root link 1401 which originates at `#116` "Your ZIT LoRa".

But `#114`'s `clip` is **dead weight**: `ComfyUI-Impact-Pack/modules/impact/core.py:267`
reads

```python
if wildcard_opt is not None and wildcard_opt != "":
```

and only then re-encodes using `clip`. `#114`'s `wildcard` widget (index 23) is
`""`, and `#598 ToDetailerPipeSDXL`'s wildcard (`widgets_values[0]`) is also
`""`. So the LoRA'd CLIP never gets used for anything.

**The pattern is graph-wide, not local to `#106`.** Every Z-Image text encode
takes the raw `#110` CLIP:

| encode | stage | clip link | source |
|---|---|---|---|
| `#105`, `#106` face | sg5 | 191, 192 | `#110` raw |
| `#166`, `#167` mouth | sg4 | 1410, 1411 | sg4 input ← root 1423 ← `#620[2]` = `#110` raw |
| `#394`, `#398` eyes | sg6 | 1413, 1412 | sg6 input ← root 1429 ← `#620[2]` = `#110` raw |

whereas every Z-Image **MODEL** input is LoRA'd (`#114`/`#165` via `-10[2]` ←
root 1400 ← `#116[0]`; `#406` via `-10[3]` ← root 1432 ← `#116[0]`).

So STATE.md's "hidden third LoRA stack … Fixed" repaired the **model** path to
the eye pass. The **CLIP** path was not repaired anywhere. A buyer's Z-Image
LoRA reaches the UNet of all three Z-Image passes and the text encoder of none.

### Verdict and action — I changed nothing, and here is why

1. **The text is the user's content**, and root `#649` already instructs the
   buyer to replace it. Overwriting it would break the note.
2. **The CLIP rewire is inert at shipped defaults but touches the riskiest
   structure in the file.** `rgthree-comfy/py/lora_stack.py:35-45`:
   `load_lora` returns `(model, clip)` untouched when all four slots are
   `"None"` — which is the shipped state of `#116`
   (`["None", 1, "None", 0.9, "None", 0.9, "None", 1]`). So for a first-time
   buyer the rewire is a guaranteed no-op. Its only effect appears once a buyer
   loads a Z-Image LoRA with a CLIP component.
   Against that zero first-run benefit: rewiring `#105`/`#106` to the subgraph
   input means editing the `linkIds` array on a subgraph IO slot.
   `litegraph/src/subgraph/SubgraphOutput.ts` maintains `linkIds` explicitly and
   `SubgraphOutput.disconnect()` carries the comment *"should never have more
   than one connection"* — this array is load-bearing state, and a desynced IO
   `linkIds` array is the same class of corruption as the current shipped
   blocker. Taking that risk for zero default-configuration benefit is the wrong
   trade for a first-time buyer.

**Logged as a question with the exact patch** in `WS4-questions.md` Q-A. The
render evidence for what the placeholder does is in the A/B section below.

---

## D3 — the face is detailed twice · **CONFIRMED**

### Evidence, both figures read from the file

**Pass 1 — `#607 FaceDetailerPipe`**, subgraph "2. Base Generator (SDXL)":
```
widgets_values: [1280, true, 1280, 100097229797074, "fixed", 20, 3,
                 "dpmpp_2m_sde", "karras", 0.45, 10, true, true, 0.5, 30, 3,
                 "center-1", 0, 0.93, 0, 0.7, "False", 10, 0, 1, false, 20,
                 false, false]
```
29 entries. Mapped against `impact_pack.py:1636-1680` (`FaceDetailerPipe.INPUT_TYPES`)
— 2 link inputs (`image`, `detailer_pipe`), 24 required widgets + 1 synthetic
`control_after_generate`, 4 optional widgets (`scheduler_func_opt` is a link) =
**29**. Index **9 is `denoise` = 0.45**. Confirmed independently of AUDIT.md.

Its detector is `#611 UltralyticsDetectorProvider` = `bbox/face_yolov8m.pt`,
reaching `#607` through `#598 ToDetailerPipeSDXL` (link 1241 → `#598[9]`, then
link 1256 → `#607.detailer_pipe`).

**Pass 2 — `#114 FaceDetailer`**, subgraph "5. Face & Mouth Detail (Z-Image)":
denoise **0.80** (above). Its detector is `#107 UltralyticsDetectorProvider` =
`bbox/face_yolov8m.pt` — **the same checkpoint**.

So: same detector file, same target region, SDXL at 0.45 then Z-Image at 0.80.

### The other three detailers, for the record

| node | stage | detector | denoise | guide/max |
|---|---|---|---|---|
| `#92 FaceDetailer` "HandDetailer" | sg3 | `bbox/hand_yolov8s.pt` | 0.42 | 1024/1024 |
| `#165 FaceDetailer` "Mouth Detailer" | sg5 | `bbox/lips_v1.pt` | 0.35 | 1808/1808 |
| `#406 DetailerForEachDebug` | sg6 | MediaPipe FaceMesh + `face_yolov8m` | 0.42 | 1920/1920 |

All read from `widgets_values` index 9 (index 9 for `DetailerForEachDebug` too —
`#406`'s array is 19 long, consistent with `DetailerForEach`'s shorter widget
list). These match the figures in the brief.

### Verdict

Real and structural. Whether pass 1 is wasted is a **quality judgement I am not
allowed to make and cannot make**. The deliverable is the ablation A/B plus
timing, below.

---

## D4 — "`#600` reseeds itself every run" · **STATE.md IS WRONG**

This was the most involved of the five. Three separate questions had to be
settled.

### 1. What `#600`'s widgets actually say

`#600 KSamplerAdvanced`, subgraph "2. Base Generator (SDXL)":
```
inputs: model(link 1244), positive(1245), negative(1246), latent_image(1247)
widgets_values: ["enable", 578361683541099, "fixed", 70, 1, "lcm", "normal", 66, 1000, "disable"]
```

**All four inputs are link-typed; none is a widget-input.** So there is no
possibility of widget-index desync here, and the array maps 1:1 onto
`nodes.py:1595-1613` (`KSamplerAdvanced.INPUT_TYPES`) plus the synthetic
`control_after_generate` that `noise_seed`'s `{"control_after_generate": True}`
(nodes.py:1601) creates:

| idx | param | value |
|---|---|---|
| 0 | add_noise | "enable" |
| 1 | noise_seed | 578361683541099 |
| 2 | **control_after_generate** | **"fixed"** |
| 3 | steps | 70 |
| 4 | cfg | 1 |
| 5 | sampler_name | "lcm" |
| 6 | scheduler | "normal" |
| 7 | start_at_step | 66 |
| 8 | end_at_step | 1000 |
| 9 | return_with_leftover_noise | "disable" |

10 entries, 10 slots. **`#600` is `"fixed"`.** `AUDIT.md` A21's table records it
as `"randomize"`. Either it was changed on the destroyed pod, or A21 misread it —
I cannot distinguish, because the file has only ever been committed once
(`4d8a9ce recovered shipping state`) and there is no earlier revision in git to
diff against. Either way, **for the file that ships today, STATE.md's D4 as
written is false.**

### 2. `#592` is the only node in the graph that is not "fixed"

I scanned every `widgets_values` array in all 8 containers for the tokens
`fixed / randomize / increment / decrement / increment-wrap`:

```
sg3 #98  UltimateSDUpscale     wv[2]=fixed
sg3 #92  FaceDetailer          wv[4]=fixed
sg2 #592 KSampler              wv[1]=randomize   <-- the only one
sg2 #600 KSamplerAdvanced      wv[2]=fixed
sg2 #607 FaceDetailerPipe      wv[4]=fixed
sg2 #617 UltimateSDUpscale     wv[2]=fixed
sg5 #165 FaceDetailer          wv[4]=fixed
sg5 #114 FaceDetailer          wv[4]=fixed
sg6 #406 DetailerForEachDebug  wv[4]=fixed
sg7 #256 FaceDetailer          wv[4]=fixed   (inside the bypassed stage)
sg7 #176 FaceDetailer          wv[4]=fixed   (inside the bypassed stage)
sg1 #625 PrimitiveInt Width    wv[1]=fixed
sg1 #628 PrimitiveInt Height   wv[1]=fixed
```

`#592 KSampler` `widgets_values: [1083387472542732, "randomize", 40, 4,
"dpmpp_2m_sde", "karras", 1]` — and both `seed` and `denoise` are **linked**
inputs (`inputs[4].link = 1271`, `inputs[5].link = 1272`, each carrying
`"widget": {"name": ...}`).

### 3. Does `control_after_generate` still mutate a widget whose input is linked? **YES.**

From the frontend sourcemaps at
`/venv/main/lib/python3.12/site-packages/comfyui_frontend_package/static/assets/`:

- `src/scripts/app.ts` (in `dialogService-Cj1Hfeot.js.map`), inside the queue
  loop: `executeWidgetsCallback(queuedNodes, 'afterQueued', {isPartialExecution})`
  where `queuedNodes = collectAllNodes(this.rootGraph)`.
- `src/utils/graphTraversalUtil.ts` (in `api-gz4kgzki.js.map`): `collectAllNodes`
  → `mapAllNodes`, which **recurses into every subgraph**
  (`if (node.isSubgraphNode?.() && node.subgraph) results.push(...mapAllNodes(node.subgraph, mapFn))`).
  So nodes inside sg2 are included.
- `src/scripts/widgets.ts` (same map), `addValueControlWidgets`:
  `valueControl.afterQueued = ({isPartialExecution} = {}) => { if (!isPartialExecution && !controlValueRunBefore()) applyWidgetControl() }`
  and `applyWidgetControl()` does, for a number widget,
  `case 'randomize': targetWidget.value = Math.floor(Math.random() * range) * step2 + min`.
  **There is no check anywhere in `applyWidgetControl` for whether the target
  widget's input is connected.** The only link-awareness in that function is
  `Object.defineProperty(valueControl, 'disabled', { get: () => targetWidget.computedDisabled })`,
  which affects rendering, not the callback.

So `#592`'s `seed` widget **is** re-randomised in memory after every queue, even
though its value is not what executes.

### 4. But the executed seed comes from the link, and the link is reproducible

`src/utils/executionUtil.ts` `graphToPrompt` writes widget values first, then
**overwrites** them from resolved links:

```
if (widgets) { for (const [i, widget] of widgets.entries()) { ... inputs[widget.name] = widgetValue } }
for (const [i, input] of node.inputs.entries()) {
  const resolvedInput = node.resolveInput(i)
  ...
  inputs[input.name] = [String(resolvedInput.origin_id), parseInt(resolvedInput.origin_slot)]
}
```

So `#592.seed` in the API graph is a link reference, not `1083387472542732`.

Chain: `#483 INSTARAW_RealityPromptGenerator.seed_list` → root link 1373 →
`#619` (sg2 host) input 4 `seed` → sg2 link 1271 → `#592.seed`.

`#483.widgets_values[3]` currently holds exactly one batch entry with
`"seed": 12345, "seed_control": "fixed"`.

`ComfyUI_INSTARAW/nodes/input_nodes/reality_prompt_generator.py:199-206` reads
`entry_seed = int(entry.get("seed", 1111111))` and appends `entry_seed +
repeat_idx`; line 202 comments *"(seed_control is for AFTER execution, handled in
frontend)"*.

`ComfyUI_INSTARAW/js/reality_prompt_generator.js:9014-9040`
(`updateSeedsAfterGenerate`, hooked to the `execution_success` API event at
:9046-9060) advances the stored seed per entry:

```js
const seedControl = entry.seed_control || "randomize";
if (seedControl === "increment") { entry.seed = currentSeed + 100; ... }
else if (seedControl === "decrement") { ... }
else if (seedControl === "randomize") { entry.seed = Math.floor(Math.random() * (9999999 - 1111111 + 1)) + 1111111; ... }
// "fixed" does nothing - seeds stay the same
```

Shipped value is `"fixed"` → seed stays 12345 across runs. **Note the fallback:
`entry.seed_control || "randomize"` — any batch entry authored without a
`seed_control` key silently randomises.**

### Verdict — the true reproducibility story

**The graph as shipped IS reproducible from the seed it exposes.** Every sampler
seed is fixed; the one exposed seed (`#483` entry seed 12345) drives `#592`
through a link and does not advance because `seed_control` is `"fixed"`.

The **actual** residual defect is narrower and different from STATE.md's:

`#592`'s `control_after_generate` is `"randomize"` on a widget that is overridden
by a link. Consequences:
1. The in-memory widget value changes after every queue, so **the saved workflow
   file differs after every run** even when nothing was edited. That defeats
   file-diff-based "did anything change?" checks, which is exactly the
   verification method this project relies on.
2. It is a **latent landmine**: it is dormant only for as long as the link
   survives. If a buyer deletes `#483`, disconnects the seed wire, or the RPG
   panel is emptied, `#592`'s seed becomes live and randomises on every run —
   silently making the pipeline non-reproducible, which is precisely the failure
   STATE.md described but attributed to the wrong node.

**The fix is provably inert in the API graph by construction.** In
`src/scripts/widgets.ts` the control widget is created with
`{ values: [...], serialize: false, canvasOnly: true }`, and
`src/utils/executionUtil.ts` skips it:
`if (!widget.name || widget.options?.serialize === false) continue`.
A `control_after_generate` value **never reaches the backend at all**. Changing
`"randomize"` → `"fixed"` therefore cannot alter any submitted prompt.

---

## D5 — the mis-wired ControlNet path · **MOOT, the path is gone**

`grep -c` over `OFMTech-NSFW/OFMTech_NSFW.json` for each type returns **0**:

```
SetUnionControlNetType           0
ControlNetLoader                 0
ControlNetApplyAdvanced          0
IPAdapter                        0   (substring — catches IPAdapterUnifiedLoader too)
DepthAnythingV2Preprocessor      0
INSTARAW_BrandingNode            0
INSTARAW_LatentSwitch            0
```

Node ids `#638`, `#639`, `#641`, `#645` do not exist in root or in any of the
seven subgraph definitions. Subgraph "1. Canvas & Routing" — the stage that used
to hold them — now contains exactly four nodes: `#625 PrimitiveInt` (Width),
`#628 PrimitiveInt` (Height), `#627 PrimitiveFloat` (Base denoise), `#635
EmptyLatentImage`.

This independently confirms main's finding. `AUDIT.md` A5, `QUESTIONS.md` Q3 and
`STATE.md`'s unfixed list all describe a path that was deleted on the destroyed
pod. **No action. Nothing to repair, nothing to delete.**

Consequence for `SETUP.md`: the models QUESTIONS.md Q3 flagged as unfetched
(`controlnet-union-sdxl-promax.safetensors`, `depth_anything_v2_vitl.pth`, the
IPAdapter models) are now correctly absent from the graph, so their absence from
the setup script is no longer a defect. Not my file — flagged for whoever owns
`SETUP.md`.

---

## Adjacent items main asked me to settle if cheap

### A23 — bbox detector wired into a segm input · **already fixed in this file**

`#114 FaceDetailer.inputs[8] segm_detector_opt` → `link: None`.
`#107 UltralyticsDetectorProvider.outputs[1] SEGM_DETECTOR` → `links: None`.
The link AUDIT.md A23 describes does not exist any more. The second instance it
cites, sg7 `#171` → `#176`, is inside the bypassed stage; I did not re-check it
because it cannot execute. **A23 is stale. No action.**

### A3 — `#87 ImageBlend` at `blend_factor: 1.0` · **confirmed, and it is a real no-op**

Subgraph "3. Hands, Skin & Second Upscale (SDXL)":
```
136:  92[0] -> 87[0]   (HandDetailer -> ImageBlend.image1)
139:  92[0] -> 91[1]   (HandDetailer -> ImageUpscaleWithModel.image)
138:  90[0] -> 91[0]   (#90 = x1_ITF_SkinDiffDetail_Lite_v1.pth)
137:  91[0] -> 87[1]   (skin-detail output -> ImageBlend.image2)
#87 widgets_values: [1, "normal"]
```

`comfy_extras/nodes_post_processing.py:44-46`:
```python
blended_image = cls.blend_mode(image1, image2, blend_mode)
blended_image = image1 * (1 - blend_factor) + blended_image * blend_factor
```
and `:51-52` `if mode == "normal": return img2`.

At `blend_factor = 1.0` the result is exactly `image2`. **`#87` is a pure
passthrough of `#91`; `image1` contributes nothing**, so the skin-detail filter
runs at 100% with no blend back. Confirmed from source, as AUDIT.md A3 claimed.

Whether 1.0 is right is a **quality** call — not mine. I have added it to the
A/B set as an extra arm so the user has the picture rather than the argument.

---

---

# Part 2 — verification and A/B evidence

## How the renders were driven, and how it differs from the buyer's path

**This is stated up front, not in a footnote, because an A/B run through a
modified prompt is not the buyer's path.**

Each arm is defined by an **API graph captured from a real Chromium against the
live ComfyUI**, by calling `app.graphToPrompt(app.rootGraph)` after loading the
saved workflow. That is the identical conversion the Run button performs —
`src/scripts/app.ts` calls `await this.graphToPrompt(this.rootGraph)` immediately
before `api.queuePrompt`. So the frontend UI-graph → API-graph conversion, which
is where this run's shipped blocker lived, **is** exercised.

Two things about it are not the buyer's path, and both are identical in every
arm:

1. **I did not click the Run button.** The INSTARAW selector element
   (`<instaraw-imgae-filter-popup class="instaraw_popup">`, `filter.css:1-8`:
   `position:absolute; width:100%; height:100%; z-index:100000`) intercepted
   pointer events over the Run button in one of my probe runs, so I captured the
   converted graph directly instead of clicking. **My method therefore does not
   prove the button is clickable** — that is WS2's harness's job, not mine.
2. **`pick_list` is set to `"0"` on `#603 INSTARAW_ImageFilter` in the submitted
   prompt only. The workflow file is untouched.** Without it every render
   blocks: `#603` ships with `pick_list = ""` and `ontimeout = "send none"`, and
   `image_filter.py:103-131` then opens the selector, waits 600 s, and on
   `TimeoutResponse` sets `images_to_return = []`, which reaches
   `image_filter.py:131`, `raise InterruptProcessingException()`.
   `pick_list="0"` is deterministic here: `#602 INSTARAW_BatchFromImageList`
   receives one image from `#617` and `list_utility_nodes.py:46-47` returns
   `images[0]` unchanged when `len(images) == 1`, so the batch is B=1 and
   `[int(x) % B for x in "0".split(',')]` is `[0]` in every arm.

Both LoRA stacks were left at the **shipped `"None"` state** in every arm. No
LoRA was loaded, so the baseline is the configuration a buyer gets on first open.

Artifacts: `/workspace/nsfw-fix/results/ws4/<arm>/` holds `api_graph.json` (the
exact submitted prompt), `result.json` (prompt id, timing, peak GPU), and the
PNG.

## Arm reconciliation

WS1 issued an unscoped `POST /api/queue {"clear": true}` partway through my
runs, which silently drops **pending** items with no history entry at all — so
`/history` cannot tell you what was dropped. I therefore reconciled every prompt
id I submitted against the server. **All seven arms are accounted for; none of
mine was dropped.**

| arm | graph | prompt id | outcome | server-side execution |
|---|---|---|---|---|
| `A_baseline` | A | `3dba994f-2d22-4be3-9e9c-8abf26e17dc5` | success | 214.2 s |
| `A2_control_repeat` (1st launch) | A | `fe17460b-64c8-4ecf-b5b2-f65bbb4d99ed` | success | 209.7 s |
| `A2_control_repeat` (2nd launch) | A | `77244669-0904-49d5-add1-5482de33de3e` | success | 210.6 s |
| `A3_control_repeat` | A | `9fac6819-e1e8-471d-b2c7-58b6ac8d6e05` | success | **311.9 s** |
| `A4_control_repeat` | A | `49c0761f-a44a-4f18-a92a-fdc62e3ae243` | success | 209.8 s |
| `B_no_vae_roundtrip` | B | `fa9bc0a5-db65-4bd6-b475-d1190417ab0c` | success | 280.5 s |
| `B2_no_vae_roundtrip_repeat` | B | `b477f1fd-5c4d-4639-853e-357c6b6d6965` | success | 280.2 s |
| `C_no_sdxl_face_pass` | C | `47d54fad-4093-4102-99ac-6b650d06c528` | success | 280.8 s |

**Eight prompts, not seven — and I initially miscounted my own.** The
`A2_control_repeat` arm's output folder held two PNGs. Rather than assume the
extra one was another workstream's, I traced it: I had launched that arm twice
(the first `nohup` redirected its log to a relative path I then failed to read,
so I re-launched it), and **both submissions ran**. `fe17460b` is confirmed mine
by signature — it carries `pick_list: '0'` on `#603`, which only my driver sets;
every other workstream's prompt in history has `pick_list: ''`. Its output is
`HasMetadata_00003_.png` and it is bit-identical to the second launch's
`HasMetadata_00004_.png`.

I had previously reported `fe17460b` as another workstream's. It was mine. The
correction adds a control sample rather than removing one, but the error is worth
recording: **"it must be someone else's" is an assumption, and it was checkable.**

Neither errored prompt in history is mine. `47c2df2f` was WS1's own.
`824dd0d6` has `execution_start` at 1785969249574, and my earliest submission of
any kind is `3dba994f` at 1785969997325 — 748 s later. I had not submitted
anything when it started. `4f4d2b7d` and `5d8a3345` carry `pick_list: ''` and a
7-node graph respectively, so neither is mine.

Every comparison in this report uses the single image named in each arm's own
`result.json`, which is taken from that prompt id's `/history` outputs — not from
globbing the folder.

---

# Finding 1 — this pipeline is deterministic under fixed seeds (7 runs, 2 graphs)

**Five** arms submitted the identical A-graph and **two** submitted the identical
B-graph. Within each graph, every pairwise comparison gives **MSE exactly 0**,
maximum absolute difference **0** 8-bit levels, SSIM **1.000**, on the full
2688x3456 frame. That is all six A-graph pairs and the one B-graph pair.

The strongest single datum is `A3_control_repeat`. The server reports it executed
with **zero cached nodes** — every sampler in the graph re-ran from scratch — and
it still produced an image bit-identical to the other four. So this is not an
artifact of ComfyUI handing back a cached tensor, which matters, because the
faster A runs *did* have most of the base generator served from cache (see
Finding 2). `A3` is the run that makes the claim mean something.

This is consistent with what I proved separately and earlier from the file: every
`control_after_generate` in the graph is now `"fixed"`, and the one exposed seed
does not advance between runs because `#483`'s batch entry carries
`seed_control: "fixed"`.

**Three limits on this finding, all of which matter:**

1. **It is 7 runs, not a guarantee.** The documented failure mode on this project
   is *five agreeing renders before a sixth disagreed*. Seven agreeing runs is a
   larger version of the same shape, not a different kind of thing.
2. **It does not license verifying by hashes.** CLAUDE.md's ban was written about
   the **sibling video** pipeline, and I have not overturned it. Observed
   determinism on 7 samples is not guaranteed determinism, and a **zero** pixel
   delta still proves nothing about whether a change is inert. Inertness is
   proved here by graph diff and never by pixels.
3. It says nothing about other seeds, resolutions, or prompts. One prompt, one
   seed, one resolution.

---

# Finding 2 — none of my timing numbers are comparable, and the reason is not the one I first gave

**I got this wrong twice and the second correction matters more than the first.**

### First attempt: wall-clock

My driver's wall-clock includes queue wait. Two runs of the identical graph took
485.7 s and 752.9 s. Useless; discarded.

### Second attempt: server-side execution time, n=2 — wrong

I substituted the server's `execution_start` → `execution_success` timestamps and
reported that **D1 made the render 31 % slower**. That was wrong. I replaced a
noisy instrument with a less noisy one and then stopped questioning it, on two
samples.

### Third attempt: n=4 control, "it is contention" — also wrong

With four control samples the spread was 209.8 / 210.6 / 214.2 / **311.9 s** on
provably identical work, so I retracted the 31 % claim and attributed the spread
to a shared GPU. **That attribution was also wrong.** The renders are strictly
sequential — ComfyUI serialises the queue, and the history timestamps show every
prompt starting within ~1 s of the previous one finishing. There was no
concurrency to contend for.

### What was actually happening: ComfyUI's execution cache

The server records it directly, in the `execution_cached` message of every
history entry:

| arm | exec | cached nodes | was `619:617 UltimateSDUpscale` cached? |
|---|---|---|---|
| `A_baseline` | 214.2 s | 49 | **yes** |
| `A2_control` | 210.6 s | 57 | **yes** |
| `A4_control` | 209.8 s | 57 | **yes** |
| `A3_control` | **311.9 s** | **0** | no — fully cold |
| `B_no_roundtrip` | 280.5 s | 53 | **no** |
| `B2_no_roundtrip` | 280.2 s | 53 | **no** |
| `C_no_face_pass` | 280.8 s | 52 | **no** |

Every arm did a **different amount of real work**, decided by what the previous
prompt happened to leave in the cache:

- The three "fast" A runs at ~211 s had the entire base generator, **including
  `#617 UltimateSDUpscale`**, served from cache and skipped.
- The B and C runs re-pointed `619:617.image`, which changes `#617`'s input
  signature and invalidates its cache entry — so `#617` actually ran. That, not
  the change itself, is the ~70 s.
- `A3` cached nothing at all, because another workstream's unrelated 1.8 s prompt
  ran immediately before it and evicted everything. Its **311.9 s is the only
  honest full-graph number I have.**

The clincher is `C`. It deletes an entire `FaceDetailerPipe` pass — 20 steps at
guide_size 1280 — and came in at 280.8 s against `B`'s 280.5 s. A real detailer
pass cannot cost 0.3 s. The numbers were never measuring the graph.

### What this means

**There is no valid timing comparison anywhere in my results, and no timing claim
survives — in either direction.** D1 is neither faster nor slower on this
evidence; the evidence cannot speak to it.

**The pixel comparisons are unaffected.** A cache hit returns the identical
stored tensor, so caching cannot manufacture or hide a pixel difference — which
is exactly why the four A arms are bit-identical and `A3`, with nothing cached,
matches them.

### How to actually measure timing here, for whoever does it next

- Compare only runs that report `execution_cached: 0`, or force that state by
  submitting an unrelated prompt between arms to evict the cache. Read
  `execution_cached` from `/history` for every run and **discard any arm whose
  cached-node set differs from its comparator's** — this is a cheap, decisive
  check that I should have run first.
- Per-node timings would be better still. One tooling trap: ComfyUI targets
  execution websocket events at the **submitting client's** `client_id`
  (`execution.py` passes `self.server.client_id` into `send_sync`), so a passive
  listener on `/ws` with any other `clientId` receives nothing. The listener must
  reuse the submitter's id. Mine did not, which is why I have no per-node data.

### The lesson, stated plainly

I substituted a less noisy metric and then treated it as noise-free on n=2, which
is the same error in a smarter disguise. Widening the denominator caught the
error but produced a second wrong explanation for it; only reading the server's
own record of what it had actually executed produced the right one. **Two of my
three attempts to explain these numbers were wrong, and none of the numbers
themselves would have revealed it.**

## D4 — proven inert

API graphs captured from Chromium against the live server, before and after the
one-line change:

```
A: api_ws1.json  (88 nodes)      <- WS1's commit 41e77f9, pre-D4
B: api_d4.json   (88 nodes)      <- post-D4
IDENTICAL — 0 differences across 88 nodes and all inputs
```

This is the second, independent confirmation of the by-construction argument:
`control_after_generate` carries `serialize: false`, so it never reaches the
backend. Empirically, **no node in any captured API graph carries a
`control_after_generate` key at all.**

No render was needed and none was run for D4.

## D1 — graph diff

```
A: api_current.json (88 nodes)   <- pre-D1 (verified identical to WS1's commit)
B: api_d1_c.json    (86 nodes)   <- post-D1
3 DIFFERENCE(S):
  NODE ONLY IN A          A='VAEEncode'         B=None
  NODE ONLY IN A          A='VAEDecode'         B=None
  INPUT 619:617.image     A=['619:616', 0]      B=['619:607', 0]
```

Exactly the intended change, and nothing else moved across the 86 shared nodes
or any of their inputs.

**A trap worth recording for anyone repeating this.** Node `419`'s
`rgthree_comparer` input **flaps between captures of the identical file** — it
holds stale `/api/view` preview URLs that the rgthree extension restores
asynchronously, so whether it is present depends on capture timing. I confirmed
this by capturing the same unchanged file three times: present, absent, present.
It is cosmetic and unrelated, but it will appear as a spurious fourth difference
if the two captures happen to disagree, and it would be easy to misread as "the
change was not clean". Before diffing, capture the *same* file twice and check
that this input agrees.

## D1 — what it does to the image, and a result I did not expect

Full numbers in `results/ws4/metrics_D1_B_vs_A.json`.

| | full frame | face crop |
|---|---|---|
| PSNR | **30.63 dB** | 28.64 dB |
| SSIM | **0.857** | 0.743 |
| mean abs diff | 4.26 levels | 5.78 levels |
| max abs diff | 168 levels | 168 levels |
| pixels differing > 1 level | **83.9 %** | 87.4 % |
| pixels differing > 8 levels | **15.7 %** | 26.4 % |

Images to compare by eye:
- A: `/workspace/nsfw-fix/results/ws4/A_baseline/HasMetadata_00001_.png`
- B: `/workspace/nsfw-fix/results/ws4/B_no_vae_roundtrip/HasMetadata_00005_.png`

Both 2688x3456.

**This is a large change, far larger than one VAE round-trip costs directly.**
That is expected on reflection and worth stating so nobody reads 30.6 dB as "the
round-trip was destroying 30 dB of quality": `#617 UltimateSDUpscale` re-samples
at denoise 0.25 from a *different* starting image, and every downstream pass —
hands, face at 0.80, mouth, eyes — then runs on a different image. The
difference compounds. **Neither image is "correct". The user judges.**

### D1 timing: no claim survives — see Finding 2

**I published a wrong result here and it is worth showing rather than deleting.**

On two arms I reported: *"Removing the round-trip made the render 31 % slower —
214.2 s to 280.5 s. Two VAE operations cannot account for +66 s, so a detector
that did not fire before now fires."* On that basis I wrote that the case for D1
was materially weakened.

**All of that is withdrawn.** The sequence that killed it:

1. Two more control arms (`A3`, `A4`) on the **identical** graph came back at
   **311.9 s** and 209.8 s. `A3` at 311.9 s versus `A_baseline` at 214.2 s —
   same graph, pixel-identical output, 98 s apart. A 102 s spread on provably
   identical work is larger than the effect I had claimed.
2. So I retracted the 31 % and blamed a shared GPU. **That was wrong too** — the
   queue is serialised and the history timestamps show no overlap.
3. Reading `execution_cached` in each history entry gave the real answer: every
   arm had a different set of nodes served from cache. The ~211 s A runs skipped
   `#617 UltimateSDUpscale` entirely; the B and C runs re-ran it because
   re-pointing `619:617.image` invalidated its cache entry. `A3` cached **zero**
   nodes, which is why it was slowest and why it is the only honest full-graph
   number.

The detector hypothesis is dropped entirely; there is nothing left for it to
explain. **D1 is neither faster nor slower on this evidence — the evidence cannot
speak to timing at all.** Full analysis, and how to measure it properly, in
Finding 2 above.

**The case for D1 therefore rests where it should: on the graph diff.** Two nodes
removed, one input re-pointed, nothing else moved across 86 shared nodes and
every input, and the deleted pair is a provably redundant image→latent→image with
no sampler between. The image change is real and is a look question for the
owner, with `423df24` a clean single-commit revert if he prefers the old one.

### D1 — reproducibility of the changed arm

`B_no_vae_roundtrip` and `B2_no_vae_roundtrip_repeat` submitted the identical
post-D1 graph and produced **bit-identical** images (MSE 0, max abs diff 0
levels). So the post-D1 graph is as deterministic as the pre-D1 graph, and the
A-vs-B difference below is a property of the change, not of a single roll.

---

## D3 — the ablation, and it corrects AUDIT.md A22

Arm `C_no_sdxl_face_pass` is arm `B` with **one variable changed**: `#607
FaceDetailerPipe` (SDXL, denoise 0.45, `bbox/face_yolov8m.pt`) deleted and
`619:617.image` re-pointed to `619:596 VAEDecode`, which is what fed `#607`.
`#598 ToDetailerPipeSDXL` becomes unreachable and is pruned by the executor.
The submitted graph is saved at
`results/ws4/C_no_sdxl_face_pass/api_graph.json`.

**C vs B** (`results/ws4/metrics_D3_C_vs_B.json`):

| | full frame | face crop |
|---|---|---|
| PSNR | 32.56 dB | **27.69 dB** |
| SSIM | 0.900 | **0.723** |
| mean abs diff | 3.20 levels | 6.61 levels |
| pixels differing > 8 levels | 10.4 % | **32.8 %** |

Images:
- with pass 1: `/workspace/nsfw-fix/results/ws4/B_no_vae_roundtrip/HasMetadata_00005_.png`
- without pass 1: `/workspace/nsfw-fix/results/ws4/C_no_sdxl_face_pass/HasMetadata_00006_.png`

**`AUDIT.md` A22 is too strong.** It argues that pass 3 at denoise 0.80 "largely
erases" pass 1, and that pass 1 "may be paying a full detailer pass to produce
detail that pass 3 discards". If that were true, deleting pass 1 would leave the
final image nearly unchanged. Instead **32.8 % of face-crop pixels move by more
than 8 levels**. Pass 1 measurably survives into the final image.

**And the "free speed" argument is unsupported too** — `C` at 280.8 s against
`B` at 280.5 s, with both inside the same cache regime and the whole timing
method shown unusable in Finding 2. Deleting a 20-step detailer pass did not
measurably save time on this instrument, which is a statement about the
instrument, not about the pass.

**I am shipping no change for D3.** It is neither provably wasted nor provably
free to remove. It is a look question — does the final face look better with two
passes or one — and I cannot answer it and neither can the user's agent. The A/B
pair above is the deliverable.

For context only, `C` vs the shipped baseline `A` (two variables changed, so not
a clean comparison): full frame PSNR 30.13 dB / SSIM 0.851; face crop 27.22 dB /
SSIM 0.716. (`results/ws4/metrics_C_vs_A_context.json`.)

---

# Summary of what shipped and what did not

| defect | verdict | shipped? | commit |
|---|---|---|---|
| **D1** VAE round-trip `#597`→`#616` | real | **yes** | `423df24` |
| **D2** `#106` placeholder at denoise 0.8 | real but documented buyer content | **no**, by design | — |
| **D3** face detailed twice (0.45 then 0.80) | real, but neither wasted nor free | **no** | — |
| **D4** "`#600` reseeds every run" | **false**; real defect was `#592` | **yes** | `a01ae3a` |
| **D5** ControlNet path mis-wired | **moot**, path deleted before this session | n/a | — |

Two commits, each independently revertible. `a01ae3a` is proven inert by graph
diff and by construction. `423df24` is proven to be exactly the intended
structural change and nothing else, with its image effect measured and left for
the owner to judge.

**Things I got wrong during this session and corrected**, recorded because the
next session's risk is repeating them rather than repeating my conclusions:

1. Reported a 31 % slowdown from D1 on two samples. Withdrawn.
2. Then blamed the spread on GPU contention. Also wrong — the queue is
   serialised.
3. The actual cause was ComfyUI's execution cache giving each arm a different
   amount of real work, visible all along in `execution_cached` in `/history`.
4. Attributed one of my own prompts (`fe17460b`) to another workstream. It was
   mine, identifiable by the `pick_list: '0'` signature.

The common thread is that every one of these was checkable from data I already
had, and none of them would have been revealed by looking harder at the numbers
themselves.

---

## Appendix — the skin-filter A/B (AUDIT.md A3 / Q-D)

Not one of my five defects; run because main asked for it if cheap and because I
had promised the pair in `WS4-questions.md`.

Arm `D_skinblend_050` (`9760ac4e-a238-4516-a382-67df4ebdcc18`) is arm `B` with
one input changed: `587:87.blend_factor` 1.0 → 0.5.

| | full frame | face crop |
|---|---|---|
| PSNR | 33.88 dB | 29.05 dB |
| SSIM | 0.924 | 0.780 |
| pixels differing > 1 level | 80.4 % | 87 % |
| pixels differing > 8 levels | 7.9 % | 24.5 % |

- filter at 100 % (shipped): `results/ws4/B_no_vae_roundtrip/HasMetadata_00005_.png`
- filter at 50 %: `results/ws4/D_skinblend_050/HasMetadata_00011_.png`

Confirmed unchanged: at `blend_factor` 1.0 with `blend_mode "normal"`,
`comfy_extras/nodes_post_processing.py:44-52` computes
`image1*(1-1.0) + image2*1.0`, so `#87` returns `#91`'s output exactly and the
un-filtered `#92 HandDetailer` image contributes nothing. The
`x1_ITF_SkinDiffDetail_Lite_v1` filter runs at full strength with no blend back.

**Shipped no change.** It is a look question. The pair is the deliverable.
