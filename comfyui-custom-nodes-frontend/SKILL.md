---
name: comfyui-custom-nodes-frontend
description: Comprehensive guide for developing ComfyUI custom nodes frontend/UI in JavaScript. Use this skill when creating JavaScript extensions for ComfyUI, adding UI elements (settings, dialogs, toasts, sidebar tabs, bottom panels, menus), implementing extension hooks, working with ComfyApp/LiteGraph objects, adding commands/keybindings, creating context menus, or implementing i18n localization for custom nodes.
---

# ComfyUI Custom Nodes Frontend Development

This skill provides complete guidance for developing ComfyUI custom node frontends in JavaScript.

## Extension Basics

### Setup Structure
```javascript
// In __init__.py
WEB_DIRECTORY = "./js"
__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
```

### Basic Extension Registration
```javascript
import { app } from "../../scripts/app.js";

app.registerExtension({
  name: "unique.extension.name",
  async setup() {
    // Called at end of startup
  },
  async init() {
    // Called before nodes are registered
  },
  async beforeRegisterNodeDef(nodeType, nodeData, app) {
    // Called for each node type
  },
  async nodeCreated(node) {
    // Called when node instance is created
  }
});
```

## Extension Hooks

### Key Hooks
| Hook | When Called | Use Case |
|------|-------------|----------|
| `init()` | After graph created, before nodes registered | Hijack core behavior |
| `setup()` | End of startup | Add event listeners, menus |
| `beforeRegisterNodeDef(nodeType, nodeData, app)` | For each node type | Modify node prototypes |
| `nodeCreated(node)` | When node instance created | Modify specific instances |
| `beforeConfigureGraph` | Before workflow loads | Pre-load setup |
| `afterConfigureGraph` | After workflow loads | Post-load actions |

### Hook Call Sequence
**Page Load:**
```
init → addCustomNodeDefs → getCustomWidgets → beforeRegisterNodeDef (×N) 
→ registerCustomNodes → beforeConfigureGraph → nodeCreated → loadedGraphNode 
→ afterConfigureGraph → setup
```

**Loading Workflow:**
```
beforeConfigureGraph → beforeRegisterNodeDef (0-N) → nodeCreated (×N) 
→ loadedGraphNode (×N) → afterConfigureGraph
```

### beforeRegisterNodeDef Pattern
```javascript
async beforeRegisterNodeDef(nodeType, nodeData, app) {
  if (nodeType.comfyClass === "MyNodeClass") {
    // Hijack existing method
    const original = nodeType.prototype.onConnectionsChange;
    nodeType.prototype.onConnectionsChange = function(side, slot, connect, link_info, output) {
      const r = original?.apply(this, arguments);
      console.log("Connection changed!");
      return r;
    }
  }
}
```

## ComfyApp Object

### Key Properties
| Property | Description |
|----------|-------------|
| `app.canvas` | LGraphCanvas - current UI |
| `app.canvasEl` | DOM canvas element |
| `app.graph` | LGraph - current graph state |
| `app.runningNodeId` | Currently executing node ID |
| `app.ui` | UI elements (queue, menu, dialogs) |

### Key Functions
| Function | Description |
|----------|-------------|
| `app.graphToPrompt()` | Convert graph to prompt |
| `app.loadGraphData(data)` | Load a graph |
| `app.queuePrompt()` | Submit prompt to queue |
| `app.registerExtension(ext)` | Register extension |

## ComfyNode Object

### Properties
| Property | Description |
|----------|-------------|
| `node.id` | Unique node ID |
| `node.comfyClass` | Python class name |
| `node.type` | Node type name |
| `node.inputs` | List of inputs |
| `node.widgets` | List of widgets |
| `node.widgets_values` | Current widget values |
| `node.pos` | [x, y] position |
| `node.size` | [width, height] |
| `node.mode` | 0=normal, 2=muted, 4=bypassed |
| `node.flags.collapsed` | Collapsed state |

### Key Functions
| Function | Description |
|----------|-------------|
| `addInput(name, type)` | Create input |
| `addWidget(type, name, value, callback, options)` | Add widget |
| `connect(output_slot, target_node, target_slot)` | Connect nodes |
| `disconnectInput(slot)` | Remove input link |
| `getInputNode(slot)` | Get connected input node |
| `setDirtyCanvas(fg, bg)` | Request redraw |

## Settings API

### Register Settings
```javascript
app.registerExtension({
  name: "MyExtension",
  settings: [
    {
      id: "example.boolean",
      name: "Example Setting",
      type: "boolean",  // boolean, text, number, slider, combo, color, image, hidden
      defaultValue: false,
      category: ["Category", "Section", "Label"],
      tooltip: "Help text",
      onChange: (newVal, oldVal) => {
        console.log(`Changed: ${oldVal} → ${newVal}`);
      }
    }
  ]
});
```

### Setting Types
| Type | Options |
|------|---------|
| `boolean` | Toggle switch |
| `text` | Free text input |
| `number` | Number input (use `attrs: {showButtons: true, maxFractionDigits: 2}`) |
| `slider` | Slider with `attrs: {min, max, step}` |
| `combo` | Dropdown with `options: [{text, value}]` or `options: ["a", "b"]` |
| `color` | Color picker (hex format, 6 digits) |
| `image` | Image upload (saved as data URL) |
| `hidden` | Not displayed, but readable/writable |

### Read/Write Settings
```javascript
// Read
const value = app.extensionManager.setting.get('example.boolean');

// Write
await app.extensionManager.setting.set('example.boolean', true);
```

## Dialog API

```javascript
// Prompt dialog
const result = await app.extensionManager.dialog.prompt({
  title: "Input",
  message: "Enter value:",
  defaultValue: "default"
});
// result: string | null

// Confirm dialog
const confirmed = await app.extensionManager.dialog.confirm({
  title: "Confirm",
  message: "Are you sure?",
  type: "default"  // default, overwrite, delete, dirtyClose, reinstall
});
// confirmed: boolean | null
```

## Toast API

```javascript
// Show toast
app.extensionManager.toast.add({
  severity: "info",  // success, info, warn, error, secondary, contrast
  summary: "Title",
  detail: "Message content",
  life: 3000,  // Auto-close ms
  closable: true
});

// Quick alert
app.extensionManager.toast.addAlert("Important message");

// Remove all
app.extensionManager.toast.removeAll();
```

## About Panel Badges

```javascript
app.registerExtension({
  name: "MyExtension",
  aboutPageBadges: [
    {
      label: "Documentation",
      url: "https://example.com/docs",
      icon: "pi pi-book"
    },
    {
      label: "GitHub",
      url: "https://github.com/user/repo",
      icon: "pi pi-github"
    }
  ]
});
```

## Bottom Panel Tabs

```javascript
app.registerExtension({
  name: "MyExtension",
  bottomPanelTabs: [
    {
      id: "myTab",
      title: "My Tab",
      type: "custom",
      render: (el) => {
        el.innerHTML = '<div>Tab content</div>';
        // Add event listeners here
      }
    }
  ]
});

// Standalone registration
app.extensionManager.registerBottomPanelTab({...});
```

## Sidebar Tabs

```javascript
app.extensionManager.registerSidebarTab({
  id: "mySidebar",
  icon: "pi pi-compass",  // PrimeVue icon
  title: "My Sidebar",
  tooltip: "Tooltip text",
  type: "custom",
  render: (el) => {
    el.innerHTML = '<div>Sidebar content</div>';
    
    // Return cleanup function (optional)
    return () => {
      // Remove event listeners
    };
  }
});
```

## Selection Toolbox

```javascript
app.registerExtension({
  name: "MyExtension",
  commands: [
    {
      id: "my-ext.action",
      label: "Do Action",
      icon: "pi pi-star",
      function: (selectedItem) => {
        const items = app.canvas.selectedItems;
        console.log(`${items.size} items selected`);
      }
    }
  ],
  getSelectionToolboxCommands: (selectedItem) => {
    const count = app.canvas.selectedItems?.size || 0;
    if (count > 0) {
      return ["my-ext.action"];
    }
    return [];
  }
});
```

## Commands and Keybindings

```javascript
app.registerExtension({
  name: "MyExtension",
  commands: [
    {
      id: "myCommand",
      label: "My Command",
      icon: "pi pi-play",
      function: () => {
        app.queuePrompt();
      }
    }
  ],
  keybindings: [
    {
      combo: { key: "r", ctrl: true, shift: false, alt: false },
      commandId: "myCommand"
    }
  ]
});
```

### Special Keys
- Arrow keys: `ArrowUp`, `ArrowDown`, `ArrowLeft`, `ArrowRight`
- Function keys: `F1` through `F12`
- Others: `Escape`, `Tab`, `Enter`, `Backspace`, `Delete`, `Home`, `End`, `PageUp`, `PageDown`

## Topbar Menu

```javascript
app.registerExtension({
  name: "MyExtension",
  commands: [
    { id: "cmd1", label: "Action 1", function: () => {} },
    { id: "cmd2", label: "Action 2", function: () => {} }
  ],
  menuCommands: [
    { path: ["Extensions", "My Tools"], commands: ["cmd1", "cmd2"] },
    { path: ["Extensions", "My Tools", "Advanced"], commands: ["cmd1"] }
  ]
});
```

## Context Menus (New API)

### Canvas Menu
```javascript
app.registerExtension({
  name: "MyExtension",
  getCanvasMenuItems(canvas) {
    return [
      null,  // Separator
      {
        content: "My Action",
        callback: () => { console.log("Clicked!"); }
      },
      {
        content: "Submenu",
        submenu: {
          options: [
            { content: "Option 1", callback: () => {} },
            { content: "Option 2", callback: () => {} }
          ]
        }
      }
    ];
  }
});
```

### Node Menu
```javascript
app.registerExtension({
  name: "MyExtension",
  getNodeMenuItems(node) {
    if (node.comfyClass === "KSampler") {
      return [{
        content: "Randomize Seed",
        callback: () => {
          const widget = node.widgets.find(w => w.name === "seed");
          if (widget) widget.value = Math.floor(Math.random() * 1000000);
        }
      }];
    }
    return [];
  }
});
```

## LiteGraph Objects

### LGraph (app.graph)
```javascript
// Get node by ID
const node = app.graph._nodes_by_id[nodeId];

// Get link info
const link = app.graph.links[linkId];
// link.origin_id, link.origin_slot, link.target_id, link.target_slot, link.type
```

### Widget Object
```javascript
widget.name      // Widget name
widget.type      // Widget type (lowercase)
widget.value     // Current value (getter/setter)
widget.options   // Options from Python (default, min, max)
widget.callback  // Called on value change
widget.last_y    // Vertical position
```

### Prompt Object
```javascript
const prompt = await app.graphToPrompt();
// prompt.output[nodeId].class_type - Python class name
// prompt.output[nodeId].inputs - Input values or links
// prompt.workflow.nodes - All nodes
// prompt.workflow.links - All links [link_id, origin_id, origin_slot, target_id, target_slot, type]
```

## API Events

```javascript
import { api } from "../../scripts/api.js";

// In setup()
api.addEventListener("execution_start", () => {
  console.log("Workflow started");
});

api.addEventListener("executed", (event) => {
  // event.detail contains execution info
});
```

## i18n Support

### Directory Structure
```
your_custom_node/
├── __init__.py
└── locales/
    ├── en/
    │   ├── main.json        # General translations
    │   ├── nodeDefs.json    # Node definitions
    │   └── settings.json    # Settings translations
    └── zh/
        ├── main.json
        ├── nodeDefs.json
        └── settings.json
```

### nodeDefs.json Format
```json
{
  "MyNodeClass": {
    "display_name": "My Node",
    "description": "Node description",
    "inputs": {
      "input_name": {
        "name": "Display Name",
        "tooltip": "Help text",
        "options": {
          "option1": "Option 1 Label"
        }
      }
    },
    "outputs": {
      "0": {
        "name": "Output Name",
        "tooltip": "Output help"
      }
    }
  }
}
```

### settings.json Format
```json
{
  "MyExt_SettingName": {
    "name": "Setting Display Name",
    "tooltip": "Setting description",
    "options": {
      "value1": "Label 1"
    }
  }
}
```

### main.json Format
```json
{
  "settingsCategories": {
    "MyExtension": "My Extension",
    "SectionName": "Section Display Name"
  }
}
```

### Supported Languages
en, zh (Simplified), zh-TW (Traditional), fr, ko, ru, es, ja, ar

## Common Patterns

### Detect Workflow Events
```javascript
import { api } from "../../scripts/api.js";

async setup() {
  api.addEventListener("execution_start", () => {});
  api.addEventListener("executed", (e) => {});
  api.addEventListener("execution_interrupted", () => {});
}
```

### Access Selected Nodes
```javascript
const selected = app.canvas.selectedItems;  // Set of selected items
const selectedNodes = app.canvas.selected_nodes;  // Object of selected nodes (legacy)
```

### Redraw Canvas
```javascript
app.graph.setDirtyCanvas(true, true);  // foreground, background
```

### Using React in Panels
```javascript
import React from "react";
import ReactDOM from "react-dom/client";

render: (el) => {
  const container = document.createElement("div");
  el.appendChild(container);
  
  ReactDOM.createRoot(container).render(
    <React.StrictMode>
      <MyComponent />
    </React.StrictMode>
  );
}
```

## Icon Libraries

PrimeVue icons: `pi pi-[name]` (pi-home, pi-github, pi-star, pi-book, pi-copy, etc.)
See: https://primevue.org/icons/
