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
