# TRACK E — why does a particular token count produce black?

## The mechanism, in one paragraph

**`620:114 FaceDetailer` is bistable, and which of its two states you land in is
decided by the last few digits of `620:106`'s conditioning — not by anything
semantic, and not by anything in the graph.** The pass either returns a normal
face or returns a face-shaped region of exactly `(0,0,0)`; there is nothing in
between, and the black state is byte-for-byte the same whatever the prompt was.
The black itself is manufactured at one line: `enhance_detail` finishes with
`utils.tensor_resize(refined_image, w, h)`
(`ComfyUI-Impact-Pack/modules/impact/core.py:405`), which goes through
`tensor2pil` → `Image.fromarray(np.clip(255.*x, 0, 255).astype(np.uint8))`
(`utils.py:153-155`). `np.clip` propagates NaN and the `uint8` cast turns it into
`0`; any value ≤ 0 also clips to `0`. So whatever went wrong inside the pass —
a NaN or a strongly negative decode — is converted to exact black *before*
`620:114` returns, and the node can only ever hand out honest, NaN-free zeros.
**Which state you get is a property of the process, not of the files.** A fourth
ComfyUI started from the *same* `/workspace/ComfyUI` directory as `:18188`, with
the same core, the same `custom_nodes`, the same model bytes and the same
`Using pytorch attention`, does not reproduce the failure in **10 cold arms
across four server configurations**, while `:18188` crashed **9 out of 9** in the
same window — and the two servers produce **bit-identical** output
(`max_abs_diff 0` over 2688×3456×3) on the clean placeholder arm. On `:18188`
the state can be flipped at will, in either direction, by changing where the
conditioning is computed: `620:110 CLIPLoader.device = "cpu"` gives a healthy
face **7/7**, interleaved against **9/9** crashes with the shipped GPU encoder,
and the CPU/GPU conditioning differ by `max 0.0059` on a tensor whose `absmax` is
`13753` — a relative difference of about `4e-7`.

**What I did not manage to do, and it is the one thing the brief asked for
first:** I could not read the tensor inside the failing pass on the instance that
fails. `:18188` is the only reproducer any Track E arm could find, it cannot be
instrumented without restarting it, and every instance I *could* instrument
refuses to fail. So "NaN or real zeros" is answered by the code path and by the
character of the output, not by a direct `isnan()` on the failing tensor. Say
so when quoting this.

---

## The one-widget workaround, which is the useful part of this file

`620:110 CLIPLoader` has a `device` widget (`nodes.py:982`). Setting it to
**`cpu`** cures the crash on the only instance that has it.

| `620:110.device` | arms | result |
|---|---|---|
| `default` (shipped, cuda:0) | 9 | **error `622:403` 9/9** |
| `cpu` | 7 | **success 7/7, healthy image 7/7** |

Interleaved, on a server whose health is attested on both sides, exactly one
widget apart. And "success" here is not the weak kind Track A warned about
(`E398_tok31` shipped a success with black eye-holes): the cured arms measure
`flat_frac 0.0748`, modal colour `(255,255,255)` at 2.39 % and **PSNR 48.9 dB
against the known-good placeholder render** — i.e. a real face, at this
project's own measured run-to-run floor of ~48.7 dB. The crashing arms measure
`flat_frac 0.2387`, modal `(56,51,47)` at **16.97 %**, PSNR **14.33 dB**.
Numbers for every arm: `results/crash/E/out/e9_images.json`.

Sheet: **`results/crash/E/E_cpuclip_sheet.png`** — the same face box from the
crashing arm, the cured arm and the control, at 1:2, same pixel region. I am not
judging the images; the panels are there because the owner reads them. The
measurements are the table above.

**Cost.** The encoder runs on the CPU: ~+15–30 s per render on this box
(cured arms 66.9–71.8 s against 36.4–46.3 s for the crashing ones — but the
crashing ones die early, so compare against the 53.6 s clean control: about
+14 s). It is a one-widget change to a loader, it does not touch the sampler, and
it is the only thing measured in this session that turns the failure off.

**[I] It is a workaround, not a fix, and I would not ship it without the pod
confirming it on an instance where the crash is first shown to reproduce.** It
also does not fix the second defect — `622:403 MaskBoundingBox+` still turns
"detector found nothing" into a `RuntimeError`.

---

## 1. Is the black a NaN or real zeros?

**Not measured directly. Here is exactly what is and is not established.**

### Established, from source: `620:114` cannot report a NaN even if it has one

`ComfyUI-Impact-Pack/modules/impact/core.py`, end of `enhance_detail`:

```python
405    refined_image = utils.tensor_resize(refined_image, w, h)
407    refined_image = refined_image.cpu()
411    return refined_image, cnet_pils
```

`modules/impact/utils.py:129-141`, `tensor_resize`, taken for any image with
≥3 channels:

```python
135            single_pil = tensor2pil(single_image)
136            scaled_pil = single_pil.resize((w, h), resample=LANCZOS)
138            single_image = pil2tensor(scaled_pil)
```

and `utils.py:153-155`:

```python
def tensor2pil(image):
    return Image.fromarray(np.clip(255. * image.cpu().numpy().squeeze(0), 0, 255).astype(np.uint8))
```

`np.clip` propagates NaN, and the `uint8` cast of a NaN is `0` on x86-64. Any
value `≤ 0` also clips to `0`. This runs **unconditionally** — even when
`upscale == 1.0` and `new_w == w`, as it is here (`crop region (2010, 2859) x 1.0
-> (2010, 2859)`), the PIL round-trip still happens.

**Consequence: Track A's NaN refutation does not hold.** `notes/A-length-vs-content.md`
argues that because `620:111 ImageColorMatch+` would have `nan_to_num`'d the
whole frame to a constant and did not, `620:114` "emitted honest zeros, not
NaNs". That is correct **about `620:114`'s output tensor** and says nothing about
what was inside the pass — the launder happens one line before the return. NaN is
back on the table, and so is a saturated-negative decode.

### Established, by elimination: it is not the encoder and not a single DiT forward

* **The conditioning is finite at every length.** Offline, through the graph's
  own encoder (`qwen.safetensors` → `TEModel.QWEN3_4B` →
  `comfy.text_encoders.z_image.ZImageTokenizer` / `Qwen3_4BModel`, loaded exactly
  as `620:110` loads it), token counts **12 through 80**:
  `isnan().any() == False`, `isinf().any() == False`, `absmax ≈ 13753` at every
  length, `std` falling smoothly. `results/crash/E/out/e1_cond.json`.
* **One DiT forward is finite at every length.** `zimage.safetensors` loaded as
  `620:113` loads it (bf16, `pad_tokens_multiple 32`), latent at the face pass's
  real geometry `(1,16,357,251)` — which the in-graph tap confirms is the real
  shape — one `diffusion_model()` call per conditioning at sigma 0.8, token
  counts **26–50**: every output finite, `absmax` 4.78–4.81 and `std` 0.884 at
  every length including 30, 31, 32, 44, 45, 46, 47.
  `results/crash/E/out/e2b_fwd_fwd.json`.

### Strong circumstantial: the output is not "the model painted a face black"

Track A measured **one unique colour, exactly `[0,0,0]`, over a 600×600 patch**
(360,000 pixels) and 16.94 % of the frame. A VAE decode is continuous; quantised
to 8 bits it produces 0s and 1s and 2s, not 360,000 exact zeros. A single
saturating clip does produce exactly that. **[I] So the decoded crop was either
non-finite or ≤ 0 over the whole face region.** Both are numerical blowup. What
it is *not* is a diffusion model drawing something dark.

### Why I could not close it

`gdb`-based injection into the live `:18188` was blocked by this session's
permission system, and I did not attempt to work around it. Restarting `:18188`
with a probe pack would have instrumented it, but on the evidence in §3 there was
a real chance the reproducer would not survive the restart, and it is the only
one this session could reach that I am allowed to submit to. I judged the
reproducer worth more than the measurement. **This is the single highest-value
arm left and it is written up for the pod in `notes/E-questions.md`.**

---

## 2. Where do clean and crashing first diverge?

**Not answered, and I want to be blunt about why: I could only instrument
instances that do not diverge at all.**

Track E's probe pack (`/workspace/trackE/custom_nodes/trackE_probe/__init__.py`)
wraps `comfy.sd.VAE.decode`, `comfy.samplers.KSAMPLER.sample`,
`comfy.sd.CLIP.encode_from_tokens` and `impact.utils.tensor_resize` and records
`nan`/`inf`/min/max/`exact0` for every tensor through them. On `:32000` it
produced a complete trace for both the 46-token crash string and the 16-token
placeholder — and **every stage was finite in both**, with `out_exact0 = 0`
(not one exactly-black pixel anywhere) and identical latent geometry
`(1,16,357,251)`. Trace: `/workspace/trackE/logs/probe.jsonl`.

What the elimination above *does* narrow it to: not the encoder, not one DiT
forward. That leaves the 8-step `euler_ancestral` / `kl_optimal` sampling loop at
`denoise 0.80` inside `620:114`, or the VAE decode of its result. **[I]**

---

## 3. The reproducer is a property of the process, not the files

This is the biggest thing in this file after the workaround.

Track E stood up its own ComfyUI **from `/workspace/ComfyUI` itself** — the same
directory `:18188` runs from, so the same core, the same `custom_nodes`, the same
model files, and the same `--disable-xformers` / `Using pytorch attention`. Only
port, output/temp dirs, an in-memory DB and `--disable-assets-autoscan` differ.
Track A's probe harness was imported, not rebuilt (`results/crash/E/tools/e_drive.py`
sets `drive.SERVER`, `drive.ROOT`, `drive.COMFY_OUT` on Track A's own module).

| server | config | crash-string arms | result |
|---|---|---|---|
| `:32000` | + probe pack | 1 | success |
| `:32001` | no probe pack, partial load (39 lowvram patches) | 1 | success |
| `:32001` | no probe pack, **full load**, 48.7 GiB free | 1 | success |
| `:32002` | `--reserve-vram 16` (Track B's reproducing config) + probe | 1 | success |
| `:32003` | `--use-sage-attention` | 1 | success |
| **`:18188`** | shipped | **9** | **error `622:403` 9/9** |

Every arm cold (`execution_cached: []`). Nothing here touched `:28191` or
`:31910` other than reading `/system_stats`, `/proc/<pid>/cmdline` and
`/proc/<pid>/environ`.

**And the two disagreeing servers are numerically identical on the clean path.**
`A1_gate_placeholder` on `:18188` (Track A) vs `E_gate_placeholder` on `:32000`:
`max_abs_diff 0` over 2688×3456×3. Also `E_rv16_placeholder` on `:32002` vs
`E18_placeholder_ctl` on `:18188`: PSNR 99, i.e. identical. So this is not "two
boxes with different kernels". They agree bit-for-bit until the prompt lands in a
band, and then one of them collapses and the other does not.

### What is NOT the discriminator (each tested, not assumed)

* **The code tree.** Same directory. `diff -rq` of `/workspace/comfy-d-gate`
  (does not reproduce) against `/workspace/comfy-r2gate3` (reproduces) shows only
  `.git` metadata and `__pycache__`; no source difference. Nine `.py` files under
  `custom_nodes/ComfyUI_INSTARAW` have mtimes after `:18188` started, but their
  content is identical to the frozen `OFMTech-NSFW/ComfyUI_INSTARAW` copy.
* **The environment.** `/proc/<pid>/environ` diffed across all four. `:28191`
  (reproduces) and `:31910` (does not) have **identical** environments — both
  launched from an agent shell — and both differ from `:18188` only in shell
  noise. Nothing numerically relevant (`PYTORCH_CUDA_ALLOC_CONF`, `OMP_NUM_THREADS`,
  `LD_PRELOAD`) tracks the split.
* **The allocator.** All four report `cudaMallocAsync` in the device name.
* **The attention backend at ComfyUI level.** All four log `Using pytorch
  attention`; `comfy/ldm/modules/attention.py:724-742` selects it because
  `--disable-xformers` leaves `pytorch_attention_enabled()` true.
* **VRAM pressure.** `E18_tok30_gpuclip` crashed with **49.9 GiB free**; the
  identical graph on `:32001` with 48.7 GiB free rendered clean. And `:32001`
  rendered clean at 15.9 GiB free too. Free VRAM does not predict either way.
  (This corroborates Track B's withdrawal.)
* **Full load vs lowvram.** The crashing arm on `:18188` and every clean arm on
  `:32001`/`:32002` all show `full load: True, lowvram patches: 0` for Lumina2 in
  the face pass at least once. Also tested `:32001` *with* 39 lowvram patches —
  clean.
* **`--reserve-vram 16`.** `:28191` has it and reproduces; `:31910` has it and
  does not; `:18188` does not have it and reproduces; `:32002` has it and does
  not.
* **Track E's own instrumentation.** My first thought was that the probe's
  tensor reductions inserted CUDA synchronisation points and suppressed a
  stream-ordering race. **Refuted:** `:32001` with the probe pack removed is
  still clean, 2/2.

### What differs between `:18188` and Track D's `:31910` (question (d))

Nothing I can find that could change numerics:

```
                :18188                          :31910 (Track D)
cwd             /workspace/ComfyUI              /workspace/comfy-d-gate
argv            --disable-auto-launch           --disable-auto-launch
                --disable-xformers              --disable-xformers
                --port 18188                    --port 31910 --listen 127.0.0.1
                --enable-cors-header            --enable-cors-header --reserve-vram 16
comfyui         0.15.1                          0.15.1
torch           2.9.1+cu128                     2.9.1+cu128
python          3.12.12 (same /venv/main)       3.12.12 (same /venv/main)
allocator       cudaMallocAsync                 cudaMallocAsync
attention       Using pytorch attention         Using pytorch attention
TE dtype        float16, cuda:0                 float16, cuda:0
DiT dtype       bfloat16 (model_type FLOW)      bfloat16
models          hardlinked, same bytes          hardlinked, same bytes
```

`--reserve-vram 16` is the only argv difference, and it is not the
discriminator (see above). **[I] The difference lives in per-process runtime
state — most plausibly a kernel/algorithm selection made once per process for
the shapes this pass uses. I have no direct evidence for that and will not
dress it up as more than a guess.**

---

## 4. The conditioning experiments — what actually flips it

Three arms, each one input apart from the crashing arm, all on `:18188`.

### E3/E3b/E6 — where the conditioning is COMPUTED decides it

`620:110.device = "cpu"` makes `CLIPLoader.load_clip` set
`model_options["load_device"] = ["offload_device"] = torch.device("cpu")`
(`nodes.py:995-996`). Weight dtype stays `torch.float16` in both cases — the
server log says so for both — so this is a device change, not a dtype change.

```
E18_alt1_gpuclip_crash   ERROR 622:403   41.6 s   cached 0
E18_alt2_cpuclip_crash   success         66.9 s   cached 0
E18_alt3_gpuclip_crash   ERROR 622:403   39.6 s   cached 0
E18_alt4_cpuclip_crash   success         69.9 s   cached 0
```

and in the **other** band, 30 tokens, Track A's own `"a woman's face" + 18×" the"`:

```
E18_tok30_gpuclip        ERROR 622:403   36.4 s   cached 0   (49.9 GiB free)
E18_tok30_cpuclip        success         69.1 s   cached 0
E18_tok30_gpuclip_b      ERROR 622:403   38.6 s   cached 0
E18_tok30_cpuclip_b      success         67.0 s   cached 0
```

### E4 — and the difference between the two conditionings is pure rounding

Both encoders loaded offline from the same file, same fp16 weights, conditioning
compared element-wise:

| prompt | tokens | `max abs diff` | `mean abs diff` | `absmax` of the tensor | finite? |
|---|---|---|---|---|---|
| placeholder | 16 | 0.0078 | 8.3e-06 | 13753.5 | both |
| crash string | 46 | 0.0059 | 9.0e-06 | 13753.5 | both |
| `tok30` | 30 | 0.00098 | 7.2e-06 | 13753.5 | both |
| `tok44/45/46` | 44/45/46 | 0.0059 | ~6.9e-06 | 13753.5 | both |

`results/crash/E/out/e4_cpu_vs_gpu.json`. Relative difference ≈ 4e-7. **Nothing
is non-finite on either side, at any length.**

### E5 — but not *every* small perturbation flips it

A `ConditioningAverage` spliced between `620:106` and `620:114.positive` with
**both** inputs taken from `620:106` (`nodes.py:125`,
`tw = t1*s + t0*(1-s)`):

```
E18_condavg_s100    s=1.00  exact no-op   ERROR 622:403   2/2
E18_condavg_s070    s=0.70  1-ulp perturb ERROR 622:403   2/2
```

Verified offline that the splice really does perturb: at `s=0.7`, 7321 of 117760
elements change, `max|d| = 3.05e-05`; at `s=1.0` and `s=0.5` it is bitwise
identical, which is why `s=1.0` is a clean inertness control.

So a perturbation ~15× smaller in the mean than the CPU/GPU one does **not**
cure it. **[I] That reads as a threshold rather than a knife edge, but two points
do not define a curve and I did not sweep it.**

### E7 — and it is the conditioning's source, not the encoder's residency

I inferred from E5 that the CPU cure had to be the memory timeline (the 7.7 GB
encoder no longer sitting in VRAM while the face pass samples). **That inference
was wrong and the next arm refuted it.** A *second* `CLIPLoader` on the CPU was
added and wired to `620:106` **only**; `620:105`, `621:166`, `621:167`,
`622:394` and `622:398` stayed on the original GPU `620:110`, which the server
log confirms still loaded completely (`7672.25 MB loaded, full load: True`) and
still ran.

```
E18_split_crash     success  57.6 s  cached 0
E18_split_crash_b   success  58.4 s  cached 0
```

**The GPU encoder is resident and executing, and the crash is still cured.** So
it is `620:106`'s conditioning values that decide it, not the encoder's presence
in VRAM.

**Reconciling B's `622:398` anomaly with this:** if the deciding quantity is the
exact bits of a conditioning tensor, then anything that perturbs the *process*
before the face pass can flip the outcome without any dataflow path, which is
precisely what Track B observed and could not explain. **[I] Consistent, not
demonstrated — I did not run a `622:398` arm.**

### A bonus reconciliation, free from the tokenizer

Track B reported "the `luna, ` prefix is load-bearing": the 169-char crash string
crashes and the same string minus `luna, ` (163 chars) is clean. Measured on the
graph's own tokenizer: the full string is **46 tokens** and without the prefix it
is **43**. 46 is in Track A's crash region and 43 is the last clean value below
it. **The prefix is not load-bearing; its three tokens are.** No new arm needed.

---

## 5. Sage attention (the coordinator's arm)

`:32003` started with `--use-sage-attention`; log confirms `Using sage attention`
(against `Using pytorch attention` everywhere else). `sageattention` imports from
`/venv/main/lib/python3.12/site-packages/sageattention/`.

| arm | tokens | status | image |
|---|---|---|---|
| `E_sage_placeholder` | 16 | success | healthy, PSNR 57.10 vs the `:18188` control |
| `E_sage_crashstring` | 46 | success | healthy, PSNR 48.91 |
| `E_sage_tok30` | 30 | success | healthy, PSNR 51.36 |

**Read this narrowly.** Track E's own servers do not reproduce the crash under
*any* configuration, so these arms cannot test whether sage removes the bands —
there were no bands on this instance to remove. What they do rule out is the
third of the coordinator's three outcomes: **sage did not create a failure where
this instance was clean**, 3/3, and the images stay healthy. Sage does change the
numerics (PSNR 57.1 rather than 99 against the same placeholder control), so it
is a genuinely different path — it just did not break anything here.

**The arm that matters for the product is still unrun:** sage on an instance
where the crash is first shown to reproduce. That needs `:18188` restarted with
the flag, which I did not do.

---

## Every arm, all cold

28 arms, `execution_cached: []` on every one, fresh `client_id` per arm, full
`/history/<prompt_id>` kept under `results/crash/E/history/`.

| arm | status | exec s | cached | error node | prompt_id |
|---|---|---|---|---|---|
| `E18_alt1_gpuclip_crash` | error | 41.6 | 0 | 622:403 | `c933e35b-6923-48ae-957b-b506da348d7f` |
| `E18_alt2_cpuclip_crash` | success | 66.9 | 0 | — | `448d58d6-1268-4e4d-aac9-b7650b0a5f9d` |
| `E18_alt3_gpuclip_crash` | error | 39.6 | 0 | 622:403 | `5e0dd95d-5987-44e1-bc18-96565d3babff` |
| `E18_alt4_cpuclip_crash` | success | 69.9 | 0 | — | `0d942ee0-b2c2-4614-9c6b-68ec98b35410` |
| `E18_condavg_s070` | error | 38.7 | 0 | 622:403 | `d5f7529a-a85d-480a-9316-8225d9c57c5f` |
| `E18_condavg_s070b` | error | 40.8 | 0 | 622:403 | `96dba53a-c654-4151-8374-7f17d764fdf0` |
| `E18_condavg_s100` | error | 38.9 | 0 | 622:403 | `733164cd-214d-43c8-bb63-130276610c10` |
| `E18_condavg_s100b` | error | 40.1 | 0 | 622:403 | `219efa35-457c-43df-966a-eb55996cd515` |
| `E18_cpuclip_crash` | success | 71.8 | 0 | — | `21cb4525-c7cb-4acf-b7ae-a9af81e785ef` |
| `E18_cpuclip_placeholder` | success | 68.3 | 0 | — | `16d97921-65f4-442d-ad1c-c20861b785f1` |
| `E18_placeholder_ctl` | success | 53.6 | 0 | — | `7ec2f7ac-4680-49bd-bf06-3bd67b2868d5` |
| `E18_split_crash` | success | 57.6 | 0 | — | `474076c6-49d8-4c39-a615-4bc1e7efc2bf` |
| `E18_split_crash_b` | success | 58.4 | 0 | — | `c9c28ae1-ead5-4634-8528-7df727f9ff89` |
| `E18_tok30_cpuclip` | success | 69.1 | 0 | — | `a1c1afdd-a300-445d-a88a-ee9f7728566e` |
| `E18_tok30_cpuclip_b` | success | 67.0 | 0 | — | `3fc89cfe-5c3a-4256-9674-0dec3c6bfb20` |
| `E18_tok30_gpuclip` | error | 36.4 | 0 | 622:403 | `98923de8-2a6d-47d4-ad1f-3ff89c814bad` |
| `E18_tok30_gpuclip_b` | error | 38.6 | 0 | 622:403 | `054ee7c7-24c1-4799-bdbf-4b21d341e935` |
| `E_fullvram_crashstring` | success | 46.2 | 0 | — | `07a921d4-730b-41db-917a-4bd2e39de465` |
| `E_gate_crashstring` | success | 64.2 | 0 | — | `6b8f9ec8-d2bf-4e24-8f5a-ffb898b20cdf` |
| `E_gate_placeholder` | success | 62.0 | 0 | — | `c4d66821-b0ce-4f08-b5bd-8ab14094ac71` |
| `E_noprobe_crashstring` | success | 77.6 | 0 | — | `4c95f578-10b0-4613-9947-7d7a6ff93aab` |
| `E_noprobe_placeholder` | success | 75.8 | 0 | — | `0838d834-dccc-41fe-b205-1c41a027e5aa` |
| `E_ref18188_crashstring` | error | 46.3 | 0 | 622:403 | `cbc85696-87e8-466f-9932-09f66f0e8622` |
| `E_rv16_crashstring` | success | 60.6 | 0 | — | `cbe35c54-a4df-4bf3-88f0-8ed513b93fbc` |
| `E_rv16_placeholder` | success | 58.0 | 0 | — | `730ab8a5-0bc7-4116-9558-6bf0520c963e` |
| `E_sage_crashstring` | success | 55.9 | 0 | — | `ac82b395-0119-4496-8d20-677befb5ee4b` |
| `E_sage_placeholder` | success | 57.7 | 0 | — | `6aeaa4a3-265c-47cd-a76b-1153ef64556d` |
| `E_sage_tok30` | success | 56.9 | 0 | — | `67c89952-f7b4-4794-97b8-0d5f2ccfcde5` |

Servers: `:18188` (used, per the brief) and Track E's own `:32000`–`:32003`.
`:28191` and `:31910` received **read-only** `GET /system_stats` and nothing
else; their `argv` and `environ` were read from `/proc`. No POST, no `/free`, no
restart, no broad `pkill`. The workflow JSON was not edited — every arm is an
in-memory mutation of an already-submitted API graph, as Track A's harness does.

---

## Index

| what | where |
|---|---|
| every arm's submitted graph, metadata, images | `results/crash/E/arms/<ARM>/` |
| every arm's raw `/history/<prompt_id>` | `results/crash/E/history/` |
| offline conditioning sweep, 12–80 tokens | `results/crash/E/out/e1_cond.json` |
| offline DiT forward sweep, 26–50 tokens | `results/crash/E/out/e2b_fwd_fwd.json` |
| CPU vs GPU conditioning diff | `results/crash/E/out/e4_cpu_vs_gpu.json` |
| image health of every arm | `results/crash/E/out/e9_images.json` |
| the tools (Track A's harness repointed, plus E1–E9) | `results/crash/E/tools/` |
| the read-only probe pack and its traces | `/workspace/trackE/custom_nodes/trackE_probe/`, `/workspace/trackE/logs/` |
