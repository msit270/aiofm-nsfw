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

*(filled in as cells complete; a cell not listed in the grid below was NOT RUN)*

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
