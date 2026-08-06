#!/usr/bin/env python3
"""Emit the V-verify grid as markdown, straight from the recorded arms."""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import v_check

ORDER_HINT = ["V_PC1", "V_ISO", "V_P", "V_CTL", "V_AW", "V_SW", "V_SEED", "V_E398",
              "V_CLEAN", "V_FULL", "V_PCEND"]


def y(x):
    return {True: "pass", False: "**FAIL**", None: "n/a"}[x]


def main(ref=None, only=None):
    rows = v_check.run(ref_arm=ref)
    json.dump(rows, open("/workspace/nsfw-fix/results/crash/V/out/v_checks.json", "w"), indent=1)
    keys = sorted(rows, key=lambda k: (next((i for i, p in enumerate(ORDER_HINT)
                                             if k.startswith(p)), 99), k))
    print("| arm | string (`620:106`) | tokens | `110.device` | `114.denoise` | prompt_id | cached | exec s | A | B | C | D | verdict |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for k in keys:
        r = rows[k]
        if only and not k.startswith(only):
            continue
        t = json.load(open(f"/workspace/nsfw-fix/results/crash/V/arms/{k}/meta.json")).get("text_106", "")
        s = repr(t)
        s = (s[:46] + "…" + s[-1]) if len(s) > 48 else s
        s = s.replace("|", "\\|")
        print(f"| `{k}` | `{s}` | {r['tokens']} | {r['device_110']} | {r['denoise_114']} | "
              f"`{r['prompt_id'][:8]}` | {r['cached']} | {r['exec_seconds']} | "
              f"{y(r['A'])} | {y(r['B'])} | {y(r['C'])} | {y(r['D'])} | "
              f"{'**PASS**' if r['pass'] else '**FAIL**'} |")
    print()
    print("| arm | judged on | exact-black | biggest 1-RGB blob | biggest non-white blob | YOLO max conf | error node |")
    print("|---|---|---|---|---|---|---|")
    for k in keys:
        r = rows[k]
        if only and not k.startswith(only):
            continue
        f = r["delivered"] or r["tap163"] or {}
        print(f"| `{k}` | {r['judged_on']} | {f.get('exact_black_frac')} | "
              f"{f.get('largest_single_rgb_cc_frac')} {f.get('largest_single_rgb_cc_rgb')} | "
              f"{f.get('largest_nonwhite_rgb_cc_frac')} {f.get('largest_nonwhite_rgb_cc_rgb')} | "
              f"{f.get('yolo_face_max_conf')} | {r['error_node'] or '-'} |")


if __name__ == "__main__":
    main(ref=(sys.argv[1] if len(sys.argv) > 1 else None),
         only=(sys.argv[2] if len(sys.argv) > 2 else None))
