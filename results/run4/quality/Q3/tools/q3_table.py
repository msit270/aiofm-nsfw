#!/usr/bin/env python3
"""Emit the per-lever markdown tables for notes/Q3-zimage.md from the
per-arm meta.json + deltas_vs_*.json files. Read-only."""
import glob, json, os

Q3 = "/workspace/nsfw-fix/results/run4/quality/Q3"


def m(arm):
    return json.load(open(f"{Q3}/{arm}/meta.json"))


def d(arm, base="A0_baseline"):
    p = f"{Q3}/{arm}/deltas_vs_{base}.json"
    return json.load(open(p)) if os.path.exists(p) else None


def seg_line(arm, which):
    """which: index into the detailer 'segment upscale' lines (0 sdxl-face,
    1 hands, 2 z-face, 3 eyes on the balcony comp; portrait may differ)."""
    lines = [l for l in m(arm)["detailer_log_lines"] if "segment upscale" in l]
    return lines[which] if which < len(lines) else "(absent)"


def row(arm, base="A0_baseline", tag="final"):
    mm = m(arm)
    dd = d(arm, base)
    if dd is None or tag not in dd["tags"]:
        return f"| {arm} | (deltas not computed) | {mm['exec_seconds']} | {mm['vram']['arm_server_peak_mib']} |"
    t = dd["tags"][tag]
    return ("| {a} | {p} | {fmean} | {fpct} | {facep} | {eyep} | {moup} | {pig} | {blob} | {lap} | {ex} | {vr} |"
            .format(a=arm, p=mm["param"].split("|")[0].strip()[:44],
                    fmean=t["frame_mean_abs"], fpct=t["frame_pct_gt8"],
                    facep=t["face_pct_gt8"], eyep=t["eyeband_pct_gt8"],
                    moup=t["mouthband_pct_gt8"],
                    pig=f"{t['pigment_pct_arm']} (base {t['pigment_pct_base']})",
                    blob=f"{t['brightblob_pct_arm']} (base {t['brightblob_pct_base']})",
                    lap=f"{t['lapvar_face_arm']} (base {t['lapvar_face_base']})",
                    ex=mm["exec_seconds"], vr=mm["vram"]["arm_server_peak_mib"]))


HDR = ("| arm | change | frame mean|Δ| | frame %>8 | face %>8 | eye %>8 | mouth %>8 "
       "| pigment % | bright-blob % | lapvar(face) | exec s | VRAM MiB |\n"
       "|---|---|---|---|---|---|---|---|---|---|---|---|")

if __name__ == "__main__":
    import sys
    arms = sys.argv[1:]
    base = "A0_baseline"
    if arms and arms[0].startswith("--base="):
        base = arms[0].split("=", 1)[1]
        arms = arms[1:]
    print(HDR)
    for a in arms:
        print(row(a, base))
