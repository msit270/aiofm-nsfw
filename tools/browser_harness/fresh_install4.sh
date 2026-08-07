#!/usr/bin/env bash
# Run-4 DoD: fresh ComfyUI tree + ONE-LINE INSTALL FROM THE LIVE GIST, with the
# BASE CHECKPOINT ABSENT so the new Civitai route runs for real.
#
# Differences from run-3's fresh_install.sh, all deliberate:
#   * SDXLNSFW.safetensors is NOT hardlinked into the fresh tree — the install
#     must fetch all 6.9 GB from civitai.com with the buyer's own API key, or
#     fail. That is the point of the run.
#   * dmd2_sdxl_4step_lora_fp16.safetensors and v1-5-pruned-emaonly-fp16 are
#     also withheld, to prove the install completes without the files the owner
#     is about to delete from the HF repo.
#   * own target/ports so nothing collides with run-3's tree or the live pod.
#
# Stated deviations from a true fresh pod (recorded, not hidden), inherited:
#   * the other models are hardlinked from the live install (that 193 GB
#     download is verified, not re-fetched);
#   * ComfyUI core is copied from the live install rather than a template image;
#   * same GPU, driver and venv as the dev instance.
set -uo pipefail

# All overridable so a re-run can use a fresh target/output and clobber
# nothing: the run-4 gate evidence lives in results/run4/fresh and re-running
# with defaults would overwrite install.log/comfy-fresh.log there.
TARGET="${FRESH_TARGET:-/workspace/comfy-fresh4}"
DEST="${FRESH_DEST:-/workspace/fresh-pack4}"
PORT="${FRESH_PORT:-31960}"
DEAD="${FRESH_DEAD:-31961}"
MPORT="${FRESH_MPORT:-31962}"
LIVE_COMFY=/workspace/ComfyUI
GIST_URL="https://gist.githubusercontent.com/msit270/70256ac1ebf2760e10f78804862db528/raw/aiofm_setupnsfw.sh"
OUT="${FRESH_OUT:-/workspace/nsfw-fix/results/run4/fresh}"
WITHHOLD=(
  "checkpoints/SDXLNSFW.safetensors"
  "diffusion_models/SDXLNSFW.safetensors"
  "loras/dmd2_sdxl_4step_lora_fp16.safetensors"
  "checkpoints/v1-5-pruned-emaonly-fp16.safetensors"
)
mkdir -p "$OUT"

echo "=== preconditions ==="
[[ -e "$TARGET" ]] && { echo "✗ $TARGET exists — delete deliberately first"; exit 2; }
for P in $PORT $DEAD $MPORT; do
  curl -fsS --max-time 2 "http://127.0.0.1:$P/" >/dev/null 2>&1 && { echo "✗ something answers on $P"; exit 2; }
done
[[ -s /workspace/.civitai_token ]] || { echo "✗ no /workspace/.civitai_token"; exit 2; }
echo "  target absent, ports dead, civitai key present: OK"

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
  [[ -e "$TARGET/models/$f" ]] && { echo "✗ could not withhold $f"; exit 2; }
  echo "  withheld: models/$f"
done
echo "  custom_nodes entries: $(ls -A "$TARGET/custom_nodes" | wc -l) (0 = empty)"
echo "  models: hardlinked ($(ls -A "$TARGET/models" | wc -l) dirs), 4 files withheld"

echo "=== THE BUYER'S ONE-LINER, from the live gist ==="
echo "  bash <(wget -qO- $GIST_URL)"
# Pre-publish mode (the pod's HF token is role:read, so the run-4 cut cannot be
# uploaded from here): AIOFM_PACK_URL is the bootstrap's OWN documented
# override. The gist bytes still come from the LIVE gist, and the models still
# come from LIVE HuggingFace. After the owner publishes, re-running without
# MIRROR_PACK is the full-live test.
MIRROR_PID=""
EXTRA_ENV=()
if [[ -n "${MIRROR_PACK:-}" ]]; then
  ( cd "$(dirname "$MIRROR_PACK")" && exec python3 -m http.server "$MPORT" --bind 127.0.0.1 ) >/dev/null 2>&1 &
  MIRROR_PID=$!
  sleep 1
  EXTRA_ENV+=( "AIOFM_PACK_URL=http://127.0.0.1:$MPORT/$(basename "$MIRROR_PACK")" )
  echo "  [pre-publish] pack served from local mirror: ${EXTRA_ENV[0]}"
  echo "  [pre-publish] sha256 $(sha256sum "$MIRROR_PACK" | cut -d' ' -f1)"
fi
t0=$SECONDS
env HF_TOKEN="$(tr -d '[:space:]' < /workspace/.hf_token)" \
    AIOFM_DEST="$DEST" \
    COMFYUI_DIR="$TARGET" \
    COMFYUI_PORT="$DEAD" \
    "${EXTRA_ENV[@]}" \
    bash <(wget -qO- "$GIST_URL") 2>&1 | tee "$OUT/install.log"
rc=${PIPESTATUS[0]}
[[ -n "$MIRROR_PID" ]] && kill "$MIRROR_PID" 2>/dev/null
echo "--> installer exit $rc after $((SECONDS-t0))s" | tee -a "$OUT/install.log"
[[ $rc -eq 0 ]] || exit $rc

echo "=== the Civitai route, verified on the installed bytes ==="
CK="$TARGET/models/checkpoints/SDXLNSFW.safetensors"
[[ -s "$CK" ]] || { echo "✗ checkpoint absent after a successful install"; exit 1; }
GOT="$(sha256sum "$CK" | cut -d' ' -f1)"
echo "  size   : $(stat -c %s "$CK")"
echo "  sha256 : $GOT"
[[ "$GOT" == d234c60d67cedfe69433e3934a459707c2cf43b30232d3db2becd10371d2220f ]] \
  || { echo "✗ installed checkpoint is not LUSTIFY GGWP V7"; exit 1; }
# diffusion_models/SDXLNSFW.safetensors is EXPECTED — the installer hardlinks
# it from the Civitai copy (0 extra bytes). Same inode proves it came from
# Civitai and not from the repo, which is the thing under test.
DIFF="$TARGET/models/diffusion_models/SDXLNSFW.safetensors"
[[ -e "$DIFF" ]] || { echo "✗ the diffusion_models mirror was not created"; exit 1; }
if [[ "$(stat -c %i "$CK")" == "$(stat -c %i "$DIFF")" ]]; then
  echo "  diffusion_models mirror: hardlink of the Civitai file (same inode, 0 extra bytes)"
else
  echo "  ✗ EXCLUSION LEAK: diffusion_models/SDXLNSFW.safetensors is a SEPARATE file — it came from the repo"; exit 1
fi
# These two must not arrive at all: they are excluded from the bulk pull and
# are scheduled for deletion from the HF repo.
for f in "${WITHHOLD[@]:2}"; do
  if [[ -e "$TARGET/models/$f" ]]; then
    echo "  ✗ EXCLUSION LEAK: models/$f arrived from the repo"; exit 1
  fi
  echo "  still absent (excluded): models/$f"
done

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
echo "=== boot log: packs that failed to import ==="
grep -icE "IMPORT FAILED|Cannot import" "$OUT/comfy-fresh.log" || true
echo "=== ready for the browser gate ==="
