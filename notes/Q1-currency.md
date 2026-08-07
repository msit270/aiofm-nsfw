# Q1 — Currency: pins, detectors, upscalers (2026-08-07)

Agent Q1, recommend-only. Nothing under `OFMTech-NSFW/`, `dist/`, or the
workflow JSON was edited. Evidence stored under:

- `results/run4/quality/pins/` — GitHub compare/release/commit API responses
- `results/run4/quality/licences/` — Civitai / HF / GitHub licence responses,
  file hashes, OpenModelDB entry copies (`omdb/` + `PROVENANCE.txt`)
- `results/run4/quality/Q1/detectors/` — CPU detector-inference raw results + META.json

Every licence flag below cites a response file stored **this session**. No GPU
was touched: no lock taken, no server contacted, no pipeline render. Detector
comparisons ran on CPU against existing run3 renders, as mandated.

---

## THE RANKED MENU (by expected value)

### 1. Replace `4x-UltraSharpV2.pth` — shipped upscaler is licensed NON-COMMERCIAL, and it sits on the live path twice

**What exists.** The shipped file (sha256 `0335cf48…`, in
`licences/shipped_model_sha256.txt`) is **byte-identical** to
`4x-UltraSharpV2.pth` in HF repo `Kim2091/UltraSharpV2` — LFS oid match in
`licences/hf_tree_Kim2091_UltraSharpV2.json`. That repo's licence tag, read
from the HF API this session, is **`cc-by-nc-sa-4.0`**
(`licences/hf_Kim2091_UltraSharpV2.json`). OpenModelDB agrees
(`licences/omdb/4x-UltraSharpV2.json`). NonCommercial + ShareAlike, in a
product being sold. This is exactly the class of problem the DMD2→TDD swap
already removed once (the "NOT DMD2" comment block in aiofm_setup.sh's
models/loras section).

**Where it is used** (live path, verified from the workflow JSON):
- `#612 UpscaleModelLoader → #617 UltimateSDUpscale` ("2. Base Generator": upscale_by 1.25, denoise 0.25 — the main tiled refine)
- `#100 UpscaleModelLoader → #98 UltimateSDUpscale` ("3. Hands, Skin & Second Upscale": upscale_by 1.5, denoise 0.08, lcm 2 steps — nearly pure ESRGAN-class upscale with light polish)

**Sad wrinkle:** the current community consensus "best realistic upscale
model" of 2025/26 *is* UltraSharpV2 ("Kim2091's best model ever", DAT2,
2025-05-23 — WebSearch, Kim2091-Models releases). The shipped pack is
quality-current; only the licence is the problem. Expect the swap to be a
quality-neutral-at-best change that must be A/B'd, not a free upgrade.

**Candidates** (all licences from `licences/omdb/<name>.json`, cloned from
OpenModelDB@`982f73db` this session; download URLs inside those files; all
archs confirmed loadable by the pod's spandrel 0.4.2 — DAT/SPAN/DRCT/ATD/
PLKSR/ESRGAN all in `spandrel.MAIN_REGISTRY`):

| candidate | licence | size | arch | note |
|---|---|---|---|---|
| 4x-Nomos8kDAT | CC-BY-4.0 | 309 MB | DAT | closest arch/character to UltraSharpV2 (also DAT); photo-trained |
| 4x-RealWebPhoto-v4-dat2 | CC-BY-4.0 | 140 MB | DAT2 | trained for degraded *web/phone photos* — closest to this product's "Instagram-real" target |
| 4x-Nomos2-hq-atd | CC-BY-4.0 | 82 MB | ATD | small, strong, 2024-09 |
| 4x-Nomos2-hq-drct-l | CC-BY-4.0 | 243 MB | DRCT-L | heaviest, highest-fidelity of the set |
| 4x-FaceUpDAT / 4x-FaceUpSharpDAT | CC-BY-4.0 | 155 MB | DAT | trained specifically on faces — aligned with a face product |
| 4x-NomosUni-span-multijpg | CC-BY-4.0 | 9 MB | SPAN | fast option for the **#98 hands slot**, where denoise 0.08 repaint hides upscaler character |
| RealESRGAN_x4plus | BSD-3-Clause | 67 MB | ESRGAN | boring, safe fallback (`licences/omdb/4x-realesrgan-x4plus.json`) |

**What it would change.** Output-affecting in both slots → per prime directive
this needs a pod A/B pair per candidate with objective deltas; I cannot and do
not judge which looks better. Render seconds: UNVERIFIED; DAT-class ≈
UltraSharpV2's own arch so #617 should be roughly cost-neutral, SPAN in #98
should be faster — measure, don't trust this sentence.

**Cost.** One mirror upload + one `dl` line change per slot; 9–309 MB
download; CC-BY-4.0 requires attribution (a line in the README/manifest) and,
unlike NC-SA, permits sale and mirroring.

**Recommendation.** Treat as a Track-1-grade licence defect with a Track-2
A/B: stage 4x-RealWebPhoto-v4-dat2 and 4x-FaceUpDAT for #617, and
4x-NomosUni-span-multijpg + 4x-Nomos8kDAT for #98, render the four arms
against baseline (Q-PROTOCOL lock, fresh process each), owner picks by eye.
DO NOT ship UltraSharpV2 further. (Also note ShareAlike: even past
distribution arguably obligates share-alike terms — owner/legal call, not mine.)

---

### 2. Replace or delete `x1_ITF_SkinDiffDetail_Lite_v1.pth` — second NC licence on the live path

**What exists.** Shipped file sha256 `94d368b6…` **matches exactly** the
OpenModelDB record for `1x-ITF-SkinDiffDetail-Lite-v1` — licence
**CC-BY-NC-SA-4.0**, author intheflesh, 2022
(`licences/omdb/1x-ITF-SkinDiffDetail-Lite-v1.json`, sha256 field vs
`shipped_model_sha256.txt`). Used once, live: `#90 UpscaleModelLoader → #91
ImageUpscaleWithModel` (Hands stage; FaceDetailer#92 output → #91 → ImageBlend#87
→ UltimateSDUpscale#98).

**Candidates.** The 1x "skin texture" niche is almost entirely NC
(`1x-ITF-SkinDiffDDS-v1` is CC-BY-NC-4.0 too). The exceptions found in the
whole 671-model DB:
- **1x-SkinContrast-(High-)SuperUltraCompact — CC0-1.0**, 181 KB (!), Compact
  arch (`licences/omdb/1x-SkinContrast-SuperUltraCompact.json`). CC0 means it
  may legally be mirrored straight into `$REPO` (its mediafire hosting is
  flaky, so mirroring matters). Honest caveat: it is a skin *contrast* model,
  not a diffuse-texture model — the visual effect is NOT equivalent, only
  adjacent. UNVERIFIED visually.
- **Deleting the node pair** (#90+#91, feed FaceDetailer#92 output into
  ImageBlend#87 directly). ImageBlend#87 already mixes this branch, and
  UltimateSDUpscale#98 repaints at denoise 0.08 afterwards; whether the 1x
  pass survives that pipeline visibly is exactly the kind of thing run-2/3
  history says must be A/B'd, not asserted.

**Recommendation.** A/B three arms on the pod: baseline / SkinContrast /
1x-pass-bypassed. If bypass is visually indistinguishable, delete — that
removes an NC licence AND a model load for free. Cost: one 181 KB file or one
graph edit; render seconds unchanged or slightly reduced (UNVERIFIED).

---

### 3. `lips_v1.pt` — provenance SOLVED this session; redistribution flags are not clean; no clean drop-in exists

**What exists.** The shipped mouth detector (sha256 `ce9fe145…`) had unknown
provenance — Civitai by-hash missed it
(`licences/civitai_byhash_lips_v1_pt.json`) because Civitai hashes the
*zip*, not the payload. I downloaded Civitai model **142240** "ADetailer
(After Detailer) Lips Model" (creator mooseh111): the zip's sha256
`dc37038e…` matches Civitai's own file record, and the zip contains exactly
one file, `lips_v1.pt`, **byte-identical to the shipped file**
(`licences/civitai_model_142240_lips.json`; hashes in
`Q1/detectors/META.json`). Embedded training metadata (read from the
checkpoint): YOLOv8**n**, single class `lips`, trained 2023-09-08,
ultralytics 8.0.138, imgsz 640, batch 5 — a small hobby-trained nano model.

**The flag.** Civitai permissions read this session:
`allowCommercialUse = ['Image','RentCivit']` — **'Sell' is absent**. Selling
images made with it: permitted. **Redistributing the file in a paid pack — 
which `dl "$REPO/lips_v1.pt"` in aiofm_setup.sh's models/ultralytics section
still does at pack-cut 62acf44 — is not a granted permission.** Per my brief this marks it DISQUALIFIED for
continued mirror distribution.

**Is it at least good?** On the run3 renders: found lips on **26/26 valid
frames**, top-conf 0.745–0.845 against the mouth pass's bbox_threshold 0.70
(FaceDetailer #165). Margin is thin — one arm (R3_MOUTH_ceil40) passed by
0.045 — and the single "miss" (R3_PC_mid_46 tap) turned out to be the
**crash-guard control frame with a blacked-out face** (visually confirmed;
MediaPipe also finds no face on it) — i.e. the detector correctly rejects the
guard's failure state. That incidentally re-validates the mouth guard design.
Raw numbers: `Q1/detectors/yolo_compare_raw.json`.

**Candidates — there is no clean drop-in.** Searched this session:
- Civitai `query=lips` → only model 142240 itself (`licences/civitai_search_lips_adetailer.json`)
- HF `search=lips detection` / `mouth yolo` → one hit, `cc-by-nc-sa-4.0` → DISQUALIFIED (`licences/hf_search_lips.json`, `hf_search_mouth_yolo.json`)
- Anzhc/Anzhcs_YOLOs (the popular ADetailer YOLO source) → **agpl-3.0** → DISQUALIFIED (`licences/hf_Anzhc_Anzhcs_YOLOs.json`)

**Three real options, in my preference order:**
1. **Buyer-side download instead of mirror**: the zip downloaded
   *unauthenticated* today from `civitai.com/api/download/models/157700`
   (observed once this session; Civitai auth walls have fluctuated
   historically — mark that risk). A `dl_public`-style fetch + unzip removes
   the redistribution problem while changing zero bytes of behavior.
2. **Train an own lips nano** — lips_v1 itself is a 300-epoch yolov8n hobby
   job; the owner has pods and a licence-clean base (yolov8n weights via the
   ultralytics pipeline; note ultralytics itself is AGPL — the product
   ALREADY depends on the ultralytics runtime via Impact Subpack, so training
   adds no new runtime dependency, but distribution of self-trained weights
   is cleanest done under the owner's own terms). Also fixes the thin 0.70
   margin by training at the product's actual framing distribution.
3. **MediaPipe lips rework** — replace `#161 lips_v1 + #160 SAMLoader` with a
   MediaPipe FaceMesh lips SEGS (the graph already ships mediapipe for the
   eye pass; `MediaPipeFaceMeshToSEGS` in Impact Pack has lips parts). My CPU
   test: MediaPipe finds the mouth on 12/12 valid taps, lips-landmark bbox
   vs lips_v1 box IoU ≈ 0.55 (systematic: landmark hull is tighter than the
   YOLO box — crop_factor would need retuning, so this is output-affecting
   and needs an A/B). Kills a licence flag, a mirror file, AND one of four
   SAMLoader instances. Evidence: `Q1/detectors/mediapipe_lips_vs_yolo.json`.
   My originally hoped robustness advantage was falsified — on the one hard
   frame, MediaPipe fails exactly like lips_v1 (it was the black-face guard
   control), so this stands on licence/dependency grounds only.

---

### 4. Pin currency — six of seven pins are AT upstream HEAD; the seventh must NOT be bumped (proof included)

Verified 2026-08-07 via `git ls-remote` + GitHub compare API (stored:
`pins/compare_*.json`, all `"status": "identical"` except aux). Node types
each pack serves in THIS graph were extracted from the workflow JSON first
(listing below).

**Mid-session note:** aiofm_setup.sh was rewritten by Track 1 while I worked
(commits cbc4ac2 → b0ab0d4 "TRIM: install only the six packs" → f7da36b →
62acf44 "PACK CUT 8f376926", 13:17–13:23 UTC). I re-read NODE_REPOS at
62acf44: it now holds exactly the six NSFW packs **with the same six SHAs
audited below**, and the commit states the workflow is byte-unchanged — so
everything in this file carries over. Line-number citations elsewhere in this
note were rewritten as content anchors because the script's numbering moved
under me.

| pack | pinned | pin date | vs HEAD | verdict |
|---|---|---|---|---|
| ComfyUI-Impact-Pack (`FaceDetailer` ×3, `FaceDetailerPipe`, `BboxDetectorSEGS`, `DetailerForEachDebug`, `ToDetailerPipeSDXL`, `SAMLoader` ×3, `MaskToSEGS`, `SegsToCombinedMask` ×2, `MediaPipeFaceMeshToSEGS`, `ImpactConditionalBranch`, `ImpactIsNotEmptySEGS`, `SEGSRangeFilterDetailerHookProvider`) | `429d0159` | 2026-04-20 | **identical** | current; zero upstream fixes pending by definition |
| ComfyUI-Impact-Subpack (`UltralyticsDetectorProvider` ×5) | `50c7b71a` | 2025-07-22 | **identical** | current; upstream simply hasn't moved in >1 yr |
| comfyui_controlnet_aux (`MediaPipe-FaceMeshPreprocessor` ×1) | `95a13e2e` | 2026-02-16 | **7 behind** (HEAD `e8b689a`, 2026-04-13) | **DO NOT BUMP — see below** |
| ComfyUI_essentials (`ImageColorMatch+` ×3, `ImageResize+`, `MaskBoundingBox+`) | `9d9f4bed` | 2025-04-14 | **identical** | current; repo is in declared maintenance mode (frozen) |
| ComfyUI_UltimateSDUpscale (`UltimateSDUpscale` ×2) | `a5547db9` | 2026-06-22 | **identical** | current |
| rgthree-comfy (`Lora Loader Stack` ×2, `Image Comparer` ×1) | `6b76ee6f` | 2026-07-23 | **identical** | current |
| ComfyUI_IPAdapter_plus (**zero nodes in this graph**) | `a0f451a5` | 2025-04-14 | identical | was pinned+installed for nothing — the IPAdapter path was deleted from the graph in run-2/3 (`grep IPAdapter` over shipped JSONs: no hits). **Already resolved mid-session:** Track 1's commit b0ab0d4 removed it from NODE_REPOS along with the video repos; row kept for the audit record |

**Why controlnet_aux must stay pinned.** All 7 missing commits are one
MediaPipe-compat effort: `4d8bc17` "Add MediaPipe 0.10.32+ compatibility"
(rewrites `mediapipe_face_common.py`, +237/−85), plus requirements bumps
(`e8f52c9`, `4c742a7`, `fa41fbb`, merges `defae8c`/`9c49b2f`, version bump
`e8b689a`). The compat commit gates on `mp.tasks.vision.FaceLandmarker`
existing → "new API". **Probed on the pod's mediapipe 0.10.14 (the exact
version aiofm_setup.sh pins in its dependency section, re-confirmed present
at 62acf44): `FaceLandmarker` EXISTS but
`mp.tasks.vision.drawing_utils` does NOT** — so upstream HEAD takes the
new-API branch and dies at import:
`AttributeError: module 'mediapipe.tasks.python.vision' has no attribute 'drawing_utils'`
(executed HEAD's file against the pod interpreter this session; the eye pass
would fail at first `MediaPipe-FaceMeshPreprocessor` execution). The upstream
"fix" is defective for the mediapipe this product pins. Pin stays; re-examine
only if the mediapipe==0.10.14 pin ever has to move.

---

### 5. ComfyUI 0.15.1 / frontend 1.39.19 — 15 minor versions behind; one output-affecting change to this graph's model family; do not bump casually

Read from APIs this session (`pins/releases_ComfyUI*.json`,
`pins/commit_ComfyUI_v0.15.1.json`, `pins/releases_ComfyUI_frontend.json`,
`pins/contents_ComfyUI_v0.30.0_requirements.json`):

- Pod/product: **ComfyUI 0.15.1** (tag 2026-02-26, pins
  `comfyui-frontend-package==1.39.19`). Current stable: **v0.30.0**
  (2026-08-03, pins frontend **1.47.11**; the 1.48–1.50 trains exist above
  that, current 1.50.2 released today). Repo moved to `Comfy-Org/ComfyUI`.
- **Graph-relevant core change found:** v0.29.0 (2026-07-29) "Make z
  image/lumina 2 models use comfy kitchen rms rope" — this touches the exact
  arch the "5. Face & Mouth Detail (Z-Image)" stage runs (UNETLoader
  `zimage.safetensors` + CLIPLoader `lumina2`). Numerics change ⇒
  output-affecting for #114/#165/#406 passes. A bump is NOT behavior-neutral
  for this product and would need a full A/B + gate re-run.
- Nothing in the 0.16→0.30 release notes names fixes for the SDXL/KSampler/
  PAG/ModelSamplingDiscrete/VAE nodes this graph uses in a way that reads as
  a bug this graph suffers from (grep across stored release bodies; the VAE
  work is video-arch-specific).
- **Frontend / subgraph flattening:** between 1.39.19 and current there are
  repeated subgraph correctness fixes, most relevantly “lock in subgraph
  data-loss fixes (group→subgraph connection + nested-promotion value)”
  (≤1.48.4) and **“Fix migration of legacy reordered linked subgraph
  widgets” (PR 14113; in 1.47.11 / 1.48.6 / 1.49.0)** — i.e. the widget-order
  machinery this project's traps live in is being actively migrated upstream.
  Two consequences: (a) staying on 0.15.1/1.39.19 keeps the flattening
  behavior the pack was actually validated on — correct choice for the
  product today; (b) a buyer who upgrades ComfyUI will get frontend ≥1.47.11
  whose subgraph-widget migration path differs from what was tested —
  **UNVERIFIED how this graph loads there; that is a controlled-pod
  experiment worth scheduling before buyers do it for you.** The run-2
  `-10→-20` passthrough construct is confirmed absent from the shipping file
  (0 such links, checked this session), so that particular frontend hazard is
  dormant regardless.

**Recommendation:** stay pinned; add "open + flatten + render OFMTech_NSFW on
v0.30.0/frontend 1.47.11" as a single pod-session compatibility arm with the
graph-diff method, before any support statement about newer ComfyUI.

---

### 6. Face/hand detectors — shipped files are licence-clean and near-optimal; one free candidate upgrade available; the fashionable alternatives are all licence-disqualified

**Shipped, verified:** `bbox/face_yolov8m.pt` (live ×3: #611 base pipe, #107
face pass, #426 eyes) and `bbox/hand_yolov8s.pt` (live ×1: #89 hands) are
byte-identical to `Bingsu/adetailer` LFS objects
(`licences/hf_tree_Bingsu_adetailer.json`), whose repo licence tag is
**apache-2.0** (`licences/hf_Bingsu_adetailer.json`). No action required on
licence grounds. (Fetched buyer-side by `dl_public`, not mirrored — already
the right pattern.)

**Candidate:** `face_yolov9c.pt` from the SAME apache-2.0 repo (LFS oid
`d02fe493…` = my download's sha256). CPU A/B on the 14 delivered run3 frames
(`Q1/detectors/yolo_compare_raw.json`):

- mean top-confidence **0.9288 vs 0.9019** (+0.027, consistent every frame)
- top-box IoU vs incumbent **0.963 mean** (same face, same crop)
- both models: exactly 1 face ≥0.5 on every frame; CPU time equal (~0.4 s/img)
- file size 51.6 MB vs 52.0 MB — cost-neutral

Honest read: on nominal frames this changes **nothing** — both clear the
graph's 0.5/0.6 thresholds by miles. The +2.7 pts and YOLOv9 arch buy
robustness margin on hard frames only. Expected value: LOW but positive,
licence-free, drop-in (`ultralytics 8.4.115` on the pod loads it — done this
session). Recommendation: adopt at the next mirror/script touch, verify with
one pod A/B that SEGS crops land identically (bbox jitter of ~4% IoU can
shift detailer crops slightly — output-affecting in principle).
`hand_yolov9c.pt` equally available; see item 8 before spending any effort.

**Disqualified alternatives** (all flags read this session):
- `Anzhc/Anzhcs_YOLOs` (community favourite face/eye/lips segs) — **agpl-3.0** (`licences/hf_Anzhc_Anzhcs_YOLOs.json`)
- `deepghs/yolo-face` (YOLO11-face hub, the 2026 ecosystem pick per WebSearch) — licence tag **"other"** = unclear (`licences/hf_deepghs_yolo-face.json`)
- YOLO12-era models: per current community guidance, no accuracy win over YOLO11 for this task; no clean-licence hosting found — not pursued.

---

### 7. SAM — keep `sam_vit_b_01ec64.pth`; alternatives cost much and the loader can't take the new ones anyway

**Shipped, verified:** three live `SAMLoader`s (#88, #108, #160), all
`sam_vit_b_01ec64.pth` device AUTO; file sha256 `ec2df627…`. Canonical
source: Meta `segment-anything` — GitHub licence **Apache-2.0**
(`licences/github_segment-anything.json`); the HF mirror the script fetches
(`segments-arnaud/sam_vit_b`) carries no licence tag of its own
(`licences/hf_segments-arnaud_sam_vit_b.json`) — the Apache claim rides on
the upstream project, which also serves the identical file (the models/sams
comment in aiofm_setup.sh already documents Meta's bucket).

- **sam_vit_l / sam_vit_h**: 1,249,524,607 B / 2,564,550,879 B (HTTP HEAD
  against Meta's bucket this session). Same Apache-2.0. Expected effect on
  *this* graph: the SAMs only refine masks around detections that
  bbox-detectors already found, on large single faces — marginal.
  Cost: +0.9–2.2 GB download and VRAM. Not recommended without a demonstrated
  mask defect.
- **MobileSAM** (Apache-2.0, `licences/github_MobileSAM.json`): 10× smaller,
  drop-in name-detected by Impact. Only worth it if SAM load/VRAM ever shows
  up in profiling — UNVERIFIED that it does; the pod session can read it off
  history timings.
- **SAM2 / SAM3**: NOT loadable here — Impact Pack's `SAMLoader` enumerates
  `models/sams` and supports SAM1-family plus optional ESAM only (read from
  the pinned source, `modules/impact/impact_pack.py:108-148`). The `sam2/`
  and `sam3/` dirs on the pod belong to the video pipeline's other packs. A
  SAM2 move would be a graph rework (different provider nodes), not a swap:
  file it as an ambition, not a menu item.

**Recommendation:** keep vit_b. No change.

---

### 8. Free observation from the detector runs — the hands stage found nothing to do on every delivered frame

Both `hand_yolov8s` (shipped) and `hand_yolov9c` returned **zero hand
detections at conf ≥0.05 on all 14 delivered run3 frames** — and the default
composition (visually confirmed on the guard tap) frames the subject
waist-up with hands out of frame. FaceDetailer#92 (bbox_threshold 0.23)
therefore had no SEGS to work on in these renders; the hands pass ran as a
no-op. Not a currency defect — but it means (a) any effort spent on better
hand detectors is wasted at current default framing, and (b) the pod session
could measure what the idle hands pass still costs in load/VRAM/time and
whether an `ImpactIsNotEmptySEGS`-style guard (already used for the mouth)
should skip it explicitly. Raw evidence: `Q1/detectors/yolo_compare_raw.json`.

---

### 9. NMKD-Superscale — keep, with one conflicting flag on record

Shipped `4x_NMKD-Superscale-SP_178000_G.pth` (live ×1: `#615 → #593
ImageUpscaleWithModel`, whose 4× output ImageScaleBy#595 immediately lanczos-
rescales by 0.4 — net 1.6×, so this model contributes detail character, not
scale). Two API answers this session disagree:

- OpenModelDB `4x-NMKD-Superscale` — **WTFPL** (do-what-you-want; commercial
  fine), and its recorded sha256 **matches the shipped bytes exactly**
  (`licences/omdb/4x-NMKD-Superscale.json`). Author: nmkd.
- Civitai model 141491 (a third-party re-upload by "Samael1976") —
  `allowCommercialUse: []` (`licences/civitai_model_141491_NMKD_Superscale.json`,
  found via by-hash `licences/civitai_byhash_4x_NMKD-Superscale-SP_178000_G_pth.json`).

The author's own licence (WTFPL, byte-bound) governs; a re-uploader cannot
add restrictions to it. **Verdict: usable, keep** — but the conflict is now
on file for the owner's licence dossier. If the owner wants belt-and-braces,
`4x-LSDIR`/`4x-LSDIRplus` (CC-BY-4.0, same ESRGAN arch/size class, 67 MB,
`licences/omdb/4x-LSDIR*.json`) are the like-for-like replacements to A/B.

---

## Also on file (adjacent, handed to Track 1)

- **`upscale1.pth` in the mirror is a renamed `4x-UltraSharp` v1** — sha256
  `a5812231…` equals OpenModelDB's recorded hash for 4x-UltraSharp
  (`licences/omdb/4x-UltraSharp.json`): **CC-BY-NC-SA-4.0**. Not referenced
  by the NSFW graph; it is still fetched by a `dl "$REPO/upscale1.pth"` line
  in aiofm_setup.sh at 62acf44. Same NC class as item 1, hidden by the rename.
- `RealityGlass4x.pth` (sha256 `a4cd3a25…`, 9 MB): not referenced by the NSFW
  graph; provenance UNVERIFIED (not queried further — video-side scope).
- All Civitai by-hash responses, including the misses, are kept under
  `licences/civitai_byhash_*.json` so the negative results are re-checkable.

## What I could not verify (explicitly)

- Any render-seconds or visual delta for any swap above — needs the pod A/Bs
  (Q-PROTOCOL lock), which I did not run.
- How the shipping graph loads/flattens on frontend ≥1.47.11 (buyer-upgrade
  scenario) — untested here.
- The in-pipeline (mid-resolution) detector confidences — my numbers are on
  delivered 2688×3456 frames; cross-checked against run3's
  `yolo_confidences.json` (same frames, same model, 0.9015–0.9021 vs my
  0.9015–0.9028), so the testbed is consistent, but stage-input confidences
  for #607/#114 would need taps at those points.
- NMKD's WTFPL beyond OpenModelDB's record (nmkd's original page not fetched
  via an API this session) — flagged as a conflict rather than resolved.
