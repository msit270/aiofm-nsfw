#!/usr/bin/env python3
"""The token-count map: every measured conditioning length and its outcome,
pooled across ALL arms (ladder, A3 controls, swaps and the T_tok family)."""
import json, os, sys
sys.path.insert(0, "/workspace/ComfyUI")
import comfy.text_encoders.z_image as z

A = "/workspace/nsfw-fix/results/crash/A"


# Arms that must not enter the map:
#  TAP114_*  -- graph truncated at 621:163, so they CANNOT reach 622:403 and
#               cannot report a crash. Their taps are still used elsewhere.
#  REP_w17 / CTL_placeholder_after_REP_w17 -- VOID: that control failed with
#               execution_cached: 16, so neither arm was cold. Both re-run as REP2_*.
EXCLUDE = {"REP_w17", "CTL_placeholder_after_REP_w17"}
#  E398_*   -- the variable in those arms is 622:398 (the EYE prompt), not
#              620:106, so their 620:106 length says nothing about the outcome.
EXCLUDE_PREFIX = ("TAP114_", "A0_", "E398_")


def main():
    tok = z.ZImageTokenizer()
    y = json.load(open(os.path.join(A, "arm_yolo.json")))
    rows = []
    for arm, r in y.items():
        if arm in EXCLUDE or arm.startswith(EXCLUDE_PREFIX):
            continue
        mp = os.path.join(A, "arms", arm, "meta.json")
        if not os.path.exists(mp):
            continue
        m = json.load(open(mp))
        txt = m.get("text_106")
        if txt is None or r.get("status") is None:
            continue
        if m.get("cached") not in (0,):        # not cold -> not evidence
            continue
        n = len(tok.tokenize_with_weights(txt)["qwen3_4b"][0])
        rows.append({"arm": arm, "tokens": n, "words": len(txt.split()),
                     "status": r["status"], "conf": r.get("highest_conf"),
                     "family": ("T" if arm.startswith("T_tok") else
                                "ladder" if arm.startswith(("L_w", "REP")) else
                                "control" if arm.startswith("CTL") or "placeholder" in arm else
                                "A3" if arm.startswith("A3") else "other"),
                     "text": txt})
    by = {}
    for r in rows:
        by.setdefault(r["tokens"], []).append(r)
    out = []
    for n in sorted(by):
        arms = by[n]
        crash = [a for a in arms if a["status"] == "error"]
        clean = [a for a in arms if a["status"] == "success"]
        out.append({"tokens": n, "n_arms": len(arms), "n_crash": len(crash),
                    "n_clean": len(clean),
                    "verdict": ("CRASH" if crash and not clean else
                                "clean" if clean and not crash else "MIXED"),
                    "arms": [a["arm"] for a in arms]})
    json.dump(out, open(os.path.join(A, "token_map.json"), "w"), indent=1)
    print(f"{'tok':>4}  {'verdict':7} {'n':>2}  arms")
    for o in out:
        print(f"{o['tokens']:>4}  {o['verdict']:7} {o['n_arms']:>2}  {', '.join(o['arms'])}")
    mixed = [o for o in out if o["verdict"] == "MIXED"]
    print("\nMIXED (same token count, different outcome):", [o["tokens"] for o in mixed] or "none")
    return out


if __name__ == "__main__":
    main()
