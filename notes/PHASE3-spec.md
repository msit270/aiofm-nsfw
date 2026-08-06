# Phase 3 — proving a fix, specified before any fix exists

Written now so the acceptance test cannot be quietly weakened to fit whatever
lands. Every number here is measured, not assumed.

---

## 1. Your proof string is 32 tokens — inside the crash band. Good news, with a catch.

Tokenised with the graph's own encoder (`comfy.text_encoders.z_image.ZImageTokenizer`,
the class `620:110` actually instantiates — *not* the `lumina2` one its widget names):

| string | tokens | band |
|---|---|---|
| **the brief's proof string** — `luna, 21 year old woman, freckles, green eyes, detailed skin texture, soft window light` | **32** | **CRASH (30–32)** |
| the known crashing string | 46 | CRASH (44+) |
| shipped placeholder `TRIGGER, PROMPT FOR YOUR MODEL` | 16 | clean — 21 arms, all clean |
| empty `""` | 8 | **UNMEASURED** |

**So the brief's own test string does exercise the bug.** That is lucky and it
matters: a proof string sitting in a clean band would have returned 10/10 green
against a fix that did nothing at all.

**The catch: 32 is the top edge of the lower band.** 33 is clean. One word either
way and the test stops testing anything. So the Phase 3 set must not rest on it
alone — pin the exact byte string, and add arms deeper in the crashing region.

**Required proof set** (all with both LoRAs, on the shipping graph):

| # | string | tokens | why |
|---|---|---|---|
| P1 | the brief's proof string, byte-exact | 32 | the owner's own test, edge of the lower band |
| P2 | the known crashing string | 46 | deep in the upper region, 4/4 crash history |
| P3 | any 47–50 token string | 47–50 | unbroken crash run, furthest from an edge |
| P4 | shipped placeholder | 16 | must stay clean — regression guard |
| P5 | empty | 8 | unmeasured; brief says it may refuse but must refuse *cleanly* |

Awkward-string arms from the brief — very long, punctuation-heavy, non-English —
still required, and **report each one's token count** so a pass can be read
against the map rather than taken on faith.

---

## 2. "10/10 clean" is NOT sufficient. Three failure modes pass it.

This is the whole trap of this bug, and it has already bitten three times today:

1. **`E398_tok31`** — `status: success`, image delivered, **both eyes solid black
   holes**. Exit code 0.
2. **LoRAs off** (`B1_noloras_crashstring`) — `status: success`, **23.5 % of the
   frame a single exact RGB**. Exit code 0.
3. **Track C's guard**, if applied alone, would convert every crash into exactly
   this shape by design.

**A green render is not evidence of a fix here. It is the failure mode.**

### Acceptance criteria — all four, per arm, or it is not fixed

| # | check | pass condition |
|---|---|---|
| A | no exception | `status: success`, no `execution_error` |
| B | **no black region** | exact-`(0,0,0)` fraction over the frame **≈ 0**; and no single exact RGB occupying a large contiguous area (the `(56,51,47)` signature that `ImageColorMatch+` lifts black to) |
| C | **the face survives detection** | `face_yolov8m.pt` max confidence on the delivered frame in the **0.89 class**, not the **0.466 class**. There is a 0.43 gap and nothing in it, so this is unambiguous |
| D | **the eyes stage actually ran** | if a guard is part of the fix, a fired guard is a **FAIL**, not a pass. Prove the eyes detailer executed — its node id in `/history`'s `executed` list |

Cold, `/free` before each, and **`execution_cached: []` confirmed in `/history`** —
not merely a `/free` issued. `POST /free` only sets flags the worker consumes
later; Track A reproduced the project's long-standing "server poisoning" 2/2 as
exactly this stale cache.

---

## 3. The positive control — without it the whole test is void

**Track D's instance renders the crashing string clean, 3/3.** So a green result
proves nothing unless *that same instance* was first shown able to fail.

**Before** applying any fix, on the instance you will validate on:
- run P2 (46 tokens) and observe the crash at `622:403`;
- run P4 (16 tokens) and observe a clean render.

If the instance will not crash pre-fix, **stop** — it cannot validate anything.
Use one that does. `notes/D-gate.md` §6 carries a one-line pre-fix probe.

---

## 4. What would kill a candidate fix

- Any arm passing A but failing B, C or D — the fix is a silencer.
- The band moving rather than vanishing (e.g. now crashes at 33–35). Re-run the
  full ladder, not just the proof set.
- A pass that only reproduces on one instance. Two, minimum, one of which was
  shown able to fail.
- Any change to `620:114`'s output on a **clean** arm. The fix must be inert where
  nothing was wrong — prove it with a constant-folded API-graph diff, and note
  that **hashing rendered output is banned** as a verification method here.
