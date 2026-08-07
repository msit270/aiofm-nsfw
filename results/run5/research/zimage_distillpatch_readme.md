---
license: apache-2.0
---
# Z-Image Turbo Acceleration Capability Fix LoRA

## Model Introduction

This model is a LoRA used to fix the acceleration capability of Z-Image Turbo LoRA.

LoRAs trained directly based on Z-Image Turbo will lose their acceleration capability. Images generated under acceleration configuration (steps=8, cfg=1) become blurry, while images generated under non-acceleration configuration (steps=30, cfg=2) remain normal.


## Results

Training Data:

![](assets/training_data.jpg)

Generation Results:

|steps=8, cfg=1|steps=30, cfg=2|steps=8, cfg=1, with our model fix|
|-|-|-|
|![](assets/image_base_acc.jpg)|![](assets/image_base_nonacc.jpg)|![](assets/image_with_our_lora.jpg)|

## Training with Z-Image Turbo

If you want to train LoRAs based on Z-Image Turbo while maintaining its acceleration capability, please refer to our detailed training strategies guide:

📖 [**Training Strategies of Z-Image Turbo**](https://huggingface.co/blog/kelseye/training-strategies-of-z-image-turbo)

This guide covers four different training approaches:
- **Scheme 1**: Standard SFT Training + No Acceleration Configuration
- **Scheme 2**: Differential LoRA Training + Acceleration Configuration
- **Scheme 3**: Standard SFT + Trajectory Imitation Distillation + Acceleration Configuration
- **Scheme 4**: Standard SFT + Loading DistillPatch LoRA (Recommended) + Acceleration Configuration

We recommend **Scheme 4** as it offers the best trade-off between training simplicity and inference speed.

## Inference Code

```python
from diffsynth.pipelines.z_image import ZImagePipeline, ModelConfig
import torch

pipe = ZImagePipeline.from_pretrained(
    torch_dtype=torch.bfloat16,
    device="cuda",
    model_configs=[
        ModelConfig(model_id="Tongyi-MAI/Z-Image-Turbo", origin_file_pattern="transformer/*.safetensors"),
        ModelConfig(model_id="Tongyi-MAI/Z-Image-Turbo", origin_file_pattern="text_encoder/*.safetensors"),
        ModelConfig(model_id="Tongyi-MAI/Z-Image-Turbo", origin_file_pattern="vae/diffusion_pytorch_model.safetensors"),
    ],
    tokenizer_config=ModelConfig(model_id="Tongyi-MAI/Z-Image-Turbo", origin_file_pattern="tokenizer/"),
)
pipe.load_lora(pipe.dit, "path/to/your/lora.safetensors")
pipe.load_lora(pipe.dit, ModelConfig(model_id="DiffSynth-Studio/Z-Image-Turbo-DistillPatch", origin_file_pattern="model.safetensors"))

image = pipe(prompt="a dog", seed=42, rand_device="cuda")
image.save("image.jpg")
```