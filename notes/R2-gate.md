# R2 — the gate

Everything below was produced by driving a real Chromium against a real ComfyUI.
Command output is pasted, not summarised. Where something is inference it says so.
The screenshots are in `results/gate/` and are the point of this document; the prose
only tells you what to look at.

---

## 0. Verdict

| leg | what was under test | result |
|---|---|---|
| **run 1** | the working copy on the live ComfyUI (18188) | **PASS** — rendered end to end |
| **run 2** | the *then-committed* `dist/AIOFMTech-NSFW.tar.gz` (`27fa2e1c…`) installed into a ComfyUI that was empty before the run | **PASS** — rendered end to end |
| **run 3** | **the re-cut artifact that ships, `5f2a0f2b…`**, installed into a second, separately-built empty ComfyUI | **PASS** — rendered end to end |

`No output node found for id [647] slot [4] MODEL` **is fixed.** It did not occur on
any of the three legs. What it was, and how I checked rather than took it on trust, is §2.

**Exactly which bytes each leg covers:**

```
run 1  /workspace/ComfyUI/user/default/workflows/OFMTech_NSFW.json
       sha256 a811b5d690ccc5207bc7bd1c626cdd3db3b720b9be60d0a687436efcfd2143d8
       (identical to the repo copy at the time of the run — after #114 steps 8,
        #105 emptied + note, bbox_crop_factor 1.5)

run 2  dist/AIOFMTech-NSFW.tar.gz  sha256 27fa2e1c5496c4d0efee7d5b626e7638b197e1327500f86936a2a9e918dd3d37
       its OFMTech_NSFW.json       sha256 f1ac7e55d375380033f6b0acc67ee0f4706dd618303075f86213fc09e6beb22e

run 3  dist/AIOFMTech-NSFW.tar.gz  sha256 5f2a0f2bed3805e87aeb77d513118f6316af221dafb7da809967e146c36c5ab1
       its OFMTech_NSFW.json       sha256 a811b5d690ccc5207bc7bd1c626cdd3db3b720b9be60d0a687436efcfd2143d8
       8 155 368 bytes, 170 files, top-level AIOFMTech-NSFW/     <- THIS IS THE ONE THAT SHIPS
```

**Run 3's artifact is the one that ships**, and its workflow member is byte-identical
to the repo copy, so the shipped-tarball leg now covers the current graph — `#114`
steps 8, `#105` emptied plus its note, `bbox_crop_factor` 1.5. I verified both hashes
myself from the file on disk rather than accepting them:

```
$ sha256sum dist/AIOFMTech-NSFW.tar.gz
5f2a0f2bed3805e87aeb77d513118f6316af221dafb7da809967e146c36c5ab1
$ tar -xzf dist/AIOFMTech-NSFW.tar.gz -C … && sha256sum …/AIOFMTech-NSFW/OFMTech_NSFW.json
a811b5d690ccc5207bc7bd1c626cdd3db3b720b9be60d0a687436efcfd2143d8
$ sha256sum OFMTech-NSFW/OFMTech_NSFW.json
a811b5d690ccc5207bc7bd1c626cdd3db3b720b9be60d0a687436efcfd2143d8
```

**Run 2 is superseded and is kept only for what it independently shows** (a clean
install of an older cut also worked). Its artifact `27fa2e1c…` was the **committed
dist artifact**, not a published one — nothing a buyer could fetch. I checked what
Hugging Face actually serves rather than inheriting a hash from earlier notes:

```
$ curl -sSL -I -H "Authorization: Bearer …" \
    "https://huggingface.co/msit270/AIOFM-Pack/resolve/main/dist/AIOFMTech-NSFW.tar.gz"
x-linked-size: 8202871
x-linked-etag: "3f6d0f2ffd092cf9a1691684029030e37283dd484cd550573290677400aada76"
```

**Live HF is `3f6d0f2f…`, two cuts behind `5f2a0f2b…`.** Neither re-cut has been
uploaded. So *nothing I tested is currently downloadable by a buyer* — what I tested
is what is in `dist/`, which is what the publish command in `HANDOFF.md` would upload.

---

## 1. What the screenshots show

Names are self-describing; this is the reading order.

| file | what to look for |
|---|---|
| `run{2,3}-…-01-first-run-dialog.png` | **the buyer's literal first screen on a fresh install** — stock ComfyUI's Templates browser, modal, over everything (§5.1). Seen on both clean installs, independently |
| `run{1,2,3}-…-00-whole-graph-legible-5760px.png` | the whole graph in one frame at a zoom where node titles render (5760×3240, scale 0.78). Open this one to actually read the canvas |
| `run{1,2,3}-…-workflow-open-full-canvas.png` | the same fit at the ordinary 1920×1080 the gate runs at — the whole graph, nothing red, no dialog |
| `run{1,2,3}-…-both-lora-stacks.png` | **`2 · Your SDXL LoRa` carrying `lunaskye.safetensors` and `2 · Your ZIT LoRa` carrying `luna.safetensors`**, titles and values both legible |
| `run{1,2,3}-…-prompt-entered.png` | the prompt typed into the panel on `#483 1 · YOUR PROMPTS & SEED` |
| `run{1,2,3}-…-run-submitted.png` | after the real Run button; the prompt accepted |
| `run{1,2,3}-…-selector-popup.png` | `#603 INSTARAW_ImageFilter` pausing the render and waiting for a human |
| `run{1,2,3}-…-selector-image-picked.png` | the selection made and Send enabled |
| `run{1,2,3}-…-final-image-on-canvas.png` | **the finished image on `#505 YOUR IMAGE`** |
| `run{1,2,3}-…-final-image-feed.png` | the same image in the ComfyUI image feed |
| `run{1,2,3}-…-render-complete.png` | the moment the render finished |

`run{1,2,3}-…-result.json` is the machine-readable verdict for each leg, and
`run{1,2,3}-…-api_graph.json` is the API graph the browser actually POSTed.

The tool is `tools/browser_harness/gate.js`, committed. It is not a wrapper around
`run.js`; it drives the same journey and photographs it, and every claim it prints is
**read back out of the page after the action** — the LoRA value out of the graph, the
prompt out of `prompt_batch_data`, the Send button's real DOM `.disabled` property —
rather than inferred from a click that did not throw.

```bash
node tools/browser_harness/gate.js -w OFMTech_NSFW --tag mytag          # live, full journey
node tools/browser_harness/gate.js -w OFMTech_NSFW --tag mytag --no-run # everything but Run, ~40 s
```

---

## 2. `No output node found for id [647] slot [4] MODEL` — fixed, and what it was

I was told the cause. I checked it, because being told is not evidence.

**In the file.** `tools/fixtures/red_OFMTech_NSFW.json` is the graph as shipped before
the fix. Its subgraph `1. Canvas & Routing` carries three links that run straight from
the SubgraphInputNode `-10` to the SubgraphOutputNode `-20` with no node in between:

```
RED(pre-fix) SG: 1. Canvas & Routing
   declared inputs : [('vae','VAE'), ('positive','CONDITIONING'), ('negative','CONDITIONING'), ('model','MODEL')]
   declared outputs: [('output','LATENT'), ('FLOAT','FLOAT'), ('positive','CONDITIONING'), ('negative','CONDITIONING'), ('MODEL','MODEL')]
   links:
     link 1493: 635[0] -> -20[0] (LATENT)
     link 1494: 627[0] -> -20[1] (FLOAT)
     link 1495: -10[1] -> -20[2] (CONDITIONING) <== BARE IO PASSTHROUGH
     link 1496: -10[2] -> -20[3] (CONDITIONING) <== BARE IO PASSTHROUGH
     link 1497: -10[3] -> -20[4] (MODEL)        <== BARE IO PASSTHROUGH
```

`-20[4]` is output slot 4, named `MODEL`. The error names **slot [4] MODEL**. Node
`647` is the root-level host of this exact subgraph (`#647 9050d895-… '1 · Canvas &
Routing (output size)'`). The error's two identifiers both land on link 1497.

**In the frontend the buyer runs.** Fetched live from the running server, not from
memory (`http://127.0.0.1:18188/assets/api-gz4kgzki.js`):

```js
get originIsIoNode(){return this.origin_id===-10}
get targetIsIoNode(){return this.target_id===-20}

resolve(e){
  let t=this.target_id===-1?void 0:e.getNodeById(this.target_id)??void 0,
      n=t?.inputs[this.target_slot],
      r=this.originIsIoNode?e.inputNode?.slots[this.origin_slot]:void 0;
  if(r)return{inputNode:t,input:n,subgraphInput:r,link:this};        // <-- early return
  ...
}

_resolveSubgraphOutput(e,t,n){
  ...
  let a=r.resolveSubgraphOutputLink(e);
  if(!a)return;
  let o=a.outputNode;
  if(!o)throw Error(`No output node found for id [${this.id}] slot [${e}] ${i.name}`);
```

For a link `-10 → -20`, `originIsIoNode` is true, so `resolve()` takes the first
branch and returns an object **with no `outputNode` key at all**. `_resolveSubgraphOutput`
then throws with the host id and the output slot — which is precisely the message.
So the shape "input node straight to output node" is not representable by that
resolver; it is not a missing node or a missing model.

**The fix.** In the current file that whole passthrough is gone — the subgraph declares
`inputs: []` and two outputs instead of five, both fed by real nodes (`635
EmptyLatentImage`, `627 PrimitiveFloat`), and `#647`'s four root-level inputs and three
of its outputs were removed with the root graph rewired to match:

```
NOW  SG '1. Canvas & Routing'
   declared inputs : []
   declared outputs: [('output','LATENT'), ('FLOAT','FLOAT')]
   links: 1476 625[0]->635[0], 1477 628[0]->635[1], 1493 635[0]->-20[0], 1494 627[0]->-20[1]
 #647 inputs : []
 #647 outputs: output -> #619[1] (LATENT),  FLOAT -> #619[3] (FLOAT)
```

**And it converts.** All three legs pressed the real Run button and got `HTTP 200` with
an 88-node API graph, which is only reachable by completing `graphToPrompt`.

---

## 3. Run 1 — the working copy on the live ComfyUI

```
workflow        /workspace/ComfyUI/user/default/workflows/OFMTech_NSFW.json
                sha256 a811b5d690ccc5207bc7bd1c626cdd3db3b720b9be60d0a687436efcfd2143d8
object_info     1936 node types registered on the server
boot            4775 ms
open workflow   4498 ms   from the Workflows sidebar   title="OFMTech_NSFW - ComfyUI"
node audit      110 nodes across root + every subgraph, 59 distinct types
                frontend registered_node_types: 1953
                node types NOT registered in the frontend (= red nodes): 0
                node types absent from /object_info (excl. 7 subgraph hosts): 1
                  ABSENT   MarkdownNote
                nodes flagged has_errors: 0
                modal dialogs on screen: 0
                error toasts on screen: 0
lora            #618 SDXL stack: lora_01 = "lunaskye.safetensors"  (clicked in the widget's own menu)
lora            #116 Z-Image stack: lora_01 = "luna.safetensors"   (clicked in the widget's own menu)
prompt          typed into the RPG panel on #483 and committed on blur
press Run       the real Run button, label="Run"
prompt accepted HTTP 200  prompt_id=b0ad2862-5466-4ed8-a88e-180775377258  api graph 88 nodes  (1276 ms after the click)
  selector      1 image(s); Send on open=true, after clicking #0=false, after clicking it again=true
  selector      Send pressed at 283s into the render
render          415s wall (queue included)
  output        OK   /workspace/ComfyUI/output/Instaraw/SDXL/Metadata/HasMetadata_00041_.png  11140426 B  [node 505]
RESULT: PASS
```

### How "zero red nodes" was actually decided

Not by looking at the picture. A red node is one whose type never registered, and the
frontend's own test for that is in `loadGraphData` (`assets/dialogService-Cj1Hfeot.js`):

```js
collectMissingNodesAndModels=(e,t=``)=>{ for(let n of e){ if(!(n.type in U.registered_node_types)){ u.push({type:n.type,…}) …
collectMissingNodesAndModels(e.nodes);
if(e.definitions?.subgraphs) for(let t of e.definitions.subgraphs) … collectMissingNodesAndModels(t.nodes, t.name||t.id);
```

The gate applies the same predicate — `node.type in LiteGraph.registered_node_types` —
to every node at root **and inside every subgraph**, then cross-checks the same type
list against the server's `/object_info` over HTTP, and separately looks for ComfyUI's
missing-node dialog (`showLoadWorkflowWarning`, dialog key `global-missing-nodes`) and
for any error toast. All four came back clean.

**The walk is provably complete**, because its node count matches the file exactly:

```
dev copy (run1):        root=17 subgraph_total=93 TOTAL=110   <- gate reported 110
shipped tarball (run2): root=17 subgraph_total=92 TOTAL=109   <- gate reported 109
     (the one extra node is in '5. Face & Mouth Detail (Z-Image)', 13 vs 12 — the
      canvas note added by a806ce3, which the tarball predates)
```

`MarkdownNote` is the only type absent from `/object_info`, and that is correct: it is a
frontend-only node, present in `registered_node_types`, with no server class. It is not
red. **Naming it here rather than filtering it out is deliberate** — a check that
silently drops its own exceptions cannot be audited.

### It is not the flat-face failure

`#114`-class silent corruption presents as a large flat region of RGB ~(53,47,43)
delivered with `status: success`, so "it produced a PNG" is not enough. Measured:

```
/workspace/ComfyUI/output/Instaraw/SDXL/Metadata/HasMetadata_00041_.png
   2688x3456  mean RGB [121.8 110.7  97.5]  std [61.8 58.1 53.6]
   pixels within +-3 of the poisoned grey (53,47,43): 0.118 %
   largest single 4-bit colour bucket               : 4.78 % of frame
```

That is a positive reading, not an absence of symptoms.

### This leg doubles as the server-health control

An earlier attempt at this same leg (`8e8aa729`, same graph, same prompt, same LoRAs)
died at `622:403 MaskBoundingBox+` with
`min(): Expected reduction dim to be specified for input.numel() == 0`. Main established
independently — from a byte-identical resubmission of an arm that had rendered clean
earlier, and from a second agent's arm failing at the same node in the same window — that
the server had gone into a bad state at ~13:17, and R4 cleared it with
`POST /free {"unload_models":true,"free_memory":true}`. Run 1 above is the same graph and
prompt rendering clean **after** that `/free`. So: the crash was the instrument, and the
instrument is measurably back. I did not diagnose that myself and am not claiming it; what
I contribute is the after-control.

---

## 4. Run 2 — the shipped tarball, into a ComfyUI that was empty

### Standing up the clean instance without touching the live one

`tools/verify_buyer_path.sh` (WS5's, reused unchanged) into a **new** target so the
existing `comfy-ws5-verify` was not disturbed:

```
WS5_WORK=/workspace/r2gate-verify WS5_TARGET=/workspace/comfy-r2gate bash tools/verify_buyer_path.sh gist
  sha256 (api)    : bf80cb656be8d69c62150f9ceed42dbd8f6b228411b19e790795a7d25f45589a
  sha256 (raw CDN): bf80cb656be8d69c62150f9ceed42dbd8f6b228411b19e790795a7d25f45589a
  raw CDN matches the API right now

… prepare
  custom_nodes entries: 0  (0 = empty, as intended)
  models entries      : 29 directories, hardlinked
  hf download metadata: 74 files
  live models fingerprint: 87 files recorded

… happy   (the live gist bootstrap, pack served from a local mirror)
  pack sha256: 27fa2e1c5496c4d0efee7d5b626e7638b197e1327500f86936a2a9e918dd3d37
  profile        : all          time : 1m 27s
  downloaded     : nothing — everything was already on disk
  integrity      : OK           comfyui core : 0.15.1 validated
  comfyui        : not running — nodes load on next start
  --> exit code 0 after 87s
  shared venv unchanged (pip freeze identical before/after)
```

**The live instance was never restarted.** The installer restarts ComfyUI by supervisord
*program name*, so the harness forces `COMFYUI_PORT` to a dead port (39997, checked dead
first); the installer then takes its "ComfyUI is not running" branch and touches nothing.
That is WS5's protection, and I used it rather than inventing my own.

Then the fresh tree was started **with the GPU** (it has to render), politely:

```
cd /workspace/comfy-r2gate && /venv/main/bin/python main.py --disable-auto-launch \
    --disable-xformers --port 28190 --listen 127.0.0.1 --enable-cors-header --reserve-vram 16
UP after 3s      /object_info -> 1935 node types
```

Node-type diff against the live instance, so "clean" is a measurement and not a hope:

```
live 18188: 1936   fresh 28190: 1935
on live only : ['SaveImageWebsocket']      <- ComfyUI's own custom_nodes/websocket_image_save.py,
on fresh only: []                             which the fresh target's empty custom_nodes lacks. Unused by this workflow.
```

The workflow the installer put in that instance is byte-identical to the one inside the
tarball, which is what makes this leg a test of the artifact rather than of my tree:

```
f1ac7e55…beb22e  /workspace/comfy-r2gate/user/default/workflows/OFMTech_NSFW.json
f1ac7e55…beb22e  <tarball>/AIOFMTech-NSFW/OFMTech_NSFW.json
custom_nodes: 20 packs, ComfyUI_INSTARAW vendored @ 12afb909
```

### The run

```
boot            4422 ms
first-run modal 1 dialog(s) open on the very first page load of this install:
                  "Templates / All Templates / Popular"
                closed the way a buyer does; dialogs still open: 0
open workflow   4541 ms   from the Workflows sidebar
node audit      109 nodes, 0 not registered, 0 has_errors, 0 dialogs, 0 toasts
lora            #618 = lunaskye.safetensors     #116 = luna.safetensors
prompt accepted HTTP 200  prompt_id=76cbd518-9334-499b-8195-f282af7755a3  api graph 88 nodes
  selector      1 image(s); Send on open=true, after clicking #0=false, after clicking it again=true
  selector      Send pressed at 2s into the render
render          171s
  output        OK  /workspace/comfy-r2gate/output/Instaraw/SDXL/Metadata/HasMetadata_00001_.png  11151307 B  [node 505]
RESULT: PASS
```

`Send pressed at 2s` is not a fast render: the base generator's outputs were already in
ComfyUI's cache from the aborted attempt described in §5.2, so execution reached `#603`
almost immediately. The stages after the selector all ran.

**The two legs produced genuinely different images**, so neither is a stale file read
twice:

```
run1 3456x2688, run2 3456x2688
mean abs diff 0.1053  max 101  pixels differing 7.41%
```

Blast radius, checked rather than assumed: live ComfyUI (pid 8584) never restarted and
answering throughout, supervisord `comfyui` uptime unbroken, shared `/venv/main` identical
before and after, and the live `models/` tree fingerprinted before the run (87 files,
inode/size/mtime) — the hardlinked copy means a download into the fresh tree would replace
its own link, never the live file.

---

## 4b. Run 3 — the artifact that ships, into a second empty ComfyUI

Same method as §4, built again from scratch rather than reusing run 2's tree, against
the re-cut `5f2a0f2b…`. Work dir `/workspace/r2gate3-verify`, target
`/workspace/comfy-r2gate3`, ComfyUI on **28191**.

```
prepare   custom_nodes entries: 0  (0 = empty, as intended)
          models entries      : 29 directories, hardlinked
happy     pack sha256: 5f2a0f2bed3805e87aeb77d513118f6316af221dafb7da809967e146c36c5ab1
          profile : all   time : 1m 26s   integrity : OK   comfyui core : 0.15.1 validated
          comfyui : not running — nodes load on next start
          --> exit code 0 after 86s     shared venv unchanged (pip freeze identical before/after)
workflow that landed:  a811b5d690ccc5207bc7bd1c626cdd3db3b720b9be60d0a687436efcfd2143d8
custom_nodes after  :  20 packs
```

```
workflow        /workspace/comfy-r2gate3/user/default/workflows/OFMTech_NSFW.json
                sha256 a811b5d690ccc5207bc7bd1c626cdd3db3b720b9be60d0a687436efcfd2143d8
object_info     1935 node types registered on the server
first-run modal 1 dialog(s) open on the very first page load of this install:
                  "Templates / All Templates / Popular"      <- reproduced independently, §5.1
                closed the way a buyer does; dialogs still open: 0
open workflow   4565 ms   from the Workflows sidebar   title="OFMTech_NSFW - ComfyUI"
node audit      110 nodes across root + every subgraph, 59 distinct types
                node types NOT registered in the frontend (= red nodes): 0
                nodes flagged has_errors: 0   modal dialogs: 0   error toasts: 0
lora            #618 = lunaskye.safetensors    #116 = luna.safetensors
prompt          typed into the panel on #483, committed to prompt_batch_data
prompt accepted HTTP 200  prompt_id=ae0c3573-c5c8-4b5c-9d11-66da44b01b23  api graph 88 nodes
  selector      1 image(s); Send on open=true, after clicking #0=false, after clicking it again=true
render          292s
  output        OK  /workspace/comfy-r2gate3/output/Instaraw/SDXL/Metadata/HasMetadata_00001_.png  11142035 B  [node 505]
RESULT: PASS
```

Node count 110, matching the current graph (run 2's older cut had 109 — the extra node
is the `#105` canvas note). Not the flat-face failure: `0.118 %` of pixels within ±3 of
(53,47,43), largest flat colour bucket `4.78 %`.

### Isolation of this run, since the shared harness collides on hardcoded ports

`tools/verify_buyer_path.sh` defaults `WS5_MIRROR_PORT=38080`, `WS5_NODE_PORT=28188`,
`WS5_DEAD_PORT=39997`, and two agents ran it at once. I used the **defaults** for the
mirror and dead port, and **did not use `c_nodes` at all** — so the `28188` false-pass
class (probe succeeds against another agent's ComfyUI) cannot apply to any result here.
What I ran was `prepare` + `happy` only, and then my own ComfyUI on a port I chose.

The collision did touch me, and this is the reconstruction, from **my** mirror's log:

```
$ cat /workspace/r2gate3-verify/mirror.log
Serving HTTP on 127.0.0.1 port 38080 …
127.0.0.1 - - [06/Aug/2026 13:48:23] "GET /AIOFMTech-NSFW.tar.gz HTTP/1.1" 200 -   <- my installer, my file, complete
127.0.0.1 - - [06/Aug/2026 13:48:45] "GET /not-an-archive.tar.gz HTTP/1.1" 404 -   <- R5's bad-archive case, 22 s LATER
```

My transfer finished 22 seconds before the foreign request arrived, and the file my
mirror was serving is the target artifact (`sha256 5f2a0f2b…` on
`/workspace/r2gate3-verify/mirror/AIOFMTech-NSFW.tar.gz`).

**The clincher is content, not ports.** The tree the installer unpacked is byte-identical
to the artifact:

```
$ diff -r <tarball>/AIOFMTech-NSFW /workspace/r2gate3-verify/dest-happy/AIOFMTech-NSFW
  (exit 0, zero lines of output)
```

and the ComfyUI the browser talked to is provably mine:

```
$ ss -ltnp | grep 28191
LISTEN 0 128 127.0.0.1:28191  users:(("python",pid=144284,…))
$ ps -o pid,ppid,args -p 144284
144284 144282 /venv/main/bin/python main.py … --port 28191 …   (144282 = my nohup)
```

So this leg was not "isolated by luck" — it is isolated by evidence that can be
re-derived from the logs, and no re-run is needed to defend it. Ports and work dirs, for
the record: run 2 used `/workspace/r2gate-verify` → `/workspace/comfy-r2gate`, ComfyUI on
**28190**; run 3 used `/workspace/r2gate3-verify` → `/workspace/comfy-r2gate3`, ComfyUI on
**28191**; both used mirror `38080` and dead port `39997`; neither ran `c_nodes`. Run 1
used no part of this harness at all — it is a browser against the live 18188.

---

## 5. What the browser gate found that no API check could

### 5.1 A fresh install's first screen is a modal the buyer must close

`results/gate/run2-shipped-tarball-01-first-run-dialog.png`.

On the **very first page load** of a ComfyUI that has never been opened in a browser,
stock ComfyUI opens its **Templates browser** as a modal over the whole UI. It covers the
left toolbar, so the Workflows tab cannot be clicked until it is closed. The gate's first
attempt at run 2 failed on exactly that:

```
<div data-pc-section="mask" class="p-dialog-mask p-overlay-mask p-overlay-mask-enter">…</div> intercepts pointer events
```

It appears once. Closing it (or merely showing it) writes `Comfy.InstalledVersion` and
`Comfy.TutorialCompleted` into `user/default/comfy.settings.json`, after which it never
returns — which is why the second visit looks clean and why nothing but a first-ever
browser load can see it. To reproduce: `rm <comfy>/user/default/comfy.settings.json` and
reload.

**Not ours and not a defect** — it is stock ComfyUI 1.39.19 behaviour. It is in this
report because it is the first thing a buyer sees after a successful install, it is not
mentioned anywhere in our docs, and an API-only check is structurally incapable of
noticing it. The gate now photographs it and closes it the way a buyer does.

### 5.2 The image selector on a **single-image** batch opens with Send already enabled

Recorded on all three legs:

```
selector      1 image(s); Send on open=true, after clicking #0=false, after clicking it again=true
```

Read that in the light of the multi-image defect main fixed: with >1 image the popup opens
with Send **disabled** and one thumbnail click must enable it. With exactly one image it
opens **enabled**, because `popup.js:517-518` pre-picks it:

```js
this.picked = new Set();
if (this.n_images == 1) this.picked.add('0');
```

and `select_unselect()` (`popup.js:687-704`) **toggles**:

```js
if (this.picked.has(s)) this.picked.delete(s);
else this.picked.add(s);
```

So on the one-image path a thumbnail click *deselects*, and `Send` correctly goes
`true → false → true` across click and re-click. **That confirms the fix rather than
contradicting it**: the button tracks `picked.size` in both directions.

This cost me a run. My first gate clicked the thumbnail unconditionally and then reported
`clicked image #0 of 1 but the Send button is still disabled — the buyer cannot proceed`.
**That verdict was wrong and it was my harness, not the graph** (`04165d3` → fixed in the
next commit). It is recorded here because a false red is exactly as damaging as a false
green, and because the run it broke is the reason two renders were spent twice.

The 600 s abort path is also now observed rather than assumed. The render left waiting at
`#603` with nobody to answer it ended, in the fresh instance's own log:

```
Processing interrupted
Prompt executed in 00:12:30
```

which is `ontimeout='send none'` → `images_to_return=[]` → `raise InterruptProcessingException()`
in `image_filter.py:160`. A buyer who walks away loses the render.

### 5.3 The prompt panel on `#483` overhangs its own node and covers the LoRA titles

Measured, not eyeballed. With the canvas at scale 1.5, the DOM widget's own bounding rect
maps to graph y `298 → 1581`, while node `#483` occupies `110 → 1540`. It overhangs its
node by ~41 graph units, and `#618`/`#116` have their title bars at `1570 → 1600`, so the
panel covers the **top third of both LoRA node titles**, which is where litegraph draws the
title text. That is why `both-lora-stacks.png` is taken with `#483` collapsed for that one
frame (and expanded again immediately; nothing is saved). Cosmetic, ours, and worth a
one-line fix in the widget's height some day.

A related quirk, in case someone else hits it: a DOM widget only recomputes its visibility
when its **own** node is drawn, so expanding a node while it is culled leaves the panel
blank until something else forces a draw. The gate works around it by framing `#483`
before expanding it. On both legs the log line still reads
`prompt panel visible again: false`, because the check runs before the next draw settles —
that is a cosmetic artefact of my own check's timing, not a broken panel; the panel is
visible in `prompt-entered.png` taken earlier in the same run.

### 5.4 Page errors

Boot-phase (before any workflow is opened): 44 on the live instance, 15 on each clean
one. After the workflow was opened on the shipped-artifact run: **7**, every one a
`404`. Six of the seven are ours and they are on the buyer's very first open:

```
404 /api/view?filename=rgthree.compare._temp_aggxo_00001_.png&type=temp&…
404 /api/view?filename=rgthree.compare._temp_aggxo_00002_.png&type=temp&…
404 /api/view?filename=rgthree.compare._temp_fepic_00001_.png&type=temp&…
404 /api/view?filename=rgthree.compare._temp_fepic_00002_.png&type=temp&…
404 /api/view?filename=rgthree.compare._temp_tpbop_00001_.png&type=temp&…
404 /api/view?filename=rgthree.compare._temp_tpbop_00002_.png&type=temp&…
404 /api/userdata/workflows%2F.index.json
```

That is WS2 §3.2 — a developer's saved `Image Comparer (rgthree)` state baked into the
shipped workflow — **still present in `5f2a0f2b…`, and now observed on a clean install
rather than inferred from the file.** The last one is the optional workflow index, benign.
(Run 2's older cut logged only the index 404 in the post-load window; the six comparer
requests landed inside its longer boot window, so the difference is bucketing, not a
difference between the two graphs — both files carry the same ten `_temp_` names.) The boot noise is the documented pod
set — `user.css`, `comfy.templates.json`, `pysssss/autocomplete`, the `ComfyUI_Swwan`
`preloadError`s and the `rgthree.*` double-registration. Notably the fresh instance shows
the same `Swwan`/`rgthree` collisions, because **the bootstrap installs `ComfyUI_Swwan`
itself** — so WS2's note that "a buyer installing only the NSFW pack has neither problem"
does not hold for a buyer who runs `aiofm_setupnsfw.sh`. Flagging, not fixing: it is
another workstream's file.

---

## 6. What this does NOT prove

- **Image quality.** Not my call and not measurable here. The A/B evidence for the face
  work is R1/P2's.
- **A buyer's machine.** All three legs ran on this pod. The clean instance is genuinely clean
  in `custom_nodes` (0 → 20 from the tarball) and in `user/`, but it shares the pod's
  Python venv, its GPU driver and its model tree.
- **A cold model pull.** `models/` was hardlinked, so the installer verified 178.8 GB
  instead of downloading it. WS5 says the same thing about its own run and it is still true.
- **The multi-image selector path.** All three legs got a single image, so what they exercise is
  §5.2's one-image path. The multi-image Send-enable guard is WS2's fixture
  (`harness_selector_multi.json`), which is where that assertion lives.
- **That a buyer can download these bytes.** Hugging Face still serves `3f6d0f2f…`
  (§0). Nothing I tested has been published; publishing is one command in `HANDOFF.md`
  and it is the owner's to run.
- **The 178 GB cold pull, twice over.** Both clean installs re-verified a hardlinked tree.
- **`c_nodes` / `verify_buyer_path.sh nodes`.** I never ran it, so nothing here rests on it.

---

## 7. The gap between what I tested and what ships — closed, with one caveat left

When the first two legs ran, `dist/AIOFMTech-NSFW.tar.gz` was `27fa2e1c…` (workflow
`f1ac7e55…`), older than the tree. **That gap is now closed:** run 3 (§4b) put the
re-cut `5f2a0f2b…` into a second, separately built empty ComfyUI and rendered it end to
end, and its workflow member `a811b5d6…` is byte-identical to `OFMTech-NSFW/OFMTech_NSFW.json`.

What remains open, stated rather than papered over:

1. **If the tarball is cut again after this, my pass stops covering it.** The check is
   one command — `sha256sum dist/AIOFMTech-NSFW.tar.gz` — and the number to match is
   `5f2a0f2bed3805e87aeb77d513118f6316af221dafb7da809967e146c36c5ab1`. Anything else and
   the shipped-artifact leg must be re-run:
   ```bash
   WS5_WORK=/workspace/rX-verify WS5_TARGET=/workspace/comfy-rX \
   WS5_MIRROR_PORT=<free> WS5_DEAD_PORT=<free, checked dead> \
     bash tools/verify_buyer_path.sh gist && … prepare && … happy
   cd /workspace/comfy-rX && /venv/main/bin/python main.py --port <free> --listen 127.0.0.1 \
       --disable-auto-launch --disable-xformers --enable-cors-header --reserve-vram 16 &
   node tools/browser_harness/gate.js -w OFMTech_NSFW --tag rX --out results/gate \
       --url http://127.0.0.1:<free> \
       --workflows-dir /workspace/comfy-rX/user/default/workflows \
       --output-dir /workspace/comfy-rX/output
   ```
   About 12 minutes, all of it unattended.
2. **Nothing I tested is downloadable.** Live HF is `3f6d0f2f…`, two cuts behind. A green
   gate on `dist/` is not a green gate on what a buyer would fetch today.
