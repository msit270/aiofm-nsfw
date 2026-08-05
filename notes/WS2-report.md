# WS2 — test harness

Everything below was produced by running the tools on this pod. Command output is
pasted, not summarised. Where I could not test something, it says so.

- `tools/browser_harness/run.js` — real-browser test
- `tools/graph_diff/graph_diff.py` — the sanctioned inertness check
- `tools/preflight/integrity.py` — static link lint, vendored from WS1
- `tools/README.md` — how to run each, and what pass and fail look like

---

## 1. The proof the run was built on

The blocker reproduces in a real browser and **never reaches the server**. This
is the verbatim capture, from `results/browser/20260805-230516-red_OFMTech_NSFW/`:

```
RESULT: FAIL — 1 failure(s) in 1 class(es): frontend-conversion

  1. [frontend-conversion]
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
     ---
     Error
     No output node found for id [647] slot [4] MODEL
```

Two facts follow directly, without inference:

1. It is raised inside `graphToPrompt`, in the browser. The frame is
   `ExecutableNodeDTO._resolveSubgraphOutput`.
2. `prompt_posted: false` in `result.json`. **No POST to `/prompt` was ever
   made.** An API-only harness cannot see this class of bug, because there is
   nothing to submit.

The second block (`Error` / `No output node found…`) is the PrimeVue error toast
the buyer sees, captured separately from the console error.

**A caution for whoever reads a future trace.** `ComfyUI-KJNodes/js/setgetnodes.js`
monkey-patches `resolveOutput` and sits in this stack. KJNodes is installed on
this pod and will not be on a buyer's, so the same bug produces a differently
shaped stack there. Compare the message and the raising frame, not the whole
stack. This is also why the harness attributes an error to the **first** frame in
the stack rather than to any pack appearing anywhere in it — an earlier version
blamed KJNodes for a frontend-core error.

---

## 2. Proving the harness itself works

### Red — the pre-fix graph, exit 1

```
$ node tools/browser_harness/run.js --workflow red_OFMTech_NSFW \
    --install tools/fixtures/red_OFMTech_NSFW.json --no-submit
...
RESULT: FAIL — 1 failure(s) in 1 class(es): frontend-conversion
EXIT=1

real	0m9.378s
```

### Green — the fixed graph converts, exit 0

Same command against the current `OFMTech_NSFW`, after WS1's fix (`41e77f9`):

```
open workflow   3549 ms   path=ui  title="OFMTech_NSFW - ComfyUI"  root-level nodes=17
press Run       real button, label="Run"
api graph       86 nodes -> results/browser/20260805-230448-OFMTech_NSFW/api_graph.json
prompt accepted HTTP 200  prompt_id=harness-no-submit-c7d0cc3d339818  (732 ms from the click)
...
RESULT: PASS  (no-submit)
EXIT=0

real	0m9.341s
```

Red and green differ only in the workflow file. **The harness discriminates.**

### Green, end to end, with a real image on disk — exit 0

`results/browser/20260805-230510-harness_known_good/`:

```
$ node tools/browser_harness/run.js --workflow harness_known_good \
    --install tools/fixtures/harness_known_good.json

boot            4452 ms   0 pre-existing error(s) before any workflow was opened
open workflow   3288 ms   path=ui  title="harness_known_good - ComfyUI"  root-level nodes=7
press Run       real button, label="Run"
api graph       7 nodes -> .../api_graph.json
prompt accepted HTTP 200  prompt_id=5d8a3345-fe0b-4523-92cb-a3f568d2b5db  (970 ms from the click)
  queue         our prompt is waiting behind 3 other item(s) on this ComfyUI
render          673748 ms  (674s)
  output images:
    OK   /workspace/ComfyUI/output/harness_known_good_00001_.png  (198349 bytes)  [node 9]

RESULT: PASS  (execute)
GREEN_EXIT=0
```

```
status: pass | classes: [] | load_path: ui
counts: {'boot_errors': 0, 'load_errors': 0, 'run_errors': 0, 'ignored': 16}
$ ls -la /workspace/ComfyUI/output/harness_known_good_00001_.png
-rw-rw-r-- 1 root root 198349 Aug  5 23:16 .../harness_known_good_00001_.png
```

**Read the 674 s correctly.** Almost all of it is queue wait — this pod was
running other workstreams' 4-minute NSFW renders throughout. From the websocket
timestamps in `ws_events.json`, `execution_start` → `execution_success` for this
prompt was **1 814 ms**. The harness reports the wall time it actually waited and
prints the queue depth, rather than quietly presenting queue time as render time.

`boot_errors: 0` is worth noting on its own: with the ignore-list in place, a
page load on this pod now produces zero unignored errors, so the boot phase is
genuinely usable as a signal rather than permanent noise.

### Wall-clock timings measured

| run | mode | time |
|---|---|---|
| conversion check, either graph | `--no-submit` | **9.3–9.5 s** |
| static lint alone | `--preflight-only` | **~0.3 s** wall, 23 ms in the linter |
| boot phase | — | 4.2–4.5 s |
| open a 132-node, 7-subgraph workflow through the sidebar | — | 3.3–3.6 s |
| Run click → `/prompt` body captured | — | 0.73–0.97 s |

The 9 s conversion check is the number that matters: it is cheap enough to run on
every edit, and it is the check that would have caught the shipped blocker.

### Failure class (b) — server-side validation — demonstrated

Claiming the harness distinguishes three failure classes is worth nothing until
each has been seen. `harness_known_good` with `steps` hand-edited to `-5` (below
the server's `min: 1`, and no GPU is used because the prompt is rejected before
it queues):

```
$ node tools/browser_harness/run.js -w harness_bad_validation \
    --install .../bad_validation.json --no-execute --cleanup-install

FAILURE — (b) SERVER-SIDE VALIDATION REJECTION (HTTP 400)
  The frontend converted the graph and POSTed it. ComfyUI refused it at
  validation. Graph/model/widget problem, not a frontend conversion problem.

    "node_errors": {
      "3": {
        "errors": [ { "type": "value_smaller_than_min",
                      "message": "Value -5 smaller than min of 1",
                      "details": "steps", ... "received_value": -5 } ],
        "dependent_outputs": [ "9" ],
        "class_type": "KSampler"

EXIT=1
status: fail | classes: ['server-validation'] | http: 400 | posted: True
```

Contrast with the red fixture: `posted: True` and `http: 400` here, versus
`prompt_posted: false` and no HTTP status at all there. **That difference is the
whole point of separating the classes** — one means the graph never left the
browser, the other means it left and was refused.

### The ignore-list is auditable, and it is doing real work

`--no-default-ignores` on the same known-good workflow that otherwise passes
with `ignored: 16`:

```
UNIGNORED ERRORS FROM OTHER PACKS (environment, still counted): 9
  [boot/third-party-pack:ComfyUI_Swwan] ...
PRODUCT-SIGNAL ERRORS (frontend core / ComfyUI_INSTARAW / unattributable): 7
  [boot/comfyui-asset] Failed to load resource: ... 404
  [boot/frontend-core] [vite:preloadError] Error: Extension named 'rgthree.ImportIndividualNodes' already registered.
RESULT: FAIL — 1 failure(s) in 1 class(es): frontend-load
EXIT=1
```

All 16 reappear and the run goes red. Nothing is being hidden — the flag shows
the raw truth, and the committed list is what makes the difference.

`--cleanup-install` verified in the same run:

```
installed       tools/fixtures/harness_known_good.json
cleanup         removed /workspace/ComfyUI/user/default/workflows/harness_known_good.json
```

### graph_diff, both directions

Zero differences on a graph against itself (the 86-node API graph the browser
actually POSTed):

```
$ python3 tools/graph_diff/graph_diff.py api_postfix.json api_postfix_copy.json
  A  api_postfix.json  (85 nodes after normalisation)
  B  api_postfix_copy.json  (85 nodes after normalisation)
  folding ON   _meta ignored

folds applied to A: 1
    dropped 1 folded passthrough node(s): 619:604 (INSTARAW_BooleanBypass)
folds applied to B: 1
    dropped 1 folded passthrough node(s): 619:604 (INSTARAW_BooleanBypass)

RESULT: IDENTICAL — 0 differences.
EXIT=0
```

Non-zero on a perturbed copy — one widget changed:

```
$ python3 tools/graph_diff/graph_diff.py api_postfix.json api_postfix_perturbed.json
RESULT: DIFFERENT — 1 difference(s): value_changed=1

  value_changed      619:592.inputs.steps  (KSampler)
                       A: 40
                       B: 999
EXIT=1
```

And a harder perturbation — a deleted node, a rewired literal, and a link
replaced by a constant, all caught:

```
RESULT: DIFFERENT — 3 difference(s): link_changed=1, node_removed=1, value_changed=1

  node_removed       node 587:99  (GetImageSize)
  value_changed      587:506.inputs.text  (CLIPTextEncode)
                       A: ""
                       B: "PERTURBED PROMPT"
  link_changed       619:592.inputs.seed  (KSampler)
                       A: ["483", 2]
                       B: 999
```

**The test that proves the folding does something**, rather than merely claiming
to. An `INSTARAW_BooleanBypass` was inserted into a live `MODEL` link:

```
inserting a BooleanBypass into 116.inputs.model (was ['620:113', 0])

=== WITH FOLDING ===
folds applied to B: 2
    116.inputs.model: ['ZZ_fold_test', 0] -> ['620:113', 0] (through ZZ_fold_test[0])
    dropped 2 folded passthrough node(s): 619:604, ZZ_fold_test
RESULT: IDENTICAL — 0 differences.
EXIT=0

=== WITHOUT FOLDING (--no-fold) ===
RESULT: DIFFERENT — 2 difference(s): link_changed=1, node_added=1
EXIT=1
```

Timing: **33 ms** on an 86-node graph.

Two more behaviours checked, because a differ that misreports is worse than none:

*It refuses a UI-format file instead of diffing it into nonsense*, and exits 2 so
the caller can tell "you gave me the wrong file" from "the graphs differ":

```
$ python3 tools/graph_diff/graph_diff.py tools/fixtures/harness_known_good.json api_postfix.json
graph_diff: ...harness_known_good.json does not look like an API-format graph:
  10 entr(y|ies) without a class_type, e.g. ['id', 'revision', 'last_node_id'].
  This tool takes API format (what the browser POSTs to /prompt), not the
  UI/litegraph workflow file. browser_harness writes api_graph.json for you.
EXIT=2
```

*An unknown switch-like node is reported, not silently skipped.* A synthetic
`Some Impact Switch` was added to a graph and diffed against itself:

```
CAVEATS — things this diff did NOT fold or could not reason about: 1
  ! node ZZ_unknown_switch is a Some Impact Switch: the name looks like it selects
    between inputs but it is not in the fold table, so it was NOT folded. A change
    that replaces it with a direct wire will show as a difference.

RESULT: IDENTICAL — 0 differences.
  NOTE: read the caveats above before reading this as unconditional.
```

That last line is the point. "0 differences" is qualified by what the differ
could not reason about, rather than presented as unconditional proof.

---

## 3. Product defects the harness found

These were not looked for. They fell out of running it.

### 3.1 `popup.js` crashed on any client that did not have the node — FIXED

Reported to main from run `20260805-225520`, fixed in `342a038`:

```
TypeError: Cannot read properties of undefined (reading 'subgraph')
    at http://127.0.0.1:18188/extensions/ComfyUI_INSTARAW/popup.js:346:18
    at Popup.find_node (popup.js:344:9)
    at Popup._handle_message (popup.js:355:25)
    at WebSocket.<anonymous> (assets/api-gz4kgzki.js:4:4787)
```

Read at source: `find_node` walks `bits.forEach(bit => { node = graph._nodes_by_id[bit]; graph = node.subgraph })`
with no existence check per hop. The guard that was clearly intended —
`if (!this.node) return console.log('Message was for … which doesn't exist')` —
sits on the line *after* the throw and could never be reached for a nested uid,
and every uid in this graph is nested.

**Confirmed cleared.** Runs `20260805-230407`, `230448` and `230516` all show
`boot 0 pre-existing error(s)` and no `subgraph` pageerror, against the same
selector broadcast traffic that produced it before.

### 3.2 Ten stale preview filenames shipped inside the workflow JSON

```
$ grep -c "rgthree.compare._temp" OFMTech-NSFW/OFMTech_NSFW.json
10
$ grep -o "rgthree\.compare\._temp_[a-z]*_0000[0-9]_\.png" OFMTech-NSFW/OFMTech_NSFW.json | sort -u | head -3
rgthree.compare._temp_aggxo_00001_.png
rgthree.compare._temp_aggxo_00002_.png
rgthree.compare._temp_fepic_00001_.png
```

A developer's session state, baked into the file. The buyer gets six
`404 /api/view?filename=rgthree.compare._temp_*` the moment they open the
workflow. Cosmetic — the comparer widget shows nothing — but it is shipped dev
instrumentation, which CLAUDE.md already flags the comparers as.

**How to make the counter go to zero:** strip the saved image state from the
`Image Comparer (rgthree)` nodes in `OFMTech-NSFW/OFMTech_NSFW.json`, then delete
the `rgthree-comparer-stale-temp-images` rule from
`tools/browser_harness/ignore.json`. The run banner will drop from 7 to 1, and
the ignored count from 23 to 17. That drop is the proof.

### 3.3 Our pack logs `console.error` on a buyer's first load

```
[load/instaraw] [RPG] ERROR: detailsElement not found - probably not on Generate tab
  at http://127.0.0.1:18188/extensions/ComfyUI_INSTARAW/reality_prompt_generator.js:8280
```

Read at source, `reality_prompt_generator.js:8280-8282`: it is the `else` of
`if (detailsElement)`, and the only thing skipped is
`detailsElement.addEventListener('toggle', updateDetailsContent)`. Execution
continues to the Generate button handler at `:8284`. The immediately preceding
log lines are `Current active tab: library` and `Total <details> elements: 0`, so
the panel simply is not on the active tab.

Cosmetic, but our pack should not shout `ERROR` at a buyer for a condition it
handles. One-line fix: `console.error` → `console.debug`. Not changed by me —
WS3 also has that file.

**To make the counter go to zero:** make that change, then delete the
`instaraw-rpg-details-element` rule.

### 3.4 The selector popup is broadcast to every connected browser

Not a crash, but it decides how the harness must behave, and it is a real
multi-client property of the product. Observed directly: a fresh browser session
that had opened `OFMTech_NSFW` was covered by a full-screen selector popup
belonging to a render **started by a different client**, with the Run button
unclickable underneath it:

```
- <span class="grid">…</span> from <instaraw-imgae-filter-popup class="instaraw_popup">…</instaraw-imgae-filter-popup> subtree intercepts pointer events
```

The `unique` check in `_handle_message` is supposed to reject foreign messages —
`this.node._ni_widget?.value != message.detail.unique` — but `node_identifier` is
**persisted in the saved workflow file** (`#603` widgets_values ends `958955`),
so two browsers with the same saved workflow open compute the same value and both
accept the message. Two people on one server can therefore both see, and both
answer, the same selector.

Out of scope for me to change. The harness detects it, waits, and refuses to
dismiss it (see §5).

### 3.5 Pod-only, recorded so nobody re-diagnoses it

`ComfyUI_Swwan` (an rgthree fork, for the sibling video pipeline) is missing two
files its own modules import — `web/js/config.js` and `web/js/common/utils_dom.js`
— producing six Vite `preloadError`s per page load; and it collides with
`rgthree-comfy` on extension names (`rgthree.ImportIndividualNodes`,
`rgthree.ImageComparer`, `rgthree.Seed` are registered by both). A buyer
installing only the NSFW pack has neither problem.

---

## 4. Which boot errors a buyer on a clean install would also see

Main asked for this distinction specifically. Every 404 below was verified live
with `curl` and against the filesystem, not assumed.

| error | buyer sees it? | why |
|---|---|---|
| `404 /user.css` | **yes** | optional user stylesheet; not in `comfyui_frontend_package/static/`, absent here, requested unconditionally every load |
| `404 /api/userdata/user.css` | **yes** | same file via the userdata API |
| `404 /api/userdata/comfy.templates.json` | **yes** | saved node templates; only written once the user saves one |
| `404 /api/userdata?dir=subgraphs` | **yes** | subgraph blueprints dir; only created once the user saves one |
| `404 /api/userdata/workflows%2F.index.json` | **yes** | optional workflow index; never written on a fresh install |
| `404 /api/pysssss/autocomplete` | **no** | route belongs to `ComfyUI-Custom-Scripts` (`py/autocomplete.py`), which the NSFW bootstrap does not install |
| 6x `preloadError ComfyUI_Swwan/*` | **no** | pod-only pack, two of its own files missing |
| `Extension named 'rgthree.*' already registered` | **no** | needs both `ComfyUI_Swwan` and `rgthree-comfy` installed |
| 6x `404 /api/view?…rgthree.compare._temp_*` | **YES** | §3.2 — baked into the shipped workflow |
| `[RPG] ERROR: detailsElement not found` | **YES** | §3.3 — our pack |

The last two are the only entries that are ours, and they are the only two with
scope `product-known`. Everything above them is either genuinely benign on any
ComfyUI or specific to this pod.

---

## 5. Design decisions worth knowing about

**Three exit states, deliberately.** `0` pass, `1` the workflow failed, `2` the
test could not be carried out. Conflating "untested" with "passing" is the
failure mode this whole run exists to correct, so `harness-error` never returns 1.

**It does not stop at the first failure.** The first version did, and it hid the
Run-phase blocker behind two load-phase errors. Now a load-phase error does not
prevent pressing Run.

**Errors are classified by origin, not just severity.** `/assets/*` is frontend
core, `/extensions/ComfyUI_INSTARAW/*` is ours, another pack's extension URL is
this pod's environment. Attribution uses the **first** frame of a stack, because
several packs monkey-patch `graphToPrompt` and blaming any pack that appears
anywhere in the stack gets it wrong.

**It will not dismiss a foreign selector popup.** Cancel would abort somebody
else's render. It waits `--wait-for-idle-ui-ms` then exits 2 with an explanation.

**`--no-execute` cancels only its own queue item.** `{"clear":true}` would kill
another workstream's render on this shared pod.

**One bug worth recording because it silently disabled the ignore-list.**
Playwright reports a console location as `<url>:<line>`, so a `$`-anchored path
regex in `ignore.json` never matched and the list did nothing while appearing to
work. Fixed in `urlCandidates()`, which offers both the raw and the
line-stripped URL. A second, related one: de-duplicating events on message text
alone collapsed every distinct `Failed to load resource … 404` into one, so a
single ignored 404 could hide real ones. The de-dup key now includes the URL.

---

## 6. The static pre-flight

WS1's `results/ws1/integrity.py`, vendored to `tools/preflight/integrity.py`,
runs before the browser. Reviewed rather than adopted on faith:

```
$ python3 tools/preflight/integrity.py OFMTech-NSFW/OFMTech_NSFW.json
--- OFMTech-NSFW/OFMTech_NSFW.json: 0 problem(s) ---
real	0m0.023s

$ python3 tools/preflight/integrity.py tools/fixtures/red_OFMTech_NSFW.json
--- tools/fixtures/red_OFMTech_NSFW.json: 14 problem(s) ---
  SG '1. Canvas & Routing': link 1497 is a BARE IO PASSTHROUGH -10[3] -> -20[4] (MODEL) -- unsupported by ExecutableNodeDTO
  SG '1. Canvas & Routing': outputs[4] 'MODEL' linkIds names non-existent link(s) [1498]
  … 12 more
```

It names `outputs[4] 'MODEL'` — the same slot the browser names in
`No output node found for id [647] slot [4] MODEL`. **It would have caught the
blocker before anyone opened a browser.**

Where it must not be over-read, and this is in the vendored file's header:

- It checks **link bookkeeping only**. It does not check `widgets_values` desync
  on subgraph hosts, which CLAUDE.md calls the single highest-value audit in this
  file. "0 problems" is not "no defects".
- `inputs[i] has NO internal link (dead inside)` is warning-grade — a declared
  but unused subgraph input is legal litegraph. Here it coincided with a real
  defect; elsewhere it could be a false positive.
- "0 problems implies the browser converts" is a correlation established on
  **one** before/after pair. The browser stage remains the authority.

---

## 7. What is NOT proven

Stated plainly rather than papered over.

- **The multi-image selector interaction.** See §8.
- **Failure class (c), execution error.** Implemented — detected from the
  websocket `execution_error` / `execution_interrupted` frames and `/history`
  status, and deliberately not ignorable — but **not demonstrated**. It needs a
  render that fails mid-flight, and GPU time on this shared pod went to work
  worth more. A fixture is prepared (`INSTARAW_ImageFilter` with `timeout: 20`
  and no `--drive-selector`, which raises `InterruptProcessingException` on an
  empty selection) and not queued. Classes (a) and (b) are demonstrated above;
  this one is code I have read, not output I have seen.
- **A buyer's environment.** Everything here is one pod with ~20 extra packs
  installed. The ignore-list's `environment` entries are reasoned from which packs
  the bootstrap installs, not observed on a clean machine.

### Closed since the first draft

`--strict-boot` exercised on a run where it changes the verdict:

```
$ node tools/browser_harness/run.js -w OFMTech_NSFW --no-submit --no-default-ignores --strict-boot
RESULT: FAIL — 16 failure(s) in 2 class(es): frontend-load, boot-noise
EXIT=1
```

`--load-mode api` exercised, and it **reports itself honestly**:

```
open workflow   3363 ms   path=api-fallback  title="*Unsaved Workflow (2) - ComfyUI"  root-level nodes=17
api graph       86 nodes
RESULT: PASS  (no-submit)
EXIT=0
```

Note the title still reads `*Unsaved Workflow (2)`. The fallback does not make the
workflow "active", and the harness does not fake the title to cover that up — it
records `load_path_used: "api-fallback"` and lets the screenshot show the truth.

**The cross-check between the two load paths found something.** Diffing the API
graph produced via the sidebar against the one produced via `loadGraphData`:

```
RESULT: DIFFERENT — 1 difference(s): input_removed=1

  input_removed  419.inputs.rgthree_comparer  (Image Comparer (rgthree))
                 was {"images": [{"name": "A", "selected": true,
                      "url": "/api/view?filename=rgthree.compare....
```

The two paths are **not** equivalent. Opening the saved workflow properly carries
the persisted comparer state into the submitted prompt; `loadGraphData` on raw
JSON does not. Two consequences:

1. `--load-mode api` is a genuine fallback, not a shortcut — a run that used it
   has tested a slightly different graph. That is why the UI path is the default
   and the path used is recorded on every run.
2. The stale comparer state in §3.2 is not merely a UI artifact. It is **real
   payload being POSTed to the server** on every run a buyer makes.

### Now proven: graph_diff on a real before/after of the shipped graph

An earlier draft of this section said this could not be done, because the pre-fix
graph cannot produce an API graph at all — that is the bug. WS1 got round it by
making the "before" convertible: a control that keeps the original root wiring and
inserts frontend-virtual `Reroute` nodes. I ran **my** differ on that pair rather
than citing the result:

```
$ python3 tools/graph_diff/graph_diff.py results/ws1/control-api.json results/ws1/fixed-api.json
  A  results/ws1/control-api.json  (87 nodes after normalisation)
  B  results/ws1/fixed-api.json    (87 nodes after normalisation)
RESULT: IDENTICAL — 0 differences.
EXIT=0

real	0m0.033s
```

88 nodes each before normalisation, 87 after the `INSTARAW_BooleanBypass`
passthrough is folded out of both. **WS1's fix is inert**, independently
confirmed, in 33 ms and without a render.

Incidentally this corroborates a claim `graph_diff`'s own docstring makes: both
API graphs contain **zero** `Reroute` nodes even though the control was built by
inserting them, because the frontend resolves virtual reroutes before export.
That is why the fold table's `Reroute` entries are documented as only mattering
for API graphs from other sources.

---

## 8. The multi-image image selector

`#603 INSTARAW_ImageFilter` pauses every render for up to 600 s waiting for a
human to pick an image. Main fixed a defect in it (`3afa7ed`) where, with more
than one image, `select_unselect()` did not call `render()` after `redraw()`, so
the Send button never became enabled and the buyer was stranded until the timeout
sent nothing. That fix was established by logic proof against the real
`sendDisabled` expression — exact, but not a click.

**The single-image case must not be substituted for it.** With one image
`handle_filter` auto-picks index 0, so Send opens already enabled; that is
precisely the path that masked the defect.

### The fixture

`tools/fixtures/harness_selector_multi.json` — SD1.5, `batch_size 4`, 256x256,
4 steps, feeding an `INSTARAW_ImageFilter` with `pick_list=""` (empty is what
makes it wait for a human) and `timeout 300`. Built **through the real frontend**
via the litegraph API so that litegraph did the link bookkeeping rather than me:

```
$ python3 tools/preflight/integrity.py tools/fixtures/harness_selector_multi.json
--- tools/fixtures/harness_selector_multi.json: 0 problem(s) ---

10 INSTARAW_ImageFilter [300, 'send none', 'Run selector normally', '', '', '', '', 0, '', 1, 321186]
5  EmptyLatentImage      [256, 256, 4]
```

Four images at `#603`, and it costs seconds of GPU rather than four minutes.

**Which route to multi-image this exercises, and which it does not.** The fixture
gets four images by setting `batch_size 4` on the latent. A buyer reaches
multi-image the other way, through `#602 BatchFromImageList` fed by several
prompts. The popup code downstream of `#603` is identical either way — it
receives an image tensor of batch N and knows nothing about where N came from —
so this is a valid test of the Send-button behaviour. It is **not** a test of the
batch-from-prompts path, and nobody should later read it as one.

### How the harness asserts it

`popup.js:179-181` — `disabled(item, value) { item.disabled = value }` — sets the
real DOM `.disabled` property, so `isEnabled()` is a true reading of what the
buyer sees, not an inference. The harness therefore:

1. finds the Send button **before** clicking anything and records `isEnabled()`
2. clicks the chosen thumbnail
3. records `isEnabled()` again
4. **fails** with `clicked image #N of M but the Send button is still disabled —
   the buyer cannot proceed` if the enable did not happen

That is a positive reading of buyer-visible state rather than the absence of a
symptom — a click that merely times out could mean many things. Against the
shipped defect, step 4 is what would fire.

The Send button is located document-wide on purpose: it hangs off
`this.floating_window.body`, appended to `document.body`, **not** inside
`<instaraw-imgae-filter-popup>` (`popup.js:122-125`).

### A node-count reconciliation, from two independent directions

The API graph exported from the current tree has **86** nodes, where earlier
captures had 88. Both numbers are accounted for, and the two lines of evidence do
not depend on each other:

- *By arithmetic* (main's, GPU-free): 107 nodes in the file − 3 `MarkdownNote`
  (frontend-only) − 7 subgraph hosts − 11 nodes inside the bypassed anatomy stage
  = **86**. The drop from 88 is WS4's D1 removing `#597` and `#616`.
- *By diff* (mine): `graph_diff` on WS1's control/fix pair reports 88 vs 88 and
  **0 differences**, so the blocker fix itself changed nothing in the submitted
  graph. The node count moved for a different, known reason.

One counts, the other compares; neither uses the other's method.

### Result — PASS. The fix is verified in a real browser.

`results/browser/20260805-232312-harness_selector_multi/`:

```
$ node tools/browser_harness/run.js --workflow harness_selector_multi \
    --install tools/fixtures/harness_selector_multi.json --drive-selector --cleanup-install

preflight       integrity.py: --- harness_selector_multi.json: 0 problem(s) ---
open workflow   3303 ms   path=ui  title="harness_selector_multi - ComfyUI"  root-level nodes=8
press Run       real button, label="Run"
api graph       8 nodes
prompt accepted HTTP 200  prompt_id=c32645e4-a506-4204-86be-428d47dc3e66  (717 ms from the click)
  selector      image selector popup appeared with 4 image(s); clicking #0 then Send
  selector      Send enabled before pick=false, after pick=true
  selector      Send pressed at 398s into the render
render          400420 ms  (400s)
  output images:
    OK   /workspace/ComfyUI/output/harness_selector_multi_00001_.png  (64684 bytes)  [node 9]
cleanup         removed /workspace/ComfyUI/user/default/workflows/harness_selector_multi.json

RESULT: PASS  (execute)
```

```json
"selector": {
 "driven": true, "appeared": true, "images": 4, "picked": 0,
 "send_enabled_before_pick": false,
 "send_enabled_after_pick": true
}
```

`status: pass`, `failure_classes: []`, exit 0.

**The two readings that matter are `images: 4` and `false → true`.** Four images
in the popup; Send correctly starts disabled with nothing picked; clicking a
thumbnail enables it. Against the shipped defect this run would instead have
printed `clicked image #0 of 4 but the Send button is still disabled — the buyer
cannot proceed` and exited 1.

Main established the same conclusion by logic proof against the `sendDisabled`
expression. The two agree, and they agree **without sharing a method** — one
reasons about the source, the other reads the DOM property after a real click.

As with the green control, the 400 s is almost entirely queue: this was third in
line behind two ~86-node NSFW renders, and Send was pressed 398 s in, meaning the
popup appeared essentially the moment the prompt started running.

The fixture is kept permanently. It costs seconds of GPU, so it is cheap enough
to be a standing regression test for an interaction that every single render of
the shipped graph stops at — and this defect would have been caught on day one
by it.

---

## 9. State left behind

`/workspace/ComfyUI/user/default/workflows/` contains **only** `OFMTech_NSFW.json`.
Every fixture this session installed has been removed from the list a buyer picks
their workflow from; all three live in `tools/fixtures/` and are copied in on
demand by `--install`, and back out again by `--cleanup-install`.

Run artifacts are under `results/browser/<timestamp>-<workflow>/`. They are not
committed — `api_graph.json` is regenerated by any `--no-submit` run in 9 seconds,
so there is nothing there worth carrying in git.
