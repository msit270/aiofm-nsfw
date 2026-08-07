# DoD 4 — CLIPLoader device assertion, negative test (2026-08-07)

Two assertions added to aiofm_setup.sh:
1. Static, "ComfyUI core version" stage: regex the CLIPLoader class block of
   $COMFYUI_DIR/nodes.py for the optional "device" input; `die` with a message
   naming the black-face fix (620:110 device=cpu, commit 7ce1539) if absent.
2. Runtime, comfy_verify_nodes(): /object_info CLIPLoader.input.optional.device
   must exist on the server that will execute the graph; exit 2 + FATAL text.

Negative test (this file's terminal record, run this session):
- bash -n aiofm_setup.sh -> SYNTAX_OK
- assertion vs /workspace/ComfyUI/nodes.py (real 0.15.1 tree) -> exit 0 PASS
- assertion vs doctored copy with the optional-device block stripped
  (the pre-v0.3.11 CLIPLoader shape) -> exit 1 FAIL, as required.
Upstream introduction: ComfyUI commit 5cbf7978 "Add advanced device option to
clip loader nodes", first tag v0.3.11 (2025-01-05). COMFY_MIN in the script is
0.3.70 — the version floor already implies the capability when the version
string is honest; the capability check catches trees where it is not.
