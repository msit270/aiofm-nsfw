#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# Vendored from WS1's results/ws1/integrity.py, logic unchanged, so the harness
# does not depend on a file in the scratch results/ tree.
#
# WS2 review — verified, not taken on faith:
#   * 14 problems on tools/fixtures/red_OFMTech_NSFW.json (pre-fix), 0 on the
#     current OFMTech-NSFW/OFMTech_NSFW.json, in 23 ms.
#   * It names "SG '1. Canvas & Routing': outputs[4] 'MODEL' linkIds names
#     non-existent link(s) [1498]" — slot 4 MODEL, which is precisely what the
#     browser reports as "No output node found for id [647] slot [4] MODEL".
#     So this static check does point at the same defect, before a browser runs.
#
# What it is NOT, and do not let it be read as more:
#   * It checks LINK BOOKKEEPING only: link<->slot cross-references, subgraph IO
#     linkIds, and host-vs-definition slot agreement. It does NOT check
#     widgets_values desync on subgraph hosts, which CLAUDE.md calls the single
#     highest-value thing to audit in this file. "0 problems" is not "no defects".
#   * "inputs[i] has NO internal link (dead inside)" is warning-grade. A declared
#     but unused subgraph input is legal litegraph. On the red fixture it
#     coincided with a real defect; on another graph it could be a false positive.
#   * 0 problems here does NOT imply the browser will convert the graph. The
#     correlation is established on exactly one before/after pair. The browser
#     stage remains the authority; this is a fast pre-filter in front of it.
# ---------------------------------------------------------------------------
"""Full link-bookkeeping integrity check for a ComfyUI workflow JSON (0.4 schema, subgraphs)."""
import json, sys

def norm(l):
    if isinstance(l, dict): return l
    return {"id": l[0], "origin_id": l[1], "origin_slot": l[2], "target_id": l[3], "target_slot": l[4], "type": l[5]}

def check_graph(label, nodes, links, sg=None, problems=None):
    L = {l["id"]: l for l in map(norm, links)}
    N = {n["id"]: n for n in nodes}
    def P(msg): problems.append(f"{label}: {msg}")

    # 1. every link references existing endpoints
    for lid, l in L.items():
        o, t = l["origin_id"], l["target_id"]
        if o not in N and o not in (-10,):
            P(f"link {lid} origin_id {o} is not a node in this graph")
        if t not in N and t not in (-20,):
            P(f"link {lid} target_id {t} is not a node in this graph")
        if o == -10 and t == -20:
            P(f"link {lid} is a BARE IO PASSTHROUGH -10[{l['origin_slot']}] -> -20[{l['target_slot']}] ({l['type']}) -- unsupported by ExecutableNodeDTO")
        if o in N:
            outs = N[o].get("outputs") or []
            if l["origin_slot"] >= len(outs):
                P(f"link {lid} origin_slot {l['origin_slot']} out of range on node {o} ({len(outs)} outputs)")
            elif lid not in (outs[l["origin_slot"]].get("links") or []):
                P(f"link {lid} not listed in node {o}.outputs[{l['origin_slot']}].links")
        if t in N:
            ins = N[t].get("inputs") or []
            if l["target_slot"] >= len(ins):
                P(f"link {lid} target_slot {l['target_slot']} out of range on node {t} ({len(ins)} inputs)")
            elif ins[l["target_slot"]].get("link") != lid:
                P(f"link {lid} not set on node {t}.inputs[{l['target_slot']}].link (has {ins[l['target_slot']].get('link')})")

    # 2. every node slot reference points at an existing link
    for nid, n in N.items():
        for i, inp in enumerate(n.get("inputs") or []):
            lk = inp.get("link")
            if lk is not None and lk not in L:
                P(f"node {nid}.inputs[{i}] {inp.get('name')!r} link {lk} does not exist")
            elif lk is not None and L[lk]["target_id"] != nid:
                P(f"node {nid}.inputs[{i}] link {lk} targets node {L[lk]['target_id']}")
        for i, out in enumerate(n.get("outputs") or []):
            for lk in (out.get("links") or []):
                if lk not in L:
                    P(f"node {nid}.outputs[{i}] {out.get('name')!r} links contains {lk} which does not exist")
                elif L[lk]["origin_id"] != nid:
                    P(f"node {nid}.outputs[{i}] link {lk} originates at node {L[lk]['origin_id']}")

    # 3. subgraph IO slot linkIds bookkeeping
    if sg is not None:
        for kind, key, sid in (("inputs", "origin", -10), ("outputs", "target", -20)):
            for i, s in enumerate(sg.get(kind) or []):
                declared = list(s.get("linkIds") or [])
                actual = [l["id"] for l in L.values()
                          if l[f"{key}_id"] == sid and l[f"{key}_slot"] == i]
                ghost = [x for x in declared if x not in L]
                missing = [x for x in actual if x not in declared]
                if ghost:
                    P(f"{kind}[{i}] {s.get('name')!r} linkIds names non-existent link(s) {ghost}")
                if missing:
                    P(f"{kind}[{i}] {s.get('name')!r} linkIds OMITS real link(s) {missing} (declared={declared})")
                if not actual and kind == "outputs":
                    P(f"outputs[{i}] {s.get('name')!r} has NO internal link")
                if not actual and kind == "inputs":
                    P(f"inputs[{i}] {s.get('name')!r} has NO internal link (dead inside)")

def main(path):
    d = json.load(open(path))
    problems = []
    check_graph("ROOT", d["nodes"], d["links"], None, problems)
    defs = {s["id"]: s for s in d.get("definitions", {}).get("subgraphs", [])}
    for s in defs.values():
        check_graph(f"SG {s['name']!r}", s["nodes"], s["links"], s, problems)
    # host node slot counts must match definition
    for n in d["nodes"]:
        s = defs.get(n.get("type"))
        if not s: continue
        if len(n.get("inputs") or []) != len(s.get("inputs") or []):
            problems.append(f"HOST {n['id']}: inputs {len(n.get('inputs') or [])} != def {len(s.get('inputs') or [])}")
        if len(n.get("outputs") or []) != len(s.get("outputs") or []):
            problems.append(f"HOST {n['id']}: outputs {len(n.get('outputs') or [])} != def {len(s.get('outputs') or [])}")
        for i, (a, b) in enumerate(zip(n.get("inputs") or [], s.get("inputs") or [])):
            if a.get("name") != b.get("name") or a.get("type") != b.get("type"):
                problems.append(f"HOST {n['id']}: inputs[{i}] {a.get('name')}/{a.get('type')} != def {b.get('name')}/{b.get('type')}")
        for i, (a, b) in enumerate(zip(n.get("outputs") or [], s.get("outputs") or [])):
            if a.get("name") != b.get("name") or a.get("type") != b.get("type"):
                problems.append(f"HOST {n['id']}: outputs[{i}] {a.get('name')}/{a.get('type')} != def {b.get('name')}/{b.get('type')}")
    print(f"--- {path}: {len(problems)} problem(s) ---")
    for p in problems: print("  " + p)
    return 1 if problems else 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "/workspace/nsfw-fix/OFMTech-NSFW/OFMTech_NSFW.json"))
