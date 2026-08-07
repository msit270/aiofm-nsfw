# LEGAL-MEMO — the licensing position after run 4 (2026-08-07)

Written by the run-4 session. I am not a lawyer and this is not legal advice;
it is an engineering account of what is now true, with every licence fact
traced to an API response stored in this repo this session. Where something
is a judgement call, it says so and whose call it is.

---

## 1. What was done, in one paragraph

The base checkpoint (`SDXLNSFW.safetensors` = LUSTIFY! GGWP (V7), proven by
SHA256, not filename) is no longer delivered by your installer: every fresh
install now downloads it directly from Civitai under the **buyer's own free
account and API key**, verifies it byte-for-byte against the exact version
this pack was built on, and fails loudly by name if the key is missing/bad,
the version disappears, the upstream file changes, or the disk is too small.
The DMD2 LoRA (cc-by-nc-4.0) and two other files are excluded from the bulk
download the same way. The UnMarker- and GrainNet-derived code and weights
are deleted from the ComfyUI_INSTARAW pack that ships. The installer now
installs only the six node packs the NSFW graph uses. The full model
library was audited by hash against Civitai/HuggingFace/OpenModelDB APIs.
What remains for you is in `OWNER-ACTIONS.md` (publish + repo deletions) and
§3 below (three decisions).

## 2. PROVEN — things you can say with evidence in hand

Every item cites files in this repo.

1. **What the checkpoint is.** `SDXLNSFW.safetensors` (sha256 `d234c60d…`)
   is byte-identical to Civitai version 2155386 of model 573152, "LUSTIFY!
   [NSFW checkpoint] — GGWP (V7)", upstream filename
   `lustifyNSFWCheckpoint_ggwpV7.safetensors`, creator coyotte.
   (`results/run4/civitai/sdxlnsfw_by_hash.json` — the API's SHA256 equals
   the repo's LFS oid.) The brief's version id 1094291 was indeed wrong —
   that is ENDGAME (V5-era); the correct id is **2155386**.
2. **What its flags say.** From `results/run4/civitai/lustify_model_573152.json`,
   fetched this session: `allowCommercialUse: ['RentCivit','Image']`,
   `allowDerivatives: false`, `allowDifferentLicense: false`,
   `allowNoCredit: true`. In Civitai's own legend, `Image` = "sell images
   they generate"; `Sell` (sell the model) is **absent**. So: **selling
   images made with it is expressly within the granted permissions; selling
   or redistributing the model file is not.** Your buyers' use case sits in
   the granted column. (One unknown field recorded honestly: the version
   object carries `licensingFee: 1` — that field is in
   `results/run4/civitai/sdxlnsfw_by_hash.json`, the version-level response;
   Civitai does not document its semantics and I did not interpret it.)
3. **The installer no longer delivers it.** Grep-provable in the shipped
   `aiofm_setup.sh` (no repo URL for the file remains; the bulk pull
   `--exclude`s both repo paths), and proven end-to-end on a genuinely fresh
   tree this session: with the file withheld, the install fetched all
   6,938,099,634 bytes from civitai.com with the pod's key, the SHA256
   matched, and the excluded files (`dmd2`, `v1-5`) did **not** arrive
   (`results/run4/fresh/install.log`, `driver.log`).
4. **Every failure mode is loud and named.** Six negative tests, each dying
   with the cause and the buyer's next step; none demoted to a warning
   (`results/run4/routea/SUMMARY.md` + captured outputs).
5. **The buyer journey grew by exactly one step** — putting a free Civitai
   API key in a file — and the install stops in its first minute with
   instructions if the step was skipped. (INSTALL MODELS.txt teaches it;
   the preflight enforces it.)
6. **UnMarker (B3) and GrainNet (B4) no longer ship.** 11 files deleted from
   the pack source including the weights; binary-safe grep of the shipped
   tree hits only the notices file; the pack still registers 96 node types
   with the 7 the workflow needs all present, proven twice on isolated
   instances and again by the fresh install's zero-import-failure boot
   (`results/run4/instaraw/`, `notes/R4B-instaraw-removal.md`).
7. **DMD2 (B2)** is referenced by neither shipped workflow (grep of both
   JSONs), is excluded from the NSFW bulk pull, and its deletion command is
   staged. Its cc-by-nc-4.0 licence was re-verified from the HF API this
   session (`results/run4/hf/tianweiy_DMD2_meta.json`).
8. **The whole model library is identified and flagged** — 43 LFS binaries,
   38 of 42 unique contents identified cryptographically (hash match), each
   with licence/flags from a stored API response
   (`results/run4/MODEL-AUDIT.md`). The prior "audit came back clean" is
   dead: see §3.
9. **The workflow did not change.** The archive's `OFMTech_NSFW.json` hashes
   `47419606…` — identical to the published run-3 cut. No rendered pixel is
   affected by anything in this run.

## 3. NOT resolved — the decisions that are yours (or a lawyer's)

**3a. Whether route (a) is *sufficient* for LUSTIFY.** What the change
achieves mechanically: you no longer copy or transmit the model file to
anyone; each buyer obtains it from Civitai under their own account, inside
the permissions Civitai's flags grant them, and your product then uses a
file lawfully present on the buyer's machine to make images — a use the
flags expressly allow ("Image"). That is the strongest position available
without a licence from coyotte. What I cannot tell you: whether
"instructing and automating the buyer's download" fully discharges *your*
exposure in any given jurisdiction, or how Civitai's own Terms of Service
bear on scripted downloads through a user's API key (the key mechanism
exists for exactly this, but I did not and cannot read their ToS into a
legal opinion). **Route (a) is built and working; whether it is sufficient
is a judgement you need to make or take to a lawyer.** Route (c) —
a written licence from coyotte — remains the only thing that would settle
it outright, and you said you are handling that yourself.

**3b. Three encumbered files are still on the NSFW render path**, found by
this run's audit and NOT fixed, because fixing them changes rendered output
and that is your call by standing rule:

| file | licence (API-read) | why it is worse than LUSTIFY |
|---|---|---|
| `4x-UltraSharpV2.pth` (loaded twice: #612 main upscale, #100 second upscale) | CC-BY-NC-SA-4.0 (`results/run4/hf/Kim2091_UltraSharpV2_meta.json`) | **NonCommercial restricts the use itself**, not just redistribution — a buyer-side fetch does not cure it |
| `x1_ITF_SkinDiffDetail_Lite_v1.pth` (#90, hands/skin) | CC-BY-NC-SA-4.0 (OpenModelDB sha-match, re-fetched live) | same |
| `lips_v1.pt` (#161, mouth detector) | Civitai flags `['Image','RentCivit']`, **no Sell** (`results/run4/verify/civitai_model_142240.json`; zip-member hash match) | same shape as LUSTIFY — a buyer-side fetch (of the zip) or a swap would cure it |

Until these three are replaced (or, for lips_v1, buyer-side-fetched), **the
product is not clean even with LUSTIFY solved.** Permissively-licensed
replacement candidates for the two upscalers, with flags read from APIs and
staged A/B plans, are in `notes/Q1-currency.md`; the swap needs your eye on
sheets because it alters pixels.

**3c. What you can and cannot claim to buyers.** Supportable now: "the
images you generate with this product may be sold" (LUSTIFY grants `Image`;
every other NSFW-live model is Apache/WTFPL/clean **except the three in
3b**). Not supportable until 3b is resolved: any blanket "fully licensed /
fully commercial-safe" claim about the *pipeline*.

**3d. The pack still states no licence of its own (old B5).** The INSTARAW
notices file is accurate about third parties, but nothing tells a buyer
what THEY may do with your pack (resell it? share it?). Writing that EULA
is a product/legal decision, not an engineering one. Unchanged this run.

**3e. Past distribution is not undone.** Everything shipped before today —
LUSTIFY, DMD2, the NC upscalers, UnMarker/GrainNet inside INSTARAW — was
received by every earlier buyer, and run-3's pack remains live until you
publish (OWNER-ACTIONS §1). Deletion is prospective. Whether anything ought
to be done about past deliveries is a lawyer question; nothing in this repo
answers it.

**3f. One judgement call inside the INSTARAW cleanup.**
`non_semantic_attack.py` (+ its node, absent from the workflow) was removed
although its licensing was *uncleared* rather than *proven encumbered* —
its own docstring calls it "the core UnMarker-style optimization" and the
upstream comparison never covered it. Risk-removing option taken;
reverting is two files (`notes/R4B-instaraw-removal.md` §6.1). If you want
it back, the clean path is diffing it against the ai-watermark repo first.

## 4. Residual dependencies you now carry (eyes open)

- **Civitai availability.** Every fresh install now depends on
  civitai.com being up and version 2155386 staying published. The preflight
  makes failure loud and honest, and V7 sits behind V8/V9/V10 (all Public as
  of today, stored in `results/run4/civitai/lustify_model_573152.json`) — a
  creator pulling a superseded version is the realistic risk. Mitigation if
  it ever fires: re-cut the pack against a version you CAN rely on (route
  b candidates and their flags are in `notes/Q1-currency.md`), never
  "find the file elsewhere" — INSTALL MODELS.txt tells buyers the same.
- **Civitai download speed** is the slowest single file in the install
  (measured: the 6.9 GB took ~2.5 minutes on this pod's link; buyer pods
  will vary widely).
- **Buyers with the OLD pack** keep working — their SDXLNSFW is already on
  disk and the new script accepts a present-and-complete file — but anyone
  re-running the OLD script after you delete the repo files sees `dl`
  warnings, not failures (verified behavior of the old script's warn
  branch). The old pack stops being downloadable the moment you publish
  over it.
