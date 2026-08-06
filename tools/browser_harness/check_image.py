#!/usr/bin/env python3
"""Is this actually a render, or the silent flat-grey failure delivered as success?

`status: success` is not an image. The failure mode this exists to catch delivers a
PNG in which a face-sized region is a constant fill, and it has already produced
confident wrong conclusions on this project.

The two continuous quantities are Track A's, reused unchanged so the numbers are
comparable with `results/crash/A/arm_yolo.json`:

    luma_sd    std of the luma plane over the whole frame
    flat_frac  fraction of horizontally adjacent pixel pairs whose luma differs by
               less than 0.5   (results/crash/A/tools/analyse.py:50-51)

plus two that catch a flat region too small to move a whole-frame average:

    grey53_frac      fraction of pixels within +-3 of the poisoned grey (53,47,43),
                     the value R2 measured at 0.118 % on a known-good render
    flat_block_frac  fraction of 64x64 blocks whose luma std is under 1.0

Pass one or more PNGs. Exit 0 if every image passes, 1 if any looks like the failure,
2 if it could not be measured.  --json <path> writes the numbers out.
"""
import json
import sys

import numpy as np
from PIL import Image

Image.MAX_IMAGE_PIXELS = None

# Calibrated against real images rather than chosen by eye, because the first set I
# picked flagged a KNOWN-GOOD control. Measured with this script:
#
#   flat_block_frac   R2 run 3 delivered image  0.0066   clean
#                     Track A arm L_w16 tap     0.0220   clean
#                     Track A arm A1 crash tap  0.1834   the face-shaped void
#   flat_frac         0.2346 / 0.1859 clean, 0.3591 on the void
#   grey53_frac       0.0012 / 0.0017 clean, 0.0000 on the void  <- the void is NOT
#                     the poisoned grey; they are two different failures, so both
#                     numbers are kept.
#
# 0.08 sits 3.6x above the worst clean control and 2.3x below the failure. Two clean
# samples that themselves differ by 3.3x is a coarse instrument -- every number is
# printed so a human can overrule the verdict.
LIMITS = {
    "luma_sd_min": 10.0,
    "flat_frac_max": 0.50,
    "grey53_frac_max": 0.02,
    "flat_block_frac_max": 0.08,
}
POISONED_GREY = (53, 47, 43)


def measure(path):
    im = Image.open(path).convert("RGB")
    a = np.asarray(im).astype(np.float32)
    h, w, _ = a.shape
    lum = 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]

    grey = np.all(np.abs(a - np.array(POISONED_GREY, dtype=np.float32)) <= 3, axis=-1)

    bs = 64
    bh, bw = h // bs, w // bs
    if bh and bw:
        blocks = lum[: bh * bs, : bw * bs].reshape(bh, bs, bw, bs).transpose(0, 2, 1, 3)
        block_sd = blocks.reshape(bh * bw, bs * bs).std(axis=1)
        flat_block_frac = float((block_sd < 1.0).mean())
        flattest_block_sd = float(block_sd.min())
    else:
        flat_block_frac, flattest_block_sd = 0.0, None

    # largest single 4-bit colour bucket, the figure R2 quoted (4.78 % on a good render)
    q = (a.astype(np.uint8) >> 4).astype(np.int32)
    codes = (q[..., 0] << 8) | (q[..., 1] << 4) | q[..., 2]
    _, counts = np.unique(codes, return_counts=True)

    return {
        "path": path,
        "size": [w, h],
        "mean_rgb": [round(float(x), 2) for x in a.reshape(-1, 3).mean(axis=0)],
        "std_rgb": [round(float(x), 2) for x in a.reshape(-1, 3).std(axis=0)],
        "luma_sd": round(float(lum.std()), 2),
        "flat_frac": round(float((np.abs(np.diff(lum, axis=1)) < 0.5).mean()), 4),
        "grey53_frac": round(float(grey.mean()), 6),
        "flat_block_frac": round(flat_block_frac, 6),
        "flattest_block_sd": None if flattest_block_sd is None else round(flattest_block_sd, 3),
        "largest_4bit_bucket_frac": round(float(counts.max()) / float(codes.size), 4),
    }


def verdict(m):
    bad = []
    if m["luma_sd"] < LIMITS["luma_sd_min"]:
        bad.append(f"luma_sd {m['luma_sd']} < {LIMITS['luma_sd_min']} — the frame is flat")
    if m["flat_frac"] > LIMITS["flat_frac_max"]:
        bad.append(f"flat_frac {m['flat_frac']} > {LIMITS['flat_frac_max']}")
    if m["grey53_frac"] > LIMITS["grey53_frac_max"]:
        bad.append(f"grey53_frac {m['grey53_frac']} > {LIMITS['grey53_frac_max']} — poisoned-grey fill")
    if m["flat_block_frac"] > LIMITS["flat_block_frac_max"]:
        bad.append(f"flat_block_frac {m['flat_block_frac']} > {LIMITS['flat_block_frac_max']} — a flat REGION")
    return bad


def main(argv):
    out_json = None
    paths = []
    i = 0
    while i < len(argv):
        if argv[i] == "--json":
            i += 1
            out_json = argv[i]
        else:
            paths.append(argv[i])
        i += 1
    if not paths:
        print("usage: check_image.py [--json out.json] IMAGE [IMAGE...]", file=sys.stderr)
        return 2

    rows, worst = [], 0
    for p in paths:
        try:
            m = measure(p)
        except Exception as e:                       # noqa: BLE001
            print(f"  COULD NOT MEASURE {p}: {e}")
            rows.append({"path": p, "error": str(e)})
            worst = max(worst, 2)
            continue
        bad = verdict(m)
        m["verdict"] = "FLAT-GREY FAILURE" if bad else "looks like a real render"
        m["reasons"] = bad
        rows.append(m)
        print(f"  {p}")
        print(f"    {m['size'][0]}x{m['size'][1]}  mean {m['mean_rgb']}  std {m['std_rgb']}")
        print(f"    luma_sd {m['luma_sd']}   flat_frac {m['flat_frac']}   "
              f"grey53_frac {m['grey53_frac']}   flat_block_frac {m['flat_block_frac']}   "
              f"largest_4bit_bucket {m['largest_4bit_bucket_frac']}")
        print(f"    -> {m['verdict']}" + ("".join("\n       * " + b for b in bad)))
        if bad:
            worst = max(worst, 1)

    if out_json:
        with open(out_json, "w") as f:
            json.dump({"limits": LIMITS, "images": rows}, f, indent=2)
        print(f"  wrote {out_json}")
    return worst


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
