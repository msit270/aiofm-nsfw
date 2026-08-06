# TRACK P — packaging, and the one honest timing number

Two jobs, reported separately because they have very different confidence levels.
The artifact block is mechanical and I stand behind every number in it. The
timing block is a measurement on a shared GPU and I have tried to say plainly
where it stops being quotable.

Server used throughout: **`127.0.0.1:28191`** (pid 144284, ComfyUI 0.15.1, tree
`/workspace/comfy-r2gate3`, `--reserve-vram 16`). `:18188` was never touched —
Track V is validating there and it is the only instance that reproduces the bug.

---

## JOB 1 — the cold timing number

*(filled in below once the sweep completes)*

---

## JOB 2 — the re-cut pack

### `PACK_TOP` needed no fix

The brief said to fix `PACK_TOP` so the archive name and the unpack directory
match. **It was already fixed** and I am flagging that rather than claiming
credit for it. Commit `310621c` ("tools: reproducible pack build, and make the
name mismatch impossible") rewrote `tools/build_pack.sh` to derive the top-level
directory from the archive's own basename and then assert it against the
finished artifact:

```bash
ARCHIVE_BASE="$(basename "$OUT")"          # AIOFMTech-NSFW.tar.gz
TOP="${ARCHIVE_BASE%.tar.gz}"              # AIOFMTech-NSFW
…
PACK_TOP="$(sed -n '1{s|/.*||;p;}' "$LIST")"
[[ "$PACK_TOP" == "$TOP" ]] || { echo "✗ bootstrap PACK_TOP would read …"; exit 1; }
```

That `sed` expression is the same one the live gist bootstrap uses at line 99 to
find the directory, so the archive is checked the way the buyer's installer reads
it. The previous artifact already unpacked to `AIOFMTech-NSFW/` — I confirmed by
listing it — and the new one does too. The assertion passed on this build; I did
not observe it fire, so my evidence that it *would* fire is R5's recorded
negative control (`notes/R5-package.md:233-235`), not my own.

### The artifact

```
dist/AIOFMTech-NSFW.tar.gz
  sha256   8695a11e63630671ad9c18e47236b4d5415409df853365ae561867063b23b8af
  bytes    8,155,371
  files    170          (196 tar entries = 170 files + 26 directories)
  top-level  AIOFMTech-NSFW/     matches the archive basename

  shipped workflow, read OUT OF THE ARCHIVE:
    AIOFMTech-NSFW/OFMTech_NSFW.json
    sha256   f5bed59676c6dc5f827100890cc98acd88b7b3c3e9295f50e5283118e9d77fd8
    bytes    296,338
```

**I am quoting files, not entries.** `tar -tzf | wc -l` gives 196 for both the
old and the new archive; `grep -vc '/$'` gives 170 files and `grep -c '/$'` gives
26 directories. Same split both sides.

### Delta against the previous cut

| | previous | new |
|---|---|---|
| sha256 | `5f2a0f2b…c5ab1` | `8695a11e…3b8af` |
| bytes | 8,155,368 | 8,155,371 |
| files | 170 | 170 |
| dirs | 26 | 26 |
| tar entries | 196 | 196 |

**Zero additions, zero removals**, so nothing needs explaining on that axis:
`diff` over the two sorted `tar -tzf` listings reports no name-level differences
at all.

Exactly **one member changed bytes**. I extracted both archives in full and ran
`diff -rq` over the two trees; the only line of output was:

```
Files …/xprev/AIOFMTech-NSFW/OFMTech_NSFW.json and
      …/xnew/AIOFMTech-NSFW/OFMTech_NSFW.json differ
```

And within that file the change is **exactly the two commits and nothing else** —
a normalised (`sort_keys`, `indent=1`) diff of the two extracted copies is four
lines:

```
5075c5075
<        0.8,          -->        0.35,          #114 FaceDetailer denoise   (8d166e0)
5248c5248
<        "default"     -->        "cpu"          #110 CLIPLoader device      (7ce1539)
```

The size change is fully accounted for. The uncompressed member went
**296,341 → 296,338 bytes = −3**, and the two edits predict exactly −3:
`0.8`→`0.35` is **+1** character, `"default"`→`"cpu"` is **−4**. The *compressed*
archive moved the other way, 8,155,368 → 8,155,371 = **+3 bytes**, which is
ordinary gzip behaviour and not evidence of anything — a shorter input can
compress larger.

The previous archive's member hashes `a811b5d690ccc520…`, matching the workflow
hash `HANDOFF.md` recorded for the stale artifact. So the before-state is
confirmed against an independent record, not just assumed.

### Verified from the archive, not the tree

The distinction has mattered here before, so every check below reads the bytes
back out of the tarball:

- `tar -xzOf … AIOFMTech-NSFW/OFMTech_NSFW.json` → sha256 `f5bed596…7fd8`,
  296,338 bytes. Identical to the tree copy, so the pack ships what was committed.
- It parses as JSON.
- `#114 FaceDetailer` — `steps=8`, `denoise=0.35`, `bbox_crop_factor=1.5`.
- `#110 CLIPLoader` — `["qwen.safetensors", "lumina2", "cpu"]`.
- `python3 tools/preflight/integrity.py` on the extracted copy: **0 problem(s)**,
  exit 0.

So both fixes are present in the bytes a buyer would receive.

### One more control worth recording

My arm builder re-serialised the committed workflow with no patch applied and got
sha256 `f5bed596…7fd8` back — **byte-identical to the source**. That proves the
`indent=2, ensure_ascii=False`, no-trailing-newline formatting rule in
`notes/PHASE5-spec.md` is exactly what is on disk, and it means the two timing
arms below differ from the shipping file by precisely one widget value each,
with no serialiser drift mixed in.

### Buyer-path verification against the live gist

*(filled in below)*

---

## Publishing

`HANDOFF.md` has been updated with the new hash and a commit message naming the
change. **Nothing was uploaded, and no credentials were requested.** The command
is printed there for the owner to run.
