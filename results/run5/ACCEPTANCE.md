# run-5 acceptance criteria (written 2026-08-07 ~21:30, BEFORE verification)

Phase-1 (architecture) claims are acceptable only if:

A1. Every likeness number traces to `results/run5/likeness_scores.json`, which
    traces to PNGs under /workspace/run5/output/ rendered this session, with
    per-arm submitted graphs in `results/run5/<batch>/<arm>/api_graph.json`.
A2. The ZIT reference band and the no-LoRA floor both exist as measured rows
    (identity claims are relative to BOTH anchors, not absolute).
A3. Stage attribution (e.g. "619:600 destroys identity", "617 smooths") is
    supported by consecutive-tap deltas within a SINGLE arm (same render),
    not across arms.
A4. The A0_repeat arm is bit-identical to A0 on the final frame (determinism
    guard for the persistent-server method). If it is not, all same-server
    pixel comparisons are invalid and must be redone fresh-process.
A5. Structural wiring claims (LoRA-less 619:600/587:92; colormatch topology;
    prompt contents) are quoted from api_final.json / the api_graph.json of
    the arm concerned.
A6. Every "arm ok" row has history.json with status completed and
    execution error absent.
A7. No claim of visual BETTER/WORSE — only measured deltas + descriptions;
    taste calls are marked for the owner's eye and sheeted.
A8. V9 file identity: sha256 on disk == Civitai API hash for version 3045803.
A9. The reconstructed ZIT reference is labelled as a reconstruction
    (owner's actual simple workflow not found on pod) everywhere it is used.
A10. Mouth-threshold decision backed by detector log lines from the arm
     servers (which threshold fires on which composition), not inference.

## Phase-2/3 addenda (written 2026-08-07 ~22:4x, BEFORE the phase-2/3 verification)

A11. The NaN containment claim: str08's frame is max()==0 black; every arm
     LISTED as re-run in batchBC2 has a fresh history + canary bit-identity
     rows in the log; no post-purge likeness row cites a poisoned render.
A12. luna-on-base incompatibility: zbref_P_12345 re-rendered AFTER a clean
     canary on a fresh server; nolora control clean. Both files exist.
A13. Mouth threshold: "1 lips" lines exist in the arm server log; T10-vs-T12
     diff >8 confined to lips region at thr 0.5; identical result at 0.3.
A14. LUNA-Z numbers (0.733 final etc.) re-derive from likeness_scores.json
     against the PINNED centroid.json (not a per-run centroid).
A15. The converter equivalence: compare_api.py run on A0 source vs
     harness-captured api graph prints EQUIVALENT; the benign-key allowlist
     is exactly {rgthree_comparer, node_identifier, previewMode}.
A16. Texture parity claim (faceHF 10.35/bodyHF 9.66 vs ref 10.6/9.5) traces
     to tap_metrics.json rows for D_lunaz_FB and zref_B/zref_P refs;
     the caveat that framing differs between LUNA-Z and A0 is stated
     wherever parity is claimed.

## Phase-4 criteria (written 2026-08-08 ~01:0x, BEFORE the work they judge:
## batch G verdicts + agents A-F + final rebuild)

A17. RECONCILIATION: both readings rendered (Z-native PC on FB/PT/CU + the
     literal Z30+SDXL hybrid tile); the 30-vs-8-step base cost quoted in
     seconds FROM SAMPLER LOG LINES of these arms, not whole-render deltas;
     negative-liveness proven two ways (mechanism with a source line in
     comfy/samplers.py + the loud-negative arm visibly changing the base
     output) — or stated unproven.
A18. CONSTRAINT-2 SCORING: every rendered arm's record carries a
     "photographic read" line, explicitly labelled MY JUDGEMENT, and every
     case where a metric and that read disagree is called out in the arm's
     row, not silently resolved.
A19. CHARACTER-GENERALITY: the final config document marks EVERY landed
     setting character-general or character-specific (with default + sane
     range for specific ones); no Luna-named text in the shipped workflow's
     prompts, node titles, or file names; CHARACTER-SWAP-CHECKLIST.md
     exists, is referenced from README-PERSONAL, and states that
     generalisation is unproven (only Luna LoRAs on this pod).
A20. HANDS (A+E): research claims carry stored source files; every rendered
     hand arm appears on a like-for-like sheet (mediapipe hand box, equal
     hand scale per tile); the verdict text uses constraint-2 language and
     records which arms were rejected for over-detail regardless of metric.
A21. MOUTH (B): before/after rendered on FB, PT, CU AND an added open-mouth
     close-up; deletion verdict cites pixel-diff evidence per comp; the
     lips_v1.pt licensing consequence stated factually (sellable-relevant,
     personal-neutral).
A22. LIGHTING (C): any lighting metric is labelled a proxy with its formula
     stored; arms change ONE lever each; the final lighting statement
     separates measured deltas from my read and defers the look call to the
     owner's sheet.
A23. BLACK RENDERS (D): every replay/toggle run recorded with server boot
     id, graph, outcome; NO root-cause claim without a reproduced
     discriminating experiment (toggle flips outcome); if the cause stays
     unfound, the deliverable is the measured failure rate per mitigation,
     stated as such.
A24. ARCHITECTURE (F): each structural claim tagged VENDOR/REFERENCE or
     COMMUNITY-HYPOTHESIS with stored sources; no structural change adopted
     on authority — only via an A/B rendered on THIS graph; rejected
     structural arms remain in the record with their evidence.
A25. PROCESS: GPU work serialized through the orchestrator only (no agent
     renders); every render batch canary-bracketed and black-swept; the
     final pack re-cut is gated (round-trip EQUIVALENT + fresh-tree render)
     before any "done" claim; a fresh-context verifier judges A17-A25
     before the final report.
A26. DEPENDENCY PARITY: any dependency the shipped graph gains (pip package,
     model file, node pack) is added to Personal-NSFW/aiofm_setup.sh in the
     same commit that puts it in the graph, and the final fresh-tree gate
     run proves it installs and loads. Analysis-venv tools (insightface,
     mediapipe-in-venv for sheets) are exempt but must never be imported by
     anything the pack ships.
