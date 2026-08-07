# VERIFIER_NOTES — run 4 (fresh-context verifier, 2026-08-07)

Adversarial re-derivation of `results/run4/ACCEPTANCE.md` sections A–G and I
(+ H's prerequisites; H itself not judged per instruction). Nothing below is
taken from commit messages or notes — every check was re-run from the files,
scripts, and stored API responses named beside it. Read-only run: this file
and scratch space (`…/scratchpad/verify4/`) are the only writes; no server
contacted; the one Python import harness was re-run CPU-only.

## Verdict, one line per section

| section | verdict |
|---|---|
| A. Identification & flags | **PASS** (A1, A2) |
| B. Route (a) | **PASS** (B1–B7) |
| C. Repo cleanup | **PASS** (C1; C2 install-side proven, render side is H) |
| D. Model audit | **PASS** (D1, D3; D2 pass with stale-citation defect #1) |
| E. QUESTIONS §0 closures | **PASS** (E1, E2, E3; E2's render clause is H-gated) |
| F. Pack-list trim | **PASS** (F1, F2; F3 pass with note) |
| G. INSTALL MODELS.txt | **PASS** (minor doc nits, defect #4) |
| H prerequisites only | **SOUND** (harness logic + install.log verified; H not judged) |
| I. Memo & handoff | **PASS** (I1, I2) |
| Workflow invariant | **PASS** (repo copy and tarball copy both `47419606…fca30d4b`) |
| Track-2 non-interference | **PASS** (pack source git-clean; quality dirs never touch it) |

## Ranked defect list

No blocking defects found. Six non-blocking items, worst first:

1. **MODEL-AUDIT §C audits the pre-trim script** (minor, evidence hygiene).
   Its line numbers (851–856, 910, 957–958, 990, 1374–1375, 1399–1404) match
   `cbc4ac2^`, not the shipped script (actual: 1134–1140, 1202, 1249–1250,
   1282), and two of its rows — `rife49.pth` and
   `sam2.1_hiera_base_plus-fp16.safetensors` — are not fetched by the shipped
   NSFW script at all (grep: zero hits; they left with the trim). Error is
   over-inclusion only (both moot rows are CLEAN); no fetched file is
   missing from §C.
2. **`count_nodes.py`'s `--cpu` is inert** (minor, latent harness bug).
   ComfyUI's `cli_args` ignores `sys.argv` unless
   `comfy.options.enable_args_parsing()` is called first
   (`/workspace/comfy-r5-verify/comfy/options.py`: `args_parsing = False`),
   so the harness's `sys.argv = ["main.py", "--cpu"]` does nothing and every
   stored run initialized CUDA on import (with `CUDA_VISIBLE_DEVICES=""` it
   crashes in `model_management.py:201`). Results are unaffected — my
   CPU-only re-run (args parsing enabled, harness bytes unmodified) matches
   the stored AFTER list exactly.
3. **Gist bootstrap misnames the pack source under override** (cosmetic).
   `gist/aiofm_setupnsfw.sh:74` prints "downloading the pack from
   msit270/AIOFM-Pack" unconditionally, so `fresh/install.log`'s own opening
   lines say HF while the pack actually came from the `AIOFM_PACK_URL` local
   mirror (disambiguated only by `driver.log`'s `[pre-publish]` lines and the
   7904k size == the run-4 tarball).
4. **INSTALL MODELS.txt's "all 54 present" is conditional** (cosmetic, doc).
   The summary prints `all 54 present` only when ComfyUI was running to be
   restarted; otherwise it prints the honest `all packs present — verified on
   first start` (`aiofm_setup.sh:2210-2213`) — which the guide's "if either
   line says anything else, stop and read the warnings" would misread as a
   failure. Same doc also says the installer restarts ComfyUI "by itself"
   (step 2) vs the script's supervised-only restart (step 4's "when it can"
   is the accurate wording).
5. **Idempotent skip is size-only** (observation, within acceptance letter).
   `lustify_installed()` compares byte count (6,938,099,634) not hash, so a
   same-size wrong file already on disk is accepted by preflight and
   `fetch_lustify` on re-runs. Fresh installs are fully protected (full
   SHA256 gate before install).
6. **LEGAL-MEMO §2.2 citation nit.** `licensingFee: 1` is in
   `civitai/sdxlnsfw_by_hash.json` (a version response — consistent with
   "the version carries"), not in `civitai/lustify_model_573152.json`, which
   is the file that sentence's context cites. The fact itself is stored and
   true.

---

## Per-criterion detail (evidence = file + what I found there)

### A

- **A1 PASS** — `results/run4/hf_tree_before.json`: both
  `models/{checkpoints,diffusion_models}/SDXLNSFW.safetensors` carry
  `lfs.oid d234c60d67cedfe69433e3934a459707c2cf43b30232d3db2becd10371d2220f`
  (6,938,099,634 B). `results/run4/civitai/sdxlnsfw_by_hash.json`: SHA256
  `D234C60D…D2220F` (case-insensitively equal), modelId 573152, version id
  2155386 "GGWP (V7)", file `lustifyNSFWCheckpoint_ggwpV7.safetensors`,
  creator coyotte.
- **A2 PASS** — `civitai/lustify_model_573152.json`:
  `allowCommercialUse ['RentCivit','Image']`, `allowDerivatives False`,
  `allowDifferentLicense False`, `allowNoCredit True` — byte-exact match to
  LEGAL-MEMO §2.2. V8/V9/V10 Published/Public as §4 claims.
  `LICENCE-AUDIT.md` confirmed absent. (Nit: defect #6.)

### B

- **B1 PASS** — `OFMTech-NSFW/aiofm_setup.sh`: SDXLNSFW appears only in the
  exclude list (215–216), comments, `LUSTIFY_*` constants (386–394), and the
  hardlink block (1180–1188, which has **no** repo fallback). Zero
  `dl`/`dl_public`/wget lines fetch it (full `dl` inventory checked, lines
  1138–1300). Bulk pull: `--include "models/*"` + `--exclude` × 4
  (both SDXLNSFW paths, dmd2, v1-5). fnmatch simulated with the installed
  `huggingface_hub` 1.5.0 semantics (`filter_repo_objects` read from source:
  item passes only if allow matches AND no ignore matches — deny wins) over
  the real 77-path tree: exactly the 4 paths filtered, 70 fetched, zero
  leaks; video profile's 12 include patterns match none of the four. The
  gist bootstrap (`gist/aiofm_setupnsfw.sh`) fetches only the pack tarball.
  Integrity check (1682–1717) reports, never refetches.
- **B2 PASS** — `LUSTIFY_SHA256` is the full 64-hex hash (== the LFS oid);
  post-download compare is full-string equality (`aiofm_setup.sh:495-503`),
  mismatch = `die` + file deleted. Preflight step 3 compares the API's
  full SHA256 to the same constant (907).
- **B3 PASS** — `OFMTech_NSFW.json`: the only node loading it is
  `CheckpointLoaderSimple` #613 (`['SDXLNSFW.safetensors']`) →
  `models/checkpoints/`, exactly where `fetch_lustify` installs. The
  `UNETLoader` (#113) loads `zimage.safetensors`, not this file. The
  diffusion_models copy is a hardlink for layout parity.
- **B4 PASS** — `results/run4/routea/`: all six `neg_*.exitcode` files
  contain 1, both `pos_*` contain 0. Each `.out` names cause AND buyer
  action: (i) key how-to 5 steps; (ii) HTTP 401 + fresh-key steps;
  (iv) "LUSTIFY! GGWP (V7) did not resolve … HTTP 404" + contact-support;
  (v) need vs free + provision instructions; (vi-a) both full hashes +
  refuse; (vi-b) both full hashes + bad file deleted. `die()` exits 1
  (`aiofm_setup.sh:185`); grep of lines 386–507 and 858–956: **zero `warn`**,
  9+9 `die`. The extracted test harness
  (`scratchpad/civitest/extracted_lustify.sh`) is byte-identical to script
  lines 386–507 (diff: empty). The 403 path (iii) exists in code at both
  stages, untested — the criterion requires tests only for i/ii/iv/vi.
- **B5 PASS** — preflight stage at :868, model download stage at :963,
  `fetch_lustify` call at :1152; runtime order confirmed in
  `fresh/install.log` ([6/14] preflight before [7/14] downloads), and
  `neg_iv` dies inside preflight before any model stage. Caveat noted:
  pip packages and the SageAttention `wheels/*` pull can run earlier — no
  **model** bytes precede the preflight.
- **B6 PASS** — one added buyer action (step 1b, Civitai key →
  `/workspace/.civitai_token`); the guide's NOTES section shows the manual
  detector placement was actually removed; restart handling unchanged.
- **B7 PASS** — `routea/pos_idempotent.out`: exit 0, "already installed …
  nothing to fetch". (Size-only check: defect #5.)

### C

- **C1 PASS** — `/venv/main/bin/hf repos delete-files --help` on this pod:
  `REPO_ID PATTERNS...` with `--commit-message` — exactly the syntax used;
  help text confirms fnmatch/`*`-recursive, matching OWNER-ACTIONS' own
  warning. All 14 delete paths contain no `*?[]` and each exists verbatim in
  `hf_tree_before.json`. `hf upload REPO_ID LOCAL PATH_IN_REPO
  --commit-message` — valid. Publish expect-hash
  `8f37692638535f004c19e93454c90f395774ca4bba737f8fb9cbf0adf21c41f5` ==
  sha256 of `dist/AIOFMTech-NSFW.tar.gz` I computed on disk; expect-size
  8,094,057 == on-disk size. Video impact re-derived from the **extracted
  published video tarball** (scratchpad copy): its `aiofm_setup.sh` lines
  770/802 (SDXLNSFW), 810 (dmd2), 782–789 (flux/High/Low set) as cited; its
  `dl()` failure branch is `warn` (:734), not `die`; its workflow JSON
  references none of the 14 files.
- **C2 PASS (install side)** — `fresh/driver.log`: 4 files withheld from the
  hardlinked tree; installer exit 0; installed checkpoint sha256
  `d234c60d…` (full) verified post-install; diffusion copy same inode
  (proves Civitai origin, no repo fetch); dmd2 + v1-5 "still absent
  (excluded)" after install. The render half of C2's gate is section H.

### D

- **D1 PASS** — coverage: all 43 `models/` LFS binaries from the tree have
  rows in `MODEL-AUDIT.md` (programmatic check: zero missing). Spot-checked
  5 random rows against their stored responses, all exact:
  Z-TurboSkinForge (2305301/2593828, `['RentCivit','Rent']`, deriv F,
  noCredit F — sha match), HyperFleshUltrav4 (978314/1413133, incl `Sell`,
  deriv F, noCredit F — sha match), NovaMind_X1 (oid found in alibaba-pai
  tree, `license:apache-2.0`; re-list 1953737 `['RentCivit']` as recorded),
  sam3.pt (**git-pointer proof independently re-derived**: sha1 of the
  reconstructed LFS pointer blob == facebook/sam3's git oid
  `5b7c2eab…`, with the stored tree's lfs.oid indeed redacted to asterisks
  as the audit's anomaly note says), primary_net_v2 (2420939/2721846, incl
  `Sell`, diffLic F — sha match). Headline rows: 4x-UltraSharpV2
  `license:cc-by-nc-sa-4.0` in `hf/Kim2091_UltraSharpV2_meta.json` + oid in
  that repo's tree + OMDB agrees; x1_ITF_SkinDiffDetail CC-BY-NC-SA-4.0 in
  `external/omdb_1x-ITF-SkinDiffDetail-Lite-v1.json` **which carries our
  full sha256** (hash match, not name match) + oid in uwg tree; lips_v1
  flags `['Image','RentCivit']` no Sell in `verify/civitai_model_142240.json`
  and I re-hashed the stored `adetailer_lips.zip` member myself:
  `ce9fe145…fe99`, 6,222,638 B — exact match to the tree oid/size.
- **D2 PASS with defect #1** — §C rows exist with stored responses for every
  outside-repo fetch (TDD apache-2.0, Bingsu apache-2.0 tag, sam_vit_b
  untagged mirror/Apache upstream, vitpose/yolov10m), but the section was
  written against the pre-trim script (stale line numbers; rife49/sam2 rows
  now moot).
- **D3 PASS** — counts re-derived from `hf_tree_before.json`: 77 files =
  43 models-LFS (42 unique oids) + 11 configs + 20 zero-byte placeholders +
  `.gitattributes` + 2 dist tarballs. Matches the audit's stated counts,
  not the brief's "76".

### E

- **E1 PASS** — `grep -c dmd2` in `OFMTech_NSFW.json`: 0; in the extracted
  video workflow: 0. Excluded from bulk (B1 simulation). Tier-1 delete
  staged. Video setup line :810 verified in the extracted published
  tarball. cc-by-nc-4.0 re-verified in stored
  `hf/tianweiy_DMD2_meta.json` (`license:cc-by-nc-4.0`).
- **E2 PASS** — my own run of `results/run4/instaraw/tools/count_nodes.py`
  (unmodified bytes, CPU-only, scratch copy of
  `OFMTech-NSFW/ComfyUI_INSTARAW`, host `/workspace/comfy-r5-verify`, no
  ports touched): **96 types, import_ok, node list identical to stored
  count-AFTER.json**; all 7 workflow INSTARAW types present (list extracted
  from the workflow myself); BEFORE(98)→AFTER(96) delta is exactly
  `INSTARAW_NeuralGrain` + `INSTARAW_Spectral_Normalizer`. Binary-safe grep
  (`grep -r -i -a`) for unmarker/grainnet/adaptive_filter/neural_grain over
  the pack source AND the tarball-extracted pack: hits only
  `THIRD_PARTY_NOTICES.md`. Tarball listing: zero `__pycache__`, `*.pyc`,
  `*.pt`, `*.pth` entries anywhere; none of the 11 deleted files (list
  re-derived from commit 9776061's D-entries) present. The "fresh gate
  render passes" clause: evidence exists (`fresh/gate.log` RESULT: PASS)
  but is judged under H, not here. (Harness defect #2 noted.)
- **E3 PASS** — `v1-5-pruned`: 0 refs in either workflow JSON; absent from
  the video setup's fetch list (grep: none); present in the NSFW script only
  as an exclusion; tier-1 delete staged.

### F

- **F1 PASS** — mapping re-derived from `OFMTech_NSFW.json` node
  `properties.cnr_id`: 27 core types, 7 INSTARAW, and exactly six external
  packs (impact-pack 12, impact-subpack 1, controlnet_aux 1, essentials 3,
  ultimatesdupscale 1, rgthree 2 — 27 non-core types total). `NODE_REPOS`
  (:1363-1370) holds exactly those six repos; no Swwan/pysssss/IPAdapter
  anywhere outside explanatory comments (workflow JSON itself has zero
  IPAdapter/ControlNet/DepthAnything strings); the static node check
  (:1815-1847) hardcodes only these NSFW types. `bash -n`: clean.
- **F2 PASS** — `fresh/comfy-fresh.log`: 0 lines matching swwan/pysssss,
  0 IMPORT FAILED/Cannot import, no rgthree collision lines; exactly the 7
  intended packs load.
- **F3 PASS (with note)** — static check "all 27 node types found on disk"
  in `install.log:114`. The script's runtime /object_info union check did
  not execute during the install (ComfyUI not running at [14/14] — its
  documented, honestly-summarized behavior). On the booted fresh instance
  the gate's node audit found every workflow type registered except
  frontend-only `MarkdownNote` (exactly what the script's own filter
  exempts), 0 red nodes, and the graph validated and rendered.
- **"54"** — recomputed via the script's own union logic
  (baseline 27 ∪ workflow-derived 54, subgraph hosts and Note/MarkdownNote
  filtered): **54**, with only `OFMTech_NSFW.json` beside the script (repo
  and tarball each ship exactly one workflow JSON).

### G

- **G1 PASS** — read end-to-end. Terms defined at first use (workflow,
  model, checkpoint, custom nodes, LoRA, VRAM). Civitai key steps
  (:73-75) are complete and identical to the script's `CIVITAI_KEY_HOWTO`
  (account → profile picture → Account settings → API Keys → Add API key →
  name → Save → copy → echo to `/workspace/.civitai_token`), plus the
  fail-safe "install stops in its first minute" (matches preflight
  behavior). No contradiction of the gist-bootstrap path — the manual-run
  warning matches the script's PIPED detection, and the bootstrap is named
  as the supported path. Claims verified against the script/workflow:
  detectors auto-hardlinked into `models/ultralytics/bbox` (:1253-1259);
  both LoRA stacks ship `None` (#618, #116); selector timeout 600 s with
  'send none' (#603 widgets). Node-count 54 verified above. Nits: defect #4.

### H prerequisites (H itself not judged)

- `tools/browser_harness/fresh_install4.sh` logic verified: preconditions
  refuse to run if the target exists or anything answers on 31960/31961/31962
  (so it cannot touch 18188/19188); fresh tree rsync excludes models/
  custom_nodes/user/output/input/temp (empty custom_nodes = 0 confirmed in
  driver.log); models hardlinked with the 4 withholds enforced and verified
  absent; LIVE gist one-liner; `AIOFM_PACK_URL` mirror is the bootstrap's
  own documented override, with the served tarball's sha256 logged
  (`8f376926…` == dist file); post-install it verifies full checkpoint
  sha256, hardlink inode equality, and continued absence of dmd2/v1-5;
  boots only its own port.
- `fresh/install.log`: complete, "installer exit 0 after 170s", checkpoint
  "installed from Civitai and SHA256-verified (LUSTIFY! GGWP (V7))",
  preflight all-green before any model stage.

### I

- **I1 PASS** — LEGAL-MEMO separates §2 PROVEN (each item's citations
  spot-verified above), §3 NOT-resolved owner/lawyer calls (3a–3f), §4
  residual dependencies; it explicitly refuses the "solved" claim ("the
  product is not clean even with LUSTIFY solved", §3b) and states the three
  live encumbered files.
- **I2 PASS** — HANDOFF.md rewritten as the run-4 statement; its archive
  facts re-verified (8f376926…, 8,094,057 B, **159 files** — my tar listing:
  182 entries − 23 dirs = 159). QUESTIONS.md has "§5. Run 4 (2026-08-07)"
  (:383). One scoped commit per change (cbc4ac2 route, b0ab0d4 trim,
  f7da36b header, 9a09fcd docs, 9776061 INSTARAW, 62acf44 cut, 9c37b00
  audit, 8c622a7 memo/owner/questions).

### Invariants

- **Workflow hash PASS** — `sha256sum OFMTech-NSFW/OFMTech_NSFW.json` =
  `4741960602085c6277eecd5f3d25e8e023e71df842c5987714886ef2fca30d4b`; the
  copy extracted from `dist/AIOFMTech-NSFW.tar.gz` hashes identically.
- **Track-2 non-interference PASS** — `git status --porcelain --
  OFMTech-NSFW/`: empty (no modified or untracked files under the pack);
  all uncommitted changes sit under `results/run4/quality/`,
  `results/run4/fresh/`, `notes/Q*.md`, and `.gpu_lock`; grep of
  `results/run4/quality/` (including its tools) for `OFMTech-NSFW`: zero
  hits.
