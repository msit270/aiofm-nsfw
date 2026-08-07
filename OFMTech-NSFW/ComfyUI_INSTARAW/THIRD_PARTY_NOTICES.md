# Third-party notices — ComfyUI_INSTARAW

This package contains code from third-party open-source projects. Those parts
remain under their own licences, listed below. **This file applies only to the
files it names.** Every other file in this package is covered by whatever terms
accompany the product as a whole; nothing here grants rights over them.

Full licence texts are in `licenses/` inside this package:

| File | Covers |
|---|---|
| `licenses/Apache-2.0.txt` | the cg-image-filter derived files (section 1) |
| `licenses/MIT-Filmgrainer.txt` | `modules/detection_bypass/filmgrainer_local/` (section 2) |
| `licenses/OFL-1.1-BricolageGrotesque.txt` (also at `fonts/OFL.txt`) | `fonts/BricolageGrotesque.ttf` (section 3) |
| `licenses/ICC-sRGB-profile-license.txt` | `modules/color_profiles/sRGB_IEC61966-2-1_no_black_scaling.icc` (section 4) |

---

## 1. cg-image-filter — Apache License 2.0

**Upstream project:** cg-image-filter
**Upstream URL:** https://github.com/chrisgoringe/cg-image-filter
**Licence:** Apache License, Version 2.0 — full text in `licenses/Apache-2.0.txt`

    Copyright 2024-2025 Chris Goringe

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.

### Note on the copyright line above

The upstream repository does not state a copyright holder anywhere. Its
`LICENSE` is the unmodified Apache-2.0 boilerplate, with the appendix left as
`Copyright [yyyy] [name of copyright owner]`, and there is no `NOTICE` file and
no per-file copyright header. The holder and years above were therefore
established from the repository itself:

- the repository is owned by GitHub user `chrisgoringe`;
- `pyproject.toml` declares `PublisherId = "chrisgoringe"` and
  `license = { file = "LICENSE" }`;
- of 219 commits, 216 are authored by `Chris <chris.goringe@gmail.com>` /
  `chrisgoringe <chris.goringe@gmail.com>`. The three commits by other people
  either touch only packaging metadata (2, by `snomiao`) or post-date every file
  vendored here (1, by `Łukasz Pazgan`, 2026-04-22). No other person's work is
  present in the files listed below;
- the earliest upstream commit is 2024-12-27 and the newest change reflected in
  the vendored files is 2025-11-29, giving the year range 2024-2025.

If the upstream author states a different copyright line, that one governs and
this file should be updated to match it.

### Apache-2.0 section 4(d) — NOTICE file

Section 4(d) applies only where the upstream work includes a `NOTICE` file.
cg-image-filter does not include one, so no NOTICE content is redistributed.

### Apache-2.0 section 4(c) — retained notices

Section 4(c) requires retaining all copyright, patent, trademark and attribution
notices from the source form of the upstream work. The upstream source files
carry no such notices — the only occurrences of the word "copyright" anywhere in
the upstream repository are inside the body of its `LICENSE` file. There was
therefore nothing to retain, and the headers added under section 4(b) below are
additions rather than reproductions.

### Files derived from cg-image-filter

All of the following carry a header notice stating that they were changed, as
required by Apache-2.0 section 4(b).

| File in this package | Derived from (upstream path) | What was changed |
|---|---|---|
| `nodes/interactive_nodes/image_filter.py` | `image_filter.py` | classes renamed to `INSTARAW_ImageFilter` / `INSTARAW_TextImageFilter` / `INSTARAW_MaskImageFilter`; `CATEGORY` changed; the `graph_id` widget replaced by a hidden `node_identifier` input; on-disk caching of selections, edited text and masks added; `enabled` bypass toggles added; extra mask helpers and a `mask_inverted` output added |
| `nodes/interactive_nodes/image_filter_messaging.py` | `image_filter_messaging.py` | HTTP route renamed `/cg-image-filter-message` → `/instaraw/interactive_message`; socket event renamed `cg-image-filter-images` → `instaraw-interactive-images`; a `/instaraw/clear_text_filter_cache` endpoint added; a `crop` field added to `Response`; a two-second grace period added before interrupt polling |
| `nodes/utility_nodes/list_utility_nodes.py` | `list_utility_nodes.py` | classes prefixed `INSTARAW_`; `CATEGORY` changed; `IO.ANY` replaced with `"*"`; empty-input guards and index-range checking added |
| `nodes/utility_nodes/mask_utility_nodes.py` | `mask_utility_nodes.py` | `MaskedSection` renamed `INSTARAW_MaskedSection` and `CATEGORY` changed (method body unchanged). `INSTARAW_MaskCombine` in the same file is not upstream code and is not covered by the Apache licence |
| `nodes/utility_nodes/string_utility_nodes.py` | `string_utility_nodes.py` | `SplitByCommas`, `AnyListToString`, `StringToInt`, `StringToFloat` prefixed `INSTARAW_`; `CATEGORY` changed; tooltips removed. `INSTARAW_ConcatenateStringsNullSafe` and `INSTARAW_StringCombine` in the same file are not upstream code and are not covered by the Apache licence |
| `js/image_filter.js` | `js/image_filter.js` | extension name and all setting ids re-namespaced to `INSTARAW.Interactive.*`; handled node types changed to the `INSTARAW_*` names; an upstream attribution link added to the settings panel |
| `js/popup.js` | `js/popup.js` | reformatted; `POPUP_NODES` / `MASK_NODES` changed to the `INSTARAW_*` node types; a `CROP` state and an interactive crop UI added; asset paths changed to this package |
| `js/log.js` | `js/log.js` | logging setting key changed from `Image Filter.Z.Detailed Logging` to `INSTARAW.Interactive.DetailedLogging` |
| `js/utils.js` | `js/utils.js` | a `const _aq = !!true;` statement added at the top of the file |
| `js/mask_utils.js` | `js/mask_utils.js` | reformatted; null-guards added around mask-editor DOM lookups; `open_maskeditor` given an explicit `typeof` check and error branches |
| `js/floating_window.js` | `js/floating_window.js` | custom element renamed `cg-floater` → `instaraw-floater`; a `const _ax = encodeURI('');` statement added at the top of the file |
| `js/filter.css` | `js/filter.css` | CSS class prefix renamed `.cg_popup` → `.instaraw_popup`; interactive-crop rules added |
| `js/floating_window.css` | `js/floating_window.css` | **no change to the original content** — this file is byte-for-byte upstream. The only modification is the notice header added at the top |
| `js/zoomed.css` | `js/zoomed.css` | CSS class prefix renamed `.cg_popup` → `.instaraw_popup`; no other change |

### Which upstream version

The vendored code does not correspond to a single upstream commit. It was
compared against the upstream repository at commit
`694f8444e67f44d601861c5604bb3e55c35daf9d` (2026-06-01) and against its full
history. The closest single match is upstream **v1.6.3**, commit
`2cd49e79a` (2025-09-17) — that revision's file layout is exactly the set of
files vendored here, and its `wait_for_response(secs, uid, unique)` /
`send_and_wait(payload, timeout, uid, unique)` signatures match this package.
Some files additionally carry changes first made upstream in commit
`c491514` (2025-11-29, v1.7, "new mask editor") — the `masked_data` base64
mask path and the `js/mask_utils.js` null-guards. No single upstream commit
contains both sets of changes, so the vendored code is a blend of roughly
v1.6.3 and v1.7.

`js/floating_window.css` is byte-identical to the upstream blob
`94f29263f1a8a16ff3ea9b2775599507e6209f1f`, which was present in upstream from
2025-05-06 to 2025-11-15.

Other files in this package (`nodes/interactive_nodes/interactive_crop.py`,
`nodes/interactive_nodes/prompt_filter.py`,
`nodes/interactive_nodes/batch_image_generator.py`) call into
`image_filter_messaging.py`, but were checked line-by-line against the whole
upstream history and reproduce nothing from it beyond unavoidable ComfyUI
boilerplate — the `from nodes import PreviewImage` and
`from comfy.model_management import InterruptProcessingException` imports and
the `"extra_pnginfo": "EXTRA_PNGINFO"` hidden-input key. They are not covered by
the Apache licence.

---

## 2. Filmgrainer — MIT License

**Upstream project:** Filmgrainer
**Upstream URL:** https://github.com/larspontoppidan/filmgrainer
**Licence:** MIT — full text, including the copyright notice, in
`licenses/MIT-Filmgrainer.txt`

    MIT License

    Copyright (c) 2022 Lars Ole Pontoppidan

(The permission notice and the warranty disclaimer are in
`licenses/MIT-Filmgrainer.txt`. The MIT licence requires that the copyright
notice and the permission notice are included in all copies or substantial
portions of the software; shipping that file with this package is how that
requirement is met.)

| File in this package | Derived from | What was changed |
|---|---|---|
| `modules/detection_bypass/filmgrainer_local/filmgrainer.py` | `filmgrainer/filmgrainer.py` | absolute `import filmgrainer.*` changed to relative imports; `MASK_CACHE_PATH` changed from the hard-coded `/tmp/mask-cache/` to `tempfile.gettempdir()` and path joining changed to `os.path.join`; `os.mkdir` changed to `os.makedirs(..., exist_ok=True)`; every progress `print()` commented out; the local variable `map` renamed `map_obj` |
| `modules/detection_bypass/filmgrainer_local/graingen.py` | `filmgrainer/graingen.py` | **no change** — byte-for-byte upstream apart from the notice header added at the top |
| `modules/detection_bypass/filmgrainer_local/graingamma.py` | `filmgrainer/graingamma.py` | **no change** — byte-for-byte upstream apart from the notice header added at the top |

---

## 3. Bricolage Grotesque — SIL Open Font License 1.1

**Upstream project:** Bricolage Grotesque, by Atelier Triay
**Upstream URL:** https://github.com/ateliertriay/bricolage
**Licence:** OFL-1.1 — full text in `licenses/OFL-1.1-BricolageGrotesque.txt`
and, as the OFL expects, alongside the font itself at `fonts/OFL.txt`

    Copyright 2022 The Bricolage Grotesque Project Authors
    (https://github.com/ateliertriay/bricolage)

That copyright line is read from the shipped font's own `name` table (name ID
0). The same table declares the licence at name ID 13 ("This Font Software is
licensed under the SIL Open Font License, Version 1.1") and name ID 14
(https://scripts.sil.org/OFL). The shipped file is the variable font — it has
an `fvar` table — at version 1.001, PostScript name
`BricolageGrotesque-96ptExtraBold`.

| File in this package | Change |
|---|---|
| `fonts/BricolageGrotesque.ttf` | not modified; the filename differs from upstream's, which the OFL does not restrict |

OFL clause 2 permits bundling and selling the font as part of other software,
provided each copy contains the copyright notice and the licence — which is
what `fonts/OFL.txt` is for. Clause 1 forbids selling the font on its own;
this package does not do that. No Reserved Font Name is declared after the
copyright statement in the upstream `OFL.txt`, so clause 3 has nothing to bite
on. Clause 5 means the font stays under the OFL and is not relicensed under
this package's terms.

---

## 4. sRGB ICC profile — International Color Consortium

**Publisher:** International Color Consortium
**Registry:** https://registry.color.org/rgb-registry/black_scaled_2009_srgb
**Licence:** a custom permissive ICC grant — full text in
`licenses/ICC-sRGB-profile-license.txt`

    Copyright International Color Consortium, 2009

(read from the profile's own `cprt` tag)

| File in this package | Change |
|---|---|
| `modules/color_profiles/sRGB_IEC61966-2-1_no_black_scaling.icc` | not modified; byte-identical to the ICC's own copy (3,052 bytes, md5 `ce7471dab641af1016dfc8f3482da966`) |

The grant is conditional on the file not being changed, including its
copyright tag, and on ICC's name not being used in advertising or publicity
about this distribution. See `licenses/ICC-sRGB-profile-license.txt`.

---

## 5. Items that were NOT cleared — removed in this version

Sections 5.1 and 5.2 describe material that **used to be** in this package and
that is **no longer shipped**. Neither was cleared for redistribution: in both
cases the upstream licence refuses commercial use outright, so no notice could
have made them shippable. They are kept on record here, marked as removed, so
that anyone comparing this package against an older copy can see what changed
and why. Section 5.3 lists items still shipped whose terms are not established.

### 5.1 UnMarker — non-commercial only, NOT cleared — **removed in this version**

Removed files:

- `modules/detection_bypass/utils/adaptive_filter.py`
- `modules/detection_bypass/utils/unmarker_losses.py`
- `modules/detection_bypass/utils/unmarker_full.py` (imported both of the above
  at module level and could not run without them)
- `modules/detection_bypass/utils/non_semantic_attack.py` (self-described as
  "the core UnMarker-style optimization"; its provenance was never established
  either way, so it was removed rather than shipped uncleared)
- `nodes/utility_nodes/spectral_normalizer_node.py` — the `INSTARAW_Spectral_Normalizer`
  node, whose only engine was `non_semantic_attack.py`
- `modules/detection_bypass/processor.py`, `modules/detection_bypass/pipeline.py`,
  `modules/detection_bypass/pipeline_v2.py` — the command-line and pipeline
  orchestration around the attack. All three were already unreachable: nothing
  in the package imported them, and `processor.py` and `pipeline_v2.py` could
  not even be imported (they asked `utils` for a name, `attack_non_semantic`,
  that no longer existed anywhere in the package)

The first two declared in their own docstrings that they were "Ported from
`ai-watermark/modules/attack/unmark/cw.py:Filter`" and ".../losses.py".
Compared against https://github.com/andrekassis/ai-watermark at branch
`master`, they shared whole class inventories and dozens of verbatim lines with
those files. That project's `LICENSE` ("Source Code License for UnMarker") says
at 3.3:

> The Work and any derivative works thereof only may be used or intended for
> use non-commercially. ... As used herein, "non-commercially" means for
> research or evaluation purposes only.

`utils/__init__.py` no longer imports any of them, and the two symbols it used
to re-export from `unmarker_full` (`normalize_spectrum_twostage`,
`SpectralNormalizer`) plus `non_semantic_attack` are gone from its `__all__`.
No other file in the package referenced them.

### 5.2 GrainNet — all rights reserved, academic use only, NOT cleared — **removed in this version**

Removed files:

- `modules/neural_grain/net.py`
- `pretrained/neural_grain/grainnet.pt`
- `nodes/utility_nodes/neural_grain_node.py` — the `INSTARAW_NeuralGrain` node,
  which loaded them

`net.py` differed from
https://github.com/Gwilherm-LESNE/Neural_Film_Grain_Rendering `net.py` by
three lines out of 192, and `grainnet.pt` was **byte-identical** to that
project's `models/GrainNet/default/grainnet.pt` (45,929 bytes, md5
`91907c73885d4ac65790b198657a80d5`). That project has no LICENSE file; its
README says, in full:

> All rights reserved. The code is released for academic research use only.

The `pretrained/` directory existed only to hold that weight file and has been
removed with it.

### 5.2.1 A note on compiled bytecode

Deleting the `.py` files is not on its own enough. This package previously
shipped `__pycache__/` directories, and a `.pyc` compiled from an encumbered
module contains that module's code — including, in `adaptive_filter`'s case,
the "Ported from ai-watermark" docstring, readable with `strings`. Python never
loads a `__pycache__/*.pyc` whose source file is absent, so such a file would
have shipped the encumbered code while being invisible at runtime. **All
`__pycache__/` directories have been removed from this package, and packaging
must exclude them.**

### 5.3 Not yet investigated — still shipped

- `modules/authenticity_profiles/*.icc` (iPhone device profiles) —
  redistribution terms not established.
- `modules/detection_bypass/_luts/*.cube` — several filenames carry
  third-party creator names. Redistribution terms not established.
