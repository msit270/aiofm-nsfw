#!/usr/bin/env python3
"""A2 length ladder. Ascending word count, probe graph, /free before every arm,
and a byte-identical known-clean control immediately after ANY error arm."""
import sys, json, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import drive, mk, strings

BASE_IMG = "trackA_base137.png"
LOG = "/workspace/nsfw-fix/results/crash/A/ladder_results.json"


def control(tag):
    g = mk.probe_graph(strings.PLACEHOLDER, BASE_IMG)
    return drive.run_arm(f"CTL_placeholder_{tag}", g,
                         note="health control: byte-identical to A1_gate_placeholder, "
                              "run immediately after an error arm")


def main(counts):
    res = []
    if os.path.exists(LOG):
        res = json.load(open(LOG))
    for n in counts:
        text = strings.prefix(n)
        g = mk.probe_graph(text, BASE_IMG)
        m = drive.run_arm(f"L_w{n:02d}", g, note=f"ladder: first {n} words of the crashing string")
        m["words"] = n
        res.append(m)
        json.dump(res, open(LOG, "w"), indent=1)
        if m.get("status") == "error":
            c = control(f"after_w{n:02d}")
            c["words"] = None
            res.append(c)
            json.dump(res, open(LOG, "w"), indent=1)
            if c.get("status") != "success":
                print("!!! HEALTH CONTROL FAILED -- server poisoned, stopping", flush=True)
                return
    print("ladder done", flush=True)


if __name__ == "__main__":
    main([int(x) for x in sys.argv[1:]])
