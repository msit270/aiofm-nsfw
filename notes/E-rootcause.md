# TRACK E — why does a particular token count produce black?

**Status: in progress.** This file is being written as the arms land; the
mechanism paragraph goes at the top once it is established, not before.

## What is measured so far

1. **The conditioning is finite at every length.** Offline, through the graph's
   own encoder (`qwen.safetensors`, `CLIPType.LUMINA2` -> `ZImageTokenizer` /
   `Qwen3_4B`), token counts **12 through 80**: `isnan().any() == False`,
   `isinf().any() == False` on every one. `absmax` is ~13753 at every length and
   `std` falls smoothly with length. `results/crash/E/out/e1_cond.json`.
   **The encoder does not produce NaN. An encoder bug is refuted for lengths 12-80.**

2. **A single DiT forward is finite at every length.** `zimage.safetensors`
   loaded exactly as `620:113` loads it (bf16, `pad_tokens_multiple 32`), a
   latent at the face pass's real geometry `(1,16,357,251)`, one
   `diffusion_model()` call per conditioning at sigma 0.8, token counts 26-50:
   every output finite, `absmax` 4.78-4.81 and `std` 0.884 at **every** length,
   including 30, 31, 32, 44, 45, 46, 47.
   `results/crash/E/out/e2b_fwd_fwd.json`.

3. **The exact black IS consistent with a NaN, contrary to Track A's reading.**
   `ComfyUI-Impact-Pack/modules/impact/core.py:405` ends `enhance_detail` with
   ```python
   refined_image = utils.tensor_resize(refined_image, w, h)
   ```
   and `modules/impact/utils.py:129-141` implements that via
   `tensor2pil` -> `Image.fromarray(np.clip(255.*x, 0, 255).astype(np.uint8))`
   (`utils.py:153-155`). `np.clip` propagates NaN and the `uint8` cast turns it
   into **0**. So a NaN in the decoded crop is laundered into exact `(0,0,0)`
   **before** `620:114` returns, and `620:114`'s output is then honest,
   NaN-free zeros. Track A's inference "620:114 emitted honest zeros, not NaNs"
   is correct about the output tensor and does **not** rule out a NaN upstream
   of that line. This re-opens NaN as the mechanism.

## The gate — and it did NOT reproduce on a fourth instance

Track A's probe harness, unmodified (`results/crash/A/tools/{drive,mk,strings}.py`,
imported not copied), repointed at Track E's own ComfyUI on `127.0.0.1:32000`.

That server runs **from `/workspace/ComfyUI` itself** — the same directory,
the same core, the same `custom_nodes`, the same model files as `:18188`, with
the same `--disable-xformers` and the same `Using pytorch attention`. The only
additions are an extra `custom_nodes` search path, a private output/temp dir, an
in-memory DB, and `--disable-assets-autoscan`.

| arm | `620:106.text` | tokens | expected | got | prompt_id |
|---|---|---|---|---|---|
| `E_gate_crashstring` | the known-crashing string | 46 | crash at `622:403` | **success**, 64.2 s, `cached 0` | `6b8f9ec8-d2bf-4e24-8f5a-ffb898b20cdf` |
| `E_gate_placeholder` | `TRIGGER, PROMPT FOR YOUR MODEL` | 16 | clean | success, 62.0 s, `cached 0` | `c4d66821-b0ce-4f08-b5bd-8ab14094ac71` |

**Both halves clean.** Same frozen base image (`trackA_base137.png`), same probe
graph, same everything Track A ran on `:18188` where it crashed.

Instrumentation on that run (`/workspace/trackE/logs/probe.jsonl`) shows every
stage finite in **both** arms — conditioning, sampler latent, VAE decode, and the
image entering `tensor_resize`; `out_exact0 = 0`, i.e. not one exactly-black
pixel anywhere.

**So the reproducer is not a property of the installed bytes.** Track D found
that on a separately-built tree; this finds it on the *same* tree, which removes
"different custom-node versions" as the explanation.

**[I] The leading hypothesis this creates, and the next arm tests it:** Track E's
probe pack wraps `VAE.decode`, `KSAMPLER.sample` and `CLIP.encode_from_tokens`
with tensor reductions, and a reduction on a CUDA tensor is a **synchronisation
point**. Both `:18188` and `:32000` log `Using async weight offloading with 2
streams`. If the fault is a stream-ordering race, adding syncs would suppress it,
and a race would also explain length-banding (shapes set kernel durations),
content-independence (timing does not depend on values), bit-identical crashing
frames (a stable race is deterministic), and Track B's `622:398` result (a
downstream prompt that changes what is resident before the face pass).
**Not established. The control is: same server, probe pack removed.**
