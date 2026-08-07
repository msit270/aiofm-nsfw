#!/usr/bin/env python3
"""Batch D — the two candidate configs on three compositions, plus the
LUNA-Z base-30 taste variant and ZIT references for the new compositions."""
import sys, time
sys.path.insert(0, "/workspace/run5/tools")
from r5 import boot, run_arm, zit_simple, pipeline_graph, STD_TAPS, BALCONY
from candidates import luna_z, sdxl_fixed, ZTAPS

boot()

PT = ("photorealistic portrait photograph of a young woman standing in soft "
      "window light, natural skin texture with visible pores, detailed eyes, "
      "detailed hands at her sides, looking at the camera, 85mm lens, shallow "
      "depth of field")
CU = ("close-up beauty photograph of a young woman, face and bare shoulders "
      "filling the frame, direct eye contact, soft window light, natural skin "
      "texture with visible pores and freckles, shot on 85mm f1.8")
PT_TRIG = "lunaskye, " + PT
CU_TRIG = "lunaskye, " + CU

def go(arm, graph):
    t0 = time.time()
    try:
        ex, _ = run_arm("D", arm, graph)
        print(f"[{arm}] ok exec={ex:.1f}s wall={time.time()-t0:.1f}s", flush=True)
    except Exception as e:
        print(f"[{arm}] FAIL {e}", flush=True)

# ZIT references for the two new compositions (likeness anchors per comp)
go("zref_PT_12345", zit_simple(PT.replace("a young woman", "luna, a young woman"), 12345, arm="img"))
go("zref_CU_12345", zit_simple(CU.replace("a young woman", "luna, a young woman"), 12345, arm="img"))

# candidates x compositions
go("D_lunaz_FB", luna_z())
go("D_sdxlfix_FB", sdxl_fixed())
go("D_lunaz_PT", luna_z(prompt=PT))
go("D_sdxlfix_PT", sdxl_fixed(prompt=PT_TRIG))
go("D_lunaz_CU", luna_z(prompt=CU))
go("D_sdxlfix_CU", sdxl_fixed(prompt=CU_TRIG))

# taste variant: freckle-rich 30-step cfg-2 Z base
go("D_lunaz30_FB", luna_z(base_steps=30, base_cfg=2.0))

# baseline on the new comps (A0 equivalent), for the sheets
import json
from r5 import buyer_values
for tag, prompt in (("PT", PT), ("CU", CU)):
    bv = buyer_values()
    pb = json.loads(bv["483"]["inputs"]["prompt_batch_data"])
    pb[0]["positive_prompt"] = prompt
    go(f"A0_{tag}", pipeline_graph(taps=STD_TAPS,
        overrides={"483": {"prompt_batch_data": json.dumps(pb)}}))

# canary close
import numpy as np
from PIL import Image
go("canary3_zref_P_12345", zit_simple(
    "luna, a young woman in her mid twenties with wavy auburn hair, warm hazel "
    "eyes, soft natural makeup, light freckles on her cheeks, gentle smile, "
    "photorealistic skin texture with visible pores, soft diffused studio light",
    12345, arm="img"))
a = np.asarray(Image.open("/workspace/run5/output/A/zref_P_12345/img/img_00001_.png"))
c = np.asarray(Image.open("/workspace/run5/output/D/canary3_zref_P_12345/img/img_00001_.png"))
print(f"[canary3] max_abs_diff={int(np.abs(a.astype(np.int16)-c.astype(np.int16)).max())}", flush=True)
print("batch D done", flush=True)
