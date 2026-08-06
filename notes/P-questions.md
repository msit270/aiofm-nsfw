# TRACK P — judgement calls

Written as I went, with my best guess and the reasoning, per the working rule.
Nothing here blocked; I took the lower-risk option each time and moved on.

---

## 1. `PACK_TOP` was already fixed. I did not re-fix it.

The brief said "fix `PACK_TOP` so the archive name and the unpack directory
match." Commit `310621c` already did this, and the previous artifact already
unpacked to `AIOFMTech-NSFW/`.

**Taken:** confirm and report it as already-done rather than manufacture a change.
Inventing a no-op commit to match the brief would have been the dishonest option.

**Residual uncertainty I am flagging rather than hiding:** I saw the assertion
*pass*, I did not see it *fire*. My evidence that it would fire against a
mismatch is R5's recorded negative control (`notes/R5-package.md:233-235`), not
my own observation. If the owner wants that re-proved on this build it is one
command — build with `OUT=…/OFMTech-NSFW.tar.gz` and watch it refuse.

---

## 2. How the two timing arms were built

**Options:** (a) patch `620:114.inputs.denoise` directly in the API graph;
(b) patch the litegraph `widgets_values` and convert through the real browser
frontend.

**Taken: (b).** Slower, but it exercises the same `graphToPrompt` path the buyer's
Run button uses, so a widget-order desync — the trap the project has been bitten
by — would show up as extra diff lines instead of being bypassed. It did not:
both pairs diff to exactly one input.

A control fell out of this that I did not plan and am glad of. Re-serialising the
committed workflow with **no** patch reproduced sha256 `f5bed596…7fd8`
byte-for-byte. So the builder is provably neutral, and each arm differs from the
shipping file by exactly one widget value with no serialiser drift folded in.

---

## 3. Latin square rather than A/B/A/B

Cold render time here is mostly model loading, and the GPU is shared with **two
other ComfyUI servers** (`:18188` Track V, `:31910` Track D). A block-ordered run
would confound arm with whatever those two were doing.

**Taken:** three arms × three rounds, rotating order, so each arm sits in each
position exactly once. That balances monotone drift and position exactly. I also
sample every other process's GPU memory and `vram_free` at submit time, so a slow
run can be checked against contention instead of explained away.

---

## 4. Buyer-path verification deferred until after the timing sweep

`verify_buyer_path.sh prepare` rsyncs a ComfyUI tree and `happy` runs the real
installer. That is heavy disk I/O, and cold render time is dominated by loading
models off disk.

**Taken:** run them strictly after the sweep. Running them concurrently would have
saved ~20 minutes and contaminated the one number this track exists to produce.

---

## 5. `n = 3` per arm — is it enough?

Honestly: it is enough to support a **null** result and not enough to support a
small positive one. If the denoise delta is genuinely ~0.4 s (the warm prior),
n=3 against a cold-load spread of tens of seconds will show "indistinguishable
from zero", which is the expected and useful answer. If something *had* shown a
large delta I would have needed more runs before believing it — and per the
brief, a large delta is a reason to suspect the measurement anyway.

The verdict I report is therefore framed as a **bound** ("the effect is smaller
than X, where X is the within-arm spread"), not as a point estimate.

---

## 6. Which buyer-path cases to run

The owner named three: no token, bad archive, happy path. `verify_buyer_path.sh`
also has `gist`, `bad-token`, `prepare` and `nodes`.

**Taken:** run the three named, plus `gist` (pure network, no cost, and it proves
the bootstrap I am testing is the one actually live), plus `prepare` (a
precondition of `happy`) and `nodes` (the only check that the installed pack
actually registers every node type — an installer can exit 0 and still leave a
graph that will not load). `bad-token` is reported if run but is not one of the
three.

---

## 7. Port discipline for the `nodes` case

`verify_buyer_path.sh` defaults its ComfyUI to `28188`. My instructions reserve
`34000-34099` for any ComfyUI I start.

**Taken:** override `WS5_NODE_PORT` into the assigned range and confirm the port
is free before binding, failing loud rather than probing whatever answers there.
`:18188` is never contacted by any of this; the happy path is additionally pinned
to a dead `COMFYUI_PORT` so the installer's restart stage cannot reach the live
supervisor-managed instance.

---

## 8. The hardlink risk in `prepare`, accepted with eyes open

`c_prepare` hardlinks `/workspace/ComfyUI/models` (Track V's tree) into the test
target. If the installer ever wrote in place, it would write through to the live
models a running server is using.

**Taken:** accept, because the script's design already handles it — downloads go
to a temp file and rename, which replaces the link rather than the file, and the
script fingerprints the live models tree before and re-checks after. I verify
that fingerprint comes back clean and report it. The read-side rsync is
read-only against Track V's tree and cannot disturb the running process; the only
cost to them is a brief I/O blip, which is why it happens after my sweep and not
during it.

---

## 9. `/free` is racy, and the project's rule about it is right for the wrong reason

`HANDOFF.md` says to confirm `execution_cached: []` rather than trust the `/free`.
That rule is correct. The mechanism turns out to be worse than "the worker
consumes it later":

- `server.py:976-981` — `/free` only calls `set_flag(...)`. It never frees anything.
- `main.py:284-296` — the flags are read **after** a prompt executes, and that is
  the only place `unload_all_models()` and `e.reset()` are called.
- `execution.py:1154-1159` — `q.get(timeout)` only returns `None` (and so only
  lets the worker reach `get_flags()`) **when it was given a timeout**.
- `main.py:242,246` — a timeout is set only while `need_gc` is true, i.e. for
  `gc_collect_interval = 10.0` seconds after a render.

So on an idle server the worker is parked in `q.get(timeout=None)` and **a
`/free` can sit unconsumed indefinitely**. Post it more than ~10 s after the last
render and the next submission may run warm; the flag is then consumed *after*
that render.

I hit this: my first node-timing pass had one arm come back `cold=False` despite
a 200 from `/free`. My main 9-run sweep got 9/9 cold — partly because its
`/history` polling happened to land each `/free` inside the 10 s window. **That
was luck, not design.**

**Taken:** post `/free`, then wait past `gc_collect_interval` and confirm the
unload actually happened via `torch_vram_free` before submitting, and
**discard and re-run any arm that still comes back non-cold**. Every number in
`P-package.md` is from a run confirmed cold this way.

**Recommendation for the next session:** whatever driver you use, do not treat a
200 from `/free` as meaning anything at all. Either post it within ten seconds of
the previous render finishing, or verify and retry.

---

## 10. Question I could not answer from here

**Is `317 s` the right ballpark for a cold render on this pod at all?** R1
recorded 270.5 s cold for the same graph, but on a different server
(`:18188`, `/workspace/ComfyUI`) and with three ComfyUI processes now sharing the
GPU rather than one. I have no way to separate "this tree is slower" from "the
box is busier" without taking the other tracks offline, which I will not do.

**Best guess:** contention, not a tree difference — the arms are internally
consistent and the absolute level is not what the comparison rests on. Every
number I report is a **within-sweep** comparison for exactly this reason, and the
absolute figures should not be quoted to a buyer as "the render takes N seconds"
without a quiet box.
