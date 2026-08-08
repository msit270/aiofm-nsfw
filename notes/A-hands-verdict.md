# Agent A — hands verdict (2026-08-08)

All arms on the PC baseline, one change each, like-for-like mediapipe hand
crops (S14/S14b; equal hand scale). Constraint-2 scored: photographic beats
detailed. MY JUDGEMENT lines are marked; diffs are measured.

| arm | read (J) | verdict |
|---|---|---|
| baseline (ship prompt "Detailed hand/fingers/fingernails") | pale, waxy, tendon lines, white knuckle speckles on PT | the rejected state |
| A1 neutral prompt | warmer, smoother, natural; PT speckles GONE | ADOPT |
| A1b "a hand" | like A1, slightly waxier highlight | no gain over A1 |
| A2 cf 3.0 | aged/wrinkled knuckles (fifty-year-old direction) | REJECT |
| A3 dn 0.28 / 0.32 | near-baseline, softer | neutral |
| A3g guide 768 | soft, fine natural texture, most photographic single | ADOPT |
| A4 hands AFTER final upscale | hallucinated beaded-jewelry artifacts across the hand | REJECT (refutes the reference-practice hypothesis on THIS graph) |
| A4b keep early + 0.15 polish after upscale | crusty/scabby texture | REJECT |
| **combo: A1 + A3g** | soft natural skin, fine pores, warm, no veins/artifacts — best hand of the run (J) | **ADOPTED into PC-final** |

Notes:
- The ordering hypothesis from reference practice (hands after upscale)
  FAILED by rendering — both post-upscale arms produced artifacts. The
  early-pass + ESRGAN-path order stays.
- The shipped detail-stack prompt was a real cause of overbake: prompt
  neutralization alone removed the PT knuckle speckles.
- The hands prompt is CHARACTER-SPECIFIC-ish (describe the character's
  hands); the neutral default ships, swap-checklist notes it.
- Depth-CN structural arm (Z Fun-Union, downloaded) NOT rendered: no
  structural failures appeared in any J arm to justify the complexity; the
  model file + research stay staged for a future structural-hands session.
- Detector: hand_yolov8s kept; hand_yolov9c fetched + staged (recall-only
  upgrade, licence ambiguity same class as shipped; not adopted this run).
