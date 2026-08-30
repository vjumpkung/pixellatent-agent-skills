---
name: comfyui-custom-nodes-backend
description: Create, modify, or debug Python backend custom nodes for ComfyUI using the modern V3 schema (`comfy_api`, `io.ComfyNode`, `define_schema`, `io.NodeOutput`, `ComfyExtension`, and `comfy_entrypoint`). Use for new backend node packs and V3 implementations; use legacy V1 syntax only when the user explicitly requires compatibility with an older ComfyUI. Do not use for frontend-only JavaScript extensions.
---

# ComfyUI V3 Backend Custom Nodes

Build backend nodes against the target ComfyUI installation, using the V3 schema by default. Keep node contracts stable, implementation stateless, and generated code consistent with the installed version of `comfy_api`.

## Ground Rules

- For new nodes, use `io.ComfyNode`, `define_schema`, classmethod `execute`, `io.NodeOutput`, `ComfyExtension`, and `comfy_entrypoint`.
- Do not mix V1 registration (`INPUT_TYPES`, `RETURN_TYPES`, `FUNCTION`, `NODE_CLASS_MAPPINGS`) into a V3 pack unless the user explicitly requests a compatibility layer.
- Treat `comfy_api.latest` as a moving development API. Inspect the target installation before relying on a class, field, or helper; pin a numbered API only when the pack's support policy calls for it.
- Use the target installation's exported `comfy_api.<version>.io` and `ui` modules as the final authority. The general backend documentation still contains V1 examples, and even the V3 guide can lag or contain naming mistakes.
- V3 node methods are classmethods. Do not put execution state in `__init__` or expect instance fields to persist.
- Preserve the user's requested behavior and existing pack layout. Do not add frontend code, packaging infrastructure, routes, or dependencies unless the node needs them.

## Workflow

1. Inspect the node pack and target environment.
   - Find existing package entrypoints, node IDs, dependency declarations, tests, and supported ComfyUI versions.
   - If ComfyUI is available locally, inspect `comfy_api/latest/_io_public.py`, `_io.py`, `_ui_public.py`, and the selected numbered API. A re-exported symbol must exist in the public module, not merely an internal file.
   - If the target version is unknown, write against `comfy_api.latest` but call out that assumption.

2. Define the node contract before implementation.
   - Choose a globally unique, prefixed `node_id`; changing it later breaks workflows unless a replacement is registered.
   - Specify input IDs, optionality, defaults, bounds, socket/widget behavior, output order, list behavior, cache semantics, and whether the node is an output node.
   - Make each input ID match the corresponding `execute` keyword exactly. Give optional arguments Python defaults such as `mask=None`.

3. Implement the V3 node and extension.
   - Read [references/v3-node-api.md](references/v3-node-api.md) for the core schema, types, registration, hidden values, and UI return patterns.
   - For images, masks, latents, audio, batching, device placement, or PIL conversion, also read [references/data-and-tensors.md](references/data-and-tensors.md).
   - For lazy inputs, caching, list processing, expansion, blocking, progress, dynamic inputs, or node replacement, also read [references/advanced-execution.md](references/advanced-execution.md).

4. Verify observable behavior.
   - Compile/import the Python package in an environment containing the target ComfyUI when available.
   - Finalize or inspect every schema and confirm unique node IDs, public type names, input/signature alignment, output count/order, and async extension registration.
   - Exercise meaningful edge cases: optional inputs absent, batch sizes greater than one, 2D/3D masks, non-default device/dtype, empty lists, and external-state cache changes as applicable.
   - Start ComfyUI and load a minimal workflow when the installation is available; report when only static validation was possible.

## Required V3 Invariants

- `define_schema` and `execute` are classmethods on an `io.ComfyNode` subclass.
- `execute` returns `io.NodeOutput`; positional values follow `Schema.outputs` order.
- `get_node_list` is async and returns node classes. `comfy_entrypoint` returns the extension instance and may be sync or async.
- Input IDs are stable Python-compatible names and match execution parameters.
- Optional inputs are safe when omitted; output list declarations match actual returned container semantics.
- Tensor code preserves batch dimensions, dtype, device, and latent metadata unless conversion is intentional.
- Caching reflects all non-input state. Never return a constant from `fingerprint_inputs` to mean "always rerun."
- Advanced features are enabled in the schema when required, such as `enable_expand=True` for node expansion.

## Source Precedence

When sources disagree, use this order:

1. The target ComfyUI installation and pinned API implementation.
2. The matching official ComfyUI source for that version.
3. The official [V3 migration guide](https://docs.comfy.org/custom-nodes/v3_migration).
4. The legacy backend pages for execution and tensor concepts that V3 still adapts.

The current source defines model wrappers as `io.Vae` and `io.Clip`; do not copy `io.VAE` or `io.CLIP` from a documentation table without verifying the target API.
