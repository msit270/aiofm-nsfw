#!/usr/bin/env python3
"""Run-3 arm driver. Reuses Track V's proven tooling (cold discipline, ws
recording, /free poll) with evidence redirected to results/run3/.

    python3 r3.py pc103          # positive control, current bytes, 103 tokens
    python3 r3.py <stage>        # stages defined below as they are added

Server 127.0.0.1:18188 ONLY, same as Track V. One process at a time.
"""
import sys, os, json

HERE = os.path.dirname(os.path.abspath(__file__))
VTOOLS = "/workspace/nsfw-fix/results/crash/V/tools"
sys.path.insert(0, VTOOLS)
import v_drive, v_mk, v_tok  # noqa: E402

v_drive.ROOT = "/workspace/nsfw-fix/results/run3"


def ladder(n):
    s = "a woman's face" + " the" * (n - v_tok.count("a woman's face"))
    assert v_tok.count(s) == n, (n, v_tok.count(s))
    return s


def run(name, graph, note, tokens=None):
    return v_drive.run_arm(name, graph, note, tokens)


def pc103():
    """Positive control: the CURRENT shipping bytes (head = denoise 0.35 +
    device cpu), full 88-node graph, 103-token ASCII ladder. V-verify proved
    this crashes at 622:403 on :18188 on the probe; this is the full-graph
    same-day control for run 3. Expect: error at 622:403."""
    g = v_mk.full_graph("head", ladder(103))
    run("R3_PC_head_103", g, "Run-3 positive control: current bytes, 103 tokens, full graph. Expect 622:403 error.", 103)


def pc46mid():
    """Secondary control at 46 tokens with the fix backed out (device default).
    Confirms the classic band also still reproduces on this instance today."""
    g = v_mk.full_graph("mid", v_mk.CRASH46)
    run("R3_PC_mid_46", g, "Run-3 positive control 2: device default, 46 tokens, full graph. Expect 622:403 error.", 46)


STAGES = {"pc103": pc103, "pc46mid": pc46mid}

if __name__ == "__main__":
    for s in sys.argv[1:]:
        STAGES[s]()
