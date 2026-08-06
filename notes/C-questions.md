# TRACK C — questions, judgement calls, and things I am not sure about

Format per `CLAUDE.md`: best guess + reasoning + the lower-risk option taken.
Nothing here blocked the work.

---

## Q1. Is a silent degraded image actually better than a crash? **This is yours, not mine.**

**The question.** C1 turns `RuntimeError` into "an image with undetailed eyes,
`status: success`". If the detector fails because the face pass wrecked the face,
the buyer gets a wrecked face and no error.

**My guess:** yes, ship the guard — **but only together with a visible signal**
(C1b), never alone. A pipeline that dies on a legal input is unsellable; a
pipeline that degrades on a rare input and says so is normal. But
`HANDOFF.md` §6.1 is the counter-argument in your own words: on this exact
pipeline, "a flat grey face with `status: success`" cost six arms and two
confident wrong conclusions. Silence is expensive here specifically.

**Lower-risk option taken:** I designed the guard *and* the signal, ranked the
signal as a companion rather than an optional extra, and put the trade-off in its
own section (`C-fix-design.md` §6) in plain language rather than burying it.
I did not apply either.

## Q2. Was I right to keep it a graph change rather than an INSTARAW node?

**My guess:** yes, strongly. `aiofm_setup.sh:1165-1166` leaves an existing
INSTARAW install alone by design, so a *new node type* means a returning buyer
opens the workflow to a red node and a dead graph. Impact Pack is already a hard,
pinned dependency carrying 10 of this graph's node types and it already ships the
exact two nodes. A new INSTARAW node would reimplement a one-line function.

**Where I could be wrong:** if you would rather not depend on Impact Pack's
`ImpactConditionalBranch` staying lazy across future pins. It is pinned at
`429d0159`, so it cannot move under us without someone changing the pin — but a
future pin bump is a thing that happens. If that worries you, C4b (making our own
`INSTARAW_ImageSwitch` lazy, no new type) is the version we control.

## Q3. I did not write the "warn the buyer in the filename" patch.

The clean way to put the warning where a buyer will see it is to switch
`505 SaveImage.filename_prefix` so a skipped-eyes render lands as
`..._NOEYES_...`. That needs a new `STRING` output on host node `622` plus an
`INSTARAW_StringSwitch` inside the subgraph — a change to the host node's output
list, which is a bigger review than the guard itself.

**Judgement:** out of scope for a first commit, and mixing it in would make the
inertness proof harder to read. Recorded as a follow-on. C1b (`PreviewAny` on the
boolean) is the cheap version that at least makes it machine-checkable from
`/history` and visible in the UI.

## Q4. Can the batch at `622:431` ever exceed 1? **Not fully proven.**

`635 EmptyLatentImage` has `widgets_values [896, 1152, 1]` with only width/height
linked, so `batch_size` is 1. I walked the path from that latent to `622` and
found no node that multiplies the batch — `619:601`/`619:602` are list↔batch
conversions and `619:603 INSTARAW_ImageFilter` is a user-driven *subset* selection
of what it was given. **I did not exhaustively prove that no configuration can
raise it**, and `HANDOFF.md` §8 mentions the selector behaving differently "with
>1 image", which is about the selector UI but left me unwilling to call it closed.

**Why it matters:** with a mixed batch, `check_lazy_status` results are unioned
(`execution.py:490-492`), both branches become strong links, and the crash
returns. **Lower-risk option taken:** I designed C3 (the eager fallback-mask
version) that survives it, ranked it below C1, and said explicitly not to adopt it
speculatively.

## Q5. Will the frontend accept a `*`-typed *output* into an `IMAGE` subgraph output slot?

I could not settle this from source and I did not run the browser harness (it
would touch a server another track owns). The server side is settled —
`comfy_execution/validation.py:28-30`. The file already carries `*`-typed
**inputs** with live links in two places (`481.source`, `619:604.input_1`), but no
`*` **output** that is connected to anything.

**Lower-risk option taken:** flagged it as C1's one real risk, made it proof step
P2 (9 s, no GPU, `--no-submit`, nothing reaches the server), and pre-wrote the
fallback (C2b, `easy imageIndexSwitch`, strictly `IMAGE`-typed both sides) so the
next session does not have to redesign under time pressure.

## Q6. `properties.ver` on the two new nodes: `8.25.1` or `8.28.3`?

The installed Impact Pack's `pyproject.toml` says `version = "8.28.3"` at pin
`429d0159`; every Impact node already in the workflow records `"ver": "8.25.1"`.
The field is cosmetic — API export carries only `class_type`, `inputs`, `_meta`.

**Taken:** `8.25.1`, matching the file's existing nodes, so ComfyUI-Manager does
not start reporting a mixed-version graph. Say the word and it is a one-token change.

## Q7. Git: I committed to `trackB-crash-grid`, not a new branch.

`CLAUDE.md` says "git branch, one commit per change". When I started, the worktree
was on `trackB-crash-grid` with another track's uncommitted work in `results/`
and `tools/`. Creating a branch would have moved HEAD under two agents running
measurements, and their next commit would have landed somewhere they did not
expect.

**Taken:** stayed on the current branch and committed **only** `notes/C-*.md` by
explicit path — nothing else staged, no other track's files touched. If you would
rather this lived on its own branch, it is two files and cherry-picks cleanly.

## Q8. Things I deliberately did not do

* Did not edit `OFMTech-NSFW/OFMTech_NSFW.json` — not one byte. The patch was
  generated and validated against a copy in the session scratchpad.
* Did not apply any patch to `ComfyUI_essentials` or anything else under
  `/workspace/ComfyUI/custom_nodes/`, and installed nothing.
* Did not POST to either server. The only network call was
  `GET 127.0.0.1:18188/object_info`.
* Did not run the browser harness (it drives a real browser against a server
  another track owns), and did not render anything.

## Q9. One thing I would want checked that nobody has asked for

`622:403 MaskBoundingBox+` has `padding 0` and its `MASK`/`IMAGE` outputs
unconnected (`outputs[0].links: []`, `outputs[1].links: null`) — only the four
`INT`s are used. It is being used purely as a bbox calculator. If that is all it
is for, `ImpactCount_Elts_in_SEGS` plus Impact's own SEGS geometry would do the
same job from a pack that already guards emptiness, and the essentials dependency
on this path could go away entirely. That is a bigger rework than the crash fix
and I did not design it — noting it because it is the version where the bug
becomes structurally impossible rather than caught.
