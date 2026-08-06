#!/bin/bash
# Wait for the whole Track V plan to finish, then run every analysis in one pass.
# Runner discipline: exactly one run_v.py at a time. This waits for the main chain
# (PID given as $1), then for the follow-up chain to start and finish.
set -u
MAIN_PID="$1"
count_runners() {
  ps -eo pid,cmd --no-headers | awk '$2=="/venv/main/bin/python" && /run_v.py/' | wc -l
}

echo "waiting for main chain PID $MAIN_PID"
while kill -0 "$MAIN_PID" 2>/dev/null; do sleep 30; done
echo "main chain done at $(date +%H:%M:%S); waiting up to 5 min for the follow-up chain to start"
for _ in $(seq 1 20); do
  [ "$(count_runners)" -ge 1 ] && break
  sleep 15
done
while [ "$(count_runners)" -ge 1 ]; do sleep 30; done
echo "ALL RUNNERS IDLE at $(date +%H:%M:%S)"
echo "arms recorded: $(ls -1 /workspace/nsfw-fix/results/crash/V/arms/*/meta.json 2>/dev/null | wc -l)"

cd /workspace/nsfw-fix
export OMP_NUM_THREADS=8
echo "===== ACCEPTANCE GRID ====="
/venv/main/bin/python results/crash/V/tools/v_check.py V_P4a 2>&1 | grep -v WARNING
echo "===== BAND MAP ====="
/venv/main/bin/python results/crash/V/tools/v_bandmap.py 2>&1 | grep -v WARNING
echo "===== INERTNESS PAIRS ====="
/venv/main/bin/python results/crash/V/tools/v_pairs.py \
  V_CLEAN_mid_16a=V_CLEAN_head_16a \
  V_CLEAN_mid_16a=V_CLEAN_mid_16b \
  V_CLEAN_head_16a=V_CLEAN_head_16b \
  V_CLEAN_mid_16b=V_CLEAN_head_16b \
  V_CLEAN_mid_40a=V_CLEAN_head_40a 2>&1 | grep -v WARNING
echo "===== DONE ====="
