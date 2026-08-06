# TRACK V — adversarial verification of `620:110.device = "cpu"`

**VERDICT: PENDING — arms still landing. Do not quote this line until it changes.**

---

## 0. What was under test, and what I ran it against

Two commits sit on `trackB-crash-grid`, each one line of `OFMTech_NSFW.json`:

| commit | node | change |
|---|---|---|
| `8d166e0` | `620:114 FaceDetailer` | `denoise` 0.80 → 0.35 |
| `7ce1539` | `620:110 CLIPLoader` | `device` `default` → `cpu` ← **the fix under test** |

Three revisions were converted to API format **through the real frontend**
(`browser_harness --no-submit --api-out`, the same `graphToPrompt` path a buyer's
Run button takes), never by hand:

| name | revision | `620:114.denoise` | `620:110.device` | md5 of the UI JSON |
|---|---|---|---|---|
| `prefix` | `8d166e0^` (`56adda8`) | 0.80 | `default` | `372f554a91b55650096e88e2c60c9ff9` |
| `mid` | `8d166e0` | 0.35 | `default` | `9c01cb829d4404df5368656a9de7b7ff` |
| `head` | `7ce1539` (HEAD) | 0.35 | `cpu` | `99423c096cc930432a38452880830a43` |

`tools/graph_diff/graph_diff.py` on the converted API graphs, constant-folded:

* `prefix` → `mid`: **1 real difference**, `620:114.inputs.denoise 0.8 → 0.35`
* `mid` → `head`: **1 real difference**, `620:110.inputs.device "default" → "cpu"`

Each also reported `419.inputs.rgthree_comparer` appearing or disappearing —
baked-in stale temp-image state on the `Image Comparer (rgthree)` node, already
listed as a shipped defect in `tools/README.md`. It varies with the browser
session, has no execution effect, and Track V's builder strips it from all three
so the arms are comparable.

**`OFMTech-NSFW/OFMTech_NSFW.json` was not edited.** Every arm is an in-memory
mutation of one of those three converted graphs. `results/crash/V/arms/<ARM>/api_graph.json`
is the exact body submitted, for every arm.

### The harness is Track E's, proven rather than asserted

`graph_diff` between Track E's crashing arm `E18_alt1_gpuclip_crash` and Track V's
positive control `V_PC1_prefix_crash46_probe`:

```
RESULT: DIFFERENT — 1 difference(s): value_changed=1
  value_changed  TAP163.inputs.filename_prefix (SaveImage)
                 A: "crashA/tap163"   B: "crashV/tap163"
```

**One SaveImage filename apart.** So Track V is not "a similar setup" to the one
that produced the 9/9-vs-7/7 claim — node for node, input for input, it is the
same graph, rebuilt independently from the committed workflow rather than copied
from Track A's pinned snapshot.

And within Track V, the two halves of every A/B are one widget apart:

```
V_ISO_d035_gpu_a vs V_ISO_d035_cpu_a
RESULT: DIFFERENT — 1 difference(s): value_changed=1
  value_changed  620:110.inputs.device   A: "default"   B: "cpu"
```

---

## 1. STEP 1 — the positive control. This instance can still fail.

Pre-fix graph (`8d166e0^`: denoise 0.80, device `default`), the 46-token crashing
string, cold:

| arm | status | error | exec s | `execution_cached` | prompt_id |
|---|---|---|---|---|---|
| `V_PC1_prefix_crash46_probe` | **error** | `622:403 MaskBoundingBox+` | 38.0 | `[]` | `8f645231-50b3-4783-a4ea-8d7c9f0aa3b7` |

**`:18188` still reproduces.** Green results from it therefore mean something.

---

## 2. The attack that had to come first: the fix ships with a second commit attached

`8d166e0` (denoise 0.80 → 0.35) landed one commit before the fix, and Track E's
7/7-vs-9/9 evidence was gathered at denoise **0.80**, on `results/r4/R4_CF15_filled`,
a snapshot that predates it. So nothing on the record answered *"is the failure
even still there once the denoise commit is in?"* — and if the answer were no,
every green arm under the fix would be measuring nothing at all.

Full 2×2, 46-token string, interleaved, all cold:

| `620:114.denoise` | `620:110.device` | arms | result |
|---|---|---|---|
| 0.80 | `default` | 2 | **error `622:403` 2/2** (`V_PC1`, `V_ISO_d080_gpu_b`) |
| 0.35 | `default` | 2 | **error `622:403` 2/2** (`V_ISO_d035_gpu_a`, `V_ISO_d035_gpu_b`) |
| 0.80 | `cpu` | 1 | success (`V_ISO_d080_cpu_a`) |
| 0.35 | `cpu` | 2 | success (`V_ISO_d035_cpu_a`, `V_ISO_d035_cpu_b`) |

**The denoise change does not touch the failure. The device change removes it at
both denoise settings.** The confound is broken and the fix is genuinely testable
on the shipping artifact.

---

*(sections 3-9: proof set, awkward set, band sweep, seed attack, eye-prompt
attack, inertness, cost — appended as the arms land)*
