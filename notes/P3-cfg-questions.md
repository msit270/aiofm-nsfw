# P3-CFG — judgement calls

Written while answering "is `cfg = 1` on the Z-Image detail passes a constraint
or an accident, and what should happen to the negative prompts beside them".
Everything here is a decision I took without asking, with the reasoning and the
lower-risk option I chose. Nothing in the graph was changed.

---

## Q1 — Which raised cfg values to test

**Chose 1.5 and 3.0, against a cfg 1.0 reference.**

Reasoning. Two things needed showing and they want different step sizes.

- **1.5** is the smallest raise anyone would plausibly try, and it is the value
  that turns up in third-party Z-Image-Turbo guides. If a gentle nudge were
  survivable, this is where it would show. It is also the cheapest possible
  version of "the negative now applies", which is the thing the owner actually
  wants to see.
- **3.0** is the bottom of the range ComfyUI's own **base** Z-Image template
  documents (`image_z_image.json`, MarkdownNote `#86`: `- Steps: 30~50\n- cfg:
  3~5`). It is exactly the number a buyer would land on if they read Z-Image
  documentation without noticing which variant they have. Showing what that does
  is more useful than showing an arbitrary large value.

I did not sweep. The brief allowed two or three values per stage and a sweep
would not add anything a distilled model does not already tell you at two
points.

## Q2 — Isolated re-execution of each detailer instead of four full pipeline runs

**Chose isolated.** One full pipeline run at the shipped settings produced the
three intermediate images that feed `#114`, `#165` and `#406`; every arm then
re-runs only the node under test, from that same image, with the same fixed
seed.

Reasoning. In the full pipeline the three passes are in series — `#114` feeds
`#165` feeds the eye stage — so changing cfg on `#114` moves the input to the
other two and you can no longer attribute anything. Isolating removes that
confound entirely and makes each arm cost one detailer pass instead of a
five-minute pipeline. On a queue shared with two other agents that also matters.

**The cost, stated plainly.** The tap between the full run and the isolated arms
is an 8-bit PNG, so the isolated arms start from a quantised copy of the tensor
the pipeline would have handed over. That makes the isolated cfg-1 arm not
bit-identical to the full run's own output. It does **not** affect any
comparison in this report, because every arm — including the cfg-1 reference —
goes through the identical 8-bit input. Comparisons are arm-to-arm, never
arm-to-full-run.

## Q3 — What "negative present" means for `#165` and `#406`, whose negatives are empty

**Rendered both the shipped state and the buyer's plausible action.**

The brief asked for "cfg 1 with the negative present (the shipped state)". For
`#165` and `#406` the shipped negative is `""`, so the shipped state and the
"negative present" state are not the same thing. Rather than pick one I ran
both: the shipped empty negative, and the same string `#105` carries, which is
what a buyer would paste in if they decided the mouth or the eyes needed
protecting too.

## Q4 — Whether to use the empty-negative arm at cfg 1 as proof of inertness

**Rendered it, but it is not the proof and the report does not lean on it.**

The project bans hash comparison of rendered output as a verification method,
and "render twice, get the same pixels, therefore the change is inert" is
exactly the banned shape. The proof that the negative cannot apply at cfg 1 is
`comfy/samplers.py:370`, which sets `uncond_ = None` before the model is ever
called, together with the check that nothing in this graph's model chain sets
`disable_cfg1_optimization`. The render is reported as corroboration and
labelled as such.

## Q5 — Scope: three other cfg-1 samplers exist in this graph

**Reported them, did not test them.**

While listing every cfg-bearing node I found `619:600 KSamplerAdvanced` (cfg 1,
`lcm`) and `587:98 UltimateSDUpscale` (cfg 1, `lcm`) on the SDXL half, both on
`sdxl_tdd_lora_weights.safetensors`. `619:600`'s negative is the **buyer's own
negative prompt**, not a hard-coded string. That is the same defect class and
arguably a worse instance, but it is a different model family with a different
distillation and my brief was the three Z-Image passes. I have written down what
I observed and explicitly not concluded anything about it.

## Q6 — Reordering my own queue, which was a mistake

Main asked mid-run for a `guide_size` sweep and said it should beat my remaining
cfg arms if I had to choose. My cfg arms were already queued at positions 35–46
with 8 other agents' jobs ahead of them; the sweep, submitted later, sat at
roughly position 52 with 17 ahead. To put the sweep first **among my own work** I
deleted my 12 pending cfg arms (only ever my own prompt ids, by explicit id,
never `clear`) and resubmitted them.

**That made things worse, not better.** ComfyUI's queue is FIFO by submission
number, so deleting and resubmitting can only ever move work *backwards*. The
sweep did not advance by a single position — it was always behind those 17 — and
the cfg arms lost their good positions and went from 8 jobs deep to behind all
17 plus the four sweep arms. Net effect: the sweep is unchanged and the cfg arms
are roughly 35 minutes later than they would have been.

I have not undone it, because undoing means another delete-and-resubmit, which
would push everything back again. Recording it because the lesson generalises:
**on a shared FIFO queue, requeueing is never a reordering primitive.** If you
want something to run early, submit it early.

## Q7 — I contradicted the sweep I was asked to run, before running it

Main's request assumed `#114` downsamples its crop to `max_size 1024` and scales
back up ~3.4x. The server log says otherwise: `force inpaint` fires and the pass
diffuses at native `2688x3456`, so `guide_size` values of 1408/1808/2048 cannot
change anything. Rather than run three renders to produce three copies of the
shipped image, I ran **one** of the predicted-inert values (2048) as a falsifiable
check, one value that genuinely engages the lever (4096), and two on
`bbox_crop_factor`, which is the only setting that can make this pass sample
*smaller*. I told main immediately and gave the prediction in advance so it can
be checked against me rather than taken on trust.

## Q8 — Committing 1:1 NSFW renders to a repository

Main told me mid-task the repo was public and to pause pushing, then told me the
freeze was lifted and the owner is handling visibility separately. I have
followed the second instruction and committed and pushed as originally briefed.
Recording the sequence here only so the inventory is accurate: **nothing of mine
was pushed during the freeze**, because I had not committed anything at that
point.
