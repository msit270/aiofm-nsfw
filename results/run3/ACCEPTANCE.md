# Run 3 — acceptance criteria (written BEFORE the work, 2026-08-07)

Verifier subagents judge against THIS file. Every criterion names the evidence
file that must exist. "Verified" means a tool result from this session, on disk.

## A. The guard (DoD 3)
- A1. `OFMTech_NSFW.json` contains `ImpactIsNotEmptySEGS` + `ImpactConditionalBranch`
  inside sg622 per notes/C-fix-design.md C1, plus a visibility companion (C1b).
- A2. P1 preflight: `tools/preflight/integrity.py` → 0 problems on the patched file.
- A3. P2 conversion: `--no-submit` harness run, exit 0, no error naming 660/661.
- A4. P3 inertness: constant-folded API diff vs pre-guard export → 0 differences.
  Evidence: results/run3/guard/.
- A5. P4-FAIL on :18188 (repro instance, positive control first): a prompt in a
  crash band renders to `status: success`, eyes-stage nodes absent from executed
  set, delivered image == 621:163 tap (within-run identity). Evidence: history
  JSON + images under results/run3/guard/.
- A6. Happy path byte-identical: fixed seed, cache cleared, guarded vs unguarded
  render — byte-identical delivered PNG (pixel compare, not hash-only).
- A7. No prompt length crashes the render: arms at 32, 46, 103, 110 tokens on the
  final config all reach `status: success`. 103/110 may be degraded but must be
  loud (warning visible in /history outputs).

## B. The eye regression (DoD 5)
- B1. A decision exists: keep cpu / revert / alternative — with evidence.
- B2. If any device config changes: A/B eye-tile sheet at 1:1 comparing final
  config vs pre-fix (`default`) vs full-cpu, same seed, cold. Labelled.
- B3. Band coverage re-verified on the final config: 46-token arm clean render
  (healthy face, YOLO ≥0.75), on the repro instance with a same-day positive
  control.
- B4. The verdict + trade-off in the final report, with sheet paths.

## C. Setup assertion (DoD 4)
- C1. aiofm_setup.sh fails loudly (nonzero, message naming the black-face fix)
  when the installed ComfyUI's CLIPLoader lacks the optional `device` input.
- C2. Negative test: assertion demonstrably fires on a doctored old nodes.py
  (or equivalent), and passes on the real tree. Evidence: results/run3/setup/.

## D. Browser gate (DoD 2)
- D1. Current (final) workflow installed as the live saved workflow for :18188
  (/workspace/ComfyUI/user/default/workflows/OFMTech_NSFW.json), hash recorded.
- D2. :18188 shown to reproduce the crash the same day (positive control arm:
  pre-guard config, crash-band prompt → 622:403 error).
- D3. Full --drive-selector browser gate on the final bytes, on :18188, with a
  103–120-token prompt in #106: exit 0, render completes through the browser.
- D4. Same gate with a clean-band real prompt (46 tok): exit 0, healthy image
  (check_image.py verdict "real render", YOLO face present).

## E. ignore.json (DoD 7)
- E1. Every rule either (a) removed because the underlying error is fixed, or
  (b) kept with a written justification in the final report.
- E2. product-known count == 0 in the shipped harness config.
- E3. A gate run on the final bytes on a clean install shows zero ignored
  product-known events (green on merits). Evidence: gate result.json.

## F. Selector trap (DoD 8)
- F1. popup.js: clicking the auto-picked/only image can no longer produce a dead
  Send. Behavior decided, coded, and the mechanism described in the report.
- F2. Browser-level proof: gate run drives the selector with a single click and
  Send is enabled at press time (result.json shows it). Multi-image path not
  regressed (harness or manual DOM check on a batch >1 if reachable; else record).

## G. Pack + publish (DoD 6)
- G1. build_pack.sh re-cut; tarball sha256 recorded; workflow-inside-archive hash
  == repo workflow hash; file count vs previous cut reconciled (adds/removes named).
- G2. Uploaded to msit270/AIOFM-Pack; buyer-side HEAD shows x-linked-etag ==
  new sha256 and x-linked-size == new byte size.
- G3. One-line install command in the final report, byte-exact.

## H. Fresh install end-to-end (DoD 1)
- H1. A fresh ComfyUI tree (empty custom_nodes) installed via the LIVE gist URL
  (not a local copy), exit 0.
- H2. Browser session on that install: workflow opened from sidebar, zero red
  nodes, both Luna LoRAs selected via widget menus, a real character description
  typed into #106, queued, selector answered, render completes.
- H3. Screenshot of the final image on canvas + the delivered PNG saved under
  results/run3/fresh/. check_image verdict recorded.
- H4. Deviations from a true fresh pod stated (models cache, same GPU, etc.).

## I. Known-opens (each fixed or explicitly accepted in the final report)
- I1. #600/#592 reseed claim re-checked on current bytes (expect: already fixed).
- I2. cfg=1 negatives: state on current bytes verified; resolution recorded.
- I3. #597→#616 round-trip: verified present (decision "D1 stays reverted").
- I4. Double face detail: recommendation + existing A/B sheet referenced.
- I5. ControlNet/SetUnion: verified absent from current bytes.
- I6. sg5/#623: removed with inertness proof, or accepted with reasoning.
- I7. Subgraph names: verified named on current bytes.
- I8. CORS: fixed in pack or accepted with reasoning.
- I9. LICENSE beside cg-image-filter derivation: present in pack.
- I10. Loader duplication: decision recorded with reasoning.
- I11. Mouth #648 silent skip: fixed with A/B + threshold rationale, or accepted
  with the evidence that stopped the fix.
- I12. Cyrillic localized_name: fixed (inert proof) or accepted.
- I13. Collapsed #620 / unlabelled promoted widgets: fixed (inert proof) or accepted.
- I14. node_identifier cross-client selector: fixed or accepted.
- I15. Seam at face-box edge: attempted with sheet, or accepted.
- I16. Stale rgthree temp filenames / comparers: fixed with proof.

## J. Process
- J1. One commit per change, reasoning in message, pushed.
- J2. HANDOFF.md rewritten as re-grounding; QUESTIONS.md updated; notes/ updated.
- J3. Every report claim traceable to a file in results/run3/ or a commit.
- J4. LUSTIFY (§0 B1) untouched beyond keeping QUESTIONS.md §0 accurate.
