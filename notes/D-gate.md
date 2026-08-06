# TRACK D — the browser gate, Phase 4

Everything below came out of a real Chromium driving a real ComfyUI that was built from
the shipped tarball. Command output is pasted, not summarised. Screenshots are in
`results/gate2/` and are the point of the document.

**Artifact actually tested:** `dist/AIOFMTech-NSFW.tar.gz`
`sha256 5f2a0f2bed3805e87aeb77d513118f6316af221dafb7da809967e146c36c5ab1`,
8 155 368 bytes, 170 files, 26 directories, top level `AIOFMTech-NSFW/`.
Hash verified **before** unpacking, and again in the preflight of every gate run.

---

## 0. Verdict

| shot the brief asked for | state |
|---|---|
| 1. workflow loaded from the workflow list, **zero red nodes**, no error dialog | **PASS** — both legs |
| 2. both LoRA stacks populated, selected through the widget's own menu, read back | **PASS** — both legs |
| 3. a **real** character prompt typed into `#106` | **PASS** — Stage 1A |
| 4. the finished image on screen | **PASS** — Stage 1B, **with the placeholder prompt** |
| 3 **and** 4 in the same run | **BLOCKED on the fix.** This is Stage 2. |

```
STAGE 1A  stage1a-realprompt-nosubmit    exit 0   status "pass-no-run"
STAGE 1B  stage1b-placeholder-render     exit 0   status "pass"
```

**The two legs are not interchangeable and must not be quoted as one.** Stage 1B put a
finished image on screen using the **shipped placeholder** in `#106`
(`"TRIGGER, PROMPT FOR YOUR MODEL"`), which is a value observed safe 3/3. The real
character description is exactly what crashes `622:403 MaskBoundingBox+` 4/4 on these
bytes, so Stage 1A stops one click before Run, by design.

> **Erratum, flagged rather than quietly patched.** Two screenshot captions inside
> `stage1b-placeholder-render-result.json` read *"the character prompt typed into…"* and
> *"carrying the typed character prompt"*. **Stage 1B did not type a character prompt —
> it typed the placeholder.** I changed those captions in `gate.js` to embed the actual
> text, but the edit landed *while Stage 1B's node process was already running*, so that
> leg kept the old generic wording. I have not rewritten the result file: patching a
> recorded artifact after the fact is how evidence stops being evidence. The record is
> self-correcting if read in place — the filename says `placeholder`, and the console
> line immediately above the screenshot reads
> `read back from the host widget : "TRIGGER, PROMPT FOR YOUR MODEL"...`. Stage 2's
> captions carry the literal text.

Otherwise every caption in `results/gate2/` carries the text that was typed, so the legs
cannot be confused by someone reading the pictures without the prose.

---

## 1. The instance, and why it is provably not someone else's

Two other agents were measuring on this pod throughout: **Track A on `18188`** and
**Track B on `28191`**. Neither was touched — no GET, no POST, no `/free`, no `/queue`,
no `pkill` of any pattern.

Track D's ports, all inside the assigned `31900-31999`, all checked dead before binding:

```
ComfyUI      31910
pack mirror  31921        (verify_buyer_path.sh WS5_MIRROR_PORT, default 38080 NOT used)
dead port    31939        (WS5_DEAD_PORT, so the installer never restarts anything)
```

The default `WS5_MIRROR_PORT=38080` and `WS5_DEAD_PORT=39997` were deliberately
overridden, because R2 §4b records two agents colliding on exactly those defaults. I
never ran `verify_buyer_path.sh nodes`, so the `28188` false-pass class cannot apply to
anything here.

The install, by the buyer's own path (`tools/browser_harness/d_setup.sh`):

```
=== artifact verification (before anything is unpacked) ===
  expected sha256 : 5f2a0f2bed3805e87aeb77d513118f6316af221dafb7da809967e146c36c5ab1
  actual   sha256 : 5f2a0f2bed3805e87aeb77d513118f6316af221dafb7da809967e146c36c5ab1
  bytes           : 8155368
  files (non-dir) : 170
  top-level       : AIOFMTech-NSFW/
=== target must not exist beforehand ===
  /workspace/comfy-d-gate does not exist: OK
  ports 31921 / 31939 are dead: OK

CASE prepare   custom_nodes entries: 0  (0 = empty, as intended)
               models entries      : 29 directories, hardlinked
CASE happy     pack sha256: 5f2a0f2bed3805e87aeb77d513118f6316af221dafb7da809967e146c36c5ab1
               profile : all   time : 1m 35s   integrity : OK   comfyui core : 0.15.1 validated
               downloaded : nothing — everything was already on disk
               comfyui : not running — nodes load on next start
               --> exit code 0 after 95s
               shared venv unchanged (pip freeze identical before/after)
```

`d_setup.sh` **refuses to run if the target directory already exists**, so "unpacked
into a directory that was empty beforehand" is enforced rather than remembered.

What landed is the artifact, not my tree:

```
$ diff -r <tarball>/AIOFMTech-NSFW /workspace/d-gate-verify/dest-happy/AIOFMTech-NSFW
  (exit 0, zero lines of output)

a811b5d6…2143d8  /workspace/comfy-d-gate/user/default/workflows/OFMTech_NSFW.json
a811b5d6…2143d8  <tarball>/AIOFMTech-NSFW/OFMTech_NSFW.json
a811b5d6…2143d8  OFMTech-NSFW/OFMTech_NSFW.json          <- the frozen repo copy
custom_nodes after: 20 packs
```

And the server the browser talked to is mine, checked on the process rather than on the
port answering:

```
$ ss -ltnp 'sport = :31910'
LISTEN 0 128 127.0.0.1:31910  users:(("python",pid=173610,…))
$ ps -o pid,ppid,args -p 173610
173610 173608 /venv/main/bin/python main.py --disable-auto-launch --disable-xformers \
              --port 31910 --listen 127.0.0.1 --enable-cors-header --reserve-vram 16
$ readlink -f /proc/173610/cwd
/workspace/comfy-d-gate
```

`d_gate.sh` re-derives all three of those in its preflight on **every** run and exits 2
if any disagrees. It does not fall back to another port; a bind or identity failure is
loud, per the brief.

**The graph was never edited.** `OFMTech-NSFW/OFMTech_NSFW.json` is untouched, and each
run re-hashes the installed copy afterwards:
`workflow on disk after the run: a811b5d6… unchanged — the browser saved nothing`.

---

## 2. Stage 1A — the real character prompt into `#106`

```
workflow        /workspace/comfy-d-gate/user/default/workflows/OFMTech_NSFW.json
                sha256 a811b5d690ccc5207bc7bd1c626cdd3db3b720b9be60d0a687436efcfd2143d8
object_info     1935 node types registered on the server
boot            19193 ms
open workflow   6909 ms   from the Workflows sidebar   title="OFMTech_NSFW - ComfyUI"
node audit      110 nodes across root + every subgraph, 59 distinct types
                frontend registered_node_types: 1952
                node types NOT registered in the frontend (= red nodes): 0
                node types absent from /object_info (excl. 7 subgraph hosts): 1
                  ABSENT   MarkdownNote
                nodes flagged has_errors: 0
                modal dialogs on screen: 0
                error toasts on screen: 0
lora            #618 SDXL stack: lora_01 = "lunaskye.safetensors"  (clicked in the widget's own menu)
lora            #116 Z-Image stack: lora_01 = "luna.safetensors"   (clicked in the widget's own menu)
face prompt     #620 as shipped: collapsed=true  (the buyer must expand it to reach #106)
face prompt     clicked the collapse box in #620's title bar; collapsed is now false
face prompt     "106: text" is a customtext DOM widget, visible=true, rect=[675,667,616,42]
                value as shipped: "TRIGGER, PROMPT FOR YOUR MODEL"
face prompt     read back from #106 CLIPTextEncode "Face Detailer Prompt" inside "5. Face & Mouth Detail (Z-Image)"
face prompt     entered via: title-button click (the UI affordance)
face prompt     entered the subgraph: isRoot=false, 13 nodes, breadcrumb=["OFMTech_NSFW","5. Face & Mouth Detail (Z-Image)"]
face prompt     back out via the breadcrumb: isRoot=true
--no-run: stopping before the Run button. Nothing was submitted.
RESULT: pass-no-run   exit 0
```

The prompt is the **byte-exact** string that crashes, lifted out of a recorded crash arm
rather than retyped from prose — `results/r4/R4_CF15_filled/api_graph.json`, key
`620:106.inputs.text`, 169 bytes,
`sha256 bd134ac03f4bbddb807e6063672fd4aa7d9f02f08fd9aff8585d4eccecb3c42b`. It lives in
`tools/browser_harness/face_prompt_real.txt` so Stage 2 cannot drift from it.

### How "zero red nodes" was decided

Not by looking. `gate.js` applies the frontend's own predicate from `loadGraphData`
(`node.type in LiteGraph.registered_node_types`) to every node at root **and inside
every subgraph**, cross-checks the same type list against the server's `/object_info`
over HTTP, and separately looks for the missing-node dialog and any error toast. All
four came back clean. This is R2's check, reused unchanged rather than rewritten.

**The walk is provably complete** — 110 nodes matches the file exactly (root 17 +
subgraph 93). `MarkdownNote` is named rather than filtered: it is frontend-only, present
in `registered_node_types`, with no server class, so it is correctly absent from
`/object_info` and is **not** red.

### How "typed into #106" was decided

`#106` is a `CLIPTextEncode` **inside** the subgraph `5. Face & Mouth Detail (Z-Image)`.
It is not on the root canvas. Three separate pieces of evidence, because a log line
saying "typed" is worth nothing:

1. the value read back out of the **promoted widget** `"106: text"` on host `#620`;
2. the value read back out of **`#106`'s own widget object** inside the subgraph
   definition — reached via `host.subgraph.nodes`, not via the host;
3. the run then **enters the subgraph** and photographs the node.

`stage1a-…-07-face-prompt-on-node-106.png` shows the breadcrumb
`OFMTech_NSFW / 5. Face & Mouth Detail (Z-Image)` and the node titled **Face Detailer
Prompt** carrying the text, legibly, at scale 1.0.

Worth flagging because it surprised me: the promoted widget and `#106`'s widget hold
equal values but are **`same_object: false`** — two objects kept in sync, not one seen
twice. That is precisely why item 2 is in the list.

---

## 3. Stage 1B — a complete render, on the placeholder

Identical journey, one field different: `#106` keeps the shipped placeholder.

```
prompt accepted HTTP 200  prompt_id=cf992629-0f77-40ee-bd0d-8f7b3ff98788  api graph 88 nodes
  selector      1 image(s); Send on open=true, after clicking #0=false, after clicking it again=true
  selector      Send pressed at 176s into the render
render          443s wall (queue included)
  output        OK   /workspace/comfy-d-gate/output/Instaraw/SDXL/Metadata/HasMetadata_00001_.png
                     11142028 B  [node 505]
RESULT: PASS   exit 0
```

### It is an image, not a status

`status: success` is not an image. Measured with
`tools/browser_harness/check_image.py`:

```
2688x3456  mean [121.72, 108.75, 95.95]  std [61.35, 57.53, 53.14]
luma_sd 58.26   flat_frac 0.2346   grey53_frac 0.001182   flat_block_frac 0.006614
largest_4bit_bucket 0.0478
-> looks like a real render
```

The tool was **calibrated against real images, and my first thresholds were wrong** —
`flat_block_frac_max = 0.02` flagged a *known-good* control. Re-set to `0.08` on three
measured points:

| image | flat_block_frac | verdict |
|---|---|---|
| R2 run 3 delivered image | 0.0066 | clean |
| Track A arm `L_w16` tap | 0.0220 | clean |
| Track A arm `A1_gate_crashstring` tap | **0.1834** | the face-shaped void |

Exit codes verified on all three: 1 / 0 / 0. A detector that never fires proves nothing,
so the negative control is part of the calibration, not decoration.

Also recorded: the crash tap's void has `grey53_frac = 0.0`. **It is not the poisoned
grey.** The face-shaped void and the NaN-poisoned flat grey are two different failures
and one metric would not catch both, which is why both are reported.

### A third instance reproduces R2 run 3 exactly

```
pixels differing : 0.0
max abs diff     : 0
mean abs diff    : 0.0
IDENTICAL PIXELS
```

My render is **pixel-identical** to R2 run 3's, from a separately built instance on a
different port at a different time under a different `prompt_id` (the 7-byte file-size
difference is embedded PNG metadata). That corroborates Track B's bit-identical finding
from a third independent install.

**This is a reported delta, not verification by hashing.** Nothing here is claimed inert
on the strength of it; the banned method is using output identity to conclude a *change*
did nothing, and no such conclusion is drawn anywhere in this document.

---

## 4. What the browser found that no API check could

### 4.1 All seven subgraph hosts ship COLLAPSED — including the one holding the face prompt

In the file, every subgraph host carries `flags: {"collapsed": true}`:

```
#621 4 · Mouth Resources        #647 1 · Canvas & Routing     #619 2 · Base Generator
#587 3 · Hands, Skin & Upscale  #620 5 · Face & Mouth Detail   #622 6 · Eyes
#623 7 · Anatomy Detail — OFF   (also #480 "Prompts loaded")
```

`HANDOFF.md` §7 sends the buyer to "sg `5 · Face & Mouth Detail`, `#106`" for the face
prompt. **On the shipped canvas that node renders as a bare title bar** — no widgets, no
enter-subgraph button (the frontend does not hit-test title buttons on a collapsed node:
`n.title_buttons?.length && !n.flags.collapsed`). The buyer must first click the small
collapse box at the top-left of the title bar. Nothing in the docs says so.
`stage1a-…-04-face-host-collapsed.png` is what they actually get;
`…-05-face-host-expanded.png` is what the docs assume.

### 4.2 `#106`'s prompt is promoted onto `#620` — and the promoted widgets are unlabelled

Once `#620` is expanded it carries four promoted widgets:

```
"165: seed"   "114: seed"   "106: text"   "105: text"
```

Good news: the buyer never has to enter the subgraph at all. Bad news, visible in
`…-05-face-host-expanded.png`: on the canvas the two seeds both draw as **`seed`** and
the two text boxes draw with **no label at all** — one pre-filled with
`TRIGGER, PROMPT FOR YOUR MODEL`, one empty. Nothing on screen says which is the face
prompt and which is the negative, or which seed is the face pass and which the mouth.

Also worth a line for whoever audits `widgets_values` desync: `#620`'s
`widgets_values` in the file is `[]` while the live host has **four** promoted widgets.

### 4.3 The workflow ships **126 Russian slot labels**, and every buyer sees them

This is the one I did not expect. Counted in the frozen file:

```
localized_name fields total : 413
   of which Cyrillic        : 126
   by subgraph:
       57  2. Base Generator (SDXL)
       22  6. Eyes (FaceMesh crop/composite)
       20  3. Hands, Skin & Second Upscale (SDXL)
        8  5. Face & Mouth Detail (Z-Image)
        7  1. Canvas & Routing
        6  4. Mouth Resources & Colour Reconcile
        6  7. Anatomy Detailers - DISABLED
```

`ИЗОБРАЖЕНИЕ` (image) ×26, `КОНДИЦИОНИРОВАНИЕ` (conditioning) ×16, `МОДЕЛЬ` ×9,
`МОДЕЛЬ_АПСКЕЙЛА` ×4, `ЛАТЕНТНЫЙ` ×5, `шумоподавление` (denoise), `сид` (seed),
`ширина`/`высота` (width/height), and so on.

**It is not a locale setting and it is not my browser.** The strings are baked into the
shipped JSON as `localized_name`, and the frontend's slot draw path prefers them:

```js
// api-gz4kgzki.js
label || e.localized_name || e.name || ``
label ?? this.localized_name ?? this.name
```

None of these slots carries a `label`, so `localized_name` wins **for every viewer
regardless of their own language**. The install ships no `comfy.settings.json` at all
(`tar -tzf` finds nothing under `user/`), so there is no locale to blame. Someone built
this graph on a Russian-locale ComfyUI and the auto-generated slot names were saved with
it.

Visible in `stage1a-…-05-face-host-expanded.png` (`#620`'s outputs read
`ИЗОБРАЖЕНИЕ / МОДЕЛЬ / CLIP / VAE / ИЗОБРАЖЕНИЕ_1 / image`) and again in
`…-07-face-prompt-on-node-106.png`. Note the mixture: `CLIP` and `VAE` have no
translation entry so they stay English, which is why the result reads as broken rather
than as a translated product.

**An API check is structurally incapable of seeing this** — `localized_name` never
reaches the API graph, and `/object_info` has nothing to do with it. It is a pure
frontend display field in the workflow file.

### 4.4 The buyer's first screen is a modal — R2 §5.1 confirmed on a third install

Neither gate run saw it, and I nearly wrote that up as a correction to R2. It is not
one. My own probe scripts had already consumed the first-ever browser load. Tested
directly instead of argued (`results/gate2/firstrun-templates-modal.png`):

| | state | dialogs |
|---|---|---|
| A | settings present, `Comfy.TutorialCompleted: true` | 0 |
| B | `comfy.settings.json` removed | **1 — "Templates / All Templates / Popular"** |
| C | immediately after B | 0, and `TutorialCompleted` written back |

The modal covers the left toolbar, so the Workflows tab is unreachable until it is
closed. Not ours, not a defect, but it is the first thing a buyer sees and it is in no
document of ours. Full write-up of how I nearly got this wrong: `notes/D-questions.md` §8.

### 4.5 Seven 404s on a clean install's first open — still present in `5f2a0f2b…`

`page errors     15 during boot, 7 after the workflow was opened` — six stale
`rgthree.compare._temp_*` fetches plus the benign workflow index. Same as R2 §5.4, now
observed on a third clean install. Unfixed in the shipping artifact.

### 4.6 The single-image selector opens with Send already enabled

```
selector  1 image(s); Send on open=true, after clicking #0=false, after clicking it again=true
```

Reproduces R2 §5.2 exactly: `popup.js:517-518` pre-picks image 0 when there is exactly
one, and `select_unselect()` toggles, so a click *deselects*. The button tracks
`picked.size` in both directions. Confirms the fix rather than contradicting it.

---

## 4b. The Stage 2 command was run on the **unfixed** bytes — and it did not crash

I ran `d_gate.sh stage2` before any fix existed, to prove the one-command path works
rather than hand over an untested one-liner. It works. It also produced a result I did
not expect and which needs stating carefully.

**With the byte-exact crashing string in `#106`, on the shipped artifact, in a browser,
the render completed and delivered a correct face.**

```
prompt_id 7cb9e814-775b-4cf6-b58a-af8d19b950e7
status success   193 s   HasMetadata_00002_.png  11,142,044 B   exit 0
```

Everything that could make this a false green was checked:

| what could be wrong | check | result |
|---|---|---|
| the browser sent a different string | sha256 of `620:106.inputs.text` in the POSTed api_graph | `bd134ac0…c42b` — **matches** the recorded crash arm exactly, 169 bytes |
| the LoRAs were not loaded | api_graph | `luna.safetensors` + `lunaskye.safetensors` |
| the face pass was served from cache | `/history` `execution_cached` | `620:106`, `620:114`, `620:165`, `621:163`, `622:424`, **`622:403`** all `cached=False` |
| it was a different graph config | api_graph | `620:114` steps 8, cfg 1, denoise 0.80, `bbox_crop_factor` 1.5 — the shipping values |
| the image is the silent void | `check_image.py` | `flat_block_frac 0.0071` vs clean control `0.0066`, void `0.1834` |

32 of 88 nodes executed. The 56 cached ones are all **upstream of the selector `#603`**;
because `#603` cannot be cached, the whole chain below it re-ran — `587:92`, `587:98`
(UltimateSDUpscale), the face pass, the mouth pass, the colormatch and all 15 Eyes-stage
nodes including `622:403` itself.

**And it is a real face, localised.** Against the placeholder render the difference is
confined to a **290×386 px box at x 837-1127, y 326-712 — 1.20 % of the frame**, which
is the head. That crop has `luma_sd 37.23` and **38 760 unique colours**; a void has one.
`results/gate2/stage2-realprompt-FACE-CROP.png` and
`stage1b-placeholder-FACE-CROP.png` are both written out at 1:1.

> **A correction to my own commit message.** `282ac07` says the crop "shows the freckles
> the prompt asked for". **That implies causation I have not shown** — the *placeholder*
> crop has freckles too, so they are the LoRA's, not the prompt's. What the crop shows is
> a detailed, correct face. Nothing more should be read into it.

### What this is NOT

**It is not a refutation of `HANDOFF.md` §6.0's 4/4.** It is one trial. Taken with the
existing record it says the crash is **state-dependent, not deterministic on the
prompt** — which is what Track A's non-monotone ladder (`w19`/`w20` clean past a
"crashing" length) and Track B's independent VRAM route already say. My run adds a
browser-level data point to that picture; it does not overturn a documented 4/4.

Two conditions of my run differ from every documented crash arm and either could matter:

1. **The SDXL base was cached.** Every crash arm ran cold (`execution_cached: []`).
2. **VRAM.** My instance logged
   `Unloaded partially: 7558.29 MB freed … lowvram patches: 128` during this very run —
   *higher* patching than the `83` in Track B's crashing D2 example — and it still
   rendered clean. Read against Track B's finding that is an observation, not a
   refutation: they have a controlled arm, I have one log line. But it does suggest
   lowvram patching alone is not sufficient to cause the crash. **Note the patching
   happened in the upscale stage, not the face stage** — I misread that at first and
   checked the log context rather than leaving it inferred.

**The decisive follow-up is a cold run**, which removes difference 1. Result in §4c.
The warm run's artifacts are preserved separately under
`results/gate2/stage2-warmcache-run/` so the two can never be conflated.

**What the owner should take from this:** do not treat "the crash string" as a reliable
reproducer. Anyone testing the fix needs *n* trials from a known cache and VRAM state,
not one, or they will conclude the fix worked when the dice simply landed differently.

---

## 5. What this does NOT prove

* **That a real prompt renders.** That is Stage 2 and it is blocked. Stage 1B's finished
  image was produced by the **placeholder**.
* **Image quality.** Not my call and not measured. `check_image.py` answers "is this an
  image or a flat fill", nothing more.
* **A buyer's machine.** The clean install is genuinely clean in `custom_nodes` (0 → 20)
  and in `user/`, but shares the pod's venv, driver and model tree.
* **A cold model pull.** `models/` was hardlinked; the installer verified instead of
  downloading 178 GB.
* **Timings.** Tracks A and B were on the GPU throughout. 443 s is not comparable with
  anything in `HANDOFF.md` §4 and I have not quoted it as a measurement.
* **The multi-image selector path.** This render produced one image.
* **That a buyer can download these bytes.** Per R2 §0, live HF is `3f6d0f2f…`, two cuts
  behind. Nothing tested here is published.

---

## 6. Stage 2 — the run that actually counts

**One command.** It re-runs the identical journey with the identical prompt bytes:

```bash
bash /workspace/nsfw-fix/tools/browser_harness/d_gate.sh stage2
```

That is the whole thing. It will, in order: re-verify the artifact hash against
`5f2a0f2b…`; re-verify the installed workflow against `a811b5d6…`; confirm `31910` is
Track D's own ComfyUI by pid, argv and cwd and **exit 2 loudly** rather than probe
anything else; load the workflow from the sidebar; audit all 110 nodes for red;
set both LoRA stacks through the widget menus; expand `#620`, type
`face_prompt_real.txt` into `#106` and read it back from inside the subgraph; press Run;
answer the selector; wait for the image; and then measure that image for the flat-grey
failure, **demoting a green gate to a failure if the image is flat**.

Exit codes are honest and unchanged: `0` pass · `1` the workflow is broken · `2` it
could not be run.

### Preconditions

1. **The instance must be up.** If `31910` is gone (pod restart, or someone stopped it):
   ```bash
   cd /workspace/comfy-d-gate && nohup /venv/main/bin/python main.py \
       --disable-auto-launch --disable-xformers --port 31910 --listen 127.0.0.1 \
       --enable-cors-header --reserve-vram 16 > /workspace/d-gate-verify/comfy-31910.log 2>&1 &
   ```
   If `/workspace/comfy-d-gate` itself is gone, rebuild it first — this also refuses to
   run unless the target directory is absent, so delete it deliberately:
   ```bash
   bash /workspace/nsfw-fix/tools/browser_harness/d_setup.sh
   ```
2. **If the tarball is re-cut, this gate stops covering it.** `d_gate.sh` will exit 2
   rather than silently test the wrong bytes. Update `EXPECT_ARTIFACT` /
   `EXPECT_WORKFLOW` in `d_gate.sh` and re-run `d_setup.sh` from scratch.
3. **A NaN can poison the server** (`HANDOFF.md` §6.1). If a run has crashed on this
   instance beforehand, clear it and re-confirm with something that already worked:
   ```bash
   curl -s -X POST 127.0.0.1:31910/free -H 'Content-Type: application/json' \
        -d '{"unload_models":true,"free_memory":true}'
   bash /workspace/nsfw-fix/tools/browser_harness/d_gate.sh stage1b   # must still pass
   ```
   Only `31910`. `18188` and `28191` are other agents'.
4. **Do not press Run and walk away** — `#603` pauses for a human and times out at
   600 s, sending nothing. `d_gate.sh` answers it automatically.

### What a Stage 2 pass looks like

`exit 0`, a `stage2-realprompt-render-result.json` with `status: "pass"` and
`failures: []`, a `stage2-realprompt-render-image_check.json` whose verdict is
`looks like a real render`, and
`stage2-realprompt-render-*-final-image-on-canvas.png` showing an image on `#505`.

### What a Stage 2 failure looks like, and what it means

* `execution` failure naming **`622:403 MaskBoundingBox+`** → the fix did not take. Same
  crash, same node.
* `exit 0` from `gate.js` but the image check fires → the crash became a *silent* flat
  face instead of an exception. **That is worse, not better**, and it is exactly why the
  image check demotes it.
* `exit 2` → the gate could not run. Not a pass. Read the preflight lines.

### Re-running Stage 1 alongside it

```bash
bash /workspace/nsfw-fix/tools/browser_harness/d_gate.sh stage1a   # real prompt, no submit
bash /workspace/nsfw-fix/tools/browser_harness/d_gate.sh stage1b   # placeholder, full render
```
`stage1b` is the control: if it stops passing, the instrument moved, not the fix.

---

## 7. Files

| what | where |
|---|---|
| screenshots + machine-readable results | `results/gate2/` |
| Stage 1A verdict | `results/gate2/stage1a-realprompt-nosubmit-result.json` |
| Stage 1B verdict | `results/gate2/stage1b-placeholder-render-result.json` |
| Stage 1B image measurement | `results/gate2/stage1b-placeholder-render-image_check.json` |
| the API graph the browser POSTed | `results/gate2/stage1b-placeholder-render-api_graph.json` |
| the runner | `tools/browser_harness/d_gate.sh` |
| the install | `tools/browser_harness/d_setup.sh` |
| the journey + screenshots | `tools/browser_harness/gate.js` (R2's, extended for `#106`) |
| flat-grey detector | `tools/browser_harness/check_image.py` |
| the exact prompts | `tools/browser_harness/face_prompt_{real,placeholder}.txt` |
| judgement calls | `notes/D-questions.md` |

`gate.js` changes are additive: a `useCurrentGraph` argument on `FRAME_FN` that defaults
to the old behaviour, and a `--face-prompt` leg that is skipped entirely when the option
is absent. Every pre-existing call site is unchanged in effect, so R2's legs still run.
