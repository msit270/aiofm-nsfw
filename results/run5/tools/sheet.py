#!/usr/bin/env python3
"""Contact sheets: labelled face-crop (or body-crop) tiles at 1:1.

Usage:
  sheet.py out.png title crop_mode tile_px label=path [label=path ...]
crop_mode: face | body | mouth | full
Baseline tile: prefix its label with '*' -> drawn with a red border + [BASELINE].
Face box detected per image (never reused). Tiles are 1:1 pixels from the
source (face box height scaled to tile_px only if larger than tile_px).
"""
import sys, os
import numpy as np
import cv2

sys.path.insert(0, "/workspace/run5/tools")
from likeness import top_face

def get_crop(path, mode, tile):
    img = cv2.imread(path)
    if img is None:
        return None
    h, w = img.shape[:2]
    f = top_face(path)
    if f is None:
        # fall back: centre crop
        cx, cy, bh = w // 2, h // 3, h // 4
    else:
        via = f.get("via", "full@640").split("@")[0]
        x1, y1, x2, y2 = f["bbox"]
        mul = {"half": 2, "quarter": 4}.get(via, 1)
        x1, y1, x2, y2 = [v * mul for v in (x1, y1, x2, y2)]
        if via == "upper":
            x1, x2 = x1 + w * 0.15, x2 + w * 0.15
        cx, cy = int((x1 + x2) / 2), int((y1 + y2) / 2)
        bh = int(y2 - y1)
    if mode == "face":
        half = int(bh * 0.75)
    elif mode == "mouth":
        cy = int(cy + bh * 0.25)
        half = int(bh * 0.35)
    elif mode == "body":
        cy = int(cy + bh * 1.8)
        half = int(bh * 0.9)
    else:  # full
        scale = tile / max(h, w)
        return cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
    x1c, x2c = max(0, cx - half), min(w, cx + half)
    y1c, y2c = max(0, cy - half), min(h, cy + half)
    crop = img[y1c:y2c, x1c:x2c]
    if crop.shape[0] == 0 or crop.shape[1] == 0:
        return None
    if crop.shape[0] > tile:
        s = tile / crop.shape[0]
        crop = cv2.resize(crop, (int(crop.shape[1] * s), tile), interpolation=cv2.INTER_AREA)
    return crop


def main():
    out, title, mode, tile_px = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
    pairs = [a.split("=", 1) for a in sys.argv[5:]]
    tiles = []
    for label, path in pairs:
        baseline = label.startswith("*")
        label = label.lstrip("*")
        crop = get_crop(path, mode, tile_px)
        if crop is None:
            print("SKIP (no crop):", path)
            continue
        tiles.append((label, baseline, crop))
    if not tiles:
        sys.exit("no tiles")
    th = max(t[2].shape[0] for t in tiles) + 46
    tw = max(t[2].shape[1] for t in tiles) + 16
    cols = min(4, len(tiles))
    rows = (len(tiles) + cols - 1) // cols
    W, H = cols * tw, rows * th + 40
    sheet = np.full((H, W, 3), 24, np.uint8)
    cv2.putText(sheet, title, (12, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    for i, (label, baseline, crop) in enumerate(tiles):
        r, c = divmod(i, cols)
        x0, y0 = c * tw + 8, 40 + r * th + 4
        ch, cw = crop.shape[:2]
        sheet[y0:y0 + ch, x0:x0 + cw] = crop
        if baseline:
            cv2.rectangle(sheet, (x0 - 3, y0 - 3), (x0 + cw + 3, y0 + ch + 3), (0, 0, 255), 3)
            label = "[BASELINE] " + label
        cv2.putText(sheet, label[:60], (x0, y0 + ch + 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.62, (0, 255, 255) if baseline else (255, 255, 255), 1)
    cv2.imwrite(out, sheet)
    print("wrote", out, sheet.shape)


if __name__ == "__main__":
    main()
