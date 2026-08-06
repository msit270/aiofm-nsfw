#!/usr/bin/env python3
"""TRACK P arm builder.

Builds three litegraph arms from the CURRENT committed workflow. Asserting:
every expected pre-state is checked before the patch, and the diff against the
source is confirmed to be exactly the intended widget.

NEVER writes OFMTech-NSFW/OFMTech_NSFW.json.
"""
import json, os, hashlib, copy

SRC = "/workspace/nsfw-fix/OFMTech-NSFW/OFMTech_NSFW.json"
OUT = "/tmp/claude-0/-workspace-nsfw-fix/47375d2b-87bd-4073-a1e2-67796f8c1345/scratchpad/P/arms"

raw = open(SRC, encoding="utf-8").read()
print("source        :", SRC)
print("source sha256 :", hashlib.sha256(raw.encode()).hexdigest())
print("source bytes  :", len(raw.encode()))
base = json.loads(raw)

def find(d, nid):
    hits = []
    def rec(o):
        if isinstance(o, dict):
            if o.get("id") == nid and "widgets_values" in o: hits.append(o)
            for v in o.values(): rec(v)
        elif isinstance(o, list):
            for v in o: rec(v)
    rec(d)
    assert len(hits) == 1, (nid, len(hits))
    return hits[0]

# --- verify the pre-state of the CURRENT file, quoted from it -----------------
n114 = find(base, 114); n110 = find(base, 110)
assert n114["type"] == "FaceDetailer", n114["type"]
assert n110["type"] == "CLIPLoader", n110["type"]
wv114 = n114["widgets_values"]; wv110 = n110["widgets_values"]
assert len(wv114) == 29, len(wv114)
assert wv114[5] == 8,     ("steps", wv114[5])
assert wv114[9] == 0.35,  ("denoise", wv114[9])
assert wv114[15] == 1.5,  ("bbox_crop_factor", wv114[15])
assert wv110 == ["qwen.safetensors", "lumina2", "cpu"], wv110
print("pre-state OK  : #114 steps=8 denoise=0.35 cf=1.5 | #110 device=cpu")

def emit(name, patch, desc):
    d = copy.deepcopy(base)
    patch(d)
    # confirm exactly the intended nodes moved, by full-tree comparison
    a = json.dumps(base, sort_keys=True, indent=1).splitlines()
    b = json.dumps(d,    sort_keys=True, indent=1).splitlines()
    import difflib
    delta = [l for l in difflib.unified_diff(a, b, n=0, lineterm="")
             if l.startswith(("+", "-")) and not l.startswith(("+++", "---"))]
    p = os.path.join(OUT, name + ".json")
    txt = json.dumps(d, indent=2, ensure_ascii=False)
    open(p, "w", encoding="utf-8").write(txt)
    print(f"\n{name}: {desc}")
    print(f"  changed lines vs source ({len(delta)}):")
    for l in delta: print("    ", l.strip())
    print(f"  -> {p}  sha256 {hashlib.sha256(txt.encode()).hexdigest()[:16]}…")

# P_D035 == the current file verbatim (shipping config). Emitted through the same
# code path as the others so any serialiser effect is common to all three arms.
emit("P_D035", lambda d: None,
     "SHIPPING: #114 denoise 0.35, #110 device cpu (current committed file)")

def p080(d):
    n = find(d, 114); assert n["widgets_values"][9] == 0.35
    n["widgets_values"][9] = 0.8
emit("P_D080", p080,
     "#114 denoise 0.35 -> 0.80 (the old shipping value). #110 stays cpu")

def pdef(d):
    n = find(d, 110); assert n["widgets_values"][2] == "cpu"
    n["widgets_values"][2] = "default"
emit("P_CLIPDEF", pdef,
     "#110 device cpu -> default (pre-7ce1539). #114 denoise stays 0.35")
