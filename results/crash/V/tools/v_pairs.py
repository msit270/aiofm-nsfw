#!/usr/bin/env python3
"""Objective deltas between two arms' delivered frames.

Used for "the fix must be inert where nothing was wrong". NOT a hash comparison:
this project bans verifying by hashing rendered output, because run-to-run noise
sits near 48.7 dB and matching hashes are a strong attractor rather than proof.
What is reported is PSNR, max |diff| and mean |diff| per channel, alongside a
same-arm-repeat pair that gives this box's own run-to-run floor for comparison.
"""
import sys, os, glob, json
import numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS = None

ROOT = "/workspace/nsfw-fix/results/crash/V/arms"


def frame(arm, kind="n505"):
    f = sorted(glob.glob(os.path.join(ROOT, arm, f"{kind}__*.png")))
    if not f:
        f = sorted(glob.glob(os.path.join(ROOT, arm, "nTAP163__*.png")))
    return np.asarray(Image.open(f[0]).convert("RGB")) if f else None


def cmp(a, b, kind="n505"):
    x, y = frame(a, kind), frame(b, kind)
    if x is None or y is None:
        return {"a": a, "b": b, "error": "missing frame"}
    if x.shape != y.shape:
        return {"a": a, "b": b, "error": f"shape {x.shape} vs {y.shape}"}
    d = np.abs(x.astype(np.int32) - y.astype(np.int32))
    mse = float((d.astype(np.float64) ** 2).mean())
    return {"a": a, "b": b, "shape": list(x.shape),
            "psnr_db": 99.0 if mse == 0 else round(10 * np.log10(255 * 255 / mse), 2),
            "max_abs_diff": int(d.max()), "mean_abs_diff": round(float(d.mean()), 5),
            "frac_pixels_differing": round(float((d.max(2) > 0).mean()), 5),
            "frac_pixels_diff_gt_1": round(float((d.max(2) > 1).mean()), 5)}


if __name__ == "__main__":
    pairs = [tuple(p.split("=")) for p in sys.argv[1:]]
    out = [cmp(a, b) for a, b in pairs]
    for r in out:
        if "error" in r:
            print(f"{r['a']} vs {r['b']}: {r['error']}")
        else:
            print(f"{r['a']:22s} vs {r['b']:22s}  PSNR {r['psnr_db']:6.2f} dB  "
                  f"maxdiff {r['max_abs_diff']:3d}  meandiff {r['mean_abs_diff']:.5f}  "
                  f"pix!=  {r['frac_pixels_differing']:.5f}")
    json.dump(out, open("/workspace/nsfw-fix/results/crash/V/out/v_pairs.json", "w"), indent=1)
