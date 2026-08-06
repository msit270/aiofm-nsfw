#!/usr/bin/env python3
"""Track V's token map under the fix, laid against Track A's map without it.

Track A measured, on this same instance with device `default`:
  clean 11-29, CRASH 30-32, clean 33-43, CRASH 44-50 (unbroken to the top tested).
The question this answers is whether the fix removed the bands or merely moved them.
"""
import json, os, glob, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import v_check

ROOT = "/workspace/nsfw-fix/results/crash/V"
A_MAP = "/workspace/nsfw-fix/results/crash/A/token_map.json"


def main():
    a = {r["tokens"]: r["verdict"] for r in json.load(open(A_MAP))}
    rows = {}
    for d in sorted(glob.glob(os.path.join(ROOT, "arms", "V_SW_*"))):
        p = os.path.join(d, "meta.json")
        if not os.path.exists(p):
            continue
        m = json.load(open(p))
        name = m["arm"]
        ctl = "_ctl_" in name
        rows.setdefault(m["tokens"], {}).setdefault("ctl" if ctl else "fix", []).append(m)
    checks = v_check.run(names={os.path.basename(d) for d in glob.glob(os.path.join(ROOT, "arms", "V_SW_*"))})
    print("| tokens | Track A (device default) | V control (device default) | V under fix (device cpu) | A/B/C/D |")
    print("|---|---|---|---|---|")
    for n in sorted(rows):
        fix = rows[n].get("fix", [])
        ctl = rows[n].get("ctl", [])
        f = fix[0] if fix else None
        c = ctl[0] if ctl else None
        j = checks.get(f["arm"], {}) if f else {}
        abcd = "".join({True: "Y", False: "N", None: "-"}[j.get(k)] for k in "ABCD") if j else "-"
        print(f"| {n} | {a.get(n, '-')} | "
              f"{(c['status'] + (' ' + str(c['error_node']) if c.get('error_node') else '')) if c else '-'} | "
              f"{(f['status'] + (' ' + str(f['error_node']) if f.get('error_node') else '')) if f else '-'} | "
              f"{abcd} |")
    bad = [n for n in sorted(rows) if rows[n].get("fix") and rows[n]["fix"][0]["status"] != "success"]
    print()
    print(f"tokens swept under the fix: {sorted(rows)}")
    print(f"NON-SUCCESS under the fix: {bad if bad else 'none'}")


if __name__ == "__main__":
    main()
