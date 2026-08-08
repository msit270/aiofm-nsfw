# Settled-decision audit: what rests on pre-PC (SDXL-architecture) calibration
(2026-08-08, after the owner's S11 verdict. "Settled" numbers were calibrated
on the SDXL chain in runs 2-4; the base architecture has been replaced.)

## Already re-derived on PC
- Face denoise: 0.35 (run-3 settled) -> 0.50 on PC (S11 verdict; the owner's
  own example of a settled number failing to carry).
- Face sampler: euler_ancestral re-CONFIRMED on PC by eye+metric (S11);
  the S4 rms preference measured as architecture-specific.
- Hands: prompt + guide re-derived (batch J); denoise 0.42 kept after a
  0.28/0.32 ladder showed no gain.
- Mouth stage: deleted (batch H) — its settled ceiling/threshold moot.

## Carrying over on MECHANISM (architecture-independent, no re-test needed)
- cfg 1 on all detail passes (guidance-distilled Turbo; uncond-skip at
  cfg==1 is source-cited). Raising it remains known-bad.
- Eyes STEPS dead-lever (plain-euler ODE refines the same trajectory —
  mechanism, not calibration).
- Trap-11 guide/max mechanics; slot-0 measurement rule; determinism method.
- Eyes feather/composite fixes (compositing mechanics).

## RESTING ON DEAD CALIBRATION — recommend re-testing on PC (batch L)
1. **#617 Z-USDU denoise 0.25** — inherited from the SDXL USDU sweep (Q4).
   Arms: 0.15 / 0.35.
2. **#98 Z-USDU denoise 0.08** — inherited. Arms: 0.05 / 0.12.
3. **Eyes denoise 0.42** — never swept on ANY architecture. Arms: 0.30/0.55.
4. **Face steps 8** — Q3's speckle finding was measured on the SHIP arch.
   One arm: 12.
5. **Face bbox_crop_factor 1.5** — Q2's "sideways" verdict was SHIP-arch;
   LOW priority (mechanism partly carries); not in batch L, flagged only.
6. **#98 whole-frame tile (GetImageSize wiring)** — Q4 recommended 1024
   tiles for VRAM; never applied; PC renders fine on this 96 GB card and
   whole-frame tiling cannot seam. Carried DELIBERATELY for the personal
   build; revisit only on smaller cards.

## The additive-freckle hypothesis (owner chase #2) — test design
res_multistep's texture increment may be ~constant, so it HELPS where the
base lacks texture (old S4) and OVERSHOOTS where the base has it (S11).
2x2: base {8/cfg1, 30/cfg2} x face sampler {ea, rms}, all else PC.
G_PC1 and G_PC_rms are the 30/cfg2 pair; batch L renders the 8/cfg1 pair.
Rule confirmed if faceHF(rms-ea) is ≈equal at both base levels AND the eye
prefers rms only on the low-texture base. If confirmed: "choose face
sampler by the base's existing texture level" goes in CONFIG-SPEC as a
character/composition rule, and res_multistep KEEPS its place in the tiled
refine slots (where it feeds texture the 1.6x resample stripped).

## Batch L results (2026-08-08 ~01:1x; PC1 baseline cos .799 / faceHF 9.73 / bodyHF 9.60)

| lever | arms | result | verdict |
|---|---|---|---|
| #617 denoise | 0.15 / 0.35 | .744 / .795 | 0.25 CONFIRMED (0.15 loses likeness — the Z refine pulls TOWARD the character; starving it hurts) |
| #98 denoise | 0.05 / 0.12 | .788 / .793 | near-dead lever; 0.08 stands |
| eyes denoise | 0.30 / 0.55 | .793 / .800 | flat; 0.42 stands |
| face steps | 12 | .762 | 8 RE-CONFIRMED on PC |
| additive 2x2 | 8/1 pair | rms increment +0.43 vs +0.55 at 30/2 | ADDITIVE RULE HOLDS (≈constant increment); rms loses cos at BOTH bases on PC |
| tiled refines ea | 617+98 -> euler_ancestral | **.809, bodyHF 9.94** | the ONE arm beating the S11 pick on metric; rms now wins NOWHERE measurable on PC. NOT silently adopted — S18 sheet for the owner (their S3 body verdict was formed with rms in these slots; HF-band proxies failed to capture that difference before) |

Answer to the owner's "if res_multistep still wins somewhere, show me where":
on the PC architecture, nowhere I measured — face (S11), and now the tiled
slots (L_usdu_ea beats it on likeness AND body-texture band). Its S4 win
was a property of the texture-poor SHIP architecture. The additive rule
explains both: rms adds a ~fixed texture increment; add it only where the
base lacks texture.
