#!/usr/bin/env python3
"""Batch F2 — re-render the intermittent black-frame failures, fresh server."""
import sys, time, json
sys.path.insert(0, "/workspace/run5/tools")
from r5 import boot, run_arm, zit_simple, pipeline_graph, STD_TAPS, buyer_values
from candidates import luna_z
boot()

def go(batch, arm, graph):
    t0 = time.time()
    try:
        ex, _ = run_arm(batch, arm, graph)
        print(f"[{arm}] ok exec={ex:.1f}s", flush=True)
    except Exception as e:
        print(f"[{arm}] FAIL {e}", flush=True)

PT = ("photorealistic portrait photograph of a young woman standing in soft "
      "window light, natural skin texture with visible pores, detailed eyes, "
      "detailed hands at her sides, looking at the camera, 85mm lens, shallow "
      "depth of field")
CU = ("close-up beauty photograph of a young woman, face and bare shoulders "
      "filling the frame, direct eye contact, soft window light, natural skin "
      "texture with visible pores and freckles, shot on 85mm f1.8")
go("D", "zref_PT_12345_rr", zit_simple(PT.replace("a young woman", "luna, a young woman"), 12345, arm="img"))
go("D", "zref_CU_12345_rr", zit_simple(CU.replace("a young woman", "luna, a young woman"), 12345, arm="img"))
go("D", "D_lunaz30_FB_rr", luna_z(base_steps=30, base_cfg=2.0))
bv = buyer_values()
pb = json.loads(bv["483"]["inputs"]["prompt_batch_data"])
pb[0]["positive_prompt"] = PT
go("D", "A0_PT_rr", pipeline_graph(taps=STD_TAPS,
   overrides={"483": {"prompt_batch_data": json.dumps(pb)}}))
print("batch F2 done", flush=True)
