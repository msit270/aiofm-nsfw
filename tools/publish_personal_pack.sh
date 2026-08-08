#!/usr/bin/env bash
# publish_personal_pack.sh — upload the personal pack to a PRIVATE HF repo and
# verify it. The pod's own HF token is read-only (role: read, VastAI), so this
# needs the OWNER's write token:
#
#   HF_WRITE_TOKEN=hf_xxx bash tools/publish_personal_pack.sh
#   bash tools/publish_personal_pack.sh /path/to/token_file
#
# Safety: never touches msit270/AIOFM-Pack (buyer-readable); creates the repo
# PRIVATE; if the repo already exists but is NOT private, aborts before any
# byte is uploaded; after upload, proves anonymous download is blocked and the
# authed round-trip hash matches the local pack.
set -euo pipefail

REPO="${PERSONAL_REPO:-msit270/AIOFM-Personal}"
PACK="${PACK:-/workspace/nsfw-quality/dist-personal/AIOFMTech-NSFW-Personal.tar.gz}"
# Repo-ROOT path: matches where the owner actually uploaded v4 (2026-08-08),
# so re-publishing overwrites the live file instead of forking a dist/ copy.
DEST_PATH="AIOFMTech-NSFW-Personal.tar.gz"

TOK="${HF_WRITE_TOKEN:-}"
[[ -z "$TOK" && -n "${1:-}" && -s "${1:-}" ]] && TOK="$(cat "$1")"
[[ -n "$TOK" ]] || { echo "x need HF_WRITE_TOKEN env or a token-file argument" >&2; exit 2; }
[[ -s "$PACK" ]] || { echo "x no pack at $PACK" >&2; exit 2; }
case "$REPO" in *AIOFM-Pack*) echo "x refusing: $REPO is the buyer-readable repo" >&2; exit 2;; esac

LOCAL_SHA="$(sha256sum "$PACK" | cut -d' ' -f1)"
echo "  pack   : $PACK"
echo "  sha256 : $LOCAL_SHA"
echo "  repo   : $REPO (target path: $DEST_PATH)"

ROLE="$(curl -fsS -H "Authorization: Bearer $TOK" https://huggingface.co/api/whoami-v2 \
  | python3 -c "import json,sys; d=json.load(sys.stdin); a=d.get('auth',{}).get('accessToken',{}); print(d.get('name'), '/', a.get('role') or 'fine-grained')")"
echo "  token  : $ROLE"

CODE="$(curl -s -o /tmp/hfrepo.json -w '%{http_code}' -H "Authorization: Bearer $TOK" \
  "https://huggingface.co/api/models/$REPO")"
if [[ "$CODE" == "404" ]]; then
  curl -fsS -X POST -H "Authorization: Bearer $TOK" -H 'Content-Type: application/json' \
    -d "{\"name\":\"${REPO#*/}\",\"type\":\"model\",\"private\":true}" \
    https://huggingface.co/api/repos/create >/dev/null
  echo "  created $REPO as PRIVATE"
elif [[ "$CODE" == "200" ]]; then
  PRIV="$(python3 -c "import json; print(json.load(open('/tmp/hfrepo.json')).get('private'))")"
  [[ "$PRIV" == "True" ]] || { echo "x $REPO exists and is NOT private — refusing to upload" >&2; exit 1; }
  echo "  $REPO exists and is private: OK"
else
  echo "x unexpected HTTP $CODE checking $REPO" >&2; exit 1
fi

HF_TOKEN="$TOK" hf upload "$REPO" "$PACK" "$DEST_PATH" --repo-type model

URL="https://huggingface.co/$REPO/resolve/main/$DEST_PATH"

ANON="$(curl -s -o /dev/null -w '%{http_code}' -L "$URL")"
[[ "$ANON" != "200" ]] || { echo "x ANONYMOUS DOWNLOAD SUCCEEDED — repo is public, fix immediately" >&2; exit 1; }
echo "  anonymous fetch blocked (HTTP $ANON): private confirmed"

RT="$(curl -fsSL -H "Authorization: Bearer $TOK" "$URL" | sha256sum | cut -d' ' -f1)"
[[ "$RT" == "$LOCAL_SHA" ]] || { echo "x round-trip hash mismatch: $RT" >&2; exit 1; }
echo "  round-trip sha256 verified: $RT"

echo
echo "=== PUBLISHED + VERIFIED ==="
echo "AIOFM_PACK_URL=\"$URL\""
