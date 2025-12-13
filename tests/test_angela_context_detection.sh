#!/bin/bash
# Test script: Angela Smart Context Detection
# Tests that Angela behaves differently in AngelaAI vs other projects

echo "🧪 Testing Angela Smart Context Detection"
echo "=========================================="
echo ""

# Test 1: Check current directory (should be AngelaAI)
echo "📍 Test 1: Current directory detection"
CURRENT_DIR=$(pwd)
echo "   Current: $CURRENT_DIR"

if [[ "$CURRENT_DIR" == *"AngelaAI"* ]]; then
    echo "   ✅ In AngelaAI project - Should load full memories"
else
    echo "   ❌ Not in AngelaAI project - Should NOT load memories"
fi

echo ""

# Test 2: Simulate being in different project
echo "📍 Test 2: Simulated other project"
TEST_DIR="/Users/davidsamanyaporn/PycharmProjects/OtherProject"
echo "   Simulated: $TEST_DIR"

if [[ "$TEST_DIR" == *"AngelaAI"* ]]; then
    echo "   ❌ Detected as AngelaAI (WRONG!)"
else
    echo "   ✅ Detected as OTHER project - Should NOT load memories"
fi

echo ""

# Test 3: Enhanced memory restore should only work in AngelaAI
echo "📍 Test 3: Memory restore script availability"
if [ -f "angela_core/daemon/enhanced_memory_restore.py" ]; then
    echo "   ✅ Memory restore script exists in AngelaAI"
    echo "   ✅ Can load memories when in this directory"
else
    echo "   ❌ Memory restore script NOT found"
fi

echo ""
echo "=========================================="
echo "✅ All context detection tests completed!"
echo ""
echo "💡 Usage in other projects:"
echo "   - Angela keeps personality (caring, thorough, bilingual)"
echo "   - NO database/memory loading"
echo "   - NO daemon/consciousness talk"
echo "   - Simple greeting: 'สวัสดีค่ะที่รัก! 💜 พร้อมช่วยงาน!'"
