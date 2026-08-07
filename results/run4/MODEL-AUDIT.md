# MODEL-AUDIT — msit270/AIOFM-Pack, run 4 (2026-08-07)

Every flag in this file was read from an API response fetched **this session**
and stored under `results/run4/`. Nothing is quoted from memory or from any
prior audit document. Response-file paths below are relative to
`results/run4/`.

## Counts (the brief said "76 files"; these are the real numbers)

The live tree (`hf_tree_before.json`, fetched 2026-08-07) holds **77 files**:

- **43 LFS binaries under `models/`** — 42 unique contents
  (`SDXLNSFW.safetensors` sits at two paths with the same sha256).
- **11 config YAMLs** under `models/configs/`.
- **20 zero-byte `put_*_here` placeholders** under `models/`.
- Root `.gitattributes` (1,607 B).
- **2 LFS tarballs under `dist/`** (`AIOFMTech-NSFW.tar.gz`,
  `AIOFMTech-Video.tar.gz`) — the owner's own packaged products, not
  third-party models; the video one is analysed in the overlap section.

So `models/` itself contains 74 files: 43 binaries + 11 configs + 20
placeholders.

## Method and anomalies (read before trusting any row)

1. **Identity = hash, not name.** Primary: full SHA256 (`lfs.oid` from the
   live tree) → `civitai.com/api/v1/model-versions/by-hash/`. Misses →
   candidate HF repos, verified by exact `lfs.oid` match against the
   candidate's tree JSON (stored under `hf/`). Name-only matches are marked
   as such and are **not** identification.
2. **Sandbox redaction anomaly (recorded, worked around).** The HF tree
   responses for exactly three repos — `black-forest-labs/FLUX.1-schnell`,
   `black-forest-labs/FLUX.2-klein-9B`, `facebook/sam3` — arrived with every
   `lfs.oid`/`xetHash` value replaced by asterisks by this sandbox's response
   filter (files stored as received; reproduced with and without auth). For
   those three, identity was proven instead by **git pointer-blob equality**:
   the tree's 40-hex `oid` is the SHA1 of the LFS pointer file, whose content
   is exactly `oid sha256:<hash>` + `size <n>`; equal pointer blob ⇒ equal
   sha256 and size. Byte sizes also match exactly. Rows using this say
   `hf-oid (git-pointer)`.
3. **Civitai sweep:** 41 unique un-audited hashes queried (2s spacing), 27
   hits / 14 misses; all misses were clean HTTP 404 ("no file with that
   hash"), logged in `civitai/_sweep_misses.json`. No call needed the API
   key (no 401/429 seen).
4. **Re-uploads vs canonical:** several Civitai hits are third-party
   re-uploads of standard files (e.g. `clip_l` matched inside a stranger's
   bundle). Where the same bytes were oid-proven in the canonical HF repo,
   the canonical repo's licence governs the row; re-uploader flags are noted
   only where relevant.
5. **Gated licence texts:** `facebook/sam3` and `FLUX.2-klein-9B` LICENSE
   files are behind their gates — raw fetch returned "Access … is
   restricted" (that failure is itself evidence of gating). The SAM licence
   text was obtained from the public GitHub mirror
   (`external/gh_facebookresearch_sam3_LICENSE.txt`, via
   `api.github.com/repos/facebookresearch/sam3/license`).
6. **openmodeldb.info API endpoints return 404 HTML** (stored:
   `external/openmodeldb_models.json`). Its data was read instead from the
   OpenModelDB GitHub repo (`external/omdb_*.json`) — those entries carry
   full SHA256s, so three upscalers are **hash**-matched there, not
   name-matched.
7. "Graph use" below comes from walking every widget string in the two
   shipped workflow JSONs (`OFMTech-NSFW/OFMTech_NSFW.json`; the video
   workflow extracted from the published tarball) plus a node-mode check
   (mode 0 = live) for every flagged NSFW loader. Deeper dataflow was not
   traced.
8. Local files were not re-hashed except the video tarball
   (sha256 `343619dc…` == its `lfs.oid` — download integrity confirmed).

Civitai `allowCommercialUse` legend: `Image` = sell generated images,
`RentCivit` = on-Civitai generation, `Rent` = other hosted generation
services, `Sell` = sell/redistribute the model itself. **No `Sell` ⇒ the
flags do not permit redistributing the file in a pack the owner sells.**

---

## A. The 43 LFS binaries under `models/`

Verdicts: **CLEAN** = CLEAN-REDISTRIBUTABLE; **ENC** = ENCUMBERED;
**GATED** = GATED-LICENCE (source licence forbids/conditions redistribution,
flux-dev style); **UNKNOWN**/**UNIDENTIFIED** as defined in the brief.

### models/checkpoints

| path | size | sha256 | identified as | method | source | licence / flags | response files | verdict | graph use |
|---|---|---|---|---|---|---|---|---|---|
| SDXLNSFW.safetensors | 6.94 GB | d234c60d67ce | LUSTIFY! [NSFW checkpoint], version **GGWP (V7)** (model 573152, version 2155386), upstream `lustifyNSFWCheckpoint_ggwpV7.safetensors`, creator coyotte | civitai-hash (prior, cited) | civitai.com/models/573152 | allowCommercialUse=`['RentCivit','Image']` (no Sell/Rent), allowDerivatives=False, allowDifferentLicense=False, allowNoCredit=True, availability=Public; version `licensingFee: 1` | `civitai/sdxlnsfw_by_hash.json`, `civitai/lustify_model_573152.json` | **ENC** — flags do not permit selling/redistributing the model | **NSFW LIVE** (CheckpointLoaderSimple #613, mode 0) |
| v1-5-pruned-emaonly-fp16.safetensors | 2.13 GB | e9476a13728c | Stable Diffusion v1.5, pruned ema-only fp16 (same upstream filename) | hf-oid | Comfy-Org/stable-diffusion-v1-5-archive | `license:creativeml-openrail-m`, gated=False | `hf/Comfy-Org_stable-diffusion-v1-5-archive_tree.json`, `..._meta.json` | **CLEAN** with condition — OpenRAIL-M permits redistribution but requires the licence + use restrictions to accompany the weights; the repo attaches neither | neither workflow (E3 re-confirmed) |

### models/clip_vision, models/detection

| path | size | sha256 | identified as | method | source | licence / flags | response files | verdict | graph use |
|---|---|---|---|---|---|---|---|---|---|
| IronSight_V7.safetensors | 1.26 GB | 64a7ef761bfc | **Wan 2.1 CLIP-Vision H** = `split_files/clip_vision/clip_vision_h.safetensors` | hf-oid; also civitai-hash to CivitaiOfficial "Wan Video 2.1" v1501088 | Comfy-Org/Wan_2.1_ComfyUI_repackaged | Comfy-Org repo declares **no licence tag**; Wan 2.1 family Apache-2.0 (Wan-AI/Wan2.1-I2V-14B-720P `license:apache-2.0`); CivitaiOfficial flags incl `Sell` | `hf/Comfy-Org_Wan_2.1_ComfyUI_repackaged_tree.json` + `_meta.json`, `hf/Wan-AI_Wan2.1-I2V-14B-720P_meta.json`, `civitai/IronSight_V7_by_hash.json`, `civitai/model_1329096.json` | **CLEAN** (note: distributing repo untagged; licence evidence is family-level) | video LIVE |
| vitpose_h_wholebody_data.bin | 2.55 GB | f6a9e7cb3a87 | ViTPose-H wholebody ONNX external-data blob, `onnx/vitpose_h_wholebody_data.bin` | hf-oid | Kijai/vitpose_comfy | `license:apache-2.0` | `hf/Kijai_vitpose_comfy_tree.json`, `..._meta.json` | **CLEAN** | video LIVE (sidecar of the .onnx) |
| vitpose_h_wholebody_model.onnx | 420 KB | f21466cd6c93 | ViTPose-H wholebody ONNX graph, same repo | hf-oid | Kijai/vitpose_comfy | `license:apache-2.0` | same | **CLEAN** | video LIVE |
| yolov10m.onnx | 61.7 MB | 89b526498a6d | YOLOv10-M ONNX exactly as shipped in Wan2.2-Animate's preprocess kit (`process_checkpoint/det/yolov10m.onnx`) | hf-oid | Wan-AI/Wan2.2-Animate-14B | repo `license:apache-2.0`; upstream YOLOv10 project THU-MIG/yolov10 is **AGPL-3.0** (GitHub API) — factual note, the distributing repo tags Apache | `hf/Wan-AI_Wan2.2-Animate-14B_tree.json` + `_meta.json`, `external/gh_THU-MIG_yolov10_license.json` | **CLEAN** (with the AGPL-lineage note on record) | video LIVE |

### models/diffusion_models

| path | size | sha256 | identified as | method | source | licence / flags | response files | verdict | graph use |
|---|---|---|---|---|---|---|---|---|---|
| High.safetensors | 14.53 GB | f1a2e7b4b65f | **DaSiWa WAN 2.2 I2V 14B "Lightspeed" — SynthSeduction High v9** (model 1981116, version 2555640), upstream `DasiwaWAN22I2V14BLightspeed_synthseductionHighV9.safetensors`, baseModel "Wan Video 2.2 I2V-A14B", creator Darksidewalker | civitai-hash | civitai.com/models/1981116 | commercial=`['RentCivit','Image']` (no Sell/Rent), deriv=**False**, diffLic=**False**, noCredit=**False** | `civitai/High_by_hash.json`, `civitai/model_1981116.json` | **ENC** — a fine-tune whose flags do not permit redistribution, with credit required | neither workflow |
| HyperFleshUltrav4.safetensors | 11.90 GB | 4e675980ea77 | **UltraReal Fine-Tune v4** (model 978314, version 1413133), upstream `ultrarealFineTune_v4.safetensors`, baseModel "Flux.1 D", creator Danrisi | civitai-hash | civitai.com/models/978314 | commercial=`['Image','RentCivit','Rent','Sell']`, deriv=False, diffLic=True, noCredit=**False** (credit required) | `civitai/HyperFleshUltrav4_by_hash.json`, `civitai/model_978314.json` | **ENC (conditional)** — `Sell` is granted but credit is required and not given; baseModel is FLUX.1-dev, whose own non-commercial licence vs these flags is a lawyer call, recorded not resolved | neither workflow |
| Low.safetensors | 14.53 GB | ae436c2d8c8d | **SynthSeduction Low v9** (same model 1981116, version 2555652) | civitai-hash | as High | as High | `civitai/Low_by_hash.json`, `civitai/model_1981116.json` | **ENC** | neither workflow |
| SDXLNSFW.safetensors | 6.94 GB | d234c60d67ce | duplicate path of the checkpoints row — same sha256, one file, two locations | — | — | see checkpoints row | same | **ENC** | NSFW LIVE (via checkpoints copy) |
| Z-TurboSkinForge.safetensors | 6.15 GB | c7c0c6816746 | **Z-epiCRealism, Turbo V1 (fp8)** (model 2305301, version 2593828), upstream `zEpicrealism_turboV1Fp8.safetensors`, baseModel ZImageTurbo, creator epinikion | civitai-hash | civitai.com/models/2305301 | commercial=`['RentCivit','Rent']` — **no `Image`, no `Sell`**; deriv=**False**; diffLic=True; noCredit=**False** | `civitai/Z-TurboSkinForge_by_hash.json`, `civitai/model_2305301.json` | **ENC (hard)** — flags permit neither redistribution nor even commercial use of images | neither workflow |
| flux-2.safetensors | 18.16 GB | 0975d6b77b5f | **FLUX.2 [klein] 9B** = `flux-2-klein-9b.safetensors` | hf-oid (git-pointer) + civitai-hash (CivitaiOfficial mirror v2612554) | black-forest-labs/FLUX.2-klein-9B | `license:other`, **license_name `flux-non-commercial-license`**, **gated=auto**; LICENSE.md itself not fetchable without accepting the gate (failure stored) | `hf/black-forest-labs_FLUX.2-klein-9B_tree.json` + `_meta.json`, `civitai/flux-2_by_hash.json`, `civitai/model_2322332.json` | **GATED** — BFL non-commercial licence, redistributed here ungated | neither workflow |
| flux4b.safetensors | 7.75 GB | ec3d4e733a77 | **FLUX.2 [klein] 4B** = `flux-2-klein-4b.safetensors` | hf-oid + civitai-hash (v2612557) | black-forest-labs/FLUX.2-klein-4B | `license:apache-2.0`, gated=False | `hf/black-forest-labs_FLUX.2-klein-4B_tree.json` + `_meta.json`, `civitai/flux4b_by_hash.json` | **CLEAN** | neither workflow |
| wan2.2_animate_14B_bf16.safetensors | 34.55 GB | 7d37cb012048 | **Wan 2.2 Animate 14B bf16**, Comfy-Org split file (same upstream filename) | hf-oid + civitai-hash (mirror 1974861) | Comfy-Org/Wan_2.2_ComfyUI_Repackaged | Comfy-Org repo **no licence tag**; Wan-AI/Wan2.2-Animate-14B `license:apache-2.0` | `hf/Comfy-Org_Wan_2.2_ComfyUI_Repackaged_tree.json` + `_meta.json`, `hf/Wan-AI_Wan2.2-Animate-14B_meta.json`, `civitai/wan2.2_animate_14B_bf16_by_hash.json` | **CLEAN** | video LIVE |
| zimage.safetensors | 12.31 GB | 2407613050b8 | **Z-Image-Turbo bf16** = `split_files/diffusion_models/z_image_turbo_bf16.safetensors` (STATE.md's claim re-verified by oid this session) | hf-oid + civitai-hash (CivitaiOfficial 2168935) | Comfy-Org/z_image_turbo | Comfy-Org repo **no licence tag**; upstream Tongyi-MAI/Z-Image-Turbo `license:apache-2.0` | `hf/Comfy-Org_z_image_turbo_tree.json` + `_meta.json`, `hf/Tongyi-MAI_Z-Image-Turbo_meta.json`, `civitai/zimage_by_hash.json` | **CLEAN** | **NSFW LIVE** (UNETLoader #113) |

### models/loras

| path | size | sha256 | identified as | method | source | licence / flags | response files | verdict | graph use |
|---|---|---|---|---|---|---|---|---|---|
| DetailedNipples.safetensors | 913 MB | baa378f5766d | **Detailed nipples XL v1.0** (model 328932, version 368603, creator graam558) | civitai-hash | civitai.com/models/328932 | commercial=`['RentCivit','Image']` (no Sell/Rent), deriv=True, diffLic=True, noCredit=True | `civitai/DetailedNipples_by_hash.json`, `civitai/model_328932.json` | **ENC** — no redistribution right | neither workflow (sg-anatomy path is dead) |
| FrostByte_K7.safetensors | 1.23 GB | 024f21de095b | **Wan2.2-Lightning I2V-A14B-4steps LoRA rank64 Seko-V1, low-noise** (`low_noise_model.safetensors`) | hf-oid (two repos) | lightx2v/Wan2.2-Lightning (author) + Comfy-Org Wan2.2 repack mirror | lightx2v repo `license:apache-2.0` | `hf/lightx2v_Wan2.2-Lightning_tree.json` + `_meta.json`, `civitai/FrostByte_K7_by_hash.json` | **CLEAN** | video LIVE |
| NovaMind_X1.safetensors | 858 MB | 0e6ac56c8906 | **Wan2.2-Fun-A14B-InP low-noise MPS reward LoRA** (`Wan2.2-Fun-A14B-InP-low-noise-MPS.safetensors`) | hf-oid | alibaba-pai/Wan2.2-Fun-Reward-LoRAs | `license:apache-2.0` (the Civitai re-list 1953737 by a non-author claims `['RentCivit']` only — the author repo governs; both stored) | `hf/alibaba-pai_Wan2.2-Fun-Reward-LoRAs_tree.json` + `_meta.json`, `civitai/NovaMind_X1_by_hash.json`, `civitai/model_1953737.json` | **CLEAN** | video LIVE |
| PhantomWeave_R5.safetensors | 4.91 GB | a510b5562e05 | **Pusa V1 LoRA 14B rank512 bf16** (Kijai conversion, `Pusa/Wan21_PusaV1_LoRA_14B_rank512_bf16.safetensors`) | hf-oid | Kijai/WanVideo_comfy | Kijai repo **no licence tag**; upstream RaphaelLiu/PusaV1 `license:apache-2.0` | `hf/Kijai_WanVideo_comfy_tree.json` + `_meta.json`, `hf/RaphaelLiu_PusaV1_meta.json` | **CLEAN** | video LIVE |
| SolarFlint_L2.safetensors | 1.44 GB | 5f4b6b9d3bc7 | **Wan2.2-Animate relight LoRA bf16** (`split_files/loras/wan2.2_animate_14B_relight_lora_bf16.safetensors`) | hf-oid | Comfy-Org/Wan_2.2_ComfyUI_Repackaged | Comfy-Org **no licence tag**; the relight LoRA is part of Wan-AI/Wan2.2-Animate-14B (`relighting_lora.ckpt` present in that Apache-2.0 repo) | `hf/Comfy-Org_Wan_2.2_ComfyUI_Repackaged_tree.json`, `hf/Wan-AI_Wan2.2-Animate-14B_meta.json` | **CLEAN** | video LIVE |
| VelvetPores_Flux.safetensors | 76.7 MB | da97701b932c | **"Photorealistic Skin ⛔️ No plastic [FLUX]" v0.1** (model 1157318, version 1301668, creator AIDigitalMediaAgency) | civitai-hash | civitai.com/models/1157318 | commercial=`['Image','RentCivit']` (no Sell/Rent), deriv=**False**, diffLic=**False**, noCredit=True | `civitai/VelvetPores_Flux_by_hash.json`, `civitai/model_1157318.json` | **ENC** — no redistribution right | neither workflow |
| VelvetRush_Q4.safetensors | 2.50 GB | 0bda20598ece | **lightx2v T2V-14B cfg-step-distill v2 LoRA rank256 bf16** (Kijai conversion, `Lightx2v/lightx2v_T2V_14B_cfg_step_distill_v2_lora_rank256_bf16.safetensors`) | hf-oid | Kijai/WanVideo_comfy | Kijai **no licence tag**; upstream lightx2v/Wan2.1-T2V-14B-StepDistill-CfgDistill `license:apache-2.0` | `hf/Kijai_WanVideo_comfy_tree.json`, `hf/lightx2v_Wan2.1-T2V-14B-StepDistill-CfgDistill_meta.json` | **CLEAN** | video LIVE |
| dmd2_sdxl_4step_lora_fp16.safetensors | 394 MB | b3d9173815a4 | **DMD2 SDXL 4-step LoRA fp16** (same upstream filename) | hf-oid (+ a non-author civitai re-list 1608870) | tianweiy/DMD2 | **`license:cc-by-nc-4.0`** (re-verified from the HF API this session); the civitai re-list's permissive flags cannot override the author's licence; its version carries `licensingFee: 1` | `hf/tianweiy_DMD2_tree.json` + `_meta.json`, `civitai/dmd2_sdxl_4step_lora_fp16_by_hash.json`, `civitai/model_1608870.json` | **ENC** — non-commercial licence | neither workflow (NSFW graph: zero references; video graph: zero references; only the video **setup** fetches it, see §C) |
| primary_net_v2.safetensors | 170 MB | 1fd3c728ade7 | **z-image-turbo-flow-dpo v1.0** (model 2420939, version 2721846, creator fok3827) | civitai-hash | civitai.com/models/2420939 | commercial incl `Sell`, deriv=True, diffLic=**False** (same-licence flow-down), noCredit=True | `civitai/primary_net_v2_by_hash.json`, `civitai/model_2420939.json` | **CLEAN** with flow-down condition | neither workflow |
| x_gen_weights.safetensors | 170 MB | fd679d15ba83 | **Realistic Snapshot (Z-Image-Turbo + Krea 2), ZIT v3.5 PHOTOREALISM** (model 2268008, version 2600004, creator MonkeyForever) | civitai-hash | civitai.com/models/2268008 | commercial=`['Image','RentCivit','Rent','Sell']`, deriv=True, diffLic=True, noCredit=True | `civitai/x_gen_weights_by_hash.json`, `civitai/model_2268008.json` | **CLEAN** | neither workflow |

### models/sam3, models/text_encoders

| path | size | sha256 | identified as | method | source | licence / flags | response files | verdict | graph use |
|---|---|---|---|---|---|---|---|---|---|
| sam3.pt | 3.45 GB | 9999e2341cee | **Meta SAM 3 checkpoint** (`sam3.pt`, byte-size also exact) | hf-oid (git-pointer) | facebook/sam3 | `license:other` (**SAM License**), **gated=manual**; licence text (GitHub API copy): distribution of SAM Materials or derivatives allowed "only … under the terms of this Agreement and you shall provide a copy of this Agreement" | `hf/facebook_sam3_tree.json` + `_meta.json`, `external/gh_facebookresearch_sam3_LICENSE.txt`; gated-fetch failure recorded; the civitai re-upload "samsan" (2231845, commercial=`[]`) is a stranger's copy, stored for completeness | **GATED** — redistribution is conditioned (agreement copy + flow-down) and the source is manually gated; the pack ships it bare | neither workflow |
| EchoVault_T9.safetensors | 11.36 GB | 4fa971faf306 | **UMT5-XXL text encoder, bf16** (Kijai `umt5-xxl-enc-bf16.safetensors`, the Wan text encoder) | hf-oid | Kijai/WanVideo_comfy | Kijai **no licence tag**; Wan family Apache-2.0 (Wan-AI metas); the civitai bundle (1295569) listing these bytes flags Image/RentCivit/Rent, deriv=True | `hf/Kijai_WanVideo_comfy_tree.json` + `_meta.json`, `civitai/EchoVault_T9_by_hash.json`, `civitai/model_1295569.json` | **CLEAN** (family-level licence evidence) | video LIVE |
| TitanFP8.safetensors | 4.89 GB | 7d330da48161 | **T5-XXL fp8_e4m3fn** (`t5xxl_fp8_e4m3fn.safetensors`) | hf-oid | comfyanonymous/flux_text_encoders | `license:apache-2.0` | `hf/comfyanonymous_flux_text_encoders_tree.json` + `_meta.json`, `civitai/TitanFP8_by_hash.json` | **CLEAN** | neither workflow |
| clip_l.safetensors | 246 MB | 660c6f5b1aba | **CLIP-L text encoder** (`clip_l.safetensors`; the civitai by-hash hit lands in a stranger's "LunaR - v2" bundle — re-upload, noted only) | hf-oid | comfyanonymous/flux_text_encoders | `license:apache-2.0` | same tree/meta, `civitai/clip_l_by_hash.json`, `civitai/model_2644014.json` | **CLEAN** | neither workflow |
| qwen-4b-zimage-heretic-q8.gguf | 4.28 GB | 70af2493307e | **Heretic-abliterated Qwen3-4B Z-Image text encoder, Q8 GGUF** (same filename) | hf-oid | Lockout/qwen3-4b-heretic-zimage | `license:apache-2.0` (base Qwen/Qwen3-4B also `license:apache-2.0`) | `hf/Lockout_qwen3-4b-heretic-zimage_tree.json` + `_meta.json`, `hf/Qwen_Qwen3-4B_meta.json` | **CLEAN** | neither workflow (installed by the script; not named in either workflow JSON) |
| qwen.safetensors | 8.04 GB | 6c671498573a | **Qwen3-4B text encoder for Z-Image** (`split_files/text_encoders/qwen_3_4b.safetensors`) | hf-oid + civitai-hash (CivitaiOfficial 2168935) | Comfy-Org/z_image_turbo | Comfy-Org **no licence tag**; Qwen/Qwen3-4B `license:apache-2.0` | `hf/Comfy-Org_z_image_turbo_tree.json`, `hf/Qwen_Qwen3-4B_meta.json`, `civitai/qwen_by_hash.json` | **CLEAN** | **NSFW LIVE** (CLIPLoader #110) |
| umt5.safetensors | 6.74 GB | c3355d30191f | **UMT5-XXL fp8_e4m3fn_scaled** (`umt5_xxl_fp8_e4m3fn_scaled.safetensors`, present identically in both Comfy-Org Wan repos) | hf-oid (two repos) | Comfy-Org Wan 2.1 + 2.2 repackaged | both repos **no licence tag**; Wan family Apache-2.0 | both Comfy-Org trees + metas, `civitai/umt5_by_hash.json` | **CLEAN** | neither workflow |

### models/ultralytics (all three: no Civitai by-hash hit — clean 404s)

| path | size | sha256 | identified as | method | source | licence / flags | response files | verdict | graph use |
|---|---|---|---|---|---|---|---|---|---|
| lips_v1.pt | 6.2 MB | ce9fe145352a | **IDENTIFIED (orchestrator, after this table was drafted): "ADetailer (After Detailer) Lips Model"**, Civitai model **142240**, version **157700**, creator mooseh111. The by-hash endpoint 404s because Civitai only indexes the hash of the **uploaded archive** — the published file is `adetailerAfterDetailer_v10.zip`. Downloading that zip this session and hashing its members gives one member, `lips_v1.pt`, sha256 `ce9fe145352af12c072ee11536a3d0de9425280096c4367e7a08636f57c7fe99`, 6,222,638 bytes — an **exact match, name included**, to the pack's file | civitai-zip-member-hash | civitai.com/models/142240 | allowCommercialUse=`['Image','RentCivit']` — **no `Sell`, no `Rent`**; allowDerivatives=True, allowDifferentLicense=True, allowNoCredit=True | `verify/civitai_model_142240.json` (flags), zip-member hash transcript in the run log; `civitai/_sweep_misses.json` records the original 404 | **ENC** — same shape as LUSTIFY: images sellable, model redistribution not granted | **NSFW LIVE** — `UltralyticsDetectorProvider` node #161 (`bbox/lips_v1.pt`), mode 0, in the Mouth-Resources subgraph |
| nipple.pt | 36.6 MB | 67e04f8d23cb | **UNIDENTIFIED** — no hash match anywhere queried | — | unknown | UNKNOWN | `civitai/_sweep_misses.json` | **UNIDENTIFIED / UNKNOWN** | neither workflow |
| pussyV2.pt | 6.2 MB | b7c38d3ecf1c | Bytes are **hash-proven identical** to `vermin94/nipples_yolov8s.pt:pussyV2.pt` (repo created 2026-02-27, tag `not-for-all-audiences`) — a stash, not an authored release; true origin unknown | hf-oid (mirror only) | vermin94/nipples_yolov8s.pt | that repo declares **no licence** | `hf/vermin94_nipples_yolov8s.pt_tree.json` + `_meta.json` | **UNKNOWN** (bytes located, licence and author not) | neither workflow |

### models/upscale_models

| path | size | sha256 | identified as | method | source | licence / flags | response files | verdict | graph use |
|---|---|---|---|---|---|---|---|---|---|
| 4x-UltraSharpV2.pth | 140 MB | 0335cf48ad65 | **Kim2091 UltraSharp V2** (`4x-UltraSharpV2.pth`) | hf-oid | Kim2091/UltraSharpV2 | **`license:cc-by-nc-sa-4.0`** (HF API); OpenModelDB entry agrees (CC-BY-NC-SA-4.0) | `hf/Kim2091_UltraSharpV2_tree.json` + `_meta.json`, `external/omdb_4x-UltraSharpV2.json` | **ENC — non-commercial** | **NSFW LIVE ×2** (UpscaleModelLoader #100 and #612, both mode 0) |
| 4x_NMKD-Superscale-SP_178000_G.pth | 67.0 MB | 1d1b0078fe71 | **NMKD Superscale SP 178000 G** (author nmkd) | **omdb sha256 full match** + civitai-hash (non-author re-list 141491) + uwg/upscaler mirror oid | OpenModelDB record | OMDB licence: **WTFPL**; the civitai re-lister (Samael1976, not the author) claims commercial=`[]` — conflict recorded; uwg mirror blanket-tags MIT | `external/omdb_4x-NMKD-Superscale.json`, `civitai/4x_NMKD-Superscale-SP_178000_G_by_hash.json`, `civitai/model_141491.json`, `hf/uwg_upscaler_tree.json` + `_meta.json` | **CLEAN** per the author-licence claim (WTFPL), with the conflicting non-author flags on record | NSFW LIVE (#615, mode 0) |
| RealityGlass4x.pth | 9.0 MB | a4cd3a25b00e | **UNIDENTIFIED** — compact-architecture-sized 4x model; no hash match on Civitai (404), HF candidates, or OpenModelDB (full-repo grep) | — | unknown | UNKNOWN | `civitai/_sweep_misses.json` | **UNIDENTIFIED / UNKNOWN** | neither workflow |
| upscale1.pth | 67.0 MB | a5812231fc93 | **Kim2091 4x-UltraSharp v1.0** | hf-oid (Kim2091/UltraSharp) + omdb sha256 full match + civitai-hash (non-author re-list 116225) + uwg mirror | Kim2091/UltraSharp | **`license:cc-by-nc-sa-4.0`** (HF API); OMDB agrees; the civitai re-lister's `Sell` flag is a non-author claim | `hf/Kim2091_UltraSharp_tree.json` + `_meta.json`, `external/omdb_4x-UltraSharp.json`, `civitai/upscale1_by_hash.json`, `civitai/model_116225.json` | **ENC — non-commercial** | neither workflow |
| x1_ITF_SkinDiffDetail_Lite_v1.pth | 20.1 MB | 94d368b63361 | **ITF SkinDiffDetail Lite v1** (author intheflesh) | **omdb sha256 full match** + uwg mirror oid | OpenModelDB record | **CC-BY-NC-SA-4.0** (OMDB `license` field) | `external/omdb_1x-ITF-SkinDiffDetail-Lite-v1.json`, `hf/uwg_upscaler_tree.json` | **ENC — non-commercial** | **NSFW LIVE** (#90, mode 0) |

### models/vae

| path | size | sha256 | identified as | method | source | licence / flags | response files | verdict | graph use |
|---|---|---|---|---|---|---|---|---|---|
| GlassRoot_D2.safetensors | 254 MB | e027f6859a9c | **Wan 2.1 VAE, bf16, Kijai conversion** — hash-proven to the file `ltx23Gtanimation25Frames_kijaiWan21VAE.safetensors` ("Kijai_Wan2_1_VAE", version 1463486) in AiMetatron's civitai bundle 1295569. **Caveat:** the file currently in Kijai/WanVideo_comfy (`Wan2_1_VAE_bf16.safetensors`, 253,806,278 B) and Comfy-Org's `wan_2.1_vae.safetensors` (253,815,318 B) are byte-different from ours (253,807,438 B), so attribution to "Wan 2.1 VAE" rests on the bundle's filename, not an oid match to a canonical repo | civitai-hash | civitai.com/models/1295569 | bundle flags: commercial=`['Image','RentCivit','Rent']`, deriv=True, diffLic=True, noCredit=False; Wan family Apache-2.0 | `civitai/GlassRoot_D2_by_hash.json`, `civitai/model_1295569.json`, `hf/Kijai_WanVideo_comfy_tree.json` | **CLEAN with provenance caveat** (if the name is accurate it is an Apache-2.0 Wan component; byte-provenance to a canonical repo not established) | video LIVE |
| flux2-vae.safetensors | 336 MB | d64f3a68e1cc | **FLUX.2-dev VAE** = `split_files/vae/flux2-vae.safetensors` in Comfy-Org's flux2-dev repack | hf-oid | Comfy-Org/flux2-dev | Comfy-Org repo: `license:other`, license_name **`flux-1-dev-non-commercial-license`**; canonical black-forest-labs/FLUX.2-dev: license_name **`flux-non-commercial-license`**, **gated=auto**; (a non-author civitai re-list 2165923 claims permissive flags — recorded) | `hf/Comfy-Org_flux2-dev_tree.json` + `_meta.json`, `hf/black-forest-labs_FLUX.2-dev_meta.json`, `civitai/flux2-vae_by_hash.json`, `civitai/model_2165923.json` | **GATED** — a FLUX.2-dev component under the FLUX non-commercial licence | neither workflow |
| variational_encoder_primary.safetensors | 335 MB | afc8e28272cd | **FLUX.1 autoencoder (`ae.safetensors`)** — the identical bytes are oid-proven in TWO homes: black-forest-labs/FLUX.1-schnell (`ae.safetensors`) and Comfy-Org/z_image_turbo (`split_files/vae/ae.safetensors`) | hf-oid (z_image_turbo) + hf-oid git-pointer (FLUX.1-schnell) + civitai re-list 636193 | FLUX.1-schnell / Comfy-Org z_image_turbo | FLUX.1-schnell: **`license:apache-2.0`** (gated=auto, click-through); z_image_turbo copy: ungated, repo untagged | `hf/black-forest-labs_FLUX.1-schnell_tree.json` + `_meta.json`, `hf/Comfy-Org_z_image_turbo_tree.json` + `_meta.json`, `civitai/variational_encoder_primary_by_hash.json` | **CLEAN** — the exact bytes ship under Apache-2.0 in schnell | **NSFW LIVE** (VAELoader #109, as the `ae.safetensors` hardlink the setup script creates) |

### B. Config YAMLs and placeholders (one row each, per brief)

| files | identified as | verdict |
|---|---|---|
| `models/configs/*.yaml` — 11 files: anything_v3, v1-inference (+`_fp16`, `_clip_skip_2`, `_clip_skip_2_fp16`), v1-inpainting-inference, v2-inference (+`-v`, `_fp32`, `-v_fp32`), v2-inpainting-inference | Standard Stable Diffusion 1.x/2.x LDM inference configs — hyperparameter text (`target: ldm.models.diffusion.ddpm.LatentDiffusion`, read from the live repo this session), the stock set ComfyUI ships in `models/configs`. `anything_v3.yaml` and `v1-inference_clip_skip_2.yaml` are byte-identical (same git blob `8bcfe584`) | Licence-irrelevant configuration text, not weights. No action |
| 20 × zero-byte `put_*_here` placeholders | Empty ComfyUI directory-structure markers (git blob `e69de29b`, the empty blob) | Nothing to licence |

---

## C. Files the NSFW setup script fetches from OUTSIDE the AIOFM-Pack repo

From `OFMTech-NSFW/aiofm_setup.sh` (grep of every `dl`/`dl_public`/
`hf_pull_flat`/`wget` URL). These are **buyer-side fetches from public
sources at install time** — the owner does not redistribute these bytes;
each buyer downloads them from the named public repo under that repo's own
terms.

| file (script line) | source URL | licence read this session | verdict |
|---|---|---|---|
| `vitpose_h_wholebody_data.bin`, `vitpose_h_wholebody_model.onnx` (851-856) | huggingface.co/Kijai/vitpose_comfy | `license:apache-2.0` (`hf/Kijai_vitpose_comfy_meta.json`) | CLEAN |
| `yolov10m.onnx` (853-857) | huggingface.co/Wan-AI/Wan2.2-Animate-14B | `license:apache-2.0` (`hf/Wan-AI_Wan2.2-Animate-14B_meta.json`); upstream THU-MIG/yolov10 GitHub licence **AGPL-3.0** (`external/gh_THU-MIG_yolov10_license.json`) | CLEAN, AGPL lineage noted |
| `wan2.2_animate_14B_bf16.safetensors` (875) | huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged | repo untagged; Wan-AI family Apache-2.0 | CLEAN |
| `sdxl_tdd_lora_weights.safetensors` (910) | huggingface.co/RED-AIGC/TDD | **`license:apache-2.0`** (`hf/RED-AIGC_TDD_meta.json`) — the DMD2 replacement, NSFW-live | CLEAN |
| `face_yolov8m.pt`, `hand_yolov8s.pt` (957-958) | huggingface.co/Bingsu/adetailer | The live API this session tags the repo **`license:apache-2.0`** (`hf/Bingsu_adetailer_meta.json`; `cardData.license: "apache-2.0"`). The brief expected an AGPL-3.0 tag — that is **not** what the API returns today. The AGPL-3.0 question attaches to the Ultralytics YOLOv8 training framework (`ultralytics/ultralytics` is AGPL-3.0 per `external/gh_ultralytics_ultralytics_license.json`); whether AGPL reaches model *weights* trained with it is an open legal question, not settled by any API. Factually: these files are fetched by the buyer from a public Apache-tagged repo and are not redistributed in the owner's pack | CLEAN as fetched; unresolved framework-licence question recorded |
| `sam_vit_b_01ec64.pth` (990) | huggingface.co/segments-arnaud/sam_vit_b | mirror repo declares **no licence** (`hf/segments-arnaud_sam_vit_b_meta.json`, tags `['region:us']` only); the original SAM release (facebookresearch/segment-anything) is **Apache-2.0** (`external/gh_facebookresearch_segment-anything_license.json`); the script comment names Meta's own bucket as alternate source | CLEAN (Apache upstream; mirror untagged) — NSFW-live |
| `rife49.pth` (1374-1375, render-time prefetch) | github.com/Fannovel16/ComfyUI-Frame-Interpolation releases; fallback github.com/styler00dollar/VSGAN-tensorrt-docker releases | Fannovel16 repo **MIT**, styler00dollar repo **BSD-3-Clause**, RIFE upstream hzwer/Practical-RIFE **MIT** (all via api.github.com, stored as `external/gh_*_license.json`) | CLEAN |
| `sam2.1_hiera_base_plus-fp16.safetensors` (1399-1404, render-time prefetch) | huggingface.co/Kijai/sam2-safetensors | `license:apache-2.0` (`hf/Kijai_sam2-safetensors_meta.json`); upstream facebookresearch/sam2 **Apache-2.0** (`external/gh_facebookresearch_sam2_license.json`) | CLEAN |

---

## D. Video-pack overlap (extracted from the published tarball this session)

`dist/AIOFMTech-Video.tar.gz` downloaded with the read token; its sha256
equals the tree's `lfs.oid` (`343619dc…`). Contents: `aiofm_setup.sh`
(1,696 lines) + `AIOFM Character Animation v1.2.json`.

**Does the video install reference the files the owner wants to delete?**

`SDXLNSFW.safetensors` — yes, three places:

    770:dl "$REPO/SDXLNSFW.safetensors" "$COMFYUI_DIR/models/checkpoints"
    793:SDXL_CKPT="$COMFYUI_DIR/models/checkpoints/SDXLNSFW.safetensors"
    794:SDXL_DIFF="$COMFYUI_DIR/models/diffusion_models/SDXLNSFW.safetensors"
    802:    dl "$REPO/SDXLNSFW.safetensors" "$COMFYUI_DIR/models/diffusion_models"

`dmd2_sdxl_4step_lora_fp16.safetensors` — yes, line 810 exactly as briefed:

    810:dl "$REPO/dmd2_sdxl_4step_lora_fp16.safetensors" "$COMFYUI_DIR/models/loras"

`v1-5-pruned-emaonly-fp16.safetensors` — **no reference anywhere** in the
video script or the video workflow (grep: zero hits).

The video script also `dl`s the whole diffusion_models set from the pack repo
(lines 782-789: wan2.2_animate from Comfy-Org, then `$REPO/` flux-2, flux4b,
High, HyperFleshUltrav4, Low, Z-TurboSkinForge, zimage).

**But three mitigating facts, all verifiable in the same files:**

1. The video **workflow** loads none of them. Its full model-file reference
   list is: EchoVault_T9, FrostByte_K7, GlassRoot_D2, IronSight_V7,
   NovaMind_X1, PhantomWeave_R5, SolarFlint_L2, VelvetRush_Q4, rife49.pth,
   sam2.1_hiera_base_plus.safetensors, vitpose_h_wholebody_model.onnx,
   wan2.2_animate_14B_bf16.safetensors, yolov10m.onnx. No SDXLNSFW, no dmd2,
   no v1-5, no flux/High/Low/zimage.
2. The script has profiles (lines 145-152): `PROFILE=video` limits `dl` via
   `want()` (lines 154-158) to the `VIDEO_FILES` list — which contains
   **neither SDXLNSFW nor dmd2** nor any of the flux/High/Low set. Under
   `PROFILE=video`, deleting them changes nothing. The **default is
   `PROFILE=all`** (line 147: `PROFILE="${PROFILE:-all}"`).
3. Under the default `PROFILE=all`, a deleted repo file makes that `dl` fail
   **non-fatally** — the failure branch of `dl()` is:

       warn "failed: $fname (partial kept for resume)"

   (no `die`, no `exit`). The install completes with warnings, and the
   render is unaffected because of fact 1.

**Net:** deleting SDXLNSFW / dmd2 / v1-5 (or flux-2, High, Low, etc.) from
the HF repo does **not break video renders**; it produces `warn` lines
during a default-profile video install, and the video pack's setup script
would ideally be re-cut without those `dl` lines at the next publish.

---

## E. Closing — live licensing problems, ranked; then the unidentified

Every file below sits in a repo the owner sells access to (or on the render
path of the sold product). "Delete-safe" = referenced by neither shipped
workflow, and any video-setup reference degrades to a warn (§D.3).

### Problems, most severe first

1. **`models/upscale_models/4x-UltraSharpV2.pth` — CC-BY-NC-SA-4.0, LIVE on
   the NSFW render path twice** (UpscaleModelLoader #100 and #612, mode 0).
   Non-commercial licence on both axes: redistributed in a paid pack AND
   used inside a commercial product's pipeline. Needs replacement in the
   graph, not just deletion. Evidence: `hf/Kim2091_UltraSharpV2_meta.json`.
2. **`models/upscale_models/x1_ITF_SkinDiffDetail_Lite_v1.pth` —
   CC-BY-NC-SA-4.0, LIVE on the NSFW render path** (#90). Same double
   problem. Evidence: `external/omdb_1x-ITF-SkinDiffDetail-Lite-v1.json`.
3. **`models/diffusion_models/flux-2.safetensors` — FLUX.2 [klein] 9B,
   `flux-non-commercial-license`, source gated (auto)**. 18.2 GB
   redistributed ungated. Referenced by neither workflow → delete-safe.
4. **`models/vae/flux2-vae.safetensors` — FLUX.2-dev VAE, flux
   non-commercial licence** per both Comfy-Org and BFL metadata.
   Delete-safe.
5. **`models/sam3/sam3.pt` — Meta SAM License, gated=manual**: redistribution
   only under the Agreement with a copy attached; shipped bare here.
   Delete-safe.
6. **`models/checkpoints/SDXLNSFW.safetensors` +
   `models/diffusion_models/SDXLNSFW.safetensors` — LUSTIFY GGWP V7, flags
   grant no `Sell`/`Rent`**, `licensingFee: 1` on the version. NSFW-LIVE —
   already being rerouted to a buyer-side Civitai fetch by track 1 (route
   B); both repo copies then deletable (video impact: §D warns only).
7. **`models/loras/dmd2_sdxl_4step_lora_fp16.safetensors` — CC-BY-NC-4.0**
   (author repo, API-verified). Referenced by neither workflow; only video
   setup line 810 fetches it under the default profile. Delete-safe
   (warn-only on video installs until the video pack is re-cut).
8. **`models/diffusion_models/High.safetensors` + `Low.safetensors` —
   DaSiWa "SynthSeduction v9"**: no Sell/Rent, derivatives forbidden,
   credit required. 29 GB of encumbered dead weight. Delete-safe.
9. **`models/diffusion_models/Z-TurboSkinForge.safetensors`** — flags grant
   only RentCivit+Rent: **no commercial image use, no redistribution**.
   Delete-safe.
10. **`models/loras/VelvetPores_Flux.safetensors`** — no Sell/Rent,
    deriv=False, diffLic=False. Delete-safe.
11. **`models/loras/DetailedNipples.safetensors`** — no Sell/Rent.
    Delete-safe (its anatomy path is dead in the graph).
12. **`models/diffusion_models/HyperFleshUltrav4.safetensors`** — `Sell`
    granted but **credit required** and not given; FLUX.1-dev base-licence
    tension unresolved (lawyer call). Delete-safe (unreferenced).
13. **`models/upscale_models/upscale1.pth` — 4x-UltraSharp v1,
    CC-BY-NC-SA-4.0**. Delete-safe (unreferenced; the live UltraSharp
    problem is #1, the V2 file).
14. **`models/checkpoints/v1-5-pruned-emaonly-fp16.safetensors`** — minor:
    OpenRAIL-M redistribution requires the licence text to accompany;
    unreferenced by both workflows → simplest fix is deletion (E3).

Minor process notes, not ranked: three "clean" hosts (Comfy-Org repacks,
Kijai/WanVideo_comfy) declare **no licence tag at all** — the CLEAN verdicts
for files from them rest on upstream-family Apache-2.0 evidence, which is
one step weaker than a tag on the distributing repo; and
`models/loras/NovaMind_X1` has a non-author Civitai re-list claiming
restrictive flags that the author's Apache-2.0 repo overrides.

### Unidentified (no hash match anywhere queried this session)

- ~~**`models/ultralytics/lips_v1.pt`**~~ — **RESOLVED after this section was
  drafted.** It is Civitai model 142240 ("ADetailer Lips Model", creator
  mooseh111), published as a zip, which is why the by-hash endpoint 404s:
  Civitai indexes the archive's hash, not its members'. The zip was
  downloaded this session and its single member hashes exactly to the pack's
  file. Flags: `['Image','RentCivit']` — **no `Sell`**. It moves out of this
  list and into the ranked problems as item 6b: same shape as LUSTIFY, live
  on the mouth path, 6.2 MB. See the `models/ultralytics` table row.
  **Method note worth keeping: a 404 from `by-hash` does not mean "not on
  Civitai" — it means "not published as a bare file".** Two of the three
  remaining unidentified files below are the same size class and may well be
  zip members too; that search was not run for them.
- **`models/ultralytics/nipple.pt`** — dead path, unidentified.
- **`models/ultralytics/pussyV2.pt`** — dead path; bytes located in an
  unlicensed third-party HF stash (`vermin94/nipples_yolov8s.pt`), author
  unknown.
- **`models/upscale_models/RealityGlass4x.pth`** — unreferenced,
  unidentified 4x compact upscaler.

All four are delete-safe except `lips_v1.pt`, which needs a graph edit to
remove or replace.
