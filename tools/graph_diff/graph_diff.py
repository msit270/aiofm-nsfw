#!/usr/bin/env python3
"""
graph_diff — the sanctioned way to verify that a workflow change is inert.

WHY NOT HASH THE OUTPUT
-----------------------
Comparing rendered images (by hash or by PSNR) does not work on this pipeline.
Run-to-run noise sits around 48.7 dB, below one 8-bit level, so identical hashes
are a strong attractor rather than proof. CLAUDE.md and STATE.md record three
separate confident-and-wrong "reproducible" verdicts reached that way, the last
surviving five agreeing renders before a sixth disagreed.

WHAT THIS DOES INSTEAD
----------------------
Takes two API-format graphs, optionally constant-folds pure passthrough nodes,
and compares every node on every input. Zero differences proves the change is
inert without rendering anything.

WHAT "CONSTANT-FOLD" COVERS  (read this before trusting a result)
-----------------------------------------------------------------
Folding rewrites links that pass through a node whose output is, per that node's
own Python source, exactly one of its inputs. That is ALL it does. The fold table
below is small on purpose and every entry cites the source it was read from.

It DOES:
  * follow a link through a listed passthrough node to the real upstream producer,
    transitively, with cycle protection
  * drop the passthrough node itself once nothing references it
  * report every fold it performed

It DOES NOT:
  * evaluate arithmetic, string templating, wildcards or seeds
  * simulate execution or constant-propagate widget values into downstream nodes
  * understand any class_type absent from FOLD_TABLE — those are left alone and,
    if their name looks switch-like, reported as an explicit caveat
  * resolve bypass (mode 4) or mute (mode 2). API format has no mode field: the
    frontend already removed bypassed nodes and rewired their links before this
    tool ever sees the graph. If you need bypass semantics checked, diff the
    API graphs the browser actually POSTed — that is what browser_harness
    captures as api_graph.json.
  * prove anything about nodes whose behaviour depends on server state
    (file contents, RNG, wildcards, IS_CHANGED returning NaN)

So: "0 differences" means the two graphs submit the same work to the same nodes
with the same inputs. It does not mean two renders will be pixel-identical, and
it cannot mean that — see above.

EXIT CODES
  0  no differences
  1  differences found
  2  usage / parse error
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from typing import Any

# ---------------------------------------------------------------------------
# Fold table. Every entry must cite the source that proves the passthrough.
# ---------------------------------------------------------------------------

FIRST_LINK = "__FIRST_LINK__"  # marker: use whichever input holds the first link

FOLD_TABLE: dict[str, dict[str, Any]] = {
    # OFMTech-NSFW/ComfyUI_INSTARAW/nodes/logic_nodes/virtual_nodes.py
    #   def passthrough(self, boolean, invert_input, input_1=None, ... ):
    #       return (input_1, input_2, input_3, input_4)
    # The two BOOLEAN inputs are ignored by the function entirely; the bypass they
    # name is applied client-side by JS, never here. So output N is exactly input N.
    "INSTARAW_BooleanBypass": {
        "outputs": {0: "input_1", 1: "input_2", 2: "input_3", 3: "input_4"},
        "source": "ComfyUI_INSTARAW/nodes/logic_nodes/virtual_nodes.py :: INSTARAW_BooleanBypass.passthrough",
    },
    # Core / rgthree reroutes are pure wire. The frontend normally resolves these
    # before export, so this entry only matters for API graphs from other sources.
    "Reroute": {
        "outputs": {0: FIRST_LINK},
        "source": "ComfyUI core Reroute: single input forwarded to single output",
    },
    "Reroute (rgthree)": {
        "outputs": {0: FIRST_LINK},
        "source": "rgthree-comfy Reroute: single input forwarded to single output",
    },
}

# Names that look like they select between inputs. If one of these turns up and is
# not in FOLD_TABLE we say so loudly rather than quietly under-folding.
SWITCH_LIKE = re.compile(r"switch|branch|conditional|impactif|selector|multiplex|pick", re.I)


# ---------------------------------------------------------------------------
# Loading / normalising
# ---------------------------------------------------------------------------

def die(msg: str) -> "NoReturn":  # type: ignore[name-defined]
    """Usage / parse error. Exit 2, per the contract in the module docstring —
    sys.exit(str) would exit 1 and be indistinguishable from 'graphs differ'."""
    sys.stderr.write(f"graph_diff: {msg}\n")
    raise SystemExit(2)


def load_graph(path: str) -> dict[str, dict]:
    """Accept either a bare API graph or a full POST /prompt body."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError:
        die(f"no such file: {path}")
    except json.JSONDecodeError as exc:
        die(f"{path} is not valid JSON: {exc}")

    if isinstance(data, dict) and "prompt" in data and isinstance(data["prompt"], dict):
        data = data["prompt"]

    if not isinstance(data, dict):
        die(f"{path} is not an API-format graph (expected an object keyed by node id)")

    bad = [k for k, v in data.items() if not isinstance(v, dict) or "class_type" not in v]
    if bad:
        die(
            f"{path} does not look like an API-format graph: "
            f"{len(bad)} entr(y|ies) without a class_type, e.g. {bad[:3]}.\n"
            "  This tool takes API format (what the browser POSTs to /prompt), not the\n"
            "  UI/litegraph workflow file. browser_harness writes api_graph.json for you."
        )
    return data


def is_link(value: Any) -> bool:
    """API-format link: [node_id, output_slot]."""
    return (
        isinstance(value, list)
        and len(value) == 2
        and isinstance(value[0], (str, int))
        and isinstance(value[1], int)
        and not isinstance(value[1], bool)
    )


def normalise(graph: dict[str, dict], include_meta: bool) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for nid, node in graph.items():
        entry = {"class_type": node.get("class_type"), "inputs": dict(node.get("inputs") or {})}
        for k, v in entry["inputs"].items():
            if is_link(v):
                entry["inputs"][k] = [str(v[0]), v[1]]
        if include_meta:
            entry["_meta"] = node.get("_meta")
        out[str(nid)] = entry
    return out


def apply_renames(graph: dict[str, dict], renames: dict[str, str]) -> dict[str, dict]:
    """Explicit id remapping. Deliberately not a heuristic: matching is by id, and
    if ids moved you say so on the command line."""
    if not renames:
        return graph
    out: dict[str, dict] = {}
    for nid, node in graph.items():
        new_id = renames.get(nid, nid)
        inputs = {}
        for k, v in node["inputs"].items():
            inputs[k] = [renames.get(v[0], v[0]), v[1]] if is_link(v) else v
        entry = {"class_type": node["class_type"], "inputs": inputs}
        if "_meta" in node:
            entry["_meta"] = node["_meta"]
        out[new_id] = entry
    return out


# ---------------------------------------------------------------------------
# Constant folding
# ---------------------------------------------------------------------------

def _fold_source(graph: dict[str, dict], nid: str, slot: int):
    """If (nid, slot) is the output of a foldable passthrough, return the link it
    forwards, else None. Returns ('MISSING', None) when the passthrough has no
    link on that input (a genuinely dangling wire)."""
    node = graph.get(nid)
    if node is None:
        return None
    rule = FOLD_TABLE.get(node["class_type"])
    if rule is None:
        return None

    name = rule["outputs"].get(slot)
    if name is None:
        return None

    if name == FIRST_LINK:
        for value in node["inputs"].values():
            if is_link(value):
                return value
        return ("MISSING", None)

    value = node["inputs"].get(name)
    if is_link(value):
        return value
    return ("MISSING", None)


def fold(graph: dict[str, dict]) -> tuple[dict[str, dict], list[str], list[str]]:
    """Rewrite links through foldable passthroughs and drop the passthroughs.
    Returns (graph, fold_log, caveats)."""
    log: list[str] = []
    caveats: list[str] = []

    foldable = {nid for nid, n in graph.items() if n["class_type"] in FOLD_TABLE}
    for nid, node in graph.items():
        ct = node["class_type"]
        if ct not in FOLD_TABLE and SWITCH_LIKE.search(ct or ""):
            caveats.append(
                f"node {nid} is a {ct}: the name looks like it selects between inputs but it "
                f"is not in the fold table, so it was NOT folded. A change that replaces it "
                f"with a direct wire will show as a difference."
            )

    def resolve(link: list) -> tuple[Any, list[str]]:
        chain: list[str] = []
        nid, slot = link[0], link[1]
        seen: set[tuple[str, int]] = set()
        while True:
            src = _fold_source(graph, nid, slot)
            if src is None:
                return [nid, slot], chain
            if src[0] == "MISSING":
                chain.append(f"{nid}[{slot}]->(dangling)")
                return None, chain
            if (nid, slot) in seen:
                caveats.append(f"fold cycle detected at {nid}[{slot}]; stopped folding this link")
                return [nid, slot], chain
            seen.add((nid, slot))
            chain.append(f"{nid}[{slot}]")
            nid, slot = str(src[0]), src[1]

    for nid, node in graph.items():
        if nid in foldable:
            continue
        for key, value in list(node["inputs"].items()):
            if not is_link(value):
                continue
            new, chain = resolve(value)
            if not chain:
                continue
            if new is None:
                node["inputs"][key] = None
                log.append(f"{nid}.inputs.{key}: {value} -> None (through {' -> '.join(chain)}; passthrough input not connected)")
            else:
                node["inputs"][key] = new
                log.append(f"{nid}.inputs.{key}: {value} -> {new} (through {' -> '.join(chain)})")

    referenced: set[str] = set()
    for nid, node in graph.items():
        if nid in foldable:
            continue
        for value in node["inputs"].values():
            if is_link(value):
                referenced.add(value[0])

    dropped = []
    for nid in sorted(foldable):
        if nid not in referenced:
            ct = graph[nid]["class_type"]
            del graph[nid]
            dropped.append(f"{nid} ({ct})")
    if dropped:
        log.append(f"dropped {len(dropped)} folded passthrough node(s): {', '.join(dropped)}")
    still = sorted(foldable & referenced)
    if still:
        caveats.append(
            "passthrough node(s) kept because something still references them after folding "
            f"(usually an output-slot this table does not map): {', '.join(still)}"
        )
    return graph, log, caveats


# ---------------------------------------------------------------------------
# Diffing
# ---------------------------------------------------------------------------

def diff(a: dict[str, dict], b: dict[str, dict]) -> list[dict]:
    diffs: list[dict] = []
    a_ids, b_ids = set(a), set(b)

    for nid in sorted(a_ids - b_ids, key=str):
        diffs.append({"kind": "node_removed", "node": nid, "class_type": a[nid]["class_type"]})
    for nid in sorted(b_ids - a_ids, key=str):
        diffs.append({"kind": "node_added", "node": nid, "class_type": b[nid]["class_type"]})

    for nid in sorted(a_ids & b_ids, key=str):
        na, nb = a[nid], b[nid]
        if na["class_type"] != nb["class_type"]:
            diffs.append({"kind": "class_type_changed", "node": nid, "a": na["class_type"], "b": nb["class_type"]})
        ka, kb = set(na["inputs"]), set(nb["inputs"])
        for key in sorted(ka - kb):
            diffs.append({"kind": "input_removed", "node": nid, "class_type": na["class_type"],
                          "input": key, "a": na["inputs"][key]})
        for key in sorted(kb - ka):
            diffs.append({"kind": "input_added", "node": nid, "class_type": nb["class_type"],
                          "input": key, "b": nb["inputs"][key]})
        for key in sorted(ka & kb):
            va, vb = na["inputs"][key], nb["inputs"][key]
            if va != vb:
                diffs.append({"kind": "link_changed" if (is_link(va) or is_link(vb)) else "value_changed",
                              "node": nid, "class_type": na["class_type"], "input": key, "a": va, "b": vb})
        if "_meta" in na or "_meta" in nb:
            if na.get("_meta") != nb.get("_meta"):
                diffs.append({"kind": "meta_changed", "node": nid, "a": na.get("_meta"), "b": nb.get("_meta")})
    return diffs


def fmt(value: Any, width: int = 90) -> str:
    text = json.dumps(value, ensure_ascii=False, sort_keys=True)
    return text if len(text) <= width else text[: width - 3] + "..."


# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(
        prog="graph_diff",
        description="Constant-folded structural diff of two API-format ComfyUI graphs.",
        epilog="Exit 0 = identical (change is inert), 1 = differences, 2 = usage error.",
    )
    ap.add_argument("a", help="baseline API graph (or a POST /prompt body)")
    ap.add_argument("b", help="candidate API graph (or a POST /prompt body)")
    ap.add_argument("--no-fold", action="store_true", help="compare raw, no constant folding")
    ap.add_argument("--include-meta", action="store_true",
                    help="also compare _meta (node titles). Off by default: titles do not affect execution.")
    ap.add_argument("--rename", action="append", default=[], metavar="OLD=NEW",
                    help="explicitly map a node id in A to one in B (repeatable). Matching is by id; "
                         "this tool never guesses at renames.")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--quiet", action="store_true", help="only the verdict line")
    args = ap.parse_args()

    renames = {}
    for item in args.rename:
        if "=" not in item:
            die(f"--rename wants OLD=NEW, got {item!r}")
        old, new = item.split("=", 1)
        renames[old] = new

    ga = apply_renames(normalise(load_graph(args.a), args.include_meta), renames)
    gb = normalise(load_graph(args.b), args.include_meta)

    log_a: list[str] = []
    log_b: list[str] = []
    caveats: list[str] = []
    if not args.no_fold:
        ga, log_a, cav_a = fold(ga)
        gb, log_b, cav_b = fold(gb)
        seen: set[str] = set()
        caveats = [c for c in (cav_a + cav_b) if not (c in seen or seen.add(c))]

    diffs = diff(ga, gb)

    if args.json:
        json.dump({
            "a": args.a, "b": args.b,
            "folded": not args.no_fold,
            "folds_a": log_a, "folds_b": log_b,
            "caveats": caveats,
            "node_count_a": len(ga), "node_count_b": len(gb),
            "difference_count": len(diffs),
            "differences": diffs,
            "identical": not diffs,
        }, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 1 if diffs else 0

    out = sys.stdout.write
    if not args.quiet:
        out(f"graph_diff\n  A  {args.a}  ({len(ga)} nodes after normalisation)\n")
        out(f"  B  {args.b}  ({len(gb)} nodes after normalisation)\n")
        out(f"  folding {'OFF (--no-fold)' if args.no_fold else 'ON'}"
            f"   _meta {'compared' if args.include_meta else 'ignored'}\n")
        if renames:
            out(f"  renames applied to A: {renames}\n")
        out("\n")
        for label, log in (("A", log_a), ("B", log_b)):
            if log:
                out(f"folds applied to {label}: {len(log)}\n")
                for line in log:
                    out(f"    {line}\n")
                out("\n")
        if caveats:
            out(f"CAVEATS — things this diff did NOT fold or could not reason about: {len(caveats)}\n")
            for c in caveats:
                out(f"  ! {c}\n")
            out("\n")

    if not diffs:
        out("RESULT: IDENTICAL — 0 differences.\n")
        if not args.quiet:
            out("  Every node present in both, same class_type, same value on every input.\n")
            out("  The change is inert with respect to what gets submitted for execution.\n")
            if caveats:
                out("  NOTE: read the caveats above before reading this as unconditional.\n")
        return 0

    by_kind: dict[str, int] = {}
    for d in diffs:
        by_kind[d["kind"]] = by_kind.get(d["kind"], 0) + 1
    out(f"RESULT: DIFFERENT — {len(diffs)} difference(s): "
        + ", ".join(f"{k}={v}" for k, v in sorted(by_kind.items())) + "\n")
    if args.quiet:
        return 1
    out("\n")
    for d in diffs:
        kind = d["kind"]
        if kind in ("node_added", "node_removed"):
            out(f"  {kind:18s} node {d['node']}  ({d['class_type']})\n")
        elif kind == "class_type_changed":
            out(f"  {kind:18s} node {d['node']}:  {d['a']}  ->  {d['b']}\n")
        elif kind == "meta_changed":
            out(f"  {kind:18s} node {d['node']}:  {fmt(d['a'])}  ->  {fmt(d['b'])}\n")
        elif kind == "input_removed":
            out(f"  {kind:18s} {d['node']}.inputs.{d['input']}  ({d['class_type']})  was {fmt(d['a'])}\n")
        elif kind == "input_added":
            out(f"  {kind:18s} {d['node']}.inputs.{d['input']}  ({d['class_type']})  now {fmt(d['b'])}\n")
        else:
            out(f"  {kind:18s} {d['node']}.inputs.{d['input']}  ({d['class_type']})\n")
            out(f"  {'':18s}   A: {fmt(d['a'])}\n")
            out(f"  {'':18s}   B: {fmt(d['b'])}\n")
    return 1


if __name__ == "__main__":
    sys.exit(main())
