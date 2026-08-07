#!/usr/bin/env python3
"""Lighting proxies (research_lighting Q7 — PROXIES, not truth; same-seed
A/B deltas only). Per image:
  hist: P0.5/P5/P50/P95/P99.5 of linear luminance, f_black, f_white,
        rolloff=(P99.5-P95)/(P95-P50), shadow_depth=P5
  dirR: directional coherence of low-freq shading inside the face+body
        region (gaussian sigma~32px on L, gradient vector mean resultant)
  lc:   local RMS contrast in 32px tiles: mean(c), CV=std/mean
Usage: light_metrics.py <png> [...]  -> prints one JSON line per file and
appends to results/run5/light_metrics.json
"""
import sys, os, json
import numpy as np
import cv2

DEST = "/workspace/nsfw-quality/results/run5/light_metrics.json"


def srgb_to_linear(x):
    x = x / 255.0
    return np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4)


def measure(path):
    img = cv2.imread(path)
    if img is None:
        return None
    b, g, r = [srgb_to_linear(img[:, :, i].astype(np.float64)) for i in range(3)]
    L = 0.2126 * r + 0.7152 * g + 0.0722 * b
    P = lambda q: float(np.percentile(L, q))
    p05, p5, p50, p95, p995 = P(0.5), P(5), P(50), P(95), P(99.5)
    hist = {
        "P0.5": p05, "P5": p5, "P50": p50, "P95": p95, "P99.5": p995,
        "f_black": float((L < 2 / 255) .mean()),
        "f_white": float((L > 253 / 255).mean()),
        "rolloff": float((p995 - p95) / max(1e-6, p95 - p50)),
        "spread_95_5": p95 - p5,
    }
    # directional coherence on centre region (person area proxy: middle 60% w)
    h, w = L.shape
    roi = L[int(h * 0.05):int(h * 0.95), int(w * 0.2):int(w * 0.8)]
    small = cv2.resize(roi.astype(np.float32), (roi.shape[1] // 4, roi.shape[0] // 4))
    blur = cv2.GaussianBlur(small, (0, 0), 8)   # ~32px at full res
    gx = cv2.Sobel(blur, cv2.CV_32F, 1, 0)
    gy = cv2.Sobel(blur, cv2.CV_32F, 0, 1)
    wgt = np.sqrt(gx * gx + gy * gy)
    ang = np.arctan2(gy, gx)
    # double-angle so opposite directions (same light axis) reinforce
    R = float(np.abs((wgt * np.exp(2j * ang)).sum()) / max(1e-6, wgt.sum()))
    # local contrast dispersion, 32px tiles on full L
    ts = 32
    Hc, Wc = h // ts, w // ts
    tiles = L[:Hc * ts, :Wc * ts].reshape(Hc, ts, Wc, ts).transpose(0, 2, 1, 3)
    m = tiles.mean(axis=(2, 3))
    s = tiles.std(axis=(2, 3))
    c = s / np.maximum(m, 1e-4)
    lc = {"mean_c": float(c.mean()), "cv_c": float(c.std() / max(1e-6, c.mean()))}
    return {"hist": hist, "dirR": R, "lc": lc}


def main():
    res = json.load(open(DEST)) if os.path.exists(DEST) else {}
    for p in sys.argv[1:]:
        key = os.path.relpath(p, "/workspace/run5/output")
        m = measure(p)
        res[key] = m
        print(key, json.dumps({"P5": round(m['hist']['P5'], 4),
                               "spread": round(m['hist']['spread_95_5'], 3),
                               "rolloff": round(m['hist']['rolloff'], 3),
                               "f_white": round(m['hist']['f_white'], 4),
                               "dirR": round(m['dirR'], 3),
                               "mean_c": round(m['lc']['mean_c'], 3),
                               "cv_c": round(m['lc']['cv_c'], 3)}) if m else "SKIP")
    json.dump(res, open(DEST, "w"), indent=1)


if __name__ == "__main__":
    main()
