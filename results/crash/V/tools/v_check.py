#!/usr/bin/env python3
"""TRACK V acceptance checks A-D, per notes/PHASE3-spec.md 2.

A  no exception            status success, no execution_error
B  no black / no flat fill exact-(0,0,0) fraction ~= 0, and no LARGE CONTIGUOUS
                           single-RGB region -- measured as the biggest 4-connected
                           component of any one exact RGB value, not merely the
                           modal-colour count. (56,51,47) called out by name.
C  face survives detection face_yolov8m.pt max confidence in the 0.89 class, not
                           the 0.466 class. Replicates 622:424's own call:
                           Impact-Subpack subcore.py:319-325 does
                           `model(pil_rgb, conf=t, device=...)`, nothing else.
D  eyes stage ran          622:406 DetailerForEachDebug in the websocket
                           `executing` stream for that prompt_id.

Two frames are measured per arm where both exist:
  * TAP163 -- 621:163, the image handed to the failing detector. This is where
    the black face lives, and it is the ONLY frame a crashing arm produces.
  * n505   -- 622:418, the delivered frame.
"""
import os, json, glob, sys
import numpy as np
from PIL import Image
from scipy import ndimage
Image.MAX_IMAGE_PIXELS = None

ROOT = "/workspace/nsfw-fix/results/crash/V"
YOLO_MODEL = "/workspace/ComfyUI/models/ultralytics/bbox/face_yolov8m.pt"
BLACK_MAX = 0.001          # "exact-(0,0,0) fraction ~= 0"
# PHASE3-spec 2 asks for "no single exact RGB occupying a large contiguous area"
# without naming a number, so one has to be chosen. The two populations measured
# on this box are far apart: a healthy frame's biggest single-RGB blob is
# (255,255,255) at 2.07% -- a clipped window highlight, present identically in
# device-default clean arms -- and a failed frame's is (56,51,47) at 16.97%.
# 5% sits between them with a wide margin on both sides. The white highlight is
# excluded from the tighter NONWHITE test for the same reason, so a legitimately
# blown background cannot mask a coloured fill.
BIGCC_MAX = 0.05
BIGCC_NONWHITE_MAX = 0.02
CONF_PASS = 0.75           # the 0.89 class; the 0.466 class sits 0.43 below with nothing between
_yolo = None


def _y():
    global _yolo
    if _yolo is None:
        from ultralytics import YOLO
        _yolo = YOLO(YOLO_MODEL)
    return _yolo


def image_stats(path, want_yolo=True):
    im = Image.open(path).convert("RGB")
    a = np.asarray(im)
    f = a.astype(np.float32)
    packed = (a[:, :, 0].astype(np.uint32) << 16) | (a[:, :, 1].astype(np.uint32) << 8) | a[:, :, 2]
    vals, cnt = np.unique(packed, return_counts=True)
    order = np.argsort(cnt)[::-1]
    top = []
    big_cc_frac, big_cc_rgb = 0.0, None
    nw_cc_frac, nw_cc_rgb = 0.0, None
    for i in order[:6]:                       # only the six commonest can hold a big blob
        v = int(vals[i])
        rgb = [(v >> 16) & 255, (v >> 8) & 255, v & 255]
        top.append({"rgb": rgb, "frac": round(float(cnt[i]) / packed.size, 5)})
        lbl, n = ndimage.label(packed == v)
        if n:
            sizes = np.bincount(lbl.ravel())
            sizes[0] = 0
            fr = float(sizes.max()) / packed.size
            if fr > big_cc_frac:
                big_cc_frac, big_cc_rgb = fr, rgb
            if rgb != [255, 255, 255] and fr > nw_cc_frac:
                nw_cc_frac, nw_cc_rgb = fr, rgb
    black = float((a.sum(2) == 0).mean())
    lbl, n = ndimage.label(a.sum(2) == 0)
    black_cc = 0.0
    if n:
        s = np.bincount(lbl.ravel()); s[0] = 0
        black_cc = float(s.max()) / packed.size
    out = {"path": os.path.basename(path), "size": list(im.size),
           "exact_black_frac": round(black, 6),
           "largest_black_cc_frac": round(black_cc, 6),
           "largest_single_rgb_cc_frac": round(big_cc_frac, 5),
           "largest_single_rgb_cc_rgb": big_cc_rgb,
           "largest_nonwhite_rgb_cc_frac": round(nw_cc_frac, 5),
           "largest_nonwhite_rgb_cc_rgb": nw_cc_rgb,
           "top_colours": top,
           "flat_frac": round(float((np.abs(np.diff(f, axis=1)).max(2) < 0.5).mean()), 4),
           "luma_sd": round(float(f.mean(2).std()), 2)}
    if want_yolo:
        pred = _y()(im, conf=0.1, device="cpu", verbose=False)
        b = pred[0].boxes
        confs = sorted([float(c) for c in b.conf.cpu().numpy()], reverse=True) if len(b) else []
        out["yolo_face_max_conf"] = round(confs[0], 4) if confs else None
        out["yolo_face_n_at_0.1"] = len(confs)
        pred6 = _y()(im, conf=0.6, device="cpu", verbose=False)
        out["yolo_face_n_at_0.6"] = len(pred6[0].boxes)
    return out


def psnr(a, b):
    d = a.astype(np.float64) - b.astype(np.float64)
    mse = (d ** 2).mean()
    return 99.0 if mse == 0 else round(10 * np.log10(255 * 255 / mse), 2)


def judge(meta, tap, deliv):
    """The four acceptance checks. `tap` is 621:163, `deliv` is the 505 frame."""
    A = meta.get("status") == "success" and not meta.get("error")
    frame = deliv or tap
    if frame is None:
        B = C = None
    else:
        B = (frame["exact_black_frac"] <= BLACK_MAX
             and frame["largest_single_rgb_cc_frac"] <= BIGCC_MAX
             and frame["largest_nonwhite_rgb_cc_frac"] <= BIGCC_NONWHITE_MAX
             and frame["largest_single_rgb_cc_rgb"] != [56, 51, 47]
             and frame["largest_nonwhite_rgb_cc_rgb"] != [56, 51, 47])
        C = frame["yolo_face_max_conf"] is not None and frame["yolo_face_max_conf"] >= CONF_PASS
    D = "622:406" in (meta.get("executed_nodes") or [])
    return {"A": A, "B": B, "C": C, "D": D,
            "pass": bool(A and B and C and D),
            "judged_on": "505" if deliv else ("TAP163" if tap else None)}


def run(names=None, ref_arm=None):
    rows = {}
    ref = None
    dirs = sorted(glob.glob(os.path.join(ROOT, "arms", "*")))
    for d in dirs:
        name = os.path.basename(d)
        if names and name not in names:
            continue
        mp = os.path.join(d, "meta.json")
        if not os.path.exists(mp):
            continue
        meta = json.load(open(mp))
        tapf = glob.glob(os.path.join(d, "nTAP163__*.png"))
        delf = glob.glob(os.path.join(d, "n505__*.png"))
        tap = image_stats(tapf[0]) if tapf else None
        deliv = image_stats(delf[0]) if delf else None
        row = {"arm": name, "tokens": meta.get("tokens"), "prompt_id": meta.get("prompt_id"),
               "status": meta.get("status"), "cached": meta.get("cached"),
               "error_node": meta.get("error_node"), "exec_seconds": meta.get("exec_seconds"),
               "device_110": (meta.get("620:110") or {}).get("device"),
               "denoise_114": (meta.get("620:114") or {}).get("denoise"),
               "n_executed": len(meta.get("executed_nodes") or []),
               "tap163": tap, "delivered": deliv}
        row.update(judge(meta, tap, deliv))
        rows[name] = row
        if ref_arm and name == ref_arm and tapf:
            ref = np.asarray(Image.open(tapf[0]).convert("RGB"))
    if ref is not None:
        for name, row in rows.items():
            tapf = glob.glob(os.path.join(ROOT, "arms", name, "nTAP163__*.png"))
            if tapf:
                a = np.asarray(Image.open(tapf[0]).convert("RGB"))
                row["psnr_tap163_vs_ref"] = psnr(a, ref) if a.shape == ref.shape else None
    return rows


if __name__ == "__main__":
    ref = sys.argv[1] if len(sys.argv) > 1 else None
    rows = run(ref_arm=ref)
    json.dump(rows, open(os.path.join(ROOT, "out", "v_checks.json"), "w"), indent=1)
    hdr = f"{'arm':34s} {'tok':>4s} {'st':7s} {'cch':>3s} {'A':>1s}{'B':>1s}{'C':>1s}{'D':>1s} {'blk':>7s} {'cc':>7s} {'ccnw':>7s} {'conf':>6s} {'psnr':>6s}"
    print(hdr); print("-" * len(hdr))
    for n, r in sorted(rows.items()):
        f = r["delivered"] or r["tap163"] or {}
        def y(x): return {True: "Y", False: "N", None: "-"}[x]
        print(f"{n:34s} {str(r['tokens']):>4s} {str(r['status'])[:7]:7s} {str(r['cached']):>3s} "
              f"{y(r['A'])}{y(r['B'])}{y(r['C'])}{y(r['D'])} "
              f"{f.get('exact_black_frac', float('nan')):7.4f} "
              f"{f.get('largest_single_rgb_cc_frac', float('nan')):7.4f} "
              f"{f.get('largest_nonwhite_rgb_cc_frac', float('nan')):7.4f} "
              f"{str(f.get('yolo_face_max_conf')):>6s} {str(r.get('psnr_tap163_vs_ref')):>6s}"
              f"  {'PASS' if r['pass'] else 'FAIL'}  on={r['judged_on']}")
