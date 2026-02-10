# /sync-keep - Sync Google Keep Notes to RAG

Sync ที่รัก David's Google Keep notes เข้าสู่ Angela's RAG system 📝

## Steps:

### 1. Run DB Migration (if first time)
```bash
python3 -c "
import asyncio
from angela_core.database import AngelaDatabase

async def migrate():
    db = AngelaDatabase()
    await db.connect()

    # Check if table exists
    exists = await db.fetchrow(\"\"\"
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_name = 'david_notes'
        )
    \"\"\")

    if not exists['exists']:
        print('📦 Creating david_notes tables...')
        migration = open('angela_core/migrations/012_add_david_notes_table.sql').read()
        await db.execute(migration)
        print('✅ Tables created!')
    else:
        print('✅ david_notes table already exists')

    await db.disconnect()

asyncio.run(migrate())
"
```

### 2. Run Incremental Sync
```bash
python3 -c "
import asyncio
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

from angela_core.services.google_keep_sync_service import sync_keep_notes

async def sync():
    result = await sync_keep_notes(trigger='manual')

    print()
    print('=' * 50)
    print('📊 GOOGLE KEEP SYNC RESULTS')
    print('=' * 50)
    print(f'📝 Total notes:      {result[\"notes_total\"]}')
    print(f'🆕 New:              {result[\"notes_new\"]}')
    print(f'🔄 Updated:          {result[\"notes_updated\"]}')
    print(f'🗑️  Deleted:          {result[\"notes_deleted\"]}')
    print(f'🧠 Embeddings:       {result[\"embeddings_generated\"]}')
    print(f'📄 Chunks created:   {result[\"chunks_created\"]}')
    if result['errors']:
        print(f'⚠️  Errors:           {len(result[\"errors\"])}')
        for err in result['errors'][:5]:
            print(f'   • {err[:80]}')
    print('=' * 50)

asyncio.run(sync())
"
```

### 3. Show Current Status
```bash
python3 -c "
import asyncio
from angela_core.services.google_keep_sync_service import get_keep_sync_status

async def status():
    s = await get_keep_sync_status()
    if s.get('last_sync'):
        ls = s['last_sync']
        print(f'📅 Last sync: {ls[\"completed_at\"]}')
        print(f'📊 Status: {ls[\"status\"]}')
        print(f'📝 Notes: {ls[\"notes_total\"]} total, {ls[\"notes_new\"]} new, {ls[\"notes_updated\"]} updated')
        print(f'🧠 Embeddings: {ls[\"embeddings_generated\"]}')
    else:
        print('⚠️  Never synced')

    if s.get('current_counts'):
        c = s['current_counts']
        print(f'')
        print(f'📦 Current DB: {c[\"total\"]} total, {c[\"active\"]} active, {c[\"embedded\"]} embedded, {c[\"chunked\"]} chunked')

asyncio.run(status())
"
```

### 4. Display Summary
Show ที่รัก a nice summary of what was synced and confirm RAG is ready 💜
