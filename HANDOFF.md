# HANDOFF.md

**Workflow `f5bed596…` · artifact `8695a11e…` · nothing uploaded.**
Detail in `notes/` — `CRASH.md`, then `A-` `B-` `C-` `D-` `E-` `V-` `P-` per track.

---

## The one decision that wants you

**The face-prompt crash has a one-widget fix, it is applied, and it costs you the
eyes.** Sheet: **`results/crash/V/out/V_SHEET_EYES_face_sheet1of1.png`** — two
tiles, 1:1, identical graph and seed, one widget apart.

The change is **12.8 % of pixels on a render where nothing was wrong**, and it is
almost entirely the eyes. Outside the face box only 1.7 % of pixels move at all,
never by more than 2 levels. No tone shift, no colour cast, **no change in skin
texture or sharpness** (high-frequency ratio 1.00012 — the cheek tile is on the
sheet so you can check that rather than take it from me).

Describing, not rating:
- **`default` (before)** — pupil is a clean closed dark oval with a crisp edge;
  the catchlight sits *beside* it as a fine branching wispy filament.
- **`cpu` (now)** — the catchlight becomes a larger, blockier, harder-edged mass
  that **crosses the pupil boundary**, so the pupil reads notched rather than
  closed. Iris fibres above the pupil read coarser and lighter. Both eyes.

**And the thing that makes this your call, not mine:** the graph's own eye prompt
`622:398` reads *"perfect eyes, round pupils, round iris, symmetrical eyes,
realistic eyes, perfect circles, round"*. **The fix moves the pupil away from
closed and round** — against what the pipeline is explicitly asking for.

**What you get for it:** two of the three crash bands closed, and — more
importantly — the *silent* failure closed. The one arm all session that returned
`status: success` with a ruined face was `device: default`. **No fix arm ever
failed silently; where it fails, it fails loudly.** Cost **+37.4 s** (~12 % of a
cold render). **Revert with one commit: `git revert 7ce1539`.**

---

## What the bug actually is

**`620:114 FaceDetailer` paints the face solid black** — pure `(0,0,0)` over ~17 %
of the frame, the exact outline of the face with nothing inside it, hair and
background normal. `ImageColorMatch+` lifts that to `(56,51,47)`. The
`622:403 MaskBoundingBox+` crash is only the consequence: YOLO scores the leftover
silhouette 0.466 and finds no face at 0.6.

**It is the TOKEN COUNT of the prompt. Content is irrelevant** — ~56 cold arms,
8 unrelated content families, not one token count with two different outcomes.

```
tokens  11…29 │30 31 32│ 33…43 │44…50│ 60 72 80 90 96 │103…120│ 140 166
        clean │ CRASH  │ clean │CRASH│     clean      │ CRASH │  clean
```

**Bands, not a threshold.** At least three. The fix closes the first two and
**does not close 103–120** — a buyer reaches that with an ordinary ASCII prompt.

**Root cause is still open**, and I am not dressing it up. `620:114` is **bistable
on numerical noise**: CPU and GPU conditioning differ by ~**4e-7 relative**, both
finite, and that decides between a healthy render and a black face. Ruled out with
controls: VRAM pressure, lowvram, `--reserve-vram`, sage attention, code-tree
differences, environment — the box that reproduces and the box that does not have
**identical `/proc/environ`**. It is a property of the **process**: a fourth
ComfyUI from the *same directory* was clean 10/10 while `:18188` crashed 9/9 in
the same window.

**The crash is the good case.** Turning off the LoRAs gives `status: success` with
23.5 % of the frame a flat fill. Padding the *eye* prompt by three tokens ships a
delivered image with **two solid black eye holes**. A guard on the crash would
produce exactly that shape by design — which is why the guard designed for this
was **not** applied. Your shipped eye prompt sits **two tokens** from a band.

---

## Applied this run — three commits, revert individually

| commit | change | why |
|---|---|---|
| `8d166e0` | `#114` denoise `0.80 → 0.35` | your pick off the R1 sheet. **Free** — both arms run exactly 8 sampling steps |
| `7ce1539` | `#110 CLIPLoader` device `→ cpu` | the partial fix above |
| — | pack re-cut, `8695a11e…` | 170 → 170 files, one member changed |

Earlier runs: `2e4e8e9` steps 30→8, `a806ce3` `#105` emptied + canvas note,
`74c0f11` crop factor 3→1.5.

## Still broken

1. **103–120 tokens still crashes**, fix or no fix. Root cause open.
2. **`device` is an *optional* `CLIPLoader` input.** On an older ComfyUI the
   `"cpu"` is **silently dropped** — no error — and the buyer runs the broken
   configuration believing they have the fix.
3. **`622:403` has no guard.** "Detector found nothing" is still an unhandled
   `RuntimeError`. Design ready in `notes/C-fix-design.md`, deliberately unapplied.
4. **Three things only a browser can see, all in the shipped bytes:** all seven
   subgraph hosts ship **collapsed**, so §7's route to `#106` has **no way in**
   until the buyer finds the collapse box · `#106`'s promoted widgets are
   **unlabelled** (two boxes both drawn `seed`) · **126 Cyrillic `localized_name`
   fields**, so **every buyer sees Russian slot labels regardless of locale**.
5. **`#165 Mouth Detailer` silently skipped ~half the time** — `#648` drops the
   lips segment above 1.7 M crop area; observed 1.77–2.06 M. One session: 19
   passed, 20 dropped.
6. **A hard composite seam** at the face-box edge, visible in the delivered image.
7. **Five licence blockers** — `QUESTIONS.md` §0, untouched as instructed. DMD2
   (cc-by-nc) still ships because `--include "models/*"` sweeps it regardless.
8. **`/free` is racy** — it only sets a flag the worker consumes on a 10 s timer,
   so a late `/free` can go unconsumed and the next run silently runs warm. Always
   confirm `execution_cached: []` in `/history`. *This is what the project has
   been calling "server poisoning" — reproduced 2/2 as a stale execution cache.*

## Where I was wrong this run

Each is marked in place in the notes, not quietly dropped.

- **"Marginal detection near the 0.6 threshold."** Refuted — the distribution is
  two-valued with a 0.43 gap and nothing in it.
- **"The cured arms are indistinguishable from a good render."** Wrong — I quoted
  a 48.7 dB noise floor that does not exist on that instance (repeats are
  bit-identical), so 48.9 dB was **100 % signal**. The fix is not inert.
- **The tokenizer.** I read `lumina2.py` because the widget says `lumina2`; the
  dispatch is on the state dict and it is `ZImageTokenizer`. Conclusion survived
  by luck, not method.
- **"+14 s for the fix."** It is **+37.4 s**.
- **A confound I set and the verifier caught:** the fix's original evidence was
  gathered at the old denoise value. A 2×2 showed `device` is the whole effect —
  testable by luck, not design.
- **Withdrawn timing figures, do not quote any of them:** `−103.7 s / −26 %`,
  `−53 %`, `−6.9 %`, `−118 s`, `−12.1 s`.

## Using it

| what | where |
|---|---|
| prompts + seed | panel beside `1 · YOUR PROMPTS & SEED` |
| **SDXL LoRA** | `#618` — body, pose, hands, upscales |
| **Z-Image LoRA** | `#116` — face, mouth, eyes. **Your likeness lives here** |
| **face prompt** | sg `5 · Face & Mouth Detail`, `#106` — subgraph ships collapsed |

The render **pauses** at an image selector and waits — walk away and it times out
after 10 minutes and sends nothing.

```bash
# 9 s, no GPU, after any graph edit.  0=pass 1=broken 2=could-not-run
node tools/browser_harness/run.js --workflow OFMTech_NSFW --no-submit
# fresh pod (provision 250 GB — the old "~176 GB" was wrong low)
echo "hf_YOUR_TOKEN" > /workspace/.hf_token
bash <(curl -sSL "https://gist.githubusercontent.com/msit270/70256ac1ebf2760e10f78804862db528/raw/aiofm_setupnsfw.sh")
```

**Browser gate: all four shots pass** from the shipped tarball — zero red nodes
across root and every subgraph, both LoRA stacks set through the widget's own
menu, a real prompt in `#106`, finished image. `results/gate2/`, 67 artifacts.

## Publishing — you run this, nobody else. **Nothing was uploaded.**

**Fine for your own testing. I would not put it in front of a buyer yet** — item 1
above means a normal-length prompt still kills the render, and item 2 means they
may not even have the fix. Your call; it changes who should receive the bytes,
not the bytes.

```
dist/AIOFMTech-NSFW.tar.gz   8,155,371 B   sha256 8695a11e…3b8af   170 files
workflow inside it: f5bed596…   verified out of the archive, not off the tree
```
`170 → 170` files, zero additions, zero removals, exactly one member changed
(`diff -rq` over both extracted trees) carrying exactly the two commits.
`tar -tzf | wc -l` says 196 — that is 170 files + 26 directories. Reproducible:
byte-identical rebuild. Buyer path: no-token exit 1, bad-archive exit 1, happy
exit 0 in 85 s, 51/51 node types. **Live HF still serves an artifact four cuts
behind; neither graph fix has ever been published.**

```bash
HF_TOKEN="$(tr -d '[:space:]' < /workspace/.hf_token)" \
/venv/main/bin/hf upload msit270/AIOFM-Pack \
    /workspace/nsfw-fix/dist/AIOFMTech-NSFW.tar.gz \
    dist/AIOFMTech-NSFW.tar.gz \
    --commit-message "NSFW pack re-cut: #114 denoise 0.80->0.35 (8d166e0) and #110 CLIPLoader device default->cpu, the black-face fix (7ce1539). Workflow f5bed596, archive 8695a11e"
```

```bash
# check from the buyer's side, the only side that counts
curl -sS -I -H "Authorization: Bearer $(tr -d '[:space:]' < /workspace/.hf_token)" \
  "https://huggingface.co/msit270/AIOFM-Pack/resolve/main/dist/AIOFMTech-NSFW.tar.gz" \
  | grep -i 'x-linked-etag\|x-linked-size'
# expect: x-linked-etag: "8695a11e…3b8af"   x-linked-size: 8155371
```

*Everything from this run is on branch `trackB-crash-grid`, not `master`.*
*Previous run's findings — freckles, cfg, the browser bug — in `notes/HANDOFF-detail.md`.*
