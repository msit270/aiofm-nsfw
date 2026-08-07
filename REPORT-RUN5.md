# Run 5 — final report (personal-max)

Written for the owner, phone-readable. Every number traces to
`results/run5/` (likeness_scores.json, tap_metrics.json, SCOREBOARD.md,
per-arm api_graph/history). Verified twice by fresh-context verifiers
(`results/run5/verify/phase1_verifier.md`, `phase23_verifier.md`).

## One sentence

Your instinct was right: identity was never in the widgets — the SDXL half
of the pipeline destroys it structurally, so I rebuilt the graph so that
Z-Image Turbo + your luna LoRA drives every sampling pass, which takes
likeness from 0.59 to 0.73-0.77 (reference band 0.92+), brings skin texture
to reference level, and it is packaged as a one-command install that
passed a fresh-tree gate end to end.

## What you need to look at and decide (sheets in results/run5/SHEETS/)

1. **S1 + S2** — the winner. LUNA-Z vs the shipping pipeline, faces and all
   three compositions. If LUNA-Z's look is right, you are done: the pack is
   built and gated; publish per OWNER-ACTIONS-PERSONAL.md.
2. **S3 + lunaz30 tile** — base 30-step/cfg-2 variant: denser freckles,
   measured best likeness of the run (0.774). Taste call: default stays
   8-step/cfg-1; switching = two widget values on the base sampler.
3. **S9 / S8** — if you ever want the SDXL architecture back: den 0.85 gets
   0.696-0.769 on full-body but collapses on portrait/close-up (0.41-0.49)
   and the body/light stay SDXL. My judgement: not worth it; your eye may
   differ.
4. **S5/S10 hands** — Z-hands adds real texture (tendons, knuckles) but one
   arm showed a ragged thumbnail. n=1 each way; the shipped default keeps
   the Z hands pass. If nails misbehave in practice, say so and I'll sweep
   the hands denoise next session.
5. **S4/S6** — face-pass sampler pairing (taste) and the mouth fix
   (objective, already applied at threshold 0.5).

## Proven vs my judgement

PROVEN (measured, re-derived by independent verifiers):
- Likeness chain: base 0.29 → LoRA-less TDD refine 0.16 → SDXL face pass
  0.55 → USDU erosion → Z-face ceiling 0.58-0.70. The refine (`619:600`)
  and hands (`587:92`) passes run with NO character LoRA in the shipped
  graph; the base prompt carries no trigger and the wrong hair.
- The two LoRAs encode the same person unevenly: lunaskye(SDXL) tops out
  ~0.48-0.54 even alone; luna(ZIT) hits 0.92-0.94. Any SDXL sampling pass
  therefore repaints toward a half-Luna. That is the whole likeness story.
- luna does NOT work on Z-Image BASE (confetti; clean no-LoRA control) —
  Turbo only, until you retrain.
- Turbo at 30 steps/cfg 2 is NOT blurry for luna (no acceleration-loss
  symptom; 0.843 same-identity, denser texture).
- Mouth: at threshold 0.7 the lips detector finds nothing on full-body
  renders (pass never ran); at 0.5 it fires and edits exactly the lips.
  Applied. 0.3 adds nothing.
- V9: naive swap degrades likeness (0.499); repaired stacks stay below V7
  equivalents (0.708 vs 0.769). Your V7-tuned numbers do not carry, as you
  said. V9 is installed and the slot is swappable; V7 remains the better
  SDXL base for lunaskye TODAY.
- The pack: workflow member == proven graph (harness round-trip EQUIVALENT);
  that graph rendered bit-identical to the measured winner on two separate
  server boots; fresh-tree one-command install gate PASSED: install exit 0 in 115 s,
  V9 re-fetched from Civitai byte-exact, browser render bit-identical to
  the measured winner (results/run5/fresh/).
- Determinism held throughout (every canary bit-identical), and the
  likeness metric shows no architecture bias (Z-stranger 0.337 vs
  SDXL-stranger 0.335).

MY JUDGEMENT (override freely):
- LUNA-Z as the ship default (metric + my eye agree; your eye rules).
- Keeping euler_ancestral/kl_optimal on the face pass (vendor template says
  res_multistep/simple; Q3 says that direction adds heavy freckle character;
  S4 is the tile).
- Keeping the 1x SkinDiff pass and colormatch chain (measured near-no-op;
  kept for stability).
- Dropping the Image Comparer node from the personal workflow.
- Face denoise 0.35 kept (identity now arrives from the base; the ladder is
  S9 if you want more).

## The four defects, closed out

- LIKENESS: structural, fixed by architecture (0.59 → 0.73-0.77; the
  remaining gap to 0.92 is resampling/composite损, not identity drift).
- PLASTIC SKIN: the SDXL chain never reached reference texture anywhere
  (7.5-8.9 face / 6.1-7.5 body vs ref 10.6/9.5); LUNA-Z lands 10.3-11.5 /
  9.5-9.7. Body skin now gets real freckle texture.
- LIGHTING: no honest single metric (first claim was retracted by my own
  verifier); deeper shadows + warmer directional light visible in S2 —
  your eye decides.
- HANDS: the pass DOES fire (Q1's zero-detection was composition-specific);
  it ran LoRA-less on raw SDXL. Now Z-native; textured but n=1 nail
  artifact on one arm — S5/S10, watch it in use.

## Open items, honest

- **Intermittent black Z-renders on this pod** (~7 in ~90), both
  architectures, incl. the CURRENT shipping graph on the portrait comp
  (2/2 boots). Per-graph deterministic within a boot; re-render on a fresh
  boot clears it; LUNA-Z default was 5/5 clean. Strength-0.8 and
  ZeroOut-negative theories tested and falsified. Suspect (unproven):
  torch 2.9.1+cu128 numeric edge on Blackwell. Root-cause session
  recommended; repro graphs preserved.
- lunaskye is the weak link if you ever return to SDXL: 2250 steps vs
  luna's 5000, half-fidelity ceiling. V9's card claims better LoRA
  training; a lunaskye-on-V9 retrain would be the experiment.
- Retraining luna on Z-Image BASE would unlock real negatives + 28-50-step
  quality and the base model's higher diversity (vendor: Turbo is
  "Diversity: Low"). ai-toolkit supports it.
- V10 (Krea 2) unlocks Aug 10: needs ComfyUI ≥0.26 (this build pins
  0.15.1). Full runbook in notes/V10-krea2-runbook.md; the base slot in
  the personal graph is three link changes.
- The mouth pass now runs on full-body; its output is subtle (lips-region
  only). If you want more, the lever is mouth denoise, one arm.

## The one-liner (after you publish per OWNER-ACTIONS-PERSONAL.md)

    AIOFM_PACK_URL=<your-hosted-pack-url> \
    bash <(wget -qO- <live-gist-raw-url>)

Same bootstrap as the sellable, personal pack URL, nothing sellable
touched: dist/AIOFMTech-NSFW.tar.gz, the gist, and the HF paths are
byte-untouched by this run (the pack builder refuses to write into dist/).
