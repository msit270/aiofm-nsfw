#!/usr/bin/env python3
"""Batch H — agent B: mouth stage deletion, before/after on FB/PT/CU
plus an OPEN-MOUTH close-up (the composition class where a mouth pass
should earn its keep; none of the three standard comps has one)."""
import sys, time
import numpy as np
from PIL import Image
sys.path.insert(0, "/workspace/run5/tools")
from r5 import boot, run_arm, zit_simple, BALCONY, FACE_PROMPT
from candidates import photo_config, ZTAPS

boot()

def go(arm, graph):
    t0 = time.time()
    try:
        ex, _ = run_arm("H", arm, graph)
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
OM = ("close-up portrait photograph of a young woman laughing with her mouth "
      "open, visible teeth, direct eye contact, soft window light, natural "
      "skin texture with visible pores, shot on 85mm f1.8")

MOUTH_NODES = ["620:165", "621:163", "621:160", "621:161", "621:166",
               "621:167", "620:648"]

def no_mouth(prompt):
    g = photo_config(prompt=prompt, taps=ZTAPS)
    # eyes stage takes the after-face colormatch directly; mouth chain dropped
    g["622:431"]["inputs"]["images"] = ["620:111", 0]
    for n in MOUTH_NODES:
        g.pop(n, None)
    # drop the now-dangling mouth tap
    g.pop("TAP_T12_mouth163", None)
    return g

go("canaryH", zit_simple(FACE_PROMPT, 12345, arm="img"))
a = np.asarray(Image.open("/workspace/run5/output/A/zref_P_12345/img/img_00001_.png"))
c = np.asarray(Image.open("/workspace/run5/output/H/canaryH/img/img_00001_.png"))
print(f"[canaryH] max_abs_diff={int(np.abs(a.astype(np.int16)-c.astype(np.int16)).max())}", flush=True)

# the open-mouth BEFORE (with mouth stage) — FB/PT/CU befores are batch G's PC1 arms
go("H_PC1_OM", photo_config(prompt=OM, taps=ZTAPS))
# AFTER arms (mouth stage deleted)
go("H_nomouth_FB", no_mouth(BALCONY))
go("H_nomouth_PT", no_mouth(PT))
go("H_nomouth_CU", no_mouth(CU))
go("H_nomouth_OM", no_mouth(OM))

go("canaryH2", zit_simple(FACE_PROMPT, 12345, arm="img"))
c2 = np.asarray(Image.open("/workspace/run5/output/H/canaryH2/img/img_00001_.png"))
print(f"[canaryH2] max_abs_diff={int(np.abs(a.astype(np.int16)-c2.astype(np.int16)).max())}", flush=True)
print("batch H done", flush=True)
