# R6 — A/B + attribution results (STEPS 2-3)

All numbers: results/run6/scores.json (ArcFace cos to the run-5 luna
centroid; ZIT-to-ZIT band 0.92-0.94; faceHF/bodyHF = run-5 freckle-band
RMS, scale-normalized). Every arm black-checked; determinism proven
bit-identical same-boot AND cross-boot on 4 boots (R_FB x4, P_FB x2,
stockTE x2). Single seed (12345) unless noted — deltas under ~0.03
treated as composition noise, and said so.

## Head-to-head (same positive prompt, same seed, luna@1.0 both sides,
## each graph's own shipped negative)

comp  | MarlAI ref (1344x1728, ~20 s) | pc_final (2688x3456, ~140-210 s)
FB    | .726  faceHF 10.95 body 10.65 | .759  faceHF 9.65  body 9.62
PT    | .828  faceHF 11.29 body 12.84 | .747  faceHF 10.97 body 9.50
CU    | .740  faceHF 11.18 body 5.54  | .659  faceHF 11.76 body 4.81
COZY  | .767  faceHF 12.31 body 13.73 | .728  faceHF 10.10 body 11.91

- Ref wins likeness on PT (+.081), CU (+.081), COZY (+.038); loses FB
  (-.033). Ref PT .828 is the highest likeness this project has
  measured on any full pipeline (run-5 best: film-sentence FB .820).
- Ref body texture 10.6-13.7 vs pc 4.8-11.9 — at or above the ZIT
  reference band (~9.5) on every comp; pc reaches it only on FB.
- FB caveat: the ref forms composition at a 112x144 draft — its FB
  frame drifted to a 3/4 shot (no balcony/golden-hour framing); the
  likeness loss and the framing drift travel together.
- Ref stage-3 (896x1152) beats its own final on FB/PT/CU
  (.817/.849/.790 vs .726/.828/.740) — the last 1344 pass COSTS
  likeness on 3 of 4 comps (not COZY). The vendor ships it anyway.
- Speed: ref renders in ~19-20 s; pc in 140-208 s (7-10x). Ref output
  is 27% of pc's pixels — do not credit the ref for that (step-4 list).

## Lever attribution (FB, single seed; both directions where possible)

pc_final + lever:
- den045 (USDU-617 denoise .25->.45)      cos .808 (+.049)  texture flat
- shift ladder 6/7 on the two tiled USDUs cos .782 (+.023)
- anti-AI Chinese negative (base only)    cos .779 (+.020)  bodyHF +0.4
- combo of the three                      cos .789 (+.030)  NOT additive
- UltraFlux VAE drop-in                   cos .696 (-.063)  faceHF +3.0,
  bodyHF +2.7 — and the EYE COLOR CHANGED (visually confirmed identity
  drift, 3/3 replications incl. combo_uvae .676)
- heretic GGUF TE                         BROKEN 2/2 (black face-region
  composite; then full-frame confetti) — see black-frame rule below.

MarlAI ref + lever (reverse direction):
- stock ae VAE (replace UltraFlux)        cos .770 (+.044)  faceHF -1.4,
  bodyHF -2.0  -> the texture gap IS the VAE, both directions.
- stock qwen safetensors TE               cos .745 (+.019)
- pc 7-word negative                      cos .769 (+.043)
- luna @ 0.8 (vendor's shipped strength)  cos .750 (+.024)

Reading: every exotic COMPONENT of the ref (UltraFlux VAE, heretic TE,
giant negative) moves likeness DOWN or within noise when isolated.
The ref's likeness edge is therefore ARCHITECTURAL — the multi-scale
full-frame regeneration with the character LoRA active at every scale
(exactly the mechanism run 5 identified: Z+luna repainting RAISES
likeness; pc only does it in two low-denoise tiled passes + one face
crop). Its texture edge is the UltraFlux VAE, which pc cannot adopt
naively (identity drift) but the ref absorbs inside regeneration.

## Score-vs-look (step 3)

NO inversion found. On every pair I examined (PT/FB/COZY faces, VAE
tiles), metric direction and my visual read agree — where the ref
scores higher it also carries denser freckling, sharper catchlights,
more directional light (JUDGEMENT, owner's eye rules; sheets S1-S17).
The one tension — UltraFlux raising texture while dropping cos — is
resolved IN FAVOR of the metric: the drop is real drift (eye color).
Caveat: cos-to-Luna still cannot see lighting/pose taste; the sheets
are the authority for that, as in run 5.

## Cross-run note

P_FB here scores .759 vs .789 for the byte-same graph in run-5 M2.
The two renders differ (max_abs 163, mean 2.7): this server runs
--disable-xformers (run-5's 19188 did not). Backend delta, labeled
inference; all run-6 arms share one backend so every comparison above
is internally consistent.

## Renders/evidence
results/run6/<arm>/{api_graph,history,meta}.json for all 40 arms;
sheets S1-S17 in results/run6/SHEETS/; black-frame isolation in
notes/R6-black-incident.md (deterministic repro rule found — first
reproducible recipe for the run-5 open defect).
