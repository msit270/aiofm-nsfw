#!/usr/bin/env python3
"""TRACK P — per-node cold timing.

Why this exists. A whole-render cold delta is ~300 s of which most is model
loading, so a lever worth a fraction of a second is invisible in it. The
websocket emits an "executing" message each time the executor moves to a new
node, so timestamping those transitions gives the duration of every node
individually. That measures the two levers where they actually act:

    620:114  FaceDetailer   <- the denoise lever
    620:110  CLIPLoader     <- the device lever

Same coldness discipline as drive.py: empty queue, /free, and execution_cached
confirmed out of /history rather than trusted from the free.

Usage:  node_time.py <arm> [<arm> ...]
"""
import json, os, sys, time, urllib.request, uuid
from websockets.sync.client import connect

URL  = "http://127.0.0.1:28191"
WS   = "ws://127.0.0.1:28191/ws"
S    = "/tmp/claude-0/-workspace-nsfw-fix/47375d2b-87bd-4073-a1e2-67796f8c1345/scratchpad/P"
OUTD = "/workspace/comfy-r2gate3/output"


def post(path, obj):
    req = urllib.request.Request(URL + path, data=json.dumps(obj).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        b = r.read()
        return r.status, (json.loads(b) if b.strip().startswith(b"{") else b.decode())


def get(path):
    with urllib.request.urlopen(URL + path, timeout=180) as r:
        return json.loads(r.read())


def run(arm, tag):
    g = json.load(open(f"{S}/api/{arm}_submitted.json"))
    cid = f"trackP-nodetime-{uuid.uuid4().hex[:8]}"

    while True:
        q = get("/queue")
        if not q.get("queue_running") and not q.get("queue_pending"):
            break
        time.sleep(3)

    # /free is NOT synchronous. server.py:976-981 only sets a flag; main.py:284
    # consumes it in the prompt worker, and execution.py:1154-1159 shows the
    # worker only returns from q.get() -- and therefore only reaches
    # get_flags() -- when it was given a timeout. main.py:246 sets a timeout
    # only while need_gc is true, i.e. for gc_collect_interval = 10 s after a
    # render. Post the free and then wait past that window so at least one tick
    # consumes it, and confirm the unload actually happened via torch_vram_free
    # rather than trusting the 200.
    def torch_free():
        d = get("/system_stats")["devices"][0]
        return d["torch_vram_free"], d["torch_vram_total"]

    post("/free", {"unload_models": True, "free_memory": True})
    t_free = time.time()
    while time.time() - t_free < 90:
        time.sleep(3)
        fr, tot = torch_free()
        # unload_all_models() returns the pool to torch: free/total goes high.
        if tot == 0 or fr / max(tot, 1) > 0.85:
            break
    fr, tot = torch_free()
    print(f"  after /free: torch_vram_free={fr/2**30:.1f}/{tot/2**30:.1f} GiB "
          f"({time.time()-t_free:.0f}s)", flush=True)

    events = []          # (monotonic, node_or_None)
    with connect(f"{WS}?clientId={cid}", max_size=None, open_timeout=30) as ws:
        st, resp = post("/prompt", {"prompt": g, "client_id": cid})
        assert st == 200, (st, resp)
        pid = resp["prompt_id"]
        print(f"  {tag}/{arm} pid={pid}", flush=True)
        t0 = time.monotonic()
        cached = None
        while True:
            try:
                msg = ws.recv(timeout=1800)
            except TimeoutError:
                print("  ws timeout"); break
            if isinstance(msg, bytes):
                continue                       # preview frames
            m = json.loads(msg)
            d = m.get("data") or {}
            if d.get("prompt_id") not in (None, pid):
                continue
            t = time.monotonic() - t0
            if m["type"] == "executing":
                events.append((t, d.get("node")))
                if d.get("node") is None:
                    break
            elif m["type"] == "execution_cached":
                cached = d.get("nodes", [])
            elif m["type"] in ("execution_success", "execution_error", "execution_interrupted"):
                events.append((t, None))
                if m["type"] != "execution_success":
                    print(f"  !! {m['type']}: {json.dumps(d)[:300]}")
                break

    hist = get(f"/history/{pid}").get(pid, {})
    msgs = hist.get("status", {}).get("messages", [])
    hcached = []
    for mm in msgs:
        if isinstance(mm, list) and mm[0] == "execution_cached":
            hcached = mm[1].get("nodes", [])
    ts = {}
    for mm in msgs:
        if isinstance(mm, list) and len(mm) == 2 and isinstance(mm[1], dict) and "timestamp" in mm[1]:
            ts.setdefault(mm[0], mm[1]["timestamp"])
    exec_s = round((ts["execution_success"] - ts["execution_start"]) / 1000.0, 1) \
        if "execution_success" in ts and "execution_start" in ts else None

    # duration of node i = t(i+1) - t(i)
    durs = {}
    for i in range(len(events) - 1):
        n = events[i][1]
        if n is None:
            continue
        durs[n] = durs.get(n, 0.0) + (events[i + 1][0] - events[i][0])

    out = {"arm": arm, "tag": tag, "prompt_id": pid, "client_id": cid,
           "exec_seconds": exec_s, "cached_nodes_ws": cached,
           "cached_nodes_history": hcached, "cold": (hcached == []),
           "status": hist.get("status", {}).get("status_str"),
           "node_durations": durs,
           "n_transitions": len(events)}
    os.makedirs(f"{S}/nodetime", exist_ok=True)
    json.dump(out, open(f"{S}/nodetime/{tag}_{arm}.json", "w"), indent=1)

    top = sorted(durs.items(), key=lambda kv: -kv[1])[:6]
    print(f"  exec={exec_s}s cold={hcached == []} status={out['status']}  "
          f"114={durs.get('620:114', float('nan')):.2f}s 110={durs.get('620:110', float('nan')):.2f}s", flush=True)
    print(f"    slowest: {', '.join(f'{k}={v:.1f}s' for k, v in top)}", flush=True)
    return out


if __name__ == "__main__":
    tag = os.environ.get("TAG", "n1")
    for arm in sys.argv[1:]:
        for attempt in (1, 2, 3):
            r = run(arm, f"{tag}" if attempt == 1 else f"{tag}retry{attempt}")
            if r["cold"] and r["status"] == "success":
                break
            print(f"  !! {arm} came back cold={r['cold']} status={r['status']} — "
                  f"discarding and re-running (attempt {attempt})", flush=True)
