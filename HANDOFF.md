# HANDOFF.md — run 3 (2026-08-07)

**Workflow `47419606…fca30d4b` · archive `29175edc…5fe16a3e` (8,153,528 B, 170
files) · NOT yet on HuggingFace — the pod's token is read-only; publishing is
your one manual step, below.**

Everything else in the definition-of-done is DONE, with evidence under
`results/run3/` and the reasoning in `QUESTIONS.md` §4, `notes/R3-guard.md`,
`notes/R3-eyes.md`.

---

## The one thing only you can do

The pod's HF token (`/workspace/.hf_token`, named "VastAI") is **role: read**.
It downloads fine and cannot upload — no cut has ever been published from
here. With a WRITE token, from any machine:

```bash
HF_TOKEN="hf_your_WRITE_token" \
/venv/main/bin/hf upload msit270/AIOFM-Pack \
    /workspace/nsfw-fix/dist/AIOFMTech-NSFW.tar.gz \
    dist/AIOFMTech-NSFW.tar.gz \
    --commit-message "NSFW run-3 cut: no-face guard, selector fixes, setup device asserts, polish. Workflow 47419606, archive 29175edc"
```

Then confirm from the buyer's side (the only side that counts):

```bash
curl -sS -I -H "Authorization: Bearer $HF_TOKEN" \
  "https://huggingface.co/msit270/AIOFM-Pack/resolve/main/dist/AIOFMTech-NSFW.tar.gz" \
  | grep -i 'x-linked-etag\|x-linked-size'
# expect: x-linked-etag: "29175edc581cd61d96324bd3bcedc4da36c638b90211554fa1823f4c5fe16a3e"
#         x-linked-size: 8153528
```

Live HF currently serves `3f6d0f2f…` (8,202,871 B) — an artifact with none of
the graph fixes. The buyer one-liner (unchanged, the gist needed no edit):

```bash
echo "hf_YOUR_TOKEN" > /workspace/.hf_token
bash <(wget -qO- "https://gist.githubusercontent.com/msit270/70256ac1ebf2760e10f78804862db528/raw/aiofm_setupnsfw.sh")
```

---

## What changed, and the proof for each

**1. `622:403` can no longer kill a render — at any prompt length (DoD 3).**
The eyes stage now checks its own face detection (`ImpactIsNotEmptySEGS` →
lazy `ImpactConditionalBranch`, C-fix-design C1): no face found → the whole
eyes subtree (including the crashing `MaskBoundingBox+` and its 8-step
sampler) is never scheduled and the mouth-stage image passes through, with
`PreviewAny` ("eyes ran? False = …") putting the skip in `/history` and on the
canvas (C1b). Commit `6de805d`. Proof: fold-diff vs the pre-guard export
IDENTICAL; happy path **byte-identical pixels** (max abs diff 0, full frame,
cold, fixed seeds); and the deterministic pair — detector threshold forced to
0.99 so detection MUST fail — crashes the unguarded bytes at `622:403` and
completes on the guarded bytes with the delivered image pixel-equal to the
mouth-stage tap. Bands on the shipping config, all cold, all healthy faces
(YOLO 0.90 class): 16, 46, 103, 110 tokens.

**2. The "103–120 band" was probe-only — a correction to the last handoff.**
All eight arms behind "103–120 still crashes, fix or no fix" ran the probe
graph (frozen base image). The full 88-node graph had never been run at 103
tokens; it rendered clean today (`R3_PC_head_103`). The full-graph crash is
still real — `R3_PC_mid_46` (device default, 46 tokens) died at `622:403`
cold the same hour — and the bistability now flips arm-to-arm on one process,
so only same-window controls mean anything. `notes/R3-guard.md`.

**3. The eye regression: `device=cpu` stays, and the dual-loader idea is dead
(DoD 5).** The experiment: face/mouth encodes on cpu with eye encodes back on
the GPU renders **pixel-identical to full-cpu** (max 2 levels) while both
differ from all-default identically. So the eye change enters through the
face-pass output image — changing the face encode IS the fix — and no loader
arrangement keeps both. Reverting instead would reopen black-face failures at
ordinary prompt lengths (30–96, 166 measured); the guard would make those
loud, but a loud black face is still not sellable output. Cost on the full
graph, measured: 2.97 % of pixels, eye band mean 0.5 levels / max 85 / 3.2 %
of eye-band pixels over 4 levels — milder than the probe-graph sheet that
alarmed us. Sheets (1:1, labelled): `results/run3/sheets/
R3_EYES_default_cpu_dual.png` and V's original
`results/crash/V/out/V_SHEET_EYES_face_sheet1of1.png`. Overrule me with
`git revert 7ce1539` — everything else stands either way. `notes/R3-eyes.md`.

**4. The setup script cannot let a buyer run the broken config believing they
are fixed (DoD 4).** Two assertions, both naming the fix in their failure
text: a static regex of CLIPLoader's class block in the installed `nodes.py`
(dies during install), and a runtime check of `/object_info` (exit 3 → die;
the verifier caught the first version being swallowed and it is now
end-to-end fatal). Negative-tested against a doctored pre-v0.3.11 `nodes.py`.
Commits `d4bde0f`, `d7ea270`.

**5. The selector trap is gone (DoD 8).** No auto-pick: the popup opens with
nothing selected and Send disabled; one click selects and enables, every
batch size. Companions: Enter now respects the disabled Send (it used to
submit an empty selection — `InterruptProcessingException`, render dead, from
one keypress), and digit keys can no longer index past the batch end. Browser
proof in both DoD-2 gates: `send_enabled on open=false → one click → true`.
Commits `f3cff3b`, `fd77e7a`.

**6. ignore.json (DoD 7): two rules fixed at source, three reclassified by
what the fresh install exposed.** The two original `product-known` rules are
deleted because their defects are gone: the ten stale
`rgthree.compare._temp_*.png` refs are out of the workflow (8 died with the
anatomy subgraph, 2 reset on `#419`), and the RPG `console.error` was already
downgraded (`73e0a2c`). Then the fresh install falsified a run-2 premise: the
three "environment" rules claimed a buyer never has Swwan / pysssss / the
rgthree collision — but **the NSFW installer reuses the video `NODE_REPOS`
wholesale, so every buyer gets all of them**, and a fresh install's boot logs
~40 cosmetic console errors from Swwan's two missing web files plus its
extension-name collisions with the rgthree the graph genuinely needs. Those
three rules are now honestly `product-known` with the fix named: **trim
`NODE_REPOS` to the packs the NSFW graph uses and drop the Swwan fork**.
Deferred this run because the "Workflow node check" stage hard-names video
packs, and editing install-check logic during a distribution cut risks more
than labeled console noise. Nothing here gates: boot errors never fail a run
by design, and both this run's gates were green with zero load/run errors.

**7. Polish, each provably conversion-inert (fold-diff IDENTICAL, integrity
0 problems, plus the byte-identical A6 render):** dead anatomy subgraph
deleted (`b4f7359` — it sat bypassed on the live image wire; a buyer can no
longer un-bypass into five never-validated detailer paths); `#419` comparer
state reset (`4226580`); all 120 remaining Russian `localized_name` fields
stripped (`fd140a2` — every buyer saw Russian slot labels); host `#620` ships
expanded (`fea23a3` — the face-prompt route is visible).

**8. Output-changing fixes, each with its A/B sheet (the standing rule):**
- **Mouth guard ceiling 1.7M → 4M** (`07d61b2`): the old ceiling sat inside
  the real-lips range and silently deleted mouth detail on close-up renders
  (20 recorded drops; one session went 19-passed / 20-dropped). The full
  211-line log dataset is now in the repo: real lips up to 2.06M, the
  full-frame false positive the guard exists for at 9.29M, nothing between.
  A/B on the recorded dropping config: the same 1,933,356 segment drops at
  1.7M and passes at 4M. Sheet: `results/run3/sheets/R3_MOUTH_ceiling_ab.png`.
- **Eyes-composite feather, P14** (`72f95ba`): `622:418` pasted the
  eye-detailed crop back with NO mask — a hard rectangle on the face box.
  `622:403`'s already-computed mask now runs through `FeatherMask` 30 px into
  `622:418.mask`. A/B: 0.35 % of the frame, max 5 levels, all in the boundary
  ring, interior 0.0000 %. Sheet: `results/run3/sheets/R3_SEAM_feather_ab.png`.
  (The `#114`-internal mask-edge step is a separate, unfixed defect.)
- **CORS wildcard removed** (`5c17404`): 12 responses hardcoded
  `Access-Control-Allow-Origin: *`; all callers are same-origin and ComfyUI's
  middleware owns the policy. The three OPTIONS handlers had provably never
  executed.

**9. Console hygiene:** the five perpetual-interval RPG debug dumps (one
every 5 s, forever) → `console.debug` (`cda9c93`); popup per-image URL log →
debug. Per-action logs remain — accepted this run.

**10. `INSTALL MODELS.txt` step 1** no longer tells gist-bootstrap buyers
their working install is broken (`0079b53`).

## Verified-stale items from your list (checked on current bytes, not assumed)

- **`#600` reseeding**: no sampler randomizes — all 13 seed controls read
  `fixed`; the graph is reproducible from its exposed seeds. (Fixed in a
  prior run; the open-items list predated it.)
- **cfg=1 negatives**: all three Z-side negatives (`105`, `167`, `394`) ship
  empty, and canvas notes `649`/`652` explain why at length. The SDXL side
  runs real cfg and its negatives apply. Nothing to change.
- **ControlNet / SetUnionControlNetType**: zero matches in the file — that
  path was deleted before this run.
- **"Dont touch!!!" subgraph names**: already renamed; all six (was seven)
  defs carry descriptive names.
- **`#597`→`#616` VAE round-trip**: present, per your "D1 stays reverted".
- **Double face detail (sg1 0.45 → sg2 0.80)**: kept. Removal saved no
  measurable time and pass 1 measurably survives into the final image; the
  A/B pair is in `results/ws4/` if you want to overrule.

## Accepted, with reasons (QUESTIONS.md §4)

Loader duplication (3× face_yolov8m, 3× sam_vit_b, 2× UltraSharp);
`node_identifier` persistence + the server-global selector waiter
(single-tenant product); RPG per-action logs; `#98` tiling question;
`MAP.md`/`AUDIT.md` describe the pre-run-2 graph and were not rewritten —
`notes/` + this file are current.

## Licensing (untouched, per instruction)

`QUESTIONS.md` §0 unchanged and still accurate: LUSTIFY (B1) is your next
run; DMD2/UnMarker/GrainNet (B2–B4) still ship to every buyer because the
model repo and pack contents were out of scope here. Publishing the run-3
tarball changes `dist/` only — it does not fix B2–B4.

## The fresh-install proof (DoD 1)

`tools/browser_harness/fresh_install.sh`: fresh tree (empty `custom_nodes`,
hardlinked models), the LIVE gist one-liner, the run-3 pack served through
the bootstrap's own `AIOFM_PACK_URL` override (read-only token — see above;
re-run without `MIRROR_PACK` after you publish for the full-live version).
Install exit 0 in 85 s with the device assertion visibly passing; ComfyUI
booted on `:31950`; the buyer gate (`results/run3/fresh/`): **PASS** — zero
red nodes, both Luna LoRAs through the widget menus, the 60-token character
description typed and read back on `#106`, Run, 92-node graph accepted,
selector answered with a single click (Send: disabled on open → enabled after
the click), render complete in 271 s, `HasMetadata_00001_.png` delivered, and
twelve screenshots ending with the finished image on the canvas
(`fresh-buyer-11-final-image-on-canvas.png`).

## Instruments

- `results/run3/ACCEPTANCE.md` — the criteria this run was judged against.
- `results/run3/tools/r3.py` — the arm driver (cold discipline inherited from
  Track V); `analyze.py` — pixel compares + 1:1 sheets.
- Gates: `node tools/browser_harness/gate.js -w OFMTech_NSFW --url … --tag …
  --face-prompt-file …` (typing now follows the buyer route into the
  subgraph); `run.js --no-submit --install` for 9-second conversion checks.
- `d_gate.sh` / `d_setup.sh` EXPECT hashes moved to the `29175edc…` cut.

*Everything is on `master`, one commit per change, pushed.*
