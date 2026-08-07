#!/usr/bin/env python3
"""Q2 objective deltas — no GPU, no server. Run after the arms.

Per arm, against the baseline arm's delivered 505 frame:
  * full-frame: max_abs_diff, mean_abs_diff, %pixels differing, %pixels moving
    more than 8 levels, PSNR
  * face-crop (YOLO face_yolov8m.pt per image — never a fixed box): same
    metrics over ONE common union box so crops are comparable
  * health: modal_frac / flat_frac / luma_sd (fresh implementation — comparable
    only within this session)
The baseline-vs-repeat row IS the same-window noise floor; every other row is
read against it.

Writes q2_metrics.json next to the arms and prints a markdown table.
"""
import glob
import json
import os
import sys

import numpy as np
from PIL import Image

Q2 = "/workspace/nsfw-fix/results/run4/quality/Q2"
YOLO_W = "/workspace/ComfyUI/models/ultralytics/bbox/face_yolov8m.pt"
BASELINE = "A_cf15_baseline"


def delivered(arm):
    c = sorted(glob.glob(f"{Q2}/{arm}/n505__*.png"))
    return c[0] if c else None


def arms():
    out = []
    for d in sorted(os.listdir(Q2)):
        mp = os.path.join(Q2, d, "meta.json")
        if os.path.isdir(os.path.join(Q2, d)) and os.path.exists(mp):
            out.append((d, json.load(open(mp))))
    return out


def img(p):
    return np.asarray(Image.open(p).convert("RGB")).astype(np.int64)


def pair_metrics(a, b):
    d = np.abs(a - b)
    mse = float((d.astype(np.float64) ** 2).mean())
    return {
        "max_abs_diff": int(d.max()),
        "mean_abs_diff": round(float(d.mean()), 4),
        "pct_pixels_differing": round(float((d.sum(axis=2) > 0).mean()) * 100, 2),
        "pct_pixels_gt8": round(float((d.max(axis=2) > 8).mean()) * 100, 2),
        "psnr_db": round(10 * np.log10(255 * 255 / mse), 2) if mse > 0 else None,
    }


def health(a):
    flat = a.reshape(-1, 3)
    colors, counts = np.unique(flat, axis=0, return_counts=True)
    mi = int(counts.argmax())
    luma = 0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]
    gx = np.abs(np.diff(luma, axis=1))
    gy = np.abs(np.diff(luma, axis=0))
    flat_frac = float(((gx[:-1, :] == 0) & (gy[:, :-1] == 0)).mean())
    return {
        "modal_rgb": [int(x) for x in colors[mi]],
        "modal_frac": round(float(counts[mi]) / flat.shape[0], 5),
        "flat_frac": round(flat_frac, 5),
        "luma_sd": round(float(luma.std()), 3),
    }


def facebox(path):
    from ultralytics import YOLO
    m = YOLO(YOLO_W)
    r = m(path, verbose=False)[0]
    if not len(r.boxes):
        return None
    bi = int(r.boxes.conf.argmax())
    x1, y1, x2, y2 = [float(v) for v in r.boxes.xyxy[bi].tolist()]
    return (x1, y1, x2, y2, float(r.boxes.conf[bi]))


def main():
    rows = []
    base_img = None
    base_path = delivered(BASELINE)
    if base_path is None:
        sys.exit(f"no delivered frame for baseline {BASELINE}")
    base_img = img(base_path)
    H, W = base_img.shape[:2]

    # one common face box: union of all detections + 8% pad per axis
    dets = {}
    for name, meta in arms():
        p = delivered(name)
        if p:
            dets[name] = facebox(p)
    good = [v for v in dets.values() if v]
    if good:
        x1 = min(v[0] for v in good); y1 = min(v[1] for v in good)
        x2 = max(v[2] for v in good); y2 = max(v[3] for v in good)
        pw, ph = 0.08 * (x2 - x1), 0.08 * (y2 - y1)
        fb = (max(0, int(x1 - pw)), max(0, int(y1 - ph)),
              min(W, int(x2 + pw)), min(H, int(y2 + ph)))
    else:
        fb = None

    for name, meta in arms():
        p = delivered(name)
        row = {"arm": name, "bbox_crop_factor": meta.get("bbox_crop_factor"),
               "status": meta.get("status"), "exec_seconds": meta.get("exec_seconds"),
               "execution_cached": meta.get("execution_cached"),
               "prompt_id": meta.get("prompt_id"), "image": p and os.path.basename(p)}
        if p:
            a = img(p)
            row["health"] = health(a)
            row["face_det"] = dets.get(name) and {
                "xyxy": [round(v, 1) for v in dets[name][:4]],
                "conf": round(dets[name][4], 4)}
            if a.shape == base_img.shape and name != BASELINE:
                row["vs_baseline_full"] = pair_metrics(a, base_img)
                if fb:
                    row["vs_baseline_face"] = pair_metrics(
                        a[fb[1]:fb[3], fb[0]:fb[2]], base_img[fb[1]:fb[3], fb[0]:fb[2]])
        rows.append(row)

    out = {"baseline": BASELINE, "common_face_box_xyxy": fb and list(fb),
           "image_size": [W, H], "rows": rows}
    json.dump(out, open(os.path.join(Q2, "q2_metrics.json"), "w"), indent=1)

    print(f"common face box (union of per-image YOLO dets, 8% pad): {fb}")
    print()
    hdr = ("| arm | cf | status | exec s | cached | face conf | full PSNR dB | "
           "full %px>8 | face PSNR dB | face %px>8 | modal_frac |")
    print(hdr)
    print("|" + "---|" * 11)
    for r in rows:
        f = r.get("vs_baseline_full") or {}
        fc = r.get("vs_baseline_face") or {}
        h = r.get("health") or {}
        fd = r.get("face_det") or {}
        print(f"| {r['arm']} | {r['bbox_crop_factor']} | {r['status']} | "
              f"{r['exec_seconds']} | {r['execution_cached'] == [] and 'cold' or r['execution_cached']} | "
              f"{fd.get('conf', '-')} | {f.get('psnr_db', '-')} | {f.get('pct_pixels_gt8', '-')} | "
              f"{fc.get('psnr_db', '-')} | {fc.get('pct_pixels_gt8', '-')} | {h.get('modal_frac', '-')} |")


if __name__ == "__main__":
    main()
