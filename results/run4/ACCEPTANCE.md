# ACCEPTANCE — run 4 (2026-08-07), written before the work it judges

Two tracks. Track 1 (licensing + beginner install) has priority; track 2
(quality menu) must never contend with it for the GPU.

The workflow JSON does not change this run: `OFMTech-NSFW/OFMTech_NSFW.json`
must hash `47419606…fca30d4b` at the end of the run, from either track.

---

## Track 1 — a product that can legally be sold, beginner-installable

### A. Identification and flags (evidence, not memory)

- **A1** `SDXLNSFW.safetensors` identified by full SHA256 (HF LFS oid) through
  `civitai.com/api/v1/model-versions/by-hash/`; the stored response's SHA256
  equals the LFS oid; model id, version id and upstream filename named.
  Response file in `results/run4/civitai/`.
- **A2** Licence flags quoted anywhere this run come from an API response
  fetched THIS SESSION and stored under `results/run4/`. No flag quoted from
  memory or LICENCE-AUDIT.md (which does not exist in this repo — noted).

### B. Route (a) — buyer-side Civitai fetch

- **B1** The setup script obtains `SDXLNSFW.safetensors` ONLY from Civitai
  (version 2155386) using the buyer's own Civitai token. The HF bulk download
  and every fallback path exclude it. Grep-provable in the script.
- **B2** The downloaded file is verified by full SHA256 against
  `d234c60d67cedfe69433e3934a459707c2cf43b30232d3db2becd10371d2220f` before
  the install proceeds; mismatch is fatal and named.
- **B3** The file lands where the NSFW graph loads it from (verify which
  loader/dir the workflow actually uses; do not assume both repo paths are
  needed).
- **B4** Each failure stops the install with a message naming the cause and
  the buyer's next action — none demoted to `warn`:
  (i) missing Civitai token, (ii) invalid token / 401, (iii) valid token but
  no access / 403, (iv) version id no longer resolving / 404 — message names
  LUSTIFY GGWP (V7) by name, (v) insufficient disk before the download
  starts, (vi) SHA256 mismatch. Negative tests for at least (i), (ii), (iv),
  (vi) with output captured under `results/run4/routea/`.
- **B5** A preflight names the model and fails loudly BEFORE any bytes are
  downloaded if version 2155386 stops resolving.
- **B6** Buyer journey grows by AT MOST one step over today's nine, and that
  step is putting a Civitai token where the script reads it. No manual file
  placement, no manual restarts.
- **B7** Re-running the script with the checkpoint already present and
  correct skips the download (idempotent).

### C. Repo cleanup (owner-gated — pod token is read-only, role checked)

- **C1** `OWNER-ACTIONS.md` contains exact commands to delete
  `models/checkpoints/SDXLNSFW.safetensors`,
  `models/diffusion_models/SDXLNSFW.safetensors`, and the B2/dead-weight
  files the owner approves, plus the republish command for the new pack —
  with the stated impact on the VIDEO pack for each (from the video pack's
  own fetch list, extracted from the published tarball, not assumed).
- **C2** The new NSFW install is proven to need none of the files those
  commands delete (the fresh gate runs with the checkpoint absent locally
  and excluded from the HF fetch).

### D. The model audit

- **D1** Every file under `models/` in the live HF tree
  (`results/run4/hf_tree_before.json`) gets a row in
  `results/run4/MODEL-AUDIT.md`: identification method (Civitai by-hash /
  HF LFS-oid match against a named candidate repo / config text /
  UNIDENTIFIED), source, licence or flags with the stored response cited,
  and a verdict. Unidentifiable files say UNIDENTIFIED, not a guess.
- **D2** Files the setup script fetches from public URLs outside the HF repo
  (the `dl` fallback lines and render-time models) are audited the same way.
- **D3** The audit states its own counts (LFS binaries vs configs vs
  placeholders) rather than inheriting "76"/"77" from the brief.

### E. QUESTIONS §0 B2–B4 closed

- **E1** DMD2: proven unreferenced by the NSFW workflow (grep of the graph);
  excluded from the NSFW install; repo deletion command prepared with video
  impact stated (video setup line :810 checked in the extracted tarball).
- **E2** UnMarker + GrainNet: removed from the INSTARAW that ships in the new
  pack via a code change; the four untraced modules traced; after removal the
  pack registers every node type the NSFW workflow uses (list-diff before vs
  after, expected loss = only the removed nodes); no unmarker/grainnet file in
  the cut archive (grep of the tarball listing); the fresh gate render passes
  on the modified pack.
- **E3** `v1-5-pruned-emaonly-fp16.safetensors`: referenced-by-nothing claim
  re-checked this session; owner deletion command prepared.

### F. Pack-list trim

- **F1** `NODE_REPOS` in the NSFW setup script contains only packs the NSFW
  graph needs (+ vendored INSTARAW); Swwan gone; pysssss gone unless proven
  needed; the "Workflow node check" no longer hardcodes video types on the
  NSFW path.
- **F2** The fresh-install boot log contains zero Swwan/pysssss lines and no
  rgthree extension-name collisions.
- **F3** Every node type the NSFW workflow references registers on the fresh
  install (the script's own workflow-derived check passes).

### G. INSTALL MODELS.txt

- **G1** Rewritten for a reader who has never used ComfyUI (terms explained
  at first use), includes the Civitai token step with the exact clicks, and
  never contradicts the gist-bootstrap path.

### H. The fresh-install gate (the beginner claim, made testable)

- **H1** Fresh tree: empty `custom_nodes`, no INSTARAW, no installed
  workflow; models hardlinked EXCEPT `SDXLNSFW.safetensors`, which must be
  absent so the Civitai path runs for real; the LIVE gist one-liner; the new
  pack served through `AIOFM_PACK_URL` (publish itself is owner-gated).
- **H2** Install exits 0 with log evidence the checkpoint came from Civitai
  and passed SHA256.
- **H3** Browser gate on that install: both Luna LoRAs picked through the
  widget menus, a long character description (≥60 tokens) typed into `#106`,
  Run pressed, selector answered by click, render delivered, PNG on disk,
  screenshots saved under `results/run4/fresh/`.
- **H4** The bad-token negative path stops the install with the named
  message (captured, not claimed).

### I. Memo and handoff

- **I1** `LEGAL-MEMO.md` separates: proven facts (with file citations),
  what changed, residual exposure, and the judgement calls that are the
  owner's or a lawyer's. It does not claim "licensing solved".
- **I2** `HANDOFF.md` updated as the current statement; every change its own
  commit; QUESTIONS.md gains a §5 for this run's calls.

---

## Track 2 — quality menu (recommend-only)

- **Q1** Nothing in `OFMTech-NSFW/` changes from track 2; the workflow hash
  is unchanged; no track-2 render uses the shipping output directory.
- **Q2** All track-2 GPU work serializes behind `flock` on
  `/workspace/nsfw-fix/.gpu_lock` and runs on a dedicated ComfyUI process
  (port 19188, own output dir), started and killed per arm. The main
  instance on 18188 is never touched: no queue posts, no /free, no restart.
  Zero track-2 renders during the track-1 fresh-gate window (the gate holds
  the same lock).
- **Q3** Every menu entry has: a contact sheet with every tile labelled
  (what changed + its timing) and the baseline identified on the sheet; the
  sheet path; cost in seconds and VRAM; licence flags READ FROM AN API this
  session (response stored under `results/run4/quality/licences/`) for any
  recommended model file; a recommendation. If a metric winner looks worse
  by eye, the entry says so and ranks by sight.
- **Q4** bbox_crop_factor arms: fresh server process per arm (the NaN
  poisoning history is why), one variable per arm, cold (no cache reuse —
  `execution_cached` empty in the history entry), n stated per cell.
- **Q5** `notes/QUALITY-MENU.md` exists, ranked, and every item is
  recommend-only.
