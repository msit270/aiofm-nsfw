#!/usr/bin/env python3
"""Q3 analysis: per-arm objective deltas vs baseline, at the tap points.

Usage:
    q3_analyze.py identity <armA> <armB> <tapname>     # e.g. tap137
    q3_analyze.py deltas   <arm> [<baseline>]          # full table vs baseline
    q3_analyze.py texture  <arm> ...                   # per-arm texture stats

All boxes are detected per image with the graph's own face_yolov8m.pt (trap:
never reuse a fixed crop box). Diff metrics are computed over the BASELINE's
detected box after asserting the arm's detection centre moved < 5 % of the box
diagonal; both boxes are recorded.
Bands, as fractions of the detected face-box height (same convention as
results/run3/tools/analyze.py): eyes 0.18-0.55, mouth 0.55-1.00.
Texture proxy for airbrushing: variance of the 3x3 Laplacian over the face
crop's luma, plus the same over a 400px flat-skin patch found by
tools/contact_sheet.py::find_skin_box on the baseline and reused at the SAME
coordinates for every arm (texture comparability needs identical regions).
"""
import glob, json, os, sys
import numpy as np
from PIL import Image

Q3 = "/workspace/nsfw-fix/results/run4/quality/Q3"
YOLO_W = "/workspace/ComfyUI/models/ultralytics/bbox/face_yolov8m.pt"
sys.path.insert(0, "/workspace/nsfw-fix/tools")

_model = None


def png(arm, tag):
    """tag: tap137 | tap114 | tap111 | tap163 | final"""
    pat = {"final": f"{Q3}/{arm}/n505__*.png"}.get(tag, f"{Q3}/{arm}/nTAP*__{tag}_*.png")
    c = sorted(glob.glob(pat))
    assert c, f"no {tag} png for {arm}"
    return c[0]


def facebox(path):
    global _model
    if _model is None:
        os.environ.setdefault("YOLO_VERBOSE", "False")
        from ultralytics import YOLO
        _model = YOLO(YOLO_W)
    r = _model(path, verbose=False)[0]
    assert len(r.boxes), f"no face in {path}"
    i = int(r.boxes.conf.argmax())
    x1, y1, x2, y2 = [int(v) for v in r.boxes.xyxy[i].tolist()]
    return (x1, y1, x2, y2), float(r.boxes.conf[i])


def arr(path):
    return np.asarray(Image.open(path).convert("RGB")).astype(np.int64)


def region_stats(da, name):
    d = np.abs(da)
    out = {
        f"{name}_mean_abs": round(float(d.mean()), 3),
        f"{name}_max_abs": int(d.max()),
        f"{name}_pct_gt0": round(float((d.sum(axis=2) > 0).mean() * 100), 2),
        f"{name}_pct_gt8": round(float((d.max(axis=2) > 8).mean() * 100), 2),
    }
    mse = float((da.astype(np.float64) ** 2).mean())
    out[f"{name}_psnr_db"] = round(10 * np.log10(255 * 255 / mse), 2) if mse > 0 else None
    return out


def lap_var(a_uint8_rgb):
    import cv2
    g = cv2.cvtColor(a_uint8_rgb, cv2.COLOR_RGB2GRAY)
    return float(cv2.Laplacian(g, cv2.CV_64F).var())


def pigment_stats(rgb_u8, radius):
    """R1-denoise.md's rule, reimplemented: CIELAB (D65), local background =
    median filter of radius ~2 % of face width. pigment = locally darker
    (L* < bg-2.0) AND locally more yellow (b* > bg+0.6) — flat brown marks.
    bright-blob = locally brighter (L* > bg+2.0) — the raised-bump defect.
    Returns percentages of the given region."""
    from skimage.color import rgb2lab
    from scipy.ndimage import median_filter
    lab = rgb2lab(rgb_u8)
    L, b = lab[..., 0], lab[..., 2]
    k = max(3, int(radius) | 1)
    Lbg = median_filter(L, size=k)
    bbg = median_filter(b, size=k)
    pig = ((L < Lbg - 2.0) & (b > bbg + 0.6)).mean() * 100
    blob = (L > Lbg + 2.0).mean() * 100
    return round(float(pig), 3), round(float(blob), 3)


def identity(a, b, tag):
    ia, ib = arr(png(a, tag)), arr(png(b, tag))
    assert ia.shape == ib.shape, (ia.shape, ib.shape)
    d = np.abs(ia - ib)
    r = {"a": a, "b": b, "tag": tag, "max_abs": int(d.max()),
         "pct_gt0": round(float((d.sum(axis=2) > 0).mean() * 100), 4)}
    print(json.dumps(r))
    return r


def skin_box_for_baseline(base_final, fb_xywh):
    """Flat-skin patch INSIDE the detected face box. 400px (contact_sheet's
    default) does not fit a ~330px face and falls back to a whole-frame search
    that lands on the skin-toned balcony floor — measured, not guessed. A
    third of the face width keeps it on the cheek."""
    from contact_sheet import find_skin_box
    im = Image.open(base_final).convert("RGB")
    size = max(60, min(120, fb_xywh[2] // 3))
    box, stats = find_skin_box(im, fb_xywh, size, "face")
    return box, stats


def deltas(armname, basename="A0_baseline", tags=("tap114", "tap163", "final")):
    out = {"arm": armname, "baseline": basename, "tags": {}}
    for tag in tags:
        pa, pb = png(armname, tag), png(basename, tag)
        (bx1, by1, bx2, by2), bconf = facebox(pb)
        (ax1, ay1, ax2, ay2), aconf = facebox(pa)
        diag = float(np.hypot(bx2 - bx1, by2 - by1))
        moved = float(np.hypot((ax1 + ax2 - bx1 - bx2) / 2, (ay1 + ay2 - by1 - by2) / 2))
        t = {"base_facebox_xyxy": [bx1, by1, bx2, by2], "base_conf": round(bconf, 3),
             "arm_facebox_xyxy": [ax1, ay1, ax2, ay2], "arm_conf": round(aconf, 3),
             "face_centre_moved_px": round(moved, 1)}
        assert moved < 0.05 * diag, f"face moved {moved:.0f}px on {armname}/{tag} — boxes not comparable"
        ia, ib = arr(pa), arr(pb)
        assert ia.shape == ib.shape
        da = ia - ib
        t.update(region_stats(da, "frame"))
        f = da[by1:by2, bx1:bx2]
        t.update(region_stats(f, "face"))
        h = by2 - by1
        ey1, ey2 = by1 + int(0.18 * h), by1 + int(0.55 * h)
        my1, my2 = by1 + int(0.55 * h), by2
        t.update(region_stats(da[ey1:ey2, bx1:bx2], "eyeband"))
        t.update(region_stats(da[my1:my2, bx1:bx2], "mouthband"))
        # texture (absolute per arm, same regions)
        au8 = ia.astype(np.uint8)
        bu8 = ib.astype(np.uint8)
        t["lapvar_face_arm"] = round(lap_var(au8[by1:by2, bx1:bx2]), 1)
        t["lapvar_face_base"] = round(lap_var(bu8[by1:by2, bx1:bx2]), 1)
        sb, sstats = skin_box_for_baseline(pb, (bx1, by1, bx2 - bx1, by2 - by1))
        sx, sy, sw, sh = sb
        t["skin_box_xywh"] = list(sb)
        t["skin_stats"] = sstats
        t["lapvar_skin_arm"] = round(lap_var(au8[sy:sy + sh, sx:sx + sw]), 1)
        t["lapvar_skin_base"] = round(lap_var(bu8[sy:sy + sh, sx:sx + sw]), 1)
        # nose/cheek band for the R1 pigment rule: central band of the face box
        fw = bx2 - bx1
        nx1, nx2 = bx1 + int(0.15 * fw), bx1 + int(0.85 * fw)
        ny1, ny2 = by1 + int(0.35 * h), by1 + int(0.75 * h)
        rad = max(3, int(round(0.02 * fw)))
        t["pigment_rect_xyxy"] = [nx1, ny1, nx2, ny2]
        t["pigment_radius_px"] = rad
        pa_, ba_ = pigment_stats(au8[ny1:ny2, nx1:nx2], rad)
        pb_, bb_ = pigment_stats(bu8[ny1:ny2, nx1:nx2], rad)
        t["pigment_pct_arm"], t["brightblob_pct_arm"] = pa_, ba_
        t["pigment_pct_base"], t["brightblob_pct_base"] = pb_, bb_
        out["tags"][tag] = t
    path = f"{Q3}/{armname}/deltas_vs_{basename}.json"
    json.dump(out, open(path, "w"), indent=1)
    print(json.dumps(out, indent=1))
    return out


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "identity":
        identity(sys.argv[2], sys.argv[3], sys.argv[4])
    elif cmd == "deltas":
        deltas(sys.argv[2], *(sys.argv[3:4] or ["A0_baseline"]))
