# HANDOFF.md

Two pages. Evidence for every line is in **`notes/HANDOFF-detail.md`** and the
per-agent reports in `notes/`. Some work was still running when this was written;
those lines say so.

**Graph as it stands: workflow `a811b5d6…`. Artifact `5f2a0f2b…`.**

---

## 1. Is the browser bug fixed? **YES**

`No output node found for id [647] slot [4] MODEL` is gone, proved in a real
browser **from the artifact that ships** — `5f2a0f2b…c5ab1` unpacked into a
ComfyUI that was empty before the run, on a separately built instance, with the
live one never restarted.

```
110 nodes audited: 0 unregistered (red), 0 has_errors, 0 dialogs, 0 toasts
#618 lora_01 = lunaskye.safetensors   #116 lora_01 = luna.safetensors
   (both clicked in the widget's own menu, both read back from the graph)
prompt typed -> Run pressed -> POST /prompt 200, 88-node API graph
selector driven -> render -> HasMetadata_00041_.png, 11,140,426 B
```

**Screenshots: `results/gate/`** (37 artifacts, three legs). "Zero red nodes" was
*checked* with the frontend's own predicate across root and every subgraph,
cross-checked against `/object_info`, with the walk's node count matching the
file exactly — which is what proves the check complete rather than merely quiet.
What it was: three links inside subgraph
`1. Canvas & Routing` ran straight from the SubgraphInputNode `-10` to the
SubgraphOutputNode `-20` with no node between — `1497 = -10[3] → -20[4] (MODEL)`
is the exact slot named. `LLink.resolve` returns early on the input side with no
`outputNode` key, so the resolver throws. Those links and the passthrough IO are
gone.

**Also worth knowing:** on a **first-ever** page load of a fresh install, stock
ComfyUI puts the Templates browser modal over the whole UI. You must close it
before you can reach the Workflows sidebar. Not ours, harmless — but it is your
buyer's literal first screen, and no API-level check could ever see it.

## 2. Testing it yourself

**This pod** — 9 s, no GPU, run after any graph edit:
```bash
cd /workspace/nsfw-fix
node tools/browser_harness/run.js --workflow OFMTech_NSFW --no-submit
```
`0` = pass · `1` = workflow broken · `2` = couldn't run (**not** a pass).
Full journey incl. the selector pause: `--drive-selector` instead of `--no-submit`.

**Fresh pod:**
```bash
echo "hf_YOUR_TOKEN" > /workspace/.hf_token
bash <(curl -sSL "https://gist.githubusercontent.com/msit270/70256ac1ebf2760e10f78804862db528/raw/aiofm_setupnsfw.sh")
```
Restart ComfyUI **and** hard-reload the browser. Look for `workflow nodes : all
88 present` and `integrity : OK`. **Provision 250 GB** — the old "~176 GB" was
wrong low, and the script prints GiB while labelling it GB.

## 3. In the browser

| What | Where |
|---|---|
| prompts + seed | the panel beside `1 · YOUR PROMPTS & SEED` |
| **SDXL LoRA** | node **`618`** — body, pose, hands, upscales |
| **Z-Image LoRA** | node **`116`** — face, mouth, eyes. **Your likeness lives here** |
| **face prompt** | sg `5 · Face & Mouth Detail`, **"Face Detailer Prompt"** (`#106`) — reads `TRIGGER, PROMPT FOR YOUR MODEL`, replace it |

**Fill both slots.** The first face pass runs on SDXL through `618`; face, mouth
and eyes run on Z-Image through `116`. **The render pauses** at an image selector
and waits for you — walk away and it times out after 10 minutes and sends nothing.

## 4. What I applied to the graph

| commit | change | why |
|---|---|---|
| `2e4e8e9` | `#114` **steps 30 → 8** | your pick and the grid's, independently |
| `a806ce3` | `#105` **emptied** + note `#652` inside sg 5 | the text cannot act at cfg 1 |
| `74c0f11` | `#114` **`bbox_crop_factor` 3 → 1.5** | cf 3 was putting visible damage on the face |

**steps 8:** bumps gone, lips look like lips, lashes are strands not scribble.
Softer than before — **and the grain it loses was never pores, it was damage.**
Steps 16 is not enough; it keeps a third of the defect.

**crop factor 1.5:** at cf 3 the crop clamps to the full frame, so the pass
diffuses 9.29 MP in one go on a ~1024-class model. At 1:1 that was leaving
fibrous growth on the philtrum, debris on the lips, a scaly chin and a hard jaw
seam — **in the steps-8 graph you approved**. cf 1.5 is the same face without it,
and it refines **0.04 % more** pixels, so it is not doing less. **If the residual
lip blister bothers you, 1.0 is one integer away** (`widgets_values[15]`).

> ⚠ **Speed: unquantified. Do not quote the numbers I gave you.** I said "26 %
> faster" and "400.7 s → 189.3 s". A cold control has since shown the steps-8
> LoRA arm is **388.9 s cold**, not 189.3 s — that run had 57 nodes cached
> including the whole base generator. **Most of that gap was cache, not steps.**
> A proper cold pair was rendering when this was written. Treat steps 8 as a
> **quality** change until it lands.

### Luna's freckles — answered, and it moves the question off this node

**They die at `#98 UltimateSDUpscale`, two stages before the face pass runs.**
A tap render saved the image at every stage, with your LoRAs loaded, same seed
(`results/face/R1_where_freckles_die_1to1.png`):

| # | stage | pigment % | bright blobs % |
|---|---|---|---|
| 1 | base generator `619:601` | 3.39 | 3.75 |
| 2 | `587:92` HandDetailer | 3.39 | 3.75 |
| 3 | `587:91` skin-detail model | **6.58** | 10.51 |
| 4 | `587:87` ImageBlend | 6.58 | 10.51 |
| 5 | **`587:98` UltimateSDUpscale** | **2.09** | 3.14 |
| 6 | into `#114` | 2.10 | 3.17 |
| 7 | delivered `#505` | 3.25 | **8.19** |

**So: no value of `#114`'s `steps`, `denoise` or `bbox_crop_factor` can bring
them back.** Your denoise pick is purely about how the skin looks. If you want
the freckles, the lever is **`#98`** (1.5x, 2 steps, denoise 0.08) in
`3. Hands, Skin & Second Upscale` — **logged, not touched, no value recommended.**

Three things fall out that nobody knew:
- `#92 HandDetailer` does not touch the face at all — stages 1 and 2 are identical
  to four figures.
- `#87 ImageBlend` at `blend_factor 1` **is** a pass-through of `#91` — inferred
  before from the widget, now measured: stages 3 and 4 identical.
- **The skin-detail model nearly doubles the freckles** (3.39 → 6.58). It does not
  remove them. An earlier guess that blamed `#87`/`#91` was wrong and is retracted.
- `#114` does exactly what it was accused of and no more: bright blobs 3.17 → 8.19.
  **It adds the bumps; it does not remove pigment that had already gone.**

*Scale was controlled for, because stages 1–4 are 1792-wide and 5–7 are 2688: a
pure LANCZOS resize in either direction moves the measure only 2–5 % relative,
against the 67 % drop across `#98`. The step is real, not resampling.*

**Still open, and the sheet answers it:** whether denoise moves as well. Four
arms with your LoRAs were rendering when this was written. **Contact sheets:**
`results/face/facetight_face_sheet1of1.png` (all arms, tight, 1:1) and
`face_skin_sheet1of1.png` (texture without features).

**Cleared, not the cause:** `#607` first face pass (your stop condition fired —
it looks identical to baseline), `#87` skin blend (8 % vs steps' 69 %, and it
demonstrably reaches the neck without making bumps there), and cfg.

**The metric winner was the wrong answer.** `steps 8 + denoise 0.50` wins every
column and looks airbrushed. Its `pores/MP` column counts dark minima, and at
that smoothness those are as likely noise as pores — **the count rises while the
thing being counted disappears.**

## 5. cfg — **left at 1. Negatives emptied and explained on canvas.**

`zimage.safetensors` is Z-Image-**Turbo** by sha256; the vendor documents
`guidance_scale=0.0`; at cfg 1 `comfy/samplers.py:369-370` never evaluates the
uncond, so a negative's tokens never reach the model. Raising cfg does **not**
visibly break anything — but making the negative live moves **0.048 % / 0.000 % /
0.000 %** of pixels. No benefit behind the dead field, so raising cfg is
pointless rather than catastrophic. `#167` and `#394` were already empty; `#105`
now matches them, and note `#652` sits beside them explaining why in plain words.

**At cfg 1 your positive prompt is the only conditioning** — filling in `#106` is
a requirement, not step 3 of a list.

## 6. Changed without being asked

- **`popup.js` ×2** — threw for any browser receiving a selector broadcast for a
  node it lacked; and the Send button never tracked the selection, so with >1
  image the buyer **could not send at all**. Verified fixed by a 4-image run.
- **`reality_prompt_generator.js`** — a `console.error` on every buyer's first
  load, downgraded after confirming it was a normal condition.
- **`aiofm_setup.sh`** — `SETUP_URL` returned **HTTP 404** in both places a stuck
  buyer is told to retry; two banners named the *video* pack; the disk figure was
  low.
- Docs: `STATE.md`, `QUESTIONS.md`, `CLAUDE.md` environment section.

## 7. Still broken

1. **A NaN in one render poisons the server so later renders fail silently.** Two
   symptoms: a **flat grey face** delivered with `status: success`, or a **hard
   crash** at `622:403 MaskBoundingBox+` (`x.min()` on an all-zero mask). **It
   recurs.** Fix: `POST /free {"unload_models": true, "free_memory": true}` —
   confirmed to recover it; a restart was not needed. Always confirm with a
   byte-identical resubmission of something that already worked before trusting
   anything measured afterwards. *This voided six arms and produced two confident
   wrong conclusions before controls caught them.*
2. **`#165 Mouth Detailer` is silently skipped about half the time.** `#648`'s
   guard drops the lips segment when its crop area exceeds **1,700,000**, and
   observed values cluster **1.77–2.06 M**. Across one session: **19 passed, 20
   dropped.** No warning, `status: success`. Whether your mouth gets detailed
   depends on how large it happens to render.
3. **A hard composite seam** at the face-box edge survives every arm (×6.76
   baseline, ×3.57 at steps 8, never 1.0) and is visible in the delivered image.
4. **Five licence blockers** — `QUESTIONS.md` §0, untouched this run as you
   instructed. DMD2 (cc-by-nc) **still ships** because `--include "models/*"`
   sweeps it regardless of the fetch list.
5. Stale `rgthree.compare._temp_*` names baked into the workflow — **observed
   firing** as 404s on a clean install's first open, present in the shipped
   bytes, and **real payload POSTed on every run** (not a UI artifact).
6. `node_identifier` is saved in the workflow, so two open tabs both answer the
   selector.
7. `AUDIT.md`, `MAP.md`, `PROPOSALS.md`, `SETUP.md` predate this work.

## Publishing — owner runs this, nobody else. **Nothing was uploaded.**

```
dist/AIOFMTech-NSFW.tar.gz   8,155,368 B   sha256 5f2a0f2b…c5ab1   170 files
workflow inside it: a811b5d6…   verified out of the archive, not off the tree
```
Verified against **these** bytes: all four buyer-path cases green (no token,
rejected token, bad archive, happy path — exit 0 in 127 s, `integrity: OK`, all
51 node types registered), the `PACK_TOP` assertion observed firing with a
negative control that discriminates, and a 170 → 170 delta with **zero additions
and zero removals**.

```bash
HF_TOKEN="$(tr -d '[:space:]' < /workspace/.hf_token)" \
/venv/main/bin/hf upload msit270/AIOFM-Pack \
    /workspace/nsfw-fix/dist/AIOFMTech-NSFW.tar.gz \
    dist/AIOFMTech-NSFW.tar.gz \
    --commit-message "NSFW pack re-cut against the #114/#105 graph changes (workflow a811b5d6)"
```
`dist/` is deliberate — it keeps the artifact out of the bulk
`hf download --include "models/*"`.

Check from the buyer's side, the only side that counts:
```bash
curl -sS -I -H "Authorization: Bearer $(tr -d '[:space:]' < /workspace/.hf_token)" \
  "https://huggingface.co/msit270/AIOFM-Pack/resolve/main/dist/AIOFMTech-NSFW.tar.gz" \
  | grep -i 'x-linked-etag\|x-linked-size'
# expect: x-linked-etag: "5f2a0f2b…c5ab1"   x-linked-size: 8155368
```

**Seeing `3f6d0f2f…aada76` means the upload did not land — retry, do not wait for
CDN lag.** That URL 302s to a content-keyed object, so the old hash means the
repo still points at the old bytes.

⚠ **`15706aa7…` and `27fa2e1c…` can never appear.** **Three consecutive re-cuts
have never been uploaded** — so the "watch for this hash" lines in
`notes/WS5-report.md` and `notes/P4-package.md` name hashes that cannot show up
at that URL, and following either would misread a *successful* upload as a
failure. **It also means buyers today still get the old `OFMTech-NSFW/`
top-level directory**; the rename exists only in artifacts nobody published.

Confirm the shipped graph without unpacking:
```bash
tar -xzOf /workspace/nsfw-fix/dist/AIOFMTech-NSFW.tar.gz \
    AIOFMTech-NSFW/OFMTech_NSFW.json | sha256sum
# a811b5d690ccc5207bc7bd1c626cdd3db3b720b9be60d0a687436efcfd2143d8
```

A green cut is **not** a clean licence position — these bytes contain the
UnMarker and GrainNet trees. See §7.4 and `QUESTIONS.md` §0.
