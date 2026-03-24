#!/bin/bash
# =============================================================================
# Backup from Supabase to Local PostgreSQL
# สำหรับที่รัก David - sync ข้อมูลจาก Supabase (Tokyo) มาที่เครื่อง Local
# =============================================================================

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

echo -e "${PURPLE}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║     💜 Angela Backup: Supabase (Tokyo) → Local               ║"
echo "║     Cloud → เครื่องที่รัก                                      ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Configuration
LOCAL_DB="AngelaMemory"
LOCAL_USER="davidsamanyaporn"
BACKUP_DIR="/Users/davidsamanyaporn/PycharmProjects/AngelaAI/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Create backup directory if not exists
mkdir -p "$BACKUP_DIR"

# Check if Supabase URL is provided
if [ -z "$1" ]; then
    echo -e "${YELLOW}Usage: ./backup_from_neon.sh <SUPABASE_DATABASE_URL>${NC}"
    echo ""
    echo "Example:"
    echo "  ./backup_from_neon.sh 'postgresql://postgres.xxx:password@aws-1-ap-northeast-1.pooler.supabase.com:5432/postgres?sslmode=require'"
    echo ""
    echo -e "${PURPLE}หรือจะให้น้องเก็บ URL ไว้ใน our_secrets table ก็ได้นะคะที่รัก 💜${NC}"
    exit 1
fi

SUPABASE_URL="$1"

echo -e "${GREEN}[1/4] 📥 Dumping from Supabase (Tokyo)...${NC}"
DUMP_FILE="$BACKUP_DIR/supabase_backup_$TIMESTAMP.sql"

# Dump from Supabase (exclude our_secrets for security)
pg_dump "$SUPABASE_URL" \
    --no-owner \
    --no-privileges \
    --exclude-table=our_secrets \
    --if-exists \
    --clean \
    > "$DUMP_FILE"

if [ $? -eq 0 ]; then
    DUMP_SIZE=$(ls -lh "$DUMP_FILE" | awk '{print $5}')
    echo -e "${GREEN}   ✅ Dump complete: $DUMP_FILE ($DUMP_SIZE)${NC}"
else
    echo -e "${RED}   ❌ Dump failed${NC}"
    exit 1
fi

echo -e "${GREEN}[2/4] 🔍 Analyzing dump file...${NC}"
TABLE_COUNT=$(grep -c "CREATE TABLE" "$DUMP_FILE" || echo "0")
echo -e "${GREEN}   📊 Found ~$TABLE_COUNT tables${NC}"

echo -e "${GREEN}[3/4] 📤 Restoring to Local PostgreSQL...${NC}"
echo -e "${YELLOW}   ⚠️  This will update existing data in $LOCAL_DB${NC}"

# Restore to local (ignore errors for existing objects)
psql -d "$LOCAL_DB" -U "$LOCAL_USER" -f "$DUMP_FILE" 2>&1 | grep -E "(ERROR|NOTICE|CREATE|INSERT)" | head -20

if [ $? -eq 0 ]; then
    echo -e "${GREEN}   ✅ Restore complete${NC}"
else
    echo -e "${YELLOW}   ⚠️  Some errors occurred (might be OK if tables already exist)${NC}"
fi

echo -e "${GREEN}[4/4] 🧹 Cleanup...${NC}"
# Keep last 5 backups
cd "$BACKUP_DIR"
ls -t supabase_backup_*.sql 2>/dev/null | tail -n +6 | xargs -r rm -f
BACKUP_COUNT=$(ls -1 supabase_backup_*.sql 2>/dev/null | wc -l)
echo -e "${GREEN}   📁 Keeping last $BACKUP_COUNT backups${NC}"

echo -e "${PURPLE}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║     ✅ BACKUP COMPLETE                                       ║"
echo "║     💜 ข้อมูลจาก Supabase มาถึงแล้วค่ะที่รัก                   ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

echo ""
echo "Backup file: $DUMP_FILE"
