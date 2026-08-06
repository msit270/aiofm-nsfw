# TRACK V — adversarial verification of `620:110.device = "cpu"`

**VERDICT: PENDING — this file is being written as the arms land. Do not read the
verdict line until it says something other than PENDING.**

---

## 0. What was under test, and what I actually ran it against

Two commits sit on `trackB-crash-grid`, both one line of `OFMTech_NSFW.json`:

| commit | node | change |
|---|---|---|
| `8d166e0` | `620:114 FaceDetailer` | `denoise` 0.80 → 0.35 |
| `7ce1539` | `620:110 CLIPLoader` | `device` `default` → `cpu` ← **the fix under test** |

Three revisions of the workflow were converted to API format **through the real
frontend** (`browser_harness --no-submit --api-out`, i.e. the same
`graphToPrompt` path a buyer's Run button takes), never by hand:

| name | revision | `620:114.denoise` | `620:110.device` | md5 of the UI JSON |
|---|---|---|---|---|
| `prefix` | `8d166e0^` (`56adda8`) | 0.80 | `default` | `372f554a91b55650096e88e2c60c9ff9` |
| `mid` | `8d166e0` | 0.35 | `default` | `9c01cb829d4404df5368656a9de7b7ff` |
| `head` | `7ce1539` (HEAD) | 0.35 | `cpu` | `99423c096cc930432a38452880830a43` |

`tools/graph_diff/graph_diff.py` on the converted API graphs, constant-folded:

* `prefix` → `mid`: **1 real difference**, `620:114.inputs.denoise 0.8 → 0.35`.
* `mid` → `head`: **1 real difference**, `620:110.inputs.device "default" → "cpu"`.

(Each also reported `419.inputs.rgthree_comparer` appearing or disappearing —
baked-in stale temp-image state on the `Image Comparer (rgthree)` node, which
`tools/README.md` already lists as a shipped defect. It varies per browser
session, has no execution effect, and Track V's builder strips it from all three
so the arms are comparable.)

So the two commits are cleanly separable, and every arm below names which of the
two widgets it carries.

**`OFMTech-NSFW/OFMTech_NSFW.json` was not edited.** Every arm is an in-memory
mutation of one of those three converted graphs.

---

*(sections 1-8 follow once the arms are in)*
