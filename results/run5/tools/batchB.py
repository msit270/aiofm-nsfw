#!/usr/bin/env python3
"""Batch B — structure arms: Z-base splice, SDXL repairs, vendor pairing,
mouth threshold, first V9 look."""
import sys, time, json, copy
sys.path.insert(0, "/workspace/run5/tools")
from r5 import (boot, run_arm, pipeline_graph, zbase_splice, STD_TAPS,
                BALCONY, FACE_PROMPT, buyer_values)

boot()
B = "B"
TAPS_SPLICE = {k: v for k, v in STD_TAPS.items() if k != "T01_base591"}
TAPS_SPLICE["T00_zbase"] = ("ZB_dec", 0)

def go(arm, graph):
    t0 = time.time()
    try:
        ex, _ = run_arm(B, arm, graph)
        print(f"[{arm}] ok exec={ex:.1f}s wall={time.time()-t0:.1f}s", flush=True)
    except Exception as e:
        print(f"[{arm}] FAIL {e}", flush=True)

# 1) Z-Image as the base generator, SDXL detail chain unchanged
go("ZB1", zbase_splice(pipeline_graph(taps=TAPS_SPLICE)))

# 2) SDXL repair: TDD refine gets the character stack (610 on top of 618)
go("B_fix610", pipeline_graph(taps=STD_TAPS,
                              rewires={("619:610", "model"): ["618", 0],
                                       ("619:610", "clip"): ["618", 1]}))

# 3) SDXL repair: base prompt trigger + hair as the LoRA renders it
bv = buyer_values()
pb = json.loads(bv["483"]["inputs"]["prompt_batch_data"])
pb[0]["positive_prompt"] = ("lunaskye, photorealistic full body photograph of a "
    "young woman with long straight blonde hair with dark roots and curtain "
    "bangs, standing on a hotel balcony at golden hour, wearing a black silk "
    "slip dress, natural skin texture with visible pores and freckles, shot on "
    "85mm, shallow depth of field")
go("B_fixprompt", pipeline_graph(taps=STD_TAPS,
                                 overrides={"483": {"prompt_batch_data": json.dumps(pb)}}))

# 4) both SDXL repairs together
go("B_fixboth", pipeline_graph(taps=STD_TAPS,
                               overrides={"483": {"prompt_batch_data": json.dumps(pb)}},
                               rewires={("619:610", "model"): ["618", 0],
                                        ("619:610", "clip"): ["618", 1]}))

# 5) vendor pairing on the face pass
go("B_rms_simple", pipeline_graph(taps=STD_TAPS,
                                  overrides={"620:114": {"sampler_name": "res_multistep",
                                                          "scheduler": "simple"}}))

# 6) mouth detector threshold on full-body
go("B_mouth05", pipeline_graph(taps=STD_TAPS,
                               overrides={"620:165": {"bbox_threshold": 0.5}}))
go("B_mouth03", pipeline_graph(taps=STD_TAPS,
                               overrides={"620:165": {"bbox_threshold": 0.3}}))

# 7) face-pass denoise 0.85 (identity-rebuild direction, beyond A's 0.65)
go("B_den085", pipeline_graph(taps=STD_TAPS, overrides={"620:114": {"denoise": 0.85}}))

# 8) first V9 look: base checkpoint swap only
go("B_v9", pipeline_graph(taps=STD_TAPS,
                          overrides={"619:613": {"ckpt_name": "lustifyNSFWCheckpoint_zenithV9.safetensors"}}))
print("batch B done", flush=True)
