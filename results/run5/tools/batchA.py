#!/usr/bin/env python3
"""Batch A — architecture: references + tapped baseline + face-pass arms.
Sequential on the persistent 19188 server. Prints one line per arm."""
import sys, time
sys.path.insert(0, "/workspace/run5/tools")
from r5 import (boot, run_arm, pipeline_graph, zit_simple, sdxl_simple,
                STD_TAPS, BALCONY, BALCONY_NEG, FACE_PROMPT)

boot()
B = "A"

def go(arm, graph):
    t0 = time.time()
    try:
        ex, _ = run_arm(B, arm, graph)
        print(f"[{arm}] ok exec={ex:.1f}s wall={time.time()-t0:.1f}s", flush=True)
    except Exception as e:
        print(f"[{arm}] FAIL {e}", flush=True)

# --- ZIT references (the reconstructed simple workflow) ---
go("zref_B_12345", zit_simple(BALCONY, 12345, arm="img"))
go("zref_B_777", zit_simple(BALCONY, 777, arm="img"))
go("zref_P_12345", zit_simple(FACE_PROMPT, 12345, arm="img"))
go("zref_P_777", zit_simple(FACE_PROMPT, 777, arm="img"))
go("zref_P_999", zit_simple(FACE_PROMPT, 999, arm="img"))
# sampler-identity probe: pipeline's face-pass sampler on the same seed
go("zref_P_12345_eak", zit_simple(FACE_PROMPT, 12345, sampler="euler_ancestral",
                                  scheduler="kl_optimal", arm="img"))
# no-LoRA control: what Z-Image thinks the prompt looks like without luna
go("zref_P_12345_nolora", zit_simple(FACE_PROMPT, 12345, lora=None, arm="img"))

# --- SDXL identity probe: LUSTIFY V7 + lunaskye, portrait ---
go("sxref_P_12345", sdxl_simple(FACE_PROMPT.replace("luna, ", "lunaskye, "), 12345, arm="img"))
go("sxref_P_12345_luna_trigger", sdxl_simple(FACE_PROMPT, 12345, arm="img"))
go("sxref_P_12345_nolora", sdxl_simple(FACE_PROMPT, 12345, lora=None, arm="img"))

# --- pipeline: tapped baseline + arms ---
go("A0", pipeline_graph(taps=STD_TAPS))
# skip the SDXL face pass (619:596 -> 619:597 directly)
go("A_skip607", pipeline_graph(taps=STD_TAPS,
                               rewires={("619:597", "pixels"): ["619:596", 0]}))
# skip the Z-Image face pass (620:111.image <- 620:137)
go("A_skip114", pipeline_graph(taps=STD_TAPS,
                               rewires={("620:111", "image"): ["620:137", 0]}))
# face-pass denoise up: the "rebuild the face toward luna" direction
go("A_den050", pipeline_graph(taps=STD_TAPS, overrides={"620:114": {"denoise": 0.50}}))
go("A_den065", pipeline_graph(taps=STD_TAPS, overrides={"620:114": {"denoise": 0.65}}))
# determinism guard
go("A0_repeat", pipeline_graph(taps=STD_TAPS))
print("batch A done", flush=True)
