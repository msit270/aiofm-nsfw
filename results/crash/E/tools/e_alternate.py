#!/usr/bin/env python3
"""E3b -- the alternation test for the CPU-encoder result, on :18188.

`E18_cpuclip_crash` flipped against expectation (it did NOT crash), so per the
brief's rule it gets re-run, and it gets re-run *interleaved* with the arm it is
supposed to differ from, on a server whose health is attested at both ends.

Sequence: GPU-clip crash (expect ERROR) -> CPU-clip crash (expect success)
          -> GPU-clip crash (expect ERROR) -> CPU-clip crash (expect success)

Exactly one widget differs between the two graphs: 620:110.device.
"""
import sys, os
os.environ.setdefault("E_SERVER", "127.0.0.1:18188")
os.environ.setdefault("E_OUTDIR", "/workspace/ComfyUI/output")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import e_drive, mk, strings

CPU = {"620:110": {"device": "cpu"}}

ARMS = [
    ("E18_alt1_gpuclip_crash", None, "GPU encoder (shipped). Expect ERROR 622:403."),
    ("E18_alt2_cpuclip_crash", CPU, "CPU encoder. Expect success."),
    ("E18_alt3_gpuclip_crash", None, "GPU encoder again. Expect ERROR 622:403."),
    ("E18_alt4_cpuclip_crash", CPU, "CPU encoder again. Expect success."),
]

if __name__ == "__main__":
    for name, ov, note in ARMS:
        g = mk.probe_graph(strings.CRASH, "trackA_base137.png", overrides=ov)
        e_drive.run_arm(name, g, note=note)
