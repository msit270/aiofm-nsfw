#!/usr/bin/env python3
"""E9 -- "status: success" is not evidence of a good image (Track A's E398_tok31
shipped a success with two black eye-holes). This measures the 621:163 taps of
every Track E arm that produced one: the fraction of the frame that is a single
modal colour, the exact-black fraction, and flat_frac, plus PSNR against the
known-good placeholder render."""
import os, json, glob
import numpy as np
from PIL import Image
Image.MAX_IMAGE_PIXELS = None

ROOT = "/workspace/nsfw-fix/results/crash/E/arms"
REF = None


def load(p):
    return np.asarray(Image.open(p).convert("RGB"))


def stats(a):
    f = a.astype(np.float32)
    flat = float((np.abs(np.diff(f, axis=1)).max(2) < 0.5).mean())
    black = float((a.sum(2) == 0).mean())
    packed = (a[:, :, 0].astype(np.uint32) << 16) | (a[:, :, 1].astype(np.uint32) << 8) | a[:, :, 2]
    vals, cnt = np.unique(packed, return_counts=True)
    i = int(cnt.argmax())
    v = int(vals[i])
    return {"flat_frac": round(flat, 4), "exact_black_frac": round(black, 5),
            "modal_rgb": [(v >> 16) & 255, (v >> 8) & 255, v & 255],
            "modal_frac": round(float(cnt[i]) / packed.size, 4),
            "luma_sd": round(float(f.mean(2).std()), 2)}


def psnr(a, b):
    d = (a.astype(np.float64) - b.astype(np.float64))
    mse = (d ** 2).mean()
    return 99.0 if mse == 0 else round(10 * np.log10(255 * 255 / mse), 2)


if __name__ == "__main__":
    out = {}
    ref = None
    for d in sorted(glob.glob(os.path.join(ROOT, "*"))):
        taps = glob.glob(os.path.join(d, "nTAP163__*.png"))
        if not taps:
            continue
        name = os.path.basename(d)
        a = load(taps[0])
        s = stats(a)
        meta = json.load(open(os.path.join(d, "meta.json")))
        s["status"] = meta.get("status")
        s["error_node"] = meta.get("error_node")
        if name == "E18_placeholder_ctl":
            ref = a
        out[name] = (a, s)
    rows = []
    for name, (a, s) in out.items():
        s["psnr_vs_18188_placeholder"] = psnr(a, ref) if ref is not None and a.shape == ref.shape else None
        rows.append((name, s))
    for name, s in rows:
        print(f"{name:26s} {str(s['status']):8s} black={s['exact_black_frac']:.5f} "
              f"flat={s['flat_frac']:.4f} modal={str(s['modal_rgb']):15s} mfrac={s['modal_frac']:.4f} "
              f"psnr_vs_ctl={s['psnr_vs_18188_placeholder']}")
    json.dump({n: s for n, s in rows},
              open("/workspace/nsfw-fix/results/crash/E/out/e9_images.json", "w"), indent=1)
