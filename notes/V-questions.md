# TRACK V — judgement calls, and what I got wrong mid-run

## Things I got wrong, recorded because the brief asks for them

### 1. I ran two of my own drivers concurrently for about four minutes

The first attempt at the 2×2 stage was launched in a foreground shell that the
tool killed at its 2-minute limit. I read `ps` and concluded the Python child had
died with it. **It had not** — `timeout 1800 python …` survived the shell, and so
did a later `nohup … &` copy. For roughly four minutes two Track V drivers were
alive at once, both calling `POST /free` and both submitting.

`POST /free` only sets flags the worker consumes between prompts
(`drive.py`'s own docstring, and the behaviour Track A documented), so it cannot
corrupt a render already in flight. But one arm was submitted with
`queue_before = [1, 0]`, i.e. it queued **behind** another of my own arms rather
than running in isolation, and I cannot say from the record which of the two
drivers' `/free` the worker consumed when.

**What I did:** killed both, moved every arm whose record was written inside the
overlap window to `results/crash/V/arms_void/`, and re-ran them serially. Voided:
`V_ISO_d035_cpu_a`, `V_ISO_d080_cpu_a`, `V_ISO_d035_gpu_b`, `V_ISO_d035_cpu_b`.
Their re-runs carry the same names under `arms/`. Everything from that point on
goes through one process (`tools/run_v.py`), which is resumable so a stage can be
restarted without re-running recorded arms.

Two prompt_ids were executed by the server but never recorded by a driver:
`6309ef32-3b05-4426-8e5e-9ccc6637e130` and `439609a1-e1cf-44e6-8be2-b7afae47c241`
(both `success`, both the 46-token string with `device: cpu`). They are **not**
counted anywhere in `V-verify.md` — a run I did not record is not a result. I
note them so the server's history and my grid can be reconciled.

### 1b. And then I did it a second time, with `pkill`

Chaining stages with `pkill -f "run_v.py awkward clean sweep"` killed **the shell
that was running the pkill**, because that shell's own command line contains the
pattern. The compound command died before its second `pkill` ran, which released a
waiting loop early and started a second runner on top of the first — again.

Caught within ~90 s from `pgrep -fc`, killed by PID, and `V_P1b` — the only arm
whose render overlapped the second runner — was voided and re-run.
**Rule adopted for the rest of the session: manage processes by PID only, never
by pattern, and verify with `pgrep -af` immediately after every launch.**
`V_SEED_1111112_cpu` was submitted by the doomed runner and never recorded; the
directory was left without a `meta.json` so the resumable runner would re-run it
from scratch, which it did.

### 2. The bug I nearly walked into: the fix arrives with a second commit attached

`8d166e0` (`#114` denoise 0.80 → 0.35) landed one commit before the fix. The
brief calls it "a quality decision, not part of the fix", and the Phase 3
positive control is specified against `8d166e0^` — which carries **both** the old
denoise **and** the old device. Comparing that against HEAD therefore compares
two changes at once, and Track E's own 7/7-vs-9/9 evidence was gathered at
denoise **0.80**, on a graph snapshot (`results/r4/R4_CF15_filled`) that predates
the denoise commit.

So "does the crash survive the denoise change?" is a real question and nothing in
the record answered it. If denoise 0.35 alone had cured the failure, every green
arm under the fix would have been measuring nothing. I ran the 2×2 first for that
reason. It is in `V-verify.md` §2.

---

## Judgement calls

### Which graph the arms run

The proof set, the awkward set, the band sweep and the seed attack all run
**Track A's probe graph**: the shipping graph with `620:114.image` and
`620:111.reference` repointed at a frozen base image (`trackA_base137.png`), so
the SDXL half is skipped and each arm costs ~40–115 s instead of ~250–450 s.

Justification, and its limits:
* `620:106` feeds exactly one input, `620:114.positive`, so everything up to and
  including `620:137` is prompt-independent (`notes/CRASH.md`, "Efficiency note").
* It is the harness Track A used for its 40-arm band map and Track E used for the
  7/7-vs-9/9 result this session is testing, so my numbers are directly
  comparable to theirs.
* **It is validated the way `CRASH.md` demands**: the pre-fix graph crashes at
  `622:403` on it and the placeholder renders clean.
* **What it does not cover:** `#618`, the SDXL LoRA, is pruned out of the probe
  graph (nothing downstream of the frozen base reads it), so "both LoRAs" is only
  literally true on the full-graph arms. The frozen base was itself rendered with
  `#618 = lunaskye.safetensors`, so its effect is baked into the pixels, but the
  node does not run.
* For that reason there are also full 88-node arms (`V_FULL_*`), with a
  device-`default` control run **first** so a green full render cannot be
  over-read.

### Two mutations the full-graph arms need

* `619:603 INSTARAW_ImageFilter.pick_list = "0"`. The shipped graph pauses
  mid-render for a human to choose an image (600 s, then `send none` →
  `InterruptProcessingException`). `image_filter.py:133` short-circuits
  `send_and_wait` entirely when `pick_list` parses, so setting it to `"0"` picks
  image 0 without touching the image pipeline. R4's own crash arm did the same.
* Both LoRAs set on `#618`/`#116`. The shipped file ships them as `"None"`; the
  Phase 3 proof set requires them.

### `execution_cached` and what "cold" means here

Every arm does `POST /free {"unload_models":true,"free_memory":true}`, then polls
`/system_stats` until VRAM comes back, then submits — and then **checks
`execution_cached` in `/history` and re-runs the arm if it is non-empty**. No arm
in the grid was accepted warm.

### Check D had to be measured a different way than the brief describes

The brief and `PHASE3-spec.md` §2 both say to read the eyes stage out of
`/history`'s `executed` list. **This ComfyUI's `/history` has no such list** —
its `status.messages` carry only `execution_start`, `execution_cached` and
`execution_success`/`execution_error`, and `outputs`/`meta` cover output nodes
only. I verified that against Track E's stored history files as well as my own.

So Track V's driver opens a websocket on the arm's own `client_id` and records
every `executing` message, which is where this server does report per-node
progress. Check D is `"622:406" in executed`, `622:406` being the eyes stage's
`DetailerForEachDebug`. The full per-arm stream is kept in `arms/<ARM>/ws.json`.
A second, independent argument backs it up on successful arms: `505`'s image
exists and `execution_cached` was `[]`, and `505 ← 622:418 ← 622:401 ← 622:406`,
so `622:406` cannot have been skipped or served from cache.

### Where checks B and C are measured

On the **delivered frame** (`505 ← 622:418`) when there is one. A crashing arm
never produces one, so for those the only frame available is the `TAP163` tap of
`621:163` — the exact image handed to the failing detector. Each row says which.

### Every "the fix works" arm has a one-widget control at the same string

A green arm is only evidence if the identical arm with `620:110.device` back at
`default` goes red. Otherwise a fix that does nothing scores 100 %. So the grid
is built in pairs, and the awkward set in particular needed controls I nearly
forgot: `AW1` is 166 tokens, `AW3` 103, `AW2` 72, and **Track A's map stops at
50**. Nothing on the record says this instance fails at those lengths at all, so
`V_AW*_ctl` arms (same string, `device: default`) were added to make the awkward
results readable rather than decorative.

### The pass thresholds

* **B**: exact-`(0,0,0)` fraction ≤ 0.001, **and** the largest 4-connected
  component of any single exact RGB value ≤ 2 % of the frame, **and** that colour
  is not `(56,51,47)`. The contiguity test is deliberate: a modal-colour *count*
  can be large on a legitimately flat background, whereas the failure signature is
  a face-shaped **blob** of one exact value.
* **C**: `face_yolov8m.pt` max confidence ≥ 0.75 at `conf=0.1`. Track A's
  `arm_yolo.json` contains exactly four distinct values across all its arms —
  `0.466` (every crashing arm) and `0.894/0.895/0.896` (every clean one). 0.75
  sits in the middle of a gap that contains no observation at all.
* Detection replicates what `622:424` itself does: Impact-Subpack
  `subcore.py:319-325` calls `model(pil_rgb, conf=t, device=…)` and nothing else.

---

## Open questions for the owner / the pod

### Q1. On a ComfyUI without the `device` widget, this fix silently does nothing

`nodes.py:975-982` puts `device` in CLIPLoader's **`optional`** dict, and
`load_clip(self, clip_name, type="stable_diffusion", device="default")` defaults
it. ComfyUI passes only declared inputs, so on any build that predates the widget
the `"cpu"` in `widgets_values` is **dropped without an error** and the buyer gets
the shipped-broken configuration with no indication anything is wrong.

*My guess:* ship a minimum-ComfyUI-version note with the pack and have the
preflight lint assert `620:110.device == "cpu"` survives the round trip through
`/object_info`. *Lower-risk option taken here:* none needed — this is a packaging
concern, not something Track V can change without editing the workflow.

### Q1b. One Phase 3 criterion is NOT met, and I did not try to meet it

`PHASE3-spec.md` §4 lists, among the things that kill a candidate fix:

> A pass that only reproduces on one instance. **Two, minimum, one of which was
> shown able to fail.**

**Track V validated on one instance.** `:18188` is the only reproducer anyone has
found — Track E stood up four ComfyUIs from the same directory (`:32000`–`:32003`)
and none of them would fail under any configuration, and Track D's `:31910` does
not fail either. So a second instance is available only in the useless direction:
it could show the fix does no harm on a healthy server, not that it repairs a
sick one.

I judged that a fifth non-reproducing instance was not worth an hour of GPU
contention against the 60 arms that were actually discriminating, and that
starting one while three ComfyUIs already share this GPU risked the run. **So this
criterion is open, and it should not be recorded as met.** The pod session should
close it on a second box that is first shown able to fail.

### Q2. The fix is a workaround and the underlying instability is untouched

Nothing in this session made `620:114` stop being bistable; it moved the
conditioning far enough that this instance lands on the good side. Track E is
explicit about that and I found nothing to contradict it. The second defect —
`622:403 MaskBoundingBox+` turning "detector found nothing" into a `RuntimeError`
rather than a message a buyer can act on — is also still there, and the fix does
not address it. Track C's guard remains worth having *in addition*, on the
understanding that a fired guard is a failure report, not a pass.

### Q3. `results/r4/R4_CF15_*` is no longer the shipping graph

Track A's and Track E's probe graphs are built from `R4_CF15_filled/api_graph.json`,
which differs from a fresh conversion of HEAD in five inputs — including
`483.prompt_batch_data`, the SDXL prompt that produces the base image. Track V
rebuilt its probes from freshly converted HEAD/`8d166e0`/`8d166e0^` graphs for
that reason. Anyone re-using the `mk.py` in `results/crash/A/tools/` should know
it is pinned to a graph that is now three commits stale.
