# P2-RENDER — judgement calls

Logged as I made them, with the reasoning and the option I took. I did not stop
to ask; where a call could have gone either way I took the lower-risk option and
wrote it down here.

---

## 1. I changed the prompt. That is a deviation from the shipped batch entry.

The brief said to use the shipped batch entry but with a prompt that exercises
the complaint, and that it must ask for visible pores **and** freckles. The
shipped entry asks for `natural skin texture with visible pores` and says
nothing about freckles.

**Taken:** the shipped positive prompt with exactly one clause inserted —
`light freckles across her nose and cheeks, ` after `visible pores, `. Negative
prompt and seed left at the shipped values (`12345`, `seed_control: fixed`).

**Consequence to be honest about:** my numbers are not comparable with WS4's.
WS4 rendered the unmodified shipped prompt. Any cross-reference between my
grid and `results/ws4/` is a different prompt as well as (for most of their
arms) a different base graph.

**Worth recording:** the bump artefact is present in WS4's render of the
*unmodified* shipped prompt too — I looked at
`results/ws4/A_baseline/HasMetadata_00001_.png` at 1:1 before starting. So
asking for freckles is not what causes it. It makes the arm honest, not the
defect.

## 2. Arm A leaves `#598 ToDetailerPipeSDXL` in the graph instead of deleting it

Removing `#607` orphans `#598`, whose only output link was `1256` → `#607`.

The tidy thing would be to delete `#598` as well. I did not, because `#598`'s
two `clip` inputs (links `1367`, `1368`) are the **only** internal consumers of
sg-2 input slot 4. Deleting the node strands a declared subgraph input, and
removing the input slot instead would shift the host's slot indices — which is
the widget-desync trap this project keeps hitting. Not worth it for an arm
whose purpose is to measure an image.

**It costs nothing at run time.** `execution.py:727` seeds the execution list
from `execute_outputs` and walks backwards; `validate_prompt`
(`execution.py:1014-1063`) validates output nodes and their dependencies only.
An unreferenced node is neither validated nor executed. `#611
UltralyticsDetectorProvider` has no other consumer either, so it also stops
loading in this arm. That is part of arm A's time saving, not a confound.

**If arm A is adopted for shipping, `#598` and `#611` should be deleted
properly, and that edit needs its own graph diff.** Not my call and not this
run's.

## 3. I strip one input from every submitted prompt besides `pick_list`

`#419 Image Comparer (rgthree)` serialises a frontend-only widget,
`rgthree_comparer`, containing `/api/view` URLs for whatever temp previews that
browser session had seen. It is **not in the node's `INPUT_TYPES` at all** —
`/object_info` shows `required: {}`, `optional: {image_a, image_b}`,
`hidden: {prompt, extra_pnginfo}` — so the server ignores it.

My phase-1 arms were converted in a browser session that had seen no previews
and carry no such key; my phase-2 session had seen some and did. Left alone
that would appear as a spurious per-arm difference and would change that node's
cache key.

**Taken:** delete `419.inputs.rgthree_comparer` from every submitted prompt, so
all arms match. Recorded in each `meta.json` as `rgthree_comparer_stripped`.
This changes no executed node's inputs.

## 4. No cfg arm, on main's instruction

`#114` runs `cfg 1`, which is required by a guidance-distilled model; at cfg 1
the uncond branch is never evaluated. P3 owns that question. I have no cfg arm
and made no cfg claim.

## 5. Ladder values

denoise `0.65 / 0.50 / 0.35` and steps `16 / 8`. `8` is the model's design
point per ComfyUI's own turbo templates and per `#165 Mouth Detailer` in this
same subgraph, which already runs 8 steps at denoise 0.35 on the same model.
`0.35` on the denoise ladder deliberately lands on the mouth pass's value, so
one arm answers "what if the face were tuned like the mouth already is".

## 6. Control repeat

WS4 established this pipeline is bit-deterministic under fixed seeds — five
submissions of one graph and two of another, all pairwise MSE exactly 0,
including one run with zero cached nodes. Every `control_after_generate` in the
graph is `"fixed"` and my arms change one input each.

**Taken:** rely on that, and spend the GPU on arms instead of a control repeat,
**unless** two arms come back looking suspiciously identical or suspiciously
unrelated, in which case a repeat is the first thing to run. Recorded because
it is an assumption I am carrying, not something I proved for my prompt.

## 7. Arm directories hold exactly three files

P2-SHEET builds the owner's contact sheets from
`results/face/arms/<arm>/{*.png, api_graph.json, meta.json}`. I kept each
directory to exactly that so a glob cannot pick up anything unexpected. The arm
**workflow** JSONs (UI format, pre-conversion) therefore live only in the
session scratchpad; the `api_graph.json` in each arm directory is the
authoritative record of what was actually submitted.

## 8. The bump metric is mine and it is supporting detail only

Looking at the baseline face at 1:1, the artefact is **bright convex blobs
6-14 px across with specular tops** — the opposite of a pore, which is a small
dark depression. So I count bright local maxima at the blob scale and dark
local minima at the fine scale, over a **single skin mask computed once from
the baseline and reused for every arm** (recomputing it per arm moves the
denominator with the change under test).

It is a crude mask and a hand-set threshold. It is in the report as supporting
detail because the owner has said outright that metrics tell you something
changed, not whether it looks better. The crops carry the argument.

## 9. What I did not do

No `POST /api/interrupt`. No `POST /api/queue {"clear": true}`. No hashing of
rendered output as a verification method. No commit to
`OFMTech-NSFW/OFMTech_NSFW.json`.
