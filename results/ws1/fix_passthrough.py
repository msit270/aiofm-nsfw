#!/usr/bin/env python3
"""
WS1 fix for `No output node found for id [647] slot [4] MODEL`.

Removes the three bare SubgraphInputNode -> SubgraphOutputNode passthrough links
(-10 -> -20) inside subgraph "1. Canvas & Routing", which litegraph's
ExecutableNodeDTO._resolveSubgraphOutput cannot resolve, by finishing the
interrupted cleanup that created them:

  * positive / negative are a laundered self-loop on host 619 - #599 "PURE
    POSITIVE" and #606 "PURE NEGATIVE" leave subgraph "2. Base Generator", cross
    to 647, and come straight back into #592 KSampler / #617 UltimateSDUpscale
    in the same subgraph.  Connected internally instead; the four IO slots and
    four root links that carried the detour are deleted.
  * MODEL is plain fan-out from root #618 Lora Loader Stack to 587.model and
    619.model.  Wired directly; 647's model input / MODEL output deleted.
  * vae (647 input 0) has no internal link at all - deleted.

Net semantic effect after flattening: none.  647 becomes a pure source
(EmptyLatentImage + denoise float) with zero inputs.

Usage: fix_passthrough.py <in.json> <out.json> [--control]
  --control  instead of removing the construct, insert three frontend-virtual
             `Reroute` nodes inside 647 between input and output, leaving all
             other wiring byte-identical.  Virtual nodes are folded out of the
             API graph, so the control's API graph is the API graph the shipped
             file would have produced.  Used to prove the fix is inert.
"""
import json, sys, copy

CANVAS = "9050d895-4e70-44f5-9c2b-57e2be7df0ec"   # "1. Canvas & Routing", host 647
BASE   = "3ff96466-2d66-45ea-8761-c9123bec3435"   # "2. Base Generator (SDXL)", host 619
H_CANVAS, H_BASE, H_HANDS, N_LORA = 647, 619, 587, 618


# ---------------------------------------------------------------- helpers
# Root links are serialised as arrays [id, origin_id, origin_slot, target_id,
# target_slot, type]; subgraph links as dicts.  Both forms are kept as-is so the
# git diff shows only real changes.
FIELDS = ("id", "origin_id", "origin_slot", "target_id", "target_slot", "type")

def lg(l, field):
    return l[field] if isinstance(l, dict) else l[FIELDS.index(field)]

def ls(l, field, value):
    if isinstance(l, dict): l[field] = value
    else: l[FIELDS.index(field)] = value

def sg(d, sid):
    return next(s for s in d["definitions"]["subgraphs"] if s["id"] == sid)

def node(nodes, nid):
    return next(n for n in nodes if n["id"] == nid)

def link(g, lid):
    return next(l for l in g["links"] if lg(l, "id") == lid)

def del_link(g, nodes, lid):
    """Delete a link and scrub every slot that references it."""
    l = link(g, lid)
    g["links"] = [x for x in g["links"] if lg(x, "id") != lid]
    for n in nodes:
        for o in (n.get("outputs") or []):
            if o.get("links"):
                o["links"] = [x for x in o["links"] if x != lid]
        for i in (n.get("inputs") or []):
            if i.get("link") == lid:
                i["link"] = None
    return l

def add_link(g, nodes, lid, oid, oslot, tid, tslot, typ):
    proto = g["links"][0] if g["links"] else {}
    rec = [lid, oid, oslot, tid, tslot, typ] if isinstance(proto, list) else \
          {"id": lid, "origin_id": oid, "origin_slot": oslot,
           "target_id": tid, "target_slot": tslot, "type": typ}
    g["links"].append(rec)
    if oid >= 0:
        o = node(nodes, oid)["outputs"][oslot]
        o.setdefault("links", [])
        if o["links"] is None:
            o["links"] = []
        o["links"].append(lid)
    if tid >= 0:
        node(nodes, tid)["inputs"][tslot]["link"] = lid

def drop_slots(definition, host, kind, remove):
    """Remove IO slots `remove` (indices) from a subgraph definition + its host
    node, and return the old->new index map."""
    old = definition[kind]
    keep = [i for i in range(len(old)) if i not in remove]
    definition[kind] = [old[i] for i in keep]
    host[kind] = [host[kind][i] for i in keep]
    return {o: n for n, o in enumerate(keep)}

def remap_internal(definition, imap_in, imap_out):
    for l in definition["links"]:
        if lg(l, "origin_id") == -10:
            ls(l, "origin_slot", imap_in[lg(l, "origin_slot")])
        if lg(l, "target_id") == -20:
            ls(l, "target_slot", imap_out[lg(l, "target_slot")])

def remap_root(d, host_id, imap_in, imap_out):
    for l in d["links"]:
        if lg(l, "target_id") == host_id:
            ls(l, "target_slot", imap_in[lg(l, "target_slot")])
        if lg(l, "origin_id") == host_id:
            ls(l, "origin_slot", imap_out[lg(l, "origin_slot")])

def rebuild_linkids(d):
    """Recompute every subgraph IO slot's linkIds from the actual link array.
    linkIds is authoritative at runtime (SubgraphSlotBase.getLinks iterates it
    and silently drops ids with no link object), so stale entries are real
    bookkeeping corruption, not cosmetics."""
    for s in d["definitions"]["subgraphs"]:
        for i, slot in enumerate(s["inputs"]):
            slot["linkIds"] = [lg(l, "id") for l in s["links"]
                               if lg(l, "origin_id") == -10 and lg(l, "origin_slot") == i]
        for i, slot in enumerate(s["outputs"]):
            slot["linkIds"] = [lg(l, "id") for l in s["links"]
                               if lg(l, "target_id") == -20 and lg(l, "target_slot") == i]


# ---------------------------------------------------------------- the fix
def apply_fix(d):
    canvas, base = sg(d, CANVAS), sg(d, BASE)
    h647, h619, h587 = (node(d["nodes"], x) for x in (H_CANVAS, H_BASE, H_HANDS))
    n618 = node(d["nodes"], N_LORA)

    # --- 1. inside "2. Base Generator": source positive/negative internally ---
    #     #599 PURE POSITIVE -> #592 KSampler.positive (1266), #617 USDU.positive (1267)
    #     #606 PURE NEGATIVE -> #592 KSampler.negative (1268), #617 USDU.negative (1269)
    for lid, origin in ((1266, 599), (1267, 599), (1268, 606), (1269, 606)):
        l = link(base, lid)
        assert lg(l, "origin_id") == -10, l
        ls(l, "origin_id", origin); ls(l, "origin_slot", 0)
    # #599 and #606 already fan out to #598/#600 inside the subgraph; append.
    node(base["nodes"], 599)["outputs"][0]["links"] += [1266, 1267]
    node(base["nodes"], 606)["outputs"][0]["links"] += [1268, 1269]
    # the two links that used to carry them out of the subgraph
    del_link(base, base["nodes"], 1275)   # 599 -> OUT[0] CONDITIONING
    del_link(base, base["nodes"], 1282)   # 606 -> OUT[2] CONDITIONING_1

    # --- 2. root links that formed the detour ---
    for lid in (1500, 1501, 1505, 1506):
        del_link(d, d["nodes"], lid)
    for lid in (1499, 1502, 1507, 1508):
        del_link(d, d["nodes"], lid)

    # --- 3. the three passthroughs themselves ---
    for lid in (1495, 1496, 1497):
        del_link(canvas, canvas["nodes"], lid)

    # --- 4. drop the now-unused IO slots ---
    b_in = drop_slots(base, h619, "inputs", {1, 2})       # positive, negative
    b_out = drop_slots(base, h619, "outputs", {0, 2})     # CONDITIONING, CONDITIONING_1
    remap_internal(base, b_in, b_out)
    remap_root(d, H_BASE, b_in, b_out)

    c_in = drop_slots(canvas, h647, "inputs", {0, 1, 2, 3})   # vae, positive, negative, model
    c_out = drop_slots(canvas, h647, "outputs", {2, 3, 4})    # positive, negative, MODEL
    remap_internal(canvas, c_in, c_out)
    remap_root(d, H_CANVAS, c_in, c_out)

    # --- 5. MODEL fan-out, direct from #618 ---
    nl = d["last_link_id"]
    add_link(d, d["nodes"], nl + 1, N_LORA, 0, H_HANDS, 4, "MODEL")
    add_link(d, d["nodes"], nl + 2, N_LORA, 0, H_BASE, b_in[8], "MODEL")
    d["last_link_id"] = nl + 2

    rebuild_linkids(d)
    return d


# ---------------------------------------------------------------- the control
def apply_control(d):
    """Insert a frontend-virtual `Reroute` for each passthrough. Nothing else changes."""
    canvas = sg(d, CANVAS)
    nl = d["last_link_id"]
    nid = canvas["state"]["lastNodeId"]
    y = 6200.0
    for (lid, in_slot, out_slot, typ) in ((1495, 1, 2, "CONDITIONING"),
                                          (1496, 2, 3, "CONDITIONING"),
                                          (1497, 3, 4, "MODEL")):
        canvas["links"] = [l for l in canvas["links"] if lg(l, "id") != lid]
        nid += 1
        a, b = nl + 1, nl + 2
        nl += 2
        canvas["nodes"].append({
            "id": nid, "type": "Reroute",
            "pos": [-4900.0, y], "size": [90, 26], "flags": {}, "order": 0, "mode": 0,
            "inputs": [{"name": "", "type": typ, "link": a}],
            "outputs": [{"name": "", "type": typ, "slot_index": 0, "links": [b]}],
            "properties": {"showOutputText": False, "horizontal": False},
        })
        y += 60
        canvas["links"].append({"id": a, "origin_id": -10, "origin_slot": in_slot,
                                "target_id": nid, "target_slot": 0, "type": typ})
        canvas["links"].append({"id": b, "origin_id": nid, "origin_slot": 0,
                                "target_id": -20, "target_slot": out_slot, "type": typ})
    canvas["state"]["lastNodeId"] = nid
    canvas["state"]["lastLinkId"] = nl
    d["last_link_id"] = max(d["last_link_id"], nl)
    rebuild_linkids(d)
    return d


if __name__ == "__main__":
    src, dst = sys.argv[1], sys.argv[2]
    d = json.load(open(src))
    d = apply_control(copy.deepcopy(d)) if "--control" in sys.argv else apply_fix(d)
    with open(dst, "w") as f:
        json.dump(d, f, indent=2, ensure_ascii=False)
    print(f"wrote {dst}")
