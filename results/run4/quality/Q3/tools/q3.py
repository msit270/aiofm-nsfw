#!/usr/bin/env python3
"""Q3 arm driver — Z-Image detail-pass quality sweep (track 2, Q-PROTOCOL).

Per arm, under an exclusive flock on /workspace/nsfw-fix/.gpu_lock:
  boot a FRESH ComfyUI on 127.0.0.1:19188 (never 18188) ->
  submit ONE graph -> poll history -> collect evidence -> kill server ->
  release lock.

Evidence per arm under results/run4/quality/Q3/<arm>/:
  api_graph.json   the submitted graph, verbatim
  history.json     the /history/<pid> entry, verbatim
  meta.json        exec seconds, execution_cached, VRAM peak, detailer log lines
  server.log       the arm server's full stdout/stderr
  vram_samples.csv nvidia-smi samples across the arm (2 s period)
  n<NODE>__*.png   every image the server wrote, prefixed by producing node id

Graph = results/run3/guard/api_final.json (proven == published bytes modulo the
four buyer-typed values; see notes/Q3-zimage.md 'base bytes') + those four buyer
values from results/run3/fresh/fresh-buyer-api_graph.json + pick_list "0"
(protocol) + four SaveImage taps that are IDENTICAL in every arm:
  TAP137 620:137 slot0  face-pass input
  TAP114 620:114 slot0  face-pass output   (slot 0 = the downstream-wired slot)
  TAP111 620:111 slot0  after-face colormatch = mouth-pass input
  TAP163 621:163 slot0  after-mouth colormatch = eyes-stage input
Baseline == the verified fresh-buyer render graph + taps, 0 other diffs.
"""
import fcntl, json, os, shutil, signal, subprocess, sys, time, urllib.request, uuid

NSFW = "/workspace/nsfw-fix"
FINAL = f"{NSFW}/results/run3/guard/api_final.json"
FRESH = f"{NSFW}/results/run3/fresh/fresh-buyer-api_graph.json"
Q3 = f"{NSFW}/results/run4/quality/Q3"
LOCK = f"{NSFW}/.gpu_lock"
OUT = "/workspace/trackQ/output"
SERVER = "127.0.0.1:19188"
COMFY = "/workspace/ComfyUI"

TAPS = {
    "TAP137": ("620:137", "q3tap/tap137", "face-pass input (620:137 colormatch out)"),
    "TAP114": ("620:114", "q3tap/tap114", "face-pass output slot 0 (downstream-wired)"),
    "TAP111": ("620:111", "q3tap/tap111", "after-face colormatch = mouth-pass input"),
    "TAP163": ("621:163", "q3tap/tap163", "after-mouth colormatch = eyes-stage input"),
}


def norm(g):
    import copy
    g = copy.deepcopy(g)
    if "419" in g:
        g["419"]["inputs"].pop("rgthree_comparer", None)
    return g


def buyer_values():
    f = json.load(open(FRESH))
    return {
        "116.lora_01": f["116"]["inputs"]["lora_01"],
        "618.lora_01": f["618"]["inputs"]["lora_01"],
        "483.prompt_batch_data": f["483"]["inputs"]["prompt_batch_data"],
        "620:106.text": f["620:106"]["inputs"]["text"],
    }


def q3_graph(overrides=None):
    g = norm(json.load(open(FINAL)))
    bv = buyer_values()
    g["116"]["inputs"]["lora_01"] = bv["116.lora_01"]
    g["618"]["inputs"]["lora_01"] = bv["618.lora_01"]
    g["483"]["inputs"]["prompt_batch_data"] = bv["483.prompt_batch_data"]
    g["620:106"]["inputs"]["text"] = bv["620:106.text"]
    g["619:603"]["inputs"]["pick_list"] = "0"
    for nid, kv in (overrides or {}).items():
        g[nid]["inputs"].update(kv)
    for tap, (src, prefix, title) in TAPS.items():
        g[tap] = {"class_type": "SaveImage",
                  "inputs": {"images": [src, 0], "filename_prefix": prefix},
                  "_meta": {"title": f"Q3 tap: {title}"}}
    return g


def _req(path, data=None, timeout=60):
    url = f"http://{SERVER}{path}"
    body = json.dumps(data).encode() if data is not None else None
    hdrs = {"Content-Type": "application/json"} if data is not None else {}
    with urllib.request.urlopen(urllib.request.Request(url, data=body, headers=hdrs),
                                timeout=timeout) as f:
        raw = f.read()
    return json.loads(raw) if raw else None


def vram_free_mib():
    out = subprocess.run(["nvidia-smi", "--query-gpu=memory.free",
                          "--format=csv,noheader,nounits"],
                         capture_output=True, text=True).stdout.strip()
    return int(out.splitlines()[0])


class VramSampler:
    """2 s nvidia-smi loop -> csv; also per-process peak for the arm server pid."""

    def __init__(self, csv_path, server_pid):
        self.path, self.pid = csv_path, server_pid
        self.proc = None

    def start(self):
        script = (
            "while true; do "
            "t=$(date +%s.%N); "
            "g=$(nvidia-smi --query-gpu=memory.used,memory.free --format=csv,noheader,nounits); "
            "p=$(nvidia-smi --query-compute-apps=pid,used_memory --format=csv,noheader,nounits "
            f"| awk -F', *' '$1=={self.pid} {{print $2}}'); "
            "echo \"$t,$g,${p:-0}\"; sleep 2; done")
        self.f = open(self.path, "w")
        self.f.write("unix_time,gpu_used_mib,gpu_free_mib,arm_server_used_mib\n")
        self.f.flush()
        self.proc = subprocess.Popen(["bash", "-c", script], stdout=self.f,
                                     stderr=subprocess.DEVNULL)

    def stop(self):
        if self.proc:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=5)
            except Exception:
                self.proc.kill()
        self.f.close()
        peak_gpu = peak_arm = None
        try:
            rows = [l.strip().split(",") for l in open(self.path).read().splitlines()[1:] if l.strip()]
            if rows:
                peak_gpu = max(int(r[1].strip()) for r in rows if len(r) >= 2)
                peak_arm = max(int(r[3].strip()) for r in rows if len(r) >= 4)
        except Exception:
            pass
        return {"gpu_peak_used_mib": peak_gpu, "arm_server_peak_mib": peak_arm}


def summarize(hist):
    out = {"status": None, "exec_seconds": None, "execution_cached": None,
           "error": None, "error_node": None, "images": []}
    st = hist.get("status", {})
    out["status"] = st.get("status_str")
    t0 = t1 = None
    for m in st.get("messages", []):
        kind, payload = m[0], m[1]
        if kind == "execution_cached":
            out["execution_cached"] = payload.get("nodes", [])
        if kind == "execution_start":
            t0 = payload.get("timestamp")
        if kind in ("execution_success", "execution_error", "execution_interrupted"):
            t1 = payload.get("timestamp")
        if kind == "execution_error":
            out["error_node"] = payload.get("node_id")
            out["error"] = f"{payload.get('exception_type')}: {payload.get('exception_message')}"
    if t0 and t1:
        out["exec_seconds"] = round((t1 - t0) / 1000.0, 1)
    for nid, o in (hist.get("outputs") or {}).items():
        for im in o.get("images", []):
            out["images"].append({"node": nid, **im})
    return out


def run_arm(name, overrides, param_desc, is_baseline=False):
    d = os.path.join(Q3, name)
    if os.path.exists(os.path.join(d, "meta.json")):
        m = json.load(open(os.path.join(d, "meta.json")))
        if m.get("status") == "success" and m.get("execution_cached") == []:
            print(f"[{name}] already recorded cold+success — skipping", flush=True)
            return m
    os.makedirs(d, exist_ok=True)
    graph = q3_graph(overrides)
    json.dump(graph, open(os.path.join(d, "api_graph.json"), "w"), indent=1)

    lock_f = open(LOCK, "w")
    print(f"[{name}] waiting for gpu lock ...", flush=True)
    t_lock = time.time()
    fcntl.flock(lock_f, fcntl.LOCK_EX)
    lock_wait = round(time.time() - t_lock, 1)
    print(f"[{name}] lock acquired after {lock_wait}s", flush=True)
    server = None
    sampler = None
    try:
        # VRAM gate per protocol
        waited = 0
        while vram_free_mib() < 50000:
            print(f"[{name}] vram_free {vram_free_mib()} < 50000 MiB — waiting 60 s", flush=True)
            time.sleep(60)
            waited += 60
            if waited > 3600:
                raise RuntimeError("VRAM gate never opened in 1 h")

        # clean per-arm output dir so filenames are deterministic and unmixed
        if os.path.isdir(OUT):
            shutil.rmtree(OUT)
        os.makedirs(OUT, exist_ok=True)

        log_path = os.path.join(d, "server.log")
        log_f = open(log_path, "w")
        server = subprocess.Popen(
            ["python3", "main.py", "--port", "19188", "--disable-auto-launch",
             "--output-directory", OUT],
            cwd=COMFY, stdout=log_f, stderr=subprocess.STDOUT,
            start_new_session=True)
        t0 = time.time()
        while True:
            if server.poll() is not None:
                raise RuntimeError(f"arm server exited rc={server.returncode} during boot")
            try:
                _req("/system_stats", timeout=5)
                break
            except Exception:
                if time.time() - t0 > 300:
                    raise RuntimeError("server did not answer /system_stats in 300 s")
                time.sleep(2)
        boot_s = round(time.time() - t0, 1)
        print(f"[{name}] server up (pid {server.pid}) in {boot_s}s", flush=True)

        # snapshot object_info enums once (first arm that runs)
        oi_path = os.path.join(Q3, "tools", "object_info_detailers.json")
        if not os.path.exists(oi_path):
            oi = _req("/object_info", timeout=120)
            keep = {k: oi[k] for k in ("FaceDetailer", "DetailerForEachDebug", "KSampler")
                    if k in oi}
            json.dump(keep, open(oi_path, "w"), indent=1)

        sampler = VramSampler(os.path.join(d, "vram_samples.csv"), server.pid)
        sampler.start()

        cid = f"q3-{name}-{uuid.uuid4().hex[:8]}"
        t_sub = time.time()
        pid = _req("/prompt", {"prompt": graph, "client_id": cid})["prompt_id"]
        print(f"[{name}] submitted {pid}", flush=True)
        hist = None
        while time.time() - t_sub < 3600:
            try:
                h = _req(f"/history/{pid}", timeout=30)
            except Exception:
                h = None
            if h and pid in h:
                st = h[pid].get("status", {})
                if st.get("completed") is True or st.get("status_str") in ("success", "error"):
                    hist = h[pid]
                    break
            time.sleep(5)
        wall = round(time.time() - t_sub, 1)
        vram_peaks = sampler.stop()
        sampler = None
        if hist is None:
            raise RuntimeError(f"no terminal history entry after {wall}s")
        json.dump(hist, open(os.path.join(d, "history.json"), "w"), indent=1)
        s = summarize(hist)

        # collect every image the server wrote
        copied = []
        for im in s["images"]:
            src = os.path.join(OUT, im.get("subfolder", ""), im["filename"])
            if os.path.exists(src):
                dst = os.path.join(d, f"n{im['node'].replace(':', '_')}__{im['filename']}")
                shutil.copy2(src, dst)
                copied.append(os.path.basename(dst))

        # graceful shutdown before releasing the lock
        server.send_signal(signal.SIGTERM)
        try:
            server.wait(timeout=60)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait(timeout=30)
        log_f.close()
        server = None

        detailer_lines = [l.rstrip() for l in open(log_path, errors="replace")
                          if "Detailer:" in l or "segment upscale" in l]
        meta = {"arm": name, "param": param_desc, "baseline": is_baseline,
                "prompt_id": pid, "client_id": cid,
                "lock_wait_s": lock_wait, "boot_s": boot_s,
                "wall_seconds": wall, "exec_seconds": s["exec_seconds"],
                "status": s["status"], "error": s["error"], "error_node": s["error_node"],
                "execution_cached": s["execution_cached"],
                "vram": vram_peaks, "images": copied,
                "overrides": overrides,
                "detailer_log_lines": detailer_lines}
        json.dump(meta, open(os.path.join(d, "meta.json"), "w"), indent=1)
        print(f"[{name}] {s['status']} exec={s['exec_seconds']}s cached={s['execution_cached']} "
              f"vram_arm_peak={vram_peaks['arm_server_peak_mib']}MiB imgs={len(copied)}", flush=True)
        return meta
    finally:
        if sampler is not None:
            try:
                sampler.stop()
            except Exception:
                pass
        if server is not None:
            try:
                server.send_signal(signal.SIGTERM)
                server.wait(timeout=60)
            except Exception:
                try:
                    server.kill()
                except Exception:
                    pass
        fcntl.flock(lock_f, fcntl.LOCK_UN)
        lock_f.close()
        print(f"[{name}] lock released", flush=True)


# The shipped-default 483 prompt (from api_final.json itself): a PORTRAIT
# composition. On the fresh-buyer full-body composition the lips detector finds
# nothing (server.log "0: 640x512 (no detections)") and 620:165 is a no-op, so
# the mouth lever needs a composition where lips detect. This IS a buyer
# default too — it is the placeholder every buyer sees.
PORTRAIT_483 = json.load(open(FINAL))["483"]["inputs"]["prompt_batch_data"]

ARMS = {
    # name: (overrides, description, is_baseline)
    "A0_baseline": ({}, "BASELINE (ships): face 620:114 steps 8, denoise 0.35, euler_ancestral/kl_optimal; mouth 620:165 steps 8 den 0.35; eyes 622:406 steps 8 den 0.42 euler/beta", True),
    "P0_portrait_baseline": ({"483": {"prompt_batch_data": PORTRAIT_483}},
                             "BASELINE-2 (ships, portrait): identical settings, 483 prompt = the shipped placeholder portrait (mouth pass has lips to find here)", True),
    "P_M_steps16": ({"483": {"prompt_batch_data": PORTRAIT_483},
                     "620:165": {"steps": 16}},
                    "portrait composition + mouth 620:165 steps 8 -> 16 (one variable vs P0_portrait_baseline)", False),
    "F_steps12":   ({"620:114": {"steps": 12}}, "face 620:114 steps 8 -> 12", False),
    "F_steps16":   ({"620:114": {"steps": 16}}, "face 620:114 steps 8 -> 16", False),
    "F_den030":    ({"620:114": {"denoise": 0.30}}, "face 620:114 denoise 0.35 -> 0.30", False),
    "F_den045":    ({"620:114": {"denoise": 0.45}}, "face 620:114 denoise 0.35 -> 0.45", False),
    "F_res_multistep": ({"620:114": {"sampler_name": "res_multistep"}}, "face 620:114 sampler euler_ancestral -> res_multistep (scheduler stays kl_optimal)", False),
    "F_euler":     ({"620:114": {"sampler_name": "euler"}}, "face 620:114 sampler euler_ancestral -> euler (scheduler stays kl_optimal)", False),
    "E_steps16":   ({"622:406": {"steps": 16}}, "eyes 622:406 steps 8 -> 16", False),
    "M_steps16":   ({"620:165": {"steps": 16}}, "mouth 620:165 steps 8 -> 16", False),
}

if __name__ == "__main__":
    failed = []
    for a in sys.argv[1:]:
        ov, desc, base = ARMS[a]
        try:
            run_arm(a, ov, desc, base)
        except Exception as e:
            print(f"[{a}] ARM FAILED: {type(e).__name__}: {e} — continuing with the next arm", flush=True)
            failed.append(a)
    if failed:
        print(f"FAILED ARMS: {failed}", flush=True)
    print("QUEUE-DONE", flush=True)
