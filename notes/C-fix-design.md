# TRACK C — designing the fix for the no-face crash

**Recommendation, one line:** add two Impact Pack nodes inside subgraph `622`
(`ImpactIsNotEmptySEGS` + `ImpactConditionalBranch`) so that when
`622:424 BboxDetectorSEGS` returns no face the Eyes stage is **not scheduled at
all** and the mouth-stage image passes straight through — no code changes in any
pack, no new dependency, and the change constant-folds to the shipping graph
when a face *is* found.

**Status of this document:** design and source work only. **Nothing was applied.**
`OFMTech-NSFW/OFMTech_NSFW.json` is untouched. The patch was generated against a
copy in the session scratchpad and validated there; the exact generator is in §4.2.

Every claim below cites a file and line. `[I]` marks inference.

---

## 1. What the source actually says

These are the four questions the brief asked, answered from the installed trees,
which are checked out at the SHAs `aiofm_setup.sh` pins (verified: `git rev-parse
HEAD` on each equals the `NODE_REPOS` entry — Impact Pack `429d0159`,
Impact-Subpack `50c7b71a`, essentials `9d9f4bedf`; `aiofm_setup.sh:1058-1062`).

### 1.1 `BboxDetectorSEGS` on no detection returns a *well-formed* SEGS with an empty list

`BboxDetectorSEGS` is registered to class `BboxDetectorForEach`
(`ComfyUI-Impact-Pack/__init__.py:154`). Its `doit`
(`ComfyUI-Impact-Pack/modules/impact/detectors.py:100-111`) calls
`bbox_detector.detect(...)`, then — because the widget is `labels: "all"` —
passes through `SEGSLabelFilter.filter`, which for `'all'` returns the SEGS
unchanged (`modules/impact/segs_nodes.py:450-451`):

```python
if 'all' in labels:
    return (segs, (segs[0], []), )
```

The detector is `UltraBBoxDetector.detect`
(`ComfyUI-Impact-Subpack/modules/subcore.py:418-456`). It appends to `items`
only inside the per-box loop, then unconditionally:

```python
shape = image.shape[1], image.shape[2]
segs = shape, items
...
return segs
```

**So on no detection it returns `((H, W), [])`** — the shape header is always
valid and correct; only the item list is empty. It is *not* an empty tuple and it
is *not* `None`.

**Consequence: a guard can tell the two cases apart, cheaply and exactly.** That
is precisely what Impact Pack's own `ImpactNotEmptySEGS` does
(`modules/impact/logics.py:49-60`):

```python
class ImpactNotEmptySEGS:
    ...
    RETURN_TYPES = ("BOOLEAN", )
    def doit(self, segs):
        return (segs[1] != [], )
```

It is registered under the node name **`ImpactIsNotEmptySEGS`**
(`ComfyUI-Impact-Pack/__init__.py:285` — note the class name and the node name
differ; wiring the class name into a workflow would produce a red node).

### 1.2 `SegsToCombinedMask` on empty SEGS emits an all-zero mask of the right shape

`SegsToCombinedMask.doit` (`modules/impact/segs_nodes.py:1253-1266`) delegates to
`core.segs_to_combined_mask` (`modules/impact/core.py:1481-1493`):

```python
def segs_to_combined_mask(segs):
    shape = segs[0]
    h = shape[0]
    w = shape[1]

    mask = np.zeros((h, w), dtype=np.uint8)

    for seg in segs[1]:
        ...
    return torch.from_numpy(mask.astype(np.float32) / 255.0)
```

With `segs[1] == []` the loop body never executes, so the return is
`torch.zeros(H, W)`. `utils.make_3d_mask` then makes it `(1, H, W)`. That is
**exactly** the tensor recorded in `notes/CRASH.md` — 3-D `(1,H,W)`, all zero.
It does not raise, and it never has.

### 1.3 The defect is one node from one pack — every other node on this path is already empty-safe

This is the single most useful thing I found, because it localises the bug and
kills the temptation to "harden the pipeline" broadly.

* **`MaskToSEGS` → `mask_to_segs` guards the identical situation**
  (`modules/impact/core.py:1323-1325`):

  ```python
  if combined:
      indices = np.nonzero(mask_i)
      if len(indices[0]) > 0 and len(indices[1]) > 0:
          bbox = ( np.min(indices[1]), ... )
  ```

  `622:408` runs with `combined = true` (widgets `[true, 3, false, 10, false]`),
  so it takes that branch. **The `622:402 → 622:408` path — MediaPipe finding no
  eyes — already degrades quietly today and has never crashed.**

* **`DetailerForEachDebug` (= class `DetailerForEachTest`,
  `ComfyUI-Impact-Pack/__init__.py:74`) is empty-safe.** `do_detail` iterates
  `for i, seg in enumerate(ordered_segs)` (`modules/impact/impact_pack.py:306`)
  and computes its return value *outside* the loop
  (`impact_pack.py:408`: `image_tensor = utils.tensor_convert_rgb(image)`).
  Empty SEGS ⇒ the input image comes back unchanged. `DetailerForEachTest.doit`
  additionally substitutes `utils.empty_pil_tensor()` for each empty list output
  (`impact_pack.py:1866-1878`).

* **`MaskBoundingBox+` does not guard it** (`ComfyUI_essentials/mask.py:183-187`):

  ```python
  _, y, x = torch.where(mask)
  x1 = max(0, x.min().item() - padding)
  ```

  No emptiness check. This is the whole defect.

**So the correct framing for the owner is not "the graph is fragile". It is:
Impact Pack checks for empty detections in the two analogous places; the one node
on this path that comes from `ComfyUI_essentials` does not.**

### 1.4 The nodes needed for a graph-level guard are already installed and already pinned

Enumerated by `GET 127.0.0.1:18188/object_info` (read only; nothing was POSTed),
1936 node types, cross-checked against the source trees:

| node name | pack | pinned in `NODE_REPOS`? | signature (from `/object_info`) |
|---|---|---|---|
| `ImpactIsNotEmptySEGS` | ComfyUI-Impact-Pack | **yes**, `429d0159` (`aiofm_setup.sh:1058`) | in `{segs: SEGS}` → out `BOOLEAN` |
| `ImpactConditionalBranch` | ComfyUI-Impact-Pack | **yes**, same | in `{cond: BOOLEAN, tt_value: ["*",{lazy:true}], ff_value: ["*",{lazy:true}]}` → out `*` |
| `ImpactConditionalBranchSelMode` | ComfyUI-Impact-Pack | yes | same, **not lazy** — inputs are plain `optional` |
| `ImpactCount_Elts_in_SEGS` | ComfyUI-Impact-Pack | yes | in `{segs}` → `INT` |
| `LazySwitchKJ` | ComfyUI-KJNodes | yes, `4d46ac10` | `switch: BOOLEAN`, `on_false`/`on_true` `["*",{lazy:true}]` → `*` |
| `easy imageIndexSwitch` | ComfyUI-Easy-Use | yes, `595e0738` | `index: INT`, `image0..19` `["IMAGE",{lazy:true}]` → `IMAGE` |
| `easy isMaskEmpty` | ComfyUI-Easy-Use | yes | in `{mask: MASK}` → `BOOLEAN` |
| `INSTARAW_ImageSwitch` | ComfyUI_INSTARAW (ours) | vendored | `boolean/input_true/input_false`, **eager** — see §5.3 |

**Which packs the graph already depends on** (resolved by looking every node type
in the workflow up in `/object_info`): Impact-Pack 10 types, INSTARAW 7,
essentials 3, rgthree 2, controlnet_aux 1, Impact-Subpack 1, UltimateSDUpscale 1,
rest core. **Zero** Easy-Use, **zero** KJNodes, **zero** ComfyMath types are used.
So an Impact-Pack-only guard adds no new pack to this workflow's dependency set;
the KJNodes and Easy-Use variants each would.

### 1.5 Laziness genuinely prevents upstream execution — this is the mechanism the fix rests on

`comfy_execution/graph.py:139-166`, `TopologicalSort.add_node`:

```python
_, _, input_info = self.get_input_info(unique_id, input_name)
is_lazy = input_info is not None and "lazy" in input_info and input_info["lazy"]
if (include_lazy or not is_lazy):
    if not self.is_cached(from_node_id):
        node_ids.append(from_node_id)
    links.append((from_node_id, from_socket, unique_id))
```

With `include_lazy=False` (the default on the normal traversal) the producer of a
lazy input is **not added to the pending set and no blocking link is created**.
It is scheduled only if `check_lazy_status` later asks for it, via
`make_input_strong_link` (`execution.py:490-497`, `graph.py:121-129`).

`ImpactConditionalBranch.check_lazy_status` (`modules/impact/logics.py:77-81`)
asks for `tt_value` only when `cond` is true and `ff_value` only when it is false.
So when no face is found, **`622:418`, `622:403`, `622:404`, `622:414`,
`622:415`, `622:410`, `622:402`, `622:408`, `622:406`, `622:401`, `622:399`,
`622:400`, `622:394`, `622:398` are never scheduled** — the crash node is not
merely tolerated, it is not run, and the 8-step sampler `622:406` is skipped with it.

`622:424` and `622:426` still run: they feed `cond`, which is a normal (non-lazy)
input.

Wildcard typing is accepted by the server: `comfy_execution/validation.py:28-30`,
`if received_type == IO.AnyType.io_type or input_type == IO.AnyType.io_type:
return True`.

---

## 2. Map of subgraph `622` (`6 · Eyes`), read from the file

Root node `622`, type `f3ba7c90-fce5-4154-9cb0-7a1de52da0fe`, title `6 · Eyes`,
`mode 0`, `widgets_values: []`. Subgraph inputs `clip, vae, images, model`;
outputs `IMAGE` (slot 0) and `IMAGE_1` (slot 1, **dead at root** —
`outputs[1].links: null`).

```
             sg-in images ──1424──▶ 431 INSTARAW_ImageListFromBatch   (OUTPUT_IS_LIST=[True])
                                       │
        ┌──────────────────────────────┼───────────────┬─────────────┐
      799│                          793│            796│          797,798
        ▼                              ▼               ▼             ▼
 424 BboxDetectorSEGS            404 ImageCrop   418 ImageComposite  sg-out IMAGE_1 (dead)
   thr 0.6 dil 10 cf 3               (.destination)      ▲
   drop 10 labels "all"                                  │761
        │791                                    401 INSTARAW_ImageResizeFill
        ▼                                                ▲729
 407 SegsToCombinedMask                          406 DetailerForEachDebug
        │733                                       seed 1111112, 8 steps, cfg 1,
        ▼                                          euler/beta, denoise 0.42
 403 MaskBoundingBox+   ◀── CRASHES                    ▲741      ▲742
   x→737(404.x),762(418.x)                        414 ImageResize+   408 MaskToSEGS
   y→738(404.y),763(418.y)                          1920 lanczos      ▲747
   w→735(404.w)  h→736(404.h)                       keep-proportion  402 SegsToCombinedMask
                                                        ▲753           ▲732
                                                   404 ImageCrop   410 MediaPipeFaceMeshToSEGS
                                                                       ▲749
                                                                  415 MediaPipe-FaceMesh
                                                                      Preprocessor
418 ─── links 764,773,774,775 ──▶ sg-out IMAGE  ──▶ root 623 (bypassed) ──▶ 419.image_b, 505.images
```

Consumers of the Eyes output confirmed against a real browser export
(`results/browser/20260806-125050-OFMTech_NSFW/api_graph.json`, 88 nodes):
`622:418` feeds exactly `419 Image Comparer (rgthree).image_b` and
`505 SaveImage.images`.

**What *should* happen when there is no face:** `622:431`'s image — the
mouth-stage output that `418` would otherwise composite onto — is already
available and already wired to two places. Passing it through is a one-link
change conceptually. The graph can express this **without any new node type**;
it needs one boolean node and one branch node, both already installed and pinned.

### 2.1 The batch caveat, stated plainly

`622:431 INSTARAW_ImageListFromBatch` declares `OUTPUT_IS_LIST = [True,]`
(`ComfyUI_INSTARAW/nodes/utility_nodes/list_utility_nodes.py:56`), so every node
below it is mapped once per list element (`execution.py:300-306`). `check_lazy_status`
is mapped the same way and its results are **unioned**
(`execution.py:490-492`: `required_inputs = set(sum([r for r in required_inputs
if isinstance(r,list)], []))`).

**Therefore: with a batch of >1 where some images have a face and some do not,
both branches become strong links and the crash returns.** The guard is complete
only for a batch where detection succeeds or fails uniformly.

In the shipping configuration the list has length 1: `635 EmptyLatentImage` in
subgraph `1. Canvas & Routing` has `widgets_values [896, 1152, 1]` and only
`width`/`height` are linked (links 1476, 1477) — `batch_size` is widget-only and
is 1. `[I]` I checked every node between that latent and `622` and found none
that multiplies the batch; `601`/`602`/`603` in the Base Generator are
list↔batch conversions and a user-driven *subset* selection of the same set. I
did not exhaustively prove no path can raise it, so treat "batch is always 1" as
inference, and see C3 for the version that is robust regardless.

---

## 3. Ranked candidates

Best first. "No-op on success" means: when the detector finds a face, the node
receives byte-identical inputs and the delivered image is produced by the same
computation.

| # | candidate | code changes | new pack dep | no-op on success | on failure | main risk |
|---|---|---|---|---|---|---|
| **C1** | **`ImpactIsNotEmptySEGS` + `ImpactConditionalBranch` inside sg622** | **none** | **none** | **yes — folds to the shipping graph** | eyes subtree never scheduled; mouth-stage image passes through | one `*`-typed *output* link, a pattern not yet exercised in this file (§4.4) |
| C1b | + `PreviewAny` on the boolean (companion, separate commit) | none | none | yes | makes the skip visible in `/history` and in the UI | one extra output-node execution root |
| C2 | same shape, `LazySwitchKJ` instead | none | **+KJNodes** | yes | same | slot order is `on_false` **then** `on_true` — inverted vs Impact; easy to miswire |
| C2b | same shape, `ImpactConvertDataType` → `easy imageIndexSwitch` | none | **+Easy-Use** | yes | same | 3 nodes instead of 2; but strictly `IMAGE`-typed on both sides — this is the fallback if C1 fails §4.4 |
| C3 | C1 **plus** a non-empty fallback mask into `622:403` (eager) | none | none | yes, if the switch is eager-safe | survives a *mixed* batch >1; burns one wasted eyes pass on the no-face element | more nodes, more ways to be wrong; only needed if batch >1 becomes reachable |
| C4 | new guard node in `ComfyUI_INSTARAW` | ours | none | yes | same as C1 | a **new node type** ⇒ the workflow needs a newer INSTARAW, and `aiofm_setup.sh:1165-1166` **does not update an existing install** ⇒ returning buyers get a red node and a dead graph |
| C4b | make the existing `INSTARAW_ImageSwitch` lazy | ours | none | yes | same as C1 | no new type, so an old INSTARAW opens fine — but silently reverts to eager, i.e. the crash comes back with no warning |
| C5 | patch `ComfyUI_essentials/mask.py` | **third-party** | none | **no** | returns the full-frame bbox ⇒ runs the eyes pass on the whole image ⇒ a lanczos up/down round-trip of the delivered image | forces a fork; see §5.5 |
| C6 | lower the YOLO threshold / swap the detector | none | none | **no** (changes detection everywhere) | moves the boundary rather than removing it | **this is the thing the owner explicitly rejected** — it is a complement, never the fix |

---

## 4. C1 — the recommended fix, exactly

### 4.1 The change in words

Inside subgraph `f3ba7c90-fce5-4154-9cb0-7a1de52da0fe` (`6. Eyes …`), add:

* **node `660`, type `ImpactIsNotEmptySEGS`**, title `face found?`
  * `segs` ← new link `1520` from `424:0`
* **node `661`, type `ImpactConditionalBranch`**, title
  `eyes pass, or pass through if no face`
  * `cond`      ← new link `1521` from `660:0`
  * `tt_value`  ← new link `1522` from `418:0`   *(the eyes result)*
  * `ff_value`  ← new link `1523` from `431:0`   *(the mouth-stage image, untouched)*
  * output → existing links `764, 773, 774, 775` → subgraph output slot 0

and repoint the four existing subgraph-output links from `418` to `661`. That is
eight edits in total:

| # | what | from | to |
|---|---|---|---|
| 1 | `nodes[424].outputs[0].links` | `[791]` | `[791, 1520]` |
| 2 | `nodes[418].outputs[0].links` | `[764,773,774,775]` | `[1522]` |
| 3 | `nodes[431].outputs[0].links` | `[793,796,797,798,799]` | `[…, 1523]` |
| 4 | links `764,773,774,775` `.origin_id` | `418` | `661` |
| 5 | new link objects | — | `1520,1521,1522,1523` |
| 6 | new nodes | — | `660`, `661` |
| 7 | `subgraph.state.lastNodeId / lastLinkId` | `647 / 1508` | `661 / 1523` |
| 8 | root `last_node_id / last_link_id` | `652 / 1511` | `661 / 1523` |

`subgraph.outputs[0].linkIds` stays `[764,773,774,775]` — the link *ids* do not
change, only their origin, so no IO bookkeeping moves.

**Ids were chosen above both counters** (root `last_node_id` 652, subgraph
`state.lastNodeId` 647; root `last_link_id` 1511, subgraph `state.lastLinkId`
1508) so they cannot collide with anything the frontend allocates.

**No `widgets_values` desync risk.** The trap in `CLAUDE.md` fires when a
*promoted widget* is added or removed on a subgraph host. `sg622.widgets` is `[]`
and root node `622.widgets_values` is `[]`; neither new node promotes anything, so
no host array shifts. Checked, not assumed.

### 4.2 The patch, ready to apply

Deterministic, self-checking, and byte-format-matched to the shipping file (which
is exactly `json.dump(indent=2, ensure_ascii=False)` **with no trailing newline** —
verified by round-tripping the file and getting a 1-byte difference, the newline).

```python
#!/usr/bin/env python3
"""Apply the Eyes-stage no-face guard.  usage: apply_guard.py <in.json> <out.json>"""
import json, sys, collections

SG = "f3ba7c90-fce5-4154-9cb0-7a1de52da0fe"
N_BOOL, N_BRANCH = 660, 661
L_SEGS, L_COND, L_TT, L_FF = 1520, 1521, 1522, 1523

def main(src, dst):
    with open(src, "r", encoding="utf-8") as fh:
        d = json.load(fh, object_pairs_hook=collections.OrderedDict)

    sg = next(s for s in d["definitions"]["subgraphs"] if s["id"] == SG)
    nodes = {n["id"]: n for n in sg["nodes"]}

    # refuse to patch anything but the exact shipping shape
    assert nodes[424]["type"] == "BboxDetectorSEGS"
    assert nodes[418]["type"] == "ImageCompositeMasked"
    assert nodes[431]["type"] == "INSTARAW_ImageListFromBatch"
    assert nodes[418]["outputs"][0]["links"] == [764, 773, 774, 775]
    assert nodes[424]["outputs"][0]["links"] == [791]
    assert 660 not in nodes and 661 not in nodes
    assert sg["outputs"][0]["linkIds"] == [764, 773, 774, 775]

    nodes[424]["outputs"][0]["links"] = [791, L_SEGS]
    nodes[418]["outputs"][0]["links"] = [L_TT]
    nodes[431]["outputs"][0]["links"] = [793, 796, 797, 798, 799, L_FF]

    for l in sg["links"]:
        if l["id"] in (764, 773, 774, 775):
            assert l["origin_id"] == 418 and l["target_id"] == -20
            l["origin_id"] = N_BRANCH

    sg["links"] += [
        {"id": L_SEGS, "origin_id": 424,     "origin_slot": 0, "target_id": N_BOOL,   "target_slot": 0, "type": "SEGS"},
        {"id": L_COND, "origin_id": N_BOOL,  "origin_slot": 0, "target_id": N_BRANCH, "target_slot": 0, "type": "BOOLEAN"},
        {"id": L_TT,   "origin_id": 418,     "origin_slot": 0, "target_id": N_BRANCH, "target_slot": 1, "type": "IMAGE"},
        {"id": L_FF,   "origin_id": 431,     "origin_slot": 0, "target_id": N_BRANCH, "target_slot": 2, "type": "IMAGE"},
    ]

    UE = {"widget_ue_connectable": {}, "input_ue_unconnectable": {}, "version": "7.4.1"}

    sg["nodes"].append(collections.OrderedDict([
        ("id", N_BOOL), ("type", "ImpactIsNotEmptySEGS"),
        ("pos", [5088.0, 5560.0]), ("size", [270, 26]),
        ("flags", {"collapsed": True}), ("order", 21), ("mode", 0),
        ("inputs",  [{"localized_name": "segs", "name": "segs", "type": "SEGS", "link": L_SEGS}]),
        ("outputs", [{"localized_name": "BOOLEAN", "name": "BOOLEAN", "type": "BOOLEAN", "links": [L_COND]}]),
        ("properties", collections.OrderedDict([
            ("cnr_id", "comfyui-impact-pack"), ("ver", "8.25.1"),
            ("Node name for S&R", "ImpactIsNotEmptySEGS"), ("ue_properties", UE)])),
        ("widgets_values", []), ("title", "face found?"),
    ]))

    sg["nodes"].append(collections.OrderedDict([
        ("id", N_BRANCH), ("type", "ImpactConditionalBranch"),
        ("pos", [5480.0, 5667.0]), ("size", [270, 66]),
        ("flags", {}), ("order", 22), ("mode", 0),
        ("inputs", [
            {"localized_name": "cond",     "name": "cond",     "type": "BOOLEAN", "link": L_COND},
            {"localized_name": "tt_value", "name": "tt_value", "type": "*",       "link": L_TT},
            {"localized_name": "ff_value", "name": "ff_value", "type": "*",       "link": L_FF},
        ]),
        ("outputs", [{"localized_name": "*", "name": "*", "type": "*",
                      "links": [764, 773, 774, 775]}]),
        ("properties", collections.OrderedDict([
            ("cnr_id", "comfyui-impact-pack"), ("ver", "8.25.1"),
            ("Node name for S&R", "ImpactConditionalBranch"), ("ue_properties", UE)])),
        ("widgets_values", []), ("title", "eyes pass, or pass through if no face"),
    ]))

    sg["state"]["lastNodeId"] = max(sg["state"]["lastNodeId"], N_BRANCH)
    sg["state"]["lastLinkId"] = max(sg["state"]["lastLinkId"], L_FF)
    d["last_node_id"] = max(d["last_node_id"], N_BRANCH)
    d["last_link_id"] = max(d["last_link_id"], L_FF)

    # shipping file has NO trailing newline; match it so the diff is minimal
    with open(dst, "w", encoding="utf-8") as fh:
        json.dump(d, fh, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
```

Run against the shipping file it produces a 245-line unified diff, 168 changed
lines, all of them the eight edits above and nothing else.

**Two notes on the metadata fields.** `properties.ver` is set to `8.25.1` to match
every other Impact node already in this file (`622:407`, `622:424`, …). It is
cosmetic — API export carries only `class_type`, `inputs` and `_meta` — but a
mixed-version graph makes ComfyUI-Manager noisy. `order` values are advisory;
the frontend recomputes topological order on load.

### 4.3 Behaviour

**When a face is found** (`cond = True`): `661` returns `tt_value`, i.e. the exact
tensor object `622:418` produced. `662`… nothing else changes. Every other node
in the whole graph receives byte-identical inputs. The two added nodes are pure
functions of already-computed values with no side effects, no RNG, no model load.

`[I]` I am asserting, not proving from a render, that adding two nodes does not
perturb sampling. The basis: every sampler in this graph carries an explicit fixed
seed in its own widgets (`622:406` seed 1111112 `fixed`; `619` KSampler
1083387472542732 `fixed`; etc.), and ComfyUI seeds each sampler's noise from that
value rather than from a global stream, so execution order is not load-bearing.
If a pod run ever shows otherwise, that is a much bigger finding than this fix.

**When no face is found** (`cond = False`): `661` returns `ff_value` =
`622:431`'s image — the mouth-stage output, unmodified. Per §1.5, the whole eyes
subtree is never scheduled. The render completes. The buyer gets an image whose
eyes were not detailed. Read §6 before deciding that is acceptable.

### 4.4 The one real risk, named

The shipping file already contains `*`-typed **inputs** carrying real links —
root `481 PreviewAny.source` ← link 892 from `480`, and
`619:604 INSTARAW_BooleanBypass.input_1` ← link 1251 from `603` (an `IMAGE`
output). Nine `"type": "*"` occurrences in total. What it does **not** yet
contain is a `*`-typed **output** feeding a typed consumer: `604`'s four outputs
are all unconnected, and `481` is terminal.

`661.outputs[0]` is `*` and it feeds a subgraph output slot declared `IMAGE`. The
**server** accepts this (`comfy_execution/validation.py:28-30`). Whether the
**frontend** will convert it without complaint through the subgraph-output
dissolve is the thing I cannot settle from source, and it is settled in 9 s with
no GPU by proof step P2 below. If it fails, **C2b** is the drop-in replacement
with strict `IMAGE` typing on both sides.

### 4.5 Proof plan — executable without re-deriving anything

None of P1–P3 needs a GPU. All of them refuse to use rendered-output hashing.

**P1 — link bookkeeping (25 ms, no server, no browser). ALREADY RUN.**

```bash
python3 tools/preflight/integrity.py OFMTech-NSFW/OFMTech_NSFW.json
```

Baseline: `0 problem(s)`. Patched copy: `0 problem(s)`. I ran both against the
scratchpad copies during this session. Note the tool's own caveat block
(`tools/preflight/integrity.py:14-24`): it checks link bookkeeping only, not
`widgets_values` desync, and 0 problems is not "no defects".

**P2 — frontend conversion (≈9 s, no GPU, no queue).**

```bash
node tools/browser_harness/run.js --workflow OFMTech_NSFW --no-submit
```

`--no-submit` intercepts `POST /prompt` and answers locally, so nothing reaches
the server (`tools/browser_harness/run.js`, MODE block). Expect exit 0 and no
error naming node `660`/`661` or a link type. This is the step that settles §4.4.
**Kill criterion:** a pageerror or error-level console message about the `*`
output ⇒ abandon C1, apply C2b instead.

**P3 — the inertness proof: constant-folded API-graph diff, 0 differences.**

The harness writes `api_graph.json` for each run. Take one from the **shipping**
graph and one from the **patched** graph, both exported the same way with the
same widget values (`results/browser/20260806-125050-OFMTech_NSFW/api_graph.json`
is a valid 88-node "before" if its widgets match; otherwise re-export first, so
the only delta is the guard). Then fold `cond = True` explicitly:

```python
import json
g = json.load(open("after/api_graph.json"))
if "prompt" in g and isinstance(g["prompt"], dict): g = g["prompt"]
src = g["622:661"]["inputs"]["tt_value"]      # must be ["622:418", 0]
assert src == ["622:418", 0]
for n in g.values():
    for k, v in list(n["inputs"].items()):
        if isinstance(v, list) and len(v) == 2 and v[0] == "622:661":
            n["inputs"][k] = src
del g["622:661"]; del g["622:660"]
json.dump(g, open("folded.json", "w"))
```

```bash
python3 tools/graph_diff/graph_diff.py before/api_graph.json folded.json
# required: "RESULT: IDENTICAL — 0 differences."  (exit 0)
```

Expected *unfolded* delta, for cross-checking that the fold did what it claims:
two new nodes `622:660`, `622:661`, and exactly two consumers repointed from
`["622:418",0]` to `["622:661",0]` — `419 Image Comparer (rgthree).image_b` and
`505 SaveImage.images` (both verified in the 88-node browser export). Nothing else.

> **Do not add `ImpactConditionalBranch` to `graph_diff.py`'s `FOLD_TABLE`.** The
> entry criterion in that file's docstring (lines 20-24) is a node "whose output
> is, per that node's own Python source, exactly one of its inputs". A conditional
> branch is not such a node, and an entry claiming it is would silently launder
> future changes. Fold it externally and visibly, as above. Note also that
> `graph_diff`'s `SWITCH_LIKE` regex (line 92) will flag `ImpactConditionalBranch`
> as an unfolded switch-like node in a *raw* diff — that caveat is correct and
> expected; the external fold is the answer to it.

**P4 — behaviour, on the pod, after P1–P3 pass.** Two arms, both cold, both on
the patched artifact, differing only in `620:106.inputs.text`.

* **P4-FAIL** — `620:106` = the exact crash string in `HANDOFF.md` §6.0
  reproduction block, both LoRAs loaded.
  * *Expect:* `status: success`, an image delivered, and `622:403`, `622:404`,
    `622:406`, `622:418` **absent** from the executed-node list in
    `/history/<prompt_id>`. That absence is the positive evidence that the lazy
    skip fired; it is stronger than "it didn't crash".
  * *Also expect:* the delivered image equals the `621:163` tap **from the same
    run**. Add a tap `SaveImage` on `621:163` (the arms in `results/crash/A/arms/`
    already do exactly this, e.g. `TAP163`). This is a **within-run identity
    check**, not a run-to-run output hash — it asks "is the output byte-equal to
    a specific tensor produced earlier in this same execution", which is a
    structural claim. It is not the banned method and should be labelled as such
    in the writeup so nobody mistakes it for one.
  * *Kill criterion:* still crashes at `622:403` ⇒ laziness is not behaving as
    `graph.py:160-165` says. The most likely reason is that the list at `622:431`
    has length >1 with mixed detection (§2.1); check `INSTARAW_ImageListFromBatch`'s
    output length before blaming the design.
* **P4-PASS** — `620:106` = the shipped placeholder, both LoRAs.
  * *Expect:* completes as before; executed-node list = the shipping set plus
    `622:660`, `622:661`.
  * **This arm proves nothing about inertness** — P3 does that. It is a smoke
    test. Do not report a matching image as evidence; that is the banned method
    wearing a hat.

### 4.6 What would kill C1

* P2 fails on the `*` output → C2b.
* P3 shows any difference beyond the two added nodes and the two repointed
  consumers → the patch is wrong; do not proceed.
* P4-FAIL still crashes → laziness assumption broken; re-examine §2.1.
* The owner decides a silent degraded image is worse than a crash (§6) → then
  C1 alone is not the answer, and C1 + C1b + a hard stop is.

---

## 5. The other candidates, assessed

### 5.1 C1b — make the skip visible (recommended companion, separate commit)

C1 converts a loud failure into a quiet one. The cheapest honest counterweight:
add **one** node inside sg622, `PreviewAny` (core,
`comfy_extras.nodes_preview_any`, `output_node: true`, input `source: "*"`),
fed from `660:0`. Cost: one extra link off `660`. Because it is an output node it
always executes, and its value lands in `/history/<prompt_id>.outputs["622:66x"]`
as the text `False` — machine-checkable headless, visible in the UI to anyone who
opens the subgraph. The pattern is already in this file: root `481 PreviewAny`
with a `*` link from `480`.

This does **not** put the warning in front of a buyer who never opens the
subgraph. Doing that properly means switching `505 SaveImage.filename_prefix`,
which needs a new `STRING` output on the host node `622` and an
`INSTARAW_StringSwitch` inside — a bigger change that touches the host node's
output list. It is worth doing, but it is its own commit and its own review;
I have not written that patch. Recorded in `notes/C-questions.md` as Q3.

### 5.2 C2 / C2b — the same design with other packs' nodes

**C2 (`LazySwitchKJ`)** is a genuine drop-in: `switch: BOOLEAN`,
`on_false`/`on_true` both `["*", {"lazy": true}]`, `check_lazy_status` at
`ComfyUI-KJNodes/nodes/nodes.py:2780-2784`. KJNodes is pinned (`4d46ac10`). The
only reasons not to prefer it: it adds KJNodes to this workflow's dependency set
(currently zero KJNodes types are used), and **its slot order is `on_false` then
`on_true`** — the reverse of Impact's — which is exactly the shape of mistake
that produces a graph that runs and does the wrong thing.

**C2b (`ImpactConvertDataType` → `easy imageIndexSwitch`)** is the fallback if
§4.4 goes badly. `easy imageIndexSwitch`
(`ComfyUI-Easy-Use/py/nodes/logic.py:356-377`) declares
`io.Image.Input("image%d", optional=True, lazy=True)` and a `check_lazy_status`
that requests only `image{index}` — strictly `IMAGE`-typed on both sides, and
genuinely lazy. Wiring: `660 ImpactIsNotEmptySEGS` → `ImpactConvertDataType`
(`modules/impact/logics.py:125-147`, returns `(STRING, FLOAT, INT, BOOLEAN)`,
take the `INT` at slot 2) → `index`; `image0` ← `431:0` (pass-through),
`image1` ← `418:0` (eyes result). Three nodes and one new pack dependency, but no
wildcard output anywhere.

### 5.3 C3 — the version that survives a mixed batch

Needed only if the batch at `622:431` can exceed 1 with mixed detection (§2.1).
Keep C1's branch on the output, and *additionally* stop `622:403` from ever
seeing an empty mask, so that the wasted element does not crash before the branch
discards it:

* `SolidMask` (core, `comfy_extras/nodes_mask.py`) with `value 1.0`, small
  `width`/`height` — the values do not matter because the branch throws the
  result away; they only need to be non-zero so `torch.where` is non-empty.
* an **eager** mask switch: `INSTARAW_MaskSwitch`
  (`boolean/input_true/input_false`, `logic_nodes.py:118-127`) with
  `input_true` ← `407:0`, `input_false` ← the solid mask, `boolean` ← `660:0`.
* `622:403.mask` ← that switch instead of `407:0`.

Cost when detection succeeds: one extra eager node evaluation, no change to the
mask. Cost on the failing element: a full wasted eyes pass (an 8-step sampler on
a junk crop) whose result is discarded. That is why it is not the default.
**Do not adopt C3 speculatively** — adopt it if and only if someone demonstrates
a batch >1 reaching `622`.

### 5.4 C4 / C4b — putting the guard in `ComfyUI_INSTARAW`

Honest assessment, because we own the pack and it is tempting.

*What is cheap about it:* INSTARAW is **vendored, not cloned** — the setup script
copies the folder that ships beside it (`aiofm_setup.sh:1164-1172`). There is no
repo, no pin, no upstream to negotiate with. Editing the folder in the tarball
*is* shipping it.

*What is not cheap about it:*

1. **`aiofm_setup.sh:1165-1166` deliberately does not update an existing
   install:** `if [[ -d "$COMFYUI_DIR/custom_nodes/ComfyUI_INSTARAW" ]]; then ok
   "ComfyUI_INSTARAW already present (left as-is)"`. A returning buyer who
   already has INSTARAW keeps the old one. A workflow that needs a **new node
   type** then opens with a red node and does not run at all. That is a worse
   failure than the bug we are fixing, and it lands on exactly the customers who
   have already paid.
2. It buys nothing. Impact Pack — already a hard dependency, already pinned,
   already carrying 10 of this graph's node types — ships the exact two nodes
   required. A new INSTARAW node would be reimplementing
   `ImpactNotEmptySEGS.doit`'s one-line body.

**C4b** is the narrower variant: add `{"lazy": True}` to `input_true`/
`input_false` on the existing `INSTARAW_ImageSwitch` and give
`INSTARAW_SwitchBase` a `check_lazy_status`. No new node type, so an old INSTARAW
still opens the graph — but it reverts to eager and the crash returns **with no
warning**, which is arguably worse than a red node. It would also change the
behaviour of every other `INSTARAW_*Switch` in every workflow that uses them.
Not recommended as the fix; worth doing on its own merits later.

### 5.5 C5 — patching `ComfyUI_essentials/mask.py`: what shipping it would mean

The minimal patch is obvious:

```python
_, y, x = torch.where(mask)
if x.numel() == 0:
    return (mask, image_optional, 0, 0, mask.shape[2], mask.shape[1])
```

**It does not do what you want.** A full-frame bbox does not skip the eyes pass —
it runs it on the whole image: `622:404 ImageCrop` returns the full frame,
`622:414 ImageResize+` upscales it to 1920 with lanczos, MediaPipe runs on it,
`622:401 INSTARAW_ImageResizeFill` scales it back down, and `622:418` composites
that over the original. The delivered image is then a **lanczos up-and-down
round-trip of the whole frame** — visibly softer, and produced silently. So even
with the patch you still need C1's branch, and the patch has bought nothing but
a fork.

*And it forces a fork.* `install_node()` (`aiofm_setup.sh:1071-1113`) does
`git fetch` then `git checkout -q "$sha"` on every run, and clones fresh if the
directory is absent. On a fresh pod the patch is simply not there. To persist it
we would have to publish a fork of `cubiq/ComfyUI_essentials`, put our URL in
`NODE_REPOS`, and own it — a pack whose upstream is already in declared
maintenance-only mode (the setup script's own comment,
`aiofm_setup.sh:1054-1057`, flags exactly this as a deliberate risk,
`QUESTIONS.md` Q12). Three nodes in this graph come from that pack
(`ImageColorMatch+` ×3 is on the live path, plus `MaskBoundingBox+` and
`ImageResize+`).

**Verdict: no.** If upstream should be fixed, the right move is a PR to cubiq,
not a shipped fork — and the graph-level guard makes us not care whether it lands.
**Per the brief, no such patch was applied.**

### 5.6 C6 — changing the detector

Lowering `622:424.threshold` from 0.6, or swapping `face_yolov8m.pt`, changes
detection on *every* render, including all the ones that work. It is not a fix
for "the graph has no guard"; it moves the boundary and leaves the cliff. It may
still be the right thing to do **on top of** C1 once Track A's data says whether
the face is destroyed or merely under-scored — their A4 tap (the actual image
handed to the failing detector, plus offline detection at descending thresholds)
is what decides it. Any such change is output-changing everywhere and needs an
A/B pair plus objective deltas, not a verdict.

---

## 6. What this does NOT fix

Stated plainly, because it is the part that matters and it is a genuine trade-off,
not a footnote.

1. **A guard turns a crash into a silently worse image.** If detection fails
   because the face pass produced garbage — currently the surviving hypothesis in
   `notes/CRASH.md` §"What this leaves" — then with the guard the buyer receives
   that garbage with `status: success` and no eyes detailing, instead of an error.
   `HANDOFF.md` §6.1 already records this exact failure *shape* on this pipeline
   ("a flat grey face with `status: success`") and records that it voided six arms
   and produced two confident wrong conclusions before controls caught it. **A
   crash is information. Removing it without adding a signal removes information.**
   That is why C1b is a companion and not an optional extra, and why I would not
   ship C1 alone.
2. **It does not restore the eyes pass.** The output on the failure path is
   strictly the mouth-stage image. Whether that is acceptable is a product
   judgement I am not able to make — I cannot judge image quality, here or on a pod.
3. **It does not explain why detection fails.** That is Track A's question. If the
   answer turns out to be "the prompt length pushes the face pass off a cliff",
   the guard stops the crash but the buyer still cannot type the character
   description they came for and get a good face. **The guard is necessary and it
   is not sufficient.**
4. **It does not cover a batch >1 with mixed detection** (§2.1). Shipping config
   is batch 1; C3 exists for the day that changes.
5. **It fixes nothing else on the open list**: the mouth-pass SEGS drop
   (`620:648`, `HANDOFF.md` §6.2, ~half of renders, no warning), the hard
   composite seam at the face-box edge (§6.3), NaN server poisoning (§6.1), or the
   five licence blockers (§6.4).
6. **It is not a quality change and must not be sold as one.** The only quality
   claim it supports is "renders that used to die now finish".

---

## 7. Appendix — evidence index

| claim | file:line |
|---|---|
| crash line | `/workspace/ComfyUI/custom_nodes/ComfyUI_essentials/mask.py:183-187` |
| `BboxDetectorSEGS` → `BboxDetectorForEach` | `ComfyUI-Impact-Pack/__init__.py:154` |
| `BboxDetectorForEach.doit` | `ComfyUI-Impact-Pack/modules/impact/detectors.py:100-111` |
| `labels="all"` is a no-op filter | `ComfyUI-Impact-Pack/modules/impact/segs_nodes.py:450-451` |
| detector returns `((H,W), [])` | `ComfyUI-Impact-Subpack/modules/subcore.py:451-456` |
| `ImpactNotEmptySEGS.doit` | `ComfyUI-Impact-Pack/modules/impact/logics.py:49-60` |
| registered as `ImpactIsNotEmptySEGS` | `ComfyUI-Impact-Pack/__init__.py:285` |
| `ImpactConditionalBranch` + `check_lazy_status` | `ComfyUI-Impact-Pack/modules/impact/logics.py:63-88` |
| `SegsToCombinedMask.doit` | `ComfyUI-Impact-Pack/modules/impact/segs_nodes.py:1253-1266` |
| all-zero mask from empty SEGS | `ComfyUI-Impact-Pack/modules/impact/core.py:1481-1493` |
| Impact *does* guard the analogous case | `ComfyUI-Impact-Pack/modules/impact/core.py:1323-1325` |
| `DetailerForEach` empty-SEGS safe | `ComfyUI-Impact-Pack/modules/impact/impact_pack.py:306, 408, 1866-1878` |
| lazy inputs are not scheduled | `/workspace/ComfyUI/comfy_execution/graph.py:139-166` |
| `check_lazy_status` → strong link | `/workspace/ComfyUI/execution.py:483-498` |
| lazy status is **unioned** over list elements | `/workspace/ComfyUI/execution.py:490-492` |
| list mapping | `/workspace/ComfyUI/execution.py:300-306` |
| `*` accepted by validation | `/workspace/ComfyUI/comfy_execution/validation.py:28-30` |
| `INSTARAW_ImageListFromBatch` is `OUTPUT_IS_LIST` | `OFMTech-NSFW/ComfyUI_INSTARAW/nodes/utility_nodes/list_utility_nodes.py:51-63` |
| INSTARAW switches are eager | `OFMTech-NSFW/ComfyUI_INSTARAW/nodes/logic_nodes/logic_nodes.py:87-96` |
| `LazySwitchKJ` | `ComfyUI-KJNodes/nodes/nodes.py:2761-2788` |
| `easy imageIndexSwitch` | `ComfyUI-Easy-Use/py/nodes/logic.py:356-377` |
| pins | `OFMTech-NSFW/aiofm_setup.sh:1058-1063` |
| `install_node` re-checkouts on every run | `OFMTech-NSFW/aiofm_setup.sh:1071-1113` |
| INSTARAW vendored, existing install left alone | `OFMTech-NSFW/aiofm_setup.sh:1148-1176` |
| sg622 nodes/links | `OFMTech-NSFW/OFMTech_NSFW.json` → `definitions.subgraphs[f3ba7c90…]` |
| `EmptyLatentImage` batch_size 1 | same file, subgraph `1. Canvas & Routing`, node 635 `widgets_values [896,1152,1]` |
| consumers of `622:418` | `results/browser/20260806-125050-OFMTech_NSFW/api_graph.json` |
| crash-run chain | `notes/CRASH.md` Phase 0 |
