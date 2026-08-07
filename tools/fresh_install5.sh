#!/usr/bin/env bash
# Run-5 DoD: fresh ComfyUI tree + one-line install of the PERSONAL pack via
# the LIVE sellable gist bootstrap + AIOFM_PACK_URL override (local mirror
# until the owner publishes). Proves the personal deltas arrive:
#   * V9 checkpoint fetched from civitai.com (withheld from the tree)
#   * luna/lunaskye installed from the VENDORED pack (withheld)
#   * OFMTech_NSFW_Personal.json installed and rendering end-to-end
# Inherited deviations from a true fresh pod (recorded): other models
# hardlinked from the live install; ComfyUI core copied; same GPU/venv.
set -uo pipefail

TARGET="${FRESH_TARGET:-/workspace/comfy-fresh5}"
PORT="${FRESH_PORT:-31970}"
MPORT="${FRESH_MPORT:-31972}"
LIVE_COMFY=/workspace/ComfyUI
GIST_URL="https://gist.githubusercontent.com/msit270/70256ac1ebf2760e10f78804862db528/raw/aiofm_setupnsfw.sh"
OUT="${FRESH_OUT:-/workspace/nsfw-quality/results/run5/fresh}"
MIRROR_PACK="${MIRROR_PACK:-/workspace/nsfw-quality/dist-personal/AIOFMTech-NSFW-Personal.tar.gz}"
WITHHOLD=(
  "checkpoints/lustifyNSFWCheckpoint_zenithV9.safetensors"
  "loras/luna.safetensors"
  "loras/lunaskye.safetensors"
)
mkdir -p "$OUT"

echo "=== preconditions ==="
[[ -e "$TARGET" ]] && { echo "x $TARGET exists — delete deliberately first"; exit 2; }
curl -fsS --max-time 2 "http://127.0.0.1:$PORT/" >/dev/null 2>&1 && { echo "x something answers on $PORT"; exit 2; }
[[ -s /workspace/.civitai_token ]] || { echo "x no /workspace/.civitai_token"; exit 2; }
[[ -s "$MIRROR_PACK" ]] || { echo "x no personal pack at $MIRROR_PACK"; exit 2; }
echo "  target absent, port dead, civitai key present, pack present: OK"
mkdir -p "${FRESH_DEST:-/workspace/fresh5-dest}"

echo "=== fresh tree ==="
mkdir -p "$TARGET"
rsync -a \
    --exclude '/models/' --exclude '/custom_nodes/' --exclude '/user/' \
    --exclude '/output/' --exclude '/input/' --exclude '/temp/' \
    --exclude '/.tmpdl/' --exclude '/.aiofm_expected_sizes.txt' \
    "$LIVE_COMFY"/ "$TARGET"/ || exit 1
mkdir -p "$TARGET/custom_nodes" "$TARGET/user" "$TARGET/output" "$TARGET/input" "$TARGET/temp"
cp -al "$LIVE_COMFY/models" "$TARGET/models" || exit 1
for f in "${WITHHOLD[@]}"; do
  rm -f "$TARGET/models/$f"
  [[ -e "$TARGET/models/$f" ]] && { echo "x could not withhold $f"; exit 2; }
  echo "  withheld: models/$f"
done
# the sellable workflow must not mask the personal one in the fresh tree
rm -f "$TARGET/user/default/workflows/OFMTech_NSFW.json" 2>/dev/null

echo "=== local pack mirror on :$MPORT ==="
( cd "$(dirname "$MIRROR_PACK")" && exec python3 -m http.server "$MPORT" --bind 127.0.0.1 ) >/dev/null 2>&1 &
MIRROR_PID=$!
sleep 1
echo "  [pre-publish] pack sha256 $(sha256sum "$MIRROR_PACK" | cut -d' ' -f1)"

echo "=== one-line install (live gist + AIOFM_PACK_URL override) ==="
T0=$(date +%s)
AIOFM_PACK_URL="http://127.0.0.1:$MPORT/$(basename "$MIRROR_PACK")" \
AIOFM_DEST="${FRESH_DEST:-/workspace/fresh5-dest}" \
COMFYUI_DIR="$TARGET" \
bash <(curl -fsSL "$GIST_URL") > "$OUT/install.log" 2>&1
RC=$?
echo "  install exit $RC in $(( $(date +%s) - T0 ))s (log: $OUT/install.log)"
kill "$MIRROR_PID" 2>/dev/null
[[ $RC -eq 0 ]] || { tail -40 "$OUT/install.log"; exit 1; }

echo "=== personal deltas arrived? ==="
for f in "${WITHHOLD[@]}"; do
  [[ -s "$TARGET/models/$f" ]] || { echo "x missing after install: models/$f"; exit 1; }
  echo "  present: models/$f ($(stat -c %s "$TARGET/models/$f") B)"
done
V9SHA=$(sha256sum "$TARGET/models/checkpoints/lustifyNSFWCheckpoint_zenithV9.safetensors" | cut -d' ' -f1)
[[ "$V9SHA" == "1a3abf0bf48113eb5e17d2f8ae012c5b60cb97d81d79c4d9e47cd5af56c162f1" ]] \
  || { echo "x V9 sha mismatch: $V9SHA"; exit 1; }
echo "  V9 sha256 verified (civitai fetch, byte-exact)"
[[ -f "$TARGET/user/default/workflows/OFMTech_NSFW_Personal.json" ]] \
  || { echo "x personal workflow not installed"; exit 1; }
echo "  OFMTech_NSFW_Personal.json installed"

echo "=== boot + render gate ==="
( cd "$TARGET" && exec python3 main.py --port "$PORT" --disable-auto-launch \
    --output-directory "$OUT/render" ) > "$OUT/comfy-fresh.log" 2>&1 &
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
  --out "$OUT/gate" --drive-selector --selector-pick 0 2>>"$OUT/gate.err" | tail -5
GRC=$?
kill $CPID 2>/dev/null
[[ $GRC -eq 0 ]] || { echo "x render gate failed (see $OUT/gate)"; exit 1; }
echo "=== PASS: fresh-tree personal install + end-to-end render ==="
