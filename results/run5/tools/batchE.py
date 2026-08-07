#!/usr/bin/env python3
"""Batch E — V9 mini-derivation on top of the measured SDXL repairs."""
import sys, time, json
sys.path.insert(0, "/workspace/run5/tools")
from r5 import boot, run_arm, pipeline_graph, STD_TAPS, buyer_values
from candidates import sdxl_fixed, V9, FIXED_PROMPT

boot()

def go(arm, graph):
    t0 = time.time()
    try:
        ex, _ = run_arm("E", arm, graph)
        print(f"[{arm}] ok exec={ex:.1f}s wall={time.time()-t0:.1f}s", flush=True)
    except Exception as e:
        print(f"[{arm}] FAIL {e}", flush=True)

def v9fix(extra=None):
    g = sdxl_fixed()          # V9 + fixboth + mouth 0.5 by default
    for nid, kv in (extra or {}).items():
        g[nid]["inputs"].update(kv)
    return g

# 1) V9 + repairs, stock 40/4 base
go("E_v9fix", v9fix())
# 2) creator-recommended base: 30 steps cfg 3
go("E_v9fix_c3s30", v9fix({"619:592": {"steps": 30, "cfg": 3}}))
# 3) + max-likeness face rebuild
go("E_v9fix_den085", v9fix({"620:114": {"denoise": 0.85}}))
# 4) V7 + repairs + den085 (is V9 or V7 the better repaired base?)
g = sdxl_fixed()
g["619:613"]["inputs"]["ckpt_name"] = "SDXLNSFW.safetensors"
g["620:114"]["inputs"]["denoise"] = 0.85
go("E_v7fix_den085", g)
print("batch E done", flush=True)
