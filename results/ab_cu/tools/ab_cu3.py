#!/usr/bin/env python3
"""AB round 3 — body regression check for the close-up default candidates.

Owner picked D (base 8/cfg1.0, 617 den .25) as CU default candidate. Decision
rule: if D regresses body, D becomes a CLOSE-UP PRESET, not a global default.
So the candidates render on FULL-BODY and PORTRAIT against the CURRENT PC1
ea-0.50 config, fresh, same boot, same protocol. Owner named F/G for the body
run; D-base arms are included because the stated decision hinges on D's body
numbers (noted in the report).

  H_pc1_FB / I_pc1_PT              PC1 verbatim        (gate: == run-6 P_FB / P_PT)
  J_b8c10_FB / K_b8c10_PT          D base (8/1.0), den .25
  L_b30c15den25_FB / M_b30c15den25_PT   F config (30/1.5, den .25)
  N_b30c15den45_FB / O_b30c15den45_PT   G config (30/1.5, den .45)

Prompts: run-6 FB/PT verbatim. Seed 12345, luna@1.0, /free before each arm.
Widget-only diffs -> one model composition. Gates enumerate exact deltas.

Usage: ab_cu3.py [--dry]
"""
import sys, json

sys.path.insert(0, "/workspace/nsfw-quality/results/ab_cu/tools")
from ab_cu import pc_graph, run_arm, free

R6 = "/workspace/nsfw-quality/results/run6"

FB = ("photorealistic full body photograph of a young woman with long dark "
      "hair standing on a hotel balcony at golden hour, wearing a black silk "
      "slip dress, natural skin texture with visible pores and freckles, "
      "shot on 85mm, shallow depth of field")
PT = ("photorealistic portrait photograph of a young woman standing in soft "
      "window light, natural skin texture with visible pores, detailed eyes, "
      "detailed hands at her sides, looking at the camera, 85mm lens, shallow "
      "depth of field")

ARMS = [
    # arm, prompt, ref arm for gate, base edits, 617 denoise
    ("H_pc1_FB",         FB, "P_FB", None,                       None),
    ("I_pc1_PT",         PT, "P_PT", None,                       None),
    ("J_b8c10_FB",       FB, "P_FB", {"steps": 8,  "cfg": 1.0},  None),
    ("K_b8c10_PT",       PT, "P_PT", {"steps": 8,  "cfg": 1.0},  None),
    ("L_b30c15den25_FB", FB, "P_FB", {"steps": 30, "cfg": 1.5},  None),
    ("M_b30c15den25_PT", PT, "P_PT", {"steps": 30, "cfg": 1.5},  None),
    ("N_b30c15den45_FB", FB, "P_FB", {"steps": 30, "cfg": 1.5},  0.45),
    ("O_b30c15den45_PT", PT, "P_PT", {"steps": 30, "cfg": 1.5},  0.45),
]


def build(prompt, base, den):
    g = pc_graph(prompt)
    if base:
        g["ZB_k"]["inputs"]["steps"] = base["steps"]
        g["ZB_k"]["inputs"]["cfg"] = base["cfg"]
    if den is not None:
        g["619:617"]["inputs"]["denoise"] = den
    return g


def gate(arm, g, refarm, base, den):
    ref = json.load(open(f"{R6}/{refarm}/api_graph.json"))
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
    if base:
        if base["steps"] != 30:
            expect[("ZB_k", "steps")] = (30, base["steps"])
        if base["cfg"] != 2.0:
            expect[("ZB_k", "cfg")] = (2.0, base["cfg"])
    if den is not None:
        expect[("619:617", "denoise")] = (0.25000000000000006, den)
    if diffs != expect:
        raise SystemExit(f"{arm}: GATE FAIL vs {refarm}\n  got     {diffs}\n  expected {expect}")
    tag = sorted(expect) if expect else "NONE (verbatim PC1)"
    print(f"{arm}: gate PASS vs {refarm} — deltas {tag}", flush=True)


if __name__ == "__main__":
    built = []
    for arm, prompt, refarm, base, den in ARMS:
        g = build(prompt, base, den)
        gate(arm, g, refarm, base, den)
        built.append((arm, g))
    if "--dry" in sys.argv:
        print("dry run: 8 arms built, gates passed, nothing submitted")
        sys.exit(0)
    for arm, g in built:
        free()
        ex = run_arm(arm, g)
        print(f"[{arm}] ok exec={ex:.1f}s", flush=True)
    print("AB round 3 (body) done", flush=True)
