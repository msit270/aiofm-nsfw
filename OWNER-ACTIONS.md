# OWNER-ACTIONS — what only you can do (run 4, 2026-08-07)

Nothing in this file has been done for you. Each item says why it needs you,
what to run, and what happens if you skip it. Read `LEGAL-MEMO.md` first for
the reasoning; this is the command list.

The pod's HuggingFace token is **role: read** (checked this session via
`api/whoami-v2`), so nothing here could be executed from the session that
wrote it. Everything below needs a **write** token.

---

## 1. Publish the new pack  (required — nothing else ships without it)

```bash
HF_TOKEN="hf_your_WRITE_token" \
/venv/main/bin/hf upload msit270/AIOFM-Pack \
    /workspace/nsfw-fix/dist/AIOFMTech-NSFW.tar.gz \
    dist/AIOFMTech-NSFW.tar.gz \
    --commit-message "NSFW run-4: buyer-side Civitai checkpoint fetch, pack-list trim, UnMarker/GrainNet removed. Archive 8f376926, workflow 47419606 (unchanged)"
```

Then confirm from the buyer's side, which is the only side that counts:

```bash
curl -sS -I -H "Authorization: Bearer $HF_TOKEN" \
  "https://huggingface.co/msit270/AIOFM-Pack/resolve/main/dist/AIOFMTech-NSFW.tar.gz" \
  | grep -i 'x-linked-etag\|x-linked-size'
# expect: x-linked-etag: "8f37692638535f004c19e93454c90f395774ca4bba737f8fb9cbf0adf21c41f5"
#         x-linked-size: 8094057
```

The gist needs no edit. The workflow inside the archive is byte-identical to
run 3 (`47419606…fca30d4b`), so no render changes.

**After publishing**, re-run the fresh-install gate without the mirror to get
the fully-live proof:

```bash
rm -rf /workspace/comfy-fresh4 /workspace/fresh-pack4
bash /workspace/nsfw-fix/tools/browser_harness/fresh_install4.sh
```

---

## 2. Delete the encumbered files from the HF repo  (required to stop shipping them)

**Removing a file from the setup script does not stop it shipping.** The
install is one bulk `hf download --include "models/*"` and `fnmatch`'s `*`
matches `/`, so it sweeps the whole tree. The run-4 script now `--exclude`s
the four files below as a second layer, but **only deleting them from the
repo stops delivery** — a buyer running an older copy of the script still
gets whatever is in the repo.

Every file below is referenced by **neither** shipped workflow, and the video
impact was checked in the published video tarball, not assumed: the video
workflow loads none of them, `PROFILE=video` filters them out, and under the
default `PROFILE=all` a missing repo file hits `dl()`'s `warn` branch, not
`die`. **Deleting these breaks no video render.**

Note on the command: `hf repos delete-files` takes **fnmatch patterns**, and
its own `*` matches `/` recursively — the same mechanic that made the bulk
download sweep everything. Every path below is written in full with no
wildcard, so each pattern can only ever match the one file it names.
(`hf repo-files … delete` is the older spelling of the same thing and now
prints a deprecation warning; this is the current one.)

```bash
export HF_TOKEN="hf_your_WRITE_token"
R=msit270/AIOFM-Pack

# --- tier 1: encumbered AND now unnecessary (delete these first) ---
/venv/main/bin/hf repos delete-files $R \
  models/checkpoints/SDXLNSFW.safetensors \
  models/diffusion_models/SDXLNSFW.safetensors \
  models/loras/dmd2_sdxl_4step_lora_fp16.safetensors \
  models/checkpoints/v1-5-pruned-emaonly-fp16.safetensors \
  --commit-message "Remove encumbered weights: LUSTIFY (buyers now fetch from Civitai), DMD2 (cc-by-nc-4.0), unreferenced SD1.5"
#   SDXLNSFW ×2  LUSTIFY GGWP V7 — buyers now fetch it themselves (run-4 change)
#   dmd2         cc-by-nc-4.0; replaced by TDD (Apache-2.0) two runs ago, still shipping
#   v1-5         referenced by nothing; OpenRAIL-M flow-down for no benefit

# --- tier 2: encumbered dead weight, ~62 GB, nothing loads any of it ---
/venv/main/bin/hf repos delete-files $R \
  models/diffusion_models/flux-2.safetensors \
  models/vae/flux2-vae.safetensors \
  models/sam3/sam3.pt \
  models/diffusion_models/High.safetensors \
  models/diffusion_models/Low.safetensors \
  models/diffusion_models/Z-TurboSkinForge.safetensors \
  models/loras/VelvetPores_Flux.safetensors \
  models/loras/DetailedNipples.safetensors \
  models/diffusion_models/HyperFleshUltrav4.safetensors \
  models/upscale_models/upscale1.pth \
  --commit-message "Remove unreferenced encumbered weights (non-commercial / no-redistribution flags)"
#   flux-2             FLUX.2-klein-9B, flux-non-commercial-license, gated at source
#   flux2-vae          FLUX.2-dev VAE, same non-commercial licence
#   sam3.pt            Meta SAM License, source gated=manual, agreement must accompany
#   High / Low         no Sell, derivatives forbidden, credit required (29 GB)
#   Z-TurboSkinForge   grants neither commercial image use NOR redistribution
#   VelvetPores        no Sell, derivatives forbidden
#   DetailedNipples    no Sell (its anatomy path is dead in the graph)
#   HyperFleshUltrav4  Sell granted but credit required and not given
#   upscale1.pth       4x-UltraSharp v1, cc-by-nc-sa-4.0
```

Tier 2 is delete-safe but is **your call, not mine** — it is your model
library and you may want those files for work that is not this product. The
licensing reasoning for each is in `results/run4/MODEL-AUDIT.md` §E with the
API response cited per row.

Verify afterwards:

```bash
curl -s -H "Authorization: Bearer $HF_TOKEN" \
  "https://huggingface.co/api/models/msit270/AIOFM-Pack/tree/main?recursive=true" \
  | python3 -c "import json,sys; [print(e['path']) for e in json.load(sys.stdin) if e['path'].startswith('models/')]"
```

**Do NOT delete these three — the NSFW graph loads them:**
`models/upscale_models/4x-UltraSharpV2.pth`,
`models/upscale_models/x1_ITF_SkinDiffDetail_Lite_v1.pth`,
`models/ultralytics/lips_v1.pt`. They have their own problem; see item 3.

---

## 3. Decide on the three encumbered files that are ON the render path

**This one is a decision, not a command, and it is the biggest thing left.**
See `LEGAL-MEMO.md` §3. Summary of the choice:

| file | what its licence says | can a buyer-side fetch fix it? |
|---|---|---|
| `4x-UltraSharpV2.pth` (loaders #100, #612) | CC-BY-NC-SA-4.0 — **NonCommercial** | **No.** NC restricts the *use*, not just distribution |
| `x1_ITF_SkinDiffDetail_Lite_v1.pth` (loader #90) | CC-BY-NC-SA-4.0 — **NonCommercial** | **No**, same reason |
| `lips_v1.pt` (detector #161) | Civitai `['Image','RentCivit']`, no `Sell` | **Yes** — same shape as LUSTIFY |

Replacing the two upscalers changes every rendered pixel, so I did not touch
them: that needs your eye on an A/B, per your own standing rule. The
candidate replacements with permissive licences (CC-BY-4.0 / CC0 / BSD, each
flag read from an API this session) are listed in `notes/Q1-currency.md`
items 1 and 2, staged as pod A/B arms.

---

## 4. Revoke the run-3 write token

Still outstanding from the last run: the write token supplied in-session on
2026-08-07 ("pack-publish-aug7") passed through a conversation. Revoke it at
huggingface.co → Settings → Access Tokens if you have not already.

---

## 5. Re-cut the VIDEO pack at your convenience  (low priority, cosmetic)

The published video `aiofm_setup.sh` still `dl`s files that will no longer
exist after item 2 — `SDXLNSFW.safetensors` (lines 770, 802),
`dmd2_sdxl_4step_lora_fp16.safetensors` (line 810), and the
flux/High/Low/zimage set (lines 782-789). Under the default `PROFILE=all`
those produce `warn "failed: …"` lines in a video install and nothing else;
the video workflow loads none of them. Cleaning it up is tidiness, not a fix.

---

## 6. Nothing was sent to anyone

No email, message, DM or PR was sent or drafted for sending, per your
instruction. If you decide to approach coyotte about a LUSTIFY licence, that
conversation has not been started and no draft of it exists in this repo.
