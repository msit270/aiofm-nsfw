#!/usr/bin/env python3
"""E7 -- is the CPU-encoder cure about WHO COMPUTED #106's conditioning, or about
the GPU encoder being resident/executed at all?

`620:110.device = cpu` (E3b, E6) cures the crash 5/5. That arm moves *every*
prompt in the graph onto the CPU encoder, so the GPU copy of Qwen3-4B is never
loaded or run.

Here a SECOND `CLIPLoader` is added on the CPU and wired to `620:106` only.
`620:105`, `621:166`, `621:167`, `622:394` and `622:398` stay on the original
GPU `620:110`, so the 7.7 GB GPU encoder is still loaded and still executed.

  crashes -> the cure is about the GPU encoder being loaded/run, not about the
             source of #106's conditioning
  clean   -> #106's conditioning source is what matters, which would contradict
             E5 (a rounding perturbation of #106 did not cure it)
"""
import sys, os
os.environ.setdefault("E_SERVER", "127.0.0.1:18188")
os.environ.setdefault("E_OUTDIR", "/workspace/ComfyUI/output")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import e_drive, mk, strings


def split_graph(text):
    g = mk.probe_graph(text, "trackA_base137.png")
    g["ECPUCLIP"] = {"class_type": "CLIPLoader",
                     "inputs": {"clip_name": "qwen.safetensors", "type": "lumina2",
                                "device": "cpu"},
                     "_meta": {"title": "TRACK E: second encoder, CPU, for 620:106 only"}}
    g["620:106"]["inputs"]["clip"] = ["ECPUCLIP", 0]
    return g


ARMS = [
    ("E18_split_crash", strings.CRASH, "46-token crash string; #106 on a CPU encoder, everything else on the GPU one."),
    ("E18_split_crash_b", strings.CRASH, "repeat"),
]

if __name__ == "__main__":
    for name, text, note in ARMS:
        e_drive.run_arm(name, split_graph(text), note=note)
