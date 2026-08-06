# MAIN-findings.md — established by the orchestrating session, before/alongside the workstreams

Everything here was read out of a file or observed in command output on this pod
on 2026-08-05. Inferences are labelled. This is raw material for the next
`STATE.md`; it is not itself the handoff document.

---

## 1. The environment described in CLAUDE.md is not the environment

`CLAUDE.md` asserted: *"You are running on a local machine. There is no ComfyUI
here, no models, and no GPU."*

Observed on this pod:

| Claim | Reality |
|---|---|
| no GPU | `nvidia-smi -L` → `NVIDIA RTX PRO 6000 Blackwell Max-Q`, 96 GB VRAM |
| no ComfyUI | ComfyUI **0.15.1 running**, PID 8584, `127.0.0.1:18188`, args `--disable-auto-launch --disable-xformers --port 18188 --enable-cors-header` |
| no models | ~178 GB under `/workspace/ComfyUI/models` (checkpoints 6.5 G, loras 13 G, text_encoders 34 G, diffusion_models 119 G) |
| — | 384 CPU, 1.13 TB RAM, ~224 GB free disk, `comfyui-frontend-package` 1.39.19 |

Corrected in commit `31303bf` by making the section conditional with three
commands that settle it, rather than deleting it — the GPU-less local machine it
was written for is still a real configuration.

**Why this mattered enough to fix:** left as-is it instructs a future session to
defer all render work to `PROPOSALS.md`. That is the same failure mode that let
the browser blocker ship — a claim about the environment that nobody re-checked.

### Caveat on this pod as a test bed

`/workspace/ComfyUI/custom_nodes` holds **23 entries**, including the video
pipeline's packs (`ComfyUI-KJNodes`, `ComfyUI-WanVideoWrapper`,
`ComfyUI-Frame-Interpolation`, `ComfyUI-VideoHelperSuite`,
`ComfyUI-segment-anything-2`, `ComfyUI_Swwan`, `ofmtechclip`, `ComfyMath`,
`ComfyUI-Easy-Use`, `ComfyUI-Custom-Scripts`, `comfyui-propost`,
`ComfyUI-Manager`). **This is not the "fresh pod with only the NSFW pack"
configuration the blocker was reported against.** Anything proved here about
pack interaction does not transfer to a buyer's install; only the
empty-ComfyUI verification does.

---

## 2. Source-of-truth check — the three copies agree

    10b1a6676e5444a15e48d1ed260ca1373a4f39e9ea045f7605d334da9153fa72  nsfw-fix/OFMTech-NSFW/OFMTech_NSFW.json
    10b1a6676e5444a15e48d1ed260ca1373a4f39e9ea045f7605d334da9153fa72  /workspace/OFMTech-NSFW/OFMTech_NSFW.json      (stale dup)
    10b1a6676e5444a15e48d1ed260ca1373a4f39e9ea045f7605d334da9153fa72  /workspace/ComfyUI/user/default/workflows/OFMTech_NSFW.json

    63123c2f532bc3a425df94bec976b7e9f35ce83c07c19be5b4a3f5f766cf682e  both copies of aiofm_setup.sh

`diff -rq` of the repo `ComfyUI_INSTARAW` against the installed one differs only
by `__pycache__` directories. `dist/AIOFMTech-NSFW.tar.gz` is sha256
`3f6d0f2f…aada76`, matching what STATE.md records as published.

So at the start of this run the repo, the stale duplicate and the live install
were all the same bytes. Drift is not a confounder for anything measured here.

---

## 3. The blocker: what node 647 is, and why it throws

**`#647` is the root-level subgraph host** for definition
`9050d895-4e70-44f5-9c2b-57e2be7df0ec`, name `"1. Canvas & Routing"`, host title
`"1 · Canvas & Routing  (output size)"`. Its outputs in order:

| slot | name | type | root links |
|---|---|---|---|
| 0 | `output` | LATENT | 1503 |
| 1 | `FLOAT` | FLOAT | 1504 |
| 2 | `positive` | CONDITIONING | 1505 |
| 3 | `negative` | CONDITIONING | 1506 |
| **4** | **`MODEL`** | MODEL | 1507, 1508 |

Slot 4 is named `MODEL`, matching `No output node found for id [647] slot [4]
MODEL` exactly.

**The throw site**, from the shipped sourcemap
`/venv/main/lib/python3.12/site-packages/comfyui_frontend_package/static/assets/api-gz4kgzki.js.map`,
original source `src/lib/litegraph/src/subgraph/ExecutableNodeDTO.ts`, method
`_resolveSubgraphOutput`:

```ts
const innerResolved = node.resolveSubgraphOutputLink(slot)
if (!innerResolved) return
const innerNode = innerResolved.outputNode
if (!innerNode)
  throw new Error(`No output node found for id [${this.id}] slot [${slot}] ${output.name}`)
```

and `src/lib/litegraph/src/subgraph/SubgraphNode.ts`:

```ts
resolveSubgraphOutputLink(slot) {
  const outputSlot = this.subgraph.outputNode.slots[slot]
  const innerLink = outputSlot.getLinks().at(0)
  if (innerLink) return innerLink.resolve(this.subgraph)
  console.warn(...)
}
```

**The cause.** Inside `"1. Canvas & Routing"` three links go straight from the
subgraph input sentinel `-10` to the subgraph output sentinel `-20`, with no node
between:

```
{id:1495, origin_id:-10, origin_slot:1, target_id:-20, target_slot:2, type:'CONDITIONING'}  positive -> positive
{id:1496, origin_id:-10, origin_slot:2, target_id:-20, target_slot:3, type:'CONDITIONING'}  negative -> negative
{id:1497, origin_id:-10, origin_slot:3, target_id:-20, target_slot:4, type:'MODEL'}         model    -> MODEL
```

**This is the only subgraph in the file containing `-10 -> -20` links** — all
seven were scanned.

The precise mechanism, read from `src/lib/litegraph/src/LLink.ts` in the same
sourcemap (my first reading of this was wrong — see below):

```ts
resolve(network: BasicReadonlyNetwork): ResolvedConnection {
  const inputNode = this.target_id === -1 ? undefined : (network.getNodeById(this.target_id) ?? undefined)
  const input = inputNode?.inputs[this.target_slot]
  const subgraphInput = this.originIsIoNode ? network.inputNode?.slots[this.origin_slot] : undefined
  if (subgraphInput) {
    return { inputNode, input, subgraphInput, link: this }   // <-- no outputNode key at all
  }

  const outputNode = this.origin_id === -1 ? undefined : (network.getNodeById(this.origin_id) ?? undefined)
  const output = outputNode?.outputs[this.origin_slot]
  const subgraphOutput = this.targetIsIoNode ? network.outputNode?.slots[this.target_slot] : undefined
  if (subgraphOutput) {
    return { outputNode, output, subgraphInput: undefined, subgraphOutput, link: this }
  }
  ...
}
```

and the two getters, whose sentinel values I read out of the **shipped minified
bundle** rather than inferring them, because the sourcemap has no literal:

    originIsIoNode(){return this.origin_id===-10}
    targetIsIoNode(){return this.target_id===-20}

Link 1497 satisfies **both** predicates. `resolve()` tests the input side first,
`subgraphInput` is truthy, and it **returns early with an object literal that has
no `outputNode` property**. `_resolveSubgraphOutput` then reads
`innerResolved.outputNode`, gets `undefined`, and throws.

So the real defect is narrower and more interesting than "node -10 does not
exist": **a link that is simultaneously `originIsIoNode` and `targetIsIoNode` can
never reach the `subgraphOutput` branch**, because the `subgraphInput` branch
returns first. A direct subgraph-input → subgraph-output connection is
unrepresentable in `ResolvedConnection`. The `getNodeById(this.origin_id)` line
is never executed for these links, and note it guards against `-1`, not `-10`, so
it would have returned `undefined` there too — same outcome, different route.

**Correction to my own earlier claim in this file:** I first wrote that
`getNodeById(-10)` is called and returns undefined. That was inference stated as
fact, and it was wrong on the path taken. Corrected above from the source. The
consequence for the fix is unchanged — the passthrough must go — but the
explanation in any shipped report should be the branch-order one.

### How it got there — the origin story

`MAP.md` §4 describes this same subgraph *before* the destroyed-pod session, when
it had 22 nodes, 13 bypassed. Lines 171–175:

> - `#638` bypassed → `positive`/`negative` pass straight from sg6's inputs to its outputs …
> - `#644`→`#643` bypassed → `MODEL` passes from sg6's `model` input to its output …

So those three connections **used to run through real (bypassed) nodes**, which
is the supported path — `ExecutableNodeDTO` resolves a bypassed node via
`_getBypassSlotIndex` then `resolveInput`, which handles `origin_id: -10`
correctly. **[I]** When the dead ControlNet + IPAdapter + depth path was deleted
on the destroyed pod, the editor reconnected the severed wires input-to-output
directly, producing links litegraph will draw but cannot flatten.

**The blocker is a regression introduced by that cleanup, not a long-standing
latent defect.** The same edit explains the now-dead `vae` input on `#647`:
`MAP.md` §4 shows `#631 VAEEncode` was its only consumer, and `#631` was deleted.

It also fixed something: `AUDIT.md` A2 described the `FLOAT` output coming from a
**bypassed** `#637 PrimitiveFloat` (0.5) with nothing to pass through. It now
comes from `#627 PrimitiveFloat` = 1, not bypassed. The cleanup fixed A2 and
created the blocker in the same stroke.

### Why the passthroughs are load-bearing, and why the obvious fix is wrong

The root graph is a host-level **cycle** between `#647` and `#619`
("2. Base Generator (SDXL)"):

```
619.out[0] CONDITIONING   --1500-->  647.in[1] positive
619.out[2] CONDITIONING_1 --1501-->  647.in[2] negative
619.out[5] VAE            --1499-->  647.in[0] vae      (dead inside)
618 LoraStack.MODEL       --1502-->  647.in[3] model
647.out[0] LATENT         --1503-->  619.in[3] latent_image
647.out[1] FLOAT          --1504-->  619.in[5] denoise
647.out[2] positive       --1505-->  619.in[1] positive
647.out[3] negative       --1506-->  619.in[2] negative
647.out[4] MODEL          --1507-->  587.in[4] model
647.out[4] MODEL          --1508-->  619.in[8] model
```

`positive` and `negative` are therefore **self-loops on `#619`, laundered through
`#647`**. Inside sg1, output slot 0 comes from `#599` "PURE POSITIVE" (link 1275)
and input slot 1 goes to `#592 KSampler.positive` (1266) and
`#617 UltimateSDUpscale.positive` (1267). Flattened, the whole excursion is just
`#599 → #592.positive` and `#599 → #617.positive`, both inside the same subgraph.
Negative is identical via `#606`.

Consequence: "rewire the root consumer straight to whatever feeds 647's input"
would create a direct `619 → 619` edge. The correct repair is to make the
connection *inside* sg1 and delete the IO slots — i.e. finish the interrupted
cleanup. `MODEL` is the exception: plain fan-out from `#618`, safe to wire
directly to `#587.in[4]` and `#619.in[8]`.

---

## 3b. The newer frontend the file was authored on has the identical defect

`OFMTech_NSFW.json` carries `extra.frontendVersion: "1.41.20"` while ComfyUI
0.15.1 pins **1.39.19**. That raised a competing explanation for why the author
never saw the error: perhaps their newer editor resolved these links fine.

**It does not.** I downloaded `comfyui-frontend-package==1.41.20` from PyPI and
compared the original TypeScript sources out of both wheels' sourcemaps:

| source file | 1.39.19 sha256[:16] | 1.41.20 sha256[:16] | identical |
|---|---|---|---|
| `litegraph/src/LLink.ts` | `65f981e1d43a72ae` | `65f981e1d43a72ae` | **yes** (15,505 B both) |
| `litegraph/src/subgraph/ExecutableNodeDTO.ts` | `4b0b9c68c4f83953` | `b8dd5ebf3ccec49b` | no (13,909 → 13,999 B) |
| `litegraph/src/subgraph/SubgraphNode.ts` | `f6a819d9a4d8d31c` | `7d597d3a975b08cd` | no (20,780 → 44,188 B) |

`LLink.resolve` — the function whose branch order causes the throw — is
**byte-identical between the two versions**. And `ExecutableNodeDTO.ts`, although
it changed slightly, still contains the same throw reached the same way:

```ts
const innerResolved = node.resolveSubgraphOutputLink(slot)
if (!innerResolved) return

const innerNode = innerResolved.outputNode
if (!innerNode)
  throw new Error(
    `No output node found for id [${this.id}] slot [${slot}] ${output.name}`
  )
```

**Consequences.**
1. The author would have hit this error too, had they pressed Run in a browser on
   the machine that saved the file. Frontend version is **not** why it went
   unseen — which leaves the API-harness explanation (§4) as the only one
   standing. This is corroboration by elimination, and it is the kind this
   project keeps needing: a competing hypothesis killed by comparing against
   something rather than by thinking harder.
2. **Upgrading the frontend is not a fix**, and would not have been. Removing the
   construct, as WS1 did, is the only available repair.
3. The residual recurrence risk is narrower than feared: not "a newer editor
   spontaneously emits these", but "deleting a node that sits between a subgraph
   input and output may reconnect them directly". That is an editing hazard to
   document, not a version trap. I did not drive 1.41.20's UI to confirm the
   deletion behaviour — **unverified**.

---

## 4. Why no test caught it — server side, checked independently of WS1

`server.py:889` takes `prompt = json_data["prompt"]` and passes it to
`execution.validate_prompt` at `:898`. Nothing reads `definitions`.

`grep -rn "definitions" --include=*.py` over core (excluding `custom_nodes`)
returns only unrelated hits plus `blueprints/.glsl/update_blueprints.py`, a build
script. The `subgraph` hits in `execution.py:337-403` are **runtime node
expansion** (`GraphBuilder`, a node returning a new graph mid-execution) — an
unrelated mechanism. `app/subgraph_manager.py` is a catalogue that serves
subgraph blueprint files from custom nodes and templates to the browser.

**Nothing server-side flattens `definitions.subgraphs`.** UI-graph → API-format
conversion happens only in the browser, so a harness that POSTs an API graph to
`/prompt` cannot exercise it. The STATE.md hypothesis holds on the evidence I
gathered; WS1 owns the confirmed verdict.

---

## 5. The graph has moved a long way from the older docs

Current file: **109 nodes**, **exactly one bypassed** (root `#623`, the host for
"7. Anatomy Detailers - DISABLED"), zero muted.

`CLAUDE.md` describes 132 nodes and 24 bypassed. `MAP.md` §0 confirms "132 nodes
total, 24 bypassed, 0 muted **[F]**". Both are now stale.

A search of every node in root and all seven subgraph definitions for types
matching ControlNet / IPAdapter / Depth / Branding / LatentSwitch / SetUnion
returns **zero matches**. `#638`, `#639`, `#641`, `#645 INSTARAW_BrandingNode`,
`#636 INSTARAW_LatentSwitch`, `#630/#631` no longer exist.

Node counts per stage as they stand:

| subgraph | nodes | bypassed |
|---|---|---|
| 1. Canvas & Routing | 4 | 0 |
| 2. Base Generator (SDXL) | 28 | 0 |
| 3. Hands, Skin & Second Upscale (SDXL) | 14 | 0 |
| 4. Mouth Resources & Colour Reconcile | 5 | 0 |
| 5. Face & Mouth Detail (Z-Image) | 12 | 0 |
| 6. Eyes (FaceMesh crop/composite) | 18 | 0 |
| 7. Anatomy Detailers - DISABLED | 11 | 0 |
| ROOT | 17 | 1 (`#623`) |

The seven stages **have already been renamed** — they are no longer all called
"Dont touch!!!". The names match `MAP.md` §2's proposals, with numeric prefixes.
Three `MarkdownNote` nodes (`#649`, `#650`, `#651`) now carry buyer-facing
instructions at root.

**Consequences for STATE.md's "still NOT fixed" list:** two of the five entries
look already resolved. The ControlNet mis-wire has no nodes left to mis-wire, and
`#600 KSamplerAdvanced` reads `control_after_generate: "fixed"` where `AUDIT.md`
A21 recorded `"randomize"`. WS4 owns the verdict on both.

---

## 6. Structural residue worth a verdict

Subgraph IO slots whose `linkIds` name links that do not exist in that
subgraph's `links` array:

| subgraph | slot | linkIds | missing |
|---|---|---|---|
| 1. Canvas & Routing | input[0] `vae` | [1488, 1489] | both |
| 1. Canvas & Routing | input[1] `positive` | [1490] | 1490 |
| 1. Canvas & Routing | input[2] `negative` | [1491] | 1491 |
| 1. Canvas & Routing | input[3] `model` | [1492] | 1492 |
| 1. Canvas & Routing | output[4] `MODEL` | [1497, 1498] | 1498 |
| 3. Hands, Skin & Second Upscale | input[0] `image_b` | [1164, 1163] | 1164 |
| 6. Eyes | input[0] `clip` | [1415, 1413, 1414, 1412] | 1414 |

**[I]** Same class of residue as the blocker — bookkeeping left behind by node
deletion. The first five are in the subgraph WS1 is repairing. The last two are
in subgraphs the cleanup also touched and need their own verdict on whether
`getLinks()` tolerates a linkId with no link object.

---

## 7. Incident: a credential nearly entered the repo

`npm init -y`, run to install Playwright, copied the git remote URL into
`package.json`. That URL embeds a GitHub personal access token. GitHub push
protection rejected the push (`GH013`, `path: package.json:11`).

Nothing was pushed. `package.json` is now gitignored outright rather than
scrubbed, so no agent can reintroduce it (`c2dc9a7`). A full worktree scan for
the token pattern is queued before the final merge.

Worth carrying forward: **this repo's `origin` remote contains a live PAT.** Any
command whose output is pasted into a committed file — `git remote -v`,
`git config --list`, a failed-push transcript — leaks it.
