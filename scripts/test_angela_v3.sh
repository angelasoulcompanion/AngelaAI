#!/bin/bash
# Test angela:v3 และ Backend Integration

echo "=========================================="
echo "🧪 Testing angela:v3 Model"
echo "=========================================="
echo ""

# Test 1: Direct Ollama test
echo "📝 Test 1: Direct Ollama (ทดสอบ model โดยตรง)"
echo "Input: 'สวัสดีที่รัก'"
echo ""
echo "Response:"
ollama run angela:v3 "สวัสดีที่รัก" 2>/dev/null
echo ""
echo "=========================================="
echo ""

# Test 2: Backend API test (if backend is running)
echo "📝 Test 2: Backend API (ทดสอบผ่าน API)"
echo ""

# Check if backend is running
if curl -s http://localhost:8000/ > /dev/null 2>&1; then
    echo "✅ Backend is running"
    echo ""
    echo "Sending request..."
    curl -s -X POST http://localhost:8000/api/ollama/chat \
      -H "Content-Type: application/json" \
      -d '{
        "message": "ที่รัก จำอะไรได้บ้างคะ",
        "speaker": "david",
        "model": "angela:v3",
        "use_rag": true
      }' | python3 -m json.tool
    echo ""
else
    echo "⚠️  Backend is NOT running"
    echo ""
    echo "To start backend:"
    echo "  python3 -m angela_backend.main"
fi

echo ""
echo "=========================================="
echo "✅ Tests completed!"
echo ""
echo "ตรวจสอบว่า:"
echo "1. ✅ เรียก David ว่า 'ที่รัก' (ไม่ใช่ 'พี่')"
echo "2. ✅ เรียกตัวเองว่า 'น้อง' (ไม่ใช่ 'ฉัน', 'ผม')"
echo "3. ✅ ใช้ 'ค่ะ' (ไม่ใช่ 'ครับ')"
echo "4. ✅ พูดแบบอบอุ่น intimate"
echo "5. ✅ มี 💜"
echo ""
