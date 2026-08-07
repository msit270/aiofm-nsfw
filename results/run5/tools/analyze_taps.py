#!/usr/bin/env python3
"""Per-tap texture + lighting analysis along the pipeline chain.

For each arm dir: for each tap PNG, detect the face (multi-scale, likeness.py
logic), then measure inside the face box and on a body-skin patch:
  - lapvar: variance of Laplacian (micro-detail energy) on L channel
  - highfreq: band-pass RMS 1.5-8 px (freckle/pore band)
  - p5/p50/p95 luma percentiles (shadow depth / key / highlight)
  - sat: mean HSV saturation ; warmth: mean (R-B)
Face box from detector; body patch = box of same size directly below the face
box (clamped), which lands on chest/torso in these compositions.
Everything is computed at a COMMON working scale: the frame is resized so the
face box is 512 px tall before measuring (stage resolutions differ; this
normalizes the band definitions).
Output: results/run5/tap_metrics.json (merged) + printed table per arm.
"""
import sys, os, json, glob
import numpy as np
import cv2

sys.path.insert(0, "/workspace/run5/tools")
from likeness import top_face

OUT = "/workspace/run5/output"
DEST = "/workspace/nsfw-quality/results/run5/tap_metrics.json"


def measure(path):
    f = top_face(path)
    img = cv2.imread(path)
    if img is None or f is None:
        return None
    h, w = img.shape[:2]
    # bbox came from a detection variant; rescale to full-res coords
    via = f.get("via", "full@640")
    tag = via.split("@")[0]
    x1, y1, x2, y2 = f["bbox"]
    if tag == "half":
        x1, y1, x2, y2 = [v * 2 for v in (x1, y1, x2, y2)]
    elif tag == "quarter":
        x1, y1, x2, y2 = [v * 4 for v in (x1, y1, x2, y2)]
    elif tag == "upper":
        x1, y1 = x1 + w * 0.15, y1
        x2, y2 = x2 + w * 0.15, y2
    bh = y2 - y1
    if bh < 10:
        return None
    # normalize: face box height -> 512 px
    s = 512.0 / bh
    img_s = cv2.resize(img, (int(w * s), int(h * s)), interpolation=cv2.INTER_AREA)
    X1, Y1, X2, Y2 = [int(v * s) for v in (x1, y1, x2, y2)]
    H, W = img_s.shape[:2]
    def clamp(a, lo, hi):
        return max(lo, min(hi, a))
    def patch_stats(px):
        lab = cv2.cvtColor(px, cv2.COLOR_BGR2LAB)
        L = lab[:, :, 0].astype(np.float32)
        lap = cv2.Laplacian(L, cv2.CV_32F)
        # freckle/pore band: gaussian band-pass 1.5-8px
        g1 = cv2.GaussianBlur(L, (0, 0), 1.5)
        g2 = cv2.GaussianBlur(L, (0, 0), 8.0)
        band = g1 - g2
        hsv = cv2.cvtColor(px, cv2.COLOR_BGR2HSV)
        b, g, r = px[:, :, 0].astype(np.float32), px[:, :, 1].astype(np.float32), px[:, :, 2].astype(np.float32)
        luma = 0.2126 * r + 0.7152 * g + 0.0722 * b
        return {"lapvar": float(lap.var()),
                "highfreq_rms": float(np.sqrt((band ** 2).mean())),
                "p5": float(np.percentile(luma, 5)),
                "p50": float(np.percentile(luma, 50)),
                "p95": float(np.percentile(luma, 95)),
                "sat": float(hsv[:, :, 1].mean()),
                "warmth": float((r - b).mean())}
    fx1, fy1, fx2, fy2 = (clamp(X1, 0, W - 2), clamp(Y1, 0, H - 2),
                          clamp(X2, 2, W), clamp(Y2, 2, H))
    face = img_s[fy1:fy2, fx1:fx2]
    # body patch: same box shifted down by 1.2*boxheight (chest/torso)
    off = int((fy2 - fy1) * 1.2)
    by1, by2 = clamp(fy1 + off, 0, H - 2), clamp(fy2 + off, 2, H)
    body = img_s[by1:by2, fx1:fx2]
    r = {"face": patch_stats(face)}
    if body.shape[0] > 50:
        r["body"] = patch_stats(body)
    # frame-level lighting
    small = cv2.resize(img, (min(w, 768), int(h * min(w, 768) / w)))
    b, g, rr = small[:, :, 0].astype(np.float32), small[:, :, 1].astype(np.float32), small[:, :, 2].astype(np.float32)
    luma = 0.2126 * rr + 0.7152 * g + 0.0722 * b
    r["frame"] = {"p5": float(np.percentile(luma, 5)),
                  "p95": float(np.percentile(luma, 95)),
                  "luma_sd": float(luma.std()),
                  "warmth": float((rr - b).mean())}
    r["face_px_h"] = float(bh)
    return r


def main():
    dirs = sys.argv[1:]
    res = json.load(open(DEST)) if os.path.exists(DEST) else {}
    for d in dirs:
        for p in sorted(glob.glob(os.path.join(d, "**", "*.png"), recursive=True)):
            rel = os.path.relpath(p, OUT)
            if rel in res:
                continue
            m = measure(p)
            res[rel] = m
            print("measured", rel, "ok" if m else "SKIP", flush=True)
    json.dump(res, open(DEST, "w"), indent=1)
    # table for the requested dirs
    print(f"\n{'tap':64s} {'faceHF':>7s} {'bodyHF':>7s} {'f-lap':>8s} {'fr-p5':>6s} {'fr-sd':>6s} {'warm':>6s}")
    for d in dirs:
        pref = os.path.relpath(d, OUT)
        for rel in sorted(res):
            if not rel.startswith(pref) or res[rel] is None:
                continue
            m = res[rel]
            body = m.get("body", {})
            print(f"{rel:64s} {m['face']['highfreq_rms']:7.3f} "
                  f"{body.get('highfreq_rms', float('nan')):7.3f} "
                  f"{m['face']['lapvar']:8.1f} {m['frame']['p5']:6.1f} "
                  f"{m['frame']['luma_sd']:6.1f} {m['frame']['warmth']:6.1f}")


if __name__ == "__main__":
    main()
