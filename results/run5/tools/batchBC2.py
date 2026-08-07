#!/usr/bin/env python3
"""Batch BC2 — re-run of everything queued after the str08 NaN poisoning,
on a fresh server. zbref first (poisoning-vs-incompatibility disambiguation),
then a canary (zref_P_12345 re-render must be bit-identical to batch A's),
then the surviving B and C arms. str08 deliberately EXCLUDED (parked)."""
import sys, time, json
import numpy as np
from PIL import Image
sys.path.insert(0, "/workspace/run5/tools")
from r5 import (boot, run_arm, pipeline_graph, zbase_splice, zit_simple,
                STD_TAPS, BALCONY, BALCONY_NEG, FACE_PROMPT, buyer_values)

boot()

def go(batch, arm, graph):
    t0 = time.time()
    try:
        ex, _ = run_arm(batch, arm, graph)
        print(f"[{arm}] ok exec={ex:.1f}s wall={time.time()-t0:.1f}s", flush=True)
        return True
    except Exception as e:
        print(f"[{arm}] FAIL {e}", flush=True)
        return False

# 1) Z-Image BASE + luna, fresh server: garbage again => real incompatibility
go("C", "zbref_P_12345", zit_simple(FACE_PROMPT, 12345, steps=30, cfg=4.0,
   neg=BALCONY_NEG, arm="img", unet="z_image_bf16.safetensors"))
go("C", "zbref_P_12345_nolora", zit_simple(FACE_PROMPT, 12345, steps=30, cfg=4.0,
   neg=BALCONY_NEG, arm="img", unet="z_image_bf16.safetensors", lora=None))

# 2) canary: must be bit-identical to batch A's zref_P_12345
go("C", "canary_zref_P_12345", zit_simple(FACE_PROMPT, 12345, arm="img"))
a = np.asarray(Image.open("/workspace/run5/output/A/zref_P_12345/img/img_00001_.png"))
c = np.asarray(Image.open("/workspace/run5/output/C/canary_zref_P_12345/img/img_00001_.png"))
d = int(np.abs(a.astype(np.int16) - c.astype(np.int16)).max())
print(f"[canary] max_abs_diff={d}", flush=True)
if d != 0:
    print("[canary] FAILED — aborting batch (server not clean)", flush=True)
    sys.exit(2)

# 3) batch B remainder
go("B", "B_fix610", pipeline_graph(taps=STD_TAPS,
   rewires={("619:610", "model"): ["618", 0], ("619:610", "clip"): ["618", 1]}))

bv = buyer_values()
pb = json.loads(bv["483"]["inputs"]["prompt_batch_data"])
pb[0]["positive_prompt"] = ("lunaskye, photorealistic full body photograph of a "
    "young woman with long straight blonde hair with dark roots and curtain "
    "bangs, standing on a hotel balcony at golden hour, wearing a black silk "
    "slip dress, natural skin texture with visible pores and freckles, shot on "
    "85mm, shallow depth of field")
go("B", "B_fixprompt", pipeline_graph(taps=STD_TAPS,
   overrides={"483": {"prompt_batch_data": json.dumps(pb)}}))
go("B", "B_fixboth", pipeline_graph(taps=STD_TAPS,
   overrides={"483": {"prompt_batch_data": json.dumps(pb)}},
   rewires={("619:610", "model"): ["618", 0], ("619:610", "clip"): ["618", 1]}))
go("B", "B_rms_simple", pipeline_graph(taps=STD_TAPS,
   overrides={"620:114": {"sampler_name": "res_multistep", "scheduler": "simple"}}))
go("B", "B_mouth05", pipeline_graph(taps=STD_TAPS,
   overrides={"620:165": {"bbox_threshold": 0.5}}))
go("B", "B_mouth03", pipeline_graph(taps=STD_TAPS,
   overrides={"620:165": {"bbox_threshold": 0.3}}))
go("B", "B_den085", pipeline_graph(taps=STD_TAPS,
   overrides={"620:114": {"denoise": 0.85}}))
go("B", "B_v9", pipeline_graph(taps=STD_TAPS,
   overrides={"619:613": {"ckpt_name": "lustifyNSFWCheckpoint_zenithV9.safetensors"}}))

# 4) batch C remainder
go("C", "C_tdd_cfg", pipeline_graph(taps=STD_TAPS,
   overrides={"619:600": {"cfg": 1.8, "scheduler": "sgm_uniform"},
              "587:98": {"cfg": 1.8}}))
go("C", "C_zhands", pipeline_graph(taps=STD_TAPS,
   overrides={"587:92": {"cfg": 1.0, "steps": 8, "sampler_name": "res_multistep",
                          "scheduler": "simple"}},
   rewires={("587:92", "model"): ["116", 0],
            ("587:92", "clip"): ["620:110", 0],
            ("587:92", "vae"): ["620:109", 0],
            ("587:93", "clip"): ["620:110", 0],
            ("587:506", "clip"): ["620:110", 0]}))
go("C", "C_nocm111", pipeline_graph(taps=STD_TAPS,
   rewires={("620:165", "image"): ["620:114", 0],
            ("621:163", "reference"): ["620:114", 0]}))
extra = {
    "ZU_pos": {"class_type": "CLIPTextEncode",
               "inputs": {"text": BALCONY, "clip": ["620:110", 0]}},
    "ZU_neg": {"class_type": "ConditioningZeroOut",
               "inputs": {"conditioning": ["ZU_pos", 0]}},
}
g = pipeline_graph(taps=STD_TAPS,
    overrides={"619:617": {"cfg": 1.0, "steps": 8, "sampler_name": "res_multistep",
                            "scheduler": "simple"}},
    rewires={("619:617", "model"): ["116", 0],
             ("619:617", "positive"): ["ZU_pos", 0],
             ("619:617", "negative"): ["ZU_neg", 0],
             ("619:617", "vae"): ["620:109", 0]})
g.update(extra)
go("C", "C_zusdu617", g)

# 5) final canary
go("C", "canary2_zref_P_12345", zit_simple(FACE_PROMPT, 12345, arm="img"))
c2 = np.asarray(Image.open("/workspace/run5/output/C/canary2_zref_P_12345/img/img_00001_.png"))
d2 = int(np.abs(a.astype(np.int16) - c2.astype(np.int16)).max())
print(f"[canary2] max_abs_diff={d2}", flush=True)
print("batch BC2 done", flush=True)
