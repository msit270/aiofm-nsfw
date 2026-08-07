# QUALITY-MENU — run 4, track 2 (2026-08-07, overnight)

Ranked menu of quality changes for your approval. **Nothing here has been
applied** — the shipping workflow hashes `47419606…` before and after track 2,
and every render ran on isolated per-arm servers. Every entry below has a
labelled contact sheet with the baseline tile marked; costs are measured, not
estimated. Where an entry names a model file, its licence flags were read from
an API this session and the response path is given. Sources:
`notes/Q1-currency.md` (pins/models), `notes/Q2-cropfactor.md`,
`notes/Q3-zimage.md`, `notes/Q4-settings.md` — each with per-arm evidence
under `results/run4/quality/`.

Method floor for everything: one variable per arm, fresh server per arm,
`execution_cached []` verified, fixed seeds, cfg 1 untouched, measurements on
the downstream-wired slots. n=1 per cell unless stated. One measured fact
raises confidence across the board: **Q2's repeat of the shipped config is
bit-identical to its baseline (max abs diff 0 over the full frame)** — this
graph renders deterministically under the protocol, so pixel deltas are real
effects, not noise. (Timing still wobbles tens of seconds run-to-run; only
within-window sampler-level timings are quoted as costs.)

---

## The menu, ranked

### 1. Fix `#98`'s tiles at 1024 — the one candidate for an actual default change
- **Change:** `587:98 UltimateSDUpscale` tile_width/height 1024 fixed,
  replacing the `#99 GetImageSize` wiring that makes the tile equal the whole
  frame (Q8 answered: the 512×512 widgets never execute).
- **Why:** caps `#98`'s VRAM at a resolution-independent size — its stage
  window dropped 18.8 → 12.9 GiB — which is the part of Q8's concern that
  scales with whatever resolution a buyer renders. Seams probed objectively
  at every tile boundary: none (boundary ratios 0.70–0.83, i.e. marginally
  smoother than flanks; off-boundary controls clean).
- **Cost:** none measurable in time; run PEAK unchanged on this box (the
  peak lives in the eyes/final stage at ~22.3 GiB, not in `#98`).
- **Caveats:** the face texture re-rolls (33 % of face pixels >8 levels) —
  equivalent-looking, not degraded, but that is exactly the call you make
  from the sheet, and one higher-resolution repeat is needed to confirm the
  hump-capping where Q8 worried. n=1.
- **Sheets/evidence:** `results/run4/quality/Q4_sheets/Q4_{face,skin}_sheet1of1.png`
  (tile arm labelled), `results/run4/quality/Q4/usdu98_tile1024/seam_probe.json`,
  `notes/Q4-settings.md` §4.

### 2. Face-pass sampler — the only lever that changes the LOOK, and it is free
- **Change:** `620:114` sampler euler_ancestral → `euler` (moderate) or
  `res_multistep` (strong), scheduler kl_optimal held.
- **Measured:** euler = +39 % pigment speckle / +58 % bright micro-blob —
  denser fine freckling. res_multistep = +149 % / +175 %, 10 % of face
  pixels >8 — a character-level change: dense clumped freckle masses, cheek
  mottle, warmer darker complexion. Risk: may read as blotchy — your eye
  decides.
- **Cost:** free (no time, no VRAM). n=1 each.
- **Note:** the vendor's own Z-Image template pairs `res_multistep + simple`;
  that exact pairing is untested (one more arm if you like the direction).
- **Sheet:** `results/run4/quality/Q3/sheets/Q3_L3_face_sampler_face_sheet1of1.png`,
  `notes/Q3-zimage.md` lever 3.

### 3. Expose `#87` skin-filter blend as a "skin grain strength" knob
- **Change:** `587:87 ImageBlend` blend_factor 1.0 (ships) / 0.5 / 0.0.
- **Measured at 0.5:** micro-speckle roughly halved (fine-band RMS −4.6 %,
  dark pores −10.5 %, bright blobs −9.4 % frame-wide; face blobs −31 %);
  freckle/mole layout identical; no artifacts.
- **Cost:** zero time, zero VRAM, one widget. n=1.
- **Sheets:** `results/run4/quality/Q4_sheets/Q4_{face,skin}_sheet1of1.png`,
  `notes/Q4-settings.md` §1.

### 4. "First-upscale strength": `#617` denoise 0.15 / 0.25 (ships) / 0.35
- **Measured:** asymmetric — 0.35 moves the face nearly twice as far as 0.15
  (29.3 % vs 16.1 % >8). 0.15 reads slightly softer/flatter, 0.35 slightly
  more contrasty with more visible spot events. If the old "face
  crunchiness" concern resurfaces, 0.15 attenuates what `#617` amplifies.
- **Cost:** free either way. n=1 per cell.
- **Sheets:** Q4 sheets as above, `notes/Q4-settings.md` §3.

### 5. "SDXL face pass strength": `#607` denoise 0.45 (ships) / 0.30
- **Measured:** the largest face-only movement of the non-steps arms
  (28.1 dB, 31.3 % of face >8); 0.30 reads slightly softer/more even with
  marginally fewer freckle-scale events; sampled resolution unchanged
  (trap-11 line identical). 0.60 direction unmeasured.
- **Cost:** free. n=1.
- **Sheets:** Q4 sheets, `notes/Q4-settings.md` §6.

### 6. "Softer face" option: `bbox_crop_factor` 1.0 (ships 1.5) — and do NOT raise cf for quality
- **Measured (full ladder 1.0–3.5, zero noise floor):** quality moves
  sideways, not up — all arms sit ~35.6–36.4 dB from baseline in the face
  crop regardless of cf; by eye cf 1.0 is the most different (softer skin,
  softer lashes/iris); cf 2.0–3.5 are baseline's family with micro-detail
  reshuffled. Cost is superlinear: face-pass sampler 1/3/6/11/19/29 s across
  the ladder (~area^1.5); cf 3.5 nudged even this 96 GB card into a partial
  unload — on buyer cards cf ≥ 3 is a lowvram/OOM risk.
- **Recommendation:** keep 1.5 shipped; offer 1.0 as a "softer face" look
  option (≈2 s cheaper); treat "raise cf" as refuted for quality.
- **Sheets:** `results/run4/quality/Q2/q2cf_face_sheet1of1.png`,
  `q2cf_skin_sheet1of1.png`, `q2cf_eyeband_A_B_F.png`; grid in
  `notes/Q2-cropfactor.md`.

### 7. Face steps 12 — only if you read the speckle as character
- **Measured:** steps 8→12→16 is free (+0.8/+1.6 s) but monotonically adds
  pigment/bright speckle (+14/+19 % at 12, +31/+31 % at 16) — the metric
  direction of the steps-30 crust you already paid to remove. Keep 8 unless
  the L1 sheet's densification looks like character to you; then 12, not 16.
- **Sheet:** `results/run4/quality/Q3/sheets/Q3_L1_face_steps_*.png`,
  `notes/Q3-zimage.md` lever 1.

### 8. Mouth quality on full-body renders — a detector problem, not a dial problem (next arm, not approvable today)
- **Finding (measured):** on the full-body buyer default the lips detector
  finds nothing at threshold 0.7, so the mouth pass NEVER RUNS — mouth
  quality on that whole class of render is whatever the face pass leaves.
  On portraits it runs and its steps dial is dead (≤14 levels on 0.57 % of
  frame). The hands pass has the mirrored behavior (idle on portraits, and
  Q1 found zero hand detections in all 14 delivered run-3 frames).
- **The lever worth one arm each, UNTESTED:** `621:161` threshold 0.7→~0.5,
  or a lips-detector swap. Flagged, not approvable from a sheet today.
- **Evidence:** `notes/Q3-zimage.md` lever 5 + baseline section;
  `notes/Q1-currency.md` §2.

### 9. Levers measured DEAD or settled — spend nothing further
- Eyes steps 16: max 4 levels on 0.015 % of frame (plain-euler ODE refines
  the same trajectory). ~2 s for nothing. (`Q3_L4` sheets.)
- Face denoise: 0.30 is a near no-op, 0.45 starts the airbrush direction —
  **0.35 is the knee; both sides now measured; done litigating.** (`Q3_L2`.)
- Mouth steps dial: dead on-mask (`Q3_L5`).
- `#592` steps 40→60: NOT an upgrade — dpmpp_2m_sde re-rolls the whole
  trajectory (17 dB full-frame, face moved 24 px, tone warmed). The seed
  gives you "different render" for free. Anti-recommended as a menu item.
  (`notes/Q4-settings.md` §5.)

---

## Licence-forced model swaps (track-1 items needing your EYE — sheets do not exist yet)

These are not optional quality ideas; the shipped files are encumbered
(LEGAL-MEMO §3b). They appear here because each fix changes pixels and
therefore needs an A/B you look at. Candidates below are staged with flags
read from APIs this session (`results/run4/quality/licences/`,
`notes/Q1-currency.md` items 1–2):

- **`4x-UltraSharpV2.pth`** (cc-by-nc-sa-4.0, live twice: #612 main upscale,
  #100 second): candidates all CC-BY-4.0/BSD — 4x-RealWebPhoto-v4-dat2 and
  4x-FaceUpDAT for #617's slot; 4x-NomosUni-span-multijpg (9 MB, fast) or
  4x-Nomos8kDAT for #98's slot; RealESRGAN_x4plus as the boring fallback.
  Expect quality-neutral-at-best; UltraSharpV2 is genuinely current — only
  the licence is the problem.
- **`x1_ITF_SkinDiffDetail_Lite_v1.pth`** (CC-BY-NC-SA-4.0, live at #90):
  1x-SkinContrast (CC0) or simply delete the 1x pass — A/B needed.
- **`lips_v1.pt`** (no-Sell flags, live at #161): LUSTIFY-style buyer-side
  fetch of the publisher's zip, or a detector swap (no clean drop-in found:
  Anzhc = AGPL, deepghs = "other", HF search = NC — all disqualified with
  stored responses).
- **Free detector upgrade candidate:** `face_yolov9c` from the same
  apache-2.0 Bingsu repo — +0.027 confidence, IoU 0.963 vs shipped on 14
  frames, behaviorally identical. Low value, zero cost.

## Currency facts (no action recommended)

- Six of seven pins are at upstream HEAD. **Do not bump controlnet_aux** —
  its 7 newer commits are a MediaPipe-0.10.32 rewrite proven (executed, not
  read) to crash under the product's own mediapipe 0.10.14 pin.
- ComfyUI core v0.29.0 changed Z-Image/Lumina2 RoPE numerics —
  output-affecting; the 0.15.1 pin stands. A buyer who upgrades core gets
  untested numerics; one controlled arm on a newer core is the cheap hedge.
- The unused `qwen-4b-zimage-heretic-q8.gguf` (apache-2.0 chain, provenance
  stored) needs a GGUF loader pack to even test — pack decision first.

## Protocol notes
Track 2 never touched `OFMTech-NSFW/`; the GPU lock + fresh-server-per-arm
discipline held throughout, including a mid-run priority yield to track 1's
gate (flock is not FIFO — recorded in `notes/R4-decisions.md` #10, drivers
now VRAM-gate before locking). Compiled by the orchestrating session from the
four agents' notes; every number above traces to a per-arm `meta.json`,
`metrics.json` or server log under `results/run4/quality/`.
