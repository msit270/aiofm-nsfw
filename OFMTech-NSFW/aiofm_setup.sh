#!/bin/bash
# =============================================================
#  AIOFM · Character Animation v1.2
#  One-shot setup for a fresh pod. Run it once; it is safe to re-run.
#
#  This pack ships ONE workflow: "AIOFM Character Animation v1.2.json".
#  The script installs everything that workflow needs to open and run --
#
#    - the Wan 2.2 Animate 14B model, plus the VAE, CLIP vision and
#      text encoder it loads
#    - the five LoRAs the pipeline applies
#    - the pose and detection models (ViTPose, YOLO) and, at the end,
#      the RIFE and SAM2 weights that used to download mid-render
#    - every custom node pack the graph depends on, pinned to a known
#      revision, with their Python dependencies
#    - the workflow itself, into ComfyUI's own workflow list, so it is
#      there when you open the UI
#
#  PROFILE=video pulls only the files this workflow uses.
#  PROFILE=all (the default) also pulls the wider model library.
#
#  It verifies rather than assumes: downloads resume and are size-checked
#  against the manifest, ComfyUI core is held to a minimum version, and a
#  final pass confirms every node type the workflow references actually
#  registered -- reading that list out of the workflow rather than from a
#  hand-maintained list that can drift.
# =============================================================

set -e

# --- where this script is fetched from -------------------------------------
# Printed in two places: the HF_TOKEN message below, and the low-memory retry
# hint during downloads. Defined once so those two can never drift apart.
#
# Deliberately NOT pinned to a revision. A gist raw URL carrying a commit sha
# serves that exact revision forever, so a buyer who installs next month would
# fetch today's script no matter how many times the gist had been fixed. This
# form always serves the current file.
#
# It named aiofm_setupall.sh, which does not exist. That gist holds exactly two
# files -- aiofm_setupnsfw.sh and aiofm_setupvideo.sh -- confirmed against
# api.github.com/gists/70256ac1…, and the raw URL for aiofm_setupall.sh returns
# HTTP 404. Both places this URL is printed are recovery instructions given to a
# buyer who is already stuck: "no HF_TOKEN" and "retry with fewer workers". Both
# were handing them a command that pipes a 404 body into bash.
SETUP_URL="${SETUP_URL:-https://gist.githubusercontent.com/msit270/70256ac1ebf2760e10f78804862db528/raw/aiofm_setupnsfw.sh}"

# The pod image this pack is built and tested against. Printed at startup so it
# travels with every copy of the script.
VAST_TEMPLATE_URL="${VAST_TEMPLATE_URL:-https://cloud.vast.ai/?ref_id=638421&creator_id=638421&name=AIOFM%20ComfyUI}"

# --- HuggingFace token ---
if [[ -z "$HF_TOKEN" ]]; then
    if [[ -f /workspace/.hf_token ]]; then
        HF_TOKEN=$(cat /workspace/.hf_token | tr -d '[:space:]')
    else
        echo ""
        echo "=========================================="
        echo "  HF_TOKEN not found!"
        echo ""
        echo "  Run this in the terminal:"
        echo "  echo \"hf_yourtoken\" > /workspace/.hf_token"
        echo ""
        echo "  Then run this script again:"
        echo "  bash <(curl -sSL \"$SETUP_URL\")"
        echo "=========================================="
        exit 1
    fi
fi
export HF_TOKEN

COMFYUI_DIR="${COMFYUI_DIR:-/workspace/ComfyUI}"

# Where this script (and the rest of the delivered pack) lives. Hoisted to the
# top because three separate stages now need it: vendoring ComfyUI_INSTARAW,
# installing the workflow json, and deriving the node check from that json.
# Empty when the script is piped from curl rather than run from the pack.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd)" || SCRIPT_DIR=""
# Piped invocation -- `bash <(wget -qO- URL)` or `curl … | bash` -- leaves
# BASH_SOURCE pointing at /dev/fd/63, so SCRIPT_DIR resolves to /dev/fd and
# every "look beside the script" stage silently finds nothing: ComfyUI_INSTARAW
# is not vendored and the workflow is not installed, with no error. Detect it
# and say so, rather than completing and looking successful.
PIPED=0
case "$SCRIPT_DIR" in
    /dev/fd|/proc/*/fd|"") PIPED=1; SCRIPT_DIR="" ;;
esac

# The workflow files this pack ships, as a glob list. The NSFW image workflow
# is named OFMTech_NSFW.json, so an AIOFM*.json-only glob silently skipped it:
# it was neither installed into user/default/workflows nor fed to the
# workflow-derived node check, which is why that check never noticed the six
# missing packs.
WORKFLOW_GLOBS=("AIOFM*.json" "OFMTech*.json")

# Every shipped workflow json beside this script, one per line. Empty output
# and a non-zero status when there are none, so callers can test it directly.
workflow_files() {
    local dir="${1:-$SCRIPT_DIR}" g f found=1
    [[ -n "$dir" ]] || return 1
    for g in "${WORKFLOW_GLOBS[@]}"; do
        for f in "$dir"/$g; do
            [[ -f "$f" ]] || continue
            printf '%s\n' "$f"
            found=0
        done
    done
    return $found
}

# --- git must never block this script ---
# An unreachable, renamed or private repo makes git ask for a username on
# stdin. This script runs unattended on a fresh pod, so a prompt turns a clean
# failure into an indefinite hang with no output. Fail immediately instead.
# GIT_TERMINAL_PROMPT=0 covers the terminal prompt; a credential helper
# configured in the base image (credential.helper=manager and friends) ignores
# it and can still block, so helpers are disabled per-invocation in GIT_Q below.
export GIT_TERMINAL_PROMPT=0
# Clear any askpass helper inherited from the base image; leaving one set
# makes git report the helper's failure instead of the real cause.
unset GIT_ASKPASS SSH_ASKPASS
GIT_Q=(git -c credential.helper= -c core.askPass=)
# =============================================================
#  Output formatting, timing, download profiles
# =============================================================
# stdout is piped through tee, so -t 1 is false here. Use the real terminal.
# -w only checks permission bits; with no controlling terminal /dev/tty
# still passes it but fails to open (ENXIO). Actually try to open it.
if { true >/dev/tty; } 2>/dev/null; then TTY=/dev/tty; else TTY=""; fi
if [[ -n "$TTY" && -z "$NO_COLOR" ]]; then
    C_B=$'\033[1m'; C_G=$'\033[32m'; C_Y=$'\033[33m'
    C_R=$'\033[31m'; C_C=$'\033[36m'; C_0=$'\033[0m'
else
    C_B=""; C_G=""; C_Y=""; C_R=""; C_C=""; C_0=""
fi

T_START=$SECONDS
STAGE=0
WARNINGS=0
# stage count depends on which options are enabled
# Custom nodes are always installed (the workflow cannot load without them);
# PIN_NODES only decides whether they are pinned or left on their default
# branch, so it no longer adds or removes a stage.
# Eleven stages always run: Environment, Download accelerators, ComfyUI core
# version, Downloading models, Custom nodes (one of the pinned/unpinned pair),
# Custom node dependencies, Render-time models, Integrity check, ViTPose check,
# Workflow node check, ComfyUI restart.
#
# This read 10, which is where "[14/13]" came from. Two further errors sat on
# top of it: the Workflow stage was never counted at all, and SageAttention was
# counted whenever SAGE_INSTALL=1 even though its stage only runs when a build
# was actually started -- on a pod that already has it, it is counted and never
# runs. Those cancelled to -1 rather than to 0.
STAGES=11
[[ "${FIX_ORT:-1}"     == "1" ]] && STAGES=$((STAGES+1))
[[ "${PIN_FRONTEND:-1}" == "1" ]] && STAGES=$((STAGES+1))
# The Workflow stage runs when a workflow sits beside this script. That is
# knowable now, and it is the same test the stage itself uses.
workflow_files >/dev/null 2>&1 && STAGES=$((STAGES+1))
# SageAttention is NOT counted here. Whether its stage runs depends on whether
# a background build was started, which is not known until stage 2; STAGES is
# incremented there instead.

hms() { printf '%dm %02ds' $(( $1/60 )) $(( $1%60 )); }
human() {  # bytes -> MB/GB
    awk -v b="$1" 'BEGIN{
        if (b >= 1073741824) printf "%.1f GB", b/1073741824;
        else if (b >= 1048576) printf "%.0f MB", b/1048576;
        else printf "%.0f KB", b/1024 }'
}
stage() {
    STAGE=$((STAGE+1))
    # Backstop: a miscounted STAGES must never render as "[14/13]" to a buyer.
    # If a stage is ever added without updating the arithmetic above, the total
    # grows to meet it instead of the display going nonsensical.
    (( STAGE > STAGES )) && STAGES=$STAGE
    STAGE_T=$SECONDS
    printf '\n%s[%d/%d] %s%s\n' "$C_C$C_B" "$STAGE" "$STAGES" "$1" "$C_0"
}
stage_done() { printf '      %s✓ %s%s\n' "$C_G" "$(hms $((SECONDS-STAGE_T)))" "$C_0"; }
warn() { WARNINGS=$((WARNINGS+1)); printf '      %s! %s%s\n' "$C_Y" "$1" "$C_0"; }
ok()   { printf '      %s✓ %s%s\n' "$C_G" "$1" "$C_0"; }
info() { printf '      %s\n' "$1"; }
die()  { printf '\n%s✗ %s%s\n  log: %s\n' "$C_R$C_B" "$1" "$C_0" "$SETUP_LOG"; exit 1; }
trap 'printf "\n%s✗ Aborted at stage %d/%d%s\n  log: %s\n" "$C_R" "$STAGE" "$STAGES" "$C_0" "$SETUP_LOG"' ERR

# --- Profiles: pull everything, or only what one workflow needs ---
#   PROFILE=all   (default) — the whole pack, all 10 workflows
#   PROFILE=video — only the models the Wan video workflow uses
PROFILE="${PROFILE:-all}"
VIDEO_FILES="wan2.2_animate_14B_bf16.safetensors GlassRoot_D2.safetensors \
EchoVault_T9.safetensors IronSight_V7.safetensors SolarFlint_L2.safetensors \
VelvetRush_Q4.safetensors FrostByte_K7.safetensors PhantomWeave_R5.safetensors \
NovaMind_X1.safetensors vitpose_h_wholebody_model.onnx \
vitpose_h_wholebody_data.bin yolov10m.onnx"

want() {
    [[ "$PROFILE" == "all" ]] && return 0
    case " $(echo $VIDEO_FILES) " in *" $1 "*) return 0 ;; esac
    return 1
}

dir_size() { du -sb "$1" 2>/dev/null | cut -f1 || echo 0; }

# --- live progress bar, drawn on the real terminal (never into the log) ---
bar_draw() {   # $1=done bytes  $2=total bytes (0 = unknown)  $3=elapsed s
    [[ -n "$TTY" ]] || return 0
    local done=$1 total=$2 el=$3 width=34 filled pct rate eta line
    rate=$(( el > 0 ? done/el : 0 ))
    if (( total > 0 )); then
        pct=$(( done*100/total )); (( pct > 100 )) && pct=100
        filled=$(( pct*width/100 ))
        if (( rate > 0 && total > done )); then
            eta=$(hms $(( (total-done)/rate )))
        else
            eta="--"
        fi
        local fb="" eb=""
        (( filled > 0 ))       && fb=$(printf '█%.0s' $(seq 1 "$filled"))
        (( width-filled > 0 )) && eb=$(printf '░%.0s' $(seq 1 "$((width-filled))"))
        line=$(printf '  [%s%s] %3d%%  %s / %s  %s/s  ETA %s' \
            "$fb" "$eb" "$pct" "$(human $done)" "$(human $total)" \
            "$(human $rate)" "$eta")
    else
        line=$(printf '  %s downloaded  %s/s  %s elapsed' \
            "$(human $done)" "$(human $rate)" "$(hms $el)")
    fi
    printf '\r\033[K%s' "$line" > "$TTY"
}

# --- how many bytes are on disk for this download (incl. in-flight .incomplete) ---
mem_avail_gb() {
    awk '/^MemAvailable:/{printf "%d", $2/1048576; f=1} END{if(!f) print 999}' \
        /proc/meminfo 2>/dev/null || echo 999
}

dl_bytes_now() {
    local t=0 d
    for d in "$COMFYUI_DIR/models" "$COMFYUI_DIR/.cache"; do
        [[ -d "$d" ]] && t=$(( t + $(du -sb "$d" 2>/dev/null | cut -f1) ))
    done
    echo "$t"
}

# --- expected download size, asked of the Hub up front ---
repo_expected_bytes() {
    python3 - "$HF_REPO_ID" "$PROFILE" "$VIDEO_FILES" <<'PYEOF' 2>/dev/null || echo 0
import os, sys
try:
    from huggingface_hub import HfApi
    repo, profile, vf = sys.argv[1], sys.argv[2], sys.argv[3].split()
    info = HfApi().repo_info(repo, files_metadata=True,
                             token=os.environ.get("HF_TOKEN"))
    total = 0
    for f in info.siblings:
        if not f.rfilename.startswith("models/"):
            continue
        if profile != "all" and os.path.basename(f.rfilename) not in vf:
            continue
        total += (f.lfs.size if getattr(f, "lfs", None) else None) or f.size or 0
    print(total)
except Exception:
    print(0)
PYEOF
}

# Per-file expected sizes from the same API call shape as repo_expected_bytes,
# but kept per file instead of summed. Without this there is no way to tell a
# finished download from one that stopped half way: an interrupted wget leaves
# a large, non-empty, completely useless file, and every existence check in
# this script used to accept it.
MANIFEST=""
build_manifest() {
    # Deliberately NOT under $TMPDL: that directory is wiped just before the
    # integrity check, which is the one place the manifest matters most.
    MANIFEST="$COMFYUI_DIR/.aiofm_expected_sizes.txt"
    mkdir -p "$COMFYUI_DIR"
    [[ -s "$MANIFEST" ]] && return 0
    python3 - "$HF_REPO_ID" > "$MANIFEST" 2>/dev/null <<'PYEOF' || true
import os, sys
try:
    from huggingface_hub import HfApi
    info = HfApi().repo_info(sys.argv[1], files_metadata=True,
                             token=os.environ.get("HF_TOKEN"))
    for f in info.siblings:
        size = (f.lfs.size if getattr(f, "lfs", None) else None) or f.size or 0
        if size:
            print(os.path.basename(f.rfilename), size)
except Exception:
    pass
PYEOF
    [[ -s "$MANIFEST" ]] || return 1
    return 0
}

# Expected byte count for a file, or empty if unknown. Unknown must always mean
# "cannot verify", never "assume bad" -- a buyer whose network blocks the HF
# API still needs the install to complete.
expected_size() {
    # ONE line out, always. The manifest legitimately lists a basename more than
    # once when the same file is published under two model directories --
    # SDXLNSFW.safetensors appears twice, for checkpoints/ and
    # diffusion_models/. Returning both made `have`/`exp` two-line strings, and
    # the integrity check's arithmetic then died with
    #   ((: 6938099634\n6938099634: syntax error in expression
    # and reported a perfectly good 6.9 GB model as OVER-SIZE. Caught by the
    # clean-install test, not by reading the code.
    #
    # Duplicates are only safe to collapse if they agree; if they ever disagree
    # that is a manifest bug and guessing which one is right would be worse than
    # saying so.
    [[ -n "$MANIFEST" && -s "$MANIFEST" ]] || return 1
    awk -v n="$1" '
        $1==n { if (found && $2 != v) { conflict=1 } ; v=$2 ; found=1 }
        END {
            if (!found) exit 1
            if (conflict) { print "conflict" > "/dev/stderr" ; exit 1 }
            print v
        }' "$MANIFEST"
}

# Is a local file present AND the size it should be?
file_complete() {
    local path="$1" fname exp have
    fname="$(basename "$path")"
    [[ -s "$path" ]] || return 1
    exp="$(expected_size "$fname")" || return 0   # unverifiable: accept
    have="$(stat -c %s "$path" 2>/dev/null || echo 0)"
    [[ "$have" == "$exp" ]]
}

SETUP_LOG="${SETUP_LOG:-/workspace/setup.log}"
exec > >(tee -a "$SETUP_LOG") 2>&1
REPO="https://huggingface.co/msit270/AIOFM-Pack/resolve/main/models"
HF_REPO_ID="msit270/AIOFM-Pack"
TMPDL="$COMFYUI_DIR/.tmpdl"

mkdir -p "$COMFYUI_DIR"

echo "=========================================="
echo "  AIOFM · OFM Tech NSFW — setup"
echo "  ComfyUI dir: $COMFYUI_DIR"
echo "=========================================="
# printf '%s' rather than echo, because the URL contains %20 and a printf
# FORMAT string would read that as a conversion spec. The variable is
# double-quoted so the two & characters stay literal -- unquoted, the first &
# would end the command and background it.
printf '  Built for this template:\n  %s\n' "$VAST_TEMPLATE_URL"
echo ""
stage "Environment"
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader \
    2>/dev/null | sed "s/^/    GPU: /" || echo "    GPU: nvidia-smi unavailable"
python3 -c "import torch;print('    torch:',torch.__version__,'| cuda:',torch.version.cuda)" \
    2>/dev/null || echo "    torch: not found"
echo ""
echo "      disk before:"
df -h "$COMFYUI_DIR" | tail -1
echo ""

# =============================================================
#  Download accelerators
#  hf_transfer  — multi-connection downloads for regular LFS files
#  hf_xet       — for Xet-backed repos
#  Both install standalone and do NOT touch huggingface_hub,
#  so the ComfyUI environment stays intact.
# =============================================================
stage "Download accelerators"
pip install -q hf_transfer hf_xet 2>/dev/null || true
export HF_HUB_ENABLE_HF_TRANSFER="${HF_TURBO:-1}"
export HF_XET_HIGH_PERFORMANCE=1

# --- Pick worker count based on available RAM ---
# hf_transfer buffers file chunks in RAM. Too many workers on a small
# pod means an OOM kill and a stopped instance.
RAM_GB="$(free -g 2>/dev/null | awk '/^Mem:/{print $2}')"
[[ -z "$RAM_GB" ]] && RAM_GB=8
# hf_transfer buffers multi-GB chunks per worker. Measured: 8 workers on a
# 128GB pod pushed it into swap. These tiers are deliberately cautious —
# the link, not the worker count, is the bottleneck above ~4 workers anyway.
if [[ -z "$HF_WORKERS" ]]; then
    if   [[ "$RAM_GB" -ge 500 ]]; then HF_WORKERS=12
    elif [[ "$RAM_GB" -ge 200 ]]; then HF_WORKERS=8
    elif [[ "$RAM_GB" -ge 100 ]]; then HF_WORKERS=4
    elif [[ "$RAM_GB" -ge 48  ]]; then HF_WORKERS=3
    else                               HF_WORKERS=2
    fi
fi
echo "      RAM: ${RAM_GB}G total, $(mem_avail_gb)G available  ->  workers: $HF_WORKERS"

HF_CMD=""
if command -v hf >/dev/null 2>&1; then
    HF_CMD="hf"
elif command -v huggingface-cli >/dev/null 2>&1; then
    HF_CMD="huggingface-cli"
fi

# huggingface_hub < 0.23 writes to BOTH the cache and local-dir, i.e.
# twice the disk. Disable bulk mode on those versions.
HF_VER="$(python3 -c 'import huggingface_hub as h; print(h.__version__)' 2>/dev/null || echo 0)"
version_ge() {
    [ "$(printf '%s\n%s\n' "$2" "$1" | sort -V | head -1)" = "$2" ]
}
if [[ -n "$HF_CMD" ]] && version_ge "$HF_VER" "0.23.0"; then
    BULK_OK=1
else
    BULK_OK=0
    warn "huggingface_hub $HF_VER is too old — bulk mode off, falling back to wget"
fi

# =============================================================
#  SageAttention — attention speedup (Wan / Flux)
#  Tries a prebuilt wheel from AIOFM-Pack first (seconds), otherwise
#  builds from source (10-20 min) IN THE BACKGROUND, in parallel with
#  the model download.  Disable with: SAGE_INSTALL=0
# =============================================================
WHEELDIR="$COMFYUI_DIR/.wheels"
SAGE_LOG="/tmp/sage_install.log"
SAGE_PID=""
MAX_JOBS="$(nproc 2>/dev/null || echo 4)"
[[ "$MAX_JOBS" -gt 8 ]] && MAX_JOBS=8
export MAX_JOBS

if [[ "${SAGE_INSTALL:-1}" == "1" ]]; then
    if python3 -c 'import sageattention' 2>/dev/null; then
        ok "SageAttention already installed"
    else
        info "SageAttention: building in background (log: $SAGE_LOG)"
        (
            set +e
            mkdir -p "$WHEELDIR"
            # IMPORTANT: never blindly upgrade triton — its version is tied
            # to torch, and a mismatch breaks torch.compile.
            python3 -c 'import triton' 2>/dev/null || pip install -q triton

            # 1) prebuilt wheel from the mirror — fast path
            if [[ "$BULK_OK" == "1" ]]; then
                "$HF_CMD" download "$HF_REPO_ID" --include "wheels/*" \
                    --local-dir "$WHEELDIR" >/dev/null 2>&1
            fi
            W="$(find "$WHEELDIR" -name 'sageattention*.whl' 2>/dev/null | head -1)"

            if [[ -n "$W" ]] && pip install -q "$W"; then
                echo "installed from prebuilt wheel: $(basename "$W")"
            else
                # 2) build from source. pip wheel (not install) so the .whl
                #    survives and can be uploaded to the mirror.
                echo "no prebuilt wheel — building from source (MAX_JOBS=$MAX_JOBS)..."
                if pip wheel -q --no-deps \
                        git+https://github.com/thu-ml/SageAttention.git \
                        -w "$WHEELDIR"; then
                    pip install -q "$WHEELDIR"/sageattention*.whl
                fi
            fi
            python3 -c 'import sageattention; print("import OK")'
        ) > "$SAGE_LOG" 2>&1 &
        SAGE_PID=$!
        # Its stage runs only because this build was started, so count it now.
        STAGES=$((STAGES+1))
    fi
fi

# =============================================================
#  onnxruntime-gpu MUST match torch's CUDA major version.
#  From 1.27 onward the PyPI package is built for CUDA 13, while torch
#  here is cu12x. On a mismatch CUDAExecutionProvider silently falls back
#  to CPU and pose detection (ViTPose-H) runs on the processor — very slow.
#  Detected and repaired automatically. Disable with: FIX_ORT=0
# =============================================================
if [[ "${FIX_ORT:-1}" == "1" ]]; then
    echo ""
    stage "onnxruntime / CUDA"
    ORT_STATUS="$(python3 - <<'PYEOF' 2>/dev/null || echo "unknown"
try:
    import torch, onnxruntime as ort
except Exception:
    print("missing"); raise SystemExit
tmaj = int((torch.version.cuda or "0").split(".")[0])
omaj, omin = (list(map(int, ort.__version__.split(".")[:2])) + [0, 0])[:2]
ort_cuda = 13 if (omaj, omin) >= (1, 27) else 12
print("ok" if ort_cuda == tmaj else f"mismatch {ort.__version__} cuda{ort_cuda} vs torch cuda{tmaj}")
PYEOF
)"
    case "$ORT_STATUS" in
        ok)      ok "onnxruntime matches torch CUDA" ;;
        missing) info "onnxruntime not installed — installing the CUDA 12 build"
                 pip install -q "onnxruntime-gpu<1.27" ;;
        mismatch*) echo "    $ORT_STATUS"
                 warn "reinstalling for CUDA 12 (otherwise ViTPose runs on CPU)"
                 pip uninstall -y -q onnxruntime onnxruntime-gpu 2>/dev/null
                 pip install -q "onnxruntime-gpu<1.27" ;;
        *)       warn "could not determine onnxruntime/CUDA state — skipping" ;;
    esac

    # torch ships the CUDA libraries in site-packages/nvidia/*/lib, but
    # onnxruntime doesn't look there -> libcublasLt.so.12 not found -> CPU
    # fallback. Register those paths system-wide so it works no matter how
    # ComfyUI gets launched.
    if python3 -c 'import nvidia' 2>/dev/null; then
        python3 - > /etc/ld.so.conf.d/nvidia-python.conf 2>/dev/null <<'PYEOF'
import os, nvidia
# nvidia is a namespace package (no __init__.py), so __file__ is None.
# __path__ is the correct source of directories.
bases = list(getattr(nvidia, "__path__", []))
if not bases and getattr(nvidia, "__file__", None):
    bases = [os.path.dirname(nvidia.__file__)]
seen = set()
for b in bases:
    for d in sorted(os.listdir(b)):
        lib = os.path.join(b, d, "lib")
        if os.path.isdir(lib) and lib not in seen:
            seen.add(lib)
            print(lib)
PYEOF
        if ldconfig 2>/dev/null; then
            ok "CUDA library paths registered (ldconfig)"
        else
            warn "ldconfig unavailable — exporting LD_LIBRARY_PATH instead"
            LD_LIBRARY_PATH="$(tr '\n' ':' < /etc/ld.so.conf.d/nvidia-python.conf)$LD_LIBRARY_PATH"
            export LD_LIBRARY_PATH
        fi
    fi
fi

# =============================================================
#  ComfyUI frontend version
#
#  This script does not install ComfyUI itself — it uses whatever the pod
#  image ships, and the image decides the frontend version. That was harmless
#  while the workflow was a flat graph. It is not harmless now: the graph is
#  built from subgraphs with promoted ("exposed") widgets, and that is the
#  exact feature area the frontend has been regressing in.
#
#  Known-bad on 1.47.x, all open upstream at the time of writing:
#    #14536  exposed-widget visibility toggles non-functional
#    #14495  edits to a promoted STRING widget are not written back to the
#            interior node — the buyer changes the prompt and it does nothing
#    #14488  null entries in a subgraph host's widgets_values load as undefined
#
#  1.39.19 is the version this workflow was authored and tested against, and
#  the one the exposed widgets are known to behave correctly on. Pin it so a
#  buyer gets that regardless of which pod image they rented.
#
#  Minimum for the features this graph needs: subgraphs require >= 1.24.3,
#  the Edit Subgraph Widgets parameter panel requires >= 1.28.7 (first shipped
#  with ComfyUI 0.3.66). Do not lower the pin past 1.28.7.
#
#  If the pod's ComfyUI pins a newer frontend in its own requirements.txt, it
#  logs a startup warning and carries on — it does not hard-fail. The warning
#  is expected and is not a broken install; only a missing package is fatal.
#
#  Disable with: PIN_FRONTEND=0     Override with: FRONTEND_VERSION=x.y.z
# =============================================================
# =============================================================
#  ComfyUI core version
#
#  Every node pack here is pinned to an exact commit, but ComfyUI core is
#  whatever the pod image happened to ship. That is the one moving part left
#  in the install, and it is the one most likely to change under a buyer.
#
#  This does NOT clone or downgrade core. The buyer rented the pod; silently
#  rewriting its ComfyUI is more likely to break their machine than to fix
#  anything, and a checkout would fight the image's own updater. Instead:
#  report what is installed, hard-fail below the minimum the graph needs, and
#  warn on anything not actually validated, so a support conversation starts
#  with a version number instead of a guess.
#
#  MIN 0.3.66 is a real floor, not a guess: this graph is built from subgraphs
#  and the Edit Subgraph Widgets panel, which needs frontend >= 1.28.7, first
#  shipped with core 0.3.66. Below that the graph opens but the control panel
#  does not work.
#
#  The NSFW image workflow raises that floor to 0.3.70. Its #614
#  PrimitiveBoolean carries cnr_id "comfy-core", ver "0.3.70" -- the highest
#  core version anywhere in that file, and therefore the earliest core it can
#  have been authored against.
#
#  Sanity-checked against the pod that rendered it, because a version floor
#  that rejects a working install is worse than no floor at all: that pod runs
#  core 0.15.1, `sort -V` ranks 0.15.1 above 0.3.70 (15 > 3 componentwise), and
#  PrimitiveBoolean is registered there. So the raise does not lock out the
#  current release line.
#
#  Override the validated version with: COMFY_VALIDATED=x.y.z
# =============================================================
COMFY_MIN="0.3.70"
COMFY_VALIDATED="${COMFY_VALIDATED:-0.15.1}"
echo ""
stage "ComfyUI core version"
COMFY_VER="$(python3 -c "
import re,sys
try:
    src = open('$COMFYUI_DIR/comfyui_version.py').read()
    print(re.search(r'__version__\s*=\s*[\"\']([^\"\']+)', src).group(1))
except Exception:
    sys.exit(1)
" 2>/dev/null)" || COMFY_VER=""
if [[ -z "$COMFY_VER" ]]; then
    COMFY_VER="$(grep -m1 '^version' "$COMFYUI_DIR/pyproject.toml" 2>/dev/null \
                 | sed 's/.*"\(.*\)".*/\1/')"
fi
COMFY_SHA="$(cd "$COMFYUI_DIR" 2>/dev/null && "${GIT_Q[@]}" rev-parse --short HEAD 2>/dev/null)" || COMFY_SHA=""

if [[ -z "$COMFY_VER" ]]; then
    warn "could not read ComfyUI core version from $COMFYUI_DIR"
    COMFY_STATUS="unknown"
elif ! version_ge "$COMFY_VER" "$COMFY_MIN"; then
    # Below the floor the control panel silently does not work, which reads to
    # a buyer as a broken product. Better to stop here with the reason.
    die "ComfyUI core $COMFY_VER is below the minimum $COMFY_MIN this workflow needs.
  The graph uses subgraphs and the Edit Subgraph Widgets panel, which need
  core >= $COMFY_MIN. Update ComfyUI on this pod and re-run setup."
elif [[ "$COMFY_VER" == "$COMFY_VALIDATED" ]]; then
    ok "ComfyUI core $COMFY_VER${COMFY_SHA:+ @ $COMFY_SHA} (validated)"
    COMFY_STATUS="$COMFY_VER validated"
else
    warn "ComfyUI core is $COMFY_VER${COMFY_SHA:+ @ $COMFY_SHA}; this pack was validated on $COMFY_VALIDATED"
    info "above the $COMFY_MIN minimum, so it should work — but it is untested here."
    info "if anything misbehaves, quote this version first."
    COMFY_STATUS="$COMFY_VER (validated on $COMFY_VALIDATED)"
fi

# --- CLIPLoader `device` capability — the black-face fix depends on it -------
#
# The shipped workflow sets CLIPLoader device="cpu" on the Z-Image text encoder
# (node 620:110; commit 7ce1539 in the pack's history). That input is OPTIONAL
# in ComfyUI, so on a core that predates it (added upstream in v0.3.11,
# 5cbf7978) the value is silently dropped at load — no error, no red node — and
# the buyer renders the broken configuration while believing they have the fix.
# A version floor alone can't catch a modified or partially-updated tree, so
# assert the capability itself in the source that will run.
if ! python3 - "$COMFYUI_DIR/nodes.py" <<'PYEOF'
import re, sys
try:
    src = open(sys.argv[1], encoding="utf-8").read()
except Exception as e:
    print("      could not read nodes.py: %s" % e); sys.exit(1)
m = re.search(r'class CLIPLoader\b.*?(?=\nclass\s)', src, re.S)
sys.exit(0 if (m and '"device"' in m.group(0)) else 1)
PYEOF
then
    die "this ComfyUI's CLIPLoader has no 'device' input ($COMFYUI_DIR/nodes.py).
  The workflow sets device=\"cpu\" on the Z-Image text encoder (node 620:110) —
  the fix for the black-face / MaskBoundingBox+ crash. Because the input is
  optional, an older core SILENTLY DROPS the value and you would render the
  broken configuration believing you have the fix.
  Update ComfyUI core (the input exists from v0.3.11; this pack is validated
  on $COMFY_VALIDATED) and re-run setup."
fi
ok "CLIPLoader supports the 'device' input (black-face fix will apply)"

FRONTEND_VERSION="${FRONTEND_VERSION:-1.39.19}"
if [[ "${PIN_FRONTEND:-1}" == "1" ]]; then
    echo ""
    stage "ComfyUI frontend (pinned $FRONTEND_VERSION)"
    FE_BEFORE="$(python3 -c 'import importlib.metadata as m; print(m.version("comfyui-frontend-package"))' 2>/dev/null || echo "none")"
    if [[ "$FE_BEFORE" == "$FRONTEND_VERSION" ]]; then
        ok "comfyui-frontend-package already $FRONTEND_VERSION"
        FE_STATUS="pinned $FRONTEND_VERSION"
    elif pip install -q "comfyui-frontend-package==$FRONTEND_VERSION" 2>/dev/null; then
        FE_AFTER="$(python3 -c 'import importlib.metadata as m; print(m.version("comfyui-frontend-package"))' 2>/dev/null || echo "unknown")"
        if [[ "$FE_AFTER" == "$FRONTEND_VERSION" ]]; then
            ok "comfyui-frontend-package $FE_BEFORE -> $FRONTEND_VERSION"
            FE_STATUS="pinned $FRONTEND_VERSION"
        else
            warn "frontend pin reported success but version is $FE_AFTER"
            FE_STATUS="$FE_AFTER (pin did not take)"
        fi
    else
        # Not fatal. A wrong frontend still loads the workflow; the exposed
        # widgets are what degrade. Say so plainly rather than aborting a
        # setup that is otherwise complete.
        warn "could not install comfyui-frontend-package==$FRONTEND_VERSION (staying on $FE_BEFORE)"
        printf '        subgraph widgets may misbehave — see the comment above this stage\n'
        FE_STATUS="$FE_BEFORE (wanted $FRONTEND_VERSION)"
    fi
else
    FE_STATUS="$(python3 -c 'import importlib.metadata as m; print(m.version("comfyui-frontend-package"))' 2>/dev/null || echo "unknown") (PIN_FRONTEND=0)"
fi

# =============================================================
#  BULK PULL — the whole repo in one parallel download.
#  hf download verifies each file's checksum, so truncated or corrupt
#  models can't get through. If it fails, the wget path below takes over.
# =============================================================
stage "Downloading models ($HF_REPO_ID, profile: $PROFILE)"
SIZE_BEFORE=$(dir_size "$COMFYUI_DIR/models")
BULK_FAILED=0
# Built before the branch, not inside it: the wget/curl fallback path below
# needs per-file sizes to resume just as much as the bulk path does.
build_manifest || info "per-file sizes unavailable — resume and size checks disabled"

if [[ "$BULK_OK" == "1" ]]; then
    INC=(--include "models/*")
    if [[ "$PROFILE" != "all" ]]; then
        INC=()
        for f in $VIDEO_FILES; do INC+=(--include "models/**/$f"); done
    fi

    info "asking the Hub how much there is to fetch..."
    EXPECTED=$(repo_expected_bytes)
    HAVE_START=$(dl_bytes_now)
    if (( EXPECTED > 0 )); then
        REMAIN=$(( EXPECTED - HAVE_START )); (( REMAIN < 0 )) && REMAIN=0
        info "$(human $EXPECTED) total, $(human $REMAIN) still to download"
    else
        info "size unknown — showing raw progress"
    fi

    DL_LOG=$(mktemp)
    ( "$HF_CMD" download "$HF_REPO_ID" "${INC[@]}" \
        --local-dir "$COMFYUI_DIR" \
        --max-workers "$HF_WORKERS" ) > "$DL_LOG" 2>&1 &
    DL_PID=$!

    DL_T0=$SECONDS
    MEM_WARNED=0
    if [[ -n "$TTY" ]]; then
        LAST_LOG=0
        while kill -0 "$DL_PID" 2>/dev/null; do
            NOW=$(dl_bytes_now)
            DONE=$(( NOW - HAVE_START )); (( DONE < 0 )) && DONE=0
            bar_draw "$DONE" "$EXPECTED" "$(( SECONDS - DL_T0 ))"
            # watchdog: warn once if the pod is about to start swapping
            AVAIL=$(mem_avail_gb)
            if (( AVAIL < 6 && MEM_WARNED == 0 )); then
                MEM_WARNED=1
                printf '\r\033[K' > "$TTY"
                warn "only ${AVAIL}GB RAM available — hf_transfer is using too much"
                info "if this run fails, retry with fewer parallel workers:"
                info "  HF_WORKERS=2 HF_TURBO=0 bash <(curl -sSL \"$SETUP_URL\")"
            fi
            # a line into the log every 30s so the file stays useful
            if (( SECONDS - LAST_LOG >= 30 )); then
                LAST_LOG=$SECONDS
                printf '      %s downloaded (%s elapsed)\n' \
                    "$(human $DONE)" "$(hms $((SECONDS-DL_T0)))"
            fi
            sleep 1
        done
        printf '\r\033[K' > "$TTY"
    fi

    wait "$DL_PID" || BULK_FAILED=1
    DL_EL=$(( SECONDS - DL_T0 )); (( DL_EL < 1 )) && DL_EL=1
    DL_GOT=$(( $(dl_bytes_now) - HAVE_START )); (( DL_GOT < 0 )) && DL_GOT=0
    if [[ -n "$TTY" ]]; then
        bar_draw "$DL_GOT" "$EXPECTED" "$DL_EL"
        printf '\n' > "$TTY"
    fi
    if (( BULK_FAILED )); then
        warn "bulk pull failed — falling back to wget"
        tail -5 "$DL_LOG" | sed 's/^/      /'
    elif (( DL_GOT > 0 )); then
        ok "pulled $(human $DL_GOT) in $(hms $DL_EL) (~$(human $((DL_GOT/DL_EL)))/s)"
    else
        ok "already up to date — nothing to download"
    fi
    rm -f "$DL_LOG"
else
    info "bulk mode unavailable — using wget"
fi

# --- Pull from a third-party repo via hf (fast), flattening the files ---
hf_pull_flat() {
    local repo="$1" pat="$2" dest="$3"
    [[ "$BULK_OK" == "1" ]] || return 1
    mkdir -p "$dest" "$TMPDL"
    local tmp
    tmp="$TMPDL/$(echo "$repo" | tr '/' '_')"
    rm -rf "$tmp"
    if "$HF_CMD" download "$repo" --include "$pat" \
            --local-dir "$tmp" --max-workers "$HF_WORKERS" >/dev/null 2>&1; then
        # mv within one filesystem is an instant rename, not a copy
        find "$tmp" -type f ! -path "*/.cache/*" -exec mv -n {} "$dest"/ \; 2>/dev/null || true
        rm -rf "$tmp"
        return 0
    fi
    rm -rf "$tmp"
    return 1
}

# --- One file from the private AIOFM-Pack mirror ---
dl() {
    local url="$1"
    local dir="$2"
    local fname
    fname="$(basename "$url")"
    local sub="${dir##*/models/}"
    mkdir -p "$dir"
    local exp have
    exp="$(expected_size "$fname")" || exp=""
    if [[ -s "$dir/$fname" ]]; then
        if [[ -z "$exp" ]]; then
            return 0                       # nothing to check against
        fi
        have="$(stat -c %s "$dir/$fname" 2>/dev/null || echo 0)"
        if [[ "$have" == "$exp" ]]; then
            return 0
        fi
        if [[ "$have" -gt "$exp" ]]; then
            warn "$fname is larger than expected ($have vs $exp) — refetching"
            rm -f "$dir/$fname"
        else
            # The common case after a dropped connection or a killed pod.
            info "resuming $fname ($(human $have) of $(human $exp))"
        fi
    fi
    want "$fname" || return 0
    [[ -s "$dir/$fname" ]] || echo "    get:  $fname"
    # curl -C - rather than wget -c: resuming and writing to an explicit
    # output path are documented as not composing in wget, and the whole
    # point here is to resume into the final path.
    if curl -fL --retry 5 --retry-delay 3 --retry-connrefused \
            -H "Authorization: Bearer $HF_TOKEN" \
            -C - -o "$dir/$fname" "$REPO/$sub/$fname" 2>/dev/null; then
        if [[ -n "$exp" ]]; then
            have="$(stat -c %s "$dir/$fname" 2>/dev/null || echo 0)"
            if [[ "$have" != "$exp" ]]; then
                rm -f "$dir/$fname"
                warn "size mismatch after download: $fname ($have, wanted $exp)"
                return 0
            fi
        fi
    else
        # Leave the partial file in place; the next run resumes it. Deleting
        # it was the old behaviour and it threw away good bytes.
        warn "failed: $fname (partial kept for resume)"
    fi
}

# --- One file from a public repo by direct URL ---
dl_public() {
    local url="$1"
    local dir="$2"
    local fname
    fname="$(basename "$url")"
    mkdir -p "$dir"
    if [[ -s "$dir/$fname" ]]; then
        return 0
    fi
    want "$fname" || return 0
    echo "    get:  $fname"
    wget --show-progress -q -O "$dir/$fname" "$url" \
         || { rm -f "$dir/$fname"; warn "failed: $fname"; }
}

# ============================================
# models/detection  (public repos — pulled via hf, which is faster)
# ============================================
echo ">>> models/detection"
hf_pull_flat "Kijai/vitpose_comfy" "onnx/vitpose_h_wholebody*" \
             "$COMFYUI_DIR/models/detection" || true
hf_pull_flat "Wan-AI/Wan2.2-Animate-14B" "process_checkpoint/det/yolov10m.onnx" \
             "$COMFYUI_DIR/models/detection" || true
dl_public "https://huggingface.co/Kijai/vitpose_comfy/resolve/main/onnx/vitpose_h_wholebody_data.bin" "$COMFYUI_DIR/models/detection"
dl_public "https://huggingface.co/Kijai/vitpose_comfy/resolve/main/onnx/vitpose_h_wholebody_model.onnx" "$COMFYUI_DIR/models/detection"
dl_public "https://huggingface.co/Wan-AI/Wan2.2-Animate-14B/resolve/main/process_checkpoint/det/yolov10m.onnx" "$COMFYUI_DIR/models/detection"

# ============================================
# models/checkpoints
# ============================================
echo ">>> models/checkpoints"
dl "$REPO/SDXLNSFW.safetensors" "$COMFYUI_DIR/models/checkpoints"

# ============================================
# models/clip_vision
# ============================================
echo ">>> models/clip_vision"
dl "$REPO/IronSight_V7.safetensors" "$COMFYUI_DIR/models/clip_vision"

# ============================================
# models/diffusion_models
# ============================================
echo ">>> models/diffusion_models"
dl "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/diffusion_models/wan2.2_animate_14B_bf16.safetensors" "$COMFYUI_DIR/models/diffusion_models"
dl "$REPO/flux-2.safetensors" "$COMFYUI_DIR/models/diffusion_models"
dl "$REPO/flux4b.safetensors" "$COMFYUI_DIR/models/diffusion_models"
dl "$REPO/High.safetensors" "$COMFYUI_DIR/models/diffusion_models"
dl "$REPO/HyperFleshUltrav4.safetensors" "$COMFYUI_DIR/models/diffusion_models"
dl "$REPO/Low.safetensors" "$COMFYUI_DIR/models/diffusion_models"
dl "$REPO/Z-TurboSkinForge.safetensors" "$COMFYUI_DIR/models/diffusion_models"
dl "$REPO/zimage.safetensors" "$COMFYUI_DIR/models/diffusion_models"

# --- SDXLNSFW is needed in both checkpoints and diffusion_models.
#     A hardlink instead of a second download: 0 bytes, 0 seconds. ---
SDXL_CKPT="$COMFYUI_DIR/models/checkpoints/SDXLNSFW.safetensors"
SDXL_DIFF="$COMFYUI_DIR/models/diffusion_models/SDXLNSFW.safetensors"
if [[ -s "$SDXL_CKPT" && ! -s "$SDXL_DIFF" ]]; then
    ln "$SDXL_CKPT" "$SDXL_DIFF" 2>/dev/null || cp "$SDXL_CKPT" "$SDXL_DIFF"
    echo "    link: SDXLNSFW.safetensors -> diffusion_models"
elif [[ -s "$SDXL_DIFF" && ! -s "$SDXL_CKPT" ]]; then
    ln "$SDXL_DIFF" "$SDXL_CKPT" 2>/dev/null || cp "$SDXL_DIFF" "$SDXL_CKPT"
    echo "    link: SDXLNSFW.safetensors -> checkpoints"
elif [[ ! -s "$SDXL_CKPT" && ! -s "$SDXL_DIFF" ]]; then
    dl "$REPO/SDXLNSFW.safetensors" "$COMFYUI_DIR/models/diffusion_models"
fi

# ============================================
# models/loras
# ============================================
echo ">>> models/loras"
dl "$REPO/DetailedNipples.safetensors" "$COMFYUI_DIR/models/loras"
# --- 4-step speed LoRA ---
# NOT DMD2. tianweiy/DMD2 is cc-by-nc-4.0 (verified against the HF API), and it
# was loaded twice on the live render path of a product being sold. Replaced
# with TDD (RED-AIGC), Apache-2.0 -- the cleanest licence of the five legal
# candidates tested, with no RAIL use restrictions and no flow-down. Chosen on a
# measurement, not a benchmark: of the legal options it retains the most
# high-frequency skin detail, which is what this product sells. See RESULTS R19.
dl_public "https://huggingface.co/RED-AIGC/TDD/resolve/main/sdxl_tdd_lora_weights.safetensors" "$COMFYUI_DIR/models/loras"
dl "$REPO/FrostByte_K7.safetensors" "$COMFYUI_DIR/models/loras"
dl "$REPO/NovaMind_X1.safetensors" "$COMFYUI_DIR/models/loras"
dl "$REPO/PhantomWeave_R5.safetensors" "$COMFYUI_DIR/models/loras"
dl "$REPO/primary_net_v2.safetensors" "$COMFYUI_DIR/models/loras"
dl "$REPO/SolarFlint_L2.safetensors" "$COMFYUI_DIR/models/loras"
dl "$REPO/VelvetPores_Flux.safetensors" "$COMFYUI_DIR/models/loras"
dl "$REPO/VelvetRush_Q4.safetensors" "$COMFYUI_DIR/models/loras"
dl "$REPO/x_gen_weights.safetensors" "$COMFYUI_DIR/models/loras"

# ============================================
# models/sam3
# ============================================
echo ">>> models/sam3"
dl "$REPO/sam3.pt" "$COMFYUI_DIR/models/sam3"

# ============================================
# models/text_encoders
# ============================================
echo ">>> models/text_encoders"
dl "$REPO/clip_l.safetensors" "$COMFYUI_DIR/models/text_encoders"
dl "$REPO/EchoVault_T9.safetensors" "$COMFYUI_DIR/models/text_encoders"
dl "$REPO/qwen.safetensors" "$COMFYUI_DIR/models/text_encoders"
dl "$REPO/qwen-4b-zimage-heretic-q8.gguf" "$COMFYUI_DIR/models/text_encoders"
dl "$REPO/TitanFP8.safetensors" "$COMFYUI_DIR/models/text_encoders"
dl "$REPO/umt5.safetensors" "$COMFYUI_DIR/models/text_encoders"

# ============================================
# models/ultralytics
# ============================================
echo ">>> models/ultralytics"
dl "$REPO/lips_v1.pt" "$COMFYUI_DIR/models/ultralytics"
dl "$REPO/nipple.pt" "$COMFYUI_DIR/models/ultralytics"
dl "$REPO/pussyV2.pt" "$COMFYUI_DIR/models/ultralytics"

# --- Detectors on the NSFW graph's LIVE path ---
# These two are NOT in the AIOFM-Pack mirror. That was verified against the
# manifest build_manifest() writes, which lists all 55 files the private repo
# holds: it has lips_v1/nipple/pussyV2 -- the three DEAD-path detectors -- and
# neither of the two the live path needs.
#
#   face_yolov8m.pt   #611 (sg1), #107 (sg2), #426 (sg4)   -- three live uses
#   hand_yolov8s.pt   #89  (sg0)                           -- the hand detailer
#
# Bingsu/adetailer is the canonical public home for both. Content-Length was
# checked against the working copies on the render pod and matches exactly:
# 52,026,019 and 22,507,643 bytes.
dl_public "https://huggingface.co/Bingsu/adetailer/resolve/main/face_yolov8m.pt" "$COMFYUI_DIR/models/ultralytics"
dl_public "https://huggingface.co/Bingsu/adetailer/resolve/main/hand_yolov8s.pt" "$COMFYUI_DIR/models/ultralytics"

# --- Auto-populate bbox/ (used to be a manual step) ---
mkdir -p "$COMFYUI_DIR/models/ultralytics/bbox"
for f in "$COMFYUI_DIR"/models/ultralytics/*.pt; do
    [[ -e "$f" ]] || continue
    b="$COMFYUI_DIR/models/ultralytics/bbox/$(basename "$f")"
    [[ -s "$b" ]] || ln "$f" "$b" 2>/dev/null || cp "$f" "$b"
done
echo "    bbox: done"

# Impact Subpack registers models/ultralytics/segm as well as bbox/. This
# graph's seven detectors are all bbox/, so nothing reads it -- but the Subpack
# expects the directory to exist and nothing else creates it.
mkdir -p "$COMFYUI_DIR/models/ultralytics/segm"

# ============================================
# models/sams
#
# Impact Pack's SAMLoader reads from models/sams and nowhere else
# (impact_pack.py registers "sams" -> models/sams). Three LIVE SAMLoader nodes
# in the NSFW graph -- #88 (sg0), #108 (sg2), #160 (sg3) -- plus one bypassed.
# This directory was never created by this script and the model was never
# fetched, so all three found nothing.
#
# Not in the AIOFM-Pack mirror either (checked against the 55-entry manifest).
# Content-Length verified against the render pod: 375,042,383 bytes. Meta's own
# bucket serves the identical file if the HF mirror ever moves:
#   https://dl.fbaipublicfiles.com/segment_anything/sam_vit_b_01ec64.pth
# ============================================
echo ">>> models/sams"
mkdir -p "$COMFYUI_DIR/models/sams"
dl_public "https://huggingface.co/segments-arnaud/sam_vit_b/resolve/main/sam_vit_b_01ec64.pth" "$COMFYUI_DIR/models/sams"

# ============================================
# models/upscale_models
# ============================================
echo ">>> models/upscale_models"
dl "$REPO/4x-UltraSharpV2.pth" "$COMFYUI_DIR/models/upscale_models"
dl "$REPO/4x_NMKD-Superscale-SP_178000_G.pth" "$COMFYUI_DIR/models/upscale_models"
dl "$REPO/RealityGlass4x.pth" "$COMFYUI_DIR/models/upscale_models"
dl "$REPO/upscale1.pth" "$COMFYUI_DIR/models/upscale_models"
dl "$REPO/x1_ITF_SkinDiffDetail_Lite_v1.pth" "$COMFYUI_DIR/models/upscale_models"

# ============================================
# models/vae
# ============================================
echo ">>> models/vae"
dl "$REPO/flux2-vae.safetensors" "$COMFYUI_DIR/models/vae"
dl "$REPO/GlassRoot_D2.safetensors" "$COMFYUI_DIR/models/vae"
dl "$REPO/variational_encoder_primary.safetensors" "$COMFYUI_DIR/models/vae"

# --- ae.safetensors: the name the NSFW graph asks for ---
# #109 VAELoader in sg2 loads "ae.safetensors" and nothing in this script ever
# produced that name, so the Z-Image half of the graph had no VAE.
#
# It is not a missing download. variational_encoder_primary.safetensors IS the
# file, under a codename -- confirmed from its safetensors header rather than
# from its size:
#   modelspec.architecture : Flux.1-AE
#   modelspec.title        : Flux.1 Autoencoder
#   modelspec.author       : Black Forest Labs
#   decoder.conv_in.weight : [512, 16, 3, 3]   -- 16-channel latent
# which is the autoencoder Z-Image expects. Note it is NOT flux2-vae.
# safetensors, which this script also fetches and which is a different file.
#
# Hardlinked rather than copied, exactly as the SDXL block above does: same
# filesystem, so it is an instant rename and costs no extra disk. Guarded so
# re-runs stay idempotent.
VAE_PRIMARY="$COMFYUI_DIR/models/vae/variational_encoder_primary.safetensors"
VAE_AE="$COMFYUI_DIR/models/vae/ae.safetensors"
if [[ -s "$VAE_PRIMARY" && ! -s "$VAE_AE" ]]; then
    ln "$VAE_PRIMARY" "$VAE_AE" 2>/dev/null || cp "$VAE_PRIMARY" "$VAE_AE"
    echo "    link: variational_encoder_primary.safetensors -> ae.safetensors"
fi

# ============================================
# Custom nodes
#
# Every pack the video workflow references, pinned to a commit verified to
# provide the node types the graph actually uses. Pinning is the default so a
# fresh pod reproduces the environment the workflow was authored against
# without the buyer setting anything; PIN_NODES=0 tracks default branches
# instead.
#
# Repo URLs were resolved from the workflow JSON's own cnr_id / aux_id fields
# through the ComfyUI registry (api.comfy.org/nodes/<cnr_id>) and each repo was
# confirmed to still export the node names the graph expects. They are not
# guesses. The previous pin (WanVideoWrapper 5a23836) predated Wan Animate and
# was missing 5 of the 13 WanVideo* classes this graph needs.
#
# Format: <clone url>|<commit sha>
# ============================================
NODE_REPOS=(
    "https://github.com/kijai/ComfyUI-WanVideoWrapper.git|088128b224242e110d3906c6750e9a3a348a659b"
    "https://github.com/kijai/ComfyUI-KJNodes.git|4d46ac107c33ed8a3d181b8776ede66498583380"
    "https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite.git|4ee72c065db22c9d96c2427954dc69e7b908444b"
    "https://github.com/kijai/ComfyUI-WanAnimatePreprocess.git|0e0b6a2a555625acf4d4aefb780e27d06937132f"
    "https://github.com/kijai/ComfyUI-segment-anything-2.git|0c35fff5f382803e2310103357b5e985f5437f32"
    "https://github.com/Fannovel16/ComfyUI-Frame-Interpolation.git|26545cc2dd95bc3d27f056016300673bdeee78f5"
    "https://github.com/rgthree/rgthree-comfy.git|6b76ee6f2c5a007710b5a16f97c94330d6ecc871"
    "https://github.com/yolain/ComfyUI-Easy-Use.git|595e0738a9e3f8d0d9c4d875461b2d2c9e7559c7"
    "https://github.com/evanspearman/ComfyMath.git|c01177221c31b8e5fbc062778fc8254aeb541638"
    "https://github.com/digitaljohn/comfyui-propost.git|df6a6d122498f57ad7195d58e07701a501c9dcb6"
    "https://github.com/pythongosssss/ComfyUI-Custom-Scripts.git|609f3afaa74b2f88ef9ce8d939626065e3247469"
    "https://github.com/aining2022/ComfyUI_Swwan.git|258a15eacd9f956b94fca134442e77709e8d45f7"

    # --- Added for the NSFW image workflow (OFMTech_NSFW.json) ---
    # None of these six were installed by this script before, which left that
    # graph a wall of red nodes. Every SHA below is the commit that is checked
    # out on the pod where OFMTech_NSFW.json was rendered end to end, so these
    # are validated by a working 240s render, not resolved on paper.
    #
    # Two notes that cost real time to establish:
    #   * UltralyticsDetectorProvider (7 instances) is in Impact SUBPACK, not
    #     Impact Pack. Installing only the Pack leaves 7 nodes unresolvable.
    #   * MediaPipeFaceMeshToSEGS is in Impact PACK, not controlnet_aux.
    #     controlnet_aux supplies only MediaPipe-FaceMeshPreprocessor and
    #     DepthAnythingV2Preprocessor.
    #
    # UltimateSDUpscale has a hard floor: both UltimateSDUpscale nodes in that
    # graph carry 21 widgets_values ending in batch_size, which was added
    # around fe0196319f19 (~2026-02-08). Pinning older silently desyncs every
    # widget on both nodes. a5547db9 is 2026-06-22, comfortably past it.
    #
    # cubiq's essentials and IPAdapter_plus are both in declared
    # maintenance-only mode (README banners, 2025-04-14). ImageColorMatch+ is
    # used three times on the live path. Two unmaintained dependencies in a
    # product being sold is a deliberate risk, not an oversight -- QUESTIONS Q12.
    "https://github.com/ltdrdata/ComfyUI-Impact-Pack|429d0159ad429e64d2b3916e6e7be9c22d025c3c"
    "https://github.com/ltdrdata/ComfyUI-Impact-Subpack|50c7b71a6a224734cc9b21963c6d1926816a97f1"
    "https://github.com/Fannovel16/comfyui_controlnet_aux|95a13e2e5d8f8ae57583fbebb0be1f670889858b"
    "https://github.com/cubiq/ComfyUI_IPAdapter_plus|a0f451a5113cf9becb0847b92884cb10cbdec0ef"
    "https://github.com/cubiq/ComfyUI_essentials|9d9f4bedfc9f0321c19faf71855e228c93bd0dc9"
    "https://github.com/ssitu/ComfyUI_UltimateSDUpscale|a5547db9e1d07d3318bb21e9e9c474f4c1e9c8df"
)

# Never returns non-zero: a single bad repo must not abort the whole setup
# under `set -e`, so one dead URL does not leave the pod half-built. Every
# failure names the repo and its URL on the spot, is counted by warn(), and is
# re-reported by the workflow node check at the end.
NODE_CLONE_FAIL=0
install_node() {
    local url="$1" sha="$2" name dir head err
    name="$(basename "$url" .git)"
    dir="$COMFYUI_DIR/custom_nodes/$name"

    if [[ ! -d "$dir/.git" ]]; then
        err="$("${GIT_Q[@]}" clone -q "$url" "$dir" 2>&1)" || {
            NODE_CLONE_FAIL=$((NODE_CLONE_FAIL+1))
            warn "CLONE FAILED: $name"
            printf '        repo: %s\n' "$url"
            if [[ -n "$err" ]]; then
                printf '        git : %s\n' \
                    "$(echo "$err" | grep -m1 '^fatal:' || echo "$err" | head -1)"
            fi
            printf '        the nodes this pack provides will be red in the graph\n'
            return 0
        }
    fi

    if [[ "${PIN_NODES:-1}" == "1" ]]; then
        # Check out the exact commit. Fetching the sha directly works whatever
        # the repo's default branch is — comfyui-propost defaults to master,
        # every other pack here defaults to main — so no branch is assumed.
        (
            cd "$dir" || exit 1
            "${GIT_Q[@]}" fetch -q origin "$sha" 2>/dev/null \
                || "${GIT_Q[@]}" fetch -q --all 2>/dev/null || true
            "${GIT_Q[@]}" -c advice.detachedHead=false checkout -q "$sha" 2>/dev/null
        ) || true
        # `|| true` matters: under `set -e` an assignment from a failing
        # command substitution aborts the script, and the ERR trap would
        # report it as a stage failure.
        head="$( cd "$dir" 2>/dev/null && git rev-parse HEAD 2>/dev/null )" || true
        if [[ "$head" == "$sha" ]]; then
            ok "$name @ ${sha:0:7}"
        else
            warn "$name is at ${head:0:7}, wanted ${sha:0:7} — node versions may not match the workflow"
        fi
    else
        ( cd "$dir" 2>/dev/null && "${GIT_Q[@]}" pull -q 2>/dev/null ) || true
        ok "$name @ default branch (unpinned)"
    fi
    return 0
}

echo ""
if [[ "${PIN_NODES:-1}" == "1" ]]; then
    stage "Custom nodes (pinned)"
else
    stage "Custom nodes (unpinned — PIN_NODES=0)"
fi
mkdir -p "$COMFYUI_DIR/custom_nodes"
for entry in "${NODE_REPOS[@]}"; do
    install_node "${entry%%|*}" "${entry##*|}"
done

# ofmtechclip is not pinned: it is our own repo and is expected to move.
OFMTECH_URL="https://github.com/msit270/ofmtechclip.git"
if [[ -d "$COMFYUI_DIR/custom_nodes/ofmtechclip/.git" ]]; then
    ( cd "$COMFYUI_DIR/custom_nodes/ofmtechclip" && "${GIT_Q[@]}" pull -q ) || true
    ok "ofmtechclip updated"
elif "${GIT_Q[@]}" clone -q "$OFMTECH_URL" "$COMFYUI_DIR/custom_nodes/ofmtechclip" 2>/dev/null; then
    ok "ofmtechclip cloned"
else
    NODE_CLONE_FAIL=$((NODE_CLONE_FAIL+1))
    warn "CLONE FAILED: ofmtechclip"
    printf '        repo: %s\n' "$OFMTECH_URL"
fi

if (( PIPED )); then
    warn "this script was piped, so it cannot see the files shipped beside it"
    printf '        ComfyUI_INSTARAW will NOT be installed and the workflow will\n'
    printf '        NOT appear in your workflow list. To get both, unpack the\n'
    printf '        pack and run the copy inside it:\n'
    printf '            cd /workspace/AIOFMTech-NSFW && bash aiofm_setup.sh\n'
fi

# --- ComfyUI_INSTARAW: vendored, not cloned ---
# This pack cannot go in NODE_REPOS. That array is <url>|<sha> and this pack
# has no public URL: no pyproject.toml, no cnr_id, no LICENSE and no git remote
# in the delivered folder. Its own node metadata gives
# aux_id "instara-io/ComfyUI_INSTARAW" and
# ver 12afb909b3380bd4a3f118061654dd72d1edcd4c, implying a private repo, and a
# buyer-facing script cannot clone one of those. That is exactly why
# INSTALL MODELS.txt used to tell the buyer to drag the folder in by hand.
#
# So it ships inside the distribution archive and is copied into place here.
# 16 of the NSFW graph's nodes come from it, including #483, the entry node
# that supplies the prompt, the negative and the seed for the whole pipeline.
# Without it the graph does not merely lose a feature, it does not run.
#
# Copied, never overwritten: if the buyer already has a newer copy installed,
# leave it alone rather than silently reverting them to the shipped one.
if [[ -n "$SCRIPT_DIR" && -d "$SCRIPT_DIR/ComfyUI_INSTARAW" ]]; then
    if [[ -d "$COMFYUI_DIR/custom_nodes/ComfyUI_INSTARAW" ]]; then
        ok "ComfyUI_INSTARAW already present (left as-is)"
    elif cp -r "$SCRIPT_DIR/ComfyUI_INSTARAW" "$COMFYUI_DIR/custom_nodes/" 2>/dev/null; then
        ok "ComfyUI_INSTARAW vendored @ 12afb909 (provenance marker)"
    else
        NODE_CLONE_FAIL=$((NODE_CLONE_FAIL+1))
        warn "could not copy ComfyUI_INSTARAW into custom_nodes"
        printf '        source: %s\n' "$SCRIPT_DIR/ComfyUI_INSTARAW"
    fi
fi

if [[ "$NODE_CLONE_FAIL" -gt 0 ]]; then
    warn "$NODE_CLONE_FAIL repo(s) could not be cloned — see the lines above"
fi

# ============================================
# Custom node dependencies
#
# 10 of the 12 packs ship a requirements.txt. Without them the pack fails to
# import and every node it provides turns red, so this is not optional.
#
# Two package families are filtered out before install:
#
#   onnxruntime / onnxruntime-gpu — ComfyUI_Swwan and ComfyUI-Easy-Use list
#     plain `onnxruntime` unpinned, and WanAnimatePreprocess lists
#     `onnxruntime-gpu` unpinned. Installing either here would pull a CUDA 13
#     build over the CUDA 12 one selected in the onnxruntime stage above and
#     send ViTPose-H silently back to the CPU. Having both packages installed
#     side by side causes the same failure. onnxruntime-gpu already provides
#     the `onnxruntime` module, so nothing loses a real dependency.
#
#   torch / torchvision / torchaudio — unpinned in ComfyUI_Swwan. Letting pip
#     resolve those risks replacing the cu12x build the pod is set up around.
#
#   numpy — ComfyUI_INSTARAW pins `numpy==1.26.4`, a hard pin that downgrades
#     numpy for the entire ComfyUI environment, not just that pack. Its own
#     line 2 says "torch and numpy are already included with ComfyUI", which
#     its line 63 then contradicts. Highest blast radius in that file.
#
#   opencv-contrib-python — ComfyUI_INSTARAW pins the NON-headless build,
#     while comfyui_controlnet_aux (which the NSFW graph requires) installs the
#     headless one. Both distributions in one environment is a known breakage,
#     and the loser is whichever imported cv2 first.
#
#   mediapipe, opencv-python -- comfyui_controlnet_aux lists BOTH UNPINNED, and
#     unpinned means newest. Caught by the clean-install test, which upgraded a
#     working pod to mediapipe 1.0.0 and broke the eye pass outright:
#       AttributeError: module 'mediapipe' has no attribute 'solutions'
#     mediapipe 1.0 removed the legacy `mp.solutions` API, and
#     src/custom_controlnet_aux/mediapipe_face/mediapipe_face_common.py:8-12
#     needs drawing_utils, drawing_styles, face_detection, face_mesh and
#     face_mesh_connections from exactly that namespace. The same run pulled
#     opencv 5.0.0.93 in all three distributions at once.
#     Pinned explicitly below instead. Note the ORIGINAL ComfyUI_INSTARAW
#     requirements.txt pinned mediapipe==0.10.14 with the comment "for
#     compatibility with comfyui_controlnet_aux" -- that comment was correct,
#     and dropping the pin as unused-by-INSTARAW missed that another pack needs
#     it. Restored here, where it belongs.
#
# The two numpy/opencv entries were added when ComfyUI_INSTARAW was brought
# into this script. Both are also fixed at source in that pack's own
# requirements.txt now, but the filter stays: it is the backstop for the pack
# being re-vendored from an older copy, which is exactly how it shipped.
#
# ComfyUI-Frame-Interpolation ships two variants. RIFE never imports cupy and
# cupy-wheel is CUDA-version sensitive, so the no-cupy set is used.
# ============================================
NODE_DEP_SKIP='^[[:space:]]*(torch|torchvision|torchaudio|onnxruntime|onnxruntime-gpu|numpy|opencv-contrib-python|opencv-python|mediapipe)([[:space:]<>=!~;[]|$)'

install_node_deps() {
    local dir="$1" name req tmp
    name="$(basename "$dir")"
    req="$dir/requirements.txt"
    [[ -f "$dir/requirements-no-cupy.txt" ]] && req="$dir/requirements-no-cupy.txt"
    [[ -f "$req" ]] || return 0

    tmp="$(mktemp)"
    grep -vEi "$NODE_DEP_SKIP" "$req" > "$tmp" 2>/dev/null || true
    if [[ -s "$tmp" ]]; then
        if pip install -q -r "$tmp" 2>/dev/null; then
            ok "$name"
        else
            warn "$name — some dependencies failed to install, its nodes may not load"
        fi
    fi
    rm -f "$tmp"
    return 0
}

echo ""
stage "Custom node dependencies"
for entry in "${NODE_REPOS[@]}"; do
    url="${entry%%|*}"
    install_node_deps "$COMFYUI_DIR/custom_nodes/$(basename "$url" .git)"
done
# INSTARAW is vendored rather than cloned, so it is not in NODE_REPOS and would
# otherwise never reach the filter above. Routing it through install_node_deps
# rather than a bare `pip install -r` is the whole point: its requirements.txt
# is what NODE_DEP_SKIP's numpy and opencv-contrib-python entries exist for.
install_node_deps "$COMFYUI_DIR/custom_nodes/ComfyUI_INSTARAW"

# --- pinned versions the packs ask for unpinned ---
# See the NODE_DEP_SKIP rationale above. These are filtered out of every pack's
# requirements precisely so they can be set once, here, to versions the graph is
# known to render on.
for spec in "mediapipe==0.10.14" "opencv-python-headless==4.10.0.84"; do
    have="$(python3 -c "import importlib.metadata as m,sys; print(m.version(sys.argv[1].split('==')[0]))" "$spec" 2>/dev/null || echo none)"
    want="${spec##*==}"
    if [[ "$have" == "$want" ]]; then
        ok "$spec already satisfied"
    elif pip install -q "$spec" 2>/dev/null; then
        ok "$spec installed (was $have)"
    else
        warn "could not install $spec -- the eye pass may fail at render time"
    fi
done
# mediapipe 1.x removes mp.solutions, which controlnet_aux imports at module
# scope, so assert it rather than trusting the pin took.
if python3 -c "import mediapipe as mp; assert hasattr(mp,'solutions')" 2>/dev/null; then
    ok "mediapipe exposes mp.solutions (controlnet_aux face mesh will load)"
else
    warn "mediapipe does not expose mp.solutions -- sg4's eye pass will fail"
fi

# --- Impact Subpack: trust the three custom detectors ---
# Under PyTorch >= 2.6, torch.load defaults to weights_only=True and the
# Subpack falls back to an explicit whitelist for .pt files that fail safe
# loading. lips_v1.pt, nipple.pt and pussyV2.pt are exactly that class of file.
#
# Honest note: this did NOT bite at the pins above on torch 2.9.1 -- the full
# graph rendered with all three detectors loading normally, and the Subpack's
# own auto-created whitelist was still empty. This is pre-emptive, because the
# failure without it is an opaque mid-render error on some other torch version,
# and the three files come from the vendor's own mirror. Appended, never
# rewritten, so a buyer's own entries survive a re-run.
SUBPACK_WL="$COMFYUI_DIR/user/default/ComfyUI-Impact-Subpack/model-whitelist.txt"
mkdir -p "$(dirname "$SUBPACK_WL")"
touch "$SUBPACK_WL"
for det in lips_v1.pt nipple.pt pussyV2.pt; do
    grep -qxF "$det" "$SUBPACK_WL" 2>/dev/null || echo "$det" >> "$SUBPACK_WL"
done

# ============================================
# SageAttention — wait for the background install
# ============================================
if [[ -n "$SAGE_PID" ]]; then
    echo ""
    stage "SageAttention"
    wait "$SAGE_PID" 2>/dev/null || true
    if python3 -c 'import sageattention' 2>/dev/null; then
        ok "SageAttention installed"
        BUILT="$(find "$WHEELDIR" -name 'sageattention*.whl' 2>/dev/null | head -1)"
        if [[ -n "$BUILT" ]]; then
            echo ""
            info "Upload the wheel to the mirror once to skip the 15-min build:"
            echo "    $HF_CMD upload $HF_REPO_ID $BUILT wheels/$(basename "$BUILT")"
        fi
    else
        warn "SageAttention NOT installed — see $SAGE_LOG (not fatal)"
    fi
fi

# ============================================
# Models that other nodes fetch themselves at render time.
# Pulling them here means no mid-render network call — a failed
# download at that point costs the whole sampling pass.
# ============================================
stage "Render-time models (RIFE, SAM2)"

# ComfyUI-Frame-Interpolation resolves a checkpoint as
#     <pack root>/<ckpts_path from config.yaml>/<model type>
# where ckpts_path defaults to "./ckpts" and the model type for RIFE is the
# directory name "rife". The file therefore has to land in <pack>/ckpts/rife
# or the node ignores it and downloads again mid-render. The pack is installed
# above, so this path is now deterministic rather than globbed for.
RIFE_DIR="$COMFYUI_DIR/custom_nodes/ComfyUI-Frame-Interpolation/ckpts/rife"
mkdir -p "$RIFE_DIR"
if [[ -s "$RIFE_DIR/rife49.pth" ]]; then
    ok "rife49.pth present"
else
    for u in "https://github.com/Fannovel16/ComfyUI-Frame-Interpolation/releases/download/models/rife49.pth" \
             "https://github.com/styler00dollar/VSGAN-tensorrt-docker/releases/download/models/rife49.pth"; do
        if wget -q --show-progress -O "$RIFE_DIR/rife49.pth" "$u"; then
            ok "rife49.pth fetched"; break
        fi
        rm -f "$RIFE_DIR/rife49.pth"
    done
    [[ -s "$RIFE_DIR/rife49.pth" ]] || warn "rife49.pth could not be fetched — it will download mid-render"
fi

# DownloadAndLoadSAM2Model does NOT load the filename shown on its widget.
# ComfyUI-segment-anything-2/nodes.py:62-65:
#     if precision != 'fp32' and "2.1" in model:
#         base_name, extension = model.rsplit('.', 1)
#         model = f"{base_name}-fp16.{extension}"
# The graph runs that node at precision=fp16 with sam2.1_hiera_base_plus, so
# the file it actually opens is sam2.1_hiera_base_plus-fp16.safetensors and
# anything else is downloaded mid-render — which is exactly what this stage
# exists to prevent. Fetching the plain name pulled 323 MB that is never read
# and still left the 162 MB the render needs to arrive during sampling.
# Verified on this pod: setup wrote the plain file at 00:19, and the node
# downloaded the -fp16 file itself at 00:42 during the first render.
mkdir -p "$COMFYUI_DIR/models/sam2"
SAM2_FILE="sam2.1_hiera_base_plus-fp16.safetensors"
if [[ -s "$COMFYUI_DIR/models/sam2/$SAM2_FILE" ]]; then
    ok "$SAM2_FILE present"
else
    hf_pull_flat "Kijai/sam2-safetensors" "$SAM2_FILE" \
                 "$COMFYUI_DIR/models/sam2" \
        && ok "sam2 fetched (fp16)" \
        || warn "sam2 not fetched — it will download on first render"
fi
# Only needed if a buyer switches that node to precision=fp32, which the
# shipped graph does not. Fetched best-effort so that path is not a surprise,
# but its absence is not worth a warning.
if [[ ! -s "$COMFYUI_DIR/models/sam2/sam2.1_hiera_base_plus.safetensors" ]] \
   && [[ "${SAM2_FP32:-0}" == "1" ]]; then
    hf_pull_flat "Kijai/sam2-safetensors" "sam2.1_hiera_base_plus.safetensors" \
                 "$COMFYUI_DIR/models/sam2" \
        && ok "sam2 fp32 variant fetched" || true
fi

# ============================================
# Install the workflow itself
#
# Everything above installs what the workflow NEEDS and then leaves the buyer
# to find the .json and import it by hand. ComfyUI reads saved workflows from
# user/default/workflows, so putting it there means the pack is simply present
# in the workflow list when they first open the UI.
#
# Copies from beside this script, which is how the pack is delivered. Silent
# no-op if the json is not there, since the script must also work when it is
# run on its own.
# ============================================
# SCRIPT_DIR is defined at the top of this script -- it is needed long before
# here now, for vendoring ComfyUI_INSTARAW.
WF_DEST="$COMFYUI_DIR/user/default/workflows"
if workflow_files >/dev/null 2>&1; then
    echo ""
    stage "Workflow"
    mkdir -p "$WF_DEST"
    while IFS= read -r wf; do
        base="$(basename "$wf")"
        if [[ -f "$WF_DEST/$base" ]] && ! cmp -s "$wf" "$WF_DEST/$base"; then
            # Never clobber edits a buyer has made to their own copy.
            cp -n "$wf" "$WF_DEST/$base.new" 2>/dev/null || true
            warn "$base differs from the installed copy — wrote $base.new instead"
        else
            cp -f "$wf" "$WF_DEST/$base" && ok "$base installed"
        fi
    done < <(workflow_files)
    info "open ComfyUI and it will be in the workflow list"
fi

# ============================================
# Integrity check
# ============================================
rm -rf "$TMPDL"
echo ""
stage "Integrity check"
SUSPECT=0
TRUNCATED=0
OVERSIZE=0
# Size-verify every file we have an expected size for. The <1MB heuristic
# below only ever caught an HTML error page saved under a .safetensors name;
# a 34 GB model cut off at 20 GB sailed straight through it, and then failed
# at load time looking like a corrupt model rather than a short download.
#
# Report EXACT BYTES, not human(). The comparison on the line below is
# byte-exact, but this used to print through human()'s "%.1f GB", so a file
# 300 KB short of 6.9 GB rendered as
#     INCOMPLETE: SDXLNSFW.safetensors has 6.5 GB, expected 6.5 GB
# -- a message that names a problem, shows two identical numbers as evidence
# for it, and gives the reader nothing to act on. Exact bytes plus the signed
# delta says how short it is and which direction, which is the whole point.
while IFS= read -r f; do
    fname="$(basename "$f")"
    exp="$(expected_size "$fname")" || continue
    have="$(stat -c %s "$f" 2>/dev/null || echo 0)"
    if [[ "$have" != "$exp" ]]; then
        if (( have < exp )); then
            echo "      INCOMPLETE: $fname"
            printf '        have %s bytes, expected %s (short by %s, %s)\n' \
                "$have" "$exp" "$((exp - have))" "$(human $((exp - have)))"
            TRUNCATED=$((TRUNCATED+1))
        else
            # Resuming cannot fix this: curl -C - only appends. dl() deletes
            # and refetches an over-size file, so if it survives to here the
            # manifest and the file disagree in a way re-running will not
            # resolve, and saying "re-run to resume" would loop forever.
            echo "      OVER-SIZE:  $fname"
            printf '        have %s bytes, expected %s (%s larger, %s)\n' \
                "$have" "$exp" "$((have - exp))" "$(human $((have - exp)))"
            printf '        delete it and re-run; resuming cannot shrink a file\n'
            OVERSIZE=$((OVERSIZE+1))
        fi
    fi
done < <(find "$COMFYUI_DIR/models" -type f ! -path "*/.cache/*" 2>/dev/null)
if [[ "$TRUNCATED" -gt 0 || "$OVERSIZE" -gt 0 ]]; then
    # Counted separately because the remedies are opposite. Telling a buyer to
    # "re-run to resume" an over-size file sends them round a loop that cannot
    # terminate, which is the failure this split exists to prevent.
    [[ "$TRUNCATED" -gt 0 ]] && \
        warn "$TRUNCATED file(s) are short — re-run this script to resume them"
    [[ "$OVERSIZE" -gt 0 ]] && \
        warn "$OVERSIZE file(s) are larger than the manifest — delete those and re-run"
elif [[ -n "$MANIFEST" && -s "$MANIFEST" ]]; then
    ok "all sized files match the manifest"
else
    info "no manifest available — size verification skipped"
fi

while IFS= read -r f; do
    # ONNX with external weights: the graph itself is small (a few hundred
    # KB) and the weights sit beside it in a .bin. Treat the graph as valid
    # if it references a weights file that actually exists.
    if [[ "$f" == *.onnx ]]; then
        onnx_ok=0
        for b in "$(dirname "$f")"/*.bin; do
            [[ -s "$b" ]] || continue
            if grep -qaF "$(basename "$b")" "$f" 2>/dev/null; then
                onnx_ok=1
                break
            fi
        done
        [[ "$onnx_ok" == "1" ]] && continue
    fi
    sz=$(stat -c %s "$f" 2>/dev/null || echo 0)
    if [[ "$sz" -lt 1000000 ]]; then
        echo "      SUSPICIOUSLY SMALL ($((sz/1024)) KB): $f"
        SUSPECT=$((SUSPECT+1))
    fi
done < <(find "$COMFYUI_DIR/models" -type f \
         \( -name "*.safetensors" -o -name "*.pth" -o -name "*.pt" \
            -o -name "*.gguf" -o -name "*.onnx" -o -name "*.bin" \) \
         ! -path "*/.cache/*" 2>/dev/null)

TOTAL=$(find "$COMFYUI_DIR/models" -type f ! -path "*/.cache/*" 2>/dev/null | wc -l)

echo ""
stage "ViTPose GPU inference check"
python3 - <<PYEOF 2>/dev/null || warn "could not verify"
import onnxruntime as ort, os
m = "$COMFYUI_DIR/models/detection/vitpose_h_wholebody_model.onnx"
if not os.path.exists(m):
    print("      model not downloaded yet — skipped")
else:
    s = ort.InferenceSession(m, providers=["CUDAExecutionProvider","CPUExecutionProvider"])
    p = s.get_providers()
    print("      providers:", p)
    print("      OK — pose detection will run on the GPU" if "CUDAExecutionProvider" in p
          else "      WARNING: fell back to CPU — detection will be very slow")
PYEOF

# ============================================
# Workflow node check
#
# Confirms every node type the video workflow references is actually provided
# by something on disk, so a missing pack shows up here as one line of text
# instead of a red node in the graph an hour later.
#
# This is a static check of the installed sources. It proves the pack is
# present and exports the name; it cannot prove the pack imports cleanly at
# runtime (a missing Python dependency would still break it). The dependency
# stage above reports those separately, and the ComfyUI restart stage below
# does the real runtime check against /object_info once ComfyUI is back up.
# ============================================
echo ""
stage "Workflow node check"
CN_DIR="$COMFYUI_DIR/custom_nodes"
NODE_FAIL=0
# Counted, not hardcoded. This stage used to end with a literal
# `all 40 workflow node types present`. The 40 happened to be arithmetically
# right -- 27 loop-driven check_node calls + 9 direct + 3 check_web_node + 1
# inline Any Switch -- but only by hand-maintenance, and it sat on the same
# screen as the summary's `workflow nodes : all 88 present` with nothing to
# explain why a buyer was being shown two different numbers for what reads like
# the same thing. They measure different things:
#
#   this stage : are the FILES on disk? A source grep or a marker file, over a
#                fixed baseline list. No Python is imported, so a pack that is
#                present but broken passes here.
#   the 88     : the union of that baseline with the node types read out of the
#                shipped workflow json, checked against a running server's
#                /object_info. That is the authoritative one.
#
# Deriving the number means it can never drift from the list again.
NODE_CHECKED=0

check_node() {   # $1 = pack directory name, $2 = node type string
    NODE_CHECKED=$((NODE_CHECKED+1))
    local d="$CN_DIR/$1"
    if [[ ! -d "$d" ]]; then
        printf '      %sMISSING PACK%s  %-34s provides: %s\n' "$C_R" "$C_0" "$1" "$2"
        NODE_FAIL=$((NODE_FAIL+1)); return 0
    fi
    grep -rqF --include='*.py' "\"$2\"" "$d" 2>/dev/null && return 0
    grep -rqF --include='*.py' "'$2'"  "$d" 2>/dev/null && return 0
    printf '      %sMISSING NODE%s  %-34s expected in: %s\n' "$C_R" "$C_0" "$2" "$1"
    NODE_FAIL=$((NODE_FAIL+1))
    return 0
}

for n in WanVideoAnimateEmbeds WanVideoBlockSwap WanVideoClipVisionEncode \
         WanVideoDecode WanVideoLoraSelect WanVideoLoraSelectMulti \
         WanVideoModelLoader WanVideoSampler WanVideoSetBlockSwap \
         WanVideoSetLoRAs WanVideoTextEncodeCached \
         WanVideoTorchCompileSettings WanVideoVAELoader; do
    check_node ComfyUI-WanVideoWrapper "$n"
done
for n in BlockifyMask GetImageSizeAndCount GrowMaskWithBlur ImageConcatMulti \
         ImageResizeKJv2 INTConstant; do
    check_node ComfyUI-KJNodes "$n"
done
# SetNode / GetNode are deliberately not in that list — see the frontend-only
# section below.
check_node ComfyUI-VideoHelperSuite   VHS_LoadVideo
check_node ComfyUI-VideoHelperSuite   VHS_VideoCombine
for n in PoseAndFaceDetection DrawViTPose OnnxDetectionModelLoader \
         PoseRetargetPromptHelper; do
    check_node ComfyUI-WanAnimatePreprocess "$n"
done
check_node ComfyUI-segment-anything-2 DownloadAndLoadSAM2Model
check_node ComfyUI-segment-anything-2 Sam2Segmentation
check_node ComfyUI-Frame-Interpolation "RIFE VFI"
for n in "easy cleanGpuUsed" "easy clearCacheAll" "easy mathFloat" \
         "easy showAnything"; do
    check_node ComfyUI-Easy-Use "$n"
done
check_node ComfyMath                  CM_IntToFloat
check_node comfyui-propost            ProPostFilmGrain
check_node ComfyUI-Custom-Scripts     "ShowText|pysssss"
check_node ComfyUI_Swwan              DrawMaskOnImage

# --- nodes that are NOT registered in Python ---
#
# Four of the graph's node types never appear in NODE_CLASS_MAPPINGS, so
# grepping the Python sources for them reports a false MISSING on a perfectly
# good install, and they never show up in /object_info either:
#
#   SetNode, GetNode        KJNodes registers these client-side with
#                           LiteGraph.registerNodeType() in
#                           web/js/setgetnodes.js, delivered via
#                           WEB_DIRECTORY = "./web". No Python class exists —
#                           the strings do not occur anywhere in the pack's
#                           .py files.
#   Label (rgthree)         Same situation: frontend-only, registered in JS as
#                           rgthree.Label in web/comfyui/label.js.
#   Any Switch (rgthree)    Does have a Python class, but its name is built at
#                           runtime — py/constants.py sets NAMESPACE='rgthree'
#                           and get_name() appends " (rgthree)" — so the literal
#                           string never appears in the source either.
#
# For all four, check the real marker that proves the node will be available.
check_web_node() {   # $1 = pack dir, $2 = marker file relative to it, $3 = node name
    NODE_CHECKED=$((NODE_CHECKED+1))
    if [[ -f "$CN_DIR/$1/$2" ]]; then return 0; fi
    printf '      %sMISSING NODE%s  %-34s expected in: %s/%s\n' "$C_R" "$C_0" "$3" "$1" "$2"
    NODE_FAIL=$((NODE_FAIL+1))
    return 0
}

check_web_node ComfyUI-KJNodes web/js/setgetnodes.js      SetNode
check_web_node ComfyUI-KJNodes web/js/setgetnodes.js      GetNode
check_web_node rgthree-comfy   web/comfyui/label.js       "Label (rgthree)"

NODE_CHECKED=$((NODE_CHECKED+1))
if [[ -d "$CN_DIR/rgthree-comfy" ]]; then
    grep -rqF 'get_name("Any Switch")' "$CN_DIR/rgthree-comfy" 2>/dev/null \
        || { printf '      %sMISSING NODE%s  Any Switch (rgthree)\n' "$C_R" "$C_0"; NODE_FAIL=$((NODE_FAIL+1)); }
else
    printf '      %sMISSING PACK%s  rgthree-comfy\n' "$C_R" "$C_0"
    NODE_FAIL=$((NODE_FAIL+1))
fi

if [[ "$NODE_FAIL" -eq 0 ]]; then
    ok "all $NODE_CHECKED node types found on disk (static check of the installed packs)"
else
    warn "$NODE_FAIL of $NODE_CHECKED node types not found on disk — the graph will show red nodes"
fi

# ============================================
# Restart ComfyUI so the newly installed nodes register
#
# ComfyUI only scans custom_nodes at startup. Installing packs into a running
# instance changes nothing until it restarts, so the graph keeps showing red
# nodes. That reads as a broken install, and the obvious next move is to open
# ComfyUI Manager and click Install / Try update — which would move every pack
# off its pinned commit and destroy the reproducibility this script just set up.
#
# RunPod and Vast ComfyUI images (ai-dock and its derivatives) run ComfyUI under
# supervisord, normally as a program named "comfyui", restartable with
# supervisorctl. That case is handled first, systemd second for bare-VM installs.
#
# Anything else is deliberately NOT touched. A hand-started `python main.py`, or
# ComfyUI running as the container's PID 1 entrypoint, has nothing supervising
# it — killing it would leave the pod with no ComfyUI and no way back. Those
# cases get an explicit instruction banner instead of a restart.
# ============================================
echo ""
stage "ComfyUI restart"

# Find the port ComfyUI is actually on, rather than assuming 8188.
#
# This was a silent failure, not a theoretical one. The pod this pack is built
# and rendered on runs ComfyUI on 18188 and does not set COMFYUI_PORT, so
# COMFY_URL pointed at a port with nothing on it. comfy_up() then always
# returned false, which meant RESTART_NEEDED was cleared, the restart never
# happened, and -- worse -- comfy_verify_nodes could never reach /object_info.
# The stage whose entire job is confirming every node registered has been
# reporting nothing on the machine this was developed on.
#
# Explicit COMFYUI_PORT still wins. Otherwise probe the usual ports and, before
# that, read it out of the running process's own arguments, which is the only
# source that cannot be wrong.
if [[ -n "${COMFYUI_PORT:-}" ]]; then
    COMFY_PORT="$COMFYUI_PORT"
else
    COMFY_PORT=""
    ARGPORT="$(ps -eo args 2>/dev/null | grep -m1 '[m]ain\.py' \
                | sed -n 's/.*--port[= ]\+\([0-9]\+\).*/\1/p')" || true
    for p in $ARGPORT 8188 18188; do
        [[ -n "$p" ]] || continue
        if curl -fsS --max-time 3 "http://127.0.0.1:$p/system_stats" >/dev/null 2>&1; then
            COMFY_PORT="$p"; break
        fi
    done
    if [[ -z "$COMFY_PORT" ]]; then
        COMFY_PORT="${ARGPORT:-8188}"     # nothing answered; keep it for the banner
    fi
fi
COMFY_URL="http://127.0.0.1:$COMFY_PORT"
info "ComfyUI expected on port $COMFY_PORT"

comfy_up() { curl -fsS --max-time 3 "$COMFY_URL/system_stats" >/dev/null 2>&1; }

comfy_wait_up() {   # $1 = max seconds. Images note ComfyUI can take 30-60s to rebind.
    local waited=0
    while (( waited < $1 )); do
        comfy_up && return 0
        sleep 3; waited=$((waited+3))
    done
    return 1
}

# Verifies the packs actually registered, which the static check above cannot
# do — it only proves the files are on disk, not that they imported cleanly.
# The 3 frontend-only types (SetNode, GetNode, Label (rgthree)) are excluded:
# they are registered client-side by LiteGraph and never appear in object_info.
comfy_verify_nodes() {
    python3 - "$COMFY_URL" "${SCRIPT_DIR:-}" <<'PYEOF' 2>/dev/null || return 1
import glob, json, os, sys, urllib.request
need = ["Any Switch (rgthree)","BlockifyMask","CM_IntToFloat","DownloadAndLoadSAM2Model",
        "DrawMaskOnImage","DrawViTPose","GetImageSizeAndCount","GrowMaskWithBlur",
        "INTConstant","ImageConcatMulti","ImageResizeKJv2","OnnxDetectionModelLoader",
        "PoseAndFaceDetection","PoseRetargetPromptHelper","ProPostFilmGrain","RIFE VFI",
        "Sam2Segmentation","ShowText|pysssss","VHS_LoadVideo","VHS_VideoCombine",
        "WanVideoAnimateEmbeds","WanVideoBlockSwap","WanVideoClipVisionEncode",
        "WanVideoDecode","WanVideoLoraSelect","WanVideoLoraSelectMulti",
        "WanVideoModelLoader","WanVideoSampler","WanVideoSetBlockSwap","WanVideoSetLoRAs",
        "WanVideoTextEncodeCached","WanVideoTorchCompileSettings","WanVideoVAELoader",
        "easy cleanGpuUsed","easy clearCacheAll","easy mathFloat","easy showAnything"]
# The list above is hand-maintained and had drifted: it missed CLIPVisionLoader
# and LoadImage, which the shipped graph uses, and named three nodes the graph
# does not contain. So derive the truth from the workflow when it is beside
# this script, and UNION it with the list -- union, so this can only ever check
# MORE than before, never fewer, and the other profile's extras stay covered.
def from_workflow(script_dir):
    found = set()
    if not script_dir:
        return found
    # Both shipped naming schemes. The NSFW image workflow is OFMTech_NSFW.json,
    # so an AIOFM-only glob meant this check silently verified nothing about it
    # -- which is how six missing node packs went unreported by a stage whose
    # entire job is reporting missing node packs.
    paths = sorted(set(glob.glob(os.path.join(script_dir, "AIOFM*.json")))
                   | set(glob.glob(os.path.join(script_dir, "OFMTech*.json"))))
    for path in paths:
        try:
            doc = json.load(open(path))
        except Exception:
            continue
        subs = {s["id"]: s for s in
                doc.get("definitions", {}).get("subgraphs", [])}
        nodes = list(doc.get("nodes", []))
        for s in subs.values():
            nodes.extend(s.get("nodes", []))
        for n in nodes:
            t = n.get("type")
            # This filter is LOAD-BEARING, not tidiness. Note and MarkdownNote
            # are frontend-only: the browser draws them and they never appear in
            # /object_info. Without this skip, a completely healthy install
            # reports a phantom missing node type and the buyer is told, by the
            # one line INSTALL MODELS.txt tells them to check, that their
            # install failed. Same reasoning for subgraph HOSTS, whose "type" is
            # a subgraph uuid rather than a registered node class.
            #
            # Bypassed nodes are kept on purpose: they still show red in the UI
            # if their pack is missing.
            if t and t not in ("Note", "MarkdownNote") and t not in subs:
                found.add(t)
    return found

derived = from_workflow(sys.argv[2] if len(sys.argv) > 2 else "")
if derived:
    added = sorted(derived - set(need))
    need = sorted(set(need) | derived)
    if added:
        print("      + %d node type(s) read from the workflow: %s"
              % (len(added), ", ".join(added)))

try:
    info = json.load(urllib.request.urlopen(sys.argv[1] + "/object_info", timeout=30))
    have = set(info)
except Exception as e:
    print("      could not read object_info: %s" % e); sys.exit(1)
# The running server must expose CLIPLoader's optional `device` input — the
# black-face fix (620:110 device="cpu") is silently dropped without it. The
# static check at install time reads the source; this reads the server that
# will actually execute the graph. Both must hold.
try:
    dev = info["CLIPLoader"]["input"]["optional"]["device"]
except (KeyError, TypeError):
    dev = None
if not dev:
    print("      FATAL: the running ComfyUI's CLIPLoader has no optional 'device'")
    print("      input. The workflow's device=\"cpu\" (the black-face fix, node")
    print("      620:110) would be SILENTLY DROPPED. Update ComfyUI core")
    print("      (>= v0.3.11) and re-run setup.")
    sys.exit(2)
missing = [n for n in need if n not in have]
if missing:
    print("      %d of %d node types did NOT register:" % (len(missing), len(need)))
    for m in missing:
        print("        %s" % m)
    sys.exit(2)
print("      all %d node types registered" % len(need))
# Publish the count actually verified, so the summary cannot claim a number
# the check never used. The old summary said "all 40 present" while the list
# held 37 and, once derived from the workflow, the real figure is 39.
try:
    open(os.environ.get("NODE_COUNT_FILE", "/dev/null"), "w").write(str(len(need)))
except Exception:
    pass
sys.exit(0)
PYEOF
}
NODE_COUNT_FILE="${TMPDIR:-/tmp}/.aiofm_node_count.$$"
export NODE_COUNT_FILE
trap 'rm -f "$NODE_COUNT_FILE"' EXIT

restart_banner() {   # $1 = reason
    printf '\n%s' "$C_R$C_B"
    echo "########################################################################"
    echo "#                                                                      #"
    echo "#   ACTION REQUIRED — RESTART COMFYUI BEFORE YOU RENDER                #"
    echo "#                                                                      #"
    echo "########################################################################"
    printf '%s\n' "$C_0"
    printf '  New custom nodes were installed. ComfyUI only loads custom nodes\n'
    printf '  when it starts, so until you restart it the workflow will show\n'
    printf '  %sRED NODES%s. That is expected. Nothing is broken.\n\n' "$C_R$C_B" "$C_0"
    printf '  %s\n\n' "$1"
    printf '%s  DO NOT use ComfyUI Manager to "Install missing nodes" or%s\n' "$C_Y$C_B" "$C_0"
    printf '%s  "Try update". Every pack is pinned to a specific version that%s\n' "$C_Y$C_B" "$C_0"
    printf '%s  this workflow was built against. Manager would move them and%s\n' "$C_Y$C_B" "$C_0"
    printf '%s  break the pinning. Just restart — the nodes are already here.%s\n\n' "$C_Y$C_B" "$C_0"
    printf '  After the restart, confirm with:\n'
    printf '    curl -s %s/object_info > /dev/null && echo OK\n' "$COMFY_URL"
    printf '  and re-run this script — it re-checks and will report clean.\n\n'
    printf '%s  Then HARD-RELOAD the browser tab (Ctrl-Shift-R / Cmd-Shift-R).%s\n' "$C_Y$C_B" "$C_0"
    printf '  The frontend is pinned to %s and the browser caches the old\n' "$FRONTEND_VERSION"
    printf '  JS across a server restart. A stale tab is the usual reason\n'
    printf '  subgraph widgets look wrong after a fresh setup.\n'
    printf '%s' "$C_B"
    echo "########################################################################"
    printf '%s\n' "$C_0"
}

RESTART_DONE=0
RESTART_NEEDED=1

if ! comfy_up; then
    RESTART_NEEDED=0
    ok "ComfyUI is not running — the new nodes will register when you start it"
else
    # supervisord (RunPod / Vast / ai-dock images). The program name is
    # discovered rather than assumed; `supervisorctl status` exits non-zero
    # whenever any program is not RUNNING, so its exit code is ignored and only
    # its output is used.
    #
    # An exact "comfyui" match is taken first, falling back to any comfy* name.
    # Without that precedence a sibling program listed earlier — comfyui-api,
    # comfyui-manager and similar exist in some images — would be restarted
    # instead of ComfyUI itself.
    SUPERVISOR_PROG=""
    if command -v supervisorctl >/dev/null 2>&1; then
        SUPERVISOR_NAMES="$(supervisorctl status 2>/dev/null | awk '{print $1}')" || true
        SUPERVISOR_PROG="$(printf '%s\n' "$SUPERVISOR_NAMES" | grep -ixE 'comfyui' | head -1)" || true
        if [[ -z "$SUPERVISOR_PROG" ]]; then
            SUPERVISOR_PROG="$(printf '%s\n' "$SUPERVISOR_NAMES" | grep -iE 'comfy' | head -1)" || true
        fi
    fi

    # systemd, for bare-VM installs. /run/systemd/system is the canonical test
    # for systemd actually being the init system — it is absent in containers.
    # Overridable only so this branch can be exercised in a test harness.
    SYSTEMD_MARKER="${SYSTEMD_MARKER:-/run/systemd/system}"
    SYSTEMD_UNIT=""
    if [[ -z "$SUPERVISOR_PROG" && -d "$SYSTEMD_MARKER" ]] && command -v systemctl >/dev/null 2>&1; then
        SYSTEMD_UNIT="$(systemctl list-units --type=service --no-legend --plain 2>/dev/null \
                        | awk '{print $1}' | grep -iE 'comfy' | head -1)" || true
    fi

    if [[ -n "$SUPERVISOR_PROG" ]]; then
        info "supervisord program '$SUPERVISOR_PROG' — restarting"
        if supervisorctl restart "$SUPERVISOR_PROG" >/dev/null 2>&1; then
            if comfy_wait_up 120; then
                ok "ComfyUI restarted on port $COMFY_PORT"
                RESTART_DONE=1
            else
                warn "restart issued but ComfyUI has not answered on port $COMFY_PORT within 120s"
                restart_banner "supervisorctl restart $SUPERVISOR_PROG   # then wait for it to come up"
            fi
        else
            warn "supervisorctl restart failed for '$SUPERVISOR_PROG'"
            restart_banner "supervisorctl restart $SUPERVISOR_PROG"
        fi

    elif [[ -n "$SYSTEMD_UNIT" ]]; then
        info "systemd unit '$SYSTEMD_UNIT' — restarting"
        if systemctl restart "$SYSTEMD_UNIT" >/dev/null 2>&1; then
            if comfy_wait_up 120; then
                ok "ComfyUI restarted on port $COMFY_PORT"
                RESTART_DONE=1
            else
                warn "restart issued but ComfyUI has not answered on port $COMFY_PORT within 120s"
                restart_banner "systemctl restart $SYSTEMD_UNIT"
            fi
        else
            warn "systemctl restart failed for '$SYSTEMD_UNIT'"
            restart_banner "systemctl restart $SYSTEMD_UNIT"
        fi

    else
        # Not supervised by anything this script can drive. Do not kill it:
        # there would be nothing to bring it back.
        COMFY_PID="$(pgrep -f 'main\.py' 2>/dev/null | head -1)" || true
        if [[ "$COMFY_PID" == "1" ]]; then
            warn "ComfyUI is PID 1 (the container entrypoint) — only a pod restart can reload it"
            restart_banner "Restart the pod from the RunPod / Vast dashboard."
        else
            warn "ComfyUI is running but not under supervisord or systemd — not touching it"
            restart_banner "Stop ComfyUI in the terminal or tab where you started it, then start it again."
        fi
    fi
fi

if [[ "$RESTART_DONE" == "1" ]]; then
    comfy_verify_nodes || warn "some node types did not register — see the list above"
elif [[ "$RESTART_NEEDED" == "0" ]]; then
    : # nothing running, nothing to verify
fi

SIZE_AFTER=$(dir_size "$COMFYUI_DIR/models")
DL_BYTES=$(( SIZE_AFTER - SIZE_BEFORE ))
(( DL_BYTES < 0 )) && DL_BYTES=0
TOTAL_T=$(( SECONDS - T_START ))
DL_GB=$(human "$DL_BYTES")
ALL_GB=$(human "$SIZE_AFTER")
if (( TOTAL_T > 0 && DL_BYTES > 0 )); then
    SPEED=$(awk "BEGIN{printf \"%.0f\", $DL_BYTES/1048576/$TOTAL_T}")
else
    SPEED=0
fi

printf '\n%s' "$C_B"
echo "=========================================================="
printf '  AIOFM · OFM Tech NSFW — setup done%s\n' "$C_0"
echo "=========================================================="
printf '  profile        : %s\n' "$PROFILE"
printf '  time           : %s\n' "$(hms $TOTAL_T)"
if (( DL_BYTES > 0 )); then
    printf '  downloaded     : %s  (~%s MB/s avg)\n' "$DL_GB" "$SPEED"
else
    printf '  downloaded     : nothing — everything was already on disk\n'
fi
printf '  models total   : %s in %s files\n' "$ALL_GB" "$TOTAL"
printf '  free space     : %s\n' "$(df -h "$COMFYUI_DIR" | awk 'NR==2{print $4}')"
# Truncated files are reported separately from "suspicious" ones because the
# fix is different: a short file resumes on re-run, a suspicious one has to be
# deleted first. Reporting only SUSPECT here would print "integrity: OK" over
# a half-downloaded 34 GB model, which is the exact failure this pass exists
# to catch.
if [[ "${TRUNCATED:-0}" -gt 0 && "${OVERSIZE:-0}" -gt 0 ]]; then
    printf '  integrity      : %s%s short + %s over-size — resume the short ones, delete the rest%s\n' "$C_R" "$TRUNCATED" "$OVERSIZE" "$C_0"
elif [[ "${TRUNCATED:-0}" -gt 0 ]]; then
    printf '  integrity      : %s%s short file(s) — re-run to resume them%s\n' "$C_R" "$TRUNCATED" "$C_0"
elif [[ "${OVERSIZE:-0}" -gt 0 ]]; then
    printf '  integrity      : %s%s over-size file(s) — delete them and re-run%s\n' "$C_R" "$OVERSIZE" "$C_0"
elif [[ "$SUSPECT" -eq 0 ]]; then
    printf '  integrity      : %sOK%s\n' "$C_G" "$C_0"
else
    printf '  integrity      : %s%s suspicious file(s) — delete them and re-run%s\n' "$C_R" "$SUSPECT" "$C_0"
fi
printf '  comfyui core   : %s\n' "${COMFY_STATUS:-unknown}"
# `cat` on a missing file exits non-zero, and an assignment takes the status of
# its command substitution -- so under `set -e` this aborted the whole script,
# AFTER the summary had already printed a clean install. The file is only
# written by the runtime node check, which needs ComfyUI to be answering; on a
# fresh pod it is not, and a fresh pod is the case this script exists for. So
# every clean first install ended in "Aborted at stage 14/13" with nothing
# actually wrong. `|| true` is the whole fix.
NODE_NEED_COUNT="$(cat "$NODE_COUNT_FILE" 2>/dev/null || true)"
if [[ "${NODE_FAIL:-0}" -eq 0 && -z "$NODE_NEED_COUNT" ]]; then
    # Static check passed; ComfyUI was not up, so nothing was verified against
    # a running instance. Say that rather than print "all ? present".
    printf '  workflow nodes : %sall packs present%s — verified on first start\n' "$C_G" "$C_0"
elif [[ "${NODE_FAIL:-0}" -eq 0 ]]; then
    printf '  workflow nodes : %sall %s present%s\n' "$C_G" "$NODE_NEED_COUNT" "$C_0"
else
    printf '  workflow nodes : %s%s missing — graph will show red nodes%s\n' "$C_R" "$NODE_FAIL" "$C_0"
fi
if [[ "${PIN_NODES:-1}" == "1" ]]; then
    printf '  node versions  : pinned\n'
else
    printf '  node versions  : %sunpinned (PIN_NODES=0)%s\n' "$C_Y" "$C_0"
fi
case "$FE_STATUS" in
    "pinned $FRONTEND_VERSION") printf '  frontend       : %s\n' "$FE_STATUS" ;;
    *)                          printf '  frontend       : %s%s%s\n' "$C_Y" "$FE_STATUS" "$C_0" ;;
esac
if [[ "${RESTART_NEEDED:-0}" == "0" ]]; then
    printf '  comfyui        : not running — nodes load on next start\n'
elif [[ "${RESTART_DONE:-0}" == "1" ]]; then
    printf '  comfyui        : %srestarted, nodes registered%s\n' "$C_G" "$C_0"
else
    printf '  comfyui        : %sRESTART REQUIRED — see the banner above%s\n' "$C_R$C_B" "$C_0"
fi
if (( WARNINGS > 0 )); then
    printf '  warnings       : %s%s%s (see above)\n' "$C_Y" "$WARNINGS" "$C_0"
fi
printf '  log            : %s\n' "$SETUP_LOG"
echo "=========================================================="

# --- anything still needing a manual step ---
NEEDS=()
# INSTARAW is only used by the NSFW workflow, which PROFILE=video does not pull
# models for. Flagging it on a video-only run makes a complete install look
# incomplete, so it is scoped to the profiles that actually need it.
#
# This is now a backstop rather than the normal path: the custom-nodes stage
# vendors the folder from beside this script. It only fires if the script was
# piped from curl with no pack beside it, in which case there is genuinely
# nothing to copy and the buyer does have to supply the folder.
if [[ "$PROFILE" != "video" ]]; then
    [[ -d "$COMFYUI_DIR/custom_nodes/ComfyUI_INSTARAW" ]] \
        || NEEDS+=("ComfyUI_INSTARAW — not found beside this script; copy the folder into custom_nodes (16 nodes in the NSFW graph need it, including the entry node #483)")
fi
BUILT="$(find "$WHEELDIR" -name 'sageattention*.whl' 2>/dev/null | head -1)"
[[ -n "$BUILT" ]] && NEEDS+=("upload the wheel once so it never rebuilds:
                 $HF_CMD upload $HF_REPO_ID $BUILT wheels/$(basename "$BUILT" 2>/dev/null)")

if (( ${#NEEDS[@]} > 0 )); then
    printf '%s  Still to do:%s\n' "$C_Y$C_B" "$C_0"
    for x in "${NEEDS[@]}"; do printf '   - %s\n' "$x"; done
    echo "=========================================================="
fi

printf '%s  Options:%s\n' "$C_B" "$C_0"
echo "   PROFILE=video   — only pull the Wan video models"
echo "   PIN_NODES=0     — track each node repo's default branch instead of"
echo "                     the pinned commits (pinned is the default)"
echo "   SAGE_INSTALL=0  — skip SageAttention"
echo "   FIX_ORT=0       — leave onnxruntime alone"
echo "   PIN_FRONTEND=0  — keep the pod image's ComfyUI frontend instead of"
echo "                     $FRONTEND_VERSION (subgraph widgets are version-sensitive)"
echo "   HF_WORKERS=N    — set the worker count manually"
echo "=========================================================="
