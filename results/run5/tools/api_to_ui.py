#!/usr/bin/env python3
"""API-format graph -> flat UI-format ComfyUI workflow.

Why flat: the shipped 7-subgraph UI file is the widgets_values-desync trap
zone. A flat graph has one widgets_values per node, derived from the server's
own /object_info widget order, and the browser-harness capture loop proves
the round-trip (UI -> frontend conversion -> API) equals the source graph.

Layout: topological columns left->right; interactive nodes (483 prompt,
116/618 LoRA stacks, 603 selector, 505 save) pinned to a front column with
a MarkdownNote header.

Usage: api_to_ui.py <api_graph.json> <out_ui.json> [title]
Needs the 19188 server up for /object_info.
"""
import json, sys, urllib.request
from collections import defaultdict, deque

SERVER = "http://127.0.0.1:19188"
SEEDY = {"seed", "noise_seed"}
ORIG_UI = "/workspace/nsfw-quality/OFMTech-NSFW/OFMTech_NSFW.json"

# These classes serialize JS-managed/hidden inputs positionally; object_info
# cannot tell us the order. Orders read from the shipped UI file + the api
# widget names of the same nodes.
SPECIAL_ORDER = {
    "INSTARAW_RealityPromptGenerator":
        ["gemini_api_key", "grok_api_key", "aspect_label", "prompt_batch_data"],
    "INSTARAW_ImageFilter":
        ["timeout", "ontimeout", "cache_behavior", "tip", "extra1", "extra2",
         "extra3", "pick_list_start", "pick_list", "video_frames",
         "node_identifier"],
}

def load_templates():
    w = json.load(open(ORIG_UI))
    nodes = list(w.get("nodes", []))
    for d in w.get("definitions", {}).get("subgraphs", []):
        nodes.extend(d.get("nodes", []))
    t = {}
    for n in nodes:
        t.setdefault(n["type"], n.get("widgets_values"))
    return t


def object_info():
    with urllib.request.urlopen(SERVER + "/object_info", timeout=60) as f:
        return json.load(f)


def widget_inputs(cls, oi):
    """Ordered widget-input names for a class (excluding link-typed), plus
    which get a control_after_generate companion."""
    info = oi[cls]["input"]
    ordered = []
    for section in ("required", "optional"):
        for name, spec in info.get(section, {}).items():
            t = spec[0] if isinstance(spec, list) else spec
            if isinstance(t, list):          # legacy enum list -> widget
                ordered.append(name)
            elif t in ("INT", "FLOAT", "STRING", "BOOLEAN", "COMBO"):
                ordered.append(name)         # COMBO = new-style enum widget
            # everything else (MODEL, CLIP, IMAGE, ...) is link-typed
    return ordered


def link_inputs(cls, oi):
    """Ordered link-input names (non-widget)."""
    info = oi[cls]["input"]
    out = []
    for section in ("required", "optional"):
        for name, spec in info.get(section, {}).items():
            t = spec[0] if isinstance(spec, list) else spec
            if isinstance(t, list) or t in ("INT", "FLOAT", "STRING", "BOOLEAN", "COMBO"):
                continue
            out.append((name, t))
    return out


# widget-typed inputs may ALSO be wired (widget-as-input). Track those.

def convert(api, title="run5 personal"):
    oi = object_info()
    templates = load_templates()
    ids = list(api.keys())
    id_map = {nid: i + 1 for i, nid in enumerate(ids)}   # UI wants int ids
    # topological depth for layout
    depth = {nid: 0 for nid in ids}
    for _ in range(len(ids)):
        changed = False
        for nid in ids:
            for v in api[nid]["inputs"].values():
                if isinstance(v, list) and v[0] in depth:
                    if depth[nid] < depth[v[0]] + 1:
                        depth[nid] = depth[v[0]] + 1
                        changed = True
        if not changed:
            break
    nodes, links = [], []
    link_id = 1
    col_y = defaultdict(int)
    for nid in ids:
        n = api[nid]
        cls = n["class_type"]
        if cls not in oi:
            raise SystemExit(f"class {cls} not in object_info")
        wnames = widget_inputs(cls, oi)
        if cls in SPECIAL_ORDER:
            wnames = SPECIAL_ORDER[cls]
        lnames = link_inputs(cls, oi)
        inputs_arr, widgets = [], []
        # JS-extra widget tail: when the shipped file serializes MORE widget
        # slots than object_info declares (control_after_generate, previewMode,
        # UI blobs), append the template's tail after the declared values.
        tail = []
        tpl = templates.get(cls)
        n_seedy = sum(1 for k in wnames if k in SEEDY)
        declared_len = len(wnames) + n_seedy
        if (cls not in SPECIAL_ORDER and tpl is not None
                and len(tpl) > declared_len):
            tail = tpl[declared_len:]
        # link-typed declared inputs
        for name, t in lnames:
            v = n["inputs"].get(name)
            inputs_arr.append({"name": name, "type": t, "link": None, "_v": v})
        # widget inputs: value or wired
        for name in wnames:
            v = n["inputs"].get(name)
            if isinstance(v, list):
                # widget-as-input (wired): input slot typed as DECLARED (a "*"
                # slot silently drops the link at conversion — proven on
                # ImpactConditionalBranch.cond, which fell back to false)
                spec = (oi[cls]["input"].get("required", {}).get(name)
                        or oi[cls]["input"].get("optional", {}).get(name))
                t0 = spec[0] if isinstance(spec, list) else spec
                declared_t = ("COMBO" if isinstance(t0, list) or t0 == "COMBO"
                              else t0)
                inputs_arr.append({"name": name, "type": declared_t,
                                   "link": None, "widget": {"name": name},
                                   "_v": v})
                dflt = 0
                if isinstance(spec, list) and len(spec) > 1 and isinstance(spec[1], dict):
                    dflt = spec[1].get("default", 0)
                elif isinstance(spec, list) and isinstance(spec[0], list):
                    dflt = spec[0][0] if spec[0] else ""
                widgets.append(dflt)
            else:
                widgets.append(v)
            if name in SEEDY:
                widgets.append("fixed")     # control_after_generate companion
        widgets.extend(tail)
        x = 60 + depth[nid] * 320
        y = 60 + col_y[depth[nid]] * 260
        col_y[depth[nid]] += 1
        outputs = []
        for i, t in enumerate(oi[cls].get("output", [])):
            outputs.append({"name": (oi[cls].get("output_name") or [str(t)])[i]
                            if i < len(oi[cls].get("output_name") or []) else str(t),
                            "type": t if isinstance(t, str) else "COMBO",
                            "links": [], "slot_index": i})
        nodes.append({"id": id_map[nid], "type": cls,
                      "pos": [x, y], "size": [280, 120],
                      "flags": {}, "order": depth[nid], "mode": 0,
                      "inputs": inputs_arr, "outputs": outputs,
                      "properties": {"Node name for S&R": cls},
                      "widgets_values": widgets,
                      "_api_id": nid})
    node_by_ui = {n["id"]: n for n in nodes}
    # links
    for n in nodes:
        for inp in n["inputs"]:
            v = inp.pop("_v", None)
            if isinstance(v, list):
                src_ui = id_map[v[0]]
                src_slot = v[1]
                lk = [link_id, src_ui, src_slot, n["id"],
                      n["inputs"].index(inp), inp["type"]]
                inp["link"] = link_id
                node_by_ui[src_ui]["outputs"][src_slot]["links"].append(link_id)
                links.append(lk)
                link_id += 1
    # note header
    nodes.append({"id": len(ids) + 1, "type": "MarkdownNote",
                  "pos": [60, -160], "size": [700, 180], "flags": {},
                  "order": 0, "mode": 0, "inputs": [], "outputs": [],
                  "properties": {},
                  "widgets_values": [f"# {title}\nFlat personal build. "
                                     "Prompt: INSTARAW_RealityPromptGenerator. "
                                     "LoRAs: the two Lora Loader Stack nodes. "
                                     "Face prompt: the CLIPTextEncode fed into the "
                                     "Z face detailer."],
                  })
    ui = {"id": "run5-personal", "revision": 0,
          "last_node_id": len(ids) + 1, "last_link_id": link_id - 1,
          "nodes": nodes, "links": links, "groups": [],
          "config": {}, "extra": {}, "version": 0.4}
    return ui


if __name__ == "__main__":
    api = json.load(open(sys.argv[1]))
    # strip tap SaveImage nodes (TAP_*) — measurement only
    api = {k: v for k, v in api.items() if not k.startswith("TAP_")}
    ui = convert(api, sys.argv[3] if len(sys.argv) > 3 else "run5 personal")
    json.dump(ui, open(sys.argv[2], "w"), indent=1)
    print("wrote", sys.argv[2], "nodes:", len(ui["nodes"]), "links:", len(ui["links"]))
