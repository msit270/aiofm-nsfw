#!/usr/bin/env python3
"""TRACK P cold-timing driver.  NEVER interrupts, NEVER clears the queue.

Design notes that matter for whether the number is defensible:

  * Latin square ordering. Three arms over three rounds, each arm occupying each
    position exactly once. Cold render time here is dominated by model loading and
    the GPU is shared with two other ComfyUI servers, so a block-ordered run would
    confound arm with drift. Rotating the order balances position exactly.

  * Coldness is CONFIRMED, not assumed. /free only sets flags the prompt worker
    consumes later, so every run reads execution_cached back out of /history. A run
    that comes back non-cold is recorded as INVALID and the cell is re-run.

  * Contention is recorded, not hoped away. vram_free and the other servers' GPU
    memory are sampled at submit time so a slow run can be checked against load.

  * Raw /history is saved per run. R1 did not do this and it cost a provenance
    argument over which prompt_id produced which arm.
"""
import json, os, re, shutil, subprocess, sys, time, urllib.request

URL     = "http://127.0.0.1:28191"
OUTDIR  = "/workspace/comfy-r2gate3/output"
S       = "/tmp/claude-0/-workspace-nsfw-fix/47375d2b-87bd-4073-a1e2-67796f8c1345/scratchpad/P"
CLIENT  = "trackP-pack-timing"
MYPID   = 144284           # the ComfyUI serving :28191

ARMS = {
    "P_D080":    "#114 denoise 0.80 (old shipping value), #110 device cpu",
    "P_D035":    "#114 denoise 0.35 (as committed 8d166e0), #110 device cpu",
    "P_CLIPDEF": "#114 denoise 0.35, #110 device default (pre-7ce1539)",
}
# Latin square: each arm hits each position once.
ROUNDS = [
    ["P_D080", "P_D035", "P_CLIPDEF"],
    ["P_D035", "P_CLIPDEF", "P_D080"],
    ["P_CLIPDEF", "P_D080", "P_D035"],
]


def post(path, obj):
    req = urllib.request.Request(URL + path, data=json.dumps(obj).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        b = r.read()
        return r.status, (json.loads(b) if b.strip().startswith(b"{") else b.decode(errors="replace"))


def get(path):
    with urllib.request.urlopen(URL + path, timeout=180) as r:
        return json.loads(r.read())


def queue_state():
    q = get("/queue")
    return len(q.get("queue_running", [])), len(q.get("queue_pending", []))


def gpu_sample():
    """Other processes' GPU memory + my own, and free VRAM as ComfyUI sees it."""
    out = {"others_mib": {}, "mine_mib": None, "vram_free": None, "err": None}
    try:
        r = subprocess.run(["nvidia-smi", "--query-compute-apps=pid,used_memory",
                            "--format=csv,noheader,nounits"],
                           capture_output=True, text=True, timeout=30)
        for line in r.stdout.strip().splitlines():
            m = re.match(r"\s*(\d+)\s*,\s*(\d+)", line)
            if not m:
                continue
            pid, mib = int(m.group(1)), int(m.group(2))
            if pid == MYPID:
                out["mine_mib"] = mib
            else:
                out["others_mib"][str(pid)] = mib
    except Exception as e:                                    # noqa: BLE001
        out["err"] = repr(e)
    try:
        out["vram_free"] = get("/system_stats")["devices"][0]["vram_free"]
    except Exception as e:                                    # noqa: BLE001
        out["err"] = (out["err"] or "") + repr(e)
    return out


def run_once(arm, round_no, pos, seq):
    name = f"{arm}__r{round_no}p{pos}"
    d = os.path.join(S, "runs", name)
    os.makedirs(d, exist_ok=True)
    g = json.load(open(os.path.join(S, "api", f"{arm}_submitted.json")))

    # Shared server. Wait for a genuinely empty queue; never interrupt, never clear.
    t_wait = time.time()
    while True:
        r, p = queue_state()
        if (r, p) == (0, 0):
            break
        if time.time() - t_wait > 5400:
            raise SystemExit(f"gave up waiting for empty queue (running={r} pending={p})")
        time.sleep(3)
    waited = round(time.time() - t_wait, 1)

    st, _ = post("/free", {"unload_models": True, "free_memory": True})
    time.sleep(4)
    gpu_pre = gpu_sample()

    before = set(os.listdir(OUTDIR)) if os.path.isdir(OUTDIR) else set()
    t0 = time.time()
    stp, resp = post("/prompt", {"prompt": g, "client_id": CLIENT})
    assert stp == 200, (stp, resp)
    pid = resp["prompt_id"]
    print(f"[{seq}] {name} submitted pid={pid} free={st} queue_wait={waited}s "
          f"vram_free={gpu_pre['vram_free']} others={gpu_pre['others_mib']}", flush=True)

    hist = None
    while True:
        time.sleep(8)
        h = get(f"/history/{pid}")
        if pid in h and h[pid].get("status", {}).get("completed") is not None:
            hist = h[pid]
            if hist["status"].get("completed") or hist["status"].get("status_str") == "error":
                break
        if time.time() - t0 > 3600:
            print(f"[{seq}] {name} TIMEOUT 3600 s", flush=True)
            return {"arm": arm, "name": name, "prompt_id": pid, "valid": False,
                    "invalid_reason": "timeout", "exec_seconds": None}
    wall = round(time.time() - t0, 1)
    gpu_post = gpu_sample()

    json.dump(hist, open(os.path.join(S, "history", f"{name}__{pid}.json"), "w"), indent=1)

    msgs = hist.get("status", {}).get("messages", [])
    ts = {}
    for m in msgs:
        if isinstance(m, list) and len(m) == 2 and isinstance(m[1], dict) and "timestamp" in m[1]:
            ts.setdefault(m[0], m[1]["timestamp"])
    exec_s = None
    if "execution_start" in ts and "execution_success" in ts:
        exec_s = round((ts["execution_success"] - ts["execution_start"]) / 1000.0, 1)
    cached = []
    for m in msgs:
        if isinstance(m, list) and m[0] == "execution_cached":
            cached = m[1].get("nodes", [])

    status = hist["status"].get("status_str")
    imgs = []
    for nid, o in (hist.get("outputs") or {}).items():
        for im in o.get("images", []):
            if im.get("type") == "output":
                imgs.append((nid, im["filename"], im.get("subfolder", "")))
    copied = []
    for nid, fn, sub in imgs:
        src = os.path.join(OUTDIR, sub, fn) if sub else os.path.join(OUTDIR, fn)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(d, fn))
            copied.append(fn)

    valid, why = True, None
    if status != "success":
        valid, why = False, f"status={status}"
    elif cached:
        valid, why = False, f"not cold: execution_cached has {len(cached)} nodes"
    elif exec_s is None:
        valid, why = False, "no execution_start/execution_success pair"

    meta = {"arm": arm, "name": name, "round": round_no, "pos": pos, "seq": seq,
            "changed": ARMS[arm], "prompt_id": pid, "client_id": CLIENT,
            "api_nodes": len(g), "free_status": st, "queue_wait_s": waited,
            "exec_seconds": exec_s, "wall_seconds": wall,
            "cached_nodes": len(cached), "cached_node_ids": cached,
            "status": status, "images": copied,
            "gpu_pre": gpu_pre, "gpu_post": gpu_post,
            "valid": valid, "invalid_reason": why}
    json.dump(meta, open(os.path.join(d, "meta.json"), "w"), indent=2)
    print(f"[{seq}] {name} status={status} exec={exec_s}s wall={wall}s "
          f"cached={len(cached)} valid={valid} {why or ''} imgs={copied}", flush=True)
    return meta


if __name__ == "__main__":
    results = []
    seq = 0
    for rn, order in enumerate(ROUNDS, 1):
        for pos, arm in enumerate(order, 1):
            seq += 1
            m = run_once(arm, rn, pos, seq)
            results.append(m)
            json.dump(results, open(os.path.join(S, "results.json"), "w"), indent=1)
    print("\n==== DONE ====", flush=True)
    for m in results:
        print(f"  {m['name']:26s} exec={m.get('exec_seconds')} cached={m.get('cached_nodes')} "
              f"valid={m.get('valid')} {m.get('invalid_reason') or ''}", flush=True)
