#!/usr/bin/env python3
"""E6 -- does the CPU-encoder cure hold in the OTHER band, at 30 tokens?

Track A's map has two crashing regions: [30,32] and 44+. E3/E3b cured 46 tokens.
This checks 30, using Track A's own T-family string ("a woman's face" + k x " the")
so content is held constant, interleaved GPU / CPU.
"""
import sys, os
os.environ.setdefault("E_SERVER", "127.0.0.1:18188")
os.environ.setdefault("E_OUTDIR", "/workspace/ComfyUI/output")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import e_drive, mk

TOK30 = "a woman's face" + " the" * 18          # 30 tokens (Track A T_tok30)
CPU = {"620:110": {"device": "cpu"}}

ARMS = [
    ("E18_tok30_gpuclip", TOK30, None, "30-token band, GPU encoder. Expect ERROR (Track A: T_tok30 crashed)."),
    ("E18_tok30_cpuclip", TOK30, CPU, "30-token band, CPU encoder."),
    ("E18_tok30_gpuclip_b", TOK30, None, "repeat"),
    ("E18_tok30_cpuclip_b", TOK30, CPU, "repeat"),
]

if __name__ == "__main__":
    for name, text, ov, note in ARMS:
        g = mk.probe_graph(text, "trackA_base137.png", overrides=ov)
        e_drive.run_arm(name, g, note=note)
