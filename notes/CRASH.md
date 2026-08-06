# The face-prompt crash — investigation

**Status: Phase 0 COMPLETE.** The exception exists in writing, verbatim, below.

---

## Phase 0 — the exception

Recovered from ComfyUI's own `/history` record of the crash run
`dd94393a-9b61-4d03-9a4b-70f314311b29` — arm `R4_CF15_filled`, the **shipping**
graph (`a811b5d6…`, `#114` cf 1.5), both LoRAs loaded, `execution_cached: []`
(cold). This is the stored record of the run that crashed, not a re-creation.

```
node_id        : 622:403
node_type      : MaskBoundingBox+
exception_type : RuntimeError
exception_message:
    min(): Expected reduction dim to be specified for input.numel() == 0.
    Specify the reduction dim with the 'dim' argument.
```

**Traceback, complete and unedited:**

```
  File "/workspace/ComfyUI/execution.py", line 524, in execute
    output_data, output_ui, has_subgraph, has_pending_tasks = await get_output_data(
        prompt_id, unique_id, obj, input_data_all,
        execution_block_cb=execution_block_cb, pre_execute_cb=pre_execute_cb, v3_data=v3_data)

  File "/workspace/ComfyUI/execution.py", line 333, in get_output_data
    return_values = await _async_map_node_over_list(
        prompt_id, unique_id, obj, input_data_all, obj.FUNCTION, allow_interrupt=True,
        execution_block_cb=execution_block_cb, pre_execute_cb=pre_execute_cb, v3_data=v3_data)

  File "/workspace/ComfyUI/execution.py", line 307, in _async_map_node_over_list
    await process_inputs(input_dict, i)

  File "/workspace/ComfyUI/execution.py", line 295, in process_inputs
    result = f(**inputs)

  File "/workspace/ComfyUI/custom_nodes/ComfyUI_essentials/mask.py", line 184, in execute
    x1 = max(0, x.min().item() - padding)
                ^^^^^^^
```

**Inputs at the failure point**, as recorded by the server:

```
padding : 0
blur    : 0
mask    : tensor([[[0., 0., 0.,  ..., 0., 0., 0.],
                   [0., 0., 0.,  ..., 0., 0., 0.],
                   ...
                   [0., 0., 0.,  ..., 0., 0., 0.]]])      <- all zero, 3-D (1,H,W)
```

64 nodes had executed; the graph died 248.8 s in.

### The node-level mechanism is exact, and it is NOT what we have been saying

`ComfyUI_essentials/mask.py`, `MaskBoundingBox+.execute`:

```python
183    _, y, x = torch.where(mask)
184    x1 = max(0, x.min().item() - padding)
185    x2 = min(mask.shape[2], x.max().item() + 1 + padding)
186    y1 = max(0, y.min().item() - padding)
187    y2 = min(mask.shape[1], y.max().item() + 1 + padding)
```

**Correction to the wording carried in `HANDOFF.md` §6.0 and `notes/R4-defects.md`:**
the crash is *not* `.min()` on an all-zero mask — `torch.zeros(3,3).min()` returns
`0.0` quite happily. It is `.min()` on an **empty index tensor**. `torch.where(mask)`
on an all-zero mask returns three *zero-length* tensors, so `x.numel() == 0` and
line 184 raises. The distinction matters because it tells you the failure is
upstream detection returning **nothing**, not a mask full of zeros being
mishandled — and any fix has to restore a detection or handle "no detection",
not sanitise mask values.

The message text confirms it: `input.numel() == 0`.

### The chain that feeds it

Walked from the crash arm's own submitted `api_graph.json`, not from the editor:

```
622:403  MaskBoundingBox+          <- CRASHES
  .mask
622:407  SegsToCombinedMask         (empty SEGS -> all-zero mask)
  .segs
622:424  BboxDetectorSEGS           threshold 0.6, dilation 10, crop_factor 3,
  .bbox_detector                     drop_size 10, labels 'all'
622:426  UltralyticsDetectorProvider  bbox/face_yolov8m.pt
  .image
622:431  INSTARAW_ImageListFromBatch
621:163  ImageColorMatch+
620:165  FaceDetailer               the MOUTH pass  (steps 8, cfg 1, denoise 0.35)
620:111  ImageColorMatch+
620:114  FaceDetailer               the FACE pass   (steps 8, cfg 1, denoise 0.80)
  .positive
620:106  CLIPTextEncode             <- THE PROMPT UNDER TEST
  .clip
620:110  CLIPLoader                 qwen.safetensors, type lumina2
```

**So the immediate cause is that the Eyes stage's face detector
(`face_yolov8m.pt` @ threshold 0.6) finds no face at all** in the image handed to
it, and the graph has no guard for "detector found nothing".

`620:106` reaches the pipeline through exactly one path: `620:114.positive`. It is
a `CLIPTextEncode` on the **lumina2** encoder, shared with `620:105` (negative,
empty), `621:166`/`621:167` (mouth).

### What this does and does not establish

- **Established:** the node, the line, the exception, the empty-index mechanism,
  and that the mask arrives all-zero from `SegsToCombinedMask`.
- **Established:** the crash is a *detection* failure, not a mask-arithmetic bug.
- **NOT established:** why a longer prompt causes the detector to find no face.
  Everything below Phase 0 is open.

### Two hypotheses this trace does not distinguish [I]

1. **The face pass damages the image** until YOLO no longer sees a face. `620:114`
   runs at **denoise 0.80** with the test prompt as its *only* conditioning
   (cfg 1). A prompt that pulls the sample far from a face would do it.
2. **A conditioning-shape problem** in the lumina2 encoder path, per the brief.
   Not yet examined.

Note in favour of neither yet: `620:648 SEGSRangeFilterDetailerHookProvider`
(`max_value 1700000`) is attached to `620:165`, the **mouth** pass — it is *not*
in the path of `622:424`, so it cannot empty this mask directly. It can only make
the mouth pass a no-op. Phase 1E still worth running, but the wiring says it is
not the direct cause.

---

## Efficiency note for Phase 1 — the base image is prompt-independent

Everything up to and including `620:137` (`ImageColorMatch+`, the input to the
face pass) depends on `#106` **not at all** — `620:106` feeds only
`620:114.positive`. The SDXL side uses its own prompts (`587:93`, `587:506`,
`587:508`, `587:509`).

That means a bisection does not need a ~250 s full render per arm: render the
base **once**, then drive only `620:114` → `620:165` → `621:163` → `622:424` per
arm. **Any such probe must first be validated** by reproducing crash-on-the-known-
crashing-string and clean-on-the-placeholder, or its results mean nothing.
