# Advanced V3 Execution

Read only the sections needed by the node. Verify constructor and method signatures in the target `comfy_api` because V3 advanced features are evolving.

## Input Validation

Use a classmethod returning `True` or a user-facing error string:

```python
@classmethod
def validate_inputs(cls, width: int, height: int, **kwargs) -> bool | str:
    if width * height > 16_777_216:
        return "The requested image exceeds 16 megapixels."
    return True
```

Schema bounds handle ordinary widget validation. Use `validate_inputs` for relationships, file checks, or constraints that the schema cannot express.

## Cache Fingerprints

Normal caching already accounts for declared inputs. Implement `fingerprint_inputs` when results also depend on external state such as file contents:

```python
import hashlib
from pathlib import Path


@classmethod
def fingerprint_inputs(cls, path: str, **kwargs) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
```

Equal fingerprints permit reuse; changed fingerprints force recomputation. A constant `True` therefore tends to cache forever, not rerun every time. Use `Schema.not_idempotent` only for truly non-idempotent semantics supported by the target version.

## Lazy Evaluation

Mark deferrable inputs with `lazy=True`. ComfyUI initially passes `None`; return the IDs that are actually needed:

```python
@classmethod
def check_lazy_status(cls, condition: bool, on_true, on_false):
    needed = []
    if condition and on_true is None:
        needed.append("on_true")
    if not condition and on_false is None:
        needed.append("on_false")
    return needed
```

The input IDs returned here must exactly match schema IDs. `execute` must handle only the branch selected by the condition and not touch the unevaluated `None` value.

## List Processing

Set `is_input_list=True` in `io.Schema` when the node needs whole ComfyUI data lists. Every argument, including widget values, then arrives as a list. Set `is_output_list=True` on each output that returns a data list. Do not use these flags for tensor batches.

Define behavior for empty lists, unequal lengths, and scalar-like one-element lists rather than relying on accidental indexing.

## Node Expansion

Expansion returns a generated subgraph. Enable it explicitly:

```python
from comfy_execution.graph_utils import GraphBuilder


@classmethod
def define_schema(cls) -> io.Schema:
    return io.Schema(
        node_id="PixelLatent_ExpandExample",
        inputs=[io.Float.Input("value", default=1.0)],
        outputs=[io.Float.Output("value")],
        enable_expand=True,
    )

@classmethod
def execute(cls, value: float) -> io.NodeOutput:
    graph = GraphBuilder()
    node = graph.node("PrimitiveFloat", value=value)
    return io.NodeOutput(node.out(0), expand=graph.finalize())
```

Use actual built-in node IDs and input names from the target installation; the placeholder ID above illustrates the V3 return shape, not a guaranteed built-in contract. If expansion behavior depends on the mutable graph, request `io.Hidden.dynprompt`.

## Blocking Execution

V3 `NodeOutput` can block downstream execution with an optional message:

```python
if model is None:
    return io.NodeOutput(block_execution="A model is required for this branch.")
```

Use blocking for an intentional control-flow result, not as a substitute for validation errors or exception handling.

## Async Execution and Progress

Use async execution for actual awaitable I/O or runtime APIs:

```python
from comfy_api.latest import ComfyAPI, io


api = ComfyAPI()

@classmethod
async def execute(cls, images) -> io.NodeOutput:
    total = len(images)
    for index, image in enumerate(images):
        await api.execution.set_progress(
            value=index + 1,
            max_value=total,
            preview_image=image,
        )
    return io.NodeOutput(images)
```

Do not make CPU-bound tensor work async merely to change syntax. Use ComfyUI's execution API instead of global progress hooks.

## Dynamic Inputs

- `io.MatchType` links generic input and output types through a shared template.
- `io.MultiType` permits one input to accept a controlled set of wire types.
- `io.Autogrow` exposes a bounded variable number of inputs and passes a dictionary keyed by generated names.
- `io.DynamicCombo` exposes option-dependent nested inputs and passes a nested dictionary.

Keep dynamic paths stable because they are serialized in workflows. Bound autogrow input counts and validate nested values. Prefer ordinary fixed schemas when the interface does not require dynamism.

## Extension Lifecycle and Replacement

Use `ComfyExtension.on_load` for one-time registration, including `ComfyAPI().node_replacement.register(...)`. Use `io.NodeReplace` when changing a node ID or serialized interface so old workflows can map input IDs, widget positions, and output indexes.

Workflow JSON stores widget values positionally. Supply `old_widget_ids` in the old serialized order, not the new schema order. Test replacement using a saved workflow from before the change.

Do not rename a released `node_id` casually. Display-name changes do not require replacement registration.
