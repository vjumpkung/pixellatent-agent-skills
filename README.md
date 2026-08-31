# PixelLatent Agent Skills 

แหล่งรวม Agents SKILLS ที่ทำเล่น ๆ 

## Skills List

- comfyui-custom-nodes-backend - สำหรับการสร้าง backend custom nodes บน ComfyUI ด้วย V3 schema
- comfyui-custom-nodes-frontend - สำหรับการปรับแต่งหน้าเว็บของ ComfyUI
- (EXPERIMENTAL) comfyui-migrate-to-v3 - สำหรับการ Migrate Format การเขียน Custom Nodes บน ComfyUI แบบ Version 3 
- comfyui-publish-node - สำหรับการ Publish Custom Nodes ขึ้น Comfy Registry ด้วย `uvx comfy-cli node publish` โดยอ่าน token จาก environment หรือ `.env` และปฏิเสธการ publish ถ้าไม่ได้ตั้ง token ไว้
- pageindex - agent skills version สำหรับ pageindex
- pageindex-search - agent skills สำหรับการค้นหาไฟล์แบบ pageindex (ใช้คู่กันกับ pageindex)
- axios-security-check - ช่วยตรวจสอบ version ของ axios ที่พึ่งเกิน Supply Chain Attack (ไม่แนะนำให้ bypass permission)

## วิธีการติดตั้ง 

comfyui-custom-nodes-backend

```bash
npx skills add https://github.com/vjumpkung/pixellatent-agent-skills/tree/main/skills/comfyui-custom-nodes-backend
```

comfyui-custom-nodes-frontend

```bash
npx skills add https://github.com/vjumpkung/pixellatent-agent-skills/tree/main/skills/comfyui-custom-nodes-frontend
```

comfyui-migrate-to-v3

```bash
npx skills add https://github.com/vjumpkung/pixellatent-agent-skills/tree/main/skills/comfyui-migrate-to-v3
```

comfyui-publish-node

```bash
npx skills add https://github.com/vjumpkung/pixellatent-agent-skills/tree/main/skills/comfyui-publish-node
```

pageindex

```bash
npx skills add https://github.com/vjumpkung/pixellatent-agent-skills/tree/main/skills/pageindex
```

pageindex-search

```bash
npx skills add https://github.com/vjumpkung/pixellatent-agent-skills/tree/main/skills/pageindex-search
```

axios-security-check

```bash
npx skills add https://github.com/vjumpkung/pixellatent-agent-skills/tree/main/skills/axios-security-check
```
