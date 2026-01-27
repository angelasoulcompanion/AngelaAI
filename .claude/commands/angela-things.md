# /angela-things - Sync Things3 → Neon Cloud

> Sync meeting notes จาก Things3 ไปยัง Neon Cloud database แล้วแจ้งผลลัพธ์

---

## EXECUTION

### Step 1: Sync Meeting Notes from Things3

```bash
cd /Users/davidsamanyaporn/PycharmProjects/AngelaAI
python3 angela_core/daemon/meeting_sync_daemon.py
```

### Step 2: Verify Sync Result

```bash
cd /Users/davidsamanyaporn/PycharmProjects/AngelaAI
python3 -c "
import asyncio
from angela_core.database import AngelaDatabase

async def verify():
    db = AngelaDatabase()
    await db.connect()

    # Meeting counts
    total = await db.pool.fetchval('SELECT COUNT(*) FROM meeting_notes')
    open_count = await db.pool.fetchval(\"\"\"SELECT COUNT(*) FROM meeting_notes WHERE things3_status = 'open'\"\"\")
    completed = await db.pool.fetchval(\"\"\"SELECT COUNT(*) FROM meeting_notes WHERE things3_status = 'completed'\"\"\")
    actions = await db.pool.fetchval('SELECT COUNT(*) FROM meeting_action_items WHERE is_completed = FALSE')

    # Last sync
    last_sync = await db.pool.fetchrow('SELECT sync_date, meetings_found, meetings_synced, meetings_updated FROM meeting_sync_log ORDER BY synced_at DESC LIMIT 1')

    print(f'Total meetings: {total}')
    print(f'Open: {open_count} | Completed: {completed}')
    print(f'Open action items: {actions}')
    if last_sync:
        print(f'Last sync: {last_sync[\"sync_date\"]} - Found: {last_sync[\"meetings_found\"]}, New: {last_sync[\"meetings_synced\"]}, Updated: {last_sync[\"meetings_updated\"]}')

    await db.disconnect()

asyncio.run(verify())
"
```

### Step 3: Report to User

แจ้งผลลัพธ์ให้ที่รัก David:
- จำนวน meetings ที่ sync ได้ (new + updated)
- จำนวน open / completed
- จำนวน open action items
- บอกให้ refresh Dashboard เพื่อดูข้อมูลใหม่

---

## NOTES

- Things3 database อยู่ที่ `~/Library/Group Containers/JLMPQHK86H.com.culturedcode.ThingsMac/`
- Sync จะ insert meetings ใหม่ และ update meetings ที่มีอยู่แล้ว
- Daemon อัตโนมัติทุกวัน 19:00 แต่เรียก manual ได้ตลอด
- Dashboard (Things Overview) จะแสดงข้อมูลใหม่ทันทีหลัง sync

---

💜 Made with love by Angela 💜
