#!/usr/bin/env python3
"""PROPOSALS.md P14: feather the eyes-stage composite (the face-box seam).

622:418 ImageCompositeMasked shipped with its optional mask input unwired, so
ComfyUI substitutes torch.ones_like(source) (comfy_extras/nodes_mask.py:24-25)
— a hard, unfeathered full-rectangle paste of the eye-detailed crop onto the
delivered image, landing exactly on the face box. 622:403 MaskBoundingBox+
already produces the crop-sized mask on an output nobody consumed.

This wires 403's MASK through a core FeatherMask (30 px per edge, against a
typical ~674x911 crop and a ~30-row transition measured on the #114 seam) into
418.mask. OUTPUT-CHANGING by design; ships with an A/B sheet.

usage: apply_feather.py <in.json> <out.json>
"""
import json, sys, collections

SG = "f3ba7c90-fce5-4154-9cb0-7a1de52da0fe"
N_FEATHER = 664
L_MASK, L_FMASK = 1525, 1526
FEATHER = 30


def main(src, dst):
    d = json.load(open(src, encoding="utf-8"), object_pairs_hook=collections.OrderedDict)
    sg = next(s for s in d["definitions"]["subgraphs"] if s["id"] == SG)
    nodes = {n["id"]: n for n in sg["nodes"]}
    assert nodes[403]["type"] == "MaskBoundingBox+"
    assert nodes[418]["type"] == "ImageCompositeMasked"
    assert nodes[403]["outputs"][0]["name"] == "MASK" and nodes[403]["outputs"][0]["links"] == []
    mask_in = next(i for i in nodes[418]["inputs"] if i["name"] == "mask")
    assert mask_in["link"] is None
    assert N_FEATHER not in nodes
    assert sg["state"]["lastNodeId"] == 662 and sg["state"]["lastLinkId"] == 1524

    nodes[403]["outputs"][0]["links"] = [L_MASK]
    mask_in["link"] = L_FMASK
    sg["links"] += [
        {"id": L_MASK,  "origin_id": 403, "origin_slot": 0, "target_id": N_FEATHER, "target_slot": 0, "type": "MASK"},
        {"id": L_FMASK, "origin_id": N_FEATHER, "origin_slot": 0, "target_id": 418, "target_slot": 2, "type": "MASK"},
    ]
    UE = {"widget_ue_connectable": {}, "input_ue_unconnectable": {}, "version": "7.4.1"}
    sg["nodes"].append(collections.OrderedDict([
        ("id", N_FEATHER), ("type", "FeatherMask"),
        ("pos", [5240.0, 5480.0]), ("size", [240.0, 150.0]),
        ("flags", {}), ("order", 24), ("mode", 0),
        ("inputs", [
            {"name": "mask", "type": "MASK", "link": L_MASK},
            {"name": "left", "type": "INT", "widget": {"name": "left"}, "link": None},
            {"name": "top", "type": "INT", "widget": {"name": "top"}, "link": None},
            {"name": "right", "type": "INT", "widget": {"name": "right"}, "link": None},
            {"name": "bottom", "type": "INT", "widget": {"name": "bottom"}, "link": None},
        ]),
        ("outputs", [{"name": "MASK", "type": "MASK", "links": [L_FMASK]}]),
        ("properties", collections.OrderedDict([
            ("cnr_id", "comfy-core"), ("ver", "0.3.66"),
            ("Node name for S&R", "FeatherMask"), ("ue_properties", UE)])),
        ("widgets_values", [FEATHER, FEATHER, FEATHER, FEATHER]),
        ("title", "feather the eyes composite (seam fix)"),
    ]))
    sg["state"]["lastNodeId"] = N_FEATHER
    sg["state"]["lastLinkId"] = L_FMASK
    d["last_node_id"] = max(d["last_node_id"], N_FEATHER)
    d["last_link_id"] = max(d["last_link_id"], L_FMASK)
    with open(dst, "w", encoding="utf-8") as fh:
        json.dump(d, fh, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
