#!/usr/bin/env python3
"""AB_CU round 2 — 617 denoise judged on a NON-BROKEN close-up base.

Round 1 (A/B/C) all carried the shipped base 30 steps / cfg 2.0 = the S12
blotchy-CU regime, so the dominant variable was the base defect, not 617.
This round corrects the base first, then varies 617 denoise:

  D_b8c10_den25    base 8 steps / cfg 1.0   617 den .25   (README CU fallback)
  E_b8c10_den45    base 8 steps / cfg 1.0   617 den .45
  F_b30c15_den25   base 30 steps / cfg 1.5  617 den .25   (run-5 open item:
  G_b30c15_den45   base 30 steps / cfg 1.5  617 den .45    cfg-1.5-on-CU untested)

Same CU prompt, seed 12345, luna@1.0, /free before each arm, one render per
arm, server 18188. Widget-only diffs -> one model composition, interleave rule
not in play.

Gate per arm, before any submit: the graph must differ from the committed
run-6 P_CU reference by EXACTLY the intended widget set (plus SaveImage
prefix), enumerated below. SystemExit on any surplus or missing diff.

Usage: ab_cu2.py [--dry]
"""
import sys, json

sys.path.insert(0, "/workspace/nsfw-quality/results/ab_cu/tools")
from ab_cu import pc_graph, run_arm, free, CU, P_CU_REF

ARMS = [
    ("D_b8c10_den25",  {"steps": 8,  "cfg": 1.0}, 0.25000000000000006),
    ("E_b8c10_den45",  {"steps": 8,  "cfg": 1.0}, 0.45),
    ("F_b30c15_den25", {"steps": 30, "cfg": 1.5}, 0.25000000000000006),
    ("G_b30c15_den45", {"steps": 30, "cfg": 1.5}, 0.45),
]


def build(base, den):
    g = pc_graph(CU)
    g["ZB_k"]["inputs"]["steps"] = base["steps"]
    g["ZB_k"]["inputs"]["cfg"] = base["cfg"]
    g["619:617"]["inputs"]["denoise"] = den
    return g


def gate(arm, g, base, den):
    ref = json.load(open(P_CU_REF))
    diffs = {}
    for nid in sorted(set(ref) | set(g)):
        a, b = ref.get(nid), g.get(nid)
        if a is None or b is None:
            raise SystemExit(f"{arm}: node set differs at {nid}")
        for k in sorted(set(a["inputs"]) | set(b["inputs"])):
            va, vb = a["inputs"].get(k), b["inputs"].get(k)
            if va != vb:
                if a["class_type"] == "SaveImage" and k == "filename_prefix":
                    continue
                diffs[(nid, k)] = (va, vb)
    expect = {}
    if base["steps"] != 30:
        expect[("ZB_k", "steps")] = (30, base["steps"])
    if base["cfg"] != 2.0:
        expect[("ZB_k", "cfg")] = (2.0, base["cfg"])
    if den != 0.25000000000000006:
        expect[("619:617", "denoise")] = (0.25000000000000006, den)
    if diffs != expect:
        raise SystemExit(f"{arm}: GATE FAIL\n  got     {diffs}\n  expected {expect}")
    print(f"{arm}: gate PASS — diffs vs P_CU are exactly {sorted(expect)}", flush=True)


if __name__ == "__main__":
    built = []
    for arm, base, den in ARMS:
        g = build(base, den)
        gate(arm, g, base, den)
        built.append((arm, g))
    if "--dry" in sys.argv:
        print("dry run: 4 arms built, gates passed, nothing submitted")
        sys.exit(0)
    for arm, g in built:
        free()
        ex = run_arm(arm, g)
        print(f"[{arm}] ok exec={ex:.1f}s", flush=True)
    print("AB_CU round 2 done", flush=True)
