# HANDOFF.md — run 4 (2026-08-07, evening)

**The licensing run. Workflow `47419606…fca30d4b` (byte-identical to run 3 —
no rendered pixel changed) · new archive `06ad99f2…134affb9` (8,094,282 B,
159 files) · NOT yet published — the pod token is read-only; the publish and
repo-deletion commands are in `OWNER-ACTIONS.md` and are the owner's first
move. Fresh-install + buyer gate PASS on the new cut with the checkpoint
fetched from Civitai for real.**

Read in this order: `LEGAL-MEMO.md` (what is proven vs. what is your
judgement), `OWNER-ACTIONS.md` (the commands only you can run),
`results/run4/MODEL-AUDIT.md` (every model file, hash-identified, flags from
APIs), `notes/R4-decisions.md` (this run's judgment calls). Acceptance
criteria this run was judged against: `results/run4/ACCEPTANCE.md`; verifier
notes beside it.

---

## What changed, and the proof for each

**1. The base checkpoint is no longer redistributed (route a — the run's
point).** `SDXLNSFW.safetensors` is LUSTIFY! GGWP (V7) — proven by SHA256
(repo LFS oid == Civitai version 2155386's published hash; the brief's
1094291 was wrong, it maps to the ENDGAME-era version). Flags read from the
API this session and stored: `allowCommercialUse ['RentCivit','Image']`
(no Sell), `allowDerivatives false`. The installer now: excludes both repo
copies from the bulk pull (`LICENCE_EXCLUDE_PATHS`), preflights Civitai
BEFORE any download (key present → version resolves → upstream hash still
identical → key unlocks the download (401/403 disambiguated) → disk
sufficient), downloads with the buyer's own key, verifies exact size then
full SHA256, places, and hardlinks the diffusion_models mirror. Every
failure is fatal and names the cause + the buyer's next step; none is a
warning. Negative-tested six ways on the shipped bytes
(`results/run4/routea/SUMMARY.md`). Commit `cbc4ac2`.

**2. Proven end-to-end on a fresh install (DoD).** `fresh_install4.sh`:
fresh tree, empty custom_nodes, SDXLNSFW/dmd2/v1-5 withheld, LIVE gist
one-liner, run-4 pack via the bootstrap's own mirror override. Install exit
0 in 170 s — the 6.94 GB came from civitai.com (~2.5 min on this pod's
link), SHA256-verified in-script, and the excluded files did not arrive
(asserted, including hardlink-inode identity for the diffusion_models
mirror). Buyer gate PASS: both LoRAs via widget menus, face prompt typed
into `#106` and read back, Run → 92-node graph accepted, selector answered
(Send disabled on open → click → enabled), render success 280 s,
`HasMetadata_00001_.png` 2688×3456 delivered, eyes stage ran
(`622:662 → True`), face YOLO 0.8652. Twelve screenshots +
api graph + result.json in `results/run4/fresh/`. Only page errors:
ComfyUI's stock first-boot userdata 404s (user.css/templates/index probes),
none from our packs. Commit `d34c481`.
Buyer journey delta: **one new step** — put a free Civitai API key in
`/workspace/.civitai_token`; skip it and the install stops in minute one
with the five-step instructions.

**3. The pack-list trim (run-3's §4-amendment debt, paid).** NODE_REPOS is
now exactly the six packs the graph resolves to (rgthree, Impact-Pack,
Impact-Subpack, controlnet_aux, essentials, UltimateSDUpscale) + vendored
INSTARAW; Swwan, pysssss and eleven other video repos gone, IPAdapter_plus
and ofmtechclip gone (zero graph nodes from either), the RIFE/SAM2
render-time stage gone with them. Both node checks rescoped: static = 27
verified (pack, literal) pairs incl. rgthree's runtime names via their
`get_name()` call sites; runtime = 27-type baseline ∪ workflow-derived
(= 54 types, re-derived independently and confirmed against the fresh
server). Fresh boot: 7 packs, 0 import failures, 0 Swwan/pysssss lines,
0 collisions — the ~40 cosmetic boot errors are gone at the source, so the
three run-3 `product-known` ignore rules are now moot in fresh installs.
Commit `b0ab0d4`. Model downloads deliberately untouched.

**4. UnMarker (B3) and GrainNet (B4) are out of the shipped INSTARAW.**
11 files deleted (both declared "Ported from ai-watermark" files +
unmarker_full + the GrainNet trio incl. `grainnet.pt` + the dead, already
un-importable UnMarker driver pipeline + — judgment call, reversible,
`notes/R4B-instaraw-removal.md` §6.1 — `non_semantic_attack.py` and its
`INSTARAW_Spectral_Normalizer` node). Root cause of the old 95→0 trap:
`utils/__init__.py:12` imported the encumbered chain unconditionally.
Result: 98→96 registered types, delta exactly the two intended nodes, all
7 workflow types present, registration surface of survivors identical to a
control (0 field diffs), ComfyUI's own loader clean both sides —
independently re-verified before commit. Also: `__pycache__` purged
(bytecode ships code; `strings` on the .pyc proved it) — build_pack already
excludes it and the published run-3 tarball was checked clean of .pyc.
Commit `9776061`.

**5. The full model audit — the pack was dirtier than QUESTIONS §0 said.**
All 43 LFS binaries identified by hash (38/42 unique contents to a named
model; obfuscated names fall away: IronSight_V7 = Wan CLIP-Vision H,
EchoVault_T9 = UMT5-XXL, High/Low = a no-Sell Civitai Wan fine-tune, etc.),
every flag from a stored API response. `results/run4/MODEL-AUDIT.md`,
commit `9c37b00`. Headlines:
- **Three NEW problems ON the NSFW render path**, unfixed (each fix
  changes output → owner's eye required): `4x-UltraSharpV2.pth`
  (cc-by-nc-sa-4.0, loaded TWICE — #612 main upscale, #100 second),
  `x1_ITF_SkinDiffDetail_Lite_v1.pth` (cc-by-nc-sa-4.0, #90), `lips_v1.pt`
  (Civitai 142240, flags no-Sell — found by downloading the publisher's
  ZIP and hashing its members; a by-hash 404 means "not published as a
  bare file", not "not on Civitai"). NC restricts USE, not just
  redistribution — a buyer-side fetch cannot cure the first two.
  Permissively-licensed replacement candidates with stored flags:
  `notes/Q1-currency.md`.
- Delete-safe encumbered dead weight staged for the owner: flux-2
  (= FLUX.2-klein-9B, non-commercial, source-gated, 18 GB), flux2-vae
  (FLUX.2-dev VAE), sam3.pt (Meta SAM License, gated=manual), High+Low
  (29 GB), Z-TurboSkinForge (grants neither commercial images nor
  redistribution), VelvetPores, DetailedNipples, HyperFleshUltrav4
  (Sell granted but credit required, not given), upscale1.pth
  (= 4x-UltraSharp v1, cc-by-nc-sa-4.0), dmd2 (cc-by-nc-4.0), v1-5.
- Video impact of every deletion checked in the published video tarball:
  the video workflow loads none of them; worst case is `warn` lines under
  PROFILE=all. Deleting breaks no video render.
- Still unidentified: `nipple.pt`, `pussyV2.pt` (dead path),
  `RealityGlass4x.pth` (unreferenced). The zip-member trick has not been
  tried on them.

**6. Docs.** INSTALL MODELS.txt rewritten for a first-time ComfyUI user
(terms defined, bootstrap primary, the two keys as one step with exact
clicks, "all 54 present" derived-not-hardcoded). Commit `9a09fcd`. The
installer header no longer describes the video product (`f7da36b`).

**7. Owner-gated state.** `OWNER-ACTIONS.md`: publish command + buyer-side
verify line for the `06ad99f2` cut; two-tier `hf repos delete-files`
commands (full paths, no wildcards); run-3 write-token revocation reminder;
video-pack re-cut noted as cosmetic. Publish, then re-run
`fresh_install4.sh` WITHOUT `MIRROR_PACK` for the fully-live proof.

**8. One post-verifier re-cut, precision note.** The gate in §2 ran on cut
`8f376926`. The verifier then caught a beginner-hostile wording in INSTALL
MODELS.txt (the healthy "verified on first start" summary form read as a
failure per the guide's own instruction), fixing it forced a re-cut, and the
final artifact is `06ad99f2`. The two archives were member-diffed out of git:
159 files each, **exactly one differing member — `INSTALL MODELS.txt`**;
workflow and installer members byte-identical. The gate's proof carries to
the final cut modulo that one text file, which no code path reads.

## Track 2 — quality menu (recommend-only, in flight at handoff time)

Four Q agents ran under `notes/Q-PROTOCOL.md` (GPU lock, fresh server per
arm on :19188, never 18188, one variable per arm). Q1 (currency) is
complete — `notes/Q1-currency.md`: six of seven pins current;
controlnet_aux's 7-commit lag is a MediaPipe rewrite PROVEN to crash under
our pin (do not bump); core v0.29 changed Z-Image RoPE numerics
(output-affecting — pin stands); detector/upscaler alternatives with
API-read licences; zero hands detected in all 14 delivered frames (the
hands pass may be idle at default framing — menu item). Q2
(bbox_crop_factor: UNTESTED→measured), Q3 (Z-Image levers), Q4 (other
settings) had completed arms + partial sheets at handoff and resume
automatically; their notes land in `notes/Q2-…/Q3-…/Q4-settings.md` and
sheets under `results/run4/quality/`. NOTHING from track 2 touched the
pack: the workflow hash is the invariant above. Mid-run lesson now in the
protocol's history: flock is not FIFO — the track-1 gate was starved until
a sentinel-yield was imposed (`notes/R4-decisions.md` #10).

## Standing facts (unchanged from run 3)

The run-3 published pack (`29175edc`) remains live until the owner
publishes. Crash guard, selector fixes, cpu CLIPLoader, mouth ceiling 4M,
eyes feather, two-LoRA design: all stand; nothing output-changing shipped
this run. `d_setup.sh`/`d_gate.sh` EXPECT hashes moved to the `06ad99f2`
cut (workflow EXPECT unchanged).

*Everything on `master`, one commit per change. The pod HF token cannot
push to HuggingFace and there is no git remote configured for this repo on
this pod beyond what `git log` shows pushed previously.*
