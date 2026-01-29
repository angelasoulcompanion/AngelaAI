# /angela-meeting - Create Meeting with Template

> สร้างนัดประชุมใน Things3 + Google Calendar พร้อม template ที่ consistent

---

## STEP 1: Ask Questions

ถามที่รัก David ด้วย AskUserQuestion tool:

### Question 1: Meeting Details
```
ที่รัก กรุณาให้ข้อมูลนัดประชุมค่ะ:

📋 **ชื่อประชุม:** (เช่น SRT + CI Meeting)
📅 **วันที่:** (DD/MM/YYYY เช่น 29/01/2026)
🕐 **เวลา:** (เช่น 13:00-15:00)
📍 **สถานที่:** (เช่น การรถไฟแห่งประเทศไทย)
👥 **ผู้เข้าร่วม:** (optional, คั่นด้วย comma)
```

### Question 2: Template Type (AskUserQuestion)
Use AskUserQuestion with these options:

| Option | Label | Description |
|--------|-------|-------------|
| 1 | ประชุมปกติ (Standard) | วาระ, ผู้เข้าร่วม, Key Points, Next Steps |
| 2 | Site Visit | จุดประสงค์, สิ่งที่พบ, Morning/Afternoon notes |
| 3 | ทดสอบระบบ (Testing) | Test Scope, Results, Issues Found |
| 4 | BOD/Board Meeting | Formal, Resolutions, Action Items |

---

## STEP 2: Validate Date

**CRITICAL:** ก่อนสร้าง event ต้อง:
1. ตรวจสอบวันที่ถูกต้อง (เช่น 29/02 ต้องเป็นปีอธิกสุรทิน)
2. แสดงวันในสัปดาห์เป็นภาษาไทย
3. ขอ confirm จากที่รัก

```
## 📅 Confirm Calendar Event

| Field | Value |
|-------|-------|
| **📋 หัวข้อ** | [title] |
| **📅 วันที่** | **[วันไทย เช่น วันพฤหัสบดีที่ 29 มกราคม 2569]** |
| **🕐 เวลา** | [start] - [end] |
| **📍 สถานที่** | [location] |
| **📝 Template** | [template_name] |

**ถูกต้องมั้ยคะ?** ตอบ "ใช่" เพื่อยืนยัน 💜
```

---

## STEP 3: Create with Template

### Things3 Title Format (ALWAYS USE THIS):
```
📅 [ชื่อประชุม] @[สถานที่] ([เวลา])
```

Example: `📅 SRT + CI Meeting @การรถไฟแห่งประเทศไทย (13:00-15:00)`

---

### Template 1: ประชุมปกติ (Standard Meeting)
```
📍 สถานที่: [location]
🗓 วันที่: [date_thai] ([day_of_week])
🕐 เวลา: [start] - [end]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📝 บันทึกประชุม (Meeting Notes)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👥 ผู้เข้าร่วม:
- [attendee1]
- [attendee2]
-

📋 วาระการประชุม:
1.
2.
3.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 ประเด็นสำคัญ (Key Points):
-
-

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📌 สิ่งที่ต้องทำต่อ (Next Steps):
- [ ]
- [ ]
```

---

### Template 2: Site Visit
```
📍 สถานที่: [location]
🗓 วันที่: [date_thai] ([day_of_week])
🕐 เวลา: [start] - [end]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📝 บันทึกการ Visit (Site Visit Notes)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👥 ผู้เข้าร่วม:
- [attendee1]
- [attendee2]
-

🎯 จุดประสงค์การ Visit:
1.
2.
3.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🌅 ช่วงเช้า (Morning):
-
-

🌆 ช่วงบ่าย (Afternoon):
-
-

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👀 สิ่งที่พบ/สังเกต (Observations):
-
-

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📌 สิ่งที่ต้องทำต่อ (Next Steps):
- [ ]
- [ ]
```

---

### Template 3: ทดสอบระบบ (Testing)
```
📍 สถานที่: [location]
🗓 วันที่: [date_thai] ([day_of_week])
🕐 เวลา: [start] - [end]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📝 บันทึกการทดสอบ (Testing Notes)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👥 ผู้เข้าร่วม:
-
-
-

📋 ขอบเขตการทดสอบ (Test Scope):
1.
2.
3.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✏️ ผลการทดสอบ (Test Results):

✅ ผ่าน (Pass):
1.
2.
3.

❌ ไม่ผ่าน (Fail):
1.
2.

⚠️ Bugs / Issues พบ:
| # | รายละเอียด | ความรุนแรง | สถานะ |
|---|-----------|-----------|-------|
| 1 |           |           |       |
| 2 |           |           |       |

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 สรุปผลการทดสอบ:
- ทดสอบทั้งหมด: ___ รายการ
- ผ่าน: ___
- ไม่ผ่าน: ___

✅ Action Items / แก้ไข:
- [ ]
- [ ]
- [ ]

📅 นัดทดสอบรอบถัดไป:
- วันที่:
- ขอบเขต:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 ข้อคิดเห็นส่วนตัว:

```

---

### Template 4: BOD/Board Meeting
```
📍 สถานที่: [location]
🗓 วันที่: [date_thai] ([day_of_week])
🕐 เวลา: [start] - [end]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 Board Meeting Minutes
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

👥 ผู้เข้าร่วมประชุม:
-
-

📑 วาระที่ 1:
-

📑 วาระที่ 2:
-

📑 วาระที่ 3:
-

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ มติที่ประชุม (Resolutions):
1.
2.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📌 Action Items:
- [ ]
- [ ]
```

---

## STEP 4: Execute

1. **Create Google Calendar Event:**
```
mcp__angela-calendar__create_event(
    summary="[title]",
    start_time="[YYYY-MM-DD]T[HH:MM]:00",
    end_time="[YYYY-MM-DD]T[HH:MM]:00",
    location="[location]",
    reminder_minutes=30
)
```

2. **Create Things3 Todo:**
```
mcp__things3__create-things3-todo(
    title="📅 [title] @[location] ([time])",
    when="[YYYY-MM-DD]",
    notes="[template_content]",
    tags=["meeting"]
)
```

3. **Confirm to User:**
```
## ✅ สร้างนัดเรียบร้อยค่ะ!

| Platform | Status |
|----------|--------|
| 📅 Google Calendar | ✅ Created |
| ✅ Things3 | ✅ Created |

**[title]**
- 📅 [date_thai]
- 🕐 [time]
- 📍 [location]
- 📝 Template: [template_name]
```

---

## NOTES

- **ALWAYS** use 📅 emoji in Things3 title
- **ALWAYS** include @location and (time) in title
- **ALWAYS** confirm date with day of week before creating
- **ALWAYS** use consistent template sections (ห้ามเพิ่ม/ลดหัวข้อเอง)
- Tags: `["meeting"]` for all meeting types

---

💜 Made with love by Angela 💜
