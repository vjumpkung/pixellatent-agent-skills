# ComfyUI Data and Tensors

Use this reference for backend code that reads or writes ComfyUI images, masks, latents, audio, or batches. These runtime formats remain relevant even when older documentation shows V1 node declarations.

## Core Shapes

| Wire type | Runtime representation | Important detail |
|---|---|---|
| `IMAGE` | `torch.Tensor[B, H, W, C]` | Channel-last, normally floating point in `[0, 1]`; do not assume batch size 1. |
| `MASK` | `torch.Tensor[H, W]` or `[B, H, W]` | Normalize dimensions deliberately; do not use an unconstrained `squeeze()`. |
| `LATENT` | dictionary with `samples: Tensor[B, C, H, W]` | Channel count and spatial compression depend on the model; preserve other dictionary keys. |
| `AUDIO` | dictionary containing waveform and sample-rate metadata | Confirm exact keys against the target ComfyUI API. |

Model objects such as MODEL, CLIP, VAE, CONDITIONING, CONTROL_NET, NOISE, SAMPLER, SIGMAS, and GUIDER are opaque ComfyUI values. Use their public APIs; do not copy, serialize, or move them as tensors unless their contract says to.

## Tensor Rules

- Preserve batch dimensions unless the node explicitly changes batching.
- Keep output tensors on the compatible device and preserve dtype. Avoid unconditional `.cpu()`, `.cuda()`, `.float()`, or `.half()` calls.
- Create constants with the input tensor's device and dtype (`tensor.new_zeros(...)`, `torch.zeros_like(...)`) when practical.
- Treat image and mask ranges explicitly. Clamp only when the operation promises a bounded image; silent clamping can hide algorithm errors.
- Avoid testing a multi-element tensor directly in an `if`; use reductions such as `torch.all`, `torch.any`, `.min()`, or `.max()` and convert scalar results when needed.
- Use broadcasting only after documenting compatible shapes.

## Images and PIL

Convert a single RGB PIL image to a one-item IMAGE batch:

```python
import numpy as np
import torch
from PIL import ImageOps


pil_image = ImageOps.exif_transpose(pil_image).convert("RGB")
array = np.asarray(pil_image, dtype=np.float32) / 255.0
image = torch.from_numpy(array).unsqueeze(0)  # [1, H, W, 3]
```

Convert each item in an IMAGE batch to PIL only at an I/O boundary:

```python
from PIL import Image
import numpy as np
import torch


pil_images = []
for item in images:
    array = item.detach().clamp(0, 1).mul(255).to("cpu", torch.uint8).numpy()
    pil_images.append(Image.fromarray(array))
```

Moving to CPU is appropriate here because PIL/NumPy require host data; keep tensor-native processing on the original device.

## Masks

Normalize masks to `[B, H, W, 1]` for channel-last image arithmetic:

```python
def mask_to_bhwc(mask: torch.Tensor) -> torch.Tensor:
    if mask.ndim == 2:
        return mask.unsqueeze(0).unsqueeze(-1)
    if mask.ndim == 3:
        return mask.unsqueeze(-1)
    if mask.ndim == 4 and mask.shape[-1] == 1:
        return mask
    raise ValueError(f"Expected [H,W], [B,H,W], or [B,H,W,1], got {tuple(mask.shape)}")
```

Before mixing, make the batch and spatial compatibility explicit. Decide whether a one-item mask may broadcast across an image batch; reject other mismatches with a useful error.

## Latents

Do not replace a latent dictionary with only a `samples` key, because additional metadata may be meaningful to downstream nodes:

```python
samples = latent["samples"]
result = dict(latent)
result["samples"] = transform(samples)
return io.NodeOutput(result)
```

Do not assume latent channel count is four or that its spatial scale is always eight. Derive shape from `samples` and use the target model/VAE behavior when converting between pixel and latent space.

## Batches Versus Data Lists

A batch is contained inside one value, such as an IMAGE tensor with `B > 1`. A ComfyUI data list is a collection of values that the execution engine maps across nodes. They are not interchangeable.

- Process tensor batches vectorially when possible.
- Use `Schema.is_input_list=True` only when `execute` is designed to receive lists for every input.
- Use `Output(..., is_output_list=True)` only when returning a data list for list-aware downstream execution.
- Do not mark a batched IMAGE tensor as an output list.

## Validation Targets

For tensor nodes, test at least:

- batch sizes 1 and greater than 1;
- non-square dimensions;
- optional mask absent;
- 2D and batched masks where supported;
- CPU and the available accelerator;
- the dtypes the node claims to support;
- latent dictionaries with an unrelated metadata key, verifying it survives.
