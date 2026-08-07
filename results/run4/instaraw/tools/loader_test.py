#!/usr/bin/env python3
"""
Load the pack through ComfyUI's OWN custom-node loader (nodes.load_custom_node),
which is the code path a real boot uses and the one that swallows an exception
into a "Cannot import ..." warning and returns False -- the IMPORT FAILED / 0
nodes failure mode this task exists to avoid.

Reports the loader's boolean return, any warning it logged, and the INSTARAW
entries it actually installed into the global nodes.NODE_CLASS_MAPPINGS.

usage: loader_test.py <comfy_root> <pack_dir> <label> <out.json>
"""
import sys, os, json, asyncio, logging, io

sys.dont_write_bytecode = True

comfy_root = os.path.abspath(sys.argv[1])
pack_dir = os.path.abspath(sys.argv[2])
label = sys.argv[3]
out_path = os.path.abspath(sys.argv[4])

sys.argv = ["main.py", "--cpu"]
sys.path.insert(0, comfy_root)
os.chdir(comfy_root)

import utils.install_util  # noqa: F401
import server  # noqa: F401
_loop = asyncio.new_event_loop()
asyncio.set_event_loop(_loop)
server.PromptServer(_loop)
import nodes

# capture WARNING+ from the loader
buf = io.StringIO()
h = logging.StreamHandler(buf)
h.setLevel(logging.WARNING)
logging.getLogger().addHandler(h)
logging.getLogger().setLevel(logging.INFO)

before_keys = set(nodes.NODE_CLASS_MAPPINGS.keys())
ok = _loop.run_until_complete(nodes.load_custom_node(pack_dir))
after_keys = set(nodes.NODE_CLASS_MAPPINGS.keys())

logging.getLogger().removeHandler(h)
warn_text = buf.getvalue()

added = sorted(after_keys - before_keys)
out = {
    "label": label,
    "pack_dir": pack_dir,
    "load_custom_node_returned": ok,
    "nodes_installed": len(added),
    "instaraw_installed": len([n for n in added if "INSTARAW" in n or "Ideogram" in n]),
    "added": added,
    "loader_warnings": warn_text.splitlines(),
}
open(out_path, "w").write(json.dumps(out, indent=1))
print("WROTE", out_path)
print("load_custom_node returned:", ok, " nodes installed:", len(added))
print("loader warnings:", len(out["loader_warnings"]))
for line in out["loader_warnings"]:
    print("   WARN:", line)
