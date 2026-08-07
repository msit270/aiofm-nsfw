#!/usr/bin/env python3
"""Q4 (other settings) arm driver -- run-4 quality menu, per notes/Q-PROTOCOL.md.

Every GPU-touching step runs under an exclusive flock on
/workspace/nsfw-fix/.gpu_lock. Each arm gets a FRESH ComfyUI process on port
19188 (never 18188), rendered cold by construction, then the process is killed
and the lock released. Evidence per arm under results/run4/quality/Q4/<arm>/.

Graph provenance
----------------
The protocol names results/run3/guard/api_guarded.json as "the current shipping
bytes, guarded conversion". Measured this session, that file PREDATES two
shipped output-changing fixes (620:648 mouth ceiling 1.7M->4M, commit 07d61b2;
622:664 FeatherMask into 622:418.mask, commit 72f95ba). api_final.json in the
same directory carries both and differs from the buyer-verified conversion
(results/run3/fresh/fresh-buyer-api_graph.json) in EXACTLY the four buyer-typed
inputs (2 LoRAs, 483 batch data, 620:106 text). So arms are built from
api_final.json, mutated the r3.py::guarded_graph way, with the buyer values
read from the fresh-buyer graph -- and build() asserts the resulting baseline
equals the fresh-buyer graph except pick_list ("" -> "0", injected at submit
per the standing practice) and the TAP163 SaveImage. That assertion is the
proof this is "current bytes + the buyer prompt", not a stale config.

Usage:
    q4.py build           # build all graphs + graph_diff each arm vs baseline
    q4.py render <arm>    # one arm under the lock, fresh server, cold
    q4.py render-all      # all arms in order, lock taken per arm
    q4.py analyze         # metrics + health + log extracts (CPU-only YOLO)
"""
import json, os, sys, time, uuid, copy, threading, subprocess, shutil, socket, signal, fcntl
import urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
Q4 = os.path.dirname(HERE)                       # results/run4/quality/Q4
NSFW = "/workspace/nsfw-fix"
VTOOLS = f"{NSFW}/results/crash/V/tools"
sys.path.insert(0, VTOOLS)
import v_mk  # noqa: E402  (norm + set_loras, proven in run 3)

FINAL = f"{NSFW}/results/run3/guard/api_final.json"
FRESH = f"{NSFW}/results/run3/fresh/fresh-buyer-api_graph.json"
GRAPH_DIFF = f"{NSFW}/tools/graph_diff/graph_diff.py"
LOCK = f"{NSFW}/.gpu_lock"
TRACKQ = "/workspace/trackQ"
OUT = f"{TRACKQ}/output"
COMFY = "/workspace/ComfyUI"
PY = "/venv/main/bin/python"
PORT = 19188
SERVER = f"127.0.0.1:{PORT}"
VRAM_GATE_MIB = 50000

# ---------------------------------------------------------------- arm builders
def base_graph():
    g = v_mk.norm(json.load(open(FINAL)))
    fresh = v_mk.norm(json.load(open(FRESH)))
    v_mk.set_loras(g)                            # lunaskye on 618, luna on 116
    # buyer-typed values, read from the buyer-verified conversion (not retyped)
    g["483"]["inputs"]["prompt_batch_data"] = fresh["483"]["inputs"]["prompt_batch_data"]
    g["620:106"]["inputs"]["text"] = fresh["620:106"]["inputs"]["text"]
    g["619:603"]["inputs"]["pick_list"] = "0"    # selector short-circuit, standing practice
    g["TAP163"] = {"class_type": "SaveImage",
                   "inputs": {"images": ["621:163", 0],
                              "filename_prefix": "q4tap/tap163"},
                   "_meta": {"title": "Q4 tap: 621:163 (post-mouth, pre-eyes image)"}}
    return g


def assert_is_current_bytes(g):
    """Baseline must equal the buyer-verified fresh conversion except
    pick_list and the TAP163 addition."""
    fresh = v_mk.norm(json.load(open(FRESH)))
    diffs = []
    for k in set(g) | set(fresh):
        if k == "TAP163":
            continue
        if k not in g:
            diffs.append(("missing-in-baseline", k)); continue
        if k not in fresh:
            diffs.append(("extra-in-baseline", k)); continue
        for ik in set(g[k]["inputs"]) | set(fresh[k]["inputs"]):
            a, b = g[k]["inputs"].get(ik), fresh[k]["inputs"].get(ik)
            if a != b:
                diffs.append((k, ik, b, a))
    allowed = [("619:603", "pick_list", "", "0")]
    unexpected = [d for d in diffs if d not in allowed]
    assert not unexpected, f"baseline is NOT current-bytes+buyer: {unexpected}"
    return diffs


ARMS = {
    # name: (param label for the sheet, {node: {input: value}} overrides)
    "baseline_ships": ("BASELINE (ships) - shipped settings, no change", {}),
    "blend87_050": ("#87 ImageBlend blend_factor 1.0 -> 0.5 (skin filter half strength)",
                    {"587:87": {"blend_factor": 0.5}}),
    "usdu617_dn015": ("#617 UltimateSDUpscale (first, SDXL 25st cfg4.5) denoise 0.25 -> 0.15",
                      {"619:617": {"denoise": 0.15}}),
    "usdu617_dn035": ("#617 UltimateSDUpscale (first, SDXL 25st cfg4.5) denoise 0.25 -> 0.35",
                      {"619:617": {"denoise": 0.35}}),
    "usdu98_tile1024": ("#98 USDU tile: whole-frame 1792x2304 (wired from #99) -> fixed 1024x1024",
                        {"587:98": {"tile_width": 1024, "tile_height": 1024}}),
    "base592_steps60": ("#592 KSampler (SDXL base gen) steps 40 -> 60 (+50%)",
                        {"619:592": {"steps": 60}}),
    "face607_dn030": ("#607 FaceDetailerPipe (SDXL face pass) denoise 0.45 -> 0.30",
                      {"619:607": {"denoise": 0.30}}),
}
ORDER = ["baseline_ships", "blend87_050", "usdu617_dn015", "usdu617_dn035",
         "usdu98_tile1024", "base592_steps60", "face607_dn030"]


def build():
    base = base_graph()
    prov = assert_is_current_bytes(base)
    print(f"[build] baseline == fresh-buyer conversion except: {prov} + TAP163  -- PASS")
    for name in ORDER:
        param, ov = ARMS[name]
        g = copy.deepcopy(base)
        for nid, kv in ov.items():
            g[nid]["inputs"].update(kv)
        d = os.path.join(Q4, name)
        os.makedirs(d, exist_ok=True)
        json.dump(g, open(os.path.join(d, "api_graph.json"), "w"), indent=1)
        # sanctioned diff vs baseline: must show exactly the intended inputs
        if name != "baseline_ships":
            r = subprocess.run([PY, GRAPH_DIFF, os.path.join(Q4, "baseline_ships", "api_graph.json"),
                                os.path.join(d, "api_graph.json")],
                               capture_output=True, text=True)
            open(os.path.join(d, "graph_diff_vs_baseline.txt"), "w").write(r.stdout + r.stderr)
            want = sum(len(kv) for kv in ov.values())
            got = r.stdout.count("value_changed")
            line = [l for l in r.stdout.splitlines() if l.startswith("RESULT")]
            print(f"[build] {name}: {line[0] if line else '??'}  (want {want} value_changed)")
            assert f"{want} difference" in r.stdout, f"{name}: unexpected diff\n{r.stdout}"
    print("[build] all graphs written and diffed")


# ---------------------------------------------------------------- http helpers
def req(path, data=None, timeout=60):
    url = f"http://{SERVER}{path}"
    body = json.dumps(data).encode() if data is not None else None
    hdrs = {"Content-Type": "application/json"} if data is not None else {}
    with urllib.request.urlopen(urllib.request.Request(url, data=body, headers=hdrs),
                                timeout=timeout) as f:
        raw = f.read()
    return json.loads(raw) if raw else None


def server_alive():
    try:
        req("/system_stats", timeout=5)
        return True
    except Exception:
        return False


def nvsmi(q, sel):
    r = subprocess.run(["nvidia-smi", f"--query-{q}={sel}",
                        "--format=csv,noheader,nounits"], capture_output=True, text=True)
    return r.stdout.strip()


class WSRec(threading.Thread):
    """Records (t, node) for every `executing` message, plus all non-progress
    messages. Timestamps are local receipt time, used to attribute VRAM samples
    to node windows."""
    def __init__(self, cid):
        super().__init__(daemon=True)
        self.cid, self.events, self.msgs, self.error = cid, [], [], None
        self.stop_flag, self.ready = threading.Event(), threading.Event()

    def run(self):
        try:
            from websockets.sync.client import connect
            with connect(f"ws://{SERVER}/ws?clientId={self.cid}",
                         open_timeout=30, max_size=None) as ws:
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
                        self.events.append((time.time(), (d.get("data") or {}).get("node")))
        except Exception as e:
            self.error = f"{type(e).__name__}: {e}"
            self.ready.set()


class VramSampler(threading.Thread):
    """Every 2 s: per-process VRAM (compute apps) + whole-GPU used."""
    def __init__(self, watch_pid):
        super().__init__(daemon=True)
        self.pid, self.samples, self.stop_flag = watch_pid, [], threading.Event()

    def run(self):
        while not self.stop_flag.is_set():
            t = time.time()
            per = {}
            for line in nvsmi("compute-apps", "pid,used_gpu_memory").splitlines():
                if "," in line:
                    p, m = line.split(",")
                    try:
                        per[int(p)] = int(m)
                    except ValueError:
                        pass
            tot = nvsmi("gpu", "memory.used")
            try:
                tot = int(tot)
            except ValueError:
                tot = None
            self.samples.append({"t": t, "mine_mib": per.get(self.pid),
                                 "total_used_mib": tot})
            self.stop_flag.wait(2.0)


def summarize(hist):
    out = {"status": None, "exec_seconds": None, "cached": None, "cached_ids": [],
           "error": None, "error_node": None, "error_type": None, "images": []}
    st = hist.get("status", {})
    out["status"] = st.get("status_str")
    t0 = t1 = None
    for m in st.get("messages", []):
        kind, payload = m[0], m[1]
        if kind == "execution_cached":
            out["cached_ids"] = payload.get("nodes", [])
            out["cached"] = len(out["cached_ids"])
        if kind == "execution_start":
            t0 = payload.get("timestamp")
        if kind in ("execution_success", "execution_error", "execution_interrupted"):
            t1 = payload.get("timestamp")
        if kind == "execution_error":
            out["error_node"] = payload.get("node_id")
            out["error_type"] = payload.get("node_type")
            out["error"] = f"{payload.get('exception_type')}: {payload.get('exception_message')}"
    if t0 and t1:
        out["exec_seconds"] = round((t1 - t0) / 1000.0, 1)
    for nid, o in (hist.get("outputs") or {}).items():
        for im in o.get("images", []):
            out["images"].append({"node": nid, **im})
    return out


# ---------------------------------------------------------------- render loop
def render(name):
    param, ov = ARMS[name]
    d = os.path.join(Q4, name)
    graph = json.load(open(os.path.join(d, "api_graph.json")))
    os.makedirs(OUT, exist_ok=True)
    slog = f"{TRACKQ}/server_{name}.log"
    pidfile = f"{TRACKQ}/server_19188.pid"

    # pre-gate OUTSIDE the lock, but only when the lock is FREE while VRAM is
    # low -- that is true external scarcity (e.g. a track-1 server resident
    # without the lock) and queueing three Q drivers on flock during it is the
    # starvation pattern the orchestrator flagged. When the lock is BUSY, the
    # VRAM is (mostly) the holder's own arm server, which dies before the lock
    # frees -- so the right move is to queue on the lock, not to poll VRAM.
    # The mandatory post-acquisition re-check below is unchanged either way.
    waited = 0
    while True:
        free = int(nvsmi("gpu", "memory.free"))
        if free >= VRAM_GATE_MIB:
            break
        probe = open(LOCK, "w")
        try:
            fcntl.flock(probe, fcntl.LOCK_EX | fcntl.LOCK_NB)
            fcntl.flock(probe, fcntl.LOCK_UN)
            lock_free = True
        except BlockingIOError:
            lock_free = False
        finally:
            probe.close()
        if not lock_free:
            print(f"[{name}] vram low ({free} MiB) but lock busy (a sibling's arm) -- queueing on the lock", flush=True)
            break
        print(f"[{name}] pre-gate: vram free {free} MiB < {VRAM_GATE_MIB}, lock free -- external scarcity, waiting 60 s (not holding lock)", flush=True)
        time.sleep(60)
        waited += 60
        if waited > 14400:
            raise RuntimeError("VRAM pre-gate not passed in 4 h")

    lk = open(LOCK, "w")
    print(f"[{name}] waiting for GPU lock ...", flush=True)
    fcntl.flock(lk, fcntl.LOCK_EX)
    print(f"[{name}] lock held", flush=True)
    proc = None
    try:
        # another agent's server may still be mid-shutdown when the lock frees;
        # give the port up to 90 s to go quiet before treating it as a leak
        t_q = time.time()
        while server_alive() and time.time() - t_q < 90:
            time.sleep(3)
        # stale-server check: only kill a 19188 this driver recorded as its own
        if server_alive():
            stale_ok = False
            if os.path.exists(pidfile):
                try:
                    sp = int(open(pidfile).read().strip())
                    cmd = open(f"/proc/{sp}/cmdline", "rb").read().decode(errors="replace")
                    if f"--port\x00{PORT}" in cmd or f"--port {PORT}" in cmd:
                        os.kill(sp, signal.SIGKILL)
                        time.sleep(3)
                        stale_ok = not server_alive()
                except Exception:
                    pass
            if not stale_ok and server_alive():
                raise RuntimeError(f"port {PORT} answers but is not a leak of this driver -- refusing")

        # VRAM gate
        waited = 0
        while True:
            free = int(nvsmi("gpu", "memory.free"))
            if free >= VRAM_GATE_MIB:
                break
            print(f"[{name}] vram free {free} MiB < {VRAM_GATE_MIB} -- waiting 60 s", flush=True)
            time.sleep(60)
            waited += 60
            if waited > 7200:
                raise RuntimeError("VRAM gate not passed in 2 h")

        # fresh server
        lf = open(slog, "w")
        proc = subprocess.Popen([PY, "main.py", "--port", str(PORT),
                                 "--disable-auto-launch", "--disable-xformers",
                                 "--output-directory", OUT],
                                cwd=COMFY, stdout=lf, stderr=subprocess.STDOUT)
        open(pidfile, "w").write(str(proc.pid))
        t_boot = time.time()
        while not server_alive():
            if proc.poll() is not None:
                raise RuntimeError(f"server died during boot, see {slog}")
            if time.time() - t_boot > 420:
                raise RuntimeError("server did not answer /system_stats in 420 s")
            time.sleep(2)
        boot_s = round(time.time() - t_boot, 1)
        print(f"[{name}] server up pid={proc.pid} in {boot_s}s", flush=True)

        cid = f"q4-{name}-{uuid.uuid4().hex[:8]}"
        rec = WSRec(cid); rec.start(); rec.ready.wait(timeout=35)
        vs = VramSampler(proc.pid); vs.start()
        t0 = time.time()
        resp = req("/prompt", {"prompt": graph, "client_id": cid}, timeout=180)
        pid = resp["prompt_id"]
        print(f"[{name}] submitted {pid}", flush=True)

        hist = None
        while time.time() - t0 < 3600:
            time.sleep(5)
            try:
                h = req(f"/history/{pid}", timeout=30)
            except Exception:
                continue
            if h and pid in h:
                st = h[pid].get("status", {})
                if st.get("completed") is True or st.get("status_str") in ("success", "error"):
                    hist = h[pid]
                    break
        wall = round(time.time() - t0, 1)
        time.sleep(2)
        rec.stop_flag.set(); vs.stop_flag.set()
        rec.join(timeout=10); vs.join(timeout=10)
        if hist is None:
            raise RuntimeError(f"prompt {pid} did not complete in 3600 s")

        json.dump(hist, open(os.path.join(d, "history.json"), "w"), indent=1)
        json.dump({"events": [[round(t, 3), n] for t, n in rec.events],
                   "ws_error": rec.error, "messages": rec.msgs},
                  open(os.path.join(d, "ws.json"), "w"), indent=1)
        json.dump(vs.samples, open(os.path.join(d, "vram_samples.json"), "w"), indent=1)

        s = summarize(hist)
        # peak VRAM (this server's pid) + the node window it fell in
        peak = peak_t = None
        for smp in vs.samples:
            if smp["mine_mib"] is not None and (peak is None or smp["mine_mib"] > peak):
                peak, peak_t = smp["mine_mib"], smp["t"]
        peak_node = None
        if peak_t is not None:
            for t, n in rec.events:
                if t <= peak_t and n is not None:
                    peak_node = n
        for im in s["images"]:
            src = os.path.join(OUT, im.get("subfolder", ""), im["filename"])
            if os.path.exists(src):
                shutil.copy2(src, os.path.join(d, f"n{im['node'].replace(':', '_')}__{im['filename']}"))
        shutil.copy2(slog, os.path.join(d, "server.log"))

        main_png = next((f"n{im['node'].replace(':', '_')}__{im['filename']}"
                         for im in s["images"] if im["node"] == "505"), None)
        meta = {"arm": name, "param": param, "baseline": name == "baseline_ships",
                "prompt_id": pid, "client_id": cid, "server_pid": proc.pid,
                "boot_seconds": boot_s, "wall_seconds": wall,
                "exec_seconds": s["exec_seconds"], "status": s["status"],
                "cached_nodes": s["cached_ids"], "cached": s["cached"],
                "error": s["error"], "error_node": s["error_node"],
                "peak_vram_mib": peak, "peak_vram_node": peak_node,
                "overrides": ov, "images": s["images"], "image": main_png,
                "graph_sha_note": "built from api_final.json (see module docstring)"}
        json.dump(meta, open(os.path.join(d, "meta.json"), "w"), indent=1)
        cold = "COLD" if s["cached"] == 0 or s["cached_ids"] == [] else f"NOT COLD ({s['cached']})"
        print(f"[{name}] {s['status']} exec={s['exec_seconds']}s wall={wall}s {cold} "
              f"peak={peak}MiB@{peak_node} imgs={[i['filename'] for i in s['images']]}", flush=True)
        return meta
    finally:
        if proc is not None:
            proc.terminate()
            try:
                proc.wait(timeout=45)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=15)
            # do not release the lock until the port stops answering
            for _ in range(30):
                if not server_alive():
                    break
                time.sleep(2)
        if os.path.exists(pidfile):
            os.unlink(pidfile)
        fcntl.flock(lk, fcntl.LOCK_UN)
        lk.close()
        print(f"[{name}] lock released", flush=True)


def render_all():
    for name in ORDER:
        mp = os.path.join(Q4, name, "meta.json")
        if os.path.exists(mp):
            m = json.load(open(mp))
            if m.get("status") == "success" and m.get("cached") in (0, None):
                print(f"[{name}] already recorded -- skipping", flush=True)
                continue
        render(name)
    print("Q4-RENDER-ALL-DONE", flush=True)


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "build":
        build()
    elif cmd == "render":
        render(sys.argv[2])
    elif cmd == "render-all":
        render_all()
    else:
        sys.exit(f"unknown command {cmd}")
