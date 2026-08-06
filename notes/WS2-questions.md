# WS2 — judgement calls

Written rather than asked. Each records the option taken and why it is the one
that is safest for a first-time buyer.

---

## Q1. Should boot-phase errors fail the run?

**Taken: no by default, `--strict-boot` to opt in.**

This install emits errors on every page load regardless of which workflow is
open — before the rebuild of the ignore-list it was nine. A harness that is red
before it has done anything is a harness nobody reads, and then it protects
nothing. But silently swallowing errors is how the shipped blocker survived.

The middle path taken: errors are bucketed by phase (`boot` / `load` / `run`),
only `load` and `run` gate the exit code, and every boot error is still printed
under a `BOOT-NOISE` heading with a note that `--strict-boot` makes it fatal.

## Q2. Should the harness ever ignore an error?

**Taken: yes, but only from a committed file with a written justification per
entry, and never silently.**

`tools/browser_harness/ignore.json` carries a `reason` per rule that cites what
was checked on the filesystem or over HTTP, not an assumption. Matched errors
are downgraded to `ignored`, not dropped: they are printed under the rule id
that matched, counted in `result.json` `counts.ignored`, and listed in full in
`result.json` `ignored`. `--no-default-ignores` shows the raw truth.
`frontend-conversion` and `execution` are never ignorable whatever the file says.

## Q3. What about defects in our own pack that would make every run red?

**Taken: a third scope, `product-known`, with a loud per-run banner. Not
`benign`.**

Two errors are ours and appear on a buyer's first load: the ten stale
`rgthree.compare._temp_*.png` filenames baked into the shipped workflow JSON,
and `[RPG] ERROR: detailsElement not found` from `reality_prompt_generator.js`.
Filing them as benign would have been a lie; leaving them fatal would have made
the harness useless. So they are ignored for gating but the run prints:

```
  !! 7 of the above are scope=product-known: REAL defects in what we ship,
     ignored only so they do not make every run red.
```

The counter going to zero is the proof for whoever fixes them. **The list should
be empty.** If a later session finds it growing, that is the signal to stop
adding to it.

## Q4. Fail fast, or collect every failure?

**Taken: collect.** The first version stopped at the first failure and hid the
Run-phase blocker behind two load-phase errors. Now a load-phase error does not
prevent pressing Run, so one run reports every phase and `result.json` carries
`failure_classes` as an array.

## Q5. Should `harness-error` be distinct from `fail`?

**Taken: yes, distinct exit code 2.**

"The environment prevented a verdict" and "the workflow is broken" must never be
conflated — treating an untested path as a passing one is this project's entire
problem. A foreign selector popup blocking the UI, ComfyUI unreachable, or a
missing workflow all exit 2 and say plainly that no verdict was reached.

## Q6. Should the harness dismiss a selector popup left open by another client?

**Taken: no. Refuse and explain.**

The INSTARAW popup is broadcast to every connected browser, so a render paused
by anyone covers this page and swallows the Run click. Cancel would abort
somebody else's render. The harness waits `--wait-for-idle-ui-ms` (default 90 s)
and then exits 2 with an explanation. A buyer never hits this; only a shared
server does.

## Q7. `--no-execute` cancellation on a shared pod

**Taken: cancel only our own queue item.**

The obvious implementation is `POST /interrupt` + `POST /queue {"clear":true}`.
On this pod that would kill another workstream's in-flight render. The harness
checks `/queue` first and uses `POST /queue {"delete":[our_prompt_id]}` unless
our own prompt is the one running.

## Q8. UI load path vs the internal API

**Taken: UI by default, API only on request, and always reported.**

`--load-mode ui` clicks the workflow in the Workflows sidebar. The API fallback
exists but is never used unless `--load-mode api` or `--allow-load-fallback` is
given, and the path actually taken is printed and recorded in `result.json` as
`load_path_used` — a run can never quietly claim a UI path it did not take.
Every run recorded in this session used `ui`.

## Q9. Should `graph_diff` try to fold every switch-like node?

**Taken: no. A tiny table with a cited source per entry, and loud caveats for
everything else.**

An over-claiming differ is worse than none. The table holds three entries;
`INSTARAW_BooleanBypass` is there because its `passthrough()` was read and
returns `input_1..4` while ignoring both BOOLEAN inputs. Anything whose
`class_type` matches `/switch|branch|conditional|selector|multiplex|pick/i` and
is **not** in the table is reported as an explicit caveat rather than skipped
quietly.

## Q10. Node-id matching when ids move

**Taken: match by id, with explicit `--rename OLD=NEW`.**

Heuristic matching (by title, by structure) would make the differ guess, and a
differ that guesses cannot be used to prove inertness. If ids moved, the caller
says so on the command line.

## Q11. Adopting WS1's `integrity.py`

**Taken: adopt, vendored, with the over-claim boundaries written into the file.**

Verified rather than trusted: 14 problems on the pre-fix fixture, 0 on the
current tree, 23 ms, and it names `outputs[4] 'MODEL'` — exactly the slot the
browser error names. It runs before the browser stage.

It is **link bookkeeping only**. It does not check `widgets_values` desync,
which CLAUDE.md calls the highest-value audit in this file, so "0 problems" is
not "no defects". And "0 problems implies the browser converts" is a correlation
established on exactly **one** before/after pair. Those limits are in the
vendored file's header so nobody reads it as more than it is.

## Q12. Test fixtures living in the buyer's workflow list

**Taken: `--cleanup-install`, and the fixtures removed from the install
directory at the end of this session.**

`harness_known_good`, `red_OFMTech_NSFW` and `harness_selector_multi` are test
fixtures. They are harmless on this pod but they sit in the same list a buyer
picks their workflow from. They live in `tools/fixtures/` in the repo and are
copied in on demand with `--install`.

**Open for whoever cuts the tarball:** confirm the packaging step ships only
`OFMTech_NSFW.json` into `user/default/workflows/`. I have not audited the
packaging script — that is SETUP.md's territory, not mine.

## Q13. Does rendering a pre-configured fixture prove the buyer journey?

**Taken: no, and I said so rather than banking the easier green run.**

I was offered a pre-built `WS6_acceptance.json` with both LoRA slots and the
prompt already saved into the file, to run with `--drive-selector`. Rendering it
would have produced a green result against the user's stated bar — *"open ComfyUI
once, pick my two LoRAs, set a prompt, press Run, get an image"*.

But it would have proven "a correctly-configured file converts, submits and
renders", and the **picking** and the **setting** are the claim. Baking them into
the JSON assumes away the thing under test. My harness drives the selector; it
does not perform the configure step. Those are two different claims and the
second is the one that matters.

Main agreed and took the acceptance journey as one continuous browser session
instead — load, configure, Run, drive selector, image — which is the only version
that tests the join between configure and render.

**The general rule this is an instance of:** a green result whose setup contains
the thing being tested is worth less than an honest gap. This project's whole
problem is a test that passed on a path the buyer does not take.

## Q14. Which failure classes to demonstrate versus claim

**Taken: demonstrate (a) and (b); state plainly that (c) is implemented but not
yet demonstrated.**

(a) `frontend-conversion` is the red fixture. (b) `server-validation` needed a
deliberately invalid graph — `steps: -5` against the server's `min: 1` — which
costs no GPU because the prompt is rejected before it queues.

(c) `execution` cannot be demonstrated without a render that fails mid-flight,
and GPU time on this shared pod is contended. A fixture is prepared
(`INSTARAW_ImageFilter` with `timeout: 20` and no `--drive-selector`, which
raises `InterruptProcessingException` on an empty selection — the documented
behaviour a buyer hits by walking away) but was not queued, because main is
waiting on the same GPU for the acceptance journey, which is worth more.

Detection for (c) is via the websocket `execution_error` / `execution_interrupted`
frames plus `/history` status, and it is deliberately **not** ignorable by the
ignore-list. That is implementation, not evidence, and the report says so.
