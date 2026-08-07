#!/usr/bin/env python3
"""Packaging gate: source api graph vs harness-captured api graph.

Ignores: TAP_* nodes; the benign key set (rgthree_comparer UI blob,
node_identifier regeneration, previewMode JS widget). Everything else must
match under canonical relabeling (greedy class+widgets pairing, then link
topology check via recursive signature).
Exit 0 = equivalent; 1 = differences (printed).
"""
import json, sys
from collections import defaultdict

BENIGN_KEYS = {"rgthree_comparer", "node_identifier", "previewMode"}


def norm(g):
    out = {}
    for nid, n in g.items():
        if nid.startswith("TAP_"):
            continue
        inputs = {k: v for k, v in n["inputs"].items() if k not in BENIGN_KEYS}
        out[nid] = {"class_type": n["class_type"], "inputs": inputs}
    return out


def sig(g):
    memo = {}
    def h(nid, depth=0):
        if nid in memo:
            return memo[nid]
        if depth > 300:
            return "CYCLE"
        n = g[nid]
        parts = [n["class_type"]]
        for k in sorted(n["inputs"]):
            v = n["inputs"][k]
            if isinstance(v, list) and str(v[0]) in g:
                parts.append((k, h(str(v[0]), depth + 1), v[1]))
            else:
                parts.append((k, json.dumps(v, sort_keys=True)))
        memo[nid] = hash(tuple(map(str, parts)))
        return memo[nid]
    return sorted(h(n) for n in g), memo


def main():
    a = norm(json.load(open(sys.argv[1])))
    b = norm(json.load(open(sys.argv[2])))
    sa, ma = sig(a)
    sb, mb = sig(b)
    if sa == sb:
        print(f"EQUIVALENT ({len(a)} nodes, canonical signatures match)")
        sys.exit(0)
    # locate differing nodes: signature multiset diff
    from collections import Counter
    ca, cb = Counter(ma.values()), Counter(mb.values())
    onlya = ca - cb
    onlyb = cb - ca
    ra = {v: k for k, v in ma.items()}
    rb = {v: k for k, v in mb.items()}
    print("DIFFERENT — nodes whose canonical signature has no partner:")
    for s in onlya:
        nid = ra[s]
        print(f"  A {nid} {a[nid]['class_type']}: "
              f"{json.dumps({k: v for k, v in a[nid]['inputs'].items() if not isinstance(v, list)})[:220]}")
    for s in onlyb:
        nid = rb[s]
        print(f"  B {nid} {b[nid]['class_type']}: "
              f"{json.dumps({k: v for k, v in b[nid]['inputs'].items() if not isinstance(v, list)})[:220]}")
    sys.exit(1)


if __name__ == "__main__":
    main()
