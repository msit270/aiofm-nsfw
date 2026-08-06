#!/usr/bin/env python3
"""A4 contact sheet: the image handed to the failing detector 622:424, from a
CRASHING arm and a CLEAN arm, side by side at 1:1.

The two panels are DIFFERENT CONFIGURATIONS (they differ in 620:106.inputs.text),
so the header is red per the brief."""
import json, os
from PIL import Image, ImageDraw, ImageFont

OUT = "/workspace/nsfw-fix/results/crash/A/A4_contact_sheet.png"
RED = (200, 30, 25)
BG = (250, 250, 248)
INK = (20, 20, 20)
BOX = (848, 790, 2196, 2726)          # union of the two YOLO detections, padded to even


def font(sz, bold=False):
    for p in ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else
              "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
              "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else
              "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"]:
        if os.path.exists(p):
            return ImageFont.truetype(p, sz)
    return ImageFont.load_default()


def build(panels, header_lines, sub_lines, out=OUT):
    """panels: list of (title_lines, image_path)"""
    crops = [Image.open(p).convert("RGB").crop(BOX) for _, p in panels]
    cw, ch = crops[0].size
    gut = 24
    pad = 28
    hdr_h = 40 + 46 * len(header_lines) + 30 * len(sub_lines) + 24
    lab_h = 34 * max(len(t) for t, _ in panels) + 20
    W = pad * 2 + cw * len(crops) + gut * (len(crops) - 1)
    H = hdr_h + lab_h + ch + pad
    sheet = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(sheet)

    d.rectangle([0, 0, W, hdr_h - 12], fill=RED)
    y = 18
    for ln in header_lines:
        d.text((pad, y), ln, font=font(38, True), fill=(255, 255, 255))
        y += 46
    for ln in sub_lines:
        d.text((pad, y), ln, font=font(23), fill=(255, 235, 232))
        y += 30

    x = pad
    for (titles, _), crop in zip(panels, crops):
        yy = hdr_h
        for i, t in enumerate(titles):
            d.text((x, yy), t, font=font(26, i == 0), fill=INK if i else RED)
            yy += 34
        sheet.paste(crop, (x, hdr_h + lab_h))
        d.rectangle([x - 1, hdr_h + lab_h - 1, x + cw, hdr_h + lab_h + ch], outline=(120, 120, 120))
        x += cw + gut
    sheet.save(out)
    return out, sheet.size


if __name__ == "__main__":
    y = json.load(open("/workspace/nsfw-fix/results/crash/A/yolo_A4.json"))

    def line(name):
        v = y[name]
        return (f"face_yolov8m.pt highest conf = {v['highest_conf_seen']:.3f}"
                if v["highest_conf_seen"] is not None else "face_yolov8m.pt: NOTHING at any threshold")

    panels = [
        (["CRASHING ARM  -  620:106 = the 25-word character description",
          "621:163, the exact image handed to 622:424 BboxDetectorSEGS",
          line("nTAP163__tap163_00001_.png"),
          "BELOW the graph's threshold of 0.6 -> 0 SEGS -> all-zero mask -> RuntimeError",
          "arm A1_gate_crashstring / 19d04a85   status: ERROR at 622:403"],
         "/workspace/nsfw-fix/results/crash/A/arms/A1_gate_crashstring/nTAP163__tap163_00001_.png"),
        (["CLEAN ARM  -  620:106 = the shipped placeholder",
          "621:163, same node, same base image, same seeds",
          line("nTAP163__tap163_00002_.png"),
          "above 0.6 -> the detector fires and the graph completes",
          "arm A1_gate_placeholder / 2dbc564d   status: success"],
         "/workspace/nsfw-fix/results/crash/A/arms/A1_gate_placeholder/nTAP163__tap163_00002_.png"),
    ]
    hdr = ["!! THIS SHEET MIXES CONFIGURATIONS -- THE TWO PANELS ARE NOT THE SAME RENDER !!"]
    sub = ["They differ in exactly one input: 620:106.inputs.text. Everything else -- base image, LoRAs, seeds, all other nodes -- is identical.",
           "Both panels are crops of the SAME pixel region (848,790)-(2196,2726) of the same 2688x3456 canvas, shown at 1:1, no scaling.",
           "Server 127.0.0.1:18188. Shipping graph a811b5d6..., bbox_crop_factor 1.5, both owner LoRAs loaded."]
    print(build(panels, hdr, sub))
