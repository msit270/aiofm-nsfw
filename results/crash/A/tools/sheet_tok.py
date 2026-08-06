#!/usr/bin/env python3
"""T_tok sweep on one sheet: identical content, token count varied one at a time."""
import json, os, glob, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sheet_ladder import main as build

A = "/workspace/nsfw-fix/results/crash/A"

if __name__ == "__main__":
    y = json.load(open(os.path.join(A, "arm_yolo.json")))
    toks = sorted(int(k[5:]) for k in y if k.startswith("T_tok"))
    order = [(f"{t} tokens", f"T_tok{t:02d}", None) for t in toks]
    print(build(order, out=os.path.join(A, "T_token_sweep_sheet.png")))
