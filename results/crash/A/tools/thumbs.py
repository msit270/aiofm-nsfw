#!/usr/bin/env python3
"""Commit-sized view of every arm: the 621:163 tap cropped to the detector's own
face box and halved. The full-resolution frames stay on the pod."""
import os, glob, json
from PIL import Image

ARMS = "/workspace/nsfw-fix/results/crash/A/arms"
OUT = "/workspace/nsfw-fix/results/crash/A/thumbs"
BOX = (848, 790, 2196, 2726)

os.makedirs(OUT, exist_ok=True)
n = 0
for d in sorted(os.listdir(ARMS)):
    p = os.path.join(ARMS, d)
    if not os.path.isdir(p):
        continue
    for tap in glob.glob(os.path.join(p, "nTAP163__*.png")):
        dst = os.path.join(OUT, f"{d}__tap163_facebox_half.png")
        if os.path.exists(dst):
            continue
        im = Image.open(tap).convert("RGB").crop(BOX)
        im.resize((im.size[0] // 2, im.size[1] // 2), Image.LANCZOS).save(dst)
        n += 1
# the base too
b = "/workspace/ComfyUI/output/crashA/base137_00001_.png"
dst = os.path.join(OUT, "A0_base_620-137_facebox_half.png")
if os.path.exists(b) and not os.path.exists(dst):
    im = Image.open(b).convert("RGB").crop(BOX)
    im.resize((im.size[0] // 2, im.size[1] // 2), Image.LANCZOS).save(dst)
    n += 1
print("wrote", n)
