#!/usr/bin/env bash
# Gate retry: boot + render half of tools/fresh_install5.sh only, against the
# ALREADY-INSTALLED fresh7 tree (install half passed: exit 0, V9 byte-exact,
# loras vendored, workflow installed). First attempt failed on the known
# late-Templates-modal harness race; run.js now retries dismiss+click.
set -uo pipefail
TARGET=/workspace/comfy-fresh7
PORT=31980
OUT=/workspace/nsfw-quality/results/closing/fresh7

( cd "$TARGET" && exec python3 main.py --port "$PORT" --disable-auto-launch \
    --output-directory "$OUT/render" ) > "$OUT/comfy-fresh2.log" 2>&1 &
CPID=$!
for i in $(seq 1 90); do
  sleep 2
  curl -fsS --max-time 2 "http://127.0.0.1:$PORT/system_stats" >/dev/null 2>&1 && break
done
curl -fsS --max-time 2 "http://127.0.0.1:$PORT/system_stats" >/dev/null 2>&1 \
  || { echo "x fresh server did not boot"; kill $CPID; exit 1; }
echo "  fresh server up on :$PORT"
RUN5_DISMISS_BOOT=1 node /workspace/nsfw-quality/tools/browser_harness/run.js \
  --workflow OFMTech_NSFW_Personal --url "http://127.0.0.1:$PORT" \
  --out "$OUT/gate2" --drive-selector --selector-pick 0 2>>"$OUT/gate2.err" | tail -5
GRC=$?
kill $CPID 2>/dev/null
[[ $GRC -eq 0 ]] || { echo "x render gate failed (see $OUT/gate2)"; exit 1; }
GPNG="$(find "$OUT/render" -name '*.png' | head -1)"
[[ -n "$GPNG" ]] || { echo "x no gate render output"; exit 1; }
/workspace/run5/venv/bin/python - "$GPNG" <<'PY'
import sys, cv2
sys.path.insert(0, "/workspace/run5/tools")
from likeness import top_face
im = cv2.imread(sys.argv[1])
assert im is not None and im.mean() > 20, f"gate render black/degenerate (mean {im.mean():.1f})"
f = top_face(sys.argv[1])
assert f is not None, "no face detected in gate render (black-face NaN?)"
print(f"  gate render healthy: mean {im.mean():.1f}, face det {f['det']:.3f}")
PY
[[ $? -eq 0 ]] || { echo "x gate render failed the black/face check"; exit 1; }
echo "=== PASS: fresh-tree personal install + end-to-end render (gate2) ==="
