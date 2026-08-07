# Phase-2/3 verifier report (fresh context, round 2) — 2026-08-07

Scope: HANDOFF-QUALITY.md "Phase-2 results", commit messages a1c8fe7 + dc1a51d,
judged against ACCEPTANCE.md A11–A16 (A1–A10 where touched). All numbers below
re-derived with my own code (/workspace/run5/venv python, insightface buffalo_l
CPU, cv2/numpy). No renders, no server contact; read-only outside verify/.

VERDICT: **ISSUES (minor)** — every load-bearing number reproduces exactly;
four letter-of-acceptance / wording defects and one open item listed at the end.

---

## A11 — NaN containment: PASS

- Quarantine note exists: `/workspace/run5/quarantine/README.txt`
  ("poisoned arms deleted (fix610, fixprompt partial, zbref_P, str08); re-render scheduled"),
  mtime 21:20:46.
- `batchBC2.log` contains both `[canary] max_abs_diff=0` (line 4) and
  `[canary2] max_abs_diff=0` (line 18). **Independently recomputed**: I compared
  output/A/zref_P_12345 vs output/C/canary_zref_P_12345 and canary2 myself —
  max_abs_diff **0 and 0** (1152x896x3). A4 determinism therefore re-confirmed
  on the fresh server.
- `likeness_scores.json`: **zero** rows matching `str08` (grep count 0).
  `/workspace/run5/output/C/` contains no str08 dir (frame deleted).
- **B_fix610 rows are provably from the re-run, not the poisoned run**:
  - Current evidence `results/run5/B/B_fix610/{meta,history}.json` agree on
    prompt_id `9e412ef9-fdc6-4fe4-a7e8-ae6bb99d7f2b`; history execution_start
    epoch = 21:22:19 UTC, success at +140.0 s — matches batchBC2.log
    (`exec=140.0s`) and the output PNG mtimes (21:22:33–21:24:39).
  - The **poisoned** run's meta survives in git at commit 6208372:
    prompt_id `b29d2841-25ca-4d70-b65c-cfafc9ddde4d`, exec 138.553 — a
    different execution. Different pid + post-purge mtimes = fresh render.
  - Soft corroboration: current B_fix610 T10_zface row has det 0.8998 — a
    blacked-out face (the poisoning symptom) would not detect at 0.90.
- All 16 arms in batchBC2.log have evidence dirs with meta/history/api_graph,
  meta pid == history pid, status success/completed, execution_start 21:21:39 →
  21:45:26 — all after the purge (21:20:46) and the fresh server boot (21:21:34,
  second startup banner in server_19188.log).
- Whole-file sweep: all 235 rows in likeness_scores.json point to files that
  exist under /workspace/run5/output. Reconstructed server-side render order
  (evidence mtimes + log segmentation): s30cfg2 finished 21:12:37, ZB1 finished
  21:15:23, **str08 executed 21:15:25–29** (submitted 21:12:38, queued behind
  ZB1), poisoned arms after it. **No scored file was rendered between str08 and
  the server kill** — ZB1/s30cfg2/A0_repeat all predate str08's execution.
- Git never held a poisoned row: scores at 6208372^ = 76 rows, at 6208372 = 88
  rows (76 + ZB1's 11 + s30cfg2), zero citing str08/zbref/poisoned-fix610. The
  "13 purged rows" existed only in the working file.

**Not provable post-hoc**: (a) str08's frame max()==0 — the PNG was deliberately
deleted; only the notes (notes/R5-nan-poisoning.md) attest it. (b) That
likeness.py read exactly the current PNG bytes (no per-row content hashes);
supported by mtime ordering (scores written 21:53:33, after all re-runs) and the
det-score consistency above. (c) Leftover stub `results/run5/C/zbref_B_12345/`
holds only an api_graph.json (submitted 21:18, killed mid-poisoning) — cited
nowhere, scored nowhere; harmless but un-noted anywhere.

## A12 — luna-on-base incompatibility: PASS on substance, wording defect

Both files exist and I recomputed their stats:

| render | lapvar | colorfulness | mean/std | face |
|---|---|---|---|---|
| zbref_P_12345 (base+luna) | **1492.2** | **73.0** | 137.7/63.3 | **none at any scale/variant** |
| zbref_P_12345_nolora | 506.4 | 32.7 | 101.4/56.3 | det **0.867** (via full@320) |
| zref_P_12345 (turbo+luna, ref) | 171.1 | 36.8 | 128.4/63.8 | det 0.759 |

The +luna frame is high-frequency, hyper-saturated, faceless — consistent with
"confetti garbage"; the no-LoRA control is a coherent photo with a detectable
face (likeness 0.021 → different woman, as expected without the LoRA).
Detector note: the nolora face is found at full-frame det_size **320**, not 640
(large-face SCRFD quirk documented in likeness.py itself); det 0.867 matches
the stored row exactly.

**Wording defect**: ACCEPTANCE A12 says "re-rendered AFTER a clean canary". The
driver (batchBC2.py) deliberately ran **zbref first, canary after** ("zbref
first (poisoning-vs-incompatibility disambiguation), then a canary") and the
log confirms that order. The disambiguation logic is actually sound — zbref was
the *first* render on a fresh process (nothing prior could poison it) and the
trailing canary is bit-identical, proving the process stayed clean — but the
acceptance text misstates the protocol. HANDOFF's "canary-verified-clean
server" is defensible; the A12 sentence is not.

## A13 — mouth threshold: PASS

- "1 lips" lines exist: 8 hits in /workspace/run5/server_19188.log. By log
  segmentation (got-prompt markers + mtimes): line 1114 = **ZB1** (process 1),
  2494 = **B_mouth05**, 2574 = **B_mouth03**, 2654 = **B_den085**, and
  3620/3824/3979/4186 = the four batch-D pipeline arms (mouth 0.5 candidates).
- Recomputed B_mouth05 T10-vs-T12 (frame 2688x3456): max diff **18** (claimed
  "18 levels" — exact), 394 px >8, all inside one bbox x[906,1043] y[587,657]
  = 138x71 px, **0.11 % of frame area**, 0.004 % of pixels.
- The region IS the lips: insightface mouth-corner keypoints on that frame land
  at (910.6, 627.6) and (1026.5, 617.0) — both inside the diff bbox.
- 0.3 adds nothing over 0.5: B_mouth03 T12 is **bit-identical** to B_mouth05
  T12 (max_abs_diff 0).
- 0.7 default confirmed from A0's own api_graph (620:165 bbox_threshold 0.7);
  at 0.7 the stage is inert on the default composition: A0, A0_repeat,
  A_den050, A_den065 all show T10-vs-T12 max diff 1, zero px >8. (A10 also
  satisfied.)
- **Precision note**: "stage never ran on this composition class at 0.7" has
  measured exceptions: B_den085 (thr 0.7, den-0.85 face) fired and edited a
  361-px lips region, and ZB1 (Z-base composition) fired at 0.7 (1646 px,
  bbox x[1253,1491] y[828,928]). True as scoped to the unmodified default
  pipeline; false as a blanket statement.

## A14 — LUNA-Z likeness 0.733: PASS (exact)

Independent recompute (my own detection code, buffalo_l CPU, det 640, full
frame — no code shared with likeness.py's scan): cos(D_lunaz_FB final,
stored centroid) = **0.732718**, det 0.8353, vs claimed 0.7327182614987167 —
delta ≈ 1e-7, far inside the 0.01 tolerance.
Centroid pin verified: recomputing the centroid from the three declared
reference renders reproduces the stored vector at cos = **1.00000000** and the
stored pairwise band 0.7816/0.8283/0.7985 to 4 dp; centroid.json is unchanged
in git since 6208372. The D-batch scores (21:53) were made against this pinned
file.

## A15 — converter equivalence: PASS, with silent-normalization notes

My run: `compare_api.py A/A0/api_graph.json test_ui_captured_api.json` →
**"EQUIVALENT (92 nodes, canonical signatures match)"**, exit 0.
BENIGN_KEYS is exactly `{"rgthree_comparer", "node_identifier", "previewMode"}`.
Normalizations it performs **beyond** that allowlist (documented in its
docstring but silent in the verdict line):
1. Drops every node whose id starts with `TAP_` before comparing.
2. `nnum`: treats 1.0 == 1 (float/int coercion on all widget values).
3. Ignores `_meta` (titles) and any non-`inputs` node keys entirely.
4. Node ids are never compared (canonical relabeling by recursive upstream
   signature; multiset compare) — intended, but means id-level provenance is
   not checked.
5. Theoretical: a widget value that is a 2-list whose first element collides
   with a node id would be misread as a link; `hash()` collisions could mask a
   diff (both negligible; same-process hashing makes PYTHONHASHSEED moot).

## A16 — texture parity: numbers PASS, caveat clause FAIL

tap_metrics.json rows (re-read):
- D_lunaz_FB final: faceHF **10.3453**, bodyHF **9.6551** (claimed 10.35/9.66 ✓)
- zref_B_12345: faceHF **10.6064**, bodyHF **9.4942** (the "ref 10.6/9.5" ✓)
- zref_P_12345: faceHF 11.579 (portrait ref)
- A0 final: faceHF **7.7343**, bodyHF **6.8298** (claimed 7.73/6.83 ✓)

**The framing caveat required by A16 is stated nowhere the parity is claimed.**
Commit a1c8fe7 says "texture at reference level (faceHF 10.35, bodyHF 9.66)"
with no framing caveat; HANDOFF-QUALITY.md has no phase-3/D section at all yet;
README-PERSONAL.txt doesn't carry the claim; the sheet/scoreboard tools embed no
caveat text. The framing difference is real and large: face_px_h 731 (D_lunaz_FB)
vs 242 (zref_B) vs 447 (A0). Mitigation: the metric itself is scale-normalized
(face box rescaled to 512 px before band measurement, per analyze_taps.py), so
the comparison is not raw-scale-confounded — but the acceptance criterion the
session wrote for itself is unmet as of this snapshot. Also note D_lunaz_FB
face lapvar 755.8 vs refs 93.0/277.4 and A0 104.2 — the parity claim holds for
the freckle-band RMS specifically, not for local contrast, and should not be
quoted broader than that.

## Check 7 — LUNA-Z graph is what the prose says: PASS on all seven

results/run5/D/D_lunaz_FB/api_graph.json (107 nodes):
(a) 619:617 UltimateSDUpscale: model ["116",0], positive ["ZU_pos",0]
    (negative ZU_neg = ConditioningZeroOut of ZU_pos), cfg 1.0,
    res_multistep/simple ✓ (was: model ["618",0], cfg 4.5, 25-step
    dpmpp_2m_sde/karras in A0).
(b) 587:98: model ["116",0], positive ZU_pos, cfg 1.0, res_multistep/simple ✓
    (steps 2 / den 0.08 retained from buyer; was lcm/sgm_uniform on 587:97 TDD).
(c) 587:92 FaceDetailer: model ["116",0], cfg 1, steps 8, res_multistep/simple,
    den 0.42, clip 620:110, vae 620:109 ✓ (was raw checkpoint ["619:613",0],
    cfg 3, 30-step dpmpp_2m_sde).
(d) 619:617.image = ["619:595",0]; upstream chain 619:595 ← 619:593
    (ImageUpscaleWithModel) ← ZB_dec ← ZB_k — no SDXL refine (619:600), no
    SDXL face pass (619:607), no extra VAE round-trip on the path ✓.
(e) 620:165.bbox_threshold = 0.5 ✓.
(f) ZB_k KSampler exists: model ["116",0], steps 8, cfg 1.0, res_multistep/
    simple, seed 12345, 896x1152 EmptySD3LatentImage ✓.
(g) Reachability: naive all-sinks walk is contaminated by dead-end nodes (stray
    VAEDecodes 619:591/616, sink LoraLoader 587:97 etc.), so I walked from
    OUTPUT-class nodes only (SaveImage x9 incl. taps, PreviewAny x2, rgthree
    Comparer 419 — the nodes ComfyUI actually executes from): **79/107 nodes
    on the executed path; 619:613 (SDXL ckpt), 618 (lunaskye stack), 619:610
    (TDD LoRA), 619:600, 619:596, 619:607 are all unreachable**, from every
    output root including the Comparer. Corroborated twice at runtime: the
    run's history.json outputs list exactly the 13 output nodes, and the
    D_lunaz_FB log stretch contains only "Requested to load Lumina2" (x5) +
    ZImageTEModel_ — zero SDXL loads. 116 = Lora Loader Stack with
    luna.safetensors @ 1.0 feeding all seven sampling passes ✓.
    (28 dead nodes ride along in the submitted graph — inert, but present.)

Observation (not on the checklist): ZB_pos still carries the buyer's original
balcony prompt — "long dark hair", no "luna" trigger token — i.e. HANDOFF
structural finding #3 (prompt describes a different character) is reproduced
inside the LUNA-Z candidate's own base prompt. The LoRA drives identity anyway
(0.733 vs no-LoRA floor 0.34), but the fixprompt lesson (B_fixprompt +0.012,
B_fixboth +0.062 on SDXL) was not folded into the candidate.

## Check 8 — metric bias sanity: no measurable arch bias; honest caveats

Experiment (my own embedding code, same pinned centroid):
- Z-Turbo arch, no LoRA (zref_P_12345_nolora): **0.3373**
- SDXL arch, no LoRA (sxref_P_12345_nolora): **0.3350**
- Z-BASE arch, no LoRA (zbref_P_12345_nolora): **0.0210**

If architecture-shared low-level statistics inflated similarity to the
Z-derived centroid, the Z no-LoRA controls would sit clearly above the SDXL
no-LoRA control. Measured: +0.0023 (Turbo) and −0.31 (Base) — no inflation;
the claimed effect sizes (0.585 vs 0.733 etc.) are ~65x the residual. Also,
every pipeline arm's final frame passes through the same Z face pass last, so
cross-arch comparisons at the final tap share their last-stage texture regime.
Caveats stated plainly: n=1 per control (single seed/composition/prompt);
ArcFace is not provably texture-blind in general; and the centroid *defines*
likeness as "luna as the ZIT renders her", so a Z+luna-rendered face is being
compared to its own generator's notion of the character — that is the metric's
declared meaning, not a bug, but "likeness 0.733" should always be read
against the ZIT self-band (0.92–0.94) and stranger floor (~0.33-0.34), both of
which exist as measured rows (A2 satisfied).

## Commit-message spot checks (a1c8fe7 / dc1a51d)

- a1c8fe7: 0.733 ✓ (exact), faceHF 10.35 / bodyHF 9.66 ✓, S1/S5/S6 sheets exist,
  README-PERSONAL.txt exists. Missing framing caveat → the A16 issue above.
- dc1a51d: fresh_install5.sh exists (tools/), scoreboard.py exists.
  "zusdu617 = biggest single-node likeness gain (0.674)": C_zusdu617 final =
  0.6744 ✓, biggest **within the batch-C Z-substitution family** — but
  B_den085 (also a one-node override, 620:114 denoise) scores 0.6960. The
  unqualified superlative is wrong; qualified to "Z-substitution arms" it holds.
  "nocm111 near-no-op": supported — my pixel diff vs A0 final: max 30, mean
  0.021, 244 of 9.29M px >8 (0.003 %); final faceHF 7.736 vs A0 7.734.
  Caveat: C_nocm111 has **no rows at all** in likeness_scores.json and
  C_zhands stops at T04 — the scoring scan of those dirs is incomplete, so the
  no-op claim rests on tap_metrics + pixels, not likeness (fine, but A1-style
  traceability is thinner there).
  "zhands textured but nail artifact (n=1)": eye-call tile, flagged n=1 —
  A7-compliant as sheeted; note my crop-level check shows hand_zhands HF 11.70
  vs hand_A0 11.85 (≈equal), so "textured" is not (yet) a measured delta.
- HANDOFF phase-2 numbers all reproduce from likeness_scores.json: fix610
  0.5710, fixprompt 0.5967, fixboth 0.6466, A0 0.5845, den085 0.6960,
  rms_simple 0.6119 (faceHF 7.969 vs 7.734 ✓), B_v9 0.4986, C_tdd_cfg 0.5868
  (faceHF 7.631, f-lap 82.0 vs A0 104.2 ✓), s30cfg2 0.8432 (faceHF 11.87 vs
  ref 11.58 — "denser freckles" is objectively grounded).

## Open item

Batch D was still in flight at verification time (batchD.log grew during this
session; canary3 — the closing bracket of the D batch — had not yet run). The
0.733/texture claims are therefore front-bracketed only (canary2 = 0 diff,
39 s before D started). Two compensating checks I ran: D_lunaz_FB's T00 base
render is **bit-identical** (max_abs_diff 0) to ZB1's pre-incident clean T00 —
the Z UNET was producing byte-reproducible clean output inside the D batch —
and the final frame carries a healthy detectable face (det 0.835), which the
known poisoning failure modes (black face / confetti) would destroy. Canary3
must still be confirmed when the batch closes.

## Issues list (for the summary verdict)

1. **A16 (partial FAIL)**: framing caveat absent everywhere parity is claimed
   (a1c8fe7 message; no HANDOFF phase-3 text exists). Numbers themselves exact.
2. **A12 wording**: acceptance text says canary-then-zbref; the protocol
   (deliberately, and defensibly) did zbref-then-canary on a fresh server.
3. **canary3 pending**: D-batch claims lack their closing canary at snapshot
   (mitigated by T00 bit-identity, shown here).
4. **dc1a51d superlative**: "biggest single-node likeness gain" is false
   unqualified (B_den085 0.696 > 0.674); true within batch C.
5. Minor: likeness scan incomplete for C_nocm111/C_zhands; blanket "never ran
   at 0.7" has measured exceptions (B_den085, ZB1); zbref_B_12345 stub dir
   undocumented; 28 dead nodes still submitted in the LUNA-Z graph.
