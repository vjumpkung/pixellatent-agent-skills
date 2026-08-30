# V3 Node API

Use this reference when creating the node schema, execution method, extension entrypoint, or UI result.

## Version Choice

For a node pack that follows the user's installed ComfyUI:

```python
from comfy_api.latest import ComfyExtension, io, ui
```

For a pack with an explicit compatibility contract, import the numbered API that contract names:

```python
from comfy_api.v0_0_2 import ComfyExtension, io, ui
```

Do not describe `latest` as stable. Before pinning, confirm that the numbered module exists in the oldest supported ComfyUI and that every used symbol is public in that module.

## Minimal Pack

`nodes.py`:

```python
from comfy_api.latest import io


class PixelLatentInvertImage(io.ComfyNode):
    @classmethod
    def define_schema(cls) -> io.Schema:
        return io.Schema(
            node_id="PixelLatent_InvertImage",
            display_name="Invert Image",
            category="pixellatent/image",
            description="Blends an image with its color inverse.",
            inputs=[
                io.Image.Input("image", tooltip="Image batch in BHWC format."),
                io.Float.Input(
                    "strength",
                    default=1.0,
                    min=0.0,
                    max=1.0,
                    step=0.01,
                ),
            ],
            outputs=[
                io.Image.Output("image", display_name="image"),
            ],
        )

    @classmethod
    def execute(cls, image, strength: float) -> io.NodeOutput:
        result = image.lerp(1.0 - image, strength)
        return io.NodeOutput(result)
```

Package `__init__.py`:

```python
from comfy_api.latest import ComfyExtension, io

from .nodes import PixelLatentInvertImage


class PixelLatentExtension(ComfyExtension):
    async def get_node_list(self) -> list[type[io.ComfyNode]]:
        return [PixelLatentInvertImage]


async def comfy_entrypoint() -> PixelLatentExtension:
    return PixelLatentExtension()


__all__ = ["comfy_entrypoint"]
```

Keep node IDs prefixed and stable. Display names and categories may change without changing workflow identity.

## Schema Contract

The commonly used `io.Schema` fields are:

- `node_id`: required globally unique workflow identity.
- `display_name`, `category`, `description`, `search_aliases`: discovery and UI metadata.
- `inputs`, `outputs`, `hidden`: ordered node interface.
- `is_output_node`: makes the node and its dependencies execution roots; output nodes automatically request prompt and extra PNG metadata.
- `is_input_list`: delivers every input as a list.
- `is_deprecated`, `is_experimental`, `is_dev_only`: lifecycle/UI flags.
- `not_idempotent`: marks genuinely non-idempotent behavior; inspect the target version's caching behavior before using it.
- `enable_expand`: required before returning an expanded subgraph.
- `accept_all_inputs`: passes undeclared prompt inputs; use only for a deliberate dynamic contract.

The API may add fields. Inspect the target `io.Schema` signature instead of guessing.

## Inputs and Outputs

Common inputs:

```python
inputs=[
    io.Int.Input("count", default=1, min=1, max=100, step=1),
    io.Float.Input("strength", default=1.0, min=0.0, max=2.0, step=0.05),
    io.String.Input("prompt", default="", multiline=True),
    io.Boolean.Input("enabled", default=True),
    io.Combo.Input("mode", options=["fast", "quality"]),
    io.Image.Input("image"),
    io.Mask.Input("mask", optional=True),
    io.Latent.Input("latent"),
    io.Model.Input("model"),
    io.Vae.Input("vae"),
    io.Clip.Input("clip"),
]
```

All inputs support `display_name`, `optional`, `tooltip`, `lazy`, `raw_link`, and `advanced`. Widget inputs also support `default`, `socketless`, and `force_input`. Use the exact target API spelling; these replace V1 camelCase keys such as `forceInput` and `rawLink`.

Output order is positional:

```python
outputs=[
    io.Image.Output("image", display_name="processed"),
    io.Mask.Output("mask", display_name="mask"),
]

@classmethod
def execute(cls, image, mask=None) -> io.NodeOutput:
    return io.NodeOutput(image, mask)
```

Use `is_output_list=True` on an output only when its value is a ComfyUI data list to be mapped downstream. A batched IMAGE tensor is one IMAGE value, not an output list.

## Optional and Hidden Inputs

An optional schema input can be absent from the execution call. Make that safe in Python:

```python
@classmethod
def execute(cls, image, mask=None) -> io.NodeOutput:
    if mask is None:
        return io.NodeOutput(image)
    return io.NodeOutput(apply_mask(image, mask))
```

Request execution context through the schema and read it from `cls.hidden`:

```python
@classmethod
def define_schema(cls) -> io.Schema:
    return io.Schema(
        node_id="PixelLatent_MetadataNode",
        hidden=[io.Hidden.unique_id, io.Hidden.prompt, io.Hidden.extra_pnginfo],
        outputs=[io.String.Output("node_id")],
    )

@classmethod
def execute(cls) -> io.NodeOutput:
    node_id = cls.hidden.unique_id
    return io.NodeOutput(str(node_id))
```

Other target-dependent values include `io.Hidden.dynprompt` and ComfyOrg authentication fields. Request only what the node uses. Hidden state is execution-scoped; do not save `cls.hidden` for later use.

## Custom and Generic Types

For a pack-specific connection type:

```python
settings_type = io.Custom("PIXELLATENT_SETTINGS")

inputs=[settings_type.Input("settings")]
outputs=[settings_type.Output("settings")]
```

Use `@io.comfytype` when a reusable custom type needs a concrete `Type` annotation or specialized Input/Output classes. Prefix the wire type name to avoid collisions.

Use `io.MultiType`, `io.MatchType`, `io.Autogrow`, or `io.DynamicCombo` only when the interface genuinely needs multiple or dynamic types. Read their constructors from the target API because these are V3-only and more likely to evolve.

## UI Results

Return execution values and UI data together through `io.NodeOutput`:

```python
return io.NodeOutput(image, ui=ui.PreviewImage(image, cls=cls))
return io.NodeOutput(ui=ui.PreviewText("Finished"))
```

For output files, prefer the matching `ui` save helper so filenames, previews, and workflow metadata follow ComfyUI behavior:

```python
return io.NodeOutput(
    ui=ui.ImageSaveHelper.get_save_images_ui(
        images=images,
        filename_prefix=filename_prefix,
        cls=cls,
    )
)
```

Set `is_output_node=True` or explicitly request `io.Hidden.prompt` and `io.Hidden.extra_pnginfo` when the helper needs metadata.

## Common V1-to-V3 Mapping

| Legacy V1 | V3 |
|---|---|
| `INPUT_TYPES` | `define_schema(... inputs=[...])` |
| `RETURN_TYPES`, `RETURN_NAMES` | `Schema.outputs` |
| `FUNCTION` | classmethod `execute` |
| `CATEGORY` | `Schema.category` |
| `OUTPUT_NODE` | `Schema.is_output_node` |
| `INPUT_IS_LIST` | `Schema.is_input_list` |
| `OUTPUT_IS_LIST` | per-output `is_output_list=True` |
| `VALIDATE_INPUTS` | `validate_inputs` |
| `IS_CHANGED` | `fingerprint_inputs` |
| `NODE_CLASS_MAPPINGS` | `ComfyExtension.get_node_list` plus `comfy_entrypoint` |

Do not retain both sides of this table in a normal V3 implementation.
