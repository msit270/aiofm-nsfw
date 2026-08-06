#!/usr/bin/env python3
"""Offline replication of what the graph's failing detector does.

`622:424 BboxDetectorSEGS` -> Impact-Subpack `UltraBBoxDetector.detect`, whose
only inference call is (subcore.py:319-325):

    pred = model(image, conf=confidence, device=device)     # image is a PIL RGB

so `YOLO(face_yolov8m.pt)(pil, conf=t)` is the same call, with ultralytics'
default imgsz/letterbox. No ComfyUI involved.
"""
import sys, json, os
import numpy as np
from PIL import Image

MODEL = "/workspace/ComfyUI/models/ultralytics/bbox/face_yolov8m.pt"
THRESHOLDS = [0.6, 0.5, 0.4, 0.3, 0.2, 0.1]


def run(paths, device="cpu"):
    from ultralytics import YOLO
    m = YOLO(MODEL)
    out = {}
    for p in paths:
        im = Image.open(p).convert("RGB")
        row = {"path": p, "size": list(im.size), "per_threshold": {}}
        for t in THRESHOLDS:
            pred = m(im, conf=t, device=device, verbose=False)
            b = pred[0].boxes
            confs = sorted([float(c) for c in b.conf.cpu().numpy()], reverse=True) if len(b) else []
            boxes = [[round(float(v), 1) for v in x] for x in b.xyxy.cpu().numpy()] if len(b) else []
            row["per_threshold"][str(t)] = {"n": len(confs), "max_conf": (confs[0] if confs else None),
                                            "confs": confs[:8], "boxes": boxes[:8]}
        # the number the brief asks for: highest confidence at the loosest threshold
        row["highest_conf_seen"] = row["per_threshold"]["0.1"]["max_conf"]
        a = np.asarray(im).astype(np.float32)
        luma = 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]
        row["luma_sd"] = round(float(luma.std()), 2)
        row["flat_frac"] = round(float((np.abs(np.diff(luma, axis=1)) < 0.5).mean()), 4)
        out[os.path.basename(p)] = row
    return out


if __name__ == "__main__":
    res = run(sys.argv[1:])
    print(json.dumps(res, indent=1))
