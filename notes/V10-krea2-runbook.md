# V10 (Krea 2) swap runbook — written 2026-08-07, before V10 unlocks

Facts (research/, fetched this session):
- LUSTIFY V10 = Civitai version **3112728**, baseModel "Krea 2 Standard",
  published 2026-07-25, **early access until 2026-08-10** (our key got HTTP
  401 on the download today). Files: Raw fp16/fp8/int8, Turbo fp16/fp8/int8,
  GGUF Q4/Q2. Creator: "Use Turbo for everyday inference, Raw for training."
- Krea 2 = Krea AI's from-scratch 12B dense DiT; **Qwen Image VAE** +
  **Qwen3-VL text encoder** (NOT FLUX-derived, NOT SDXL).
- ComfyUI support needs **core >= 0.26.0** (`krea2` CLIP type;
  qwen3vl_4b text encoder + qwen_image_vae). This pod runs 0.15.1.
- Known output-affecting core change on the way up: v0.29.0 changed
  Z-Image/Lumina2 RoPE numerics (Q1) — a core upgrade shifts ALL Z-pass
  outputs slightly; re-A/B after upgrade.

The afternoon-swap procedure (personal build):
1. `cd /workspace/ComfyUI && git fetch && git checkout v0.30.x` (or latest);
   `pip install -r requirements.txt` in the venv. Frontend comes from the
   pinned comfyui-frontend-package wheel; expect >=1.47 with different
   subgraph handling — the personal workflow is FLAT, so the class of
   subgraph-flattening regressions the sellable fears does not apply to it.
2. Re-render the run-5 canary (zref_P_12345, stored bytes) — EXPECT small
   pixel drift from the RoPE change; store the new reference.
3. Fetch V10 Turbo fp16 via the installer's LUSTIFY route:
   `LUSTIFY_VERSION_ID=3112728 LUSTIFY_SHA256=<pick file hash from
   results/run5/civitai_model_573152.json> LUSTIFY_BYTES=<bytes>
   LUSTIFY_FILE=lustifyNSFWCheckpoint_v10Krea2.safetensors bash
   aiofm_setup.sh` — the machinery already does key-preflight + sha verify.
   NOTE: pick the exact file variant (fp8 vs bf16 vs full) by hash from the
   API listing; there are SEVEN files on that version.
4. Krea2 loaders: UNETLoader (v10 file) + CLIPLoader type `krea2`
   (qwen3vl_4b_fp8_scaled.safetensors) + VAELoader qwen_image_vae
   (both fetched from Comfy-Org repos — see the official Krea2 template in
   research/comfy_template_image_krea2_turbo_t2i.json; 8 steps / cfg 1 /
   euler / simple for Turbo).
5. The base-slot swap in the personal workflow = repoint the BASE sampler's
   model/clip/vae to the Krea2 loaders (three link changes in the flat
   graph, or rebuild via candidates.py with a krea2_base() builder).
   EVERYTHING tuned remains Z-Image-side and carries over; the BASE slot is
   the only change. Then re-run the likeness/texture score vs the stored
   references.
6. Open question V10 does not answer by itself: whether luna/lunaskye-class
   LoRAs exist for Krea 2 — LUSTIFY V10 is the BASE model; the character
   LoRA would need retraining on Krea 2 for the base slot to carry identity
   the way ZIT+luna does now. Until then V10 is a composition/scene-quality
   candidate with identity still carried by the Z-Image face pass.
