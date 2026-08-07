#!/usr/bin/env python3
"""Batch I — agent C lighting arms on the PC baseline, one change each.
Evidence-first: the pass-probe showed the chain (NMKD sandwich + tiled
refines) flattens the base's directional light; preservation arms lead."""
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
        ex, _ = run_arm("I", arm, graph)
        print(f"[{arm}] ok exec={ex:.1f}s", flush=True)
    except Exception as e:
        print(f"[{arm}] FAIL {e}", flush=True)

go("canaryI", zit_simple(FACE_PROMPT, 12345, arm="img"))
a = np.asarray(Image.open("/workspace/run5/output/A/zref_P_12345/img/img_00001_.png"))
c = np.asarray(Image.open("/workspace/run5/output/I/canaryI/img/img_00001_.png"))
print(f"[canaryI] max_abs_diff={int(np.abs(a.astype(np.int16)-c.astype(np.int16)).max())}", flush=True)

# 1) light-preservation: NMKD 4x + x0.4 sandwich -> single lanczos 1.6x
g = photo_config(taps=ZTAPS)
g["ZL"] = {"class_type": "ImageScaleBy",
           "inputs": {"upscale_method": "lanczos", "scale_by": 1.6,
                      "image": ["ZB_dec", 0]}}
g["619:617"]["inputs"]["image"] = ["ZL", 0]
go("I_lanczos_FB", g)

# 2) light-preservation: colormatch references -> the BASE output
g = photo_config(taps=ZTAPS)
for cm in ("620:137", "620:111", "621:163"):
    g[cm]["inputs"]["reference"] = ["ZB_dec", 0]
go("I_cmref_FB", g)

# 3) prompt lever: source + direction + quality sentence
go("I_lightpos_FB", photo_config(taps=ZTAPS, prompt=BALCONY +
   ", lit by the low golden sun from the left, soft directional light, deep "
   "natural shadows falling to the right, gentle highlight rolloff"))

# 4) negative lever (exactly 5 terms, quality terms removed — one change)
go("I_negflat_FB", photo_config(taps=ZTAPS,
   neg="flat lighting, overexposed, washed out, low contrast, HDR"))

# 5-7) base-pass shift ladder (detail passes stay at default 3.0)
for shift in (1.5, 4.5, 6.0):
    g = photo_config(taps=ZTAPS)
    g["ZBms"] = {"class_type": "ModelSamplingAuraFlow",
                 "inputs": {"shift": shift, "model": ["116", 0]}}
    g["ZB_k"]["inputs"]["model"] = ["ZBms", 0]
    go(f"I_shift{str(shift).replace('.','')}_FB", g)

# 8-9) base cfg calibration
go("I_cfg15_FB", photo_config(taps=ZTAPS, base_cfg=1.5))
go("I_cfg25_FB", photo_config(taps=ZTAPS, base_cfg=2.5))

# 10) film-stock lever
go("I_film_FB", photo_config(taps=ZTAPS, prompt=BALCONY +
   ", shot on Kodak Portra 400, gentle flash falloff, candid unstaged "
   "documentary feel"))

go("canaryI2", zit_simple(FACE_PROMPT, 12345, arm="img"))
c2 = np.asarray(Image.open("/workspace/run5/output/I/canaryI2/img/img_00001_.png"))
print(f"[canaryI2] max_abs_diff={int(np.abs(a.astype(np.int16)-c2.astype(np.int16)).max())}", flush=True)
print("batch I done", flush=True)
