#!/usr/bin/env python3
"""Q2 full-frame OVERVIEW sheet. Downscaled — navigation only, loudly bannered
as such; quality is judged on the 1:1 face/skin sheets from contact_sheet.py.
Every tile: crop-factor value + server-side exec seconds; baseline marked
"BASELINE (ships)". Protocol: a sheet without a labelled baseline is discarded.
"""
import glob
import json
import os

from PIL import Image, ImageDraw, ImageFont

Q2 = "/workspace/nsfw-fix/results/run4/quality/Q2"
TILE_W = 560
COLS = 4

FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_R = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


def main():
    arms = []
    for d in sorted(os.listdir(Q2)):
        mp = os.path.join(Q2, d, "meta.json")
        pngs = sorted(glob.glob(os.path.join(Q2, d, "n505__*.png")))
        if os.path.exists(mp):
            m = json.load(open(mp))
            arms.append((d, m, pngs[0] if pngs else None))
    if not arms:
        raise SystemExit("no arms")

    fb, fr, fs = font(FONT_B, 26), font(FONT_R, 20), font(FONT_R, 17)
    tiles = []
    for name, m, p in arms:
        if p:
            im = Image.open(p).convert("RGB")
            th = int(im.height * TILE_W / im.width)
            im = im.resize((TILE_W, th), Image.LANCZOS)
        else:
            im = Image.new("RGB", (TILE_W, int(TILE_W * 3456 / 2688)), (60, 20, 20))
        tiles.append((name, m, im))

    th = max(t[2].height for t in tiles)
    LABEL = 96
    BANNER = 110
    rows = (len(tiles) + COLS - 1) // COLS
    W = 20 + COLS * (TILE_W + 16)
    H = BANNER + 20 + rows * (th + LABEL + 16)
    sheet = Image.new("RGB", (W, H), (26, 26, 26))
    dr = ImageDraw.Draw(sheet)
    dr.rectangle([0, 0, W, BANNER], fill=(140, 20, 20))
    dr.text((16, 10), "Q2 OVERVIEW — 620:114 bbox_crop_factor ladder — DOWNSCALED, navigation only.",
            font=fb, fill=(255, 255, 255))
    dr.text((16, 44), "Judge quality on the 1:1 sheets (q2cf_face_sheet*, q2cf_skin_sheet*). "
                      "One variable per arm; 60-token buyer prompt; fixed seeds; fresh server per arm (cold).",
            font=fr, fill=(255, 235, 235))
    dr.text((16, 72), "Times are server-side execution seconds from each arm's history entry.",
            font=fr, fill=(255, 235, 235))

    for i, (name, m, im) in enumerate(tiles):
        r, c = divmod(i, COLS)
        ox = 20 + c * (TILE_W + 16)
        oy = BANNER + 20 + r * (th + LABEL + 16)
        base = bool(m.get("baseline"))
        dr.rectangle([ox, oy, ox + TILE_W - 1, oy + LABEL - 1],
                     fill=(20, 44, 60) if base else (38, 38, 38))
        cf = m.get("bbox_crop_factor")
        es = m.get("exec_seconds")
        status = m.get("status")
        t1 = f"bbox_crop_factor {cf}" + ("   — BASELINE (ships)" if base else "")
        t2 = f"exec {es} s   status {status}   cached {'[] (cold)' if m.get('execution_cached') == [] else m.get('execution_cached')}"
        t3 = f"{name}   prompt {str(m.get('prompt_id'))[:8]}"
        dr.text((ox + 10, oy + 6), t1, font=fb, fill=(120, 200, 255) if base else (238, 238, 238))
        dr.text((ox + 10, oy + 40), t2, font=fr, fill=(200, 200, 200))
        dr.text((ox + 10, oy + 66), t3, font=fs, fill=(150, 150, 150))
        sheet.paste(im, (ox, oy + LABEL))
        col = (120, 200, 255) if base else (70, 70, 70)
        for k in range(3 if base else 1):
            dr.rectangle([ox - 1 - k, oy - 1 - k, ox + TILE_W + k, oy + LABEL + im.height + k], outline=col)

    out = os.path.join(Q2, "q2cf_overview_downscaled.png")
    sheet.save(out)
    print("wrote", out, sheet.size)


if __name__ == "__main__":
    main()
