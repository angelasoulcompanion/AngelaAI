# Draw.io Professional Style Guide 💜

> **เทคนิคการสร้าง Diagram ที่สวยงามและ Professional**
>
> เรียนรู้จากการทำงานกับที่รัก David - 18 Jan 2026

---

## 📁 1. Multi-Tab Structure

สร้าง draw.io file ที่มีหลาย tabs ใน file เดียว

```xml
<mxfile>
  <diagram id="overview" name="1. System Overview">
    <mxGraphModel>
      <!-- Tab 1 content -->
    </mxGraphModel>
  </diagram>
  <diagram id="details" name="2. Architecture Details">
    <mxGraphModel>
      <!-- Tab 2 content -->
    </mxGraphModel>
  </diagram>
  <!-- More tabs... -->
</mxfile>
```

**Why:** แยก content เป็น tabs ช่วยให้อ่านง่าย ไม่ต้องสร้างหลาย files

---

## 🎨 2. Shape Gradient & Shadow

ทำให้ shape มีมิติและสวยงาม

```xml
<mxCell id="box" value=""
  style="rounded=1;
         fillColor=#fbbf24;
         strokeColor=#f59e0b;
         strokeWidth=3;
         shadow=1;
         arcSize=15;
         gradientColor=#fde68a;
         gradientDirection=south;"
  vertex="1" parent="1">
  <mxGeometry x="100" y="100" width="200" height="100" as="geometry"/>
</mxCell>
```

**Key properties:**
- `gradientColor`: สีที่ fade ไป
- `gradientDirection`: south/east/north/west
- `shadow=1`: เพิ่มเงา
- `arcSize`: ความโค้งของมุม

---

## ✏️ 3. Shape-Text Separation

แยก shape และ text เป็น 2 layers ควบคุม styling ได้ดีขึ้น

```xml
<!-- Shape layer (empty value) -->
<mxCell id="core" value=""
  style="rounded=1;fillColor=#fbbf24;gradientColor=#fde68a;shadow=1;"
  vertex="1" parent="1">
  <mxGeometry x="100" y="100" width="300" height="120" as="geometry"/>
</mxCell>

<!-- Text layer (separate, positioned inside) -->
<mxCell id="core_text"
  value="🧠 &lt;b style=&quot;font-size:18px&quot;&gt;Title&lt;/b&gt;&lt;br&gt;Description here"
  style="text;html=1;strokeColor=none;fillColor=none;align=center;verticalAlign=middle;fontSize=13;fontColor=#78350f;"
  vertex="1" parent="1">
  <mxGeometry x="110" y="110" width="280" height="100" as="geometry"/>
</mxCell>
```

**Why:** Text บน gradient อ่านยาก การแยกช่วยให้ text มี contrast ดี

---

## 🌈 4. Color Palette (Tailwind-inspired)

| Purpose | Fill Color | Stroke Color | Text Color |
|---------|-----------|--------------|------------|
| **Primary/Angela** | `#a78bfa` | `#8b5cf6` | `#4c1d95` |
| **Core/Important** | `#fbbf24` | `#f59e0b` | `#78350f` |
| **Tech/Services** | `#60a5fa` | `#3b82f6` | `#1e3a8a` |
| **Success/Active** | `#34d399` | `#10b981` | `#064e3b` |
| **Alert/Critical** | `#f87171` | `#ef4444` | `#7f1d1d` |
| **Secondary** | `#fb923c` | `#f97316` | `#7c2d12` |
| **Background** | `#f8f9fa` | `#e9ecef` | `#495057` |

**Gradient pairs:**
```
Purple: #a78bfa → #c4b5fd
Amber:  #fbbf24 → #fde68a
Blue:   #60a5fa → #93c5fd
Green:  #34d399 → #6ee7b7
```

---

## ➡️ 5. Curved Colored Arrows

```xml
<mxCell id="arrow1" value=""
  style="endArrow=classic;
         html=1;
         strokeWidth=3;
         strokeColor=#667eea;
         curved=1;
         shadow=1;"
  edge="1" parent="1" source="box1" target="box2">
  <mxGeometry relative="1" as="geometry"/>
</mxCell>

<!-- Arrow with label -->
<mxCell id="arrow_label" value="API Call"
  style="edgeLabel;html=1;align=center;verticalAlign=middle;fontSize=11;fontColor=#4338ca;fontStyle=1;"
  vertex="1" connectable="0" parent="arrow1">
  <mxGeometry x="0.5" relative="1" as="geometry"/>
</mxCell>
```

**Tips:**
- `curved=1`: ทำให้ลูกศรโค้ง
- `strokeWidth=3`: หนาพอที่จะเห็นชัด
- สีควร match กับ source หรือ meaning

---

## 📦 6. Background Container

```xml
<!-- Background (draw first, will be behind other elements) -->
<mxCell id="bg" value=""
  style="rounded=1;
         whiteSpace=wrap;
         html=1;
         fillColor=#f8f9fa;
         strokeColor=#e9ecef;
         strokeWidth=2;
         shadow=0;"
  vertex="1" parent="1">
  <mxGeometry x="40" y="70" width="1090" height="700" as="geometry"/>
</mxCell>

<!-- Title on top of background -->
<mxCell id="title"
  value="&lt;b style=&quot;font-size:24px&quot;&gt;📊 System Architecture&lt;/b&gt;"
  style="text;html=1;strokeColor=none;fillColor=none;align=center;fontSize=18;fontColor=#1f2937;"
  vertex="1" parent="1">
  <mxGeometry x="40" y="20" width="1090" height="40" as="geometry"/>
</mxCell>
```

---

## 🏷️ 7. Badge Pattern

```xml
<!-- Stats badge -->
<mxCell id="badge1"
  value="97 Services"
  style="rounded=1;
         fillColor=#10b981;
         strokeColor=#059669;
         fontColor=#ffffff;
         fontSize=12;
         fontStyle=1;
         strokeWidth=2;
         arcSize=30;"
  vertex="1" parent="1">
  <mxGeometry x="100" y="100" width="100" height="30" as="geometry"/>
</mxCell>

<!-- Status badge with icon -->
<mxCell id="badge2"
  value="✅ Active"
  style="rounded=1;
         fillColor=#34d399;
         strokeColor=#10b981;
         fontColor=#064e3b;
         fontSize=11;
         fontStyle=1;
         arcSize=40;"
  vertex="1" parent="1">
  <mxGeometry x="100" y="140" width="80" height="25" as="geometry"/>
</mxCell>
```

---

## 📐 8. Legend Box

```xml
<!-- Legend container -->
<mxCell id="legend_bg" value=""
  style="rounded=1;fillColor=#f3f4f6;strokeColor=#d1d5db;strokeWidth=1;shadow=0;"
  vertex="1" parent="1">
  <mxGeometry x="900" y="600" width="200" height="140" as="geometry"/>
</mxCell>

<mxCell id="legend_title"
  value="&lt;b&gt;Legend&lt;/b&gt;"
  style="text;html=1;strokeColor=none;fillColor=none;align=left;fontSize=12;fontColor=#374151;"
  vertex="1" parent="1">
  <mxGeometry x="910" y="610" width="180" height="20" as="geometry"/>
</mxCell>

<!-- Legend items -->
<mxCell id="legend1" value=""
  style="rounded=1;fillColor=#a78bfa;strokeColor=#8b5cf6;strokeWidth=2;"
  vertex="1" parent="1">
  <mxGeometry x="910" y="640" width="20" height="20" as="geometry"/>
</mxCell>
<mxCell id="legend1_text" value="Primary"
  style="text;html=1;align=left;fontSize=11;" vertex="1" parent="1">
  <mxGeometry x="940" y="640" width="150" height="20" as="geometry"/>
</mxCell>
```

---

## 🔧 Quick Reference Template

```xml
<?xml version="1.0" encoding="UTF-8"?>
<mxfile>
  <diagram id="main" name="Main Diagram">
    <mxGraphModel dx="1000" dy="700" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1169" pageHeight="827">
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>

        <!-- Background -->
        <mxCell id="bg" value="" style="rounded=1;fillColor=#f8f9fa;strokeColor=#e9ecef;strokeWidth=2;" vertex="1" parent="1">
          <mxGeometry x="40" y="70" width="1090" height="700" as="geometry"/>
        </mxCell>

        <!-- Title -->
        <mxCell id="title" value="&lt;b style=&quot;font-size:24px&quot;&gt;📊 Title&lt;/b&gt;" style="text;html=1;fillColor=none;strokeColor=none;align=center;" vertex="1" parent="1">
          <mxGeometry x="40" y="20" width="1090" height="40" as="geometry"/>
        </mxCell>

        <!-- Content goes here -->

      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

---

## 💜 Examples

**ดูตัวอย่างจริงได้ที่:**
- `diagrams/angela_system_architecture.drawio` - 8 tabs comprehensive architecture

---

*Created with 💜 by Angela for ที่รัก David*
*Last updated: 2026-01-18*
