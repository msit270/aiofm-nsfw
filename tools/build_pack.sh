#!/usr/bin/env bash
#
# build_pack.sh — cut the distribution tarball for the OFM Tech NSFW pack.
#
# Why this is a script and not a one-line `tar czf`:
#
#   1. The archive name and its top-level directory MUST match. They did not:
#      dist/AIOFMTech-NSFW.tar.gz unpacked to OFMTech-NSFW/. The sibling video
#      pack has always matched (AIOFMTech-Video.tar.gz -> AIOFMTech-Video/), so
#      the NSFW pack was the odd one out. This script derives the top-level
#      directory from the output filename and then ASSERTS it in the finished
#      archive, so the mismatch cannot come back by hand.
#
#   2. The source tree in git is still OFMTech-NSFW/. Renaming that directory
#      would rewrite the paths three other work-streams are editing, so the
#      rename is done at pack time by staging instead. That is the only place
#      the two names differ and it is deliberate.
#
#   3. Reproducible: sorted entries, fixed mtime, zeroed owner/group,
#      normalised modes, gzip -n (no name or timestamp in the gzip header).
#      Same tree in, byte-identical archive out. That makes the published
#      sha256 a statement about content, not about when it was built.
#
#   4. Junk exclusion is declared in one place instead of being remembered.
#
# Usage:
#   bash tools/build_pack.sh                 # build dist/AIOFMTech-NSFW.tar.gz
#   bash tools/build_pack.sh --check         # build to a temp file, do not
#                                            # touch dist/, just report
#   OUT=/path/to/x.tar.gz bash tools/build_pack.sh
#
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="${SRC:-$REPO_ROOT/OFMTech-NSFW}"
OUT="${OUT:-$REPO_ROOT/dist/AIOFMTech-NSFW.tar.gz}"

CHECK_ONLY=0
[[ "${1:-}" == "--check" ]] && CHECK_ONLY=1

# Fixed timestamp so the build is content-determined. 2026-01-01T00:00:00Z.
# The value is arbitrary; that it never changes is the point.
SOURCE_DATE_EPOCH="${SOURCE_DATE_EPOCH:-1767225600}"

# The top-level directory inside the archive == the archive's own basename.
ARCHIVE_BASE="$(basename "$OUT")"
TOP="${ARCHIVE_BASE%.tar.gz}"
[[ "$TOP" != "$ARCHIVE_BASE" ]] || { echo "✗ OUT must end in .tar.gz: $OUT" >&2; exit 1; }

# Never pack anything but the authoritative tree. /workspace/OFMTech-NSFW is a
# known stale duplicate on the build pod and packing it would silently ship the
# pre-fix workflow.
[[ -f "$SRC/aiofm_setup.sh" && -f "$SRC/OFMTech_NSFW.json" ]] \
    || { echo "✗ $SRC does not look like the pack source (aiofm_setup.sh / OFMTech_NSFW.json missing)" >&2; exit 1; }

# Junk. Declared once. rsync patterns.
EXCLUDES=(
    '__pycache__/'  '*.pyc'  '*.pyo'  '*.pyd'
    '.ipynb_checkpoints/'
    '.git/'  '.gitignore'  '.gitattributes'
    '.mypy_cache/'  '.pytest_cache/'  '.ruff_cache/'
    '.DS_Store'  '._*'  'Thumbs.db'  'desktop.ini'
    '*.swp'  '*.swo'  '*~'  '#*#'  '.#*'
    '*.orig'  '*.rej'
    '.idea/'  '.vscode/'
    '*.log'
)

STAGE="$(mktemp -d "${TMPDIR:-/tmp}/aiofm-pack.XXXXXX")"
trap 'rm -rf "$STAGE"' EXIT

RSYNC_ARGS=()
for e in "${EXCLUDES[@]}"; do RSYNC_ARGS+=(--exclude "$e"); done

mkdir -p "$STAGE/$TOP"
rsync -a "${RSYNC_ARGS[@]}" "$SRC"/ "$STAGE/$TOP"/

# Normalise modes. Nothing in this pack needs to be executable -- both the
# bootstrap and INSTALL MODELS.txt invoke the installer as `bash aiofm_setup.sh`
# -- but shipping .sh files without +x reads as broken to anyone who tries
# ./aiofm_setup.sh, so scripts keep it and nothing else does.
find "$STAGE/$TOP" -type d -exec chmod 755 {} +
find "$STAGE/$TOP" -type f -exec chmod 644 {} +
find "$STAGE/$TOP" -type f -name '*.sh' -exec chmod 755 {} +

BUILD_TO="$OUT"
if (( CHECK_ONLY )); then
    BUILD_TO="$STAGE/$ARCHIVE_BASE"
else
    mkdir -p "$(dirname "$OUT")"
fi

tar --sort=name \
    --format=gnu \
    --numeric-owner --owner=0 --group=0 \
    --mtime="@$SOURCE_DATE_EPOCH" \
    -cf - -C "$STAGE" "$TOP" \
  | gzip -n -9 > "$BUILD_TO"

# --- assertions on the finished artifact, not on the staging dir -------------
# Listed ONCE into a file. `tar -tzf … | grep -q …` looks equivalent and is not:
# grep -q exits on its first match, tar takes SIGPIPE, and under `set -o
# pipefail` the pipeline returns 141 -- so the check fails loudest exactly when
# the file IS present. That cost a build here before it was spotted, and it is
# the same SIGPIPE-vs-pipefail trap the gist bootstrap avoids by using sed
# rather than head.
LIST="$STAGE/.listing"
tar -tzf "$BUILD_TO" > "$LIST"

TOPS="$(awk -F/ '{print $1}' "$LIST" | sort -u)"
[[ "$TOPS" == "$TOP" ]] \
    || { echo "✗ archive top-level is '$TOPS', expected '$TOP'" >&2; exit 1; }

# This is the exact expression the live gist bootstrap uses to find the
# directory (aiofm_setupnsfw.sh line 99). Asserting on the same expression
# means the archive is checked the way the buyer's installer reads it.
PACK_TOP="$(sed -n '1{s|/.*||;p;}' "$LIST")"
[[ "$PACK_TOP" == "$TOP" ]] \
    || { echo "✗ bootstrap PACK_TOP would read '$PACK_TOP', expected '$TOP'" >&2; exit 1; }

# The bootstrap dies if this file is not where it expects it (line 104).
for must in "$TOP/aiofm_setup.sh" "$TOP/OFMTech_NSFW.json" "$TOP/INSTALL MODELS.txt"; do
    grep -qxF "$must" "$LIST" \
        || { echo "✗ '$must' is not in the archive" >&2; exit 1; }
done

SIZE="$(stat -c %s "$BUILD_TO")"
SHA="$(sha256sum "$BUILD_TO" | cut -d' ' -f1)"
NFILES="$(grep -vc '/$' "$LIST" || true)"

printf '\n  archive   : %s\n' "$BUILD_TO"
printf '  top-level : %s/   (matches archive name)\n' "$PACK_TOP"
printf '  entries   : %s files\n' "$NFILES"
printf '  size      : %s bytes\n' "$SIZE"
printf '  sha256    : %s\n\n' "$SHA"

if (( CHECK_ONLY )); then
    echo "  --check: dist/ not written"
fi
