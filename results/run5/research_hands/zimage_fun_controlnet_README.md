---
license: apache-2.0
library_name: videox_fun
---

# Z-Image-Turbo-Fun-Controlnet-Union-2.1

[![Github](https://img.shields.io/badge/🎬%20Code-VideoX_Fun-blue)](https://github.com/aigc-apps/VideoX-Fun)

## Update
- **[2026.02.26]** Update to version 2602, with support for Gray Control.
- **[2026.01.12]** Update to version 2601, with support for Scribble Control. Added lite models (1.9GB, 5 layers). Retrained Control and Tile models with enriched mask varieties, improved training schedules, and multi-resolution control images (512~1536) to fix mask pattern leakage and large `control_context_scale` artifacts.
- **[2025.12.22]** Performed 8-step distillation on v2.1 to restore acceleration lost when applying ControlNet. Uploaded a tile model for super-resolution.
- **[2025.12.17]** Fixed v2.0 typo (`control_layers` used instead of `control_noise_refiner`), which caused double forward pass and slow inference. Speed restored in v2.1.

## Model Card
### a. 2602 Models
| Name | Description |
|--|--|
| Z-Image-Turbo-Fun-Controlnet-Union-2.1-2602-8steps.safetensors | Supports multiple control conditions (Canny, Depth, Pose, MLSD, Hed, Scribble, and Gray).|
| Z-Image-Turbo-Fun-Controlnet-Union-2.1-lite-2602-8steps.safetensors | Same training scheme as the 2601 version, but with control applied to fewer layers. Supports multiple control conditions (Canny, Depth, Pose, MLSD, Hed, Scribble, and Gray). |

### b. 2601 Models
| Name | Description |
|--|--|
| Z-Image-Turbo-Fun-Controlnet-Union-2.1-2601-8steps.safetensors | Compared to the old version, this model uses more diverse masks, a more reasonable training schedule, and multi-resolution control images (512–1536) instead of single resolution (512). This reduces artifacts and mask information leakage while improving robustness. Supports multiple control conditions (Canny, Depth, Pose, MLSD, Hed, and Scribble). |
| Z-Image-Turbo-Fun-Controlnet-Tile-2.1-2601-8steps.safetensors | Compared to the old version, uses higher training resolution and a more refined distillation schedule, reducing bright spots and artifacts. |
| Z-Image-Turbo-Fun-Controlnet-Union-2.1-lite-2601-8steps.safetensors | Same training scheme as the 2601 version, but with control applied to fewer layers, resulting in weaker control. This allows for larger control_context_scale values with more natural results, and is also better suited for lower-spec machines. Supports multiple control conditions (Canny, Depth, Pose, MLSD, Hed, and Scribble). |
| Z-Image-Turbo-Fun-Controlnet-Tile-2.1-lite-2601-8steps.safetensors | Same training scheme as the 2601 version, but with control applied to fewer layers, resulting in weaker control. Allows larger control_context_scale values with more natural results, and better suits lower-spec machines. |

### c. Models Before 2601
| Name | Description |
|--|--|
| Z-Image-Turbo-Fun-Controlnet-Union-2.1-8steps.safetensors | Distilled from version 2.1 using an 8-step distillation algorithm. Compared to version 2.1, 8-step prediction yields clearer images with more reasonable composition. Supports Canny, Depth, Pose, MLSD, and Hed. |
| Z-Image-Turbo-Fun-Controlnet-Tile-2.1-8steps.safetensors | A Tile model trained on high-definition datasets (up to 2048×2048) for super-resolution, distilled using an 8-step algorithm. 8-step prediction is recommended. |
| Z-Image-Turbo-Fun-Controlnet-Union-2.1.safetensors | A retrained model fixing the typo in version 2.0, with faster single-step speed. Supports Canny, Depth, Pose, MLSD, and Hed. However, like version 2.0, some acceleration capability was lost during training, requiring more steps and cfg. |
| Z-Image-Turbo-Fun-Controlnet-Union-2.0.safetensors | ControlNet weights for Z-Image-Turbo. Compared to version 1.0, more layers are modified with longer training. However, a code typo caused layer blocks to forward twice, resulting in slower speed. Supports Canny, Depth, Pose, MLSD, and Hed. Some acceleration capability was lost during training, requiring more steps. |

## Model Features
- This ControlNet is applied to 15 layer blocks and 2 refiner layer blocks (Lite models: 3 layer blocks and 2 refiner layer blocks). It supports multiple control conditions including Canny, HED, Depth, Pose, and MLSD (supporting Scribble in 2601 models and Gray in 2602 models).
- Inpainting mode is also supported. For inpaint mode, use a larger `control_context_scale` for better image continuity.
- **Training Process:**
  - **2.0:** Trained from scratch for 70,000 steps on 1M high-quality images (general and human-centric content) at 1328 resolution with BFloat16 precision, batch size 64, learning rate 2e-5, and text dropout ratio 0.10.
  - **2.1:** Continued training from 2.0 weights for 11,000 additional steps after fixing a typo, using the same parameters and dataset.
  - **2.1-8-steps:** Distilled from version 2.1 using an 8-step distillation algorithm for 5,500 steps.
- **Note on Steps:**
  - **2.0 and 2.1:** Higher `control_context_scale` values may require more inference steps for better results, likely because the control model has not been distilled.
  - **2.1-8-steps:** Use 8 steps for inference.
- Adjust `control_context_scale` (optimal range: 0.65–1.00) for stronger control and better detail preservation. A detailed prompt is highly recommended for stability.
- In versions 2.0 and 2.1, applying ControlNet to Z-Image-Turbo caused loss of acceleration capability and blurry images. For strength and step count testing details, refer to [Scale Test Results](#scale-test-results) (generated with version 2.0).

## Results
### a. Difference between 2.1-8steps and 2.1-2601-8steps.

The old 8-steps model had bright spots/artifacts when the control_context_scale was too large, while the new version does not.

<table border="0" style="width: 100%; text-align: left; margin-top: 20px;">
  <tr>
    <td>Z-Image-Turbo-Fun-Controlnet-Union-2.1-8steps</td>
    <td>Z-Image-Turbo-Fun-Controlnet-Union-2.1-2601-8steps</td>
  </tr>
  <tr>
    <td><img src="results/hed_2_1.png" width="100%" /></td>
    <td><img src="results/hed_2_1_2601.png" width="100%" /></td>
  </tr>
</table>

The old 8-steps model sometimes learned the mask information and tended to completely fill the mask during removal, while the new version does not.

<table border="0" style="width: 100%; text-align: left; margin-top: 20px;">
  <tr>
    <td>Z-Image-Turbo-Fun-Controlnet-Union-2.1-8steps</td>
    <td>Z-Image-Turbo-Fun-Controlnet-Union-2.1-2601-8steps</td>
  </tr>
  <tr>
    <td><img src="results/mask_2_1.png" width="100%" /></td>
    <td><img src="results/mask_2_1_2601.png" width="100%" /></td>
  </tr>
</table>

### b. Difference between 2.1 and 2.1-8steps.

8 steps results:
<table border="0" style="width: 100%; text-align: left; margin-top: 20px;">
  <tr>
    <td>Z-Image-Turbo-Fun-Controlnet-Union-2.1-8steps</td>
    <td>Z-Image-Turbo-Fun-Controlnet-Union-2.1</td>
  </tr>
  <tr>
    <td><img src="results/8steps.png" width="100%" /></td>
    <td><img src="results/nsteps.png" width="100%" /></td>
  </tr>
</table>

### c. Generation Results With 2.1-lite-2601-8steps

Shares the same training scheme as the 2601 version, but with control applied to fewer layers, resulting in weaker control. This allows for larger control_context_scale values with more natural results, and is also better suited for lower-spec machines.

<table border="0" style="width: 100%; text-align: left; margin-top: 20px;">
  <tr>
    <td>Pose</td>
    <td>Output</td>
  </tr>
  <tr>
    <td><img src="asset/pose.jpg" width="100%" /></td>
    <td><img src="results/pose_lite.png" width="100%" /></td>
  </tr>
</table>

<table border="0" style="width: 100%; text-align: left; margin-top: 20px;">
  <tr>
    <td>Pose</td>
    <td>Output</td>
  </tr>
  <tr>
    <td><img src="asset/pose2.jpg" width="100%" /></td>
    <td><img src="results/pose2_lite.png" width="100%" /></td>
  </tr>
</table>

<table border="0" style="width: 100%; text-align: left; margin-top: 20px;">
  <tr>
    <td>Canny</td>
    <td>Output</td>
  </tr>
  <tr>
    <td><img src="asset/canny.jpg" width="100%" /></td>
    <td><img src="results/canny_lite.png" width="100%" /></td>
  </tr>
</table>

<table border="0" style="width: 100%; text-align: left; margin-top: 20px;">
  <tr>
    <td>Depth</td>
    <td>Output</td>
  </tr>
  <tr>
    <td><img src="asset/depth.jpg" width="100%" /></td>
    <td><img src="results/depth_lite.png" width="100%" /></td>
  </tr>

### d. Generation Results With 2.1-2601-8steps

<table border="0" style="width: 100%; text-align: left; margin-top: 20px;">
  <tr>
    <td>Pose + Inpaint</td>
    <td>Output</td>
  </tr>
  <tr>
    <td><img src="asset/inpaint.jpg" width="100%" /><img src="asset/mask.jpg" width="100%" /></td>
    <td><img src="results/inpaint.png" width="100%" /></td>
  </tr>
</table>

<table border="0" style="width: 100%; text-align: left; margin-top: 20px;">
  <tr>
    <td>Pose + Inpaint</td>
    <td>Output</td>
  </tr>
  <tr>
    <td><img src="asset/inpaint.jpg" width="100%" /><img src="asset/mask.jpg" width="100%" /><img src="asset/pose.jpg" width="100%" /></td>
    <td><img src="results/pose_inpaint.png" width="100%" /></td>
  </tr>
</table>

<table border="0" style="width: 100%; text-align: left; margin-top: 20px;">
  <tr>
    <td>Pose</td>
    <td>Output</td>
  </tr>
  <tr>
    <td><img src="asset/pose2.jpg" width="100%" /></td>
    <td><img src="results/pose2.png" width="100%" /></td>
  </tr>
</table>

<table border="0" style="width: 100%; text-align: left; margin-top: 20px;">
  <tr>
    <td>Pose</td>
    <td>Output</td>
  </tr>
  <tr>
    <td><img src="asset/pose.jpg" width="100%" /></td>
    <td><img src="results/pose.png" width="100%" /></td>
  </tr>
</table>

<table border="0" style="width: 100%; text-align: left; margin-top: 20px;">
  <tr>
    <td>Pose</td>
    <td>Output</td>
  </tr>
  <tr>
    <td><img src="asset/pose3.jpg" width="100%" /></td>
    <td><img src="results/pose3.png" width="100%" /></td>
  </tr>
</table>

<table border="0" style="width: 100%; text-align: left; margin-top: 20px;">
  <tr>
    <td>Canny</td>
    <td>Output</td>
  </tr>
  <tr>
    <td><img src="asset/canny.jpg" width="100%" /></td>
    <td><img src="results/canny.png" width="100%" /></td>
  </tr>
</table>

<table border="0" style="width: 100%; text-align: left; margin-top: 20px;">
  <tr>
    <td>HED</td>
    <td>Output</td>
  </tr>
  <tr>
    <td><img src="asset/hed.jpg" width="100%" /></td>
    <td><img src="results/hed.png" width="100%" /></td>
  </tr>
</table>

<table border="0" style="width: 100%; text-align: left; margin-top: 20px;">
  <tr>
    <td>Depth</td>
    <td>Output</td>
  </tr>
  <tr>
    <td><img src="asset/depth.jpg" width="100%" /></td>
    <td><img src="results/depth.png" width="100%" /></td>
  </tr>
</table>

<table border="0" style="width: 100%; text-align: left; margin-top: 20px;">
  <tr>
    <td>Low Resolution</td>
    <td>High Resolution</td>
  </tr>
  <tr>
    <td><img src="asset/low_res.jpg" width="100%" /></td>
    <td><img src="results/high_res.png" width="100%" /></td>
  </tr>
</table>

### e. Gray Control Results with 2602 Models

<table border="0" style="width: 100%; text-align: left; margin-top: 20px;">
  <tr>
    <td>Low Resolution</td>
    <td>High Resolution</td>
  </tr>
  <tr>
    <td><img src="asset/gray.jpg" width="100%" /></td>
    <td><img src="results/gray.png" width="100%" /></td>
  </tr>
</table>

## Inference
Go to the VideoX-Fun repository for more details.

Please clone the VideoX-Fun repository and create the required directories:

```sh
# Clone the code
git clone https://github.com/aigc-apps/VideoX-Fun.git

# Enter VideoX-Fun's directory
cd VideoX-Fun

# Create model directories
mkdir -p models/Diffusion_Transformer
mkdir -p models/Personalized_Model
```

Then download the weights into models/Diffusion_Transformer and models/Personalized_Model.

```
📦 models/
├── 📂 Diffusion_Transformer/
│   └── 📂 Z-Image-Turbo/
├── 📂 Personalized_Model/
│   ├── 📦 Z-Image-Turbo-Fun-Controlnet-Union-2.1.safetensors
│   ├── 📦 Z-Image-Turbo-Fun-Controlnet-Union-2.1-8steps.safetensors
│   └── 📦 Z-Image-Turbo-Fun-Controlnet-Tile-2.1-8steps.safetensors
```

Then run the file `examples/z_image_fun/predict_t2i_control_2.1.py` and `examples/z_image_fun/predict_i2i_inpaint_2.1.py`.

<details>
  <summary>(Obsolete) Scale Test Results:</summary>

## Scale Test Results

The table below shows the generation results under different combinations of Diffusion steps and Control Scale strength:

| Diffusion Steps | Scale 0.65 | Scale 0.70 | Scale 0.75 | Scale 0.8 | Scale 0.9 | Scale 1.0 |
|:---------------:|:----------:|:----------:|:----------:|:---------:|:---------:|:---------:|
| **9** | ![](results/scale_test/9_scale_0.65.png) | ![](results/scale_test/9_scale_0.70.png) | ![](results/scale_test/9_scale_0.75.png) | ![](results/scale_test/9_scale_0.8.png) | ![](results/scale_test/9_scale_0.9.png) | ![](results/scale_test/9_scale_1.0.png) |
| **10** | ![](results/scale_test/10_scale_0.65.png) | ![](results/scale_test/10_scale_0.70.png) | ![](results/scale_test/10_scale_0.75.png) | ![](results/scale_test/10_scale_0.8.png) | ![](results/scale_test/10_scale_0.9.png) | ![](results/scale_test/10_scale_1.0.png) |
| **20** | ![](results/scale_test/20_scale_0.65.png) | ![](results/scale_test/20_scale_0.70.png) | ![](results/scale_test/20_scale_0.75.png) | ![](results/scale_test/20_scale_0.8.png) | ![](results/scale_test/20_scale_0.9.png) | ![](results/scale_test/20_scale_1.0.png) |
| **30** | ![](results/scale_test/30_scale_0.65.png) | ![](results/scale_test/30_scale_0.70.png) | ![](results/scale_test/30_scale_0.75.png) | ![](results/scale_test/30_scale_0.8.png) | ![](results/scale_test/30_scale_0.9.png) | ![](results/scale_test/30_scale_1.0.png) |
| **40** | ![](results/scale_test/40_scale_0.65.png) | ![](results/scale_test/40_scale_0.70.png) | ![](results/scale_test/40_scale_0.75.png) | ![](results/scale_test/40_scale_0.8.png) | ![](results/scale_test/40_scale_0.9.png) | ![](results/scale_test/40_scale_1.0.png) |

Parameter Description:

Diffusion Steps: Number of iteration steps for the diffusion model (9, 10, 20, 30, 40)
Control Scale: Control strength coefficient (0.65 - 1.0)
</details>