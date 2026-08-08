#!/usr/bin/env python3
"""D identity sheet — owner checks IDENTITY, not just texture, before D ships.

Panels (left to right):
  A   shipped config close-up (30/cfg2, den .25)          cos .6590
  D   candidate close-up (8/cfg1.0, den .25)              cos .7597
  Z   zref_P_12345 — a centroid SOURCE render (the likeness instrument's
      own definition of Luna; portrait comp)
  M   run-5 M2_luna_CU — established Luna close-up (itself 30/cfg2 era)

Row 1: full frames at 1/3 (composition drift of D visible here).
Row 2: per-image face-CENTERED square crops at 1:1, common side length —
       centered per face (not same-rect) because identity, not texture,
       is the question; no resizing.
"""
import os, sys, json
sys.path.insert(0, "/workspace/run5/tools")
from PIL import Image, ImageDraw, ImageFont
from likeness import top_face

RES = "/workspace/nsfw-quality/results/ab_cu"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
PANELS = [
    (f"{RES}/A_base_CU/img_00001_.png",  "A  shipped 30/cfg2 den.25   cos .6590"),
    (f"{RES}/D_b8c10_den25/img_00001_.png", "D  candidate 8/cfg1.0 den.25   cos .7597"),
    ("/workspace/run5/output/A/zref_P_12345/img/img_00001_.png",
     "Z  zref_P_12345 — centroid source (what the instrument calls Luna)"),
    ("/workspace/run5/output/M2/M2_luna_CU/Personal/render_00001_.png",
     "M  run-5 M2 luna CU (30/cfg2 era)"),
]


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


imgs, bbs = [], []
for path, lab in PANELS:
    img = Image.open(path).convert("RGB")
    bb = full_bbox(path)
    assert bb, f"no face found in {path}"
    imgs.append((img, lab)); bbs.append(bb)

# row 1: full frames at 1/3
row1 = hcat([vstack(label_bar(i.width // 3, lab), i.resize((i.width // 3, i.height // 3), Image.LANCZOS))
             for i, lab in imgs])

# row 2: per-image face-centered 1:1 crops, common side
side = int(max(max(b[2] - b[0], b[3] - b[1]) for b in bbs) * 1.5)
panels2 = []
for (img, lab), b in zip(imgs, bbs):
    s = min(side, img.width, img.height)
    cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
    L = int(max(0, min(cx - s / 2, img.width - s)))
    T = int(max(0, min(cy - s / 2, img.height - s)))
    panels2.append(vstack(label_bar(s, lab), img.crop((L, T, L + s, T + s))))
row2 = hcat(panels2)

sheet = vstack(row1, vstack(Image.new("RGB", (row1.width, 24), (60, 60, 60)), row2))
sheet.save(f"{RES}/AB_CU_D_identity_sheet.png")
print("wrote AB_CU_D_identity_sheet.png", sheet.size)
