# WS1 — `No output node found for id [647] slot [4] MODEL`

Thread owner: WS1. Branch `fix/run2`, commit `41e77f9`.
Environment: live pod, ComfyUI 0.15.1 + `comfyui-frontend-package` 1.39.19 on
`http://127.0.0.1:18188`, RTX PRO 6000. CLAUDE.md's "no GPU, no ComfyUI" is
stale and does not apply here.

Everything below is either quoted from a file on this disk or pasted from
command output. Inference is labelled.

---

## 1. What node 647 is

Root node `647` is the **subgraph host** for definition
`9050d895-4e70-44f5-9c2b-57e2be7df0ec`, name `"1. Canvas & Routing"`, host title
`"1 · Canvas & Routing  (output size)"`. As shipped it had four inputs and five
outputs:

```
node 647 -> '1. Canvas & Routing'
    in [0] 'vae'      VAE          link 1499   <- 619.out[5] VAE
    in [1] 'positive' CONDITIONING link 1500   <- 619.out[0] CONDITIONING
    in [2] 'negative' CONDITIONING link 1501   <- 619.out[2] CONDITIONING_1
    in [3] 'model'    MODEL        link 1502   <- 618.out[0] MODEL  (Lora Loader Stack)
    out[0] 'output'   LATENT       [1503]      -> 619.in[3] latent_image
    out[1] 'FLOAT'    FLOAT        [1504]      -> 619.in[5] denoise
    out[2] 'positive' CONDITIONING [1505]      -> 619.in[1] positive
    out[3] 'negative' CONDITIONING [1506]      -> 619.in[2] negative
    out[4] 'MODEL'    MODEL        [1507,1508] -> 587.in[4] model, 619.in[8] model
```

Slot 4 is named `MODEL`, which is the name in the error text.

The subgraph contains only four real nodes: `#625 PrimitiveInt` Width=896,
`#628 PrimitiveInt` Height=1152, `#627 PrimitiveFloat` "Base denoise"=1, and
`#635 EmptyLatentImage`. Its real job is the latent and the denoise float.
Outputs 2/3/4 did no work at all.

---

## 2. Why it threw — file and line

Inside the subgraph, three links go **straight from the SubgraphInputNode to the
SubgraphOutputNode with no node in between**:

```
{id:1495, origin_id:-10, origin_slot:1, target_id:-20, target_slot:2, type:'CONDITIONING'}
{id:1496, origin_id:-10, origin_slot:2, target_id:-20, target_slot:3, type:'CONDITIONING'}
{id:1497, origin_id:-10, origin_slot:3, target_id:-20, target_slot:4, type:'MODEL'}
```

I scanned all seven subgraph definitions: `"1. Canvas & Routing"` was the only
one containing `-10 -> -20` links.

Sources below are the original TypeScript recovered from the shipped sourcemap
`/venv/main/lib/python3.12/site-packages/comfyui_frontend_package/static/assets/api-gz4kgzki.js.map`.

**`src/lib/litegraph/src/subgraph/ExecutableNodeDTO.ts:381-388` — the throw:**

```ts
    // Link inside the subgraph
    const innerResolved = node.resolveSubgraphOutputLink(slot)
    if (!innerResolved) return

    const innerNode = innerResolved.outputNode
    if (!innerNode)
      throw new Error(
        `No output node found for id [${this.id}] slot [${slot}] ${output.name}`
      )
```

**`src/lib/litegraph/src/subgraph/SubgraphNode.ts:467-477`:**

```ts
  resolveSubgraphOutputLink(slot: number): ResolvedConnection | undefined {
    const outputSlot = this.subgraph.outputNode.slots[slot]
    const innerLink = outputSlot.getLinks().at(0)
    if (innerLink) {
      return innerLink.resolve(this.subgraph)
    }
    ...
```

**`src/lib/litegraph/src/LLink.ts:309-338` — the actual mechanism:**

```ts
  resolve(network: BasicReadonlyNetwork): ResolvedConnection {
    const inputNode =
      this.target_id === -1 ? undefined : (network.getNodeById(this.target_id) ?? undefined)
    const input = inputNode?.inputs[this.target_slot]
    const subgraphInput = this.originIsIoNode
      ? network.inputNode?.slots[this.origin_slot]
      : undefined
    if (subgraphInput) {
      return { inputNode, input, subgraphInput, link: this }   // <- no outputNode key
    }

    const outputNode =
      this.origin_id === -1 ? undefined : (network.getNodeById(this.origin_id) ?? undefined)
    ...
    const subgraphOutput = this.targetIsIoNode
      ? network.outputNode?.slots[this.target_slot]
      : undefined
    if (subgraphOutput) {
      return { outputNode, output, subgraphInput: undefined, subgraphOutput, link: this }
    }
```

Sentinel values, taken from the **shipped minified bundle** because no
sourcemap in this build carries a literal assignment for them
(`grep -oE "origin_id===-?[0-9]+" assets/*.js` → `origin_id===-10` ×7;
`target_id===-20` ×7):

```
get originIsIoNode(){return this.origin_id===-10}
get targetIsIoNode(){return this.target_id===-20}
```

Link 1497 satisfies **both** predicates. `resolve()` tests the input side first,
`subgraphInput` is truthy, and it returns early with an object literal that has
**no `outputNode` property at all**. `_resolveSubgraphOutput` then reads
`innerResolved.outputNode`, gets `undefined`, and throws.

The precise finding: **a link that is simultaneously `originIsIoNode` and
`targetIsIoNode` can never reach the `subgraphOutput` branch, so a direct
subgraph-input → subgraph-output connection is unrepresentable in
`ResolvedConnection`.** The construct is unsupported by the resolver's design,
not merely dangling. No amount of `linkIds` tidying could have fixed it. (Note
also that the output-side guard compares against `-1`, not `-10`, so even that
path would have produced `undefined` — same outcome by a different route.)

Verified in the shipped minified bundle as well:

```
subgraphInput:r,link:this};let i=this.origin_id===-1?void 0:e.getNodeById(this.origin_id)??void 0,...
```

**How it got there — my reading of the evidence, labelled inference.** `MAP.md`
§4 describes this same subgraph before the destroyed-pod session with 22 nodes,
13 bypassed, and records that `#638 ControlNetApplyAdvanced` carried
positive/negative from the subgraph's inputs to its outputs and
`#644 IPAdapterUnifiedLoader → #643 IPAdapter` carried MODEL, all at `mode: 4`.
A **bypassed real node** between the IO nodes is the supported path — the DTO
resolves it through `_getBypassSlotIndex` then `resolveInput`, and
`resolveInput` explicitly handles `originIsIoNode` (`ExecutableNodeDTO.ts:175`,
"Link goes up and out of this subgraph"). When the dead ControlNet + IPAdapter
path was deleted, the editor reconnected the severed wires input-to-output
directly. That is a regression introduced by that cleanup, not a long-standing
latent defect. The dead `vae` input has the same origin: `MAP.md` §4 shows
`#631 VAEEncode` consumed it and `#631` was deleted too.

Consequently **this fix is not a workaround — it finishes an interrupted
cleanup.** The graph is now in the state it would have been in had the deletion
been completed properly.

---

## 3. Why no test caught it — confirmed, and it is worse than "a gap"

**STATE.md's hypothesis holds. Subgraph flattening is 100% frontend. The server
has no code that reads `definitions.subgraphs`, and no route that accepts a UI
workflow.** Ground truth from this disk:

- `server.py:872` `@routes.post("/prompt")` → `json_data["prompt"]` →
  `execution.validate_prompt(...)`. `validate_prompt` iterates
  `prompt[x]['class_type']` — a flat `{node_id: {class_type, inputs}}` dict.
  There is no other entry point for execution.
- `grep -rn "definitions" --include=*.py` over `/workspace/ComfyUI` (excluding
  `custom_nodes`) returns exactly two functional hits, both in
  `blueprints/.glsl/update_blueprints.py`, a developer tool for the blueprint
  library. Nothing in the request path.
- `app/subgraph_manager.py` is **not** a flattener. It registers only
  `@routes.get("/global_subgraphs")` and `@routes.get("/global_subgraphs/{id}")`
  (lines 123, 128) — it *serves* reusable subgraph blueprint files *to* the
  frontend. It never receives a workflow.
- `execution.py`'s `has_subgraph` (lines 337-403) is a different mechanism
  entirely: node-level dynamic expansion, triggered by a node returning
  `{'expand': ...}` or a V3 `NodeOutput.expand`. Nothing to do with UI
  subgraphs.
- `extra_data.extra_pnginfo.workflow` is read only for PNG metadata and for
  `workflow_id` in `comfy_execution/jobs.py:86-88`. It is never executed.

So: **a harness that POSTs an API graph to `/prompt` cannot possibly exercise
`graphToPrompt`, and `graphToPrompt` is the only thing that flattens
subgraphs.** Every render on this project to date went through that harness.

**Stated plainly: before today, this graph had never once been run the way a
buyer runs it.** "The NSFW graph renders" was true via the API and false via the
browser, and no amount of re-running the old harness would ever have said
otherwise. The blocker is not a test that was skipped; it is a whole half of the
system that had no test at all.

**And the one competing explanation is dead.** The obvious alternative — "the
author's editor was newer (`extra.frontendVersion` in the file is `1.41.20`, the
installed frontend is `1.39.19`), so maybe it converted for them and only breaks
here" — does not survive contact with the evidence. Main pulled
`comfyui-frontend-package==1.41.20` from PyPI and compared the original
TypeScript out of both wheels' sourcemaps (committed as `9a3a88a`):

| source | 1.39.19 sha256[:16] | 1.41.20 sha256[:16] | identical |
|---|---|---|---|
| `litegraph/src/LLink.ts` | `65f981e1d43a72ae` | `65f981e1d43a72ae` | **yes**, 15,505 B both |
| `subgraph/ExecutableNodeDTO.ts` | `4b0b9c68c4f83953` | `b8dd5ebf3ccec49b` | no, 13,909 → 13,999 B |
| `subgraph/SubgraphNode.ts` | `f6a819d9a4d8d31c` | `7d597d3a975b08cd` | no, 20,780 → 44,188 B |

`LLink.resolve` is **byte-identical** between the two versions, and 1.41.20's
`ExecutableNodeDTO.ts`, though changed, still carries the same throw reached the
same way. **The author would have hit this error on the very editor that saved
the file, had they pressed Run in a browser.** That leaves the API-harness
finding as the only explanation standing — corroboration by elimination, which
this project's history says is the method that works.

Two corollaries. First, upgrading the frontend was never going to be a fix, so
removing the construct was not one option among several — it was the only
available repair. Second, the recurrence risk is narrower and more precise than
a version trap: it is an **editing hazard**, namely that deleting a node which
sits between a subgraph input and a subgraph output may reconnect them directly.
That behaviour has *not* been confirmed by driving either editor's UI; see §8.

The stack trace confirms the same thing from the other side — every frame is
frontend, and the run never reached the network:

```
at graphToPrompt (http://127.0.0.1:18188/assets/dialogService-Cj1Hfeot.js:163:3857)
```

with `[queue] {"running":0,"pending":0,"history":0}` after pressing Run, and no
`POST /prompt` request recorded at all.

---

## 4. Reproduction in a real browser — verbatim

Playwright/Chromium against the live server. Loaded `OFMTech_NSFW` the way a
buyer does — Workflows sidebar → click the workflow — then pressed the Run
button. Full log: `results/ws1/repro-browser-events.log`. Install target was
byte-identical to the repo copy at the time
(sha256 `10b1a667…3fa72`, verified on both paths).

Workflow confirmed loaded before Run:

```
[info] loaded={"activeName":"OFMTech_NSFW","rootNodes":17,
       "nodeIds":[480,481,419,505,621,647,619,587,620,622,623,483,618,116,649,650,651],
       "subgraphDefs":7}
```

`console.error`:

```
Error: No output node found for id [647] slot [4] MODEL
    at ExecutableNodeDTO._resolveSubgraphOutput (http://127.0.0.1:18188/assets/api-gz4kgzki.js:2:210216)
    at ExecutableNodeDTO.resolveOutput (http://127.0.0.1:18188/assets/api-gz4kgzki.js:2:209110)
    at proto.resolveOutput (http://127.0.0.1:18188/extensions/ComfyUI-KJNodes/js/setgetnodes.js:1601:35)
    at ExecutableNodeDTO.resolveInput (http://127.0.0.1:18188/assets/api-gz4kgzki.js:2:208374)
    at ExecutableNodeDTO.resolveInput (http://127.0.0.1:18188/assets/api-gz4kgzki.js:2:208054)
    at graphToPrompt (http://127.0.0.1:18188/assets/dialogService-Cj1Hfeot.js:163:3857)
    at async app.graphToPrompt (http://127.0.0.1:18188/extensions/ComfyUI-Manager/components-manager.js:783:10)
    at async app.graphToPrompt (http://127.0.0.1:18188/extensions/rgthree-comfy/rgthree.js:503:13)
    at async app.graphToPrompt (http://127.0.0.1:18188/extensions/ComfyUI-Custom-Scripts/js/repeater.js:10:16)
    at async app.graphToPrompt (http://127.0.0.1:18188/extensions/ComfyUI-Custom-Scripts/js/reroutePrimitive.js:32:16)
```

Toast the buyer sees:

```
[toast/dialog] .p-toast-summary :: Error
[toast/dialog] .p-toast-detail  :: No output node found for id [647] slot [4] MODEL
```

Direct probe of the conversion, and the queue state afterwards:

```
[graphToPrompt] THREW Error: No output node found for id [647] slot [4] MODEL
[queue] {"running":0,"pending":0,"history":0}
```

No unhandled rejections. No `POST /prompt`. **Nothing ever reaches the server.**

One incidental observation, worth an audit line but not mine to chase: frame 3
of the stack is `ComfyUI-KJNodes/js/setgetnodes.js:1601` monkey-patching
`ExecutableNodeDTO.prototype.resolveOutput`, and four extensions wrap
`app.graphToPrompt`. None of them caused this, but they all sit in the path.

---

## 5. The fix

Design decision: **eliminate the unsupported construct rather than work around
it**, but *not* by the naive rewire. Wiring the root consumers straight to
whatever fed 647 would have produced a direct `619 → 619` edge for positive and
negative, because those two are a **self-loop on host 619 laundered through
647**:

```
#599 "PURE POSITIVE"  -> sg2 OUT[0] -> 1500 -> 647.in[1] -> 1495 -> 647.out[2] -> 1505 -> sg2 IN[1]
                                                                        -> #592 KSampler.positive  (1266)
                                                                        -> #617 UltimateSDUpscale.positive (1267)
```

Identical shape for `#606 "PURE NEGATIVE"`. The conditioning leaves subgraph 2
and comes straight back into subgraph 2. MODEL is different — it is plain
fan-out from root `#618`, not a loop.

Shipped changes (`fix_passthrough.py`, kept in `results/ws1/`; JSON edited
programmatically, never by hand):

1. **positive / negative — connect inside subgraph 2 where they belong.**
   Links 1266/1267 re-originated to `#599[0]`, links 1268/1269 to `#606[0]`.
   Links 1275 and 1282 (the ones that carried them out) deleted. sg2 inputs
   `positive`/`negative` and outputs `CONDITIONING`/`CONDITIONING_1` deleted.
   Root links 1500/1501/1505/1506 deleted. Host 619: 10 inputs → 8, 6 outputs → 4.
2. **MODEL — wire the fan-out directly.** New root links 1510
   (`#618[0] → 587.model`) and 1511 (`#618[0] → 619.model`). 1502/1507/1508
   deleted.
3. **vae — delete.** `647.in[0]` had no internal link at all; nothing consumed
   it. Root link 1499 deleted.
4. **647's IO removed:** all four inputs and outputs 2/3/4, plus passthrough
   links 1495/1496/1497. 647 is now a **pure source: zero inputs, LATENT +
   FLOAT out** — which is what "Canvas & Routing (output size)" should always
   have been. The host-level `619 ↔ 647` cycle is gone with it.
5. **All subgraph IO `linkIds` recomputed** from the actual link arrays.

Every remaining slot index was renumbered consistently in five places: the
definition's `inputs`/`outputs`, the host node's `inputs`/`outputs`, root links'
`origin_slot`/`target_slot`, internal links' `origin_slot` where
`origin_id == -10`, and `target_slot` where `target_id == -20`. A link-bookkeeping
checker (`results/ws1/integrity.py`) that validates all of that plus every
`node.outputs[].links` / `node.inputs[].link` cross-reference reports:

```
$ python3 integrity.py <shipped>          $ python3 integrity.py <fixed>
--- ...OFMTech_NSFW.json: 14 problem(s) ---   --- fixed.json: 0 problem(s) ---
  SG '1. Canvas & Routing': link 1495 is a BARE IO PASSTHROUGH -10[1] -> -20[2] (CONDITIONING)
  SG '1. Canvas & Routing': link 1496 is a BARE IO PASSTHROUGH -10[2] -> -20[3] (CONDITIONING)
  SG '1. Canvas & Routing': link 1497 is a BARE IO PASSTHROUGH -10[3] -> -20[4] (MODEL)
  SG '1. Canvas & Routing': inputs[0] 'vae' has NO internal link (dead inside)
  ... plus the 10 linkIds defects listed below
```

Nothing else in the file was wrong: those 14 are the complete list, and 12 of
them are on this one subgraph.

The `json.dump(indent=2, ensure_ascii=False)` round-trip of the untouched file
is **byte-identical** to the original, so the git diff shows only real changes
(68 insertions, 371 deletions).

### On `linkIds` — harmless bookkeeping, or a second failure?

`SubgraphSlotBase.ts:114-123`:

```ts
  getLinks(): LLink[] {
    const links: LLink[] = []
    const { subgraph } = this.parent
    for (const id of this.linkIds) {
      const link = subgraph.getLink(id)
      if (link) links.push(link)
    }
    return links
  }
```

A `linkId` naming a link that does not exist is **silently skipped**, so a
*ghost* id cannot throw. That is the whole of the `"3. Hands…"` `image_b` 1164
and `"6. Eyes"` `clip` 1414 residue: harmless.

But `linkIds` is **authoritative, not derived** — `SubgraphSlotBase.ts:98` is
`Object.assign(this, slot)` in the constructor body, which overwrites the
`readonly linkIds: LinkId[] = []` field initialiser with whatever the file
supplies. And on `"1. Canvas & Routing"` three input slots did the *opposite* of
the harmless case — they **omitted the real link while naming a dead one**:

```
inputs[1] 'positive' linkIds=[1490] actual=[1495]   1490 does not exist
inputs[2] 'negative' linkIds=[1491] actual=[1496]   1491 does not exist
inputs[3] 'model'    linkIds=[1492] actual=[1497]   1492 does not exist
outputs[4] 'MODEL'   linkIds=[1497,1498]            1498 does not exist
```

A slot whose `linkIds` omits its real link reports `isConnected === false`
(`SubgraphSlotBase.ts:82`) and returns nothing from `getLinks()`, which is what
`resolveSubgraphInputLinks()` uses. **My inference:** that asymmetry — output
bookkeeping updated, input bookkeeping left pointing at links to the deleted
`#638`/`#643`/`#644` — is further evidence for the interrupted-cleanup story.
I have not found a code path that turns it into a crash, so I am recording it as
*latent, not proven dangerous*; recomputing it costs nothing and removes the
question.

### The alternative I did not ship

Inserting an identity node inside the subgraph between input and output **does
work**, and I proved it (see §6). The core `Reroute` is registered by the
frontend extension `Comfy.RerouteNode` with `this.isVirtualNode = true`
(`src/extensions/core/rerouteNode.ts:37`, comment on :36 — *"This node is purely
frontend and does not impact the resulting prompt so should not be
serialized"*), and `/object_info/Reroute` on this server returns `{}` — there is
no server-side node of that type. `ExecutableNodeDTO.resolveOutput:290-312`
handles `isVirtualNode` by walking to `getInputLink(slot)` and calling
`resolveInput` on the reroute's own DTO, which then takes the
`link.originIsIoNode` branch at :175 and escapes correctly to the host input.
So it folds out cleanly and the API graph is identical to a direct connection.

I did not ship it because:
- it preserves the `619 ↔ 647` host-level cycle and the pointless detour, which
  is exactly the confusion this session is meant to remove;
- it makes the shipped product depend on a frontend extension node. This build
  carries `src/utils/migration/migrateReroute.ts` and a
  `RerouteMigrationToast.vue` whose job is converting legacy `Reroute` **nodes**
  to native link reroute **points** — shipping new ones to a buyer bets on a
  construct ComfyUI is actively migrating away from.

It was, however, exactly the right thing to build as the control.

---

## 6. Proof — constant-folded API-graph diff, zero differences

A "before" API graph cannot be produced: producing one is what crashes. So the
control is a variant that **keeps the original root wiring byte-identical** and
only inserts three virtual `Reroute` nodes inside 647 between input and output
(`fix_passthrough.py --control`). Because virtual nodes are folded out of the
API graph by the frontend itself, the control's API graph *is* the API graph the
shipped file would have produced.

Both were loaded in the **same browser session**, from the saved workflow list,
and their API graphs exported via `app.graphToPrompt()` **without pressing Run**,
so nothing mutated seeds or `control_after_generate` between them.

```
[ZZ_CONTROL_reroute] OK -> ctl-api.json  (88 nodes)
[OFMTech_NSFW]       OK -> fix-api.json  (88 nodes)
```

```
$ python3 apidiff.py ctl-api.json fix-api.json
ctl-api.json: 88 nodes   fix-api.json: 88 nodes
--- 0 difference(s) ---
```

The differ compares every node's `class_type` and every input — link inputs as
`[origin_execution_id, slot]`, widget inputs by value — and reports id-set
differences in both directions. `Reroute` does not appear anywhere in the
control's API graph, confirming the fold happened natively and no manual folding
was needed.

Artifacts: `results/ws1/control-api.json`, `results/ws1/fixed-api.json`,
`results/ws1/apidiff.py`, `results/ws1/fix_passthrough.py`,
`results/ws1/integrity.py`.

The control workflow itself was deliberately **not** left in
`/workspace/ComfyUI/user/default/workflows/` — a stray `ZZ_CONTROL_reroute`
there is exactly the sort of thing that ends up in a tarball. Regenerate it in
one command from the pre-fix file:
`python3 results/ws1/fix_passthrough.py <pre-fix.json> control.json --control`.

Spot-check that the diff is not vacuous — the routing that used to run through
647 now resolves to the right sources in the fixed API graph:

```
619:592 KSampler            positive ["619:599",0]  negative ["619:606",0]
                            model ["619:609",0]  latent_image ["647:635",0]  denoise ["647:627",0]
619:617 UltimateSDUpscale   positive ["619:599",0]  negative ["619:606",0]  model ["618",0]
619:608 ModelSamplingDiscrete  model ["618",0]
587:97  LoraLoader          model ["618",0]
647:635 EmptyLatentImage    width ["647:625",0]  height ["647:628",0]
505     SaveImage           images ["622:418",0]
```

**Rendered output was not hashed. That method is banned on this project.**

The control also settles the regression question independently: it converted,
POSTed `status=200`, and began rendering on the GPU. With the original wiring
intact and only a resolvable node inserted, the graph works — so the passthroughs
really are the whole defect.

---

## 7. Browser Run evidence — end to end, a real image

**The fixed workflow was loaded from the saved-workflow list in Chromium, Run
was pressed, and it produced an image.** This is the first time this pipeline
has been run the way a buyer runs it.

```
[22:47:20][info] opened OFMTech_NSFW
[22:47:42][info] pressed Run
[22:47:42][POST /prompt] status=200 {"prompt_id":"4f4d2b7d-6257-434a-8f7b-cd0086559701",
                                     "number":4,"node_errors":{}}
```

`node_errors: {}` — the server accepted all 88 nodes. Zero `pageerror`, zero
`console.error` in the whole session apart from pre-existing extension noise
(missing `ComfyUI_Swwan` assets, a duplicate `rgthree.ImportIndividualNodes`
registration, and 404s for `pysssss/autocomplete` and
`Comfy.CustomColorPalettes` — all present in the pre-fix run too).

Result:

```
[23:00:09][RESULT] SUCCESS outputs=[["505",["Instaraw/SDXL/Metadata/HasMetadata_00002_.png"]]]
```

```
$ /api/history/4f4d2b7d-...
status: success  completed: True
outputs: {'505': ['HasMetadata_00002_.png']}
execution_start   timestamp 1785970212133
execution_success timestamp 1785970805485      -> 593.4 s wall, filter pause included

$ ls -la /workspace/ComfyUI/output/Instaraw/SDXL/Metadata/
-rw-rw-r-- 1 root root 11294761 Aug  5 23:00 HasMetadata_00002_.png
PIL: size (2688, 3456)  mode RGB  metadata keys ['prompt', 'workflow']
```

Node `505` is the root `SaveImage`, `filename_prefix` =
`Instaraw/SDXL/Metadata/HasMetadata` — the product's final output node. A
2688×3456 RGB PNG. **I have not looked at the image and make no claim about its
quality;** the claim is that the pipeline ran to its terminal node.

**The prompt that actually executed is the graph I exported.** Diffing the API
graph recorded in `/api/history` against my exported `fixed-api.json`:

```
hist-4f4d2b7d-api.json: 88 nodes   fix-api.json: 88 nodes
--- 1 difference(s) ---
  node 419 (Image Comparer (rgthree)) input 'rgthree_comparer':
    hist='<absent>'  fix={'images': [...preview urls...]}
```

The single difference is rgthree's UI-only preview-URL blob on the Image
Comparer, which is populated by a *previous* render and was therefore absent at
submission time and present at export time. No routing input differs.

### Subsequent errors hit on the way, and how they were resolved

Fixing slot 4 exposed **no further graph errors** — the first Run after the fix
converted, validated and executed. The two obstacles below were in my harness
and in the INSTARAW pack's UI, not in the graph:

1. **The render pauses, by design, and looks like a hang.**
   `#614 PrimitiveBoolean "ENABLE IMAGE FILTERING?"` ships `true`, so
   `#603 INSTARAW_ImageFilter` ("Image Selector - PAUSES the render until you
   choose") blocks with GPU at 0 % behind a popup until the buyer clicks Send.
   Its widgets are `[600, 'send none', 'Run selector normally', …]` — a 600 s
   timeout that then sends **nothing**. Resolved by servicing the popup, which
   is what a buyer does. Logged as Q-WS1-4; I did not change the default.
2. **Two real defects in `ComfyUI_INSTARAW/js/popup.js`, found while
   automating that click.** Both are in the pack, not the graph, and neither is
   caused by the fix:
   - The popup's Send / Cancel / Hide buttons are **not children of the
     `<instaraw-imgae-filter-popup>` element** — they live in a sibling floating
     window in `document.body` (`popup.js:122-125`, `create('button', 'control',
     this.button_row, …)` where `button_row` hangs off `this.floating_window.body`).
     Anything scoping a query to the custom element finds zero buttons. Probe
     output: `"buttons":[]` inside the element, `"docButtons":[{"text":"Send",
     "disabled":false,"visible":true,"cls":"control"}, …]` document-wide.
   - `select_unselect()` (`popup.js:687-700`) calls `redraw()`, which only
     repaints thumbnail classes. The Send button's `disabled` state is computed
     in `render()` (`popup.js:214-218`), which `redraw()` never calls — so
     **clicking an image does not enable Send**. It happens to be masked in the
     single-image case because `handle_filter` auto-picks (`popup.js:518`
     `if (this.n_images == 1) this.picked.add('0')`) and `render()` runs after.
     With more than one image I expect a buyer to be unable to send at all.
     I did not test that case; see §8.
   My harness works around both (document-wide button query; force `render()`
   after picking) rather than patching the pack, which is not my thread.

### Independent corroboration

A second, unrelated prompt — `3dba994f`, from another agent's browser session
(`client_id 388b832a-…`) — completed `success` at 22:50 and wrote
`HasMetadata_00001_.png` from the same node 505. Its recorded API graph diffs
against mine on exactly one input:

```
hist-3dba994f-api.json: 88 nodes   fix-api.json: 88 nodes
--- 1 difference(s) ---
  node 619:603 (INSTARAW_ImageFilter) input 'pick_list': hist='0'  fix=''
```

`pick_list` is the filter node's own pre-selection widget (setting it to `'0'`
skips the pause). Every one of the other 87 nodes and every other input is
identical. So the fixed graph has now rendered to completion twice, from two
independent browser sessions, with two different people's harnesses.

Artifacts: `results/ws1/render-events.log`,
`results/ws1/rendered-prompt-api.json`.

---

## 8. What I could not verify

- **Whether the `linkIds` omission is exploitable.** I proved ghost ids are
  skipped and I proved `linkIds` is authoritative; I did **not** find a concrete
  code path in which a slot whose `linkIds` omits its real link produces a user-
  visible failure. Recorded as latent. Recomputing them was free, so the
  question is now moot for this file, but a future edit could reintroduce it.
- **The origin story is inference, not proof.** It rests on `MAP.md` §4
  describing a state of the file that no longer exists on this disk. I have no
  pre-cleanup copy of the workflow to diff against. The mechanism is proven; the
  history is reconstructed.
- **Whether other saved workflows in the product carry the same construct.**
  I scanned the seven subgraphs in `OFMTech_NSFW.json` only.
- **Whether the fix changes the image.** By construction it cannot — the API
  graph is identical — but I do not judge image quality, here or anywhere.
- **The editing hazard is still unverified.** The version hypothesis is settled
  (§3): 1.39.19 and 1.41.20 throw identically, so this is not a version trap.
  What remains open is the *editor behaviour* that produced the construct in the
  first place — whether deleting a node that sits between a subgraph input and a
  subgraph output causes either editor to reconnect them directly. Neither main
  nor I drove a UI to confirm it. Proposed experiment, precise enough to
  execute: open the fixed file, add a node inside a subgraph between an input
  and an output, bypass it, delete it, save, and check whether a `-10 -> -20`
  link appears in the saved JSON. Run it on both 1.39.19 and 1.41.20. If it
  reproduces, it is an upstream bug worth reporting and a permanent hazard for
  anyone editing this pack.
- **Whether the popup defect in §7 has a wider blast radius.**
  `select_unselect()` calling `redraw()` instead of `render()` is a real defect
  in `ComfyUI_INSTARAW/js/popup.js`, but I only observed it in the
  auto-picked single-image case where it happens to be harmless. I did not test
  the multi-image case, which is where I expect it to strand a buyer.
