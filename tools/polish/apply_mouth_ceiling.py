#!/usr/bin/env python3
"""I11: raise the mouth-guard ceiling out of the real-lips range.

620:648 SEGSRangeFilterDetailerHookProvider dropped every lips segment whose
crop area exceeded 1,700,000 px². The full server log (203 decisions) shows
real lips at 1.77M-2.06M being dropped — close-up renders silently lose all
mouth detail — while the false positive the guard exists to kill (the lips
detector latching onto the whole frame) measures 9,289,728, with NOTHING
observed between 2.06M and 9.29M. New ceiling 4,000,000: passes every real
lips segment ever logged with a 2x margin, still kills the full-frame false
positive with a 2.3x margin. Title updated to say what it does; the old
"(see note)" pointed at a note that does not exist.

usage: apply_mouth_ceiling.py <in.json> <out.json>
"""
import json, sys, collections

SG = "d6db378b-b089-4636-91bb-6e0cf9a81503"
NEW_MAX = 4000000


def main(src, dst):
    d = json.load(open(src, encoding="utf-8"), object_pairs_hook=collections.OrderedDict)
    sg = next(s for s in d["definitions"]["subgraphs"] if s["id"] == SG)
    n = next(n for n in sg["nodes"] if n["id"] == 648)
    assert n["type"] == "SEGSRangeFilterDetailerHookProvider"
    assert n["widgets_values"] == ["area(=w*h)", True, 0, 1700000], n["widgets_values"]
    n["widgets_values"][3] = NEW_MAX
    n["title"] = "Mouth size guard: drop full-frame false detections (area > 4M)"
    with open(dst, "w", encoding="utf-8") as fh:
        json.dump(d, fh, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
