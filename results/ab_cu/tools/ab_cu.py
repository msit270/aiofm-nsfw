#!/usr/bin/env python3
"""Owner A/B (post-run6): CLOSE-UP, one arm per unapplied candidate.

  A_base_CU    shipped/live config: USDU-617 denoise .25, res_multistep tiled
  B_den045_CU  USDU-617 denoise .25 -> .45      (run-6 LAND-CANDIDATE, +.049 on FB)
  C_s18ea_CU   euler_ancestral in BOTH tiled-refine slots (617 + 98), run-5 S18
               (cos .809 vs .799 on run-5 sheet; denoise stays .25/.08)

Same prompt (run-6 CU), same seed (12345), luna@1.0 both sides, /free
(unload_models + free_memory) before every arm = cache cleared, one render per
arm. Server 127.0.0.1:18188 — the supervised instance with the README
mitigation flags. All arms share one model composition (widget-only diffs), so
the run-6 black-frame interleave rule is not in play.

Gate before any submit: the A_base_CU graph must equal the committed run-6
baseline results/run6/P_CU/api_graph.json on every node and every input,
excepting only SaveImage.filename_prefix. Zero tolerance; SystemExit on diff.

Usage: ab_cu.py [--dry]   (--dry: build + gate only, no render)
"""
import json, os, sys, time, copy, glob, urllib.request
import numpy as np
from PIL import Image

SERVER = "127.0.0.1:18188"
OUT = "/workspace/ComfyUI/output"
RES = "/workspace/nsfw-quality/results/ab_cu"
P_CU_REF = "/workspace/nsfw-quality/results/run6/P_CU/api_graph.json"

CU = ("close-up beauty photograph of a young woman, face and bare shoulders "
      "filling the frame, direct eye contact, soft window light, natural skin "
      "texture with visible pores and freckles, shot on 85mm f1.8")

sys.path.insert(0, "/workspace/run5/tools")
from candidates import pc_final  # shipped 66-node graph builder (run-5 gated)
_bv = json.load(open("/workspace/nsfw-quality/results/run3/fresh/fresh-buyer-api_graph.json"))


def _req(path, data=None, timeout=120):
    url = f"http://{SERVER}{path}"
    body = json.dumps(data).encode() if data is not None else None
    hdrs = {"Content-Type": "application/json"} if data is not None else {}
    with urllib.request.urlopen(urllib.request.Request(url, data=body, headers=hdrs),
                                timeout=timeout) as f:
        raw = f.read()
    return json.loads(raw) if raw else None


def free():
    _req("/free", {"unload_models": True, "free_memory": True})


def pc_graph(prompt, seed=12345, negative=None):
    # verbatim from run6/tools/r6.py pc_graph
    g = pc_final(pick_list="0")
    g["116"]["inputs"]["lora_01"] = "luna.safetensors"
    pb = json.loads(g["483"]["inputs"]["prompt_batch_data"])
    pb[0]["positive_prompt"] = prompt
    pb[0]["seed"] = seed
    if negative is not None:
        pb[0]["negative_prompt"] = negative
    g["483"]["inputs"]["prompt_batch_data"] = json.dumps(pb)
    g["620:106"]["inputs"]["text"] = _bv["620:106"]["inputs"]["text"]
    for nid, n in g.items():
        if n["class_type"] == "SaveImage":
            n["inputs"]["filename_prefix"] = "%ARM%/img"
    return g


def gate_baseline(g):
    ref = json.load(open(P_CU_REF))
    diffs = []
    for nid in sorted(set(ref) | set(g)):
        if nid not in ref:
            diffs.append(f"node {nid} not in P_CU"); continue
        if nid not in g:
            diffs.append(f"node {nid} missing vs P_CU"); continue
        a, b = ref[nid], g[nid]
        if a["class_type"] != b["class_type"]:
            diffs.append(f"{nid}: class {a['class_type']} vs {b['class_type']}"); continue
        for k in sorted(set(a["inputs"]) | set(b["inputs"])):
            va, vb = a["inputs"].get(k), b["inputs"].get(k)
            if va != vb:
                if a["class_type"] == "SaveImage" and k == "filename_prefix":
                    continue
                diffs.append(f"{nid}.{k}: {va!r} vs {vb!r}")
    if diffs:
        raise SystemExit("BASELINE GATE FAIL vs run-6 P_CU:\n" + "\n".join(diffs))
    print("baseline gate PASS: A_base_CU == run-6 P_CU (modulo save prefix)", flush=True)


def build_arms():
    A = pc_graph(CU)
    gate_baseline(A)
    B = pc_graph(CU)
    B["619:617"]["inputs"]["denoise"] = 0.45          # exactly run-6 batch2 arm D
    C = pc_graph(CU)
    C["619:617"]["inputs"]["sampler_name"] = "euler_ancestral"
    C["587:98"]["inputs"]["sampler_name"] = "euler_ancestral"
    return [("A_base_CU", A), ("B_den045_CU", B), ("C_s18ea_CU", C)]


def blackcheck(arm):
    pngs = sorted(glob.glob(f"{OUT}/AB_CU/{arm}/**/*.png", recursive=True))
    rep = {}
    for p in pngs:
        a = np.asarray(Image.open(p).convert("RGB"), dtype=np.float32)
        rep[os.path.relpath(p, f"{OUT}/AB_CU/{arm}")] = {
            "mean": round(float(a.mean()), 2), "std": round(float(a.std()), 2),
            "size": list(Image.open(p).size)}
    black = [k for k, v in rep.items() if v["mean"] < 8.0 and v["std"] < 6.0]
    return rep, black


def run_arm(arm, graph, timeout=1500):
    graph = copy.deepcopy(graph)
    for nid, n in graph.items():
        if n["class_type"] == "SaveImage":
            n["inputs"]["filename_prefix"] = n["inputs"]["filename_prefix"].replace(
                "%ARM%", f"AB_CU/{arm}")
    armdir = f"{RES}/{arm}"
    os.makedirs(armdir, exist_ok=True)
    json.dump(graph, open(f"{armdir}/api_graph.json", "w"), indent=1, sort_keys=True)
    t0 = time.time()
    r = _req("/prompt", {"prompt": graph})
    pid = r["prompt_id"]
    if r.get("node_errors"):
        json.dump(r, open(f"{armdir}/submit_errors.json", "w"), indent=1)
        raise RuntimeError(f"{arm}: node_errors: {list(r['node_errors'])[:5]}")
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
    ts, td = (msgs.get("execution_start", {}).get("timestamp"),
              (msgs.get("execution_success", {}) or msgs.get("execution_error", {})).get("timestamp"))
    exec_s = (td - ts) / 1000.0 if ts and td else None
    rep, black = blackcheck(arm) if ok else ({}, [])
    meta = {"arm": arm, "ok": ok, "exec_s": exec_s, "prompt_id": pid,
            "images": rep, "black": black, "status_str": st.get("status_str")}
    json.dump(meta, open(f"{armdir}/meta.json", "w"), indent=1)
    if not ok:
        err = [m[1] for m in st.get("messages", []) if m[0] == "execution_error"]
        raise RuntimeError(f"{arm}: render failed: {str(err)[:300]}")
    if black:
        print(f"[{arm}] BLACK FRAMES: {black}", flush=True)
    return exec_s


if __name__ == "__main__":
    arms = build_arms()
    if "--dry" in sys.argv:
        print("dry run: arms built, gate passed, nothing submitted")
        sys.exit(0)
    for arm, g in arms:
        free()
        ex = run_arm(arm, g)
        print(f"[{arm}] ok exec={ex:.1f}s", flush=True)
    print("AB_CU done", flush=True)
