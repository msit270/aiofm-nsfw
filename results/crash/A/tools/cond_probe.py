#!/usr/bin/env python3
"""Offline: encode prompts of exact token lengths through the graph's own text
encoder (620:110 CLIPLoader -> qwen.safetensors, and optionally the 116 LoRA on
the CLIP side) and report whether the conditioning tensor is finite.

CPU only -- run with CUDA_VISIBLE_DEVICES= so it cannot contend with renders.
"""
import sys, os, json
sys.path.insert(0, "/workspace/ComfyUI")
import comfy.cli_args
comfy.cli_args.args.cpu = True           # model_management reads this at import time
import torch
import comfy.sd
import comfy.utils
import comfy.sd1_clip
import folder_paths

CLIP_PATH = "/workspace/ComfyUI/models/text_encoders/qwen.safetensors"
LORA_PATH = "/workspace/ComfyUI/models/loras/luna.safetensors"
BASE = "a woman's face"


def summarise(t):
    t = t.float()
    return {"shape": list(t.shape), "finite": bool(torch.isfinite(t).all()),
            "nan": int(torch.isnan(t).sum()), "inf": int(torch.isinf(t).sum()),
            "absmax": float(t.abs().max()), "mean": float(t.mean()),
            "std": float(t.std())}


def main(lengths, use_lora=True):
    clip = comfy.sd.load_clip(ckpt_paths=[CLIP_PATH], embedding_directory=None,
                              clip_type=comfy.sd.CLIPType.LUMINA2)
    if use_lora and os.path.exists(LORA_PATH):
        lora = comfy.utils.load_torch_file(LORA_PATH, safe_load=True)
        _, clip = comfy.sd.load_lora_for_models(None, clip, lora, 0, 1.0)
        print("LoRA applied to CLIP: luna.safetensors @ 1.0", flush=True)
    out = {}
    for n in lengths:
        text = BASE + " the" * (n - 12)
        tokens = clip.tokenize(text)
        ntok = len(tokens["qwen3_4b"][0])
        cond = clip.encode_from_tokens_scheduled(text) if False else None
        c = clip.encode_from_tokens(tokens, return_pooled=False)
        r = summarise(c)
        r["tokens"] = ntok
        out[n] = r
        print(f"{n:3d} req / {ntok:3d} actual  finite={r['finite']} nan={r['nan']} inf={r['inf']} "
              f"absmax={r['absmax']:.4g} std={r['std']:.4g} shape={r['shape']}", flush=True)
    return out


if __name__ == "__main__":
    lens = [int(x) for x in sys.argv[1:]] or [28, 29, 30, 31, 32, 33]
    res = main(lens)
    json.dump(res, open("/workspace/nsfw-fix/results/crash/A/cond_probe.json", "w"), indent=1)
