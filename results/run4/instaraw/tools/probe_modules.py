#!/usr/bin/env python3
"""
Probe the importability of the four never-traced detection_bypass modules
(plus the encumbered ones), independently of the node registration path.

usage: probe_modules.py <comfy_root> <pack_parent> <label> <out.json>
"""
import sys, os, json, traceback, importlib

comfy_root = os.path.abspath(sys.argv[1])
pack_parent = os.path.abspath(sys.argv[2])
label = sys.argv[3]
out_path = os.path.abspath(sys.argv[4])

sys.argv = ["main.py", "--cpu"]
sys.path.insert(0, pack_parent)
sys.path.insert(0, comfy_root)
os.chdir(comfy_root)

# Same boot order as a real ComfyUI start: pin top-level `utils` to ComfyUI's
# own package and create PromptServer.instance before any custom node imports.
import utils.install_util  # noqa: F401
import asyncio
import server  # noqa: F401
_loop = asyncio.new_event_loop()
asyncio.set_event_loop(_loop)
server.PromptServer(_loop)

TARGETS = [
    "ComfyUI_INSTARAW.modules.detection_bypass.utils",
    "ComfyUI_INSTARAW.modules.detection_bypass.utils.unmarker_full",
    "ComfyUI_INSTARAW.modules.detection_bypass.utils.unmarker_losses",
    "ComfyUI_INSTARAW.modules.detection_bypass.utils.adaptive_filter",
    "ComfyUI_INSTARAW.modules.detection_bypass.utils.non_semantic_attack",
    "ComfyUI_INSTARAW.modules.detection_bypass.pipeline",
    "ComfyUI_INSTARAW.modules.detection_bypass.pipeline_v2",
    "ComfyUI_INSTARAW.modules.detection_bypass.processor",
    "ComfyUI_INSTARAW.modules.detection_bypass.camera_pipeline",
    "ComfyUI_INSTARAW.modules.neural_grain.net",
]

out = {"label": label, "results": {}}
for name in TARGETS:
    # fresh interpreter state is not available; import in-process is fine
    # because a failed import does not get cached as success.
    try:
        importlib.import_module(name)
        out["results"][name] = {"import": "OK"}
    except Exception as e:
        out["results"][name] = {
            "import": "FAIL",
            "exc": type(e).__name__,
            "msg": str(e),
            "last_frame": traceback.format_exc().strip().splitlines()[-3:],
        }

open(out_path, "w").write(json.dumps(out, indent=2))
print("WROTE", out_path)
for k, v in out["results"].items():
    print(f'{v["import"]:5s} {k}' + ("" if v["import"] == "OK" else f'   <- {v["exc"]}: {v["msg"]}'))
