#!/usr/bin/env python3
"""TRACK V strings. Every token count here is measured by v_tok.count(), i.e. by
comfy.text_encoders.z_image.ZImageTokenizer -- the class 620:110 actually
instantiates -- and asserted at import time. Nothing is taken from another
track's table.
"""
P1_32 = ("luna, 21 year old woman, freckles, green eyes, detailed skin texture, "
         "soft window light")
P2_46 = ("luna, a young woman with light freckles across her nose and cheeks, "
         "natural skin texture with visible pores, detailed eyes, "
         "photorealistic portrait photograph, 85mm lens")
P4_16 = "TRIGGER, PROMPT FOR YOUR MODEL"
P5_0 = ""

# P3: 47-50 tokens, constructed here. Same register as the shipped prompt so it
# is not testing "weird text" as well as length -- the awkward set does that.
P3_50 = ("luna, a young woman with light freckles across her nose and cheeks, "
         "natural skin texture with visible pores, detailed eyes, warm rim light, "
         "photorealistic portrait photograph, 85mm lens")

AWKWARD = {
    # very long -- an order of magnitude past anything measured so far
    "AW1_verylong": (
        "luna, a young woman photographed in a quiet north-facing studio on a "
        "grey afternoon, light freckles scattered across the bridge of her nose "
        "and over both cheekbones, natural skin texture with visible pores and "
        "fine vellus hair catching the light, faint shadows under the eyes, a "
        "small mole below the left jaw, dark hair pushed back behind one ear, "
        "detailed eyes with a clear catchlight from a large softbox placed "
        "slightly camera left and above, relaxed mouth, unretouched complexion "
        "with a little redness around the nostrils, photorealistic portrait "
        "photograph shot on an 85mm lens at f2 with shallow depth of field, "
        "colour graded gently towards neutral, no makeup, no jewellery, plain "
        "背景, calm expression, looking directly into the camera lens"),
    # punctuation-heavy -- nothing but delimiters and symbols around real words
    "AW2_punct": (
        "luna,,, ((21-year-old woman)) [freckles!!] {green eyes} <detailed skin> "
        "-- \"soft window light\"; 85mm/f1.4 @ 1/125s ... ***photoreal*** "
        "#portrait $$$ 100% ~~~ |||"),
    # non-English: Japanese, Russian, Arabic, Greek, emoji, combining accents
    "AW3_nonenglish": (
        "luna、21歳の女性、そばかす、緑の瞳、詳細な肌の質感、柔らかい窓明かり "
        "молодая женщина, веснушки, зелёные глаза "
        "امرأة شابة، نمش، عيون خضراء "
        "νεαρή γυναίκα, φακίδες 🌸👁️ éàüñçß"),
    # whitespace only -- the degenerate neighbour of the empty string
    "AW4_whitespace": "   \n\t  ",
    # a single token of content
    "AW5_oneword": "luna",
}


def _check():
    import v_tok
    got = {}
    for k, v in {"P1_32": P1_32, "P2_46": P2_46, "P3_50": P3_50,
                 "P4_16": P4_16, "P5_0": P5_0}.items():
        got[k] = v_tok.count(v)
    want = {"P1_32": 32, "P2_46": 46, "P4_16": 16, "P5_0": 8}
    for k, n in want.items():
        assert got[k] == n, (k, got[k], n)
    assert 47 <= got["P3_50"] <= 50, ("P3 out of the 47-50 band", got["P3_50"])
    for k, v in AWKWARD.items():
        got[k] = v_tok.count(v)
    return got


if __name__ == "__main__":
    import json
    print(json.dumps(_check(), indent=1))
