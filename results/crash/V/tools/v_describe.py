#!/usr/bin/env python3
"""What does the fix actually change on a render where nothing was wrong?

Not a rating. This decomposes the measured difference between the device=default
and device=cpu arms of the SAME clean 16-token prompt so the change can be
described in words the owner can act on: where in the frame it sits, whether it
is tone or colour, and whether fine detail goes up or down.

Nothing here judges quality. It reports where the pixels moved and in which
direction, and the sheet is what the owner looks at.
"""
import sys, os, glob, json
import numpy as np
from PIL import Image
from scipy import ndimage
Image.MAX_IMAGE_PIXELS = None

ROOT = "/workspace/nsfw-fix/results/crash/V/arms"
YOLO_MODEL = "/workspace/ComfyUI/models/ultralytics/bbox/face_yolov8m.pt"


def frame(arm, kind):
    f = sorted(glob.glob(os.path.join(ROOT, arm, f"{kind}__*.png")))
    return np.asarray(Image.open(f[0]).convert("RGB")).astype(np.float64) if f else None


def face_box(arm, kind):
    f = sorted(glob.glob(os.path.join(ROOT, arm, f"{kind}__*.png")))
    from ultralytics import YOLO
    im = Image.open(f[0]).convert("RGB")
    p = YOLO(YOLO_MODEL)(im, conf=0.3, device="cpu", verbose=False)[0].boxes
    if not len(p):
        return None
    i = int(p.conf.cpu().numpy().argmax())
    return [int(v) for v in p.xyxy.cpu().numpy()[i]]


def luma(a):
    return 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]


def hf_energy(g):
    """Mean |Laplacian| -- higher means more fine detail / acutance."""
    return float(np.abs(ndimage.laplace(g)).mean())


def report(a_name, b_name, kind="n505", label=""):
    A, B = frame(a_name, kind), frame(b_name, kind)
    if A is None or B is None or A.shape != B.shape:
        return {"error": f"missing or mismatched frames for {a_name}/{b_name} @ {kind}"}
    d = B - A
    ad = np.abs(d)
    H, W, _ = A.shape
    box = face_box(a_name, kind)
    mask = np.zeros((H, W), bool)
    if box:
        x1, y1, x2, y2 = box
        mask[y1:y2, x1:x2] = True
    out = {"pair": f"{a_name} (A, default)  vs  {b_name} (B, cpu)", "stage": kind,
           "label": label, "face_box": box, "shape": [H, W]}

    def sub(m, tag):
        if m.sum() == 0:
            return
        px = ad.max(2)[m]
        out[tag] = {
            "area_frac_of_frame": round(float(m.mean()), 4),
            "pixels_differing": round(float((px > 0).mean()), 5),
            "pixels_differing_gt1": round(float((px > 1).mean()), 5),
            "pixels_differing_gt4": round(float((px > 4).mean()), 5),
            "mean_abs_diff": round(float(ad[m].mean()), 4),
            "p99_abs_diff": round(float(np.percentile(px, 99)), 2),
            "max_abs_diff": int(px.max()),
        }
    sub(mask, "inside_face_box")
    sub(~mask, "outside_face_box")

    # tone vs colour: signed luma shift, and chroma change with luma removed
    lA, lB = luma(A), luma(B)
    dl = lB - lA
    chromaA = A - lA[..., None]
    chromaB = B - lB[..., None]
    dc = np.abs(chromaB - chromaA).max(2)
    out["tone_vs_colour"] = {
        "mean_signed_luma_shift": round(float(dl.mean()), 4),
        "mean_abs_luma_shift": round(float(np.abs(dl).mean()), 4),
        "mean_abs_chroma_shift": round(float(dc.mean()), 4),
        "per_channel_mean_signed": [round(float(d[..., i].mean()), 4) for i in range(3)],
    }
    if box:
        x1, y1, x2, y2 = box
        fA, fB = lA[y1:y2, x1:x2], lB[y1:y2, x1:x2]
        out["fine_detail_in_face_box"] = {
            "hf_energy_default": round(hf_energy(fA), 5),
            "hf_energy_cpu": round(hf_energy(fB), 5),
            "hf_ratio_cpu_over_default": round(hf_energy(fB) / hf_energy(fA), 5),
            "local_sd_default": round(float(ndimage.generic_filter(
                fA[::4, ::4], np.std, size=5).mean()), 4),
            "local_sd_cpu": round(float(ndimage.generic_filter(
                fB[::4, ::4], np.std, size=5).mean()), 4),
        }
    # where the biggest differences concentrate: 8x8 grid of mean |diff|
    gh, gw = H // 8, W // 8
    grid = [[round(float(ad[r * gh:(r + 1) * gh, c * gw:(c + 1) * gw].mean()), 3)
             for c in range(8)] for r in range(8)]
    out["mean_abs_diff_grid_8x8"] = grid
    return out


if __name__ == "__main__":
    res = []
    res.append(report("V_CLEAN_mid_16a", "V_CLEAN_head_16a", "n505",
                      "THE COST PAIR: clean 16-token prompt, delivered frame"))
    res.append(report("V_CLEAN_mid_16a", "V_CLEAN_head_16a", "nTAP163",
                      "same pair at 621:163, the stage the sheet shows"))
    res.append(report("V_CLEAN_mid_16b", "V_CLEAN_head_16b", "n505",
                      "the repeat of the cost pair"))
    json.dump(res, open("/workspace/nsfw-fix/results/crash/V/out/v_describe.json", "w"), indent=1)
    for r in res:
        print("=" * 78)
        print(r.get("label"), "|", r.get("stage"))
        for k, v in r.items():
            if k in ("mean_abs_diff_grid_8x8", "label", "stage", "pair"):
                continue
            print(f"  {k}: {v}")
        print("  grid of mean|diff|, 8x8 over the frame:")
        for row in r["mean_abs_diff_grid_8x8"]:
            print("    " + " ".join(f"{v:6.3f}" for v in row))
