# TRACK A — judgement calls, corrections, and things I am not sure of

## Judgement calls made without asking

### 1. I did not create a branch. I committed onto `trackB-crash-grid`.
`git worktree list` shows **one** worktree, `/workspace/nsfw-fix`, and it was
already checked out on `trackB-crash-grid` when I started (the session snapshot
said `master`, so somebody switched it under me). Another agent is working in
this same directory. `git checkout -b trackA-…` would not have changed any files,
but it would have redirected *their* next commit onto my branch, and any
`git checkout` they ran would have yanked files out from under me mid-render.
**Lower-risk option taken:** stay on whatever branch is current, and only ever
`git add` paths that are unambiguously mine — `results/crash/A/**` and
`notes/A-*.md`. If the owner wants Track A on its own branch, the commits are
contiguous and trivially cherry-pickable.

### 2. Arms branch from the stored `R4_CF15_filled` API graph, not from a fresh
conversion of the workflow.
The brief says convert the frozen JSON and mutate in memory. I used the *already
converted and already submitted* API graph from the arm that actually crashed
(`results/r4/R4_CF15_filled/api_graph.json`, `workflow_sha256 a811b5d6…` recorded
in its `meta.json`, matching `sha256sum OFMTech-NSFW/OFMTech_NSFW.json` today).
Reason: it is a stricter control than a re-conversion — it is byte-for-byte the
graph with a recorded crash, so any difference in my result cannot be a
conversion difference. The workflow JSON was not opened for writing at any point.

### 3. The base render is truncated, not full.
`A0_base_tap137` prunes the graph to the ancestors of `620:137` plus a
`SaveImage`. This is safe because `620:106` is **not** an ancestor of `620:137` —
verified by walking the submitted graph, not from the note: the ancestor set of
`620:137` is 47 nodes and contains no `620:10x`. So the base image cannot depend
on the prompt under test.

### 4. I added a `SaveImage` tap on `621:163` to **every** arm, not just the A4 pair.
Risk considered: an extra output node changes the executor's node ordering, and on
a crashing arm the tap might or might not fire before `622:403` raises. It fired
on the crashing gate arm, so A4 came out of the same run as the crash rather than
a re-creation — which is strictly better evidence than a separate tap-only run
would have been. The tap adds no input to any existing node, so it cannot change
what any other node computes.

### 5. The A3 "different content" strings include a non-face and a non-visual one.
The brief asks for ≥2. I wrote 4 at 25 words: two are *other people's faces*
(the fair same-length contrast — the face pass still has a face to converge on),
one is a rusting locomotive (no face at all), one is a sentence about a committee
meeting (no visual content at all). The last two are bounds rather than fair
contrasts and are labelled that way in the results.

---

## Things I checked rather than assumed

* **That the tokenizer is not lumina2.** `620:110` says `type: lumina2`, and that
  is not what runs. See `A-length-vs-content.md` §Method — `detect_te_model`
  wins, the file is a Qwen3-4B, the tokenizer is `ZImageTokenizer`. If I had
  counted tokens with a Gemma2 or a CLIP tokenizer every number in the ladder
  would have been wrong.
* **That there is no 77-token limit on this path.** `max_length=99999999`,
  `pad_to_max_length=False` (`comfy/text_encoders/z_image.py:11`). The crashing
  string is 46 tokens including the 8-token chat template. So a "prompt too long
  for the encoder" story is dead before the first render.
* **That the offline YOLO call matches the graph's.** `subcore.py:319-325`
  `inference_bbox` is `pred = model(image, conf=confidence, device=device)` on a
  PIL image; `yolo_probe.py` makes exactly that call on exactly that `.pt`.

---

## Corrections I made to myself mid-run

### "The boundary" is the wrong shape and I had already written it down before I found out.
After `L_w16` clean / `L_w17` crash I wrote the A2 section calling 16→17 words
(29→30 tokens) **the** boundary, and framed the ladder as a monotone
clean→crash transition. Then `L_w19` came back **clean**. So there is no single
boundary: the crashing region is not an upper tail, it is interleaved. I have
rewritten the section rather than leaving the earlier phrasing to be read
charitably. The first-crash figure (17 words / 30 tokens) is still correct and
still the right length to run the content controls at; the word "boundary" around
it is not.

### I nearly answered "it is the words" the moment the ladder came back non-monotone, and the second content control caught me.
The non-monotone ladder (17, 18 crash · 19–23 clean · 24, 25 crash) does refute
**word-count** as a threshold, and I had the sentence written. Then the A3
controls came in split — `A3_C1_fisherman_w17` **clean**, `A3_C2_gardener_w17`
**crash** — and the token counts are the tell:

```
L_w17               17 words  30 tokens   CRASH
A3_C2_gardener_w17  17 words  30 tokens   CRASH      <- different subject, no shared words
A3_C1_fisherman_w17 17 words  34 tokens   clean
```

Every crashing string measured so far is 30, 32, 45 or 46 tokens; every clean one
is 11–29, 33, 34, 35, 38, 39 or 41. **So "length" may be back — not as a
threshold in words, but as specific values of the token count.** Two unrelated
30-token strings both crashing could be coincidence (the crash rate is about 4 in
25, so ~16 % for one such hit), which is exactly why it needs its own experiment
rather than a sentence. `T_tok*` is that experiment: one fixed phrase,
`"a woman's face"` (known clean at 12 tokens), plus k repetitions of the
single-token word `" the"`, giving **exactly** 12+k tokens with the content held
constant. If 30 and 32 crash and 29, 31, 33 do not, the trigger is the sequence
length and content is irrelevant.

### I nearly reported "past 16 words it crashes" off five arms.
`w17`, `w18`, `w24`, `w25` crash and `w16` is clean — that is a clean-looking
pattern from four positive cells, and it is wrong. Rule 6 in the brief
("never round a single observation up to a pattern") is what stopped it: I ran
the intermediate rungs instead of interpolating them, and `w19` fell in the gap.
Both `L_w17` and `L_w19` are therefore being **repeated** before either is leaned
on.

---

## Open / unsure

* **What produces the constant fill.** The failing image's face is a single RGB
  value (56, 51, 47) with standard deviation exactly 0 over 360,000 pixels. It is
  not a VAE decode of a constant latent (I swept latent values −1000…1000 through
  the graph's own `ae.safetensors`; the flattest result still has sd ≈ 2.3) and it
  is not a NaN reaching `SaveImage` (that would be black). **I do not know what
  writes it.** The `TAP114_*` arms tap `620:114`'s raw output to find out whether
  the face pass emits it or something between `620:114` and `621:163` does.
* **Whether "visible" is special or whether that position is.** The swap arms
  (`A3_swap_*`) hold word count *and* token count at 17/30 and change only the
  17th word. If they crash too, the position matters more than the word.
* **Whether the probe's lower VRAM pressure changes the crashing set.** The probe
  reproduces the gate exactly and reproduces `w24`/`w25` — both known crashers
  from full renders — so the crashing cases carry over. Whether some string that
  is clean under the probe would crash under a full render is untested, and it is
  the one direction the gate does not cover.
* **Everything here is with both owner LoRAs loaded and on the shipping graph.**
  I did not vary LoRAs, denoise, steps, sampler or `bbox_threshold`. Track B has
  the LoRA cell.
* **One base image.** Every arm in this file shares a single frozen base render
  (`A0_base_tap137`, from the shipping graph's own fixed seeds, so it is the base
  the R4 full renders had too). Whether the crashing *set of strings* is a
  property of this face or of the model is untested, and it is the most obvious
  next experiment: re-run the ladder against a base rendered from a different
  seed. If the crashing set moves, the trigger is an interaction with the image,
  not a property of the prompt at all. **[I]** I would bet it moves, but that is a
  bet, not a measurement.
* **Whether the crash set is a fixed point of the string or of a hash of it.**
  Four crashing strings give bit-identical output, and the run is deterministic
  (every seed `fixed`, base frozen, controls reproduce bit-for-bit). What I have
  not done is repeat a *clean* arm at two different times to prove the clean side
  is equally deterministic — `CTL_placeholder_*` does exactly that three times
  over for the placeholder, so I am treating that as settled for the placeholder
  and as strongly implied, not proven, for the rest.
