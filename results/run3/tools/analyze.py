#!/usr/bin/env python3
"""Run-3 analysis: A6 pixel-identity check and the DoD-5 eye-tile sheet.

  analyze.py ab16                    # guarded vs unguarded happy path: pixel identity
  analyze.py pair <armA> <armB>      # generic delivered-frame pixel compare
  analyze.py eyesheet <out.png> <arm:label> [<arm:label> ...]
                                     # 1:1 eye-band tiles, YOLO face box per image,
                                     # red banner, no downscaling
"""
import sys, os, glob, json
import numpy as np
from PIL import Image, ImageDraw

ARMS = "/workspace/nsfw-fix/results/run3/arms"
YOLO = "/workspace/ComfyUI/models/ultralytics/bbox/face_yolov8m.pt"


def delivered(arm):
    c = sorted(glob.glob(f"{ARMS}/{arm}/n505__*.png"))
    assert c, f"no delivered frame for {arm}"
    return c[0]


def pair(a, b):
    ia = np.asarray(Image.open(delivered(a)).convert("RGB")).astype(int)
    ib = np.asarray(Image.open(delivered(b)).convert("RGB")).astype(int)
    assert ia.shape == ib.shape, (ia.shape, ib.shape)
    d = np.abs(ia - ib)
    r = {"a": a, "b": b, "shape": list(ia.shape), "max_abs_diff": int(d.max()),
         "pixels_differing": float((d.sum(axis=2) > 0).mean()),
         "mean_abs_diff": float(d.mean())}
    print(json.dumps(r, indent=1))
    return r


def facebox(img_path):
    from ultralytics import YOLO as Y
    m = Y(YOLO)
    res = m(img_path, verbose=False)[0]
    assert len(res.boxes), f"no face detected in {img_path}"
    bi = int(res.boxes.conf.argmax())
    x1, y1, x2, y2 = [int(v) for v in res.boxes.xyxy[bi].tolist()]
    return x1, y1, x2, y2, float(res.boxes.conf[bi])


def eyesheet(out, specs, band=(0.18, 0.55), banner=None):
    tiles, labels = [], []
    for spec in specs:
        arm, _, label = spec.partition(":")
        p = delivered(arm)
        x1, y1, x2, y2, conf = facebox(p)
        # band: fraction of the face box height, full box width, 1:1
        h = y2 - y1
        ey1, ey2 = y1 + int(band[0] * h), y1 + int(band[1] * h)
        img = Image.open(p).convert("RGB").crop((x1, ey1, x2, ey2))
        tiles.append(img)
        labels.append(f"{label or arm}   (YOLO {conf:.3f})  crop {x2-x1}x{ey2-ey1} @1:1")
    W = max(t.width for t in tiles)
    BANNER, LABEL = 64, 34
    H = BANNER + sum(t.height + LABEL for t in tiles)
    sheet = Image.new("RGB", (W, H), (12, 12, 12))
    dr = ImageDraw.Draw(sheet)
    dr.rectangle([0, 0, W, BANNER], fill=(140, 20, 20))
    dr.text((12, 8), banner or
            "RUN3 EYE BAND -- same seed, cold, 1:1 native pixels, no resampling.\n"
            "Rows differ ONLY in which device encodes which Z-Image prompts.",
            fill=(255, 255, 255))
    y = BANNER
    for t, lab in zip(tiles, labels):
        dr.rectangle([0, y, W, y + LABEL], fill=(30, 30, 30))
        dr.text((12, y + 8), lab, fill=(255, 220, 120))
        y += LABEL
        sheet.paste(t, (0, y))
        y += t.height
    sheet.save(out)
    # verify 1:1: re-open and byte-compare one tile region
    re = np.asarray(Image.open(out).convert("RGB"))
    y = BANNER + LABEL
    t0 = np.asarray(tiles[0])
    assert (re[y:y + t0.shape[0], 0:t0.shape[1]] == t0).all(), "tile not 1:1!"
    print(f"sheet written {out}  {W}x{H}, tiles verified 1:1")


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "ab16":
        r = pair("R3_AB_unguard_16", "R3_AB_guard_16")
        print("A6 VERDICT:", "BYTE-IDENTICAL PIXELS" if r["max_abs_diff"] == 0 else "NOT IDENTICAL — STOP")
    elif cmd == "pair":
        pair(sys.argv[2], sys.argv[3])
    elif cmd == "eyesheet":
        eyesheet(sys.argv[2], sys.argv[3:])
    elif cmd == "mouthsheet":
        eyesheet(sys.argv[2], sys.argv[3:], band=(0.55, 1.0),
                 banner="RUN3 MOUTH BAND -- same graph, cold, 1:1 native pixels, no resampling.\n"
                        "Rows differ ONLY in 620:648 max_value (the mouth-guard ceiling).")
