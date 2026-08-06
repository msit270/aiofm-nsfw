#!/usr/bin/env python3
"""Re-derive every arm's conditioning length from the graph that was actually
SUBMITTED (arms/*/api_graph.json), not from the metadata, and check it against
the arm's name and its recorded meta. Nothing in the write-up is transcribed."""
import sys, json, os
sys.path.insert(0, "/workspace/ComfyUI")
import comfy.text_encoders.z_image as z

A = "/workspace/nsfw-fix/results/crash/A/arms"

tok = z.ZImageTokenizer()
nt = lambda s: len(tok.tokenize_with_weights(s)["qwen3_4b"][0])
bad, rows = [], []
for d in sorted(os.listdir(A)):
    g, m = os.path.join(A, d, "api_graph.json"), os.path.join(A, d, "meta.json")
    if not (os.path.exists(g) and os.path.exists(m)):
        continue
    G, M = json.load(open(g)), json.load(open(m))
    if "620:106" not in G:
        continue
    t = G["620:106"]["inputs"]["text"]
    if t != (M.get("text_106") or ""):
        bad.append((d, "meta text does not match the submitted graph"))
    n = nt(t)
    if d.startswith("T_tok"):
        exp = int(d[5:].split("__")[0])
        if n != exp:
            bad.append((d, f"token count {n} != name {exp}"))
    rows.append(f"{d:40s} tokens={n:3d} status={str(M.get('status')):8s} cached={M.get('cached')}")
print("\n".join(rows))
print("\nPROBLEMS:", bad or "none")
