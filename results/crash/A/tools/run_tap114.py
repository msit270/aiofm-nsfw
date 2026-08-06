#!/usr/bin/env python3
"""Attribution arm: truncate the probe at 621:163 and ALSO tap 620:114's raw
output, before 620:111's colour match. Cannot reach 622:403, so it always saves
even when the same prompt would crash the full probe."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import drive, mk, strings

BASE_IMG = "trackA_base137.png"

if __name__ == "__main__":
    for name, text, note in [
        ("TAP114_w17", strings.prefix(17),
         "620:114 raw output for the FIRST CRASHING string (17 words). Graph truncated at 621:163 so it cannot reach 622:403."),
        ("TAP114_placeholder", strings.PLACEHOLDER,
         "620:114 raw output for the shipped placeholder -- the clean control for TAP114_w17."),
    ]:
        g = mk.tap_only_graph(text, BASE_IMG)
        drive.run_arm(name, g, note=note)
