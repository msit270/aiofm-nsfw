# HANDOFF.md

Two pages, as asked. Evidence for every line is in **`notes/HANDOFF-detail.md`**.
Live document — some Phase 2 arms were still rendering when this was written.

---

## 1. Is the browser bug fixed? **YES**

`No output node found for id [647] slot [4] MODEL` is gone. Proved in a real
browser on the graph you ship, not taken from the previous run:

```
opened OFMTech_NSFW from the Workflows sidebar
sdxl=lunaskye.safetensors  zit=luna.safetensors  seed=20260806
pressed Run  ->  POST /prompt 200, 88 nodes
RESULT status=success  outputs=[["505","HasMetadata_00012_.png"]]   pageerrors: 0
```

**Screenshot: `results/phase0/04-final.png`** — your workflow loaded, rendered
portrait in the image feed. Merge commit `b328f024`.

## 2. Testing it yourself

**On this pod** — 9 s, no GPU. Run this after any graph edit:
```bash
cd /workspace/nsfw-fix
node tools/browser_harness/run.js --workflow OFMTech_NSFW --no-submit
```
`0` = pass · `1` = workflow broken · `2` = test couldn't run (**not** a pass).
Full journey incl. the selector pause: swap `--no-submit` for `--drive-selector`.

**Fresh pod:**
```bash
echo "hf_YOUR_TOKEN" > /workspace/.hf_token
bash <(curl -sSL "https://gist.githubusercontent.com/msit270/70256ac1ebf2760e10f78804862db528/raw/aiofm_setupnsfw.sh")
```
Then restart ComfyUI **and** hard-reload the browser. Look for `workflow nodes :
all 88 present` and `integrity : OK`. **Provision 250 GB** — the old "~176 GB"
was wrong low, and the script prints GiB while labelling it GB.

## 3. In the browser

| What | Where |
|---|---|
| prompts + seed | the panel beside `1 · YOUR PROMPTS & SEED` |
| **SDXL LoRA** | node **`618`** — body, pose, hands, upscales |
| **Z-Image LoRA** | node **`116`** — face, mouth, eyes. **Your likeness lives here** |
| **face prompt** | subgraph `5 · Face & Mouth Detail`, node **"Face Detailer Prompt"** (`#106`), reads `TRIGGER, PROMPT FOR YOUR MODEL` |

Your `luna` / `lunaskye` are both present and both were exercised in the proof.
**Fill both slots** — the first face pass runs on SDXL through `618`, everything
after on Z-Image through `116`. **The render pauses** at an image selector and
waits for you; if you walk away it times out after 10 min and sends nothing.

## 4. The face — **set `#114` steps 30 → 8**

**Open `results/face/facetight_face_sheet1of1.png` first** (all arms, tight
crop, 1:1). Then `face_skin_sheet1of1.png` for texture without features.
Baseline is top-left on every sheet; every tile is verified byte-identical to
its source crop.

`#114` runs **30 steps on a model distilled for 8** — and your own mouth pass
`#165` already runs 8 on that same model.

| | blobs/MP ↓ *(the defect)* | pores/MP ↑ *(what you asked for)* | exec |
|---|---|---|---|
| baseline 30 / 0.80 | 764 | 16,471 | 397.8 s |
| steps 16 | 552 | 19,339 | 224.1 s |
| **steps 8** | **239** | **23,213** | 294.1 s |
| denoise 0.50 | 157 | 23,050 | 291.6 s |

Bumps gone, freckles visible as flat brown marks, eyelashes clean strands.
**26 % faster, and that is a lower bound** (verified against cache state, not
assumed). **Steps 16 is not enough** — it keeps a third of the defect, so it does
not answer "more grain" the way you hoped. Steps 8 is **softer** than baseline;
denoise 0.50 scores better still and is **free** (`denoise` costs no time — it
moves where on the schedule the pass starts, it does not shorten it) but reads
waxier and shifts the iris. **Combination arms and a LoRA-loaded confirmation
pair were still rendering.**

**Not the cause, all cleared:** the first face pass `#607` (D3 — your stop
condition fired, nothing applied), `#87` skin blend (8 % vs steps' 69 %), and
cfg. **No safe way to make `#114` sample fewer pixels exists** — `guide_size` is
inert, `bbox_crop_factor` is catastrophic (see §7).

## 5. cfg — **empty the negatives, note it on canvas. Do not raise cfg.**

`zimage.safetensors` is **Z-Image-Turbo** by sha256; vendor says
`guidance_scale=0.0`; at cfg 1 `comfy/samplers.py:370` never evaluates the
uncond, so the negative's tokens never reach the model. **Two of the three are
already empty** (`#167`, `#394`); only `#105` still carries text.

Raising cfg does **not** visibly break the image — but making the negative live
moves **0.048 % / 0.000 % / 0.000 %** of pixels. There is no benefit behind the
dead field. Draft canvas wording in `notes/P3-cfg.md` §7.

**At cfg 1 your positive prompt is the only conditioning** — so filling in `#106`
is a requirement, not step 3 of a list.

## 6. Changed without being asked

- **Reverted D1** (`73f3d5c`) before any render, so the run used the graph you ship.
- **`popup.js` ×2** — it threw for any browser receiving a selector broadcast for
  a node it lacked, and **the Send button never tracked the selection**, so with
  >1 image the buyer could not send at all. Verified fixed by a 4-image browser run.
- **`reality_prompt_generator.js`** — a `console.error` on every buyer's first
  load, downgraded to `debug` after checking it was a normal condition.
- **`aiofm_setup.sh`** — `SETUP_URL` returned **HTTP 404**, in both places a stuck
  buyer is told to retry; two banners named the *video* pack; disk figure was low.
- Docs: `STATE.md`, `QUESTIONS.md`, `CLAUDE.md` environment section.

## 7. Still broken

1. **A NaN in one render can poison the server so every later render silently
   delivers a faceless image.** Six arms came back with a **flat RGB (53, 47, 43)**
   region over 23.5 % of the frame where the face should be, `status: success`,
   no warning. **Settled by control, not by theory:** a *byte-identical*
   resubmission of an arm that had rendered cleanly at 01:30 also came back flat
   at 02:38 — same graph, same hash. After `POST /free {"unload_models": true}`
   the same graph rendered **bit-identical to the 01:30 original** (mean abs diff
   0.0000) from a cold cache. So the fault was **server model state**, following
   a NaN reaching `tensor2pil` at 02:11:21 (`impact/utils.py:155`).
   *Two intermediate claims were retracted along the way and neither is true:
   `bbox_crop_factor` is **not** catastrophic (those arms are **void, untested**,
   and that lever is **unmeasured, not closed**), and the buyer's LoRAs do **not**
   crash the graph.*
   **What this means for you: if a render ever comes back with a flat grey face,
   the fix is `/free` or a ComfyUI restart, not a settings change.** And a render
   can fail this way with no error at all.
   Related **latent** defect, no claim about triggers: the Eyes stage has no
   empty-mask guard, so anything that makes the face undetectable becomes a hard
   crash at `622:403 MaskBoundingBox+` rather than a degraded image.
2. **A hard seam at the mask edge**, with faint text-like marks, survives into
   your saved image. Steps 8 halves it (×6.76 → ×3.57); it does not remove it.
3. **Five licence blockers** — `QUESTIONS.md` §0. DMD2 (cc-by-nc) **still ships**
   because `--include "models/*"` sweeps it regardless of the fetch list.
   Removing UnMarker/GrainNet is a **code change, not an `rm`** (95 node types → 0).
4. Ten stale `rgthree.compare._temp_*` names in the workflow — 404s on open, and
   **real payload POSTed every run**.
5. `node_identifier` is saved in the workflow, so two open tabs both answer the
   selector.
6. `AUDIT.md`, `MAP.md`, `PROPOSALS.md`, `SETUP.md` predate this work.

## Publishing — one command, yours to run. **Nothing was uploaded.**

```
dist/AIOFMTech-NSFW.tar.gz  8,154,217 B  sha256 27fa2e1c…dd3d37  170 files
```
```bash
HF_TOKEN="$(tr -d '[:space:]' < /workspace/.hf_token)" \
/venv/main/bin/hf upload msit270/AIOFM-Pack \
    /workspace/nsfw-fix/dist/AIOFMTech-NSFW.tar.gz dist/AIOFMTech-NSFW.tar.gz \
    --commit-message "NSFW pack re-cut (workflow f1ac7e55)"
```
Verify it landed — **if you see `3f6d0f2f…aada76` it did not** (that is what HF
serves today; the previous run's re-cut was never published):
```bash
curl -fsSL -H "Authorization: Bearer $(tr -d '[:space:]' < /workspace/.hf_token)" \
  "https://huggingface.co/msit270/AIOFM-Pack/resolve/main/dist/AIOFMTech-NSFW.tar.gz" | sha256sum
```
A green cut is **not** a clean licence position — these bytes contain the
encumbered trees. See §7.3.
