---
license: cc0-1.0
language:
- en
tags:
- super-resolution
- image-super-resolution
- sisr
- single-image-super-resolution
- training-dataset
- cc0
- lucid
- hat
- swinir
- diffusion
- image-restoration
task_categories:
- image-to-image
task_ids:
- image-super-resolution
size_categories:
- 1M<n<10M
---

# LUCID-CC0 v2: Large-Scale Curated CC0 Training Dataset for Single-Image Super-Resolution

A large-scale, high-quality training dataset for single-image super-resolution (SISR), filtered from [nyuuzyou/pxhere](https://huggingface.co/datasets/nyuuzyou/pxhere) using the [LUCID filtering pipeline](https://github.com/Phips/lucid-sisr). All source images are CC0-licensed (public domain).

## Overview

| Property | Value |
|----------|-------|
| **Source** | PxHere (CC0) via WebDataset tars |
| **Filtering** | LUCID pipeline (ICNet complexity + signal filter + deduplication) |
| **Tile size** | 256×256 pixels |
| **Multiscale** | Yes (1.0×, 0.75×, 0.5×, 0.25× scales) |
| **Complexity threshold** | ≥ 0.6 (LUCID auto-calibrated) |
| **Deduplication** | Cosine similarity < 0.96 |
| **License** | CC0-1.0 (public domain) |
| **Total tiles** | 1,590,938 |
| **Disk size** | 199 GB |

## Intended Use

This dataset is designed for **training SISR models from scratch**, particularly large transformer-based architectures that are data-hungry:

- **HAT** (Hybrid Attention Transformer)
- **HAT-L** (Large variant)
- **SwinIR**
- **RealESRGAN** / traiNNer-redux
- **Diffusion-based** super-resolution models
- **Any new architecture** that benefits from diverse, high-quality training data

### Recommended Training Strategy

This dataset is part of a three-stage training pipeline:

| Stage | Dataset | Purpose |
|-------|---------|---------|
| **1. Pretrain from scratch** | This dataset (lucid-cc0-v2) | Learn general image representations from diverse CC0 photos |
| **2. Finetune** | [lucid-cc0-v2-hc](https://huggingface.co/Phips/lucid-cc0-v2-hc) (high-complexity, 256×256) | Refine on highest-quality, most detailed tiles |
| **3. Finetune-finetune** | [lucid-cc0-v2-hc-512](https://huggingface.co/Phips/lucid-cc0-v2-hc-512) (high-complexity, 512×512) | Push quality with maximum patch size |

## Dataset Structure

```
lucid-cc0-v2/
├── train/
│   ├── 000/          # ≤10,000 tiles per subdirectory
│   │   ├── 00000.png
│   │   ├── 00001.png
│   │   └── ...
│   ├── 001/
│   └── ...
├── LR/
│   ├── x2/           # Bicubic downscaled ×2 (MATLAB-compatible)
│   └── x4/           # Bicubic downscaled ×4 (MATLAB-compatible)
├── batch_manifest.json
├── lineage_batch_*.csv
└── DATASET_NOTES.md
```

## Filtering Pipeline

Images were filtered using [LUCID](https://github.com/Phips/lucid-sisr) with the following stages:

1. **Signal filter** — Removes low-information images (blurry, overexposed, underexposed, low-contrast)
2. **ICNet complexity scoring** — Neural network estimates perceptual complexity; tiles below threshold are removed
3. **Multiscale tiling** — Images tiled at multiple scales (1.0×, 0.75×, 0.5×, 0.25×) to capture both fine detail and global structure
4. **Deduplication** — Perceptual cosine similarity deduplication (threshold 0.96) removes near-duplicate tiles
5. **Tile extraction** — 256×256 PNG tiles saved with ≤10,000 files per subdirectory

## Source Data

- **Repository**: [nyuuzyou/pxhere](https://huggingface.co/datasets/nyuuzyou/pxhere)
- **Description**: ~1.1M CC0 images from PxHere, stored as WebDataset tars
- **Content**: Professional photography spanning landscapes, architecture, nature, objects, and more
- **License**: CC0-1.0 (public domain)

## Bicubic Downscaling

LR (low-resolution) images are provided alongside HR tiles, downscaled using MATLAB-compatible bicubic interpolation (`a = -0.5` anti-aliased cubic kernel). This matches the standard used in SISR benchmarks (Urban100, Set5, Set14, etc.) and ensures comparable PSNR/SSIM values.

Scale factors: ×2 and ×4.

## Lineage

Each batch produces a `lineage_batch_*.csv` file tracking per-image complexity scores and tile counts for reproducibility.

## Citation

If you use this dataset, please cite:

```bibtex
@dataset{lucid_cc0_v2,
  title={LUCID-CC0 v2: Large-Scale Curated CC0 Training Dataset for SISR},
  author={Phips},
  year={2026},
  license={CC0-1.0},
  url={https://huggingface.co/datasets/Phips/lucid-cc0-v2}
}
```

## Acknowledgments

- Source images from [PxHere](https://pxhere.com/) (CC0)
- Filtering powered by [LUCID](https://github.com/Phips/lucid-sisr)
- Inspired by the SISR community's need for large-scale, ethically-sourced training data
