# R2 — judgement calls and open questions

I was told not to stop and ask, so each of these is a decision I took, with the reasoning
and the lower-risk option I chose. Anything the owner disagrees with is cheap to redo.

---

## 1. I set the LoRAs and typed the prompt through the real UI, not the widget API

**Decision:** the LoRA values were set by clicking the combo widget on the canvas and then
clicking `lunaskye.safetensors` / `luna.safetensors` in the menu litegraph opens, and the
prompt was typed into the panel's textarea and committed by blurring it.

**Why it matters:** setting `widget.value` in JavaScript would have produced identical
screenshots and identical JSON, and would have proved nothing about whether a buyer *can*
set them. The menu route also incidentally proves the files are visible to the server —
if `lunaskye.safetensors` were missing, the menu would not list it and the gate fails with
`"…" is not offered by the widget. Offered: [...]`.

**Verified rather than assumed:** after each click the value is read back out of the graph
(`n.widgets.find(w => w.name === 'lora_01').value`), and the prompt is read back out of
`#483`'s `prompt_batch_data` widget, not out of the textarea I typed into.

## 2. I collapsed `#483` for exactly one screenshot

The prompt panel's DOM element overhangs its own node by ~41 graph units and covers the
top of `#618`/`#116`'s title bars, which is where litegraph draws the title text (§5.3 of
the report, measured). Without collapsing, the LoRA screenshot shows the values but not
which nodes they are on.

**Lower-risk option taken:** collapse is a normal UI action, it is undone immediately in
the same run, and **the workflow is never saved**. The alternative — hiding the element
with CSS — would have been staging the photograph, which is exactly what this project's
standard forbids.

If the owner would rather have no UI state touched at all, the fallback artifact is the
`-04-both-lora-stacks` frame without the collapse: values legible, titles obscured.

## 3. I hid the minimap for the canvas screenshots

The minimap is a floating panel covering ~250×200 px of the canvas. For a screenshot whose
entire claim is "nothing on this canvas is red", a panel that could be covering a node is
not acceptable. It is turned off through ComfyUI's own setting (`Comfy.Minimap.Visible`)
and the run logs that it did so, including the previous value.

## 4. The whole-graph screenshot exists twice, at two viewport sizes

At 1920×1080 the whole graph fits at scale 0.23, and litegraph stops drawing node titles
and widgets below 0.5 — so the honest "everything is visible" shot is also an unreadable
one. I added a second capture at 5760×3240, where the same fit lands at scale 0.78 and the
canvas is legible. **Both are kept.** The small one is what the gate takes on every run;
the large one is the one to actually look at.

## 5. I answered a stalled selector over HTTP once, and it is not part of any result

When my own harness bug (§5.2) stranded a render at `#603`, I answered it with the same
POST the browser makes:

```
curl -X POST http://127.0.0.1:18188/instaraw/interactive_message \
     --data-urlencode 'response={"unique":"958955","selection":["0"]}'
```

**Why:** the alternative was 600 s of a shared queue held by a render nobody would answer.
**What it is not:** evidence. That render (`8e8aa729`) is not cited as a pass anywhere; it
is the one that later died at `622:403` during the server's bad window. Every result in the
report comes from a browser pressing Send.

I did **not** use `POST /interrupt` or `POST /queue {"clear":true}` at any point, on any
instance.

## 6. Both clean instances were started with `--reserve-vram 16`

They share one GPU with the live instance other agents render against. Reserving 16 GB is a
politeness margin, not a requirement, and it is a difference from how a buyer would start
ComfyUI. It cannot change whether the graph converts or which nodes register; it could in
principle change offloading behaviour and therefore render time. Render times in the report
should be read with that in mind.

## 7. Open — for whoever picks this up

1. **`ComfyUI_Swwan` is installed by the NSFW bootstrap.** WS2's ignore-list justifies six
   `preloadError`s and three `rgthree.*` double-registrations as "pod-only, a buyer
   installing the NSFW pack does not have this". Both my clean installs — built by running
   the live bootstrap into an empty tree — **do** have it, and do emit them. Either the
   justification or the pack list is wrong. I did not change either; it is another
   workstream's file.
2. **The six `rgthree.compare._temp_*` 404s are still in the shipped bytes** and now
   confirmed buyer-visible on a clean install rather than inferred from the JSON.
   WS2 §3.2 says how to make them go away.
3. **A DOM widget does not recompute its visibility while its node is culled.** Collapsing
   and re-expanding a node off-screen leaves its panel blank until something forces a draw.
   Harmless for the gate (it frames the node first), but it is the kind of thing that will
   look like "the prompt panel disappeared" in a support ticket.
4. **`tools/verify_buyer_path.sh` hardcodes ports 38080 / 28188 / 39997.** Two agents ran
   it at once today and R5's `bad-archive` case hit my mirror. My runs are defensible
   (report §4b) but the next pair may not be. `c_nodes` is the dangerous one: it binds
   28188, and if the bind fails its readiness probe succeeds against *someone else's*
   ComfyUI, so "all 51 node types registered" can be reported from an install you did not
   make. Deriving the defaults from `$$`, or refusing to run without explicit ports, would
   close it.
5. **Nothing tested is published.** Live HF serves `3f6d0f2f…`; the artifact I passed is
   `5f2a0f2b…` in `dist/`. Two cuts have never been uploaded.
