# tools/

Rebuilt test harness for the NSFW pipeline. Owned by WS2.

Two tools:

| tool | what it answers |
|---|---|
| `preflight/integrity.py` | "Is the graph's link bookkeeping self-consistent?" (~25 ms, no browser) |
| `browser_harness` | "Does this workflow work **in a browser**, the way a buyer runs it?" |
| `graph_diff` | "Is this change to the graph **inert**?" |

The old harness submitted an already-flattened API graph straight to `/prompt`.
That path never exercises the frontend's UI-graph → API-graph conversion, and
the conversion is where the shipped-graph blocker lived. **A render that only
passes via the API is not a passing test.** Everything here exists to close that
gap.

---

## 0. preflight — static, ~25 ms, no browser

A link-bookkeeping lint on the **UI-format** workflow JSON. It runs automatically
before the browser stage whenever `--install` or `--preflight` names a file.

```bash
python3 tools/preflight/integrity.py OFMTech-NSFW/OFMTech_NSFW.json
# --- OFMTech-NSFW/OFMTech_NSFW.json: 0 problem(s) ---

node tools/browser_harness/run.js -w OFMTech_NSFW \
  --preflight OFMTech-NSFW/OFMTech_NSFW.json --preflight-only
```

On the pre-fix fixture it reports 14 problems in 23 ms, including
`SG '1. Canvas & Routing': outputs[4] 'MODEL' linkIds names non-existent link(s) [1498]`
— the same slot the browser names in `No output node found for id [647] slot [4] MODEL`.
**It would have caught the shipped blocker before anyone opened a browser.**

**Do not over-read it.** It checks link bookkeeping only — not `widgets_values`
desync on subgraph hosts, which CLAUDE.md calls the highest-value audit in this
file. "0 problems" is not "no defects", and "0 problems implies the browser
converts" is a correlation established on exactly one before/after pair. The
browser stage remains the authority. Full caveats are in the file's header.

---

## 1. browser_harness

Launches Chromium (Playwright), opens a saved workflow **through the Workflows
sidebar the way a buyer does**, presses the **real Run button**, and fails on any
frontend error.

### Copy-paste commands

Fast conversion check — no server, no GPU, ~9 s. **Use this while iterating on the graph.**

```bash
cd /workspace/nsfw-fix
node tools/browser_harness/run.js --workflow OFMTech_NSFW --no-submit
```

Same, but install your repo copy over the install target first, and drop the
captured API graph somewhere convenient for diffing:

```bash
node tools/browser_harness/run.js \
  --workflow OFMTech_NSFW \
  --install OFMTech-NSFW/OFMTech_NSFW.json \
  --no-submit \
  --api-out /tmp/api_after.json
```

Conversion **plus** real server-side validation, still no render (~15 s). Cancels
only its own queue item:

```bash
node tools/browser_harness/run.js --workflow OFMTech_NSFW --no-execute
```

Full buyer journey, including the deliberate mid-render image-selector pause:

```bash
node tools/browser_harness/run.js --workflow OFMTech_NSFW --drive-selector
```

Known-good control — proves the harness itself can go green:

```bash
node tools/browser_harness/run.js \
  --workflow harness_known_good \
  --install tools/fixtures/harness_known_good.json
```

Permanent red fixture — proves the harness can still go red:

```bash
node tools/browser_harness/run.js \
  --workflow red_OFMTech_NSFW \
  --install tools/fixtures/red_OFMTech_NSFW.json \
  --no-submit
```

`node tools/browser_harness/run.js --help` lists every option.

### The three modes, and what each one does NOT test

| mode | frontend conversion | server validation | render | typical time |
|---|---|---|---|---|
| `--no-submit` | tested | **not tested** | **not run** | ~9 s |
| `--no-execute` | tested | tested | **not run** | ~15 s |
| default | tested | tested | tested | render time |

`--no-submit` intercepts `POST /prompt` and answers it locally, so nothing
reaches the server at all. `--no-execute` really submits, takes the server's
verdict, then cancels **only its own** queue item (`POST /queue {"delete":[id]}`),
never `{"clear":true}` — this pod is shared and clearing would kill another
workstream's render.

### What a PASS looks like

```
RESULT: PASS  (no-submit)
  The frontend converted the graph and produced a well-formed /prompt body.
  Nothing was sent to the server: server validation and execution are UNTESTED.
```

Exit code `0`.

### What a FAIL looks like

```
RESULT: FAIL — 3 failure(s) in 2 class(es): frontend-load, frontend-conversion

  3. [frontend-conversion]
     Error: No output node found for id [647] slot [4] MODEL
         at ExecutableNodeDTO._resolveSubgraphOutput (.../api-gz4kgzki.js:2:210216)
         ...
```

Exit code `1`. Exit code `2` means the test could **not be carried out**
(ComfyUI unreachable, workflow not found, a foreign popup blocking the UI) — that
is not a verdict on the workflow.

### The three failure classes, because they mean different things

| class | meaning | who fixes it |
|---|---|---|
| `frontend-conversion` | Run pressed, frontend threw during `graphToPrompt`, **no POST to `/prompt` was made**. The server never saw it. Invisible to any API-only harness. | graph / subgraph wiring |
| `server-validation` | Frontend converted fine and POSTed. ComfyUI refused it (non-200, or `node_errors` on a 200). | widgets, model files, node inputs |
| `execution` | Prompt accepted, then a node raised mid-render (websocket `execution_error`). | node behaviour, VRAM, model contents |

Also emitted: `frontend-load` (an error while merely *opening* the workflow —
a buyer sees these before touching Run), `frontend-runtime`, `execution-timeout`,
`submit-timeout`, `workflow-load`, `selector`.

The harness does **not** stop at the first failure. A load-phase error does not
prevent it pressing Run, so one run reports every phase. `result.json` carries
`failure_classes` as an array.

### Artifacts

Written to `results/browser/<timestamp>-<workflow>/` (override with `--out`):

| file | what it is |
|---|---|
| `api_graph.json` | **the API graph the browser POSTed** — this is the diffing input other workstreams want |
| `prompt_post_body.json` | the full `/prompt` POST body (`prompt` + `extra_data` + `client_id`) |
| `result.json` | machine-readable verdict: status, `failure_classes`, every error with phase + origin, timings, outputs |
| `console.log` | every console message, page error, toast, dialog, failed request, tagged by phase and origin |
| `ws_events.json` | websocket traffic minus progress spam |
| `screenshot-fail.png` / `screenshot-final.png` | |

`--api-out <path>` additionally copies `api_graph.json` anywhere you like.

### Errors: what fails the run, and what does not

Fatal when they occur in the **load** or **run** phase: `pageerror`,
`window.onerror`, unhandled promise rejection, console message at error level,
PrimeVue error toast, any modal dialog, non-200 from `POST /prompt`,
`node_errors`, websocket `execution_error`, `execution_interrupted`.

**Boot-phase** errors (before the workflow is opened) are printed as `BOOT-NOISE`
and are not fatal by default — this install emits some on every page load
regardless of workflow. `--strict-boot` makes them fatal.

Every error is also classified by **origin**, because where it comes from decides
whether it is a product signal:

| origin | product signal? |
|---|---|
| `frontend-core` (`/assets/*`) | yes |
| `instaraw` (`/extensions/ComfyUI_INSTARAW/*`) | yes — our pack |
| `comfyui-asset` (a bare ComfyUI URL) | yes |
| `unknown` (no attributable URL) | yes, conservatively |
| `third-party-pack:<name>` | no — this pod's environment |

### The ignore-list

`tools/browser_harness/ignore.json` is a committed list of known-benign or
pod-specific errors, **one written justification per entry**, each verified
against the filesystem rather than assumed. Matched errors are downgraded to
`ignored`: they are still printed in the run log under the rule that matched
them, still counted in `result.json` `counts.ignored`, and still listed in full
in `result.json` `ignored`. Nothing is silently dropped.

* `--no-default-ignores` — ignore nothing, show the raw truth
* `--ignore-error <regex>` — ad-hoc rule on top of the committed list

`frontend-conversion` and `execution` failures are **never** ignorable, whatever
the list says.

Each rule carries a `scope`:

| scope | meaning |
|---|---|
| `benign` | happens on a stock ComfyUI including a buyer's, and is not a defect |
| `environment` | pod-only; a buyer following the NSFW bootstrap lacks the pack that causes it |
| `product-known` | a **real defect in what we ship**, ignored only so it does not make every run red |

Every run with a `product-known` match prints:

```
  !! 7 of the above are scope=product-known: REAL defects in what we ship,
     ignored only so they do not make every run red.
```

**This list should be empty. Making it empty is the point — and as of run 3
(2026-08-07) it IS empty.** The two entries it used to carry were fixed at the
source and their rules deleted (commit `73e0a2c`): the ten baked
`rgthree.compare._temp_*.png` refs are gone from the workflow (8 died with the
anatomy subgraph `b4f7359`, 2 reset on node 419 `4226580`), and the RPG
`console.error` was downgraded to `console.debug` in fix/run2. A later session
finding this list growing again should treat that as the signal it was designed
to be, not as normal.

### The interactive image selector

The shipped NSFW graph pauses mid-render on `#603 INSTARAW_ImageFilter` and waits
for a human to pick an image (600 s timeout, then it aborts the render). That is
deliberate and documented to the buyer. Two consequences:

1. A default full-render run **will** stall there. Use `--drive-selector` to do
   what the buyer does: wait for the popup, click an image, press Send. It
   asserts the Send button's real DOM `.disabled` property before and after the
   thumbnail click (`popup.js:179-181` sets it directly), recording
   `send_enabled_before_pick` / `send_enabled_after_pick` in `result.json`, and
   fails with `the buyer cannot proceed` if clicking a thumbnail does not enable
   Send. That is the shipped defect this guards against, so the check is a
   positive reading of buyer-visible state rather than a click that times out.
   On a shared server it only ever answers **its own** prompt — it checks
   `/queue` for its `prompt_id` first, because pressing Send on someone else's
   selector would hand their render an image they did not choose.
2. The popup is driven by a server broadcast that ComfyUI sends to **every**
   connected browser, so a render paused by someone else covers your page and
   swallows the Run click. The harness detects this before clicking, waits
   `--wait-for-idle-ui-ms` (default 90 s) for it to clear, and then exits `2`
   with an explanation. It will **not** dismiss it, because Cancel would abort
   somebody else's render.

### Stack traces are environment-dependent

The failing stack for the shipped blocker passes through
`ComfyUI-KJNodes/js/setgetnodes.js`, which monkey-patches `resolveOutput`.
KJNodes is installed on this pod and will **not** be on a buyer's. The same bug
will produce a differently-shaped stack there. Do not treat a differing trace as
a different bug — compare the error message and the raising frame
(`ExecutableNodeDTO._resolveSubgraphOutput`), not the whole stack.

### Loading path

Default `--load-mode ui` clicks the workflow in the Workflows sidebar — a real
buyer action. `--load-mode api` calls `app.loadGraphData` directly, and
`--allow-load-fallback` retries with it if the UI path fails. Whichever ran is
printed and recorded in `result.json` as `load_path_used`, so a run can never
quietly claim the UI path it did not take.

---

## 2. graph_diff

The sanctioned verification method. **Do not verify changes by hashing rendered
output** — run-to-run noise on this pipeline sits around 48.7 dB, below one 8-bit
level, so matching hashes are a strong attractor rather than proof. Three
separate confident-and-wrong "reproducible" verdicts were reached that way.

```bash
python3 tools/graph_diff/graph_diff.py BEFORE.json AFTER.json
```

Inputs are **API-format** graphs — either a bare API graph or a whole `/prompt`
POST body (the `prompt` key is unwrapped automatically). `browser_harness`
writes exactly this as `api_graph.json`.

Exit `0` = no differences (**the change is inert**), `1` = differences, `2` = usage error.

### The normal loop

```bash
# capture before
node tools/browser_harness/run.js -w OFMTech_NSFW --no-submit --api-out /tmp/before.json
# ...make the change, install it...
node tools/browser_harness/run.js -w OFMTech_NSFW --install OFMTech-NSFW/OFMTech_NSFW.json \
     --no-submit --api-out /tmp/after.json
# verdict
python3 tools/graph_diff/graph_diff.py /tmp/before.json /tmp/after.json
```

### What "constant-fold" covers — read this before trusting a result

Folding rewrites links that pass **through a node whose output is, per that
node's own Python source, exactly one of its inputs**. That is all it does. The
fold table is deliberately small and every entry cites the source it was read
from (`FOLD_TABLE` in `graph_diff.py`). Currently: `INSTARAW_BooleanBypass`
(verified against `nodes/logic_nodes/virtual_nodes.py` — `passthrough()` returns
`input_1..4` and ignores both BOOLEAN inputs entirely), `Reroute`,
`Reroute (rgthree)`.

It **does**: follow a link transitively through listed passthroughs with cycle
protection; drop the passthrough once nothing references it; report every fold.

It **does not**:
* evaluate arithmetic, string templating, wildcards or seeds
* simulate execution or propagate widget values downstream
* understand any `class_type` absent from the fold table — those are left alone,
  and if the name looks switch-like it is reported as an explicit **caveat**
  rather than silently skipped
* resolve bypass (mode 4) or mute (mode 2) — API format has no `mode` field. The
  frontend already removed bypassed nodes and rewired their links before this
  tool sees the graph. That is another reason to diff the API graphs the browser
  actually POSTed.
* prove anything about behaviour that depends on server state (file contents,
  RNG, wildcards, `IS_CHANGED` returning `NaN`)

So **"0 differences" means the two graphs submit the same work to the same nodes
with the same inputs.** It does not mean two renders will be pixel-identical, and
it cannot mean that.

### Options

| flag | effect |
|---|---|
| `--no-fold` | compare raw |
| `--include-meta` | also compare `_meta` titles (off by default: titles do not affect execution) |
| `--rename OLD=NEW` | explicitly map a node id in A to one in B, repeatable. Matching is by id; the tool never guesses at renames |
| `--json` | machine-readable |
| `--quiet` | verdict line only |

---

## Fixtures

| file | why it exists |
|---|---|
| `tools/fixtures/harness_known_good.json` | Trivial SD1.5 graph (7 nodes, 384x384, 6 steps, `v1-5-pruned-emaonly-fp16.safetensors`). The control: if this does not go green, the harness or the pod is broken, not the workflow under test. |
| `tools/fixtures/red_OFMTech_NSFW.json` | The shipped graph **as of commit `4d8a9ce`, before the blocker fix** (301 235 bytes, md5 `fa0a7af467ce6d6547805947c3b12d66`). A permanent known-failing case, so the harness can always be shown to still detect the thing it was built to detect. Do not "fix" this file. |
| `tools/fixtures/harness_selector_multi.json` | SD1.5 at `batch_size 4` feeding an `INSTARAW_ImageFilter` with `pick_list=""`, so the selector opens with **four** thumbnails and waits for a human. Built through the real frontend so litegraph did the link bookkeeping (preflight: 0 problems). Exists to exercise the multi-image Send-enable path, which the single-image path masks. |

Fixtures are copied into the ComfyUI workflows directory by `--install` and stay
there. They are harmless but they sit in the same list a buyer picks their
workflow from, so use `--cleanup-install` to remove them again when the run ends:

```bash
node tools/browser_harness/run.js -w harness_known_good \
  --install tools/fixtures/harness_known_good.json --cleanup-install
```

---

## Requirements

Node 24 + Playwright 1.62.1 from `/workspace/nsfw-fix/node_modules` (already
installed), Chromium in `/root/.cache/ms-playwright`, Python 3 (stdlib only), and
a ComfyUI reachable at `--url` (default `http://127.0.0.1:18188`, env `COMFY_URL`).
