#!/usr/bin/env python3
"""E8 -- the sage-attention survey the coordinator asked for.

`aiofm_setup.sh` installs sageattention but nothing enables it; a buyer's
template may well pass `--use-sage-attention`. This runs Track A's probe arms on
a Track E server started WITH that flag (`:32003`, log says "Using sage
attention").

Read the caveat in notes/E-rootcause.md before quoting this: Track E's own
servers do NOT reproduce the crash at all, so these arms cannot test whether sage
removes the bands. They can only test whether sage *creates* a failure where
this instance was clean.
"""
import sys, os
os.environ.setdefault("E_SERVER", "127.0.0.1:32003")
os.environ.setdefault("E_OUTDIR", "/workspace/trackE/output")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import e_drive, mk, strings

TOK30 = "a woman's face" + " the" * 18

ARMS = [
    ("E_sage_placeholder", strings.PLACEHOLDER, "sage: shipped placeholder, 16 tokens."),
    ("E_sage_crashstring", strings.CRASH, "sage: the known-crashing 46-token string."),
    ("E_sage_tok30", TOK30, "sage: 30 tokens, Track A's T-family filler."),
]

if __name__ == "__main__":
    for name, text, note in ARMS:
        g = mk.probe_graph(text, "trackA_base137.png")
        e_drive.run_arm(name, g, note=note)
