#!/usr/bin/env python3
"""TRACK V -- token counts, measured with the class 620:110 actually instantiates.

`620:110 CLIPLoader` has `type: "lumina2"` on its widget, but `comfy/sd.py`
dispatches on `detect_te_model(state_dict)` FIRST; qwen.safetensors resolves to
TEModel.QWEN3_4B and sd.py instantiates comfy.text_encoders.z_image.ZImageTokenizer.
So that is the class counted here. Verified independently of Track A/E's numbers.
"""
import sys, json
sys.path.insert(0, "/workspace/ComfyUI")
from comfy.text_encoders.z_image import ZImageTokenizer

_tok = ZImageTokenizer()


def count(s):
    return len(_tok.tokenize_with_weights(s)["qwen3_4b"][0])


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--json":
        data = json.load(open(sys.argv[2]))
        print(json.dumps({k: count(v) for k, v in data.items()}, indent=1))
    else:
        for s in sys.argv[1:]:
            print(f"{count(s):4d}  {s!r}")
