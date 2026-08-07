#!/usr/bin/env python3
"""Batch G — the reconciliation: PC on three comps + den/sampler/hybrid tiles
+ negative-liveness proof. Fresh server, canary-bracketed, black-swept."""
import sys, time, json
import numpy as np
from PIL import Image
sys.path.insert(0, "/workspace/run5/tools")
from r5 import boot, run_arm, zit_simple, STD_TAPS, BALCONY, BALCONY_NEG, FACE_PROMPT
from candidates import photo_config, hybrid_zusdu, ZTAPS

boot()

def go(arm, graph):
    t0 = time.time()
    try:
        ex, _ = run_arm("G", arm, graph)
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

go("canaryG", zit_simple(FACE_PROMPT, 12345, arm="img"))
a = np.asarray(Image.open("/workspace/run5/output/A/zref_P_12345/img/img_00001_.png"))
c = np.asarray(Image.open("/workspace/run5/output/G/canaryG/img/img_00001_.png"))
print(f"[canaryG] max_abs_diff={int(np.abs(a.astype(np.int16)-c.astype(np.int16)).max())}", flush=True)

# PC primary, three compositions
go("G_PC1_FB", photo_config(taps=ZTAPS))
go("G_PC1_PT", photo_config(prompt=PT, taps=ZTAPS))
go("G_PC1_CU", photo_config(prompt=CU, taps=ZTAPS))
# face-denoise comparison (0.35 = LUNA-Z default) on the same base
go("G_PC_den035_FB", photo_config(face_denoise=0.35, taps=ZTAPS))
# S4 retest ON THIS GRAPH: vendor pairing on the face pass
go("G_PC_rms_FB", photo_config(face_sampler="res_multistep",
                               face_scheduler="simple", taps=ZTAPS))
# literal hybrid: Z-30 base + SDXL face treatment (the zusdu617 reading)
go("G_PCH_FB", hybrid_zusdu(taps=STD_TAPS))
# negative-liveness proof: loud negative must visibly change the base
go("G_PC_negproof_FB", photo_config(
    neg=BALCONY_NEG + ", black dress, black clothing, dark fabric", taps={}))

go("canaryG2", zit_simple(FACE_PROMPT, 12345, arm="img"))
c2 = np.asarray(Image.open("/workspace/run5/output/G/canaryG2/img/img_00001_.png"))
print(f"[canaryG2] max_abs_diff={int(np.abs(a.astype(np.int16)-c2.astype(np.int16)).max())}", flush=True)
print("batch G done", flush=True)
