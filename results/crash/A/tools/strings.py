#!/usr/bin/env python3
"""The strings under test. Ladder = the crashing string truncated, SAME words,
SAME order. Content controls = same word count, completely different content."""

CRASH = ("luna, a young woman with light freckles across her nose and cheeks, "
         "natural skin texture with visible pores, detailed eyes, "
         "photorealistic portrait photograph, 85mm lens")
PLACEHOLDER = "TRIGGER, PROMPT FOR YOUR MODEL"

WORDS = CRASH.split(" ")
assert len(WORDS) == 25, len(WORDS)


def prefix(n):
    return " ".join(WORDS[:n])


# --- A3 content controls, all 25 words, no `luna`, no freckles, no camera words ---
CONTENT_25 = {
    # a different person's face -- the fairest same-length contrast
    "C1_fisherman": ("a bearded fisherman in his sixties, deep lines around the eyes, "
                     "sun-darkened forehead, grey stubble along the jaw, calm steady gaze, "
                     "a thick knitted collar"),
    "C2_gardener": ("an elderly gardener with a broad flat nose, heavy grey eyebrows, "
                    "deep creases on both cheeks, a straw hat pushed back off the damp "
                    "forehead"),
    # no face at all
    "C3_locomotive": ("a rusting freight locomotive parked on overgrown sidings, bramble "
                      "climbing the couplings, chipped enamel plates, oil stains spreading "
                      "across the sleepers, thistles waist high everywhere"),
    # no visual content at all -- length with the semantics stripped out
    "C4_committee": ("the committee approved the revised schedule on Tuesday and asked the "
                     "treasurer to circulate a summary before the next meeting of the "
                     "regional planning board"),
}

for _k, _v in CONTENT_25.items():
    assert len(_v.split(" ")) == 25, (_k, len(_v.split(" ")))


def content_at(n):
    """Truncate the content controls to n words."""
    return {k: " ".join(v.split(" ")[:n]) for k, v in CONTENT_25.items()}
