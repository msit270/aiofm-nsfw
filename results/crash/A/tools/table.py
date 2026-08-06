#!/usr/bin/env python3
"""Emit the results table straight from the recorded arm metadata, so nothing in
the write-up is transcribed by hand."""
import json, os, sys, glob

A = "/workspace/nsfw-fix/results/crash/A"


def rows(order=None):
    y = json.load(open(os.path.join(A, "arm_yolo.json")))
    tk = json.load(open(os.path.join(A, "ladder_tokens_full.json")))
    out = []
    names = order or sorted(y)
    for n in names:
        m = {}
        mp = os.path.join(A, "arms", n, "meta.json")
        if os.path.exists(mp):
            m = json.load(open(mp))
        r = y.get(n, {})
        words = m.get("words")
        if words is None and n.startswith("L_w"):
            words = int(n[3:])
        txt = m.get("text_106") or m.get("text") or r.get("text") or ""
        toks = None
        if words is not None and str(words) in tk and tk[str(words)]["text"] == txt:
            toks = tk[str(words)]["tokens"]
        out.append({
            "arm": n, "words": (len(txt.split()) if txt else 0), "tokens": toks,
            "status": r.get("status") or m.get("status"),
            "exec": r.get("exec_seconds") or m.get("exec_seconds"),
            "cached": r.get("cached") if r.get("cached") is not None else m.get("cached"),
            "err": m.get("error_node"), "conf": r.get("highest_conf"),
            "n06": (r.get("per_threshold") or {}).get("0.6", {}).get("n"),
            "flat": r.get("flat_frac"),
            "prompt_id": m.get("prompt_id"), "text": txt,
        })
    return out


def md(rs, show_text=False):
    h = "| arm | words | tokens | status | exec s | cached | conf @621:163 | n@0.6 | flat_frac | prompt_id |"
    s = [h, "|" + "---|" * 10]
    for r in rs:
        st = "**ERROR 622:403**" if r["status"] == "error" else r["status"]
        c = f"{r['conf']:.4f}" if r["conf"] is not None else "—"
        s.append(f"| `{r['arm']}` | {r['words']} | {r['tokens'] if r['tokens'] else '—'} | {st} | "
                 f"{r['exec']} | {r['cached']} | {c} | {r['n06']} | {r['flat']} | `{r['prompt_id']}` |")
    return "\n".join(s)


if __name__ == "__main__":
    rs = rows(sys.argv[1:] or None)
    print(md(rs))
