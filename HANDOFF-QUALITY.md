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
pipeline 7.5-8.9/6.1-6.8 at every stage — never reaches ZIT level anywhere;
USDU617 is the biggest smoother (8.29→7.55 face); the body NEVER gets a
texture pass (Z pass is face-crop only). Face local contrast (lapvar): ZIT
277 vs pipeline ~110 — where the "flat lighting" look lives.

**Hands correction to Q1:** on THIS composition the hand detector FIRES
(1 hand, 1024x704 crop sampled, run5/A/A0 server log) — the pass runs and the
hand still reads wrong; its model is the RAW checkpoint (no character/detail
LoRA), dpmpp_2m_sde 30 steps @ denoise 0.42.

**Z-Image holds the full-body composition** (zref_B_12345: coherent balcony
3/4-body frame, likeness 0.81, freckled skin, warm light) — Q2's "one render
answers it" answered YES (feet out of frame; framing control TBD).
