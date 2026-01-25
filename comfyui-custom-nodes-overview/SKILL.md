---
name: comfyui-custom-nodes-overview
description: High-level guide for ComfyUI custom node development covering architecture, project structure, node documentation, and workflow templates. Use this skill as an entry point when starting ComfyUI custom node development, understanding the client-server architecture, setting up project structure, adding node documentation/help pages, or creating workflow templates. For detailed backend (Python) implementation, use the comfyui-custom-nodes-backend skill. For detailed frontend (JavaScript) implementation, use the comfyui-custom-nodes-frontend skill.
---

# ComfyUI Custom Nodes Overview

This skill provides a high-level overview of ComfyUI custom node development. For detailed implementation guidance, refer to:
- **Backend (Python)**: Use the `comfyui-custom-nodes-backend` skill
- **Frontend (JavaScript)**: Use the `comfyui-custom-nodes-frontend` skill

## What Are Custom Nodes?

Custom nodes extend ComfyUI with new functionality. Each node takes inputs, processes them, and produces outputs. Custom nodes can range from simple operations (like inverting an image) to complex workflows.

## Architecture: Client-Server Model

ComfyUI uses a client-server architecture:
- **Server (Python)**: Handles data processing, models, image diffusion
- **Client (JavaScript)**: Handles the user interface

### Custom Node Categories

| Category | Description | API Compatible |
|----------|-------------|----------------|
| **Server-side only** | Python class defining inputs, outputs, processing function | ✅ Yes |
| **Client-side only** | UI modifications only (may not add actual nodes) | ✅ Yes |
| **Independent Client & Server** | Server features + related UI (new widgets, etc.) | ✅ Yes |
| **Connected Client & Server** | Direct client-server communication required | ❌ No |

Most custom nodes are server-side only.

## Project Structure

### Minimal Structure (Server-side Only)
```
my-custom-node/
├── __init__.py          # Module entry point
└── nodes.py             # Node definitions
```

### Full Structure (With Frontend & Documentation)
```
my-custom-node/
├── __init__.py              # Module entry point with NODE_CLASS_MAPPINGS
├── nodes.py                 # Python node definitions
├── js/                      # Frontend JavaScript (WEB_DIRECTORY)
│   └── my_extension.js      # Extension code
├── docs/                    # Node documentation (inside WEB_DIRECTORY)
│   ├── NodeName.md          # Default documentation
│   └── NodeName/            # Localized docs
│       ├── en.md
│       └── zh.md
├── locales/                 # i18n translations
│   ├── en/
│   │   ├── main.json
│   │   ├── nodeDefs.json
│   │   └── settings.json
│   └── zh/
│       └── ...
└── example_workflows/       # Workflow templates
    ├── example1.json
    ├── example1.jpg         # Thumbnail (optional)
    └── example2.json
```

## __init__.py Template

```python
from .nodes import MyNode, AnotherNode

# Required: Maps unique names to node classes
NODE_CLASS_MAPPINGS = {
    "MyNode": MyNode,
    "AnotherNode": AnotherNode
}

# Optional: Display names for UI
NODE_DISPLAY_NAME_MAPPINGS = {
    "MyNode": "My Custom Node",
    "AnotherNode": "Another Custom Node"
}

# Optional: Path to JavaScript files for frontend extensions
WEB_DIRECTORY = "./js"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
```

## Basic Node Definition (Python)

```python
class MyNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "strength": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.1}),
            },
            "optional": {
                "mask": ("MASK",),
            }
        }
    
    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("output_image",)
    FUNCTION = "process"
    CATEGORY = "My Nodes"
    DESCRIPTION = "Description shown in node info"
    
    def process(self, image, strength, mask=None):
        # Process the image
        result = image * strength
        return (result,)
```

For complete backend documentation, use the **comfyui-custom-nodes-backend** skill.

## Basic Frontend Extension (JavaScript)

```javascript
import { app } from "../../scripts/app.js";

app.registerExtension({
    name: "my.extension.name",
    
    async setup() {
        // Called at end of startup
    },
    
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        // Modify node types
        if (nodeType.comfyClass === "MyNode") {
            // Add custom behavior
        }
    }
});
```

For complete frontend documentation, use the **comfyui-custom-nodes-frontend** skill.

## Node Documentation

Add rich markdown documentation for your nodes to help users understand how to use them.

### Setup
1. Create `docs` folder inside your `WEB_DIRECTORY`
2. Add markdown files named after nodes (keys in `NODE_CLASS_MAPPINGS`)

### File Structure
```
WEB_DIRECTORY/docs/
├── MyNode.md                # Default/fallback documentation
└── MyNode/                  # Localized versions
    ├── en.md                # English
    ├── zh.md                # Chinese
    ├── fr.md                # French
    └── ...
```

### Supported Markdown Features
- Standard markdown (headings, lists, code blocks)
- Images: `![alt text](image.png)`
- Videos: `<video controls loop muted><source src="demo.mp4" type="video/mp4"></video>`
- Allowed video attributes: `controls`, `autoplay`, `loop`, `muted`, `preload`, `poster`

### Example Documentation File
```markdown
# My Custom Node

This node processes images using advanced algorithms.

## Parameters

- **image**: Input image to process
- **strength**: Processing strength (0.0 - 1.0)

## Usage

![example usage](example.png)

<video controls loop muted>
  <source src="demo.mp4" type="video/mp4">
</video>
```

### Alternative: Tooltips Only
If you add tooltips in your Python node definition, users can access basic info without separate documentation:

```python
"strength": ("FLOAT", {
    "default": 1.0,
    "tooltip": "Processing strength from 0.0 to 1.0"
})
```

## Workflow Templates

Provide example workflows to help users get started with your nodes.

### Setup
1. Create `example_workflows` folder in your custom node root
2. Add `.json` workflow files
3. Optionally add `.jpg` thumbnails with matching names

### Accepted Folder Names
- `example_workflows` (recommended)
- `workflow`, `workflows`
- `example`, `examples`

### Example Structure
```
my-custom-node/
└── example_workflows/
    ├── basic_usage.json
    ├── basic_usage.jpg      # Thumbnail (optional)
    ├── advanced_example.json
    └── advanced_example.jpg
```

Templates appear in ComfyUI under `Workflow → Browse Templates` menu, categorized by your module name.

## Template Repositories

- [cookiecutter-comfy-extension](https://github.com/Comfy-Org/cookiecutter-comfy-extension) - Cookiecutter template
- [ComfyUI-React-Extension-Template](https://github.com/Comfy-Org/ComfyUI-React-Extension-Template) - React-based template
- [ComfyUI_frontend_vue_basic](https://github.com/jtydhr88/ComfyUI_frontend_vue_basic) - Vue-based template

## Quick Start Checklist

1. ☐ Create project directory in `custom_nodes/`
2. ☐ Create `__init__.py` with `NODE_CLASS_MAPPINGS`
3. ☐ Define Python node class(es) with `INPUT_TYPES`, `RETURN_TYPES`, `FUNCTION`
4. ☐ (Optional) Add `WEB_DIRECTORY` for JavaScript extensions
5. ☐ (Optional) Add `docs/` folder with markdown documentation
6. ☐ (Optional) Add `locales/` folder for i18n support
7. ☐ (Optional) Add `example_workflows/` with template workflows
8. ☐ Restart ComfyUI to load your custom node

## Related Skills

- **comfyui-custom-nodes-backend**: Complete Python/backend documentation including datatypes, tensors, lazy evaluation, node expansion, data lists
- **comfyui-custom-nodes-frontend**: Complete JavaScript/frontend documentation including hooks, settings, dialogs, toasts, panels, menus, commands, i18n
