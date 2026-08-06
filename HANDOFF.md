# HANDOFF.md

**Workflow `a811b5d6…` · artifact `5f2a0f2b…` · nothing uploaded.**
Evidence for every line: `notes/HANDOFF-detail.md` and the per-agent reports in
`notes/`. One test was still running when this was written; §6.0 says so.

---

## Two things want you, everything else is done

**1. Pick a denoise.** `#114 widgets_values[9]`, `0.80` → **`0.35`** is my
recommendation. **Not applied.** Sheet: `results/face/R1denoise_face_sheet1of1.png`
— 7 tiles, 1:1, rows 2–3 are the shipping graph with your LoRAs.

At the shipped **0.80** the cheek and brow carry a fine granular crust — much
fainter than at 30 steps, but the surface still reads like **orange peel**: pale
raised specks packed edge to edge. At **0.35** it is gone; the cheek *is* skin,
carrying the pore texture that was already there before the pass. Lashes are
strands. The iris has structure instead of being a flat disc. A brown mark under
the right eye survives that appears in **no** 0.80 arm — it is in the pre-pass
tap, so it is real, and 0.35 is the only setting that carries it through.
Costs 0.4 s. **0.50 is *smoother* than 0.35, not rougher** — so if you want less
smoothing than the 0.35 tile, 0.50 is the wrong direction.

**2. Decide whether this ships to anyone but you.** See §6.0. The bytes are ready
either way.

## 1. The browser bug is fixed — **proved from the artifact that ships**

`No output node found for id [647] slot [4] MODEL` is gone. `5f2a0f2b…` unpacked
into a ComfyUI that was empty before the run, on a separately built instance,
live one never restarted.

```
110 nodes audited: 0 unregistered (red), 0 has_errors, 0 dialogs, 0 toasts
#618 lora_01 = lunaskye.safetensors   #116 lora_01 = luna.safetensors
prompt typed -> Run -> POST /prompt 200 -> HasMetadata_00041_.png, 11,140,426 B
```

Screenshots: `results/gate/`, 37 artifacts, three legs. "Zero red" was *checked*
with the frontend's own predicate across root and every subgraph, cross-checked
against `/object_info`, walk count matching the file — that is what makes it a
check rather than a quiet pass. Cause and mechanism: `notes/HANDOFF-detail.md` §1.

**Your buyer's literal first screen:** stock ComfyUI puts the Templates modal
over the whole UI on a first-ever load. Not ours, harmless, must be closed before
the Workflows sidebar is reachable — and no API-level check could ever see it.

## 2. What I applied

| commit | change | why |
|---|---|---|
| `2e4e8e9` | `#114` **steps 30 → 8** | your pick and the grid's, independently |
| `a806ce3` | `#105` **emptied** + canvas note `#652` | the text cannot act at cfg 1 |
| `74c0f11` | `#114` **`bbox_crop_factor` 3 → 1.5** | cf 3 was putting visible damage on the face |

**steps 8:** bumps gone, lips look like lips, lashes are strands. Softer — **and
the grain it loses was never pores, it was damage.** 16 keeps a third of it.

**crop factor 1.5:** at cf 3 the crop clamps to the full frame, so the pass
diffuses 9.29 MP in one go on a ~1024-class model — fibrous growth on the
philtrum, debris on the lips, scaly chin, hard jaw seam, **in the steps-8 graph
you approved**. cf 1.5 refines **0.04 % more** pixels, so it is not doing less.
**Honest negative:** on the cheek alone cf 1.5 is *not* better than cf 3 (8.19 %
vs 7.78 % bright-blob). Its case is philtrum/lips/chin/jaw. On the nose and
cheeks the lever is denoise. If the residual lip blister bothers you, `1.0` is
one integer away (`widgets_values[15]`).

## 3. Luna's freckles — **`X2` is not Luna**

You judged that tile and asked whether her freckles survive it.
`results/face/arms/X2_steps08_denoise050/api_graph.json` carries
`"lora_01": "None"` on both `116` and `618`. **The whole face grid ran with both
LoRA stacks empty** — that face is the base model's, not your character's, and
nothing you concluded from it about her carries over. Re-rendered with both your
LoRAs loaded; §1 and everything below is from those.

**With your LoRAs, the freckles die at `#98 UltimateSDUpscale`, two stages before
the face pass runs.** One render, six taps, same seed
(`results/face/R1_where_freckles_die_1to1.png`) — pigment % by stage:

| base `619:601` | `#92` hands | `#91` skin model | `#87` blend | **`#98` upscale** | into `#114` | delivered |
|---|---|---|---|---|---|---|
| 3.39 | 3.39 | **6.58** | 6.58 | **2.09** | 2.10 | 3.25 |

**No value of `#114`'s steps, denoise or crop factor can bring them back** — your
denoise pick is purely about how the skin looks. The lever is **`#98`** (1.5x, 2
steps, denoise 0.08) in `3. Hands, Skin & Second Upscale`: **logged, not touched,
no value recommended.** Note the skin-detail model **nearly doubles** the freckles
rather than removing them, which retracts an earlier guess that blamed
`#87`/`#91`. *(Scale controlled with a LANCZOS resize across the 1792→2688
boundary: 2–5 % against the 67 % step. Full stage notes in `notes/R1-denoise.md`.)*

## 4. Speed — **quote ~53 s / −16.8 % and nothing else**

I gave you "26 % faster" and "400.7 → 189.3 s". **Both wrong**; that 53 % was
cache, not steps. Measured twice from **opposite cache regimes**, agreeing to 0.2 s:

| steps 30 → 8 | |
|---|---|
| **cold**, 0 cached both sides (315.5 → 262.6 s) | **−52.9 s, −16.8 %** |
| **warm**, byte-identical 57-node cache sets | **−53.1 s** |

`denoise` costs 0.4 s. `crop factor` saves an **unknown** amount — the one pair
suggesting −118 s was withdrawn as implausible. **Why every timing claim here
went wrong, three of them mine:** the same graph cold vs warm is 388.9 vs 190.1 s,
so **120–200 s of a cold render on this pod is model loading** — bigger than any
lever being argued about. A comparison that does not hold cache constant measures
loading. *Do not quote `−103.7 s / −26 %`, `−53 %`, `−6.9 %` or `−118 s`.*

## 5. cfg — left at 1, negatives emptied, explained on canvas

`zimage.safetensors` is Z-Image-**Turbo** by sha256; vendor documents
`guidance_scale=0.0`; at cfg 1 `comfy/samplers.py:369-370` never evaluates the
uncond, so a negative's tokens never reach the model. Raising cfg does not
visibly break anything — but making the negative live moves **0.048 % / 0 % / 0 %**
of pixels. Pointless rather than catastrophic. `#167`/`#394` were already empty;
`#105` now matches, with note `#652` beside them in plain words.

## 6. Still broken

**0. Following your own on-canvas instruction crashes the render.** Root note
`#649` §3 tells the buyer to type their character into `#106`. Done **with a LoRA
loaded that crashed 2 of 2** — hard `RuntimeError` at `622:403 MaskBoundingBox+`,
no image. Placeholder text ran clean 2 of 2. The arms differ by **one input**
(`620:106.inputs.text`, graph-diffed), were alternated post-`/free` with **16
unrelated successes interleaved**, and both crashes stopped at the same node
0.5 s apart — deterministic, not the flakiness in item 1. **Caveats, real ones:
n=2 a side, one string tested, and a filled `#106` *without* LoRAs rendered
clean**, so "needs the LoRAs" is unproven. **[I]** The defect is probably not
`#106` but the missing guard in item 1 — `essentials/mask.py:184` calls `.min()`
on an empty tensor, so anything emptying the Eyes-stage face mask is a crash
instead of a degraded image; the prompt looks like one route in. **A 3-render
test splitting trigger-prefix from description from LoRAs is running now.** Until
it reports, treat §3 of the canvas instructions as unsafe. The note is unchanged
because I do not yet know what it should say. `notes/R4-defects.md` §2b.

   **This collides with §5 and that is the worst part.** At cfg 1 the positive
   prompt is the *only* conditioning the model gets, so filling `#106` is a
   requirement, not an optional step — and leaving the placeholder, the one thing
   observed not to crash, means the face pass is steered by the literal string
   `TRIGGER, PROMPT FOR YOUR MODEL`.

1. **A NaN in one render poisons the server.** Later renders then deliver a **flat
   grey face with `status: success`**, or crash at `622:403`. **It recurs.** Fix:
   `POST /free {"unload_models": true, "free_memory": true}`. Always re-confirm
   with a byte-identical resubmission of something that already worked before
   trusting anything measured afterwards. *This voided six arms and produced two
   confident wrong conclusions before controls caught them.*
2. **`#165 Mouth Detailer` is silently skipped ~half the time.** `#648` drops the
   lips segment when crop area exceeds **1,700,000**; observed values cluster
   **1.77–2.06 M**. One session: **19 passed, 20 dropped.** No warning.
3. **A hard composite seam** at the face-box edge survives every arm (×6.76
   baseline, ×3.57 at steps 8, never 1.0) and is visible in the delivered image.
4. **Five licence blockers** — `QUESTIONS.md` §0, untouched as instructed. DMD2
   (cc-by-nc) **still ships**, because `--include "models/*"` sweeps it whatever
   the fetch list says.
5. Stale `rgthree.compare._temp_*` names in the workflow — **observed firing** as
   404s on a clean install's first open, real payload POSTed every run.
6. `node_identifier` is saved in the workflow, so two open tabs both answer the
   selector.
7. `AUDIT.md`, `MAP.md`, `PROPOSALS.md`, `SETUP.md` predate this work.

## 7. Using and testing it

| What | Where |
|---|---|
| prompts + seed | panel beside `1 · YOUR PROMPTS & SEED` |
| **SDXL LoRA** | node **`618`** — body, pose, hands, upscales |
| **Z-Image LoRA** | node **`116`** — face, mouth, eyes. **Your likeness lives here** |
| **face prompt** | sg `5 · Face & Mouth Detail`, `#106` — **but read §6.0 first** |

Fill both slots. **The render pauses** at an image selector and waits — walk away
and it times out after 10 minutes and sends nothing.

```bash
# this pod, 9 s, no GPU, after any graph edit. 0=pass 1=broken 2=couldn't run
node tools/browser_harness/run.js --workflow OFMTech_NSFW --no-submit
# fresh pod  (provision 250 GB — the old "~176 GB" was wrong low)
echo "hf_YOUR_TOKEN" > /workspace/.hf_token
bash <(curl -sSL "https://gist.githubusercontent.com/msit270/70256ac1ebf2760e10f78804862db528/raw/aiofm_setupnsfw.sh")
```

## 8. Changed without being asked

**`popup.js` ×2** (threw on a selector broadcast for a node the browser lacked;
and the Send button never tracked the selection, so with >1 image the buyer
**could not send at all** — verified by a 4-image run) · **`reality_prompt_generator.js`**
(`console.error` on every first load) · **`aiofm_setup.sh`** (`SETUP_URL` **404**
in both places a stuck buyer is told to retry; two banners named the *video*
pack; disk figure low) · docs: `STATE.md`, `QUESTIONS.md`, `CLAUDE.md`.

## Publishing — you run this, nobody else. **Nothing was uploaded.**

**Fine to upload for your own testing, which is what you said it was for. I would
not put it in front of a buyer until §6.0 is settled** — the canvas tells them to
do the thing that crashed. Your call; §6.0 changes none of these bytes.

```
dist/AIOFMTech-NSFW.tar.gz   8,155,368 B   sha256 5f2a0f2b…c5ab1   170 files
workflow inside it: a811b5d6…   verified out of the archive, not off the tree
```
Verified against **these** bytes: all four buyer-path cases green (no token,
rejected token, bad archive, happy path — exit 0 in 127 s, `integrity: OK`, all
51 node types registered), the `PACK_TOP` assertion observed firing against a
discriminating negative control, and a 170 → 170 delta with zero additions and
zero removals.

```bash
HF_TOKEN="$(tr -d '[:space:]' < /workspace/.hf_token)" \
/venv/main/bin/hf upload msit270/AIOFM-Pack \
    /workspace/nsfw-fix/dist/AIOFMTech-NSFW.tar.gz \
    dist/AIOFMTech-NSFW.tar.gz \
    --commit-message "NSFW pack re-cut against the #114/#105 graph changes (workflow a811b5d6)"
```
`dist/` is deliberate — it keeps the artifact out of the bulk
`hf download --include "models/*"`.

```bash
# check from the buyer's side, the only side that counts
curl -sS -I -H "Authorization: Bearer $(tr -d '[:space:]' < /workspace/.hf_token)" \
  "https://huggingface.co/msit270/AIOFM-Pack/resolve/main/dist/AIOFMTech-NSFW.tar.gz" \
  | grep -i 'x-linked-etag\|x-linked-size'
# expect: x-linked-etag: "5f2a0f2b…c5ab1"   x-linked-size: 8155368
```
