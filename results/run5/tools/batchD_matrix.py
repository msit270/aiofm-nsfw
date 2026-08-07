#!/usr/bin/env python3
"""Black-render experiment matrix (agent D). Each ARM = fresh cold boot with
specific CLI flags/env, replaying a fixed probe set of known-failing graphs;
count black frames / black faces per boot. Probe set covers both suspected
limbs per boot: zref_* use GPU CLIP (TE limb), pipeline arms use cpu CLIP
(UNET limb). Boots are serialized; server killed between arms."""
import sys, os, time, json, subprocess, signal, copy
import urllib.request
import numpy as np
from PIL import Image
sys.path.insert(0, "/workspace/run5/tools")
import r5
from r5 import zit_simple, pipeline_graph, STD_TAPS, FACE_PROMPT, buyer_values
from candidates import luna_z, photo_config, ZTAPS

OUT = "/workspace/run5/output"
RES = "/workspace/nsfw-quality/results/run5/Dmatrix"
os.makedirs(RES, exist_ok=True)
PT = ("photorealistic portrait photograph of a young woman standing in soft "
      "window light, natural skin texture with visible pores, detailed eyes, "
      "detailed hands at her sides, looking at the camera, 85mm lens, shallow "
      "depth of field")
CU = ("close-up beauty photograph of a young woman, face and bare shoulders "
      "filling the frame, direct eye contact, soft window light, natural skin "
      "texture with visible pores and freckles, shot on 85mm f1.8")


def kill_server():
    subprocess.run(["pkill", "-f", "main.py --port 19188"], capture_output=True)
    time.sleep(4)


def boot_with(extra_args, env_extra):
    kill_server()
    env = dict(os.environ)
    env.update(env_extra)
    p = subprocess.Popen(
        [sys.executable, "main.py", "--port", "19188", "--disable-auto-launch",
         "--output-directory", OUT] + extra_args,
        cwd="/workspace/ComfyUI", stdout=open("/workspace/run5/server_19188.log", "a"),
        stderr=subprocess.STDOUT, env=env, start_new_session=True)
    for _ in range(150):
        time.sleep(2)
        if r5.server_up():
            return p.pid
    raise RuntimeError("boot failed")


def probes():
    bv = buyer_values()
    pb = json.loads(bv["483"]["inputs"]["prompt_batch_data"])
    pb[0]["positive_prompt"] = PT
    return [
        ("zref_P_canary", zit_simple(FACE_PROMPT, 12345, arm="img")),      # never failed
        ("zref_PT", zit_simple(PT.replace("a young woman", "luna, a young woman"), 12345, arm="img")),
        ("zref_CU", zit_simple(CU.replace("a young woman", "luna, a young woman"), 12345, arm="img")),
        ("lunaz30", luna_z(base_steps=30, base_cfg=2.0, taps={})),          # 3/4 failer
        ("A0_PT", pipeline_graph(taps={}, overrides={"483": {"prompt_batch_data": json.dumps(pb)}})),  # 2/2 failer
    ]


def frame_state(arm_dir):
    """healthy / black_frame / black_face for the newest png set in arm_dir."""
    import glob, cv2
    worst = "healthy"
    for p in glob.glob(arm_dir + "/**/*.png", recursive=True):
        im = cv2.imread(p)
        if im is None:
            continue
        if im.max() == 0 or im.mean() < 8:
            return "black_frame"
        # black-face: central-upper region almost black while frame isn't
        h, w = im.shape[:2]
        face = im[int(h*0.05):int(h*0.5), int(w*0.25):int(w*0.75)]
        dark = (face.max(axis=2) < 10).mean()
        if dark > 0.12:
            worst = "black_face"
    return worst


ARMS = [
    ("baseline", [], {}, 2),
    ("no_xformers", ["--use-pytorch-cross-attention"], {}, 2),
    ("no_async_offload", ["--disable-async-offload"], {}, 2),
    ("cublas_ws", [], {"CUBLAS_WORKSPACE_CONFIG": ":4096:8"}, 2),
    ("force_fp32", ["--force-fp32"], {}, 1),
]

results = json.load(open(f"{RES}/matrix.json")) if os.path.exists(f"{RES}/matrix.json") else {}
for arm_name, args, env, nboots in ARMS:
    for b in range(nboots):
        key = f"{arm_name}/boot{b}"
        if key in results:
            continue
        print(f"=== {key} args={args} env={env}", flush=True)
        boot_with(args, env)
        row = {"args": args, "env": env, "probes": {}}
        for pname, graph in probes():
            tag = f"Dmx_{arm_name}_b{b}_{pname}"
            try:
                ex, _ = r5.run_arm("Dmx", tag, copy.deepcopy(graph), timeout=900)
                state = frame_state(f"{OUT}/Dmx/{tag}")
                row["probes"][pname] = {"exec_s": round(ex, 1), "state": state}
                print(f"  [{pname}] {state} ({ex:.0f}s)", flush=True)
            except Exception as e:
                row["probes"][pname] = {"error": str(e)[:200]}
                print(f"  [{pname}] ERROR {e}", flush=True)
        results[key] = row
        json.dump(results, open(f"{RES}/matrix.json", "w"), indent=1)
kill_server()
print("matrix done", flush=True)
# summary
for k, v in results.items():
    states = [p.get("state", "ERR") for p in v["probes"].values()]
    print(k, "->", states, flush=True)
