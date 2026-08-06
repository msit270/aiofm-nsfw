# R4 — the four STATE.md defects, re-assessed against the current file

Owner: R4. Branch `master`.
Authoritative file: `/workspace/nsfw-fix/OFMTech-NSFW/OFMTech_NSFW.json`,
sha256 `8d50f636b77532153389004bbc2ac7a1f0c7b8e92de6212e257db12170458966`
(`2e4e8e9`, i.e. `#114` steps 30 → 8 already applied). Every render below is on
top of that file.

A previous run (`notes/WS4-report.md`) assessed this same list. I re-verified its
conclusions against the current file rather than repeating its work, and the two
questions the world had changed under — D1 at steps 8, and whether the
placeholder measurably harms output at steps 8 — I re-rendered.

Every claim is traceable to a node id, a link id, a file:line or pasted command
output. Inference is labelled **[I]**.

---

## Verdict table

| | Defect as stated in STATE.md | Verdict | Shipped |
|---|---|---|---|
| 1 | `#597 VAEEncode` → `#616 VAEDecode` round-trip | **real; re-rendered at steps 8; still moves the face the way the owner rejected** — §1 | no change |
| 2 | `#106` placeholder driving the face pass at denoise 0.8 | **not an oversight; at steps 8 measurably *different* from a real prompt but not *worse*** — §2. **But with the owner's LoRAs loaded, filling `#106` in as `#649` instructs crashes the graph 2/2 at `622:403` — §2b. New, reproducible, and not one of the four.** | no change; needs a decision |
| 3 | `#600 KSamplerAdvanced` reseeding itself | **FALSE, and nothing residual remains** | no change needed |
| 4 | `SetUnionControlNetType` wired in parallel | **MOOT — the path does not exist** | no change needed |

---

## 0 — the controls, before any A/B is read

### The renders

Seven arms. Six are API graphs captured from a real Chromium against the live
ComfyUI by calling `app.graphToPrompt(app.rootGraph)` — the identical conversion
the Run button performs — then POSTed to `/prompt`. The seventh
(`R4_D2_loras_filled`, §2b) is branched from a previous run's already-submitted
API graph so that it differs from an *existing* render in one input only; that is
stated where it is used.
`inputs.pick_list = "0"` is set on `619:603 INSTARAW_ImageFilter` **in the
submitted prompt only, identically in every arm; no arm's workflow file contains
it.** Without it `#603` opens the selector, waits 600 s and aborts. Every arm
passes `tools/preflight/integrity.py` with 0 problems, and every arm is
graph-diffed against the baseline to prove only the intended input moved.

Seed 12345 and the `results/face/ARMS.md` prompt in every arm; both LoRA stacks
left at the shipped `"None"`, so this is a first-open buyer configuration.
I did not press the Run button, so **none of this is proof the buyer journey
works** — that is the browser harness's job, not mine.

### Control 1 — the server is not in the poisoned state, and it is not a judgement call

`HANDOFF.md` §7.1: a NaN reaching `tensor2pil` poisons the resident model and
every later render silently returns a flat grey face with `status: success`. I
calibrated a detector for it before reading any arm — fraction of face-box pixels
whose 9×9 local luma σ is below one 8-bit level:

```
KNOWN GOOD  C_zface_steps_08   flat_frac=0.0000  median_rgb=[141, 99, 81]  luma_sd=46.25
KNOWN GOOD  A0_baseline        flat_frac=0.0000  median_rgb=[139, 98, 79]  luma_sd=46.32
VOID        CF_crop_1.5        flat_frac=0.9994  median_rgb=[ 53, 47, 43]  luma_sd= 0.64
VOID        CF_crop_1.0        flat_frac=0.9994  median_rgb=[ 53, 47, 43]  luma_sd= 0.64
```

The documented `(53, 47, 43)` signature reproduces exactly and the two classes
are three orders of magnitude apart, so this is a threshold test, not an opinion.
**Every arm below is reported with its `flat_frac`.**

### Control 2 — my baseline is the previous run's baseline, bit for bit

`R4_base` versus the previous run's `C_zface_steps_08` — the same graph rendered
in a different session, hours earlier:

```
psnr_db: inf   ssim: 1.0   mean_abs_diff: 0.0   max_abs_diff: 0   pct_gt_1: 0.0%
```

Identical on all 2688×3456 pixels. That anchors three things at once: the server
is healthy, my arm-building pipeline reproduces the previous run's exactly, and
the published steps-8 evidence in `results/face/` is directly comparable with
everything here.

A second, within-session control says the same thing. `R4_base_ctl` submitted a
byte-identical prompt **four arms later** in the queue:

```
R4_base vs R4_base_ctl   full: max_abs_diff 0   face: max_abs_diff 0
cached nodes: base=57  ctl=56   (620:106 re-executed in the control, not served from cache)
```

So the block did not drift, and the identity is not an artefact of everything
being handed back from cache — a node genuinely re-ran and still produced the
same bytes.

**This is a control, not a verification method.** `CLAUDE.md` bans proving a
change inert by comparing rendered output, and I have not done that anywhere —
inertness is proved by graph diff throughout. A matching image tells me the
instrument is behaving; it is never my evidence that a change did nothing.

**What it does license, narrowly:** on this pipeline with fixed seeds the
observed run-to-run difference is **exactly zero**, not the ~48.7 dB floor
`CLAUDE.md` cites from the sibling video pipeline. That is why the 1–2 % readings
in §2 can be reported as signal at all. Three agreeing samples across two
sessions is still not a guarantee — the documented failure mode here is five
agreeing renders before a sixth disagreed — and I am not claiming one.

### Control 3 — the file moved under me mid-run, and I tested rather than assumed

I built and submitted five arms against `8d50f636…` (`2e4e8e9`). While they were
queued another agent committed `a806ce3`, taking the shipped file to
`0be499d3…`. It changes three things: `#105.widgets_values[0]` → `""`, a new
`#652 MarkdownNote` inside sg5, and `#649`'s text.

Only one of the three can execute. Verified, not assumed — none of `#649`,
`#650`, `#651`, `#652` appears in the API graph (88 nodes both sides), and a
graph diff of the current file's own conversion against my baseline's gives:

```
RESULT: DIFFERENT — 1 difference(s): value_changed=1
  value_changed  620:105.inputs.text   A: "deformed, ugly, blurry, ..."   B: ""
```

`a806ce3` shipped that on a by-construction argument with **no render behind
it**. So I added a sixth arm, `R4_cur`, built from the current file, to test it:

```
R4_base (#105 = the old negative text)  vs  R4_cur (#105 = "", the file as it ships now)
  full: max_abs_diff 0   psnr inf   ssim 1.0
  face: max_abs_diff 0   psnr inf   ssim 1.0
R4_cur: success, exec 183.5 s, cached 57, flat_frac 0.0000
```

**Bit-identical.** Two things follow. First, my baseline was the shipped graph's
output at that moment, not a superseded one. Second, `a806ce3`'s inertness claim,
which rested on `comfy/samplers.py:370` dropping the uncond at cfg 1, now has a
render behind it as well as the argument. That was somebody else's commit and it
holds up.

### Correction — the file moved a THIRD time, after I verified all this

Later in the session another agent landed `74c0f11`, **`#114` `bbox_crop_factor`
3 → 1.5** (`widgets_values` index 15), taking the file to
`a811b5d690ccc5207bc7bd1c626cdd3db3b720b9be60d0a687436efcfd2143d8`. Unlike
`a806ce3` that is an **executable** change to the face pass itself — it sets the
size of the region `#114` crops and re-diffuses.

```
OLD (my arms): [..., 0.8, 18, True, True, 0.5, 10, 3,   'center-1', ...]
NEW (ships):   [..., 0.8, 18, True, True, 0.5, 10, 1.5, 'center-1', ...]
                                              index 15 ^
```

**So I must withdraw the sentence I wrote above before that commit existed:
"every A/B in this report applies unchanged to the file that ships today". It was
true when written and it is not true now.** Everything in §1, §2 and §2b was
measured at `bbox_crop_factor 3`.

What that does and does not affect, stated carefully:

* **§3 and §4 are unaffected** — they are static readings and I re-checked them
  against the current file.
* **§1 (D1) and §2 (D2) are comparisons of two arms that both had crop_factor 3.**
  Each comparison is internally valid; whether the *magnitudes* carry over to
  crop_factor 1.5 is **untested**. The D1 verdict rests on direction plus the
  owner's standing decision, neither of which I expect to move — but that is
  **[I]**, not a measurement.
* **§2b is the one that genuinely needs re-testing.** `bbox_crop_factor` changes
  what the face pass produces, and the crash is a downstream face-detection
  failure. Whether filling `#106` still crashes at crop_factor 1.5 is **not
  known**. It is one render on each side to find out, and it should be done
  before anyone concludes either that the defect is gone or that it still bites.

### One thing the timing cannot do — stated before the numbers, not after

`R4_base` executed with **57 cached nodes**, including `619:617
UltimateSDUpscale`, `619:597` and `619:616`. `R4_D1_novae` re-points
`619:617.image`, which invalidates that node's cache entry, so `#617` genuinely
runs in that arm. **The arms did different amounts of real work and their wall
figures are not comparable.** That is exactly the trap behind the previous run's
retracted "+31 % slower". I make **no timing claim for D1**, in either
direction, and the cached-node set for every arm is recorded in each
`results/r4/<arm>/meta.json`.

---

## 3 — "`#600 KSamplerAdvanced` reseeds itself" · **FALSE. And unlike last time, there is no residual either.**

STATE.md:161-163 already records the correction; this section is the
confirmation against the current file, which is what I was asked for.

The claim being checked, verbatim from `AUDIT.md` A21 — note it is marked
**[F]**, this project's tag for a fact read off the file:

> | sg1 `#600 KSamplerAdvanced` | `578361683541099` | **`"randomize"`** | **no** — widget only |
>
> `#600` has no `seed` input slot at all **[F]** — its `noise_seed` is widget-only,
> and it is set to randomize after every run.

The seed value `578361683541099` and "no `seed` input slot" are both correct.
**The `"randomize"` is not.**

### `#600` reads `fixed`

`2. Base Generator (SDXL)`, `#600 KSamplerAdvanced`:

```
widgets_values (10): ['enable', 578361683541099, 'fixed', 70, 1, 'lcm', 'normal', 66, 1000, 'disable']
inputs[0] model  link=1244   inputs[1] positive link=1245
inputs[2] negative link=1246 inputs[3] latent_image link=1247
```

All four inputs are link-typed and none is a widget-input, so the array maps 1:1
onto `nodes.py` `KSamplerAdvanced.INPUT_TYPES` plus the one synthetic
`control_after_generate` companion that `noise_seed` creates. 10 entries, 10
slots, **index 2 = `"fixed"`**.

### `#592` — the residual WS4 found — is now `fixed` too

WS4 reported `#592 KSampler` as the one node still reading `"randomize"`, and
`a01ae3a` changed it. Confirmed applied:

```
#592 KSampler  widgets_values (7): [1083387472542732, 'fixed', 40, 4, 'dpmpp_2m_sde', 'karras', 1]
```

### Nothing else in the file randomises

I scanned every `widgets_values` array in all eight containers (root + seven
subgraphs, 109 nodes) for the tokens
`fixed / randomize / increment / decrement / increment-wrap`. **Thirteen hits,
all `fixed`:**

```
3. Hands, Skin & Second Upscale  #98  UltimateSDUpscale     wv[2] = 'fixed'
3. Hands, Skin & Second Upscale  #92  FaceDetailer          wv[4] = 'fixed'
2. Base Generator (SDXL)         #592 KSampler              wv[1] = 'fixed'
2. Base Generator (SDXL)         #600 KSamplerAdvanced      wv[2] = 'fixed'
2. Base Generator (SDXL)         #607 FaceDetailerPipe      wv[4] = 'fixed'
2. Base Generator (SDXL)         #617 UltimateSDUpscale     wv[2] = 'fixed'
5. Face & Mouth Detail (Z-Image) #165 FaceDetailer          wv[4] = 'fixed'
5. Face & Mouth Detail (Z-Image) #114 FaceDetailer          wv[4] = 'fixed'
6. Eyes (FaceMesh crop/composite)#406 DetailerForEachDebug  wv[4] = 'fixed'
7. Anatomy Detailers - DISABLED  #256 FaceDetailer          wv[4] = 'fixed'
7. Anatomy Detailers - DISABLED  #176 FaceDetailer          wv[4] = 'fixed'
1. Canvas & Routing              #625 PrimitiveInt Width    wv[1] = 'fixed'
1. Canvas & Routing              #628 PrimitiveInt Height   wv[1] = 'fixed'
```

**Zero occurrences of `randomize` anywhere in the file.**

### The one exposed seed does not advance

The seed a buyer sets is `#483 INSTARAW_RealityPromptGenerator`'s batch entry.
Read from the file:

```
ROOT #483  batch entries: 1
  id='default-01'  seed=12345  seed_control='fixed'
  outputs[2] seed_list  links=[891, 1373]
```

and the chain into the only sampler that consumes it, each hop read from the
file rather than assumed:

```
root link 1373: [1373, 483, 2, 619, 2, 'INT']        #483[2] -> #619 input slot 2
ROOT #619 (host of sg 3ff96466 "2 · Base Generator (SDXL)")
      inputs[2] name='seed' link=1373
sg2 declared inputs[2] name='seed' type=INT linkIds=[1271]
sg2 link 1271: -10[2] -> 592[4]  type=INT               -> #592.seed
```

`#592.inputs[4] seed` carries `widget: {'name': 'seed'}` **and** `link: 1271`, so
the link wins and the widget value `1083387472542732` never executes — the
wired-input-overrides-widget trap, here working in the graph's favour.

`ComfyUI_INSTARAW/js/reality_prompt_generator.js` advances the stored seed after
`execution_success` only for `increment`/`decrement`/`randomize`; `"fixed"` does
nothing. Shipped value is `"fixed"`.

### Verdict

**The graph as shipped is reproducible from the seed it exposes.** Every
`control_after_generate` in the file is `fixed`, the exposed seed is `fixed`, and
there is no `randomize` left anywhere. **STATE.md's defect 3 is false, and the
narrower residual WS4 identified has since been fixed and stays fixed. No action.**

Two limits I will not paper over:

* This is a **static** argument plus the previous run's seven agreeing renders.
  It is not a guarantee — the documented failure mode on this project is five
  agreeing renders before a sixth disagreed. What I can say without a render is
  that no mechanism in the file re-randomises anything.
* The latent landmine WS4 named is unchanged and is *not* a `control_after_generate`
  issue: `reality_prompt_generator.js` reads `entry.seed_control || "randomize"`,
  so a batch entry authored **without** a `seed_control` key silently randomises.
  The shipped entry has the key. A buyer-authored one might not. **[I]** — I have
  not tested whether the panel can create an entry lacking the key.

---

## 4 — "the mis-wired ControlNet path, `SetUnionControlNetType` in parallel" · **MOOT. The path does not exist.**

Raw-string counts over the whole 10,939-line file:

```
SetUnionControlNetType           0
ControlNetLoader                 0
ControlNetApply                  0
ControlNet                       0
IPAdapter                        0
DepthAnything                    0
depth_anything                   0
Depth                            0
INSTARAW_BrandingNode            0
INSTARAW_LatentSwitch            0
controlnet                       2   <-- both are pack metadata, see below
```

The two lowercase hits are `cnr_id` / `aux_id` provenance strings on a
`MediaPipe-FaceMeshPreprocessor` node, which ships inside the
`comfyui_controlnet_aux` pack:

```
"cnr_id": "comfyui_controlnet_aux",
"ver": "12f35647f0d510e03b45a47fb420fe1245a575df",
"Node name for S&R": "MediaPipe-FaceMeshPreprocessor",
"aux_id": "comfyui_controlnet_aux/",
```

That is a face-mesh preprocessor used by the Eyes stage — not a ControlNet.

I also censused every node type across all 109 nodes in all eight containers and
regex-matched `control|ipadapter|depth|union` case-insensitively against the type
names: **zero matches**.

### Verdict

**Moot.** Nothing to rewire, nothing to delete, nothing to test on a pod. This
independently confirms WS4's D5 and STATE.md:158-160 against the current file.
**No action, and no further time spent.**

Consequence worth carrying to `SETUP.md` (not my file): the models that
`QUESTIONS.md` Q3 flags as unfetched for this path —
`controlnet-union-sdxl-promax.safetensors`, `depth_anything_v2_vitl.pth`, the
IPAdapter models — are correctly absent from the graph, so their absence from the
setup script is not a defect.

---
## 1 — `#597 VAEEncode` → `#616 VAEDecode` with nothing between · structure re-confirmed

### It is still there, and it is still a pure image → latent → image

Read from `2. Base Generator (SDXL)` in the current file:

```
#596 VAEDecode          out[0] IMAGE  links=[1255]
#607 FaceDetailerPipe   in[0] image link=1255      out[0] image links=[1232]
                        out[1..5] cropped_refined / cropped_enhanced_alpha /
                                  mask / detailer_pipe / cnet_images  all links=[]
#597 VAEEncode          in[0] pixels link=1232  in[1] vae link=1233   out[0] LATENT links=[1260]
#616 VAEDecode          in[0] samples link=1260 in[1] vae link=1261   out[0] IMAGE  links=[1262]
#617 UltimateSDUpscale  in[0] image link=1262
```

```
1232: 607[0] -> 597[0]  IMAGE
1233: 613[2] -> 597[1]  VAE
1260: 597[0] -> 616[0]  LATENT
1261: 613[2] -> 616[1]  VAE
1262: 616[0] -> 617[0]  IMAGE
```

`#597.outputs[0].links == [1260]` and `#616.outputs[0].links == [1262]` — one
consumer each, and both VAEs come from the same `#613 CheckpointLoaderSimple`
slot 2. **No sampler, no resize, no mask sits between them.** All four modes are
`0` (not bypassed). So the pair is redundant *in intent*: it costs one full VAE
encode and one full VAE decode and applies one extra lossy round-trip.

### Why it is nonetheless load-bearing *in effect*

`#617 UltimateSDUpscale`, the immediate consumer, re-samples what it is handed:

```
#617 widgets_values: [1.25, 34651603, 'fixed', 25, 4.5, 'dpmpp_2m_sde', 'karras',
                      0.25, 'Linear', 896, 1152, 8, 64, 'None', 0.30, 128, 8, 16,
                      True, False, 1]
```

— 25 steps at cfg 4.5, **denoise 0.25**. So whatever softening the round-trip
applies is not merely passed through, it is re-diffused from, and every
downstream pass (hands, skin, face, mouth, eyes) then runs on a different image.
That is the mechanism behind `73f3d5c`'s revert note and behind the large
whole-frame deltas the previous run measured.

### History, so nobody re-litigates it from scratch

* `423df24` removed the pair.
* `73f3d5c` **reverted it — the owner's call, on the A/B**: *"removing it makes
  the face crunchier, and the face is the pipeline's existing quality problem."*
* The A/B that decision rested on was measured with `#114` at **steps 30**.
  `2e4e8e9` has since taken `#114` to **steps 8**, a far less aggressive face
  pass. That is why this was re-rendered rather than taken as closed.

### The arm

`R4_D1_novae` — link 1262 re-originated `#616[0]` → `#607[0]`; links
1232/1233/1260/1261 deleted; `#613`'s VAE fan-out 12 → 10; nodes `#597` and
`#616` deleted; sg2 28 → 26 nodes. Preflight `integrity.py`: 0 problems.

Graph diff of the submitted API prompt against the baseline's — the sanctioned
inertness check, run here to prove the arm is a *single* structural change and
not to prove anything about pixels:

```
RESULT: DIFFERENT — 3 difference(s): link_changed=1, node_removed=2
  node_removed       node 619:597  (VAEEncode)
  node_removed       node 619:616  (VAEDecode)
  link_changed       619:617.inputs.image   A: ["619:616", 0]   B: ["619:607", 0]
```

Exactly the intended change and nothing else across the 85 shared nodes and all
their inputs.

### What it does to the image at steps 8 — rendered, not argued

Both arms healthy: `flat_frac` 0.0000, `median_rgb` [141, 99, 81] / [141, 99, 81].

**`R4_D1_novae` vs `R4_base`** (`results/r4/metrics.json`):

| | full frame | face crop |
|---|---|---|
| PSNR | **34.41 dB** | 34.01 dB |
| SSIM | 0.9026 | 0.9040 |
| mean abs diff | 2.769 levels | 2.998 levels |
| max abs diff | 179 | 179 |
| pixels differing > 1 level | 78.12 % | 79.56 % |
| pixels differing > 8 levels | **6.03 %** | **7.61 %** |

**The pair to look at, 1:1, 940×1180, native resolution:**
`results/r4/D1_face_sheet1of1.png` — baseline left, round-trip removed right.
Full frames: `results/r4/R4_base/HasMetadata_00035_.png` and
`results/r4/R4_D1_novae/HasMetadata_00036_.png`, both 2688×3456.

### Scale — because "6 %" means nothing without something to compare it to

Same composition, same instrument, one fixed skin mask taken from the baseline so
the denominator does not move with the arm. `A0_baseline` is the *same* prompt and
seed with `#114` at steps 30, so all three rows differ in one variable at a time:

| | blobs/Mpx ↓ *(the defect)* | pores/Mpx ↑ *(what was asked for)* | fine_rms | blob_rms |
|---|---|---|---|---|
| steps 30 + round-trip *(what shipped before `2e4e8e9`)* | 1148.8 | 9822.3 | 5.045 | 4.949 |
| **steps 8 + round-trip — SHIPPED TODAY** | **821.9** | **15383.1** | **3.033** | **4.533** |
| steps 8 − round-trip *(D1)* | 872.6 | 15571.9 | 3.263 | 4.573 |

Read as movement away from the shipped graph:

```
steps 30 -> 8   (already applied, 2e4e8e9)   blobs -28.5%   pores +56.6%   fine_rms -39.9%
remove round-trip at steps 8   (D1)          blobs  +6.2%   pores  +1.2%   fine_rms  +7.6%
```

and on pixels, against the same shipped baseline's face crop:

```
steps 30 (A0_baseline)      PSNR 26.19 dB  SSIM 0.6231  >8 levels 52.63%
D1 removed (R4_D1_novae)    PSNR 34.01 dB  SSIM 0.9040  >8 levels  7.61%
```

So at steps 8 the round-trip is worth roughly **a fifth** of what the steps change
was worth, **and it points the other way**: removing it puts bright blobs and
fine-band energy back, which is the direction the owner described as "crunchier"
when he reverted it at steps 30. The mechanism is unchanged — `#617` re-samples
at denoise 0.25 from whatever it is handed, and every later pass compounds it.

### A cross-run comparison I am NOT making, and why

The previous A/B measured this at steps 30 and reported full-frame PSNR 30.63 dB
/ face crop 28.64 dB. My instrument reproduces its full-frame figures exactly
(30.63 dB, mad 4.264, 83.91 % > 1 level, 15.75 % > 8 levels against its published
30.63 / 4.26 / 83.9 % / 15.7 %), so the instruments agree. **But the two A/Bs are
not on the same image.** That run's prompt lacked the `light freckles across her
nose and cheeks, ` clause, and that one clause moves the whole composition — the
face detector puts its face at `(984, 413)-(1638, 1304)` and mine at
`(1060, 1180)-(2000, 2360)`:

```
WS4 A_baseline   conf=0.8846 xyxy=(984.3, 413.0, 1638.5, 1303.7)  wh=(654.2, 890.7)
R4 C_steps_08    conf=0.9039 xyxy=(797.3, 694.5, 2231.1, 2693.8)  wh=(1433.8, 1999.3)
```

Different scenes. **The 30.63 dB and the 34.41 dB must not be subtracted from
each other.** The scale table above is the controlled comparison; it stays inside
one composition.

### Verdict — **left in place. No commit. Here is exactly what I am and am not saying.**

**What I measured:** removing the round-trip at steps 8 still changes the face,
and the change goes in the direction the owner rejected — bright blobs +6.2 %,
fine-band energy +7.6 %, i.e. it partially undoes what `2e4e8e9` was applied to
achieve. It is about a fifth the size of that change.

**What I am not saying:** that I looked at it and it is worse. `CLAUDE.md`
forbids that and I have not done it. "Blobs up 6.2 %" is a direction, not a
verdict, and the previous run's own experience is that this class of metric can
rise while the thing being counted disappears.

**Why the graph is unchanged:** redundant in intent, load-bearing in effect —
unchanged at steps 8, only smaller. The owner's standing decision (`73f3d5c`) was
made on this same evidence at steps 30, his instruction for this run was *"If
removing it costs face quality, say so and leave it"*, and the objective deltas
point the same way his eye did. Overturning that on a judgement I am not
permitted to make would be the higher-risk option.

**I am not claiming to have judged the image** — `CLAUDE.md` forbids that and I
have not done it. The pair above is the deliverable and the look is his. If he
prefers the crunchier face now that steps 8 has cleaned up the blobs, `423df24`
is still in history as the exact patch, and its graph diff (2 nodes removed, 1
input re-pointed, nothing else across 85 shared nodes) is reproduced above.

---

## 2 — `#106` driving the face pass at denoise 0.8 with placeholder text

### Both already-established points confirmed against the current file

**(a) There is no typo.** `#106 CLIPTextEncode`, title `"Face Detailer Prompt"`,
in `5. Face & Mouth Detail (Z-Image)`:

```
widgets_values: ['TRIGGER, PROMPT FOR YOUR MODEL']
in[0] clip link=192      out[0] CONDITIONING links=[199]  ->  #114.inputs[4] positive
```

The file says **`PROMPT`**. `AUDIT.md` A4's and `QUESTIONS.md` Q2's "the typo
`PROMT`" describes a string that is not in this file.

**(b) It is documented buyer-facing template text, not an oversight.** Root
`#649 MarkdownNote`, verbatim:

> ## 3 · One thing you must fill in
> Open **5. Face & Mouth Detail**, find *Face Detailer Prompt*, and replace
> `TRIGGER, PROMPT FOR YOUR MODEL` with your LoRA's trigger word and a short
> description of your character. That node drives the single most expensive
> pass in the workflow.

The note quotes the placeholder with the same spelling the node carries.
**Overwriting the node's text would desynchronise it from its own instructions,
so I did not.**

### Why it still matters at cfg 1 — the sharpened question

`#114 FaceDetailer`:

```
widgets_values (29): [1024, True, 1024, 1111111, 'fixed', 8, 1, 'euler_ancestral',
                      'kl_optimal', 0.8, 18, True, True, 0.5, 10, 3, 'center-1',
                      0, 0.93, 0, 0.7, 'False', 10, '', 1, False, 20, False, False]
```

index 5 `steps` = **8** (the change this run applied), index 6 `cfg` = **1**,
index 9 `denoise` = **0.8**.

At cfg 1 the negative is never evaluated — `comfy/samplers.py:370-373`:

```python
def sampling_function(model, x, timestep, uncond, cond, cond_scale, model_options={}, seed=None):
    if math.isclose(cond_scale, 1.0) and model_options.get("disable_cfg1_optimization", False) == False:
        uncond_ = None
    else:
        uncond_ = uncond
```

So `#106` is **the only conditioning that reaches the model** in the pipeline's
most expensive pass, which is re-generating the face at denoise 0.8. A weak
positive is worth more here than it would be on a cfg>1 model.

### The arms

Two, so that "the placeholder is weak conditioning" and "the placeholder's own
tokens are actively steering" can be told apart — a distinction one arm cannot
make:

| arm | `#106.text` |
|---|---|
| `R4_base` | `TRIGGER, PROMPT FOR YOUR MODEL` (shipped) |
| `R4_D2_real` | `a young woman with light freckles across her nose and cheeks, natural skin texture with visible pores, detailed eyes, photorealistic portrait photograph, 85mm lens` |
| `R4_D2_empty` | `""` |

**I did not invent character text for the shipped file and this arm is not a
proposal to.** The `R4_D2_real` string is the *description* half of what `#649`
asks a buyer for; the trigger-word half is deliberately absent because no LoRA is
loaded in any arm, so a trigger token would be meaningless. Both arms are scratch
copies under the session scratchpad.

Graph diffs against the baseline — one input each, nothing else:

```
R4_base vs R4_D2_real   — 1 difference: value_changed 620:106.inputs.text
R4_base vs R4_D2_empty  — 1 difference: value_changed 620:106.inputs.text
```

### What the placeholder is actually worth at steps 8 — rendered

All three arms healthy (`flat_frac` 0.0000; median RGB [141,99,81] / [142,100,82]
/ [141,99,82]). **The arm that returned a black image on a previous run came back
clean here** — consistent with `HANDOFF.md` §7.1's conclusion that that failure
was server model state and not the prompt.

**vs `R4_base` (the shipped placeholder):**

| | full frame | face crop |
|---|---|---|
| `R4_D2_real` PSNR / SSIM | 46.92 dB / 0.9961 | **39.36 dB / 0.9799** |
| `R4_D2_real` mean abs diff | 0.365 levels | 1.493 levels |
| `R4_D2_real` > 1 level | 13.78 % | 57.99 % |
| `R4_D2_real` **> 8 levels** | 0.19 % | **1.28 %** |
| `R4_D2_empty` PSNR / SSIM | 46.60 dB / 0.9966 | **37.86 dB / 0.9786** |
| `R4_D2_empty` mean abs diff | 0.223 levels | 1.054 levels |
| `R4_D2_empty` > 1 level | 5.63 % | 26.77 % |
| `R4_D2_empty` **> 8 levels** | 0.26 % | **2.07 %** |

and the two edits against each other, `R4_D2_real` vs `R4_D2_empty`:
full 44.82 dB / 0.9949 / 0.35 % > 8 levels; face **36.71 dB / 0.9715 / 2.51 %
> 8 levels**.

**The pair to look at, 1:1, three tiles at 940×1180:**
`results/r4/D2_face_sheet1of1.png`.

### The result, and it is not the one the framing predicts

Put beside the other two changes measured on this exact composition with this
exact instrument, face crop, pixels moving more than 8 levels:

```
steps 30 -> 8      (already applied, 2e4e8e9)   52.63 %
remove VAE round-trip  (D1)                      7.61 %
#106 placeholder -> real description  (D2)       1.28 %
#106 placeholder -> empty             (D2)       2.07 %
```

**At `#114` steps 8 the text in `#106` barely moves the output.** Every pairwise
distance in the three-way is between 1.3 % and 2.5 % of face-crop pixels beyond 8
levels, and no state dominates — the placeholder is not measurably worse than a
real description; if anything an *empty* box is slightly further from the
placeholder than a real description is. Mean absolute difference over the face
crop is **1.0–1.7 levels**, i.e. mostly sub-visible amplitude spread broadly.

Two things that keep this from being an artefact:

* **The noise floor on this pipeline is zero, not small.** `R4_base` came back
  bit-identical to the same graph rendered in a different session hours earlier
  (max abs diff 0 across 2688×3456, §0 Control 2). So a 1.28 % reading is real
  signal, however small. This is the one place the usual "48.7 dB run-to-run
  noise" caveat does *not* apply, and it is why these small numbers can be
  reported at all.
* **The change lands where the wiring says it must.** `#106` feeds only
  `#114.positive` (link 199), and the effect is ~7× stronger inside the face crop
  than over the full frame (1.28 % vs 0.19 %). If the plumbing were different
  from what §2 describes, that ratio would not hold.

I am **not** offering a mechanism for why denoise 0.8 moves so little. I did not
measure one, and guessing at it is exactly what this project's history punishes.

### Verdict — **not an oversight; and at steps 8 the placeholder is measurably *different* from a real prompt but not measurably *worse*. No content change. No commit.**

* `AUDIT.md` A4's "typo" does not exist in this file.
* The placeholder is documented buyer-facing template text and `#649` quotes it
  verbatim; overwriting it would break the note. **I did not.**
* The cfg-1 concern is real as *stated* — `#106` genuinely is the only
  conditioning `#114` sees — but the render says that conditioning is worth about
  1–2 % of the face at 8 steps. The sharpened worry ("a placeholder positive is
  more damaging here than on a cfg>1 model") is **not supported at steps 8**.

**Limit, and it is the important one:** every arm above has **no LoRA loaded**.
A buyer's `#106` carries a *trigger word* whose whole job is to activate a LoRA,
and with `#116` at the shipped `"None"` a trigger token can do nothing by
construction. So the arms above measure the *description* half only. §2b covers
the LoRA case.

### One structural fact that bounds what `#106` can ever do — WS4's finding, re-confirmed here

`#106` is encoded by the **raw** text encoder, not the LoRA'd one. Read from the
current file and from the submitted API graph:

```
sg5 link 192: 110[0] -> 106[0]  CLIP          #110 CLIPLoader qwen.safetensors (lumina2)
sg5 link 191: 110[0] -> 105[0]  CLIP
sg5 link 209: -10[3] -> 114[2]  CLIP          #114's clip comes from the subgraph input...
620:106 CLIPTextEncode : {"text": "...", "clip": ["620:110", 0]}          <- raw
116 Lora Loader Stack  : {..., "model": ["620:113",0], "clip": ["620:110",0]}   <- the LoRA'd CLIP
```

So the ZIT LoRA stack `#116` produces a LoRA'd CLIP, `#114` receives it, and
`#106` — the node that actually encodes the buyer's trigger word — does not.
`#114`'s own `clip` is dead weight besides: `ComfyUI-Impact-Pack` only re-encodes
with it when `wildcard_opt` is non-empty, and `#114.wildcard` (widget index 23)
is `""`.

**Consequence:** a buyer's Z-Image LoRA reaches the UNet of the face pass and the
text encoder of none of it. Whatever the trigger word is worth here, it is worth
it through the base encoder's embedding of that token only. This is WS4's
finding, verified against the current file, and it is **not** something I changed
— rewiring `#105`/`#106` to the subgraph input means editing a subgraph IO
`linkIds` array, which is the class of edit that produced this project's shipped
browser blocker, for zero benefit in the shipped `"None"` configuration.

---


## 2b — the LoRA case, and the wrong conclusion I nearly published

The §2 arms have no LoRA loaded, so they measure only the *description* half of
what `#649` asks a buyer to write. `results/face/arms/L1b_steps08_loras` is the
buyer's actual configuration — `lunaskye` on `#618`, `luna` on `#116`, `#114` at
steps 8 — with `#106` **left at the placeholder**, and it rendered clean earlier
today (`5dc3b3e6`, 189.3 s). So one render answers the buyer's question: branch
that arm's already-submitted API graph and change `#106` alone.

```
L1b_steps08_loras  vs  R4_D2_loras_filled
RESULT: DIFFERENT — 1 difference(s): value_changed=1
  value_changed  620:106.inputs.text
    A: "TRIGGER, PROMPT FOR YOUR MODEL"
    B: "luna, a young woman with light freckles across her nose and cheeks, natural skin ..."
```

### It crashed — and the obvious reading of that is wrong

```
prompt 43a16c5f  status: error  after 304.6 s
  node_id 622:403   node_type MaskBoundingBox+   RuntimeError
  "min(): Expected reduction dim to be specified for input.numel() == 0."
  ComfyUI_essentials/mask.py:184   x1 = max(0, x.min().item() - padding)
  current_inputs.mask = tensor([[[0., 0., 0., ..., 0., 0., 0.]]])     <- an all-zero mask
```

One input changed, and the graph died. The available conclusion — *"filling in
the face prompt with LoRAs loaded crashes the pipeline"* — is the same shape as
the near-miss `HANDOFF.md` §7.1 records from the previous run (*"a near-miss
report that the buyer's LoRAs crash the graph"*). So it got a control instead of
a write-up.

**Control 1 — byte-identical resubmission of the arm that had worked.** Same
bytes, same graph, clean at 02:59 today. It **failed identically**:

```
d18d8f31  R4_CTL_loras_placeholder  error 270.8 s   622:403  RuntimeError
```

**Control 2 — a different agent's unrelated prompt.** Stronger, because it shares
none of my inputs. `8e8aa729` is not mine and I did not build it. It failed the
same way, between my two failures:

```
13:15:53  c2448308  success  103.7 s
13:17:37  43a16c5f  error    304.6 s   <-- 622:403   (mine, the filled prompt)
13:22:43  8e8aa729  error    389.1 s   <-- 622:403   (NOT mine)
13:29:13  d18d8f31  error    270.8 s   <-- 622:403   (mine, the placeholder control)
```

Everything up to 13:15:53 succeeded; everything from 13:17:37 failed, across two
different agents and three different graphs, at the same node.

**So the crashes *in that window* are server state, not the prompt** — and in
particular the one that looked like my change is not attributable to it. (The
post-`/free` picture is different and is taken up two headings down; this
paragraph settles the 13:17–13:37 block only.) `HANDOFF.md` §7.1 is confirmed
again, with two things added to it:

1. **It reproduced today**, hours after the `/free` that cleared it last time.
2. **It does not always look like a flat grey face.** Here the same underlying
   fault — the face destroyed upstream — surfaced as a *hard crash* at the Eyes
   stage, because `622:403 MaskBoundingBox+` has no empty-mask guard and
   `ComfyUI_essentials/mask.py:184` calls `.min()` on an empty tensor. `HANDOFF.md`
   §7.1 lists that as a *latent* defect "no claim about triggers". **It is no
   longer latent — this is it firing, three times.**

I am making **no claim about what put the server into that state.** My arm was
the first prompt after it went bad, which is a coincidence of ordering, not
evidence — and treating it as evidence is exactly the error this control existed
to catch.

### `POST /free` recovered it — and the answer to "is a restart needed" is no

```
13:33:44 -> 13:37:24  cbc1fa2b  error    622:403     <-- STARTED BEFORE the /free
        [ POST /free {"unload_models": true, "free_memory": true}  -> HTTP 200,
          issued while cbc1fa2b was the running job; vram_free 50.6 GiB after ]
13:37:31 -> 13:41:30  b0ad2862  SUCCESS  239.5 s     <-- not mine
13:41:31 -> 13:46:18  110d0594  SUCCESS  286.9 s     <-- mine: byte-identical to the arm
                                                         that failed at 622:403 pre-free
```

`cbc1fa2b` was already executing when I POSTed, so it is **not** evidence about
the remedy in either direction — and my `/free` may well have landed mid-render
on it. **Every prompt that *started* after the free succeeded**, including
another agent's. `HANDOFF.md` §7.1's advice — free, do not restart — holds.

And the recovery is exact, not merely "it ran". `110d0594`'s image against the
**02:59 render of the same graph**, from before the server ever went bad:

```
R4_CTL_loras_placeholder_postfree  vs  L1b_steps08_loras (02:59)
  max_abs_diff 0   psnr inf   ssim 1.0        flat_frac 0.0034, luma_sd 37.93
```

Bit-identical across 2688×3456. So the freed server is not approximately
recovered, it is back to producing the same bytes it produced before the fault.
That is the strongest form this test can take.

### RESOLVED — and it is not what the pre-`/free` evidence suggested

With the server freed, the two arms were run **alternately**, and the alternation
is the whole result. Every row below is on a server whose health is attested by
**sixteen** unrelated successes, most of them other agents' prompts:

```
13:37:31  b0ad2862  success  239.5      (not mine)
13:41:31  110d0594  SUCCESS  286.9   <== #106 PLACEHOLDER + LoRAs
13:46:19  94552d00  ERROR    173.4   <== #106 FILLED + LoRAs      622:403
13:49:18  11a4670d  success  388.9      (not mine -- R1)
13:55:54  ec02909f  success  270.5      (not mine -- R1)
14:00:25  b6769fc9  success  150.0      (not mine -- R1)
14:02:56  8eae3e66  success  190.1      (not mine -- R1)
   ... 7 further successes, 14:06:07 - 14:29:07, none of them mine ...
14:34:23  3ffb8610  SUCCESS  189.3   <== #106 PLACEHOLDER + LoRAs
14:37:38  4a422a94  success  262.6      (not mine)
14:42:02  81c9e758  ERROR    172.9   <== #106 FILLED + LoRAs      622:403

since the /free: 16 success, 2 error.  BOTH errors are the filled-prompt arm.
```

**Placeholder 2/2 clean. Filled 2/2 crash. One input apart.** Both crashes are
the same node, the same exception, the same all-zero mask:

```
94552d00  622:403 MaskBoundingBox+ RuntimeError  mask all-zero: True   173.4 s
81c9e758  622:403 MaskBoundingBox+ RuntimeError  mask all-zero: True   172.9 s
```

The two failures are **0.5 s apart in execution time**. That is a deterministic
path terminating at the same point, not a stochastic event.

So my earlier reading — "server state, not the prompt" — was correct **for the
13:17–13:37 window** and **wrong as a general conclusion**. Both were true at
once: the server really was poisoned then (another agent's prompt failed too, and
`/free` restored bit-identical output), *and* this arm has a genuine, repeatable
trigger underneath it. Settling the first did not settle the second, and it took
alternation on a proven-healthy server to separate them.

### What is established, and what is not

**Established.** In the owner's own configuration — `lunaskye` on `#618`, `luna`
on `#116`, `#114` at steps 8 — replacing `#106`'s placeholder with a filled
character prompt crashes the pipeline at `622:403 MaskBoundingBox+`, reproducibly,
on a healthy server. **Filling that box in is the buyer's first documented
action**: root `#649` §3 says *"replace `TRIGGER, PROMPT FOR YOUR MODEL` with your
LoRA's trigger word and a short description of your character."*

**Not established, and I am not implying it.**

* **That any filled prompt does this.** I tested one string,
  `"luna, a young woman with light freckles across her nose and cheeks, natural
  skin texture with visible pores, detailed eyes, photorealistic portrait
  photograph, 85mm lens"`.
* **That it needs the LoRAs.** But note `R4_D2_real` in §2 — a filled `#106`
  **without** LoRAs and without the `luna, ` trigger prefix — rendered **clean**.
  So the no-LoRA case does not crash. Two variables differ between that arm and
  this one (LoRA stacks loaded, and the `luna, ` prefix) and I have **not**
  isolated which matters.
* **That the prompt is the defect.** **[I]** The defect is more likely the
  missing guard: `622:403 MaskBoundingBox+` calls `.min()` on an empty tensor
  (`ComfyUI_essentials/mask.py:184`) whenever the Eyes stage's face mask comes
  back empty, so *anything* that makes the face undetectable is a hard crash
  rather than a degraded image. The poisoned server reaches that state one way;
  this prompt reaches it another. On that reading the prompt is a trigger, not
  the fault, and there are likely other triggers.

### Why this is worth a decision before the pack ships

A buyer who follows `#649` §3 with a LoRA loaded hit a hard crash in 2 of 2
attempts here. Even if the trigger turns out to be narrower than that sentence
makes it sound, **the Eyes stage converting an undetectable face into a
`RuntimeError` instead of a degraded image is a defect in its own right**, and it
is the thing that turns any such trigger into a dead render rather than a bad
one. `HANDOFF.md` §7.1 already lists the missing guard; what is new is that it is
now reachable from the documented happy path, not only from a poisoned server.

Evidence: `results/r4/R4_D2_loras_filled_postfree/`,
`results/r4/R4_D2_loras_filled_confirm/`,
`results/r4/R4_CTL_loras_placeholder_postfree/` (with its image),
`results/r4/R4_CTL_loras_placeholder_final/` (with its image).

---

## Summary — what shipped, and what did not

| defect | verdict | workflow changed? |
|---|---|---|
| **1** `#597`→`#616` VAE round-trip | **real, and still load-bearing at steps 8**. Removing it moves the face in the direction the owner rejected (blobs +6.2 %, fine-band +7.6 %), at ~⅕ the size of the steps change | **no** — left in place, on his standing decision `73f3d5c` and his instruction for this run |
| **2** `#106` placeholder at denoise 0.8 | **not an oversight** (documented template text, no typo), and at steps 8 **measurably different from a real prompt but not measurably worse** — 1.28 % of face-crop pixels beyond 8 levels | **no** — no content change, and none warranted |
| **3** `#600` reseeding itself | **FALSE.** `#600` reads `"fixed"`; the residual WS4 found (`#592`) was fixed in `a01ae3a` and is still fixed; **zero occurrences of `randomize` in the file**; the exposed seed is `"fixed"`. The graph *is* reproducible from the seed it exposes | **no** — nothing left to fix |
| **4** `SetUnionControlNetType` in parallel | **MOOT.** The entire path is gone — 0 matches for ControlNet / IPAdapter / Depth / SetUnion across all 109 nodes; the only two `controlnet` strings are pack metadata on a FaceMesh preprocessor | **no** — nothing to repair |

**`OFMTech-NSFW/OFMTech_NSFW.json` is untouched by this run.** Two of the four
did not exist, and the two that do are both owner-judgement calls where the
lower-risk option is the graph as it stands. Nothing here needed a code change to
be worth doing — the deliverables are the verdicts and the pairs.

**One thing came out of this that was not on the list of four, and it is the most
consequential thing I found: §2b.** With the owner's LoRAs loaded, filling `#106`
in the way root `#649` §3 instructs the buyer to crashes the pipeline at
`622:403 MaskBoundingBox+`. **Reproduced 2/2, against the placeholder's 2/2
clean, alternated on a server attested by 16 unrelated successes**, both failures
on the same node with the same all-zero mask and execution times 0.5 s apart.

It is **not** a defect in `#106` and I am not proposing a content change. **[I]**
The fault is most likely the missing empty-mask guard — `ComfyUI_essentials/mask.py:184`
calls `.min()` on an empty tensor, so *anything* that leaves the Eyes stage's face
mask empty is a `RuntimeError` instead of a degraded image. The prompt is one
route in; the poisoned server is another; there are probably more. What is new is
that it is now **reachable from the documented happy path**, not only from a
broken server. That needs a decision before the pack ships, and it is not mine to
make.

### Documents still carrying claims this run contradicts

Not my files; listed so whoever owns them can act.

* `AUDIT.md` **A21** — records `#600 control_after_generate` as `"randomize"`,
  tagged **[F]**. The file reads `"fixed"`. The rest of that row (`578361683541099`,
  "no `seed` input slot") is correct.
* `AUDIT.md` **A4** / `QUESTIONS.md` **Q2** — quote `"TRIGGER, PROMT FOR YOUR
  MODEL"` and call `PROMT` "the typo". The file says `PROMPT`; `grep -c PROMT`
  returns 0.
* `AUDIT.md` **A5** / `QUESTIONS.md` **Q3** — describe a ControlNet path that
  does not exist.
* `CLAUDE.md` / `MAP.md` §0 — 132 nodes, 24 bypassed, seven stages all named
  "Dont touch!!!". The file is **109 nodes**, one bypassed (root `#623`), stages
  already named.

`STATE.md` already records all four of these corrections; the source documents do
not.

### What I would hand a pod session next, on this list only

Nothing on defects 3 and 4 — they are closed and need no GPU.

For defect 1, the one thing I could not do here: **a controlled timing number.**
Take `R4_base` and `R4_D1_novae` on an idle server, `POST /free {"unload_models":
true, "free_memory": true}` before each, confirm `execution_cached: 0` in
`/history` for both, and discard any pair whose cached-node sets differ. Two VAE
operations is the whole of the saving and it may well be inside the noise; the
point is to have the number rather than the argument. **This does not change the
verdict** — the verdict is a look, and the look says leave it.

**[I]** WS4 derived the round-trip's working resolution as **1432×1840** (896×1152
base → `#593` 4× → `#595 ImageScaleBy` lanczos 0.4 → `round()` to 1434×1843 →
`#594 VAEEncode` cropping each dim to a multiple of 8 at `comfy/sd.py:847-857`).
I re-read `nodes.py:1903-1904` and `sd.py:847-857` and the arithmetic follows,
but **I did not measure it** — nothing in my arms taps that tensor. Treat the
figure as inference, not as a reading. It does not bear on the verdict either
way.
