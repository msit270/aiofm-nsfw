# STATE.md — read this before AUDIT.md, MAP.md, SETUP.md or PROPOSALS.md

Written 2026-08-05, at the end of a run on a **live pod** (RTX PRO 6000, 96 GB
VRAM; ComfyUI 0.15.1 on `127.0.0.1:18188`; frontend 1.39.19; all ~178 GB of
models present). Branch `fix/run2`, 33 commits, all pushed.

`QUESTIONS.md` §0 is the short answer to "what still stops me selling this".
Start there if that is your question.

The previous STATE.md described a graph that could not be run in a browser. That
is fixed. This file records what changed, what it corrected in the older
documents, and — as carefully as I can put it — **what is proven versus what is
merely believed.**

---

## 1. The blocker is fixed

`No output node found for id [647] slot [4] MODEL` no longer occurs. A real
browser Run now produces an image.

**What 647 is.** The root host for subgraph `"1. Canvas & Routing"` — four real
nodes (width, height, denoise float, `EmptyLatentImage`). Its outputs 2, 3 and 4
did no work at all.

**Why it threw.** Three links inside it ran straight from the SubgraphInputNode
`-10` to the SubgraphOutputNode `-20` with no node between. Such a link satisfies
both `originIsIoNode` (`origin_id === -10`) and `targetIsIoNode`
(`target_id === -20`). `LLink.resolve` tests the **input** side first and returns
early with `{inputNode, input, subgraphInput, link}` — **an object with no
`outputNode` key at all** — so `_resolveSubgraphOutput` reads `undefined` and
throws. The construct is **unrepresentable in `ResolvedConnection`**, not merely
dangling: no amount of linkId tidying could have fixed it. Sentinel values read
out of the shipped minified bundle; mechanism read from
`assets/api-gz4kgzki.js.map`.

**Why no test caught it.** `/prompt` takes a flat `{id: {class_type, inputs}}`
dict. `definitions` appears nowhere in the request path. `subgraph_manager.py`
only serves blueprint files over two GET routes, and `execution.py`'s
`has_subgraph` is node-level *dynamic expansion*, an unrelated mechanism.
**Subgraph flattening is 100% frontend**, so an API harness cannot exercise it.
The hypothesis in the old STATE.md is confirmed: **this graph had never once been
run the way a buyer runs it.**

A competing explanation was eliminated rather than argued away. The file carries
`extra.frontendVersion: 1.41.20` while ComfyUI 0.15.1 pins 1.39.19, so the author
might have had a version that coped. It does not: `comfyui-frontend-package`
1.41.20 was downloaded and its `LLink.ts` is **byte-identical** to 1.39.19's
(sha256 `65f981e1d43a72ae`, 15,505 bytes both), and its `ExecutableNodeDTO.ts`
still carries the same throw. Upgrading the frontend was never a fix.

**Where it came from.** `MAP.md` §4 records that `#638 ControlNetApplyAdvanced`
carried positive/negative and `#644`→`#643 IPAdapter` carried MODEL across that
subgraph while bypassed — which is the *supported* path. Deleting the dead
ControlNet path on the destroyed pod severed them and reconnected input to output
directly. **The blocker was a regression introduced by that cleanup**, not a
long-standing latent defect. The same edit left `#647`'s `vae` input dead
(`#631 VAEEncode` was its only consumer) and simultaneously *fixed* `AUDIT.md`
A2. This is inference from a document describing a file state no longer on disk —
there is no pre-cleanup copy to diff — but the control run below corroborates it.

**The fix.** Finish the interrupted cleanup rather than work around the
limitation. positive/negative were a **self-loop on host 619 laundered through
647** (`#599`/`#606` left subgraph 2 and came straight back into `#592`/`#617` in
subgraph 2), so they were connected *inside* subgraph 2 where they belong. MODEL
was plain fan-out and was wired direct from `#618`. The dead `vae` input was
removed. `#647` is now a pure source: **0 inputs, LATENT + FLOAT out**, and the
host-level `619 ↔ 647` cycle is gone. All seven subgraphs' `linkIds` were
recomputed from their actual link arrays.

**The proof, and it is not output hashing.** A control was built that kept the
original root wiring byte-identical and inserted three frontend-virtual `Reroute`
nodes inside `#647` (`isVirtualNode = true`, so they fold out of the API graph).
Both were loaded in Chromium against the live server in one session and both API
graphs exported without pressing Run:

    ctl-api.json: 88 nodes   fix-api.json: 88 nodes
    --- 0 difference(s) ---

The control **also POSTed successfully and began rendering**, which independently
confirms the old wiring would have converted — i.e. the regression diagnosis.

**And it renders.** `POST /prompt → 200`, `node_errors: {}`, `status: success`,
`HasMetadata_00002_.png`, **2688×3456**, from root `#505 SaveImage`. The executed
prompt differs from the exported graph only by rgthree's UI-only preview blob.
A second, independent session rendered the same graph to completion, differing on
one input (`pick_list`). Nobody has judged the image; the claim is only that the
pipeline reached its terminal node.

Incidentally this **measured** `MAP.md` §12's resolution ladder, which was
labelled "arithmetic, not measured". 2688×3456 is exactly what it predicted.

---

## 2. What else changed

**Graph (`OFMTech_NSFW.json`, now sha256 `c7708761…0841f7`)**
- **D1** — the pure `#597 VAEEncode → #616 VAEDecode` round-trip removed.
  **This is output-changing and is not a free win** (see §5).
- **D4** — `#592 KSampler`'s `control_after_generate` set to `"fixed"`. Provably
  inert by construction, not merely by diff: the control widget carries
  `serialize: false` and `graphToPrompt` skips those, so its value never reaches
  the backend at all.

**Pack (`ComfyUI_INSTARAW`)**
- Apache-2.0 §4(a) and §4(b) satisfied for the `cg-image-filter` derivation,
  which turned out to be **14 files, not 4**. §4(c)/§4(d) recorded as not
  applicable with reasons. Also fixed: Filmgrainer (MIT, two files had **no**
  notice at all), the Bricolage Grotesque font (OFL), the sRGB ICC profile.
  All 17 edits proved pure prepends by byte-comparing tails against backups.
- `popup.js` — two real defects fixed, both proven by running the real
  expressions rather than reasoning about them. `find_node` threw an uncaught
  `TypeError` for any client whose graph did not contain the broadcast node
  (reachable by reloading during the 600 s pause). The Send button never tracked
  the selection: with >1 image the buyer **could not send at all**; with exactly
  one, deselecting left Send enabled and pressing it submitted an empty
  selection. Both end at `raise InterruptProcessingException()` — no image.
- `reality_prompt_generator.js` — a `console.error` that fired on every buyer's
  first load downgraded to `debug`, after confirming the element is
  conditionally rendered rather than always expected.

**Setup / distribution**
- Archive and directory names now match: `AIOFMTech-NSFW.tar.gz` →
  `AIOFMTech-NSFW/`. The rename happens at pack time and the build **asserts** it
  using the bootstrap's own `sed` expression, so they cannot drift again.
- `SETUP_URL` pointed at a gist file that **returns HTTP 404**, in both places a
  stuck buyer is told how to retry — so both piped a 404 body into bash. Fixed.
- Two buyer-visible banners in the NSFW installer announced the **video** pack.
- **The disk figure was wrong in the expensive direction.** `~176 GB` against a
  measured 193.7 GB decimal / 180.4 GiB. Worse, the script's `human()` divides by
  1024³ and labels the result "GB", so every figure it prints is really GiB. A
  buyer provisioning 176 GB decimal — how pod disk is sold — fails at 95%, after
  paying for the whole download. Now "provision at least 250 GB", both units.
- `all 40 workflow node types present` was hardcoded. It was *arithmetically
  correct*, which is worse than stale — nothing would have caught it drifting.
  Now derived from a counter and relabelled to say it counts files on disk, while
  the 88 is checked against a running server.
- **`all 88 present` is now verified**, reconciled from two independent routes:
  37 hardcoded video types ∪ 51 derived from the workflow, zero overlap, all 88
  registering against a live `/object_info`. The `Note`/`MarkdownNote` filter that
  makes it come out right is load-bearing and is now marked as such — both are
  frontend-only and never appear in `/object_info`.

---

## 3. Corrections to the older documents

**`CLAUDE.md`** said "There is no ComfyUI here, no models, and no GPU". False on a
pod. Rewritten as conditional with three commands that settle it. Left as-is it
would make a future session decline work it can do — the same failure mode as the
blocker: a claim about the environment nobody re-checked.

**`CLAUDE.md` / `MAP.md` §0** say 132 nodes, 24 bypassed. The file is **109 nodes
with exactly one bypassed node** (root `#623`). The seven stages are **already
renamed** — "all seven are called Dont touch!!!" no longer applies.

**`AUDIT.md` A5, `QUESTIONS.md` Q3, and the old STATE.md's unfixed list** all
describe a ControlNet path that **no longer exists**. Zero matches for
ControlNet / IPAdapter / Depth / Branding / LatentSwitch / SetUnion anywhere.

**`AUDIT.md` A21 and the old STATE.md** say `#600 KSamplerAdvanced` reseeds every
run. It reads `"fixed"`. The real residual defect was `#592`, and the graph as
shipped **was already reproducible** from the seed it exposes.

**`AUDIT.md` A4 and `QUESTIONS.md` Q2** quote the face prompt as `PROMT` and call
it a typo. **The file says `PROMPT`**; `grep -c "PROMT"` returns 0. And the
placeholder is not forgotten — root `#649 MarkdownNote` tells the buyer verbatim
to replace it.

**`AUDIT.md` A23** describes a bbox detector wired into `#114`'s
`segm_detector_opt`. That link no longer exists.

**`AUDIT.md` A1 and the old STATE.md** put the round-trip at ~1434×1843. It runs
at **1432×1840** — `#594 VAEEncode` already crops to a multiple of 8.

---

## 4. What blocks selling

**See `QUESTIONS.md` §0.** Five items, found by four different workstreams, none
discoverable from the others. Summary only:

- **LUSTIFY** base checkpoint — redistribution, not image rights.
- **DMD2** (`cc-by-nc-4.0`) — **still in the published repo; every buyer receives
  it.** Recorded as "Replaced" before, which was true of the graph and the fetch
  list and false of the delivery.
- **UnMarker** and **GrainNet** — both forbid commercial use in writing. Stricter
  than LUSTIFY, which at least permits selling the output.
- The pack **states no licence of its own** anywhere.

Two mechanics that made the earlier verdicts wrong, and that will do so again:

1. **Removing a file from the fetch list does not stop it shipping.** The install
   is one bulk `hf download --include "models/*"`, and `fnmatch`'s `*` matches
   `/`. Only deleting from the repo stops delivery.
2. **Deleting the encumbered trees naively takes INSTARAW from 95 registered node
   types to 0**, `IMPORT FAILED`, including `#483` which supplies the prompt,
   negative and seed. It is a code change, not an `rm`, and four modules in the
   chain have not been traced to a conclusion.

**Nothing was deleted.** Scope was Apache-only and nothing reaches a buyer until
the `hf upload` command is run by hand.

---

## 5. Proven, versus believed

**Proven, with evidence in the repo**
- The blocker's mechanism, from the frontend source.
- Flattening is frontend-only, from the server source.
- The fix is routing-identical: 88 vs 88 nodes, 0 differences.
- The graph renders end to end in a browser, from three independent sessions.
- Output is 2688×3456.
- **The buyer journey, as one continuous session** — the user's stated bar. Opened
  `OFMTech_NSFW` from the Workflows sidebar, **picked both LoRAs and typed a
  prompt and seed in the browser**, pressed Run, answered the selector, got an
  image. Verified not from the script's own log but from the API graph the
  **server** embedded in the PNG it wrote:

      618  Lora Loader Stack (rgthree)   lora_01 = 'lunaskye.safetensors'
      116  Lora Loader Stack (rgthree)   lora_01 = 'luna.safetensors'
      483  prompt_batch_data            positive_prompt = "photorealistic portrait
                                        photograph of a woman on a balcony at
                                        golden hour…"   seed = 987654
      505  SaveImage → HasMetadata_00010_.png   2688×3456   12,477,643 bytes
      pageerrors: none

  This is the join that the other two renders did not cover: they used shipped
  defaults, so they tested *render* but not *configure-then-render*. Nobody has
  judged the image.
- D4 cannot alter a submitted prompt (`serialize: false`).
- Both `popup.js` defects and both fixes, against the real expressions — **and
  the Send-button fix confirmed in a real browser with a real 4-image batch**:
  `send_enabled_before_pick: false → send_enabled_after_pick: true`, read off the
  DOM `.disabled` property either side of the click, image on disk, exit 0. On
  the shipped code that run prints *"clicked image #0 of 4 but the Send button is
  still disabled — the buyer cannot proceed"*. A logic proof and a click, agreeing
  without sharing a method. Caveat on the route: the fixture reaches 4 images via
  `batch_size 4`, not via `#602 BatchFromImageList` as a buyer does; the popup
  receives a batch-N tensor either way, so the Send-button behaviour is tested and
  the batch-from-prompts path is not.
- DMD2 ships, from this pod's own `hf` download record.
- A naive licence delete breaks the pack (95 → 0), measured on an isolated
  instance.
- `all 88 present`, reconciled two ways.

**Believed, or measured too few times**
- **D1 is output-changing and substantial.** Full frame PSNR **30.6 dB**, SSIM
  0.857, 15.7% of pixels differing by >8 levels; face crop PSNR 28.6 dB, SSIM
  0.743, 26.4% >8 levels. The mechanism is that `#616` feeds `#617
  UltimateSDUpscale` at denoise 0.25, so a sampler *amplifies* what the
  round-trip was doing. It was a no-op in intent, not in effect. **A/B pair:**
  `results/ws4/A_baseline/HasMetadata_00001_.png` versus
  `results/ws4/B_no_vae_roundtrip/HasMetadata_00005_.png`. **Nobody here can
  judge which is better.** Reverting is one commit (`423df24`). It was kept
  because the justification rests on the graph diff — two nodes removed, one
  input re-pointed, nothing else moved across 86 shared nodes — and **not** on
  pixels or clocks.
- **The first face pass is not cosmetically irrelevant.** `AUDIT.md` A22 says
  pass 3 at denoise 0.80 "largely erases" pass 1. Deleting `#607
  FaceDetailerPipe` as a single variable gives full-frame PSNR 32.56 dB / SSIM
  0.900 and face-crop PSNR 27.69 dB / SSIM 0.723, with 32.8 % of face pixels
  differing by more than 8 levels — pass 1 measurably survives into the final
  image. A22 is too strong. It also saved no measurable time, so the "free speed"
  argument is unsupported too. **No change shipped**; it is purely a look
  question and the A/B pair is saved for the owner.
- **This pipeline appears deterministic under fixed seeds: 5 of 5 control arms on
  the A graph pixel-identical, plus 2 of 2 on the B graph**, pairwise MSE exactly
  0 and max abs diff 0 levels at 2688×3456. Consistent with every sampler being
  `"fixed"` and the exposed seed not advancing. The weight is carried by
  `A3_control_repeat`, which had **zero** cached nodes — every sampler re-ran
  from scratch — and still matched, so this is not an artifact of ComfyUI handing
  back a cached tensor.
  **This does not lift the ban on hash-comparing rendered output.** That ban was
  written about the **sibling video pipeline**, it has not been overturned, and
  determinism observed on four samples is not determinism guaranteed. Use the
  graph diff.
- **No timing number from this run is comparable to any other, and the reason is
  ComfyUI's execution cache — not GPU contention.** This was got wrong three
  times, and the third correction is the one to carry forward.
  Wall-clock was discarded first (it includes queue wait; identical graphs took
  485.7 s and 752.9 s). Server-side `execution_start → execution_success` on n=2
  then produced "D1 makes the render 31 % slower", which was a less noisy
  instrument treated as noise-free. A four-arm control killed that, and the
  spread was attributed to a shared GPU — **also wrong**: ComfyUI serialises the
  queue and history timestamps show each prompt starting ~1 s after the previous
  finished. There was no concurrency to contend for.
  The server records the real cause in every history entry's `execution_cached`:

  | arm | exec | cached nodes | `619:617` cached? |
  |---|---|---|---|
  | `A_baseline` | 214.2 s | 49 | yes |
  | `A2_control` | 210.6 s | 57 | yes |
  | `A4_control` | 209.8 s | 57 | yes |
  | `A3_control` | **311.9 s** | **0** | no — fully cold |
  | `B_no_roundtrip` | 280.5 s | 53 | no |
  | `B2_no_roundtrip` | 280.2 s | 53 | no |
  | `C_no_face_pass` | 280.8 s | 52 | no |

  Each arm did a different amount of real work, decided by what the *previous*
  prompt left cached. The fast A runs had the whole base generator including
  `#617 UltimateSDUpscale` served from cache; B and C re-point `619:617.image`,
  which changes `#617`'s input signature and invalidates it, so `#617` actually
  ran — that is the ~70 s, not the change. `A3` cached nothing (an unrelated
  1.8 s prompt ran before it and evicted everything) and is **the only honest
  full-graph number in the set**.
  **There is no measured timing regression from any change this run.** To measure
  timing here at all, control what is cached — or read `execution_cached` and
  only compare arms that match.
  (The 48.7 % spread is a coincidence of digits with CLAUDE.md's 48.7 dB noise
  figure — different quantity, different units, unrelated.)
- Whether the multi-image selector defect strands a buyer **was** the open
  question here. It is now **proven and closed** — see the entry in the proven
  list above. Carried as unresolved in `notes/WS1-report.md` §8, which was
  written before the test existed; that section is superseded on this point.
- Whether frontend 1.41.x's **editor** recreates `-10 → -20` links when a node
  between subgraph IO is deleted. If it does, any future save can reintroduce
  this blocker invisibly. Untested; only 1.39.19 is installed here.
- The happy-path install was verified with **0 bytes downloaded** — the model
  phase was satisfied from local cache. `integrity: OK` is a **per-file
  byte-exact size check against the Hub API's figures**, not a content hash.
- Everything was observed on **one pod with ~20 extra packs installed**. This is
  not the "fresh pod, NSFW pack only" configuration the blocker was reported
  against.

---

## 6. Tools that now exist (`tools/`, and they are the point)

- `browser_harness/run.js` — drives a real Chromium, loads the workflow through
  the Workflows sidebar, presses Run, and fails on any frontend error. Three
  distinct exit codes: **0 pass, 1 the workflow failed, 2 harness-error** —
  "the environment prevented a verdict" and "the workflow is broken" must never
  be conflated. Captures the `/prompt` POST body as the API graph.
- `graph_diff/graph_diff.py` — the sanctioned inertness check. Folds only three
  node types, each with a cited source; anything switch-like and not in the table
  is reported as an explicit caveat rather than skipped quietly.
- `preflight/integrity.py` — static link lint, 23 ms, no browser. Names
  `outputs[4] 'MODEL'` on the pre-fix file — **it would have caught this
  blocker before anyone opened a browser.** Link bookkeeping only; "0 problems"
  is not "no defects".
- `build_pack.sh` / `compare_pack.sh` / `verify_buyer_path.sh` — reproducible
  build with the top-level name asserted, and the three bootstrap cases.

Run the pre-flight, then the harness, before anything ships.

---

## 7. Traps — carried forward, and new

Keep all of the old ones. **Hash comparison of rendered output remains banned.**
The raw gist URL still serves a stale CDN cache; `api.github.com/gists/<id>` is
authoritative, and its content is a *string*, so `len()` is characters.

New, all paid for this run:

1. **A bare subgraph input→output link is unrepresentable in the frontend.** It
   draws fine in the editor and cannot be flattened. Deleting a bypassed node
   sitting between subgraph IO is how you create one.
2. **`fnmatch`'s `*` matches `/`.** Removing a fetch line stops nothing.
3. **A safety mechanism that silently no-ops is worse than none.** The harness's
   own ignore-list did nothing for a while because a `$`-anchored regex never
   matched Playwright's `<url>:<line>` format, and de-duplicating on message text
   alone let one ignored 404 hide real ones.
4. **A hardcoded number that happens to be correct is worse than a stale one** —
   nothing catches it drifting.
5. **The image selector broadcasts to every connected browser** and blocks the
   page. Never dismiss one you did not open: Cancel aborts somebody else's
   render. For the same reason, never `POST /queue {"clear":true}` on a shared
   pod — a clear removes pending items **with no history entry**, so what was
   destroyed cannot afterwards be identified. That happened during this run.
6. **The graph moves under the documentation faster than the documentation is
   rewritten.** Six claims in `AUDIT.md`/`MAP.md`/`QUESTIONS.md` described nodes
   that no longer exist. Re-check node ids against the file before acting.
7. **You cannot compare render times across arms without controlling ComfyUI's
   execution cache.** A change that alters any node's input signature
   invalidates that node's cache entry, so the *changed* arm re-runs work the
   baseline skipped — and the difference looks exactly like the change costing
   time. Read `execution_cached` in the history entry and only compare arms with
   matching cache state, or force a cold run. This produced a wrong "+31 %"
   conclusion and then a wrong "it is GPU contention" explanation of the wrong
   conclusion.
8. **Substituting a less noisy instrument is not the same as validating it.**
   Wall-clock → server-side timestamps felt like rigour and was still n=2 treated
   as noise-free. Ask what the denominator is before believing any measurement.

---

## 8. Still open

- The five selling blockers (§4, `QUESTIONS.md` §0).
- **Three A/B pairs need an eye on them.** All under `results/ws4/`, each with the
  exact submitted `api_graph.json` beside it. Nobody here can judge any of them:
  - **D1**, the VAE round-trip: `A_baseline/…00001_.png` vs
    `B_no_vae_roundtrip/…00005_.png` — PSNR 30.63 dB, SSIM 0.857.
  - **D3**, the first face pass: `B…00005_.png` vs
    `C_no_sdxl_face_pass/…00006_.png` — face crop 27.69 dB, 32.8 % of face pixels
    moving more than 8 levels.
  - **A3**, the skin filter at `#87 ImageBlend` 1.0 vs 0.5: `B…00005_.png` vs
    `D_skinblend_050/…00011_.png` — 33.88 dB, SSIM 0.924; 80.4 % of pixels move
    but only 7.9 % by more than 8 levels, the signature of a whole-frame filter.
- **The face negative prompt cannot apply, and cfg 1 is required — do not "fix"
  it by raising cfg.** `#114`, `#165` and `#406` run at `cfg = 1`, so
  classifier-free guidance is off. This is **not an oversight**: `zimage.safetensors`
  is sha256 `2407613050b809ff…5574a6`, which is an exact match for Comfy-Org's
  **`z_image_turbo`** `z_image_turbo_bf16.safetensors` and *not* the base
  `z_image` model — the two are the same byte length, so size alone would not
  distinguish them. It is a guidance-distilled Turbo model; the vendor card says
  *"Guidance should be 0 for the Turbo models"*, and ComfyUI's own shipped
  templates use steps 8 / cfg 1 for turbo against steps 25 / cfg 4 for base.
  `comfy/samplers.py:370` shows that at cfg 1 the uncond is **never evaluated**,
  so the negative's tokens never reach the transformer at all.
  **Raising cfg on the Z-Image passes is actively bad advice for this graph**, and
  nothing may be costed as if those passes pay for a negative branch. The SDXL
  half is a normal cfg model and is unaffected.
  Of the three negatives, **two are already empty** — `#167` (mouth) and `#394`
  (eyes) — and only `#105` (face) still carries `"deformed, ugly, blurry, …"`.
  So the file itself shows someone reached this conclusion twice and stopped. The
  remaining work is documentation, not a cfg change. Unchanged pending a decision.
- The multi-image selector needs one real browser click.
- Ten stale `rgthree.compare._temp_*.png` filenames are baked into the shipped
  workflow — a buyer gets 404s the moment they open it. The harness counts them
  under `scope=product-known`; **that counter should be zero.** Worse than it
  first looks: because the sidebar and `loadGraphData` paths were proved to
  differ on exactly `419.inputs.rgthree_comparer`, that state is **real payload
  POSTed to the server on every buyer run**, not a UI artifact.
- **`node_identifier` is persisted in the saved workflow file**, so the `unique`
  check meant to stop a selector message reaching the wrong client cannot do its
  job: two browsers with the same workflow open both accept it, and either can
  answer somebody else's pause. The harness works around it; the product does
  not.
- `reality_prompt_generator.js` ships saturated with leftover `console.log`
  developer instrumentation.
- `INSTALL MODELS.txt` step 1 tells the buyer a one-line `bash <(wget …)` install
  gets no custom nodes or workflow. True of piping the installer, **false of the
  gist bootstrap**, which is the delivery method. Needs a rewrite, not an edit.
- `ComfyUI_INSTARAW` is copied, never overwritten, so anyone re-running after
  this re-cut keeps the **old** pack and nothing tells them.
- `AUDIT.md`, `MAP.md`, `PROPOSALS.md` and `SETUP.md` have **not** been rewritten
  against the current file. §3 lists the corrections I can prove; assume more.
