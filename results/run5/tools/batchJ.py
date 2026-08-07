#!/usr/bin/env python3
"""Batch J — agent A hands arms on the PC baseline. One change per arm.
Research ranking: prompt neutralization first (the 'detailed' stack is the
overbake suspect), context/denoise/resolution levers, then ordering (the
only region whose delivered pixels are ESRGAN-invented, per F research)."""
import sys, time, copy
import numpy as np
from PIL import Image
sys.path.insert(0, "/workspace/run5/tools")
from r5 import boot, run_arm, zit_simple, FACE_PROMPT
from candidates import photo_config, ZTAPS

boot()

def go(arm, graph):
    t0 = time.time()
    try:
        ex, _ = run_arm("J", arm, graph)
        print(f"[{arm}] ok exec={ex:.1f}s", flush=True)
    except Exception as e:
        print(f"[{arm}] FAIL {e}", flush=True)

PT = ("photorealistic portrait photograph of a young woman standing in soft "
      "window light, natural skin texture with visible pores, detailed eyes, "
      "detailed hands at her sides, looking at the camera, 85mm lens, shallow "
      "depth of field")
NEUTRAL = ("young woman's hand, smooth soft skin, natural hand, elegant "
           "fingers, neat fingernails")

go("canaryJ", zit_simple(FACE_PROMPT, 12345, arm="img"))
a = np.asarray(Image.open("/workspace/run5/output/A/zref_P_12345/img/img_00001_.png"))
c = np.asarray(Image.open("/workspace/run5/output/J/canaryJ/img/img_00001_.png"))
print(f"[canaryJ] max_abs_diff={int(np.abs(a.astype(np.int16)-c.astype(np.int16)).max())}", flush=True)

# A1: prompt neutralization (the rank-1 arm), FB + PT
g = photo_config(taps=ZTAPS)
g["587:93"]["inputs"]["text"] = NEUTRAL
go("J_A1_neutral_FB", g)
g = photo_config(prompt=PT, taps=ZTAPS)
g["587:93"]["inputs"]["text"] = NEUTRAL
go("J_A1_neutral_PT", g)
# A1b: near-empty positive
g = photo_config(taps=ZTAPS)
g["587:93"]["inputs"]["text"] = "a hand"
go("J_A1b_ahand_FB", g)

# A2: crop factor 1.5 -> 3.0 (context; the reference default)
g = photo_config(taps=ZTAPS)
g["587:92"]["inputs"]["bbox_crop_factor"] = 3.0
go("J_A2_cf30_FB", g)

# A3: denoise ladder down (anti-overbake)
for dn in (0.28, 0.32):
    g = photo_config(taps=ZTAPS)
    g["587:92"]["inputs"]["denoise"] = dn
    go(f"J_A3_dn{str(dn).replace('0.','')}_FB", g)
# A3g: sample the hand crop at lower res (768) — enlargement amplifier test
g = photo_config(taps=ZTAPS)
g["587:92"]["inputs"]["guide_size"] = 768
g["587:92"]["inputs"]["max_size"] = 768
go("J_A3g_guide768_FB", g)

# A4: MOVE the hands pass after the final USDU (diffusion-sampled at
# delivered scale instead of ESRGAN-invented)
g = photo_config(taps=ZTAPS)
g["587:91"]["inputs"]["image"] = ["619:601", 0]
g["587:87"]["inputs"]["image1"] = ["619:601", 0]
g["587:92"]["inputs"]["image"] = ["587:98", 0]
g["620:137"]["inputs"]["image"] = ["587:92", 0]
go("J_A4_post98_FB", g)

# A4b: KEEP the early structural pass, ADD a light polish pass after 98
g = photo_config(taps=ZTAPS)
hp = copy.deepcopy(g["587:92"])
hp["inputs"]["image"] = ["587:98", 0]
hp["inputs"]["denoise"] = 0.15
g["HPOL"] = hp
g["620:137"]["inputs"]["image"] = ["HPOL", 0]
go("J_A4b_polish_FB", g)

go("canaryJ2", zit_simple(FACE_PROMPT, 12345, arm="img"))
c2 = np.asarray(Image.open("/workspace/run5/output/J/canaryJ2/img/img_00001_.png"))
print(f"[canaryJ2] max_abs_diff={int(np.abs(a.astype(np.int16)-c2.astype(np.int16)).max())}", flush=True)
print("batch J done", flush=True)
