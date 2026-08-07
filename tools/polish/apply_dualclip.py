#!/usr/bin/env python3
"""DoD 5 resolution (if the dual-loader experiment wins): encode the FIXED eye
prompts on a GPU-resident CLIPLoader while 620:110 stays on cpu for the
buyer-variable face prompt.

Inside sg622: new node 665 CLIPLoader (same checkpoint/type as 620:110, device
"default"); links 1412 (->398.clip) and 1413 (->394.clip) re-originate from it;
the subgraph's clip input keeps feeding only 406's wildcard-only clip (1415).

usage: apply_dualclip.py <in.json> <out.json>
"""
import json, sys, collections

SG = "f3ba7c90-fce5-4154-9cb0-7a1de52da0fe"
SG5 = "d6db378b-b089-4636-91bb-6e0cf9a81503"
N_CLIP = 665


def main(src, dst):
    d = json.load(open(src, encoding="utf-8"), object_pairs_hook=collections.OrderedDict)
    sg5 = next(s for s in d["definitions"]["subgraphs"] if s["id"] == SG5)
    n110 = next(n for n in sg5["nodes"] if n["id"] == 110)
    assert n110["type"] == "CLIPLoader" and n110["widgets_values"][2] == "cpu", n110["widgets_values"]
    clip_name, clip_type = n110["widgets_values"][0], n110["widgets_values"][1]

    sg = next(s for s in d["definitions"]["subgraphs"] if s["id"] == SG)
    nodes = {n["id"]: n for n in sg["nodes"]}
    assert N_CLIP not in nodes
    links = {l["id"]: l for l in sg["links"]}
    for lid, target in ((1412, 398), (1413, 394)):
        assert links[lid]["origin_id"] == -10 and links[lid]["target_id"] == target, links[lid]
        links[lid]["origin_id"] = N_CLIP
        links[lid]["origin_slot"] = 0
    ci = next(i for i in sg["inputs"] if i["name"] == "clip")
    assert sorted(ci["linkIds"]) == [1412, 1413, 1415], ci["linkIds"]
    ci["linkIds"] = [1415]

    UE = {"widget_ue_connectable": {}, "input_ue_unconnectable": {}, "version": "7.4.1"}
    sg["nodes"].append(collections.OrderedDict([
        ("id", N_CLIP), ("type", "CLIPLoader"),
        ("pos", [4300.0, 5900.0]), ("size", [320.0, 110.0]),
        ("flags", {}), ("order", 0), ("mode", 0),
        ("inputs", [
            {"name": "clip_name", "type": "COMBO", "widget": {"name": "clip_name"}, "link": None},
            {"name": "type", "type": "COMBO", "widget": {"name": "type"}, "link": None},
            {"name": "device", "type": "COMBO", "widget": {"name": "device"}, "link": None},
        ]),
        ("outputs", [{"name": "CLIP", "type": "CLIP", "links": [1412, 1413]}]),
        ("properties", collections.OrderedDict([
            ("cnr_id", "comfy-core"), ("ver", "0.3.66"),
            ("Node name for S&R", "CLIPLoader"), ("ue_properties", UE)])),
        ("widgets_values", [clip_name, clip_type, "default"]),
        ("title", "GPU encoder for the FIXED eye prompts (620:110 stays cpu for the buyer's face prompt)"),
    ]))
    sg["state"]["lastNodeId"] = max(sg["state"]["lastNodeId"], N_CLIP)
    d["last_node_id"] = max(d["last_node_id"], N_CLIP)
    with open(dst, "w", encoding="utf-8") as fh:
        json.dump(d, fh, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
