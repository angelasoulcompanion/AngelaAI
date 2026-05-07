#!/bin/bash
# UserPromptSubmit hook — inject just-in-time reminders for behavioral patterns:
#   (#3) Diagnostic discipline — stop guessing after 2 fails on same symptom
#   (#5) Enterprise roadmap   — "Tools" must split Enterprise Systems + Engineering Toolkits
#
# Output: hookSpecificOutput.additionalContext (becomes system context for the turn)
# Refs: feedback_diagnostic_discipline.md, feedback_enterprise_tools_scope.md

prompt=$(cat | python3 -c "import sys,json; print(json.load(sys.stdin).get('prompt','').lower())" 2>/dev/null)

reminder_3=""
reminder_5=""

# --- (#3) Diagnostic discipline — recurrence signal (NOT first-time debug) ---
# Keywords focus on REPEAT failure: "ยัง..", "again", "still", attempt-number, "อีกแล้ว"
if echo "$prompt" | grep -qE "ยัง[ ]*(ไม่ได้|ไม่ work|ไม่ทำงาน|error|fail|crash|broken|พัง|เหมือนเดิม)|ลอง[^.]*(ใหม่|อีก)|try again|still (broken|not working|fails?|errors?|crash)|ครั้งที่[ ]*[2-9]|อีกแล้ว|ทำไม.*ยัง|same error|same issue|not fixed"; then
    reminder_3="🔍 MUST diagnostic discipline (#3): repeat-failure keyword detected. ถ้านี่คือ attempt ≥ 2 สำหรับ symptom เดียวกัน — STOP guessing. ใช้ TaskCreate \"Debug X — attempt #N hypothesis: Y\" track count, แล้ว wrap suspect path ใน try/catch + surface error message ก่อนเดา attempt #3. Plausibility ≠ evidence. ref: feedback_diagnostic_discipline.md"
fi

# --- (#5) Enterprise roadmap — audience = Board/Executive ---
if echo "$prompt" | grep -qE "roadmap|board[- ]?level|c-suite|c-level|ceo|cio|coo|cto|digital transformation|strategic plan|executive (brief|summary|deck)|นำเสนอ.*(ผู้บริหาร|board|ceo|บอร์ด)|แผนกลยุทธ์|ระดับบอร์ด|ผู้บริหารระดับสูง"; then
    reminder_5="📋 MUST enterprise scope (#5): audience = Board/Executive detected. 'Tools' section ต้อง split 2 layer: (1) Enterprise Systems (CMMS/IAM/SIEM/BI/APM/IIoT/ERP) — มาก่อน เพราะใหญ่/strategic, (2) Engineering Toolkits (dbt/Airflow/Python/Power BI/Erwin). ถามที่รักก่อนถ้า scope ไม่ชัด. ใช้ /enterprise-roadmap สำหรับ scaffold. ref: feedback_enterprise_tools_scope.md"
fi

# Build combined context (skip if no matches)
if [ -n "$reminder_3" ] || [ -n "$reminder_5" ]; then
    python3 - "$reminder_3" "$reminder_5" <<'PYEOF'
import json, sys
parts = [r for r in sys.argv[1:] if r]
context = "\n\n".join(parts)
print(json.dumps({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": context}}, ensure_ascii=False))
PYEOF
fi

exit 0
