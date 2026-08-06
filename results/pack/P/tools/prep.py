#!/usr/bin/env python3
"""Apply the two submitted-prompt modifications, unchanged from P2-RENDER/R1."""
import json, sys
def prepare(api_path):
    g = json.load(open(api_path))
    g["419"]["inputs"].pop("rgthree_comparer", None)
    assert g["619:603"]["class_type"] == "INSTARAW_ImageFilter", g["619:603"]["class_type"]
    g["619:603"]["inputs"]["pick_list"] = "0"
    return g
if __name__ == "__main__":
    json.dump(prepare(sys.argv[1]), open(sys.argv[2], "w"), indent=1)
