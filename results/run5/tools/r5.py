#!/usr/bin/env python3
"""run-5 driver — personal-max quality run (2026-08-07).

One persistent ComfyUI server on 127.0.0.1:19188 (18188 never touched),
output to /workspace/run5/output. Graph builders:
  pipeline_graph()  — shipped buyer graph (api_final + buyer values) + taps
  zit_simple()      — reconstructed "simple ZIT" reference (vendor template + luna)
  sdxl_simple()     — LUSTIFY + lunaskye portrait probe

Evidence per arm under /workspace/nsfw-quality/results/run5/<batch>/<arm>/:
  api_graph.json, history.json, meta.json ; PNGs stay under /workspace/run5/output
  (repo gets metrics + sheets, not every raw frame — flagged in meta paths).
Determinism guard: baseline arm re-rendered at batch end, bit-compare.
"""
import json, os, subprocess, sys, time, urllib.request, copy, glob, shutil

NQ = "/workspace/nsfw-quality"
FINAL = f"{NQ}/results/run3/guard/api_final.json"
FRESH = f"{NQ}/results/run3/fresh/fresh-buyer-api_graph.json"
RES = f"{NQ}/results/run5"
OUT = "/workspace/run5/output"
COMFY = "/workspace/ComfyUI"
SERVER = "127.0.0.1:19188"
LOG = "/workspace/run5/server_19188.log"

BALCONY = ("photorealistic full body photograph of a young woman with long dark "
           "hair standing on a hotel balcony at golden hour, wearing a black silk "
           "slip dress, natural skin texture with visible pores and freckles, "
           "shot on 85mm, shallow depth of field")
BALCONY_NEG = "bad quality, worst quality, low quality, deformed, extra fingers, watermark, text"
FACE_PROMPT = ("luna, a young woman in her mid twenties with wavy auburn hair, warm "
               "hazel eyes, soft natural makeup, light freckles on her cheeks, gentle "
               "smile, photorealistic skin texture with visible pores, soft diffused studio light")

# ---------- server ----------

def _req(path, data=None, timeout=120):
    url = f"http://{SERVER}{path}"
    body = json.dumps(data).encode() if data is not None else None
    hdrs = {"Content-Type": "application/json"} if data is not None else {}
    with urllib.request.urlopen(urllib.request.Request(url, data=body, headers=hdrs),
                                timeout=timeout) as f:
        raw = f.read()
    return json.loads(raw) if raw else None


def server_up():
    try:
        _req("/system_stats", timeout=5)
        return True
    except Exception:
        return False


def boot():
    if server_up():
        return None
    os.makedirs(OUT, exist_ok=True)
    p = subprocess.Popen(
        [sys.executable, "main.py", "--port", "19188", "--disable-auto-launch",
         "--output-directory", OUT],
        cwd=COMFY, stdout=open(LOG, "a"), stderr=subprocess.STDOUT,
        start_new_session=True)
    for _ in range(120):
        time.sleep(2)
        if server_up():
            return p.pid
    raise RuntimeError("server did not come up; see " + LOG)


# ---------- graph builders ----------

def buyer_values():
    f = json.load(open(FRESH))
    return f

def pipeline_graph(overrides=None, rewires=None, taps=None, drop=None):
    """Shipped graph + buyer values. taps: {name: (node_id, slot)} -> SaveImage.
    rewires: {(node,input): [src, slot]}. drop: [node_ids to delete]."""
    g = copy.deepcopy(json.load(open(FINAL)))
    if "419" in g:
        g["419"]["inputs"].pop("rgthree_comparer", None)
    f = buyer_values()
    g["116"]["inputs"]["lora_01"] = f["116"]["inputs"]["lora_01"]
    g["618"]["inputs"]["lora_01"] = f["618"]["inputs"]["lora_01"]
    g["483"]["inputs"]["prompt_batch_data"] = f["483"]["inputs"]["prompt_batch_data"]
    g["620:106"]["inputs"]["text"] = f["620:106"]["inputs"]["text"]
    g["619:603"]["inputs"]["pick_list"] = "0"
    for nid, kv in (overrides or {}).items():
        g[nid]["inputs"].update(kv)
    for (nid, inp), src in (rewires or {}).items():
        g[nid]["inputs"][inp] = src
    for nid in (drop or []):
        del g[nid]
    for name, (src, slot) in (taps or {}).items():
        g["TAP_" + name] = {"class_type": "SaveImage",
                            "inputs": {"images": [src, slot],
                                       "filename_prefix": "%ARM%/" + name},
                            "_meta": {"title": f"r5 tap {name}"}}
    return g


STD_TAPS = {
    "T01_base591":    ("619:591", 0),
    "T02_nmkd595":    ("619:595", 0),
    "T03_refine596":  ("619:596", 0),
    "T04_sdxlface607": ("619:607", 0),
    "T05_usdu617":    ("619:617", 0),
    "T06_hands92":    ("587:92", 0),
    "T07_blend87":    ("587:87", 0),
    "T08_usdu98":     ("587:98", 0),
    "T10_zface114":   ("620:114", 0),
    "T12_mouth163":   ("621:163", 0),
}


def zit_simple(prompt, seed, w=896, h=1152, steps=8, cfg=1.0,
               sampler="res_multistep", scheduler="simple", denoise=1.0,
               lora="luna.safetensors", lora_strength=1.0, shift=None,
               neg="", arm="zit"):
    """Reconstruction of the owner's 'simple ZIT workflow': vendor Z-Image
    template graph + character LoRA. shift=None -> model default (ZImage 3.0)."""
    g = {
        "u": {"class_type": "UNETLoader",
              "inputs": {"unet_name": "zimage.safetensors", "weight_dtype": "default"}},
        "c": {"class_type": "CLIPLoader",
              "inputs": {"clip_name": "qwen.safetensors", "type": "lumina2", "device": "default"}},
        "v": {"class_type": "VAELoader", "inputs": {"vae_name": "ae.safetensors"}},
        "lat": {"class_type": "EmptySD3LatentImage",
                "inputs": {"width": w, "height": h, "batch_size": 1}},
        "pos": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["c", 0]}},
        "dec": {"class_type": "VAEDecode", "inputs": {"samples": ["k", 0], "vae": ["v", 0]}},
        "save": {"class_type": "SaveImage",
                 "inputs": {"images": ["dec", 0], "filename_prefix": arm + "/img"}},
    }
    model_src = "u"
    if lora:
        g["lo"] = {"class_type": "LoraLoaderModelOnly",
                   "inputs": {"lora_name": lora, "strength_model": lora_strength,
                              "model": [model_src, 0]}}
        model_src = "lo"
    if shift is not None:
        g["ms"] = {"class_type": "ModelSamplingAuraFlow",
                   "inputs": {"shift": shift, "model": [model_src, 0]}}
        model_src = "ms"
    if neg == "":
        g["neg"] = {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["pos", 0]}}
    else:
        g["neg"] = {"class_type": "CLIPTextEncode", "inputs": {"text": neg, "clip": ["c", 0]}}
    g["k"] = {"class_type": "KSampler",
              "inputs": {"seed": seed, "steps": steps, "cfg": cfg,
                         "sampler_name": sampler, "scheduler": scheduler,
                         "denoise": denoise, "model": [model_src, 0],
                         "positive": ["pos", 0], "negative": ["neg", 0],
                         "latent_image": ["lat", 0]}}
    return g


def sdxl_simple(prompt, seed, w=896, h=1152, steps=40, cfg=4.0,
                sampler="dpmpp_2m_sde", scheduler="karras",
                ckpt="SDXLNSFW.safetensors",
                lora="lunaskye.safetensors", lora_strength=1.0,
                neg=BALCONY_NEG, pag=True, arm="sdxl"):
    """Pipeline-base-mirror: LUSTIFY + character LoRA (+MSD eps + PAG 1)."""
    g = {
        "ck": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": ckpt}},
        "lat": {"class_type": "EmptyLatentImage",
                "inputs": {"width": w, "height": h, "batch_size": 1}},
        "dec": {"class_type": "VAEDecode", "inputs": {"samples": ["k", 0], "vae": ["ck", 2]}},
        "save": {"class_type": "SaveImage",
                 "inputs": {"images": ["dec", 0], "filename_prefix": arm + "/img"}},
    }
    model_src, clip_src = "ck", ["ck", 1]
    if lora:
        g["lo"] = {"class_type": "LoraLoader",
                   "inputs": {"lora_name": lora, "strength_model": lora_strength,
                              "strength_clip": lora_strength,
                              "model": [model_src, 0], "clip": clip_src}}
        model_src, clip_src = "lo", ["lo", 1]
    g["pos"] = {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": clip_src}}
    g["neg"] = {"class_type": "CLIPTextEncode", "inputs": {"text": neg, "clip": clip_src}}
    if pag:
        g["msd"] = {"class_type": "ModelSamplingDiscrete",
                    "inputs": {"sampling": "eps", "zsnr": False, "model": [model_src, 0]}}
        g["pag"] = {"class_type": "PerturbedAttentionGuidance",
                    "inputs": {"scale": 1, "model": ["msd", 0]}}
        model_src = "pag"
    g["k"] = {"class_type": "KSampler",
              "inputs": {"seed": seed, "steps": steps, "cfg": cfg,
                         "sampler_name": sampler, "scheduler": scheduler,
                         "denoise": 1.0, "model": [model_src, 0],
                         "positive": ["pos", 0], "negative": ["neg", 0],
                         "latent_image": ["lat", 0]}}
    return g


# ---------- runner ----------

def run_arm(batch, arm, graph, timeout=900):
    """Submit graph, wait, store evidence. Returns (exec_seconds, history)."""
    graph = copy.deepcopy(graph)
    # arm-scoped filename prefixes
    for nid, n in graph.items():
        if n["class_type"] == "SaveImage":
            n["inputs"]["filename_prefix"] = (
                n["inputs"]["filename_prefix"].replace("%ARM%", f"{batch}/{arm}"))
            if not n["inputs"]["filename_prefix"].startswith(f"{batch}/{arm}"):
                n["inputs"]["filename_prefix"] = f"{batch}/{arm}/" + n["inputs"]["filename_prefix"]
    armdir = f"{RES}/{batch}/{arm}"
    os.makedirs(armdir, exist_ok=True)
    json.dump(graph, open(f"{armdir}/api_graph.json", "w"), indent=1, sort_keys=True)
    t0 = time.time()
    r = _req("/prompt", {"prompt": graph})
    pid = r["prompt_id"]
    if r.get("node_errors"):
        json.dump(r, open(f"{armdir}/submit_errors.json", "w"), indent=1)
        raise RuntimeError(f"{arm}: node_errors on submit: {list(r['node_errors'])[:5]}")
    hist = None
    while time.time() - t0 < timeout:
        time.sleep(3)
        h = _req(f"/history/{pid}")
        if h and pid in h:
            hist = h[pid]
            st = hist.get("status", {})
            if st.get("completed") or st.get("status_str") == "error":
                break
    if hist is None:
        raise RuntimeError(f"{arm}: no history after {timeout}s")
    json.dump(hist, open(f"{armdir}/history.json", "w"), indent=1)
    st = hist.get("status", {})
    ok = st.get("completed", False)
    msgs = {m[0]: m[1] for m in st.get("messages", []) if len(m) > 1}
    t_start = msgs.get("execution_start", {}).get("timestamp")
    t_done = (msgs.get("execution_success", {}) or msgs.get("execution_error", {})).get("timestamp")
    exec_s = (t_done - t_start) / 1000.0 if t_start and t_done else None
    cached = []
    for m in st.get("messages", []):
        if m[0] == "execution_cached":
            cached = m[1].get("nodes", [])
    meta = {"arm": arm, "batch": batch, "ok": ok, "exec_s": exec_s,
            "cached_nodes": len(cached), "prompt_id": pid,
            "outputs_dir": f"{OUT}/{batch}/{arm}",
            "status_str": st.get("status_str")}
    json.dump(meta, open(f"{armdir}/meta.json", "w"), indent=1)
    if not ok:
        raise RuntimeError(f"{arm}: render failed, see {armdir}/history.json")
    return exec_s, hist


if __name__ == "__main__":
    boot()
    print("server up")
