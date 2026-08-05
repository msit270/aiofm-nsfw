#!/usr/bin/env bash
#
# verify_buyer_path.sh — run the LIVE gist bootstrap the way a buyer runs it.
#
# Cases:
#   gist        fetch the bootstrap from api.github.com (authoritative) and
#               compare it byte-for-byte against the raw CDN URL, which serves
#               a cache and can lag an edit by minutes to hours.
#   no-token    no HF_TOKEN and no token file            -> expect exit 1
#   bad-token   a token the Hub rejects                  -> expect exit 1
#   bad-archive a 200 response that is not a gzip archive -> expect exit 1
#   prepare     build a fresh, EMPTY ComfyUI install target
#   happy       full install into that target from a local mirror of the pack
#   nodes       start that target's ComfyUI and check every node type the
#               NSFW workflow references actually registered
#
# Safety rules this script enforces, because the pod is shared:
#
#   * COMFYUI_PORT is forced to a dead port for the happy path. The installer's
#     restart stage does `supervisorctl restart <comfy program>` whenever it can
#     reach ComfyUI, and supervisord here manages the LIVE instance on 18188
#     that other work is rendering against. A dead port makes comfy_up() false,
#     the installer takes its "ComfyUI is not running" branch, and nothing is
#     restarted. Node registration is then verified by this script instead,
#     against its own instance -- a stricter check, since that instance has a
#     custom_nodes directory the installer populated from empty.
#
#   * The fresh target's models/ is HARDLINKED from the live ComfyUI. 179 GB of
#     models for 0 bytes of disk, and the installer skips every download whose
#     size matches the manifest. Downloads that do happen write to a temp file
#     and rename, so they replace this tree's link and never the live file.
#     `prepare` records inode/size/mtime for the live models tree and `nodes`
#     re-checks it, so any in-place write would be caught rather than assumed
#     away.
#
set -uo pipefail

GIST_ID="70256ac1ebf2760e10f78804862db528"
GIST_FILE="aiofm_setupnsfw.sh"
GIST_RAW="https://gist.githubusercontent.com/msit270/${GIST_ID}/raw/${GIST_FILE}"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK="${WS5_WORK:-/workspace/ws5-verify}"
TARGET="${WS5_TARGET:-/workspace/comfy-ws5-verify}"
LIVE_COMFY="${WS5_LIVE_COMFY:-/workspace/ComfyUI}"
DEAD_PORT="${WS5_DEAD_PORT:-39997}"     # nothing listens here; keep it that way
MIRROR_PORT="${WS5_MIRROR_PORT:-38080}"
NODE_PORT="${WS5_NODE_PORT:-28188}"
PACK="${WS5_PACK:-$REPO_ROOT/dist/AIOFMTech-NSFW.tar.gz}"

BOOT="$WORK/$GIST_FILE"
mkdir -p "$WORK"

hr() { printf '\n%s\n' "------------------------------------------------------------"; }
note() { printf '  %s\n' "$*"; }

df_now() { df --output=pcent,avail / | tail -1 | tr -s ' '; }

# --- fetch the live bootstrap, authoritatively -------------------------------
c_gist() {
    hr; echo "CASE gist — what is actually live right now"
    python3 - "$GIST_ID" "$GIST_FILE" "$BOOT" <<'PY'
import json, sys, urllib.request
gid, fname, out = sys.argv[1], sys.argv[2], sys.argv[3]
d = json.load(urllib.request.urlopen(
    urllib.request.Request("https://api.github.com/gists/" + gid,
                           headers={"Accept": "application/vnd.github+json"}),
    timeout=30))
print("  gist            : %s  (public=%s, owner=%s)" % (d["id"], d["public"],
                                                         (d.get("owner") or {}).get("login")))
print("  updated_at      : %s" % d["updated_at"])
print("  files in gist   : %s" % ", ".join(sorted(d["files"])))
f = d["files"][fname]
c = f["content"]
# The API returns content as a STRING. len(c) is characters; the byte count a
# byte-for-byte comparison needs is len(c.encode()).
print("  %-15s : %d bytes (%d characters), %d lines, truncated=%s"
      % (fname, len(c.encode()), len(c), c.count("\n"), f["truncated"]))
open(out, "w").write(c)
PY
    [[ -s "$BOOT" ]] || { echo "  ✗ could not write $BOOT"; return 1; }
    note "sha256 (api)    : $(sha256sum "$BOOT" | cut -d' ' -f1)"
    curl -sSL "$GIST_RAW" -o "$WORK/cdn.$GIST_FILE"
    note "sha256 (raw CDN): $(sha256sum "$WORK/cdn.$GIST_FILE" | cut -d' ' -f1)"
    if cmp -s "$BOOT" "$WORK/cdn.$GIST_FILE"; then
        note "raw CDN matches the API right now"
    else
        note "✗ raw CDN DIFFERS from the API — the CDN is serving a stale cache"
        diff "$WORK/cdn.$GIST_FILE" "$BOOT" | head -40
    fi
    # SETUP_URL in the shipped installer names a file in this same gist.
    local code
    code="$(curl -sS -o /dev/null -w '%{http_code}' -L \
        "https://gist.githubusercontent.com/msit270/${GIST_ID}/raw/aiofm_setupall.sh")"
    note "aiofm_setupall.sh (named by aiofm_setup.sh SETUP_URL): HTTP $code"
}

run_case() {   # $1 = label, rest = command
    local label="$1"; shift
    hr; echo "CASE $label"
    local out rc
    out="$("$@" 2>&1)"; rc=$?
    printf '%s\n' "$out" | sed 's/^/  | /'
    printf '\n  --> exit code %d\n' "$rc"
    return $rc
}

c_no_token() {
    rm -rf "$WORK/dest-notoken"; mkdir -p "$WORK/dest-notoken"
    run_case "no-token" env -u HF_TOKEN \
        HF_TOKEN_FILE="$WORK/definitely-not-a-token-file" \
        AIOFM_DEST="$WORK/dest-notoken" \
        bash "$BOOT"
}

c_bad_token() {
    rm -rf "$WORK/dest-badtoken"; mkdir -p "$WORK/dest-badtoken"
    printf 'hf_thisTokenIsNotValid000000000000000000\n' > "$WORK/bad.token"
    run_case "bad-token" env -u HF_TOKEN \
        HF_TOKEN_FILE="$WORK/bad.token" \
        AIOFM_DEST="$WORK/dest-badtoken" \
        bash "$BOOT"
}

mirror_start() {   # serves $WORK/mirror on $MIRROR_PORT
    mkdir -p "$WORK/mirror"
    ( cd "$WORK/mirror" && exec python3 -m http.server "$MIRROR_PORT" --bind 127.0.0.1 ) \
        > "$WORK/mirror.log" 2>&1 &
    MIRROR_PID=$!
    local i=0
    while (( i < 40 )); do
        curl -fsS -o /dev/null "http://127.0.0.1:$MIRROR_PORT/" 2>/dev/null && return 0
        i=$((i+1)); sleep 0.25
    done
    echo "  ✗ mirror did not come up"; return 1
}
mirror_stop() { [[ -n "${MIRROR_PID:-}" ]] && kill "$MIRROR_PID" 2>/dev/null; MIRROR_PID=""; }

c_bad_archive() {
    rm -rf "$WORK/dest-badarchive"; mkdir -p "$WORK/dest-badarchive" "$WORK/mirror"
    # An auth error page delivered with HTTP 200 — the case the bootstrap's
    # tar -tzf guard exists for.
    cat > "$WORK/mirror/not-an-archive.tar.gz" <<'EOF'
<!DOCTYPE html><html><head><title>401 Unauthorized</title></head>
<body><h1>Invalid credentials</h1></body></html>
EOF
    mirror_start || return 1
    run_case "bad-archive" env \
        HF_TOKEN="dummy-token-not-used-by-a-local-mirror" \
        AIOFM_PACK_URL="http://127.0.0.1:$MIRROR_PORT/not-an-archive.tar.gz" \
        AIOFM_DEST="$WORK/dest-badarchive" \
        bash "$BOOT"
    local rc=$?
    mirror_stop
    return $rc
}

# --- a genuinely empty ComfyUI to install into --------------------------------
c_prepare() {
    hr; echo "CASE prepare — empty ComfyUI install target at $TARGET"
    note "disk before: $(df_now)"
    [[ -d "$LIVE_COMFY" ]] || { echo "  ✗ $LIVE_COMFY not found"; return 1; }
    rm -rf "$TARGET"; mkdir -p "$TARGET"

    # Everything except models/ and the runtime dirs, as a REAL copy, so no
    # write here can reach the live install through a shared inode.
    # Anchored with a leading slash. An unanchored 'models/' also matches
    # .cache/huggingface/download/models/, which is where hf keeps the per-file
    # download metadata -- losing it turns "verify 74 files" into "re-download
    # 178 GB", and the only symptom is a metadata count of 0.
    rsync -a \
        --exclude '/models/' --exclude '/custom_nodes/' --exclude '/user/' \
        --exclude '/output/' --exclude '/input/' --exclude '/temp/' \
        --exclude '/.tmpdl/' --exclude '/.aiofm_expected_sizes.txt' \
        "$LIVE_COMFY"/ "$TARGET"/ || return 1
    mkdir -p "$TARGET/custom_nodes" "$TARGET/user" "$TARGET/output" \
             "$TARGET/input" "$TARGET/temp"

    # models/ hardlinked: 0 bytes, and .cache/huggingface came across in the
    # rsync above as a real copy, so `hf download --local-dir` finds its
    # per-file metadata and re-verifies instead of re-fetching 178 GB.
    cp -al "$LIVE_COMFY/models" "$TARGET/models" || return 1

    note "custom_nodes entries: $(ls -A "$TARGET/custom_nodes" | wc -l)  (0 = empty, as intended)"
    note "models entries      : $(ls -A "$TARGET/models" | wc -l) directories, hardlinked"
    note "hf download metadata: $(find "$TARGET/.cache/huggingface/download" -name '*.metadata' 2>/dev/null | wc -l) files"

    # Fingerprint of the LIVE models tree, to prove afterwards that nothing
    # wrote through a hardlink.
    find "$LIVE_COMFY/models" -type f -printf '%i %s %T@ %p\n' | sort > "$WORK/live-models.before"
    note "live models fingerprint: $(wc -l < "$WORK/live-models.before") files recorded"
    note "disk after : $(df_now)"
}

c_happy() {
    hr; echo "CASE happy — live gist bootstrap into $TARGET"
    [[ -f "$PACK" ]] || { echo "  ✗ pack not found: $PACK"; return 1; }
    [[ -d "$TARGET/custom_nodes" ]] || { echo "  ✗ run 'prepare' first"; return 1; }
    if curl -fsS --max-time 3 "http://127.0.0.1:$DEAD_PORT/system_stats" >/dev/null 2>&1; then
        echo "  ✗ something is listening on the supposedly dead port $DEAD_PORT — refusing to run"
        return 1
    fi

    mkdir -p "$WORK/mirror"
    cp -f "$PACK" "$WORK/mirror/$(basename "$PACK")"
    mirror_start || return 1
    rm -rf "$WORK/dest-happy"; mkdir -p "$WORK/dest-happy"

    note "disk before: $(df_now)"
    note "pack sha256: $(sha256sum "$PACK" | cut -d' ' -f1)"
    /venv/main/bin/pip freeze > "$WORK/pip.before" 2>/dev/null

    local t0=$SECONDS rc
    env HF_TOKEN="$(tr -d '[:space:]' < /workspace/.hf_token)" \
        AIOFM_PACK_URL="http://127.0.0.1:$MIRROR_PORT/$(basename "$PACK")" \
        AIOFM_DEST="$WORK/dest-happy" \
        COMFYUI_DIR="$TARGET" \
        COMFYUI_PORT="$DEAD_PORT" \
        SETUP_LOG="$WORK/setup.log" \
        bash "$BOOT" 2>&1 | tee "$WORK/happy.out"
    rc=${PIPESTATUS[0]}
    mirror_stop

    printf '\n  --> exit code %d after %ds\n' "$rc" "$((SECONDS - t0))"
    note "disk after : $(df_now)"
    /venv/main/bin/pip freeze > "$WORK/pip.after" 2>/dev/null
    if diff -q "$WORK/pip.before" "$WORK/pip.after" >/dev/null; then
        note "shared venv unchanged (pip freeze identical before/after)"
    else
        note "shared venv CHANGED:"
        diff "$WORK/pip.before" "$WORK/pip.after" | sed 's/^/    /'
    fi
    note "unpacked to: $(ls -d "$WORK"/dest-happy/*/ 2>/dev/null)"
    return $rc
}

c_nodes() {
    hr; echo "CASE nodes — does every node type the NSFW workflow needs register?"
    local wf
    wf="$(ls "$TARGET"/user/default/workflows/OFMTech_NSFW.json 2>/dev/null)" || true
    [[ -n "$wf" ]] || { echo "  ✗ workflow not installed at $TARGET/user/default/workflows"; return 1; }
    note "workflow installed: $wf"

    # --cpu so this second instance cannot contend for the GPU other work is on.
    ( cd "$TARGET" && exec /venv/main/bin/python main.py --cpu --port "$NODE_PORT" \
        --disable-auto-launch --listen 127.0.0.1 ) > "$WORK/comfy.log" 2>&1 &
    local pid=$!
    note "started ComfyUI from $TARGET on port $NODE_PORT (pid $pid, --cpu)"
    local i=0 up=0
    while (( i < 180 )); do
        if curl -fsS --max-time 3 "http://127.0.0.1:$NODE_PORT/system_stats" >/dev/null 2>&1; then
            up=1; break
        fi
        kill -0 "$pid" 2>/dev/null || break
        i=$((i+1)); sleep 1
    done
    if (( ! up )); then
        echo "  ✗ it did not come up in ${i}s — tail of its log:"
        tail -30 "$WORK/comfy.log" | sed 's/^/    /'
        kill "$pid" 2>/dev/null
        return 1
    fi
    note "up after ${i}s"

    python3 - "http://127.0.0.1:$NODE_PORT" "$wf" <<'PY'
import json, sys, urllib.request
url, wfp = sys.argv[1], sys.argv[2]
doc = json.load(open(wfp))
subs = {s["id"]: s for s in doc.get("definitions", {}).get("subgraphs", [])}
nodes = list(doc.get("nodes", []))
for s in subs.values():
    nodes.extend(s.get("nodes", []))
need = set()
for n in nodes:
    t = n.get("type")
    if t and t not in ("Note", "MarkdownNote") and t not in subs:
        need.add(t)
have = set(json.load(urllib.request.urlopen(url + "/object_info", timeout=120)))
missing = sorted(t for t in need if t not in have)
print("  node types the workflow references : %d" % len(need))
print("  node types registered by ComfyUI    : %d" % len(have))
if missing:
    print("  ✗ %d did NOT register:" % len(missing))
    for m in missing:
        print("      " + m)
    sys.exit(2)
print("  ✓ all %d registered" % len(need))
PY
    local rc=$?
    kill "$pid" 2>/dev/null; wait "$pid" 2>/dev/null

    # Did anything write through a hardlink into the live models tree?
    if [[ -f "$WORK/live-models.before" ]]; then
        find "$LIVE_COMFY/models" -type f -printf '%i %s %T@ %p\n' | sort > "$WORK/live-models.after"
        if diff -q "$WORK/live-models.before" "$WORK/live-models.after" >/dev/null; then
            note "live models tree untouched (inode/size/mtime identical for every file)"
        else
            note "✗ LIVE MODELS TREE CHANGED:"
            diff "$WORK/live-models.before" "$WORK/live-models.after" | head -20 | sed 's/^/    /'
            rc=3
        fi
    fi
    return $rc
}

case "${1:-all}" in
    gist)        c_gist ;;
    no-token)    c_no_token ;;
    bad-token)   c_bad_token ;;
    bad-archive) c_bad_archive ;;
    prepare)     c_prepare ;;
    happy)       c_happy ;;
    nodes)       c_nodes ;;
    all)         c_gist; c_no_token; c_bad_token; c_bad_archive
                 c_prepare && c_happy && c_nodes ;;
    *)           echo "usage: $0 {gist|no-token|bad-token|bad-archive|prepare|happy|nodes|all}"; exit 1 ;;
esac
