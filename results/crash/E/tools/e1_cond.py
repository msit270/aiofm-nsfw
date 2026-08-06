#!/usr/bin/env python3
"""E1 -- is the CONDITIONING out of a CLIPTextEncode on 620:110 finite?

Replicates exactly what the graph does:
  620:110  CLIPLoader   qwen.safetensors, type lumina2, device default
  620:106  CLIPTextEncode  (clip taken straight from 620:110 -- NO LoRA;
                            116 Lora Loader Stack feeds 620:114.model, and
                            620:106.clip is ["620:110", 0] in the submitted graph)

No ComfyUI server is touched. This is an offline load of the same file with the
same code path, so the dtype/device decisions are the ones ComfyUI makes.

Usage:  python3 e1_cond.py  [lo hi]      (default 8..64)
"""
import sys, os, json, argparse
sys.path.insert(0, "/workspace/ComfyUI")
os.chdir("/workspace/ComfyUI")

import torch
import comfy.sd
import comfy.model_management as mm
import folder_paths

OUT = "/workspace/nsfw-fix/results/crash/E/out"

BASE = "a woman's face"          # Track A's T_tok family: 12 tokens
PLACEHOLDER = "TRIGGER, PROMPT FOR YOUR MODEL"
CRASH = ("luna, a young woman with light freckles across her nose and cheeks, "
         "natural skin texture with visible pores, detailed eyes, "
         "photorealistic portrait photograph, 85mm lens")
EYE = ("perfect eyes, round pupils, round iris, symmetrical eyes, realistic eyes, "
       "perfect circles, round")


def stats(t):
    tf = t.float()
    return {
        "shape": list(t.shape),
        "dtype": str(t.dtype),
        "nan": int(torch.isnan(tf).sum().item()),
        "inf": int(torch.isinf(tf).sum().item()),
        "finite": bool(torch.isfinite(tf).all().item()),
        "absmax": float(tf.abs().max().item()) if torch.isfinite(tf).any() else None,
        "mean": float(tf[torch.isfinite(tf)].mean().item()) if torch.isfinite(tf).any() else None,
        "std": float(tf[torch.isfinite(tf)].std().item()) if torch.isfinite(tf).any() else None,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("lo", nargs="?", type=int, default=8)
    ap.add_argument("hi", nargs="?", type=int, default=64)
    ap.add_argument("--tag", default="e1")
    a = ap.parse_args()

    clip_path = folder_paths.get_full_path_or_raise("text_encoders", "qwen.safetensors")
    clip = comfy.sd.load_clip(ckpt_paths=[clip_path],
                              embedding_directory=folder_paths.get_folder_paths("embeddings"),
                              clip_type=comfy.sd.CLIPType.LUMINA2, model_options={})
    print("load_device", clip.patcher.load_device, "offload", clip.patcher.offload_device,
          "dtype", clip.patcher.model.dtype if hasattr(clip.patcher.model, "dtype") else "?", flush=True)
    print("cond_stage_model dtype:", next(clip.cond_stage_model.parameters()).dtype, flush=True)

    cases = []
    for n in range(a.lo, a.hi + 1):
        k = n - 12
        if k < 0:
            continue
        cases.append((f"tok{n}", BASE + " the" * k))
    cases += [("PLACEHOLDER", PLACEHOLDER), ("CRASHSTRING", CRASH), ("EYE_shipped", EYE)]

    res = {}
    for name, text in cases:
        tokens = clip.tokenize(text)
        ntok = len(tokens["qwen3_4b"][0])
        out = clip.encode_from_tokens_scheduled(tokens)
        cond = out[0][0]
        extra = out[0][1]
        r = {"name": name, "tokens": ntok, "cond": stats(cond)}
        for k, v in extra.items():
            if isinstance(v, torch.Tensor):
                r[f"extra_{k}"] = stats(v)
        res[name] = r
        c = r["cond"]
        print(f"{name:14s} tok={ntok:3d} shape={c['shape']} finite={c['finite']} "
              f"nan={c['nan']} inf={c['inf']} absmax={c['absmax']} std={c['std']}", flush=True)

    json.dump(res, open(os.path.join(OUT, f"{a.tag}_cond.json"), "w"), indent=1)
    print("wrote", os.path.join(OUT, f"{a.tag}_cond.json"))


if __name__ == "__main__":
    main()
