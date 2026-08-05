# WS5 — distribution re-cut

Everything below is either quoted command output or a file/line reference.
Anything I could not run is called out as not run, not glossed.

---

## READ FIRST — exactly which phases were exercised over the wire

The happy-path install finished `exit 0 in 83s` with **0 bytes downloaded**.
That is not a cold install. Precisely:

**Exercised over the wire, for real:**

- the gist fetch (`api.github.com/gists/…`, and the raw CDN URL for comparison)
- the pack download over HTTP with an `Authorization: Bearer` header, in all
  three states: rejected token (401), non-archive body with HTTP 200, and a
  successful transfer
- `git clone` of all 18 custom node packs to their pinned commits, from GitHub
- the archive fetch from the live HF repo — verified separately, byte-identical
  to the committed artifact (§4)

**NOT exercised over the wire:**

- **the 178 GB model pull.** The models were already on this pod and were
  hardlinked into the install target, so the bulk `hf download` ran as a
  *verification* pass and fetched nothing. A cold 178 GB pull has **not** been
  re-verified by me. STATE.md records it verified cold once
  (`PROFILE=all, 178.4 GB in 84 files, 6m36s`) on a pod that no longer exists;
  my run reports **178.8 GB in 87 files**, so the set has grown by 3 files since
  that measurement. Do not read "full install verified green" as covering a cold
  pull.
- **the pip dependency resolution for the node packs.** They were already
  satisfied in the shared `/venv/main`, so every `pip install` was a no-op
  (`pip freeze` identical before and after). A pod with a fresh venv does real
  work here that I did not exercise.
- **HF delivery of the *new* artifact**, because I have no upload mandate. The
  leg itself is proven against the *current* artifact (§4).

**What the `integrity: OK` line actually means.** This is a genuinely strong
check and deserves not to be undersold, but the distinction is exactly the kind
of thing that gets rounded up later into "verified", so stating it precisely:

> `integrity: OK` is a **per-file byte-exact size check of all 87 files against
> the Hub API's own figures**. It is **not** a content hash, and my run
> downloaded nothing.

The mechanism is `aiofm_setup.sh:1424-1476`: it walks every file under `models/`,
compares `stat -c %s` against a manifest of byte-exact sizes fetched from the Hub
API at the start of the run, and reports short versus over-size files separately
with signed deltas — the two having opposite remedies. Content hashing is done by
`hf download` on the files it actually downloads; mine downloaded none, so no
content hash was recomputed on this run.

No render was performed and no image was judged.

---

## 1. The name mismatch — fixed, and which name won

**Decision: the archive name wins. `dist/AIOFMTech-NSFW.tar.gz` now unpacks to
`AIOFMTech-NSFW/`.**

### The evidence that decided it

The sibling pack in the same HF repo already matches. I downloaded it:

```
$ tar tzf AIOFMTech-Video.tar.gz
AIOFMTech-Video/
AIOFMTech-Video/aiofm_setup.sh
AIOFMTech-Video/AIOFM Character Animation v1.2.json
```

`AIOFMTech-Video.tar.gz` → `AIOFMTech-Video/`. So `AIOFMTech-<product>` is an
existing convention and the NSFW pack was the one out of step, not the one
setting a new rule.

### The mechanical reason, which matters more

The live bootstrap (`aiofm_setupnsfw.sh`) treats the two names very differently:

- line 24: `PACK_PATH="dist/AIOFMTech-NSFW.tar.gz"` — the archive path is
  **hardcoded**.
- line 99: `PACK_TOP="$(tar -tzf "${TMP}/pack.tar.gz" | sed -n '1{s|/.*||;p;}')"`
  — the directory is **read out of the archive at run time**.

So renaming the **directory** needs no gist edit and republishes over the same
HF path — a buyer running any revision of the bootstrap gets the new pack.
Renaming the **archive** would require the gist edited in lockstep, and if that
paste is late or forgotten, every buyer silently keeps fetching the old
`dist/AIOFMTech-NSFW.tar.gz` while the new artifact sits unread beside it, with
no error anywhere. That is the exact class of silent failure this project keeps
being bitten by, so the change was made on the side that cannot have it.

### Every place the directory name is referenced

```
$ grep -rn 'OFMTech-NSFW\|AIOFMTech' OFMTech-NSFW/
OFMTech-NSFW/INSTALL MODELS.txt:33:    cd /workspace/OFMTech-NSFW
OFMTech-NSFW/aiofm_setup.sh:1138:    printf '            cd /workspace/OFMTech-NSFW && bash aiofm_setup.sh\n'
```

Two, both instructions a buyer is meant to type, both updated to
`/workspace/AIOFMTech-NSFW` (commit `9f0e1a7`). Nothing else in the pack names
the directory. The HF repo has no README to update (its non-`models/` contents
are exactly `.gitattributes`, `dist/AIOFMTech-NSFW.tar.gz`,
`dist/AIOFMTech-Video.tar.gz`).

### The git tree deliberately still says `OFMTech-NSFW/`

Renaming the source directory would rewrite paths WS1, WS3 and WS4 were editing
live. `tools/build_pack.sh` does the rename at pack time via a staging
directory and then **asserts** the result on the finished archive, using the
same `sed` expression the bootstrap uses:

```bash
PACK_TOP="$(sed -n '1{s|/.*||;p;}' "$LIST")"
[[ "$PACK_TOP" == "$TOP" ]] || { echo "✗ bootstrap PACK_TOP would read ..."; exit 1; }
```

The names cannot drift apart again without the build failing. Renaming the git
directory to match is a tidy-up for after the branch merges; nothing depends on
it.

---

## 2. The build

`tools/build_pack.sh`, committed. Reproducible: sorted entries, fixed mtime
(`SOURCE_DATE_EPOCH` default 1767225600), zeroed owner/group, normalised modes,
`gzip -n`. Verified:

```
run1=a0a6032c75c2cedbe1e8581f399ab9e3c1739873d520290a02ce3941727c633f
run2=a0a6032c75c2cedbe1e8581f399ab9e3c1739873d520290a02ce3941727c633f
REPRODUCIBLE
```

Junk excluded (declared once, in the script): `__pycache__`, `*.pyc/pyo/pyd`,
`.ipynb_checkpoints`, `.git`, `.gitignore`, `.gitattributes`, `.mypy_cache`,
`.pytest_cache`, `.ruff_cache`, `.DS_Store`, `._*`, `Thumbs.db`, `desktop.ini`,
`*.swp/swo`, `*~`, `#*#`, `.#*`, `*.orig`, `*.rej`, `.idea`, `.vscode`, `*.log`.
The source tree was already clean of all of them — `find` for every pattern
returned nothing — so exclusion is insurance, not a repair.

### A trap worth recording

The first version of the assertion block was:

```bash
tar -tzf "$ARCHIVE" | grep -qx "$TOP/OFMTech_NSFW.json" || die ...
```

It reported the workflow **missing from an archive that contained it**.
`grep -q` exits on its first match, `tar` takes SIGPIPE, and `set -o pipefail`
turns that into exit 141. The check therefore fails loudest exactly when the
file *is* present, and passes for `aiofm_setup.sh` only because that entry
sorts last. This is the same SIGPIPE/pipefail hazard STATE.md records the gist
bootstrap avoiding by using `sed` rather than `head`. The listing is now taken
once into a file and grepped there.

### Old vs new file list

`tools/compare_pack.sh OLD NEW` reports additions, removals and per-entry
content changes, comparing paths *below* the top-level directory so the rename
does not read as "164 removed, 170 added".

A note on reading its output: the ADDED block is printed with its count on the
first line. I clipped that line with `tail` once and briefly thought WS3 had
added five files rather than six. Read the whole block, or read the count.

*(Final cut numbers: see §6.)*

---

## 3. What is actually live in the gist, right now

Read from `https://api.github.com/gists/70256ac1ebf2760e10f78804862db528`,
which is authoritative and immediate where the raw URL is a CDN cache:

```
  gist            : 70256ac1ebf2760e10f78804862db528  (public=False, owner=msit270)
  updated_at      : 2026-08-05T20:40:36Z
  files in gist   : aiofm_setupnsfw.sh, aiofm_setupvideo.sh
  aiofm_setupnsfw.sh : 5114 bytes (5104 characters), 116 lines, truncated=False
  sha256 (api)    : bf80cb656be8d69c62150f9ceed42dbd8f6b228411b19e790795a7d25f45589a
  sha256 (raw CDN): bf80cb656be8d69c62150f9ceed42dbd8f6b228411b19e790795a7d25f45589a
  raw CDN matches the API right now
```

**STATE.md is correct**: 116 lines / 5,114 B is exactly what is live. Note
`len()` on the API string gives 5,104 — the 10-byte difference is multi-byte
characters, which is the trap STATE.md flags; the script prints both so the
number can never be mistaken again. The raw CDN happens to be in sync at this
moment; that is a fact about now, not a property, and it will lag the moment
the gist is edited.

### The `aiofm_setupall.sh` question — answered, and it was a live defect

`aiofm_setup.sh:39` set

```
SETUP_URL="…/70256ac1ebf2760e10f78804862db528/raw/aiofm_setupall.sh"
```

**That file does not exist.** The gist holds exactly two files, neither of them
`aiofm_setupall.sh`, and the raw URL 404s:

```
  aiofm_setupall.sh (named by aiofm_setup.sh SETUP_URL): HTTP 404
```

`SETUP_URL` is printed in two places, and both are recovery instructions handed
to a buyer who is **already stuck**: the "HF_TOKEN not found … then run this
script again: `bash <(curl -sSL "$SETUP_URL")`" message at line 58, and the
low-memory retry hint at line 701. Both were telling a stuck buyer to pipe a
404 body into bash. Repointed at `aiofm_setupnsfw.sh` (commit `bf96d0a`).

The relationship, established rather than assumed:

| thing | gist | contents |
|---|---|---|
| NSFW bootstrap | `70256ac1…` | `aiofm_setupnsfw.sh` 5,114 B / 116 lines |
| Video bootstrap | `70256ac1…` | `aiofm_setupvideo.sh` 5,474 B / 124 lines |
| Video pack's own `SETUP_URL` | `e5aa1b82…` | one file, `aiofm_setup.sh`, 75,268 B / 1,643 lines — the *full installer*, the older "pipe the whole thing" model |
| `aiofm_setupall.sh` | — | **does not exist anywhere** |

The two bootstraps are near-identical siblings; `aiofm_setupvideo.sh` differs in
`PACK_PATH="dist/AIOFMTech-Video.tar.gz"` and its `PACK_TOP` handling is the
same. The two packs do **not** share a bootstrap, so the `SETUP_URL` change
cannot affect the video pack.

---

## 4. Verification of the live buyer path

Harness: `tools/verify_buyer_path.sh`, committed. It pipes the bootstrap
**fetched from the API** — not from a stale CDN — into a fresh install target.

### How the running ComfyUI was protected

`/workspace/ComfyUI` is managed by supervisord:

```
$ supervisorctl status
comfyui                          RUNNING   pid 8567, uptime 0:58:29
```

`aiofm_setup.sh`'s restart stage runs `supervisorctl restart <comfy program>`
whenever `comfy_up()` succeeds — and it discovers the program **by name**, so
setting `COMFYUI_PORT` to my own instance would *still* have restarted the
shared one and killed other agents' renders. The harness therefore forces
`COMFYUI_PORT` to a dead port (39997, checked dead before the run). The
installer takes its "ComfyUI is not running" branch and touches nothing. Node
registration is then verified by the harness against its own instance, which is
a **stricter** check: that instance's `custom_nodes` started empty.

### How the full model pull was avoided

The target's `models/` is hardlinked from the live install (178.8 GB for 0
bytes) and `hf`'s per-file download metadata is copied with it, so the bulk pull
re-verifies instead of re-fetching.

One thing that had to be got right: `rsync --exclude 'models/'` is **unanchored**
and also matches `.cache/huggingface/download/models/`, which is where that
metadata lives. Losing it turns "verify 74 files" into "re-download 178 GB",
and the only symptom is a metadata count of 0 — which is what I saw:

```
  hf download metadata: 0 files      <- unanchored exclude
  hf download metadata: 74 files     <- '/models/'
```

### Case 1 — no token

```
env -u HF_TOKEN HF_TOKEN_FILE=<nonexistent> AIOFM_DEST=… bash aiofm_setupnsfw.sh
```

```
  === AIOFM · OFMTech NSFW — bootstrap ===

  ==========================================================
    No HuggingFace token found.

    The models live in a private repository, so the install
    cannot start without one. Create the file first:

      echo "hf_yourtoken" > /workspace/.hf_token

    (replace hf_yourtoken with your real token), then run
    this same command again.
  ==========================================================

  --> exit code 1
```

**Intelligible to a first-time buyer: yes.** It names the problem, the exact
command to fix it, and what to do next. Nothing is written to disk first.

### Case 2a — rejected token

```
  read your HuggingFace token from /workspace/ws5-verify/bad.token
  downloading the pack from msit270/AIOFM-Pack …
curl: (22) The requested URL returned error: 401

✗ could not download dist/AIOFMTech-NSFW.tar.gz from msit270/AIOFM-Pack.
  Check that your token is valid and has access to that repository.
  URL: https://huggingface.co/msit270/AIOFM-Pack/resolve/main/dist/AIOFMTech-NSFW.tar.gz

  --> exit code 1
```

**Intelligible: yes**, with one wart — curl's raw progress meter and
`curl: (22)` are printed above the friendly message. A buyer sees noise, then a
correct explanation. Acceptable; not worth risking a change on the critical
path.

### Case 2b — bad archive (HTTP 200 that is not a gzip)

Served from a local HTTP mirror returning an HTML "401" page with status 200 —
the proxy case the bootstrap's guard exists for.

```
  using HF_TOKEN from the environment
  downloading the pack from msit270/AIOFM-Pack …
100   115  100   115 …

✗ the downloaded file is not a valid archive.
  Usually this means the token was rejected and an error page was saved instead.

  --> exit code 1
```

**Intelligible: yes**, and it correctly guesses the usual cause. Nothing is
unpacked. The temp directory is removed by the `trap`.

### Case 3 — happy path

Full install into an empty ComfyUI (`/workspace/comfy-ws5-verify`,
`custom_nodes` entries = 0 at start):

```
[14/14] ComfyUI restart
      ComfyUI expected on port 39997
      ✓ ComfyUI is not running — the new nodes will register when you start it

==========================================================
  profile        : all
  time           : 1m 23s
  downloaded     : nothing — everything was already on disk
  models total   : 178.8 GB in 87 files
  free space     : 223G
  integrity      : OK
  comfyui core   : 0.15.1 validated
  workflow nodes : all packs present — verified on first start
  node versions  : pinned
  frontend       : pinned 1.39.19
==========================================================

  --> exit code 0 after 83s
  shared venv unchanged (pip freeze identical before/after)
  unpacked to: /workspace/ws5-verify/dest-happy/…
```

All 18 node packs cloned at their pinned commits, `ofmtechclip` cloned, and
`ComfyUI_INSTARAW vendored @ 12afb909 (provenance marker)`.

Then, node registration on a fresh `--cpu` instance started from that target:

```
  workflow installed: /workspace/comfy-ws5-verify/user/default/workflows/OFMTech_NSFW.json
  up after 10s
  node types the workflow references : 51
  node types registered by ComfyUI    : 1935
  ✓ all 51 registered
  live models tree untouched (inode/size/mtime identical for every file)
```

51 types derived from the workflow the same way `aiofm_setup.sh`'s own
`comfy_verify_nodes` derives them (walking `definitions.subgraphs` and skipping
`Note`/`MarkdownNote`/subgraph hosts).

Blast radius, measured not assumed:

```
$ ps -p 8584 -o pid,etime,args --no-headers
   8584    01:10:32 /venv/main/bin/python main.py … --port 18188 …
LIVE ComfyUI on 18188 still up and answering
comfyui                          RUNNING   pid 8567, uptime 1:10:32
overlay         410G  188G  223G  46% /
```

Live instance never restarted, uptime unbroken, shared `/venv/main` unchanged
(`pip freeze` identical before and after), live `models/` byte-identical for all
87 files, disk 46% throughout — never near the 85% ceiling.

### WHAT I DID NOT RE-RUN — see also the READ FIRST block at the top

**The 178 GB model download was not re-executed.** The models were already
present on this pod and were hardlinked in, so the bulk pull ran in
*verification* mode and reported `downloaded: nothing — everything was already
on disk`. What that proves: the manifest build, the per-file byte-exact size
checks, the integrity arithmetic and the resume logic all run clean against a
complete tree. What it does **not** prove: that a cold pod pulls 178 GB
successfully today. **A genuinely cold full pull has not been re-verified by me
and should not be reported as if it had.**

**The HF delivery leg of the *new* archive is not verified**, because I am not
permitted to upload. What I did verify is that the leg works and that the
currently published object is exactly the committed one:

```
live HF bytes: 8202871
3f6d0f2ffd092cf9a1691684029030e37283dd484cd550573290677400aada76  live-hf.tar.gz
3f6d0f2ffd092cf9a1691684029030e37283dd484cd550573290677400aada76  dist/AIOFMTech-NSFW.tar.gz
IDENTICAL: the live HF object == the committed dist artifact
```

So the untested link is only "the new bytes reached HF", which the sha256 check
in §5 closes.

**No render was performed and no image was judged.** The blocker WS1 is fixing
is a browser-side failure; whether the graph now runs to an image is theirs to
report, not mine.

---

## 4b. What the published repo actually ships — DMD2 is still in it

**Yes. `models/loras/dmd2_sdxl_4step_lora_fp16.safetensors` is still in
`msit270/AIOFM-Pack`, 393,854,592 bytes, and every buyer on the default profile
receives it.**

This is not inference. The file arrived **on this pod, from the buyer install
path**, during the setup run at 21:25:

```
$ ls -l /workspace/ComfyUI/models/loras/
-rw-rw-r-- 2 root root 393854592 Aug 5 21:25 dmd2_sdxl_4step_lora_fp16.safetensors

$ sha256sum /workspace/ComfyUI/models/loras/dmd2_sdxl_4step_lora_fp16.safetensors
b3d9173815a4b595991c3a7a0e0e63ad821080f314a0b2a3cc31ecd7fcf2cbb8
```

and `hf` wrote its own download record for it, which is the mechanism, not a
coincidence:

```
$ cat .cache/huggingface/download/models/loras/dmd2_sdxl_4step_lora_fp16.safetensors.metadata
acc2b7d3bf163a223b8f25fcb1ad0cd76c0c179c
b3d9173815a4b595991c3a7a0e0e63ad821080f314a0b2a3cc31ecd7fcf2cbb8
1785965151.2124577
```

It is the upstream file, matched by content and not by filename:

```
$ curl -I https://huggingface.co/tianweiy/DMD2/resolve/main/dmd2_sdxl_4step_lora_fp16.safetensors
x-linked-size: 393854592
x-linked-etag: "b3d9173815a4b595991c3a7a0e0e63ad821080f314a0b2a3cc31ecd7fcf2cbb8"
```

Identical sha256. And the licence, read from the Hub API rather than from
memory:

```
tianweiy/DMD2       license=cc-by-nc-4.0  tags=['license:cc-by-nc-4.0']
```

**Main's framing was right and the mechanism is exactly as suspected.** The
NSFW `aiofm_setup.sh` no longer names DMD2 anywhere, and the graph genuinely
uses TDD instead — but the default `PROFILE=all` path is
`hf download msit270/AIOFM-Pack --include "models/*"` (line 657), and Python's
`fnmatch` `*` matches `/`, so that pattern sweeps the entire `models/` tree
recursively. **Removing a file from the fetch list does nothing; the file has to
leave the repo.**

Two things that check out clean, since "audit came back clean" is not to be
trusted on this project:

- **The TDD replacement is real, not a rename.** `sdxl_tdd_lora_weights.safetensors`
  is coincidentally the same size (393,854,592 B) as DMD2, which is exactly the
  shape of a bad swap — so I compared the bytes. `cmp` says they differ at offset
  350,299, and TDD's sha256 `88981de843013d395c689cb29101f7e0f8a7f856813a7cfb6adf6a7be0e1cd6a`
  matches `RED-AIGC/TDD`'s `x-linked-etag` exactly. `RED-AIGC/TDD` is
  `license=apache-2.0`. TDD also has **no** `.metadata` file, confirming it comes
  from the public `dl_public` fetch and not from the AIOFM-Pack bulk pull — it is
  not in the repo at all.
- **Neither workflow references DMD2.** Not in `OFMTech_NSFW.json`, and not in
  the video pack's `AIOFM Character Animation v1.2.json` either.

### Everything in the repo that no code path names

Reconciled by taking every basename under `models/` in the repo and grepping
`aiofm_setup.sh` for it. Only **two** real files are unreferenced:

```
      2132696762  models/checkpoints/v1-5-pruned-emaonly-fp16.safetensors   named in workflow json: no
       393854592  models/loras/dmd2_sdxl_4step_lora_fp16.safetensors        named in workflow json: no

  subtotal: 2,526,551,354 bytes (2.53 GB)
  plus 31 ComfyUI placeholder/config files totalling 23,243 bytes
```

- **`dmd2_sdxl_4step_lora_fp16.safetensors`** — cc-by-nc-4.0. See above. This is
  a licence problem, not a weight problem.
- **`v1-5-pruned-emaonly-fp16.safetensors`** — 2.13 GB of Stable Diffusion 1.5,
  sha256 `e9476a13728cd75d8279f6ec8bad753a66a1957ca375a1464dc63b37db6e3916`,
  identical to `Comfy-Org/stable-diffusion-v1-5-archive`, which the Hub API
  reports as `license=creativeml-openrail-m`. Referenced by no script and no
  workflow in either pack. It is 2.13 GB every buyer downloads for nothing, and
  RAIL-M carries use restrictions that flow down to redistributors, so it is a
  smaller version of the same problem. (On this pod it also exists as a symlink
  into the pod image's `/opt/model_store`, but `hf` wrote a `.metadata` record
  for it too, so a buyer whose image lacks it does receive the 2.13 GB.)
- The 31 placeholders are ComfyUI's own `put_*_here` marker files and
  `models/configs/*.yaml`. 23 KB total. Harmless.

**Before deleting DMD2 from the repo, note this:** the **video pack's**
`aiofm_setup.sh:810` still contains

```
dl "$REPO/dmd2_sdxl_4step_lora_fp16.safetensors" "$COMFYUI_DIR/models/loras"
```

so the two products share the repo and the video installer explicitly fetches
DMD2 — even though the video workflow does not reference it either. Removing the
file from the repo without also removing that line makes every video-pack
install print `failed: dmd2_sdxl_4step_lora_fp16.safetensors`. **Both changes
have to happen together.** I have made neither; that is the user's call, and I
have no delete mandate on the repo. Logged in `WS5-questions.md`.

---

## 4c. The artifact contains two non-commercial code trees

Recording this at main's instruction. **The tarball I cut contains both trees.
Nothing was deleted.** The exact paths, all under
`AIOFMTech-NSFW/ComfyUI_INSTARAW/`:

**UnMarker** — `github.com/andrekassis/ai-watermark`, "non-commercially … for
research or evaluation purposes only" (verified by WS3 and independently by
main):

- `modules/detection_bypass/utils/adaptive_filter.py`
- `modules/detection_bypass/utils/unmarker_losses.py`
- `modules/detection_bypass/utils/unmarker_full.py` *(imports both of the above;
  same derivation)*

**GrainNet** — `github.com/Gwilherm-LESNE/Neural_Film_Grain_Rendering`,
"academic research use only":

- `modules/neural_grain/net.py`
- `pretrained/neural_grain/grainnet.pt`
- `nodes/utility_nodes/neural_grain_node.py` *(the wrapper; it is ours, but it is
  useless without the two above)*

Neither `INSTARAW_NeuralGrain` nor `INSTARAW_Spectral_Normalizer` appears in
`OFMTech_NSFW.json` — I confirmed that independently against the 51 node types I
derived from the workflow. Removing them changes no rendered output.

### Would a naive delete break the pack? YES — measured, not reasoned

I tested it on my isolated `--cpu` instance rather than arguing about it. Moved
the four encumbered paths aside, restarted, read `/object_info`, restored:

```
=== BASELINE (all files present) ===
  INSTARAW node types registered: 95

=== after moving the licence-encumbered files aside ===
  INSTARAW node types registered: 0
  LOG: ModuleNotFoundError: No module named '…ComfyUI_INSTARAW.modules.detection_bypass.utils.unmarker_losses'
  LOG: Cannot import …/ComfyUI_INSTARAW module for custom nodes
  LOG:    0.0 seconds (IMPORT FAILED): …/custom_nodes/ComfyUI_INSTARAW

=== restoring ===
  INSTARAW node types registered: 95
```

**95 node types to 0.** Every import in the chain is unconditional and top-level,
with no `try`/`except` anywhere:

```
ComfyUI_INSTARAW/__init__.py            from .nodes import NODE_CLASS_MAPPINGS
  nodes/__init__.py:14                  from .utility_nodes import ...
    nodes/utility_nodes/__init__.py:82  from .neural_grain_node import ...
      neural_grain_node.py:10           from ...modules.neural_grain.net import GrainNet
    nodes/utility_nodes/__init__.py:100 from .spectral_normalizer_node import ...
      spectral_normalizer_node.py:4     from ...modules.detection_bypass.utils.non_semantic_attack import ...
        utils/__init__.py:12            from .unmarker_full import ...
          unmarker_full.py:19-20        from .unmarker_losses import ...
                                        from .adaptive_filter import AdaptiveFilter
```

So a `rm` of the encumbered files takes down **all 16 INSTARAW node types the
NSFW graph uses**, including `#483 INSTARAW_RealityPromptGenerator`, which
supplies the prompt, the negative and the seed for the whole pipeline. The buyer
sees a graph full of red nodes and one `IMPORT FAILED` line in a console they are
not reading. ComfyUI itself still starts — it wraps custom-node loading — so
nothing else looks wrong.

**A removal re-cut is therefore a code change, not a file deletion.** It needs,
at minimum:

- the two `from .` lines in `nodes/utility_nodes/__init__.py` (82 and 100), and
  their `NODE_CLASS_MAPPINGS` / `NODE_DISPLAY_NAME_MAPPINGS` entries, removed;
- the `unmarker_full` import dropped from
  `modules/detection_bypass/utils/__init__.py:12`, and `'SpectralNormalizer'`
  from its `__all__` at line 30;
- **and then whatever `pipeline.py`, `pipeline_v2.py`, `processor.py` and
  `non_semantic_attack.py` need. Those four also reference the UnMarker path and
  I did not trace them to a conclusion.** That is not a caveat to tidy away: it
  is the unbounded part of the job, and it is why "just delete the files" is the
  wrong mental model. Anyone picking this up should start by tracing those four,
  not by deleting anything.

### What a removal re-cut would cost

- **Paths to exclude:** the six listed above. `tools/build_pack.sh` takes them as
  `EXCLUDES` entries; no new tooling is needed.
- **Size delta:** `grainnet.pt` is the only large one. The rest are source files.
  Expect the archive to shrink by roughly the compressed size of `grainnet.pt`
  plus a few tens of KB — I have not measured it, because measuring it means
  cutting the alternative archive and I was told not to.
- **The sha256 changes.** That is the real cost. The published sha256 in this
  report, in `STATE.md`, and anywhere the user has recorded it must be updated in
  lockstep with the upload, or the verification command in §5 reports a mismatch
  that looks like a failed upload.
- **The code changes above must be verified by the same 95-to-0 test.** Rerun
  `bash tools/verify_buyer_path.sh nodes` and require 95 INSTARAW types, not just
  "it imported".
- **Not performed.** Per main's decision, and it is the right one: nothing
  reaches a buyer until the user runs the upload command in §5, so including these
  files today is fully reversible.

---

## 5. Upload command — for the user to run, not me

Do NOT run this until the tarball in §6 is the one you want published. It
overwrites the object buyers are fetching right now.

```bash
HF_TOKEN="$(tr -d '[:space:]' < /workspace/.hf_token)" \
/venv/main/bin/hf upload msit270/AIOFM-Pack \
    /workspace/nsfw-fix/dist/AIOFMTech-NSFW.tar.gz \
    dist/AIOFMTech-NSFW.tar.gz \
    --commit-message "NSFW pack re-cut: archive and directory names match; licence files; graph fixes"
```

The three positional arguments are repo, local path, path-in-repo, in that
order. `dist/` is deliberate — it keeps the artifact out of the bulk
`hf download --include "models/*"`, which would otherwise sweep it and then
size-verify it against a manifest that does not list it.

Then verify from the buyer's side, which is the only side that counts:

```bash
curl -fsSL -H "Authorization: Bearer $(tr -d '[:space:]' < /workspace/.hf_token)" \
  "https://huggingface.co/msit270/AIOFM-Pack/resolve/main/dist/AIOFMTech-NSFW.tar.gz" \
  | sha256sum
```

It must print the sha256 recorded in §6. If it prints
`3f6d0f2ffd092cf9a1691684029030e37283dd484cd550573290677400aada76`, that is the
**old** artifact and the upload did not land — retry rather than assuming CDN
lag.

---

## 6. The cut

*(filled in below once main confirmed the tree was final)*

---

## 7. Does the bootstrap need updating?

**No — nothing breaks if you never touch the gist.** That is a consequence of
choosing to rename the directory rather than the archive: `PACK_PATH` still
points at `dist/AIOFMTech-NSFW.tar.gz`, which is still where the artifact goes,
and `PACK_TOP` is still read out of the archive.

There is one comment in it that is now false. Lines 95-98 currently assert:

```
# The archive's filename and its top-level directory are NOT the same thing --
# the published file is AIOFMTech-NSFW.tar.gz and it unpacks to OFMTech-NSFW/.
```

The exact replacement text is committed at `gist/aiofm_setupnsfw.sh`. To apply
it: open <https://gist.github.com/msit270/70256ac1ebf2760e10f78804862db528>,
edit the file `aiofm_setupnsfw.sh`, and replace its **entire** contents with
that file (118 lines, 5,310 B). Do not hand-edit only the comment — replacing
wholesale is what makes the result checkable.

It is comment-only, and that is proven rather than claimed:

```
$ diff <(grep -v '^\s*#' live) <(grep -v '^\s*#' proposed)
NO CODE CHANGE — comment-only
$ bash -n gist/aiofm_setupnsfw.sh
syntax OK
```

**If you do not paste it:** nothing at all breaks for a buyer. The only cost is
that the next person to read the bootstrap is told something about the archive
that stopped being true, and might "fix" the mismatch back.

**If you do paste it:** remember the raw CDN URL will keep serving the old text
for a while. Check with `api.github.com/gists/<id>`, not the raw URL. The
harness does this for you: `bash tools/verify_buyer_path.sh gist`.

---

## 8. Other things found, not fixed

- **`INSTALL MODELS.txt` step 1 contradicts the delivery method.** It says a
  one-line `bash <(wget ...)` install "will NOT get the custom nodes or the
  workflow". That is true of piping `aiofm_setup.sh` — the `PIPED` branch at
  line 1133 exists for it — and **false of the gist bootstrap**, which is also a
  one-line `bash <(wget ...)` and which exists specifically to make that work. A
  buyer handed the bootstrap one-liner and then reading this text has been told
  their install is broken when it is not. Left alone because it is product copy
  and rewriting it is a bigger call than a re-cut should make. It should be
  rewritten before sale.
- **`ComfyUI_INSTARAW` is copied, never overwritten** (`aiofm_setup.sh:1156`,
  "if the buyer already has a newer copy installed, leave it alone"). Correct
  for a buyer's own edits, but it also means a buyer who installed the current
  pack and re-runs after this re-cut keeps the **old** INSTARAW, including
  whatever WS3's licence work and WS1's fixes changed inside it. Worth a
  deliberate decision before the next release.
- **Existing buyers will end up with two directories.** Anyone who installed
  before this re-cut has `/workspace/OFMTech-NSFW` with a stale `aiofm_setup.sh`
  and the pre-fix workflow beside it. The bootstrap creates
  `/workspace/AIOFMTech-NSFW` and does not remove the old one. Low impact if the
  pack has not gone out yet; if it has, the release note should say "delete
  `/workspace/OFMTech-NSFW`".
- **The `Workflow node check` stage checks the video workflow's node list.**
  `aiofm_setup.sh:1531-1573` is a hardcoded list of Wan/KJ/VHS node types, and
  it printed `✓ all 40 workflow node types present` during an NSFW install
  without checking a single NSFW node type. The workflow-derived check that
  *would* catch it (`comfy_verify_nodes`) only runs after a successful restart,
  which is exactly the path I had to disable. Not a defect I introduced and not
  a blocker, but that green tick means less than it looks like.

---

## 9. Files I own on this branch

- `tools/build_pack.sh`, `tools/compare_pack.sh`, `tools/verify_buyer_path.sh`
- `gist/aiofm_setupnsfw.sh`
- `OFMTech-NSFW/aiofm_setup.sh`, `OFMTech-NSFW/INSTALL MODELS.txt`
- `dist/AIOFMTech-NSFW.tar.gz`
- `notes/WS5-report.md`, `notes/WS5-questions.md`

I did not touch `OFMTech-NSFW/OFMTech_NSFW.json` or anything under
`OFMTech-NSFW/ComfyUI_INSTARAW/`.
