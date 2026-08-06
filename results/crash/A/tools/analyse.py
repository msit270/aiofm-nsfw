#!/usr/bin/env python3
"""Run the graph's own detector, offline, over the 621:163 tap of every arm.

This turns the binary crash/clean outcome into the underlying continuous
quantity -- the face confidence the detector would return -- so the shape of the
transition is visible rather than inferred.
"""
import os, sys, json, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import yolo_probe

ARMS = "/workspace/nsfw-fix/results/crash/A/arms"
OUT = "/workspace/nsfw-fix/results/crash/A/arm_yolo.json"


def main(only=None):
    res = {}
    if os.path.exists(OUT):
        res = json.load(open(OUT))
    from ultralytics import YOLO
    m = YOLO(yolo_probe.MODEL)
    from PIL import Image
    import numpy as np
    for d in sorted(os.listdir(ARMS)):
        p = os.path.join(ARMS, d)
        if not os.path.isdir(p):
            continue
        if only and d not in only:
            continue
        if res.get(d, {}).get("status") is not None:
            continue                      # only cache rows that actually landed
        taps = glob.glob(os.path.join(p, "nTAP163__*.png"))
        meta = json.load(open(os.path.join(p, "meta.json"))) if os.path.exists(os.path.join(p, "meta.json")) else {}
        row = {"status": meta.get("status"), "prompt_id": meta.get("prompt_id"),
               "exec_seconds": meta.get("exec_seconds"), "cached": meta.get("cached"),
               "text": meta.get("text_106"), "error_node": meta.get("error_node"),
               "tap": os.path.basename(taps[0]) if taps else None}
        if taps:
            im = Image.open(taps[0]).convert("RGB")
            per = {}
            for t in yolo_probe.THRESHOLDS:
                pred = m(im, conf=t, device="cpu", verbose=False)
                b = pred[0].boxes
                per[str(t)] = {"n": len(b),
                               "max_conf": (float(b.conf.max()) if len(b) else None)}
            row["per_threshold"] = per
            row["highest_conf"] = per["0.1"]["max_conf"]
            a = np.asarray(im).astype(np.float32)
            l = 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]
            row["luma_sd"] = round(float(l.std()), 2)
            row["flat_frac"] = round(float((np.abs(np.diff(l, axis=1)) < 0.5).mean()), 4)
        res[d] = row
        json.dump(res, open(OUT, "w"), indent=1)
        print(f"{d:28s} {str(row['status']):8s} conf={row.get('highest_conf')} "
              f"n@0.6={row.get('per_threshold',{}).get('0.6',{}).get('n')} "
              f"flat={row.get('flat_frac')}", flush=True)
    return res


if __name__ == "__main__":
    main(set(sys.argv[1:]) or None)
