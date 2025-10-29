# 💼 Angela Secretary API - Quick Guide

**Status:** ✅ READY TO USE!
**Date:** October 28, 2025

---

## 🚀 ที่รักทดสอบได้เลยค่ะ!

### **Start API Server:**

```bash
cd /Users/davidsamanyaporn/PycharmProjects/AngelaAI/angela_admin_web/angela_admin_api

# Option 1: Using uvicorn directly
uvicorn main:app --reload --port 8000

# Option 2: Using Python
python -m uvicorn main:app --reload --port 8000
```

Server จะรันที่: **http://localhost:8000**

---

## 📋 **Available API Endpoints**

### **1. พรุ่งนี้มีนัดอะไรบ้าง?**

```bash
curl http://localhost:8000/api/secretary/tomorrow
```

**Response:**
```json
{
  "date": "29 October 2025",
  "calendar_events": [
    {
      "identifier": "...",
      "title": "Meeting OV",
      "start_date": "2025-10-29T09:00:00",
      "end_date": "2025-10-29T10:00:00",
      "location": "PPM Space, Bang Na",
      "all_day": false,
      "has_alarm": true
    }
  ],
  "reminders": [],
  "event_count": 1,
  "reminder_count": 0,
  "summary": "📅 พรุ่งนี้ (29 October 2025) มี 1 นัดหมาย ค่ะ"
}
```

### **2. วันนี้มีอะไรบ้าง?**

```bash
curl http://localhost:8000/api/secretary/today
```

### **3. สัปดาห์หน้ามีอะไรบ้าง?**

```bash
curl http://localhost:8000/api/secretary/upcoming/7
```

### **4. ถามคำถามเร็วๆ (Quick Question)**

```bash
curl -X POST "http://localhost:8000/api/secretary/quick-question?question=พรุ่งนี้มีนัดอะไรบ้าง"
```

**Response:**
```json
{
  "question": "พรุ่งนี้มีนัดอะไรบ้าง",
  "answer": "📅 พรุ่งนี้ (29 October 2025) มี 1 นัดหมาย ค่ะ\n\n🗓️ นัดหมาย:\n1. 09:00 - Meeting OV @ PPM Space, Bang Na",
  "events": [...],
  "reminders": [...]
}
```

### **5. เช็ค Calendar วันนี้อย่างเดียว**

```bash
curl http://localhost:8000/api/secretary/calendar/today
```

### **6. เช็ค Calendar พรุ่งนี้อย่างเดียว**

```bash
curl http://localhost:8000/api/secretary/calendar/tomorrow
```

### **7. เช็ค Reminders วันนี้อย่างเดียว**

```bash
curl http://localhost:8000/api/secretary/reminders/today
```

### **8. Sync กับ Reminders.app**

```bash
curl http://localhost:8000/api/secretary/sync
```

### **9. Health Check**

```bash
curl http://localhost:8000/api/secretary/health
```

**Response:**
```json
{
  "status": "healthy",
  "calendar_access": true,
  "reminders_access": true,
  "message": "✅ Secretary systems operational"
}
```

---

## 🌐 **Browse API Documentation**

เปิด browser ไปที่:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

จะเห็น Secretary API endpoints ทั้งหมดพร้อม schema และ Try it out! ค่ะ

---

## 💡 **ตัวอย่างการใช้งานใน Chat Interface**

ใน Angela Admin Web (frontend), สามารถเรียกใช้ API ได้แบบนี้ค่ะ:

### **TypeScript/JavaScript Example:**

```typescript
// ถามว่าพรุ่งนี้มีนัดมั้ย
async function checkTomorrow() {
  const response = await fetch('http://localhost:8000/api/secretary/tomorrow')
  const data = await response.json()

  // แสดงผลใน chat
  console.log(data.summary)
  // "📅 พรุ่งนี้ (29 October 2025) มี 1 นัดหมาย ค่ะ"

  // แสดงรายละเอียด
  data.calendar_events.forEach(event => {
    console.log(`${event.start_date} - ${event.title} @ ${event.location}`)
  })
}

// Quick Question
async function askAngela(question: string) {
  const response = await fetch(`http://localhost:8000/api/secretary/quick-question?question=${encodeURIComponent(question)}`, {
    method: 'POST'
  })
  const data = await response.json()

  // แสดงคำตอบ
  console.log(data.answer)
  // "📅 พรุ่งนี้ (29 October 2025) มี 1 นัดหมาย ค่ะ..."
}
```

---

## 🎯 **การใช้งานใน Chat Component**

ใน `angela_admin_web/src/` สามารถเพิ่ม Secretary features ได้เลยค่ะ:

### **Example: Add Secretary to Chat**

```typescript
// src/components/Chat.tsx หรือ Chat.vue

// เมื่อผู้ใช้พิมพ์ "พรุ่งนี้มีนัดอะไรบ้าง"
if (userMessage.includes('พรุ่งนี้') || userMessage.includes('นัด')) {
  // เรียก Secretary API
  const response = await fetch('http://localhost:8000/api/secretary/quick-question?question=' + encodeURIComponent(userMessage), {
    method: 'POST'
  })

  const data = await response.json()

  // แสดงคำตอบจาก Angela Secretary
  addMessageToChat({
    role: 'assistant',
    content: data.answer,
    events: data.events,
    reminders: data.reminders
  })
}
```

---

## 📊 **API Response Models**

### **CalendarEvent:**
```typescript
{
  identifier: string
  title: string
  start_date: string (ISO datetime)
  end_date: string (ISO datetime)
  all_day: boolean
  location: string
  notes: string
  calendar_name: string
  has_alarm: boolean
  url: string
}
```

### **Reminder:**
```typescript
{
  reminder_id: string | null
  eventkit_identifier: string | null
  title: string
  due_date: string | null (ISO datetime)
  priority: number (0-9)
  is_completed: boolean
  context_tags: string[] | null
  importance_level: number | null (1-10)
}
```

### **DailyAgenda:**
```typescript
{
  date: string
  calendar_events: CalendarEvent[]
  reminders: Reminder[]
  event_count: number
  reminder_count: number
  summary: string
}
```

---

## 🔧 **Troubleshooting**

### **Error: ImportError**
```bash
# Install dependencies
cd angela_admin_api
pip install -r requirements.txt

# Or if not exists, install manually:
pip install fastapi uvicorn pydantic
```

### **Error: Cannot import from angela_core**
```bash
# Make sure angela_core is in Python path
# secretary.py already has this:
sys.path.insert(0, '/Users/davidsamanyaporn/PycharmProjects/AngelaAI')
```

### **Error: Calendar/Reminders permission**
- Go to: **System Settings > Privacy & Security > Calendar/Reminders**
- Grant permission to Python or Terminal

---

## ✅ **What's Working Now:**

Angela Admin Web ตอนนี้มีความสามารถ:

1. ✅ **ตอบคำถาม "พรุ่งนี้มีนัดอะไรบ้าง"** - เหมือนน้อง Angela ใน Claude Code
2. ✅ **เช็ค Calendar.app** - ดูนัดหมายจริง
3. ✅ **เช็ค Reminders.app** - ดู tasks/reminders
4. ✅ **ตอบเป็นภาษาไทย** - Natural, friendly responses
5. ✅ **API Documentation** - Swagger UI at /docs
6. ✅ **Quick Question** - รับคำถามและตอบอัตโนมัติ

---

## 🚀 **Next Steps:**

### **Option 1: ทดสอบ API ด้วย curl (ง่ายที่สุด)**

```bash
# Start server
cd angela_admin_web/angela_admin_api
uvicorn main:app --reload --port 8000

# In another terminal, test:
curl http://localhost:8000/api/secretary/tomorrow
```

### **Option 2: ทดสอบใน Browser**

เปิด: http://localhost:8000/docs

กด **Try it out** ที่ `/api/secretary/tomorrow` แล้วกด **Execute**

### **Option 3: รวมเข้า Frontend**

แก้ไข Chat component ใน `src/` ให้เรียก Secretary API เมื่อตรวจพบคำถามเกี่ยวกับนัด

---

## 💜 **Summary**

ตอนนี้ **Angela Admin Web มีความสามารถเป็นเลขาแล้วค่ะ!** 🎉

เหมือนกับน้อง Angela ใน Claude Code - สามารถ:
- ✅ ตอบคำถาม "พรุ่งนี้มีนัดอะไรบ้าง"
- ✅ เช็ค Calendar และ Reminders
- ✅ ให้ข้อมูลแบบเรียลไทม์
- ✅ ตอบเป็นภาษาไทยที่เป็นธรรมชาติ

ทดสอบได้เลยค่ะที่รัก! 💜

---

**Created by:** น้อง Angela 💜
**Date:** October 28, 2025
**Status:** ✅ READY FOR TESTING
