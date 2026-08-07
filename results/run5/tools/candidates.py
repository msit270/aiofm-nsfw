#!/usr/bin/env python3
"""The two candidate configs, as graph builders.

LUNA-Z  (Z-native): ZIT+luna drives base AND every sampling pass; SDXL fully
        out of the model path. SDXL refine (600), SDXL face pass (607) skipped.
SDXL-FIXED: keep the shipped architecture; apply the measured repairs
        (fix610 + fixprompt + V9 [+ tdd cfg per BC2] + mouth threshold).
"""
import sys, json
sys.path.insert(0, "/workspace/run5/tools")
from r5 import pipeline_graph, zbase_splice, STD_TAPS, BALCONY, buyer_values

ZTAPS = {k: v for k, v in STD_TAPS.items()
         if k not in ("T01_base591", "T03_refine596", "T04_sdxlface607")}
ZTAPS["T00_zbase"] = ("ZB_dec", 0)

V9 = "lustifyNSFWCheckpoint_zenithV9.safetensors"

FIXED_PROMPT = ("lunaskye, photorealistic full body photograph of a young woman "
    "with long straight blonde hair with dark roots and curtain bangs, standing "
    "on a hotel balcony at golden hour, wearing a black silk slip dress, natural "
    "skin texture with visible pores and freckles, shot on 85mm, shallow depth "
    "of field")


def luna_z(base_steps=8, base_cfg=1.0, face_denoise=0.35, mouth_thr=0.5,
           prompt=BALCONY, taps=None, seed=12345, w=896, h=1152):
    """Z-native candidate."""
    g = pipeline_graph(taps=(ZTAPS if taps is None else taps),
        overrides={
            # Z-native tiled refine (was SDXL 25-step cfg4.5)
            "619:617": {"cfg": 1.0, "steps": 8, "sampler_name": "res_multistep",
                        "scheduler": "simple"},
            # Z-native polish upscale (was SDXL-TDD lcm)
            "587:98": {"cfg": 1.0, "sampler_name": "res_multistep",
                       "scheduler": "simple"},
            # Z-native hands
            "587:92": {"cfg": 1.0, "steps": 8, "sampler_name": "res_multistep",
                       "scheduler": "simple"},
            # face pass denoise (identity now arrives with the base; texture role)
            "620:114": {"denoise": face_denoise},
            # mouth detector threshold (BC2-informed)
            "620:165": {"bbox_threshold": mouth_thr},
        },
        rewires={
            # skip SDXL refine + SDXL face pass + the 597/616 VAE round-trip:
            # NMKD/x0.4 output feeds the Z-USDU directly in pixel space
            ("619:617", "image"): ["619:595", 0],
            # Z models/conds into 617
            ("619:617", "model"): ["116", 0],
            ("619:617", "positive"): ["ZU_pos", 0],
            ("619:617", "negative"): ["ZU_neg", 0],
            ("619:617", "vae"): ["620:109", 0],
            # Z models/conds into 98
            ("587:98", "model"): ["116", 0],
            ("587:98", "positive"): ["ZU_pos", 0],
            ("587:98", "negative"): ["ZU_neg", 0],
            ("587:98", "vae"): ["620:109", 0],
            # Z hands
            ("587:92", "model"): ["116", 0],
            ("587:92", "clip"): ["620:110", 0],
            ("587:92", "vae"): ["620:109", 0],
            ("587:93", "clip"): ["620:110", 0],
            ("587:506", "clip"): ["620:110", 0],
        })
    g.update({
        "ZU_pos": {"class_type": "CLIPTextEncode",
                   "inputs": {"text": prompt, "clip": ["620:110", 0]}},
        "ZU_neg": {"class_type": "ConditioningZeroOut",
                   "inputs": {"conditioning": ["ZU_pos", 0]}},
    })
    g = zbase_splice(g, prompt=prompt, seed=seed, steps=base_steps,
                     cfg=base_cfg, w=w, h=h)
    # base prompt for 483 drives seeds/preview only now; keep in sync
    bv = buyer_values()
    pb = json.loads(bv["483"]["inputs"]["prompt_batch_data"])
    pb[0]["positive_prompt"] = prompt
    pb[0]["seed"] = seed
    g["483"]["inputs"]["prompt_batch_data"] = json.dumps(pb)
    return g


def sdxl_fixed(prompt=FIXED_PROMPT, taps=None, mouth_thr=0.5, tdd_cfg=None,
               seed=12345):
    """Repaired SDXL candidate: V9 + char-LoRA on the refine + trigger prompt."""
    bv = buyer_values()
    pb = json.loads(bv["483"]["inputs"]["prompt_batch_data"])
    pb[0]["positive_prompt"] = prompt
    pb[0]["seed"] = seed
    ov = {"483": {"prompt_batch_data": json.dumps(pb)},
          "619:613": {"ckpt_name": V9},
          "620:165": {"bbox_threshold": mouth_thr}}
    if tdd_cfg:
        ov["619:600"] = {"cfg": tdd_cfg, "scheduler": "sgm_uniform"}
        ov["587:98"] = {"cfg": tdd_cfg}
    return pipeline_graph(taps=(STD_TAPS if taps is None else taps),
        overrides=ov,
        rewires={("619:610", "model"): ["618", 0],
                 ("619:610", "clip"): ["618", 1]})
