#!/usr/bin/env python3
"""Q4 analysis. CPU-only by construction (YOLO device='cpu'): no GPU touch, so
it runs outside the flock.

  q4_analyze.py metrics    # health + per-arm YOLO + pixel deltas vs baseline
  q4_analyze.py logx       # extract USDU tiling + Detailer lines from server logs

Face-crop rule: the box is DETECTED on the baseline image with the graph's own
detector (bbox/face_yolov8m.pt) and applied to every arm; each arm's own
detection is recorded, and any centre moving >25% of the box size is flagged.
Never the WS4 hardcoded square (STATE.md §8). Deltas are measured on the
delivered 505 frame -- the slot actually wired downstream (STATE.md trap #10);
the TAP163 (post-mouth, pre-eyes) pair is measured separately for attribution.
"""
import json, os, re, sys, glob
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
Q4 = os.path.dirname(HERE)
BASE = "baseline_ships"
DETECTOR = "/workspace/ComfyUI/models/ultralytics/bbox/face_yolov8m.pt"
ORDER = ["baseline_ships", "blend87_050", "usdu617_dn015", "usdu617_dn035",
         "usdu98_tile1024", "base592_steps60", "face607_dn030"]


def arm_png(arm, which="505"):
    pre = "n505__" if which == "505" else "nTAP163__"
    c = sorted(glob.glob(os.path.join(Q4, arm, pre + "*.png")))
    return c[0] if c else None


def load(p):
    return np.asarray(Image.open(p).convert("RGB")).astype(np.int64)


def facebox(path, model):
    res = model(path, device="cpu", verbose=False)[0]
    if not len(res.boxes):
        return None, None
    bi = int(res.boxes.conf.argmax())
    x1, y1, x2, y2 = [int(v) for v in res.boxes.xyxy[bi].tolist()]
    return (x1, y1, x2, y2), float(res.boxes.conf[bi])


def health(img, box):
    """R4's flat-face detector: fraction of face-box pixels whose 9x9 local
    luma sigma is below one 8-bit level. Poisoned renders read ~0.999."""
    a = img.astype(np.float64)
    if box:
        x1, y1, x2, y2 = box
        a = a[y1:y2, x1:x2]
    luma = 0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]
    k = 9
    c = np.pad(luma, ((1, 0), (1, 0))).cumsum(0).cumsum(1)
    c2 = np.pad(luma ** 2, ((1, 0), (1, 0))).cumsum(0).cumsum(1)

    def box_sum(cc):
        return (cc[k:, k:] - cc[:-k, k:] - cc[k:, :-k] + cc[:-k, :-k])
    n = k * k
    mean = box_sum(c) / n
    var = np.maximum(box_sum(c2) / n - mean ** 2, 0)
    sd = np.sqrt(var)
    med = [int(np.median(a[..., i])) for i in range(3)]
    return {"flat_frac": round(float((sd < 1.0).mean()), 4),
            "median_rgb": med, "luma_sd": round(float(luma.std()), 2)}


def pair_stats(a, b, box=None):
    if box:
        x1, y1, x2, y2 = box
        a, b = a[y1:y2, x1:x2], b[y1:y2, x1:x2]
    d = np.abs(a - b)
    mse = float(((a - b) ** 2).mean())
    psnr = float("inf") if mse == 0 else 20 * np.log10(255.0 / np.sqrt(mse))
    try:
        from skimage.metrics import structural_similarity as ssim_fn
        ssim = float(ssim_fn(a.astype(np.uint8), b.astype(np.uint8),
                             channel_axis=-1, data_range=255))
    except Exception:
        ssim = None
    dm = d.max(axis=2)
    return {"psnr_db": round(psnr, 2) if psnr != float("inf") else "inf",
            "ssim": round(ssim, 4) if ssim is not None else None,
            "mean_abs": round(float(d.mean()), 3),
            "max_abs": int(d.max()),
            "pct_gt_1": round(float((dm > 1).mean() * 100), 2),
            "pct_gt_8": round(float((dm > 8).mean() * 100), 2)}


def _blur(a, r):
    from PIL import ImageFilter
    return np.asarray(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
                      .filter(ImageFilter.GaussianBlur(r)), dtype=np.float64)


def _luma(a):
    a = a.astype(np.float64)
    return 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]


def skin_mask(a):
    """R4's mask, verbatim (scratchpad r4_analyse.py skin_mask): the same
    instrument that produced the published blobs/pores figures, so Q4's numbers
    sit on the same scale as R4's."""
    from scipy import ndimage
    r, g, b = a[..., 0].astype(float), a[..., 1].astype(float), a[..., 2].astype(float)
    mx, mn = a.max(2).astype(float), a.min(2).astype(float)
    s = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1), 0)
    m = (mx > 90) & (mx < 250) & (r > g) & (g > b) & (s > 0.10) & (s < 0.55)
    m = ndimage.binary_opening(m, np.ones((9, 9)))
    return ndimage.binary_erosion(m, np.ones((15, 15)))


def texture(img, mask):
    """R4's texture instrument, verbatim: bright blobs (the defect the owner
    dislikes) and dark pores (the texture he asked for) per Mpx, plus two
    band RMS figures, over a mask FIXED from the baseline so the denominator
    does not move with the arm. Descriptive only -- never a quality verdict."""
    from scipy import ndimage
    y = _luma(img)
    area = mask.sum() / 1e6
    if area == 0:
        return None
    dog_blob = _blur(y, 3) - _blur(y, 10)
    dog_fine = _blur(y, 0.8) - _blur(y, 2.5)

    def count(field, sign, thresh, lo, hi):
        lab, n = ndimage.label(((field * sign) > thresh) & mask)
        if n == 0:
            return 0
        sz = np.bincount(lab.ravel())[1:]
        return int(((sz >= lo) & (sz <= hi)).sum())

    return {"skin_mpx": round(float(area), 4),
            "bright_blobs_per_mpx": round(count(dog_blob, +1, 3.0, 20, 400) / area, 1),
            "dark_pores_per_mpx": round(count(dog_fine, -1, 2.0, 2, 30) / area, 1),
            "fine_rms": round(float(np.sqrt(np.mean((_blur(y, 1) - _blur(y, 3))[mask] ** 2))), 3),
            "blob_rms": round(float(np.sqrt(np.mean((_blur(y, 8) - _blur(y, 24))[mask] ** 2))), 3)}


def metrics():
    from ultralytics import YOLO
    model = YOLO(DETECTOR)
    bp = arm_png(BASE)
    assert bp, "no baseline render yet"
    bimg = load(bp)
    bbox, bconf = facebox(bp, model)
    print(f"[base] {os.path.basename(bp)}  face {bbox} conf={bconf:.3f}")
    btap = arm_png(BASE, "tap")
    btimg = load(btap) if btap else None
    # texture masks fixed from the baseline: one over the detected face, one
    # over all skin in the frame (this composition is full-body, so the face is
    # only 332x438 of 2688x3456 and the skin filter acts everywhere).
    bu8 = bimg.astype(np.uint8)
    fx1, fy1, fx2, fy2 = bbox
    mask_face = skin_mask(bu8[fy1:fy2, fx1:fx2])
    mask_body = skin_mask(bu8)
    print(f"[base] fixed skin masks: face {mask_face.sum()/1e6:.4f} Mpx, "
          f"frame {mask_body.sum()/1e6:.4f} Mpx")

    out = {"baseline_face_box_xyxy": bbox, "baseline_face_conf": round(bconf, 4),
           "note": "face box detected per image (CPU YOLO); crop metrics use the "
                   "baseline box on both sides; arm det recorded; measured on the "
                   "delivered 505 frame + TAP163 separately", "arms": {}}
    for arm in ORDER:
        p = arm_png(arm)
        if not p:
            print(f"[{arm}] no render yet -- skipped")
            continue
        img = load(p)
        dbox, dconf = facebox(p, model)
        rec = {"png": os.path.basename(p),
               "det_xyxy": dbox, "det_conf": round(dconf, 4) if dconf else None,
               "health": health(img, dbox or bbox)}
        if dbox and bbox:
            c0 = ((bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2)
            c1 = ((dbox[0] + dbox[2]) / 2, (dbox[1] + dbox[3]) / 2)
            move = float(np.hypot(c1[0] - c0[0], c1[1] - c0[1]))
            rec["face_centre_moved_px"] = round(move, 1)
            rec["face_moved_flag"] = move > 0.25 * max(bbox[2] - bbox[0], bbox[3] - bbox[1])
        rec["texture_face"] = texture(img[fy1:fy2, fx1:fx2], mask_face)
        rec["texture_frame_skin"] = texture(img, mask_body)
        if arm != BASE:
            rec["vs_baseline_full"] = pair_stats(img, bimg)
            rec["vs_baseline_face"] = pair_stats(img, bimg, bbox)
            tp = arm_png(arm, "tap")
            if tp and btimg is not None:
                rec["vs_baseline_tap163_full"] = pair_stats(load(tp), btimg)
        out["arms"][arm] = rec
        # fold key numbers into the arm's meta.json so the sheet can show them
        mp = os.path.join(Q4, arm, "meta.json")
        if os.path.exists(mp):
            m = json.load(open(mp))
            m["health"] = rec["health"]
            m["det"] = {"xyxy": dbox, "conf": rec["det_conf"]}
            m["texture_frame_skin"] = rec["texture_frame_skin"]
            if "vs_baseline_face" in rec:
                m["vs_baseline_face"] = rec["vs_baseline_face"]
                m["vs_baseline_full"] = rec["vs_baseline_full"]
            json.dump(m, open(mp, "w"), indent=1)
        print(f"[{arm}] health={rec['health']}  "
              + (f"face {rec['vs_baseline_face']}" if arm != BASE else "(baseline)"))
    json.dump(out, open(os.path.join(Q4, "metrics.json"), "w"), indent=1)
    print(f"[done] {os.path.join(Q4, 'metrics.json')}")


def vram_by_node(arm):
    """Attribute each VRAM sample to the node window it fell in (ws `executing`
    events carry local receipt timestamps). Returns {node: max_mine_mib}."""
    d = os.path.join(Q4, arm)
    try:
        ws = json.load(open(os.path.join(d, "ws.json")))
        samples = json.load(open(os.path.join(d, "vram_samples.json")))
    except FileNotFoundError:
        return None
    events = [(t, n) for t, n in ws.get("events", []) if n is not None]
    if not events:
        return None
    out = {}
    for smp in samples:
        if smp["mine_mib"] is None:
            continue
        node = None
        for t, n in events:
            if t <= smp["t"]:
                node = n
            else:
                break
        if node is None:
            node = "(pre-exec/model-load)"
        out[node] = max(out.get(node, 0), smp["mine_mib"])
    return out


def vram():
    for arm in ORDER:
        bv = vram_by_node(arm)
        if bv is None:
            continue
        mp = os.path.join(Q4, arm, "meta.json")
        m = json.load(open(mp))
        m["vram_max_by_node"] = dict(sorted(bv.items(), key=lambda kv: -kv[1]))
        json.dump(m, open(mp, "w"), indent=1)
        top = sorted(bv.items(), key=lambda kv: -kv[1])[:6]
        print(f"[{arm}] top VRAM windows: " + ", ".join(f"{n}={v}MiB" for n, v in top))


USDU_RE = re.compile(r"(Canva size|Image size|Scale factor|Tile size|Tiles amount|Grid|Redraw enabled|Seams fix mode): .*")
DET_RE = re.compile(r"Detailer: segment upscale for .*")


def logx():
    for arm in ORDER:
        lp = os.path.join(Q4, arm, "server.log")
        if not os.path.exists(lp):
            continue
        usdu, det = [], []
        for line in open(lp, errors="replace"):
            m = USDU_RE.search(line)
            if m:
                usdu.append(line.strip())
            m = DET_RE.search(line)
            if m:
                det.append(line.strip())
        mp = os.path.join(Q4, arm, "meta.json")
        m = json.load(open(mp))
        m["log_usdu"] = usdu
        m["log_detailer"] = det
        json.dump(m, open(mp, "w"), indent=1)
        print(f"[{arm}] usdu_lines={len(usdu)} detailer_lines={len(det)}")
        for l in usdu:
            print("   ", l)


if __name__ == "__main__":
    {"metrics": metrics, "logx": logx, "vram": vram}[sys.argv[1]]()
