# Run 6 — your home Z-Image workflow vs pc_final: the diff and the diagnosis

Phone-readable. Every number verifier-re-derived from
results/run6/scores.json; sheets in results/run6/SHEETS/ (S1-S17).
Nothing in pc_final or the pack was changed; nothing pushed to master.

## First: score and eye AGREE this time

You told me to say it loudly if the reference looked better but scored
worse. It doesn't. It scores better too — on 3 of 4 compositions it
beats pc_final on cos-to-Luna, and on the sheets it also carries the
denser freckling, sharper catchlights and more directional light
(my read; your eye rules). The one place metric and texture pulled
apart — the UltraFlux VAE — the metric was RIGHT: dropping that VAE
into pc_final raised texture but visibly changed her eye color, 3/3
renders. cos-to-Luna has not been steering you wrong.

## What the file actually is

Not home-built: "MarlAI VIP - licensed copy, Licensed to: Stray,
Do not redistribute" (kept untracked in git for that reason). A flat
93-node Z-Image-Turbo pyramid: 112x144 draft -> refine at 224 ->
iterative latent upscale to 672 -> full-frame refine at 896x1152 ->
full-frame refine at 1344x1728, done. Denoise 0.5-0.7 at EVERY scale,
character LoRA active in EVERY pass, one prompt, a 1,466-character
Chinese anti-AI-look negative, UltraFlux fine-tuned VAE everywhere,
abliterated "heretic" Qwen GGUF text encoder, RES4LYF samplers with
detail-boost and perlin noise, inter-stage noise injection. No face
pass, no hands, no eyes, no detectors, no upscalers. 3 model files.
Renders in ~20 s at 1344x1728 (pc_final: 140-210 s at 2688x3456).

## Head-to-head (same prompt, same stage-1 seed, luna both sides,
## bit-exact deterministic — the zero noise floor held on 8 boots)

           reference      pc_final
portrait   .828  <- best likeness ever measured here   .747
close-up   .740                                        .659
cozy/home  .767                                        .728
full-body  .726                                        .759  <- pc wins

Body texture: reference 10.6-13.7 (at/above the 9.5 ZIT band on every
comp); pc reaches the band only on full-body. Sheets S1-S8.

## WHY it wins — measured, both directions

Every exotic component was isolated, in both graphs. None of them is
the likeness edge:
- UltraFlux VAE: +3 texture, MINUS .05-.06 likeness (both directions;
  eye-color drift on pc — S12). The texture gap IS this VAE; the
  likeness gap is despite it.
- Heretic GGUF TE: -.02 on the ref; transplanting it into pc_final
  broke the render twice (black face-hole, then confetti).
- The giant negative: +/-.02-.04 both ways = composition noise.
- LoRA 0.8 vs 1.0: +.024 on the ref.

What's left after you subtract the components is the architecture:
the pyramid re-generates the WHOLE frame with luna active at every
scale (7 passes, den 0.5-0.7). pc_final generates once, then protects
(den .25/.08 tiled + crop-composite face/eyes/hands). Run 5 already
proved Z+luna repainting raises likeness — the vendor built an entire
pipeline out of exactly that mechanism.

Direct confirmation on pc's own graph: raising ONE widget — the first
tiled refine's denoise .25 -> .45 — was worth +.049 (.759 -> .808 on
FB), the biggest single-widget likeness gain the project has recorded.

## The verdict you asked for, plainly

It's BOTH, split cleanly down the middle:

1. The likeness gap is something pc_final can PARTIALLY adopt today
   (widgets: den045 +.049, shift ladder +.023, anti-AI negative +.020;
   combo .789, not additive — S14/S16). Closing the rest of the PT/CU
   margin (+.08) needs pc to adopt the ref's PHILOSOPHY — regenerate
   instead of protect — which is a restructure, not a widget. Your
   call, sheeted not applied.

2. AND the reference genuinely does less, and part of its look rides
   on that: no hands/eyes/NSFW machinery to keep consistent, 27% of
   pc's pixels (downscaled viewing hides smoothing), and composition
   forms at 112x144 — which is precisely where it LOST to pc (its
   "full body balcony golden hour" drifted to a 3/4 indoor shot,
   and full-body is its one likeness loss). It also over-runs its own
   peak: its stage-3 preview at 896x1152 scores ABOVE its final on
   3 of 4 comps (.817/.850/.790 vs .726/.828/.740 — S11). Even the
   pipeline that does less, does too much at the end.

So: "your pipeline is doing too much" is TRUE about pc_final's
protect-don't-repaint refine settings, and FALSE about its surgical
machinery — hands, eyes, NSFW anatomy and 2688 delivery are work the
reference simply never attempts, and run 5's verdicts (hands combo,
mouth deletion) came from needing exactly that machinery.

## What I'd land / test next (recommendations only)

1. LAND-CANDIDATE: USDU-617 denoise 0.45 (one widget, +.049, texture
   flat, S16 to judge). Check close-up before adopting — untested there.
2. SHEET-AND-DECIDE: shift ladder 6/7 on the two tiled refines; the
   anti-AI negative text (results/run6/cn_negative.txt, translated
   summary: anti anime/CG/beauty-filter/influencer-face/studio-look).
3. DO NOT adopt UltraFlux VAE as a drop-in (identity drift). If you
   want its texture, it has to ride inside a regeneration pass the
   way the vendor uses it.
4. THE BIG ONE (pod session, restructure, your approval): hybrid —
   pyramid base (112->896 regeneration, luna active throughout) feeding
   pc_final's hands/eyes/upscale back-end. The ref's stage-3 at .85 is
   the likeness budget walking in the door; pc's back-end is the
   delivery machinery the ref lacks.
5. If you retrain anything: the vendor ships luna-class LoRAs at 0.8 —
   worth one tile per character (was +.024 here).

## Black frames — the open defect just became reproducible

Run 5 left this "environmental, non-reproduced in 40 probes". Run 6
found the recipe, reproduced across 8 boots with zero counterexamples:
a reference-family render goes black IFF an earlier reference-family
render with a DIFFERENT model composition (LoRA strength, VAE file, or
TE file) ran that boot AND at least one pc-family render came between
them; after the first black, everything ref-family stays black until
reboot. Text-only changes never trigger it. Suspect (inference): the
GGUF text encoder's eviction/reload path producing NaN conditioning —
it also explains the face-hole and confetti failures of the heretic-TE
transplant. Full isolation log: notes/R6-black-incident.md. Operational
rule until root-caused: one model composition per boot when the two
graph families share a server. This is the strongest lead the defect
has ever had — hand it to the torch-2.10/V10 upgrade session.

## Caveats, honest

- aikozimage.safetensors (your home character LoRA) isn't on this pod;
  both graphs ran luna. The comparison measures the GRAPHS, not aiko.
- RES4LYF/GGUF packs installed at today's HEAD; the vendor cut the file
  in June. Home-vs-here parity unproven; both arms ran today's code.
- Single composition seed per comp; lever deltas under ~.03 are noise.
- This server ran --disable-xformers (run-5 M2 didn't): same pc graph
  scores .759 here vs .789 there, bits differ — backend, not
  regression; all run-6 comparisons share one backend.
- P_hereticTE face-hole, P_COZY one-off black: documented, re-rendered.

## Three-way (your question): YES — upload the real ZIT-only workflow

Run 5's entire likeness anchor (the 0.92-0.94 band, the centroid
itself) was built from a RECONSTRUCTION of it. With the real file I
can (a) verify the reconstruction, (b) re-anchor the centroid if it
differs, and (c) close the triangle: simple-ZIT vs MarlAI pyramid vs
pc_final tells us whether the pyramid's +.08 comes from regeneration
scale-climbing or just from being Z-native end-to-end with no
detail passes. Drop it in reference/ and I'll run the same protocol.

## Evidence map

REF-PREFLIGHT.md (identity, hashes, packs) | notes/R6-structural-diff.md
(step 1) | notes/R6-ab-results.md (steps 2-3) | notes/R6-black-incident.md
(defect) | results/run6/ (40 arms: api_graph/history/meta each, scores.json,
SHEETS/S1-S17) | renders on pod: /workspace/run6/output/R6/.
Verifier pass: all claims re-derived clean; its 5 nits are fixed above.
