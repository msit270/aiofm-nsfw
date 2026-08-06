#!/usr/bin/env python3
"""TRACK P timing analysis.

Reports each arm's runs, the within-arm spread, and the between-arm difference.
The verdict rule is fixed here BEFORE the numbers are read: a difference is only
quotable if it is larger than the within-arm spread. Otherwise the honest
statement is a bound, not a point estimate.
"""
import json, re, statistics as st
from collections import Counter

S = "/tmp/claude-0/-workspace-nsfw-fix/47375d2b-87bd-4073-a1e2-67796f8c1345/scratchpad/P"
LOG = "/tmp/claude-0/-workspace-nsfw-fix/47375d2b-87bd-4073-a1e2-67796f8c1345/scratchpad/r3comfy.log"
res = json.load(open(f"{S}/results.json"))


def load_profiles():
    """Per-render model-load work, from the server's own log.

    execution_cached: [] proves the NODE OUTPUT cache was cleared. It does not
    prove the models were evicted from VRAM, and nvidia-smi cannot prove it
    either because PyTorch's caching allocator keeps the freed pool. What does
    prove it is the server re-emitting 'Requested to load' / 'loaded completely'
    for every model on every run. Keyed by exec seconds, which the log prints.
    """
    lines = open(LOG, errors="replace").read().splitlines()
    out, cur = {}, None
    for l in lines:
        if l.strip() == "got prompt":
            cur = {"req": [], "loaded": 0}
        elif cur is not None and l.startswith("Prompt executed in"):
            cur["secs"] = round(float(re.search(r"([\d.]+)", l).group(1)), 1)
            out[cur["secs"]] = {"n_requested": len(cur["req"]),
                                "n_loaded_completely": cur["loaded"],
                                "models": dict(Counter(cur["req"]))}
            cur = None
        elif cur is not None:
            if l.startswith("Requested to load"):
                cur["req"].append(l.split("Requested to load ")[1])
            elif l.startswith("loaded completely"):
                cur["loaded"] += 1
    return out


PROF = load_profiles()

by = {}
for m in res:
    if not m.get("valid"):
        print(f"  EXCLUDED {m['name']}: {m.get('invalid_reason')}")
        continue
    by.setdefault(m["arm"], []).append(m)

LABEL = {"P_D080": "denoise 0.80, CLIP cpu   (old shipping)",
         "P_D035": "denoise 0.35, CLIP cpu   (as committed)",
         "P_CLIPDEF": "denoise 0.35, CLIP default (pre-fix)"}

print("\n=== per-run ===")
print(f"{'arm':<11} {'run':<6} {'exec_s':>8} {'cached':>7} {'reqLoad':>8} {'loaded':>7} "
      f"{'vram_free_GiB':>13} {'others_MiB':>11}")
for arm in ("P_D080", "P_D035", "P_CLIPDEF"):
    for m in sorted(by.get(arm, []), key=lambda x: x["seq"]):
        others = sum(m["gpu_pre"]["others_mib"].values())
        p = PROF.get(m["exec_seconds"], {})
        print(f"{arm:<11} r{m['round']}p{m['pos']:<4} {m['exec_seconds']:>8.1f} "
              f"{m['cached_nodes']:>7} {p.get('n_requested', '?'):>8} "
              f"{p.get('n_loaded_completely', '?'):>7} "
              f"{m['gpu_pre']['vram_free']/2**30:>13.1f} {others:>11}")

print("\n=== load-work profiles (proof each run really re-loaded) ===")
seen = {}
for arm in ("P_D080", "P_D035", "P_CLIPDEF"):
    for m in sorted(by.get(arm, []), key=lambda x: x["seq"]):
        p = PROF.get(m["exec_seconds"])
        if p:
            seen.setdefault(json.dumps(p["models"], sort_keys=True), []).append(m["name"])
for k, v in seen.items():
    print(f"  {k}\n     -> {', '.join(v)}")

print("\n=== per-arm ===")
stats = {}
for arm in ("P_D080", "P_D035", "P_CLIPDEF"):
    v = [m["exec_seconds"] for m in by.get(arm, [])]
    if not v:
        continue
    stats[arm] = {"n": len(v), "vals": sorted(v), "mean": st.mean(v),
                  "median": st.median(v), "min": min(v), "max": max(v),
                  "range": max(v) - min(v),
                  "sd": st.stdev(v) if len(v) > 1 else float("nan")}
    s = stats[arm]
    print(f"{arm:<11} {LABEL[arm]:<40} n={s['n']}  mean={s['mean']:7.1f}  median={s['median']:7.1f}  "
          f"min={s['min']:7.1f}  max={s['max']:7.1f}  range={s['range']:6.1f}  sd={s['sd']:6.1f}")

pooled_range = max(s["range"] for s in stats.values())
pooled_sd = st.mean([s["sd"] for s in stats.values() if s["sd"] == s["sd"]])
print(f"\nwithin-arm spread: worst range = {pooled_range:.1f} s, mean sd = {pooled_sd:.1f} s")


def compare(a, b, what):
    sa, sb = stats[a], stats[b]
    dm = sb["mean"] - sa["mean"]
    dmed = sb["median"] - sa["median"]
    print(f"\n--- {what} ---")
    print(f"  {a} mean {sa['mean']:.1f} s   ->   {b} mean {sb['mean']:.1f} s")
    print(f"  delta (mean)   = {dm:+.1f} s")
    print(f"  delta (median) = {dmed:+.1f} s")
    print(f"  worst within-arm range of the two = {max(sa['range'], sb['range']):.1f} s")
    print(f"  arms overlap?  {a} [{sa['min']:.1f}, {sa['max']:.1f}]  "
          f"{b} [{sb['min']:.1f}, {sb['max']:.1f}]  -> "
          f"{'OVERLAP' if not (sa['max'] < sb['min'] or sb['max'] < sa['min']) else 'DISJOINT'}")
    quotable = abs(dm) > max(sa["range"], sb["range"])
    print(f"  VERDICT: {'quotable' if quotable else 'NOT quotable — smaller than load variance'}")
    return dm


if "P_D080" in stats and "P_D035" in stats:
    compare("P_D080", "P_D035", "JOB 1a: the denoise lever (0.80 -> 0.35)")
if "P_D035" in stats and "P_CLIPDEF" in stats:
    compare("P_CLIPDEF", "P_D035", "JOB 1b: the CLIPLoader device lever (default -> cpu)")

json.dump(stats, open(f"{S}/stats.json", "w"), indent=1, default=str)
