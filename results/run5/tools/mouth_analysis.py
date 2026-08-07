#!/usr/bin/env python3
"""Agent B analysis: mouth-stage deletion, before vs after per composition.
Diff maps + mouth-region localization + verdict data."""
import cv2, numpy as np, glob, json, os, sys
sys.path.insert(0, "/workspace/run5/tools")
from likeness import top_face

O = "/workspace/run5/output"
PAIRS = [
    ("FB", f"{O}/G/G_PC1_FB/Instaraw/SDXL/Metadata/HasMetadata_00001_.png",
           f"{O}/H/H_nomouth_FB/Instaraw/SDXL/Metadata/HasMetadata_00001_.png"),
    ("PT", f"{O}/G/G_PC1_PT/Instaraw/SDXL/Metadata/HasMetadata_00001_.png",
           f"{O}/H/H_nomouth_PT/Instaraw/SDXL/Metadata/HasMetadata_00001_.png"),
    ("CU", f"{O}/G/G_PC1_CU/Instaraw/SDXL/Metadata/HasMetadata_00001_.png",
           f"{O}/H/H_nomouth_CU/Instaraw/SDXL/Metadata/HasMetadata_00001_.png"),
    ("OM", f"{O}/H/H_PC1_OM/Instaraw/SDXL/Metadata/HasMetadata_00001_.png",
           f"{O}/H/H_nomouth_OM/Instaraw/SDXL/Metadata/HasMetadata_00001_.png"),
]
out = {}
for comp, before, after in PAIRS:
    a, b = cv2.imread(before), cv2.imread(after)
    if a is None or b is None:
        out[comp] = "missing"
        print(comp, "missing"); continue
    d = np.abs(a.astype(np.int16) - b.astype(np.int16)).max(axis=2)
    ys, xs = np.where(d > 8)
    row = {"px_gt8": int(len(xs)), "pct": round(100 * len(xs) / d.size, 4),
           "max": int(d.max())}
    if len(xs):
        row["bbox"] = [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]
    out[comp] = row
    print(comp, row, flush=True)
    # mouth crops for the sheet (before/after), around the diff or face lower third
    f = top_face(before)
    if f:
        via = f.get("via", "full@640").split("@")[0]
        mul = {"half": 2, "quarter": 4}.get(via, 1)
        x1, y1, x2, y2 = [v * mul for v in f["bbox"]]
        cy = int(y2 - (y2 - y1) * 0.18); cx = int((x1 + x2) / 2)
        half = int((y2 - y1) * 0.35)
        for tag, im in (("before", a), ("after", b)):
            crop = im[max(0, cy - half):cy + half, max(0, cx - half * 2):cx + half * 2]
            cv2.imwrite(f"/workspace/run5/mouthdiff_{comp}_{tag}.png", crop)
json.dump(out, open("/workspace/nsfw-quality/results/run5/mouth_deletion.json", "w"), indent=1)
print("written results/run5/mouth_deletion.json")
