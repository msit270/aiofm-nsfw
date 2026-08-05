# WS3 — licence compliance for the `cg-image-filter` derivation

Scope: `OFMTech-NSFW/ComfyUI_INSTARAW/`. Branch `fix/run2`.
`OFMTech-NSFW/OFMTech_NSFW.json` was **read but never written** (other agents own it).

**Headline:** the cg-image-filter obligation is now met, and the derivation
turned out to be **14 files, not the 4 the brief guessed**. The sweep of the
rest of the pack found **two further licences that forbid commercial use
outright** — worse than LUSTIFY, and previously unrecorded anywhere.

---

## 1. Establishing the facts

### Method

Cloned `https://github.com/chrisgoringe/cg-image-filter` and compared against
its **entire history**, not just HEAD — 219 commits, 7,332 distinct blobs
indexed. HEAD at clone time was
`694f8444e67f44d601861c5604bb3e55c35daf9d`, 2026-06-01, `pyproject.toml`
version `1.9`.

Comparing only against HEAD would have been misleading: upstream has since
migrated to the `comfy_api.latest.io` schema API and moved files into
`utility_nodes/`, so several derived files score near-zero similarity against
HEAD while being near-verbatim copies of an older revision.

### The derivation is 14 files, not 4

The brief named `nodes/interactive_nodes/image_filter.py`,
`image_filter_messaging.py`, `js/image_filter.js` and `js/filter.css` as
"plausible starting points". All four are derived. So are ten more:

| File | Evidence |
|---|---|
| `js/floating_window.css` | **byte-identical** to upstream blob `94f29263f1a8a16ff3ea9b2775599507e6209f1f`. Exact git-hash match across all 7,332 upstream blobs |
| `nodes/interactive_nodes/image_filter_messaging.py` | whole-file copy. Line 116 (post-header) still reads `async def cg_image_filter_message(request):` — the upstream function name, unrenamed. Constants `REQUEST_RESHOW = "-1"` / `CANCEL = "-3"` / `WAITING_FOR_RESPONSE = "-9"` and the entire `MessageState` class are identical |
| `nodes/interactive_nodes/image_filter.py` | whole-file copy. `HIDDEN` dict, `INPUT_TYPES` bodies, `mask_to_image()`, and the four `if ontimeout=='send …'` branches are verbatim. Classes renamed `ImageFilter`→`INSTARAW_ImageFilter`, `TextImageFilterWithExtras`→`INSTARAW_TextImageFilter`, `MaskImageFilter`→`INSTARAW_MaskImageFilter` |
| `nodes/utility_nodes/mask_utility_nodes.py` | `INSTARAW_MaskedSection` is upstream `MaskedSection` with **only** the class name and `CATEGORY` changed — the method body is character-for-character identical |
| `nodes/utility_nodes/string_utility_nodes.py` | `SplitByCommas`, `AnyListToString`, `StringToInt`, `StringToFloat` copied verbatim from upstream `string_utility_nodes.py`, prefixed `INSTARAW_` |
| `nodes/utility_nodes/list_utility_nodes.py` | `BatchFromImageList`, `ImageListFromBatch`, `StringListFromStrings`, `PickFromList` all present, same structure |
| `js/zoomed.css` | upstream file with a single global rename `.cg_popup` → `.instaraw_popup`. Nothing else differs |
| `js/filter.css` | same rename, plus appended crop rules. Local line 105 (post-header) still reads `.cgfloat .hidden {` |
| `js/popup.js` | same imports, same `POPUP_NODES`/`MASK_NODES`/`REQUEST_RESHOW`/`CANCEL`/`GRID_IMAGE_SPACE`, identical `get_full_url()` body, identical `State` freeze object with `CROP: 6` appended. Local line 44 (post-header) comment: `// Renamed to INSTARAW node class names` |
| `js/mask_utils.js` | 24 exported/private function names shared, including `press_maskeditor_cancel`, `get_mask_editor_save_button`, `mask_editor_listen_for_cancel` |
| `js/floating_window.js` | `FloatingWindow` class identical; upstream's `cg-floater` custom element renamed `instaraw-floater`. Local still writes `this.classList.add('cgfloat')` |
| `js/log.js` | `Log` class identical apart from the settings key |
| `js/utils.js` | `create()` identical |
| `js/image_filter.js` | lines 46-47 (post-header) already carried an in-code credit: `"Based on original work by chrisgoringe (cg-image-filter)"` |

Cross-check: the upstream tree at commit `2cd49e7` contains **exactly** the set
of files vendored here — `image_filter.py`, `image_filter_messaging.py`,
`list_utility_nodes.py`, `mask_utility_nodes.py`, `string_utility_nodes.py`,
and `js/{ding.mp3, filter.css, floating_window.css, floating_window.js,
image_filter.js, log.js, mask_utils.js, popup.js, utils.js, zoomed.css}`.

`js/ding.mp3` shares a path with upstream but is a **different file** (53,104 B
vs upstream's 15,466 B) — replaced, not vendored. Excluded from the notices.

### Which upstream version — it is a blend, not one commit

Closest single match: **v1.6.3**, commit `2cd49e79a`, 2025-09-17. That
revision's `wait_for_response(secs, uid, unique)` and
`send_and_wait(payload, timeout, uid, unique)` signatures match this pack
exactly, and its file layout is the vendored set.

But `image_filter.py` and `image_filter_messaging.py` also carry the
`masked_data` base64 mask path, which upstream first added in `c491514`,
2025-11-29, v1.7 ("new mask editor") — two days *after* `dc60707` renamed
`unique` → `graph_id`. I checked every commit: **zero upstream commits contain
both `unique_expected` and `masked_data`**. The pack is therefore a blend of
~v1.6.3 and ~v1.7, not a clean snapshot. Recorded as such rather than
asserting a single pin.

### Copyright holder — upstream declares none

This is the part that could not be taken on assumption, and the answer is
awkward: **upstream states no copyright holder anywhere.**

- `LICENSE` is the unmodified Apache-2.0 boilerplate. Its appendix still reads
  `Copyright [yyyy] [name of copyright owner]` (line 189).
- There is **no NOTICE file**.
- No source file carries a copyright header. `grep -rn -i copyright` over the
  whole upstream repo matches only inside the body of `LICENSE`.
- `pyproject.toml` declares `license = { file = "LICENSE" }` and
  `PublisherId = "chrisgoringe"`.

Constructed from repository evidence: **Copyright 2024-2025 Chris Goringe**.
216 of 219 commits are `Chris <chris.goringe@gmail.com>` /
`chrisgoringe <chris.goringe@gmail.com>`. Of the three others, two (`snomiao`)
touch only `pyproject.toml` and a CI workflow, and one (`Łukasz Pazgan`,
2026-04-22) post-dates every file vendored here — so **no other person's work
is present in the vendored files**. Years span the first upstream commit
(2024-12-27) to the newest change reflected here (2025-11-29).

The derivation of that line is written into `THIRD_PARTY_NOTICES.md` so it can
be checked rather than trusted, with a note that an upstream-stated line would
supersede it.

---

## 2. What was shipped, and which clause each artifact satisfies

Placed inside `ComfyUI_INSTARAW/`, so they reach the buyer in the tarball:

| Artifact | Clause it satisfies |
|---|---|
| `licenses/Apache-2.0.txt` | **§4(a)** — "give any other recipients … a copy of this License". Byte-identical to `https://www.apache.org/licenses/LICENSE-2.0.txt` (11,358 B, sha256 `cfc7749b…523d30`), verified with `cmp` |
| Header on each of the 14 derived files | **§4(b)** — "cause any modified files to carry prominent notices stating that You changed the files". Each header carries the upstream project, URL, the copyright line, the Apache boilerplate, and a specific `NOTICE:` sentence naming what changed in that file |
| `THIRD_PARTY_NOTICES.md` | attribution and scope. Names all 14 files, what each is derived from, and exactly what changed |
| — | **§4(c)** — retain notices from the source form. **Nothing to retain**: the upstream source files carry no copyright, patent, trademark or attribution notices. Stated explicitly in the notices file rather than silently skipped |
| — | **§4(d)** — NOTICE file. **Does not apply**: upstream has no NOTICE file, so there is no NOTICE content to redistribute. Stated explicitly |

**Not claimed:** that adding files makes the pack compliant overall. §4 is met
for cg-image-filter. Section 5 below is not met and cannot be met by adding
files.

### Why there is no `LICENSE` at the pack root

The brief allowed "a clearly-named third-party licences file … if you justify
it". A bare `LICENSE` containing Apache-2.0 at the root of `ComfyUI_INSTARAW/`
would read as "this whole pack is Apache-2.0". That is false — 28 files in the
pack carry `PROPRIETARY SOFTWARE - ALL RIGHTS RESERVED` (e.g.
`nodes/interactive_nodes/interactive_crop.py:3-4`) — and it would appear to
grant buyers Apache rights over proprietary code. It also contradicts
requirement 3's demand that scope be unambiguous. Full reasoning in
`notes/WS3-questions.md` Q2, along with the gap it leaves: **the pack still
states no licence of its own anywhere**, which someone must write before sale.

---

## 3. Files changed

New (6):

```
ComfyUI_INSTARAW/THIRD_PARTY_NOTICES.md
ComfyUI_INSTARAW/licenses/Apache-2.0.txt
ComfyUI_INSTARAW/licenses/MIT-Filmgrainer.txt
ComfyUI_INSTARAW/licenses/OFL-1.1-BricolageGrotesque.txt
ComfyUI_INSTARAW/licenses/ICC-sRGB-profile-license.txt
ComfyUI_INSTARAW/fonts/OFL.txt
```

Modified — **comment header prepended, nothing else** (17):

```
nodes/interactive_nodes/image_filter.py            nodes/utility_nodes/list_utility_nodes.py
nodes/interactive_nodes/image_filter_messaging.py  nodes/utility_nodes/mask_utility_nodes.py
js/image_filter.js  js/popup.js  js/log.js         nodes/utility_nodes/string_utility_nodes.py
js/utils.js  js/mask_utils.js  js/floating_window.js
js/filter.css  js/floating_window.css  js/zoomed.css
modules/detection_bypass/filmgrainer_local/{filmgrainer,graingen,graingamma}.py
```

Every one of the 17 was proved to be a pure prepend by taking the last N bytes
of the new file, where N is the original file size, and byte-comparing against
a pre-edit backup:

```
js/filter.css                                              + 1122 bytes  BODY-IDENTICAL
js/floating_window.css                                     + 1071 bytes  BODY-IDENTICAL
js/floating_window.js                                      + 1236 bytes  BODY-IDENTICAL
js/image_filter.js                                         + 1313 bytes  BODY-IDENTICAL
js/log.js                                                  + 1213 bytes  BODY-IDENTICAL
js/mask_utils.js                                           + 1252 bytes  BODY-IDENTICAL
js/popup.js                                                + 1295 bytes  BODY-IDENTICAL
js/utils.js                                                + 1206 bytes  BODY-IDENTICAL
js/zoomed.css                                              + 1110 bytes  BODY-IDENTICAL
modules/detection_bypass/filmgrainer_local/filmgrainer.py  + 1119 bytes  BODY-IDENTICAL
modules/detection_bypass/filmgrainer_local/graingamma.py   +  839 bytes  BODY-IDENTICAL
modules/detection_bypass/filmgrainer_local/graingen.py     +  839 bytes  BODY-IDENTICAL
nodes/interactive_nodes/image_filter.py                    + 1442 bytes  BODY-IDENTICAL
nodes/interactive_nodes/image_filter_messaging.py          + 1414 bytes  BODY-IDENTICAL
nodes/utility_nodes/list_utility_nodes.py                  + 1221 bytes  BODY-IDENTICAL
nodes/utility_nodes/mask_utility_nodes.py                  + 1301 bytes  BODY-IDENTICAL
nodes/utility_nodes/string_utility_nodes.py                + 1384 bytes  BODY-IDENTICAL
```

Comment style follows each file: `#` for Python, `//` for JS, `/* */` for CSS.

---

## 4. Other vendored third-party code found (task item 5)

`filmgrainer_local` was flagged in the brief on its name. It is real, and it
was not the only one.

### 4.1 Filmgrainer — MIT — **fixed**

`https://github.com/larspontoppidan/filmgrainer`, `Copyright (c) 2022 Lars Ole
Pontoppidan`. Verified by diff against upstream:

- `graingen.py` — **byte-identical** to upstream
- `graingamma.py` — **byte-identical** to upstream
- `filmgrainer.py` — upstream with relative imports, `tempfile.gettempdir()`,
  `os.makedirs`, prints commented out, `map`→`map_obj`

What was actually there before: a single line,
`filmgrainer.py` (now line 26, was line 4) — `# Filmgrainer - by Lars Ole Pontoppidan - MIT License`.
**No copyright year, no permission notice, no warranty disclaimer, and nothing
at all in the other two files.** MIT requires the copyright notice *and* the
permission notice in all copies. Fixed: `licenses/MIT-Filmgrainer.txt` plus
headers on all three files.

### 4.2 Bricolage Grotesque font — OFL-1.1 — **fixed**

`fonts/BricolageGrotesque.ttf`. I parsed the shipped file's own `name` table:

- name ID 0: `Copyright 2022 The Bricolage Grotesque Project Authors (https://github.com/ateliertriay/bricolage)`
- name ID 13: `This Font Software is licensed under the SIL Open Font License, Version 1.1`
- name ID 14: `https://scripts.sil.org/OFL`
- has an `fvar` table — it is the variable font, v1.001, PS name `BricolageGrotesque-96ptExtraBold`

OFL clause 2 permits bundling and selling with other software **provided each
copy contains the copyright notice and the licence**, which was not shipped.
Fixed: upstream `OFL.txt` (4,403 B, md5 `ca124d9d…8ceb`) at `fonts/OFL.txt`
and `licenses/OFL-1.1-BricolageGrotesque.txt`. No Reserved Font Name is
declared after the copyright statement, so clause 3 does not bite, and the
renamed filename is not a modification of the Font Software.

### 4.3 sRGB ICC profile — permissive — **fixed**

`modules/color_profiles/sRGB_IEC61966-2-1_no_black_scaling.icc` is
**byte-identical** to the ICC registry's own copy — 3,052 B, md5
`ce7471dab641af1016dfc8f3482da966`. Its `cprt` tag, which I read out of the
file, says `Copyright International Color Consortium, 2009`.

The ICC notes this profile carries *different* terms from the standard ICC
profile licence. The grant is conditional on the file not being changed
(including that tag), on not using ICC's name in advertising about the
distribution, and on the "AS IS" acknowledgement — which is why the text must
ship. Fixed: `licenses/ICC-sRGB-profile-license.txt`.

### 4.4 UnMarker — **NOT fixable by adding a notice**

`modules/detection_bypass/utils/adaptive_filter.py` and `unmarker_losses.py`
declare in their own docstrings that they are ported from
`ai-watermark/modules/attack/unmark/cw.py:Filter` and `losses.py`. I fetched
both upstream files and compared:

- `unmarker_losses.py` shares 7 class names (`NormLoss`, `MeanLoss`,
  `PerceptualLoss`, `LpipsAlex`, `LpipsVGG`, `DeeplossVGG`, `FFTLoss`) and
  `get_loss` with upstream, plus dozens of verbatim lines
- `adaptive_filter.py` shares private methods `__apply_filter`,
  `__get_color_kernel`, `__get_init_w`, `__compute_filter_loss` and dozens of
  verbatim expression lines with `cw.py`

`https://github.com/andrekassis/ai-watermark` `LICENSE` §3.3, which I fetched
and read:

> The Work and any derivative works thereof only may be used or intended for
> use non-commercially. … "non-commercially" means for research or evaluation
> purposes only.

### 4.5 GrainNet — **NOT fixable by adding a notice**

- `pretrained/neural_grain/grainnet.pt` is **byte-identical** to
  `Gwilherm-LESNE/Neural_Film_Grain_Rendering` `models/GrainNet/default/grainnet.pt`
  — 45,929 B, md5 `91907c73885d4ac65790b198657a80d5`, confirmed with `cmp`
- `modules/neural_grain/net.py` differs from upstream `net.py` by **three
  lines out of 192** (a CUDA-move refactor)

That repo has no LICENSE file. Its README section `## Licence`, in full:

> All rights reserved. The code is released for academic research use only.

**Neither of these is curable by attribution.** Both are written refusals of
commercial use — stricter than LUSTIFY, which at least permits selling output.
I did not delete them: file deletion inside the pack was outside this run's
brief. But **neither `INSTARAW_NeuralGrain` nor `INSTARAW_Spectral_Normalizer`
appears anywhere in `OFMTech-NSFW/OFMTech_NSFW.json`**, so removing both trees
would change no rendered output. Logged as Q4 in `notes/WS3-questions.md`.

This is the second time this project has had a "clean" licence audit that
missed something. Recording so it does not read as cleared: I did **not**
establish terms for `modules/authenticity_profiles/*.icc` (iPhone device
profiles) or `modules/detection_bypass/_luts/*.cube` (several carry
third-party creator names in the filename). Both are logged as uninvestigated
in `THIRD_PARTY_NOTICES.md` §5.3.

---

## 5. Verification — pasted output

ComfyUI was **not** restarted. The repo copy and the install target
`/workspace/ComfyUI/custom_nodes/ComfyUI_INSTARAW/` were synced and now differ
only by the runtime `cache/` directory and `__pycache__`.

**Byte-compile, repo copy — all 8 Python files touched:**

```
$ cd /workspace/nsfw-fix/OFMTech-NSFW/ComfyUI_INSTARAW && python3 -m py_compile \
    nodes/interactive_nodes/image_filter.py nodes/interactive_nodes/image_filter_messaging.py \
    nodes/utility_nodes/list_utility_nodes.py nodes/utility_nodes/mask_utility_nodes.py \
    nodes/utility_nodes/string_utility_nodes.py \
    modules/detection_bypass/filmgrainer_local/{filmgrainer,graingen,graingamma}.py
py_compile exit=0  (0 = all 8 python files compiled clean)
Python 3.12.12
```

**Byte-compile, installed copy:**

```
py_compile (INSTALLED copy at /workspace/ComfyUI/custom_nodes/) exit=0
```

**AST-parse of every Python file in the installed pack:**

```
parsed 107 python files, 0 syntax errors
```

**JavaScript — `node --check` (v24.12.0), after proving the checker rejects
bad input:**

```
--- broken.mjs ---
SyntaxError: Function statements require a function name
exit=1
--- ok.mjs (copy of popup.js) ---
exit=0

floating_window.mjs exit=0
image_filter.mjs    exit=0
log.mjs             exit=0
mask_utils.mjs      exit=0
popup.mjs           exit=0
utils.mjs           exit=0
```

**CSS — comment and brace balance:**

```
js/filter.css              open-comments=2 close-comments=2 braces {=16 }=16  balanced=True
js/floating_window.css     open-comments=6 close-comments=6 braces {=15 }=15  balanced=True
js/zoomed.css              open-comments=1 close-comments=1 braces {=8  }=8   balanced=True
```

**Real import of the MIT-vendored package from the installed pack:**

```
imported OK from the INSTALLED pack:
  filmgrainer.MASK_CACHE_PATH = /tmp/filmgrainer-mask-cache
  filmgrainer._grainTypes(2)  = (1, 45)
  graingen.grainGen           = <function grainGen at 0x7337263d65c0>
  graingamma.Map.calculate    = <function Map.calculate at 0x7337263d62a0>
exit=0
```

**Real import of every edited node module (ComfyUI's `server`/`nodes`/`comfy`
stubbed, so nothing touched the live server or the GPU):**

```
image_filter_messaging OK -> ['Response', 'MessageState', 'send_and_wait', 'wait_for_response']
image_filter OK -> ['INSTARAW_ImageFilter', 'INSTARAW_MaskImageFilter', 'INSTARAW_TextImageFilter']
list_utility_nodes OK -> ['INSTARAW_BatchFromImageList', 'INSTARAW_ImageListFromBatch',
                          'INSTARAW_PickFromList', 'INSTARAW_StringListFromStrings']
mask_utility_nodes OK -> ['INSTARAW_MaskCombine', 'INSTARAW_MaskedSection']
string_utility_nodes OK -> ['INSTARAW_AnyListToString', 'INSTARAW_ConcatenateStringsNullSafe',
                            'INSTARAW_SplitByCommas', 'INSTARAW_StringCombine',
                            'INSTARAW_StringToFloat', 'INSTARAW_StringToInt']
INPUT_TYPES() executes on a derived node: ['images', 'timeout', 'ontimeout', 'cache_behavior']
```

**Live ComfyUI still healthy, not restarted:**

```
GET /system_stats HTTP=200
ComfyUI reports 1936 node types, 92 INSTARAW node types registered
  INSTARAW_ImageFilter             registered
  INSTARAW_MaskImageFilter         registered
  INSTARAW_TextImageFilter         registered
  INSTARAW_BatchFromImageList      registered
  INSTARAW_MaskedSection           registered
  INSTARAW_SplitByCommas           registered
  INSTARAW_NeuralGrain             registered
```

Note on scope of that last check: `/object_info` reflects the node set from
ComfyUI's startup, i.e. *before* my edits, so it proves the server is
undisturbed — not that my edits load. The evidence that my edits are inert is
the byte-identical-body proof plus the compile and import runs above.

---

## 6. Limits of what this establishes

- The Apache-covered code **is live in the shipped graph** —
  `INSTARAW_ImageFilter`, `INSTARAW_BatchFromImageList` and
  `INSTARAW_ImageListFromBatch` all appear in `OFMTech_NSFW.json`. This was not
  a dormant obligation.
- The copyright line for cg-image-filter is **constructed, not quoted**,
  because upstream states none. Labelled as inference wherever it appears.
- Upstream UnMarker's `losses.py` imports a vendored `special_loss` tree.
  That tree was **not** copied here: `unmarker_losses.py` contains zero
  references to `special_loss`, and `find` over the pack returns no such path.
  The port substitutes `lpips` instead. So that provenance chain does not
  extend into this pack.
- §4.4 and §4.5 are reported, not resolved. Nothing I shipped makes them
  shippable.
