# P2-SHEET — judgement calls, logged as made

Not questions to be answered before work continues. These are decisions I took
with a reason, the lower-risk option where there was one, and where I could be
wrong. Every measurement quoted here is from a command whose output is in
`notes/P2-sheet.md`.

---

## 1. "1:1 native, no downscaling" vs "under 4000px wide"

**Resolved by choosing the crop size and the column count. Never by resampling.**

There is no resize call anywhere in the image path of `tools/contact_sheet.py`.
Tiles are `Image.crop` + `Image.paste` only. Column count is derived from the
tile width:

```
cols = (max_width - 2*MARGIN + GUTTER) // (tile_w + GUTTER)
```

If even one tile will not fit under `--max-width`, the tool **refuses that
sheet and exits 1** rather than scale anything. Verified: `--max-width 500`
prints `REFUSING: one 774px tile does not fit under --max-width 500. Not
downscaling.` and returns exit code 1.

If arms exceed `cols * --max-rows`, it emits numbered sheets
(`..._sheet1of2.png`) with the baseline repeated top-left on each. Verified
with `--max-rows 1`.

## 2. One common crop box for all arms, not a per-arm box

The brief says detection "gives a crop that follows the face across arms". It
does, and I use it — but I use it to compute **one** box, not one box per arm.

Reason: comparability is the entire point. If each arm is cropped around its
own detection, the face sits at a slightly different offset in each tile, and
flicking between tiles shows apparent motion that is a detector jitter artefact,
not a quality difference. Measured jitter across the four existing images is
small — x1 spans 971.9–984.3, y1 spans 400.0–413.0 — so a union box costs
almost nothing and buys pixel-aligned tiles.

The per-arm case is not abandoned, it is **promoted to an exception**: an arm
whose detected face centre moves more than `--move-tol` (default 25 % of the
face's long side) is excluded from the union, gets its own box, and is labelled
`FACE MOVED Npx -- OWN CROP BOX, NOT COMPARABLE TO THE REST` in red. Verified
on a synthetic arm rolled 260/300 px: it was flagged at 393 px against a 223 px
tolerance and given its own box.

**Where I could be wrong:** if a real arm shifts the face by 40–200 px it stays
inside the union, the union grows, and every tile silently gains slack instead
of being flagged. The header line reports the union each run, so it is visible,
but it is not loud. If that happens, lower `--move-tol`.

## 3. The face box in the brief is not what the detector returns — I did not hardcode it

The brief gives `[1028, 498, 732, 732]` and says verify, do not assume. Verified,
and it does **not** match the detector.

`face_yolov8m.pt` on `results/ws4/A_baseline/HasMetadata_00001_.png` returns one
face at conf 0.8846, `xyxy = (984.3, 413.0, 1638.5, 1303.7)` — **654 x 891, not
732 x 732**. The brief's box is a square whose centre is ~83 px right of the
detection centre; visually it clips the chin and takes in more hair on the right.

Provenance of the brief's number: it is the `face_box_xywh` field in
`results/ws4/metrics_*.json`, the box WS4 measured its face-crop PSNR/SSIM over.
It is a reasonable region, it is just not a detection.

So it is used in exactly one place: `FALLBACK_FACE_XYWH`, the last-resort box
when the detector is unavailable **and** no arm detected anything. When it is
used, every tile carries a red `CROP IS A HARDCODED FALLBACK -- NOT VERIFIED ON
THIS IMAGE` chip.

## 4. The flat-skin region is a cheek, inside the face box — not a shoulder

The brief allows "cheek or shoulder". I took cheek, and the reason is what the
arms actually change.

`results/face/ARMS.md` lists P2-RENDER's arms: `#114` denoise/steps and `#607`
removal are **face-pass** changes. A shoulder or forearm crop would be
byte-identical across those arms and the sheet would show nothing.

Measured, on the baseline: the flattest 400x400 window inside the detected face
box is at **(959, 847)**, skin fraction 0.9503, blurred-luma gradient 0.6656.
Scored as skin fraction (YCbCr gate) against the gradient magnitude of a
*blurred* luma — blurring first is deliberate, so fine skin texture, which is
the thing being judged, does not count against a window, while eyes, nostrils,
lips and hair edges do.

For comparison I also searched the whole frame. The flattest large skin regions
are on the forearm around y≈2760–3000 (600x600 at (780,2760), gradient 0.663) —
genuinely flatter and larger, but outside every face pass. Two of the arms
(`D_skinblend_075`, `H_skinblend_050`, and `#98 UltimateSDUpscale`) *are*
whole-frame, so for those a forearm crop would show something. `--skin-anchor
image` switches to a whole-frame search for exactly that case; `--skin-box
x,y,w,h` pins any region.

**Where I could be wrong:** if the owner wants the skin sheet to be about the
skin-detail amplifier rather than the face pass, the forearm is the better
region and `--skin-anchor image` is the flag. I took the face-pass reading
because that is what most of the arm list changes.

## 5. The skin tile cannot be the same size as the face tile

The brief says "a second sheet at the same crop". Read literally as the same
tile *size*, it is not achievable: I searched every window from 240x240 to
640x880 inside the face box and the **largest** one with skin ≥ 97 % and low
structure is **400x520**. A 774x1050 region of featureless facial skin does not
exist on this composition — the face is only 654x891 including the eyes, nose
and mouth.

So I read "at the same crop" as **at the same 1:1 scale**, which is the
invariant the owner actually stated, and sized the skin tile to a region that
exists. Default 400x400 (square, comfortably feature-free, 9 per row).
`--skin-size` changes it.

## 6. The crop box moves as arms land, unless it is pinned

The face box is the union of the detections present, so adding an arm can
change it, and two runs a day apart can produce slightly different crops. That
is honest — the box is printed on every sheet and stored in the manifest — but
it makes sheets non-identical.

**Recommendation for the final deliverable:** run once with all arms present,
read `face_box_xywh` and `skin_box_xywh` out of `<prefix>_manifest.json`, then
re-run with `--face-box` and `--skin-box` pinned to those values. Every
subsequent sheet is then byte-comparable.

## 7. `results/face/arms/` layout: agreed by using it

`results/face/ARMS.md` specifies `results/face/arms/<arm_name>/` with `*.png`,
`api_graph.json`, `meta.json` carrying `arm`, `changed`, `prompt_id`,
`exec_seconds`, `cached_nodes`. The tool reads exactly that and writes nothing
under `arms/`. Key lookup is defensive (`arm`/`name`/`label`… ,
`changed`/`param`/`parameter_changed`…) so a schema drift degrades to the
directory name plus a red chip rather than a crash.

`exec_seconds` and `cached_nodes` are **displayed and not interpreted** —
`ARMS.md` warns that arms with differing cache state must not be compared on
time, so both numbers sit on the tile and the reader can see the mismatch.

**One real trap I hit:** P2-RENDER's baseline is `A0_baseline`. My first
baseline matcher checked a list of prefixes and missed it, which would have put
the wrong tile top-left on every sheet. Now a regex that strips an ordering
prefix (`a_`, `A0_`, `00-`, `1.`) before matching
`baseline|base|control|reference|ref`. Tested against all 12 names in `ARMS.md`:
exactly one match, `A0_baseline`.

Residual risk: an arm named like `A2_control_repeat` would also match. That is
handled loudly rather than silently — the header prints `! N arms claim to be
the baseline` and uses the first.

## 8. Smaller calls

- **Sheet background** neutral dark grey `#1a1a1a`, the convention for image
  review, so the surround does not bias skin-tone judgement.
- **Label gutter height** is computed from the tallest label stack actually on
  that sheet, not a constant, so nothing clips and nothing ever overlays a crop.
- **Label font size scales with tile width** (floor 21/17/15 px) so a 400 px
  skin tile is as legible as a 774 px face tile.
- **Label truncation order**: crop mode, then confidence, then the box — so a
  narrow tile that has to ellipsise loses the box (recoverable from the header
  and the manifest), never the crop mode.
- **`--pad-frac` applies per axis**, not as a fraction of the long side. Padding
  a 667-wide box by 8 % of its 905 height inflated the tile to 812 px and cost a
  column for nothing; per-axis gives 774 px and 5 columns.
- **Half-written PNGs** are skipped with a `[skip]` line instead of killing the
  run, because the tool is meant to be re-run while renders are landing.
