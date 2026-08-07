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
