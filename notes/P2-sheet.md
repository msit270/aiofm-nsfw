# P2-SHEET — the contact sheet builder

**Tool:** `/workspace/nsfw-fix/tools/contact_sheet.py`
**Proof sheets:** `/workspace/nsfw-fix/results/face/proof_face_sheet1of1.png`,
`/workspace/nsfw-fix/results/face/proof_skin_sheet1of1.png`
**Judgement calls:** `notes/P2-sheet-questions.md`

The tool is built and proven against the four existing WS4 images. It reads
`results/face/arms/` and will build the real sheets the moment P2-RENDER's arms
land, with no further work.

No renders, no GPU, no graph edits were involved. Nothing was written under
`results/face/arms/`.

---

## How to re-run it

Once arms are present under `results/face/arms/`:

```
cd /workspace/nsfw-fix
python3 tools/contact_sheet.py --arms-dir results/face/arms --out-dir results/face --prefix face
```

That writes `results/face/face_face_sheet1of1.png`,
`results/face/face_skin_sheet1of1.png` and `results/face/face_manifest.json`,
and prints a PASS/FAIL for the width limit and for the 1:1 pixel check on every
tile. **Exit code is 0 only if every check passed.** It is safe to re-run as
each arm lands; arms with no PNG yet are skipped with a `[skip]` line.

Right now, against the live directory:

```
$ python3 tools/contact_sheet.py --arms-dir results/face/arms --out-dir results/face --prefix face
  [skip] A0_baseline: no PNG yet (api_graph.json)
no arms found (looked in /workspace/nsfw-fix/results/face/arms). Expected <dir>/<arm_name>/{*.png,meta.json}.
exit=1
```

For the **final** deliverable, pin the crop so re-runs are byte-comparable
(see judgement call 6):

```
python3 tools/contact_sheet.py --arms-dir results/face/arms --out-dir results/face \
    --prefix face --face-box 919,327,774,1050 --skin-box 959,847,400,400
```

Useful flags: `--max-width` (default 4000), `--max-rows` (default 4, splits into
numbered sheets), `--skin-size` (default 400), `--skin-anchor face|image`,
`--pad-frac` (default 0.08), `--move-tol` (default 0.25), `--no-detect`,
`--note 'banner text'`.

---

## The proof sheet, and how it was checked

Command (this is the exact one that produced the committed sheets):

```
python3 tools/contact_sheet.py \
  --arm 'A_baseline|shipped graph, no change|results/ws4/A_baseline/HasMetadata_00001_.png' \
  --arm 'B_no_vae_roundtrip|#597->#616 VAE round-trip removed|results/ws4/B_no_vae_roundtrip/HasMetadata_00005_.png' \
  --arm 'C_no_sdxl_face_pass|#607 FaceDetailerPipe (SDXL, denoise 0.45) deleted|results/ws4/C_no_sdxl_face_pass/HasMetadata_00006_.png' \
  --arm 'D_skinblend_050|ImageBlend skin filter blend 0.50|results/ws4/D_skinblend_050/HasMetadata_00011_.png' \
  --out-dir results/face --prefix proof \
  --note 'TOOLING TEST -- proves the sheet builder, NOT the face deliverable. Arms are WS4 graph ablations, not P2-RENDER face arms.'
```

Output:

```
[arms] 4 from explicit --arm list
  A_baseline                   2688x3456  detected       conf=0.8846  (984,413)-(1638,1304)  [BASELINE]
  B_no_vae_roundtrip           2688x3456  detected       conf=0.8876  (975,412)-(1638,1302)
  C_no_sdxl_face_pass          2688x3456  detected       conf=0.8929  (972,400)-(1630,1305)
  D_skinblend_050              2688x3456  detected       conf=0.8892  (974,403)-(1639,1303)
[face] face box from 4 detection(s): union (972,400)-(1639,1305) = 667x905, +8% pad per axis -> 774x1050 at (919,327)
[skin] (959, 847, 400, 400) skin_frac=0.9503 blur_grad=0.6656 anchor=face (chosen on 'A_baseline', applied identically to every arm)
[face] wrote results/face/proof_face_sheet1of1.png  3190x1442  cols=4 rows=1  width<= 4000: PASS
[face] 1:1 pixel verification: 4/4 tiles byte-identical to source crop -- PASS
[skin] wrote results/face/proof_skin_sheet1of1.png  1694x774  cols=4 rows=1  width<= 4000: PASS
[skin] 1:1 pixel verification: 4/4 tiles byte-identical to source crop -- PASS
[done] manifest results/face/proof_manifest.json
[done] ALL CHECKS PASS
```

**The sheet is labelled as a tooling test on its face** — the red banner reads
`TOOLING TEST -- proves the sheet builder, NOT the face deliverable. Arms are
WS4 graph ablations, not P2-RENDER face arms.` These four images are WS4's graph
ablations; they are the right *shape* to develop against and nothing more.

### I checked it four ways

**1. Crops are on the face.** I opened both sheets. The face tiles are forehead
to chin, and the skin tiles are cheek. The detector agrees: all four arms return
one face each at conf 0.88–0.89, within 13 px of each other on every edge.

**2. Pixels are 1:1 — verified numerically, twice, by two different methods.**

The tool's own check (`verify_sheet`) re-opens the written PNG and asserts
`np.array_equal` between each tile region and the source crop. 4/4 and 4/4 above.

Because that check uses coordinates the tool itself recorded, I wrote a second
check that shares no code with it and takes no coordinate on trust. It picks a
12-pixel run from the middle row of each source crop, finds every position in
the sheet where that run occurs exactly, and at each candidate tests the full
tile for exact equality — so the location is *derived from the pixels*, not
read from the manifest:

```
=== face  sheet 3190x1442
  A_baseline             src[919,327,774,1050] -> exact 774x1050 match(es) in sheet at [(20, 372)]  claimed (20, 372)  OK
    control: 1px-shifted compare must FAIL -> FAIL(good)
    control: down/up-resampled compare must FAIL -> FAIL(good)
  B_no_vae_roundtrip     src[919,327,774,1050] -> exact 774x1050 match(es) in sheet at [(812, 372)]  claimed (812, 372)  OK
  C_no_sdxl_face_pass    src[919,327,774,1050] -> exact 774x1050 match(es) in sheet at [(1604, 372)]  claimed (1604, 372)  OK
  D_skinblend_050        src[919,327,774,1050] -> exact 774x1050 match(es) in sheet at [(2396, 372)]  claimed (2396, 372)  OK

=== skin  sheet 1694x774
  A_baseline             src[959,847,400,400] -> exact 400x400 match(es) in sheet at [(20, 354)]  claimed (20, 354)  OK
    control: 1px-shifted compare must FAIL -> FAIL(good)
    control: down/up-resampled compare must FAIL -> FAIL(good)
  ... all four OK
INDEPENDENT RESULT: PASS
```

The two controls matter: they prove the test can fail. Comparing the tile
against the source shifted by one pixel fails, and comparing it against a
down-then-up resampled copy of the same crop fails. So exact equality at the
claimed offset is not something that happens by accident — a 774x1050 region of
this image matches in exactly one place, and it is the right one.

**3. Labels are legible and correct.** Checked by cropping the label strips at
1:1 and reading them. Each tile carries arm name, the parameter that changed,
and a crop line naming the region, the crop mode, the detector confidence and
the exact box. An early version was wrong here and it is worth recording: the
skin sheet's tiles were printing the *face* box on the crop line. Fixed — the
skin tiles now read `skin crop: common, conf 0.89, 1:1 [959,847,400,400]`.

**4. Width is under 4000.** Face sheet 3190, skin sheet 1694. The tool asserts
this every run and refuses rather than scale.

---

## The crop-size decision

This is the part the brief called the whole job, so here is the reasoning in
full.

**The constraint is width only.** "Under 4000px wide" says nothing about height,
so tile height is free and tile width is the only thing to trade. That is why
the face crop is *not* forced square.

**The face is not square.** Detector output on `A_baseline` is
`(984.3, 413.0, 1638.5, 1303.7)` — **654 x 891**, aspect 0.73. The brief's
`732 x 732` is a square that clips the chin and takes in hair. Cropping to the
detector's shape keeps more face per pixel of width, which is exactly the
currency being spent.

**Sizing.** Union of the four detections is `(972,400)-(1639,1305)` = 667x905.
Padded 8 % per axis: **774 x 1050**.

**Column count falls out of that:**

```
cols = (4000 - 2*20 + 18) // (774 + 18) = 3978 // 792 = 5
sheet width = 40 + 5*774 + 4*18 = 3982   (under 4000, PASS)
```

So **5 tiles per row at 774 px**, which is what the brief anticipated at 700 px.
With P2-RENDER's 12 arms that is 3 rows on a single 3982 x 3871 sheet — verified
by a full rehearsal against all 12 arm names and their exact `meta.json` schema:

```
[face] wrote .../rehearse_face_sheet1of1.png  3982x3871  cols=5 rows=3  width<= 4000: PASS
[face] 1:1 pixel verification: 12/12 tiles byte-identical to source crop -- PASS
[skin] wrote .../rehearse_skin_sheet1of1.png  3784x1298  cols=9 rows=2  width<= 4000: PASS
[skin] 1:1 pixel verification: 12/12 tiles byte-identical to source crop -- PASS
```

**Note it adapts.** Nothing above is hardcoded. If a later arm's face is bigger,
the union grows, the tile grows, and the column count drops to 4 — the sheet
gets taller, never blurrier. Confirmed by forcing it: `--max-width 1800` gave
`1606x5204 cols=2 rows=4`, still 8/8 byte-identical.

**Multi-sheet.** If arms exceed `cols * --max-rows`, numbered sheets are emitted
with the baseline repeated top-left on each. Forced with `--max-rows 1`:
`split_face_sheet1of2.png` (5 tiles) and `split_face_sheet2of2.png` (4 tiles),
and I confirmed by reading sheet 2 that its top-left tile is
`BASELINE - baseline`.

---

## How face detection behaves

Detector is `/workspace/ComfyUI/models/ultralytics/bbox/face_yolov8m.pt` — the
same checkpoint `#607 FaceDetailerPipe` and `#114 FaceDetailer` use, per
`notes/WS4-report.md:236` and `results/face/ARMS.md`. `ultralytics 8.4.115`,
`torch 2.9.1+cu128`, PIL 12.1.0, numpy 2.4.0.

On the four real images it is boring, which is the good outcome: one face each,
conf 0.8846 / 0.8876 / 0.8929 / 0.8892, every edge within 13 px across arms. It
runs on CPU here in a few seconds per image.

**It is not allowed to be a dependency that breaks the sheet.** Every failure
path was exercised against synthetic arms and every one is loud on the tile —
red gutter, red border, red chip:

| I fed it | what it did |
|---|---|
| a flat grey image with no face | `FACE DETECTION FOUND NO FACE` + `CROP NOT VERIFIED ON THIS IMAGE (no-face) -- using the common box from the other arms` |
| a frame rolled 260 px x / 300 px y | detected at 393 px from the anchor against a 223 px tolerance → own crop box + `FACE MOVED 393px -- OWN CROP BOX, NOT COMPARABLE TO THE REST`. The crop did follow the moved face. |
| no `meta.json` | `meta.json MISSING`, name falls back to the directory |
| `meta.json` containing `not json at all` | `meta.json unreadable: JSONDecodeError` |
| `meta.json` = `{}` | `no parameter field in meta.json` |
| two PNGs in one arm dir | `2 PNGs, used newest: zzz.png` |
| `--no-detect` | header `NO ARM DETECTED A FACE -- fell back to hardcoded box (1028, 498, 732, 732)`, every tile chipped |
| a tile wider than `--max-width` | refuses the sheet, exits 1, scales nothing |

Every one of those runs still passed the 1:1 pixel check on every tile, because
the failure modes affect *which region* is cropped, never *how* it is pasted.

The verdict on the brief's "make misdetection loud": a tile whose crop is not
trustworthy is impossible to mistake for one that is — it has a red border, a
red label strip and a red chip naming the reason, against a plain grey strip and
thin grey border on the good ones.

---

## Two things I could not do here and did not fake

- **I cannot judge whether any of this looks better.** The proof sheet shows
  four WS4 ablations; visible differences between them are not a finding of
  mine. The owner looks at the images.
- **The flat-skin region's representativeness is an inference, not a
  measurement.** I can state its skin fraction (0.9503) and its flatness score
  (blurred-luma gradient 0.6656) and that it is the flattest 400x400 window
  inside the detected face box. Whether a cheek is the *right* region to judge
  the whole pipeline's skin rendering is a judgement, and I have written it up
  as one in `notes/P2-sheet-questions.md` §4 with the alternative and the flag
  that selects it.
