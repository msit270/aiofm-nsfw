# TRACK E — questions, judgement calls, and things I got wrong

## Things I got wrong during the session, in order

Every one was killed by an arm, not by thinking harder. Recorded so the pattern
is visible.

1. **"The probe pack's CUDA synchronisation is suppressing a stream-ordering
   race."** My first hypothesis after `:32000` failed to reproduce. Both `:18188`
   and `:32000` log `Using async weight offloading with 2 streams`, and my
   wrappers force syncs by reducing tensors. **Refuted** by `:32001` — same tree,
   probe pack removed, still clean 2/2.

2. **"It is full-load vs lowvram."** The `:18188` crashing arm full-loaded
   Lumina2 (`lowvram patches: 0`) while my clean arm loaded it partially
   (39 patches). **Refuted** by `E_fullvram_crashstring`: same server, 48.7 GiB
   free, `full load: True`, still clean.

3. **"It is `--reserve-vram 16`", because that is Track B's reproducing config.**
   **Refuted** by `E_rv16_*` on `:32002` — clean. (And `:31910` has the flag and
   does not reproduce, while `:18188` lacks it and does.)

4. **"The CPU-encoder cure must be the memory timeline, not the conditioning
   values, because E5's rounding perturbation did not cure it."** I wrote that
   inference down and then `E18_split_crash` refuted it two arms later: with a
   *second* CPU encoder feeding only `620:106` and the GPU encoder still loaded
   and running, the crash is still cured, 2/2. The values are what matter. I have
   left the wrong inference visible in `E-rootcause.md` §4 rather than quietly
   deleting it.

5. **The `L_w17`/`L_w16` strings I typed by hand into `e2a_save_conds.py` are off
   by one word** against Track A's `strings.prefix(n)` — mine are 29 and 28
   tokens where Track A's are 30 and 29. Nothing in this file rests on them
   (the 30-token content check used `A3_gardener_w17`, which does match Track A
   at 30, and every rendered arm used Track A's own `strings.py`), but do not
   quote those two rows of `conds_meta.json`.

## Correction I am making to another track's file

**`notes/A-length-vs-content.md`'s NaN refutation is not sound.** Track A argues
that a NaN in `620:114`'s output would have made `620:111 ImageColorMatch+`'s
global mean NaN, `nan_to_num` would have flattened the whole frame, and the frame
is not flat, therefore `620:114` "emitted honest zeros, not NaNs". The reasoning
about `620:111` is right; the conclusion is not, because
`ComfyUI-Impact-Pack/modules/impact/core.py:405` runs
`utils.tensor_resize(refined_image, w, h)` **inside** `enhance_detail`, and
`utils.py:129-155` implements it through
`np.clip(255.*x, 0, 255).astype(np.uint8)`. A NaN is turned into an exact `0`
there, one line before `620:114` returns. So `620:114`'s output is honest zeros
**whether or not** the decode was NaN. I have not corrected Track A's file — that
is the coordinator's call — but nothing downstream should treat NaN as excluded.

## Judgement calls

* **I did not restart `:18188`.** It is the only reproducer this session could
  submit to, and restarting it with a probe pack was the one move that would have
  answered "NaN or real zeros" directly. Against that: three separate fresh
  servers of mine, from the same tree, do not reproduce it at all, so there was a
  real chance a restarted `:18188` would not either — and then the project would
  have no reproducer and no measurement. I took the lower-risk option and banked
  the arms that need a live reproducer instead. **I think this was right, but it
  is the call most worth second-guessing, and it is the reason questions (a) and
  (b) come back partly unanswered.**
* **`gdb` injection into the live process was blocked** by the permission system.
  I did not attempt to work around it.
* **I ran my instances out of `/workspace/ComfyUI` itself** rather than a fresh
  install, deliberately: it removes "different custom-node versions" as an
  explanation, which is what Track D's non-reproduction could not rule out. The
  cost is that my server shares `input/` and `custom_nodes/` with `:18188`; I
  gave it its own `--output-directory`, `--temp-directory` and an in-memory DB
  so nothing was written into the shared tree. **My debug pack lives in
  `/workspace/trackE/custom_nodes/` and is reached through
  `--extra-model-paths-config`; `/workspace/ComfyUI/custom_nodes` was not
  touched.**
* **I POSTed `/free` to `:18188` and sent it one trivial `LoadImage` →
  `PreviewImage` prompt.** `/free` alone does nothing until the prompt worker
  wakes (`main.py:249` blocks in `q.get(timeout=1000.0)` when idle), so the nudge
  prompt is what actually made it unload. It writes one preview into `:18188`'s
  temp dir and loads no models. Flagged because it is a POST to a shared server,
  which the brief permits for `:18188` only.
* **`pkill -f "port 32002"` matched and killed my own shell** (exit 144). No
  other process was affected — `:28191` (pid 144284) and `:31910` (pid 173610)
  were verified still running in `nvidia-smi` immediately afterwards, and their
  command lines do not contain that string. I stopped using `pkill` after that
  and killed by explicit pid.
* **I killed one of my own leftover servers by pid (201313)** after discovering
  that `$!` from a `nohup ... &` had reported the wrapper, not the python
  process, so an earlier `kill` had missed it and it was still holding 20 GB.
  Verified the cmdline was mine (`--port 32000`) before killing.

## Questions for the coordinator

1. **Do you want `:18188` restarted with instrumentation?** It is the one arm
   that closes "NaN or real zeros", and it costs the reproducer if the crash does
   not survive a restart. My guess: **yes, but only after someone has a second
   reproducing instance in hand** — `:28191` currently reproduces and is Track
   B's; if Track B is finished, restart *that* one with the probe pack and keep
   `:18188` pristine. Exact recipe: drop
   `/workspace/trackE/custom_nodes/trackE_probe/` into the server's
   `custom_nodes` (or pass `--extra-model-paths-config /workspace/trackE/paths.yaml`)
   and read `/workspace/trackE/logs/probe*.jsonl`. It registers no nodes and
   changes no numerics beyond inserting reductions.
2. **Is the `620:110.device = "cpu"` workaround acceptable to ship?** It is one
   widget, it cures the crash 7/7 on the only reproducer, it produces a healthy
   image at the noise floor, and it costs roughly +14 s per render on this box.
   My guess: ship it as an interim mitigation *and* fix `622:403`'s empty-mask
   guard, because the workaround has not been shown to cover the `622:398` route
   and a buyer whose encoder is on the GPU by default is still exposed.
3. **Should the bands be re-mapped on the CPU encoder?** Track A's map
   (30–32, 44+) was measured entirely with the GPU encoder. If the cure works by
   moving the conditioning off a bad numerical path, the CPU encoder may have its
   own bands elsewhere. I tested two points (30 and 46) and both are clean. Two
   points is not a map. My guess: worth a 20-arm sweep on the pod, cheap at
   ~70 s/arm with Track A's probe.
4. **`aiofm_setup.sh` builds sageattention and nothing enables it.** Logged as a
   product issue, not acted on. My arms show sage does not *create* a failure on
   a clean instance, but they cannot say whether it removes or moves the bands,
   because Track E's instances have no bands.

## What I would do next, in order

1. Instrument a reproducing instance and read the tensor inside `620:114` —
   `KSAMPLER.sample`'s output latent first, then `VAE.decode`'s output, then the
   image entering `tensor_resize`. One arm answers "NaN vs saturated-negative vs
   genuinely black" and tells you whether the sampler or the decode is at fault.
2. On a reproducing instance, bisect the sampler: run `620:114` at `steps 1..8`
   (via the arm graph, not the file) and find the first step at which the latent
   goes bad. That converts "somewhere in an 8-step loop" into a single call.
3. On a reproducing instance, try the attention backends the brief asked for —
   `--use-pytorch-cross-attention`, `--use-split-cross-attention`,
   `--use-quad-cross-attention`, `--use-sage-attention`. I could not: my
   instances have nothing to remove. This is still the cleanest test of "is it a
   kernel".
4. Sweep the perturbation size between E5 (`mean ~6e-7`, does not cure) and E4
   (`mean 9e-6`, cures) to find the threshold, using `ConditioningAverage`
   against a *slightly different* conditioning at strengths near 1.0. If there is
   a clean threshold, that is the number that characterises the instability.
