#!/usr/bin/env python3
"""Batch C — research-informed arms: Turbo-LoRA acceleration test, Z-Image
BASE model, TDD on-recommendation, Z-hands, colormatch bypass, Z-USDU."""
import sys, time
sys.path.insert(0, "/workspace/run5/tools")
from r5 import (boot, run_arm, pipeline_graph, zbase_splice, zit_simple,
                STD_TAPS, BALCONY, BALCONY_NEG, FACE_PROMPT)

boot()
B = "C"

def go(arm, graph):
    t0 = time.time()
    try:
        ex, _ = run_arm(B, arm, graph)
        print(f"[{arm}] ok exec={ex:.1f}s wall={time.time()-t0:.1f}s", flush=True)
    except Exception as e:
        print(f"[{arm}] FAIL {e}", flush=True)

# 1) DistillPatch blur test: luna on Turbo at non-acceleration config
go("zref_P_12345_s30cfg2", zit_simple(FACE_PROMPT, 12345, steps=30, cfg=2.0,
                                      neg=BALCONY_NEG, arm="img"))
# 2) community-recommended LoRA strength
go("zref_P_12345_str08", zit_simple(FACE_PROMPT, 12345, lora_strength=0.8, arm="img"))
# 3) Z-Image BASE (non-turbo) with luna — vendor settings 30 steps cfg 4
go("zbref_P_12345", zit_simple(FACE_PROMPT, 12345, steps=30, cfg=4.0,
                               neg=BALCONY_NEG, arm="img", unet="z_image_bf16.safetensors"))
go("zbref_B_12345", zit_simple(BALCONY, 12345, steps=30, cfg=4.0,
                               neg=BALCONY_NEG, arm="img", unet="z_image_bf16.safetensors"))

# 4) TDD on-recommendation: cfg 1.8 + sgm_uniform on both TDD passes
go("C_tdd_cfg", pipeline_graph(taps=STD_TAPS,
   overrides={"619:600": {"cfg": 1.8, "scheduler": "sgm_uniform"},
              "587:98": {"cfg": 1.8}}))

# 5) hands pass on the Z-Image model (luna stack; qwen conditioning)
go("C_zhands", pipeline_graph(taps=STD_TAPS,
   overrides={"587:92": {"cfg": 1.0, "steps": 8, "sampler_name": "res_multistep",
                          "scheduler": "simple"}},
   rewires={("587:92", "model"): ["116", 0],
            ("587:92", "clip"): ["620:110", 0],
            ("587:92", "vae"): ["620:109", 0],
            ("587:93", "clip"): ["620:110", 0],
            ("587:506", "clip"): ["620:110", 0]}))

# 6) drop the after-face colormatch 620:111
go("C_nocm111", pipeline_graph(taps=STD_TAPS,
   rewires={("620:165", "image"): ["620:114", 0],
            ("621:163", "reference"): ["620:114", 0]}))

# 7) Z-native tiled refine: USDU 617 on the luna'd Z model
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
go("C_zusdu617", g)
print("batch C done", flush=True)
