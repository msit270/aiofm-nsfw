#!/usr/bin/env bash
# Final sheet set — run after batches D+E complete.
set -uo pipefail
O=/workspace/run5/output
S=/workspace/nsfw-quality/results/run5/SHEETS
P=/workspace/run5/venv/bin/python
T=/workspace/run5/tools/sheet.py
mkdir -p "$S"

# S2: the winner across compositions vs baseline (full frames)
$P $T "$S/S2_compositions.png" "S2 COMPS: A0-ship vs LUNA-Z on FB / PT / CU (full frames)" full 700 \
  "*A0 FB=$O/A/A0/Instaraw/SDXL/Metadata/HasMetadata_00001_.png" \
  "LUNA-Z FB 0.733=$O/D/D_lunaz_FB/Instaraw/SDXL/Metadata/HasMetadata_00001_.png" \
  "A0 PT (Z-face BLACKED 2of2 boots)=$O/D/A0_PT/Instaraw/SDXL/Metadata/HasMetadata_00001_.png" \
  "LUNA-Z PT=$O/D/D_lunaz_PT/Instaraw/SDXL/Metadata/HasMetadata_00001_.png" \
  "A0 CU=$O/D/A0_CU/Instaraw/SDXL/Metadata/HasMetadata_00001_.png" \
  "LUNA-Z CU=$O/D/D_lunaz_CU/Instaraw/SDXL/Metadata/HasMetadata_00001_.png"

# S3: body skin texture (chest patch crops)
$P $T "$S/S3_body_skin.png" "S3 BODY SKIN: chest crops — ZIT ref / A0 / LUNA-Z / LUNA-Z-30" body 560 \
  "ZIT-ref=$O/A/zref_B_12345/img/img_00001_.png" \
  "*A0-ship bodyHF 6.8=$O/A/A0/Instaraw/SDXL/Metadata/HasMetadata_00001_.png" \
  "LUNA-Z bodyHF 9.7=$O/D/D_lunaz_FB/Instaraw/SDXL/Metadata/HasMetadata_00001_.png" \
  "LUNA-Z-30 0.774 base30/cfg2=$O/D/D_lunaz30_FB_v3/Instaraw/SDXL/Metadata/HasMetadata_00001_.png"

# S4: face-pass sampler pairing (taste)
$P $T "$S/S4_face_sampler.png" "S4 FACE SAMPLER on ship-arch: euler_ancestral(kl_opt) vs res_multistep+simple" face 560 \
  "*A0 euler_ancestral=$O/A/A0/Instaraw/SDXL/Metadata/HasMetadata_00001_.png" \
  "res_multistep+simple 0.612=$O/B/B_rms_simple/Instaraw/SDXL/Metadata/HasMetadata_00001_.png"

# S8: V9 ladder (faces)
$P $T "$S/S8_v9_ladder.png" "S8 V9: naive swap vs repaired stacks (faces)" face 560 \
  "*A0 V7-ship 0.585=$O/A/A0/Instaraw/SDXL/Metadata/HasMetadata_00001_.png" \
  "V9 naive 0.499=$O/B/B_v9/Instaraw/SDXL/Metadata/HasMetadata_00001_.png" \
  "V9+fixboth 0.612=$O/D/D_sdxlfix_FB/Instaraw/SDXL/Metadata/HasMetadata_00001_.png" \
  "E_v9fix_c3s30 0.650=$O/E/E_v9fix_c3s30/Instaraw/SDXL/Metadata/HasMetadata_00001_.png" \
  "E_v9fix_den085 0.708=$O/E/E_v9fix_den085/Instaraw/SDXL/Metadata/HasMetadata_00001_.png" \
  "E_v7fix_den085 0.769=$O/E/E_v7fix_den085/Instaraw/SDXL/Metadata/HasMetadata_00001_.png"

# S9: SDXL face-pass denoise ladder (the identity-vs-airbrush tradeoff)
$P $T "$S/S9_den_ladder.png" "S9 Z-FACE DENOISE on ship-arch: 0.35 ships / 0.50 / 0.65 / 0.85" face 560 \
  "*0.35 ships 0.585=$O/A/A0/Instaraw/SDXL/Metadata/HasMetadata_00001_.png" \
  "0.50 0.638=$O/A/A_den050/Instaraw/SDXL/Metadata/HasMetadata_00001_.png" \
  "0.65 0.664=$O/A/A_den065/Instaraw/SDXL/Metadata/HasMetadata_00001_.png" \
  "0.85 0.696=$O/B/B_den085/Instaraw/SDXL/Metadata/HasMetadata_00001_.png"

# S10: LUNA-Z PT hands (the "hands at her sides" comp) vs A0 PT
$P $T "$S/S10_hands_PT.png" "S10 HANDS on portrait comp (hands at sides)" body 620 \
  "*A0 PT=$O/D/A0_PT/Instaraw/SDXL/Metadata/HasMetadata_00001_.png" \
  "LUNA-Z PT=$O/D/D_lunaz_PT/Instaraw/SDXL/Metadata/HasMetadata_00001_.png"
echo "sheets done"
