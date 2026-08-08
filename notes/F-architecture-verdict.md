# Agent F — architecture verdict (2026-08-08)

Reference research: results/run5/research_arch/ (no vendor reference for
this pipeline class exists; Impact-Pack docs/source are the de-facto
standard). Every community hypothesis was settled by rendering on THIS
graph (zero noise floor). Baseline: PC1 cos .799, dirR .208.

| structural A/B | result | verdict |
|---|---|---|
| K1 run-order flip (face+mouth detail BEFORE final upscale) | cos .780, light flat, no visible gain | current order (upscale->detail) CONFIRMED; matches ADetailer/USDU design intent |
| K4a colormatch chain removed | cos .765 | keep the chain (near-inert but removal measured slightly worse) |
| K4b colormatch once-at-end | cos .769 | no gain over per-pass |
| K4c colormatch factor 0.5 | cos .781 | no gain; factor 1.0 stays |
| K5 ImageBlend 1.0->0.6 (the dead dial made live) | cos .783, cv_c up | keep 1.0; dial documented as REPLACE semantics at 1.0 |
| K8 eyes noise-inject hook | requires ComfyUI_Noise pack (BNK nodes) — not installed | dropped; no sibling arm justified a new dependency |
| hands post-upscale (J_A4/A4b) | jewelry hallucination / crust | ordering hypothesis REFUTED on this graph |
| VAE round trip | REMOVED by the PC architecture itself | F question dissolved |
| SDXL double face pass | REMOVED by the PC architecture | dissolved |
| exclusive-region SEGS (eyes/mouth subtracted from face pass) | NOT rendered (wiring complexity; mouth deleted anyway) | open item, low priority — eyes pass re-samples ~its own region after face at 0.42; measured harm not demonstrated |

NET: zero structural adoptions. The PC chain as assembled (Z base ->
NMKD/x0.4 -> Z-USDU 1.25x -> hands -> 1x skin+blend -> Z-USDU 1.5x ->
face -> eyes) survives every A/B run against it. The architecture
interrogation is closed with the structure UNCHANGED but now EVIDENCED —
which is the difference the owner asked for.
