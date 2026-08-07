#!/usr/bin/env python3
"""
Registration-count harness for ComfyUI_INSTARAW.

Imports the pack exactly the way ComfyUI would (as a package, with a ComfyUI
root on sys.path so `import nodes` / `folder_paths` / `comfy.*` resolve) and
prints the NODE_CLASS_MAPPINGS keys.

Deliberately does NOT boot a server and does NOT touch any running instance.

usage: count_nodes.py <comfy_root> <pack_parent_dir> <label> <out.json>
"""
import sys, os, json, traceback

comfy_root = os.path.abspath(sys.argv[1])
pack_parent = os.path.abspath(sys.argv[2])
label = sys.argv[3] if len(sys.argv) > 3 else "run"
out_path = os.path.abspath(sys.argv[4])

# ComfyUI's cli_args parses sys.argv at import time.
sys.argv = ["main.py", "--cpu"]

sys.path.insert(0, pack_parent)
sys.path.insert(0, comfy_root)
os.chdir(comfy_root)

result = {"label": label, "comfy_root": comfy_root, "pack_parent": pack_parent}

try:
    # Pin top-level `utils` to ComfyUI's own package before anything can bind
    # the name to comfy/utils.py, then import server the way main.py does.
    import utils.install_util  # noqa: F401
    import asyncio
    import server  # noqa: F401
    # The pack registers aiohttp routes at import time, exactly as it does under
    # a real ComfyUI boot; PromptServer.instance is created by main.py there.
    _loop = asyncio.new_event_loop()
    asyncio.set_event_loop(_loop)
    server.PromptServer(_loop)
    import nodes  # noqa: F401  (ComfyUI core; the pack does `import nodes` at top level)
except Exception:
    result["error"] = "failed to import ComfyUI core `nodes`"
    result["traceback"] = traceback.format_exc()
    open(out_path, "w").write(json.dumps(result, indent=2))
    sys.exit(2)

try:
    import ComfyUI_INSTARAW as pack
    ncm = pack.NODE_CLASS_MAPPINGS
    ndm = pack.NODE_DISPLAY_NAME_MAPPINGS
    result["import_ok"] = True
    result["pack_file"] = pack.__file__
    result["count"] = len(ncm)
    result["display_count"] = len(ndm)
    result["nodes"] = sorted(ncm.keys())
except Exception:
    result["import_ok"] = False
    result["count"] = 0
    result["nodes"] = []
    result["traceback"] = traceback.format_exc()

open(out_path, "w").write(json.dumps(result, indent=2))
print("WROTE", out_path, "count=", result.get("count"))
