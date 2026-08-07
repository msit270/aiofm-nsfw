# Final-verifier findings and dispositions (2026-08-07)

Two verifier passes ran (fresh-context subagents, adversarial). Pass 1: all 10
areas PASS; 4 defects, all fixed in-run (runtime device FATAL made fatal
d7ea270; untracked evidence committed; note timestamps corrected; the feather
was in-flight and later landed with its A/B). Pass 2 (final): all 10 areas
PASS; 5 minor defects, dispositions:

1. YOLO confidences were quoted but not on disk → re-derived and persisted:
   `results/run3/yolo_confidences.json` (values match every quoted figure;
   gates 0.8653/0.8654, fresh 0.8652, arms 0.9015–0.9021).
2. HANDOFF said "13 seed controls"; current bytes have 11 (anatomy deletion
   removed 2) → corrected in HANDOFF; substance (zero randomize) unchanged.
3. ACCEPTANCE E2 reads 0 but final state is 3 product-known by honest
   reclassification → E2 amended in place with the reason.
4. Commit 72f95ba said "single input diff"; strictly two (the second being
   419's browser-session comparer state, the documented noise field that
   every diff in this project strips) → recorded here; commit not rewritten.
5. Screenshot-filename nick + the 203-vs-211 log-line totals → HANDOFF fixed;
   reconciliation: 203 decisions predate run 3, 8 more landed during run-3
   arms (all ~0.37M passes), 211 total in the extract.
