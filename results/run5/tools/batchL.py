#!/usr/bin/env python3
"""Batch L — the additive-freckle 2x2 completion + re-derivation of settled
numbers now resting on dead (SDXL-arch) calibration. One change per arm vs
the PC1 baseline unless stated."""
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
        ex, _ = run_arm("L", arm, graph)
        print(f"[{arm}] ok exec={ex:.1f}s", flush=True)
    except Exception as e:
        print(f"[{arm}] FAIL {e}", flush=True)

go("canaryL", zit_simple(FACE_PROMPT, 12345, arm="img"))
a = np.asarray(Image.open("/workspace/run5/output/A/zref_P_12345/img/img_00001_.png"))
c = np.asarray(Image.open("/workspace/run5/output/L/canaryL/img/img_00001_.png"))
print(f"[canaryL] max_abs_diff={int(np.abs(a.astype(np.int16)-c.astype(np.int16)).max())}", flush=True)

# additive-freckle 2x2: the 8/cfg1 (low-texture base) pair; the 30/cfg2 pair
# already exists (G_PC1_FB = ea, G_PC_rms_FB = rms)
go("L_add8_ea_FB", photo_config(base_steps=8, base_cfg=1.0))
go("L_add8_rms_FB", photo_config(base_steps=8, base_cfg=1.0,
                                 face_sampler="res_multistep",
                                 face_scheduler="simple"))

# re-derivation on the PC base
g = photo_config(taps=ZTAPS)
g["620:114"]["inputs"]["steps"] = 12
go("L_fsteps12_FB", g)
for dn, tag in ((0.30, "eyes_dn030"), (0.55, "eyes_dn055")):
    g = photo_config(taps=ZTAPS)
    g["622:406"]["inputs"]["denoise"] = dn
    go(f"L_{tag}_FB", g)
for dn, tag in ((0.15, "617_dn015"), (0.35, "617_dn035")):
    g = photo_config(taps=ZTAPS)
    g["619:617"]["inputs"]["denoise"] = dn
    go(f"L_{tag}_FB", g)
for dn, tag in ((0.05, "98_dn005"), (0.12, "98_dn012")):
    g = photo_config(taps=ZTAPS)
    g["587:98"]["inputs"]["denoise"] = dn
    go(f"L_{tag}_FB", g)

go("canaryL2", zit_simple(FACE_PROMPT, 12345, arm="img"))
c2 = np.asarray(Image.open("/workspace/run5/output/L/canaryL2/img/img_00001_.png"))
print(f"[canaryL2] max_abs_diff={int(np.abs(a.astype(np.int16)-c2.astype(np.int16)).max())}", flush=True)
print("batch L done", flush=True)
