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
