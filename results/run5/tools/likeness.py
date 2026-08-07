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

_app = None
def app():
    global _app
    if _app is None:
        _app = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
        _app.prepare(ctx_id=-1, det_size=(1024, 1024))
    return _app

def top_face(path):
    img = cv2.imread(path)
    if img is None:
        return None
    faces = app().get(img)
    if not faces:
        # retry on upper-centre crop (full-body small-face fallback)
        h, w = img.shape[:2]
        crop = img[0:int(h*0.55), int(w*0.15):int(w*0.85)]
        faces = app().get(crop)
        if not faces:
            return None
    f = max(faces, key=lambda x: x.det_score)
    return {"emb": f.normed_embedding.astype(float).tolist(),
            "det": float(f.det_score),
            "bbox": [float(v) for v in f.bbox]}

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

def main():
    dirs = sys.argv[1:] or [OUT + "/A"]
    rows = scan(dirs)
    # centroid from ZIT portrait references (res_multistep arms only, with lora)
    ref_keys = [k for k in rows
                if "/zref_P_" in "/" + k and "nolora" not in k and "eak" not in k
                and rows[k]["face"]]
    if not ref_keys:
        print("no ZIT portrait refs found"); sys.exit(1)
    embs = np.array([rows[k]["face"]["emb"] for k in ref_keys])
    centroid = embs.mean(axis=0)
    centroid /= np.linalg.norm(centroid)
    # within-reference band
    band = [cos(rows[a]["face"]["emb"], rows[b]["face"]["emb"])
            for i, a in enumerate(ref_keys) for b in ref_keys[i+1:]]
    out = {"reference_images": ref_keys,
           "zit_to_zit_pairwise": {"min": min(band) if band else None,
                                    "max": max(band) if band else None,
                                    "mean": float(np.mean(band)) if band else None},
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
