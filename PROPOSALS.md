# PROPOSALS.md — task list for the pod session

Written to be executed without re-deriving anything. Node ids match `MAP.md`.
Ordered so that **P0–P2 are prerequisites** — everything after assumes the
harness from P1 exists and the baseline from P2 has been captured.

**Verification method throughout is the graph diff, never output hashing.**
Rationale is in `CLAUDE.md`; the harness is specified in P1.

Each item states: **change · expect · measure · kill criterion**.

---

## Tier 0 — do these first

### P0 · Recover the orphaned prompt batch — **no GPU needed, do this on the laptop**

**Change.** `#483`'s six real prompts live in `properties.prompt_queue_data`; the
pack reads `properties.prompt_batch_data`, which is `"[]"` (`AUDIT.md` A0).
Decide one of:

- **(a) Migrate.** Copy `prompt_queue_data` into `prompt_batch_data`. The entry
  schema already matches what `reality_prompt_generator.py:181-206` expects
  (`positive_prompt`, `negative_prompt`, `repeat_count`, `seed`, `tags`).
- **(b) Replace.** The six prompts are interior/scene photography, not this
  product's content. Author six real NSFW character prompts and write those in.
- **(c) Ship deliberately empty**, and make the failure loud instead of silent —
  see the sub-task below.

**Recommendation: (b), then (c) as a safety net.** (a) preserves data that looks
like somebody else's test fixture.

**Sub-task, independent of which you pick.** In
`nodes/input_nodes/reality_prompt_generator.py:224-227`, the empty path returns
`([""], [""], [0], 0, resolved)` silently. Change it to raise, or at minimum to
surface a UI-visible error. A pipeline that renders an unprompted image at seed 0
rather than refusing to run is the worst possible failure mode for a paid product
— the buyer gets a plausible-looking wrong result and no signal.

**Measure.** Load the saved file in a fresh browser profile (no IndexedDB, no
localStorage — the panel caches there and will mask the bug). Confirm the prompt
panel shows six entries and that a queued prompt carries a non-empty
`prompt_batch_data`.

**Kill criterion.** If a fresh-profile load *does* populate the panel from
`prompt_queue_data`, then some code path reads that key and my grep missed it —
in which case find it and tell me, because the rest of A0 is then wrong.

---

### P1 · Build the graph-diff harness — **no GPU needed, everything else depends on it**

**Change.** A script `tools/graphdiff.py` that takes two workflow JSONs and
reports semantic differences. It must:

1. **Flatten subgraphs.** Interior links use `origin_id: -10` for the subgraph
   input node and `target_id: -20` for the output node, with slots indexing the
   definition's `inputs`/`outputs` arrays. Recurse; key nodes as
   `(host_path, node_id)`.
2. **Constant-fold bypass (`mode: 4`).** For each output of a bypassed node, find
   the **first input whose type matches that output's type** and forward its
   producer. If no input matches, the link resolves to **nothing** — record that
   explicitly, it is how `AUDIT.md` A2 and A6 were found.
3. **Constant-fold the INSTARAW switches** — `INSTARAW_LatentSwitch`,
   `INSTARAW_ImageSwitch`, `INSTARAW_FloatSwitch`, `INSTARAW_StringSwitch`,
   `INSTARAW_AnySwitch`, etc. Their first widget is the boolean; fold to
   `input_true` or `input_false` accordingly.
4. **Resolve widget-vs-link.** For every input carrying a `"widget"` key, report
   the *effective* value: the link's producer if linked, else the widget value
   from `widgets_values`. This is what catches the A7 class.
5. **Compare** every resolved node on every resolved input, and report added,
   removed and changed nodes. **Zero differences proves a change is inert.**

A working flattener already exists at
`scratchpad/flat.py` from this session (reachability walk + boundary resolution);
it is a starting point, not the finished tool — it does not yet do steps 2–4.

**Measure.** Self-test: `graphdiff(OFMTech_NSFW.json, OFMTech_NSFW.json)` must
report zero differences. Then re-order the `nodes` array and re-run — still zero.
Then change one widget value — exactly one difference.

**Kill criterion.** If the self-test on an unmodified file reports differences,
the flattener is wrong and every result downstream is untrustworthy.

---

### P2 · Capture the baseline — measurements, not impressions

**Change.** None. Run the graph as-is, after P0.

**Measure.** Record all of:

- Wall-clock total, and per-node timing (ComfyUI logs this; or use
  `--verbose`). **Attribute time to each of the five detailer passes and the two
  UltimateSDUpscale passes separately** — everything downstream is an ablation
  against these numbers.
- Peak VRAM, and where in the run it occurs. My prediction from static reading is
  the peak is sg1 `#593`'s 3584×4608 output (P3), **not** either sampler. Confirm
  or refute — it changes which optimisation matters.
- The **actual output dimensions**. `MAP.md` §12 derives ≈2688×3456 arithmetically
  and that has not been verified.
- Model load time, and whether SDXL and Z-Image are both resident simultaneously
  or swapped.
- Save the output PNG **and the full API-format prompt JSON**. The prompt JSON is
  the control for every later graph diff.

**Kill criterion.** None — this is instrumentation. But if peak VRAM is under
~12 GB the memory proposals (P3, P4, P12) drop in priority.

---

## Tier 1 — provably inert or near-inert cleanups

### P3 · Collapse the 4×-then-0.4 hires ladder

**Change.** sg1 currently does
`#593 ImageUpscaleWithModel` (4x_NMKD, → 3584×4608) → `#595 ImageScaleBy` (lanczos
0.4, → ≈1434×1843). Net magnification **1.6×**, via a **16.5 megapixel**
intermediate.

Test three variants against baseline:
- **(a)** `ImageScaleBy` lanczos 1.6 alone — no model upscale.
- **(b)** a 2× ESRGAN model → `ImageScaleBy` 0.8. Same net 1.6×, **one quarter**
  the intermediate pixels.
- **(c)** keep 4× but move `#595` before `#593`… no — not valid, skip.

**Expect.** (b) gives most of the model-upscale detail benefit at a quarter of the
peak intermediate. (a) is the cheap floor and probably visibly softer.

**Measure.** Peak VRAM and wall-clock at `#593`/`#595`; then the A/B image pair at
final resolution for your eye. Graph-diff to confirm nothing *else* changed.

**Kill criterion.** If (b)'s output is visibly softer than baseline at 100% crop,
keep the 4× path — the intermediate cost is real but detail is the product.

**Why this is worth doing:** a 3584×4608 RGB float tensor is ~793 MB in fp32.
Producing it only to discard 91% of its pixels is the single largest transient
allocation I can identify statically.

---

### P4 · Delete the pure VAE round-trip (`AUDIT.md` A1)

**Change.** Remove sg1 `#597 VAEEncode` and `#616 VAEDecode`; wire
`#607.image` → `#617.image` directly.

**Expect.** One VAE encode + one VAE decode saved at ≈1434×1843, and one lossy
round-trip removed from every image.

**Measure.** Graph-diff: every remaining node must be identical on every input;
the only differences may be the two removed nodes. Then time delta from P2, and
an A/B pair.

**Kill criterion.** If the graph diff shows *any* other node changed, stop — the
rewire was done wrong. On pixels: a VAE round-trip is lossy, so expect a small
difference. If the "after" looks *worse*, something is wrong, because removing a
lossy step should not degrade.

---

### P5 · Delete the orphaned and dead-wired nodes (`AUDIT.md` A9)

**Change.** Remove, in this order, diffing after each:

1. `#583 DetailerPipeToBasicPipe` (sg2) — no links in either direction. **Provably
   inert.**
2. `#641 SetUnionControlNetType` (sg6) — output unconnected.
3. `#627`, `#633` (sg6) — `PrimitiveFloat` → `FloatSwitch`, output unconnected.

**Do NOT delete** `#604`, `#629`, `#634` (`INSTARAW_BooleanBypass`) or `#614`
(`PrimitiveBoolean` "ENABLE IMAGE FILTERING?") until P6 resolves what they do.

**Expect.** Graph diff reports only the removed nodes. Zero behavioural change.

**Measure.** Graph diff must be clean. No render needed to prove inertness — but
still queue once to confirm the prompt validates.

**Kill criterion.** Any diff on a retained node.

---

### P6 · Determine what `INSTARAW_BooleanBypass` actually does

**Change.** None yet — this is a source read plus one experiment.

Read `ComfyUI_INSTARAW/js/boolean_bypass.js` and
`js/group_bypass_detector.js`, and `nodes/logic_nodes/virtual_nodes.py:7`
(`INSTARAW_BooleanBypass`) and `:59` (`INSTARAW_GroupBypassToBoolean`).

**The question:** all three instances in this graph have **all four outputs
unconnected**, which is inert on the Python side. If the JS toggles other nodes'
`mode` from the browser, they are load-bearing UI and `#614` "ENABLE IMAGE
FILTERING?" is a buyer-facing control.

**Experiment.** In the UI, flip `#614` from `true` to `false`, queue, and diff the
submitted API prompt against the `true` case. If `#603 INSTARAW_ImageFilter`
disappears from the prompt, the mechanism is confirmed and these nodes must stay.

**Kill criterion.** If the two prompts are identical, the boolean does nothing and
all four nodes join P5's deletion list.

---

## Tier 2 — the architectural questions

### P7 · **Ablate the sg1 face pass** — the biggest single suspect (`AUDIT.md` A22)

**Change.** Bypass sg1 `#598 ToDetailerPipeSDXL` and `#607 FaceDetailerPipe`.
Wire `#596.IMAGE` → `#617.image` (or `#597`, depending on P4).

**Rationale.** `#607` details the face at denoise 0.45 at ≈1434×1843. The image
then goes through ×1.25 and ×1.5 upscales, after which sg2 `#114` **re-detects the
same face with the same detector and resamples it at denoise 0.80**. Very little
of `#607`'s work can survive 0.8 denoise.

**Expect.** A large time saving (one full detailer pass plus its detector and SAM
load) with little or no visible difference in the final image.

**Measure.** Time delta. A/B pair at final resolution, **plus a 100% crop of the
face** — that is where any difference will be. Also record whether `#611`
(`face_yolov8m`) and the SDXL detailer pipe drop out of the load set.

**Kill criterion.** If the face is visibly worse — softer, or with different
structure — `#607` is doing real work that `#114` builds on rather than replaces,
and it stays. **This is a quality call and it is yours to make, not mine.**

**Follow-up if the ablation succeeds:** the same logic questions `#598`'s refiner
wiring, which duplicates the base model/clip/conditioning into all four refiner
slots (`#598` in[5..8] = in[0..3] sources). If `#607` goes, `#598` goes with it.

**Sub-task, do this either way (`AUDIT.md` A23).** sg2 `#107` loads
`bbox/face_yolov8m.pt` and feeds **both** `#114.bbox_detector` and
`#114.segm_detector_opt`. A bbox-only YOLO checkpoint has no mask head. Five of
the graph's seven detector providers leave `SEGM_DETECTOR` unconnected — `#107`
and the bypassed `#171` are the only two that wire it, which suggests a
mis-drag.

Disconnect `#107.out[1]` from `#114.segm_detector_opt`, graph-diff to confirm
nothing else moved, then A/B the face at 100% crop. **Kill criterion:** if the
face changes, the segm path *was* contributing and Impact is doing something
useful with it — in which case find out what before removing it.

---

### P8 · Question the second UltimateSDUpscale (sg0 `#98`)

**Change.** Bypass sg0 `#98 UltimateSDUpscale`; wire `#87.IMAGE` to sg0's
`IMAGE_1` output.

**Rationale.** `#98` runs **2 steps at cfg 1, denoise 0.08**, on the DMD2 LoRA. A
denoise of 0.08 over 2 steps is at the threshold of doing anything at all — but it
still pays the full tiled-sampling cost across a ×1.5 upscale, plus a second
`4x-UltraSharpV2` load and a second DMD2 LoRA load.

Note the asymmetry with sg1's `#617`: 25 steps, cfg 4.5, denoise 0.25. Two
UltimateSDUpscale passes with radically different configs, separated only by the
hand detailer.

**Test three variants:**
- (a) bypass entirely (image stays at ≈1792×2304 — **this changes output
  resolution**, so it is not a like-for-like A/B; note it and judge accordingly).
- (b) replace with a plain `ImageUpscaleWithModel` + `ImageScaleBy` to the same
  ×1.5 — same resolution, no sampling.
- (c) keep it but raise denoise to 0.2 and steps to 8 — does it start
  contributing?

**Measure.** Time for `#98` alone from P2's per-node data. A/B triple at 100% crop
on skin texture, which is what a 0.08 denoise would plausibly affect.

**Kill criterion.** If (b) is indistinguishable from baseline, `#98`'s sampling is
decorative and (b) ships. If (c) is clearly better than baseline, the node is
**under-configured** rather than useless, and the answer is to fix its settings.

---

### P9 · Do both model families need to be resident?

**Change.** Three experiments, in increasing ambition.

**(9a) Measure the cost.** From P2, record whether SDXL (`SDXLNSFW.safetensors` +
2× DMD2 LoRA + PAG) and Z-Image (`zimage.safetensors` + `qwen.safetensors` +
`ae.safetensors`) are co-resident or swapped, and the VRAM/time cost of swapping.
The graph alternates families: sg1 SDXL → sg0 SDXL → sg2 **Z-Image** → sg4
**Z-Image** → (sg5 SDXL, dead). That is **one** family switch in the live path,
which is the good case. Confirm it.

**(9b) Try SDXL for the detail passes.** Repoint sg2 `#114`/`#165` and sg4 `#406`
at the SDXL model/clip/vae. **This also requires re-encoding their prompts** —
`#105`, `#106`, `#166`, `#167`, `#394`, `#398` all encode with the Qwen CLIP.

**Expect:** Z-Image drops out entirely (~one UNET + one text encoder + one VAE of
VRAM), and — the interesting part — **the three `ImageColorMatch+` nodes may
become unnecessary**, because the colour drift they correct is plausibly the
SDXL/Z-Image mismatch (`MAP.md` §8).

**(9c) The inverse.** If Z-Image is doing the quality lifting, ask whether the
SDXL base is the weak link and whether Z-Image should generate too.

**Measure.** VRAM delta, time delta, and A/B on faces and eyes. Then, separately,
bypass `#137`, `#111`, `#163` and see whether colour drifts — that tells you
whether the colormatch chain is a symptom of the split or an independent choice.

**Kill criterion.** If SDXL detail passes are visibly worse on faces, the split is
deliberate and correct, and this whole line of attack closes. Record that verdict
so nobody reopens it.

**This is the proposal I am least able to predict and most curious about.** The
three-colormatch chain is unusual enough that it is either compensating for
something real or it is cargo cult, and one render answers it.

---

### P10 · Make the graph reproducible (`AUDIT.md` A21)

**Change.** sg1 `#600 KSamplerAdvanced` `control_after_generate`:
`"randomize"` → `"fixed"`. Better: add a `noise_seed` input and wire it from the
same `#483.seed_list` that drives `#592`.

**Expect.** Two runs at the same RPG seed produce byte-identical prompts (not
byte-identical images — see the note below).

**Measure.** Queue twice at a fixed RPG seed; diff the two submitted API prompt
JSONs. They must be identical. **This is a prompt-level check, not an image-level
one** — do not compare rendered output.

**Kill criterion.** None; this is close to unambiguously correct for a product.
The only argument for the current behaviour is deliberate variation-on-repeat,
which should then be a documented, labelled control rather than a buried widget.

---

### P11 · Fix the UltimateSDUpscale tile sizing (`AUDIT.md` A7)

**Change.** sg0 `#98`'s `tile_width`/`tile_height` are wired from `#99
GetImageSize`, so tiles equal the whole image and VRAM scales quadratically with
base resolution while the widgets read a reassuring 512.

Disconnect `#99` and set fixed tiles (try 1024 and 768).

**Expect.** Materially lower peak VRAM at the cost of possible tile seams.
Critically, it makes VRAM **independent of the user's chosen resolution**, which
matters for a product shipped to unknown hardware.

**Measure.** Peak VRAM at `#98`, plus an A/B at 100% crop **specifically hunting
for tile seams** — that is the failure mode. Then repeat the whole run at
1152×1536 base to confirm VRAM no longer tracks resolution.

**Kill criterion.** Visible seams at 1024 tiles that do not appear with
whole-image tiling. If so, try `seam_fix_mode` other than `"None"` — note it is
currently `"None"`, which is exactly why seams would show.

---

### P12 · Repair or delete the ControlNet path (`AUDIT.md` A5)

**Change.** The path is mis-wired as well as bypassed: `#641
SetUnionControlNetType` sits in parallel with `#638`, so the union type is never
applied.

**My recommendation is delete** (reasoning in `QUESTIONS.md` Q3). If you want it
revived instead, the repair is:

1. Rewire `#639.CONTROL_NET` → `#641.control_net` → `#638.control_net`.
2. Un-bypass `#639`, `#641`, `#638`, `#640`, `#626`, `#630`.
3. `#626` and `#630` have **no image input** — an image source must be wired.
   `#646 LoadImage` exists but currently feeds only the IPAdapter branch.
4. `#636 INSTARAW_LatentSwitch` must flip to `true` for img2img, and `#631
   VAEEncode` un-bypassed.

That is four separate repairs, which is why I recommend deletion.

**Measure.** If revived: confirm the depth map appears at `#642 PreviewImage`, and
that `#638`'s conditioning differs from its input (graph diff will show the
node is no longer a passthrough).

**Kill criterion.** If a buyer has never asked for ControlNet, this is dead weight
carrying a latent bug. Delete it and reclaim the `controlnet-union-sdxl-promax`
(~2.5 GB) and `depth_anything_v2_vitl` downloads from the install.

---

### P13 · Resolve the bypass/lazy-evaluation questions (`AUDIT.md` A2, A6)

**Change.** None — two probes.

**Probe 1 (denoise).** Queue the unmodified graph and read the submitted API
prompt for `#592`'s `denoise`. Three possible outcomes:
- `1` → the widget fallback works; A2 is a latent trap, not a live bug.
- `0.5` → bypass forwards the widget value; sg1 is running at half denoise from an
  empty latent, which would be a serious live bug.
- prompt rejected → `denoise` is required and unresolvable.

**Probe 2 (latent switch).** In the same prompt JSON, check whether `#632
INSTARAW_ImageListFromBatch` and `#631` appear at all. If they do,
`INSTARAW_LatentSwitch` is not lazy and the dead img2img branch is being walked
every run.

**Measure.** Read the JSON. No rendering, no timing. Both probes are one queue.

**Kill criterion.** N/A — this is pure fact-finding, and it settles two of the six
open items in `MAP.md` §15.

---

### P14 · Add a feathered mask to sg4's composite (`AUDIT.md` A8)

**Change.** sg4 `#418 ImageCompositeMasked` has no `mask`. Build one: take
`#403 MaskBoundingBox+`'s mask output (currently unconnected, `out[0]`), feather
it (`INSTARAWFeatherMask` from the pack, or `FeatherMask` from core), and wire it
to `#418.mask`.

**Expect.** No hard rectangular seam where the detailed face crop is pasted back.

**Measure.** A/B at 100% crop on the crop boundary. If no seam is visible in the
baseline, this is a no-op worth doing anyway for robustness at other resolutions.

**Kill criterion.** If the feathered version blends *out* the eye detail that
`#406` added, the feather radius is too large — tune rather than abandon.

---

### P15 · Measure whether duplicate loaders actually cost anything (`AUDIT.md` A11)

**Change.** None — measurement first, consolidation only if justified.

**Measure.** From P2's per-node timings, sum the time in the 3 live `SAMLoader`,
7 `UltralyticsDetectorProvider` and 4 `UpscaleModelLoader` nodes. Check whether
ComfyUI's loader cache deduplicates them **across subgraph boundaries** — that is
the part I could not determine statically.

**Kill criterion.** If total loader time is under a few seconds and VRAM shows no
duplicate residency, **do not consolidate**. Consolidating means routing model
links across subgraph boundaries, which makes the graph harder to read for a
buyer, and the benefit would be zero. Record the verdict either way.

---

## Tier 3 — packaging and shape

### P16 · Strip development instrumentation (`AUDIT.md` A10)

**Change.** Remove or bypass the 9 live instrumentation outputs: `#104`, `#118`,
`#164`, `#419`, `#22`, `#481`, `#480` (root), `#96` (sg0), `#395`, `#396` (sg4).

Keep **one** before/after comparer if you want it as a product feature, and give
it a title that says so.

**Expect.** Fewer PNG encodes and temp writes per run; a workflow that opens with
one obvious output instead of eleven panels.

**Measure.** Time delta from P2 (I expect this to be small but non-zero — each
comparer holds two full-resolution images). The real benefit is comprehensibility,
which is not measurable and is the point.

**Kill criterion.** None, but do this **last** — the comparers are how you will
judge every A/B in P3–P14. Strip them only when the tuning is finished.

---

### P17 · Rename the seven subgraphs

**Change.** Apply the names from `MAP.md` §2. All seven are currently
`"Dont touch!!!"`.

**Measure.** Graph diff must show **zero** semantic differences — `name` is
metadata on the subgraph definition and touches no link, widget, or node input.
This is the cleanest possible test case for the P1 harness, so **run it as P1's
final validation**: a change that must diff to zero, on a real edit.

**Kill criterion.** If the diff is non-empty, the harness has a bug.

---

### P18 · Reconsider whether sg3 should exist

**Change.** sg3 is five nodes doing two unrelated jobs (`MAP.md` §7): four are
resources consumed by sg2, one (`#163 ImageColorMatch+`) post-processes sg2's
output for sg4. That split is why the sg2↔sg3 boundary looks cyclic.

Proposal: move `#160`, `#161`, `#166`, `#167` **into sg2**, and `#163` into
**sg4**. sg3 disappears; the apparent cycle disappears with it; the graph goes to
six stages that each do one thing.

**Measure.** Pure refactor — graph diff must be **zero differences**. This is the
most demanding test of the P1 harness because nodes move across subgraph
boundaries while the flattened graph stays identical.

**Kill criterion.** Any non-zero diff.

**Do this after all tuning is done** — it renumbers nothing but it does invalidate
any half-finished edit in sg2/sg3.

---

### P19 · Find the right skin-detail blend strength (`AUDIT.md` A3)

**Change.** sg0 `#87 ImageBlend` is set to `blend_factor: 1.0`, `normal`. At that
value the output is **exactly `image2`** — the `x1_ITF_SkinDiffDetail` filtered
version — and `image1`, the un-filtered hand-detailed image, contributes nothing.

Render the ladder: `blend_factor` = **0.0 / 0.25 / 0.5 / 0.75 / 1.0**.

**Rationale.** Nobody wires both the original and the filtered image into a blend
node and then sets the factor so the original is discarded. The node exists to
allow partial blending; 0.5 is the conventional use of this filter. Either the
value was set to 1.0 while debugging and never restored, or full strength is
genuinely wanted — the ladder tells you which in one batch.

**Expect.** 0.0 is the no-filter control and should look identical to bypassing
`#90`/`#91` entirely. 1.0 is current behaviour. The interesting region is 0.25–0.5.

**Measure.** Five images, same seed, **100% crops on skin**. This is entirely a
quality judgement — it is yours, not mine. Cost is negligible: `#91` runs either
way, only the blend arithmetic changes.

**Kill criterion.** If 1.0 is clearly best, close this permanently and add a
comment in the graph saying so, because it will look like a bug to the next
reader — as it did to me.

**Cheap bonus while you are here:** confirm 0.0 really is identical to bypassing
`#90`+`#91`. If it is not, `ImageBlend`'s `normal` mode is not doing what I
assumed and `AUDIT.md` A3's inference is wrong.

---

## Ideas I could not cost from here, offered as prompts rather than plans

- **The batch/list churn.** `INSTARAW_BatchFromImageList` → `INSTARAW_ImageFilter`
  → `INSTARAW_ImageListFromBatch` in sg1, plus `ImageListFromBatch` in sg4 and
  sg6. The graph converts between batch and list at least four times. If the
  filter is the only node that needs list semantics, the other conversions may be
  removable. Worth a look once P6 clarifies the filter's role.
- **Detail passes at final resolution.** `#114` details the face at guide_size
  1024 on a ≈2688×3456 image — so the face crop is downscaled to 1024, sampled,
  and upscaled back. Detailing *before* the final upscale might avoid a
  resolution round-trip on the most important region of the image. This reorders
  the pipeline, so it is a bigger swing than anything above, but it is the kind of
  question that only gets asked once someone has drawn the map.
- **PAG at scale 1.0** (`#609`). That is a mild setting. Worth a sweep at 0 / 1 /
  3 while you have the harness up — cheap, and it affects every image.
- **`#617` at 25 steps / cfg 4.5 vs `#98` at 2 steps / cfg 1.** These two upscalers
  disagree about everything. One of them is probably wrong for its job.
