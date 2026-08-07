#!/usr/bin/env python3
"""Apply the Eyes-stage no-face guard (notes/C-fix-design.md C1 + C1b).

C1  : ImpactIsNotEmptySEGS (660) + ImpactConditionalBranch (661) inside sg622,
      so "detector found no face" skips the whole eyes subtree lazily and passes
      the mouth-stage image through instead of crashing at 622:403.
C1b : PreviewAny (662) on the boolean, so the skip is VISIBLE — in the UI and in
      /history outputs — rather than silent. A fired guard is a failure report,
      not a pass.

usage: apply_guard.py <in.json> <out.json>

Refuses to patch anything but the exact shipping shape (asserts below).
Byte-format-matched to the shipping file: json.dump(indent=2, ensure_ascii=False),
no trailing newline.
"""
import json, sys, collections

SG = "f3ba7c90-fce5-4154-9cb0-7a1de52da0fe"
N_BOOL, N_BRANCH, N_WARN = 660, 661, 662
L_SEGS, L_COND, L_TT, L_FF, L_WARN = 1520, 1521, 1522, 1523, 1524


def main(src, dst):
    with open(src, "r", encoding="utf-8") as fh:
        d = json.load(fh, object_pairs_hook=collections.OrderedDict)

    sg = next(s for s in d["definitions"]["subgraphs"] if s["id"] == SG)
    nodes = {n["id"]: n for n in sg["nodes"]}

    # refuse to patch anything but the exact shipping shape
    assert nodes[424]["type"] == "BboxDetectorSEGS"
    assert nodes[418]["type"] == "ImageCompositeMasked"
    assert nodes[431]["type"] == "INSTARAW_ImageListFromBatch"
    assert nodes[418]["outputs"][0]["links"] == [764, 773, 774, 775]
    assert nodes[424]["outputs"][0]["links"] == [791]
    assert 660 not in nodes and 661 not in nodes and 662 not in nodes
    assert sg["outputs"][0]["linkIds"] == [764, 773, 774, 775]

    nodes[424]["outputs"][0]["links"] = [791, L_SEGS]
    nodes[418]["outputs"][0]["links"] = [L_TT]
    nodes[431]["outputs"][0]["links"] = [793, 796, 797, 798, 799, L_FF]

    for l in sg["links"]:
        if l["id"] in (764, 773, 774, 775):
            assert l["origin_id"] == 418 and l["target_id"] == -20
            l["origin_id"] = N_BRANCH

    sg["links"] += [
        {"id": L_SEGS, "origin_id": 424,     "origin_slot": 0, "target_id": N_BOOL,   "target_slot": 0, "type": "SEGS"},
        {"id": L_COND, "origin_id": N_BOOL,  "origin_slot": 0, "target_id": N_BRANCH, "target_slot": 0, "type": "BOOLEAN"},
        {"id": L_TT,   "origin_id": 418,     "origin_slot": 0, "target_id": N_BRANCH, "target_slot": 1, "type": "IMAGE"},
        {"id": L_FF,   "origin_id": 431,     "origin_slot": 0, "target_id": N_BRANCH, "target_slot": 2, "type": "IMAGE"},
        {"id": L_WARN, "origin_id": N_BOOL,  "origin_slot": 0, "target_id": N_WARN,   "target_slot": 0, "type": "BOOLEAN"},
    ]

    UE = {"widget_ue_connectable": {}, "input_ue_unconnectable": {}, "version": "7.4.1"}

    sg["nodes"].append(collections.OrderedDict([
        ("id", N_BOOL), ("type", "ImpactIsNotEmptySEGS"),
        ("pos", [5088.0, 5560.0]), ("size", [270, 26]),
        ("flags", {"collapsed": True}), ("order", 21), ("mode", 0),
        ("inputs",  [{"localized_name": "segs", "name": "segs", "type": "SEGS", "link": L_SEGS}]),
        ("outputs", [{"localized_name": "BOOLEAN", "name": "BOOLEAN", "type": "BOOLEAN", "links": [L_COND, L_WARN]}]),
        ("properties", collections.OrderedDict([
            ("cnr_id", "comfyui-impact-pack"), ("ver", "8.25.1"),
            ("Node name for S&R", "ImpactIsNotEmptySEGS"), ("ue_properties", UE)])),
        ("widgets_values", []), ("title", "face found?"),
    ]))

    sg["nodes"].append(collections.OrderedDict([
        ("id", N_BRANCH), ("type", "ImpactConditionalBranch"),
        ("pos", [5480.0, 5667.0]), ("size", [270, 66]),
        ("flags", {}), ("order", 22), ("mode", 0),
        ("inputs", [
            {"localized_name": "cond",     "name": "cond",     "type": "BOOLEAN", "link": L_COND},
            {"localized_name": "tt_value", "name": "tt_value", "type": "*",       "link": L_TT},
            {"localized_name": "ff_value", "name": "ff_value", "type": "*",       "link": L_FF},
        ]),
        ("outputs", [{"localized_name": "*", "name": "*", "type": "*",
                      "links": [764, 773, 774, 775]}]),
        ("properties", collections.OrderedDict([
            ("cnr_id", "comfyui-impact-pack"), ("ver", "8.25.1"),
            ("Node name for S&R", "ImpactConditionalBranch"), ("ue_properties", UE)])),
        ("widgets_values", []), ("title", "eyes pass, or pass through if no face"),
    ]))

    sg["nodes"].append(collections.OrderedDict([
        ("id", N_WARN), ("type", "PreviewAny"),
        ("pos", [5480.0, 5790.0]), ("size", [420.0, 100.0]),
        ("flags", {}), ("order", 23), ("mode", 0),
        ("inputs", [{"name": "source", "type": "*", "link": L_WARN}]),
        ("outputs", []),
        ("properties", collections.OrderedDict([
            ("cnr_id", "comfy-core"), ("ver", "0.3.66"),
            ("Node name for S&R", "PreviewAny"), ("ue_properties", UE)])),
        ("widgets_values", [None, None, None]),
        ("color", "#653"), ("bgcolor", "#764"),
        ("title", "eyes ran? False = no face found, eye detail SKIPPED"),
    ]))

    sg["state"]["lastNodeId"] = max(sg["state"]["lastNodeId"], N_WARN)
    sg["state"]["lastLinkId"] = max(sg["state"]["lastLinkId"], L_WARN)
    d["last_node_id"] = max(d["last_node_id"], N_WARN)
    d["last_link_id"] = max(d["last_link_id"], L_WARN)

    # shipping file has NO trailing newline; match it so the diff is minimal
    with open(dst, "w", encoding="utf-8") as fh:
        json.dump(d, fh, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
