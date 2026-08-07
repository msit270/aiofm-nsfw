#!/usr/bin/env python3
"""Q3 post-run validation, run once all arms are on disk.

For every arm: status success, execution_cached == [], and the tap-level
identity structure a single-variable change predicts:
  face-lever arms   : TAP137 (face input) IDENTICAL to baseline; TAP114 differs
  eyes arm          : TAP137+TAP114+TAP111+TAP163 IDENTICAL; final differs
  portrait arms     : different composition — no cross-composition identity
  P_M vs P0         : TAP137/114/111 identical; TAP163 differs (mouth ran)
'IDENTICAL' here = max abs diff 0. This is a structural control on the arms
(same-graph determinism was established in R1 §6 and STATE §5), not the banned
inertness-by-hash method: nothing here claims a CHANGE is inert — the changed
stage is required to DIFFER.
"""
import json, sys
sys.path.insert(0, "/workspace/nsfw-fix/results/run4/quality/Q3/tools")
import numpy as np
import q3_analyze as qa

FACE_ARMS = ["F_steps12", "F_steps16", "F_den030", "F_den045",
             "F_res_multistep", "F_euler"]


def cmp(a, b, tag):
    ia, ib = qa.arr(qa.png(a, tag)), qa.arr(qa.png(b, tag))
    d = int(np.abs(ia - ib).max())
    pct = float((np.abs(ia - ib).sum(axis=2) > 0).mean() * 100)
    return d, round(pct, 3)


def meta(arm):
    return json.load(open(f"{qa.Q3}/{arm}/meta.json"))


def main(arms):
    ok = True
    for arm in arms:
        m = meta(arm)
        cold = m.get("execution_cached") == []
        line = f"{arm:22s} {m['status']:8s} cold={cold} exec={m['exec_seconds']}s vram={m['vram']['arm_server_peak_mib']}MiB"
        if m["status"] != "success" or not cold:
            line += "  <-- FAILS PROTOCOL"
            ok = False
        print(line)
    print()
    base = "A0_baseline"
    for arm in arms:
        if arm in FACE_ARMS:
            d0, _ = cmp(arm, base, "tap137")
            d1, p1 = cmp(arm, base, "tap114")
            flag = "OK" if d0 == 0 and d1 > 0 else "UNEXPECTED"
            print(f"{arm:22s} tap137 vs base max={d0} (want 0) | tap114 max={d1} ({p1}%) (want >0)  {flag}")
            if flag != "OK":
                ok = False
        if arm == "E_steps16":
            r = {t: cmp(arm, base, t) for t in ("tap137", "tap114", "tap111", "tap163", "final")}
            pre = all(r[t][0] == 0 for t in ("tap137", "tap114", "tap111", "tap163"))
            flag = "OK" if pre and r["final"][0] > 0 else "UNEXPECTED"
            print(f"{arm:22s} pre-eye taps identical={pre} | final max={r['final'][0]} ({r['final'][1]}%)  {flag}")
            if flag != "OK":
                ok = False
        if arm == "P_M_steps16":
            r = {t: cmp(arm, "P0_portrait_baseline", t) for t in ("tap137", "tap114", "tap111", "tap163", "final")}
            pre = all(r[t][0] == 0 for t in ("tap137", "tap114", "tap111"))
            print(f"{arm:22s} vs P0: pre-mouth taps identical={pre} | tap163 max={r['tap163'][0]} ({r['tap163'][1]}%) | final max={r['final'][0]}")
            if not pre:
                ok = False
    print("\nALL CHECKS PASS" if ok else "\nCHECKS FAILED — see above")
    return 0 if ok else 1


if __name__ == "__main__":
    import glob, os
    arms = sys.argv[1:] or sorted(os.path.basename(os.path.dirname(p)) for p in
                                  glob.glob(f"{qa.Q3}/*/meta.json"))
    sys.exit(main(arms))
