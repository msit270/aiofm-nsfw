# Track B — the factor grid on the face-prompt crash

**Server: `127.0.0.1:28191` only** (`/workspace/comfy-r2gate3`, `--reserve-vram 16`).
Every arm and every control below ran there. Nothing here ran on 18188 and no
result from 18188 is mixed into a comparison.

**Graph frozen.** `OFMTech-NSFW/OFMTech_NSFW.json` is untouched
(`sha256 a811b5d690ccc5207bc7bd1c626cdd3db3b720b9be60d0a687436efcfd2143d8`,
checked before the first arm and after the last). Every arm is an in-memory
mutation of an already converted API graph:
`results/r4/R4_CF15_filled/api_graph.json` (crashing string) or
`results/r4/R4_CF15_placeholder/api_graph.json` (placeholder). Those two files
differ in `620:106.inputs.text` and **nothing else** — verified by a full
input-wise diff, not by eye.

Every arm: `POST /free {"unload_models":true,"free_memory":true}` first, a fresh
`client_id`, `execution_cached` confirmed `[]`. Nothing was ever deleted from the
queue. Arms, `api_graph.json`, `history.json`, `meta.json` and images are under
`results/crash/B/<arm>/`.

---

## Verdicts, one line per letter

*(filled in as cells complete; a cell not listed in the grid below was NOT RUN)*

---

## The baseline — the crash reproduces on 28191, and the clean render is bit-identical to 18188's

| cell | what varied | prompt_id | status | cached | exception node |
|---|---|---|---|---|---|
| `A0_baseline_crash` | nothing — shipping graph, both LoRAs, `#106` = the crashing string | `0e24d1c3-cd96-4837-a420-ebbb819207a7` | **error** 254.8 s | 0 | **`622:403 MaskBoundingBox+`** `RuntimeError` |
| `A1_baseline_clean` | `#106` = shipped placeholder | `c75e0d28-1a10-4d84-98e3-f4bf87816d8c` | success 306.6 s | 0 | — |

`A0`'s exception is Phase 0's, field for field:

```
node_id 622:403  node_type MaskBoundingBox+  RuntimeError
min(): Expected reduction dim to be specified for input.numel() == 0.
custom_nodes/ComfyUI_essentials/mask.py:184   x1 = max(0, x.min().item() - padding)
current_inputs.mask = tensor([[[0., 0., 0., ...]]])   <- all zero
```

The only textual difference from Phase 0's traceback is the install path:
28191 runs out of **`/workspace/comfy-r2gate3`**, not `/workspace/ComfyUI`.
`ComfyUI_essentials/mask.py` is byte-identical between the two
(`sha256 ec8ca8d3fb3614f529b9fdfbb4f511f3a72d3207bc21ff7c54e422b887749af0`), so
it is the same crash site in the same code.

**The two servers agree bit for bit on this graph.** `A1`'s image against the
18188 render of the same api_graph (`results/r4/R4_CF15_placeholder/HasMetadata_00059_.png`):

```
max_abs_diff 0    mean_abs_diff 0.0    mse 0.0    psnr inf     over 2688x3456x3
```

That is stronger than the brief assumed was available. It does not license
mixing 18188 numbers into my tables — timings still are not comparable and I
have not tested a second graph — but for *this* graph the render is reproduced
exactly, so my baseline is anchored to the same artifact the existing evidence
came from.

**Health metric.** Mine is a fresh implementation and its numbers are **not** on
the same scale as the R4 session's. On the byte-identical image above, R4
reported `flat_frac 0.0030 / luma_sd 37.38` and mine reports
`flat_frac 0.03088 / luma_sd 59.505`. Only compare my numbers to my own healthy
reference, which is that pair. `flat_frac` = fraction of pixels with zero
luma gradient to both neighbours; `luma_sd` = sd of luma over the whole frame;
`suspect_poisoned` = `flat_frac > 0.20 or luma_sd < 8`.

---

## Grid

| cell | what varied vs the crashing configuration | prompt_id | status | cached | exception node |
|---|---|---|---|---|---|

