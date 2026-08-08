#!/usr/bin/env python3
"""Batch M2 — re-proof of the FIXED pc_final: owner prompts must now drive
the base (three comps must differ), plus ship-neutral function proof."""
import sys, time, json
import numpy as np
from PIL import Image
sys.path.insert(0, "/workspace/run5/tools")
from r5 import boot, run_arm, zit_simple, BALCONY, FACE_PROMPT, buyer_values
from candidates import pc_final

boot()

def go(arm, graph):
    t0 = time.time()
    try:
        ex, _ = run_arm("M2", arm, graph)
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

go("canaryM2a", zit_simple(FACE_PROMPT, 12345, arm="img"))
a = np.asarray(Image.open("/workspace/run5/output/A/zref_P_12345/img/img_00001_.png"))
c = np.asarray(Image.open("/workspace/run5/output/M2/canaryM2a/img/img_00001_.png"))
print(f"[canary] max_abs_diff={int(np.abs(a.astype(np.int16)-c.astype(np.int16)).max())}", flush=True)

go("M2_ship_neutral", pc_final(pick_list="0"))

def owner(prompt):
    g = pc_final(pick_list="0")
    g["116"]["inputs"]["lora_01"] = "luna.safetensors"
    pb = json.loads(g["483"]["inputs"]["prompt_batch_data"])
    pb[0]["positive_prompt"] = prompt
    pb[0]["seed"] = 12345
    g["483"]["inputs"]["prompt_batch_data"] = json.dumps(pb)
    g["620:106"]["inputs"]["text"] = buyer_values()["620:106"]["inputs"]["text"]
    return g

go("M2_luna_FB", owner(BALCONY))
go("M2_luna_PT", owner(PT))
go("M2_luna_CU", owner(CU))

go("canaryM2b", zit_simple(FACE_PROMPT, 12345, arm="img"))
c2 = np.asarray(Image.open("/workspace/run5/output/M2/canaryM2b/img/img_00001_.png"))
print(f"[canary2] max_abs_diff={int(np.abs(a.astype(np.int16)-c2.astype(np.int16)).max())}", flush=True)
print("batch M2 done", flush=True)
