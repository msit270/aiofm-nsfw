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

## 3. The Phase 3 proof set

All arms cold (`execution_cached: []` confirmed in `/history`, not merely a
`/free` issued), fresh `client_id`, full history under
`results/crash/V/history/`. Token counts measured by me on
`comfy.text_encoders.z_image.ZImageTokenizer`, not taken from anyone's table.

| # | string | tokens (measured) | arms under the fix | one-widget control |
|---|---|---|---|---|
| P1 | the owner's proof string, byte-exact | **32** | `V_P1a` `V_P1c` — success | `V_CTLm1` — **error `622:403`** |
| P2 | the known crashing string | **46** | `V_P2a` `V_P2b` `V_P2c` (+ `V_ISO_d035_cpu_a/b`) — success | `V_ISO_d035_gpu_a/b`, `V_CTLm3` — **error `622:403`** |
| P3 | constructed, 47–50 band | **50** | `V_P3a` — success | `V_CTLm2` — **error `622:403`** |
| P4 | shipped placeholder | **16** | `V_P4a` `V_P4b` — success | (16 tokens is a clean band; `V_CLEAN_mid_16*` is its pair) |
| P5 | empty string | **8** | `V_P5a` — success | — |

**P5 was `UNMEASURED` in `PHASE3-spec.md`. It is measured now: the empty string
does not refuse at all.** `success`, 90.7 s, 33 nodes executed, `622:406` among
them, a healthy face at YOLO 0.8942. The 8 tokens are `ZImageTokenizer`'s fixed
`<|im_start|>user\n{}<|im_end|>\n<|im_start|>assistant\n` wrapper, so an empty
prompt is still a well-formed 8-token conditioning; nothing downstream sees an
empty tensor.

**Every one of the three interleaved one-widget controls still errors at
`622:403`**, so none of these strings is sitting in an already-safe band, and the
green arms are not measuring nothing.

*(sections 4-9 appended as the remaining arms land)*
