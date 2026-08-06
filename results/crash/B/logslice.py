#!/usr/bin/env python3
"""Slice the 28191 server log into per-prompt blocks and pull the detector events.

The log is the only place the *detector* outcomes are visible -- /history records
the exception but not "YOLO found nothing here and something there".  tqdm writes
with \\r, so the file is normalised to newlines before matching.
"""
import re, sys

LOG = "/tmp/claude-0/-workspace-nsfw-fix/47375d2b-87bd-4073-a1e2-67796f8c1345/scratchpad/r3comfy.log"

KEEP = re.compile(
    r"^(got prompt"
    r"|Prompt executed in .*"
    r"|!!! Exception during processing.*"
    r"|0: \d+x\d+ .*"                       # ultralytics detection summary
    r"|Detailer: segment upscale for .*"
    r"|\[mask_to_segs\].*"
    r"|# of Detected SEGS: .*"
    r"|No faces detected in controlnet.*"
    r"|Detailer: force inpaint"
    r"|\[Impact Pack\] .*"
    r")\s*$"
)


def main():
    lines = open(LOG, errors="replace").read().replace("\r", "\n").split("\n")
    blocks, cur = [], None
    for ln in lines:
        ln = ln.strip()
        if ln == "got prompt":
            cur = []
            blocks.append(cur)
            continue
        if cur is None:
            continue
        if KEEP.match(ln):
            cur.append(ln)
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    for i, b in enumerate(blocks):
        if i < start:
            continue
        print(f"\n===== run #{i} =====")
        for ln in b:
            if ln.startswith("[Impact Pack]"):
                continue
            print("  " + ln[:150])


if __name__ == "__main__":
    main()
