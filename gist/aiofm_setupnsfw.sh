#!/usr/bin/env bash
#
# AIOFM · OFMTech NSFW — bootstrap
#
# This is NOT the setup script. It is the ~60 lines that fetch the pack and
# then hand over to the real one.
#
#   bash <(wget -qO- https://gist.githubusercontent.com/msit270/70256ac1ebf2760e10f78804862db528/raw/aiofm_setupnsfw.sh)
#
# Why a separate bootstrap exists
# -------------------------------
# The real installer copies ComfyUI_INSTARAW and OFMTech_NSFW.json from the
# directory it lives in. Run through a pipe, BASH_SOURCE is /dev/fd/63, so
# that directory resolves to /dev/fd, both copies silently find nothing, and
# the buyer's first symptom is a graph full of red nodes with no error.
#
# So this file deliberately NEVER looks at its own location. It downloads the
# pack, unpacks it to a real directory on disk, and execs the copy inside --
# which then has genuine files beside it.
#
set -euo pipefail

REPO_ID="msit270/AIOFM-Pack"
PACK_PATH="dist/AIOFMTech-NSFW.tar.gz"      # path INSIDE the HF repo
# Overridable so the pack can be verified from a local mirror before it is
# published, without editing the file that ships.
PACK_URL="${AIOFM_PACK_URL:-https://huggingface.co/${REPO_ID}/resolve/main/${PACK_PATH}}"
DEST="${AIOFM_DEST:-/workspace}"
TOKEN_FILE="${HF_TOKEN_FILE:-/workspace/.hf_token}"

say()  { printf '  %s\n' "$1"; }
die()  { printf '\n\033[1;31m✗ %s\033[0m\n' "$1" >&2; exit 1; }

printf '\n\033[1;36m=== AIOFM · OFMTech NSFW — bootstrap ===\033[0m\n\n'

# --- 1. token ---------------------------------------------------------------
# Read it from disk rather than from an argument. An argument ends up in shell
# history and in the process list, where other users on a shared box can read
# it; a 0600 file does not.
if [[ -n "${HF_TOKEN:-}" ]]; then
    say "using HF_TOKEN from the environment"
elif [[ -f "$TOKEN_FILE" ]]; then
    HF_TOKEN="$(tr -d '[:space:]' < "$TOKEN_FILE")"
    [[ -n "$HF_TOKEN" ]] || die "$TOKEN_FILE exists but is empty."
    say "read your HuggingFace token from $TOKEN_FILE"
else
    printf '\033[1;31m'
    cat <<EOF

  ==========================================================
    No HuggingFace token found.

    The models live in a private repository, so the install
    cannot start without one. Create the file first:

      echo "hf_yourtoken" > /workspace/.hf_token

    (replace hf_yourtoken with your real token), then run
    this same command again.
  ==========================================================

EOF
    printf '\033[0m'
    exit 1
fi
export HF_TOKEN

# --- 2. somewhere to work ---------------------------------------------------
mkdir -p "$DEST" || die "cannot create $DEST"
TMP="$(mktemp -d "${DEST}/.aiofm-bootstrap.XXXXXX")" || die "cannot create a temp directory in $DEST"
trap 'rm -rf "$TMP"' EXIT

# --- 3. fetch the pack ------------------------------------------------------
say "downloading the pack from ${REPO_ID} …"
if ! curl -fL --retry 5 --retry-delay 3 --retry-connrefused \
        -H "Authorization: Bearer ${HF_TOKEN}" \
        -o "${TMP}/pack.tar.gz" "$PACK_URL"; then
    die "could not download ${PACK_PATH} from ${REPO_ID}.
  Check that your token is valid and has access to that repository.
  URL: ${PACK_URL}"
fi

# A 401/403 HTML error page can arrive with a 200 in some proxy setups, so
# check it is really a gzip archive before trusting it.
tar -tzf "${TMP}/pack.tar.gz" >/dev/null 2>&1 \
    || die "the downloaded file is not a valid archive.
  Usually this means the token was rejected and an error page was saved instead."
say "downloaded $(du -h "${TMP}/pack.tar.gz" | cut -f1)"

# --- 4. unpack --------------------------------------------------------------
# Overwrites in place on a re-run. Nothing of the buyer's lives in here: their
# LoRAs go in ComfyUI/models/loras and their edited workflow is saved by
# ComfyUI itself into user/default/workflows. This directory is only ever a
# copy of what we shipped.
# The archive's filename and its top-level directory now match: the published
# file is AIOFMTech-NSFW.tar.gz and it unpacks to AIOFMTech-NSFW/, the same way
# the video pack has always unpacked to AIOFMTech-Video/. They used to differ
# (AIOFMTech-NSFW.tar.gz -> OFMTech-NSFW/), which is why the directory is still
# read out of the archive rather than assumed -- that is what let the rename
# happen without touching this file, and it keeps either name renameable again.
PACK_TOP="$(tar -tzf "${TMP}/pack.tar.gz" | sed -n '1{s|/.*||;p;}')"
[[ -n "$PACK_TOP" ]] || die "could not read the top-level directory from the archive."
PACK_DIR="${DEST}/${PACK_TOP}"
if [[ -d "$PACK_DIR" ]]; then say "refreshing existing $PACK_DIR"; fi
tar -xzf "${TMP}/pack.tar.gz" -C "$DEST" || die "could not unpack the archive into $DEST"
[[ -f "${PACK_DIR}/aiofm_setup.sh" ]] \
    || die "unpacked, but ${PACK_DIR}/aiofm_setup.sh is not there. The archive layout has changed."
say "unpacked to $PACK_DIR"

# --- 5. hand over -----------------------------------------------------------
# cd first so the installer's own directory contains ComfyUI_INSTARAW and the
# workflow json. This is the whole reason the bootstrap exists.
cd "$PACK_DIR" || die "cannot enter $PACK_DIR"
rm -rf "$TMP"; trap - EXIT
printf '\n'
say "handing over to the installer in $PACK_DIR"
printf '\n'
exec bash ./aiofm_setup.sh "$@"
