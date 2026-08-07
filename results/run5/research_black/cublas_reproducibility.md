Source: https://docs.nvidia.com/cuda/cublas/index.html (fetched 2026-08-08 via WebFetch)
Quotes (reproducibility section):
- "all cuBLAS API routines from a given toolkit version, generate the same bit-wise results at every run when executed on GPUs with the same architecture and the same number of SMs."
- The guarantee DOES NOT HOLD "when multiple CUDA streams are concurrently active" - the library "may optimize performance by selecting different internal implementations for parallel operations".
- Mitigations listed by NVIDIA: separate workspace per stream via cublasSetWorkspace(); one handle per stream; env CUBLAS_WORKSPACE_CONFIG=:16:8 or :4096:8; cublasLtMatmul with user-owned workspace.
- Atomics-based routines (symv/hemv) are never bitwise reproducible.
Relevance: ComfyUI 0.15.1 enables async weight offloading with 2 CUDA streams BY DEFAULT on NVIDIA (comfy/model_management.py:1070-1083); multi-stream is therefore active during model load/offload juggling (FaceDetailer swaps UNET/TE/SAM/detector), which voids run-to-run cuBLAS bitwise reproducibility across process boots while staying self-consistent within a boot (algorithm choice is cached per handle).
