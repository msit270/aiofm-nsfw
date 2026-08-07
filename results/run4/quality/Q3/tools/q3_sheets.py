#!/usr/bin/env python3
"""Q3 contact sheets, one per lever, from the per-arm evidence dirs.

Wraps tools/contact_sheet.py (face + flat-skin, per-image YOLO detection,
1:1 verified) and results/run3/tools/analyze.py::eyesheet (eye/mouth bands).
Every tile label carries the change and the arm's server-side execution
seconds; the baseline tile is marked "BASELINE (ships)".
"""
import json, os, subprocess, sys

Q3 = "/workspace/nsfw-fix/results/run4/quality/Q3"
SHEETS = f"{Q3}/sheets"
CS = "/workspace/nsfw-fix/tools/contact_sheet.py"

LEVERS = {
    "L1_face_steps": ["A0_baseline", "F_steps12", "F_steps16"],
    "L2_face_denoise": ["A0_baseline", "F_den030", "F_den045"],
    "L3_face_sampler": ["A0_baseline", "F_res_multistep", "F_euler"],
    "L4_eyes_steps": ["A0_baseline", "E_steps16"],
    "L5_mouth_steps": ["P0_portrait_baseline", "P_M_steps16"],
}


def label(arm):
    m = json.load(open(f"{Q3}/{arm}/meta.json"))
    base = "BASELINE (ships) - " if m.get("baseline") else ""
    ov = m.get("overrides") or {}
    if not ov:
        what = "shipped settings"
    else:
        parts = []
        for nid, kv in ov.items():
            if nid == "483":
                parts.append("483 portrait prompt")
            else:
                parts.append(nid + " " + ", ".join(f"{k}={v}" for k, v in kv.items()))
        what = "; ".join(parts)
    return f"{base}{what} -- exec {m['exec_seconds']}s cold"


def final_png(arm):
    import glob
    c = sorted(glob.glob(f"{Q3}/{arm}/n505__*.png"))
    assert c, f"no final PNG for {arm}"
    return c[0]


def build(lever, arms):
    os.makedirs(SHEETS, exist_ok=True)
    args = ["python3", CS, "--out-dir", SHEETS, "--prefix", f"Q3_{lever}",
            "--max-width", "4000", "--skin-size", "110",
            "--note", f"Q3 {lever}: one variable per arm, cold fresh server each, fixed seeds, buyer-default prompt"]
    for a in arms:
        args += ["--arm", f"{a}|{label(a)}|{final_png(a)}"]
    print(" ".join(args))
    r = subprocess.run(args, capture_output=True, text=True)
    print(r.stdout[-3000:])
    if r.returncode != 0:
        print(r.stderr[-2000:], file=sys.stderr)
    return r.returncode


def bands(lever, arms):
    """eye + mouth band strips via run3 analyze.py (per-image YOLO)."""
    sys.path.insert(0, "/workspace/nsfw-fix/results/run3/tools")
    import analyze
    analyze.ARMS = Q3          # its delivered() globs <arm>/n505__*.png
    specs = [f"{a}:{label(a)}" for a in arms]
    analyze.eyesheet(f"{SHEETS}/Q3_{lever}_eyeband.png", specs,
                     band=(0.18, 0.55),
                     banner=f"Q3 {lever} EYE BAND - 1:1 native, per-image YOLO face box, cold fresh server per arm, fixed seeds.\n"
                            f"Baseline tile is labelled BASELINE (ships).")
    analyze.eyesheet(f"{SHEETS}/Q3_{lever}_mouthband.png", specs,
                     band=(0.55, 1.0),
                     banner=f"Q3 {lever} MOUTH BAND - 1:1 native, per-image YOLO face box, cold fresh server per arm, fixed seeds.\n"
                            f"Baseline tile is labelled BASELINE (ships).")


if __name__ == "__main__":
    todo = sys.argv[1:] or list(LEVERS)
    for lever in todo:
        arms = [a for a in LEVERS[lever] if os.path.exists(f"{Q3}/{a}/meta.json")]
        if len(arms) < 2:
            print(f"[{lever}] fewer than 2 arms ready — skipped")
            continue
        build(lever, arms)
        bands(lever, arms)
