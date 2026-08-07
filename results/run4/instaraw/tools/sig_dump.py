#!/usr/bin/env python3
"""
Dump a structural signature for every node class the pack registers, so that
BEFORE and AFTER can be compared field-by-field rather than by count alone.

Records, per node type: defining module + qualname, RETURN_TYPES, RETURN_NAMES,
FUNCTION, CATEGORY, OUTPUT_NODE, and the ordered input key names with their
declared type/spec, for required / optional / hidden.

No rendering, no hashing of output. Purely the registration surface.

usage: sig_dump.py <comfy_root> <pack_parent> <label> <out.json>
"""
import sys, os, json, traceback

sys.dont_write_bytecode = True

comfy_root = os.path.abspath(sys.argv[1])
pack_parent = os.path.abspath(sys.argv[2])
label = sys.argv[3]
out_path = os.path.abspath(sys.argv[4])

sys.argv = ["main.py", "--cpu"]
sys.path.insert(0, pack_parent)
sys.path.insert(0, comfy_root)
os.chdir(comfy_root)

import utils.install_util  # noqa: F401
import asyncio
import server  # noqa: F401
_loop = asyncio.new_event_loop()
asyncio.set_event_loop(_loop)
server.PromptServer(_loop)
import nodes  # noqa: F401

import ComfyUI_INSTARAW as pack


def spec_repr(v):
    """Stable, comparable rendering of one input spec."""
    try:
        return json.loads(json.dumps(v, default=repr, sort_keys=True))
    except Exception:
        return repr(v)


sigs = {}
for name, cls in pack.NODE_CLASS_MAPPINGS.items():
    entry = {
        "module": getattr(cls, "__module__", None),
        "qualname": getattr(cls, "__qualname__", None),
        "RETURN_TYPES": spec_repr(getattr(cls, "RETURN_TYPES", None)),
        "RETURN_NAMES": spec_repr(getattr(cls, "RETURN_NAMES", None)),
        "FUNCTION": getattr(cls, "FUNCTION", None),
        "CATEGORY": getattr(cls, "CATEGORY", None),
        "OUTPUT_NODE": getattr(cls, "OUTPUT_NODE", None),
        "INPUT_IS_LIST": getattr(cls, "INPUT_IS_LIST", None),
        "OUTPUT_IS_LIST": spec_repr(getattr(cls, "OUTPUT_IS_LIST", None)),
        "display_name": pack.NODE_DISPLAY_NAME_MAPPINGS.get(name),
    }
    try:
        it = cls.INPUT_TYPES()
        entry["INPUT_TYPES"] = {
            sec: [[k, spec_repr(v)] for k, v in (it.get(sec) or {}).items()]
            for sec in ("required", "optional", "hidden")
        }
    except Exception:
        entry["INPUT_TYPES"] = {"ERROR": traceback.format_exc().strip().splitlines()[-1]}
    sigs[name] = entry

out = {"label": label, "pack_parent": pack_parent, "count": len(sigs), "sigs": sigs}
open(out_path, "w").write(json.dumps(out, indent=1, sort_keys=True))
print("WROTE", out_path, "count=", len(sigs))
