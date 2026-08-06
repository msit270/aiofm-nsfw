#!/usr/bin/env python3
"""TRACK B arm runner -- ComfyUI on 127.0.0.1:28191 ONLY.

One arm per invocation.  Always:
  1. POST /free {"unload_models":true,"free_memory":true}
  2. submit with a fresh client_id
  3. poll /history until the prompt reports terminal status
  4. save api_graph.json / history.json / meta.json  + any output images
  5. health-check every success (flat_frac, luma_sd) -- "success" is not a render

NEVER deletes or clears the queue.  NEVER touches 18188.
"""
import argparse, json, os, sys, time, uuid, urllib.request, urllib.error, urllib.parse, hashlib

SERVER = "127.0.0.1:28191"
ROOT = os.path.dirname(os.path.abspath(__file__))


def api(path, payload=None, timeout=60):
    url = f"http://{SERVER}{path}"
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data,
                                 headers={"Content-Type": "application/json"} if data else {})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read()
    return json.loads(raw) if raw else None


def free_server():
    api("/free", {"unload_models": True, "free_memory": True})
    time.sleep(3.0)


def set_path(graph, spec):
    """spec: '620:106.inputs.text=some value'  or  '620:165.inputs.detailer_hook=__DELETE__'"""
    key, _, val = spec.partition("=")
    parts = key.split(".")
    node_id, field = parts[0], parts[1:]
    assert node_id in graph, f"node {node_id} not in graph"
    cur = graph[node_id]
    for p in field[:-1]:
        cur = cur[p]
    leaf = field[-1]
    if val == "__DELETE__":
        assert leaf in cur, f"{key} not present, cannot delete"
        old = cur.pop(leaf)
    else:
        old = cur.get(leaf, "<absent>")
        # keep the JSON type of the existing value where it is a number
        if isinstance(old, bool):
            val = val.lower() in ("1", "true", "yes")
        elif isinstance(old, int) and not isinstance(old, bool):
            val = int(val) if val.lstrip("-").isdigit() else float(val)
        elif isinstance(old, float):
            val = float(val)
        cur[leaf] = val
    return key, old, (None if val == "__DELETE__" else cur.get(leaf))


def health(png_path):
    import numpy as np
    from PIL import Image
    Image.MAX_IMAGE_PIXELS = None
    im = Image.open(png_path).convert("RGB")
    a = np.asarray(im).astype(np.float32)
    luma = 0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]
    gx = np.abs(np.diff(luma, axis=1))
    gy = np.abs(np.diff(luma, axis=0))
    g = np.zeros_like(luma)
    g[:, :-1] += gx
    g[:-1, :] += gy
    flat_frac = float((g == 0).mean())
    luma_sd = float(luma.std())
    return {
        "file": os.path.basename(png_path),
        "size": list(im.size),
        "flat_frac": round(flat_frac, 6),
        "luma_sd": round(luma_sd, 3),
        "luma_mean": round(float(luma.mean()), 3),
        "has_nan": bool(np.isnan(a).any()),
        "suspect_poisoned": bool(flat_frac > 0.20 or luma_sd < 8.0),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", required=True)
    ap.add_argument("--base", required=True)
    ap.add_argument("--set", action="append", default=[])
    ap.add_argument("--note", default="")
    ap.add_argument("--expect", default="", help="crash|clean|unknown -- recorded, not enforced")
    ap.add_argument("--timeout", type=int, default=1500)
    a = ap.parse_args()

    outdir = os.path.join(ROOT, a.arm)
    os.makedirs(outdir, exist_ok=True)

    graph = json.load(open(a.base))
    changes = []
    for spec in a.set:
        k, old, new = set_path(graph, spec)
        changes.append({"path": k, "from": old, "to": new})
        print(f"  SET {k}: {json.dumps(old)[:90]} -> {json.dumps(new)[:90]}")

    json.dump(graph, open(os.path.join(outdir, "api_graph.json"), "w"), indent=1)
    gsha = hashlib.sha256(json.dumps(graph, sort_keys=True).encode()).hexdigest()

    q = api("/queue")
    if q["queue_running"] or q["queue_pending"]:
        print("QUEUE NOT EMPTY -- waiting", file=sys.stderr)
        while True:
            time.sleep(10)
            q = api("/queue")
            if not q["queue_running"] and not q["queue_pending"]:
                break

    print("  POST /free ...")
    free_server()

    client_id = f"trackB-{a.arm}-{uuid.uuid4().hex[:8]}"
    t0 = time.time()
    res = api("/prompt", {"prompt": graph, "client_id": client_id})
    pid = res["prompt_id"]
    print(f"  prompt_id {pid}  client_id {client_id}")

    hist = None
    while time.time() - t0 < a.timeout:
        time.sleep(6)
        try:
            h = api(f"/history/{pid}")
        except Exception as e:
            print("   poll err", e); continue
        if h and pid in h:
            st = h[pid].get("status", {})
            if st.get("completed") is not None or st.get("status_str") in ("success", "error"):
                hist = h[pid]
                break
    wall = round(time.time() - t0, 1)

    if hist is None:
        json.dump({"arm": a.arm, "prompt_id": pid, "status": "TIMEOUT", "wall": wall},
                  open(os.path.join(outdir, "meta.json"), "w"), indent=1)
        print("TIMEOUT"); sys.exit(2)

    json.dump({pid: hist}, open(os.path.join(outdir, "history.json"), "w"), indent=1)

    st = hist["status"]
    msgs = st.get("messages", [])
    cached, t_start, t_end, err = [], None, None, None
    for m in msgs:
        if m[0] == "execution_cached":
            cached = m[1].get("nodes", [])
        elif m[0] == "execution_start":
            t_start = m[1].get("timestamp")
        elif m[0] in ("execution_success", "execution_error", "execution_interrupted"):
            t_end = m[1].get("timestamp")
            if m[0] != "execution_success":
                err = m[1]
    exec_s = round((t_end - t_start) / 1000.0, 1) if (t_start and t_end) else None

    imgs, hchecks = [], []
    for nid, out in (hist.get("outputs") or {}).items():
        for im in out.get("images", []) or []:
            if im.get("type") != "output":
                continue
            u = (f"/view?filename={urllib.parse.quote(im['filename'])}"
                 f"&subfolder={urllib.parse.quote(im.get('subfolder',''))}&type=output")
            dest = os.path.join(outdir, im["filename"])
            try:
                with urllib.request.urlopen(f"http://{SERVER}{u}", timeout=180) as r, open(dest, "wb") as f:
                    f.write(r.read())
                imgs.append(im["filename"])
                if nid == "505":
                    hchecks.append(health(dest))
            except Exception as e:
                print("   image fetch failed", im, e)

    meta = {
        "arm": a.arm, "note": a.note, "expect": a.expect,
        "server": SERVER, "base": os.path.relpath(a.base, "/workspace/nsfw-fix"),
        "changes": changes, "graph_sha256": gsha,
        "prompt_id": pid, "client_id": client_id,
        "status": st.get("status_str"), "exec_seconds": exec_s, "wall_seconds": wall,
        "cached_count": len(cached), "cached_nodes": cached,
        "images": imgs, "health": hchecks,
        "error_node_id": (err or {}).get("node_id"),
        "error_node_type": (err or {}).get("node_type"),
        "exception_type": (err or {}).get("exception_type"),
        "exception_message": (err or {}).get("exception_message"),
    }
    json.dump(meta, open(os.path.join(outdir, "meta.json"), "w"), indent=1)

    print(f"RESULT {a.arm}: {meta['status']}  exec={exec_s}s  cached={len(cached)}")
    if err:
        print(f"  ERROR at {err.get('node_id')} {err.get('node_type')} "
              f"{err.get('exception_type')}: {str(err.get('exception_message'))[:120]}")
    for h in hchecks:
        print(f"  HEALTH {h['file']} flat_frac={h['flat_frac']} luma_sd={h['luma_sd']} "
              f"poisoned={h['suspect_poisoned']}")
    if len(cached):
        print("  !! WARNING: execution_cached is NOT empty")


if __name__ == "__main__":
    main()
