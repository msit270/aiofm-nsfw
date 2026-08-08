#!/usr/bin/env python3
"""Round-3 body sheets: FB and PT, PC1 vs D-base vs F vs G. Same construction
as sheet_ab2.py (full frames 1/3 + same-rect 1:1 face crops per sheet).
Labels carry widget deltas + cos/bodyHF readings. No verdicts."""
import os, sys, json, glob, shutil
sys.path.insert(0, "/workspace/run5/tools")
from PIL import Image, ImageDraw, ImageFont
from likeness import top_face

OUT = "/workspace/ComfyUI/output/AB_CU"
RES = "/workspace/nsfw-quality/results/ab_cu"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
scores = json.load(open(f"{RES}/scores.json"))

SHEETS = {
    "AB_BODY_sheet_FB.png": [
        ("H_pc1_FB",         "H  PC1 30/cfg2 den.25 (current)"),
        ("J_b8c10_FB",       "J  D-base 8/cfg1.0 den.25"),
        ("L_b30c15den25_FB", "L  F 30/cfg1.5 den.25"),
        ("N_b30c15den45_FB", "N  G 30/cfg1.5 den.45")],
    "AB_BODY_sheet_PT.png": [
        ("I_pc1_PT",         "I  PC1 30/cfg2 den.25 (current)"),
        ("K_b8c10_PT",       "K  D-base 8/cfg1.0 den.25"),
        ("M_b30c15den25_PT", "M  F 30/cfg1.5 den.25"),
        ("O_b30c15den45_PT", "O  G 30/cfg1.5 den.45")],
}


def arm_png(arm):
    ps = sorted(glob.glob(f"{OUT}/{arm}/img*.png"))
    assert len(ps) == 1, f"{arm}: expected 1 png, got {ps}"
    return ps[0]


def full_bbox(path):
    f = top_face(path)
    if not f:
        return None
    x0, y0, x1, y1 = f["bbox"]
    tag = f["via"].split("@")[0]
    img = Image.open(path)
    if tag == "half":
        x0, y0, x1, y1 = [v * 2 for v in (x0, y0, x1, y1)]
    elif tag == "quarter":
        x0, y0, x1, y1 = [v * 4 for v in (x0, y0, x1, y1)]
    elif tag == "upper":
        x0 += img.width * 0.15; x1 += img.width * 0.15
    return [x0, y0, x1, y1]


def label_bar(w, text, h=64):
    bar = Image.new("RGB", (w, h), (20, 20, 20))
    d = ImageDraw.Draw(bar)
    d.text((16, 14), text, fill=(240, 240, 240), font=ImageFont.truetype(FONT, 26))
    return bar


def hcat(panels, gutter=8):
    w = sum(p.width for p in panels) + gutter * (len(panels) - 1)
    h = max(p.height for p in panels)
    out = Image.new("RGB", (w, h), (60, 60, 60))
    x = 0
    for p in panels:
        out.paste(p, (x, 0)); x += p.width + gutter
    return out


def vstack(a, b):
    out = Image.new("RGB", (max(a.width, b.width), a.height + b.height), (20, 20, 20))
    out.paste(a, (0, 0)); out.paste(b, (0, a.height))
    return out


for sheet_name, arms in SHEETS.items():
    paths, bboxes, panels_full = {}, [], []
    for arm, lab in arms:
        p = arm_png(arm)
        paths[arm] = p
        os.makedirs(f"{RES}/{arm}", exist_ok=True)
        shutil.copy2(p, f"{RES}/{arm}/{os.path.basename(p)}")
        s = scores.get(f"{arm}/{os.path.basename(p)}", {})
        lab_full = f"{lab}   cos {s.get('cos')}  bodyHF {s.get('bodyHF')}"
        img = Image.open(p)
        bb = full_bbox(p)
        if bb:
            bboxes.append(bb)
        third = img.resize((img.width // 3, img.height // 3), Image.LANCZOS)
        panels_full.append(vstack(label_bar(third.width, lab_full), third))

    row1 = hcat(panels_full)

    x0 = min(b[0] for b in bboxes); y0 = min(b[1] for b in bboxes)
    x1 = max(b[2] for b in bboxes); y1 = max(b[3] for b in bboxes)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    side = max(x1 - x0, y1 - y0) * 1.6
    ref = Image.open(paths[arms[0][0]])
    side = min(side, ref.width, ref.height)
    L = int(max(0, min(cx - side / 2, ref.width - side)))
    T = int(max(0, min(cy - side / 2, ref.height - side)))
    rect = (L, T, int(L + side), int(T + side))

    panels_face = []
    for arm, lab in arms:
        crop = Image.open(paths[arm]).crop(rect)
        panels_face.append(vstack(label_bar(crop.width, lab), crop))
    row2 = hcat(panels_face)

    sheet = vstack(row1, vstack(Image.new("RGB", (row1.width, 24), (60, 60, 60)), row2))
    sheet.save(f"{RES}/{sheet_name}")
    print(f"wrote {sheet_name} {sheet.size} face-rect {rect}")
