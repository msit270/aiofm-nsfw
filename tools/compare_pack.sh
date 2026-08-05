#!/usr/bin/env bash
#
# compare_pack.sh OLD.tar.gz NEW.tar.gz
#
# Reports every addition and removal between two pack archives, comparing paths
# BELOW the top-level directory so a directory rename does not read as "every
# file removed and every file added".
#
# Also reports files whose content changed, by per-entry sha256 of the extracted
# bytes. That is a checksum of an archive member, not of a rendered image -- the
# banned verification method on this project is hashing renders, and this is not
# that.
#
set -euo pipefail

OLD="${1:?usage: compare_pack.sh OLD.tar.gz NEW.tar.gz}"
NEW="${2:?usage: compare_pack.sh OLD.tar.gz NEW.tar.gz}"

TMP="$(mktemp -d "${TMPDIR:-/tmp}/packcmp.XXXXXX")"
trap 'rm -rf "$TMP"' EXIT

listing() {   # $1 = archive, $2 = output prefix
    local a="$1" p="$2"
    mkdir -p "$TMP/$p"
    tar -xzf "$a" -C "$TMP/$p"
    ( cd "$TMP/$p"/*/ && find . -type f | sed 's|^\./||' | sort ) > "$TMP/$p.list"
    ( cd "$TMP/$p"/*/ && find . -type f -print0 | sort -z \
        | xargs -0 sha256sum ) | sed 's|\./||' | sort -k2 > "$TMP/$p.sums"
    ( cd "$TMP/$p" && ls -d */ ) | tr -d '/' > "$TMP/$p.top"
}

listing "$OLD" old
listing "$NEW" new

printf '\n  old : %s\n' "$OLD"
printf '        top-level %s/   %s bytes   sha256 %s\n' \
    "$(cat "$TMP/old.top")" "$(stat -c %s "$OLD")" "$(sha256sum "$OLD" | cut -d' ' -f1)"
printf '  new : %s\n' "$NEW"
printf '        top-level %s/   %s bytes   sha256 %s\n\n' \
    "$(cat "$TMP/new.top")" "$(stat -c %s "$NEW")" "$(sha256sum "$NEW" | cut -d' ' -f1)"

ADDED="$(comm -13 "$TMP/old.list" "$TMP/new.list")"
REMOVED="$(comm -23 "$TMP/old.list" "$TMP/new.list")"
COMMON="$(comm -12 "$TMP/old.list" "$TMP/new.list")"

printf '  files: %s old -> %s new\n\n' \
    "$(wc -l < "$TMP/old.list")" "$(wc -l < "$TMP/new.list")"

if [[ -n "$ADDED" ]]; then
    printf '  ADDED (%s):\n' "$(printf '%s\n' "$ADDED" | wc -l)"
    printf '%s\n' "$ADDED" | sed 's/^/    + /'
else
    printf '  ADDED: none\n'
fi
printf '\n'

if [[ -n "$REMOVED" ]]; then
    printf '  REMOVED (%s):\n' "$(printf '%s\n' "$REMOVED" | wc -l)"
    printf '%s\n' "$REMOVED" | sed 's/^/    - /'
else
    printf '  REMOVED: none\n'
fi
printf '\n'

CHANGED=""
while IFS= read -r f; do
    [[ -n "$f" ]] || continue
    o="$(grep -F "  $f" "$TMP/old.sums" | head -1 | cut -d' ' -f1)"
    n="$(grep -F "  $f" "$TMP/new.sums" | head -1 | cut -d' ' -f1)"
    [[ "$o" == "$n" ]] || CHANGED="${CHANGED}${f}"$'\n'
done <<< "$COMMON"

if [[ -n "$CHANGED" ]]; then
    printf '  CHANGED (%s):\n' "$(printf '%s' "$CHANGED" | grep -c .)"
    printf '%s' "$CHANGED" | sed 's/^/    ~ /'
else
    printf '  CHANGED: none\n'
fi
printf '\n'
