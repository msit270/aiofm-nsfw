# P4 — distribution re-cut, against the D1-reverted tree

Everything below is quoted command output or a file/line reference. Where I am
inferring, it says so. Nothing here is reported as verified on the strength of
having read a script.

This repeats the work recorded in `notes/WS5-report.md` against a changed tree.
Read that first for *why* the tooling looks the way it does; this file is the
new run's evidence and the numbers that supersede it.

---

## READ FIRST — what this run does and does not prove

**Exercised over the wire, for real, against these bytes:**

- the gist fetch (`api.github.com/gists/…`, authoritative, plus the raw CDN URL
  for comparison)
- the pack download with an `Authorization: Bearer` header in three states:
  rejected token (401), non-archive body at HTTP 200, successful transfer
- `git clone` of all 18 custom node packs to their pinned commits, from GitHub
- `rife49.pth` fetched over HTTP during `[9/14]`
- a live `HEAD` against the HF repo, which is how I know nothing has been
  uploaded since the previous cut

**NOT exercised:**

- **a cold 178 GB model pull.** The models were already on this pod and were
  hardlinked into the install target, so the bulk `hf download` ran as a
  verification pass. Same limitation WS5 recorded; it has not been re-verified
  by me and must not be read as covered.
- **pip dependency resolution for the node packs.** Already satisfied in the
  shared `/venv/main`; every install was a no-op and `pip freeze` was identical
  before and after. A fresh venv does real work I did not exercise.
- **HF delivery of the new artifact.** I have no upload mandate and asked for no
  credentials. §6 is the command for the owner.

**No render was performed and no image was judged.** Nothing in this file is a
statement about output quality.

---

## 1. Two corrections to the brief I was given

### 1a. The three JS commits were already in the previous cut

My brief said `js/popup.js` (`342a038`, `3afa7ed`) and
`js/reality_prompt_generator.js` (`7de8c15`) "also changed since the last cut".
They did not. All three are ancestors of the previous cut's commit `3357ae3`:

```
$ for c in 342a038 3afa7ed 7de8c15; do git merge-base --is-ancestor $c 3357ae3 && echo yes; done
  342a038 : YES already in the previous cut
  3afa7ed : YES already in the previous cut
  7de8c15 : YES already in the previous cut
```

`notes/WS5-report.md:745` says the same thing independently — "main's
`342a038`/`3afa7ed`/`7de8c15` all in". **The only source change since the
previous cut is `73f3d5c`:**

```
$ git log --oneline 3357ae3..HEAD -- OFMTech-NSFW/
73f3d5c Revert D1: keep the VAE round-trip -- owner's call, on the A/B
```

This matters because it is what makes the expected delta a single changed file,
and §4 confirms that is exactly what came out. Had I taken the brief at face
value I would have expected three more changed members and had no way to tell a
correct build from a broken one.

### 1b. The previous cut was never published

`git status --porcelain OFMTech-NSFW/` was empty before the build, as required.
And the live HF object is still the **164-file** one:

```
$ curl -I -H "Authorization: Bearer …" \
    https://huggingface.co/msit270/AIOFM-Pack/resolve/main/dist/AIOFMTech-NSFW.tar.gz
HTTP/2 302
x-linked-size: 8202871
x-linked-etag: "3f6d0f2ffd092cf9a1691684029030e37283dd484cd550573290677400aada76"
```

So `15706aa7…` (WS5's cut) never shipped. **This cut supersedes it entirely.**
The owner has one upload to do, not two, and the "did it land?" check in §6 must
compare against `3f6d0f2f…`, **not** against WS5's `15706aa7…`.

---

## 2. The cut

Built with the committed `tools/build_pack.sh`. No hand-rolled tar.

```
$ bash tools/build_pack.sh

  archive        : /workspace/nsfw-fix/dist/AIOFMTech-NSFW.tar.gz
  top-level      : AIOFMTech-NSFW/   (matches archive name)
  entries        : 170 files
  size           : 8154217 bytes
  sha256         : 27fa2e1c5496c4d0efee7d5b626e7638b197e1327500f86936a2a9e918dd3d37

  shipped members (hashed out of the archive):
    OFMTech_NSFW.json  294296 bytes
      sha256       : f1ac7e55d375380033f6b0acc67ee0f4706dd618303075f86213fc09e6beb22e
    aiofm_setup.sh
      sha256       : 19667d8e96a737bc605b76fbed638ab1d8ccf2c83d374f91e3cb0b8f5c43cd46
```

Re-measured independently rather than trusting the builder's own print:

```
$ stat -c 'size: %s bytes' dist/AIOFMTech-NSFW.tar.gz
size: 8154217 bytes
$ sha256sum dist/AIOFMTech-NSFW.tar.gz
27fa2e1c5496c4d0efee7d5b626e7638b197e1327500f86936a2a9e918dd3d37
```

Reproducible, three builds from the same tree:

```
dist=27fa2e1c5496c4d0efee7d5b626e7638b197e1327500f86936a2a9e918dd3d37
run1=27fa2e1c5496c4d0efee7d5b626e7638b197e1327500f86936a2a9e918dd3d37
run2=27fa2e1c5496c4d0efee7d5b626e7638b197e1327500f86936a2a9e918dd3d37
REPRODUCIBLE (3/3 identical)
```

### The one number that matters: the workflow, read back out of the archive

```
$ tar -xzOf dist/AIOFMTech-NSFW.tar.gz AIOFMTech-NSFW/OFMTech_NSFW.json | sha256sum
f1ac7e55d375380033f6b0acc67ee0f4706dd618303075f86213fc09e6beb22e
```

That is the required `f1ac7e55…`, off the finished artifact and not off the
source tree. The same digest at every point it can be observed — the fourth line
is where a buyer's ComfyUI actually reads it from, in the install performed in
§5, not a copy I made:

```
  1. source tree                                  : f1ac7e55…beb22e
  2. member of dist/AIOFMTech-NSFW.tar.gz         : f1ac7e55…beb22e
  3. unpacked pack dir the installer ran from     : f1ac7e55…beb22e
  4. user/default/workflows/OFMTech_NSFW.json     : f1ac7e55…beb22e
```

Archive-member hashing is the right instrument here. **The project's ban is on
hashing rendered output**, and none of this is that.

### The D1 revert is in the shipped bytes, not just in git

Parsed out of the archived copy, not out of the source tree:

```
  subgraphs: 7
    3. Hands, Skin & Second Upscale (SDXL)    14 nodes
    2. Base Generator (SDXL)                  28 nodes
    5. Face & Mouth Detail (Z-Image)          12 nodes
    4. Mouth Resources & Colour Reconcile      5 nodes
    6. Eyes (FaceMesh crop/composite)         18 nodes
    7. Anatomy Detailers - DISABLED           11 nodes
    1. Canvas & Routing                        4 nodes
    node #597 type=VAEEncode  (in subgraph '2. Base Generator (SDXL)')
    node #616 type=VAEDecode  (in subgraph '2. Base Generator (SDXL)')
```

`#597`/`#616` back, "2. Base Generator (SDXL)" at 28 nodes, and the seven stages
carry their real names rather than seven copies of "Dont touch!!!".

---

## 3. Archive name vs internal directory — the assertion, observed firing

The requirement is that `AIOFMTech-NSFW.tar.gz` unpacks to `AIOFMTech-NSFW/`,
and that the builder's assertion actually ran rather than being assumed to have.

**Observed executing.** The same script under `bash -x`, with the values
expanded:

```
86:++ awk -F/ '{print $1}' /tmp/aiofm-pack.BDKwzq/.listing
87:+ TOPS=AIOFMTech-NSFW
88:+ [[ AIOFMTech-NSFW == \A\I\O\F\M\T\e\c\h\-\N\S\F\W ]]
89:++ sed -n '1{s|/.*||;p;}' /tmp/aiofm-pack.BDKwzq/.listing
90:+ PACK_TOP=AIOFMTech-NSFW
91:+ [[ AIOFMTech-NSFW == \A\I\O\F\M\T\e\c\h\-\N\S\F\W ]]
93:+ grep -qxF AIOFMTech-NSFW/aiofm_setup.sh /tmp/aiofm-pack.BDKwzq/.listing
95:+ grep -qxF AIOFMTech-NSFW/OFMTech_NSFW.json /tmp/aiofm-pack.BDKwzq/.listing
97:+ grep -qxF 'AIOFMTech-NSFW/INSTALL MODELS.txt' /tmp/aiofm-pack.BDKwzq/.listing
```

Both comparisons ran on real derived values, and all three required members were
checked. Note lines 93-97 grep a **file**, never `tar -tzf … | grep -q …` — that
pipeline exits 141 under `pipefail` when the pattern matches early, i.e. it
fails loudest exactly when the file *is* present. It is why the builder takes
the listing into a file once.

**The expression is the buyer's, verbatim.** Line 99 of the bootstrap I fetched
from the GitHub API in §5:

```
24:PACK_PATH="dist/AIOFMTech-NSFW.tar.gz"      # path INSIDE the HF repo
99:PACK_TOP="$(tar -tzf "${TMP}/pack.tar.gz" | sed -n '1{s|/.*||;p;}')"
```

Same `sed -n '1{s|/.*||;p;}'`. So the archive is checked the way the installer
reads it, not an approximation of it.

**Negative control — the assertion is not a tautology.** A passing check on a
value derived from the thing it is checking is worth little unless it can fail,
so I ran the identical expression on the previously published archive:

```
=== apply the bootstrap's OWN sed expression to the NEW archive ===
  archive basename : AIOFMTech-NSFW.tar.gz
  expected TOP     : AIOFMTech-NSFW
  PACK_TOP read    : AIOFMTech-NSFW
  MATCH
  distinct top-level dirs in archive: AIOFMTech-NSFW

=== NEGATIVE CONTROL: same expression on the previously PUBLISHED archive ===
  PACK_TOP read    : OFMTech-NSFW
  would FAIL the assertion -- expression discriminates, it is not a tautology
```

The old published artifact is exactly the case the assertion exists to catch,
and it is caught.

---

## 4. Full file-list delta

Two baselines, because they answer different questions. Both recovered from git,
so anyone can redo this without my scratch space.

### 4a. vs the PREVIOUS CUT — is this build only the D1 revert?

`git show 3357ae3:dist/AIOFMTech-NSFW.tar.gz`, sha256 `15706aa7…d069e` — verified
by running exactly that. Both baselines below come out of git, so this whole
comparison can be redone at any time without my scratch space:

```bash
git show 3357ae3:dist/AIOFMTech-NSFW.tar.gz > /tmp/prevcut.tar.gz    # 15706aa7…d069e
git show 8e7b1c3:dist/AIOFMTech-NSFW.tar.gz > /tmp/published.tar.gz  # 3f6d0f2f…aada76
bash tools/compare_pack.sh /tmp/prevcut.tar.gz   dist/AIOFMTech-NSFW.tar.gz
bash tools/compare_pack.sh /tmp/published.tar.gz dist/AIOFMTech-NSFW.tar.gz
```

```
  old : top-level AIOFMTech-NSFW/   8154042 bytes   sha256 15706aa7…d069e
  new : top-level AIOFMTech-NSFW/   8154217 bytes   sha256 27fa2e1c…d3d37

  files: 170 old -> 170 new

  ADDED: none

  REMOVED: none

  CHANGED (1):
    ~ OFMTech_NSFW.json
```

**One changed member, zero additions, zero removals.** That is precisely
`73f3d5c` and nothing else, which is the strongest statement available that this
build carries no accidental cargo. The 175-byte size increase is the compressed
cost of `#597`/`#616` returning (294,296 vs 290,550 bytes uncompressed).

### 4b. vs the PUBLISHED archive — what a buyer actually receives that changed

`git show 8e7b1c3:dist/AIOFMTech-NSFW.tar.gz`, sha256 `3f6d0f2f…aada76`,
confirmed above to be the object live on HF right now.

```
  old : top-level OFMTech-NSFW/     8202871 bytes   sha256 3f6d0f2f…aada76
  new : top-level AIOFMTech-NSFW/   8154217 bytes   sha256 27fa2e1c…d3d37

  files: 164 old -> 170 new

  ADDED (6):
    + ComfyUI_INSTARAW/THIRD_PARTY_NOTICES.md
    + ComfyUI_INSTARAW/fonts/OFL.txt
    + ComfyUI_INSTARAW/licenses/Apache-2.0.txt
    + ComfyUI_INSTARAW/licenses/ICC-sRGB-profile-license.txt
    + ComfyUI_INSTARAW/licenses/MIT-Filmgrainer.txt
    + ComfyUI_INSTARAW/licenses/OFL-1.1-BricolageGrotesque.txt

  REMOVED: none

  CHANGED (21):
    ~ ComfyUI_INSTARAW/js/filter.css
    ~ ComfyUI_INSTARAW/js/floating_window.css
    ~ ComfyUI_INSTARAW/js/floating_window.js
    ~ ComfyUI_INSTARAW/js/image_filter.js
    ~ ComfyUI_INSTARAW/js/log.js
    ~ ComfyUI_INSTARAW/js/mask_utils.js
    ~ ComfyUI_INSTARAW/js/popup.js
    ~ ComfyUI_INSTARAW/js/reality_prompt_generator.js
    ~ ComfyUI_INSTARAW/js/utils.js
    ~ ComfyUI_INSTARAW/js/zoomed.css
    ~ ComfyUI_INSTARAW/modules/detection_bypass/filmgrainer_local/filmgrainer.py
    ~ ComfyUI_INSTARAW/modules/detection_bypass/filmgrainer_local/graingamma.py
    ~ ComfyUI_INSTARAW/modules/detection_bypass/filmgrainer_local/graingen.py
    ~ ComfyUI_INSTARAW/nodes/interactive_nodes/image_filter.py
    ~ ComfyUI_INSTARAW/nodes/interactive_nodes/image_filter_messaging.py
    ~ ComfyUI_INSTARAW/nodes/utility_nodes/list_utility_nodes.py
    ~ ComfyUI_INSTARAW/nodes/utility_nodes/mask_utility_nodes.py
    ~ ComfyUI_INSTARAW/nodes/utility_nodes/string_utility_nodes.py
    ~ INSTALL MODELS.txt
    ~ OFMTech_NSFW.json
    ~ aiofm_setup.sh
```

**No further additions and no further removals.** The six additions are exactly
WS3's licence files, the same six as the previous cut; the removal list is empty
on both baselines. Nothing has been dropped from the pack at any point.

Reconciled against the builder's own independent entry count, which is what
caught a miscount on the previous run:

```
  previously published : 164 files
  additions            : 6
  removals             : 0
  164 + 6 - 0          = 170
  new archive          : 170 files
```

The archive is 48,654 bytes *smaller* than the published one despite gaining six
files — that is the reproducible-build normalisation (sorted entries, fixed
mtimes, zeroed owner/group) compressing better.

---

## 5. The live gist bootstrap, piped into an empty ComfyUI

Harness: the committed `tools/verify_buyer_path.sh`. It pipes the bootstrap
**fetched from `api.github.com`** — authoritative and immediate, where the raw
URL is a CDN cache that lags edits.

### What is live in the gist right now

```
  gist            : 70256ac1ebf2760e10f78804862db528  (public=False, owner=msit270)
  updated_at      : 2026-08-05T20:40:36Z
  files in gist   : aiofm_setupnsfw.sh, aiofm_setupvideo.sh
  aiofm_setupnsfw.sh : 5114 bytes (5104 characters), 116 lines, truncated=False
  sha256 (api)    : bf80cb656be8d69c62150f9ceed42dbd8f6b228411b19e790795a7d25f45589a
  sha256 (raw CDN): bf80cb656be8d69c62150f9ceed42dbd8f6b228411b19e790795a7d25f45589a
  raw CDN matches the API right now
  aiofm_setupall.sh (named by aiofm_setup.sh SETUP_URL): HTTP 404
```

Unchanged from WS5's run. The 5,114-vs-5,104 gap is multi-byte characters —
`len()` on the API string is a **character** count; the harness prints
`len(c.encode())` beside it so the two can never be confused.

The owner has **not** pasted WS5's comment-only replacement — live is 116 lines
/ `bf80cb65…`, the committed `gist/aiofm_setupnsfw.sh` is 118 lines /
`a7c7186c…`. Nothing breaks either way; `PACK_PATH` and `PACK_TOP` are unchanged
between them, which is why the rename was done on the archive's directory rather
than its filename.

The `aiofm_setupall.sh` 404 is a fact about the *gist*, not a live defect: the
shipped installer no longer names it. Confirmed out of the artifact itself:

```
$ tar -xzOf dist/AIOFMTech-NSFW.tar.gz AIOFMTech-NSFW/aiofm_setup.sh | grep -n SETUP_URL=
46:SETUP_URL="${SETUP_URL:-https://gist.githubusercontent.com/msit270/70256ac1ebf2760e10f78804862db528/raw/aiofm_setupnsfw.sh}"
```

### How the shared ComfyUI was protected

`aiofm_setup.sh`'s restart stage runs `supervisorctl restart <comfy program>`
and finds the program **by name**, so choosing my own port would still have
restarted the shared instance. The harness forces `COMFYUI_PORT=39997`, checked
dead first, so `comfy_up()` is false and the installer takes its "not running"
branch. Node registration is then verified against the harness's own instance —
a stricter check, because that instance's `custom_nodes` started at 0 entries.

I issued no `POST` to the live instance at any point. The only requests to
`18188` were read-only `GET /queue`.

### The three cases, against THESE bytes

`pack sha256: 27fa2e1c…d3d37` appears in the happy-path log, so this is
provably about the artifact in §2 and is not carried over.

| case | observed | exit |
|---|---|---|
| **no token** | red banner naming the file to create and the command to re-run; nothing written to disk first | **1** |
| **rejected token** | `curl: (22) … 401`, then `✗ could not download dist/AIOFMTech-NSFW.tar.gz`, naming repo and URL | **1** |
| **bad archive** (HTTP 200, not a gzip) | `✗ the downloaded file is not a valid archive.` + the usual cause; nothing unpacked | **1** |
| **happy path** | below | **0** |

Verbatim, no-token:

```
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

Bad archive:

```
  using HF_TOKEN from the environment
  downloading the pack from msit270/AIOFM-Pack …
100   115  100   115    0     0  64425      0 --:--:-- --:--:-- --:--:--  112k

✗ the downloaded file is not a valid archive.
  Usually this means the token was rejected and an error page was saved instead.

  --> exit code 1
```

Rejected-token still prints curl's progress meter and `curl: (22)` above the
friendly message. A buyer sees noise, then a correct explanation. Same wart WS5
recorded; still not worth a change on the critical path.

### Happy path, into a genuinely empty ComfyUI

`custom_nodes entries: 0 (0 = empty, as intended)` at the start.

```
  pack sha256: 27fa2e1c5496c4d0efee7d5b626e7638b197e1327500f86936a2a9e918dd3d37
  downloaded 7.8M
  unpacked to /workspace/ws5-verify/dest-happy/AIOFMTech-NSFW
  ✓ ComfyUI core 0.15.1 @ 3dd10a59 (validated)
  ✓ comfyui-frontend-package already 1.39.19
  ✓ ComfyUI_INSTARAW vendored @ 12afb909 (provenance marker)
  ✓ OFMTech_NSFW.json installed
  ✓ all sized files match the manifest
  ✓ all 40 node types found on disk (static check of the installed packs)
[14/14] ComfyUI restart
      ComfyUI expected on port 39997
      ✓ ComfyUI is not running — the new nodes will register when you start it

  profile        : all
  time           : 1m 24s
  downloaded     : nothing — everything was already on disk
  models total   : 178.8 GB in 87 files
  free space     : 221G
  integrity      : OK
  node versions  : pinned
  frontend       : pinned 1.39.19

  --> exit code 0 after 85s
  shared venv unchanged (pip freeze identical before/after)
```

All 18 node packs cloned at their pinned commits. Then node registration on a
fresh `--cpu` instance started from that target:

```
  workflow installed: /workspace/comfy-ws5-verify/user/default/workflows/OFMTech_NSFW.json
  up after 10s
  node types the workflow references : 51
  node types registered by ComfyUI    : 1935
  ✓ all 51 registered
  live models tree untouched (inode/size/mtime identical for every file)
```

### Blast radius, measured

```
### supervisord BEFORE:  comfyui  RUNNING  pid 8567, uptime 3:52:54
### supervisord AFTER :  comfyui  RUNNING  pid 8567, uptime 3:55:32
$ ps -p 8584 -o pid,etime --no-headers
   8584    03:55:31
### df BEFORE: overlay 410G 190G 221G 47% /
### df AFTER : overlay 410G 190G 221G 47% /
  39997 / 28188 / 38080 all free again
```

Same pid, uptime continuous across the whole run — the live instance was never
restarted. Disk 47 % throughout, never near the 85 % ceiling; peak observed
during the run was 47 %. The live queue was `running 1 / pending 33` before and
`running 1 / pending 31` after — two of the other workstreams' jobs completed
normally. **Nothing was interrupted and nothing was cleared.**

### One log line I checked rather than glossed

`[6/14]` printed two lines that contradict each other:

```
      179.5 GB total, 724 MB still to download
      ✓ already up to date — nothing to download
```

I reconciled the Hub's own file list against the installed tree rather than
guessing which line was right:

```
  Hub repo models/ files : 74
  Hub repo models/ bytes : 192707596145
  present locally        : 74
  MISSING locally        : 0  (0 bytes)
  size-mismatched        : 0
```

**All 74 repo files present at byte-exact size.** The `724 MB` is an artifact of
the estimate line's arithmetic, not a real gap — it is roughly the difference
between the `179.5 GB` it quotes and the `178.8 GB` the summary reports, which
is the same shape as the multiple-denominators problem WS5 §8b documented. I did
**not** establish the cause; that is inference and it is not a packaging defect.
It is logged in `notes/P4-questions.md`.

---

## 6. Upload command — for the OWNER to run. I did not upload anything.

I asked no one for credentials and pushed nothing to HuggingFace. This
overwrites the object buyers fetch, so run it only when the artifact in §2 is
the one you want live.

```bash
HF_TOKEN="$(tr -d '[:space:]' < /workspace/.hf_token)" \
/venv/main/bin/hf upload msit270/AIOFM-Pack \
    /workspace/nsfw-fix/dist/AIOFMTech-NSFW.tar.gz \
    dist/AIOFMTech-NSFW.tar.gz \
    --commit-message "NSFW pack re-cut against the D1-reverted graph (workflow f1ac7e55)"
```

Positional arguments are repo, local path, path-in-repo, in that order. `dist/`
is deliberate: it keeps the artifact out of the bulk
`hf download --include "models/*"`, which would otherwise sweep it and then
size-verify it against a manifest that does not list it.

### Verify from the buyer's side — the only side that counts

```bash
curl -fsSL -H "Authorization: Bearer $(tr -d '[:space:]' < /workspace/.hf_token)" \
  "https://huggingface.co/msit270/AIOFM-Pack/resolve/main/dist/AIOFMTech-NSFW.tar.gz" \
  | sha256sum
```

It must print:

```
27fa2e1c5496c4d0efee7d5b626e7638b197e1327500f86936a2a9e918dd3d37
```

**If it prints `3f6d0f2ffd092cf9a1691684029030e37283dd484cd550573290677400aada76`,
that is the OLD artifact and the upload did not land. Retry the upload — do not
wait for CDN lag.** That URL resolves through a `302` to a CAS object keyed by
content, so the old hash means the old bytes are still what the repo points at,
not that a cache is stale. `15706aa7…` should never appear: WS5's cut was never
published (§1b).

A cheaper check that needs no download, since HF returns the sha256 as the
linked etag:

```bash
curl -sS -I -H "Authorization: Bearer $(tr -d '[:space:]' < /workspace/.hf_token)" \
  "https://huggingface.co/msit270/AIOFM-Pack/resolve/main/dist/AIOFMTech-NSFW.tar.gz" \
  | grep -i 'x-linked-etag\|x-linked-size'
# expect: x-linked-etag: "27fa2e1c…d3d37"    x-linked-size: 8154217
```

And to confirm the shipped graph is the reverted one, without unpacking:

```bash
tar -xzOf /workspace/nsfw-fix/dist/AIOFMTech-NSFW.tar.gz \
    AIOFMTech-NSFW/OFMTech_NSFW.json | sha256sum
# f1ac7e55d375380033f6b0acc67ee0f4706dd618303075f86213fc09e6beb22e
```

---

## 7. ⚠️ A GREEN CUT IS NOT A CLEAN LICENCE POSITION

**This artifact CONTAINS both non-commercial code trees. Nothing was deleted,
and nothing should be deleted with `rm`.** Confirmed present in *these* bytes,
by grepping a listing taken once into a file:

```
  PRESENT: AIOFMTech-NSFW/ComfyUI_INSTARAW/modules/detection_bypass/utils/adaptive_filter.py
  PRESENT: AIOFMTech-NSFW/ComfyUI_INSTARAW/modules/detection_bypass/utils/unmarker_losses.py
  PRESENT: AIOFMTech-NSFW/ComfyUI_INSTARAW/modules/detection_bypass/utils/unmarker_full.py
  PRESENT: AIOFMTech-NSFW/ComfyUI_INSTARAW/modules/neural_grain/net.py
  PRESENT: AIOFMTech-NSFW/ComfyUI_INSTARAW/pretrained/neural_grain/grainnet.pt
  PRESENT: AIOFMTech-NSFW/ComfyUI_INSTARAW/nodes/utility_nodes/neural_grain_node.py
```

- **UnMarker** — `github.com/andrekassis/ai-watermark`, non-commercial /
  research-or-evaluation only: the first three paths.
- **GrainNet** — `github.com/Gwilherm-LESNE/Neural_Film_Grain_Rendering`,
  academic research use only: the last three.

`QUESTIONS.md` §0 (B3, B4) is the standing record and this run changes none of
it. Removing them is a **code change, not a deletion**: WS5 measured a naive
delete taking INSTARAW from **95 registered node types to 0**, because every
import in the chain is unconditional and top-level, and that takes down
`#483 INSTARAW_RealityPromptGenerator` which supplies the prompt, negative and
seed for the whole pipeline. Four modules (`pipeline.py`, `pipeline_v2.py`,
`processor.py`, `non_semantic_attack.py`) reference the UnMarker path and have
never been traced to a conclusion. It is the owner's decision, and nothing
reaches a buyer until the §6 upload is run, so it stays fully reversible.

**One correction to WS5 §4c on the cost of removal.** It expected the archive to
shrink by "roughly the compressed size of `grainnet.pt` plus a few tens of KB",
calling `grainnet.pt` "the only large one". Measured from the archive's own
listing:

```
   10771  …/modules/detection_bypass/utils/adaptive_filter.py
   14808  …/modules/detection_bypass/utils/unmarker_full.py
   16413  …/modules/detection_bypass/utils/unmarker_losses.py
    6380  …/modules/neural_grain/net.py
    4660  …/nodes/utility_nodes/neural_grain_node.py
   45929  …/pretrained/neural_grain/grainnet.pt
```

`grainnet.pt` is **45,929 bytes**, and the whole encumbered set is ~99 KB
uncompressed. **Size is not an argument in either direction here** — the entire
question is the code change and the sha256 churn, not bytes on the wire.

Also unresolved and independent of this cut: DMD2 (`cc-by-nc-4.0`) and the SD
1.5 checkpoint are still in the HF repo and ship on the default profile
(`QUESTIONS.md` §0 B2). Nothing in this re-cut touches that — it is a repo
deletion plus a matching edit to the **video** pack's `aiofm_setup.sh:810`, and
both must happen together.

---

## 8. Files I own on this run

- `dist/AIOFMTech-NSFW.tar.gz` (commit `859f829`)
- `notes/P4-package.md`, `notes/P4-questions.md`

I did not touch `OFMTech-NSFW/OFMTech_NSFW.json`, anything under
`OFMTech-NSFW/`, or any other workstream's files. `git status --porcelain
OFMTech-NSFW/` was empty before the build and after it.
