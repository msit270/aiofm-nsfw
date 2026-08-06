#!/usr/bin/env python3
"""E4 -- how different is the conditioning when 620:110 runs on the CPU?

`E18_alt*` showed, interleaved 2/2 against 2/2, that setting `620:110.device`
to "cpu" turns the crash into a clean render on :18188. That arm changes two
things at once, so this measures the first of them directly: the conditioning
tensor itself, CPU vs cuda:0, same file, same fp16 weights.

  identical  -> the CPU arm cannot be about conditioning values; it is the
                memory timeline (the encoder no longer sits in VRAM during the
                face pass)
  different  -> the size of the perturbation says how knife-edge this is
"""
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


def load(dev):
    mo = {}
    if dev == "cpu":
        mo["load_device"] = mo["offload_device"] = torch.device("cpu")
    p = folder_paths.get_full_path_or_raise("text_encoders", "qwen.safetensors")
    return comfy.sd.load_clip(ckpt_paths=[p],
                              embedding_directory=folder_paths.get_folder_paths("embeddings"),
                              clip_type=comfy.sd.CLIPType.LUMINA2, model_options=mo)


def enc(clip, text):
    return clip.encode_from_tokens_scheduled(clip.tokenize(text))[0][0].float().cpu()


cases = {"PLACEHOLDER": PLACEHOLDER, "CRASHSTRING": CRASH}
for n in (29, 30, 31, 32, 33, 43, 44, 45, 46):
    cases[f"tok{n}"] = BASE + " the" * (n - 12)

g = load("default")
gpu = {k: enc(g, v) for k, v in cases.items()}
del g
torch.cuda.empty_cache()
c = load("cpu")
cpu = {k: enc(c, v) for k, v in cases.items()}

res = {}
for k in cases:
    a, b = gpu[k], cpu[k]
    d = (a - b).abs()
    res[k] = {"tokens": int(a.shape[1]),
              "identical": bool(torch.equal(a, b)),
              "max_abs_diff": float(d.max()),
              "mean_abs_diff": float(d.mean()),
              "rel_max": float((d / (a.abs() + 1e-6)).max()),
              "gpu_absmax": float(a.abs().max()), "cpu_absmax": float(b.abs().max()),
              "gpu_finite": bool(torch.isfinite(a).all()), "cpu_finite": bool(torch.isfinite(b).all())}
    r = res[k]
    print(f"{k:14s} L={r['tokens']:3d} identical={r['identical']} "
          f"max|d|={r['max_abs_diff']:.6g} mean|d|={r['mean_abs_diff']:.6g} "
          f"gpu_absmax={r['gpu_absmax']:.6g} finite gpu/cpu={r['gpu_finite']}/{r['cpu_finite']}", flush=True)

json.dump(res, open(os.path.join(OUT, "e4_cpu_vs_gpu.json"), "w"), indent=1)
print("wrote e4_cpu_vs_gpu.json")
