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

### What was run

Three arms, all built from the current committed workflow (`f5bed596…`), all
converted to API format through the real browser frontend, all submitted to
`:28191`:

| arm | `#114` denoise | `#110` device | what it is |
|---|---|---|---|
| `P_D080` | **0.80** | cpu | the old shipping value |
| `P_D035` | **0.35** | cpu | the current graph as committed |
| `P_CLIPDEF` | 0.35 | **default** | pre-`7ce1539`, for the CLIP question |

**Graph diff, both pairs, on the submitted API graphs** (after the two
submitted-prompt modifications R1/P2 used — `pick_list="0"` and dropping the
frontend-only `rgthree_comparer`):

```
P_D080 vs P_D035    RESULT: DIFFERENT — 1 difference(s): value_changed=1
    620:114.inputs.denoise  (FaceDetailer)   0.8 -> 0.35

P_CLIPDEF vs P_D035 RESULT: DIFFERENT — 1 difference(s): value_changed=1
    620:110.inputs.device   (CLIPLoader)     "default" -> "cpu"
```

Exactly one input each, nothing else. Both graphs are 88 nodes (87 after the
tool folds the one `INSTARAW_BooleanBypass` passthrough).

**No taps.** The defect the brief flagged in the old `Z0` — six `SaveImage` nodes
writing full-resolution PNGs on one arm only — is absent here. All three arms are
the same 88 nodes and write the same single output.

### Design: a 3×3 Latin square, not A/B repeats

The GPU is shared with **two other ComfyUI servers** (`:18188` Track V, `:31910`
Track D). Each arm was run three times, rotating position so each arm sits in
each position of the round exactly once.

### The runs

Every run: empty queue confirmed, `/free {unload_models, free_memory}`, and
**`execution_cached: []` read back out of `/history`** — not trusted from the
free. All nine came back cold on the first attempt; none had to be discarded.

| arm | run | exec (s) | cached | models requested / loaded | `vram_free` at submit (GiB) |
|---|---|---|---|---|---|
| `P_D080` | r1p1 | 317.1 | 0 | 11 / 8 | 36.8 |
| `P_D080` | r2p3 | 319.2 | 0 | 11 / 8 | 41.7 |
| `P_D080` | r3p2 | 326.6 | 0 | 11 / 8 | 58.3 |
| `P_D035` | r1p2 | 306.2 | 0 | 11 / 8 | 42.3 |
| `P_D035` | r2p1 | 300.3 | 0 | 11 / 8 | 35.3 |
| `P_D035` | r3p3 | 320.0 | 0 | 11 / 8 | 49.7 |
| `P_CLIPDEF` | r1p3 | 292.7 | 0 | 11 / 8 | 64.0 |
| `P_CLIPDEF` | r2p2 | 289.4 | 0 | 11 / 8 | 60.4 |
| `P_CLIPDEF` | r3p1 | 257.3 | 0 | 11 / 8 | 52.9 |

**A stronger coldness check than `execution_cached`.** `execution_cached: []`
proves the *node output cache* was cleared. It does **not** prove the models were
evicted from VRAM, and `nvidia-smi` cannot prove it either — I checked, and my
process still shows 19.6 GB allocated straight after `/free`, because PyTorch's
caching allocator keeps the freed pool. What does prove it is the server
re-emitting the load lines every run. All nine runs have an **identical load
profile**:

```
{"AutoencoderKL": 1, "AutoencodingEngine": 1, "Lumina2": 3,
 "SDXL": 4, "SDXLClipModel": 1, "ZImageTEModel_": 1}      11 requested, 8 loaded completely
```

So every run did the same loading work. The arms are matched on the load side,
which is the thing that could otherwise have explained a difference.

**Every delivered image was checked** for the flat-grey / flat-fill failure with
`tools/browser_harness/check_image.py`. All nine pass: `luma_sd` ≈ 67,
`flat_block_frac` ≈ 0.014 against a 0.08 limit, `grey53_frac` ≈ 0.0017 against
0.02. None is the silent failure.

### 1a. The denoise lever — **not quotable, and mechanistically it cannot be real**

```
P_D080 (0.80)  mean 321.0 s   n=3   min 317.1  max 326.6   range  9.5  sd  5.0
P_D035 (0.35)  mean 308.8 s   n=3   min 300.3  max 320.0   range 19.7  sd 10.1

delta (mean)   = -12.1 s
delta (median) = -13.0 s
ranges OVERLAP  (D080 [317.1, 326.6] vs D035 [300.3, 320.0])
```

The measured delta is **smaller than the within-arm spread of one of the two
arms**, and the ranges overlap. On the rule I fixed before reading the numbers,
that is **not quotable**.

**And it should not be, because the lever cannot cost time.** This is the part I
would put in front of a buyer instead of a measurement, because it is read out of
the source rather than timed on a shared box. `comfy/samplers.py:1145-1155`:

```python
def set_steps(self, steps, denoise=None):
    ...
    new_steps = int(steps/denoise)
    sigmas = self.calculate_sigmas(new_steps).to(self.device)
    self.sigmas = sigmas[-(steps + 1):]
```

and the path `FaceDetailer` actually takes, `ComfyUI-Impact-Pack`
`modules/impact/impact_sampling.py:205-207`:

```python
advanced_steps = math.floor(steps / denoise)
start_at_step  = advanced_steps - steps
end_at_step    = start_at_step + steps
```

At `steps = 8`:

| denoise | advanced_steps | start | end | **steps executed** |
|---|---|---|---|---|
| 0.80 | 10 | 2 | 10 | **8** |
| 0.35 | 22 | 14 | 22 | **8** |

**Both arms run exactly 8 sampling steps.** `denoise` selects *where on the sigma
schedule* the face pass starts, not how much compute it does. The only extra work
at 0.35 is computing a 22-entry sigma array instead of a 10-entry one, which is
microseconds of CPU.

So the honest public line is the one the brief predicted: **"denoise 0.35 is
free."** The −12.1 s I measured is noise pointing in a flattering direction, and
I am explicitly *not* claiming it. It is also consistent with the matched-cache
warm figure of 0.4 s that was recorded before I started.

### 1b. The `cpu` CLIPLoader — a real effect, but I cannot give a clean number

```
P_CLIPDEF (default)  mean 279.8 s  n=3  min 257.3  max 292.7  range 35.4  sd 19.6
P_D035    (cpu)      mean 308.8 s  n=3  min 300.3  max 320.0  range 19.7  sd 10.1

delta (mean)   = +29.0 s   (cpu is slower)
delta (median) = +16.8 s
ranges are DISJOINT  (CLIPDEF max 292.7  <  D035 min 300.3)
```

This one is **directionally solid but numerically soft**, and the two statistics
disagree by a factor of nearly two (mean +29.0 s, median +16.8 s), which is
itself a warning.

What supports it being real:
- The ranges are **disjoint**. With n=3 vs n=3, perfect separation by chance has
  probability 1/C(6,3) = **0.05**.
- It has a mechanism: `device=cpu` keeps the Qwen text encoder in system RAM, so
  its weights cross PCIe on every use instead of living in VRAM.
- The direction matches the ~+14 s that was estimated but never measured cold.

What stops me quoting it:
- **A systematic confound I did not design out.** `P_CLIPDEF` ran under
  systematically *lighter* external load: mean `vram_free` at submit was
  **59.1 GiB** for CLIPDEF against **42.4 GiB** for D035. The other two servers
  were quieter during CLIPDEF's slots. The Latin square balances position within
  a round; it does not balance an external cycle that happens to alias with my
  run cadence, and this one did.
- The 257.3 s run is a 35 s outlier and it drags the mean well below the median.
- n=3.

**Verdict: `cpu` costs something, most likely in the +15 to +30 s band on a cold
render, and I would not put a single number in front of a buyer.** What I would
say is: *the black-face fix costs roughly 5–10 % of a cold render, and it is
worth it* — because the alternative is a ruined face.

### The decisive follow-up

Both whole-render deltas are differences of ~300 s totals, most of which is model
loading, so a lever worth seconds is buried. The fix is to time the two nodes
directly off the websocket `executing` transitions, which gives per-node
durations and is immune to the load confound entirely.

*(results below)*

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
