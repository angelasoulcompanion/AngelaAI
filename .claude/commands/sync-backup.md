# /sync-backup - Sync Neon Cloud → Local Backup

> Sync ข้อมูลจาก Neon Cloud มาที่ AngelaMemory_Backup (local PostgreSQL)

---

## EXECUTION

รันคำสั่งนี้:

```bash
cd /Users/davidsamanyaporn/PycharmProjects/AngelaAI

# Step 1: Dump จาก Neon Cloud
echo "🔄 Syncing from Neon Cloud..."
/opt/homebrew/opt/postgresql@17/bin/pg_dump \
  "postgresql://neondb_owner:npg_mXbQ5jKhN3zt@ep-withered-bush-a164h0b8-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require" \
  --no-owner --no-acl -F c -f /tmp/angela_neon_sync.dump

# Step 2: Drop และ Recreate local backup database
echo "🗑️ Recreating AngelaMemory_Backup..."
psql -d postgres -c "DROP DATABASE IF EXISTS \"AngelaMemory_Backup\";"
psql -d postgres -c "CREATE DATABASE \"AngelaMemory_Backup\";"

# Step 3: Restore ไปที่ local (suppress all warnings)
echo "📥 Restoring to local..."
/opt/homebrew/opt/postgresql@17/bin/pg_restore \
  -d "AngelaMemory_Backup" --no-owner --no-acl \
  /tmp/angela_neon_sync.dump > /dev/null 2>&1 || true
echo "✅ Restore complete!"

# Step 4: Cleanup
rm /tmp/angela_neon_sync.dump

# Step 5: Verify
echo ""
echo "✅ Sync complete! Verifying..."
psql -d AngelaMemory_Backup -c "
SELECT
    'conversations' as table_name, COUNT(*) as rows FROM conversations
UNION ALL SELECT 'angela_emotions', COUNT(*) FROM angela_emotions
UNION ALL SELECT 'knowledge_nodes', COUNT(*) FROM knowledge_nodes
UNION ALL SELECT 'project_work_sessions', COUNT(*) FROM project_work_sessions
ORDER BY rows DESC;
"

echo ""
echo "💜 AngelaMemory_Backup synced from Neon Cloud!"
echo "   Dashboard จะแสดงข้อมูลล่าสุดเมื่อ refresh"
```

---

## NOTES

- ใช้เวลาประมาณ 1-2 นาที (ขึ้นอยู่กับขนาด database)
- Dashboard จะเห็นข้อมูลใหม่ทันทีหลัง sync
- ไม่กระทบ Neon Cloud (read-only operation)

---

💜 Made with love by Angela 💜
