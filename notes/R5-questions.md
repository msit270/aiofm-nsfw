# R5 — questions and defects found while cutting

Best guess and reasoning recorded for each, lower-risk option taken, no one
asked. Ranked by how much it would matter if true.

---

## 1. `verify_buyer_path.sh` hardcodes ports that two agents now share — HIGH

**Observed.** `tools/verify_buyer_path.sh:46-48` defaults to
`WS5_DEAD_PORT=39997`, `WS5_MIRROR_PORT=38080`, `WS5_NODE_PORT=28188`. R2 and I
ran the harness concurrently; R2 changed its work directory but not its ports,
and my `bad-archive` case silently fetched from **R2's** mirror:

```
$ ls -l /proc/141329/cwd
/proc/141329/cwd -> /workspace/r2gate3-verify/mirror
$ ps -p 141320 -o args --no-headers
bash tools/verify_buyer_path.sh happy
```

The cause is that `mirror_start` (line 130-135) probes
`curl http://127.0.0.1:$MIRROR_PORT/` for readiness. **That probe cannot tell
whose server answered**, so it returns success against another agent's server
and the case then runs against the wrong bytes.

`c_nodes` has the same shape and a worse consequence: it starts ComfyUI on
`$NODE_PORT` and queries `http://127.0.0.1:$NODE_PORT/object_info`. Under a
collision the bind fails, the query succeeds against the *other* instance, and
the harness reports "✓ all 51 registered" having interrogated a ComfyUI it did
not install. That is a silent false pass. **This part is inference** — I did not
let it happen — but it follows directly from the same readiness-probe pattern I
did observe failing.

**My guess at the fix, not applied:** have `mirror_start` serve a nonce file and
require the probe to fetch *that*, and have `c_nodes` compare
`/system_stats`' reported base path (or a marker file it plants in the target)
against `$TARGET`. Both turn "something answered" into "my thing answered".
Deriving the default ports from `$$` would reduce collisions but would not fix
the underlying "any answer is my answer" bug, so it is the weaker fix.

**Why I did not apply it:** the harness is shared and R2 was mid-run against it.
Editing a verification tool while another agent is depending on it is the higher
risk. I took the lower-risk option — overrode the ports via the environment
variables the script already supports (`38081` / `28189` / `39996`), confirmed
each free first, and proved after the fact from my own mirror's access log that
my server answered every request. **Whoever owns `tools/` should make this
change before the next multi-agent session.**

**For main:** I could not determine whether my run damaged R2's. Both processes
were gone by the time I looked. `mirror_stop` kills `$MIRROR_PID`, which is my
own subshell's pid, so it should have been a no-op — but I will not assert it,
and R2 should confirm its own happy-path log shows a complete transfer and
`exit code 0` rather than inherit my guess.

---

## 2. `pack sha256:` never reaches `happy.out` — MEDIUM

**Observed.** `c_happy` prints it with `note` at line 210; the `tee "$WORK/happy.out"`
is at line 220. So the one line that ties the whole happy-path log to a specific
artifact goes to the terminal and **not** into the saved log:

```
$ grep -n 'pack sha256' /workspace/r5-verify/happy.out
(no output)
```

That matters because the log is what survives a session. Anyone reading
`happy.out` later cannot tell which bytes were installed, and the natural
assumption — that it was whatever `dist/` holds *now* — is exactly the
assumption that goes wrong after a re-cut.

**Best guess at the fix:** move the `note` calls inside the `tee`, or echo the
sha into `$WORK/happy.out` before the run. One line either way.

**Not applied**, same reasoning as §1 — shared tool, another agent mid-run. I
closed it for this run by other means (hashing the file the mirror actually
served, plus the mirror access log, plus reconciling curl's byte count), all in
`notes/R5-package.md` §6.

---

## 3. Eight `.pyc` files have appeared in the pack source — LOW, but watch it

**Observed.** `find OFMTech-NSFW -name '*.pyc' | wc -l` → `8`, in three
`__pycache__` directories under `ComfyUI_INSTARAW/`. WS5 recorded the tree clean
of every junk pattern; that is no longer true.

The builder excluded all of them and none reached the archive (verified against
the archive's own listing), so **there is no defect in the artifact**. But two
things follow:

- The exclusion list is no longer insurance; it is load-bearing. A hand-rolled
  `tar czf` would now ship eight `.pyc` files compiled for the build pod's
  Python 3.12 to buyers who may be on another minor version.
- Something on this pod is importing INSTARAW from the *source* tree rather than
  from an installed copy. **I did not establish what** — that is inference from
  the file locations. Not harmful, but it means the pack source is being used as
  a live import path, and a stray `.pyc` is the mildest thing that can leave
  behind.

**Guess:** another agent's node-registration or import test. Harmless. Left
alone; deleting another workstream's build residue mid-session is exactly the
kind of tidy-up that costs someone else an hour.

---

## 4. `Ideogram4PromptBuilderKJ` raises on `/object_info` — LOW, not ours

**Observed** in the node-check instance's log:

```
[ERROR] An error occurred while retrieving information for the 'Ideogram4PromptBuilderKJ' node.
TypeError: BoundingBox.Input.__init__() got an unexpected keyword argument 'force_input'
```

Checked directly: `Ideogram4PromptBuilderKJ` is **not** among the 51 node types
this workflow references, and all 51 registered. So it does not affect this
pack. It is API drift between a KJNodes-family node and the pinned ComfyUI core
(`0.15.1`).

Recorded only so a future session does not see it in a log and mistake it for a
packaging fault. **Guess:** harmless for us; would matter if anyone later adds an
Ideogram node to this graph.

---

## 5. Three consecutive cuts have never been uploaded — for the owner

Not a defect in anything I can fix, but it is the single most consequential fact
I found. Live HF has served `3f6d0f2f…aada76` throughout WS5, P4 and this run:

```
x-linked-size: 8202871
x-linked-etag: "3f6d0f2ffd092cf9a1691684029030e37283dd484cd550573290677400aada76"
```

So every buyer today still receives the archive with the **`OFMTech-NSFW/`
top-level directory** — the mismatch WS5 fixed is fixed only in artifacts nobody
has published — and none of the graph fixes since have reached anyone.

Two prior reports tell the reader to watch for a hash that **cannot appear**
(`notes/WS5-report.md:724` says `15706aa7…`; `notes/P4-package.md:551` says
`27fa2e1c…`). Both are stale. `notes/R5-package.md` §8 states the correct pair:
expect `5f2a0f2b…`, and `3f6d0f2f…` means the upload did not land.

**No question here, just the recommendation:** the upload is the owner's to run
and it is the only remaining step between three sessions of work and a buyer.
