# TRACK V — adversarial verification of `620:110.device = "cpu"`

**VERDICT: THE FIX DOES NOT HOLD. `620:110.device = "cpu"` does not cure the
black-face failure — it narrows it.** On the shipping artifact, with the fix
applied, cold and with an empty queue, a 103-token prompt reproduced
`622:403 MaskBoundingBox+ RuntimeError` **2 out of 2**, and the frame it produced
carries the identical failure signature to every pre-fix crash arm to five
decimal places: `(56,51,47)` over `0.16969` of the frame, `face_yolov8m.pt` max
confidence `0.4656`, zero faces at threshold 0.6. The fix does hold everywhere
`PHASE3-spec.md`'s required proof set looks — all five proof strings, both
measured bands, 4/4 acceptance checks — which is exactly why the proof set alone
would have passed it.

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

---

## 4. THE REFUTATION — `622:403` reproduced 3/3 with the fix applied

The brief also asked for "the awkward set: very long, punctuation-heavy,
non-English". One of those three strings breaks the fix.

`AW3_nonenglish`, **103 tokens** measured on the graph's own tokenizer:

```
luna、21歳の女性、そばかす、緑の瞳、詳細な肌の質感、柔らかい窓明かり
молодая женщина, веснушки, зелёные глаза
امرأة شابة، نمش، عيون خضراء
νεαρή γυναίκα, φακίδες 🌸👁️ éàüñçß
```

On the **shipping artifact** — `620:110.device = "cpu"`, `620:114.denoise = 0.35`,
both LoRAs, cold, empty queue, fresh `client_id`:

| arm | device | status | error | exec s | cached | prompt_id |
|---|---|---|---|---|---|---|
| `V_AW3_nonenglish` | **cpu** | **error** | `622:403 MaskBoundingBox+` | 81.5 | `[]` | `5b92eedd-20fc-4300-975e-16d5700f016a` |
| `V_AW3_rep1` | **cpu** | **error** | `622:403 MaskBoundingBox+` | 86.8 | `[]` | `08b43150-b078-475c-b2b8-9cdde2d727e3` |
| `V_AW3_rep2` | **cpu** | **error** | `622:403 MaskBoundingBox+` | 86.3 | `[]` | `c9f674e0` |
| `V_AW3_ctl` | `default` | error | `622:403 MaskBoundingBox+` | 49.4 | `[]` | `3f264f3d` |

Exception text, identical to `notes/CRASH.md` Phase 0:

```
RuntimeError: min(): Expected reduction dim to be specified for input.numel() == 0.
              Specify the reduction dim with the 'dim' argument.
```

22 nodes executed, the eyes stage never reached — the same 22 as every pre-fix
crash arm.

### It is the same failure, not a different bug on the same node

`621:163` tap of `V_AW3_nonenglish` (device **cpu**) against the pre-fix crash
arms (device `default`):

| measure | `V_AW3_nonenglish` (**cpu, the fix**) | every pre-fix crash arm |
|---|---|---|
| largest contiguous single-RGB blob | **0.16969** | 0.16969 |
| its colour | **(56,51,47)** | (56,51,47) |
| `face_yolov8m.pt` max confidence | **0.4656** | 0.4656 |
| faces detected at threshold 0.6 | **0** | 0 |
| `flat_frac` | **0.2387** | 0.2387 |
| exact-`(0,0,0)` fraction | 0.0 | 0.0 |

Five measures, five exact matches. This is `620:114`'s black state, lifted to
`(56,51,47)` by `620:111 ImageColorMatch+`, exactly as Track E described it —
reached with the fix in place.

### It is NOT the non-English content. It is the token count, and 103 is in a band nobody had mapped.

The obvious reading of `AW3` is "unicode breaks it". That is wrong, and the arm
that shows it is `V_AW3_ascii103`: **Track A's own pure-ASCII ladder string**
(`a woman's face` + `" the"` × 91) at **exactly 103 tokens**.

| tokens | string | `device: cpu` (the fix) | `device: default` |
|---|---|---|---|
| 34 | Russian only | success | — |
| 41 | Japanese only | success | — |
| 72 | `AW2`, ASCII, punctuation-heavy | success | — |
| **103** | `AW3`, mixed non-English | **error `622:403`** ×3 | **error `622:403`** |
| **103** | **ASCII ladder** | **error `622:403`** | **error `622:403`** |
| 166 | `AW1`, near-ASCII | success | — |
| 166 | ASCII ladder | success | — |

Both 103-token strings fail and both 166-token strings pass, on either device.
Russian at 34 tokens and Japanese at 41 are clean. **So the discriminator is
length, exactly as it always was — there is simply another crash band at ~103
tokens, and neither Track A's map nor the Phase 3 proof set ever went there.**
`notes/A-length-vs-content.md` describes the region above 44 as "a threshold with
no top"; that was an extrapolation from seven consecutive values and it is now
falsified in both directions — 103 fails, 166 does not.

### What the fix actually did

It did not remove the failure. It cured the bands that had been measured, and
those are the only bands the acceptance test looks at. Inside `PHASE3-spec.md`'s
proof set and inside Track A's 11–50 map the fix works — every arm in §3 passes
all four checks. In the ~103-token band it does nothing at all: `cpu` and
`default` fail identically, at the same node, with the same image.

---

## 5. The shape of the hole: the fix works at 60–96 and 140–166, and fails at 103–120

18 arms, ASCII ladder strings at fixed token counts, **each length run on both
devices**, all cold, all one widget apart:

| tokens | `device: cpu` (the fix) | `device: default` | what it means |
|---|---|---|---|
| 60 | clean | **error `622:403`** | fix works |
| 72 | clean | **error `622:403`** | fix works |
| 80 | clean | **error `622:403`** | fix works |
| 90 | clean | **error `622:403`** | fix works |
| 96 | clean | **error `622:403`** | fix works |
| **103** | **error `622:403`** | **error `622:403`** | **FIX FAILS** |
| **110** | **error `622:403`** | **error `622:403`** | **FIX FAILS** |
| **120** | **error `622:403`** | **error `622:403`** | **FIX FAILS** |
| 140 | clean | clean | nothing was wrong here |
| 166 | clean | **error `622:403`** | fix works |

Plus, from §4, 103 tokens on the *non-English* string: `cpu` error ×3,
`default` error, and error on the fully pre-fix graph too.

So the fix is not a cure and it is not a moved band. **It is a repair with a hole
in it, spanning at least 103–120 tokens**, sitting inside a region it otherwise
repairs on both sides. The lower edge is between 96 and 103; the upper edge is
between 120 and 140. I did not narrow either further.

Two other things fall out of this map that are worth more than the fix itself:

* **`notes/A-length-vs-content.md`'s "44+ is a threshold with no top" is false.**
  140 tokens renders clean on the *shipped, unfixed* graph. The claim was an
  extrapolation from seven consecutive values and the region above 50 is banded,
  not open-ended.
* **A buyer's prompt lands in this hole easily.** 103–120 tokens is an ordinary
  descriptive prompt — the shipped SDXL prompt in `483.prompt_batch_data` is
  already 60+ tokens, and the failure needs no unusual characters: a plain ASCII
  string of the right length is enough.

---

## 6. What I tried that did NOT break the fix

Everything below was an attempt to falsify it and failed to. It is the honest
other half of §4 and §5 — inside the region the fix covers, it is solid.

| attack | arms | result |
|---|---|---|
| Backing the denoise commit out (`8d166e0`) to check it was not the real cure | 7 | the denoise change is irrelevant; `device` is the whole effect (§2) |
| P1, the owner's own 32-token proof string | 2 fix / 1 control | fix passes 4/4 checks; control errors |
| P2, the 46-token crash string | 5 fix / 4 controls | fix passes 4/4; every control errors |
| P3, a constructed 50-token string | 1 fix / 1 control | fix passes 4/4; control errors |
| P4, the shipped 16-token placeholder | 2 | passes 4/4 |
| P5, the empty string (unmeasured before this session) | 1 | passes 4/4; does not refuse at all |
| Punctuation-heavy ASCII, 72 tokens | 1 fix / 2 controls | fix passes; controls error |
| Japanese only (41 tokens), Russian only (34 tokens) | 2 | both pass |
| Very long, 166 tokens, two different strings | 2 fix / 1 control | fix passes; control errors |
| Emoji, RTL Arabic, combining accents (inside `AW3`) | — | not the cause; the ASCII string of the same length fails identically |
| 622:403 as a "different bug" hypothesis | — | five image measures identical to the pre-fix crashes, to 5 d.p. |

**A green render was never accepted on its own.** Every fix arm was checked on
all four Phase 3 criteria — no exception, no black/flat fill, `face_yolov8m.pt`
confidence in the 0.89 class, and `622:406` present in the websocket `executing`
stream — and every one that passed, passed all four. Not one arm passed A while
failing B, C or D. Where the fix fails it fails loudly, at `622:403`; it never
produced the silent ruined-face success that `PHASE3-spec.md` §2 warned about.

---

## 7. The fix is NOT inert on clean renders — and the noise floor this project quotes does not apply here

The brief asked: "compare a 16-token render before and after the device change …
use the API-graph diff plus objective image deltas". Hashing output is banned, so
none was done.

**API-graph diff**: `V_CLEAN_mid_16a` vs `V_CLEAN_head_16a`, constant-folded —
`RESULT: DIFFERENT — 1 difference(s): 620:110.inputs.device "default" → "cpu"`.
One input, on one node. Nothing else in the submitted work differs.

**Objective image deltas**, delivered frames (`505 ← 622:418`), all cold:

| pair | what it isolates | PSNR | max abs diff | mean abs diff | pixels differing | pixels differing by >1 |
|---|---|---|---|---|---|---|
| `mid_16a` vs `mid_16b` | run-to-run, `default` | **99.00** | **0** | 0.00000 | **0.00000** | 0.00000 |
| `head_16a` vs `head_16b` | run-to-run, `cpu` | **99.00** | **0** | 0.00000 | **0.00000** | 0.00000 |
| `mid_16a` vs `head_16a` | **the fix**, 16 tokens | 48.77 | **135** | 0.10825 | **0.12824** | 0.02045 |
| `mid_16b` vs `head_16b` | the fix, 16 tokens, repeat | 48.77 | **135** | 0.10825 | **0.12824** | 0.02045 |
| `mid_40a` vs `head_40a` | the fix, 40 tokens | 47.67 | **135** | 0.12969 | 0.11916 | 0.02553 |

**Read the first two rows before the others.** Repeating the *same* graph on this
instance gives a **bit-identical** frame — `max_abs_diff 0`, not one pixel
different, twice. So on `:18188` the run-to-run noise floor is not 48.7 dB; it is
**zero**.

That matters because `notes/E-rootcause.md` argues the cured arms are healthy
partly on the grounds that they measure "PSNR 48.9 dB against the known-good
placeholder render — i.e. a real face, at this project's own measured run-to-run
floor of ~48.7 dB". **On this instance that comparison has no headroom in it.**
A same-graph repeat here is identical, so 48.77 dB between the two devices is not
noise — **all of it is the fix**. On a clean 16-token render where nothing was
wrong, changing the widget moves **12.8 % of the frame's pixels**, 2.0 % of them
by more than one 8-bit level, with a worst-case channel delta of **135 out of
255**.

Whether that is visible or an improvement is not mine to judge — the pair is at
`results/crash/V/arms/V_CLEAN_{mid,head}_16a/` and the 1:1 sheets are in
`results/crash/V/out/`. But "the fix must be inert where nothing was wrong" is
**not satisfied**, and it is measurable rather than arguable.

### Cost

Cold, on the probe graph, same box, interleaved:

| tokens | `device: default` | `device: cpu` | delta |
|---|---|---|---|
| 16 | 50.1 s, 50.9 s | 64.7 s, 64.7 s | **+14.1 s** |
| 40 | 50.6 s | 68.2 s | **+17.6 s** |

Track E's "+14 s per render" is **confirmed** at 16 tokens and grows with prompt
length, as an encoder running on the CPU would. These are probe-graph timings —
the SDXL half is replaced by a frozen base image — so they are the marginal cost
of the Z-Image detail stages, not of a whole buyer render.

---

## 8. The 26–50 band sweep: the fix holds everywhere it was measured

Track A's ladder string (`a woman's face` + `" the"` × n), every token count from
26 to 50, under the fix, all cold, plus interleaved one-widget controls:

**All 25 arms clean. Not one failure anywhere in 26–50.**

| tokens | under the fix (`cpu`) | interleaved control (`default`) | Track A's map |
|---|---|---|---|
| 26–29 | clean | — | clean |
| **30–32** | **clean** | `@32` **error `622:403`** | **CRASH** |
| 33–39 | clean | — | clean |
| 40 | clean | `@40` clean | clean |
| 41–43 | clean | — | clean |
| **44–50** | **clean** | `@46` **error `622:403`** | **CRASH** |

So the band did **not** move into 33–43 — the failure genuinely is gone from the
whole 26–50 range under the fix, and the two controls confirm the instance would
still have failed at 32 and 46 without it. This is the strongest single piece of
evidence *for* the fix in the session, and it is exactly what the acceptance test
was designed to see.

## 9. Final controls — the instance was still able to fail at the end

`PHASE3-spec.md` and the brief both require the pre-fix control re-run at the end,
because "if it stops failing mid-run, everything after the last good control is
void". Run last, after every fix arm:

| arm | `620:114.denoise` | `620:110.device` | status | error | cached |
|---|---|---|---|---|---|
| `V_PCEND_prefix` | 0.80 | `default` | **error** | `622:403` | `[]` |
| `V_PCEND_mid` | 0.35 | `default` | **error** | `622:403` | `[]` |
| `V_PCEND_head` | 0.35 | `cpu` | success | — | `[]` |

Plus two mid-run positive controls that also failed — `V_CTLm3` (pre-fix graph,
46 tokens) and `V_AW3_prefix_ctl` (pre-fix graph, 103 tokens) — and the
interleaved sweep controls at 32 and 46. **The reproducer was live at the start,
in the middle and at the end.** Nothing in this report sits after a control that
stopped working.

---

## 9b. Two more attacks, neither of which broke it — and one real win

**The seed attack** (mine, not in the brief). Track E's account is that `620:114`
is bistable on numerical noise of order 4e-7 relative. If so, the sampler seed is
a far larger perturbation than the one the fix applies, and a fix that only holds
at the shipped seed `1111111` would be luck. 46-token crash string,
`620:114.seed` changed:

| seed | `cpu` | `default` |
|---|---|---|
| 1111112 | success, 4/4 | **error `622:403`** |
| 42 | success, 4/4 | **error `622:403`** |
| 987654321 | success, 4/4 | — |
| 7 | success, 4/4 | — |

**The fix is not seed-specific.** Four seeds, four clean passes, and the two
controls still fail.

**The eye-prompt attack, and the fix's best result in the whole session.**
The second place this failure has been seen is the *eyes* pass, not the face
pass: Track A's `E398_tok31` shipped `status: success` with both eyes solid
black, by lengthening `622:398` (the eye prompt) from its shipped 28 tokens to 31
while leaving `620:106` on the safe placeholder. `622:398` encodes on the same
`620:110`, so the fix should reach it. It does:

| arm | `620:110.device` | A (no exception) | B (no black) | exact-black fraction | verdict |
|---|---|---|---|---|---|
| `V_E398_tok31_gpu` | `default` | **pass** | **FAIL** | **0.00452** (largest black blob 0.00251) | **FAIL** |
| `V_E398_tok31_cpu` | `cpu` | pass | pass | **0.00000** | **PASS** |
| `V_E398_tok31_cpu_b` | `cpu` | pass | pass | **0.00000** | **PASS** |

This is the one arm in the whole session that reproduces the failure mode
`PHASE3-spec.md` §2 was most worried about — **a green render with a ruined
face**, exit code 0, `status: success`, no exception anywhere — and the fix
removes it, 2/2. Note also that check A alone passes all three of these arms;
only B tells them apart. The four-check standard earned its keep here.

---

## 10. Verdict, stated plainly

**The fix does not hold, and I would not ship it as a cure.**

* It is real, and it is not the denoise commit: 60, 72, 80, 90, 96 and 166 tokens
  all fail on `default` and all render clean on `cpu`. Add the entire 26–50
  sweep and both proof-set bands. That is a lot of genuine repair.
* **It leaves a hole at 103–120 tokens**, where `cpu` and `default` fail
  identically, in a region an ordinary buyer prompt reaches without trying, using
  plain ASCII. Eight arms in that hole, zero of them clean.
* **It is not inert where nothing was wrong.** Same-graph repeats on this
  instance are bit-identical, so the 12.8 % of pixels that move on a clean
  16-token render — max channel delta 135/255 — are entirely the fix's doing.
* It costs +14 s at 16 tokens and +18 s at 40, growing with prompt length.
* It is **not** seed-specific (4 seeds, 4 passes), and it **does** cure the silent
  black-eyes failure on the eyes pass — the one failure mode that passes a naive
  "no crash" test — 2/2 against a `default` arm that produces `status: success`
  with 0.45 % of the frame exactly black.

**What I would do with it:** keep it, do not call it fixed. It is a strict
improvement over the shipped configuration on everything measured except cost and
byte-exactness, and it never once produced the silent ruined-face success that
`PHASE3-spec.md` §2 warns about — where it fails, it fails loudly at `622:403`.
But `622:403 MaskBoundingBox+` still converts "the detector found nothing" into an
unhandled `RuntimeError`, and with the hole at 103–120 still open that is now the
defect a buyer will actually meet. Track C's guard is worth having **in addition**,
on the explicit understanding that a fired guard is a failure report and not a pass.

**Where the acceptance test failed us:** every string in `PHASE3-spec.md`'s
required proof set passes, on all four checks, and so does the whole 26–50 sweep
the brief asked for. The fix would have been declared proven. It was caught only
by the awkward-string arms, and then only because the follow-up asked whether it
was the unicode or the length — it was the length, at a value nobody had ever
tested.


---

## Appendix A — the full grid

Every arm Track V ran, generated straight from the recorded `meta.json` and the
measured frames by `results/crash/V/tools/v_report.py`. Two tables: the four
acceptance checks, then the measurements they were judged on.

`A` no exception · `B` no black / no large single-RGB fill · `C` `face_yolov8m.pt`
max confidence >= 0.75 (the 0.89 class) · `D` `622:406` in the websocket
`executing` stream. `cached` is `len(execution_cached)` from `/history` — every
arm is 0. PSNR column is against `V_P4a`, the 16-token placeholder under the fix.

| arm | string (`620:106`) | tokens | `110.device` | `114.denoise` | prompt_id | cached | exec s | A | B | C | D | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `V_PC1_prefix_crash46_probe` | `'luna, a young woman with light freckles acros…'` | 46 | default | 0.8 | `8f645231` | 0 | 38.0 | **FAIL** | **FAIL** | **FAIL** | **FAIL** | **FAIL** |
| `V_ISO_d035_cpu_a` | `'luna, a young woman with light freckles acros…'` | 46 | cpu | 0.35 | `de408b96` | 0 | 102.4 | pass | pass | pass | pass | **PASS** |
| `V_ISO_d035_cpu_b` | `'luna, a young woman with light freckles acros…'` | 46 | cpu | 0.35 | `e901aa5b` | 0 | 91.6 | pass | pass | pass | pass | **PASS** |
| `V_ISO_d035_gpu_a` | `'luna, a young woman with light freckles acros…'` | 46 | default | 0.35 | `fcef2c9a` | 0 | 37.5 | **FAIL** | **FAIL** | **FAIL** | **FAIL** | **FAIL** |
| `V_ISO_d035_gpu_b` | `'luna, a young woman with light freckles acros…'` | 46 | default | 0.35 | `04c3d046` | 0 | 55.0 | **FAIL** | **FAIL** | **FAIL** | **FAIL** | **FAIL** |
| `V_ISO_d080_cpu_a` | `'luna, a young woman with light freckles acros…'` | 46 | cpu | 0.8 | `5ea56ccc` | 0 | 101.5 | pass | pass | pass | pass | **PASS** |
| `V_ISO_d080_gpu_b` | `'luna, a young woman with light freckles acros…'` | 46 | default | 0.8 | `7f199684` | 0 | 53.6 | **FAIL** | **FAIL** | **FAIL** | **FAIL** | **FAIL** |
| `V_P1a` | `'luna, 21 year old woman, freckles, green eyes…'` | 32 | cpu | 0.35 | `6383ce2f` | 0 | 105.3 | pass | pass | pass | pass | **PASS** |
| `V_P1b` | `'luna, 21 year old woman, freckles, green eyes…'` | 32 | cpu | 0.35 | `3c9e8a3b` | 0 | 67.3 | pass | pass | pass | pass | **PASS** |
| `V_P1c` | `'luna, 21 year old woman, freckles, green eyes…'` | 32 | cpu | 0.35 | `e42eac2f` | 0 | 89.5 | pass | pass | pass | pass | **PASS** |
| `V_P2a` | `'luna, a young woman with light freckles acros…'` | 46 | cpu | 0.35 | `49f85d96` | 0 | 92.3 | pass | pass | pass | pass | **PASS** |
| `V_P2b` | `'luna, a young woman with light freckles acros…'` | 46 | cpu | 0.35 | `4225fd8e` | 0 | 90.2 | pass | pass | pass | pass | **PASS** |
| `V_P2c` | `'luna, a young woman with light freckles acros…'` | 46 | cpu | 0.35 | `ae108075` | 0 | 91.1 | pass | pass | pass | pass | **PASS** |
| `V_P3a` | `'luna, a young woman with light freckles acros…'` | 50 | cpu | 0.35 | `f46a0593` | 0 | 93.1 | pass | pass | pass | pass | **PASS** |
| `V_P4a` | `'TRIGGER, PROMPT FOR YOUR MODEL'` | 16 | cpu | 0.35 | `dc28500c` | 0 | 75.9 | pass | pass | pass | pass | **PASS** |
| `V_P4b` | `'TRIGGER, PROMPT FOR YOUR MODEL'` | 16 | cpu | 0.35 | `1ca615f4` | 0 | 96.7 | pass | pass | pass | pass | **PASS** |
| `V_P5a` | `''` | 8 | cpu | 0.35 | `25d773fd` | 0 | 90.7 | pass | pass | pass | pass | **PASS** |
| `V_PCEND_head` | `'luna, a young woman with light freckles acros…'` | 46 | cpu | 0.35 | `9ba855a5` | 0 | 67.2 | pass | pass | pass | pass | **PASS** |
| `V_PCEND_mid` | `'luna, a young woman with light freckles acros…'` | 46 | default | 0.35 | `bc629b0a` | 0 | 38.5 | **FAIL** | **FAIL** | **FAIL** | **FAIL** | **FAIL** |
| `V_PCEND_prefix` | `'luna, a young woman with light freckles acros…'` | 46 | default | 0.8 | `fc0e5301` | 0 | 38.9 | **FAIL** | **FAIL** | **FAIL** | **FAIL** | **FAIL** |
| `V_CTLm1` | `'luna, 21 year old woman, freckles, green eyes…'` | 32 | default | 0.35 | `50586036` | 0 | 51.4 | **FAIL** | **FAIL** | **FAIL** | **FAIL** | **FAIL** |
| `V_CTLm2` | `'luna, a young woman with light freckles acros…'` | 50 | default | 0.35 | `2612bcfd` | 0 | 54.2 | **FAIL** | **FAIL** | **FAIL** | **FAIL** | **FAIL** |
| `V_CTLm3` | `'luna, a young woman with light freckles acros…'` | 46 | default | 0.8 | `4488368c` | 0 | 54.6 | **FAIL** | **FAIL** | **FAIL** | **FAIL** | **FAIL** |
| `V_AW1_verylong` | `'luna, a young woman photographed in a quiet n…'` | 166 | cpu | 0.35 | `7a0eb767` | 0 | 98.6 | pass | pass | pass | pass | **PASS** |
| `V_AW1_verylong_ctl` | `'luna, a young woman photographed in a quiet n…'` | 166 | default | 0.35 | `e23f77ce` | 0 | 60.1 | **FAIL** | **FAIL** | **FAIL** | **FAIL** | **FAIL** |
| `V_AW2_punct` | `'luna,,, ((21-year-old woman)) [freckles!!] {g…'` | 72 | cpu | 0.35 | `0c9ae8de` | 0 | 97.7 | pass | pass | pass | pass | **PASS** |
| `V_AW2_punct_ctl` | `'luna,,, ((21-year-old woman)) [freckles!!] {g…'` | 72 | default | 0.35 | `95a025cc` | 0 | 53.4 | **FAIL** | **FAIL** | **FAIL** | **FAIL** | **FAIL** |
| `V_AW3_ascii103` | `"a woman's face the the the the the the the th…"` | 103 | cpu | 0.35 | `b036d336` | 0 | 93.1 | **FAIL** | **FAIL** | **FAIL** | **FAIL** | **FAIL** |
| `V_AW3_ascii103_ctl` | `"a woman's face the the the the the the the th…"` | 103 | default | 0.35 | `04993591` | 0 | 57.3 | **FAIL** | **FAIL** | **FAIL** | **FAIL** | **FAIL** |
| `V_AW3_ascii166` | `"a woman's face the the the the the the the th…"` | 166 | cpu | 0.35 | `28824c28` | 0 | 103.3 | pass | pass | pass | pass | **PASS** |
| `V_AW3_ctl` | `'luna、21歳の女性、そばかす、緑の瞳、詳細な肌の質感、柔らかい窓明かり молодая…'` | 103 | default | 0.35 | `3f264f3d` | 0 | 49.4 | **FAIL** | **FAIL** | **FAIL** | **FAIL** | **FAIL** |
| `V_AW3_jp_only` | `'luna、21歳の女性、そばかす、緑の瞳、詳細な肌の質感、柔らかい窓明かり'` | 41 | cpu | 0.35 | `4582ed8c` | 0 | 89.3 | pass | pass | pass | pass | **PASS** |
| `V_AW3_nonenglish` | `'luna、21歳の女性、そばかす、緑の瞳、詳細な肌の質感、柔らかい窓明かり молодая…'` | 103 | cpu | 0.35 | `5b92eedd` | 0 | 81.5 | **FAIL** | **FAIL** | **FAIL** | **FAIL** | **FAIL** |
| `V_AW3_nonenglish_ctl` | `'luna、21歳の女性、そばかす、緑の瞳、詳細な肌の質感、柔らかい窓明かり молодая…'` | 103 | default | 0.35 | `a60839c9` | 0 | 49.5 | **FAIL** | **FAIL** | **FAIL** | **FAIL** | **FAIL** |
| `V_AW3_prefix_ctl` | `'luna、21歳の女性、そばかす、緑の瞳、詳細な肌の質感、柔らかい窓明かり молодая…'` | 103 | default | 0.8 | `54ab81f2` | 0 | 55.0 | **FAIL** | **FAIL** | **FAIL** | **FAIL** | **FAIL** |
| `V_AW3_rep1` | `'luna、21歳の女性、そばかす、緑の瞳、詳細な肌の質感、柔らかい窓明かり молодая…'` | 103 | cpu | 0.35 | `08b43150` | 0 | 86.8 | **FAIL** | **FAIL** | **FAIL** | **FAIL** | **FAIL** |
| `V_AW3_rep2` | `'luna、21歳の女性、そばかす、緑の瞳、詳細な肌の質感、柔らかい窓明かり молодая…'` | 103 | cpu | 0.35 | `c9f674e0` | 0 | 86.3 | **FAIL** | **FAIL** | **FAIL** | **FAIL** | **FAIL** |
| `V_AW3_ru_only` | `'luna, молодая женщина, веснушки, зелёные глаз…'` | 34 | cpu | 0.35 | `0a6a5fe0` | 0 | 97.8 | pass | pass | pass | pass | **PASS** |
| `V_SW_ctl_tok32` | `"a woman's face the the the the the the the th…"` | 32 | default | 0.35 | `b294632f` | 0 | 38.8 | **FAIL** | **FAIL** | **FAIL** | **FAIL** | **FAIL** |
| `V_SW_ctl_tok40` | `"a woman's face the the the the the the the th…"` | 40 | default | 0.35 | `e499a466` | 0 | 50.8 | pass | pass | pass | pass | **PASS** |
| `V_SW_ctl_tok46` | `"a woman's face the the the the the the the th…"` | 46 | default | 0.35 | `272ff3cc` | 0 | 37.7 | **FAIL** | **FAIL** | **FAIL** | **FAIL** | **FAIL** |
| `V_SW_tok26` | `"a woman's face the the the the the the the th…"` | 26 | cpu | 0.35 | `990d15a1` | 0 | 66.9 | pass | pass | pass | pass | **PASS** |
| `V_SW_tok27` | `"a woman's face the the the the the the the th…"` | 27 | cpu | 0.35 | `065d987e` | 0 | 66.1 | pass | pass | pass | pass | **PASS** |
| `V_SW_tok28` | `"a woman's face the the the the the the the th…"` | 28 | cpu | 0.35 | `f6023d31` | 0 | 66.0 | pass | pass | pass | pass | **PASS** |
| `V_SW_tok29` | `"a woman's face the the the the the the the th…"` | 29 | cpu | 0.35 | `d8e62b1b` | 0 | 66.4 | pass | pass | pass | pass | **PASS** |
| `V_SW_tok30` | `"a woman's face the the the the the the the th…"` | 30 | cpu | 0.35 | `4f3a4b3c` | 0 | 66.0 | pass | pass | pass | pass | **PASS** |
| `V_SW_tok31` | `"a woman's face the the the the the the the th…"` | 31 | cpu | 0.35 | `9c2611ce` | 0 | 66.2 | pass | pass | pass | pass | **PASS** |
| `V_SW_tok32` | `"a woman's face the the the the the the the th…"` | 32 | cpu | 0.35 | `92978b04` | 0 | 66.0 | pass | pass | pass | pass | **PASS** |
| `V_SW_tok33` | `"a woman's face the the the the the the the th…"` | 33 | cpu | 0.35 | `3fb68865` | 0 | 65.8 | pass | pass | pass | pass | **PASS** |
| `V_SW_tok34` | `"a woman's face the the the the the the the th…"` | 34 | cpu | 0.35 | `c6f67ebc` | 0 | 66.3 | pass | pass | pass | pass | **PASS** |
| `V_SW_tok35` | `"a woman's face the the the the the the the th…"` | 35 | cpu | 0.35 | `4cb20320` | 0 | 67.6 | pass | pass | pass | pass | **PASS** |
| `V_SW_tok36` | `"a woman's face the the the the the the the th…"` | 36 | cpu | 0.35 | `c047afee` | 0 | 67.5 | pass | pass | pass | pass | **PASS** |
| `V_SW_tok37` | `"a woman's face the the the the the the the th…"` | 37 | cpu | 0.35 | `c080b603` | 0 | 67.2 | pass | pass | pass | pass | **PASS** |
| `V_SW_tok38` | `"a woman's face the the the the the the the th…"` | 38 | cpu | 0.35 | `1f2d599e` | 0 | 67.6 | pass | pass | pass | pass | **PASS** |
| `V_SW_tok39` | `"a woman's face the the the the the the the th…"` | 39 | cpu | 0.35 | `238e3029` | 0 | 67.7 | pass | pass | pass | pass | **PASS** |
| `V_SW_tok40` | `"a woman's face the the the the the the the th…"` | 40 | cpu | 0.35 | `1f096e5a` | 0 | 67.3 | pass | pass | pass | pass | **PASS** |
| `V_SW_tok41` | `"a woman's face the the the the the the the th…"` | 41 | cpu | 0.35 | `224a92ff` | 0 | 66.8 | pass | pass | pass | pass | **PASS** |
| `V_SW_tok42` | `"a woman's face the the the the the the the th…"` | 42 | cpu | 0.35 | `37cd8c68` | 0 | 65.1 | pass | pass | pass | pass | **PASS** |
| `V_SW_tok43` | `"a woman's face the the the the the the the th…"` | 43 | cpu | 0.35 | `d69ea071` | 0 | 67.5 | pass | pass | pass | pass | **PASS** |
| `V_SW_tok44` | `"a woman's face the the the the the the the th…"` | 44 | cpu | 0.35 | `3cbe0bd4` | 0 | 66.6 | pass | pass | pass | pass | **PASS** |
| `V_SW_tok45` | `"a woman's face the the the the the the the th…"` | 45 | cpu | 0.35 | `aa243845` | 0 | 68.0 | pass | pass | pass | pass | **PASS** |
| `V_SW_tok46` | `"a woman's face the the the the the the the th…"` | 46 | cpu | 0.35 | `43c32d6d` | 0 | 68.5 | pass | pass | pass | pass | **PASS** |
| `V_SW_tok47` | `"a woman's face the the the the the the the th…"` | 47 | cpu | 0.35 | `8927159d` | 0 | 67.9 | pass | pass | pass | pass | **PASS** |
| `V_SW_tok48` | `"a woman's face the the the the the the the th…"` | 48 | cpu | 0.35 | `6e84816b` | 0 | 67.9 | pass | pass | pass | pass | **PASS** |
| `V_SW_tok49` | `"a woman's face the the the the the the the th…"` | 49 | cpu | 0.35 | `ecc0e2e5` | 0 | 68.7 | pass | pass | pass | pass | **PASS** |
| `V_SW_tok50` | `"a woman's face the the the the the the the th…"` | 50 | cpu | 0.35 | `e9659734` | 0 | 68.7 | pass | pass | pass | pass | **PASS** |
| `V_SEED_1111112_cpu` | `'luna, a young woman with light freckles acros…'` | 46 | cpu | 0.35 | `cdb9e540` | 0 | 67.8 | pass | pass | pass | pass | **PASS** |
| `V_CLEAN_head_16a` | `'TRIGGER, PROMPT FOR YOUR MODEL'` | 16 | cpu | 0.35 | `0c9f75d7` | 0 | 64.7 | pass | pass | pass | pass | **PASS** |
| `V_CLEAN_head_16b` | `'TRIGGER, PROMPT FOR YOUR MODEL'` | 16 | cpu | 0.35 | `c8eb3918` | 0 | 64.7 | pass | pass | pass | pass | **PASS** |
| `V_CLEAN_head_40a` | `"a woman's face the the the the the the the th…"` | 40 | cpu | 0.35 | `0d2ca9c2` | 0 | 68.2 | pass | pass | pass | pass | **PASS** |
| `V_CLEAN_mid_16a` | `'TRIGGER, PROMPT FOR YOUR MODEL'` | 16 | default | 0.35 | `18b35a3b` | 0 | 50.1 | pass | pass | pass | pass | **PASS** |
| `V_CLEAN_mid_16b` | `'TRIGGER, PROMPT FOR YOUR MODEL'` | 16 | default | 0.35 | `44e5a450` | 0 | 50.9 | pass | pass | pass | pass | **PASS** |
| `V_CLEAN_mid_40a` | `"a woman's face the the the the the the the th…"` | 40 | default | 0.35 | `beaf1738` | 0 | 50.6 | pass | pass | pass | pass | **PASS** |
| `V_B2_tok110_cpu` | `"a woman's face the the the the the the the th…"` | 110 | cpu | 0.35 | `a691f946` | 0 | 79.0 | **FAIL** | **FAIL** | **FAIL** | **FAIL** | **FAIL** |
| `V_B2_tok110_gpu` | `"a woman's face the the the the the the the th…"` | 110 | default | 0.35 | `2161edb9` | 0 | 38.1 | **FAIL** | **FAIL** | **FAIL** | **FAIL** | **FAIL** |
| `V_B2_tok120_cpu` | `"a woman's face the the the the the the the th…"` | 120 | cpu | 0.35 | `e7021bc7` | 0 | 80.9 | **FAIL** | **FAIL** | **FAIL** | **FAIL** | **FAIL** |
| `V_B2_tok120_gpu` | `"a woman's face the the the the the the the th…"` | 120 | default | 0.35 | `21ac5ccd` | 0 | 59.1 | **FAIL** | **FAIL** | **FAIL** | **FAIL** | **FAIL** |
| `V_B2_tok140_cpu` | `"a woman's face the the the the the the the th…"` | 140 | cpu | 0.35 | `ecaea613` | 0 | 102.3 | pass | pass | pass | pass | **PASS** |
| `V_B2_tok140_gpu` | `"a woman's face the the the the the the the th…"` | 140 | default | 0.35 | `cfff03ca` | 0 | 50.3 | pass | pass | pass | pass | **PASS** |
| `V_B2_tok166_cpu` | `"a woman's face the the the the the the the th…"` | 166 | cpu | 0.35 | `0f32dea9` | 0 | 77.2 | pass | pass | pass | pass | **PASS** |
| `V_B2_tok166_gpu` | `"a woman's face the the the the the the the th…"` | 166 | default | 0.35 | `6cb9cdf8` | 0 | 38.0 | **FAIL** | **FAIL** | **FAIL** | **FAIL** | **FAIL** |
| `V_B2_tok60_cpu` | `"a woman's face the the the the the the the th…"` | 60 | cpu | 0.35 | `7c7a57a1` | 0 | 101.6 | pass | pass | pass | pass | **PASS** |
| `V_B2_tok60_gpu` | `"a woman's face the the the the the the the th…"` | 60 | default | 0.35 | `425fbe23` | 0 | 49.7 | **FAIL** | **FAIL** | **FAIL** | **FAIL** | **FAIL** |
| `V_B2_tok72_cpu` | `"a woman's face the the the the the the the th…"` | 72 | cpu | 0.35 | `058ea935` | 0 | 69.6 | pass | pass | pass | pass | **PASS** |
| `V_B2_tok72_gpu` | `"a woman's face the the the the the the the th…"` | 72 | default | 0.35 | `fcdb1a01` | 0 | 38.4 | **FAIL** | **FAIL** | **FAIL** | **FAIL** | **FAIL** |
| `V_B2_tok80_cpu` | `"a woman's face the the the the the the the th…"` | 80 | cpu | 0.35 | `d88bcd5b` | 0 | 84.6 | pass | pass | pass | pass | **PASS** |
| `V_B2_tok80_gpu` | `"a woman's face the the the the the the the th…"` | 80 | default | 0.35 | `d48c724e` | 0 | 52.8 | **FAIL** | **FAIL** | **FAIL** | **FAIL** | **FAIL** |
| `V_B2_tok90_cpu` | `"a woman's face the the the the the the the th…"` | 90 | cpu | 0.35 | `5663d078` | 0 | 101.7 | pass | pass | pass | pass | **PASS** |
| `V_B2_tok90_gpu` | `"a woman's face the the the the the the the th…"` | 90 | default | 0.35 | `c860a1dc` | 0 | 51.5 | **FAIL** | **FAIL** | **FAIL** | **FAIL** | **FAIL** |
| `V_B2_tok96_cpu` | `"a woman's face the the the the the the the th…"` | 96 | cpu | 0.35 | `72661acd` | 0 | 71.5 | pass | pass | pass | pass | **PASS** |
| `V_B2_tok96_gpu` | `"a woman's face the the the the the the the th…"` | 96 | default | 0.35 | `22acf703` | 0 | 54.0 | **FAIL** | **FAIL** | **FAIL** | **FAIL** | **FAIL** |

| arm | judged on | exact-black | biggest 1-RGB blob | biggest non-white blob | YOLO max conf | error node |
|---|---|---|---|---|---|---|
| `V_PC1_prefix_crash46_probe` | TAP163 | 0.0 | 0.16969 [56, 51, 47] | 0.16969 [56, 51, 47] | 0.4656 | 622:403 |
| `V_ISO_d035_cpu_a` | 505 | 0.0 | 0.02073 [255, 255, 255] | 2e-05 [254, 255, 255] | 0.8941 | - |
| `V_ISO_d035_cpu_b` | 505 | 0.0 | 0.02073 [255, 255, 255] | 2e-05 [254, 255, 255] | 0.8941 | - |
| `V_ISO_d035_gpu_a` | TAP163 | 0.0 | 0.16969 [56, 51, 47] | 0.16969 [56, 51, 47] | 0.4656 | 622:403 |
| `V_ISO_d035_gpu_b` | TAP163 | 0.0 | 0.16969 [56, 51, 47] | 0.16969 [56, 51, 47] | 0.4656 | 622:403 |
| `V_ISO_d080_cpu_a` | 505 | 0.0 | 0.02073 [255, 255, 255] | 8e-05 [254, 255, 255] | 0.8946 | - |
| `V_ISO_d080_gpu_b` | TAP163 | 0.0 | 0.16969 [56, 51, 47] | 0.16969 [56, 51, 47] | 0.4656 | 622:403 |
| `V_P1a` | 505 | 0.0 | 0.02073 [255, 255, 255] | 2e-05 [254, 255, 255] | 0.8941 | - |
| `V_P1b` | 505 | 0.0 | 0.02073 [255, 255, 255] | 2e-05 [254, 255, 255] | 0.8941 | - |
| `V_P1c` | 505 | 0.0 | 0.02073 [255, 255, 255] | 2e-05 [254, 255, 255] | 0.8941 | - |
| `V_P2a` | 505 | 0.0 | 0.02073 [255, 255, 255] | 2e-05 [254, 255, 255] | 0.8941 | - |
| `V_P2b` | 505 | 0.0 | 0.02073 [255, 255, 255] | 2e-05 [254, 255, 255] | 0.8941 | - |
| `V_P2c` | 505 | 0.0 | 0.02073 [255, 255, 255] | 2e-05 [254, 255, 255] | 0.8941 | - |
| `V_P3a` | 505 | 0.0 | 0.02073 [255, 255, 255] | 2e-05 [254, 255, 255] | 0.8942 | - |
| `V_P4a` | 505 | 0.0 | 0.02073 [255, 255, 255] | 2e-05 [254, 255, 255] | 0.8943 | - |
| `V_P4b` | 505 | 0.0 | 0.02073 [255, 255, 255] | 2e-05 [254, 255, 255] | 0.8943 | - |
| `V_P5a` | 505 | 0.0 | 0.02073 [255, 255, 255] | 2e-05 [254, 255, 255] | 0.8942 | - |
| `V_PCEND_head` | 505 | 0.0 | 0.02073 [255, 255, 255] | 2e-05 [254, 255, 255] | 0.8941 | - |
| `V_PCEND_mid` | TAP163 | 0.0 | 0.16969 [56, 51, 47] | 0.16969 [56, 51, 47] | 0.4656 | 622:403 |
| `V_PCEND_prefix` | TAP163 | 0.0 | 0.16969 [56, 51, 47] | 0.16969 [56, 51, 47] | 0.4656 | 622:403 |
| `V_CTLm1` | TAP163 | 0.0 | 0.16969 [56, 51, 47] | 0.16969 [56, 51, 47] | 0.4656 | 622:403 |
| `V_CTLm2` | TAP163 | 0.0 | 0.16969 [56, 51, 47] | 0.16969 [56, 51, 47] | 0.4656 | 622:403 |
| `V_CTLm3` | TAP163 | 0.0 | 0.16969 [56, 51, 47] | 0.16969 [56, 51, 47] | 0.4656 | 622:403 |
| `V_AW1_verylong` | 505 | 0.0 | 0.02073 [255, 255, 255] | 2e-05 [254, 255, 255] | 0.8944 | - |
| `V_AW1_verylong_ctl` | TAP163 | 0.0 | 0.16969 [56, 51, 47] | 0.16969 [56, 51, 47] | 0.4656 | 622:403 |
| `V_AW2_punct` | 505 | 0.0 | 0.02073 [255, 255, 255] | 2e-05 [254, 255, 255] | 0.8943 | - |
| `V_AW2_punct_ctl` | TAP163 | 0.0 | 0.16969 [56, 51, 47] | 0.16969 [56, 51, 47] | 0.4656 | 622:403 |
| `V_AW3_ascii103` | TAP163 | 0.0 | 0.16969 [56, 51, 47] | 0.16969 [56, 51, 47] | 0.4656 | 622:403 |
| `V_AW3_ascii103_ctl` | TAP163 | 0.0 | 0.16969 [56, 51, 47] | 0.16969 [56, 51, 47] | 0.4656 | 622:403 |
| `V_AW3_ascii166` | 505 | 0.0 | 0.02073 [255, 255, 255] | 2e-05 [254, 255, 255] | 0.8942 | - |
| `V_AW3_ctl` | TAP163 | 0.0 | 0.16969 [56, 51, 47] | 0.16969 [56, 51, 47] | 0.4656 | 622:403 |
| `V_AW3_jp_only` | 505 | 0.0 | 0.02073 [255, 255, 255] | 2e-05 [254, 255, 255] | 0.8943 | - |
| `V_AW3_nonenglish` | TAP163 | 0.0 | 0.16969 [56, 51, 47] | 0.16969 [56, 51, 47] | 0.4656 | 622:403 |
| `V_AW3_nonenglish_ctl` | TAP163 | 0.0 | 0.16969 [56, 51, 47] | 0.16969 [56, 51, 47] | 0.4656 | 622:403 |
| `V_AW3_prefix_ctl` | TAP163 | 0.0 | 0.16969 [56, 51, 47] | 0.16969 [56, 51, 47] | 0.4656 | 622:403 |
| `V_AW3_rep1` | TAP163 | 0.0 | 0.16969 [56, 51, 47] | 0.16969 [56, 51, 47] | 0.4656 | 622:403 |
| `V_AW3_rep2` | TAP163 | 0.0 | 0.16969 [56, 51, 47] | 0.16969 [56, 51, 47] | 0.4656 | 622:403 |
| `V_AW3_ru_only` | 505 | 0.0 | 0.02073 [255, 255, 255] | 2e-05 [254, 255, 255] | 0.8942 | - |
| `V_SW_ctl_tok32` | TAP163 | 0.0 | 0.16969 [56, 51, 47] | 0.16969 [56, 51, 47] | 0.4656 | 622:403 |
| `V_SW_ctl_tok40` | 505 | 0.0 | 0.02073 [255, 255, 255] | 2e-05 [254, 255, 255] | 0.8944 | - |
| `V_SW_ctl_tok46` | TAP163 | 0.0 | 0.16969 [56, 51, 47] | 0.16969 [56, 51, 47] | 0.4656 | 622:403 |
| `V_SW_tok26` | 505 | 0.0 | 0.02073 [255, 255, 255] | 2e-05 [254, 255, 255] | 0.8942 | - |
| `V_SW_tok27` | 505 | 0.0 | 0.02073 [255, 255, 255] | 2e-05 [254, 255, 255] | 0.8942 | - |
| `V_SW_tok28` | 505 | 0.0 | 0.02073 [255, 255, 255] | 2e-05 [254, 255, 255] | 0.8941 | - |
| `V_SW_tok29` | 505 | 0.0 | 0.02073 [255, 255, 255] | 2e-05 [254, 255, 255] | 0.8942 | - |
| `V_SW_tok30` | 505 | 0.0 | 0.02073 [255, 255, 255] | 2e-05 [254, 255, 255] | 0.8943 | - |
| `V_SW_tok31` | 505 | 0.0 | 0.02073 [255, 255, 255] | 2e-05 [254, 255, 255] | 0.8944 | - |
| `V_SW_tok32` | 505 | 0.0 | 0.02073 [255, 255, 255] | 2e-05 [254, 255, 255] | 0.8941 | - |
| `V_SW_tok33` | 505 | 0.0 | 0.02073 [255, 255, 255] | 2e-05 [254, 255, 255] | 0.8942 | - |
| `V_SW_tok34` | 505 | 0.0 | 0.02073 [255, 255, 255] | 0.0 [16, 13, 13] | 0.8945 | - |
| `V_SW_tok35` | 505 | 0.0 | 0.02073 [255, 255, 255] | 2e-05 [254, 255, 255] | 0.8942 | - |
| `V_SW_tok36` | 505 | 0.0 | 0.02073 [255, 255, 255] | 2e-05 [254, 255, 255] | 0.8943 | - |
| `V_SW_tok37` | 505 | 0.0 | 0.02073 [255, 255, 255] | 2e-05 [254, 255, 255] | 0.8942 | - |
| `V_SW_tok38` | 505 | 0.0 | 0.02073 [255, 255, 255] | 2e-05 [254, 255, 255] | 0.8943 | - |
| `V_SW_tok39` | 505 | 0.0 | 0.02073 [255, 255, 255] | 2e-05 [254, 255, 255] | 0.894 | - |
| `V_SW_tok40` | 505 | 0.0 | 0.02073 [255, 255, 255] | 2e-05 [254, 255, 255] | 0.894 | - |
| `V_SW_tok41` | 505 | 0.0 | 0.02073 [255, 255, 255] | 2e-05 [254, 255, 255] | 0.8941 | - |
| `V_SW_tok42` | 505 | 0.0 | 0.02073 [255, 255, 255] | 2e-05 [254, 255, 255] | 0.8941 | - |
| `V_SW_tok43` | 505 | 0.0 | 0.02073 [255, 255, 255] | 0.0 [16, 13, 13] | 0.8944 | - |
| `V_SW_tok44` | 505 | 0.0 | 0.02073 [255, 255, 255] | 2e-05 [254, 255, 255] | 0.8943 | - |
| `V_SW_tok45` | 505 | 0.0 | 0.02073 [255, 255, 255] | 2e-05 [254, 255, 255] | 0.8942 | - |
| `V_SW_tok46` | 505 | 0.0 | 0.02073 [255, 255, 255] | 0.0 [16, 13, 13] | 0.8945 | - |
| `V_SW_tok47` | 505 | 0.0 | 0.02073 [255, 255, 255] | 2e-05 [254, 255, 255] | 0.8942 | - |
| `V_SW_tok48` | 505 | 0.0 | 0.02073 [255, 255, 255] | 2e-05 [254, 255, 255] | 0.8943 | - |
| `V_SW_tok49` | 505 | 0.0 | 0.02073 [255, 255, 255] | 2e-05 [254, 255, 255] | 0.8942 | - |
| `V_SW_tok50` | 505 | 0.0 | 0.02073 [255, 255, 255] | 2e-05 [254, 255, 255] | 0.8942 | - |
| `V_SEED_1111112_cpu` | 505 | 0.0 | 0.02073 [255, 255, 255] | 2e-05 [254, 255, 255] | 0.8954 | - |
| `V_CLEAN_head_16a` | 505 | 0.0 | 0.02073 [255, 255, 255] | 2e-05 [254, 255, 255] | 0.8943 | - |
| `V_CLEAN_head_16b` | 505 | 0.0 | 0.02073 [255, 255, 255] | 2e-05 [254, 255, 255] | 0.8943 | - |
| `V_CLEAN_head_40a` | 505 | 0.0 | 0.02073 [255, 255, 255] | 2e-05 [254, 255, 255] | 0.894 | - |
| `V_CLEAN_mid_16a` | 505 | 0.0 | 0.02073 [255, 255, 255] | 2e-05 [254, 255, 255] | 0.8942 | - |
| `V_CLEAN_mid_16b` | 505 | 0.0 | 0.02073 [255, 255, 255] | 2e-05 [254, 255, 255] | 0.8942 | - |
| `V_CLEAN_mid_40a` | 505 | 0.0 | 0.02073 [255, 255, 255] | 2e-05 [254, 255, 255] | 0.8944 | - |
| `V_B2_tok110_cpu` | TAP163 | 0.0 | 0.16969 [56, 51, 47] | 0.16969 [56, 51, 47] | 0.4656 | 622:403 |
| `V_B2_tok110_gpu` | TAP163 | 0.0 | 0.16969 [56, 51, 47] | 0.16969 [56, 51, 47] | 0.4656 | 622:403 |
| `V_B2_tok120_cpu` | TAP163 | 0.0 | 0.16969 [56, 51, 47] | 0.16969 [56, 51, 47] | 0.4656 | 622:403 |
| `V_B2_tok120_gpu` | TAP163 | 0.0 | 0.16969 [56, 51, 47] | 0.16969 [56, 51, 47] | 0.4656 | 622:403 |
| `V_B2_tok140_cpu` | 505 | 0.0 | 0.02073 [255, 255, 255] | 2e-05 [254, 255, 255] | 0.8942 | - |
| `V_B2_tok140_gpu` | 505 | 0.0 | 0.02073 [255, 255, 255] | 0.0 [16, 13, 13] | 0.8941 | - |
| `V_B2_tok166_cpu` | 505 | 0.0 | 0.02073 [255, 255, 255] | 2e-05 [254, 255, 255] | 0.8942 | - |
| `V_B2_tok166_gpu` | TAP163 | 0.0 | 0.16969 [56, 51, 47] | 0.16969 [56, 51, 47] | 0.4656 | 622:403 |
| `V_B2_tok60_cpu` | 505 | 0.0 | 0.02073 [255, 255, 255] | 2e-05 [254, 255, 255] | 0.8942 | - |
| `V_B2_tok60_gpu` | TAP163 | 0.0 | 0.16969 [56, 51, 47] | 0.16969 [56, 51, 47] | 0.4656 | 622:403 |
| `V_B2_tok72_cpu` | 505 | 0.0 | 0.02073 [255, 255, 255] | 2e-05 [254, 255, 255] | 0.8944 | - |
| `V_B2_tok72_gpu` | TAP163 | 0.0 | 0.16969 [56, 51, 47] | 0.16969 [56, 51, 47] | 0.4656 | 622:403 |
| `V_B2_tok80_cpu` | 505 | 0.0 | 0.02073 [255, 255, 255] | 2e-05 [254, 255, 255] | 0.8943 | - |
| `V_B2_tok80_gpu` | TAP163 | 0.0 | 0.16969 [56, 51, 47] | 0.16969 [56, 51, 47] | 0.4656 | 622:403 |
| `V_B2_tok90_cpu` | 505 | 0.0 | 0.02073 [255, 255, 255] | 0.0 [16, 13, 13] | 0.8943 | - |
| `V_B2_tok90_gpu` | TAP163 | 0.0 | 0.16969 [56, 51, 47] | 0.16969 [56, 51, 47] | 0.4656 | 622:403 |
| `V_B2_tok96_cpu` | 505 | 0.0 | 0.02073 [255, 255, 255] | 0.0 [16, 13, 13] | 0.8941 | - |
| `V_B2_tok96_gpu` | TAP163 | 0.0 | 0.16969 [56, 51, 47] | 0.16969 [56, 51, 47] | 0.4656 | 622:403 |


### Voided arms — run but NOT counted

`results/crash/V/arms_void/` holds four arms discarded because they overlapped a
second driver process of my own (see `notes/V-questions.md` §1): `V_ISO_d035_cpu_a`,
`V_ISO_d080_cpu_a`, `V_ISO_d035_gpu_b`, `V_ISO_d035_cpu_b` and `V_P1b__overlap`.
All were re-run under the same names and only the re-runs appear above. Two
further prompt_ids executed on the server without being recorded by any driver
(`6309ef32-…`, `439609a1-…`, both `success`, both the 46-token string on `cpu`);
they are counted nowhere.

## Appendix B — where everything is

| what | where |
|---|---|
| every arm: submitted API graph, meta, websocket stream, images | `results/crash/V/arms/<ARM>/` |
| every arm's verbatim `/history/<prompt_id>` | `results/crash/V/history/` |
| the three converted workflow revisions and their API graphs | `results/crash/V/graphs/` |
| acceptance measurements for every arm | `results/crash/V/out/v_checks.json` |
| inertness pair deltas | `results/crash/V/out/v_pairs.json` |
| 1:1 face/skin sheets, crash vs cure | `results/crash/V/out/V_fix_ab_*.png` |
| 1:1 face/skin sheets, the inertness pair | `results/crash/V/out/V_inert_ab_*.png` |
| tools (driver, builders, checks, report, band map) | `results/crash/V/tools/` |

Band-sweep PNGs are deliberately not committed (`.gitignore`); their evidence is
in `meta.json` and `v_checks.json`, same convention as `results/crash/A/arms`.
