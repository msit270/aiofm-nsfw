#!/usr/bin/env python3
"""A3 content control: same word count as the boundary, completely different
content. Plus, on request, a clause bisection of the original string."""
import sys, json, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import drive, mk, strings

BASE_IMG = "trackA_base137.png"
LOG = "/workspace/nsfw-fix/results/crash/A/content_results.json"


def control(tag):
    g = mk.probe_graph(strings.PLACEHOLDER, BASE_IMG)
    return drive.run_arm(f"CTL_placeholder_{tag}", g,
                         note="health control after an error arm")


def run(name, text, note, overrides=None):
    g = mk.probe_graph(text, BASE_IMG, overrides=overrides)
    m = drive.run_arm(name, g, note=note)
    m["text"] = text
    m["words"] = len(text.split(" ")) if text else 0
    return m


def main(pairs):
    res = json.load(open(LOG)) if os.path.exists(LOG) else []
    for name, text, note, ov in pairs:
        m = run(name, text, note, ov)
        res.append(m)
        json.dump(res, open(LOG, "w"), indent=1)
        if m.get("status") == "error":
            c = control(f"after_{name}")
            res.append(c)
            json.dump(res, open(LOG, "w"), indent=1)
            if c.get("status") != "success":
                print("!!! HEALTH CONTROL FAILED -- stopping", flush=True)
                return
    print("done", flush=True)


if __name__ == "__main__":
    spec = json.load(open(sys.argv[1]))
    main([(s["name"], s["text"], s.get("note", ""), s.get("overrides")) for s in spec])
