#!/usr/bin/env python3
"""Track A driver. Server 18188 ONLY. Never touches 28191.

Rules enforced here (see brief):
  * POST /free {"unload_models":true,"free_memory":true} before EVERY arm
  * distinct client_id per arm
  * capture /history/<prompt_id> verbatim for EVERY arm
  * NEVER delete a queue item / clear the queue
"""
import json, os, sys, time, uuid, urllib.request, urllib.error, shutil

SERVER = "127.0.0.1:18188"
ROOT = "/workspace/nsfw-fix/results/crash/A"
COMFY_OUT = "/workspace/ComfyUI/output"
COMFY_IN = "/workspace/ComfyUI/input"


def _req(path, data=None, method=None, timeout=120):
    url = f"http://{SERVER}{path}"
    body = None
    hdrs = {}
    if data is not None:
        body = json.dumps(data).encode()
        hdrs["Content-Type"] = "application/json"
    r = urllib.request.Request(url, data=body, headers=hdrs, method=method)
    with urllib.request.urlopen(r, timeout=timeout) as f:
        raw = f.read()
    if not raw:
        return None
    try:
        return json.loads(raw)
    except Exception:
        return raw.decode(errors="replace")


def free(min_free_gib=45.0, wait=45.0):
    """POST /free and then WAIT until the worker has actually acted on it.

    The flags set by /free are consumed by ComfyUI's prompt worker, not by the
    HTTP handler (main.py prompt_worker -> q.get_flags() -> e.reset()). If the
    next prompt is submitted before the worker gets round to them, it executes
    against the OLD cache -- observed once here as execution_cached: 16 on a
    control that then failed. So: poll until the VRAM has actually come back.
    """
    _req("/free", {"unload_models": True, "free_memory": True})
    t0 = time.time()
    dev = None
    while time.time() - t0 < wait:
        time.sleep(2.0)
        dev = _req("/system_stats")["devices"][0]
        if dev["vram_free"] / 2**30 >= min_free_gib:
            break
    return {"vram_free": dev["vram_free"], "torch_vram_free": dev["torch_vram_free"],
            "free_wait_s": round(time.time() - t0, 1)}


def queue_state():
    q = _req("/queue")
    return len(q["queue_running"]), len(q["queue_pending"])


def submit(graph, client_id):
    return _req("/prompt", {"prompt": graph, "client_id": client_id})


def wait(prompt_id, poll=5, limit=3000):
    t0 = time.time()
    while time.time() - t0 < limit:
        h = _req(f"/history/{prompt_id}")
        if h and prompt_id in h:
            st = h[prompt_id].get("status", {})
            if st.get("completed") is True or st.get("status_str") in ("success", "error"):
                return h[prompt_id]
        time.sleep(poll)
    return None


def summarize(hist):
    """Pull the fields the brief cares about out of a /history entry."""
    out = {"status": None, "exec_seconds": None, "cached": None, "cached_ids": [],
           "error": None, "error_node": None, "error_type": None, "images": []}
    st = hist.get("status", {})
    out["status"] = st.get("status_str")
    t_start = t_end = None
    for m in st.get("messages", []):
        kind, payload = m[0], m[1]
        if kind == "execution_cached":
            out["cached_ids"] = payload.get("nodes", [])
            out["cached"] = len(out["cached_ids"])
        if kind == "execution_start":
            t_start = payload.get("timestamp")
        if kind in ("execution_success", "execution_error", "execution_interrupted"):
            t_end = payload.get("timestamp")
        if kind == "execution_error":
            out["error_node"] = payload.get("node_id")
            out["error_type"] = payload.get("node_type")
            out["error"] = f"{payload.get('exception_type')}: {payload.get('exception_message')}"
    if t_start and t_end:
        out["exec_seconds"] = round((t_end - t_start) / 1000.0, 1)
    for nid, o in (hist.get("outputs") or {}).items():
        for im in o.get("images", []):
            out["images"].append({"node": nid, **im})
    return out


def prune(graph, outputs):
    """Keep only the given output nodes and their ancestors."""
    keep = set()

    def walk(nid):
        if nid in keep or nid not in graph:
            return
        keep.add(nid)
        for v in graph[nid]["inputs"].values():
            if isinstance(v, list) and len(v) == 2 and isinstance(v[0], str):
                walk(v[0])
    for o in outputs:
        walk(o)
    return {k: v for k, v in graph.items() if k in keep}


def run_arm(name, graph, note="", copy_images=True, require_cold=True, _attempt=1):
    """One arm. /free first, then submit. If the run came back with a warm cache
    (execution_cached non-empty) the arm is NOT cold and is re-run rather than
    reported -- see free() for why that can happen."""
    m = _run_arm_once(name if _attempt == 1 else f"{name}__warm{_attempt}",
                      graph, note, copy_images)
    if require_cold and m.get("cached") not in (0, None) and _attempt < 3:
        print(f"[{name}] NOT COLD (cached={m['cached']}) -- discarding and re-running", flush=True)
        return run_arm(name, graph, note, copy_images, require_cold, _attempt + 1)
    return m


def _run_arm_once(name, graph, note="", copy_images=True):
    d = os.path.join(ROOT, "arms", name)
    os.makedirs(d, exist_ok=True)
    json.dump(graph, open(os.path.join(d, "api_graph.json"), "w"), indent=1)

    r, p = queue_state()
    vram = free()
    cid = f"trackA-{name}-{uuid.uuid4().hex[:8]}"
    t0 = time.time()
    sub = submit(graph, cid)
    pid = sub["prompt_id"]
    print(f"[{name}] submitted {pid} cid={cid} queue_before=({r},{p}) vram_free={vram['vram_free']/2**30:.1f}GiB", flush=True)
    hist = wait(pid)
    wall = round(time.time() - t0, 1)
    if hist is None:
        meta = {"arm": name, "prompt_id": pid, "client_id": cid, "status": "TIMEOUT-WAIT",
                "wall_seconds": wall, "note": note}
        json.dump(meta, open(os.path.join(d, "meta.json"), "w"), indent=1)
        print(f"[{name}] TIMEOUT", flush=True)
        return meta
    json.dump(hist, open(os.path.join(ROOT, "history", f"{name}__{pid}.json"), "w"), indent=1)
    s = summarize(hist)
    meta = {"arm": name, "prompt_id": pid, "client_id": cid, "wall_seconds": wall,
            "queue_before": [r, p], "vram_free_after_free": vram["vram_free"],
            "note": note, **s}
    if "620:106" in graph:
        meta["text_106"] = graph["620:106"]["inputs"]["text"]
    json.dump(meta, open(os.path.join(d, "meta.json"), "w"), indent=1)
    if copy_images:
        for im in s["images"]:
            src = os.path.join(COMFY_OUT, im.get("subfolder", ""), im["filename"])
            if os.path.exists(src):
                dst = os.path.join(d, f"n{im['node'].replace(':','_')}__{im['filename']}")
                shutil.copy2(src, dst)
    print(f"[{name}] {s['status']} exec={s['exec_seconds']}s cached={s['cached']} "
          f"err={s['error_node']} {(s['error'] or '')[:80]} imgs={[i['filename'] for i in s['images']]}", flush=True)
    return meta
