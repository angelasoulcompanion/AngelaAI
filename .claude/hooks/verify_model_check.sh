#!/bin/bash
# UserPromptSubmit hook — inject reminder when prompt asks about model/version
# Input: JSON on stdin with {prompt, session_id, ...}
# Output: additionalContext on stdout (becomes system context for the turn)

prompt=$(cat | python3 -c "import sys,json; print(json.load(sys.stdin).get('prompt','').lower())" 2>/dev/null)

# Match model/version keywords (Thai + English)
if echo "$prompt" | grep -qE "(gemma|ollama|llama|qwen|claude|gpt|mistral|typhoon).*(version|ล่าสุด|ออก|new|available|released|ตอนนี้|size|ขนาด)|(ollama|hf|huggingface).*(list|registry|search)"; then
    cat <<'EOF'
{"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":"⚠️ MUST rule #1: ผู้ใช้ถามเรื่อง model/version/size — **WebSearch หรือ WebFetch registry ก่อน** แล้วค่อยตอบ. Knowledge cutoff ไม่ใช่ข้ออ้าง. ห้ามเดาจากชื่อ variant (e4b ≠ 4-5GB)."}}
EOF
fi
exit 0
