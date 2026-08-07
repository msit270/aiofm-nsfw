#!/usr/bin/env python3
"""Batch K — agent F structural arms on the PC baseline, one change each.
K2 (exclusive-region SEGS) and K6 (detail-daemon pack) deferred with notes."""
import sys, time
import numpy as np
from PIL import Image
sys.path.insert(0, "/workspace/run5/tools")
from r5 import boot, run_arm, zit_simple, FACE_PROMPT
from candidates import photo_config, ZTAPS

boot()

def go(arm, graph):
    t0 = time.time()
    try:
        ex, _ = run_arm("K", arm, graph)
        print(f"[{arm}] ok exec={ex:.1f}s", flush=True)
    except Exception as e:
        print(f"[{arm}] FAIL {e}", flush=True)

go("canaryK", zit_simple(FACE_PROMPT, 12345, arm="img"))
a = np.asarray(Image.open("/workspace/run5/output/A/zref_P_12345/img/img_00001_.png"))
c = np.asarray(Image.open("/workspace/run5/output/K/canaryK/img/img_00001_.png"))
print(f"[canaryK] max_abs_diff={int(np.abs(a.astype(np.int16)-c.astype(np.int16)).max())}", flush=True)

# K1: ORDER FLIP — face+mouth detail BEFORE the final x1.5 USDU; eyes after
g = photo_config(taps=ZTAPS)
g["620:137"]["inputs"]["image"] = ["587:87", 0]
g["620:137"]["inputs"]["reference"] = ["587:87", 0]
g["587:98"]["inputs"]["image"] = ["621:163", 0]
g["622:431"]["inputs"]["images"] = ["587:98", 0]
go("K1_detail_before_upscale_FB", g)

# K4a: colormatch chain REMOVED entirely
g = photo_config(taps=ZTAPS)
g["620:114"]["inputs"]["image"] = ["587:98", 0]       # skip 137
g["620:165"]["inputs"]["image"] = ["620:114", 0]      # skip 111
g["622:431"]["inputs"]["images"] = ["620:165", 0]     # skip 163
go("K4a_no_colormatch_FB", g)

# K4b: colormatch ONCE at the end (after eyes would need restructure; use
# end-of-chain before eyes input, referenced to the pre-detail frame)
g = photo_config(taps=ZTAPS)
g["620:114"]["inputs"]["image"] = ["587:98", 0]
g["620:165"]["inputs"]["image"] = ["620:114", 0]
g["621:163"]["inputs"]["image"] = ["620:165", 0]      # single cm kept here
g["621:163"]["inputs"]["reference"] = ["587:98", 0]
go("K4b_cm_end_only_FB", g)

# K4c: per-pass colormatch kept but factor 1.0 -> 0.5
g = photo_config(taps=ZTAPS)
for cm in ("620:137", "620:111", "621:163"):
    g[cm]["inputs"]["factor"] = 0.5
go("K4c_cm_factor05_FB", g)

# K5: ImageBlend 587:87 factor 1.0 -> 0.6 (the dead dial becomes a blend:
# 40% hands-pass output + 60% skin-ESRGAN texture)
g = photo_config(taps=ZTAPS)
g["587:87"]["inputs"]["blend_factor"] = 0.6
go("K5_blend06_FB", g)

# K8: NoiseInjection hook on the eyes pass (iris micro-detail lever)
g = photo_config(taps=ZTAPS)
g["KNI"] = {"class_type": "NoiseInjectionDetailerHookProvider",
            "inputs": {"schedule_for_cycle": "simple",
                       "source": "GPU", "seed": 777, "start_strength": 0.3,
                       "end_strength": 0.1}}
g["622:406"]["inputs"]["detailer_hook"] = ["KNI", 0]
go("K8_eyes_noiseinject_FB", g)

go("canaryK2", zit_simple(FACE_PROMPT, 12345, arm="img"))
c2 = np.asarray(Image.open("/workspace/run5/output/K/canaryK2/img/img_00001_.png"))
print(f"[canaryK2] max_abs_diff={int(np.abs(a.astype(np.int16)-c2.astype(np.int16)).max())}", flush=True)
print("batch K done", flush=True)
