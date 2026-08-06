# TRACK P — packaging, and the one honest timing number

Two jobs, reported separately because they have very different confidence levels.
The artifact block is mechanical and I stand behind every number in it. The
timing block is a measurement on a shared GPU and I have tried to say plainly
where it stops being quotable.

Server used throughout: **`127.0.0.1:28191`** (pid 144284, ComfyUI 0.15.1, tree
`/workspace/comfy-r2gate3`, `--reserve-vram 16`). `:18188` was never touched —
Track V is validating there and it is the only instance that reproduces the bug.

---

## READ FIRST

**The two timing numbers, with the verdict on each:**

| lever | measured | quotable? |
|---|---|---|
| `#114` denoise **0.80 → 0.35** | whole render −12.1 s (n=3 v n=3, ranges overlap) | **NO — and the effect is genuinely zero.** Both settings execute exactly 8 sampling steps. The −12.1 s exceeds the entire runtime of the only node that changed (6.5 s). Public line: **"denoise 0.35 is free."** |
| `#110` CLIPLoader **default → cpu** | whole render +29.0 s (confounded); **per-node +37.4 s** (n=2 v n=2, ~1 s spread) | **YES, at node level: ≈ +37 s per cold render**, all of it in four `CLIPTextEncode` nodes, none in the loader. ~12 % of a cold render. Worth paying — but it is **not** free. |

The whole-render cold numbers are **not** the deliverable I would stand behind;
the per-node numbers are. On a box with three ComfyUI servers sharing one GPU,
a ~300 s cold render carries ±20–35 s of variance, which swallows both levers.
Timing the individual nodes off the websocket removes that entirely.

**The artifact:**

```
dist/AIOFMTech-NSFW.tar.gz   8,155,371 B   sha256 8695a11e…3b8af   170 files (196 entries = 170 files + 26 dirs)
workflow inside it: f5bed596…7fd8   verified out of the archive, and again after a real install
```

170 → 170 files, zero additions, zero removals, exactly one member changed, and
within it exactly the two commits. All six buyer-path cases green. **Nothing was
uploaded and no credentials were requested.**

**One thing the owner should know that is not about my brief:** live HF still
serves `3f6d0f2f…` — four cuts behind. Neither graph fix has ever been published.

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

#### The measurement refutes itself, which is the cleanest evidence here

I timed the individual nodes off the websocket `executing` transitions. On a
**cold** run, node `620:114 FaceDetailer` — the *only* node whose input differs
between the two arms — takes:

```
P_D080  (denoise 0.80, cold)   620:114 = 6.47 s     whole render 308.7 s
P_D035  (denoise 0.35)         620:114 = 6.00 s
P_CLIPDEF (denoise 0.35, cold) 620:114 = 10.04 s
```

**The whole-render delta I measured (−12.1 s) is larger than the entire runtime
of the node it is supposed to have come from (6.47 s).** Even if the denoise
change had made `#114` instantaneous it could not have saved 12 s. That is
conclusive, and it needs no statistics: the −12.1 s is load noise, full stop.

Note also that the two *denoise-0.35* runs give 6.00 s and 10.04 s for the same
node — a 4 s spread at identical settings. Node-level timing is noisy here too,
so I am not claiming the 0.47 s difference either. What I am claiming is the
**bound**: the lever can move at most ~6–10 s, it mechanistically moves ~0, and
the warm matched-cache figure of 0.4 s is the best estimate anyone has.

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

#### Per-node timing localises it exactly, and this is the number I would quote

Rather than leave it at a confounded whole-render figure, I timed every node off
the websocket `executing` transitions on a **matched cold pair** that differs
only in `620:110.device` (both denoise 0.35, both `execution_cached: []`):

```
device=cpu      exec 313.7 s      device=default   exec 302.4 s
whole-render difference = +11.3 s
```

Per node, largest absolute differences:

| node | class_type | cpu (s) | default (s) | diff (s) |
|---|---|---|---|---|
| `622:398` | **CLIPTextEncode** | 11.29 | 0.03 | **+11.25** |
| `621:166` | **CLIPTextEncode** | 9.63 | 0.05 | **+9.58** |
| `620:106` | **CLIPTextEncode** | 10.54 | 1.25 | **+9.29** |
| `622:394` | **CLIPTextEncode** | 8.65 | 1.30 | **+7.35** |
| `620:110` | **CLIPLoader** | 2.11 | 2.34 | **−0.23** |
| `587:92` | FaceDetailer | 23.30 | 35.51 | −12.20 |
| `619:600` | KSamplerAdvanced | 1.83 | 7.54 | −5.71 |
| `587:98` | UltimateSDUpscale | 96.00 | 100.78 | −4.78 |

**The cost is not in the loader. It is in text encoding.**

```
four CLIPTextEncode nodes:  cpu 40.11 s   default 2.63 s   ->  +37.5 s
CLIPLoader 620:110 itself:  cpu  2.11 s   default 2.34 s   ->   -0.2 s
```

That is a 375× ratio on `622:398` (11.29 s vs 0.03 s), far outside any noise seen
at node level. The mechanism is exactly what you would expect: `device=cpu` keeps
the Qwen text encoder in system RAM, so its **forward pass runs on the CPU**. The
loading is unaffected — only the encoding is.

The rows below `620:110` in that table are the reason the whole-render number was
misleading. `587:92`, `619:600` and `587:98` swing by −12.2, −5.7 and −4.8 s
between two runs that did not differ in any input touching them; that is
ordinary run-to-run noise, and it cancelled most of the real +37.5 s, leaving a
whole-render figure of only +11.3 s. Summed over every node the diffs come to
+11.9 s, consistent with the +11.3 s total, so the accounting closes.

**Verdict on the CLIP lever.** The honest statement is:

> `#110 CLIPLoader device = cpu` costs about **+37 s of text-encoding time per
> cold render** — four `CLIPTextEncode` nodes going from ~2.6 s total on GPU to
> ~40 s total on CPU. The loader itself is free. On a ~300 s cold render that is
> roughly **12 %**.

This supersedes both the never-measured ~+14 s estimate and my own confounded
+29 s whole-render mean.

**It replicates, tightly.** I have four cold runs with node timing — two on each
device setting — and the text-encode total is essentially constant within each:

| run | cold | `622:398` | `621:166` | `620:106` | `622:394` | **encode total** | `620:110` loader |
|---|---|---|---|---|---|---|---|
| cpu, `n1_P_D080` | yes | 11.21 | 9.23 | 9.93 | 8.47 | **38.84** | 2.24 |
| cpu, `n2_P_D035` | yes | 11.29 | 9.63 | 10.54 | 8.65 | **40.11** | 2.11 |
| default, `n1_P_CLIPDEF` | yes | 0.03 | 0.05 | 1.25 | 1.30 | **2.63** | 2.34 |
| default, `n2retry2_P_CLIPDEF` | yes | 0.03 | 0.05 | 0.20 | 1.21 | **1.50** | 1.90 |

```
device=cpu     encode total: 38.8, 40.1   mean 39.5 s   (spread 1.3 s)
device=default encode total:  2.6,  1.5   mean  2.1 s   (spread 1.1 s)
cost of device=cpu = +37.4 s               (n=2 vs n=2)
```

The within-group spread is ~1 s against a between-group difference of 37 s. This
is the **one timing number in this report I would put in front of a buyer**, and
it is the opposite of the whole-render figures in that respect. It also crosses
arms: the cpu measurement holds on `P_D080` (denoise 0.80) and `P_D035`
(denoise 0.35) alike, as it should, since the two levers are independent.

It is still worth paying — the alternative is the black-face bug — but it is
**not** free, and it should not be described as free.

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

Run with `tools/verify_buyer_path.sh` against **these bytes**
(`dist/AIOFMTech-NSFW.tar.gz`, `8695a11e…`), piping the **live** gist into an
empty ComfyUI. The three cases the owner named are marked ★.

| case | what it proves | exit | verdict |
|---|---|---|---|
| `gist` | the bootstrap under test is the one actually live | **0** | pass |
| ★ `no-token` | refuses to start with no token, with a usable message | **1** | pass (1 is the expected outcome) |
| ★ `bad-archive` | a 200 response that is not a gzip archive is caught | **1** | pass (1 is the expected outcome) |
| `prepare` | builds a genuinely empty ComfyUI target | **0** | pass |
| ★ `happy` | full install from the live gist into that empty target | **0** | **pass, 85 s** |
| `nodes` | every node type the workflow needs actually registers | **0** | pass, 51/51 |

**On the exit codes.** `no-token` and `bad-archive` exit **1 by design** — they
are negative cases and exit 1 is the pass condition. I am stating that explicitly
because "exit 1" in a results table otherwise reads as a failure. `bad-token` was
not run this time; it is not one of the three named and it exercises the same
guard as `bad-archive`.

Detail worth keeping:

- **`gist`** — `api.github.com` and the raw CDN agree right now, sha256
  `bf80cb65…589a`, 5,114 bytes, 116 lines, gist updated `2026-08-05T20:40:36Z`.
  So the CDN is not serving a stale bootstrap.
- **`no-token`** — exits 1 with the "No HuggingFace token found" banner naming
  `/workspace/.hf_token`. The buyer is told what to do.
- **`bad-archive`** — a local mirror serves an HTML 401 page with HTTP **200**;
  the bootstrap's `tar -tzf` guard (line 85) catches it and prints "the
  downloaded file is not a valid archive… usually this means the token was
  rejected". Exit 1.
- **`happy`** — exit **0 after 85 s**. `integrity: OK`, `comfyui core 0.15.1
  validated`, node versions pinned, frontend pinned `1.39.19`, 178.8 GB across 87
  model files verified. **`pip freeze` identical before and after**, so the
  shared `/venv/main` was not mutated.
- **`nodes`** — a fresh ComfyUI started from the installed target on port
  **34011** (inside my assigned `34000-34099` range; I confirmed it free before
  binding and it was released afterwards). 51 node types referenced by the
  workflow, **51/51 registered** against 1,935 available.
- **The hardlink safety check passed**: "live models tree untouched (inode/size/
  mtime identical for every file)". Nothing wrote through to the ComfyUI tree
  Track V is running from.

**`PACK_TOP` proved end-to-end, by the installer rather than by my assertion.**
The real bootstrap unpacked the archive to:

```
/workspace/ws5-verify/dest-happy/AIOFMTech-NSFW/
```

which matches the archive basename. And the workflow the installer put in place
is bit-identical to the archive member:

```
installed : f5bed59676c6dc5f827100890cc98acd88b7b3c3e9295f50e5283118e9d77fd8
archive   : f5bed59676c6dc5f827100890cc98acd88b7b3c3e9295f50e5283118e9d77fd8
as installed: #114 denoise = 0.35     #110 device = cpu
```

So a buyer running the live command today would receive both fixes.

**Not exercised** (same limitations as WS5/P4/R5, not re-verified by me): a cold
178 GB model pull — the models were already on this pod and were hardlinked in,
so the bulk `hf download` ran as a verification pass; pip dependency resolution —
already satisfied, every install a no-op; and **HF delivery of this artifact**,
for which I have no mandate. **No render was performed from the installed tree,
so nothing here is a statement about output quality.**

### The artifact build is reproducible

Rebuilding from the same tree produced a byte-identical archive:
`8695a11e…3b8af` both times, 8,155,371 bytes. That is observed, not inferred from
the script's docstring — so the published sha256 is a statement about content.

### What is actually published right now

I checked HF rather than inheriting a hash from notes (read-only `HEAD`, nothing
uploaded):

```
x-linked-etag: "3f6d0f2ffd092cf9a1691684029030e37283dd484cd550573290677400aada76"
x-linked-size: 8202871
```

**Live HF is still `3f6d0f2f…`, 8,202,871 bytes** — unchanged since R5 recorded
it, and now four cuts behind. Neither `8d166e0` (denoise) nor `7ce1539` (the
black-face CLIP fix) has ever reached the Hub, and neither has the browser-bug
fix. Whatever a buyer downloads today contains none of them.

---

## Publishing

`HANDOFF.md` has been updated with the new hash and a commit message naming the
change. **Nothing was uploaded, and no credentials were requested.** The command
is printed there for the owner to run.
