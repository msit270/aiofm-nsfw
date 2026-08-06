# Track B — the factor grid on the face-prompt crash

**Server: `127.0.0.1:28191` only** (`/workspace/comfy-r2gate3`, `--reserve-vram 16`).
Every arm and every control below ran there. Nothing here ran on 18188 and no
result from 18188 is mixed into a comparison.

**Graph frozen.** `OFMTech-NSFW/OFMTech_NSFW.json` is untouched
(`sha256 a811b5d690ccc5207bc7bd1c626cdd3db3b720b9be60d0a687436efcfd2143d8`,
checked before the first arm and after the last). Every arm is an in-memory
mutation of an already converted API graph:
`results/r4/R4_CF15_filled/api_graph.json` (crashing string) or
`results/r4/R4_CF15_placeholder/api_graph.json` (placeholder). Those two files
differ in `620:106.inputs.text` and **nothing else** — verified by a full
input-wise diff, not by eye.

Every arm: `POST /free {"unload_models":true,"free_memory":true}` first, a fresh
`client_id`, `execution_cached` confirmed `[]`. Nothing was ever deleted from the
queue. Arms, `api_graph.json`, `history.json`, `meta.json` and images are under
`results/crash/B/<arm>/`.

---

## Verdicts, one line per letter

**Baseline — the crash reproduces on 28191** at `622:403 MaskBoundingBox+` with
the known string, and the shipped placeholder renders clean *and bit-identical to
the 18188 reference render*, so the grid is interpretable.

**B — the LoRAs ARE load-bearing for the crash, and so is the `luna, ` prefix; the
crash needs all three of trigger + long description + LoRAs.** The arm that shows
the LoRAs: `B1_noloras_crashstring`, two widget values apart from
`A0_baseline_crash`, does not crash (2/2, bit-identical). **But it is not a fix —
`status: success` with 23.5 % of the frame a single constant RGB where the face
should be.** The arm that shows the prefix: `B2_loras_noprefix`, one string apart,
renders clean *and healthy* (2/2, bit-identical). Removing the prefix gives a good
image back; removing the LoRAs only converts the crash into a silent ruined face.

**C — raising `cfg` does not rescue it.** `cfg 2` crashes identically to the
shipping `cfg 1`, measured cleanly. `cfg 5` also crashed but both attempts went
lowvram, so I record those as confounded rather than as evidence. Side finding:
`cfg` above 1 roughly doubles `620:114`'s sampler memory, because `cfg == 1` is a
fast path that skips the uncond pass (`comfy/samplers.py:370`).

**D — the mouth prompt does NOT crash; `#406`'s prompt DOES, and that is an
anomaly I cannot explain.** Crashing string into `621:166` (mouth) →
clean, healthy render, so this is not an encoder problem and the fix stays shaped
around `#106`/`620:114`. `#406` is `622:406 DetailerForEachDebug` (eyes), prompt
`622:398` — and **lengthening `622:398` crashes the graph 3/3 at `622:403`, a node
its change provably cannot reach, with `#106` at the safe placeholder.** `D3`
rules content out: a neutral 169-character string in the shipped idiom crashes
too. **Open, and the most important thing I am leaving.**

**E — ruled out.** `620:648` detached from `620:165.detailer_hook`: still crashes,
same node, same exception, detector trace identical to `A0` step for step. The log
also shows it never had the chance to matter — in the crashing arm the mouth
detector reports `(no detections)`, so the filter is handed no SEGS.

**One thing I published and then retracted:** "VRAM pressure is a second
independent route to the crash". `CTL3` refutes it. See the withdrawal below.

---

## Master grid — every arm, in run order

`modal_frac` is the fraction of the frame taken by its single most common exact
RGB; healthy is ~0.0245 (blown-out window white). `lowvram` is the patch count
from the server log. Blank `modal_frac` on `A1`/`B1`/`B1b` is because the metric
was added mid-session; their values, computed afterwards from the same PNGs, are
**`A1` 0.0245**, **`B1`/`B1b` 0.2350**.

| arm | prompt_id | status | exec | cached | exception node | modal_frac | lowvram |
|---|---|---|---|---|---|---|---|
| `A0_baseline_crash` | `0e24d1c3-cd96-4837-a420-ebbb819207a7` | **error** | 254.8 s | 0 | `622:403` | — | 0 |
| `A1_baseline_clean` | `c75e0d28-1a10-4d84-98e3-f4bf87816d8c` | success | 306.6 s | 0 | — | 0.0245 | 0 |
| `B1_noloras_crashstring` | `35f26d11-e81b-4040-85bc-6a830d4a7ef4` | success | 255.1 s | 0 | — | **0.2350** | 0 |
| `B1b_noloras_crashstring_repeat` | `138e71bb-7394-4914-aca5-a0ffac5010a0` | success | 276.6 s | 0 | — | **0.2350** | 0 |
| `CTL1_clean_after_B1` | `dd4384ec-43f5-4f48-bedc-e2b07999165b` | success | 292.8 s | 0 | — | 0.02448 | 0 |
| `B2_loras_noprefix` | `08878df8-c496-4975-8324-c35bf4888a9e` | success | 289.5 s | 0 | — | 0.02448 | 0 |
| `B2b_loras_noprefix_repeat` | `45294951-c4dc-4d80-b0de-9c6ef7a414c0` | success | 272.6 s | 0 | — | 0.02448 | 0 |
| `D1_mouthprompt_crashstring` | `a5822c60-a273-4073-a8a2-568ac4ab82cb` | success | 293.3 s | 0 | — | 0.02476 | 0 |
| `E1_nohook_crashstring` | `f087c4ca-272b-460f-86f4-327791690376` | **error** | 351.6 s | 0 | `622:403` | — | 0 |
| `D2_eyesprompt_crashstring` | `65e905d5-b1ad-4269-84e9-d4cf4d032253` | **error** | 431.0 s | 0 | `622:403` | — | 83 |
| `CTL2_clean_after_E1_D2` | `22c33f4b-f1ef-45a1-b3c7-62222f6f30b0` | success | 290.9 s | 0 | — | 0.02448 | 0 |
| `D2b_eyesprompt_crashstring_repeat` | `56d4c152-dd47-4697-b538-347ed5298a6a` | **error** | 321.5 s | 0 | `622:403` | — | 0 |
| `C2_cfg2` | `79f3bebe-8ad1-4da0-b7b0-44dcd731ba7e` | **error** | 449.5 s | 0 | `622:403` | — | 0 |
| `C3_cfg5` *(confounded)* | `6959d90a-6f06-4c3c-8f38-e1f12ecd0c8b` | **error** | 496.7 s | 0 | `622:403` | — | **30** |
| `C3b_cfg5_repeat` *(confounded)* | `74a754f8-a40d-406d-a904-58c4a8c85316` | **error** | 292.4 s | 0 | `622:403` | — | **779** |
| `D3_eyesprompt_neutral169` | `c241acf8-4488-4017-af0d-9eda0cf35d32` | **error** | 288.1 s | 0 | `622:403` | — | 85 |
| `CTL3_clean_final` | `45cbb945-04e1-4096-9f4a-8a07c0b9f444` | success | 308.7 s | 0 | — | 0.02448 | 85 |

**Every crash in this table is the same crash**: `622:403 MaskBoundingBox+`,
`RuntimeError: min(): Expected reduction dim to be specified for input.numel() ==
0`, `ComfyUI_essentials/mask.py:184`, mask all-zero. No arm crashed at a different
node, so there is no second bug to report separately. Every arm reported
`execution_cached: []`.

### Cells NOT run

* **`620:114.cfg` at 5 on an unloaded box** — attempted twice, both went lowvram
  because the change itself doubles sampler memory. **Not cleanly measured.**
* **`"luna, "` alone with the LoRAs OFF** — the cell that would show whether the
  trigger prefix destroys the face by itself, without the long description.
  **NOT RUN.**
* **Anything varying the *length* of `620:106` at fixed content**, or the reverse.
  Track A owns that axis; I did not touch it.
* **A tap on `620:114`'s output image** to see the constant fill at source rather
  than after the upscale. **NOT RUN** — it is a graph mutation and the graph is
  frozen for this session.

---

## The baseline — the crash reproduces on 28191, and the clean render is bit-identical to 18188's

| cell | what varied | prompt_id | status | cached | exception node |
|---|---|---|---|---|---|
| `A0_baseline_crash` | nothing — shipping graph, both LoRAs, `#106` = the crashing string | `0e24d1c3-cd96-4837-a420-ebbb819207a7` | **error** 254.8 s | 0 | **`622:403 MaskBoundingBox+`** `RuntimeError` |
| `A1_baseline_clean` | `#106` = shipped placeholder | `c75e0d28-1a10-4d84-98e3-f4bf87816d8c` | success 306.6 s | 0 | — |

`A0`'s exception is Phase 0's, field for field:

```
node_id 622:403  node_type MaskBoundingBox+  RuntimeError
min(): Expected reduction dim to be specified for input.numel() == 0.
custom_nodes/ComfyUI_essentials/mask.py:184   x1 = max(0, x.min().item() - padding)
current_inputs.mask = tensor([[[0., 0., 0., ...]]])   <- all zero
```

The only textual difference from Phase 0's traceback is the install path:
28191 runs out of **`/workspace/comfy-r2gate3`**, not `/workspace/ComfyUI`.
`ComfyUI_essentials/mask.py` is byte-identical between the two
(`sha256 ec8ca8d3fb3614f529b9fdfbb4f511f3a72d3207bc21ff7c54e422b887749af0`), so
it is the same crash site in the same code.

**The two servers agree bit for bit on this graph.** `A1`'s image against the
18188 render of the same api_graph (`results/r4/R4_CF15_placeholder/HasMetadata_00059_.png`):

```
max_abs_diff 0    mean_abs_diff 0.0    mse 0.0    psnr inf     over 2688x3456x3
```

That is stronger than the brief assumed was available. It does not license
mixing 18188 numbers into my tables — timings still are not comparable and I
have not tested a second graph — but for *this* graph the render is reproduced
exactly, so my baseline is anchored to the same artifact the existing evidence
came from.

**Health metric.** Mine is a fresh implementation and its numbers are **not** on
the same scale as the R4 session's. On the byte-identical image above, R4
reported `flat_frac 0.0030 / luma_sd 37.38` and mine reports
`flat_frac 0.03088 / luma_sd 59.505`. Only compare my numbers to my own healthy
reference, which is that pair. `flat_frac` = fraction of pixels with zero
luma gradient to both neighbours; `luma_sd` = sd of luma over the whole frame;
`suspect_poisoned` = `flat_frac > 0.20 or luma_sd < 8`.

---

## The detector trace — what the server log shows, per run

The log (28191's stdout) prints every Ultralytics detection. That is the only
place the *detector* outcomes are visible; `/history` records the exception but
not "found nothing here, found a face there". Sliced per prompt by
`results/crash/B/logslice.py`. The five detections in run order are:

| # | node | what it detects |
|---|---|---|
| 1 | `619:607 FaceDetailerPipe` | SDXL-side face |
| 2 | `587:92 HandDetailer` | hand |
| 3 | **`620:114 FaceDetailer`** | the face pass — the one `#106` conditions |
| 4 | `620:165 FaceDetailer` | lips, the mouth pass |
| 5 | **`622:424 BboxDetectorSEGS`** | `face_yolov8m.pt` @ 0.6 — **the one that crashes when it finds nothing** |

Identification is from the guide_size in the `Detailer: segment upscale` line
that follows each detection (1024/1280/1808/1920 are unique per node) plus the
crop factor, cross-checked against a run where every stage fired.

| run | arm | 1 face | 2 hand | 3 **face pass** | 4 lips | 5 **eyes-stage face** | end |
|---|---|---|---|---|---|---|---|
| #1 | `A0_baseline_crash` | 1 face | none | 1 face | **none** | **NONE** | crash `622:403` |
| #2 | `A1_baseline_clean` | 1 face | none | 1 face | 1 lips | 1 face | 5x `SEGS: 1`, eyes ran, success |
| #3 | `B1_noloras` | 1 face | none | 1 face | **none** | 1 face | `[mask_to_segs] Empty mask` / `SEGS: 0` — eyes **skipped**, success |
| #4 | `B1b` repeat | identical to #3 | | | | | identical |

---

## Grid

| cell | what varied vs the crashing configuration | prompt_id | status | cached | exception node |
|---|---|---|---|---|---|
| `B1_noloras_crashstring` | `116.lora_01` and `618.lora_01` -> `None` | `35f26d11-e81b-4040-85bc-6a830d4a7ef4` | success 255.1 s | 0 | — (**but see below**) |
| `B1b_..._repeat` | same, repeat | `138e71bb-7394-4914-aca5-a0ffac5010a0` | success 276.6 s | 0 | — |
| `CTL1_clean_after_B1` | health control, = `A1` | *(see below)* | | | |


### B — the LoRAs are load-bearing **for the crash**, and not for the failure underneath it

`B1` differs from `A0_baseline_crash` in **two widget values and nothing else**
(`116.inputs.lora_01` and `618.inputs.lora_01`, both `-> "None"`). Same prompt,
same seed, same everything downstream. It did **not** crash. Run twice, and the
two images are **bit-identical** (`max_abs_diff 0` over 2688x3456x3), so this is
a deterministic path, not a coin flip.

**But `status: success` is not a render here, and this is the part that matters.**

```
                      flat_frac   luma_sd   luma_min   modal RGB      modal_frac
A1 clean baseline      0.0309      59.51      4.67     (255,255,255)   0.0245
B1 / B1b no-LoRAs      0.2557      66.59     48.34     ( 53, 47, 43)   0.2350
```

**23.5 % of the frame is one exact RGB value, (53,47,43).** A 20x20 patch at the
face centre has standard deviation **0.0** — it is a perfectly constant fill, and
the whole-image luma minimum *is* that fill, so nothing in the frame is darker
than it. The healthy render's modal colour is blown-out window white at 2.45 %.
The face is not damaged, it is **gone and replaced by a solid colour**.
`results/crash/B/EVIDENCE_B_loras.png` is the side-by-side — I am not judging the
image, I am reporting that one is a photograph and one has a flat void where a
face goes.

The log says the same thing detector by detector. In `B1` the face pass (#3) ran,
the mouth detector (#4) then found **no lips**, the eyes-stage detector (#5)
found "1 face" — enough for `MaskBoundingBox+` to survive — and then MediaPipe
FaceMesh found no landmarks, `[mask_to_segs] Empty mask`, `# of Detected SEGS: 0`,
so the eyes pass was skipped and the run *completed*.

So the sequence in both arms is the same, and the LoRAs only move where it stops:

```
crash string in #106  ->  620:114 destroys the face
                          |
   LoRAs loaded  -------->  face_yolov8m finds NOTHING  -> empty SEGS
                          -> all-zero mask -> 622:403 .min() on empty -> CRASH
                          |
   LoRAs None    -------->  face_yolov8m still finds a box round the blob
                          -> MediaPipe finds no landmarks -> eyes pass skipped
                          -> renders to completion and SHIPS the flat face
```

**Verdict B: the LoRAs ARE load-bearing for the crash — `B1_noloras_crashstring`
is the arm that shows it, single-variable against `A0_baseline_crash`, 2/2
bit-identical. They are NOT load-bearing for the underlying defect: with the
LoRAs off the same prompt still destroys the face, and the pipeline then returns
`success` with a quarter of the frame a constant colour. Turning the LoRAs off is
not a workaround; it converts a loud failure into a silent one.**

**Health control after B1/B1b.** `CTL1_clean_after_B1`, prompt
`dd4384ec-43f5-4f48-bedc-e2b07999165b`, success 292.8 s, cached 0, and
**bit-identical to `A1_baseline_clean`** (`max_abs_diff 0`). So the constant fill
in `B1` is not the server going bad — the server produced the reference render
again immediately afterwards. `B1` is a real result.

### B, third cell — and it flips the standing bet: the `luna, ` prefix **is** load-bearing

| cell | what varied vs `A0_baseline_crash` | prompt_id | status | cached | exception node |
|---|---|---|---|---|---|
| `B2_loras_noprefix` | `620:106.text` — the `luna, ` prefix removed, LoRAs left **loaded** | `08878df8-c496-4975-8324-c35bf4888a9e` | **success** 289.5 s | 0 | — |
| `B2b_..._repeat` | same, repeat | `45294951-c4dc-4d80-b0de-9c6ef7a414c0` | **success** 272.6 s | 0 | — |

Graph diff against `A0_baseline_crash`: **exactly one difference**, `620:106.text`,
and it is the six characters `luna, ` at the front — `A0 == "luna, " + B2`,
169 chars vs 163. Nothing else in 88 nodes differs.

**And unlike `B1`, this one is a genuinely healthy render.**

```
                      flat_frac   luma_sd   modal RGB      modal_frac
A1 clean baseline      0.0309      59.51    (255,255,255)   0.0245
B2 / B2b no prefix     0.0305      59.51    (255,255,255)   0.0245     <- healthy
B1 / B1b no LoRAs      0.2557      66.59    ( 53, 47, 43)   0.2350     <- constant fill
```

Every detector fired in `B2`: face pass, **`1 lips`** (crop 1855x803 = 1.49 M, under
`#648`'s 1.7 M ceiling, so the mouth pass ran), eyes-stage face, 5x `SEGS: 1`,
eyes detailer. It is not the baseline image — `psnr 44.54`, `max_abs_diff 140`
against `A1` — it is a different, complete render. `B2` and `B2b` are
bit-identical to each other.

**This contradicts `notes/R4-defects.md` §2b's bet** ("the LoRAs are load-bearing
and the `luna, ` prefix is not — 2 in 3"). Ran twice per rule 6 because it flipped
against expectation. **Both halves of that bet are wrong in the same run:** the
LoRAs are load-bearing (B1), *and so is the prefix* (B2).

### The complete picture for B

Everything with `#106` = the long description unless stated. Rows marked `[18188]`
are prior sessions' and are quoted for context only — nothing in my verdicts rests
on them.

| `#106` | LoRAs | crash? | image |
|---|---|---|---|
| shipped placeholder | on | no | healthy — `A1`, `CTL1`, bit-identical ×2 |
| `"luna, "` alone `[18188]` | on | no | not re-measured here |
| `"a woman's face"` `[18188]` | on | no | not re-measured here |
| **`luna, ` + long description** | **on** | **CRASH `622:403`** | no image — `A0` |
| **long description, no prefix** | **on** | **no** | **healthy** — `B2`/`B2b` |
| **`luna, ` + long description** | **off** | **no** | **face is a 23.5 % constant fill** — `B1`/`B1b` |
| long description, no prefix `[18188]` | off | no | not re-measured here |

Read down the last three rows: **the crash needs the trigger word AND the long
description AND the LoRAs together.** Drop any one of the three and it does not
crash. But only dropping the *prefix* gives you a good image back; dropping the
*LoRAs* leaves the face destroyed and merely stops the exception being raised.

**[I] Inference, not measurement:** the thing that destroys the face tracks the
`luna, ` prefix, not the LoRAs — `B1` has the prefix, no LoRAs, and a destroyed
face; `B2` has the LoRAs, no prefix, and a good one. The LoRAs then decide whether
the destruction is total enough that `face_yolov8m.pt` loses it and `622:403`
raises. I have not tested `"luna, "` alone with the LoRAs *off*, so I cannot say
the prefix does this by itself, without the long description.

---

## D — the crashing string in the **mouth** prompt does not crash

| cell | what varied vs `A1_baseline_clean` | prompt_id | status | cached | exception node |
|---|---|---|---|---|---|
| `D1_mouthprompt_crashstring` | `621:166.text` `"realistic detailed mouth"` -> the crashing string. `620:106` left at the placeholder | `a5822c60-a273-4073-a8a2-568ac4ab82cb` | **success** 293.3 s | 0 | — |

Healthy: `flat_frac 0.0418`, `luma_sd 59.50`, modal colour `(253,253,252)` at
**2.48 %** of frame — no fill. Every detector fired, including `1 lips`
(crop 1844x803, byte-identical centre to `A1`'s, because with `#106` at the
placeholder the face pass output is the same). It is a real, different render:
`psnr 24.91` / `max_abs_diff 215` against `A1`, which is where the mouth changed.

`621:166` and `620:106` are both `CLIPTextEncode` on the **same** lumina2 encoder
`620:110`, and both detailers run at **cfg 1**. The same 169-character string
through the same encoder is harmless on the mouth pass and fatal on the face
pass. **So this is not a conditioning-shape or encoder problem** — which was
hypothesis 2 in `notes/CRASH.md`. The two passes still differ in denoise
(0.80 face vs 0.35 mouth) and in guide_size, so this weakens hypothesis 2 rather
than killing it outright, but the encoder itself produces a usable conditioning
from this string.

**Verdict D (mouth): it does NOT crash. This stays a `#106` / `620:114` problem
and the shape of the fix is unchanged.**

### What "#406" is

`#406` is **`622:406 DetailerForEachDebug`** — the **eyes** detailer in the Eyes
stage, guide_size 1920, seed 1111112, steps 8, cfg 1, denoise 0.42, sampler
`euler` / `beta`. Prior sessions already use that name for that node
(`notes/P3-cfg.md` §"eyes `#406`", `AUDIT.md` line 298). Its positive
conditioning is **`622:398 CLIPTextEncode` "Eye Positive Prompt"**
(`"perfect eyes, round pupils, round iris, symmetrical eyes, realistic eyes,
perfect circles, round"`) on the same lumina2 clip `620:110`, cfg 1 — so yes, it
is a text encode on the same encoder and it was tested.

**But `622:406` is *downstream* of `622:403`** — reachability walked from the
submitted graph: `622:403` is in `622:406`'s dependency set, not the other way
round. It therefore **cannot** produce the `622:403` crash; the crash would
already have happened. The cell tests whether the string does something else
there. Result below.

---

## E — the mouth SEGS size guard is **ruled out**

| cell | what varied vs `A0_baseline_crash` | prompt_id | status | cached | exception node |
|---|---|---|---|---|---|
| `E1_nohook_crashstring` | `620:165.detailer_hook` — the link from `620:648` removed | `f087c4ca-272b-460f-86f4-327791690376` | **error** 351.6 s | 0 | **`622:403 MaskBoundingBox+`** `RuntimeError` |

Graph diff against `A0`: **one difference**, the removed `detailer_hook` input.
Same node, same exception message, same all-zero mask. The detector trace is
identical to `A0`'s step for step:

```
A0:  1 face | (none) | 1 face | (none) mouth | (NONE) eyes-stage  -> crash
E1:  1 face | (none) | 1 face | (none) mouth | (NONE) eyes-stage  -> crash
```

**Verdict E: ruled out.** And the log says why it could never have been the cause
in this configuration: in the crashing arm the mouth detector prints
`(no detections)`, so `620:648` is handed **no SEGS to filter** and never
influences anything. It can make the mouth pass a no-op when a mouth *is* found
and is too big — `HANDOFF.md` §6.2's defect, which is real and separate — but it
is not on the path to this crash.

*(Timing note: 351.6 s here vs 254.8 s for the same crash in `A0`. The GPU is
shared — `nvidia-smi` shows the 18188 server holding 24 GB and a third process
20 GB, with the card at 60 % while my queue was empty. **No timing in this
document should be treated as a measurement.** Crash/no-crash and the image
metrics are unaffected.)*

---

## ~~A SECOND, INDEPENDENT ROUTE TO THE SAME CRASH: VRAM pressure~~ — **WITHDRAWN**

> **I published this and then a later control refuted it. Read the withdrawal at
> the end of this section before using anything in it.** The *data* below is
> good; the *conclusion* I drew from it was wrong, and it was wrong in the exact
> way this project keeps going wrong — one correlation, no control that varied
> the thing I was blaming. It is left standing rather than deleted so the
> correction is visible.

`D2_eyesprompt_crashstring` changed **one** input, `622:398.text` — and `622:398`
feeds only `622:406`, which is **downstream** of `622:403` (reachability walked on
the submitted graph: 69 nodes are upstream of `622:403` and neither `622:398` nor
`622:406` is among them). `620:106` was at the shipped placeholder, the
configuration that renders clean. The change is therefore **provably incapable**
of affecting `622:403`.

**It crashed at `622:403` anyway.** Same node, same exception, same all-zero mask.

The server log says why, and it is not poisoning:

```
run #10 (D2)   Requested to load Lumina2   loaded completely; 26408 MB usable
               Unloaded partially: 4183.29 MB freed, 7556.27 MB remains loaded,
                                   393.75 MB buffer reserved,  lowvram patches: 83
               Unloaded partially: 159.87 MB freed, ...
```

Per-run VRAM pressure across everything I ran (`logslice.vram_table()`):

| run | arm | min "usable" MB | lowvram patches | partial unloads | outcome |
|---|---|---|---|---|---|
| #1 | `A0` crash | 33296 | 0 | 0 | CRASH (prompt) |
| #2 | `A1` clean | 22094 | 0 | 0 | ok |
| #3–#4 | `B1`,`B1b` | 34810 / 33961 | 0 | 0 | ok |
| #5 | `CTL1` | 34478 | 0 | 0 | ok |
| #6–#7 | `B2`,`B2b` | 34478 / 26766 | 0 | 0 | ok |
| #8 | `D1` mouth | 21027 | 0 | 0 | ok |
| #9 | `E1` nohook | 25199 | 0 | 0 | CRASH (prompt) |
| **#10** | **`D2` eyes** | **12296** | **83** | **2** | **CRASH (VRAM)** |
| #11 | `CTL2` | 13498 | 0 | 0 | ok, **bit-identical to `A1`** |

Every arm above `D2` ran with the model fully resident and no patching. `D2` is
the only run in the session that went lowvram, and it is the only crash that
cannot be explained by its own change.

**The server was not poisoned.** `CTL2_clean_after_E1_D2`, a byte-identical
repeat of `A1`, ran immediately after `D2` and came back **`max_abs_diff 0`**
against `A1`. So this is not `HANDOFF.md` §7.1's NaN mode — it is a distinct
third mechanism.

### The withdrawal — `CTL3` killed it

I concluded from the table above that the lowvram path changes the face pass's
numerics and so is an independent cause of the crash. **That is refuted.**

`CTL3_clean_final` — the byte-identical repeat of `A1` — ran with
**85 lowvram patches** at 11 824 MB usable, the same patch count as `D3` which
crashed, and it produced an image that is **`max_abs_diff 0` against `A1`**.

```
run #16  D3    85 lowvram patches, 14808 MB usable   -> CRASH 622:403
run #17  CTL3  85 lowvram patches, 11824 MB usable   -> success, BIT-IDENTICAL to A1
```

So lowvram patching does **not** change this graph's output. The `A1` graph is
bit-identical **4/4** (`A1`, `CTL1`, `CTL2`, `CTL3`) across 22 GB → 11.8 GB usable
and 0 → 85 lowvram patches. Memory pressure is not a cause of anything here.

**What survives:** the *observation* that `D2` (run #10) went lowvram is true and
the per-run table is accurate and worth keeping — check it for any arm. Two arms
of mine are genuinely unusable for a different reason and are marked so in the
grid (`C3`, `C3b`, where the cfg change itself doubles sampler memory). **What
does not survive:** "VRAM pressure is an independent route to the crash" and "a
buyer on a smaller card can hit this with a good prompt". I retract both. I had
one lowvram run that crashed and no control in which lowvram happened *without*
the crash — `CTL3` is that control and it says the opposite.

I would not have caught either the finding or its refutation from `/history`.
Both are only visible in the server's stdout, which is why
`results/crash/B/logslice.py` exists.

---

## D, the `#406` half — **and this one I cannot explain, so I am reporting it as an anomaly, not a result**

| cell | what varied vs `A1_baseline_clean` | prompt_id | status | cached | exception node |
|---|---|---|---|---|---|
| `D2_eyesprompt_crashstring` | `622:398.text` (Eye Positive Prompt) -> the crashing string | `65e905d5-b1ad-4269-84e9-d4cf4d032253` | **error** 431.0 s | 0 | `622:403 MaskBoundingBox+` |
| `D2b_..._repeat` | same, repeat | `56d4c152-dd47-4697-b538-347ed5298a6a` | **error** 321.5 s | 0 | `622:403 MaskBoundingBox+` |

One input differs from `A1`. `620:106` is at the shipped placeholder in both.

**`622:398` cannot reach `622:403` through the graph.** Its only consumer is
`622:406`, and `622:403` is in `622:406`'s dependency set, not the reverse. 69
nodes are upstream of `622:403` and neither `622:398` nor `622:406` is one of
them. So there is no data path by which this change can affect the node that
crashed.

**And yet it is causal by the alternation test** — the same design `R4-defects.md`
§2b used to settle `#106`, run on a server whose health is attested at both ends:

```
#10  D2   ERROR 622:403
#11  CTL2 SUCCESS  -- byte-identical repeat of A1, max_abs_diff 0 vs A1
#12  D2b  ERROR 622:403
```

`A1`'s graph is clean **3/3 and bit-identical every time** (runs #2, #5, #11).
`D2`'s graph is crash **2/2**. Interleaved. One input apart, and that input is
downstream of the crash.

**What the log shows.** In both `CTL2` and `D2b` the face pass gets an *identical*
detection — `1 face`, crop `(2010, 2859)`, centre `(1340.1992, 1906.2034)`, the
same numbers to seven digits. So the face pass's **inputs** were the same. Its
**output** was not: `CTL2` then finds `1 lips` and `1 face`; `D2b` finds
`(no detections)` twice and dies.

The only other thing that differs is memory management. `CTL2` fully evicts the
Z-Image text encoder once (`7672.25 MB freed, 0.00 MB remains loaded`); `D2b`
does two *partial* evictions (`90.37 MB freed, 7581.88 MB remains loaded` and
`437.43 MB freed, 1123.37 MB remains loaded`). Neither used lowvram patches. So
my `lowvram` explanation for `D2` does **not** cover `D2b`, and I withdraw it as
the general explanation while keeping it as the explanation for run #10
specifically.

**[I] The only mechanism I can construct** — and it is inference, I have not
demonstrated it — is that the lumina2 text encodes all run **up front** (the very
first load in every run is `ZImageTEModel_`), so a longer string in `622:398`
changes the resident footprint before the face pass, changes the eviction
decisions, and changes the face pass numerics enough for the detectors to lose
the face. That would mean **the face pass is not numerically stable against
memory-management decisions**, which is a far more serious defect than a bad
prompt, and would also explain the VRAM-pressure crash above.

**Verdict D: the mouth prompt does NOT crash (`D1`, clean and healthy). `#406` is
`622:406`, the eyes detailer, prompt `622:398` — putting the crashing string
there DOES crash, 2/2, at `622:403`, which its own change cannot reach. I am
NOT claiming the eyes prompt causes this crash; I am reporting a reproducible
result I cannot account for, and the next arm below is the one that separates
"this specific string" from "any perturbation".**

---

## C — raising `cfg` on `620:114` does **not** rescue the crash

The control for this cell is `A0_baseline_crash`, which **is** `cfg 1` — the
shipping value, unchanged from `OFMTech_NSFW.json`. (Terminology confirmed: the
"3 vs 1.5" figures elsewhere are `bbox_crop_factor`; `620:114.cfg` is `1` in the
file and in every arm here that did not deliberately change it.)

| cell | `620:114.cfg` | prompt_id | status | cached | exception node | lowvram patches |
|---|---|---|---|---|---|---|
| `A0_baseline_crash` *(control, = shipping)* | 1 | `0e24d1c3-…` | **error** 254.8 s | 0 | `622:403` | 0 |
| `C2_cfg2` | 2 | `79f3bebe-8ad1-4da0-b7b0-44dcd731ba7e` | **error** 449.5 s | 0 | `622:403` | **0 — clean measurement** |
| `C3_cfg5` | 5 | `6959d90a-6f06-4c3c-8f38-e1f12ecd0c8b` | **error** 496.7 s | 0 | `622:403` | **30 — confounded** |
| `C3b_cfg5_repeat` | 5 | `74a754f8-a40d-406d-a904-58c4a8c85316` | **error** 292.4 s | 0 | `622:403` | **779 — confounded** |

`C2`'s detector trace is identical to `A0`'s step for step, and its mask is
all-zero. **cfg 2 does not rescue it, and that is a clean measurement.**

**cfg 5 could not be measured cleanly on this box, and the reason is the change
itself, not the neighbours.** `comfy/samplers.py:370`:

```python
if math.isclose(cond_scale, 1.0) and model_options.get("disable_cfg1_optimization", False) == False:
```

At **exactly** `cfg 1` ComfyUI skips the unconditional pass entirely. Raising cfg
above 1 makes the face pass evaluate **two** conditionings per step instead of
one, roughly doubling sampler activation memory. Both cfg-5 attempts went
lowvram — 30 patches at 4962 MB usable, then 779 patches at **194 MB** usable —
where every cfg-1 and cfg-2 arm ran fully resident. So the cfg-5 arms crashed,
but they crashed under exactly the memory condition shown above to be an
independent cause, and I will not count them as evidence about cfg.

**Verdict C: raising cfg does not rescue the crash. cfg 2 crashes identically to
cfg 1, measured cleanly. cfg 5 crashed twice but both runs went lowvram, so it is
"crashed, confounded" and not a clean result — and the useful finding from those
two arms is a different one: raising cfg above 1 on `620:114` doubles that pass's
sampler memory, because cfg exactly 1 is a fast path that skips the uncond.**

---

## The `622:398` anomaly, restated after the withdrawal — **this is the open item**

With the VRAM explanation gone, the `D2` result is sharper, not weaker.

| cell | `622:398.text` | length | prompt_id | status | cached | exception node |
|---|---|---|---|---|---|---|
| `A1` / `CTL1` / `CTL2` / `CTL3` | shipped eye prompt | 96 | four ids in the grid | **success ×4, all bit-identical** | 0 | — |
| `D2_eyesprompt_crashstring` | the crashing string | 169 | `65e905d5-…` | **error** | 0 | `622:403` |
| `D2b_..._repeat` | the crashing string | 169 | `56d4c152-…` | **error** | 0 | `622:403` |
| `D3_eyesprompt_neutral169` | **neutral** string, shipped idiom | **169** | `c241acf8-4488-4017-af0d-9eda0cf35d32` | **error** | 0 | `622:403` |

**Clean 4/4 with a 96-character eye prompt. Crash 3/3 with a 169-character one.
`620:106` is at the safe placeholder in all seven. The only input that differs is
`622:398.text`, whose sole consumer is `622:406`, which is downstream of the node
that crashes.**

`D3` is the arm that separates content from length: its 169 characters are
`"perfect eyes, round pupils, … crisp, detailed"` — the shipped prompt's own
idiom, none of the crashing string's words, no `luna`, no freckles. It crashes
just the same. **So it is not the content of the eyes prompt. It tracks its
length.**

Verified, so nobody re-derives it:

* `622:398` is referenced exactly **once** in the whole 88-node API graph, by
  `622:406`. No dict-valued inputs, no non-`[str,int]` link forms anywhere.
* `622:403` is in `622:406`'s dependency closure, not the reverse. 69 nodes are
  upstream of `622:403`; `622:398` and `622:406` are not among them.
* ComfyUI's execution order is **value-independent** —
  `comfy_execution/graph.py:270 ux_friendly_pick_node` branches only on
  `class_type`, `OUTPUT_NODE`, `is_async` and the `blocking` structure, falling
  back to `node_list[0]`. Changing a widget string cannot reorder execution.
* The face pass gets an **identical** detection box in the clean and crashing
  arms — `1 face`, crop `(2010, 2859)`, centre `(1340.1992, 1906.2034)` — so its
  *inputs* are the same. Its *output* is not: the clean arms then find `1 lips`
  and `1 face`, the crashing arms find `(no detections)` twice.

**I cannot account for this and I am not going to invent a mechanism.** The one
thing a longer `622:398` demonstrably does is make the lumina2 text encoder
produce a longer conditioning tensor, early — the first model loaded in every run
is `ZImageTEModel_` — which then sits resident while the face pass runs. Whether
that is enough to change a kernel choice or a reduction order in `620:114` I do
not know, and `A1`'s 4/4 bit-identity across a 10 GB swing in free VRAM argues
against it.

**What it means practically.** Something makes `620:114`'s output depend on state
that is not in its inputs, and the eyes-stage detector sits close enough to its
threshold that the difference flips a crash. That is a bigger problem than the
prompt: it means **the crash is not fully determined by the graph**, and any fix
validated only against `#106` may leave it live.

**Verdict D (`#406`): `#406` is `622:406 DetailerForEachDebug`, the eyes detailer;
its prompt is `622:398`. Lengthening `622:398` crashes the graph 3/3 at
`622:403` — a node it cannot reach — with `#106` safe. Content is ruled out by
`D3`. Mechanism unknown. This is the highest-value open item I am leaving.**
