# Track-2 (quality menu) GPU protocol — binding for every Q agent

Track 1 (licensing) owns the pod. Track 2 renders only under these rules.
Cross-contamination voided six arms in an earlier run; the NaN incident
poisoned a long-lived server. Both histories are why this is strict.

## The lock

- Every GPU-touching step (server boot → render → collect → shutdown) runs
  under an exclusive `flock` on `/workspace/nsfw-fix/.gpu_lock`:

      exec 9>/workspace/nsfw-fix/.gpu_lock
      flock 9          # blocks until free — that is the design
      … arm …
      flock -u 9

  In Python: `fcntl.flock(open('/workspace/nsfw-fix/.gpu_lock','w'), fcntl.LOCK_EX)`.
- Track 1's fresh-install gate takes the same lock for its whole window.
  If you block on it for an hour, that is correct behaviour, not a hang.
- Hold the lock for one arm at a time. Never across analysis-only work.

## The arm server (never 18188)

- The main instance `127.0.0.1:18188` is off-limits: no `/prompt`, no
  `/queue`, no `/free`, no `/interrupt`, no restart, nothing. (`/free` is
  racy; a queue clear leaves no history — both bit earlier runs.)
- Each arm gets a FRESH process:

      cd /workspace/ComfyUI && nohup python3 main.py --port 19188 \
        --disable-auto-launch --output-directory /workspace/trackQ/output \
        > /workspace/trackQ/server_<arm>.log 2>&1 &

  Wait for `GET 127.0.0.1:19188/system_stats` to answer, run the ONE arm,
  save evidence, then `kill` the process and wait for it to exit before
  releasing the lock. Fresh process per arm = cold by construction and NaN
  poisoning cannot cross arms.
- Confirm cold from the history entry: `execution_cached` must be empty.
  Record it with the arm.
- Before booting, check `nvidia-smi --query-gpu=memory.free` ≥ 50000 MiB.
  Below that, wait 60 s and re-check (the gate may be running). Never try
  to free VRAM yourself.

## The graph

- Base every arm on `results/run3/guard/api_guarded.json` (the current
  shipping bytes, guarded conversion) mutated the way
  `results/run3/tools/r3.py` does it — `v_mk.norm`, `v_mk.set_loras`, text
  into `620:106`, `619:603.pick_list = "0"` so no selector blocks the run.
  Buyer-default values live in `results/run3/fresh/fresh-buyer-api_graph.json`.
- One variable per arm. The baseline arm is rendered in the same session
  batch as its comparisons, fixed seeds, and appears ON the sheet labelled
  as baseline.
- Do not edit anything in `OFMTech-NSFW/`, the workflow JSON, or `dist/`.
  Track 2 is recommend-only. Copies live under `/workspace/trackQ/`.

## Evidence

- Per arm: the submitted graph, the history entry (timings +
  `execution_cached`), the output PNG(s), server log. Under
  `results/run4/quality/<agent>/<arm>/`.
- Contact sheets: every tile labelled with what changed and its measured
  server-side execution time; the baseline tile explicitly marked. A sheet
  without a labelled baseline is discarded. `results/run3/tools/analyze.py`
  and `tools/contact_sheet.py` are the starting points (contact_sheet.py
  detects the face box per image — never reuse a fixed crop box).
- Any model file you recommend (detector, upscaler, encoder, anything):
  licence flags read from an API THIS SESSION (Civitai
  `/api/v1/model-versions/by-hash/` + `/api/v1/models/<id>`, or the HF API),
  raw response stored under `results/run4/quality/licences/`. A
  recommendation without stored flags is discarded.
- Timing comparisons only between arms with matching cache state (fresh
  process per arm gives you that for free).

## Settled — do not re-litigate in the menu

`#114` steps 8 / denoise 0.35 is the SHIPPED BASELINE (owner decision).
Arms may explore around it for the menu, labelled as recommendations, but
no menu entry may present "change the shipped default" as already decided.
cfg on the three Z-Image passes stays 1 — guidance-distilled Turbo model;
raising it is a known-bad suggestion (HANDOFF §5 / STATE §8). D1 stays
reverted. The two-LoRA design stands. The crash guard stands.
