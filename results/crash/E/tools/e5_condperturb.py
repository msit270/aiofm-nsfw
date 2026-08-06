#!/usr/bin/env python3
"""E5 -- does a pure ROUNDING-LEVEL perturbation of the conditioning cure the
crash, with everything else (encoder on cuda:0, memory timeline, shapes) held?

`E18_alt*` cured the crash by moving the encoder to the CPU, but that arm changes
two things at once: the conditioning values (E4: max|d| 0.0059 on a tensor whose
absmax is 13753, i.e. ~4e-7 relative -- pure fp rounding) AND the memory timeline
(the 7.7 GB encoder no longer sits in VRAM while the face pass samples).

This isolates the first. A `ConditioningAverage` is spliced between `620:106` and
`620:114.positive` with BOTH of its inputs taken from `620:106`:

    nodes.py:125   tw = torch.mul(t1, s) + torch.mul(t0, 1.0 - s)

  s = 1.00 -> t1*1 + t0*0 == t1 exactly. A true no-op; proves the extra node is
              inert and the arm still crashes.
  s = 0.70 -> 0.7a + 0.3a, which is a +/- 1 ulp away from a. Same shape, same
              device, same encoder, same load order.

  s=0.70 crashes -> a rounding perturbation does NOT cure it, so the CPU-encoder
                    cure is the memory timeline, not the values.
  s=0.70 clean   -> the face pass is knife-edge on the last bits of the
                    conditioning.
"""
import sys, os, copy
os.environ.setdefault("E_SERVER", "127.0.0.1:18188")
os.environ.setdefault("E_OUTDIR", "/workspace/ComfyUI/output")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import e_drive, mk, strings


def perturb_graph(strength):
    g = mk.probe_graph(strings.CRASH, "trackA_base137.png")
    g["EAVG"] = {"class_type": "ConditioningAverage",
                 "inputs": {"conditioning_to": ["620:106", 0],
                            "conditioning_from": ["620:106", 0],
                            "conditioning_to_strength": strength},
                 "_meta": {"title": f"TRACK E: rounding perturbation s={strength}"}}
    g["620:114"]["inputs"]["positive"] = ["EAVG", 0]
    return g


ARMS = [
    ("E18_condavg_s100", 1.00, "no-op splice: t1*1 + t0*0 == t1 exactly. Expect ERROR."),
    ("E18_condavg_s070", 0.70, "1-ulp perturbation of the same conditioning."),
    ("E18_condavg_s100b", 1.00, "repeat of the no-op."),
    ("E18_condavg_s070b", 0.70, "repeat of the perturbation."),
]

if __name__ == "__main__":
    for name, s, note in ARMS:
        e_drive.run_arm(name, perturb_graph(s), note=note)
