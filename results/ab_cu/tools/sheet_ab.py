#!/usr/bin/env python3
"""AB_CU sheets for the owner's eye. No verdicts — labels carry the arm's
widget delta plus instrument readings (cos / faceHF) from scores.json.

  AB_CU_sheet_full.png     three whole frames at 1/3 scale
  AB_CU_sheet_face1to1.png the SAME face rect cut from all three at 1:1
                           (union of ArcFace bboxes, squared, +20% pad)

Also copies each arm's render PNG into results/ab_cu/<arm>/ so the evidence
survives the pod."""
import os, sys, json, glob, shutil
sys.path.insert(0, "/workspace/run5/tools")
from PIL import Image, ImageDraw, ImageFont
from likeness import top_face

OUT = "/workspace/ComfyUI/output/AB_CU"
RES = "/workspace/nsfw-quality/results/ab_cu"
ARMS = [("A_base_CU", "A  baseline  den .25 / rms+rms"),
        ("B_den045_CU", "B  USDU-617 den .45  (run-6 cand)"),
        ("C_s18ea_CU", "C  S18 euler_ancestral tiled x2")]
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
scores = json.load(open(f"{RES}/scores.json"))


def arm_png(arm):
    ps = sorted(glob.glob(f"{OUT}/{arm}/img*.png"))
    assert len(ps) == 1, f"{arm}: expected 1 png, got {ps}"
    return ps[0]


def full_bbox(path):
    """top_face bbox mapped back to full-res coords."""
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
    d.text((16, 14), text, fill=(240, 240, 240), font=ImageFont.truetype(FONT, 30))
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


paths, bboxes, panels_full = {}, [], []
for arm, lab in ARMS:
    p = arm_png(arm)
    paths[arm] = p
    os.makedirs(f"{RES}/{arm}", exist_ok=True)
    shutil.copy2(p, f"{RES}/{arm}/{os.path.basename(p)}")
    s = scores.get(f"{arm}/{os.path.basename(p)}", {})
    lab_full = f"{lab}   cos {s.get('cos')}  faceHF {s.get('faceHF')}"
    img = Image.open(p)
    bb = full_bbox(p)
    if bb:
        bboxes.append(bb)
    third = img.resize((img.width // 3, img.height // 3), Image.LANCZOS)
    panels_full.append(vstack(label_bar(third.width, lab_full), third))

hcat(panels_full).save(f"{RES}/AB_CU_sheet_full.png")
print("wrote AB_CU_sheet_full.png")

# common 1:1 face rect: union of bboxes -> square + 20% pad, clamped
x0 = min(b[0] for b in bboxes); y0 = min(b[1] for b in bboxes)
x1 = max(b[2] for b in bboxes); y1 = max(b[3] for b in bboxes)
cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
side = max(x1 - x0, y1 - y0) * 1.2
ref = Image.open(paths[ARMS[0][0]])
side = min(side, ref.width, ref.height)
L = int(max(0, min(cx - side / 2, ref.width - side)))
T = int(max(0, min(cy - side / 2, ref.height - side)))
rect = (L, T, int(L + side), int(T + side))
print("face rect 1:1:", rect)

panels_face = []
for arm, lab in ARMS:
    crop = Image.open(paths[arm]).crop(rect)
    panels_face.append(vstack(label_bar(crop.width, lab), crop))
hcat(panels_face).save(f"{RES}/AB_CU_sheet_face1to1.png")
print("wrote AB_CU_sheet_face1to1.png")
