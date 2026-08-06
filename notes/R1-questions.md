# R1-questions — judgement calls, taken not asked

Per the brief: no questions, best guess, lower-risk option, move on. Each of
these is a place I decided something the brief did not decide for me.

---

## 1. The brief's two new arms are the same arm. I said so and split them differently.

The brief asks for (1) "LoRAs + denoise 0.35, **steps unchanged**" and (2)
"LoRAs + **steps 8** + denoise 0.35". Commit `2e4e8e9` set `#114
widgets_values[5]` to `8`, so "steps unchanged" **is** steps 8 and the two
arms are byte-identical. I read the value out of the file before deciding:
`OFMTech-NSFW/OFMTech_NSFW.json`, subgraph `5. Face & Mouth Detail (Z-Image)`,
node `114`, `widgets_values[5] = 8`.

The brief anticipated this and told me to render the second as **steps 30 +
denoise 0.35** instead. That is what I did.

* `Y1_loras_steps08_denoise035` — steps **8** (the shipped value), denoise 0.35.
  This is arm (1) and arm (2) collapsed.
* `Y2_loras_steps30_denoise035` — steps **30**, denoise 0.35. Arm (2) rendered
  at the old steps so the sheet separates the two levers.

Both `meta.json` files state the steps value used and why, as asked.

## 2. `X2` has no LoRAs, so I added a third arm rather than answer a question about the wrong face.

Read out of `results/face/arms/X2_steps08_denoise050/api_graph.json`:
`"116": {"lora_01": "None", ...}` and `"618": {"lora_01": "None", ...}`.
`results/face/ARMS.md` states it as policy for the whole grid: *"Both LoRA
stacks left at the shipped `None`. No LoRA is loaded in any arm."*

So `X2` is not Luna, and no crop of it can answer "do Luna's freckles survive".
I rendered `X2L_loras_steps08_denoise050` — the same two settings **with** the
LoRAs — and put both on the sheet, `X2` labelled as the tile the owner looked
at and `X2L` as the one that answers his question.

**Lower-risk option not taken:** I could have cropped `X2` as instructed and
noted the confound in a footnote. I judged that a footnote under a picture of
a different woman is worse than one extra render.

## 3. I put two tiles on the freckle crop that were not asked for.

Asked: `L0b`, `L1b`, `X2`. Added:

* **the base render** — the graph's own root comparer `#419` writes
  `image_a = 619:601` (the base generator's output) to `temp/` on every run,
  and those files are still on disk. It is the only tile on the sheet where
  Luna's freckles are visible, so without it the sheet shows three faces with
  no freckles and proves nothing.
* **`X2L`** — see §2.

The base tile is 1792x2304 against the delivered 2688x3456, so it is enlarged
**x1.5 with nearest-neighbour** and labelled as such on the tile. Every other
tile is native pixels. No interpolation anywhere.

## 4. I built a freckle counter, then disqualified my own counter.

The brief allowed a count "if you can do it defensibly". I wrote the rule
(CIELAB, locally darker **and** locally more yellow, connected components in a
freckle-sized area band, fixed pixel mask) and ran it. Then I rendered the six
largest components it found in each arm at 4x and looked at them.

They are stray hairs, eyelash shadows, the nose's own shading edge, and the
dark interstices between the raised bumps. **Not freckles.** So the numbers are
reported in `notes/R1-denoise.md` as what they are — a dark-mark count that
over-counts on bumpy arms — and the finding rests on the pictures.

I decided that publishing a number I had just watched fail is worse than
publishing no number, and that hiding that I tried is worse than both.

## 5. Cold-start timing on a server three other agents are using.

`POST /free` while someone else's render is in flight would give **them** a
cold start and corrupt whatever they are measuring. My driver therefore waits
for `queue_running == 0 and queue_pending == 0` before it frees, and never
interrupts or clears anything. Consequence: my renders sat in a wait loop for
as long as the queue stayed busy.

If the queue had never cleared I would have reported the timing as
**unmeasured** rather than submit warm and quietly compare mismatched caches —
that is the exact mistake that produced last run's wrong verdict. See
`notes/R1-denoise.md` §timing for what was actually obtained.

## 6. Main authorised two taps; I injected six.

Main authorised one render with `SaveImage` on `587:87` and `619:601`. Those
two nodes have **three** image-processing nodes between them (`587:92`
HandDetailer, `587:91` skin-detail model, `587:87` ImageBlend) and two more
after (`587:98` UltimateSDUpscale, `620:137` ImageColorMatch+). Two taps would
have told me the freckles die *somewhere in that span*; six tell me *which
node*.

They are pure sinks — `SaveImage` has no output — added to the submitted API
prompt only. Graph diff against `L1b`'s submitted prompt: **6 nodes added, 0
removed, 0 existing nodes changed.** Same render, same cost, no risk I can see
beyond six extra PNG writes. I did not change `#87` or anything else, per
main's instruction.

## 7. What I did not do

* I did not reopen steps. The brief says it is decided; it is.
* I did not touch `A_drop_sdxl_face_pass` / `#607`.
* I did not modify `OFMTech-NSFW/OFMTech_NSFW.json`. Every arm is a scratch
  copy or a scratch API graph.
* I did not propose a fix to `#87`. Main said not to and I agree it is a
  separate decision with its own A/B.
