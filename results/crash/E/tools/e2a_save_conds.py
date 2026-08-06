#!/usr/bin/env python3
"""E2a -- encode the test prompts through the graph's own text encoder and save
the conditioning tensors to disk, so the DiT probe can run without the encoder
resident. Offline; no ComfyUI server is touched."""
import sys, os, json
sys.path.insert(0, "/workspace/ComfyUI")
os.chdir("/workspace/ComfyUI")
import torch
import comfy.sd
import folder_paths

OUT = "/workspace/nsfw-fix/results/crash/E/out"
BASE = "a woman's face"
PLACEHOLDER = "TRIGGER, PROMPT FOR YOUR MODEL"
CRASH = ("luna, a young woman with light freckles across her nose and cheeks, "
         "natural skin texture with visible pores, detailed eyes, "
         "photorealistic portrait photograph, 85mm lens")
NOPREFIX = CRASH[len("luna, "):]
EYE = ("perfect eyes, round pupils, round iris, symmetrical eyes, realistic eyes, "
       "perfect circles, round")

clip_path = folder_paths.get_full_path_or_raise("text_encoders", "qwen.safetensors")
clip = comfy.sd.load_clip(ckpt_paths=[clip_path],
                          embedding_directory=folder_paths.get_folder_paths("embeddings"),
                          clip_type=comfy.sd.CLIPType.LUMINA2, model_options={})

cases = {}
for n in range(12, 81):
    cases[f"tok{n}"] = BASE + " the" * (n - 12)
cases["PLACEHOLDER"] = PLACEHOLDER
cases["CRASHSTRING"] = CRASH
cases["CRASH_NOPREFIX"] = NOPREFIX
cases["EYE_shipped"] = EYE
# Track A's content families at 30 tokens, to test content-independence in the DiT
cases["A3_gardener_w17"] = ("an elderly gardener with a broad flat nose, heavy grey eyebrows, "
                            "deep creases on both cheeks, a")
cases["L_w17"] = ("luna, a young woman with light freckles across her nose and cheeks, "
                  "natural skin texture with")
cases["L_w16"] = ("luna, a young woman with light freckles across her nose and cheeks, "
                  "natural skin texture")

store, meta = {}, {}
for name, text in cases.items():
    tokens = clip.tokenize(text)
    ntok = len(tokens["qwen3_4b"][0])
    out = clip.encode_from_tokens_scheduled(tokens)
    cond = out[0][0].cpu()
    store[name] = cond
    meta[name] = {"tokens": ntok, "text": text, "shape": list(cond.shape),
                  "finite": bool(torch.isfinite(cond).all().item()),
                  "absmax": float(cond.abs().max().item()),
                  "std": float(cond.std().item())}
    print(f"{name:18s} tok={ntok:3d} finite={meta[name]['finite']}", flush=True)

torch.save(store, os.path.join(OUT, "conds.pt"))
json.dump(meta, open(os.path.join(OUT, "conds_meta.json"), "w"), indent=1)
print("saved", len(store), "conditionings")
