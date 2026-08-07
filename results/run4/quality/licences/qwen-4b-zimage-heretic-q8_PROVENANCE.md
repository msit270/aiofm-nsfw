# qwen-4b-zimage-heretic-q8.gguf — provenance and licence (Q3, 2026-08-07)

UNTESTED possibility only. No render was or can be run with this file in this
session: ComfyUI core `CLIPLoader` does not enumerate `.gguf`, no GGUF loader
pack is installed (`ls custom_nodes` shows none), and installing packs is
banned for track-2 agents. Recorded for the owner's menu, nothing more.

- Local file: /workspace/ComfyUI/models/text_encoders/qwen-4b-zimage-heretic-q8.gguf
- Size: 4,280,404,896 bytes
- SHA256: 70af2493307e38df4f3957811887d037821c4cea3d4230bb7430cd78d90f1ef3
- Origin (SHA256 match via HF API `?blobs=true`, THIS session):
  * https://huggingface.co/Lockout/qwen3-4b-heretic-zimage  (created 2025-11-30,
    licence tag **apache-2.0**, not gated) — raw response:
    hf_model_Lockout_qwen3-4b-heretic-zimage.json
  * byte-identical mirror: ItBitter/qwen3-4b-heretic-zimage (2026-03-17, also
    apache-2.0) — hf_model_ItBitter_qwen3-4b-heretic-zimage.json
- Model card (hf_readme_Lockout_qwen3-4b-heretic-zimage.md): "I ran the actual
  TE from z-image through heretic ... The model is abliterated." I.e. it is the
  Z-Image text encoder (Qwen3-4B family) run through the Heretic abliteration
  tool, quantised Q8_0 GGUF. A V2 ("lower KLD") exists in the same repo,
  sha256 0919a15e..., NOT the shipped file.
- Upstream base: Tongyi-MAI/Z-Image-Turbo carries licence tag **apache-2.0**
  (hf_model_Tongyi-MAI_Z-Image-Turbo.json, fetched this session).
- Caveats: the apache-2.0 tag on the Lockout repo is the uploader's own claim
  on a derivative; the card documents no dataset provenance for the
  abliteration pass. Chain (Qwen3-4B -> Z-Image TE -> heretic abliteration) is
  Apache-2.0 at every link that states a licence.
