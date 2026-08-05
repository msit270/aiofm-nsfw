Read STATE.md first. The other .md files in this folder were
written before a long session whose work is not reflected in
them. STATE.md records what changed.

The only authoritative copies of the workflow, setup script and
ComfyUI_INSTARAW are under OFMTech-NSFW/, extracted from the
published tarball.

# AIOFM NSFW — Sandbox

A ComfyUI image pipeline for NSFW character generation. **132 nodes** across
seven subgraphs, roughly three times the size of the sibling video workflow,
and almost entirely undocumented.

This is a sandbox. Nothing here reaches a customer without passing through me
first. It will eventually be packaged and sold alongside the video pipeline,
but the first job is understanding it, not shipping it.

**Take big swings.** This graph has accumulated years of half-finished
experiments and I would rather you propose tearing something out than tidy
around it.

---

## Your environment — read this first

**You are running on a local machine. There is no ComfyUI here, no models,
and no GPU.** You cannot install packs, run the graph, render, or measure
anything.

That is deliberate. This session is for the work that does not need a GPU, and
that is more of the job than it sounds — mapping the graph, naming the stages,
finding the dead paths, resolving node repos, reading the INSTARAW source.

Where something genuinely needs a running graph, **write down what you would
test and exactly how, in `PROPOSALS.md`, and move on.** A later session on a
rented pod will execute those. A precise, ordered list of experiments is a real
deliverable — treat it as one, not as a footnote.

Do not simulate, guess at, or estimate anything that would need a render. If
you cannot know it here, say so plainly.

---

## The prime directive

**Never state as fact anything you have not read in the file.**

Static inspection has missed every real regression in this project's history —
that is exactly why the runtime half of this work is deferred rather than
faked. So the standard here is: every claim traceable to a node id, a link, or
a line of source. Where you are inferring, label it as inference.

### One method that is banned outright

On the sibling pipeline, verifying changes by hashing rendered output produced
**three separate confident wrong conclusions**, and the last survived five
agreeing renders before a sixth disagreed. Run-to-run noise sits around 48.7 dB
— below one 8-bit level — so matching hashes are a strong attractor, not proof.

When you propose a verification method in `PROPOSALS.md`, do not propose
hashing output. The method that works is a **graph diff**: convert before and
after to API format, constant-fold any switch or bypass chains, compare every
node on every input. Zero differences proves a change is inert. That needs no
GPU and you can specify it precisely from here.

### You cannot judge image quality

Not here, and not on a pod either. For anything that alters output, the
deliverable is the A/B pair plus objective deltas. I look at the images.

---

## What is already known about this graph

I ran a structural pass. Take this as a starting map, not gospel — correct
anything you find wrong, and say so when you do.

### The seven stages are all named "Dont touch!!!"

That is the core problem. You cannot reason about a graph where every stage has
the same name, and neither can a buyer. **Naming them correctly is the whole
point of this session.**

My hypothesis from node types and wiring, to be confirmed or corrected:

| subgraph | nodes | bypassed | looks like |
|---|---|---|---|
| sg6 | 22 | 13 | inputs, latent, width/height, ControlNet + IPAdapter + depth (all dead), branding |
| sg1 | 28 | 0 | the main generator — SDXL checkpoint, KSampler + KSamplerAdvanced, PAG, prompts, image filter |
| sg2 | 12 | 0 | face + mouth detail — second model family (UNET/CLIP/VAE), colormatch |
| sg3 | 5 | 0 | mouth prompts and detector loaders, feeding sg2 |
| sg4 | 21 | 0 | eyes — MediaPipe FaceMesh, face crop, composite back |
| sg0 | 15 | 0 | hands + final upscale — HandDetailer, UltimateSDUpscale, ImageBlend |
| sg5 | 11 | **11** | anatomy detailers (pussy, nipples, breasts) — entirely dead |

Likely run order: sg6 → sg1 → sg3/sg2 → sg4 → sg0.

sg3 is only five nodes and exists to feed sg2. Ask whether it should be a stage
at all.

### Known defects

**The entry node is unconnected.** `INSTARAW_RealityPromptGenerator` is
execution order 0 with all five image inputs (`images`, `images2`, `images3`,
`images4`, `character_image`) unlinked and empty widget values. Either that is
the bug, or it is fed some other way. The INSTARAW source is in this folder —
read it and work out what that node expects.

**A third of the graph is switched off.** 24 bypassed nodes. sg5 is dead in
full. sg6 has the whole ControlNet + IPAdapter + DepthAnythingV2 path dead,
plus `INSTARAW_BrandingNode` ("Powered by 🍑"). Each needs a verdict with
reasoning: revive, or delete.

**Loaders are duplicated across stages.** Seven `UltralyticsDetectorProvider`,
four `SAMLoader`, four `UpscaleModelLoader`. Work out which load the same file
and whether they can share.

**Two model families run in one graph.** sg1 uses `CheckpointLoaderSimple`
(SDXL); sg2 uses `UNETLoader` + `CLIPLoader` + `VAELoader`. Both resident means
both in memory. Understand why before proposing a change — it may be
deliberate.

**Seven rgthree Image Comparer nodes**, four at root. Development
instrumentation, not product.

---

## Custom nodes this graph needs

The setup script's `NODE_REPOS` covers the video pipeline only. This graph also
requires, and **none of these are in the script**:

- **Impact Pack** — `FaceDetailer`, `FaceDetailerPipe`, `UltralyticsDetectorProvider`, `SAMLoader`, `ToDetailerPipeSDXL`, `DetailerPipeToBasicPipe`, `DetailerForEachDebug`, `BboxDetectorSEGS`, `MaskToSEGS`, `SegsToCombinedMask`
- **comfyui_controlnet_aux** — `MediaPipe-FaceMeshPreprocessor`, `MediaPipeFaceMeshToSEGS`, `DepthAnythingV2Preprocessor`
- **ComfyUI_IPAdapter_plus** — `IPAdapter`, `IPAdapterUnifiedLoader`
- **ComfyUI_essentials** — `ImageColorMatch+`, `MaskBoundingBox+`, `ImageResize+`
- **UltimateSDUpscale**
- **ComfyUI_INSTARAW** — our own pack, in this folder

Resolve each repo from the workflow's own `cnr_id` / `aux_id` fields through
`api.comfy.org/nodes/<cnr_id>`, and confirm the repo still exports the node
names this graph uses. **Do not guess a URL.** You have web access; use it.

You cannot verify a pin by installing it here, so pin the commit you can
justify and record why in your report. The pod session will confirm.

---

## Traps carried over from the video graph

Every one has already cost real time on the sibling pipeline. This graph is
built the same way, so assume they are present until you have checked.

**`widgets_values` on a subgraph host covers only the widget-typed entries of
`inputs`, skipping pure-link ones.** Adding or removing a promoted widget
shifts everything after it. This silently fed a colormatch string into a
`face_strength` float. **This is the single highest-value thing to audit in
this file** — with seven hosts and 132 nodes, a desync here would be invisible
and would explain output nobody can account for.

**Wired inputs silently override widget values.** Width/Height widgets read
832x480 while the graph rendered 720x1280. **Always check whether a slot has a
link before trusting its widget.**

**Promoting `seed` drags its synthetic `control_after_generate` companion**,
desyncing `widgets_values` on that host.

**`ImageResizeKJv2`** throws "Lanczos is not supported on the GPU" when device
is gpu and upscale_method is lanczos.

**`DrawMaskOnImage`** widget order is color / opacity / device; device defaults
to cpu when absent from the file.

**`DownloadAndLoadSAM2Model` does not load the filename on its widget** — at
precision fp16 with a "2.1" model it rewrites the name to add `-fp16`. Fetching
the displayed name downloads a file that is never read and still leaves a
mid-render download.

---

## What I want from this session

### 1. `MAP.md` — the deliverable

The first true description of this pipeline. Name each of the seven stages for
what it actually does. For each: what it takes in, what it puts out, which
stage feeds it, which it feeds, and the node ids so I can find things.

Include the dead paths, marked as dead. Include what you are unsure about,
marked as unsure.

There is no accurate documentation for this graph anywhere. A guide video
exists from an earlier version and the workflow has drifted far enough that it
no longer matches. Assume nothing written about this pipeline is current,
**including the notes inside the file itself** — on the sibling pipeline, three
of five documented claims turned out to be false and two of those would crash a
user with correct hardware.

### 2. `AUDIT.md` — everything wrong with it

Widget desyncs. Wired inputs overriding widgets. Version mismatches implied by
the node metadata. Redundant VAE round-trips. Duplicate loaders. Dead paths
still costing load time. Anything that looks like a bug, whether or not you can
prove it without running.

Rank by how much it would matter if true.

### 3. `PROPOSALS.md` — the pod session's task list

Everything that needs a GPU, written so precisely that the next session can
execute it without re-deriving anything. For each: what changes, what you
expect, how to measure it, and what result would kill the idea.

Be ambitious. Speed, memory, quality, architecture. Whether five separate
detailer passes is right or whether some do nothing. Whether both model
families need to be resident. I want ideas I have not had.

### 4. `SETUP.md` — what packaging it will take

The node packs with resolved repos and proposed pins. The models from INSTALL
MODELS reconciled against what the setup script already fetches. What is
missing. Where `ComfyUI_INSTARAW` needs to go.

---

## How to work

- Git branch. One commit per change, so anything can be reverted individually.
- Do not edit the workflow JSON in this session unless a change is provably
  inert. Understanding first. If you do edit, one change per commit with the
  reasoning in the message.
- Work continuously. Do not stop to ask me questions — write them to
  `QUESTIONS.md` with your best guess and your reasoning, take the lower-risk
  option, and move on.
- Audit your own claims before reporting them. On the sibling pipeline every
  correction came from **comparing against something** — a control, a clean
  run, the delivered file — and none came from thinking harder. Here your only
  control is the file itself, so quote it.
- Flag uncertainty rather than resolving it silently. An honest "I am not sure
  this is right" is worth more than a confident summary I have to go verify
  myself.
