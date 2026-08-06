# WS3 — questions and logged blockers

WS3 owns licence compliance for the `cg-image-filter` derivation inside
`ComfyUI_INSTARAW`. Per instructions I did not stop to ask anything; where a
call had to be made I took the option safest for a first-time buyer and
recorded it here.

---

## Q1 — LUSTIFY base checkpoint (logged, explicitly out of scope this run)

**Status: still the remaining blocker on selling. No action taken. Nothing
touched.**

- Base checkpoint is **LUSTIFY! GGWP (V7)**, shipped in the pack as
  `SDXLNSFW.safetensors`.
- Civitai metadata: `allowCommercialUse: ['RentCivit', 'Image']`,
  `allowDerivatives: False`.
- `Image` means buyers may **sell images generated with it** — the product's
  core use case is fine.
- The problem is narrower: **redistributing the checkpoint file itself inside
  the pack**. `allowDerivatives: False` plus the absence of a redistribution
  permission is what bites, not the image rights.
- Likely fix: remove `SDXLNSFW.safetensors` from the pack and have buyers pull
  it from Civitai themselves, accepting the licence in their own name. Zero
  output change, no graph re-verification needed, both LoRA slots untouched.
- Per this run's scope I did **not** remove the checkpoint, did **not** touch
  the Civitai path, and did **not** touch the setup script.

---

## Q2 — Where to put the Apache-2.0 licence text (decision taken, no answer needed)

The brief said to follow the standard layout — `LICENSE` at the package root —
with "a clearly-named third-party licences file is acceptable if you justify
it".

**I did not put a bare `LICENSE` at the package root.** Justification: a file
called `LICENSE` at the root of `ComfyUI_INSTARAW/` containing the Apache-2.0
text reads as "this whole pack is Apache-2.0". That is false — 28 files in the
pack carry `PROPRIETARY SOFTWARE - ALL RIGHTS RESERVED` headers (for example
`nodes/interactive_nodes/interactive_crop.py:3-4`) — and it would work against
the seller by appearing to grant buyers Apache rights over the entire pack.
It also directly conflicts with requirement 3, which asks for attribution that
is *unambiguous about which parts the Apache licence covers versus the rest*.

What ships instead:

- `ComfyUI_INSTARAW/THIRD_PARTY_NOTICES.md` — names every third-party file and
  its licence, and states explicitly that it applies only to the files it names.
- `ComfyUI_INSTARAW/licenses/Apache-2.0.txt` — the full licence text, verbatim.
- plus `licenses/MIT-Filmgrainer.txt`, `licenses/OFL-1.1-BricolageGrotesque.txt`
  (also `fonts/OFL.txt`), `licenses/ICC-sRGB-profile-license.txt`.

**Open question for the owner:** the pack still has no statement of its *own*
licence terms anywhere. A buyer unpacking the tarball can see what the
third-party parts allow but has nothing telling them what they may do with the
rest. Writing that is a business decision, not mine — but it should exist
before sale, and it belongs at `ComfyUI_INSTARAW/LICENSE`.

---

## Q3 — Upstream declares no copyright holder (decision taken)

`chrisgoringe/cg-image-filter` has **no NOTICE file and no copyright line
anywhere**. Its `LICENSE` is the unmodified Apache-2.0 boilerplate with the
appendix still reading `Copyright [yyyy] [name of copyright owner]`, and no
source file carries a header.

I constructed `Copyright 2024-2025 Chris Goringe` from repository evidence
(owner, `pyproject.toml` `PublisherId`, 216 of 219 commits, and the date range
of the vendored code). The reasoning is written into `THIRD_PARTY_NOTICES.md`
so a reader can check it rather than take it on faith, and the file says that
if the upstream author states a different line, that one governs.

**Lower-risk option not taken:** emailing the author to confirm. Worth doing
before sale, but it should not block the tarball — the notice as written is
better than the nothing that was there before.

---

## Q4 — Two NEW licence blockers found (need a decision, not from me)

These came out of the "sanity-check the rest of the pack" sweep. Both are
verified against upstream, both forbid commercial use in writing, and both are
**more restrictive than LUSTIFY** — LUSTIFY at least permits selling the output.

### Q4a — UnMarker (`ai-watermark`) — non-commercial only

- `modules/detection_bypass/utils/adaptive_filter.py`
- `modules/detection_bypass/utils/unmarker_losses.py`

Their own docstrings say "Ported from `ai-watermark/modules/attack/unmark/`".
`https://github.com/andrekassis/ai-watermark` `LICENSE` §3.3:

> The Work and any derivative works thereof only may be used or intended for
> use non-commercially. ... "non-commercially" means for research or
> evaluation purposes only.

### Q4b — GrainNet — all rights reserved, academic only

- `modules/neural_grain/net.py` (3 lines different from upstream, out of 192)
- `pretrained/neural_grain/grainnet.pt` (**byte-identical** to upstream)
- `nodes/utility_nodes/neural_grain_node.py`

`https://github.com/Gwilherm-LESNE/Neural_Film_Grain_Rendering` has no LICENSE
file. Its README, in full:

> All rights reserved. The code is released for academic research use only.

**Why this is cheap to fix, and my recommendation:** neither
`INSTARAW_NeuralGrain` nor `INSTARAW_Spectral_Normalizer` appears anywhere in
`OFMTech-NSFW/OFMTech_NSFW.json`. Deleting both trees changes no rendered
output. I did not delete them because file deletion inside the pack is outside
what I was asked to do this run and WS5 is re-cutting the tarball — but this
should be decided before that re-cut, not after.

---

## Q5 — Unexplained no-op statements inside the vendored files (flagged, not changed)

Three additions to cg-image-filter files do nothing and look like markers:

- `js/utils.js` — `const _aq = !!true;` added at the top
- `js/floating_window.js` — `const _ax = encodeURI('');` added at the top
- `js/image_filter.js` — 417 zero-width unicode characters (U+200B / U+200C) embedded in the
  trailing comment on line 38, the `name:` line of `app.registerExtension({...})`

I left all three exactly as they are (the brief said not to touch semantics)
and described the first two truthfully in the modification notices. If they are
deliberate watermarks, someone should know they now sit inside files this
package publicly attributes to a third party.
