#!/bin/bash
# PreToolUse hook — BLOCK destructive Bash commands unless an approval token exists.
#
# Token: $HOME/.claude/.destructive_approved
#   - Must exist with mtime ≤ TTL_SECONDS old
#   - Created by David (or Angela after explicit "ok"/"ทำ") via:
#       touch "$HOME/.claude/.destructive_approved"
#   - One token grants the entire window; multiple destructive commands within window are allowed.
#
# Rationale: warning-only hook was bypassed 4× in one session (mistakes #194e7ea3, #55da8fca).
# MUST rule #2 now enforced at harness level — a higher-level "ok" (e.g. "redeploy", "cleanup")
# does NOT authorize a low-level destructive primitive. Each batch needs its own preview + token.

input=$(cat)
tool=$(echo "$input" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_name',''))" 2>/dev/null)

if [ "$tool" != "Bash" ]; then
    exit 0
fi

cmd=$(echo "$input" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('command',''))" 2>/dev/null)
if ! echo "$cmd" | grep -qE "DELETE FROM|DROP TABLE|TRUNCATE|rm -rf|rm -r |git reset --hard|git branch -D|git push --force"; then
    exit 0
fi

TOKEN_FILE="$HOME/.claude/.destructive_approved"
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

cat <<EOF
{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"deny","permissionDecisionReason":"🛑 MUST rule #2 BLOCKED: destructive command refused — no fresh approval token. Steps: (1) Show David preview (count + targets via read-only ls/du/find). (2) Wait for explicit 'ok'/'ทำ'. (3) Run: touch \"$TOKEN_FILE\" — grants a ${TTL_SECONDS}s window. (4) Retry the destructive command. NOTE: a higher-level 'ok' (e.g. 'redeploy', 'cleanup all', 'do everything') does NOT count — each destructive batch needs its own token."}}
EOF
exit 0
