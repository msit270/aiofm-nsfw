# STATE.md — read this before AUDIT.md, MAP.md, QUESTIONS.md, SETUP.md or PROPOSALS.md

Those documents were written around 03:24–03:52 on 2026-08-05, during a local
graph-mapping session. A great deal happened afterwards on a pod that has since
been destroyed with no git remote. **Treat those files as a snapshot of the
pre-render state, not as current.** This file records what changed after them.

---

## The single blocker right now

Opening `OFMTech_NSFW` in the browser and pressing Run throws:

```
No output node found for id [647] slot [4] MODEL
```

- Reproduces on a genuinely fresh pod with only the NSFW pack installed.
- Reproduces with **both LoRA stacks left at `None`**, so it is not LoRA wiring.
- It is in the shipped graph.

Working hypothesis, unverified: this is a **frontend** error raised while the
browser converts the UI graph to API format. Every render verified so far went
through a harness that submits the API graph directly and never exercises that
conversion. If that is right, this graph has never once been run the way a buyer
runs it, and "the NSFW graph renders" was true via the harness and false via the
browser.

Confirm or kill that hypothesis before changing anything. Then find what node 647
actually is — the graph is seven subgraphs deep, so check subgraph host slot
mapping.

---

## Corrections to MAP.md

Five corrections were established after MAP.md was written:

1. Run order is `sg1 → sg0 → sg2` — **sg0 runs third, not last**. Root order is
   unreliable because the graph looks cyclic at host level until flattened.
2. **sg5 is dead logic on a LIVE wire** — the last hop before SaveImage, passing
   through by bypass. The final image is actually sg4's `#418`.
3. sg5 has **two** detailers, not three. "Breasts" is only a comparer title.
4. The second model family is **Z-Image** (`zimage.safetensors` +
   `qwen.safetensors` type lumina2 + `ae.safetensors`). Both sg2 and sg4 run on it.
5. Pack list had two misattributions: `UltralyticsDetectorProvider` is **Impact
   Subpack**, and `MediaPipeFaceMeshToSEGS` is **Impact Pack**, not controlnet_aux.

Also closed since: `ae.safetensors` is a hardlink of
`variational_encoder_primary.safetensors` and is the **Flux.1 autoencoder**. That
answers SETUP.md's open question.

---

## Defects fixed after those docs (all in the published tarball)

- **A0 — the graph rendered from an empty prompt at seed 0.** `#483`
  `INSTARAW_RealityPromptGenerator` is fed by a client-side panel through
  `node.properties`. `prompt_queue_data` held six real prompts;
  `prompt_batch_data`, the key the pack actually reads, was `"[]"`.
  `reality_prompt_generator.py:224-227` does not raise on an empty batch, it
  returns `([""], [""], [0], 0, resolved)`, which wired straight into sg1's
  positive, negative and seed — and since a linked input beats a widget it also
  defeated the shipped negative prompt. Only manifested on a fresh load of the
  saved file, which is exactly what a buyer does. **Fixed.**
- `#598` stale wildcard combo failing server-side validation. **Fixed.**
- **Mouth detailer near-full-frame false positive.** `lips_v1.pt` produced a
  spurious ~2500x2000px detection on every one of 11 renders at confidence
  0.583–0.703 against a threshold of 0.70; three runs tripped it, costing +27%
  wall clock and repainting the torso with a "realistic detailed mouth" pass.
  Raising the threshold is unsafe (clusters nearly touch, 0.703 vs 0.714), so an
  Impact `SEGSRangeFilter` hook on size was wired instead — separates them 30x,
  byte-identical output when not needed, 284s → 223s when it is. **Fixed.**
- **A hidden third LoRA stack** meant the buyer's Z-Image LoRA never reached the
  eye pass. **Fixed.**
- INSTARAW `requirements.txt` rewritten to the pack's real dependencies (it had
  contained `numpy==1.26.4` plus a verbatim paste of MediaPipe's lockfile).

## Defects known and still NOT fixed

- `#597` VAEEncode feeds `#616` VAEDecode in sg1 with nothing between them — a
  pure round-trip at ~1434x1843.
- `#106` drives the face pass at denoise 0.8 with the literal placeholder text.
- The face is detailed twice — sg1 at 0.45, then sg2 at 0.80.
- `#600` KSamplerAdvanced reseeds itself every run, so the graph is not
  reproducible from the seed it exposes.
- The dead ControlNet path is mis-wired: `SetUnionControlNetType` sits in parallel
  rather than series, so the union type is never applied.

---

## Packaging — the gaps in SETUP.md are closed

- All six required node packs now install (Impact Pack, Impact Subpack,
  controlnet_aux, IPAdapter_plus, Essentials, UltimateSDUpscale) plus INSTARAW,
  at pinned commits.
- `models/sams` is created and holds `sam_vit_b_01ec64.pth`.
  `models/ultralytics/bbox` holds `face_yolov8m.pt`, `hand_yolov8s.pt`,
  `lips_v1.pt`, `nipple.pt`, `pussyV2.pt`. Verified on a fresh install.
- `expected_size()` returned two lines for `SDXLNSFW.safetensors` (listed twice in
  the manifest), crashing the integrity arithmetic. That was the root cause of the
  unactionable "has 6.5 GB, expected 6.5 GB" warning. **Fixed.**
- Setup script bug: `COMFY_PORT` defaulted to 8188 while these pods run 18188, so
  `comfy_up()` probed a dead port, took the "not running" branch, printed a green
  check saying nodes would register on startup, and never restarted ComfyUI —
  leaving the pre-install node set live. `comfy_verify_nodes`, the check that
  exists to catch exactly this, was skipped by the same flag. **Fixed.** This was
  the long-standing "red nodes on fresh install" symptom.
- Full-pack pull verified cold on a fresh pod: PROFILE=all, 178.4 GB in 84 files,
  6m36s, integrity OK, all 88 node types registered.

---

## Distribution — new since those docs

- Published artifact: `dist/AIOFMTech-NSFW.tar.gz` in `msit270/AIOFM-Pack`,
  8,202,871 bytes, sha256 `3f6d0f2f…aada76`. Deliberately **not** under `models/`,
  because the bulk `hf download --include "models/*"` would sweep it and the
  integrity check would try to size-verify it against a manifest that omits it.
- Bootstrap lives in a gist as `aiofm_setupnsfw.sh`, 116 lines / 5,114 B. It never
  references `SCRIPT_DIR` (a piped install leaves `BASH_SOURCE` at `/dev/fd/63`,
  which silently broke both the INSTARAW vendoring and the workflow install),
  reads `PACK_TOP` out of the archive rather than assuming it, reads the token from
  a file never an argument, and uses `sed` not `head` so `pipefail` cannot turn
  SIGPIPE into exit 141.
- The archive name and its top-level directory intentionally differ:
  `AIOFMTech-NSFW.tar.gz` unpacks to `OFMTech-NSFW/`. The bootstrap reads the
  directory out of the archive, so either can be renamed independently.
- Buyer path proven end to end from the live gist against the live repo into an
  empty ComfyUI — **via the API harness**. See the blocker above: the browser path
  is what is now known to fail.

---

## Licensing

- **`tianweiy/DMD2` is cc-by-nc-4.0** (non-commercial) and its LoRA sat in the live
  render path at strength 1.0. **Replaced.**
- **Base checkpoint is LUSTIFY! GGWP (V7)** with `allowCommercialUse:
  ['RentCivit','Image']` and `allowDerivatives: False`. `Image` means buyers may
  sell generated images — the product's core use case is fine. The problem is
  redistribution of the checkpoint inside the pack. Likely fix: remove
  `SDXLNSFW.safetensors` from the pack and have buyers download it from Civitai
  themselves, accepting the licence as themselves. Zero output change, no graph
  re-verification, both LoRA slots untouched. **UNRESOLVED — blocks selling.**
- `cg-image-filter` derivation is **Apache-2.0**. Needs the licence text and the
  original copyright notice shipped inside `ComfyUI_INSTARAW/`, with modified files
  marked as changed. **UNRESOLVED.** Doing this requires re-cutting the tarball.
- The other 76 model files in the pack were audited and came back clean. Treat
  "audit came back clean" on this project as provisional — DMD2 was found only
  because someone happened to check, and LUSTIFY surfaced after a clean report.

---

## QUESTIONS.md is incomplete

The desktop copy stops well short. Questions raised afterwards on the destroyed
pod included, at minimum: Q14, Q15 (header notes uncollapsed), Q16 (DMD2
replacements), Q18 (setup script defects), Q20 (measuring the model-download
phase), Q22 (archive name vs internal directory), Q25 (verification gotchas).
Their text is lost. Re-derive as needed rather than assuming the desktop file is
the full set.

---

## Two verification traps worth keeping

1. **Hash comparison does not work on this pipeline.** Renders land on a strong
   attractor, not determinism — a confident "reproducible" conclusion was drawn
   three separate times and was wrong each time. Verify with a constant-folded
   API-graph diff instead.
2. **A raw gist URL serves a stale CDN cache.** `api.github.com/gists/<id>` is
   authoritative and immediate. Also note the API returns content as a *string*, so
   `len()` is a character count, not a byte count — use `len(c.encode())` or diff.

---

## What was lost with the pod

`tools/` (fingerprint.py, compare.py, drift.py, the graph flattener/differ, the
render harness) and `results/` (40 render records, 28 renders). The harness needs
rebuilding — and the rebuild should drive a **real browser** via Playwright, load
the workflow, press Run, and fail on any frontend error. A render that only passes
via the API is not a passing test. That is the gap that let the current blocker
ship.
