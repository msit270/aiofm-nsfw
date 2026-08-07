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
        # empty-text encode, NOT ConditioningZeroOut: at cfg 1 the negative is
        # never evaluated (identical output, verified by bit-compare), and at
        # cfg > 1 ZeroOut black-frames Z-Image deterministically (batch F2).
        "ZU_neg": {"class_type": "CLIPTextEncode",
                   "inputs": {"text": "", "clip": ["620:110", 0]}},
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


def final_graph(kind="luna_z", pick_list="", **kw):
    """The shippable graph: no measurement taps, selector live by default,
    product SaveImage prefix, prompt/seed WIRED from the 483 UI node, dead
    SDXL-side nodes pruned."""
    g = luna_z(taps={}, **kw) if kind == "luna_z" else sdxl_fixed(taps={}, **kw)
    g["619:603"]["inputs"]["pick_list"] = pick_list
    g["505"]["inputs"]["filename_prefix"] = "Luna/Personal"
    if kind == "luna_z":
        # dev instrumentation out of the product (run-2 verdict; its stale
        # rgthree_comparer temp URLs were a known buyer-visible trap)
        g.pop("419", None)
        # the owner's prompt/seed UI (483 -> 590 string, 483 slot2 seed)
        g["ZB_pos"]["inputs"]["text"] = ["619:590", 0]
        g["ZB_k"]["inputs"]["seed"] = ["483", 2]
        # ZU (tiled-refine cond) follows the same prompt
        g["ZU_pos"]["inputs"]["text"] = ["619:590", 0]
        # prune everything unreachable from the terminal nodes
        sinks = [n for n, v in g.items() if v["class_type"] in
                 ("SaveImage", "PreviewAny", "Image Comparer (rgthree)",
                  "INSTARAW_PromptBatchPreview")]
        seen = set()
        def walk(n):
            if n in seen:
                return
            seen.add(n)
            for v in g[n]["inputs"].values():
                if isinstance(v, list) and str(v[0]) in g:
                    walk(str(v[0]))
        for s in sinks:
            walk(s)
        for n in [n for n in g if n not in seen]:
            del g[n]
    return g


def photo_config(base_steps=30, base_cfg=2.0, face_denoise=0.50,
                 face_sampler="euler_ancestral", face_scheduler="kl_optimal",
                 prompt=BALCONY, neg=None, taps=None, seed=12345,
                 w=896, h=1152, mouth_thr=0.5):
    """PC — the reconciled, CHARACTER-NEUTRAL config (owner verdicts, 2026-08-08).

    S3 pick: Z base 30 steps / cfg 2 (negatives LIVE at cfg>1 — ZB_neg wired
    from the 483 negative string). S1 pick's essence (soft, photographic
    face): the face pass repaints the crunchy 30-step crop with the smoothest
    sampler (euler_ancestral, Q3) at a higher denoise. Body texture channel
    (Z-USDU 617/98 res_multistep) kept exactly as the S3 winner had it.
    Character-specific values are ARGUMENTS, never constants."""
    g = luna_z(base_steps=base_steps, base_cfg=base_cfg,
               face_denoise=face_denoise, mouth_thr=mouth_thr,
               prompt=prompt, taps=taps, seed=seed, w=w, h=h)
    g["620:114"]["inputs"]["sampler_name"] = face_sampler
    g["620:114"]["inputs"]["scheduler"] = face_scheduler
    # negatives live on the base pass at cfg 2: wire the owner's typed
    # negative (483 slot 1 -> 619:605 passthrough) into ZB_neg
    g["ZB_neg"] = {"class_type": "CLIPTextEncode",
                   "inputs": {"text": ["619:605", 0], "clip": ["620:110", 0]}}
    g["ZB_k"]["inputs"]["negative"] = ["ZB_neg", 0]
    if neg is not None:
        import json as _j
        pb = _j.loads(g["483"]["inputs"]["prompt_batch_data"])
        pb[0]["negative_prompt"] = neg
        g["483"]["inputs"]["prompt_batch_data"] = _j.dumps(pb)
    return g


def hybrid_zusdu(base_steps=30, base_cfg=2.0, taps=None, prompt=BALCONY, seed=12345):
    """PC-H — the LITERAL reading of the owner's two picks: Z base 30/cfg2
    but the SDXL face treatment retained (607 + SDXL refine chain + SDXL 98),
    i.e. the zusdu617 arm with only the base swapped. Costs SDXL residency."""
    g = pipeline_graph(taps=(taps if taps is not None else {}),
        overrides={"619:617": {"cfg": 1.0, "steps": 8,
                                "sampler_name": "res_multistep",
                                "scheduler": "simple"},
                   "620:165": {"bbox_threshold": 0.5}},
        rewires={("619:617", "model"): ["116", 0],
                 ("619:617", "positive"): ["ZU_pos", 0],
                 ("619:617", "negative"): ["ZU_neg", 0],
                 ("619:617", "vae"): ["620:109", 0]})
    g.update({
        "ZU_pos": {"class_type": "CLIPTextEncode",
                   "inputs": {"text": prompt, "clip": ["620:110", 0]}},
        "ZU_neg": {"class_type": "CLIPTextEncode",
                   "inputs": {"text": "", "clip": ["620:110", 0]}},
    })
    g = zbase_splice(g, prompt=prompt, seed=seed, steps=base_steps,
                     cfg=base_cfg, w=w if False else 896, h=1152)
    g["ZB_neg"] = {"class_type": "CLIPTextEncode",
                   "inputs": {"text": ["619:605", 0], "clip": ["620:110", 0]}}
    g["ZB_k"]["inputs"]["negative"] = ["ZB_neg", 0]
    import json as _j
    bv = buyer_values()
    pb = _j.loads(bv["483"]["inputs"]["prompt_batch_data"])
    pb[0]["positive_prompt"] = prompt
    pb[0]["seed"] = seed
    g["483"]["inputs"]["prompt_batch_data"] = _j.dumps(pb)
    return g
