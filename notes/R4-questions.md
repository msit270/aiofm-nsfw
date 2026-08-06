# R4 — questions, with my best guess and what I did instead of asking

Per `CLAUDE.md`: I did not stop to ask. Each item below records the question, my
reasoning, and the **lower-risk option I actually took**.

**Nothing in this file is about licensing.** `QUESTIONS.md` §0 was out of scope
for this run and I did not open it.

---

## Q-1 · D1: the A/B is rendered — who decides, and on what?

**Question.** At `#114` steps 8, does the `#597`/`#616` VAE round-trip still earn
its place?

**Why I cannot answer it.** `CLAUDE.md`: *"You cannot judge image quality. Not
here, and not on a pod either. For anything that alters output, the deliverable
is the A/B pair plus objective deltas. I look at the images."* The round-trip is
output-changing — that is not in dispute, it is measured below and was measured
at steps 30 before. So the verdict is a look, and the look is the owner's.

**The standing decision is already the owner's.** `73f3d5c` reverted the removal
*after* he looked at the steps-30 pair, and his instruction for this run was *"If
removing it costs face quality, say so and leave it."*

**What I did: left the graph unchanged and shipped the pair.** Re-removing it
would overturn an explicit owner decision on the strength of a judgement I am not
permitted to make. Leaving it is the lower-risk option and is reversible in one
commit if he wants the other answer — `423df24` is still in history as the exact
patch.

**What would settle it:** open the 1:1 face-crop pair named in `R4-defects.md`
§1. If the round-trip's softening is no longer wanted now that steps 8 has
removed the blob defect it was masking, re-apply `423df24`; the graph diff proving
that patch is exactly two node removals and one re-pointed input is in this
report.

---

## Q-2 · D2: the placeholder is documented text. Should the *documentation* change?

**Question.** `#106` ships reading `TRIGGER, PROMPT FOR YOUR MODEL`, and root
`#649` tells the buyer to replace exactly that string — so it is deliberate. But
`#114` runs at cfg 1, where `comfy/samplers.py:370` drops the uncond entirely, so
`#106` is the **only** conditioning steering the pipeline's most expensive pass.
If a buyer queues before editing it, what do they get?

**What I did not do.** I did not write character text into `#106`. It is the
buyer's content, `#649` quotes the placeholder verbatim, and overwriting it
desynchronises the node from its own instructions. The A/B arm that carries a
real description is a scratch copy and is not a proposal to ship that string.

**What I did.** Rendered the three-way A/B (placeholder / real description /
empty) so the question is answered with pixels, and recorded the result in
`R4-defects.md` §2. **Any fix here is documentation/UX, never content** — and the
docs half already moved under me this run: `a806ce3` (another agent) added
`#652 MarkdownNote` inside `5. Face & Mouth Detail` and a pointer sentence in
`#649`. Note nodes do not appear in the API graph at all (verified: 88 nodes both
sides, none of `#649`/`#650`/`#651`/`#652`), so wording changes there are
provably inert.

---

## Q-3 · The file moved under me mid-run. I did not assume it was harmless.

**What happened.** I built and submitted five arms against
`8d50f636…` (`2e4e8e9`). While they were queued, another agent committed
`a806ce3`, taking the file to `0be499d3…`. It changes three things:
`#105.widgets_values[0]` → `""`, a new `#652 MarkdownNote` inside sg5, and
`#649`'s text.

**The risk.** Publishing an A/B against a file that is no longer the shipped one.

**What I did instead of assuming.** Only one of those three reaches the API graph
— confirmed by graph diff of the current file's own conversion against my
baseline's: **1 difference, `620:105.inputs.text`**. Rather than argue from
`samplers.py:370` that it must therefore be inert, I **added a sixth render**,
`R4_cur`, built from the current file, so the claim is tested rather than
asserted. Result in `R4-defects.md` §0.

**The question I am leaving.** `a806ce3` shipped an executable input change
(`#105` → `""`) on a by-construction inertness argument with no render behind it.
The argument looks right to me and my sixth arm tests it — but the general
practice of shipping executable changes on construction alone is what this
project's history warns about. **Not my commit and not my call**; flagged for
whoever owns that decision.

---

## Q-5 · The one thing I did not settle: does filling in `#106` crash the graph when a LoRA is loaded?

**Question.** With the owner's LoRAs loaded, `#106` at the placeholder rendered
clean (`110d0594`, 286.9 s) and the same graph with **only `620:106.inputs.text`
changed** to a filled character prompt crashed at `622:403 MaskBoundingBox+`
(`94552d00`) — on a server that two consecutive successes had just shown healthy.
Filling that box in is the buyer's first documented action (`#649` §3).

**My best guess, and I am holding it loosely.** **[I]** The unified reading that
fits everything is that `622:403` has no empty-mask guard, so *anything* that
leaves the Eyes stage's face mask empty is a hard crash — the poisoned-server
state does that by destroying the face, and a prompt change might do it by moving
the face enough that MediaPipe FaceMesh misses. On that reading the defect is the
missing guard, not the prompt, and the prompt is one of several routes into it.

**What I did instead of asking.** I did not report it. Three reasons, all
checkable: it is n=1 per side post-`/free`; `notes/P2-render.md:445-446` records
this same node crashing with the **placeholder** in place, twice, for
server-state reasons; and `ebb2f8e` already made a near-identical claim
("a possible crash on the buyer's documented action") which was later attributed
to server NaN state. Publishing it now would be the third airing of a claim
withdrawn twice.

**What settles it: one byte-identical resubmission of `L1b_steps08_loras`.**
Success → placeholder/filled/placeholder is success/fail/success and the trigger
is real and crash-class. Failure → the server re-poisoned within minutes of a
clear, which is its own finding. There is no outcome that tells us nothing, which
is why I asked for the slot rather than dropping it — and why I asked rather than
queueing it, since R1 held the GPU for the owner's contact sheet.

---

## Q-4 · Timing: I am making no timing claim for D1, deliberately

`R4_base` ran with **57 cached nodes**, including `619:617 UltimateSDUpscale`,
`619:597` and `619:616` — the whole base generator was served from cache.
`R4_D1_novae` re-points `619:617.image`, which invalidates that node's cache
entry, so `#617` actually executes in that arm. The two arms therefore did
**different amounts of real work**, and their wall figures are not comparable.

This is the exact trap that produced the previous run's retracted "+31 % slower".
Forcing matched cold runs would need `POST /free` between arms, and other agents
are rendering into the same queue, so I could not hold the cache state steady
without disrupting them. **The D1 question is a quality question, not a speed
one, so I spent the renders on pixels instead.** Anyone who wants the timing
number should take it cold, on an idle server, reading `execution_cached` from
`/history` for every arm and discarding any pair whose cached-node sets differ.
