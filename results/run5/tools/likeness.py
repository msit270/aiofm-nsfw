#!/usr/bin/env python3
"""ArcFace likeness scoring (insightface buffalo_l, CPU).

Reference identity = mean normed embedding of the ZIT portrait renders
(zref_P_*), i.e. "Luna as the ZIT LoRA defines her".
Score = cosine similarity of each image's top face to that centroid.
Outputs results/run5/<batch>/likeness.json + a printed table.

Usage: likeness.py <glob-or-dir> [more...]   (each arg: dir scanned for pngs)
"""
import sys, os, json, glob
import numpy as np
import cv2
from insightface.app import FaceAnalysis

OUT = "/workspace/run5/output"

_apps = {}
def app(ds=640):
    if ds not in _apps:
        a = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
        # NOTE: det_size (1024,1024) returns 0 faces on 896x1152 inputs in this
        # build (debugged 2026-08-07) -> 640 primary, 320 fallback.
        a.prepare(ctx_id=-1, det_size=(ds, ds))
        _apps[ds] = a
    return _apps[ds]

def top_face(path):
    img = cv2.imread(path)
    if img is None:
        return None
    variants = [("full", img)]
    h, w = img.shape[:2]
    # frame-filling face: SCRFD misses very large faces -> downscale retries
    variants.append(("half", cv2.resize(img, (w // 2, h // 2))))
    variants.append(("quarter", cv2.resize(img, (w // 4, h // 4))))
    # full-body small face: upper-centre crop retry
    variants.append(("upper", img[0:int(h * 0.55), int(w * 0.15):int(w * 0.85)]))
    for tag, v in [(f"{t}@{d}", vv) for t, vv in variants for d in (640, 320)]:
        d = int(tag.split("@")[1])
        faces = app(d).get(v)
        if faces:
            f = max(faces, key=lambda x: x.det_score)
            return {"emb": f.normed_embedding.astype(float).tolist(),
                    "det": float(f.det_score), "via": tag,
                    "bbox": [float(x) for x in f.bbox]}
    return None

def cos(a, b):
    a, b = np.asarray(a), np.asarray(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

def scan(dirs):
    rows = {}
    for d in dirs:
        for p in sorted(glob.glob(os.path.join(d, "**", "*.png"), recursive=True)):
            rel = os.path.relpath(p, OUT)
            r = top_face(p)
            rows[rel] = {"path": p, "face": r}
            print(f"  scanned {rel}: " +
                  (f"det={r['det']:.3f}" if r else "NO FACE"), flush=True)
    return rows

CENTROID_FILE = "/workspace/nsfw-quality/results/run5/centroid.json"
REF_ARMS = ["A/zref_P_12345/img/img_00001_.png",
            "A/zref_P_777/img/img_00001_.png",
            "A/zref_P_999/img/img_00001_.png"]

def get_centroid():
    """Pinned reference identity: the three batch-A ZIT portrait renders.
    Computed once, stored; every later scan scores against the SAME centroid."""
    if os.path.exists(CENTROID_FILE):
        d = json.load(open(CENTROID_FILE))
        return np.array(d["centroid"]), d
    rows = {k: {"face": top_face(os.path.join(OUT, k))} for k in REF_ARMS}
    missing = [k for k in rows if not rows[k]["face"]]
    if missing:
        raise RuntimeError(f"centroid refs missing/faceless: {missing}")
    embs = np.array([rows[k]["face"]["emb"] for k in REF_ARMS])
    centroid = embs.mean(axis=0)
    centroid /= np.linalg.norm(centroid)
    band = [cos(rows[a]["face"]["emb"], rows[b]["face"]["emb"])
            for i, a in enumerate(REF_ARMS) for b in REF_ARMS[i+1:]]
    d = {"centroid": centroid.tolist(), "reference_images": REF_ARMS,
         "zit_to_zit_pairwise": {"min": min(band), "max": max(band),
                                  "mean": float(np.mean(band))}}
    json.dump(d, open(CENTROID_FILE, "w"), indent=1)
    return centroid, d

def main():
    dirs = sys.argv[1:] or [OUT + "/A"]
    centroid, cd = get_centroid()
    rows = scan(dirs)
    out = {"reference_images": cd["reference_images"],
           "zit_to_zit_pairwise": cd["zit_to_zit_pairwise"],
           "scores": {}}
    for k, v in sorted(rows.items()):
        if v["face"]:
            out["scores"][k] = {"cos_to_luna": cos(v["face"]["emb"], centroid),
                                "det": v["face"]["det"]}
        else:
            out["scores"][k] = {"cos_to_luna": None, "det": None}
    print(f"\nZIT-to-ZIT band: {out['zit_to_zit_pairwise']}")
    print(f"{'image':66s} {'cos':>7s} {'det':>6s}")
    for k, s in out["scores"].items():
        c = f"{s['cos_to_luna']:.4f}" if s["cos_to_luna"] is not None else "  none"
        d = f"{s['det']:.3f}" if s["det"] else "    -"
        print(f"{k:66s} {c:>7s} {d:>6s}")
    dest = "/workspace/nsfw-quality/results/run5/likeness_scores.json"
    # merge if exists
    if os.path.exists(dest):
        old = json.load(open(dest))
        old["scores"].update(out["scores"])
        for f in ("reference_images", "zit_to_zit_pairwise"):
            old[f] = out[f]
        out = old
    json.dump(out, open(dest, "w"), indent=1)
    print("\nwrote", dest)

if __name__ == "__main__":
    main()
