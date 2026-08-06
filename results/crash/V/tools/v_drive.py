#!/usr/bin/env python3
"""TRACK V driver. Server 127.0.0.1:18188 ONLY. Never touches :28191.

Rules enforced here:
  * POST /free before EVERY arm, then POLL until the worker has acted on it,
    then REJECT the arm if /history still reports execution_cached != []
  * fresh client_id per arm
  * /history/<prompt_id> kept verbatim
  * NEVER delete a queue item, never clear the queue

Beyond Track A's driver it also records the websocket `executing` stream, which
is the only place this ComfyUI reports WHICH nodes ran -- /history carries
`outputs`/`meta` for output nodes only. Acceptance check D ("the eyes stage
actually ran") is read off that list.
"""
import json, os, time, uuid, threading, urllib.request, shutil

SERVER = "127.0.0.1:18188"
ROOT = "/workspace/nsfw-fix/results/crash/V"
COMFY_OUT = "/workspace/ComfyUI/output"


def _req(path, data=None, method=None, timeout=180):
    url = f"http://{SERVER}{path}"
    body = json.dumps(data).encode() if data is not None else None
    hdrs = {"Content-Type": "application/json"} if data is not None else {}
    r = urllib.request.Request(url, data=body, headers=hdrs, method=method)
    with urllib.request.urlopen(r, timeout=timeout) as f:
        raw = f.read()
    if not raw:
        return None
    try:
        return json.loads(raw)
    except Exception:
        return raw.decode(errors="replace")


def free(wait=90.0):
    """POST /free, then wait until the worker has ACTED on it.

    /free only sets flags that ComfyUI's prompt worker consumes between prompts,
    so returning as soon as the HTTP call succeeds is what produced this
    project's long-standing "server poisoning" (an arm executing against the old
    cache). Waiting for an absolute VRAM figure is wrong on a shared box -- this
    GPU also carries :28191 and :31910 -- so instead: wait for VRAM to come back
    and then settle, i.e. two consecutive identical readings after it has stopped
    rising. Coldness is still *verified* afterwards from `execution_cached`, which
    is the acceptance criterion; this only decides how long to wait first.
    """
    before = _req("/system_stats")["devices"][0]["vram_free"]
    _req("/free", {"unload_models": True, "free_memory": True})
    t0 = time.time()
    dev = None
    prev = None
    stable = 0
    while time.time() - t0 < wait:
        time.sleep(2.0)
        dev = _req("/system_stats")["devices"][0]
        v = dev["vram_free"]
        if prev is not None and v == prev:
            stable += 1
        else:
            stable = 0
        prev = v
        if stable >= 2 and (time.time() - t0) >= 8.0:
            break
    return {"vram_free": dev["vram_free"], "vram_free_before": before,
            "free_wait_s": round(time.time() - t0, 1)}


class WSRecorder(threading.Thread):
    """Records every ws message for one client_id. `executed` is the ordered list
    of node ids the server announced it was executing."""

    def __init__(self, client_id):
        super().__init__(daemon=True)
        self.client_id = client_id
        self.executed = []
        self.msgs = []
        self.stop_flag = threading.Event()
        self.ready = threading.Event()
        self.error = None

    def run(self):
        try:
            from websockets.sync.client import connect
            url = f"ws://{SERVER}/ws?clientId={self.client_id}"
            with connect(url, open_timeout=30, max_size=None) as ws:
                self.ready.set()
                while not self.stop_flag.is_set():
                    try:
                        m = ws.recv(timeout=2.0)
                    except TimeoutError:
                        continue
                    if isinstance(m, (bytes, bytearray)):
                        continue
                    try:
                        d = json.loads(m)
                    except Exception:
                        continue
                    if d.get("type") == "progress":
                        continue
                    self.msgs.append(d)
                    if d.get("type") == "executing":
                        n = (d.get("data") or {}).get("node")
                        if n is not None:
                            self.executed.append(n)
        except Exception as e:                      # never let ws failure kill an arm
            self.error = f"{type(e).__name__}: {e}"
            self.ready.set()


def wait(prompt_id, poll=5, limit=3600):
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


def run_arm(name, graph, note="", tokens=None, require_cold=True, _attempt=1):
    tag = name if _attempt == 1 else f"{name}__warm{_attempt}"
    m = _run_once(tag, graph, note, tokens)
    if require_cold and m.get("cached") not in (0, None) and _attempt < 4:
        print(f"[{name}] NOT COLD (cached={m['cached']}) -- discarded, re-running", flush=True)
        return run_arm(name, graph, note, tokens, require_cold, _attempt + 1)
    return m


def _run_once(name, graph, note, tokens):
    d = os.path.join(ROOT, "arms", name)
    os.makedirs(d, exist_ok=True)
    os.makedirs(os.path.join(ROOT, "history"), exist_ok=True)
    json.dump(graph, open(os.path.join(d, "api_graph.json"), "w"), indent=1)

    q = _req("/queue")
    qbefore = [len(q["queue_running"]), len(q["queue_pending"])]
    vram = free()
    cid = f"trackV-{name}-{uuid.uuid4().hex[:8]}"
    rec = WSRecorder(cid)
    rec.start()
    rec.ready.wait(timeout=35)
    t0 = time.time()
    pid = _req("/prompt", {"prompt": graph, "client_id": cid})["prompt_id"]
    print(f"[{name}] {pid} cid={cid} q={qbefore} vram_free={vram['vram_free']/2**30:.1f}GiB", flush=True)
    hist = wait(pid)
    wall = round(time.time() - t0, 1)
    time.sleep(2.0)
    rec.stop_flag.set()
    rec.join(timeout=10)

    if hist is None:
        meta = {"arm": name, "prompt_id": pid, "client_id": cid, "status": "TIMEOUT-WAIT",
                "wall_seconds": wall, "note": note, "tokens": tokens}
        json.dump(meta, open(os.path.join(d, "meta.json"), "w"), indent=1)
        print(f"[{name}] TIMEOUT", flush=True)
        return meta

    json.dump(hist, open(os.path.join(ROOT, "history", f"{name}__{pid}.json"), "w"), indent=1)
    json.dump({"executed": rec.executed, "ws_error": rec.error, "messages": rec.msgs},
              open(os.path.join(d, "ws.json"), "w"), indent=1)
    s = summarize(hist)
    meta = {"arm": name, "prompt_id": pid, "client_id": cid, "wall_seconds": wall,
            "queue_before": qbefore, "vram_free_after_free": vram["vram_free"],
            "free_wait_s": vram.get("free_wait_s"),
            "note": note, "tokens": tokens,
            "executed_nodes": rec.executed, "ws_error": rec.error, **s}
    if "620:106" in graph:
        meta["text_106"] = graph["620:106"]["inputs"]["text"]
    for nid in ("620:110", "620:114"):
        if nid in graph:
            meta[nid] = {k: graph[nid]["inputs"][k] for k in ("device", "denoise")
                         if k in graph[nid]["inputs"]}
    json.dump(meta, open(os.path.join(d, "meta.json"), "w"), indent=1)
    for im in s["images"]:
        src = os.path.join(COMFY_OUT, im.get("subfolder", ""), im["filename"])
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(d, f"n{im['node'].replace(':', '_')}__{im['filename']}"))
    print(f"[{name}] {s['status']} exec={s['exec_seconds']}s cached={s['cached']} "
          f"err={s['error_node']} nodes_exec={len([x for x in rec.executed if x])} "
          f"eyes406={'622:406' in rec.executed} imgs={[i['filename'] for i in s['images']]}", flush=True)
    return meta


def done(name):
    """True if this arm already has a recorded, cold, completed result."""
    p = os.path.join(ROOT, "arms", name, "meta.json")
    if not os.path.exists(p):
        return False
    m = json.load(open(p))
    return m.get("status") in ("success", "error") and m.get("cached") == 0


def run_set(arms, mkfn):
    """arms: list of (name, tokens, note, kwargs-for-mkfn). Resumable."""
    for name, tokens, note, kw in arms:
        if done(name):
            print(f"[{name}] already recorded -- skipping", flush=True)
            continue
        run_arm(name, mkfn(**kw), tokens=tokens, note=note)
    print("RUNSET-DONE", flush=True)
