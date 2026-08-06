#!/usr/bin/env python3
"""E2b -- run the graph's own Z-Image DiT (620:113 zimage.safetensors) offline and
ask whether its OUTPUT goes non-finite as a function of the conditioning length.

No ComfyUI server is touched. Latent geometry matches the face pass's real crop:
the server log for the face pass reads
    Detailer: segment upscale for ((1340.1992, 1906.2034)) | crop region (2010, 2859) x 1.0
so the tile handed to the sampler is 2010x2859 px -> latent 251 x 357 (w x h).

modes:
  fwd   one diffusion_model() forward per conditioning at a fixed sigma  (cheap)
  samp  the real sampler: euler_ancestral / kl_optimal / 8 steps / cfg 1 /
        denoise 0.8, i.e. 620:114's own settings                          (slow)
"""
import sys, os, json, argparse, time
sys.path.insert(0, "/workspace/ComfyUI")
os.chdir("/workspace/ComfyUI")
import torch
import comfy.sd
import comfy.utils
import comfy.sample
import comfy.samplers
import comfy.model_management as mm
import folder_paths

OUT = "/workspace/nsfw-fix/results/crash/E/out"


def fin(t):
    tf = t.float()
    nan = int(torch.isnan(tf).sum().item())
    inf = int(torch.isinf(tf).sum().item())
    good = tf[torch.isfinite(tf)]
    return {"nan": nan, "inf": inf, "n": int(tf.numel()),
            "absmax": float(good.abs().max().item()) if good.numel() else None,
            "std": float(good.std().item()) if good.numel() > 1 else None,
            "mean": float(good.mean().item()) if good.numel() else None}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", default="fwd", choices=["fwd", "samp"])
    ap.add_argument("--names", default="")
    ap.add_argument("--lo", type=int, default=26)
    ap.add_argument("--hi", type=int, default=50)
    ap.add_argument("--sigma", type=float, default=0.8)
    ap.add_argument("--lat-h", type=int, default=357)
    ap.add_argument("--lat-w", type=int, default=251)
    ap.add_argument("--lora", default="")
    ap.add_argument("--seed", type=int, default=1111111)
    ap.add_argument("--tag", default="e2b")
    a = ap.parse_args(sys.argv[1:])

    conds = torch.load(os.path.join(OUT, "conds.pt"))
    meta = json.load(open(os.path.join(OUT, "conds_meta.json")))

    if a.names:
        names = [n for n in a.names.split(",") if n]
    else:
        names = [f"tok{n}" for n in range(a.lo, a.hi + 1) if f"tok{n}" in conds]

    unet = folder_paths.get_full_path_or_raise("diffusion_models", "zimage.safetensors")
    mp = comfy.sd.load_diffusion_model(unet)
    if a.lora:
        lp = folder_paths.get_full_path_or_raise("loras", a.lora)
        lora = comfy.utils.load_torch_file(lp, safe_load=True)
        mp, _ = comfy.sd.load_lora_for_models(mp, None, lora, 1.0, 0.0)
        print("LoRA applied to UNET:", a.lora, flush=True)
    mm.load_model_gpu(mp)
    dm = mp.model.diffusion_model
    dev = mp.load_device
    dt = mp.model.get_dtype()
    print("dit dtype", dt, "device", dev, "pad_tokens_multiple",
          getattr(dm, "pad_tokens_multiple", None), flush=True)

    torch.manual_seed(a.seed)
    x0 = torch.randn(1, 16, a.lat_h, a.lat_w, generator=torch.Generator().manual_seed(a.seed))
    res = {}

    for name in names:
        c = conds[name].to(device=dev, dtype=dt)
        L = c.shape[1]
        t0 = time.time()
        if a.mode == "fwd":
            x = x0.to(device=dev, dtype=dt)
            ts = torch.tensor([a.sigma], device=dev, dtype=dt)
            with torch.no_grad():
                o = dm(x, ts, context=c, num_tokens=L, transformer_options={})
            r = fin(o)
        else:
            latent = {"samples": x0.clone() * 0.0}
            noise = comfy.sample.prepare_noise(latent["samples"], a.seed)
            pos = [[conds[name].clone(), {}]]
            neg = [[conds["PLACEHOLDER"].clone() * 0.0, {}]]
            s = comfy.sample.sample(mp, noise, 8, 1.0, "euler_ancestral", "kl_optimal",
                                    pos, neg, latent["samples"], denoise=0.8,
                                    disable_noise=False, seed=a.seed)
            r = fin(s)
        r["tokens"] = L
        r["seconds"] = round(time.time() - t0, 1)
        res[name] = r
        bad = r["nan"] or r["inf"]
        print(f"{name:18s} L={L:3d} {'*** NON-FINITE ***' if bad else 'finite          '} "
              f"nan={r['nan']} inf={r['inf']} absmax={r['absmax']} std={r['std']} {r['seconds']}s",
              flush=True)

    json.dump({"args": vars(a), "results": res},
              open(os.path.join(OUT, f"{a.tag}_{a.mode}.json"), "w"), indent=1)
    print("wrote", os.path.join(OUT, f"{a.tag}_{a.mode}.json"))


if __name__ == "__main__":
    main()
