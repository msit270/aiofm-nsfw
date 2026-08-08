# REF-PREFLIGHT — reference workflow identity check (2026-08-08)

## VERDICT: WRONG FILE — comparison blocked, nothing rendered

The file uploaded to `reference/` is **not** the Z-Image stills workflow
described in the brief. It is **"AIOFM · CHARACTER ANIMATION · v1.2"** —
the WanVideo 2.2 Animate VIDEO product (the sibling pipeline this project
itself documented). Per the brief's own STEP-0 rule ("for anything
ambiguous, stop and tell me exactly what it is... a silent substitution
would invalidate the entire comparison"), the session stops here. No
renders, no A/B, no structural diff was run — there is nothing valid to
diff pc_final against.

File: `reference/AIOFM Character Animation v1.2.json`
sha256 (first 16): af43c1d5935b3e14 · 150,340 bytes · uploaded 12:20

## Evidence (all read from the file)

1. **Zero Z-Image content.** grep for zimage / z-image / ZIT / lumina /
   EmptySD3 across the whole file: no matches. No UNET/checkpoint loader
   references any Z-Image model.
2. **It is a video graph.** Top level: `LoadImage` (character photo #57) +
   `VHS_LoadVideo` (driving clip "2026-03-09 13.00.30.mp4", #63) →
   5 subgraphs → `VHS_VideoCombine` (h264 MP4 out, #213).
3. **The generator is WAN, not Z.** `WanVideoModelLoader`
   `wan2.2_animate_14B_bf16.safetensors` (#298), `WanVideoSampler`
   4 steps / cfg 1 / seed 1234 (#27), `WanVideoAnimateEmbeds` +
   pose retarget stack (ViTPose `vitpose_h_wholebody_model.onnx` +
   `yolov10m.onnx` + SAM2 `sam2.1_hiera_base_plus`), RIFE 2x + film
   grain finish.
4. **It self-identifies.** Root MarkdownNote #332: "AIOFM · CHARACTER
   ANIMATION · v1.2 — Your character. Your video's motion. One button."
   The embedded notes carry this project's own documented traps verbatim
   (lanczos-on-gpu error, DrawMaskOnImage device order, seed-promotion
   corruption) — this is the packaged sibling video product, not a
   home-built stills graph.
5. **Wrong architecture family for the brief's premise.** WAN 2.2 video
   DiT vs Z-Image; "same architecture family, so the comparison should
   be clean" cannot refer to this file.

## Preflight inventory anyway (models this file wants vs pod)

All present under /workspace/ComfyUI/models except one:
- diffusion_models/wan2.2_animate_14B_bf16.safetensors — PRESENT
- clip_vision/IronSight_V7.safetensors — PRESENT
- text_encoders/EchoVault_T9.safetensors — PRESENT
- vae/GlassRoot_D2.safetensors — PRESENT
- loras: SolarFlint_L2, VelvetRush_Q4, FrostByte_K7, PhantomWeave_R5,
  NovaMind_X1 — ALL PRESENT
- detection/vitpose_h_wholebody_model.onnx, yolov10m.onnx — PRESENT
- rife49.pth — not under models/ (ComfyUI-Frame-Interpolation fetches
  into its own ckpts dir on demand; not checked further — irrelevant to
  the stills comparison)

Expected: this pod built the video product. Nothing was fetched.

## Also checked

- The real Z-Image workflow did not land elsewhere in this upload:
  `.ipynb_checkpoints/` is empty; a filesystem sweep for JSONs modified
  since 12:00 finds only this one file outside Claude/ComfyUI internals.
- Run 5 already established the owner's simple ZIT workflow is NOT on
  this pod (HANDOFF-QUALITY.md), and its blueprint reconstruction was
  explicitly flagged as a substitution needing re-anchoring. It was NOT
  used here.

## To resume the diff-and-diagnosis

Upload the actual home workflow JSON (the Z-Image/ZIT stills graph —
from the home machine: ComfyUI → Workflow → Export, or the API-format
export; a PNG render carrying the embedded workflow also works) into
`reference/`. Everything else is staged: pc_final is intact at pack v3
f70c9af4, the run-5 zero-noise-floor A/B method and likeness/texture
tooling are on the pod, and steps 1–4 of the brief can start immediately
on the correct file.
