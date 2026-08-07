# Phase-1 verifier report (fresh-context, adversarial)

Verifier session 2026-08-07. Scope: HANDOFF-QUALITY.md "Phase-1 results
(batch A...)" vs results/run5/ACCEPTANCE.md. No renders, no server contact,
no files touched outside results/run5/verify/. All numbers below re-derived
by me from the files cited; nothing taken from prose.

## State caveat (important)

Verification ran while the work session was live. Mid-verification:
likeness_scores.json was clobbered by a batch-C rescore (dynamic-centroid
rebuild from a single C zref file), then deleted, then restored under a new
commit 6208372 with a pinned centroid (results/run5/centroid.json) after a
NaN-poisoning incident in batch B/C (notes/R5-nan-poisoning.md).

I verified phase-1 against the commit that carries it, 2b75fdb ("batch A:
likeness trace complete"), and then re-checked the post-incident HEAD
(6208372): **all 76 batch-A score rows are byte-identical across the purge**,
and centroid.json's reference set and pairwise band exactly equal 2b75fdb's
values (min 0.781619645577781 / max 0.8283369340780794 / mean 0.79854).
The incident (~21:4x, trigger arm zref_P_12345_str08, batch C) postdates all
batch-A renders (files 21:02–21:12); batch-A rows were not among the 13
purged. Phase-1 evidence stands at current HEAD.

## 1. Likeness chain (re-derived from likeness_scores.json @ 2b75fdb)

prose        json value   file (A/A0/...)                      match
0.287        0.286490     T01_base591                          +0.0005 (a)
0.163        0.163387     T03_refine596                        exact
0.546        0.545472     T04_sdxlface607                      +0.0005 (a)
0.487        0.487030     T05_usdu617                          exact
0.523        0.523230     T08_usdu98                           exact
0.581        0.580521     T10_zface114                         exact
0.585        0.584505     Instaraw/SDXL/Metadata/HasMetadata   exact
skip607 0.457 = 0.457234; skip114 0.523 = 0.522811;
den0.50 0.638 = 0.637486 (+0.0005, a); den0.65 0.664 = 0.664376.

(a) Three values are 1 ulp high at 3 dp (double-rounding: 0.28649->0.2865->
0.287). Max abs error 0.0005 — immaterial, but strict rounding gives 0.286,
0.545, 0.637. Same pattern in texture: "8.29" for 8.2849.

Note: the prose chain omits T02_nmkd595 (0.272602) between base and refine;
most of the base->refine drop is T02->T03 (0.273->0.163), so attributing the
destruction to the LoRA-less refine 619:600 is unchanged.

All 11 tap/final PNGs exist under /workspace/run5/output/A/A0/ (T01–T08,
T10, T12 + Instaraw/SDXL/Metadata/HasMetadata_00001_.png), 10 taps as
claimed. Arm finals exist per arm dir.

## 2. Determinism (A0_repeat vs A0)

Recomputed myself (venv PIL/numpy): both finals 2688x3456 = 9,289,728 px
("9.29M px" correct), **max_abs_diff = 0, zero differing pixels**. Caveats:
- The PNG *files* differ (10,925,175 vs 10,925,252 bytes — embedded
  metadata carries the arm path), so "bit-identical" strictly means
  pixel-identical; the parenthetical (max_abs_diff 0) is the accurate claim.
- A0_repeat ran last with 57/102 nodes cache-served (meta.json); only the
  tail (620:114 Z-face onward + saves) re-executed. The guard therefore
  proves tail re-sampling determinism plus shared-cache prefix identity —
  sufficient for the same-server arm comparisons it licenses (arms share
  those cached prefixes), but it is not a full fresh re-render. The later
  NaN incident shows why repeat-runs-last mattered; the BC2 canary
  (bit-compare re-render of zref_P_12345) is the pending stronger check.
- Graph diff: A0_repeat api_graph is input-identical to A0 except the 11
  SaveImage filename_prefix values (arm output dir). Proper repeat.

## 3. Structural claims (from committed api_graph.json files)

(a) PASS — A0 619:610 = LoraLoader(sdxl_tdd_lora_weights.safetensors),
    model ["619:613",0], clip ["619:613",1]. 619:613 =
    CheckpointLoaderSimple(SDXLNSFW.safetensors). Walked 619:600's model
    chain: 600 -> 610 -> 613; node 618 (rgthree Lora Loader Stack,
    lora_01=lunaskye.safetensors) is not in it. Claim 1 verified.
(b) PASS — 587:92 FaceDetailer model = ["619:613",0] (raw checkpoint);
    dpmpp_2m_sde, 30 steps, denoise 0.42, cfg 3 — all as prosed.
    Nuance: its positive prompt 587:93 encodes with clip ["618",1] (the
    lunaskye-stack CLIP). Phase-1's wording ("its model is the RAW
    checkpoint") is scoped correctly; the Status-section phrase "no LoRA at
    all" is overbroad for the CLIP path.
(c) PASS — 483 prompt_batch_data (469 chars) contains "long dark hair";
    zero case-insensitive occurrences of "luna"/"lunaskye". ("auburn"
    absent from the base prompt, consistent with the face-prompt mismatch
    claim, whose other half I did not audit.)
(d) PASS — A_skip607 vs A0 full dict-diff: sole non-prefix difference is
    619:597 (VAEEncode).pixels ["619:607",0] -> ["619:596",0], where
    619:596 = VAEDecode of refine 619:600. True bypass of 607.
(e) PASS — A_den065 vs A0 full dict-diff: sole non-prefix difference is
    620:114 (FaceDetailer).denoise 0.35 -> 0.65. Suppressed diffs were
    exactly the 11 SaveImage filename_prefix values, nothing else.
    Also verified (not requested): A_den050 sole diff denoise 0.35->0.50;
    A_skip114 sole diff 620:111 (ImageColorMatch+).image ["620:114",0] ->
    ["620:137",0] (bypass-by-rewire of the Z-face pass).

## 4. ZIT bands

PASS — portraits to centroid: 0.919748 / 0.935041 / 0.936485 -> "0.92-0.94".
Pairwise: min 0.781620, max 0.828337 -> "0.78-0.83". Full-body 0.755094 /
0.813958 -> "0.76-0.81"; zref_B_12345 "likeness 0.81" = 0.813958.
Stranger floor: zref_P_12345_nolora 0.337300, sxref_P_12345_nolora 0.335035
-> "~0.33". Excluded-from-centroid arms are present as scored rows:
zref_P_12345_eak 0.888907, zref_P_12345_nolora 0.337300.

## 5. Hands claim

PASS — A0's execution window in /workspace/run5/server_19188.log is lines
199 ("got prompt") to 403 ("Prompt executed in 142.48 seconds", matching A0
meta exec_s 142.482). Inside it: line 320 "0: 640x512 1 hand, 1.8ms" and
line 322 "Detailer: segment upscale ... -> (1024, 704)". So "1 hand,
1024x704 crop sampled" is log-backed for A0 specifically (the literal
string "1024x704" does not occur; the crop line renders it "(1024, 704)").
A0 history.json: completed=true, status_str success, messages end
execution_success, no execution_error. Sampler/steps/denoise/model claims
confirmed under 3(b).

## 6. V9 identity

PASS — /workspace/run5/v9_sha256.txt:
1a3abf0bf48113eb5e17d2f8ae012c5b60cb97d81d79c4d9e47cd5af56c162f1 for
/workspace/run5/lustifyNSFWCheckpoint_zenithV9.safetensors. civitai_model_
573152.json version id 3045803 "ZENITH (V9)", file lustifyNSFWCheckpoint_
zenithV9.safetensors, SHA256 identical (case-insensitive). HANDOFF's
abbreviated 1a3abf0b…c162f1 matches.

## 7. Likeness methodology / centroid trap

Confirmed at 2b75fdb: ref_keys filter is `"/zref_P_" in "/"+k and "nolora"
not in k and "eak" not in k` -> centroid = mean of exactly the 3 batch-A
ZIT portraits (JSON reference_images agrees). Pipeline images cannot match
the path filter, so no pipeline contamination of the phase-1 centroid.
THE TRAP WAS REAL AND FIRED: the per-invocation rebuild meant a later
batch-C scan (whose only matching file was C/zref_P_12345_s30cfg2) rebuilt
the centroid from that single image and clobbered reference_images/band in
the merged file — observed live during this verification. The worker caught
it; likeness.py now pins the centroid via centroid.json (committed in
6208372) with byte-identical band values, and batch-A rows were never
recomputed. Phase-1 numbers are unaffected; any C-batch scores produced by
the clobbering invocation were purged with the incident cleanup. Residual
risk (merge writes rows from potentially different centroids into one file)
is closed by the pin.

## 8. Arm sanity

PASS — all six named arms (A0, A0_repeat, A_skip607, A_skip114, A_den050,
A_den065) have meta.json ok=true / status_str success, and history.json
completed=true with no execution_error. Also verified for all 10 reference
arms (zref_P_12345/777/999, zref_P_12345_eak/_nolora, zref_B_12345/777,
sxref_P_12345, sxref_P_12345_luna_trigger, sxref_P_12345_nolora).

## Texture claims (tap_metrics.json)

- "ZIT ref 10.6/9.5": zref_B_12345 face 10.61 / body 9.49. PASS.
- Pipeline face band "7.5-8.9": A0 range 7.55–8.92 across all 11 entries. PASS.
- **Pipeline body band "6.1-6.8 at every stage": DOES NOT RE-DERIVE.**
  A0 body range is 6.07–7.52; T02_nmkd595 = 7.52 and T03_refine596 = 6.88
  exceed the stated band. The supported conclusion ("never reaches ZIT
  level [9.49] anywhere") still holds with margin, but the quoted range is
  wrong for 2 of 11 stages.
- "USDU617 biggest smoother (8.29->7.55)": T04 8.2849 -> T05 7.5518, and
  -0.73 is the largest single-stage face-RMS drop. PASS (8.29 is the
  double-rounding artifact noted above).
- "lapvar ZIT 277 vs pipeline ~110": zref_P_12345 face lapvar 277.4;
  pipeline final 104.2, T10/T12 110.7–111.5. Numbers re-derive, but the
  claim MIXES ANCHORS: the RMS sentence uses the composition-matched
  full-body ZIT (zref_B), while the lapvar sentence uses the portrait ZIT.
  The full-body ZIT's face lapvar is 93.0 — BELOW the pipeline final — and
  both are confounded by native face size under the 512 px normalization
  (zref_P face 781 px native, zref_B 242, pipeline final 447). Directionally
  suggestive, weaker than stated; flagged as overstated.

## Acceptance verdicts

A1 PASS — every likeness number traces to likeness_scores.json (2b75fdb =
   current HEAD for batch A), PNGs on pod, per-arm api_graph.json present.
A2 PASS — band and floor exist as measured rows; both anchors used.
A3 PASS — chain attribution is consecutive taps within the single A0
   render; "617 smooths" likewise (T04->T05 within A0).
A4 PASS — re-measured max_abs_diff 0 over 9,289,728 px; see cache and
   file-bytes caveats in §2.
A5 PASS — all wiring/prompt claims quoted and re-verified from api_graphs.
A6 PASS — 16/16 batch-A arms completed, no execution_error.
A7 PASS with flags — "the hand still reads wrong" is an unmeasured visual
   verdict (it restates the owner's known defect, but no hand metric
   exists in evidence); "coherent balcony 3/4-body frame" is descriptive
   but unmeasured. Neither is an A/B better/worse call.
A8 PASS — hash identity confirmed.
A9 PASS with flag — reconstruction is prominently labelled in Status, but
   phase-1's "The user's simple-ZIT reference" attributes the reconstructed
   workflow to the user at point of use.
A10 N/A — phase-1 makes no mouth-threshold decision (listed under Next).

## Verdict

ISSUES (minor; no acceptance item fails):
1. Body-texture band "6.1-6.8 at every stage" is false as stated (actual
   6.07–7.52; T02 7.52, T03 6.88). Conclusion unaffected.
2. lapvar 277-vs-110 mixes reference anchors and is resolution-confounded;
   composition-matched anchor (zref_B, 93.0) would not support the sentence
   as written.
3. Rounding: 0.287 / 0.546 / 0.638 / 8.29 are one final-digit high
   (double-rounding); strict values 0.286 / 0.545 / 0.637 / 8.28.
4. "Bit-identical" = pixel-identical (PNG bytes differ); repeat exercised
   only the ~45 non-cached nodes (see §2).
5. A7/A9 phrasing flags as above.
Everything else re-derives exactly, including all seven chain numbers, all
four arm finals, both bands, the floor, all five structural claims, the
hands log evidence, the V9 hash, and arm completion statuses.
