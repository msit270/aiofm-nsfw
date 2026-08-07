#!/usr/bin/env python3
"""Master scoreboard: one row per (arm, composition) — likeness + texture.
Reads likeness_scores.json + tap_metrics.json; prints markdown; writes
results/run5/SCOREBOARD.md."""
import json, re

L = json.load(open("/workspace/nsfw-quality/results/run5/likeness_scores.json"))
try:
    T = json.load(open("/workspace/nsfw-quality/results/run5/tap_metrics.json"))
except FileNotFoundError:
    T = {}

rows = []
for k, s in sorted(L["scores"].items()):
    if "HasMetadata" not in k and "/img/" not in k:
        continue
    m = T.get(k) or {}
    face = (m.get("face") or {})
    body = (m.get("body") or {})
    rows.append({
        "arm": k.split("/Instaraw")[0].split("/img/")[0],
        "cos": s["cos_to_luna"],
        "det": s["det"],
        "faceHF": face.get("highfreq_rms"),
        "bodyHF": body.get("highfreq_rms"),
        "flap": face.get("lapvar"),
    })

md = ["# run-5 scoreboard (likeness = cos to luna-ZIT centroid; band 0.92-0.94, floor ~0.33)",
      "", "| arm | cos | faceHF | bodyHF | face-lap |", "|---|---|---|---|---|"]
for r in rows:
    f = lambda v, d=2: ("%.*f" % (d, v)) if isinstance(v, (int, float)) else "-"
    md.append(f"| {r['arm']} | {f(r['cos'],4)} | {f(r['faceHF'])} | {f(r['bodyHF'])} | {f(r['flap'],1)} |")
out = "\n".join(md)
print(out)
open("/workspace/nsfw-quality/results/run5/SCOREBOARD.md", "w").write(out + "\n")
