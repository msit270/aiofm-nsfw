# research_arch sources (fetched 2026-08-08)

## Raw files stored here
- impact_core.py, impact_utils.py — ltdrdata/ComfyUI-Impact-Pack@Main modules/impact/. Load-bearing lines:
  core.py:260-265 noise_mask+feather>0 => utils.apply_differential_diffusion(model) (auto Differential Diffusion on every detailer pass);
  core.py:287-297 guide_size skip + upscale=guide/min(bbox); core.py:305-321 max_size clamp THEN force_inpaint resets upscale<=1 -> sample at NATIVE crop res (max_size effectively uncapped for big faces);
  core.py:~417 refined_image = utils.tensor_resize(...) back to crop size (PIL LANCZOS, utils.py:129) then masked tensor_paste; comment "non-latent downscale - latent downscale cause bad quality".
  utils.py:693 apply_differential_diffusion.
- ltdrdata_detailers.md / detectors.md / mediapipe.md / pk_hook.md / extreme-upscale.md / advanced.md / TwoSamplersUpscale.md / PromptPerTileUpscale.md — ltdrdata/ComfyUI-extension-tutorials@Main (Impact tutorial = closest thing to Impact design docs). detailers.md: guide_size semantics ("larger than guide_size are skipped, deemed not requiring detailing"), cycle+hooks for gradual denoise, noise_mask recommended on.
- ltdrdata_sdxl_reencode_exp1.md — ltdrdata's own cross-family 2-pass experiments (SDXL base + SD1.5 second pass ± SDXL refiner).
- impact_README.md — hook inventory: NoiseInjectionDetailerHookProvider, DenoiseSchedulerDetailerHookProvider, VariationNoiseDetailerHookProvider, UnsamplerDetailerHookProvider, DetailerHookCombine.
- adetailer_README.md — Bing-su/adetailer (A1111): per-mask inpaint pipeline, "After Detailer" = runs in postprocess.
- usdu_README.md (ssitu ComfyUI port) — "performing the image-to-image diffusion process on large images in tiles... improves the details that is commonly found on upscaled images... maintaining an image size that the diffusion model is trained on" = vendor statement of upscale-then-tile-refine design.
- usdu_a1111_wiki_FAQ.md — Coyote-A wiki FAQ: denoise "0.35 for image enhancements... if you don't want changes use 0.15-0.20"; larger tile = fewer artifacts; seam fix "Do not use it if result image haven't visible grid".
- detail_daemon_README.md — Jonseed/ComfyUI-Detail-Daemon: sigma-schedule detail enhancement, explicitly supports Z-Image; Multiply Sigmas / Lying Sigma Sampler variants.
- comfy_nodes_post_processing.py — ComfyUI ImageBlend: out = image1*(1-f) + blend(image1,image2)*f; normal mode + factor 1.0 => output == image2 exactly (lines 47-49).
- hf_mirror_usdu_facedetailer_01.json — 401, not retrievable.

## WebFetch-only (summaries, not stored raw)
- github.com/Bing-su/adetailer/discussions/634 + /437 — users ask to run ADetailer BEFORE hires fix; unanswered/no mechanism offered; ADetailer by design runs after the full gen incl. hires upscale (workaround = disable hires, detail, then upscale separately). => vendor default = upscale-then-detail(-at-crop-scale).
- civitai.com/articles/3495 (HiRes Fix + ADetailer guide) — order shown: hires fix then ADetailer; no explicit quality reasoning.
- comfyanonymous.github.io/ComfyUI_examples/2_pass_txt2img/ — official hires-fix: gen -> upscale -> img2img refine; cross-model 2-pass example (WD1.5 -> cardosAnime); no face detailing in any official example.
- forum.comfy.org/t/skin-color-mismatch/3840 — FaceDetailer/SEGS color desaturation + visible box seams are a live community problem; no settled fix in-thread.
- lewdly.ai/blog/comfyui-face-detailer-nsfw-workflow — [community hypothesis] "Pass 1 before upscaling (fixes structural problems at low cost). Pass 2 after upscaling at lower denoise"; 0.5 then 0.3; hands want higher denoise 0.5-0.6.
- runcomfy/thinkdiffusion face-detailer tutorials — 2-pass face detail (0.5 fix -> 0.3 refine) is a documented known pattern.
- Comfy-Org workflow_templates list (../research/comfy_templates_list.json) — ~1000 template asset names, NO face/hand/eye detailer template among official templates; multi-pass portrait finishing lives entirely in the extension ecosystem.
