# PixelLatent Agent Skills 

- รวม Agent Skills สำหรับ การใช้งาน Agentic Coding ต่าง ๆ โดยปัจจุบันมี Skill สำหรับการเขียน ComfyUI Custom Nodes 

**Generated With Claude Code**

# ComfyUI Custom Nodes Development Skills

คู่มือครบครันสำหรับการพัฒนา Custom Nodes ใน ComfyUI แบ่งเป็น 3 ส่วนหลัก

## 📚 Skills ที่มีให้

### 1. **comfyui-custom-nodes-overview** - ภาพรวมและโครงสร้าง

**ใช้เมื่อไหร่**: เริ่มต้นพัฒนา custom node หรือต้องการเข้าใจภาพรวม

**เนื้อหาหลัก**:
- สถาปัตยกรรมแบบ Client-Server ของ ComfyUI
- โครงสร้างโปรเจกต์และไฟล์ต่างๆ
- วิธีสร้าง `__init__.py` และ `NODE_CLASS_MAPPINGS`
- การเพิ่มเอกสารประกอบ node (markdown docs)
- การสร้าง workflow templates ตัวอย่าง
- i18n (การแปลภาษา)

**ประเภทของ Custom Nodes**:
- **Server-side only**: เขียน Python อย่างเดียว (ส่วนใหญ่เป็นแบบนี้)
- **Client-side only**: เขียน JavaScript ปรับ UI อย่างเดียว
- **Independent Client & Server**: มีทั้ง Python และ JavaScript แยกกันทำงาน
- **Connected Client & Server**: สื่อสารกันโดยตรง (ไม่ compatible กับ API)

**โครงสร้างโปรเจกต์แบบเต็ม**:
```
my-custom-node/
├── __init__.py              # จุดเริ่มต้น + NODE_CLASS_MAPPINGS
├── nodes.py                 # คลาส node ที่เขียนด้วย Python
├── js/                      # โค้ด JavaScript (WEB_DIRECTORY)
│   └── my_extension.js
├── docs/                    # เอกสารประกอบ node
│   ├── NodeName.md
│   └── NodeName/            # เอกสารแยกตามภาษา
│       ├── en.md
│       └── zh.md
├── locales/                 # การแปลภาษา
│   ├── en/
│   └── zh/
└── example_workflows/       # workflow ตัวอย่าง
    ├── example1.json
    └── example1.jpg
```

---

### 2. **comfyui-custom-nodes-backend** - การพัฒนา Backend (Python)

**ใช้เมื่อไหร่**: เขียนโค้ด Python เพื่อสร้าง/แก้ไข node, ทำงานกับ datatype, tensor, ภาพ

**เนื้อหาหลัก**:

#### โครงสร้าง Node พื้นฐาน
```python
class MyCustomNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {"image_in": ("IMAGE", {})},
            "optional": {...},
            "hidden": {...}
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image_out",)
    CATEGORY = "examples"
    FUNCTION = "process"
    OUTPUT_NODE = False

    def process(self, image_in):
        result = 1 - image_in  # กลับสี
        return (result,)
```

#### Properties สำคัญ
- **INPUT_TYPES**: กำหนด input ที่ node รับ (required/optional/hidden)
- **RETURN_TYPES**: กำหนดประเภทของ output (ต้องเป็น tuple)
- **FUNCTION**: ชื่อ method ที่จะถูกเรียก
- **CATEGORY**: กลุ่มใน menu
- **IS_CHANGED**: ควบคุมการ cache (return `float("NaN")` เพื่อรันทุกครั้ง)

#### Datatypes หลัก

**Python Types**:
- `INT`: ตัวเลขจำนวนเต็ม (ต้องมี default, min, max)
- `FLOAT`: ทศนิยม (default, min, max, step)
- `STRING`: ข้อความ (default, multiline, placeholder)
- `BOOLEAN`: true/false (default, label_on, label_off)
- `COMBO`: dropdown (ใช้ list แทน string)

**Tensor Types**:
- `IMAGE`: รูปภาพ shape `[B,H,W,C]` C=3 (RGB)
- `LATENT`: dict มี key `samples` shape `[B,C,H,W]` C=4
- `MASK`: หน้ากาก shape `[H,W]` หรือ `[B,H,W]`
- `AUDIO`: dict มี `waveform` และ `sample_rate`

**Model Types**: `MODEL`, `CLIP`, `VAE`, `CONDITIONING`

#### การทำงานกับรูปภาพ
```python
# โหลดรูปเป็น tensor
from PIL import Image
import numpy as np
import torch

image = Image.open(path).convert("RGB")
image = np.array(image).astype(np.float32) / 255.0
image = torch.from_numpy(image)[None,]  # เพิ่ม batch dimension

# บันทึกรูป
i = 255. * image.cpu().numpy()
img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))
img.save(filepath)
```

#### ฟีเจอร์ขั้นสูง
- **Lazy Evaluation**: เลื่อนการคำนวณ input จนกว่าจะต้องใช้จริงๆ
- **Node Expansion**: return subgraph แทนผลลัพธ์
- **Data Lists**: รับ/ส่งข้อมูลเป็น list (INPUT_IS_LIST, OUTPUT_IS_LIST)
- **VALIDATE_INPUTS**: validate ค่า input ก่อนรัน
- **Hidden Inputs**: `UNIQUE_ID`, `PROMPT`, `EXTRA_PNGINFO`, `DYNPROMPT`

#### Tips สำคัญ
- Return ต้องเป็น tuple เสมอ: `return (result,)` ไม่ใช่ `return (result)`
- ใช้ `forceInput` เพื่อบังคับให้เป็น input socket
- ใช้ `defaultInput` เพื่อให้มีทั้ง socket และ widget
- Latent เข้าถึงผ่าน `latent["samples"]`
- ตรวจสอบ mask dimension: `len(mask.shape)` อาจเป็น 2 หรือ 3

---

### 3. **comfyui-custom-nodes-frontend** - การพัฒนา Frontend (JavaScript)

**ใช้เมื่อไหร่**: สร้าง UI, เพิ่ม settings, dialogs, menus, keybindings, แก้ไขพฤติกรรม node

**เนื้อหาหลัก**:

#### โครงสร้าง Extension พื้นฐาน
```javascript
import { app } from "../../scripts/app.js";

app.registerExtension({
    name: "unique.extension.name",

    async init() {
        // เรียกก่อน register nodes
    },

    async setup() {
        // เรียกตอนจบ startup
    },

    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        // เรียกสำหรับแต่ละ node type
        if (nodeType.comfyClass === "MyNodeClass") {
            // แก้ไขพฤติกรรม node
        }
    },

    async nodeCreated(node) {
        // เรียกเมื่อสร้าง node instance
    }
});
```

#### Hooks ลำดับการเรียก
**ตอนโหลดหน้า**:
```
init → addCustomNodeDefs → getCustomWidgets → beforeRegisterNodeDef
→ registerCustomNodes → beforeConfigureGraph → nodeCreated
→ loadedGraphNode → afterConfigureGraph → setup
```

#### Settings API
```javascript
settings: [
    {
        id: "example.boolean",
        name: "Example Setting",
        type: "boolean",  // boolean, text, number, slider, combo, color, image
        defaultValue: false,
        category: ["Category", "Section", "Label"],
        tooltip: "Help text",
        onChange: (newVal, oldVal) => {
            console.log(`เปลี่ยนจาก ${oldVal} เป็น ${newVal}`);
        }
    }
]

// อ่าน/เขียน setting
const value = app.extensionManager.setting.get('example.boolean');
await app.extensionManager.setting.set('example.boolean', true);
```

#### Dialog และ Toast
```javascript
// Prompt dialog
const result = await app.extensionManager.dialog.prompt({
    title: "Input",
    message: "ใส่ค่า:",
    defaultValue: "default"
});

// Confirm dialog
const confirmed = await app.extensionManager.dialog.confirm({
    title: "Confirm",
    message: "แน่ใจหรือไม่?",
    type: "default"  // default, overwrite, delete, dirtyClose
});

// Toast notification
app.extensionManager.toast.add({
    severity: "info",  // success, info, warn, error
    summary: "Title",
    detail: "Message",
    life: 3000
});
```

#### UI Extensions

**Sidebar Tab**:
```javascript
app.extensionManager.registerSidebarTab({
    id: "mySidebar",
    icon: "pi pi-compass",
    title: "My Sidebar",
    tooltip: "คำอธิบาย",
    type: "custom",
    render: (el) => {
        el.innerHTML = '<div>เนื้อหา sidebar</div>';
        return () => { /* cleanup */ };
    }
});
```

**Bottom Panel Tab**:
```javascript
bottomPanelTabs: [
    {
        id: "myTab",
        title: "My Tab",
        type: "custom",
        render: (el) => {
            el.innerHTML = '<div>เนื้อหา tab</div>';
        }
    }
]
```

#### Commands และ Keybindings
```javascript
commands: [
    {
        id: "myCommand",
        label: "My Command",
        icon: "pi pi-play",
        function: () => { app.queuePrompt(); }
    }
],
keybindings: [
    {
        combo: { key: "r", ctrl: true, shift: false, alt: false },
        commandId: "myCommand"
    }
]
```

#### Context Menus
```javascript
// Canvas menu
getCanvasMenuItems(canvas) {
    return [
        null,  // เส้นแบ่ง
        {
            content: "My Action",
            callback: () => { console.log("Clicked!"); }
        },
        {
            content: "Submenu",
            submenu: {
                options: [
                    { content: "Option 1", callback: () => {} }
                ]
            }
        }
    ];
}

// Node menu
getNodeMenuItems(node) {
    if (node.comfyClass === "KSampler") {
        return [{
            content: "สุ่ม Seed ใหม่",
            callback: () => {
                const widget = node.widgets.find(w => w.name === "seed");
                widget.value = Math.floor(Math.random() * 1000000);
            }
        }];
    }
}
```

#### Objects สำคัญ

**ComfyApp (app)**:
- `app.canvas`: LGraphCanvas - UI ปัจจุบัน
- `app.graph`: LGraph - graph state
- `app.ui`: UI elements
- `app.graphToPrompt()`: แปลง graph เป็น prompt
- `app.queuePrompt()`: ส่ง prompt ไป queue

**ComfyNode (node)**:
- `node.id`: ID ของ node
- `node.comfyClass`: ชื่อคลาส Python
- `node.widgets`: list ของ widgets
- `node.widgets_values`: ค่าของ widgets
- `node.mode`: 0=normal, 2=muted, 4=bypassed

#### i18n (การแปลภาษา)
```
locales/
├── en/
│   ├── main.json        # การแปลทั่วไป
│   ├── nodeDefs.json    # คำแปล node
│   └── settings.json    # คำแปล settings
└── zh/
    └── ...
```

**ภาษาที่รองรับ**: en, zh, zh-TW, fr, ko, ru, es, ja, ar

#### API Events
```javascript
import { api } from "../../scripts/api.js";

api.addEventListener("execution_start", () => {
    console.log("Workflow เริ่มทำงาน");
});

api.addEventListener("executed", (event) => {
    console.log("เสร็จแล้ว", event.detail);
});
```

---

## 🚀 Quick Start

1. สร้างโฟลเดอร์ใน `custom_nodes/`
2. สร้าง `__init__.py` พร้อม `NODE_CLASS_MAPPINGS`
3. สร้างคลาส Python ด้วย `INPUT_TYPES`, `RETURN_TYPES`, `FUNCTION`
4. (ถ้าต้องการ) เพิ่ม `WEB_DIRECTORY` สำหรับ JavaScript
5. (ถ้าต้องการ) เพิ่ม `docs/` สำหรับเอกสาร
6. (ถ้าต้องการ) เพิ่ม `example_workflows/` สำหรับ workflow ตัวอย่าง
7. Restart ComfyUI

---

## 📖 เอกสารเพิ่มเติม

แต่ละ skill มีเอกสารแบบละเอียดใน:
- `comfyui-custom-nodes-overview/SKILL.md`
- `comfyui-custom-nodes-backend/SKILL.md`
- `comfyui-custom-nodes-frontend/SKILL.md`

## 🔗 Template Repositories
- [cookiecutter-comfy-extension](https://github.com/Comfy-Org/cookiecutter-comfy-extension)
- [ComfyUI-React-Extension-Template](https://github.com/Comfy-Org/ComfyUI-React-Extension-Template)
- [ComfyUI_frontend_vue_basic](https://github.com/jtydhr88/ComfyUI_frontend_vue_basic)
