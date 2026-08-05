# SETUP.md — what packaging this graph will take

Reconciles the workflow's requirements against `aiofm_setup.sh` (1,644 lines,
video-pipeline only) and `INSTALL MODELS.txt`.

**Bottom line: the setup script installs none of the six custom-node packs this
graph needs, and does not fetch four models the live path requires.** Details
below, each traceable to a line number or a node id.

---

## 1. Node packs — resolved through the registry

Every repo below was resolved from the workflow's own `cnr_id` via
`api.comfy.org/nodes/<cnr_id>`, then the node names were checked against the
repository source at HEAD. No URL is guessed.

| `cnr_id` in the file | Repository | In `NODE_REPOS`? | Proposed pin |
|---|---|---|---|
| `comfyui-impact-pack` | `https://github.com/ltdrdata/ComfyUI-Impact-Pack` | **NO** | `429d0159ad429e64d2b3916e6e7be9c22d025c3c` |
| `comfyui-impact-subpack` | `https://github.com/ltdrdata/ComfyUI-Impact-Subpack` | **NO** | `50c7b71a6a224734cc9b21963c6d1926816a97f1` |
| `comfyui_controlnet_aux` | `https://github.com/Fannovel16/comfyui_controlnet_aux` | **NO** | `e8b689a513c3e6b63edc44066560ca5919c0576e` |
| `comfyui_ipadapter_plus` | `https://github.com/cubiq/ComfyUI_IPAdapter_plus` | **NO** | `a0f451a5113cf9becb0847b92884cb10cbdec0ef` |
| `comfyui_essentials` | `https://github.com/cubiq/ComfyUI_essentials` | **NO** | `9d9f4bedfc9f0321c19faf71855e228c93bd0dc9` |
| `comfyui_ultimatesdupscale` | `https://github.com/ssitu/ComfyUI_UltimateSDUpscale` | **NO** | `a5547db9e1d07d3318bb21e9e9c474f4c1e9c8df` |
| `rgthree-comfy` | `https://github.com/rgthree/rgthree-comfy` | **yes**, line 888 | already pinned `6b76ee6f2c5a007710b5a16f97c94330d6ecc871` |
| *(none)* | `ComfyUI_INSTARAW` — local folder | **no** (checked only, line 1623) | vendored, see §4 |

### Two corrections to the pack list in `CLAUDE.md`

Both were confirmed **from the workflow's own metadata**, then cross-checked
against repository source:

1. **`UltralyticsDetectorProvider` is in Impact _Subpack_, not Impact Pack.** All
   seven instances in this file carry
   `cnr_id: "comfyui-impact-subpack"`, `aux_id: "ltdrdata/ComfyUI-Impact-Subpack"`.
   Impact Pack's README states it outright at line 8. Installing only Impact Pack
   leaves **seven nodes unresolvable**.
2. **`MediaPipeFaceMeshToSEGS` is in Impact _Pack_, not `controlnet_aux`.** Node
   `#410` carries `cnr_id: "comfyui-impact-pack"`, `ver: "8.25.1"`. A `grep` of
   the controlnet_aux tarball at HEAD finds nothing. Only
   `MediaPipe-FaceMeshPreprocessor` (`#415`) and `DepthAnythingV2Preprocessor`
   (`#640`) come from controlnet_aux — both confirmed at
   `node_wrappers/mediapipe_face.py:34` and `node_wrappers/depth_anything_v2.py:50`.

### Why pin by SHA rather than by version

- **Four of the six repos publish no tags or releases at all** (controlnet_aux,
  IPAdapter_plus, essentials, UltimateSDUpscale). There is nothing to pin *to*
  except a SHA.
- Where tags exist they are **behind** the registry: Impact Pack HEAD is `8.28.3`
  but the last tag is `8.28`; Subpack HEAD is `1.3.5`, last tag `1.3.4`.
  Tag-pinning ships strictly older code than the registry serves.
- Version strings are not unique. UltimateSDUpscale HEAD and registry both say
  `1.7.2`, but HEAD is three months newer and adds a node.

This matches the existing script's own convention — `NODE_REPOS` is already
`<url>|<40-char sha>` (line 879) with all 12 entries pinned to full SHAs.

### One hard minimum, verified

**UltimateSDUpscale must be pinned no older than ~2026-02-08.** Both
`UltimateSDUpscale` nodes in this file (`#98`, `#617`) carry **21**
`widgets_values`, ending in `batch_size = 1`. `batch_size` was added around commit
`fe0196319f19`; before that the widget list was one shorter. **Pinning older
desyncs both nodes** — and this is the real instance of the `widgets_values` trap
in this project, just on a third-party node rather than a subgraph host.

### Two risks worth stating plainly

- **`cubiq/ComfyUI_essentials` and `cubiq/ComfyUI_IPAdapter_plus` are both in
  declared maintenance-only mode** (identical README banners dated 2025-04-14).
  Neither is archived and neither names a replacement. `ImageColorMatch+` is used
  three times on the live path. For something you intend to sell, two unmaintained
  dependencies deserve a conscious decision.
- **Impact Subpack + PyTorch ≥2.6 `weights_only`.** The Subpack README documents
  that unsafe-but-trusted `.pt` files must be whitelisted in
  `<user_directory>/default/ComfyUI-Impact-Subpack/model-whitelist.txt`. Your
  three custom detectors — `lips_v1.pt`, `nipple.pt`, `pussyV2.pt` — are exactly
  that case. **Expect this to bite on a fresh pod.** Add the whitelist file to the
  install script.

---

## 2. Models — reconciled against what the script already fetches

Every filename on the left is read from a `widgets_values` in the workflow. Line
numbers on the right are `aiofm_setup.sh`.

### Live path — required

| Model | Directory | Used by | In script? |
|---|---|---|---|
| `SDXLNSFW.safetensors` | `checkpoints/` | `#613` | ✅ 762 |
| `zimage.safetensors` | `diffusion_models/` | `#113` | ✅ 781 |
| `qwen.safetensors` | `text_encoders/` | `#110` | ✅ 824 |
| **`ae.safetensors`** | `vae/` | `#109` | ❌ **not named** |
| `dmd2_sdxl_4step_lora_fp16.safetensors` | `loras/` | `#610`, `#97` | ✅ 802 |
| `4x-UltraSharpV2.pth` | `upscale_models/` | `#612`, `#100` | ✅ 850 |
| `4x_NMKD-Superscale-SP_178000_G.pth` | `upscale_models/` | `#615` | ✅ 851 |
| `x1_ITF_SkinDiffDetail_Lite_v1.pth` | `upscale_models/` | `#90` | ✅ 854 |
| **`bbox/face_yolov8m.pt`** | `ultralytics/bbox/` | `#611`,`#107`,`#426` | ❌ **missing** |
| **`bbox/hand_yolov8s.pt`** | `ultralytics/bbox/` | `#89` | ❌ **missing** |
| `bbox/lips_v1.pt` | `ultralytics/bbox/` | `#161` | ✅ 833 → hardlinked 838-844 |
| **`sam_vit_b_01ec64.pth`** | **`sams/`** | `#88`,`#108`,`#160` | ❌ **missing, and the directory is never created** |

### Dead path — only needed if `PROPOSALS.md` P12 revives it

| Model | Directory | Used by | In script? |
|---|---|---|---|
| `bbox/nipple.pt` | `ultralytics/bbox/` | `#171` (sg5) | ✅ 834 |
| `bbox/pussyV2.pt` | `ultralytics/bbox/` | `#246` (sg5) | ✅ 835 |
| `DetailedNipples.safetensors` | `loras/` | `#174` (sg5) | ✅ 801 |
| `controlnet-union-sdxl-promax.safetensors` | `controlnet/` | `#639` (sg6) | ❌ missing |
| `depth_anything_v2_vitl.pth` | controlnet_aux's own dir | `#640` (sg6) | ❌ missing |
| IPAdapter `PLUS FACE (portraits)` models | `ipadapter/` | `#644` (sg6) | ❌ missing, dir never created |

**So the dead sg5 path is fully provisioned while the live path is missing four
models.** That is a strong practical argument for `PROPOSALS.md` P12's delete
recommendation on the ControlNet/IPAdapter side, and for reviving sg5 being cheap
if you want it — the models are already there.

### Four missing directories

The script creates `models/ultralytics/bbox` (line 838) and, incidentally,
`models/clip_vision` (via `dl()`'s `mkdir -p`, line 688). It **never creates**:

- **`models/sams`** — Impact Pack's `SAMLoader` reads only from here
  (`modules/impact/impact_pack.py:51` registers `"sams"` → `models/sams`;
  README line 404). Three live `SAMLoader` nodes will find nothing.
- **`models/ultralytics/segm`** — Impact Subpack registers it
  (`subpack_nodes.py:9-11`). Not strictly required by this graph, since all seven
  detectors use `bbox/`, but the Subpack expects the directory to exist.
- `models/ipadapter`, `models/controlnet` — dead path only.

### `ae.safetensors` — the one I could not settle

The script's `vae/` fetches are `flux2-vae.safetensors`, `GlassRoot_D2.safetensors`
and `variational_encoder_primary.safetensors` (lines 860-862). None is
`ae.safetensors`.

**But this may still land.** Lines 584-611 do a bulk
`hf download msit270/AIOFM-Pack --include "models/*"` under the default
`PROFILE=all`, which deposits whatever that private repo's `models/` tree
contains. I cannot see inside that repo from here.

Note also that the script uses codename-style filenames that span folders
(`GlassRoot_D2` is a VAE, `EchoVault_T9` a text encoder), so **you cannot infer a
file's identity from its name** — `variational_encoder_primary.safetensors` could
plausibly *be* the Z-Image `ae`, renamed.

**Action for the pod session:** run `ls models/vae/` after setup and check whether
`ae.safetensors` exists. If not, either add an explicit `dl` line or change `#109`
to point at whichever file is the Z-Image autoencoder. **Do not assume either
way.** Same check for `face_yolov8m.pt` and `hand_yolov8s.pt` in
`models/ultralytics/bbox/`, which are common enough that the bulk pull may well
include them.

---

## 3. ComfyUI core and frontend versions

**Core floor is `0.3.70`, not `0.3.66`.** The script's `COMFY_MIN="0.3.66"`
(line 513) is a hard `die()`. But this workflow contains `#614 PrimitiveBoolean`
with `cnr_id: "comfy-core"`, `ver: "0.3.70"` — the highest core version in the
file. **Raise `COMFY_MIN` to `0.3.70` for the NSFW profile**, or confirm
`PrimitiveBoolean` exists at 0.3.66 and leave it.

**Keep the frontend pin at 1.39.19** (line 550). The script's own rationale
(lines 463-491) names three open upstream bugs on 1.47.x, and **all three are
subgraph/promoted-widget bugs**:

- exposed-widget visibility toggles
- promoted STRING widget edits not written back to the interior node
- null entries in a subgraph host's `widgets_values` loading as `undefined`

This graph has **seven subgraph hosts** — twice the video pipeline's exposure.
The pin is more load-bearing here than where it was written. Do not relax it.

*(Note: this graph promotes no widgets at all — see `MAP.md` §0 — so the second
and third bugs cannot bite it today. They would the moment anyone promotes one.)*

---

## 4. Where `ComfyUI_INSTARAW` needs to go

**Destination:** `$COMFYUI_DIR/custom_nodes/ComfyUI_INSTARAW/`

The script currently only *checks* for it and prints a "still to do" line if
absent (lines 1619-1624). It never clones, copies, or installs it.

**It cannot be added to `NODE_REPOS`.** That array is `<url>|<sha>`, and this pack
has no public URL: no `pyproject.toml`, no `cnr_id`, no LICENSE, no git remote in
this folder. Its own node metadata gives `aux_id: "instara-io/ComfyUI_INSTARAW"`
and `ver: "12afb909b3380bd4a3f118061654dd72d1edcd4c"` (node `#645`), implying a
private repository. A buyer-facing script cannot clone a private repo — which is
presumably why `INSTALL MODELS.txt` step 3 tells the buyer to drag the folder in
by hand.

**Recommendation: vendor it.** Ship the folder inside the distribution archive and
have the script `cp -r` it into `custom_nodes/`, guarded by an existence check so
re-runs stay idempotent. Record `12afb909…` as the provenance marker in the
install log.

### ⚠️ Do **not** run its `requirements.txt` unfiltered

This is the sharpest packaging hazard in the whole job (`AUDIT.md` A17).

- `numpy==1.26.4` (line 63) — a hard pin that **downgrades numpy for the entire
  ComfyUI environment**.
- `opencv-contrib-python==4.10.0.84` (line 73) — the **non-headless** build, while
  `comfyui_controlnet_aux` (which this graph requires) installs the headless one.
  Mixing the two distributions in one env is a known breakage.
- Lines 29-98 are a **verbatim paste of MediaPipe's pip-compile lockfile**, header
  comment included — `jax`, `sounddevice`, `matplotlib`, `sentencepiece` and other
  build deps that have nothing to do with this pack.
- `mediapipe==0.10.14` (line 102) is pinned "for compatibility with
  comfyui_controlnet_aux", yet **mediapipe is imported by zero files in this pack**.

The script already has the right machinery: `NODE_DEP_SKIP` (line 996) filters
`torch|torchvision|torchaudio|onnxruntime|onnxruntime-gpu` out of every pack's
requirements for exactly this reason. **Extend that regex with `numpy` and
`opencv-contrib-python`**, and route INSTARAW's requirements through
`install_node_deps()` rather than a bare `pip install -r`.

Note `INSTALL MODELS.txt` step 4 currently instructs the buyer to run
`pip install -r ComfyUI_INSTARAW/requirements.txt` **directly** — that is the
unfiltered path, and it is what the documentation tells them to do today.

### One more dependency pip cannot supply

`pyexiftool` (requirements line 27) needs the **exiftool binary on `PATH`**.
`nodes/output_nodes/save_with_metadata.py:132` and
`synthesize_with_metadata.py:404` shell out to it. Neither of those nodes is used
by this workflow, so it is not blocking — but if the "authentic metadata" feature
is part of the product, the install needs `apt-get install -y libimage-exiftool-perl`.

---

## 5. `INSTALL MODELS.txt` is stale in three places

| Step | Says | Actually |
|---|---|---|
| 1 | Three files "will need to be moved to the bbox holder" | The script **already hardlinks** every `.pt` from `models/ultralytics/` into `bbox/` (lines 838-844). Redundant. |
| 1 | Names them `lipsv1`, `pussy2`, `nipple` | Real filenames are `lips_v1.pt`, `pussyV2.pt`, `nipple.pt`. A buyer searching literally finds nothing. |
| 4 | `pip install -r ComfyUI_INSTARAW/requirements.txt` | Unfiltered — see the numpy/opencv hazard above. |
| 8 | "Download nodes (Install Missing Custom Nodes)" via Manager | The setup script **explicitly warns buyers away from Manager** (lines 1439-1442) because it moves the pins. These two documents contradict each other. |
| 10 | "Watch the video guide in the folder" | There is no video in this folder, and per `CLAUDE.md` the guide predates the current workflow. |

Step 7 refers to "the 10.OFM Tech NSFW++ workflow", while the file here is
`OFMTech_NSFW.json`. Worth reconciling the naming before sale.

---

## 6. Suggested order of work for packaging

1. **Fix `AUDIT.md` A0 first.** Shipping a graph that renders an empty prompt at
   seed 0 on a fresh load makes every other packaging step moot.
2. Add the six repos to `NODE_REPOS` with the SHAs in §1.
3. Add `mkdir -p models/sams models/ultralytics/segm`.
4. Resolve `ae.safetensors`, `face_yolov8m.pt`, `hand_yolov8s.pt` — check the bulk
   pull first, add explicit `dl` lines only for what is genuinely absent.
5. Vendor `ComfyUI_INSTARAW`; extend `NODE_DEP_SKIP` with `numpy` and
   `opencv-contrib-python`.
6. Add the Impact Subpack `model-whitelist.txt` for the three custom `.pt`
   detectors.
7. Raise `COMFY_MIN` to `0.3.70` (or verify 0.3.66 suffices).
8. Extend the script's existing workflow-derived node check (lines 1371-1400 —
   it already walks `definitions.subgraphs` and skips UUID-typed hosts) to cover
   this graph. That logic is directly reusable as written.
9. Rewrite `INSTALL MODELS.txt` against §5.
10. Decide the `AUDIT.md` A16 (wildcard CORS) and A18 (no LICENSE) questions
    **before** anything ships.
