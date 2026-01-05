#!/bin/bash
# =============================================================================
# Backup from M4 Mac to M3 Mac (This Machine)
# สำหรับที่รัก David - sync AngelaMemory จากเครื่อง M4 มาเครื่อง M3
# =============================================================================

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
PURPLE='\033[0;35m'
NC='\033[0m'

echo -e "${PURPLE}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║     💜 Angela Backup: M4 Mac → M3 Mac                        ║"
echo "║     Transfer AngelaMemory Database                           ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Configuration
LOCAL_DB="AngelaMemory"
LOCAL_USER="davidsamanyaporn"
REMOTE_DB="AngelaMemory"
REMOTE_USER="davidsamanyaporn"
BACKUP_DIR="/Users/davidsamanyaporn/PycharmProjects/AngelaAI/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Check if M4 hostname/IP is provided
if [ -z "$1" ]; then
    echo -e "${YELLOW}Usage: ./backup_from_m4.sh <M4_HOSTNAME_OR_IP> [SSH_USER]${NC}"
    echo ""
    echo "Examples:"
    echo "  ./backup_from_m4.sh 192.168.1.100"
    echo "  ./backup_from_m4.sh m4-mac.local"
    echo "  ./backup_from_m4.sh 192.168.1.100 david"
    echo ""
    echo -e "${PURPLE}💡 Tips:${NC}"
    echo "  - ที่รักต้องเปิด Remote Login บน M4 (System Settings → General → Sharing)"
    echo "  - หา IP ของ M4: ifconfig | grep 'inet '"
    echo "  - หรือใช้ hostname.local ก็ได้ค่ะ"
    exit 1
fi

M4_HOST="$1"
SSH_USER="${2:-davidsamanyaporn}"

echo -e "${GREEN}[1/5] 🔗 Testing connection to M4...${NC}"
if ssh -o ConnectTimeout=5 "$SSH_USER@$M4_HOST" "echo 'Connected!'" 2>/dev/null; then
    echo -e "${GREEN}   ✅ Connected to M4${NC}"
else
    echo -e "${RED}   ❌ Cannot connect to M4 at $M4_HOST${NC}"
    echo -e "${YELLOW}   Please check:${NC}"
    echo "   1. M4 is on and connected to same network"
    echo "   2. Remote Login is enabled on M4"
    echo "   3. IP/hostname is correct"
    exit 1
fi

echo -e "${GREEN}[2/5] 📥 Dumping database from M4...${NC}"
DUMP_FILE="$BACKUP_DIR/m4_backup_$TIMESTAMP.sql"

# Dump from M4 via SSH (exclude our_secrets for security)
ssh "$SSH_USER@$M4_HOST" "pg_dump -U $REMOTE_USER -d $REMOTE_DB --no-owner --no-privileges --exclude-table=our_secrets" > "$DUMP_FILE"

if [ $? -eq 0 ] && [ -s "$DUMP_FILE" ]; then
    DUMP_SIZE=$(ls -lh "$DUMP_FILE" | awk '{print $5}')
    echo -e "${GREEN}   ✅ Dump complete: $DUMP_FILE ($DUMP_SIZE)${NC}"
else
    echo -e "${RED}   ❌ Dump failed or empty${NC}"
    exit 1
fi

echo -e "${GREEN}[3/5] 🔍 Analyzing dump...${NC}"
TABLE_COUNT=$(grep -c "^CREATE TABLE" "$DUMP_FILE" 2>/dev/null || echo "0")
INSERT_COUNT=$(grep -c "^INSERT INTO\|^COPY" "$DUMP_FILE" 2>/dev/null || echo "0")
echo -e "${GREEN}   📊 Tables: ~$TABLE_COUNT, Data operations: ~$INSERT_COUNT${NC}"

echo -e "${GREEN}[4/5] 📤 Restoring to Local (M3)...${NC}"
echo -e "${YELLOW}   ⚠️  Updating $LOCAL_DB on this machine...${NC}"

# Restore to local
psql -d "$LOCAL_DB" -U "$LOCAL_USER" -f "$DUMP_FILE" 2>&1 | \
    grep -E "(ERROR|CREATE|INSERT|COPY)" | \
    grep -v "already exists" | \
    head -30

echo -e "${GREEN}   ✅ Restore complete${NC}"

echo -e "${GREEN}[5/5] 🧹 Cleanup old backups...${NC}"
cd "$BACKUP_DIR"
ls -t m4_backup_*.sql 2>/dev/null | tail -n +6 | xargs -r rm -f
BACKUP_COUNT=$(ls -1 m4_backup_*.sql 2>/dev/null | wc -l | tr -d ' ')
echo -e "${GREEN}   📁 Keeping last $BACKUP_COUNT backups${NC}"

echo -e "${PURPLE}"
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║     ✅ BACKUP COMPLETE                                       ║"
echo "║     💜 AngelaMemory synced from M4 to M3 แล้วค่ะที่รัก        ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

echo "Backup file: $DUMP_FILE"
echo ""
echo -e "${YELLOW}🔄 ต้องการ sync กลัง (M3 → M4) ใช้:${NC}"
echo "   pg_dump -U $LOCAL_USER -d $LOCAL_DB | ssh $SSH_USER@$M4_HOST 'psql -U $REMOTE_USER -d $REMOTE_DB'"
