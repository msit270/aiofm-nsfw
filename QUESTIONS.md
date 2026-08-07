# QUESTIONS.md

Judgement calls, with the option taken and why. Nothing here blocked work.

This file is the index. Each workstream's full working — evidence, file:line,
rejected alternatives — is in `notes/WS<n>-questions.md`, and is not duplicated
here.

Read §0 first if you are deciding what to do next. Everything else is detail.

---

# §0. What actually blocks selling

Five things, collected in one place because they were found by four different
workstreams and none of them is discoverable from the others.

| # | What | Licence | Ships today? | Cost to fix |
|---|---|---|---|---|
| B1 | `SDXLNSFW.safetensors` — **LUSTIFY! GGWP (V7)**, the base checkpoint | `allowCommercialUse: ['RentCivit','Image']`, `allowDerivatives: False` | yes | buyers pull it from Civitai themselves |
| B2 | `models/loras/dmd2_sdxl_4step_lora_fp16.safetensors` | **cc-by-nc-4.0** — no commercial use | **yes, confirmed** | delete from the HF repo **and** fix the video pack's `aiofm_setup.sh:810` |
| B3 | UnMarker — `modules/detection_bypass/utils/{adaptive_filter,unmarker_losses}.py` | **non-commercial only**, `ai-watermark` LICENSE §3.3 | yes | code change, not `rm` — see below |
| B4 | GrainNet — `modules/neural_grain/net.py`, `pretrained/neural_grain/grainnet.pt`, `nodes/utility_nodes/neural_grain_node.py` | **"All rights reserved… academic research use only"** | yes | same |
| B5 | The pack states **no licence of its own** anywhere | — | — | someone must write it |

**B1** permits selling generated images — the product's core use case is fine.
The problem is redistributing the checkpoint file. **B2, B3 and B4 are stricter
than B1**: they forbid commercial use outright.

Two mechanics that make these non-obvious, and that caused the earlier
"replaced" and "audit came back clean" conclusions to be wrong:

1. **Dropping a file from the fetch list does not stop it shipping.** The default
   install is one bulk `hf download --include "models/*"`, and `fnmatch`'s `*`
   matches `/`, so it sweeps the whole tree recursively. The per-file `dl` lines
   are only a fallback. **Only deleting from the repo stops delivery.** This is
   exactly why B2 was recorded as "Replaced" — the graph and fetch list were
   changed, and every buyer kept receiving the file.
2. **Deleting B3/B4 naively takes the whole pack down.** Measured on an isolated
   instance: INSTARAW goes from **95 registered node types to 0**, with
   `IMPORT FAILED` in a console nobody reads as the only symptom — including
   `#483`, which supplies the prompt, negative and seed. Every import in the
   chain is unconditional and top-level. A licence cleanup here is a code change
   touching two `__init__.py` files plus four modules
   (`pipeline.py`, `pipeline_v2.py`, `processor.py`, `non_semantic_attack.py`)
   that **nobody has traced to a conclusion yet**. Trace those before deleting.

Neither `INSTARAW_NeuralGrain` nor `INSTARAW_Spectral_Normalizer` appears in
`OFMTech_NSFW.json`, so removing B3/B4 changes no rendered output.

**Nothing was deleted this run.** Licensing scope was Apache-only, and nothing
reaches a buyer until the `hf upload` command is run by hand — so this is fully
reversible and the decision is the owner's, with the evidence in front of them.

Also unresolved, lower stakes: `models/checkpoints/v1-5-pruned-emaonly-fp16.safetensors`,
2.13 GB of SD 1.5 under `creativeml-openrail-m`, referenced by nothing in either
pack. Dead weight plus a milder version of the same flow-down problem. These two
are the *complete* set of unreferenced non-placeholder files — all 74 `models/`
entries were checked, not sampled.

---

# §1. The pre-existing Q1–Q8, re-checked against this run

`Q1`–`Q8` were written before the destroyed-pod session. Four are now settled and
one is moot. **Do not act on the originals without reading this table** — the
graph moved underneath several of them.

| | Original question | Status now |
|---|---|---|
| **Q1** | Are `#483`'s five image inputs meant to be connected? | **Stands.** They are `optional`; unlinked selects txt2img. Only `images` is ever read. |
| **Q2** | What should sg2's face-detailer prompt say? | **Answered — and the premise was wrong.** See §1.1. |
| **Q3** | Revive or delete the ControlNet + IPAdapter + depth path? | **Moot.** The path no longer exists. See §1.2. |
| **Q4** | What are the `cnr_id: comfy-core, ver: 0.15.1 / 0.17.2` nodes? | **Still open.** Constrains nothing at load time; low value. |
| **Q5** | Is `lumina2` the right `CLIPLoader` type for Qwen on Z-Image? | **Answered: yes.** The graph now renders end to end in a browser, so the encoder loads and drives three Z-Image passes. |
| **Q6** | Are the six orphaned prompts worth recovering? | **Superseded.** `prompt_batch_data` now ships one real default prompt; the orphans remain unread. |
| **Q7** | Should `ComfyUI_INSTARAW` be added to `NODE_REPOS`? | **Answered: no.** It is vendored into the archive and copied into place. |
| **Q8** | Is `#98`'s whole-image tiling deliberate? | **Still open.** Peak VRAM still tracks the frame while the widgets read 512×512. |

## §1.1 — Q2 was asking the wrong thing

`#106`'s `"TRIGGER, PROMPT FOR YOUR MODEL"` is **not** an unfilled placeholder
someone forgot. It is documented buyer-facing template text: root `#649
MarkdownNote` tells the buyer, verbatim, to *"replace `TRIGGER, PROMPT FOR YOUR
MODEL` with your LoRA's trigger word"*. Changing the node would desynchronise it
from its own instructions. **Left exactly as-is, deliberately.**

Two corrections fall out. `AUDIT.md` A4 and the original Q2 both quote the string
as `PROMT` and call it "the typo" — **the file says `PROMPT`**; `grep -c "PROMT"`
returns 0. And `#114` runs at **cfg 1**, so CFG is off and the fully-written
negative `#105` is not applied at all — the negative is effectively as inert as
the positive was assumed to be.

The real finding underneath Q2 is bigger and was not part of the question:
**a buyer's Z-Image LoRA reaches the UNet of all three Z-Image passes and the
text encoder of none.** All three Z-Image text encodes take the raw `#110` CLIP.
The LoRA'd CLIP that does reach `#114`/`#165` is consumed by nothing, because
Impact only uses it when `wildcard != ""` and both are empty. The earlier "hidden
third LoRA stack — Fixed" repaired the model path only.

**Not rewired, deliberately.** It is a no-op at the shipped all-`None` defaults;
none of the three Z-Image LoRAs on this pod has any text-encoder tensors at all,
so it would be a no-op even with one loaded; and the rewire means editing
subgraph IO `linkIds`, which is the exact structure that produced this run's
blocker. Latent, not demonstrable, and logged rather than risked. A buyer could
bring a LoRA with a CLIP component, at which point it would matter.

## §1.2 — Q3 is moot, and that is how the blocker got in

Searching every node in root and all seven subgraphs for ControlNet / IPAdapter /
Depth / Branding / LatentSwitch / SetUnion returns **zero matches**. `#638`,
`#639`, `#641`, `#645` do not exist. The file is now **109 nodes with exactly one
bypassed node**, against CLAUDE.md's 132 and 24.

That deletion is what created this run's blocker: `MAP.md` §4 records that
`#638` carried positive/negative and `#644`→`#643` carried MODEL from the
subgraph's inputs to its outputs while bypassed. Removing them reconnected the
wires input-to-output directly, producing links the frontend cannot resolve.
`AUDIT.md` A5, Q3 and STATE.md's unfixed list all describe a path that was
already gone.

---

# §2. This run's calls, by workstream

Full reasoning in the linked files. Only the call and its one-line basis here.

## The blocker — `notes/WS1-questions.md`

- **Delete the passthroughs rather than insert identity nodes.** The Reroute
  variant works and was proven — it became the control — but it preserves a
  pointless host-level cycle and makes the product depend on a frontend node
  ComfyUI is actively migrating away from.
- **Overruled the brief's rewire.** Wiring root consumers straight to 647's
  sources would have produced a `619 → 619` self-edge; positive/negative belong
  *inside* subgraph 2. MODEL was genuinely plain fan-out and was wired at root.
- **Recomputing every subgraph's `linkIds` was in scope.** `linkIds` is
  authoritative at runtime, five slots were corrupt, and it is covered by the
  zero-diff proof.
- **`#614 "ENABLE IMAGE FILTERING?"` ships `true` — flagged, not changed.** Every
  render pauses behind a popup at ~0% GPU with a 600 s timeout that then sends
  nothing. Defensible as a feature, questionable as a default. Output-changing,
  so not touched.
- **Unverified and worth a pod experiment:** whether frontend 1.41.x *emits*
  `-10 → -20` links when a node between subgraph IO is deleted. `LLink.resolve`
  is byte-identical in 1.41.20, so the newer editor throws the same way — but
  whether its *editor* recreates the construct is untested, and if it does, any
  future save can reintroduce this blocker invisibly.

## The harness — `notes/WS2-questions.md`

- **Boot errors do not gate; load and run errors do.** `--strict-boot` opts in.
  A harness that is red before it does anything is one nobody reads.
- **Ignoring is allowed only from a committed file with a per-entry
  justification, and never silently** — matched errors are printed, counted and
  listed. `frontend-conversion` and `execution` are never ignorable.
- **`product-known` is a third scope with a loud banner**, for real defects in
  what we ship. Filing them as benign would be a lie; leaving them fatal would
  make the harness useless. **The list should be empty** — a later session
  finding it growing is the signal to stop adding to it.
- **`harness-error` is exit code 2, distinct from failure.** "The environment
  prevented a verdict" and "the workflow is broken" must never be conflated.
- **Refuse to dismiss another client's selector popup.** Cancel would abort
  somebody else's render.
- **`graph_diff` folds only three node types, each with a cited source.** An
  over-claiming differ is worse than none; anything switch-like and not in the
  table is reported as an explicit caveat.
- **Open for packaging:** confirm only `OFMTech_NSFW.json` ships into
  `user/default/workflows/`, not the test fixtures.

## Licensing — `notes/WS3-questions.md`

- **No bare `LICENSE` at the pack root.** 28 files carry `PROPRIETARY — ALL
  RIGHTS RESERVED`; an Apache `LICENSE` there would read as covering the whole
  pack and would work against the seller. Shipped `THIRD_PARTY_NOTICES.md` plus a
  `licenses/` directory instead.
- **The copyright line is constructed, not quoted.** Upstream declares none
  anywhere. Derived from repository evidence and written into the notices so it
  can be checked; an upstream-stated line would supersede it.
- **Three unexplained no-op statements left alone** — `const _aq` in `utils.js`,
  `const _ax` in `floating_window.js`, and 417 zero-width characters in
  `image_filter.js`. If they are deliberate markers, someone should know they now
  sit inside files the pack publicly attributes to a third party.

## The graph defects — `notes/WS4-questions.md`

- **`#106`'s text and the Z-Image CLIP path: changed nothing.** See §1.1.
- **A/B renders submit `pick_list="0"` in the API prompt only**, identically in
  every arm, workflow file untouched — otherwise no unattended render can
  complete. Stated prominently because it is not the buyer's path.

## Distribution — `notes/WS5-questions.md`

- **`AIOFMTech-NSFW` wins; the directory changes, not the archive.** The
  bootstrap hardcodes the archive path but reads the directory out of the archive
  at run time, so renaming the directory needs no gist edit and republishes over
  the same HF path. Renaming the archive would open a window where the user has
  uploaded a pack no buyer can reach.
- **The git source directory was not renamed** — it would rewrite paths three
  other workstreams were editing. `build_pack.sh` renames at pack time and
  asserts the result. Worth a clean `git mv` after merge.
- **`INSTALL MODELS.txt` step 1 contradicts the delivery method** and was left
  alone. It warns that a one-line `bash <(wget …)` install gets no custom nodes
  or workflow — true of piping the installer, **false of the gist bootstrap**,
  which is also a one-liner and exists to fix exactly that. A buyer handed the
  bootstrap and then reading this has been told their working install is broken.
  The fix is a rewrite, not an edit, and getting it wrong risks talking a buyer
  out of the working path.
- **`ComfyUI_INSTARAW` is copied, never overwritten** (`aiofm_setup.sh:1156`).
  Correct for protecting a buyer's edits; it also means anyone re-running after
  this re-cut keeps the **old** pack, licence files and all, and nothing tells
  them. A version-aware update keyed on the `12afb909…` provenance marker is the
  right answer.
- **The `Workflow node check` stage checks the wrong workflow** — a hardcoded
  Wan/KJ/VHS list that reported green during an NSFW install without looking at a
  single NSFW node type. Reported, not fixed: editing check logic during a
  distribution cut is the wrong moment.

---

# §3. Raised by the orchestrating session

- **Do not delete B3/B4 in this run.** Scope was Apache-only, the delete is a
  code change with a whole-pack outage as its failure mode, and nothing reaches a
  buyer until the upload command is run by hand. Reversible, and the owner
  decides with the evidence.
- **`popup.js` fixed twice, both proven by running the real expressions rather
  than reasoning about them.** `find_node` threw for any client whose graph did
  not contain the broadcast node; the Send button never tracked the selection,
  stranding a buyer with more than one image and letting a single-image buyer
  submit an empty selection. Both ended at `raise InterruptProcessingException()`
  — no image. **Not verified in a browser with a real multi-image batch.**
- **`reality_prompt_generator.js`'s `console.error` downgraded to `debug`.**
  Verified first that the element is conditionally rendered — if it were
  unconditional its absence would be a real defect and the change would be wrong.
  **Not fixed, and larger:** that region ships saturated with leftover
  `console.log` developer instrumentation.
- **A subagent ran an unscoped `POST /api/queue {"clear":true}`** on the shared
  server to unstick what it wrongly believed was a hung render. A queue clear
  removes pending items **without leaving any history entry**, so what was lost
  cannot be recovered from `/history`. Recorded because the run's A/B evidence
  depends on no arm having silently vanished.
</content>

---

## Crash run — terminology slip in the brief, interpreted rather than asked

**The brief says "4/4 — 3/3 at cfg 3, 1/1 at cfg 1.5 which is what ships" and
Phase 1C says "It crashes at 3 and at 1.5. Test 1.0 and something high."**

Those 3 and 1.5 figures are **`bbox_crop_factor`**, not `cfg`. Actual `cfg` on
`620:114` is **1** and always has been — visible in the crash arm's own submitted
`api_graph.json` (`620:114.inputs.cfg = 1`), and §5 of HANDOFF is the whole
argument for why it must stay 1 on a guidance-distilled Turbo model.

**My reading, taken without stopping:** Phase 1C is asking whether *real* cfg is a
factor, so the arms are `620:114.cfg` at 1 (control = shipping), 2 and 5. Raising
it will probably degrade the image badly — that is expected and irrelevant, the
cell is crash/no-crash only.

**Risk if I read it wrong:** low. If he meant "re-test crop factor 1.0 and a high
crop factor", that has already been answered — crop factor is not a factor,
crash 3/3 at cf 3 and 1/1 at cf 1.5. Either reading leaves the cfg cell worth
running, and it had never been run.

## Crash run — no 77-token boundary in this encoder

The brief flags "77 is a number worth checking against" for the length ladder.
77 is **CLIP's** padded context length. `620:110` loads `qwen.safetensors` as type
`lumina2`, whose tokenizer sets `pad_to_max_length=False` and `max_length=99999999`
(`comfy/text_encoders/lumina2.py`), so nothing pads or chunks at 77 or anywhere
else. Checking it anyway because a boundary appearing exactly at 77 would be
genuinely informative — but the prediction is that it will not.

## The setup script builds sageattention and nothing ever enables it

`aiofm_setup.sh` imports-or-builds sageattention (`:424-454`) and hunts for a
prebuilt `sageattention*.whl` (`:1314-1316`, `:2009`). It is importable in
`/venv/main`.

**Nothing switches it on.** ComfyUI routes through it only with
`--use-sage-attention` (`comfy/ldm/modules/attention.py:724` →
`model_management.sage_attention_enabled()`), the pack never launches ComfyUI,
and neither test instance passes the flag.

So one of two things is true and I do not know which:
- it is **dead weight** — the buyer pays build time for a kernel never used; or
- the buyer's template **does** pass the flag, in which case **every render they
  make is on a numeric path nobody here has ever tested.**

That second case matters because the crash is sequence-length-dependent numerics.
The token bands were measured without sage. On sage they could sit elsewhere, be
wider, or catch the 16-token placeholder that is currently the buyer's safe
default. One arm would tell us; requested from Track E as a low-priority
discriminator, not yet run.

**Not acted on.** Logged per the standing rule to log rather than start.

---

# §4. Run 3 (2026-08-07) — the ship-readiness run's calls

Full evidence in `results/run3/` and `notes/R3-guard.md`. Only the call and its
basis here. Nothing below blocked work.

- **The guard went in even though HANDOFF §6 argued a guard ships ruined faces
  by design.** The owner's brief resolved that argument explicitly: "a degraded
  render beats a crash, and both beat a silent success with a ruined face" —
  and the silent half is answered by C1b (`622:662 PreviewAny` lands the skip
  in /history and on the canvas) plus the harness's flat-face demotion. A fired
  guard is a failure report, not a pass.
- **"103–120 still crashes" was a probe-graph fact, not a product fact.** All
  eight V-track arms in that band ran the probe (frozen base). The full graph
  at 103 tokens had never been run; today it rendered clean (`R3_PC_head_103`).
  The mechanism (empty detection → 622:403) is still real on the full graph —
  `R3_PC_mid_46` crashed cold the same hour — and the guard closes the
  mechanism at any length, which is the stronger property anyway.
- **The bistability now flips arm-to-arm on one process.** `R3_PC_mid_46`
  (default device, 46 tok) errored at 00:48 UTC; `R3_GUARD_mid46` — same
  config plus the guard — rendered a healthy 0.9016-confidence face at 01:01.
  Consequence: only same-window controls mean anything, and the guard's proof
  is the deterministic forced-threshold pair, not any band arm.
- **Anatomy subgraph deleted, not revived.** It was bypassed on the live image
  wire; conversion already folded it out of every render ever made (fold-diff
  0 differences), reviving it would mean validating five never-tested detailer
  paths and their models, and its def carried 8 of the 10 stale rgthree temp
  refs. Delete was the lower-risk, higher-value call. Revert: `git revert
  b4f7359`.
- **CORS: deleted our headers rather than parameterizing them.** Every caller
  is same-origin; ComfyUI's middleware owns cross-origin policy and overwrites
  per-response headers when enabled. A pack must not widen a server's CORS
  stance. The old audit line "23 routes with ACAO *" was wrong twice (24
  registrations, 12 with the header).
- **Selector: removed the auto-pick instead of special-casing the toggle.**
  Uniform rule — nothing is selected until the buyer selects it; Send tracks
  the selection. The Enter key now respects the disabled Send (it could submit
  an empty selection and kill the render), and the keyboard path can no longer
  index one past the batch end. TEXT-state sends are unaffected (its Send is
  never selection-disabled).
- **Mouth ceiling 1.7M → 4M is evidence-bounded, not a guess.** 203 logged
  decisions: real lips 0.29M–2.06M (20 dropped in 1.77M–2.06M), the full-frame
  false positive at 9.29M ×2, and NOTHING between 2.06M and 9.29M. 4M passes
  every real segment ever logged at 2× margin and kills the false positive at
  2.3× margin. The old ceiling silently deleted mouth detail on exactly the
  close-up renders where it matters. (A/B pair on the recorded dropping config
  ships with the change.)
- **Seam: executed PROPOSALS P14 rather than inventing.** 622:418 composited
  with NO mask (ComfyUI substitutes all-ones), i.e. a hard rectangle at the
  face box; 622:403's mask output was computed and discarded. FeatherMask 30px
  per edge on a ~700–900px crop. Output-changing by design; ships with the A/B
  sheet; the #114-internal seam (its own feather 18/20) is out of scope here.
- **INSTALL MODELS step 1 got its exception paragraph** instead of a full
  rewrite: the blanket "one-liners give you no nodes" warning now names the
  command it applies to and states that the gist bootstrap is the supported
  path. The old text told bootstrap buyers their working install was broken.
- **Accepted, with reasons, this run:** loader duplication (face_yolov8m ×3,
  sam_vit_b ×3, UltraSharp ×2 — consolidation needs cross-subgraph IO edits of
  the exact class that caused the 647 blocker, to save seconds of load);
  node_identifier persistence + the server-global selector waiter (single-
  tenant product, one render at a time; the harness handles it; fix touches
  accept logic verifiable only cross-browser); RPG per-action console.log
  saturation (the five perpetual interval dumps are silenced; the rest fire on
  user action only); #98 whole-image tiling (Q8 stands, untouched).

## §4 amendment, same run — the fresh install falsified an accepted premise

The three ignore.json rules scoped "environment" claimed a buyer never has
ComfyUI_Swwan / ComfyUI-Custom-Scripts / the rgthree name collision. The DoD-1
fresh install disproved it: `aiofm_setup.sh` installs the full video
`NODE_REPOS` (20 packs), so a buyer's boot logs ~40 cosmetic console errors
from Swwan's missing web files and its collisions with the rgthree-comfy this
graph needs. Reclassified product-known with reasons; the recorded fix is a
`NODE_REPOS` trim to the NSFW-used set (Impact, Subpack, essentials,
rgthree-comfy, controlnet_aux, UltimateSDUpscale + vendored INSTARAW), plus
making the video-typed "Workflow node check" profile-aware. Deferred: editing
install-check logic during a distribution cut was judged the larger risk, per
WS5's own caution. Nothing gates on these; both DoD-2 gates and the DoD-1
gate were green with zero load/run errors.

---

# §5. Run 4 (2026-08-07) — the licensing run's calls

Full list with reasons: `notes/R4-decisions.md`. Headlines only:

- **§0's table is superseded by `results/run4/MODEL-AUDIT.md`.** B1 (LUSTIFY)
  is closed by the buyer-side Civitai fetch (route a, implemented + gated);
  B2 (DMD2) is excluded from the NSFW install and staged for repo deletion;
  B3/B4 (UnMarker/GrainNet) are deleted from the shipped INSTARAW (96 types
  survive, the workflow's 7 all present). B5 (no pack licence) is UNCHANGED —
  still open, owner/lawyer item.
- **The audit found THREE NEW problems on the live render path** that §0
  never contained: `4x-UltraSharpV2.pth` (cc-by-nc-sa-4.0, loaded twice),
  `x1_ITF_SkinDiffDetail_Lite_v1.pth` (cc-by-nc-sa-4.0), `lips_v1.pt`
  (Civitai flags with no Sell). Not fixed this run — each fix changes
  rendered output. This is the top of the next session's list:
  `LEGAL-MEMO.md` §3b, candidates in `notes/Q1-currency.md`.
- **Owner actions staged, not executed** (pod token is read-only):
  `OWNER-ACTIONS.md` — publish the 8f376926 cut, delete the encumbered repo
  files (tier 1 required, tier 2 owner's call), revoke the run-3 write
  token, re-cut the video pack at leisure.
- The `non_semantic_attack.py` judgment call: removed while uncleared
  (`notes/R4B-instaraw-removal.md` §6.1 has the two-file revert).
