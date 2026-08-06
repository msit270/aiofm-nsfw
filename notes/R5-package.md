# R5 — distribution re-cut, against the three-graph-change tree

Everything below is quoted command output or a file/line reference. Where I am
inferring, it says so. Nothing is reported as verified on the strength of having
read a script.

This is the third run of a known procedure. Read `notes/WS5-report.md` for *why*
the tooling looks the way it does, and `notes/P4-package.md` for the previous
run. **This file's numbers supersede both.**

---

## READ FIRST

**The cut:**

```
size   : 8155368 bytes
sha256 : 5f2a0f2bed3805e87aeb77d513118f6316af221dafb7da809967e146c36c5ab1
workflow member : a811b5d690ccc5207bc7bd1c626cdd3db3b720b9be60d0a687436efcfd2143d8
```

Committed as `a288295`. **Not uploaded** — §7 is the command for the owner.

**Exercised over the wire, for real, against these bytes:** the gist fetch
(`api.github.com`, plus the raw CDN for comparison); the pack download with an
`Authorization: Bearer` header in three states (rejected token → 401,
non-archive body at HTTP 200, successful transfer); `git clone` of all node
packs to their pinned commits; `rife49.pth` fetched over HTTP during `[9/14]`;
a live `HEAD` against the HF repo.

**NOT exercised:** a cold 178 GB model pull (models were already on this pod and
were hardlinked in, so the bulk `hf download` ran as a verification pass — same
limitation WS5 and P4 recorded, not re-verified by me); pip dependency
resolution (already satisfied in the shared `/venv/main`, every install a no-op,
`pip freeze` identical before and after); **HF delivery of this artifact**, for
which I have no mandate and asked for no credentials.

**No render was performed and no image was judged.** Nothing here is a statement
about output quality.

---

## 1. Two corrections to the brief, both from my own measurement

### 1a. `27fa2e1c…` is NOT the published artifact — nothing since `3f6d0f2f…` has ever shipped

My brief describes `27fa2e1c…dd3d37` as the "currently published" artifact. It
is not published. I checked what HF serves **now** rather than inheriting a hash
from anyone's notes:

```
$ curl -sS -I -H "Authorization: Bearer …" \
    https://huggingface.co/msit270/AIOFM-Pack/resolve/main/dist/AIOFMTech-NSFW.tar.gz
HTTP/2 302
x-linked-size: 8202871
x-linked-etag: "3f6d0f2ffd092cf9a1691684029030e37283dd484cd550573290677400aada76"
```

**Live HF is `3f6d0f2f…aada76`, 8202871 bytes — three cuts behind now.** WS5's
`15706aa7…`, P4's `27fa2e1c…` and this one have all never been uploaded.

Consequences, and they matter:

- The **"upload did not land" hash a buyer or the owner should watch for is
  `3f6d0f2f…aada76`**, not `27fa2e1c…` and not `15706aa7…`. Those two cannot
  appear at that URL and telling someone to watch for them would misread a
  successful upload as a failure — the exact trap my brief flagged, now
  confirmed for a second consecutive cut.
- R2's earlier buyer-path pass was against the **committed dist artifact**, not
  against anything a buyer can currently fetch. That is not a criticism of R2 —
  it said plainly its pass did not cover the final bytes — but "published"
  should not be used for `27fa2e1c…` in the handoff.
- The published archive is still the one whose top-level directory is
  `OFMTech-NSFW/`, i.e. the name mismatch WS5 fixed is **still live for
  buyers**. It is fixed only in artifacts nobody has uploaded.

### 1b. The pack source did not move, but HEAD did — provenance stated exactly

`git status --porcelain OFMTech-NSFW/` was **empty** at the start of my session
and re-checked **empty immediately before the build**, which is the check that
counts. HEAD, however, moved from `d384eff` to `735f13c` while I was doing prep:

```
$ git log --oneline d384eff..735f13c
735f13c R1: two thirds of the freckle pigment is gone before #114 is reached
$ git log --oneline d384eff..735f13c -- OFMTech-NSFW/
(empty)
$ git diff --name-only d384eff..735f13c
notes/R1-denoise.md
```

**Notes only. The pack source did not move.** Built at HEAD `735f13c` against
workflow `a811b5d6…`, exactly the hash in my brief.

Main confirmed before I cut that R1 ships no graph change and that R4 had said
"no workflow change from me so far, and none expected". If R4 lands one later,
this artifact is stale and needs a re-cut — a 30-second rebuild.

---

## 2. The cut

Built with the committed `tools/build_pack.sh`. No hand-rolled tar.

```
$ bash tools/build_pack.sh

  archive        : /workspace/nsfw-fix/dist/AIOFMTech-NSFW.tar.gz
  top-level      : AIOFMTech-NSFW/   (matches archive name)
  entries        : 170 files
  size           : 8155368 bytes
  sha256         : 5f2a0f2bed3805e87aeb77d513118f6316af221dafb7da809967e146c36c5ab1

  shipped members (hashed out of the archive):
    OFMTech_NSFW.json  296341 bytes
      sha256       : a811b5d690ccc5207bc7bd1c626cdd3db3b720b9be60d0a687436efcfd2143d8
    aiofm_setup.sh
      sha256       : 19667d8e96a737bc605b76fbed638ab1d8ccf2c83d374f91e3cb0b8f5c43cd46
```

Re-measured independently rather than trusting the builder's own print:

```
$ stat -c 'size: %s bytes' dist/AIOFMTech-NSFW.tar.gz
size: 8155368 bytes
$ sha256sum dist/AIOFMTech-NSFW.tar.gz
5f2a0f2bed3805e87aeb77d513118f6316af221dafb7da809967e146c36c5ab1
```

Reproducible, three builds from the same tree:

```
dist=5f2a0f2bed3805e87aeb77d513118f6316af221dafb7da809967e146c36c5ab1
run1=5f2a0f2bed3805e87aeb77d513118f6316af221dafb7da809967e146c36c5ab1
run2=5f2a0f2bed3805e87aeb77d513118f6316af221dafb7da809967e146c36c5ab1
REPRODUCIBLE (3/3 identical)
```

### The one number that matters: the workflow, read back out of the archive

```
$ tar -xzOf dist/AIOFMTech-NSFW.tar.gz AIOFMTech-NSFW/OFMTech_NSFW.json | sha256sum
a811b5d690ccc5207bc7bd1c626cdd3db3b720b9be60d0a687436efcfd2143d8
```

That is the required `a811b5d6…` off the finished artifact, not off the source
tree. **The tree did not move**, so no exception applies. Same digest at every
point it can be observed — point 4 is where a buyer's ComfyUI actually reads it
from, in the install performed in §6, not a copy I made:

```
  1. source tree                              : a811b5d6…2143d8
  2. member of dist/AIOFMTech-NSFW.tar.gz     : a811b5d6…2143d8
  3. unpacked pack dir the installer ran from : a811b5d6…2143d8
  4. user/default/workflows/OFMTech_NSFW.json : a811b5d6…2143d8
```

Archive-member hashing is the right instrument here. **The project's ban is on
hashing rendered output**, and none of this is that.

### The three graph changes are in the shipped bytes, not just in git

Parsed out of the **archived** copy, not the source tree:

```
  #114 FaceDetailer widgets_values =
    [1024, True, 1024, 1111111, 'fixed', 8, 1, 'euler_ancestral', 'kl_optimal',
     0.8, 18, True, True, 0.5, 10, 1.5, 'center-1', 0, 0.93, 0, 0.7, 'False',
     10, '', 1, False, 20, False, False]
                       ↑ index 5 = steps = 8        ↑ index 15 = bbox_crop_factor = 1.5
  #105 CLIPTextEncode widgets_values = ['']
  #652 MarkdownNote in subgraph: 5. Face & Mouth Detail (Z-Image)
```

`2e4e8e9` (steps 30 → 8), `74c0f11` (bbox_crop_factor 3 → 1.5), `a806ce3`
(`#105` emptied, `MarkdownNote #652` added inside sg 5) — **all three present in
the artifact.**

---

## 3. Archive name vs internal directory — the assertion, observed firing

**Observed executing**, not assumed. The committed script under `bash -x`, with
the values expanded (`--check`, so `dist/` was not touched):

```
85:++ awk -F/ '{print $1}' /tmp/aiofm-pack.gs4kNm/.listing
87:+ TOPS=AIOFMTech-NSFW
88:+ [[ AIOFMTech-NSFW == \A\I\O\F\M\T\e\c\h\-\N\S\F\W ]]
89:++ sed -n '1{s|/.*||;p;}' /tmp/aiofm-pack.gs4kNm/.listing
90:+ PACK_TOP=AIOFMTech-NSFW
91:+ [[ AIOFMTech-NSFW == \A\I\O\F\M\T\e\c\h\-\N\S\F\W ]]
93:+ grep -qxF AIOFMTech-NSFW/aiofm_setup.sh /tmp/aiofm-pack.gs4kNm/.listing
95:+ grep -qxF AIOFMTech-NSFW/OFMTech_NSFW.json /tmp/aiofm-pack.gs4kNm/.listing
97:+ grep -qxF 'AIOFMTech-NSFW/INSTALL MODELS.txt' /tmp/aiofm-pack.gs4kNm/.listing
```

Both comparisons ran on real derived values and all three required members were
checked. Lines 93-97 grep a **file** — never `tar -tzf … | grep -q …`, which
exits 141 under `pipefail` when the pattern matches early, failing loudest
exactly when the file *is* present. The builder takes the listing into a file
once (`build_pack.sh:107-108`), and so do I everywhere in this run.

**The expression is the buyer's, verbatim.** Line 99 of the bootstrap I fetched
from the GitHub API in §5:

```
24:PACK_PATH="dist/AIOFMTech-NSFW.tar.gz"      # path INSIDE the HF repo
99:PACK_TOP="$(tar -tzf "${TMP}/pack.tar.gz" | sed -n '1{s|/.*||;p;}')"
```

Same `sed -n '1{s|/.*||;p;}'` as `build_pack.sh:117`. So the archive is checked
the way the installer reads it, not an approximation of it.

**Negative control — the assertion is not a tautology.** A check on a value
derived from the thing it is checking is worth little unless it can fail. I ran
the identical expression, under the identical filename, on the archive that is
**live on HF**:

```
=== bootstrap's OWN sed expression applied to the NEW archive ===
  archive basename : AIOFMTech-NSFW.tar.gz
  expected TOP     : AIOFMTech-NSFW
  PACK_TOP read    : AIOFMTech-NSFW
  distinct top-level dirs: AIOFMTech-NSFW
  -> assertion PASSES (exit 0)
  exit=0

=== NEGATIVE CONTROL: same expression, same filename, on the archive LIVE ON HF ===
  archive basename : AIOFMTech-NSFW.tar.gz
  expected TOP     : AIOFMTech-NSFW
  PACK_TOP read    : OFMTech-NSFW
  distinct top-level dirs: OFMTech-NSFW
  -> assertion FAILS: '✗ bootstrap PACK_TOP would read 'OFMTech-NSFW',
                        expected 'AIOFMTech-NSFW'' (exit 1)
  exit=1
```

**exit 0 on the new archive, exit 1 on the live one.** The expression
discriminates. The live artifact is exactly the case the assertion exists to
catch, and it is caught.

---

## 4. Full file-list delta

Both baselines recovered from git, so this is redoable without my scratch space:

```bash
git show 859f829:dist/AIOFMTech-NSFW.tar.gz > prevcut.tar.gz    # 27fa2e1c…dd3d37
git show 8e7b1c3:dist/AIOFMTech-NSFW.tar.gz > published.tar.gz  # 3f6d0f2f…aada76
bash tools/compare_pack.sh prevcut.tar.gz   dist/AIOFMTech-NSFW.tar.gz
bash tools/compare_pack.sh published.tar.gz dist/AIOFMTech-NSFW.tar.gz
```

Both digests verified by running exactly that.

### 4a. vs the previous cut `27fa2e1c…` — the delta my brief asked for

```
  old : top-level AIOFMTech-NSFW/   8154217 bytes   sha256 27fa2e1c…dd3d37
  new : top-level AIOFMTech-NSFW/   8155368 bytes   sha256 5f2a0f2b…c5ab1

  files: 170 old -> 170 new

  ADDED: none

  REMOVED: none

  CHANGED (1):
    ~ OFMTech_NSFW.json
```

**Zero additions, zero removals, one changed member — exactly as expected, so
there is nothing to stop and escalate.** It reconciles against git
independently:

```
$ git log --oneline 859f829..HEAD -- OFMTech-NSFW/
74c0f11 #114 FaceDetailer: bbox_crop_factor 3 -> 1.5
a806ce3 #105: empty the dead negative, and put the reason on canvas where the buyer is
2e4e8e9 #114 FaceDetailer: steps 30 -> 8
$ git diff --name-only 859f829..HEAD -- OFMTech-NSFW/
OFMTech-NSFW/OFMTech_NSFW.json
```

The +1151-byte archive growth is the compressed cost of the workflow going
294,296 → 296,341 bytes uncompressed (the MarkdownNote's text).

**One thing this delta caught that is worth recording.** Eight `.pyc` files have
appeared in the pack source since P4's cut, which WS5 had found clean:

```
$ find OFMTech-NSFW -name '*.pyc' | wc -l
8
$ find OFMTech-NSFW -name '__pycache__' | wc -l
3
```

They are under `ComfyUI_INSTARAW/{modules/detection_bypass/filmgrainer_local,
nodes/interactive_nodes,nodes/utility_nodes}/__pycache__/` — presumably left by
another agent importing INSTARAW (**inference**; I did not establish who). The
builder's `EXCLUDES` caught all of them and none reached the archive:

```
=== no junk leaked into the archive ===
  __pycache__ : 0
  \.pyc$ : 0
  \.ipynb_checkpoints : 0
  \.DS_Store : 0
  \.orig$ : 0
  \.log$ : 0
```

Source tree has 178 files; 178 − 8 = 170, matching the archive's entry count.
**This is the first cut where the junk exclusion did real work rather than being
insurance.** Had the pack been hand-rolled with `tar czf`, eight `.pyc` files
compiled for the *build pod's* Python 3.12 would have shipped to buyers.

### 4b. vs the archive live on HF `3f6d0f2f…` — what a buyer actually receives

```
  old : top-level OFMTech-NSFW/     8202871 bytes   sha256 3f6d0f2f…aada76
  new : top-level AIOFMTech-NSFW/   8155368 bytes   sha256 5f2a0f2b…c5ab1

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
    ~ ComfyUI_INSTARAW/js/{filter.css,floating_window.css,floating_window.js,
        image_filter.js,log.js,mask_utils.js,popup.js,
        reality_prompt_generator.js,utils.js,zoomed.css}
    ~ ComfyUI_INSTARAW/modules/detection_bypass/filmgrainer_local/
        {filmgrainer.py,graingamma.py,graingen.py}
    ~ ComfyUI_INSTARAW/nodes/interactive_nodes/{image_filter.py,
        image_filter_messaging.py}
    ~ ComfyUI_INSTARAW/nodes/utility_nodes/{list_utility_nodes.py,
        mask_utility_nodes.py,string_utility_nodes.py}
    ~ INSTALL MODELS.txt
    ~ OFMTech_NSFW.json
    ~ aiofm_setup.sh
```

*(The CHANGED list is brace-collapsed for width; it is 21 individual entries in
the tool's output, identical to the list in `notes/P4-package.md:290-312`.)*

**No removals on either baseline. Nothing has ever been dropped from the pack.**
The six additions are WS3's licence files, the same six as the last two cuts.
Reconciled against the builder's own independent entry count, which is what
caught a miscount on the WS5 run:

```
  live on HF   : 164 files
  additions    : 6
  removals     : 0
  164 + 6 - 0  = 170
  new archive  : 170 files
```

The archive is 47,503 bytes *smaller* than the live one despite six more files —
reproducible-build normalisation (sorted entries, fixed mtimes, zeroed
owner/group) compressing better.

---

## 5. What is live in the gist right now

Read from `api.github.com`, which is authoritative where the raw URL is a CDN
cache that lags edits:

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

Unchanged from WS5 and P4. The 5,114-vs-5,104 gap is multi-byte characters:
`len()` on the API string is a **character** count, `len(c.encode())` is the byte
count, and the harness prints both so they can never be confused
(`verify_buyer_path.sh:75-78`).

The owner has still **not** pasted WS5's comment-only replacement — live is 116
lines / `bf80cb65…`, the committed `gist/aiofm_setupnsfw.sh` is 118 lines.
Nothing breaks either way: `PACK_PATH` and `PACK_TOP` are identical between
them, which is exactly why the rename was done on the archive's directory rather
than its filename.

---

## 6. The live gist bootstrap, piped into an empty ComfyUI

Harness: the committed `tools/verify_buyer_path.sh`, piping the bootstrap
**fetched from `api.github.com`**.

### ⚠️ First attempt was invalid — a port collision with R2. Discarded and re-run.

This is the most important operational finding of the run and it nearly produced
a false pass, so it is recorded before the results.

`verify_buyer_path.sh` hardcodes default ports `38080` (pack mirror), `28188`
(node-check ComfyUI) and `39997` (the forced-dead port). **R2 was running the
same committed harness at the same time**, having changed its work directory
(`/workspace/r2gate3-verify`) but not its ports. My `bad-archive` case returned
the wrong error:

```
CASE bad-archive
  | curl: (22) The requested URL returned error: 404
  | ✗ could not download dist/AIOFMTech-NSFW.tar.gz from msit270/AIOFM-Pack.
  |   URL: http://127.0.0.1:38080/not-an-archive.tar.gz
```

It should have been a 200 carrying a non-gzip body. Chasing the 404:

```
$ ps -p 141329 -o pid,ppid,lstart,args --no-headers
 141329  141320 Thu Aug  6 13:48:22 2026  python3 -m http.server 38080 --bind 127.0.0.1
$ ls -l /proc/141329/cwd
/proc/141329/cwd -> /workspace/r2gate3-verify/mirror
$ ps -p 141320 -o args --no-headers
bash tools/verify_buyer_path.sh happy
```

**R2's mirror, serving R2's directory, mid-run.** `mirror_start`'s readiness
probe is `curl http://127.0.0.1:$MIRROR_PORT/` — it cannot tell *whose* server
answered, so it returned success against R2's and my bootstrap then fetched from
R2's directory, which has no `not-an-archive.tar.gz`.

**The `28188` case would have been far worse.** `c_nodes` starts a ComfyUI on
that port and then queries `http://127.0.0.1:28188/object_info`. Under a
collision the second agent's bind fails and its query **succeeds against the
other agent's instance** — reporting "all 51 node types registered" having
interrogated a ComfyUI it did not install. That is a silent false pass of
precisely the kind this project keeps being bitten by. This is **inference**
about what would have happened; the mirror collision is observed fact.

**Everything in that first batch was discarded.** Re-ran on private ports
(`38081` / `28189` / `39996`) and a private work dir (`/workspace/r5-verify`,
`/workspace/comfy-r5-verify`), each confirmed free first. All results below are
from the clean re-run, and each is now backed by my own mirror's access log so
"whose server answered" is no longer a matter of trust:

```
  mirror.log (208 bytes)
    Serving HTTP on 127.0.0.1 port 38081 (http://127.0.0.1:38081/) ...
    127.0.0.1 - - [06/Aug/2026 13:51:45] "GET / HTTP/1.1" 200 -
    127.0.0.1 - - [06/Aug/2026 13:51:45] "GET /not-an-archive.tar.gz HTTP/1.1" 200 -
```

**Did I damage R2's run?** Both processes are gone and I cannot tell from here.
`mirror_stop` kills `$MIRROR_PID`, which is my own subshell's pid, so it should
have been a no-op on a pid that had already exited — but I will not assert that.
I told main immediately so R2 could re-check its own run independently rather
than inherit my guess. **Anyone reading R2's result should confirm its
happy-path log shows a complete transfer and `exit code 0`.** Recorded as a
defect in `notes/R5-questions.md` with a proposed fix.

### How the shared ComfyUI was protected

`aiofm_setup.sh`'s restart stage finds the ComfyUI program **by supervisord
program name**, so choosing my own port would still have restarted the shared
instance. The harness forces `COMFYUI_PORT` to a dead port — 39996 here,
confirmed dead first — so `comfy_up()` is false and the installer takes its "not
running" branch. Proven from the log rather than assumed:

```
[14/14] ComfyUI restart
      ComfyUI expected on port 39996
      ✓ ComfyUI is not running — the new nodes will register when you start it

$ grep -c 'supervisorctl' happy.out
0
```

I issued no `POST` to the live instance at any point. The only requests to
`18188` were read-only `GET /queue`. I never touched `/api/interrupt` or
`/api/queue`.

### The three cases, against THESE bytes

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

Bad archive — note the `100 115 100 115`, a completed 115-byte transfer at HTTP
200, which is the case the `tar -tzf` guard exists for:

```
  using HF_TOKEN from the environment
  downloading the pack from msit270/AIOFM-Pack …
100   115  100   115    0     0  60052      0 --:--:-- --:--:-- --:--:--  112k

✗ the downloaded file is not a valid archive.
  Usually this means the token was rejected and an error page was saved instead.

  --> exit code 1
```

Rejected-token still prints curl's progress meter and `curl: (22)` above the
friendly message. A buyer sees noise, then a correct explanation. Same wart WS5
and P4 recorded; still not worth a change on the critical path.

### Happy path — and how I know it was these bytes

`custom_nodes entries: 0 (0 = empty, as intended)` and
`hf download metadata: 74 files` at the start — the latter confirming the
anchored `--exclude '/models/'` (an unanchored one silently turns "verify 74
files" into "re-download 178 GB", `verify_buyer_path.sh:168-170`).

**A gap in the harness I had to close.** `c_happy` prints
`note "pack sha256: …"` at line 210, which is *outside* the `tee "$WORK/happy.out"`
at line 220 — so **the pack sha256 never reaches `happy.out`**. A future session
reading that log alone cannot tell which artifact was tested. I closed it by
hashing the file my mirror actually served:

```
$ sha256sum /workspace/r5-verify/mirror/AIOFMTech-NSFW.tar.gz dist/AIOFMTech-NSFW.tar.gz
5f2a0f2bed3805e87aeb77d513118f6316af221dafb7da809967e146c36c5ab1  …/mirror/AIOFMTech-NSFW.tar.gz
5f2a0f2bed3805e87aeb77d513118f6316af221dafb7da809967e146c36c5ab1  dist/AIOFMTech-NSFW.tar.gz
  BYTE-IDENTICAL to the cut

$ grep AIOFMTech-NSFW.tar.gz /workspace/r5-verify/mirror.log
127.0.0.1 - - [06/Aug/2026 13:52:20] "GET /AIOFMTech-NSFW.tar.gz HTTP/1.1" 200 -
```

and by reconciling the transfer the bootstrap itself reported:

```
100 7964k  100 7964k    0     0   725M      0 …
  downloaded 7.8M
  → 8155368 bytes = 7964.2k = 7.78M   ✓ matches the cut exactly
```

Three independent handles on the same bytes. The install:

```
      ✓ rife49.pth fetched
      ✓ sam2.1_hiera_base_plus-fp16.safetensors present
[10/14] Workflow
      ✓ OFMTech_NSFW.json installed
[11/14] Integrity check
      ✓ all sized files match the manifest
[12/14] ViTPose GPU inference check
      providers: ['CUDAExecutionProvider', 'CPUExecutionProvider']
      OK — pose detection will run on the GPU
[13/14] Workflow node check
      ✓ all 40 node types found on disk (static check of the installed packs)
[14/14] ComfyUI restart
      ✓ ComfyUI is not running — the new nodes will register when you start it

  profile        : all
  time           : 2m 06s
  downloaded     : nothing — everything was already on disk
  models total   : 178.8 GB in 87 files
  free space     : 217G
  integrity      : OK
  comfyui core   : 0.15.1 validated
  node versions  : pinned
  frontend       : pinned 1.39.19

  --> exit code 0 after 127s
  shared venv unchanged (pip freeze identical before/after)
  unpacked to: /workspace/r5-verify/dest-happy/AIOFMTech-NSFW/
```

170 files unpacked, top-level `AIOFMTech-NSFW/`.

Then node registration on a fresh `--cpu` instance started from that target:

```
  workflow installed: /workspace/comfy-r5-verify/user/default/workflows/OFMTech_NSFW.json
  started ComfyUI from /workspace/comfy-r5-verify on port 28189 (pid 148324, --cpu)
  up after 10s
  node types the workflow references : 51
  node types registered by ComfyUI    : 1935
  ✓ all 51 registered
  live models tree untouched (inode/size/mtime identical for every file)
```

**Confirmed it was my instance, not somebody else's** — the lesson from the
collision above:

```
$ grep 'To see the GUI' comfy.log
To see the GUI go to: http://127.0.0.1:28189
$ ls /workspace/comfy-r5-verify/custom_nodes | wc -l
20
$ grep -c 'IMPORT FAILED' comfy.log
0
```

`51` is unchanged from the previous cuts even though `a806ce3` added
`MarkdownNote #652`, because the derivation skips `Note`/`MarkdownNote` — they
are frontend-only and never appear in `/object_info`. That filter is
LOAD-BEARING; without it a healthy install reports a phantom missing type. 7 of
the 51 are INSTARAW types, including `INSTARAW_RealityPromptGenerator`, so the
INSTARAW import chain is intact in the shipped pack.

**One unrelated error observed in the log**, recorded because I do not want it
mistaken for a packaging fault later:

```
[ERROR] An error occurred while retrieving information for the 'Ideogram4PromptBuilderKJ' node.
TypeError: BoundingBox.Input.__init__() got an unexpected keyword argument 'force_input'
```

`Ideogram4PromptBuilderKJ` is **not** among the 51 types this workflow
references (checked directly), so it does not affect this pack. It is a KJNodes
/ ComfyUI core API drift in a node we do not use. Logged in
`notes/R5-questions.md`.

### Blast radius, measured

```
### supervisord comfyui: pid 8567, uptime 16:15:35 → 16:19:06 → 16:22:34 → 16:26:16
### live comfy process : pid 8584, etime 16:15:34 → 16:26:15  (continuous)
### live queue          : running 1 / pending 1  →  running 1 / pending 3
### df                  : 47% → 48% (peak 48%), 216G free
### ports 38081 / 28189 / 39996 : free again, no stray processes
```

**Same pid, uptime continuous across the whole run — the live instance was never
restarted.** Disk never near the 85% ceiling. The live queue grew rather than
shrank, i.e. other agents' work was queuing normally; nothing was interrupted
and nothing was cleared.

---

## 7. ⚠️ A GREEN CUT IS NOT A CLEAN LICENCE POSITION

**This artifact CONTAINS both non-commercial code trees. Nothing was deleted,
and nothing should be deleted with `rm`.** Confirmed present in *these* bytes,
by grepping a listing taken once into a file (never `tar -tzf | grep -q`):

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

This is **a factual note for the owner, not an action.** Licensing was explicitly
out of scope for this run and I changed nothing for licence reasons.
`QUESTIONS.md` §0 is intact and untouched by me (`git diff HEAD -- QUESTIONS.md`
empty). WS5 measured that a naive delete takes INSTARAW from **95 registered
node types to 0** — every import in the chain is unconditional and top-level —
which would take down `INSTARAW_RealityPromptGenerator` and with it the prompt,
negative and seed for the whole pipeline. It is a code change, not a deletion.
Nothing reaches a buyer until §8 is run, so it stays fully reversible.

Also unresolved and independent of this cut: DMD2 (`cc-by-nc-4.0`) and the SD
1.5 checkpoint are still in the HF repo and ship on the default profile
(`QUESTIONS.md` §0 B2).

---

## 8. Upload command — for the OWNER to run. I uploaded nothing.

I asked no one for credentials and pushed nothing to HuggingFace. This
overwrites the object buyers fetch, so run it only when the artifact in §2 is
the one you want live.

```bash
HF_TOKEN="$(tr -d '[:space:]' < /workspace/.hf_token)" \
/venv/main/bin/hf upload msit270/AIOFM-Pack \
    /workspace/nsfw-fix/dist/AIOFMTech-NSFW.tar.gz \
    dist/AIOFMTech-NSFW.tar.gz \
    --commit-message "NSFW pack re-cut against the #114/#105 graph changes (workflow a811b5d6)"
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
5f2a0f2bed3805e87aeb77d513118f6316af221dafb7da809967e146c36c5ab1
```

**If it prints `3f6d0f2ffd092cf9a1691684029030e37283dd484cd550573290677400aada76`,
that is the OLD artifact and the upload did not land. Retry the upload — do not
wait for CDN lag.** That URL resolves through a `302` to a content-keyed CAS
object, so the old hash means the repo still points at the old bytes, not that a
cache is stale.

**`15706aa7…` and `27fa2e1c…` should never appear at that URL** — neither was
ever published (§1a). If you are working from `notes/WS5-report.md` or
`notes/P4-package.md`, their "watch for this" hashes are both wrong now.

A cheaper check that needs no download, since HF returns the sha256 as the
linked etag:

```bash
curl -sS -I -H "Authorization: Bearer $(tr -d '[:space:]' < /workspace/.hf_token)" \
  "https://huggingface.co/msit270/AIOFM-Pack/resolve/main/dist/AIOFMTech-NSFW.tar.gz" \
  | grep -i 'x-linked-etag\|x-linked-size'
# expect: x-linked-etag: "5f2a0f2b…c5ab1"    x-linked-size: 8155368
```

And to confirm the shipped graph carries the three changes, without unpacking:

```bash
tar -xzOf /workspace/nsfw-fix/dist/AIOFMTech-NSFW.tar.gz \
    AIOFMTech-NSFW/OFMTech_NSFW.json | sha256sum
# a811b5d690ccc5207bc7bd1c626cdd3db3b720b9be60d0a687436efcfd2143d8
```

---

## 9. Files I own on this run

- `dist/AIOFMTech-NSFW.tar.gz` (commit `a288295`)
- `notes/R5-package.md`, `notes/R5-questions.md`

I did not touch `OFMTech-NSFW/OFMTech_NSFW.json`, anything under
`OFMTech-NSFW/`, `HANDOFF.md`, `QUESTIONS.md`, or any other workstream's files.
`git status --porcelain OFMTech-NSFW/` was empty before the build and after it.
Every commit was by explicit path; I never used `git add -A`.
