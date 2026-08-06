#!/usr/bin/env python3
"""Constant-folded API-graph diff.

Compares two ComfyUI API-format prompts node-by-node, input-by-input.
Link inputs are compared as [origin_execution_id, slot]; widget inputs by value.
Optionally folds out identity nodes (`--fold CLASS`) by rewriting every reference
to that node's output back to whatever feeds its single input.
"""
import json, sys, collections

def load(p):
    d = json.load(open(p))
    return d.get("prompt", d)

def fold(g, classes):
    """Replace references to identity-node outputs with their upstream source."""
    ids = [k for k, v in g.items() if v.get("class_type") in classes]
    src = {}
    for k in ids:
        ins = list(g[k]["inputs"].values())
        assert len(ins) == 1 and isinstance(ins[0], list), (k, g[k])
        src[k] = ins[0]
    def resolve(ref):
        seen = set()
        while isinstance(ref, list) and ref[0] in src:
            if ref[0] in seen: raise RuntimeError("identity cycle")
            seen.add(ref[0]); ref = src[ref[0]]
        return ref
    out = {}
    for k, v in g.items():
        if k in src: continue
        nv = dict(v); nv["inputs"] = {ik: (resolve(iv) if isinstance(iv, list) else iv)
                                      for ik, iv in v["inputs"].items()}
        out[k] = nv
    return out

def diff(a, b, la="A", lb="B"):
    problems = []
    ka, kb = set(a), set(b)
    for k in sorted(ka - kb): problems.append(f"node {k} ({a[k].get('class_type')}) only in {la}")
    for k in sorted(kb - ka): problems.append(f"node {k} ({b[k].get('class_type')}) only in {lb}")
    for k in sorted(ka & kb):
        na, nb = a[k], b[k]
        if na.get("class_type") != nb.get("class_type"):
            problems.append(f"node {k}: class_type {na.get('class_type')} != {nb.get('class_type')}")
            continue
        ia, ib = na.get("inputs", {}), nb.get("inputs", {})
        for name in sorted(set(ia) | set(ib)):
            va, vb = ia.get(name, "<absent>"), ib.get(name, "<absent>")
            if va != vb:
                problems.append(f"node {k} ({na.get('class_type')}) input {name!r}: {la}={va!r}  {lb}={vb!r}")
    return problems

if __name__ == "__main__":
    args = [x for x in sys.argv[1:] if not x.startswith("--")]
    folds = set()
    for i, x in enumerate(sys.argv):
        if x == "--fold": folds.add(sys.argv[i + 1])
    A, B = load(args[0]), load(args[1])
    if folds:
        A, B = fold(A, folds), fold(B, folds)
    ca = collections.Counter(v.get("class_type") for v in A.values())
    cb = collections.Counter(v.get("class_type") for v in B.values())
    print(f"{args[0]}: {len(A)} nodes   {args[1]}: {len(B)} nodes")
    if ca != cb:
        for c in sorted(set(ca) | set(cb)):
            if ca[c] != cb[c]: print(f"  class count differs: {c}: {ca[c]} vs {cb[c]}")
    p = diff(A, B, args[0], args[1])
    print(f"--- {len(p)} difference(s) ---")
    for x in p: print("  " + x)
    sys.exit(1 if p else 0)
