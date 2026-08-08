# Run 5 — final report (personal-max), phase 4 complete

Phone-readable. Every number traces to `results/run5/` (likeness_scores.json,
tap_metrics.json, light_metrics.json, mouth_deletion.json, Dmatrix/,
per-arm api_graph/history). Four fresh-context verifier passes:
`results/run5/verify/`. The phase-3 report (pre-verdict) is preserved as
REPORT-RUN5-phase3.md.

## One sentence

Your S11 pick (PC1: Z-Image base at 30 steps/cfg 2 with live negatives, a
soft euler_ancestral face pass at denoise 0.50) is now the shipped,
character-neutral workflow — with hands fixed by prompt neutralization plus
lower-res sampling, the mouth stage deleted on evidence, lighting moved to
where it actually lives (the base prompt and the shift dial), every
inherited setting re-derived or evidenced on the new architecture, and the
whole thing cut into a one-command pack whose proof renders caught and
fixed a real ship bug before it reached you.

## What you need to look at (results/run5/SHEETS/)

1. **S17** — the shipped graph's own renders, three comps + neutral. This
   is what the pack produces. FB 0.789 / PT 0.731 / CU 0.644.
2. **S14** — hands: the adopted combo tile (neutral prompt + 768 sampling)
   vs everything else, like-for-like crops at last. My read: the first
   genuinely photographic hand of the project. Your eye rules.
3. **S18/S18b** — the ONE thing that beat your pick after you made it:
   euler_ancestral in the tiled-refine slots (cos .809 vs .799, body
   texture band higher). One widget-pair away; NOT applied — your call.
4. **S15** — lighting: the film-stock sentence tile (best frame of the
   run, cos .820) and the shift 4.5/6 tiles. Prompt-level, in README.
5. **S12** — the close-up caveat on the 30/cfg2 base (goes blotchy on
   face-filling comps; drop to 8/cfg1 or cfg 1.5 there). Documented in
   README + checklist; batch I's cfg-1.5 arm was clean but not
   close-up-tested — one arm if you want it settled.

## The four defects — final state

- **LIKENESS**: structural, solved by architecture. Ship 0.585 → PC 0.789
  (FB), reference band 0.92+. The two LoRAs encode the same person
  unevenly (lunaskye caps ~0.5); every SDXL pass repainted toward the
  half-copy. SDXL is out of the render path entirely.
- **PLASTIC SKIN**: solved. Ship body texture 6.8 (band) → PC 9.6 at
  reference level (~9.5); face at reference class. The S3-pick base
  (30/cfg2) carries the freckle density you chose.
- **HANDS**: the shipped "Detailed hand, detailed fingers, detailed
  fingernails" prompt was a measured CAUSE of the overbake; neutral
  prompt + 768 sampling adopted. The reference-practice "hands after
  upscale" idea hallucinated jewelry on this graph — refuted by render.
- **LIGHTING**: measured for the first time. The chain flattens whatever
  the base gives (and no downstream knob recovers it — lanczos swap and
  colormatch re-referencing both measured no-effect). Light is GENERATED:
  the film/direction sentences and the shift dial (now exposed) are the
  levers; identity holds (cos up to .820).

## Proven vs my judgement

PROVEN (measured, verifier-re-derived):
- The additive-freckle rule you hypothesized: res_multistep adds a
  ~constant texture increment (+0.43/+0.55 at the two base levels) — so
  it helped the texture-poor SHIP architecture and overshoots on PC.
  On PC it wins nowhere measurable, including its own tiled slots.
- Sampler preference is architecture-specific (your S4 verdict did not
  carry, exactly as you suspected).
- Mouth stage: fired only where useless (closed mouths), blocked by its
  own 4M area ceiling on open-mouth close-ups (91 px difference there).
  Deleted; lips_v1.pt left the graph with it.
- Settled-number audit on the new base: 617@0.25 confirmed (0.15 LOSES
  likeness — the Z refine pulls toward the character), 98@0.08 near-dead,
  eyes@0.42 flat, face steps 8 confirmed, face denoise 0.50 (your pick)
  over the old settled 0.35.
- Negatives are live on the base at cfg 2 (mechanism + 76.2% pixel steer
  from a negative-only edit); they lose direct positive conflicts.
- The proof chain: your pick → api graph → UI file (round-trip EQUIVALENT,
  66 nodes) → browser full-render gate PASS → three distinct comp proofs.
  The proofs CAUGHT A SHIP BUG (the base ignored the typed 483 prompt —
  all comps rendered identical) — fixed, re-proven distinct.
- Fresh-tree one-command install: [GATE RESULT PENDING]
- Structural interrogation (F): run order, colormatch, blend, VAE trip,
  double-face — every A/B lost or tied vs PC1; the structure is unchanged
  but now evidenced. The VAE round trip and double face pass left with
  the SDXL chain.

MY JUDGEMENT (override freely):
- The hands combo tile reads photographic (S14) — n=1 per arm.
- PC1's PT frame reads photographed; CU at 30/cfg2 reads processed (S12).
- The film-sentence frame is the best-looking image of the run (S15).
- Keeping rms in the tiled slots despite S18's metric (your S3 body
  verdict was formed with rms there; the swap is sheeted, not applied).

## Character-generality (constraint 1)

The shipped workflow is neutral: LoRA widget "None", placeholder prompts,
nothing Luna-named anywhere in it (the vendored luna/lunaskye FILES ride
in the pack as your content). CONFIG-SPEC.txt marks every setting
GENERAL/SPECIFIC with defaults + ranges; CHARACTER-SWAP-CHECKLIST.txt is
in the pack root and README points to it. Generalisation beyond Luna is
UNPROVEN (single-LoRA pod) — the checklist is the mitigation, and
cos-to-Luna numbers are instrument readings, not the goal.

## Black renders (agent D)

Same story as the pod-independent GitHub issue this project already filed
(#15110): intermittent Z-side NaN, per-graph deterministic within a boot,
varies across boots, ~8% of renders, both architectures, LUNA-Z/PC default
config 5/5 clean across boots but NOT immune as a class. Research located
three concrete mechanisms (bf16 path has NO NaN clamp upstream; xformers
cutlass kernels on sm_120 carried every failure; ComfyUI's default
2-stream async offload meets cuBLAS's documented multi-stream
nondeterminism, fixed in torch 2.10). Experiment matrix:
[D-MATRIX RESULT PENDING — arms: baseline / no-xformers /
no-async-offload / CUBLAS workspace / fp32]
Interim mitigation (measured all session): re-render on a fresh boot
always cleared it; the fresh-install gate black-checks its render.

## The pack

`dist-personal/AIOFMTech-NSFW-Personal.tar.gz`
sha256 80977842… (PACK.txt), 163 files. Workflow member 50b2b3ff….
Publish + one-liner: OWNER-ACTIONS-PERSONAL.md — the live sellable gist,
unchanged, with AIOFM_PACK_URL pointed at your hosting. Nothing sellable
was touched at any point (builder refuses to write into dist/).

## Open items, honest

- Close-up regime for the 30/cfg2 base (S12): documented; cfg-1.5-on-CU
  is the one untested arm that could dissolve it.
- S18 tiled-sampler swap: metric says yes, your S3 eye said rms — decide
  from the sheet.
- Black-render root cause: [PENDING — see D-matrix section].
- V10/Krea2 (unlocks Aug 10): runbook ready (notes/V10-krea2-runbook.md);
  needs a core upgrade session.
- Retraining luna on Z-Image BASE would unlock real negatives + the base
  model's diversity; lunaskye is the weak link if SDXL ever returns.
- Exclusive-region SEGS for the face/eyes overlap: deferred, low priority.
