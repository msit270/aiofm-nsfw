#!/usr/bin/env python3
"""AB_CU scorer: ArcFace cos-to-Luna centroid + run-5 texture metrics,
over /workspace/ComfyUI/output/AB_CU/<arm>/. Mirrors run6/tools/score6.py.
Writes results/ab_cu/scores.json."""
import sys, os, json, glob
sys.path.insert(0, "/workspace/run5/tools")
from likeness import top_face, cos
from analyze_taps import measure

OUT = "/workspace/ComfyUI/output/AB_CU"
DEST = "/workspace/nsfw-quality/results/ab_cu/scores.json"
C = json.load(open("/workspace/nsfw-quality/results/run5/centroid.json"))["centroid"]

rows = {}
for p in sorted(glob.glob(f"{OUT}/*/img*.png")):
    rel = os.path.relpath(p, OUT)
    f = top_face(p)
    m = measure(p)
    rows[rel] = {
        "cos": round(cos(f["emb"], C), 4) if f else None,
        "det": round(f["det"], 3) if f else None,
        "face_px_h": round(m["face_px_h"], 0) if m else None,
        "faceHF": round(m["face"]["highfreq_rms"], 2) if m else None,
        "bodyHF": round(m["body"]["highfreq_rms"], 2) if m and "body" in m else None,
        "face_lapvar": round(m["face"]["lapvar"], 0) if m else None,
        "frame_luma_sd": round(m["frame"]["luma_sd"], 1) if m else None,
        "frame_warmth": round(m["frame"]["warmth"], 1) if m else None,
    }
    print(f"{rel:40s} cos={rows[rel]['cos']} det={rows[rel]['det']} "
          f"faceHF={rows[rel]['faceHF']} bodyHF={rows[rel]['bodyHF']}", flush=True)
json.dump(rows, open(DEST, "w"), indent=1, sort_keys=True)
print("wrote", DEST)
