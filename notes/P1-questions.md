# P1 — judgement calls and open questions

Logged rather than asked, per the brief. Each has my best guess and the reason.

---

## J1 — I used B, not A, as the comparator for the gold artifact

**Call:** followed the brief and compared `D_skinblend_050` against
`B_no_vae_roundtrip`. **I also measured A and C at the same pixels**, because it
cost nothing and it turns a two-arm claim into a four-arm one. All three
non-D arms have zero pixels above the segmentation threshold in that window, so
the choice of comparator does not affect the verdict.

---

## J2 — the D graph was rendered once, so its determinism is untested

**Call:** treated the attribution as sound anyway, and said so explicitly rather
than burying it.

**Reason:** determinism was demonstrated on the A graph (5 renders, 10 pairs,
MSE 0) and the B graph (2 renders, MSE 0), and every sampler in the file reads
`"fixed"`. A single D-graph repeat would close it. Lower-risk option was to state
the gap rather than assume it away — STATE.md §7 item 8 is explicit that
substituting a better instrument is not the same as validating it.

**Proposed pod task:** re-submit `results/ws4/D_skinblend_050/api_graph.json`
unchanged and confirm MSE 0 against `HasMetadata_00011_.png`. One render.

---

## J3 — I said "brown to desaturated olive/hazel", not "brown to green"

**Call:** reported the measured direction and magnitude, and stated plainly that
`a*` stays positive so the endpoint is not green.

**Reason:** the prime directive. `a*` = 3.66 (left) and 6.23 (right) in arm C are
both on the red side of neutral. The finding's substance is unchanged — the shift
is real, it is 2-4× larger than any other arm-to-arm difference, and it is in the
green direction — but the endpoint matters if anyone later tries to reproduce
"green eyes" and cannot.

**Risk if I am wrong:** my annulus (r 15-27, lower half) could be sampling
limbal ring rather than iris body. I re-ran it with each arm's own pupil centre
to guard against that and the result held in both eyes. If the owner disagrees
with the crop, the raw images are in `results/phase1/` and the measurement is
20 lines.

---

## J4 — I did not look at the other workstreams' in-flight renders in any depth

**Call:** noted that `results/phase0/api_graph.json` and
`results/cfg/00-baseline-full/api_graph.json` both carry
`lunaskye.safetensors` in `#618` and `luna.safetensors` in `#116`, and used that
only as evidence about **product intent** (both slots are meant to be filled).
Did not use their images for anything.

**Reason:** they are another agent's live work, they are untracked, and
`results/phase0/result.json` is timestamped minutes ago. Drawing conclusions
from a moving target would be exactly the failure mode STATE.md §7 item 6 warns
about. If a LoRA-loaded D3 pair is wanted, it should be rendered deliberately,
not scavenged.

---

## J5 — the "deformed piercing" negative finding

**Call:** reported it as a strong circumstantial link, labelled **[I]**, rather
than as the cause.

**Reason:** I can prove three things from the file — the negative text names
piercings twice, it feeds `#620:114`, and `#620:114` runs at cfg 1. I cannot
prove from here that this negative would have suppressed *this* object, nor
which pass drew it. The connection is too useful to omit and too unproven to
assert.

**Open question for the owner:** was the "deformed piercing, bad piercing"
wording added after someone saw an artifact like this one? If so, this is a
recurring failure mode, not a one-off, and it raises the priority of the cfg-1
item in STATE.md §8 considerably.

---

## J6 — I did not touch the workflow JSON, `PROPOSALS.md`, or any WS4 file

**Call:** wrote only `notes/P1-analysis.md`, `notes/P1-questions.md` and
`results/phase1/*`. Committed by explicit path.

**Reason:** brief says no graph edits, and the pod experiments I identified
belong in `PROPOSALS.md`, which another workstream owns. They are listed at the
end of `notes/P1-analysis.md` under "What I did not settle" so whoever owns that
file can lift them.

---

## Open questions I could not answer from disk

1. **Which detail pass draws the gold object.** `#620:165 Mouth Detailer`
   (lips_v1 detector, bbox_crop_factor 3) or `#620:114 FaceDetailer` (denoise
   0.80). Both cover the location.
2. **Is the artifact reproducible at blend 0.5, or was it one unlucky draw?**
   n=1. A sweep at 0.25 / 0.5 / 0.75 would answer it and would also show whether
   the sub-lip region is generally unstable under this knob.
3. **Does raising cfg on `#620:114` above 1 suppress it?** Would make the
   existing negative live. Changes output everywhere, so it needs its own A/B.
4. **Does the eye shift get worse with character LoRAs loaded?** The question
   that decides whether D3 is a quality tweak or a likeness bug for buyers.
   Render the B/C pair again with `lunaskye` in `#618` and `luna` in `#116` and
   re-run the iris measurement in `notes/P1-analysis.md` §2.6.
5. **Does the buyer-facing text tell a buyer to fill both LoRA slots?** `#618`
   and `#116` feed different model families and different passes; filling only
   one leaves the face rendered under one identity and re-rendered at denoise
   0.80 under another. I did not audit `#649 MarkdownNote` or `INSTALL MODELS.txt`
   for this.
6. **Do any third-party character LoRAs carry `lora_te*` tensors?** The three
   files on this box carry none, so the raw-CLIP routing is currently free. A
   LoRA that did carry them would be silently half-applied. Unknown and
   unknowable from here.
