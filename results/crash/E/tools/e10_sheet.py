#!/usr/bin/env python3
"""E10 -- the picture the owner asked to be given rather than a verdict:
the same face region from the crashing arm and from the cured arm, at 1:2,
same pixel region, plus the known-good control. Also writes half-scale thumbs
of every Track E tap so the arms can be eyeballed without opening 9 MB PNGs."""
import os, glob
from PIL import Image, ImageDraw
Image.MAX_IMAGE_PIXELS = None

ROOT = "/workspace/nsfw-fix/results/crash/E"
BOX = (856, 790, 2193, 2698)          # Track A's face box on 621:163
PANELS = [
    ("E18_alt1_gpuclip_crash", "GPU encoder (shipped)  -  ERROR 622:403"),
    ("E18_alt2_cpuclip_crash", "620:110.device = cpu  -  success"),
    ("E18_placeholder_ctl", "control: shipped placeholder  -  success"),
]


def tap(arm):
    g = glob.glob(os.path.join(ROOT, "arms", arm, "nTAP163__*.png"))
    return g[0] if g else None


if __name__ == "__main__":
    os.makedirs(os.path.join(ROOT, "thumbs"), exist_ok=True)
    for d in sorted(glob.glob(os.path.join(ROOT, "arms", "*"))):
        p = tap(os.path.basename(d))
        if not p:
            continue
        im = Image.open(p).convert("RGB").crop(BOX)
        im = im.resize((im.width // 2, im.height // 2), Image.LANCZOS)
        im.save(os.path.join(ROOT, "thumbs", os.path.basename(d) + "__facebox_half.png"))

    ims = []
    for arm, cap in PANELS:
        im = Image.open(tap(arm)).convert("RGB").crop(BOX)
        im = im.resize((im.width // 2, im.height // 2), Image.LANCZOS)
        ims.append((im, cap))
    W = sum(i.width for i, _ in ims) + 20 * (len(ims) + 1)
    H = ims[0][1] and ims[0][0].height + 90
    sheet = Image.new("RGB", (W, H), (24, 24, 28))
    d = ImageDraw.Draw(sheet)
    d.text((20, 12), "TRACK E  -  620:110 CLIPLoader device widget, same 46-token prompt, "
                     "same server :18188, interleaved.  621:163 tap, face box, 1:2",
           fill=(255, 210, 60))
    x = 20
    for im, cap in ims:
        sheet.paste(im, (x, 60))
        d.text((x, 44), cap, fill=(235, 235, 235))
        x += im.width + 20
    sheet.save(os.path.join(ROOT, "E_cpuclip_sheet.png"))
    print("wrote", os.path.join(ROOT, "E_cpuclip_sheet.png"), sheet.size)
