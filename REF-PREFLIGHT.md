# REF-PREFLIGHT — reference workflow identity check

## RUN 6 (2026-08-08 12:2x): correct file received — PREFLIGHT PASS

File: `reference/MarlAI_ImageGen_ZImage.json`
sha256 8cccce5b0667de9c… · 151,793 bytes · uploaded 12:27

### Identity

A genuine Z-Image-Turbo stills workflow — flat graph, 93 nodes, no
subgraphs. NOT home-built: it is a licensed vendor product — root notes
read "MarlAI VIP - licensed copy / Licensed to: Stray / Issued:
2026-06-14 / Do not redistribute", plus a "SynariAI" label node. Because
of that license line the JSON stays UNTRACKED in git (hash above pins
identity); analysis stays local to this pod.

### Architecture (fully traced, Set/Get resolved — 20 KJNodes virtual links)

One model chain feeds everything: UNETLoader `zimage.safetensors` →
LoraLoaderModelOnly `aikozimage.safetensors` @ 0.8. One TE:
CLIPLoaderGGUF `qwen-4b-zimage-heretic-q8.gguf` (lumina2) — an
abliterated Qwen3-4B. One VAE everywhere: "UltraFlux VAE"
(`diffusion_pytorch_model.safetensors`). Same positive+negative
conditioning at every stage; negative = ~600-term Chinese anti-AI-look
block (anti plastic-skin / influencer-face / studio-look).

Progressive-upscale pyramid, portrait 7:9:
- S1a draft: 112x144 px latent (#166) → SamplerCustom #448, euler_ancestral,
  9 steps via FlowMatchEulerDiscreteScheduler(Custom) #507 (shift 3,
  exponential), cfg 1, model shift 3 (#411)
- S1b: latent x2 → 224x288 → ClownsharKSampler_Beta #408 (RES4LYF):
  eta .52, linear/euler, beta57, 5 steps, denoise 0.7, cfg 2, bongmath,
  perlin SharkOptions, DetailBoost 1.2 (steps 1-3), model = LoRA stack
  (default shift 3)
- S2: decode → re-encode (UltraFlux VAE roundtrip) → InjectLatentNoise 0.3
  → IterativeLatentUpscale #147 x3 in 5 hops (Impact) → 672x864;
  per-hop PixelKSampleUpscaler euler/beta 9 steps den 0.6 cfg 1,
  model shift 6 (#88)
- S3: LatentUpscale → 896x1152 → noise 0.4 → Clown #235: 9 steps,
  den 0.5, cfg 1, DetailBoost 1.4, shift 7 (#455)
- S4: LatentUpscale → 1344x1728 → noise 0.2 → Clown #428: 9 steps,
  den 0.5, cfg 1, DetailBoost 1.2, shift 7 (#456) → SaveImage.
FINAL OUTPUT 1344x1728 (pc_final delivers 2688-wide — note for step 4).

Dead/bypassed in the file: CLIPLoader qwen_3_4b (bypassed; GGUF used),
ModelPatchLoader Z-Image-Turbo-Fun-Controlnet-Union-2.1 (bypassed),
VAELoader ae.safetensors (loaded, never consumed), landscape latent
144x112 (Set, never Get), ImageResizeKJv2 448x576 → "Stage 2 Image"
(Set, never Get — preview-only path via VAEDecode #78).

### Requirements vs pod — every item resolved, nothing ambiguous left

PRESENT and hash-verified byte-exact:
- zimage.safetensors = OFFICIAL Z-Image-Turbo bf16
  2407613050b809ff… = Comfy-Org/z_image_turbo
  split_files/diffusion_models/z_image_turbo_bf16.safetensors ✓
- qwen-4b-zimage-heretic-q8.gguf 70af2493307e38df… =
  Lockout/qwen3-4b-heretic-zimage (V1, 4.28 GB) ✓

FETCHED this session and hash-verified:
- UltraFlux VAE → models/vae/diffusion_pytorch_model.safetensors
  (filename kept exactly as the workflow references it)
  2bf9ad685686b480b03651a8d8595951e4a5578016b8ead4af5e22d3dc9b3409
  = Owen777/UltraFlux-v1 vae/diffusion_pytorch_model.safetensors ✓
  Config confirms drop-in for Z-Image latents: AutoencoderKL, 16
  latent channels, f8, scaling 0.3611 / shift 0.1159 (Flux family),
  fine-tuned on 4K data (community-verified Z-Image compatible).

NODE PACKS installed this session (were missing), pinned:
- RES4LYF (ClownsharKSampler_Beta, SharkOptions_Beta,
  ClownOptions_DetailBoost_Beta) — github.com/ClownsharkBatwing/RES4LYF
  @ 26036f6 (registry: api.comfy.org/nodes/res4lyf)
- ComfyUI-GGUF (CLIPLoaderGGUF) — github.com/city96/ComfyUI-GGUF
  @ 6ea2651 (registry latest 1.1.10)
- ComfyUI-EulerDiscreteScheduler (FlowMatchEulerDiscreteScheduler
  (Custom)) — github.com/erosDiffusion/ComfyUI-EulerDiscreteScheduler
  @ eb5bd4d (registry: erosdiffusion-eulerflowmatchingdiscretescheduler
  v1.0.8, "Noise Free images ... with Z-Image")
- Python deps: only pywavelets was missing (installed 1.8.0;
  numpy verified untouched at 2.4.0)

NOT NEEDED at runtime (bypassed/dead paths): qwen_3_4b.safetensors,
the Fun-ControlNet patch (pod has a different variant of it anyway),
ae.safetensors (present regardless).

UNAVAILABLE — flagged, not silently substituted:
- `aikozimage.safetensors` @ 0.8 — the owner's HOME character LoRA
  (trigger "AIKZZ1L"). Does not exist on this pod and cannot be
  fetched. The A/B therefore runs BOTH graphs with luna.safetensors
  (the pod's ZIT-trained character LoRA) — an EXPLICIT substitution
  that is exactly the controlled variable the brief asks for ("same
  LoRA" both sides). Consequence: this session measures the GRAPHS,
  not the home character; aiko-specific behavior (e.g. whether 0.8 is
  the right strength for luna) is separately sheeted.

### Version-drift caveats (vendor cut 2026-06-14, packs are HEAD)

- ClownsharKSampler_Beta now takes options via one autogrow group
  (`options_group`) instead of the file's numbered "options 2/3" slots;
  wiring adapted at API-conversion; queue validation is the check.
- IterativeLatentUpscale gained `vae_compression` (=8, matches the
  file's 5th widget). Widget maps verified name-by-name against live
  /object_info on :19188 for every RES4LYF/Impact/essentials node used.
- RES4LYF's exact June revision is unknowable from the file; if a
  sampler-math change since then alters output, the A/B still stands
  (both arms render on today's code) but home-vs-here parity is
  UNPROVEN. Stated once here, not repeated.

### Runtime

Work server :19188 booted (pod ComfyUI 0.15.1, torch 2.9.1+cu128,
--disable-xformers --disable-async-offload per run-5 daily flags;
:18188 untouched). All required backend classes load; SetNode/GetNode
are KJNodes FRONTEND-ONLY virtual nodes — they never reach the server
and are resolved during API conversion (expected, not a gap).
Known pre-existing loader error for `Ideogram4PromptBuilderKJ`
(KJNodes/frontend mismatch) — unrelated to this graph.

Black-frame discipline from run 5 stays in force: every render is
black-checked; on black, fresh-boot re-render.

---

# ARCHIVED — first upload (2026-08-08 12:20): wrong file

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
