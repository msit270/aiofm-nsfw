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


GUARDED = "/workspace/nsfw-fix/results/run3/guard/api_guarded.json"


def guarded_graph(text, overrides=None, pick=0):
    """Arm on the GUARDED conversion (browser export of commit 6de805d),
    mutated exactly the way v_mk.full_graph mutates the unguarded one."""
    g = v_mk.norm(json.load(open(GUARDED)))
    v_mk.set_loras(g)
    g["620:106"]["inputs"]["text"] = text
    g["619:603"]["inputs"]["pick_list"] = str(pick)
    for nid, kv in (overrides or {}).items():
        g[nid]["inputs"].update(kv)
    g["TAP163"] = {"class_type": "SaveImage",
                   "inputs": {"images": ["621:163", 0],
                              "filename_prefix": "run3/tap163"},
                   "_meta": {"title": "run3 tap: 621:163 (mouth-stage image)"}}
    return g


def forced():
    """The deterministic pair: force 'detector finds nothing' by raising the
    face detector threshold to 0.99 (clean faces score ~0.89-0.90). Bistability
    cannot rescue these arms; they exercise the exact crash mechanism.
      unguarded -> must ERROR at 622:403 (same-day proof the mechanism is live)
      guarded   -> must SUCCEED, eyes subtree unscheduled, 662 shows False."""
    thr = {"622:424": {"threshold": 0.99}}
    g = v_mk.full_graph("head", v_mk.PLACEHOLDER16, overrides=thr)
    run("R3_FORCED_unguard", g,
        "threshold 0.99 on pre-guard bytes: expect error 622:403 (empty-SEGS mechanism, deterministic).", 16)
    g = guarded_graph(v_mk.PLACEHOLDER16, overrides=thr)
    run("R3_FORCED_guard", g,
        "threshold 0.99 on guarded bytes: expect success, eyes skipped, PreviewAny=False.", 16)


def ab16():
    """Happy-path inertness: guarded vs unguarded, shipped placeholder, cold,
    fixed shipped seeds. Deliverable is a PIXEL comparison of the 505 outputs
    (PNG file bytes necessarily differ: the embedded workflow metadata carries
    the guard nodes)."""
    run("R3_AB_unguard_16", v_mk.full_graph("head", v_mk.PLACEHOLDER16),
        "A/B baseline: pre-guard bytes, placeholder, cold.", 16)
    run("R3_AB_guard_16", guarded_graph(v_mk.PLACEHOLDER16),
        "A/B: guarded bytes, placeholder, cold. Pixels must equal baseline.", 16)


def guard_mid46():
    """THE arm that matters: the configuration proven to crash on this instance
    TODAY (R3_PC_mid_46: device default, 46 tokens, full graph, error 622:403),
    re-run identically but on the guarded bytes. Guard must convert the crash
    into success + eyes-skip + PreviewAny False."""
    g = guarded_graph(v_mk.CRASH46, overrides={"620:110": {"device": "default"}})
    run("R3_GUARD_mid46", g,
        "Guarded bytes, device default, 46 tokens -- the same-day crashing config. Expect success + eyes skipped.", 46)


def guard_bands():
    """Real-prompt bands on the guarded shipping config (device cpu)."""
    run("R3_GUARD_46", guarded_graph(v_mk.CRASH46),
        "46-token crash string on guarded bytes: expect healthy success.", 46)
    run("R3_GUARD_103", guarded_graph(ladder(103)),
        "103-token ladder on guarded bytes: success required; healthy or loud-degraded.", 103)
    run("R3_GUARD_110", guarded_graph(ladder(110)),
        "110-token ladder on guarded bytes: success required.", 110)


def dual_graph(text, overrides=None):
    """DoD-5 candidate: keep 620:110 on cpu (the band fix for the buyer-variable
    face prompt) but encode the FIXED eye prompts on a second, GPU-resident
    CLIPLoader — so the eyes stage sees pre-fix conditioning bytes and the
    catchlight regression should revert, while the face pass keeps the fix."""
    g = guarded_graph(text, overrides=overrides)
    assert g["620:110"]["inputs"]["device"] == "cpu"
    g["DUALCLIP"] = {"class_type": "CLIPLoader",
                     "inputs": {"clip_name": g["620:110"]["inputs"]["clip_name"],
                                "type": g["620:110"]["inputs"]["type"],
                                "device": "default"},
                     "_meta": {"title": "run3 dual-loader experiment: GPU encoder for the fixed eye prompts"}}
    assert g["622:398"]["class_type"] == "CLIPTextEncode"
    assert g["622:394"]["class_type"] == "CLIPTextEncode"
    g["622:398"]["inputs"]["clip"] = ["DUALCLIP", 0]
    g["622:394"]["inputs"]["clip"] = ["DUALCLIP", 0]
    return g


def dual16():
    run("R3_DUAL_16", dual_graph(v_mk.PLACEHOLDER16),
        "dual-loader: face/mouth on cpu, eye encodes on GPU. 16-token placeholder. Eye tiles must match the default arm.", 16)
    g = guarded_graph(v_mk.PLACEHOLDER16, overrides={"620:110": {"device": "default"}})
    run("R3_DEFAULT_16", g,
        "reference: everything on default (pre-fix conditioning), guarded bytes, placeholder. The pristine-eye reference.", 16)


def dual46():
    run("R3_DUAL_46", dual_graph(v_mk.CRASH46),
        "dual-loader at 46 tokens: face pass keeps cpu conditioning, band must stay closed (healthy face).", 46)


def mouth_ab():
    """I11: the mouth-guard ceiling. Single-variable pair on the exact recorded
    R1 A0_baseline graph (its lips segment measured 1,933,356 -- inside the
    1.7M-2.06M drop band). Only 620:648.max_value differs. Old config on
    purpose: current shipped-prompt renders sit at ~0.37M and never reach the
    window, but buyer close-ups do; this is the recorded configuration that
    demonstrates the ceiling's effect with one variable."""
    base = json.load(open("/workspace/nsfw-fix/results/face/arms/A0_baseline/api_graph.json"))
    a = json.loads(json.dumps(base))
    run("R3_MOUTH_ceil17", a,
        "A0_baseline graph verbatim, ceiling 1,700,000: expect [filter] drop, mouth pass skipped.", None)
    b = json.loads(json.dumps(base))
    b["620:648"]["inputs"]["max_value"] = 4000000
    run("R3_MOUTH_ceil40", b,
        "A0_baseline + ceiling 4,000,000 (the only change): expect [in] pass, mouth pass runs.", None)


FEATHERED = "/workspace/nsfw-fix/results/run3/guard/api_feather.json"


def feather16():
    """P14 A/B: the feathered eyes composite vs the hard paste. Baseline is
    R3_AB_guard_16 (same bytes minus the feather, same seeds, cold)."""
    g = v_mk.norm(json.load(open(FEATHERED)))
    v_mk.set_loras(g)
    g["620:106"]["inputs"]["text"] = v_mk.PLACEHOLDER16
    g["619:603"]["inputs"]["pick_list"] = "0"
    run("R3_FEATHER_16", g,
        "feathered composite (664 FeatherMask 30px into 418.mask), placeholder, cold. Compare boundary ring vs R3_AB_guard_16.", 16)


STAGES = {"pc103": pc103, "pc46mid": pc46mid, "forced": forced, "ab16": ab16,
          "guard_mid46": guard_mid46, "guard_bands": guard_bands,
          "dual16": dual16, "dual46": dual46, "mouth_ab": mouth_ab,
          "feather16": feather16}

if __name__ == "__main__":
    for s in sys.argv[1:]:
        STAGES[s]()
