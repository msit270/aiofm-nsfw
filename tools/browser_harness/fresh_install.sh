#!/usr/bin/env bash
# Run-3 DoD-1: fresh ComfyUI tree + ONE-LINE INSTALL FROM THE LIVE GIST.
#
# Differences from d_setup.sh / verify_buyer_path.sh, deliberately:
#   * the bootstrap comes from the LIVE gist URL (the buyer's actual command),
#     not a local copy of the file;
#   * the pack comes from LIVE HuggingFace (no AIOFM_PACK_URL mirror), so this
#     only makes sense AFTER the re-cut is published;
#   * target/ports are run-3's own: /workspace/comfy-fresh, 31950 (ComfyUI),
#     31951 (dead port handed to the installer so it never restarts anything —
#     the established guard from verify_buyer_path.sh:218).
#
# Stated deviations from a true fresh pod (recorded, not hidden):
#   * models/ hardlinked from the live install (the 193 GB download is
#     verified, not re-fetched);
#   * ComfyUI core is copied from the live install rather than a template image;
#   * same GPU, same driver, same venv as the dev instance.
set -uo pipefail

TARGET=/workspace/comfy-fresh
DEST=/workspace/fresh-pack
PORT=31950
DEAD=31951
LIVE_COMFY=/workspace/ComfyUI
GIST_URL="https://gist.githubusercontent.com/msit270/70256ac1ebf2760e10f78804862db528/raw/aiofm_setupnsfw.sh"
OUT=/workspace/nsfw-fix/results/run3/fresh
mkdir -p "$OUT"

echo "=== preconditions ==="
[[ -e "$TARGET" ]] && { echo "✗ $TARGET exists — delete deliberately first"; exit 2; }
for P in $PORT $DEAD; do
  curl -fsS --max-time 2 "http://127.0.0.1:$P/" >/dev/null 2>&1 && { echo "✗ something answers on $P"; exit 2; }
done
echo "  target absent, ports dead: OK"

echo "=== fresh tree (c_prepare pattern) ==="
mkdir -p "$TARGET"
rsync -a \
    --exclude '/models/' --exclude '/custom_nodes/' --exclude '/user/' \
    --exclude '/output/' --exclude '/input/' --exclude '/temp/' \
    --exclude '/.tmpdl/' --exclude '/.aiofm_expected_sizes.txt' \
    "$LIVE_COMFY"/ "$TARGET"/ || exit 1
mkdir -p "$TARGET/custom_nodes" "$TARGET/user" "$TARGET/output" "$TARGET/input" "$TARGET/temp"
cp -al "$LIVE_COMFY/models" "$TARGET/models" || exit 1
echo "  custom_nodes entries: $(ls -A "$TARGET/custom_nodes" | wc -l) (0 = empty)"
echo "  models: hardlinked ($(ls -A "$TARGET/models" | wc -l) dirs)"

echo "=== THE BUYER'S ONE-LINER, from the live gist ==="
echo "  bash <(wget -qO- $GIST_URL)"
t0=$SECONDS
env HF_TOKEN="$(tr -d '[:space:]' < /workspace/.hf_token)" \
    AIOFM_DEST="$DEST" \
    COMFYUI_DIR="$TARGET" \
    COMFYUI_PORT="$DEAD" \
    bash <(wget -qO- "$GIST_URL") 2>&1 | tee "$OUT/install.log"
rc=${PIPESTATUS[0]}
echo "--> installer exit $rc after $((SECONDS-t0))s" | tee -a "$OUT/install.log"
[[ $rc -eq 0 ]] || exit $rc

echo "=== boot the fresh ComfyUI on :$PORT ==="
cd "$TARGET" && nohup /venv/main/bin/python main.py \
    --disable-auto-launch --disable-xformers --port $PORT --listen 127.0.0.1 \
    --enable-cors-header > "$OUT/comfy-fresh.log" 2>&1 &
echo $! > "$OUT/comfy-fresh.pid"
for i in $(seq 1 60); do
  curl -fsS --max-time 3 "http://127.0.0.1:$PORT/system_stats" >/dev/null 2>&1 && break
  sleep 3
done
curl -fsS --max-time 3 "http://127.0.0.1:$PORT/system_stats" >/dev/null 2>&1 \
    || { echo "✗ fresh ComfyUI did not come up"; exit 1; }
echo "  up. object_info types: $(curl -s 127.0.0.1:$PORT/object_info | python3 -c 'import json,sys; print(len(json.load(sys.stdin)))')"
echo "=== ready for the browser gate ==="
