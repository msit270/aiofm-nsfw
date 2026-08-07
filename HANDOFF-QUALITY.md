# HANDOFF-QUALITY — run 5, personal-max branch (2026-08-07, night)

Personal build. Goal: best-looking output; four defects traced (plastic skin,
hands, likeness, lighting); base swappable; one-command install SEPARATE from
the sellable pack. Never touch dist/AIOFMTech-NSFW.tar.gz, the gist, or the
published HF paths.

## Status: IN FLIGHT

Done so far (all evidence under `results/run5/`):
- **LUSTIFY V9 ZENITH fetched and verified.** Civitai model 573152, version
  **3045803** (resolved from the API this session — the old brief's 1094291 is
  ENDGAME, wrong). SHA256 `1a3abf0b…c162f1` matches the API's published hash
  exactly (`results/run5/civitai_model_573152.json`, `/workspace/run5/v9_sha256.txt`).
  Placed at `models/checkpoints/lustifyNSFWCheckpoint_zenithV9.safetensors`.
- **V10 (Krea 2) exists in the API already**: version 3112728, published
  2026-07-25, multiple files (fp8 12.5G, bf16 12.8G, full 25.7G, GGUF Q2/Q4).
  Download probe with our key: HTTP 401 → still early-access-locked (opens
  ~Aug 10 per owner). Krea 2 = NOT SDXL; swap will need arch support research.
- **The owner's simple ZIT workflow is NOT on this pod** (searched /workspace,
  /root, ComfyUI user dirs). Reconstructed from the vendor blueprint
  (`/workspace/ComfyUI/blueprints/Text to Image (Z-Image-Turbo).json`):
  UNET zimage + LoraLoaderModelOnly luna 1.0 + KSampler res_multistep/simple
  cfg 1 + EmptySD3LatentImage. This substitution is flagged; if the owner's
  real workflow differs (strength, steps, shift), re-anchor the reference.
- **Likeness metric**: ArcFace (insightface buffalo_l) in an isolated venv at
  /workspace/run5/venv — ComfyUI's env untouched. Reference identity = centroid
  of ZIT portrait renders. Scores → `results/run5/likeness_scores.json`.
- **Batch A rendering now** (persistent server :19188; 18188 untouched):
  ZIT references (balcony/portrait, multi-seed, sampler probe, no-LoRA
  control), SDXL+lunaskye portrait probes, tapped pipeline baseline (10 taps
  T01–T12 along the chain), skip-#607, skip-#114, den 0.50/0.65, repeat.

## Structural facts found before any render (from api_final.json)

1. **Base-refine KSamplerAdvanced `619:600` bypasses the character LoRA.**
   Its model path is `619:610 LoraLoader(TDD) ← 619:613 checkpoint` — the
   buyer's `618` stack (lunaskye) is NOT in that chain. The 4-step TDD refine
   at the 1432×1840 re-encode repaints the whole frame with no character LoRA.
2. **Hands detailer `587:92` model = raw checkpoint** (no LoRA at all).
3. **The buyer base prompt carries no LoRA trigger token** ("luna"/"lunaskye"
   appear nowhere in it) and describes "long dark hair" while the face prompt
   says "wavy auburn hair" — the base generator is being told a different
   character than the face pass.
4. luna LoRA: zimage base, ai-toolkit, 5000 steps. lunaskye: SDXL, 2250 steps.
   (ai-toolkit metadata carries no trigger words; inferred from prompt text.)
5. Z-Image passes get shift 3.0 by default (ComfyUI ZImage class) — the
   vendor template's ModelSamplingAuraFlow(3) is redundant; NOT a deviation.
   The sampler pairing (euler_ancestral/kl_optimal vs vendor res_multistep/
   simple) IS the remaining deviation (Q3 measured direction, pairing untested).

## Layout
- Driver/metric tools: `/workspace/run5/tools/` (r5.py, batchA.py, likeness.py),
  copies committed under `results/run5/tools/`.
- Renders: `/workspace/run5/output/<batch>/<arm>/` (not committed — PNGs stay
  on the pod; sheets + metrics go to the repo).
- Per-arm evidence: `results/run5/<batch>/<arm>/{api_graph,history,meta}.json`.

## Next
- Score batch A → answer "where is likeness lost" with numbers.
- Z-base splice arms (ZB1: Z-Image base + unchanged SDXL detail chain; ZB2:
  + skip #607). Vendor-pairing arm res_multistep+simple on #114.
- V9 base swap arm + re-derivation (V7-calibrated values do not carry).
- Mouth threshold 0.5 arm on full-body. Three compositions. Sheets. Package.

## Phase-1 results (batch A, all numbers in results/run5/likeness_scores.json + tap_metrics.json)

Determinism: A0_repeat bit-identical to A0 (max_abs_diff 0, 9.29M px) on the
persistent warm server — same-server comparisons valid (ACCEPTANCE A4 PASS).

**Likeness (cos to luna-ZIT centroid; same-identity band 0.92-0.94, stranger
floor ~0.33):** base out 0.287 → after LoRA-less TDD refine 0.163 (the pass
DESTROYS identity) → after SDXL face pass 0.546 → after USDU617 0.487 (erodes)
→ after USDU98 0.523 → after Z face pass 0.581 → final 0.585.
Arms: skip607 final 0.457 (607 EARNS its keep — run-3's keep-decision holds,
now on likeness grounds); skip114 final 0.523; den0.50 0.638; den0.65 0.664.
The user's simple-ZIT reference sits at 0.92-0.94 (portraits), 0.76-0.81
(full-body small-face). The SDXL-base architecture caps likeness ~0.66 even
at denoise 0.65.

**Texture (freckle-band RMS face/body, scale-normalized):** ZIT ref 10.6/9.5;
pipeline face 7.5-8.9, body 6.1-7.5 across stages — never reaches ZIT level
anywhere; USDU617 is the biggest smoother (8.28→7.55 face); the body NEVER
gets a texture pass (Z pass is face-crop only).
VERIFIER CORRECTION (phase1_verifier.md): the earlier lapvar-based "face
local contrast 277 vs 110" lighting claim was overstated — the 277 anchor is
the PORTRAIT ref; the composition-matched full-body ZIT ref measures 93.0,
below the pipeline final's 104. Lighting flatness therefore has NO clean
objective metric yet; it goes to the owner's eye via sheets.

**Hands correction to Q1:** on THIS composition the hand detector FIRES
(1 hand, 1024x704 crop sampled, run5/A/A0 server log) — the pass runs; to MY eye the railing hand still reads wrong (owner judges from the sheet); its model is the RAW checkpoint (no character/detail
LoRA), dpmpp_2m_sde 30 steps @ denoise 0.42.

**Z-Image holds the full-body composition** (zref_B_12345: coherent balcony
3/4-body frame, likeness 0.81, freckled skin, warm light) — Q2's "one render
answers it" answered YES (feet out of frame; framing control TBD).

## Phase-2 results (batches B/C — structure arms; likeness_scores.json)

- **NaN incident**: str08 (LoRA strength 0.8) black-framed and poisoned all
  subsequent Z-UNET renders on that server; killed, quarantined, re-run clean
  with canary brackets (notes/R5-nan-poisoning.md). Canary bit-identical.
- **luna does NOT transfer to Z-Image BASE** (z_image_bf16 + luna = confetti
  garbage on a canary-verified-clean server; base WITHOUT LoRA renders a
  clean prompt-faithful portrait). The Z-native path stays on Turbo.
  If the owner ever retrains luna on base, negatives + 28-50-step quality
  open up (vendor: base = cfg 3-5, steps 28-50).
- **Turbo at 30 steps / cfg 2** (DiffSynth "non-acceleration config"): NOT
  blurry — denser freckles, crisper strands, same identity (0.843 to
  centroid). No acceleration-loss symptom for luna at 8 steps either.
  A base-config taste tile (D_lunaz30).
- **Mouth threshold**: 0.7→0.5 makes the lips detector fire on the full-body
  default ("1 lips", T10→T12 now differs 18 levels on the lips); 0.3 adds
  nothing over 0.5. ADOPTED 0.5 in both candidates — objectively correct
  (stage never ran on this composition class at 0.7).
- SDXL repairs, final-frame cos: fix610 0.571, fixprompt 0.597, fixboth
  0.647 (vs A0 0.585). den085 0.696 (best SDXL number; risk: 0.85 face
  rebuild — owner's eye). rms_simple 0.612, texture slightly crisper
  (faceHF 7.97 vs 7.73).
- **B_v9 (naive checkpoint swap, V7 tuning): 0.499 — WORSE.** Confirms
  "re-derive, do not carry over". V9 needs its own mini-derive (batch E)
  before it can claim the base slot.
- C_tdd_cfg (TDD at author-recommended cfg 1.8/sgm_uniform): likeness ~flat
  (0.587), texture bands softer (faceHF 7.63, f-lap 82 vs 104). NOT adopted
  by default; sheet tile only.


## Verifier-2 corrections adopted (results/run5/verify/phase23_verifier.md)

- Texture-parity claims carry this caveat from now on: the LUNA-Z frame
  composes the face LARGER than A0's (face height ~731 px vs ~242 px on the
  FB comps); the HF metric is scale-normalized (face height -> 512 px before
  banding), which mitigates but does not perfectly remove framing effects.
  The body-texture visual check is the S3 sheet.
- "zusdu617 = biggest single-node gain" is qualified: biggest single WIRING
  change. The den085 WIDGET change scored higher (0.696).
- zbref ran before (not after) the canary — deliberate ordering (fresh-server
  first render), acceptance A12's wording was imprecise, the verifier
  confirmed the logic sound.
- canary3 (D close) completed after verification: max_abs_diff=0.
- The LUNA-Z arms deliberately kept the buyer's original balcony prompt
  ("long dark hair", no trigger) for comparability with A0; measured: the
  LoRA overrides hair anyway (zref_B with the same prompt scored 0.81).
  README-PERSONAL tells the owner how to prompt hair consistently.
- Metric arch-bias control: Z-rendered stranger 0.3373 vs SDXL-rendered
  stranger 0.3350 — architecture alone contributes ~0.002; likeness deltas
  are identity, not texture-statistics.

## FINAL STATE (end of run 5, 2026-08-08 ~00:0x)

**Recommendation: LUNA-Z** — Z-Image Turbo + luna drives base AND every
sampling pass; SDXL fully out of the render path (79-node executed graph).
Numbers (cos to luna centroid; ZIT-to-ZIT band 0.92-0.94):
- LUNA-Z: FB 0.733 / PT 0.740 / CU 0.746 / base-30-variant 0.774.
  Texture at reference level (faceHF 10.3-11.5, bodyHF 9.6+; A0 ship: 7.7/6.8;
  framing caveat in verify/phase23_verifier.md).
- Ship-arch A0: 0.585 FB; PT arm black-faced 2/2 boots on this pod.
- Repaired SDXL (fixboth-class): 0.61-0.77 on FB depending on den085,
  but composition-fragile: sdxlfix PT 0.485 / CU 0.413.
- V9 < V7 for likeness even fully repaired (0.708 vs 0.769 at den085) —
  lunaskye expresses better on V7. V9 installed for future re-derive.

**Shipped artifact** (results/run5/PACK.txt): AIOFMTech-NSFW-Personal.tar.gz
sha256 8573e474…, workflow OFMTech_NSFW_Personal.json (flat, 71 nodes,
member sha f89bb021…). Proof chain: measured winner D_lunaz_FB ← bit-identical
(max_abs_diff 0, two servers) ← final_luna_z_api.json ← harness round-trip
EQUIVALENT ← the UI file in the pack. Buyer-journey values (mouth thr 0.5,
prompt wiring via 483, selector live) included.

**Known open defect — intermittent Z-render black frames on THIS pod:**
~7 events across ~90 Z renders, both architectures (incl. the SHIPPED A0 on
the PT comp, 2/2 boots), per-graph deterministic within a boot, varies across
boots; LUNA-Z default config 5/5 clean across boots. ZeroOut-negative and
LoRA-strength theories tested and falsified. Mitigation shipped: fresh-boot
+ re-render; fresh_install5 gate black-checks its render. Root-cause session
proposed (torch 2.9.1+cu128 / Blackwell numeric edge suspected, unproven);
failing graphs preserved under results/run5/*/api_graph.json.

**Fresh-tree one-command install:** tools/fresh_install5.sh — live sellable
gist + AIOFM_PACK_URL override to the personal pack; withholds V9+LoRAs,
verifies they arrive (V9 sha-checked from civitai), installs the personal
workflow, boots, browser-harness renders end-to-end with the selector
driven, black-checks the output. Result recorded below when it lands.


## FRESH-TREE GATE: PASS (2026-08-08 ~00:2x)

Install phase: exit 0 in 115 s via the LIVE sellable gist + AIOFM_PACK_URL
override to the local mirror of pack 8573e474. Withheld V9 + both LoRAs
arrived (V9 re-fetched from civitai.com, sha256 byte-exact); personal
workflow installed. First gate invocation failed on the first-boot Templates
modal appearing after the dismissal window (cold tree) — harness dismissal
loop hardened (waits until the overlay mask is gone, <=25 s) — second
invocation: real-browser open -> Run -> selector driven -> render complete,
zero frontend errors, and the delivered frame is BIT-IDENTICAL
(max_abs_diff 0) to the measured D_lunaz_FB winner, face det 0.835.
Evidence: results/run5/fresh/{install.log,gate2/,render/}.

The sellable product is untouched: dist/AIOFMTech-NSFW.tar.gz, the gist,
and the published HF paths were never written to (pack builder carries a
dist/ write-guard; every artifact of this run lives under dist-personal/,
Personal-NSFW/, results/run5/).

## MID-RUN OWNER DIRECTION (2026-08-08, run 5 continues)

CONSTRAINT 1 — CHARACTER-GENERAL BUILD. Luna is the tuning subject, not the
target. cos-to-Luna is an instrument only. Every landed setting gets marked
character-general vs character-specific (documented default + sane range).
LoRA path stays a widget; nothing Luna-named ships in prompts/nodes/files;
"LUNA-Z" name retired (architecture = Z-NATIVE, config = PC). A
CHARACTER-SWAP-CHECKLIST.md will list what to re-check on first non-Luna
LoRA. Generalisation is UNPROVEN (only Luna LoRAs exist here) and will be
stated as such.

CONSTRAINT 2 — PHOTOGRAPHIC BEATS DETAILED. More texture was PICKED (S3
body, S4 res_multistep freckling); what loses is anything that reads
PROCESSED (LUNA-Z S1 face = too hard; S10 Z-hands = overbaked/veiny; SDXL
baseline = plastic). Arms are scored by that rule; metric disagreements get
called out explicitly.

VERDICTS: S1 face → zusdu617 (soft SDXL-born face, gently Z-textured);
S3 body → LUNA-Z-30 (Z base 30/cfg2); S4 res_multistep+simple won on ship
arch — RETEST on the shipping graph; S6 mouth: no visible difference fired
vs not → agent B tests full deletion; S5/S10 hands: both rejected, S10
layout broken → agents A + E.

IN FLIGHT: batch G = PC reconciliation (Z-30/cfg2 base + live negatives +
soft face pass) x3 comps + den/sampler/hybrid tiles + negative-liveness
proof. Agents: A hands research, C lighting research, D black-render
research, F architecture research. GPU serialized through the orchestrator.
