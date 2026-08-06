#!/usr/bin/env python3
"""T_tok sweep on one sheet: identical content, token count varied one at a time."""
import json, os, glob, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sheet_ladder import main as build

A = "/workspace/nsfw-fix/results/crash/A"

if __name__ == "__main__":
    y = json.load(open(os.path.join(A, "arm_yolo.json")))
    import json as _j, os as _os
    names = []
    for k in y:
        if not k.startswith("T_tok"):
            continue
        mp = _os.path.join(A, "arms", k, "meta.json")
        if not _os.path.exists(mp) or _j.load(open(mp)).get("cached") != 0:
            continue                       # only cold arms
        names.append((int(k[5:].split("__")[0]), k))
    order = [(f"{t} tokens", k, None) for t, k in sorted(names)]
    print(build(order, out=os.path.join(A, "T_token_sweep_sheet.png")))
