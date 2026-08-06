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

### Speed — **quote this one and nothing else: ~53 s, −16.8 %**

I gave you "26 % faster" and "400.7 s → 189.3 s". **Both were wrong** — the second
by a factor of eight; that 53 % was cache, not steps. The lever has now been
measured twice from **opposite cache regimes** on the shipping graph, and the two
agree to 0.2 s:

| steps 30 → 8 | measurement |
|---|---|
| **cold**, 0 cached both sides (315.5 → 262.6 s) | **−52.9 s, −16.8 %** |
| **warm**, byte-identical 57-node cache sets | **−53.1 s** |

Two regimes, one answer. That is the steps lever. **`denoise` costs 0.4 s —
nothing.** `crop factor` is a saving of **unknown size**: the one cold pair
suggesting −118 s was withdrawn as implausible (larger than the pass itself
costs, and that arm was also writing six full-resolution PNGs).

**Why every timing claim here went wrong, including three of mine:** the same
graph cold vs warm is 388.9 s vs 190.1 s. **120–200 s of a cold render on this
pod is model loading** — larger than any lever being argued about. A comparison
that does not hold cache constant measures loading, not sampling.

*Do not quote `−103.7 s / −26 %`, `−53 %`, `−6.9 %` or `−118 s`. All four have
that defect and all four are withdrawn.*

### Luna's freckles — **X2 is not Luna**

You asked whether Luna's freckles survive in `X2`. **That tile is a different
woman.** `results/face/arms/X2_steps08_denoise050/api_graph.json` has
`"lora_01": "None"` on both `116` and `618` — the whole face grid ran with both
LoRA stacks empty. There were never any Luna freckles in `X2` to lose, and the
face you judged is the base model's. **Nothing you concluded from that tile
about your character carries over.** New arms were rendered with both your LoRAs
loaded; everything below is from those.

**With your LoRAs loaded, the freckles die at `#98 UltimateSDUpscale`, two
stages before the face pass runs.**
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

### The denoise question — **recommendation: `#114 denoise` 0.80 → 0.35**

`widgets_values[9]`, `0.8` → `0.35`. One float. **Not applied — you pick from the
sheet.** `results/face/R1denoise_face_sheet1of1.png`, 7 tiles at 1:1, row 1 is
what you already saw at cf 3, rows 2–3 are the shipping graph with your LoRAs.

**In plain language.** At the shipped **0.80** the cheeks, nose and brow carry a
fine granular crust — much fainter than at 30 steps, but the surface still reads
like **orange peel**: small pale raised specks packed edge to edge, catching the
light. That is the pass adding texture that is not skin.

At **0.35** it is gone. The cheek *is* skin — even, carrying the pore-scale
texture that was already in the image before the face pass. Eyelashes are
separate strands. The iris has structure instead of being a flat disc. And a
small brown mark below the right eye survives that appears in **no** 0.80 arm —
it is in the pre-pass tap, so it is real, and 0.35 is the only setting that
carries it through.

**0.50 fails in the direction nobody expects: it is *smoother* than 0.35**, not
rougher (fine texture 0.883 vs 0.972), and the brown mark is gone. So if you look
at the 0.35 tile and want *less* smoothing, 0.50 is the wrong way to go.

**Steps 30 at the same denoise puts the crust back** (bright-blob 3.36 % vs
1.68 %) and costs 53 s — the control showing the two levers are independent.

**It does not bring the freckles back.** Nothing on this node can; see below.

**One honest negative on my crop-factor change:** on the *cheek* specifically,
cf 1.5 is not better than cf 3 at the same steps and denoise (8.19 % vs 7.78 %
bright-blob). The case for cf 1.5 is the philtrum, lips, chin and jaw seam —
different regions. **On the nose and cheeks the lever is denoise, not crop
factor.** Both are worth having; they are not doing the same job. For the record,
the server log confirms cf engaged: 9.29 MP → 5.75 MP per pass, a 38 % cut.

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

0. **Following your own on-canvas instruction crashes the render.** Root note
   `#649` §3 tells the buyer to type their character into `#106`. Done with a
   LoRA loaded, that **crashed 2 of 2 attempts** — hard `RuntimeError` at
   `622:403 MaskBoundingBox+`, no image. The placeholder text ran clean 2 of 2.
   The two arms differ by **one input** (`620:106.inputs.text`, graph-diffed,
   nothing else), the runs were alternated post-`/free` with **16 unrelated
   successes interleaved**, and both crashes stopped at the same node 0.5 s
   apart — a deterministic path, not the NaN flakiness in item 1.
   **Caveats, and they are real: n=2 per side, one string tested, and a filled
   `#106` *without* LoRAs rendered clean — so "needs the LoRAs" is unproven.**
   **[I]** The defect is probably not `#106` at all but the missing guard in
   item 1 — `ComfyUI_essentials/mask.py:184` calls `.min()` on an empty tensor,
   so anything that empties the Eyes-stage face mask is a crash instead of a
   degraded image. The prompt looks like one route in; the poisoned server is
   another. A test splitting trigger-token from description from LoRAs is
   running now. **Until it reports, treat §3 of the canvas instructions as
   unsafe** — the note has not been changed, because I do not yet know what it
   should say. Evidence: `results/r4/R4_D2_loras_filled_*`,
   `R4_CTL_loras_placeholder_*`; write-up `notes/R4-defects.md` §2b.
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

**Fine to upload for your own testing, which is what you said you wanted it for.
I would not put it in front of a buyer until §7.0 is settled** — the canvas tells
them to do the thing that crashed. Your call, not mine; the bytes are ready
either way and nothing about §7.0 changes them.

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
