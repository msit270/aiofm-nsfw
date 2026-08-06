#!/usr/bin/env python3
"""Graph builders for Track A. The workflow JSON is FROZEN; everything here
mutates an in-memory copy of an already-submitted API graph."""
import json, copy, os

R4 = "/workspace/nsfw-fix/results/r4"
FILLED = os.path.join(R4, "R4_CF15_filled", "api_graph.json")       # shipping cf1.5 + LoRAs, crashed
PLACEHOLDER = os.path.join(R4, "R4_CF15_placeholder", "api_graph.json")  # same, clean

CRASH_STRING = ("luna, a young woman with light freckles across her nose and cheeks, "
                "natural skin texture with visible pores, detailed eyes, "
                "photorealistic portrait photograph, 85mm lens")
PLACEHOLDER_STRING = "TRIGGER, PROMPT FOR YOUR MODEL"


def load(which="filled"):
    return json.load(open(FILLED if which == "filled" else PLACEHOLDER))


def prune(graph, outputs):
    keep = set()

    def walk(nid):
        if nid in keep or nid not in graph:
            return
        keep.add(nid)
        for v in graph[nid]["inputs"].values():
            if isinstance(v, list) and len(v) == 2 and isinstance(v[0], str):
                walk(v[0])
    for o in outputs:
        walk(o)
    return {k: v for k, v in graph.items() if k in keep}


def base_graph():
    """Full pipeline truncated at 620:137 with a SaveImage tap.
    620:106 is NOT an ancestor of 620:137, so this render is prompt-independent."""
    g = copy.deepcopy(load("placeholder"))
    g["TAP137"] = {"class_type": "SaveImage",
                   "inputs": {"images": ["620:137", 0], "filename_prefix": "crashA/base137"},
                   "_meta": {"title": "TRACK A tap: 620:137 (input to the face pass)"}}
    return prune(g, ["TAP137"])


def probe_graph(text, base_image_filename, tap163=True):
    """Cheap probe: LoadImage(frozen base) -> 620:114 -> 620:111 -> 620:165
    -> 621:163 -> 622:431 -> 622:424 -> 622:407 -> 622:403 -> ... -> 505 SaveImage."""
    g = copy.deepcopy(load("filled"))
    g["BASE"] = {"class_type": "LoadImage",
                 "inputs": {"image": base_image_filename, "upload": "image"},
                 "_meta": {"title": "TRACK A frozen base (was 620:137)"}}
    g["620:114"]["inputs"]["image"] = ["BASE", 0]
    g["620:111"]["inputs"]["reference"] = ["BASE", 0]
    g["620:106"]["inputs"]["text"] = text
    outs = ["505"]
    if tap163:
        g["TAP163"] = {"class_type": "SaveImage",
                       "inputs": {"images": ["621:163", 0],
                                  "filename_prefix": "crashA/tap163"},
                       "_meta": {"title": "TRACK A tap: 621:163 (image handed to 622:424)"}}
        outs.append("TAP163")
    return prune(g, outs)


def tap_only_graph(text, base_image_filename):
    """Probe truncated at 621:163 -- the exact image handed to the failing detector.
    Cannot reach 622:403, so it always saves."""
    g = copy.deepcopy(load("filled"))
    g["BASE"] = {"class_type": "LoadImage",
                 "inputs": {"image": base_image_filename, "upload": "image"},
                 "_meta": {"title": "TRACK A frozen base (was 620:137)"}}
    g["620:114"]["inputs"]["image"] = ["BASE", 0]
    g["620:111"]["inputs"]["reference"] = ["BASE", 0]
    g["620:106"]["inputs"]["text"] = text
    g["TAP163"] = {"class_type": "SaveImage",
                   "inputs": {"images": ["621:163", 0], "filename_prefix": "crashA/tap163"},
                   "_meta": {"title": "TRACK A tap: 621:163"}}
    g["TAP114"] = {"class_type": "SaveImage",
                   "inputs": {"images": ["620:114", 0], "filename_prefix": "crashA/tap114"},
                   "_meta": {"title": "TRACK A tap: 620:114 raw face-pass output"}}
    return prune(g, ["TAP163", "TAP114"])


def full_graph(text):
    """Unmodified shipping-arm graph, only 620:106.inputs.text changed."""
    g = copy.deepcopy(load("filled"))
    g["620:106"]["inputs"]["text"] = text
    return g
