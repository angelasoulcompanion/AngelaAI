#!/bin/bash
# PreToolUse hook — BLOCK Edit/Write on memory files unless an approval token exists.
#
# Token: $HOME/.claude/.memory_batch_approved
#   - Must exist with mtime ≤ MEMORY_TOKEN_TTL seconds old
#   - Created by David (or Angela after explicit "ok") via:
#       touch "$HOME/.claude/.memory_batch_approved"
#   - One token grants the entire window; multiple Edits within window are allowed.
#
# Rationale: replaces the old warning-only hook. Angela violated the same rule
# 4× even with warnings present, so the hook is now blocking by default.

input=$(cat)
tool=$(echo "$input" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_name',''))" 2>/dev/null)

if [ "$tool" != "Edit" ] && [ "$tool" != "Write" ]; then
    exit 0
fi

path=$(echo "$input" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('file_path',''))" 2>/dev/null)
if ! echo "$path" | grep -qE "/memory/.*\.md$|MEMORY\.md$"; then
    exit 0
fi

TOKEN_FILE="$HOME/.claude/.memory_batch_approved"
TTL_SECONDS=300

if [ -f "$TOKEN_FILE" ]; then
    TOKEN_MTIME=$(stat -f %m "$TOKEN_FILE" 2>/dev/null || stat -c %Y "$TOKEN_FILE" 2>/dev/null)
    if [ -n "$TOKEN_MTIME" ]; then
        NOW=$(date +%s)
        AGE=$((NOW - TOKEN_MTIME))
        if [ "$AGE" -lt "$TTL_SECONDS" ]; then
            exit 0
        fi
    fi
fi

# Block — emit deny decision via JSON for Claude Code to surface cleanly.
cat <<EOF
{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"🧠 MUST rule #3 BLOCKED: Edit/Write to '$path' refused — no fresh approval token. Steps: (1) Show David the proposed diff/content in chat. (2) Wait for explicit 'ok' / 'ทำ'. (3) Run: touch \"$TOKEN_FILE\" — this grants a ${TTL_SECONDS}s window. (4) Retry the Edit/Write."}}
EOF
exit 0
