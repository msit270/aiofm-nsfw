#!/usr/bin/env python3
"""E3 -- on the ONE instance that reproduces (:18188), move the text encoder off
the GPU and see whether the crash survives.

`620:110 CLIPLoader` has a `device` widget; setting it to "cpu" makes
`CLIPLoader.load_clip` pass `model_options["load_device"] = ["offload_device"] =
torch.device("cpu")` (nodes.py:995-996), so the Qwen3-4B encoder runs on CPU
instead of on cuda:0 in float16. Exactly one widget differs from the crashing arm.

  crash survives   -> the encoder's GPU/fp16 numerics are NOT the mechanism
  crash disappears -> they are
"""
import sys, os
os.environ.setdefault("E_SERVER", "127.0.0.1:18188")
os.environ.setdefault("E_OUTDIR", "/workspace/ComfyUI/output")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import e_drive, mk, strings

ARMS = [
    ("E18_placeholder_ctl", strings.PLACEHOLDER, None,
     "18188 control: shipped placeholder, unmodified probe graph."),
    ("E18_cpuclip_crash", strings.CRASH, {"620:110": {"device": "cpu"}},
     "18188: crash string, 620:110 CLIPLoader device=cpu. One widget differs from the crashing arm."),
    ("E18_cpuclip_placeholder", strings.PLACEHOLDER, {"620:110": {"device": "cpu"}},
     "18188: its control."),
]

if __name__ == "__main__":
    for name, text, ov, note in ARMS:
        g = mk.probe_graph(text, "trackA_base137.png", overrides=ov)
        e_drive.run_arm(name, g, note=note)
