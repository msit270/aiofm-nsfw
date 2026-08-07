# R4B — removing UnMarker (B3) and GrainNet (B4) from `ComfyUI_INSTARAW`

Track 1, licensing. Source edited: `/workspace/nsfw-fix/OFMTech-NSFW/ComfyUI_INSTARAW/`
(the authoritative shipping copy). No git run. No GPU. No renders. Main session
re-verifies and commits.

**Headline:** the pack goes from **98 registered node types to 96**. The two that
go are `INSTARAW_NeuralGrain` and `INSTARAW_Spectral_Normalizer`, neither of which
appears in `OFMTech_NSFW.json`. Every one of the other **96 is byte-for-byte
identical in its registration surface** — module, qualname, `RETURN_TYPES`,
`RETURN_NAMES`, `FUNCTION`, `CATEGORY`, `OUTPUT_NODE`, `INPUT_IS_LIST`,
`OUTPUT_IS_LIST`, display name and the full `INPUT_TYPES()` spec. ComfyUI's own
loader returns `True` with **zero warnings**.

`QUESTIONS.md` §0 says the count was "95". Measured here it is **98 before**.
I did not try to reconcile that; 98 is what the current source registers, and the
before/after pair is internally consistent (98 − 2 = 96, arithmetic checked).

---

## 1. Node types the shipping workflow actually needs

`grep -o 'INSTARAW_[A-Za-z0-9_]*' OFMTech_NSFW.json`, plus a JSON walk over every
`type` field. **Seven distinct types, and no others:**

| node type | notes |
|---|---|
| `INSTARAW_RealityPromptGenerator` | this is `#483` (`"1 · YOUR PROMPTS & SEED - start here"`), the prompt/negative/seed source |
| `INSTARAW_BatchFromImageList` | |
| `INSTARAW_BooleanBypass` | |
| `INSTARAW_ImageFilter` | |
| `INSTARAW_ImageListFromBatch` | |
| `INSTARAW_ImageResizeFill` | |
| `INSTARAW_PromptBatchPreview` | |

All seven are present in the AFTER mapping — checked explicitly, not by count.
Neither `INSTARAW_NeuralGrain` nor `INSTARAW_Spectral_Normalizer` appears in the
workflow (re-verified by grep, both spellings), so removing them changes no
rendered output for this product.

---

## 2. The import map (why a naive `rm` gave 0 nodes)

Every arrow below is an unconditional, top-level import. Line numbers are from the
**pre-edit** files.

### 2.1 The B3 / UnMarker chain — this is the one that took the pack to zero

```
ComfyUI_INSTARAW/__init__.py:25          from .nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS
  └─ nodes/__init__.py:14                from .utility_nodes import (...)
       └─ nodes/utility_nodes/__init__.py    ← six separate lines reach the same package:
            :77  from .color_science_node    → color_science_node.py:10   from ...modules.detection_bypass.utils import apply_lut, load_lut
            :73  from .spectral_engine_node  → spectral_engine_node.py:8  from ...modules.detection_bypass.utils import direct_spectral_match
            :96  from .fft_match             → fft_match.py:6             ...utils.direct_spectral_matching
            :97  from .texture_normalize     → texture_normalize.py:6,7   ...utils.glcm_normalization / .lbp_normalization
            :99  from .texture_engine        → texture_engine.py:12       ...utils.texture_utils
            :102 from .blend_colors          → blend_colors.py:4          ...utils.blend
                 (importing ANY submodule of a package first executes the package __init__)
                 └─ modules/detection_bypass/utils/__init__.py:12   from .unmarker_full import normalize_spectrum_twostage, SpectralNormalizer
                      └─ utils/unmarker_full.py:19  from .unmarker_losses import FFTLoss, LpipsVGG, LpipsAlex, NormLoss, DeeplossVGG   ← B3
                      └─ utils/unmarker_full.py:20  from .adaptive_filter import AdaptiveFilter                                        ← B3
                      └─ utils/unmarker_full.py:21  from .stats_utils import StatsMatcher                                              (own code)
                 └─ modules/detection_bypass/utils/__init__.py:16   from .non_semantic_attack import non_semantic_attack
```

Delete `adaptive_filter.py` and `unmarker_losses.py` and leave line 12 alone, and
`utils/__init__.py` raises `ModuleNotFoundError`. That propagates up through
`utility_nodes/__init__.py` → `nodes/__init__.py` → the pack `__init__.py`, where
ComfyUI's `nodes.load_custom_node` (`/workspace/comfy-r5-verify/nodes.py:2294-2297`)
catches it, logs `Cannot import ... module for custom nodes`, and **returns
`False`** — registering nothing at all. That is the measured 95 → 0 / `IMPORT
FAILED` in `QUESTIONS.md` §0, and it is why the fix has to be a code change.

Note the failure has nothing to do with the two attack nodes themselves. It is
`INSTARAW_ImageFilter`, `INSTARAW_RealityPromptGenerator` and every other node in
the pack going down because a package `__init__` two directories away could not
resolve one name.

### 2.2 The B4 / GrainNet chain — shallow, no shared module

```
nodes/utility_nodes/__init__.py:82-85    from .neural_grain_node import NODE_CLASS_MAPPINGS as NEURAL_GRAIN_MAPPINGS, ...
  └─ nodes/utility_nodes/neural_grain_node.py:10   from ...modules.neural_grain.net import GrainNet     ← B4
     nodes/utility_nodes/neural_grain_node.py:15   MODEL_PATH = <root>/pretrained/neural_grain/grainnet.pt  ← B4 weights
  used at :147  **NEURAL_GRAIN_MAPPINGS
  used at :196  **NEURAL_GRAIN_DISPLAY_MAPPINGS
```

`modules/neural_grain/` had no `__init__.py` (namespace package) and contained
only `net.py`. `pretrained/` existed only to hold `grainnet.pt`.

### 2.3 The four modules `QUESTIONS.md` says nobody traced — traced, with a result

Traced statically **and** measured by importing each one on an isolated CPU
instance (`results/run4/instaraw/probe-BEFORE.json`).

| module | who imports it | what it imports | import status BEFORE any edit |
|---|---|---|---|
| `modules/detection_bypass/processor.py` | only `pipeline_v2.py:18` | `:20-32` `from .utils import (..., attack_non_semantic, ...)`; `:33` `.camera_pipeline` | **FAIL** — `ImportError: cannot import name 'attack_non_semantic'`. `utils/__init__` exports `non_semantic_attack`, not `attack_non_semantic`. The name exists nowhere in the pack. |
| `modules/detection_bypass/pipeline_v2.py` | **nothing** | `:15` `.filmgrainer_local.filmgrainer`; `:18` `from .processor import process_image` | **FAIL** — inherits processor's error |
| `modules/detection_bypass/pipeline.py` | **nothing** | top level: stdlib + torch/PIL/numpy only. `:89`, inside `_run_unmarker()`: `from .utils import attack_non_semantic, attack_two_stage_unmarker` | **OK to import**, but `_run_unmarker` — its entire reason to exist — would raise on first call. `attack_two_stage_unmarker` exists nowhere in the pack either. |
| `modules/detection_bypass/utils/non_semantic_attack.py` | `utils/__init__.py:16` and `nodes/utility_nodes/spectral_normalizer_node.py:4` | `torch`, `torch.optim`, `lpips`, `numpy`, `threading`. **No import of any encumbered module.** | OK |

So: `processor.py` and `pipeline_v2.py` were **already dead and already broken**
before this session, and `pipeline.py` was dead with a broken core method. None of
them is reachable from `NODE_CLASS_MAPPINGS`. Nothing dynamic reaches them either
— no `importlib`, `__import__`, `getattr`-by-string or entry in any mapping names
them (grepped across `.py`, `.js`, `.json` and the workflow).

### 2.4 Symbols exported from the encumbered files, and who used them

- `normalize_spectrum_twostage`, `SpectralNormalizer` (from `unmarker_full.py`):
  referenced **only** inside `unmarker_full.py` itself and re-exported by
  `utils/__init__.py`. **No node, no other module.**
- `FFTLoss`, `LpipsVGG`, `LpipsAlex`, `NormLoss`, `DeeplossVGG` (`unmarker_losses.py`)
  and `AdaptiveFilter` (`adaptive_filter.py`): used **only** by `unmarker_full.py`.
- `GrainNet` (`neural_grain/net.py`): used only by `neural_grain_node.py`.
- `non_semantic_attack`: used by `spectral_normalizer_node.py:49` and re-exported.

Nothing needed splitting. No file mixed encumbered code with code the product uses.

---

## 3. What I changed

### 3.1 Files deleted (11)

**B3 — named in `QUESTIONS.md`:**
1. `modules/detection_bypass/utils/adaptive_filter.py` — docstring: *"Adaptive spatial filtering for UnMarker. Ported from ai-watermark/modules/attack/unmark/cw.py:Filter"*
2. `modules/detection_bypass/utils/unmarker_losses.py` — docstring: *"Ported from ai-watermark/modules/attack/unmark/losses.py"*

**B3 — found by me, same subsystem:**
3. `modules/detection_bypass/utils/unmarker_full.py` — imports both of the above at
   module level (`:19`, `:20`); guaranteed `ImportError` once they are gone. Its
   two exports are used by nothing outside itself.
4. `modules/detection_bypass/utils/non_semantic_attack.py` — **judgment call, see §6.**
5. `nodes/utility_nodes/spectral_normalizer_node.py` — the `INSTARAW_Spectral_Normalizer`
   node; `non_semantic_attack` is its only engine, so it cannot survive #4.
6. `modules/detection_bypass/processor.py` — docstring: *"orchestrates … the UnMarker
   attack"*. Dead and already un-importable (§2.3).
7. `modules/detection_bypass/pipeline.py` — dead; `_run_unmarker()` is its purpose;
   calls two names that exist nowhere.
8. `modules/detection_bypass/pipeline_v2.py` — dead and already un-importable; its
   `_get_ns_args()` pass is literally named `"AI Normalizer (UnMarker Attack)"`
   (`:159`). Deleting `processor.py` would have left it importing a file that no
   longer exists.

**B4 — all named in `QUESTIONS.md`:**
9. `modules/neural_grain/net.py` (directory `modules/neural_grain/` removed, now empty)
10. `pretrained/neural_grain/grainnet.pt` (directories `pretrained/neural_grain/` and
    `pretrained/` removed, now empty)
11. `nodes/utility_nodes/neural_grain_node.py` — the `INSTARAW_NeuralGrain` node

### 3.2 Files edited (4)

**`modules/detection_bypass/utils/__init__.py`** — removed the two import lines
(old `:12` `unmarker_full`, old `:16` `non_semantic_attack`) and the three
corresponding `__all__` entries (`normalize_spectrum_twostage`,
`SpectralNormalizer`, `non_semantic_attack`). Added a three-line comment pointing
at `THIRD_PARTY_NOTICES.md` §5 — deliberately worded so it names no removed module,
which keeps a grep of the shipped source for `unmarker`/`grainnet`/`adaptive_filter`/
`neural_grain` clean outside the notices file. Every other import and `__all__`
entry is untouched.

**`nodes/utility_nodes/__init__.py`** — six deletions, no other change:
- old `:82-85` the `from .neural_grain_node import (...)` block
- old `:100` `from .spectral_normalizer_node import INSTARAW_Spectral_Normalizer`
- old `:147` `**NEURAL_GRAIN_MAPPINGS`
- old `:156` `"INSTARAW_Spectral_Normalizer": INSTARAW_Spectral_Normalizer,`
- old `:196` `**NEURAL_GRAIN_DISPLAY_MAPPINGS`
- old `:205` `"INSTARAW_Spectral_Normalizer": "🛡️ INSTARAW Spectral Normalizer",`

No `try`/`except` shim anywhere. A swallowed `ImportError` that half-registers is
the failure mode this project keeps finding, so the importing statement and the
dependent node class both go, and any future breakage is loud.

**`requirements.txt`** — comment-only. `kornia`'s justification comment listed
`adaptive_filter`; `lpips`'s listed `non_semantic_attack, unmarker_losses`. Both
packages **stay** — `kornia` is still imported by `feather_mask`,
`grow_mask_with_blur`, `realistic_noise`, `realistic_jpeg`, `texture_engine`, and
`lpips` by `texture_engine` (`texture_engine.py:7,9`). Only the stale names were
struck from the comments.

**`THIRD_PARTY_NOTICES.md`** — §5 rewritten: heading changed from "Items NOT
cleared" to "Items that were NOT cleared — **removed in this version**", §5.1 and
§5.2 marked removed with the full file list (including the six files beyond the
five originally named), §5.3 relabelled "Not yet investigated — **still shipped**".
The upstream findings (the ai-watermark §3.3 quote, the `grainnet.pt` md5, the
"academic research use only" quote) are kept verbatim as the record of why. A new
§5.2.1 documents the bytecode problem below. Sections 1-4 untouched; `licenses/`
untouched (it never held an UnMarker or GrainNet licence, so nothing there
over-claims).

### 3.3 `__pycache__` — the part that would have leaked the code anyway

**A `.pyc` of an encumbered module ships that module's code.** Proven, not
asserted:

```
$ strings modules/detection_bypass/utils/__pycache__/adaptive_filter.cpython-312.pyc
Adaptive spatial filtering for UnMarker.
Ported from ai-watermark/modules/attack/unmark/cw.py:Filter
```

Python (PEP 3147) never loads a `__pycache__/x.cpython-312.pyc` whose `x.py` is
absent, so an orphaned `.pyc` is invisible at runtime while still being shipped
bytes. `grep -a unmarker` over the tree hit ten `.pyc` files. **All `__pycache__/`
directories have been removed from the pack** — 14 directories, 103 `.pyc`. This is
provably inert: Python regenerates them from source, and no `.pyc` in the pack was
sourceless (checked all 103 against their `.py` before deleting).

**Disclosure:** 8 of those `.pyc` were in the pack at the start of my session; the
other ~95 were created by **my own import harness** running against the
authoritative tree before I noticed. I switched all later test runs to a scratch
copy with `sys.dont_write_bytecode = True`, and the product tree now contains
zero `.pyc` and zero `__pycache__`. File count: 175 at start − 8 pre-existing
`.pyc` = 167 source files; 167 − 11 deleted = **156**, which is what the tree
now holds. **Packaging must exclude `__pycache__`** or the next dev-machine run
puts it straight back.

---

## 4. Test transcripts

All under `/workspace/nsfw-fix/results/run4/instaraw/`. Harness scripts are in
`.../instaraw/tools/` so this can be re-run. **No main server touched** — nothing
was booted, no port was bound, 18188 and 19188 were never contacted. The ComfyUI
tree used as a host is the existing isolated checkout `/workspace/comfy-r5-verify`,
read-only (verified: no `.pyc` written into it).

| file | what it is |
|---|---|
| `count-BEFORE.json` / `.console.txt` | pack imported from the authoritative tree **before** any edit — `import_ok: true`, **98** classes, 98 display names, full sorted name list |
| `count-AFTER.json` / `.console.txt` | same, after — `import_ok: true`, **96** / 96 |
| `diff-BEFORE-AFTER.txt` | the name diff, the seven-workflow-type check, and the arithmetic |
| `probe-BEFORE.json` | per-module import status of the ten `detection_bypass` / `neural_grain` modules before the edit — this is where `processor.py` and `pipeline_v2.py` are shown already broken |
| `probe-AFTER.json` / `.console.txt` | after — `utils` and `camera_pipeline` still `OK`; the eight deleted modules `ModuleNotFoundError` |
| `sig-BEFORE.json` / `sig-AFTER.json` | full registration signature of all 98 / 96 node classes |
| `sig-diff.txt` | the field-by-field comparison |
| `loader-BEFORE.json` / `loader-AFTER.json` | the pack put through **ComfyUI's own** `nodes.load_custom_node`, the code path a real boot uses and the one that swallows exceptions into a warning |

### Results

**(a) BEFORE:** 98 `NODE_CLASS_MAPPINGS` entries, 98 display names, `import_ok: true`.

**(b) AFTER:** 96 / 96, `import_ok: true`. `98 − 2 = 96`, and the removed set is
**exactly** `INSTARAW_NeuralGrain` and `INSTARAW_Spectral_Normalizer`. Zero nodes
added, zero other nodes lost.

**(c)** All seven workflow node types present in the AFTER mapping, checked by name.

**Inertness beyond the count.** Counting alone would not catch a node that
survived with a changed signature, so I compared the whole registration surface of
all 96 survivors against an untouched pre-edit control — the installed copy at
`/workspace/comfy-r5-verify/custom_nodes/ComfyUI_INSTARAW`, which differs from the
authoritative source in only three files (`js/popup.js`,
`js/reality_prompt_generator.js`, `nodes/api_nodes/creative_api.py`), none of
which I touched, and which registers the same 98 types. Result: **0 differences**
across module, qualname, `RETURN_TYPES`, `RETURN_NAMES`, `FUNCTION`, `CATEGORY`,
`OUTPUT_NODE`, `INPUT_IS_LIST`, `OUTPUT_IS_LIST`, display name and the full
`INPUT_TYPES()` spec.

One apparent diff had to be normalised away and is worth recording:
`INSTARAW_SynthesizeAuthenticMetadata` builds its `start_date` / `end_date`
defaults from `datetime.now()` **inside `INPUT_TYPES()`**, so those two strings
differ between any two runs seven seconds apart. That is a pre-existing property
of the node, present identically in both trees, not something this change caused.

**Through ComfyUI's real loader:** `load_custom_node` returned `True` for both
control and edited pack, installing 98 and 96 nodes respectively, with **zero
warnings logged** in either case. `compileall` over every `.py` in the edited
pack: clean.

**(d)** `grep -rain -e unmarker -e grainnet -e adaptive_filter -e neural_grain
-e NeuralGrain -e GrainNet` over the whole pack, binary-safe, all file types:
matches in `THIRD_PARTY_NOTICES.md` **only**. Zero elsewhere — no `.py`, no `.js`,
no `.pyc`, no `requirements.txt`. Also zero references to `INSTARAW_NeuralGrain`
or `INSTARAW_Spectral_Normalizer` anywhere, including `js/` (no front-end
extension registered widgets for either).

**(e)** `pretrained/` does not exist. No `*.pt`, `*.pth`, `*.ckpt`, `*.safetensors`
or `*.onnx` anywhere in the pack. `grainnet.pt` was the only weight file it shipped.

---

## 5. Scope

Written: `OFMTech-NSFW/ComfyUI_INSTARAW/**`, `notes/R4B-instaraw-removal.md`,
`results/run4/instaraw/**`, and scratch. Nothing else. No git command of any kind
was run — not even `status`; the before/after control came from an existing
isolated checkout instead.

---

## 6. What I am not sure about — read this before committing

**6.1 `non_semantic_attack.py` + `INSTARAW_Spectral_Normalizer` is a judgment call,
and it is the one thing here I would most like a second opinion on.** It is the
only deletion not forced by the licence or by a broken import.

The case for removing it: its own docstring (`:10`) says it *"Runs the core
UnMarker-style optimization"*, and that is what it does — maximise a frequency-
domain distance subject to an LPIPS and an L2 constraint, which is the UnMarker
objective. Nobody has ever established whether it was written from the paper or
lifted from the repo. `THIRD_PARTY_NOTICES.md` §5.1's line-by-line comparison
against `ai-watermark@master` covered only the two files that **declare**
"Ported from"; it is silent on this one, which is not the same as clearing it.
Shipping uncleared UnMarker-lineage code in a product whose upstream forbids
commercial use is the exact risk this task exists to remove, and the brief named
`INSTARAW_Spectral_Normalizer` as output-neutral for this product.

The case against: it imports nothing encumbered — only `torch`, `torch.optim`,
`numpy`, `threading` and the pip `lpips` package — and copyright protects
expression, not algorithms. If someone diffs it against `ai-watermark` and it
shares nothing, it was shippable and a node was lost for no reason.

**I could not settle it from here** and took the option that removes the risk
rather than the one that keeps the feature. **Reverting is two files and two
lines:** restore `modules/detection_bypass/utils/non_semantic_attack.py` and
`nodes/utility_nodes/spectral_normalizer_node.py`, then put back the
`from .spectral_normalizer_node import ...` line and its two mapping entries in
`nodes/utility_nodes/__init__.py` (`utils/__init__.py` does **not** need the
`non_semantic_attack` re-export back — the node imports the module directly).
The real fix is to diff it against `https://github.com/andrekassis/ai-watermark`
the way §5.1 did for the other two.

**6.2 `pipeline.py` / `pipeline_v2.py` / `processor.py` are the owner's own code,
not encumbered code.** I deleted them because they are dead, two of the three
could not be imported at all, all three exist to drive the UnMarker attack, and
leaving them would have put `unmarker` back into a grep of the shipped source. If
the owner wants the film-grain / camera-simulation pipeline back one day,
`pipeline_v2.py` is the file to restore — but it would need `processor.py` back
**and** `processor.py`'s `attack_non_semantic` import fixed, because it has never
worked in this tree.

**6.3 Now-orphaned, left in place deliberately.**
`modules/detection_bypass/utils/stats_utils.py` (`StatsMatcher`) had exactly one
consumer, `unmarker_full.py:21`, and now has none. It is the owner's own code and
not encumbered, so removing it is a product decision, not a licensing one. Same for
`modules/detection_bypass/filmgrainer_local/` (MIT, cleared, covered by
`THIRD_PARTY_NOTICES.md` §2), whose only consumer was `pipeline_v2.py:15`. Both
still ship. Note `unmarker_full.py:58` also referenced a `pretrained/iphone_stats.npz`
that **was never in the pack** — `StatsMatcher` could only ever have been reached
through a file that did not exist.

**6.4 The 98-vs-95 discrepancy.** `QUESTIONS.md` §0 records 95 registered types;
I measure 98 on the current source, twice, on two different trees. I did not chase
it. If the earlier figure came from a different build, the "95 → 0" story still
holds — the mechanism in §2.1 is the same regardless of the starting number.

**6.5 Not verified in a browser.** The registration surface is proven identical
for all 96 survivors and the loader is proven clean, but no ComfyUI front end was
opened and `OFMTech_NSFW.json` was not loaded into a running graph. The remaining
risk is front-end only — a `js/` extension keyed to a removed node type — and I
grepped `js/` for both removed type names and their display names and found
nothing.

**6.6 Two pre-existing defects found in passing, not fixed** (out of scope, no
licence bearing): `utils/__init__.py` never exported `attack_non_semantic` or
`attack_two_stage_unmarker`, yet `processor.py:30` and `pipeline.py:89` both ask
for them — so those code paths have been broken for as long as the names have
differed. And `modules/detection_bypass/utils/` still ships
`direct_spectral_matching copy.py` and `direct_spectral_matching copy 2.py`,
two dead duplicates that nothing imports.
