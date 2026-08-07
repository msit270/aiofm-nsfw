# research_black raw sources (fetched 2026-08-08)
| file | what | url |
|---|---|---|
| issue_15110.json / issue_15110_comments.json | Z-Image Qwen3-4B GPU TE all-NaN conditioning on Blackwell sm_120 (RTX PRO 6000, torch 2.9.1+cu130, ComfyUI 0.28.0; TE->CPU prevents; sticky until restart). Filed 2026-07-27 by "nubsgroup" - PROBABLY THIS PROJECT'S OWN REPORT (same falsified-theory list); only comment is a bot. | https://github.com/Comfy-Org/ComfyUI/issues/15110 |
| issue_13123.json (+_comments) | Z-Image BASE black at all precisions (AMD/ZLUDA; Turbo fine) - different failure, shows silent-black class | https://github.com/Comfy-Org/ComfyUI/issues/13123 |
| issue_14249.json | Lumina-family PiD pixel-space NaN in bf16 on ROCm gfx1151; only --force-fp32 valid; NaN cast warning at save | https://github.com/Comfy-Org/ComfyUI/issues/14249 |
| wt_issue_401.json | Z-Image Turbo template black images (Desktop 0.3.76) | https://github.com/Comfy-Org/workflow_templates/issues/401 |
| tongyi_issue_14.json | Upstream model: fp16 inference = NaN latents/black (bf16 ok on that card) | https://github.com/Tongyi-MAI/Z-Image/issues/14 |
| hf_z_image_turbo_disc4.html | "getting black outputs" community thread | https://huggingface.co/Comfy-Org/z_image_turbo/discussions/4 |
| commits_lumina_model.json | comfy/ldm/lumina/model.py history since v0.15.1 (3 commits; no NaN fix) | api.github.com Comfy-Org/ComfyUI |
| commits_z_image_te.json | comfy/text_encoders/z_image.py history since v0.15.1: EMPTY (unchanged) | idem |
| commits_ops.json | comfy/ops.py history since v0.15.1 (SDPA priority churn Jul-Aug 2026) | idem |
| commit_f73e8cde88.patch | 2026-07-29 "Fallback to cudnn attention on linux if flash attention doesn't work" - extends SDPA priority override (flash>cudnn>efficient>math) to Linux | https://github.com/Comfy-Org/ComfyUI/commit/f73e8cde88 |
| commit_40dbdc1bef.patch | 2026-08-04 "restore SDPA non-cudnn small attention bypass" (<128K elements bypasses cudnn) | .../commit/40dbdc1bef |
| commit_7c806288d5.patch | 2026-07-31 placeholder/materialization logic applied to Linux (RAM-transient fix) | .../commit/7c806288d5 |
| commit_2e47082c8e.patch | 2026-07-22 "Make z image/lumina 2 models use comfy kitchen rms rope" = the known ~v0.29 RoPE change (fused rms_rope kernel, inference-only path) | .../commit/2e47082c8e |
| pr_15146.json | PR body for f73e8cde88 | https://github.com/Comfy-Org/ComfyUI/pull/15146 |
| pytorch_releases.json, pt_release_v2.10.0.json | torch releases: NO v2.9.2 exists; v2.10.0 (2026-01-21) has "Fix safety issues when calling cuBLAS from multiple threads" (#167248) and "Disable cuDNN for 3D convolutions ... due to a numerical issue" (#163581) | https://github.com/pytorch/pytorch/releases |
| pt_issue_151912.json | bf16 numerical errors, SDPA math backend (compile) | https://github.com/pytorch/pytorch/issues/151912 |
| search_comfy_zimage_black.json, search_pt_cudnn_nan.json | issue-search snapshots | api.github.com |
| cublas_reproducibility.md | NVIDIA cuBLAS reproducibility quotes (multi-stream voids bitwise run-to-run guarantee) | https://docs.nvidia.com/cuda/cublas/index.html |
