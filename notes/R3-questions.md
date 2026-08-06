# R3 — questions, with my best guess and the lower-risk option already taken

As briefed: not asked, answered provisionally, moved on. Nothing here blocked
the three decisions.

---

## Q1 · Should `619:600 KSamplerAdvanced` get the same treatment as `#105`?

`notes/P3-cfg.md` §6 found it and did not test it: `619:600` on the SDXL half
runs **cfg 1** for 70 steps on `lcm`, with the **buyer's own typed negative**
(`#483` → `619:605` → `619:606`) wired into it. Same shape as `#105`.

**My guess: no, and emptying it would be a bug.** The same `619:606` encode also
feeds `619:592 KSampler` at cfg 4 and `619:617 UltimateSDUpscale` at cfg 4.5,
where the negative is evaluated normally. `#105` was a dead field with one
consumer; `619:606` is a live field with three consumers, one of which happens
to ignore it. The right question is whether `619:600` should run at cfg 1 at
all, which is a different model family (`sdxl_tdd_lora_weights.safetensors`) and
a different distillation, and needs its own A/B.

**Taken:** left untouched, and the canvas note is scoped to "the face, mouth and
eye passes" so it does not make a claim about the SDXL half.

## Q2 · Should the `bbox_crop_factor` change be applied, not just recommended?

**My guess: not by me.** The standing rule is that anything altering output is
delivered as an A/B pair plus objective deltas and the owner looks at the
images. The brief for this run authorised editing the workflow for Decision 1
only. cf 1.5 is a one-integer change (`#114 widgets_values[15]`, `3 → 1.5`) that
can be applied in seconds once the sheets have been looked at.

**Taken:** measured, recommended, not applied.

## Q3 · Does the cfg evidence need re-measuring at steps 8?

The twelve cfg arms were rendered on the 30-step graph, before `2e4e8e9`.

**My guess: no.** The decision rests on the model's identity (sha256 against the
publisher's manifest), the vendor's `guidance_scale=0.0`, and
`comfy/samplers.py:370` — none of which involve step count. What is
step-dependent is the *magnitude* of the pixel differences in the tables, and no
part of the decision turns on that magnitude: the answer would be the same if
cfg 3.0 moved twice as many pixels or half as many, because the payoff for
raising it is ~0 either way.

**Taken:** decision recorded, and the caveat written into
`notes/R3-decisions.md` §2 rather than left implicit.

## Q4 · `#648`'s size guard is silently skipping the mouth pass about half the time

Found while measuring Decision 3, and bigger than the thing I was measuring.

`#648 SEGSRangeFilterDetailerHookProvider`, titled **"Mouth SEGS size guard (see
note)"**, is set to `area(=w*h)` / `inside` / `0` / **`1700000`**. It hooks
`#165 Mouth Detailer`'s `post_detection` (`modules/impact/hooks.py:507-508` →
`modules/impact/segs_nodes.py:614-620`) and throws away any lips segment whose
crop area exceeds the ceiling. When it does, `#165` runs and does nothing, with
no warning and `status: success`.

Across every render on this server since 21:37 yesterday: **19 passed, 20
dropped.** Dropped values cluster at 1.77 M – 2.06 M against a 1.70 M ceiling —
4 % to 21 % over. The threshold sits inside the natural spread of this
pipeline's lips crop area, not outside it. **All three of my arms dropped it, and
so did the steps-8 arm in `HANDOFF.md` §4** — which that section cites as the
internal control proving the same model runs happily at 8 steps.

And the title's "(see note)" points at nothing: I searched every `Note` and
`MarkdownNote` in the workflow — root `#649`, `#650`, `#651` and now my `#652`.
None mentions SEGS, `#648`, or a size guard.

**My guess:** the guard exists to stop `#165` re-diffusing a huge region when the
lips detector latches onto more than the lips, and the ceiling was tuned on an
image whose mouth was smaller. Raising it, removing it, or making it log loudly
are all plausible; I do not know which without seeing what it was protecting
against.

**Taken:** recorded, nothing changed. It is not one of the three decisions I was
handed, and guessing a new threshold from one image would be exactly the kind of
confident wrong answer this project keeps having to retract.

## Q5 · `#165 Mouth Detailer` also carries `bbox_crop_factor 3`

Its bbox is small enough that the crop does not clamp to the frame
(`crop region (1827, 768)` in the shipped log), so the pathology that makes cf 3
bad on `#114` does not obviously apply.

**My guess:** leave it. The `#114` finding is specifically about the clamp
handing the model 9.3 MP in one pass; `#165` is nowhere near that.

**Taken:** untested and unchanged, and said so in `notes/R3-decisions.md` §3.

## Q6 · Should `#652` also warn about the flat-grey server fault?

The buyer can hit `HANDOFF.md` §7.1 — a NaN poisons the resident model and every
later render silently returns a faceless image with `status: success`.

**My guess: yes, but not in this note.** `#652` is about one thing and a note
that tries to cover two is read as neither. It belongs beside `#649`'s "While it
renders" section, or in the packaged docs.

**Taken:** left out of `#652`. Flagging it here so it does not get lost.
