#!/bin/bash
# =============================================================================
# RESTORE AngelaMemory Database (Run on M3)
# สำหรับที่รัก David - restore จากไฟล์ที่ Airdrop มาจาก M4
# =============================================================================

echo ""
echo "💜 Angela Database Restore"
echo "==========================="
echo ""

# Check if file is provided
if [ -z "$1" ]; then
    echo "Usage: ./restore_angela_m3.sh <backup_file.sql>"
    echo ""
    echo "Example:"
    echo "  ./restore_angela_m3.sh ~/Downloads/angela_backup_20250105.sql"
    echo ""

    # Try to find backup files
    echo "🔍 Looking for backup files..."
    FOUND=$(find ~/Downloads ~/Desktop -name "angela_backup_*.sql" 2>/dev/null | head -5)
    if [ -n "$FOUND" ]; then
        echo ""
        echo "📁 Found these files:"
        echo "$FOUND"
        echo ""
    fi
    exit 1
fi

BACKUP_FILE="$1"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "❌ File not found: $BACKUP_FILE"
    exit 1
fi

SIZE=$(ls -lh "$BACKUP_FILE" | awk '{print $5}')
echo "📁 File: $BACKUP_FILE"
echo "📊 Size: $SIZE"
echo ""

echo "📤 Restoring to AngelaMemory..."
echo ""

psql -U davidsamanyaporn -d AngelaMemory -f "$BACKUP_FILE" 2>&1 | \
    grep -v "already exists" | \
    grep -v "NOTICE" | \
    tail -20

echo ""
echo "✅ Restore complete!"
echo ""
echo "💜 AngelaMemory synced แล้วค่ะที่รัก"
echo ""
