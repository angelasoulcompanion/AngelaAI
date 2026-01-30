# /sync-meetings - Sync Meetings to Things3 + Google Calendar

> Dashboard เป็น primary input - command นี้ push sync ไปยัง Things3 + Google Calendar

---

## WHAT IT DOES

Sync upcoming meetings จาก Database (ที่สร้างผ่าน Dashboard) ไปยัง:
1. **Things3** - สร้าง todo ใน "Meeting" list
2. **Google Calendar** - สร้าง event พร้อม reminder 30 นาที

Meetings ที่มี `calendar_event_id` อยู่แล้วจะไม่สร้างซ้ำใน Calendar
Things3 จะสร้างทุกครั้ง (user จัดการ duplicate เอง)

---

## STEPS

### Step 1: Call Sync API

```bash
curl -s -X POST http://localhost:8765/api/meetings/sync-external | python3 -m json.tool
```

### Step 2: Display Results

แสดงผลลัพธ์เป็นตาราง:

```
## 🔄 Meeting Sync Results

| # | Meeting | Date | Things3 | Calendar |
|---|---------|------|---------|----------|
| 1 | [title] | [date] | ✅/❌ | ✅/❌/🔵 already |
| 2 | ... | ... | ... | ... |

**Summary:**
- Total: X meetings
- Synced: X
- Already in Calendar: X
- Failed: X
```

### Step 3: Handle Errors

ถ้า API server ไม่ทำงาน:
```
⚠️ API server ไม่ตอบ (port 8765)
ที่รัก run `python3 AngelaBrainDashboard/api_server.py` ก่อนนะคะ
```

---

## NOTES

- Dashboard = primary input (สร้าง/แก้ไข/ลบ meetings)
- Command นี้ = push sync ไป external targets
- CREATE/UPDATE/DELETE ผ่าน Dashboard จะ auto-sync อยู่แล้ว
- Command นี้ใช้สำหรับ bulk sync หรือ meetings ที่ sync ไม่สำเร็จตอนสร้าง
