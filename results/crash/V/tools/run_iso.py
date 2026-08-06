import sys
sys.path.insert(0, "/workspace/nsfw-fix/results/crash/V/tools")
import v_drive, v_mk
ARMS = [
    ("V_ISO_d035_cpu_a",  "head",   {}, "denoise 0.35 + device cpu: the shipping artifact."),
    ("V_ISO_d080_cpu_a",  "prefix", {"620:110": {"device": "cpu"}}, "denoise 0.80 + device cpu: the 4th cell of the 2x2."),
    ("V_ISO_d035_gpu_b",  "mid",    {}, "repeat: denoise 0.35 + device default (the isolating control)."),
    ("V_ISO_d035_cpu_b",  "head",   {}, "repeat: the shipping artifact."),
    ("V_ISO_d080_gpu_b",  "prefix", {}, "repeat: the pre-fix positive control, interleaved."),
]
v_drive.run_set([(n, 46, note, {"variant": v, "text": v_mk.CRASH46, "overrides": ov})
                 for n, v, ov, note in ARMS], v_mk.probe_graph)
