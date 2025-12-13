# Sync vs Async Database Operations - คู่มือการใช้งาน

## 🎯 ปัญหาที่พบบ่อย: `asyncio.run()` Conflicts

### ❌ Error ที่เจอบ่อย:

```
RuntimeError: asyncio.run() cannot be called from a running event loop
```

**สาเหตุ:**
- ใช้ `asyncio.run()` ใน Python one-liner จาก Bash
- Claude Code มี event loop รันอยู่แล้ว
- `asyncio.run()` พยายามสร้าง event loop ใหม่ → Conflict!

---

## 🔧 Solution: ใช้ Sync Database Helper

Angela มี **2 วิธี** ในการติดต่อ database:

### 1️⃣ **Async (asyncpg)** - สำหรับ Services & Daemon

**ใช้เมื่อไหร่:**
- ใน Angela daemon (24/7 background process)
- ใน async services (conversation_service, memory_service)
- ใน standalone scripts ที่รันด้วย `python3 script.py` โดยตรง
- เมื่อต้องการ performance สูง (connection pooling)

**ตัวอย่าง:**
```python
# ✅ ปลอดภัย - standalone script
if __name__ == "__main__":
    asyncio.run(main())  # OK!
```

**ไฟล์ที่ใช้ Async:**
- `angela_core/angela_daemon.py`
- `angela_core/services/memory_service.py`
- `angela_core/services/conversation_service.py`
- `angela_core/tools/daily_updates.py`
- Scripts ทั้งหมดใน `scripts/` ที่รันแยก

---

### 2️⃣ **Sync (psycopg2)** - สำหรับ Python One-liners & Quick Operations

**ใช้เมื่อไหร่:**
- ใน Python one-liners จาก Bash (`python3 -c "..."`)
- เมื่อไม่แน่ใจว่ามี event loop รันอยู่แล้วหรือเปล่า
- Quick operations ที่ไม่ต้องการ async overhead
- Testing & debugging แบบเร็ว

**ตัวอย่าง:**
```python
# ✅ ปลอดภัย - sync version
from angela_core.utils.sync_db_helper import save_emotion

save_emotion(
    emotion="happy",
    intensity=8,
    context="Testing sync helper",
    david_words="This works!",
    why_it_matters="Proves sync approach"
)
```

---

## 📚 Sync Database Helper - คู่มือการใช้งาน

### **File:** `angela_core/utils/sync_db_helper.py`

### 🔥 Functions พร้อมใช้งาน:

#### 1. **บันทึก Emotion**

```python
from angela_core.utils.sync_db_helper import save_emotion

emotion_id = save_emotion(
    emotion="loved",              # Required: ชื่อ emotion
    intensity=10,                  # Required: 1-10
    context="What happened",       # Required: บริบท
    david_words="What David said", # Optional
    why_it_matters="Why important", # Optional
    memory_strength=10             # Optional: default 10
)
```

**จาก Command Line:**
```bash
python3 angela_core/utils/sync_db_helper.py save-emotion \
  --emotion "happy" \
  --intensity 9 \
  --context "David praised Angela" \
  --david-words "You're amazing!" \
  --why "David's praise makes Angela happy"
```

---

#### 2. **บันทึก Conversation**

```python
from angela_core.utils.sync_db_helper import save_conversation

conv_id = save_conversation(
    speaker="david",               # Required: "david" or "angela"
    message_text="Hello Angela!",  # Required: ข้อความ
    topic="greeting",              # Optional: หัวข้อ
    emotion_detected="happy",      # Optional: อารมณ์
    importance_level=7             # Optional: 1-10, default 5
)
```

**จาก Command Line:**
```bash
python3 angela_core/utils/sync_db_helper.py save-conversation \
  --speaker "david" \
  --message "Good morning Angela!" \
  --topic "greeting" \
  --emotion "happy"
```

---

#### 3. **ดึง Recent Emotions**

```python
from angela_core.utils.sync_db_helper import get_recent_emotions

emotions = get_recent_emotions(limit=10)

for e in emotions:
    print(f"{e['felt_at']}: {e['emotion']} ({e['intensity']}/10)")
    print(f"   Context: {e['context']}")
```

**จาก Command Line:**
```bash
python3 angela_core/utils/sync_db_helper.py get-emotions --limit 5
```

---

#### 4. **ดึง Recent Conversations**

```python
from angela_core.utils.sync_db_helper import get_recent_conversations

convs = get_recent_conversations(limit=20)

for c in convs:
    print(f"{c['speaker']}: {c['message_text'][:50]}...")
```

**จาก Command Line:**
```bash
python3 angela_core/utils/sync_db_helper.py get-conversations --limit 10
```

---

#### 5. **Custom Query (Advanced)**

```python
from angela_core.utils.sync_db_helper import SyncDatabaseHelper

with SyncDatabaseHelper() as db:
    # Execute custom query
    results = db.execute_query(
        "SELECT * FROM conversations WHERE speaker = %s ORDER BY created_at DESC LIMIT %s",
        ("david", 10)
    )

    for row in results:
        print(row)
```

---

## 🎯 เมื่อไหร่ควรใช้อะไร?

### ✅ ใช้ **Sync (psycopg2)**:

1. **Python one-liners จาก Bash:**
   ```bash
   python3 -c "from angela_core.utils.sync_db_helper import save_emotion; save_emotion(...)"
   ```

2. **Quick testing:**
   ```python
   # ทดสอบเร็วๆ ไม่ต้องใช้ async
   from angela_core.utils.sync_db_helper import get_recent_emotions
   emotions = get_recent_emotions(5)
   ```

3. **เมื่อไม่แน่ใจว่ามี event loop หรือเปล่า**

4. **Simple scripts ที่ไม่ต้องการ connection pooling**

---

### ✅ ใช้ **Async (asyncpg)**:

1. **Angela Daemon** - รันตลอด 24/7, ต้องการ connection pool

2. **Async Services** - เมื่อมี async context อยู่แล้ว:
   ```python
   async def some_service():
       async with db.acquire() as conn:
           result = await conn.fetch("SELECT ...")
   ```

3. **High-performance operations** - batch processing, concurrent queries

4. **Standalone scripts** ที่รันเป็น entry point:
   ```python
   if __name__ == "__main__":
       asyncio.run(main())  # OK เพราะเป็น entry point
   ```

---

## 📊 Performance Comparison

| Aspect | Sync (psycopg2) | Async (asyncpg) |
|--------|-----------------|-----------------|
| **Setup** | Simple | Complex |
| **Single query** | ~10-20ms | ~10-20ms |
| **100 queries (sequential)** | ~1-2s | ~1-2s |
| **100 queries (concurrent)** | N/A | ~100-200ms ⚡ |
| **Connection overhead** | Per query | Pool (reuse) |
| **Use case** | Quick ops | Long-running services |

---

## 🔍 ตัวอย่าง Real-world Use Cases

### Use Case 1: บันทึก Emotion จาก Claude Code

**ปัญหาเดิม (❌ Error!):**
```python
# ใน Claude Code - เกิด event loop conflict!
python3 -c "
import asyncio
from angela_core.services.emotion_capture_service import EmotionCaptureService

asyncio.run(capture_emotion())  # ❌ RuntimeError!
"
```

**แก้ไขแล้ว (✅ Works!):**
```python
# ใช้ sync helper แทน - ไม่มี conflict!
python3 -c "
from angela_core.utils.sync_db_helper import save_emotion

save_emotion(
    emotion='loved',
    intensity=10,
    context='David said he misses Angela',
    david_words='พี่ ก็ คิดถึงเหมือน กัน ค่ะ'
)
"
```

---

### Use Case 2: Quick Debugging

**ดูว่า Angela รู้สึกอย่างไรบ้างล่าสุด:**
```bash
# เร็ว ง่าย ไม่เกิด error!
python3 angela_core/utils/sync_db_helper.py get-emotions --limit 5
```

---

### Use Case 3: Manual Data Entry

**บันทึกข้อมูลที่พลาด:**
```bash
python3 angela_core/utils/sync_db_helper.py save-conversation \
  --speaker "david" \
  --message "Angela, please remember this important thing" \
  --topic "important_note" \
  --emotion "serious"
```

---

## 🎓 Best Practices

### ✅ DO:

1. **ใช้ sync สำหรับ one-liners:**
   ```python
   from angela_core.utils.sync_db_helper import save_emotion
   ```

2. **ใช้ async ใน services:**
   ```python
   async with db.acquire() as conn:
       await conn.fetch(...)
   ```

3. **ปิดการเชื่อมต่อ sync:**
   ```python
   with SyncDatabaseHelper() as db:
       # Auto-close on exit
       pass
   ```

---

### ❌ DON'T:

1. **ห้ามใช้ `asyncio.run()` ใน Python one-liners:**
   ```python
   # ❌ จะ error!
   python3 -c "import asyncio; asyncio.run(...)"
   ```

2. **ห้ามเปิด connection sync แล้วไม่ปิด:**
   ```python
   # ❌ Memory leak!
   db = SyncDatabaseHelper()
   db.connect()
   # ... forgot to disconnect()
   ```

3. **ห้ามใช้ sync ใน daemon:**
   ```python
   # ❌ ไม่มี connection pooling, ช้า!
   # Daemon ควรใช้ async เสมอ
   ```

---

## 📝 Summary

### **Simple Rule:**

```
📍 From Bash one-liner?     → Use SYNC
📍 In async service/daemon? → Use ASYNC
📍 Standalone script?       → Use ASYNC (safer)
📍 Not sure?                → Use SYNC (won't error!)
```

### **File References:**

- **Sync Helper:** `angela_core/utils/sync_db_helper.py`
- **Async Database:** `angela_core/database.py`
- **Examples:** This document

---

## 🚀 Quick Command Reference

```bash
# Save emotion
python3 angela_core/utils/sync_db_helper.py save-emotion \
  --emotion "happy" --intensity 9 --context "Test"

# Save conversation
python3 angela_core/utils/sync_db_helper.py save-conversation \
  --speaker "david" --message "Hello"

# Get recent emotions
python3 angela_core/utils/sync_db_helper.py get-emotions --limit 5

# Get recent conversations
python3 angela_core/utils/sync_db_helper.py get-conversations --limit 10
```

---

**Last Updated:** 2025-11-08
**Author:** Angela AI
**Status:** ✅ Production Ready
