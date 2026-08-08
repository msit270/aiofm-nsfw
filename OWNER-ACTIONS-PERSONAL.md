# OWNER-ACTIONS — personal build (run 5)

Only you can do these; the pod token is read-only. NOTHING here touches the
sellable pack, gist, or its HF paths.

## 1. Publish the personal pack — DONE (2026-08-08, v4)

PUBLISHED: `msit270/AIOFM-Personal` (private), pack at the repo ROOT —
`AIOFMTech-NSFW-Personal.tar.gz` (owner uploaded manually; NOT dist/).
Verified from the pod: anonymous download 401 (private), authed
round-trip sha256 == `a122699c…` (= pack v4), fetched with the pod's
READ token — the same token class a fresh install uses.

To re-publish a future cut to the SAME location:

    HF_WRITE_TOKEN=hf_xxx bash tools/publish_personal_pack.sh

(script targets the repo root path and refuses public repos / AIOFM-Pack;
the pod token is read-only and cannot publish.)

## 2. The one-liner (fresh pod)

Pre-reqs on the pod, same as the sellable + nothing new:
    echo "hf_..."   > /workspace/.hf_token        # HF read token
    echo "<civkey>" > /workspace/.civitai_token    # Civitai API key

Then ONE line:

    AIOFM_PACK_URL="https://huggingface.co/msit270/AIOFM-Personal/resolve/main/AIOFMTech-NSFW-Personal.tar.gz" \
    bash <(wget -qO- https://gist.githubusercontent.com/msit270/70256ac1ebf2760e10f78804862db528/raw/aiofm_setupnsfw.sh)

The live sellable gist is reused UNCHANGED — AIOFM_PACK_URL is the supported
override it already ships with. The personal tarball unpacks to its own
directory (AIOFMTech-NSFW-Personal/), installs OFMTech_NSFW_Personal.json,
fetches V9 from Civitai with your key, and installs luna/lunaskye from
inside the tarball.

## 3. Aug 10 — V10 (Krea 2)

`notes/V10-krea2-runbook.md` — the whole procedure. Requires a ComfyUI core
upgrade to >=0.26 (this build pins 0.15.1), so treat it as its own session:
upgrade, re-run the run-5 canary, then swap the base slot.
