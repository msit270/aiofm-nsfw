#!/usr/bin/env python3
"""A3 sheet: seven 17-word prompts, all different, labelled by token count."""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sheet_ladder import main as build

A = "/workspace/nsfw-fix/results/crash/A"

ORDER = [
    ("placeholder  (4w)", "A1_gate_placeholder", None),
    ("L_w17  the original", "L_w17", 17),
    ("C2 gardener", "A3_C2_gardener_w17", None),
    ("swap: 'fine'", "A3_swap_fine", None),
    ("swap: 'Tuesday'", "A3_swap_Tuesday", None),
    ("swap: 'obvious'", "A3_swap_obvious", None),
    ("C1 fisherman", "A3_C1_fisherman_w17", None),
    ("C3 locomotive", "A3_C3_locomotive_w17", None),
    ("C4 committee", "A3_C4_committee_w17", None),
]

if __name__ == "__main__":
    # patch in measured token counts by rewriting ladder_tokens_full for these arms
    sys.path.insert(0, "/workspace/ComfyUI")
    import comfy.text_encoders.z_image as z
    tok = z.ZImageTokenizer()
    tk = json.load(open(os.path.join(A, "ladder_tokens_full.json")))
    order = []
    for label, arm, _ in ORDER:
        mp = os.path.join(A, "arms", arm, "meta.json")
        txt = json.load(open(mp)).get("text_106", "")
        n = len(tok.tokenize_with_weights(txt)["qwen3_4b"][0])
        key = f"_{arm}"
        tk[key] = {"words": len(txt.split()), "tokens": n, "text": txt}
        order.append((label, arm, key))
    json.dump(tk, open(os.path.join(A, "ladder_tokens_full.json"), "w"), indent=1)
    print(build(order, out=os.path.join(A, "A3_content_sheet.png")))
