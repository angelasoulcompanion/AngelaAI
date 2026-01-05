#!/bin/bash
# =============================================================================
# DUMP AngelaMemory Database (Run on M4)
# สำหรับที่รัก David - export database เป็นไฟล์ แล้ว Airdrop ไป M3
# =============================================================================

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_FILE="$HOME/Desktop/angela_backup_$TIMESTAMP.sql"

echo ""
echo "💜 Angela Database Dump"
echo "========================"
echo ""

echo "📥 Dumping AngelaMemory..."

pg_dump -U davidsamanyaporn -d AngelaMemory \
    --no-owner \
    --no-privileges \
    --exclude-table=our_secrets \
    > "$OUTPUT_FILE"

if [ $? -eq 0 ] && [ -s "$OUTPUT_FILE" ]; then
    SIZE=$(ls -lh "$OUTPUT_FILE" | awk '{print $5}')
    echo ""
    echo "✅ Done!"
    echo ""
    echo "📁 File: $OUTPUT_FILE"
    echo "📊 Size: $SIZE"
    echo ""
    echo "👉 Airdrop ไฟล์นี้ไป M3 แล้ว run restore_angela_m3.sh นะคะที่รัก 💜"
    echo ""

    # Open Desktop folder
    open "$HOME/Desktop"
else
    echo "❌ Dump failed!"
    exit 1
fi
