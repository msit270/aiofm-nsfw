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

## 4. The face work — contact sheets and recommendation **[IN FLIGHT]**

Renders are running. **This section will be filled in as arms land.**

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

## 5. cfg recommendation **[IN FLIGHT — evidence gathered, renders running]**

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
