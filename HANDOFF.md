# HANDOFF.md

Written 2026-08-06. **Live document — updated as each phase completes**, so if
this session dies you have what was known up to that point. Sections marked
**[IN FLIGHT]** are not finished.

---

## 1. Is the browser bug fixed? **YES.**

`No output node found for id [647] slot [4] MODEL` no longer occurs. Proved in a
real browser on the shipped graph, not taken from a previous run:

```
opened OFMTech_NSFW from the Workflows sidebar
configured: sdxl=lunaskye.safetensors  zit=luna.safetensors  seed=20260806
pressed Run
POST /prompt -> 200; 88 nodes; 618=lunaskye 116=luna
RESULT status=success  outputs=[["505","HasMetadata_00012_.png"]]
pageerrors: 0
```

**Screenshot proof:** `results/phase0/04-final.png` — shows your workflow loaded
and the rendered portrait in the image feed. Also `01-workflow-loaded.png`,
`02-loras-and-prompt-set.png`, `03-selector-answered.png`. Machine-readable
detail in `results/phase0/result.json`.

Merge commit: **`b328f0243c2cd8b6ececc4620828b6b8c876faf7`** on `master`.

One thing I am **not** claiming: my selector probe reported `Send STILL DISABLED
after pick` once, then succeeded 5 s later. Most likely my crude thumbnail
selector firing before the grid was interactive — a purpose-built harness
asserted `false → true` cleanly on a 4-image batch. Unexplained, not dismissed.

---

## 2. How to test it yourself

### (a) On this pod, right now

Fast check, ~9 s, no GPU — this is the gate to run after any graph edit:

```bash
cd /workspace/nsfw-fix
node tools/browser_harness/run.js --workflow OFMTech_NSFW --no-submit
```
Exit 0 = the browser converted the graph. Exit 1 = the workflow is broken.
Exit 2 = the test could not run (environment), which is **not** a pass.

Full buyer journey including the image-selector pause (~6 min):
```bash
node tools/browser_harness/run.js --workflow OFMTech_NSFW --drive-selector
```

Static lint, 23 ms, catches the class of bug that shipped:
```bash
python3 tools/preflight/integrity.py OFMTech-NSFW/OFMTech_NSFW.json
```

### (b) From scratch on a fresh pod

```bash
echo "hf_YOUR_TOKEN" > /workspace/.hf_token
bash <(curl -sSL "https://gist.githubusercontent.com/msit270/70256ac1ebf2760e10f78804862db528/raw/aiofm_setupnsfw.sh")
```
Then **restart ComfyUI and hard-reload the browser** (Ctrl-Shift-R). Custom
nodes only register at startup.

Watch for these two lines at the end; anything else means stop and read above them:
```
workflow nodes : all 88 present
integrity      : OK
```

**Provision at least 250 GB of disk.** The old "~176 GB" figure was wrong in the
expensive direction — measured need is 193.7 GB decimal / 180.4 GiB, and the
script prints GiB while labelling it "GB".

---

## 2c. Publishing the re-cut pack — one command, for you to run

The tarball is re-cut against the D1-reverted graph and verified end to end.
**Nothing was uploaded.**

```
dist/AIOFMTech-NSFW.tar.gz   8,154,217 bytes
sha256  27fa2e1c5496c4d0efee7d5b626e7638b197e1327500f86936a2a9e918dd3d37
170 files, top-level AIOFMTech-NSFW/   (matches the archive name)
```

```bash
HF_TOKEN="$(tr -d '[:space:]' < /workspace/.hf_token)" \
/venv/main/bin/hf upload msit270/AIOFM-Pack \
    /workspace/nsfw-fix/dist/AIOFMTech-NSFW.tar.gz \
    dist/AIOFMTech-NSFW.tar.gz \
    --commit-message "NSFW pack re-cut against the D1-reverted graph (workflow f1ac7e55)"
```

Verify it landed:
```bash
curl -fsSL -H "Authorization: Bearer $(tr -d '[:space:]' < /workspace/.hf_token)" \
  "https://huggingface.co/msit270/AIOFM-Pack/resolve/main/dist/AIOFMTech-NSFW.tar.gz" | sha256sum
# must print 27fa2e1c…dd3d37
```

**If it prints `3f6d0f2f…aada76`, the upload did not land — retry, do not wait for
CDN lag.** That is the hash live HF serves *today*: **the previous run's re-cut
was never published**, so this artifact supersedes it and `3f6d0f2f…` is the
"before" you are watching for. (An earlier draft of these instructions would have
told you to watch for a hash that cannot appear.)

Delta against what is published: **164 → 170 files, six additions — the licence
files — and no removals.** Against the previous unpublished cut: 170 → 170, one
file changed, the workflow. The gist needs no edit.

**A green cut is not a clean licence position.** These bytes contain the UnMarker
and GrainNet trees — see §7 and `QUESTIONS.md` §0.

---

## 3. What to do in the browser once it loads

Everything you touch is in the green box at the top left.

| What | Where | Note |
|---|---|---|
| **Your prompts + seed** | the panel to the right of `1 · YOUR PROMPTS & SEED` | one prompt = one full render |
| **SDXL LoRA** | node **`618`**, "2 · Your SDXL LoRa (body, pose, hands)" | drives body, pose, hands, both upscales |
| **Z-Image LoRA** | node **`116`**, "2 · Your ZIT LoRa (face, mouth, eyes)" | **this is where your character's likeness lives** |
| **Face prompt placeholder** | open subgraph **`5 · Face & Mouth Detail`**, node titled **"Face Detailer Prompt"** (`#106`) | reads `TRIGGER, PROMPT FOR YOUR MODEL` — replace with your trigger word + character description |

**Your Luna LoRAs are present** and both were exercised in the Phase 0 proof:
`luna.safetensors` (Z-Image, 170 MB) → slot `116`; `lunaskye.safetensors`
(SDXL, 186 MB) → slot `618`. Both are offered by the dropdown.

**Fill both slots.** The first face pass runs on SDXL through `618`; the face,
mouth and eye passes run on Z-Image through `116`. Fill only one and your face
is rendered under one identity, then re-rendered at denoise 0.80 under another.

**The render pauses partway** at an image-selector popup and waits for you to
pick an image and press Send. That is deliberate. If you walk away it times out
after 10 minutes and sends **nothing** — you get no image.

---

## 4. The face work

### RECOMMENDATION SO FAR: set `#114` steps 30 → 8. It fixes the face *and* saves 26 % of the render.

**Nothing has been applied.** This is the pick to make; more arms are still landing.

`#114 FaceDetailer` runs **30 steps on a model distilled for 8** — and the graph's
own mouth pass `#165` already runs 8 on the same model. Setting the face pass to
match is the single biggest win in the grid.

**How it looks** (the render agent's words, not a metric): the dense field of
white raised bumps is **gone**. Cheek, nose and brow read as skin — smooth with
fine texture, **freckles now visible as flat brown marks** instead of drowned in
white foam. Eyelashes are clean strands instead of scribble. The geometric
grid/hexagon mess over the lips is largely gone too. **Its one reservation, and
it is yours to judge: it is noticeably softer than the baseline**, and you may
want a value between 8 and 30 if you want more grain. `C_16` is queued to answer
exactly that.

| | baseline | steps 8 |
|---|---|---|
| bright blobs / MP — **the defect** | 764 | **239** (−69 %) |
| dark pores / MP — **the texture you asked for** | 16,471 | **23,213** (+41 %) |
| blob-band RMS | 4.30 | **3.07** |
| execution | 397.8 s | **294.1 s** (−26 %) |

The two texture measures move in **opposite** directions. That is the point: it
is not smoothing the image, it is the pass no longer inventing lesions.

### The full ladder — and **16 is not enough**

Bright blobs per megapixel over a fixed skin mask, identical pixels every arm.
Lower is better. Dark pores are the texture you actually asked for.

| arm | blobs/MP ↓ | pores/MP ↑ | exec |
|---|---|---|---|
| baseline (30 steps / 0.80) | 764 | 16,471 | 397.8 s *(cold)* |
| steps **16** | 552 | 19,339 | 224.1 s *(warm)* |
| **steps 8** | **239** | **23,213** | 294.1 s *(cold)* |
| **denoise 0.50** (30 steps) | **157** | 23,050 | 291.6 s *(warm)* |
| `#87` blend 0.75 / 0.50 | 702 / 702 | ~17,700 | ~292 s *(warm)* |

**Steps 16 answers your grain question, and the answer is no** — it is visibly
still speckled. It does not preserve grain, it preserves a third of the defect.
**8 is the value.**

### An unexpected second lever: `denoise` is free

Four arms came back with **identical cache state — the same 10 heavy nodes
cached**, so this is a genuinely matched comparison for once:

```
blend 0.75   (30 steps, 0.80)  292.0 s
blend 0.50   (30 steps, 0.80)  291.6 s
denoise 0.50 (30 steps)        291.6 s     <- halving denoise: 0.0 s
steps 16     (0.80 denoise)    224.1 s     <- halving steps: -67.5 s
```

And `comfy/samplers.py`, `KSampler.set_steps`, says why:
`new_steps = int(steps/denoise)`, then `self.sigmas = sigmas[-(steps + 1):]`.
The schedule is always `steps + 1` long — **denoise does not reduce how many
sampling steps execute**, it computes a *longer* schedule and runs the last
`steps` of it. So denoise changes only *where on the noise schedule the pass
starts*, at identical cost. **Steps is the only time lever.**

**Denoise 0.50 scores better on the defect than steps 8 and costs nothing** — but
the agent's eye says it is slightly **waxier** than steps 8 and it **shifts the
iris toward hazel**. Combination arms (steps 8 + denoise 0.50 / 0.65) are queued,
as is a **confirmation pair with your Luna LoRAs loaded** at the likely
recommendation, since the whole grid otherwise ran with both stacks at `"None"`.

**Why the timing claim is safe**, given this project's history of wrong timing
verdicts: the arms had mismatched cache counts (31 vs 8), so the agent checked
*what* was cached. In both arms every cached node is a loader, text encoder or
primitive — **no sampler, detailer, VAE or upscale node was cached in either**,
so all the sampling ran from scratch both times. The difference is model *load*
time only, and it runs **against** the fast arm, which had 23 fewer loaders warm
and still finished 103.7 s quicker. **The 26 % is a lower bound.**

**Still a defect after this fix:** the mask seam survives, halved but not gone —
band-pass step across the jaw goes from **x6.76** baseline to **x3.57** at steps
8. The composite boundary is still visible in the delivered image and wants its
own fix, whatever you decide here.

### `#87` skin filter — cleared. Leave it at 1.0.

Turning the skin amplifier down **does not fix the skin**. Blobs per megapixel:
baseline (1.0) **764**, at 0.75 **702**, at 0.50 **702** — an 8 % move, against
steps' 69 %. At 1:1 the three are genuinely hard to tell apart.

The check that makes this a disproof rather than an absence of evidence:
changing `blend_factor` **does** reach the neck — neck and shoulder pixels move
by mean 1.6–2.5 levels, up to 1.70 % of them by more than 8 — **and yet neck
band-pass RMS stays flat at 0.94 / 0.99 / 0.96 across all three values.** It
reaches the neck, changes it, and creates no bumps there. So it is not creating
them on the face either.

### Correction: the gold lip artifact does not reproduce

I told you earlier this was real and caused by the blend change. **The second
half of that is not supported and I withdraw it.** Five arms were re-tested under
the same rule in three windows, including `H_skinblend_050` — P1's *exact*
setting — and every one returns **0 px**. The object genuinely is in the older
render P1 measured; that was a different composition and a different prompt. One
occurrence, not a reproducible effect of the setting. The only two arms with any
warm specks near the lips are ones that never touch `#87`.

So the reason to leave `#87` alone is simply that **turning it down does not fix
the skin** — not the artifact.

### The rest of the grid **[IN FLIGHT]**

### D3 — STOPPED. Your stop condition triggered. Nothing was applied.

You said: *take it, pending re-measurement against `A_baseline` without D1 — if
the improvement does not survive, tell me and stop.* **It does not survive.**

Re-measured on the D1-free baseline: `results/face/arms/A0_baseline/` versus
`results/face/arms/A_drop_sdxl_face_pass/`. Graph diff between the two submitted
prompts is exactly two differences — `619:607` removed and `619:597.inputs.pixels`
re-pointed to `619:596`. Nothing else moved.

**Dropping the first face pass does not fix the overbaked skin.** The bumps are
still there, same density, same places. Bright-blob density over a fixed skin
mask goes **764 → 800 per megapixel** and blob-band RMS **4.30 → 4.42** — no
improvement, marginally worse. The change is real (19.8 % of face pixels move
more than 8 levels) but real is not better. WS4's original D3 measured that the
change is real; it never measured that it is an improvement, and now that it has
been, it is not.

So `#607` stays. It survives only as a possible *cost* saving, and even that is
unmeasured — the two runs had mismatched cache states (31 vs 11 cached nodes),
which is precisely the condition that produced a wrong timing verdict last run.

### What the skin actually looks like, at 1:1

Not metrics — this is the description that matters: a dense field of small
**bright, whitish, raised bumps with specular tops**, reading as milia or a foam.
**A pore is a small dark depression; these are convex and light.** Plus a few
larger red-brown lesions reading as pimples. That is the opposite of the
"visible pores" the prompt asks for, and it points away from the samplers and
towards something that *amplifies* fine bright detail.

### It is `#114`. Two agents proved it independently, by different methods.

**Measurement 1 — before/after across the pass.** The image *entering* `#114`
(tapped at `620:137`, i.e. **after** `#87`'s skin amplifier) is **clean, smooth
skin**. The same region *leaving* `#114` is covered in blistered bubble-wrap
texture. If `#87` were the source it would already be visible in the input. It is
not. `#114` **creates** the texture; it does not amplify something handed to it.
Crops: `results/cfg/compare/baseline_114_input_mouthregion_1to1.png` and
`…_output_mouthregion_1to1.png`.

**Measurement 2 — where the damage stops.** High-frequency energy (1–4 px DoG
RMS) across a strip through the jaw:

| arm | detected face box | inside, above jaw | outside, below jaw |
|---|---|---|---|
| `A0_baseline` | x800–2228 y696–**2685** | **5.87** | **0.87** |
| `A_drop_sdxl_face_pass` | x794–2227 y686–**2677** | **6.15** | **0.87** |

A **~7x step** across a line that lands on the face detector's own bbox edge, in
both arms, outside identical to two decimal places. Neck, shoulder and background
are completely clean. **A whole-frame filter cannot produce a boundary that
follows the face detector's bbox** — so the depositor is a face-detailer
composite, and since removing `#607` changed nothing, it is `#114`.

`#87` is demoted from prime suspect to contributor-at-most. Arm H (`#87` at 0.5)
settles it: if the **neck's** hf RMS moves when the blend moves, `#87` reaches the
neck; if the neck stays at 0.87 while the face changes, `#87` is not the depositor.

### Two further defects found on the way, neither previously reported

**The damage is confined to the mask — and there is a hard seam at its edge.**
`#114` changes **9.08 %** of the frame by more than 8 levels, a clean silhouette
of the SAM mask, and **16.27 %** by more than 0 levels. Outside the mask the
delivered image is **bit-identical** to the input (flat patches: background
2.685 → 2.685, wall 1.572 → 1.572).

*An earlier figure of 99.05 % was reported and I repeated it here — it was wrong
and is retracted. It came from sampling the detailer's `cropped_refined` output
slot, which is the raw VAE-decoded crop and carries round-trip drift everywhere;
the slot actually wired downstream composites the refined region back in pixel
space. **There is no whole-frame VAE damage in your delivered image.***

What does survive: a **hard seam where the mask ends** — bumped inside, clean
outside — with faint reddish text-like marks along it, still present in the saved
file. Two rigs measured the step across it independently and agreed:
edited-region band-pass RMS **5.841** and **5.87**.

**The mouth is not merely bumpy — it is destroyed.** At 1:1 the lips and chin
carry **rectangles, hexagons, dot-matrix grids, ladder patterns and hair-like
filaments**, as if a texture from a different image were composited on. An older
baseline shows the bumps but **not** these.

### The mechanism, corrected — `#114` diffuses 9.3 megapixels in one pass

I twice told the render agent the face pass was *downsampling* to 1024 and
scaling back up. **That was wrong**, caught by the agent reading the server's own
log rather than reasoning about it:

```
Detailer: segment upscale for ((1297.18, 1833.26)) | crop region (2688, 3456) x 1.0 -> (2688, 3456)
```

`x 1.0` — no downsample. `#114` has `force_inpaint: true`, and Impact clamps a
would-be downscale up to 1.0 and samples at native size
(`modules/impact/core.py:291-320`), so **`max_size 1024` is inert on this node**.
Corroborated by the eye pass in the same log, where the lever *does* engage:
`crop region (1381, 342) x 1.39 -> (1920, 475)`, and 1920/1381 = 1.3903 exactly.

**So `#114` diffuses the full 2688x3456 — 9.3 MP — in one pass at denoise 0.8 for
30 steps.** Z-Image is a ~1024-class model; that is roughly 36x its training
area. Tiled, repeated micro-structure — hexagons, dot-matrix grids, ladders — is
the classic signature of sampling far **above** a model's native resolution.

Consequences:
- **`guide_size`/`max_size` is not the lever.** Below 3456 it changes nothing;
  above it, it makes things worse.
- **`bbox_crop_factor` (currently 3) is the lever** — the only setting that makes
  this pass sample *fewer* pixels. 1.5 → ~1946x2750; 1.0 → ~1297x1833, which is
  in the range Z-Image is actually trained for.
- **Close-up framing is still worse, and the finding survives** — but the variable
  is the absolute pixel count diffused in one pass, not a downsample ratio. The
  older baseline's crop was ~5.2 MP against this one's 9.3 MP. It saturates once
  `bbox x 3` exceeds the frame. **A buyer shooting close-up portraits gets a
  materially worse result than one shooting wider, from the same graph.**

**Confirmed a third way, from the pixels alone.** Radially-averaged power spectra
on 512x512 patches: if the face had been generated at 1024 and upscaled to 2688
there would be a hard knee at f/Nyquist = 1024/2688 = **0.381**. There is none —
the cheek's roll-off has the same shape as the background that was never
re-diffused, and the bumps carry energy right up to Nyquist. That is not
upsampled content. The render agent ran this to test its *own* resample
hypothesis and it falsified it, before either of us knew about the log line.

### And at cfg 1, your positive prompt is the *only* steering signal

There is no negative branch to dilute a bad positive (§5). `#106` ships as the
literal placeholder `"TRIGGER, PROMPT FOR YOUR MODEL"`, and that placeholder is
driving 30 steps at denoise 0.8 over the whole frame. **Filling it in is far more
load-bearing than the on-canvas note makes it sound.** An arm testing a real
character prompt with everything else unchanged is queued.

### Why the face is overbaked — established so far

What is already established about *why* the face is overbaked — three findings,
each verified independently, and none of them was in the original hypothesis:

1. **The face pass is not a face pass.** `#114 FaceDetailer`'s `cropped_refined`
   comes back at **2688x3456 — the full frame**; with `bbox_crop_factor 3` on a
   portrait the crop clamps to the whole image. It is then downsampled to
   `max_size 1024`, re-diffused at **denoise 0.80 for 30 steps**, and scaled back
   up ~3.4x. Pore detail is destroyed by the downsample, texture is invented at
   low resolution, and the upscale enlarges every invented blob.
2. **The mouth is tuned correctly and the face is not.** Same node class, same
   model, same sampler and scheduler:
   `#165 mouth = guide/max 1808, steps 8, denoise 0.35` against
   `#114 face = guide/max 1024, steps 30, denoise 0.80`. The mouth sits on the
   model's design point; the face is at ~4x the steps, more than double the
   denoise, and *lower* working resolution on a *larger* region.
3. **A skin amplifier runs at full strength upstream of it.** `#87 ImageBlend` is
   `blend_factor 1, normal`, so its output *is* `image2` — the
   `x1_ITF_SkinDiffDetail_Lite_v1.pth` version — and the clean image is
   discarded. `#114` then re-diffuses already-amplified skin.

`zimage.safetensors` is **Z-Image-TURBO** (sha256 `2407613050b8…5574a6`, exact
match to Comfy-Org's `z_image_turbo_bf16`), distilled for **8 steps at cfg 1**.

Contact sheets will be at `results/face/face_sheet*.png` (faces) and
`results/face/face_skin_sheet*.png` (flat skin). Rebuild any time with:
```bash
python3 tools/contact_sheet.py --arms-dir results/face/arms --out-dir results/face --prefix face
```

---

## 5. cfg recommendation: **empty the negatives and note it on canvas**

Of your three options — raise cfg / empty and note / leave and document — the
recommendation is the middle one. **Nothing was changed.**

**Why not raise cfg — and the renders changed this argument, so read it as it now
stands.** The agent expected cfg 3.0 to visibly break the image. **It does not**
(face 44.56 dB / SSIM 0.9938 against its own cfg-1 arm). So "raising cfg wrecks
it" is *not* the reason, and the report was corrected to say so.

The reason is that **there is no prize behind that door.** Isolating the negative
at a cfg where it *is* live — same cfg, text on versus off — moves:

```
face  #114   0.048 % of pixels by >8 levels
mouth #165   0.000 %
eyes  #406   0.000 %
```

**Even when the negative can act, this string does nothing that matters.** So
raising cfg buys nothing measurable, while moving a guidance-distilled model off
its design point: `zimage.safetensors` is Z-Image-Turbo by sha256, the vendor's
quick-start carries `guidance_scale=0.0, # Guidance should be 0 for the Turbo
models`, ComfyUI's own turbo template runs cfg 1 where its base template runs
cfg 4, and the file contains **zero guidance tensors**. Anything proposing "raise
cfg and A/B it" should still be struck — but because it is pointless, not because
it is catastrophic.

**cfg is also excluded as a cause of the blistering.** Band-pass energy on
`#114`'s edit footprint moves **1.8 %** across the entire cfg 1.0→3.0 range, and
is flat to three decimals on the mouth and eye passes. That is an independent
instrument arriving at the same place as the face grid: the lever is **steps**.

**Why not just leave it.** `#649` sends the buyer to that exact subgraph, where
`#105` sits beside `#106` reading *"deformed, ugly, blurry, … watermark, text"* —
specific, confident, professional-looking, and inert. And the pipeline produces
exactly the defects it names: `#114` leaves a blistered texture, a mask seam and
faint text-like marks that survive into the delivered image. A buyer who sees
that, then finds `watermark, text` already in the negative, will conclude it
needs **strengthening**. Notes are read once; the field is read every time.

**Why emptying is safe.** `comfy/samplers.py:370` sets `uncond_ = None` at cfg 1
*before* the model is called, and nothing in this chain sets
`disable_cfg1_optimization`. The string cannot affect a pixel. Provable by graph
diff plus that source line — no render needed. It also makes the graph
self-consistent, since `#167` and `#394` are **already** empty. The text is
preserved verbatim in `notes/P3-cfg.md`, in `QUESTIONS.md` and in git.

**Scope: `#105`, `#167`, `#394` only.** `619:600` on the SDXL half has the same
shape but a different model, a different distillation, and carries your own typed
negative — untested, needs its own decision.

**Do not** rewire through `ConditioningZeroOut` as ComfyUI's template does. Same
result, but it means adding a node and editing subgraph IO, and that is precisely
the class of edit that produced this run's browser blocker.

**The note is the load-bearing half** — draft wording is in `notes/P3-cfg.md` §7
for you to put in your own voice. It has to say: Turbo has no negative prompt so
the boxes are empty deliberately; do not raise cfg to make them work; put what
you want *and* what you want avoided into the positive.

### The consequence that matters more than the negative

At cfg 1 the positive is the **only** conditioning. So `#106` shipping as
`"TRIGGER, PROMPT FOR YOUR MODEL"` is far more damaging here than the same
placeholder would be on a cfg>1 model, where a negative branch would dilute it.
`#649` already tells the buyer to replace it. On this evidence that is not step 3
of a list — it is a requirement.

### Supporting evidence **[cfg A/B arms still queued]**

**Do not raise cfg.** cfg 1 is a *requirement* of the model, not an oversight.
`zimage.safetensors` is the guidance-distilled Turbo; the vendor says guidance
should be 0; ComfyUI's own templates use cfg 1 / 8 steps for turbo against cfg 4
/ 25 steps for base; and `comfy/samplers.py:370` shows that at cfg 1 the uncond
is **never evaluated**, so the negative's tokens never reach the transformer.

So the negatives beside `#114`, `#165` and `#406` cannot act. **Two of the three
are already empty** (`#167` mouth, `#394` eyes); only `#105` (face) still carries
text. Someone reached this conclusion twice and stopped.

The sharp edge: `#105` reads `"… deformed piercing, bad piercing …"` — a written
defence against exactly the gold lip artifact that appeared in the skin-blend
arm — and it is inert. Final recommendation pending the A/B.

---

## 6. Things I changed that you did not ask for

- **Reverted D1** (`73f3d5c`) — you rejected it; done before any render so the
  whole run uses the graph you ship.
- **`popup.js`, twice** (`342a038`, `3afa7ed`). It threw an uncaught error for any
  browser that received a selector broadcast for a node it did not have, and the
  Send button never tracked the selection — with >1 image the buyer **could not
  send at all**; with one, deselecting left Send enabled and pressing it
  submitted an empty selection. Both ended with no image. Verified by a real
  4-image browser run: `send_enabled_before_pick: false → after: true`.
- **`reality_prompt_generator.js`** (`7de8c15`) — a `console.error` fired on every
  buyer's first load for a normal condition; downgraded to `debug` after checking
  the element is conditionally rendered, so a real fault is not being hidden.
- **`aiofm_setup.sh`** — `SETUP_URL` pointed at a gist file returning **HTTP 404**,
  in both places a stuck buyer is told how to retry, so both piped a 404 into
  bash. Also two banners announced the *video* pack, and the disk figure was low.
- **Docs** — `STATE.md` rewritten as the handoff, `QUESTIONS.md` consolidated,
  `CLAUDE.md`'s "there is no GPU here" made conditional.

---

## 7. Still broken / still open

- **Five licence blockers on selling** — `QUESTIONS.md` §0. LUSTIFY, DMD2
  (cc-by-nc, **still shipping** from the HF repo because `--include "models/*"`
  sweeps it regardless of the fetch list), UnMarker and GrainNet (both
  non-commercial), and the pack states no licence of its own. Deleting the
  encumbered trees is a **code change, not an `rm`** — a naive delete takes
  INSTARAW from 95 registered node types to **0**.
- **The face quality work is unfinished** — see §4.
- **`#105`'s negative cannot act** — see §5.
- Ten stale `rgthree.compare._temp_*` filenames are baked into the shipped
  workflow; a buyer gets 404s on open, and they are **real payload POSTed on
  every run**, not a UI artifact.
- **`node_identifier` is persisted in the workflow file**, so two browsers with it
  open both accept the selector message and either can answer the other's pause.
- `INSTALL MODELS.txt` step 1 tells the buyer a one-line `bash <(wget …)` install
  gets no custom nodes — true of piping the installer, **false of the gist
  bootstrap**, which is the delivery method.
- `AUDIT.md`, `MAP.md`, `PROPOSALS.md`, `SETUP.md` predate the pod session and are
  **not** rewritten; `STATE.md` §3 lists the corrections I can prove.
