# QUESTIONS.md

Per `CLAUDE.md`: each question carries my best guess, my reasoning, and the
lower-risk option I took so the work could continue. Nothing here blocked me.

---

## Q1 — Are `#483`'s five image inputs *meant* to be connected?

**Context.** `INSTARAW_RealityPromptGenerator` has all five image inputs unlinked.
This was framed as "either that is the bug, or it is fed some other way".

**Answer, from the source — it is neither, quite.** The image inputs are declared
**`optional`** (`reality_prompt_generator.py:41-77`, all inside the `"optional"`
dict opened at `:40`), and the workflow's slots carry `"shape": 7`, the
optional-slot shape. Unlinked is a **legitimate state**: it selects txt2img.
`execute` sets `resolved = "img2img" if image_count > 0 else "txt2img"` (`:208-212`).

Also worth knowing: **only `images` is ever read**. `images2`, `images3`,
`images4`, `character_image` and `aspect_label` are accepted as parameters and
referenced nowhere in the function body. Whatever they were for, the Python side
does not use them; `js/reality_prompt_generator.js:9191-9219` reads linked image
data client-side instead.

**So the unconnected inputs are not the bug.** The real defect is A0 — the prompt
batch is stored under a key nothing reads.

**My guess:** these inputs are vestigial for txt2img use and only matter if you
ship an img2img variant. **Action taken:** documented, changed nothing.

---

## Q2 — What should sg2's face detailer prompt actually say?

**Context.** `#106` reads `"TRIGGER, PROMT FOR YOUR MODEL"` and drives the face
pass at denoise 0.8 (`AUDIT.md` A4).

This needs your text — it depends on the LoRA a buyer loads and on whether the
Z-Image checkpoint wants a trigger word. I cannot invent it.

**My guess:** it is meant to be replaced per-character, and the intended shape is
`<lora trigger>, <character description>`. The fact that the *negative* (`#105`)
is fully written while only the positive is a placeholder supports that.

**Action taken:** left it exactly as-is and flagged it at S1. Changing it would
alter output, which `CLAUDE.md` puts out of scope for this session.

**Sub-question:** should `#105`/`#106` encode through the `#116` "Your ZIT LoRa"
stack rather than the raw `#110` CLIP? Right now a buyer's Z-Image LoRA does not
affect these encodes. I think it should, but that is an output-changing edit.

---

## Q3 — Revive or delete the ControlNet + IPAdapter + depth path?

**My recommendation: delete, and delete the branding node with it.**

**Reasoning.**
1. The path is **mis-wired**, not merely disabled — `#641 SetUnionControlNetType`
   is in parallel with `#638`, so the union type is never applied (`AUDIT.md` A5).
   Reviving it as-is gives a union ControlNet with no type set.
2. It needs **four** separate repairs to work (`PROPOSALS.md` P12), including
   wiring an image source that does not currently exist.
3. It costs real install weight: `controlnet-union-sdxl-promax.safetensors`
   (~2.5 GB), `depth_anything_v2_vitl.pth`, plus the IPAdapter models — **none of
   which the setup script fetches** (`SETUP.md`). So today it is dead weight that
   would also *fail to install*.
4. The graph is committed to txt2img elsewhere: `#636 INSTARAW_LatentSwitch` is
   `false` **and** `#631 VAEEncode` is bypassed. Two independent switches both say
   txt2img.

**Counter-argument I can see:** ControlNet + IPAdapter face conditioning is a
plausible premium feature for a character-consistency product, and
`IPAdapterUnifiedLoader` is set to `"PLUS FACE (portraits)"`, which is exactly
the character-likeness use case. If that is on the roadmap, repair it properly as
a separate feature rather than leaving a broken skeleton in the shipped graph.

**Action taken:** the lower-risk option — **changed nothing**. Documented the
mis-wiring so the decision is informed either way.

---

## Q4 — What are the `cnr_id: comfy-core, ver: 0.15.1` and `0.17.2` nodes?

**Context.** Six nodes carry `ver: "0.15.1"` and one carries `"0.17.2"` under
`cnr_id: "comfy-core"`, while every other core node is in the `0.3.x` series
(`AUDIT.md` A12).

**My guess:** these are **frontend** package versions, not core versions —
`comfyui-frontend-package` is in the 1.x range, but an older or differently-scoped
version string may have been written into `properties.ver` by a particular build.
I could not confirm this and I do not want to assert it.

**Why it probably does not matter:** `properties.ver` is written at edit time and
constrains nothing at load time. ComfyUI does not validate it.

**Action taken:** recorded the fact, labelled the interpretation as unresolved,
and derived the version floor from the `0.3.x` values only (max `0.3.70`).

---

## Q5 — Is `lumina2` the right `CLIPLoader` type for a Qwen encoder on Z-Image?

**Context.** sg2 `#110 CLIPLoader` = `qwen.safetensors`, type `lumina2`.

I cannot check ComfyUI's supported type list without a ComfyUI install, and I will
not guess at a model-architecture detail.

**My guess:** it is correct, because the graph reportedly runs and a wrong CLIP
type usually fails loudly at load rather than degrading quietly. But "reportedly
runs" is not evidence I have.

**Action taken:** flagged in `MAP.md` §15 as unresolved. One line of the pod
session's first run settles it — if the graph loads and sg2 produces sane faces,
it is right.

**Related, and more suspicious:** the setup script also fetches
`qwen-4b-zimage-heretic-q8.gguf` into `text_encoders`. That name says
*Z-Image* explicitly, while `qwen.safetensors` does not. If the graph is meant to
use the GGUF, it would need `CLIPLoaderGGUF` from ComfyUI-GGUF, **which is not in
any pack list**. Worth one look on the pod.

---

## Q6 — Are the six orphaned prompts worth recovering?

**Context.** `#483.properties.prompt_queue_data` holds six complete prompt
entries that nothing reads (`AUDIT.md` A0).

**My guess: no.** All six are interior/architectural photography — walk-in
closets, a home theatre, people floating in a pool. For an NSFW character
pipeline they read as leftover fixtures from unrelated testing, not as product
content. They also all share `seed: 1111111`.

**Action taken:** documented both options in `PROPOSALS.md` P0 and recommended
authoring real prompts rather than migrating these. I did **not** modify the
workflow — `CLAUDE.md` restricts edits to provably-inert changes, and this is
not one.

---

## Q7 — Should `ComfyUI_INSTARAW` be added to `NODE_REPOS`?

**Context.** The setup script only checks whether the directory exists and prints
a "still to do" line (`aiofm_setup.sh:1619-1624`); it never installs it.

**Complication:** the pack has **no git remote in this folder, no
`pyproject.toml`, no LICENSE, and no `cnr_id`** — so it cannot be resolved through
`api.comfy.org` like the other six packs, and `NODE_REPOS` entries are
`<url>|<sha>` pairs, which this has no URL for. The node's own metadata gives
`aux_id: "instara-io/ComfyUI_INSTARAW"` and `ver: 12afb909b3380bd4a3f118061654dd72d1edcd4c`
(`#645`), implying a private repo at `github.com/instara-io/ComfyUI_INSTARAW`.

**My guess:** it is a private repo, so a buyer-facing script cannot clone it, which
is exactly why `INSTALL MODELS.txt` step 3 tells the buyer to drag the folder in by
hand.

**Action taken:** in `SETUP.md` I proposed vendoring it into the distribution
archive and copying it into place, rather than adding it to `NODE_REPOS` — and
flagged that its `requirements.txt` must **not** be installed unfiltered
(`AUDIT.md` A17). Recorded the `12afb909…` SHA as the provenance marker.

---

## Q8 — Is `#98`'s whole-image tiling deliberate?

**Context.** sg0 `#98 UltimateSDUpscale` has `tile_width`/`tile_height` wired from
`GetImageSize`, so tiles equal the full frame.

**My guess: deliberate, to avoid tile seams** — `seam_fix_mode` is `"None"`, and
whole-image tiling is the one configuration where that setting is safe. Someone
probably hit seams and solved it this way.

**Why it is still a problem:** it makes peak VRAM scale with the buyer's chosen
resolution, on hardware you do not control, while the widgets display a reassuring
512×512.

**Action taken:** documented in `AUDIT.md` A7, proposed the fixed-tile test in
`PROPOSALS.md` P11 **with seam-hunting as the explicit kill criterion** rather
than assuming seams were not the original motivation. Changed nothing.
