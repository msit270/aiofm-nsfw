# R4 — run-4 judgment calls, with the option taken and why

One line per call here; full evidence lives where each line points. This file
feeds QUESTIONS.md §5.

1. **LUSTIFY pinned to version id 2155386 by TWO hash checks** — preflight
   compares Civitai's published SHA256 against the baked expectation before
   any download, and the downloaded bytes are re-hashed after. A creator
   swapping the file under the same version id (or our constant drifting)
   fails closed with both hashes printed. Constants are env-overridable —
   that is what let every negative test run against the SHIPPED bytes
   instead of a sed-patched copy (`results/run4/routea/SUMMARY.md`).
2. **The gist bootstrap was deliberately NOT edited.** The Civitai key check
   lives in the setup script's preflight instead. Same failure quality
   (stops in the first minute, names the fix), zero risk from the gist raw
   URL's stale-CDN behavior (STATE.md trap), and no republish coordination.
3. **The diffusion_models mirror of SDXLNSFW stays**, as a hardlink of the
   Civitai-fetched file (0 bytes). The NSFW graph loads only the
   checkpoints copy (CheckpointLoaderSimple #613); the mirror preserves
   layout parity with existing installs and whatever else reads it. The
   fresh gate asserts the mirror shares the checkpoint's inode — if it ever
   arrives as a separate file, that is a repo leak and the gate fails.
4. **dmd2 + v1-5 + both SDXLNSFW paths are excluded from the bulk pull in
   the script** even though deletion from the repo is the real fix (owner
   action). Two layers because the fnmatch sweep is exactly how "removed"
   files kept shipping twice before.
5. **IPAdapter_plus and ofmtechclip were dropped from NODE_REPOS** beyond
   the six packs QUESTIONS §4 named: zero node types in the current
   workflow resolve to either (the IPAdapter graph path was deleted in
   run 2). Model downloads were NOT trimmed — the brief's trim is the pack
   list; the model-profile design is accepted scope.
6. **The RIFE/SAM2 render-time stage went with the video packs** — RIFE's
   checkpoint lands INSIDE the removed Frame-Interpolation pack (an
   import-failing bare dir under custom_nodes on every boot), SAM2 is
   loaded only by the removed segment-anything-2. The NSFW graph uses
   neither (grep).
7. **SageAttention stays** — prior run's logged decision stands; nothing
   this run touched it.
8. **INSTARAW `non_semantic_attack.py` + its node removed although
   uncleared rather than proven-encumbered** — the risk-removing option;
   docstring says "core UnMarker-style optimization", upstream comparison
   never covered it, node absent from the workflow. Two-file revert path in
   `notes/R4B-instaraw-removal.md` §6.1. Owner may overrule.
9. **The three NEW live-path licence problems (UltraSharpV2 ×2,
   SkinDiffDetail, lips_v1) were NOT fixed** — every fix is
   output-changing (model swap) and the standing rule sends those to the
   owner with A/B sheets. Candidates with API-read permissive licences are
   staged in `notes/Q1-currency.md`. lips_v1 alone could take the
   LUSTIFY-style buyer-side fetch (its flags are the same shape); not done
   this run because it, too, warrants the owner choosing between fetch and
   swap.
10. **Track-2 lock starvation, caught and fixed mid-run:** flock is not
    FIFO; three Q drivers re-acquiring in a loop starved the track-1 gate
    for minutes. Yield protocol: Q agents finish the in-flight arm, then
    wait on the sentinel `/workspace/nsfw-fix/.track1_gate_done`. Lesson
    for any future shared-lock design here: a lock alone is not a priority
    scheme.
11. **INSTARAW registered-type count: QUESTIONS said 95, measured 98
    (twice, two trees) before the edit, 96 after.** Recorded, not chased;
    the 95→0 naive-delete mechanism is independent of the starting count.
12. **The audit's "76 files" premise corrected**: 43 LFS binaries (42
    unique), 11 configs, 20 placeholders. And a method lesson worth
    keeping: **a Civitai by-hash 404 means "not published as a bare file",
    not "not on Civitai"** — lips_v1 was found by downloading the
    candidate's ZIP and hashing its members.
13. **Node-check number now derives to 54** (baseline 27 NSFW types ∪
    54 workflow-derived; baseline is a strict subset). Verified against the
    fresh server's /object_info: none missing. INSTALL MODELS.txt quotes
    54 and says the script derives it, so the doc cannot silently drift.

## Post-verifier addendum (same day)

The fresh-context verifier passed every acceptance section and raised six
non-blocking defects. Disposition:
- **Fixed:** INSTALL MODELS.txt now documents BOTH healthy forms of the
  summary's nodes line (the "verified on first start" fallback would have
  told an obedient beginner to stop on a healthy install); MODEL-AUDIT §C
  carries a correction note (it audited the pre-trim script — over-inclusion
  only); LEGAL-MEMO's licensingFee sentence now cites the version-level
  response file it actually lives in.
- **Accepted, recorded:** `count_nodes.py --cpu` is inert (ComfyUI ignores
  sys.argv without enable_args_parsing) — results unaffected, verifier's
  CPU-only re-run matched exactly; the gist bootstrap prints the repo name
  rather than the mirror URL under AIOFM_PACK_URL (pre-publish testing only,
  buyers never see it, and editing the live gist for a log line is worse
  than the line); the idempotent re-run skip is size-only by design — the
  realistic same-size file IS the same bytes (fresh installs stay fully
  SHA-gated, and re-hashing 6.9 GB on every re-run taxes every buyer for a
  hypothetical).
- The INSTALL MODELS fix forces a re-cut; the member-level diff against the
  gate-proven 8f376926 cut is recorded in the re-cut commit.
