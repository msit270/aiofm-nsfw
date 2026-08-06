#!/usr/bin/env python3
"""The whole ladder on one sheet: the 621:163 face region of every arm, in word
order, with the offline detector confidence under each. Every panel is a
different prompt, so the header is red."""
import json, os, glob
from PIL import Image, ImageDraw, ImageFont

A = "/workspace/nsfw-fix/results/crash/A"
BOX = (848, 790, 2196, 2726)
TW = 300
RED = (200, 30, 25)
GREEN = (20, 110, 45)
BG = (250, 250, 248)
INK = (20, 20, 20)


def font(sz, bold=False):
    base = "/usr/share/fonts/truetype/dejavu/DejaVuSans"
    p = base + ("-Bold.ttf" if bold else ".ttf")
    return ImageFont.truetype(p, sz) if os.path.exists(p) else ImageFont.load_default()


def main(order, out=os.path.join(A, "A2_ladder_sheet.png")):
    y = json.load(open(os.path.join(A, "arm_yolo.json")))
    tk = json.load(open(os.path.join(A, "ladder_tokens_full.json")))
    panels = []
    for label, arm, words in order:
        taps = glob.glob(os.path.join(A, "arms", arm, "nTAP163__*.png"))
        if not taps:
            continue
        r = y.get(arm, {})
        conf = r.get("highest_conf")
        n06 = (r.get("per_threshold") or {}).get("0.6", {}).get("n")
        tok = None
        if words is not None and str(words) in tk:
            tok = tk[str(words)]["tokens"]
            words = tk[str(words)]["words"]
        panels.append({"label": label, "arm": arm, "path": taps[0], "words": words,
                       "tokens": tok, "status": r.get("status"), "conf": conf, "n06": n06})

    im0 = Image.open(panels[0]["path"]).crop(BOX)
    th = int(TW * im0.size[1] / im0.size[0])
    cols = 6
    rows = (len(panels) + cols - 1) // cols
    gut, pad = 14, 24
    lab_h = 104
    hdr_h = 150
    W = pad * 2 + cols * TW + (cols - 1) * gut
    H = hdr_h + pad + rows * (th + lab_h + gut)
    sheet = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(sheet)
    d.rectangle([0, 0, W, hdr_h - 14], fill=RED)
    d.text((pad, 14), "!! EVERY PANEL IS A DIFFERENT CONFIGURATION -- THEY DIFFER IN 620:106.inputs.text !!",
           font=font(26, True), fill=(255, 255, 255))
    for i, t in enumerate([
        "621:163, the image handed to the failing detector 622:424, cropped to (848,790)-(2196,2726) and scaled to a common width. Base image, LoRAs, seeds and every other node are identical across panels.",
        "conf = the graph's own detector run offline: YOLO('bbox/face_yolov8m.pt')(pil, conf=0.1), highest confidence returned. The graph's threshold is 0.6 -- below it, 0 SEGS -> all-zero mask -> RuntimeError at 622:403.",
        "Server 127.0.0.1:18188. Shipping graph a811b5d6..., bbox_crop_factor 1.5, lunaskye on #618 and luna on #116. POST /free before every arm; every arm execution_cached: []."]):
        d.text((pad, 52 + i * 26), t, font=font(17), fill=(255, 236, 233))

    for i, p in enumerate(panels):
        cx = pad + (i % cols) * (TW + gut)
        cy = hdr_h + (i // cols) * (th + lab_h + gut)
        im = Image.open(p["path"]).convert("RGB").crop(BOX).resize((TW, th), Image.LANCZOS)
        sheet.paste(im, (cx, cy))
        crashed = p["status"] == "error"
        d.rectangle([cx - 2, cy - 2, cx + TW + 1, cy + th + 1],
                    outline=RED if crashed else (150, 150, 150), width=3 if crashed else 1)
        yy = cy + th + 6
        d.text((cx, yy), p["label"], font=font(19, True), fill=RED if crashed else INK)
        yy += 24
        wt = (f"{p['words']} words / {p['tokens']} tokens" if p["words"] is not None else "—")
        d.text((cx, yy), wt, font=font(16), fill=INK); yy += 21
        d.text((cx, yy), ("CRASH 622:403" if crashed else "clean"), font=font(17, True),
               fill=RED if crashed else GREEN); yy += 22
        c = f"conf {p['conf']:.3f}" if p["conf"] is not None else "conf —"
        d.text((cx, yy), f"{c}   n@0.6={p['n06']}", font=font(16),
               fill=RED if (p["n06"] == 0) else INK)
    sheet.save(out)
    return out, sheet.size


if __name__ == "__main__":
    order = [
        ("base 620:137", "A0_base_tap137", None),
        ("placeholder", "A1_gate_placeholder", None),
        ("w01", "L_w01", 1), ("w02", "L_w02", 2), ("w03", "L_w03", 3), ("w04", "L_w04", 4),
        ("w06", "L_w06", 6), ("w08", "L_w08", 8), ("w12", "L_w12", 12),
        ("w16  LAST CLEAN", "L_w16", 16),
        ("w17  FIRST CRASH", "L_w17", 17),
        ("w18", "L_w18", 18), ("w19", "L_w19", 19), ("w20", "L_w20", 20),
        ("w21", "L_w21", 21), ("w22", "L_w22", 22), ("w23", "L_w23", 23),
        ("w24", "L_w24", 24), ("w25 full string", "A1_gate_crashstring", 25),
    ]
    print(main(order))
