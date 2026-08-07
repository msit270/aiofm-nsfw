#!/usr/bin/env python3
"""Agent A/E: like-for-like hand sheet across all J arms + baseline.
Every tile: mediapipe hand box, equal hand scale, same margin."""
import sys, glob, os
sys.path.insert(0, "/workspace/run5/tools")
import subprocess

O = "/workspace/run5/output"
pairs = [("*PC1 baseline (detailed-prompt)", f"{O}/G/G_PC1_FB/Instaraw/SDXL/Metadata/HasMetadata_00001_.png")]
for d in sorted(glob.glob(f"{O}/J/J_*")):
    arm = os.path.basename(d)
    f = glob.glob(d + "/Instaraw/SDXL/Metadata/*.png")
    if f and "_PT" not in arm:
        pairs.append((arm.replace("J_", ""), f[0]))
args = [f"{l}={p}" for l, p in pairs]
cmd = ["/workspace/run5/venv/bin/python", "/workspace/run5/tools/sheet.py",
       "/workspace/nsfw-quality/results/run5/SHEETS/S14_hands_arms.png",
       "S14 HANDS: all arms, like-for-like hand crops (FB comp)", "hand", "430"] + args
r = subprocess.run(cmd, capture_output=True, text=True)
print(r.stdout[-500:], r.stderr[-200:] if r.returncode else "")
# PT pair separately (different comp)
pt = [("*PC1 PT baseline", f"{O}/G/G_PC1_PT/Instaraw/SDXL/Metadata/HasMetadata_00001_.png"),
      ("A1_neutral_PT", f"{O}/J/J_A1_neutral_PT/Instaraw/SDXL/Metadata/HasMetadata_00001_.png")]
cmd = ["/workspace/run5/venv/bin/python", "/workspace/run5/tools/sheet.py",
       "/workspace/nsfw-quality/results/run5/SHEETS/S14b_hands_PT.png",
       "S14b HANDS PT comp", "hand", "430"] + [f"{l}={p}" for l, p in pt]
r = subprocess.run(cmd, capture_output=True, text=True)
print(r.stdout[-300:])
