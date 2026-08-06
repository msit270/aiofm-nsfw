#!/usr/bin/env python3
"""TRACK V graph builders.

Every base graph here came out of the REAL FRONTEND for a specific committed
revision of OFMTech-NSFW/OFMTech_NSFW.json (browser_harness --no-submit
--api-out). The workflow JSON is never edited; arms are in-memory mutations.

    prefix  = 8d166e0^  (56adda8)   620:114.denoise 0.80  620:110.device default
    mid     = 8d166e0                            0.35                   default
    head    = 7ce1539  (HEAD)                    0.35                   cpu

graph_diff proves prefix->mid differs only in 620:114.denoise and mid->head only
in 620:110.device (plus 419.inputs.rgthree_comparer, browser-session state that
norm() strips).
"""
import json, copy, os

G = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "graphs")
BASES = {"prefix": "api_prefix.json", "mid": "api_mid.json", "head": "api_head.json"}

CRASH46 = ("luna, a young woman with light freckles across her nose and cheeks, "
           "natural skin texture with visible pores, detailed eyes, "
           "photorealistic portrait photograph, 85mm lens")
PROOF32 = ("luna, 21 year old woman, freckles, green eyes, detailed skin texture, "
           "soft window light")
PLACEHOLDER16 = "TRIGGER, PROMPT FOR YOUR MODEL"

# the eyes stage, node ids as they appear in the API graph
EYES_DETAILER = "622:406"          # DetailerForEachDebug -- "the eyes stage ran"
EYES_STAGE = ["622:394", "622:398", "622:399", "622:400", "622:401", "622:402",
              "622:403", "622:404", "622:406", "622:407", "622:408", "622:410",
              "622:414", "622:415", "622:418", "622:424", "622:426", "622:431"]


def norm(g):
    """Strip 419.inputs.rgthree_comparer -- baked-in stale temp-image state on the
    Image Comparer node. It appears or not depending on which browser session did
    the conversion (tools/README documents it as a known shipped defect), and it
    has no effect on execution. Removing it makes the three conversions
    byte-comparable."""
    g = copy.deepcopy(g)
    if "419" in g:
        g["419"]["inputs"].pop("rgthree_comparer", None)
    return g


def load(variant):
    return norm(json.load(open(os.path.join(G, BASES[variant]))))


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


def set_loras(g):
    """The proof set requires both LoRAs. #618 is the SDXL side (absent from the
    probe graph, which starts from a frozen base); #116 is the Z-Image side and is
    in the face/mouth/eyes path."""
    if "618" in g:
        g["618"]["inputs"]["lora_01"] = "lunaskye.safetensors"
    if "116" in g:
        g["116"]["inputs"]["lora_01"] = "luna.safetensors"
    return g


def probe_graph(variant, text, overrides=None, base_image="trackA_base137.png"):
    """Track A's probe, rebuilt on a freshly converted graph.

    620:106 feeds only 620:114.positive, and everything up to 620:137 is therefore
    prompt-independent (CRASH.md 'Efficiency note'). So the base image is frozen
    and the arm drives exactly the failing path:
    620:114 -> 620:111 -> 620:165 -> 621:163 -> 622:431 -> 622:424 -> 622:407
    -> 622:403 -> ... -> 622:418 -> 505.
    """
    g = load(variant)
    set_loras(g)
    g["BASE"] = {"class_type": "LoadImage",
                 "inputs": {"image": base_image, "upload": "image"},
                 "_meta": {"title": "TRACK V frozen base (stands in for 620:137)"}}
    g["620:114"]["inputs"]["image"] = ["BASE", 0]
    g["620:111"]["inputs"]["reference"] = ["BASE", 0]
    g["620:106"]["inputs"]["text"] = text
    for nid, kv in (overrides or {}).items():
        g[nid]["inputs"].update(kv)
    g["TAP163"] = {"class_type": "SaveImage",
                   "inputs": {"images": ["621:163", 0],
                              "filename_prefix": "crashV/tap163"},
                   "_meta": {"title": "TRACK V tap: 621:163, the image handed to 622:424"}}
    return prune(g, ["505", "TAP163"])


def full_graph(variant, text, overrides=None, pick=0):
    """The whole 88-node shipping graph. Two mutations beyond 620:106.text:
      * both LoRAs, per the Phase 3 proof set;
      * 619:603 INSTARAW_ImageFilter pick_list = "0", so the deliberate mid-render
        human selector auto-picks image 0 instead of blocking for 600 s.
        image_filter.py:133 -- pick_list short-circuits send_and_wait entirely.
        R4's own crash arm used exactly this.
    """
    g = load(variant)
    set_loras(g)
    g["620:106"]["inputs"]["text"] = text
    g["619:603"]["inputs"]["pick_list"] = str(pick)
    for nid, kv in (overrides or {}).items():
        g[nid]["inputs"].update(kv)
    g["TAP163"] = {"class_type": "SaveImage",
                   "inputs": {"images": ["621:163", 0],
                              "filename_prefix": "crashV/ftap163"},
                   "_meta": {"title": "TRACK V tap: 621:163"}}
    return g
