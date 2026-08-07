#!/usr/bin/env python3
"""Q2 arm driver — bbox_crop_factor ladder on 620:114 (the face pass).

Protocol (notes/Q-PROTOCOL.md), enforced here:
  * exclusive flock on /workspace/nsfw-fix/.gpu_lock around every GPU-touching
    step (boot -> render -> collect -> shutdown), released between arms
  * FRESH ComfyUI process per arm on port 19188, killed and reaped before the
    lock is released.  127.0.0.1:18188 is NEVER touched.
  * nvidia-smi memory.free >= 50000 MiB before boot, else wait 60 s and re-check
  * graphs built exactly like results/run3/tools/r3.py::guarded_graph
    (v_mk.norm, v_mk.set_loras, text -> 620:106, 619:603.pick_list = "0",
    TAP163 SaveImage), ONE variable per arm: 620:114.inputs.bbox_crop_factor
  * coldness verified from execution_cached in the history entry
  * evidence per arm under results/run4/quality/Q2/<arm>/

Arms (run order — baseline first, ladder, baseline repeat last so the session
is bracketed by same-window controls):
  A_cf15_baseline  1.5 (ships)   B_cf10 1.0   C_cf20 2.0   D_cf25 2.5
  E_cf30 3.0       F_cf35 3.5    G_cf15_repeat 1.5
"""
import fcntl
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid

sys.path.insert(0, "/workspace/nsfw-fix/results/crash/V/tools")
import v_mk  # noqa: E402  (graph mutations only; no server code)

LOCK = "/workspace/nsfw-fix/.gpu_lock"
SERVER = "127.0.0.1:19188"          # NEVER 18188
COMFY = "/workspace/ComfyUI"
OUTDIR = "/workspace/trackQ/output"
Q2 = "/workspace/nsfw-fix/results/run4/quality/Q2"
GUARDED = "/workspace/nsfw-fix/results/run3/guard/api_guarded.json"

# The 60-token buyer prompt — verbatim 620:106 text from
# results/run3/fresh/fresh-buyer-api_graph.json (v_tok.count == 60).
BUYER60 = ("luna, a young woman in her mid twenties with wavy auburn hair, "
           "warm hazel eyes, soft natural makeup, light freckles on her cheeks, "
           "gentle smile, photorealistic skin texture with visible pores, "
           "soft diffused studio light")

ARMS = [
    ("A_cf15_baseline", 1.5, True,  "bbox_crop_factor 1.5 (SHIPPED)"),
    ("B_cf10",          1.0, False, "bbox_crop_factor 1.0"),
    ("C_cf20",          2.0, False, "bbox_crop_factor 2.0"),
    ("D_cf25",          2.5, False, "bbox_crop_factor 2.5"),
    ("E_cf30",          3.0, False, "bbox_crop_factor 3.0"),
    ("F_cf35",          3.5, False, "bbox_crop_factor 3.5"),
    ("G_cf15_repeat",   1.5, False, "bbox_crop_factor 1.5 repeat (same-window noise control)"),
]


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def req(path, data=None, timeout=60):
    url = f"http://{SERVER}{path}"
    body = json.dumps(data).encode() if data is not None else None
    hdrs = {"Content-Type": "application/json"} if data is not None else {}
    r = urllib.request.Request(url, data=body, headers=hdrs)
    with urllib.request.urlopen(r, timeout=timeout) as f:
        raw = f.read()
    return json.loads(raw) if raw else None


def server_up():
    try:
        req("/system_stats", timeout=5)
        return True
    except Exception:
        return False


# ---------------------------------------------------------------- graph
def guarded_graph(text, overrides=None, pick=0):
    """Byte-for-byte the mutation r3.py::guarded_graph performs."""
    g = v_mk.norm(json.load(open(GUARDED)))
    v_mk.set_loras(g)
    g["620:106"]["inputs"]["text"] = text
    g["619:603"]["inputs"]["pick_list"] = str(pick)
    for nid, kv in (overrides or {}).items():
        g[nid]["inputs"].update(kv)
    g["TAP163"] = {"class_type": "SaveImage",
                   "inputs": {"images": ["621:163", 0],
                              "filename_prefix": "run3/tap163"},
                   "_meta": {"title": "run3 tap: 621:163 (mouth-stage image)"}}
    return g


def graph_diff(a, b):
    """Input-wise diff, both directions. Returns [(node, key, a_val, b_val)]."""
    out = []
    for nid in sorted(set(a) | set(b)):
        if nid not in a or nid not in b:
            out.append((nid, "<node>", nid in a, nid in b))
            continue
        ia, ib = a[nid]["inputs"], b[nid]["inputs"]
        for k in sorted(set(ia) | set(ib)):
            if ia.get(k) != ib.get(k):
                out.append((nid, k, ia.get(k), ib.get(k)))
    return out


# ---------------------------------------------------------------- gpu / server
def vram_free_mib():
    r = subprocess.run(["nvidia-smi", "--query-gpu=memory.free",
                        "--format=csv,noheader,nounits"],
                       capture_output=True, text=True)
    return int(r.stdout.strip().splitlines()[0])


def wait_vram(min_mib=50000, max_wait=3600):
    t0 = time.time()
    while True:
        v = vram_free_mib()
        if v >= min_mib:
            return v
        if time.time() - t0 > max_wait:
            raise RuntimeError(f"VRAM never reached {min_mib} MiB (last {v})")
        log(f"  vram_free {v} MiB < {min_mib} — waiting 60 s (gate may be running)")
        time.sleep(60)


def boot(arm):
    if server_up():
        # Somebody's server already on 19188 while WE hold the lock. Wait, then abort.
        for _ in range(10):
            time.sleep(30)
            if not server_up():
                break
        else:
            raise RuntimeError("port 19188 already serving under our lock — aborting, not killing it")
    logpath = f"/workspace/trackQ/server_Q2_{arm}.log"
    lf = open(logpath, "w")
    p = subprocess.Popen(
        ["python3", "main.py", "--port", "19188", "--disable-auto-launch",
         "--output-directory", OUTDIR],
        cwd=COMFY, stdout=lf, stderr=subprocess.STDOUT,
        start_new_session=True)
    t0 = time.time()
    while time.time() - t0 < 600:
        if p.poll() is not None:
            raise RuntimeError(f"server exited during boot, rc={p.returncode}, log {logpath}")
        if server_up():
            return p, logpath, round(time.time() - t0, 1)
        time.sleep(2)
    kill(p)                      # do not leak the half-booted process
    raise RuntimeError(f"server did not answer within 600 s, log {logpath}")


def kill(p):
    if p.poll() is None:
        os.killpg(os.getpgid(p.pid), signal.SIGTERM)
        try:
            p.wait(timeout=60)
        except subprocess.TimeoutExpired:
            os.killpg(os.getpgid(p.pid), signal.SIGKILL)
            p.wait(timeout=30)
    t0 = time.time()
    while server_up() and time.time() - t0 < 60:
        time.sleep(2)
    if server_up():
        raise RuntimeError("port 19188 still answering after kill")


# ---------------------------------------------------------------- history
def wait_done(pid, limit=3600):
    t0 = time.time()
    while time.time() - t0 < limit:
        try:
            h = req(f"/history/{pid}", timeout=30)
        except Exception:
            h = None
        if h and pid in h:
            st = h[pid].get("status", {})
            if st.get("completed") is True or st.get("status_str") in ("success", "error"):
                return h[pid]
        time.sleep(5)
    return None


def summarize(hist):
    out = {"status": None, "exec_seconds": None, "execution_cached": None,
           "error": None, "error_node": None, "error_type": None, "images": []}
    st = hist.get("status", {})
    out["status"] = st.get("status_str")
    t_start = t_end = None
    for m in st.get("messages", []):
        kind, payload = m[0], m[1]
        if kind == "execution_cached":
            out["execution_cached"] = payload.get("nodes", [])
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
        if "text" in o:
            out["images"].append({"node": nid, "text": o["text"]})
    return out


# ---------------------------------------------------------------- log slicing
KEEP = re.compile(r"Detailer: segment upscale|Detailer: force inpaint|"
                  r"Detailer: segment skip|# of Detected SEGS|mask_to_segs|"
                  r"\d+ (face|hand|lip)|no detections|lowvram|NaN|nan detected|"
                  r"Unloaded partially|loaded completely|"
                  r"\[filter\]|\[in\]|\[out\]|SEGSRangeFilter", re.IGNORECASE)


def slice_log(path):
    lines = []
    with open(path, errors="replace") as f:
        for ln in f:
            if KEEP.search(ln):
                lines.append(ln.rstrip("\n"))
    return lines


# ---------------------------------------------------------------- one arm
def run_arm(name, cf, is_base, param, base_graph):
    d = os.path.join(Q2, name)
    os.makedirs(d, exist_ok=True)
    if os.path.exists(os.path.join(d, "meta.json")):
        m = json.load(open(os.path.join(d, "meta.json")))
        if m.get("status") in ("success", "error"):
            log(f"[{name}] already recorded ({m['status']}) — skipping")
            return m

    overrides = {"620:114": {"bbox_crop_factor": cf}}
    g = guarded_graph(BUYER60, overrides=overrides)
    diff = graph_diff(base_graph, g)
    expected = [] if cf == 1.5 else [("620:114", "bbox_crop_factor", 1.5, cf)]
    assert diff == expected, f"one-variable check FAILED: {diff}"
    json.dump(g, open(os.path.join(d, "api_graph.json"), "w"), indent=1)

    lockf = open(LOCK, "w")
    log(f"[{name}] waiting for gpu lock …")
    fcntl.flock(lockf, fcntl.LOCK_EX)
    log(f"[{name}] lock acquired")
    meta = {"arm": name, "param": param, "baseline": is_base,
            "bbox_crop_factor": cf, "prompt_text_620:106": BUYER60,
            "graph_diff_vs_baseline_arm": [list(x) for x in diff]}
    proc = None
    try:
        meta["vram_free_before_boot_mib"] = wait_vram()
        proc, slog, boot_s = boot(name)
        meta["server_log"] = slog
        meta["boot_seconds"] = boot_s
        cid = f"Q2-{name}-{uuid.uuid4().hex[:8]}"
        t0 = time.time()
        pid = req("/prompt", {"prompt": g, "client_id": cid}, timeout=120)["prompt_id"]
        meta["prompt_id"], meta["client_id"] = pid, cid
        log(f"[{name}] submitted {pid} (boot {boot_s}s, vram {meta['vram_free_before_boot_mib']} MiB)")
        hist = wait_done(pid)
        meta["wall_seconds"] = round(time.time() - t0, 1)
        if hist is None:
            meta["status"] = "TIMEOUT-WAIT"
        else:
            json.dump(hist, open(os.path.join(d, "history.json"), "w"), indent=1)
            s = summarize(hist)
            meta.update(s)
            meta["cached_nodes"] = s["execution_cached"]   # contact_sheet.py reads this key
            meta["cold"] = (s["execution_cached"] == [])
            for im in s["images"]:
                if "filename" not in im:
                    continue
                src = os.path.join(OUTDIR, im.get("subfolder", ""), im["filename"])
                if os.path.exists(src):
                    dst = os.path.join(d, f"n{im['node'].replace(':', '_')}__{im['filename']}")
                    shutil.copy2(src, dst)
                    if im["node"] == "505":
                        meta["image"] = os.path.basename(dst)
        log(f"[{name}] {meta.get('status')} exec={meta.get('exec_seconds')}s "
            f"cached={meta.get('execution_cached')} err={meta.get('error_node')}")
    finally:
        if proc is not None:
            kill(proc)
            log(f"[{name}] server killed and reaped")
            shutil.copy2(slog, os.path.join(d, "server.log"))
            meta["log_slice"] = slice_log(slog)
        fcntl.flock(lockf, fcntl.LOCK_UN)
        lockf.close()
        log(f"[{name}] lock released")
    json.dump(meta, open(os.path.join(d, "meta.json"), "w"), indent=1)
    return meta


def main():
    base_graph = guarded_graph(BUYER60, overrides={"620:114": {"bbox_crop_factor": 1.5}})
    for name, cf, is_base, param in ARMS:
        try:
            run_arm(name, cf, is_base, param, base_graph)
        except Exception as e:
            log(f"[{name}] FAILED: {type(e).__name__}: {e} — continuing with remaining arms")
            d = os.path.join(Q2, name)
            os.makedirs(d, exist_ok=True)
            json.dump({"arm": name, "param": param, "baseline": is_base,
                       "bbox_crop_factor": cf, "status": "DRIVER-ERROR",
                       "error": f"{type(e).__name__}: {e}"},
                      open(os.path.join(d, "meta.json"), "w"), indent=1)
    log("Q2-RUNSET-DONE")


if __name__ == "__main__":
    main()
