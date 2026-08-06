#!/usr/bin/env python3
"""
contact_sheet.py -- build 1:1 native-resolution face contact sheets for A/B arm review.

WHY THIS EXISTS
---------------
The owner judges face work by looking at pixels, not at PSNR/SSIM. So the
deliverable is a tiled sheet of face crops, every tile at *native* resolution,
each labelled with its arm name and the parameter that changed, with the
baseline pinned top-left of every sheet as the reference.

THE ONE INVARIANT
-----------------
NO DOWNSCALING, EVER. A 700px region of a source render occupies exactly 700px
on the sheet. This is enforced, not assumed: --verify (on by default) re-opens
the written PNG and asserts every tile is byte-identical to the source crop.
The "sheet must be under 4000px wide" constraint is resolved by choosing the
crop size and the column count -- never by resampling.

TWO SHEETS PER RUN
------------------
  face  -- the detected face box (+ padding), same region for every arm
  skin  -- a flat, featureless skin patch (default: cheek), same region for
           every arm, so texture can be judged apart from features

USAGE
-----
  # normal: build from whatever arms P2-RENDER has landed so far
  python3 tools/contact_sheet.py --arms-dir results/face/arms --out-dir results/face

  # proof/tooling run from explicit images
  python3 tools/contact_sheet.py \
      --arm 'A_baseline|baseline|results/ws4/A_baseline/HasMetadata_00001_.png' \
      --arm 'B_no_vae_roundtrip|VAE round-trip removed|results/ws4/B.../x.png' \
      --out-dir results/face --prefix proof --note 'TOOLING TEST'

Re-runnable: safe to run again as each new arm lands.
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# Pillow >= 10 removed Image.ANTIALIAS etc.; we never resample anyway.
Image.MAX_IMAGE_PIXELS = None

# --------------------------------------------------------------------------
# Look
# --------------------------------------------------------------------------
BG = (26, 26, 26)             # neutral dark grey -- standard for image review
HEADER_BG = (16, 16, 16)
FG = (238, 238, 238)
DIM = (150, 150, 150)
ACCENT = (120, 200, 255)      # baseline highlight
WARN_BG = (190, 40, 30)       # loud red chip for any crop that is not trustworthy
WARN_FG = (255, 245, 240)
OK_DIM = (130, 160, 130)
TILE_BORDER = (70, 70, 70)
BASELINE_BORDER = ACCENT

MARGIN = 20
GUTTER = 18                   # space between tiles
LABEL_PAD = 6

FONT_CANDIDATES_BOLD = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
]
FONT_CANDIDATES_REG = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
]
FONT_CANDIDATES_MONO = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
]

DEFAULT_DETECTOR = "/workspace/ComfyUI/models/ultralytics/bbox/face_yolov8m.pt"

# Last-resort face box, used only when detection is unavailable AND no arm
# detects. Provenance: results/ws4/metrics_*.json "face_box_xywh", the box WS4
# measured its face-crop PSNR/SSIM over on this exact composition.
FALLBACK_FACE_XYWH = (1028, 498, 732, 732)


def _load_font(cands, size):
    for p in cands:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return None


class Fonts:
    """Resolved once. If no TrueType font exists we say so loudly rather than
    silently falling back to the 11px bitmap font, which would be unreadable
    next to a 700px tile.

    Tile label sizes scale with tile width so a 400px skin tile is as legible
    as a 774px face tile, with floors so they never become unreadable."""

    REF_TILE = 774.0

    def __init__(self):
        self.ok = True
        self.h1 = _load_font(FONT_CANDIDATES_BOLD, 46)
        self.h2 = _load_font(FONT_CANDIDATES_REG, 26)
        if any(f is None for f in (self.h1, self.h2)):
            self.ok = False
        d = ImageFont.load_default()
        self.h1 = self.h1 or d
        self.h2 = self.h2 or d
        self._cache = {}

    def tile(self, tile_w):
        """-> (name_font, param_font, small_font, line_heights)"""
        k = int(tile_w)
        if k in self._cache:
            return self._cache[k]
        s = min(1.0, max(0.62, tile_w / self.REF_TILE))
        sizes = (max(21, int(34 * s)), max(17, int(27 * s)), max(15, int(23 * s)))
        f = (_load_font(FONT_CANDIDATES_BOLD, sizes[0]),
             _load_font(FONT_CANDIDATES_REG, sizes[1]),
             _load_font(FONT_CANDIDATES_REG, sizes[2]))
        if any(x is None for x in f):
            self.ok = False
            d = ImageFont.load_default()
            f = tuple(x or d for x in f)
        lh = tuple(int(sz * 1.30) for sz in sizes)
        self._cache[k] = (f[0], f[1], f[2], lh)
        return self._cache[k]


# --------------------------------------------------------------------------
# Arm discovery
# --------------------------------------------------------------------------
@dataclass
class Arm:
    name: str
    param: str
    path: str
    is_baseline: bool = False
    extra: str = ""                   # optional context line, e.g. exec seconds
    warnings: list = field(default_factory=list)
    # filled in later
    det_xyxy: Optional[tuple] = None
    det_conf: Optional[float] = None
    det_status: str = "pending"      # detected | no-face | multi-face | detector-off | detector-error
    face_box: Optional[tuple] = None  # (x,y,w,h) actually cropped
    crop_mode: str = "pending"        # common | own | fallback
    size: Optional[tuple] = None


# meta.json keys are read defensively: P2-RENDER owns that file's schema and I
# do not control it. Anything unrecognised falls back to the directory name and
# the tile says so.
_NAME_KEYS = ("arm", "arm_name", "name", "label", "id")
_PARAM_KEYS = ("param", "parameter", "parameter_changed", "param_changed",
               "changed", "change", "delta", "description", "desc", "note", "what")
_BASE_KEYS = ("baseline", "is_baseline")
_IMG_KEYS = ("image", "img", "file", "png", "filename", "output")


def _first(d, keys):
    for k in keys:
        if isinstance(d, dict) and k in d and d[k] not in (None, ""):
            return d[k]
    return None


# Matches an optional ordering prefix (a_, A0_, 00-, 1., ...) followed by
# baseline/base/control/reference. P2-RENDER's baseline is 'A0_baseline'
# (results/face/ARMS.md), which a naive prefix list misses -- and misidentifying
# the baseline puts the wrong tile top-left on every sheet.
_BASE_RE = re.compile(r"^(?:[a-z]?\d*[._\-]+)?(baseline|base|control|reference|ref)"
                      r"(?:[._\-].*)?$")


def _looks_baseline(name: str) -> bool:
    return bool(_BASE_RE.match(name.strip().lower()))


def discover_arms(arms_dir: str) -> list:
    arms = []
    if not os.path.isdir(arms_dir):
        return arms
    for entry in sorted(os.listdir(arms_dir)):
        d = os.path.join(arms_dir, entry)
        if not os.path.isdir(d):
            continue
        warns = []
        meta = {}
        mp = os.path.join(d, "meta.json")
        if os.path.exists(mp):
            try:
                with open(mp) as fh:
                    meta = json.load(fh)
                if not isinstance(meta, dict):
                    warns.append("meta.json not an object")
                    meta = {}
            except Exception as e:
                warns.append(f"meta.json unreadable: {type(e).__name__}")
                meta = {}
        else:
            warns.append("meta.json MISSING")

        pngs = sorted(p for p in os.listdir(d) if p.lower().endswith(".png"))
        if not pngs:
            # An arm dir with no render yet (P2-RENDER writes api_graph.json
            # first). Skipping is right, but say so -- a silently absent arm is
            # indistinguishable from an arm that was never briefed.
            print(f"  [skip] {entry}: no PNG yet ({', '.join(sorted(os.listdir(d))) or 'empty'})")
            continue
        named = _first(meta, _IMG_KEYS)
        if named and os.path.basename(str(named)) in pngs:
            png = os.path.basename(str(named))
        elif len(pngs) == 1:
            png = pngs[0]
        else:
            png = max(pngs, key=lambda p: os.path.getmtime(os.path.join(d, p)))
            warns.append(f"{len(pngs)} PNGs, used newest: {png}")

        name = str(_first(meta, _NAME_KEYS) or entry)
        param = _first(meta, _PARAM_KEYS)
        if param is None:
            param = "(parameter not recorded in meta.json)"
            if "meta.json MISSING" not in warns:
                warns.append("no parameter field in meta.json")
        base = _first(meta, _BASE_KEYS)
        is_base = bool(base) if base is not None else _looks_baseline(entry)

        # Optional context P2-RENDER records. Shown, never interpreted: it warns
        # in results/face/ARMS.md that arms with differing cache state must not
        # be compared on time, so the cache state is displayed alongside.
        bits = []
        if meta.get("exec_seconds") is not None:
            bits.append(f"{meta['exec_seconds']} s")
        cn = meta.get("cached_nodes")
        if cn is not None:
            bits.append(f"{len(cn) if isinstance(cn, (list, tuple)) else cn} cached nodes")
        if meta.get("prompt_id"):
            bits.append(f"prompt {str(meta['prompt_id'])[:8]}")

        arms.append(Arm(name=name, param=str(param), path=os.path.join(d, png),
                        is_baseline=is_base, extra="  |  ".join(bits), warnings=warns))
    return arms


def parse_explicit(specs: list) -> list:
    arms = []
    for s in specs:
        parts = s.split("|")
        if len(parts) != 3:
            sys.exit(f"--arm needs 'name|param|path', got: {s!r}")
        name, param, path = (p.strip() for p in parts)
        if not os.path.exists(path):
            sys.exit(f"--arm path does not exist: {path}")
        arms.append(Arm(name=name, param=param, path=path,
                        is_baseline=_looks_baseline(name)))
    return arms


# --------------------------------------------------------------------------
# Face detection
# --------------------------------------------------------------------------
class Detector:
    """Wraps the same checkpoint the graph's FaceDetailer uses
    (bbox/face_yolov8m.pt). Never fatal: if it cannot load, every arm is marked
    detector-off and the sheet says so in the header."""

    def __init__(self, model_path: str, enabled: bool = True):
        self.model = None
        self.err = None
        self.path = model_path
        if not enabled:
            self.err = "disabled by --no-detect"
            return
        if not os.path.exists(model_path):
            self.err = f"checkpoint not found: {model_path}"
            return
        try:
            os.environ.setdefault("YOLO_VERBOSE", "False")
            from ultralytics import YOLO
            self.model = YOLO(model_path)
        except Exception as e:
            self.err = f"{type(e).__name__}: {e}"

    def detect(self, im: Image.Image):
        """-> (xyxy|None, conf|None, status, extra_warning|None)"""
        if self.model is None:
            return None, None, "detector-off", None
        try:
            res = self.model(im, verbose=False)
        except Exception as e:
            return None, None, "detector-error", f"{type(e).__name__}: {e}"
        boxes = []
        for r in res:
            b = r.boxes
            if b is None:
                continue
            for i in range(len(b)):
                boxes.append((float(b.conf[i]), tuple(float(v) for v in b.xyxy[i].tolist())))
        if not boxes:
            return None, None, "no-face", None
        boxes.sort(reverse=True)
        conf, xyxy = boxes[0]
        extra = None
        strong = [b for b in boxes if b[0] >= 0.50]
        if len(strong) > 1:
            extra = f"{len(strong)} faces >=0.50 conf, used highest ({conf:.2f})"
            return xyxy, conf, "multi-face", extra
        return xyxy, conf, "detected", None


# --------------------------------------------------------------------------
# Crop geometry
# --------------------------------------------------------------------------
def _even(n):
    n = int(round(n))
    return n + (n % 2)


def clamp_box(x, y, w, h, W, H):
    """Slide (never shrink) the box to fit inside the image, so the tile size
    stays uniform across arms. Shrinking would break 1:1 comparability."""
    w = min(w, W)
    h = min(h, H)
    x = max(0, min(int(round(x)), W - w))
    y = max(0, min(int(round(y)), H - h))
    return (x, y, w, h)


def plan_face_box(arms, pad_frac, move_tol_frac, pinned, img_wh):
    """Decide the single common face crop box, and which arms need their own.

    Returns (common_xywh, notes[]). Mutates arm.face_box / arm.crop_mode.

    Design: comparability first. Every arm whose detected face sits inside the
    common box gets the *identical* pixel region, so tiles flick-compare
    cleanly. An arm whose face has moved far enough to be a different
    composition gets its own box and is flagged LOUDLY -- a crop that silently
    lands on the wrong region is the worst failure this tool can have.
    """
    W, H = img_wh
    notes = []

    if pinned:
        common = clamp_box(*pinned, W, H)
        notes.append(f"face box PINNED by --face-box to {tuple(common)}")
        for a in arms:
            a.face_box = common
            a.crop_mode = "common"
            if a.det_status not in ("detected", "multi-face"):
                a.warnings.append(f"CROP UNVERIFIED ({a.det_status}) -- pinned box used")
        return common, notes

    det = [a for a in arms if a.det_xyxy is not None]
    if not det:
        common = clamp_box(*FALLBACK_FACE_XYWH, W, H)
        notes.append(f"NO ARM DETECTED A FACE -- fell back to hardcoded box {tuple(common)} "
                     f"(provenance: results/ws4/metrics_*.json face_box_xywh)")
        for a in arms:
            a.face_box = common
            a.crop_mode = "fallback"
            a.warnings.append("CROP IS A HARDCODED FALLBACK -- NOT VERIFIED ON THIS IMAGE")
        return common, notes

    # Anchor on the baseline if we have one, else the median detection.
    base = next((a for a in det if a.is_baseline), None)
    if base is not None:
        ax = base.det_xyxy
    else:
        arr = np.array([a.det_xyxy for a in det], dtype=np.float64)
        ax = tuple(np.median(arr, axis=0).tolist())
        notes.append("no baseline among detected arms -- anchored on the median detection")
    acx, acy = (ax[0] + ax[2]) / 2.0, (ax[1] + ax[3]) / 2.0
    adim = max(ax[2] - ax[0], ax[3] - ax[1])
    tol = move_tol_frac * adim

    inliers, movers = [], []
    for a in det:
        cx, cy = (a.det_xyxy[0] + a.det_xyxy[2]) / 2.0, (a.det_xyxy[1] + a.det_xyxy[3]) / 2.0
        d = float(np.hypot(cx - acx, cy - acy))
        (movers if d > tol else inliers).append((a, d))

    if not inliers:                       # anchor itself is always distance 0, so unreachable
        inliers, movers = [(base, 0.0)], []

    u = np.array([a.det_xyxy for a, _ in inliers], dtype=np.float64)
    x1, y1 = u[:, 0].min(), u[:, 1].min()
    x2, y2 = u[:, 2].max(), u[:, 3].max()
    uw, uh = x2 - x1, y2 - y1
    # Pad each dimension by a fraction of ITSELF. Padding width by a fraction of
    # the (larger) height would inflate the tile width for no reason, and tile
    # width is the only thing the 4000px sheet limit actually constrains.
    tw, th = _even(uw * (1 + 2 * pad_frac)), _even(uh * (1 + 2 * pad_frac))
    common = clamp_box((x1 + x2) / 2 - tw / 2, (y1 + y2) / 2 - th / 2, tw, th, W, H)
    notes.append(
        f"face box from {len(inliers)} detection(s): union "
        f"({x1:.0f},{y1:.0f})-({x2:.0f},{y2:.0f}) = {uw:.0f}x{uh:.0f}, "
        f"+{pad_frac:.0%} pad per axis -> {common[2]}x{common[3]} at ({common[0]},{common[1]})")

    for a, _ in inliers:
        a.face_box = common
        a.crop_mode = "common"
    for a, d in movers:
        b = a.det_xyxy
        cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
        a.face_box = clamp_box(cx - common[2] / 2, cy - common[3] / 2, common[2], common[3], W, H)
        a.crop_mode = "own"
        a.warnings.append(f"FACE MOVED {d:.0f}px -- OWN CROP BOX, NOT COMPARABLE TO THE REST")
        notes.append(f"arm '{a.name}': face centre moved {d:.0f}px (tol {tol:.0f}px) -> own box")

    for a in arms:
        if a.face_box is None:
            a.face_box = common
            a.crop_mode = "fallback"
            a.warnings.append(f"CROP NOT VERIFIED ON THIS IMAGE ({a.det_status}) -- "
                              f"using the common box from the other arms")
    return common, notes


def find_skin_box(im: Image.Image, face_xywh, size, anchor="face"):
    """Pick a flat, featureless skin patch. Same box is then used for EVERY arm
    so texture is comparable.

    Scored on two integral images:
      skin fraction  -- YCbCr skin gate, want ~1.0
      structure      -- gradient magnitude of a *blurred* luma, so fine skin
                        texture (the thing being judged) does not count as
                        structure, but eyes/nostrils/lips/hair edges do.
    Returns (box_xywh, stats dict).
    """
    a = np.asarray(im.convert("RGB")).astype(np.float32)
    H, W, _ = a.shape
    R, G, B = a[..., 0], a[..., 1], a[..., 2]
    Y = 0.299 * R + 0.587 * G + 0.114 * B
    Cb = -0.168736 * R - 0.331264 * G + 0.5 * B + 128
    Cr = 0.5 * R - 0.418688 * G - 0.081312 * B + 128
    skin = ((Cb > 77) & (Cb < 130) & (Cr > 133) & (Cr < 180) &
            (Y > 40) & (Y < 250) & (R > G) & (G > B)).astype(np.float32)
    Yb = np.asarray(Image.fromarray(Y.astype(np.uint8))
                    .filter(ImageFilter.GaussianBlur(6))).astype(np.float32)
    gy, gx = np.gradient(Yb)
    grad = np.sqrt(gx * gx + gy * gy)

    def integ(x):
        return np.pad(x, ((1, 0), (1, 0))).cumsum(0).cumsum(1)

    Is, Ig = integ(skin), integ(grad)

    def bs(I, x, y, w, h):
        return I[y + h, x + w] - I[y, x + w] - I[y + h, x] + I[y, x]

    tw = th = int(size)
    if anchor == "face" and face_xywh:
        fx, fy, fw, fh = face_xywh
        x0, y0 = max(0, fx), max(0, fy)
        x1, y1 = min(W, fx + fw), min(H, fy + fh)
    else:
        x0, y0, x1, y1 = 0, 0, W, H
    if x1 - x0 < tw or y1 - y0 < th:
        x0, y0, x1, y1 = 0, 0, W, H

    step = 8
    best = None
    n = tw * th
    for y in range(y0, y1 - th + 1, step):
        for x in range(x0, x1 - tw + 1, step):
            sf = bs(Is, x, y, tw, th) / n
            if sf < 0.95:
                continue
            gm = bs(Ig, x, y, tw, th) / n
            if best is None or gm < best[0]:
                best = (gm, sf, x, y)
    if best is None:                     # nothing skin-like at this size
        for y in range(y0, y1 - th + 1, step):
            for x in range(x0, x1 - tw + 1, step):
                sf = bs(Is, x, y, tw, th) / n
                gm = bs(Ig, x, y, tw, th) / n
                score = gm - 2.0 * sf
                if best is None or score < best[0]:
                    best = (score, sf, x, y)
    gm, sf, x, y = best
    return (x, y, tw, th), {"skin_frac": round(float(sf), 4),
                            "blur_grad": round(float(gm), 4),
                            "anchor": anchor,
                            "search_region": [x0, y0, x1 - x0, y1 - y0]}


# --------------------------------------------------------------------------
# Drawing
# --------------------------------------------------------------------------
def _tw(draw, text, font):
    b = draw.textbbox((0, 0), text, font=font)
    return b[2] - b[0], b[3] - b[1]


def _fit(draw, text, font, maxw):
    if _tw(draw, text, font)[0] <= maxw:
        return text
    e = "..."
    lo, hi = 0, len(text)
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if _tw(draw, text[:mid] + e, font)[0] <= maxw:
            lo = mid
        else:
            hi = mid - 1
    return text[:lo] + e


def _wrap(draw, text, font, maxw, max_lines):
    """Word-wrap, then ellipsis only if it still will not fit. Truncating a
    label is how a tile ends up mislabelled, so we wrap first."""
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if _tw(draw, t, font)[0] <= maxw or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
            if len(lines) == max_lines:
                break
    if len(lines) < max_lines and cur:
        lines.append(cur)
    if not lines:
        return [""]
    used = sum(len(l.split()) for l in lines)
    if used < len(words):
        lines[-1] = _fit(draw, lines[-1] + " " + " ".join(words[used:]), font, maxw)
    else:
        lines = [_fit(draw, l, font, maxw) for l in lines]
    return lines


def tile_label_lines(draw, fonts, arm, tw, region_label, region_box):
    """The exact lines a tile's gutter will carry, so the gutter can be sized
    to them instead of guessed at."""
    fname, fparam, fsmall, lh = fonts.tile(tw)
    ind = LABEL_PAD + (10 if arm.is_baseline else 0)
    maxw = tw - ind - LABEL_PAD
    out = []
    title = ("BASELINE - " + arm.name) if arm.is_baseline else arm.name
    for l in _wrap(draw, title, fname, maxw, 2):
        out.append((l, fname, ACCENT if arm.is_baseline else FG, lh[0], False))
    for l in _wrap(draw, arm.param, fparam, maxw, 2):
        out.append((l, fparam, DIM, lh[1], False))
    if arm.warnings:
        for w in arm.warnings:
            for l in _wrap(draw, "! " + w, fsmall, maxw - 8, 2):
                out.append((l, fsmall, WARN_FG, lh[2], True))
    else:
        # Order matters: crop mode first, then confidence, then the box. If this
        # line has to be ellipsised on a narrow tile, what is lost is the box
        # (recoverable from the sheet header and the manifest), never the mode.
        conf = f"conf {arm.det_conf:.2f}" if arm.det_conf is not None else arm.det_status
        b = region_box
        out.append((_fit(draw, f"{region_label} crop: {arm.crop_mode}, {conf}, 1:1  "
                              f"[{b[0]},{b[1]},{b[2]},{b[3]}]", fsmall, maxw),
                    fsmall, OK_DIM, lh[2], False))
    if arm.extra:
        out.append((_fit(draw, arm.extra, fsmall, maxw), fsmall, DIM, lh[2], False))
    return out, ind


def draw_tile(sheet, draw, fonts, arm, crop_img, ox, oy, tw, th, gut,
              region_label, region_box):
    """Tile = label gutter strip ABOVE, then the crop pasted 1:1. Labels never
    overlay the crop -- the owner is judging those pixels."""
    warn = bool(arm.warnings)
    draw.rectangle([ox, oy, ox + tw - 1, oy + gut - 1],
                   fill=(58, 20, 16) if warn else (38, 38, 38))
    if arm.is_baseline:
        draw.rectangle([ox, oy, ox + 6, oy + gut - 1], fill=ACCENT)

    lines, ind = tile_label_lines(draw, fonts, arm, tw, region_label, region_box)
    tx, ty = ox + ind, oy + 5
    for text, font, col, lheight, chip in lines:
        if chip:
            w, _h = _tw(draw, text, font)
            draw.rectangle([tx - 3, ty - 2, tx + w + 7, ty + lheight - 1], fill=WARN_BG)
        draw.text((tx, ty), text, font=font, fill=col)
        ty += lheight

    # the crop, pasted with no resampling of any kind
    py = oy + gut
    sheet.paste(crop_img, (ox, py))
    bc = BASELINE_BORDER if arm.is_baseline else (WARN_BG if warn else TILE_BORDER)
    bwid = 3 if (arm.is_baseline or warn) else 1
    for i in range(bwid):
        draw.rectangle([ox - 1 - i, py - 1 - i, ox + tw + i, py + th + i], outline=bc)
    return (ox, py, tw, th)


def build_sheet(arms_on_sheet, crops, boxes, region, tile_wh, cols, fonts,
                title, subtitle, header_lines, out_path, sheet_idx, sheet_n):
    tw, th = tile_wh
    rows = (len(arms_on_sheet) + cols - 1) // cols

    # Size the label gutter to the tallest label stack actually on this sheet,
    # so nothing is clipped and nothing overlays a crop.
    d0 = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    gut = 12 + max(sum(l[3] for l in tile_label_lines(d0, fonts, a, tw, region, b)[0])
                   for a, b in zip(arms_on_sheet, boxes))

    hdr_top = MARGIN
    hdr_h = 62 + 34 * (1 + len(header_lines)) + 14

    W = MARGIN * 2 + cols * tw + (cols - 1) * GUTTER
    H = hdr_top + hdr_h + MARGIN + rows * (gut + th) + (rows - 1) * GUTTER + MARGIN

    sheet = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(sheet)
    draw.rectangle([0, 0, W, hdr_top + hdr_h], fill=HEADER_BG)

    y = hdr_top + 4
    draw.text((MARGIN, y), _fit(draw, title, fonts.h1, W - 2 * MARGIN), font=fonts.h1, fill=FG)
    y += 58
    sub = subtitle + (f"   |   sheet {sheet_idx} of {sheet_n}" if sheet_n > 1 else "")
    draw.text((MARGIN, y), _fit(draw, sub, fonts.h2, W - 2 * MARGIN), font=fonts.h2, fill=ACCENT)
    y += 34
    for line in header_lines:
        col = WARN_FG if line.startswith("!") else DIM
        if line.startswith("!"):
            w, _h = _tw(draw, " " + line + " ", fonts.h2)
            draw.rectangle([MARGIN - 2, y - 2, MARGIN + w + 6, y + 30], fill=WARN_BG)
        draw.text((MARGIN, y), _fit(draw, line, fonts.h2, W - 2 * MARGIN), font=fonts.h2, fill=col)
        y += 34

    placements = []
    top = hdr_top + hdr_h + MARGIN
    for i, arm in enumerate(arms_on_sheet):
        r, c = divmod(i, cols)
        ox = MARGIN + c * (tw + GUTTER)
        oy = top + r * (gut + th + GUTTER)
        p = draw_tile(sheet, draw, fonts, arm, crops[i], ox, oy, tw, th, gut,
                      region, boxes[i])
        placements.append((arm, p))

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    sheet.save(out_path, "PNG", compress_level=6)
    return out_path, (W, H), placements


# --------------------------------------------------------------------------
# Verification -- this is the part that makes "1:1, no downscaling" a fact
# --------------------------------------------------------------------------
def verify_sheet(out_path, placements, source_boxes):
    """Re-open the written PNG and assert each tile region is byte-identical to
    the corresponding source crop. Not 'my resize call looks right' -- actual
    pixel equality, read back off disk."""
    sheet = np.asarray(Image.open(out_path).convert("RGB"))
    results = []
    for (arm, (ox, oy, tw, th)), (src_path, box) in zip(placements, source_boxes):
        x, y, w, h = box
        src = np.asarray(Image.open(src_path).convert("RGB"))[y:y + h, x:x + w]
        got = sheet[oy:oy + th, ox:ox + tw]
        same = (src.shape == got.shape) and bool(np.array_equal(src, got))
        results.append({
            "arm": arm.name, "ok": same,
            "src_box": [x, y, w, h], "sheet_at": [ox, oy, tw, th],
            "src_shape": list(src.shape), "sheet_shape": list(got.shape),
            "max_abs_diff": (0 if same and src.shape == got.shape
                             else (int(np.abs(src.astype(int) - got.astype(int)).max())
                                   if src.shape == got.shape else None)),
        })
    return results


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--arms-dir", default="results/face/arms",
                    help="each subdir = one arm (PNG + meta.json). Read-only.")
    ap.add_argument("--arm", action="append", default=[],
                    help="explicit arm 'name|parameter changed|path.png' (repeatable)")
    ap.add_argument("--out-dir", default="results/face")
    ap.add_argument("--prefix", default="face", help="output basename prefix")
    ap.add_argument("--title", default=None)
    ap.add_argument("--note", default=None,
                    help="loud banner line, e.g. 'TOOLING TEST -- not the deliverable'")
    ap.add_argument("--max-width", type=int, default=4000)
    ap.add_argument("--max-rows", type=int, default=4,
                    help="rows per sheet before splitting into numbered sheets")
    ap.add_argument("--pad-frac", type=float, default=0.08,
                    help="padding around the detected face union, as a fraction of its long side")
    ap.add_argument("--move-tol", type=float, default=0.25,
                    help="face-centre movement (fraction of face size) past which an arm "
                         "gets its own crop box and is flagged")
    ap.add_argument("--face-box", default=None, help="pin the face crop: x,y,w,h")
    ap.add_argument("--skin-box", default=None, help="pin the skin crop: x,y,w,h")
    ap.add_argument("--skin-size", type=int, default=400)
    ap.add_argument("--skin-anchor", choices=["face", "image"], default="face",
                    help="search for flat skin inside the face box (default) or the whole frame")
    ap.add_argument("--no-skin-sheet", action="store_true")
    ap.add_argument("--detector", default=DEFAULT_DETECTOR)
    ap.add_argument("--no-detect", action="store_true",
                    help="skip YOLO; use --face-box or the hardcoded fallback")
    ap.add_argument("--no-verify", action="store_true")
    args = ap.parse_args()

    def parse_box(s):
        if not s:
            return None
        try:
            v = [int(t) for t in s.replace(" ", "").split(",")]
            assert len(v) == 4
            return tuple(v)
        except Exception:
            sys.exit(f"bad box {s!r}, want x,y,w,h")

    pin_face, pin_skin = parse_box(args.face_box), parse_box(args.skin_box)

    arms = parse_explicit(args.arm) if args.arm else discover_arms(args.arms_dir)
    src_desc = "explicit --arm list" if args.arm else os.path.abspath(args.arms_dir)
    if not arms:
        sys.exit(f"no arms found (looked in {src_desc}). "
                 f"Expected <dir>/<arm_name>/{{*.png,meta.json}}.")

    fonts = Fonts()
    header = []
    if args.note:
        header.append("! " + args.note)
    if not fonts.ok:
        header.append("! NO TRUETYPE FONT FOUND -- labels rendered with the bitmap fallback")

    # ---- load + detect -----------------------------------------------------
    det = Detector(args.detector, enabled=not args.no_detect)
    if det.err and not args.no_detect:
        header.append(f"! FACE DETECTOR UNAVAILABLE ({det.err}) -- crops are not verified per image")
    images = {}
    sizes = set()
    print(f"[arms] {len(arms)} from {src_desc}")
    loadable = []
    for a in arms:
        try:
            # This tool is meant to be re-run as arms land, so it may catch a
            # PNG mid-write. Skip that arm loudly; do not kill the whole sheet.
            im = Image.open(a.path)
            im.load()
            im = im.convert("RGB")
        except Exception as e:
            print(f"  [skip] {a.name}: cannot read {a.path} ({type(e).__name__}: {e})")
            continue
        loadable.append(a)
        images[a.path] = im
        a.size = im.size
        sizes.add(im.size)
        xyxy, conf, status, extra = det.detect(im)
        a.det_xyxy, a.det_conf, a.det_status = xyxy, conf, status
        if extra:
            a.warnings.append(extra)
        if status == "no-face":
            a.warnings.append("FACE DETECTION FOUND NO FACE")
        elif status == "detector-error":
            a.warnings.append("FACE DETECTOR ERRORED")
        b = f"({xyxy[0]:.0f},{xyxy[1]:.0f})-({xyxy[2]:.0f},{xyxy[3]:.0f})" if xyxy else "-"
        print(f"  {a.name:<28} {im.size[0]}x{im.size[1]}  {status:<14} conf="
              f"{('%.4f' % conf) if conf else '   -  '}  {b}"
              + ("  [BASELINE]" if a.is_baseline else ""))

    arms = loadable
    if not arms:
        sys.exit("no readable arm images")
    if len(sizes) > 1:
        header.append("! ARMS ARE NOT ALL THE SAME SIZE: " +
                      ", ".join(f"{w}x{h}" for w, h in sorted(sizes)) +
                      " -- crops are absolute pixel boxes, so tiles may not correspond")
    W0, H0 = max(sizes, key=lambda s: s[0] * s[1])

    n_base = sum(1 for a in arms if a.is_baseline)
    if n_base == 0:
        header.append("! NO BASELINE IDENTIFIED among the arms -- top-left tile is NOT a reference")
    elif n_base > 1:
        header.append(f"! {n_base} arms claim to be the baseline -- using the first")
        seen = False
        for a in arms:
            if a.is_baseline:
                if seen:
                    a.is_baseline = False
                seen = True

    # ---- geometry ----------------------------------------------------------
    face_box, notes = plan_face_box(arms, args.pad_frac, args.move_tol, pin_face, (W0, H0))
    for n in notes:
        print(f"[face] {n}")

    baseline = next((a for a in arms if a.is_baseline), arms[0])
    if pin_skin:
        skin_box = clamp_box(*pin_skin, W0, H0)
        skin_stats = {"pinned": True}
        print(f"[skin] PINNED {tuple(skin_box)}")
    else:
        skin_box, skin_stats = find_skin_box(images[baseline.path], face_box,
                                             args.skin_size, args.skin_anchor)
        print(f"[skin] {tuple(skin_box)} skin_frac={skin_stats['skin_frac']} "
              f"blur_grad={skin_stats['blur_grad']} anchor={skin_stats['anchor']} "
              f"(chosen on '{baseline.name}', applied identically to every arm)")

    # ---- ordering: baseline first, then by name ----------------------------
    ordered = ([a for a in arms if a.is_baseline] +
               sorted([a for a in arms if not a.is_baseline], key=lambda a: a.name.lower()))
    base_arm = ordered[0] if ordered[0].is_baseline else None
    rest = ordered[1:] if base_arm else ordered

    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    os.makedirs(args.out_dir, exist_ok=True)
    manifest = {
        "generated": stamp, "source": src_desc, "tool": os.path.abspath(__file__),
        "max_width": args.max_width, "detector": args.detector,
        "detector_error": det.err, "face_box_xywh": list(face_box),
        "skin_box_xywh": list(skin_box), "skin_stats": skin_stats,
        "image_size": [W0, H0], "sheets": [],
        "arms": [{k: v for k, v in asdict(a).items()} for a in ordered],
    }

    all_ok = True
    for region, box in (("face", face_box), ("skin", skin_box)):
        if region == "skin" and args.no_skin_sheet:
            continue
        tw, th = box[2], box[3]
        cols = (args.max_width - 2 * MARGIN + GUTTER) // (tw + GUTTER)
        if cols < 1:
            print(f"[{region}] REFUSING: one {tw}px tile does not fit under "
                  f"--max-width {args.max_width}. Not downscaling. "
                  f"Raise --max-width or pin a smaller --{region}-box.", file=sys.stderr)
            all_ok = False
            continue
        cols = int(min(cols, max(1, len(ordered))))
        per_sheet = max(1, cols * args.max_rows - (1 if base_arm else 0))
        chunks = [rest[i:i + per_sheet] for i in range(0, len(rest), per_sheet)] or [[]]
        n_sheets = len(chunks)

        for si, chunk in enumerate(chunks, start=1):
            on = ([base_arm] if base_arm else []) + chunk
            crops, srcs, boxes = [], [], []
            for a in on:
                b = a.face_box if region == "face" else box
                b = clamp_box(*b, *a.size)
                crops.append(images[a.path].crop((b[0], b[1], b[0] + b[2], b[1] + b[3])))
                srcs.append((a.path, b))
                boxes.append(b)
            name = f"{args.prefix}_{region}_sheet{si}of{n_sheets}.png"
            out = os.path.join(args.out_dir, name)

            title = args.title or (f"{args.prefix} contact sheet - "
                                   f"{'FACE CROP' if region == 'face' else 'FLAT SKIN CROP'}")
            sub = (f"{len(on)} tiles, {tw}x{th} each, 1:1 native (no downscaling)   |   "
                   f"crop {tuple(box) if region == 'skin' else tuple(face_box)}   |   {stamp}")
            hl = list(header)
            if region == "skin":
                hl.append(f"same {tw}x{th} region on every arm: "
                          f"x={box[0]} y={box[1]}  skin={skin_stats.get('skin_frac','-')} "
                          f"flatness(blur-grad)={skin_stats.get('blur_grad','-')} "
                          f"-- texture only, no features")
            else:
                hl.append(f"source {W0}x{H0}; face box {tuple(face_box)}; "
                          f"detector {os.path.basename(args.detector)}")
            if base_arm:
                hl.append(f"baseline '{base_arm.name}' is the top-left tile of every sheet")

            p, (SW, SH), placements = build_sheet(on, crops, boxes, region, (tw, th),
                                                  cols, fonts, title, sub, hl,
                                                  out, si, n_sheets)
            wok = SW <= args.max_width
            all_ok &= wok
            print(f"[{region}] wrote {p}  {SW}x{SH}  cols={cols} rows="
                  f"{(len(on)+cols-1)//cols}  width<= {args.max_width}: "
                  f"{'PASS' if wok else 'FAIL'}")

            vres = None
            if not args.no_verify:
                vres = verify_sheet(p, placements, srcs)
                bad = [v for v in vres if not v["ok"]]
                print(f"[{region}] 1:1 pixel verification: {len(vres)-len(bad)}/{len(vres)} "
                      f"tiles byte-identical to source crop -- "
                      f"{'PASS' if not bad else 'FAIL'}")
                for v in bad:
                    print(f"        FAIL {v['arm']}: src {v['src_shape']} vs sheet "
                          f"{v['sheet_shape']} maxdiff {v['max_abs_diff']}", file=sys.stderr)
                all_ok &= not bad
            manifest["sheets"].append({"region": region, "path": os.path.abspath(p),
                                       "size": [SW, SH], "cols": cols,
                                       "tiles": [a.name for a in on],
                                       "width_ok": wok, "verify": vres})

    mp = os.path.join(args.out_dir, f"{args.prefix}_manifest.json")
    with open(mp, "w") as fh:
        json.dump(manifest, fh, indent=1)
    print(f"[done] manifest {mp}")
    print(f"[done] {'ALL CHECKS PASS' if all_ok else 'CHECKS FAILED -- see above'}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
