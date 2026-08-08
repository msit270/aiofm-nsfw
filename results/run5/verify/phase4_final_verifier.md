# Phase-4 FINAL verifier (round 4, fresh context, 2026-08-08)

## VERDICT: ISSUES (minor; nothing overturns the pack or any measured claim)

Re-derived independently, all PASS:
- A19: tarball member OFMTech_NSFW_Personal.json (sha 50b2b3ff… = PACK.txt): 0 hits for luna/lunaskye, 0 lips_v1; LoRA stack all "None"; face prompt "TRIGGER, PROMPT FOR YOUR MODEL". CONFIG-SPEC marks every BASE/DETAIL setting GENERAL/SPECIFIC; CHECKLIST in tarball, cited by README, states generalisation UNPROVEN.
- A21: recomputed H_PC1_OM vs H_nomouth_OM finals: 91 px >8, max 31, bbox identical to mouth_deletion.json. H_nomouth_FB api_graph: no lips_v1. Licensing consequence stated factually.
- A20: S14 has the COMBO WINNER tile, like-for-like crops; J_combo history success; (J) marks + rejected arms recorded; research_hands sources stored.
- A17/A18: M2 FB-vs-PT max diff = 253 (distinct scenes); recomputed cos: FB .7894, PT .7314, CU .6436, neutral .2338 — match claims and likeness_scores.json. M2_ship_neutral: ZB_pos.text=["619:590",0], loras None. 30-step tqdm bars 11-13 s vs 8-step 1-2 s in server log; negproof recomputed 76.2% px >8; samplers.py isclose-uncond mechanism confirmed (line 371, cited 370 — off by one, immaterial).
- A24: K4a diff vs G_PC1_FB = exactly the 3 colormatch-bypass rewires (+prefix rows); K1: 587:98.image ← 621:163; all five K cos values match json to 3 dp.
- A22: all 10 I rows present; film dirR .3407/spread .7210/P5 .0030, lightpos .3274, shift60 spread .9109, cfg25 .1365 all match; metrics labelled PROXIES with stored formula; I_shift45 graph is single-lever.
- A25/A26: canaries max_abs_diff=0 in batchG/H/I/J/K/L/M/M2 logs; all 9 model refs in the member resolve to installer fetch/hardlink lines (ae.safetensors via verified hardlink; bbox/ auto-populated); no new pack/pip dep (K8 BNK dropped). compare_api: fresh-gate browser graph ≡ M2_ship_neutral graph except SaveImage prefix.
- fresh2 gate: install.log "setup done / integrity OK / all 46 node types registered" (2m37s); gate1 failed on a browser dialog-mask flake; gate2 PASS, full render 150.26 s, PNG present.

ISSUES:
1. A23 in-flight: D-matrix absent (pending per cf8b6d7), yet shipped README cites "results/run5/Dmatrix + REPORT" and "~8%" — dangling until it lands.
2. A18 partial: I_cfg15_FB rendered (cos .778) but no read/verdict recorded; PC-reconciliation's cfg-1.5 CU question left open (arm was FB-only). F/K reads unlabelled (J).
3. Nits: shipped MarkdownNote says "two" Lora Loader Stacks (graph has one); installer still fetches dropped lips_v1.pt (extra file, not parity).
