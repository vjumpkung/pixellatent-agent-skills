---
name: comfyui-migrate-to-v3
description: Guide for migrating ComfyUI custom nodes from V1 (legacy) to V3 schema. Use this skill whenever the user wants to migrate, convert, or update ComfyUI nodes to V3, asks about the new ComfyUI node API, mentions `io.ComfyNode`, `define_schema`, `comfy_entrypoint`, `ComfyExtension`, or `comfy_api`, or is writing new custom nodes and should use the modern schema. Also trigger when the user asks about `INPUT_TYPES`, `NODE_CLASS_MAPPINGS`, or other V1 patterns in the context of updating or modernizing their node code.
---

# ComfyUI V1 → V3 Node Migration

The V3 schema replaces the old V1 pattern (dict-based `INPUT_TYPES`, `NODE_CLASS_MAPPINGS`, etc.) with a class-based API. All future ComfyUI features will only be added to V3.

Import from `comfy_api.latest` for the latest (currently `v0_0_2`) or pin a version explicitly:

```python
from comfy_api.latest import ComfyExtension, io, ui
# or pin: from comfy_api.v0_0_2 import ComfyExtension, io, ui
```

---

## Migration Steps

### Step 1 — Change base class

```python
# V1
class MyNode:
    pass

# V3
from comfy_api.latest import io
class MyNode(io.ComfyNode):
    pass  # No __init__ — all methods are classmethods
```

### Step 2 — Convert `INPUT_TYPES` to `define_schema`

```python
# V1
@classmethod
def INPUT_TYPES(s):
    return {
        "required": {
            "image": ("IMAGE",),
            "count": ("INT", {"default": 0, "min": 0, "max": 4096, "step": 64}),
            "text": ("STRING", {"multiline": False, "default": "Hello"}),
            "mode": (["opt1", "opt2"],),
            "custom_field": ("MY_CUSTOM_TYPE",),
        },
        "optional": {"mask": ("MASK",)},
    }
RETURN_TYPES = ("IMAGE",)
RETURN_NAMES = ("result",)
FUNCTION = "run"
CATEGORY = "my_category"
OUTPUT_NODE = False

# V3
@classmethod
def define_schema(cls) -> io.Schema:
    return io.Schema(
        node_id="MyNode",
        display_name="My Node",
        category="my_category",
        description="Tooltip shown on hover.",
        inputs=[
            io.Image.Input("image"),
            io.Int.Input("count", default=0, min=0, max=4096, step=64),
            io.String.Input("text", default="Hello", multiline=False),
            io.Combo.Input("mode", options=["opt1", "opt2"]),
            io.Custom("MY_CUSTOM_TYPE").Input("custom_field"),
            io.Mask.Input("mask", optional=True),
        ],
        outputs=[
            io.Image.Output(display_name="result"),
        ],
        is_output_node=False,
    )
```

### Step 3 — Rename `execute` / update signature

The method is always named `execute` and is a classmethod:

```python
# V1
def run(self, image, count, text):
    return (image,)

# V3
@classmethod
def execute(cls, image, count, text) -> io.NodeOutput:
    return io.NodeOutput(image)
```

### Step 4 — Rename special methods

| V1 | V3 |
|----|----|
| `VALIDATE_INPUTS(s, **kw)` | `validate_inputs(cls, **kw) -> bool \| str` |
| `IS_CHANGED(s, **kw)` | `fingerprint_inputs(cls, **kw)` |
| `check_lazy_status(self, ...)` | `check_lazy_status(cls, ...)` — same logic, classmethod |

`fingerprint_inputs` note: return the SAME value to reuse cache, a NEW value to force rerun. Returning `True` always means "always cached" (not "always rerun").

### Step 5 — Replace `NODE_CLASS_MAPPINGS` with `comfy_entrypoint`

```python
# V1
NODE_CLASS_MAPPINGS = {"MyNode": MyNode}
NODE_DISPLAY_NAME_MAPPINGS = {"MyNode": "My Node"}

# V3
from comfy_api.latest import ComfyExtension

class MyExtension(ComfyExtension):
    async def get_node_list(self) -> list[type[io.ComfyNode]]:
        return [MyNode, AnotherNode]

async def comfy_entrypoint() -> MyExtension:
    return MyExtension()
```

---

## Type Reference

### Basic types

| V1 | V3 |
|----|----|
| `"INT"` | `io.Int.Input("name", default=0, min=0, max=100)` |
| `"FLOAT"` | `io.Float.Input("name", default=1.0)` |
| `"STRING"` | `io.String.Input("name", multiline=True)` |
| `"BOOLEAN"` | `io.Boolean.Input("name", default=True)` |

### ComfyUI types

> **Note:** Class names use PascalCase, not all-caps. `io.VAE` and `io.CLIP` do NOT exist — use `io.Vae` and `io.Clip`.

| V1 | V3 |
|----|----|
| `"IMAGE"` | `io.Image.Input("name")` |
| `"MASK"` | `io.Mask.Input("name")` |
| `"LATENT"` | `io.Latent.Input("name")` |
| `"CONDITIONING"` | `io.Conditioning.Input("name")` |
| `"MODEL"` | `io.Model.Input("name")` |
| `"VAE"` | `io.Vae.Input("name")` |
| `"CLIP"` | `io.Clip.Input("name")` |
| `"CLIP_VISION"` | `io.ClipVision.Input("name")` |
| `"CLIP_VISION_OUTPUT"` | `io.ClipVisionOutput.Input("name")` |
| `"CONTROL_NET"` | `io.ControlNet.Input("name")` |
| `"STYLE_MODEL"` | `io.StyleModel.Input("name")` |
| `"UPSCALE_MODEL"` | `io.UpscaleModel.Input("name")` |
| `"AUDIO"` | `io.Audio.Input("name")` |
| `"NOISE"` | `io.Noise.Input("name")` |
| `"SAMPLER"` | `io.Sampler.Input("name")` |
| `"SIGMAS"` | `io.Sigmas.Input("name")` |
| `"GUIDER"` | `io.Guider.Input("name")` |
| `"MODEL_PATCH"` | `io.ModelPatch.Input("name")` |
| `"AUDIO_ENCODER_OUTPUT"` | `io.AudioEncoderOutput.Input("name")` |

### Custom types

```python
# Simple — use the helper inline
io.Custom("MY_TYPE").Input("field_name")
io.Custom("MY_TYPE").Output()

# Full definition with decorator
@io.comfytype(io_type="MY_TYPE")
class MyType:
    Type = any
    class Input(io.Input):
        def __init__(self, id: str, **kwargs): super().__init__(id, **kwargs)
    class Output(io.Output):
        def __init__(self, **kwargs): super().__init__(**kwargs)
```

### Seed / control_after_generate

```python
io.Int.Input("seed", default=0, min=0, max=0xFFFFFFFFFFFFFFFF,
    control_after_generate=io.ControlAfterGenerate.randomize)
# or just: control_after_generate=True  (same as randomize)
```

---

## Common Input Parameters

All inputs accept:
- `optional=True` — makes the input optional
- `tooltip="..."` — hover text
- `advanced=True` — hidden behind "Advanced" toggle
- `lazy=True` — lazy evaluation
- `display_name="..."` — UI label override

Widget inputs (Int, Float, String, Boolean, Combo) also accept:
- `default=...` — default value
- `socketless=True` — widget only, no socket
- `force_input=True` — socket only, no widget

---

## Hidden Inputs

```python
# V1: declared in INPUT_TYPES "hidden" dict, received as args
# V3: declared in Schema.hidden, accessed via cls.hidden

@classmethod
def define_schema(cls) -> io.Schema:
    return io.Schema(
        node_id="MyNode",
        inputs=[...],
        hidden=[io.Hidden.unique_id, io.Hidden.prompt, io.Hidden.extra_pnginfo],
    )

@classmethod
def execute(cls, ...) -> io.NodeOutput:
    print(cls.hidden.unique_id)
```

Output nodes (`is_output_node=True`) automatically receive `prompt` and `extra_pnginfo`.

---

## NodeOutput & UI Helpers

```python
from comfy_api.latest import ui

# Single or multiple outputs (order matches Schema.outputs list)
return io.NodeOutput(image)
return io.NodeOutput(width, height, batch_size)

# With UI preview
return io.NodeOutput(image, ui=ui.PreviewImage(image, cls=cls))
return io.NodeOutput(ui=ui.PreviewText("some text"))
return io.NodeOutput(ui=ui.PreviewAudio(audio, cls=cls))

# Save to output folder (output nodes)
return io.NodeOutput(
    ui=ui.ImageSaveHelper.get_save_images_ui(
        images=images, filename_prefix=prefix, cls=cls
    )
)
```

---

## Progress Reporting (replaces `comfy.utils.PROGRESS_BAR_HOOK`)

```python
from comfy_api.latest import ComfyAPI
api = ComfyAPI()

@classmethod
async def execute(cls, images, **kwargs) -> io.NodeOutput:
    for i, img in enumerate(images):
        process(img)
        await api.execution.set_progress(value=i+1, max_value=len(images))
    return io.NodeOutput(result)
```

---

## Advanced: MatchType, Autogrow, DynamicCombo

These are V3-only features with no V1 equivalent.

**MatchType** — type-linked inputs/outputs (for Switch, CreateList patterns):
```python
template = io.MatchType.Template("t")
inputs=[
    io.MatchType.Input("on_false", template=template, lazy=True),
    io.MatchType.Input("on_true", template=template, lazy=True),
]
outputs=[io.MatchType.Output(template=template)]
```

**Autogrow** — variable-count inputs:
```python
tpl = io.Autogrow.TemplatePrefix(input=io.Image.Input("image"), prefix="image", min=2, max=50)
inputs=[io.Autogrow.Input("images", template=tpl)]
# execute receives images as dict: {"image0": ..., "image1": ...}
```

**DynamicCombo** — mode-dependent inputs:
```python
io.DynamicCombo.Input("resize_type", options=[
    io.DynamicCombo.Option("by dimensions", [io.Int.Input("width"), io.Int.Input("height")]),
    io.DynamicCombo.Option("by multiplier", [io.Float.Input("multiplier", default=1.0)]),
])
# execute receives resize_type as dict: {"resize_type": "by dimensions", "width": 512, ...}
```

---

## Node Replacement (for deprecating old node IDs)

Register in `on_load` so old workflows automatically remap:

```python
from comfy_api.latest import ComfyAPI
api = ComfyAPI()

class MyExtension(ComfyExtension):
    async def on_load(self) -> None:
        await api.node_replacement.register(io.NodeReplace(
            new_node_id="MyNewNode",
            old_node_id="MyOldNode",
            old_widget_ids=["param1", "param2"],  # positional widget order in old node
            input_mapping=[
                {"new_id": "image", "old_id": "input_image"},
                {"new_id": "method", "set_value": "lanczos"},
            ],
            output_mapping=[{"new_idx": 0, "old_idx": 0}],
        ))
```

`old_widget_ids` maps positional indexes (how workflow JSON stores widget values) to input IDs.

---

## Schema Field Reference

| Field | Default | Description |
|-------|---------|-------------|
| `node_id` | required | Globally unique. Prefix with pack name to avoid clashes. |
| `display_name` | `node_id` | Label in UI |
| `category` | `"sd"` | Menu path, e.g. `"image/transform"` |
| `description` | `""` | Hover tooltip |
| `is_output_node` | `False` | Shows Run button; auto-receives prompt/extra_pnginfo |
| `is_deprecated` | `False` | Flags node as deprecated in UI |
| `is_experimental` | `False` | Flags node as experimental |
| `not_idempotent` | `False` | Always reruns, never reuses cached output |
| `search_aliases` | `[]` | Alternative search names |
| `accept_all_inputs` | `False` | Pass all prompt kwargs even if not in schema |
