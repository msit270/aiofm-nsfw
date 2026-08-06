# WS5 — questions

Per the brief I did not stop to ask these. Each records the option I took and
why it is the lower-risk one for a first-time buyer.

---

## Q-WS5-1 — DMD2 is still in the published repo. **Second blocker on selling,
alongside LUSTIFY.**

`models/loras/dmd2_sdxl_4step_lora_fp16.safetensors`, 393,854,592 bytes,
sha256 `b3d9173815a4b595991c3a7a0e0e63ad821080f314a0b2a3cc31ecd7fcf2cbb8`, is
present in `msit270/AIOFM-Pack` today. Its sha256 is identical to
`tianweiy/DMD2`'s copy, and that repo is **`cc-by-nc-4.0` — non-commercial**,
read from the Hub API, not from memory.

STATE.md records DMD2 as **"Replaced."** That is true of the graph and of the
fetch list, and I verified the replacement is genuine (TDD is different bytes,
matching `RED-AIGC/TDD`, `apache-2.0`). It is **not** true of what a buyer
receives.

### The mechanic that makes this non-obvious — read this before "removing" any other file

**Dropping a file from the fetch list does not stop it shipping.**

The default `PROFILE=all` path does not fetch files one by one. It is a single
bulk pull, `aiofm_setup.sh:657`:

```bash
INC=(--include "models/*")
"$HF_CMD" download "$HF_REPO_ID" "${INC[@]}" --local-dir "$COMFYUI_DIR" …
```

`huggingface_hub` matches those patterns with `fnmatch`, and **`fnmatch`'s `*`
matches `/`** — unlike a shell glob. So `models/*` is not "the files directly
under `models/`", it is **every file under `models/`, recursively, forever**. The
per-file `dl` lines further down the script are a fallback for when the bulk pull
fails; they are not the thing that decides what a buyer gets.

That is precisely why the earlier DMD2 replacement looked complete and was not.
Someone removed the `dl` line, changed the graph, and reasonably concluded the
file was gone. Nothing in the script mentions DMD2 any more — and every buyer on
the default profile still receives it, because it is still in the repo.

**The only way to stop a file shipping is to delete it from the repo.** This is
the sentence that stops the same mistake being made again with the SD 1.5
checkpoint in Q-WS5-2.

The evidence it ships: the file landed on this pod from the buyer install path at
21:25, and `hf` wrote its own download record for it at
`.cache/huggingface/download/models/loras/dmd2_sdxl_4step_lora_fp16.safetensors.metadata`,
holding that same sha256.

**My best guess:** delete it from the repo. Nothing in either product references
it, so the cost is zero and the exposure is a non-commercial licence sitting
inside a product being sold.

**But it cannot be a one-line deletion.** The *video* pack's `aiofm_setup.sh:810`
still contains `dl "$REPO/dmd2_sdxl_4step_lora_fp16.safetensors" …`. Both packs
share this repo. Delete the file without also fixing that line and every
video-pack install prints `failed: dmd2_sdxl_4step_lora_fp16.safetensors`.

**What I did:** nothing. I have no delete mandate on the repo and this is the
user's call. Reported rather than acted on. **This should be treated as blocking
sale in the same way LUSTIFY is** — LUSTIFY at least permits selling generated
images; cc-by-nc-4.0 permits no commercial use at all.

---

## Q-WS5-2 — 2.13 GB of unreferenced Stable Diffusion 1.5 also ships

`models/checkpoints/v1-5-pruned-emaonly-fp16.safetensors`, 2,132,696,762 bytes,
sha256 `e9476a13728cd75d8279f6ec8bad753a66a1957ca375a1464dc63b37db6e3916` —
identical to `Comfy-Org/stable-diffusion-v1-5-archive`, which the Hub reports as
`license=creativeml-openrail-m`.

No script and no workflow in either pack names it. It is 2.13 GB of a 178 GB
download that exists for nothing, and RAIL-M carries use restrictions that flow
down to anyone redistributing it — a smaller instance of the DMD2 problem.

**My best guess:** delete it too, in the same pass as DMD2. It is
lower-stakes — RAIL-M is not a flat commercial prohibition — so it is a
tidiness-plus-caution item rather than a blocker. **What I did:** reported only.

These two are the *complete* set of unreferenced non-placeholder files in the
repo. I checked every one of the 74 `models/` entries, not a sample.

---

## Q-WS5-3 — which name wins, `AIOFMTech-NSFW` or `OFMTech-NSFW`?

**Taken: `AIOFMTech-NSFW`**, i.e. the archive name stays and the directory
changes. Reasoning is in `WS5-report.md` §1: the sibling video pack already does
this, and — the part that actually decides it — the bootstrap hardcodes the
archive path but reads the directory out of the archive at run time. Renaming
the directory needs no gist edit and republishes over the same HF path, so there
is no window in which the user has uploaded a new pack that no buyer can reach.
Renaming the archive would create exactly that window.

Residual risk I accepted: an existing buyer ends up with both
`/workspace/OFMTech-NSFW` (stale) and `/workspace/AIOFMTech-NSFW` (current). The
lower-risk option would have been to have the bootstrap remove the old
directory, and I rejected it — deleting a directory a buyer may have put files
in is a worse failure than an unused stale copy.

---

## Q-WS5-4 — should the git source directory be renamed to match?

**Taken: no, not this session.** `OFMTech-NSFW/` in git would become
`AIOFMTech-NSFW/`, which rewrites paths WS1, WS3 and WS4 were editing while I
worked. `tools/build_pack.sh` does the rename at pack time and asserts the
result, so the shipped artifact is correct either way. Worth doing as a clean
`git mv` once the branch merges; nothing depends on it.

---

## Q-WS5-5 — `INSTALL MODELS.txt` step 1 contradicts how the pack is delivered

It warns that a one-line `bash <(wget ...)` install "will NOT get the custom
nodes or the workflow". True of piping `aiofm_setup.sh`; **false of the gist
bootstrap**, which is also a one-line `bash <(wget ...)` and which exists
specifically to fix that. A buyer handed the bootstrap one-liner and then reading
this text has been told their install is broken when it is not.

**Taken: left alone.** It is product copy, the fix is a rewrite rather than an
edit, and getting it wrong risks talking a buyer *out* of the working path. It
should be rewritten before sale.

---

## Q-WS5-6 — `ComfyUI_INSTARAW` is copied, never overwritten

`aiofm_setup.sh:1156`: if the buyer already has a copy in `custom_nodes/`, it is
left alone. Correct for protecting a buyer's edits. But it also means anyone who
installed the current pack and re-runs after this re-cut keeps the **old**
INSTARAW — including whatever WS3's licence files and WS1's fixes changed inside
it — and nothing tells them.

**Taken: left alone**, because changing it means overwriting files a buyer may
have edited, which is a worse default. But a version-aware update (compare the
`12afb909…` provenance marker, warn on mismatch) is the right answer and this
should not ship many more times without one.

---

## Q-WS5-7 — the `Workflow node check` stage checks the wrong workflow

`aiofm_setup.sh:1531-1573` is a hardcoded list of Wan/KJ/VHS node types. During
an NSFW install it printed `✓ all 40 workflow node types present` without
checking a single NSFW node type. The workflow-derived check that would catch
this (`comfy_verify_nodes`, line ~1705) only runs after a successful restart.

**Taken: reported, not fixed.** It is a real hole — a stage whose entire job is
catching missing packs, reporting green on a workflow it never looked at — but
fixing it means editing the check logic during a distribution cut, and my own
harness covers the same ground more strictly (all 51 NSFW node types against a
live `/object_info`). It belongs in the same pass as SETUP.md §6 item 8.

---

## Q-WS5-8 — should the gist be updated?

**Taken: prepared, not required.** `gist/aiofm_setupnsfw.sh` holds the exact new
content and the change is comment-only, proven by diffing with comments
stripped. Nothing breaks if the user never pastes it. Full instructions in
`WS5-report.md` §7.
