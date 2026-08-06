#!/usr/bin/env python3
"""Track E driver -- Track A's validated harness, repointed at Track E's OWN
ComfyUI on 127.0.0.1:32000. Nothing here touches 18188, 28191 or 31910.

Reuses results/crash/A/tools/drive.py and mk.py verbatim (imported, not copied);
only the server address, the results root and the output directory are
overridden, because 32000 writes to /workspace/trackE/output.
"""
import sys, os
A_TOOLS = "/workspace/nsfw-fix/results/crash/A/tools"
sys.path.insert(0, A_TOOLS)
import drive, mk, strings  # noqa: E402

SERVER = os.environ.get("E_SERVER", "127.0.0.1:32000")
ROOT = "/workspace/nsfw-fix/results/crash/E"
OUTDIR = os.environ.get("E_OUTDIR", "/workspace/trackE/output")

drive.SERVER = SERVER
drive.ROOT = ROOT
drive.COMFY_OUT = OUTDIR
os.makedirs(os.path.join(ROOT, "arms"), exist_ok=True)
os.makedirs(os.path.join(ROOT, "history"), exist_ok=True)

run_arm = drive.run_arm
free = drive.free
