#!/usr/bin/env python3
"""TRACK V master runner. ONE process at a time -- two concurrent drivers both
issuing /free is how the cold discipline gets broken (it happened once here; the
affected arms are in results/crash/V/arms_void/).

    python run_v.py iso|proof|awkward|sweep|endctl

Every arm is resumable: an arm with a recorded status and execution_cached []
is skipped. Server 127.0.0.1:18188 only.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import v_drive, v_mk, v_strings, v_tok

HEAD = "head"        # denoise 0.35 + device cpu  -- the shipping artifact, the fix
MID = "mid"          # denoise 0.35 + device default -- the fix backed out, one widget
PREFIX = "prefix"    # denoise 0.80 + device default -- the brief's positive control

LADDER_BASE = "a woman's face"           # Track A's ladder, reused so the two maps compare


def ladder(n):
    """String of exactly n tokens, built the way Track A built its map."""
    s = LADDER_BASE + " the" * (n - v_tok.count(LADDER_BASE))
    got = v_tok.count(s)
    assert got == n, (n, got, s)
    return s


def arm(name, variant, text, tokens, note, overrides=None):
    if tokens is None:
        tokens = v_tok.count(text)
    return (name, tokens, note, {"variant": variant, "text": text, "overrides": overrides})


ISO = [
    arm("V_ISO_d035_cpu_a", HEAD, v_mk.CRASH46, 46,
        "2x2 cell: denoise 0.35 + device cpu -- the shipping artifact."),
    arm("V_ISO_d080_cpu_a", PREFIX, v_mk.CRASH46, 46,
        "2x2 cell: denoise 0.80 + device cpu.", {"620:110": {"device": "cpu"}}),
    arm("V_ISO_d035_gpu_b", MID, v_mk.CRASH46, 46,
        "2x2 cell repeat: denoise 0.35 + device default -- the isolating control."),
    arm("V_ISO_d035_cpu_b", HEAD, v_mk.CRASH46, 46,
        "2x2 cell repeat: the shipping artifact."),
    arm("V_ISO_d080_gpu_b", PREFIX, v_mk.CRASH46, 46,
        "2x2 cell repeat: the pre-fix positive control, interleaved."),
]

PROOF = [
    arm("V_P1a", HEAD, v_strings.P1_32, 32, "P1 the owner's proof string, byte-exact, 32 tokens (top edge of the lower crash band)."),
    arm("V_P2a", HEAD, v_strings.P2_46, 46, "P2 the known crashing string, 46 tokens."),
    arm("V_P1b", HEAD, v_strings.P1_32, 32, "P1 repeat."),
    arm("V_CTLm1", MID, v_strings.P1_32, 32, "Interleaved one-widget control: P1 with device default. Must still crash, or P1 is not testing anything."),
    arm("V_P2b", HEAD, v_strings.P2_46, 46, "P2 repeat."),
    arm("V_P3a", HEAD, v_strings.P3_50, 50, "P3 constructed 50-token string, deep in the upper crash region."),
    arm("V_CTLm2", MID, v_strings.P3_50, 50, "Interleaved one-widget control for P3."),
    arm("V_P4a", HEAD, v_strings.P4_16, 16, "P4 shipped placeholder, 16 tokens -- the regression guard, must stay clean."),
    arm("V_P5a", HEAD, v_strings.P5_0, 8, "P5 empty string, 8 tokens (the encoder's fixed chat wrapper). May refuse, but must refuse cleanly."),
    arm("V_P1c", HEAD, v_strings.P1_32, 32, "P1 third repeat -- weighting toward P1 per the brief."),
    arm("V_P2c", HEAD, v_strings.P2_46, 46, "P2 third repeat."),
    arm("V_CTLm3", PREFIX, v_mk.CRASH46, 46, "Mid-run pre-fix positive control. If this stops failing, everything after it is void."),
    arm("V_P4b", HEAD, v_strings.P4_16, 16, "P4 repeat."),
]

AWKWARD = [arm(f"V_{k}", HEAD, v, v_tok.count(v),
               f"Awkward set: {k}. Token count measured, not assumed.")
           for k, v in v_strings.AWKWARD.items()]

# Every awkward string except AW4/AW5 lands ABOVE 50 tokens, and Track A's map
# stops at 50. So a green awkward arm proves nothing on its own -- there is no
# evidence this instance fails at 72/103/166 tokens at all. These are the
# one-widget controls that make those arms readable.
AWKCTL = [arm(f"V_{k}_ctl", MID, v_strings.AWKWARD[k], v_tok.count(v_strings.AWKWARD[k]),
              f"Control for the awkward arm {k}: same string, device default. "
              f"Establishes whether this instance fails at that length at all.")
          for k in ("AW1_verylong", "AW2_punct", "AW3_nonenglish")]

# ---------------------------------------------------------------------------
# THE REFUTATION. V_AW3_nonenglish -- 103 tokens, mixed Japanese/Russian/Arabic/
# Greek/emoji -- errored at 622:403 WITH THE FIX APPLIED (device cpu, denoise
# 0.35, cold, queue empty), and its 621:163 tap carries the identical failure
# signature: (56,51,47) over 0.16969 of the frame, YOLO 0.4656, flat_frac 0.2387.
# Everything here exists to answer: is it reproducible, is it length or content,
# and does device default fail there too?
AW3 = v_strings.AWKWARD["AW3_nonenglish"]
AW3_ARMS = [
    arm("V_AW3_rep1", HEAD, AW3, 103, "Is the failure under the fix reproducible? Repeat 1."),
    arm("V_AW3_ctl", MID, AW3, 103, "Same string, device default. Does backing the fix out change anything here?"),
    arm("V_AW3_rep2", HEAD, AW3, 103, "Repeat 2 under the fix."),
    arm("V_AW3_ascii103", HEAD, ladder(103), 103,
        "LENGTH vs CONTENT: an ASCII ladder string at exactly 103 tokens, device cpu. "
        "If this is clean, 103 tokens is not the problem and the non-ASCII content is."),
    arm("V_AW3_ascii103_ctl", MID, ladder(103), 103, "Its device-default control."),
    arm("V_AW3_ascii166", HEAD, ladder(166), 166,
        "AW1 was 166 tokens and passed, but it is nearly all ASCII. ASCII ladder at 166, device cpu."),
    arm("V_AW3_jp_only", HEAD,
        "luna、21歳の女性、そばかす、緑の瞳、詳細な肌の質感、柔らかい窓明かり", None,
        "Isolating the script: Japanese only, device cpu."),
    arm("V_AW3_ru_only", HEAD,
        "luna, молодая женщина, веснушки, зелёные глаза, детальная текстура кожи", None,
        "Isolating the script: Russian only, device cpu."),
    arm("V_AW3_prefix_ctl", PREFIX, AW3, 103,
        "The same string on the fully pre-fix graph (denoise 0.80, device default)."),
]

SWEEP = []
for n in range(26, 51):
    SWEEP.append(arm(f"V_SW_tok{n}", HEAD, ladder(n), n,
                     f"Band sweep under the fix, {n} tokens, Track A's own ladder string. "
                     f"Track A's map on this instance: CRASH at 30-32 and 44-50, clean elsewhere."))
    if n in (32, 40, 46):
        SWEEP.append(arm(f"V_SW_ctl_tok{n}", MID, ladder(n), n,
                         f"Interleaved one-widget control at {n} tokens: same string, device default."))

ENDCTL = [
    arm("V_PCEND_prefix", PREFIX, v_mk.CRASH46, 46,
        "FINAL positive control, pre-fix graph. Everything after the last passing control is void."),
    arm("V_PCEND_mid", MID, v_mk.CRASH46, 46,
        "FINAL isolating control, denoise 0.35 + device default."),
    arm("V_PCEND_head", HEAD, v_mk.CRASH46, 46,
        "FINAL fix arm, immediately after the controls."),
]

# "the fix must be inert where nothing was wrong" -- 16 tokens is deep in a clean
# band, so head and mid should be indistinguishable there. Compared by objective
# image deltas, NOT by hashing output (banned on this project).
CLEAN = [
    arm("V_CLEAN_mid_16a", MID, v_strings.P4_16, 16, "Inertness check: 16 tokens, device default."),
    arm("V_CLEAN_head_16a", HEAD, v_strings.P4_16, 16, "Inertness check: 16 tokens, device cpu."),
    arm("V_CLEAN_mid_16b", MID, v_strings.P4_16, 16, "Inertness check repeat, device default -- gives the run-to-run floor on this box."),
    arm("V_CLEAN_head_16b", HEAD, v_strings.P4_16, 16, "Inertness check repeat, device cpu."),
    arm("V_CLEAN_mid_40a", MID, ladder(40), 40, "Inertness check at 40 tokens (clean band, longer prompt), device default."),
    arm("V_CLEAN_head_40a", HEAD, ladder(40), 40, "Inertness check at 40 tokens, device cpu."),
]

# Track E's account of the mechanism is that 620:114 is BISTABLE on numerical
# noise ~4e-7 relative. If that is right, the sampler seed is a vastly larger
# perturbation than the one the fix applies, so a fix that only holds at the
# shipped seed 1111111 is luck rather than a cure. Nothing in the brief or in
# Phase 3 covers this; it is the attack I most expect to work.
SEEDS = [
    arm(f"V_SEED_{s}_cpu", HEAD, v_mk.CRASH46, 46,
        f"Seed attack: 620:114.seed = {s}, device cpu. Shipped seed is 1111111.",
        {"620:114": {"seed": s}})
    for s in (1111112, 42, 987654321, 7)
] + [
    arm(f"V_SEED_{s}_gpu", MID, v_mk.CRASH46, 46,
        f"Seed attack control: 620:114.seed = {s}, device default.",
        {"620:114": {"seed": s}})
    for s in (1111112, 42)
]

# The SECOND place this failure has been seen is the EYES pass, not the face pass:
# Track A's E398_tok31 shipped `status: success` with both eyes solid black, by
# lengthening 622:398 (the eye prompt) from the shipped 28 tokens to 31 while
# leaving 620:106 on the safe placeholder. 622:398 encodes on the same 620:110, so
# if the fix is really about conditioning values it should cure that too. If it
# does not, the artifact still ships a black-region failure mode.
EYE398 = "perfect eyes, round pupils, round iris, symmetrical eyes, realistic eyes, perfect circles, round"
E398 = [
    arm("V_E398_tok31_gpu", MID, v_strings.P4_16, 16,
        "Eye-prompt attack CONTROL: 622:398 at 31 tokens, 620:106 on the safe placeholder, device default. Reproduces Track A's E398_tok31.",
        {"622:398": {"text": EYE398 + " the the the"}}),
    arm("V_E398_tok31_cpu", HEAD, v_strings.P4_16, 16,
        "Eye-prompt attack: same, device cpu. Does the fix reach the eyes pass?",
        {"622:398": {"text": EYE398 + " the the the"}}),
    arm("V_E398_tok31_cpu_b", HEAD, v_strings.P4_16, 16,
        "Eye-prompt attack repeat.",
        {"622:398": {"text": EYE398 + " the the the"}}),
]

STAGES = {"iso": ISO, "proof": PROOF, "awkward": AWKWARD, "sweep": SWEEP,
          "endctl": ENDCTL, "clean": CLEAN, "seeds": SEEDS, "e398": E398,
          "awkctl": AWKCTL, "aw3": AW3_ARMS}

# --- full 88-node renders -------------------------------------------------
# The probe stages freeze the base image at trackA_base137.png. The SHIPPED file's
# SDXL prompt differs from the one that base was rendered with (483.prompt_batch_data
# lost "light freckles across her nose and cheeks" between R4 and HEAD), so a full
# render exercises a different base. Control first: if `mid` does not crash on the
# full graph, the full graph cannot validate anything and the probe stays the
# authority.
FULL = [
    arm("V_FULL_mid_46", MID, v_mk.CRASH46, 46,
        "FULL 88-node render, device default. The full-graph positive control."),
    arm("V_FULL_head_46", HEAD, v_mk.CRASH46, 46,
        "FULL 88-node render, device cpu -- the shipping artifact end to end."),
    arm("V_FULL_head_32", HEAD, v_strings.P1_32, 32,
        "FULL 88-node render, device cpu, the owner's own proof string."),
]

if __name__ == "__main__":
    for s in sys.argv[1:]:
        mk = v_mk.full_graph if s == "full" else v_mk.probe_graph
        arms = FULL if s == "full" else STAGES[s]
        print(f"===== STAGE {s}  ({len(arms)} arms) =====", flush=True)
        v_drive.run_set(arms, mk)
