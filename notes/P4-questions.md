# P4 — judgement calls, logged as made

Nothing here blocked the work. Each is the option I took, why, and what would
change my mind. No question was asked of anyone.

---

## Q1. My brief said three JS files had changed since the last cut. They had not.

**Taken: verified the claim before building, and built to the corrected
expectation.**

The brief listed `js/popup.js` (`342a038`, `3afa7ed`) and
`js/reality_prompt_generator.js` (`7de8c15`) as changes since the previous cut.
`git merge-base --is-ancestor` puts all three inside `3357ae3`, the previous cut
itself, and `notes/WS5-report.md:745` says the same independently. The only
change since is `73f3d5c`.

Why it mattered rather than being pedantry: the expected delta is the only
control I have on the build. Had I expected four changed members I would have
had no way to distinguish a correct build from one that had picked up
uncommitted work, and "three files I expected are missing from the delta" would
have looked like a builder fault. Verifying the premise cost one command.

I did not treat this as a reason to distrust the rest of the brief — the sha256
`f1ac7e55…` it gave me was exactly right.

## Q2. Which archive is "the previously published archive"?

**Taken: reported the delta against BOTH, and led with the one that answers the
question that was actually asked.**

Two candidates: the 164-file `3f6d0f2f…` live on HF, and the 170-file
`15706aa7…` WS5 cut but never uploaded. The brief's own framing ("the previous
cut went 164 → 170 … this one should show no further additions or removals")
only makes sense against the published one, so §4b is that. But the sharper
control is §4a against WS5's cut, where the expected answer is a single changed
member — and that is what came out.

Reporting only 4b would have hidden the strongest evidence in the run. Reporting
only 4a would not have answered the brief. Both cost nothing.

## Q3. The live HF object is still the OLD one. Does that change the upload note?

**Taken: yes — the "it did not land" hash is `3f6d0f2f…`, not WS5's
`15706aa7…`.**

A `HEAD` against the repo shows `x-linked-etag: "3f6d0f2f…aada76"`, so WS5's cut
was never published. If I had copied WS5's §5 wording forward, the owner would
have been told to watch for a hash that has never existed on HF and cannot
appear. `15706aa7…` is now a hash that should never be seen at all, and the
report says so.

## Q4. How to prove the `PACK_TOP` assertion fired, given it prints nothing on success

**Taken: `bash -x` on the same script, plus a negative control on a real
artifact.**

The builder's assertions are `[[ … ]] || { echo …; exit 1; }` — silent when they
pass, so "the build exited 0" only proves they did not fail, not that they ran.
`bash -x` shows both comparisons executing with expanded values.

That still leaves the weaker objection: `TOP` is derived from the output
filename and `PACK_TOP` from the archive the script just built, so a passing
comparison could in principle be a tautology. I could not make the real build
fail the assertion — the two names agree by construction — so I ran the
identical `sed -n '1{s|/.*||;p;}'` against the previously published archive,
which reads `OFMTech-NSFW` and would fail. The expression discriminates.

**Rejected:** hand-crafting a deliberately mismatched tarball to feed the
assertion block. It would test a copy of the logic rather than the committed
script, and the published artifact is a better negative control because it is
the exact historical case the assertion was written for.

## Q5. `[6/14]` printed "724 MB still to download" and then "nothing to download"

**Taken: measured which was right; reported the measurement; did not diagnose
the cause.**

I compared the Hub's own `models/` file list against the installed tree: 74
files, all present, all byte-exact, zero missing. So no buyer-visible gap.
Beyond that I would be guessing at the estimate's arithmetic, and this is not a
packaging defect — it is the installer's own reporting. Left alone. It is the
same shape as WS5 §8b's multiple-denominators finding (`179.5` vs `178.8` GB;
`74` vs `87` vs `89` files) and belongs with that work, not in a re-cut.

**Worth someone's time later:** `integrity: OK` checks the size of files that
are *present*; on this evidence it says nothing about files that are *absent*. I
have not read that code path this run, so that is inference from the reported
behaviour, not a claim about the source.

## Q6. `prepare` does `rm -rf` on a 180 GB hardlink tree while renders are running

**Taken: ran it, because unlinking a hardlink cannot touch the other link's
content, and verified rather than assumed.**

`rm` on a hardlink decrements the link count; the live file keeps its inode and
bytes. The harness fingerprints every file under the live `models/` by
inode/size/mtime before and re-checks after, and reported `live models tree
untouched (inode/size/mtime identical for every file)` across all 87. `df` was
47 % before and after.

**Rejected:** skipping `prepare` and reusing the existing target. It would have
made the happy path an upgrade-over-an-existing-install rather than the cold
install a buyer performs, and `custom_nodes entries: 0` is the line that makes
the node-registration result meaningful.

## Q7. Push failed — other agents' unstaged files blocked `git pull --rebase`

**Taken: `git fetch` + verify, never `--autostash`.**

`git pull --rebase` refused because of unstaged changes under `results/` and
`notes/` belonging to `P2-RENDER` and `P3-CFG`. `--autostash` would have
stashed and restored another agent's in-progress files while they may have been
writing them — a real corruption risk for work I do not own, to solve a problem
that is mine.

Instead I fetched and checked divergence. A concurrent agent had already
rebased and pushed, carrying my commit `859f829` with it. Confirmed the artifact
landed by hashing the blob as it exists on the remote ref:

```
$ git show origin/master:dist/AIOFMTech-NSFW.tar.gz | sha256sum
27fa2e1c5496c4d0efee7d5b626e7638b197e1327500f86936a2a9e918dd3d37
```

I checked the pushed bytes rather than trusting "the push exited 0", which is
the whole point.

## Q8. Should the re-cut drop the licence-encumbered files?

**Taken: no. Not my call, and `rm` is the wrong instrument.**

The brief is explicit and `QUESTIONS.md` §0 is the standing record. Recording it
here so the decision is not re-litigated silently on the next cut: WS5 measured
INSTARAW going from 95 registered node types to **0** on a naive delete, and
four modules referencing the UnMarker path have never been traced. The artifact
ships both trees, §7 of the report says so in the same breath as the green
result, and nothing reaches a buyer until the owner runs the upload.

One thing I did change: WS5 §4c framed the size cost as "roughly the compressed
size of `grainnet.pt`". Measured, `grainnet.pt` is 45,929 bytes and the whole
encumbered set is ~99 KB, so size should not feature in the decision at all.

## Q9. The gist still has WS5's comment-only fix unpasted

**Taken: reported it, changed nothing.**

Live gist is 116 lines / `bf80cb65…`; the committed replacement is 118 lines /
`a7c7186c…`. `PACK_PATH` and `PACK_TOP` are identical between them, so this cut
installs correctly either way — which is exactly the property WS5 was buying by
renaming the archive's *directory* rather than its *filename*. I have no gist
mandate and pasting it is not a packaging step.
