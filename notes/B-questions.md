# Track B — judgement calls, corrections, and what I am not sure of

## Things I got wrong, or that the brief got wrong, and corrected

**1. `620:648` *is* in the data path of the failing detector.** The brief says
"the wiring says this hook is on the MOUTH pass and is NOT in the path of the
failing detector `622:424`". Walked from the submitted API graph, the hook **is**
upstream of `622:403` — the reachability set of `622:403` contains `620:648`,
`620:165`, `621:166` and `620:106`. The route is
`620:648 -> 620:165.detailer_hook -> 620:165` image out `-> 621:163 -> 622:431 ->
622:424`. What is true is the narrower statement: the hook does not configure
`622:424`, it only changes the *image* handed to it. I ran cell E anyway, as
asked, and the outcome is in the grid.

**2. `notes/R4-defects.md` §2b's bet is wrong in both directions.** It bet 2-in-3
that "the LoRAs are load-bearing and the `luna, ` prefix is not". Cell B says the
LoRAs are load-bearing *and so is the prefix*: removing either one stops the
crash. That bet is the reason this cell was left open, so it is worth saying
plainly that betting past the untested cell would have produced a wrong
published claim.

**3. My own health check would have passed `B1` if I had used only the metrics
this project has been using.** `B1`'s `luma_sd` is **66.59** — *higher* than the
healthy baseline's 59.51 — and a "success" status. Only `flat_frac` (0.256) and
the modal-colour coverage I added afterwards (23.5 % of the frame one exact RGB)
catch it. `luma_sd` alone is the wrong detector for this failure mode: a frame
that is three-quarters photograph and one-quarter solid fill has a *high*
variance. If any earlier session cleared an arm on `luma_sd` alone, that clearance
is not safe.

**4. My `flat_frac` / `luma_sd` numbers are not comparable to R4's.** On a
bit-identical image R4 reports `0.0030 / 37.38` and I report `0.03088 / 59.505`.
Different implementations. I only ever compare my numbers to my own baseline.
Nobody should read my 0.0309 as a regression against R4's 0.0030.

---

## Judgement calls

**`619:603.inputs.pick_list` left at `"0"`.** `INSTARAW_ImageFilter` with
`pick_list = ""` posts the batch to a browser and blocks up to `timeout` (600 s),
then `ontimeout = 'send none'` gives an empty selection and
`image_filter.py:160` raises `InterruptProcessingException`. `"0"` auto-selects
image 0 and never blocks (`image_filter.py:133`). Both R4 CF15 arms carry `"0"`
in their saved `api_graph.json`, so it is constant across every arm of mine
including both baselines — it cannot be a variable in any comparison. Recorded
because `R4-defects.md` notes `"0" -> ""` as "injected at submit" and the
direction of that note is ambiguous.

**I used R4's already converted API graphs rather than re-converting the
workflow.** The brief says convert and mutate in memory; re-converting would have
required a converter run against a frozen file for no benefit, and R4's two CF15
graphs are provably (a) derived from `a811b5d6…`, which is still the file's
current sha256, and (b) different from each other in `620:106.inputs.text` and
nothing else. Re-converting would have risked introducing a difference, not
removed one. The graph file was never opened for writing.

**Repeats.** Rule 6 asks for a second run where crash/clean flips against
expectation. I ran `B1` twice (unexpected non-crash) and `B2` twice (unexpected
clean-and-healthy). Both pairs came back **bit-identical**, so the extra run buys
determinism, not an average.

**Health controls.** `A0` crashed and `A1` immediately after it was bit-identical
to the 18188 reference. `B1`/`B1b` produced the constant fill and `CTL1` right
after was bit-identical to `A1`. Where an expected-clean cell follows a crash
cell, I let it serve as the health control **only when it came back clean *and*
healthy *and* deterministic**; anything else and I ran an explicit control before
believing the cell. Every such use is named in the grid.

---

## What I am not sure of

**Whether the constant fill in `B1` is a NaN.** I can see the output — 23.5 % of
the frame at one exact RGB with sd 0.0 — but I have not seen a NaN, and the
server log printed no NaN warning during that run. The fill is dark
`(53,47,43)`, not the "flat grey" `HANDOFF.md` §7.1 describes, and it is
face-shaped rather than frame-wide. It could equally be the sampler collapsing to
a constant latent. Deciding it needs a tap on `620:114`'s output, which is a
graph mutation I did not make.

**Which node writes the fill.** I attribute it to `620:114` from the log ordering
and from the fill being the shape and position of the face crop, but I did not
tap the intermediate image, so that is inference.

**Whether the `luna, ` prefix destroys the face on its own.** I have not run
`"luna, "` alone with the LoRAs **off**. `B1` (prefix, no LoRAs) is destroyed and
`B2` (no prefix, LoRAs) is healthy, which is what makes me point at the prefix —
but every destroyed arm I have also contains the long description, so
"prefix alone, no LoRAs" is **not run** and I am not claiming it.

**Whether any of this generalises past this one string.** Everything here varies
one thing about *one* 169-character prompt. Track A is running length-vs-content
on the same defect; nothing in my grid should be read as a claim about prompts in
general.
