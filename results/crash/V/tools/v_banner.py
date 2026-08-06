#!/usr/bin/env python3
"""Stack a loud red comparability banner on top of a contact sheet.

Why this exists: `tools/contact_sheet.py --note` renders exactly ONE red header
line, and the thing that has to be unmissable here is several lines long — which
tiles come from which graph, and which tiles may legitimately be compared with
which. An earlier sheet on this project mixed configurations and the owner formed
an opinion about a character whose LoRAs were not even loaded, so this is the one
piece of text on the sheet that must not be truncated.

It only PREPENDS a band. Every tile pixel is copied verbatim, and the copy is
verified byte-for-byte against the original sheet before the file is written, so
the contact sheet's own 1:1 native-resolution guarantee still holds.
"""
import sys, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

RED = (208, 44, 32)
WHITE = (255, 255, 255)
BG = (12, 12, 12)
PAD = 22
LINE_GAP = 12


def _font(size, bold=True):
    for p in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else
              "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
              "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def banner(sheet_path, lines, out_path=None, title=None):
    src = Image.open(sheet_path).convert("RGB")
    W, H = src.size
    f_title = _font(max(30, W // 90))
    f_line = _font(max(24, W // 125))
    probe = ImageDraw.Draw(Image.new("RGB", (10, 10)))

    def th(font, text):
        b = probe.textbbox((0, 0), text, font=font)
        return b[3] - b[1] + LINE_GAP

    def tw(font, text):
        b = probe.textbbox((0, 0), text, font=font)
        return b[2] - b[0]

    def wrap(font, text, maxw):
        """Hard-wrap on words so nothing is ever truncated. The whole point of
        this banner is that it cannot be cut off."""
        if not text:
            return [""]
        out, cur = [], ""
        for word in text.split(" "):
            trial = (cur + " " + word) if cur else word
            if tw(font, trial) <= maxw or not cur:
                cur = trial
            else:
                out.append(cur)
                cur = "    " + word          # continuation indent
        out.append(cur)
        return out

    maxw = W - 2 * PAD
    title_lines = wrap(f_title, title, maxw) if title else []
    body_lines = [w for ln in lines for w in wrap(f_line, ln, maxw)]

    band_h = PAD * 2
    for t in title_lines:
        band_h += th(f_title, t)
    if title_lines:
        band_h += 10
    for ln in body_lines:
        band_h += th(f_line, ln)

    out = Image.new("RGB", (W, H + band_h), BG)
    d = ImageDraw.Draw(out)
    d.rectangle([0, 0, W, band_h], fill=RED)
    y = PAD
    for t in title_lines:
        d.text((PAD, y), t, font=f_title, fill=WHITE)
        y += th(f_title, t)
    if title_lines:
        y += 10
    for ln in body_lines:
        d.text((PAD, y), ln, font=f_line, fill=WHITE)
        y += th(f_line, ln)
    out.paste(src, (0, band_h))

    # prove the sheet body was copied, not resampled
    a = np.asarray(src)
    b = np.asarray(out)[band_h:band_h + H, 0:W]
    assert a.shape == b.shape and int(np.abs(a.astype(int) - b.astype(int)).max()) == 0, \
        "banner corrupted the sheet body"
    out_path = out_path or sheet_path
    out.save(out_path, "PNG", compress_level=6)
    print(f"[banner] {out_path}  {out.size}  body byte-identical to source: PASS")
    return out_path


if __name__ == "__main__":
    sheet = sys.argv[1]
    title = sys.argv[2]
    banner(sheet, sys.argv[3:], title=title)
