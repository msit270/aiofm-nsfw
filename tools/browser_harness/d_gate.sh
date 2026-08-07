#!/usr/bin/env bash
#
# d_gate.sh — TRACK D's browser gate against the SHIPPED tarball.
#
#   bash tools/browser_harness/d_gate.sh stage1a   # real prompt in #106, stops before Run
#   bash tools/browser_harness/d_gate.sh stage1b   # shipped placeholder in #106, full render
#   bash tools/browser_harness/d_gate.sh stage2    # real prompt in #106, FULL RENDER  <- the gate
#
# Stage 2 is one command on purpose: when the #106 crash fix lands, run it and nothing
# else. It re-runs the identical journey with the identical prompt bytes.
#
# Exit codes are gate.js's, passed straight through:  0 pass · 1 workflow broken · 2 could not run.
#
set -uo pipefail

REPO=/workspace/nsfw-fix
PORT=31910                                   # TRACK D's own port. 18188=A, 28191=B: never touched.
TARGET=/workspace/comfy-d-gate               # built from the tarball into a dir that was empty
OUT="$REPO/results/gate2"
EXPECT_ARTIFACT=8f37692638535f004c19e93454c90f395774ca4bba737f8fb9cbf0adf21c41f5
EXPECT_WORKFLOW=4741960602085c6277eecd5f3d25e8e023e71df842c5987714886ef2fca30d4b

STAGE="${1:-}"
case "$STAGE" in stage1a|stage1b|stage2) ;; *)
  echo "usage: $0 {stage1a|stage1b|stage2}" >&2; exit 2 ;;
esac

mkdir -p "$OUT"

echo "=== preflight ==="
GOT=$(sha256sum "$REPO/dist/AIOFMTech-NSFW.tar.gz" | cut -d' ' -f1)
echo "  artifact sha256 : $GOT"
if [[ "$GOT" != "$EXPECT_ARTIFACT" ]]; then
  echo "  ✗ artifact is NOT the one this gate covers ($EXPECT_ARTIFACT) — re-cut, re-install, re-run" >&2; exit 2
fi
WF=$(sha256sum "$TARGET/user/default/workflows/OFMTech_NSFW.json" 2>/dev/null | cut -d' ' -f1)
echo "  workflow sha256 : ${WF:-MISSING}"
if [[ "$WF" != "$EXPECT_WORKFLOW" ]]; then
  echo "  ✗ the workflow in $TARGET is not the artifact's ($EXPECT_WORKFLOW)" >&2; exit 2
fi

# The port must answer, and it must be OUR ComfyUI. A successful probe against the
# wrong server is worse than a failed run, so this checks the process behind the
# socket, not just that something replied.
PID=$(ss -ltnp "sport = :$PORT" 2>/dev/null | grep -o 'pid=[0-9]*' | head -1 | cut -d= -f2)
if [[ -z "${PID:-}" ]]; then
  echo "  ✗ nothing is listening on $PORT — start Track D's ComfyUI first. NOT falling back to any other port." >&2; exit 2
fi
ARGS=$(tr '\0' ' ' < "/proc/$PID/cmdline" 2>/dev/null)
echo "  :$PORT is pid $PID"
echo "  argv            : $ARGS"
case "$ARGS" in
  *"--port $PORT"*) ;;
  *) echo "  ✗ the process on $PORT was not started with --port $PORT — refusing to probe it" >&2; exit 2 ;;
esac
case "$ARGS" in
  *"$TARGET"*|*"main.py"*) ;;
  *) echo "  ✗ unexpected process on $PORT" >&2; exit 2 ;;
esac
CWD=$(readlink -f "/proc/$PID/cwd" 2>/dev/null)
echo "  cwd             : $CWD"
if [[ "$CWD" != "$TARGET" ]]; then
  echo "  ✗ the ComfyUI on $PORT is not running out of $TARGET — refusing" >&2; exit 2
fi
curl -fsS --max-time 5 "http://127.0.0.1:$PORT/system_stats" >/dev/null || {
  echo "  ✗ $PORT did not answer /system_stats" >&2; exit 2; }
echo "  preflight OK"

COMMON=(--workflow OFMTech_NSFW --url "http://127.0.0.1:$PORT"
        --workflows-dir "$TARGET/user/default/workflows"
        --output-dir "$TARGET/output" --out "$OUT")

case "$STAGE" in
  stage1a)
    echo "=== STAGE 1A — REAL character prompt in #106, stops before Run (no render) ==="
    set -x
    node "$REPO/tools/browser_harness/gate.js" "${COMMON[@]}" \
        --tag stage1a-realprompt-nosubmit \
        --face-prompt-file "$REPO/tools/browser_harness/face_prompt_real.txt" \
        --no-run
    ;;
  stage1b)
    echo "=== STAGE 1B — SHIPPED PLACEHOLDER in #106, full render to a finished image ==="
    echo "    (the placeholder is the prompt observed safe; this leg proves the harness"
    echo "     end to end. It is NOT a real-prompt render and must not be presented as one.)"
    set -x
    node "$REPO/tools/browser_harness/gate.js" "${COMMON[@]}" \
        --tag stage1b-placeholder-render \
        --face-prompt-file "$REPO/tools/browser_harness/face_prompt_placeholder.txt"
    ;;
  stage2)
    echo "=== STAGE 2 — REAL character prompt in #106, FULL RENDER. This is the gate. ==="
    set -x
    node "$REPO/tools/browser_harness/gate.js" "${COMMON[@]}" \
        --tag stage2-realprompt-render \
        --face-prompt-file "$REPO/tools/browser_harness/face_prompt_real.txt"
    ;;
esac
RC=$?
set +x
echo "=== gate.js exit code $RC  (0=pass 1=workflow broken 2=could not run) ==="

# A status of success is not an image. Any render leg gets its output measured for the
# silent flat-grey failure, and a flat image demotes the whole run to a failure.
case "$STAGE" in
  stage1b|stage2)
    TAG=$([ "$STAGE" = stage1b ] && echo stage1b-placeholder-render || echo stage2-realprompt-render)
    RJ="$OUT/$TAG-result.json"
    if [[ -f "$RJ" ]]; then
      mapfile -t IMGS < <(python3 -c "
import json,sys
d=json.load(open('$RJ'))
for o in d.get('outputs') or []:
    if o.get('exists'): print(o['path'])
")
      if (( ${#IMGS[@]} )); then
        echo "=== is it actually an image, or the silent flat-grey failure? ==="
        /venv/main/bin/python "$REPO/tools/browser_harness/check_image.py" \
            --json "$OUT/$TAG-image_check.json" "${IMGS[@]}"
        IRC=$?
        echo "  image check exit $IRC"
        if (( IRC != 0 )) && (( RC == 0 )); then
          echo "  ✗ gate.js passed but the delivered image reads as the flat-grey failure — demoting to FAIL"
          RC=1
        fi
      else
        echo "  ✗ no output image on disk to check"
        (( RC == 0 )) && RC=1
      fi
    fi
    ;;
esac
echo "=== $STAGE final exit code $RC ==="

# the graph is frozen: prove this run did not write to it
WF2=$(sha256sum "$TARGET/user/default/workflows/OFMTech_NSFW.json" | cut -d' ' -f1)
echo "workflow on disk after the run: $WF2"
[[ "$WF2" == "$EXPECT_WORKFLOW" ]] && echo "  unchanged — the browser saved nothing" \
                                   || echo "  ✗ THE WORKFLOW ON DISK CHANGED"
exit $RC
