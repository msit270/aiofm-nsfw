# TRACK A — judgement calls, corrections, and things I am not sure of

## Judgement calls made without asking

### 1. I did not create a branch. I committed onto `trackB-crash-grid`.
`git worktree list` shows **one** worktree, `/workspace/nsfw-fix`, and it was
already checked out on `trackB-crash-grid` when I started (the session snapshot
said `master`, so somebody switched it under me). Another agent is working in
this same directory. `git checkout -b trackA-…` would not have changed any files,
but it would have redirected *their* next commit onto my branch, and any
`git checkout` they ran would have yanked files out from under me mid-render.
**Lower-risk option taken:** stay on whatever branch is current, and only ever
`git add` paths that are unambiguously mine — `results/crash/A/**` and
`notes/A-*.md`. If the owner wants Track A on its own branch, the commits are
contiguous and trivially cherry-pickable.

### 2. Arms branch from the stored `R4_CF15_filled` API graph, not from a fresh
conversion of the workflow.
The brief says convert the frozen JSON and mutate in memory. I used the *already
converted and already submitted* API graph from the arm that actually crashed
(`results/r4/R4_CF15_filled/api_graph.json`, `workflow_sha256 a811b5d6…` recorded
in its `meta.json`, matching `sha256sum OFMTech-NSFW/OFMTech_NSFW.json` today).
Reason: it is a stricter control than a re-conversion — it is byte-for-byte the
graph with a recorded crash, so any difference in my result cannot be a
conversion difference. The workflow JSON was not opened for writing at any point.

### 3. The base render is truncated, not full.
`A0_base_tap137` prunes the graph to the ancestors of `620:137` plus a
`SaveImage`. This is safe because `620:106` is **not** an ancestor of `620:137` —
verified by walking the submitted graph, not from the note: the ancestor set of
`620:137` is 47 nodes and contains no `620:10x`. So the base image cannot depend
on the prompt under test.

### 4. I added a `SaveImage` tap on `621:163` to **every** arm, not just the A4 pair.
Risk considered: an extra output node changes the executor's node ordering, and on
a crashing arm the tap might or might not fire before `622:403` raises. It fired
on the crashing gate arm, so A4 came out of the same run as the crash rather than
a re-creation — which is strictly better evidence than a separate tap-only run
would have been. The tap adds no input to any existing node, so it cannot change
what any other node computes.

### 5. The A3 "different content" strings include a non-face and a non-visual one.
The brief asks for ≥2. I wrote 4 at 25 words: two are *other people's faces*
(the fair same-length contrast — the face pass still has a face to converge on),
one is a rusting locomotive (no face at all), one is a sentence about a committee
meeting (no visual content at all). The last two are bounds rather than fair
contrasts and are labelled that way in the results.

---

## Things I checked rather than assumed

* **That the tokenizer is not lumina2.** `620:110` says `type: lumina2`, and that
  is not what runs. See `A-length-vs-content.md` §Method — `detect_te_model`
  wins, the file is a Qwen3-4B, the tokenizer is `ZImageTokenizer`. If I had
  counted tokens with a Gemma2 or a CLIP tokenizer every number in the ladder
  would have been wrong.
* **That there is no 77-token limit on this path.** `max_length=99999999`,
  `pad_to_max_length=False` (`comfy/text_encoders/z_image.py:11`). The crashing
  string is 46 tokens including the 8-token chat template. So a "prompt too long
  for the encoder" story is dead before the first render.
* **That the offline YOLO call matches the graph's.** `subcore.py:319-325`
  `inference_bbox` is `pred = model(image, conf=confidence, device=device)` on a
  PIL image; `yolo_probe.py` makes exactly that call on exactly that `.pt`.

---

## Open / unsure

_(filled in as the run proceeds)_
