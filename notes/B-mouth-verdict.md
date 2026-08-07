# Agent B — mouth stage deletion verdict (2026-08-08)

Measured (before/after deletion on PC baseline, per comp; deterministic
pipeline, diffs are pure effect; results/run5/mouth_deletion.json):

| comp | deletion diff >8 | read |
|---|---|---|
| FB full-body | 0.068% (lips box, max 123) | pass fires; subtle lip edit |
| PT portrait | 0.489% (lips + eyes re-roll coupling) | fires; subtle |
| CU close-up | 1.79% (mostly eyes-pass re-roll coupling) | fires; subtle at lips |
| OM open-mouth | 0.001% (91 px) | pass BLOCKED — SEGSRangeFilter 4M ceiling drops the big lips segment |

The mechanism inverts the stage's purpose: closed/small mouths (where
nothing needs fixing) get a subtle repaint; the open-mouth close-up — the
one composition class where a mouth pass could earn its keep (teeth) —
never runs it, because the lips segment at crop-factor 3 exceeds the 4M
area ceiling (620:648) on big faces.

**RECOMMENDATION (MY JUDGEMENT + the S6 verdict "no visible difference"):
DELETE the mouth stage.** Cost: the subtle lip edits shown in the
mouthdiff sheet tiles. Gains: 7 nodes and one detector model out;
~3 s/render; one less failure surface; and the graph drops lips_v1.pt
entirely — which for the SELLABLE product removes one of the three
NonCommercial-encumbered files (personal build: licensing-neutral, the
gain is simplicity).
Alternative kept on record, NOT recommended: raise the 4M ceiling so OM
comps fire — that would need its own quality A/B on teeth, and the stage's
measured contribution elsewhere is near-invisible.

Sheet: SHEETS/S13_mouth_deletion.png (before/after lips crops per comp).
