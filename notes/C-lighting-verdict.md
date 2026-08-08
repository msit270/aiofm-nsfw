# Agent C — lighting verdict (2026-08-08)

First honest lighting measurement of this project. Metrics are PROXIES
(formulas in tools/light_metrics.py): P5 shadow depth, spread (P95-P5),
rolloff shoulder, dirR directional coherence, local-contrast stats.
Baseline PC1: dirR .208, spread .563.

MEASURED (one change per arm, same seed; scene changes with prompt levers
are inherent — the sheet is the decision artifact):
- FILM sentence ("Kodak Portra 400, gentle flash falloff, candid"):
  dirR .341, spread .721, deepest shadows (P5 .0030), cos 0.820 — the
  best likeness AND strongest light of the run. Photographic read (J):
  reads like a real dusk flash photo; passes the 2D test emphatically.
- LIGHTPOS sentence (source+direction+quality): dirR .327 — second.
- SHIFT 4.5/6.0 on the base: spread .911 (+62%), dirR up — the strongest
  WIDGET lever; scene held better than prompt levers.
- negatives-vs-flatness: weak. cfg 2.5: dirR .137 — flattens (burn).
- PRESERVATION ARMS MEASURED NO-EFFECT: replacing the NMKD 4x sandwich
  with plain lanczos, and re-referencing colormatch to the base, both
  land within noise of baseline at delivery. The chain's flattening
  (pass-probe) is not recoverable by those two knobs; light must be
  GENERATED at the base.

ADOPTED into the build:
1. ModelSamplingAuraFlow exposed on the base at default 3.0 (inert by
   default — ComfyUI's ZImage class default is 3.0; the dial becomes
   visible for the shift 4.5-6 look).
2. Prompting guidance (README + CONFIG-SPEC): the film-stock and
   light-direction sentence patterns, marked SCENE-LEVEL (character-
   general technique, per-scene text).
NOT adopted: cfg above 2 (flattens); lighting negatives (weak).
