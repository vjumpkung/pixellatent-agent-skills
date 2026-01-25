---
name: comfyui-custom-nodes-backend
description: Comprehensive guide for developing ComfyUI custom nodes backend in Python. Use this skill when creating, modifying, or debugging ComfyUI custom nodes, working with ComfyUI datatypes (IMAGE, LATENT, MASK, CONDITIONING, MODEL, etc.), implementing node properties (INPUT_TYPES, RETURN_TYPES, FUNCTION), handling images/masks/latents as torch.Tensor, implementing lazy evaluation, node expansion, data lists, or any ComfyUI node backend development task.
---

# ComfyUI Custom Nodes Backend Development

This skill provides complete guidance for developing ComfyUI custom node backends in Python.

## Node Structure Overview

Every custom node is a Python class with these key properties:

```python
class MyCustomNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": { "image_in": ("IMAGE", {}) },
            "optional": { ... },
            "hidden": { ... }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image_out",)
    CATEGORY = "examples"
    FUNCTION = "process"
    OUTPUT_NODE = False  # Set True for output nodes

    def process(self, image_in):
        image_out = 1 - image_in
        return (image_out,)
```

## Main Properties

### INPUT_TYPES (classmethod)
Returns a `dict` with keys:
- `required`: Inputs that must be connected
- `optional`: Inputs that can be left unconnected (provide defaults in function)
- `hidden`: Special inputs like `UNIQUE_ID`, `PROMPT`, `EXTRA_PNGINFO`, `DYNPROMPT`

Each input is defined as: `"name": ("TYPE", {options})`

### RETURN_TYPES
Tuple of strings defining output datatypes: `RETURN_TYPES = ("IMAGE", "MASK")`
- Empty tuple if no outputs: `RETURN_TYPES = ()`
- Single output needs trailing comma: `RETURN_TYPES = ("IMAGE",)`

### RETURN_NAMES (optional)
Labels for outputs. Defaults to lowercase RETURN_TYPES if omitted.

### CATEGORY
Menu location: `"examples/trivial"` creates submenu.

### FUNCTION
Name of the method to call. Method receives named arguments and returns tuple matching RETURN_TYPES.

### OUTPUT_NODE
Set `True` for nodes that produce final output (like Save Image).

### IS_CHANGED (classmethod)
Override caching behavior. Return any Python object; node re-executes if value differs from previous run.
- Return `float("NaN")` to always execute
- Example: return file hash for LoadImage

```python
@classmethod
def IS_CHANGED(cls, image):
    image_path = folder_paths.get_annotated_filepath(image)
    m = hashlib.sha256()
    with open(image_path, 'rb') as f:
        m.update(f.read())
    return m.digest().hex()
```

## Datatypes

### Python Types
| Type | Options | Notes |
|------|---------|-------|
| `INT` | `default` (required), `min`, `max` | |
| `FLOAT` | `default` (required), `min`, `max`, `step` | |
| `STRING` | `default` (required), `multiline`, `placeholder` | |
| `BOOLEAN` | `default` (required), `label_on`, `label_off` | |

### COMBO (Dropdown)
Defined by `list[str]` instead of type string:
```python
"ckpt_name": (folder_paths.get_filename_list("checkpoints"), )
"play_sound": (["no", "yes"], {})
```

### Tensor Types
| Type | Shape | Notes |
|------|-------|-------|
| `IMAGE` | `[B,H,W,C]` C=3 | Batch of RGB images |
| `LATENT` | `dict` with `samples` key `[B,C,H,W]` C=4 | Channel-first |
| `MASK` | `[H,W]` or `[B,H,W]` | Check `len(mask.shape)` |
| `AUDIO` | `dict` with `waveform` `[B,C,T]` and `sample_rate` | |

### Model Types
`MODEL`, `CLIP`, `VAE`, `CONDITIONING` - for stable diffusion models.

### Custom Sampling Types
- `NOISE`: Object with `generate_noise(input_latent) -> Tensor` and `seed` property
- `SAMPLER`: Object with `sample` method
- `SIGMAS`: 1D tensor of length `steps+1`
- `GUIDER`: Callable for denoising process

### Additional Input Options
| Key | Description |
|-----|-------------|
| `default` | Default value |
| `min`, `max` | Number bounds |
| `step` | Increment amount |
| `defaultInput` | Defaults to input socket |
| `forceInput` | Forces input socket, no widget |
| `lazy` | Enables lazy evaluation |
| `rawLink` | Receives link reference instead of value |

## Module Lifecycle

### __init__.py Structure
```python
from .my_nodes import MyCustomNode, AnotherNode

NODE_CLASS_MAPPINGS = {
    "My Custom Node": MyCustomNode,
    "Another Node": AnotherNode
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "My Custom Node": "My Custom Node Display Name"
}
WEB_DIRECTORY = "./js"  # For client-side JavaScript

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
```

## Images, Latents, and Masks

### Working with PIL
```python
from PIL import Image, ImageOps
import torch
import numpy as np

# Load image to tensor [1,H,W,3]
i = Image.open(image_path)
i = ImageOps.exif_transpose(i)
if i.mode == 'I':
    i = i.point(lambda i: i * (1 / 255))
image = i.convert("RGB")
image = np.array(image).astype(np.float32) / 255.0
image = torch.from_numpy(image)[None,]

# Save batch of images
for batch_number, image in enumerate(images):
    i = 255. * image.cpu().numpy()
    img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))
    img.save(filepath)
```

### Mask Operations
```python
# Invert mask
mask = 1.0 - mask

# Convert mask to image shape [B,H,W,C]
if len(mask.shape) == 2:      # [H,W]
    mask = mask[None,:,:,None]
elif len(mask.shape) == 3 and mask.shape[2] == 1:  # [H,W,C]
    mask = mask[None,:,:,:]
elif len(mask.shape) == 3:    # [B,H,W]
    mask = mask[:,:,:,None]

# Use mask as transparency
mask = mask.unsqueeze(-1)
rgba_image = torch.cat((rgb_image, mask), dim=-1)
```

## Hidden Inputs

```python
"hidden": {
    "unique_id": "UNIQUE_ID",      # Node's unique identifier
    "prompt": "PROMPT",            # Complete prompt from client
    "extra_pnginfo": "EXTRA_PNGINFO",  # Metadata for PNG files
    "dynprompt": "DYNPROMPT"       # Mutable prompt during execution
}
```

## Flexible Inputs

### Custom Datatypes
```python
"my_cheese": ("CHEESE", {"forceInput": True})
```

### Wildcard Inputs
```python
@classmethod
def INPUT_TYPES(cls):
    return {"required": {"anything": ("*", {})}}

@classmethod
def VALIDATE_INPUTS(cls, input_types):
    return True
```

### Dynamic Inputs
```python
class ContainsAnyDict(dict):
    def __contains__(self, key):
        return True

@classmethod
def INPUT_TYPES(cls):
    return {"required": {}, "optional": ContainsAnyDict()}

def main_method(self, **kwargs):
    # Access dynamic inputs via kwargs
```

## VALIDATE_INPUTS

```python
@classmethod
def VALIDATE_INPUTS(cls, foo):
    if foo < 0:
        return "foo must be non-negative"
    return True

# Type validation with input_types parameter
@classmethod
def VALIDATE_INPUTS(cls, input_types):
    if input_types["input1"] not in ("INT", "FLOAT"):
        return "input1 must be INT or FLOAT"
    return True
```

## Lazy Evaluation

Defer input evaluation until needed:

```python
@classmethod
def INPUT_TYPES(cls):
    return {
        "required": {
            "image1": ("IMAGE", {"lazy": True}),
            "image2": ("IMAGE", {"lazy": True}),
            "mask": ("MASK",),
        },
    }

def check_lazy_status(self, mask, image1, image2):
    needed = []
    if image1 is None and mask.min() != 1.0:
        needed.append("image1")
    if image2 is None and mask.max() != 0.0:
        needed.append("image2")
    return needed

def mix(self, mask, image1, image2):
    if mask.min() == 0.0 and mask.max() == 0.0:
        return (image1,)
    if mask.min() == 1.0 and mask.max() == 1.0:
        return (image2,)
    return (image1 * (1. - mask) + image2 * mask,)
```

## Execution Blocking

```python
from comfy_execution.graph import ExecutionBlocker

def passthrough(self, value, blocked):
    if blocked:
        return (ExecutionBlocker(None),)  # Silent block
    return (value,)

# With error message
vae = ExecutionBlocker(f"No VAE in model {name}")
```

## Node Expansion

Return subgraph instead of results:

```python
from comfy_execution.graph_utils import GraphBuilder

def expand_node(self, ckpt1, ckpt2, ratio):
    graph = GraphBuilder()
    n1 = graph.node("CheckpointLoaderSimple", checkpoint_path=ckpt1)
    n2 = graph.node("CheckpointLoaderSimple", checkpoint_path=ckpt2)
    merge = graph.node("ModelMergeSimple", model1=n1.out(0), model2=n2.out(0), ratio=ratio)
    return {
        "result": (merge.out(0), n1.out(1), n1.out(2)),
        "expand": graph.finalize(),
    }
```

## Data Lists

### OUTPUT_IS_LIST
Outputs a list for sequential processing:
```python
OUTPUT_IS_LIST = (True,)
```

### INPUT_IS_LIST
Receives all values as lists:
```python
INPUT_IS_LIST = True

def rebatch(self, images, batch_size):
    batch_size = batch_size[0]  # Everything is a list
    # Process list of image batches
    return (output_list,)
```

## torch.Tensor Essentials

### Shape Operations
```python
a = torch.Tensor((1,2))
a.shape                    # torch.Size([2])
a[:,None].shape           # torch.Size([2, 1]) - unsqueeze
a[None,:].shape           # torch.Size([1, 2])
a.reshape((1,-1)).shape   # torch.Size([1, 2])
a.squeeze()               # Remove size-1 dimensions
a.unsqueeze(0)            # Add dimension at position 0
a.unsqueeze(-1)           # Add dimension at end
```

### Elementwise Operations
```python
a * b      # Element-wise multiply (same shape or scalar)
a / b      # Element-wise divide
a == b     # Element-wise comparison (returns tensor of bools)
```

### Tensor Truthiness
```python
# Don't use: if tensor:  (ambiguous for multi-element tensors)
tensor.all()  # True if all elements are true
tensor.any()  # True if any element is true

# Check if tensor exists
if tensor is not None:  # Correct
```

## Custom Noise Example

```python
class MixedNoise:
    def __init__(self, noise1, noise2, weight2):
        self.noise1 = noise1
        self.noise2 = noise2
        self.weight2 = weight2

    @property
    def seed(self):
        return self.noise1.seed

    def generate_noise(self, input_latent: torch.Tensor) -> torch.Tensor:
        n1 = self.noise1.generate_noise(input_latent)
        n2 = self.noise2.generate_noise(input_latent)
        return n1 * (1.0 - self.weight2) + n2 * self.weight2
```

## Common Patterns

### Single Output Return
Always use trailing comma:
```python
return (image,)  # Correct
return (image)   # Wrong - not a tuple
```

### Latent Access
```python
samples = latent["samples"]  # Get tensor [B,C,H,W]
new_latent = {"samples": new_samples}  # Create latent dict
```

### Device Handling
```python
tensor = tensor.to(device)
tensor = tensor.cpu()  # Move to CPU for PIL/numpy operations
```
