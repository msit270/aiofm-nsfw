# Agent D — black-render verdict (2026-08-08, matrix complete)

## The replay matrix (results/run5/Dmatrix/matrix.json; fresh cold boot per
## row; probe set = the session's known failers + a never-failed canary)

| arm | boots | probes | outcome |
|---|---|---|---|
| baseline (stock flags) | 2 | 10 | 10/10 healthy |
| --use-pytorch-cross-attention (xformers off) | 2 | 10 | 10/10 healthy |
| --disable-async-offload | 2 | 10 | 10/10 healthy |
| CUBLAS_WORKSPACE_CONFIG=:4096:8 | 2 | 10 | 10/10 healthy |
| --force-fp32 (standalone) | 1 | 5 | 5/5 ERROR — xformers has no fp32 memory-efficient kernel; the flag REQUIRES pairing with --use-pytorch-cross-attention on this stack |

## The honest conclusion

THE FAILURE DID NOT REPRODUCE. The exact graphs that black-framed earlier
(A0_PT: 2/2 boots black-faced; lunaz30: 3/4; zref_PT/CU) rendered healthy
on every boot tonight, under stock flags. Therefore:
- No root cause is PROVEN, and no toggle earns credit. Anyone claiming a
  fix from this matrix would be lying with statistics.
- What IS established: (a) the failure is an environmental, boot/time-
  clustered die, not a property of any graph or config — every one of the
  session's 7 failures fell in one ~2-hour window, and 0/40 replays hit
  it hours later; (b) session-wide rate revised: 7 in ~150 Z-renders
  (~5%), clustered; (c) all four mitigation flags are compatibility-
  proven (render correctly), so adopting them costs nothing.

## Recommendation (adopted into README-PERSONAL)

Run daily with `--disable-async-offload` and
`CUBLAS_WORKSPACE_CONFIG=:4096:8` — the two flags aimed at the strongest
mechanism hypothesis (ComfyUI's default 2-stream async offload meets
cuBLAS's documented multi-stream nondeterminism; torch 2.10 ships the
thread-safety fix). Belt-and-braces, not a proven cure. If a black frame
appears anyway: restart ComfyUI, re-render — cleared every single
occurrence this session. Structural path: the V10 core-upgrade session
lands torch 2.10 + current ComfyUI (which also reorders SDPA backends);
re-run this matrix there. Upstream watch: Comfy-Org/ComfyUI#15110.
Research (mechanisms, upstream diffs, local code reads):
results/run5/research_black/.
