# P1 — two questions about renders that already exist

Owner: P1-ANALYSIS. Branch `master`. **No GPU used, no renders made, no graph
edited.** Everything below comes from files already on disk: the four WS4 arm
PNGs, the eight submitted `api_graph.json` files, and the two LoRA `.safetensors`
headers at `/workspace/ComfyUI/models/loras/`.

Every number is pasted from command output. Inference is labelled **[I]**.

Deliverable crops are in `results/phase1/`.

---

## Answers in one line each

**Q1 — the gold lower-lip artifact is real.** It is a ~16×12 px gold metallic
object at full-res **x 1371-1386, y 1183-1194**, immediately below the lower-lip
border on the chin. It is present in `D_skinblend_050` and **absent from
`B_no_vae_roundtrip`, `A_baseline` and `C_no_sdxl_face_pass`**. B and D differ in
**exactly one graph input**, so the blend change caused it.

**Q2 — no character LoRA was loaded in any WS4 arm.** All four slots on `#618`
*and* all four on `#116` read the string `"None"` in **all eight** arms. The
eye-colour change is therefore the two face passes disagreeing on an un-LoRA'd
face — a quality finding, not a likeness bug. **But** the mechanism the owner was
worried about is structurally live for a buyer; see §2.4.

---

# Q1 — the gold lower-lip artifact

## 1.1 The two arms differ in exactly one input

`B_no_vae_roundtrip/api_graph.json` vs `D_skinblend_050/api_graph.json`,
compared node-by-node on every input:

```
=== B_no_vae_roundtrip  vs  D_skinblend_050 ===
  nodes: 86 vs 86
  #587:87 (ImageBlend / 'ImageBlend')
        .blend_factor:  1  ->  0.5
  --- 1 input/class difference(s) on shared nodes ---
```

No node added, none removed, no other input changed anywhere in the graph. This
is the cleanest single-variable A/B in the set.

For completeness, the other two pairs are also single-variable:

```
=== B_no_vae_roundtrip  vs  C_no_sdxl_face_pass ===
  nodes: 86 vs 85
  ONLY IN B: ['619:607']
  #619:617 UltimateSDUpscale .image: ['619:607',0] -> ['619:596',0]
  --- 1 input/class difference(s) on shared nodes ---

=== A_baseline  vs  B_no_vae_roundtrip ===
  nodes: 88 vs 86
  ONLY IN A: ['619:597', '619:616']
  #619:617 UltimateSDUpscale .image: ['619:616',0] -> ['619:607',0]
  --- 1 input/class difference(s) on shared nodes ---
```

`#587:87` is inside subgraph host `587` ("3. Hands, Skin & Second Upscale
(SDXL)"). The owner's shorthand "`#87 ImageBlend`" and the API-graph id
`587:87` are the same node.

## 1.2 Determinism — verified here, not taken on trust

I recomputed it from the PNGs rather than reading `metrics_control.json`.
All five A-graph renders, all ten pairs:

```
=== A-GRAPH ARMS: pairwise MSE on raw pixels ===
  MSE A_baseline        vs A2_control_repeat  = 0   maxabs=0
  MSE A_baseline        vs A2_control_repeat  = 0   maxabs=0     (00003 and 00004)
  MSE A_baseline        vs A3_control_repeat  = 0   maxabs=0
  MSE A_baseline        vs A4_control_repeat  = 0   maxabs=0
  MSE A2_control_repeat vs A2_control_repeat  = 0   maxabs=0
  MSE A2_control_repeat vs A3_control_repeat  = 0   maxabs=0
  MSE A2_control_repeat vs A4_control_repeat  = 0   maxabs=0
  MSE A2_control_repeat vs A3_control_repeat  = 0   maxabs=0
  MSE A2_control_repeat vs A4_control_repeat  = 0   maxabs=0
  MSE A3_control_repeat vs A4_control_repeat  = 0   maxabs=0

=== B-GRAPH ARMS ===
  MSE B_no_vae_roundtrip vs B2_no_vae_roundtrip_repeat = 0   maxabs=0
```

All at 2688×3456. This reproduces STATE.md §5's claim independently. Combined
with §1.1, any pixel difference between B and D **is** caused by
`blend_factor 1 → 0.5`; there is no noise floor available to explain it away.

**The one gap I will not paper over:** determinism was demonstrated on the A
graph (5 samples) and the B graph (2 samples). The **D graph was rendered
once**. Nothing in the evidence suggests the D graph would behave differently,
but a single D-graph repeat would close the last gap and costs one render.
Logged in `PROPOSALS.md` terms in `notes/P1-questions.md`.

## 1.3 The artifact — present in D, absent in B

Look at `results/phase1/Q1_artifact_B_vs_D_8x.png` (B left, D right). In D there
is a small gold/brass object shaped like a hook or a partial ring, with a darker
lower lobe, sitting on the chin against the lower-lip border. In B that area is
plain skin.

**Segmentation.** Yellowness is defined as `(R+G)/2 − B`. In a 45×35 px window
covering the sub-lip area (`y 1175-1210, x 1355-1400`):

```
OBJECT: D yellowness>65 -> 54 px
  bbox full-res: x 1371-1386  y 1183-1194  (16 x 12 px)
  same threshold in the same window: A=0  B=0  C=0  D=54
```

Threshold sweep in the same window — the object is not a threshold artefact:

```
  thr     A     B     C     D
   60     6    68     0   162
   65     0     0     0    54
   70     0     0     0    22
   75     0     0     0    10
   80     0     0     0     7
   85     0     0     0     3
```

Above 65 levels of yellowness, **only D has any pixels there at all.**

## 1.4 The RGB numbers

Mean over the same 54-pixel set in every arm (identical pixel coordinates, so
this is a like-for-like comparison):

| arm | R | G | B | yellowness |
|---|---|---|---|---|
| A_baseline | 174.3 | 123.4 | 94.2 | 54.6 |
| B_no_vae_roundtrip | 170.9 | 127.4 | 93.8 | 55.4 |
| C_no_sdxl_face_pass | 174.3 | 130.5 | 99.8 | 52.6 |
| **D_skinblend_050** | **198.0** | **162.0** | **108.6** | **71.4** |

`D − B = dR +27.1, dG +34.6, dB +14.8`. All three channels rise, but R and G
rise roughly twice as much as B — which moves hue toward yellow and raises
value. On the tighter 10-px core (`D yellowness > 75`) the blue channel is
essentially pinned while R and G climb, which is the textbook signature:

| arm | mean RGB over the 10-px core | HSV hue | sat | val |
|---|---|---|---|---|
| A | (182.0, 142.6, 108.4) | 27.9° | 0.405 | 0.714 |
| B | (181.0, 137.6, 102.1) | 27.0° | 0.436 | 0.710 |
| C | (175.4, 131.7, 100.0) | 25.2° | 0.430 | 0.688 |
| **D** | **(205.8, 164.0, 102.5)** | **35.7°** | **0.504** | **0.807** |

B → D on the same ten pixels: **R +24.8, G +26.4, B +0.4**; hue **+8.7°** toward
yellow; saturation +0.068; value +0.097. Hue in D spans 34.6°-37.5° across those
pixels — a tight gold band, not scattered noise.

Single most-yellow pixel, full-res **(1377, 1192)**:

```
A: RGB=(183,145,110)  hue=28.8°  sat=0.399  val=0.718
B: RGB=(184,140,105)  hue=26.6°  sat=0.429  val=0.722
C: RGB=(175,131, 99)  hue=25.3°  sat=0.434  val=0.686
D: RGB=(226,181,115)  hue=35.7°  sat=0.491  val=0.886
```

The object also carries a dark lobe. Over the 170 px where D's mean channel
value is under 110: D mean luma **90.1** against A 120.1, B 120.6, C 131.9 — so
D has genuinely new dark structure there too, not just a colour wash.

## 1.5 Control: this is not a global colour shift

If D were simply warmer overall, every warm region would move. It does not.
Full-frame signed mean `D − B`:

```
  R: -0.3576     G: -0.8952     B: -0.8440
  mean yellowness delta over the whole frame: +0.2176
```

D is very slightly **darker** overall, and the whole-frame yellowness change is
**+0.22** against **+16.0** inside the object footprint — roughly 70×.

Stronger still: counting "gold-like" pixels full-frame (yellowness > 70 **and**
max channel > 150) and locating them:

```
A: 562 px  — 450 at y1920-2048 x2176-2304 ... of which in the sub-lip window: 0
B: 376 px  — 371 at y1920-2048 x2176-2304 ... of which in the sub-lip window: 0
C: 825 px  — 798 at y1920-2048 x2176-2304 ... of which in the sub-lip window: 0
D:  33 px  —  22 at y1152-1280 x1280-1408 ... of which in the sub-lip window: 22
```

D has the **fewest** gold-like pixels in the whole frame, and two-thirds of the
ones it does have are the artifact. A/B/C have **zero** there. The pre-existing
gold cluster at `y1920-2048 x2176-2304` is present in all four arms and is not
what we are looking at.

## 1.6 Verdict on Q1

**Confirmed on all three sub-questions.**

- Present in `D_skinblend_050/HasMetadata_00011_.png` — yes, 54 px above a
  threshold that no other arm reaches at all.
- Absent in its correct comparator `B_no_vae_roundtrip/HasMetadata_00005_.png` —
  yes, and also absent in A and C.
- Attributable to the blend rather than run-to-run variation — yes. The graphs
  differ in exactly one input, and the pipeline returned pixel-identical output
  across 5 A-graph and 2 B-graph renders.

I am not offering a view on which image looks better. The measurement says the
object is there in D and not in B.

## 1.7 Mechanism — **[I]**, but grounded, and it points somewhere useful

`#587:87 ImageBlend` is not a terminal cosmetic node. Tracing its consumers:

```
#587:87 ImageBlend  (blend_factor, blend_mode 'normal', image1=587:92, image2=587:91)
  -> 587:98 UltimateSDUpscale .image      (steps 2, cfg 1, denoise 0.08)
  -> 587:99 GetImageSize
  -> 620:137 ImageColorMatch+ .reference
  ... and downstream of those: 620:114, 620:165, 621:163, 15 nodes in host 622, root 419/505
```

So the blend output is fed into **four further samplers**, including:

```
#620:114  FaceDetailer    'FaceDetailer'   steps 30  cfg 1  denoise 0.80   bbox 620:107 face_yolov8m
#620:165  FaceDetailer    'Mouth Detailer' steps  8  cfg 1  denoise 0.35   bbox 621:161 bbox/lips_v1.pt
                          guide_size 1808, bbox_dilation 10, bbox_crop_factor 3
```

Changing `blend_factor` changes the image handed to those samplers, so they
re-derive their region from a different starting point and can synthesise
content that was not there before. The artifact sits at y 1183-1194, a few
pixels below the lip — comfortably inside a lips bbox expanded by
`bbox_crop_factor 3`. That is why a whole-frame filter knob produces a discrete
new object in one small place. **[I]** — I cannot attribute it to a specific
pass without a render.

**The finding I did not expect.** The only non-empty negative prompt in the
entire Z-Image detail chain is `#620:105`, and it reads:

```
'deformed, ugly, blurry, bad anatomy, disfigured, extra eyes, cropped face,
 out of frame, deformed piercing, bad piercing, watermark, text'
```

Someone has already met this artifact class and written **"deformed piercing,
bad piercing"** into the negative to suppress it. That negative is attached to
`#620:114`, which runs at **cfg = 1** — and STATE.md §8 records that at cfg 1
classifier-free guidance is off, so the negative cannot act. The Mouth
Detailer's own negative, `#621:167`, is the **empty string**.

Every sampler's cfg, read from the graph:

```
node         class                    title                 cfg  steps  denoise
#587:92      FaceDetailer             HandDetailer            3     30     0.42
#587:98      UltimateSDUpscale        Ultimate SD Upscale     1      2     0.08
#619:592     KSampler                 KSampler                4     40   (wired)
#619:600     KSamplerAdvanced         KSampler (Advanced)     1     70      -
#619:607     FaceDetailerPipe         FaceDetailer (pipe)     3     20     0.45
#619:617     UltimateSDUpscale        Ultimate SD Upscale   4.5     25     0.25
#620:114     FaceDetailer             FaceDetailer            1     30     0.80   <- negative names piercings
#620:165     FaceDetailer             Mouth Detailer          1      8     0.35   <- negative empty
#622:406     DetailerForEachDebug     DetailerDebug (SEGS)    1      8     0.42
```

This confirms STATE.md §8's "`#114`, `#165` and `#406` all run at `cfg = 1`"
exactly. It also upgrades that item from a tidiness concern to something with a
named consequence: **the graph's own written defence against a bad lip piercing
is inert, and a bad lip piercing is what appeared.** Whether raising cfg on
`#620:114` suppresses it is a pod experiment, not something I can settle here.

---

# Q2 — was a character LoRA loaded?

## 2.1 No. Both stacks were `"None"` in all eight arms.

Read directly from each arm's submitted `api_graph.json`:

| arm | nodes | `#618` "Your SDXL LoRa" lora_01..04 | `#116` "Your ZIT LoRa" lora_01..04 |
|---|---|---|---|
| A_baseline | 88 | None, None, None, None | None, None, None, None |
| A2_control_repeat | 88 | None, None, None, None | None, None, None, None |
| A3_control_repeat | 88 | None, None, None, None | None, None, None, None |
| A4_control_repeat | 88 | None, None, None, None | None, None, None, None |
| B_no_vae_roundtrip | 86 | None, None, None, None | None, None, None, None |
| B2_no_vae_roundtrip_repeat | 86 | None, None, None, None | None, None, None, None |
| C_no_sdxl_face_pass | 85 | None, None, None, None | None, None, None, None |
| D_skinblend_050 | 86 | None, None, None, None | None, None, None, None |

The value is the literal string `"None"`, which is rgthree's "no LoRA selected"
sentinel. Strengths were left at their defaults (1 / 0.8 / 1 / 0.8 on `#618`,
1 / 0.9 / 0.9 / 1 on `#116`) but with no file selected they load nothing.

Full titles, from `_meta`:

```
#618  Lora Loader Stack (rgthree)  '2 · Your SDXL LoRa  (body, pose, hands)'
      model = ['619:613', 0]   clip = ['619:613', 1]     <- SDXLNSFW.safetensors
#116  Lora Loader Stack (rgthree)  '2 · Your ZIT LoRa  (face, mouth, eyes)'
      model = ['620:113', 0]   clip = ['620:110', 0]     <- zimage.safetensors / qwen.safetensors
```

## 2.2 The only LoRA actually loaded anywhere is a speed LoRA

Every LoRA-class node and every model filename in the graph:

```
LORA-CLASS #116      Lora Loader Stack (rgthree)  '2 · Your ZIT LoRa'      (all None)
LORA-CLASS #618      Lora Loader Stack (rgthree)  '2 · Your SDXL LoRa'     (all None)
LORA-CLASS #587:97   LoraLoader  '4-step speed LoRA (TDD, Apache-2.0)'  sdxl_tdd_lora_weights.safetensors
LORA-CLASS #619:610  LoraLoader  '4-step speed LoRA (TDD, Apache-2.0)'  sdxl_tdd_lora_weights.safetensors
```

`sdxl_tdd_lora_weights.safetensors` is a step-distillation / speed LoRA, not a
character LoRA. **No trained character identity was present in any WS4 render.**

## 2.3 Therefore: this is a quality finding, not a likeness bug

The owner's fork was explicit, so I will answer it in his terms. Both stacks
were `"None"`, so there were no trained character features in these renders for
the first face pass to overwrite. The eye-colour change between B and C is
**the two face passes disagreeing with each other on an un-LoRA'd face.**

The likeness-bug reading is **not** live *for these particular renders*.

## 2.4 …but the mechanism the owner was worried about is structurally live

This is the part I would not want him to miss. Tracing the model that drives the
first face pass:

```
#619:613 CheckpointLoaderSimple (SDXLNSFW.safetensors)
  -> #618 Lora Loader Stack (rgthree)      <- the buyer's SDXL character LoRA goes HERE
    -> #619:608 ModelSamplingDiscrete
      -> #619:609 PerturbedAttentionGuidance
        -> #619:598 ToDetailerPipeSDXL     (clip = ['618', 1])
          -> #619:607 FaceDetailerPipe     denoise 0.45   <- FIRST face pass
```

and the pass that runs after it:

```
#620:113 UNETLoader (zimage.safetensors)
  -> #116 Lora Loader Stack (rgthree)      <- the buyer's Z-Image character LoRA goes HERE
    -> #620:114 FaceDetailer               denoise 0.80   <- THIRD pass, different model family
    -> #620:165 FaceDetailer 'Mouth Detailer'  denoise 0.35
    -> #622:406 DetailerForEachDebug (eyes)    denoise 0.42
```

The first face pass carries `#618`'s LoRA. Everything after it carries `#116`'s.
They are **different model families and different LoRA slots.** So a buyer who
fills only one of the two stacks gets a face that is rendered under one identity
and then re-rendered at denoise 0.80 under another. **[I]** That is exactly the
shape of the failure the owner was describing, and it does not need these
renders to be true — it is readable off the wiring.

The shipped product appears to intend both slots to be filled: STATE.md §5's
buyer-journey render used `lunaskye.safetensors` in `#618` **and**
`luna.safetensors` in `#116`, and two other workstreams' in-flight graphs on
disk (`results/phase0/api_graph.json`, `results/cfg/00-baseline-full/api_graph.json`)
do the same. Nothing in the graph or in `#649 MarkdownNote` **enforces** it,
though, and I have not checked what the buyer-facing text says about needing two
LoRAs — that is worth a look by whoever owns the docs.

**The decisive experiment is one render pair, not a re-analysis:** repeat the D3
ablation (B vs C) with `lunaskye` in `#618` and `luna` in `#116`, and measure
the same iris statistic. If the iris shift is larger with LoRAs loaded than the
`dE76 ≈ 7-8` measured below, the likeness reading is live for buyers.

## 2.5 Text-encoder context — verified from the files, not assumed

The routing claim first. `#620:110` is the `CLIPLoader` (`qwen.safetensors`).
Its output 0 goes to:

```
#116     Lora Loader Stack (rgthree) .clip
#620:105 CLIPTextEncode .clip     (face negative)
#620:106 CLIPTextEncode .clip     (face positive)
#621:166 CLIPTextEncode .clip     (mouth positive)
#621:167 CLIPTextEncode .clip     (mouth negative)
#622:394 CLIPTextEncode .clip     (eyes negative)
#622:398 CLIPTextEncode .clip     (eyes positive)
#622:406 DetailerForEachDebug .clip
```

That is three stages × (positive, negative) = six `CLIPTextEncode` nodes, all on
the **raw** CLIP, which matches `notes/WS4-report.md` lines 180-186 exactly.
One refinement worth recording: `#620:114` and `#620:165` additionally take
`#116`'s **clip output (slot 1)** on their own `clip` input, so the LoRA-side
clip does reach those two nodes even though the standalone text encodes bypass
it.

Now the part that makes the routing moot. I read the safetensors headers of the
LoRA files present on this box:

```
luna.safetensors                       480 tensors    170.1 MB
      diffusion_model (UNet/DiT): 480
      >>> TEXT-ENCODER TENSORS: 0
      meta ss_base_model_version = 'zimage'
lunaskye.safetensors                  2364 tensors    185.7 MB
      lora_unet (SDXL UNet): 2364
      >>> TEXT-ENCODER TENSORS: 0
      meta ss_base_model_version = 'sdxl_1.0'
sdxl_tdd_lora_weights.safetensors     2364 tensors    393.9 MB
      lora_unet (SDXL UNet): 2364
      >>> TEXT-ENCODER TENSORS: 0
```

Every key in `luna.safetensors` is prefixed `diffusion_model.`; every key in the
other two is prefixed `lora_unet_`. Zero keys match any of
`text_model`, `lora_te`, `text_encoder`, `clip`, `t5`, `qwen`, `token_embed`.

**So the raw-CLIP routing costs nothing for these files.** Even when a buyer
loads them, there are no text-encoder weights to route. This confirms WS4's
claim from the files themselves rather than from memory. It does **not**
generalise: a third-party LoRA carrying `lora_te*` tensors would be silently
half-applied — UNet yes, text encoder no. Worth a line in the buyer docs.

## 2.6 The eye colour — real, but "brown to green" overstates the endpoint

Measured on the D3 pair (B vs C), in CIELAB, which is the right space for this
question: **positive `a*` is toward red, negative `a*` is toward green.**

Method: locate each arm's **own** pupil centre independently (darkest 11×11
mean, searched in a 50×50 window) so a shifted eye cannot bias the sample; take
the iris annulus r 15-27 px, lower half only (the upper half carries lash shadow
that differs between arms); drop the darkest 15 % and brightest 15 % by luma to
exclude pupil and speculars. ~550 px per measurement.

Pupil centres found, showing the eye did move slightly between arms:

```
LEFT  eye: A(1244,752) B(1244,748) C(1246,748) D(1242,745)
RIGHT eye: A(1511,800) B(1510,797) C(1511,801) D(1513,802)
```

**Left eye (viewer's left), full-res centre ~(1244,748):**

| arm | n | R | G | B | L* | a* | b* | chroma |
|---|---|---|---|---|---|---|---|---|
| A | 548 | 60.2 | 40.2 | 30.9 | 18.33 | 8.08 | 9.94 | 12.81 |
| **B** | 552 | 62.5 | 40.8 | 29.7 | 18.81 | **8.68** | 11.43 | **14.35** |
| **C** | 551 | 61.4 | 50.0 | 41.6 | 21.75 | **3.66** | 7.29 | **8.16** |
| D | 552 | 55.2 | 34.0 | 23.9 | 15.63 | 8.78 | 10.89 | 13.99 |

**Right eye (viewer's right), full-res centre ~(1510,797):**

| arm | n | R | G | B | L* | a* | b* | chroma |
|---|---|---|---|---|---|---|---|---|
| A | 555 | 69.0 | 44.8 | 33.4 | 20.94 | 9.59 | 11.92 | 15.30 |
| **B** | 549 | 72.6 | 43.9 | 30.9 | 21.18 | **11.60** | 13.96 | **18.15** |
| **C** | 548 | 77.5 | 59.1 | 47.1 | 26.56 | **6.23** | 10.59 | **12.29** |
| D | 551 | 75.4 | 50.6 | 37.8 | 23.56 | 9.52 | 12.77 | 15.93 |

Deltas against B, with the other two arms as the scale reference:

```
LEFT   A-B: dL*=-0.49  da*=-0.60  db*=-1.49   dE76= 1.68
       C-B: dL*=+2.93  da*=-5.02  db*=-4.14   dE76= 7.13
       D-B: dL*=-3.18  da*=+0.10  db*=-0.54   dE76= 3.23
RIGHT  A-B: dL*=-0.25  da*=-2.01  db*=-2.04   dE76= 2.88
       C-B: dL*=+5.38  da*=-5.37  db*=-3.37   dE76= 8.31
       D-B: dL*=+2.37  da*=-2.08  db*=-1.19   dE76= 3.38
```

**What the numbers say.**

1. The change is **real and specific to C.** `dE76` is 7.13 / 8.31 for C against
   1.68 / 2.88 for A and 3.23 / 3.38 for D — two to four times larger, in both
   eyes independently.
2. It is **in the brown → green direction.** `a*` falls by ~5 in both eyes
   (8.68 → 3.66 and 11.60 → 6.23), which is a move away from red toward green,
   and chroma drops 43 % and 32 %. The iris also lightens (`L*` +2.9 / +5.4).
   R−G narrows from 21.7 to 11.4 (left) and 28.7 to 18.4 (right).
3. **It does not reach green.** `a*` stays **positive** in both eyes (3.66 and
   6.23). Colorimetrically the endpoint is a desaturated **olive / hazel-grey**,
   not a green iris. "Brown to green" describes the direction correctly and the
   destination too strongly.

I am reporting the direction and the magnitude. I am not saying whether the
result looks acceptable — that is the owner's call on
`results/phase1/Q2_eyeL_B_vs_C_6x.png` and `Q2_eyeR_B_vs_C_6x.png`.

One observation beyond colour, offered as **[I]**: in the wider crops
(`Q2_eyeL_context_B_vs_C_1to1.png`) the eyelid and lash structure differs
noticeably between B and C, not only the iris colour. Removing the first face
pass changes the eye's drawn geometry, not just its tint. The `metrics_D3_C_vs_B.json`
face crop already records this at the whole-face level: PSNR 27.687 dB, SSIM
0.7227, 32.77 % of face pixels moving more than 8 levels.

---

## Cross-check against the existing metrics files

My independently computed full-frame numbers for B vs D agree with
`results/ws4/metrics_A3_blend_D_vs_B.json` to every published digit:

| quantity | metrics file | recomputed here |
|---|---|---|
| PSNR | 33.88 dB | 33.88 dB |
| mean abs diff | 2.9733 | 2.9733 |
| max abs diff | 170.0 | 170 |
| pct > 1 level | 80.3648 % | 80.36 % |
| pct > 8 levels | 7.8988 % | 7.90 % |

Two independent implementations agreeing is worth something; it is not
independent evidence about the artifact, which rests on §1.3-§1.5.

---

## Files written

```
results/phase1/Q1_mouth_B_1to1.png                     350x180 native crop, arm B
results/phase1/Q1_mouth_D_1to1.png                     350x180 native crop, arm D
results/phase1/Q1_mouth_B_vs_D_sidebyside_1to1.png     both, 1:1, B left / D right
results/phase1/Q1_artifact_B_vs_D_1to1.png             65x55 tight pair, 1:1
results/phase1/Q1_artifact_B_vs_D_8x.png               same, 8x nearest-neighbour
results/phase1/Q2_eyeL_B_vs_C_1to1.png                 90x90 iris pair, 1:1
results/phase1/Q2_eyeL_B_vs_C_6x.png                   same, 6x nearest-neighbour
results/phase1/Q2_eyeR_B_vs_C_1to1.png                 90x90 iris pair, 1:1
results/phase1/Q2_eyeR_B_vs_C_6x.png                   same, 6x nearest-neighbour
results/phase1/Q2_eyeL_context_B_vs_C_1to1.png         200x140 whole-eye pair, 1:1
results/phase1/Q2_eyeR_context_B_vs_C_1to1.png         200x140 whole-eye pair, 1:1
```

All crops are native resolution unless the filename says `6x` or `8x`, and the
upscales are nearest-neighbour so no pixel is invented.

---

## What I did not settle

- **Which pass draws the object.** `#620:165 Mouth Detailer` is the best
  candidate on bbox geometry, but `#620:114` at denoise 0.80 covers the same
  area. Needs a render with one pass disabled.
- **Whether cfg > 1 on `#620:114` suppresses it.** The negative already names
  "deformed piercing, bad piercing" and is inert at cfg 1. Needs a render, and
  raising cfg changes output everywhere.
- **Whether the D graph is deterministic.** n=1. One repeat closes it.
- **Whether the eye shift is worse with character LoRAs loaded** — §2.4. This is
  the one that decides whether D3 is a quality tweak or a likeness bug for
  buyers, and it needs the render pair described there.
- **Whether the blend at 0.5 produces this artifact reliably or was unlucky
  once.** One sample. A blend sweep (0.25 / 0.5 / 0.75) would show whether the
  sub-lip region is generally unstable under this knob.

I have deliberately not extended "the images match" into any claim beyond the
specific pixels measured. The output-hash ban stands.
